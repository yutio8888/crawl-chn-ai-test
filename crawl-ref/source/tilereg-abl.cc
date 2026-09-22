#include "AppHdr.h"
#include "database.h"
#ifdef USE_TILE_LOCAL
#include "tilereg-abl.h"
#include "ability.h"
#include "cio.h"
#include "describe.h"
#include "libutil.h"
#include "macro.h"
#include "message.h"
#include "output.h"
#include "stringutil.h"
#include "tile-inventory-flags.h"
#include "rltiles/tiledef-icons.h"
#include "tilepick.h"
#include "tiles-build-specific.h"
#include "tilereg-cmd.h"
#include "topbar-drawer.h"
#include "tilefont.h"
#include "rltiles/tiledef-gui.h"
AbilityRegion::AbilityRegion(const TileRegionInit &init, bool quick_access)
    : GridRegion(init), m_quick_access(quick_access)
{
}
// A category icon with a visible plus denotes access to the complete list.
// Draw the label at the reading font size, independently of tile scaling.
void AbilityRegion::render()
{
    GridRegion::render();
    if (!m_quick_access || mx <= 0 || m_items.empty() || m_items.back().idx != -1)
        return;
    const int index = m_items.size() - 1;
    auto* font = tiles.get_msg_font();
    font->render_string(sx + ox + (index % mx + 1) * dx - font->char_width(),
                        sy + oy + (index / mx + 1) * dy - font->char_height(),
                        formatted_string("+", YELLOW));
}
void AbilityRegion::activate()
{
    if (your_talents(true).size() == 0)
    {
        no_ability_msg();
        flush_prev_message();
    }
}
void AbilityRegion::draw_tag()
{
    if (m_cursor == NO_CURSOR)
        return;
    int curs_index = cursor_index();
    if (curs_index >= (int)m_items.size())
        return;
    int idx = m_items[curs_index].idx;
    if (idx == -1)
    {
        if (m_quick_access)
            draw_desc(T_("All abilities"));
        return;
    }
    const ability_type ability = (ability_type) idx;
    const string failure = failure_rate_to_string(get_talent(ability).fail);
    string desc = make_stringf("%s    (%s)",
                               ability_name(ability).c_str(), failure.c_str());
    draw_desc(desc.c_str());
}
int AbilityRegion::handle_mouse(wm_mouse_event &event)
{
    unsigned int item_idx = UINT_MAX;
    const bool selected = place_cursor(event, item_idx);
    // GridRegion marks idx=-1 as empty, but sets item_idx only for a valid
    // command-mode press. Intercept our overflow before any spell/talent API.
    if (m_quick_access && item_idx < m_items.size() && m_items[item_idx].idx == -1)
    {
        if (event.button != wm_mouse_event::LEFT && event.button != wm_mouse_event::RIGHT)
            return 0;
        show_topbar_command_menu(nullptr, CommandMenuSection::ABILITIES);
        return CK_MOUSE_CMD;
    }
    if (!selected || tile_command_not_applicable(CMD_USE_ABILITY, true))
        return 0;
    const ability_type ability = (ability_type) m_items[item_idx].idx;
    if (event.button == wm_mouse_event::LEFT)
    {
        m_last_clicked_item = item_idx;
        tiles.set_need_redraw();
        talent tal = get_talent(ability);
        if (tal.which == ABIL_NON_ABILITY || !activate_talent(tal))
            flush_input_buffer(FLUSH_ON_FAILURE);
        return CK_MOUSE_CMD;
    }
    else if (ability != NUM_ABILITIES && event.button == wm_mouse_event::RIGHT)
    {
        describe_ability(ability);
        redraw_screen();
        update_screen();
        return CK_MOUSE_CMD;
    }
    return 0;
}
bool AbilityRegion::update_tab_tip_text(string &tip, bool active)
{
    const string prefix1 = active ? "" : string(T_("[L-Click]")) + " ";
    const char *prefix2 = active ? "" : "          ";
    tip = make_stringf("%s%s\n%s%s",
                       prefix1.c_str(), T_("Display abilities"),
                       prefix2, T_("Use abilities"));
    return true;
}
bool AbilityRegion::update_tip_text(string& tip)
{
    if (m_cursor == NO_CURSOR)
        return false;
    unsigned int item_idx = cursor_index();
    if (item_idx >= m_items.size())
        return false;
    if (m_items[item_idx].idx == -1)
    {
        if (!m_quick_access)
            return false;
        tip = T_("All abilities");
        return true;
    }
    int flag = m_items[item_idx].flag;
    vector<command_type> cmd;
    if (flag & TILEI_FLAG_INVALID)
        tip = T_("You cannot use this ability right now.");
    else
    {
        tip = T_("[L-Click] Use (%)");
        cmd.push_back(CMD_USE_ABILITY);
    }
    tip += T_("\n[R-Click] Describe");
    insert_commands(tip, cmd);
    return true;
}
bool AbilityRegion::update_alt_text(string &alt)
{
    if (m_cursor == NO_CURSOR)
        return false;
    unsigned int item_idx = cursor_index();
    if (item_idx >= m_items.size())
        return false;
    if (m_items[item_idx].idx == -1)
    {
        if (!m_quick_access)
            return false;
        alt = T_("All abilities");
        return true;
    }
    if (m_last_clicked_item >= 0
        && item_idx == (unsigned int) m_last_clicked_item)
    {
        return false;
    }
    int idx = m_items[item_idx].idx;
    const ability_type ability = (ability_type) idx;
    describe_info inf;
    inf.body << get_ability_desc(ability);
    alt = process_description(inf);
    return true;
}
int AbilityRegion::get_max_slots()
{
    const int MAX_INTRINSICS = 3;
    const int MAX_GOD_ABILS = 6;
    const int MAX_EVOKES = 6; // TODO: don't hardcode this
    return MAX_INTRINSICS + MAX_GOD_ABILS + MAX_EVOKES;
}
void AbilityRegion::pack_buffers()
{
    if (m_items.size() == 0)
        return;
    int i = 0;
    for (int y = 0; y < my; y++)
    {
        if (i >= (int)m_items.size())
            break;
        for (int x = 0; x < mx; x++)
        {
            if (i >= (int)m_items.size())
                break;
            InventoryTile &item = m_items[i++];
            if (item.flag & TILEI_FLAG_INVALID)
                m_buf.add_icons_tile(TILEI_MESH, x, y);
            if (item.flag & TILEI_FLAG_CURSOR)
                m_buf.add_icons_tile(TILEI_CURSOR, x, y);
            if (item.quantity > 0) // mp cost
                draw_number(x, y, item.quantity);
            if (item.tile)
                m_buf.add_spell_tile(item.tile, x, y);
        }
    }
}
static InventoryTile _tile_for_ability(ability_type ability)
{
    InventoryTile desc;
    desc.tile     = tileidx_ability(ability);
    desc.idx      = (int) ability;
    desc.quantity = ability_mp_cost(ability);
    if (tile_command_not_applicable(CMD_USE_ABILITY, true)
        || !check_ability_possible(ability, true))
    {
        desc.flag |= TILEI_FLAG_INVALID;
    }
    return desc;
}
void AbilityRegion::update()
{
    m_items.clear();
    m_dirty = true;
    if (mx * my == 0)
        return;
    const vector<talent> talents = your_talents(true);
    const bool overflow = m_quick_access && (int)talents.size() > mx*my;
    const unsigned int max_abilities = m_quick_access
        ? mx*my - (overflow ? 1 : 0) : min(get_max_slots(), mx*my);
    // Keep the sidebar's existing non-invocation-before-invocation order.
    // Collect identities first so a zero-capacity real list still gets More.
    vector<ability_type> ordered;
    for (const auto& talent : talents)
        if (!talent.is_invocation)
            ordered.push_back(talent.which);
    for (const auto& talent : talents)
        if (talent.is_invocation)
            ordered.push_back(talent.which);
    for (auto ability : ordered)
    {
        if (m_items.size() >= max_abilities)
            break;
        m_items.push_back(_tile_for_ability(ability));
    }
    if (overflow)
    {
        InventoryTile more;
        more.tile = TILEG_MENU_ABILITIES;
        m_items.push_back(more);
    }
}
#endif
