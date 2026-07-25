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


if __name__ == "__main__":
    unittest.main()
