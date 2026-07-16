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
                          "march of sorrows bone dragon cast"], candidates)
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

    def test_current_slice_rejects_unwired_binding_metadata(self):
        value = copy.deepcopy(MANIFEST)
        value["entries"][0]["variants"][0]["slot_schema"][2]["type"] = (
            "resolved_beam")
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "requires resolved_target"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        value["entries"][0]["variants"][0]["applicability"][
            "requires_foe"] = True
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "applicability metadata"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        value["entries"][0]["variants"][0]["line_metadata"][0][
            "behavior"]["implies_gesture"] = True
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "behavior metadata"):
            self.validate(value)


if __name__ == "__main__":
    unittest.main()
