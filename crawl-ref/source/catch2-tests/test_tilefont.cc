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

TEST_CASE("missing fullwidth punctuation uses a compatibility glyph after exact lookup",
          "[tilefont][playtest-004]")
{
    vector<char32_t> queried;
    auto lookup = [&](char32_t ch)
    {
        queried.push_back(ch);
        return ch == '/' ? 42u : 0u;
    };
    const char32_t slash = 0xff0f;
    CHECK(tilefont_internal::lookup_glyph(slash, lookup) == 42);
    REQUIRE(queried.size() == 2);
    CHECK(queried[0] == slash);
    CHECK(queried[1] == '/');
    CHECK(slash == 0xff0f);

    queried.clear();
    auto exact = [&](char32_t ch)
    {
        queried.push_back(ch);
        return 17u;
    };
    CHECK(tilefont_internal::lookup_glyph(slash, exact) == 17);
    REQUIRE(queried.size() == 1);
    CHECK(queried[0] == slash);

    queried.clear();
    CHECK(tilefont_internal::lookup_glyph(U'中', lookup) == 0);
    REQUIRE(queried.size() == 1);
    CHECK(queried[0] == U'中');
    queried.clear();
    CHECK(tilefont_internal::lookup_glyph('/', lookup) == 42);
    CHECK(queried.size() == 1);
}

TEST_CASE("single-channel alpha font atlas yields 4x capacity or 75% VRAM savings",
          "[tilefont]")
{
    const size_t budget = 16 * 1024 * 1024;
    const unsigned int max_cols = 64;
    unsigned int cols = 0, rows = 0;

    // 4K / HiDPI 64x64 glyph cell: RGBA is capped at 32x32 (1024 slots),
    // while 1-byte GL_ALPHA reaches the full 64x64 (4096 slots) in 16 MiB.
    tilefont_internal::choose_atlas_grid(64, 64, 4096, 4, max_cols, budget,
                                         cols, rows);
    CHECK(cols * rows == 1024);

    tilefont_internal::choose_atlas_grid(64, 64, 4096, 1, max_cols, budget,
                                         cols, rows);
    CHECK(cols == 64);
    CHECK(rows == 64);
    CHECK(cols * rows == 4096);

    // Oversized 128x128 cell: RGBA fits only 256 slots; ALPHA fits 1024 slots.
    tilefont_internal::choose_atlas_grid(128, 128, 8192, 4, max_cols, budget,
                                         cols, rows);
    CHECK(cols * rows == 256);

    tilefont_internal::choose_atlas_grid(128, 128, 8192, 1, max_cols, budget,
                                         cols, rows);
    CHECK(cols * rows == 1024);

    // Standard 32x32 cell: both hit 4096 slots, ALPHA uses 4 MiB vs 16 MiB.
    tilefont_internal::choose_atlas_grid(32, 32, 4096, 1, max_cols, budget,
                                         cols, rows);
    CHECK(cols == 64);
    CHECK(rows == 64);
    CHECK(size_t(cols * 32) * (rows * 32) * 1 == 4 * 1024 * 1024);

    // Zero / degenerate inputs fail safely.
    tilefont_internal::choose_atlas_grid(0, 32, 4096, 1, max_cols, budget,
                                         cols, rows);
    CHECK(cols == 0);
    CHECK(rows == 0);
}

TEST_CASE("FontAtlasCache allocates free slots O(1) and evicts in strict LRU order",
          "[tilefont]")
{
    constexpr char32_t kMissing = 0xFFFD;
    tilefont_internal::FontAtlasCache cache;
    cache.reset(6); // slots 0..5
    REQUIRE(cache.generation() == 1);

    // Reserve slot 0 (colour bar), slot 1 (MISSING_CHAR), slot 2 ('A').
    cache.reserve_slot(0, 0);
    cache.reserve_slot(1, kMissing);
    cache.reserve_slot(2, 'A');
    cache.clear_pins();

    // Reserved lookup hits without loading or bumping generation.
    auto rA = cache.acquire('A', kMissing);
    CHECK(rA.slot == 2);
    CHECK_FALSE(rA.needs_load);
    CHECK_FALSE(rA.evicted);
    CHECK(cache.generation() == 1);

    // Fill the 3 dynamic slots (3, 4, 5) via O(1) free-slot pointer.
    auto r1 = cache.acquire(U'甲', kMissing);
    auto r2 = cache.acquire(U'乙', kMissing);
    auto r3 = cache.acquire(U'丙', kMissing);
    CHECK(r1.slot == 3);
    CHECK(r2.slot == 4);
    CHECK(r3.slot == 5);
    CHECK(r1.needs_load);
    CHECK(r2.needs_load);
    CHECK(r3.needs_load);
    CHECK_FALSE(r1.evicted);
    CHECK_FALSE(r2.evicted);
    CHECK_FALSE(r3.evicted);
    CHECK(cache.peak_glyphs() == 3);
    CHECK(cache.generation() == 1);

    // All 3 dynamic slots are currently pinned in this batch -> overflow returns MISSING_CHAR.
    auto r_overflow = cache.acquire(U'丁', kMissing);
    CHECK(r_overflow.slot == 1);
    CHECK(r_overflow.overflow_missing);
    CHECK_FALSE(r_overflow.needs_load);
    CHECK_FALSE(r_overflow.evicted);
    CHECK(cache.generation() == 1);

    // Start new batch: touch 甲 so LRU order becomes 乙 (oldest) -> 丙 -> 甲 (newest).
    cache.clear_pins();
    auto r1_hit = cache.acquire(U'甲', kMissing);
    CHECK(r1_hit.slot == 3);
    CHECK_FALSE(r1_hit.needs_load);

    // Acquiring 丁 must evict 乙 (slot 4) and bump generation.
    auto r4 = cache.acquire(U'丁', kMissing);
    CHECK(r4.slot == 4);
    CHECK(r4.needs_load);
    CHECK(r4.evicted);
    CHECK(cache.generation() == 2);
    CHECK(cache.peak_glyphs() == 3);

    // Now 丙 (slot 5) is oldest and unpinned; 甲 (slot 3) & 丁 (slot 4) are pinned.
    // Acquiring 戊 must evict 丙 (slot 5).
    auto r5 = cache.acquire(U'戊', kMissing);
    CHECK(r5.slot == 5);
    CHECK(r5.needs_load);
    CHECK(r5.evicted);
    CHECK(cache.generation() == 3);

    // Reserved ASCII 'A' is still intact and never evicted.
    auto rA2 = cache.acquire('A', kMissing);
    CHECK(rA2.slot == 2);
    CHECK_FALSE(rA2.needs_load);

    // Next batch: touch 甲 -> LRU order becomes 丁(4) -> 戊(5) -> 甲(3); 丁 is oldest & unpinned.
    cache.clear_pins();
    CHECK(cache.acquire(U'甲', kMissing).slot == 3);
    auto r6 = cache.acquire(U'己', kMissing);
    CHECK(r6.slot == 4);
    CHECK(r6.evicted);
    CHECK(cache.generation() == 4);

    // Non-contiguous reserved slots must not waste skipped dynamic slots.
    cache.reset(4);
    cache.reserve_slot(0, 0);
    cache.reserve_slot(2, kMissing);
    cache.clear_pins();
    CHECK(cache.acquire(U'一', kMissing).slot == 1);
    CHECK(cache.acquire(U'二', kMissing).slot == 3);
    CHECK(cache.peak_glyphs() == 2);
}

#endif // USE_TILE_LOCAL
