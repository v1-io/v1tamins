#!/usr/bin/env python3
"""Offline regressions for the PR-description diff-context contract."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "plugins/v1tamins/skills/v1-pr-description/generate.sh"


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.bin = root / "bin"
        self.bin.mkdir()
        self.gh_json = root / "pr.json"
        self.repo_json = root / "repo.json"
        self.repo_selector = root / "repo-selector.txt"
        self.api_json = root / "api.json"
        self.api_request = root / "api-request.txt"
        self.work = root / "work"
        self.base = root / "base.git"

    def git(self, repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=False,
            capture_output=True,
            text=True,
        )
        if check and result.returncode:
            raise AssertionError(
                f"git {' '.join(args)} failed ({result.returncode}): {result.stderr}"
            )
        return result

    def init_bare(self, path: Path) -> None:
        self.git(self.root, "init", "--bare", "--quiet", str(path))

    def seed_remote(self, path: Path, filename: str, contents: str) -> str:
        self.init_bare(path)
        source = self.root / f"source-{path.stem}"
        self.git(self.root, "init", "--quiet", str(source))
        self.git(source, "config", "user.email", "synthetic@example.invalid")
        self.git(source, "config", "user.name", "synthetic")
        (source / filename).write_text(contents, encoding="utf-8")
        self.git(source, "add", filename)
        self.git(source, "commit", "--quiet", "-m", "baseline")
        self.git(source, "branch", "-M", "main")
        self.git(source, "remote", "add", "origin", str(path))
        self.git(source, "push", "--quiet", "origin", "main")
        return self.git(source, "rev-parse", "HEAD").stdout.strip()

    def advance_remote(self, path: Path, filename: str, contents: str) -> str:
        source = self.root / f"source-{path.stem}"
        (source / filename).write_text(contents, encoding="utf-8")
        self.git(source, "add", filename)
        self.git(source, "commit", "--quiet", "-m", "advance")
        self.git(source, "push", "--quiet", "origin", "main")
        return self.git(source, "rev-parse", "HEAD").stdout.strip()

    def add_remote(
        self,
        repo: Path,
        name: str,
        identity: str,
        target: Path,
        host: str = "github.com",
    ) -> None:
        url = f"https://{host}/{identity}.git"
        rewrite_key = f"url.file://{target}.insteadOf"
        self.git(repo, "config", rewrite_key, url)
        self.git(repo, "remote", "add", name, url)

    def make_work_from(
        self,
        remote_name: str,
        identity: str,
        target: Path,
        host: str = "github.com",
    ) -> str:
        self.git(self.root, "init", "--quiet", str(self.work))
        self.git(self.work, "config", "user.email", "synthetic@example.invalid")
        self.git(self.work, "config", "user.name", "synthetic")
        self.add_remote(self.work, remote_name, identity, target, host)
        self.git(self.work, "fetch", "--quiet", remote_name, "main")
        self.git(self.work, "checkout", "-q", "-b", "feature", "FETCH_HEAD")
        (self.work / "feature.txt").write_text("feature\n", encoding="utf-8")
        self.git(self.work, "add", "feature.txt")
        self.git(self.work, "commit", "--quiet", "-m", "feature")
        return self.git(self.work, "rev-parse", "HEAD").stdout.strip()

    def add_gh_stub(
        self,
        *,
        base_identity: str,
        head_identity: str,
        base_sha: str,
        head_sha: str,
        host: str = "github.com",
        authoritative_sha: str | None = None,
    ) -> None:
        authoritative_sha = authoritative_sha or base_sha
        metadata = {
            "number": 90,
            "url": f"https://{host}/example/base/pull/90",
            "title": "Synthetic PR",
            "body": "Existing body\n\n<!-- required footer -->",
            "baseRefName": "main",
            "baseRefOid": base_sha,
            "headRefName": "feature",
            "headRefOid": head_sha,
            "headRepository": {"nameWithOwner": head_identity},
            "headRepositoryOwner": {"login": head_identity.split("/", 1)[0]},
            "files": [{"path": "feature.txt"}],
            "commits": [{"oid": head_sha, "messageHeadline": "feature"}],
        }
        self.gh_json.write_text(json.dumps(metadata), encoding="utf-8")
        self.repo_json.write_text(
            json.dumps({"id": 12345, "nameWithOwner": base_identity}),
            encoding="utf-8",
        )
        self.api_json.write_text(
            json.dumps(
                {
                    "ref": "refs/heads/main",
                    "object": {"type": "commit", "sha": authoritative_sha},
                }
            ),
            encoding="utf-8",
        )
        gh = self.bin / "gh"
        gh.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "case \"${1:-}\" in\n"
            "  pr) cat \"$GH_PR_JSON\" ;;\n"
            "  repo) printf '%s\\n' \"${3:-}\" >> \"$GH_REPO_SELECTOR\"; cat \"$GH_REPO_JSON\" ;;\n"
            "  api) printf '%s %s\\n' \"${3:-}\" \"${4:-}\" > \"$GH_API_REQUEST\"; cat \"$GH_API_JSON\" ;;\n"
            "  *) exit 97 ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        gh.chmod(0o755)

    def environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        environment["PATH"] = f"{self.bin}{os.pathsep}{environment['PATH']}"
        environment["GH_PR_JSON"] = str(self.gh_json)
        environment["GH_REPO_JSON"] = str(self.repo_json)
        environment["GH_REPO_SELECTOR"] = str(self.repo_selector)
        environment["GH_API_JSON"] = str(self.api_json)
        environment["GH_API_REQUEST"] = str(self.api_request)
        environment["GIT_CONFIG_NOSYSTEM"] = "1"
        environment["GIT_TERMINAL_PROMPT"] = "0"
        return environment

    def run_helper(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(HELPER), "90"],
            cwd=self.work,
            env=self.environment(),
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )


class DescriptionContextTests(unittest.TestCase):
    def test_correct_fork_and_base_mapping_produces_verified_diff(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = Fixture(Path(raw))
            base_sha = fixture.seed_remote(fixture.base, "baseline.txt", "base\n")
            fork = Path(raw) / "fork.git"
            fixture.init_bare(fork)
            head_sha = fixture.make_work_from("upstream", "example/base", fixture.base)
            fixture.add_remote(fixture.work, "origin", "example/fork", fork)
            fixture.git(fixture.work, "push", "--quiet", "origin", "feature")
            fixture.add_gh_stub(
                base_identity="example/base",
                head_identity="example/fork",
                base_sha=base_sha,
                head_sha=head_sha,
            )

            result = fixture.run_helper()

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Base repository: example/base", result.stdout)
            self.assertIn("Base SHA: " + base_sha, result.stdout)
            self.assertIn("PR metadata base SHA (historical): " + base_sha, result.stdout)
            self.assertIn("feature.txt", result.stdout)
            self.assertIn("Existing body", result.stdout)
            self.assertNotIn("unavailable", result.stderr)

    def test_misleading_same_name_upstream_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = Fixture(Path(raw))
            base_sha = fixture.seed_remote(fixture.base, "baseline.txt", "base\n")
            wrong = Path(raw) / "wrong.git"
            wrong_sha = fixture.seed_remote(wrong, "baseline.txt", "wrong\n")
            self.assertNotEqual(base_sha, wrong_sha)
            head_sha = fixture.make_work_from("origin", "example/base", fixture.base)
            fixture.add_remote(fixture.work, "upstream", "other/base", wrong)
            fixture.add_gh_stub(
                base_identity="example/base",
                head_identity="example/fork",
                base_sha=base_sha,
                head_sha=head_sha,
            )

            result = fixture.run_helper()

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("feature.txt", result.stdout)
            self.assertNotIn("resolved to " + wrong_sha, result.stderr)

    def test_stale_tracking_ref_after_fetch_failure_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = Fixture(Path(raw))
            base_sha = fixture.seed_remote(fixture.base, "baseline.txt", "base\n")
            head_sha = fixture.make_work_from("upstream", "example/base", fixture.base)
            fixture.base.rename(Path(raw) / "base-offline.git")
            fixture.add_gh_stub(
                base_identity="example/base",
                head_identity="example/fork",
                base_sha=base_sha,
                head_sha=head_sha,
            )

            result = fixture.run_helper()

            self.assertEqual(result.returncode, 2)
            self.assertIn("Diff context: unavailable", result.stderr)
            self.assertIn("could not fetch", result.stderr)
            self.assertNotIn("=== Diff Stat", result.stdout)

    def test_fetched_base_sha_mismatch_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = Fixture(Path(raw))
            wrong = Path(raw) / "wrong.git"
            wrong_sha = fixture.seed_remote(wrong, "baseline.txt", "wrong\n")
            head_sha = fixture.make_work_from("origin", "example/base", wrong)
            expected_sha = "0" * 40
            fixture.add_gh_stub(
                base_identity="example/base",
                head_identity="example/fork",
                base_sha=expected_sha,
                head_sha=head_sha,
            )

            result = fixture.run_helper()

            self.assertEqual(result.returncode, 2)
            self.assertIn("resolved to " + wrong_sha, result.stderr)
            self.assertIn("Diff context: unavailable", result.stderr)
            self.assertNotIn("=== Diff Stat", result.stdout)

    def test_mismatched_local_head_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = Fixture(Path(raw))
            base_sha = fixture.seed_remote(fixture.base, "baseline.txt", "base\n")
            local_head = fixture.make_work_from("origin", "example/base", fixture.base)
            fixture.add_gh_stub(
                base_identity="example/base",
                head_identity="example/fork",
                base_sha=base_sha,
                head_sha="f" * 40,
            )

            result = fixture.run_helper()

            self.assertEqual(result.returncode, 2)
            self.assertIn("local HEAD (" + local_head + ") does not match", result.stdout)
            self.assertIn("local HEAD does not match PR head SHA", result.stderr)
            self.assertNotIn("=== Diff Stat", result.stdout)

    def test_enterprise_host_is_passed_to_repo_selector(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = Fixture(Path(raw))
            host = "ghe.example.invalid"
            base_sha = fixture.seed_remote(fixture.base, "baseline.txt", "base\n")
            head_sha = fixture.make_work_from("upstream", "example/base", fixture.base, host)
            fixture.add_gh_stub(
                base_identity="example/base",
                head_identity="example/fork",
                base_sha=base_sha,
                head_sha=head_sha,
                host=host,
            )

            result = fixture.run_helper()

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                fixture.repo_selector.read_text(encoding="utf-8").strip(),
                f"{host}/example/base\n{host}/example/base",
            )
            self.assertEqual(
                fixture.api_request.read_text(encoding="utf-8").strip(),
                f"{host} repos/example/base/git/ref/heads/main",
            )
            self.assertIn("feature.txt", result.stdout)

    def test_authoritative_base_advancement_overrides_cached_pr_oid(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = Fixture(Path(raw))
            cached_sha = fixture.seed_remote(fixture.base, "baseline.txt", "base\n")
            authoritative_sha = fixture.advance_remote(
                fixture.base, "advanced.txt", "current\n"
            )
            self.assertNotEqual(cached_sha, authoritative_sha)
            head_sha = fixture.make_work_from("origin", "example/base", fixture.base)
            fixture.add_gh_stub(
                base_identity="example/base",
                head_identity="example/fork",
                base_sha=cached_sha,
                head_sha=head_sha,
                authoritative_sha=authoritative_sha,
            )

            result = fixture.run_helper()

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Base SHA: " + authoritative_sha, result.stdout)
            self.assertIn("PR metadata base SHA (historical): " + cached_sha, result.stdout)
            self.assertIn("feature.txt", result.stdout)


if __name__ == "__main__":
    unittest.main()
