#pragma once

#ifdef USE_TILE_LOCAL

#include <memory>
#include "maybe-bool.h"

class LayoutPolicy
{
public:
    virtual ~LayoutPolicy() = default;

    /// Update policy state with current window metrics.
    /// Called from do_layout() before semantic queries.
    virtual void update(int window_width, int window_height,
                        int stat_cw, int msg_cw,
                        maybe_bool override_mode) = 0;

    /// Compact HUD text formatting (short HP/MP/status in output.cc)
    virtual bool uses_compact_hud() const = 0;

    /// Sidebar overlays the dungeon view (tabs on right, tilesdl.cc layout)
    virtual bool uses_overlay_sidebar() const = 0;

    /// Stat region uses compact layout (tilereg-stat.cc)
    virtual bool uses_compact_stats() const = 0;

    /// Tabs support touch interaction mode
    virtual bool uses_touch_tabs() const = 0;

    /// Messages region overlays the dungeon view
    virtual bool uses_overlay_messages() const = 0;

    /// Stat region rendered as a top horizontal bar (portrait HUD).
    /// When false, stat region is a right-side column (desktop / small-landscape).
    virtual bool uses_top_hud() const = 0;
};

class DesktopLayoutPolicy : public LayoutPolicy
{
    int m_window_width;
    int m_window_height;
    int m_stat_cw;
    int m_msg_cw;
    maybe_bool m_override;

    bool active() const;

public:
    DesktopLayoutPolicy();

    void update(int window_width, int window_height,
                int stat_cw, int msg_cw,
                maybe_bool override_mode) override;

    bool uses_compact_hud() const override;
    bool uses_overlay_sidebar() const override;
    bool uses_compact_stats() const override;
    bool uses_touch_tabs() const override;
    bool uses_overlay_messages() const override;

    bool uses_top_hud() const override;
};

class AndroidPortraitLayoutPolicy : public LayoutPolicy
{
    int m_window_width;
    int m_window_height;
    int m_stat_cw;
    int m_msg_cw;
    maybe_bool m_override;

    bool is_portrait() const;

public:
    AndroidPortraitLayoutPolicy();

    void update(int window_width, int window_height,
                int stat_cw, int msg_cw,
                maybe_bool override_mode) override;

    bool uses_compact_hud() const override;
    bool uses_overlay_sidebar() const override;
    bool uses_compact_stats() const override;
    bool uses_touch_tabs() const override;
    bool uses_overlay_messages() const override;

    bool uses_top_hud() const override;
};

std::unique_ptr<LayoutPolicy> make_layout_policy();

#endif // USE_TILE_LOCAL
