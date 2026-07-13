from contextlib import redirect_stdout
from io import StringIO
import tempfile
import unittest
from pathlib import Path

import check_glossary_terms


class CheckGlossaryTermsTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.glossary = root / "glossary.utf8"
        self.translation = root / "source.txt"
        self.glossary.write_text(
            "cast\t施法\tdomain=core\ncast\t吟诵\tdomain=core\nbroad axe\t阔刃斧\tdomain=items\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def test_accepts_any_allowed_translation(self):
        self.translation.write_text("cast\n吟诵\n%%%%\n", encoding="utf-8")
        terms = check_glossary_terms.load_terms(self.glossary)
        checked, failures = check_glossary_terms.validate(terms, [self.translation])
        self.assertEqual((1, 0), (checked, failures))

    def test_strips_context_labels_from_allowed_targets(self):
        self.glossary.write_text("cast\t施法（通用） / 吟诵（仪式）\tdomain=core\n", encoding="utf-8")
        self.translation.write_text("cast\n施法\n%%%%\n", encoding="utf-8")
        terms = check_glossary_terms.load_terms(self.glossary)
        checked, failures = check_glossary_terms.validate(terms, [self.translation])
        self.assertEqual((1, 0), (checked, failures))

    def test_rejects_stale_exact_key_translation(self):
        self.translation.write_text("broad axe\n阔斧\n%%%%\n", encoding="utf-8")
        terms = check_glossary_terms.load_terms(self.glossary)
        with redirect_stdout(StringIO()):
            checked, failures = check_glossary_terms.validate(terms, [self.translation])
        self.assertEqual((1, 1), (checked, failures))

    def test_rejects_allowed_term_with_unapproved_suffix(self):
        self.glossary.write_text("Recall\t召回\tdomain=spells\n", encoding="utf-8")
        self.translation.write_text("Recall\n召回术\n%%%%\n", encoding="utf-8")
        terms = check_glossary_terms.load_terms(self.glossary)
        with redirect_stdout(StringIO()):
            checked, failures = check_glossary_terms.validate(terms, [self.translation])
        self.assertEqual((1, 1), (checked, failures))


if __name__ == "__main__":
    unittest.main()
