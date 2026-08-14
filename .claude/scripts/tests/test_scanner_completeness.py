#!/usr/bin/env python3
"""Cross-scanner regressions for Issue #12 discovery and dataflow gaps."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
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
        # Issue #40 W1: the production-root directory entry (a one-file
        # temporary .../crawl-ref/source root whose basename is 'source'
        # with parent 'crawl-ref' sets production_root=true and skips parse
        # validation) must agree with the --files entry (validation on) on
        # exact exit code, coverage, and every normalized finding
        # (TEST-003: the fixture must live under a temporary crawl-ref/
        # source path, not an arbitrary directory).
        directn = ROOT / "crawl-ref" / "source" / "directn.cc"
        self.assertTrue(directn.is_file(), directn)
        expected = {
            "scan_string_concat.py": (1, self.DIRECTN_CONCAT_FINDINGS),
            "scan_varargs_string.py": (0, []),
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "crawl-ref" / "source"
            root.mkdir(parents=True)
            shutil.copy2(directn, root / "directn.cc")
            for scanner, (exit_code, findings) in expected.items():
                with self.subTest(scanner=scanner, entry="dir"):
                    proc = self.run_scanner(scanner, root, "--format", "json",
                                            "--require-parser")
                    self.assertEqual(exit_code, proc.returncode, proc.stderr)
                    data = json.loads(proc.stdout)
                    coverage = _coverage(data)
                    self.assertEqual(
                        coverage, {"discovered": 1, "scanned": 1,
                                   "failed": []})
                    self.assertEqual(findings,
                                     self._normalized_findings(data))
                    # Exact parity with the --files entry.
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

    def test_preprocessor_mutations_fail_closed_both_entries(self):
        # Issue #40 W1 round-2 blockers, end to end: fake #ifdef/#endif
        # inside raw strings or line-spliced comments must not forge switch
        # eligibility (CODE-002), a live conditional nested inside #if 0
        # must not leak a post-#endif window over the frozen baseline
        # (CODE-001), and unmatched openers / extra #endif must fail closed
        # (CODE-003). Every mutation runs through both real scanner CLIs
        # and both validating entries with exact exit/coverage assertions.
        baseline = ('const vault_placement '
                    '&vp(*env.level_vaults[map_index]);')
        mutations = {
            "raw-string-pseudo-directives": f'''void f() {{
    const char* s = R"(
some "quoted text
#ifdef FAKE
#endif
)";
    {baseline}
    (void)s;
}}
''',
            "line-spliced-comment-pseudo-directives": f'''void f() {{
    int x = 1; // \\
#ifdef FAKE
    // \\
#endif
    {baseline}
    (void)x;
}}
''',
            "nested-dead-window-over-baseline": f'''void f() {{
#if 0
#ifdef INNER
#endif
#endif
    {baseline}
}}
''',
            "unmatched-opener": '''void f() {
#ifdef REAL
    int x = 1;
}
''',
            "extra-endif": '''void f() {
    int x = 1;
#endif
}
''',
            # R3-CODE-003: '#IF'/'#ENDIF' are not directives (directive
            # names are case-sensitive); with no conditional recognized the
            # frozen baseline right after them must fail closed.
            "uppercase-directives": (
                f"void f() {{\n#IF 1\n    {baseline}\n#ENDIF\n}}\n"),
            # R3-CODE-002: '#elif 0' after '#if 0' is dead, so a nested
            # conditional inside it must not forge a switch point over the
            # frozen baseline.
            "elif-zero-dead-if-nested": (
                f"void f() {{\n#if 0\n#elif 0\n#ifdef INNER\n    {baseline}"
                f"\n#endif\n#endif\n    (void)0;\n}}\n"),
            # R3-CODE-001: a CRLF-spliced line comment stays open across
            # the splice, so fake directives on the continuation lines are
            # comment text and cannot forge a switch point.
            "crlf-spliced-comment-pseudo-directives": (
                b"void f() {\r\n    int x = 1; // \\\r\n"
                b"#ifdef FAKE\r\n    // \\\r\n#endif\r\n"
                + baseline.encode() + b"\r\n    (void)x;\r\n}\r\n"),
            # R3-CODE-001: a CRLF splice inside a raw-string prefix must be
            # assembled before prefix recognition, so '#ifdef FAKE'/'#endif'
            # inside the raw string stay opaque content.
            "crlf-spliced-raw-string-prefix": (
                b"void f() {\r\n    const char* s = R\\\r\n\"(\r\n"
                b"#ifdef FAKE\r\n#endif\r\n)\";\r\n"
                + baseline.encode() + b"\r\n    (void)s;\r\n}\r\n"),
            # R4-CODE-001: a branch after the chain was already taken
            # (#elif 0 after #if 1) is dead; its lines must never become
            # switch points, so the frozen baseline inside the nested
            # #ifdef in the dead elif branch fails closed. (The old code
            # kept lines 4-6 in the switch set and wrongly certified this
            # file clean.)
            "chain-dead-elif-baseline": (
                f"void f() {{\n#if 1\n#elif 0\n#ifdef INNER\n    "
                f"{baseline}\n#endif\n#endif\n    (void)0;\n}}\n"),
            # R4-CODE-002: a duplicate #else and a #elif after #else are
            # rejected by g++; the directive chain is unpairable and must
            # fail closed instead of computing switch points.
            "duplicate-else": (
                "void f() {\n#if 1\n#else\n#else\n    int x = 1;\n"
                "#endif\n}\n"),
            "elif-after-else": (
                "void f() {\n#if 1\n#else\n#elif 0\n    int x = 1;\n"
                "#endif\n}\n"),
            # R4-CODE-003: comments are replaced before the first condition
            # token is read, so '#if /* comment */ 0' is a dead branch and
            # the frozen baseline inside it fails closed. (The old code
            # read '/*' as the first token, treated the branch as live and
            # wrongly exempted the baseline.)
            "if-comment-zero-baseline": (
                f"void f() {{\n#if /* comment */ 0\n    {baseline}"
                f"\n#endif\n}}\n"),
            # R4-CODE-003: a multi-line block comment inside a directive
            # line is comment text; its interior lines cannot forge
            # directives.
            "if-comment-multiline-directives": (
                f"void f() {{\n#if 0 /* comment\n#ifdef FAKE\n#endif\n*/\n"
                f"    {baseline}\n#endif\n}}\n"),
            # R4-CODE-004: generic '}' / 'else' ERROR nodes at a switch
            # point are not the frozen baseline nodes (file content, line
            # and node text all differ), so they fail closed. (The old
            # line-text exemption wrongly certified both files clean.)
            "generic-brace-at-switch-point": (
                "void f() {\n#ifdef FOO\n}\n#endif\n}\n"),
            "generic-else-at-switch-point": (
                "void f() {\n#ifdef FOO\n    else\n#endif\n}\n"),
            # R4-CODE-005: bare CR is a phase-1 end-of-line indicator, so
            # directives are discovered with real physical line numbers;
            # the frozen baseline inside a live conditional of a bare-CR
            # file still fails closed (the file is not the frozen content).
            "bare-cr-live-conditional": (
                b"void f() {\x0d#ifdef REAL\x0d    " + baseline.encode()
                + b"\x0d#endif\x0d}\x0d"),
        }
        for name, content in mutations.items():
            for scanner in ("scan_string_concat.py", "scan_varargs_string.py"):
                with tempfile.TemporaryDirectory() as td:
                    source = Path(td) / "mutation.cc"
                    if isinstance(content, bytes):
                        source.write_bytes(content)
                    else:
                        source.write_text(content, encoding="utf-8")
                    for entry, args in (("files", ("--files", source)),
                                        ("dir", (td,))):
                        with self.subTest(mutation=name, scanner=scanner,
                                          entry=entry):
                            proc = self.run_scanner(
                                scanner, *args, "--format", "json",
                                "--require-parser")
                            self.assertEqual(2, proc.returncode, proc.stderr)
                            coverage = _coverage(json.loads(proc.stdout))
                            self.assertEqual(coverage["scanned"], 0)
                            self.assertEqual(len(coverage["failed"]), 1)
                            self.assertIn(str(source),
                                          coverage["failed"][0])

    def test_baseline_exemption_binds_frozen_directn_nodes(self):
        # R4-CODE-004: the frozen exemption is bound to the real
        # ERROR/missing nodes of the baseline directn.cc content. Only the
        # byte-identical baseline content parses as exempt; a generic '}'
        # / 'else' ERROR node at a switch point, the same line text at a
        # switch point in another file, and every mutation of the baseline
        # content (single-byte flip, line shift, truncation) fail closed.
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
        baseline_bytes = (ROOT / "crawl-ref" / "source" / "directn.cc")\
            .read_bytes()
        baseline_line = ('const vault_placement '
                         '&vp(*env.level_vaults[map_index]);')
        cases = [
            ("the exact frozen baseline content is fully exempt",
             baseline_bytes, False),
            ("generic '}' ERROR node at a switch point fails closed",
             b'''void f() {
#ifdef FOO
}
#endif
}
''',
             True),
            ("generic 'else' ERROR node at a switch point fails closed",
             b'''void f() {
#ifdef FOO
    else
#endif
}
''',
             True),
            ("frozen line text at a switch point in another file fails closed",
             f'''void f() {{
#ifdef FOO
    {baseline_line}
#endif
}}
'''.encode("utf-8"),
             True),
            ("single-byte mutation of the baseline fails closed",
             baseline_bytes[:50000] + b"X" + baseline_bytes[50001:],
             True),
            ("line-shifted copy of the baseline fails closed",
             b"int x = 1;\n" + baseline_bytes, True),
            ("truncated baseline fails closed",
             baseline_bytes[:3000], True),
        ]
        for name, source, expected in cases:
            with self.subTest(case=name):
                tree = parser.parse(source)
                self.assertEqual(
                    expected,
                    has_relevant_parse_error(tree.root_node, source),
                    name)

    def test_dead_preprocessor_blocks_are_subtracted_from_switch_points(self):
        # Issue #40 W1 blockers: dead #if 0 interiors must be subtracted
        # from the final switch-point set even when an enclosing live span,
        # a nested live span, or a preceding post-#endif window also covers
        # them; standalone dead blocks contribute no lines at all; a live
        # conditional nested inside a dead branch leaks neither body nor
        # post-#endif window (CODE-001); and #else reactivates the branch.
        # Exact expected sets, no vacuous subset checks (TEST-003).
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
             {3, 4, 6, 7, 9, 10, 11, 12}),  # dead interior line 5 subtracted
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
            ("nested live conditional inside #if 0 leaks no window",
             b'''void f() {
#if 0
#ifdef INNER
#endif
#endif
}
''',
             set()),  # CODE-001: inner body and post-#endif window suppressed
            ("dead block inside the post-#endif window of a live span",
             b'''void f() {
#ifdef FOO
#endif
#if 0
    int dead = 1;
#endif
}
''',
             {4, 6, 7}),  # live window minus the dead interior
            ("standalone dead block contributes no lines",
             b'''void f() {
#if 0
    int dead = 1;
#endif
}
''',
             set()),
            ("else branch of a dead #if 0 stays active",
             b'''void f() {
#if 0
    int dead = 1;
#else
    int live = 2;
#endif
}
''',
             {5}),  # only the reactivated else-branch body
        ]
        for name, source, expected in cases:
            with self.subTest(case=name):
                switch = _preprocessor_switch_lines(source)
                self.assertIsNotNone(switch, name)
                self.assertEqual(expected, switch, name)
                # No line inside any dead body may survive subtraction.
                dead_body = {line_no for line_no, text in enumerate(
                    source.split(b"\n"), start=1)
                    if b"int dead" in text}
                self.assertTrue(dead_body.isdisjoint(switch), switch)

    def test_elif_chains_track_dead_branches_exactly(self):
        # Issue #40 W1 R3-CODE-002: the whole #if/#elif/#else/#endif chain
        # is tracked. A #elif or #else after a branch already taken is dead
        # (even with a true #elif condition), '#elif 0' is dead, #else takes
        # the inverse of the chain, and a conditional nested inside a dead
        # branch contributes neither body nor post-#endif window. R4-CODE-001:
        # lines of branches dead because the chain was already taken are
        # subtracted from the switch set even when an enclosing live span
        # covers them. R4-CODE-002: a duplicate #else and a #elif after
        # #else are rejected (None), matching g++. Exact expected sets, no
        # vacuous subset checks (TEST-003).
        sys.path.insert(0, str(SCRIPTS))
        from i18n_shared import _preprocessor_switch_lines

        cases = [
            ("#if 0 -> #elif 0 -> nested is all dead",
             b'''void f() {
#if 0
#elif 0
#ifdef INNER
    int x = 1;
#endif
#endif
    int ok = 1;
}
''',
             set()),
            ("#if 1 -> #elif 0 -> nested: elif dead, nested suppressed",
             b'''void f() {
#if 1
#elif 0
#ifdef INNER
    int x = 1;
#endif
#endif
    int ok = 1;
}
''',
             # Chain-dead elif body (4-6) subtracted, not just un-added:
             # the switch set is only the post-#endif window (CODE-001).
             {8, 9, 10, 11}),
            ("#if 1 -> #else -> nested: else dead, nested suppressed",
             b'''void f() {
#if 1
#else
#ifdef INNER
    int x = 1;
#endif
#endif
    int ok = 1;
}
''',
             {8, 9, 10, 11}),
            ("#if 1 -> #elif 1 -> nested: taken #if kills the #elif",
             b'''void f() {
#if 1
#elif 1
#ifdef INNER
    int x = 1;
#endif
#endif
    int ok = 1;
}
''',
             {8, 9, 10, 11}),
            ("#if 0 -> #elif 1 -> nested stays live",
             b'''void f() {
#if 0
#elif 1
#ifdef INNER
    int x = 1;
#endif
    int live = 1;
#endif
    int ok = 1;
}
''',
             {4, 5, 6, 7, 8, 9, 10}),  # dead_if chain adds no outer window
            ("#if 0 -> #else -> nested: else is the chain inverse, live",
             b'''void f() {
#if 0
#else
#ifdef INNER
    int x = 1;
#endif
    int live = 1;
#endif
    int ok = 1;
}
''',
             {4, 5, 6, 7, 8, 9, 10}),
            ("#if 0 -> #elif 1 -> #else -> nested: else dead after taken elif",
             b'''void f() {
#if 0
#elif 1
#else
#ifdef INNER
    int x = 1;
#endif
#endif
    int ok = 1;
}
''',
             set()),
        ]
        for name, source, expected in cases:
            with self.subTest(case=name):
                switch = _preprocessor_switch_lines(source)
                self.assertIsNotNone(switch, name)
                self.assertEqual(expected, switch, name)
                # Suppression is encoded precisely by the exact-set
                # assertions above: a nested conditional inside a dead
                # branch adds nothing beyond the enclosing frame's branch
                # ranges.

        # R4-CODE-002: malformed chains are rejected by g++ and fail
        # closed (None) instead of computing switch points.
        for name, source in (
            ("duplicate #else",
             b'''void f() {
#if 1
#else
#else
    int x = 1;
#endif
}
'''),
            ("#elif after #else",
             b'''void f() {
#if 1
#else
#elif 0
    int x = 1;
#endif
}
'''),
            ("duplicate #else in a nested chain",
             b'''void f() {
#if 1
#ifdef A
#else
#else
#endif
#endif
}
'''),
            ("#elif after #else in a nested chain",
             b'''void f() {
#if 1
#ifdef A
#else
#elif 0
#endif
#endif
}
'''),
        ):
            with self.subTest(fail_closed=name):
                self.assertIsNone(_preprocessor_switch_lines(source), name)

    def test_crlf_splices_and_case_sensitive_directives(self):
        # Issue #40 W1 R3-CODE-001/003: line splicing must accept CRLF and
        # bare-CR new-lines and raw-string prefix/delimiter recognition must
        # run on the assembled logical line, so CRLF-spliced comments or raw
        # strings cannot forge directives and line numbers stay physical.
        # Directive names are case-sensitive: '#IF'/'#ENDIF' are not
        # directives. Exact expected sets (TEST-003).
        sys.path.insert(0, str(SCRIPTS))
        from i18n_shared import _preprocessor_switch_lines

        CRLF = b"\r\n"
        BS = b"\\"

        # Fake #ifdef/#endif kept inside line comments by CRLF splices.
        switch = _preprocessor_switch_lines(
            b"void f() {" + CRLF + b"    int x = 1; // " + BS + CRLF
            + b"#ifdef FAKE" + CRLF + b"    // " + BS + CRLF
            + b"#endif" + CRLF + b"    int ok = 1;" + CRLF + b"}" + CRLF)
        self.assertEqual(frozenset(), switch)

        # Fake #ifdef/#endif inside a raw string whose prefix is split by a
        # CRLF splice: the prefix is assembled before recognition.
        switch = _preprocessor_switch_lines(
            b"void f() {" + CRLF + b'    const char* s = R' + BS + CRLF
            + b'"(' + CRLF + b"#ifdef FAKE" + CRLF + b"#endif" + CRLF
            + b')";' + CRLF + b"    int ok = 1;" + CRLF + b"}" + CRLF)
        self.assertEqual(frozenset(), switch)

        # Fake #ifdef/#endif inside a raw string whose delimiter is split
        # by a CRLF splice: R"foo\<CRLF>( ... )foo" assembles to R"foo(...".
        switch = _preprocessor_switch_lines(
            b"void f() {" + CRLF + b'    const char* s = R"foo' + BS
            + CRLF + b'(' + CRLF + b"#ifdef FAKE" + CRLF + b"#endif" + CRLF
            + b')foo";' + CRLF + b"    int ok = 1;" + CRLF + b"}" + CRLF)
        self.assertEqual(frozenset(), switch)

        # Bare-CR splice in a line comment: '\\<CR>' is a splice too, so the
        # fake #ifdef stays inside the comment. Bare CR is also a phase-1
        # end-of-line indicator (R4-CODE-005), so the file is no longer one
        # logical line: the '#endif' on its own physical line is a real
        # directive with no opener, and the chain fails closed (None)
        # instead of silently producing no switch points.
        switch = _preprocessor_switch_lines(
            b"void f() {\x0d    int x = 1; // " + BS + b"\x0d"
            + b"#ifdef FAKE\x0d#endif\x0d    int ok = 1;\x0d}\x0d")
        self.assertIsNone(switch)

        # Uppercase '#IF 1'/'#ENDIF' are not directives (R3-CODE-003): the
        # real lowercase conditional still yields exactly its own body plus
        # its post-#endif window.
        switch = _preprocessor_switch_lines(
            b'''void f() {
#IF 1
    int x = 1;
#ENDIF
#ifdef REAL
    int y = 1;
#endif
    int ok = 1;
}
''')
        self.assertEqual(frozenset({6, 8, 9, 10, 11}), switch)

        # Real directives in a CRLF file still pair with physical line
        # numbers (the line_of mapping): body line 3 plus window 5-8.
        switch = _preprocessor_switch_lines(
            b"void f() {" + CRLF + b"#ifdef REAL" + CRLF + b"    int y = 1;"
            + CRLF + b"#endif" + CRLF + b"    int ok = 1;" + CRLF + b"}"
            + CRLF)
        self.assertEqual(frozenset({3, 5, 6, 7, 8}), switch)

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

        # Normal directives outside comments still pair correctly; the
        # chain-dead #else body of the inner '#if defined(B)' is subtracted
        # from the switch set (R4-CODE-001).
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
            frozenset({3, 4, 5, 7, 8, 9, 10, 11, 12}), switch)

        # Unmatched directives still fail closed.
        self.assertIsNone(_preprocessor_switch_lines(
            b'''void f() {
#ifdef REAL
    int ok = 1;
}
'''))

        # Fake #ifdef/#endif inside a raw string literal whose content
        # includes a standalone quote must not forge directives (CODE-002):
        # no conditional exists, so no line can be a switch point.
        switch = _preprocessor_switch_lines(
            b'''void f() {
    const char* s = R"(
some "quoted text
#ifdef FAKE
#endif
)";
    int ok = 1;
}
''')
        self.assertEqual(frozenset(), switch)

        # Fake directives kept inside line comments by backslash-newline
        # splicing must not forge directives either (CODE-002).
        switch = _preprocessor_switch_lines(
            b'''void f() {
    int x = 1; // \\
#ifdef FAKE
    // \\
#endif
    int ok = 1;
}
''')
        self.assertEqual(frozenset(), switch)

        # An extra #endif with no matching opener is unpairable (CODE-003).
        self.assertIsNone(_preprocessor_switch_lines(
            b'''void f() {
    int x = 1;
#endif
}
'''))

    def test_if_condition_comments_are_comment_replaced(self):
        # Issue #40 W1 R4-CODE-003: the first token of a #if/#elif
        # condition is read after phase-3 comment replacement, so
        # '#if /* comment */ 0' (and '#if/**/0', '#if 0 // comment') are
        # dead branches, and a multi-line block comment inside a directive
        # line is consumed wholesale — its interior newlines are comment
        # text and cannot forge directives. Exact expected sets.
        sys.path.insert(0, str(SCRIPTS))
        from i18n_shared import _preprocessor_switch_lines

        cases = [
            ("comment before the zero token is dead",
             b'''void f() {
#if /* comment */ 0
    int dead = 1;
#endif
}
''',
             frozenset()),
            ("adjacent comment without spaces is dead",
             b'''void f() {
#if/**/0
    int dead = 1;
#endif
}
''',
             frozenset()),
            ("zero before a trailing line comment is dead",
             b'''void f() {
#if 0 // trailing
    int dead = 1;
#endif
}
''',
             frozenset()),
            ("comment before the zero token spanning lines is dead",
             b'''void f() {
#if /* multi
line */ 0
    int dead = 1;
#endif
}
''',
             frozenset()),
            ("non-zero after a comment stays live",
             b'''void f() {
#if /* comment */ 1
    int live = 1;
#endif
}
''',
             frozenset({3, 5, 6, 7, 8})),
            ("multi-line block comment cannot forge directives",
             b'''void f() {
#if 0 /* comment
#ifdef FAKE
#endif
*/
    int dead = 1;
#endif
    int ok = 1;
}
''',
             frozenset()),
            ("elif zero after a comment is dead too",
             b'''void f() {
#if 1
#elif /* comment */ 0
    int dead = 1;
#endif
}
''',
             frozenset({6, 7, 8, 9})),
        ]
        for name, source, expected in cases:
            with self.subTest(case=name):
                switch = _preprocessor_switch_lines(source)
                self.assertIsNotNone(switch, name)
                self.assertEqual(expected, switch, name)

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
