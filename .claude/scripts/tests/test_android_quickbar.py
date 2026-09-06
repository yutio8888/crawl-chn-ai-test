#!/usr/bin/env python3
"""Source invariants for the Android command panel and quick row.

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
            "keyboard_rest": "Rest",
            "keyboard_wait": "Wait",
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
            "key_mobile_5": "@string/keyboard_wait",
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


class QuickAccessPanelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SOURCE.read_text(encoding="utf-8")

    def block_after(self, anchor: str) -> str:
        return block_after(self.source, anchor)

    def command_entries(self) -> list[tuple[str, str, str]]:
        table = self.block_after("const command_entry commands[] =")
        pattern = r'\{"([^"]+)",\s*(TILEG_\w+),\s*(CMD_\w+)\},'
        entries = re.findall(pattern, table)
        # Reject an unparsed initializer, not merely accept a subset.
        self.assertEqual("{}", re.sub(r"\s+", "", re.sub(pattern, "", table)))
        return entries

    def test_cards_wrap_text_without_truncating_the_live_list(self) -> None:
        # Static regression checks only; actual fitting and scrolling need SDL.
        self.assertIn("entry.name = spell_title(spell)", self.source)
        self.assertIn("entry.name = ability_name(tal.which)", self.source)
        self.assertIn("entry.cost = make_cost_description(tal.which)", self.source)
        self.assertIn("set_wrap_text(true)", self.block_after("_drawer_text("))
        section = self.block_after("const auto add_quick_section =")
        self.assertIn("for (const quick_entry &entry : entries)", section)
        self.assertNotRegex(section, r"\b(?:break|continue)\b")
        for value in ("entry.name", "_quick_entry_caption(entry)", "entry.reason"):
            self.assertRegex(section, r"_drawer_text\(formatted_string\(\s*" + re.escape(value))
        self.assertIn('T_("MP")', self.source)

    def test_inline_sections_require_a_non_empty_list(self) -> None:
        section = self.block_after("const auto add_quick_section =")
        self.assertRegex(section, r"if \(entries.empty\(\)\)\s*return;")
        self.assertLess(section.index("entries.empty()"), section.index("content->add_child(title)"))
        for entries, label, spell in (
            ("_quick_spell_entries()", "Quick Cast", "true"),
            ("_quick_ability_entries()", "Quick Abilities", "false"),
        ):
            self.assertIn(f'add_quick_section({entries}, "{label}", {spell});', self.source)

    def test_ordinary_spell_and_ability_commands_are_preserved(self) -> None:
        for command in ("CMD_DISPLAY_SPELLS", "CMD_USE_ABILITY"):
            self.assertIn(command, self.source)

    def test_single_scroller_has_no_page_or_submenu_navigation(self) -> None:
        menu = self.block_after("command_type show_topbar_command_menu")
        description = self.block_after("const auto describe =")
        # The independent modal hint has its own scrolling body. Only the
        # main panel must have a single shared scroller for all its sections.
        panel = menu.replace(description, "", 1)
        self.assertEqual(1, panel.count("make_shared<DrawerScroller>()"))
        self.assertIn("scroller->set_child(content);", panel)
        self.assertIn("content->add_child(command_grid);", menu)
        self.assertIn("content->add_child(grid);", menu)
        for absent in ('"Previous"', '"Next"', '"Back"',
                       "QUICK_ICON_PAGE_SIZE", "turn_page", "show_page"):
            self.assertNotIn(absent, menu)
        self.assertIn("cancel_drag()", self.block_after("const auto describe ="))

    def test_description_escape_is_consumed_before_focus_reset(self) -> None:
        description = self.block_after("const auto describe =")
        self.assertIn("auto popup = make_shared<ui::Popup>(details);", description)
        self.assertIn("details->add_child(detail_scroll);", description)
        handler = block_after(description, "const auto detail_key =")
        exit_guard = block_after(handler, "if (ui::key_exits_popup(event.key(), true))")
        self.assertIn("dismissed = true;", exit_guard)
        self.assertIn("return true;", exit_guard)
        self.assertIn("detail_scroll->on_event(event)", handler)
        for receiver in ("dismiss", "popup"):
            binding = f"{receiver}->on_keydown_event(detail_key);"
            self.assertIn(binding, description)
            self.assertLess(description.index(binding), description.index("ui::run_layout("))
        # Escape must reach the handler on the initially focused close button,
        # before UIRoot can clear focus, and returning must reset the old drag.
        self.assertIn("ui::run_layout(popup, dismissed, dismiss);", description)
        self.assertLess(description.index("ui::run_layout("),
                        description.index("owner->cancel_drag();"))

    def test_child_description_callbacks_do_not_own_their_scroller(self) -> None:
        # The scroller owns content -> buttons -> callbacks. Retaining a
        # shared scroller in either stored description callback leaks that
        # complete tree whenever the menu is dismissed.
        self.assertIn("const weak_ptr<DrawerScroller> weak_scroller = scroller;",
                      self.source)
        self.assertIn("const auto describe = [weak_scroller]", self.source)
        self.assertIn("button->on_describe = [weak_scroller, idx, is_spell]",
                      self.source)
        for anchor in ("const auto describe =",
                       "button->on_describe = [weak_scroller, idx, is_spell]"):
            callback = self.block_after(anchor)
            self.assertRegex(callback, r"if \(const auto owner = weak_scroller.lock\(\)\)\s*owner->cancel_drag\(\);")
            self.assertNotIn("scroller->", callback)

    def test_selection_uses_the_normal_cast_and_activate_calls(self) -> None:
        # z reaches cast_a_spell(true, ...); Z would pass false. Nothing may
        # cast or activate behind those calls.
        self.assertIn("cast_a_spell(true, quick_spell)", self.source)
        self.assertNotIn("cast_a_spell(false", self.source)
        self.assertNotIn("your_spells(", self.source)
        self.assertIn("get_talent(quick_ability)", self.source)
        self.assertIn("activate_talent(tal)", self.source)

    def test_all_commands_keep_their_fixed_order_and_identity(self) -> None:
        expected = [
            ("Auto-explore", "EXPLORE", "EXPLORE"),
            ("Inventory", "INVENTORY", "DISPLAY_INVENTORY"),
            ("Full View", "LOOK", "FULL_VIEW"),
            ("Spells", "SPELLS", "DISPLAY_SPELLS"),
            ("Abilities", "ABILITIES", "USE_ABILITY"),
            ("Memorise", "MEMORISE", "MEMORISE_SPELL"),
            ("Character", "CHARACTER", "RESISTS_SCREEN"),
            ("Skills", "SKILLS", "DISPLAY_SKILLS"),
            ("Religion", "RELIGION", "DISPLAY_RELIGION"),
            ("Map", "MAP", "DISPLAY_MAP"),
            ("Known Objects", "KNOWN_ITEMS", "DISPLAY_KNOWN_OBJECTS"),
            ("Mutations", "MUTATIONS", "DISPLAY_MUTATIONS"),
            ("Commands", "HELP", "DISPLAY_COMMANDS"),
            ("Pick Up", "PICKUP", "PICKUP"),
            ("Exit", "EXIT", "NO_CMD"),
        ]
        self.assertEqual([(label, "TILEG_MENU_" + tile, "CMD_" + cmd)
                          for label, tile, cmd in expected], self.command_entries())
        loop = self.block_after("for (const auto &entry : commands)")
        self.assertNotRegex(loop, r"\b(?:continue|break)\b")
        self.assertIn("command_grid->append(button);", loop)
        self.assertIn("you.visible_igrd(you.pos()) == NON_ITEM", loop)
        self.assertIn("command = feat_stair_direction(feature);", loop)
        self.assertIn("feat_is_altar(feature)", loop)
        for reason in ("No items here", "No exit here"):
            self.assertIn(f'summary_key = "{reason}";', loop)
        self.assertRegex(loop, r"if \(!available\)\s*describe\(label, summary\);\s*else\s*\{\s*selected_command = command;\s*done = true;")

    def test_menu_does_not_resize_surface_or_toggle_keyboard(self) -> None:
        for absent in ("show_keyboard(", "hide_keyboard(", "toggle_keyboard(",
                       "set_keyboard_height(", "resize_window(", "do_layout(",
                       "SDL_SetWindowSize(", "SDL_StartTextInput(", "SDL_StopTextInput("):
            self.assertNotIn(absent, self.source)

    def test_unavailable_entries_describe_without_selecting(self) -> None:
        spells = self.block_after("static vector<quick_entry> _quick_spell_entries")
        abilities = self.block_after("static vector<quick_entry> _quick_ability_entries")
        self.assertIn("spell_uselessness_reason(spell, true, true)", spells)
        self.assertIn("entry.usable = entry.reason.empty();", spells)
        self.assertIn("check_ability_possible(tal.which, true, &entry.reason)", abilities)
        self.assertIn('"Unavailable"', abilities)
        section = self.block_after("const auto add_quick_section =")
        self.assertRegex(section, r"if \(!usable\)\s*describe\(name, reason\);\s*else\s*\{")
        self.assertRegex(section, r"\[&, idx, is_spell, usable, name, reason, describe\]")
        self.assertIn("const int idx = entry.idx;", section)
        selection = block_after(section, "else")
        self.assertIn("quick_spell = (spell_type)idx;", selection)
        self.assertIn("quick_ability = (ability_type)idx;", selection)
        self.assertIn("done = true;", selection)

    def test_selection_runs_only_after_the_drawer_layout_is_popped(self) -> None:
        popped = self.source.rindex("ui::pop_layout();")
        self.assertLess(popped, self.source.index("cast_a_spell(true,"))
        self.assertLess(popped, self.source.index("activate_talent(tal)"))
        self.assertLess(popped, self.source.index("get_talent(quick_ability)"))

    def test_description_is_reached_by_the_right_button(self) -> None:
        # SDLActivity.onTouch() replays a held touch as the right button at
        # release, so the drawer must not try to time the press itself.
        handler = self.block_after("class QuickButton final : public MenuButton")
        self.assertIn("ui::MouseEvent::Button::Right", handler)
        self.assertIn("on_describe()", handler)
        for absent in ("QUICK_LONG_PRESS", "m_pressing", "m_press_ticks",
                       "get_ticks", "windowmanager.h"):
            self.assertNotIn(absent, self.source, absent)
        right = block_after(handler, "if (mouse.button() == ui::MouseEvent::Button::Right)")
        self.assertIn("return true;", right)
        self.assertNotIn("MenuButton::on_event", right)
        self.assertIn("ui::Event::Type::MouseUp", handler)
        describe = self.block_after("button->on_describe = [weak_scroller, idx, is_spell]")
        self.assertIn("describe_spell((spell_type)idx);", describe)
        self.assertIn("describe_ability((ability_type)idx);", describe)
        self.assertIn("cancel_drag()", describe)

    def test_every_menu_label_resolves_in_both_description_databases(self) -> None:
        used = {"%s|%s" % match for match in MENU_TEXT_CALL.findall(self.source)}
        # Labels now also reach TextDB through the command inventory and the
        # inline-section helper; direct literal calls alone miss those sinks.
        labels = {label for label, _, _ in self.command_entries()}
        labels.update(("Enter Shop", "Enter", "Go Upstairs", "Go Downstairs"))
        for label in labels:
            used.add("android command menu|" + label)
            # Exit's summary always becomes an actual stair label or the
            # unavailable reason before reaching the display sink.
            if label != "Exit":
                used.add("android command menu summary|" + label)
        for label in ("Quick Cast", "Quick Abilities"):
            used.add("android command menu|" + label)
        for reason in ("No items here", "No exit here"):
            used.add("android command menu summary|" + reason)
        self.assertIn("android command menu|Quick Cast", used)
        self.assertIn("android command menu|Quick Abilities", used)
        for path in (DESCRIPT_EN, DESCRIPT_ZH):
            self.assertEqual([], sorted(used - database_keys(path)), str(path))

    def test_menu_invariants_reject_minimal_regressions(self) -> None:
        # Run the same checks over in-memory negative mutations; never edit
        # the production source during tests. These remain static guards,
        # not a replacement for the parent task's SDL/device event testing.
        original = self.source
        mutations = (
            ("CMD_EXPLORE}", "CMD_PICKUP}",
             self.test_all_commands_keep_their_fixed_order_and_identity),
            ("command_grid->append(button);", "continue;",
             self.test_all_commands_keep_their_fixed_order_and_identity),
            ("if (!usable)", "if (usable)",
             self.test_unavailable_entries_describe_without_selecting),
            ("get_talent(quick_ability)", "get_talent(ABIL_NON_ABILITY)",
             self.test_selection_uses_the_normal_cast_and_activate_calls),
            ("tiles.set_need_redraw();", "tiles.do_layout();",
             self.test_menu_does_not_resize_surface_or_toggle_keyboard),
            ("owner->cancel_drag();", "/* missing drag reset */",
             self.test_single_scroller_has_no_page_or_submenu_navigation),
            ("dismiss->on_keydown_event(detail_key);", "/* no focus-target handler */",
             self.test_description_escape_is_consumed_before_focus_reset),
            ("const auto describe = [weak_scroller]", "const auto describe = [scroller]",
             self.test_child_description_callbacks_do_not_own_their_scroller),
            ("button->on_describe = [weak_scroller, idx, is_spell]",
             "button->on_describe = [scroller, idx, is_spell]",
             self.test_child_description_callbacks_do_not_own_their_scroller),
        )
        try:
            for before, after, check in mutations:
                with self.subTest(mutation=before):
                    self.assertIn(before, original)
                    self.source = original.replace(before, after)
                    with self.assertRaises(AssertionError):
                        check()
        finally:
            self.source = original


class ContextActionRefreshTests(unittest.TestCase):
    """Guard the two real input loops against stale in-place mode labels.

    These source checks establish publication lifetime and ordering, not JNI
    delivery; equip/unequip and rune/gem label changes still need device tests.
    """

    CASES = (
        ("menu.cc", "void Menu::do_menu()",
         "while (alive && !done && !crawl_state.seen_hups)", "ui::pump_events();"),
        ("prompt.cc", "vector<MenuEntry *> PromptMenu::show_in_msgpane()",
         "while (true)", "int key = get_ch();"),
    )

    def assert_refreshes_each_wait(self, function: str, loop_anchor: str,
                                  wait: str) -> None:
        loop = block_after(function, loop_anchor)
        # No nested scope may destroy InputActionScope before the input wait.
        # Match the direct loop prefix, including its Android-only guard.
        clean = re.sub(r"//[^\n]*", "", loop)
        self.assertRegex(
            clean,
            r"^\{\s*#ifdef __ANDROID__\s*"
            r"ui::InputScreen keyboard_screen;\s*"
            r"std::array<ui::InputAction, 6> keyboard_actions;\s*"
            r"keyboard_descriptor\(keyboard_screen, keyboard_actions\);\s*"
            r"ui::InputActionScope keyboard_scope\(keyboard_screen,\s*"
            r"std::move\(keyboard_actions\)\);\s*#endif")
        for marker in ("keyboard_descriptor(", "ui::InputActionScope keyboard_scope("):
            self.assertEqual(1, function.count(marker))
            self.assertLess(loop.index(marker), loop.index(wait))

    def test_menu_and_prompt_publish_current_actions_each_input_wait(self) -> None:
        for filename, signature, loop, wait in self.CASES:
            with self.subTest(source=filename):
                source = (ROOT / "crawl-ref/source" / filename).read_text(encoding="utf-8")
                self.assert_refreshes_each_wait(block_after(source, signature), loop, wait)

    def test_publication_outside_loop_is_rejected(self) -> None:
        for filename, signature, anchor, wait in self.CASES:
            source = (ROOT / "crawl-ref/source" / filename).read_text(encoding="utf-8")
            function = block_after(source, signature)
            loop = block_after(function, anchor)
            android_start = loop.index("#ifdef __ANDROID__")
            android_end = loop.index("#endif", android_start) + len("#endif")
            publication = loop[android_start:android_end]
            descriptor = "keyboard_descriptor(keyboard_screen, keyboard_actions);"
            scope_match = re.search(
                r"ui::InputActionScope keyboard_scope\(keyboard_screen,\s*"
                r"std::move\(keyboard_actions\)\);", publication)
            self.assertIsNotNone(scope_match)
            for moved in (publication, descriptor, scope_match.group()):
                with self.subTest(source=filename, moved=moved):
                    # Keep each production statement present, but hoist it
                    # once before the loop: the original stale-label bug.
                    mutated = function.replace(moved, "", 1)
                    insertion = mutated.index(anchor)
                    mutated = mutated[:insertion] + moved + "\n" + mutated[insertion:]
                    with self.assertRaises(AssertionError):
                        self.assert_refreshes_each_wait(mutated, anchor, wait)


class GameActionRowTests(unittest.TestCase):
    """The dungeon's own action row and the wait/rest split of the centre key.

    Static checks only: the descriptor branch, the Java tag switch and the
    resources it names. Turn accounting and delivery need device tests.
    """

    GAME_KEYS = ("'5'", "'q'", "'r'", "'f'", "'z'", "'a'")

    def setUp(self) -> None:
        self.ui_h = (ROOT / "crawl-ref/source/ui.h").read_text(encoding="utf-8")
        self.ui_cc = UI_CC.read_text(encoding="utf-8")
        self.java = (ROOT / "crawl-ref/source/android-project/app/src/main/java/"
                     "org/develz/crawl/DCSSKeyboard.java").read_text(encoding="utf-8")

    def screens(self) -> list:
        body = block_after(self.ui_h, "enum class InputScreen")
        return [name.strip() for name in body.strip("{}").replace("\n", "").split(",")
                if name.strip()]

    def game_branch(self) -> str:
        function = block_after(self.ui_cc, "InputDescriptor input_descriptor()")
        anchor = "else if (result.context == InputContext::GAME)"
        self.assertIn(anchor, function)
        # A registered scope on top of the dungeon must win over these actions.
        self.assertLess(function.index("input_action_scope->owner == top_layout()"),
                        function.index(anchor))
        return block_after(function, anchor)

    def test_game_screen_is_appended_last_and_shared_with_java(self) -> None:
        screens = self.screens()
        self.assertEqual("GAME", screens[-1])
        self.assertIn("case %d: // Ordinary dungeon commands" % screens.index("GAME"),
                      self.java)

    def test_game_actions_are_plain_default_keys(self) -> None:
        branch = self.game_branch()
        keys = re.findall(r"InputAction\(\"\",\s*('.')\)", branch)
        self.assertEqual(list(self.GAME_KEYS), keys)
        for key in keys:
            # Only printable characters reach the game through the
            # InputConnection; CK_* keys need the native bridge allowlist.
            self.assertTrue(32 <= ord(key[1]) <= 126, key)
        self.assertNotIn("CK_", branch)
        self.assertIn("InputScreen::GAME", branch)

    def test_java_labels_cover_exactly_the_published_keys(self) -> None:
        case = self.java[self.java.index("// Ordinary dungeon commands"):]
        case = case[:case.index("break;")]
        labelled = re.findall(r"case ('.'): return R\.string\.(keyboard_\w+);", case)
        self.assertEqual(list(self.GAME_KEYS), [key for key, _ in labelled])
        names = [name for _, name in labelled]
        self.assertEqual("keyboard_rest", names[0])
        for qualifier in ("values", "values-zh"):
            strings = AndroidFirstRunTests().string_names(qualifier)
            for name in names + ["keyboard_wait"]:
                self.assertIn(name, strings, qualifier)

    def test_centre_key_waits_only_in_the_dungeon(self) -> None:
        function = block_after(self.java, "public void setInputContext(")
        self.assertIn("KeyEvent.KEYCODE_PERIOD", function)
        self.assertRegex(function, r"center\.setTag\(Integer\.toString\(gameplay \? "
                         r"KeyEvent\.KEYCODE_PERIOD\s*:\s*KeyEvent\.KEYCODE_NUMPAD_5\)\);")
        self.assertIn("R.string.keyboard_wait) : \"5\"", function)
        self.assertNotIn("R.string.keyboard_rest", function)
        # The static layout keeps numpad 5 until the dungeon context arrives.
        root = ET.parse(ANDROID_MOBILE_LAYOUT).getroot()
        android = "{http://schemas.android.com/apk/res/android}"
        tags = {node.attrib.get(android + "id"): node.attrib.get(android + "tag")
                for node in root.iter("Button")}
        self.assertEqual("149", tags["@+id/key_mobile_5"])

    def test_wait_and_rest_labels_differ_in_every_locale(self) -> None:
        for qualifier in ("values", "values-zh", "values-zh-rCN"):
            root = ET.parse(ANDROID_RES / qualifier / "strings.xml").getroot()
            text = {node.attrib.get("name"): node.text for node in root}
            self.assertNotEqual(text["keyboard_rest"], text["keyboard_wait"], qualifier)


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

    def test_row_requires_a_live_list_and_available_space(self) -> None:
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
            r"int quick_row_h = m_quick_row_spells \|\| m_quick_row_abilities"
            r"\s*\? m_region_quick_spl->dy : 0;")
        self.assertRegex(
            layout,
            r"m_quick_row_shown\s*=\s*use_top_bar\s*&&\s*"
            r"quick_row_h > 0")
        # A live list must also yield when it would shrink the full LOS.
        self.assertRegex(
            layout,
            r"if \(m_windowsz.y - min_top_bar_h - msg_min_h - quick_row_h"
            r"\s*< ENV_SHOW_DIAMETER \* m_region_tile->dy\)"
            r"\s*\{\s*quick_row_h = 0;")
        # Empty lists or insufficient space leave no drawable/hittable cells.
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
