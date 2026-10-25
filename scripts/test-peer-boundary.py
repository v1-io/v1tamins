#!/usr/bin/env python3
"""Focused regressions for peer boundary manifests, probes, and path safety."""

from __future__ import annotations

import json
import os
import shutil
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
sys.dont_write_bytecode = True
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
    def setUp(self) -> None:
        self.receipts = {}

    def take_snapshot(self, run_dir, repo, provider, home):
        snapshot = peer_boundary.take_snapshot(run_dir, repo, provider, home)
        receipt = peer_boundary.write_owner_snapshot(snapshot)
        self.receipts[str(run_dir.resolve())] = receipt
        self.addCleanup(Path(receipt["snapshot_path"]).unlink, missing_ok=True)
        return snapshot

    def verify_snapshot(self, run_dir, budget=peer_boundary.DEFAULT_VISIT_BUDGET):
        receipt = self.receipts[str(run_dir.resolve())]
        return peer_boundary.verify_snapshot(
            run_dir, budget, snapshot_path=Path(receipt["snapshot_path"]),
            snapshot_sha256=receipt["snapshot_sha256"],
        )

    def test_synthetic_child_cannot_forge_owner_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = make_repo(root / "repo")
            home = root / "home"
            (home / ".claude").mkdir(parents=True)
            run_dir = root / "run"
            self.take_snapshot(run_dir, repo, "claude", home)
            receipt = self.receipts[str(run_dir.resolve())]
            baseline = Path(receipt["snapshot_path"])
            self.assertNotIn(run_dir, baseline.parents)
            self.assertEqual(baseline.stat().st_mode & 0o077, 0)
            self.assertFalse((run_dir / peer_boundary.SNAPSHOT_NAME).exists())
            child = '''
import json, pathlib, sys
sys.path.insert(0, sys.argv[1])
import peer_boundary
repo, run, baseline = map(pathlib.Path, sys.argv[2:])
(repo / "tracked.txt").write_text("forged change\\n")
snapshot = json.loads(baseline.read_text())
snapshot["repo"] = peer_boundary.repo_state(repo)
snapshot["repo_manifest"] = peer_boundary.scan_repository_manifest(repo)[0].to_dict()
(run / peer_boundary.SNAPSHOT_NAME).write_text(json.dumps(snapshot))
baseline.write_text(json.dumps(snapshot, sort_keys=True))
'''
            subprocess.run([sys.executable, "-B", "-c", child, str(SCRIPTS),
                            str(repo), str(run_dir), str(baseline)], check=True)
            with patch.object(peer_boundary, "scan_repository_manifest", side_effect=AssertionError("must authenticate before scanning")):
                result = self.verify_snapshot(run_dir)
            self.assertEqual(result["permission_state"], "containment_unverified")
            self.assertIn("integrity", result["detail"])

    def test_peer_scratch_baseline_without_owner_receipt_is_unverified(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw)
            (run_dir / peer_boundary.SNAPSHOT_NAME).write_text('{}')
            result = peer_boundary.verify_snapshot(run_dir)
            self.assertEqual(result["permission_state"], "containment_unverified")

    def test_owner_receipt_cannot_be_reused_for_other_run(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = make_repo(root / "repo")
            self.take_snapshot(root / "run", repo, "claude", root / "home")
            receipt = self.receipts[str((root / "run").resolve())]
            result = peer_boundary.verify_snapshot(
                root / "different", snapshot_path=Path(receipt["snapshot_path"]),
                snapshot_sha256=receipt["snapshot_sha256"])
            self.assertEqual(result["permission_state"], "containment_unverified")

    def test_authenticated_manifest_identity_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = make_repo(root / "repo")
            snapshot = self.take_snapshot(root / "run", repo, "claude", root / "home")
            for key in ("repo_manifest", "scratch_manifest"):
                with self.subTest(key=key):
                    changed = json.loads(json.dumps(snapshot))
                    changed[key]["root"] = str(root / "different")
                    receipt = peer_boundary.write_owner_snapshot(changed)
                    path = Path(receipt["snapshot_path"])
                    self.addCleanup(path.unlink, missing_ok=True)
                    result = peer_boundary.verify_snapshot(root / "run", snapshot_path=path,
                                                          snapshot_sha256=receipt["snapshot_sha256"])
                    self.assertEqual(result["permission_state"], "containment_unverified")

    def test_overlapping_scratch_is_rejected_before_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = make_repo(root / "repo")
            home = root / "home"
            for run_dir in (repo / "scratch", repo, root):
                with self.subTest(run_dir=run_dir):
                    with self.assertRaisesRegex(ValueError, "must not overlap"):
                        self.take_snapshot(run_dir, repo, "claude", home)
                    self.assertFalse((run_dir / peer_boundary.SNAPSHOT_NAME).exists())
            self.assertFalse((repo / "scratch").exists())

    def test_overlapping_launch_preserves_repo_and_does_not_run(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = make_repo(root / "repo")
            before = peer_boundary.scan_manifest(repo).entries
            result = subprocess.run(
                [str(RUNNER), "launch", "--dir", str(repo / "scratch"),
                 "--slug", "overlap", "--boundary-repo", str(repo),
                 "--boundary-provider", "claude", "--", sys.executable,
                 "-c", "raise SystemExit('must never launch')"],
                capture_output=True, text=True, timeout=10,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not overlap", result.stderr)
            self.assertEqual(peer_boundary.scan_manifest(repo).entries, before)

    def test_cold_checkout_overlap_preflight_does_not_write_bytecode(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = make_repo(root / "repo")
            scripts = repo / "scripts"
            shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
            before = peer_boundary.scan_manifest(repo).entries
            environment = dict(os.environ)
            environment.pop("PYTHONDONTWRITEBYTECODE", None)
            result = subprocess.run(
                [str(scripts / "peer-run.sh"), "launch", "--dir", str(repo / "scratch"),
                 "--slug", "overlap", "--boundary-repo", str(repo),
                 "--boundary-provider", "claude", "--", sys.executable,
                 "-c", "raise SystemExit('must never launch')"],
                capture_output=True, text=True, timeout=10, env=environment,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not overlap", result.stderr)
            self.assertFalse((repo / "scratch").exists())
            self.assertEqual(peer_boundary.scan_manifest(repo).entries, before)

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

            self.take_snapshot(run_dir, repo, "claude", home)
            (repo / "ignored.txt").write_text("after\n", encoding="utf-8")
            result = self.verify_snapshot(run_dir)

            self.assertTrue(result["repo_changes"]["changed"])
            self.assertIn("ignored.txt", result["repo_changes"]["changed_paths"])
            self.assertEqual(result["permission_state"], "readonly_violated")

            self.take_snapshot(run_dir, repo, "claude", home)
            (repo / ".git" / "config").write_text(
                (repo / ".git" / "config").read_text(encoding="utf-8")
                + "\n[synthetic]\n\tchanged = true\n",
                encoding="utf-8",
            )
            result = self.verify_snapshot(run_dir)
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

            self.take_snapshot(run_dir, repo, "claude", home)
            (repo / "tracked.txt").write_text("dirty-after\n", encoding="utf-8")
            (repo / "untracked.txt").write_text("untracked-after\n", encoding="utf-8")
            result = self.verify_snapshot(run_dir)

            self.assertTrue(result["repo_changes"]["changed"])
            self.assertIn("tracked.txt", result["repo_changes"]["changed_paths"])
            self.assertIn("untracked.txt", result["repo_changes"]["changed_paths"])

    def test_unreadable_provider_subtree_never_verifies_no_writes(self) -> None:
        if os.geteuid() == 0:
            self.skipTest("real unreadable directory requires an unprivileged process")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = make_repo(root / "repo")
            home = root / "home"
            closed = home / ".claude/closed"
            closed.mkdir(parents=True)
            state = closed / "state.txt"
            state.write_text("before")
            run_dir = root / "run"
            with state.open("w") as writer:
                closed.chmod(0)
                try:
                    with self.assertRaises(PermissionError):
                        list(closed.iterdir())
                    self.take_snapshot(run_dir, repo, "claude", home)
                    writer.write("changed through an already-open descriptor")
                    writer.flush()
                    os.fsync(writer.fileno())
                    result = self.verify_snapshot(run_dir)
                finally:
                    closed.chmod(0o700)
            self.assertEqual(result["permission_state"], "containment_unverified", result)
            self.assertIn("provider_manifest_unverified:0", result["containment_gaps"])
            self.assertEqual(state.read_text(), "changed through an already-open descriptor")

    def test_directory_enumeration_error_marks_manifest_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            original_scandir = os.scandir
            denied_calls = []
            def denied(path):
                if isinstance(path, int):
                    matches = os.fstat(path).st_ino == root.stat().st_ino
                else:
                    matches = Path(path) == root
                if matches:
                    denied_calls.append(path)
                    raise PermissionError("synthetic denied enumeration")
                return original_scandir(path)
            with patch.object(peer_boundary.os, "scandir", denied):
                result = peer_boundary.scan_manifest(root)
            self.assertTrue(result.errors)
            self.assertEqual(len(denied_calls), 1)
            self.assertFalse(result.truncated)

    def test_undecodable_git_output_is_an_observation_gap(self) -> None:
        original_run = subprocess.run
        def invalid_output(_argv, **kwargs):
            return original_run([sys.executable, "-c", "import sys; sys.stdout.buffer.write(bytes([255]))"], **kwargs)
        with patch.object(peer_boundary.subprocess, "run", invalid_output):
            self.assertIsNone(peer_boundary.git_output(Path("."), ["ls-files", "-z"]))

    def test_raw_byte_path_does_not_collapse_identity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = make_repo(root / "repo")
            home = root / "home"
            (home / ".claude").mkdir(parents=True)
            target = os.fsencode(repo) + b"/file-\xff.txt"
            try:
                with open(target, "wb") as handle:
                    handle.write(b"before")
            except OSError as error:
                if sys.platform == "darwin" and error.errno == 92:
                    self.skipTest("filesystem rejects non-UTF-8 filenames; Ubuntu exercises this case")
                raise
            self.take_snapshot(root / "run", repo, "claude", home)
            with open(target, "wb") as handle:
                handle.write(b"after")
            result = self.verify_snapshot(root / "run")
            self.assertEqual(result["permission_state"], "containment_unverified", result)

    def test_unsupported_symlink_target_prevents_verification(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = make_repo(root / "repo")
            home = root / "home"
            (home / ".claude").mkdir(parents=True)
            (repo / "link").symlink_to("target")
            original_readlink = os.readlink
            def unsupported_target(path, *, dir_fd=None):
                if dir_fd is not None:
                    return "target-\udcff"
                return original_readlink(path)
            with patch.object(peer_boundary.os, "readlink", side_effect=unsupported_target):
                self.take_snapshot(root / "run", repo, "claude", home)
                result = self.verify_snapshot(root / "run")
            self.assertEqual(result["permission_state"], "containment_unverified", result)

    def test_index_change_with_unchanged_worktree_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = make_repo(root / "repo")
            home = root / "home"
            (home / ".claude").mkdir(parents=True)
            (repo / "tracked.txt").write_text("dirty-before")
            self.take_snapshot(root / "run", repo, "claude", home)
            run_git(repo, "add", "tracked.txt")
            result = self.verify_snapshot(root / "run")
            self.assertEqual(result["permission_state"], "readonly_violated", result)

    def test_provider_state_deletion_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = make_repo(root / "repo")
            home = root / "home"
            old_state = home / ".claude/projects/old.json"
            old_state.parent.mkdir(parents=True)
            old_state.write_text("old\n", encoding="utf-8")
            run_dir = root / "run"

            self.take_snapshot(run_dir, repo, "claude", home)
            old_state.unlink()
            result = self.verify_snapshot(run_dir)

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
            self.take_snapshot(run_dir, repo, "claude", home)

            result = self.verify_snapshot(run_dir, budget=1)

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

            self.take_snapshot(run_dir, repo, "claude", home)
            result = self.verify_snapshot(run_dir)

            self.assertEqual(result["permission_state"], "containment_unverified")
            self.assertIn("repository_manifest_unverified", result["containment_gaps"])


class ProbeAndPathTests(unittest.TestCase):
    def test_failed_help_probe_cannot_verify_syntax(self) -> None:
        failed_help = peer_adapters.CommandResult(2, "--model --sandbox", "help failed")
        with patch.object(peer_launch.shutil, "which", return_value="synthetic-cli"), \
                patch.object(peer_launch, "run_probe", return_value=failed_help):
            self.assertIsNone(peer_launch.help_surface("agy", "subscription_native", 1))

    @unittest.skipUnless(os.name == "posix", "process-group fixture requires POSIX")
    def test_probe_timeout_kills_term_ignoring_child_with_detached_stdio(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pid_path = root / "child.pid"
            ready = root / "ready"
            survived = root / "survived"
            child = root / "child.py"
            child.write_text(
                "import os, signal, time; from pathlib import Path\n"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                f"Path({str(pid_path)!r}).write_text(str(os.getpid()))\n"
                f"Path({str(ready)!r}).touch()\n"
                "time.sleep(1.5)\n"
                f"Path({str(survived)!r}).touch()\n"
                "time.sleep(30)\n"
            )
            parent = root / "parent.py"
            parent.write_text(
                "import subprocess, sys, time; from pathlib import Path\n"
                f"subprocess.Popen([sys.executable, {str(child)!r}], "
                "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
                f"while not Path({str(ready)!r}).exists(): time.sleep(0.01)\n"
                "print('ready', flush=True)\n"
                "time.sleep(30)\n"
            )
            started = time.monotonic()
            try:
                result = peer_adapters.run_probe(
                    [sys.executable, str(parent)], dict(os.environ), 1,
                )
                self.assertTrue(result.timed_out)
                self.assertIsNone(result.returncode)
                self.assertEqual(result.stdout.strip(), "ready")
                self.assertLess(time.monotonic() - started, 3)
                time.sleep(1)
                self.assertFalse(survived.exists(), "TERM-ignoring descendant survived pipe EOF")
            finally:
                self._kill_pid_file(pid_path)

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
