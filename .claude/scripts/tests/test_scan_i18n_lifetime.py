#!/usr/bin/env python3
"""Black-box regression tests for scan_i18n_lifetime.py."""

from __future__ import annotations

import json
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


SCANNER = Path(__file__).resolve().parents[1] / "scan_i18n_lifetime.py"


class LifetimeScannerTests(unittest.TestCase):
    def run_scan(self, files: dict[str, str], *args: str):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, source in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(textwrap.dedent(source), encoding="utf-8")
            proc = subprocess.run(
                ["python3", str(SCANNER), str(root), *args],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            return proc

    def json_scan(self, files: dict[str, str], *args: str):
        proc = self.run_scan(files, "--format", "json", *args)
        return proc, json.loads(proc.stdout)

    def test_direct_static_raw_sinks_are_blocking(self):
        proc, data = self.json_scan({"sample.cc": r'''
            const char *T_(const char *);
            const char *C_(const char *, const char *);
            void f() {
                static const char *one = T_("one");
                static const char *many[] = { C_("ctx", "many") };
            }
        '''})
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual([f["rule"] for f in data["findings"]],
                         ["LIFE001", "LIFE001"])
        self.assertEqual(data["summary"], {"HIGH": 2, "WARN": 0, "total": 2})

    def test_aggregate_and_borrowed_helper_chain(self):
        proc, data = self.json_scan({
            "model.h": r'''
                struct entry { int id; const char *name; };
                const char *first(const char *);
                const char *second(const char *);
            ''',
            "model.cc": r'''
                #include "model.h"
                #include <vector>
                const char *T_(const char *);
                const char *first(const char *s) { return T_(s); }
                const char *second(const char *s) { return first(s); }
                void f() {
                    static const std::vector<entry> values = {
                        { 1, second("borrowed") },
                    };
                }
            ''',
        })
        self.assertEqual(proc.returncode, 1, proc.stderr)
        high = data["findings"]
        self.assertEqual(len(high), 1)
        self.assertEqual(high[0]["rule"], "LIFE001")
        self.assertEqual(high[0]["field_path"], "[].name")
        self.assertEqual(len(high[0]["fingerprint"]), 64)

    def test_member_assignment_and_persistent_container_mutation(self):
        proc, data = self.json_scan({"sample.cc": r'''
            #include <vector>
            const char *T_(const char *);
            struct item { const char *name; };
            struct cache {
                const char *current;
                std::vector<item> items;
                void update() {
                    current = T_("now");
                    items.emplace_back(item{T_("later")});
                }
            };
        '''})
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual({f["rule"] for f in data["findings"]},
                         {"LIFE002", "LIFE003"})

    def test_warnings_are_advisory_and_hidden_by_default(self):
        files = {"sample.cc": r'''
            #include <string>
            const char *T_(const char *);
            const char *global_name = T_("global");
            void f() { static std::string frozen = T_("frozen"); }
        '''}
        default, default_data = self.json_scan(files)
        self.assertEqual(default.returncode, 0, default.stderr)
        self.assertEqual(default_data["findings"], [])
        warned, warned_data = self.json_scan(files, "--include-warn")
        self.assertEqual(warned.returncode, 0, warned.stderr)
        self.assertEqual({f["rule"] for f in warned_data["findings"]},
                         {"LIFE101", "LIFE102"})

    def test_namespace_static_linkage_is_still_advisory(self):
        proc, data = self.json_scan({"sample.cc": r'''
            const char *T_(const char *);
            static const char *internal = T_("startup");
        '''}, "--include-warn")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual([f["rule"] for f in data["findings"]], ["LIFE101"])

    def test_mixed_aggregate_fields_are_mapped_by_position(self):
        proc, data = self.json_scan({"sample.cc": r'''
            #include <string>
            #include <vector>
            const char *T_(const char *);
            struct entry { std::string owned; const char *raw; };
            void f() {
                static const std::vector<entry> values = {
                    { T_("owned"), T_("raw") },
                };
            }
        '''}, "--include-warn")
        self.assertEqual(proc.returncode, 1, proc.stderr)
        by_rule = {f["rule"]: f for f in data["findings"]}
        self.assertEqual(by_rule["LIFE102"]["field_path"], "[].owned")
        self.assertEqual(by_rule["LIFE001"]["field_path"], "[].raw")

    def test_automatic_and_deferred_uses_are_safe(self):
        proc, data = self.json_scan({"sample.cc": r'''
            #include <string>
            const char *T_(const char *);
            void consume(const char *value = T_("default"));
            struct item { const char *name; };
            void f() {
                const char *local = T_("local");
                const char *array[] = { T_("array") };
                std::string owned = T_("owned");
                item transient{T_("transient")};
                consume(T_("immediate"));
                static auto callback = [] { return T_("runtime"); };
            }
        '''}, "--include-warn")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(data["findings"], [])

    def test_raw_english_key_translated_at_use_is_safe(self):
        proc, data = self.json_scan({"sample.cc": r'''
            const char *T_(const char *);
            static const char *keys[] = { "first", "second" };
            void consume(const char *);
            void f() { consume(T_(keys[0])); }
        '''}, "--include-warn")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(data["summary"]["total"], 0)

    def test_json_is_stable_sorted_and_schema_complete(self):
        files = {"z.cc": r'''
            const char *T_(const char *);
            void z() { static const char *z = T_("z"); }
        ''', "a.cc": r'''
            const char *T_(const char *);
            void a() { static const char *a = T_("a"); }
        '''}
        first, data1 = self.json_scan(files)
        second, data2 = self.json_scan(files)
        self.assertEqual(first.returncode, 1)
        self.assertEqual(second.returncode, 1)
        self.assertEqual(data1, data2)
        required = {"rule", "risk", "file", "line", "column", "storage",
                    "sink_type", "field_path", "source_expr", "message",
                    "fingerprint"}
        self.assertTrue(all(required == set(finding) for finding in data1["findings"]))
        self.assertEqual([f["file"] for f in data1["findings"]], ["a.cc", "z.cc"])

    def test_fingerprint_ignores_line_number_churn(self):
        source = r'''
            const char *T_(const char *);
            void f() { static const char *value = T_("stable"); }
        '''
        _, first = self.json_scan({"sample.cc": source})
        _, shifted = self.json_scan({"sample.cc": "\n\n\n" + source})
        self.assertNotEqual(first["findings"][0]["line"], shifted["findings"][0]["line"])
        self.assertEqual(first["findings"][0]["fingerprint"],
                         shifted["findings"][0]["fingerprint"])

    def test_non_pointer_return_is_not_a_borrowed_helper(self):
        proc, data = self.json_scan({"sample.cc": r'''
            const char *T_(const char *);
            int numeric(const char *s) { return (T_(s), 1); }
            void f() { static const char *value = numeric("not a pointer"); }
        '''}, "--include-warn")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(data["findings"], [])

    def test_files_mode_indexes_from_stable_source_root(self):
        with tempfile.TemporaryDirectory() as temp:
            source_root = Path(temp) / "crawl-ref" / "source"
            helper = source_root / "lib" / "helper.cc"
            target = source_root / "feature" / "use.cc"
            helper.parent.mkdir(parents=True)
            target.parent.mkdir(parents=True)
            helper.write_text(textwrap.dedent(r'''
                const char *T_(const char *);
                const char *borrowed(const char *s) { return T_(s); }
            '''), encoding="utf-8")
            target.write_text(textwrap.dedent(r'''
                const char *borrowed(const char *);
                void f() { static const char *value = borrowed("cross-dir"); }
            '''), encoding="utf-8")
            proc = subprocess.run(
                ["python3", str(SCANNER), "--files", str(target),
                 "--format", "json"], text=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, check=False)
            data = json.loads(proc.stdout)
            self.assertEqual(proc.returncode, 1, proc.stderr)
            self.assertEqual(data["summary"]["HIGH"], 1)
            self.assertEqual(data["findings"][0]["file"], "feature/use.cc")

    def test_syntax_error_in_target_fails_closed(self):
        proc = self.run_scan({"broken.cc": "void f( { static const char *x = T_(\"x\");"})
        self.assertEqual(proc.returncode, 2)
        self.assertIn("ERROR", proc.stderr)

    def test_large_root_keeps_helper_assignment_and_container_rules(self):
        files = {f"padding/{i:03}.h": "#pragma once\n" for i in range(205)}
        files.update({
            "helper.cc": r'''
                const char *T_(const char *);
                const char *borrowed(const char *s) { return T_(s); }
            ''',
            "target.cc": r'''
                #include <vector>
                const char *T_(const char *);
                const char *borrowed(const char *);
                struct item { const char *name; };
                struct cache {
                    const char *current;
                    std::vector<item> items;
                    void update() {
                        current = T_("assigned");
                        items.emplace_back(item{T_("inserted")});
                    }
                };
                void f() { static const char *value = borrowed("helper"); }
            ''',
        })
        proc, data = self.json_scan(files)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual({f["rule"] for f in data["findings"]},
                         {"LIFE001", "LIFE002", "LIFE003"})

    def test_immediately_invoked_lambda_is_not_deferred(self):
        proc, data = self.json_scan({"sample.cc": r'''
            const char *T_(const char *);
            void f() {
                static const char *value = [] { return T_("now"); }();
            }
        '''})
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual([f["rule"] for f in data["findings"]], ["LIFE001"])

    def test_invalid_input_fails_closed(self):
        proc = subprocess.run(
            ["python3", str(SCANNER), "/definitely/not/a/source/tree"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("ERROR", proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
