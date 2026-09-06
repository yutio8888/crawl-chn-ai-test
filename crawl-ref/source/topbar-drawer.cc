#include "AppHdr.h"

#ifdef USE_TILE_LOCAL

#include "topbar-drawer.h"

#include "ability.h"
#include "database.h"
#include "describe.h"
#include "env.h"
#include "items.h"
#include "libutil.h"
#include "macro.h"
#include "outer-menu.h"
#include "options.h"
#include "player.h"
#include "prompt.h"
#include "quiver.h"
#include "shout.h"
#include "spl-cast.h"
#include "spl-util.h"
#include "status.h"
#include "stringutil.h"
#include "terrain.h"
#include "tilepick.h"
#include "tiletex.h"
#include "tiles-build-specific.h"
#include "ui.h"
#ifdef __ANDROID__
#include "syscalls.h"
#endif

namespace
{

static const int DRAWER_PADDING = 24;

static shared_ptr<ui::Text> _drawer_text(const formatted_string &content)
{
    auto text = make_shared<ui::Text>(content);
#ifdef __ANDROID__
    // Unlike legacy CRT menus, drawer rows can wrap and scroll at the larger
    // message font size without imposing a fixed-column minimum width.
    text->set_font(tiles.get_msg_font());
    text->set_wrap_text(true);
#endif
    return text;
}

// Android dp expressed in the game's logical coordinate space. Do not resize
// the Surface or change the user's keyboard height to make room for this UI.
static int _menu_dp(int dp)
{
#ifdef __ANDROID__
    const int pixels = (int) ceil(dp * jni_get_display_density());
    return max(1, display_density.apply_game_scale(
        pixels + Options.game_scale - 1));
#else
    return dp;
#endif
}

static bool _negative_status(int status)
{
    if (status < NUM_DURATIONS)
        return duration_negative((duration_type) status);
    // These effects are intrinsically harmful. Mixed-purpose statuses such as
    // terrain, clouds, speed and regeneration deliberately keep their order.
    switch (status)
    {
    case STATUS_BEHELD:
    case STATUS_NET:
    case STATUS_BACKLIT:
    case STATUS_CONSTRICTED:
    case STATUS_LIQUEFIED:
    case STATUS_DRAINED:
    case STATUS_NO_SCROLL:
    case STATUS_RF_ZERO:
    case STATUS_CORROSION:
    case STATUS_NO_POTIONS:
    case STATUS_LOWERED_WL:
    case STATUS_STAT_ZERO:
    case STATUS_CLAUSTROPHOBIA:
    case STATUS_OSTRACISM:
        return true;
    default:
        return false;
    }
}

static string _status_description(const status_info &info)
{
    if (!info.db_key.empty())
    {
        const string description = getLongDescription(info.db_key + " status");
        if (!description.empty())
            return description;
    }

    if (!info.long_text.empty())
        return info.long_text;

    return info.short_text;
}

static string _command_menu_text(const char *context, const char *text)
{
    const string db_key = string(context) + "|" + text;
    string translated = getLongDescription(db_key);
    trim_string_right(translated);
    return translated.empty() ? text : translated;
}

static formatted_string _build_status_text(int selected_status)
{
    formatted_string text(LIGHTGREY);
    bool found_status = false;

    vector<int> statuses;
    for (int status = 0; status <= STATUS_LAST_STATUS; ++status)
    {
        status_info info;
        if (fill_status_info(status, info))
            statuses.push_back(status);
    }
    const auto priority = [selected_status](int status) {
        if (status == selected_status)
            return 0;
        if (_negative_status(status))
            return 1;
        return 2;
    };
    stable_sort(statuses.begin(), statuses.end(), [&](int a, int b) {
        return priority(a) < priority(b);
    });

    for (int status : statuses)
    {
        status_info info;
        if (!fill_status_info(status, info))
            continue;

        const string title = !info.light_text.empty() ? info.light_text
                           : !info.short_text.empty() ? info.short_text
                                                     : info.db_key;
        const string description = _status_description(info);
        if (title.empty() && description.empty())
            continue;

        if (found_status)
            text += "\n\n";

        text.textcolour(info.light_colour ? info.light_colour : LIGHTGREY);
        text += title;
        if (!info.short_text.empty() && info.short_text != title)
        {
            text += "\n";
            text += formatted_string::parse_string(info.short_text, LIGHTGREY);
        }
        if (!description.empty() && description != title
            && description != info.short_text)
        {
            text += "\n";
            text += formatted_string::parse_string(description, LIGHTGREY);
        }
        found_status = true;
    }

    if (!found_status)
        text += T_("no status effects");

    return text;
}

// One tappable entry in a quick-access page. Display strings are owned snapshots;
// the live spell or talent is resolved by enum again when the entry is used, so
// a page can never act on a stale reference.
struct quick_entry
{
    int idx;
    char letter;
    tileidx_t tile;
    string cost;
    bool usable;
    string name;
    string reason;
};

// Memorised spells in the same deterministic letter order the spell tab and
// the "Cast which spell?" prompt use.
static vector<quick_entry> _quick_spell_entries()
{
    vector<quick_entry> entries;

    for (int i = 0; i < 52; ++i)
    {
        const char letter = index_to_letter(i);
        const spell_type spell = get_spell_by_letter(letter);
        if (spell == SPELL_NO_SPELL)
            continue;

        quick_entry entry;
        entry.idx = (int) spell;
        entry.letter = letter;
        entry.tile = tileidx_spell(spell);
        entry.cost = string(T_("MP")) + make_stringf(": %d", spell_mana(spell));
        entry.name = spell_title(spell);
        entry.reason = spell_uselessness_reason(spell, true, true);
        entry.usable = entry.reason.empty();
        entries.push_back(entry);
    }

    return entries;
}

// Talents in the same deterministic order your_talents() hands to the ability
// menu, including currently unusable ones so the page does not reshuffle.
static vector<quick_entry> _quick_ability_entries()
{
    vector<quick_entry> entries;

    for (const talent &tal : your_talents(true))
    {
        quick_entry entry;
        entry.idx = (int) tal.which;
        entry.letter = tal.hotkey;
        entry.tile = tileidx_ability(tal.which);
        entry.cost = make_cost_description(tal.which);
        entry.usable = check_ability_possible(tal.which, true, &entry.reason);
        entry.name = ability_name(tal.which);
        if (!entry.usable && entry.reason.empty())
        {
            entry.reason = _command_menu_text("android command menu summary",
                                              "Unavailable");
        }
        entries.push_back(entry);
    }

    return entries;
}

static string _quick_entry_caption(const quick_entry &entry)
{
    string caption = isaalpha(entry.letter) ? string(1, entry.letter) : "-";
    caption += "  " + entry.cost;
    return caption;
}

class DrawerScroller final : public ui::Scroller
{
public:
    bool on_event(const ui::Event &event) override
    {
        if (_handle_pointer_event(event))
            return true;
        return ui::Scroller::on_event(event);
    }

    // Continue a drag after the pointer has left the panel. The scrim remains
    // the event target there, so it forwards only an already-active gesture.
    bool continue_drag(const ui::Event &event)
    {
        return m_dragging && event.type() != ui::Event::Type::MouseDown
               && _handle_pointer_event(event);
    }

    void cancel_drag()
    {
        m_dragging = false;
    }

private:
    bool _handle_pointer_event(const ui::Event &event)
    {
        switch (event.type())
        {
        case ui::Event::Type::MouseDown:
        {
            const auto &mouse = static_cast<const ui::MouseEvent&>(event);
            if (mouse.button() != ui::MouseEvent::Button::Left)
                return false;
            m_dragging = true;
            m_last_y = mouse.y();
            return true;
        }

        case ui::Event::Type::MouseMove:
        {
            const auto &mouse = static_cast<const ui::MouseEvent&>(event);
            if (!m_dragging)
                return false;

            set_scroll(get_scroll() + m_last_y - mouse.y());
            m_last_y = mouse.y();
            return true;
        }

        case ui::Event::Type::MouseUp:
            if (m_dragging)
            {
                m_dragging = false;
                return true;
            }
            return false;

        default:
            return false;
        }
    }

    bool m_dragging = false;
    int m_last_y = 0;
};

class DrawerPanel final : public ui::Bin
{
public:
    explicit DrawerPanel(shared_ptr<ui::Widget> child,
                         int padding = DRAWER_PADDING, bool command_style = false)
        : m_padding(padding), m_command_style(command_style)
    {
        set_child(std::move(child));
        expand_h = expand_v = true;
    }

    void _render() override
    {
        m_background.draw();
        if (m_child)
            m_child->render();
    }

    ui::SizeReq _get_preferred_size(Direction dim, int prosp_width) override
    {
        if (!m_child)
            return {0, 0};

        const int child_width = dim == VERT
            ? max(0, prosp_width - 2 * m_padding) : -1;
        ui::SizeReq size = m_child->get_preferred_size(dim, child_width);
        size.min += 2 * m_padding;
        size.nat += 2 * m_padding;
        return size;
    }

    void _allocate_region() override
    {
        m_background.clear();
        if (!m_region.empty())
        {
            m_background.add(m_region.x, m_region.y, m_region.ex(),
                             m_region.ey(), m_command_style
                                 ? VColour(18, 20, 25, 255)
                                 : VColour(18, 18, 22, 248));
            m_background.add(m_region.x, m_region.y, m_region.ex(),
                             m_region.y + 3, VColour(125, 98, 60, 255));
        }

        if (!m_child)
            return;

        ui::Region content = m_region;
        content.x += m_padding;
        content.y += m_padding;
        content.width = max(0, content.width - 2 * m_padding);
        content.height = max(0, content.height - 2 * m_padding);
        m_child->allocate_region(content);
    }

    bool on_event(const ui::Event &event) override
    {
        if (ui::Bin::on_event(event))
            return true;

        switch (event.type())
        {
        case ui::Event::Type::MouseDown:
        case ui::Event::Type::MouseUp:
        case ui::Event::Type::MouseMove:
        case ui::Event::Type::MouseWheel:
            return true;
        default:
            return false;
        }
    }

private:
    int m_padding;
    bool m_command_style;
    ShapeBuffer m_background;
};

class DrawerScrim final : public ui::Bin
{
public:
    DrawerScrim(shared_ptr<DrawerPanel> panel,
                shared_ptr<DrawerScroller> scroller = nullptr,
                bool full_height = false)
        : m_scroller(std::move(scroller)), m_full_height(full_height)
    {
        set_child(std::move(panel));
        expand_h = expand_v = true;
    }

    bool close_requested() const
    {
        return m_close_requested;
    }

    void close() { m_close_requested = true; }

    function<bool(int)> navigate;

    void _render() override
    {
        m_scrim.draw();
        if (m_child)
            m_child->render();
    }

    ui::SizeReq _get_preferred_size(Direction, int) override
    {
        return {0, 0};
    }

    void _allocate_region() override
    {
        m_scrim.clear();
        if (!m_region.empty())
        {
            m_scrim.add(m_region.x, m_region.y, m_region.ex(), m_region.ey(),
                        VColour(0, 0, 0, 104));
        }

        if (!m_child)
            return;

        const int panel_height = max(1, m_full_height
            ? m_region.height : m_region.height * 3 / 5);
        m_child->allocate_region({m_region.x, m_region.ey() - panel_height,
                                  m_region.width, panel_height});
    }

    bool on_event(const ui::Event &event) override
    {
        if (event.type() == ui::Event::Type::KeyDown)
        {
            const int key = static_cast<const ui::KeyEvent&>(event).key();
            if (key_is_escape(key))
            {
                m_close_requested = true;
                return true;
            }
            if (navigate && navigate(key))
                return true;
        }

        if (m_scroller && m_scroller->continue_drag(event))
            return true;

        if (event.type() == ui::Event::Type::KeyDown
            && m_scroller
            && m_scroller->on_event(event))
        {
            return true;
        }

        if (event.type() == ui::Event::Type::MouseDown)
        {
            const auto &mouse = static_cast<const ui::MouseEvent&>(event);
            if (mouse.button() == ui::MouseEvent::Button::Left
                && m_child
                && !m_child->get_region().contains_point(mouse.x(), mouse.y()))
            {
                if (m_scroller)
                    m_scroller->cancel_drag();
                m_outside_press = true;
            }
            return true;
        }

        if (event.type() == ui::Event::Type::MouseUp)
        {
            const auto &mouse = static_cast<const ui::MouseEvent&>(event);
            if (mouse.button() == ui::MouseEvent::Button::Left
                && m_outside_press)
            {
                m_close_requested = true;
            }
            m_outside_press = false;
            return true;
        }

        // The modal scrim owns every remaining pointer and key event so none
        // can fall through to the dungeon or other Tiles regions.
        return true;
    }

private:
    shared_ptr<DrawerScroller> m_scroller;
    bool m_full_height;
    ShapeBuffer m_scrim;
    bool m_close_requested = false;
    bool m_outside_press = false;
};

// A quick-access icon button.
//
// The Android touch adapter in SDLActivity.onTouch() sends nothing at
// finger-down; on release it replays the whole gesture as one button, left for
// a short tap and right once the hold reaches its own half-second threshold.
// So the drawer cannot time a press itself, and does not try to: a long press
// simply arrives as the right button, exactly as the spell and ability tile
// regions already treat right-click as "describe".
//
// The right press describes and the right release is swallowed, so a hold
// never also reaches MenuButton, which only ever activates on the left button.
class QuickButton final : public MenuButton
{
public:
    function<void ()> on_describe;
    bool available = true;

    void _allocate_region() override
    {
        MenuButton::_allocate_region();
        m_buf.clear();
        m_line_buf.clear();
        const VColour bg = active ? VColour(67, 59, 43)
            : focused || hovered ? VColour(43, 48, 57)
                                 : VColour(32, 37, 45);
        m_buf.add(m_region.x, m_region.y, m_region.ex(), m_region.ey(), bg);
        if (focused || hovered || active)
        {
            m_line_buf.add_square(m_region.x, m_region.y, m_region.ex()-1,
                                 m_region.ey()-1, VColour(198, 166, 107));
        }
    }

    void _render() override
    {
        MenuButton::_render();
        if (!available)
        {
            ShapeBuffer shade;
            shade.add(m_region.x, m_region.y, m_region.ex(), m_region.ey(),
                      VColour(18, 20, 25, 100));
            shade.draw();
        }
    }

    bool on_event(const ui::Event &event) override
    {
        if (event.type() == ui::Event::Type::MouseDown
            || event.type() == ui::Event::Type::MouseUp)
        {
            const auto &mouse = static_cast<const ui::MouseEvent&>(event);
            if (mouse.button() == ui::MouseEvent::Button::Right)
            {
                if (event.type() == ui::Event::Type::MouseDown && on_describe)
                    on_describe();
                return true;
            }
        }

        return MenuButton::on_event(event);
    }
};

// ui::Image normally repeats a tile at its native size. Menu icons instead
// occupy a fixed square, keeping both small sprites and large ones centred.
class MenuIcon final : public ui::Image
{
public:
    explicit MenuIcon(tileidx_t tile) : ui::Image(tile_def(tile)) {}

    ui::SizeReq _get_preferred_size(Direction, int) override
    {
        return {_menu_dp(24), _menu_dp(24)};
    }

    void _render() override
    {
        if (m_tw <= 0 || m_th <= 0 || m_region.empty())
            return;
        const float scale = min(m_region.width / (float)m_tw,
                                m_region.height / (float)m_th);
        TileBuffer buffer(&tiles.get_image_manager()->get_texture(
            get_tile_texture(m_tile.tile)));
        // The enclosing Scroller owns clipping. Do not reset its scissor here.
        buffer.add(m_tile.tile,
            m_region.x + (m_region.width - m_tw * scale) / 2,
            m_region.y + (m_region.height - m_th * scale) / 2,
            0, 0, false, m_tile.ymax, 1.0f / scale, 1.0f / scale);
        buffer.draw();
    }
};

// Reuse Grid's sizing and clipping. Reflow only the positions: children retain
// their identity, callbacks and focus when the window or font size changes.
class CommandGrid final : public ui::Grid
{
public:
    CommandGrid(int columns, int min_cell_width)
        : m_max_columns(columns), m_min_cell_width(min_cell_width)
    {
        stretch_h = true;
    }

    void append(shared_ptr<ui::Widget> child)
    {
        const int index = m_order.size();
        m_order.push_back(child.get());
        add_child(std::move(child), index % m_columns, index / m_columns);
    }

    ui::SizeReq _get_preferred_size(Direction dim, int width) override
    {
        if (dim == HORZ)
        {
            // The parent is allowed to narrow the grid to a single column.
            return {_menu_dp(48), m_min_cell_width * m_max_columns};
        }
        const int columns = max(1, min(m_max_columns, width / m_min_cell_width));
        if (columns != m_columns)
        {
            m_columns = columns;
            for (auto &child : m_child_info)
            {
                const int index = find(m_order.begin(), m_order.end(),
                                       child.widget.get()) - m_order.begin();
                child.pos.x = index % columns;
                child.pos.y = index / columns;
            }
            m_track_info_dirty = true;
        }
        return ui::Grid::_get_preferred_size(dim, width);
    }

private:
    int m_columns = 1;
    int m_max_columns;
    int m_min_cell_width;
    vector<ui::Widget*> m_order;
};

} // namespace

void show_topbar_status_drawer(int selected_status)
{
    auto text = _drawer_text(_build_status_text(selected_status));
    text->set_wrap_text(true);

    auto scroller = make_shared<DrawerScroller>();
    scroller->set_child(text);
    scroller->set_scrollbar_visible(true);
    scroller->expand_h = scroller->expand_v = true;

    auto panel = make_shared<DrawerPanel>(scroller);
    auto scrim = make_shared<DrawerScrim>(panel, scroller);

    ui::push_layout(scrim);
    while (!scrim->close_requested() && !crawl_state.seen_hups)
        ui::pump_events();
    ui::pop_layout();
    tiles.set_need_redraw();
}

command_type show_topbar_command_menu(bool *acted)
{
    command_type selected_command = CMD_NO_CMD;
    spell_type quick_spell = SPELL_NO_SPELL;
    ability_type quick_ability = ABIL_NON_ABILITY;
    bool done = false;

    vector<shared_ptr<QuickButton>> buttons;
    auto content = make_shared<ui::Box>(ui::Widget::VERT);
    content->set_cross_alignment(ui::Widget::STRETCH);
    auto scroller = make_shared<DrawerScroller>();
    scroller->set_child(content);
    scroller->set_scrollbar_visible(true);
    scroller->expand_h = scroller->expand_v = true;

    auto root = make_shared<ui::Box>(ui::Widget::VERT);
    root->set_cross_alignment(ui::Widget::STRETCH);
    auto header = make_shared<ui::Box>(ui::Widget::HORZ);
    header->set_cross_alignment(ui::Widget::CENTER);
    header->set_margin_for_sdl(0, 0, _menu_dp(8), 0);
    auto heading = make_shared<ui::Box>(ui::Widget::VERT);
    heading->expand_h = true;
    heading->add_child(_drawer_text(formatted_string(
        _command_menu_text("android command menu", "Game menu"), YELLOW)));
    heading->add_child(_drawer_text(formatted_string(
        _command_menu_text("android command menu summary",
                           "Long press for details"), LIGHTGREY)));
    header->add_child(heading);

    auto close = make_shared<QuickButton>();
    auto close_text = _drawer_text(formatted_string(
        _command_menu_text("android command menu", "Close"), WHITE));
    close_text->set_margin_for_sdl(_menu_dp(12));
    close->set_child(close_text);
    close->min_size().width = close->min_size().height = _menu_dp(48);
    header->add_child(close);
    buttons.push_back(close);
    root->add_child(header);
    root->add_child(scroller);

    auto panel = make_shared<DrawerPanel>(root, _menu_dp(12), true);
    auto scrim = make_shared<DrawerScrim>(panel, scroller, true);
    const weak_ptr<DrawerScrim> weak_scrim = scrim;
    close->on_activate_event([weak_scrim](const ui::ActivateEvent&) {
        if (const auto owner = weak_scrim.lock())
            owner->close();
        return true;
    });

    // Commands stay in a stable row-major order inside titled sections,
    // including the unavailable pickup and exit slots. Sections are plain
    // headings in the one scroller; there are no tabs, pages or submenus.
    // Every entry returns its command to the main loop through
    // encode_command_as_key(), which encodes the enum itself, so commands
    // without a default key such as CMD_AUTOFIGHT_NOMOVE work unchanged.
    struct command_entry
    {
        const char *section;
        const char *label;
        tileidx_t tile;
        command_type command;
    };
    const command_entry commands[] = {
        {"Combat and items", "Auto-fight in place", TILEG_CMD_AUTOFIGHT, CMD_AUTOFIGHT_NOMOVE},
        {"Combat and items", "Attack", TILE_WPN_LONG_SWORD, CMD_PRIMARY_ATTACK},
        {"Combat and items", "Fire Item", TILE_MI_STONE, CMD_FIRE_ITEM_NO_QUIVER},
        {"Combat and items", "Quiver", TILE_MI_ARROW, CMD_QUIVER_ITEM},
        {"Combat and items", "Evoke", TILE_WAND_OFFSET, CMD_EVOKE},
        {"Combat and items", "Swap Weapon", TILE_WPN_DAGGER, CMD_WEAPON_SWAP},
        {"Combat and items", "Inventory", TILEG_MENU_INVENTORY, CMD_DISPLAY_INVENTORY},
        {"Combat and items", "Pick Up", TILEG_MENU_PICKUP, CMD_PICKUP},
        {"Combat and items", "Drop", TILEG_CMD_DROP, CMD_DROP},
        {"Combat and items", "Orders", TILEG_ABILITY_BEOGH_RECALL, CMD_SHOUT},
        {"Combat and items", "Spells", TILEG_MENU_SPELLS, CMD_DISPLAY_SPELLS},
        {"Combat and items", "Abilities", TILEG_MENU_ABILITIES, CMD_USE_ABILITY},
        {"Explore and map", "Auto-explore", TILEG_MENU_EXPLORE, CMD_EXPLORE},
        {"Explore and map", "Map", TILEG_MENU_MAP, CMD_DISPLAY_MAP},
        {"Explore and map", "Travel", TILEG_CMD_INTERLEVEL_TRAVEL, CMD_INTERLEVEL_TRAVEL},
        {"Explore and map", "Overview", TILEG_CMD_DISPLAY_OVERMAP, CMD_DISPLAY_OVERMAP},
        {"Explore and map", "Search", TILEG_CMD_SEARCH_STASHES, CMD_SEARCH_STASHES},
        {"Explore and map", "Full View", TILEG_MENU_LOOK, CMD_FULL_VIEW},
        {"Explore and map", "Exit", TILEG_MENU_EXIT, CMD_NO_CMD},
        {"Character and info", "Character", TILEG_MENU_CHARACTER, CMD_RESISTS_SCREEN},
        {"Character and info", "Skills", TILEG_MENU_SKILLS, CMD_DISPLAY_SKILLS},
        {"Character and info", "Religion", TILEG_MENU_RELIGION, CMD_DISPLAY_RELIGION},
        {"Character and info", "Mutations", TILEG_MENU_MUTATIONS, CMD_DISPLAY_MUTATIONS},
        {"Character and info", "Memorise", TILEG_MENU_MEMORISE, CMD_MEMORISE_SPELL},
        {"Character and info", "Known Objects", TILEG_MENU_KNOWN_ITEMS, CMD_DISPLAY_KNOWN_OBJECTS},
        {"Character and info", "Messages", TILEG_CMD_REPLAY_MESSAGES, CMD_REPLAY_MESSAGES},
        {"Character and info", "Gold", TILEG_ABILITY_ZIN_DONATE_GOLD, CMD_LIST_GOLD},
        {"System", "Commands", TILEG_MENU_HELP, CMD_DISPLAY_COMMANDS},
        {"System", "System Menu", TILEG_CMD_GAME_MENU, CMD_GAME_MENU},
    };

    // Keep enough width for two lines at the chosen game font size. Increasing
    // the font can reduce the column count; it must never shrink the font.
    const int min_command_width = max(_menu_dp(96),
        (int)tiles.get_msg_font()->char_height() * 4 + _menu_dp(16));
    // One grid per section, created when the table reaches a new heading.
    const char *current_section = nullptr;
    shared_ptr<CommandGrid> command_grid;

    const weak_ptr<DrawerScroller> weak_scroller = scroller;
    const auto describe = [weak_scroller](const string &label, const string &body) {
        // Command hints use the same readable font as the panel; the generic
        // CRT description popup is too small on a high-density phone.
        auto details = make_shared<ui::Box>(ui::Widget::VERT);
        details->set_cross_alignment(ui::Widget::STRETCH);
        details->max_size().width = _menu_dp(320);
        auto title = _drawer_text(formatted_string(label, YELLOW));
        title->set_margin_for_sdl(0, 0, _menu_dp(8), 0);
        details->add_child(title);
        auto detail_scroll = make_shared<DrawerScroller>();
        detail_scroll->set_child(_drawer_text(
            formatted_string::parse_string(body, LIGHTGREY)));
        details->add_child(detail_scroll);
        bool dismissed = false;
        auto dismiss = make_shared<QuickButton>();
        auto text = _drawer_text(formatted_string(
            _command_menu_text("android command menu", "Close"), WHITE));
        text->set_margin_for_sdl(_menu_dp(12));
        dismiss->set_child(text);
        dismiss->min_size().height = _menu_dp(48);
        dismiss->set_margin_for_sdl(_menu_dp(12), 0, 0, 0);
        dismiss->on_activate_event([&dismissed](const ui::ActivateEvent&) {
            dismissed = true;
            return true;
        });
        details->add_child(dismiss);
        auto popup = make_shared<ui::Popup>(details);
        const auto detail_key = [&dismissed, detail_scroll](const ui::KeyEvent &event) {
            if (ui::key_exits_popup(event.key(), true))
            {
                dismissed = true;
                return true;
            }
            const int key = numpad_to_regular(event.key(), true);
            return key == CK_UP || key == CK_DOWN || key == CK_PGUP
                || key == CK_PGDN || key == CK_HOME || key == CK_END
                ? detail_scroll->on_event(event) : false;
        };
        // Handle Escape on the focus target before UIRoot's focus-reset rule.
        dismiss->on_keydown_event(detail_key);
        popup->on_keydown_event(detail_key);
        ui::run_layout(popup, dismissed, dismiss);
        if (const auto owner = weak_scroller.lock())
            owner->cancel_drag();
    };
    for (const auto &entry : commands)
    {
        if (!current_section || strcmp(current_section, entry.section) != 0)
        {
            current_section = entry.section;
            auto section = _drawer_text(formatted_string(
                _command_menu_text("android command menu", entry.section),
                YELLOW));
            section->set_margin_for_sdl(_menu_dp(12), _menu_dp(4), _menu_dp(4),
                                        _menu_dp(4));
            content->add_child(section);
            command_grid = make_shared<CommandGrid>(3, min_command_width);
            content->add_child(command_grid);
        }
        const char *label_key = entry.label;
        const char *summary_key = label_key;
        command_type command = entry.command;
        bool available = true;
        string unavailable_reason;
        if (command == CMD_QUIVER_ITEM && !quiver::anything_to_quiver())
        {
            available = false;
            unavailable_reason = T_("You have nothing to quiver.");
        }
        else if (command == CMD_SHOUT && you.cannot_speak()
                 && !have_allies_to_order())
        {
            available = false;
            unavailable_reason = T_("You cannot shout and have no allies to order.");
        }
        if (command == CMD_PICKUP && you.visible_igrd(you.pos()) == NON_ITEM)
        {
            available = false;
            summary_key = "No items here";
        }
        else if (command == CMD_NO_CMD)
        {
            const dungeon_feature_type feature = env.grid(you.pos());
            command = feat_stair_direction(feature);
            if (command == CMD_NO_CMD || feat_is_altar(feature))
            {
                command = CMD_NO_CMD;
                available = false;
                summary_key = "No exit here";
            }
            else
            {
                label_key = feature == DNGN_ENTER_SHOP ? "Enter Shop"
                          : feat_is_gate(feature) ? "Enter"
                          : command == CMD_GO_UPSTAIRS ? "Go Upstairs"
                                                      : "Go Downstairs";
                summary_key = label_key;
            }
        }
        const string label = _command_menu_text("android command menu", label_key);
        const string summary = unavailable_reason.empty()
            ? _command_menu_text("android command menu summary", summary_key)
            : unavailable_reason;
        auto cell = make_shared<ui::Box>(ui::Widget::VERT);
        cell->set_cross_alignment(ui::Widget::CENTER);
        cell->set_main_alignment(ui::Widget::CENTER);
        cell->set_margin_for_sdl(_menu_dp(6), _menu_dp(4));
        auto icon = make_shared<MenuIcon>(entry.tile);
        icon->set_margin_for_sdl(0, 0, _menu_dp(4), 0);
        cell->add_child(icon);
        cell->add_child(_drawer_text(formatted_string(label,
                                                     available ? WHITE : LIGHTGREY)));
        auto button = make_shared<QuickButton>();
        button->available = available;
        button->set_child(cell);
        button->min_size().height = _menu_dp(64);
        button->set_margin_for_sdl(_menu_dp(4));
        button->on_describe = [describe, label, summary]() {
            describe(label, summary);
        };
        button->on_activate_event(
            [&, command, available, describe, label, summary](const ui::ActivateEvent&) {
                if (!available)
                    describe(label, summary);
                else
                {
                    selected_command = command;
                    done = true;
                }
                return true;
            });
        buttons.push_back(button);
        command_grid->append(button);
    }

    const auto add_quick_section = [&](const vector<quick_entry> &entries,
                                        const char *title_key, bool is_spell) {
        if (entries.empty())
            return;
        auto title = _drawer_text(formatted_string(
            _command_menu_text("android command menu", title_key), YELLOW));
        title->set_margin_for_sdl(_menu_dp(12), _menu_dp(4), _menu_dp(4),
                                 _menu_dp(4));
        content->add_child(title);
        auto grid = make_shared<CommandGrid>(2, max(_menu_dp(150),
            (int)tiles.get_msg_font()->char_height() * 6 + _menu_dp(40)));
        content->add_child(grid);
        for (const quick_entry &entry : entries)
        {
            auto row = make_shared<ui::Box>(ui::Widget::HORZ);
            row->set_cross_alignment(ui::Widget::CENTER);
            row->set_margin_for_sdl(_menu_dp(8));
            auto icon = make_shared<MenuIcon>(entry.tile);
            icon->set_margin_for_sdl(0, _menu_dp(8), 0, 0);
            row->add_child(icon);
            auto labels = make_shared<ui::Box>(ui::Widget::VERT);
            labels->set_cross_alignment(ui::Widget::STRETCH);
            labels->expand_h = true;
            labels->add_child(_drawer_text(formatted_string(
                entry.name, entry.usable ? WHITE : LIGHTGREY)));
            labels->add_child(_drawer_text(formatted_string(
                _quick_entry_caption(entry), LIGHTGREY)));
            if (!entry.reason.empty())
            {
                labels->add_child(_drawer_text(formatted_string(
                    entry.reason, LIGHTGREY)));
            }
            row->add_child(labels);

            auto button = make_shared<QuickButton>();
            button->available = entry.usable;
            button->set_child(row);
            button->min_size().height = _menu_dp(64);
            button->set_margin_for_sdl(_menu_dp(4));
            const int idx = entry.idx;
            const bool usable = entry.usable;
            const string name = entry.name, reason = entry.reason;
            button->on_activate_event(
                [&, idx, is_spell, usable, name, reason, describe](const ui::ActivateEvent&) {
                    if (!usable)
                        describe(name, reason);
                    else
                    {
                        if (is_spell)
                            quick_spell = (spell_type)idx;
                        else
                            quick_ability = (ability_type)idx;
                        done = true;
                    }
                    return true;
                });
            button->on_describe = [weak_scroller, idx, is_spell]() {
                if (is_spell)
                    describe_spell((spell_type)idx);
                else
                    describe_ability((ability_type)idx);
                if (const auto owner = weak_scroller.lock())
                    owner->cancel_drag();
            };
            buttons.push_back(button);
            grid->append(button);
        }
    };
    add_quick_section(_quick_spell_entries(), "Quick Cast", true);
    add_quick_section(_quick_ability_entries(), "Quick Abilities", false);

    // Spatial navigation uses the allocated geometry, so the same logic works
    // after a three-to-two-column reflow and between sections of different width.
    scrim->navigate = [&, scroller](int raw_key) {
        const int key = numpad_to_regular(raw_key, true);
        const bool horizontal = key == CK_LEFT || key == CK_RIGHT;
        if (!horizontal && key != CK_UP && key != CK_DOWN
            && key != CK_HOME && key != CK_END && key != CK_TAB)
        {
            return false;
        }
        const auto current = ui::get_focused_widget();
        auto found = find_if(buttons.begin(), buttons.end(),
            [current](const shared_ptr<QuickButton> &b) { return b.get() == current; });
        auto target = buttons.front();
        if (key == CK_HOME)
            target = buttons[1];
        else if (key == CK_END)
            target = buttons.back();
        else if (key == CK_TAB || found == buttons.end())
            target = found == buttons.end() || found + 1 == buttons.end()
                ? buttons.front() : *(found + 1);
        else
        {
            const auto from = (*found)->get_region();
            int best = INT_MAX;
            target = *found;
            for (const auto &button : buttons)
            {
                if (button.get() == current)
                    continue;
                const auto to = button->get_region();
                const int dx = to.x + to.width/2 - from.x - from.width/2;
                const int dy = to.y + to.height/2 - from.y - from.height/2;
                if ((key == CK_LEFT && dx >= 0) || (key == CK_RIGHT && dx <= 0)
                    || (key == CK_UP && dy >= 0) || (key == CK_DOWN && dy <= 0))
                {
                    continue;
                }
                if (horizontal && abs(dy) > min(from.height, to.height)/2)
                    continue;
                const int score = horizontal ? abs(dx) + abs(dy)*1000
                                             : abs(dy)*1000 + abs(dx);
                if (score < best)
                {
                    best = score;
                    target = button;
                }
            }
        }
        ui::set_focused_widget(target.get());
        if (target != close)
        {
            const auto item = target->get_region();
            const auto viewport = scroller->get_region();
            const int padding = _menu_dp(4);
            if (item.y < viewport.y + padding)
            {
                scroller->set_scroll(scroller->get_scroll()
                                     + item.y - viewport.y - padding);
            }
            else if (item.ey() > viewport.ey() - padding)
                scroller->set_scroll(scroller->get_scroll()
                                     + item.ey() - viewport.ey() + padding);
        }
        return true;
    };
    for (const auto &button : buttons)
    {
        button->on_keydown_event([weak_scrim](const ui::KeyEvent &event) {
            if (const auto owner = weak_scrim.lock())
            {
                if (key_is_escape(event.key()))
                {
                    owner->close();
                    return true;
                }
                if (owner->navigate)
                    return owner->navigate(event.key());
            }
            return false;
        });
    }

    ui::push_layout(scrim);
    ui::set_focused_widget(buttons[1].get());
    while (!done && !scrim->close_requested() && !crawl_state.seen_hups)
        ui::pump_events();
    ui::pop_layout();
    tiles.set_need_redraw();

    if (acted)
        *acted = false;

    // A quick-access pick runs only once the drawer has closed, through the
    // same calls the z and a commands reach after their own selection step, so
    // range checks, confirmations, costs, failures, messages and turn use are
    // unchanged. Only the enum was carried out of the page, and the talent
    // behind an ability is looked up again here, so nothing stale is used.
    if (quick_spell != SPELL_NO_SPELL)
    {
        if (acted)
            *acted = true;
        if (cast_a_spell(true, quick_spell) == spret::abort)
            flush_input_buffer(FLUSH_ON_FAILURE);
        return CMD_NO_CMD;
    }

    if (quick_ability != ABIL_NON_ABILITY)
    {
        if (acted)
            *acted = true;
        const talent tal = get_talent(quick_ability);
        if (tal.which == ABIL_NON_ABILITY || !activate_talent(tal))
            flush_input_buffer(FLUSH_ON_FAILURE);
        return CMD_NO_CMD;
    }

    return selected_command;
}

#endif
