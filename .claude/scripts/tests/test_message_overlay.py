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
        self.assertEqual(["beam catchall cast"], candidates)
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

    def test_unimplemented_materialization_policy_is_rejected(self):
        value = copy.deepcopy(MANIFEST)
        value["entries"][0]["variants"][0]["materialization_policy"] = "CASE_MAP"
        with self.assertRaisesRegex(MODULE.ManifestError, "not enabled yet"):
            self.validate(value)


if __name__ == "__main__":
    unittest.main()
