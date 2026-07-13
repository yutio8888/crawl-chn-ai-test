#!/usr/bin/env python3
"""Focused regression tests for the project terminology checker."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from check_terms import check


XLIFF = '''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file source-language="en" target-language="zh" datatype="x-crawl">
    <body>
      <trans-unit id="cast"><source>Cast the fire spell</source><target>施放火焰法术</target></trans-unit>
      <trans-unit id="domain"><source>Fire bolt</source><target>闪电</target><note>context=spell</note></trans-unit>
      <trans-unit id="context"><source>chant</source><target>咏唱</target><note>context=ritual</note></trans-unit>
    </body>
  </file>
</xliff>
'''

GLOSSARY = '''cast\t施法 / 施放 / 咏唱\tdomain=core
fire bolt\t火焰弹\tdomain=spells
fire bolt\t闪电\tdomain=items
chant\t吟唱\tcontext=spell
chant\t咏唱\tcontext=ritual
'''


class CheckTermsTest(unittest.TestCase):
    def test_alternatives_and_context(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.xlf"
            glossary = root / "glossary.tsv"
            source.write_text(XLIFF, encoding="utf-8")
            glossary.write_text(GLOSSARY, encoding="utf-8")

            report = check(source, glossary)
            self.assertEqual(report["issue_count"], 1)
            self.assertEqual(report["issues"][0]["term"], "fire bolt")

            spell_report = check(source, glossary, "spells")
            self.assertEqual(spell_report["issue_count"], 1)
            self.assertEqual(spell_report["issues"][0]["term"], "fire bolt")

    def test_context_mismatch_is_not_a_match(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.xlf"
            glossary = root / "glossary.tsv"
            source.write_text(XLIFF, encoding="utf-8")
            glossary.write_text(GLOSSARY, encoding="utf-8")
            report = check(source, glossary)
            self.assertNotIn("chant", [issue["term"] for issue in report["issues"]])


if __name__ == "__main__":
    unittest.main()
