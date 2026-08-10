#!/usr/bin/env python3

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/monflee_inventory.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("monflee_inventory", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

BASELINE = subprocess.run(
    ["git", "-C", str(ROOT), "rev-parse", "HEAD^"],
    check=True, text=True, capture_output=True,
).stdout.strip()
CANDIDATE = subprocess.run(
    ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
    check=True, text=True, capture_output=True,
).stdout.strip()
NON_DESCENDANT = subprocess.run(
    ["git", "-C", str(ROOT), "rev-parse", "HEAD^^"],
    check=True, text=True, capture_output=True,
).stdout.strip()
KEY = "dream sheep flee"
EN_PATTERNS = [
    "@The_monster@ bleats in terror.",
    "VISUAL:@The_monster@ is struck with panic!",
    "VISUAL:@The_monster@ panics and turns to flee.",
    "VISUAL:A frightened @monster@ leaps away.",
    "VISUAL:@The_monster@ stampedes away.",
]
ZH_PATTERNS = [
    "@The_monster@旧一。",
    "VISUAL:@The_monster@旧二。",
    "VISUAL:@The_monster@旧三。",
    "VISUAL:旧四@monster@。",
    "VISUAL:@The_monster@旧五。",
]
WEIGHTS = [30, 10, 10, 10, 10]


def committed_source(oid: str, source_name: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), "show",
         f"{oid}:crawl-ref/source/dat/{source_name}"],
        check=True, capture_output=True,
    ).stdout.decode("utf-8")


def artifact(
    language: str, patterns: list[str] | None = None, oid: str = BASELINE,
) -> dict:
    patterns = list(patterns or (EN_PATTERNS if language == "en" else ZH_PATTERNS))
    directory = "database/" if language == "en" else "database/zh/"
    source_name = f"{directory}monflee.txt"
    provenance = {
        "source_name": source_name,
        "load_index": 0,
        "definition_ordinal": 0,
    }
    return {
        "schema_version": 1,
        "database_name": "speak",
        "source_directory": directory,
        "sources": [{
            "source_name": source_name,
            "load_index": 0,
            "normalized_utf8": committed_source(oid, source_name),
        }],
        "entries": [{
            "canonical_key": KEY,
            "effective_provenance": provenance,
            "raw_body": "opaque production parser body",
            "source_history": [provenance],
            "variants": [
                {
                    "locator": {"canonical_key": KEY, "variant_ordinal": ordinal},
                    "provenance": provenance,
                    "weight": WEIGHTS[ordinal],
                    "raw_pattern": pattern,
                }
                for ordinal, pattern in enumerate(patterns)
            ],
            "parse_error": None,
            "body_empty": False,
        }],
    }


def card_for(inventory: dict, conclusion: str = "keep") -> dict:
    entry = inventory["entries"][0]
    current_en = [variant["english"] for variant in entry["variants"]]
    current_zh = [variant["chinese"] for variant in entry["variants"]]
    card = {
        "identity": entry["identity"],
        "key": entry["key"],
        "lifecycle": "current-player-visible",
        "terminal_conclusion": conclusion,
        "confidence": "high",
        "dependency_group": f"{entry['key']} voice and visual motion",
        "glossary_authority": (
            f"{inventory['glossary']['path']}@{inventory['glossary']['sha256']}"
        ),
        "actual_behavior": MODULE.FROZEN_ACTUAL_BEHAVIOR,
        "display_context": MODULE.FROZEN_DISPLAY_CONTEXT,
        "consumer": copy.deepcopy(MODULE.FROZEN_CONSUMER),
        "producers": copy.deepcopy(MODULE.FROZEN_PRODUCERS),
        "evidence_locations": list(MODULE.FROZEN_EVIDENCE_LOCATIONS),
        "production_facts": MODULE._expected_production_facts(inventory, entry),
        "reentry_trigger": "源、结构或生产路由变化时重新审阅。",
        "rejected_alternatives": ["不改变 lookup、权重或通道协议。"],
        "reviewer_rationale": "已核对生产来源、消费者与所有变体。",
        "current_english": current_en,
        "current_chinese": current_zh,
        "proposed_translation": list(current_zh),
        "variant_reviews": [],
    }
    for variant in entry["variants"]:
        card["variant_reviews"].append({
            "variant_ordinal": variant["locator"]["variant_ordinal"],
            "weight": variant["weight"],
            "control_prefix": variant["control_prefix"],
            "runtime_tokens": variant["runtime_tokens"],
            "english": variant["english"],
            "current_chinese": variant["chinese"],
            "proposed_translation": variant["chinese"],
            "terminal_conclusion": "keep",
            "rationale": "完整审阅并保留。",
        })
    return card


def metadata_for(inventory: dict) -> dict:
    return {
        "baseline": inventory["baseline_ref"],
        "glossary_sha256": inventory["glossary"]["sha256"],
        "identity_count": len(inventory["entries"]),
        "inventory_sha256": inventory["inventory_sha256"],
    }


class MonfleeInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.glossary = self.root / "glossary.md"
        self.glossary.write_text("glossary fixture\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def write_dump(self, name: str, value: dict) -> Path:
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def inventory(self, en: dict | None = None, zh: dict | None = None) -> dict:
        en_value = en or artifact("en")
        zh_value = zh or artifact("zh")
        en_path = self.write_dump("en.json", en_value)
        zh_path = self.write_dump("zh.json", zh_value)
        with mock.patch.object(
            MODULE, "_trusted_artifacts_at_oid",
            return_value=(copy.deepcopy(en_value), copy.deepcopy(zh_value)),
        ):
            return MODULE.build_inventory(BASELINE, en_path, zh_path, self.glossary)

    def add_candidate(
        self, inventory: dict, en: dict, zh: dict, candidate_ref: str = CANDIDATE,
    ) -> list[dict]:
        en_path = self.write_dump("candidate-en.json", en)
        zh_path = self.write_dump("candidate-zh.json", zh)
        with mock.patch.object(
            MODULE, "_trusted_artifacts_at_oid",
            return_value=(copy.deepcopy(en), copy.deepcopy(zh)),
        ):
            return MODULE.add_candidate(
                inventory, candidate_ref, en_path, zh_path
            )

    def write_results(self, inventory: dict, cards: list[dict], metadata=None) -> Path:
        records = [metadata or metadata_for(inventory), *cards]
        path = self.root / "results.md"
        path.write_text(
            "heading\n\n" + MODULE.STRICT_BEGIN + "\n```jsonl\n"
            + "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True)
                         for row in records)
            + "\n```\n" + MODULE.STRICT_END + "\n",
            encoding="utf-8",
        )
        return path

    def assert_rejected(self, en=None, zh=None, contains=None):
        with self.assertRaises(MODULE.InventoryError) as raised:
            self.inventory(en, zh)
        if contains:
            self.assertIn(contains, str(raised.exception))

    def test_build_binds_all_sources_and_is_deterministic(self):
        en = artifact("en")
        en["sources"].append({
            "source_name": "database/monspeak.txt", "load_index": 1,
            "normalized_utf8": committed_source(BASELINE, "database/monspeak.txt"),
        })
        first = self.inventory(en=en)
        second = self.inventory(en=en)
        self.assertEqual(first["inventory_sha256"], second["inventory_sha256"])
        self.assertEqual(2, len(first["dumps"]["english"]["source_snapshots"]))
        self.assertEqual({"monflee:dream sheep flee"},
                         {entry["identity"] for entry in first["entries"]})
        self.assertEqual(WEIGHTS,
                         [v["weight"] for v in first["entries"][0]["variants"]])

    def test_schema_and_source_snapshot_binding_fail_closed(self):
        bad = artifact("en")
        bad["schema_version"] = 2
        self.assert_rejected(en=bad, contains="schema_version")
        bad = artifact("en")
        bad["sources"][0]["source_name"] = "outside/monflee.txt"
        self.assert_rejected(en=bad, contains="source_name")
        bad = artifact("en")
        bad["sources"][0]["normalized_utf8"] = 7
        self.assert_rejected(en=bad, contains="normalized_utf8")
        bad = artifact("en")
        bad["sources"][0]["normalized_utf8"] += "snapshot drift"
        self.assert_rejected(en=bad, contains="does not match OID")

    def test_complete_production_derivation_rejects_omission_and_forgery(self):
        def complete(language: str, source_count: int) -> dict:
            value = artifact(language)
            directory = value["source_directory"]
            for index in range(1, source_count):
                value["sources"].append({
                    "source_name": f"{directory}fixture-{index}.txt",
                    "load_index": index,
                    "normalized_utf8": f"fixture {index}\n",
                })
            return value

        trusted_en = complete("en", 10)
        trusted_zh = complete("zh", 23)
        MODULE._require_production_derivation(trusted_en, trusted_en, "baseline EN")
        MODULE._require_production_derivation(trusted_zh, trusted_zh, "baseline ZH")

        missing_source = copy.deepcopy(trusted_en)
        missing_source["sources"].pop()
        MODULE.validate_artifact(missing_source, "missing-source fixture")
        with self.assertRaisesRegex(MODULE.InventoryError, "source discovery/order"):
            MODULE._require_production_derivation(
                missing_source, trusted_en, "baseline EN"
            )

        forged_body = copy.deepcopy(trusted_en)
        forged_body["entries"][0]["raw_body"] += "forged"
        MODULE.validate_artifact(forged_body, "forged-body fixture")
        with self.assertRaisesRegex(MODULE.InventoryError, "raw_body/variants"):
            MODULE._require_production_derivation(forged_body, trusted_en, "baseline EN")

        forged_variant = copy.deepcopy(trusted_zh)
        forged_variant["entries"][0]["variants"][0]["raw_pattern"] += "forged"
        MODULE.validate_artifact(forged_variant, "forged-variant fixture")
        with self.assertRaisesRegex(MODULE.InventoryError, "raw_body/variants"):
            MODULE._require_production_derivation(
                forged_variant, trusted_zh, "candidate ZH"
            )

        trusted_override = copy.deepcopy(trusted_zh)
        entry = trusted_override["entries"][0]
        earlier = copy.deepcopy(entry["effective_provenance"])
        effective = {
            "source_name": trusted_override["sources"][1]["source_name"],
            "load_index": 1,
            "definition_ordinal": 0,
        }
        entry["effective_provenance"] = effective
        entry["source_history"] = [earlier, effective]
        for variant in entry["variants"]:
            variant["provenance"] = effective
        drifted_override = copy.deepcopy(trusted_override)
        drifted_override["entries"][0]["source_history"] = [effective]
        MODULE.validate_artifact(trusted_override, "trusted override fixture")
        MODULE.validate_artifact(drifted_override, "drifted override fixture")
        with self.assertRaisesRegex(MODULE.InventoryError, "raw_body/variants"):
            MODULE._require_production_derivation(
                drifted_override, trusted_override, "candidate ZH"
            )

    def test_english_and_chinese_artifacts_cannot_swap_slots(self):
        with self.assertRaisesRegex(
            MODULE.InventoryError,
            "baseline EN source_directory must be exactly 'database/'",
        ):
            self.inventory(en=artifact("zh"), zh=artifact("en"))

        inventory = self.inventory()
        swapped_en = self.write_dump(
            "candidate-swapped-en.json", artifact("zh", oid=CANDIDATE)
        )
        swapped_zh = self.write_dump(
            "candidate-swapped-zh.json", artifact("en", oid=CANDIDATE)
        )
        with self.assertRaisesRegex(
            MODULE.InventoryError,
            "candidate EN source_directory must be exactly 'database/'",
        ):
            MODULE.add_candidate(inventory, CANDIDATE, swapped_en, swapped_zh)

    def test_duplicate_key_and_locator_and_ordinal_gap_are_rejected(self):
        bad = artifact("en")
        bad["entries"].append(copy.deepcopy(bad["entries"][0]))
        self.assert_rejected(en=bad, contains="strictly sorted and unique")
        bad = artifact("en")
        bad["entries"][0]["variants"][1]["locator"]["variant_ordinal"] = 0
        self.assert_rejected(en=bad, contains="contiguous")
        bad = artifact("en")
        bad["entries"][0]["variants"][1]["locator"]["variant_ordinal"] = 2
        self.assert_rejected(en=bad, contains="contiguous")

    def test_parse_error_override_and_definition_gap_are_rejected(self):
        bad = artifact("en")
        bad["entries"][0]["parse_error"] = "WEIGHT AT END"
        bad["entries"][0]["variants"] = []
        self.assert_rejected(en=bad, contains="parse error")

        bad = artifact("en")
        other = {"source_name": "database/monspeak.txt", "load_index": 1,
                 "normalized_utf8": committed_source(BASELINE, "database/monspeak.txt")}
        bad["sources"].append(other)
        other_prov = {"source_name": "database/monspeak.txt", "load_index": 1,
                      "definition_ordinal": 0}
        entry = bad["entries"][0]
        entry["source_history"].append(other_prov)
        entry["effective_provenance"] = other_prov
        for variant in entry["variants"]:
            variant["provenance"] = other_prov
        self.assert_rejected(en=bad, contains="overridden")

        bad = artifact("en")
        entry = bad["entries"][0]
        entry["effective_provenance"]["definition_ordinal"] = 1
        for variant in entry["variants"]:
            variant["provenance"]["definition_ordinal"] = 1
        self.assert_rejected(en=bad, contains="definition ordinals")

    def test_exact_scope_key_set_not_count_only(self):
        bad = artifact("en")
        bad["entries"][0]["canonical_key"] = "different flee"
        for variant in bad["entries"][0]["variants"]:
            variant["locator"]["canonical_key"] = "different flee"
        self.assert_rejected(en=bad, contains="key set mismatch")

    def test_weight_order_and_control_prefix_drift_are_rejected(self):
        bad = artifact("zh")
        bad["entries"][0]["variants"][1]["weight"] = 11
        self.assert_rejected(zh=bad, contains="topology")
        bad = artifact("zh")
        variants = bad["entries"][0]["variants"]
        variants[3]["raw_pattern"], variants[4]["raw_pattern"] = (
            variants[4]["raw_pattern"], variants[3]["raw_pattern"]
        )
        self.assert_rejected(zh=bad, contains="topology")
        bad = artifact("zh")
        bad["entries"][0]["variants"][0]["raw_pattern"] = (
            "VISUAL:" + bad["entries"][0]["variants"][0]["raw_pattern"]
        )
        self.assert_rejected(zh=bad, contains="topology")
        bad = artifact("zh")
        bad["entries"][0]["variants"][1]["raw_pattern"] = (
            "SOUND:" + bad["entries"][0]["variants"][1]["raw_pattern"].split(":", 1)[1]
        )
        self.assert_rejected(zh=bad, contains="unrecognized control")

    def test_token_case_order_and_count_drift_are_rejected(self):
        bad = artifact("zh")
        bad["entries"][0]["variants"][0]["raw_pattern"] = "@the_monster@旧一。"
        self.assert_rejected(zh=bad, contains="topology")

        en_patterns = list(EN_PATTERNS)
        zh_patterns = list(ZH_PATTERNS)
        en_patterns[0] = "@The_monster@ sees @monster@."
        zh_patterns[0] = "@monster@看见@The_monster@。"
        self.assert_rejected(en=artifact("en", en_patterns),
                             zh=artifact("zh", zh_patterns), contains="topology")

        bad = artifact("zh")
        bad["entries"][0]["variants"][0]["raw_pattern"] = (
            "@The_monster@@monster@旧一。"
        )
        self.assert_rejected(zh=bad, contains="topology")

    def test_review_keep_card_passes_and_missing_duplicate_cards_fail(self):
        inventory = self.inventory()
        card = card_for(inventory)
        path = self.write_results(inventory, [card])
        loaded = MODULE.validate_results(path, inventory, None)
        self.assertEqual(1, len(loaded["cards"]))

        missing = self.write_results(inventory, [])
        with self.assertRaisesRegex(MODULE.InventoryError, "identity set mismatch"):
            MODULE.validate_results(missing, inventory, None)
        duplicate = self.write_results(inventory, [card, copy.deepcopy(card)])
        with self.assertRaisesRegex(MODULE.InventoryError, "duplicate review card"):
            MODULE.validate_results(duplicate, inventory, None)

    def test_review_missing_variant_and_nonterminal_fail(self):
        inventory = self.inventory()
        card = card_for(inventory)
        card["variant_reviews"].pop()
        path = self.write_results(inventory, [card])
        with self.assertRaisesRegex(MODULE.InventoryError, "coverage mismatch"):
            MODULE.validate_results(path, inventory, None)

        card = card_for(inventory)
        card["variant_reviews"][0]["terminal_conclusion"] = "pending"
        path = self.write_results(inventory, [card])
        with self.assertRaisesRegex(MODULE.InventoryError, "nonterminal"):
            MODULE.validate_results(path, inventory, None)

    def test_review_baseline_and_current_agreement_fail_closed(self):
        inventory = self.inventory()
        card = card_for(inventory)
        card["current_chinese"][0] += "漂移"
        path = self.write_results(inventory, [card])
        with self.assertRaisesRegex(MODULE.InventoryError, "current_chinese"):
            MODULE.validate_results(path, inventory, None)
        metadata = metadata_for(inventory)
        metadata["inventory_sha256"] = "0" * 64
        path = self.write_results(inventory, [card_for(inventory)], metadata)
        with self.assertRaisesRegex(MODULE.InventoryError, "inventory_sha256"):
            MODULE.validate_results(path, inventory, None)

    def test_review_requires_exact_production_behavior_evidence(self):
        inventory = self.inventory()
        for field in (
            "actual_behavior", "confidence", "consumer", "dependency_group",
            "display_context", "evidence_locations", "glossary_authority",
            "production_facts", "producers", "reentry_trigger",
            "rejected_alternatives", "reviewer_rationale",
        ):
            with self.subTest(missing=field):
                card = card_for(inventory)
                del card[field]
                with self.assertRaises(MODULE.InventoryError):
                    MODULE.validate_results(
                        self.write_results(inventory, [card]), inventory, None
                    )

        mutations = []
        card = card_for(inventory)
        card["actual_behavior"] += " drift"
        mutations.append(card)
        card = card_for(inventory)
        card["confidence"] = "certain"
        mutations.append(card)
        card = card_for(inventory)
        card["dependency_group"] += " drift"
        mutations.append(card)
        card = card_for(inventory)
        card["display_context"] += " drift"
        mutations.append(card)
        card = card_for(inventory)
        card["consumer"]["channel_routing"] = "wrong:1"
        mutations.append(card)
        card = card_for(inventory)
        card["production_facts"]["weights"][0] += 1
        mutations.append(card)
        card = card_for(inventory)
        card["production_facts"]["control_prefixes"][0] = "VISUAL"
        mutations.append(card)
        card = card_for(inventory)
        card["production_facts"]["runtime_tokens"][0][0] = "@the_monster@"
        mutations.append(card)
        card = card_for(inventory)
        card["producers"][0]["mode"] = "wrong"
        mutations.append(card)
        card = card_for(inventory)
        card["evidence_locations"].pop()
        mutations.append(card)
        card = card_for(inventory)
        card["glossary_authority"] = "docs/glossary.md@" + "0" * 64
        mutations.append(card)
        for index, mutated in enumerate(mutations):
            with self.subTest(drift=index):
                with self.assertRaises(MODULE.InventoryError):
                    MODULE.validate_results(
                        self.write_results(inventory, [mutated]), inventory, None
                    )

    def test_review_evidence_fields_reject_wrong_types_and_empty_values(self):
        inventory = self.inventory()
        mutations = (
            ("actual_behavior", ""),
            ("confidence", ""),
            ("consumer", []),
            ("dependency_group", []),
            ("display_context", ""),
            ("evidence_locations", {}),
            ("glossary_authority", None),
            ("production_facts", []),
            ("producers", {}),
            ("reentry_trigger", "  "),
            ("rejected_alternatives", []),
            ("rejected_alternatives", ["valid", "  "]),
            ("reviewer_rationale", 7),
        )
        for field, invalid in mutations:
            with self.subTest(field=field, invalid=invalid):
                card = card_for(inventory)
                card[field] = invalid
                with self.assertRaises(MODULE.InventoryError):
                    MODULE.validate_results(
                        self.write_results(inventory, [card]), inventory, None
                    )

    def test_adjust_and_retranslate_require_changed_proposals(self):
        inventory = self.inventory()
        for conclusion in ("adjust", "retranslate"):
            with self.subTest(conclusion=conclusion):
                card = card_for(inventory, conclusion)
                card["proposed_translation"][0] = "@The_monster@新译。"
                review = card["variant_reviews"][0]
                review["proposed_translation"] = card["proposed_translation"][0]
                review["terminal_conclusion"] = conclusion
                path = self.write_results(inventory, [card])
                MODULE.validate_results(path, inventory, None)

                broken = copy.deepcopy(card)
                broken["variant_reviews"][0]["proposed_translation"] = ZH_PATTERNS[0]
                path = self.write_results(inventory, [broken])
                with self.assertRaisesRegex(MODULE.InventoryError, "proposed_translation mismatch"):
                    MODULE.validate_results(path, inventory, None)

    def test_both_deferrals_require_owner_reason_and_reentry(self):
        inventory = self.inventory()
        for conclusion in ("defer terminology", "defer implementation"):
            with self.subTest(conclusion=conclusion):
                card = card_for(inventory, conclusion)
                card.update({"deferral_owner": "owner", "deferral_reason": "reason",
                             "reentry_trigger": "trigger"})
                review = card["variant_reviews"][0]
                review["terminal_conclusion"] = conclusion
                review.update({"deferral_owner": "owner", "deferral_reason": "reason",
                               "reentry_trigger": "trigger"})
                MODULE.validate_results(
                    self.write_results(inventory, [card]), inventory, None
                )
                del review["deferral_owner"]
                with self.assertRaisesRegex(MODULE.InventoryError, "deferral_owner"):
                    MODULE.validate_results(
                        self.write_results(inventory, [card]), inventory, None
                    )

        card = card_for(inventory, "defer")
        with self.assertRaisesRegex(MODULE.InventoryError, "nonterminal"):
            MODULE.validate_results(
                self.write_results(inventory, [card]), inventory, None
            )

    def test_candidate_exact_agreement_and_structure(self):
        inventory = self.inventory()
        candidate_zh_patterns = list(ZH_PATTERNS)
        candidate_zh_patterns[0] = "@The_monster@新译。"
        candidate_en = artifact("en", oid=CANDIDATE)
        candidate_zh = artifact("zh", candidate_zh_patterns, CANDIDATE)
        candidate_entries = self.add_candidate(inventory, candidate_en, candidate_zh)

        card = card_for(inventory, "retranslate")
        card["proposed_translation"][0] = candidate_zh_patterns[0]
        card["variant_reviews"][0]["proposed_translation"] = candidate_zh_patterns[0]
        card["variant_reviews"][0]["terminal_conclusion"] = "retranslate"
        path = self.write_results(inventory, [card])
        MODULE.validate_results(path, inventory, candidate_entries)

        bad = copy.deepcopy(card)
        bad["proposed_translation"][0] += "候选不一致"
        bad["variant_reviews"][0]["proposed_translation"] = bad["proposed_translation"][0]
        path = self.write_results(inventory, [bad])
        with self.assertRaisesRegex(MODULE.InventoryError, "candidate dump"):
            MODULE.validate_results(path, inventory, candidate_entries)

        drift = artifact("zh", candidate_zh_patterns, CANDIDATE)
        drift["entries"][0]["variants"][0]["weight"] = 31
        with self.assertRaisesRegex(MODULE.InventoryError, "topology"):
            self.add_candidate(self.inventory(), candidate_en, drift)

    def test_candidate_english_drift_is_rejected(self):
        inventory = self.inventory()
        drift = artifact("en", oid=CANDIDATE)
        drift["entries"][0]["variants"][0]["raw_pattern"] += " changed"
        with self.assertRaisesRegex(MODULE.InventoryError, "English drift"):
            self.add_candidate(inventory, drift, artifact("zh", oid=CANDIDATE))

    def test_candidate_must_descend_from_baseline(self):
        inventory = self.inventory()
        en_path = self.write_dump("candidate-en.json", artifact("en", oid=CANDIDATE))
        zh_path = self.write_dump("candidate-zh.json", artifact("zh", oid=CANDIDATE))
        with self.assertRaisesRegex(MODULE.InventoryError, "ancestor"):
            MODULE.add_candidate(inventory, NON_DESCENDANT, en_path, zh_path)

    def test_cli_exclusive_tmp_output(self):
        en_value = artifact("en")
        zh_value = artifact("zh")
        en_path = self.write_dump("cli-en.json", en_value)
        zh_path = self.write_dump("cli-zh.json", zh_value)
        output = Path("/private/tmp") / f"monflee-test-{id(self)}.json"
        arguments = [
            "--baseline-ref", BASELINE,
            "--english-dump", str(en_path), "--localized-dump", str(zh_path),
            "--glossary", str(self.glossary), "--inventory-output", str(output),
        ]
        with mock.patch.object(
            MODULE, "_trusted_artifacts_at_oid",
            return_value=(copy.deepcopy(en_value), copy.deepcopy(zh_value)),
        ):
            self.assertEqual(0, MODULE.main(arguments))
            with self.assertRaisesRegex(MODULE.InventoryError, "exclusively create"):
                MODULE.main(arguments)
        output.unlink()

        outside_arguments = arguments[:-1] + [str(self.root / "out.json")]
        with mock.patch.object(
            MODULE, "_trusted_artifacts_at_oid",
            return_value=(copy.deepcopy(en_value), copy.deepcopy(zh_value)),
        ):
            with self.assertRaisesRegex(MODULE.InventoryError, "/tmp"):
                MODULE.main(outside_arguments)


if __name__ == "__main__":
    unittest.main()
