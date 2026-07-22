#!/usr/bin/env python3
"""Cross-scanner regressions for Issue #12 discovery and dataflow gaps."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / ".claude/scripts"


class ScannerCompletenessTests(unittest.TestCase):
    def run_scanner(self, name, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / name), *map(str, args)],
            text=True, capture_output=True, check=False)

    def test_explicit_missing_inputs_fail_visible(self):
        missing = ROOT / "does-not-exist.cc"
        for scanner in ("scan_string_concat.py", "scan_varargs_string.py",
                        "scan_i18n_lifetime.py"):
            with self.subTest(scanner=scanner):
                proc = self.run_scanner(scanner, "--files", missing)
                self.assertEqual(2, proc.returncode, proc.stderr)
                self.assertIn("ERROR", proc.stderr)
        proc = self.run_scanner("i18n_extract.py", "extract", missing)
        self.assertEqual(2, proc.returncode, proc.stderr)

    def test_extractor_emits_explicit_coverage_report(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "sample.cc").write_text('auto x = T_("key");\n',
                                             encoding="utf-8")
            report = root / "coverage.json"
            proc = self.run_scanner("i18n_extract.py", "extract", root,
                                    "--report-json", report)
            data = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual(data["coverage"],
                         {"discovered": 1, "scanned": 1, "failed": []})

    def test_relevant_parser_errors_fail_visible(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "broken.cc"
            source.write_text('void f( { auto x = "broken";\n',
                              encoding="utf-8")
            for scanner in ("scan_string_concat.py",
                            "scan_varargs_string.py"):
                with self.subTest(scanner=scanner):
                    proc = self.run_scanner(scanner, "--files", source,
                                            "--format", "json")
                    self.assertEqual(2, proc.returncode, proc.stderr)
                    data = json.loads(proc.stdout)
                    coverage = (data["coverage"] if "coverage" in data
                                else data["meta"]["coverage"])
                    self.assertEqual(coverage["scanned"], 0)
                    self.assertEqual(len(coverage["failed"]), 1)

    def test_valid_preprocessor_and_member_pointer_nodes_are_recoverable(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "valid.cc"
            source.write_text(r'''
                struct sample {
                    void invoke(void (sample::*member)());
                };
                void sample::invoke(void (sample::*member)()) {
                    (this->*member)();
                    const char* values[] = {
                #if TAG_MAJOR_VERSION == 34
                        "legacy",
                #endif
                        "current",
                    };
                }
            ''', encoding="utf-8")
            for scanner in ("scan_string_concat.py",
                            "scan_varargs_string.py"):
                with self.subTest(scanner=scanner):
                    proc = self.run_scanner(scanner, "--files", source,
                                            "--format", "json",
                                            "--require-parser")
                    self.assertEqual(0, proc.returncode, proc.stderr)
                    data = json.loads(proc.stdout)
                    coverage = (data["coverage"] if "coverage" in data
                                else data["meta"]["coverage"])
                    self.assertEqual(coverage,
                                     {"discovered": 1,
                                      "scanned": 1,
                                      "failed": []})

    def test_deferred_stream_builder_traces_to_display_sink(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "sample.cc"
            source.write_text(r'''
                void f() {
                    ostringstream text;
                    text << N_("deferred raw text");
                    mpr(text.str());
                }
                void unrelated() {
                    ostringstream text;
                    text << "same receiver, different function";
                    // mpr(text.str());
                }
            ''', encoding="utf-8")
            proc = self.run_scanner(
                "scan_string_concat.py", "--files", source,
                "--min-risk", "HIGH", "--format", "json")
        self.assertEqual(1, proc.returncode, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["meta"]["coverage"],
                         {"discovered": 1, "scanned": 1, "failed": []})
        self.assertEqual(data["findings"][0]["sink"], "mpr")
        self.assertEqual(data["findings"][0]["literal"], "deferred raw text")
        unrelated = next(item for item in data["findings"]
                         if item["literal"] ==
                         "same receiver, different function")
        self.assertIsNone(unrelated["sink"])

    def test_varargs_uses_local_type_and_every_ternary_arm(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "sample.cc"
            source.write_text(r'''
                void f(bool flag) {
                    string local;
                    make_stringf("%s", local);
                    make_stringf("%s", flag ? T_("safe") : local);
                    mprf(MSGCH_PLAIN, 0, "%s", local);
                    die(__FILE__, __LINE__, "%s", local);
                }
            ''', encoding="utf-8")
            proc = self.run_scanner(
                "scan_varargs_string.py", "--files", source,
                "--format", "json")
        self.assertEqual(1, proc.returncode, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual([item["rule"] for item in data["findings"]],
                         ["STRING_OBJECT", "TERNARY",
                          "STRING_OBJECT", "STRING_OBJECT"])
        self.assertEqual(data["coverage"],
                         {"discovered": 1, "scanned": 1, "failed": []})


if __name__ == "__main__":
    unittest.main(verbosity=2)
