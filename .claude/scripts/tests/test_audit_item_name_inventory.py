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
    def test_source_entries_match_localized_sourcedb_semantics(self):
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory)
            source = source_dir / "source.txt"
            source.write_text(
                "%%%%\n"
                "Death\n"
                "死亡\n"
                "%%%%\n"
                " death \n"
                "带空格\n",
                encoding="utf-8",
            )
            (source_dir / "items.txt").write_text(
                "%%%%\n"
                "Death\n"
                "后定义\n",
                encoding="utf-8",
            )
            entries = MODULE.source_entries(source_dir)
        self.assertEqual(
            {"death": "后定义", " death ": "带空格"},
            entries,
        )

    def test_source_entries_requires_source_txt(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                MODULE.source_entries(Path(directory))

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

    def test_tag_branch_filter_rejects_unknown_tag_expression(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "sample.cc"
            source.write_text(
                "#if TAG_MAJOR_VERSION == 34 || defined(TEST_ONLY)\n"
                "ambiguous\n"
                "#endif\n",
                encoding="utf-8",
            )
            with mock.patch.object(MODULE, "tag_major_version",
                                   return_value=34):
                with self.assertRaisesRegex(
                    RuntimeError, "unsupported TAG_MAJOR_VERSION condition"
                ):
                    MODULE.active_source(source)

    def test_tag_branch_filter_rejects_mixed_elif_chain(self):
        for tag_condition in ("== 34", "> 34"):
            with self.subTest(tag_condition=tag_condition):
                with tempfile.TemporaryDirectory() as directory:
                    source = Path(directory) / "sample.cc"
                    source.write_text(
                        f"#if TAG_MAJOR_VERSION {tag_condition}\n"
                        "tag branch\n"
                        "#elif defined(TEST_ONLY)\n"
                        "unknown branch\n"
                        "#else\n"
                        "fallback branch\n"
                        "#endif\n",
                        encoding="utf-8",
                    )
                    with mock.patch.object(MODULE, "tag_major_version",
                                           return_value=34):
                        with self.assertRaisesRegex(
                            RuntimeError,
                            "unsupported non-TAG #elif in TAG condition chain",
                        ):
                            MODULE.active_source(source)

    def test_contextual_item_overrides_fail_closed_on_syntax_drift(self):
        item_name = MODULE.active_source(MODULE.SRC / "item-name.cc")
        broken_brand = item_name.replace(
            "brand == SPWPN_DRAINING", "brand != SPWPN_DRAINING", 1
        )
        with self.assertRaisesRegex(
            RuntimeError, "unparsed contextual weapon-brand"
        ):
            MODULE.contextual_brand_forms(broken_brand)

        broken_book = item_name.replace(
            "sub_type == BOOK_NECROMANCY",
            "sub_type != BOOK_NECROMANCY",
            1,
        )
        with self.assertRaisesRegex(
            RuntimeError, "unparsed contextual book-name"
        ):
            MODULE.contextual_book_names(broken_book)

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

        missing_form_translation = [dict(valid[0])]
        missing_form_translation[0]["category"] = "weapon_brand"
        missing_form_translation[0]["forms"] = {
            "verbose": {"en": "test", "zh": None},
            "terse": {"en": "test", "zh": "测试"},
            "adj": {"en": "test", "zh": "测试"},
        }
        self.assertEqual(
            ["weapon:WPN_TEST:verbose"],
            MODULE.inventory_violations(missing_form_translation)[
                "missing_forms"
            ],
        )

        missing_form_producer = [dict(valid[0])]
        missing_form_producer[0]["category"] = "armour_ego"
        missing_form_producer[0]["forms"] = {
            "verbose": {"en": "test", "zh": "测试"},
        }
        self.assertEqual(
            ["weapon:WPN_TEST:terse"],
            MODULE.inventory_violations(missing_form_producer)[
                "missing_forms"
            ],
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
        by_identity = {row["identity"]: row for row in payload["rows"]}
        self.assertEqual(
            "armour ego full name|invisibility",
            by_identity["armour_ego:SPARM_INVISIBILITY"]["translation_key"],
        )
        self.assertEqual(
            "armour ego full name|infusion",
            by_identity["armour_ego:SPARM_INFUSION"]["translation_key"],
        )
        self.assertEqual(
            "book full name|Necromancy",
            by_identity["book:BOOK_NECROMANCY"]["translation_key"],
        )
        draining = by_identity["weapon_brand:SPWPN_DRAINING"]
        self.assertEqual(
            "weapon brand full name|draining",
            draining["translation_key"],
        )
        self.assertEqual(
            {"verbose": "汲取", "terse": "汲取", "adj": "汲取"},
            {
                form: data["zh"]
                for form, data in draining["forms"].items()
            },
        )

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
