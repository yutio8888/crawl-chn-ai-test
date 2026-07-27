#!/usr/bin/env python3

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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

    def test_enum_parser_keeps_explicit_expressions_and_excludes_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "status.h"
            source = (
                "STATUS_AIRBORNE = NUM_DURATIONS + 1,\n"
                "STATUS_CURRENT,\n"
                "STATUS_LAST_STATUS = STATUS_CURRENT,\n"
            )
            with mock.patch.object(MODULE, "active_source", return_value=source):
                self.assertEqual(
                    ["STATUS_AIRBORNE", "STATUS_CURRENT"],
                    MODULE.concrete_enum_identities(path, "STATUS_"),
                )

    def test_status_producer_proof_rejects_each_conservation_failure(self):
        source = """
        static void _describe_one(status_info& inf)
        {
            inf.light_text = T_("One");
        }
        """
        clean = MODULE.status_producer_proof(
            ["STATUS_ONE", "STATUS_IN_DEBT"],
            {"STATUS_ONE": "case STATUS_ONE: _describe_one(inf); break;"},
            source,
        )
        self.assertFalse(any(
            clean[key] for key in (
                "missing_status_producers",
                "unexpected_status_producers",
                "stale_producerless_status_exceptions",
                "unresolved_status_helpers",
            )
        ))

        missing = MODULE.status_producer_proof(
            ["STATUS_ONE", "STATUS_TWO", "STATUS_IN_DEBT"],
            {"STATUS_ONE": "case STATUS_ONE: break;"},
            source,
        )
        self.assertEqual(
            ["STATUS_TWO"], missing["missing_status_producers"]
        )

        unexpected = MODULE.status_producer_proof(
            ["STATUS_ONE", "STATUS_IN_DEBT"],
            {
                "STATUS_ONE": "case STATUS_ONE: break;",
                "STATUS_UNKNOWN": "case STATUS_UNKNOWN: break;",
            },
            source,
        )
        self.assertEqual(
            ["STATUS_UNKNOWN"], unexpected["unexpected_status_producers"]
        )

        stale = MODULE.status_producer_proof(
            ["STATUS_ONE", "STATUS_IN_DEBT"],
            {
                "STATUS_ONE": "case STATUS_ONE: break;",
                "STATUS_IN_DEBT": "case STATUS_IN_DEBT: break;",
            },
            source,
        )
        self.assertEqual(
            ["STATUS_IN_DEBT"],
            stale["stale_producerless_status_exceptions"],
        )

        unresolved = MODULE.status_producer_proof(
            ["STATUS_ONE", "STATUS_IN_DEBT"],
            {"STATUS_ONE": "case STATUS_ONE: _describe_missing(inf); break;"},
            source,
        )
        self.assertEqual(
            ["STATUS_ONE"], unresolved["unresolved_status_helpers"]
        )

    def test_airborne_card_contains_helper_display_facts(self):
        rows, proof = MODULE.status_rows({}, with_proof=True)
        airborne = next(
            row for row in rows
            if row["identity"] == "status:STATUS_AIRBORNE"
        )
        self.assertTrue(airborne["producer_present"])
        self.assertEqual(["Fly"], airborne["db_keys"])
        self.assertEqual(
            ["Fly", "flying", "You are flying."],
            [item["english"] for item in airborne["display_strings"]],
        )
        self.assertFalse(any(proof.values()))

    def test_airborne_missing_or_incomplete_card_is_a_violation(self):
        descriptions = {}
        missing = MODULE.inventory_violations(
            [], descriptions,
            {
                "missing_status_producers": ["STATUS_AIRBORNE"],
                "unexpected_status_producers": [],
                "stale_producerless_status_exceptions": [],
                "unresolved_status_helpers": [],
            },
        )
        self.assertEqual(
            ["STATUS_AIRBORNE"], missing["missing_status_producers"]
        )
        incomplete = [{
            "identity": "status:STATUS_AIRBORNE",
            "category": "status",
            "lifecycle": "current",
            "display_strings": [{
                "lookup_key": "Fly",
                "english": "Fly",
                "translation_present": True,
            }],
        }]
        facts = MODULE.inventory_violations(incomplete, descriptions)
        self.assertIn(
            "status:STATUS_AIRBORNE",
            facts["missing_status_display_facts"],
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
            "glossary_sha256": "a" * 64,
            "inventory_sha256": "b" * 64,
            "count": 2,
            "rows": [
                {"identity": "mutation:MUT_TEST"},
                {"identity": "attribute:STAT_STR"},
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.md"
            conclusions = {
                "mutation:MUT_TEST": "keep",
                "attribute:STAT_STR": "adjust",
            }
            path.write_text(
                MODULE.strict_review_block(payload, conclusions) + "\n",
                encoding="utf-8",
            )
            clean = MODULE.review_coverage(payload, path)
            self.assertTrue(clean["coverage_equal"])

            conclusions["mutation:MUT_TEST"] = "pending"
            text = MODULE.strict_review_block(payload, conclusions)
            text = "\n".join(
                line for line in text.splitlines()
                if '"identity":"attribute:STAT_STR"' not in line
            )
            path.write_text(text + "\n", encoding="utf-8")
            broken = MODULE.review_coverage(payload, path)
        self.assertFalse(broken["coverage_equal"])
        self.assertEqual(
            ["attribute:STAT_STR"], broken["missing_evidence_cards"]
        )
        self.assertEqual(
            ["mutation:MUT_TEST"], broken["invalid_terminal_conclusions"]
        )

    def test_strict_review_rejects_stale_bindings_fact_and_card_mutations(self):
        payload = {
            "glossary_sha256": "a" * 64,
            "inventory_sha256": "b" * 64,
            "count": 2,
            "rows": [
                {"identity": "status:STATUS_ONE", "fact": "one"},
                {"identity": "status:STATUS_TWO", "fact": "two"},
            ],
        }
        clean_text = MODULE.strict_review_block(
            payload,
            {
                "status:STATUS_ONE": "keep",
                "status:STATUS_TWO": "adjust",
            },
        )

        def mutate_metadata(text, field, value):
            lines = text.splitlines()
            metadata = json.loads(lines[1])
            metadata[field] = value
            lines[1] = json.dumps(
                metadata, sort_keys=True, separators=(",", ":")
            )
            return "\n".join(lines)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.md"
            path.write_text(clean_text + "\n", encoding="utf-8")
            self.assertTrue(MODULE.review_coverage(payload, path)[
                "coverage_equal"
            ])
            for field, value in (
                ("baseline", "0" * 40),
                ("glossary_sha256", "0" * 64),
                ("inventory_sha256", "1" * 64),
                ("identity_count", 3),
            ):
                with self.subTest(field=field):
                    path.write_text(
                        mutate_metadata(clean_text, field, value) + "\n",
                        encoding="utf-8",
                    )
                    self.assertFalse(MODULE.review_coverage(payload, path)[
                        "coverage_equal"
                    ])

            lines = clean_text.splitlines()
            first = json.loads(lines[3])
            second = json.loads(lines[4])
            mutations = {
                "fact": [
                    *lines[:3],
                    json.dumps(
                        dict(first, fact_sha256="0" * 64),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    *lines[4:],
                ],
                "pending": [
                    *lines[:3],
                    json.dumps(
                        dict(first, terminal_conclusion="pending"),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    *lines[4:],
                ],
                "duplicate": [*lines[:4], lines[3], *lines[4:]],
                "missing": [*lines[:3], *lines[4:]],
                "extra": [
                    *lines[:5],
                    json.dumps(
                        dict(second, identity="status:STATUS_EXTRA"),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    *lines[5:],
                ],
                "reordered": [*lines[:3], lines[4], lines[3], *lines[5:]],
            }
            for name, mutated in mutations.items():
                with self.subTest(mutation=name):
                    path.write_text("\n".join(mutated) + "\n", encoding="utf-8")
                    self.assertFalse(MODULE.review_coverage(payload, path)[
                        "coverage_equal"
                    ])

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
