#!/usr/bin/env python3
"""
Start one or more servers, wait for them to be ready, run a command, then clean up.

Requires POSIX process groups (macOS/Linux). Each server command must stay in
the foreground; readiness means a local TCP connection succeeds, not that the
application's HTTP/API behavior is correct. Existing listeners are rejected.

Usage:
    # Single server
    python scripts/with_server.py --server "npm run dev" --port 5173 -- python automation.py
    python scripts/with_server.py --server "npm start" --port 3000 -- python test.py

    # Multiple servers
    python scripts/with_server.py \
      --server "cd backend && python server.py" --port 3000 \
      --server "cd frontend && npm run dev" --port 5173 \
      -- python test.py
"""

import subprocess
import socket
import time
import sys
import argparse
import os
import signal


def port_is_open(port):
    """Check only TCP availability; callers must verify application readiness."""
    try:
        with socket.create_connection(("localhost", port), timeout=0.2):
            return True
    except OSError:
        return False


def wait_for_server(process, port, timeout, check_interrupted):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        check_interrupted()
        status = process.poll()
        if status is not None:
            raise RuntimeError(f"Server command exited with status {status} before port {port} was ready")
        if port_is_open(port) and process.poll() is None:
            return
        time.sleep(0.1)
    raise RuntimeError(f"Server failed to start on port {port} within {timeout}s")


def stop_process_group(process):
    """Stop the command's entire group, including children of a shell wrapper."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    finally:
        # The shell may have exited while a descendant is still running.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def main():
    parser = argparse.ArgumentParser(description="Run command with one or more servers")
    parser.add_argument(
        "--server",
        action="append",
        dest="servers",
        required=True,
        help="Server command (can be repeated)",
    )
    parser.add_argument(
        "--port",
        action="append",
        dest="ports",
        type=int,
        required=True,
        help="Port for each server (must match --server count)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds per server (default: 30)",
    )
    parser.add_argument(
        "command", nargs=argparse.REMAINDER, help="Command to run after server(s) ready"
    )

    args = parser.parse_args()

    if os.name != "posix":
        parser.error("Server descendant cleanup requires POSIX process groups (macOS/Linux)")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if any(port < 1 or port > 65535 for port in args.ports):
        parser.error("--port must be between 1 and 65535")

    # Remove the '--' separator if present
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]

    if not args.command:
        print("Error: No command specified to run")
        sys.exit(1)

    # Parse server configurations
    if len(args.servers) != len(args.ports):
        print("Error: Number of --server and --port arguments must match")
        sys.exit(1)

    servers = []
    for cmd, port in zip(args.servers, args.ports):
        servers.append({"cmd": cmd, "port": port})

    server_processes = []
    command_process = None
    interrupted_signal = None

    def handle_signal(signum, frame):
        nonlocal interrupted_signal
        # Defer interruption until a launched process is recorded for cleanup.
        if interrupted_signal is None:
            interrupted_signal = signum

    def check_interrupted():
        if interrupted_signal is not None:
            raise KeyboardInterrupt

    previous_handlers = {}
    for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        previous_handlers[signum] = signal.signal(signum, handle_signal)

    exit_status = 1

    try:
        # Start all servers
        for i, server in enumerate(servers):
            check_interrupted()
            if port_is_open(server["port"]):
                raise RuntimeError(f"Port {server['port']} already has a listener; server was not launched")
            print(f"Starting server {i+1}/{len(servers)}: {server['cmd']}")

            # Use shell=True to support commands with cd and &&.
            # Discard stdout/stderr so a chatty server can't fill its pipe
            # buffer and block. Switch to inherited streams or a log file if
            # output is needed for debugging.
            process = subprocess.Popen(
                server["cmd"],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            server_processes.append(process)

            # Wait for this server to be ready
            print(f"Waiting for server on port {server['port']}...")
            wait_for_server(process, server["port"], args.timeout, check_interrupted)

            print(f"Server ready on port {server['port']}")

        print(f"\nAll {len(servers)} server(s) ready")

        # Run the command
        check_interrupted()
        print(f"Running: {' '.join(args.command)}\n")
        command_process = subprocess.Popen(args.command, start_new_session=True)
        while True:
            check_interrupted()
            try:
                exit_status = command_process.wait(timeout=0.1)
                break
            except subprocess.TimeoutExpired:
                pass

    except (OSError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
    except KeyboardInterrupt:
        exit_status = 130

    finally:
        try:
            if command_process is not None:
                stop_process_group(command_process)
            print(f"\nStopping {len(server_processes)} server(s)...")
            for i, process in reversed(list(enumerate(server_processes))):
                stop_process_group(process)
                print(f"Server {i+1} stopped")
        finally:
            for signum, handler in previous_handlers.items():
                signal.signal(signum, handler)

    return 128 + interrupted_signal if interrupted_signal is not None else exit_status


if __name__ == "__main__":
    sys.exit(main())
