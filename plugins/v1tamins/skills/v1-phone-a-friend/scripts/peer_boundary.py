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

# Filesystem timestamps are coarse; treat anything within this window of the
# snapshot as possibly written by the run.
CLOCK_SLACK_SECONDS = 2.0
# A walk that would exceed this budget cannot prove containment, so it stops
# and reports the gap instead of spending unbounded time.
DEFAULT_VISIT_BUDGET = 50000

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
class TreeScan:
    """Files under one root that changed after a moment in time."""

    root: str
    exists: bool
    changed: tuple[str, ...]
    visited: int
    truncated: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "exists": self.exists,
            "changed": list(self.changed),
            "visited": self.visited,
            "truncated": self.truncated,
        }


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def git_output(repo: Path, args: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=False,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            errors="replace",
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


def scan_tree(
    root: Path, since: float, budget: int, limit: int = 200
) -> TreeScan:
    """List files under root modified at or after `since`, within a budget."""

    if not root.is_dir():
        return TreeScan(str(root), False, (), 0, False)
    changed: list[str] = []
    visited = 0
    truncated = False
    threshold = since - CLOCK_SLACK_SECONDS
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            children = sorted(current.iterdir())
        except OSError:
            continue
        for child in children:
            if visited >= budget:
                truncated = True
                stack.clear()
                break
            visited += 1
            try:
                stat = child.stat(follow_symlinks=False)
            except OSError:
                continue
            if child.is_dir() and not child.is_symlink():
                stack.append(child)
                continue
            if stat.st_mtime >= threshold:
                if len(changed) < limit:
                    changed.append(str(child.relative_to(root)))
                else:
                    truncated = True
    return TreeScan(str(root), True, tuple(sorted(changed)), visited, truncated)


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
    snapshot = {
        "schema": SCHEMA,
        "provider": provider,
        "started_at": time.time(),
        "repo": repo_state(repo),
        "run_dir": str(run_dir),
        "state_isolation": spec.state_isolation if spec else "none",
        "state_roots": [str(path) for path in state_roots(provider, home)],
    }
    run_dir.mkdir(parents=True, exist_ok=True)
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
    repo_changed = repo_readable and (
        before.get("status_digest") != after["status_digest"]
        or before.get("head") != after["head"]
    )

    started_at = float(snapshot.get("started_at", 0.0))
    scratch = scan_tree(Path(snapshot.get("run_dir", str(run_dir))), started_at, budget)
    scratch_artifacts = [
        name for name in scratch.changed if name not in RUNNER_ARTIFACTS
    ]

    roots = [Path(item) for item in snapshot.get("state_roots", [])]
    scans = [scan_tree(root, started_at, budget) for root in roots]
    provider_changes = [
        {"root": scan.root, "changed": list(scan.changed)}
        for scan in scans
        if scan.changed
    ]

    # Containment is about what was observed, not about what was clean.
    contained: Containment = "verified"
    gaps: list[str] = []
    if not repo_readable:
        contained = "unverified"
        gaps.append("repository_state_unreadable")
    if not roots:
        contained = "unverified"
        gaps.append("no_declared_provider_state_surface")
    if any(scan.truncated for scan in scans) or scratch.truncated:
        contained = "unverified"
        gaps.append("scan_budget_exceeded")

    return {
        "schema": SCHEMA,
        "provider": snapshot.get("provider"),
        "state_isolation": snapshot.get("state_isolation", "none"),
        "repo_changes": {
            "path": str(repo_path),
            "readable": repo_readable,
            "changed": bool(repo_changed),
        },
        "scratch_artifacts": scratch_artifacts,
        "provider_state_changes": provider_changes,
        "provider_state_scans": [scan.to_dict() for scan in scans],
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
