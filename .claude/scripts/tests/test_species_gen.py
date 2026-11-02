#!/usr/bin/env python3
"""Guard the species generator's index-paired fake mutation arrays.

`mutation.cc` pairs terse and verbose fake mutations by index, so a species
description that provides only one form must keep an empty slot instead of
shrinking one array.  Regression for the mottled draconian out-of-bounds read.
"""
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "crawl-ref/source/util/species-gen.py"
SPECIES_DIR = ROOT / "crawl-ref/source/dat/species"
TEMPLATES = ROOT / "crawl-ref/source/util/species-gen"


def _entries(rendered: str) -> list[str]:
    return re.findall(r'"(?:[^"\\]|\\.)*"', rendered.strip())


class SpeciesFakeMutationPairingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temporary.name)
        cls.proc = subprocess.run(
            [sys.executable, str(GENERATOR), str(SPECIES_DIR), str(TEMPLATES),
             str(cls.output / "species-data.h"), str(cls.output / "aptitudes.h"),
             str(cls.output / "species-groups.h"), str(cls.output / "species-type.h")],
            text=True, capture_output=True, check=False)
        cls.addClassCleanup(cls.temporary.cleanup)

    def test_generator_succeeds(self):
        self.assertEqual(0, self.proc.returncode, self.proc.stderr)

    def test_species_with_one_form_keeps_paired_empty_slot(self):
        self.assertEqual(0, self.proc.returncode, self.proc.stderr)
        text = (self.output / "species-data.h").read_text(encoding="utf-8")
        for enum in ("SP_MOTTLED_DRACONIAN",):
            with self.subTest(enum=enum):
                marker = f"{{  {enum},"
                start = text.index(marker)
                block = text[start:text.index("\n},", start)]
                # Verbose, then terse fake mutations are the first two
                # quoted initializer lists (the aptitude list has no leading
                # string literal).
                lists = [line.strip() for line in block.splitlines()
                         if line.strip().startswith('{ "')]
                self.assertGreaterEqual(len(lists), 2, block)
                verbose, terse = lists[0], lists[1]
                self.assertEqual(2, len(_entries(verbose)), verbose)
                self.assertEqual(2, len(_entries(terse)), terse)
                self.assertEqual('""', _entries(terse)[1],
                                 f"{enum} must keep the empty terse slot")


if __name__ == "__main__":
    unittest.main()
