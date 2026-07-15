#!/usr/bin/env python3

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
SCRIPT = TEST_DIR.parent / "compare_monspell_phase0.py"
FIXTURES = TEST_DIR / "fixtures" / "monspell-phase0-diff"

SPEC = importlib.util.spec_from_file_location("compare_monspell_phase0", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class CompareMonspellPhase0Test(unittest.TestCase):
    def test_unchanged_dump_has_no_review_evidence(self):
        old = load("old.json")
        report = MODULE.compare(old, old)
        self.assertFalse(report["summary"]["changed"])
        self.assertFalse(report["summary"]["review_required"])
        self.assertEqual([], report["changes"])
        self.assertEqual([], report["global_evidence"])
        self.assertEqual("old-semantic", report["old_inventory"]["semantic_fingerprint"])

    def test_added_removed_and_all_protocol_evidence_are_reported(self):
        report = MODULE.compare(load("old.json"), load("new.json"))
        by_key = {change["canonical_key"]: change for change in report["changes"]}
        self.assertEqual("removed", by_key["alpha"]["status"])
        self.assertEqual("added", by_key["delta"]["status"])
        removed = next(item for item in by_key["alpha"]["evidence"]
                       if item["kind"] == "key_removed")
        added = next(item for item in by_key["delta"]["evidence"]
                     if item["kind"] == "key_added")
        self.assertEqual("monspell.txt", removed["old"]["provenance"]["effective_source"])
        self.assertEqual("alpha-text", removed["old"]["variants"][0]["text_fingerprint"])
        self.assertEqual("delta-entry", added["new"]["entry_text_fingerprint"])
        self.assertEqual(10, added["new"]["variants"][0]["weight"])
        beta_kinds = {item["kind"] for item in by_key["beta"]["evidence"]}
        self.assertTrue({
            "effective_source_provenance",
            "variant_count",
            "variant_weight",
            "variant_text_fingerprint",
            "placeholder_token_set",
            "runtime_token_set",
            "recursive_target_set",
            "random_substring_sites",
            "random_substring_option_count",
            "random_substring_options",
            "control_prefixes",
            "lua_boundaries",
            "entry_text_fingerprint",
            "closure_outgoing_edges",
        }.issubset(beta_kinds))
        gamma_kinds = {item["kind"] for item in by_key["gamma"]["evidence"]}
        self.assertIn("variant_order", gamma_kinds)
        epsilon_kinds = {item["kind"] for item in by_key["epsilon"]["evidence"]}
        self.assertIn("random_substring_sites", epsilon_kinds)
        self.assertNotIn("random_substring_options", epsilon_kinds)
        epsilon_site = next(item for item in by_key["epsilon"]["evidence"]
                            if item["kind"] == "random_substring_sites")
        self.assertEqual(3, epsilon_site["old"][0]["start"])
        self.assertEqual(10, epsilon_site["new"][0]["end"])
        self.assertEqual("a|b", epsilon_site["new"][0]["raw"])
        global_kinds = {item["kind"] for item in report["global_evidence"]}
        self.assertEqual({"speakdb_load_order", "closure_cycles"}, global_kinds)
        self.assertTrue(all(change["review_required"] for change in report["changes"]))
        self.assertFalse(report["review_policy"]["automatic_stable_id_inheritance"])
        self.assertEqual("unclassified", report["review_policy"]["body_change_classification"])
        self.assertEqual(1, report["tool_schema_version"])

    def test_changes_are_sorted_by_canonical_key(self):
        report = MODULE.compare(load("old.json"), load("new.json"))
        keys = [change["canonical_key"] for change in report["changes"]]
        self.assertEqual(sorted(keys), keys)

    def test_changed_dump_is_a_successful_cli_result(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(FIXTURES / "old.json"),
             str(FIXTURES / "new.json")],
            check=False, capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr.decode())
        self.assertTrue(json.loads(result.stdout)["summary"]["changed"])

    def test_output_and_byte_for_byte_check(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            write = subprocess.run(
                [sys.executable, str(SCRIPT), str(FIXTURES / "old.json"),
                 str(FIXTURES / "new.json"), "--output", str(output)],
                check=False, capture_output=True,
            )
            self.assertEqual(0, write.returncode, write.stderr.decode())
            check = subprocess.run(
                [sys.executable, str(SCRIPT), str(FIXTURES / "old.json"),
                 str(FIXTURES / "new.json"), "--check", str(output)],
                check=False, capture_output=True,
            )
            self.assertEqual(0, check.returncode, check.stderr.decode())
            output.write_bytes(output.read_bytes() + b" ")
            drift = subprocess.run(
                [sys.executable, str(SCRIPT), str(FIXTURES / "old.json"),
                 str(FIXTURES / "new.json"), "--check", str(output)],
                check=False, capture_output=True,
            )
            self.assertEqual(1, drift.returncode)
            self.assertIn(b"drift", drift.stderr)

    def test_unsupported_inventory_schema_returns_protocol_error(self):
        bad = load("old.json")
        bad["schema_version"] = 2
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text(json.dumps(bad), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), str(FIXTURES / "new.json")],
                check=False, capture_output=True,
            )
        self.assertEqual(2, result.returncode)
        self.assertIn(b"unsupported schema_version", result.stderr)

    def test_malformed_inventory_returns_protocol_error(self):
        bad = load("old.json")
        bad["entries"][0]["variants"] = "not-an-array"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text(json.dumps(bad), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), str(FIXTURES / "new.json")],
                check=False, capture_output=True,
            )
        self.assertEqual(2, result.returncode)
        self.assertIn(b"protocol error", result.stderr)

    def test_malformed_token_random_site_and_options_are_protocol_errors(self):
        mutations = [
            lambda d: d["entries"][1]["variants"][0]["tokens"].__setitem__(0, "bad"),
            lambda d: d["entries"][1]["variants"][0]["random_substring_sites"].__setitem__(0, "bad"),
            lambda d: d["entries"][2]["variants"][0]["random_substring_sites"][0].update(options="bad"),
            lambda d: d["entries"][2]["variants"][0]["random_substring_sites"][0].update(options=["wrong"]),
        ]
        for mutation in mutations:
            bad = load("old.json")
            mutation(bad)
            with self.subTest(mutation=mutation):
                with self.assertRaises(MODULE.ProtocolError):
                    MODULE.compare(bad, load("new.json"))

        bad = load("old.json")
        bad["entries"][1]["variants"][0]["tokens"][0] = "bad"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad-token.json"
            path.write_text(json.dumps(bad), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path),
                 str(FIXTURES / "new.json")],
                check=False, capture_output=True,
            )
        self.assertEqual(2, result.returncode)
        self.assertIn(b"protocol error", result.stderr)


if __name__ == "__main__":
    unittest.main()
