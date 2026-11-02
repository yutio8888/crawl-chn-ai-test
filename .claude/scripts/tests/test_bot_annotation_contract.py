#!/usr/bin/env python3
"""Bind the PTY bot's annotation expectations to the actual display code.

`dgn-overview.cc` renders the annotation prompt and the stored note list with
either `_overview_level_name()` (translated short branch name + depth, e.g.
地牢:1 in ZH) or `level_id::describe()` (canonical D:1). The bot must assert
whichever form the code really uses, so a display change cannot silently leave
the regression bot checking the old token.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OVERVIEW = ROOT / "crawl-ref/source/dgn-overview.cc"
BOT = ROOT / ".claude/scripts/zh_console_ui_bot.py"

LOCALIZED = "_overview_level_name"
CANONICAL = "describe("


def _region(source: str, start_marker: str, end_marker: str = None,
            window: int = None) -> str:
    start = source.index(start_marker)
    if end_marker is not None:
        return source[start:source.index(end_marker, start)]
    return source[start:start + window]


def annotation_display_forms(source: str) -> tuple[str, str]:
    """Return (prompt form, list form) as 'localized' or 'canonical'."""
    # The level name is computed just before the make_stringf() call.
    marker = source.index('Add new annotation for %s')
    prompt = source[max(0, marker - 400):marker + 300]
    stored = _region(source, "static const string _get_coloured_level_annotation"
                     "(level_id li)\n{", "\n}", window=400)

    def classify(text: str) -> str:
        has_localized = LOCALIZED in text
        has_canonical = CANONICAL in text
        if has_localized and not has_canonical:
            return "localized"
        if has_canonical and not has_localized:
            return "canonical"
        raise AssertionError(f"ambiguous annotation display form:\n{text}")

    return classify(prompt), classify(stored)


def bot_expectations(source: str) -> tuple[str, list[str]]:
    prompt = re.search(
        r"workflow:annotation:text',\s*annotation_prompt,\s*\('([^']+)'", source)
    overview = re.search(
        r"workflow:annotation:overview',\s*overview,\s*\(([^)]*)\)", source)
    if prompt is None or overview is None:
        raise AssertionError("bot annotation expectations not found")
    return prompt.group(1), re.findall(r"'([^']*)'", overview.group(1))


class BotAnnotationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.overview_source = OVERVIEW.read_text(encoding="utf-8")
        cls.bot_source = BOT.read_text(encoding="utf-8")
        cls.prompt_form, cls.list_form = annotation_display_forms(
            cls.overview_source)
        cls.prompt_expectation, cls.overview_expectation = bot_expectations(
            cls.bot_source)

    def test_both_annotation_sites_use_the_same_display_form(self):
        self.assertEqual(
            self.prompt_form, self.list_form,
            "annotation prompt and stored note list must render level names the "
            "same way; a partial change breaks the bot contract")

    def test_bot_expectation_matches_the_actual_display_form(self):
        if self.prompt_form == "canonical":
            token = "D:1"
        else:
            token = "地牢:1"
        self.assertEqual(f"为{token}添加新注释", self.prompt_expectation)
        self.assertIn(token, self.overview_expectation)

    def test_overview_title_expectation_is_localized(self):
        # The title comes from the zh asset; the bot pins the localized form so
        # a title regression cannot pass unnoticed.
        self.assertEqual("地牢总览", self.overview_expectation[0])


if __name__ == "__main__":
    unittest.main()
