#!/usr/bin/env python3
"""Exercise formatted-scroller widget construction with font/UI doubles.

The production construction path and Text size request run unchanged. The
fixture ends before input dispatch and uses deterministic font measurements;
SDL rendering, scrolling gestures and actual font shaping need device evidence.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_android_quickbar as regression

ROOT = Path(__file__).resolve().parents[3]


class AndroidScrollerFontTests(unittest.TestCase):
    def test_reflowable_scrollers_use_reading_font_only_on_small_android(self):
        source = (ROOT / "crawl-ref/source/scroller.cc").read_text()
        show = regression.block_after(source, "int formatted_scroller::show()")
        setup = show[1:show.index("    auto popup =")]
        ui = (ROOT / "crawl-ref/source/ui.cc").read_text()
        text_size = regression.block_after(ui, "SizeReq Text::_get_preferred_size")
        fixture = r'''
#define USE_TILE_LOCAL
#include <algorithm>
#include <cassert>
#include <climits>
#include <memory>
#include <string>
#include <vector>
using namespace std;
struct formatted_string {
    string value;
    formatted_string(string text = "") : value(text) {}
    bool empty() { return value.empty(); }
    string to_colour_string(int) { return value; }
    static formatted_string parse_string(string value) { return value; }
};
struct Font {
    int pixels;
    int char_width() { return pixels; }
    int char_height() { return pixels; }
    int string_width(const formatted_string& text) {
        return text.value.size() * pixels;
    }
    int string_height(const formatted_string& text) {
        return (1 + count(text.value.begin(), text.value.end(), '\n')) * pixels;
    }
};
struct {
    Font crt{8}, message{14};
    bool small = true;
    Font* get_crt_font() { return &crt; }
    Font* get_msg_font() { return &message; }
    bool is_using_small_layout() { return small; }
} tiles;
struct SizeReq { int min, nat; };
struct Widget {
    enum Direction { HORZ, VERT };
    enum class Align { CENTER, STRETCH };
    virtual ~Widget() = default;
};
struct Text : Widget {
    Font* m_font = tiles.get_crt_font();
    formatted_string m_text, m_text_wrapped;
    bool wrap_text = false, ellipsize = false;
    void set_font(Font* font) { m_font = font; }
    void set_wrap_text(bool wrap) { wrap_text = wrap; }
    void set_text(formatted_string text) { m_text = text; }
    void set_highlight_pattern(string, bool) {}
    void set_margin_for_crt(int, int, int, int) {}
    void set_margin_for_sdl(int, int, int, int) {}
    void wrap_text_to_size(int width, int) {
        m_text_wrapped = m_text;
        if (wrap_text) {
            const int chars = max(1, width / m_font->pixels);
            for (int pos = chars; pos < (int)m_text_wrapped.value.size(); pos += chars + 1)
                m_text_wrapped.value.insert(pos, "\n");
        }
    }
    SizeReq _get_preferred_size(Direction dim, int prosp_width)
''' + text_size + r'''
};
struct Box : Widget {
    struct { int width = INT_MAX; } maximum;
    vector<shared_ptr<Widget>> children;
    explicit Box(Direction) {}
    void set_cross_alignment(Align) {}
    void set_main_alignment(Align) {}
    void add_child(shared_ptr<Widget> child) { children.push_back(child); }
    decltype(maximum)& max_size() { return maximum; }
};
struct formatted_scroller;
struct UIHookedScroller : Widget {
    shared_ptr<Text> child;
    explicit UIHookedScroller(formatted_scroller&) {}
    void set_child(shared_ptr<Text> text) { child = text; }
};
enum { FS_PREWRAPPED_TEXT = 2, LIGHTGRAY = 7 };
struct formatted_scroller {
    int m_flags = 0;
    formatted_string m_title{string(90, 'T')};
    formatted_string contents{string(90, 'B')};
    formatted_string m_more{string(90, 'F')};
    shared_ptr<Text> m_title_text;
    shared_ptr<UIHookedScroller> m_scroller;
    string highlight;
    void construct_and_check(bool reading) {
''' + setup + r'''
        assert(vbox->children.size() == 3);
        auto title_box = dynamic_pointer_cast<Box>(vbox->children[0]);
        auto title = dynamic_pointer_cast<Text>(title_box->children[0]);
        auto body = m_scroller->child;
        auto footer = dynamic_pointer_cast<Text>(vbox->children[2]);
        assert(title && body && footer);
        for (const auto& part : {title, body, footer}) {
            assert(part->m_font == (reading ? tiles.get_msg_font() : tiles.get_crt_font()));
            // Larger fonts must not impose the entire line as a minimum width.
            if (reading) {
                assert(part->_get_preferred_size(Widget::HORZ, -1).min == 0);
                for (int width : {180, 360, 540})
                    assert(part->_get_preferred_size(Widget::VERT, width).nat
                           > part->m_font->char_height());
            }
        }
        assert(title->wrap_text == reading && footer->wrap_text == reading);
        assert(body->wrap_text == !(m_flags & FS_PREWRAPPED_TEXT));
        assert(title->m_text.value == m_title.value);
        assert(body->m_text.value == contents.value);
        assert(footer->m_text.value == m_more.value);
    }
};
int main() {
    for (bool small : {false, true})
        for (int flags : {0, int(FS_PREWRAPPED_TEXT)})
            for (int pixels : {14, 21, 28}) {
                tiles.small = small;
                tiles.message.pixels = pixels;
                formatted_scroller scroller;
                scroller.m_flags = flags;
#ifdef __ANDROID__
                scroller.construct_and_check(small && !(flags & FS_PREWRAPPED_TEXT));
#else
                scroller.construct_and_check(false);
#endif
            }
}
'''
        for android in (True, False):
            with self.subTest(android=android):
                regression.TargetingSafetyTests.run_cpp(
                    self, ("#define __ANDROID__\n" if android else "") + fixture)


if __name__ == "__main__":
    unittest.main()
