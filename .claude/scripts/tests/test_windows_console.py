#!/usr/bin/env python3
"""Exercise the Windows cell writer with Win32 I/O doubles on any host.

The buffer writer, dirty-region handling and Windows wcwidth implementation
come from production source. These tests do not validate terminal/font rendering;
Windows compilation and visual acceptance are separate checks.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]


class WindowsConsoleTests(unittest.TestCase):
    def test_wide_cells_cursor_overwrites_and_clipping(self):
        compiler = shutil.which("c++")
        self.assertIsNotNone(compiler, "C++ compiler required for console regression")
        source = (ROOT / "crawl-ref/source/libw32c.cc").read_text()
        writer = source[source.index("static void _update_dirty_area("):
                        source.index("void set_mouse_enabled(")]
        flush = source[source.index("void update_screen()"):
                       source.index("int get_number_of_lines()")]
        widths = (ROOT / "crawl-ref/source/wcwidth.cc").read_text()
        widths = widths.replace('#include "AppHdr.h"', "").replace(
            '#include "unicode.h"', "")
        fixture = r'''
#include <cassert>
#include <cstdint>
#include <string>
#include <algorithm>
using namespace std;
#define ARRAYSZ(a) (sizeof(a) / sizeof((a)[0]))
#define SCREENINDEX(x,y) ((x)+screensize.X*(y))
#define WIN32COLOR(col) (WORD)(col)
using WORD = uint16_t;
struct COORD { short X, Y; };
struct SMALL_RECT { short Left, Top, Right, Bottom; };
struct CHAR_INFO { struct { char16_t UnicodeChar; } Char; WORD Attributes; };
using PCHAR_INFO = CHAR_INFO*;
constexpr WORD COMMON_LVB_LEADING_BYTE = 0x100;
constexpr WORD COMMON_LVB_TRAILING_BYTE = 0x200;
CHAR_INFO storage[32];
CHAR_INFO *screen = storage;
COORD screensize = {8, 3}, dirty_area_start = {}, dirty_area_end = {};
COORD last_cursor = {};
SMALL_RECT last_flush = {};
void *outbuf = nullptr;
bool cursor_is_enabled = true;
int cx = 0, cy = 0, current_colour = 7, flushes = 0;
void SetConsoleCursorPosition(void*, COORD pos) { last_cursor = pos; }
void WriteConsoleOutputW(void*, CHAR_INFO*, COORD, COORD, SMALL_RECT *rect) {
    last_flush = *rect;
    ++flushes;
}
void gotoxy_sys(int x, int y) {
    cx = max(0, min(x - 1, int(screensize.X) - 1));
    cy = max(0, min(y - 1, int(screensize.Y) - 1));
}
''' + widths + writer + flush + r'''
void reset() {
    fill(begin(storage), end(storage), CHAR_INFO{{u' '}, 7});
    cx = cy = flushes = 0;
    current_colour = 7;
    _clear_dirty_area();
}
void pair_at(int x, char32_t glyph, WORD colour=7) {
    assert(screen[x].Char.UnicodeChar == glyph);
    assert(screen[x+1].Char.UnicodeChar == glyph);
    assert(screen[x].Attributes == (colour | COMMON_LVB_LEADING_BYTE));
    assert(screen[x+1].Attributes == (colour | COMMON_LVB_TRAILING_BYTE));
}
void blank_at(int x) {
    assert(screen[x].Char.UnicodeChar == ' ');
    assert(!(screen[x].Attributes & 0x300));
}
int main() {
    reset();
    for (char32_t c : U"A中文：B") if (c) writeChar(c);
    assert(cx == 8 && cy == 0);
    pair_at(1, U'中'); pair_at(3, U'文'); pair_at(5, U'：');
    assert(screen[0].Char.UnicodeChar == 'A');
    assert(screen[7].Char.UnicodeChar == 'B');
    update_screen();
    assert(flushes == 1 && last_flush.Left == 0 && last_flush.Right == 7);
    assert(last_cursor.X == 7 && last_cursor.Y == 0);
    // Redrawing unchanged cells is a no-op; recolouring updates both halves.
    gotoxy_sys(2, 1); writeChar(U'中'); update_screen();
    assert(flushes == 1 && cx == 3);
    current_colour = 12;
    gotoxy_sys(2, 1); writeChar(U'中'); update_screen();
    pair_at(1, U'中', 12);
    assert(flushes == 2 && last_flush.Left == 1 && last_flush.Right == 2);
    // Overwrite either half and flush the erased neighbour as well.
    gotoxy_sys(2, 1); writeChar('x'); update_screen();
    blank_at(2);
    assert(last_flush.Left == 1 && last_flush.Right == 2);
    gotoxy_sys(5, 1); writeChar('y'); update_screen();
    blank_at(3);
    assert(last_flush.Left == 3 && last_flush.Right == 4);
    reset();
    writeChar(U'中'); writeChar(U'文'); update_screen();
    gotoxy_sys(2, 1); writeChar(U'国'); update_screen();
    pair_at(1, U'国'); blank_at(0); blank_at(3);
    assert(last_flush.Left == 0 && last_flush.Right == 3);
    // A full row clips later characters instead of destroying a trailing half.
    reset(); gotoxy_sys(7, 1); writeChar(U'中'); writeChar('x');
    pair_at(6, U'中');
    assert(cx == 8 && storage[8].Char.UnicodeChar == ' ');
    _sync_cursor(); assert(last_cursor.X == 7);
    reset(); gotoxy_sys(8, 1); writeChar(U'中');
    blank_at(7); assert(cx == 8);
    // Tabs, CR/LF, and zero-width codepoints retain cell-based positioning.
    reset(); writeChar('\t'); assert(cx == 8);
    writeChar('\r'); assert(cx == 8);
    writeChar('\n'); assert(cx == 0 && cy == 1);
    writeChar('A'); writeChar(U'\u0301'); writeChar(0);
    assert(cx == 1 && cy == 1);
    writeChar(U'中'); assert(cx == 3);
    pair_at(9, U'中');
    reset(); writeChar(U'\U0001f600');
    assert(cx == 1 && screen[0].Char.UnicodeChar == 0xbf);
    // All writes remain inside the screen, including a one-column terminal.
    reset(); screensize.X = 1; writeChar(U'中'); writeChar('x');
    blank_at(0); blank_at(1); assert(cx == 1);
}
'''
        with tempfile.TemporaryDirectory(prefix="windows-console-") as tmp:
            directory = Path(tmp)
            (directory / "test.cc").write_text(fixture)
            build = subprocess.run(
                [compiler, "-std=c++11", "-Wall", "-Wextra", "-Werror",
                 "-Wno-parentheses", str(directory / "test.cc"),
                 "-o", str(directory / "test")],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            result = subprocess.run(
                [str(directory / "test")], capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
