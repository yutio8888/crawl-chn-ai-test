#!/usr/bin/env python3

from __future__ import annotations

import copy
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/wpnnoise_inventory.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("wpnnoise_inventory", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

# Issue #60 frozen baseline boundary.  The tool accepts --baseline-ref at
# runtime; the tests pin the boundary the inventory freezes.  The candidate
# ref must be a real commit that is never equal to the baseline (HEAD^^ is
# the pre-baseline commit while HEAD is the baseline before the tooling
# commit lands, and the tooling commit afterwards).
BASELINE = "7b56bccf9ce06646b65acf056b1445ad2999512d"
CANDIDATE = subprocess.run(
    ["git", "-C", str(ROOT), "rev-parse", "HEAD^^"],
    check=True, text=True, capture_output=True,
).stdout.strip()


def exact_artifact(oid: str, directory: str) -> dict:
    scoped = MODULE.shared._derive_scoped_dump(
        oid, directory, f"fixture {directory}",
        source_basename=MODULE.SOURCE_BASENAME,
    )
    return {
        "schema_version": 1,
        "database_name": "speak",
        "source_directory": directory,
        "sources": copy.deepcopy(scoped["sources"]),
        "entries": copy.deepcopy(scoped["entries"]),
    }


def derived_of(artifact: dict) -> dict:
    source = f"{artifact['source_directory']}{MODULE.SOURCE_BASENAME}"
    return {
        "sources": copy.deepcopy(artifact["sources"]),
        "entries": [
            copy.deepcopy(entry) for entry in artifact["entries"]
            if any(item["source_name"] == source
                   for item in entry["source_history"])
        ],
    }


def metadata_for(inventory: dict, counts: dict[str, int] | None = None) -> dict:
    counts = counts or {"keep": len(inventory["entries"])}
    return {
        "baseline": inventory["baseline_ref"],
        "chinese_production_dump_sha256":
            inventory["dumps"]["localized"]["artifact_sha256"],
        "en_lua_site_count": MODULE.EXPECTED_EN_LUA_SITES,
        "en_random_site_count": MODULE.EXPECTED_EN_RANDOM_SITES,
        "en_variant_count": MODULE.EXPECTED_EN_VARIANT_COUNT,
        "english_production_dump_sha256":
            inventory["dumps"]["english"]["artifact_sha256"],
        "glossary_sha256": inventory["glossary"]["sha256"],
        "identity_count": len(inventory["entries"]),
        "inventory_sha256": inventory["inventory_sha256"],
        "terminal_conclusion_counts": dict(sorted(counts.items())),
        "zh_lua_site_count": MODULE.EXPECTED_ZH_LUA_SITES,
        "zh_random_site_count": MODULE.EXPECTED_ZH_RANDOM_SITES,
        "zh_variant_count": MODULE.EXPECTED_ZH_VARIANT_COUNT,
    }


def card_for(
    inventory: dict, entry: dict, conclusion: str = "keep",
    variant_override: dict[int, tuple[str, str]] | None = None,
) -> dict:
    """Synthetic strict review card bound to the exact baseline inventory."""
    variant_override = variant_override or {}
    frozen = MODULE._frozen_route_evidence(entry)
    current_en = [variant["raw_pattern"] for variant in entry["english_variants"]]
    current_zh = [variant["chinese"] for variant in entry["variants"]]
    proposed = list(current_zh)
    reviews = []
    for variant in entry["variants"]:
        ordinal = variant["locator"]["variant_ordinal"]
        override = variant_override.get(ordinal)
        variant_conclusion, variant_proposal = (
            override if override is not None else ("keep", variant["chinese"])
        )
        if variant_conclusion == "keep":
            variant_proposal = variant["chinese"]
        proposed[ordinal] = variant_proposal
        review = {
            "variant_ordinal": ordinal,
            "weight": variant["weight"],
            "control_prefix": variant["control_prefix"],
            "runtime_tokens": variant["runtime_tokens"],
            "random_site_counts": variant["random_site_counts"],
            "lua_site_count": variant["lua_site_count"],
            "lua_comparison_strings": variant["lua_comparison_strings"],
            "english": variant["english"],
            "current_chinese": variant["chinese"],
            "proposed_translation": variant_proposal,
            "terminal_conclusion": variant_conclusion,
            "rationale": "完整审阅并保留。" if variant_conclusion == "keep"
            else "已核对生产消费者语义并确认改译。",
        }
        if variant_conclusion in MODULE.DEFER_CONCLUSIONS:
            review.update({
                "deferral_owner": "translation-reviewer",
                "deferral_reason": "需要人工确认术语与语气。",
                "reentry_trigger": "术语裁定或上下文证据出现后重新审阅。",
            })
        reviews.append(review)
    card = {
        "identity": entry["identity"],
        "key": entry["key"],
        "lifecycle": entry["lifecycle"],
        "terminal_conclusion": conclusion,
        "deferral_owner": None,
        "deferral_reason": None,
        "confidence": "high",
        "dependency_group": entry["dependency_group"],
        "glossary_authority": (
            f"{inventory['glossary']['path']}@{inventory['glossary']['sha256']}"
        ),
        "actual_behavior": frozen["actual_behavior"],
        "display_context": frozen["display_context"],
        "consumer": copy.deepcopy(frozen["consumer"]),
        "producers": copy.deepcopy(frozen["producers"]),
        "evidence_locations": list(entry["evidence_locations"]),
        "production_facts": MODULE._expected_production_facts(inventory, entry),
        "reentry_trigger": MODULE.REENTRY_TRIGGER,
        "rejected_alternatives": ["不改变 lookup、权重、控制、token 或拓扑协议。"],
        "reviewer_rationale": "已核对生产来源、消费者、变体与配对证据。",
        "current_english": current_en,
        "current_chinese": current_zh,
        "proposed_translation": proposed,
        "variant_reviews": reviews,
    }
    if conclusion in MODULE.DEFER_CONCLUSIONS:
        card.update({
            "deferral_owner": "translation-reviewer",
            "deferral_reason": "需要人工确认术语与语气。",
        })
    return card


class WpnnoiseInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.en_artifact = exact_artifact(BASELINE, "database/")
        cls.zh_artifact = exact_artifact(BASELINE, "database/zh/")
        cls.en_path = cls.root / "en.json"
        cls.zh_path = cls.root / "zh.json"
        cls.en_path.write_text(
            json.dumps(cls.en_artifact, ensure_ascii=False), encoding="utf-8"
        )
        cls.zh_path.write_text(
            json.dumps(cls.zh_artifact, ensure_ascii=False), encoding="utf-8"
        )
        cls.inventory = MODULE.build_inventory(
            BASELINE, cls.en_path, cls.zh_path, ROOT / "docs/glossary.md"
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def write_records(self, records: list[dict]) -> Path:
        path = self.root / f"results-{self.id().split('.')[-1]}.md"
        path.write_text(
            "fixture\n\n" + MODULE.STRICT_BEGIN + "\n```jsonl\n"
            + "\n".join(
                json.dumps(record, ensure_ascii=False, sort_keys=True)
                for record in records
            )
            + "\n```\n" + MODULE.STRICT_END + "\n",
            encoding="utf-8",
        )
        return path

    def validate(self, records: list[dict], candidate=None):
        return MODULE.validate_results(
            self.write_records(copy.deepcopy(records)), self.inventory, candidate
        )

    def all_cards(self) -> list[dict]:
        return [card_for(self.inventory, entry) for entry in self.inventory["entries"]]

    def bind_rejected(self, artifact: dict, directory: str, contains: str):
        path = self.root / f"bad-{self.id().split('.')[-1]}.json"
        path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")
        label = "fixture EN" if directory == "database/" else "fixture ZH"
        with self.assertRaisesRegex(MODULE.InventoryError, contains):
            dump, raw = MODULE.shared._load_dump(path, label, directory)
            MODULE._dump_binding(dump, raw, label)

    # ── exact-Git inventory shape ─────────────────────────────────────────

    def test_exact_git_inventory_binds_frozen_shape_and_is_deterministic(self):
        first = self.inventory
        second_en = self.root / "en2.json"
        second_zh = self.root / "zh2.json"
        second_en.write_bytes(self.en_path.read_bytes())
        second_zh.write_bytes(self.zh_path.read_bytes())
        rebuilt = MODULE.build_inventory(
            BASELINE, second_en, second_zh, ROOT / "docs/glossary.md"
        )
        self.assertEqual(first["inventory_sha256"], rebuilt["inventory_sha256"])
        self.assertEqual(MODULE.EXPECTED_IDENTITY_COUNT, len(first["entries"]))
        self.assertEqual(
            MODULE.EXPECTED_EN_VARIANT_COUNT,
            sum(entry["en_variant_count"] for entry in first["entries"]),
        )
        self.assertEqual(
            MODULE.EXPECTED_ZH_VARIANT_COUNT,
            sum(entry["zh_variant_count"] for entry in first["entries"]),
        )
        self.assertEqual(
            MODULE.EXPECTED_EN_RANDOM_SITES,
            sum(len(variant["random_site_counts"])
                for entry in first["entries"]
                for variant in entry["english_variants"]),
        )
        self.assertEqual(
            MODULE.EXPECTED_ZH_RANDOM_SITES,
            sum(len(variant["random_site_counts"])
                for entry in first["entries"]
                for variant in entry["variants"]),
        )
        self.assertEqual(
            MODULE.EXPECTED_EN_LUA_SITES,
            sum(variant["lua_site_count"]
                for entry in first["entries"]
                for variant in entry["english_variants"]),
        )
        self.assertEqual(
            MODULE.EXPECTED_ZH_LUA_SITES,
            sum(variant["lua_site_count"]
                for entry in first["entries"]
                for variant in entry["variants"]),
        )
        roots = {
            entry["key"] for entry in first["entries"]
            if entry["lifecycle"] == "direct-production-root"
        }
        fragments = {
            entry["key"] for entry in first["entries"]
            if entry["lifecycle"] == "recursive-internal-fragment"
        }
        self.assertEqual(set(MODULE.ROOT_KEYS), roots)
        self.assertEqual(65, len(roots | fragments))
        self.assertTrue(fragments.isdisjoint(roots))
        for entry in first["entries"]:
            self.assertIn(entry["key"], MODULE.DEPENDENCY_GROUP)

    def test_lua_comparison_strings_are_frozen_protocol(self):
        comparisons = {
            comparison
            for entry in self.inventory["entries"]
            for variant in entry["variants"]
            for comparison in variant["lua_comparison_strings"]
        } | {
            comparison
            for entry in self.inventory["entries"]
            for variant in entry["english_variants"]
            for comparison in variant["lua_comparison_strings"]
        }
        self.assertEqual(set(MODULE.LUA_COMPARISON_STRINGS), comparisons)

    def test_asymmetric_and_one_sided_variants_are_frozen_facts(self):
        by_key = {entry["key"]: entry for entry in self.inventory["entries"]}
        for key, (en_count, zh_count) in MODULE.ASYMMETRIC_VARIANT_KEYS.items():
            with self.subTest(key=key):
                entry = by_key[key]
                self.assertEqual(en_count, entry["en_variant_count"])
                self.assertEqual(zh_count, entry["zh_variant_count"])
        high = by_key["_speaking_high_tension_"]
        self.assertEqual([32], high["zh_only_variant_ordinals"])
        self.assertEqual([], high["en_only_variant_ordinals"])
        self.assertIsNone(high["variants"][32]["english"])
        self.assertEqual(0, high["variants"][32]["lua_site_count"])
        self.assertEqual([], high["variants"][32]["lua_comparison_strings"])
        self.assertEqual(1, high["variants"][1]["lua_site_count"])
        self.assertEqual(["No God"],
                         high["variants"][1]["lua_comparison_strings"])
        scream = by_key["_scream_"]
        self.assertEqual([70], scream["en_only_variant_ordinals"])
        self.assertEqual([], scream["zh_only_variant_ordinals"])
        fungus = by_key["fungus thoughts"]
        self.assertEqual(list(range(7, 14)), fungus["en_only_variant_ordinals"])
        self.assertEqual([], fungus["zh_only_variant_ordinals"])
        instrumental = by_key["_instrumental_noises_"]
        self.assertEqual([12], instrumental["en_only_variant_ordinals"])

    def test_recursive_closure_reachability_is_proven_not_assumed(self):
        for entry in self.inventory["entries"]:
            if entry["lifecycle"] == "recursive-internal-fragment":
                sites = entry["referencing_sites"]
                self.assertTrue(
                    sites["english"] or sites["chinese"],
                    f"{entry['key']} fragment has no referencing site",
                )
        root_keys = {entry["key"] for entry in self.inventory["entries"]
                     if entry["lifecycle"] == "direct-production-root"}
        self.assertEqual(28, len(root_keys))
        self.assertEqual(37, 65 - 28)

    # ── malicious refs, paths, types ─────────────────────────────────────

    def test_malicious_git_paths_and_refs_fail_closed(self):
        for bad in ("../database/wpnnoise.txt", "/etc/passwd",
                    "database/./wpnnoise.txt"):
            with self.subTest(path=bad):
                with self.assertRaisesRegex(MODULE.InventoryError, "unsafe Git path"):
                    MODULE.shared._git_blob_at_oid(BASELINE, bad, "fixture")
        with self.assertRaisesRegex(MODULE.InventoryError, "full lowercase OID"):
            MODULE.shared._validate_oid("ABCDEF" * 6 + "abcd", "fixture")
        with self.assertRaisesRegex(MODULE.InventoryError, "not a commit"):
            MODULE.shared._validate_oid("0" * 40, "fixture")

    def test_source_manifest_parsing_fails_closed(self):
        def tree_record(mode: bytes, kind: bytes, name: bytes) -> bytes:
            return mode + b" " + kind + b" " + b"1" * 40 + b"\t" + name + b"\0"

        tree = b"".join([
            tree_record(b"100644", b"blob", b"wpnnoise.txt"),
            tree_record(b"040000", b"tree", b"nested"),
            tree_record(b"120000", b"blob", b"linked.txt"),
        ])
        with mock.patch.object(MODULE.shared, "_git_output", return_value=tree):
            with self.assertRaisesRegex(MODULE.InventoryError, "unsupported tree"):
                MODULE.shared._localized_source_manifest(BASELINE, "ZH fixture")

        with mock.patch.object(
            MODULE.shared, "_git_blob_at_oid",
            return_value=b'TextDB("speak", "database/", { "a.txt", "a.txt", })',
        ):
            with self.assertRaisesRegex(MODULE.InventoryError, "duplicate SpeakDB"):
                MODULE.shared._english_source_manifest(BASELINE, "EN fixture")
        with mock.patch.object(
            MODULE.shared, "_git_blob_at_oid",
            return_value=b'TextDB("speak", "database/", { "evil.txt; rm -rf /" })',
        ):
            with self.assertRaisesRegex(MODULE.InventoryError, "unsafe SpeakDB"):
                MODULE.shared._english_source_manifest(BASELINE, "EN fixture")

    def test_artifact_objects_reject_unknown_fields_and_boolean_integers(self):
        cases = (
            ("unknown field", lambda value: value.__setitem__("unknown", None),
             "field set mismatch"),
            ("schema boolean",
             lambda value: value.__setitem__("schema_version", True),
             "must be an integer"),
            ("source index boolean",
             lambda value: value["sources"][0].__setitem__("load_index", False),
             "must be an integer"),
            ("variant ordinal boolean",
             lambda value: value["entries"][0]["variants"][0][
                 "locator"
             ].__setitem__("variant_ordinal", False),
             "must be an integer"),
            ("weight boolean",
             lambda value: value["entries"][0]["variants"][0].__setitem__(
                 "weight", True),
             "must be an integer"),
        )
        for name, mutate, message in cases:
            bad = copy.deepcopy(self.en_artifact)
            mutate(bad)
            with self.subTest(case=name):
                self.bind_rejected(bad, "database/", message)

    def test_override_provenance_parse_error_and_ordinal_gap_fail(self):
        bad = copy.deepcopy(self.en_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "noisy weapon"
        )
        other_prov = {"source_name": "database/insult.txt", "load_index": 4,
                      "definition_ordinal": 0}
        entry["source_history"].append(other_prov)
        entry["effective_provenance"] = other_prov
        for variant in entry["variants"]:
            variant["provenance"] = other_prov
        self.bind_rejected(bad, "database/", "overridden")

        bad = copy.deepcopy(self.en_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "noisy weapon"
        )
        entry["effective_provenance"]["definition_ordinal"] = 4
        for variant in entry["variants"]:
            variant["provenance"]["definition_ordinal"] = 4
        self.bind_rejected(bad, "database/", "not contiguous")

        bad = copy.deepcopy(self.en_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "noisy weapon"
        )
        entry["parse_error"] = "BUG, WEIGHT AT END OF ENTRY"
        entry["variants"] = []
        self.bind_rejected(bad, "database/", "parse error")

        bad = copy.deepcopy(self.en_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "noisy weapon"
        )
        entry["variants"][0]["raw_pattern"] = "BOGUS:broken pattern"
        self.bind_rejected(bad, "database/", "unrecognized control")

        bad = copy.deepcopy(self.zh_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "_speaking_high_tension_"
        )
        entry["variants"][1]["raw_pattern"] = (
            entry["variants"][1]["raw_pattern"].replace("}}", "")
        )
        self.bind_rejected(bad, "database/zh/", "unbalanced Lua")

        bad = copy.deepcopy(self.zh_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "eel hand solo actions"
        )
        entry["variants"][0]["raw_pattern"] = (
            entry["variants"][0]["raw_pattern"].replace("]", "")
        )
        self.bind_rejected(bad, "database/zh/", "unbalanced random")

    def test_frozen_counts_drift_is_rejected(self):
        renamed = copy.deepcopy(self.en_artifact)
        entry = next(
            entry for entry in renamed["entries"]
            if entry["canonical_key"] == "weapon_noises"
        )
        entry["canonical_key"] = "weapon_noises_renamed"
        for variant in entry["variants"]:
            variant["locator"]["canonical_key"] = entry["canonical_key"]
        self.bind_rejected(renamed, "database/", "key set mismatch")

        trimmed = copy.deepcopy(self.zh_artifact)
        entry = next(
            entry for entry in trimmed["entries"]
            if entry["canonical_key"] == "_scream_"
        )
        entry["variants"].pop()
        self.bind_rejected(trimmed, "database/zh/", "variant count mismatch")

    # ── review results: completeness, conclusions, metadata ──────────────

    def test_completeness_equality_all_cards_pass(self):
        records = [metadata_for(self.inventory), *self.all_cards()]
        loaded = self.validate(records)
        self.assertEqual(65, len(loaded["cards"]))
        self.assertEqual(
            {"keep": 65}, loaded["metadata"]["terminal_conclusion_counts"]
        )

    def test_completeness_equality_rejects_missing_extra_and_duplicate_cards(self):
        cards = self.all_cards()
        with self.assertRaisesRegex(MODULE.InventoryError, "coverage mismatch"):
            self.validate([metadata_for(self.inventory), *cards[:-1]])
        with self.assertRaisesRegex(MODULE.InventoryError, "coverage mismatch"):
            self.validate([metadata_for(self.inventory), *cards,
                           copy.deepcopy(cards[0])])
        replaced = copy.deepcopy(cards)
        replaced[0]["identity"] = "wpnnoise:not a real key"
        replaced[0]["key"] = "not a real key"
        with self.assertRaisesRegex(MODULE.InventoryError, "identity set mismatch"):
            self.validate([metadata_for(self.inventory), *replaced])
        duplicate = [metadata_for(self.inventory), cards[0],
                     copy.deepcopy(cards[0]), *cards[2:]]
        with self.assertRaisesRegex(MODULE.InventoryError, "duplicate review card"):
            self.validate(duplicate)

    def test_review_card_order_and_field_set_fail_closed(self):
        cards = self.all_cards()
        cards[0], cards[1] = cards[1], cards[0]
        with self.assertRaisesRegex(MODULE.InventoryError, "identity order mismatch"):
            self.validate([metadata_for(self.inventory), *cards])
        cards = self.all_cards()
        del cards[5]["production_facts"]
        with self.assertRaisesRegex(MODULE.InventoryError, "production_facts"):
            self.validate([metadata_for(self.inventory), *cards])

    def test_review_metadata_bindings_fail_closed(self):
        metadata = metadata_for(self.inventory)
        metadata["baseline"] = "0" * 40
        with self.assertRaisesRegex(MODULE.InventoryError, "baseline mismatch"):
            self.validate([metadata, *self.all_cards()])
        metadata = metadata_for(self.inventory)
        metadata["inventory_sha256"] = "0" * 64
        with self.assertRaisesRegex(MODULE.InventoryError, "inventory_sha256"):
            self.validate([metadata, *self.all_cards()])
        metadata = metadata_for(self.inventory)
        metadata["english_production_dump_sha256"] = "0" * 64
        with self.assertRaisesRegex(
            MODULE.InventoryError, "english_production_dump_sha256"
        ):
            self.validate([metadata, *self.all_cards()])
        metadata = metadata_for(self.inventory)
        metadata["zh_variant_count"] += 1
        with self.assertRaisesRegex(MODULE.InventoryError, "variant counts"):
            self.validate([metadata, *self.all_cards()])
        metadata = metadata_for(self.inventory)
        metadata["terminal_conclusion_counts"] = {"keep": 64, "adjust": 1}
        with self.assertRaisesRegex(
            MODULE.InventoryError, "terminal_conclusion_counts"
        ):
            self.validate([metadata, *self.all_cards()])

    def test_review_conclusion_semantics_and_deferral_fields(self):
        cards = self.all_cards()
        cards[0]["variant_reviews"][0]["terminal_conclusion"] = "pending"
        with self.assertRaisesRegex(MODULE.InventoryError, "nonterminal"):
            self.validate([metadata_for(self.inventory), *cards])

        cards = self.all_cards()
        card = cards[0]
        card["terminal_conclusion"] = "adjust"
        card["variant_reviews"][0]["terminal_conclusion"] = "adjust"
        card["variant_reviews"][0]["proposed_translation"] += "（调整）"
        card["proposed_translation"][0] = (
            card["variant_reviews"][0]["proposed_translation"]
        )
        records = [metadata_for(self.inventory, {"keep": 64, "adjust": 1}), *cards]
        loaded = self.validate(records)
        self.assertEqual("adjust", loaded["cards"][0]["terminal_conclusion"])

        # adjust without a changed proposal is rejected.
        cards = self.all_cards()
        card = cards[0]
        card["terminal_conclusion"] = "adjust"
        card["variant_reviews"][0]["terminal_conclusion"] = "adjust"
        with self.assertRaisesRegex(MODULE.InventoryError, "must change"):
            self.validate([metadata_for(self.inventory), *cards])

        # defer terminology requires owner/reason/reentry at card and variant.
        cards = self.all_cards()
        card = cards[0]
        card["terminal_conclusion"] = "defer terminology"
        card["deferral_owner"] = "translation-reviewer"
        card["deferral_reason"] = "术语待裁定。"
        card["reentry_trigger"] = "术语裁定后重新审阅。"
        review = card["variant_reviews"][0]
        review["terminal_conclusion"] = "defer terminology"
        review.update({
            "deferral_owner": "translation-reviewer",
            "deferral_reason": "术语待裁定。",
            "reentry_trigger": "术语裁定后重新审阅。",
        })
        records = [metadata_for(
            self.inventory, {"keep": 64, "defer terminology": 1}), *cards]
        self.validate(records)
        del review["deferral_owner"]
        with self.assertRaisesRegex(MODULE.InventoryError, "deferral_owner"):
            self.validate([metadata_for(self.inventory), *cards])

    def test_variant_review_protocol_facts_fail_closed(self):
        cards = self.all_cards()
        card = next(card for card in cards if card["key"] == "noisy weapon")
        card["variant_reviews"][3]["weight"] = 21
        with self.assertRaisesRegex(MODULE.InventoryError, "weight mismatch"):
            self.validate([metadata_for(self.inventory), *cards])
        cards = self.all_cards()
        card = next(card for card in cards
                    if card["key"] == "singing sword silenced")
        card["variant_reviews"][0]["control_prefix"] = "SOUND"
        with self.assertRaisesRegex(MODULE.InventoryError, "control_prefix mismatch"):
            self.validate([metadata_for(self.inventory), *cards])
        cards = self.all_cards()
        card = next(card for card in cards
                    if card["key"] == "_speaking_high_tension_")
        card["variant_reviews"][32]["lua_comparison_strings"] = ["Zin"]
        with self.assertRaisesRegex(
            MODULE.InventoryError, "lua_comparison_strings mismatch"
        ):
            self.validate([metadata_for(self.inventory), *cards])

    def test_production_facts_cover_tokens_sites_lua_and_pairing(self):
        by_key = {entry["key"]: entry for entry in self.inventory["entries"]}
        noisy = MODULE._expected_production_facts(self.inventory,
                                                  by_key["noisy weapon"])
        self.assertEqual([], noisy["caller_tokens"])
        for token in ("@_weapon_chatter_@", "@weapon_noises@",
                      "@_instrumental_noises_@", "@weapon_noise@"):
            self.assertIn(token, noisy["recursive_tokens"])
        self.assertEqual([None, None, None, "SOUND"],
                         noisy["control_prefixes"]["english"])

        noises = MODULE._expected_production_facts(self.inventory,
                                                   by_key["weapon_noises"])
        self.assertEqual(["@Your_weapon@"], noises["caller_tokens"])
        self.assertEqual([], noises["recursive_tokens"])
        self.assertEqual([], noises["en_only_variant_ordinals"])
        self.assertEqual(24, noises["en_variant_count"])
        self.assertEqual(24, noises["zh_variant_count"])
        self.assertEqual(noises["weights"]["english"],
                         noises["weights"]["chinese"])

        eel = MODULE._expected_production_facts(self.inventory,
                                                by_key["eel hand solo actions"])
        self.assertEqual([2], eel["random_site_counts"]["chinese"][0])
        self.assertEqual(20, eel["weights"]["chinese"][0])

        high = MODULE._expected_production_facts(
            self.inventory, by_key["_speaking_high_tension_"])
        self.assertIn("lua", high["pairing_protocol_differences"][3])
        self.assertIn("lua", high["pairing_protocol_differences"][4])
        self.assertEqual([], high["pairing_protocol_differences"][32])
        self.assertIn("@_godless_sorter_@", high["recursive_tokens"])
        self.assertIn("@player_god@", high["caller_tokens"])

    # ── candidate binding ────────────────────────────────────────────────

    def add_candidate(self, en: dict, zh: dict,
                      candidate_ref: str = CANDIDATE) -> list[dict]:
        en_path = self.root / f"candidate-en-{self.id().split('.')[-1]}.json"
        zh_path = self.root / f"candidate-zh-{self.id().split('.')[-1]}.json"
        en_path.write_text(json.dumps(en, ensure_ascii=False), encoding="utf-8")
        zh_path.write_text(json.dumps(zh, ensure_ascii=False), encoding="utf-8")
        real_derive = MODULE.shared._derive_scoped_dump

        def fake_derive(oid, directory, label, source_basename=None):
            if oid == candidate_ref:
                artifact = en if directory == "database/" else zh
                return derived_of(artifact)
            return real_derive(oid, directory, label,
                               source_basename=source_basename)

        with mock.patch.object(MODULE.shared, "_require_candidate_commit"), \
                mock.patch.object(
                    MODULE.shared, "_derive_scoped_dump", side_effect=fake_derive,
                ):
            return MODULE.add_candidate(self.inventory, candidate_ref,
                                        en_path, zh_path)

    @staticmethod
    def zh_variant(artifact: dict, key: str, ordinal: int) -> dict:
        entry = next(
            entry for entry in artifact["entries"]
            if entry["canonical_key"] == key
        )
        return entry["variants"][ordinal]

    def mutated_zh(self, key: str, ordinal: int, mutator) -> dict:
        artifact = copy.deepcopy(self.zh_artifact)
        mutator(self.zh_variant(artifact, key, ordinal))
        return artifact

    def test_candidate_exact_zh_binding_and_english_no_drift(self):
        identity = "wpnnoise:_speaking_high_tension_"
        entry = next(
            entry for entry in self.inventory["entries"]
            if entry["identity"] == identity
        )
        new_text = entry["variants"][0]["chinese"] + "（候选改译）"
        candidate_zh = self.mutated_zh(
            "_speaking_high_tension_", 0,
            lambda variant: variant.__setitem__("raw_pattern", new_text),
        )
        candidate_entries = self.add_candidate(self.en_artifact, candidate_zh)
        candidate = next(
            entry for entry in candidate_entries
            if entry["identity"] == identity
        )
        self.assertEqual(new_text, candidate["variants"][0]["chinese"])

        cards = self.all_cards()
        card = next(card for card in cards if card["identity"] == identity)
        card["terminal_conclusion"] = "retranslate"
        card["variant_reviews"][0]["terminal_conclusion"] = "retranslate"
        card["variant_reviews"][0]["proposed_translation"] = new_text
        card["proposed_translation"][0] = new_text
        records = [metadata_for(self.inventory, {"keep": 64, "retranslate": 1}),
                   *cards]
        loaded = self.validate(records, candidate_entries)
        loaded_card = next(
            card for card in loaded["cards"] if card["identity"] == identity
        )
        self.assertEqual(new_text, loaded_card["proposed_translation"][0])

        # A proposal that disagrees with the exact candidate ZH fails.
        bad_cards = copy.deepcopy(cards)
        bad_card = next(
            card for card in bad_cards if card["identity"] == identity
        )
        bad_card["proposed_translation"][0] = new_text + "不一致"
        bad_card["variant_reviews"][0]["proposed_translation"] = (
            new_text + "不一致"
        )
        with self.assertRaisesRegex(MODULE.InventoryError, "candidate ZH dump"):
            self.validate(
                [metadata_for(self.inventory, {"keep": 64, "retranslate": 1}),
                 *bad_cards],
                candidate_entries,
            )

    def test_candidate_english_drift_is_rejected(self):
        drift = copy.deepcopy(self.en_artifact)
        self.zh_variant(drift, "noisy weapon", 0)["raw_pattern"] += " drift"
        with self.assertRaisesRegex(MODULE.InventoryError, "English drift"):
            self.add_candidate(drift, copy.deepcopy(self.zh_artifact))

    def test_candidate_zh_protocol_drift_is_rejected(self):
        def swap_first_two_tokens(variant):
            pattern = variant["raw_pattern"]
            tokens = re.findall(r"@[^@]+@", pattern)
            first0 = pattern.find(tokens[0])
            first1 = pattern.find(tokens[1])
            t0, t1 = tokens[0], tokens[1]
            if first0 > first1:
                t0, t1 = t1, t0
                first0, first1 = first1, first0
            variant["raw_pattern"] = (
                pattern[:first0] + t1
                + pattern[first0 + len(t0):first1] + t0
                + pattern[first1 + len(t1):]
            )

        def swap_bracket_groups(variant):
            pattern = variant["raw_pattern"]
            spans = [
                (match.start(), match.end())
                for match in re.finditer(r"\[[^\[\]]*\]", pattern)
            ]
            first, second = spans[0], spans[1]
            group_a = pattern[first[0]:first[1]]
            group_b = pattern[second[0]:second[1]]
            variant["raw_pattern"] = (
                pattern[:first[0]] + group_b
                + pattern[first[1]:second[0]] + group_a
                + pattern[second[1]:]
            )

        def lua_swap_artifact():
            artifact = copy.deepcopy(self.zh_artifact)
            entry = next(
                entry for entry in artifact["entries"]
                if entry["canonical_key"] == "_speaking_high_tension_"
            )
            first, second = entry["variants"][1], entry["variants"][2]
            first["raw_pattern"], second["raw_pattern"] = (
                second["raw_pattern"], first["raw_pattern"]
            )
            return artifact

        cases = (
            ("token reorder",
             lambda: self.mutated_zh("_speaking_high_tension_", 1,
                                     swap_first_two_tokens),
             "protocol drift"),
            ("duplicate token",
             lambda: self.mutated_zh(
                 "_speaking_high_tension_", 1,
                 lambda variant: variant.__setitem__(
                     "raw_pattern",
                     variant["raw_pattern"].replace(
                         "@The_weapon@", "@The_weapon@@The_weapon@", 1))),
             "protocol drift"),
            ("weight drift",
             lambda: self.mutated_zh(
                 "eel hand solo actions", 0,
                 lambda variant: variant.__setitem__("weight", 30)),
             "protocol drift"),
            ("random-site shape drift",
             lambda: self.mutated_zh("frozen axe \"frostbite\"", 0,
                                     swap_bracket_groups),
             "protocol drift"),
            ("lua site removed", lua_swap_artifact, "protocol drift"),
            ("lua comparison drift",
             lambda: self.mutated_zh(
                 "_speaking_high_tension_", 1,
                 lambda variant: variant.__setitem__(
                     "raw_pattern",
                     variant["raw_pattern"].replace('"No God"', '"Zin"'))),
             "unknown Lua comparison string"),
        )
        for name, build, message in cases:
            with self.subTest(case=name):
                with self.assertRaisesRegex(MODULE.InventoryError, message):
                    self.add_candidate(self.en_artifact, build())

    def test_candidate_variant_count_drift_is_rejected(self):
        trimmed = copy.deepcopy(self.zh_artifact)
        entry = next(
            entry for entry in trimmed["entries"]
            if entry["canonical_key"] == "_speaking_high_tension_"
        )
        entry["variants"].pop()
        with self.assertRaisesRegex(MODULE.InventoryError, "variant count"):
            self.add_candidate(self.en_artifact, trimmed)

    # ── CLI safe output ──────────────────────────────────────────────────

    def test_cli_exclusive_tmp_output(self):
        output = Path("/tmp") / f"wpnnoise-test-{id(self)}.json"
        arguments = [
            "--baseline-ref", BASELINE,
            "--english-dump", str(self.en_path),
            "--localized-dump", str(self.zh_path),
            "--glossary", str(ROOT / "docs/glossary.md"),
            "--inventory-output", str(output),
        ]
        derive = lambda _oid, directory, _label, **kwargs: derived_of(  # noqa: E731
            self.en_artifact if directory == "database/" else self.zh_artifact
        )
        with mock.patch.object(
            MODULE.shared, "_derive_scoped_dump", side_effect=derive,
        ):
            self.assertEqual(0, MODULE.main(arguments))
            with self.assertRaisesRegex(MODULE.InventoryError, "exclusively create"):
                MODULE.main(arguments)
        output.unlink()

        outside = arguments[:-1] + [str(self.root / "out.json")]
        with mock.patch.object(
            MODULE.shared, "_derive_scoped_dump", side_effect=derive,
        ):
            with self.assertRaisesRegex(MODULE.InventoryError, "/tmp"):
                MODULE.main(outside)


if __name__ == "__main__":
    unittest.main()
