#!/usr/bin/env python3

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / ".claude/scripts/audit_move_i18n.py"


class MoveI18nAuditTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.source = self.root / "source"
        (self.source / "dat/species").mkdir(parents=True)
        (self.source / "movement.cc").write_text(
            'static string _get_move_verb(bool) { return "walk"; }\n',
            encoding="utf-8")
        (self.source / "spl-transloc.cc").write_text("", encoding="utf-8")

        self.contexts = {
            "move.bare": [],
            "move.enter-area": ["step", "walk"],
            "move.onto-surface": ["step", "walk"],
            "move.onto-actor": [],
            "move.through-obstacle": ["walk"],
            "move.toward-target": [],
            "move.over-terrain": ["step", "walk"],
        }
        self.manifest = self.root / "manifest.json"
        self.source_txt = self.root / "source.txt"
        self.write_manifest()
        self.write_source_txt()

    def tearDown(self):
        self.tempdir.cleanup()

    def write_manifest(self):
        data = {"contexts": {
            context: {"description": f"test {context}", "verbs": verbs}
            for context, verbs in self.contexts.items()
        }}
        self.manifest.write_text(json.dumps(data), encoding="utf-8")

    def write_source_txt(self, empty_key=None):
        blocks = []
        for context, verbs in self.contexts.items():
            for verb in verbs:
                key = f"{context}|{verb}"
                value = "" if key == empty_key else "译"
                blocks.append(f"{key}\n{value}\n")
        self.source_txt.write_text("%%%%\n" + "%%%%\n".join(blocks),
                                   encoding="utf-8")

    def run_audit(self):
        return subprocess.run(
            [sys.executable, str(AUDIT), str(self.source),
             "--source-txt", str(self.source_txt),
             "--manifest", str(self.manifest)],
            text=True, capture_output=True, check=False)

    def test_missing_context_is_blocking(self):
        del self.contexts["move.bare"]
        self.write_manifest()
        result = self.run_audit()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("manifest missing contexts: move.bare", result.stderr)

    def test_empty_exact_translation_is_blocking(self):
        self.write_source_txt("move.enter-area|walk")
        result = self.run_audit()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("empty translation: move.enter-area|walk", result.stderr)

    def test_new_literal_moveto_verb_is_blocking(self):
        (self.source / "new-move.cc").write_text(
            'void f() { check_moveto(p, "burrow"); }\n', encoding="utf-8")
        result = self.run_audit()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unclassified reachable verbs: burrow", result.stderr)

    def test_new_get_move_verb_return_is_blocking(self):
        (self.source / "movement.cc").write_text(
            'static string _get_move_verb(bool x) {\n'
            '    if (x) return "burrow";\n'
            '    return "walk";\n'
            '}\n', encoding="utf-8")
        result = self.run_audit()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unclassified reachable verbs: burrow", result.stderr)

    def test_multiline_moveto_literal_is_blocking(self):
        (self.source / "new-move.cc").write_text(
            'void f() { check_moveto(\n'
            '    destination,\n'
            '    "climb",\n'
            '    false); }\n', encoding="utf-8")
        result = self.run_audit()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unclassified reachable verbs: climb", result.stderr)

    def test_check_move_over_literal_is_blocking(self):
        (self.source / "new-move.cc").write_text(
            'void f() { check_move_over(destination, "vault"); }\n',
            encoding="utf-8")
        result = self.run_audit()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("move.enter-area: unclassified reachable verbs: vault",
                      result.stderr)
        self.assertIn("move.onto-surface: unclassified reachable verbs: vault",
                      result.stderr)

    def test_direct_context_helper_literal_is_blocking(self):
        (self.source / "new-move.cc").write_text(
            'void f() { translated_move_phrase(\n'
            '    "burrow", move_phrase_context::through_obstacle); }\n',
            encoding="utf-8")
        result = self.run_audit()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "move.through-obstacle: unclassified reachable verbs: burrow",
            result.stderr)

    def test_non_verb_literal_argument_is_not_inventory(self):
        (self.source / "new-move.cc").write_text(
            'void f() { check_moveto_terrain(destination, move_verb, '
            '"burrow warning"); }\n', encoding="utf-8")
        result = self.run_audit()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("burrow warning", result.stdout + result.stderr)

    def test_unqualified_fallback_does_not_satisfy_exact_key(self):
        text = self.source_txt.read_text(encoding="utf-8")
        text = text.replace("%%%%\nmove.enter-area|walk\n译\n", "", 1)
        text += "%%%%\nwalk\n走\n"
        self.source_txt.write_text(text, encoding="utf-8")
        result = self.run_audit()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing exact TextDB key: move.enter-area|walk",
                      result.stderr)

    def test_stale_manifest_verb_is_warning_only(self):
        self.contexts["move.bare"].append("ghost-step")
        self.write_manifest()
        self.write_source_txt()
        result = self.run_audit()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("WARNING: move.bare: stale manifest verbs: ghost-step",
                      result.stdout)


if __name__ == "__main__":
    unittest.main()
