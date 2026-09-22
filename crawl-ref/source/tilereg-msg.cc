#include "AppHdr.h"

#ifdef USE_TILE_LOCAL

#include "tilereg-msg.h"

#include "command.h"
#include "libutil.h"
#include "format.h"
#include "macro.h"
#include "options.h"
#include "syscalls.h"
#include "tilebuf.h"
#include "tilefont.h"
#include "tiles-build-specific.h"
#include "stringutil.h"

MessageRegion::MessageRegion(FontWrapper *font_arg) :
    TextRegion(font_arg),
    m_overlay(false)
{
}

int MessageRegion::handle_mouse(wm_mouse_event &event)
{
    coord_def start, end;
    formatted_string label;
    if (history_button_bounds(start, end, label)
        && event.px >= start.x && event.px < end.x
        && event.py >= start.y && event.py < end.y)
    {
        // The overlay receives events before the dungeon. Consume every event
        // in this visible button so a tap cannot also move the player.
        return event.event == wm_mouse_event::PRESS
               && event.button == wm_mouse_event::LEFT
               ? encode_command_as_key(CMD_REPLAY_MESSAGES) : CK_NO_KEY;
    }

    if (m_overlay)
        return 0;

    // TODO enne - mouse scrolling here should mouse scroll up through
    // the message history in the message pane, without going to the CRT.

    if (!inside(event.px, event.py))
        return 0;

    if (event.event != wm_mouse_event::PRESS || event.button != wm_mouse_event::LEFT)
        return 0;

    if (mouse_control::current_mode() != MOUSE_MODE_COMMAND)
        return 0;

    return encode_command_as_key(CMD_REPLAY_MESSAGES);
}

bool MessageRegion::history_button_bounds(coord_def &start, coord_def &end,
                                         formatted_string &label) const
{
#ifdef __ANDROID__
    if (!m_overlay || !tiles.is_using_small_layout() || mx <= 0 || my <= 0
        || mouse_control::current_mode() != MOUSE_MODE_COMMAND)
    {
        return false;
    }

    const int pixels = static_cast<int>(ceil(48 * jni_get_display_density()));
    const int touch = max(1, display_density.apply_game_scale(
                                pixels + Options.game_scale - 1));
    const int padding = max(2, static_cast<int>(m_font->char_height()) / 4);
    const int available = ex - sx;
    if (available < touch || available <= 2 * padding || sy < touch
        || sy - 2 * padding < static_cast<int>(m_font->char_height()))
    {
        return false;
    }

    label = m_font->split(formatted_string::parse_string(T_("Message history")),
                         available - 2 * padding, sy - 2 * padding);
    if (label.empty())
        return false;
    const int label_width = m_font->string_width(label) + 2 * padding;
    const int label_height = m_font->string_height(label) + 2 * padding;
    if (label_width > available || label_height > sy)
        return false;
    const int width = min(available, max(touch,
                                       label_width));
    const int height = max(touch, label_height);
    start = coord_def(ex - width, sy - height);
    end = coord_def(ex, sy);
    return true;
#else
    return false;
#endif
}

bool MessageRegion::update_tip_text(string& tip)
{
    if (mouse_control::current_mode() != MOUSE_MODE_COMMAND)
        return false;

    tip = T_("[L-Click] Browse message history");
    return true;
}

void MessageRegion::set_overlay(bool is_overlay, const VColour &col)
{
    m_overlay = is_overlay;
    m_overlay_col = col;
}

void MessageRegion::render()
{
#ifdef DEBUG_TILES_REDRAW
    cprintf("rendering MessageRegion\n");
#endif
    int idx = -1;
    char32_t char_back = 0;
    uint8_t col_back = 0;

    if (!m_overlay && !m_alt_text.empty())
    {
        coord_def min_pos(sx, sy);
        coord_def max_pos(ex, ey);
        // these hover strings never use the last line
        formatted_string text = m_font->split(formatted_string::parse_string(m_alt_text),
                ex-sx-2*ox, ey-sy-2*oy-m_font->char_height());
        if (ends_with(text, ".."))
            text = text.substr_bytes(0, text.tostring().find_last_of('\n')) + "\n...";

        m_font->render_string(sx + ox, sy + oy, text);
        return;
    }

    if (this == TextRegion::cursor_region && cursor_x > 0 && cursor_y > 0)
    {
        idx = cursor_x + mx * cursor_y;
        char_back = cbuf[idx];
        col_back  = abuf[idx];

        cbuf[idx] = '_';
        abuf[idx] = WHITE;
    }

    if (m_overlay)
    {
        int height;
        bool found = false;
        for (height = my; height > 0; height--)
        {
            char32_t *buf = &cbuf[mx * (height - 1)];
            for (int x = 0; x < mx; x++)
            {
                if (buf[x] != ' ')
                {
                    found = true;
                    break;
                }
            }

            if (found)
                break;
        }

        if (height > 0)
        {
            height *= m_font->char_height();

            glmanager->reset_transform();

            ShapeBuffer buff;
            buff.add(sx, sy, ex, sy + height, m_overlay_col);
            buff.draw();
        }
    }

    m_font->render_textblock(sx + ox, sy + oy, cbuf, abuf, mx, my, m_overlay);

    if (idx >= 0)
    {
        cbuf[idx] = char_back;
        abuf[idx] = col_back;
    }

    coord_def start, end;
    formatted_string label;
    if (history_button_bounds(start, end, label))
    {
        glmanager->reset_transform();
        ShapeBuffer button;
        button.add(start.x, start.y, end.x, end.y, VColour(40, 55, 70, 255));
        button.draw();
        const int x = start.x + (end.x - start.x - m_font->string_width(label)) / 2;
        const int y = start.y + (end.y - start.y - m_font->string_height(label)) / 2;
        m_font->render_string(x, y, label);
    }
}

#endif
