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

    def test_annotation_functions_keep_body_findings_and_source_locations(self):
        prefixes = ("NORETURN void", "static void CALLBACK",
                    'extern "C" JNIEXPORT void JNICALL')
        bodies = {
            "scan_varargs_string.py": 'mprf("%s", std::string("unsafe value"));',
            "scan_string_concat.py": 'auto label = std::string("visible ") + value;',
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "annotations.cc"
            for prefix in prefixes:
                for scanner, body in bodies.items():
                    for unsafe in (False, True):
                        with self.subTest(prefix=prefix, scanner=scanner, unsafe=unsafe):
                            statement = body if unsafe else 'mprf("%s", "safe");'
                            path.write_text('// 中文 keeps byte offsets significant\n'
                                            + prefix + ' f() {\n  ' + statement
                                            + '\n}\n', encoding="utf-8")
                            proc = self.run_scanner(scanner, "--files", path,
                                                    "--format", "json", "--require-parser")
                            self.assertEqual(1 if unsafe else 0, proc.returncode, proc.stderr)
                            data = json.loads(proc.stdout)
                            self.assertEqual({"discovered": 1, "scanned": 1, "failed": []},
                                             _coverage(data))
                            if unsafe:
                                self.assertTrue(data["findings"])
                                self.assertTrue(all(f["line"] == 3 for f in data["findings"]))
                            else:
                                self.assertEqual([], data["findings"])

    def test_annotation_parse_preserves_bytes_except_known_declaration_tokens(self):
        sys.path.insert(0, str(SCRIPTS))
        from i18n_shared import parse_cpp_annotations
        import tree_sitter_cpp
        from tree_sitter import Language, Parser
        parser = Parser(Language(tree_sitter_cpp.language()))
        source = (b'// NORETURN void comment() {}\n'
                  b'#define NORETURN __attribute__((noreturn))\n'
                  b'const char* raw = R"x(\nNORETURN void literal() {}\n)x";\n'
                  b'int NORETURN = 1;\nvoid f(int CALLBACK);\n'
                  b'NORETURN void real();\n'
                  b'extern "C" JNIEXPORT void JNICALL real_jni() { mprf("%s", "ok"); }\n')
        expected = source.replace(b'NORETURN void real()', b'         void real()')
        expected = expected.replace(b'JNIEXPORT void JNICALL real_jni',
                                    b'          void         real_jni')
        tree = parse_cpp_annotations(parser, source)
        self.assertFalse(tree.root_node.has_error)
        self.assertEqual(len(source), tree.root_node.end_byte)
        self.assertEqual(expected, tree.root_node.text)

    def test_annotation_normalization_does_not_hide_unknown_or_broken_syntax(self):
        cases = (
            'UNKNOWN void f() {}',
            'NORETURN UNKNOWN void f() {}',
            'extern "C" JNIEXPORT void UNKNOWN f() {}',
            'JNIEXPORT void JNICALL f() {}',
            'static void UNKNOWN f() {}',
            'NORETURN void f() { mprf("%s", std::string("bad"); }',
            'NORETURN void f( { return; }',
        )
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "broken.cc"
            for source in cases:
                path.write_text(source + "\n", encoding="utf-8")
                for scanner in ("scan_varargs_string.py", "scan_string_concat.py"):
                    with self.subTest(source=source, scanner=scanner):
                        proc = self.run_scanner(scanner, "--files", path,
                                                "--format", "json", "--require-parser")
                        self.assertEqual(2, proc.returncode, proc.stderr)
                        self.assertIn("parse error", proc.stderr)
                        self.assertEqual(1, len(_coverage(json.loads(proc.stdout))["failed"]))

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
            source = Path(td) / "crawl-ref/source/directn.cc"
            source.parent.mkdir(parents=True)
            for broken in (False, True):
                source.write_bytes((b"int x = ;\n" if broken else b"")
                                   + directn.read_bytes())
                for scanner in ("scan_string_concat.py", "scan_varargs_string.py"):
                    for entry, args in (("files", ("--files", source)),
                                        ("dir", (source.parent,))):
                        with self.subTest(scanner=scanner, entry=entry, broken=broken):
                            proc = self.run_scanner(scanner, *args,
                                                    "--format", "json",
                                                    "--require-parser")
                            expected = 2 if broken else (
                                1 if scanner == "scan_string_concat.py" else 0)
                            self.assertEqual(expected, proc.returncode, proc.stderr)
                            coverage = _coverage(json.loads(proc.stdout))
                            self.assertEqual(coverage["scanned"], 0 if broken else 1)
                            self.assertEqual(len(coverage["failed"]), 1 if broken else 0)

    def test_preprocessor_mutations_fail_closed_both_entries(self):
        # End-to-end rejection cases from Issue #40 W1. Since Issue #120,
        # copied baseline fragments in mutation.cc cannot match the registered
        # path or full context. These cases therefore test CLI rejection, not
        # lexer window eligibility in isolation. The dedicated phase-2/window
        # tests below directly exercise fake directives, dead branches and
        # unmatched conditionals. Both real CLIs and both entries reject here.
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
            # copied fragment right after them is unregistered and rejected.
            "uppercase-directives": (
                f"void f() {{\n#IF 1\n    {baseline}\n#ENDIF\n}}\n"),
            # R3-CODE-002: '#elif 0' after '#if 0' is dead, so a nested
            # conditional inside it must not forge a switch point over the
            # copied baseline fragment (also unregistered at this path).
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
            # switch points. This copied fragment is also unregistered
            # at mutation.cc. (The old code
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
            # this unregistered copied fragment fails closed. (The old code
            # read '/*' as the first token, treated the branch as live and
            # wrongly exempted the copied fragment.)
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
            # point do not match the registered path and full context,
            # so they fail closed. (The old
            # line-text exemption wrongly certified both files clean.)
            "generic-brace-at-switch-point": (
                "void f() {\n#ifdef FOO\n}\n#endif\n}\n"),
            "generic-else-at-switch-point": (
                "void f() {\n#ifdef FOO\n    else\n#endif\n}\n"),
            # R4-CODE-005: bare CR is a phase-1 end-of-line indicator, so
            # directives are discovered with real physical line numbers;
            # the copied fragment inside a live conditional of a bare-CR
            # file still fails closed (unregistered path and context).
            "bare-cr-live-conditional": (
                b"void f() {\x0d#ifdef REAL\x0d    " + baseline.encode()
                + b"\x0d#endif\x0d}\x0d"),
            # R6-TEST-002: a backslash-newline inside a raw-string body
            # is literal text (no phase-2 splice), so the fake directives
            # on the continuation line cannot forge switch points for the
            # copied fragment, which is also unregistered at this path.
            "raw-body-backslash-eol-pseudo-directives": (
                b"void f() {\n    auto s = R\"_x(\n\\\n"
                b"#ifdef FAKE\n#endif\n)_x\";\n"
                + baseline.encode() + b"\n    (void)s;\n}\n"),
            # R6-TEST-002: an adjacent trailing comment is phase-3
            # comment replacement, so '#if 0/**/' and '#if 0//comment'
            # are dead branches (g++ accepts both); the copied fragment
            # inside them is also unregistered at this path and fails closed.
            "if-adjacent-trailing-block-comment-zero-baseline": (
                f"void f() {{\n#if 0/**/\n    {baseline}\n#endif\n}}\n"),
            "if-adjacent-trailing-line-comment-zero-baseline": (
                f"void f() {{\n#if 0//comment\n    {baseline}\n#endif\n}}\n"),
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

    def test_baseline_exemption_binds_directn_context(self):
        # Issue 120 replaces content hashes with path and local context.
        # Line shifts pass; generic tokens, incomplete context and real
        # syntax errors still fail closed.
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
            ("syntax error added to the baseline fails closed",
             b"int x = ;\n" + baseline_bytes,
             True),
            ("line-shifted copy of the baseline remains exempt",
             b"int x = 1;\n" + baseline_bytes, False),
            ("truncated baseline fails closed",
             baseline_bytes[:3000], True),
        ]
        for name, source, expected in cases:
            with self.subTest(case=name):
                tree = parser.parse(source)
                self.assertEqual(
                    expected,
                    has_relevant_parse_error(tree.root_node, source,
                                             "crawl-ref/source/directn.cc"),
                    name)

    def test_phase2_splice_advances_across_all_line_endings(self):
        sys.path.insert(0, str(SCRIPTS))
        from i18n_shared import _phase2_splice

        logical, line_of = _phase2_splice(b"a\nb\r\nc\rd")
        self.assertEqual(b"a\nb\nc\nd", logical)
        self.assertEqual([1, 1, 2, 2, 3, 3, 4], line_of)
        self.assertEqual(len(logical), len(line_of))

    def test_backslash_run_splice_precedes_escape_pairs(self):
        # I40-W1-R7-CODE-001: phase 2 makes only the LAST backslash of a
        # run of consecutive backslashes eligible for a splice when it is
        # immediately followed by a new-line, and the splice is deleted
        # before string parsing. g++/clang++ -fsyntax-only accept
        #   const char *s = "\\<LF>#ifdef FAKE";
        # as the single logical line "\#ifdef FAKE" (g++ -E -P output):
        # the trailing backslash+LF splice vanishes first, then the
        # surviving backslash escapes '#', so no '#ifdef' directive
        # exists. The old escape-pair branch consumed '\\' as a pair and
        # kept the LF, forging an unmatched '#ifdef' event and failing
        # both scanners on a file the compilers accept. Every expected
        # output below was compiler verified (g++ -E -P / -fsyntax-only
        # and clang++ -fsyntax-only, see
        # test_compiler_verified_fixtures_are_accepted).
        sys.path.insert(0, str(SCRIPTS))
        from i18n_shared import (_directive_events, _phase2_splice,
                                 _preprocessor_switch_lines)

        BS = b"\\"
        cases = [
            # Even backslash run + LF: the splice deletes the trailing
            # backslash + LF and the single survivor escapes '#'.
            ("even run + LF splices then escapes",
             b'const char *s = "' + BS + BS + b'\n#ifdef FAKE";',
             b'const char *s = "\\#ifdef FAKE";', []),
            # Odd run + LF: the whole run is spliced and the string
            # absorbs the directive text.
            ("odd run + LF splices entirely",
             b'const char *s = "' + BS + b'\n#ifdef FAKE";',
             b'const char *s = "#ifdef FAKE";', []),
            # Bare escape pair without EOL: no splice; the string closes
            # on its own line and the following directives are real.
            ("bare escape pair does not splice",
             b'const char *s = "' + BS + BS + b'";\n#ifdef FAKE\n#endif\n',
             b'const char *s = "\\\\";\n#ifdef FAKE\n#endif\n',
             [(b"ifdef", 2, False), (b"endif", 3, False)]),
            # Even run + LF + closing quote: the survivor escapes the
            # quote, so the literal stays open (g++: missing terminating
            # '"' character).
            ("even run + LF escapes the closing quote",
             b'const char *s = "' + BS + BS + b'\n";',
             b'const char *s = "\\";', []),
            # Odd run + LF + closing quote: an even survivor is a plain
            # escape pair and the quote closes.
            ("triple run + LF leaves an escape pair",
             b'const char *s = "' + BS + BS + BS + b'\n";',
             b'const char *s = "\\\\";', []),
            # Cascaded splices: the survivor escapes the byte after the
            # second splice (phase 2 deletes every backslash-newline
            # pair on each physical line before string parsing).
            ("cascaded splices still escape the quote",
             b'const char *s = "' + BS + BS + b'\n' + BS + b'\n";',
             b'const char *s = "\\";', []),
            # CRLF and bare-CR splices behave identically.
            ("even run + CRLF splices",
             b'const char *s = "' + BS + BS + b'\r\n#ifdef FAKE";',
             b'const char *s = "\\#ifdef FAKE";', []),
            ("even run + bare CR splices",
             b'const char *s = "' + BS + BS + b'\r#ifdef FAKE";',
             b'const char *s = "\\#ifdef FAKE";', []),
        ]
        for name, source, expected_logical, expected_events in cases:
            with self.subTest(case=name):
                logical, line_of = _phase2_splice(source)
                self.assertEqual(expected_logical, logical, name)
                self.assertEqual(len(logical), len(line_of), name)
                self.assertEqual(expected_events,
                                 list(_directive_events(source)), name)
        # The even-run fixture must not forge a switch set.
        self.assertEqual(
            frozenset(),
            _preprocessor_switch_lines(
                b'void f() {\n    const char *s = "' + BS + BS
                + b'\n#ifdef FAKE";\n    (void)s;\n}\n'))

        # CLI end-to-end through both entries: varargs must exit 0 (no
        # parse failure, no findings); concat must exit 1 driven by the
        # real COMPOUND_ASSIGN finding, never by the false directive
        # (old behavior: exit 2 parse failure on both scanners). The odd
        # and bare fixtures scan clean on both scanners.
        even_cli = (b"void f() {\n    const char *s = \"" + BS + BS
                    + b"\n#ifdef FAKE\";\n    std::string msg = "
                    b"\"even-bs\";\n    msg += \" tail\";\n"
                    b"    (void)s;\n    (void)msg;\n}\n")
        odd_cli = (b"void f() {\n    const char *s = \"" + BS
                   + b"\n#ifdef FAKE\";\n    int ok = 1;\n"
                   b"    (void)s;\n    (void)ok;\n}\n")
        bare_cli = (b'void f() {\n    const char *s = "' + BS + BS
                    + b'";\n#ifdef FAKE\n#endif\n    int ok = 1;\n'
                    b"    (void)s;\n    (void)ok;\n}\n")
        expected = {
            "scan_string_concat.py": {
                "even": (1, [("fixture.cc", 5, "COMPOUND_ASSIGN",
                              " tail")]),
                "odd": (0, []),
                "bare": (0, []),
            },
            "scan_varargs_string.py": {
                "even": (0, []),
                "odd": (0, []),
                "bare": (0, []),
            },
        }
        for name, content in (("even", even_cli), ("odd", odd_cli),
                              ("bare", bare_cli)):
            with tempfile.TemporaryDirectory() as td:
                root = Path(td) / "crawl-ref" / "source"
                root.mkdir(parents=True)
                source = root / "fixture.cc"
                source.write_bytes(content)
                for scanner, expectations in expected.items():
                    for entry, args in (("files", ("--files", source)),
                                        ("dir", (root,))):
                        with self.subTest(fixture=name, scanner=scanner,
                                          entry=entry):
                            proc = self.run_scanner(
                                scanner, *args, "--format", "json",
                                "--require-parser")
                            exit_code, findings = expectations[name]
                            self.assertEqual(exit_code, proc.returncode,
                                             proc.stderr)
                            data = json.loads(proc.stdout)
                            coverage = _coverage(data)
                            self.assertEqual(coverage["scanned"], 1)
                            self.assertEqual(coverage["failed"], [])
                            self.assertEqual(
                                findings, self._normalized_findings(data))

    def test_raw_string_body_backslash_eol_is_literal(self):
        # I40-W1-R7-TEST-002: phase 2 does not splice inside a raw-string
        # body; g++ keeps a backslash-newline there as literal text, so
        # the fake '#ifdef'/'#endif' on the following line stay raw
        # content and no directive is forged for any prefix (R/u8R/uR/
        # UR/LR) with a custom delimiter. Each fixture is compiler
        # verified (g++/clang++ -fsyntax-only exit 0, see
        # test_compiler_verified_fixtures_are_accepted); a splice inside
        # the body would turn '#ifdef FAKE' into an unmatched directive
        # and fail both scanners.
        sys.path.insert(0, str(SCRIPTS))
        from i18n_shared import (_directive_events, _phase2_splice,
                                 _preprocessor_switch_lines)

        fixtures = {}
        for prefix in (b"R", b"u8R", b"uR", b"UR", b"LR"):
            src = (b"void f() {\n    auto s = " + prefix
                   + b'"_x(\n\\\n#ifdef FAKE\n#endif\n)_x";\n'
                   + b"    int ok = 1;\n    (void)s;\n    (void)ok;\n}\n")
            fixtures[prefix.decode()] = src

        for prefix, src in fixtures.items():
            with self.subTest(prefix=prefix, level="helper"):
                logical, line_of = _phase2_splice(src)
                # The backslash + new-line inside the body survives as
                # literal text (the new-line is only normalized).
                self.assertIn(b"(\n\\\n#ifdef FAKE\n#endif\n", logical)
                self.assertEqual(len(logical), len(line_of))
                self.assertEqual([], list(_directive_events(src)))
                self.assertEqual(frozenset(),
                                 _preprocessor_switch_lines(src))

        for prefix, src in fixtures.items():
            with tempfile.TemporaryDirectory() as td:
                root = Path(td) / "crawl-ref" / "source"
                root.mkdir(parents=True)
                source = root / "raw_fixture.cc"
                source.write_bytes(src)
                for scanner in ("scan_string_concat.py",
                                "scan_varargs_string.py"):
                    for entry, args in (("files", ("--files", source)),
                                        ("dir", (root,))):
                        with self.subTest(prefix=prefix, scanner=scanner,
                                          entry=entry):
                            proc = self.run_scanner(
                                scanner, *args, "--format", "json",
                                "--require-parser")
                            self.assertEqual(0, proc.returncode,
                                             proc.stderr)
                            data = json.loads(proc.stdout)
                            coverage = _coverage(data)
                            self.assertEqual(coverage["scanned"], 1)
                            self.assertEqual(coverage["failed"], [])
                            self.assertEqual(
                                [], self._normalized_findings(data))

    def test_compiler_verified_fixtures_are_accepted(self):
        # I40-W1-R7-TEST-002: every new fixture in this module is
        # compiler verified. When g++ (or clang++ as fallback) is
        # installed, the fixtures below must pass -fsyntax-only exactly
        # as recorded in the review (g++ and clang++ both exit 0 for the
        # even/odd/bare backslash fixtures, the raw-body fixtures with
        # custom delimiters, and the adjacent trailing-comment forms);
        # without a compiler this assertion is skipped and the scanner
        # and helper assertions above still run.
        compiler = shutil.which("g++") or shutil.which("clang++")
        if compiler is None:
            self.skipTest("no C++ compiler (g++/clang++) available")
        BS = b"\\"
        fixtures = {
            "even backslash run + EOL": (
                b'const char *s = "' + BS + BS
                + b'\n#ifdef FAKE";\nint main() { return 0; }\n'),
            "odd backslash + EOL": (
                b'const char *s = "' + BS
                + b'\n#ifdef FAKE";\nint main() { return 0; }\n'),
            "bare backslash pair": (
                b'const char *s = "' + BS + BS
                + b'";\n#ifdef FAKE\n#endif\nint main() { return 0; }\n'),
            "raw body backslash-EOL": (
                b'void f() { auto s = R"_x(\n\\\n#ifdef FAKE\n#endif\n)_x"; }'
                b'\nint main() { return 0; }\n'),
            "#if 0/**/": (
                b"#if 0/**/\nint x = 1;\n#endif\n"
                b"int main() { return 0; }\n"),
            "#if 0//comment": (
                b"#if 0//comment\nint x = 1;\n#endif\n"
                b"int main() { return 0; }\n"),
            "#elif 0/**/": (
                b"#if 0\n#elif 0/**/\nint x = 1;\n#endif\n"
                b"int main() { return 0; }\n"),
            "#elif 0//comment": (
                b"#if 0\n#elif 0//comment\nint x = 1;\n#endif\n"
                b"int main() { return 0; }\n"),
        }
        for name, source in fixtures.items():
            with self.subTest(fixture=name):
                proc = subprocess.run(
                    [compiler, "-fsyntax-only", "-x", "c++", "-"],
                    input=source, capture_output=True)
                self.assertEqual(
                    0, proc.returncode,
                    f"{compiler} rejected {name}: "
                    f"{proc.stderr.decode(errors='replace')}")

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
            # I40-W1-R7-TEST-002: a comment adjacent to the token ends
            # it (phase 3 replaces the comment with one space), so
            # '#if 0/**/' and '#if 0//comment' read '0' and are dead
            # (g++ accepts both); the same holds for '#elif 0/**/' and
            # '#elif 0//comment' in a dead-#if chain (the elif is dead
            # because of the zero, not just because the chain was taken).
            ("adjacent trailing block comment after zero is dead",
             b'''void f() {
#if 0/**/
    int dead = 1;
#endif
}
''',
             frozenset()),
            ("adjacent trailing line comment after zero is dead",
             b'''void f() {
#if 0//comment
    int dead = 1;
#endif
}
''',
             frozenset()),
            ("adjacent trailing block comment after elif zero is dead",
             b'''void f() {
#if 0
#elif 0/**/
    int dead = 1;
#endif
}
''',
             frozenset()),
            ("adjacent trailing line comment after elif zero is dead",
             b'''void f() {
#if 0
#elif 0//comment
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

        # I40-W1-R7-TEST-002: CLI end-to-end through both entries. g++
        # accepts all four adjacent-comment forms (compiler verified in
        # test_compiler_verified_fixtures_are_accepted) and the real
        # scanners scan them clean; a misread dead branch would leave a
        # mis-paired directive chain and fail closed.
        clean = b'''void f() {
#if 0/**/
    int dead1 = 1;
#endif
#if 0//comment
    int dead2 = 2;
#endif
#if 0
#elif 0/**/
    int dead3 = 3;
#endif
#if 0
#elif 0//comment
    int dead4 = 4;
#endif
    int ok = 1;
}
'''
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "crawl-ref" / "source"
            root.mkdir(parents=True)
            source = root / "comment_fixture.cc"
            source.write_bytes(clean)
            for scanner in ("scan_string_concat.py",
                            "scan_varargs_string.py"):
                for entry, args in (("files", ("--files", source)),
                                    ("dir", (root,))):
                    with self.subTest(scanner=scanner, entry=entry,
                                      case="adjacent-trailing-comments"):
                        proc = self.run_scanner(
                            scanner, *args, "--format", "json",
                            "--require-parser")
                        self.assertEqual(0, proc.returncode, proc.stderr)
                        data = json.loads(proc.stdout)
                        coverage = _coverage(data)
                        self.assertEqual(coverage["scanned"], 1)
                        self.assertEqual(coverage["failed"], [])

    def test_directive_tail_honors_literal_state(self):
        # R5-CODE-001: the directive-line tail scan must track literal
        # state. '//' and '/*' inside string, char and raw-string
        # literals are literal text, not comments, so a legal '#define S
        # "/*"' ends at its own newline and the conditionals after it are
        # still discovered. The old bare-byte search truncated the
        # '#define' line at the literal '/*' and swallowed the rest of
        # the file, so the following '#ifdef'/'#endif' pair vanished and
        # the frozen-line scenario failed closed on a file g++ accepts
        # and tree-sitter has no error on.
        sys.path.insert(0, str(SCRIPTS))
        from i18n_shared import (_directive_events,
                                 _preprocessor_switch_lines)

        cases = [
            ("block-comment opener inside a string literal",
             b'#define S "/*"\n#ifdef REAL\n    int x = 1;\n#endif\n',
             [(b"ifdef", 2, False), (b"endif", 4, False)]),
            ("line-comment opener inside a string literal",
             b'#define S "//"\n#ifdef REAL\n    int x = 1;\n#endif\n',
             [(b"ifdef", 2, False), (b"endif", 4, False)]),
            ("comment opener inside a char literal",
             b"#define C '/*'\n#ifdef REAL\n    int x = 1;\n#endif\n",
             [(b"ifdef", 2, False), (b"endif", 4, False)]),
            ("comment openers inside a raw string",
             b'#define R R"(/* // )"\n#ifdef REAL\n    int x = 1;\n#endif\n',
             [(b"ifdef", 2, False), (b"endif", 4, False)]),
            ("real comment after a literal still truncates",
             b'#define S "x" /* tail */\n#ifdef REAL\n    int x = 1;\n'
             b'#endif\n',
             [(b"ifdef", 2, False), (b"endif", 4, False)]),
        ]
        for name, source, expected in cases:
            with self.subTest(case=name):
                self.assertEqual(expected, list(_directive_events(source)))

        # CLI-level clean companion: g++ accepts and tree-sitter reports
        # no error; the scanners must not fail closed because the lexer
        # truncated the '#define' line at the literal '/*' and orphaned
        # the '#endif' (old behavior: exit 2 on both entries).
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "mutation.cc"
            source.write_bytes(b'''#define S "/*"
#ifdef A
/* real comment */
#endif
int main() { return 0; }
''')
            for scanner in ("scan_string_concat.py",
                            "scan_varargs_string.py"):
                for entry, args in (("files", ("--files", source)),
                                    ("dir", (td,))):
                    with self.subTest(scanner=scanner, entry=entry,
                                      case="clean"):
                        proc = self.run_scanner(scanner, *args,
                                                "--format", "json",
                                                "--require-parser")
                        self.assertEqual(0, proc.returncode, proc.stderr)
                        coverage = _coverage(json.loads(proc.stdout))
                        self.assertEqual(coverage["scanned"], 1)
                        self.assertEqual(coverage["failed"], [])

        # Frozen-line scenario: '#define S "/*"' before a live conditional
        # containing the frozen baseline construct. The lexer must still
        # see the conditional (the baseline line is a switch point); the
        # scanners fail closed on the real, un-exempted tree-sitter ERROR
        # of the baseline construct, not because of a lexer misjudgment.
        baseline = ('const vault_placement '
                    '&vp(*env.level_vaults[map_index]);')
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "mutation.cc"
            source.write_text(
                f'#define S "/*"\n#ifdef REAL\n    {baseline}\n#endif\n',
                encoding="utf-8")
            switch = _preprocessor_switch_lines(source.read_bytes())
            self.assertIsNotNone(switch)
            self.assertIn(3, switch)
            for scanner in ("scan_string_concat.py",
                            "scan_varargs_string.py"):
                for entry, args in (("files", ("--files", source)),
                                    ("dir", (td,))):
                    with self.subTest(scanner=scanner, entry=entry,
                                      case="frozen"):
                        proc = self.run_scanner(scanner, *args,
                                                "--format", "json",
                                                "--require-parser")
                        self.assertEqual(2, proc.returncode, proc.stderr)
                        coverage = _coverage(json.loads(proc.stdout))
                        self.assertEqual(coverage["scanned"], 0)
                        self.assertEqual(len(coverage["failed"]), 1)
                        self.assertIn(str(source),
                                      coverage["failed"][0])

    def test_directive_leading_trivia_and_name_comments(self):
        # R5-CODE-002: directive-line recognition applies phase-3 comment
        # replacement. A leading comment before '#' is trivia, so
        # '/* leading */ #if 1' is a directive (the old code dropped
        # at_line_start after a closed block comment and missed it), and
        # comments between '#' and the name (or inside it) are replaced by
        # one space, so '#/**/if 1' and '# /* c */ if 1' are '#if 1' (the
        # old code read an empty keyword and missed them). A mid-line '#'
        # after real code is still not a directive even when a comment
        # precedes it.
        sys.path.insert(0, str(SCRIPTS))
        from i18n_shared import _directive_events, _preprocessor_switch_lines

        cases = [
            ("leading block comment before '#'",
             b'''/* leading trivia */ #if 1
    int x = 1;
#endif
''',
             frozenset({2, 4, 5, 6, 7})),
            ("multi-line leading comment before '#'",
             b'''/* leading
trivia */ #if 1
    int x = 1;
#endif
''',
             frozenset({3, 5, 6, 7, 8})),
            ("comment inside the directive name",
             b'''#/**/if 1
    int x = 1;
#endif
''',
             frozenset({2, 4, 5, 6, 7})),
            ("trivia and comment between '#' and the name",
             b'''# /* c */ if 1
    int x = 1;
#endif
''',
             frozenset({2, 4, 5, 6, 7})),
            ("dead condition recognized through the name comment",
             b'''#/**/if 0
    int dead = 1;
#endif
''',
             frozenset()),
        ]
        for name, source, expected in cases:
            with self.subTest(case=name):
                self.assertEqual(expected,
                                 _preprocessor_switch_lines(source))

        # A '#' after real code on the same line is not a directive, even
        # when a block comment sits between the code and the '#': phase-3
        # trivia does not make it the first token of the line.
        self.assertEqual(
            [(b"endif", 2, False)],
            list(_directive_events(b'int x = 1; /* c */ #if 1\n#endif\n')))

        # CLI-level: g++ accepts both sources and they scan clean through
        # the real scanners (old behavior: exit 2 on the orphaned
        # '#endif' because the '#if' was never recognized).
        clean_sources = [
            b'''/* leading trivia */ #if 1
    int ok = 1;
#endif
int main() { return 0; }
''',
            b'''#/**/if 1
    int ok = 1;
#endif
int main() { return 0; }
''',
        ]
        for source in clean_sources:
            with tempfile.TemporaryDirectory() as td:
                source_path = Path(td) / "mutation.cc"
                source_path.write_bytes(source)
                for scanner in ("scan_string_concat.py",
                                "scan_varargs_string.py"):
                    with self.subTest(scanner=scanner, entry="files"):
                        proc = self.run_scanner(
                            scanner, "--files", source_path,
                            "--format", "json", "--require-parser")
                        self.assertEqual(0, proc.returncode, proc.stderr)
                        coverage = _coverage(json.loads(proc.stdout))
                        self.assertEqual(coverage["scanned"], 1)
                        self.assertEqual(coverage["failed"], [])

    def test_line_ending_normalization_equivalence(self):
        # R5-CODE-003: the lexer and tree-sitter must share one line
        # mapping for every line-ending style. The lexer normalizes
        # CR/CRLF to LF in _phase2_splice(); tree-sitter consumes the
        # same normalized bytes (the exemption binding hashes the
        # normalized content, and node line numbers are resolved with the
        # same EOL-agnostic mapping), so a directn.cc copy stored with
        # CRLF or bare-CR endings behaves exactly like the LF original:
        # varargs exit 0, concat exit 1 with the six known findings.
        # tree-sitter itself cannot consume bare-CR bytes (its grammar
        # treats a bare CR as content, not an end of line), so the bare-CR
        # equivalence is asserted on the normalized input here. The
        # scanner entry points normalize before parsing, so the end-to-end
        # CLI equivalence for LF, CRLF AND bare-CR runs in
        # test_directn_line_endings_end_to_end_matrix (I40-W1-R7-TEST-002
        # closed the bare-CR CLI gap this comment used to document).
        sys.path.insert(0, str(SCRIPTS))
        from i18n_shared import (_normalize_eol, _preprocessor_switch_lines,
                                 has_relevant_parse_error)
        try:
            import tree_sitter_cpp as _tscpp
            from tree_sitter import Language as _Language
            from tree_sitter import Parser as _Parser
        except ImportError as exc:
            self.skipTest(f"tree-sitter not installed: {exc}")

        directn = ROOT / "crawl-ref" / "source" / "directn.cc"
        lf = directn.read_bytes()
        crlf = lf.replace(b"\n", b"\r\n")
        cr = lf.replace(b"\n", b"\r")

        # Phase-1 normalization is line-ending-style independent: the
        # three forms of the same file normalize to identical bytes.
        self.assertEqual(lf, _normalize_eol(lf))
        self.assertEqual(lf, _normalize_eol(crlf))
        self.assertEqual(lf, _normalize_eol(cr))

        # The lexer sees the same conditional events and switch lines for
        # every style (the frozen baseline lines stay switch points).
        switch_lf = _preprocessor_switch_lines(lf)
        self.assertIsNotNone(switch_lf)
        self.assertEqual(switch_lf, _preprocessor_switch_lines(crlf))
        self.assertEqual(switch_lf, _preprocessor_switch_lines(cr))
        self.assertIn(622, switch_lf)
        self.assertIn(3721, switch_lf)

        # tree-sitter agrees with the lexer on the same normalized input:
        # parsing _normalize_eol(cr) is byte-identical to parsing the LF
        # baseline, so the exemption outcome is the same and the frozen
        # baseline stays fully exempt regardless of the stored style.
        lang = _Language(_tscpp.language())
        parser = _Parser(lang)
        tree_lf = parser.parse(lf)
        tree_norm = parser.parse(_normalize_eol(cr))
        self.assertFalse(has_relevant_parse_error(tree_lf.root_node, lf, directn))
        self.assertEqual(
            has_relevant_parse_error(tree_lf.root_node, lf, directn),
            has_relevant_parse_error(tree_norm.root_node,
                                     _normalize_eol(cr), directn))

        # End-to-end through the real scanner CLIs: the CRLF-converted
        # copy of directn.cc must produce the same exit codes, coverage
        # and the same six known findings as the LF original (the
        # exemption binding is line-ending-agnostic, so the copy is not a
        # parse failure; old behavior: exit 2 on both scanners).
        expected = {
            "scan_string_concat.py": (1, self.DIRECTN_CONCAT_FINDINGS),
            "scan_varargs_string.py": (0, []),
        }
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "crawl-ref/source/directn.cc"
            source.parent.mkdir(parents=True)
            source.write_bytes(crlf)
            for scanner, (exit_code, findings) in expected.items():
                with self.subTest(scanner=scanner, entry="files"):
                    proc = self.run_scanner(scanner, "--files", source,
                                            "--format", "json",
                                            "--require-parser")
                    self.assertEqual(exit_code, proc.returncode,
                                     proc.stderr)
                    data = json.loads(proc.stdout)
                    coverage = _coverage(data)
                    self.assertEqual(coverage["scanned"], 1)
                    self.assertEqual(coverage["failed"], [])
                    self.assertEqual(findings,
                                     self._normalized_findings(data))

    def test_directn_line_endings_end_to_end_matrix(self):
        # I40-W1-R7-TEST-002: the directn.cc end-to-end equivalence runs
        # for every line-ending style (LF, CRLF, bare CR) through both
        # entry points (--files with parse validation and the
        # production-form crawl-ref/source directory entry). The scanners
        # apply phase-1 normalization before tree-sitter parses, so the
        # bare-CR copy behaves exactly like the LF original: varargs
        # exits 0 with zero findings, concat exits 1 driven by the six
        # known findings (never by a parse failure), with exact coverage
        # and normalized findings on every combination.
        directn = ROOT / "crawl-ref" / "source" / "directn.cc"
        lf = directn.read_bytes()
        variants = {
            "LF": lf,
            "CRLF": lf.replace(b"\n", b"\r\n"),
            "bare-CR": lf.replace(b"\n", b"\r"),
        }
        expected = {
            "scan_string_concat.py": (1, self.DIRECTN_CONCAT_FINDINGS),
            "scan_varargs_string.py": (0, []),
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "crawl-ref" / "source"
            root.mkdir(parents=True)
            for style, content in variants.items():
                source = root / "directn.cc"
                source.write_bytes(content)
                for scanner, (exit_code, findings) in expected.items():
                    for entry, args in (("files", ("--files", source)),
                                        ("dir", (root,))):
                        with self.subTest(style=style, scanner=scanner,
                                          entry=entry):
                            proc = self.run_scanner(
                                scanner, *args, "--format", "json",
                                "--require-parser")
                            self.assertEqual(exit_code, proc.returncode,
                                             proc.stderr)
                            data = json.loads(proc.stdout)
                            coverage = _coverage(data)
                            self.assertEqual(coverage["scanned"], 1)
                            self.assertEqual(coverage["failed"], [])
                            self.assertEqual(
                                findings, self._normalized_findings(data))

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
