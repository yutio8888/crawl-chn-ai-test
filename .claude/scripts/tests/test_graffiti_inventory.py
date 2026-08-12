#!/usr/bin/env python3

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/graffiti_inventory.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("graffiti_inventory", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BASELINE = "888354b254f86a6b2de13e7ec6b1b73992a629f7"
RESULTS = ROOT / "docs/graffiti-review-results.md"


def exact_artifact(oid: str, directory: str) -> dict:
    scoped = MODULE.hardened.shared._derive_scoped_dump(
        oid, directory, f"fixture {directory}",
        source_basename=MODULE.SOURCE_BASENAME,
    )
    entries = copy.deepcopy(scoped["entries"])
    for basename in ("monname.txt", "colourname.txt"):
        dependency = MODULE.hardened.shared._derive_scoped_from_sources(
            copy.deepcopy(scoped["sources"]), directory,
            f"fixture {directory} {basename}", source_basename=basename,
        )
        entries.extend(copy.deepcopy(dependency["entries"]))
    return {
        "schema_version": 1,
        "database_name": "speak",
        "source_directory": directory,
        "sources": copy.deepcopy(scoped["sources"]),
        "entries": sorted(entries, key=lambda entry: entry["canonical_key"]),
    }


def review_variant(variant: dict) -> dict:
    return {"weight": variant["weight"], "text": variant["text"]}


def card_for(entry: dict) -> dict:
    current_en = [review_variant(variant) for variant in entry["english_variants"]]
    current_zh = [review_variant(variant) for variant in entry["chinese_variants"]]
    return {
        "identity": entry["identity"],
        "key": entry["key"],
        "lifecycle": entry["lifecycle"],
        "dependency_group": entry["dependency_group"],
        "display_context": "由 any_graffiti 递归展开并显示在地形/Xom 消息中。",
        "producer_consumer": {
            "loader": "crawl-ref/source/database.cc",
            "root": "any_graffiti",
        },
        "evidence_locations": [
            f"crawl-ref/source/dat/database/graffiti.txt:{entry['english_source_line']}",
            f"crawl-ref/source/dat/database/zh/graffiti.txt:{entry['chinese_source_line']}",
        ],
        "current_english_variants": current_en,
        "current_chinese_variants": current_zh,
        "proposed_english_variants": copy.deepcopy(current_en),
        "proposed_chinese_variants": copy.deepcopy(current_zh),
        "terminal_conclusion": "keep",
        "confidence": "high",
        "rationale": "逐变体核对语义、权重、token 与组合语序后保持现状。",
        "rejected_alternatives": ["不改变随机权重或递归身份。"],
        "reentry_trigger": "graffiti source、消费者、加载顺序或术语权威变化时重审。",
        "deferral_owner": None,
        "deferral_reason": None,
    }


class GraffitiInventoryTests(unittest.TestCase):
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
        return MODULE.validate_results(self.write_records(records), self.inventory)

    def test_exact_git_inventory_freezes_complete_baseline(self):
        self.assertEqual(58, len(self.inventory["entries"]))
        self.assertEqual(404, self.inventory["dumps"]["english"]["variant_count"])
        self.assertEqual(403, self.inventory["dumps"]["localized"]["variant_count"])
        self.assertEqual(
            MODULE.EXPECTED_BASELINE_UNRESOLVED["english"],
            self.inventory["dumps"]["english"]["token_facts"]["unresolved"],
        )
        self.assertEqual(
            ["_graffiti_unreadable_"],
            self.inventory["dumps"]["localized"]["reachability"]["unreachable"],
        )
        by_key = {entry["key"]: entry for entry in self.inventory["entries"]}
        for key, counts in MODULE.EXPECTED_BASELINE_ASYMMETRY.items():
            self.assertEqual(
                counts,
                (len(by_key[key]["english_variants"]),
                 len(by_key[key]["chinese_variants"])),
            )

    def test_complete_keep_ledger_passes(self):
        evidence = self.validate(self.records())
        self.assertEqual(58, len(evidence["cards"]))

    def test_checked_in_ledger_binds_complete_production_inventory(self):
        records = MODULE._strict_block(RESULTS)
        inventory = copy.deepcopy(self.inventory)
        inventory["dumps"]["english"]["artifact_sha256"] = records[0][
            "english_production_dump_sha256"
        ]
        inventory["dumps"]["localized"]["artifact_sha256"] = records[0][
            "chinese_production_dump_sha256"
        ]
        core = {key: value for key, value in inventory.items()
                if key != "inventory_sha256"}
        inventory["inventory_sha256"] = MODULE._sha256(
            MODULE._canonical_json(core)
        )
        self.assertEqual(records[0]["inventory_sha256"],
                         inventory["inventory_sha256"])
        evidence = MODULE.validate_results(RESULTS, inventory, records=records)
        self.assertEqual(58, len(evidence["cards"]))

    def test_missing_identity_and_current_text_drift_fail_closed(self):
        records = self.records()
        records.pop()
        records[0] = MODULE._expected_metadata(self.inventory, records[1:])
        with self.assertRaisesRegex(MODULE.InventoryError, "58 cards"):
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

    def test_recursive_and_external_token_classification(self):
        facts = self.inventory["dumps"]["english"]["token_facts"]
        self.assertIn("_graffiti_unreadable_", facts["edges"][MODULE.ROOT_KEY])
        self.assertTrue(any(site["token"] == "@random_god@"
                            for site in facts["postprocess_sites"]))
        self.assertTrue(any(site["token"] == "@ancestor name@"
                            for site in facts["external_sites"]))

    def test_candidate_pair_rejects_weight_or_count_drift(self):
        variants = [{
            "weight": 10, "text": "x", "runtime_tokens": [],
            "random_site_counts": [],
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
            "random_site_counts": [2],
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


if __name__ == "__main__":
    unittest.main()
