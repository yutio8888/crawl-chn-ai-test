#!/usr/bin/env python3
"""Regression tests for the parallel tooling-test dispatcher."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


RUNNER = Path(__file__).with_name("run_all.sh")


class RunAllTests(unittest.TestCase):
    def test_parallel_workers_replay_in_order_and_continue_failures(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runner = root / "run_all.sh"
            shutil.copyfile(RUNNER, runner)
            sync = root / "sync"
            sync.mkdir()

            for name, peer, marker in (("01_first", "second", "first"),
                                       ("02_second", "first", "second")):
                (root / f"test_{name}.sh").write_text(textwrap.dedent(f"""\
                    #!/bin/bash
                    set -euo pipefail
                    touch "$RUN_ALL_TEST_SYNC/{marker}"
                    for _attempt in $(seq 1 100); do
                        [[ -f "$RUN_ALL_TEST_SYNC/{peer}" ]] && break
                        sleep 0.01
                    done
                    [[ -f "$RUN_ALL_TEST_SYNC/{peer}" ]]
                    echo "output-{marker}"
                """), encoding="utf-8")
            (root / "test_03_failure.sh").write_text(
                "#!/bin/bash\necho output-failure\nexit 7\n", encoding="utf-8")
            (root / "test_04_after.py").write_text(
                "print('output-after')\n", encoding="utf-8")
            (root / "test_post_coder_cleanup.sh").write_text(
                "#!/bin/bash\necho output-foreground\n", encoding="utf-8")

            env = os.environ.copy()
            env.update({"ZH_TOOLING_TEST_JOBS": "2",
                        "RUN_ALL_TEST_SYNC": str(sync)})
            proc = subprocess.run(
                ["/bin/bash", str(runner)], cwd=root, env=env, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

        self.assertEqual(1, proc.returncode, proc.stderr)
        headings = [proc.stdout.index(f">>> test_{name}") for name in (
            "01_first.sh", "02_second.sh", "03_failure.sh", "04_after.py")]
        self.assertEqual(sorted(headings), headings)
        for marker in ("output-first", "output-second", "output-failure",
                       "output-after", "output-foreground"):
            self.assertIn(marker, proc.stdout)
        self.assertIn("=== Results: 4 passed, 1 failed ===", proc.stdout)

    def test_invalid_job_count_fails_before_discovery(self):
        env = os.environ.copy()
        env["ZH_TOOLING_TEST_JOBS"] = "zero"
        proc = subprocess.run(
            ["/bin/bash", str(RUNNER)], env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(2, proc.returncode)
        self.assertIn("positive integer", proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
