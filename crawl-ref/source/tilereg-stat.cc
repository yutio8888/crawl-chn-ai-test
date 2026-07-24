#include "AppHdr.h"

#ifdef USE_TILE_LOCAL

#include "tilereg-stat.h"

#include "command.h"
#include "database.h"
#include "describe.h"
#include "libutil.h"
#include "macro.h"
#include "status.h"
#include "stringutil.h"
#include "tiles-build-specific.h"

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

    if (event.event != wm_mouse_event::PRESS || event.button != wm_mouse_event::LEFT)
        return 0;

#ifdef __ANDROID__
    if (tiles.is_using_small_layout())
        return command_to_key(CMD_TOGGLE_TAB_ICONS);
#endif

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
        tip = T_("[L-Click] Toggle tab icons");
        return true;
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
