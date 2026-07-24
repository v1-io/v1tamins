#!/usr/bin/env python3
"""Single source of truth for peer provider IDs, key scrubbing, and specs."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

CatalogMode = Literal["command", "explicit_required"]

# These are names only. Values are never printed, hashed, or passed through in
# subscription_native mode. Provider-native OAuth variables remain available.
API_KEY_ENV_VARS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_API_KEY",
    "OPENAI_API_KEY",
    "OPENAI_AUTH_TOKEN",
    "CODEX_API_KEY",
    "CURSOR_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_GENAI_API_KEY",
)

PROVIDER_KEY_ENV_VARS = {
    "claude": ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_API_KEY"),
    "codex": ("OPENAI_API_KEY", "OPENAI_AUTH_TOKEN", "CODEX_API_KEY"),
    "cursor-agent": ("CURSOR_API_KEY",),
    "agy": ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY"),
}

PROVIDER_IDS = tuple(PROVIDER_KEY_ENV_VARS)


@dataclass(frozen=True)
class ProviderSpec:
    binary: str
    catalog_mode: CatalogMode
    catalog_args: tuple[str, ...] | None
    auth_args: tuple[str, ...] | None
    roles: tuple[str, ...]
    # Bound by peer_adapters after parser definitions to avoid import cycles.
    parse_auth: Callable[..., object] | None = None


PROVIDERS: dict[str, ProviderSpec] = {
    "claude": ProviderSpec(
        "claude",
        "explicit_required",
        None,
        ("auth", "status"),
        ("correctness/security", "structural review", "maintainability"),
    ),
    "codex": ProviderSpec(
        "codex",
        "explicit_required",
        None,
        ("doctor", "--json"),
        ("structural review", "correctness/security", "verification"),
    ),
    "cursor-agent": ProviderSpec(
        "cursor-agent",
        "command",
        ("--list-models",),
        ("status", "--format", "json"),
        ("structural review", "maintainability", "verification"),
    ),
    "agy": ProviderSpec(
        "agy",
        "command",
        ("models",),
        None,
        ("large-context", "multimodal", "research"),
    ),
}


def scrub_key_names() -> tuple[str, ...]:
    return API_KEY_ENV_VARS


def subscription_environment(mode: str) -> dict[str, str]:
    if mode not in {"subscription_native", "api_explicit"}:
        raise ValueError(f"unsupported auth mode: {mode}")

    environment = dict(os.environ)
    if mode == "subscription_native":
        for name in scrub_key_names():
            environment.pop(name, None)
    return environment


def emit_shell_unset() -> str:
    return "unset " + " ".join(scrub_key_names())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--emit-shell-unset",
        action="store_true",
        help="print a bash unset line for subscription_native scrubbing",
    )
    group.add_argument(
        "--emit-providers",
        action="store_true",
        help="print provider IDs as a | separated case pattern",
    )
    group.add_argument(
        "--require-provider",
        metavar="NAME",
        help="exit 0 when NAME is a supported provider ID, else 2",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.emit_shell_unset:
        print(emit_shell_unset())
        return 0
    if args.emit_providers:
        print("|".join(PROVIDER_IDS))
        return 0
    if args.require_provider is not None:
        if args.require_provider in PROVIDERS:
            return 0
        print(f"unsupported provider: {args.require_provider}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
