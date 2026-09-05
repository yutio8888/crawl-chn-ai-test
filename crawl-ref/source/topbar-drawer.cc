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
#include "spl-cast.h"
#include "spl-util.h"
#include "status.h"
#include "stringutil.h"
#include "terrain.h"
#include "tilepick.h"
#include "tiles-build-specific.h"
#include "ui.h"
#ifdef __ANDROID__
#include "syscalls.h"
#endif

namespace
{

static const int DRAWER_PADDING = 24;
static const int COMMAND_MENU_ITEM_HEIGHT = 72;
static const int COMMAND_MENU_ITEM_PADDING = 12;
static const int COMMAND_MENU_ICON_GAP = 16;
static const int QUICK_ICON_PAGE_SIZE = 12;

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

static int _command_item_height()
{
#ifdef __ANDROID__
    const int pixels = (int) ceil(48 * jni_get_display_density());
    return max(COMMAND_MENU_ITEM_HEIGHT,
               display_density.apply_game_scale(pixels + Options.game_scale - 1));
#else
    return COMMAND_MENU_ITEM_HEIGHT;
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
        entry.usable = check_ability_possible(tal.which, true);
        entry.name = ability_name(tal.which);
        if (!entry.usable)
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
            {
#ifdef __ANDROID__
                // SDL's Android touch adapter emits Move/Up, but no Down, for
                // a single-finger swipe. Treat the first in-panel move as the
                // drag origin; taps still arrive as Down/Up at release time.
                m_dragging = true;
                m_last_y = mouse.y();
                return true;
#else
                return false;
#endif
            }

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
    explicit DrawerPanel(shared_ptr<ui::Widget> child)
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
            ? max(0, prosp_width - 2 * DRAWER_PADDING) : -1;
        ui::SizeReq size = m_child->get_preferred_size(dim, child_width);
        size.min += 2 * DRAWER_PADDING;
        size.nat += 2 * DRAWER_PADDING;
        return size;
    }

    void _allocate_region() override
    {
        m_background.clear();
        if (!m_region.empty())
        {
            m_background.add(m_region.x, m_region.y, m_region.ex(),
                             m_region.ey(), VColour(18, 18, 22, 248));
            m_background.add(m_region.x, m_region.y, m_region.ex(),
                             m_region.y + 3, VColour(125, 98, 60, 255));
        }

        if (!m_child)
            return;

        ui::Region content = m_region;
        content.x += DRAWER_PADDING;
        content.y += DRAWER_PADDING;
        content.width = max(0, content.width - 2 * DRAWER_PADDING);
        content.height = max(0, content.height - 2 * DRAWER_PADDING);
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
    ShapeBuffer m_background;
};

class DrawerScrim final : public ui::Bin
{
public:
    DrawerScrim(shared_ptr<DrawerPanel> panel,
                shared_ptr<DrawerScroller> scroller = nullptr)
        : m_scroller(std::move(scroller))
    {
        set_child(std::move(panel));
        expand_h = expand_v = true;
    }

    bool close_requested() const
    {
        return m_close_requested;
    }

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

        const int panel_height = max(1, m_region.height * 3 / 5);
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

// The parts of a built quick-access page the drawer has to wire up afterwards.
struct quick_page_refs
{
    shared_ptr<MenuButton> back;
    shared_ptr<MenuButton> focus;
    int index = -1;
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

    vector<shared_ptr<MenuButton>> buttons;
    const auto make_button = [&buttons](string label, string summary,
                                        tileidx_t tile) {
        auto row = make_shared<ui::Box>(ui::Widget::HORZ);
        row->set_cross_alignment(ui::Widget::CENTER);
        row->set_margin_for_sdl(COMMAND_MENU_ITEM_PADDING);

        auto icon = make_shared<ui::Image>(tile_def(tile));
        icon->set_margin_for_sdl(0, COMMAND_MENU_ICON_GAP, 0, 0);
        row->add_child(std::move(icon));

        auto labels = make_shared<ui::Box>(ui::Widget::VERT);
        labels->expand_h = true;
        labels->add_child(_drawer_text(
            formatted_string(std::move(label), WHITE)));

        auto summary_text = _drawer_text(
            formatted_string(std::move(summary), LIGHTGREY));
        summary_text->set_wrap_text(true);
        labels->add_child(std::move(summary_text));
        row->add_child(std::move(labels));

        auto button = make_shared<MenuButton>();
        button->min_size().height = _command_item_height();
        button->highlight_colour = BROWN;
        button->set_child(std::move(row));
        buttons.push_back(button);
        return button;
    };

    auto pages = make_shared<ui::Switcher>();
    pages->align_x = pages->align_y = ui::Widget::STRETCH;

    auto scroller = make_shared<DrawerScroller>();
    scroller->set_child(pages);
    scroller->set_scrollbar_visible(true);
    scroller->expand_h = scroller->expand_v = true;

    const auto make_compact_button = [&buttons](string label) {
        auto text = _drawer_text(
            formatted_string(std::move(label), WHITE));
        text->set_margin_for_sdl(COMMAND_MENU_ITEM_PADDING);

        auto button = make_shared<MenuButton>();
        button->highlight_colour = BROWN;
        button->set_child(std::move(text));
        buttons.push_back(button);
        return button;
    };

    // Build one quick-access page: a title, a Back entry, full-width cards in
    // pages of at most QUICK_ICON_PAGE_SIZE, and explicit
    // Previous/Next controls with a current/total indicator when more than one
    // icon page exists. A tap records the entry and closes the drawer; the
    // action itself runs afterwards, outside the pushed layout.
    const auto build_quick_page =
        [&](const vector<quick_entry> &entries, const string &title_label,
            bool is_spell) {
        quick_page_refs refs;

        auto page = make_shared<ui::Box>(ui::Widget::VERT);
        page->set_cross_alignment(ui::Widget::STRETCH);

        auto page_title = _drawer_text(
            formatted_string(title_label, YELLOW));
        page_title->set_margin_for_sdl(0, 0, 16, 0);
        page->add_child(std::move(page_title));

        auto hint = _drawer_text(formatted_string(
            _command_menu_text("android command menu summary",
                               "Long press for details"), LIGHTGREY));
        hint->set_wrap_text(true);
        page->add_child(std::move(hint));

        refs.back = make_button(
            _command_menu_text("android command menu", "Back"),
            _command_menu_text("android command menu summary", "Back"),
            TILEG_CMD_MAP_EXIT_MAP);
        page->add_child(refs.back);

        const int icon_page_count =
            ((int) entries.size() + QUICK_ICON_PAGE_SIZE - 1)
            / QUICK_ICON_PAGE_SIZE;

        auto icon_pages = make_shared<ui::Switcher>();
        icon_pages->align_x = icon_pages->align_y = ui::Widget::STRETCH;

        for (int icon_page = 0; icon_page < icon_page_count; ++icon_page)
        {
            auto grid = make_shared<ui::Box>(ui::Widget::VERT);
            grid->set_cross_alignment(ui::Widget::STRETCH);

            // A single column lets the text use all available drawer width;
            // wrapped names and reasons determine each card's height.
            for (int row = 0; row < QUICK_ICON_PAGE_SIZE; ++row)
            {
                const size_t at = (size_t) icon_page * QUICK_ICON_PAGE_SIZE
                                  + row;
                if (at >= entries.size())
                    break;

                const quick_entry &entry = entries[at];
                auto cell = make_shared<ui::Box>(ui::Widget::HORZ);
                cell->set_cross_alignment(ui::Widget::CENTER);
                cell->set_margin_for_sdl(COMMAND_MENU_ITEM_PADDING);
                auto icon = make_shared<ui::Image>(tile_def(entry.tile));
                icon->set_margin_for_sdl(0, COMMAND_MENU_ICON_GAP, 0, 0);
                cell->add_child(std::move(icon));
                auto labels = make_shared<ui::Box>(ui::Widget::VERT);
                labels->set_cross_alignment(ui::Widget::STRETCH);
                labels->expand_h = true;
                auto name = _drawer_text(formatted_string(
                    entry.name, entry.usable ? WHITE : LIGHTGREY));
                name->set_wrap_text(true);
                labels->add_child(std::move(name));
                auto caption = _drawer_text(formatted_string(
                    _quick_entry_caption(entry), LIGHTGREY));
                caption->set_wrap_text(true);
                labels->add_child(std::move(caption));
                if (!entry.reason.empty())
                {
                    auto reason = _drawer_text(formatted_string(
                        entry.reason, LIGHTRED));
                    reason->set_wrap_text(true);
                    labels->add_child(std::move(reason));
                }
                cell->add_child(std::move(labels));

                auto button = make_shared<QuickButton>();
                button->min_size().height = _command_item_height();
                button->highlight_colour = BROWN;
                button->expand_h = true;
                button->set_child(std::move(cell));

                const int idx = entry.idx;
                button->on_activate_event(
                    [&, idx, is_spell](const ui::ActivateEvent&) {
                        if (is_spell)
                            quick_spell = (spell_type) idx;
                        else
                            quick_ability = (ability_type) idx;
                        done = true;
                        return true;
                    });
                button->on_describe = [&scroller, idx, is_spell]() {
                    if (is_spell)
                        describe_spell((spell_type) idx);
                    else
                        describe_ability((ability_type) idx);
                    // The moves that opened this gesture left the drawer
                    // scroller mid-drag; drop it so returning to the page
                    // does not scroll from a stale origin.
                    scroller->cancel_drag();
                };

                buttons.push_back(button);
                if (!refs.focus)
                    refs.focus = button;
                grid->add_child(std::move(button));
            }

            icon_pages->add_child(std::move(grid));
        }

        icon_pages->current() = 0;
        page->add_child(icon_pages);

        if (icon_page_count > 1)
        {
            auto indicator = _drawer_text(formatted_string(
                make_stringf("1 / %d", icon_page_count), LIGHTGREY));
            indicator->set_margin_for_sdl(0, COMMAND_MENU_ICON_GAP);

            // Wrapping keeps both controls meaningful on every icon page and
            // keeps the switcher index in range without extra bookkeeping.
            const auto turn_page =
                [&scroller, icon_pages, indicator, icon_page_count](int delta) {
                    int &shown = icon_pages->current();
                    shown = (shown + delta + icon_page_count)
                            % icon_page_count;
                    indicator->set_text(formatted_string(
                        make_stringf("%d / %d", shown + 1, icon_page_count),
                        LIGHTGREY));
                    scroller->cancel_drag();
                };

            auto previous_button = make_compact_button(
                _command_menu_text("android command menu", "Previous"));
            previous_button->on_activate_event(
                [turn_page](const ui::ActivateEvent&) {
                    turn_page(-1);
                    return true;
                });

            auto next_button = make_compact_button(
                _command_menu_text("android command menu", "Next"));
            next_button->on_activate_event(
                [turn_page](const ui::ActivateEvent&) {
                    turn_page(1);
                    return true;
                });

            auto controls = make_shared<ui::Box>(ui::Widget::HORZ);
            controls->set_cross_alignment(ui::Widget::CENTER);
            controls->add_child(std::move(previous_button));
            controls->add_child(std::move(indicator));
            controls->add_child(std::move(next_button));
            page->add_child(std::move(controls));
        }

        if (!refs.focus)
            refs.focus = refs.back;

        refs.index = (int) pages->num_children();
        pages->add_child(std::move(page));
        return refs;
    };

    const auto add_command_button =
        [&](const shared_ptr<ui::Box> &page, string label, string summary,
            tileidx_t tile, command_type command) {
            auto button = make_button(std::move(label), std::move(summary),
                                      tile);
            button->on_activate_event([&, command](const ui::ActivateEvent&) {
                selected_command = command;
                done = true;
                return true;
            });
            page->add_child(button);
            return button;
        };

    // Quick-access pages exist only for a non-empty current list, so the menu
    // never offers an entry point that would open an empty page.
    const vector<quick_entry> spell_entries = _quick_spell_entries();
    const vector<quick_entry> ability_entries = _quick_ability_entries();

    auto main_page = make_shared<ui::Box>(ui::Widget::VERT);
    main_page->set_cross_alignment(ui::Widget::STRETCH);
    auto main_title = _drawer_text(formatted_string(
        _command_menu_text("android command menu", "Game menu"), YELLOW));
    main_title->set_margin_for_sdl(0, 0, 16, 0);
    main_page->add_child(std::move(main_title));

    // Contextual entries must not shift the stable command positions when the
    // player moves off stairs or picks up the last item on a square.
    auto context_commands = make_shared<ui::Box>(ui::Widget::VERT);
    context_commands->set_cross_alignment(ui::Widget::STRETCH);
    context_commands->set_margin_for_sdl(16, 0, 0, 0);
    const dungeon_feature_type feature = env.grid(you.pos());
    const command_type stair_command = feat_stair_direction(feature);
    if (stair_command != CMD_NO_CMD && !feat_is_altar(feature))
    {
        const char *label;
        const char *summary;
        if (feature == DNGN_ENTER_SHOP)
        {
            label = "Enter Shop";
            summary = "Enter Shop";
        }
        else if (feat_is_gate(feature))
        {
            label = "Enter";
            summary = "Enter";
        }
        else if (stair_command == CMD_GO_UPSTAIRS)
        {
            label = "Go Upstairs";
            summary = "Go Upstairs";
        }
        else
        {
            label = "Go Downstairs";
            summary = "Go Downstairs";
        }

        add_command_button(
            context_commands,
            _command_menu_text("android command menu", label),
            _command_menu_text("android command menu summary", summary),
            tileidx_feature(you.pos()), stair_command);
    }

    if (you.visible_igrd(you.pos()) != NON_ITEM)
    {
        add_command_button(
            context_commands,
            _command_menu_text("android command menu", "Pick Up"),
            _command_menu_text("android command menu summary", "Pick Up"),
            TILEG_TAB_ITEM, CMD_PICKUP);
    }

    const auto primary_button = add_command_button(
        main_page,
        _command_menu_text("android command menu", "Auto-explore"),
        _command_menu_text("android command menu summary", "Auto-explore"),
        tileidx_command(CMD_EXPLORE), CMD_EXPLORE);

    add_command_button(
        main_page,
        _command_menu_text("android command menu", "Inventory"),
        _command_menu_text("android command menu summary", "Inventory"),
        TILEG_CMD_DISPLAY_INVENTORY, CMD_DISPLAY_INVENTORY);
    add_command_button(
        main_page,
        _command_menu_text("android command menu", "Spells"),
        _command_menu_text("android command menu summary", "Spells"),
        TILEG_CMD_CAST_SPELL, CMD_DISPLAY_SPELLS);
    shared_ptr<MenuButton> quick_spell_entry;
    if (!spell_entries.empty())
    {
        quick_spell_entry = make_button(
            _command_menu_text("android command menu", "Quick Cast"),
            _command_menu_text("android command menu summary", "Quick Cast"),
            TILEG_TAB_SPELL);
    }
    add_command_button(
        main_page,
        _command_menu_text("android command menu", "Abilities"),
        _command_menu_text("android command menu summary", "Abilities"),
        TILEG_CMD_USE_ABILITY, CMD_USE_ABILITY);
    shared_ptr<MenuButton> quick_ability_entry;
    if (!ability_entries.empty())
    {
        quick_ability_entry = make_button(
            _command_menu_text("android command menu", "Quick Abilities"),
            _command_menu_text("android command menu summary",
                               "Quick Abilities"),
            TILEG_TAB_ABILITY);
    }
    add_command_button(
        main_page,
        _command_menu_text("android command menu", "Character"),
        _command_menu_text("android command menu summary", "Character"),
        TILEG_CMD_RESISTS_SCREEN, CMD_RESISTS_SCREEN);
    add_command_button(
        main_page,
        _command_menu_text("android command menu", "Skills"),
        _command_menu_text("android command menu summary", "Skills"),
        TILEG_CMD_DISPLAY_SKILLS, CMD_DISPLAY_SKILLS);
    add_command_button(
        main_page,
        _command_menu_text("android command menu", "Religion"),
        _command_menu_text("android command menu summary", "Religion"),
        TILEG_CMD_DISPLAY_RELIGION, CMD_DISPLAY_RELIGION);
    const string more_label =
        _command_menu_text("android command menu", "More");
    const auto more = make_button(
        more_label,
        _command_menu_text("android command menu summary", "More"),
        TILEG_TAB_COMMAND2);
    main_page->add_child(more);

    if (quick_spell_entry)
        context_commands->add_child(quick_spell_entry);
    if (quick_ability_entry)
        context_commands->add_child(quick_ability_entry);
    if (context_commands->num_children())
        main_page->add_child(context_commands);

    auto more_page = make_shared<ui::Box>(ui::Widget::VERT);
    more_page->set_cross_alignment(ui::Widget::STRETCH);
    auto more_title = _drawer_text(
        formatted_string(more_label, YELLOW));
    more_title->set_margin_for_sdl(0, 0, 16, 0);
    more_page->add_child(std::move(more_title));

    const auto back = make_button(
        _command_menu_text("android command menu", "Back"),
        _command_menu_text("android command menu summary", "Back"),
        TILEG_CMD_MAP_EXIT_MAP);
    more_page->add_child(back);
    add_command_button(
        more_page,
        _command_menu_text("android command menu", "Memorise"),
        _command_menu_text("android command menu summary", "Memorise"),
        TILEG_CMD_MEMORISE_SPELL, CMD_MEMORISE_SPELL);
    add_command_button(
        more_page,
        _command_menu_text("android command menu", "Map"),
        _command_menu_text("android command menu summary", "Map"),
        TILEG_CMD_DISPLAY_MAP, CMD_DISPLAY_MAP);
    add_command_button(
        more_page,
        _command_menu_text("android command menu", "Known Objects"),
        _command_menu_text("android command menu summary", "Known Objects"),
        TILEG_CMD_KNOWN_ITEMS, CMD_DISPLAY_KNOWN_OBJECTS);
    add_command_button(
        more_page,
        _command_menu_text("android command menu", "Full View"),
        _command_menu_text("android command menu summary", "Full View"),
        TILEG_TAB_MONSTER, CMD_FULL_VIEW);
    add_command_button(
        more_page,
        _command_menu_text("android command menu", "Mutations"),
        _command_menu_text("android command menu summary", "Mutations"),
        TILEG_CMD_DISPLAY_MUTATIONS, CMD_DISPLAY_MUTATIONS);
    add_command_button(
        more_page,
        _command_menu_text("android command menu", "Commands"),
        _command_menu_text("android command menu summary", "Commands"),
        TILEG_CMD_DISPLAY_COMMANDS, CMD_DISPLAY_COMMANDS);

    pages->add_child(main_page);
    pages->add_child(more_page);
    pages->current() = 0;

    more->on_activate_event([&](const ui::ActivateEvent&) {
        pages->current() = 1;
        scroller->set_scroll(0);
        ui::set_focused_widget(back.get());
        return true;
    });
    back->on_activate_event([&](const ui::ActivateEvent&) {
        pages->current() = 0;
        scroller->set_scroll(0);
        ui::set_focused_widget(primary_button.get());
        return true;
    });

    const auto show_page = [&](int index, MenuButton *focus) {
        pages->current() = index;
        scroller->cancel_drag();
        scroller->set_scroll(0);
        ui::set_focused_widget(focus);
    };

    if (quick_spell_entry)
    {
        const quick_page_refs spell_page = build_quick_page(
            spell_entries,
            _command_menu_text("android command menu", "Quick Cast"), true);
        quick_spell_entry->on_activate_event(
            [&, spell_page](const ui::ActivateEvent&) {
                show_page(spell_page.index, spell_page.focus.get());
                return true;
            });
        spell_page.back->on_activate_event([&](const ui::ActivateEvent&) {
            show_page(0, primary_button.get());
            return true;
        });
    }

    if (quick_ability_entry)
    {
        const quick_page_refs ability_page = build_quick_page(
            ability_entries,
            _command_menu_text("android command menu", "Quick Abilities"),
            false);
        quick_ability_entry->on_activate_event(
            [&, ability_page](const ui::ActivateEvent&) {
                show_page(ability_page.index, ability_page.focus.get());
                return true;
            });
        ability_page.back->on_activate_event([&](const ui::ActivateEvent&) {
            show_page(0, primary_button.get());
            return true;
        });
    }

    auto panel = make_shared<DrawerPanel>(scroller);
    auto scrim = make_shared<DrawerScrim>(panel, scroller);
    const weak_ptr<DrawerScrim> weak_scrim = scrim;
    for (const auto &button : buttons)
    {
        button->on_keydown_event([weak_scrim](const ui::KeyEvent &event) {
            if (!key_is_escape(event.key()))
                return false;

            const auto active_scrim = weak_scrim.lock();
            return active_scrim && active_scrim->on_event(event);
        });
    }

    ui::push_layout(scrim);
    ui::set_focused_widget(primary_button.get());
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
