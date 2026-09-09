#!/usr/bin/env python3
"""Issue 120: exercise real scanner entries, patterns and macro adapters."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

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


class PreprocessorOutputTests(unittest.TestCase):
    def setUp(self):
        self.compiler = shutil.which('clang++')
        if self.compiler is None:
            self.skipTest('clang++ is not installed')

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
            root = Path(td)
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
                    expanded = [f for f in findings if f.get('configuration') == str(database)]
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
            root = Path(td)
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
            root = Path(td)
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
            self.assertTrue(any(f.get('configuration') == str(borrowed)
                                and f['risk'] == 'HIGH' for f in findings))
            self.assertFalse(any(f.get('configuration') == str(safe) for f in findings))

    def test_missing_configuration_and_real_cpp_or_syntax_errors_block(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
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

    def test_explicit_configuration_requires_parser_without_optional_flag(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
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
            root = Path(td)
            target = root / 'sample.cc'
            target.write_text('#include "calls.h"\nvoid f(){\n  BAD();\n}\n')
            (root / 'calls.h').write_text('#define BAD() int value =\n')
            database = self.database(root, 'source', ('sample.cc',))
            for scanner in ('scan_varargs_string.py', 'scan_string_concat.py',
                            'scan_i18n_lifetime.py'):
                result = self.run_cli(scanner, target, [database])
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(str(target) + ':3:', result.stdout + result.stderr)

    def test_compilation_database_preserves_flags_and_rejects_ambiguous_entries(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
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
            for invalid in ('I18N_SCAN_FILES=mpr.h', 'I18N_SCAN_FILES=util/levcomp.cc',
                            'I18N_SCAN_FILES=catch2-tests/catch_amalgamated.cc',
                            'I18N_SCAN_FILES=', 'I18N_COMPILE_COMMANDS='):
                result = subprocess.run(command + [invalid], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(database.read_bytes(), before)

    def test_output_and_dependency_options_cannot_overwrite_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
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
