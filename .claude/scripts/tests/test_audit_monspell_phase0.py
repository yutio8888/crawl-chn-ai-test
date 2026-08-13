#!/usr/bin/env python3

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / ".claude/scripts/audit_monspell_phase0.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures/monspell-phase0-artifact.json"

SPEC = importlib.util.spec_from_file_location("audit_monspell_phase0", AUDIT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class ArtifactInventoryTest(unittest.TestCase):
    def load_value(self, value):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            return MODULE.load_artifact(path)

    def build(self):
        return MODULE.build_inventory(MODULE.load_artifact(FIXTURE))

    def materialization_policy(self, inventory=None):
        inventory = inventory or self.build()
        return {
            "schema_version": 1,
            "inventory_semantic_fingerprint": inventory["semantic_fingerprint"],
            "variants": [{
                "key": "mixed key",
                "variant_ordinal": 0,
                "random_site_option_counts": [2, 3],
                "recursive_dynamic_targets": [],
                "lua_site_count": 1,
                "policy": "LEGACY_ONLY",
                "evidence": "fixture policy",
            }],
        }

    def assert_protocol_error(self, mutate):
        value = fixture()
        mutate(value)
        with self.assertRaises(MODULE.ArtifactError):
            self.load_value(value)

    def test_maps_production_provenance_and_variants(self):
        inventory = self.build()
        self.assertEqual(
            inventory["speakdb_files"],
            ["monspeak.txt", "monspell.txt", "monflee.txt"],
        )
        entries = {entry["key"]: entry for entry in inventory["entries"]}
        self.assertEqual(set(entries), {"mixed key", "overridden key"})
        overridden = entries["overridden key"]
        self.assertTrue(overridden["overridden"])
        self.assertEqual("monflee.txt", overridden["effective_source"])
        self.assertEqual(
            overridden["source_history"],
            [{"file": "monspell.txt", "ordinal": 1},
             {"file": "monflee.txt", "ordinal": 0}],
        )
        self.assertEqual("from later file", overridden["variants"][0]["text"])

    def test_classifies_tokens_and_static_sites_from_raw_pattern(self):
        inventory = self.build()
        entry = next(e for e in inventory["entries"] if e["key"] == "mixed key")
        first = entry["variants"][0]
        self.assertEqual(3, first["weight"])
        self.assertEqual(10, entry["variants"][1]["weight"])
        self.assertEqual(
            [(t["token"], t["classification"]) for t in first["tokens"]],
            [("Flavor", "recursive"), ("Target", "runtime")],
        )
        self.assertEqual("VISUAL", first["control_prefixes"][0]["prefix"])
        self.assertEqual(1, len(first["lua_sites"]))
        self.assertEqual(["casts", "pitches"],
                         first["random_substring_sites"][0]["options"])
        self.assertEqual(["left", "", "right"],
                         first["random_substring_sites"][1]["options"])
        self.assertEqual(
            {"canonical_key": "mixed key", "variant_ordinal": 0},
            first["snapshot_locator"],
        )

    def test_recursive_closure_without_cycle(self):
        closure = self.build()["closure"]
        self.assertEqual(
            ["cycle a", "cycle b", "flavor", "mixed key", "overridden key"],
            closure["keys"],
        )
        self.assertEqual(["cycle a", "cycle b", "flavor"],
                         [node["key"] for node in closure["additional_nodes"]])
        self.assertEqual(3, len(closure["edges"]))
        self.assertEqual([], closure["cycles"])

    def test_runtime_marker_scanner_drives_inventory_and_edges(self):
        value = fixture()
        entry = next(item for item in value["entries"]
                     if item["canonical_key"] == "mixed key")
        pattern = "@Flavor@@@@cross\nline@"
        entry["variants"][0]["raw_pattern"] = pattern
        inventory = MODULE.build_inventory(value)
        mixed = next(item for item in inventory["entries"]
                     if item["key"] == "mixed key")
        tokens = mixed["variants"][0]["tokens"]
        self.assertEqual(
            [(item["token"], item["classification"],
              item["start"], item["end"]) for item in tokens],
            [("Flavor", "recursive", 0, 8),
             ("", "runtime", 8, 10),
             ("cross\nline", "runtime", 10, 22)],
        )
        edges = [edge for edge in inventory["closure"]["edges"]
                 if edge["from_key"] == "mixed key"]
        self.assertEqual(1, len(edges))
        self.assertEqual((0, 8, "Flavor", "flavor"),
                         (edges[0]["start"], edges[0]["end"],
                          edges[0]["token"], edges[0]["to_key"]))

    def test_negative_weight_reachability_matches_first_cumulative_hit(self):
        def weighted_fixture(weights, patterns):
            value = fixture()
            entry = next(item for item in value["entries"]
                         if item["canonical_key"] == "mixed key")
            provenance = entry["effective_provenance"]
            entry["variants"] = [{
                "locator": {
                    "canonical_key": "mixed key",
                    "variant_ordinal": ordinal,
                },
                "provenance": provenance,
                "weight": weight,
                "raw_pattern": pattern,
            } for ordinal, (weight, pattern)
              in enumerate(zip(weights, patterns))]
            return value

        unreachable_danger = weighted_fixture(
            [10, -5, 3], ["safe first", "safe second", "before @broken"])
        reachable = MODULE._reachable_variants(
            next(item for item in unreachable_danger["entries"]
                 if item["canonical_key"] == "mixed key"))
        self.assertEqual(["safe first"],
                         [item["raw_pattern"] for item in reachable])
        MODULE.build_inventory(unreachable_danger)

        reachable_danger = weighted_fixture(
            [10, -5, 10], ["safe first", "safe second", "before @broken"])
        reachable = MODULE._reachable_variants(
            next(item for item in reachable_danger["entries"]
                 if item["canonical_key"] == "mixed key"))
        self.assertEqual(["safe first", "before @broken"],
                         [item["raw_pattern"] for item in reachable])
        with self.assertRaisesRegex(MODULE.ArtifactError,
                                    "unbalanced @ marker"):
            MODULE.build_inventory(reachable_danger)

    def test_static_closure_rejects_unbalanced_markers_and_limits(self):
        def set_first_pattern(value, key, pattern):
            entry = next(item for item in value["entries"]
                         if item["canonical_key"] == key)
            entry["raw_body"] = pattern + "\n"
            entry["variants"][0]["raw_pattern"] = pattern

        cases = [
            ("unbalanced @", "before @broken", "unbalanced @ marker"),
            ("unbalanced Lua", "before {{return 'broken'", "unbalanced Lua site"),
            ("replacement limit", "@target@" * 101, "replacement limit 100"),
        ]
        for label, pattern, error in cases:
            with self.subTest(case=label):
                value = fixture()
                set_first_pattern(value, "mixed key", pattern)
                with self.assertRaisesRegex(MODULE.ArtifactError, error):
                    MODULE.build_inventory(value)

        cycle = fixture()
        set_first_pattern(cycle, "cycle b", "@cycle a@")
        with self.assertRaisesRegex(MODULE.ArtifactError,
                                    "recursive closure cycle"):
            MODULE.build_inventory(cycle)

        depth = fixture()
        for index in range(11):
            key = f"zz depth {index:02d}"
            target = (f"@zz depth {index + 1:02d}@"
                      if index < 10 else "depth leaf")
            provenance = {
                "source_name": "database/monspell.txt",
                "load_index": 1,
                "definition_ordinal": 100 + index,
            }
            depth["entries"].append({
                "canonical_key": key,
                "effective_provenance": provenance,
                "raw_body": target + "\n",
                "source_history": [provenance],
                "variants": [{
                    "locator": {"canonical_key": key, "variant_ordinal": 0},
                    "provenance": provenance,
                    "weight": 10,
                    "raw_pattern": target,
                }],
                "parse_error": None,
                "body_empty": False,
            })
        with self.assertRaisesRegex(MODULE.ArtifactError,
                                    "recursion depth 10"):
            MODULE.build_inventory(depth)

    def test_determinism_and_source_fingerprint_uses_artifact_sources(self):
        loaded = MODULE.load_artifact(FIXTURE)
        first = MODULE.build_inventory(loaded)
        second = MODULE.build_inventory(copy.deepcopy(loaded))
        self.assertEqual(first, second)
        changed = copy.deepcopy(loaded)
        changed["sources"][0]["normalized_utf8"] += "changed\n"
        changed_inventory = MODULE.build_inventory(changed)
        self.assertNotEqual(first["source_fingerprint"],
                            changed_inventory["source_fingerprint"])
        self.assertEqual(first["semantic_fingerprint"],
                         changed_inventory["semantic_fingerprint"])
        self.assertEqual(MODULE._render(first), MODULE._render(second))

    def test_materialization_policy_exactly_covers_dynamic_variants(self):
        inventory = self.build()
        policy = self.materialization_policy(inventory)
        MODULE.validate_materialization_policy(inventory, policy)

        mutations = [
            lambda value: value.update(schema_version=2),
            lambda value: value.update(inventory_semantic_fingerprint="stale"),
            lambda value: value["variants"].clear(),
            lambda value: value["variants"][0].update(
                random_site_option_counts=[2]
            ),
            lambda value: value["variants"][0].update(
                policy="CASE_MAP_PROTOTYPE"
            ),
            lambda value: value["variants"][0].update(evidence=""),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(policy)
                mutation(changed)
                with self.assertRaises(MODULE.ArtifactError):
                    MODULE.validate_materialization_policy(inventory, changed)

    def test_materialization_policy_detects_new_recursive_dynamic_output(self):
        value = fixture()
        flavor = next(item for item in value["entries"]
                      if item["canonical_key"] == "flavor")
        second = copy.deepcopy(flavor["variants"][0])
        second["locator"]["variant_ordinal"] = 1
        second["raw_pattern"] = "another flavor"
        flavor["variants"].append(second)
        flavor["raw_body"] = "@cycle a@\n\nanother flavor\n"
        inventory = MODULE.build_inventory(value)
        policy = self.materialization_policy(inventory)
        with self.assertRaisesRegex(MODULE.ArtifactError,
                                    "does not exactly cover"):
            MODULE.validate_materialization_policy(inventory, policy)

    def test_rejects_schema_database_source_and_entry_order_errors(self):
        mutations = [
            lambda d: d.update(schema_version=2),
            lambda d: d.update(database_name="other"),
            lambda d: d["sources"][1].update(load_index=4),
            lambda d: d["sources"][1].update(source_name=d["sources"][0]["source_name"]),
            lambda d: d["entries"].reverse(),
            lambda d: d["entries"].insert(1, copy.deepcopy(d["entries"][0])),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assert_protocol_error(mutation)

    def test_artifact_schema_is_exact_and_boolean_safe(self):
        unknown_mutations = (
            lambda d: d.update(unknown=None),
            lambda d: d["sources"][0].update(unknown=None),
            lambda d: d["entries"][0].update(unknown=None),
            lambda d: d["entries"][0]["effective_provenance"].update(
                unknown=None
            ),
            lambda d: d["entries"][0]["variants"][0].update(unknown=None),
            lambda d: d["entries"][0]["variants"][0]["locator"].update(
                unknown=None
            ),
        )
        for mutation in unknown_mutations:
            with self.subTest(kind="unknown", mutation=mutation), \
                    self.assertRaisesRegex(MODULE.ArtifactError,
                                           "unknown.*unknown"):
                value = fixture()
                mutation(value)
                self.load_value(value)

        integer_mutations = (
            lambda d: d.update(schema_version=True),
            lambda d: d["sources"][0].update(load_index=False),
            lambda d: d["entries"][0]["effective_provenance"].update(
                load_index=False
            ),
            lambda d: d["entries"][0]["effective_provenance"].update(
                definition_ordinal=False
            ),
            lambda d: d["entries"][0]["variants"][0].update(weight=True),
            lambda d: d["entries"][0]["variants"][0]["locator"].update(
                variant_ordinal=False
            ),
        )
        for mutation in integer_mutations:
            with self.subTest(kind="boolean-integer", mutation=mutation), \
                    self.assertRaisesRegex(MODULE.ArtifactError,
                                           "must be an integer"):
                value = fixture()
                mutation(value)
                self.load_value(value)

    def test_rejects_provenance_history_and_variant_protocol_errors(self):
        mutations = [
            lambda d: d["entries"][0]["effective_provenance"].update(definition_ordinal=9),
            lambda d: d["entries"][-1]["source_history"].reverse(),
            lambda d: d["entries"][0]["variants"][0]["locator"].update(variant_ordinal=1),
            lambda d: d["entries"][0]["variants"][0]["locator"].update(canonical_key="wrong"),
            lambda d: d["entries"][0]["variants"][0]["provenance"].update(definition_ordinal=9),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assert_protocol_error(mutation)

    def test_optional_expected_database_family_is_enforced(self):
        value = fixture()
        MODULE.validate_artifact(value, "fixture", expected_database="speak")
        with self.assertRaisesRegex(MODULE.ArtifactError,
                                    "database_name must be 'misc'"):
            MODULE.validate_artifact(value, "fixture", expected_database="misc")
        misc = copy.deepcopy(value)
        misc["database_name"] = "misc"
        MODULE.validate_artifact(misc, "fixture", expected_database="misc")
        with self.assertRaisesRegex(MODULE.ArtifactError,
                                    "database_name must be 'speak'"):
            MODULE.validate_artifact(misc, "fixture", expected_database="speak")

    def test_default_expected_database_is_speak(self):
        # The default family contract is 'speak': speak-family callers that
        # omit expected_database (load_artifact, build_inventory, the real
        # monspell CLI) must fail closed on a misc dump instead of accepting
        # any family.
        misc = copy.deepcopy(fixture())
        misc["database_name"] = "misc"
        with self.assertRaisesRegex(MODULE.ArtifactError,
                                    "database_name must be 'speak'"):
            MODULE.validate_artifact(misc, "fixture")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "misc.json"
            path.write_text(json.dumps(misc), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ArtifactError,
                                        "database_name must be 'speak'"):
                MODULE.load_artifact(path)
            result = subprocess.run(
                [sys.executable, str(AUDIT), "--dump", str(path)],
                text=True, capture_output=True, check=False,
            )
        self.assertEqual(2, result.returncode)
        self.assertIn("database_name must be 'speak'", result.stderr)

    def test_validates_raw_body_body_empty_and_parse_error(self):
        self.assert_protocol_error(
            lambda d: d["entries"][0].update(raw_body=7)
        )
        self.assert_protocol_error(
            lambda d: d["entries"][0].update(body_empty=True)
        )
        self.assert_protocol_error(
            lambda d: d["entries"][0].update(parse_error={"bad": True})
        )
        empty = fixture()
        provenance = {"source_name": "database/monspell.txt", "load_index": 1,
                      "definition_ordinal": 2}
        empty["entries"].append({
            "canonical_key": "zz empty", "effective_provenance": provenance,
            "raw_body": "", "source_history": [provenance], "variants": [],
            "parse_error": None, "body_empty": True,
        })
        loaded = self.load_value(empty)
        inventory = MODULE.build_inventory(loaded)
        node = next(e for e in inventory["entries"] if e["key"] == "zz empty")
        self.assertEqual([], node["variants"])

    def test_corrupt_effective_entry_is_valid_artifact_but_blocks_inventory(self):
        value = fixture()
        provenance = {"source_name": "database/monflee.txt", "load_index": 2,
                      "definition_ordinal": 7}
        value["entries"].append({
            "canonical_key": "zz corrupt", "effective_provenance": provenance,
            "raw_body": "w:not-a-number\n", "source_history": [provenance],
            "variants": [], "parse_error": "invalid weight", "body_empty": False,
        })
        loaded = self.load_value(value)
        key_sets = MODULE.validate_artifact(loaded)
        self.assertIn("zz corrupt", key_sets.reserved)
        self.assertIn("zz corrupt", key_sets.corrupt)
        self.assertNotIn("zz corrupt", key_sets.selectable)
        with self.assertRaisesRegex(MODULE.ArtifactError, "corrupt effective"):
            MODULE.build_inventory(loaded)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corrupt.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(AUDIT), "--dump", str(path)],
                text=True, capture_output=True, check=False,
            )
        self.assertEqual(2, result.returncode)
        self.assertIn("zz corrupt", result.stderr)

    def test_cli_requires_dump_and_supports_output_check_drift(self):
        missing = subprocess.run([sys.executable, str(AUDIT)], text=True,
                                 capture_output=True, check=False)
        self.assertEqual(2, missing.returncode)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "inventory.json"
            create = subprocess.run(
                [sys.executable, str(AUDIT), "--dump", str(FIXTURE),
                 "--output", str(output)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, create.returncode, create.stderr)
            self.assertEqual(2, json.loads(output.read_text())["summary"]["monspell_keys"])
            policy = Path(directory) / "policy.json"
            policy.write_text(
                json.dumps(self.materialization_policy()), encoding="utf-8"
            )
            check = subprocess.run(
                [sys.executable, str(AUDIT), "--dump", str(FIXTURE),
                 "--check", str(output),
                 "--materialization-policy", str(policy)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, check.returncode, check.stderr)
            policy.write_text("{", encoding="utf-8")
            malformed_policy = subprocess.run(
                [sys.executable, str(AUDIT), "--dump", str(FIXTURE),
                 "--check", str(output),
                 "--materialization-policy", str(policy)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(2, malformed_policy.returncode)
            self.assertIn("audit_monspell_phase0.py", malformed_policy.stderr)
            self.assertNotIn("Traceback", malformed_policy.stderr)
            output.write_text("{}\n", encoding="utf-8")
            drift = subprocess.run(
                [sys.executable, str(AUDIT), "--dump", str(FIXTURE),
                 "--check", str(output)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(1, drift.returncode)
            self.assertIn("inventory drift", drift.stderr)


if __name__ == "__main__":
    unittest.main()
