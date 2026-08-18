#!/usr/bin/env python3
"""PYTHONSAFEPATH must not break sibling imports of CI entry points.

GitHub Actions sets PYTHONSAFEPATH=1 on the unbound ZH tooling and CI-gate
jobs so Python will not prepend cwd or the executed file's directory.  The
scanners still import sibling modules such as i18n_shared.  verify_zh.sh and
run_all.sh therefore export PYTHONPATH to the executed .claude/scripts
directory.  This file pins both the fail-closed naked invocation and the
entry-point repair.
"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / ".claude" / "scripts"
MOVE_AUDIT = SCRIPTS / "audit_move_i18n.py"
VERIFY_ZH = SCRIPTS / "verify_zh.sh"
RUN_ALL = SCRIPTS / "tests" / "run_all.sh"


def _safepath_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONSAFEPATH"] = "1"
    env.pop("PYTHONPATH", None)
    return env


class PythonSafePathImportTests(unittest.TestCase):
    def test_naked_script_fails_closed_without_pythonpath(self) -> None:
        result = subprocess.run(
            [sys.executable, str(MOVE_AUDIT), str(ROOT / "crawl-ref" / "source")],
            cwd=ROOT,
            env=_safepath_env(),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("i18n_shared", result.stderr)

    def test_scripts_dir_on_pythonpath_repairs_sibling_import(self) -> None:
        env = _safepath_env()
        env["PYTHONPATH"] = str(SCRIPTS)
        result = subprocess.run(
            [sys.executable, str(MOVE_AUDIT), str(ROOT / "crawl-ref" / "source")],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)

    def test_entry_points_export_executed_scripts_directory(self) -> None:
        verify_zh = VERIFY_ZH.read_text(encoding="utf-8")
        run_all = RUN_ALL.read_text(encoding="utf-8")
        self.assertIn(
            'export PYTHONPATH="${SCRIPT_DIR}${PYTHONPATH:+:$PYTHONPATH}"',
            verify_zh,
        )
        self.assertIn(
            'export PYTHONPATH="${SCRIPTS_ROOT}${PYTHONPATH:+:$PYTHONPATH}"',
            run_all,
        )
        self.assertLess(
            verify_zh.index("SCRIPT_DIR="),
            verify_zh.index('export PYTHONPATH="${SCRIPT_DIR}'),
        )
        self.assertLess(
            run_all.index("SCRIPTS_ROOT="),
            run_all.index('export PYTHONPATH="${SCRIPTS_ROOT}'),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
