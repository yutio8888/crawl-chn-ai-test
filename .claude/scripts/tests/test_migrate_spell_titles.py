#!/usr/bin/env python3
"""Focused end-to-end tests for the read-only spell inventory CLI."""

from __future__ import annotations

import json
import hashlib
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/migrate_spell_titles.py"
SPL_DATA = ROOT / "crawl-ref/source/spl-data.h"
SPELL_TYPE = ROOT / "crawl-ref/source/spell-type.h"
TAG_VERSION = ROOT / "crawl-ref/source/tag-version.h"
SOURCE_TXT = ROOT / "crawl-ref/source/dat/i18n/zh/source.txt"
EN_DESC = ROOT / "crawl-ref/source/dat/descript/spells.txt"
ZH_DESC = ROOT / "crawl-ref/source/dat/descript/zh/spells.txt"


class SpellInventoryCliTest(unittest.TestCase):
    def run_cli(self, *args: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), *map(str, args)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def inventory_args(self, spl_data: Path = SPL_DATA,
                       source_txt: Path = SOURCE_TXT,
                       en_desc: Path = EN_DESC,
                       zh_desc: Path = ZH_DESC) -> tuple[object, ...]:
        return (
            "inventory", "--spl-data", spl_data, "--source-txt", source_txt,
            "--spell-type", SPELL_TYPE,
            "--tag-version", TAG_VERSION,
            "--en-descriptions", en_desc, "--zh-descriptions", zh_desc,
        )

    def test_default_is_help_and_real_inventory_is_complete_unique_deterministic(self):
        protected = (
            SPL_DATA, SPELL_TYPE, TAG_VERSION, SOURCE_TXT, EN_DESC, ZH_DESC,
        )
        before = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in protected
        }
        default = self.run_cli()
        explicit_help = self.run_cli("--help")
        self.assertEqual(default.returncode, 0, default.stderr)
        self.assertEqual(explicit_help.returncode, 0, explicit_help.stderr)
        self.assertIn("inventory", default.stdout)
        self.assertEqual(default.stdout, explicit_help.stdout)
        after = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in protected
        }
        self.assertEqual(before, after)

        first = self.run_cli(*self.inventory_args())
        second = self.run_cli(*self.inventory_args())
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        artifact = json.loads(first.stdout)
        spells = artifact["spells"]
        self.assertGreater(len(spells), 400)
        self.assertEqual(
            artifact["assertions"]["parsed_spell_count"],
            artifact["assertions"]["unique_enum_count"],
        )
        self.assertEqual(
            artifact["assertions"]["parsed_spell_count"],
            artifact["assertions"]["expected_enum_count"],
        )
        self.assertTrue(
            artifact["assertions"]["enum_identity_complete_and_unique"]
        )
        self.assertEqual(
            {"kind": "repo_relative", "path": "crawl-ref/source/spl-data.h"},
            artifact["inputs"]["spl_data"],
        )
        self.assertNotIn(str(ROOT), first.stdout)
        lifecycle_by_enum = {
            spell["enum"]: spell["lifecycle"] for spell in spells
        }
        self.assertEqual(lifecycle_by_enum["SPELL_MAGIC_DART"], "active")
        self.assertEqual(
            lifecycle_by_enum["SPELL_CONTROLLED_BLINK"], "axed_compat"
        )
        self.assertEqual(
            lifecycle_by_enum["SPELL_NO_SPELL"], "internal_placeholder"
        )
        self.assertEqual(
            lifecycle_by_enum["SPELL_MELEE"], "internal_placeholder"
        )
        self.assertEqual(
            lifecycle_by_enum["SPELL_PYRRHIC_RECOLLECTION"],
            "description_dummy",
        )
        self.assertEqual(
            {"enum", "english_title", "level", "schools_expression",
             "flags_expression", "lifecycle", "zh_title", "description_key",
             "en_description_present", "zh_description_present"},
            set(spells[0]),
        )

    def test_external_input_is_explicitly_marked(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spl-data.h"
            path.write_text(SPL_DATA.read_text(encoding="utf-8"), encoding="utf-8")
            result = self.run_cli(*self.inventory_args(spl_data=path))
            artifact = json.loads(result.stdout) if result.returncode == 0 else {}
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(artifact["inputs"]["spl_data"]["kind"], "external")
        self.assertEqual(artifact["inputs"]["spl_data"]["path"], str(path.resolve()))

    def test_production_textdb_semantics_for_spell_lookup_and_description_key(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            source = temp / "source.txt"
            en_desc = temp / "en-spells.txt"
            zh_desc = temp / "zh-spells.txt"
            source.write_text(
                "%%%%\nMAGIC DART\n旧值\n"
                "%%%%\nmagic dart\n\n" + r"新\n值\t\\尾" + "\n",
                encoding="utf-8",
            )
            en_desc.write_text(
                "%%%%\n   Magic Dart spell   \n\nEnglish body\n",
                encoding="utf-8",
            )
            zh_desc.write_text(
                "%%%%\n\tMagic Dart spell\t\n\n中文正文\n",
                encoding="utf-8",
            )
            result = self.run_cli(
                *self.inventory_args(
                    source_txt=source, en_desc=en_desc, zh_desc=zh_desc
                )
            )
            artifact = json.loads(result.stdout) if result.returncode == 0 else {}
        self.assertEqual(result.returncode, 0, result.stderr)
        magic_dart = next(
            row for row in artifact["spells"]
            if row["enum"] == "SPELL_MAGIC_DART"
        )
        self.assertEqual(magic_dart["zh_title"], "新\n值\t\\尾")
        self.assertTrue(magic_dart["en_description_present"])
        self.assertTrue(magic_dart["zh_description_present"])

    def test_deleting_complete_active_record_is_rejected_by_enum_authority(self):
        original = SPL_DATA.read_text(encoding="utf-8")
        mutated, count = re.subn(
            r'(?ms)\n\{\n\s*SPELL_MAGIC_DART,\s*"Magic Dart",.*?\n\},\n',
            "\n",
            original,
            count=1,
        )
        self.assertEqual(count, 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spl-data.h"
            path.write_text(mutated, encoding="utf-8")
            result = self.run_cli(*self.inventory_args(spl_data=path))
        self.assertEqual(result.returncode, 2)
        self.assertIn("missing=['SPELL_MAGIC_DART']", result.stderr)

    def test_deleting_axed_record_is_rejected_by_enum_authority(self):
        original = SPL_DATA.read_text(encoding="utf-8")
        mutated = original.replace(
            'AXED_SPELL(SPELL_AURA_OF_ABJURATION, "Aura of Abjuration")\n',
            "",
            1,
        )
        self.assertNotEqual(mutated, original)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spl-data.h"
            path.write_text(mutated, encoding="utf-8")
            result = self.run_cli(*self.inventory_args(spl_data=path))
        self.assertEqual(result.returncode, 2)
        self.assertIn("missing=['SPELL_AURA_OF_ABJURATION']", result.stderr)

    def test_duplicate_enum_minimal_mutation_is_rejected(self):
        original = SPL_DATA.read_text(encoding="utf-8")
        mutated = original.replace(
            "SPELL_MAGIC_DART, \"Magic Dart\",",
            "SPELL_CAUSE_FEAR, \"Magic Dart\",",
            1,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spl-data.h"
            path.write_text(mutated, encoding="utf-8")
            result = self.run_cli(*self.inventory_args(spl_data=path))
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate spell enum", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_incomplete_spell_record_minimal_mutation_is_rejected(self):
        original = SPL_DATA.read_text(encoding="utf-8")
        mutated = original.replace(
            'SPELL_MAGIC_DART, "Magic Dart",',
            'SPELL_MAGIC_DART,',
            1,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spl-data.h"
            path.write_text(mutated, encoding="utf-8")
            result = self.run_cli(*self.inventory_args(spl_data=path))
        self.assertEqual(result.returncode, 2)
        self.assertIn("expected 10 spell_desc fields", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_malformed_source_mapping_minimal_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.txt"
            path.write_text("unexpected data without a separator\n", encoding="utf-8")
            result = self.run_cli(*self.inventory_args(source_txt=path))
        self.assertEqual(result.returncode, 2)
        self.assertIn("no TextDB entries", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
