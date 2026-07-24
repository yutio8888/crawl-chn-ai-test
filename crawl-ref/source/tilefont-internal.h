#pragma once

#ifdef USE_TILE_LOCAL

#include <cstddef>
#include <climits>
#include <cstring>

#include "coord-def.h"
#include "format.h"
#include "unicode.h"

namespace tilefont_internal
{

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
        {
            line_start += newline + 1;
        }
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
