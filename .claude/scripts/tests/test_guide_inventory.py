#!/usr/bin/env python3

import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "guide_inventory", ROOT / ".claude/scripts/guide_inventory.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class GuideInventoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "crawl-ref/docs/zh").mkdir(parents=True)
        (self.root / "crawl-ref/source/util").mkdir(parents=True)
        (self.root / "docs").mkdir(parents=True)
        shutil.copy2(ROOT / "docs/glossary.md",
                     self.root / "docs/glossary.md")
        for _, filename, _, _ in MODULE.GUIDES:
            shutil.copy2(ROOT / "crawl-ref/docs" / filename,
                         self.root / "crawl-ref/docs" / filename)
            shutil.copy2(ROOT / "crawl-ref/docs/zh" / filename,
                         self.root / "crawl-ref/docs/zh" / filename)
        shutil.copy2(ROOT / "crawl-ref/source/util/unrest.pl",
                     self.root / "crawl-ref/source/util/unrest.pl")
        shutil.copy2(self.root / "crawl-ref/docs/zh/quickstart.md",
                     self.root / "crawl-ref/docs/zh/quickstart.txt")
        manual = subprocess.run(
            ["perl", str(self.root / "crawl-ref/source/util/unrest.pl")],
            input=(self.root / "crawl-ref/docs/zh/crawl_manual.rst").read_bytes(),
            stdout=subprocess.PIPE, check=True).stdout
        (self.root / "crawl-ref/docs/zh/crawl_manual.txt").write_bytes(manual)

    def tearDown(self):
        self.temp.cleanup()

    def _write_review_docs(self, payload, rows=None):
        (self.root / "docs/guide-review-plan.md").write_text(
            MODULE.render_review_plan(payload), encoding="utf-8")
        if rows is None:
            rows = [(card["stable_id"], "keep") for card in payload["cards"]]
        lines = [
            "# Test Review Results", "", "## Frozen boundary", "",
            f"- Inventory digest: `{payload['inventory_digest']}`",
            f"- Glossary SHA-256: `{payload['glossary_sha256']}`",
            f"- Frozen identities: {payload['coverage']['expected']}",
            "", MODULE.EVIDENCE_HEADING, "", MODULE.EVIDENCE_HEADER,
            MODULE.EVIDENCE_SEPARATOR,
        ]
        lines.extend(
            f"| `{identity}` | `{conclusion}` | E | Z | evidence | N/A | high |"
            for identity, conclusion in rows)
        (self.root / "docs/guide-review-results.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8")

    def test_complete_inventory_passes(self):
        payload = MODULE.build_inventory(self.root)
        self.assertEqual(payload["coverage"]["expected"],
                         payload["coverage"]["concluded"])
        self.assertEqual([item[0] for item in MODULE.GUIDES],
                         payload["guide_set"])

    def test_missing_section_fails(self):
        path = self.root / "crawl-ref/docs/zh/options_guide.txt"
        text = path.read_text(encoding="utf-8")
        text = text.replace("3-g     命令功能增强。\n", "命令功能增强。\n", 1)
        path.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(MODULE.InventoryError, "section identity/order"):
            MODULE.build_inventory(self.root)

    def test_duplicate_section_fails(self):
        path = self.root / "crawl-ref/docs/zh/macros_guide.txt"
        with path.open("a", encoding="utf-8") as stream:
            stream.write("\n重复章节\n--------\n")
        with self.assertRaisesRegex(MODULE.InventoryError, "section count mismatch"):
            MODULE.build_inventory(self.root)

    def test_protected_token_damage_fails(self):
        path = self.root / "crawl-ref/docs/zh/options_guide.txt"
        text = path.read_text(encoding="utf-8").replace(
            "http://crawl.develz.org/", "http://invalid.example/", 1)
        path.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(MODULE.InventoryError, "protected token mismatch"):
            MODULE.build_inventory(self.root)

    def test_plain_option_declaration_damage_fails(self):
        path = self.root / "crawl-ref/docs/zh/options_guide.txt"
        text = path.read_text(encoding="utf-8").replace(
            "name = Delilah", "nom = Delilah", 1)
        path.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "option_declaration_order"):
            MODULE.build_inventory(self.root)

    def test_named_key_damage_fails(self):
        path = self.root / "crawl-ref/docs/zh/macros_guide.txt"
        text = path.read_text(encoding="utf-8").replace("# Tab:", "# Tap:", 1)
        path.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "macro_key_declaration_order"):
            MODULE.build_inventory(self.root)

    def test_code_block_identifier_damage_fails(self):
        english = self.root / "crawl-ref/docs/macros_guide.txt"
        chinese = self.root / "crawl-ref/docs/zh/macros_guide.txt"
        english.write_text(
            english.read_text(encoding="utf-8") + "\n{{foo()}}\n",
            encoding="utf-8")
        chinese.write_text(
            chinese.read_text(encoding="utf-8") + "\n{{bar()}}\n",
            encoding="utf-8")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "code_identifier_order"):
            MODULE.build_inventory(self.root)

    def test_stale_generated_file_fails(self):
        path = self.root / "crawl-ref/docs/zh/quickstart.txt"
        path.write_text(path.read_text(encoding="utf-8") + "stale\n", encoding="utf-8")
        with self.assertRaisesRegex(MODULE.InventoryError, "generated guide is stale"):
            MODULE.build_inventory(self.root)

    def test_glossary_change_rebinds_inventory_and_stales_review_docs(self):
        original = MODULE.build_inventory(self.root)
        self._write_review_docs(original)
        MODULE.validate_review_docs(self.root, original)

        glossary = self.root / "docs/glossary.md"
        glossary.write_text(
            glossary.read_text(encoding="utf-8") + "\n<!-- mutation -->\n",
            encoding="utf-8")
        changed = MODULE.build_inventory(self.root)
        self.assertNotEqual(original["glossary_sha256"],
                            changed["glossary_sha256"])
        self.assertNotEqual(original["inventory_digest"],
                            changed["inventory_digest"])
        self.assertEqual(changed["glossary_sha256"],
                         changed["inputs"]["docs/glossary.md"])
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "review evidence is missing or stale"):
            MODULE.validate_review_docs(self.root, changed)

    def test_missing_glossary_fails_closed(self):
        (self.root / "docs/glossary.md").unlink()
        with self.assertRaisesRegex(MODULE.InventoryError, "missing glossary"):
            MODULE.build_inventory(self.root)

    def test_review_identity_and_terminal_conclusion_contract(self):
        payload = MODULE.build_inventory(self.root)
        rows = [(card["stable_id"], "keep") for card in payload["cards"]]
        self._write_review_docs(payload, rows)
        MODULE.validate_review_docs(self.root, payload)
        self.assertEqual(payload["review_coverage"]["concluded"], len(rows))

        self._write_review_docs(payload, [*rows, rows[0]])
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "duplicate review identities"):
            MODULE.validate_review_results(self.root, payload)

        self._write_review_docs(payload, rows[1:])
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "missing review identities"):
            MODULE.validate_review_results(self.root, payload)

        invalid = [*rows]
        invalid[0] = (invalid[0][0], "inventory-pass")
        self._write_review_docs(payload, invalid)
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "non-terminal review conclusions"):
            MODULE.validate_review_results(self.root, payload)

        reordered = [rows[1], rows[0], *rows[2:]]
        self._write_review_docs(payload, reordered)
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "review identity order differs"):
            MODULE.validate_review_results(self.root, payload)

        self._write_review_docs(payload, rows)
        results = self.root / "docs/guide-review-results.md"
        text = results.read_text(encoding="utf-8")
        text = text.replace(" | `keep` | E |", " |  | E |", 1)
        results.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "identity/conclusion field is invalid"):
            MODULE.validate_review_results(self.root, payload)

        self._write_review_docs(payload, rows)
        text = results.read_text(encoding="utf-8")
        text = text.replace(" | E | Z |", " |  | Z |", 1)
        results.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "required field is empty"):
            MODULE.validate_review_results(self.root, payload)


if __name__ == "__main__":
    unittest.main()
