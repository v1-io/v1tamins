#!/usr/bin/env python3
"""Discover installed peer CLIs without launching a model.

The script intentionally treats provider discovery and authentication as
separate facts. It consumes provider-owned version/help/model-list surfaces,
scrubs known API-key variables in subscription mode, and emits one JSON
proposal that a human can approve before a peer process is started.

Exit status is zero when the discovery result is valid, even when a provider
is missing or its model catalog is unresolved. Invalid explicit selections
return status 2. No command output is copied into the result; only bounded,
sanitized versions, parsed model identifiers, and fingerprints are returned.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

try:
    from peer_catalog_support import (
        DEFAULT_TIMEOUT_SECONDS,
        KNOWN_EFFORT_RANK,
        PROVIDERS,
        SCHEMA,
        discover_provider,
        effort_name,
        model_family,
        sha256_text,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from peer_catalog_support import (
        DEFAULT_TIMEOUT_SECONDS,
        KNOWN_EFFORT_RANK,
        PROVIDERS,
        SCHEMA,
        discover_provider,
        effort_name,
        model_family,
        sha256_text,
    )


def effort_rank(level: str | None) -> int:
    return KNOWN_EFFORT_RANK.get(level or "none", 0)


def choose_model(
    provider: dict[str, Any],
    profile: str,
    requested_model: str | None = None,
    requested_effort: str | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    models = provider.get("models", [])
    if requested_model:
        selected = next(
            (model for model in models if model["id"] == requested_model), None
        )
        if selected is None:
            return None, {
                "code": "model_not_current",
                "requested_model": requested_model,
                "alternatives": [model["id"] for model in models[:8]],
            }
    elif not models:
        return None, {"code": "model_unresolved", "alternatives": []}
    else:

        def score(model: dict[str, Any]) -> tuple[int, int]:
            levels = model.get("reasoning_levels") or provider.get(
                "reasoning_levels", []
            )
            strongest = max((effort_rank(level) for level in levels), default=0)
            rank = -int(model.get("rank", 0))
            if profile == "fast":
                return (-strongest, rank)
            if profile == "balanced":
                return (min(strongest, max(1, strongest - 1)), rank)
            return (strongest, rank)

        selected = sorted(models, key=score, reverse=True)[0]

    levels = selected.get("reasoning_levels") or provider.get("reasoning_levels", [])
    if requested_effort:
        normalized = effort_name(requested_effort)
        if normalized is None or normalized not in levels:
            return None, {
                "code": "reasoning_level_unsupported",
                "requested_effort": requested_effort,
                "alternatives": levels,
            }
        selected_effort = normalized
    elif levels:
        if profile == "fast":
            selected_effort = min(levels, key=effort_rank)
        elif profile == "balanced":
            ordered = sorted(levels, key=effort_rank)
            selected_effort = ordered[max(0, len(ordered) - 2)]
        else:
            selected_effort = max(levels, key=effort_rank)
    else:
        selected_effort = None

    return {
        "model": selected["id"],
        "model_family": selected.get("family", model_family(selected["id"])),
        "reasoning": selected_effort,
        "model_confidence": provider["model_catalog"]["confidence"],
    }, None


def candidate_sort_key(candidate: dict[str, Any]) -> tuple[int, int, int, int]:
    auth_source = candidate["auth"]["source"]
    auth_score = {"subscription_native": 3, "unverified": 1, "api_explicit": 1}.get(
        auth_source, 0
    )
    catalog_score = {"verified": 2, "degraded": 1, "unresolved": 0}.get(
        candidate["catalog_confidence"], 0
    )
    reasoning_score = effort_rank(candidate.get("reasoning"))
    return auth_score, catalog_score, reasoning_score, -candidate["provider_rank"]


def candidate_launch_state(provider: dict[str, Any]) -> tuple[bool, str]:
    if provider["auth"]["policy_state"] == "blocked_api_key_present":
        return False, "blocked_api_key_present"
    if provider["auth"]["source"] == "unavailable":
        return False, "auth_unavailable"
    if provider["auth"]["source"] == "unverified":
        return False, "auth_unverified"
    if provider["model_catalog"].get("status") != "resolved":
        return False, "model_unresolved"
    if provider["workflow"] != "available":
        return False, "workflow_unavailable"
    return True, "eligible"


def build_candidates(
    providers: list[dict[str, Any]],
    profile: str,
    count: int,
    requested_cli: str | None,
    requested_model: str | None,
    requested_effort: str | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for provider_rank, provider in enumerate(providers):
        if not provider["installed"]:
            continue
        if requested_cli and provider["cli"] != requested_cli:
            continue
        selection, error = choose_model(
            provider, profile, requested_model, requested_effort
        )
        if error:
            errors.append({"cli": provider["cli"], **error})
            continue
        assert selection is not None
        eligible, launch_state = candidate_launch_state(provider)
        candidates.append(
            {
                "cli": provider["cli"],
                "version": provider["version"],
                "version_fingerprint": provider["version_fingerprint"],
                "model": selection["model"],
                "model_family": selection["model_family"],
                "reasoning": selection["reasoning"],
                "role": provider["roles"][0]
                if provider["roles"]
                else "structural review",
                "permission": "readonly",
                "auth": provider["auth"],
                "catalog_confidence": provider["model_catalog"]["confidence"],
                "catalog_fingerprint": provider["model_catalog"]["fingerprint"],
                "confidence": {
                    "auth": provider["auth"]["confidence"],
                    "catalog": provider["model_catalog"]["confidence"],
                    "model": selection["model_confidence"],
                },
                "workflow": provider["workflow"],
                "provider_rank": provider_rank,
                "eligible": eligible,
                "launch_state": launch_state,
            }
        )

    ranked = sorted(candidates, key=candidate_sort_key, reverse=True)
    selected: list[dict[str, Any]] = []
    families: set[str] = set()
    for candidate in ranked:
        if len(selected) >= count:
            break
        if candidate["model_family"] in families and any(
            other["model_family"] not in families for other in ranked
        ):
            continue
        selected.append(candidate)
        families.add(candidate["model_family"])
    if len(selected) < count:
        for candidate in ranked:
            if candidate not in selected:
                selected.append(candidate)
            if len(selected) >= count:
                break
    return selected, errors


def prompt_fingerprints(paths: Iterable[str]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.is_file():
            results.append({"source": str(path), "status": "missing"})
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        results.append(
            {"source": str(path), "status": "resolved", "fingerprint": digest}
        )
    return results


def compare_preview_context(
    preview: dict[str, Any],
    catalog_fingerprint: str,
    prompt_resolution: dict[str, Any],
    snapshot_fingerprint: str | None,
) -> dict[str, Any]:
    stale_reasons: list[str] = []
    if preview.get("catalog_fingerprint") != catalog_fingerprint:
        stale_reasons.append("catalog_changed")
    if preview.get("prompt_resolution") != prompt_resolution:
        stale_reasons.append("prompt_source_changed")
    if (
        snapshot_fingerprint is not None
        and preview.get("snapshot_fingerprint") != snapshot_fingerprint
    ):
        stale_reasons.append("working_tree_changed")
    return {
        "status": "context_stale" if stale_reasons else "fresh",
        "reasons": stale_reasons,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=("quality", "balanced", "fast", "custom"),
        default="quality",
    )
    parser.add_argument(
        "--auth-mode",
        choices=("subscription_native", "api_explicit"),
        default="subscription_native",
    )
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument(
        "--cli", choices=tuple(PROVIDERS), help="restrict a custom selection to one CLI"
    )
    parser.add_argument("--model")
    parser.add_argument("--reasoning")
    parser.add_argument(
        "--prompt-profile",
        choices=(
            "structural",
            "correctness",
            "maintainability",
            "research",
            "multimodal",
            "custom",
        ),
        default="structural",
    )
    parser.add_argument("--prompt-source", action="append", default=[])
    parser.add_argument(
        "--compare-preview", help="previous JSON proposal to freshness-check"
    )
    parser.add_argument("--snapshot-fingerprint")
    parser.add_argument(
        "--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.count < 1 or args.count > len(PROVIDERS):
        print(json.dumps({"ok": False, "error": {"code": "invalid_count"}}))
        return 2
    if args.profile == "custom" and not (args.cli and args.model):
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {
                        "code": "custom_selection_required",
                        "message": "custom requires --cli and --model",
                    },
                }
            )
        )
        return 2
    if args.timeout_seconds <= 0:
        print(json.dumps({"ok": False, "error": {"code": "invalid_timeout"}}))
        return 2

    discovered = [
        discover_provider(name, args.auth_mode, args.timeout_seconds)
        for name in PROVIDERS
    ]
    selected, errors = build_candidates(
        discovered, args.profile, args.count, args.cli, args.model, args.reasoning
    )
    prompt_sources = prompt_fingerprints(args.prompt_source)
    prompt_status = "unresolved"
    if prompt_sources and all(
        source.get("status") == "resolved" for source in prompt_sources
    ):
        prompt_status = "resolved"
    elif prompt_sources:
        prompt_status = "degraded"
    prompt_resolution = {
        "profile": args.prompt_profile,
        "status": prompt_status,
        "sources": prompt_sources,
    }
    catalog_fingerprint = sha256_text(
        json.dumps(discovered, sort_keys=True, separators=(",", ":"))
    )
    context = {"status": "fresh", "reasons": []}
    if args.compare_preview:
        try:
            with open(args.compare_preview, encoding="utf-8") as handle:
                previous = json.load(handle)
        except (OSError, json.JSONDecodeError):
            print(json.dumps({"ok": False, "error": {"code": "invalid_preview"}}))
            return 2
        context = compare_preview_context(
            previous, catalog_fingerprint, prompt_resolution, args.snapshot_fingerprint
        )
    result = {
        "ok": True,
        "schema": SCHEMA,
        "profile": args.profile,
        "auth_mode": args.auth_mode,
        "confirmation_required": True,
        "profile_options": [
            {"profile": "quality", "recommended": args.profile == "quality"},
            {"profile": "balanced", "recommended": False},
            {"profile": "fast", "recommended": False},
            {"profile": "custom", "recommended": False},
        ],
        "eligible_count": sum(1 for candidate in selected if candidate["eligible"]),
        "roster_status": "complete"
        if len(selected) >= args.count
        and all(candidate["eligible"] for candidate in selected)
        else "partial",
        "recommended_roster": selected,
        "alternatives": [
            candidate
            for provider in discovered
            for candidate in build_candidates(
                [provider], args.profile, 1, None, None, None
            )[0]
            if not any(
                candidate["cli"] == chosen["cli"]
                and candidate["model"] == chosen["model"]
                and candidate["reasoning"] == chosen["reasoning"]
                for chosen in selected
            )
        ],
        "discovered": discovered,
        "selection_errors": errors,
        "prompt_resolution": prompt_resolution,
        "catalog_fingerprint": catalog_fingerprint,
        "snapshot_fingerprint": args.snapshot_fingerprint,
        "context": context,
    }
    for candidate in result["recommended_roster"] + result["alternatives"]:
        candidate["prompt"] = prompt_resolution
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
