#!/usr/bin/env python3
"""Tests for the Issue #72 quotes inventory and strict ledger."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/quotes_inventory.py"
SPEC = importlib.util.spec_from_file_location("quotes_inventory", SCRIPT)
assert SPEC and SPEC.loader
quotes = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(quotes)


def _audit_input(text: str):
    data = text.encode("utf-8")
    return quotes.AuditInput(
        audit_commit=None,
        logical_path="docs/quotes-review-results.md",
        relative_path="docs/quotes-review-results.md",
        bytes=data,
        text=text,
        sha256=hashlib.sha256(data).hexdigest(),
    )


def _card(row: dict[str, object]) -> dict[str, object]:
    return {
        "alias_target": row["alias_target"],
        "confidence": "high",
        "current_chinese": row["chinese"],
        "current_english": row["english"],
        "decision_authority": "docs/decisions.md; not applicable where no exact ruling exists",
        "deferral_owner": None,
        "deferral_reason": None,
        "dependency_group": row["dependency_group"],
        "display_context": "getQuoteString display-only quotation",
        "evidence_locations": [
            f"{quotes.QUOTES_EN}:{row['english_key_line']}",
            f"{quotes.QUOTES_ZH}:{row['chinese_key_line']}",
        ],
        "fact_sha256": row["fact_sha256"],
        "glossary_authority": f"docs/glossary.md SHA-256 {PAYLOAD['glossary_sha256']}",
        "identity": row["identity"],
        "key": row["key"],
        "lifecycle": row["lifecycle"],
        "literary_exception_reason": row["literary_exception_reason"],
        "producer_consumer": "TextDB quotes -> getQuoteString -> description UI",
        "proposed_translation": None,
        "reentry_trigger": "EN/ZH quotes, glossary, decisions, load order, alias or consumers change",
        "rejected_alternatives": [],
        "resolved_key": row["resolved_key"],
        "reviewer_rationale": "Fixture keep decision bound to the complete frozen body.",
        "section": row["section"],
        "suggestions": [],
        "terminal_conclusion": "keep",
    }


def _review_text(payload: dict[str, object], cards: list[dict[str, object]]) -> str:
    metadata = {
        "alias_count": payload["alias_count"],
        "baseline": payload["baseline"],
        "direct_quote_count": payload["direct_quote_count"],
        "glossary_sha256": payload["glossary_sha256"],
        "identity_count": payload["identity_count"],
        "inventory_sha256": payload["inventory_sha256"],
    }
    lines = [
        quotes.STRICT_REVIEW_BEGIN,
        quotes._canonical_json(metadata),
        "```jsonl",
        *(quotes._canonical_json(card) for card in cards),
        "```",
        quotes.STRICT_REVIEW_END,
        "",
    ]
    return "\n".join(lines)


BASELINE = quotes.resolve_commit("HEAD")
PAYLOAD = quotes.build_payload(BASELINE)


class QuotesInventoryTests(unittest.TestCase):
    def test_real_inventory_is_complete_unique_and_symmetric(self) -> None:
        inventory = PAYLOAD["inventory"]
        identities = [row["identity"] for row in inventory]
        self.assertEqual(PAYLOAD["identity_count"], len(identities))
        self.assertEqual(len(identities), len(set(identities)))
        self.assertEqual(
            PAYLOAD["identity_count"],
            PAYLOAD["direct_quote_count"] + PAYLOAD["alias_count"],
        )
        self.assertEqual([], PAYLOAD["english_minus_chinese"])
        self.assertEqual([], PAYLOAD["chinese_minus_english"])
        self.assertTrue(PAYLOAD["canonical_order_equal"])
        self.assertTrue(PAYLOAD["section_assignments_equal"])
        self.assertTrue(PAYLOAD["alias_graph_equal"])

    def test_inventory_is_deterministic(self) -> None:
        rerun = quotes.build_payload(BASELINE)
        self.assertEqual(PAYLOAD["inventory_sha256"], rerun["inventory_sha256"])
        self.assertEqual(PAYLOAD, rerun)

    def test_candidate_protected_input_drift_is_rejected(self) -> None:
        candidate = json.loads(json.dumps(PAYLOAD))
        protected = quotes.GLOSSARY_MD
        candidate["inputs"][protected]["sha256"] = "0" * 64
        self.assertEqual(
            [protected], quotes._protected_input_drift(PAYLOAD, candidate)
        )

        candidate = json.loads(json.dumps(PAYLOAD))
        candidate["inputs"][quotes.QUOTES_ZH]["sha256"] = "0" * 64
        self.assertEqual([], quotes._protected_input_drift(PAYLOAD, candidate))

    def test_candidate_review_path_outside_repository_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "outside the repository"):
            quotes._load_git_review_input(BASELINE, Path("/tmp/review.md"))

    def test_section_headings_are_comment_only_metadata(self) -> None:
        text = "\n".join(
            [
                "########",
                "#",
                "# First",
                "#",
                "########",
                "%%%%",
                "One",
                "body",
                "# an ordinary body comment",
                "%%%%",
                "Two",
                "body",
            ]
        )
        entries = quotes.parse_db_keys(text, "fixture.txt")
        self.assertEqual({"one": "First", "two": "First"}, quotes._entry_sections(text, entries, "fixture.txt"))

    def test_malformed_section_heading_fails_closed(self) -> None:
        text = "########\n# Missing spacer framing\n########\n%%%%\nkey\nbody\n"
        entries = quotes.parse_db_keys(text, "fixture.txt")
        with self.assertRaisesRegex(RuntimeError, "no #### section headings"):
            quotes._entry_sections(text, entries, "fixture.txt")

    def test_alias_target_and_chain_are_resolved(self) -> None:
        text = "%%%%\nA\n<B>\n%%%%\nB\n<C>\n%%%%\nC\nbody\n"
        entries, overrides = quotes.merge_desc_sequence(
            quotes.parse_db_keys(text, "fixture.txt")
        )
        self.assertEqual([], overrides)
        self.assertEqual({"a": "c", "b": "c", "c": "c"}, quotes._resolve_aliases(entries))

    def test_missing_alias_target_fails_closed(self) -> None:
        text = "%%%%\nA\n<missing>\n%%%%\n"
        entries, _ = quotes.merge_desc_sequence(quotes.parse_db_keys(text, "fixture.txt"))
        with self.assertRaisesRegex(RuntimeError, "alias target is missing"):
            quotes._resolve_aliases(entries)

    def test_alias_cycle_fails_closed(self) -> None:
        text = "%%%%\nA\n<B>\n%%%%\nB\n<A>\n%%%%\n"
        entries, _ = quotes.merge_desc_sequence(quotes.parse_db_keys(text, "fixture.txt"))
        with self.assertRaisesRegex(RuntimeError, "alias cycle"):
            quotes._resolve_aliases(entries)

    def test_complete_keep_ledger_has_exact_bidirectional_coverage(self) -> None:
        cards = [_card(row) for row in PAYLOAD["inventory"]]
        review = quotes.review_coverage(PAYLOAD, _audit_input(_review_text(PAYLOAD, cards)))
        self.assertTrue(review["coverage_equal"])
        self.assertEqual(PAYLOAD["identity_count"], review["evidence_card_count"])
        self.assertEqual([], review["inventory_minus_review"])
        self.assertEqual([], review["review_minus_inventory"])

    def test_duplicate_card_is_rejected(self) -> None:
        cards = [_card(row) for row in PAYLOAD["inventory"]]
        cards.append(cards[-1].copy())
        review = quotes.review_coverage(PAYLOAD, _audit_input(_review_text(PAYLOAD, cards)))
        self.assertFalse(review["coverage_equal"])
        self.assertEqual([cards[-1]["identity"]], review["duplicate_evidence_cards"])

    def test_changed_frozen_body_is_rejected(self) -> None:
        cards = [_card(row) for row in PAYLOAD["inventory"]]
        cards[0]["current_chinese"] = "drift"
        review = quotes.review_coverage(PAYLOAD, _audit_input(_review_text(PAYLOAD, cards)))
        self.assertFalse(review["coverage_equal"])
        self.assertIn(
            f"{cards[0]['identity']}:current_chinese",
            review["mismatched_mechanical_fields"],
        )

    def test_deferral_requires_reason_owner_and_trigger(self) -> None:
        cards = [_card(row) for row in PAYLOAD["inventory"]]
        cards[0]["terminal_conclusion"] = "defer terminology"
        review = quotes.review_coverage(PAYLOAD, _audit_input(_review_text(PAYLOAD, cards)))
        self.assertFalse(review["coverage_equal"])
        self.assertIn(f"{cards[0]['identity']}:deferral_reason", review["invalid_cards"])
        self.assertIn(f"{cards[0]['identity']}:deferral_owner", review["invalid_cards"])

    def test_adjust_requires_a_distinct_nonempty_proposal(self) -> None:
        cards = [_card(row) for row in PAYLOAD["inventory"]]
        cards[0]["terminal_conclusion"] = "adjust"
        review = quotes.review_coverage(PAYLOAD, _audit_input(_review_text(PAYLOAD, cards)))
        self.assertFalse(review["coverage_equal"])
        self.assertIn(f"{cards[0]['identity']}:proposed_translation", review["invalid_cards"])

    def test_unknown_card_field_is_rejected(self) -> None:
        cards = [_card(row) for row in PAYLOAD["inventory"]]
        cards[0]["unknown"] = True
        with self.assertRaisesRegex(RuntimeError, "card fields"):
            quotes.parse_review(_audit_input(_review_text(PAYLOAD, cards)))

    def test_noncanonical_json_is_rejected(self) -> None:
        cards = [_card(row) for row in PAYLOAD["inventory"]]
        text = _review_text(PAYLOAD, cards)
        first = quotes._canonical_json(cards[0])
        text = text.replace(first, json.dumps(cards[0], ensure_ascii=False), 1)
        with self.assertRaisesRegex(RuntimeError, "not canonical JSON"):
            quotes.parse_review(_audit_input(text))


if __name__ == "__main__":
    unittest.main()
