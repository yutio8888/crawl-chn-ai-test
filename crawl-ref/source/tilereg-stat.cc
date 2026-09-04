#include "AppHdr.h"

#ifdef USE_TILE_LOCAL

#include "tilereg-stat.h"

#include "command.h"
#include "database.h"
#include "describe.h"
#include "glwrapper.h"
#include "libutil.h"
#include "macro.h"
#include "status.h"
#include "stringutil.h"
#include "tiles-build-specific.h"
#include "tilefont.h"
#include "topbar-drawer.h"

// Per-frame hitbox registry populated by output.cc::_print_status_lights()
// and consumed by StatRegion::update_tip_text().
static vector<status_hitbox> _status_hitboxes;

void clear_status_hitboxes()
{
    _status_hitboxes.clear();
}

void record_status_hitbox(int status, int x1, int x2, int y)
{
    _status_hitboxes.push_back({status, x1, x2, y});
}

const vector<status_hitbox>& get_status_hitboxes()
{
    return _status_hitboxes;
}

StatRegion::StatRegion(FontWrapper *font_arg) : TextRegion(font_arg)
{
}

bool StatRegion::_text_mouse_pos(int mouse_x, int mouse_y, int &cx, int &cy)
{
    int x = mouse_x - ox - sx;
    int y = mouse_y - oy - sy;
    if (x < 0 || y < 0)
        return false;

    const int cell_width = max(1U, font().char_width(false));
    const int cell_height = max(1U, font().char_height(false));
    cx = glmanager->logical_to_device(x) / cell_width;
    cy = (glmanager->logical_to_device(y) + cell_height / 2) / cell_height;
    return cx < mx && cy < my;
}

int StatRegion::handle_mouse(wm_mouse_event &event)
{
    if (mouse_control::current_mode() != MOUSE_MODE_COMMAND)
        return 0;

    if (!inside(event.px, event.py))
        return 0;

    // Cache mouse position so update_tip_text() can do per-status lookup.
    m_last_mouse_x = event.px;
    m_last_mouse_y = event.py;

    if (event.event == wm_mouse_event::MOVE)
        return 0; // don't consume move events

#ifdef __ANDROID__
    if (tiles.is_using_small_layout())
    {
        if (event.event != wm_mouse_event::PRESS
            || event.button != wm_mouse_event::LEFT)
        {
            return 0;
        }

        int cx, cy;
        if (!_text_mouse_pos(event.px, event.py, cx, cy))
            return 0;

        for (const auto &hitbox : _status_hitboxes)
        {
            if (cy == hitbox.y && cx >= hitbox.x1 && cx <= hitbox.x2)
            {
                show_topbar_status_drawer();
                return CK_NO_KEY;
            }
        }

        bool acted = false;
        const command_type command = show_topbar_command_menu(&acted);
        if (command == CMD_NO_CMD)
            return acted ? CK_MOUSE_CMD : 0;
        return encode_command_as_key(command);
    }
#endif

    if (event.event != wm_mouse_event::PRESS
        || event.button != wm_mouse_event::LEFT)
    {
        return 0;
    }

    // clicking on stats should show all the stats
    return encode_command_as_key(CMD_RESISTS_SCREEN);
}

bool StatRegion::update_tip_text(string& tip)
{
    if (mouse_control::current_mode() != MOUSE_MODE_COMMAND)
        return false;

#ifdef __ANDROID__
    if (tiles.is_using_small_layout())
    {
        int cx, cy;
        if (!_text_mouse_pos(m_last_mouse_x, m_last_mouse_y, cx, cy))
            return false;

        for (const auto &hitbox : _status_hitboxes)
        {
            if (cy == hitbox.y && cx >= hitbox.x1 && cx <= hitbox.x2)
            {
                tip = T_("[L-Click] Show player information");
                return true;
            }
        }
        return false;
    }
#endif

    // Small layout uses abbreviated status text — per-status tooltips
    // would be unreliable, so keep the generic fallback.
    if (tiles.is_using_small_layout())
    {
        tip = T_("[L-Click] Show player information");
        return true;
    }

    int cx, cy;
    if (!mouse_pos(m_last_mouse_x, m_last_mouse_y, cx, cy))
    {
        tip = T_("[L-Click] Show player information");
        return true;
    }

    for (const auto &hb : _status_hitboxes)
    {
        if (cy == hb.y && cx >= hb.x1 && cx <= hb.x2 && hb.status >= 0)
        {
            status_info inf;
            if (!fill_status_info(hb.status, inf))
                continue;

            // Priority: dynamic long_text > database lookup > short_text
            if (!inf.long_text.empty())
            {
                tip = inf.long_text;
                return true;
            }

            // Use db_key for stable English TextDB lookup
            if (!inf.db_key.empty())
            {
                tip = getLongDescription(inf.db_key + " status");
                if (!tip.empty())
                    return true;
            }

            if (!inf.short_text.empty())
            {
                tip = inf.short_text;
                return true;
            }

            // A cached hitbox can outlive a dynamic status (for example a
            // channelled spell). Never claim a tooltip when all texts are empty.
            if (!inf.light_text.empty())
            {
                tip = inf.light_text;
                return true;
            }
            continue;
        }
    }

    tip = T_("[L-Click] Show player information");
    return true;
}

void StatRegion::_clear_buffers()
{
    m_shape_buf.clear();
}

void StatRegion::render()
{
    if (tiles.is_using_small_layout())
    {
        _clear_buffers();
        // black-out part of screen that stats are written on to
        //  - double up area to cover behind where tabs are drawn
        m_shape_buf.add(sx,sy,ex+(ex-sx),ey,VColour(0,0,0,255));
        // DungeonRegion leaves its tile transform active. Draw this backing
        // rectangle in screen coordinates so it cannot cover the map.
        glmanager->reset_transform();
        m_shape_buf.draw();
    }
    TextRegion::render();
}

void StatRegion::clear()
{
    _clear_buffers();
    TextRegion::clear();
}

#endif
