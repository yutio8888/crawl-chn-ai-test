#!/usr/bin/env python3
"""Issue 120: exercise real scanner entries, patterns and macro adapters."""
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / '.claude/scripts'
sys.path.insert(0, str(SCRIPTS))
from i18n_shared import (parse_cpp_annotations, _matches_preprocessor_node,
                         _directive_events, preprocess_cpp,
                         _extract_cpp_preprocessed, parse_preprocessed_cpp,
                         CppCompilationDatabase)
try:
    from tree_sitter import Language, Parser
    import tree_sitter_cpp
    PARSER_IMPORT_ERROR = None
except ImportError as exc:
    PARSER_IMPORT_ERROR = str(exc)


class PreprocessorPatternTests(unittest.TestCase):
    def setUp(self):
        if PARSER_IMPORT_ERROR is not None:
            self.skipTest(f"tree-sitter not installed: {PARSER_IMPORT_ERROR}")

    def check_cli(self, path, success, directory=False):
        for scanner in ('scan_varargs_string.py', 'scan_string_concat.py'):
            args = [str(path.parent)] if directory else ['--files', str(path)]
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / scanner), *args,
                 '--format', 'json', '--require-parser'],
                capture_output=True, text=True)
            data = json.loads(result.stdout)
            coverage = data.get('coverage', data.get('meta', {}).get('coverage'))
            with self.subTest(scanner=scanner, directory=directory):
                if success:
                    # Concat findings are advisory; they must not be confused
                    # with infrastructure/parse failures (exit 2).
                    self.assertIn(result.returncode, (0, 1), result.stderr)
                    self.assertEqual(coverage, {'discovered': 1, 'scanned': 1,
                                                'failed': []})
                else:
                    self.assertEqual(result.returncode, 2, result.stdout)
                    self.assertEqual(coverage['scanned'], 0)
                    self.assertEqual(len(coverage['failed']), 1)

    def test_three_files_and_line_shifts_through_both_entries(self):
        for name in ('directn.cc', 'main.cc', 'menu.cc'):
            original = (ROOT / 'crawl-ref/source' / name).read_bytes()
            variants = {
                'baseline': original,
                'insert-lines': b'// unrelated line\n' * 7 + original,
                'delete-lines': original.replace(b'\n\n', b'\n', 5),
            }
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / 'crawl-ref/source' / name
                path.parent.mkdir(parents=True)
                for label, source in variants.items():
                    with self.subTest(file=name, variant=label):
                        path.write_bytes(source)
                        self.check_cli(path, True)
                        self.check_cli(path, True, directory=True)

    def test_unmatched_patterns_and_outside_errors_fail_closed(self):
        for name in ('directn.cc', 'main.cc', 'menu.cc'):
            original = (ROOT / 'crawl-ref/source' / name).read_bytes()
            valid = b'void probe() { int value = 1; }\n'
            broken = valid.replace(b'1;', b'1')
            variants = {
                'outside-window': (original + b'\n' * 8 + valid,
                                   original + b'\n' * 8 + broken),
                'inside-window-unregistered': (
                    b'#ifdef LOCAL_PROBE\n' + valid + b'#endif\n' + original,
                    b'#ifdef LOCAL_PROBE\n' + broken + b'#endif\n' + original),
            }
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / 'crawl-ref/source' / name
                path.parent.mkdir(parents=True)
                for label, (good, bad) in variants.items():
                    with self.subTest(file=name, variant=label):
                        path.write_bytes(good)
                        self.check_cli(path, True)
                        path.write_bytes(bad)
                        self.check_cli(path, False)
                        self.check_cli(path, False, directory=True)
                # Identical bytes and basename at an unrelated path are not
                # the registered repository-relative identity.
                wrong = Path(td) / name
                wrong.write_bytes(original)
                self.check_cli(wrong, False)

    def test_missing_semicolon_in_conditional_source(self):
        original = (ROOT / 'crawl-ref/source/directn.cc').read_bytes()
        # The equivalent reference initializer no longer needs the historical
        # * / . recovery context. Retain its conditional and remove only ';'.
        line = b'const vault_placement &vp = *env.level_vaults[map_index];'
        self.assertEqual(original.count(line), 1)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'crawl-ref/source/directn.cc'
            path.parent.mkdir(parents=True)
            for broken in (False, True):
                path.write_bytes(original.replace(line, line[:-1]) if broken else original)
                for directory in (False, True):
                    with self.subTest(broken=broken, directory=directory):
                        self.check_cli(path, not broken, directory=directory)

    def test_issue6_sources_and_negative_mutations_through_both_entries(self):
        # These production constructs were formerly unparseable in changed
        # scope: split conditionals, reference initializers and ON_UNWIND.
        # Source-side equivalent statements avoid adding recovery exemptions.
        mutations = {
            'item-name.cc': (b'CASE_REMOVED_POTIONS(item.sub_type);',
                             b'CASE_REMOVED_POTIONS(item.sub_type)'),
            'items.cc': (b'int& ob = *obj;', b'int& ob = *obj'),
            'melee-attack.cc': (
                b'set_artefact_name(*mutable_wpn, saved_gyre_name);',
                b'set_artefact_name(*mutable_wpn, saved_gyre_name)'),
            'lang-fake.cc': (b'"!" LETTERS', b'"!" LETTERSX'),
        }
        for name, (good, bad) in mutations.items():
            original = (ROOT / 'crawl-ref/source' / name).read_bytes()
            self.assertIn(good, original)
            with tempfile.TemporaryDirectory() as td:
                # Standalone directory scans, like --files changed scope,
                # use strict parse coverage. The historical full production
                # root mode has a different, permissive parse contract.
                path = Path(td) / name
                for label, source, success in (
                    ('baseline', original, True),
                    ('line-shift', b'// unrelated line\n' * 7 + original, True),
                    ('malformed', original.replace(good, bad, 1), False),
                ):
                    path.write_bytes(source)
                    for directory in (False, True):
                        with self.subTest(file=name, variant=label,
                                          directory=directory):
                            self.check_cli(path, success, directory=directory)

    def test_issue6_cleanup_lambda_body_remains_scanned(self):
        original = (ROOT / 'crawl-ref/source/melee-attack.cc').read_bytes()
        call = b'set_artefact_name(*mutable_wpn, saved_gyre_name);'
        self.assertEqual(original.count(call), 1)
        hazard = b'mprf("%s", std::string("issue6 hazard"));'
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'melee-attack.cc'
            path.write_bytes(original.replace(call, hazard))
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / 'scan_varargs_string.py'),
                 '--files', str(path), '--format', 'json', '--require-parser'],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data['coverage'], {'discovered': 1, 'scanned': 1,
                                                 'failed': []})
            self.assertTrue(any(f['risk'] == 'HIGH'
                                and f['arg'] == 'std::string("issue6 hazard")'
                                for f in data['findings']))

    def test_directive_after_context_is_outside_context(self):
        source = b'void f() {\n    else\n#ifdef FLAG\n#endif\n}\n'
        parser = Parser(Language(tree_sitter_cpp.language()))
        tree = parser.parse(source)
        stack = [tree.root_node]
        errors = []
        while stack:
            node = stack.pop()
            if node.type == 'ERROR' and node.text == b'else':
                errors.append(node)
            stack.extend(node.children)
        self.assertEqual(len(errors), 1)
        self.assertFalse(_matches_preprocessor_node(
            errors[0], source, [('ERROR', b'else', b'    else\n')],
            frozenset(), tuple(_directive_events(source))))

    def test_each_macro_and_missing_semicolon_at_same_location(self):
        cases = (
            b'NORETURN static void f() { int x = 1; }\n',
            b'static BOOL WINAPI f() { int x = 1; }\n',
            b'void f() { auto x = "prefix" CRAWL "suffix"; }\n',
            b'void f() { auto x = "!" LETTERS; }\n',
            b'void f() { int x = va_arg(args, int); }\n',
        )
        parser = Parser(Language(tree_sitter_cpp.language()))
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'macros.cc'
            for source in cases:
                with self.subTest(source=source):
                    tree = parse_cpp_annotations(parser, source)
                    self.assertFalse(tree.root_node.has_error)
                    self.assertEqual(len(source), tree.root_node.end_byte)
                    self.assertEqual([i for i, b in enumerate(source) if b == 10],
                                     [i + tree.root_node.start_byte
                                      for i, b in enumerate(tree.root_node.text) if b == 10])
                    path.write_bytes(source)
                    self.check_cli(path, True)
                    path.write_bytes(source.replace(b';', b'', 1))
                    self.check_cli(path, False)

    def test_macro_names_trivia_and_expression_findings_are_preserved(self):
        parser = Parser(Language(tree_sitter_cpp.language()))
        source = (b'// "prefix" CRAWL va_arg(args, int)\n'
                  b'#define TEXT "prefix" CRAWL\n'
                  b'#define ARG va_arg(args, int)\n'
                  b'// "prefix" LETTERS\n'
                  b'#define TEXT2 "prefix" LETTERS\n'
                  b'auto letters_raw = R"x("prefix" LETTERS)x";\n'
                  b'int LETTERS = 0;\n'
                  b'auto winapi_raw = R"x(static BOOL WINAPI f())x";\n'
                  b'int WINAPI = 0;\n'
                  b'auto raw = R"x("prefix" CRAWL va_arg(args, int))x";\n'
                  b'int CRAWL = 0;\n')
        self.assertEqual(source, parse_cpp_annotations(parser, source).root_node.text)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'macros.cc'
            for bad in (b'void f() { auto x = "a" CRAWLX "b"; }',
                        b'void f() { auto x = "!" LETTERSX; }',
                        b'void f() { int x = va_arg_other(args, int); }',
                        b'void f() { int x = va_arg(args +, int); }',
                        b'NORETURN static void f() { int x = ; }'):
                path.write_bytes(bad)
                self.check_cli(path, False)
            # The first operand must remain an AST expression: normalizing
            # the macro cannot erase varargs hazards nested inside it.
            path.write_bytes(b'void f() { auto x = va_arg(mprf("%s", std::string("bad")), int); }')
            result = subprocess.run([sys.executable, str(SCRIPTS / 'scan_varargs_string.py'),
                                     '--files', str(path), '--format', 'json'],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)['summary']['HIGH'], 1)

    def test_winapi_annotation_preserves_signature_body_and_risks(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'winapi.cc'
            for source in (
                    b'static BOOL WINAPI f(int x,) { return 1; }',
                    b'static BOOL WINAPI f() { return ; int x = ; }',
                    b'static BOOL WINAPI f() { int x = 1 }'):
                path.write_bytes(source)
                self.check_cli(path, False)
            path.write_bytes(b'static BOOL WINAPI f() { mprf("%s", std::string("bad")); return 1; }')
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / 'scan_varargs_string.py'),
                 '--files', str(path), '--format', 'json', '--require-parser'],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)['summary']['HIGH'], 1)


class PreprocessorOutputTests(unittest.TestCase):
    def setUp(self):
        self.compiler = shutil.which('clang++')
        if self.compiler is None:
            self.skipTest('clang++ is not installed')

    def test_diagnostic_pragmas_between_if_and_body_preserve_strict_scans(self):
        source = ('#define SECTION _Pragma("clang diagnostic push") '
                  'if (bool section = true) _Pragma("clang diagnostic pop")\n'
                  'void f() {\n'
                  '  SECTION { mprf("%s", std::string("bad")); }\n'
                  '}\n'
                  'void mpr(const formatted_string &) = delete;\n')
        parser = Parser(Language(tree_sitter_cpp.language()))
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'section.cc'
            path.write_text(source)
            expanded = preprocess_cpp(path, self.compiler)
            tree = parse_preprocessed_cpp(parser, expanded.source,
                                          preprocessed=expanded, filepath=path)
            self.assertFalse(tree.root_node.has_error)
            self.assertEqual(len(expanded.source), tree.root_node.end_byte)
            self.assertEqual(
                [i for i in range(tree.root_node.start_byte, tree.root_node.end_byte)
                 if expanded.source[i] == 10],
                [tree.root_node.start_byte + i
                 for i, b in enumerate(tree.root_node.text) if b == 10])
            db = Path(td) / 'commands.json'
            db.write_text(json.dumps([{'directory': td, 'file': str(path),
                                      'arguments': [self.compiler, '-c', str(path)]}]))
            for scanner in ('scan_varargs_string.py', 'scan_string_concat.py',
                            'scan_i18n_lifetime.py'):
                result = subprocess.run(
                    [sys.executable, str(SCRIPTS / scanner), '--files', str(path),
                     '--compile-commands', str(db), '--format', 'json'],
                    capture_output=True, text=True)
                with self.subTest(scanner=scanner):
                    self.assertIn(result.returncode, (0, 1), result.stderr)
                    data = json.loads(result.stdout)
                    coverage = data.get('coverage', data.get('meta', {}).get('coverage'))
                    self.assertEqual(coverage['scanned'], 1)
                    self.assertEqual(coverage['failed'], [])
                    if scanner == 'scan_varargs_string.py':
                        self.assertTrue(any(f['risk'] == 'HIGH' and f['line'] == 3
                                            for f in data['findings']))
                path.write_text(source.replace('std::string("bad"));',
                                               'std::string("bad"))'))
                rejected = subprocess.run(
                    [sys.executable, str(SCRIPTS / scanner), '--files', str(path),
                     '--compile-commands', str(db), '--format', 'json'],
                    capture_output=True, text=True)
                self.assertEqual(rejected.returncode, 2, rejected.stderr)
                path.write_text(source)
            # Literal text and non-diagnostic directives must remain intact.
            raw = b'void f(){ auto s = R"x(\n#pragma clang diagnostic pop\n)x"; }\n'
            self.assertEqual(raw, parse_preprocessed_cpp(parser, raw).root_node.text)
            packed = b'void f(){ if(true)\n#pragma pack(push,1)\n{ int x=1; } }\n'
            self.assertEqual(packed, parse_preprocessed_cpp(parser, packed).root_node.text)

    def test_real_macro_expansion_configurations_and_original_lines(self):
        source = '''#include "calls.h"
void f() {
  auto raw = R"raw(
# 999 "pretend.h"
)raw";
#ifdef USE_TILE_LOCAL
  CALL(std::string("tiles"));
#else
  CALL(std::string("console"));
#endif
  static const char *p = LOOKUP("cached");
}
'''
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'sample.cc'
            path.write_text(source)
            (path.parent / 'calls.h').write_text(
                '#define CALL(x) mprf_p(C_("context", "%s"), x)\n'
                '#define LOOKUP(x) C_("context", x)\n')
            for defines, selected in (((), 'console'), (('-DUSE_TILE_LOCAL',), 'tiles')):
                with self.subTest(configuration=selected):
                    result = preprocess_cpp(path, self.compiler, defines)
                    text = result.source.decode()
                    expanded = text.split('\n')
                    call_row = next(i for i, line in enumerate(expanded)
                                    if 'mprf_p(' in line)
                    self.assertIn('std::string("' + selected + '")', expanded[call_row])
                    self.assertIn('CALL(', source.splitlines()[result.original_line(call_row) - 1])
                    lookup_row = next(i for i, line in enumerate(expanded)
                                      if 'static const char' in line)
                    self.assertIn('LOOKUP(', source.splitlines()[result.original_line(lookup_row) - 1])
                    self.assertIn('# 999 "pretend.h"', text)
                    self.assertNotIn('#define CALL', text)

    def test_source_authored_line_markers_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'sample.cc'
            for marker in ('#line 1 "other.h"', '# 1 "other.h"',
                           '\ufeff#line 999', '\f#line 999', '\v#line 999',
                           '#\fline 999', '#\vline 999',
                           '#li\\\nne 1 "other.h"', '#/**/line 1 "other.h"'):
                with self.subTest(marker=marker):
                    path.write_text(marker + '\nvoid f() { mprf("%s", std::string("bad")); }\n')
                    with self.assertRaisesRegex(ValueError, 'source-authored'):
                        preprocess_cpp(path, self.compiler)
            path.write_text('\ufeffvoid f() {}\n')
            expanded = preprocess_cpp(path, self.compiler)
            row = next(i for i, line in enumerate(expanded.source.decode().split('\n'))
                       if 'void f() {}' in line)
            self.assertEqual(expanded.original_line(row), 1)
            (path.parent / 'included.h').write_text('#line 1 "other.h"\nvoid g() {}\n')
            path.write_text('#include "included.h"\nvoid f() {}\n')
            with self.assertRaisesRegex(ValueError, 'filename change'):
                preprocess_cpp(path, self.compiler)

    def test_missing_inputs_and_bad_preprocessing_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'sample.cc'
            with self.assertRaises(OSError):
                preprocess_cpp(path, self.compiler)
            for source in ('#include "missing-issue120.h"\n', '#ifdef X\n',
                           '#define X(a) a\nvoid f() { X(1; }\n'):
                with self.subTest(source=source):
                    path.write_text(source)
                    with self.assertRaisesRegex(ValueError, 'preprocessor failed'):
                        preprocess_cpp(path, self.compiler)
            path.write_text('void f() {}\n')
            with self.assertRaisesRegex(ValueError, 'cannot preprocess'):
                preprocess_cpp(path, str(path.parent / 'missing' / 'clang++'))
            with self.assertRaisesRegex(ValueError, 'target provenance'):
                _extract_cpp_preprocessed(path, b'void f() {}\n')

    def test_expanded_va_arg_preserves_first_operand_and_blocks_invalid_types(self):
        if PARSER_IMPORT_ERROR is not None:
            self.skipTest(f'tree-sitter not installed: {PARSER_IMPORT_ERROR}')
        import scan_varargs_string

        parser = Parser(Language(tree_sitter_cpp.language()))
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'sample.cc'
            path.write_text('#include <cstdarg>\nvoid f(){ int x = '
                            'va_arg(mprf("%s", std::string("nested")), int); }\n')
            expanded = preprocess_cpp(path, self.compiler)
            self.assertIn(b'__builtin_va_arg', expanded.source)
            tree = parse_preprocessed_cpp(parser, expanded.source)
            self.assertFalse(tree.root_node.has_error)
            self.assertEqual(tree.root_node.end_byte, len(expanded.source))
            findings = []
            scan_varargs_string._walk(tree.root_node, expanded.source, findings, [])
            self.assertTrue(any(f['callee'] == 'mprf' and f['risk'] == 'HIGH'
                                and f['arg'] == 'std::string("nested")'
                                for f in findings))
            for arguments in ('ap +, int', 'ap, int +', 'ap, int (*)(int)',
                              'ap, "not a type"', 'ap, extra, int'):
                with self.subTest(arguments=arguments):
                    source = ('void f(){ int x = __builtin_va_arg(' + arguments + '); }').encode()
                    with self.assertRaises(ValueError):
                        parse_preprocessed_cpp(parser, source)
            missing = b'void f(){ int x = __builtin_va_arg(ap, int) }'
            self.assertTrue(parse_preprocessed_cpp(parser, missing).root_node.has_error)

    def test_deleted_free_function_adapter_preserves_signature_and_risk_nodes(self):
        if PARSER_IMPORT_ERROR is not None:
            self.skipTest(f'tree-sitter not installed: {PARSER_IMPORT_ERROR}')
        parser = Parser(Language(tree_sitter_cpp.language()))
        for declaration in (b'void mpr(const formatted_string &) = delete;',
                            b'void mpr(const formatted_string &named) = delete;',
                            b'void mpr(const formatted_string &)\n =\n delete;'):
            source = declaration + b'\nvoid f(){mprf("%s", std::string("bad"));}\n'
            tree = parse_preprocessed_cpp(parser, source)
            self.assertFalse(tree.root_node.has_error)
            self.assertEqual(tree.root_node.end_byte, len(source))
            self.assertEqual(tree.root_node.end_point[0], source.count(b'\n'))
            self.assertIn('function_declarator', str(tree.root_node))
            self.assertIn('call_expression', str(tree.root_node))
        for invalid in (b'void mpr(const formatted_string &) = delete',
                        b'void mpr(const formatted_string &) = delete reason;',
                        b'void mpr(const formatted_string &) = delete[] p;',
                        b'void mpr(const formatted_string &,) = delete;',
                        b'void mpr(const formatted_string &) = delete; int x = ;'):
            with self.subTest(source=invalid):
                try:
                    tree = parse_preprocessed_cpp(parser, invalid)
                except ValueError:
                    continue
                self.assertTrue(tree.root_node.has_error)

    def test_utf8_and_space_paths_use_real_clang_filename_decoding(self):
        with tempfile.TemporaryDirectory(prefix='issue120-路径 space-') as td:
            path = Path(td) / '测试 file.cc'
            path.write_text('void f(){ mprf("%s", std::string("bad")); }\n')
            expanded = preprocess_cpp(path, self.compiler)
            self.assertIn(b'mprf(', expanded.source)
            row = next(i for i, line in enumerate(expanded.source.split(b'\n')) if b'mprf(' in line)
            self.assertEqual(expanded.original_line(row), 1)
            with self.assertRaisesRegex(ValueError, 'clang driver'):
                preprocess_cpp(path, 'g++')


class ConfiguredScannerTests(unittest.TestCase):
    def setUp(self):
        if PARSER_IMPORT_ERROR is not None:
            self.skipTest(f'tree-sitter not installed: {PARSER_IMPORT_ERROR}')
        self.compiler = shutil.which('clang++')
        if self.compiler is None:
            self.skipTest('clang++ is not installed')

    def database(self, root, name, files, flags=()):
        path = root / (name + '.json')
        path.write_text(json.dumps([
            {'directory': str(root), 'file': file,
             'arguments': [self.compiler, '-std=c++11', *flags,
                           '-c', file, '-o', file + '.o']}
            for file in files]))
        return path

    def run_cli(self, scanner, source, databases):
        args = [sys.executable, str(SCRIPTS / scanner), '--files', str(source),
                '--format', 'json', '--require-parser']
        for database in databases:
            args.extend(('--compile-commands', str(database)))
        return subprocess.run(args, capture_output=True, text=True)

    def test_macro_findings_are_visible_through_all_three_real_clis(self):
        source = '''#include "calls.h"
void f() {
  string text;
  SHOW(std::string("bad"));
  APPEND("bare display");
  static const char *cache = LOOKUP("cached");
}
'''
        with tempfile.TemporaryDirectory() as td:
            # Reproduce macOS's /var -> /private/var canonicalization on Linux.
            physical_root = Path(td).resolve() / 'physical'
            physical_root.mkdir()
            root = Path(td).resolve() / 'linked'
            root.symlink_to(physical_root, target_is_directory=True)
            target = root / 'sample.cc'
            target.write_text(source)
            (root / 'calls.h').write_text(
                '#define SHOW(x) mprf_p(C_("context %s", "%2$s"), "safe", x)\n'
                '#define APPEND(x) text += x\n'
                '#define LOOKUP(x) C_("context", x)\n')
            database = self.database(root, 'console', ('sample.cc', 'calls.h'))
            for scanner, expected, source_call in (
                    ('scan_varargs_string.py', 'STRING_CTOR', 'SHOW('),
                    ('scan_string_concat.py', 'COMPOUND_ASSIGN', 'APPEND('),
                    ('scan_i18n_lifetime.py', 'LIFE001', 'LOOKUP(')):
                with self.subTest(scanner=scanner):
                    result = self.run_cli(scanner, target, [database])
                    self.assertEqual(result.returncode, 1, result.stderr)
                    findings = json.loads(result.stdout)['findings']
                    expanded = [f for f in findings
                                if f.get('configuration') == str(database.resolve())]
                    self.assertTrue(any(f['rule'] == expected for f in expanded), findings)
                    for finding in expanded:
                        self.assertIn(source_call, source.splitlines()[finding['line'] - 1])

    def test_configuration_does_not_remove_raw_source_findings(self):
        source = '''void f() {
  string text;
  text.append("bare display");
#ifdef UNUSED_CONFIGURATION
  static const char *p = T_("cached");
  mprf("%s", std::string("bad"));
#endif
}
'''
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            target = root / 'sample.cc'; target.write_text(source)
            database = self.database(root, 'disabled', ('sample.cc',), ('-Dappend(x)=clear()',))
            self.assertNotIn(b'bare display', CppCompilationDatabase(database).source(target).source)
            for scanner in ('scan_varargs_string.py', 'scan_string_concat.py',
                            'scan_i18n_lifetime.py'):
                with self.subTest(scanner=scanner):
                    result = self.run_cli(scanner, target, [database])
                    self.assertEqual(result.returncode, 1, result.stderr)
                    self.assertTrue(json.loads(result.stdout)['findings'])

    def test_lifetime_helpers_from_mutually_exclusive_builds_are_separate(self):
        with tempfile.TemporaryDirectory() as td:
            physical_root = Path(td).resolve() / 'physical'
            physical_root.mkdir()
            root = Path(td).resolve() / 'linked'
            root.symlink_to(physical_root, target_is_directory=True)
            (root / 'helper.cc').write_text('''const char *choose() {
#ifdef BORROW
  return T_("key");
#else
  return "key";
#endif
}
''')
            target = root / 'use.cc'
            target.write_text('#define GET choose\nvoid f(){static const char *p = GET();}\n')
            safe = self.database(root, 'safe', ('helper.cc', 'use.cc'))
            borrowed = self.database(root, 'borrowed', ('helper.cc', 'use.cc'), ('-DBORROW',))
            result = self.run_cli('scan_i18n_lifetime.py', target, [safe, borrowed])
            self.assertEqual(result.returncode, 1, result.stderr)
            findings = json.loads(result.stdout)['findings']
            self.assertTrue(any(f.get('configuration') == str(borrowed.resolve())
                                and f['risk'] == 'HIGH' for f in findings))
            self.assertFalse(any(f.get('configuration') == str(safe.resolve())
                                 for f in findings), findings)

    def test_missing_configuration_and_real_cpp_or_syntax_errors_block(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            target = root / 'sample.cc'
            (root / 'other.cc').write_text('void g() {}\n')
            missing = self.database(root, 'missing', ('other.cc',))
            for source, incomplete in (
                    ('void f() {}\n', True),
                    ('#include "missing-issue120.h"\n', False),
                    ('void f(){int x = 1}\n', False),
                    ('#line 1 "other.cc"\nvoid f(){}\n', False)):
                target.write_text(source)
                database = missing if incomplete else self.database(root, 'source', ('sample.cc',))
                for scanner in ('scan_varargs_string.py', 'scan_string_concat.py',
                                'scan_i18n_lifetime.py'):
                    with self.subTest(source=source, scanner=scanner):
                        result = self.run_cli(scanner, target, [database])
                        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_tu_only_request_rejects_source_line_directives_in_included_header(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            target = root / 'main.cc'
            target.write_text('#include "body.h"\nvoid f() {}\n')
            header = root / 'body.h'
            database = self.database(root, 'source', ('main.cc',))
            for directive in ('#line 900\n', '#line 900 "body.h"\n'):
                header.write_text(directive + 'int n;\n')
                for scanner in ('scan_varargs_string.py', 'scan_string_concat.py',
                                'scan_i18n_lifetime.py'):
                    with self.subTest(directive=directive, scanner=scanner):
                        result = self.run_cli(scanner, target, [database])
                        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                        self.assertIn(str(header), result.stderr)
                        self.assertIn('source-authored', result.stderr)

    def test_explicit_configuration_requires_parser_without_optional_flag(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            target = root / 'sample.cc'; target.write_text('void f() {}\n')
            database = self.database(root, 'source', ('sample.cc',))
            for scanner in ('scan_varargs_string.py', 'scan_string_concat.py',
                            'scan_i18n_lifetime.py'):
                result = subprocess.run(
                    [sys.executable, '-S', str(SCRIPTS / scanner), '--files', str(target),
                     '--compile-commands', str(database)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_macro_parse_failure_reports_original_invocation_line(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            target = root / 'sample.cc'
            target.write_text('#include "calls.h"\nvoid f(){\n  BAD();\n}\n')
            (root / 'calls.h').write_text('#define BAD() int value =\n')
            database = self.database(root, 'source', ('sample.cc',))
            for scanner in ('scan_varargs_string.py', 'scan_string_concat.py',
                            'scan_i18n_lifetime.py'):
                result = self.run_cli(scanner, target, [database])
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(str(target) + ':3:', result.stdout + result.stderr)

    def test_header_keeps_enclosing_class_and_physical_findings(self):
        with tempfile.TemporaryDirectory(prefix='issue120-包含 空格-') as td:
            root = Path(td).resolve()
            header = root / '成员.h'
            header.write_text('''const char *borrowed = LOOKUP("cached");
void f() {
  CALL(std::string("bad"));
  auto text = "You " + std::string("enter");
}
''')
            unit = root / 'main.cc'
            unit.write_text('''#define LOOKUP(x) C_("context", x)
#define CALL(x) mprf("%s", x)
class Holder {
#include "成员.h"
};
void unrelated(){ mprf("%s", std::string("outside"));
  static const char *p = T_("outside"); }
''')
            database = self.database(root, 'class', ('main.cc',))
            for scanner, expected_line in (('scan_varargs_string.py', 3),
                                            ('scan_string_concat.py', 4),
                                            ('scan_i18n_lifetime.py', 1)):
                with self.subTest(scanner=scanner):
                    result = self.run_cli(scanner, header, [database])
                    self.assertEqual(result.returncode, 1, result.stderr)
                    data = json.loads(result.stdout)
                    configured = [f for f in data['findings']
                                  if f.get('configuration') == str(database)]
                    self.assertTrue(configured, result.stdout)
                    self.assertTrue(any(f['line'] == expected_line for f in configured))
                    self.assertTrue(all(Path(f['file']).name == header.name for f in configured))
                    self.assertTrue(all(f['translation_unit'] == str(unit) for f in configured))
                    if scanner == 'scan_i18n_lifetime.py':
                        self.assertTrue(any(f['risk'] == 'HIGH' for f in configured))

    def test_deleted_mpr_header_uses_real_context_and_keeps_risk_and_syntax_checks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            header = root / 'mpr.h'
            source = ('class formatted_string;\n'
                      'void mpr(const formatted_string &) = delete;\n'
                      'inline void f() {\n'
                      '  mprf("%s", std::string("bad"));\n'
                      '  auto text = "You " + std::string("enter");\n'
                      '  static const char *cached = T_("key");\n'
                      '}\n')
            header.write_text(source)
            unit = root / 'main.cc'
            unit.write_text('#include "mpr.h"\n')
            database = self.database(root, 'deleted', ('main.cc',))
            for scanner, line in (('scan_varargs_string.py', 4),
                                  ('scan_string_concat.py', 5),
                                  ('scan_i18n_lifetime.py', 6)):
                with self.subTest(scanner=scanner):
                    result = self.run_cli(scanner, header, [database])
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    data = json.loads(result.stdout)
                    self.assertEqual(data.get('coverage', data.get('meta', {}).get('coverage'))['failed'], [])
                    diagnostic_root = ROOT if scanner == 'scan_varargs_string.py' else root
                    self.assertTrue(any(f.get('configuration') == str(database)
                                        and (diagnostic_root / f['file']).resolve() == header.resolve()
                                        and f['line'] == line
                                        and f['translation_unit'] == str(unit)
                                        for f in data['findings']), result.stdout)
                    for invalid in ('= delete\n', '= delete reason;\n'):
                        header.write_text(source.replace('= delete;\n', invalid))
                        rejected = self.run_cli(scanner, header, [database])
                        self.assertEqual(rejected.returncode, 2, rejected.stdout + rejected.stderr)
                        self.assertIn(str(header) + ':2:', rejected.stderr)
                    header.write_text(source)

    def test_header_argument_and_repeated_inclusion_keep_actual_macro_context(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            header = root / 'argument.h'
            header.write_text('VALUE\n')
            (root / 'main.cc').write_text('''void f() {
#define VALUE std::string("bad")
  mprf("%s",
#include "argument.h"
  );
#undef VALUE
#define VALUE "safe"
  mprf("%s",
#include "argument.h"
  );
}
''')
            database = self.database(root, 'repeated', ('main.cc',))
            result = self.run_cli('scan_varargs_string.py', header, [database])
            self.assertEqual(result.returncode, 1, result.stderr)
            findings = json.loads(result.stdout)['findings']
            configured = [f for f in findings if f.get('configuration') == str(database)]
            self.assertEqual(len(configured), 1, findings)
            self.assertEqual(configured[0]['arg'], 'std::string("bad")')
            self.assertEqual(configured[0]['line'], 1)

    def test_header_helpers_are_expanded_and_isolated_by_translation_unit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            header = root / 'slot.h'
            header.write_text('static const char *p = choose();\n')
            (root / 'helper.h').write_text('inline const char *choose(){return GET("key");}\n')
            for name, macro in (('borrowed.cc', 'T_(x)'), ('also-borrowed.cc', 'T_(x)'),
                                ('safe.cc', '(x)')):
                (root / name).write_text('#define GET(x) ' + macro + '\n'
                    '#include "helper.h"\nvoid f(){\n#include "slot.h"\n}\n')
            database = self.database(root, 'helpers', ('borrowed.cc', 'also-borrowed.cc', 'safe.cc'))
            result = self.run_cli('scan_i18n_lifetime.py', header, [database])
            self.assertEqual(result.returncode, 1, result.stderr)
            findings = [f for f in json.loads(result.stdout)['findings']
                        if f.get('configuration') == str(database)]
            self.assertEqual(len(findings), 2, result.stdout)
            self.assertEqual({f['translation_unit'] for f in findings},
                             {str(root / 'borrowed.cc'), str(root / 'also-borrowed.cc')})
            self.assertTrue(all(f['line'] == 1 and f['risk'] == 'HIGH' for f in findings))

    def test_one_successful_header_context_cannot_hide_a_later_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            header = root / 'body.h'
            header.write_text('VALUE;\n')
            (root / 'good.cc').write_text('#define VALUE int n = 1\n#include "body.h"\n')
            (root / 'bad.cc').write_text('#define VALUE int n =\n#include "body.h"\n')
            database = self.database(root, 'mixed', ('good.cc', 'bad.cc'))
            for scanner in ('scan_varargs_string.py', 'scan_string_concat.py',
                            'scan_i18n_lifetime.py'):
                with self.subTest(scanner=scanner):
                    result = self.run_cli(scanner, header, [database])
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn(str(header) + ':1:', result.stderr)
                    self.assertIn(str(root / 'bad.cc'), result.stderr)
                    if result.stdout:
                        data = json.loads(result.stdout)
                        coverage = data.get('coverage', data.get('meta', {}).get('coverage'))
                        self.assertEqual(coverage['scanned'], 0)
                        self.assertTrue(coverage['failed'])

    def test_header_context_absence_cpp_syntax_and_line_forgery_block(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            header = root / 'body.h'
            unit = root / 'main.cc'
            good_unit = 'void f(){\n#include "body.h"\n}\n'
            database = self.database(root, 'context', ('main.cc',))
            for source, body, diagnostic in (
                    ('void f(){}\n', 'int n;\n', 'no compiled inclusion context'),
                    ('#if 0\n#include "body.h"\n#endif\n', 'int n;\n', 'no compiled inclusion context'),
                    (good_unit, '#include "missing.h"\n', 'preprocessor failed'),
                    (good_unit, 'int n = ;\n', str(header) + ':1:'),
                    (good_unit, '#line 900\nint n;\n', 'source-authored'),
                    ('#include "body.h"\nvoid f(){int n=;}\n', 'int good;\n', str(unit) + ':2:')):
                unit.write_text(source)
                header.write_text(body)
                for scanner in ('scan_varargs_string.py', 'scan_string_concat.py',
                                'scan_i18n_lifetime.py'):
                    with self.subTest(scanner=scanner, diagnostic=diagnostic):
                        result = self.run_cli(scanner, header, [database])
                        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                        self.assertIn(diagnostic, result.stderr)

    def test_header_batch_preprocesses_each_unit_once_and_keeps_ancestors(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            (root / 'one.h').write_text('void f() { CALL(); }\n')
            (root / 'two.h').write_text('void g() {}\n')
            (root / 'outer.h').write_text('class Outer{\n#include "one.h"\n};\n')
            for name in ('a.cc', 'b.cc'):
                (root / name).write_text('#define CALL() mprf("%s", std::string("bad"))\n'
                    '#include "outer.h"\n#include "two.h"\n')
            database = CppCompilationDatabase(self.database(root, 'batch', ('a.cc', 'b.cc')))
            with mock.patch('i18n_shared.preprocess_cpp', wraps=preprocess_cpp) as expand:
                contexts = list(database.contexts([root / 'one.h', root / 'two.h']))
            self.assertEqual(expand.call_count, 2)
            self.assertEqual(len(contexts), 2)
            for context in contexts:
                self.assertIn(b'class Outer{', context.source)
                self.assertIn(str(root / 'outer.h'), context.original_files)
                self.assertEqual(set(context.covered_files),
                                 {str(root / 'one.h'), str(root / 'two.h')})
                parse_preprocessed_cpp(Parser(Language(tree_sitter_cpp.language())),
                                       context.source, preprocessed=context,
                                       filepath=context.translation_unit)

    def test_compilation_database_preserves_flags_and_rejects_ambiguous_entries(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            (root / 'sample.cc').write_text('#ifdef FLAG\nint selected;\n#endif\n')
            database = self.database(root, 'source', ('sample.cc',), ('-DFLAG',))
            loaded = CppCompilationDatabase(database)
            self.assertIn(b'int selected;', loaded.source(root / 'sample.cc').source)
            self.assertIs(loaded.source(root / 'sample.cc'), loaded.source(root / 'sample.cc'))
            entries = json.loads(database.read_text())
            database.write_text(json.dumps(entries * 2))
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                CppCompilationDatabase(database)
            entries[0]['arguments'] = [self.compiler, '@flags.rsp', '-c', 'sample.cc']
            database.write_text(json.dumps(entries))
            with self.assertRaisesRegex(ValueError, 'indirect'):
                CppCompilationDatabase(database)

    def test_make_export_uses_current_core_tu_flags_without_building(self):
        with tempfile.TemporaryDirectory() as td:
            database = Path(td) / 'commands 空格.json'
            command = ['make', '-C', str(ROOT / 'crawl-ref/source'),
                       'i18n-compile-commands', 'FORCE_CXX=' + self.compiler,
                       'PYTHON=' + sys.executable, 'I18N_SCAN_FILES=directn.cc main.cc',
                       'I18N_COMPILE_COMMANDS=' + str(database),
                       'EXTRA_FLAGS=-DISSUE120_EXPORT_VALUE=123']
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            entries = json.loads(database.read_text())
            self.assertEqual([entry['file'] for entry in entries], ['directn.cc', 'main.cc'])
            for entry in entries:
                self.assertIn('-DISSUE120_EXPORT_VALUE=123', entry['arguments'])
                self.assertIn('-std=c++11', entry['arguments'])
            self.assertEqual(len(CppCompilationDatabase(database).commands), 2)
            before = database.read_bytes()
            for dry_run in ('-n', '--dry-run'):
                result = subprocess.run(command + [dry_run], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(database.read_bytes(), before)
            for invalid in ('I18N_SCAN_FILES=mpr.h', 'I18N_SCAN_FILES=util/levcomp.cc',
                            'I18N_SCAN_FILES=catch2-tests/catch_amalgamated.cc',
                            'I18N_SCAN_FILES=directn.cc directn.cc',
                            'I18N_SCAN_FILES=all directn.cc',
                            'I18N_BUILD_GOAL=unknown', 'I18N_BUILD_GOAL=',
                            'I18N_BUILD_GOAL=crawl catch2-tests', 'crawl',
                            'I18N_SCAN_FILES=', 'I18N_COMPILE_COMMANDS='):
                result = subprocess.run(command + [invalid], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(database.read_bytes(), before)

    def test_export_matches_actual_object_recipe_across_build_goals(self):
        source_dir = ROOT / 'crawl-ref/source'
        # Reuse the production compile recipe, but remove its build prerequisites
        # for this read-only make -n probe. Make still evaluates the real object
        # target's flags, independently of the export sibling's target context.
        recipe = next(line for line in (source_dir / 'Makefile').read_text().splitlines()
                      if line.startswith('\t$(QUIET_CXX)$(CXX) $(STDFLAG) $(ALL_CFLAGS)')
                      and '-x c++-header' not in line)
        files = ['directn.cc', 'util/levcomp.tab.cc', 'rltiles/tiledef-main.cc']
        with tempfile.TemporaryDirectory() as td:
            database = Path(td) / 'commands.json'
            for goal, options in (('crawl', []), ('crawl', ['TILES=y']),
                                  ('crawl', ['WEBTILES=y']), ('debug', []),
                                  ('debug-lite', []), ('profile', []),
                                  ('catch2-tests', []), ('monster', [])):
                selected = files + (['catch2-tests/catch_amalgamated.cc']
                                    if goal == 'catch2-tests' else [])
                options = ['FORCE_CXX=' + self.compiler, 'PYTHON=' + sys.executable,
                           'V=1', 'EXTRA_FLAGS=-DISSUE120_EXPORT_VALUE=123', *options]
                result = subprocess.run(
                    ['make', '-C', str(source_dir), '-j4', 'i18n-compile-commands',
                     'I18N_BUILD_GOAL=' + goal, 'I18N_SCAN_FILES=' + ' '.join(selected),
                     'I18N_COMPILE_COMMANDS=' + str(database), *options],
                    capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                for entry in json.loads(database.read_text()):
                    source = entry['file']
                    obj = str(Path(source).with_suffix('.o'))
                    probe_makefile = Path(td) / 'probe.mk'
                    probe_makefile.write_text('MAKECMDGOALS := ' + goal + '\n'
                        + 'include Makefile\n.PHONY: ' + obj + '\n'
                        + obj + ': ' + source + '\n' + recipe + '\n')
                    probe = subprocess.run(
                        ['make', '-C', str(source_dir), '-n', '-o', source, obj,
                         '-f', str(probe_makefile),
                         *options],
                        capture_output=True, text=True)
                    self.assertEqual(probe.returncode, 0, probe.stdout + probe.stderr)
                    commands = [shlex.split(line) for line in probe.stdout.splitlines()
                                if ' -c ' + source + ' -o ' + obj in line]
                    with self.subTest(goal=goal, options=options, source=source):
                        self.assertEqual(commands, [entry['arguments']])

    def test_export_all_uses_selected_build_inventory_and_tilegen_host_flags(self):
        with tempfile.TemporaryDirectory() as td:
            database = Path(td) / 'commands.json'
            source_dir = ROOT / 'crawl-ref/source'
            common = ['make', '-C', str(source_dir), '-j4', 'i18n-compile-commands',
                      'FORCE_CXX=' + self.compiler, 'PYTHON=' + sys.executable,
                      'I18N_SCAN_FILES=all', 'I18N_COMPILE_COMMANDS=' + str(database)]
            inventories = {}
            for goal in ('crawl', 'catch2-tests'):
                result = subprocess.run(common + ['I18N_BUILD_GOAL=' + goal],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                entries = json.loads(database.read_text())
                inventories[goal] = {entry['file'] for entry in entries}
                self.assertEqual(len(entries), len(inventories[goal]))
                self.assertIn('util/levcomp.lex.cc', inventories[goal])
                self.assertIn('rltiles/tiledef-main.cc', inventories[goal])
            self.assertIn('main.cc', inventories['crawl'])
            self.assertNotIn('main.cc', inventories['catch2-tests'])
            self.assertIn('catch2-tests/test_main.cc', inventories['catch2-tests'])
            self.assertFalse(any(name.startswith('catch2-tests/')
                                 for name in inventories['crawl']))

            # This is the actual host-tool recipe; it must not acquire the
            # target game's flags merely because a cross build selected it.
            source_dir /= 'rltiles'
            recipe = next(line for line in (source_dir / 'Makefile').read_text().splitlines()
                          if line.startswith('\t$(QUIET_HOSTCXX)$(HOSTCXX)'))
            result = subprocess.run(
                ['make', '-C', str(source_dir), '-j4', 'i18n-compile-commands',
                 'HOSTCXX=' + self.compiler, 'CXX=missing-target-compiler',
                 'PYTHON=' + sys.executable, 'I18N_SCAN_FILES=all', 'TILES=y',
                 'DEBUG=y', 'ANDROID=1', 'I18N_COMPILE_COMMANDS=' + str(database)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            loaded = CppCompilationDatabase(database)
            self.assertTrue(loaded.commands)
            for entry in json.loads(database.read_text()):
                source = entry['file']
                obj = str(Path(source).with_suffix('.o'))
                probe_makefile = Path(td) / 'probe.mk'
                probe_makefile.write_text('include Makefile\n.PHONY: ' + obj + '\n'
                    + obj + ': ' + source + '\n' + recipe + '\n')
                probe = subprocess.run(
                    ['make', '-C', str(source_dir), '-n', '-o', source, obj,
                     'HOSTCXX=' + self.compiler, 'TILES=y', 'DEBUG=y', 'ANDROID=1', 'V=1',
                     '-f', str(probe_makefile)],
                    capture_output=True, text=True)
                self.assertEqual(probe.returncode, 0, probe.stdout + probe.stderr)
                commands = [shlex.split(line) for line in probe.stdout.splitlines()
                            if ' -c ' + source + ' -o ' + obj in line]
                self.assertEqual(commands, [entry['arguments']])
                self.assertIn('-DUSE_TILE', entry['arguments'])
                self.assertNotIn('-DCLUA_BINDINGS', entry['arguments'])

    def test_export_does_not_read_stale_dependencies_or_build_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            tile_dir = root / 'crawl-ref/source/rltiles'
            (tile_dir / 'tool').mkdir(parents=True)
            scripts = root / '.claude/scripts'
            scripts.mkdir(parents=True)
            shutil.copy(ROOT / 'crawl-ref/source/rltiles/Makefile', tile_dir)
            shutil.copy(SCRIPTS / 'export_compile_commands.py', scripts)
            (tile_dir / 'tool/main.d').write_text('$(error stale dependency was read)\n')
            (tile_dir / '.cflags').write_text('existing compiler flags\n')
            (tile_dir / 'tool/main.o').write_bytes(b'existing object\n')
            before = {str(path.relative_to(root)): path.read_bytes()
                      for path in root.rglob('*') if path.is_file()}
            database = root / 'commands.json'
            command = ['make', '-C', str(tile_dir), 'i18n-compile-commands',
                       'HOSTCXX=' + self.compiler, 'PYTHON=' + sys.executable,
                       'I18N_SCAN_FILES=all', 'I18N_COMPILE_COMMANDS=commands.json']
            # GNU make 3.81 can put assignments first when no short option
            # is set. An "n" in commands.json is not the dry-run flag.
            assignment_flags = ('MAKEFLAGS=I18N_COMPILE_COMMANDS=commands.json '
                                'I18N_SCAN_FILES=all PYTHON=' + sys.executable
                                + ' HOSTCXX=' + self.compiler)
            for options in ([], [assignment_flags]):
                with self.subTest(makeflags=options):
                    database.unlink(missing_ok=True)
                    result = subprocess.run(command + options,
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertTrue(database.is_file(), result.stdout + result.stderr)
                    after = {str(path.relative_to(root)): path.read_bytes()
                             for path in root.rglob('*')
                             if path.is_file() and path != database}
                    self.assertEqual(after, before)
            before_dryrun = {str(path.relative_to(root)): path.read_bytes()
                             for path in root.rglob('*') if path.is_file()}
            for dryrun in ('-n', '--dry-run'):
                with self.subTest(dryrun=dryrun):
                    result = subprocess.run(
                        ['make', dryrun, '-C', str(tile_dir), 'i18n-compile-commands',
                         'HOSTCXX=' + self.compiler, 'PYTHON=' + sys.executable,
                         'I18N_SCAN_FILES=all', 'I18N_COMPILE_COMMANDS=not-created.json'],
                        capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertFalse((root / 'not-created.json').exists())
                    after_dryrun = {str(path.relative_to(root)): path.read_bytes()
                                    for path in root.rglob('*') if path.is_file()}
                    self.assertEqual(after_dryrun, before_dryrun)

    def test_export_collection_failure_preserves_previous_database(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            database = root / 'database.json'
            database.write_bytes(b'previous database\n')
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / 'export_compile_commands.py'),
                 'entry', str(root), 'first.cc', '--', self.compiler,
                 '-c', 'first.cc', '-o', 'first.o'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / 'export_compile_commands.py'),
                 'collect', str(database), str(root), 'first.cc', 'missing.cc'],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(database.read_bytes(), b'previous database\n')
            self.assertFalse(list(root.glob('database.json.*')))

    def test_output_and_dependency_options_cannot_overwrite_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            target = root / 'sample.cc'; target.write_text('int value;\n')
            output = root / 'object.o'; output.write_bytes(b'object sentinel')
            dependency = root / 'deps.d'; dependency.write_bytes(b'dependency sentinel')
            for flags in (('-oobject.o', '-MFdeps.d'),
                          ('--output=object.o', '-MF', 'deps.d'),
                          ('--output', 'object.o', '-MJdeps.d'),
                          ('-o', 'object.o', '-serialize-diagnostics', 'deps.d')):
                with self.subTest(flags=flags):
                    database = self.database(root, 'source', ('sample.cc',), flags)
                    self.assertIn(b'int value;', CppCompilationDatabase(database).source(target).source)
                    self.assertEqual(output.read_bytes(), b'object sentinel')
                    self.assertEqual(dependency.read_bytes(), b'dependency sentinel')
            for flags in (('-S',), ('-M',), ('-MM',), ('-save-temps',)):
                database = self.database(root, 'source', ('sample.cc',), flags)
                with self.assertRaises(ValueError):
                    CppCompilationDatabase(database)
                self.assertEqual(output.read_bytes(), b'object sentinel')
            config = root / 'driver.cfg'
            config.write_text('-o object.o\n')
            for flags in (('--config=' + str(config),), ('--config', str(config)),
                          ('--config-system-dir=' + td,), ('--config-user-dir', td)):
                database = self.database(root, 'source', ('sample.cc',), flags)
                with self.assertRaisesRegex(ValueError, 'indirect'):
                    CppCompilationDatabase(database)
                self.assertEqual(output.read_bytes(), b'object sentinel')
            database = self.database(root, 'source', ('sample.cc',))
            entries = json.loads(database.read_text())
            entries[0]['arguments'][0] = 'g++'
            database.write_text(json.dumps(entries))
            with self.assertRaisesRegex(ValueError, 'clang driver'):
                CppCompilationDatabase(database)


if __name__ == '__main__':
    unittest.main()
