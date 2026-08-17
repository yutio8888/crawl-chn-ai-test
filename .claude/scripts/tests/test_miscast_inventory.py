#!/usr/bin/env python3

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/miscast_inventory.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("miscast_inventory", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BASELINE = "aaafab60aff68e631df0fd2b6136075166045267"
RESULTS = ROOT / "docs/miscast-review-results.md"


def exact_artifact(oid: str, directory: str) -> dict:
    scoped = MODULE.shared._derive_scoped_dump(
        oid, directory, f"fixture {directory}",
        source_basename=MODULE.SOURCE_BASENAME,
    )
    dependencies = MODULE.shared._derive_scoped_from_sources(
        copy.deepcopy(scoped["sources"]), directory, f"fixture {directory}",
        source_basename="colourname.txt",
    )
    entries = sorted(
        [*copy.deepcopy(scoped["entries"]),
         *copy.deepcopy(dependencies["entries"])],
        key=lambda entry: entry["canonical_key"],
    )
    return {
        "schema_version": 1,
        "database_name": "speak",
        "source_directory": directory,
        "sources": copy.deepcopy(scoped["sources"]),
        "entries": entries,
    }


class MiscastInventoryTests(unittest.TestCase):
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
        records = MODULE._strict_block(RESULTS)
        # The checked-in ledger binds the real production-dump byte hashes.
        # The synthetic artifacts above exercise the same exact-Git derivation
        # but have different JSON serialization bytes, so align only those two
        # metadata bindings for strict-ledger mutation tests.
        cls.inventory["dumps"]["english"]["artifact_sha256"] = records[0][
            "english_production_dump_sha256"
        ]
        cls.inventory["dumps"]["localized"]["artifact_sha256"] = records[0][
            "chinese_production_dump_sha256"
        ]
        cls.records = records

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

    def validate(self, records: list[dict] | None = None, candidate=None):
        return MODULE.validate_results(
            self.write_records(copy.deepcopy(records or self.records)),
            self.inventory, candidate,
        )

    def test_exact_git_inventory_and_checked_in_ledger_pass(self):
        loaded = self.validate()
        self.assertEqual(33, len(self.inventory["entries"]))
        self.assertEqual(
            193,
            sum(len(entry["variants"]) for entry in self.inventory["entries"]),
        )
        self.assertEqual(33, len(loaded["cards"]))
        self.assertEqual(
            25,
            sum(
                len(variant["selection_sites_english"])
                for entry in self.inventory["entries"]
                for variant in entry["variants"]
            ),
        )
        self.assertEqual(
            [MODULE.GRAMMAR_EXCEPTION], loaded["metadata"]["grammar_exceptions"]
        )

    def test_exact_identity_set_and_weight_order_mutations_fail(self):
        renamed = copy.deepcopy(self.en_artifact)
        entry = next(
            entry for entry in renamed["entries"]
            if entry["canonical_key"] == MODULE.EXPECTED_KEYS[0]
        )
        entry["canonical_key"] = "replacement miscast player"
        for variant in entry["variants"]:
            variant["locator"]["canonical_key"] = entry["canonical_key"]
        with self.assertRaisesRegex(MODULE.InventoryError, "key set mismatch"):
            MODULE._dump_binding(renamed, b"fixture", "fixture EN")

        _en_binding, en_rows = MODULE._dump_binding(
            self.en_artifact, b"fixture EN", "fixture EN"
        )
        _zh_binding, zh_rows = MODULE._dump_binding(
            self.zh_artifact, b"fixture ZH", "fixture ZH"
        )
        zh_rows[0]["variants"][0]["weight"] += 1
        with self.assertRaisesRegex(MODULE.InventoryError, "weight/order"):
            MODULE._pair_rows(en_rows, zh_rows, "fixture")

    def test_shared_derivation_is_parameterized_without_a_second_parser(self):
        source = {
            "source_name": "database/miscast.txt", "load_index": 0,
            "normalized_utf8": "%%%%\nprobe miscast player\n\nmessage\n%%%%\n",
        }
        derived = MODULE.shared._derive_scoped_from_sources(
            [source], "database/", "fixture", source_basename="miscast.txt"
        )
        self.assertEqual(
            ["probe miscast player"],
            [entry["canonical_key"] for entry in derived["entries"]],
        )
        empty = MODULE.shared._derive_scoped_from_sources(
            [source], "database/", "fixture", source_basename="monflee.txt"
        )
        self.assertEqual([], empty["entries"])

    def test_unknown_fields_fail_closed_at_every_ledger_level(self):
        mutations = []
        for record_index, nested in (
            (0, None), (1, None), (1, "production_facts"),
            (1, "variant_reviews"),
        ):
            records = copy.deepcopy(self.records)
            if nested is None:
                records[record_index]["unknown"] = True
            elif nested == "production_facts":
                records[record_index][nested]["unknown"] = True
            else:
                records[record_index][nested][0]["unknown"] = True
            mutations.append(records)
        for records in mutations:
            with self.subTest(level=len(mutations)):
                with self.assertRaisesRegex(MODULE.InventoryError, "unknown"):
                    self.validate(records)

    def test_runtime_evidence_and_provenance_drift_fail_closed(self):
        mutations = []
        records = copy.deepcopy(self.records)
        records[1]["actual_behavior"] += " drift"
        mutations.append((records, "actual_behavior"))
        records = copy.deepcopy(self.records)
        records[1]["consumer"]["final_punctuation"] = "wrong:1"
        mutations.append((records, "consumer"))
        records = copy.deepcopy(self.records)
        records[1]["evidence_locations"][0] = (
            "crawl-ref/source/dat/database/miscast.txt:1"
        )
        mutations.append((records, "evidence_locations"))
        records = copy.deepcopy(self.records)
        records[1]["production_facts"]["effective_provenance"]["english"][
            "load_index"
        ] = 8
        mutations.append((records, "production_facts"))
        records = copy.deepcopy(self.records)
        records[1]["production_facts"]["final_punctuation"] = "wrong"
        mutations.append((records, "production_facts"))
        for records, message in mutations:
            with self.subTest(message=message):
                with self.assertRaisesRegex(MODULE.InventoryError, message):
                    self.validate(records)

    def test_earth_message_precedes_special_damage_and_uses_fixed_period(self):
        earth_cards = [
            card for card in self.records[1:]
            if card["key"].startswith("earth miscast ")
        ]
        self.assertEqual(3, len(earth_cards))
        for card in earth_cards:
            self.assertIn("BEAM_NONE 令 _do_msg(..., 0)", card["actual_behavior"])
            self.assertEqual(
                MODULE.WEAK_PUNCTUATION,
                card["production_facts"]["final_punctuation"],
            )
            self.assertEqual(
                {MODULE.WEAK_PUNCTUATION},
                {review["final_message_punctuation"]
                 for review in card["variant_reviews"]},
            )

        records = copy.deepcopy(self.records)
        earth = next(
            card for card in records[1:]
            if card["key"] == "earth miscast player"
        )
        earth["production_facts"]["final_punctuation"] = (
            MODULE.DAMAGE_PUNCTUATION
        )
        with self.assertRaisesRegex(MODULE.InventoryError, "production_facts"):
            self.validate(records)

    def test_boolean_integer_fields_fail_closed(self):
        mutations = []
        records = copy.deepcopy(self.records)
        records[0]["identity_count"] = True
        mutations.append(records)
        records = copy.deepcopy(self.records)
        records[1]["production_facts"]["variant_count"] = True
        mutations.append(records)
        records = copy.deepcopy(self.records)
        records[1]["production_facts"]["weights"][0] = True
        mutations.append(records)
        records = copy.deepcopy(self.records)
        records[1]["production_facts"]["choice_site_counts"][
            "english"
        ] = False
        mutations.append(records)
        records = copy.deepcopy(self.records)
        records[1]["production_facts"]["source_history_length"][
            "english"
        ] = True
        mutations.append(records)
        records = copy.deepcopy(self.records)
        records[1]["production_facts"]["effective_provenance"]["english"][
            "definition_ordinal"
        ] = False
        mutations.append(records)
        records = copy.deepcopy(self.records)
        records[0]["terminal_conclusion_counts"]["keep"] = True
        mutations.append(records)
        records = copy.deepcopy(self.records)
        records[0]["grammar_exceptions"][0]["variant_ordinal"] = True
        mutations.append(records)
        records = copy.deepcopy(self.records)
        records[1]["variant_reviews"][0]["variant_ordinal"] = False
        mutations.append(records)
        records = copy.deepcopy(self.records)
        records[1]["variant_reviews"][0]["weight"] = True
        mutations.append(records)
        records = copy.deepcopy(self.records)
        selection_review = next(
            review
            for card in records[1:]
            for review in card["variant_reviews"]
            if review["selection_sites"]["english"]
        )
        selection_review["selection_sites"]["english"][0][
            "alternative_count"
        ] = True
        mutations.append(records)
        for records in mutations:
            with self.assertRaisesRegex(MODULE.InventoryError, "integer"):
                self.validate(records)

    def test_card_and_variant_coverage_duplicate_extra_missing_fail(self):
        for mutate in (
            lambda records: records.pop(),
            lambda records: records.append(copy.deepcopy(records[-1])),
            lambda records: records.__setitem__(1, copy.deepcopy(records[2])),
        ):
            records = copy.deepcopy(self.records)
            mutate(records)
            with self.assertRaisesRegex(
                MODULE.InventoryError, "coverage|duplicate|extra|missing|order"
            ):
                self.validate(records)

        for mutate in (
            lambda reviews: reviews.pop(),
            lambda reviews: reviews.append(copy.deepcopy(reviews[-1])),
            lambda reviews: reviews.__setitem__(0, copy.deepcopy(reviews[1])),
        ):
            records = copy.deepcopy(self.records)
            mutate(records[1]["variant_reviews"])
            with self.assertRaisesRegex(
                MODULE.InventoryError, "coverage|duplicate|extra|missing|unordered"
            ):
                self.validate(records)

    def test_token_exception_is_exact_and_other_token_drift_fails(self):
        ice = next(
            card for card in self.records[1:]
            if card["identity"] == MODULE.GRAMMAR_EXCEPTION["identity"]
        )
        self.assertEqual(
            ["@hands@"],
            ice["variant_reviews"][2]["runtime_tokens"]["chinese_candidate"],
        )
        records = copy.deepcopy(self.records)
        card = next(
            card for card in records[1:]
            if card["identity"] == "miscast:conjuration miscast monster"
        )
        ordinal = next(
            index for index, pattern in enumerate(card["proposed_translation"])
            if "@The_monster@" in pattern
        )
        card["proposed_translation"][ordinal] = card[
            "proposed_translation"
        ][ordinal].replace("@The_monster@", "@the_monster@")
        card["variant_reviews"][ordinal]["proposed_translation"] = card[
            "proposed_translation"
        ][ordinal]
        with self.assertRaisesRegex(MODULE.InventoryError, "token topology"):
            self.validate(records)

        records = copy.deepcopy(self.records)
        card = next(
            card for card in records[1:]
            if card["identity"] == "miscast:conjuration miscast monster"
        )
        ordinal = next(
            index for index, pattern in enumerate(card["proposed_translation"])
            if "@The_monster@" in pattern
        )
        card["proposed_translation"][ordinal] = card[
            "proposed_translation"
        ][ordinal].replace("@The_monster@", "@mystery@")
        with self.assertRaisesRegex(MODULE.InventoryError, "unknown proposed token"):
            self.validate(records)

    def test_choice_shape_and_all_five_body_locators_are_enforced(self):
        body_reviews = [
            review
            for card in self.records[1:]
            for review in card["variant_reviews"]
            if review["body_skin_strategy"] is not None
        ]
        self.assertEqual(5, len(body_reviews))

        records = copy.deepcopy(self.records)
        card = next(
            card for card in records[1:]
            if card["identity"] == "miscast:hexes miscast monster"
        )
        card["proposed_translation"][4] = (
            "@The_monster_possessive@身体短暂地泛起光芒"
        )
        card["variant_reviews"][4]["proposed_translation"] = card[
            "proposed_translation"
        ][4]
        with self.assertRaisesRegex(MODULE.InventoryError, "body-neutral"):
            self.validate(records)

        records = copy.deepcopy(self.records)
        card = next(
            card for card in records[1:]
            if card["identity"] == "miscast:translocation miscast player"
        )
        card["proposed_translation"][8] = card["proposed_translation"][8].replace(
            "[弯曲|扭曲]", "[弯曲|扭曲|折叠]"
        )
        card["variant_reviews"][8]["proposed_translation"] = card[
            "proposed_translation"
        ][8]
        with self.assertRaisesRegex(MODULE.InventoryError, "choice topology"):
            self.validate(records)

    def test_recursive_and_caller_token_classification_fails_closed(self):
        missing = copy.deepcopy(self.en_artifact)
        missing["entries"] = [
            entry for entry in missing["entries"]
            if entry["canonical_key"] != "any_colour"
        ]
        with self.assertRaisesRegex(MODULE.InventoryError, "no effective TextDB"):
            MODULE._dependency_binding(missing, "fixture")

        caller = copy.deepcopy(self.en_artifact)
        dependency = copy.deepcopy(next(
            entry for entry in caller["entries"]
            if entry["canonical_key"] == "any_colour"
        ))
        dependency["canonical_key"] = "hands"
        caller["entries"].append(dependency)
        with self.assertRaisesRegex(MODULE.InventoryError, "unexpectedly resolves"):
            MODULE._dependency_binding(caller, "fixture")

        forged = copy.deepcopy(self.en_artifact)
        dependency = next(
            entry for entry in forged["entries"]
            if entry["canonical_key"] == "any_colour"
        )
        dependency["raw_body"] += "forged"
        forged_path = self.root / "forged-recursive-en.json"
        forged_path.write_text(
            json.dumps(forged, ensure_ascii=False), encoding="utf-8"
        )
        with self.assertRaisesRegex(MODULE.InventoryError, "scoped history"):
            MODULE.build_inventory(
                BASELINE, forged_path, self.zh_path, ROOT / "docs/glossary.md"
            )

    def test_candidate_must_match_every_proposal_variant(self):
        candidate = copy.deepcopy(self.inventory["entries"])
        proposed = {
            card["identity"]: card["proposed_translation"]
            for card in self.records[1:]
        }
        for entry in candidate:
            for variant, pattern in zip(
                entry["variants"], proposed[entry["identity"]]
            ):
                variant["chinese"] = pattern
        self.validate(candidate=candidate)
        candidate[0]["variants"][0]["chinese"] += "漂移"
        with self.assertRaisesRegex(MODULE.InventoryError, "candidate ZH dump"):
            self.validate(candidate=candidate)

    def test_candidate_checkout_requires_exact_head_and_clean_tree(self):
        ancestor = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        clean = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        exact = subprocess.CompletedProcess(
            [], 0, stdout="f" * 40 + "\n", stderr=""
        )
        with mock.patch.object(MODULE.shared, "_validate_oid"), \
                mock.patch.object(
                    MODULE.shared.subprocess, "run",
                    side_effect=[ancestor, exact, clean],
                ):
            MODULE.shared._require_candidate_commit(
                BASELINE, "f" * 40, exact_clean_checkout=True
            )
        dirty = subprocess.CompletedProcess(
            [], 0, stdout=" M candidate\n", stderr=""
        )
        with mock.patch.object(MODULE.shared, "_validate_oid"), \
                mock.patch.object(
                    MODULE.shared.subprocess, "run",
                    side_effect=[ancestor, exact, dirty],
                ):
            with self.assertRaisesRegex(MODULE.InventoryError, "clean"):
                MODULE.shared._require_candidate_commit(
                    BASELINE, "f" * 40, exact_clean_checkout=True
                )
        wrong = subprocess.CompletedProcess(
            [], 0, stdout="e" * 40 + "\n", stderr=""
        )
        with mock.patch.object(MODULE.shared, "_validate_oid"), \
                mock.patch.object(
                    MODULE.shared.subprocess, "run",
                    side_effect=[ancestor, wrong],
                ):
            with self.assertRaisesRegex(MODULE.InventoryError, "exact"):
                MODULE.shared._require_candidate_commit(
                    BASELINE, "f" * 40, exact_clean_checkout=True
                )


if __name__ == "__main__":
    unittest.main()
