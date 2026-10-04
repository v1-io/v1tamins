#!/usr/bin/env python3
"""Focused regressions for peer boundary manifests, probes, and path safety."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import contextmanager
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/v1tamins/skills/v1-phone-a-friend/scripts"
RUNNER = SCRIPTS / "peer-run.sh"
sys.path.insert(0, str(SCRIPTS))

import peer_adapters  # noqa: E402
import peer_boundary  # noqa: E402
import peer_launch  # noqa: E402


def run_git(repo: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise AssertionError(result.stderr)


def make_repo(root: Path) -> Path:
    root.mkdir()
    run_git(root, "init", "--quiet")
    run_git(root, "config", "user.email", "synthetic@example.invalid")
    run_git(root, "config", "user.name", "synthetic")
    (root / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    run_git(root, "add", "tracked.txt")
    run_git(root, "commit", "--quiet", "-m", "baseline")
    return root


class BoundaryManifestTests(unittest.TestCase):
    def test_ignored_and_git_metadata_changes_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = make_repo(root / "repo")
            home = root / "home"
            (home / ".claude").mkdir(parents=True)
            (repo / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
            run_git(repo, "add", ".gitignore")
            run_git(repo, "commit", "--quiet", "-m", "ignore")
            (repo / "ignored.txt").write_text("before\n", encoding="utf-8")
            run_dir = root / "run"

            peer_boundary.take_snapshot(run_dir, repo, "claude", home)
            (repo / "ignored.txt").write_text("after\n", encoding="utf-8")
            result = peer_boundary.verify_snapshot(run_dir)

            self.assertTrue(result["repo_changes"]["changed"])
            self.assertIn("ignored.txt", result["repo_changes"]["changed_paths"])
            self.assertEqual(result["permission_state"], "readonly_violated")

            peer_boundary.take_snapshot(run_dir, repo, "claude", home)
            (repo / ".git" / "config").write_text(
                (repo / ".git" / "config").read_text(encoding="utf-8")
                + "\n[synthetic]\n\tchanged = true\n",
                encoding="utf-8",
            )
            result = peer_boundary.verify_snapshot(run_dir)
            self.assertIn(".git/config", result["repo_changes"]["changed_paths"])

    def test_existing_dirty_files_are_compared_by_content(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = make_repo(root / "repo")
            home = root / "home"
            (home / ".claude").mkdir(parents=True)
            (repo / "tracked.txt").write_text("dirty-before\n", encoding="utf-8")
            (repo / "untracked.txt").write_text("untracked-before\n", encoding="utf-8")
            run_dir = root / "run"

            peer_boundary.take_snapshot(run_dir, repo, "claude", home)
            (repo / "tracked.txt").write_text("dirty-after\n", encoding="utf-8")
            (repo / "untracked.txt").write_text("untracked-after\n", encoding="utf-8")
            result = peer_boundary.verify_snapshot(run_dir)

            self.assertTrue(result["repo_changes"]["changed"])
            self.assertIn("tracked.txt", result["repo_changes"]["changed_paths"])
            self.assertIn("untracked.txt", result["repo_changes"]["changed_paths"])

    def test_provider_state_deletion_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = make_repo(root / "repo")
            home = root / "home"
            old_state = home / ".claude/projects/old.json"
            old_state.parent.mkdir(parents=True)
            old_state.write_text("old\n", encoding="utf-8")
            run_dir = root / "run"

            peer_boundary.take_snapshot(run_dir, repo, "claude", home)
            old_state.unlink()
            result = peer_boundary.verify_snapshot(run_dir)

            self.assertEqual(result["permission_state"], "readonly_degraded_provider_state")
            changed = {
                path
                for entry in result["provider_state_changes"]
                for path in entry["changed"]
            }
            self.assertIn("projects/old.json", changed)

    def test_visit_budget_bounds_directory_enumeration(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for index in range(25):
                (root / str(index)).touch()
            actual_scandir = os.scandir
            enumerated = []

            @contextmanager
            def observed_scandir(path):
                with actual_scandir(path) as entries:
                    def counted_entries():
                        for entry in entries:
                            enumerated.append(entry.name)
                            yield entry
                    yield counted_entries()

            with patch.object(peer_boundary.os, "scandir", observed_scandir):
                result = peer_boundary.scan_manifest(root, budget=1)
            self.assertEqual(result.visited, 1)
            self.assertTrue(result.truncated)
            self.assertEqual(len(enumerated), 2)  # One entry proves truncation.

    def test_manifest_budget_degrades_containment(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = make_repo(root / "repo")
            home = root / "home"
            (home / ".claude").mkdir(parents=True)
            run_dir = root / "run"
            peer_boundary.take_snapshot(run_dir, repo, "claude", home)

            result = peer_boundary.verify_snapshot(run_dir, budget=1)

            self.assertEqual(result["permission_state"], "containment_unverified")
            self.assertIn("repository_manifest_unverified", result["containment_gaps"])

    def test_external_symlink_degrades_containment(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = make_repo(root / "repo")
            home = root / "home"
            (home / ".claude").mkdir(parents=True)
            outside = root / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            (repo / "link.txt").symlink_to(outside)
            run_dir = root / "run"

            peer_boundary.take_snapshot(run_dir, repo, "claude", home)
            result = peer_boundary.verify_snapshot(run_dir)

            self.assertEqual(result["permission_state"], "containment_unverified")
            self.assertIn("repository_manifest_unverified", result["containment_gaps"])


class ProbeAndPathTests(unittest.TestCase):
    def test_failed_help_probe_cannot_verify_syntax(self) -> None:
        failed_help = peer_adapters.CommandResult(2, "--model --sandbox", "help failed")
        with patch.object(peer_launch.shutil, "which", return_value="synthetic-cli"), \
                patch.object(peer_launch, "run_probe", return_value=failed_help):
            self.assertIsNone(peer_launch.help_surface("agy", "subscription_native", 1))

    def test_probe_timeout_terminates_descendants(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pid_path = root / "child.pid"
            marker = root / "child-survived"
            child_code = (
                "import pathlib,sys,time; "
                "pathlib.Path(sys.argv[2]).write_text(str(__import__('os').getpid())); "
                "time.sleep(1); pathlib.Path(sys.argv[3]).write_text('survived')"
            )
            parent_code = (
                "import pathlib,subprocess,sys,time; "
                "child=subprocess.Popen([sys.executable, '-c', sys.argv[4], 'child', sys.argv[2], sys.argv[3]]); "
                "pathlib.Path(sys.argv[2]).write_text(str(child.pid)); "
                "time.sleep(30)"
            )
            try:
                result = peer_adapters.run_probe(
                    [
                        sys.executable,
                        "-c",
                        parent_code,
                        "parent",
                        str(pid_path),
                        str(marker),
                        child_code,
                    ],
                    dict(os.environ),
                    0.2,
                )

                self.assertTrue(result.timed_out)
                for _ in range(30):
                    if pid_path.exists():
                        break
                    time.sleep(0.02)
                self.assertTrue(pid_path.exists())
                time.sleep(1.1)
                self.assertFalse(marker.exists())
            finally:
                self._kill_pid_file(pid_path)

            escaped_pid_path = root / "escaped-child.pid"
            escaped_child_code = (
                "import os,pathlib,sys,time; os.setsid(); "
                "pathlib.Path(sys.argv[2]).write_text(str(os.getpid())); time.sleep(30)"
            )
            escaped_parent_code = (
                "import subprocess,sys,time; "
                "subprocess.Popen([sys.executable, '-c', sys.argv[3], 'child', sys.argv[2]]); "
                "time.sleep(30)"
            )
            started = time.monotonic()
            try:
                result = peer_adapters.run_probe(
                    [
                        sys.executable,
                        "-c",
                        escaped_parent_code,
                        "parent",
                        str(escaped_pid_path),
                        escaped_child_code,
                    ],
                    dict(os.environ),
                    0.2,
                )
                self.assertTrue(result.timed_out)
                self.assertLess(time.monotonic() - started, 2.0)
            finally:
                self._kill_pid_file(escaped_pid_path)

    @staticmethod
    def _kill_pid_file(path: Path) -> None:
        if not path.exists():
            return
        try:
            os.kill(int(path.read_text(encoding="utf-8")), 9)
        except (OSError, ValueError):
            pass

    def test_literal_tilde_path_checks_the_directory_the_runner_uses(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            run_dir = root / "~" / "runs"
            outside = root / "outside"
            run_dir.mkdir(parents=True)
            outside.mkdir()
            (run_dir / "escape").symlink_to(outside, target_is_directory=True)
            result = subprocess.run(
                [str(RUNNER), "verdict", "--dir", "~/runs", "--slug", "escape"],
                cwd=root, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("escapes run directory", result.stderr)

    def test_runner_rejects_dot_and_symlink_escape_for_every_command(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            run_dir = root / "run"
            outside = root / "outside"
            run_dir.mkdir()
            outside.mkdir()
            (run_dir / "escape").symlink_to(outside, target_is_directory=True)

            for slug in ("..", "escape"):
                for command in ("status", "verdict", "teardown"):
                    result = subprocess.run(
                        [str(RUNNER), command, "--dir", str(run_dir), "--slug", slug],
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(result.returncode, 0, (command, slug))
                result = subprocess.run(
                    [
                        str(RUNNER),
                        "launch",
                        "--dir",
                        str(run_dir),
                        "--slug",
                        slug,
                        "--deadline-seconds",
                        "1",
                        "--",
                        sys.executable,
                        "-c",
                        "print('answer')",
                    ],
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(result.returncode, 0, slug)


if __name__ == "__main__":
    unittest.main()
