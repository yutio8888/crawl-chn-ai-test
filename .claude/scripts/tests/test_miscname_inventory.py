#!/usr/bin/env python3

from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/miscname_inventory.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("miscname_inventory", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BASELINE = "89b97ae826e1a065b9cdc9b1b715883c7eaa4d3d"


def exact_artifact(oid: str, directory: str) -> dict:
    shared = MODULE.hardened.shared
    manifest = (
        MODULE.misc_shared._misc_source_manifest(oid, f"fixture {directory}")
        if directory == "database/"
        else shared._localized_source_manifest(oid, f"fixture {directory}")
    )
    sources = []
    for load_index, source_name in enumerate(manifest):
        sources.append({
            "source_name": source_name,
            "load_index": load_index,
            "normalized_utf8": shared._source_snapshot_at_oid(
                oid, source_name, f"fixture {directory} {source_name}"
            ),
        })
    parsed = []
    provenance = {}
    histories: dict[str, list[dict]] = {}
    for source in sources:
        definitions = shared.parse_db_keys(
            source["normalized_utf8"], source["source_name"]
        )
        for ordinal, definition in enumerate(definitions):
            item = {"source_name": source["source_name"],
                    "load_index": source["load_index"],
                    "definition_ordinal": ordinal}
            parsed.append(definition)
            provenance[id(definition)] = item
            histories.setdefault(
                shared.lowercase_string(definition.raw_key), []
            ).append(item)
    effective, _overrides = shared.merge_desc_sequence(parsed)
    entries = []
    for key in sorted(effective):
        winner = effective[key]
        variants, error = shared._parse_weighted_entry(
            winner.value, provenance[id(winner)], key
        )
        entries.append({
            "canonical_key": key,
            "effective_provenance": provenance[id(winner)],
            "raw_body": winner.value,
            "source_history": histories[key],
            "variants": variants,
            "parse_error": error,
            "body_empty": winner.value == "",
        })
    return {"schema_version": 1, "database_name": "misc",
            "source_directory": directory, "sources": sources,
            "entries": entries}


def production_dump_bytes(artifact: dict) -> bytes:
    """Match the compact JSONL-free serialization emitted by the C++ dump."""
    return (json.dumps(artifact, ensure_ascii=False,
                       separators=(",", ":")) + "\n").encode("utf-8")


def card_for(entry: dict, proposed_en: list[dict] | None = None,
             proposed_zh: list[dict] | None = None) -> dict:
    proposed_en = proposed_en if proposed_en is not None else entry["english_variants"]
    proposed_zh = proposed_zh if proposed_zh is not None else entry["chinese_variants"]
    changed = MODULE._variant_digest(proposed_zh) != MODULE._variant_digest(
        entry["chinese_variants"]
    )
    return {
        "identity": entry["identity"],
        "key": entry["key"],
        "baseline_chinese_key": entry["baseline_chinese_key"],
        "lifecycle": entry["lifecycle"],
        "dependency_group": entry["dependency_group"],
        "display_context": "玩家可见 miscname TextDB 随机消息。",
        "producer_consumer": {"loader": "database.cc", "consumer": "exact Git"},
        "evidence_locations": ["crawl-ref/source/dat/database/miscname.txt"],
        "current_english_variants_sha256":
            MODULE._variant_digest(entry["english_variants"]),
        "current_chinese_variants_sha256":
            MODULE._variant_digest(entry["chinese_variants"]),
        "proposed_english_variants_sha256": MODULE._variant_digest(proposed_en),
        "proposed_chinese_variants_sha256": MODULE._variant_digest(proposed_zh),
        "terminal_conclusion": "adjust" if changed else "keep",
        "confidence": "high",
        "rationale": "逐变体核对语义、权重和运行时结构。",
        "rejected_alternatives": ["不修改英文协议键或消费者。"],
        "reentry_trigger": "miscname 源、消费者或术语权威变化时重审。",
        "deferral_owner": None,
        "deferral_reason": None,
    }


class MiscnameInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.en = exact_artifact(BASELINE, "database/")
        cls.zh = exact_artifact(BASELINE, "database/zh/")
        cls.en_path = cls.root / "en.json"
        cls.zh_path = cls.root / "zh.json"
        cls.en_path.write_text(json.dumps(cls.en, ensure_ascii=False), encoding="utf-8")
        cls.zh_path.write_text(json.dumps(cls.zh, ensure_ascii=False), encoding="utf-8")
        cls.inventory = MODULE.build_inventory(
            BASELINE, cls.en_path, cls.zh_path, ROOT / "docs/glossary.md"
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def records(self, cards: list[dict] | None = None) -> list[dict]:
        cards = cards or [card_for(entry) for entry in self.inventory["entries"]]
        return [MODULE._expected_metadata(self.inventory, cards), *cards]

    def test_inventory_is_production_derived_and_complete(self):
        self.assertEqual(
            ["_great_adj_", "_halloween_things_", "_lowly_",
             "harlequin_trap_lines", "hell_effect_noisy", "hell_effect_quiet",
             "summon_horrible_things", "welcome_spam",
             "welcome_spam dungeon descent", "welcome_spam halloween"],
            self.inventory["scope"]["identity_keys"],
        )
        self.assertEqual([], self.inventory["dumps"]["english"]["reachability"]["unreachable"])
        self.assertEqual([], self.inventory["dumps"]["localized"]["reachability"]["unreachable"])

    def test_baseline_alias_and_structural_drift_are_explicit(self):
        self.assertEqual(
            {"summon_horrible_things": "sht_int_loss"},
            self.inventory["scope"]["baseline_chinese_aliases"],
        )
        self.assertEqual(
            {"_great_adj_": [18, 17], "hell_effect_noisy": [23, 22]},
            self.inventory["scope"]["baseline_asymmetry"],
        )

    def test_consumer_and_missing_hints_lookup_are_bound(self):
        facts = self.inventory["scope"]["consumer_facts"]
        self.assertEqual("localized-key-then-english-parent", facts["fallback"])
        self.assertEqual(["welcome_spam hints"], facts["known_missing_lookups"])

    def test_changed_summon_lookup_is_rejected(self):
        original = MODULE._read_exact

        def changed(ref: str, path: str, label: str) -> str:
            text = original(ref, path, label)
            if path.endswith("spl-summoning.cc"):
                text = text.replace(
                    'getMiscString("summon_horrible_things")',
                    'getMiscString("SHT_int_loss")',
                )
            return text

        with mock.patch.object(MODULE, "_read_exact", side_effect=changed):
            with self.assertRaisesRegex(MODULE.InventoryError,
                                        "summon_horrible_things consumer"):
                MODULE._consumer_facts(BASELINE, "fixture")

    def test_changed_parent_fallback_is_rejected(self):
        original = MODULE._read_exact

        def changed(ref: str, path: str, label: str) -> str:
            text = original(ref, path, label)
            if path.endswith("database.cc"):
                text = text.replace(
                    "if (!base_only && db.translation)",
                    "if (false && db.translation)", 1,
                )
            return text

        with mock.patch.object(MODULE, "_read_exact", side_effect=changed):
            with self.assertRaisesRegex(MODULE.InventoryError,
                                        "fallback semantics changed"):
                MODULE._consumer_facts(BASELINE, "fixture")

    def test_baseline_variant_and_lua_facts(self):
        self.assertEqual(152, self.inventory["dumps"]["english"]["variant_count"])
        self.assertEqual(150, self.inventory["dumps"]["localized"]["variant_count"])
        self.assertEqual(1, self.inventory["dumps"]["english"]["lua_site_count"])
        self.assertEqual(1, self.inventory["dumps"]["localized"]["lua_site_count"])

    def test_tampered_dump_is_rejected_against_exact_git(self):
        artifact = copy.deepcopy(self.en)
        target = next(entry for entry in artifact["entries"]
                      if entry["canonical_key"] == "welcome_spam")
        target["raw_body"] += "forged"
        path = self.root / "tampered.json"
        path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")
        with self.assertRaisesRegex(Exception, "exact Git"):
            MODULE.build_inventory(BASELINE, path, self.zh_path,
                                   ROOT / "docs/glossary.md")

    def candidate_entries(self) -> list[dict]:
        result = []
        for entry in self.inventory["entries"]:
            # Structurally aligned synthetic proposal; wording is irrelevant
            # to this validator fixture and is bound by the proposal digest.
            variants = copy.deepcopy(entry["english_variants"])
            result.append({"identity": entry["identity"], "key": entry["key"],
                           "english_variants": copy.deepcopy(variants),
                           "chinese_variants": copy.deepcopy(variants)})
        return result

    def test_candidate_requires_exact_key_equality(self):
        en = {"entries": [{"key": key, "variants": []}
                          for key in sorted(MODULE.DIRECT_ROOT_KEYS
                                            | MODULE.INTERNAL_FRAGMENT_KEYS)]}
        zh = copy.deepcopy(en)
        next(item for item in zh["entries"]
             if item["key"] == "summon_horrible_things")["key"] = "sht_int_loss"
        with self.assertRaisesRegex(MODULE.InventoryError, "key sets differ"):
            MODULE._pair_candidate(en, zh)

    def test_candidate_rejects_missing_variant(self):
        entries = self.candidate_entries()
        en = {"entries": [{"key": item["key"], "variants": item["english_variants"]}
                          for item in entries]}
        zh = copy.deepcopy(en)
        next(item for item in zh["entries"]
             if item["key"] == "_great_adj_")["variants"].pop()
        with self.assertRaisesRegex(MODULE.InventoryError, "variant count"):
            MODULE._pair_candidate(en, zh)

    def test_candidate_rejects_weight_drift(self):
        entries = self.candidate_entries()
        en = {"entries": [{"key": item["key"], "variants": item["english_variants"]}
                          for item in entries]}
        zh = copy.deepcopy(en)
        next(item for item in zh["entries"]
             if item["key"] == "_great_adj_")["variants"][0]["weight"] += 1
        with self.assertRaisesRegex(MODULE.InventoryError, "weight order"):
            MODULE._pair_candidate(en, zh)

    def test_candidate_rejects_token_order_drift(self):
        entries = self.candidate_entries()
        en = {"entries": [{"key": item["key"], "variants": item["english_variants"]}
                          for item in entries]}
        zh = copy.deepcopy(en)
        target = next(item for item in zh["entries"]
                      if item["key"] == "welcome_spam")
        variant = next(item for item in target["variants"] if item["runtime_tokens"])
        variant["runtime_tokens"] = ["@unknown@"]
        with self.assertRaisesRegex(MODULE.InventoryError, "token order"):
            MODULE._pair_candidate(en, zh)

    def test_candidate_rejects_random_topology_drift(self):
        entries = self.candidate_entries()
        en = {"entries": [{"key": item["key"],
                           "variants": item["english_variants"]}
                          for item in entries]}
        zh = copy.deepcopy(en)
        en["entries"][0]["variants"][0]["random_site_counts"] = [2]
        zh["entries"][0]["variants"][0]["random_site_counts"] = [3]
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "random topology"):
            MODULE._pair_candidate(en, zh)

    def test_candidate_rejects_lua_control_flow_drift(self):
        entries = self.candidate_entries()
        en = {"entries": [{"key": item["key"],
                           "variants": item["english_variants"]}
                          for item in entries]}
        zh = copy.deepcopy(en)
        target = next(item for item in zh["entries"]
                      if item["key"] == "hell_effect_quiet")
        variant = next(item for item in target["variants"]
                       if item["lua_topology"])
        original = variant["lua_topology"][0]
        variant["lua_topology"][0] = original.replace(
            "if you.can_smell()", "if not you.can_smell()", 1
        )
        self.assertNotEqual(original, variant["lua_topology"][0])
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "Lua control flow"):
            MODULE._pair_candidate(en, zh)

    def test_repository_ledger_binds_exact_clean_candidate(self):
        """Exercise the production ledger against the exact current commit.

        This is intentionally a real repository integration test: the v5
        tooling phase runs it from a clean candidate, so neither a synthetic
        card set nor working-tree bytes can stand in for the approved ledger
        and translation asset.
        """
        status = subprocess.check_output(
            ["git", "-C", str(ROOT), "status", "--porcelain",
             "--untracked-files=all"], text=True
        )
        self.assertEqual("", status,
                         "exact candidate integration requires a clean tree")
        candidate = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip()
        english = exact_artifact(candidate, "database/")
        localized = exact_artifact(candidate, "database/zh/")
        baseline_en = self.root / "production-baseline-en.json"
        baseline_zh = self.root / "production-baseline-zh.json"
        candidate_en = self.root / "production-candidate-en.json"
        candidate_zh = self.root / "production-candidate-zh.json"
        baseline_en.write_bytes(production_dump_bytes(self.en))
        baseline_zh.write_bytes(production_dump_bytes(self.zh))
        candidate_en.write_bytes(production_dump_bytes(english))
        candidate_zh.write_bytes(production_dump_bytes(localized))
        self.assertEqual(
            "468d0df31bb3c762cc8509c80beb64ad8e130f3295c42484943b5f5c56b5f570",
            MODULE._sha256(baseline_en.read_bytes()),
        )
        self.assertEqual(
            "71d0b7573587b623eadf14d02c475c2282716a31944b8fe1afab757a910709a0",
            MODULE._sha256(baseline_zh.read_bytes()),
        )
        output = Path("/tmp") / (
            f"miscname-exact-candidate-{os.getpid()}-{id(self)}.json"
        )
        self.addCleanup(lambda: output.unlink(missing_ok=True))
        self.assertEqual(0, MODULE.main([
            "--baseline-ref", BASELINE,
            "--english-dump", str(baseline_en),
            "--localized-dump", str(baseline_zh),
            "--glossary", str(ROOT / "docs/glossary.md"),
            "--review-results", str(ROOT / "docs/miscname-review-results.md"),
            "--candidate-ref", candidate,
            "--candidate-english-dump", str(candidate_en),
            "--candidate-localized-dump", str(candidate_zh),
            "--inventory-output", str(output),
        ]))
        audited = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(10, len(audited["review_evidence"]["cards"]))
        self.assertEqual(
            152, audited["candidate"]["dumps"]["english"]["variant_count"]
        )
        self.assertEqual(
            152, audited["candidate"]["dumps"]["localized"]["variant_count"]
        )

    def test_complete_review_ledger_validates(self):
        evidence = MODULE.validate_results(
            ROOT / "unused", self.inventory, records=self.records()
        )
        self.assertEqual(len(self.inventory["entries"]), len(evidence["cards"]))

    def test_missing_review_card_is_rejected(self):
        records = self.records()
        records.pop()
        with self.assertRaisesRegex(MODULE.InventoryError, "one card per identity"):
            MODULE.validate_results(ROOT / "unused", self.inventory, records=records)

    def test_unknown_review_field_is_rejected(self):
        records = self.records()
        records[1]["unknown"] = True
        with self.assertRaisesRegex(MODULE.InventoryError, "fields mismatch"):
            MODULE.validate_results(ROOT / "unused", self.inventory, records=records)

    def test_candidate_must_equal_approved_proposal(self):
        candidate_entries = self.candidate_entries()
        cards = []
        by_identity = {item["identity"]: item for item in candidate_entries}
        for entry in self.inventory["entries"]:
            proposal = by_identity[entry["identity"]]
            cards.append(card_for(entry, proposal["english_variants"],
                                  proposal["chinese_variants"]))
        candidate = {"entries": candidate_entries}
        MODULE.validate_results(ROOT / "unused", self.inventory, candidate,
                                records=self.records(cards))
        candidate["entries"][0]["chinese_variants"][0]["text"] += " drift"
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "approved proposal"):
            MODULE.validate_results(ROOT / "unused", self.inventory, candidate,
                                    records=self.records(cards))

    def test_non_deferred_card_rejects_deferral_fields(self):
        records = self.records()
        records[1]["deferral_owner"] = "nobody"
        with self.assertRaisesRegex(MODULE.InventoryError, "forbids deferral"):
            MODULE.validate_results(ROOT / "unused", self.inventory, records=records)

    def test_inventory_output_must_be_tmp(self):
        with self.assertRaises(Exception):
            MODULE.hardened.shared._safe_output(
                ROOT / "miscname-forbidden.json", self.inventory
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
