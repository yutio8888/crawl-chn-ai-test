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

    def suppress_entry(self, key="siren song cast"):
        upstream = MODULE._inventory_nodes(INVENTORY)[key]
        self.assertEqual(1, len(upstream["variants"]))
        actual = upstream["variants"][0]
        return {
            "canonical_key": key,
            "canonical_fingerprint":
                MODULE.runtime_canonical_fingerprint(upstream),
            "selection_graph_fingerprint":
                MODULE.runtime_selection_fingerprint(upstream),
            "mode": "CANDIDATE",
            "variants": [{
                "stable_id": "mon.cast.siren_song.suppress.v1",
                "tombstone": False,
                "variant_ordinal": 0,
                "upstream_weight": actual["weight"],
                "upstream_variant_fingerprint": actual["text_fingerprint"],
                "english_snapshot": actual["text"],
                "frame": "DIRECT_EFFECT",
                "binding": {"resolves_target": False},
                "applicability": {
                    "requires_player": False,
                    "requires_foe": False,
                    "requires_named_foe": False,
                    "requires_god": False,
                    "requires_caster_visible": False,
                },
                "materialization_policy": "NONE",
                "suppresses": True,
                "slot_schema": [],
                "required_arguments": [],
                "recursive_dependency_fingerprints": {},
                "materialization_cases": [],
                "line_metadata": [],
            }],
        }

    def special_slot_entry(self, key, resolves_target=False):
        upstream = MODULE._inventory_nodes(INVENTORY)[key]
        variants = []
        replacements = {
            "@The_monster@": ("actor", "actor_ref"),
            "@The_something@": ("actor", "actor_ref"),
            "@The_monster_possessive@":
                ("actor_possessive", "actor_possessive_name"),
            "@subjective@":
                ("actor_subjective", "actor_subjective_pronoun"),
            "@player_name@": ("player_name", "player_name"),
            "@foe_possessive@":
                ("foe_possessive", "resolved_foe_possessive"),
        }
        for ordinal, actual in enumerate(upstream["variants"]):
            pattern = actual["text"]
            slots = []
            for token, (name, slot_type) in replacements.items():
                if token in pattern:
                    slots.append({"name": name, "type": slot_type})
                    pattern = pattern.replace(token, "${" + name + "}")
            has_player_marker = "@player_only@" in pattern
            pattern = pattern.replace("@player_only@", "").rstrip()
            relations = MODULE.TARGET_RELATIONS if resolves_target else ("NONE",)
            templates = []
            for language in ("en", "zh"):
                templates.extend(
                    {"language": language, "relation": relation,
                     "pattern": pattern}
                    for relation in relations)
            variants.append({
                "stable_id": f"test.{key.replace(' ', '_')}.{ordinal}",
                "tombstone": False,
                "variant_ordinal": ordinal,
                "upstream_weight": actual["weight"],
                "upstream_variant_fingerprint": actual["text_fingerprint"],
                "english_snapshot": actual["text"],
                "frame": "DIRECT_EFFECT",
                "binding": {"resolves_target": resolves_target},
                "applicability": {
                    "requires_player": has_player_marker
                        or "@player_name@" in actual["text"],
                    "requires_foe": "@foe_possessive@" in actual["text"],
                    "requires_named_foe": False,
                    "requires_god": False,
                    "requires_caster_visible": False,
                },
                "materialization_policy": "NONE",
                "slot_schema": slots,
                "required_arguments": [slot["name"] for slot in slots],
                "line_metadata": [{
                    "sensory": "PLAIN", "channel": None,
                    "behavior": {"implies_gesture": False,
                                 "audible": False},
                    "templates": templates,
                }],
                "materialization_cases": [],
                "recursive_dependency_fingerprints": {},
            })
        return {
            "canonical_key": key,
            "canonical_fingerprint":
                MODULE.runtime_canonical_fingerprint(upstream),
            "selection_graph_fingerprint":
                MODULE.runtime_selection_fingerprint(upstream),
            "mode": "CANDIDATE",
            "variants": variants,
        }

    def recursive_roxanne_fixture(self, inventory=None):
        inventory = inventory or INVENTORY
        manifest = copy.deepcopy(MANIFEST)
        nodes = MODULE._inventory_nodes(inventory)
        roxanne = nodes["roxanne cast"]
        sphinx = nodes["sphinx cast"]
        sphinx_record = self.entry(manifest, "sphinx cast")
        sphinx_record["mode"] = "CLOSURE_ONLY"
        sphinx_record["canonical_fingerprint"] = (
            MODULE.runtime_canonical_fingerprint(sphinx))
        sphinx_record["selection_graph_fingerprint"] = (
            MODULE.runtime_selection_fingerprint(sphinx))
        for descriptor, actual in zip(sphinx_record["variants"],
                                      sphinx["variants"]):
            descriptor["upstream_weight"] = actual["weight"]
            descriptor["upstream_variant_fingerprint"] = (
                actual["text_fingerprint"])
            descriptor["english_snapshot"] = actual["text"]

        signatures = [
            MODULE._identity_signature([
                ("roxanne cast", 0, ()),
                ("sphinx cast", ordinal, (0,)),
            ])
            for ordinal in range(len(sphinx["variants"]))
        ]
        lines = [
            ("${actor} mumbles some strange words.",
             "${actor}低声念着奇怪的咒语。"),
            ("${actor} casts a spell.", "${actor}施放了一个法术。"),
        ]
        cases = []
        for ordinal, (signature, patterns) in enumerate(zip(signatures,
                                                             lines)):
            cases.append({
                "case_id": f"test.roxanne.recursive.{ordinal}",
                "signature": signature,
                "line_metadata": [{
                    "sensory": "PLAIN", "channel": None,
                    "behavior": {"implies_gesture": False,
                                 "audible": False},
                    "templates": [
                        {"language": "en", "relation": "NONE",
                         "pattern": patterns[0]},
                        {"language": "zh", "relation": "NONE",
                         "pattern": patterns[1]},
                    ],
                }],
            })
        actual = roxanne["variants"][0]
        manifest["entries"].append({
            "canonical_key": "roxanne cast",
            "canonical_fingerprint":
                MODULE.runtime_canonical_fingerprint(roxanne),
            "selection_graph_fingerprint":
                MODULE.runtime_selection_fingerprint(roxanne),
            "mode": "CANDIDATE",
            "variants": [{
                "stable_id": "test.roxanne.recursive.root",
                "tombstone": False,
                "variant_ordinal": 0,
                "upstream_weight": actual["weight"],
                "upstream_variant_fingerprint": actual["text_fingerprint"],
                "english_snapshot": actual["text"],
                "frame": "VOCAL",
                "binding": {"resolves_target": False},
                "applicability": {
                    "requires_player": False,
                    "requires_foe": False,
                    "requires_named_foe": False,
                    "requires_god": False,
                    "requires_caster_visible": False,
                },
                "materialization_policy": "RECURSIVE_CASE_MAP",
                "slot_schema": [{"name": "actor", "type": "actor_ref"}],
                "required_arguments": ["actor"],
                "line_metadata": [],
                "materialization_cases": cases,
                "recursive_dependency_fingerprints": {
                    "sphinx cast":
                        MODULE.runtime_canonical_fingerprint(sphinx),
                },
                "recursive_captures": [],
            }],
        })
        return manifest

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
                          "airstrike cast",
                          "airstrike wind drake cast",
                          "battlecry cast",
                          "battlecry cherub cast",
                          "battlecry satyr cast",
                          "beckoning gale chonchon cast",
                          "beckoning gale hippogriff cast",
                          "berserker rage rupert cast",
                          "bes kemwar cast",
                          "blinkbolt cast",
                          "blizzard demon cast",
                          "bolt of draining natural cast",
                          "bolt of fire ophan cast",
                          "bolt of flesh kobold fleshcrafter cast",
                          "bolt of flesh zykzyl cast",
                          "bolt of magma molten gargoyle cast",
                          "bombardier beetle cast",
                          "call lost souls cast",
                          "call of chaos cast",
                          "cantrip cast",
                          "cause fear satyr cast",
                          "clockroach cast",
                          "cognitogaunt cast",
                          "cold breath cast",
                          "conjure living spells cast",
                          "corrupting pulse wretched star cast",
                          "crab cast targeted",
                          "creeping frost cast",
                          "crystal echidna cast targeted",
                          "crystallising shot crystal guardian cast",
                          "culicivora cast targeted",
                          "curse skull cast",
                          "death rattle ushabti cast",
                          "dissolution cast",
                          "dominate undead vampire bloodprince cast",
                          "dragon cast",
                          "dragon cast targeted",
                          "druid's call cast",
                          "dryad cast",
                          "eidolon cast targeted",
                          "electrical bolt cast",
                          "electrical bolt shock serpent cast",
                          "enfeeble zykzyl cast",
                          "ensnare natural cast",
                          "eruption cast",
                          "eye of draining cast",
                          "fire breath cast",
                          "fireball hell hog cast",
                          "flayed ghost cast",
                          "floating eye cast",
                          "floating eye cast targeted",
                          "force lance polterguardian cast",
                          "formless jellyfish cast",
                          "frances cast",
                          "freeze cast",
                          "gastronok cast targeted",
                          "geryon cast",
                          "ghost moth cast",
                          "ghost moth cast targeted",
                          "ghostly fireball revenant cast",
                          "glowing orange brain cast",
                          "golden eye cast targeted",
                          "grasping roots cast",
                          "grasping roots natural cast",
                          "grave claw vampire bloodprince cast",
                          "guardian serpent cast",
                          "harpoon shot cast",
                          "hellfire court cast",
                          "hellfire mortar cast",
                          "hoarfrost bullet cast",
                          "hoarfrost bullet cast finale",
                          "holy flames cast",
                          "hurl torchlight cast",
                          "injury mirror screaming refraction cast",
                          "invisibility shadowghast cast",
                          "kobold blastminer cast targeted",
                          "landbreaker natural cast",
                          "laughing skull cast",
                          "launch bomblet cast",
                          "lightning bolt electric golem cast",
                          "lightning bolt natural cast",
                          "living spell cast",
                          "manifold assault natural cast",
                          "manticore cast",
                          "mara summon cast",
                          "metal splinters war gargoyle cast",
                          "minor healing dryad cast",
                          "non-humanoid wizard cast",
                          "non-humanoid wizard cast targeted",
                          "orange crystal statue cast",
                          "orange crystal statue cast targeted",
                          "orb of destruction cast",
                          "orb of destruction orb spider cast",
                          "orb of fire cast",
                          "ostracise cast",
                          "paralyse xtahua cast",
                          "paralysis gaze cast",
                          "petrifying cloud cast",
                          "phantom blitz cast",
                          "phantom mirror cast",
                          "poisonous cloud natural cast",
                          "primal wave norris cast",
                          "pyroclastic surge cast",
                          "quicksilver bolt natural cast",
                          "ravenous swarm vampire bloodprince cast",
                          "rupert cast targeted",
                          "scrub nettle cast targeted",
                          "seismic stomp cast",
                          "shadow shot cast",
                          "silent berserker rage rupert cast",
                          "silent curse skull cast",
                          "silent flayed ghost cast",
                          "silent laughing skull cast",
                          "sleep satyr cast",
                          "slug dart cast",
                          "smiting guardian sphinx cast",
                          "sojourning bolt cast",
                          "spectral cloud revenant cast",
                          "sphinx cast",
                          "spit acid cast",
                          "spit lava cast",
                          "spit poison cast",
                          "splinterspray cast",
                          "steam ball natural cast",
                          "sticks to snakes cast",
                          "sticky flame cast",
                          "stone arrow gargoyle cast",
                          "stunning burst cast",
                          "summon mortal champion fravashi cast",
                          "symbol of torment cast",
                          "thrashing horror cast",
                          "throw bolas cast",
                          "throw icicle shard shrike cast",
                          "throw klown pie cast",
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
                          "volley of thorns cast",
                          "warning cry cast",
                          "warning cry hippogriff cast",
                          "warning cry howler monkey cast",
                          "warning cry seraph cast",
                          "warning cry ushabti cast",
                          "warning cry vault sentinel cast",
                          "weakening gaze cast",
                          "wind blast cast",
                          "wind blast wind drake cast",
                          "woodweal cast",
                          "word of recall cast",
                          "wretched star cast"], candidates)
        self.assertEqual(
            ["acid splash cast", "branch summon cast prefix",
             "chilling breath cast", "flashing balestra undying armoury cast",
             "lee's rapid deconstruction screaming refraction cast",
             "polymorphed wizard cast",
             "polymorphed wizard cast targeted",
             "rebounding chill thermic dynamo cast",
             "summon water elementals elemental wellspring cast"],
            [entry["canonical_key"] for entry in validated["entries"]
             if entry["mode"] == "LEGACY_ONLY"])
        nergalle = next(entry for entry in validated["entries"]
                        if "nergalle" in entry["canonical_key"])
        self.assertEqual(
            ["CAPTURE_SLOT", "NONE"],
            [variant["materialization_policy"]
             for variant in nergalle["variants"]])

    def test_explicit_suppress_descriptor_is_template_free(self):
        value = copy.deepcopy(MANIFEST)
        value["entries"].append(self.suppress_entry())
        generated = MODULE.render_sidecar(self.validate(value))
        self.assertIn('"siren song cast"', generated)
        self.assertIn("                        true,", generated)

    def test_suppress_descriptor_rejects_protocol_misuse(self):
        valid = copy.deepcopy(MANIFEST)
        valid["entries"].append(self.suppress_entry())

        missing_marker = copy.deepcopy(valid)
        missing_marker["entries"][-1]["variants"][0].pop("suppresses")
        with self.assertRaisesRegex(
                MODULE.ManifestError,
                "candidate __NONE requires suppress descriptor"):
            self.validate(missing_marker)

        legacy = copy.deepcopy(valid)
        legacy["entries"][-1]["mode"] = "LEGACY_ONLY"
        legacy["entries"][-1]["variants"][0][
            "materialization_policy"] = "LEGACY_ONLY"
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "suppress descriptor must be CANDIDATE"):
            self.validate(legacy)

        ordinary = copy.deepcopy(MANIFEST)
        entry = self.entry(
            ordinary, "summon water elementals elemental wellspring cast")
        entry["mode"] = "CANDIDATE"
        variant = entry["variants"][0]
        variant["materialization_policy"] = "NONE"
        variant["suppresses"] = True
        variant["slot_schema"] = []
        variant["required_arguments"] = []
        with self.assertRaisesRegex(
                MODULE.ManifestError,
                "suppress descriptor must select exact __NONE"):
            self.validate(ordinary)

        for field in ("slots", "lines"):
            with self.subTest(field=field):
                renderable = copy.deepcopy(valid)
                variant = renderable["entries"][-1]["variants"][0]
                if field == "slots":
                    variant["slot_schema"] = [
                        {"name": "actor", "type": "actor_ref"},
                    ]
                    variant["required_arguments"] = ["actor"]
                else:
                    variant["line_metadata"] = [{
                        "sensory": "PLAIN",
                        "channel": None,
                        "behavior": {
                            "implies_gesture": False,
                            "audible": False,
                        },
                        "templates": [{
                            "language": "en", "relation": "NONE",
                            "pattern": "not silent",
                        }],
                    }]
                with self.assertRaisesRegex(
                        MODULE.ManifestError,
                        "suppress descriptor contains renderable data"):
                    self.validate(renderable)

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

    def test_recursive_case_map_accepts_roxanne_two_leaf_identity_set(self):
        value = self.recursive_roxanne_fixture()
        validated = self.validate(value)
        variant = self.variant(validated, "roxanne cast")
        self.assertEqual("RECURSIVE_CASE_MAP",
                         variant["materialization_policy"])
        self.assertEqual(2, len(variant["materialization_cases"]))
        expected = MODULE._recursive_identity_signatures(
            MODULE._inventory_nodes(INVENTORY), "roxanne cast", 0)
        self.assertEqual(expected,
                         {case["signature"] for case
                          in variant["materialization_cases"]})
        self.assertEqual("CLOSURE_ONLY",
                         self.entry(validated, "sphinx cast")["mode"])

    def test_recursive_case_map_requires_exact_unique_case_set(self):
        value = self.recursive_roxanne_fixture()
        self.variant(value, "roxanne cast")["materialization_cases"].pop()
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "cases are incomplete"):
            self.validate(value)

        value = self.recursive_roxanne_fixture()
        cases = self.variant(value, "roxanne cast")["materialization_cases"]
        duplicate = copy.deepcopy(cases[0])
        duplicate["case_id"] = "test.roxanne.recursive.duplicate"
        cases.append(duplicate)
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "unknown/duplicate signature"):
            self.validate(value)

        value = self.recursive_roxanne_fixture()
        cases = self.variant(value, "roxanne cast")["materialization_cases"]
        extra = copy.deepcopy(cases[0])
        extra["case_id"] = "test.roxanne.recursive.extra"
        extra["signature"] += "|extra"
        cases.append(extra)
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "unknown/duplicate signature"):
            self.validate(value)

    def test_recursive_case_map_rejects_dependency_drift_and_dynamics(self):
        value = self.recursive_roxanne_fixture()
        self.variant(value, "roxanne cast")[
            "recursive_dependency_fingerprints"]["sphinx cast"] = "stale"
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "dependency fingerprint mismatch"):
            self.validate(value)

        inventory = copy.deepcopy(INVENTORY)
        sphinx = MODULE._inventory_nodes(inventory)["sphinx cast"]
        sphinx["variants"][0]["lua_sites"] = [{"source": "return 'x'"}]
        value = self.recursive_roxanne_fixture(inventory)
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "dynamic materialization|Lua or bracket"):
            MODULE.validate_manifest(value, inventory)

        inventory = copy.deepcopy(INVENTORY)
        sphinx = MODULE._inventory_nodes(inventory)["sphinx cast"]
        sphinx["variants"][0]["random_substring_sites"] = [{
            "options": ["mumbles", "chants"],
        }]
        value = self.recursive_roxanne_fixture(inventory)
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "dynamic materialization|Lua or bracket"):
            MODULE.validate_manifest(value, inventory)

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

    def test_player_name_and_subjective_slots_are_narrow_and_applicable(self):
        value = copy.deepcopy(MANIFEST)
        value["entries"].append(
            self.special_slot_entry("doomsaying cassandra cast"))
        validated = self.validate(value)
        variant = self.variant(validated, "doomsaying cassandra cast")
        self.assertTrue(variant["applicability"]["requires_player"])
        self.assertIn({"name": "player_name", "type": "player_name"},
                      variant["slot_schema"])

        bad = copy.deepcopy(value)
        self.variant(bad, "doomsaying cassandra cast")["applicability"][
            "requires_player"] = False
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "requires player applicability"):
            self.validate(bad)

        value = copy.deepcopy(MANIFEST)
        value["entries"].append(self.special_slot_entry("gastronok cast"))
        self.validate(value)
        bad = copy.deepcopy(value)
        self.variant(bad, "gastronok cast")["slot_schema"][1]["type"] = (
            "actor_possessive_pronoun")
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "subjective actor token/type mismatch"):
            self.validate(bad)

    def test_the_something_alias_and_possessive_foe_are_exact(self):
        value = copy.deepcopy(MANIFEST)
        value["entries"].append(
            self.special_slot_entry("unseen call of chaos cast"))
        variant = self.variant(self.validate(value),
                               "unseen call of chaos cast")
        self.assertEqual([{"name": "actor", "type": "actor_ref"}],
                         variant["slot_schema"])

        value = copy.deepcopy(MANIFEST)
        value["entries"].append(
            self.special_slot_entry("raven cast"))
        variant = self.variant(self.validate(value), "raven cast")
        self.assertTrue(variant["applicability"]["requires_foe"])
        self.assertIn("resolved_foe_possessive",
                      {slot["type"] for slot in variant["slot_schema"]})
        variant["applicability"]["requires_foe"] = False
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "foe applicability/slot mismatch"):
            self.validate(value)

    def test_player_only_is_zero_width_and_keeps_target_resolution(self):
        value = copy.deepcopy(MANIFEST)
        value["entries"].append(self.special_slot_entry(
            "unseen ghost moth cast targeted", resolves_target=True))
        variant = self.variant(self.validate(value),
                               "unseen ghost moth cast targeted")
        self.assertTrue(variant["binding"]["resolves_target"])
        self.assertTrue(variant["applicability"]["requires_player"])
        self.assertEqual([], variant["slot_schema"])
        self.assertEqual(
            set(MODULE.TARGET_RELATIONS),
            {template["relation"]
             for template in variant["line_metadata"][0]["templates"]})
        variant["applicability"]["requires_player"] = False
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "requires player applicability"):
            self.validate(value)

    def test_lower_actor_token_requires_the_narrow_slot_type(self):
        key = "summon water elementals elemental wellspring cast"
        value = copy.deepcopy(MANIFEST)
        entry = self.entry(value, key)
        variant = self.variant(value, key)
        entry["mode"] = "CANDIDATE"
        variant["materialization_policy"] = "NONE"
        variant["slot_schema"] = [
            {"name": "actor_lower", "type": "actor_ref_lower"},
        ]
        variant["required_arguments"] = ["actor_lower"]
        variant["line_metadata"] = [{
            "sensory": "PLAIN", "channel": None,
            "behavior": {"implies_gesture": False, "audible": False},
            "templates": [
                {"language": "en", "relation": "NONE",
                 "pattern": "Water spirits pour forth from ${actor_lower}!"},
                {"language": "zh", "relation": "NONE",
                 "pattern": "水之灵从${actor_lower}身上涌出！"},
            ],
        }]
        self.validate(value)

        variant["slot_schema"][0]["type"] = "resolved_beam"
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "lower actor token/type mismatch"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        upper = self.variant(value, "beam catchall cast")
        upper["slot_schema"][0]["type"] = "actor_ref_lower"
        with self.assertRaisesRegex(MODULE.ManifestError,
                                    "sentence actor token/type mismatch"):
            self.validate(value)

    def test_lower_possessive_actor_token_requires_the_narrow_slot_type(self):
        key = "call down lightning cast"
        value = copy.deepcopy(MANIFEST)
        entry = self.entry(value, key)
        variant = self.variant(value, key)
        entry["mode"] = "CANDIDATE"
        variant["materialization_policy"] = "NONE"
        variant["slot_schema"] = [{
            "name": "actor_possessive_lower",
            "type": "actor_possessive_name_lower",
        }]
        variant["required_arguments"] = ["actor_possessive_lower"]
        variant["line_metadata"] = [{
            "sensory": "PLAIN", "channel": None,
            "behavior": {"implies_gesture": False, "audible": False},
            "templates": [
                {"language": "en", "relation": "NONE",
                 "pattern": "Electricity crackles from "
                            "${actor_possessive_lower} apparatus."},
                {"language": "zh", "relation": "NONE",
                 "pattern": "电流在${actor_possessive_lower}装置上噼啪作响。"},
            ],
        }]
        self.validate(value)

        variant["slot_schema"][0]["type"] = "actor_possessive_name"
        with self.assertRaisesRegex(
                MODULE.ManifestError,
                "possessive actor token/type mismatch"):
            self.validate(value)

        value = copy.deepcopy(MANIFEST)
        upper = self.variant(value, "brain worm cast")
        upper["slot_schema"][0]["type"] = "actor_possessive_name_lower"
        with self.assertRaisesRegex(
                MODULE.ManifestError,
                "sentence possessive actor token/type mismatch"):
            self.validate(value)
    def test_actor_god_tokens_require_distinct_case_sensitive_slot_types(self):
        fixtures = [
            ("divine armament cast", "@My_God@", "actor_god_my",
             "${actor} beseeches ${god} to grant them a weapon."),
            ("major destruction cast", "@possessive_God@",
             "actor_god_possessive",
             "${actor} conjures force in the name of ${god}!"),
            ("unseen priest cast", "@a_God@", "actor_god_indefinite",
             "You hear prayers to ${god}."),
        ]
        for key, token, slot_type, pattern in fixtures:
            with self.subTest(token=token):
                upstream = MODULE._inventory_nodes(INVENTORY)[key]
                self.assertEqual(1, len(upstream["variants"]))
                actual = upstream["variants"][0]
                slots = []
                required = []
                if "@The_monster@" in actual["text"]:
                    slots.append({"name": "actor", "type": "actor_ref"})
                    required.append("actor")
                slots.append({"name": "god", "type": slot_type})
                required.append("god")
                record = {
                    "canonical_key": key,
                    "canonical_fingerprint":
                        MODULE.runtime_canonical_fingerprint(upstream),
                    "selection_graph_fingerprint":
                        MODULE.runtime_selection_fingerprint(upstream),
                    "mode": "CANDIDATE",
                    "variants": [{
                        "stable_id": "test." + key.replace(" ", "_"),
                        "tombstone": False,
                        "variant_ordinal": 0,
                        "upstream_weight": actual["weight"],
                        "upstream_variant_fingerprint":
                            actual["text_fingerprint"],
                        "english_snapshot": actual["text"],
                        "frame": "INVOCATION",
                        "binding": {"resolves_target": False},
                        "applicability": {
                            "requires_player": False,
                            "requires_foe": False,
                            "requires_named_foe": False,
                            "requires_god": False,
                            "requires_caster_visible": False,
                        },
                        "materialization_policy": "NONE",
                        "slot_schema": slots,
                        "required_arguments": required,
                        "line_metadata": [{
                            "sensory": "PLAIN", "channel": None,
                            "behavior": {
                                "implies_gesture": False, "audible": False,
                            },
                            "templates": [
                                {"language": "en", "relation": "NONE",
                                 "pattern": pattern},
                                {"language": "zh", "relation": "NONE",
                                 "pattern": pattern},
                            ],
                        }],
                        "materialization_cases": [],
                        "recursive_dependency_fingerprints": {},
                    }],
                }
                value = copy.deepcopy(MANIFEST)
                value["entries"].append(record)
                self.validate(value)

                record["variants"][0]["slot_schema"][-1]["type"] = (
                    "actor_god_indefinite"
                    if slot_type != "actor_god_indefinite"
                    else "actor_god_my")
                value = copy.deepcopy(MANIFEST)
                value["entries"].append(record)
                with self.assertRaisesRegex(
                        MODULE.ManifestError,
                        "token/type mismatch"):
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
