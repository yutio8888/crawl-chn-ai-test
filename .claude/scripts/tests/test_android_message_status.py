#!/usr/bin/env python3
"""Focused production-body checks for Android status and message controls.

Compile the real status producer, registry consumer, message bounds, renderer,
mouse handler and layer dispatch. Status cells use production UTF-8/chopping,
the repository fallback width table and nowrap formatter; font/JNI/GL dependencies remain
doubles. A deterministic wrapping font exercises message geometry and routing,
not FreeType/CJK glyph rasterization, GL output or actual game turns. Device
layout/font checks remain necessary for those boundaries.
"""

from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_android_quickbar as quickbar


SOURCE = Path(__file__).resolve().parents[3] / "crawl-ref/source"


def body(filename: str, anchor: str) -> str:
    return quickbar.block_after((SOURCE / filename).read_text(encoding="utf-8"), anchor)


COMMON = r'''
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdarg>
#include <cstdio>
#include <map>
#include <string>
#include <vector>
using namespace std;
#define USE_TILE_LOCAL
#define __ANDROID__
const char *T_(const char *text) { return text; }
struct coord_def {
    int x, y;
    coord_def(int x_ = 0, int y_ = 0) : x(x_), y(y_) {}
};
enum {
    CK_NO_KEY = -1, CMD_REPLAY_MESSAGES = 100, CMD_RESISTS_SCREEN,
    CMD_NO_CMD, CK_MOUSE_CMD, CK_MOUSE_CLICK,
    MOUSE_MODE_COMMAND, MOUSE_MODE_TARGET, MOUSE_MODE_MORE,
    MOUSE_MODE_PROMPT, MOUSE_MODE_YESNO, MOUSE_MODE_NORMAL
};
int current_mouse_mode = MOUSE_MODE_COMMAND;
namespace mouse_control { int current_mode() { return current_mouse_mode; } }
struct wm_mouse_event {
    enum { PRESS, RELEASE, MOVE, WHEEL, LEFT, RIGHT, MIDDLE };
    int event, button, px, py;
};
int encode_command_as_key(int command) { return command + 1000; }
'''


def status_text_contract() -> str:
    # Preserve defaults from the public declarations: chop_string pads unless
    # the caller explicitly opts out. Reusing only a truncating substr double
    # would miss a full-width label overwriting the preceding status lights.
    header = (SOURCE / "unicode.h").read_text(encoding="utf-8")
    declarations = "\n".join(line for line in header.splitlines()
                             if line.startswith("string chop_string("))
    # The repository fallback wcwidth table makes cell widths deterministic;
    # this does not claim to exercise Android libc/FreeType glyph metrics.
    functions = [
        ("wcwidth.cc", "struct interval", ";"),
        ("wcwidth.cc", "static int bisearch(char32_t ucs, const struct interval *table, char32_t max)", ""),
        ("wcwidth.cc", "int wcwidth(char32_t ucs)", ""),
        ("unicode.cc", "int utf8towc(char32_t *d, const char *s)", ""),
        ("unicode.cc", "int strwidth(const char *s)", ""),
        ("unicode.cc", "int strwidth(const string &s)", ""),
        ("unicode.cc", "string chop_string(const char *s, int width, bool spaces)", ""),
        ("unicode.cc", "string chop_string(const string &s, int width, bool spaces)", ""),
    ]
    return declarations + "\n" + "\n".join(
        signature + "\n" + body(filename, signature) + suffix
        for filename, signature, suffix in functions)


def status_fixture() -> str:
    output = (SOURCE / "output.cc").read_text(encoding="utf-8")
    getter = quickbar.block_after(output, "static void _get_status_lights")
    priority = quickbar.block_after(getter, "const unsigned int important_statuses[]")
    statuses = re.findall(r"\b(?:STATUS|DUR)_[A-Z_]+\b", priority)
    return COMMON + r'''
#include <bitset>
#define ARRAYSZ(array) (sizeof(array) / sizeof((array)[0]))
using colour_t = int;
enum { LIGHTCYAN, GOTO_STAT };
''' + "enum { " + ", ".join(statuses) + ", STATUS_LAST_STATUS = 256 };\n" + status_text_contract() + r'''
struct status_light
''' + quickbar.block_after(output, "struct status_light") + r''';
struct { bool redraw_status_lights = true; } you;
struct { coord_def hudsz = coord_def(40, 6), hudp = coord_def(1, 1); } crawl_view;
bool top_bar = true;
bool _uses_top_bar() { return top_bar; }
bool _uses_compact_hud() { return false; }
struct { bool is_using_small_layout() { return top_bar; } } tiles;
map<int, string> available_statuses;
void _add_status_light_to_out(int status, vector<status_light> &out) {
    auto it = available_statuses.find(status);
    if (it != available_statuses.end()) out.emplace_back(0, it->second, status);
}
struct status_hitbox { int status, x1, x2, y; };
vector<status_hitbox> _status_hitboxes;
void clear_status_hitboxes()
''' + body("tilereg-stat.cc", "void clear_status_hitboxes()") + r'''
void record_status_hitbox(int status, int x1, int x2, int y)
''' + body("tilereg-stat.cc", "void record_status_hitbox") + r'''
struct Paint { int x, y; string text; };
vector<Paint> paints;
map<pair<int, int>, char32_t> cells;
int cursor_x = 1, cursor_y = 1;
// LAYER_NORMAL get_number_of_cols() returns the message-region width even
// while CGOTOXY selects the status region. Keep these two widths independent.
int message_columns = 20;
int get_number_of_cols() { return message_columns; }
int wherex() { return cursor_x; }
void move_cursor(int x, int y, int) { cursor_x = x; cursor_y = y; }
#define CGOTOXY move_cursor
string vmake_stringf(const char *format, va_list args) {
    char buffer[2048];
    vsnprintf(buffer, sizeof(buffer), format, args);
    return buffer;
}
string make_stringf(const char *format, ...) {
    va_list args;
    va_start(args, format);
    string result = vmake_stringf(format, args);
    va_end(args);
    return result;
}
void cprintf(const char *format, ...) {
    va_list args;
    va_start(args, format);
    string text = vmake_stringf(format, args);
    va_end(args);
    paints.push_back({cursor_x, cursor_y, text});
    // Model the actual cell writes, including later writes overwriting prior
    // text. Draw-call presence by itself cannot prove the status survived.
    const char *next = text.c_str();
    char32_t glyph;
    while (int bytes = utf8towc(&glyph, next)) {
        int width = wcwidth(glyph);
        assert(width >= 0);
        for (int i = 0; i < width; ++i) {
            assert(cursor_x >= 1 && cursor_x <= crawl_view.hudsz.x);
            cells[{cursor_x++, cursor_y}] = i == 0 ? glyph : 0;
        }
        next += bytes;
    }
}
void nowrap_eol_cprintf(const char *s, ...)
''' + body("cio.cc", "void nowrap_eol_cprintf(const char *s, ...)") + r'''
// Top-bar TouchUI dispatches CPRINTF to cprintf and NOWRAP to this production
// formatter. Unlike CPRINTF it truncates against message_columns above.
#define NOWRAP_EOL_CPRINTF nowrap_eol_cprintf
#define CPRINTF cprintf
void textcolour(int) {}
void clear_to_end_of_line() {
    for (int x = cursor_x; x <= crawl_view.hudsz.x; ++x) cells[{x, cursor_y}] = ' ';
}
void assert_text_at(int x, int y, const string &text) {
    const char *next = text.c_str();
    char32_t glyph;
    while (int bytes = utf8towc(&glyph, next)) {
        int width = wcwidth(glyph);
        for (int i = 0; i < width; ++i) {
            pair<int, int> cell = {x++, y};
            assert(cells.at(cell) == (i == 0 ? glyph : 0));
        }
        next += bytes;
    }
}
static void _get_status_lights(vector<status_light> &out)
''' + getter + r'''
static void _print_status_lights(int y)
''' + quickbar.block_after(output, "static void _print_status_lights(int y)") + r'''
int opened_status = -999;
void show_topbar_status_drawer(int status) { opened_status = status; }
using command_type = int;
command_type show_topbar_command_menu(bool *) { return CMD_NO_CMD; }
struct StatRegion {
    int m_last_mouse_x = 0, m_last_mouse_y = 0;
    bool inside(int x, int y) {
        return x >= 0 && x < crawl_view.hudsz.x && y >= 0 && y < crawl_view.hudsz.y;
    }
    bool _text_mouse_pos(int x, int y, int &cx, int &cy) {
        cx = x; cy = y; return inside(x, y);
    }
    int handle_mouse(wm_mouse_event &event);
};
int StatRegion::handle_mouse(wm_mouse_event &event)
''' + body("tilereg-stat.cc", "int StatRegion::handle_mouse")


def message_fixture() -> str:
    return COMMON + r'''
#include <climits>
#include <cstring>
struct formatted_string : string {
    using string::string;
    formatted_string() = default;
    formatted_string(const string &text) : string(text) {}
    static formatted_string parse_string(const string &text) { return text; }
    string tostring() const { return *this; }
    formatted_string substr_bytes(size_t start, size_t count) const { return substr(start, count); }
};
bool ends_with(const formatted_string &text, const string &suffix) {
    return text.size() >= suffix.size()
        && text.compare(text.size() - suffix.size(), suffix.size(), suffix) == 0;
}
struct { int game_scale = 1; } Options;
struct Density {
    int game_scale = 1;
    int apply_game_scale(int n) const
''' + body("tilesdl.h", "constexpr int apply_game_scale(int n) const") + r'''
} display_density;
float density = 1;
float jni_get_display_density() { return density; }
struct { bool small = true; bool is_using_small_layout() { return small; } } tiles;
struct Font {
    int height = 14, cell = 7;
    bool oversize = false;
    vector<coord_def> text_positions;
    vector<formatted_string> rendered_labels;
    unsigned char_height() const { return height; }
    unsigned string_height(const formatted_string &text) const {
        return height * (1 + count(text.begin(), text.end(), '\n'));
    }
    unsigned string_width(const formatted_string &text) const {
        size_t maximum = 0, line = 0;
        for (char c : text) {
            if (c == '\n') { maximum = max(maximum, line); line = 0; }
            else ++line;
        }
        return cell * max(maximum, line);
    }
    // Match the relevant FT split contract: unsigned limits, and empty output
    // when there is not even one line. Precise glyph/word wrapping is not
    // simulated; fixed ASCII cells cover the caller's size/hitbox invariants.
    formatted_string split(const formatted_string &text, unsigned width, unsigned max_height) {
        assert(width < 100000 && max_height < 100000); // reject signed underflow
        if (max_height < unsigned(height) || width < unsigned(cell)) return {};
        if (oversize) return text; // a font cannot always fit an ellipsis/glyph
        size_t columns = width / cell;
        size_t max_lines = max_height / height;
        string result;
        size_t lines = 1, col = 0;
        for (char c : text) {
            if (col == columns) {
                if (++lines > max_lines) break;
                result += '\n'; col = 0;
            }
            result += c; ++col;
        }
        return result;
    }
    void render_textblock(int, int, const vector<char32_t> &, const vector<uint8_t> &,
                          int, int, bool) {}
    void render_string(int x, int y, const formatted_string &text) {
        text_positions.emplace_back(x, y); rendered_labels.push_back(text);
    }
};
struct VColour { VColour(int = 0, int = 0, int = 0, int = 0) {} };
struct Rect { int x1, y1, x2, y2; };
vector<Rect> shapes;
struct ShapeBuffer {
    void add(int x1, int y1, int x2, int y2, VColour) { shapes.push_back({x1, y1, x2, y2}); }
    void draw() {}
};
struct GL { void reset_transform() {} } gl, *glmanager = &gl;
enum { WHITE = 15 };
struct Region {
    virtual int handle_mouse(wm_mouse_event &) = 0;
    virtual ~Region() = default;
};
struct TextRegion : Region { static TextRegion *cursor_region; };
TextRegion *TextRegion::cursor_region = nullptr;
struct MessageRegion : TextRegion {
    Font *m_font;
    bool m_overlay = true;
    int mx = 20, my = 2, sx = 10, sy = 450, ex = 710, ey = 480;
    int ox = 0, oy = 0, cursor_x = 0, cursor_y = 0;
    string m_alt_text;
    VColour m_overlay_col;
    vector<char32_t> cbuf = vector<char32_t>(1000, ' ');
    vector<uint8_t> abuf = vector<uint8_t>(1000, 0);
    explicit MessageRegion(Font *font) : m_font(font) {}
    bool inside(int x, int y) { return x >= sx && x < ex && y >= sy && y < ey; }
    bool history_button_bounds(coord_def &start, coord_def &end, formatted_string &label) const;
    int handle_mouse(wm_mouse_event &event) override;
    void render();
};
bool MessageRegion::history_button_bounds(coord_def &start, coord_def &end,
                                           formatted_string &label) const
''' + body("tilereg-msg.cc", "bool MessageRegion::history_button_bounds") + r'''
int MessageRegion::handle_mouse(wm_mouse_event &event)
''' + body("tilereg-msg.cc", "int MessageRegion::handle_mouse") + r'''
void MessageRegion::render()
''' + body("tilereg-msg.cc", "void MessageRegion::render()") + r'''
struct Layer { vector<Region *> m_regions; };
struct TilesFramework {
    int m_active_layer = 0;
    vector<Layer> m_layers = vector<Layer>(1);
    int handle_quick_row_mouse(wm_mouse_event &) { return 0; }
    int handle_mouse(wm_mouse_event &event);
};
int TilesFramework::handle_mouse(wm_mouse_event &event)
''' + body("tilesdl.cc", "int TilesFramework::handle_mouse") + r'''
struct Dungeon : Region {
    int calls = 0;
    int handle_mouse(wm_mouse_event &) override { ++calls; return 9000; }
};
'''


class AndroidMessageStatusTests(unittest.TestCase):
    def run_cpp(self, source: str) -> None:
        quickbar.TargetingSafetyTests.run_cpp(self, source)

    def test_status_count_digit_transitions_and_full_row_hitbox(self) -> None:
        self.run_cpp(status_fixture() + r'''
int main() {
    StatRegion region;
    for (int count : {0, 1, 9, 10, 11, 99, 100, 101}) {
        available_statuses.clear();
        for (int i = 0; i < count; ++i) available_statuses[100 + i] = "s" + to_string(i);
        vector<status_light> ordered;
        _get_status_lights(ordered);
        for (int width = 1; width <= 100; ++width) {
            crawl_view.hudsz.x = width;
            message_columns = max(1, width / 2);
            paints.clear();
            _print_status_lights(3);
            assert(!you.redraw_status_lights);
            // Independent exhaustive candidate search verifies the greatest
            // prefix that fits, including hidden counts growing 9 -> 10.
            size_t visible = 0;
            for (size_t candidate = 0; candidate <= ordered.size(); ++candidate) {
                int occupied = 0;
                for (size_t i = 0; i < candidate; ++i) occupied += ordered[i].text.size() + 1;
                int hidden = ordered.size() - candidate;
                string label = hidden ? "[All statuses +" + to_string(hidden) + "]"
                                      : "[All statuses]";
                if (occupied + int(label.size()) <= width) visible = candidate;
            }
            int hidden = ordered.size() - visible;
            string label = hidden ? "[All statuses +" + to_string(hidden) + "]"
                                  : "[All statuses]";
            label = label.substr(0, width);
            assert(paints.size() == visible + 1);
            assert(paints.back().text == label);
            assert_text_at(paints.back().x, paints.back().y, label);
            assert(paints.back().x + int(label.size()) - 1 == width);
            assert(_status_hitboxes.size() == visible + 1);
            for (size_t i = 0; i < visible; ++i) {
                assert(paints[i].text == ordered[i].text);
                assert_text_at(paints[i].x, paints[i].y, ordered[i].text);
                assert(_status_hitboxes[i].status == ordered[i].status);
                assert(_status_hitboxes[i].x2 < paints.back().x - 1);
            }
            const auto &fallback = _status_hitboxes.back();
            assert(fallback.status == -1 && fallback.x1 == 0 && fallback.x2 == width - 1);
            assert(fallback.y == 2);
            // Execute the real consumer at every column: the first matching
            // individual box wins; whitespace and the button open the full list.
            for (int x = 0; x < width; ++x) {
                int expected = -1;
                for (size_t i = 0; i < visible; ++i)
                    if (x >= _status_hitboxes[i].x1 && x <= _status_hitboxes[i].x2)
                        expected = _status_hitboxes[i].status;
                wm_mouse_event event{wm_mouse_event::PRESS, wm_mouse_event::LEFT, x, 2};
                opened_status = -999;
                assert(region.handle_mouse(event) == CK_NO_KEY);
                assert(opened_status == expected);
            }
        }
    }
}
''')

    def test_status_and_button_survive_padding_and_narrower_message_width(self) -> None:
        self.run_cpp(status_fixture() + r'''
int main() {
    // These are production Unicode functions, including the public default.
    assert(chop_string("x", 4) == "x   ");
    assert(chop_string("x", 4, false) == "x");
    assert(chop_string("中文", 3) == "中 ");
    assert(chop_string("中文", 3, false) == "中");
    assert(strwidth("中文") == 4);
    available_statuses[DUR_CONF] = "confused";
    available_statuses[DUR_HASTE] = "haste";
    available_statuses[200] = "中文";
    crawl_view.hudsz.x = 60;
    for (int msg_width : {1, 8, 20, 40, 60, 100}) {
        message_columns = msg_width;
        paints.clear(); cells.clear();
        _print_status_lights(3);
        assert(paints.size() == 4);
        assert(paints[0].text == "confused");
        assert(paints[1].text == "haste");
        assert(paints[2].text == "中文");
        assert(paints[3].text == "[All statuses]");
        const int button_x = 60 - strwidth("[All statuses]") + 1;
        assert(paints[3].x == button_x);
        assert(paints[2].x + strwidth(paints[2].text) < button_x);
        assert_text_at(1, 3, "confused");
        assert_text_at(10, 3, "haste");
        assert_text_at(16, 3, "中文");
        assert_text_at(button_x, 3, "[All statuses]");
        // Verify that NOWRAP is genuinely different from CPRINTF in this
        // fixture, so changing the production sink back cannot falsely pass.
        paints.clear();
        CGOTOXY(button_x, 4, GOTO_STAT);
        NOWRAP_EOL_CPRINTF("%s", "[All statuses]");
        if (msg_width <= 40) assert(paints.back().text.empty());
        if (msg_width == 100) assert(paints.back().text == "[All statuses]");
    }
}
''')

    def test_status_priority_order_and_registry_clearing_across_empty_layouts(self) -> None:
        self.run_cpp(status_fixture() + r'''
int main() {
    available_statuses[DUR_HASTE] = "haste";
    available_statuses[200] = "ordinary";
    available_statuses[DUR_CONF] = "confused";
    crawl_view.hudsz.x = 26;
    _print_status_lights(3);
    assert(_status_hitboxes.front().status == DUR_CONF);
    assert(paints.front().text == "confused");
    assert(paints.back().text == "[All statuses +2]");
    paints.clear();
    crawl_view.hudsz.x = 60;
    _print_status_lights(3);
    assert(_status_hitboxes[0].status == DUR_CONF);
    assert(_status_hitboxes[1].status == DUR_HASTE);
    assert(_status_hitboxes[2].status == 200);
    available_statuses.clear();
    paints.clear();
    _print_status_lights(4);
    assert(_status_hitboxes.size() == 1 && _status_hitboxes[0].status == -1);
    assert(_status_hitboxes[0].y == 3);
    assert(paints.size() == 1 && paints[0].text == "[All statuses]");
    // The early return for an already-empty non-top-bar HUD must also clear
    // a previous layout's full-row box, not just its individual statuses.
    top_bar = false;
    paints.clear();
    _print_status_lights(4);
    assert(_status_hitboxes.empty());
    assert(paints.empty());
    record_status_hitbox(200, 1, 8, 3);
    _print_status_lights(4);
    assert(_status_hitboxes.empty());
}
''')

    def test_history_geometry_render_and_hidden_modes(self) -> None:
        self.run_cpp(message_fixture() + r'''
int main() {
    Font font;
    MessageRegion region(&font);
    coord_def start, end;
    formatted_string label;
    for (float dpi : {0.75f, 1.0f, 2.625f, 3.375f}) {
        for (int scale : {1, 2, 3}) {
            for (int font_height : {8, 14, 28, 70, 140}) {
                density = dpi;
                Options.game_scale = display_density.game_scale = scale;
                font.height = font_height;
                font.cell = max(1, font_height / 2);
                region.ex = region.sx + 1080 / scale;
                region.sy = 1000 / scale;
                assert(region.history_button_bounds(start, end, label));
                int touch_pixels = int(ceil(48 * dpi));
                assert((end.x - start.x) * scale >= touch_pixels);
                assert((end.y - start.y) * scale >= touch_pixels);
                assert(start.x >= region.sx && start.y >= 0);
                assert(end.x == region.ex && end.y == region.sy);
                assert(!label.empty());
                assert(font.string_width(label) <= unsigned(end.x - start.x));
                assert(font.string_height(label) <= unsigned(end.y - start.y));
                shapes.clear();
                font.text_positions.clear();
                font.rendered_labels.clear();
                region.render();
                assert(shapes.size() == 1); // blank message buffer has no overlay background
                assert(shapes[0].x1 == start.x && shapes[0].y1 == start.y);
                assert(shapes[0].x2 == end.x && shapes[0].y2 == end.y);
                assert(font.rendered_labels.size() == 1 && font.rendered_labels[0] == label);
                assert(font.text_positions[0].x >= start.x && font.text_positions[0].y >= start.y);
                assert(font.text_positions[0].x + int(font.string_width(label)) <= end.x);
                assert(font.text_positions[0].y + int(font.string_height(label)) <= end.y);
            }
        }
    }
    density = 1;
    Options.game_scale = display_density.game_scale = 1;
    font.height = 14; font.cell = 7;
    region.sx = 10; region.ex = 710; region.sy = 450;
    for (int mode : {MOUSE_MODE_TARGET, MOUSE_MODE_MORE, MOUSE_MODE_PROMPT,
                     MOUSE_MODE_YESNO, MOUSE_MODE_NORMAL}) {
        current_mouse_mode = mode;
        assert(!region.history_button_bounds(start, end, label));
        shapes.clear(); region.render(); assert(shapes.empty());
    }
    current_mouse_mode = MOUSE_MODE_COMMAND;
    region.m_overlay = false;
    assert(!region.history_button_bounds(start, end, label));
    region.m_overlay = true; tiles.small = false;
    assert(!region.history_button_bounds(start, end, label));
    tiles.small = true; region.mx = 0;
    assert(!region.history_button_bounds(start, end, label));
    region.mx = 20; region.my = 0;
    assert(!region.history_button_bounds(start, end, label));
    region.my = 2; region.ex = region.sx + 47;
    assert(!region.history_button_bounds(start, end, label));
    region.ex = 710; region.sy = 47;
    assert(!region.history_button_bounds(start, end, label));
    // Positive touch dimensions do not guarantee a line of large text fits.
    font.height = 80; font.cell = 40; region.sy = 60;
    assert(!region.history_button_bounds(start, end, label));
    region.sy = 450; region.ex = region.sx + 48; font.height = 160;
    assert(!region.history_button_bounds(start, end, label));
    font.height = 14; font.cell = 7; font.oversize = true;
    region.ex = region.sx + 48;
    assert(!region.history_button_bounds(start, end, label));
}
''')

    def test_history_click_edges_consume_other_events_and_preserve_plain_messages(self) -> None:
        # The fixture uses the actual normal-layer order. Reverse dispatch must
        # reach the message control before any dungeon action is considered.
        initialise = body("tilesdl.cc", "bool TilesFramework::initialise()")
        self.assertLess(
            initialise.index("m_layers[LAYER_NORMAL].m_regions.push_back(m_region_tile)"),
            initialise.index("m_layers[LAYER_NORMAL].m_regions.push_back(m_region_msg)"))
        self.run_cpp(message_fixture() + r'''
int main() {
    Font font;
    MessageRegion region(&font);
    Dungeon dungeon;
    TilesFramework framework;
    framework.m_layers[0].m_regions = {&dungeon, &region};
    coord_def start, end;
    formatted_string label;
    assert(region.history_button_bounds(start, end, label));
    for (int type : {wm_mouse_event::PRESS, wm_mouse_event::RELEASE,
                     wm_mouse_event::MOVE, wm_mouse_event::WHEEL}) {
        for (int button : {wm_mouse_event::LEFT, wm_mouse_event::RIGHT, wm_mouse_event::MIDDLE}) {
            for (coord_def point : {start, coord_def(end.x - 1, end.y - 1)}) {
                wm_mouse_event event{type, button, point.x, point.y};
                int expected = type == wm_mouse_event::PRESS && button == wm_mouse_event::LEFT
                    ? encode_command_as_key(CMD_REPLAY_MESSAGES) : CK_NO_KEY;
                assert(region.handle_mouse(event) == expected);
                dungeon.calls = 0;
                assert(framework.handle_mouse(event) == (expected == CK_NO_KEY ? 0 : expected));
                assert(dungeon.calls == 0);
            }
        }
    }
    // Right/bottom are exclusive; the overlay itself retains its old behavior
    // away from the explicit history control.
    for (coord_def point : {coord_def(start.x - 1, start.y),
                           coord_def(start.x, start.y - 1),
                           coord_def(end.x, start.y), coord_def(start.x, end.y)}) {
        wm_mouse_event event{wm_mouse_event::PRESS, wm_mouse_event::LEFT, point.x, point.y};
        assert(region.handle_mouse(event) == 0);
        dungeon.calls = 0;
        assert(framework.handle_mouse(event) == 9000 && dungeon.calls == 1);
    }
    region.m_overlay = false;
    for (int mode : {MOUSE_MODE_COMMAND, MOUSE_MODE_TARGET, MOUSE_MODE_MORE}) {
        current_mouse_mode = mode;
        for (int type : {wm_mouse_event::PRESS, wm_mouse_event::RELEASE, wm_mouse_event::MOVE}) {
            for (int button : {wm_mouse_event::LEFT, wm_mouse_event::RIGHT, wm_mouse_event::MIDDLE}) {
                wm_mouse_event event{type, button, region.sx, region.sy};
                bool accepts = mode == MOUSE_MODE_COMMAND && type == wm_mouse_event::PRESS
                    && button == wm_mouse_event::LEFT;
                assert(region.handle_mouse(event) == (accepts
                    ? encode_command_as_key(CMD_REPLAY_MESSAGES) : 0));
                event.px = region.ex;
                assert(region.handle_mouse(event) == 0);
            }
        }
    }
}
''')


if __name__ == "__main__":
    unittest.main()
