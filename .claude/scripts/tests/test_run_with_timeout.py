#!/usr/bin/env python3

import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest


RUNNER = Path(__file__).resolve().parents[1] / "run_with_timeout.py"


class PortableTimeoutTests(unittest.TestCase):
    def run_command(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(RUNNER), *args],
            text=True,
            capture_output=True,
            timeout=10,
        )

    def test_preserves_success_and_failure_status(self) -> None:
        success = self.run_command(
            "--timeout", "2", "--", sys.executable, "-c", "print('ok')"
        )
        self.assertEqual(0, success.returncode, success.stderr)
        self.assertEqual("ok\n", success.stdout)

        failure = self.run_command(
            "--timeout", "2", "--", sys.executable, "-c", "raise SystemExit(7)"
        )
        self.assertEqual(7, failure.returncode)

    def test_timeout_returns_124_promptly(self) -> None:
        started = time.monotonic()
        result = self.run_command(
            "--timeout", "0.2", "--", sys.executable, "-c", "import time; time.sleep(5)"
        )
        self.assertEqual(124, result.returncode)
        self.assertLess(time.monotonic() - started, 3)

    def test_pty_captures_combined_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            transcript = Path(directory) / "session.typescript"
            result = self.run_command(
                "--timeout",
                "2",
                "--pty-transcript",
                str(transcript),
                "--",
                sys.executable,
                "-c",
                "import sys; print('标准输出'); print('标准错误', file=sys.stderr)",
            )
            self.assertEqual(0, result.returncode, result.stderr)
            captured = transcript.read_text(encoding="utf-8")
            self.assertIn("标准输出", captured)
            self.assertIn("标准错误", captured)

    def test_timeout_terminates_child_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "child-finished"
            code = (
                "import subprocess,sys,time;"
                "subprocess.Popen([sys.executable,'-c',"
                f"\"import time,pathlib;time.sleep(1);pathlib.Path({str(marker)!r}).write_text('bad')\""
                "]);time.sleep(5)"
            )
            result = self.run_command(
                "--timeout", "0.2", "--", sys.executable, "-c", code
            )
            self.assertEqual(124, result.returncode)
            time.sleep(1.2)
            self.assertFalse(marker.exists())

    def test_signal_is_forwarded_and_returns_promptly(self) -> None:
        process = subprocess.Popen(
            [
                sys.executable,
                str(RUNNER),
                "--timeout",
                "5",
                "--",
                sys.executable,
                "-c",
                "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(5)",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(0.2)
        started = time.monotonic()
        process.send_signal(signal.SIGTERM)
        process.communicate(timeout=3)
        self.assertEqual(128 + signal.SIGTERM, process.returncode)
        self.assertLess(time.monotonic() - started, 2)

    def test_pty_forwarded_hup_is_not_overwritten_by_term(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ready = root / "ready"
            received = root / "received"
            transcript = root / "session.typescript"
            code = f"""
import pathlib
import signal
import time

ready = pathlib.Path({str(ready)!r})
received = pathlib.Path({str(received)!r})

def handle_hup(*_args):
    received.write_text("HUP")
    time.sleep(0.3)
    raise SystemExit(0)

def handle_term(*_args):
    received.write_text("TERM")
    raise SystemExit(0)

signal.signal(signal.SIGHUP, handle_hup)
signal.signal(signal.SIGTERM, handle_term)
ready.write_text("ready")
time.sleep(5)
"""
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(RUNNER),
                    "--timeout",
                    "5",
                    "--pty-transcript",
                    str(transcript),
                    "--",
                    sys.executable,
                    "-c",
                    code,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            for _ in range(250):
                if ready.exists():
                    break
                time.sleep(0.02)
            self.assertTrue(ready.exists(), "child did not become ready")
            process.send_signal(signal.SIGHUP)
            _stdout, stderr = process.communicate(timeout=5)
            self.assertEqual(128 + signal.SIGHUP, process.returncode, stderr)
            self.assertEqual("HUP", received.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
