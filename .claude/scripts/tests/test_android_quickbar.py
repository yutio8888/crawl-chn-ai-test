#!/usr/bin/env python3
"""Source invariants for the Android quick-access drawer pages and quick row.

Both are SDL Tiles UI with no headless harness, so these are static checks.
They cover only what could silently regress: the acceptance shape of the grid
and of the persistent bottom row, the guards that keep the normal command paths
from being bypassed, and the description keys the labels resolve against.
"""

from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "crawl-ref/source/topbar-drawer.cc"
DESCRIPT_EN = ROOT / "crawl-ref/source/dat/descript/commands.txt"
DESCRIPT_ZH = ROOT / "crawl-ref/source/dat/descript/zh/commands.txt"
TILESDL_CC = ROOT / "crawl-ref/source/tilesdl.cc"
TILESDL_H = ROOT / "crawl-ref/source/tilesdl.h"
SPELL_REGION_H = ROOT / "crawl-ref/source/tilereg-spl.h"
SPELL_REGION_CC = ROOT / "crawl-ref/source/tilereg-spl.cc"
ABILITY_REGION_CC = ROOT / "crawl-ref/source/tilereg-abl.cc"
ANDROID_RES = ROOT / "crawl-ref/source/android-project/app/src/main/res"
ANDROID_MOBILE_LAYOUT = ANDROID_RES / "layout/keyboard_mobile.xml"
UI_CC = ROOT / "crawl-ref/source/ui.cc"

MENU_TEXT_CALL = re.compile(
    r'_command_menu_text\(\s*"(android command menu(?: summary)?)"\s*,\s*'
    r'"([^"]+)"\s*\)',
    re.DOTALL,
)


def block_after(source: str, anchor: str) -> str:
    """The brace-delimited block that follows `anchor`."""
    start = source.index("{", source.index(anchor))
    depth = 0
    for offset in range(start, len(source)):
        if source[offset] == "{":
            depth += 1
        elif source[offset] == "}":
            depth -= 1
            if depth == 0:
                return source[start:offset + 1]
    raise AssertionError("unterminated block after %r" % anchor)


def statement(source: str, lhs: str) -> str:
    """The single statement assigning `lhs`, without its trailing semicolon."""
    match = re.search(re.escape(lhs) + r"\s*=(.*?);", source, re.DOTALL)
    if match is None:
        raise AssertionError("no assignment to %r" % lhs)
    return match.group(1)


def database_keys(path: Path) -> set:
    keys = set()
    for entry in path.read_text(encoding="utf-8").split("%%%%"):
        stripped = entry.strip()
        if stripped:
            keys.add(stripped.splitlines()[0].strip())
    return keys


class AndroidFirstRunTests(unittest.TestCase):
    def string_names(self, qualifier: str) -> set[str]:
        root = ET.parse(ANDROID_RES / qualifier / "strings.xml").getroot()
        return {node.attrib["name"] for node in root if "name" in node.attrib}

    def test_generic_chinese_resources_cover_the_android_shell(self) -> None:
        # A Chinese language with a non-CN region resolves values-zh rather
        # than values-zh-rCN. It must not silently inherit visible English UI.
        default_names = self.string_names("values")
        zh_names = self.string_names("values-zh")
        self.assertEqual(default_names, zh_names)

    def test_android_shell_retains_english_fallback_resources(self) -> None:
        # Check the fallback artifact, not a simulated Android locale resolver.
        # Activity resource selection still needs a device smoke test in both
        # Chinese and an unsupported locale.
        root = ET.parse(ANDROID_RES / "values/strings.xml").getroot()
        strings = {node.attrib["name"]: node.text
                   for node in root.findall("string")}
        expected = {
            "start_game": "Start Game",
            "edit_rc": "Edit Init File",
            "virtual_keyboard": "Virtual keyboard",
            "extra_keyboard": "Extra directional pad",
            "keyboard_size": "Keyboard size",
            "keyboard_explore": "Explore",
            "keyboard_autofight": "Auto-fight",
            "keyboard_rest": "Wait",
            "keyboard_inventory": "Inventory",
            "keyboard_pickup": "Pick up",
        }
        for name, text in expected.items():
            self.assertEqual(text, strings[name], name)

    def test_compact_action_buttons_have_localized_accessibility_names(self) -> None:
        root = ET.parse(ANDROID_MOBILE_LAYOUT).getroot()
        android = "{http://schemas.android.com/apk/res/android}"
        expected = {
            "key_mobile_explore": "@string/keyboard_explore",
            "key_mobile_autofight": "@string/keyboard_autofight",
            "key_mobile_5": "@string/keyboard_rest",
            "key_mobile_inventory": "@string/keyboard_inventory",
            "key_mobile_pickup": "@string/keyboard_pickup",
        }
        actual = {}
        for node in root.iter("Button"):
            resource_id = node.attrib.get(android + "id", "").removeprefix("@+id/")
            if resource_id in expected:
                actual[resource_id] = node.attrib.get(android + "contentDescription")
        self.assertEqual(expected, actual)

    def test_pointer_buttons_are_hit_tested_without_prior_motion(self) -> None:
        source = UI_CC.read_text(encoding="utf-8")
        event_loop = block_after(source, "void pump_events(int wait_event_timeout)")
        pointer_cases = event_loop[event_loop.index("case WME_MOUSEBUTTONDOWN:"):
                                   event_loop.index("default:")]
        for event_type in ("WME_MOUSEBUTTONDOWN", "WME_MOUSEBUTTONUP",
                           "WME_MOUSEMOTION"):
            self.assertIn("case %s:" % event_type, pointer_cases)
        self.assertIn("ui_root.update_hover_path();", pointer_cases)


class QuickAccessPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SOURCE.read_text(encoding="utf-8")

    def block_after(self, anchor: str) -> str:
        return block_after(self.source, anchor)

    def constant(self, name: str) -> int:
        match = re.search(r"\b%s\s*=\s*(\d+)\s*;" % name, self.source)
        self.assertIsNotNone(match, name)
        return int(match.group(1))

    def test_cards_keep_twelve_entries_per_page_and_wrap_display_text(self) -> None:
        # Static regression checks only; actual fitting and scrolling need SDL.
        self.assertEqual(12, self.constant("QUICK_ICON_PAGE_SIZE"))
        self.assertNotIn("QUICK_ICON_COLS", self.source)
        self.assertIn("entry.name = spell_title(spell)", self.source)
        self.assertIn("entry.name = ability_name(tal.which)", self.source)
        self.assertIn("entry.cost = make_cost_description(tal.which)", self.source)
        for label in ("name", "caption", "reason"):
            self.assertIn(f"{label}->set_wrap_text(true)", self.source)
        self.assertIn('T_("MP")', self.source)

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


class QuickRowTests(unittest.TestCase):
    """The persistent single icon row along the bottom of the Android surface."""

    def setUp(self) -> None:
        self.tiles = TILESDL_CC.read_text(encoding="utf-8")
        self.header = TILESDL_H.read_text(encoding="utf-8")

    def fn(self, signature: str) -> str:
        return block_after(self.tiles, signature)

    def test_row_reuses_the_existing_region_classes(self) -> None:
        # No new UI class and no JNI/Java state: two more instances of the
        # regions the sidebar already uses, owned by TilesFramework.
        self.assertRegex(self.header, r"SpellRegion\s+\*m_region_quick_spl;")
        self.assertRegex(self.header, r"AbilityRegion\s+\*m_region_quick_abl;")
        init = self.fn("bool TilesFramework::initialise()")
        self.assertIn("m_region_quick_spl = new SpellRegion(m_init, true);", init)
        self.assertIn("m_region_quick_abl = new AbilityRegion(m_init);", init)
        # separate instances, not aliases of the sidebar regions
        self.assertIn("m_region_spl  = new SpellRegion(m_init);", init)
        self.assertIn("m_region_abl  = new AbilityRegion(m_init);", init)
        shutdown = self.fn("void TilesFramework::shutdown()")
        for member in ("m_region_quick_spl", "m_region_quick_abl"):
            self.assertIn("delete %s;" % member, shutdown)
            self.assertIn("%s = nullptr;" % member, shutdown)

    def test_quick_spell_row_keeps_z_semantics_without_moving_the_sidebar(self) -> None:
        # Phase B settled on cast_a_spell(true, ...), what z reaches after its
        # own selection step. The sidebar SpellRegion must keep its own call, so
        # the adaptation is one defaulted constructor flag.
        header = SPELL_REGION_H.read_text(encoding="utf-8")
        self.assertRegex(
            header,
            r"SpellRegion\(const TileRegionInit &init,\s*bool check_range = false\)")
        source = SPELL_REGION_CC.read_text(encoding="utf-8")
        self.assertIn("cast_a_spell(m_check_range, spell)", source)
        for absent in ("cast_a_spell(false", "cast_a_spell(true"):
            self.assertNotIn(absent, source, absent)

    def test_abilities_use_the_unchanged_normal_activate_path(self) -> None:
        source = ABILITY_REGION_CC.read_text(encoding="utf-8")
        self.assertIn("talent tal = get_talent(ability);", source)
        self.assertIn("activate_talent(tal)", source)
        self.assertIn("describe_ability(ability);", source)
        # nothing quick-row specific leaked into the shared ability region
        self.assertNotIn("quick", source.lower())

    def test_row_is_reserved_only_while_a_live_list_is_non_empty(self) -> None:
        live = self.fn("void TilesFramework::quick_row_live_lists")
        self.assertIn("you.spell_no > 0", live)
        self.assertIn("your_talents(true).empty()", live)
        supported = self.fn("bool TilesFramework::quick_row_supported")
        for required in ("in_headless_mode()", "uses_top_hud()",
                         "uses_overlay_sidebar()", "!m_map_mode_enabled"):
            self.assertIn(required, supported, required)
        layout = self.fn("void TilesFramework::do_layout()")
        self.assertRegex(
            layout,
            r"m_quick_row_shown\s*=\s*use_top_bar\s*&&\s*"
            r"\(m_quick_row_spells \|\| m_quick_row_abilities\)")
        # both lists empty: no cells at all, so no blank strip is reserved
        self.assertRegex(layout, r"m_region_quick_spl->resize\(0, 0\)")
        self.assertRegex(layout, r"m_region_quick_abl->resize\(0, 0\)")

    def test_row_height_leaves_the_budget_before_tile_arithmetic(self) -> None:
        layout = self.fn("void TilesFramework::do_layout()")
        # the short-surface top-HUD fallback is decided before the branch that
        # derives tile sizes, and it pays for the row
        self.assertLess(layout.index("const int min_tile_h"),
                        layout.index("int tile_avail_h"))
        for lhs in ("const int min_tile_h", "const int expanded_tile_h",
                    "int tile_avail_h"):
            self.assertIn("quick_row_h", statement(layout, lhs), lhs)
        # the dungeon still gets a full LOS out of what is left
        self.assertIn("tile_avail_h / m_region_tile->dy < ENV_SHOW_DIAMETER",
                      layout)
        # message overlay sits directly above the row, which is at the bottom
        self.assertRegex(
            layout,
            r"m_region_msg->place\(0, m_windowsz\.y - quick_row_h - msg_min_h, 0\)")
        self.assertRegex(layout,
                         r"place_quick_row\(m_windowsz\.y - quick_row_h,")

    def test_row_is_one_visual_row_split_by_which_lists_are_live(self) -> None:
        place = self.fn("void TilesFramework::place_quick_row")
        places = re.findall(r"->place\(([^;]*)\);", place)
        self.assertEqual(2, len(places))
        for args in places:
            # both halves share the single bottom row's y
            self.assertIn("row_y", args)
        resizes = re.findall(r"->resize\(([^;]*)\);", place)
        self.assertEqual(2, len(resizes))
        for args in resizes:
            # one cell tall, or no cells at all -- never a second stacked row
            self.assertRegex(args, r"\?\s*1\s*:\s*0\s*$")
        # side by side when both are live, full width for a sole live list
        self.assertRegex(
            place,
            r"spell_cells\s*=\s*spells\s*\?\s*\(abilities\s*\?"
            r"\s*cells\s*/\s*2\s*:\s*cells\)\s*:\s*0")
        self.assertRegex(
            place,
            r"ability_cells\s*=\s*abilities\s*\?\s*cells - spell_cells\s*:\s*0")
        # overflow is left to the regions' own truncation: no paging state
        for absent in ("m_grid_page", "swipe", "turn_page"):
            self.assertNotIn(absent, place, absent)

    def test_row_is_hidden_and_inert_outside_ordinary_command_input(self) -> None:
        for signature in ("void TilesFramework::render_quick_row",
                          "int TilesFramework::handle_quick_row_mouse"):
            block = self.fn(signature)
            for guard in ("!m_quick_row_shown",
                          "m_active_layer != LAYER_NORMAL",
                          "mouse_control::current_mode() != MOUSE_MODE_COMMAND"):
                self.assertIn(guard, block, "%s / %s" % (signature, guard))

    def test_taps_are_handled_by_the_regions_own_command_behaviour(self) -> None:
        quick = self.fn("int TilesFramework::handle_quick_row_mouse")
        self.assertIn("m_region_quick_spl->handle_mouse(event)", quick)
        self.assertIn("m_region_quick_abl->handle_mouse(event)", quick)
        # no bespoke button routing, activation or press timing lives here:
        # the >=500ms Android hold arrives as a right button and the regions
        # already describe on it, and releases already match nothing.
        for absent in ("wm_mouse_event::LEFT", "wm_mouse_event::RIGHT",
                       "get_ticks", "cast_a_spell", "activate_talent",
                       "describe_spell", "describe_ability"):
            self.assertNotIn(absent, quick, absent)
        # the row is a button strip, so no grid cursor or description tag is
        # left drawn over the HUD after a gesture
        self.assertIn("m_region_quick_spl->place_cursor(NO_CURSOR);", quick)
        self.assertIn("m_region_quick_abl->place_cursor(NO_CURSOR);", quick)

    def test_visibility_transition_is_polled_then_deferred(self) -> None:
        # polled on the normal redraw cadence, from inside viewwindow()
        tabs = self.fn("void TilesFramework::update_tabs()")
        self.assertIn("update_quick_row();", tabs)
        self.assertLess(tabs.index("update_quick_row();"),
                        tabs.index("uses_legacy_tabbed_sidebar"))
        poll = self.fn("void TilesFramework::update_quick_row")
        self.assertNotIn("do_layout", poll)
        self.assertNotIn("redraw_screen", poll)
        self.assertIn("m_quick_row_relayout = true;", poll)
        # applied from the input pump instead, never re-entrantly
        getch = self.fn("int TilesFramework::getch_ck()")
        self.assertIn("apply_quick_row_relayout();", getch)
        applied = self.fn("void TilesFramework::apply_quick_row_relayout")
        self.assertIn("m_in_quick_row_relayout", applied)
        self.assertIn("unwind_bool", applied)
        self.assertIn("do_layout();", applied)
        # rebuild the dungeon buffer for the new viewport before anything
        # renders it, as set_map_display() does
        self.assertLess(applied.index("do_layout();"),
                        applied.index("redraw_screen(false);"))

    def test_row_is_drawn_and_dispatched_outside_the_region_layers(self) -> None:
        redraw = self.fn("void TilesFramework::redraw()")
        self.assertIn("render_quick_row();", redraw)
        mouse = self.fn("int TilesFramework::handle_mouse")
        self.assertIn("handle_quick_row_mouse(event)", mouse)
        self.assertLess(mouse.index("handle_quick_row_mouse(event)"),
                        mouse.index("m_layers[m_active_layer]"))
        # never pushed into a layer: layout_statcol() pops the tail of that
        # vector by count when it rebuilds the tabs
        self.assertNotRegex(
            self.tiles,
            r"m_regions\.push_back\(m_region_quick_(spl|abl)\)")


if __name__ == "__main__":
    unittest.main()
