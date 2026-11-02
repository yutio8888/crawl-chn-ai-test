#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#ifdef USE_TILE_WEB

#include "tileweb-text.h"
#include "syscalls.h"
#include <clocale>

namespace
{
class TestWebTextArea : public WebTextArea
{
public:
    TestWebTextArea(int columns, int rows = 1) :
        WebTextArea("test"), saved_locale(setlocale(LC_CTYPE, nullptr))
    {
        REQUIRE(ensure_utf8_ctype());
        resize(columns, rows);
    }
    ~TestWebTextArea() override
    {
        setlocale(LC_CTYPE, saved_locale.c_str());
    }
    string saved_locale;
    using WebTextArea::render_line;

    char32_t cell(int x, int y = 0) const { return m_cbuf[x + y * mx]; }
    string line(int y = 0)
    {
        bool dirty;
        return render_line(y, dirty);
    }
};
}

TEST_CASE("WebTiles text uses terminal cells for mixed-width strings", "[webtext]")
{
    TestWebTextArea area(24);
    int x = 0, y = 0;
    area.put_string(U"a + A中  0.0", 7, 0, x, y);
    CHECK(x == 12);
    CHECK(y == 0);
    CHECK(area.cell(5) == U'中');
    CHECK(area.cell(6) == 0);
    CHECK(area.cell(9) == U'0');
    CHECK(area.line() == "<span class=\"fg7 bg0\">a + A"
          "<span class=\"webtiles-wide\">中</span>  0.0</span>");
}

TEST_CASE("WebTiles wide glyphs wrap intact and CR advances input", "[webtext]")
{
    TestWebTextArea area(4, 3);
    int x = 0, y = 0;
    area.put_string(U"abc中\rX\n文", 7, 0, x, y);
    CHECK(area.cell(3) == U' ');
    CHECK(area.cell(0, 1) == U'中');
    CHECK(area.cell(1, 1) == 0);
    CHECK(area.cell(2, 1) == U'X');
    CHECK(area.cell(0, 2) == U'文');
    CHECK(x == 2);
    CHECK(y == 2);
    TestWebTextArea narrow(1);
    x = y = 0;
    narrow.put_string(U"中a", 7, 0, x, y);
    CHECK(x == 1);
    CHECK(y == 0);
    CHECK(narrow.cell(0) == U'a');
}

TEST_CASE("WebTiles overwriting either wide half clears the whole glyph", "[webtext]")
{
    TestWebTextArea area(6);
    int x = 0, y = 0;
    area.put_string(U"中文", 7, 0, x, y);
    SECTION("overwrite first half")
    {
        area.put_character(U'A', 7, 0, 0, 0);
        CHECK(area.cell(0) == U'A');
        CHECK(area.cell(1) == U' ');
    }
    SECTION("overwrite continuation")
    {
        area.put_character(U'A', 7, 0, 1, 0);
        CHECK(area.cell(0) == U' ');
        CHECK(area.cell(1) == U'A');
    }
    SECTION("wide write overlaps two old glyphs")
    {
        area.put_character(U'字', 7, 0, 1, 0);
        CHECK(area.cell(0) == U' ');
        CHECK(area.cell(1) == U'字');
        CHECK(area.cell(2) == 0);
        CHECK(area.cell(3) == U' ');
    }
    SECTION("clear from continuation to end of line")
    {
        for (int column = 1; column < area.mx; ++column)
            area.put_character(' ', 7, 0, column, 0);
        CHECK(area.line().find("webtiles-wide") == string::npos);
        CHECK(area.cell(0) == U' ');
    }
}

TEST_CASE("WebTiles rows retain combining marks and track complete snapshots", "[webtext]")
{
    TestWebTextArea area(4);
    int x = 0, y = 0;
    area.put_string(U"e\u0301中\u0301", 7, 0, x, y);
    CHECK(x == 3);
    bool dirty;
    const string html = area.render_line(0, dirty);
    CHECK(dirty);
    CHECK(html == "<span class=\"fg7 bg0\">é"
          "<span class=\"webtiles-wide\">中́</span></span>");
    CHECK(area.render_line(0, dirty) == html);
    CHECK_FALSE(dirty);
    area.put_string(U"\u0300", 7, 0, x, y);
    CHECK(area.render_line(0, dirty).find("中́̀") != string::npos);
    CHECK(dirty);
    area.put_character(U'A', 7, 0, 2, 0);
    CHECK(area.line().find("́") != string::npos); // accent on e survives
    CHECK(area.line().find("中") == string::npos);
    area.clear();
    CHECK(area.render_line(0, dirty).empty());
    CHECK(dirty);
    area.render_line(0, dirty);
    CHECK_FALSE(dirty);
    area.resize(8, 1);
    CHECK(area.line().empty());
}

TEST_CASE("WebTiles row HTML escapes text and preserves background cells", "[webtext]")
{
    TestWebTextArea area(16);
    int x = 0, y = 0;
    area.put_string(U"<>&\"\\", 7, 0, x, y);
    CHECK(area.line() == "<span class=\"fg7 bg0\">&lt;&gt;&amp;&quot;\\</span>");
    area.clear();
    area.put_character(' ', 7, 1, 0, 0);
    area.put_character('A', 7, 0, 2, 0);
    CHECK(area.line() == "<span class=\"fg7 bg1\"> </span> "
          "<span class=\"fg7 bg0\">A</span>");
    area.clear();
    area.put_character(U'中', 7, 1, 0, 0);
    area.put_character('A', 7, 0, 3, 0);
    CHECK(area.line() == "<span class=\"fg7 bg1\">"
          "<span class=\"webtiles-wide\">中</span></span> "
          "<span class=\"fg7 bg0\">A</span>");
}

#endif
