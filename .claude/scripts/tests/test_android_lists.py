#!/usr/bin/env python3
"""Execute Android list layout and skill dispatch with focused UI doubles.

The layout test uses production UIMenu layout with a deterministic fixed-width
font double; real font shaping, SDL clipping and touch gestures require the
Android screenshots/instrumentation. The dispatcher test executes the shared
skill state-routing code, while the skill calculation backend remains a double.
"""
from pathlib import Path
import unittest

import test_android_quickbar as regression

ROOT = Path(__file__).resolve().parents[3]


class AndroidListTests(unittest.TestCase):
    def test_compact_inventory_titles_and_cross_category_selection_count(self):
        source = (ROOT / "crawl-ref/source/invent.cc").read_text()
        title = regression.block_after(source, "void InvMenu::set_title(const string &s)")
        count = regression.block_after(source, "string InvMenu::get_select_count_string")
        footer = regression.block_after(source, "string InvMenu::get_keyhelp")
        selections = regression.block_after(source, "vector<SelItem> InvMenu::get_selitems")
        drop = regression.block_after(source, "static string _drop_menu_titlefn")
        menu_source = (ROOT / "crawl-ref/source/menu.cc").read_text()
        get_selected = regression.block_after(menu_source, "void Menu::get_selected")
        selected_entries = regression.block_after(menu_source, "vector<MenuEntry*> Menu::selected_entries")
        # Execute the real title/footer and selection collector; page membership
        # is supplied directly, independently of the game's inventory loader.
        regression.TargetingSafetyTests.run_cpp(self, r'''
#define __ANDROID__
#define T_(s) (s)
#define ARRAYSZ(a) (sizeof(a) / sizeof((a)[0]))
#include <cassert>
#include <cstdio>
#include <string>
#include <vector>
using namespace std;
enum { MF_PAGED_INVENTORY=1, MF_MULTISELECT=2, MF_NOSELECT=4, MF_NO_WRAP_ROWS=8 };
struct { bool small=true; bool is_using_small_layout() { return small; } } tiles;
template<typename... Args> string make_stringf(const char* format, Args... args) {
    char buffer[1024];
    snprintf(buffer, sizeof(buffer), format, args...);
    return buffer;
}
string slot_description() { return "2/52 gear slots"; }
struct item_def { int link; };
struct SelItem {
    int slot, quantity;
    const item_def* item;
    SelItem(int s, int q, const item_def* it) : slot(s), quantity(q), item(it) {}
};
struct MenuEntry {
    string text;
    int selected_qty=1;
    virtual ~MenuEntry() = default;
    bool selected() { return selected_qty > 0; }
};
struct InvEntry : MenuEntry { const item_def* item=nullptr; };
struct Menu {
    vector<MenuEntry*> sel, items;
    void get_selected(vector<MenuEntry*> *selected) const
''' + get_selected + r'''
    vector<MenuEntry*> selected_entries() const
''' + selected_entries + r'''
    string get_select_count_string(int) const { return "legacy annotation"; }
    string get_keyhelp(bool) const { return "legacy footer"; }
};
struct InvTitle : MenuEntry {
    InvTitle(const Menu*, const string& value, int) { text = value; }
};
struct InvMenu : Menu {
    int flags=MF_PAGED_INVENTORY|MF_MULTISELECT, cur_osel=0, title_annotate=0;
    vector<SelItem> offscreen_sel[4];
    string shown_title;
    void set_title(MenuEntry* title) { shown_title = title->text; delete title; }
    void set_title(const string& s)
''' + title + r'''
    vector<SelItem> get_selitems(bool include_offscreen=false) const
''' + selections + r'''
    string get_select_count_string(int) const
''' + count + r'''
    string get_keyhelp(bool scrollable) const
''' + footer + r'''
};
string _drop_menu_titlefn(const Menu*, const string&)
''' + drop + r'''
int main() {
    InvMenu menu;
    const string expected[] = {"Gear: 2/52 gear slots", "Potions: ", "Scrolls: ", "Evocable Items: "};
    for (int page=0; page<4; ++page) {
        menu.cur_osel = page;
        menu.set_title("");
        assert(menu.shown_title == expected[page]);
    }
    assert(_drop_menu_titlefn(&menu, "") == "Drop what? 2/52 gear slots");
    menu.cur_osel = 0;
    assert(menu.get_keyhelp(true) == "Selected: 0");
    item_def first{1}, second{2}, third{3};
    InvEntry a, b, c;
    a.item=&first; b.item=&second; c.item=&third;
    menu.sel = {&a};
    menu.items = {&a};
    assert(menu.get_keyhelp(true) == "Selected: 1");
    assert(menu.get_select_count_string(1).empty());
    menu.sel = {&a, &b};
    menu.items = {&a, &b};
    menu.offscreen_sel[0] = menu.get_selitems(); // current page snapshot must not double count
    assert(menu.get_keyhelp(true) == "Selected: 2");
    menu.cur_osel = 1;
    menu.sel = {&c};
    menu.items = {&c};
    assert(menu.get_keyhelp(true) == "Selected: 3");
    // Clear-selection changes quantities before the cached selection vector.
    c.selected_qty = 0;
    assert(menu.sel.size() == 1);
    assert(menu.get_keyhelp(true) == "Selected: 2");
    c.selected_qty = 1;
    assert(menu.get_keyhelp(true) == "Selected: 3");
    menu.offscreen_sel[1] = menu.get_selitems();
    menu.cur_osel = 2;
    menu.sel.clear();
    menu.items.clear();
    assert(menu.get_keyhelp(true) == "Selected: 3");
    menu.offscreen_sel[0].clear();
    assert(menu.get_keyhelp(true) == "Selected: 1");
    menu.offscreen_sel[1].clear();
    assert(menu.get_keyhelp(true) == "Selected: 0");
    tiles.small = false;
    menu.set_title("");
    assert(menu.shown_title.find("Left/Right to switch category") != string::npos);
    assert(_drop_menu_titlefn(&menu, "").find("(_ for help)") != string::npos);
    assert(menu.get_keyhelp(true) == "legacy footer");
    menu.sel = {&a};
    assert(menu.get_select_count_string(1) == " 1 item");
    menu.flags = 0;
    menu.set_title("");
    assert(menu.shown_title == "Inventory: 2/52 gear slots");
    assert(menu.get_select_count_string(1) == "legacy annotation");
    tiles.small = true;
    assert(menu.get_select_count_string(1) == "legacy annotation");
}
''')

    def test_compact_quiver_footer_preserves_focus_state_and_messages(self):
        source = (ROOT / "crawl-ref/source/quiver.cc").read_text()
        action_menu = regression.block_after(source, "class ActionSelectMenu : public Menu")
        footer = regression.block_after(action_menu, "string get_keyhelp(bool) const override")
        regression.TargetingSafetyTests.run_cpp(self, r'''
#define __ANDROID__
#define T_(s) (s)
#include <cassert>
#include <cstdio>
#include <string>
using namespace std;
struct { bool small=true; bool is_using_small_layout() { return small; } } tiles;
enum { CMD_MENU_CYCLE_MODE };
string menu_keyhelp_cmd(int) { return "[!]"; }
string pad_more_with(string left, string right) { return left + right; }
template<typename... Args> string make_stringf(const char* format, Args... args) {
    char buffer[2048];
    snprintf(buffer, sizeof(buffer), format, args...);
    return buffer;
}
struct ActionSelectMenu {
    enum class Focus { NONE, ITEM, SPELL, ABIL };
    Focus focus_mode=Focus::NONE;
    bool any_items=true, any_spells=true, any_abilities=true;
    string more_message;
    string get_keyhelp(bool) const
''' + footer + r'''
};
int main() {
    ActionSelectMenu menu;
    assert(menu.get_keyhelp(true) == "Focus mode: off");
    for (auto mode : {ActionSelectMenu::Focus::ITEM, ActionSelectMenu::Focus::SPELL,
                      ActionSelectMenu::Focus::ABIL}) {
        menu.focus_mode = mode;
        assert(menu.get_keyhelp(false) == "Focus mode: on");
    }
    menu.more_message = "No actions available.";
    assert(menu.get_keyhelp(true) == "No actions available.\nFocus mode: on");
    tiles.small = false;
    const auto legacy = menu.get_keyhelp(true);
    for (const auto& text : {"No actions available.", "Inventory", "All spells",
                             "All abilities", "Focus mode", "off|<w>on</w>"})
        assert(legacy.find(text) != string::npos);
}
''')

    def test_skill_categories_partition_refresh_and_reject_hidden_hotkeys(self):
        skills = (ROOT / "crawl-ref/source/skill-menu.cc").read_text()
        page = regression.block_after(skills, "class AndroidSkillMenu : public Menu")
        button = regression.block_after(skills, "class AndroidSkillPageButton : public MenuButton")
        populate = regression.block_after(skills, "void SkillMenu::populate_android_menu")
        magic = regression.block_after((ROOT / "crawl-ref/source/skills.cc").read_text(),
                                       "bool is_magic_skill")
        outer = (ROOT / "crawl-ref/source/outer-menu.cc").read_text()
        button_events = regression.block_after(outer, "bool MenuButton::on_event")
        # Use the real category adapter/population and MenuButton event handler.
        # Skill calculations and the pre-existing filter backend remain doubles.
        regression.TargetingSafetyTests.run_cpp(self, r'''
#pragma GCC diagnostic ignored "-Wparentheses"
#define USE_TILE_LOCAL
#define __ANDROID__
#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <functional>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>
using namespace std;
#define ASSERT assert
#define T_(s) (s)
enum skill_type { SK_FIGHTING, SK_ARMOUR, SK_UNARMED_COMBAT,
    SK_LAST_MUNDANE = SK_UNARMED_COMBAT, SK_SPELLCASTING, SK_CONJURATIONS,
    SK_ALCHEMY, SK_LAST_MAGIC = SK_ALCHEMY, SK_INVOCATIONS, SK_EVOCATIONS,
    SK_SHAPESHIFTING, NUM_SKILLS, SK_TITLE, SK_NONE };
bool is_invalid_skill(skill_type skill) { return skill < 0 || skill >= NUM_SKILLS; }
bool is_magic_skill(skill_type sk)
''' + magic + r'''
enum { CK_UP=1001, CK_DOWN, CK_LEFT, CK_RIGHT, CK_PGUP, CK_PGDN, CK_HOME,
       CK_END, CK_ENTER, CK_MOUSE_B1, CK_MOUSE_B2, CK_ESCAPE,
       MF_SINGLESELECT=1, MF_ARROWS_SELECT=2, MF_ALLOW_FORMATTING=4,
       SKMF_EXPERIENCE=1, SKMF_SPECIAL=SKMF_EXPERIENCE, MEL_ITEM=1,
       LIGHTCYAN=11, MOUSE_CURSOR_POINTER=1, MOUSE_CURSOR_ARROW=2 };
int numpad_to_regular(int key, bool) { return key; }
int described = -1;
void describe_skill(skill_type skill) { described = skill; }
int term_colours[16] = {};
struct { void set_mouse_cursor(int) {} } manager;
auto* wm = &manager;
struct { int game_scale = 1; } Options;
struct { int apply_game_scale(int value) { return value / Options.game_scale; } } display_density;
float density = 1;
float jni_get_display_density() { return density; }
struct Font {} font;
struct {
    bool small = true;
    bool is_using_small_layout() { return small; }
    Font* get_msg_font() { return &font; }
} tiles;
struct formatted_string {
    string text;
    formatted_string(string value, int) : text(value) {}
};
namespace ui {
enum class InputScreen { SKILLS };
struct InputAction {};
struct Event {
    enum class Type { MouseEnter, MouseLeave, FocusIn, FocusOut, MouseDown,
                      MouseUp, KeyDown };
    Type kind;
    explicit Event(Type type) : kind(type) {}
    Type type() const { return kind; }
};
struct MouseEvent : Event {
    enum class Button { Left, Right };
    Button value;
    MouseEvent(Type type, Button button) : Event(type), value(button) {}
    Button button() const { return value; }
};
struct KeyEvent : Event {
    int value;
    explicit KeyEvent(int key) : Event(Type::KeyDown), value(key) {}
    int key() const { return value; }
};
struct ActivateEvent {};
struct Widget {
    struct Region { int x=0, y=0; int ex() { return 100; } int ey() { return 48; } } m_region;
    struct Size { int height=0; } minimum;
    virtual ~Widget() = default;
    virtual void _allocate_region() {}
    virtual bool on_event(const Event&) { return false; }
    virtual bool can_take_focus() { return false; }
    void _queue_allocation() {}
    Size& min_size() { return minimum; }
};
struct Text : Widget {
    string text;
    bool wrap = false;
    void set_font(Font*) {}
    void set_wrap_text(bool value) { wrap = value; }
    void set_margin_for_sdl(int, int, int, int) {}
    void set_text(formatted_string value) { text = value.text; }
};
struct Box : Widget {
    vector<shared_ptr<Widget>> children;
    void add_child(shared_ptr<Widget> child) { children.push_back(child); }
};
struct Bin : Widget {};
}
using namespace ui;
struct MenuButton : Bin {
    bool focused=false, active=false, hovered=false;
    struct Buffer { template<typename... T> void add_square(T...) {} } m_line_buf;
    shared_ptr<Text> label;
    function<bool(const ActivateEvent&)> activated;
    void set_child(shared_ptr<Text> value) { label = value; }
    void on_activate_event(function<bool(const ActivateEvent&)> value) { activated = value; }
    bool activate() { return activated(ActivateEvent()); }
    bool on_event(const Event& event) override
''' + button_events + r'''
};
struct MenuEntry {
    string text;
    vector<int> hotkeys;
    MenuEntry(string value, int, int=0) : text(value) {}
    virtual ~MenuEntry() = default;
};
struct AndroidSkillEntry : MenuEntry {
    using MenuEntry::MenuEntry;
    skill_type skill = SK_NONE;
};
struct Menu {
    vector<MenuEntry*> items;
    int last_hovered=-1, resets=0;
    string title;
    struct { shared_ptr<Box> header = make_shared<Box>(); } m_ui;
    Menu(int, const string&) {}
    virtual ~Menu() { clear(); }
    void clear() { for (auto* item : items) delete item; items.clear(); }
    void set_title(string value) { title = value; }
    void add_entry(MenuEntry* entry) { items.push_back(entry); }
    void update_menu() {}
    void set_hovered(int value) { last_hovered = value; }
    void reset() { ++resets; }
    virtual bool process_key(int key) {
        if (key == CK_DOWN) last_hovered = min(last_hovered + 1, (int)items.size() - 1);
        if (key == CK_UP) last_hovered = max(0, last_hovered - 1);
        return true;
    }
    virtual void keyboard_descriptor(InputScreen&, array<InputAction, 6>&, vector<InputAction>&) {}
};
struct TextItem {
    string text;
    int key=0;
    TextItem(string value, int hotkey) : text(value), key(hotkey) {}
    string get_text() { return text; }
    bool can_be_highlighted() { return key != 0; }
    vector<int> get_hotkeys() { return key ? vector<int>{key} : vector<int>{}; }
};
string trimmed_string(string value) { return value; }
struct SkillMenuEntry {
    skill_type skill = SK_NONE;
    int key=0;
    bool visible=true, selectable=true;
    skill_type get_skill() { return skill; }
    void add_android_entry(Menu& menu, const SkillMenuEntry&) {
        if (!visible || is_invalid_skill(skill)) return;
        auto* item = new AndroidSkillEntry(to_string(skill), MEL_ITEM, 1);
        item->skill = skill;
        if (selectable) item->hotkeys = {key, key - 'a' + 'A'};
        menu.add_entry(item);
    }
};
const int SK_ARR_LN=NUM_SKILLS+1, SK_ARR_COL=1;
struct SkillMenu {
    bool experience=false;
    SkillMenuEntry m_skills[SK_ARR_LN][SK_ARR_COL];
    TextItem title{"XP allocation", 0}, control{"filter", '*'}, help{"help", 0};
    TextItem *m_title=&title, *m_help=&help, *m_help_button=nullptr,
             *m_middle_button=nullptr, *m_clear_targets_button=nullptr;
    map<int, TextItem*> m_switches{{0, &control}};
    bool is_set(int flag) { return experience && flag == SKMF_EXPERIENCE; }
    array<InputAction, 6> keyboard_actions() { return {}; }
    vector<InputAction> keyboard_more() { return {}; }
    void populate_android_menu(Menu& menu, bool split_pages, bool magic_page)
''' + populate + r'''
    SkillMenu() {
        for (int i=0; i<NUM_SKILLS; ++i) {
            m_skills[i][0].skill = skill_type(i);
            m_skills[i][0].key = 'a' + i;
        }
        m_skills[NUM_SKILLS][0].skill = SK_TITLE;
    }
} skm;
vector<int> dispatched;
bool _process_skill_menu_key(int key) {
    dispatched.push_back(key);
    return key == CK_ESCAPE || (key == CK_ENTER && skm.experience);
}
class AndroidSkillPageButton : public MenuButton
''' + button + r''';
class AndroidSkillMenu : public Menu
''' + page + r''';
set<skill_type> visible_skills(const Menu& menu) {
    set<skill_type> result;
    for (auto* item : menu.items) {
        auto skill = static_cast<AndroidSkillEntry*>(item)->skill;
        if (!is_invalid_skill(skill)) assert(result.insert(skill).second);
    }
    return result;
}
int main() {
    AndroidSkillMenu menu;
    const set<skill_type> general{SK_FIGHTING, SK_ARMOUR, SK_UNARMED_COMBAT,
                                 SK_INVOCATIONS, SK_EVOCATIONS, SK_SHAPESHIFTING};
    const set<skill_type> spells{SK_SPELLCASTING, SK_CONJURATIONS, SK_ALCHEMY};
    assert(visible_skills(menu) == general);
    assert(menu.title == "General skills");
    auto button = dynamic_pointer_cast<MenuButton>(menu.m_ui.header->children.at(0));
    assert(button && button->label->wrap && !button->can_take_focus());
    assert(button->label->text == "Show spell skills");
    const MouseEvent press(Event::Type::MouseDown, MouseEvent::Button::Left);
    const MouseEvent release(Event::Type::MouseUp, MouseEvent::Button::Left);
    assert(button->on_event(press));
    assert(visible_skills(menu) == general && dispatched.empty());
    assert(button->on_event(release));
    assert(visible_skills(menu) == spells && dispatched.empty());
    assert(menu.title == "Spell skills" && menu.resets == 1);
    assert(!button->on_event(release)); // no second activation on stray release
    assert(visible_skills(menu) == spells);
    assert(menu.process_key('a') && menu.process_key('A'));
    assert(dispatched.empty()); // hidden general skills cannot train
    skm.m_skills[SK_FIGHTING][0].key = '1';
    assert(menu.process_key('1') && dispatched.empty());
    skm.m_skills[SK_FIGHTING][0].key = 'a';
    assert(menu.process_key(CK_DOWN));
    assert(static_cast<AndroidSkillEntry*>(menu.items[menu.last_hovered])->skill == SK_CONJURATIONS);
    assert(menu.process_key(CK_ENTER));
    assert(dispatched.back() == 'a' + SK_CONJURATIONS);
    // Internal backend refresh can change shortcuts; restore cursor by identity.
    skm.m_skills[SK_CONJURATIONS][0].key = 'q';
    assert(menu.process_key('!'));
    assert(visible_skills(menu) == spells);
    assert(static_cast<AndroidSkillEntry*>(menu.items[menu.last_hovered])->skill == SK_CONJURATIONS);
    assert(menu.process_key(CK_ENTER) && dispatched.back() == 'q');
    assert(menu.process_key('Q') && dispatched.back() == 'Q');
    assert(menu.process_key(CK_MOUSE_B2) && described == SK_CONJURATIONS);
    // Existing useful/all and nonselectable-row state is respected on either page.
    skm.m_skills[SK_CONJURATIONS][0].visible = false;
    assert(menu.process_key('*'));
    assert(visible_skills(menu) == (set<skill_type>{SK_SPELLCASTING, SK_ALCHEMY}));
    const auto calls = dispatched.size();
    assert(menu.process_key('q') && dispatched.size() == calls);
    assert(menu.process_key('\t') && visible_skills(menu) == general);
    assert(dispatched.size() == calls); // switching is entirely presentation
    skm.m_skills[SK_FIGHTING][0].selectable = false;
    assert(menu.process_key('?'));
    const auto before_disabled = dispatched.size();
    assert(menu.process_key('a') && dispatched.size() == before_disabled);
    skm.experience = true;
    assert(menu.process_key('\t'));
    assert(menu.title == "XP allocation\nSpell skills");
    assert(!menu.process_key(CK_ENTER) && dispatched.back() == CK_ENTER);
    assert(!menu.process_key(CK_ESCAPE) && dispatched.back() == CK_ESCAPE);
    // Large-layout Android preserves the original unpartitioned adapter.
    tiles.small = false;
    AndroidSkillMenu legacy;
    assert(legacy.m_ui.header->children.empty());
    assert(visible_skills(legacy).count(SK_FIGHTING));
    assert(visible_skills(legacy).count(SK_SPELLCASTING));
    assert(legacy.title == "XP allocation");
    assert(legacy.process_key('q') && dispatched.back() == 'q');
    tiles.small = true;
    for (float d : {1.f, 1.5f, 2.625f, 3.f})
        for (int scale : {1, 2, 3}) {
            density = d;
            Options.game_scale = scale;
            AndroidSkillMenu scaled;
            auto header = scaled.m_ui.header->children.at(0);
            assert(header->minimum.height * scale >= ceil(48 * d));
        }
}
''')

    def test_touch_menu_chrome_does_not_force_popup_beyond_viewport(self):
        menu = (ROOT / "crawl-ref/source/menu.cc").read_text()
        ui = (ROOT / "crawl-ref/source/ui.cc").read_text()
        constructor = regression.block_after(menu, "Menu::Menu(int _flags")
        text_size = regression.block_after(ui, "SizeReq Text::_get_preferred_size")
        text_wrap = regression.block_after(ui, "void Text::wrap_text_to_size")
        immediate = regression.block_after(menu, "void set_text_immediately")
        keyhelp = regression.block_after(menu, "string Menu::get_keyhelp(bool scrollable) const")
        inventory = (ROOT / "crawl-ref/source/invent.cc").read_text()
        drop_title = regression.block_after(inventory, "static string _drop_menu_titlefn")
        row_layout = regression.block_after(menu, "void UIMenu::do_layout")
        touch_rows = regression.block_after(menu, "bool uses_touch_rows() const")
        hotkey_prefix = regression.block_after(menu, "static bool _has_hotkey_prefix")
        scroller_size = regression.block_after(ui, "SizeReq Scroller::_get_preferred_size")
        scroller_allocation = regression.block_after(ui, "void Scroller::_allocate_region")
        scroller_allocation = scroller_allocation[:scroller_allocation.index("#ifdef USE_TILE_LOCAL")] + "}"
        box_size = regression.block_after(ui, "SizeReq Box::_get_preferred_size")
        main_axis = regression.block_after(ui, "vector<int> Box::layout_main_axis")
        cross_axis = regression.block_after(ui, "vector<int> Box::layout_cross_axis")
        box_allocation = regression.block_after(ui, "void Box::_allocate_region")
        popup_allocation = regression.block_after(ui, "void Popup::_allocate_region")
        # Execute real menu setup and Text/Box/Popup size negotiation. Font
        # shaping, widget caching and GL are doubles; actual row wrapping is
        # exercised separately below, and final rendering requires a device.
        regression.TargetingSafetyTests.run_cpp(self, r'''
#pragma GCC diagnostic ignored "-Wparentheses"
#define USE_TILE_LOCAL
#define __ANDROID__
#include <algorithm>
#include <cassert>
#include <climits>
#include <cmath>
#include <cstdio>
#include <memory>
#include <numeric>
#include <string>
#include <vector>
using namespace std;
#define ASSERT assert
#define T_(s) (s)
struct SizeReq { int min, nat; };
struct Region { int x, y, width, height; };
struct Size {
    int width, height;
    explicit Size(int n) : width(n), height(n) {}
    Size(int w, int h) : width(w), height(h) {}
    bool is_valid() { return width >= 0 && height >= 0; }
};
enum { FSOP_TEXT };
struct formatted_string {
    struct fs_op { int type; string text; };
    vector<fs_op> ops;
    formatted_string(string text = "") { ops.push_back({FSOP_TEXT, text}); }
    void clear() { ops.clear(); }
    void operator+=(const formatted_string& text) {
        ops.insert(ops.end(), text.ops.begin(), text.ops.end());
    }
    string tostring() const {
        string result;
        for (const auto& op : ops) result += op.text;
        return result;
    }
    formatted_string chop(int n) const { return tostring().substr(0, n); }
    void del_char() { ops.front().text.erase(0, 1); }
};
struct Font {
    int pixels = 28;
    int advance = 0;
    int char_height() { return pixels; }
    int string_width(const formatted_string& text) {
        int width = 0, longest = 0;
        for (char ch : text.tostring()) {
            width = ch == '\n' ? 0 : width + (advance ? advance : pixels);
            longest = max(longest, width);
        }
        return longest;
    }
    int string_height(const formatted_string& text) {
        const string plain = text.tostring();
        return (1 + count(plain.begin(), plain.end(), '\n')) * pixels;
    }
    formatted_string split(const formatted_string& text, int width, int) {
        string wrapped = text.tostring();
        // Production splitting at width zero advances one glyph per line.
        const int chars = max(1, width / (advance ? advance : pixels));
        string output;
        int columns = 0;
        for (char ch : wrapped) {
            if (ch == '\n') columns = 0;
            else {
                if (columns == chars) { output += '\n'; columns = 0; }
                ++columns;
            }
            output += ch;
        }
        return output;
    }
} font;
struct {
    bool small = true;
    Font* get_msg_font() { return &font; }
    bool popups_anchor_bottom() { return true; }
    bool is_using_small_layout() { return small; }
} tiles;
struct { int game_scale=1; } Options;
struct { int apply_game_scale(int value) { return value / Options.game_scale; } } display_density;
float jni_get_display_density() { return 1; }
bool _has_hotkey_prefix(const string& s)
''' + hotkey_prefix + r'''
template<typename... Args> string make_stringf(const char* format, Args... args) {
    char buffer[1024];
    snprintf(buffer, sizeof(buffer), format, args...);
    return buffer;
}
enum { CMD_MENU_TOGGLE_SELECTED, CMD_MENU_ACCEPT_SELECTION, CMD_MENU_EXIT,
       CMD_MENU_PAGE_DOWN, CMD_MENU_PAGE_UP };
string menu_keyhelp_cmd(int) { return "[keyboard binding]"; }
string menu_keyhelp_select_keys() { return "[Up|Down]"; }
string pad_more_with_esc(const string& value) { return value + "[Esc] Exit"; }
string pad_more_with(const string& value, const string& suffix) { return value + suffix; }
struct Widget {
    enum Direction { HORZ, VERT };
    enum Align { START, CENTER, END, STRETCH };
    bool visible = true;
    int flex_grow = 1;
    Region m_region{0, 0, 0, 0};
    virtual ~Widget() = default;
    virtual SizeReq _get_preferred_size(Direction dim, int) {
        return {0, dim == HORZ ? 800 : 1200};
    }
    SizeReq get_preferred_size(Direction dim, int width) {
        return visible ? _get_preferred_size(dim, width) : SizeReq{0, 0};
    }
    virtual void _allocate_region() {}
    void allocate_region(Region value) {
        if (!visible) return;
        m_region = value;
        _allocate_region();
    }
    void _expose() {}
    void set_visible(bool value) { visible = value; }
};
struct Text : Widget {
    Font* m_font = &font;
    bool wrap_text = false, ellipsize = false;
    formatted_string m_text, m_text_wrapped;
    Size m_wrapped_size{-1}, m_wrapped_sizereq{-1};
    struct brkpt { unsigned op, line; };
    vector<brkpt> m_brkpts;
    void set_font(Font* value) { m_font = value; }
    void set_wrap_text(bool value) { wrap_text = value; }
    void wrap_text_to_size(int width, int height)
''' + text_wrap + r'''
    void _allocate_region() override {
        wrap_text_to_size(m_region.width, m_region.height);
    }
    SizeReq _get_preferred_size(Direction dim, int prosp_width) override
''' + text_size + r'''
};
struct Menu;
struct UIMenu : Widget {
    struct Item { int x=0, y=0, row=0, column=0; formatted_string text;
                  vector<int> tiles; bool heading=false; };
    Menu* m_menu;
    Font* m_font_entry = &font;
    int m_min_col_width=-1, m_scroll_context=0, m_height=0, m_nat_column_width=0;
    bool m_draw_tiles=false;
    static constexpr int item_pad=2, pad_right=10;
    vector<Item> item_info;
    vector<int> row_heights;
    explicit UIMenu(Menu* menu) : m_menu(menu), item_info(20) {
        for (auto& item : item_info)
            item.text = formatted_string(" a - A very long skill\nLevel 5  Training 50% Aptitude +1");
    }
    bool uses_touch_rows() const;
    void do_layout(int mw, int num_columns, bool just_checking=false);
    SizeReq _get_preferred_size(Direction dim, int width) override {
        if (dim == HORZ) return {0, 1080};
        do_layout(width, 1);
        return {0, m_height};
    }
};
struct UIMenuMore : Text {
    explicit UIMenuMore(Menu*) {}
    void set_text_immediately(const formatted_string& fs)
''' + immediate + r'''
};
struct UIMenuScroller : Widget {
    shared_ptr<Widget> m_child;
    int m_scroll=0;
    void set_child(shared_ptr<Widget> child) { m_child = child; }
    SizeReq _get_preferred_size(Direction dim, int prosp_width) override
''' + scroller_size + r'''
    void _allocate_region() override
''' + scroller_allocation + r'''
};
struct Box : Widget {
    bool horz;
    Align align_cross = STRETCH;
    Align align_main = START;
    vector<shared_ptr<Widget>> m_children;
    explicit Box(Direction dim) : horz(dim == HORZ) {}
    void set_cross_alignment(Align value) { align_cross = value; }
    void add_child(shared_ptr<Widget> child) { m_children.push_back(child); }
    vector<int> layout_main_axis(vector<SizeReq>& ch_psz, int main_sz)
''' + main_axis + r'''
    vector<int> layout_cross_axis(vector<SizeReq>& ch_psz, int cross_sz)
''' + cross_axis + r'''
    SizeReq _get_preferred_size(Direction dim, int prosp_width) override
''' + box_size + r'''
    void _allocate_region() override
''' + box_allocation + r'''
};
enum { MF_NOSELECT = 1, MF_NO_WRAP_ROWS = 2, MF_MULTISELECT = 4, MF_ARROWS_SELECT = 8 };
struct Menu {
    int flags;
    int chosen=0;
    vector<int> items = vector<int>(20);
    bool more_needs_init = false;
    struct {
        shared_ptr<UIMenu> menu;
        shared_ptr<UIMenuScroller> scroller;
        shared_ptr<Text> title;
        shared_ptr<Box> header;
        shared_ptr<UIMenuMore> more;
        shared_ptr<Box> vbox;
    } m_ui;
    bool is_set(int value) const { return flags & value; }
    vector<int> selected_entries() const { return vector<int>(chosen); }
    string get_keyhelp(bool scrollable) const
''' + keyhelp + r'''
    void set_flags(int value) { flags = value; }
    void set_more(const string&) {}
    explicit Menu(int value) : flags(value)
''' + constructor + r'''
};
bool UIMenu::uses_touch_rows() const
''' + touch_rows + r'''
void UIMenu::do_layout(int mw, int num_columns, bool just_checking)
''' + row_layout + r'''
string slot_description() { return "2/52 gear slots"; }
string _drop_menu_titlefn(const Menu*, const string&)
''' + drop_title + r'''
struct VColour { template<typename... T> VColour(T...) {} };
struct Buffer {
    void clear() {}
    template<typename... T> void add(T...) {}
};
struct Popup : Widget {
    Buffer m_buf;
    shared_ptr<Widget> m_child;
    int m_padding = 8, m_depth = 0, m_depth_indent = 0;
    bool m_centred = false;
    int base_margin() { return 0; }
    void _allocate_region()
''' + popup_allocation + r'''
};
int main() {
    for (int pixels : {21, 28, 42})
        for (int width : {320, 360, 540, 1080})
            for (bool fixed_header : {false, true})
            for (bool long_title : {false, true}) {
                font.pixels = pixels;
                Menu menu(0);
                menu.m_ui.title->m_text = string(long_title ? 90 : 5, 'T');
                // Menu templates are initialized before their first allocation.
                menu.m_ui.more->set_text_immediately(
                    formatted_string(string(long_title ? 5 : 90, 'F')));
                menu.m_ui.more->set_visible(true);
                if (fixed_header) {
                    auto label = make_shared<Text>();
                    label->m_text = formatted_string(string(26, 'H'));
                    label->set_wrap_text(true);
                    menu.m_ui.header->add_child(label);
                }
                Popup popup;
                popup.m_region = {0, 0, width, 1000};
                popup.m_child = menu.m_ui.vbox;
                popup._allocate_region();
                const Region region = menu.m_ui.vbox->m_region;
                assert(region.x >= popup.m_padding);
                assert(region.x + region.width <= width - popup.m_padding);
                assert(region.y >= popup.m_padding);
                assert(region.y + region.height <= 1000 - popup.m_padding);
                for (const auto& child : menu.m_ui.vbox->m_children) {
                    assert(child->m_region.y >= region.y);
                    if (child == menu.m_ui.header && !fixed_header)
                        assert(child->m_region.height == 0);
                    else
                        assert(child->m_region.height > 0);
                    assert(child->m_region.y + child->m_region.height
                           <= region.y + region.height);
                }
                assert(menu.m_ui.header->m_region.y + menu.m_ui.header->m_region.height
                       <= menu.m_ui.scroller->m_region.y);
                auto chrome = long_title ? menu.m_ui.title : menu.m_ui.more;
                assert(chrome->get_preferred_size(Widget::VERT, region.width).nat
                       > font.char_height());
            }
    for (int flags : {MF_NOSELECT, MF_NO_WRAP_ROWS}) {
        Menu menu(flags);
        assert(!menu.m_ui.title->wrap_text && !menu.m_ui.more->wrap_text);
    }
    // Device-equivalent 320dp/200%: 1080px wide, 890px remain above the native
    // keyboard, and MSG_FONT has a 95px line height. Run actual row wrapping,
    // title/header/footer size negotiation, scroller and popup allocation.
    font.pixels = 95;
    font.advance = 47;
    for (int flags : {MF_ARROWS_SELECT, MF_MULTISELECT})
        for (int chosen : {0, 4}) {
            Menu menu(flags);
            menu.chosen = chosen;
            menu.m_ui.title->m_text = formatted_string("General skills");
            auto label = make_shared<Text>();
            label->m_text = formatted_string("Show spell skills");
            label->set_wrap_text(true);
            menu.m_ui.header->add_child(label);
            const string footer = menu.get_keyhelp(true);
            menu.m_ui.more->set_text_immediately(formatted_string(footer));
            menu.m_ui.more->set_visible(!footer.empty());
            Popup popup;
            popup.m_region = {0, 0, 1080, 890};
            popup.m_child = menu.m_ui.vbox;
            popup._allocate_region();
            const auto& region = menu.m_ui.vbox->m_region;
            assert(region.x >= 0 && region.x + region.width <= 1080);
            assert(region.y >= 0 && region.y + region.height <= 890);
            const int first_row = menu.m_ui.menu->row_heights.at(1);
            assert(first_row >= 2 * font.char_height());
            assert(menu.m_ui.scroller->m_region.height >= first_row);
            if (flags == MF_MULTISELECT)
                assert(footer == make_stringf("Selected: %zu", size_t(chosen)));
            else
                assert(footer.empty());
            const auto header_y = menu.m_ui.header->m_region.y;
            menu.m_ui.scroller->m_scroll = first_row;
            menu.m_ui.scroller->_allocate_region();
            assert(menu.m_ui.header->m_region.y == header_y);
        }
    // The drop title, compact selected count, category heading and first item
    // must also fit together at the same large-text device dimensions.
    Menu drop(MF_MULTISELECT);
    drop.chosen = 1;
    drop.m_ui.title->m_text = formatted_string(_drop_menu_titlefn(&drop, ""));
    drop.m_ui.more->set_text_immediately(formatted_string(drop.get_keyhelp(true)));
    drop.m_ui.more->set_visible(true);
    drop.m_ui.menu->item_info[0].heading = true;
    drop.m_ui.menu->item_info[0].text = formatted_string("Weapons (select all of this category)");
    Popup drop_popup;
    drop_popup.m_region = {0, 0, 1080, 890};
    drop_popup.m_child = drop.m_ui.vbox;
    drop_popup._allocate_region();
    assert(drop.m_ui.vbox->m_region.y >= 0);
    assert(drop.m_ui.scroller->m_region.height >= drop.m_ui.menu->row_heights.at(2));
    // Desktop and fixed-column/read-only help retains the original keyhelp.
    tiles.small = false;
    Menu desktop(MF_ARROWS_SELECT);
    assert(!desktop.get_keyhelp(true).empty());
    tiles.small = true;
    for (int flags : {MF_NOSELECT, MF_NO_WRAP_ROWS}) {
        Menu fixed(flags);
        assert(!fixed.get_keyhelp(true).empty());
    }
}
''')

    def test_production_layout_wraps_all_lines_and_preserves_fixed_menus(self):
        source = (ROOT / "crawl-ref/source/menu.cc").read_text()
        layout = regression.block_after(source, "void UIMenu::do_layout")
        touch = regression.block_after(source, "bool uses_touch_rows() const")
        prefix = regression.block_after(source, "static bool _has_hotkey_prefix")
        regression.TargetingSafetyTests.run_cpp(self, r'''
#pragma GCC diagnostic ignored "-Wparentheses"
#define USE_TILE_LOCAL
#define __ANDROID__
#include <algorithm>
#include <cassert>
#include <climits>
#include <cmath>
#include <string>
#include <vector>
using namespace std;
struct formatted_string {
    string s;
    formatted_string() = default;
    formatted_string(string value) : s(value) {}
    string tostring() const { return s; }
    formatted_string chop(int n) const { return s.substr(0, n); }
    void del_char() { s.erase(0, 1); }
    void operator+=(const formatted_string& value) { s += value.s; }
};
// Deterministic font widths let us assert row geometry without needing GL.
struct Font {
    int char_height() const { return 21; }
    int string_width(const formatted_string& text) const {
        int longest = 0, current = 0;
        for (char ch : text.s) {
            if (ch == '\n') current = 0;
            else current += 10;
            longest = max(longest, current);
        }
        return longest;
    }
    int string_height(const formatted_string& text) const {
        return (1 + count(text.s.begin(), text.s.end(), '\n')) * char_height();
    }
    formatted_string split(const formatted_string& text, int width, unsigned) {
        assert(width > 0);
        string output;
        int columns = max(1, width / 10), current = 0;
        for (char ch : text.s) {
            if (ch == '\n') current = 0;
            else {
                if (current == columns) { output += '\n'; current = 0; }
                ++current;
            }
            output += ch;
        }
        return output;
    }
};
enum { MF_NOSELECT = 1, MF_NO_WRAP_ROWS = 2 };
struct Menu {
    vector<int> items;
    int flags = 0;
    bool is_set(int value) { return flags & value; }
};
struct { int game_scale = 1; } Options;
struct { int apply_game_scale(int value) { return value / Options.game_scale; } }
    display_density;
float density = 1;
float jni_get_display_density() { return density; }
bool _has_hotkey_prefix(const string& s)
''' + prefix + r'''
struct UIMenu {
    struct Item { int x=0, y=0, row=0, column=0; formatted_string text;
                  vector<int> tiles; bool heading=false; };
    Menu* m_menu;
    Font* m_font_entry;
    int m_min_col_width = -1, m_scroll_context = 0, m_height = 0;
    int m_nat_column_width = 0;
    bool m_draw_tiles = false;
    static constexpr int item_pad = 2, pad_right = 10;
    vector<Item> item_info;
    vector<int> row_heights;
    bool uses_touch_rows() const
''' + touch + r'''
    void do_layout(int mw, int num_columns, bool just_checking=false)
''' + layout + r'''
};
int main() {
    Font font;
    Menu menu;
    menu.items.resize(2);
    UIMenu ui;
    ui.m_menu = &menu;
    ui.m_font_entry = &font;
    ui.item_info.resize(2);
    ui.item_info[0].text = formatted_string(" a - short");
    ui.item_info[1].text = formatted_string(" b - " + string(100, 'L'));
    for (float d : {1.f, 1.5f, 2.f, 3.f})
        for (int scale : {1, 2, 3}) {
            density = d;
            Options.game_scale = scale;
            ui.do_layout(200, 1);
            assert(ui.row_heights.size() == 3);
            assert(ui.row_heights[1] * scale >= ceil(48 * d));
            // Full text occupies >2 lines, and the second row must fit all.
            int width = 200 - 50 - UIMenu::item_pad - UIMenu::pad_right;
            auto wrapped = font.split(formatted_string(string(100, 'L')), width, UINT_MAX);
            assert(font.string_height(wrapped) > 2 * font.char_height());
            assert(ui.row_heights[2] - ui.row_heights[1]
                   >= font.string_height(wrapped) + 2 * UIMenu::item_pad);
            assert(ui.item_info[1].y == ui.row_heights[1]);
        }
    // Skill rows contain explicit detail lines, even when the first line fits.
    ui.item_info[1].text = formatted_string(" c - A\nLevel 5\nTarget 10\nApt 1");
    ui.do_layout(1000, 1);
    assert(ui.row_heights[2] - ui.row_heights[1] >= 4 * font.char_height());
    // Fixed-column screens retain their one-line height instead of growing.
    menu.flags = MF_NO_WRAP_ROWS;
    ui.do_layout(200, 1);
    assert(ui.row_heights[1] == font.char_height() + 2 * UIMenu::item_pad);
    assert(ui.row_heights[2] == 2 * ui.row_heights[1]);
}
''')

    def test_skill_state_dispatch_preserves_help_targets_training_and_exit(self):
        source = (ROOT / "crawl-ref/source/skill-menu.cc").read_text()
        dispatch = regression.block_after(source, "static bool _process_skill_menu_key")
        regression.TargetingSafetyTests.run_cpp(self, r'''
#pragma GCC diagnostic ignored "-Wimplicit-fallthrough"
#include <cassert>
#include <vector>
using std::vector;
#define ASSERT assert
void dprf(const char*, int) {}
enum { CK_UP=1001, CK_DOWN, CK_LEFT, CK_RIGHT, CK_ENTER, CK_ESCAPE };
enum { SKMF_EXPERIENCE=1, SKMF_HELP=2, SKMF_SET_TARGET=4 };
enum { SKM_HELP=-2, SKM_CLEAR_TARGETS=-3, SKM_SET_TARGET=-4, SKM_SWITCH_FIRST=-5 };
enum skill_menu_switch { MODE=-5 };
enum skill_type { FIGHTING, SPELLCASTING };
bool is_invalid_skill(skill_type sk) { return sk < FIGHTING || sk > SPELLCASTING; }
namespace ui { bool key_exits_popup(int key, bool) { return key == CK_ESCAPE || key == CK_ENTER; } }
struct MenuItem { int id=0; int get_id() { return id; } };
struct Skills {
    bool handled=false, can_exit=true;
    int flags=0, exits=0, helps=0, clears=0, targets=0, toggles=0, selections=0;
    int selected_key=0, selected_skill=-1;
    vector<MenuItem*> selection;
    bool process_key(int) { return handled; }
    bool is_set(int value) { return flags & value; }
    bool exit(bool) { ++exits; return can_exit; }
    void cancel_help() { flags &= ~SKMF_HELP; }
    void cancel_set_target() { flags &= ~SKMF_SET_TARGET; }
    vector<MenuItem*> get_selected_items() { return selection; }
    void clear_selections() { selection.clear(); }
    void help() { ++helps; }
    void clear_targets() { ++clears; }
    void set_target_mode() { ++targets; }
    void toggle(skill_menu_switch) { ++toggles; }
    void select(skill_type sk, int key) { ++selections; selected_skill=sk; selected_key=key; }
} skm;
bool dispatch(int keyn)
''' + dispatch + r'''
int main() {
    assert(!dispatch(CK_ENTER) && !skm.exits);
    skm.flags = SKMF_HELP;
    assert(!dispatch(CK_ESCAPE) && !skm.flags && !skm.exits);
    skm.flags = SKMF_SET_TARGET;
    assert(!dispatch(CK_ESCAPE) && !skm.flags && !skm.exits);
    skm.can_exit = false;
    assert(!dispatch(CK_ESCAPE)); // no-training gate can refuse exit
    skm.can_exit = true;
    assert(dispatch(CK_ESCAPE));
    skm.flags = SKMF_EXPERIENCE;
    assert(dispatch(CK_ENTER));
    skm.handled = true;
    MenuItem item;
    const int ids[] = {SKM_HELP, SKM_CLEAR_TARGETS, SKM_SET_TARGET, SKM_SWITCH_FIRST, 1};
    for (int id : ids) {
        item.id = id;
        skm.selection = {&item};
        assert(!dispatch('B'));
        assert(skm.selection.empty());
    }
    assert(skm.helps == 1 && skm.clears == 1 && skm.targets == 1 && skm.toggles == 1);
    assert(skm.selections == 1 && skm.selected_skill == SPELLCASTING && skm.selected_key == 'B');
    assert(!dispatch('B') && skm.selections == 1); // no selection: no action
}
''')


    def test_skill_enter_uses_visible_selection_and_preserves_experience_confirm(self):
        source = (ROOT / "crawl-ref/source/skill-menu.cc").read_text()
        adapter = regression.block_after(source, "class AndroidSkillMenu : public Menu")
        process = regression.block_after(adapter, "bool process_key(int key)")
        regression.TargetingSafetyTests.run_cpp(self, r'''
#pragma GCC diagnostic ignored "-Wparentheses"
#include <algorithm>
#include <cassert>
#include <vector>
using std::vector;
using std::any_of;
using std::find;
enum { CK_UP=1001, CK_DOWN, CK_LEFT, CK_RIGHT, CK_PGUP, CK_PGDN, CK_HOME,
       CK_END, CK_ENTER, CK_MOUSE_B1, CK_MOUSE_B2, CK_ESCAPE, SKMF_EXPERIENCE };
enum skill_type { SK_NONE=-1, FIGHTING, SPELLCASTING };
bool is_invalid_skill(skill_type skill) { return skill == SK_NONE; }
int described = -1;
void describe_skill(skill_type skill) { described = skill; }
struct Entry { vector<int> hotkeys; };
using MenuEntry = Entry;
struct AndroidSkillEntry : Entry { skill_type skill = SK_NONE; };
struct Menu {
    int last_hovered = -1;
    vector<Entry*> items;
    bool process_key(int key) {
        if (key == CK_DOWN) ++last_hovered;
        if (key == CK_UP) --last_hovered;
        return true;
    }
};
struct {
    bool experience = false;
    int refreshes = 0;
    bool is_set(int flag) { return flag == SKMF_EXPERIENCE && experience; }
    void populate_android_menu(Menu&) { ++refreshes; }
} skm;
vector<int> dispatched;
bool _process_skill_menu_key(int key) {
    dispatched.push_back(key);
    return key == CK_ESCAPE;
}
struct AndroidSkillMenu : Menu {
    bool m_split_pages = true;
    void switch_page() {}
    void refresh_page() { skm.populate_android_menu(*this); }
    bool process_key(int key)
''' + process + r'''
};
int main() {
    AndroidSkillEntry first, second, information;
    first.hotkeys = {'a', 'A'};
    first.skill = FIGHTING;
    second.hotkeys = {'b', 'B'};
    second.skill = SPELLCASTING;
    AndroidSkillMenu menu;
    menu.items = {&first, &second, &information};
    menu.last_hovered = 0;
    assert(menu.process_key(CK_DOWN));
    assert(menu.last_hovered == 1 && dispatched.empty());
    assert(menu.process_key(CK_ENTER));
    assert(dispatched.back() == 'b'); // never the backend's previous cursor
    assert(menu.process_key(CK_MOUSE_B1));
    assert(dispatched.back() == 'b');
    const auto count = dispatched.size();
    assert(menu.process_key(CK_MOUSE_B2));
    assert(described == SPELLCASTING && dispatched.size() == count);
    assert(menu.process_key('B') && dispatched.back() == 'B');
    for (int no_selection : {-1, 2, 3}) {
        menu.last_hovered = no_selection;
        const auto before = dispatched.size();
        assert(menu.process_key(CK_ENTER));
        assert(menu.process_key(CK_MOUSE_B1));
        assert(dispatched.size() == before);
    }
    skm.experience = true;
    menu.last_hovered = 1;
    assert(menu.process_key(CK_ENTER) && dispatched.back() == CK_ENTER);
    assert(!menu.process_key(CK_ESCAPE) && dispatched.back() == CK_ESCAPE);
}
''')


if __name__ == "__main__":
    unittest.main()
