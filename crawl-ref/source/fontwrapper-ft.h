#pragma once

#ifdef USE_TILE_LOCAL
#ifdef USE_FT

#include <map>
#include <unordered_map>
#include <vector>

#include <ft2build.h>
#include FT_FREETYPE_H

#include "tilefont.h"

using std::vector;

// Upper bounds only: the actual atlas grid is chosen at runtime from the
// glyph cell size, GL_MAX_TEXTURE_SIZE, and a per-font memory budget.
constexpr unsigned int MAX_GLYPHS = 4096;
constexpr unsigned int MAX_GLYPH_COLUMNS = 64;
constexpr size_t FONT_ATLAS_BYTE_BUDGET = 16 * 1024 * 1024;
constexpr unsigned int RESERVED_GLYPHS = 2 + (0x7f - 0x20);

// atlas slot identifier — uint16_t is sufficient for up to 65536 slots
using atlas_slot_t = uint16_t;

struct HiDPIState;
extern HiDPIState display_density;

// TODO enne - Fonts could be made better by:
//
// * handling kerning
// * using SDL_font (maybe?)
// * the possibility of streaming this class in and out so that Crawl doesn't
//   have to link against FreeType2 or be forced do as much processing at
//   load time.

class FTFontWrapper : public FontWrapper
{
public:
    FTFontWrapper();
    virtual ~FTFontWrapper();

    // font loading
    virtual bool load_font(const char *font_name, unsigned int font_size) override;
    virtual bool configure_font() override;
    virtual bool resize(unsigned int size) override;
    virtual uint64_t atlas_generation() const override
    {
        return m_atlas_generation;
    }
    virtual void begin_font_buffer() override { clear_pins(); }

    // render just text
    virtual void render_textblock(unsigned int x, unsigned int y,
                                  char32_t *chars, uint8_t *colours,
                                  unsigned int width, unsigned int height,
                                  bool drop_shadow = false) override;

    // render text + background box
    virtual void render_tooltip(unsigned int x, unsigned int y,
                               const formatted_string &text,
                               const coord_def &min_pos,
                               const coord_def &max_pos) override;

    virtual void render_string(unsigned int x, unsigned int y,
                               const formatted_string &text) override;

    virtual void render_hover_string(unsigned int x, unsigned int y,
                               const formatted_string &text) override;

    // FontBuffer helper functions
    virtual void store(FontBuffer &buf, float &x, float &y,
                       const string &s, const VColour &c) override;
    virtual void store(FontBuffer &buf, float &x, float &y,
                       const string &s,
                       const VColour &fg, const VColour &bg) override;
    virtual void store(FontBuffer &buf, float &x, float &y,
                       const formatted_string &fs) override;
    virtual void store(FontBuffer &buf, float &x, float &y, char32_t c,
                       const VColour &col) override;
    virtual void store(FontBuffer &buf, float &x, float &y, char32_t c,
                       const VColour &fg_col, const VColour &bg_col) override;

    virtual unsigned int char_width(bool logical=true) const override;
    virtual unsigned int char_height(bool logical=true) const override;
    virtual unsigned int max_width(int length, bool logical=true) const override;
    virtual unsigned int max_height(int length, bool logical=true) const override;

    virtual unsigned int string_width(const char *text, bool logical=true) override;
    virtual unsigned int string_width(const formatted_string &str, bool logical=true) override;
    virtual unsigned int string_height(const char *text, bool logical=true) const override;
    virtual unsigned int string_height(const formatted_string &str, bool logical=true) const override;
    virtual bool is_cjk_primary() const override;

    // Try to split this string to fit in w x h pixel area.
    virtual formatted_string split(const formatted_string &str,
                                   unsigned int max_width,
                                   unsigned int max_height) override;

    virtual const GenericTexture *font_tex() const override;

protected:
    // Not overrides! These two have an additional orig_x parameter compared
    // to the virtuals.
    void store(FontBuffer &buf, float &x, float &y,
               const string &s, const VColour &c, float orig_x);
    void store(FontBuffer &buf, float &x, float &y,
               const string &s, const VColour &fg, const VColour &bg,
               float orig_x);
    void store(FontBuffer &buf, float &x, float &y, const formatted_string &fs,
               float orig_x);

    int find_index_before_width(const char *str, int max_width);

    unsigned int map_unicode(char *ch);
    unsigned int map_unicode(char32_t uchar, bool update);
    unsigned int map_unicode(char32_t uchar);
    void load_glyph(unsigned int c, char32_t uchar);
    void draw_m_buf(unsigned int x_pos, unsigned int y_pos, bool drop_shadow);

    struct GlyphInfo
    {
        // offset before drawing glyph; can be negative
        int8_t offset;
        // per-glyph horizontal advance
        int8_t advance;
        // per-glyph width
        int8_t width;
        // per-glyph ascender
        int8_t ascender;

        // does glyph have any pixels?
        bool renderable;
        bool valid;
    };
    vector<GlyphInfo> m_glyphs;
    GlyphInfo& get_glyph_info(char32_t ch);

    struct FontAtlasEntry
    {
        char32_t uchar = 0;
        uint64_t last_used = 0;
        bool reserved = false;
    };
    FontAtlasEntry *m_atlas;
    // O(1) lookup: Unicode codepoint -> atlas slot
    std::unordered_map<char32_t, atlas_slot_t> m_glyph_to_slot;

    // count of glyph loads in the current text block
    int n_subst;

    // pin bitmap: prevents eviction of atlas slots used within a single
    // render batch (render_string / render_tooltip / render_hover_string).
    // Protects against font atlas LRU eviction corrupting glyphs that have
    // already been recorded in FontBuffer vertex data.
    vector<uint8_t> m_pinned;

    // clear all pin marks — call at the start of each widget render batch
    void clear_pins();

    // cached value of the maximum advance from m_advance
    coord_def m_max_advance;

    // minimum offset (likely negative)
    int m_min_offset;

    // size of ascender according to font
    int m_ascender;

    // other font metrics
    coord_def charsz;
    unsigned int m_ft_width;
    unsigned int m_ft_height;
    unsigned int m_atlas_columns;
    unsigned int m_atlas_rows;
    unsigned int m_atlas_capacity;
    int m_max_width;
    int m_max_height;

    GenericTexture m_tex;
    GLShapeBuffer *m_buf;

    FT_Byte *ttf;
    FT_Face face;
    FT_Face cjk_face;          // fallback CJK font face
    FT_Byte *cjk_ttf;          // CJK font data (must survive until cjk_face is freed)
    unsigned char *pixels;
    unsigned int fsize;

    // monotonic clock for last_used tracking in eviction scan
    uint64_t m_atlas_clock;
    // Incremented whenever existing texture coordinates may become stale.
    uint64_t m_atlas_generation;
    // peak number of distinct glyphs concurrently resident (0 = not tracking)
    unsigned int m_peak_glyphs;
};

#endif // USE_FT
#endif // USE_TILE_LOCAL
