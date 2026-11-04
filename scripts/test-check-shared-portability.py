#!/usr/bin/env python3
"""Exercise the guard against tracked public guidance and preserved history."""
import importlib.util
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

spec = importlib.util.spec_from_file_location("portability", Path(__file__).with_name("check-shared-portability.py"))
portability = importlib.util.module_from_spec(spec)
spec.loader.exec_module(portability)
# A stand-in for the real pattern, which lives only in a CI secret.
PATTERN = r"private\.example/|(?<![A-Za-z0-9-])ACME-[0-9]+(?![0-9])"


class PortabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def write(self, path, content, tracked=True):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        if tracked:
            subprocess.run(["git", "-C", str(self.root), "add", path], check=True)

    def test_undeclared_contributor_routes_fail(self):
        self.write("docs/agents/contributing.md", "The `domain-modeling` skill creates docs.\n")
        self.write("docs/agents/issue-tracker.md", "The `triage` skill reads this flag.\n")
        self.assertEqual(len(portability.check(self.root)), 2)

    def test_new_personal_name_and_dollar_invocation_fail(self):
        self.write("AGENTS.md", "Use `$private-helper`.\nLoad the `another-private-helper` skill.\n")
        self.assertEqual(len(portability.check(self.root)), 2)

    def test_packaged_and_documented_public_skills_pass(self):
        self.write("plugins/v1tamins/skills/v1-example/SKILL.md", "Example\n")
        self.write("README.md", "Use the `v1-example` skill or the optional `ce-work` skill.\n")
        self.assertEqual(portability.check(self.root), [])

    def test_operator_homes_fail_but_portable_roots_pass(self):
        self.write("AGENTS.md", "/Users/example/project/\n/home/example/project/\nC:\\Users\\example\\project\n")
        self.assertEqual(len(portability.check(self.root)), 3)
        self.write("AGENTS.md", "~/.codex/skills/\n$HOME/.agents/skills/\n/Users/<operator>/project/\n")
        self.assertEqual(portability.check(self.root), [])

    def test_history_and_untracked_notes_are_preserved(self):
        original = "The `domain-modeling` skill was used.\n"
        self.write("CHANGELOG.md", original)
        self.write("docs/agents/local-notes.md", original, tracked=False)
        self.assertEqual(portability.check(self.root), [])
        self.assertEqual((self.root / "CHANGELOG.md").read_text(), original)

    def test_personal_cli_instructions_and_executable_calls_fail(self):
        self.write("docs/agents/tools.md", "Run taskit to record work.\nLoad tool-native-operations.\n")
        self.write("scripts/helper.sh", 'taskit list\nbash "$HOME/.local/bin/lint-pr.sh"\n')
        self.write("plugins/v1tamins/skills/v1-example/scripts/helper.py", 'import subprocess\nsubprocess.run(["taskit", "list"])\n')
        self.assertEqual(len(portability.check(self.root)), 5)
        result = subprocess.run(
            ["python3", str(Path(portability.__file__)), str(self.root)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("scripts/helper.sh:1:", result.stderr)

    def test_blocked_references_fail_in_every_tracked_file(self):
        self.write("CHANGELOG.md", "- Fixed the peer verdict (ACME-4967).\n")
        self.write(".changeset/x.md", "See https://private.example/item/1\n")
        self.write("docs/notes.md", "Moved to ACME-1234, for example.\n")
        self.write("docs/untracked.md", "ACME-1\n", tracked=False)
        with mock.patch.object(portability, "BLOCKED_REFERENCE", re.compile(PATTERN)):
            failures = portability.check(self.root)
        self.assertEqual(len(failures), 3)
        self.assertTrue(all("keep private" in failure for failure in failures))

    def test_similar_identifiers_pass_and_unset_pattern_checks_nothing(self):
        self.write("README.md", "UTF-8, SHA-256, RFC-2119, ACMEX-12, acme-12, NOTACME-3.\n")
        with mock.patch.object(portability, "BLOCKED_REFERENCE", re.compile(PATTERN)):
            self.assertEqual(portability.check(self.root), [])
        self.write("docs/notes.md", "ACME-1\n")
        with mock.patch.object(portability, "BLOCKED_REFERENCE", None):
            self.assertEqual(portability.check(self.root), [])

    def test_stdin_mode_checks_pr_and_commit_text(self):
        script = str(Path(portability.__file__))
        env = {**os.environ, "BLOCKED_REFERENCE_PATTERN": PATTERN}
        bad = subprocess.run(
            ["python3", script, "--stdin"], input="docs: close #91 (moved to ACME-4972)\n",
            capture_output=True, text=True, env=env,
        )
        self.assertEqual(bad.returncode, 1)
        self.assertIn("stdin:1:", bad.stderr)
        good = subprocess.run(
            ["python3", script, "--stdin"], input="docs: close #91 as fixed by #117\n",
            capture_output=True, text=True, env=env,
        )
        self.assertEqual(good.returncode, 0)

    def test_invalid_utf8_is_blocking(self):
        self.write("AGENTS.md", "placeholder")
        (self.root / "AGENTS.md").write_bytes(b"\xff")
        self.assertIn("UTF-8", portability.check(self.root)[0])


if __name__ == "__main__":
    unittest.main()
