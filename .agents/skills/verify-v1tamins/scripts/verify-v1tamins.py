#!/usr/bin/env python3
"""Drive the v1tamins plugin through headless Claude Code and Codex and keep evidence.

Subcommands (run from anywhere inside the checkout):

  new-run                 create a run directory under .v1tamins/verify/ and print it
  doctor                  read-only check that the runtimes and plugin are worth driving
  claude PROMPT           run one headless Claude Code turn with the checkout plugin loaded
  codex PROMPT            run one headless Codex turn against the installed plugin cache
  route [RUNNER ARGS]     run the repo's live routing eval into this run directory
  cleanup                 stop children this run started, drop scratch, keep evidence

Every command honours --run-dir or V1_VERIFY_RUN_DIR; without either, a new run
directory is created. Evidence files are never deleted by this script.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import shutil
import signal
import struct
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

STRIPPED_ENV = {
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_API_KEY",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "OPENAI_API_KEY",
    "OPENAI_AUTH_TOKEN",
    "CODEX_API_KEY",
}
WRITE_TOOLS = "Bash,Edit,Write,NotebookEdit,WebFetch,WebSearch"


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "plugins" / "v1tamins" / ".claude-plugin" / "plugin.json").is_file():
            return candidate
    sys.exit("verify-v1tamins: could not locate the v1tamins checkout above this script")


def child_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in STRIPPED_ENV}


def resolve_run_dir(root: Path, explicit: str | None) -> Path:
    value = explicit or os.environ.get("V1_VERIFY_RUN_DIR")
    if value:
        run_dir = Path(value).resolve()
    else:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        run_dir = root / ".v1tamins" / "verify" / f"run-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def emit(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def process_identity(pid: int) -> dict | None:
    """Use kernel birth time, not PID alone, to recognize a recorded child."""
    try:
        if sys.platform == "darwin":
            # PROC_PIDTBSDINFO: twelve uint32s, 16/32-byte names, six uint32s,
            # and the process birth time in seconds and microseconds.
            info = ctypes.create_string_buffer(136)
            libproc = ctypes.CDLL("libproc.dylib")
            if libproc.proc_pidinfo(pid, 3, 0, info, len(info)) != len(info):
                return None
            seconds, microseconds = struct.unpack_from("=QQ", info.raw, 120)
            identity = {"start": f"{seconds}:{microseconds}"}
            if struct.unpack_from("=I", info.raw, 4)[0] == 5:  # SZOMB
                identity["exited"] = True
            return identity
        if sys.platform.startswith("linux"):
            fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
            identity = {"start": fields[19]}
            if fields[0] == "Z":
                identity["exited"] = True
            return identity
    except (OSError, ValueError, IndexError):
        pass
    # Persisted PIDs cannot be signalled safely without a process birth identity.
    return None


def record_pid(run_dir: Path, pid: int, label: str) -> Path:
    # One file per child so parallel drives never race on a shared list.
    pids_dir = run_dir / "pids"
    pids_dir.mkdir(exist_ok=True)
    path = pids_dir / f"{pid}.json"
    write_json(path, {"pid": pid, "label": label, "identity": process_identity(pid),
                      "started_at": datetime.now(UTC).isoformat()})
    return path


def signal_child(proc: subprocess.Popen, sig: int) -> None:
    try:
        if os.name == "posix":
            # Every captured child starts a new session; its descendants share
            # the group even when the direct child has already exited.
            os.killpg(proc.pid, sig)
        else:
            proc.send_signal(sig)
    except (ProcessLookupError, PermissionError):
        pass


def captured_text(value: str | bytes | None) -> str:
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""


def stop_capture(proc: subprocess.Popen) -> tuple[str, str]:
    signal_child(proc, signal.SIGTERM)
    try:
        return proc.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        pass
    finally:
        # Parent exit and pipe EOF do not prove the group stopped: a descendant
        # can ignore TERM and redirect stdio. Escalate even after early EOF.
        signal_child(proc, signal.SIGKILL)
    try:
        return proc.communicate(timeout=1)
    except subprocess.TimeoutExpired as exc:
        # An escaped descendant may still hold pipes. Preserve partial proof
        # and close our handles instead of waiting indefinitely for its EOF.
        for stream in (proc.stdout, proc.stderr):
            if stream:
                stream.close()
        try:
            proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        return captured_text(exc.output), captured_text(exc.stderr)


def run_capture(cmd: list[str], *, cwd: Path, timeout: int, run_dir: Path, label: str) -> tuple[int, str, str, float]:
    started = time.monotonic()
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=child_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=os.name == "posix",
    )
    record = record_pid(run_dir, proc.pid, label)
    try:
        try:
            out, err = proc.communicate(timeout=timeout)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            out, err = stop_capture(proc)
            code = 124
            err += f"\nverify-v1tamins: timeout after {timeout}s; bounded process cleanup attempted\n"
        return code, out, err, round(time.monotonic() - started, 3)
    finally:
        if proc.poll() is None:
            stop_capture(proc)
        if proc.poll() is not None:
            record.unlink(missing_ok=True)


def version_of(binary: str | None) -> str | None:
    if not binary:
        return None
    try:
        done = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=30, env=child_env())
    except (OSError, subprocess.TimeoutExpired):
        return None
    return (done.stdout or done.stderr).strip().splitlines()[0] if (done.stdout or done.stderr).strip() else None


def skills_on_disk(root: Path) -> list[str]:
    skills_dir = root / "plugins" / "v1tamins" / "skills"
    return sorted(
        p.name for p in skills_dir.iterdir()
        if p.is_dir() and p.name.startswith("v1-") and not p.name.startswith("v1-_") and (p / "SKILL.md").is_file()
    )


def canonical_version(root: Path) -> str:
    return json.loads((root / "plugins" / "v1tamins" / ".claude-plugin" / "plugin.json").read_text())["version"]


def installed_codex_root(root: Path) -> Path | None:
    cache = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "plugins" / "cache" / "v1tamins" / "v1tamins"
    candidate = cache / canonical_version(root)
    if (candidate / ".codex-plugin" / "plugin.json").is_file():
        return candidate
    versions = sorted(p for p in cache.glob("*") if (p / ".codex-plugin" / "plugin.json").is_file()) if cache.is_dir() else []
    return versions[-1] if versions else None


def verify_installed(root: Path, installed: Path, runtime: str) -> dict:
    done = subprocess.run(
        [str(root / "scripts" / "verify-installed-plugin.sh"), "--canonical", str(root / "plugins" / "v1tamins"),
         "--installed", str(installed), "--runtime", runtime],
        capture_output=True, text=True, timeout=120, env=child_env(), cwd=root,
    )
    try:
        return json.loads(done.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"verification_status": "error", "message": (done.stderr or done.stdout).strip()[:500]}


def cmd_new_run(args, root: Path) -> int:
    print(resolve_run_dir(root, args.run_dir))
    return 0


def cmd_doctor(args, root: Path) -> int:
    run_dir = resolve_run_dir(root, args.run_dir)
    report: dict = {"run_dir": str(run_dir), "canonical_version": canonical_version(root), "skills_on_disk": len(skills_on_disk(root))}
    problems: list[str] = []

    if args.runtime in ("claude", "both"):
        claude_bin = shutil.which("claude")
        claude = {"bin": claude_bin, "version": version_of(claude_bin), "auth_ok": False,
                  "plugin_dir": str(root / "plugins" / "v1tamins")}
        if claude_bin:
            try:
                auth = subprocess.run([claude_bin, "auth", "status", "--text"], capture_output=True, text=True, timeout=60, env=child_env())
                claude["auth_ok"] = auth.returncode == 0
                claude["auth_detail"] = (auth.stdout or auth.stderr).strip().splitlines()[0] if (auth.stdout or auth.stderr).strip() else ""
            except (OSError, subprocess.TimeoutExpired) as exc:
                claude["auth_error"] = type(exc).__name__
                problems.append(f"claude authentication probe failed: {type(exc).__name__}")
        report["claude"] = claude
        if not claude_bin:
            problems.append("claude binary not on PATH")
        elif not claude["auth_ok"] and "auth_error" not in claude:
            problems.append("claude is not logged in (run: claude auth login)")

    if args.runtime in ("codex", "both"):
        codex_bin = shutil.which("codex")
        codex = {"bin": codex_bin, "version": version_of(codex_bin), "login_ok": False}
        if codex_bin:
            try:
                login = subprocess.run([codex_bin, "login", "status"], capture_output=True, text=True, timeout=60, env=child_env())
                codex["login_ok"] = login.returncode == 0
                codex["login_detail"] = (login.stdout or login.stderr).strip().splitlines()[0] if (login.stdout or login.stderr).strip() else ""
            except (OSError, subprocess.TimeoutExpired) as exc:
                codex["login_error"] = type(exc).__name__
                problems.append(f"codex authentication probe failed: {type(exc).__name__}")
        codex["installed_root"] = None
        try:
            installed = installed_codex_root(root)
            codex["installed_root"] = str(installed) if installed else None
            codex["installed_verification"] = verify_installed(root, installed, "codex") if installed else {"verification_status": "missing"}
        except (OSError, subprocess.TimeoutExpired) as exc:
            codex["installed_verification"] = {"verification_status": "error", "error": type(exc).__name__}
        report["codex"] = codex
        if not codex_bin:
            problems.append("codex binary not on PATH")
        elif not codex["login_ok"] and "login_error" not in codex:
            problems.append("codex is not logged in (run: codex login)")
        if codex["installed_verification"].get("verification_status") != "match":
            problems.append("installed Codex plugin cache does not match the checkout; Codex would drive a stale build")

    report["problems"] = problems
    report["drivable"] = not problems
    write_json(run_dir / "doctor.json", report)
    emit(report)
    return 0 if not problems else 1


def claude_summary(stdout: str, root: Path, expect_skill: str | None) -> dict:
    summary: dict = {"plugin": None, "plugin_is_checkout": False, "skills_loaded": 0, "skills_missing": [], "skills_unexpected": [], "result_is_error": None, "tool_uses": [], "final_text": None, "structured_output": None, "result_subtype": None, "num_turns": None}
    disk = set(skills_on_disk(root))
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            for plugin in event.get("plugins", []):
                if plugin.get("name") == "v1tamins":
                    summary["plugin"] = plugin
                    summary["plugin_is_checkout"] = Path(plugin.get("path", "")).resolve() == (root / "plugins" / "v1tamins").resolve()
            loaded = {s.split(":", 1)[1] for s in event.get("skills", []) if s.startswith("v1tamins:")}
            summary["skills_loaded"] = len(loaded)
            summary["skills_missing"] = sorted(disk - loaded)
            summary["skills_unexpected"] = sorted(loaded - disk)
            summary["expected_skill_loaded"] = (expect_skill in loaded) if expect_skill else None
        elif event.get("type") == "assistant":
            for block in (event.get("message") or {}).get("content", []):
                if block.get("type") == "tool_use":
                    summary["tool_uses"].append({"name": block.get("name"), "input": block.get("input")})
        elif event.get("type") == "result":
            summary["result_subtype"] = event.get("subtype")
            summary["result_is_error"] = event.get("is_error")
            summary["num_turns"] = event.get("num_turns")
            summary["structured_output"] = event.get("structured_output")
            summary["final_text"] = event.get("result")
    return summary


def cmd_claude(args, root: Path) -> int:
    run_dir = resolve_run_dir(root, args.run_dir)
    binary = shutil.which("claude")
    if not binary:
        sys.exit("verify-v1tamins: claude binary not on PATH")
    cmd = [binary, "-p", "--output-format", "stream-json", "--verbose", "--no-session-persistence",
           "--plugin-dir", str(root / "plugins" / "v1tamins")]
    if not args.allow_writes:
        # --disallowedTools is variadic; a single-value flag must follow it so the prompt is not swallowed.
        cmd += ["--disallowedTools", WRITE_TOOLS]
    if args.schema:
        cmd += ["--json-schema", Path(args.schema).read_text()]
    cmd += ["--max-turns", str(args.max_turns), args.prompt]
    code, out, err, duration = run_capture(cmd, cwd=root, timeout=args.timeout, run_dir=run_dir, label=f"{args.label}.claude")
    (run_dir / f"{args.label}.claude.raw.jsonl").write_text(out, encoding="utf-8")
    (run_dir / f"{args.label}.claude.stderr.txt").write_text(err, encoding="utf-8")
    summary = {"runtime": "claude", "label": args.label, "run_dir": str(run_dir), "prompt": args.prompt,
               "command": [c if not c.startswith("{") else "<schema>" for c in cmd], "returncode": code, "duration_seconds": duration}
    summary.update(claude_summary(out, root, args.expect_skill))
    ok = (
        code == 0 and summary["plugin_is_checkout"]
        and not summary["skills_missing"] and not summary["skills_unexpected"]
        and summary.get("expected_skill_loaded") is not False
        and summary["result_subtype"] == "success" and summary["result_is_error"] is False
        and (bool((summary["final_text"] or "").strip()) or summary["structured_output"] is not None)
        and (not args.schema or summary["structured_output"] is not None)
    )
    summary["status"] = "pass" if ok else "fail"
    write_json(run_dir / f"{args.label}.claude.summary.json", summary)
    emit(summary)
    return 0 if ok else 1


def codex_summary(stdout: str, schema: bool) -> dict:
    summary: dict = {"thread_id": None, "items": [], "tool_calls": [], "final_text": None, "structured_output": None, "turn_completed": False}
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        kind = event.get("type")
        if kind == "thread.started":
            summary["thread_id"] = event.get("thread_id")
        elif kind == "turn.completed":
            summary["turn_completed"] = True
        elif kind == "item.completed":
            item = event.get("item") or {}
            summary["items"].append(item.get("type"))
            if item.get("type") in {"tool_call", "function_call", "command_execution"}:
                summary["tool_calls"].append({k: item.get(k) for k in ("name", "tool_name", "command") if k in item})
            elif item.get("type") == "agent_message":
                summary["final_text"] = item.get("text")
    if schema and summary["final_text"]:
        try:
            summary["structured_output"] = json.loads(summary["final_text"])
        except ValueError:
            summary["structured_output"] = None
    return summary


def cmd_codex(args, root: Path) -> int:
    run_dir = resolve_run_dir(root, args.run_dir)
    binary = shutil.which("codex")
    if not binary:
        sys.exit("verify-v1tamins: codex binary not on PATH")
    # Recheck parity for this drive; a prior Doctor report may be stale or
    # belong to another checkout. Never launch a stale build as verified.
    installed = installed_codex_root(root)
    parity = verify_installed(root, installed, "codex") if installed else {"verification_status": "missing"}
    if parity.get("verification_status") != "match":
        summary = {"runtime": "codex", "label": args.label, "status": "fail",
                   "installed_root": str(installed) if installed else None,
                   "installed_verification": parity, "reason": "installed Codex cache does not match checkout"}
        write_json(run_dir / f"{args.label}.codex.summary.json", summary)
        emit(summary)
        return 1
    cmd = [binary, "exec", "--cd", str(root), "--sandbox", "read-only", "--ephemeral", "--json"]
    if args.schema:
        cmd += ["--output-schema", str(Path(args.schema).resolve())]
    cmd.append(args.prompt)
    code, out, err, duration = run_capture(cmd, cwd=root, timeout=args.timeout, run_dir=run_dir, label=f"{args.label}.codex")
    (run_dir / f"{args.label}.codex.raw.jsonl").write_text(out, encoding="utf-8")
    (run_dir / f"{args.label}.codex.stderr.txt").write_text(err, encoding="utf-8")
    summary = {"runtime": "codex", "label": args.label, "run_dir": str(run_dir), "prompt": args.prompt, "command": cmd,
               "returncode": code, "duration_seconds": duration}
    summary["installed_root"] = str(installed)
    summary["installed_verification"] = parity
    summary.update(codex_summary(out, bool(args.schema)))
    ok = code == 0 and summary["turn_completed"] and bool(summary["final_text"])
    summary["status"] = "pass" if ok else "fail"
    write_json(run_dir / f"{args.label}.codex.summary.json", summary)
    emit(summary)
    return 0 if ok else 1


def cmd_route(args, root: Path) -> int:
    run_dir = resolve_run_dir(root, args.run_dir)
    cmd = [sys.executable, str(root / "scripts" / "run-skill-routing-live-eval.py"), "--repo-root", str(root),
           "--output-dir", str(run_dir / "routing"), *args.runner_args]
    print(f"run_dir={run_dir}", file=sys.stderr)
    proc = subprocess.Popen(cmd, cwd=root, env=child_env(), stdin=subprocess.DEVNULL,
                            start_new_session=os.name == "posix")
    record = record_pid(run_dir, proc.pid, "route")
    try:
        return proc.wait()
    finally:
        if proc.poll() is None:
            signal_child(proc, signal.SIGTERM)
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                signal_child(proc, signal.SIGKILL)
                proc.wait(timeout=1)
        record.unlink(missing_ok=True)


def identity_exited(pid: int, identity: dict) -> bool:
    current = process_identity(pid)
    if current is not None:
        # A zombie or a different birth identity cannot be the running child.
        return current != identity
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        pass
    # Darwin's proc_pidinfo can omit zombies before their parent reaps them.
    # Confirm that state separately; an unreadable identity alone proves nothing.
    if sys.platform == "darwin":
        try:
            status = subprocess.run(["/bin/ps", "-o", "stat=", "-p", str(pid)],
                                    capture_output=True, text=True, timeout=1)
            return status.returncode == 0 and status.stdout.strip().startswith("Z")
        except (OSError, subprocess.TimeoutExpired):
            pass
    return False


def wait_for_identity_exit(pid: int, identity: dict, timeout: float = 1) -> bool:
    deadline = time.monotonic() + timeout
    while not identity_exited(pid, identity):
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.02)
    return True


def signal_recorded_child(pid: int, identity: dict, sig: int) -> bool:
    # Recheck at each signal, including escalation: the PID may now belong to
    # another process. Never use an unverified stored process-group number.
    if process_identity(pid) != identity:
        return False
    if os.name == "posix" and os.getpgid(pid) == pid:
        os.killpg(pid, sig)
    else:
        os.kill(pid, sig)
    return True


def cmd_cleanup(args, root: Path) -> int:
    run_dir = resolve_run_dir(root, args.run_dir)
    report = {"run_dir": str(run_dir), "stopped": [], "unverified": [], "survivors": [], "removed": [], "evidence_kept": sorted(p.name for p in run_dir.iterdir())}
    pids_dir = run_dir / "pids"
    if pids_dir.is_dir():
        for entry_path in sorted(pids_dir.glob("*.json")):
            entry = json.loads(entry_path.read_text())
            pid, identity = entry.get("pid"), entry.get("identity")
            if type(pid) is not int or pid <= 1 or not identity or process_identity(pid) != identity:
                report["unverified"].append(entry)
                continue
            try:
                signal_recorded_child(pid, identity, signal.SIGTERM)
                if not wait_for_identity_exit(pid, identity):
                    signal_recorded_child(pid, identity, signal.SIGKILL)
                if wait_for_identity_exit(pid, identity):
                    report["stopped"].append(entry)
                    entry_path.unlink()
                else:
                    report["survivors"].append(entry)
            except ProcessLookupError:
                # A process can exit between its identity check and signalling.
                if identity_exited(pid, identity):
                    report["stopped"].append(entry)
                    entry_path.unlink()
                else:
                    report["survivors"].append(entry)
            except PermissionError:
                report["unverified"].append(entry)
        if not any(pids_dir.iterdir()):
            pids_dir.rmdir()
            report["removed"].append("pids/")
    scratch = run_dir / "scratch"
    if scratch.is_dir():
        shutil.rmtree(scratch)
        report["removed"].append("scratch/")
    report["evidence_kept"] = sorted(p.name for p in run_dir.iterdir())
    emit(report)
    return 1 if report["survivors"] or report["unverified"] else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run-dir", help="evidence directory; defaults to $V1_VERIFY_RUN_DIR or a new .v1tamins/verify/run-* directory")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("new-run")
    doctor = sub.add_parser("doctor")
    doctor.add_argument("--runtime", choices=["claude", "codex", "both"], default="both")
    for name in ("claude", "codex"):
        drive = sub.add_parser(name)
        drive.add_argument("prompt")
        drive.add_argument("--label", default=name + "-drive", help="evidence file prefix")
        drive.add_argument("--schema", help="JSON schema file the runtime must answer with")
        drive.add_argument("--timeout", type=int, default=300)
        if name == "claude":
            drive.add_argument("--max-turns", type=int, default=6)
            drive.add_argument("--allow-writes", action="store_true", help="do not disallow Bash/Edit/Write tools")
            drive.add_argument("--expect-skill", help="v1-* skill that must appear in the loaded skill list")
    route = sub.add_parser("route")
    route.add_argument("runner_args", nargs=argparse.REMAINDER, help="arguments passed to scripts/run-skill-routing-live-eval.py")
    sub.add_parser("cleanup")
    # Split at the route subcommand before parsing so leading flags such as
    # --runtime are forwarded unchanged, without weakening other subcommands.
    argv = sys.argv[1:]
    route_index = 0
    if argv[:1] == ["--run-dir"]:
        route_index = 2
    elif argv and argv[0].startswith("--run-dir="):
        route_index = 1
    if len(argv) > route_index and argv[route_index] == "route":
        args = parser.parse_args(argv[:route_index + 1])
        args.runner_args = argv[route_index + 1:]
        if args.runner_args[:1] == ["--"]:
            args.runner_args = args.runner_args[1:]
    else:
        args = parser.parse_args(argv)
    root = repo_root()
    handler = {"new-run": cmd_new_run, "doctor": cmd_doctor, "claude": cmd_claude, "codex": cmd_codex, "route": cmd_route, "cleanup": cmd_cleanup}[args.command]
    return handler(args, root)


if __name__ == "__main__":
    raise SystemExit(main())
