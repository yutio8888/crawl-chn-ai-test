#!/usr/bin/env python3
"""Regression tests for literal and deferred i18n key extraction."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/i18n_extract.py"
SPEC = importlib.util.spec_from_file_location("i18n_extract", SCRIPT)
EXTRACT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(EXTRACT)


class DeferredMarkerTests(unittest.TestCase):
    def _extract_source(self, source: str):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sample.cc"
            path.write_text(source, encoding="utf-8")
            return [(key, ctx) for key, ctx, *_ in
                    EXTRACT.extract_keys_from_file(str(path))]

    def test_literal_markers_are_extracted_but_dynamic_t_is_not(self):
        keys = self._extract_source(
            'auto a = T_(runtime_key);\n'
            'auto b = N_("deferred key");\n'
            'auto c = NC_("attack verb", "open");\n')
        self.assertNotIn(("runtime_key", None), keys)
        self.assertIn(("deferred key", None), keys)
        self.assertIn(("open", "attack verb"), keys)

    def test_cpp_lexer_extracts_comment_annotations_but_not_string_text(self):
        keys = self._extract_source(
            '// N_("comment ghost"); T_("comment T ghost")\n'
            '/* NC_("ghost context", "block ghost"); '
            'C_("ctx", "block C ghost") */\n'
            'const char *ordinary = "N_(\\\"string ghost\\\") '
            'T_(\\\"string T ghost\\\")";\n'
            'const int character = \'N_("character ghost")\';\n'
            'const char *raw = R"tag(N_("raw ghost"); '
            'C_("ctx", "raw C ghost"))tag";\n'
            'auto a = N_("adjacent " "key");\n'
            'auto b = NC_("attack " "verb", "context " "key");\n')
        self.assertEqual([
            ("comment ghost", None),
            ("block ghost", "ghost context"),
            ("adjacent key", None),
            ("context key", "attack verb"),
        ], keys)

    def test_line_comment_escaped_newlines_hide_marker_calls(self):
        keys = self._extract_source(
            '// continued LF \\\n'
            'N_("LF ghost");\n'
            '// continued double LF \\\\\n'
            'N_("double LF ghost");\n'
            '// continued CRLF \\\r\n'
            'NC_("ctx", "CRLF ghost");\r\n'
            'auto visible = N_("visible key");\n')
        self.assertEqual([
            ("LF ghost", None),
            ("double LF ghost", None),
            ("CRLF ghost", "ctx"),
            ("visible key", None),
        ], keys)

    def test_raw_looking_comment_text_cannot_suppress_splicing(self):
        keys = self._extract_source(
            '// R"(fake \\\n'
            'N_("line raw ghost"))"\n'
            '/* R"(fake \\\n'
            'NC_("ctx", "block raw ghost"))" */\n'
            'const char *raw = R"tag(real raw \\\n'
            'N_("real raw ghost"))tag";\n'
            'auto visible = N_("visible after raw comments");\n')
        self.assertEqual([
            ("line raw ghost", None),
            ("block raw ghost", "ctx"),
            ("visible after raw comments", None),
        ], keys)

    def test_phase_two_splicing_forms_calls_contexts_and_string_keys(self):
        keys = self._extract_source(
            'auto token = N_\\\n("joined-token");\n'
            'auto identifier = N\\\n_("identifier-splice");\n'
            'auto context = NC_("attack" \\\n" verb", "open");\n'
            'auto string = N_("joined\\\nstring");\n')
        self.assertEqual([
            ("joined-token", None),
            ("identifier-splice", None),
            ("open", "attack verb"),
            ("joinedstring", None),
        ], keys)

    def test_nonliteral_deferred_marker_calls_fail_closed(self):
        for filename, prefix in (
                ("sample.cc", ""),
                ("i18n.h", "#define N_(en) helper(en)\n"
                           "#define NC_(ctx, en) helper(en)\n")):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root / filename).write_text(
                    prefix
                    + '#define DEFERRED_KEY "macro key"\n'
                    + 'const char *bad = N_(DEFERRED_KEY);\n',
                    encoding="utf-8")
                source_txt = root / "source.txt"
                source_txt.write_text(
                    "%%%%\nmacro key\n宏键\n", encoding="utf-8")
                proc = subprocess.run(
                    [sys.executable, str(SCRIPT), "validate", str(root),
                     "--source-txt", str(source_txt)],
                    text=True, capture_output=True, check=False)
            self.assertEqual(1, proc.returncode)
            self.assertIn("requires string-literal arguments", proc.stderr)

    def test_validate_cannot_pass_by_missing_an_adjacent_literal_key(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "sample.cc").write_text(
                'auto present = T_("present key");\n'
                'auto missing = N_("missing " "adjacent");\n'
                '// T_("comment ghost")\n', encoding="utf-8")
            source_txt = root / "source.txt"
            source_txt.write_text("%%%%\npresent key\n已存在\n", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "validate", str(root),
                 "--source-txt", str(source_txt)],
                text=True, capture_output=True, check=False)
        self.assertEqual(1, proc.returncode)
        self.assertIn("missing adjacent", proc.stdout)
        self.assertNotIn("comment ghost", proc.stdout)

    def test_nonliteral_comment_marker_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "sample.cc").write_text(
                '#define KEY "macro key"\n'
                '// N_(KEY)\n', encoding="utf-8")
            source_txt = root / "source.txt"
            source_txt.write_text(
                "%%%%\nmacro key\n宏键\n", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "validate", str(root),
                 "--source-txt", str(source_txt)],
                text=True, capture_output=True, check=False)
        self.assertEqual(1, proc.returncode)
        self.assertIn("requires string-literal arguments", proc.stderr)

    def test_validate_blocks_missing_deferred_key(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "sample.cc").write_text(
                'static const char *keys[] = { N_("missing deferred") };\n',
                encoding="utf-8")
            source_txt = root / "source.txt"
            source_txt.write_text("%%%%\npresent key\n已存在\n", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "validate", str(root),
                 "--source-txt", str(source_txt)],
                text=True, capture_output=True, check=False)
        self.assertEqual(1, proc.returncode)
        self.assertIn("missing deferred", proc.stdout)

    def test_issue_63_tables_expose_their_runtime_keys(self):
        expected = {
            ("It affects your AC (%d).", None),
            ("negative energy", "element"),
            ("armoured", None),
            (" It smells delicious!", None),
            ("Shadowslip", None),
            ("spit", "attack verb"),
            ("open", "attack verb"),
            ("like a pancake", None),
            ("kneecap", None),
        }
        actual = set()
        for relpath in ("crawl-ref/source/describe.cc",
                        "crawl-ref/source/ability.cc",
                        "crawl-ref/source/melee-attack.cc"):
            actual.update((key, ctx) for key, ctx, *_ in
                          EXTRACT.extract_keys_from_file(str(ROOT / relpath)))
        self.assertTrue(expected <= actual, expected - actual)

    def test_deferred_markers_reject_runtime_char_pointers(self):
        include_dir = ROOT / "crawl-ref/source"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            valid = root / "valid.cc"
            valid.write_text(
                '#include "i18n.h"\n'
                'constexpr const char *a = N_("literal");\n'
                'constexpr const char *b = NC_("ctx", "literal");\n',
                encoding="utf-8")
            invalid_pointer = root / "invalid_pointer.cc"
            invalid_pointer.write_text(
                '#include "i18n.h"\n'
                'const char *runtime_key = "runtime";\n'
                'const char *bad_pointer = N_(runtime_key);\n',
                encoding="utf-8")
            invalid_array = root / "invalid_array.cc"
            invalid_array.write_text(
                '#include "i18n.h"\n'
                'char runtime_array[] = "array";\n'
                'const char *bad_array = NC_("ctx", runtime_array);\n',
                encoding="utf-8")
            valid_proc = subprocess.run(
                ["c++", "-std=c++11", "-fsyntax-only", "-I", str(include_dir),
                 str(valid)], text=True, capture_output=True, check=False)
            invalid_pointer_proc = subprocess.run(
                ["c++", "-std=c++11", "-fsyntax-only", "-I", str(include_dir),
                 str(invalid_pointer)], text=True, capture_output=True, check=False)
            invalid_array_proc = subprocess.run(
                ["c++", "-std=c++11", "-fsyntax-only", "-I", str(include_dir),
                 str(invalid_array)], text=True, capture_output=True, check=False)
        self.assertEqual(0, valid_proc.returncode, valid_proc.stderr)
        self.assertNotEqual(0, invalid_pointer_proc.returncode)
        self.assertNotEqual(0, invalid_array_proc.returncode)


if __name__ == "__main__":
    unittest.main()
