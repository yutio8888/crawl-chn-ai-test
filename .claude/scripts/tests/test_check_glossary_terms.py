#!/usr/bin/env python3
"""Distinguish name qualifiers from glossary context annotations."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_glossary_terms import load_terms, validate


class GlossaryQualifierTests(unittest.TestCase):
    def test_name_qualifiers_and_context_annotations(self):
        with tempfile.TemporaryDirectory() as tmp:
            glossary = Path(tmp) / "glossary.utf8"
            rows = [(f"Dragon Vein ({element})", f"龙脉（{zh}）")
                    for element, zh in (("Fire", "火"), ("Ice", "冰"),
                                        ("Air", "气"), ("Earth", "土"))]
            rows += [("Example（Qualifier）", "例（限定）"),
                     ("cast", "施法（通用） / 吟诵（仪式）"),
                     ("A (note) title", "标题（注释）")]
            glossary.write_text("\n".join(f"{en}\t{zh}\ttest" for en, zh in rows))
            terms = load_terms(glossary)
            for en, zh in rows[:5]:
                self.assertEqual({zh}, terms[en])
            self.assertEqual({"施法", "吟诵"}, terms["cast"])
            self.assertEqual({"标题"}, terms["A (note) title"])
            source = Path(tmp) / "source.txt"
            source.write_text("%%%%\nDragon Vein (Fire)\n龙脉（火）\n")
            self.assertEqual((1, 0), validate(terms, [source]))
            source.write_text("%%%%\nDragon Vein (Fire)\n龙脉\n")
            self.assertEqual((1, 1), validate(terms, [source]))


if __name__ == "__main__":
    unittest.main()
