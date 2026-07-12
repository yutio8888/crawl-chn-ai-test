#include "AppHdr.h"

#ifdef USE_TILE_LOCAL

#include "layout-policy.h"
#include "libutil.h"      // for make_unique (C++11 compat)
#include "options.h"

DesktopLayoutPolicy::DesktopLayoutPolicy()
    : m_window_width(0), m_stat_cw(0), m_msg_cw(0),
      m_override(maybe_bool::maybe)
{
}

void DesktopLayoutPolicy::update(int window_width, int stat_cw, int msg_cw,
                                 maybe_bool override_mode)
{
    m_window_width = window_width;
    m_stat_cw = stat_cw;
    m_msg_cw = msg_cw;
    m_override = override_mode;
}

bool DesktopLayoutPolicy::active() const
{
    if (m_override != maybe_bool::maybe)
        return bool(m_override);
    if (m_stat_cw > 0 && m_msg_cw > 0)
        return m_window_width < m_stat_cw * 45 + m_msg_cw * 55;
    return false;
}

bool DesktopLayoutPolicy::uses_compact_hud() const
{
    return active();
}

bool DesktopLayoutPolicy::uses_overlay_sidebar() const
{
    return active();
}

bool DesktopLayoutPolicy::uses_compact_stats() const
{
    return active();
}

bool DesktopLayoutPolicy::uses_touch_tabs() const
{
    return active();
}

bool DesktopLayoutPolicy::uses_overlay_messages() const
{
    return active();
}

unique_ptr<LayoutPolicy> make_layout_policy()
{
    return make_unique<DesktopLayoutPolicy>();
}

#endif // USE_TILE_LOCAL
