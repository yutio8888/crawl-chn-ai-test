#!/usr/bin/env python3
"""Tests for the Issue #46 tutorial inventory."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/tutorial_inventory.py"
SPEC = importlib.util.spec_from_file_location("tutorial_inventory", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)
BASELINE = subprocess.check_output(
    ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
).strip()


def frozen_blobs() -> dict[str, bytes]:
    paths = [
        MODULE.TUTORIAL_EN, MODULE.TUTORIAL_ZH, MODULE.TUTORIAL_LUA,
        MODULE.TUTORIAL_CC, MODULE.HINTS_CC, MODULE.L_CRAWL_CC,
        MODULE.COMMAND_TYPE_H, MODULE.GLOSSARY_MD, *MODULE.LESSONS,
    ]
    return {path: MODULE.git_show_blob(BASELINE, path) for path in paths}


def render_review(payload: dict[str, object], *, mutate=None) -> str:
    cards = []
    for row in payload["inventory"]:
        card = {
            "actual_behavior": "Displayed through tutorial_msg after static command and platform-tag substitution.",
            "confidence": "high",
            "consumer": "hints.cc tutorial_msg and hint_replace_cmds",
            "current_chinese": row["chinese"],
            "current_english": row["english"],
            "dependency_group": row["dependency_group"],
            "display_context": "Tutorial message or summary screen.",
            "evidence_locations": row["producer_locations"] + [MODULE.TUTORIAL_EN, MODULE.TUTORIAL_ZH],
            "fact_sha256": row["fact_sha256"],
            "glossary_authority": f"docs/glossary.md SHA-256 {payload['glossary_sha256']}",
            "identity": row["identity"],
            "lifecycle": row["lifecycle"],
            "producer": "Static tutorial vault/Lua/C++ producer.",
            "production_facts": row,
            "proposed_translation": None,
            "reentry_trigger": "Re-review when source, translation, producer, consumer, or glossary changes.",
            "rejected_alternatives": [],
            "reviewer_rationale": "keep: fixture conclusion for schema validation.",
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
    lines = [
        MODULE.STRICT_REVIEW_BEGIN,
        json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        "```jsonl",
        *(json.dumps(card, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for card in cards),
        "```",
        MODULE.STRICT_REVIEW_END,
    ]
    return "\n".join(lines) + "\n"


def audit_input(text: str) -> MODULE.AuditInput:
    data = text.encode("utf-8")
    import hashlib
    return MODULE.AuditInput(
        audit_commit=None,
        logical_path="docs/tutorial-review-results.md",
        relative_path="docs/tutorial-review-results.md",
        bytes=data,
        text=text,
        sha256=hashlib.sha256(data).hexdigest(),
    )


class TutorialInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blobs = frozen_blobs()
        cls.payload = MODULE.build_payload_from_blobs(BASELINE, dict(cls.blobs))

    def test_current_tree_has_exact_three_way_coverage(self):
        payload = self.payload
        self.assertEqual(88, len(payload["inventory"]))
        for field in (
            "producer_minus_en", "en_minus_producer",
            "producer_minus_zh", "zh_minus_producer",
        ):
            self.assertEqual([], payload[field])
        self.assertEqual(len(payload["inventory"]), len({row["identity"] for row in payload["inventory"]}))

    def test_current_structural_candidates_are_visible(self):
        candidates = {
            row["identity"] for row in self.payload["inventory"]
            if row["english_tokens"]["tag_errors"]
            or row["chinese_tokens"]["tag_errors"]
            or not all(row["token_multiset_equal"].values())
        }
        self.assertEqual({
            "tutorial:tutorial3 artefact_armour",
            "tutorial:tutorial3 exit",
            "tutorial:tutorial5 berserk",
        }, candidates)

    def test_missing_or_extra_textdb_key_is_reported_bidirectionally(self):
        blobs = dict(self.blobs)
        text = blobs[MODULE.TUTORIAL_EN].decode("utf-8")
        blobs[MODULE.TUTORIAL_EN] = text.replace(
            "\ntutorial intro\n", "\ntutorial unexpected\n", 1
        ).encode("utf-8")
        payload = MODULE.build_payload_from_blobs(BASELINE, blobs)
        self.assertEqual(["tutorial intro"], payload["producer_minus_en"])
        self.assertEqual(["tutorial unexpected"], payload["en_minus_producer"])

    def test_textdb_override_is_rejected(self):
        blobs = dict(self.blobs)
        blobs[MODULE.TUTORIAL_ZH] += b"\n%%%%\ntutorial intro\nduplicate\n"
        with self.assertRaisesRegex(RuntimeError, "overrides are forbidden"):
            MODULE.build_payload_from_blobs(BASELINE, blobs)

    def test_nonliteral_producer_is_rejected(self):
        blobs = dict(self.blobs)
        path = MODULE.LESSONS[0]
        text = blobs[path].decode("utf-8").replace(
            'tutorial1.msg("go_on")', "tutorial1.msg(dynamic_key)", 1
        )
        blobs[path] = text.encode("utf-8")
        with self.assertRaisesRegex(RuntimeError, "non-literal or malformed"):
            MODULE.build_payload_from_blobs(BASELINE, blobs)

    def test_consumer_drift_is_rejected(self):
        blobs = dict(self.blobs)
        blobs[MODULE.HINTS_CC] = blobs[MODULE.HINTS_CC].replace(
            b"_replace_static_tags(text);", b"changed_consumer(text);"
        )
        with self.assertRaisesRegex(RuntimeError, "consumer shape changed"):
            MODULE.build_payload_from_blobs(BASELINE, blobs)

    def test_unknown_and_malformed_command_tokens_are_rejected(self):
        for replacement in ("$cmd[CMD_NOT_REAL]", "$cmd[CMD_MOVE_LEFT"):
            with self.subTest(replacement=replacement):
                blobs = dict(self.blobs)
                text = blobs[MODULE.TUTORIAL_ZH].decode("utf-8").replace(
                    "$cmd[CMD_MOVE_LEFT]", replacement, 1
                )
                blobs[MODULE.TUTORIAL_ZH] = text.encode("utf-8")
                with self.assertRaisesRegex(RuntimeError, "malformed or unknown"):
                    MODULE.build_payload_from_blobs(BASELINE, blobs)

    def test_tag_imbalance_is_recorded_per_identity(self):
        facts = MODULE._token_facts("<input>broken", {"CMD_NO_CMD"})
        self.assertEqual(["unclosed <input>"], facts["tag_errors"])

    def test_review_coverage_accepts_complete_canonical_ledger(self):
        result = MODULE.review_coverage(self.payload, audit_input(render_review(self.payload)))
        self.assertTrue(result["coverage_equal"])
        self.assertEqual(88, result["evidence_card_count"])

    def test_review_coverage_rejects_duplicate_and_fact_mutation(self):
        def mutate(cards):
            cards[0]["fact_sha256"] = "0" * 64
            cards.append(cards[1])
        result = MODULE.review_coverage(self.payload, audit_input(render_review(self.payload, mutate=mutate)))
        self.assertFalse(result["coverage_equal"])
        self.assertTrue(result["duplicate_evidence_cards"])
        self.assertIn(f"{self.payload['inventory'][0]['identity']}:fact_sha256", result["mismatched_mechanical_fields"])

    def test_adjust_requires_a_distinct_nonempty_proposal(self):
        def mutate(cards):
            cards[0]["terminal_conclusion"] = "adjust"
            cards[0]["proposed_translation"] = cards[0]["current_chinese"]
        result = MODULE.review_coverage(self.payload, audit_input(render_review(self.payload, mutate=mutate)))
        self.assertFalse(result["coverage_equal"])
        self.assertIn(f"{self.payload['inventory'][0]['identity']}:proposed_translation", result["invalid_cards"])

    def test_candidate_agreement_binds_keep_values_to_exact_commit(self):
        review = audit_input(render_review(self.payload))
        result = MODULE.candidate_agreement(self.payload, review, BASELINE)
        self.assertTrue(result["candidate_agrees"])
        self.assertEqual([], result["translation_mismatches"])

    def test_candidate_agreement_rejects_unlanded_adjustment(self):
        def mutate(cards):
            cards[0]["terminal_conclusion"] = "adjust"
            cards[0]["proposed_translation"] = "confirmed but absent"
        review = audit_input(render_review(self.payload, mutate=mutate))
        result = MODULE.candidate_agreement(self.payload, review, BASELINE)
        self.assertFalse(result["candidate_agrees"])
        self.assertEqual([self.payload["inventory"][0]["identity"]], result["translation_mismatches"])

    def test_cli_rejects_existing_and_nested_output_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            existing = Path(tmp) / "existing.json"
            existing.write_text("occupied", encoding="utf-8")
            for output in (existing, Path(tmp) / "nested" / "new.json"):
                with self.subTest(output=output):
                    proc = subprocess.run(
                        ["python3", str(SCRIPT), "--baseline-ref", BASELINE,
                         "--inventory-output", str(output)],
                        cwd=ROOT, text=True, capture_output=True,
                    )
                    self.assertNotEqual(0, proc.returncode)

    def test_invalid_baseline_ref_fails_closed(self):
        proc = subprocess.run(
            ["python3", str(SCRIPT), "--baseline-ref", "not-a-ref",
             "--inventory-output", "/tmp/tutorial-invalid-ref-output.json"],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertNotEqual(0, proc.returncode)

    def test_exact_git_review_input_rejects_escape_and_binds_commit(self):
        loaded = MODULE.load_git_review_input(
            BASELINE, Path("docs/command-review-results.md")
        )
        self.assertEqual(BASELINE, loaded.audit_commit)
        self.assertEqual("docs/command-review-results.md", loaded.logical_path)
        with self.assertRaisesRegex(RuntimeError, "not normalized"):
            MODULE.load_git_review_input(BASELINE, Path("../escape.md"))


if __name__ == "__main__":
    unittest.main()
