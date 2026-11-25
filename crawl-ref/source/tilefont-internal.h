#pragma once

#ifdef USE_TILE_LOCAL

#include <algorithm>
#include <climits>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <unordered_map>
#include <vector>

#include "coord-def.h"
#include "format.h"
#include "unicode.h"

namespace tilefont_internal
{

using atlas_slot_t = uint16_t;
constexpr atlas_slot_t INVALID_ATLAS_SLOT = UINT16_MAX;

inline void choose_atlas_grid(unsigned int cell_width,
                              unsigned int cell_height,
                              unsigned int max_texture_size,
                              unsigned int bytes_per_pixel,
                              unsigned int max_columns,
                              size_t byte_budget,
                              unsigned int &columns,
                              unsigned int &rows)
{
    columns = 0;
    rows = 0;
    if (!cell_width || !cell_height || !bytes_per_pixel || !max_columns)
        return;

    unsigned int best_capacity = 0;
    unsigned int best_long_side = UINT_MAX;
    unsigned int best_side_difference = UINT_MAX;

    for (unsigned int candidate_columns = 1;
         candidate_columns <= max_columns;
         candidate_columns *= 2)
    {
        const unsigned int width = candidate_columns * cell_width;
        if (width > max_texture_size)
            continue;

        for (unsigned int candidate_rows = 1;
             candidate_rows <= max_columns;
             candidate_rows *= 2)
        {
            const unsigned int height = candidate_rows * cell_height;
            if (height > max_texture_size)
                continue;

            const size_t bytes = size_t(width) * height * bytes_per_pixel;
            if (bytes > byte_budget)
                continue;

            const unsigned int capacity = candidate_columns * candidate_rows;
            const unsigned int long_side = std::max(width, height);
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

struct AtlasAcquireResult
{
    atlas_slot_t slot = 0;
    bool needs_load = false;
    bool evicted = false;
    bool overflow_missing = false;
};

// O(1) free-slot allocation and intrusive-list LRU cache for font atlas slots.
// Reserved slots (white colour bar, MISSING_CHAR, printable ASCII) are excluded
// from the LRU list and can never be evicted. Pinned slots are protected within
// the active render batch so live vertex UVs cannot be overwritten mid-batch.
class FontAtlasCache
{
public:
    void reset(unsigned int capacity, bool bump_generation = true)
    {
        if (bump_generation)
            ++m_generation;
        m_capacity = std::min<unsigned int>(capacity, INVALID_ATLAS_SLOT);
        m_entries.assign(m_capacity, Entry());
        m_pinned.assign(m_capacity, 0);
        m_glyph_to_slot.clear();
        m_lru_head = INVALID_ATLAS_SLOT;
        m_lru_tail = INVALID_ATLAS_SLOT;
        m_next_free_slot = 0;
        m_peak_glyphs = 0;
    }

    void reserve_slot(atlas_slot_t slot, char32_t uchar)
    {
        if (slot >= m_capacity)
            return;
        m_entries[slot].uchar = uchar;
        m_entries[slot].reserved = true;
        if (uchar != 0)
            m_glyph_to_slot[uchar] = slot;
    }

    void clear_pins()
    {
        std::fill(m_pinned.begin(), m_pinned.end(), 0);
    }

    AtlasAcquireResult acquire(char32_t uchar, char32_t missing_char)
    {
        AtlasAcquireResult res;

        auto it = m_glyph_to_slot.find(uchar);
        if (it != m_glyph_to_slot.end())
        {
            const atlas_slot_t slot = it->second;
            if (!m_entries[slot].reserved)
                touch_lru(slot);
            m_pinned[slot] = 1;
            res.slot = slot;
            return res;
        }

        while (m_next_free_slot < m_capacity
               && m_entries[m_next_free_slot].reserved)
        {
            ++m_next_free_slot;
        }

        if (m_next_free_slot < m_capacity)
        {
            const atlas_slot_t slot = static_cast<atlas_slot_t>(m_next_free_slot++);
            m_entries[slot].uchar = uchar;
            m_glyph_to_slot[uchar] = slot;
            push_back_lru(slot);
            m_pinned[slot] = 1;
            ++m_peak_glyphs;
            res.slot = slot;
            res.needs_load = true;
            return res;
        }

        // Atlas is full: walk from LRU head to find the oldest unpinned slot.
        // Recently touched/pinned slots live near the tail, so this normally
        // succeeds in O(1) steps.
        atlas_slot_t victim = INVALID_ATLAS_SLOT;
        for (atlas_slot_t cur = m_lru_head; cur != INVALID_ATLAS_SLOT;
             cur = m_entries[cur].lru_next)
        {
            if (!m_pinned[cur])
            {
                victim = cur;
                break;
            }
        }

        if (victim == INVALID_ATLAS_SLOT)
        {
            auto miss_it = m_glyph_to_slot.find(missing_char);
            res.slot = (miss_it != m_glyph_to_slot.end()) ? miss_it->second : 0;
            res.overflow_missing = true;
            return res;
        }

        if (m_entries[victim].uchar != 0)
        {
            m_glyph_to_slot.erase(m_entries[victim].uchar);
            ++m_generation;
            res.evicted = true;
        }

        m_entries[victim].uchar = uchar;
        m_glyph_to_slot[uchar] = victim;
        touch_lru(victim);
        m_pinned[victim] = 1;
        res.slot = victim;
        res.needs_load = true;
        return res;
    }

    bool empty() const { return m_capacity == 0; }
    unsigned int capacity() const { return m_capacity; }
    unsigned int peak_glyphs() const { return m_peak_glyphs; }
    uint64_t generation() const { return m_generation; }
    void bump_generation() { ++m_generation; }

private:
    struct Entry
    {
        char32_t uchar = 0;
        atlas_slot_t lru_prev = INVALID_ATLAS_SLOT;
        atlas_slot_t lru_next = INVALID_ATLAS_SLOT;
        bool reserved = false;
    };

    void push_back_lru(atlas_slot_t slot)
    {
        m_entries[slot].lru_prev = m_lru_tail;
        m_entries[slot].lru_next = INVALID_ATLAS_SLOT;
        if (m_lru_tail != INVALID_ATLAS_SLOT)
            m_entries[m_lru_tail].lru_next = slot;
        else
            m_lru_head = slot;
        m_lru_tail = slot;
    }

    void touch_lru(atlas_slot_t slot)
    {
        if (slot == m_lru_tail)
            return;

        const atlas_slot_t prev = m_entries[slot].lru_prev;
        const atlas_slot_t next = m_entries[slot].lru_next;

        if (prev != INVALID_ATLAS_SLOT)
            m_entries[prev].lru_next = next;
        else
            m_lru_head = next;

        if (next != INVALID_ATLAS_SLOT)
            m_entries[next].lru_prev = prev;

        push_back_lru(slot);
    }

    std::vector<Entry> m_entries;
    std::unordered_map<char32_t, atlas_slot_t> m_glyph_to_slot;
    std::vector<uint8_t> m_pinned;
    atlas_slot_t m_lru_head = INVALID_ATLAS_SLOT;
    atlas_slot_t m_lru_tail = INVALID_ATLAS_SLOT;
    unsigned int m_capacity = 0;
    unsigned int m_next_free_slot = 0;
    unsigned int m_peak_glyphs = 0;
    uint64_t m_generation = 0;
};

// Resolve the original codepoint before considering a compatibility glyph.
// Keep the caller's codepoint unchanged: layout still uses its Unicode width.
template <typename Lookup>
unsigned int lookup_glyph(char32_t ch, Lookup lookup)
{
    unsigned int index = lookup(ch);
    if (!index && ch >= 0xff01 && ch <= 0xff5e)
        index = lookup(ch - 0xfee0);
    return index;
}

struct tooltip_position
{
    int x;
    int y;
};

inline tooltip_position place_tooltip(int anchor_x, int anchor_y,
                                      int text_width, int text_height,
                                      int outline,
                                      const coord_def &min_pos,
                                      const coord_def &max_pos)
{
    tooltip_position pos = { anchor_x - 15, anchor_y + 20 };

    const int min_x = min_pos.x + outline;
    const int max_x = max_pos.x - outline - text_width;
    const int min_y = min_pos.y + outline;
    const int max_y = max_pos.y - outline - text_height;

    // If content is still too large, keep its beginning visible. Normal
    // tooltips are split to fit before this helper is called.
    if (max_x < min_x)
        pos.x = min_x;
    else if (pos.x < min_x)
        pos.x = min_x;
    else if (pos.x > max_x)
        pos.x = max_x;

    if (max_y < min_y)
        pos.y = min_y;
    else if (pos.y < min_y)
        pos.y = min_y;
    else if (pos.y > max_y)
        pos.y = max_y;

    return pos;
}

inline bool insert_text(formatted_string &text, size_t byte_index,
                        const string &insertion)
{
    for (formatted_string::fs_op &op : text.ops)
    {
        if (op.type != FSOP_TEXT)
            continue;

        if (byte_index <= op.text.size())
        {
            op.text.insert(byte_index, insertion);
            return true;
        }
        byte_index -= op.text.size();
    }
    return false;
}

inline int find_newline(const char *text)
{
    const char *newline = strchr(text, '\n');
    return newline ? newline - text : INT_MAX;
}

template <typename FindLineEnd>
formatted_string split_formatted_string(const formatted_string &text,
                                        int max_lines,
                                        FindLineEnd find_line_end)
{
    if (max_lines < 1)
        return formatted_string();

    formatted_string result;
    result += text;

    string plain = text.tostring();
    if (plain.empty())
        return result;

    int num_lines = 0;
    size_t line_start = 0;
    while (true)
    {
        char *line = &plain[line_start];
        int newline = find_newline(line);
        int line_end = find_line_end(line);
        if (line_end == INT_MAX && newline == INT_MAX)
            break;

        int space_idx;
        if (newline < line_end)
            space_idx = newline;
        else
        {
            space_idx = -1;
            for (char *search = &line[line_end];
                 search > line;
                 search = prev_glyph(search, line))
            {
                if (*search == ' ')
                {
                    space_idx = search - line;
                    break;
                }
            }
        }

        if (++num_lines >= max_lines)
        {
            line_end = line_end < newline ? line_end : newline;
            int ellipses;
            if (space_idx != -1 && space_idx - line_end > 2)
                ellipses = space_idx;
            else
            {
                ellipses = line_end;
                for (int i = 0; i < 2; ++i)
                {
                    char *previous = prev_glyph(&line[ellipses], line);
                    ellipses = (previous ? previous : line) - line;
                }
            }

            result = result.chop_bytes(line_start + ellipses);
            result += "..";
            return result;
        }

        if (space_idx == newline)
            line_start += newline + 1;
        else if (space_idx != -1)
        {
            const size_t break_at = line_start + space_idx;
            plain[break_at] = '\n';
            result[break_at] = '\n';
            line_start = break_at + 1;
        }
        else
        {
            // Languages such as Chinese do not normally separate words with
            // ASCII spaces. Insert a newline at the measured UTF-8 boundary.
            int break_idx = line_end;
            if (break_idx == 0)
                break_idx = next_glyph(line) - line;

            const size_t break_at = line_start + break_idx;
            plain.insert(break_at, 1, '\n');
            const bool inserted = insert_text(result, break_at, "\n");
            ASSERT(inserted);
            line_start = break_at + 1;
        }
    }

    return result;
}

} // namespace tilefont_internal

#endif // USE_TILE_LOCAL
