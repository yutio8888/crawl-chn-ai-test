#!/usr/bin/env python3
"""Exercise the cloud inventory's real Git-object producer search.

The search must run on the pinned baseline commit's Git objects with a
POSIX-ERE pattern: GNU regex extensions (\\s, \\b) and rev-parse's
--end-of-options flag are not portable to the host grep used by git grep.
"""
import contextlib
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "cloud_inventory.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("cloud_inventory", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CloudProducerSearchTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        self.patch = mock.patch.object(MODULE, "ROOT", self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        source = self.root / "crawl-ref/source"
        source.mkdir(parents=True)
        self.producer = source / "spell.cc"
        self.producer.write_text(
            "place_cloud(CLOUD_FIRE, pos);\n"
            "big_cloud( CLOUD_FIRE, pos);\n"
            "place_cloud(CLOUD_FIRE_OTHER, pos);\n"
            "big_cloud\t(\tCLOUD_FIRE, pos);\n"
            "place_cloud(CLOUD_FIRE2, pos);\n",
            encoding="utf-8",
        )
        (source / "cloud.cc").write_text("place_cloud(CLOUD_FIRE, pos);\n")
        for args in (["init", "-q"], ["add", "."],
                     ["-c", "user.name=Inventory Test", "-c",
                      "user.email=inventory@example.invalid", "commit", "-qm", "fixture"]):
            subprocess.run(["git", *args], cwd=self.root, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.commit = MODULE.resolve_commit("HEAD")

    def test_real_git_search_uses_pinned_blob_and_complete_enum(self):
        self.producer.write_text("place_cloud(CLOUD_COLD, pos);\n")
        self.assertEqual([
            "spell.cc:1:place_cloud(CLOUD_FIRE, pos);",
            "spell.cc:2:big_cloud( CLOUD_FIRE, pos);",
            "spell.cc:4:big_cloud\t(\tCLOUD_FIRE, pos);",
        ], MODULE.grep_producers(self.commit, "CLOUD_FIRE"))
        self.assertEqual([], MODULE.grep_producers(self.commit, "CLOUD_COLD"))

    def test_unresolved_ref_is_rejected_before_git(self):
        with self.assertRaisesRegex(ValueError, "resolved commit SHA"):
            MODULE.grep_producers("--all", "CLOUD_FIRE")

    def test_git_error_is_not_treated_as_no_producers(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            MODULE.grep_producers("0" * 40, "CLOUD_FIRE")


if __name__ == "__main__":
    unittest.main()
