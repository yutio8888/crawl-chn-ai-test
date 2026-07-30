#!/usr/bin/env python3

import hashlib
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
from i18n_shared import AuditInput


def review_input(path):
    data = path.read_bytes()
    return AuditInput(
        audit_commit=None,
        logical_path="fixtures/review.md",
        relative_path="fixtures/review.md",
        bytes=data,
        text=data.decode("utf-8", errors="strict"),
        sha256=hashlib.sha256(data).hexdigest(),
    )


def decision(conclusion, rationale):
    return {
        "terminal_conclusion": conclusion,
        "reviewer_rationale": rationale,
    }


class CharacterMechanicsInventoryAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = MODULE.build_inventory()

    def test_language_snapshot_handles_non_string_nested_keys(self):
        row = {
            "forms": {
                0: {
                    "english_value": "Full English",
                    "chinese_value": "完整中文",
                },
            },
        }
        self.assertEqual(
            {"forms.0.english_value": "Full English"},
            MODULE.language_snapshot(row, "english"),
        )
        self.assertEqual(
            {"forms.0.chinese_value": "完整中文"},
            MODULE.language_snapshot(row, "chinese"),
        )
        normalized = MODULE.canonical_json_value({
            "forms": {10: "ten", 2: "two"},
        })
        encoded = json.dumps(
            normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        self.assertEqual(normalized, json.loads(encoded))
        with self.assertRaisesRegex(RuntimeError, "colliding JSON object keys"):
            MODULE.canonical_json_value({1: "numeric", "1": "string"})

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

    def test_duration_helper_and_fallthrough_facts_fail_closed(self):
        helper_source = """
        static bool _fill_inf_from_ddef(duration_type dur, status_info& inf)
        {
            inf.db_key = ddef->light_text;
            return true;
        }
        """
        duration_facts = {
            "DUR_ONE": (
                'inf.db_key = "One";\n'
                'inf.light_text = C_("status", "One");'
            ),
            "DUR_TWO": (
                'inf.db_key = "Two";\n'
                'inf.light_text = C_("status", "Two");'
            ),
        }
        one = MODULE.status_producer_proof(
            ["STATUS_ONE"],
            {
                "STATUS_ONE": (
                    "case STATUS_ONE:\n"
                    "_fill_inf_from_ddef(DUR_ONE, inf);\n"
                    "break;"
                ),
            },
            helper_source,
            duration_facts,
        )
        two = MODULE.status_producer_proof(
            ["STATUS_ONE"],
            {
                "STATUS_ONE": (
                    "case STATUS_ONE:\n"
                    "_fill_inf_from_ddef(DUR_TWO, inf);\n"
                    "break;"
                ),
            },
            helper_source,
            duration_facts,
        )
        self.assertFalse(one["unresolved_status_helpers"])
        self.assertFalse(two["unresolved_status_helpers"])
        self.assertEqual(
            ["One"],
            MODULE.status_db_keys(one["resolved_fragments"]["STATUS_ONE"]),
        )
        self.assertEqual(
            ["Two"],
            MODULE.status_db_keys(two["resolved_fragments"]["STATUS_ONE"]),
        )
        self.assertNotEqual(
            MODULE.normalize_producer_fragment(
                one["resolved_fragments"]["STATUS_ONE"]
            ),
            MODULE.normalize_producer_fragment(
                two["resolved_fragments"]["STATUS_ONE"]
            ),
        )
        self.assertNotEqual(
            MODULE.fact_sha256({
                "identity": "status:STATUS_ONE",
                "producer_fragment": MODULE.normalize_producer_fragment(
                    one["resolved_fragments"]["STATUS_ONE"]
                ),
            }),
            MODULE.fact_sha256({
                "identity": "status:STATUS_ONE",
                "producer_fragment": MODULE.normalize_producer_fragment(
                    two["resolved_fragments"]["STATUS_ONE"]
                ),
            }),
        )

        fallthrough = """
        case STATUS_ONE:
            inf.db_key = "Before";
            // Intentional fallthrough
        case DUR_ONE:
            inf.short_text = T_("after");
            break;
        """
        fragments = MODULE.case_fragments(fallthrough, "STATUS_")
        self.assertEqual(
            ["Before"], MODULE.status_db_keys(fragments["STATUS_ONE"])
        )
        self.assertEqual(
            ["after"], MODULE.status_display_literals(fragments["STATUS_ONE"])
        )
        changed = fallthrough.replace(
            'inf.short_text = T_("after");',
            'inf.short_text = T_("changed");',
        )
        changed_fragment = MODULE.case_fragments(changed, "STATUS_")[
            "STATUS_ONE"
        ]
        self.assertNotEqual(
            MODULE.normalize_producer_fragment(fragments["STATUS_ONE"]),
            MODULE.normalize_producer_fragment(changed_fragment),
        )
        self.assertNotEqual(
            MODULE.fact_sha256({
                "identity": "status:STATUS_ONE",
                "producer_fragment": MODULE.normalize_producer_fragment(
                    fragments["STATUS_ONE"]
                ),
            }),
            MODULE.fact_sha256({
                "identity": "status:STATUS_ONE",
                "producer_fragment": MODULE.normalize_producer_fragment(
                    changed_fragment
                ),
            }),
        )

        unknown = MODULE.status_producer_proof(
            ["STATUS_ONE"],
            {"STATUS_ONE": "case STATUS_ONE: _unknown(inf); break;"},
            "",
        )
        self.assertEqual(
            ["STATUS_ONE"], unknown["unresolved_status_helpers"]
        )
        empty = MODULE.status_producer_proof(
            ["STATUS_ONE"],
            {"STATUS_ONE": "case STATUS_ONE: break;"},
            "",
        )
        self.assertEqual(["STATUS_ONE"], empty["unresolved_status_helpers"])

    def test_corrosion_and_lowered_willpower_cards_bind_real_producers(self):
        rows, proof = MODULE.status_rows({}, with_proof=True)
        by_id = {row["identity"]: row for row in rows}
        corrosion = by_id["status:STATUS_CORROSION"]
        lowered = by_id["status:STATUS_LOWERED_WL"]
        self.assertEqual(["Corr"], corrosion["db_keys"])
        self.assertIn(
            "corroded (%d)",
            [item["english"] for item in corrosion["display_strings"]],
        )
        self.assertIn("case DUR_CORROSION:", corrosion["producer_fragment"])
        self.assertEqual(["Will/2"], lowered["db_keys"])
        self.assertIn(
            "You are weak-willed.",
            [item["english"] for item in lowered["display_strings"]],
        )
        self.assertIn(
            "_fill_inf_from_ddef(DUR_LOWERED_WL, inf)",
            lowered["producer_fragment"],
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
                {
                    "identity": "mutation:MUT_TEST",
                    "category": "mutation",
                    "lifecycle": "current",
                    "english_source_name": "Test mutation",
                    "current_chinese_name": "测试变异",
                },
                {
                    "identity": "attribute:STAT_STR",
                    "category": "attribute",
                    "lifecycle": "current",
                    "english_source_name": "strength",
                    "current_chinese_name": "力量",
                },
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.md"
            conclusions = {
                "mutation:MUT_TEST": decision(
                    "keep", "完整 reviewer 理由"
                ),
                "attribute:STAT_STR": decision(
                    "adjust", "explicit attribute rationale"
                ),
            }
            path.write_text(
                MODULE.render_review_results(payload, conclusions),
                encoding="utf-8",
            )
            clean = MODULE.review_coverage(payload, review_input(path))
            self.assertTrue(clean["coverage_equal"])

            text = MODULE.render_review_results(payload, conclusions)
            text = "\n".join(
                line for line in text.splitlines()
                if '"identity":"attribute:STAT_STR"' not in line
            )
            path.write_text(text + "\n", encoding="utf-8")
            broken = MODULE.review_coverage(payload, review_input(path))
        self.assertFalse(broken["coverage_equal"])
        self.assertEqual(
            ["attribute:STAT_STR"], broken["missing_evidence_cards"]
        )
        self.assertEqual(
            [], broken["invalid_terminal_conclusions"]
        )

    def test_strict_review_rejects_stale_bindings_fact_and_card_mutations(self):
        payload = {
            "glossary_sha256": "a" * 64,
            "inventory_sha256": "b" * 64,
            "count": 2,
            "rows": [
                {
                    "identity": "status:STATUS_ONE",
                    "category": "status",
                    "lifecycle": "current",
                    "english_source_name": "one\nwith | pipe",
                    "current_chinese_name": "一\n含 | 管道",
                    "fact": "x" * 200,
                },
                {
                    "identity": "status:STATUS_TWO",
                    "category": "status",
                    "lifecycle": "current",
                    "english_source_name": "two",
                    "current_chinese_name": "二",
                    "fact": "two",
                },
            ],
        }
        clean_text = MODULE.render_review_results(
            payload,
            {
                "status:STATUS_ONE": decision(
                    "keep", "full rationale\nwith | pipe and " + "r" * 200
                ),
                "status:STATUS_TWO": decision(
                    "adjust", "second complete rationale"
                ),
            },
        )
        self.assertNotIn("…", clean_text)
        self.assertIn(r"one\nwith ", clean_text)
        self.assertIn("&#124; pipe", clean_text)
        self.assertIn("x" * 200, clean_text)
        self.assertIn("r" * 200, clean_text)

        def mutate_metadata(text, field, value):
            lines = text.splitlines()
            marker = lines.index(MODULE.STRICT_REVIEW_BEGIN)
            metadata = json.loads(lines[marker + 1])
            metadata[field] = value
            lines[marker + 1] = json.dumps(
                metadata, sort_keys=True, separators=(",", ":")
            )
            return "\n".join(lines)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.md"
            path.write_text(clean_text, encoding="utf-8")
            self.assertTrue(MODULE.review_coverage(payload, review_input(path))[
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
                    self.assertFalse(MODULE.review_coverage(
                        payload, review_input(path)
                    )[
                        "coverage_equal"
                    ])

            summary_lines = clean_text.splitlines()
            summary_index = summary_lines.index(
                MODULE.REVIEW_ARTIFACT_BEGIN
            ) + 1
            clean_summary = json.loads(summary_lines[summary_index])
            for field in clean_summary:
                with self.subTest(summary_field=field):
                    mutated_summary = dict(clean_summary)
                    mutated_summary[field] = "mutated"
                    changed = list(summary_lines)
                    changed[summary_index] = json.dumps(
                        mutated_summary,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    path.write_text(
                        "\n".join(changed) + "\n",
                        encoding="utf-8",
                    )
                    result = MODULE.review_coverage(
                        payload, review_input(path)
                    )
                    self.assertFalse(result["artifact_exact"])
                    self.assertFalse(result["coverage_equal"])

            lines = clean_text.splitlines()
            marker = lines.index(MODULE.STRICT_REVIEW_BEGIN)
            first_index = marker + 3
            second_index = marker + 4
            first = json.loads(lines[first_index])
            second = json.loads(lines[second_index])
            mutations = {
                "fact": [
                    *lines[:first_index],
                    json.dumps(
                        dict(first, fact_sha256="0" * 64),
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    *lines[first_index + 1:],
                ],
                "pending": [
                    *lines[:first_index],
                    json.dumps(
                        dict(first, terminal_conclusion="pending"),
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    *lines[first_index + 1:],
                ],
                "empty-rationale": [
                    *lines[:first_index],
                    json.dumps(
                        dict(first, reviewer_rationale=""),
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    *lines[first_index + 1:],
                ],
                "production-facts": [
                    *lines[:first_index],
                    json.dumps(
                        dict(
                            first,
                            production_facts=dict(
                                first["production_facts"], fact="tampered"
                            ),
                        ),
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    *lines[first_index + 1:],
                ],
                "duplicate": [
                    *lines[:second_index],
                    lines[first_index],
                    *lines[second_index:],
                ],
                "missing": [
                    *lines[:first_index],
                    *lines[first_index + 1:],
                ],
                "extra": [
                    *lines[:second_index + 1],
                    json.dumps(
                        dict(second, identity="status:STATUS_EXTRA"),
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    *lines[second_index + 1:],
                ],
                "reordered": [
                    *lines[:first_index],
                    lines[second_index],
                    lines[first_index],
                    *lines[second_index + 1:],
                ],
                "external-prose": [
                    *lines,
                    "unbound current/final assertion",
                ],
                "missing-artifact-marker": [
                    line for line in lines
                    if line != MODULE.REVIEW_ARTIFACT_BEGIN
                ],
                "duplicate-artifact-marker": [
                    *lines[:lines.index(MODULE.REVIEW_ARTIFACT_BEGIN)],
                    MODULE.REVIEW_ARTIFACT_BEGIN,
                    MODULE.REVIEW_ARTIFACT_BEGIN,
                    *lines[lines.index(MODULE.REVIEW_ARTIFACT_BEGIN) + 1:],
                ],
            }
            for name, mutated in mutations.items():
                with self.subTest(mutation=name):
                    path.write_text("\n".join(mutated) + "\n", encoding="utf-8")
                    self.assertFalse(MODULE.review_coverage(
                        payload, review_input(path)
                    )[
                        "coverage_equal"
                    ])
            old_v1 = (
                clean_text
                .replace("STRICT REVIEW EVIDENCE v2",
                         "STRICT REVIEW EVIDENCE v1")
                .replace("CHARACTER REVIEW ARTIFACT v2",
                         "CHARACTER REVIEW ARTIFACT v1")
            )
            path.write_text(old_v1, encoding="utf-8")
            with self.assertRaisesRegex(
                RuntimeError, "strict review evidence block is missing"
            ):
                MODULE.review_coverage(payload, review_input(path))

    def test_write_strict_review_rejects_duplicate_v2_cards_without_writing(self):
        payload = {
            "glossary_sha256": "a" * 64,
            "inventory_sha256": "b" * 64,
            "count": 1,
            "rows": [{
                "identity": "status:STATUS_TEST",
                "category": "status",
                "lifecycle": "current",
                "english_source_name": "Test",
                "current_chinese_name": "测试",
            }],
        }
        lines = MODULE.render_review_results(
            payload,
            {
                "status:STATUS_TEST": decision(
                    "keep", "complete status rationale"
                ),
            },
        ).splitlines()
        strict_end = lines.index(MODULE.STRICT_REVIEW_END)
        lines.insert(strict_end - 1, lines[strict_end - 2])
        original = ("\n".join(lines) + "\n").encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.md"
            path.write_bytes(original)
            with self.assertRaisesRegex(
                RuntimeError,
                "duplicate strict review evidence-card identities: "
                "status:STATUS_TEST",
            ):
                MODULE.write_strict_review_evidence(payload, path)
            self.assertEqual(original, path.read_bytes())

    def test_legacy_migration_preserves_rationale_and_refuses_missing_identity(self):
        payload = {
            "glossary_sha256": "a" * 64,
            "inventory_sha256": "b" * 64,
            "count": 2,
            "rows": [
                {
                    "identity": "status:STATUS_EXISTING",
                    "category": "status",
                    "lifecycle": "current",
                    "english_source_name": "Existing",
                    "current_chinese_name": "现有",
                },
                {
                    "identity": "status:STATUS_NEW",
                    "category": "status",
                    "lifecycle": "current",
                    "english_source_name": "New",
                    "current_chinese_name": "新增",
                },
            ],
        }
        legacy = (
            "| 身份 | 生命周期 | 名称 | 生产事实 | 终态结论 |\n"
            "|---|---|---|---|---|\n"
            "| `status:STATUS_EXISTING` | current | Existing → 现有 | "
            "full fact | 修订：reviewer-authored complete rationale |\n"
        )
        decisions = MODULE.legacy_review_decisions(legacy)
        self.assertEqual(
            decision("adjust", "reviewer-authored complete rationale"),
            decisions["status:STATUS_EXISTING"],
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.md"
            path.write_text(legacy, encoding="utf-8")
            before = path.read_text(encoding="utf-8")
            with self.assertRaisesRegex(
                RuntimeError, "status:STATUS_NEW"
            ):
                MODULE.write_strict_review_evidence(payload, path)
            self.assertEqual(before, path.read_text(encoding="utf-8"))
            old_hash_only = (
                "<!-- BEGIN STRICT REVIEW EVIDENCE v1 -->\n"
                "{}\n```jsonl\n"
                '{"fact_sha256":"'
                + "0" * 64
                + '","identity":"status:STATUS_EXISTING",'
                '"terminal_conclusion":"keep"}\n'
                "```\n<!-- END STRICT REVIEW EVIDENCE v1 -->\n"
            )
            path.write_text(old_hash_only, encoding="utf-8")
            with self.assertRaisesRegex(
                RuntimeError, "missing explicit reviewer decisions"
            ):
                MODULE.write_strict_review_evidence(payload, path)
            self.assertEqual(
                old_hash_only, path.read_text(encoding="utf-8")
            )

        decisions["status:STATUS_NEW"] = decision(
            "keep", "explicit reviewer decision for the new identity"
        )
        rendered = MODULE.render_review_results(payload, decisions)
        self.assertIn("reviewer-authored complete rationale", rendered)
        self.assertIn(
            "explicit reviewer decision for the new identity", rendered
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
