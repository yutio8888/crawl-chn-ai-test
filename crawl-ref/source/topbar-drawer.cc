#include "AppHdr.h"

#ifdef USE_TILE_LOCAL

#include "topbar-drawer.h"

#include "database.h"
#include "libutil.h"
#include "status.h"
#include "tiles-build-specific.h"
#include "ui.h"

namespace
{

static const int DRAWER_PADDING = 24;

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
                shared_ptr<DrawerScroller> scroller)
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

        if (m_scroller->continue_drag(event))
            return true;

        if (event.type() == ui::Event::Type::KeyDown
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

#endif
