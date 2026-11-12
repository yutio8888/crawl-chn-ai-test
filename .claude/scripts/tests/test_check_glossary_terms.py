#!/usr/bin/env python3
"""Include glossary gate regressions in the existing tooling test runner."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_check_glossary_terms import CheckGlossaryTermsTest

if __name__ == "__main__":
    unittest.main()
