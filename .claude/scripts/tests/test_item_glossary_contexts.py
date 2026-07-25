#!/usr/bin/env python3

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
CHECKER = SCRIPTS / "check_item_terms.py"
EXPORTER = SCRIPTS / "export_omegat_glossary.py"

GLOSSARY = """\
<!-- domain:items -->
<!-- item-name-terms -->
| EN | ZH | Scope / comment |
|----|----|----------------|
| `armour ego full name\\|infusion` | 灌注 | armour ego context key |
"""


class ItemGlossaryContextTest(unittest.TestCase):
    def run_script(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *arguments],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    def test_exporter_decodes_escaped_context_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "glossary.md"
            output = Path(temp_dir) / "glossary.utf8"
            source.write_text(GLOSSARY, encoding="utf-8")

            result = self.run_script(
                str(EXPORTER), "--source", str(source), "--output", str(output)
            )

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "armour ego full name|infusion\t灌注\t"
                "domain=items; source=EN/ZH; "
                "Scope / comment=armour ego context key\n",
            )

    def test_exporter_rejects_unescaped_pipe_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "glossary.md"
            output = Path(temp_dir) / "glossary.utf8"
            source.write_text(GLOSSARY, encoding="utf-8")
            source.write_text(
                GLOSSARY.replace("\\|infusion", "|infusion"),
                encoding="utf-8",
            )
            result = self.run_script(
                str(EXPORTER),
                "--source",
                str(source),
                "--output",
                str(output),
            )

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("unescaped pipe", result.stdout)

    def test_item_checker_accepts_decoded_context_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            glossary = Path(temp_dir) / "glossary.md"
            omegat = Path(temp_dir) / "glossary.utf8"
            decisions = Path(temp_dir) / "decisions.md"
            glossary.write_text(GLOSSARY, encoding="utf-8")
            omegat.write_text(
                "armour ego full name|infusion\t灌注\ttest\n",
                encoding="utf-8",
            )
            decisions.write_text(
                "### D-B-TEST\n- 旧译：绝不会出现的旧译甲乙 → **新译**\n",
                encoding="utf-8",
            )

            result = self.run_script(
                str(CHECKER),
                "--glossary",
                str(glossary),
                "--decisions",
                str(decisions),
                "--omegat",
                str(omegat),
            )

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn(
                "OK: armour ego full name|infusion → 灌注", result.stdout
            )

    def test_item_checker_rejects_unescaped_pipe_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            glossary = Path(temp_dir) / "glossary.md"
            omegat = Path(temp_dir) / "glossary.utf8"
            decisions = Path(temp_dir) / "decisions.md"
            glossary.write_text(
                GLOSSARY.replace("\\|infusion", "|infusion"),
                encoding="utf-8",
            )
            omegat.write_text(
                "armour ego full name|infusion\t灌注\ttest\n",
                encoding="utf-8",
            )
            decisions.write_text(
                "### D-B-TEST\n- 旧译：绝不会出现的旧译甲乙 → **新译**\n",
                encoding="utf-8",
            )

            result = self.run_script(
                str(CHECKER),
                "--glossary",
                str(glossary),
                "--decisions",
                str(decisions),
                "--omegat",
                str(omegat),
            )

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("unescaped pipe", result.stdout)


if __name__ == "__main__":
    unittest.main()
