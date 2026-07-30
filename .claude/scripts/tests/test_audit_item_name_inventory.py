#!/usr/bin/env python3

import contextlib
import copy
import hashlib
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

        spaced_brand = item_name.replace(
            'return C_("weapon brand adjective",',
            'return C_ ("weapon brand adjective",',
            1,
        )
        self.assertEqual(
            "weapon brand adjective|draining",
            MODULE.contextual_brand_forms(spaced_brand)[
                "SPWPN_DRAINING"
            ]["adj"]["key"],
        )

        spaced_book = item_name.replace(
            'C_("book full name", "Necromancy")',
            'C_ ("book full name", "Necromancy")',
            1,
        )
        self.assertEqual(
            "book full name|Necromancy",
            MODULE.contextual_book_names(spaced_book)[
                "BOOK_NECROMANCY"
            ]["key"],
        )

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
        self.assertEqual(390, payload["count"])
        self.assertEqual(
            "40fe2a9be419868de3ffd8ece736861b81823046654fd4710da62ec5fe2b81f4",
            payload["inventory_sha256"],
        )
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

    def test_issue29_v2_freezes_every_finite_production_boundary(self):
        payload, internal_rows = MODULE.build_extended_inventory()
        self.assertEqual(
            "dcss-item-extended-review-inventory-v2", payload["schema"]
        )
        self.assertEqual(390, payload["ordinary_v1"]["count"])
        self.assertEqual(
            {
                "unrand": 142,
                "unident": 7,
                "appearance": 186,
                "special": 23,
                "gizmo": 539,
                "item-description": 307,
                "randart-component": 2440,
                "randart-grammar": 115,
            },
            payload["category_counts"],
        )
        self.assertEqual(payload["count"], len(payload["rows"]))
        self.assertEqual(
            payload["count"],
            len({row["identity"] for row in payload["rows"]}),
        )
        self.assertFalse(payload["duplicates"])
        self.assertEqual(payload["count"], len(internal_rows))
        self.assertEqual(
            {
                "grammar_keys": 115,
                "physical_variant_identities": 2440,
                "raw_nonempty_grammar_lines": 2734,
                "explicit_weight_marker_lines": 293,
                "continuation_lines": 1,
                "weight_mass": 27304,
            },
            payload["scope"]["randart_component_metrics"]["totals"],
        )

    def test_paired_components_reject_minimal_key_count_token_mutations(self):
        def write(path, entries):
            chunks = []
            for key, values in entries:
                chunks.append("%%%%\n" + key + "\n\n"
                              + "\n\n".join(values) + "\n")
            path.write_text("".join(chunks), encoding="utf-8")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            en = root / "en.txt"
            zh = root / "zh.txt"
            valid = [("key", ["plain", "@child@tail"]),
                     ("child", ["nested"])]
            write(en, valid)
            write(zh, [("key", ["普通", "@child@尾"]),
                       ("child", ["嵌套"])])
            self.assertEqual(
                3, len(MODULE.paired_component_rows(
                    en, zh, "fixture"
                ))
            )

            write(zh, [("other", ["普通", "@child@尾"]),
                       ("child", ["嵌套"])])
            with self.assertRaisesRegex(RuntimeError, "key mismatch"):
                MODULE.paired_component_rows(en, zh, "fixture")

            write(zh, [("key", ["普通"]), ("child", ["嵌套"])])
            with self.assertRaisesRegex(RuntimeError, "physical count"):
                MODULE.paired_component_rows(en, zh, "fixture")

            write(zh, [("key", ["普通", "@other@尾"]),
                       ("child", ["嵌套"])])
            with self.assertRaisesRegex(RuntimeError, "recursive token"):
                MODULE.paired_component_rows(en, zh, "fixture")

            write(en, [("key", ["value %1$s"]), ("child", ["nested"])])
            write(zh, [("key", ["值 %2$s"]), ("child", ["嵌套"])])
            with self.assertRaisesRegex(RuntimeError, "placeholder"):
                MODULE.paired_component_rows(en, zh, "fixture")

            write(en, [("key", ["w:3\nweighted"]),
                       ("child", ["nested"])])
            write(zh, [("key", ["w:4\n加权"]),
                       ("child", ["嵌套"])])
            with self.assertRaisesRegex(RuntimeError, "weight mismatch"):
                MODULE.paired_component_rows(en, zh, "fixture")

    def test_weighted_metrics_distinguish_variants_from_raw_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            path.write_text(
                "%%%%\nkey\n\nplain\n\nw:3\nweighted\n",
                encoding="utf-8",
            )
            expected = {
                "physical_variant_identities": 2,
                "raw_nonempty_grammar_lines": 3,
                "explicit_weight_marker_lines": 1,
                "continuation_lines": 0,
                "weight_mass": 13,
            }
            actual = MODULE.weighted_grammar_metrics(
                MODULE.textdb_rows(path)
            )
            MODULE.require_weighted_metrics(actual, expected, "fixture")

            path.write_text(
                "%%%%\nkey\n\nplain\ncontinuation\n\nw:3\nweighted\n",
                encoding="utf-8",
            )
            mutated = MODULE.weighted_grammar_metrics(
                MODULE.textdb_rows(path)
            )
            self.assertEqual(
                expected["physical_variant_identities"],
                mutated["physical_variant_identities"],
            )
            with self.assertRaisesRegex(RuntimeError, "metric drift"):
                MODULE.require_weighted_metrics(
                    mutated, expected, "fixture"
                )

    def test_review_base_survives_a_clean_committed_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "fixture@example.invalid"],
                cwd=root, check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Fixture"],
                cwd=root, check=True,
            )
            tracked = root / "input.txt"
            tracked.write_text("before\n", encoding="utf-8")
            subprocess.run(["git", "add", "input.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "base"], cwd=root, check=True
            )
            base = MODULE.resolve_commit("HEAD", root)
            tracked.write_text("after\n", encoding="utf-8")
            subprocess.run(["git", "add", "input.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "candidate"], cwd=root, check=True
            )
            self.assertFalse(subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=root, text=True
            ))
            self.assertEqual(
                "before\n",
                MODULE.git_revision_text(tracked, base, root),
            )
            self.assertEqual("after\n", tracked.read_text(encoding="utf-8"))
            with self.assertRaisesRegex(RuntimeError, "invalid review base"):
                MODULE.resolve_commit("missing-review-base", root)

    def test_review_coverage_rejects_each_minimal_mutation(self):
        def card(identity, conclusion):
            return {
                "identity": identity,
                "lifecycle": "current",
                "english_source": f"English {identity}",
                "pre_review_chinese": f"旧{identity}",
                "current_chinese": f"新{identity}",
                "adopted_english": f"English {identity}",
                "adopted_chinese": f"新{identity}",
                "producer": "fixture producer",
                "consumer": "fixture consumer",
                "metadata": {"category": "fixture"},
                "input": "fixture.txt",
                "source_files": [{
                    "path": "fixture.txt",
                    "review_base_sha256": "0" * 64,
                    "current_sha256": "1" * 64,
                }],
                "terminal_conclusion": conclusion,
                "semantic_reason": f"{conclusion}: fixture reason",
                "reentry_trigger": "Re-review on fixture change.",
            }

        valid = [card("a", "keep"), card("b", "adjust")]
        inventory = copy.deepcopy(valid)
        self.assertFalse(any(
            MODULE.review_violations(inventory, valid).values()
        ))

        duplicate = valid + [dict(valid[0])]
        self.assertEqual(
            ["a"],
            MODULE.review_violations(inventory, duplicate)[
                "review_duplicates"
            ],
        )
        self.assertEqual(
            ["b"],
            MODULE.review_violations(inventory, valid[:1])[
                "inventory_minus_review"
            ],
        )
        extra = valid + [card("c", "keep")]
        self.assertEqual(
            ["c"],
            MODULE.review_violations(inventory, extra)[
                "review_minus_inventory"
            ],
        )
        invalid = [
            dict(valid[0], terminal_conclusion="pending"), valid[1]
        ]
        self.assertEqual(
            ["a"],
            MODULE.review_violations(inventory, invalid)[
                "invalid_terminal_conclusions"
            ],
        )
        deferred = [dict(
            valid[0],
            terminal_conclusion="defer implementation",
            semantic_reason="not applicable",
            reentry_trigger="not applicable",
        ), valid[1]]
        self.assertEqual(
            ["a"],
            MODULE.review_violations(inventory, deferred)[
                "invalid_deferrals"
            ],
        )

        for field, value in [
            ("adopted_english", "changed English"),
            ("adopted_chinese", "改坏"),
        ]:
            mutated = copy.deepcopy(valid)
            mutated[0][field] = value
            self.assertEqual(
                ["a"],
                MODULE.review_violations(inventory, mutated)[
                    "mismatched_evidence_cards"
                ],
            )

        mutated_sha = copy.deepcopy(valid)
        mutated_sha[0]["source_files"][0]["current_sha256"] = "2" * 64
        self.assertEqual(
            ["a"],
            MODULE.review_violations(inventory, mutated_sha)[
                "mismatched_evidence_cards"
            ],
        )

        missing = copy.deepcopy(valid)
        del missing[0]["adopted_chinese"]
        violations = MODULE.review_violations(inventory, missing)
        self.assertEqual(["a:adopted_chinese"],
                         violations["missing_required_fields"])
        self.assertEqual(["a"], violations["mismatched_evidence_cards"])

    def test_issue29_cli_review_results_has_exact_bidirectional_coverage(self):
        with tempfile.TemporaryDirectory(dir=MODULE.ROOT / ".claude") as directory:
            root = Path(directory)
            inventory = root / "inventory.json"
            results = root / "results.md"
            generated = subprocess.run(
                [
                    sys.executable, str(SCRIPT), "--scope", "issue29-v2",
                    "--output", str(inventory),
                    "--write-review-results", str(results),
                ],
                cwd=MODULE.ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, generated.returncode, generated.stderr)
            validated = subprocess.run(
                [
                    sys.executable, str(SCRIPT), "--scope", "issue29-v2",
                    "--output", str(inventory),
                    "--review-results", str(results),
                ],
                cwd=MODULE.ROOT, text=True, capture_output=True, check=False,
            )
            payload = json.loads(inventory.read_text(encoding="utf-8"))
            result_text = results.read_text(encoding="utf-8")
            parsed_results = MODULE.parse_review_results(review_input(results))
        self.assertEqual(0, validated.returncode, validated.stderr)
        self.assertFalse(any(payload["review_violations"].values()))
        self.assertEqual(
            payload["rows"], parsed_results
        )
        self.assertIn(payload["baseline"], result_text)
        self.assertNotIn(payload["candidate_head"], result_text)
        for report in MODULE.DEVELOPMENT_REPORTS:
            self.assertIn(report["path"], result_text)
            self.assertIn(f"status={report['status']}", result_text)
            self.assertIn(
                f"blocking_failures={report['blocking_failures']}",
                result_text,
            )
            self.assertIn(report["note"], result_text)
        self.assertIn(
            MODULE.DEVELOPMENT_NON_OVERWRITE_STATEMENT, result_text
        )
        for evidence in MODULE.ITEM_PRODUCER_CONSUMER_EVIDENCE:
            self.assertIn(evidence, result_text)

    def test_issue29_review_header_rejects_each_minimal_mutation(self):
        inventory = {
            "inventory_sha256": "1" * 64,
            "glossary_sha256": "2" * 64,
            "baseline": "3" * 40,
            "count": 2,
        }
        labels = {
            "inventory_sha256": "Inventory SHA-256",
            "glossary_sha256": "Glossary SHA-256",
            "baseline": "Review base",
            "count": "Inventory rows",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.md"

            def write(values):
                path.write_text("\n".join(
                    f"- {labels[field]}: `{values[field]}`"
                    for field in labels
                ) + "\n```jsonl\n```\n", encoding="utf-8")

            write(inventory)
            clean = MODULE.review_violations(
                [], [], inventory, MODULE.parse_review_header(review_input(path))
            )
            self.assertFalse(clean["header_mismatches"])
            for field, value in (
                ("inventory_sha256", "4" * 64),
                ("glossary_sha256", "5" * 64),
                ("baseline", "6" * 40),
                ("count", 3),
            ):
                with self.subTest(field=field):
                    changed = dict(inventory, **{field: value})
                    write(changed)
                    violations = MODULE.review_violations(
                        [], [], inventory,
                        MODULE.parse_review_header(review_input(path))
                    )
                    self.assertEqual(
                        [field], violations["header_mismatches"]
                    )

    def test_issue29_full_artifact_rejects_summary_marker_and_prose_mutations(self):
        inventory = {
            "inventory_sha256": "1" * 64,
            "glossary_sha256": "2" * 64,
            "baseline": "3" * 40,
            "count": 0,
            "development_reports": copy.deepcopy(
                MODULE.DEVELOPMENT_REPORTS
            ),
            "scope": {
                "randart_component_metrics": {
                    "totals": {
                        "physical_variant_identities": 1,
                        "raw_nonempty_grammar_lines": 2,
                        "explicit_weight_marker_lines": 0,
                        "continuation_lines": 1,
                        "weight_mass": 10,
                    },
                },
            },
        }
        clean = MODULE.render_review_results(inventory, [])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.md"

            def violations(text):
                path.write_text(text, encoding="utf-8")
                loaded = review_input(path)
                return MODULE.review_violations(
                    [],
                    MODULE.parse_review_results(loaded),
                    inventory,
                    MODULE.parse_review_header(loaded),
                    loaded,
                )

            self.assertFalse(any(violations(clean).values()))
            lines = clean.splitlines()
            summary_index = lines.index(MODULE.REVIEW_ARTIFACT_BEGIN) + 1
            summary = json.loads(lines[summary_index])
            mutations = {
                "external-prose": clean + "unbound final assertion\n",
                "missing-marker": clean.replace(
                    MODULE.REVIEW_ARTIFACT_BEGIN, "", 1
                ),
                "duplicate-marker": clean.replace(
                    MODULE.REVIEW_ARTIFACT_BEGIN,
                    MODULE.REVIEW_ARTIFACT_BEGIN + "\n"
                    + MODULE.REVIEW_ARTIFACT_BEGIN,
                    1,
                ),
                "old-v1-marker": clean.replace(
                    "ITEM REVIEW ARTIFACT v2",
                    "ITEM REVIEW ARTIFACT v1",
                ),
                "missing-producer-consumer": clean.replace(
                    f"- {MODULE.ITEM_PRODUCER_CONSUMER_EVIDENCE[0]}\n",
                    "",
                    1,
                ),
                "missing-development-report": clean.replace(
                    next(
                        line + "\n" for line in clean.splitlines()
                        if MODULE.DEVELOPMENT_REPORTS[0]["path"] in line
                    ),
                    "",
                    1,
                ),
                "tampered-development-status": clean.replace(
                    "status=fail; blocking_failures=1",
                    "status=pass; blocking_failures=0",
                    1,
                ),
                "missing-non-overwrite-statement": clean.replace(
                    MODULE.DEVELOPMENT_NON_OVERWRITE_STATEMENT + "\n",
                    "",
                    1,
                ),
            }
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
                mutations[f"summary-{field}"] = "\n".join(changed) + "\n"
            for name, text in mutations.items():
                with self.subTest(mutation=name):
                    self.assertTrue(
                        violations(text)["artifact_mismatch"]
                    )

        for name, reports in {
            "missing": MODULE.DEVELOPMENT_REPORTS[:-1],
            "tampered": [
                dict(MODULE.DEVELOPMENT_REPORTS[0], status="pass"),
                *MODULE.DEVELOPMENT_REPORTS[1:],
            ],
            "reordered": [
                MODULE.DEVELOPMENT_REPORTS[1],
                MODULE.DEVELOPMENT_REPORTS[0],
                *MODULE.DEVELOPMENT_REPORTS[2:],
            ],
        }.items():
            with self.subTest(inventory_history=name):
                changed = copy.deepcopy(inventory)
                changed["development_reports"] = copy.deepcopy(reports)
                with self.assertRaisesRegex(
                    RuntimeError, "four-report history"
                ):
                    MODULE.render_review_results(changed, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
