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


def codex_role_body(role: str) -> str:
    text = (ROOT / ".codex/agents" / f"{role}.toml").read_text()
    match = re.search(r"developer_instructions = (?P<quote>'''|\"\"\")\n", text)
    if match is None:
        raise AssertionError(f"missing developer_instructions for {role}")
    quote = match.group("quote")
    suffix = f"\n{quote}\n"
    if not text.endswith(suffix):
        raise AssertionError(f"malformed developer_instructions for {role}")
    return text[match.end():-len(suffix)].rstrip("\n")


def pi_role_body(role: str) -> str:
    text = (ROOT / ".pi/agents" / f"{role}.md").read_text()
    separator = "\n---\n"
    if not text.startswith("---\n") or separator not in text:
        raise AssertionError(f"malformed Pi frontmatter for {role}")
    return text.split(separator, 1)[1].lstrip("\n").rstrip("\n")


class PolicySyncTests(unittest.TestCase):
    def test_active_runtime_agents_are_policy_targets(self) -> None:
        self.assertIn(".codex/agents/crawl-coder.toml", SYNC.TARGETS["i18n-safety"])
        self.assertIn(".codex/agents/translation-reviewer.toml",
                      SYNC.TARGETS["review-contract"])
        self.assertIn(".pi/agents/zh-translator.md", SYNC.TARGETS["asset-ownership"])
        context_skill = ".agents/skills/dcss-translation-context/SKILL.md"
        for policy in ("i18n-safety", "review-contract", "asset-ownership"):
            self.assertNotIn(context_skill, SYNC.TARGETS[policy])
        for targets in SYNC.TARGETS.values():
            self.assertFalse(any(path.startswith((".claude/agents/",
                                                  ".claude/skills/",
                                                  ".opencode/"))
                                 for path in targets))

    def test_verification_authoring_has_exact_role_scope(self) -> None:
        self.assertEqual(
            {
                ".codex/agents/crawl-coder.toml",
                ".codex/agents/zh-code-reviewer.toml",
                ".pi/agents/crawl-coder.md",
                ".pi/agents/zh-code-reviewer.md",
            },
            set(SYNC.TARGETS["verification-authoring"]),
        )

    def test_translation_integrity_has_exact_writer_scope(self) -> None:
        self.assertEqual(
            {
                ".codex/agents/zh-translator.toml",
                ".pi/agents/zh-translator.md",
            },
            set(SYNC.TARGETS["translation-integrity"]),
        )

    def test_active_config_roots_are_scanned(self) -> None:
        relative_roots = {path.relative_to(ROOT).as_posix() for path in CHECK.CONFIG_ROOTS}
        self.assertEqual({".agents/skills", ".pi/agents", ".codex/agents"},
                         relative_roots)

    def test_shared_project_role_bodies_match_across_runtimes(self) -> None:
        for role in ("crawl-coder", "zh-translator", "translation-reviewer",
                     "zh-code-reviewer"):
            with self.subTest(role=role):
                self.assertEqual(codex_role_body(role), pi_role_body(role))

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
