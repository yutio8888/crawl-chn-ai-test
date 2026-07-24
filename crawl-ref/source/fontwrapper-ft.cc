#include "AppHdr.h"

#ifdef USE_TILE_LOCAL
#ifdef USE_FT

#include "fontwrapper-ft.h"

#include <ft2build.h>
#include FT_FREETYPE_H

#include "defines.h"
#include "end.h"
#include "errno.h"
#include "files.h"
#include "format.h"
#include "glwrapper.h"
#include "options.h"
#include "syscalls.h"
#include "tilebuf.h"
#include "tilefont.h"
#include "tilefont-internal.h"
#include "tilesdl.h"
#include "unicode.h"
#include "unwind.h"

// char to use if we can't find it in the font (upside-down question mark)
#define MISSING_CHAR 0xbf
// CJK fallback font — loaded alongside the primary font to provide glyphs
// for Chinese/Japanese/Korean characters that DejaVu Sans Mono lacks.
static const char* CJK_CANDIDATES[] = {
    "contrib/fonts/SarasaMonoSC-Regular.ttf",
    "contrib/fonts/SarasaFixedSC-Regular.ttf",
    "contrib/fonts/MapleMono-NF-CN-Regular.ttf",
    "dat/tiles/SarasaMonoSC-Regular.ttf",
    "dat/tiles/SarasaFixedSC-Regular.ttf",
    "dat/tiles/MapleMono-NF-CN-Regular.ttf",
};

static void _choose_atlas_grid(unsigned int cell_width,
                               unsigned int cell_height,
                               unsigned int max_texture_size,
                               unsigned int &columns,
                               unsigned int &rows)
{
    columns = 0;
    rows = 0;
    unsigned int best_capacity = 0;
    unsigned int best_long_side = UINT_MAX;
    unsigned int best_side_difference = UINT_MAX;

    for (unsigned int candidate_columns = 1;
         candidate_columns <= MAX_GLYPH_COLUMNS;
         candidate_columns *= 2)
    {
        const unsigned int width = candidate_columns * cell_width;
        if (width > max_texture_size)
            continue;

        for (unsigned int candidate_rows = 1;
             candidate_rows <= MAX_GLYPH_COLUMNS;
             candidate_rows *= 2)
        {
            const unsigned int height = candidate_rows * cell_height;
            if (height > max_texture_size)
                continue;

            const size_t bytes = size_t(width) * height * 4;
            if (bytes > FONT_ATLAS_BYTE_BUDGET)
                continue;

            const unsigned int capacity = candidate_columns * candidate_rows;
            const unsigned int long_side = max(width, height);
            const unsigned int side_difference = width > height
                                               ? width - height
                                               : height - width;
            if (capacity > best_capacity
                || (capacity == best_capacity && long_side < best_long_side)
                || (capacity == best_capacity && long_side == best_long_side
                    && side_difference < best_side_difference))
            {
                columns = candidate_columns;
                rows = candidate_rows;
                best_capacity = capacity;
                best_long_side = long_side;
                best_side_difference = side_difference;
            }
        }
    }
}

#if 0
# define dprintf(...) debuglog(__VA_ARGS__)
#else
# define dprintf(...) (void)0
#endif

class FontLibrary {
public:
    static FT_Library &get() {
        static FontLibrary instance;
        return instance.library;
    }
private:
    FT_Library library;
    FontLibrary ()
    {
        if (FT_Init_FreeType(&library))
            die_noline("Failed to initialise freetype library.\n");
    };
    ~FontLibrary ()
    {
        if (FT_Done_FreeType(library))
            die_noline("Failed to unload freetype library.\n");
    };
};

FontWrapper* FontWrapper::create()
{
    return new FTFontWrapper();
}

FTFontWrapper::FTFontWrapper() :
    m_atlas(nullptr),
    m_max_advance(0, 0),
    m_min_offset(0),
    charsz(1,1),
    m_ft_width(0),
    m_ft_height(0),
    m_atlas_columns(0),
    m_atlas_rows(0),
    m_atlas_capacity(0),
    m_max_width(0),
    m_max_height(0),
    ttf(nullptr),
    face(nullptr),
    cjk_face(nullptr),
    cjk_ttf(nullptr),
    pixels(nullptr),
    fsize(0),
    m_atlas_clock(0),
    m_atlas_generation(0),
    m_peak_glyphs(0)
{
    m_buf = GLShapeBuffer::create(true, true);
}

FTFontWrapper::~FTFontWrapper()
{
    delete[] m_atlas;
    delete[] pixels;
    delete m_buf;
    if (face)
        FT_Done_Face(face);
    if (cjk_face)
        FT_Done_Face(cjk_face);
    delete[] ttf;
    delete[] cjk_ttf;
}

void FTFontWrapper::clear_pins()
{
    for (uint8_t &pin : m_pinned)
        pin = 0;
}

/**
 * Configure the font based on metrics, and initialize caches. This may be
 * called multiple times when cached information needs to be reset, e.g. upon
 * changing DPI.
 */
bool FTFontWrapper::configure_font()
{
    // The texture is recreated below, invalidating every previously packed
    // FontBuffer even if glyphs happen to occupy the same slots afterward.
    ++m_atlas_generation;

    FT_Error error;
    error = FT_Set_Pixel_Sizes(face,
                                display_density.logical_to_device(fsize),
                                display_density.logical_to_device(fsize));
    ASSERT(!error);

    // Get maximum advance and other global metrics
    FT_Size_Metrics metrics = face->size->metrics;
    m_max_advance   = coord_def(0,0);
    // Use Latin half-width advance as grid cell, not max_advance.
    // For CJK fonts, max_advance = full-width (2em), but the cell
    // must be the Latin monospace advance so CJK fills 2 cells.
    int latin_adv = 0;
    for (char c = 0x20; c < 0x7f; ++c)
    {
        if (FT_Load_Char(face, c, FT_LOAD_DEFAULT) == 0)
            latin_adv = max(latin_adv, (int)(face->glyph->advance.x >> 6));
    }
    m_max_advance.x = latin_adv ? latin_adv : (metrics.max_advance >> 6);
    m_max_advance.y = (metrics.ascender-metrics.descender)>>6;
    m_ascender      = (metrics.ascender>>6);
    // if you're looking for realistic glyph sizes use m_max_advance
    // or char_width, these are still scaled.
    // (TODO: why would you ever use these values? m_max_advance is almost
    // certainly correct...)
    m_max_width     = (face->bbox.xMax >> 6) - (face->bbox.xMin >> 6);
    m_max_height    = (face->bbox.yMax >> 6) - (face->bbox.yMin >> 6);
    m_min_offset    = 0;

    if (cjk_face)
    {
        // Load CJK face at the same pixel size as the primary font.
        // store() and string_width() use native glyph.advance for tight
        // CJK spacing; render_textblock() uses grid advance independently.
        int device_w = display_density.logical_to_device(fsize);
        FT_Set_Pixel_Sizes(cjk_face, device_w, device_w);
    }

    charsz = coord_def(1,1);
    // Grow character size to power of 2.
    // CJK glyphs can be up to 2x the base advance, so use 2x width.
    while (charsz.x <= m_max_advance.x * 2)
        charsz.x *= 2;
    while (charsz.y <= m_max_advance.y)
        charsz.y *= 2;

    // Choose a power-of-two rectangular grid bounded by the driver, the
    // per-font RGBA memory budget, and the historical 64x64 upper bound.
    // Having to blow out 8-bit alpha values into full 32-bit textures is
    // kind of frustrating, but not all OpenGL implementations support the
    // "esoteric" ALPHA8 format and it's not like this texture is very large.

    // [frogbotherer] I think we can get memory usage lower by blowing out
    // the texture as a whole out to a power of 2, instead of each individual
    // character. Also, whilst GLES baulks at ALPHA8, there might be some
    // other compression format that we can use to get the size down a bit
    const int driver_max_texture_size = opengl::max_texture_size();
    _choose_atlas_grid(charsz.x, charsz.y,
                       max(driver_max_texture_size, 0),
                       m_atlas_columns, m_atlas_rows);
    m_atlas_capacity = m_atlas_columns * m_atlas_rows;
    if (m_atlas_capacity < RESERVED_GLYPHS)
    {
        die_noline("Font atlas cannot reserve required glyphs: %u slots "
                   "available, %u required (cell %dx%d, max texture %d).\n",
                   m_atlas_capacity, RESERVED_GLYPHS, charsz.x, charsz.y,
                   driver_max_texture_size);
    }

    m_ft_width  = m_atlas_columns * charsz.x;
    m_ft_height = m_atlas_rows * charsz.y;

    delete[] pixels; // for repeated calls

    pixels = new unsigned char[4 * charsz.x * charsz.y];
    memset(pixels, 0, sizeof(unsigned char) * 4 * charsz.x * charsz.y);

    dprintf("new font tex %d x %d x 4 = %dpx %d bytes\n",
            m_ft_width, m_ft_height, m_ft_width * m_ft_height,
            4 * m_ft_width * m_ft_height);

    // initialise empty texture of correct size
    unwind_bool noscaling(Options.tile_filter_scaling, false);
    if (!m_tex.load_texture(nullptr, m_ft_width, m_ft_height, MIPMAP_NONE))
    {
        die_noline("Failed to allocate font atlas texture (%u x %u).\n",
                   m_ft_width, m_ft_height);
    }

    m_glyphs.clear();
    m_glyph_to_slot.clear();
    m_atlas_clock = 0;

    delete[] m_atlas;
    m_atlas = new FontAtlasEntry[m_atlas_capacity];
    m_pinned.assign(m_atlas_capacity, 0);

    for (unsigned int i = 0; i < m_atlas_capacity; i++)
        m_atlas[i] = FontAtlasEntry();

    // Slot 0: full-white block (reserved, never evicted)
    // used by colour_bar
    m_atlas[0].reserved = true;
    m_atlas[0].last_used = ++m_atlas_clock;
    {
        for (int x = 0; x < m_max_advance.x; x++)
            for (int y = 0; y < m_max_advance.y; y++)
            {
                unsigned int idx = x + y * m_max_advance.x;
                idx *= 4;
                pixels[idx]     = 255;
                pixels[idx + 1] = 255;
                pixels[idx + 2] = 255;
                pixels[idx + 3] = 255;
            }

        bool success = m_tex.load_texture(pixels, charsz.x, charsz.y,
                                          MIPMAP_NONE, 0, 0);
        ASSERT(success);
    }

    // Slot 1: MISSING_CHAR (reserved, never evicted)
    {
        atlas_slot_t slot = 1;
        m_atlas[slot].uchar = MISSING_CHAR;
        m_atlas[slot].reserved = true;
        m_atlas[slot].last_used = ++m_atlas_clock;
        m_glyph_to_slot[MISSING_CHAR] = slot;
        load_glyph(slot, MISSING_CHAR);
    }

    // Preload and reserve ASCII printable characters (0x20-0x7E).
    // These are consumed by almost every UI element and must never be
    // evicted, preventing loss of menu/chrome glyphs under atlas pressure.
    atlas_slot_t next_slot = 2;
    for (char c = 0x20; c < 0x7f; c++)
    {
        atlas_slot_t slot = next_slot++;
        m_atlas[slot].uchar = c;
        m_atlas[slot].reserved = true;
        m_atlas[slot].last_used = ++m_atlas_clock;
        m_glyph_to_slot[(char32_t)c] = slot;
        load_glyph(slot, c);
    }

    clear_pins();
    m_peak_glyphs = 0;
    return true;
}

bool FTFontWrapper::load_font(const char *font_name, unsigned int font_size)
{
    FT_Error error;
    FT_Library library = FontLibrary::get();

    fsize = font_size;

    // TODO enne - need to find a cross-platform way to also
    // attempt to locate system fonts by name...
    // 1KB: fontconfig if we are not scared of hefty libraries

    // TODO: probably don't want to end here, but try a fallback font in
    // the calling function.
    string font_path = datafile_path(font_name, false, true);
    if (font_path.c_str()[0] == 0)
        end(1, false, "Could not find font '%s'", font_name);

    // Certain versions of freetype have problems reading files on Windows,
    // do that ourselves.
    FILE *f = fopen_u(font_path.c_str(), "rb");
    if (!f)
        end(1, false, "Could not read font '%s'\n", font_name);
    unsigned long size = file_size(f);
    ttf = new FT_Byte[size];
    ASSERT(ttf);
    if (fread(ttf, 1, size, f) != size)
        end(1, false, "Could not read font '%s': %s\n", font_name, strerror(errno));
    fclose(f);

    error = FT_New_Memory_Face(library, ttf, size, 0, &face);
    if (error == FT_Err_Unknown_File_Format)
        end(1, false, "Unknown font format for file '%s'\n", font_path.c_str());
    else if (error)
    {
        end(1, false, "Invalid font from file '%s' (size %lu): 0x%0x\n",
                   font_path.c_str(), size, error);
    }

    // Load CJK fallback font for Chinese/Japanese/Korean characters.
    // Failure is non-fatal — the game will use MISSING_CHAR for glyphs
    // that exist in neither font.
    string cjk_path;
    for (const char* candidate : CJK_CANDIDATES)
    {
        cjk_path = datafile_path(candidate, false, true);
        if (cjk_path.c_str()[0] != 0)
            break;
    }
    if (cjk_path.c_str()[0] == 0)
        cjk_path = datafile_path(font_name, false, true);
    if (cjk_path.c_str()[0] != 0)
    {
        FILE *fc = fopen_u(cjk_path.c_str(), "rb");
        if (fc)
        {
            unsigned long cjk_size = file_size(fc);
            cjk_ttf = new FT_Byte[cjk_size];
            if (fread(cjk_ttf, 1, cjk_size, fc) == cjk_size)
            {
                FT_Error cjk_err = FT_New_Memory_Face(library, cjk_ttf,
                                        cjk_size, 0, &cjk_face);
                if (!cjk_err)
                {
                    // Pixel size will be set in configure_font() after
                    // m_max_advance is available for CJK advance calibration.
                }
                else
                {
                    delete[] cjk_ttf;
                    cjk_ttf = nullptr;
                    cjk_face = nullptr;
                }
            }
            else
            {
                delete[] cjk_ttf;
                cjk_ttf = nullptr;
            }
            fclose(fc);
        }
    }

    // Warn if CJK fallback font could not be loaded — Chinese, Japanese, and
    // Korean characters will display as placeholder blocks.
    if (!cjk_face)
    {
        fprintf(stderr, "WARNING: CJK fallback font not found or failed to load.\n"
                        "  Expected at: %s\n"
                        "  CJK characters will render as placeholder blocks.\n"
                        "  Set tile_font_crt_file in init.txt or place a compatible font in\n"
                        "  contrib/fonts/ for proper CJK rendering.\n",
                        cjk_path.c_str()[0] ? cjk_path.c_str()
                                            : "(not found in search path)");
        mprf(MSGCH_ERROR,
            "CJK fallback font not found. Set tile_font_crt_file in init.txt"
            " to a CJK-capable font for proper rendering.");
    }

    return configure_font();
}

bool FTFontWrapper::resize(unsigned int size)
{
    fsize = size;
    return configure_font();
}

bool FTFontWrapper::is_cjk_primary() const
{
    if (!face)
        return false;

    // A common unified ideograph is a reliable signal that the primary face
    // itself is CJK-capable (e.g. Maple Mono, Sarasa SC), not just Latin-only
    // with a separate fallback.
    return FT_Get_Char_Index(face, 0x4E00) != 0;
}

FTFontWrapper::GlyphInfo& FTFontWrapper::get_glyph_info(char32_t ch)
{
    // cache glyph info in a single large buffer by unicode codepoint
    // currently dat/ only has codepoints going up to around 65536
    if (ch >= m_glyphs.size())
    {
        auto old_sz = m_glyphs.size();
        m_glyphs.resize(ch+1);
        for (size_t i = old_sz; i < m_glyphs.size(); i++)
            m_glyphs[i].valid = false;
    }
    GlyphInfo &glyph = m_glyphs[ch];
    if (!glyph.valid)
    {
        FT_Int glyph_index = FT_Get_Char_Index(face, ch);
        FT_Face use_face = face;

        // Try CJK fallback font if the primary font lacks this glyph
        if (!glyph_index && cjk_face)
        {
            glyph_index = FT_Get_Char_Index(cjk_face, ch);
            if (glyph_index)
                use_face = cjk_face;
        }

        if (!glyph_index)
            glyph_index = FT_Get_Char_Index(use_face, MISSING_CHAR);

        // need to use FT_LOAD_RENDER, otherwise glyph->bitmap isn't loaded
        FT_Error error = FT_Load_Glyph(use_face, glyph_index, FT_LOAD_RENDER |
                (Options.tile_font_ft_light ? FT_LOAD_TARGET_LIGHT : 0));
        ASSERT(!error);
        FT_Bitmap *bmp = &use_face->glyph->bitmap;
        ASSERT(bmp);

        glyph.offset = use_face->glyph->bitmap_left;
        glyph.advance = use_face->glyph->advance.x >> 6;
        glyph.ascender = use_face->glyph->bitmap_top;
        glyph.width = bmp->width;
        glyph.renderable = !!bmp->buffer;

        // For double-width characters from the primary font (e.g.
        // fullwidth punctuation that DejaVu supports), force advance
        // to the grid metric so grid rendering stays aligned.
        // For CJK fallback font glyphs, keep the native advance: in
        // free-form rendering (tooltips, menus, item descriptions),
        // Quantize double-width advance to the monospace grid.
        // The CJK fallback font's native advance (~20px) differs from
        // 2 * cell width (32px at 16px). Forcing advance to the grid
        // value makes string_width/store/render_textblock all agree,
        // eliminating column misalignment proportional to CJK count.
        int cw = wcwidth(ch);
        // Quantize all double-width advance to the grid cell.
        // Even well-designed fonts (Sarasa Fixed) can have sub-pixel
        // rounding differences at certain FreeType pixel sizes.
        // Forcing exact 2*cell advance guarantees zero cumulative drift.
        if (cw > 1)
            glyph.advance = m_max_advance.x * cw;

        // For CJK fallback glyphs, use Sarasa's native ascender values.
        // Forcing a uniform ascender caused glyphs to appear at different
        // heights because each CJK character's bitmap has different visual
        // content within the same glyph cell (e.g. "一" vs "龘").
        // Sarasa Mono SC is designed to be baseline-compatible at the same
        // point size, so native ascenders give consistent results.

        glyph.valid = true;
    }
    return glyph;
}

void FTFontWrapper::load_glyph(unsigned int c, char32_t uchar)
{
    // get on with rendering the new glyph
    FT_Error error;
    FT_Int glyph_index = FT_Get_Char_Index(face, uchar);
    FT_Face use_face = face;

    // Try CJK fallback font if the primary font lacks this glyph
    if (!glyph_index && cjk_face)
    {
        glyph_index = FT_Get_Char_Index(cjk_face, uchar);
        if (glyph_index)
            use_face = cjk_face;
    }

    if (!glyph_index)
        glyph_index = FT_Get_Char_Index(use_face, MISSING_CHAR);

    error = FT_Load_Glyph(use_face, glyph_index, FT_LOAD_RENDER |
        (Options.tile_font_ft_light ? FT_LOAD_TARGET_LIGHT : 0));
    ASSERT(!error);

    FT_Bitmap *bmp = &use_face->glyph->bitmap;
    ASSERT(bmp);

    // Was int prior to freetype 2.5.4, then became unsigned.
    typedef decltype(bmp->width) ftint;

    // Some glyphs (e.g. ' ') don't get a buffer.
    if (bmp->buffer)
    {
        ASSERT(bmp->pixel_mode == FT_PIXEL_MODE_GRAY);
        ASSERT(bmp->num_grays == 256);

        // Horizontal offset stored in m_atlas and handled when drawing
        const unsigned int offset_x = 0;
        const unsigned int offset_y = 0;
        memset(pixels, 0, sizeof(unsigned char) * 4 * charsz.x * charsz.y);

        // Some fonts have wrong size info
        const ftint charw = bmp->width;
        bmp->width = min(bmp->width, ftint(charsz.x));
        bmp->rows = min(bmp->rows, ftint(charsz.y));

        for (ftint x = 0; x < bmp->width; x++)
            for (ftint y = 0; y < bmp->rows; y++)
            {
                unsigned int idx = offset_x + x + (offset_y + y) * charsz.x;
                idx *= 4;
                if (x < bmp->width && y < bmp->rows)
                {
                    unsigned char alpha = bmp->buffer[x + charw * y];
                    pixels[idx] = 255;
                    pixels[idx + 1] = 255;
                    pixels[idx + 2] = 255;
                    pixels[idx + 3] = alpha;
                }
            }

        unwind_bool noscaling(Options.tile_filter_scaling, false);
        bool success = m_tex.load_texture(pixels, charsz.x, charsz.y,
                            MIPMAP_NONE,
                            (c % m_atlas_columns) * charsz.x,
                            (c / m_atlas_columns) * charsz.y);
        ASSERT(success);
    }
}

unsigned int FTFontWrapper::map_unicode(char *ch)
{
    char32_t c;
    utf8towc(&c, ch);
    return map_unicode(c);
}

unsigned int FTFontWrapper::map_unicode(char32_t uchar)
{
    // Fast path: hash lookup for O(1) glyph-to-slot resolution.
    auto it = m_glyph_to_slot.find(uchar);
    if (it != m_glyph_to_slot.end())
    {
        atlas_slot_t c = it->second;
        m_atlas[c].last_used = ++m_atlas_clock;
        m_pinned[c] = true;
        return c;
    }

    // Miss — need to load this glyph into the atlas.
    // Find an eviction candidate among unreserved, unpinned slots.
    atlas_slot_t evict = m_atlas_capacity;
    uint64_t oldest = UINT64_MAX;
    for (atlas_slot_t i = 1; i < m_atlas_capacity; i++)
    {
        if (m_atlas[i].reserved || m_pinned[i])
            continue;
        if (m_atlas[i].last_used < oldest)
        {
            oldest = m_atlas[i].last_used;
            evict = i;
        }
    }

    if (evict == m_atlas_capacity)
    {
        // Never invalidate texture coordinates already emitted by this
        // render batch. Missing glyph is preferable to corrupting the batch.
        return m_glyph_to_slot.at(MISSING_CHAR);
    }

    // Remove the old glyph from the hash map before overwriting.
    if (m_atlas[evict].uchar != 0)
    {
        m_glyph_to_slot.erase(m_atlas[evict].uchar);
        // A live FontBuffer may retain UVs for the overwritten slot.
        ++m_atlas_generation;
    }

    atlas_slot_t c = evict;

    // Count newly-loaded distinct glyphs for peak tracking.
    // Evictions replace existing entries so only increment when the
    // target slot was truly empty (first load since configure_font).
    if (!m_atlas[c].reserved && m_atlas[c].uchar == 0)
        m_peak_glyphs++;

    m_atlas[c].uchar = uchar;
    m_atlas[c].last_used = ++m_atlas_clock;
    m_glyph_to_slot[uchar] = c;
    load_glyph(c, uchar);
    m_pinned[c] = true;
    n_subst++;

    return c;
}

void FTFontWrapper::render_textblock(unsigned int x_pos, unsigned int y_pos,
                                     char32_t *chars,
                                     uint8_t *colours,
                                     unsigned int width, unsigned int height,
                                     bool drop_shadow)
{
    if (!chars || !colours || !width || !height || !m_atlas)
        return;

    clear_pins();
    coord_def adv(max(-m_min_offset, 0), 0);
    unsigned int i = 0;

    ASSERT(m_buf);
    m_buf->clear();
    n_subst = 0;

    float texcoord_dy = (float)m_max_advance.y / (float)m_tex.height();
    for (unsigned int y = 0; y < height; y++)
    {
        for (unsigned int x = 0; x < width; x++)
        {
            char32_t ch = chars[i];

            // Skip CJK continuation markers (ZERO WIDTH SPACE) inserted
            // by TextRegion::addstr_aux for double-width characters.
            if (ch == 0x200B)
            {
                i++;
                continue;
            }

            GlyphInfo &glyph = get_glyph_info(ch);
            uint8_t col_bg = colours[i] >> 4;
            uint8_t col_fg = colours[i] & 0xF;

            int char_w = wcwidth(ch);
            if (char_w <= 0)
                char_w = 1; // combining/control chars: treat as width 1

            if (col_bg != 0)
            {
                GLWPrim rect(adv.x, adv.y,
                             adv.x + m_max_advance.x * char_w,
                             adv.y + m_max_advance.y);
                // Leave tex coords at their default 0.0f
                VColour col(term_colours[col_bg].r,
                            term_colours[col_bg].g,
                            term_colours[col_bg].b);
                rect.set_col(col);
                m_buf->add(rect);
            }

            adv.x += glyph.offset;

            if (glyph.renderable)
            {
                unsigned int c = map_unicode(ch);
                int this_width = glyph.width;

                float tex_x = (float)(c % m_atlas_columns) * charsz.x
                              / (float)m_tex.width();
                float tex_y = (float)(c / m_atlas_columns) * charsz.y
                              / (float)m_tex.height();
                float tex_x2 = tex_x + (float)this_width / (float)m_tex.width();
                float tex_y2 = tex_y + texcoord_dy;

                GLWPrim rect(adv.x, adv.y - glyph.ascender + m_ascender,
                             adv.x + this_width, adv.y + m_max_advance.y - glyph.ascender + m_ascender);

                VColour col(term_colours[col_fg].r,
                            term_colours[col_fg].g,
                            term_colours[col_fg].b);
                rect.set_col(col);
                rect.set_tex(tex_x, tex_y, tex_x2, tex_y2);

                m_buf->add(rect);
            }

            i++;
            // Use native glyph advance, consistent with store() and
            // string_width(). All three rendering paths (grid, free-form,
            // layout) now agree on per-character advance, eliminating
            // cumulative pixel drift between columns.
            adv.x += glyph.advance - glyph.offset;

            // See if we need to flush prematurely.
            if (m_atlas_capacity > RESERVED_GLYPHS
                && n_subst >= int(m_atlas_capacity - RESERVED_GLYPHS))
            {
                draw_m_buf(x_pos, y_pos, drop_shadow);
                m_buf->clear();
                n_subst = 0;
                clear_pins();
            }
        }

        adv.x = 0;
        adv.y += m_max_advance.y;
    }

    draw_m_buf(x_pos, y_pos, drop_shadow);
}

void FTFontWrapper::draw_m_buf(unsigned int x_pos, unsigned int y_pos,
                               bool drop_shadow)
{
    if (!m_buf->size())
        return;

    GLState state;
    state.array_vertex = true;
    state.array_texcoord = true;
    state.array_colour = true;
    state.blend = true;
    state.texture = true;

    m_tex.bind();

    GLW_3VF trans(x_pos, y_pos, 0.0f);
    GLW_3VF scale(display_density.scale_to_logical(),
                  display_density.scale_to_logical(), 1);

    if (drop_shadow)
    {
        GLState state_shadow;
        state_shadow.array_colour = false;
        state_shadow.colour = VColour::black;

        GLW_3VF trans_shadow(trans.x + 1, trans.y + 1, 0.0f);
        glmanager->set_transform(trans_shadow, scale);

        m_buf->draw(state_shadow);
    }

    glmanager->set_transform(trans, scale);
    m_buf->draw(state);

    glmanager->reset_transform();
}

static void _draw_box(int x_pos, int y_pos, int width, int height, VColour colour)
{
    unique_ptr<GLShapeBuffer> buf(GLShapeBuffer::create(false, true));
    GLWPrim rect(x_pos, y_pos, x_pos + width, y_pos + height);

    rect.set_col(colour);

    buf->add(rect);

    // Load identity matrix
    glmanager->reset_transform();

    GLState state;
    state.array_vertex = true;
    state.array_colour = true;
    state.blend = true;
    buf->draw(state);
}

unsigned int FTFontWrapper::string_height(const formatted_string &str, bool logical) const
{
    string temp = str.tostring();
    return string_height(temp.c_str(), logical);
}

unsigned int FTFontWrapper::string_height(const char *text, bool logical) const
{
    int height = 1;
    for (char *itr = (char *)text; *itr; itr = next_glyph(itr))
        if (*itr == '\n')
            height++;

    return max_height(height, logical);
}

unsigned int FTFontWrapper::string_width(const formatted_string &str, bool logical)
{
    string temp = str.tostring();
    return string_width(temp.c_str(), logical);
}

unsigned int FTFontWrapper::string_width(const char *text, bool logical)
{
    unsigned int base_width = max(-m_min_offset, 0);
    unsigned int max_str_width = 0;

    unsigned int width = base_width;
    unsigned int adjust = 0;
    for (char *itr = (char *)text; *itr; itr = next_glyph(itr))
    {
        if (*itr == '\n')
        {
            max_str_width = max(width + adjust, max_str_width);
            width = base_width;
            adjust = 0;
        }
        else
        {
            char32_t ch;
            utf8towc(&ch, itr);
            GlyphInfo &glyph = get_glyph_info(ch);
            // Use native glyph advance for consistency with store().
            // Both menu titles and data entries use store() for
            // rendering, so layout (string_width) and rendering
            // (store) must agree on per-character advance.
            // render_textblock() uses grid advance independently.
            width += glyph.advance;
            adjust = max(0, glyph.width - glyph.advance);
        }
    }

    max_str_width = max(width + adjust, max_str_width);
    return logical ? display_density.device_to_logical(max_str_width)
                   : max_str_width;
}

// Find the position in `text` that does not exceed max_str_width, a width
// in pixels. Returns INT_MAX if the string doesn't exceed INT_MAX. Stops at
// newlines.
int FTFontWrapper::find_index_before_width(const char *text, int max_str_width)
{
    int width = max(-m_min_offset, 0);

    max_str_width *= display_density.scale_to_device();

    for (char *itr = (char *)text; *itr; itr = next_glyph(itr))
    {
        if (*itr == '\n')
            return INT_MAX;

        char32_t ch;
        utf8towc(&ch, itr);
        GlyphInfo &glyph = get_glyph_info(ch);
        width += glyph.advance;
        int adjust = max(0, glyph.width - glyph.advance);
        if (width + adjust > max_str_width)
            return itr-text;
    }

    return INT_MAX;
}

formatted_string FTFontWrapper::split(const formatted_string &str,
                                      unsigned int max_str_width,
                                      unsigned int max_str_height)
{
    int max_lines = display_density.logical_to_device(max_str_height)
                                                        / char_height(false);
    return tilefont_internal::split_formatted_string(str, max_lines,
        [this, max_str_width](const char *line)
        {
            return find_index_before_width(line, max_str_width);
        });
}

/**
 * Render a tooltip around the given position.
 *
 * @param px the x coordinate
 * @param py the y coordinate
 * @param text the string to render
 * @param min_pos the top-left boundary of the screen
 * @param max_pos the bottom-right boundary of the screen
 */
void FTFontWrapper::render_tooltip(int px, int py,
                                  const formatted_string &text,
                                  const coord_def &min_pos,
                                  const coord_def &max_pos)
{
    const int outline = 7;
    const int max_text_width = max_pos.x - min_pos.x - 2 * outline;
    const int max_text_height = max_pos.y - min_pos.y - 2 * outline;
    if (max_text_width <= 0 || max_text_height <= 0)
        return;

    const formatted_string fitted = split(text, max_text_width,
                                           max_text_height);
    if (fitted.empty())
        return;

    const int wx = string_width(fitted);
    const int wy = string_height(fitted);
    const tilefont_internal::tooltip_position pos =
        tilefont_internal::place_tooltip(px, py, wx, wy, outline,
                                         min_pos, max_pos);

    const VColour border_colour(125, 98, 60);
    const VColour bg_colour(4, 2, 4);
    _draw_box(pos.x - outline, pos.y - outline,
              wx + 2 * outline, wy + 2 * outline, border_colour);
    const int inner_outline = outline - 2;
    _draw_box(pos.x - inner_outline, pos.y - inner_outline,
              wx + 2 * inner_outline, wy + 2 * inner_outline, bg_colour);

    render_string(pos.x, pos.y, fitted);
}

/**
 * Render a string at the given position.
 *
 * @param px the x coordinate
 * @param py the y coordinate
 * @param text the string to render
 * @param font_colour the text colour to use
 */
void FTFontWrapper::render_string(int px, int py,
                                  const formatted_string &text)
{
    clear_pins();
    glmanager->reset_transform();
    FontBuffer m_font_buf(this);
    m_font_buf.add(text, px, py);
    m_font_buf.draw();
}

/**
 * Render a string hovering above the given position, centred horizontally.
 *
 * @param px the x coordinate
 * @param py the y coordinate
 * @param text the string to render
 * @param font_colour the text colour to use
 */
void FTFontWrapper::render_hover_string(int px, int py,
                                  const formatted_string &text)
{
    const int wx = string_width(text);
    const int wy = string_height(text);
    const int ty = py - wy;
    const int tx = px - wx / 2;

    render_string(tx, ty, text);
}

/**
 * Store a string in a FontBuffer.
 *
 * @param buf the FontBuffer to store the glyph in.
 * @param x the x coordinate
 * @param y the y coordinate
 * @param str the string to store
 * @param col a foreground color
 */
void FTFontWrapper::store(FontBuffer &buf, float &x, float &y,
                          const string &str, const VColour &col)
{
    store(buf, x, y, str, col, x);
}

/**
 * Store a string in a FontBuffer.
 *
 * @param buf the FontBuffer to store the glyph in.
 * @param x the x coordinate
 * @param y the y coordinate
 * @param str the string to store
 * @param col a foreground color
 */
void FTFontWrapper::store(FontBuffer &buf, float &x, float &y,
                          const string &str,
                          const VColour &fg, const VColour &bg)
{
    store(buf, x, y, str, fg, bg, x);
}

/**
 * Store a string in a FontBuffer.
 *
 * @param buf the FontBuffer to store the glyph in.
 * @param x the x coordinate
 * @param y the y coordinate
 * @param str the string to store
 * @param col a foreground color
 * @param orig_x an x offset to use as an origin
 */
void FTFontWrapper::store(FontBuffer &buf, float &x, float &y,
                          const string &str, const VColour &col, float orig_x)
{
    // do we really need this whole mess of overloads?
    store(buf, x, y, str, col, VColour::transparent, orig_x);
}

void FTFontWrapper::store(FontBuffer &buf, float &x, float &y,
                          const string &str,
                          const VColour &fg, const VColour &bg, float orig_x)
{
    const char *sp = str.c_str();
    char32_t c;
    while (int s = utf8towc(&c, sp))
    {
        sp += s;
        if (c == '\n')
        {
            x = orig_x;
            y += m_max_advance.y * display_density.scale_to_logical();
        }
        else if (bg == VColour::transparent)
            store(buf, x, y, c, fg);
        else
            store(buf, x, y, c, fg, bg);
    }
}

/**
 * Store a formatted_string in a FontBuffer.
 *
 * @param buf the FontBuffer to store the glyph in.
 * @param x the x coordinate
 * @param y the y coordinate
 * @param fs the formatted string to store
 */
void FTFontWrapper::store(FontBuffer &buf, float &x, float &y,
                          const formatted_string &fs)
{
    store(buf, x, y, fs, x);
}

/**
 * Store a formatted_string in a FontBuffer.
 *
 * @param buf the FontBuffer to store the glyph in.
 * @param x the x coordinate
 * @param y the y coordinate
 * @param fs the formatted string to store
 * @param orig_x an x offset to use as an origin
 */
void FTFontWrapper::store(FontBuffer &buf, float &x, float &y,
                          const formatted_string &fs, float orig_x)
{
    int colour = LIGHTGREY;
    int bg = -1;
    for (const formatted_string::fs_op &op : fs.ops)
    {
        switch (op.type)
        {
            case FSOP_COLOUR:
                colour = op.colour & 0xF;
                break;
            case FSOP_BG:
                bg = op.colour;
                break;
            case FSOP_TEXT:
                if (bg >= 0)
                {
                    store(buf, x, y, op.text,
                        term_colours[colour], term_colours[bg], orig_x);
                }
                else
                    store(buf, x, y, op.text, term_colours[colour], orig_x);
                break;
            default:
                break;
        }
    }
}

/**
 * Store a single glyph in a FontBuffer.
 *
 * @param buf the FontBuffer to store the glyph in.
 * @param x the x coordinate
 * @param y the y coordinate
 * @param ch a (unicode) character
 * @param fg_col the foreground color to print
 */
void FTFontWrapper::store(FontBuffer &buf, float &x, float &y,
                          char32_t ch, const VColour &col)
{
    GlyphInfo &glyph = get_glyph_info(ch);
    float density_mult = display_density.scale_to_logical();

    if (!glyph.renderable)
    {
        x += glyph.advance * density_mult;
        return;
    }

    unsigned int c = map_unicode(ch);
    int this_width = glyph.width;

    float pos_sx = x + glyph.offset * density_mult;
    float pos_sy = y - (glyph.ascender - m_ascender) * density_mult;
    float pos_ex = pos_sx + this_width * density_mult;
    float pos_ey = y + (m_max_advance.y - glyph.ascender + m_ascender)
                   * density_mult;

    float tex_sx = (float)(c % m_atlas_columns) * charsz.x / m_tex.width();
    float tex_sy = (float)(c / m_atlas_columns) * charsz.y / m_tex.height();
    float tex_ex = tex_sx + (float)this_width / m_tex.width();
    float tex_ey = tex_sy + (float)m_max_advance.y / m_tex.height();

    GLWPrim rect(pos_sx, pos_sy, pos_ex, pos_ey);
    rect.set_tex(tex_sx, tex_sy, tex_ex, tex_ey);
    rect.set_col(col);
    buf.add_primitive(rect);


    x += glyph.advance * density_mult;
}

/**
 * Store a single glyph, with both a background and a foreground color.
 *
 * @param buf the FontBuffer to store the glyph in.
 * @param x the x coordinate
 * @param y the y coordinate
 * @param ch a (unicode) character
 * @param fg_col the foreground color to print
 * @param bg_col the background color to print
 */
void FTFontWrapper::store(FontBuffer &buf, float &x, float &y,
                          char32_t ch, const VColour &fg_col, const VColour &bg_col)
{
    GlyphInfo &glyph = get_glyph_info(ch);
    const float density_mult = display_density.scale_to_logical();

    // if the advance is 0, use the max width
    const int this_width = glyph.advance ? glyph.advance : char_width(false);
    const float bg_width = this_width * density_mult;
    const float bg_height = char_height(false) * density_mult;

    GLWPrim bg_rect(x, y, x + bg_width, y + bg_height);
    bg_rect.set_col(bg_col);
    buf.add_primitive(bg_rect);

    store(buf, x, y, ch, fg_col);
}

/**
 * Find the (max) width of a character, in device or logical pixels.
 *
 * This will round up if a font uses logically fractional advances! It is
 * better to use max_width or string_width if you need multiple characters.
 */
unsigned int FTFontWrapper::char_width(bool logical) const
{
    return max_width(1, logical);
}

/**
 * Find the (max) height of a character, in device or logical pixels.
 *
 * This will round up if a font uses logically fractional advances! It is
 * better to use max_height or string_height if you need multiple characters.
 */
unsigned int FTFontWrapper::char_height(bool logical) const
{
    return max_height(1, logical);
}

/**
 * Find the (max) width of `length` characters, in device or logical pixels.
 *
 * This will take into account sub-logical-pixel advances. For non-fixed-width
 * fonts use string_width.
 */
unsigned int FTFontWrapper::max_width(int length, bool logical) const
{
    const int device_length = m_max_advance.x * length;

    return logical ? display_density.device_to_logical(device_length)
                   : device_length;
}

/**
 * Find the (max) height of `length` lines, in device or logical pixels.
 *
 * This will take into account sub-logical-pixel advances. For non-fixed-width
 * fonts use string_height.
 */
unsigned int FTFontWrapper::max_height(int length, bool logical) const
{
    const int device_height = m_max_advance.y * length;

    return logical ? display_density.device_to_logical(device_height)
                   : device_height;
}


const GenericTexture *FTFontWrapper::font_tex() const
{
    return &m_tex;
}

#endif // USE_FT
#endif // USE_TILE_LOCAL
