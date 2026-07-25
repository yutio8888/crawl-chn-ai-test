#!/usr/bin/env python3

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


TEST_DIR = Path(__file__).resolve().parent
SCRIPT = TEST_DIR.parent / "audit_item_name_inventory.py"

SPEC = importlib.util.spec_from_file_location(
    "audit_item_name_inventory", SCRIPT
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ItemNameInventoryAuditTest(unittest.TestCase):
    def test_source_entries_match_textdb_trim_and_replace_semantics(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.txt"
            source.write_text(
                "%%%%\n"
                "Death\n"
                "死亡\n"
                "%%%%\n"
                " death \n"
                "\n"
                "的死亡\n",
                encoding="utf-8",
            )
            entries = MODULE.source_entries(source)
        self.assertEqual({"death": "的死亡"}, entries)

    def test_tag_branch_filter_works_without_generated_build_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "sample.cc"
            source.write_text(
                "before\n"
                "#if TAG_MAJOR_VERSION == 34\n"
                "current\n"
                "#else\n"
                "future\n"
                "#endif\n"
                "after\n",
                encoding="utf-8",
            )
            with mock.patch.object(MODULE, "tag_major_version",
                                   return_value=34):
                active = MODULE.active_source(source)
        self.assertIn("before", active)
        self.assertIn("current", active)
        self.assertNotIn("future", active)
        self.assertIn("after", active)

    def test_inventory_violations_reject_each_minimal_mutation(self):
        valid = [{
            "identity": "weapon:WPN_TEST",
            "current_chinese_name": "测试武器",
            "translation_present": True,
            "runtime_lookup": True,
            "forms": {
                "verbose": {"en": "test", "zh": "测试"},
            },
        }]
        self.assertEqual(
            {
                "duplicates": [],
                "missing_identities": [],
                "unexpected_identities": [],
                "missing_chinese": [],
                "missing_forms": [],
            },
            MODULE.inventory_violations(valid),
        )

        duplicate = valid + [dict(valid[0])]
        self.assertEqual(
            ["weapon:WPN_TEST"],
            MODULE.inventory_violations(duplicate)["duplicates"],
        )

        self.assertEqual(
            ["weapon:WPN_MISSING"],
            MODULE.inventory_violations(
                valid, {"weapon:WPN_TEST", "weapon:WPN_MISSING"}
            )["missing_identities"],
        )

        self.assertEqual(
            ["weapon:WPN_TEST"],
            MODULE.inventory_violations(valid, set())[
                "unexpected_identities"
            ],
        )

        missing_translation = [dict(valid[0], translation_present=False)]
        self.assertEqual(
            ["weapon:WPN_TEST"],
            MODULE.inventory_violations(missing_translation)[
                "missing_chinese"
            ],
        )

        missing_form = [dict(valid[0])]
        missing_form[0]["forms"] = {
            "verbose": {"en": "test", "zh": None},
        }
        self.assertEqual(
            ["weapon:WPN_TEST:verbose"],
            MODULE.inventory_violations(missing_form)["missing_forms"],
        )

    def test_cli_builds_complete_unique_production_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "inventory.json"
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "--output", str(output)],
                cwd=MODULE.ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual("dcss-item-name-review-inventory-v1",
                         payload["schema"])
        self.assertEqual(payload["count"], len(payload["rows"]))
        self.assertEqual(
            payload["category_counts"],
            {
                category: sum(
                    row["category"] == category for row in payload["rows"]
                )
                for category in sorted(payload["category_counts"])
            },
        )
        self.assertEqual(
            payload["count"],
            len({row["identity"] for row in payload["rows"]}),
        )
        self.assertFalse(payload["duplicates"])
        self.assertFalse(payload["missing_identities"])
        self.assertFalse(payload["unexpected_identities"])
        self.assertFalse(payload["missing_chinese"])
        self.assertFalse(payload["missing_forms"])

    def test_cli_returns_failure_when_inventory_has_violation(self):
        payload = {
            "baseline": "test",
            "glossary_sha256": "0" * 64,
            "inventory_sha256": "1" * 64,
            "count": 1,
            "category_counts": {"weapon": 1},
            "duplicates": ["weapon:WPN_TEST"],
            "missing_identities": [],
            "unexpected_identities": [],
            "missing_chinese": [],
            "missing_forms": [],
            "rows": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "inventory.json"
            with mock.patch.object(MODULE, "build_inventory",
                                   return_value=payload):
                with contextlib.redirect_stderr(io.StringIO()):
                    result = MODULE.main(["--output", str(output)])
        self.assertEqual(1, result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
