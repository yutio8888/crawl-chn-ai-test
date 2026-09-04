#!/usr/bin/env python3
"""Source invariants for the Android quick-access drawer pages.

The drawer is SDL Tiles UI with no headless harness, so these are static
checks. They cover only what could silently regress: the acceptance shape of
the grid, the guards that keep the normal command paths from being bypassed,
and the description keys the labels resolve against.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "crawl-ref/source/topbar-drawer.cc"
DESCRIPT_EN = ROOT / "crawl-ref/source/dat/descript/commands.txt"
DESCRIPT_ZH = ROOT / "crawl-ref/source/dat/descript/zh/commands.txt"

MENU_TEXT_CALL = re.compile(
    r'_command_menu_text\(\s*"(android command menu(?: summary)?)"\s*,\s*'
    r'"([^"]+)"\s*\)',
    re.DOTALL,
)


def database_keys(path: Path) -> set:
    keys = set()
    for entry in path.read_text(encoding="utf-8").split("%%%%"):
        stripped = entry.strip()
        if stripped:
            keys.add(stripped.splitlines()[0].strip())
    return keys


class QuickAccessPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SOURCE.read_text(encoding="utf-8")

    def block_after(self, anchor: str) -> str:
        """The brace-delimited block that follows `anchor`."""
        start = self.source.index("{", self.source.index(anchor))
        depth = 0
        for offset in range(start, len(self.source)):
            if self.source[offset] == "{":
                depth += 1
            elif self.source[offset] == "}":
                depth -= 1
                if depth == 0:
                    return self.source[start:offset + 1]
        self.fail("unterminated block after %r" % anchor)

    def constant(self, name: str) -> int:
        match = re.search(r"\b%s\s*=\s*(\d+)\s*;" % name, self.source)
        self.assertIsNotNone(match, name)
        return int(match.group(1))

    def test_icon_grid_is_two_by_six_per_page(self) -> None:
        self.assertEqual(2, self.constant("QUICK_ICON_ROWS"))
        self.assertEqual(6, self.constant("QUICK_ICON_COLS"))
        self.assertIn("QUICK_ICON_PAGE_SIZE = QUICK_ICON_ROWS * QUICK_ICON_COLS",
                      self.source)

    def test_entry_points_require_a_non_empty_list(self) -> None:
        for guard, label in (
            ("if (!spell_entries.empty())", "Quick Cast"),
            ("if (!ability_entries.empty())", "Quick Abilities"),
        ):
            self.assertIn('"%s"' % label, self.block_after(guard))

    def test_ordinary_spell_and_ability_commands_are_preserved(self) -> None:
        for command in ("CMD_DISPLAY_SPELLS", "CMD_USE_ABILITY"):
            self.assertIn(command, self.source)

    def test_paging_is_explicit_and_shows_current_over_total(self) -> None:
        self.assertIn('"Previous"', self.source)
        self.assertIn('"Next"', self.source)
        self.assertRegex(self.source, r'"%d / %d"')
        # Repeated in-place presses must not leave the drawer scroller holding
        # the drag origin the tap itself created.
        self.assertIn("cancel_drag()", self.block_after("const auto turn_page ="))

    def test_selection_uses_the_normal_cast_and_activate_calls(self) -> None:
        # z reaches cast_a_spell(true, ...); Z would pass false. Nothing may
        # cast or activate behind those calls.
        self.assertIn("cast_a_spell(true, quick_spell)", self.source)
        self.assertNotIn("cast_a_spell(false", self.source)
        self.assertNotIn("your_spells(", self.source)
        self.assertIn("get_talent(quick_ability)", self.source)
        self.assertIn("activate_talent(tal)", self.source)

    def test_selection_runs_only_after_the_drawer_layout_is_popped(self) -> None:
        popped = self.source.rindex("ui::pop_layout();")
        self.assertLess(popped, self.source.index("cast_a_spell(true,"))
        self.assertLess(popped, self.source.index("activate_talent(tal)"))

    def test_description_is_reached_by_the_right_button(self) -> None:
        # SDLActivity.onTouch() replays a held touch as the right button at
        # release, so the drawer must not try to time the press itself.
        handler = self.block_after("class QuickButton final : public MenuButton")
        self.assertIn("ui::MouseEvent::Button::Right", handler)
        self.assertIn("on_describe()", handler)
        for absent in ("QUICK_LONG_PRESS", "m_pressing", "m_press_ticks",
                       "get_ticks", "windowmanager.h"):
            self.assertNotIn(absent, self.source, absent)
        describe = self.block_after("button->on_describe =")
        self.assertIn("describe_spell((spell_type) idx);", describe)
        self.assertIn("describe_ability((ability_type) idx);", describe)
        self.assertIn("cancel_drag()", describe)

    def test_every_menu_label_resolves_in_both_description_databases(self) -> None:
        used = {"%s|%s" % match for match in MENU_TEXT_CALL.findall(self.source)}
        self.assertIn("android command menu|Quick Cast", used)
        self.assertIn("android command menu|Quick Abilities", used)
        for path in (DESCRIPT_EN, DESCRIPT_ZH):
            self.assertEqual([], sorted(used - database_keys(path)), str(path))


if __name__ == "__main__":
    unittest.main()
