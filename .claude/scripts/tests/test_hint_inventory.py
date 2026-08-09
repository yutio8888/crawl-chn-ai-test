#!/usr/bin/env python3
"""Focused invariants for the Issue #50 Hints inventory."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/hint_inventory.py"
SPEC = importlib.util.spec_from_file_location("hint_inventory", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)

BASELINE = "61b35104580fb56340e3cdac87ca5fffa36788bf"
BASELINE_INVENTORY_SHA256 = (
    "8a756e6447b258eb6e53742f10ae79cbd257ddb0e19ab13926928940096242fd"
)

TEST_PLATFORM_TAGS = set(MODULE._PLATFORM_UNTAG_ORDER)
TEST_ALLOWED_TAGS = TEST_PLATFORM_TAGS | {"h", "input", "w"}
TEST_COMMAND_NAMES = {"CMD_ADJUST_INVENTORY", "CMD_EVOKE"}


def token_facts(value: str) -> dict[str, object]:
    return MODULE._token_facts(
        value,
        TEST_COMMAND_NAMES,
        set(),
        TEST_ALLOWED_TAGS,
        TEST_PLATFORM_TAGS,
    )


def frozen_blobs() -> dict[str, bytes]:
    return {
        path: MODULE.git_show_blob(BASELINE, path)
        for path in MODULE.INPUT_PATHS
    }


def clean_candidate_payload(blobs: dict[str, bytes]) -> dict[str, object]:
    """Build a structurally clean candidate without writing translation assets."""
    candidate = dict(blobs)
    english = candidate[MODULE.HINTS_EN].decode("utf-8")
    chinese = candidate[MODULE.HINTS_ZH].decode("utf-8")
    english = english.replace(
        "<nomouse\nby pressing", "<nomouse>\nby pressing", 1
    ).replace(
        'onto it."\n\nSome branches',
        'onto it."</nomouse>\n\nSome branches',
        1,
    ).replace(
        "on it<tiles>", "on it</tiles>", 1
    )
    adjacency_rewrites = (
        ("</w>nventory", "</w> inventory", 6),
        (
            "e<w>$cmd[CMD_EVOKE]</w>oke",
            "<w>$cmd[CMD_EVOKE]</w> evoke",
            2,
        ),
        (
            "e<w>$cmd[CMD_EVOKE]</w>oking",
            "<w>$cmd[CMD_EVOKE]</w> evoking",
            1,
        ),
        ("</w>ielded", "</w> wielded", 1),
        ("</w>rop", "</w> drop", 1),
        ("$cmd[CMD_DISPLAY_MAP]ee", "$cmd[CMD_DISPLAY_MAP] ee", 1),
        ("</w>uaff", "</w> quaff", 1),
        ("</w>bility", "</w> ability", 1),
        (
            "$cmd[CMD_ADJUST_INVENTORY]i",
            "$cmd[CMD_ADJUST_INVENTORY] i",
            1,
        ),
    )
    for old, new, expected_count in adjacency_rewrites:
        actual_count = english.count(old)
        if actual_count != expected_count:
            raise AssertionError(
                f"clean EN fixture expected {expected_count} occurrence(s) "
                f"of {old!r}, found {actual_count}"
            )
        english = english.replace(old, new)
    chinese = chinese.replace(
        "<input>鼠标左键点击</w >组合键",
        "<input>鼠标左键点击</input>组合键",
        1,
    ).replace(
        "<input>d键\n</w>来", "<input>d键\n</input>来", 1
    ).replace(
        "$cmd[CMD_DISPLAY_CHARACTER]",
        "$cmd[CMD_DISPLAY_CHARACTER_STATUS]",
        1,
    )
    candidate[MODULE.HINTS_EN] = english.encode("utf-8")
    candidate[MODULE.HINTS_ZH] = chinese.encode("utf-8")
    return MODULE.build_payload_from_blobs("f" * 40, candidate)


def render_candidate_review(
    payload: dict[str, object], candidate_payload: dict[str, object]
) -> str:
    candidate_by_identity = {
        row["identity"]: row for row in candidate_payload["inventory"]
    }

    def land_candidate_values(cards):
        for card in cards:
            candidate_chinese = candidate_by_identity[card["identity"]]["chinese"]
            if candidate_chinese != card["current_chinese"]:
                card["terminal_conclusion"] = "adjust"
                card["proposed_translation"] = candidate_chinese

    return render_review(payload, mutate=land_candidate_values)


def audit_input(text: str) -> MODULE.AuditInput:
    data = text.encode("utf-8")
    return MODULE.AuditInput(
        audit_commit=None,
        logical_path="docs/hint-review-results.md",
        relative_path="docs/hint-review-results.md",
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
                "The exact baseline value follows its recorded lookup, "
                "substitution, lifecycle, and display/test path."
            ),
            "confidence": "high",
            "deferral_owner": None,
            "deferral_reason": None,
            "glossary_authority": (
                f"docs/glossary.md SHA-256 {payload['glossary_sha256']}"
            ),
            "proposed_translation": None,
            "reentry_trigger": (
                "Re-review when the TextDB value, producer, consumer, "
                "lifecycle, token contract, or glossary changes."
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
    lines = [
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
    ]
    return "\n".join(lines) + "\n"


class HintInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blobs = frozen_blobs()
        cls.payload = MODULE.build_payload_from_blobs(BASELINE, dict(cls.blobs))
        cls.clean_candidate = clean_candidate_payload(cls.blobs)

    def test_union_identity_and_lifecycle_partition_is_exact(self):
        payload = self.payload
        rows = {row["key"]: row for row in payload["inventory"]}
        self.assertEqual(set(payload["union_keys"]), set(rows))
        self.assertEqual([], payload["inventory_minus_union"])
        self.assertEqual([], payload["union_minus_inventory"])
        self.assertEqual(len(rows), len(payload["inventory"]))

        current = {
            key for key, row in rows.items()
            if row["lifecycle"] == "current-producer"
        }
        self.assertEqual(set(payload["producer_keys"]), current)
        self.assertEqual(
            "tag34-enum-compatibility-unconsumed",
            rows[MODULE.FLEEING_KEY]["lifecycle"],
        )
        self.assertEqual(
            "localized-test-only-compatibility",
            rows[MODULE.DISSECTION_KEY]["lifecycle"],
        )
        self.assertEqual([], payload["producer_minus_en"])
        self.assertEqual([], payload["producer_minus_zh"])
        self.assertEqual([], payload["en_minus_zh"])
        self.assertEqual([MODULE.DISSECTION_KEY], payload["zh_minus_en"])

    def test_producers_include_every_finite_family_member(self):
        keys = set(self.payload["producer_keys"])
        self.assertTrue({f"death random {value}" for value in range(6)} <= keys)
        self.assertTrue({f"finished random {value}" for value in range(4)} <= keys)
        self.assertEqual(len(keys), len(self.payload["producer_keys"]))
        family = {
            row["key"]: row["producer_calls"]
            for row in self.payload["inventory"]
            if row["key"].startswith(("death random ", "finished random "))
        }
        self.assertTrue(all(
            calls[0]["kind"] == "finite-family" for calls in family.values()
        ))

    def test_new_dynamic_producer_shape_is_rejected(self):
        blobs = dict(self.blobs)
        text = blobs[MODULE.HINTS_CC].decode("utf-8").replace(
            'print_hint("HINT_SEEN_POTION");',
            "print_hint(dynamic_hint_key);",
            1,
        )
        blobs[MODULE.HINTS_CC] = text.encode("utf-8")
        with self.assertRaisesRegex(RuntimeError, "unparsed hint call shape"):
            MODULE.build_payload_from_blobs(BASELINE, blobs)

    def test_lifecycle_sources_are_exact_and_fail_closed(self):
        mutations = (
            (
                MODULE.HINTS_H,
                "HINT_FLEEING_MONSTER,",
                "HINT_FLEEING_MONSTER_CHANGED,",
                "lifecycle changed",
            ),
            (
                MODULE.ZH_RUNTIME_LUA,
                '"dissection reminder", "HINT_CONVERT"',
                '"HINT_CONVERT"',
                "compatibility keys changed",
            ),
        )
        for path, old, new, message in mutations:
            with self.subTest(path=path):
                blobs = dict(self.blobs)
                blobs[path] = blobs[path].decode("utf-8").replace(
                    old, new, 1
                ).encode("utf-8")
                with self.assertRaisesRegex(RuntimeError, message):
                    MODULE.build_payload_from_blobs(BASELINE, blobs)

    def test_platform_projection_consumer_is_exact_and_fail_closed(self):
        blobs = dict(self.blobs)
        blobs[MODULE.LIBUTIL_CC] = blobs[MODULE.LIBUTIL_CC].replace(
            b'_untag(s, "<tiles>", "</tiles>", is_tiles());',
            b'_untag(s, "<tiles>", "</tiles>", !is_tiles());',
            1,
        )
        with self.assertRaisesRegex(RuntimeError, "platform-tag consumer changed"):
            MODULE.build_payload_from_blobs(BASELINE, blobs)

    def test_en_zh_union_exposes_an_unexplained_new_key(self):
        blobs = dict(self.blobs)
        text = blobs[MODULE.HINTS_ZH].decode("utf-8").replace(
            "\nHINT_CLOUD_WARNING\n",
            "\nHINT_ZH_ONLY_MUTATION\n",
            1,
        )
        blobs[MODULE.HINTS_ZH] = text.encode("utf-8")
        payload = MODULE.build_payload_from_blobs(BASELINE, blobs)
        self.assertIn("hint_zh_only_mutation", payload["union_keys"])
        self.assertIn("hint_cloud_warning", payload["en_minus_zh"])
        self.assertIn("hint_zh_only_mutation", payload["zh_minus_en"])
        self.assertTrue(any(
            violation["kind"] == "unexplained-unconsumed-textdb-identity"
            and violation["identity"] == "hint:hint_zh_only_mutation"
            for violation in payload["blocking_violations"]
        ))

    def test_duplicate_and_empty_textdb_values_are_rejected(self):
        mutations = (
            (b"\n%%%%\nwelcome\nduplicate\n", "overrides are forbidden"),
            (b"\n%%%%\nempty mutation\n%%%%\n", "empty TextDB values"),
        )
        for suffix, message in mutations:
            with self.subTest(message=message):
                blobs = dict(self.blobs)
                blobs[MODULE.HINTS_EN] += suffix
                with self.assertRaisesRegex(RuntimeError, message):
                    MODULE.build_payload_from_blobs(BASELINE, blobs)

    def test_identity_membership_mismatch_is_a_blocking_violation(self):
        blobs = dict(self.blobs)
        text = blobs[MODULE.HINTS_CC].decode("utf-8").replace(
            'print_hint("HINT_SEEN_POTION");',
            'print_hint("HINT_NOT_IN_DATABASE");',
            1,
        )
        blobs[MODULE.HINTS_CC] = text.encode("utf-8")
        payload = MODULE.build_payload_from_blobs(BASELINE, blobs)
        kinds = {
            (value["identity"], value["kind"])
            for value in payload["blocking_violations"]
        }
        self.assertIn(
            ("hint:hint_not_in_database", "producer-without-textdb-identity"),
            kinds,
        )
        self.assertIn(
            ("hint:hint_seen_potion", "unexplained-unconsumed-textdb-identity"),
            kinds,
        )

    def test_token_facts_preserve_contracts_and_baseline_defects(self):
        rows = {row["key"]: row for row in self.payload["inventory"]}
        welcome = rows["welcome"]
        self.assertTrue(welcome["english_tokens"]["commands"])
        self.assertTrue(welcome["english_tokens"]["lua"]["blocks"])
        self.assertIn("lua_source_sequence", welcome["token_contract_equal"])
        self.assertIn("platform_tag_sequence", welcome["token_contract_equal"])
        self.assertIn("markup_sequence", welcome["token_contract_equal"])
        self.assertIn("placeholder_sequence", welcome["token_contract_equal"])
        self.assertIn("item_sequence", welcome["token_contract_equal"])

        blocking = {
            (value["identity"], value["kind"])
            for value in self.payload["blocking_violations"]
        }
        self.assertIn(
            ("hint:hint_seen_branch", "english-markup-malformed"), blocking
        )
        self.assertIn(
            ("hint:hint_seen_first_object", "chinese-markup-malformed"),
            blocking,
        )
        self.assertIn(
            ("hint:hint_you_mutated", "chinese-unknown-commands"), blocking
        )
        self.assertTrue(self.payload["structural_review_candidates"])

    def test_command_ascii_adjacency_uses_each_production_projection(self):
        prefix = token_facts("e<w>$cmd[CMD_EVOKE]</w>")
        self.assertEqual(1, len(prefix["command_ascii_adjacencies"]))
        prefix_projections = prefix[
            "command_ascii_adjacencies"
        ][0]["projections"]
        self.assertEqual(
            ["console", "localtiles", "webtiles"],
            [projection["platform"] for projection in prefix_projections],
        )
        self.assertTrue(all(
            projection["ascii_prefix"] == "e"
            and projection["ascii_suffix"] is None
            for projection in prefix_projections
        ))

        suffix = token_facts("<w>$cmd[CMD_EVOKE]</w>oke")
        self.assertEqual(1, len(suffix["command_ascii_adjacencies"]))
        self.assertTrue(all(
            projection["ascii_prefix"] is None
            and projection["ascii_suffix"] == "o"
            for projection in suffix[
                "command_ascii_adjacencies"
            ][0]["projections"]
        ))

        direct = token_facts("$cmd[CMD_ADJUST_INVENTORY]i")
        self.assertEqual(1, len(direct["command_ascii_adjacencies"]))
        self.assertTrue(all(
            projection["ascii_prefix"] is None
            and projection["ascii_suffix"] == "i"
            for projection in direct[
                "command_ascii_adjacencies"
            ][0]["projections"]
        ))

        exclusive = token_facts(
            "<localtiles><w>$cmd[CMD_EVOKE]</w></localtiles>"
            "<nomouse>oke</nomouse>"
        )
        self.assertEqual([], exclusive["command_ascii_adjacencies"])

    def test_command_ascii_adjacency_blocks_english_only(self):
        facts = token_facts("e<w>$cmd[CMD_EVOKE]</w>oke")
        english = MODULE._token_errors("english", "hint:fixture", facts)
        chinese = MODULE._token_errors("chinese", "hint:fixture", facts)
        self.assertEqual(
            ["english-command-ascii-adjacency"],
            [
                error["kind"] for error in english
                if "command-ascii-adjacency" in error["kind"]
            ],
        )
        self.assertFalse(any(
            "command-ascii-adjacency" in error["kind"] for error in chinese
        ))

    def test_baseline_command_ascii_adjacency_inventory_is_exact(self):
        facts = [
            (row, fact)
            for row in self.payload["inventory"]
            for fact in row["english_tokens"]["command_ascii_adjacencies"]
        ]
        occurrences = {
            (
                row["key"],
                row["english_key_line"] + fact["source_line"] + 1,
            )
            for row, fact in facts
        }
        self.assertEqual(15, len(facts))
        self.assertEqual(86, sum(
            len(row["english_tokens"]["commands"])
            for row in self.payload["inventory"]
        ))
        self.assertEqual({
            ("hint_seen_weapon", 265),
            ("hint_seen_missiles", 281),
            ("hint_seen_armour", 303),
            ("hint_seen_jewellery", 321),
            ("hint_seen_misc", 328),
            ("hint_seen_misc", 329),
            ("hint_seen_misc", 330),
            ("hint_seen_staff", 335),
            ("hint_full_inventory", 571),
            ("hint_auto_exclusion", 619),
            ("hint_need_poison_healing", 639),
            ("hint_can_berserk", 668),
            ("hint_advise_use_wand", 706),
            ("hint_wield_weapon", 756),
            ("hint_fleeing_monster", 763),
        }, occurrences)
        blocker_identities = {
            violation["identity"]
            for violation in self.payload["blocking_violations"]
            if violation["kind"] == "english-command-ascii-adjacency"
        }
        self.assertEqual(
            {f"hint:{key}" for key, _line in occurrences},
            blocker_identities,
        )
        self.assertEqual(13, len(blocker_identities))

    def test_unknown_command_and_lua_syntax_mutations_are_blocking(self):
        mutations = (
            (
                "$cmd[CMD_DISPLAY_COMMANDS]",
                "$cmd[CMD_NOT_A_COMMAND]",
                "chinese-unknown-commands",
            ),
            (
                "crawl.t_(you.class()) }}</w>",
                "crawl.t_(you.class()) </w>",
                "chinese-lua-errors",
            ),
        )
        for old, new, kind in mutations:
            with self.subTest(kind=kind):
                blobs = dict(self.blobs)
                blobs[MODULE.HINTS_ZH] = blobs[MODULE.HINTS_ZH].decode(
                    "utf-8"
                ).replace(old, new, 1).encode("utf-8")
                payload = MODULE.build_payload_from_blobs(BASELINE, blobs)
                self.assertTrue(any(
                    violation["kind"] == kind
                    for violation in payload["blocking_violations"]
                ))

    def test_review_coverage_accepts_one_canonical_card_per_identity(self):
        review = audit_input(render_review(self.payload))
        result = MODULE.review_coverage(self.payload, review)
        self.assertTrue(result["coverage_equal"])
        self.assertEqual(
            len(self.payload["inventory"]), result["evidence_card_count"]
        )
        self.assertEqual([], result["inventory_minus_review"])
        self.assertEqual([], result["review_minus_inventory"])
        self.assertTrue(result["canonical_card_order"])

    def test_review_coverage_rejects_duplicates_order_and_fact_mutation(self):
        def mutate(cards):
            cards[0]["fact_sha256"] = "0" * 64
            cards.append(cards.pop(1))
            cards.append(cards[0].copy())

        result = MODULE.review_coverage(
            self.payload, audit_input(render_review(self.payload, mutate=mutate))
        )
        self.assertFalse(result["coverage_equal"])
        self.assertTrue(result["duplicate_evidence_cards"])
        self.assertFalse(result["canonical_card_order"])
        self.assertIn(
            f"{self.payload['inventory'][0]['identity']}:fact_sha256",
            result["mismatched_mechanical_fields"],
        )

    def test_review_parser_requires_canonical_json(self):
        text = render_review(self.payload)
        metadata_line = text.splitlines()[1]
        noncanonical = text.replace(
            metadata_line,
            json.dumps(json.loads(metadata_line), ensure_ascii=False),
            1,
        )
        with self.assertRaisesRegex(RuntimeError, "not canonical JSON"):
            MODULE.parse_review(audit_input(noncanonical))

    def test_deferral_requires_reason_owner_and_reentry_trigger(self):
        identity = self.payload["inventory"][0]["identity"]

        def incomplete(cards):
            cards[0]["terminal_conclusion"] = "defer implementation"
            cards[0]["deferral_reason"] = "TBD"
            cards[0]["deferral_owner"] = "none"
            cards[0]["reentry_trigger"] = "unknown"

        invalid = MODULE.review_coverage(
            self.payload, audit_input(render_review(self.payload, mutate=incomplete))
        )
        self.assertFalse(invalid["coverage_equal"])
        for field in ("deferral_reason", "deferral_owner", "reentry_trigger"):
            self.assertIn(f"{identity}:{field}", invalid["invalid_cards"])

        def complete(cards):
            cards[0]["terminal_conclusion"] = "defer implementation"
            cards[0]["deferral_reason"] = (
                "The display consumer requires a separately assigned code change."
            )
            cards[0]["deferral_owner"] = "Issue #50 implementation owner"
            cards[0]["reentry_trigger"] = (
                "Re-enter after the assigned display-consumer patch is committed."
            )

        valid = MODULE.review_coverage(
            self.payload, audit_input(render_review(self.payload, mutate=complete))
        )
        self.assertTrue(valid["coverage_equal"])

    def test_baseline_blockers_remain_visible_and_block_same_commit(self):
        self.assertEqual(
            BASELINE_INVENTORY_SHA256, self.payload["inventory_sha256"]
        )
        self.assertTrue(self.payload["blocking_violations"])
        self.assertEqual(18, len(self.payload["blocking_violations"]))
        self.assertEqual(17, len({
            violation["identity"]
            for violation in self.payload["blocking_violations"]
        }))
        review = audit_input(render_review(self.payload))
        agreement = MODULE.candidate_agreement(self.payload, review, BASELINE)
        self.assertFalse(agreement["candidate_agrees"])
        self.assertEqual([], agreement["translation_mismatches"])
        self.assertEqual(
            self.payload["blocking_violations"],
            agreement["candidate_integrity"]["candidate_blocking_violations"],
        )
        self.assertFalse(
            agreement["candidate_integrity"]["integrity_matches"]
            ["blocking_violations"]
        )

    def test_candidate_integrity_rejects_blocker_identity_and_glossary_drift(self):
        fixtures = []

        blocker = copy.deepcopy(self.clean_candidate)
        blocker["blocking_violations"] = [{
            "identity": "hint:welcome",
            "kind": "fixture-blocker",
            "detail": "one candidate token blocker",
        }]
        fixtures.append(("blocking_violations", blocker))

        identity = copy.deepcopy(self.clean_candidate)
        identity["union_keys"] = identity["union_keys"] + ["fixture identity"]
        fixtures.append(("identity_set", identity))

        glossary = copy.deepcopy(self.clean_candidate)
        glossary["glossary_sha256"] = "0" * 64
        fixtures.append(("glossary_sha256", glossary))

        for field, candidate in fixtures:
            with self.subTest(field=field):
                integrity = MODULE.candidate_integrity(self.payload, candidate)
                self.assertFalse(integrity["integrity_equal"])
                self.assertFalse(integrity["integrity_matches"][field])

    def test_clean_candidate_closes_integrity_agreement_and_cli_status(self):
        self.assertEqual([], self.clean_candidate["blocking_violations"])
        review = audit_input(render_candidate_review(
            self.payload, self.clean_candidate
        ))
        candidate = self.clean_candidate["baseline"]
        with mock.patch.object(
            MODULE, "build_payload", return_value=self.clean_candidate
        ) as rebuild:
            agreement = MODULE.candidate_agreement(
                self.payload, review, candidate
            )
        rebuild.assert_called_once_with(candidate)
        self.assertTrue(agreement["candidate_integrity"]["integrity_equal"])
        self.assertTrue(agreement["candidate_agrees"])
        self.assertEqual([], agreement["translation_mismatches"])

        cli_payload = copy.deepcopy(self.payload)
        cli_payload["review_coverage"] = MODULE.review_coverage(
            self.payload, review
        )
        cli_payload["candidate_agreement"] = agreement
        self.assertEqual(0, MODULE._result_exit_code(cli_payload))

        blocked_cli = copy.deepcopy(cli_payload)
        blocked_cli["candidate_agreement"]["candidate_agrees"] = False
        self.assertEqual(1, MODULE._result_exit_code(blocked_cli))

    def test_candidate_translation_mismatch_still_fails_agreement(self):
        review = audit_input(render_candidate_review(
            self.payload, self.clean_candidate
        ))
        candidate = copy.deepcopy(self.clean_candidate)
        first = candidate["inventory"][0]
        first["chinese"] = "fixture value absent from the review ledger"
        mismatch = MODULE.candidate_agreement_from_payload(
            self.payload, review, candidate
        )
        self.assertFalse(mismatch["candidate_agrees"])
        self.assertEqual(
            [self.payload["inventory"][0]["identity"]],
            mismatch["translation_mismatches"],
        )

    def test_exact_baseline_manifest_and_trusted_git_are_reused(self):
        self.assertEqual(BASELINE, MODULE.resolve_commit(BASELINE))
        for path in MODULE.INPUT_PATHS:
            expected = hashlib.sha256(
                MODULE.git_show_blob(BASELINE, path)
            ).hexdigest()
            self.assertEqual(expected, self.payload["inputs"][path]["sha256"])

        with mock.patch.dict(
            os.environ,
            {"GIT_DIR": "/tmp/untrusted-git-dir", "GIT_WORK_TREE": "/tmp"},
        ):
            env = MODULE.trusted_git_environment()
            self.assertNotIn("GIT_DIR", env)
            self.assertNotIn("GIT_WORK_TREE", env)
            self.assertEqual("1", env["GIT_NO_REPLACE_OBJECTS"])
            self.assertEqual(BASELINE, MODULE.resolve_commit(BASELINE))

    def test_manifest_and_output_safety_fail_closed(self):
        blobs = dict(self.blobs)
        blobs.pop(MODULE.HINTS_H)
        with self.assertRaisesRegex(RuntimeError, "manifest mismatch"):
            MODULE.build_payload_from_blobs(BASELINE, blobs)

        with tempfile.NamedTemporaryFile(
            prefix="hint-inventory-existing-", suffix=".json", dir="/tmp"
        ) as existing:
            with self.assertRaises(SystemExit):
                MODULE.write_inventory_output(existing.name, "{}")
        with tempfile.TemporaryDirectory(
            prefix="hint-inventory-nested-", dir="/tmp"
        ) as nested:
            with self.assertRaises(SystemExit):
                MODULE.write_inventory_output(str(Path(nested) / "new.json"), "{}")


if __name__ == "__main__":
    unittest.main()
