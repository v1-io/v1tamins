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
import hmac
import json
import os
import stat as stat_module
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from peer_policy import PROVIDERS  # noqa: E402

_MANIFEST_OPEN = os.open
_MANIFEST_STAT = os.stat
_MANIFEST_READLINK = os.readlink

SCHEMA = "v1-peer-boundary/v1"
SNAPSHOT_NAME = "boundary.snapshot.json"
MAX_SNAPSHOT_BYTES = 64 * 1024 * 1024

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
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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
            encoding="utf-8",
            env=environment,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError, UnicodeError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def repo_state(repo: Path) -> dict[str, Any]:
    """Working-tree state that a read-only seat must leave untouched."""

    status = git_output(repo, ["status", "--porcelain", "-uall"])
    head = git_output(repo, ["rev-parse", "HEAD"])
    index = git_output(repo, ["ls-files", "--stage", "-z"])
    return {
        "path": str(repo),
        "readable": status is not None,
        "status_digest": digest(status) if status is not None else None,
        "head": head.strip() if head else None,
        "index_digest": digest(index) if index is not None else None,
    }


@dataclass
class _ManifestDirectory:
    """An open directory kept alive while its children are observed."""

    path: Path
    relative: str
    fd: int
    expected: tuple[int, ...]
    parent: _ManifestDirectory | None = None
    parent_name: str | None = None
    iterator: Any = None
    scandir_context: Any = None


def _manifest_stat_key(value: os.stat_result) -> tuple[int, ...]:
    """Return identity and mutation metadata for one filesystem object."""

    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _manifest_descriptor_support() -> bool:
    """Check the primitives needed for a no-follow descriptor walk."""

    return bool(
        hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
        and hasattr(os, "O_NONBLOCK")
        and hasattr(os, "scandir")
        and hasattr(os, "supports_dir_fd")
        and _MANIFEST_OPEN in os.supports_dir_fd
        and _MANIFEST_STAT in os.supports_dir_fd
        and _MANIFEST_READLINK in os.supports_dir_fd
    )


def _manifest_relative(root: Path, child: Path) -> str | None:
    """Compute a lexical relative name without resolving symlinks."""

    try:
        root_abs = Path(os.path.abspath(root))
        child_abs = Path(os.path.abspath(child))
        return str(child_abs.relative_to(root_abs))
    except (OSError, RuntimeError, ValueError):
        return None


def _manifest_close_directory(frame: _ManifestDirectory) -> None:
    """Close a scan frame without masking the original observation result."""

    context = frame.scandir_context
    frame.iterator = None
    frame.scandir_context = None
    if context is not None:
        try:
            context.__exit__(None, None, None)
        except OSError:
            pass
    try:
        os.close(frame.fd)
    except OSError:
        pass


def scan_manifest(
    root: Path,
    budget: int = DEFAULT_VISIT_BUDGET,
    hash_budget: int = DEFAULT_MANIFEST_HASH_BUDGET,
) -> ManifestScan:
    """Capture a bounded manifest with descriptor-relative no-follow reads.

    Every recursive directory stays open while its children are inspected. A
    pathname is used only for display and identity checks; directory listings,
    symlink reads, and file opens are relative to the pinned parent descriptor.
    Any unsupported primitive or identity mismatch makes this observation
    incomplete instead of risking a read outside the declared root.
    """

    try:
        root_stat = root.lstat()
    except FileNotFoundError:
        return ManifestScan(str(root), False, {}, 0, 0, False, False)
    except OSError:
        return ManifestScan(str(root), False, {}, 0, 0, False, True)
    if stat_module.S_ISLNK(root_stat.st_mode):
        return ManifestScan(str(root), True, {}, 0, 0, False, True)
    if not stat_module.S_ISDIR(root_stat.st_mode):
        return ManifestScan(str(root), True, {}, 0, 0, False, True)
    if not _manifest_descriptor_support():
        return ManifestScan(str(root), True, {}, 0, 0, False, True)

    entries: dict[str, str] = {}
    visited = 0
    hashed_bytes = 0
    truncated = False
    errors = False
    root_key = _manifest_stat_key(root_stat)
    root_resolved: Path
    try:
        root_resolved = root.resolve(strict=False)
    except (OSError, RuntimeError):
        return ManifestScan(str(root), True, {}, 0, 0, False, True)

    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        directory_flags |= os.O_CLOEXEC
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    if hasattr(os, "O_CLOEXEC"):
        file_flags |= os.O_CLOEXEC

    try:
        root_fd = os.open(root, directory_flags)
    except OSError:
        return ManifestScan(str(root), True, {}, 0, 0, False, True)
    stack: list[_ManifestDirectory] = []
    try:
        try:
            if _manifest_stat_key(os.fstat(root_fd)) != root_key:
                return ManifestScan(str(root), True, {}, 0, 0, False, True)
        except OSError:
            return ManifestScan(str(root), True, {}, 0, 0, False, True)

        stack = [
            _ManifestDirectory(root, "", root_fd, root_key)
        ]
        root_fd = -1  # The stack now owns this descriptor.
        stop = False

        def close_all() -> None:
            while stack:
                _manifest_close_directory(stack.pop())

        while stack and not stop:
            current = stack[-1]
            if current.iterator is None:
                try:
                    if _manifest_stat_key(os.fstat(current.fd)) != current.expected:
                        errors = True
                        _manifest_close_directory(stack.pop())
                        continue
                    if _manifest_stat_key(current.path.lstat()) != current.expected:
                        errors = True
                        _manifest_close_directory(stack.pop())
                        continue
                    scanned = os.scandir(current.fd)
                    current.scandir_context = scanned
                    current.iterator = scanned.__enter__()
                except (OSError, TypeError):
                    errors = True
                    _manifest_close_directory(stack.pop())
                    continue

            try:
                entry = next(current.iterator)
            except StopIteration:
                current.iterator = None
                try:
                    if _manifest_stat_key(os.fstat(current.fd)) != current.expected:
                        errors = True
                    if _manifest_stat_key(current.path.lstat()) != current.expected:
                        errors = True
                    if current.parent is not None and current.parent_name is not None:
                        parent_stat = os.stat(
                            current.parent_name,
                            dir_fd=current.parent.fd,
                            follow_symlinks=False,
                        )
                        if _manifest_stat_key(parent_stat) != current.expected:
                            errors = True
                except OSError:
                    errors = True
                _manifest_close_directory(stack.pop())
                continue
            except OSError:
                errors = True
                _manifest_close_directory(stack.pop())
                continue

            if visited >= budget:
                truncated = True
                stop = True
                close_all()
                break
            visited += 1

            name = entry.name
            child = current.path / name
            relative = _manifest_relative(root, child)
            try:
                if relative is None:
                    raise ValueError("entry escaped declared root")
                relative.encode("utf-8")
                item_stat = os.stat(name, dir_fd=current.fd, follow_symlinks=False)
            except (OSError, UnicodeError, ValueError):
                errors = True
                continue

            mode = item_stat.st_mode
            if stat_module.S_ISDIR(mode):
                metadata = f"dir:{mode:o}:{item_stat.st_mtime_ns}:{item_stat.st_size}"
                child_flags = directory_flags
                child_fd: int | None = None
                try:
                    child_fd = os.open(name, child_flags, dir_fd=current.fd)
                    child_key = _manifest_stat_key(os.fstat(child_fd))
                except OSError:
                    errors = True
                    entries[relative] = f"{metadata}:racy"
                    if child_fd is not None:
                        try:
                            os.close(child_fd)
                        except OSError:
                            pass
                    continue
                if child_key != _manifest_stat_key(item_stat):
                    errors = True
                    entries[relative] = f"{metadata}:racy"
                    os.close(child_fd)
                    continue
                entries[relative] = metadata
                stack.append(
                    _ManifestDirectory(
                        child,
                        relative,
                        child_fd,
                        child_key,
                        current,
                        name,
                    )
                )
                continue

            if stat_module.S_ISLNK(mode):
                try:
                    target = os.readlink(name, dir_fd=current.fd)
                    if _manifest_stat_key(
                        os.stat(name, dir_fd=current.fd, follow_symlinks=False)
                    ) != _manifest_stat_key(item_stat):
                        raise OSError("symlink identity changed during observation")
                    str(target).encode("utf-8")
                    resolved_target = (child.parent / target).resolve(strict=False)
                    resolved_target.relative_to(root_resolved)
                except OSError:
                    errors = True
                    target = "<unreadable>"
                except (RuntimeError, ValueError, UnicodeError):
                    errors = True
                    target = "<unreadable>"
                entries[relative] = f"link:{mode:o}:{item_stat.st_mtime_ns}:{target}"
                continue

            if stat_module.S_ISREG(mode):
                metadata = f"file:{mode:o}:{item_stat.st_size}:{item_stat.st_mtime_ns}"
                if (
                    item_stat.st_size > hash_budget
                    or hashed_bytes + item_stat.st_size > hash_budget
                ):
                    entries[relative] = f"{metadata}:opaque"
                    truncated = True
                    continue
                hasher = hashlib.sha256()
                bytes_read = 0
                fd: int | None = None
                try:
                    fd = os.open(name, file_flags, dir_fd=current.fd)
                    with os.fdopen(fd, "rb") as handle:
                        fd = None
                        opened_key = _manifest_stat_key(os.fstat(handle.fileno()))
                        if opened_key != _manifest_stat_key(item_stat):
                            hashed_bytes += bytes_read
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
                        if _manifest_stat_key(os.fstat(handle.fileno())) != _manifest_stat_key(item_stat):
                            hashed_bytes += bytes_read
                            errors = True
                            entries[relative] = f"{metadata}:racy"
                            continue
                except OSError:
                    hashed_bytes += bytes_read
                    errors = True
                    entries[relative] = f"{metadata}:unreadable"
                    continue
                finally:
                    if fd is not None:
                        try:
                            os.close(fd)
                        except OSError:
                            pass
                hashed_bytes += bytes_read
                try:
                    current_stat = os.stat(
                        name, dir_fd=current.fd, follow_symlinks=False
                    )
                except OSError:
                    errors = True
                    entries[relative] = f"{metadata}:racy"
                    continue
                if (
                    bytes_read != item_stat.st_size
                    or _manifest_stat_key(current_stat)
                    != _manifest_stat_key(item_stat)
                ):
                    errors = True
                    entries[relative] = f"{metadata}:racy"
                    continue
                entries[relative] = f"{metadata}:sha256={hasher.hexdigest()}"
                continue

            # Device files, FIFOs, and sockets cannot be content-observed safely.
            errors = True
            entries[relative] = f"other:{mode:o}:{item_stat.st_mtime_ns}"

    finally:
        while stack:
            _manifest_close_directory(stack.pop())
        if root_fd != -1:
            os.close(root_fd)

    return ManifestScan(str(root), True, entries, visited, hashed_bytes, truncated, errors)


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


def validate_layout(run_dir: Path, repo: Path) -> None:
    run_dir, repo = run_dir.resolve(), repo.resolve()
    if run_dir == repo or repo in run_dir.parents or run_dir in repo.parents:
        raise ValueError("peer scratch directory and repository must not overlap")


def take_snapshot(
    run_dir: Path, repo: Path, provider: str, home: Path
) -> dict[str, Any]:
    validate_layout(run_dir, repo)
    run_dir, repo = run_dir.resolve(), repo.resolve()
    spec = PROVIDERS.get(provider)
    home = home.resolve()
    roots = state_roots(provider, home)
    run_dir.mkdir(parents=True, exist_ok=True)
    scratch_manifest = scan_manifest(run_dir)
    repo_manifest, metadata_root, metadata_scope_error = scan_repository_manifest(repo)
    state_manifests = [scan_manifest(root) for root in roots]
    snapshot = {
        "schema": SCHEMA,
        "provider": provider,
        "home": str(home),
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
    return snapshot


def write_owner_snapshot(snapshot: dict[str, Any]) -> dict[str, str]:
    """Return a receipt for an owner-held baseline outside observed roots.

    The caller must retain this receipt, rather than recover its digest from
    peer-writable files. Same-user filesystem access is not OS isolation.
    """

    content = json.dumps(snapshot, sort_keys=True).encode("utf-8")
    if len(content) > MAX_SNAPSHOT_BYTES:
        raise ValueError("boundary snapshot exceeds the byte limit")
    roots = [Path(snapshot["run_dir"]), Path(snapshot["repo"]["path"])]
    roots.extend(Path(value) for value in snapshot["state_roots"])
    with tempfile.NamedTemporaryFile(prefix="v1-peer-boundary-", suffix=".json", delete=False) as handle:
        path = Path(handle.name).resolve()
        try:
            if any(path == root or root in path.parents for root in roots):
                raise ValueError("owner snapshot must be outside observed roots")
            handle.write(content)
        except BaseException:
            path.unlink()
            raise
    return {"schema": SCHEMA, "snapshot_path": str(path),
            "snapshot_sha256": hashlib.sha256(content).hexdigest()}


def snapshot_unverified(detail: str) -> dict[str, Any]:
    return {"schema": SCHEMA, "containment": "unverified",
            "permission_state": "containment_unverified", "detail": detail}


def validate_snapshot_identity(snapshot: Any, run_dir: Path, path: Path) -> None:
    """Validate authenticated observation identities before using any roots."""

    if not isinstance(snapshot, dict) or snapshot.get("schema") != SCHEMA:
        raise ValueError("unsupported boundary snapshot")
    provider = snapshot.get("provider")
    if not isinstance(provider, str) or provider not in PROVIDERS:
        raise ValueError("invalid boundary provider")
    repo = snapshot.get("repo")
    if not isinstance(repo, dict) or not isinstance(repo.get("path"), str):
        raise ValueError("invalid repository identity")
    repo_path = Path(repo["path"])
    if not repo_path.is_absolute() or str(repo_path) != str(repo_path.resolve()):
        raise ValueError("repository identity is not canonical")
    if snapshot.get("run_dir") != str(run_dir.resolve()):
        raise ValueError("boundary run directory does not match caller")
    validate_layout(run_dir, repo_path)
    home = snapshot.get("home")
    if not isinstance(home, str) or not Path(home).is_absolute():
        raise ValueError("invalid provider home identity")
    roots = state_roots(provider, Path(home))
    if snapshot.get("state_roots") != [str(root) for root in roots]:
        raise ValueError("provider roots do not match provider policy")
    if snapshot.get("state_isolation") != PROVIDERS[provider].state_isolation:
        raise ValueError("provider isolation does not match provider policy")
    if any(root == path or root in path.parents for root in [run_dir.resolve(), repo_path, *roots]):
        raise ValueError("owner snapshot is inside an observed root")
    manifests = [snapshot.get("repo_manifest"), snapshot.get("scratch_manifest")]
    provider_manifests = snapshot.get("state_manifests")
    if not isinstance(provider_manifests, list) or len(provider_manifests) != len(roots):
        raise ValueError("provider manifest identities missing")
    manifests.extend(provider_manifests)
    for manifest, root in zip(manifests, [repo_path, run_dir.resolve(), *roots]):
        if not isinstance(manifest, dict) or manifest.get("root") != str(root):
            raise ValueError("manifest root identity mismatch")
        if any(type(manifest.get(key)) is not bool for key in ("exists", "truncated", "errors")):
            raise ValueError("invalid manifest observation state")
        entries = manifest.get("entries")
        if not isinstance(entries, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in entries.items()):
            raise ValueError("invalid manifest entries")
    scope = snapshot.get("repo_manifest_scope")
    if not isinstance(scope, dict) or scope.get("checkout") != str(repo_path):
        raise ValueError("repository manifest scope mismatch")


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


def verify_snapshot(run_dir: Path, budget: int = DEFAULT_VISIT_BUDGET, *,
                    snapshot_path: Path | None = None,
                    snapshot_sha256: str | None = None) -> dict[str, Any]:
    if snapshot_path is None or not isinstance(snapshot_sha256, str) or len(snapshot_sha256) != 64 or any(c not in "0123456789abcdef" for c in snapshot_sha256):
        return snapshot_unverified("owner-held snapshot receipt required")
    try:
        flags = os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW
        with os.fdopen(os.open(snapshot_path, flags), "rb") as handle:
            if not stat_module.S_ISREG(os.fstat(handle.fileno()).st_mode):
                return snapshot_unverified("boundary snapshot is not a regular file")
            content = handle.read(MAX_SNAPSHOT_BYTES + 1)
        if len(content) > MAX_SNAPSHOT_BYTES or not hmac.compare_digest(hashlib.sha256(content).hexdigest(), snapshot_sha256):
            return snapshot_unverified("boundary snapshot integrity mismatch")
        snapshot = json.loads(content.decode("utf-8"))
        validate_snapshot_identity(snapshot, run_dir, snapshot_path.resolve())
    except (OSError, ValueError, UnicodeError, RuntimeError, AttributeError):
        return snapshot_unverified("boundary snapshot unavailable or invalid")

    before = snapshot.get("repo", {})
    repo_path = Path(before.get("path", "."))
    after = repo_state(repo_path)
    repo_readable = bool(before.get("readable")) and after["readable"]
    status_changed = repo_readable and (
        before.get("status_digest") != after["status_digest"]
        or before.get("head") != after["head"]
        or (before.get("index_digest") is not None and after["index_digest"] is not None
            and before["index_digest"] != after["index_digest"])
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
    if not repo_readable or before.get("index_digest") is None or after.get("index_digest") is None:
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

    layout = subcommands.add_parser("check-layout", help="require disjoint scratch and repository roots")
    layout.add_argument("--run-dir", required=True)
    layout.add_argument("--repo", required=True)

    verify = subcommands.add_parser("verify", help="report what the run wrote")
    verify.add_argument("--run-dir", required=True)
    verify.add_argument("--visit-budget", type=int, default=DEFAULT_VISIT_BUDGET)
    verify.add_argument("--snapshot-path")
    verify.add_argument("--snapshot-sha256")

    plan = subcommands.add_parser("plan", help="print any env redirection to apply")
    plan.add_argument("--run-dir", required=True)
    plan.add_argument("--provider", required=True, choices=tuple(PROVIDERS))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    home = Path(getattr(args, "home", None) or Path.home())
    if args.command == "check-layout":
        try:
            validate_layout(Path(args.run_dir), Path(args.repo))
        except ValueError as error:
            print(json.dumps({"schema": SCHEMA, "error": str(error)}), file=sys.stderr)
            return 2
        return 0
    if args.command == "snapshot":
        try:
            snapshot = take_snapshot(
                Path(args.run_dir), Path(args.repo).resolve(), args.provider, home
            )
            receipt = write_owner_snapshot(snapshot)
        except (OSError, ValueError) as error:
            print(json.dumps({"schema": SCHEMA, "error": str(error)}), file=sys.stderr)
            return 2
        print(json.dumps(receipt, sort_keys=True))
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
            verify_snapshot(Path(args.run_dir), args.visit_budget,
                            snapshot_path=Path(args.snapshot_path) if args.snapshot_path else None,
                            snapshot_sha256=args.snapshot_sha256),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
