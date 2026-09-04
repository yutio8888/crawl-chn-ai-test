#!/usr/bin/env python3
"""Source invariants for the Android quick-access drawer pages.

The drawer is SDL Tiles UI with no headless harness, so these are static
checks over the one file that implements it plus the description database
keys its labels resolve against.
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


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def database_keys(path: Path) -> set:
    keys = set()
    for entry in read(path).split("%%%%"):
        stripped = entry.strip()
        if stripped:
            keys.add(stripped.splitlines()[0].strip())
    return keys


class QuickAccessPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = read(SOURCE)

    def test_icon_grid_holds_at_most_twelve_entries_per_page(self) -> None:
        self.assertIn("static const int QUICK_ICON_ROWS = 2;", self.source)
        self.assertIn("static const int QUICK_ICON_COLS = 6;", self.source)
        self.assertIn(
            "static const int QUICK_ICON_PAGE_SIZE = "
            "QUICK_ICON_ROWS * QUICK_ICON_COLS;",
            self.source,
        )

    def test_entry_points_require_a_non_empty_list(self) -> None:
        for guard, label in (
            ("if (!spell_entries.empty())", "Quick Cast"),
            ("if (!ability_entries.empty())", "Quick Abilities"),
        ):
            self.assertIn(guard, self.source)
            guarded = self.source.index(guard)
            entry = self.source.index('"%s")' % label, guarded)
            # The entry button is created inside the guarded block, before the
            # next top-level statement of the main page.
            self.assertLess(entry - guarded, 400, label)

    def test_ordinary_spell_and_ability_commands_are_preserved(self) -> None:
        for command in ("CMD_DISPLAY_SPELLS", "CMD_USE_ABILITY"):
            self.assertIn(command, self.source)

    def test_paging_is_explicit_and_shows_current_over_total(self) -> None:
        self.assertIn('"Previous"', self.source)
        self.assertIn('"Next"', self.source)
        self.assertIn('make_stringf("%d / %d", shown + 1, icon_page_count)',
                      self.source)
        self.assertIn('make_stringf("1 / %d", icon_page_count)', self.source)

    def test_selection_uses_the_normal_cast_and_activate_calls(self) -> None:
        # z reaches cast_a_spell(true, ...); Z would pass false.
        self.assertIn("cast_a_spell(true, quick_spell)", self.source)
        self.assertNotIn("cast_a_spell(false", self.source)
        # a reaches activate_talent() with a freshly resolved talent.
        self.assertIn("const talent tal = get_talent(quick_ability);",
                      self.source)
        self.assertIn("|| !activate_talent(tal))", self.source)
        # Nothing may cast or activate behind those calls.
        self.assertNotIn("your_spells(", self.source)

    def test_selection_runs_only_after_the_drawer_layout_is_popped(self) -> None:
        popped = self.source.rindex("ui::pop_layout();")
        self.assertLess(popped, self.source.index("cast_a_spell(true,"))
        self.assertLess(popped, self.source.index("activate_talent(tal)"))

    def test_long_press_describes_without_also_activating(self) -> None:
        held = self.source.index("if (held && on_long_press)")
        cancelled = self.source.index("active = false;", held)
        invoked = self.source.index("on_long_press();", held)
        swallowed = self.source.index("return true;", invoked)
        self.assertLess(cancelled, invoked)
        self.assertLess(invoked, swallowed)
        self.assertIn("describe_spell((spell_type) idx);", self.source)
        self.assertIn("describe_ability((ability_type) idx);", self.source)

    def test_long_press_state_is_reset_on_release_and_on_leave(self) -> None:
        # Leaving the button and releasing it both end the pending gesture, so
        # no press instant can outlive the gesture that started it.
        leave = self.source.index("ui::Event::Type::MouseLeave")
        self.assertIn("m_pressing = false;",
                      self.source[leave:self.source.index("else if", leave)])
        release = self.source.index("const bool held = m_pressing")
        self.assertIn("m_pressing = false;",
                      self.source[release:self.source.index("if (held", release)])

    def test_every_menu_label_resolves_in_both_description_databases(self) -> None:
        used = {"%s|%s" % match for match in MENU_TEXT_CALL.findall(self.source)}
        self.assertIn("android command menu|Quick Cast", used)
        self.assertIn("android command menu|Quick Abilities", used)
        for path in (DESCRIPT_EN, DESCRIPT_ZH):
            missing = sorted(used - database_keys(path))
            self.assertEqual([], missing, str(path))


if __name__ == "__main__":
    unittest.main()
