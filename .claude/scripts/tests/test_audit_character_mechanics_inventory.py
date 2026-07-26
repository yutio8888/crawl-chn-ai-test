#!/usr/bin/env python3

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
SCRIPT = TEST_DIR.parent / "audit_character_mechanics_inventory.py"

SPEC = importlib.util.spec_from_file_location(
    "audit_character_mechanics_inventory", SCRIPT
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CharacterMechanicsInventoryAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = MODULE.build_inventory()

    def test_cpp_string_and_initializer_parsers_preserve_structure(self):
        row = (
            '{ ABIL_TEST, NC_("context", "Test Name"), 1, '
            '{ nested, 2 }, "tail" }'
        )
        self.assertEqual(
            ["ABIL_TEST", 'NC_("context", "Test Name")', "1",
             "{ nested, 2 }", '"tail"'],
            MODULE.initializer_fields(row),
        )
        self.assertEqual(
            ["context", "Test Name", "tail"],
            MODULE.cpp_strings(row),
        )

    def test_context_translation_uses_runtime_fallback(self):
        contextual = MODULE.translation(
            {"mutation|clever": "聪慧", "plain": "普通"},
            "clever",
            "mutation",
        )
        self.assertEqual("聪慧", contextual["chinese"])
        self.assertEqual("mutation|clever", contextual["resolved_lookup_key"])

        fallback = MODULE.translation({"plain": "普通"}, "plain", "status")
        self.assertEqual("普通", fallback["chinese"])
        self.assertEqual("plain", fallback["resolved_lookup_key"])

    def test_case_fragments_stop_before_default_and_display_only_fields(self):
        body = """
        case STATUS_ONE:
            inf.light_text = T_("One");
            inf.db_key = "One key";
            break;
        case STATUS_TWO:
            inf.long_text = C_("status", "Two long");
            break;
        default:
            inf.short_text = "missing status";
            break;
        """
        fragments = MODULE.case_fragments(body, "STATUS_")
        self.assertNotIn("missing status", fragments["STATUS_TWO"])
        self.assertEqual(
            ["Two long"],
            MODULE.status_display_literals(fragments["STATUS_TWO"]),
        )

    def test_inventory_identities_are_unique_and_category_totals_match(self):
        rows = self.payload["rows"]
        identities = [row["identity"] for row in rows]
        self.assertEqual(len(identities), len(set(identities)))
        self.assertEqual(
            self.payload["count"],
            sum(self.payload["category_counts"].values()),
        )

    def test_production_initializers_match_inventory_categories(self):
        rows = self.payload["rows"]
        mutation_ids = {
            row["identity"].split(":", 1)[1]
            for row in rows if row["category"] == "mutation"
        }
        mutation_data_ids = {
            match.group(1)
            for raw in MODULE.ordered_initializer_rows(
                MODULE.active_source(MODULE.MUTATION_DATA),
                r"\bstatic\s+const\s+mutation_def\s+mut_data\s*\[\]",
            )
            if (match := MODULE.re.search(r"\b(MUT_[A-Z0-9_]+)\b", raw))
        }
        self.assertEqual(mutation_data_ids, mutation_ids)

        duration_ids = {
            row["identity"].split(":", 1)[1]
            for row in rows if row["category"] == "duration"
        }
        self.assertEqual(
            set(MODULE.concrete_enum_identities(
                MODULE.DURATION_TYPE, "DUR_"
            )),
            duration_ids,
        )

    def test_god_abilities_are_explicitly_excluded(self):
        excluded = self.payload["scope"]["excluded_god_ability_identities"]
        ability_ids = {
            row["identity"].split(":", 1)[1]
            for row in self.payload["rows"]
            if row["category"] == "ability"
        }
        self.assertIn("ABIL_ZIN_RECITE", excluded)
        self.assertIn("ABIL_CONVERT_TO_BEOGH", excluded)
        self.assertTrue(ability_ids.isdisjoint(excluded))

    def test_removed_skills_are_compatibility_entries(self):
        rows = {
            row["identity"]: row for row in self.payload["rows"]
            if row["category"] == "skill"
        }
        for identity in (
            "SK_STABBING",
            "SK_TRAPS",
            "SK_CHARMS",
            "SK_SLINGS",
            "SK_CROSSBOWS",
        ):
            self.assertEqual(
                "compatibility",
                rows[f"skill:{identity}"]["lifecycle"],
            )

    def test_unarmed_combat_includes_both_special_title_sets(self):
        row = next(
            row for row in self.payload["rows"]
            if row["identity"] == "skill:SK_UNARMED_COMBAT"
        )
        self.assertEqual(
            {"martial_arts_titles", "claw_and_tooth_titles"},
            set(row["special_title_sets"]),
        )
        for titles in row["special_title_sets"].values():
            self.assertEqual(5, len(titles))
            self.assertTrue(all(title["translation_present"] for title in titles))

    def test_review_coverage_requires_exact_terminal_rows(self):
        payload = {
            "rows": [
                {"identity": "mutation:MUT_TEST"},
                {"identity": "attribute:STAT_STR"},
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.md"
            path.write_text(
                "| `mutation:MUT_TEST` | current | 测试 | 事实 | 保留 |\n"
                "| `attribute:STAT_STR` | current | 力量 | 事实 | 修订：措辞 |\n",
                encoding="utf-8",
            )
            clean = MODULE.review_coverage(payload, path)
            self.assertTrue(clean["coverage_equal"])

            path.write_text(
                "| `mutation:MUT_TEST` | current | 测试 | 事实 | 未决定 |\n",
                encoding="utf-8",
            )
            broken = MODULE.review_coverage(payload, path)
        self.assertFalse(broken["coverage_equal"])
        self.assertEqual(
            ["attribute:STAT_STR"], broken["missing_evidence_cards"]
        )
        self.assertEqual(
            ["mutation:MUT_TEST"], broken["invalid_terminal_conclusions"]
        )

    def test_cli_persists_inventory_when_findings_exist(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "inventory.json"
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "--output", str(output)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertIn(proc.returncode, (0, 1))
            self.assertTrue(output.is_file())
            self.assertIn(
                '"inventory_sha256"', output.read_text(encoding="utf-8")
            )


if __name__ == "__main__":
    unittest.main()
