#!/usr/bin/env python3
"""Exercise the production prompt routing and input contract.

UI doubles record TextEntry construction and invoke the real popup callback.
They do not model layout or rendering: IME resize/live-edit display needs the
Android device test, while these checks guard routing and the existing prompt
contract on both Android and desktop.
"""

from pathlib import Path
import sys
import unittest

# CI enables PYTHONSAFEPATH, so resolve the shared fixture explicitly.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_android_quickbar as regression


SOURCE = Path(__file__).resolve().parents[3] / "crawl-ref/source"


class AndroidImeInputTests(unittest.TestCase):
    def run_cpp(self, source):
        regression.TargetingSafetyTests.run_cpp(self, source)

    def prompt_fixture(self, android):
        source = (SOURCE / "message.cc").read_text(encoding="utf-8")
        unicode = (SOURCE / "unicode.cc").read_text(encoding="utf-8")
        utf8towc = regression.block_after(unicode, "int utf8towc(char32_t *d, const char *s)")
        signature = "int msgwin_get_line(string prompt, char *buf, int len,"
        return ("#define __ANDROID__\n" if android else "") + r'''
#include <cassert>
#include <cstring>
#include <functional>
#include <memory>
#include <string>
#include <vector>
using namespace std;
#define USE_TILE_LOCAL
enum { MOUSE_MODE_PROMPT, MSGCH_PROMPT, CK_ENTER = 13, CK_ESCAPE = 27 };
struct mouse_control { explicit mouse_control(int) {} };
struct input_history {};
struct { bool need_save; } crawl_state;
using msg_colour_type = int;
void linebreak_string(string &, int) {}
int prepare_message(const string &, int, int) { return 0; }
int colour_msg(int colour) { return colour; }
struct formatted_string : string {
    formatted_string(const string &text, int) : string(text) {}
};
bool has_layout = false;
bool small_layout = false;
int crt_font, msg_font;
struct Tiles {
    bool is_using_small_layout() { return small_layout; }
    int *get_msg_font() { return &msg_font; }
} tiles;
int *prompt_font;
bool prompt_wrap;
int popup_calls, legacy_calls, finish_key;
bool expected_numeric;
input_history *expected_history;
string expected_fill, incoming;
namespace ui {
bool has_layout() { return ::has_layout; }
struct Widget { enum { VERT }; };
struct Box {
    explicit Box(int) {}
    template<typename T> void add_child(shared_ptr<T>) {}
};
struct Text {
    explicit Text(const string &) { prompt_font = &crt_font; prompt_wrap = false; }
    void set_font(int *font) { prompt_font = font; }
    void set_wrap_text(bool wrap) { prompt_wrap = wrap; }
};
struct KeyEvent {
    int value;
    int key() const { return value; }
};
bool key_exits_popup(int key, bool) { return key == CK_ESCAPE; }
struct Popup {
    explicit Popup(shared_ptr<Box>) {}
    function<bool(const KeyEvent &)> callback;
    void on_hotkey_event(function<bool(const KeyEvent &)> cb) { callback = cb; }
};
struct TextEntry {
    string text;
    input_history *history = nullptr;
    bool numeric = false;
    int *font = &crt_font;
    void set_font(int *value) { font = value; }
    void set_sync_id(const string &id) { assert(id == "input"); }
    void set_text(const string &value) { text = value; }
    void set_input_history(input_history *value) { history = value; }
    void set_numeric_input(bool value) { numeric = value; }
    const string &get_text() { return text; }
};
void run_layout(shared_ptr<Popup> popup, bool &done, shared_ptr<TextEntry> input) {
    ++popup_calls;
    assert(input->text == expected_fill);
    assert(input->history == expected_history);
    assert(input->numeric == expected_numeric);
#ifdef __ANDROID__
    assert(input->font == (small_layout ? &msg_font : &crt_font));
    assert(prompt_font == input->font);
    if (small_layout) assert(prompt_wrap);
#else
    assert(input->font == &crt_font && prompt_font == &crt_font);
#endif
    assert(!popup->callback(KeyEvent{'x'}) && !done);
    input->text += incoming;
    assert(popup->callback(KeyEvent{finish_key}) && done);
}
}
void msgwin_prompt(const string &) {}
void msgwin_reply(const string &) {}
int cancellable_get_line(char *buf, int len, input_history *history, void *,
                         const string &fill, const string &, bool numeric) {
    ++legacy_calls;
    assert(fill == expected_fill && history == expected_history);
    assert(numeric == expected_numeric);
    string result = fill + incoming;
    strncpy(buf, result.c_str(), len - 1);
    buf[len - 1] = 0;
    return finish_key == CK_ENTER ? 0 : CK_ESCAPE;
}
int utf8towc(char32_t *d, const char *s)
''' + utf8towc + r'''
int msgwin_get_line(string prompt, char *buf, int len,
                    input_history *mh, const string &fill, bool numeric_input)
''' + regression.block_after(source, signature) + r'''
int main() {
    input_history history;
    for (bool in_game : {false, true})
    for (bool layout : {false, true})
    for (bool small : {false, true})
    for (bool numeric : {false, true})
    for (int key : {CK_ENTER, CK_ESCAPE})
    for (int capacity = 1; capacity <= 64; ++capacity) {
        crawl_state.need_save = in_game;
        has_layout = layout;
        small_layout = small;
        popup_calls = legacy_calls = 0;
        expected_numeric = numeric;
        expected_history = &history;
        expected_fill = numeric ? "12" : "pre";
        incoming = numeric ? "3456789" : "测试中文\xF0\x9F\x98\x80Z";
        finish_key = key;
        char output[65];
        memset(output, '?', sizeof output);
        const int result = msgwin_get_line("prompt", output, capacity,
                                          &history, expected_fill, numeric);
#ifdef __ANDROID__
        const bool expect_popup = true;
#else
        const bool expect_popup = !in_game || layout;
#endif
        assert(popup_calls == int(expect_popup));
        assert(legacy_calls == int(!expect_popup));
        assert(result == (key == CK_ENTER ? 0 : CK_ESCAPE));
        // Explicit valid prefixes are independent of the production decoder.
        // Every possible cut through the CJK and four-byte character is tried.
        const vector<string> prefixes = numeric
            ? vector<string>{"", "1", "12", "123", "1234", "12345", "123456",
                             "1234567", "12345678", "123456789"}
            : vector<string>{"", "p", "pr", "pre", "pre测", "pre测试", "pre测试中",
                             "pre测试中文", "pre测试中文\xF0\x9F\x98\x80",
                             "pre测试中文\xF0\x9F\x98\x80Z"};
        string expected;
        for (const string &prefix : prefixes)
            if (prefix.size() < static_cast<size_t>(capacity)) expected = prefix;
        if (expect_popup) {
            assert(string(output) == expected);
            assert(output[expected.size()] == '\0');
            for (size_t offset = 0; offset < expected.size();) {
                char32_t cp;
                const int bytes = utf8towc(&cp, output + offset);
                assert(bytes > 0 && cp != 0xFFFD);
                offset += bytes;
                assert(offset <= expected.size());
            }
        } else {
            // The legacy route is only a call-recording double in this test.
            assert(string(output) == (expected_fill + incoming).substr(0, capacity - 1));
        }
        assert(output[capacity] == '?');
    }
}
'''

    def test_android_in_game_prompts_keep_popup_input_contract(self):
        self.run_cpp(self.prompt_fixture(android=True))

    def test_desktop_keeps_existing_popup_selection(self):
        self.run_cpp(self.prompt_fixture(android=False))

    def test_mobile_history_reflows_but_other_layouts_keep_fixed_lines(self):
        production = (SOURCE / "message.cc").read_text(encoding="utf-8")
        body = regression.block_after(production, "void replay_messages()")
        for android in (False, True):
            self.run_cpp(("#define __ANDROID__\n" if android else "") + r'''
#include <cassert>
enum { FS_START_AT_END = 1, FS_PREWRAPPED_TEXT = 2 };
bool small_layout;
struct Tiles { bool is_using_small_layout() { return small_layout; } } tiles;
struct formatted_scroller {
    int flags;
    explicit formatted_scroller(int value) : flags(value) {}
    void set_more() {}
};
int seen_flags;
void _replay_messages_core(formatted_scroller &history) { seen_flags = history.flags; }
void replay_messages()
''' + body + r'''
int main() {
    for (int small = 0; small < 2; ++small) {
        small_layout = small;
        replay_messages();
        assert(seen_flags & FS_START_AT_END);
#ifdef __ANDROID__
        assert(bool(seen_flags & FS_PREWRAPPED_TEXT) == !small_layout);
#else
        assert(seen_flags & FS_PREWRAPPED_TEXT);
#endif
    }
}
''')

    def test_native_utf8_event_chunks_preserve_full_commit(self):
        source = (SOURCE / "windowmanager-sdl.cc").read_text(encoding="utf-8")
        unicode = (SOURCE / "unicode.cc").read_text(encoding="utf-8")
        helper = regression.block_after(source, "static void _queue_android_text_input")
        utf8towc = regression.block_after(unicode, "int utf8towc(char32_t *d, const char *s)")
        wctoutf8 = regression.block_after(unicode, "int wctoutf8(char *d, char32_t s)")
        self.run_cpp(r'''
#include <algorithm>
#include <cassert>
#include <cstring>
#include <string>
#include <vector>
using namespace std;
#define ASSERT assert
enum { SDL_TEXTINPUT = 1, SDL_ENABLE = 1 };
union SDL_Event {
    int type;
    struct { int type; unsigned windowID; char text[32]; } text;
};
struct SDL_Window { unsigned id; } window = {42};
SDL_Window *focus = &window;
int text_state = SDL_ENABLE;
int SDL_GetEventState(int) { return text_state; }
SDL_Window *SDL_GetKeyboardFocus() { return focus; }
unsigned SDL_GetWindowID(SDL_Window *value) { return value->id; }
vector<SDL_Event> queued;
int SDL_PushEvent(SDL_Event *event) { queued.push_back(*event); return 1; }
int utf8towc(char32_t *d, const char *s)
''' + utf8towc + r'''
int wctoutf8(char *d, char32_t s)
''' + wctoutf8 + r'''
static void _queue_android_text_input(const string &text)
''' + helper + r'''
void check(const string &input, const string &expected) {
    queued.clear();
    _queue_android_text_input(input);
    string joined;
    for (const SDL_Event &event : queued) {
        assert(event.type == SDL_TEXTINPUT);
        assert(event.text.windowID == (focus ? 42 : 0));
        const size_t length = strlen(event.text.text);
        assert(length > 0 && length < sizeof event.text.text);
        // Each chunk independently decodes: a correct concatenated byte stream
        // alone would not prove that event boundaries preserve code points.
        size_t offset = 0;
        while (offset < length) {
            char32_t cp;
            int bytes = utf8towc(&cp, event.text.text + offset);
            assert(bytes > 0 && cp != 0xFFFD && cp >= 32 && cp != 127);
            offset += bytes;
        }
        assert(offset == length);
        joined += event.text.text;
    }
    assert(joined == expected);
}
int main() {
    for (int prefix = 0; prefix < 65; ++prefix) {
        string input(prefix, 'a');
        input += "中文\xF0\x9F\x98\x80"; // BMP + supplementary code point
        for (int i = 0; i < 40; ++i) input += "测试";
        input += "tail";
        check(input, input);
        assert(queued.size() > 1);
    }
    check("", "");
    check("\t\r\n", "");
    check(string("a\0b\nc\t", 7), "abc");
    check("123测试中文", "123测试中文");
    focus = nullptr;
    check("中文", "中文");
    text_state = 0;
    queued.clear();
    _queue_android_text_input("must not arrive");
    assert(queued.empty());
}
''')


if __name__ == "__main__":
    unittest.main()
