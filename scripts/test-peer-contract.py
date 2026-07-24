#!/usr/bin/env python3
"""Deterministic tests for dynamic peer discovery and selection."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "plugins/v1tamins/skills/v1-phone-a-friend/scripts/peer_catalog.py"
)
SPEC = importlib.util.spec_from_file_location("peer_catalog", MODULE_PATH)
assert SPEC and SPEC.loader
peer_catalog = importlib.util.module_from_spec(SPEC)
sys.modules["peer_catalog"] = peer_catalog
SPEC.loader.exec_module(peer_catalog)


class PeerContractTests(unittest.TestCase):
    def test_provider_catalog_changes_are_reflected_without_source_edits(self) -> None:
        first = peer_catalog.parse_model_catalog(
            json.dumps({"models": [{"id": "fake-alpha", "efforts": ["low"]}]})
        )
        second = peer_catalog.parse_model_catalog(
            json.dumps({"models": [{"id": "fake-beta", "efforts": ["high"]}]})
        )
        self.assertEqual([model["id"] for model in first], ["fake-alpha"])
        self.assertEqual([model["id"] for model in second], ["fake-beta"])

    def test_quality_and_fast_profiles_use_exposed_levels(self) -> None:
        provider = {
            "models": [
                {"id": "fake-fast", "family": "fast", "rank": 0, "reasoning_levels": ["low"]},
                {"id": "fake-strong", "family": "strong", "rank": 1, "reasoning_levels": ["low", "high"]},
            ],
            "reasoning_levels": ["low", "high"],
            "model_catalog": {"confidence": "verified"},
        }
        quality, quality_error = peer_catalog.choose_model(provider, "quality")
        fast, fast_error = peer_catalog.choose_model(provider, "fast")
        self.assertIsNone(quality_error)
        self.assertIsNone(fast_error)
        self.assertEqual(quality["model"], "fake-strong")
        self.assertEqual(quality["reasoning"], "high")
        self.assertEqual(fast["model"], "fake-fast")
        self.assertEqual(fast["reasoning"], "low")

    def test_unsupported_explicit_values_return_current_alternatives(self) -> None:
        provider = {
            "models": [{"id": "fake-current", "family": "fake", "rank": 0, "reasoning_levels": ["medium"]}],
            "reasoning_levels": ["medium"],
            "model_catalog": {"confidence": "verified"},
        }
        _, model_error = peer_catalog.choose_model(provider, "custom", "fake-old")
        _, effort_error = peer_catalog.choose_model(provider, "custom", "fake-current", "max")
        self.assertEqual(model_error["code"], "model_not_current")
        self.assertEqual(effort_error["code"], "reasoning_level_unsupported")
        self.assertEqual(effort_error["alternatives"], ["medium"])

    def test_malformed_catalog_is_unresolved(self) -> None:
        self.assertEqual(peer_catalog.parse_model_catalog("not a model catalog"), [])

    def test_subscription_environment_scrubs_keys_but_keeps_native_login(self) -> None:
        values = {
            "OPENAI_API_KEY": "redacted-openai",
            "ANTHROPIC_API_KEY": "redacted-anthropic",
            "CURSOR_API_KEY": "redacted-cursor",
            "CLAUDE_CODE_OAUTH_TOKEN": "native-oauth-token",
        }
        with mock.patch.dict(os.environ, values, clear=False):
            environment = peer_catalog.subscription_environment("subscription_native")
        self.assertNotIn("OPENAI_API_KEY", environment)
        self.assertNotIn("ANTHROPIC_API_KEY", environment)
        self.assertNotIn("CURSOR_API_KEY", environment)
        self.assertEqual(environment["CLAUDE_CODE_OAUTH_TOKEN"], "native-oauth-token")

    def test_provider_auth_only_considers_that_provider_key(self) -> None:
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "redacted"}, clear=True):
            auth = peer_catalog.auth_result(
                "claude",
                peer_catalog.PROVIDERS["claude"],
                "subscription_native",
                None,
            )
        self.assertEqual(auth["source"], "unverified")
        self.assertEqual(auth["policy_state"], "auth_not_verified")

    def test_quality_roster_prefers_different_families(self) -> None:
        def provider(cli: str, family: str, rank: int) -> dict[str, object]:
            return {
                "cli": cli,
                "installed": True,
                "version": "synthetic",
                "version_fingerprint": "version",
                "models": [{"id": f"{family}-current", "family": family, "rank": 0, "reasoning_levels": ["high"]}],
                "model_catalog": {"status": "resolved", "confidence": "verified", "fingerprint": "catalog"},
                "reasoning_levels": ["high"],
                "roles": ["structural review"],
                "auth": {"source": "subscription_native", "confidence": "verified", "policy_state": "eligible"},
                "workflow": "available",
            }

        selected, errors = peer_catalog.build_candidates(
            [provider("fake-a", "family-a", 0), provider("fake-b", "family-b", 1)],
            "quality",
            2,
            None,
            None,
            None,
        )
        self.assertEqual(errors, [])
        self.assertEqual({candidate["model_family"] for candidate in selected}, {"family-a", "family-b"})

    def test_unverified_auth_is_visible_but_not_launch_eligible(self) -> None:
        provider = {
            "cli": "fake-unverified",
            "installed": True,
            "version": "synthetic",
            "version_fingerprint": "version",
            "models": [{"id": "fake-current", "family": "fake", "rank": 0, "reasoning_levels": ["high"]}],
            "model_catalog": {"status": "resolved", "confidence": "verified", "fingerprint": "catalog"},
            "reasoning_levels": ["high"],
            "roles": ["structural review"],
            "auth": {"source": "unverified", "confidence": "unresolved", "policy_state": "auth_not_verified"},
            "workflow": "available",
        }
        selected, errors = peer_catalog.build_candidates([provider], "quality", 1, None, None, None)
        self.assertEqual(errors, [])
        self.assertFalse(selected[0]["eligible"])
        self.assertEqual(selected[0]["launch_state"], "auth_unverified")

    def test_prompt_fingerprint_changes_with_source(self) -> None:
        with mock.patch("pathlib.Path.is_file", return_value=True), mock.patch(
            "pathlib.Path.read_bytes", side_effect=[b"prompt-a", b"prompt-b"]
        ):
            first = peer_catalog.prompt_fingerprints(["prompt.md"])
            second = peer_catalog.prompt_fingerprints(["prompt.md"])
        self.assertNotEqual(first[0]["fingerprint"], second[0]["fingerprint"])

    def test_changed_preview_context_is_stale(self) -> None:
        preview = {
            "catalog_fingerprint": "old-catalog",
            "prompt_resolution": {"profile": "structural", "status": "resolved", "sources": []},
            "snapshot_fingerprint": "old-tree",
        }
        current = peer_catalog.compare_preview_context(
            preview,
            "new-catalog",
            {"profile": "structural", "status": "resolved", "sources": []},
            "new-tree",
        )
        self.assertEqual(current["status"], "context_stale")
        self.assertEqual(current["reasons"], ["catalog_changed", "working_tree_changed"])

    def test_shared_sources_do_not_pin_concrete_model_ids(self) -> None:
        source_paths = [
            REPO_ROOT / "plugins/v1tamins/skills/v1-phone-a-friend/SKILL.md",
            REPO_ROOT / "plugins/v1tamins/skills/v1-phone-a-friend/references/model-selection.md",
            REPO_ROOT / "plugins/v1tamins/skills/v1-review-board/SKILL.md",
            REPO_ROOT / "plugins/v1tamins/skills/v1-review-board/references/review-contract.md",
        ]
        concrete_id = re.compile(r"\b(?:gpt|claude|gemini|sonnet|opus)[-_][0-9]", re.IGNORECASE)
        for path in source_paths:
            self.assertIsNone(concrete_id.search(path.read_text(encoding="utf-8")), path)


if __name__ == "__main__":
    unittest.main()
