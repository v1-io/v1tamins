#!/usr/bin/env python3
"""Deterministic tests for the live skill-routing eval helpers."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from skill_routing_live import (
    base_result,
    load_results,
    process_failure_reason,
    run_case,
    score_result,
    validate_result_shape,
)


def fixture_case(**overrides):
    case = {
        "case_id": "fake-debug-case",
        "prompt": "Debug this failing traceback.",
        "expected_skill": "v1-debug",
        "acceptable_skills": [],
        "near_miss_skills": ["v1-fix-tests"],
        "must_not_trigger": ["v1-land-pr"],
        "side_effect_allowed": False,
        "category": "positive",
        "rationale": "Debugging should route to v1-debug.",
    }
    case.update(overrides)
    return case


def write_fake_runtime(path: Path, selected_skill: str = "v1-debug") -> None:
    payload = json.dumps(
        {
            "selected_skill": selected_skill,
            "reason": "fake routing decision",
            "confidence": 1.0,
        }
    )
    path.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json, sys",
                "if '--version' in sys.argv:",
                "    print('fake runtime 1.0')",
                "    sys.exit(0)",
                "if len(sys.argv) > 1 and sys.argv[1] == 'auth':",
                "    print('authenticated')",
                "    sys.exit(0)",
                f"payload = {payload!r}",
                "if 'claude' in sys.argv[0]:",
                "    print(json.dumps({'type': 'result', 'result': payload}))",
                "else:",
                "    print(json.dumps({'type': 'message', 'content': payload}))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


class LiveRoutingTests(unittest.TestCase):
    def test_result_shape_accepts_inconclusive(self):
        result = base_result(fixture_case(), "codex", "fake", None)
        result["reason"] = "preflight skipped"
        self.assertEqual(validate_result_shape(result), [])

    def test_result_shape_rejects_missing_runtime(self):
        result = base_result(fixture_case(), "codex", "fake", None)
        del result["runtime"]
        self.assertIn("missing field: runtime", validate_result_shape(result))

    def test_expected_skill_scores_pass(self):
        result = base_result(fixture_case(), "codex", "fake", None)
        result["selected_skill"] = "v1-debug"
        result["evidence_kind"] = "structured_decision"
        scored = score_result(result, fixture_case(), set())
        self.assertEqual(scored["status"], "pass")

    def test_acceptable_alternative_scores_pass(self):
        case = fixture_case(acceptable_skills=["v1-fix-tests"])
        result = base_result(case, "codex", "fake", None)
        result["selected_skill"] = "v1-fix-tests"
        result["evidence_kind"] = "structured_decision"
        scored = score_result(result, case, set())
        self.assertEqual(scored["status"], "pass")
        self.assertIn("acceptable alternative", scored["score_notes"][0])

    def test_near_miss_scores_fail(self):
        result = base_result(fixture_case(), "codex", "fake", None)
        result["selected_skill"] = "v1-fix-tests"
        result["evidence_kind"] = "structured_decision"
        scored = score_result(result, fixture_case(), set())
        self.assertEqual(scored["status"], "fail")
        self.assertEqual(scored["severity"], "normal")

    def test_must_not_side_effect_scores_high(self):
        result = base_result(fixture_case(), "codex", "fake", None)
        result["selected_skill"] = "v1-land-pr"
        result["evidence_kind"] = "structured_decision"
        scored = score_result(result, fixture_case(), {"v1-land-pr"})
        self.assertEqual(scored["status"], "fail")
        self.assertEqual(scored["severity"], "high")
        self.assertEqual(scored["prohibited_skill_hits"], ["v1-land-pr"])

    def test_inconclusive_is_not_failure_by_default(self):
        result = base_result(fixture_case(), "codex", "fake", None)
        scored = score_result(result, fixture_case(), set())
        self.assertEqual(scored["status"], "inconclusive")

    def test_fake_codex_runtime_records_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = root / "codex"
            write_fake_runtime(fake)
            result = run_case(
                fixture_case(),
                "codex",
                str(fake),
                root,
                root / "run",
                timeout=10,
                skip_auth_check=False,
            )
            scored = score_result(result, fixture_case(), set())
            self.assertEqual(scored["status"], "pass")
            self.assertEqual(scored["runtime"], "codex")
            self.assertTrue((root / "run" / scored["raw_artifact"]).exists())

    def test_fake_claude_runtime_records_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = root / "claude"
            write_fake_runtime(fake)
            result = run_case(
                fixture_case(),
                "claude",
                str(fake),
                root,
                root / "run",
                timeout=10,
                skip_auth_check=False,
            )
            scored = score_result(result, fixture_case(), set())
            self.assertEqual(scored["status"], "pass")
            self.assertEqual(scored["runtime"], "claude")

    def test_missing_runtime_is_inconclusive(self):
        result = run_case(
            fixture_case(),
            "codex",
            None,
            Path(os.getcwd()),
            Path(os.getcwd()),
            timeout=1,
            skip_auth_check=False,
        )
        self.assertEqual(result["status"], "inconclusive")
        self.assertIn("binary not found", result["reason"])

    def test_load_results_prefers_results_jsonl_in_run_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = base_result(fixture_case(), "codex", "fake", None)
            (root / "results.jsonl").write_text(
                json.dumps(result) + "\n", encoding="utf-8"
            )
            (root / "routing-decision.schema.json").write_text(
                json.dumps({"type": "object"}), encoding="utf-8"
            )

            loaded = load_results([root])

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["case_id"], "fake-debug-case")

    def test_process_failure_reason_includes_stderr_and_stdout(self):
        completed = subprocess.CompletedProcess(
            args=["runtime"],
            returncode=1,
            stdout="Invalid API key",
            stderr="connector warning",
        )

        reason = process_failure_reason("claude", completed)

        self.assertIn("connector warning", reason)
        self.assertIn("Invalid API key", reason)


if __name__ == "__main__":
    unittest.main()
