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
    Candidate,
    CatalogConfidence,
    LaunchState,
    ModelEntry,
    ModelSelection,
    Proposal,
    ProviderDiscovery,
    SelectionError,
)
from peer_policy import PROVIDERS  # noqa: E402

SCHEMA = "v1-peer-catalog/v1"
# Total wall-clock budget per provider (shared across version/auth/catalog probes).
# Slow auth probes such as `codex doctor --json` still fit; hung providers cannot
# multiply this by the number of probes.
DEFAULT_TIMEOUT_SECONDS = 45
PROFILE_NAMES = ("quality", "balanced", "fast", "custom")

__all__ = [
    "PROVIDERS",
    "SCHEMA",
    "build_candidates",
    "choose_model",
    "compare_preview_context",
    "prompt_fingerprints",
]


def effort_rank(level: str | None) -> int:
    return KNOWN_EFFORT_RANK.get(level or "none", 0)


def choose_model(
    provider: ProviderDiscovery,
    profile: str,
    requested_model: str | None = None,
    requested_reasoning: str | None = None,
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
    if requested_reasoning:
        normalized = effort_name(requested_reasoning)
        if normalized is None or (levels and normalized not in levels):
            return SelectionError(
                code="reasoning_level_unsupported",
                requested_reasoning=requested_reasoning,
                alternatives=tuple(levels),
            )
        selected_reasoning = normalized
    elif levels:
        if profile == "fast":
            selected_reasoning = min(levels, key=effort_rank)
        elif profile == "balanced":
            ordered = sorted(levels, key=effort_rank)
            selected_reasoning = ordered[max(0, len(ordered) - 2)]
        else:
            selected_reasoning = max(levels, key=effort_rank)
    else:
        selected_reasoning = None

    model_confidence: CatalogConfidence = (
        "unresolved" if explicit else catalog_confidence
    )
    return ModelSelection(
        model=selected.id,
        model_family=selected.family,
        reasoning=selected_reasoning,
        model_confidence=model_confidence,
        explicit=explicit,
    )


def candidate_sort_key(candidate: Candidate) -> tuple[int, int, int, int]:
    auth_score = {
        "eligible": 3,
        "explicit_api_mode": 1,
        "auth_not_verified": 1,
    }.get(candidate.auth.policy_state, 0)
    catalog_score = {"verified": 2, "unresolved": 0}.get(
        candidate.catalog_confidence, 0
    )
    reasoning_score = effort_rank(candidate.reasoning)
    return auth_score, catalog_score, reasoning_score, -candidate.provider_rank


def candidate_launch_state(
    provider: ProviderDiscovery,
    *,
    selection: ModelSelection,
) -> LaunchState:
    """Derive launch from the auth policy tag plus catalog/selection facts."""

    policy = provider.auth.policy_state
    if policy == "blocked_api_key_present":
        return "blocked_api_key_present"
    if policy == "not_authenticated":
        return "not_authenticated"
    if policy == "api_key_required":
        return "api_key_required"
    if policy in {"auth_not_verified", "not_installed"}:
        return "auth_unverified"
    # eligible | explicit_api_mode
    if provider.model_catalog.status != "resolved" and not selection.explicit:
        return "model_unresolved"
    if selection.model is None:
        return "model_unresolved"
    return "eligible"


def build_candidates(
    providers: list[ProviderDiscovery],
    profile: str,
    count: int,
    requested_cli: str | None,
    requested_model: str | None,
    requested_reasoning: str | None,
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
        use_reasoning = (
            requested_reasoning
            if requested_cli is None or provider.cli == requested_cli
            else None
        )
        # When a custom CLI filter is set, still propose defaults for others so
        # alternatives remain available without a second discovery pass.
        if requested_cli and provider.cli != requested_cli:
            use_model = None
            use_reasoning = None
        outcome = choose_model(provider, profile, use_model, use_reasoning)
        if isinstance(outcome, SelectionError):
            if requested_cli is None or provider.cli == requested_cli:
                errors.append({"cli": provider.cli, **outcome.to_dict()})
            continue
        selection = outcome
        launch_state = candidate_launch_state(provider, selection=selection)
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
                model_confidence=selection.model_confidence,
                provider_rank=provider_rank,
                launch_state=launch_state,
            )
        )

    ranked = sorted(universe, key=candidate_sort_key, reverse=True)
    pool = [
        candidate
        for candidate in ranked
        if requested_cli is None or candidate.cli == requested_cli
    ]
    eligible_pool = [
        candidate for candidate in pool if candidate.launch_state == "eligible"
    ]
    ineligible_pool = [
        candidate for candidate in pool if candidate.launch_state != "eligible"
    ]

    # Fill the recommended roster from eligible peers first. Family diversity
    # only competes among launchable candidates so an ineligible different
    # family cannot push out a second eligible peer.
    selected: list[Candidate] = []
    families: set[str] = set()
    for candidate in eligible_pool:
        if len(selected) >= count:
            break
        if candidate.model_family in families and any(
            other.model_family not in families for other in eligible_pool
        ):
            continue
        selected.append(candidate)
        families.add(candidate.model_family)
    if len(selected) < count:
        for candidate in eligible_pool:
            if candidate not in selected:
                selected.append(candidate)
            if len(selected) >= count:
                break
    if len(selected) < count:
        for candidate in ineligible_pool:
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
    eligible_count = sum(
        1 for candidate in roster if candidate.launch_state == "eligible"
    )
    # Explicit custom/model/reasoning failures are a rejected proposal, not a
    # successful discovery receipt with selection_errors buried in the body.
    if errors and (args.profile == "custom" or args.model or args.reasoning):
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {
                        "code": "selection_rejected",
                        "selection_errors": errors,
                    },
                },
                sort_keys=True,
            )
        )
        return 2
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
        eligible_count=eligible_count,
        roster_status="complete"
        if len(roster) >= args.count and eligible_count == len(roster)
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
