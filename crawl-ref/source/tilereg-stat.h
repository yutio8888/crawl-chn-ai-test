#ifdef USE_TILE_LOCAL
#pragma once

#include <vector>

#include "tilebuf.h"
#include "tilereg-text.h"

using std::vector;

struct status_hitbox
{
    int status;
    int x1, x2; // inclusive grid-cell column range
    int y;      // grid-cell row
};

// Called by output.cc during _print_status_lights() to register hit-test
// regions for each status light rendered into the stat panel.
void clear_status_hitboxes();
void record_status_hitbox(int status, int x1, int x2, int y);
const vector<status_hitbox>& get_status_hitboxes();

class StatRegion : public TextRegion
{
public:
    StatRegion(FontWrapper *font_arg);

    virtual int handle_mouse(wm_mouse_event &event) override;
    virtual bool update_tip_text(string &tip) override;

    virtual void render() override;
    virtual void clear() override;

protected:
    ShapeBuffer m_shape_buf;
    void _clear_buffers();
    bool _text_mouse_pos(int mouse_x, int mouse_y, int &cx, int &cy);
    int m_last_mouse_x = 0;
    int m_last_mouse_y = 0;
};

#endif
