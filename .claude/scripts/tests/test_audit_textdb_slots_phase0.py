#!/usr/bin/env python3

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
SCRIPT = TEST_DIR.parent / "audit_textdb_slots_phase0.py"
FIXTURES = TEST_DIR / "fixtures" / "textdb-slots-phase0"
ARTIFACT = FIXTURES / "artifact.json"
SCHEMA = FIXTURES / "schema.json"

SPEC = importlib.util.spec_from_file_location("audit_textdb_slots_phase0", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def empty_entry(key, ordinal):
    provenance = {
        "source_name": "database/monspell.txt",
        "load_index": 0,
        "definition_ordinal": ordinal,
    }
    return {
        "canonical_key": key,
        "effective_provenance": provenance,
        "source_history": [provenance],
        "raw_body": "",
        "body_empty": True,
        "parse_error": None,
        "variants": [],
    }


class TextDBSlotAuditTest(unittest.TestCase):
    def report(self, schema=None, artifact=None):
        return MODULE.audit(artifact or load(ARTIFACT), schema or load(SCHEMA))

    def codes(self, schema=None, artifact=None):
        return {item["code"] for item in self.report(schema, artifact)["violations"]}

    def test_valid_schema_is_deterministic(self):
        first = self.report()
        second = self.report()
        self.assertEqual(first, second)
        self.assertTrue(first["summary"]["valid"])
        self.assertEqual([], first["violations"])
        self.assertRegex(first["inputs"]["dump_fingerprint"], r"^[0-9a-f]{64}$")

    def test_slot_name_format_duplicate_and_speakdb_collision(self):
        schema = load(SCHEMA)
        schema["slots"].extend([
            {"name": "Bad-Name", "type": "resolved_actor"},
            {"name": "actor", "type": "resolved_actor"},
            {"name": "flavor", "type": "resolved_actor"},
        ])
        self.assertTrue({"invalid_slot_name", "duplicate_slot_name",
                         "slot_speakdb_collision"}.issubset(self.codes(schema)))

    def test_slot_syntax_must_be_well_formed_and_declared(self):
        for text in ("${Actor}", "${actor", "$actor"):
            schema = load(SCHEMA)
            schema["templates"][0]["text"] = text
            with self.subTest(text=text):
                self.assertIn("malformed_slot_syntax", self.codes(schema))
        schema = load(SCHEMA)
        schema["templates"][0]["text"] = "${beam}"
        self.assertIn("undeclared_slot", self.codes(schema))

    def test_declared_slot_cannot_use_textdb_syntax(self):
        schema = load(SCHEMA)
        schema["templates"][0]["text"] = "@actor@"
        schema["templates"][0]["declared_recursive_keys"] = ["actor"]
        codes = self.codes(schema)
        self.assertIn("slot_uses_textdb_syntax", codes)
        self.assertIn("missing_recursive_key", codes)

    def test_recursive_keys_require_exact_declaration_use_and_existence(self):
        schema = load(SCHEMA)
        schema["templates"][0]["text"] = "@flavor@ @nested key@"
        schema["templates"][0]["declared_recursive_keys"] = ["flavor", "missing"]
        codes = self.codes(schema)
        self.assertIn("undeclared_recursive_key", codes)
        self.assertIn("unused_recursive_declaration", codes)
        self.assertIn("missing_recursive_key", codes)
        schema["templates"][0]["text"] = "unterminated @flavor"
        self.assertIn("malformed_recursive_syntax", self.codes(schema))

    def test_empty_and_corrupt_entries_are_reserved_but_not_recursive_targets(self):
        empty = load(ARTIFACT)
        flavor = empty["entries"][0]
        flavor.update(raw_body="", body_empty=True, parse_error=None, variants=[])
        self.assertIn("empty_recursive_key", self.codes(artifact=empty))

        corrupt = load(ARTIFACT)
        flavor = corrupt["entries"][0]
        flavor.update(raw_body="w:nope\n", body_empty=False,
                      parse_error="invalid weight", variants=[])
        self.assertIn("corrupt_recursive_key", self.codes(artifact=corrupt))
        self.assertFalse(self.report(artifact=corrupt)["summary"]["valid"])

    def test_overlay_namespace_and_collision_rules(self):
        schema = load(SCHEMA)
        schema["overlay_keys"] = ["outside", "__fork_message_probe",
                                  "__fork_message_PROBE"]
        codes = self.codes(schema)
        self.assertIn("overlay_outside_namespace", codes)
        self.assertIn("duplicate_overlay_key", codes)
        self.assertIn("noncanonical_overlay_key", codes)

        artifact = load(ARTIFACT)
        artifact["entries"].append(empty_entry("__fork_message_taken", 2))
        artifact["entries"].sort(key=lambda entry: entry["canonical_key"])
        schema = load(SCHEMA)
        schema["overlay_keys"] = ["__fork_message_taken"]
        codes = self.codes(schema, artifact)
        self.assertIn("overlay_speakdb_collision", codes)
        self.assertIn("namespace_speakdb_collision", codes)

        schema = load(SCHEMA)
        schema["namespace_prefix"] = "fl"
        schema["overlay_keys"] = []
        self.assertIn("namespace_speakdb_collision", self.codes(schema))

    def test_slot_overlay_and_stable_id_uniqueness(self):
        schema = load(SCHEMA)
        schema["namespace_prefix"] = "actor"
        schema["overlay_keys"] = ["actor"]
        schema["templates"].append(dict(schema["templates"][0]))
        codes = self.codes(schema)
        self.assertIn("slot_overlay_collision", codes)
        self.assertIn("duplicate_stable_id", codes)

    def test_malformed_schema_and_dump_are_protocol_errors(self):
        schema = load(SCHEMA)
        schema["schema_version"] = 2
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.audit(load(ARTIFACT), schema)
        artifact = load(ARTIFACT)
        artifact["entries"].reverse()
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.audit(artifact, load(SCHEMA))

    def test_cli_exit_codes_output_and_check(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            valid = subprocess.run(
                [sys.executable, str(SCRIPT), "--dump", str(ARTIFACT),
                 "--schema", str(SCHEMA), "--output", str(output)],
                check=False, capture_output=True,
            )
            self.assertEqual(0, valid.returncode, valid.stderr.decode())
            check = subprocess.run(
                [sys.executable, str(SCRIPT), "--dump", str(ARTIFACT),
                 "--schema", str(SCHEMA), "--check", str(output)],
                check=False, capture_output=True,
            )
            self.assertEqual(0, check.returncode, check.stderr.decode())
            output.write_bytes(output.read_bytes() + b" ")
            drift = subprocess.run(
                [sys.executable, str(SCRIPT), "--dump", str(ARTIFACT),
                 "--schema", str(SCHEMA), "--check", str(output)],
                check=False, capture_output=True,
            )
            self.assertEqual(1, drift.returncode)

            bad_schema = Path(directory) / "bad.json"
            broken = load(SCHEMA)
            broken["templates"][0]["text"] = "${missing}"
            bad_schema.write_text(json.dumps(broken), encoding="utf-8")
            violation = subprocess.run(
                [sys.executable, str(SCRIPT), "--dump", str(ARTIFACT),
                 "--schema", str(bad_schema)], check=False, capture_output=True,
            )
            self.assertEqual(1, violation.returncode)

            broken["schema_version"] = 2
            bad_schema.write_text(json.dumps(broken), encoding="utf-8")
            protocol = subprocess.run(
                [sys.executable, str(SCRIPT), "--dump", str(ARTIFACT),
                 "--schema", str(bad_schema)], check=False, capture_output=True,
            )
            self.assertEqual(2, protocol.returncode)


if __name__ == "__main__":
    unittest.main()
