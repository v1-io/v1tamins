#!/usr/bin/env python3
"""Deterministic tests for dynamic peer discovery and selection."""

from __future__ import annotations

import importlib.util
import json
import os
import re
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
                            "id": "family-a-1",
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
                            "id": "family-a-2",
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
                            "id": "family-b-1",
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


def stream(*events: dict[str, Any]) -> str:
    return "".join(json.dumps(event) + "\n" for event in events)


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
