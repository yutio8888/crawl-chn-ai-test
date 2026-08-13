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
SCRIPT = ROOT / ".claude/scripts/decorlines_inventory.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("decorlines_inventory", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BASELINE = "306d9099ae08a94a64f051d487dfed0a9675e178"


def exact_artifact(oid: str, directory: str) -> dict:
    """Rebuild the full misc TextDB dump from exact Git inputs with the
    production load order, DBM_REPLACE merge and weighted-variant parse."""
    shared = MODULE.hardened.shared
    if directory == "database/":
        manifest = MODULE._misc_source_manifest(oid, f"fixture {directory}")
    else:
        manifest = shared._localized_source_manifest(oid, f"fixture {directory}")
    sources = []
    for load_index, source_name in enumerate(manifest):
        sources.append({
            "source_name": source_name,
            "load_index": load_index,
            "normalized_utf8": shared._source_snapshot_at_oid(
                oid, source_name, f"fixture {directory} {source_name}"),
        })
    parsed = []
    provenance_by_entry: dict[int, dict] = {}
    histories: dict[str, list[dict]] = {}
    for source in sources:
        definitions = shared.parse_db_keys(source["normalized_utf8"],
                                           source["source_name"])
        for ordinal, definition in enumerate(definitions):
            provenance = {
                "source_name": source["source_name"],
                "load_index": source["load_index"],
                "definition_ordinal": ordinal,
            }
            parsed.append(definition)
            provenance_by_entry[id(definition)] = provenance
            histories.setdefault(
                shared.lowercase_string(definition.raw_key), []
            ).append(provenance)
    effective, _overrides = shared.merge_desc_sequence(parsed)
    entries = []
    for canonical_key in sorted(effective):
        winner = effective[canonical_key]
        provenance = provenance_by_entry[id(winner)]
        variants, parse_error = shared._parse_weighted_entry(
            winner.value, provenance, canonical_key)
        entries.append({
            "canonical_key": canonical_key,
            "effective_provenance": provenance,
            "raw_body": winner.value,
            "source_history": histories[canonical_key],
            "variants": variants,
            "parse_error": parse_error,
            "body_empty": winner.value == "",
        })
    return {
        "schema_version": 1,
        "database_name": "misc",
        "source_directory": directory,
        "sources": sources,
        "entries": sorted(entries, key=lambda entry: entry["canonical_key"]),
    }


def review_variant(variant: dict) -> dict:
    return {"weight": variant["weight"], "text": variant["text"]}


def card_for(entry: dict) -> dict:
    current_en = [review_variant(variant)
                  for variant in entry["english_variants"]]
    current_zh = [review_variant(variant)
                  for variant in entry["chinese_variants"]]
    return {
        "identity": entry["identity"],
        "key": entry["key"],
        "lifecycle": entry["lifecycle"],
        "dependency_group": entry["dependency_group"],
        "display_context": "由 directn.cc::_walk_on_decor 消费的 decorlines 消息。",
        "producer_consumer": {
            "loader": "crawl-ref/source/database.cc:143",
            "decor_consumer": "crawl-ref/source/directn.cc:3007",
        },
        "evidence_locations": [
            f"crawl-ref/source/dat/database/decorlines.txt:"
            f"{entry['english_source_line']}",
            f"crawl-ref/source/dat/database/zh/decorlines.txt:"
            f"{entry['chinese_source_line']}",
        ],
        "current_english_variants": current_en,
        "current_chinese_variants": current_zh,
        "proposed_english_variants": copy.deepcopy(current_en),
        "proposed_chinese_variants": copy.deepcopy(current_zh),
        "terminal_conclusion": "keep",
        "confidence": "high",
        "rationale": "逐变体核对语义、权重、token 与组合语序后保持现状。",
        "rejected_alternatives": ["不改变随机权重或递归身份。"],
        "reentry_trigger": "decorlines source、消费者、加载顺序或术语权威变化时重审。",
        "deferral_owner": None,
        "deferral_reason": None,
    }


class DecorlinesInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.en = exact_artifact(BASELINE, "database/")
        cls.zh = exact_artifact(BASELINE, "database/zh/")
        cls.en_path = cls.root / "en.json"
        cls.zh_path = cls.root / "zh.json"
        cls.en_path.write_text(json.dumps(cls.en, ensure_ascii=False),
                               encoding="utf-8")
        cls.zh_path.write_text(json.dumps(cls.zh, ensure_ascii=False),
                               encoding="utf-8")
        cls.inventory = MODULE.build_inventory(
            BASELINE, cls.en_path, cls.zh_path, ROOT / "docs/glossary.md"
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def records(self) -> list[dict]:
        cards = [card_for(entry) for entry in self.inventory["entries"]]
        return [MODULE._expected_metadata(self.inventory, cards), *cards]

    def write_records(self, records: list[dict]) -> Path:
        path = self.root / f"{self.id().split('.')[-1]}.md"
        path.write_text(
            MODULE.STRICT_BEGIN + "\n```jsonl\n"
            + "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True)
                        for record in records)
            + "\n```\n" + MODULE.STRICT_END + "\n",
            encoding="utf-8",
        )
        return path

    def validate(self, records: list[dict]):
        return MODULE.validate_results(self.write_records(records),
                                       self.inventory)

    def test_exact_git_inventory_freezes_complete_baseline(self):
        self.assertEqual(132, len(self.inventory["entries"]))
        self.assertEqual(117, self.inventory["scope"]["root_key_count"])
        self.assertEqual(209,
                         self.inventory["dumps"]["english"]["variant_count"])
        self.assertEqual(266,
                         self.inventory["dumps"]["localized"]["variant_count"])
        self.assertEqual({"english": 11, "chinese": 11},
                         self.inventory["scope"]["baseline_random_sites"])
        self.assertEqual({"english": 5, "chinese": 5},
                         self.inventory["scope"]["baseline_lua_sites"])
        self.assertEqual(63, len(self.inventory["scope"]["baseline_asymmetry"]))
        self.assertEqual(57, len(
            self.inventory["scope"]["baseline_token_multiset_drift"]))
        self.assertEqual([], self.inventory["dumps"]["english"]["token_facts"]["unresolved"])
        self.assertEqual([], self.inventory["dumps"]["localized"]["token_facts"]["unresolved"])
        self.assertEqual([], self.inventory["dumps"]["english"]["reachability"]["unreachable"])
        self.assertEqual([], self.inventory["dumps"]["localized"]["reachability"]["unreachable"])
        self.assertEqual(
            sorted(MODULE.INTERNAL_FRAGMENT_KEYS),
            sorted({site["token"][1:-1]
                    for site in self.inventory["dumps"]["english"]["token_facts"]["fragment_sites"]}),
        )

    def test_complete_keep_ledger_passes(self):
        evidence = self.validate(self.records())
        self.assertEqual(132, len(evidence["cards"]))

    def test_missing_identity_and_current_text_drift_fail_closed(self):
        records = self.records()
        records.pop()
        records[0] = MODULE._expected_metadata(self.inventory, records[1:])
        with self.assertRaisesRegex(MODULE.InventoryError, "132 cards"):
            self.validate(records)

        records = self.records()
        records[1]["current_english_variants"][0]["text"] += " drift"
        with self.assertRaisesRegex(MODULE.InventoryError, "current EN mismatch"):
            self.validate(records)

    def test_unreviewed_proposal_and_deferral_metadata_fail_closed(self):
        records = self.records()
        records[1]["proposed_chinese_variants"][0]["text"] += "改"
        with self.assertRaisesRegex(MODULE.InventoryError, "conclusion/change mismatch"):
            self.validate(records)

        records = self.records()
        records[1]["terminal_conclusion"] = "defer terminology"
        records[0] = MODULE._expected_metadata(self.inventory, records[1:])
        with self.assertRaisesRegex(MODULE.InventoryError, "requires owner"):
            self.validate(records)

    def test_token_classification_and_reachability(self):
        facts = self.inventory["dumps"]["english"]["token_facts"]
        self.assertIn("@any_graffiti@", {site["token"]
                                         for site in facts["external_sites"]})
        self.assertIn("@any_colour@", {site["token"]
                                       for site in facts["external_sites"]})
        self.assertIn("@your_weapon@", {site["token"]
                                        for site in facts["postprocess_sites"]})
        self.assertIn("@sparkling_message@", {site["token"]
                                              for site in facts["fragment_sites"]})
        roots = set(self.inventory["scope"]["root_keys"])
        reached = set(self.inventory["dumps"]["english"]["reachability"]["reachable"])
        self.assertEqual(132, len(reached))
        non_root = {entry["key"] for entry in self.inventory["entries"]
                    if entry["lifecycle"] != "direct-production-root"}
        self.assertTrue(non_root <= reached)
        self.assertEqual(117, len(roots))

    def test_asymmetry_and_drift_facts_are_frozen(self):
        by_key = {entry["key"]: entry for entry in self.inventory["entries"]}
        for key, counts in list(self.inventory["scope"]["baseline_asymmetry"].items())[:5]:
            self.assertEqual(
                counts,
                [len(by_key[key]["english_variants"]),
                 len(by_key[key]["chinese_variants"])],
            )
        self.assertEqual(
            set(tuple(item) for item in
                self.inventory["scope"]["baseline_token_multiset_drift"]),
            MODULE.EXPECTED_BASELINE_TOKEN_MULTISET_DRIFT,
        )

    def test_candidate_pair_rejects_weight_or_count_drift(self):
        variants = [{
            "weight": 10, "text": "x", "runtime_tokens": [],
            "random_site_counts": [], "lua_site_count": 0,
        }]
        en = {"entries": [{"key": "k", "variants": copy.deepcopy(variants)}]}
        zh = {"entries": [{"key": "k", "variants": copy.deepcopy(variants)}]}
        self.assertEqual(1, len(MODULE._pair_candidate(en, zh)))
        zh["entries"][0]["variants"][0]["weight"] = 2
        with self.assertRaisesRegex(MODULE.InventoryError, "weight order"):
            MODULE._pair_candidate(en, zh)
        zh["entries"][0]["variants"] = []
        with self.assertRaisesRegex(MODULE.InventoryError, "variant count"):
            MODULE._pair_candidate(en, zh)

    def test_candidate_pair_rejects_token_or_random_topology_drift(self):
        variants = [{
            "weight": 10, "text": "@a@[x|y]", "runtime_tokens": ["@a@"],
            "random_site_counts": [2], "lua_site_count": 0,
        }]
        en = {"entries": [{"key": "k", "variants": copy.deepcopy(variants)}]}
        zh = {"entries": [{"key": "k", "variants": copy.deepcopy(variants)}]}
        zh["entries"][0]["variants"][0]["runtime_tokens"] = ["@b@"]
        with self.assertRaisesRegex(MODULE.InventoryError, "token multiset"):
            MODULE._pair_candidate(en, zh)
        zh["entries"][0]["variants"][0]["runtime_tokens"] = ["@a@"]
        zh["entries"][0]["variants"][0]["random_site_counts"] = [3]
        with self.assertRaisesRegex(MODULE.InventoryError, "random-site"):
            MODULE._pair_candidate(en, zh)

    def test_dump_family_misc_is_enforced_on_all_load_paths(self):
        # A speak-family dump must never be accepted on a decorlines (misc)
        # path: baseline/candidate loads and the proposal/scaffold load all
        # fail closed with the family mismatch.
        speak_en = copy.deepcopy(self.en)
        speak_en["database_name"] = "speak"
        speak_path = self.root / "speak-en.json"
        speak_path.write_text(json.dumps(speak_en, ensure_ascii=False),
                              encoding="utf-8")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "database_name must be 'misc'"):
            MODULE._load_dataset(BASELINE, speak_path, "database/",
                                 "baseline EN", "baseline")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "database_name must be 'misc'"):
            MODULE._proposal_dataset(speak_path, "database/", "proposal EN")
        speak_zh = copy.deepcopy(self.zh)
        speak_zh["database_name"] = "speak"
        speak_zh_path = self.root / "speak-zh.json"
        speak_zh_path.write_text(json.dumps(speak_zh, ensure_ascii=False),
                                 encoding="utf-8")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "database_name must be 'misc'"):
            MODULE._load_dataset(BASELINE, speak_zh_path, "database/zh/",
                                 "baseline ZH", "baseline")

    def test_misc_dump_is_rejected_when_speak_family_is_expected(self):
        # The shared validator refuses a misc dump wherever a speak family
        # is expected, so a misc artifact can never satisfy a speak caller.
        with self.assertRaisesRegex(MODULE.hardened.ArtifactError,
                                    "database_name must be 'speak'"):
            MODULE.hardened.validate_artifact(
                self.en, "fixture EN", expected_database="speak"
            )
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "database_name must be 'speak'"):
            MODULE.hardened._load_dump_safe(
                self.en_path, "fixture EN", "database/",
                expected_database="speak",
            )

    def test_scaffold_rejects_symlinked_path_components(self):
        original = MODULE.RESULTS_PATH
        real_dir = self.root / "real-dir"
        real_dir.mkdir()
        link_dir = self.root / "link-dir"
        link_dir.symlink_to(real_dir, target_is_directory=True)
        scaffold_path = link_dir / "decorlines-review-results.md"
        MODULE.RESULTS_PATH = real_dir / "decorlines-review-results.md"
        try:
            with self.assertRaisesRegex(MODULE.InventoryError,
                                        "without following a symlink"):
                MODULE.scaffold_results(scaffold_path, self.inventory)
            self.assertFalse((real_dir / "decorlines-review-results.md")
                             .exists())
        finally:
            MODULE.RESULTS_PATH = original

    def test_scaffold_rejects_parent_renamed_between_verify_and_create(self):
        # Swap the parent away between the pre-create chain verification and
        # the exclusive create: the helper must fail closed and the ledger
        # must never survive in the relocated directory.
        original = MODULE.RESULTS_PATH
        real_dir = self.root / "rename-away"
        real_dir.mkdir()
        parent = real_dir / "parent"
        parent.mkdir()
        moved = real_dir / "moved-parent"
        scaffold_path = parent / "decorlines-review-results.md"
        MODULE.RESULTS_PATH = scaffold_path
        real_open = MODULE.os.open
        swapped = False
        def swapped_open(path, flags, *args, **kwargs):
            nonlocal swapped
            if flags & os.O_CREAT and not swapped:
                swapped = True
                os.rename(parent, moved)
            return real_open(path, flags, *args, **kwargs)
        try:
            with mock.patch.object(MODULE.os, "open",
                                   side_effect=swapped_open):
                with self.assertRaisesRegex(MODULE.InventoryError,
                                            "re-opened"):
                    MODULE.scaffold_results(scaffold_path, self.inventory)
            self.assertFalse((moved / "decorlines-review-results.md").exists())
            self.assertFalse(scaffold_path.exists())
        finally:
            MODULE.RESULTS_PATH = original

    def test_scaffold_rejects_parent_replaced_between_verify_and_create(self):
        # Replace the parent with a fresh directory at the approved pathname
        # between the pre-create chain verification and the exclusive create:
        # identity re-verification must detect the swap and remove the file
        # created through the pinned (relocated) parent.
        original = MODULE.RESULTS_PATH
        real_dir = self.root / "replace-dir"
        real_dir.mkdir()
        parent = real_dir / "parent"
        parent.mkdir()
        moved = real_dir / "moved-parent"
        scaffold_path = parent / "decorlines-review-results.md"
        MODULE.RESULTS_PATH = scaffold_path
        real_open = MODULE.os.open
        swapped = False
        def swapped_open(path, flags, *args, **kwargs):
            nonlocal swapped
            if flags & os.O_CREAT and not swapped:
                swapped = True
                os.rename(parent, moved)
                parent.mkdir()
            return real_open(path, flags, *args, **kwargs)
        try:
            with mock.patch.object(MODULE.os, "open",
                                   side_effect=swapped_open):
                with self.assertRaisesRegex(MODULE.InventoryError,
                                            "changed identity"):
                    MODULE.scaffold_results(scaffold_path, self.inventory)
            self.assertFalse((moved / "decorlines-review-results.md").exists())
            self.assertFalse((parent / "decorlines-review-results.md").exists())
        finally:
            MODULE.RESULTS_PATH = original

    def test_scaffold_rejects_parent_renamed_after_create(self):
        # A parent swap that happens after the exclusive create but before
        # the post-create chain verification must also fail closed and must
        # unlink the file already created through the pinned parent.
        original = MODULE.RESULTS_PATH
        real_dir = self.root / "rename-after"
        real_dir.mkdir()
        parent = real_dir / "parent"
        parent.mkdir()
        moved = real_dir / "moved-parent"
        scaffold_path = parent / "decorlines-review-results.md"
        MODULE.RESULTS_PATH = scaffold_path
        real_open = MODULE.os.open
        swapped = False
        def swapped_open(path, flags, *args, **kwargs):
            nonlocal swapped
            if flags & os.O_CREAT and not swapped:
                swapped = True
                fd = real_open(path, flags, *args, **kwargs)
                os.rename(parent, moved)
                return fd
            return real_open(path, flags, *args, **kwargs)
        try:
            with mock.patch.object(MODULE.os, "open",
                                   side_effect=swapped_open):
                with self.assertRaisesRegex(MODULE.InventoryError,
                                            "re-opened"):
                    MODULE.scaffold_results(scaffold_path, self.inventory)
            self.assertFalse((moved / "decorlines-review-results.md").exists())
            self.assertFalse(scaffold_path.exists())
        finally:
            MODULE.RESULTS_PATH = original

    def test_cli_rejects_speak_dump_on_decorlines_path(self):
        # The real decorlines CLI must fail closed when a speak-family dump
        # is supplied on a misc load path.
        speak = copy.deepcopy(self.en)
        speak["database_name"] = "speak"
        speak_path = self.root / "cli-speak-en.json"
        speak_path.write_text(json.dumps(speak, ensure_ascii=False),
                              encoding="utf-8")
        output = self.root / "cli-out.json"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--baseline-ref", BASELINE,
             "--english-dump", str(speak_path),
             "--localized-dump", str(self.zh_path),
             "--inventory-output", str(output)],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("database_name must be 'misc'", result.stderr)
        self.assertFalse(output.exists())

    def test_scaffold_generates_empty_ledger_and_refuses_overwrite(self):
        original = MODULE.RESULTS_PATH
        scaffold_path = self.root / "decorlines-review-results.md"
        MODULE.RESULTS_PATH = scaffold_path
        try:
            records = MODULE.scaffold_results(scaffold_path, self.inventory)
            with self.assertRaisesRegex(MODULE.InventoryError,
                                        "exclusively create"):
                MODULE.scaffold_results(scaffold_path, self.inventory)
        finally:
            MODULE.RESULTS_PATH = original
        self.assertEqual(133, len(records))
        metadata, cards = records[0], records[1:]
        self.assertEqual(132, len(cards))
        self.assertEqual(0, len(metadata["terminal_conclusion_counts"]))
        self.assertEqual("decorlines:" + self.inventory["entries"][0]["key"],
                         cards[0]["identity"])
        self.assertIsNone(cards[0]["proposed_chinese_variants"])
        self.assertIsNone(cards[0]["terminal_conclusion"])
        self.assertEqual(
            MODULE._expected_metadata(self.inventory, cards),
            metadata,
        )


if __name__ == "__main__":
    unittest.main()
