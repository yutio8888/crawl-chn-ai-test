#include "AppHdr.h"

#ifdef USE_TILE_LOCAL

#include "topbar-drawer.h"

#include "database.h"
#include "libutil.h"
#include "outer-menu.h"
#include "status.h"
#include "tiles-build-specific.h"
#include "ui.h"

namespace
{

static const int DRAWER_PADDING = 24;
static const int COMMAND_MENU_ITEM_HEIGHT = 72;
static const int COMMAND_MENU_ITEM_PADDING = 12;
static const int COMMAND_MENU_ICON_GAP = 16;

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

static formatted_string _build_status_text()
{
    formatted_string text(LIGHTGREY);
    bool found_status = false;

    for (int status = 0; status <= STATUS_LAST_STATUS; ++status)
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
        if (!description.empty() && description != title)
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

} // namespace

void show_topbar_status_drawer()
{
    auto text = make_shared<ui::Text>(_build_status_text());
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

command_type show_topbar_command_menu()
{
    command_type selected_command = CMD_NO_CMD;
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
        labels->add_child(make_shared<ui::Text>(
            formatted_string(std::move(label), WHITE)));

        auto summary_text = make_shared<ui::Text>(
            formatted_string(std::move(summary), LIGHTGREY));
        summary_text->set_wrap_text(true);
        labels->add_child(std::move(summary_text));
        row->add_child(std::move(labels));

        auto button = make_shared<MenuButton>();
        button->min_size().height = COMMAND_MENU_ITEM_HEIGHT;
        button->highlight_colour = BROWN;
        button->set_child(std::move(row));
        buttons.push_back(button);
        return button;
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

    auto main_page = make_shared<ui::Box>(ui::Widget::VERT);
    main_page->set_cross_alignment(ui::Widget::STRETCH);
    auto main_title = make_shared<ui::Text>(formatted_string(
        C_("android command menu", "Game menu"), YELLOW));
    main_title->set_margin_for_sdl(0, 0, 16, 0);
    main_page->add_child(std::move(main_title));

    const auto inventory = add_command_button(
        main_page,
        string(C_("android command menu", "Inventory")),
        string(C_("android command menu summary", "Inventory")),
        TILEG_CMD_DISPLAY_INVENTORY, CMD_DISPLAY_INVENTORY);
    add_command_button(
        main_page,
        string(C_("android command menu", "Spells")),
        string(C_("android command menu summary", "Spells")),
        TILEG_CMD_CAST_SPELL, CMD_DISPLAY_SPELLS);
    add_command_button(
        main_page,
        string(C_("android command menu", "Abilities")),
        string(C_("android command menu summary", "Abilities")),
        TILEG_CMD_USE_ABILITY, CMD_USE_ABILITY);
    add_command_button(
        main_page,
        string(C_("android command menu", "Character")),
        string(C_("android command menu summary", "Character")),
        TILEG_CMD_RESISTS_SCREEN, CMD_RESISTS_SCREEN);
    add_command_button(
        main_page,
        string(C_("android command menu", "Skills")),
        string(C_("android command menu summary", "Skills")),
        TILEG_CMD_DISPLAY_SKILLS, CMD_DISPLAY_SKILLS);
    add_command_button(
        main_page,
        string(C_("android command menu", "Religion")),
        string(C_("android command menu summary", "Religion")),
        TILEG_CMD_DISPLAY_RELIGION, CMD_DISPLAY_RELIGION);
    const auto more = make_button(
        string(C_("android command menu", "More")),
        string(C_("android command menu summary", "More")),
        TILEG_TAB_COMMAND2);
    main_page->add_child(more);

    auto more_page = make_shared<ui::Box>(ui::Widget::VERT);
    more_page->set_cross_alignment(ui::Widget::STRETCH);
    auto more_title = make_shared<ui::Text>(formatted_string(
        C_("android command menu", "More"), YELLOW));
    more_title->set_margin_for_sdl(0, 0, 16, 0);
    more_page->add_child(std::move(more_title));

    const auto back = make_button(
        string(C_("android command menu", "Back")),
        string(C_("android command menu summary", "Back")),
        TILEG_CMD_MAP_EXIT_MAP);
    more_page->add_child(back);
    add_command_button(
        more_page,
        string(C_("android command menu", "Memorise")),
        string(C_("android command menu summary", "Memorise")),
        TILEG_CMD_MEMORISE_SPELL, CMD_MEMORISE_SPELL);
    add_command_button(
        more_page,
        string(C_("android command menu", "Map")),
        string(C_("android command menu summary", "Map")),
        TILEG_CMD_DISPLAY_MAP, CMD_DISPLAY_MAP);
    add_command_button(
        more_page,
        string(C_("android command menu", "Known Objects")),
        string(C_("android command menu summary", "Known Objects")),
        TILEG_CMD_KNOWN_ITEMS, CMD_DISPLAY_KNOWN_OBJECTS);
    add_command_button(
        more_page,
        string(C_("android command menu", "Full View")),
        string(C_("android command menu summary", "Full View")),
        TILEG_TAB_MONSTER, CMD_FULL_VIEW);
    add_command_button(
        more_page,
        string(C_("android command menu", "Mutations")),
        string(C_("android command menu summary", "Mutations")),
        TILEG_CMD_DISPLAY_MUTATIONS, CMD_DISPLAY_MUTATIONS);
    add_command_button(
        more_page,
        string(C_("android command menu", "Commands")),
        string(C_("android command menu summary", "Commands")),
        TILEG_CMD_DISPLAY_COMMANDS, CMD_DISPLAY_COMMANDS);

    auto pages = make_shared<ui::Switcher>();
    pages->align_x = pages->align_y = ui::Widget::STRETCH;
    pages->add_child(main_page);
    pages->add_child(more_page);
    pages->current() = 0;

    more->on_activate_event([&](const ui::ActivateEvent&) {
        pages->current() = 1;
        ui::set_focused_widget(back.get());
        return true;
    });
    back->on_activate_event([&](const ui::ActivateEvent&) {
        pages->current() = 0;
        ui::set_focused_widget(inventory.get());
        return true;
    });

    auto panel = make_shared<DrawerPanel>(pages);
    auto scrim = make_shared<DrawerScrim>(panel);
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
    ui::set_focused_widget(inventory.get());
    while (!done && !scrim->close_requested() && !crawl_state.seen_hups)
        ui::pump_events();
    ui::pop_layout();
    tiles.set_need_redraw();

    return selected_command;
}

#endif
