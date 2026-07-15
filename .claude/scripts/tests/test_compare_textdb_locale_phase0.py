#!/usr/bin/env python3

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
SCRIPT = TEST_DIR.parent / "compare_textdb_locale_phase0.py"
FIXTURES = TEST_DIR / "fixtures" / "textdb-locale-phase0"
CANONICAL = FIXTURES / "canonical.json"
LOCALIZED = FIXTURES / "localized.json"

SPEC = importlib.util.spec_from_file_location("compare_textdb_locale_phase0", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class LocaleTopologyCompareTest(unittest.TestCase):
    def report(self):
        return MODULE.compare(load(CANONICAL), load(LOCALIZED))

    def roots(self):
        return {root["root"]: root for root in self.report()["roots"]}

    def test_resolution_records_override_fallback_localized_only_and_missing(self):
        report = self.report()
        self.assertEqual(["localized helper"], report["resolution"]["localized_only"])
        self.assertEqual(["root changed", "root same"], report["resolution"]["overridden"])
        self.assertEqual(["root fallback", "shared"], report["resolution"]["fallback"])
        self.assertEqual(["empty root"], report["resolution"]["missing"])

    def test_fallback_and_lexical_translation_preserve_static_topology(self):
        roots = self.roots()
        self.assertFalse(roots["root fallback"]["trace_topology_changed"])
        self.assertFalse(roots["root same"]["trace_topology_changed"])
        self.assertFalse(roots["empty root"]["trace_topology_changed"])
        self.assertEqual([], roots["root same"]["evidence"])

    def test_changed_root_reports_each_static_trace_dimension(self):
        root = self.roots()["root changed"]
        self.assertTrue(root["trace_topology_changed"])
        self.assertTrue(root["review_required"])
        self.assertEqual(["root changed", "shared"], root["canonical_closure"])
        self.assertEqual(["localized helper", "root changed"], root["localized_closure"])
        kinds = {item["kind"] for item in root["evidence"]}
        self.assertTrue({
            "recursive_closure",
            "weights",
            "selection_bounds",
            "random_bound",
            "recursive_reference_sequence",
            "lua_site_sequence",
            "random_substring_option_count_sequence",
            "graph_node_presence",
        }.issubset(kinds))

    def test_recursive_scanner_uses_runtime_empty_and_cross_line_pairing(self):
        sites, unbalanced = MODULE.textdb_marker_sites("@@shared@")
        self.assertEqual(
            [{"token": "", "canonical_key": "", "start": 0, "end": 2}],
            sites,
        )
        self.assertEqual(8, unbalanced)
        self.assertEqual([], MODULE._recursive_sequence("@@shared@", {"shared"}))

        sites, unbalanced = MODULE.textdb_marker_sites("@cross\nline@")
        self.assertIsNone(unbalanced)
        self.assertEqual(
            [{"token": "cross\nline", "canonical_key": "cross\nline",
              "start": 0, "end": 12}],
            sites,
        )

    def test_variant_count_is_compared(self):
        canonical = load(CANONICAL)
        localized = load(LOCALIZED)
        changed = next(e for e in localized["entries"] if e["canonical_key"] == "root changed")
        changed["variants"].append({
            "locator": {"canonical_key": "root changed", "variant_ordinal": 1},
            "provenance": changed["effective_provenance"],
            "weight": 2,
            "raw_pattern": "second",
        })
        report = MODULE.compare(canonical, localized)
        root = next(r for r in report["roots"] if r["root"] == "root changed")
        kinds = {item["kind"] for item in root["evidence"]}
        self.assertIn("variant_count", kinds)
        self.assertIn("variant_added", kinds)

    def test_corrupt_entries_are_explicit_and_require_review(self):
        canonical = load(CANONICAL)
        localized = load(LOCALIZED)
        shared = next(e for e in canonical["entries"] if e["canonical_key"] == "shared")
        shared.update(raw_body="w:nope\n", body_empty=False,
                      parse_error="invalid weight", variants=[])
        fallback = next(e for e in localized["entries"]
                        if e["canonical_key"] == "root fallback")
        fallback.update(raw_body="w:nope\n", body_empty=False,
                        parse_error="invalid weight", variants=[])

        report = MODULE.compare(canonical, localized)
        self.assertEqual({"canonical": ["shared"],
                          "localized": ["root fallback"]},
                         report["resolution"]["corrupt"])
        self.assertNotIn("root fallback", report["resolution"]["fallback"])
        self.assertNotIn("shared", report["resolution"]["missing"])
        self.assertEqual(2, report["summary"]["corrupt_entries"])
        self.assertTrue(report["summary"]["review_required"])

    def test_report_is_deterministic_and_has_static_scope_disclaimer(self):
        first = self.report()
        second = self.report()
        self.assertEqual(first, second)
        self.assertEqual("static_selection_topology_only", first["scope"])
        self.assertFalse(first["dynamic_trace_proven"])
        self.assertEqual(["root changed"],
                         first["summary"]["trace_topology_changed_roots"])
        self.assertTrue(first["summary"]["review_required"])

    def test_protocol_rejects_schema_order_body_and_locator_errors(self):
        canonical = load(CANONICAL)
        localized = load(LOCALIZED)
        bad = json.loads(json.dumps(canonical))
        bad["schema_version"] = 2
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.compare(bad, localized)
        bad = json.loads(json.dumps(canonical))
        bad["entries"].reverse()
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.compare(bad, localized)
        bad = json.loads(json.dumps(canonical))
        bad["entries"][1]["body_empty"] = True
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.compare(bad, localized)
        bad = json.loads(json.dumps(localized))
        bad["entries"][1]["variants"][0]["locator"]["variant_ordinal"] = 3
        with self.assertRaises(MODULE.ProtocolError):
            MODULE.compare(canonical, bad)

    def test_cli_output_check_and_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.json"
            create = subprocess.run(
                [sys.executable, str(SCRIPT), "--canonical-dump", str(CANONICAL),
                 "--localized-dump", str(LOCALIZED), "--output", str(report)],
                check=False, capture_output=True,
            )
            # Topology changes are a normal comparison result, not a tool error.
            self.assertEqual(0, create.returncode, create.stderr.decode())
            check = subprocess.run(
                [sys.executable, str(SCRIPT), "--canonical-dump", str(CANONICAL),
                 "--localized-dump", str(LOCALIZED), "--check", str(report)],
                check=False, capture_output=True,
            )
            self.assertEqual(0, check.returncode, check.stderr.decode())
            report.write_bytes(report.read_bytes() + b" ")
            drift = subprocess.run(
                [sys.executable, str(SCRIPT), "--canonical-dump", str(CANONICAL),
                 "--localized-dump", str(LOCALIZED), "--check", str(report)],
                check=False, capture_output=True,
            )
            self.assertEqual(1, drift.returncode)

            bad = Path(directory) / "bad.json"
            bad.write_text("{}", encoding="utf-8")
            protocol = subprocess.run(
                [sys.executable, str(SCRIPT), "--canonical-dump", str(bad),
                 "--localized-dump", str(LOCALIZED)],
                check=False, capture_output=True,
            )
            self.assertEqual(2, protocol.returncode)


if __name__ == "__main__":
    unittest.main()
