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


    def rejection_fixture(self, catalog="", english="", chinese="", family="descript"):
        root = Path(self.tempdir.name) / "dat"
        for stale in root.glob("*/**/sample.txt"):
            stale.unlink()
        for directory in ("i18n/zh", "descript/zh", "database/zh"):
            (root / directory).mkdir(parents=True, exist_ok=True)
        (root / "i18n/zh/source.txt").write_text("%%%%\n" + catalog, encoding="utf-8")
        (root / family / "sample.txt").write_text("%%%%\n" + english, encoding="utf-8")
        (root / family / "zh/sample.txt").write_text("%%%%\n" + chinese, encoding="utf-8")
        self.glossary.write_text(
            "mutagenic energy\t诱变能量\ttest; reject=变异能量／突变能量\n"
            "mutagenic energies\t诱变能量\ttest; reject=变异能量／突变能量\n"
            "mutagenic power\t诱变力量\ttest; reject=突变能量\n", encoding="utf-8")
        return root

    def rejection_scan(self, root):
        with redirect_stdout(StringIO()) as output:
            result = check_glossary_terms.validate_rejections(
                check_glossary_terms.load_rejections(self.glossary), root)
        return result, output.getvalue()

    def test_rejects_long_sentence_and_explicit_plural(self):
        root = self.rejection_fixture(
            "Mutagenic ENERGIES flow.\n变异能量流动。\n%%%%\n"
            "The mutagenic power dissipates.\n突变能量消散。\n")
        result, output = self.rejection_scan(root)
        self.assertEqual((2, 2), result)
        self.assertIn("source.txt:3", output)
        self.assertIn("deprecated", output)

    def test_pairs_prose_by_key_and_uses_english_body(self):
        for family in ("descript", "database"):
            with self.subTest(family=family):
                root = self.rejection_fixture(
                    english="Example\nIt emits mutagenic\nenergy.\n",
                    chinese="example\n它释放变异能量。\n", family=family)
                result, output = self.rejection_scan(root)
                self.assertEqual((1, 1), result)
                self.assertIn("sample.txt:3", output)

    def test_unrelated_english_and_word_prefix_do_not_match(self):
        root = self.rejection_fixture(
            "Some energy flows.\n变异能量流动。\n%%%%\n"
            "Premutagenic energy.\n突变能量。\n",
            english="sample\nAn unrelated effect.\n",
            chinese="sample\n突变能量。\n")
        self.assertEqual((0, 0), self.rejection_scan(root)[0])

    def test_fixed_spell_name_and_biological_quote_are_not_rejected(self):
        root = self.rejection_fixture(
            "Mutagenic Gaze\n变异凝视\n",
            english="quote\nMutations may confer a biological advantage.\n",
            chinese="quote\n突变可能带来生物学优势。\n")
        self.assertEqual((0, 0), self.rejection_scan(root)[0])

    def test_lookup_key_is_not_english_body_or_translation(self):
        root = self.rejection_fixture(
            english="mutagenic energy\nA harmless glow.\n",
            chinese="mutagenic energy\n变异能量。\n")
        self.assertEqual((0, 0), self.rejection_scan(root)[0])
        (root / "descript/zh/sample.txt").write_text(
            "%%%%\nmutagenic energy\n诱变能量。\n", encoding="utf-8")
        self.assertEqual((0, 0), self.rejection_scan(root)[0])

    def test_free_text_deprecation_is_not_a_rule(self):
        self.glossary.write_text("piety\t虔诚值\t弃用数值名 虔诚度\n", encoding="utf-8")
        self.assertEqual({}, check_glossary_terms.load_rejections(self.glossary))

    def test_missing_required_partner_fails_closed(self):
        root = self.rejection_fixture(english="sample\nmutagenic energy\n",
                                      chinese="sample\n诱变能量\n")
        (root / "descript/sample.txt").unlink()
        with self.assertRaisesRegex(ValueError, "missing English partner"):
            self.rejection_scan(root)

    def test_cli_scans_unchanged_residue_and_returns_failure(self):
        import subprocess
        import sys
        root = self.rejection_fixture("Mutagenic energy flows.\n突变能量流动。\n")
        command = [sys.executable, str(Path(check_glossary_terms.__file__)),
                   "--glossary", str(self.glossary), "--paths", "--data-root", str(root)]
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertIn("OK: 0 exact-key entries", result.stdout)
        self.assertIn("FAIL: 1 deprecated-form violation", result.stdout)
        (root / "i18n/zh/source.txt").write_text(
            "%%%%\nMutagenic energy flows.\n诱变能量流动。\n", encoding="utf-8")
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
