#!/usr/bin/env python3

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
SCRIPT = TEST_DIR.parent / "audit_god_inventory.py"
SPEC = importlib.util.spec_from_file_location("audit_god_inventory", SCRIPT)
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
        self.assertEqual(0, len(findings["zh_only_ability_keys"]))
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
            "glossary_sha256": "a" * 64,
            "inventory_sha256": "b" * 64,
            "count": 2,
            "parents": [
                {
                    "identity": "GOD_TEST",
                    "lifecycle": "current",
                    "english_name": "Test",
                    "current_chinese_name": "测试神",
                },
                {
                    "identity": "GOD_OTHER",
                    "lifecycle": "current",
                    "english_name": "Other",
                    "current_chinese_name": "另一神",
                },
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.md"
            path.write_text(
                MODULE.render_review_results(
                    payload,
                    {
                        "GOD_TEST": decision("keep", "complete rationale"),
                        "GOD_OTHER": decision(
                            "adjust", "other complete rationale"
                        ),
                    },
                ),
                encoding="utf-8",
            )
            self.assertTrue(MODULE.review_coverage(payload, review_input(path))[
                "coverage_equal"
            ])
            lines = path.read_text(encoding="utf-8").splitlines()
            marker = lines.index(MODULE.STRICT_REVIEW_BEGIN)
            first = marker + 3
            second = marker + 4
            path.write_text("\n".join([
                *lines[:first], lines[second], lines[second],
                *lines[second + 1:]
            ]) + "\n", encoding="utf-8")
            coverage = MODULE.review_coverage(payload, review_input(path))
            self.assertFalse(coverage["coverage_equal"])
            self.assertEqual(["GOD_TEST"], coverage[
                "duplicate_evidence_cards"
            ])
            self.assertEqual(["GOD_OTHER"], coverage[
                "missing_evidence_cards"
            ])

    def test_strict_review_rejects_stale_bindings_fact_pending_and_extra(self):
        payload = {
            "glossary_sha256": "a" * 64,
            "inventory_sha256": "b" * 64,
            "count": 2,
            "parents": [
                {
                    "identity": "GOD_OTHER",
                    "lifecycle": "current",
                    "english_name": "Other\nwith | pipe",
                    "current_chinese_name": "另一神\n含 | 管道",
                    "fact": "o" * 200,
                },
                {
                    "identity": "GOD_TEST",
                    "lifecycle": "current",
                    "english_name": "Test",
                    "current_chinese_name": "测试神",
                    "fact": "test",
                },
            ],
        }
        clean = MODULE.render_review_results(
            payload,
            {
                "GOD_OTHER": decision(
                    "keep", "full rationale\nwith | pipe and " + "r" * 200
                ),
                "GOD_TEST": decision("adjust", "test rationale"),
            },
        )
        self.assertNotIn("…", clean)
        self.assertIn(r"Other\nwith ", clean)
        self.assertIn("&#124; pipe", clean)
        self.assertIn("o" * 200, clean)
        self.assertIn("r" * 200, clean)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.md"
            path.write_text(clean, encoding="utf-8")
            self.assertTrue(MODULE.review_coverage(payload, review_input(path))[
                "coverage_equal"
            ])
            lines = clean.splitlines()
            marker = lines.index(MODULE.STRICT_REVIEW_BEGIN)
            metadata_index = marker + 1
            first_index = marker + 3
            second_index = marker + 4
            mutations = {}
            for field, value in (
                ("baseline", "0" * 40),
                ("glossary_sha256", "0" * 64),
                ("inventory_sha256", "1" * 64),
                ("identity_count", 3),
            ):
                changed = list(lines)
                metadata = json.loads(changed[metadata_index])
                metadata[field] = value
                changed[metadata_index] = json.dumps(
                    metadata, sort_keys=True, separators=(",", ":")
                )
                mutations[field] = changed
            first = json.loads(lines[first_index])
            mutations.update({
                "fact": [
                    *lines[:first_index],
                    json.dumps(
                        dict(first, fact_sha256="0" * 64),
                        ensure_ascii=False,
                        sort_keys=True, separators=(",", ":"),
                    ),
                    *lines[first_index + 1:],
                ],
                "pending": [
                    *lines[:first_index],
                    json.dumps(
                        dict(first, terminal_conclusion="pending"),
                        ensure_ascii=False,
                        sort_keys=True, separators=(",", ":"),
                    ),
                    *lines[first_index + 1:],
                ],
                "empty-rationale": [
                    *lines[:first_index],
                    json.dumps(
                        dict(first, reviewer_rationale=""),
                        ensure_ascii=False,
                        sort_keys=True, separators=(",", ":"),
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
                "missing": [
                    *lines[:first_index],
                    *lines[first_index + 1:],
                ],
                "extra": [
                    *lines[:second_index + 1],
                    json.dumps(
                        dict(first, identity="GOD_EXTRA"),
                        ensure_ascii=False,
                        sort_keys=True, separators=(",", ":"),
                    ),
                    *lines[second_index + 1:],
                ],
                "reordered": [
                    *lines[:first_index],
                    lines[second_index],
                    lines[first_index],
                    *lines[second_index + 1:],
                ],
                "restored-old-six-section": [
                    *lines,
                    "## 旧六项吐息",
                    "结论：保留旧 owner/re-entry 条件",
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
            })
            summary_index = lines.index(MODULE.REVIEW_ARTIFACT_BEGIN) + 1
            summary = json.loads(lines[summary_index])
            for field in summary:
                changed = list(lines)
                mutated = dict(summary)
                mutated[field] = "mutated"
                changed[summary_index] = json.dumps(
                    mutated,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                mutations[f"summary-{field}"] = changed
            for name, changed in mutations.items():
                with self.subTest(mutation=name):
                    path.write_text(
                        "\n".join(changed) + "\n", encoding="utf-8"
                    )
                    self.assertFalse(MODULE.review_coverage(
                        payload, review_input(path)
                    )[
                        "coverage_equal"
                    ])
            old_v1 = (
                clean
                .replace("STRICT REVIEW EVIDENCE v2",
                         "STRICT REVIEW EVIDENCE v1")
                .replace("GOD REVIEW ARTIFACT v2",
                         "GOD REVIEW ARTIFACT v1")
            )
            path.write_text(old_v1, encoding="utf-8")
            with self.assertRaisesRegex(
                RuntimeError, "strict review evidence block is missing"
            ):
                MODULE.review_coverage(payload, review_input(path))

    def test_cli_accepts_exact_artifact_and_rejects_external_prose(self):
        payload = MODULE.build_inventory()
        conclusions = {
            row["identity"]: decision(
                "keep", f"explicit reviewer rationale for {row['identity']}"
            )
            for row in payload["parents"]
        }
        with tempfile.TemporaryDirectory(
            dir=MODULE.ROOT / ".claude"
        ) as directory:
            path = Path(directory) / "god-review.md"
            path.write_text(
                MODULE.render_review_results(payload, conclusions),
                encoding="utf-8",
            )

            def validate():
                return subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT),
                        "--review-results",
                        str(path),
                    ],
                    cwd=MODULE.ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )

            clean = validate()
            self.assertEqual(0, clean.returncode, clean.stderr)
            path.write_text(
                path.read_text(encoding="utf-8")
                + "\n## restored old six breath conclusions\n",
                encoding="utf-8",
            )
            broken = validate()
            self.assertEqual(1, broken.returncode, broken.stderr)

    def test_write_strict_review_rejects_duplicate_v2_cards_without_writing(self):
        payload = {
            "glossary_sha256": "a" * 64,
            "inventory_sha256": "b" * 64,
            "count": 1,
            "parents": [{
                "identity": "GOD_TEST",
                "lifecycle": "current",
                "english_name": "Test",
                "current_chinese_name": "测试神",
            }],
        }
        lines = MODULE.render_review_results(
            payload,
            {
                "GOD_TEST": decision(
                    "keep", "complete god rationale"
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
                "duplicate strict review evidence-card identities: GOD_TEST",
            ):
                MODULE.write_strict_review_evidence(payload, path)
            self.assertEqual(original, path.read_bytes())

    def test_legacy_migration_preserves_full_rationale_and_fails_missing(self):
        payload = {
            "glossary_sha256": "a" * 64,
            "inventory_sha256": "b" * 64,
            "count": 2,
            "parents": [
                {
                    "identity": "GOD_TEST",
                    "lifecycle": "current",
                    "english_name": "Test",
                    "current_chinese_name": "测试神",
                },
                {
                    "identity": "GOD_NEW",
                    "lifecycle": "current",
                    "english_name": "New",
                    "current_chinese_name": "新神",
                },
            ],
        }
        legacy = (
            "| 父身份 | 生命周期 | 英→中短名/长名 | 子身份与资产证据 | "
            "唯一终态结论 |\n"
            "|---|---|---|---|---|\n"
            "| `GOD_TEST` | 现役 | Test→测试神 | full facts | "
            "修订：reviewer-authored full rationale。 |\n"
        )
        decisions = MODULE.legacy_review_decisions(legacy)
        self.assertEqual(
            decision("adjust", "reviewer-authored full rationale。"),
            decisions["GOD_TEST"],
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.md"
            path.write_text(legacy, encoding="utf-8")
            before = path.read_text(encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "GOD_NEW"):
                MODULE.write_strict_review_evidence(payload, path)
            self.assertEqual(before, path.read_text(encoding="utf-8"))
            old_hash_only = (
                "<!-- BEGIN STRICT REVIEW EVIDENCE v1 -->\n"
                "{}\n```jsonl\n"
                '{"fact_sha256":"'
                + "0" * 64
                + '","identity":"GOD_TEST",'
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

        decisions["GOD_NEW"] = decision(
            "keep", "explicit reviewer decision for new god"
        )
        rendered = MODULE.render_review_results(payload, decisions)
        self.assertIn("reviewer-authored full rationale", rendered)
        self.assertIn("explicit reviewer decision for new god", rendered)


if __name__ == "__main__":
    unittest.main()
