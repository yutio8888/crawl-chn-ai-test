#!/usr/bin/env python3

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
SCRIPT = TEST_DIR.parent / "audit_god_inventory.py"
SPEC = importlib.util.spec_from_file_location("audit_god_inventory", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def clean_fixture():
    parents = [{
        "identity": "GOD_TEST",
        "english_name": "Test",
        "current_chinese_name": "测试神",
        "current_chinese_titles": ["测试称号"] * 8,
    }]
    names = {
        "GOD_TEST": {"en": "Test", "key": "Test"},
    }
    databases = {
        "english_gods": {
            "test": "main",
            "test powers": "powers",
            "test wrath": "wrath",
        },
        "chinese_gods": {
            "test": "主体",
            "test powers": "能力",
            "test wrath": "惩罚",
        },
        "english_godname": {"test lastname": "Test the Test"},
        "chinese_godname": {"test lastname": "测试之神"},
        "english_godspeak": {"test death": "message"},
        "chinese_godspeak": {"test death": "消息"},
        "duplicates": {},
    }
    titles = [["none"] * 8, ["test"] * 8]
    return parents, names, databases, titles


class GodInventoryAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = MODULE.build_inventory()

    def test_production_parent_inventory_is_complete_unique_and_includes_pakellas(self):
        identities = [row["identity"] for row in self.payload["parents"]]
        self.assertEqual(MODULE.god_enum_identities(), identities)
        self.assertEqual(len(identities), len(set(identities)))
        pakellas = next(
            row for row in self.payload["parents"]
            if row["identity"] == "GOD_PAKELLAS"
        )
        self.assertEqual("Pakellas", pakellas["english_name"])
        self.assertEqual("compatibility_disabled", pakellas["lifecycle"])
        for row in self.payload["parents"]:
            self.assertTrue(row["current_chinese_name"])
            self.assertEqual(8, len(row["current_chinese_titles"]))
            self.assertTrue(all(row["current_chinese_titles"]))
            for field in (
                "ability_ids",
                "passive_ids",
                "disliked_conduct_ids",
                "liked_conduct_ids",
                "dynamic_ability_source",
                "wrath_key",
            ):
                self.assertIn(field, row)
            self.assertEqual(
                row["english_name"].lower() + " wrath", row["wrath_key"]
            )
        self.assertEqual(
            {
                "GOD_RU",
                "GOD_ASHENZARI",
                "GOD_HEPLIAKLQANA",
                "GOD_NEMELEX_XOBEH",
            },
            {
                row["identity"] for row in self.payload["parents"]
                if row["dynamic_ability_source"]
            },
        )

    def test_production_database_sets_and_title_slots_are_frozen(self):
        self.assertEqual(
            {
                "god_descriptions": 82,
                "god_longnames": 23,
                "godspeak": 193,
            },
            self.payload["textdb_counts"],
        )
        self.assertEqual(224, self.payload["child_counts"]["title_slots"])
        self.assertTrue(all(
            len(row["title_slots"]) == 8 for row in self.payload["parents"]
        ))

    def test_current_review_findings_are_visible_and_exactly_enumerated(self):
        findings = self.payload["review_findings"]
        self.assertEqual(6, len(findings["zh_only_ability_keys"]))
        self.assertNotIn(
            "ancestor life: elementalist ability",
            findings["zh_only_ability_keys"],
        )
        self.assertNotIn(
            "recall orcish followers ability",
            findings["zh_only_ability_keys"],
        )
        self.assertEqual(0, len(findings["godspeak_topology_drift"]))
        self.assertEqual(
            0,
            len({row["key"] for row in findings["godspeak_topology_drift"]}),
        )

    def test_inventory_rejects_each_parent_and_database_mutation(self):
        parents, names, databases, titles = clean_fixture()

        def violations(
            candidate_parents=parents,
            candidate_names=names,
            candidate_databases=databases,
            candidate_titles=titles,
            death_safe=True,
        ):
            return MODULE.inventory_violations(
                candidate_parents,
                ["GOD_TEST"],
                candidate_names,
                candidate_names,
                set(),
                candidate_databases,
                candidate_titles,
                death_safe,
            )

        self.assertTrue(all(not value for value in violations().values()))

        duplicate = parents + [dict(parents[0])]
        self.assertEqual(
            ["GOD_TEST"],
            violations(candidate_parents=duplicate)[
                "duplicate_parent_identities"
            ],
        )

        missing_name = dict(names)
        missing_name.pop("GOD_TEST")
        self.assertEqual(
            ["GOD_TEST"],
            violations(candidate_names=missing_name)[
                "missing_english_identity_names"
            ],
        )

        missing_description = copy.deepcopy(databases)
        missing_description["english_gods"].pop("test wrath")
        self.assertEqual(
            ["test wrath"],
            violations(candidate_databases=missing_description)[
                "missing_god_description_keys"
            ],
        )

        locale_mismatch = copy.deepcopy(databases)
        locale_mismatch["chinese_godspeak"].pop("test death")
        self.assertEqual(
            ["test death"],
            violations(candidate_databases=locale_mismatch)[
                "godspeak_locale_key_mismatch"
            ],
        )

        self.assertEqual(
            {"expected": 2, "actual": 1},
            violations(candidate_titles=titles[:-1])[
                "title_row_count_mismatch"
            ],
        )
        self.assertEqual(
            ["ouch.cc:_god_death_messages"],
            violations(death_safe=False)["death_lookup_uses_display_name"],
        )

        missing_chinese = copy.deepcopy(parents)
        missing_chinese[0]["current_chinese_name"] = None
        self.assertEqual(
            ["GOD_TEST"],
            violations(candidate_parents=missing_chinese)[
                "missing_current_chinese_names"
            ],
        )
        missing_title = copy.deepcopy(parents)
        missing_title[0]["current_chinese_titles"][3] = None
        self.assertEqual(
            ["GOD_TEST:3"],
            violations(candidate_parents=missing_title)[
                "missing_current_chinese_titles"
            ],
        )

        child_tables = {
            "abilities": ["no god", "test"],
            "passives": ["no god", "test"],
        }
        clean_children = MODULE.inventory_violations(
            parents,
            ["GOD_TEST"],
            names,
            names,
            set(),
            databases,
            titles,
            True,
            child_tables,
            {},
        )
        self.assertFalse(clean_children["child_row_count_mismatches"])
        child_tables["abilities"].pop()
        self.assertEqual(
            {"abilities": {"expected": 2, "actual": 1}},
            MODULE.inventory_violations(
                parents,
                ["GOD_TEST"],
                names,
                names,
                set(),
                databases,
                titles,
                True,
                child_tables,
                {},
            )["child_row_count_mismatches"],
        )

    def test_weighted_topology_detects_minimal_weight_and_reference_drift(self):
        known = {"root", "child"}
        base = MODULE.weighted_topology("w:2\n@child@\n\nplain", known)
        same = MODULE.weighted_topology("w:2\n译文\n\n其他", known)
        changed_weight = MODULE.weighted_topology(
            "w:3\n译文\n\n其他", known
        )
        changed_reference = MODULE.weighted_topology(
            "w:2\n译文\n\n@child@", known
        )
        self.assertNotEqual(base, same)
        self.assertNotEqual(same, changed_weight)
        self.assertNotEqual(same, changed_reference)

    def test_review_coverage_requires_one_terminal_row_per_parent(self):
        payload = {
            "parents": [
                {"identity": "GOD_TEST"},
                {"identity": "GOD_OTHER"},
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.md"
            path.write_text(
                "| `GOD_TEST` | current | facts | 保留 |\n"
                "| `GOD_OTHER` | current | facts | 修订 |\n",
                encoding="utf-8",
            )
            self.assertTrue(MODULE.review_coverage(payload, path)[
                "coverage_equal"
            ])
            path.write_text(
                "| `GOD_TEST` | current | facts | 保留 |\n"
                "| `GOD_TEST` | current | facts | 保留 |\n",
                encoding="utf-8",
            )
            coverage = MODULE.review_coverage(payload, path)
            self.assertFalse(coverage["coverage_equal"])
            self.assertEqual(["GOD_TEST"], coverage[
                "duplicate_evidence_cards"
            ])
            self.assertEqual(["GOD_OTHER"], coverage[
                "missing_evidence_cards"
            ])


if __name__ == "__main__":
    unittest.main()
