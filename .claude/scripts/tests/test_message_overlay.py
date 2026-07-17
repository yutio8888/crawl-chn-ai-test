#!/usr/bin/env python3

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/generate_message_overlay.py"
SPEC = importlib.util.spec_from_file_location("generate_message_overlay", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)

MANIFEST_PATH = ROOT / ".claude/data/message-overlay/monspell.json"
MANIFEST = MODULE.load_manifest(MANIFEST_PATH)
INVENTORY = json.loads((ROOT / ".claude/data/message-overlay/monspell-phase0-inventory.json")
                       .read_text(encoding="utf-8"))
SIDECAR = ROOT / "crawl-ref/source/fork-message-overlay.generated.inc"


class MessageOverlayTests(unittest.TestCase):
    def entry(self, manifest, key):
        return next(entry for entry in manifest["entries"]
                    if entry["canonical_key"] == key)

    def variant(self, manifest, key, ordinal=0):
        return next(variant for variant in self.entry(manifest, key)["variants"]
                    if variant["variant_ordinal"] == ordinal)

    def fragmented_manifest(self, directory, fragments):
        root = Path(directory)
        names = []
        for ordinal, fragment in enumerate(fragments):
            name = f"fragment-{ordinal}.json"
            (root / name).write_text(json.dumps(fragment, ensure_ascii=False),
                                     encoding="utf-8")
            names.append(name)
        header = {
            "schema_version": MANIFEST["schema_version"],
            "domain": MANIFEST["domain"],
            "inventory_semantic_fingerprint":
                MANIFEST["inventory_semantic_fingerprint"],
            "supported_languages": MANIFEST["supported_languages"],
            "catalog_order": [entry["canonical_key"]
                              for entry in MANIFEST["entries"]],
            "fragments": names,
        }
        path = root / "monspell.json"
        path.write_text(json.dumps(header), encoding="utf-8")
        return path

    def test_fragment_aggregation_is_order_stable(self):
        entries = copy.deepcopy(MANIFEST["entries"])
        for entry in entries:
            entry["variants"].reverse()
            for variant in entry["variants"]:
                variant["materialization_cases"].reverse()
        midpoint = len(entries) // 2
        with tempfile.TemporaryDirectory() as tmp:
            path = self.fragmented_manifest(tmp, [
                {"entries": list(reversed(entries[midpoint:])),
                 "tombstones": []},
                {"entries": list(reversed(entries[:midpoint])),
                 "tombstones": []},
            ])
            aggregated = self.validate(MODULE.load_manifest(path))
        self.assertEqual(MODULE.render_sidecar(self.validate(
                             copy.deepcopy(MANIFEST))),
                         MODULE.render_sidecar(aggregated))

    def test_fragment_duplicate_key_is_rejected_globally(self):
        duplicate = copy.deepcopy(MANIFEST["entries"][0])
        with tempfile.TemporaryDirectory() as tmp:
            path = self.fragmented_manifest(tmp, [
                {"entries": copy.deepcopy(MANIFEST["entries"]),
                 "tombstones": []},
                {"entries": [duplicate], "tombstones": []},
            ])
            with self.assertRaisesRegex(MODULE.ManifestError,
                                        "duplicate canonical_key"):
                self.validate(MODULE.load_manifest(path))

    def test_fragment_active_and_tombstone_id_conflict_is_rejected(self):
        stable_id = MANIFEST["entries"][0]["variants"][0]["stable_id"]
        with tempfile.TemporaryDirectory() as tmp:
            path = self.fragmented_manifest(tmp, [
                {"entries": copy.deepcopy(MANIFEST["entries"]),
                 "tombstones": []},
                {"entries": [], "tombstones": [
                    {"stable_id": stable_id, "reason": "fixture"},
                ]},
            ])
            with self.assertRaisesRegex(MODULE.ManifestError,
                                        "reused active stable_id"):
                self.validate(MODULE.load_manifest(path))

    def test_fragment_active_ids_are_globally_unique(self):
        entries = copy.deepcopy(MANIFEST["entries"])
        entries[1]["variants"][0]["stable_id"] = (
            entries[0]["variants"][0]["stable_id"])
        with tempfile.TemporaryDirectory() as tmp:
            path = self.fragmented_manifest(tmp, [
                {"entries": entries[:1], "tombstones": []},
                {"entries": entries[1:], "tombstones": []},
            ])
            with self.assertRaisesRegex(MODULE.ManifestError,
                                        "reused active stable_id"):
                self.validate(MODULE.load_manifest(path))

    def test_fragment_tombstones_are_sorted_and_globally_unique(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.fragmented_manifest(tmp, [
                {"entries": copy.deepcopy(MANIFEST["entries"]),
                 "tombstones": [
                     {"stable_id": "retired.z", "reason": "fixture"},
                 ]},
                {"entries": [], "tombstones": [
                     {"stable_id": "retired.a", "reason": "fixture"},
                ]},
            ])
            aggregated = MODULE.load_manifest(path)
            self.assertEqual(["retired.a", "retired.z"],
                             [item["stable_id"]
                              for item in aggregated["tombstones"]])
            self.validate(aggregated)

            duplicate = json.loads(path.read_text(encoding="utf-8"))
            duplicate["fragments"].append("duplicate.json")
            path.write_text(json.dumps(duplicate), encoding="utf-8")
            (Path(tmp) / "duplicate.json").write_text(json.dumps({
                "entries": [],
                "tombstones": [
                    {"stable_id": "retired.a", "reason": "fixture"},
                ],
            }), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ManifestError,
                                        "duplicate stable_id"):
                self.validate(MODULE.load_manifest(path))

    def validate(self, manifest):
        return MODULE.validate_manifest(manifest, INVENTORY)

    def validate_inventory(self, inventory):
        manifest = copy.deepcopy(MANIFEST)
        node = next(
            entry for entry in inventory["closure"]["additional_nodes"]
            if entry["key"] == "orc name")
        variant = next(
            entry for entry in manifest["entries"]
            if entry["canonical_key"]
               == "vanquished vanguard nergalle cast")["variants"][0]
        variant["recursive_dependency_fingerprints"]["orc name"] = (
            MODULE.runtime_canonical_fingerprint(node))
        return MODULE.validate_manifest(manifest, inventory)

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
                          "hellfire mortar wiglaf cast",
                          "vanquished vanguard nergalle cast",
                          "acid ball nascent plasmodium cast",
                          "airstrike wind drake cast",
                          "battlecry cast",
                          "battlecry cherub cast",
                          "battlecry satyr cast",
                          "beckoning gale chonchon cast",
                          "beckoning gale hippogriff cast",
                          "berserker rage rupert cast",
                          "blinkbolt cast",
                          "blizzard demon cast",
                          "bolt of draining natural cast",
                          "bolt of fire ophan cast",
                          "bolt of flesh kobold fleshcrafter cast",
                          "bolt of magma molten gargoyle cast",
                          "bombardier beetle cast",
                          "call lost souls cast",
                          "call of chaos cast",
                          "cause fear satyr cast",
                          "clockroach cast",
                          "cognitogaunt cast",
                          "cold breath cast",
                          "conjure living spells cast",
                          "corrupting pulse wretched star cast",
                          "crab cast targeted",
                          "creeping frost cast",
                          "crystal echidna cast targeted",
                          "culicivora cast targeted",
                          "curse skull cast",
                          "death rattle ushabti cast",
                          "dissolution cast",
                          "dragon cast",
                          "dragon cast targeted",
                          "druid's call cast",
                          "dryad cast",
                          "eidolon cast targeted",
                          "electrical bolt shock serpent cast",
                          "enfeeble zykzyl cast",
                          "ensnare natural cast",
                          "eye of draining cast",
                          "fire breath cast",
                          "fireball hell hog cast",
                          "floating eye cast",
                          "floating eye cast targeted",
                          "force lance polterguardian cast",
                          "formless jellyfish cast",
                          "freeze cast",
                          "geryon cast",
                          "ghost moth cast",
                          "ghost moth cast targeted",
                          "ghostly fireball revenant cast",
                          "glowing orange brain cast",
                          "grasping roots cast",
                          "grasping roots natural cast",
                          "guardian serpent cast",
                          "hoarfrost bullet cast",
                          "holy flames cast",
                          "hurl torchlight cast",
                          "invisibility shadowghast cast",
                          "manifold assault natural cast",
                          "mara summon cast",
                          "minor healing dryad cast",
                          "orange crystal statue cast",
                          "ostracise cast",
                          "phantom mirror cast",
                          "poisonous cloud natural cast",
                          "pyroclastic surge cast",
                          "silent berserker rage rupert cast",
                          "spectral cloud revenant cast",
                          "steam ball natural cast",
                          "sticks to snakes cast",
                          "sticky flame cast",
                          "summon mortal champion fravashi cast",
                          "symbol of torment cast",
                          "thrashing horror cast",
                          "undertaker cast targeted",
                          "unseen airstrike cast",
                          "unseen blinkbolt cast",
                          "unseen bolt of fire ophan cast",
                          "unseen curse skull cast",
                          "unseen dragon cast",
                          "unseen ensnare arachne cast",
                          "unseen ensnare natural cast",
                          "unseen mara summon cast",
                          "unseen non-humanoid wizard cast",
                          "unseen thermic dynamo cast",
                          "unseen vv cast",
                          "unseen warning cry cast",
                          "unseen warning cry howler monkey cast",
                          "unseen warning cry seraph cast",
                          "unseen warning cry ushabti cast",
                          "unseen warning cry vault sentinel cast",
                          "unseen weeping skull cast",
                          "unseen wizard cast",
                          "vhi's electrolunge cast",
                          "warning cry cast",
                          "warning cry hippogriff cast",
                          "warning cry howler monkey cast",
                          "warning cry ushabti cast",
                          "warning cry vault sentinel cast",
                          "weakening gaze cast",
                          "wind blast cast",
                          "wind blast wind drake cast",
                          "woodweal cast",
                          "wretched star cast"], candidates)
        self.assertEqual(
            ["acid splash cast", "branch summon cast prefix",
             "chilling breath cast"],
            [entry["canonical_key"] for entry in validated["entries"]
             if entry["mode"] == "LEGACY_ONLY"])
        nergalle = next(entry for entry in validated["entries"]
                        if "nergalle" in entry["canonical_key"])
        self.assertEqual(
            ["CAPTURE_SLOT", "NONE"],
            [variant["materialization_policy"]
             for variant in nergalle["variants"]])

    def test_unknown_schema_is_rejected(self):
        value = copy.deepcopy(MANIFEST)
        value["schema_version"] = 99
        with self.assertRaisesRegex(MODULE.ManifestError, "unknown manifest"):
            self.validate(value)

    def test_incomplete_key_closure_is_rejected(self):
        value = copy.deepcopy(MANIFEST)
        self.entry(value, "march of sorrows bone dragon cast")["variants"].pop()
        with self.assertRaisesRegex(MODULE.ManifestError, "every selectable"):
            self.validate(value)

    def test_active_and_tombstone_ids_are_globally_unique(self):
        value = copy.deepcopy(MANIFEST)
        value["tombstones"] = [{
            "stable_id": self.entry(value, "beam catchall cast")["variants"][0]["stable_id"],
            "reason": "fixture",
        }]
        with self.assertRaisesRegex(MODULE.ManifestError, "reused active"):
            self.validate(value)

    def test_slot_and_template_invariants_are_blocking(self):
        value = copy.deepcopy(MANIFEST)
        self.entry(value, "beam catchall cast")["variants"][0]["slot_schema"][0]["name"] = "Bad"
        with self.assertRaisesRegex(MODULE.ManifestError, "slot schema"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        self.entry(value, "beam catchall cast")["variants"][0]["slot_schema"][0]["type"] = (
            "unknown_ref")
        with self.assertRaisesRegex(MODULE.ManifestError, "slot schema"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        template = self.entry(value, "beam catchall cast")["variants"][0]["line_metadata"][0]["templates"][0]
        template["pattern"] += " @target@"
        with self.assertRaisesRegex(MODULE.ManifestError, "legacy TextDB"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        line = self.entry(value, "beam catchall cast")["variants"][0]["line_metadata"][0]
        line["channel"] = "not_a_message_channel"
        with self.assertRaisesRegex(MODULE.ManifestError, "invalid channel"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        template = self.entry(value, "beam catchall cast")["variants"][0]["line_metadata"][0]["templates"][0]
        template["pattern"] += "\nsecond protocol line"
        with self.assertRaisesRegex(MODULE.ManifestError, "pattern"):
            self.validate(value)

    def test_fingerprint_tampering_is_rejected(self):
        for field in ("canonical_fingerprint", "selection_graph_fingerprint"):
            value = copy.deepcopy(MANIFEST)
            self.entry(value, "beam catchall cast")[field] = "fnv1a64:0000000000000000"
            with self.assertRaisesRegex(MODULE.ManifestError, "fingerprint mismatch"):
                self.validate(value)

    def test_case_map_requires_dynamic_sites(self):
        value = copy.deepcopy(MANIFEST)
        self.entry(value, "beam catchall cast")["variants"][0]["materialization_policy"] = "CASE_MAP"
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "finite bracket sites"):
            self.validate(value)

    def test_case_map_requires_complete_unique_signatures(self):
        entry = next(e for e in MANIFEST["entries"]
                     if e["canonical_key"]
                     == "march of sorrows bone dragon cast")
        value = copy.deepcopy(MANIFEST)
        self.variant(value, entry["canonical_key"])[
            "materialization_cases"].pop()
        with self.assertRaisesRegex(MODULE.ManifestError, "cases are incomplete"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        cases = self.variant(value, entry["canonical_key"])[
            "materialization_cases"]
        cases[1]["signature"] = cases[0]["signature"]
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "unknown/duplicate signature"):
            self.validate(value)

    def test_case_map_rejects_unconsumed_or_semantic_dynamic_data(self):
        entry = next(e for e in MANIFEST["entries"]
                     if e["canonical_key"]
                     == "march of sorrows bone dragon cast")
        value = copy.deepcopy(MANIFEST)
        variant = self.variant(value, entry["canonical_key"])
        variant["line_metadata"] = (
            copy.deepcopy(variant
                          ["materialization_cases"][0]["line_metadata"]))
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "lines belong to cases"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        cases = self.variant(value, entry["canonical_key"])[
            "materialization_cases"]
        cases[1]["line_metadata"][0]["sensory"] = "VISUAL"
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "binding-relevant line metadata"):
            self.validate(value)

    def test_plural_arms_token_requires_the_narrow_slot_type(self):
        entry = next(e for e in MANIFEST["entries"]
                     if e["canonical_key"]
                     == "airstrike blizzard demon cast")
        value = copy.deepcopy(MANIFEST)
        arms = self.variant(value, entry["canonical_key"], 2)
        arms["slot_schema"][2]["type"] = "actor_ref"
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "plural arms token/type mismatch"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        plain = self.variant(value, entry["canonical_key"])
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
        self.entry(value, "beam catchall cast")["variants"][0]["binding"][
            "resolves_target"] = False
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "non-target binding declares"):
            self.validate(value)

        untargeted = next(e for e in MANIFEST["entries"]
                          if e["canonical_key"] == "wizard cast")
        value = copy.deepcopy(MANIFEST)
        self.variant(value, untargeted["canonical_key"])[
            "slot_schema"].append(
                { "name": "target", "type": "resolved_target" })
        self.variant(value, untargeted["canonical_key"])[
            "required_arguments"].append("target")
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "non-target binding declares"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        self.variant(value, untargeted["canonical_key"])[
            "line_metadata"][0]["templates"][0]["relation"] = "AT"
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "invalid/duplicate language relation"):
            self.validate(value)

        targeted = next(e for e in MANIFEST["entries"]
                        if e["canonical_key"] == "wizard cast targeted")
        value = copy.deepcopy(MANIFEST)
        self.variant(value, targeted["canonical_key"])[
            "line_metadata"][0]["templates"][0]["relation"] = "NONE"
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "invalid/duplicate language relation"):
            self.validate(value)

    def test_current_slice_rejects_unwired_metadata(self):
        for field in ("requires_named_foe", "requires_god"):
            value = copy.deepcopy(MANIFEST)
            self.entry(value, "beam catchall cast")["variants"][0]["applicability"][
                field] = True
            with self.subTest(field=field):
                with self.assertRaisesRegex(MODULE.ManifestError,
                                            "applicability metadata"):
                    self.validate(value)

        value = copy.deepcopy(MANIFEST)
        self.entry(value, "beam catchall cast")["variants"][0]["line_metadata"][0][
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

    def test_nergalle_recursive_capture_contract_is_exact(self):
        entry = next(e for e in MANIFEST["entries"]
                     if e["canonical_key"]
                     == "vanquished vanguard nergalle cast")
        variant = entry["variants"][0]
        self.assertEqual("CAPTURE_SLOT",
                         variant["materialization_policy"])
        self.assertEqual(
            ["orc_name_1", "orc_name_2", "orc_name_3"],
            [capture["name"] for capture in variant["recursive_captures"]])
        self.assertEqual(
            [0, 1, 2],
            [capture["ordinal"] for capture
             in variant["recursive_captures"]])
        self.assertEqual(
            {"_beogh_name_", "_orcish_name_", "_other_orcish_name_",
             "orc name"},
            set(variant["recursive_dependency_fingerprints"]))

        for mutation, error in (
            (lambda value: self.variant(
                value, "vanquished vanguard nergalle cast")[
                    "recursive_captures"].pop(), "capture count"),
            (lambda value: self.variant(
                value, "vanquished vanguard nergalle cast")[
                    "recursive_captures"][1].update({"ordinal": 0}),
             "capture declaration"),
            (lambda value: self.variant(
                value, "vanquished vanguard nergalle cast")[
                    "recursive_dependency_fingerprints"].pop("_beogh_name_"),
             "capture closure"),
        ):
            value = copy.deepcopy(MANIFEST)
            mutation(value)
            with self.subTest(error=error):
                with self.assertRaisesRegex(MODULE.ManifestError, error):
                    self.validate(value)

    def test_nergalle_capture_parents_are_exact_single_markers(self):
        for replacement in (
            "prefix @_beogh_name_@",
            "@_beogh_name_@@_beogh_name_@",
        ):
            inventory = copy.deepcopy(INVENTORY)
            parent = next(
                entry for entry in inventory["closure"]["additional_nodes"]
                if entry["key"] == "orc name")
            parent["variants"][0]["text"] = replacement
            with self.subTest(replacement=replacement):
                with self.assertRaisesRegex(
                        MODULE.ManifestError,
                        "capture parent must be one exact marker"):
                    self.validate_inventory(inventory)

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
