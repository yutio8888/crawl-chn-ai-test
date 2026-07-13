import hashlib
import tempfile
import unittest
from pathlib import Path

import glossary_query


SAMPLE = """# Glossary

<!-- domain:core -->
## Core

| EN | ZH | Note |
|----|----|------|
| cast | 施法（通用） / 吟诵（仪式） | context matters |

---

<!-- domain:items -->
## Items

| EN | ZH |
|----|----|
| broad axe | 阔刃斧 |

---

<!-- domain:rules -->
## Rules

- Preserve `%s`.
"""


class GlossaryQueryTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "glossary.md"
        self.path.write_text(SAMPLE, encoding="utf-8")

    def tearDown(self):
        self.tempdir.cleanup()

    def test_parses_domains_and_multiple_targets(self):
        sections = glossary_query.parse_glossary(self.path)
        self.assertEqual({"core", "items", "rules"}, set(sections))
        self.assertEqual(("施法（通用）", "吟诵（仪式）"), sections["core"].terms[0].targets)

    def test_infers_item_domain_and_always_includes_rules(self):
        domains = glossary_query.infer_domains("translate weapon names", ["dat/items.txt"])
        self.assertIn("items", domains)
        self.assertIn("core", domains)
        self.assertIn("rules", domains)

    def test_context_reports_current_hash(self):
        context = glossary_query.build_context(
            self.path,
            "translate broad axe",
            [],
            [],
            [],
            20,
            10_000,
        )
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), context["sha256"])
        self.assertTrue(any(term["source"] == "broad axe" for term in context["terms"]))
        self.assertIn("rules", context["guidance"])
        self.assertNotIn("spells", context["domains"])


if __name__ == "__main__":
    unittest.main()
