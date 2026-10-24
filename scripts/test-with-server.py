#!/usr/bin/env python3
"""Offline checks of server startup, command status, and descendant cleanup."""

import os
from pathlib import Path
import shlex
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "plugins/v1tamins/skills/v1-e2e-testing/scripts/with_server.py"


@unittest.skipUnless(os.name == "posix", "server process groups require POSIX")
class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.server_script = self.directory / "server.py"
        self.server_script.write_text(
            "import os, pathlib, socket, sys, time\n"
            "pathlib.Path(sys.argv[2]).write_text(str(os.getpid()))\n"
            "listener = socket.socket()\n"
            "listener.bind(('127.0.0.1', int(sys.argv[1])))\n"
            "listener.listen()\n"
            "while True: time.sleep(1)\n"
        )
        self.command_marker = self.directory / "command-ran"

    def tearDown(self):
        # A failed cleanup assertion must not leave the deliberately nested fixture alive.
        for pidfile in self.directory.glob("*.pid"):
            try:
                os.kill(int(pidfile.read_text()), signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.temporary.cleanup()

    def free_port(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            return listener.getsockname()[1]

    def server_command(self, port, name="server"):
        argv = [sys.executable, str(self.server_script), str(port), str(self.directory / f"{name}.pid")]
        # Force an actual shell parent, like an npm wrapper, instead of shell exec optimization.
        return f"{shlex.join(argv)} & wait"

    def command(self, status=0):
        return [sys.executable, "-c", f"from pathlib import Path; Path({str(self.command_marker)!r}).touch(); raise SystemExit({status})"]

    def run_helper(self, servers, command=None, timeout=2):
        argv = [sys.executable, str(HELPER), "--timeout", str(timeout)]
        for server, port in servers:
            argv.extend(["--server", server, "--port", str(port)])
        argv.extend(["--", *(command or self.command())])
        return subprocess.run(argv, capture_output=True, text=True, timeout=15, stdin=subprocess.DEVNULL)

    def assert_port_closed(self, port):
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            with socket.socket() as connection:
                if connection.connect_ex(("127.0.0.1", port)) != 0:
                    return
            time.sleep(0.05)
        self.fail(f"server descendant still accepts connections on {port}")

    def test_command_status_is_preserved_and_shell_descendants_are_stopped(self):
        port = self.free_port()
        result = self.run_helper([(self.server_command(port), port)], self.command(23))
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertTrue(self.command_marker.exists())
        self.assert_port_closed(port)

    def test_existing_listener_is_rejected_before_launch_or_test_command(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            result = self.run_helper([(self.server_command(port), port)])
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(self.command_marker.exists())
            self.assertFalse((self.directory / "server.pid").exists())
            # The helper must leave the pre-existing listener alone.
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                pass

    def test_failed_start_exits_promptly_without_running_test_command(self):
        port = self.free_port()
        started = time.monotonic()
        result = self.run_helper([("exit 7", port)], timeout=4)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.command_marker.exists())
        self.assertLess(time.monotonic() - started, 2)
        self.assertIn("7", result.stderr)

    def test_later_failed_start_cleans_up_an_already_started_server(self):
        first, second = self.free_port(), self.free_port()
        result = self.run_helper([(self.server_command(first), first), ("exit 9", second)])
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.command_marker.exists())
        self.assert_port_closed(first)


if __name__ == "__main__":
    unittest.main()
