#!/usr/bin/env python3
"""Deterministic tests for dynamic peer discovery and selection."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

sys.dont_write_bytecode = True


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins/v1tamins/skills/v1-phone-a-friend/scripts"
sys.path.insert(0, str(SCRIPTS))

MODULE_PATH = SCRIPTS / "peer_catalog.py"
SPEC = importlib.util.spec_from_file_location("peer_catalog", MODULE_PATH)
assert SPEC and SPEC.loader
peer_catalog = importlib.util.module_from_spec(SPEC)
sys.modules["peer_catalog"] = peer_catalog
SPEC.loader.exec_module(peer_catalog)

import peer_adapters  # noqa: E402
import peer_launch  # noqa: E402
import peer_models  # noqa: E402
import peer_policy  # noqa: E402
import peer_verdict  # noqa: E402


def provider_from_dict(payload: dict[str, Any]) -> peer_models.ProviderDiscovery:
    """Test-edge coercion from dict fixtures into typed discovery records."""

    auth_payload = payload["auth"]
    if isinstance(auth_payload, peer_models.AuthFact):
        auth = auth_payload
    else:
        auth = peer_models.AuthFact(
            policy_state=auth_payload["policy_state"],
            key_env_names=tuple(auth_payload.get("key_env_names", ())),
        )
    models = tuple(
        model
        if isinstance(model, peer_models.ModelEntry)
        else peer_models.ModelEntry(
            id=model["id"],
            family=model.get("family", peer_adapters.model_family(model["id"])),
            reasoning_levels=tuple(
                model.get("reasoning_levels") or model.get("efforts") or ()
            ),
            rank=int(model.get("rank", 0)),
        )
        for model in payload.get("models", [])
    )
    catalog_payload = payload["model_catalog"]
    if isinstance(catalog_payload, peer_models.ModelCatalog):
        catalog = catalog_payload
    else:
        catalog = peer_models.ModelCatalog(
            status=catalog_payload.get("status", "unresolved"),
            confidence=catalog_payload.get("confidence", "unresolved"),
            source=catalog_payload.get("source"),
            fingerprint=catalog_payload.get("fingerprint"),
        )
    return peer_models.ProviderDiscovery(
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
    )


def make_provider(
    *,
    cli: str = "fake",
    installed: bool = True,
    models: list[dict] | None = None,
    reasoning_levels: list[str] | None = None,
    catalog_status: str = "resolved",
    catalog_confidence: str = "verified",
    policy_state: str = "eligible",
    roles: list[str] | None = None,
    version: str = "synthetic",
    version_fingerprint: str = "version",
    catalog_fingerprint: str | None = "catalog",
    key_env_names: tuple[str, ...] = (),
) -> peer_models.ProviderDiscovery:
    payload: dict = {
        "cli": cli,
        "installed": installed,
        "version": version,
        "version_fingerprint": version_fingerprint,
        "models": models or [],
        "reasoning_levels": reasoning_levels
        or (
            sorted(
                {
                    level
                    for model in (models or [])
                    for level in model.get("reasoning_levels", [])
                }
            )
        ),
        "model_catalog": {
            "status": catalog_status,
            "confidence": catalog_confidence,
            "fingerprint": catalog_fingerprint,
        },
        "auth": {
            "policy_state": policy_state,
            "key_env_names": list(key_env_names),
        },
        "roles": roles or ["structural review"],
    }
    return provider_from_dict(payload)


class PeerContractTests(unittest.TestCase):
    def test_provider_catalog_contains_only_supported_cli_surfaces(self) -> None:
        self.assertEqual(
            set(peer_policy.PROVIDERS),
            {"claude", "codex", "cursor-agent", "agy"},
        )
        self.assertEqual(set(peer_catalog.PROVIDERS), set(peer_policy.PROVIDERS))
        self.assertNotIn("oracle", peer_policy.PROVIDERS)
        self.assertNotIn("gemini", peer_policy.PROVIDERS)
        self.assertEqual(peer_policy.PROVIDERS["claude"].catalog_mode, "explicit_required")
        self.assertEqual(peer_policy.PROVIDERS["codex"].catalog_mode, "explicit_required")
        self.assertEqual(peer_policy.PROVIDERS["cursor-agent"].catalog_mode, "command")
        self.assertFalse(hasattr(peer_policy.ProviderSpec, "parse_auth"))

    def test_provider_catalog_changes_are_reflected_without_source_edits(self) -> None:
        first = peer_adapters.parse_model_catalog(
            json.dumps({"models": [{"id": "fake-alpha", "efforts": ["low"]}]})
        )
        second = peer_adapters.parse_model_catalog(
            json.dumps({"models": [{"id": "fake-beta", "efforts": ["high"]}]})
        )
        self.assertEqual([model.id for model in first], ["fake-alpha"])
        self.assertEqual([model.id for model in second], ["fake-beta"])

    def test_cursor_list_models_line_shape(self) -> None:
        models = peer_adapters.parse_model_catalog(
            "Available models\nauto - Auto (default)\ngpt-demo-high - Demo High\n"
        )
        self.assertEqual([model.id for model in models], ["auto", "gpt-demo-high"])
        self.assertIn("high", models[1].reasoning_levels)

    def test_line_catalog_rejects_diagnostic_prose(self) -> None:
        models = peer_adapters.parse_model_catalog(
            "Warning: using cached credentials\n"
            "error: temporary upstream failure\n"
            "real-model-high\n"
        )
        self.assertEqual([model.id for model in models], ["real-model-high"])

    def test_agy_multiword_model_names_are_preserved(self) -> None:
        models = peer_adapters.parse_model_catalog(
            "* Gemini 3.5 Flash (Medium)\n"
            "GPT-OSS 120B (Medium)\n"
            "gemini-3.5-flash-medium\n"
        )
        self.assertEqual(
            [model.id for model in models],
            [
                "Gemini 3.5 Flash (Medium)",
                "GPT-OSS 120B (Medium)",
                "gemini-3.5-flash-medium",
            ],
        )

    def test_api_explicit_discovery_env_keeps_only_selected_provider_keys(self) -> None:
        values = {
            "OPENAI_API_KEY": "redacted-openai",
            "ANTHROPIC_API_KEY": "redacted-anthropic",
            "CURSOR_API_KEY": "redacted-cursor",
        }
        with mock.patch.dict(os.environ, values, clear=False):
            codex_env = peer_policy.subscription_environment("api_explicit", "codex")
            claude_env = peer_policy.subscription_environment("api_explicit", "claude")
        self.assertEqual(codex_env.get("OPENAI_API_KEY"), "redacted-openai")
        self.assertNotIn("ANTHROPIC_API_KEY", codex_env)
        self.assertNotIn("CURSOR_API_KEY", codex_env)
        self.assertEqual(claude_env.get("ANTHROPIC_API_KEY"), "redacted-anthropic")
        self.assertNotIn("OPENAI_API_KEY", claude_env)

    def test_quality_and_fast_profiles_use_exposed_levels(self) -> None:
        provider = make_provider(
            models=[
                {
                    "id": "fake-fast",
                    "family": "fast",
                    "rank": 0,
                    "reasoning_levels": ["low"],
                },
                {
                    "id": "fake-strong",
                    "family": "strong",
                    "rank": 1,
                    "reasoning_levels": ["low", "high"],
                },
            ],
            reasoning_levels=["low", "high"],
        )
        quality = peer_catalog.choose_model(provider, "quality")
        fast = peer_catalog.choose_model(provider, "fast")
        self.assertEqual(quality.model, "fake-strong")
        self.assertEqual(quality.reasoning, "high")
        self.assertEqual(fast.model, "fake-fast")
        self.assertEqual(fast.reasoning, "low")

    def test_unsupported_explicit_values_return_current_alternatives(self) -> None:
        provider = make_provider(
            models=[
                {
                    "id": "fake-current",
                    "family": "fake",
                    "rank": 0,
                    "reasoning_levels": ["medium"],
                }
            ],
            reasoning_levels=["medium"],
        )
        model_error = peer_catalog.choose_model(provider, "custom", "fake-old")
        reasoning_error = peer_catalog.choose_model(
            provider, "custom", "fake-current", "max"
        )
        self.assertEqual(model_error.code, "model_not_current")
        self.assertEqual(reasoning_error.code, "reasoning_level_unsupported")
        self.assertEqual(list(reasoning_error.alternatives), ["medium"])
        self.assertEqual(reasoning_error.requested_reasoning, "max")

    def test_explicit_reasoning_rejected_when_catalog_exposes_no_levels(self) -> None:
        provider = make_provider(
            models=[
                {
                    "id": "fake-current",
                    "family": "fake",
                    "rank": 0,
                    "reasoning_levels": [],
                }
            ],
            reasoning_levels=[],
        )
        reasoning_error = peer_catalog.choose_model(
            provider, "custom", "fake-current", "high"
        )
        self.assertEqual(reasoning_error.code, "reasoning_level_unsupported")
        self.assertEqual(list(reasoning_error.alternatives), [])
        self.assertEqual(reasoning_error.requested_reasoning, "high")

    def test_custom_explicit_model_when_catalog_empty(self) -> None:
        provider = make_provider(
            cli="cursor-agent",
            models=[],
            catalog_status="unresolved",
            catalog_confidence="unresolved",
            catalog_fingerprint=None,
            reasoning_levels=[],
        )
        selection = peer_catalog.choose_model(provider, "custom", "auto")
        self.assertEqual(selection.model, "auto")
        self.assertTrue(selection.explicit)
        self.assertEqual(selection.model_confidence, "unresolved")
        selected, alternatives, errors = peer_catalog.build_candidates(
            [provider], "custom", 1, "cursor-agent", "auto", None
        )
        self.assertEqual(errors, [])
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].launch_state, "eligible")
        self.assertEqual(alternatives, [])

    def test_catalog_less_installed_peer_is_visible_ineligible_candidate(self) -> None:
        provider = make_provider(
            cli="claude",
            models=[],
            catalog_status="unresolved",
            catalog_confidence="unresolved",
            catalog_fingerprint=None,
            reasoning_levels=[],
        )
        selected, alternatives, errors = peer_catalog.build_candidates(
            [provider], "quality", 1, None, None, None
        )
        self.assertEqual(errors, [])
        self.assertEqual(len(selected), 1)
        self.assertIsNone(selected[0].model)
        self.assertEqual(selected[0].launch_state, "model_unresolved")
        self.assertNotIn("eligible", selected[0].to_dict())
        self.assertEqual(alternatives, [])

    def test_malformed_catalog_is_unresolved(self) -> None:
        self.assertEqual(peer_adapters.parse_model_catalog("not a model catalog"), [])

    def test_failed_provider_catalog_with_output_stays_unresolved(self) -> None:
        results = [
            peer_adapters.CommandResult(0, "agy 1.0\n", ""),
            peer_adapters.CommandResult(
                3, '{"models":[{"id":"should-not-resolve"}]}', ""
            ),
        ]
        with (
            mock.patch.object(peer_adapters.shutil, "which", return_value="/fake/agy"),
            mock.patch.object(peer_adapters, "run_command", side_effect=results),
        ):
            discovered = peer_adapters.discover_provider(
                "agy", "subscription_native", 1
            )
        self.assertEqual(discovered.models, ())
        self.assertEqual(discovered.model_catalog.status, "unresolved")
        self.assertFalse(hasattr(discovered, "workflow"))

    def test_subscription_environment_scrubs_keys_but_keeps_native_login(self) -> None:
        values = {
            "OPENAI_API_KEY": "redacted-openai",
            "ANTHROPIC_API_KEY": "redacted-anthropic",
            "CURSOR_API_KEY": "redacted-cursor",
            "CLAUDE_CODE_OAUTH_TOKEN": "native-oauth-token",
        }
        with mock.patch.dict(os.environ, values, clear=False):
            environment = peer_policy.subscription_environment("subscription_native")
            unset_line = peer_policy.emit_shell_unset()
        self.assertNotIn("OPENAI_API_KEY", environment)
        self.assertNotIn("ANTHROPIC_API_KEY", environment)
        self.assertNotIn("CURSOR_API_KEY", environment)
        self.assertEqual(environment["CLAUDE_CODE_OAUTH_TOKEN"], "native-oauth-token")
        self.assertTrue(unset_line.startswith("unset "))
        for name in peer_policy.scrub_key_names():
            self.assertIn(name, unset_line)

    def test_provider_auth_only_considers_that_provider_key(self) -> None:
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "redacted"}, clear=True):
            auth = peer_adapters.auth_result(
                "claude",
                peer_policy.PROVIDERS["claude"],
                "subscription_native",
                None,
            )
        self.assertEqual(auth.policy_state, "auth_not_verified")

    def test_ambient_key_blocks_matching_provider_only(self) -> None:
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "redacted"}, clear=True):
            auth = peer_adapters.auth_result(
                "codex",
                peer_policy.PROVIDERS["codex"],
                "subscription_native",
                None,
            )
        self.assertEqual(auth.policy_state, "blocked_api_key_present")
        self.assertEqual(auth.key_env_names, ("OPENAI_API_KEY",))
        provider = make_provider(
            cli="codex",
            policy_state="blocked_api_key_present",
            key_env_names=("OPENAI_API_KEY",),
            models=[
                {
                    "id": "fake-current",
                    "family": "fake",
                    "rank": 0,
                    "reasoning_levels": ["high"],
                }
            ],
        )
        selected, _, errors = peer_catalog.build_candidates(
            [provider], "quality", 1, None, None, None
        )
        self.assertEqual(errors, [])
        self.assertEqual(selected[0].launch_state, "blocked_api_key_present")

    def test_not_authenticated_and_api_key_required_stay_distinct(self) -> None:
        logged_out = make_provider(
            cli="codex",
            policy_state="not_authenticated",
            models=[
                {
                    "id": "fake-current",
                    "family": "fake",
                    "rank": 0,
                    "reasoning_levels": ["high"],
                }
            ],
        )
        missing_key = make_provider(
            cli="claude",
            policy_state="api_key_required",
            models=[
                {
                    "id": "fake-current",
                    "family": "fake",
                    "rank": 0,
                    "reasoning_levels": ["high"],
                }
            ],
        )
        selected, _, errors = peer_catalog.build_candidates(
            [logged_out, missing_key], "quality", 2, None, None, None
        )
        self.assertEqual(errors, [])
        states = {item.cli: item.launch_state for item in selected}
        self.assertEqual(states["codex"], "not_authenticated")
        self.assertEqual(states["claude"], "api_key_required")

    def test_codex_doctor_chatgpt_auth_shape_is_recognized(self) -> None:
        doctor = {
            "overallStatus": "fail",
            "checks": {
                "auth.credentials": {
                    "status": "ok",
                    "details": {
                        "stored ChatGPT tokens": "true",
                        "stored auth mode": "chatgpt",
                    },
                },
                "network.provider_reachability": {"status": "ok"},
            },
        }
        self.assertEqual(peer_adapters.parse_codex_doctor_auth(doctor), "eligible")
        with mock.patch.dict(os.environ, {}, clear=True):
            auth = peer_adapters.auth_result(
                "codex",
                peer_policy.PROVIDERS["codex"],
                "subscription_native",
                peer_adapters.CommandResult(0, json.dumps(doctor), ""),
            )
        self.assertEqual(auth.policy_state, "eligible")

    def test_codex_doctor_verified_logout_is_not_authenticated(self) -> None:
        doctor = {
            "checks": {
                "auth.credentials": {
                    "status": "ok",
                    "details": {
                        "stored ChatGPT tokens": "false",
                        "stored auth mode": "none",
                    },
                }
            }
        }
        self.assertEqual(
            peer_adapters.parse_codex_doctor_auth(doctor), "not_authenticated"
        )
        with mock.patch.dict(os.environ, {}, clear=True):
            auth = peer_adapters.auth_result(
                "codex",
                peer_policy.PROVIDERS["codex"],
                "subscription_native",
                peer_adapters.CommandResult(0, json.dumps(doctor), ""),
            )
        self.assertEqual(auth.policy_state, "not_authenticated")

    def test_provider_without_auth_probe_is_launchable_when_catalog_resolves(
        self,
    ) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            auth = peer_adapters.auth_result(
                "agy",
                peer_policy.PROVIDERS["agy"],
                "subscription_native",
                None,
            )
        self.assertEqual(auth.policy_state, "eligible")
        provider = make_provider(
            cli="agy",
            policy_state="eligible",
            models=[
                {
                    "id": "fake-agy",
                    "family": "gemini",
                    "rank": 0,
                    "reasoning_levels": ["high"],
                }
            ],
        )
        selected, _, errors = peer_catalog.build_candidates(
            [provider], "quality", 1, None, None, None
        )
        self.assertEqual(errors, [])
        self.assertEqual(selected[0].launch_state, "eligible")

    def test_claude_structured_auth_uses_logged_in(self) -> None:
        payload = {
            "loggedIn": True,
            "authMethod": "claude.ai",
            "apiKeySource": "none",
        }
        with mock.patch.dict(os.environ, {}, clear=True):
            auth = peer_adapters.auth_result(
                "claude",
                peer_policy.PROVIDERS["claude"],
                "subscription_native",
                peer_adapters.CommandResult(0, json.dumps(payload), ""),
            )
        self.assertEqual(auth.policy_state, "eligible")
        self.assertIn("claude", peer_adapters.AUTH_PARSERS)

    def test_quality_roster_prefers_eligible_over_ineligible_diversity(self) -> None:
        selected, alternatives, errors = peer_catalog.build_candidates(
            [
                make_provider(
                    cli="eligible-a",
                    models=[
                        {
                            "id": "family-a-1-high",
                            "family": "family-a",
                            "rank": 0,
                            "reasoning_levels": ["high"],
                        }
                    ],
                ),
                make_provider(
                    cli="eligible-b",
                    models=[
                        {
                            "id": "family-a-2-high",
                            "family": "family-a",
                            "rank": 0,
                            "reasoning_levels": ["high"],
                        }
                    ],
                ),
                make_provider(
                    cli="ineligible-c",
                    policy_state="auth_not_verified",
                    models=[
                        {
                            "id": "family-b-1-high",
                            "family": "family-b",
                            "rank": 0,
                            "reasoning_levels": ["high"],
                        }
                    ],
                ),
            ],
            "quality",
            2,
            None,
            None,
            None,
        )
        self.assertEqual(errors, [])
        self.assertEqual(
            {candidate.cli for candidate in selected},
            {"eligible-a", "eligible-b"},
        )
        self.assertTrue(all(item.launch_state == "eligible" for item in selected))
        self.assertEqual(alternatives[0].cli, "ineligible-c")

    def test_quality_roster_prefers_different_families(self) -> None:
        selected, alternatives, errors = peer_catalog.build_candidates(
            [
                make_provider(
                    cli="fake-a",
                    models=[
                        {
                            "id": "family-a-current",
                            "family": "family-a",
                            "rank": 0,
                            "reasoning_levels": ["high"],
                        }
                    ],
                ),
                make_provider(
                    cli="fake-b",
                    models=[
                        {
                            "id": "family-b-current",
                            "family": "family-b",
                            "rank": 0,
                            "reasoning_levels": ["high"],
                        }
                    ],
                ),
            ],
            "quality",
            2,
            None,
            None,
            None,
        )
        self.assertEqual(errors, [])
        self.assertEqual(
            {candidate.model_family for candidate in selected},
            {"family-a", "family-b"},
        )
        self.assertEqual(alternatives, [])

    def test_alternatives_built_without_rebuild(self) -> None:
        providers = [
            make_provider(
                cli=cli,
                version_fingerprint=f"v{index}",
                catalog_fingerprint=f"c{index}",
                models=[
                    {
                        "id": f"{cli}-model",
                        "family": f"family-{index}",
                        "rank": 0,
                        "reasoning_levels": ["high"],
                    }
                ],
            )
            for index, cli in enumerate(("fake-a", "fake-b", "fake-c"))
        ]
        selected, alternatives, errors = peer_catalog.build_candidates(
            providers, "quality", 1, None, None, None
        )
        self.assertEqual(errors, [])
        self.assertEqual(len(selected), 1)
        self.assertEqual(len(alternatives), 2)
        selected_keys = {(item.cli, item.model) for item in selected}
        for alt in alternatives:
            self.assertNotIn((alt.cli, alt.model), selected_keys)

    def test_unverified_auth_is_visible_but_not_launch_eligible(self) -> None:
        provider = make_provider(
            cli="fake-unverified",
            policy_state="auth_not_verified",
            models=[
                {
                    "id": "fake-current",
                    "family": "fake",
                    "rank": 0,
                    "reasoning_levels": ["high"],
                }
            ],
        )
        selected, _alternatives, errors = peer_catalog.build_candidates(
            [provider], "quality", 1, None, None, None
        )
        self.assertEqual(errors, [])
        self.assertEqual(selected[0].launch_state, "auth_unverified")

    def test_prompt_fingerprint_changes_with_source(self) -> None:
        with (
            mock.patch("pathlib.Path.is_file", return_value=True),
            mock.patch(
                "pathlib.Path.read_bytes", side_effect=[b"prompt-a", b"prompt-b"]
            ),
        ):
            first = peer_catalog.prompt_fingerprints(["prompt.md"])
            second = peer_catalog.prompt_fingerprints(["prompt.md"])
        self.assertNotEqual(first[0]["fingerprint"], second[0]["fingerprint"])

    def test_changed_preview_context_is_stale(self) -> None:
        preview = {
            "catalog_fingerprint": "old-catalog",
            "prompt_resolution": {
                "profile": "structural",
                "status": "resolved",
                "sources": [],
            },
            "snapshot_fingerprint": "old-tree",
        }
        current = peer_catalog.compare_preview_context(
            preview,
            "new-catalog",
            {"profile": "structural", "status": "resolved", "sources": []},
            "new-tree",
        )
        self.assertEqual(current["status"], "context_stale")
        self.assertEqual(
            current["reasons"], ["catalog_changed", "working_tree_changed"]
        )

    def test_typed_models_round_trip(self) -> None:
        auth = peer_models.AuthFact.eligible()
        payload = auth.to_dict()
        self.assertEqual(payload["policy_state"], "eligible")
        self.assertIsInstance(payload["key_env_names"], list)
        self.assertNotIn("source", payload)
        self.assertNotIn("confidence", payload)
        self.assertEqual(
            peer_models.AuthFact.not_authenticated().policy_state, "not_authenticated"
        )
        self.assertEqual(
            peer_models.AuthFact.unverified().policy_state, "auth_not_verified"
        )

    def test_model_entry_emits_efforts_alias_only(self) -> None:
        entry = peer_models.ModelEntry(
            id="demo", family="demo", reasoning_levels=("high",), rank=0
        )
        payload = entry.to_dict()
        self.assertEqual(payload["reasoning_levels"], ["high"])
        self.assertEqual(payload["efforts"], ["high"])
        self.assertFalse(hasattr(entry, "efforts"))

    def test_shared_sources_do_not_pin_concrete_model_ids(self) -> None:
        source_paths = [
            REPO_ROOT / "plugins/v1tamins/skills/v1-phone-a-friend/SKILL.md",
            REPO_ROOT
            / "plugins/v1tamins/skills/v1-phone-a-friend/references/model-selection.md",
            REPO_ROOT / "plugins/v1tamins/skills/v1-review-board/SKILL.md",
            REPO_ROOT
            / "plugins/v1tamins/skills/v1-review-board/references/review-contract.md",
        ]
        concrete_id = re.compile(
            r"\b(?:gpt|claude|gemini|sonnet|opus)[-_][0-9]", re.IGNORECASE
        )
        for path in source_paths:
            self.assertIsNone(
                concrete_id.search(path.read_text(encoding="utf-8")), path
            )


class SubscriptionDiscoveryTests(unittest.TestCase):
    """Discovery must only propose what the installed CLI can actually launch."""

    def test_tab_separated_catalog_resolves_ids_and_levels(self) -> None:
        parsed = peer_adapters.parse_catalog(
            "MODEL\tDESCRIPTION\n"
            "fake-strong\tFake Strong (High)\n"
            "fake-fast-low\tFake Fast\n"
        )
        self.assertEqual(parsed.catalog_format, "tsv")
        self.assertEqual([model.id for model in parsed.models], ["fake-strong", "fake-fast-low"])
        self.assertEqual(parsed.models[0].reasoning_levels, ("high",))
        self.assertEqual(parsed.models[1].reasoning_levels, ("low",))

    def test_catalog_formats_are_reported(self) -> None:
        self.assertEqual(
            peer_adapters.parse_catalog(
                json.dumps({"models": [{"id": "fake-strong"}]})
            ).catalog_format,
            "json",
        )
        self.assertEqual(
            peer_adapters.parse_catalog("fake-strong - Fake Strong").catalog_format,
            "id_dash_label",
        )
        self.assertEqual(
            peer_adapters.parse_catalog("fake-strong\n").catalog_format, "lines"
        )
        self.assertEqual(
            peer_adapters.parse_catalog("not a model catalog").catalog_format,
            "unresolved",
        )

    def test_label_effort_reads_only_a_trailing_qualifier(self) -> None:
        self.assertEqual(peer_adapters.label_effort("Fake Strong (High)"), "high")
        self.assertEqual(peer_adapters.label_effort("Fake Strong - Max"), "max")
        # A level word elsewhere in the label is not a reasoning level.
        self.assertIsNone(peer_adapters.label_effort("Max context 200k window"))
        self.assertIsNone(peer_adapters.label_effort("Fake Strong"))

    def test_label_never_overrides_a_level_encoded_in_the_id(self) -> None:
        parsed = peer_adapters.parse_catalog("fake-strong-low\tFake Strong (High)\n")
        self.assertEqual(parsed.models[0].reasoning_levels, ("low",))

    def test_alias_provider_resolves_a_named_model_and_level(self) -> None:
        # A subscription CLI with no catalog command still selects by alias.
        provider = make_provider(
            cli="claude",
            models=[],
            catalog_status="unresolved",
            catalog_confidence="unresolved",
            catalog_fingerprint=None,
            reasoning_levels=[],
        )
        with mock.patch.dict(os.environ, {}, clear=True):
            selection = peer_catalog.choose_model(
                provider, "custom", "fake-alias", "high"
            )
        self.assertEqual(selection.model, "fake-alias")
        self.assertEqual(selection.representation, "alias")
        self.assertEqual(selection.launch_model, "fake-alias")
        self.assertEqual(selection.reasoning, "high")
        self.assertEqual(selection.model_confidence, "unresolved")
        self.assertEqual(selection.reasoning_confidence, "unresolved")
        selected, _alternatives, errors = peer_catalog.build_candidates(
            [provider], "custom", 1, "claude", "fake-alias", "high"
        )
        self.assertEqual(errors, [])
        self.assertEqual(selected[0].launch_state, "eligible")
        self.assertEqual(selected[0].launch_model_argument, "fake-alias")
        self.assertEqual(selected[0].representation, "alias")

    def test_alias_level_still_rejected_without_a_provider_effort_option(self) -> None:
        provider = make_provider(
            cli="codex",
            models=[],
            catalog_status="unresolved",
            catalog_confidence="unresolved",
            catalog_fingerprint=None,
            reasoning_levels=[],
        )
        outcome = peer_catalog.choose_model(provider, "custom", "fake-alias", "high")
        self.assertEqual(outcome.code, "reasoning_level_unsupported")
        # The same alias with the level encoded in the ID resolves.
        resolved = peer_catalog.choose_model(
            provider, "custom", "fake-alias-high", "high"
        )
        self.assertEqual(resolved.launch_model, "fake-alias-high")

    def test_selection_without_a_launch_argument_is_typed_and_ineligible(self) -> None:
        # The catalog advertises a level the model argument cannot carry.
        provider = make_provider(
            cli="cursor-agent",
            models=[{"id": "auto", "family": "auto", "rank": 0, "reasoning_levels": ["high"]}],
            reasoning_levels=["high"],
        )
        selection = peer_catalog.choose_model(provider, "quality")
        self.assertEqual(selection.model, "auto")
        self.assertIsNone(selection.launch_model)
        selected, _alternatives, errors = peer_catalog.build_candidates(
            [provider], "quality", 1, None, None, None
        )
        self.assertEqual(errors, [])
        self.assertEqual(selected[0].launch_state, "launch_unrepresentable")
        self.assertIsNone(selected[0].launch_model_argument)
        self.assertEqual(selected[0].catalog_model_id, "auto")

    def test_selection_prefers_a_launchable_model_over_an_unlaunchable_one(self) -> None:
        provider = make_provider(
            cli="cursor-agent",
            models=[
                {"id": "auto", "family": "auto", "rank": 0, "reasoning_levels": ["high"]},
                {
                    "id": "fake-strong-high",
                    "family": "strong",
                    "rank": 1,
                    "reasoning_levels": ["high"],
                },
            ],
            reasoning_levels=["high"],
        )
        selection = peer_catalog.choose_model(provider, "quality")
        self.assertEqual(selection.model, "fake-strong-high")
        self.assertEqual(selection.launch_model, "fake-strong-high")
        self.assertEqual(selection.representation, "catalog")

    def test_selection_and_launch_share_one_representability_rule(self) -> None:
        for model, reasoning, expected in (
            ("fake-strong-high", "high", True),
            ("fake-strong", "high", False),
            ("fake-strong", None, True),
        ):
            self.assertEqual(
                peer_adapters.reasoning_encoded_in_model(model, reasoning), expected
            )
            recipe = peer_launch.build_recipe(
                "cursor-agent",
                permission="readonly",
                prompt="SYNTHETIC PROMPT",
                model=model,
                reasoning=reasoning,
            )
            self.assertEqual(isinstance(recipe, peer_launch.LaunchRecipe), expected)

    def test_alias_discovery_never_exposes_api_keys(self) -> None:
        values = {name: "redacted" for name in peer_policy.API_KEY_ENV_VARS}
        with mock.patch.dict(os.environ, values, clear=False):
            environment = peer_policy.subscription_environment("subscription_native")
        for name in peer_policy.API_KEY_ENV_VARS:
            self.assertNotIn(name, environment)

    def test_catalog_format_reaches_the_discovery_receipt(self) -> None:
        results = [
            peer_adapters.CommandResult(0, "agy 1.0\n", ""),
            peer_adapters.CommandResult(0, "fake-strong\tFake Strong (High)\n", ""),
        ]
        with (
            mock.patch.object(peer_adapters.shutil, "which", return_value="/fake/agy"),
            mock.patch.object(peer_adapters, "run_command", side_effect=results),
        ):
            discovered = peer_adapters.discover_provider("agy", "subscription_native", 1)
        self.assertEqual(discovered.model_catalog.catalog_format, "tsv")
        self.assertEqual(discovered.model_catalog.status, "resolved")
        self.assertEqual([model.id for model in discovered.models], ["fake-strong"])
        self.assertIn("catalog_format", discovered.model_catalog.to_dict())


def stream(*events: dict[str, Any]) -> str:
    return "".join(json.dumps(event) + "\n" for event in events)


def wrapper_blocks(markdown: str) -> list[tuple[str, ...]]:
    """Tokenize every fenced credential-wrapper example in a templates file."""

    blocks: list[tuple[str, ...]] = []
    current: list[str] | None = None
    for line in markdown.splitlines():
        if line.startswith("```"):
            if current is not None:
                text = "\n".join(current)
                if text.lstrip().startswith('"$PEER_ENV"'):
                    blocks.append(tuple(shlex.split(text.replace("\\\n", " "))))
                current = None
            elif line.strip() == "```bash":
                current = []
            continue
        if current is not None:
            current.append(line)
    return blocks


class PeerLaunchTests(unittest.TestCase):
    """Provider argv construction, refusals, and doc/adapter agreement."""

    def recipe(self, cli: str, **kwargs: Any) -> Any:
        kwargs.setdefault("permission", "readonly")
        kwargs.setdefault("prompt", "SYNTHETIC PROMPT")
        return peer_launch.build_recipe(cli, **kwargs)

    def test_every_supported_provider_has_a_launch_adapter(self) -> None:
        self.assertEqual(set(peer_launch.BUILDERS), set(peer_policy.PROVIDERS))
        self.assertEqual(set(peer_launch.BINARIES), set(peer_policy.PROVIDERS))
        self.assertEqual(set(peer_launch.VARIADIC_FLAGS), set(peer_policy.PROVIDERS))

    def test_prompt_is_always_the_final_argument(self) -> None:
        contexts = {
            "codex": peer_launch.LaunchContext(repo="/synthetic/repo"),
            "cursor-agent": peer_launch.LaunchContext(worktree="synthetic-tree"),
        }
        for cli in peer_policy.PROVIDERS:
            for permission in peer_launch.PERMISSION_MODES:
                recipe = self.recipe(
                    cli,
                    permission=permission,
                    model="fake-strong",
                    context=contexts.get(cli, peer_launch.LaunchContext()),
                )
                self.assertIsInstance(recipe, peer_launch.LaunchRecipe, (cli, permission))
                self.assertEqual(recipe.argv[-1], "SYNTHETIC PROMPT", (cli, permission))
                self.assertEqual(recipe.prompt_placement, "final_positional")

    def test_claude_stream_json_carries_its_companion_flag(self) -> None:
        recipe = self.recipe("claude", model="fake-strong", reasoning="high")
        self.assertIn("--verbose", recipe.argv)
        index = recipe.argv.index("--output-format")
        self.assertEqual(recipe.argv[index + 1], "stream-json")
        self.assertEqual(recipe.reasoning_argument, "high")
        self.assertEqual(
            recipe.argv[recipe.argv.index("--effort") + 1], "high"
        )

    def test_claude_readonly_restricts_tools_and_mcp(self) -> None:
        recipe = self.recipe("claude", model="fake-strong")
        self.assertIn("--strict-mcp-config", recipe.argv)
        self.assertIn("--tools=Read,Grep,Glob", recipe.argv)
        self.assertIn("--allowedTools=Read,Grep,Glob", recipe.argv)
        self.assertIn("--disallowedTools=Edit,Write,Bash,mcp__*", recipe.argv)
        self.assertNotIn("bypassPermissions", recipe.argv)

    def test_variadic_options_attach_their_value(self) -> None:
        # A bare variadic pair would let the parser reach the prompt.
        for name in peer_launch.VARIADIC_FLAGS["claude"]:
            self.assertEqual(
                peer_launch.option("claude", name, "value"), [f"{name}=value"]
            )
        self.assertEqual(
            peer_launch.option("codex", "--cd", "/synthetic/repo"),
            ["--cd", "/synthetic/repo"],
        )

    def test_prompt_next_to_a_variadic_option_is_refused(self) -> None:
        outcome = peer_launch.finalize(
            "claude", ["claude", "-p", "--add-dir"], "SYNTHETIC PROMPT"
        )
        self.assertIsInstance(outcome, peer_launch.LaunchError)
        self.assertEqual(outcome.code, "launch_recipe_unresolved")
        self.assertEqual(outcome.missing_flags, ("--add-dir",))

    def test_codex_requires_an_explicit_working_directory(self) -> None:
        outcome = self.recipe("codex", model="fake-strong")
        self.assertIsInstance(outcome, peer_launch.LaunchError)
        self.assertEqual(outcome.code, "launch_recipe_unresolved")
        recipe = self.recipe(
            "codex",
            model="fake-strong",
            context=peer_launch.LaunchContext(repo="/synthetic/repo"),
        )
        self.assertEqual(
            recipe.argv[:6],
            ("codex", "exec", "--sandbox", "read-only", "--cd", "/synthetic/repo"),
        )
        self.assertIn("--json", recipe.argv)

    def test_cursor_never_synthesizes_an_effort_model_argument(self) -> None:
        outcome = self.recipe("cursor-agent", model="fake-strong", reasoning="high")
        self.assertIsInstance(outcome, peer_launch.LaunchError)
        self.assertEqual(outcome.code, "launch_recipe_unresolved")
        # The level is representable only when the catalog ID already carries it.
        recipe = self.recipe("cursor-agent", model="fake-strong-high", reasoning="high")
        self.assertEqual(recipe.launch_model_argument, "fake-strong-high")
        self.assertIsNone(recipe.reasoning_argument)
        self.assertNotIn("--effort", recipe.argv)

    def test_cursor_elevated_run_requires_a_named_worktree(self) -> None:
        outcome = self.recipe(
            "cursor-agent", permission="isolated-delegate", model="fake-strong"
        )
        self.assertIsInstance(outcome, peer_launch.LaunchError)
        recipe = self.recipe(
            "cursor-agent",
            permission="isolated-delegate",
            model="fake-strong",
            context=peer_launch.LaunchContext(worktree="synthetic-tree"),
        )
        self.assertIn("--force", recipe.argv)
        self.assertEqual(recipe.argv[recipe.argv.index("--worktree") + 1], "synthetic-tree")

    def test_agy_keeps_print_adjacent_to_the_prompt(self) -> None:
        recipe = self.recipe("agy", model="fake-strong", reasoning="high")
        self.assertEqual(recipe.argv[-2], "--print")
        self.assertIn("--sandbox", recipe.argv)
        self.assertEqual(recipe.argv[recipe.argv.index("--print-timeout") + 1], "5m")

    def test_syntax_probe_reports_missing_flags_without_repairing(self) -> None:
        recipe = self.recipe("claude", model="fake-strong")
        with mock.patch.object(
            peer_launch, "help_surface", return_value="usage\n  --model\n  --verbose\n"
        ):
            outcome = peer_launch.validate_syntax(recipe)
        self.assertIsInstance(outcome, peer_launch.LaunchError)
        self.assertEqual(outcome.code, "wrapper_validation_failed")
        self.assertIn("--strict-mcp-config", outcome.missing_flags)
        self.assertIn("--model", " ".join(recipe.argv))

    def test_syntax_probe_accepts_a_help_surface_documenting_every_flag(self) -> None:
        recipe = self.recipe("claude", model="fake-strong")
        help_text = "usage\n" + "\n".join(peer_launch.recipe_flags(recipe))
        with mock.patch.object(peer_launch, "help_surface", return_value=help_text):
            outcome = peer_launch.validate_syntax(recipe)
        self.assertIsInstance(outcome, peer_launch.LaunchRecipe)
        self.assertEqual(outcome.syntax_validation, "verified")

    def test_syntax_probe_does_not_match_a_longer_option_name(self) -> None:
        recipe = self.recipe("codex", context=peer_launch.LaunchContext(repo="/r"))
        with mock.patch.object(
            peer_launch, "help_surface", return_value="usage\n  --json-schema\n  --cd\n"
        ):
            outcome = peer_launch.validate_syntax(recipe)
        self.assertIsInstance(outcome, peer_launch.LaunchError)
        self.assertIn("--json", outcome.missing_flags)

    def test_unreadable_help_surface_leaves_the_recipe_unverified(self) -> None:
        recipe = self.recipe("claude", model="fake-strong")
        with mock.patch.object(peer_launch, "help_surface", return_value=None):
            outcome = peer_launch.validate_syntax(recipe)
        self.assertIsInstance(outcome, peer_launch.LaunchRecipe)
        self.assertEqual(outcome.syntax_validation, "unverified")

    def test_recipes_never_carry_api_key_environment(self) -> None:
        recipe = self.recipe("claude", model="fake-strong")
        self.assertEqual(recipe.auth_mode, "subscription_native")
        self.assertEqual(
            set(recipe.env_overrides) & set(peer_policy.API_KEY_ENV_VARS), set()
        )
        with mock.patch.dict(
            os.environ, {"ANTHROPIC_API_KEY": "redacted"}, clear=False
        ):
            probe_env = peer_policy.subscription_environment(recipe.auth_mode, recipe.cli)
        for name in peer_policy.API_KEY_ENV_VARS:
            self.assertNotIn(name, probe_env)

    def test_documented_wrappers_match_the_adapter_flag_for_flag(self) -> None:
        templates = (
            REPO_ROOT
            / "plugins/v1tamins/skills/v1-phone-a-friend/references/command-templates.md"
        )
        documented = wrapper_blocks(templates.read_text(encoding="utf-8"))
        rendered = [
            tuple(shlex.split(example["block"].replace("\\\n", " ")))
            for example in peer_launch.doc_examples()
        ]
        self.assertEqual(len(documented), len(rendered))
        self.assertEqual(sorted(documented), sorted(rendered))


class PeerVerdictTests(unittest.TestCase):
    """Terminal-answer classification by envelope shape, never provider name."""

    def assertAnswer(self, text: str, family: str) -> None:
        verdict = peer_verdict.classify_text(text)
        self.assertTrue(verdict.answer, text)
        self.assertEqual(verdict.envelope_family, family)

    def assertNoAnswer(self, text: str, family: str = "unknown") -> None:
        verdict = peer_verdict.classify_text(text)
        self.assertFalse(verdict.answer, text)
        self.assertEqual(verdict.envelope_family, family)

    def test_nested_result_envelope_is_a_terminal_answer(self) -> None:
        self.assertAnswer(
            stream(
                {"event": "start", "session_id": "synthetic"},
                {
                    "event": "result",
                    "result": {"status": "SUCCESS", "response": "peer answer body"},
                },
            ),
            "result_event_nested",
        )

    def test_direct_string_result_envelope(self) -> None:
        self.assertAnswer(
            stream(
                {"type": "system", "subtype": "init"},
                {
                    "type": "result",
                    "subtype": "success",
                    "result": "peer answer body",
                    "is_error": False,
                },
            ),
            "result_text",
        )

    def test_assistant_message_content_blocks(self) -> None:
        self.assertAnswer(
            stream(
                {"type": "system", "subtype": "init"},
                {
                    "type": "assistant",
                    "message": {
                        "content": [{"type": "text", "text": "peer answer body"}]
                    },
                },
            ),
            "assistant_message",
        )

    def test_item_completed_envelope(self) -> None:
        self.assertAnswer(
            stream({"type": "item.completed", "text": "peer answer body"}),
            "item_completed",
        )

    def test_framing_only_stream_has_no_answer(self) -> None:
        self.assertNoAnswer(
            stream(
                {"type": "system", "subtype": "init"},
                {"type": "progress", "text": "still working"},
                {"type": "result", "subtype": "success", "result": ""},
            )
        )

    def test_reasoning_only_stream_has_no_answer(self) -> None:
        self.assertNoAnswer(
            stream(
                {
                    "type": "assistant",
                    "message": {
                        "content": [{"type": "thinking", "thinking": "deliberating"}]
                    },
                }
            )
        )

    def test_tool_traffic_only_has_no_answer(self) -> None:
        self.assertNoAnswer(
            stream(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Read",
                                "input": {"file_path": "a.py"},
                            }
                        ]
                    },
                }
            )
        )

    def test_error_envelopes_are_rejected_at_every_level(self) -> None:
        self.assertNoAnswer(
            stream({"type": "result", "result": "failed", "is_error": True})
        )
        self.assertNoAnswer(
            stream({"type": "result", "subtype": "error", "result": "boom"})
        )
        self.assertNoAnswer(
            stream(
                {"event": "result", "result": {"status": "FAILED", "response": "boom"}}
            )
        )

    def test_plain_text_and_empty_output(self) -> None:
        self.assertAnswer("substantive synthetic peer output\n", "plain_text")
        self.assertNoAnswer("   \n\n", "empty")

    def test_mixed_prose_and_json_lines_stay_plain_text(self) -> None:
        self.assertAnswer(
            'warming up\n{"type":"system","subtype":"init"}\n', "plain_text"
        )

    def test_pretty_printed_document_is_classified(self) -> None:
        self.assertAnswer(
            json.dumps(
                {
                    "event": "result",
                    "result": {"status": "SUCCESS", "response": "peer answer body"},
                },
                indent=2,
            ),
            "result_event_nested",
        )

    def test_descent_is_depth_bounded(self) -> None:
        payload: Any = "peer answer body"
        for _ in range(peer_verdict.MAX_DEPTH + 3):
            payload = {"response": payload}
        self.assertFalse(peer_verdict.terminal_text(payload))

    def test_cli_answer_exit_status_and_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "peer.stdout"
            path.write_text(
                stream(
                    {
                        "event": "result",
                        "result": {"status": "SUCCESS", "response": "peer answer body"},
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(peer_verdict.main(["answer", str(path)]), 0)
            path.write_text(stream({"type": "system"}), encoding="utf-8")
            self.assertEqual(peer_verdict.main(["answer", str(path)]), 1)


if __name__ == "__main__":
    unittest.main()
