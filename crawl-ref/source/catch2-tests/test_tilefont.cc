#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#ifdef USE_TILE_LOCAL

#include <type_traits>

#include "tilefont-internal.h"
#include "tilefont.h"

namespace
{

using render_string_signature =
    void (FontWrapper::*)(int, int, const formatted_string &);
using render_tooltip_signature =
    void (FontWrapper::*)(int, int, const formatted_string &,
                          const coord_def &, const coord_def &);

static_assert(std::is_same<decltype(&FontWrapper::render_string),
                           render_string_signature>::value,
              "free-form font coordinates must remain signed");
static_assert(std::is_same<decltype(&FontWrapper::render_hover_string),
                           render_string_signature>::value,
              "hover font coordinates must remain signed");
static_assert(std::is_same<decltype(&FontWrapper::render_tooltip),
                           render_tooltip_signature>::value,
              "tooltip font coordinates must remain signed");

int break_after_two_glyphs(const char *line)
{
    int glyphs = 0;
    for (char *current = const_cast<char *>(line); *current;
         current = next_glyph(current))
    {
        if (*current == '\n')
            return INT_MAX;
        if (glyphs++ == 2)
            return current - line;
    }
    return INT_MAX;
}

} // namespace

TEST_CASE("tooltip placement keeps oversized text visible", "[tilefont]")
{
    const coord_def min_pos(5, 5);
    const coord_def max_pos(1275, 795);

    const tilefont_internal::tooltip_position fitted =
        tilefont_internal::place_tooltip(804, 253, 1256, 56, 7,
                                         min_pos, max_pos);
    REQUIRE(fitted.x == 12);
    REQUIRE(fitted.y == 273);
    REQUIRE(fitted.x - 7 >= min_pos.x);
    REQUIRE(fitted.x + 1256 + 7 <= max_pos.x);
    REQUIRE(fitted.y - 7 >= min_pos.y);
    REQUIRE(fitted.y + 56 + 7 <= max_pos.y);

    // This is the width from the original Searing Ray failure. Even before
    // wrapping, its position must not become negative and then wrap unsigned.
    const tilefont_internal::tooltip_position oversized =
        tilefont_internal::place_tooltip(804, 253, 1287, 42, 7,
                                         min_pos, max_pos);
    REQUIRE(oversized.x == 12);
    REQUIRE(oversized.y == 273);
}

TEST_CASE("tooltip CJK line breaks preserve UTF-8 and formatting", "[tilefont]")
{
    formatted_string text =
        formatted_string::parse_string("<red>中文</red><white>测试</white>");
    const formatted_string wrapped =
        tilefont_internal::split_formatted_string(text, 3,
                                                   break_after_two_glyphs);

    REQUIRE(wrapped.tostring() == "中文\n测试");
    REQUIRE(wrapped.ops.size() == text.ops.size());
    for (size_t i = 0; i < text.ops.size(); ++i)
    {
        REQUIRE(wrapped.ops[i].type == text.ops[i].type);
        if (text.ops[i].type != FSOP_TEXT)
            REQUIRE(wrapped.ops[i].colour == text.ops[i].colour);
    }

    REQUIRE(tilefont_internal::insert_text(text, 3, "\n"));
    REQUIRE(text.tostring() == "中\n文测试");
    REQUIRE_FALSE(tilefont_internal::insert_text(text, 100, "\n"));
}

#endif // USE_TILE_LOCAL
