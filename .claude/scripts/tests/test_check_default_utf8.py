#!/usr/bin/env python3

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "check_default_utf8.py"


class DefaultUtf8CheckTest(unittest.TestCase):
    def run_check(self, files: dict[str, bytes]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            defaults = Path(temp_dir) / "defaults"
            defaults.mkdir()
            for name, contents in files.items():
                (defaults / name).write_bytes(contents)
            return subprocess.run(
                [sys.executable, str(SCRIPT), "--defaults-dir", str(defaults)],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

    def test_accepts_ascii_and_bom_free_utf8(self) -> None:
        result = self.run_check(
            {"ascii.txt": b"show_more = false\n",
             "zh.txt": "menu += lightblue:符文\n".encode("utf-8")}
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("PASS", result.stdout)

    def test_rejects_utf8_bom(self) -> None:
        result = self.run_check({"bom.txt": b"\xef\xbb\xbfoption = value\n"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("BOM is not allowed", result.stdout)

    def test_rejects_invalid_utf8(self) -> None:
        result = self.run_check({"invalid.txt": b"option = \xff\n"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid UTF-8", result.stdout)


if __name__ == "__main__":
    unittest.main()
