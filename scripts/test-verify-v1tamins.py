#!/usr/bin/env python3
"""Offline regressions for the project-local runtime verification helper."""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / '.agents/skills/verify-v1tamins/scripts/verify-v1tamins.py'
spec = importlib.util.spec_from_file_location('verify_v1tamins', HELPER)
assert spec and spec.loader
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_completed_capture_retires_pid(self):
        code, out, _, _ = verify.run_capture(
            [sys.executable, '-c', 'print("done")'], cwd=ROOT,
            timeout=5, run_dir=self.run, label='done')
        self.assertEqual((code, out.strip()), (0, 'done'))
        self.assertEqual(list((self.run / 'pids').glob('*.json')), [])

    def test_cleanup_does_not_signal_reused_or_unverified_pid(self):
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
        try:
            verify.record_pid(self.run, child.pid, 'stale')
            record = self.run / 'pids' / f'{child.pid}.json'
            entry = json.loads(record.read_text())
            entry['identity'] = {'start': 'different-process', 'command': 'different-process'}
            record.write_text(json.dumps(entry))
            with contextlib.redirect_stdout(io.StringIO()):
                verify.cmd_cleanup(argparse.Namespace(run_dir=str(self.run)), ROOT)
            self.assertIsNone(child.poll())
        finally:
            child.terminate()
            child.wait(timeout=5)

    @unittest.skipUnless(sys.platform == 'darwin' or sys.platform.startswith('linux'), 'birth identity unsupported')
    def test_cleanup_recognizes_recorded_child(self):
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'],
                                 start_new_session=True)
        try:
            identity = verify.process_identity(child.pid)
            self.assertIsNotNone(identity)
            verify.record_pid(self.run, child.pid, 'active')
            with contextlib.redirect_stdout(io.StringIO()):
                verify.cmd_cleanup(argparse.Namespace(run_dir=str(self.run)), ROOT)
            self.assertEqual(child.wait(timeout=5), -signal.SIGTERM)
        finally:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)

    @unittest.skipUnless(sys.platform == 'darwin' or sys.platform.startswith('linux'), 'birth identity unsupported')
    def test_cleanup_waits_and_kills_term_ignoring_child(self):
        ready = self.run / 'cleanup-ready'
        child = subprocess.Popen([
            sys.executable, '-c',
            'import signal, time; from pathlib import Path; '
            'signal.signal(signal.SIGTERM, signal.SIG_IGN); '
            f'Path({str(ready)!r}).touch(); time.sleep(30)'], start_new_session=True)
        try:
            deadline = time.monotonic() + 5
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(ready.exists())
            verify.record_pid(self.run, child.pid, 'term-ignoring-cleanup')
            output = io.StringIO()
            started = time.monotonic()
            with contextlib.redirect_stdout(output):
                result = verify.cmd_cleanup(argparse.Namespace(run_dir=str(self.run)), ROOT)
            self.assertLess(time.monotonic() - started, 4)
            # Darwin can expose SZOMB just before waitpid can reap it.
            self.assertEqual(child.wait(timeout=0.5), -signal.SIGKILL)
            self.assertEqual(result, 0)
            self.assertEqual(len(json.loads(output.getvalue())['stopped']), 1)
            self.assertFalse((self.run / 'pids').exists())
        finally:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)

    @unittest.skipUnless(sys.platform == 'darwin' or sys.platform.startswith('linux'), 'birth identity unsupported')
    def test_cleanup_kills_same_group_descendant_after_leader_exits(self):
        ready = self.run / 'group-ready'
        pid_file = self.run / 'group-descendant.pid'
        descendant = self.run / 'cleanup-descendant.py'
        descendant.write_text(
            'import os, signal, time; from pathlib import Path\n'
            'signal.signal(signal.SIGTERM, signal.SIG_IGN)\n'
            f'Path({str(pid_file)!r}).write_text(str(os.getpid()))\n'
            f'Path({str(ready)!r}).touch()\n'
            'time.sleep(30)\n')
        child = subprocess.Popen([
            sys.executable, '-c',
            'import subprocess, sys, time; '
            f'subprocess.Popen([sys.executable, {str(descendant)!r}], '
            'stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); '
            'time.sleep(30)'], start_new_session=True)
        try:
            deadline = time.monotonic() + 5
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(ready.exists())
            descendant_pid = int(pid_file.read_text())
            descendant_identity = verify.process_identity(descendant_pid)
            self.assertEqual(os.getpgid(descendant_pid), child.pid)
            verify.record_pid(self.run, child.pid, 'group-cleanup')
            output = io.StringIO()
            started = time.monotonic()
            with contextlib.redirect_stdout(output):
                result = verify.cmd_cleanup(argparse.Namespace(run_dir=str(self.run)), ROOT)
            self.assertLess(time.monotonic() - started, 5)
            self.assertEqual(child.wait(timeout=0.5), -signal.SIGTERM)
            self.assertTrue(verify.identity_exited(descendant_pid, descendant_identity),
                            'TERM-ignoring descendant survived the recorded leader exit')
            self.assertEqual(result, 0)
            self.assertEqual(len(json.loads(output.getvalue())['stopped']), 1)
            self.assertFalse((self.run / 'pids').exists())
        finally:
            # Only this fixture owns the process group, and the leader PID
            # cannot be reused until this parent has reaped it.
            if pid_file.exists():
                try:
                    os.kill(int(pid_file.read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)

    def test_cleanup_keeps_survivor_record(self):
        identity = {'start': 'fixture-birth'}
        with mock.patch.object(verify, 'process_identity', return_value=identity):
            record = verify.record_pid(self.run, 123456, 'survivor')
            output = io.StringIO()
            with mock.patch.object(verify, 'group_member_pids', return_value=[123456]), \
                    mock.patch.object(verify.os, 'getpgid', return_value=123456), \
                    mock.patch.object(verify.os, 'killpg') as group_send, \
                    mock.patch.object(verify.os, 'kill') as send, \
                    contextlib.redirect_stdout(output):
                result = verify.cmd_cleanup(argparse.Namespace(run_dir=str(self.run)), ROOT)
        self.assertEqual(result, 1)
        self.assertTrue(record.exists(), 'surviving child must remain available for later cleanup')
        report = json.loads(output.getvalue())
        self.assertEqual(report['stopped'], [])
        self.assertEqual(len(report['survivors']), 1)
        self.assertEqual(send.call_args_list, [mock.call(123456, signal.SIGTERM), mock.call(123456, signal.SIGKILL)])
        group_send.assert_not_called()

    def test_cleanup_rechecks_identity_before_escalation(self):
        original = {'start': 'original'}
        replacement = {'start': 'replacement'}
        current = {123456: original, 123457: original}
        def send_signal(pid, sig):
            if sig == signal.SIGTERM:
                current[pid] = replacement
        with mock.patch.object(verify, 'process_identity', side_effect=lambda pid: current[pid]):
            record = verify.record_pid(self.run, 123456, 'reused-during-cleanup')
            with mock.patch.object(verify, 'group_member_pids', return_value=[123456, 123457]), \
                    mock.patch.object(verify.os, 'getpgid', return_value=123456), \
                    mock.patch.object(verify.os, 'kill', side_effect=send_signal) as send, \
                    mock.patch.object(verify.os, 'killpg') as group_send, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(verify.cmd_cleanup(argparse.Namespace(run_dir=str(self.run)), ROOT), 1)
        self.assertEqual(send.call_args_list, [mock.call(123456, signal.SIGTERM), mock.call(123457, signal.SIGTERM)])
        group_send.assert_not_called()
        self.assertTrue(record.exists(), 'reused group cannot certify completion')

    def test_cleanup_keeps_record_when_birth_identity_becomes_unavailable(self):
        original = {'start': 'original'}
        state = [original]
        def send_signal(pid, sig):
            if sig == signal.SIGTERM:
                state[0] = None
        with mock.patch.object(verify, 'process_identity', side_effect=lambda pid: state[0]):
            record = verify.record_pid(self.run, 123456, 'unverifiable-after-term')
            with mock.patch.object(verify, 'group_member_pids', return_value=[123456]), \
                    mock.patch.object(verify.os, 'getpgid', return_value=123456), \
                    mock.patch.object(verify.os, 'kill', side_effect=send_signal) as send, \
                    mock.patch.object(verify.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'R', '')), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(verify.cmd_cleanup(argparse.Namespace(run_dir=str(self.run)), ROOT), 1)
        signals = [call for call in send.call_args_list if call.args[1] != 0]
        self.assertEqual(signals, [mock.call(123456, signal.SIGTERM)])
        self.assertTrue(record.exists())
        self.assertEqual(json.loads(record.read_text())['cleanup_group']['members'],
                         [{'pid': 123456, 'identity': original}])

    def test_cleanup_rejects_snapshot_without_verified_leader(self):
        identity = {'start': 'fixture-birth'}
        with mock.patch.object(verify, 'process_identity', return_value=identity):
            record = verify.record_pid(self.run, 123456, 'incomplete-snapshot')
            with mock.patch.object(verify, 'group_member_pids', return_value=[]), \
                    mock.patch.object(verify.os, 'getpgid', return_value=123456), \
                    mock.patch.object(verify.os, 'kill') as send, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(verify.cmd_cleanup(argparse.Namespace(run_dir=str(self.run)), ROOT), 1)
        self.assertTrue(record.exists())
        send.assert_not_called()

    def test_cleanup_keeps_record_when_group_enumeration_fails(self):
        identity = {'start': 'fixture-birth'}
        with mock.patch.object(verify, 'process_identity', return_value=identity):
            record = verify.record_pid(self.run, 123456, 'unreadable-group')
            for error in (OSError('denied'), subprocess.TimeoutExpired('/bin/ps', 1)):
                with self.subTest(error=type(error).__name__), \
                        mock.patch.object(verify, 'group_member_pids', side_effect=error), \
                        mock.patch.object(verify.os, 'getpgid', return_value=123456), \
                        mock.patch.object(verify.os, 'kill') as send, \
                        contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(verify.cmd_cleanup(argparse.Namespace(run_dir=str(self.run)), ROOT), 1)
                self.assertTrue(record.exists())
                send.assert_not_called()

    def test_cleanup_does_not_signal_unknown_late_group_member(self):
        identity = {'start': 'fixture-birth'}
        alive = {123456: identity, 123457: {'start': 'new-member', 'exited': True}}
        def send_signal(pid, sig):
            if sig == signal.SIGTERM:
                alive[pid] = {**identity, 'exited': True}
        with mock.patch.object(verify, 'process_identity', side_effect=lambda pid: alive[pid]):
            record = verify.record_pid(self.run, 123456, 'late-member')
            with mock.patch.object(verify, 'group_member_pids', side_effect=[[123456], [123456, 123457]]), \
                    mock.patch.object(verify.os, 'getpgid', return_value=123456), \
                    mock.patch.object(verify.os, 'kill', side_effect=send_signal) as send, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(verify.cmd_cleanup(argparse.Namespace(run_dir=str(self.run)), ROOT), 1)
        send.assert_called_once_with(123456, signal.SIGTERM)
        self.assertTrue(record.exists())

    def test_cleanup_probe_wait_shares_one_deadline(self):
        clock = [0.0]
        def probe(cmd, **kwargs):
            clock[0] += kwargs['timeout']
            raise subprocess.TimeoutExpired(cmd, kwargs['timeout'])
        with mock.patch.object(verify.sys, 'platform', 'darwin'), \
                mock.patch.object(verify, 'process_identity', return_value=None), \
                mock.patch.object(verify.os, 'kill'), \
                mock.patch.object(verify.time, 'monotonic', side_effect=lambda: clock[0]), \
                mock.patch.object(verify.subprocess, 'run', side_effect=probe) as run:
            self.assertFalse(verify.wait_for_members_exit(
                [{'pid': 123456, 'identity': {'start': 'first'}},
                 {'pid': 123457, 'identity': {'start': 'second'}}], deadline=0.1))
        self.assertEqual(run.call_count, 1)
        self.assertEqual(clock[0], 0.1)

    def test_cleanup_uses_saved_members_after_leader_exit(self):
        original = {'start': 'original'}
        dead = {**original, 'exited': True}
        current = {123456: dead, 123457: original}
        record_dir = self.run / 'pids'
        record_dir.mkdir()
        record = record_dir / '123456.json'
        verify.write_json(record, {'pid': 123456, 'identity': original, 'cleanup_group': {
            'pgid': 123456, 'whole_group': True,
            'members': [{'pid': 123456, 'identity': original}, {'pid': 123457, 'identity': original}]}})
        def send_signal(pid, sig):
            current[pid] = dead
        with mock.patch.object(verify, 'process_identity', side_effect=lambda pid: current[pid]), \
                mock.patch.object(verify, 'group_member_pids', return_value=[123456, 123457]), \
                mock.patch.object(verify.os, 'getpgid', return_value=123456), \
                mock.patch.object(verify.os, 'kill', side_effect=send_signal) as send, \
                mock.patch.object(verify.os, 'killpg') as group_send, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verify.cmd_cleanup(argparse.Namespace(run_dir=str(self.run)), ROOT), 0)
        send.assert_called_once_with(123457, signal.SIGTERM)
        group_send.assert_not_called()
        self.assertFalse(record.exists())

    def test_doctor_does_not_probe_unselected_runtime(self):
        for runtime in ('claude', 'codex'):
            with self.subTest(runtime=runtime):
                def probe(cmd, **kwargs):
                    if not cmd[0].endswith(runtime):
                        raise subprocess.TimeoutExpired(cmd, 60)
                    return subprocess.CompletedProcess(cmd, 0, 'logged in', '')
                with mock.patch.object(verify.shutil, 'which', side_effect=lambda name: 'fixture-' + name), \
                        mock.patch.object(verify, 'version_of', return_value='fixture-version'), \
                        mock.patch.object(verify.subprocess, 'run', side_effect=probe) as run, \
                        mock.patch.object(verify, 'installed_codex_root', return_value=Path('fixture-cache')) as installed, \
                        mock.patch.object(verify, 'verify_installed', return_value={'verification_status': 'match'}) as parity, \
                        contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(verify.cmd_doctor(argparse.Namespace(run_dir=str(self.run), runtime=runtime), ROOT), 0)
                self.assertEqual([call.args[0][0] for call in run.call_args_list], ['fixture-' + runtime])
                if runtime == 'claude':
                    installed.assert_not_called()
                    parity.assert_not_called()
                report = json.loads((self.run / 'doctor.json').read_text())
                self.assertTrue(report['drivable'])

    def test_doctor_records_selected_probe_exceptions(self):
        for runtime, probe_kind in (('claude', 'auth'), ('codex', 'auth'), ('codex', 'cache')):
            for error in (subprocess.TimeoutExpired('fixture', 60), OSError('fixture unavailable')):
                with self.subTest(runtime=runtime, probe=probe_kind, error=type(error).__name__):
                    (self.run / 'doctor.json').unlink(missing_ok=True)
                    with mock.patch.object(verify.shutil, 'which', side_effect=lambda name: 'fixture-' + name), \
                            mock.patch.object(verify, 'version_of', return_value='fixture-version'), \
                            mock.patch.object(verify.subprocess, 'run', side_effect=error if probe_kind == 'auth' else None,
                                              return_value=subprocess.CompletedProcess([], 0, 'logged in', '')), \
                            mock.patch.object(verify, 'installed_codex_root', return_value=Path('fixture-cache')), \
                            mock.patch.object(verify, 'verify_installed', side_effect=error if probe_kind == 'cache' else None,
                                              return_value={'verification_status': 'match'}), \
                            contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(verify.cmd_doctor(argparse.Namespace(run_dir=str(self.run), runtime=runtime), ROOT), 1)
                    report = json.loads((self.run / 'doctor.json').read_text())
                    self.assertFalse(report['drivable'])
                    self.assertTrue(report['problems'])
                    self.assertIn(type(error).__name__, json.dumps(report))

    def test_route_passthrough(self):
        forwarded = ['--runtime', 'claude', '--case-id', 'fixture', '--max-cases', '1']
        for prefix in ([], ['--run-dir', str(self.run)], ['--run-dir=' + str(self.run)]):
            for separator in ([], ['--']):
                with self.subTest(prefix=prefix, separator=separator), \
                        mock.patch.object(sys, 'argv', ['verify', *prefix, 'route', *separator, *forwarded]), \
                        mock.patch.object(verify, 'cmd_route', return_value=0) as route:
                    self.assertEqual(verify.main(), 0)
                self.assertEqual(route.call_args.args[0].runner_args, forwarded)

    def test_route_rejects_unknown_helper_options_outside_route(self):
        with mock.patch.object(sys, 'argv', ['verify', 'cleanup', '--runtime', 'claude']), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            verify.main()

    @unittest.skipUnless(os.name == 'posix', 'process-group fixture requires POSIX')
    def test_timeout_with_descendant_pipe_is_bounded(self):
        self.check_timeout_fixture(escape_group=False)

    @unittest.skipUnless(os.name == 'posix', 'process-group fixture requires POSIX')
    def test_timeout_with_escaped_descendant_pipe_is_bounded(self):
        self.check_timeout_fixture(escape_group=True)

    @unittest.skipUnless(os.name == 'posix', 'process-group fixture requires POSIX')
    def test_timeout_kills_term_ignoring_descendant_without_pipes(self):
        # The descendant closes both captured pipes and ignores TERM. EOF from
        # its parent must not make cleanup forget the still-running group.
        pid_file = self.run / 'detached-stdio.pid'
        ready = self.run / 'ready'
        survived = self.run / 'survived'
        descendant = self.run / 'term-ignore.py'
        descendant.write_text(
            'import os, signal, time; from pathlib import Path\n'
            'signal.signal(signal.SIGTERM, signal.SIG_IGN)\n'
            f'Path({str(pid_file)!r}).write_text(str(os.getpid()))\n'
            f'Path({str(ready)!r}).write_text("ready")\n'
            'time.sleep(2)\n'
            f'Path({str(survived)!r}).write_text("still running")\n'
            'time.sleep(30)\n')
        parent = self.run / 'parent.py'
        parent.write_text(
            'import subprocess, sys, time; from pathlib import Path\n'
            f'subprocess.Popen([sys.executable, {str(descendant)!r}], '
            'stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n'
            f'while not Path({str(ready)!r}).exists(): time.sleep(0.01)\n'
            'print("ready", flush=True)\n'
            'time.sleep(30)\n')
        try:
            code, out, _, duration = verify.run_capture(
                [sys.executable, str(parent)], cwd=ROOT, timeout=1,
                run_dir=self.run, label='term-ignore')
            self.assertEqual(code, 124)
            self.assertEqual(out.strip(), 'ready')
            self.assertLess(duration, 5)
            time.sleep(1.5)
            self.assertFalse(survived.exists(), 'TERM-ignoring descendant survived captured-parent EOF')
            self.assertEqual(list((self.run / 'pids').glob('*.json')), [])
        finally:
            if pid_file.exists():
                try:
                    os.kill(int(pid_file.read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def check_timeout_fixture(self, *, escape_group):
        # The outer process is also bounded so the unfixed helper cannot hang this suite.
        fixture = self.run / 'descendant.py'
        pid_file = self.run / 'descendant.pid'
        fixture.write_text(
            'import subprocess, sys, time\n'
            f'p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session={escape_group!r})\n'
            f'open({str(pid_file)!r}, "w").write(str(p.pid))\n'
            'time.sleep(30)\n')
        caller = (
            'import importlib.util; from pathlib import Path; '
            f's=importlib.util.spec_from_file_location("v", {str(HELPER)!r}); '
            'v=importlib.util.module_from_spec(s); s.loader.exec_module(v); '
            f'r=v.run_capture([{sys.executable!r}, {str(fixture)!r}], '
            f'cwd=Path({str(ROOT)!r}),timeout=1,run_dir=Path({str(self.run)!r}),label="timeout"); '
            'assert r[0] == 124; assert "verify-v1tamins: timeout" in r[2]; print("bounded")')
        outer = subprocess.Popen([sys.executable, '-c', caller], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            try:
                out, err = outer.communicate(timeout=6)
            except subprocess.TimeoutExpired:
                self.fail('capture hangs after killing the direct child while a descendant holds pipes')
            self.assertEqual(outer.returncode, 0, err)
            self.assertEqual(out.strip(), 'bounded')
        finally:
            try:
                os.killpg(outer.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            outer.communicate(timeout=5)
            if pid_file.exists():
                try:
                    os.kill(int(pid_file.read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def claude_drive(self, terminal=None, *, extra_skill=False, assistant_text=None):
        init = {'type': 'system', 'subtype': 'init',
                'plugins': [{'name': 'v1tamins', 'path': str(ROOT / 'plugins/v1tamins')}],
                'skills': ['v1tamins:' + name for name in verify.skills_on_disk(ROOT)]}
        if extra_skill:
            init['skills'].append('v1tamins:v1-stale')
        events = [init]
        if assistant_text:
            events.append({'type': 'assistant', 'message': {'content': [
                {'type': 'text', 'text': assistant_text}]}})
        if terminal is not None:
            events.append({'type': 'result', **terminal})
        args = argparse.Namespace(run_dir=str(self.run), allow_writes=False, schema=None,
                                  max_turns=1, prompt='fixture', timeout=5,
                                  label='fixture', expect_skill=None)
        with mock.patch.object(verify.shutil, 'which', return_value='fixture-claude'), \
                mock.patch.object(verify, 'run_capture', return_value=(
                    0, '\n'.join(json.dumps(event) for event in events), '', 0.1)), \
                contextlib.redirect_stdout(io.StringIO()):
            return verify.cmd_claude(args, ROOT)

    def test_claude_requires_terminal_success(self):
        self.assertEqual(self.claude_drive(assistant_text='intermediate'), 1)
        self.assertEqual(self.claude_drive({'subtype': 'error_max_turns', 'is_error': True},
                                         assistant_text='intermediate'), 1)

    def test_claude_requires_final_answer(self):
        self.assertEqual(self.claude_drive({'subtype': 'success', 'is_error': False}), 1)
        self.assertEqual(self.claude_drive({'subtype': 'success', 'is_error': False},
                                         assistant_text='intermediate'), 1)

    def test_claude_rejects_unexpected_skills(self):
        self.assertEqual(self.claude_drive({'subtype': 'success', 'is_error': False,
                                           'result': 'done'}, extra_skill=True), 1)

    def test_claude_accepts_successful_terminal_answer(self):
        self.assertEqual(self.claude_drive({'subtype': 'success', 'is_error': False,
                                           'result': 'done'}), 0)
        self.assertEqual(self.claude_drive({'subtype': 'success', 'is_error': False,
                                           'structured_output': {'answer': 'done'}}), 0)

    def test_claude_accepts_empty_structured_terminal_answer(self):
        for output in ({}, []):
            with self.subTest(output=output):
                self.assertEqual(self.claude_drive({'subtype': 'success', 'is_error': False,
                                                   'structured_output': output}), 0)

    def test_codex_checks_current_cache_before_launch(self):
        args = argparse.Namespace(run_dir=str(self.run), schema=None, prompt='fixture',
                                  timeout=5, label='fixture')
        with mock.patch.object(verify.shutil, 'which', return_value='fixture-codex'), \
                mock.patch.object(verify, 'installed_codex_root', return_value=Path('fixture-cache')), \
                mock.patch.object(verify, 'verify_installed', return_value={
                    'verification_status': 'mismatch'}), \
                mock.patch.object(verify, 'run_capture', return_value=(
                    0, '{"type":"turn.completed"}\n', '', 0.1)) as launch, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verify.cmd_codex(args, ROOT), 1)
        launch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
