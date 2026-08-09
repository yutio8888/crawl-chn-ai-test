#!/usr/bin/env python3
"""Focused invariants for the Issue #52 HelpDB/FAQDB inventory."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/help_inventory.py"
SPEC = importlib.util.spec_from_file_location("help_inventory", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)

BASELINE = "7caba5166f4b2fd680ecbc258ea6ffe3f6249f50"


def frozen_blobs() -> dict[str, bytes]:
    return {
        path: MODULE.git_show_blob(BASELINE, path)
        for path in MODULE.INPUT_PATHS
    }


def audit_input(text: str) -> MODULE.AuditInput:
    data = text.encode("utf-8")
    return MODULE.AuditInput(
        audit_commit=None,
        logical_path="docs/help-review-results.md",
        relative_path="docs/help-review-results.md",
        bytes=data,
        text=text,
        sha256=hashlib.sha256(data).hexdigest(),
    )


def render_review(payload: dict[str, object], *, mutate=None) -> str:
    cards = []
    for row in payload["inventory"]:
        card = {
            **MODULE._mechanical_fields(row),
            "actual_behavior": (
                "The exact baseline value follows its recorded TextDB lookup, "
                "transformation, lifecycle, and display path."
            ),
            "confidence": "high",
            "deferral_owner": None,
            "deferral_reason": None,
            "glossary_authority": (
                f"docs/glossary.md SHA-256 {payload['glossary_sha256']}"
            ),
            "proposed_translation": None,
            "reentry_trigger": (
                "Re-review when the TextDB value, consumer, lifecycle, token "
                "contract, or glossary changes."
            ),
            "rejected_alternatives": [],
            "reviewer_rationale": "keep: schema fixture conclusion.",
            "terminal_conclusion": "keep",
        }
        cards.append(card)
    if mutate:
        mutate(cards)
    metadata = {
        "baseline": payload["baseline"],
        "glossary_sha256": payload["glossary_sha256"],
        "identity_count": len(payload["inventory"]),
        "inventory_sha256": payload["inventory_sha256"],
    }
    return "\n".join([
        MODULE.STRICT_REVIEW_BEGIN,
        json.dumps(
            metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ),
        "```jsonl",
        *(json.dumps(
            card, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ) for card in cards),
        "```",
        MODULE.STRICT_REVIEW_END,
        "",
    ])


class HelpInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blobs = frozen_blobs()
        cls.payload = MODULE.build_payload_from_blobs(BASELINE, dict(cls.blobs))

    def test_identity_union_pairing_and_order_are_complete(self):
        payload = self.payload
        help_rows = [row for row in payload["inventory"] if row["kind"] == "help"]
        faq_rows = [row for row in payload["inventory"] if row["kind"] == "faq"]
        self.assertEqual(
            set(payload["help_union_keys"]),
            {row["key"] for row in help_rows},
        )
        self.assertEqual(
            payload["faq_en_question_order"],
            [row["key"] for row in faq_rows],
        )
        self.assertEqual(
            len(payload["inventory"]),
            len({row["identity"] for row in payload["inventory"]}),
        )
        for field in (
            "help_en_minus_zh",
            "help_zh_minus_en",
            "faq_en_question_minus_answer",
            "faq_en_answer_minus_question",
            "faq_zh_question_minus_answer",
            "faq_zh_answer_minus_question",
            "faq_en_minus_zh",
            "faq_zh_minus_en",
        ):
            self.assertEqual([], payload[field])
        self.assertEqual([], payload["blocking_violations"])

    def test_every_help_identity_has_consumer_and_lifecycle_evidence(self):
        rows = [row for row in self.payload["inventory"] if row["kind"] == "help"]
        self.assertTrue(all(row["producer"] for row in rows))
        lifecycle = {row["key"]: row["lifecycle"] for row in rows}
        self.assertEqual("console-only", lifecycle["console-keycodes"])
        self.assertEqual("wizard-only", lifecycle["wiz-monster"])
        self.assertTrue(all(
            row["consumer"]["lookup"].startswith(MODULE.DATABASE_CC + ":")
            for row in rows
        ))

    def test_faq_source_order_is_bound_but_runtime_order_is_not_overclaimed(self):
        self.assertEqual(
            self.payload["faq_en_question_order"],
            self.payload["faq_zh_question_order"],
        )
        self.assertFalse(self.payload["faq_runtime_order_guaranteed"])
        faq_rows = [
            row for row in self.payload["inventory"] if row["kind"] == "faq"
        ]
        self.assertTrue(all(
            "DBM iteration order" in row["producer"]["source_note"]
            for row in faq_rows
        ))

    def test_production_parser_skips_comments_after_separator(self):
        text = "%%%%\n# comment between separator and key\nQ:version\n\nQuestion\n"
        entries = MODULE.parse_db_keys(text, "fixture.txt")
        self.assertEqual(["Q:version"], [entry.raw_key for entry in entries])
        self.assertEqual("Question\n\n", entries[0].value)

    def test_textdb_override_is_rejected(self):
        blobs = dict(self.blobs)
        blobs[MODULE.HELP_ZH] += b"\n%%%%\npick-up\nduplicate\n"
        with self.assertRaisesRegex(RuntimeError, "overrides are forbidden"):
            MODULE.build_payload_from_blobs(BASELINE, blobs)

    def test_orphan_faq_question_is_blocking(self):
        blobs = dict(self.blobs)
        text = blobs[MODULE.FAQ_ZH].decode("utf-8")
        text = text.replace("\nA:goal\n", "\nA:goal changed\n", 1)
        blobs[MODULE.FAQ_ZH] = text.encode("utf-8")
        payload = MODULE.build_payload_from_blobs(BASELINE, blobs)
        kinds = {item["kind"] for item in payload["blocking_violations"]}
        self.assertIn("chinese-question-without-answer", kinds)
        self.assertIn("chinese-answer-without-question", kinds)

    def test_question_order_drift_is_blocking(self):
        blobs = dict(self.blobs)
        text = blobs[MODULE.FAQ_ZH].decode("utf-8")
        first = "%%%%\nQ:goal\n\n这个游戏的终极目标是什么？\n"
        second = "%%%%\nQ:userdir\n\n我找不到保存的文件，死亡记录和角色记录。他们都在哪儿呢？\n"
        self.assertIn(first, text)
        self.assertIn(second, text)
        text = text.replace(first, "__FIRST__", 1).replace(second, first, 1)
        text = text.replace("__FIRST__", second, 1)
        blobs[MODULE.FAQ_ZH] = text.encode("utf-8")
        payload = MODULE.build_payload_from_blobs(BASELINE, blobs)
        self.assertIn(
            "english-chinese-question-order-mismatch",
            {item["kind"] for item in payload["blocking_violations"]},
        )

    def test_help_key_without_consumer_is_blocking(self):
        blobs = dict(self.blobs)
        key = "level-map"
        for path in MODULE.HELP_CONSUMER_PATHS:
            blobs[path] = blobs[path].replace(
                f'"{key}"'.encode(), b'"level-map-changed"'
            )
        payload = MODULE.build_payload_from_blobs(BASELINE, blobs)
        self.assertIn(
            (f"help:{key}", "help-textdb-without-consumer-evidence"),
            {
                (item["identity"], item["kind"])
                for item in payload["blocking_violations"]
            },
        )

    def test_lua_control_or_comparison_drift_is_blocking(self):
        for replacement, expected in (
            ("if not you.wizard() then", "lua-lua-control-skeleton-mismatch"),
            ('if you.wizard() == "Zin" then', "lua-lua-control-skeleton-mismatch"),
        ):
            with self.subTest(replacement=replacement):
                blobs = dict(self.blobs)
                text = blobs[MODULE.HELP_ZH].decode("utf-8").replace(
                    "if you.wizard() then", replacement, 1
                )
                blobs[MODULE.HELP_ZH] = text.encode("utf-8")
                payload = MODULE.build_payload_from_blobs(BASELINE, blobs)
                self.assertIn(
                    expected,
                    {item["kind"] for item in payload["blocking_violations"]},
                )

    def test_malformed_markup_is_recorded_for_review(self):
        blobs = dict(self.blobs)
        text = blobs[MODULE.HELP_ZH].decode("utf-8").replace(
            "<h>定位和选择物品</h>", "<h定位和选择物品</h>", 1
        )
        blobs[MODULE.HELP_ZH] = text.encode("utf-8")
        payload = MODULE.build_payload_from_blobs(BASELINE, blobs)
        row = next(
            row for row in payload["inventory"]
            if row["identity"] == "help:pick-up"
        )
        self.assertTrue(row["chinese_tokens"]["markup"]["malformed"])
        self.assertIn("help:pick-up", payload["structural_review_candidates"])
        self.assertEqual([], payload["blocking_violations"])

    def test_structural_differences_are_candidates_not_translation_verdicts(self):
        candidates = set(self.payload["structural_review_candidates"])
        self.assertTrue(candidates)
        self.assertEqual([], self.payload["blocking_violations"])
        self.assertTrue(any(
            row["structural_differences"]
            for row in self.payload["inventory"]
        ))

    def test_review_coverage_accepts_complete_canonical_ledger(self):
        result = MODULE.review_coverage(
            self.payload, audit_input(render_review(self.payload))
        )
        self.assertTrue(result["coverage_equal"])
        self.assertEqual(len(self.payload["inventory"]), result["evidence_card_count"])

    def test_review_coverage_rejects_duplicate_and_fact_mutation(self):
        def mutate(cards):
            cards[0]["fact_sha256"] = "0" * 64
            cards.append(copy.deepcopy(cards[1]))
        result = MODULE.review_coverage(
            self.payload,
            audit_input(render_review(self.payload, mutate=mutate)),
        )
        self.assertFalse(result["coverage_equal"])
        self.assertTrue(result["duplicate_evidence_cards"])
        self.assertIn(
            f"{self.payload['inventory'][0]['identity']}:fact_sha256",
            result["mismatched_mechanical_fields"],
        )

    def test_help_and_faq_adjustments_require_typed_distinct_proposals(self):
        help_identity = next(
            row["identity"] for row in self.payload["inventory"]
            if row["kind"] == "help"
        )
        faq_identity = next(
            row["identity"] for row in self.payload["inventory"]
            if row["kind"] == "faq"
        )

        def mutate(cards):
            by_id = {card["identity"]: card for card in cards}
            by_id[help_identity]["terminal_conclusion"] = "adjust"
            by_id[help_identity]["proposed_translation"] = {
                "question": "wrong type", "answer": "wrong type"
            }
            by_id[faq_identity]["terminal_conclusion"] = "adjust"
            by_id[faq_identity]["proposed_translation"] = "wrong type"

        result = MODULE.review_coverage(
            self.payload,
            audit_input(render_review(self.payload, mutate=mutate)),
        )
        self.assertFalse(result["coverage_equal"])
        self.assertIn(f"{help_identity}:proposed_translation", result["invalid_cards"])
        self.assertIn(f"{faq_identity}:proposed_translation", result["invalid_cards"])

    def test_candidate_agreement_accepts_exact_keep_candidate(self):
        review = audit_input(render_review(self.payload))
        result = MODULE.candidate_agreement_from_payloads(
            self.payload, review, self.payload, BASELINE
        )
        self.assertTrue(result["candidate_agrees"])
        self.assertEqual([], result["translation_mismatches"])

    def test_candidate_agreement_rejects_unlanded_faq_adjustment(self):
        faq_identity = next(
            row["identity"] for row in self.payload["inventory"]
            if row["kind"] == "faq"
        )

        def mutate(cards):
            card = next(card for card in cards if card["identity"] == faq_identity)
            card["terminal_conclusion"] = "adjust"
            card["proposed_translation"] = {
                "question": card["current_chinese"]["question"] + "（修订）",
                "answer": card["current_chinese"]["answer"],
            }

        review = audit_input(render_review(self.payload, mutate=mutate))
        result = MODULE.candidate_agreement_from_payloads(
            self.payload, review, self.payload, BASELINE
        )
        self.assertFalse(result["candidate_agrees"])
        self.assertEqual([faq_identity], result["translation_mismatches"])

    def test_cli_rejects_existing_and_nested_output_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            existing = Path(tmp) / "existing.json"
            existing.write_text("occupied", encoding="utf-8")
            for output in (existing, Path(tmp) / "nested" / "new.json"):
                with self.subTest(output=output):
                    proc = subprocess.run(
                        [
                            "python3", str(SCRIPT),
                            "--baseline-ref", BASELINE,
                            "--inventory-output", str(output),
                        ],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                    )
                    self.assertNotEqual(0, proc.returncode)

    def test_invalid_baseline_ref_fails_closed(self):
        proc = subprocess.run(
            [
                "python3", str(SCRIPT),
                "--baseline-ref", "not-a-ref",
                "--inventory-output", "/tmp/help-invalid-ref-output.json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(0, proc.returncode)


if __name__ == "__main__":
    unittest.main()
