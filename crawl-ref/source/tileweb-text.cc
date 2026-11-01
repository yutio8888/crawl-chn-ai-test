
#include "AppHdr.h"

#ifdef USE_TILE_WEB

#include "tileweb-text.h"

#include "stringutil.h"
#include "tiles-build-specific.h"
#include "unicode.h"

WebTextArea::WebTextArea(string name) :
    mx(0),
    my(0),
    m_cbuf(nullptr),
    m_abuf(nullptr),
    m_old_cbuf(nullptr),
    m_old_abuf(nullptr),
    m_client_side_name(name),
    m_dirty(true)
{
}

WebTextArea::~WebTextArea()
{
    if (m_cbuf != nullptr)
    {
        delete[] m_cbuf;
        delete[] m_abuf;
        delete[] m_old_cbuf;
        delete[] m_old_abuf;
    }
}

void WebTextArea::resize(int x, int y)
{
    if (mx == x && my == y)
        return;

    mx = x;
    my = y;

    if (m_cbuf != nullptr)
    {
        delete[] m_cbuf;
        delete[] m_abuf;
        delete[] m_old_cbuf;
        delete[] m_old_abuf;
    }

    int size = mx * my;
    m_cbuf = new char32_t[size];
    m_abuf = new uint8_t[size];
    m_old_cbuf = new char32_t[size];
    m_old_abuf = new uint8_t[size];
    m_combining.assign(size, "");
    m_old_combining.assign(size, "");

    for (int i = 0; i < mx * my; i++)
    {
        m_cbuf[i] = ' ';
        m_abuf[i] = 0;
        m_old_cbuf[i] = ' ';
        m_old_abuf[i] = 0;
    }

    m_dirty = true;

    on_resize();
}

void WebTextArea::clear()
{
    std::fill(m_combining.begin(), m_combining.end(), "");
    for (int i = 0; i < mx * my; i++)
    {
        m_cbuf[i] = ' ';
        m_abuf[i] = 0;
    }

    m_dirty = true;
}

// NUL cannot be printed in a text area; it marks a wide glyph's second cell.
static constexpr char32_t WIDE_CONTINUATION = 0;

void WebTextArea::put_character(char32_t chr, int fg, int bg, int x, int y)
{
    ASSERT_RANGE(x, 0, mx);
    ASSERT_RANGE(y, 0, my);
    const int width = wcwidth(chr);
    if (width <= 0)
        return;
    // Direct cell writes cannot wrap. Never leave half a glyph at the edge.
    if (x + width > mx)
        chr = ' ';
    const int cells = wcwidth(chr);
    const uint8_t col = (fg & 0xf) + (bg << 4);
    const int row = y * mx;

    auto set_cell = [&](int cell, char32_t value, uint8_t colour)
    {
        if (m_cbuf[row + cell] != value || m_abuf[row + cell] != colour
            || !m_combining[row + cell].empty())
            m_dirty = true;
        m_combining[row + cell].clear();
        m_cbuf[row + cell] = value;
        m_abuf[row + cell] = colour;
    };

    // Erasing either half erases the whole previous glyph. This also handles
    // writing a wide glyph across two neighbouring wide glyphs.
    for (int cell = x; cell < x + cells; ++cell)
    {
        if (m_cbuf[row + cell] == WIDE_CONTINUATION && cell > 0)
            set_cell(cell - 1, ' ', m_abuf[row + cell - 1]);
        else if (wcwidth(m_cbuf[row + cell]) == 2 && cell + 1 < mx)
            set_cell(cell + 1, ' ', m_abuf[row + cell + 1]);
    }
    set_cell(x, chr, col);
    if (cells == 2)
        set_cell(x + 1, WIDE_CONTINUATION, col);
}

void WebTextArea::put_string(const char32_t *str, int fg, int bg, int &x, int &y)
{
    if (mx <= 0 || my <= 0)
        return;

    for (; *str; ++str)
    {
        if (*str == '\r')
            continue;
        if (*str == '\n')
        {
            x = 0;
            ++y;
            continue;
        }
        const int width = wcwidth(*str);
        if (width == 0)
        {
            // Keep combining marks with their base, including a base ending
            // at the right edge. A continuation cell is never itself a base.
            if (x > 0 && x <= mx && y >= 0 && y < my)
            {
                int cell = y * mx + x - 1;
                if (m_cbuf[cell] == WIDE_CONTINUATION && x > 1)
                    --cell;
                char buf[5];
                buf[wctoutf8(buf, *str)] = 0;
                m_combining[cell] += buf;
                m_dirty = true;
            }
            continue;
        }
        if (width < 0 || width > mx)
            continue;
        if (x + width > mx)
        {
            x = 0;
            ++y;
        }
        if (y >= 0 && y < my)
            put_character(*str, fg, bg, x, y);
        x += width;
    }
}

string WebTextArea::render_line(int y, bool &dirty)
{
    int last_col = -1;
    int space_count = 0;
    string html;
    dirty = false;

    for (int x = 0; x < mx; ++x)
    {
        const int offset = x + y * mx;
        const char32_t chr = m_cbuf[offset];
        const uint8_t col = m_abuf[offset];
        if (chr != m_old_cbuf[offset] || col != m_old_abuf[offset]
            || m_combining[offset] != m_old_combining[offset])
        {
            dirty = true;
            m_old_cbuf[offset] = chr;
            m_old_abuf[offset] = col;
            m_old_combining[offset] = m_combining[offset];
        }
        // The preceding span already occupies this terminal cell.
        if (chr == WIDE_CONTINUATION)
            continue;

        if (chr == ' ' && (col >> 4) == 0 && m_combining[offset].empty())
        {
            ++space_count;
            continue;
        }
        if (space_count && last_col != -1 && (last_col >> 4) != 0)
        {
            html += "</span>";
            last_col = -1;
        }
        html.append(space_count, ' ');
        space_count = 0;

        if (col != last_col)
        {
            if (last_col != -1)
                html += "</span>";
            html += make_stringf("<span class=\"fg%d bg%d\">",
                                 col & 0xf, (col >> 4) & 0xf);
            last_col = col;
        }
        const bool wide = wcwidth(chr) == 2;
        if (wide)
            html += "<span class=\"webtiles-wide\">";
        switch (chr)
        {
        case '<': html += "&lt;"; break;
        case '>': html += "&gt;"; break;
        case '&': html += "&amp;"; break;
        case '"': html += "&quot;"; break;
        default:
            char buf[5];
            buf[wctoutf8(buf, chr)] = 0;
            html += buf;
            break;
        }
        html += m_combining[offset];
        if (wide)
            html += "</span>";
    }
    if (last_col != -1)
        html += "</span>";
    return html;
}

void WebTextArea::send(bool force)
{
    if (m_cbuf == nullptr || (!force && !m_dirty))
        return;
    m_dirty = false;

    bool sending = false;
    auto start_message = [&]()
    {
        tiles.json_open_object();
        tiles.json_write_string("msg", "txt");
        tiles.json_write_string("id", m_client_side_name);
        if (force)
            tiles.json_write_bool("clear", true);
        tiles.json_open_object("lines");
        sending = true;
    };
    // A forced blank area must still clear stale client-side rows.
    if (force)
        start_message();

    for (int y = 0; y < my; ++y)
    {
        bool dirty;
        const string html = render_line(y, dirty);
        if (dirty || (force && !html.empty()))
        {
            if (!sending)
                start_message();
            tiles.json_write_string(make_stringf("%d", y), html);
        }
    }
    if (sending)
    {
        tiles.json_close_object();
        tiles.json_close_object();
        tiles.finish_message();
    }
}

void WebTextArea::on_resize()
{
}
#endif
