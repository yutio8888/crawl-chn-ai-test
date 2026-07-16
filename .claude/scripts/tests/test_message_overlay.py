#!/usr/bin/env python3

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/generate_message_overlay.py"
SPEC = importlib.util.spec_from_file_location("generate_message_overlay", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)

MANIFEST = json.loads((ROOT / ".claude/data/message-overlay/monspell.json")
                      .read_text(encoding="utf-8"))
INVENTORY = json.loads((ROOT / ".claude/data/message-overlay/monspell-phase0-inventory.json")
                       .read_text(encoding="utf-8"))
SIDECAR = ROOT / "crawl-ref/source/fork-message-overlay.generated.inc"


class MessageOverlayTests(unittest.TestCase):
    def validate(self, manifest):
        return MODULE.validate_manifest(manifest, INVENTORY)

    def test_production_manifest_and_sidecar_are_exact(self):
        validated = self.validate(copy.deepcopy(MANIFEST))
        self.assertEqual(SIDECAR.read_text(encoding="utf-8"),
                         MODULE.render_sidecar(validated))
        candidates = [entry["canonical_key"] for entry in validated["entries"]
                      if entry["mode"] == "CANDIDATE"]
        self.assertEqual(["beam catchall cast",
                          "march of sorrows bone dragon cast",
                          "ensnare arachne cast",
                          "guardian serpent cast targeted",
                          "wizard cast targeted",
                          "wizard cast",
                          "magical cast targeted",
                          "magical cast",
                          "awaken flesh kobold fleshcrafter cast",
                          "dispel undead revenant cast",
                          "malign offering priest cast",
                          "sheza's dance cast",
                          "silent blizzard demon cast",
                          "ushabti cast targeted",
                          "mennas cast",
                          "airstrike blizzard demon cast",
                          "vv cast",
                          "smiting jeremiah cast",
                          "cantrip gastronok cast",
                          "hellfire mortar wiglaf cast"], candidates)
        nergalle = next(entry for entry in validated["entries"]
                        if "nergalle" in entry["canonical_key"])
        self.assertTrue(all(variant["materialization_policy"] == "LEGACY_ONLY"
                            for variant in nergalle["variants"]))

    def test_unknown_schema_is_rejected(self):
        value = copy.deepcopy(MANIFEST)
        value["schema_version"] = 99
        with self.assertRaisesRegex(MODULE.ManifestError, "unknown manifest"):
            self.validate(value)

    def test_incomplete_key_closure_is_rejected(self):
        value = copy.deepcopy(MANIFEST)
        value["entries"][1]["variants"].pop()
        with self.assertRaisesRegex(MODULE.ManifestError, "every selectable"):
            self.validate(value)

    def test_active_and_tombstone_ids_are_globally_unique(self):
        value = copy.deepcopy(MANIFEST)
        value["tombstones"] = [{
            "stable_id": value["entries"][0]["variants"][0]["stable_id"],
            "reason": "fixture",
        }]
        with self.assertRaisesRegex(MODULE.ManifestError, "reused active"):
            self.validate(value)

    def test_slot_and_template_invariants_are_blocking(self):
        value = copy.deepcopy(MANIFEST)
        value["entries"][0]["variants"][0]["slot_schema"][0]["name"] = "Bad"
        with self.assertRaisesRegex(MODULE.ManifestError, "slot schema"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        value["entries"][0]["variants"][0]["slot_schema"][0]["type"] = (
            "unknown_ref")
        with self.assertRaisesRegex(MODULE.ManifestError, "slot schema"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        template = value["entries"][0]["variants"][0]["line_metadata"][0]["templates"][0]
        template["pattern"] += " @target@"
        with self.assertRaisesRegex(MODULE.ManifestError, "legacy TextDB"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        line = value["entries"][0]["variants"][0]["line_metadata"][0]
        line["channel"] = "not_a_message_channel"
        with self.assertRaisesRegex(MODULE.ManifestError, "invalid channel"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        template = value["entries"][0]["variants"][0]["line_metadata"][0]["templates"][0]
        template["pattern"] += "\nsecond protocol line"
        with self.assertRaisesRegex(MODULE.ManifestError, "pattern"):
            self.validate(value)

    def test_fingerprint_tampering_is_rejected(self):
        for field in ("canonical_fingerprint", "selection_graph_fingerprint"):
            value = copy.deepcopy(MANIFEST)
            value["entries"][0][field] = "fnv1a64:0000000000000000"
            with self.assertRaisesRegex(MODULE.ManifestError, "fingerprint mismatch"):
                self.validate(value)

    def test_case_map_requires_dynamic_sites(self):
        value = copy.deepcopy(MANIFEST)
        value["entries"][0]["variants"][0]["materialization_policy"] = "CASE_MAP"
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "finite bracket sites"):
            self.validate(value)

    def test_case_map_requires_complete_unique_signatures(self):
        entry = next(e for e in MANIFEST["entries"]
                     if e["canonical_key"]
                     == "march of sorrows bone dragon cast")
        entry_index = MANIFEST["entries"].index(entry)

        value = copy.deepcopy(MANIFEST)
        value["entries"][entry_index]["variants"][0][
            "materialization_cases"].pop()
        with self.assertRaisesRegex(MODULE.ManifestError, "cases are incomplete"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        cases = value["entries"][entry_index]["variants"][0][
            "materialization_cases"]
        cases[1]["signature"] = cases[0]["signature"]
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "unknown/duplicate signature"):
            self.validate(value)

    def test_case_map_rejects_unconsumed_or_semantic_dynamic_data(self):
        entry = next(e for e in MANIFEST["entries"]
                     if e["canonical_key"]
                     == "march of sorrows bone dragon cast")
        entry_index = MANIFEST["entries"].index(entry)
        value = copy.deepcopy(MANIFEST)
        value["entries"][entry_index]["variants"][0]["line_metadata"] = (
            copy.deepcopy(value["entries"][entry_index]["variants"][0]
                          ["materialization_cases"][0]["line_metadata"]))
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "lines belong to cases"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        cases = value["entries"][entry_index]["variants"][0][
            "materialization_cases"]
        cases[1]["line_metadata"][0]["sensory"] = "VISUAL"
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "binding-relevant line metadata"):
            self.validate(value)

    def test_plural_arms_token_requires_the_narrow_slot_type(self):
        entry = next(e for e in MANIFEST["entries"]
                     if e["canonical_key"]
                     == "airstrike blizzard demon cast")
        entry_index = MANIFEST["entries"].index(entry)

        value = copy.deepcopy(MANIFEST)
        arms = value["entries"][entry_index]["variants"][2]
        arms["slot_schema"][2]["type"] = "actor_ref"
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "plural arms token/type mismatch"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        plain = value["entries"][entry_index]["variants"][0]
        plain["slot_schema"].append(
            { "name": "arms", "type": "actor_arms_plural" })
        plain["required_arguments"].append("arms")
        plain["line_metadata"][0]["templates"][0]["pattern"] += " ${arms}"
        plain["line_metadata"][0]["templates"][1]["pattern"] += "${arms}"
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "plural arms token/type mismatch"):
            self.validate(value)

    def test_binding_relation_contract_is_fail_closed(self):
        value = copy.deepcopy(MANIFEST)
        value["entries"][0]["variants"][0]["binding"][
            "resolves_target"] = False
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "non-target binding declares"):
            self.validate(value)

        untargeted = next(e for e in MANIFEST["entries"]
                          if e["canonical_key"] == "wizard cast")
        untargeted_index = MANIFEST["entries"].index(untargeted)
        value = copy.deepcopy(MANIFEST)
        value["entries"][untargeted_index]["variants"][0][
            "slot_schema"].append(
                { "name": "target", "type": "resolved_target" })
        value["entries"][untargeted_index]["variants"][0][
            "required_arguments"].append("target")
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "non-target binding declares"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        value["entries"][untargeted_index]["variants"][0][
            "line_metadata"][0]["templates"][0]["relation"] = "AT"
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "invalid/duplicate language relation"):
            self.validate(value)

        targeted = next(e for e in MANIFEST["entries"]
                        if e["canonical_key"] == "wizard cast targeted")
        targeted_index = MANIFEST["entries"].index(targeted)
        value = copy.deepcopy(MANIFEST)
        value["entries"][targeted_index]["variants"][0][
            "line_metadata"][0]["templates"][0]["relation"] = "NONE"
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "invalid/duplicate language relation"):
            self.validate(value)

    def test_current_slice_rejects_unwired_metadata(self):
        for field in ("requires_named_foe", "requires_god"):
            value = copy.deepcopy(MANIFEST)
            value["entries"][0]["variants"][0]["applicability"][
                field] = True
            with self.subTest(field=field):
                with self.assertRaisesRegex(MODULE.ManifestError,
                                            "applicability metadata"):
                    self.validate(value)

        value = copy.deepcopy(MANIFEST)
        value["entries"][0]["variants"][0]["line_metadata"][0][
            "behavior"]["audible"] = True
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "audible behavior metadata"):
            self.validate(value)

    def test_phase2_gesture_metadata_is_variant_exact(self):
        expected = {
            "ensnare arachne cast": [True, False],
            "guardian serpent cast targeted": [False, True, False],
            "wizard cast targeted": [True, True, False],
            "wizard cast": [True, False, False],
            "magical cast targeted": [True],
            "magical cast": [True],
            "awaken flesh kobold fleshcrafter cast": [True, False],
            "dispel undead revenant cast": [True],
            "malign offering priest cast": [True],
            "sheza's dance cast": [False, True],
            "silent blizzard demon cast": [False, True],
            "ushabti cast targeted": [True],
            "mennas cast": [True],
            "airstrike blizzard demon cast": [False, True, False],
            "vv cast": [True, False, False, False],
            "smiting jeremiah cast": [False, False, False, False, False],
            "cantrip gastronok cast": [False] * 9,
            "hellfire mortar wiglaf cast": [False, False, False],
        }
        for key, gestures in expected.items():
            entry = next(e for e in MANIFEST["entries"]
                         if e["canonical_key"] == key)
            self.assertEqual(
                gestures,
                [variant["line_metadata"][0]["behavior"]["implies_gesture"]
                 for variant in entry["variants"]])

    def test_gastronok_visibility_applicability_is_variant_exact(self):
        entry = next(e for e in MANIFEST["entries"]
                     if e["canonical_key"] == "cantrip gastronok cast")
        self.assertEqual(
            [False, True, True, True, False, False, False, False, False],
            [variant["applicability"]["requires_caster_visible"]
             for variant in entry["variants"]])
        self.assertEqual(
            [False, False, False, False, True, True, True, True, True],
            [variant["applicability"]["requires_player"]
             for variant in entry["variants"]])

    def test_wiglaf_applicability_and_foe_slots_are_variant_exact(self):
        entry = next(e for e in MANIFEST["entries"]
                     if e["canonical_key"] == "hellfire mortar wiglaf cast")
        self.assertEqual(
            [True, False, False],
            [variant["applicability"]["requires_caster_visible"]
             for variant in entry["variants"]])
        self.assertEqual(
            [False, True, True],
            [variant["applicability"]["requires_foe"]
             for variant in entry["variants"]])
        self.assertEqual(
            [False, True, True],
            [any(slot["type"] == "resolved_foe"
                 for slot in variant["slot_schema"])
             for variant in entry["variants"]])

    def test_target_binding_selects_exact_relation_schema(self):
        for entry in MANIFEST["entries"]:
            if entry["mode"] != "CANDIDATE":
                continue
            for variant in entry["variants"]:
                resolves_target = variant["binding"]["resolves_target"]
                expected = ({"AT", "NEXT_TO", "PAST"}
                            if resolves_target else {"NONE"})
                lines = variant["line_metadata"]
                for case in variant["materialization_cases"]:
                    lines = lines + case["line_metadata"]
                self.assertTrue(lines)
                for line in lines:
                    by_language = {}
                    for template in line["templates"]:
                        by_language.setdefault(
                            template["language"], set()).add(
                                template["relation"])
                    self.assertEqual(
                        {language: expected
                         for language in MANIFEST["supported_languages"]},
                        by_language)
                if not resolves_target:
                    self.assertNotIn(
                        "resolved_target",
                        {slot["type"] for slot in variant["slot_schema"]})


if __name__ == "__main__":
    unittest.main()
