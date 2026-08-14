#!/usr/bin/env python3
"""Cross-scanner regressions for Issue #12 discovery and dataflow gaps."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / ".claude/scripts"


def _coverage(data):
    return (data["coverage"] if "coverage" in data
            else data["meta"]["coverage"])


class ScannerCompletenessTests(unittest.TestCase):
    # Expected normalized findings for the real directn.cc concat scan:
    # directn.cc:3040/3042/3044 messageLookup += and 3072/3078/3081 runtime
    # concat. Tuple: (file, line, rule, literal).
    DIRECTN_CONCAT_FINDINGS = [
        ("directn.cc", 3040, "COMPOUND_ASSIGN", "fruit cache"),
        ("directn.cc", 3042, "COMPOUND_ASSIGN", "meat cache"),
        ("directn.cc", 3044, "COMPOUND_ASSIGN", "baked goods cache"),
        ("directn.cc", 3072, "RUNTIME_CONCAT", " peaceful "),
        ("directn.cc", 3078, "RUNTIME_CONCAT", "default peaceful "),
        ("directn.cc", 3081, "RUNTIME_CONCAT", "default "),
    ]

    def _normalized_findings(self, data):
        return sorted(
            (item["file"], item["line"], item["rule"], item["literal"])
            for item in data.get("findings", []))

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
                    coverage = _coverage(data)
                    self.assertEqual(coverage,
                                     {"discovered": 1,
                                      "scanned": 1,
                                      "failed": []})

    def test_directn_preprocessor_split_false_positives_pass_changed_scope(self):
        # Issue #40 W1: changed-scope --files validation used to fail closed
        # on directn.cc's pre-existing preprocessor-conditional tree-sitter
        # false positives while the full-root entry skipped validation.
        # Both entries must now scan the real file: varargs exits 0 (no
        # findings) and concat exits 1 driven by the six known findings,
        # never by a parse failure.
        directn = ROOT / "crawl-ref" / "source" / "directn.cc"
        self.assertTrue(directn.is_file(), directn)
        expected = {
            "scan_string_concat.py": (1, self.DIRECTN_CONCAT_FINDINGS),
            "scan_varargs_string.py": (0, []),
        }
        for scanner, (exit_code, findings) in expected.items():
            with self.subTest(scanner=scanner, entry="files"):
                proc = self.run_scanner(scanner, "--files", directn,
                                        "--format", "json",
                                        "--require-parser")
                self.assertEqual(exit_code, proc.returncode, proc.stderr)
                data = json.loads(proc.stdout)
                coverage = _coverage(data)
                self.assertEqual(coverage["scanned"], 1)
                self.assertEqual(coverage["failed"], [])
                self.assertEqual(findings, self._normalized_findings(data))

    def test_directn_preprocessor_split_false_positives_pass_directory_entry(self):
        # Issue #40 W1: the directory-root entry (parse validation enabled
        # for non-production roots) must agree with the --files entry on the
        # real directn.cc. The fixture lives in a unique directory directly
        # under /tmp, the repository convention used by inventory tests.
        directn = ROOT / "crawl-ref" / "source" / "directn.cc"
        self.assertTrue(directn.is_file(), directn)
        td = Path("/tmp") / (
            f"scanner-directn-test-{os.getpid()}-{uuid.uuid4().hex}")
        td.mkdir()
        try:
            shutil.copy2(directn, td / "directn.cc")
            for scanner in ("scan_string_concat.py",
                            "scan_varargs_string.py"):
                with self.subTest(scanner=scanner, entry="dir"):
                    proc = self.run_scanner(scanner, td, "--format", "json",
                                            "--require-parser")
                    data = json.loads(proc.stdout)
                    coverage = _coverage(data)
                    self.assertEqual(coverage["scanned"], 1)
                    self.assertEqual(coverage["failed"], [])
                    # Directory entry must agree with the --files entry on
                    # exit code, coverage, and every finding.
                    proc_files = self.run_scanner(
                        scanner, "--files", directn, "--format", "json",
                        "--require-parser")
                    self.assertEqual(proc_files.returncode, proc.returncode,
                                     proc.stderr)
                    self.assertEqual(
                        coverage, _coverage(json.loads(proc_files.stdout)))
                    self.assertEqual(
                        self._normalized_findings(data),
                        self._normalized_findings(
                            json.loads(proc_files.stdout)))
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_real_parse_error_fails_closed_in_directory_entry(self):
        # Real syntax errors must fail closed from the directory entry too,
        # not just from --files (Issue #40 W1 acceptance criterion 2).
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "broken.cc"
            source.write_text('void f( { auto x = "broken";\n',
                              encoding="utf-8")
            for scanner in ("scan_string_concat.py",
                            "scan_varargs_string.py"):
                with self.subTest(scanner=scanner, entry="dir"):
                    proc = self.run_scanner(scanner, td, "--format", "json",
                                            "--require-parser")
                    self.assertEqual(2, proc.returncode, proc.stderr)
                    coverage = _coverage(json.loads(proc.stdout))
                    self.assertEqual(coverage["scanned"], 0)
                    self.assertEqual(len(coverage["failed"]), 1)

    def test_real_error_in_directn_copy_still_fails_closed(self):
        # The narrow exemption must not mask a real syntax error even inside
        # the exact file it was built for: inject a genuine break at line 1
        # (outside any preprocessor switch point) and both entries must fail.
        directn = ROOT / "crawl-ref" / "source" / "directn.cc"
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "directn.cc"
            source.write_bytes(b"int x = ;\n" + directn.read_bytes())
            for scanner in ("scan_string_concat.py", "scan_varargs_string.py"):
                for entry, args in (("files", ("--files", source)),
                                    ("dir", (td,))):
                    with self.subTest(scanner=scanner, entry=entry):
                        proc = self.run_scanner(scanner, *args,
                                                "--format", "json",
                                                "--require-parser")
                        self.assertEqual(2, proc.returncode, proc.stderr)
                        coverage = _coverage(json.loads(proc.stdout))
                        self.assertEqual(coverage["scanned"], 0)
                        self.assertEqual(len(coverage["failed"]), 1)

    def test_preprocessor_switch_context_required_for_baseline_exemption(self):
        # The frozen-baseline exemption must fire only at a preprocessor
        # switch point: the same line text outside a conditional, inside a
        # dead #if 0 body, or a genuine error on other text must fail closed.
        try:
            import tree_sitter_cpp as _tscpp
            from tree_sitter import Language as _Language
            from tree_sitter import Parser as _Parser
        except ImportError as exc:
            self.skipTest(f"tree-sitter not installed: {exc}")
        sys.path.insert(0, str(SCRIPTS))
        from i18n_shared import has_relevant_parse_error

        lang = _Language(_tscpp.language())
        parser = _Parser(lang)
        baseline = ('const vault_placement '
                    '&vp(*env.level_vaults[map_index]);')
        cases = [
            ("baseline inside #ifdef is exempt",
             f'''void f() {{
#ifdef DEBUG_DIAGNOSTICS
    {baseline}
#endif
}}
''',
             False),
            ("same baseline text without any conditional fails closed",
             f'''void f() {{
    {baseline}
}}
''',
             True),
            ("baseline inside dead #if 0 body fails closed",
             f'''void f() {{
#if 0
    {baseline}
#endif
}}
''',
             True),
            ("baseline inside #if 0 nested in a live conditional fails closed",
             f'''void f() {{
#ifdef FOO
    {baseline}
#if 0
    {baseline}
#endif
    {baseline}
#endif
}}
''',
             True),
            ("real error inside #if 0 fails closed",
             '''void f() {
#if 0
    int x = ;
#endif
}
''',
             True),
            ("fake comment directives do not create a switch point",
             f'''/* comment block
#ifdef FAKE
#endif
*/
void f() {{
    {baseline}
}}
''',
             True),
            ("real error inside a live conditional fails closed",
             '''void f() {
#ifdef FOO
    int x = ;
#endif
}
''',
             True),
        ]
        for name, source, expected in cases:
            with self.subTest(case=name):
                tree = parser.parse(source.encode("utf-8"))
                self.assertEqual(
                    expected,
                    has_relevant_parse_error(tree.root_node,
                                             source.encode("utf-8")),
                    name)

    def test_dead_preprocessor_blocks_are_subtracted_from_switch_points(self):
        # Issue #40 W1 blocker A: dead #if 0 interiors must be subtracted
        # from the final switch-point set even when an enclosing live span,
        # a nested live span, or a preceding post-#endif window also covers
        # them; standalone dead blocks contribute no lines at all.
        sys.path.insert(0, str(SCRIPTS))
        from i18n_shared import _preprocessor_switch_lines

        cases = [
            ("dead block nested inside a live conditional",
             b'''void f() {
#ifdef FOO
    int live = 1;
#if 0
    int dead = 1;
#endif
    int live2 = 2;
#endif
}
''',
             {3, 7}),  # live bodies only
            ("live conditional nested inside a dead block",
             b'''void f() {
#if 0
#ifdef FOO
    int dead = 1;
#endif
#endif
}
''',
             set()),
            ("dead block inside the post-#endif window of a live span",
             b'''void f() {
#ifdef FOO
#endif
#if 0
    int dead = 1;
#endif
}
''',
             set()),
            ("standalone dead block contributes no lines",
             b'''void f() {
#if 0
    int dead = 1;
#endif
}
''',
             set()),
        ]
        for name, source, required in cases:
            with self.subTest(case=name):
                switch = _preprocessor_switch_lines(source)
                self.assertIsNotNone(switch, name)
                self.assertTrue(required.issubset(switch), switch)
                # No line inside any dead body may survive subtraction.
                dead_body = {line_no for line_no, text in enumerate(
                    source.split(b"\n"), start=1)
                    if b"int dead" in text}
                self.assertTrue(dead_body.isdisjoint(switch), switch)

    def test_comment_and_string_hash_lines_are_not_directives(self):
        # Issue #40 W1 blocker B: directive discovery must honor the C++
        # lexical context. A '#' at the start of a line inside a block
        # comment or a string literal is not a preprocessor directive:
        # fake #ifdef/#endif comment or string text must not shift pairing
        # or span computation, real directives outside comments still pair
        # correctly, and unmatched directives still fail closed (None).
        sys.path.insert(0, str(SCRIPTS))
        from i18n_shared import _preprocessor_switch_lines

        # Fake #ifdef/#endif inside a block comment: the real conditional
        # still yields exactly its own body plus the post-#endif window.
        switch = _preprocessor_switch_lines(
            b'''/* comment block
#ifdef FAKE
#endif
*/
void f() {
#ifdef REAL
    int ok = 1;
#endif
}
''')
        self.assertEqual(frozenset({7, 9, 10, 11, 12}), switch)

        # A fake #endif inside a comment must not pop a real #if.
        switch = _preprocessor_switch_lines(
            b'''/* comment
#endif
*/
void f() {
#ifdef REAL
    int ok = 1;
#endif
}
''')
        self.assertEqual(frozenset({6, 8, 9, 10, 11}), switch)

        # A '#' line inside a backslash-continued string literal is not a
        # directive either.
        switch = _preprocessor_switch_lines(
            b'''const char* s = "abc \\
#ifdef FAKE
def";
void f() {
#ifdef REAL
    int ok = 1;
#endif
}
''')
        self.assertEqual(frozenset({6, 8, 9, 10, 11}), switch)

        # Normal directives outside comments still pair correctly.
        switch = _preprocessor_switch_lines(
            b'''void f() {
#ifdef A
#if defined(B) && B > 0
    int x = 1;
#else
    int y = 1;
#endif
#endif
}
''')
        self.assertEqual(
            frozenset({3, 4, 5, 6, 7, 8, 9, 10, 11, 12}), switch)

        # Unmatched directives still fail closed.
        self.assertIsNone(_preprocessor_switch_lines(
            b'''void f() {
#ifdef REAL
    int ok = 1;
}
'''))

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
