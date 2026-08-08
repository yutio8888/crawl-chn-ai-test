#!/usr/bin/env python3

import contextlib
import copy
from collections import Counter
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
import i18n_shared as SHARED
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


_QUALITY_M1_FIXTURE = None


def quality_m1_fixture():
    global _QUALITY_M1_FIXTURE
    if _QUALITY_M1_FIXTURE is None:
        payload, _internal_rows = MODULE.build_extended_inventory()
        payload["review_input"] = {"input_sha256": "a" * 64}
        payload["review_violations"] = {}
        files = MODULE.build_quality_m1_files(
            payload,
            b"fixture prompt\n",
            b"fixture context\n",
            "b" * 64,
        )
        _QUALITY_M1_FIXTURE = (payload, files)
    payload, files = _QUALITY_M1_FIXTURE
    return copy.deepcopy(payload), dict(files)


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
            "63f0eb9c721654284401130123b6149af5cb2a46cbe2a2fe0b74979223b113d2",
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
            MODULE._REVISION_SNAPSHOTS.clear()
            cat_file_calls = []
            original_git = SHARED._run_git_bytes

            def recording_git(repo, *args):
                if args[:2] == ("cat-file", "blob"):
                    cat_file_calls.append(args[2])
                return original_git(repo, *args)

            with mock.patch.object(
                SHARED, "_run_git_bytes", side_effect=recording_git
            ):
                self.assertEqual(
                    "before\n",
                    MODULE.git_revision_text(tracked, base, root),
                )
                self.assertEqual(
                    "before\n",
                    MODULE.git_revision_text(tracked, base, root),
                )
            self.assertEqual(1, len(cat_file_calls))
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
            payload["baseline"],
            payload["review_base_snapshot"]["audit_commit"],
        )
        self.assertTrue(
            payload["review_base_snapshot"]["input_manifest"]["inputs"]
        )
        self.assertIn(
            payload["review_input"]["logical_path"],
            {
                item["path"]
                for item in payload[
                    "audit_snapshot"
                ]["input_manifest"]["inputs"]
            },
        )
        self.assertNotIn(
            str(MODULE.ROOT),
            json.dumps(
                payload["review_base_snapshot"],
                ensure_ascii=False,
                sort_keys=True,
            ),
        )
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

    def test_quality_m1_reproduces_m0_selection_and_is_byte_deterministic(self):
        payload, files = quality_m1_fixture()
        repeated = MODULE.build_quality_m1_files(
            payload,
            b"fixture prompt\n",
            b"fixture context\n",
            "b" * 64,
        )
        self.assertEqual(files, repeated)
        packet = json.loads(files["blind-packet.json"])
        self.assertEqual(
            [
                "item-description:staff of necromancy",
                "item-description:sack of spiders",
                "item-description:condenser vane",
                "item-description:staff of air",
                "item-description:whip",
                "item-description:staff of alchemy",
                "item-description:wand of mindburst",
                "item-description:horn of geryon",
                "item-description:gell's gravitambourine",
                "item-description:book of winter",
                "item-description:potion of haste",
                "item-description:granite talisman",
                "item-description:book of scorching",
                "item-description:staff of fire",
                "item-description:phantom mirror",
                "item-description:book of unlife",
            ],
            [item["identity"] for item in packet["items"]],
        )
        self.assertEqual(
            [f"M0-{index:03d}" for index in range(1, 17)],
            [item["case_id"] for item in packet["items"]],
        )
        self.assertEqual(
            16,
            len({item["identity"] for item in packet["items"]}),
        )
        truth = json.loads(files["truth.json"])
        counts = Counter(
            item["historical_expected_severity"]
            for item in truth["items"]
        )
        self.assertEqual(
            {"needs_fix": 6, "unadjudicated": 10}, dict(counts)
        )
        self.assertEqual(
            6,
            sum(
                "expected_correction_chinese" in item
                for item in truth["items"]
            ),
        )
        commitment = json.loads(files["commitment.json"])
        self.assertEqual(
            MODULE.quality_m1_digest(files["truth.json"]),
            commitment["truth_sha256"],
        )
        manifest = json.loads(files["manifest.json"])
        self.assertNotIn("truth.json", manifest["evaluator_files"])
        self.assertNotIn("population.json", manifest["evaluator_files"])
        self.assertFalse(MODULE.quality_m1_forbidden_fields(packet))
        MODULE.validate_quality_m1_files(files)

    def test_quality_m1_population_rejects_minimal_boundary_mutations(self):
        payload, _files = quality_m1_fixture()
        description = next(
            row for row in payload["rows"]
            if row["identity"].startswith("item-description:")
        )
        mutations = {}

        duplicate = copy.deepcopy(payload)
        duplicate["rows"].append(copy.deepcopy(description))
        duplicate["category_counts"]["item-description"] += 1
        mutations["identities are not unique"] = duplicate

        changed_keep = copy.deepcopy(payload)
        keep = next(
            row for row in changed_keep["rows"]
            if row["identity"].startswith("item-description:")
            and row["terminal_conclusion"] == "keep"
        )
        keep["pre_review_chinese"] += "变更"
        mutations["conclusion/revision mismatch"] = changed_keep

        absolute_path = copy.deepcopy(payload)
        row = next(
            row for row in absolute_path["rows"]
            if row["identity"].startswith("item-description:")
        )
        row["source_files"][0]["path"] = "/tmp/input.txt"
        mutations["canonical relative path"] = absolute_path

        violations = copy.deepcopy(payload)
        violations["review_violations"] = {"review_duplicates": ["x"]}
        mutations["violation-free review artifact"] = violations

        for message, mutated in mutations.items():
            with self.subTest(message=message):
                with self.assertRaisesRegex(RuntimeError, message):
                    MODULE.quality_m1_population(mutated)

    def test_quality_m1_validator_rejects_shard_truth_and_label_mutations(self):
        _payload, original = quality_m1_fixture()

        def refresh_manifest(files, name):
            manifest = json.loads(files["manifest.json"])
            artifact = next(
                item for item in manifest["artifacts"]
                if item["path"] == name
            )
            artifact["bytes"] = len(files[name])
            artifact["sha256"] = MODULE.quality_m1_digest(files[name])
            files["manifest.json"] = (
                MODULE.quality_m1_canonical_json_bytes(manifest)
            )

        shard_files = dict(original)
        shard = json.loads(shard_files["blind-shard-01.json"])
        shard["items"][0]["chinese"] += "变更"
        shard_files["blind-shard-01.json"] = (
            MODULE.quality_m1_canonical_json_bytes(shard)
        )
        refresh_manifest(shard_files, "blind-shard-01.json")
        with self.assertRaisesRegex(
            RuntimeError, "shards do not reconstruct parent"
        ):
            MODULE.validate_quality_m1_files(shard_files)

        truth_files = dict(original)
        truth = json.loads(truth_files["truth.json"])
        truth["items"][0]["semantic_reason"] += " changed"
        truth_files["truth.json"] = (
            MODULE.quality_m1_canonical_json_bytes(truth)
        )
        refresh_manifest(truth_files, "truth.json")
        with self.assertRaisesRegex(RuntimeError, "truth commitment"):
            MODULE.validate_quality_m1_files(truth_files)

        noncanonical = {"truth.json": original["truth.json"] + b"\n"}
        with self.assertRaisesRegex(RuntimeError, "not canonical JSON"):
            MODULE.quality_m1_load_canonical(noncanonical, "truth.json")

        leaked = {"items": [{"revision_kind": "adopted"}]}
        self.assertEqual(
            ["$fixture.items[0].revision_kind"],
            MODULE.quality_m1_forbidden_fields(leaked, "$fixture"),
        )

    def test_quality_m1_input_change_propagates_to_bound_artifacts(self):
        payload, original = quality_m1_fixture()
        changed = MODULE.build_quality_m1_files(
            payload,
            b"changed fixture prompt\n",
            b"fixture context\n",
            "b" * 64,
        )
        self.assertNotEqual(
            original["blind-packet.json"], changed["blind-packet.json"]
        )
        self.assertNotEqual(original["truth.json"], changed["truth.json"])
        self.assertNotEqual(
            original["commitment.json"], changed["commitment.json"]
        )
        self.assertNotEqual(
            original["manifest.json"], changed["manifest.json"]
        )

    def test_quality_m1_filesystem_verifier_fails_closed(self):
        _payload, files = quality_m1_fixture()
        MODULE.QUALITY_M1_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            dir=MODULE.QUALITY_M1_OUTPUT_ROOT
        ) as directory:
            parent = Path(directory)
            valid = parent / "valid"
            MODULE.write_quality_m1_bundle(valid, files)
            MODULE.verify_quality_m1_bundle(valid, files)
            (valid / "prompt.md").write_bytes(b"mutated\n")
            with self.assertRaisesRegex(RuntimeError, "byte mismatch"):
                MODULE.verify_quality_m1_bundle(valid, files)

            missing = parent / "missing"
            MODULE.write_quality_m1_bundle(missing, files)
            (missing / "blind-shard-04.json").unlink()
            with self.assertRaisesRegex(RuntimeError, "membership"):
                MODULE.verify_quality_m1_bundle(missing, files)

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(
                RuntimeError, "must be under .artifacts"
            ):
                MODULE.quality_m1_output_directory(Path(directory))


if __name__ == "__main__":
    unittest.main(verbosity=2)
