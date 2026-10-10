#!/usr/bin/env python3
"""Observe and report what a peer run actually wrote.

A sandbox flag and a prompt instruction are not proof. A seat approved as
``readonly`` can still write a provider-owned session file or report outside
the reviewed checkout, and reading the checkout's Git state alone will never
show it. This module records the boundary before launch and reports afterwards
what changed inside the repository, inside the disposable run directory, and
inside the provider's own state directories.

It never redirects ``$HOME`` by default: a subscription peer keeps its login
state there, and moving it would break the auth the run depends on. Redirection
happens only where a provider documents a variable for it. Everywhere else the
boundary is observed and any gap is reported as a typed degradation rather than
being claimed as clean.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat as stat_module
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from peer_policy import PROVIDERS  # noqa: E402

SCHEMA = "v1-peer-boundary/v1"
SNAPSHOT_NAME = "boundary.snapshot.json"

# A walk that would exceed this budget cannot prove containment, so it stops
# and reports the gap instead of spending unbounded time.
DEFAULT_VISIT_BUDGET = 50000
# Content hashes make the before/after manifest useful for ignored files whose
# size and timestamps happen to stay the same. A large or over-budget tree is
# deliberately an unverified boundary instead of a claim based on metadata.
DEFAULT_MANIFEST_HASH_BUDGET = 64 * 1024 * 1024
MANIFEST_CHANGE_LIMIT = 200

# Sentinels the runner itself writes into the run directory.
RUNNER_ARTIFACTS = frozenset(
    {
        "peer.pid",
        "peer.child.pid",
        "peer.session",
        "peer.done",
        "peer.deadline",
        "peer.watchdog.pid",
        "peer.stdout",
        "peer.stderr",
        SNAPSHOT_NAME,
    }
)

Containment = Literal["verified", "unverified"]
PermissionState = Literal[
    "readonly_verified",
    "readonly_degraded_provider_state",
    "readonly_violated",
    "containment_unverified",
]


@dataclass(frozen=True)
class ManifestScan:
    """Bounded before/after filesystem observation for one declared root."""

    root: str
    exists: bool
    entries: dict[str, str]
    visited: int
    hashed_bytes: int
    truncated: bool
    errors: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "exists": self.exists,
            "entries": dict(sorted(self.entries.items())),
            "visited": self.visited,
            "hashed_bytes": self.hashed_bytes,
            "truncated": self.truncated,
            "errors": self.errors,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "exists": self.exists,
            "visited": self.visited,
            "hashed_bytes": self.hashed_bytes,
            "truncated": self.truncated,
            "errors": self.errors,
        }


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def git_output(repo: Path, args: list[str]) -> str | None:
    environment = os.environ.copy()
    # status may refresh the index unless this is explicitly disabled. A
    # read-only observation must not create its own metadata change.
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=False,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            errors="replace",
            env=environment,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def repo_state(repo: Path) -> dict[str, Any]:
    """Working-tree state that a read-only seat must leave untouched."""

    status = git_output(repo, ["status", "--porcelain", "-uall"])
    head = git_output(repo, ["rev-parse", "HEAD"])
    return {
        "path": str(repo),
        "readable": status is not None,
        "status_digest": digest(status) if status is not None else None,
        "head": head.strip() if head else None,
    }


def scan_manifest(
    root: Path,
    budget: int = DEFAULT_VISIT_BUDGET,
    hash_budget: int = DEFAULT_MANIFEST_HASH_BUDGET,
) -> ManifestScan:
    """Capture a bounded manifest without following symlinks.

    The repository manifest intentionally includes the checkout's `.git`
    metadata because that is the explicit repository boundary. Provider roots
    are limited to the home-relative paths declared by ``peer_policy``; this
    function never walks the rest of a user's home directory.
    """

    try:
        root_stat = root.lstat()
    except FileNotFoundError:
        return ManifestScan(str(root), False, {}, 0, 0, False, False)
    except OSError:
        return ManifestScan(str(root), False, {}, 0, 0, False, True)
    if stat_module.S_ISLNK(root_stat.st_mode):
        # A declared root that is itself a symlink could escape the observed
        # boundary. Keep the path visible but fail closed.
        return ManifestScan(str(root), True, {}, 0, 0, False, True)
    if not stat_module.S_ISDIR(root_stat.st_mode):
        return ManifestScan(str(root), True, {}, 0, 0, False, True)

    entries: dict[str, str] = {}
    visited = 0
    hashed_bytes = 0
    truncated = False
    errors = False
    stack = [root]

    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as children:
                for entry in children:
                    if visited >= budget:
                        truncated = True
                        stack.clear()
                        break
                    visited += 1
                    child = Path(entry.path)
                    try:
                        item_stat = child.stat(follow_symlinks=False)
                    except OSError:
                        errors = True
                        continue

                    relative = str(child.relative_to(root))
                    mode = item_stat.st_mode
                    if stat_module.S_ISDIR(mode):
                        entries[relative] = (
                            f"dir:{mode:o}:{item_stat.st_mtime_ns}:{item_stat.st_size}"
                        )
                        stack.append(child)
                        continue
                    if stat_module.S_ISLNK(mode):
                        try:
                            target = child.readlink()
                            resolved_target = (child.parent / target).resolve(strict=False)
                            resolved_target.relative_to(root.resolve(strict=False))
                        except OSError:
                            errors = True
                            target = "<unreadable>"
                        except (RuntimeError, ValueError):
                            errors = True
                        entries[relative] = (
                            f"link:{mode:o}:{item_stat.st_mtime_ns}:{target}"
                        )
                        continue
                    if stat_module.S_ISREG(mode):
                        metadata = (
                            f"file:{mode:o}:{item_stat.st_size}:{item_stat.st_mtime_ns}"
                        )
                        if (
                            item_stat.st_size > hash_budget
                            or hashed_bytes + item_stat.st_size > hash_budget
                        ):
                            # Metadata is retained for useful diagnostics, but this
                            # scan cannot support a clean claim without the content.
                            entries[relative] = f"{metadata}:opaque"
                            truncated = True
                            continue
                        hasher = hashlib.sha256()
                        bytes_read = 0
                        try:
                            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                            with os.fdopen(os.open(child, flags), "rb") as handle:
                                opened_stat = os.fstat(handle.fileno())
                                if (
                                    opened_stat.st_dev,
                                    opened_stat.st_ino,
                                    opened_stat.st_mode,
                                    opened_stat.st_size,
                                    opened_stat.st_mtime_ns,
                                    opened_stat.st_ctime_ns,
                                ) != (
                                    item_stat.st_dev,
                                    item_stat.st_ino,
                                    item_stat.st_mode,
                                    item_stat.st_size,
                                    item_stat.st_mtime_ns,
                                    item_stat.st_ctime_ns,
                                ):
                                    errors = True
                                    entries[relative] = f"{metadata}:racy"
                                    continue
                                while bytes_read < item_stat.st_size:
                                    chunk = handle.read(
                                        min(1024 * 1024, item_stat.st_size - bytes_read)
                                    )
                                    if not chunk:
                                        break
                                    hasher.update(chunk)
                                    bytes_read += len(chunk)
                        except OSError:
                            hashed_bytes += bytes_read
                            errors = True
                            entries[relative] = f"{metadata}:unreadable"
                            continue
                        hashed_bytes += bytes_read
                        try:
                            current_stat = child.stat(follow_symlinks=False)
                        except OSError:
                            errors = True
                            entries[relative] = f"{metadata}:racy"
                            continue
                        if (
                            bytes_read != item_stat.st_size
                            or (
                                current_stat.st_dev,
                                current_stat.st_ino,
                                current_stat.st_mode,
                                current_stat.st_size,
                                current_stat.st_mtime_ns,
                                current_stat.st_ctime_ns,
                            )
                            != (
                                item_stat.st_dev,
                                item_stat.st_ino,
                                item_stat.st_mode,
                                item_stat.st_size,
                                item_stat.st_mtime_ns,
                                item_stat.st_ctime_ns,
                            )
                        ):
                            errors = True
                            entries[relative] = f"{metadata}:racy"
                            continue
                        entries[relative] = f"{metadata}:sha256={hasher.hexdigest()}"
                        continue

                    # Device files, FIFOs, and sockets cannot be content-observed
                    # safely as part of a read-only manifest.
                    errors = True
                    entries[relative] = f"other:{mode:o}:{item_stat.st_mtime_ns}"
        except OSError:
            errors = True

    return ManifestScan(
        str(root),
        True,
        entries,
        visited,
        hashed_bytes,
        truncated,
        errors,
    )


def git_metadata_scope(repo: Path) -> tuple[Path | None, bool]:
    """Resolve the exact Git metadata root without scanning a user's home."""

    git_entry = repo / ".git"
    try:
        git_stat = git_entry.lstat()
    except FileNotFoundError:
        return None, False
    except OSError:
        return None, True
    if stat_module.S_ISDIR(git_stat.st_mode):
        return git_entry, False
    if not stat_module.S_ISREG(git_stat.st_mode):
        return None, True
    try:
        pointer = git_entry.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None, True
    if not pointer.startswith("gitdir:"):
        return None, True
    raw_target = pointer[len("gitdir:") :].strip()
    if not raw_target:
        return None, True
    target = Path(raw_target)
    if not target.is_absolute():
        target = git_entry.parent / target
    return target, False


def scan_repository_manifest(
    repo: Path,
    budget: int = DEFAULT_VISIT_BUDGET,
    hash_budget: int = DEFAULT_MANIFEST_HASH_BUDGET,
) -> tuple[ManifestScan, Path | None, bool]:
    """Scan checkout files and identify the exact Git metadata scope.

    A linked worktree stores only a pointer in ``repo/.git`` while its index,
    logs, and other mutable metadata live elsewhere. The pointer itself is
    observed, but the external target (including any ``commondir`` root) is
    deliberately left unscanned and makes the boundary unverified.
    """

    checkout = scan_manifest(repo, budget, hash_budget)
    metadata_root, scope_error = git_metadata_scope(repo)
    if metadata_root is not None and metadata_root != repo / ".git":
        scope_error = True
    return checkout, metadata_root, scope_error


def manifest_changed_paths(
    before: dict[str, Any] | None, after: ManifestScan
) -> list[str]:
    """Return bounded paths whose before/after manifest entries differ."""

    if not isinstance(before, dict):
        return []
    if before.get("exists") != after.exists:
        return ["<root>"]
    previous_entries = before.get("entries")
    if not isinstance(previous_entries, dict):
        return []
    changed = sorted(
        key
        for key in set(previous_entries) | set(after.entries)
        if previous_entries.get(key) != after.entries.get(key)
    )
    if len(changed) > MANIFEST_CHANGE_LIMIT:
        return [*changed[:MANIFEST_CHANGE_LIMIT], "<change-list-truncated>"]
    return changed


def manifest_observation_complete(
    before: dict[str, Any] | None, after: ManifestScan
) -> bool:
    """Whether both sides contain enough evidence for a clean claim."""

    return (
        isinstance(before, dict)
        and isinstance(before.get("entries"), dict)
        and not bool(before.get("truncated"))
        and not bool(before.get("errors"))
        and not after.truncated
        and not after.errors
    )


def manifest_summary(value: dict[str, Any] | None) -> dict[str, Any] | None:
    """Keep the verdict small while retaining scan quality evidence."""

    if not isinstance(value, dict):
        return None
    return {
        key: value.get(key)
        for key in (
            "root",
            "exists",
            "visited",
            "hashed_bytes",
            "truncated",
            "errors",
        )
    }


def state_roots(provider: str, home: Path) -> list[Path]:
    spec = PROVIDERS.get(provider)
    if spec is None:
        return []
    return [home / name for name in spec.state_dirs]


def env_isolation_overrides(provider: str, run_dir: Path) -> dict[str, str]:
    """Redirect provider state into the run directory when it is documented."""

    spec = PROVIDERS.get(provider)
    if spec is None or spec.state_isolation != "env" or not spec.state_env_var:
        return {}
    target = run_dir / "provider-state"
    target.mkdir(parents=True, exist_ok=True)
    return {spec.state_env_var: str(target)}


def take_snapshot(
    run_dir: Path, repo: Path, provider: str, home: Path
) -> dict[str, Any]:
    spec = PROVIDERS.get(provider)
    roots = state_roots(provider, home)
    run_dir.mkdir(parents=True, exist_ok=True)
    scratch_manifest = scan_manifest(run_dir)
    repo_manifest, metadata_root, metadata_scope_error = scan_repository_manifest(repo)
    state_manifests = [scan_manifest(root) for root in roots]
    snapshot = {
        "schema": SCHEMA,
        "provider": provider,
        "started_at": time.time(),
        "repo": repo_state(repo),
        "repo_manifest": repo_manifest.to_dict(),
        "repo_manifest_scope": {
            "checkout": str(repo),
            "git_metadata": str(metadata_root) if metadata_root else None,
            "error": metadata_scope_error,
        },
        "run_dir": str(run_dir),
        "scratch_manifest": scratch_manifest.to_dict(),
        "state_isolation": spec.state_isolation if spec else "none",
        "state_roots": [str(path) for path in roots],
        "state_manifests": [manifest.to_dict() for manifest in state_manifests],
    }
    (run_dir / SNAPSHOT_NAME).write_text(
        json.dumps(snapshot, sort_keys=True), encoding="utf-8"
    )
    return snapshot


def permission_state(
    repo_changed: bool,
    contained: Containment,
    provider_changes: bool,
) -> PermissionState:
    """A read-only claim is only as strong as what was actually observed."""

    if repo_changed:
        return "readonly_violated"
    if contained != "verified":
        return "containment_unverified"
    if provider_changes:
        return "readonly_degraded_provider_state"
    return "readonly_verified"


def verify_snapshot(run_dir: Path, budget: int = DEFAULT_VISIT_BUDGET) -> dict[str, Any]:
    path = run_dir / SNAPSHOT_NAME
    try:
        snapshot = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "schema": SCHEMA,
            "containment": "unverified",
            "permission_state": "containment_unverified",
            "detail": "no readable boundary snapshot",
        }

    before = snapshot.get("repo", {})
    repo_path = Path(before.get("path", "."))
    after = repo_state(repo_path)
    repo_readable = bool(before.get("readable")) and after["readable"]
    status_changed = repo_readable and (
        before.get("status_digest") != after["status_digest"]
        or before.get("head") != after["head"]
    )
    before_repo_manifest = snapshot.get("repo_manifest")
    after_repo_manifest, metadata_root, metadata_scope_error = scan_repository_manifest(
        repo_path, budget
    )
    before_scope = snapshot.get("repo_manifest_scope")
    if isinstance(before_scope, dict) and before_scope.get("error"):
        metadata_scope_error = True
    repo_manifest_complete = manifest_observation_complete(
        before_repo_manifest, after_repo_manifest
    )
    repo_changed_paths = (
        manifest_changed_paths(before_repo_manifest, after_repo_manifest)
        if repo_manifest_complete
        else []
    )
    repo_manifest_changed = bool(repo_changed_paths)
    repo_changed = bool(status_changed or repo_manifest_changed)

    scratch_root = Path(snapshot.get("run_dir", str(run_dir)))
    before_scratch_manifest = snapshot.get("scratch_manifest")
    after_scratch_manifest = scan_manifest(scratch_root, budget)
    scratch_manifest_complete = manifest_observation_complete(
        before_scratch_manifest, after_scratch_manifest
    )
    scratch_changed_paths = (
        manifest_changed_paths(before_scratch_manifest, after_scratch_manifest)
        if scratch_manifest_complete
        else []
    )
    scratch_artifacts = [
        name for name in scratch_changed_paths if name not in RUNNER_ARTIFACTS
    ]

    roots = [Path(item) for item in snapshot.get("state_roots", [])]
    before_manifests = snapshot.get("state_manifests", [])
    scans = [scan_manifest(root, budget) for root in roots]
    provider_changes: list[dict[str, Any]] = []
    for index, scan in enumerate(scans):
        before_manifest = (
            before_manifests[index]
            if isinstance(before_manifests, list) and index < len(before_manifests)
            else None
        )
        changed = (
            manifest_changed_paths(before_manifest, scan)
            if manifest_observation_complete(before_manifest, scan)
            else []
        )
        if changed:
            provider_changes.append({"root": scan.root, "changed": changed})

    # Containment is about what was observed, not about what was clean.
    contained: Containment = "verified"
    gaps: list[str] = []
    if not repo_readable:
        contained = "unverified"
        gaps.append("repository_state_unreadable")
    if not manifest_observation_complete(before_repo_manifest, after_repo_manifest):
        contained = "unverified"
        gaps.append("repository_manifest_unverified")
    if metadata_scope_error:
        contained = "unverified"
        gaps.append("git_metadata_scope_unverified")
    if not roots:
        contained = "unverified"
        gaps.append("no_declared_provider_state_surface")
    if not isinstance(before_manifests, list) or len(before_manifests) != len(scans):
        contained = "unverified"
        gaps.append("provider_manifest_missing")
    for index, scan in enumerate(scans):
        before_manifest = (
            before_manifests[index]
            if isinstance(before_manifests, list) and index < len(before_manifests)
            else None
        )
        if not manifest_observation_complete(before_manifest, scan):
            contained = "unverified"
            gaps.append(f"provider_manifest_unverified:{index}")
    if not manifest_observation_complete(
        before_scratch_manifest, after_scratch_manifest
    ):
        contained = "unverified"
        gaps.append("scratch_manifest_unverified")

    return {
        "schema": SCHEMA,
        "provider": snapshot.get("provider"),
        "state_isolation": snapshot.get("state_isolation", "none"),
        "repo_changes": {
            "path": str(repo_path),
            "readable": repo_readable,
            "changed": bool(repo_changed),
            "changed_paths": repo_changed_paths,
        },
        "repo_manifest_scan": {
            "before": manifest_summary(before_repo_manifest),
            "after": after_repo_manifest.summary(),
            "git_metadata": str(metadata_root) if metadata_root else None,
        },
        "scratch_artifacts": scratch_artifacts,
        "scratch_manifest_scan": {
            "before": manifest_summary(before_scratch_manifest),
            "after": after_scratch_manifest.summary(),
            "changed": scratch_changed_paths,
        },
        "provider_state_changes": provider_changes,
        "provider_state_scans": [scan.summary() for scan in scans],
        "containment": contained,
        "containment_gaps": gaps,
        "permission_state": permission_state(
            bool(repo_changed), contained, bool(provider_changes)
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    snapshot = subcommands.add_parser("snapshot", help="record the boundary")
    snapshot.add_argument("--run-dir", required=True)
    snapshot.add_argument("--repo", required=True)
    snapshot.add_argument("--provider", required=True, choices=tuple(PROVIDERS))
    snapshot.add_argument("--home", default=None)

    verify = subcommands.add_parser("verify", help="report what the run wrote")
    verify.add_argument("--run-dir", required=True)
    verify.add_argument("--visit-budget", type=int, default=DEFAULT_VISIT_BUDGET)

    plan = subcommands.add_parser("plan", help="print any env redirection to apply")
    plan.add_argument("--run-dir", required=True)
    plan.add_argument("--provider", required=True, choices=tuple(PROVIDERS))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    home = Path(getattr(args, "home", None) or Path.home())
    if args.command == "snapshot":
        take_snapshot(
            Path(args.run_dir), Path(args.repo).resolve(), args.provider, home
        )
        print(json.dumps({"schema": SCHEMA, "snapshot": "recorded"}, sort_keys=True))
        return 0
    if args.command == "plan":
        spec = PROVIDERS[args.provider]
        print(
            json.dumps(
                {
                    "schema": SCHEMA,
                    "state_isolation": spec.state_isolation,
                    "env_overrides": env_isolation_overrides(
                        args.provider, Path(args.run_dir)
                    ),
                },
                sort_keys=True,
            )
        )
        return 0
    print(
        json.dumps(
            verify_snapshot(Path(args.run_dir), args.visit_budget),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
