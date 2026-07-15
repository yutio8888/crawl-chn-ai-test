#!/usr/bin/env python3

from pathlib import Path
import importlib.util
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "sync_agent_policies", ROOT / ".claude/scripts/sync_agent_policies.py"
)
SYNC = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SYNC)

CHECK_SPEC = importlib.util.spec_from_file_location(
    "check_agent_policies", ROOT / ".claude/scripts/check_agent_policies.py"
)
CHECK = importlib.util.module_from_spec(CHECK_SPEC)
assert CHECK_SPEC.loader is not None
CHECK_SPEC.loader.exec_module(CHECK)


class PolicySyncTests(unittest.TestCase):
    def test_replace_preserves_yaml_frontmatter(self) -> None:
        original = "---\nname: reviewer\n---\n\n# Title\n\n<!-- BEGIN GENERATED: p -->\nold\n<!-- END GENERATED: p -->\n"
        block = "<!-- BEGIN GENERATED: p -->\nnew\n<!-- END GENERATED: p -->"
        updated = SYNC.replace_block(original, "p", block)
        self.assertTrue(updated.startswith("---\nname: reviewer\n---\n"))
        self.assertIn("\n# Title\n", updated)
        self.assertIn("\nnew\n", updated)

    def test_replace_preserves_toml_string_delimiters(self) -> None:
        original = "developer_instructions = '''\n<!-- BEGIN GENERATED: p -->\nold\n<!-- END GENERATED: p -->\n'''\n"
        block = "<!-- BEGIN GENERATED: p -->\nnew\n<!-- END GENERATED: p -->"
        updated = SYNC.replace_block(original, "p", block)
        self.assertTrue(updated.startswith("developer_instructions = '''\n"))
        self.assertTrue(updated.endswith("\n'''\n"))

    def test_missing_block_is_rejected_instead_of_inserting_unsafely(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing or malformed"):
            SYNC.replace_block("---\nname: x\n---\n", "p", "block")

    def test_multiline_static_translation_initializer_is_forbidden(self) -> None:
        unsafe = 'static const char *verbs[] = {\n    T_("open"), T_("spit")\n};'
        matches = [reason for pattern, reason in CHECK.FORBIDDEN.items()
                   if re.search(pattern, unsafe, re.MULTILINE | re.DOTALL)]
        self.assertIn("persistent static T_ initializer", matches)

    def test_markdown_bold_log_interpretation_ban_is_forbidden(self) -> None:
        unsafe = "Do **not** summarize, filter, or interpret script output."
        matches = [reason for pattern, reason in CHECK.FORBIDDEN.items()
                   if re.search(pattern, unsafe, re.MULTILINE | re.DOTALL)]
        self.assertIn("ban on required log interpretation", matches)


if __name__ == "__main__":
    unittest.main()
