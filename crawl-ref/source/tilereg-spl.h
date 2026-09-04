#ifdef USE_TILE_LOCAL
#pragma once

#include "tilereg-grid.h"

class SpellRegion : public GridRegion
{
public:
    // check_range selects which of the two ordinary casting entry points a
    // left click reaches: false is the sidebar's mouse cast, true is what the
    // z command reaches after its own selection step. The Android quick row
    // needs z semantics; every other instance keeps the sidebar behaviour.
    SpellRegion(const TileRegionInit &init, bool check_range = false);

    virtual void update() override;
    virtual int handle_mouse(wm_mouse_event &event) override;
    virtual bool update_tip_text(string &tip) override;
    virtual bool update_tab_tip_text(string &tip, bool active) override;
    virtual bool update_alt_text(string &alt) override;

    virtual const string name() const override { return "Spells"; }

protected:
    virtual int get_max_slots();

    const bool m_check_range;

    virtual void pack_buffers() override;
    virtual void draw_tag() override;
    virtual void activate() override;
};

#endif
