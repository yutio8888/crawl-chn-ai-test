#!/usr/bin/env python3
"""Issue 120: exercise real scanner entries, patterns and macro adapters."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / '.claude/scripts'
sys.path.insert(0, str(SCRIPTS))
from i18n_shared import (parse_cpp_annotations, _matches_preprocessor_node,
                         _directive_events)
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

    def test_missing_semicolon_inside_registered_context(self):
        original = (ROOT / 'crawl-ref/source/directn.cc').read_bytes()
        # This exact line is inside the registered * / . error context.
        # Mutate only its semicolon; retain the registered path and directives.
        line = b'const vault_placement &vp(*env.level_vaults[map_index]);'
        self.assertEqual(original.count(line), 1)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'crawl-ref/source/directn.cc'
            path.parent.mkdir(parents=True)
            for broken in (False, True):
                path.write_bytes(original.replace(line, line[:-1]) if broken else original)
                for directory in (False, True):
                    with self.subTest(broken=broken, directory=directory):
                        self.check_cli(path, not broken, directory=directory)

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
                  b'auto raw = R"x("prefix" CRAWL va_arg(args, int))x";\n'
                  b'int CRAWL = 0;\n')
        self.assertEqual(source, parse_cpp_annotations(parser, source).root_node.text)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'macros.cc'
            for bad in (b'void f() { auto x = "a" CRAWLX "b"; }',
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


if __name__ == '__main__':
    unittest.main()
