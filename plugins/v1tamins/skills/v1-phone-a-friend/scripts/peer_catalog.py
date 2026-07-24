#!/usr/bin/env python3
"""Discover installed peer CLIs without launching a model.

Discovery and authentication are separate facts. Selection emits one JSON
proposal that a human can approve before a peer process starts.

Exit status is zero when the discovery result is valid, even when a provider
is missing or its model catalog is unresolved. Invalid explicit selections
return status 2.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from peer_adapters import (  # noqa: E402
    KNOWN_EFFORT_RANK,
    discover_provider,
    effort_name,
    model_family,
    sha256_text,
)
from peer_models import (  # noqa: E402
    AuthFact,
    Candidate,
    LaunchState,
    ModelCatalog,
    ModelEntry,
    ModelSelection,
    Proposal,
    ProviderDiscovery,
    SelectionError,
)
from peer_policy import PROVIDERS  # noqa: E402

SCHEMA = "v1-peer-catalog/v1"
DEFAULT_TIMEOUT_SECONDS = 8
PROFILE_NAMES = ("quality", "balanced", "fast", "custom")

# Re-export for contract tests and callers that import from this module.
__all__ = [
    "PROVIDERS",
    "SCHEMA",
    "build_candidates",
    "choose_model",
    "compare_preview_context",
    "prompt_fingerprints",
    "provider_from_dict",
]


def effort_rank(level: str | None) -> int:
    return KNOWN_EFFORT_RANK.get(level or "none", 0)


def provider_from_dict(payload: dict[str, Any]) -> ProviderDiscovery:
    """Normalize a dict fixture into ProviderDiscovery at the test/API edge."""

    auth_payload = payload["auth"]
    if isinstance(auth_payload, AuthFact):
        auth = auth_payload
    else:
        auth = AuthFact(
            source=auth_payload["source"],
            confidence=auth_payload.get("confidence", "unresolved"),
            credential_presence=auth_payload.get(
                "credential_presence", "none_detected"
            ),
            policy_state=auth_payload["policy_state"],
            key_env_names=tuple(auth_payload.get("key_env_names", ())),
        )
    models = tuple(
        model
        if isinstance(model, ModelEntry)
        else ModelEntry(
            id=model["id"],
            family=model.get("family", model_family(model["id"])),
            reasoning_levels=tuple(
                model.get("reasoning_levels") or model.get("efforts") or ()
            ),
            rank=int(model.get("rank", 0)),
        )
        for model in payload.get("models", [])
    )
    catalog_payload = payload["model_catalog"]
    if isinstance(catalog_payload, ModelCatalog):
        catalog = catalog_payload
    else:
        catalog = ModelCatalog(
            status=catalog_payload.get("status", "unresolved"),
            confidence=catalog_payload.get("confidence", "unresolved"),
            source=catalog_payload.get("source"),
            fingerprint=catalog_payload.get("fingerprint"),
        )
    return ProviderDiscovery(
        cli=payload["cli"],
        installed=bool(payload.get("installed", True)),
        executable=payload.get("executable"),
        version=payload.get("version"),
        version_fingerprint=payload.get("version_fingerprint"),
        auth=auth,
        models=models,
        model_catalog=catalog,
        reasoning_levels=tuple(payload.get("reasoning_levels", ())),
        roles=tuple(payload.get("roles", ("structural review",))),
        workflow=payload.get("workflow", "available"),
    )


def choose_model(
    provider: ProviderDiscovery,
    profile: str,
    requested_model: str | None = None,
    requested_effort: str | None = None,
) -> ModelSelection | SelectionError:
    models = list(provider.models)
    reasoning_levels = list(provider.reasoning_levels)
    catalog_status = provider.model_catalog.status
    catalog_confidence = provider.model_catalog.confidence

    explicit = False
    if requested_model:
        selected = next(
            (model for model in models if model.id == requested_model), None
        )
        if selected is None:
            if catalog_status != "resolved" or not models:
                selected = ModelEntry(
                    id=requested_model,
                    family=model_family(requested_model),
                    reasoning_levels=tuple(reasoning_levels),
                    rank=0,
                )
                explicit = True
            else:
                return SelectionError(
                    code="model_not_current",
                    requested_model=requested_model,
                    alternatives=tuple(model.id for model in models[:8]),
                )
    elif not models:
        return ModelSelection(
            model=None,
            model_family="unknown",
            reasoning=None,
            model_confidence="unresolved",
            explicit=False,
        )
    else:

        def score(model: ModelEntry) -> tuple[int, int]:
            levels = list(model.reasoning_levels or reasoning_levels)
            strongest = max((effort_rank(level) for level in levels), default=0)
            rank = -model.rank
            if profile == "fast":
                return (-strongest, rank)
            if profile == "balanced":
                return (min(strongest, max(1, strongest - 1)), rank)
            return (strongest, rank)

        selected = sorted(models, key=score, reverse=True)[0]

    levels = list(selected.reasoning_levels or reasoning_levels)
    if requested_effort:
        normalized = effort_name(requested_effort)
        if normalized is None or (levels and normalized not in levels):
            return SelectionError(
                code="reasoning_level_unsupported",
                requested_effort=requested_effort,
                alternatives=tuple(levels),
            )
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

    model_confidence: Any = "unresolved" if explicit else catalog_confidence
    return ModelSelection(
        model=selected.id,
        model_family=selected.family,
        reasoning=selected_effort,
        model_confidence=model_confidence,
        explicit=explicit,
    )


def candidate_sort_key(candidate: Candidate) -> tuple[int, int, int, int]:
    auth_source = candidate.auth.source
    auth_score = {"subscription_native": 3, "unverified": 1, "api_explicit": 1}.get(
        auth_source, 0
    )
    catalog_score = {"verified": 2, "degraded": 1, "unresolved": 0}.get(
        candidate.catalog_confidence, 0
    )
    reasoning_score = effort_rank(candidate.reasoning)
    return auth_score, catalog_score, reasoning_score, -candidate.provider_rank


def candidate_launch_state(
    provider: ProviderDiscovery,
    *,
    selection: ModelSelection,
) -> tuple[bool, LaunchState]:
    auth = provider.auth
    catalog_status = provider.model_catalog.status
    workflow = provider.workflow

    if auth.policy_state == "blocked_api_key_present":
        return False, "blocked_api_key_present"
    if auth.source == "unavailable":
        return False, "auth_unavailable"
    if auth.source == "unverified":
        return False, "auth_unverified"
    if catalog_status != "resolved" and not selection.explicit:
        return False, "model_unresolved"
    if selection.model is None:
        return False, "model_unresolved"
    if workflow != "available":
        return False, "workflow_unavailable"
    return True, "eligible"


def build_candidates(
    providers: list[ProviderDiscovery],
    profile: str,
    count: int,
    requested_cli: str | None,
    requested_model: str | None,
    requested_effort: str | None,
) -> tuple[list[Candidate], list[Candidate], list[dict[str, Any]]]:
    """Build the candidate universe once, then slice roster vs alternatives."""

    universe: list[Candidate] = []
    errors: list[dict[str, Any]] = []
    for provider_rank, provider in enumerate(providers):
        if not provider.installed:
            continue
        use_model = (
            requested_model
            if requested_cli is None or provider.cli == requested_cli
            else None
        )
        use_effort = (
            requested_effort
            if requested_cli is None or provider.cli == requested_cli
            else None
        )
        # When a custom CLI filter is set, still propose defaults for others so
        # alternatives remain available without a second discovery pass.
        if requested_cli and provider.cli != requested_cli:
            use_model = None
            use_effort = None
        outcome = choose_model(provider, profile, use_model, use_effort)
        if isinstance(outcome, SelectionError):
            if requested_cli is None or provider.cli == requested_cli:
                errors.append({"cli": provider.cli, **outcome.to_dict()})
            continue
        selection = outcome
        eligible, launch_state = candidate_launch_state(provider, selection=selection)
        universe.append(
            Candidate(
                cli=provider.cli,
                version=provider.version,
                version_fingerprint=provider.version_fingerprint,
                model=selection.model,
                model_family=selection.model_family,
                reasoning=selection.reasoning,
                role=provider.roles[0] if provider.roles else "structural review",
                permission="readonly",
                auth=provider.auth,
                catalog_confidence=provider.model_catalog.confidence,
                catalog_fingerprint=provider.model_catalog.fingerprint,
                confidence={
                    "auth": provider.auth.confidence,
                    "catalog": provider.model_catalog.confidence,
                    "model": selection.model_confidence,
                },
                workflow=provider.workflow,
                provider_rank=provider_rank,
                eligible=eligible,
                launch_state=launch_state,
            )
        )

    ranked = sorted(universe, key=candidate_sort_key, reverse=True)
    pool = [
        candidate
        for candidate in ranked
        if requested_cli is None or candidate.cli == requested_cli
    ]
    selected: list[Candidate] = []
    families: set[str] = set()
    for candidate in pool:
        if len(selected) >= count:
            break
        if candidate.model_family in families and any(
            other.model_family not in families for other in pool
        ):
            continue
        selected.append(candidate)
        families.add(candidate.model_family)
    if len(selected) < count:
        for candidate in pool:
            if candidate not in selected:
                selected.append(candidate)
            if len(selected) >= count:
                break

    selected_keys = {
        (candidate.cli, candidate.model, candidate.reasoning) for candidate in selected
    }
    alternatives = [
        candidate
        for candidate in ranked
        if (candidate.cli, candidate.model, candidate.reasoning) not in selected_keys
    ]
    return selected, alternatives, errors


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
        choices=PROFILE_NAMES,
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

    provider_names = tuple(PROVIDERS)
    with ThreadPoolExecutor(max_workers=len(provider_names)) as pool:
        discovered = list(
            pool.map(
                lambda name: discover_provider(
                    name, args.auth_mode, args.timeout_seconds
                ),
                provider_names,
            )
        )
    selected, alternatives, errors = build_candidates(
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
        json.dumps(
            [provider.to_dict() for provider in discovered],
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    context: dict[str, Any] = {"status": "fresh", "reasons": []}
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

    roster = [candidate.with_prompt(prompt_resolution) for candidate in selected]
    alt_roster = [
        candidate.with_prompt(prompt_resolution) for candidate in alternatives
    ]
    result = Proposal(
        ok=True,
        schema=SCHEMA,
        profile=args.profile,
        auth_mode=args.auth_mode,
        confirmation_required=True,
        profile_options=[
            {"profile": name, "recommended": args.profile == name}
            for name in PROFILE_NAMES
        ],
        eligible_count=sum(1 for candidate in roster if candidate.eligible),
        roster_status="complete"
        if len(roster) >= args.count and all(candidate.eligible for candidate in roster)
        else "partial",
        recommended_roster=roster,
        alternatives=alt_roster,
        discovered=discovered,
        selection_errors=errors,
        prompt_resolution=prompt_resolution,
        catalog_fingerprint=catalog_fingerprint,
        snapshot_fingerprint=args.snapshot_fingerprint,
        context=context,
    )
    print(json.dumps(result.to_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
