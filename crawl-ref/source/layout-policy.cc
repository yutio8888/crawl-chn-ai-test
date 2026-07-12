#include "AppHdr.h"

#ifdef USE_TILE_LOCAL

#include "layout-policy.h"
#include "libutil.h"      // for make_unique (C++11 compat)
#include "options.h"

// -------------------------------------------------------------------
// DesktopLayoutPolicy — preserves the existing width-threshold logic
// for all semantic queries. Height is accepted but unused.
// -------------------------------------------------------------------

DesktopLayoutPolicy::DesktopLayoutPolicy()
    : m_window_width(0), m_window_height(0), m_stat_cw(0), m_msg_cw(0),
      m_override(maybe_bool::maybe)
{
}

void DesktopLayoutPolicy::update(int window_width, int window_height,
                                 int stat_cw, int msg_cw,
                                 maybe_bool override_mode)
{
    m_window_width = window_width;
    m_window_height = window_height;
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

bool DesktopLayoutPolicy::uses_top_hud() const
{
    return false;
}

// -------------------------------------------------------------------
// AndroidPortraitLayoutPolicy — portrait-aware layout for Android.
// Uses aspect-ratio detection (height > width * 1.25) to switch
// between portrait and landscape semantics. In portrait mode
// uses_compact_hud() is always true (independent of width threshold).
// -------------------------------------------------------------------

AndroidPortraitLayoutPolicy::AndroidPortraitLayoutPolicy()
    : m_window_width(0), m_window_height(0), m_stat_cw(0), m_msg_cw(0),
      m_override(maybe_bool::maybe)
{
}

void AndroidPortraitLayoutPolicy::update(int window_width, int window_height,
                                         int stat_cw, int msg_cw,
                                         maybe_bool override_mode)
{
    m_window_width = window_width;
    m_window_height = window_height;
    m_stat_cw = stat_cw;
    m_msg_cw = msg_cw;
    m_override = override_mode;
}

bool AndroidPortraitLayoutPolicy::is_portrait() const
{
    if (m_override != maybe_bool::maybe)
        return bool(m_override);
    if (m_window_height <= 0)
        return false;
    return m_window_height > m_window_width * 1.25;
}

bool AndroidPortraitLayoutPolicy::uses_compact_hud() const
{
    // Portrait: always compact HUD (short HP/MP lines).
    // Landscape: fall back to width-threshold (same as desktop).
    if (is_portrait())
        return true;
    if (m_stat_cw > 0 && m_msg_cw > 0)
        return m_window_width < m_stat_cw * 45 + m_msg_cw * 55;
    return false;
}

bool AndroidPortraitLayoutPolicy::uses_overlay_sidebar() const
{
    return true;
}

bool AndroidPortraitLayoutPolicy::uses_compact_stats() const
{
    return true;
}

bool AndroidPortraitLayoutPolicy::uses_touch_tabs() const
{
    return true;
}

bool AndroidPortraitLayoutPolicy::uses_overlay_messages() const
{
    return true;
}

bool AndroidPortraitLayoutPolicy::uses_top_hud() const
{
    // TODO: temp force for testing — revert after debug
    return true;
}

// -------------------------------------------------------------------
// Factory — platform-aware policy creation
// -------------------------------------------------------------------

unique_ptr<LayoutPolicy> make_layout_policy()
{
#ifdef __ANDROID__
    return make_unique<AndroidPortraitLayoutPolicy>();
#else
    return make_unique<DesktopLayoutPolicy>();
#endif
}

#endif // USE_TILE_LOCAL
