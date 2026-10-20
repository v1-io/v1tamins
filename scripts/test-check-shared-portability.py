#!/usr/bin/env python3
"""Exercise the guard against tracked public guidance and preserved history."""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("portability", Path(__file__).with_name("check-shared-portability.py"))
portability = importlib.util.module_from_spec(spec)
spec.loader.exec_module(portability)


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

    def test_original_contributor_routes_fail(self):
        self.write("docs/agents/domain.md", "The `domain-modeling` skill creates docs.\n")
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
        self.write("docs/adr/0001-history.md", original)
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

    def test_invalid_utf8_is_blocking(self):
        self.write("AGENTS.md", "placeholder")
        (self.root / "AGENTS.md").write_bytes(b"\xff")
        self.assertIn("UTF-8", portability.check(self.root)[0])


if __name__ == "__main__":
    unittest.main()
