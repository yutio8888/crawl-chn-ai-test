#!/usr/bin/env python3
"""Execute production quick-row allocation, item construction and dispatch.

These tests use UI/game doubles around the actual C++ methods. They verify
membership, ordering, overflow reachability and no sentinel dispatch; icon
rendering and modal gestures still need the Android build/device checks.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_android_quickbar as regression

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "crawl-ref/source"


def body(filename, anchor):
    return regression.block_after((SRC / filename).read_text(), anchor)


class AndroidQuickRowTests(unittest.TestCase):
    def run_cpp(self, source):
        regression.TargetingSafetyTests.run_cpp(self, source)

    def test_actual_counts_reclaim_empty_half_without_hiding_live_lists(self):
        self.run_cpp(r'''
#include <algorithm>
#include <cassert>
#include <vector>
using namespace std;
struct { int spell_no=0; } you;
vector<int> talents;
vector<int> your_talents(bool) { return talents; }
struct Region {
    int dx=48, sy=0, sx=0, mx=0, my=0, updates=0;
    void place(int x,int y,int) { sx=x; sy=y; }
    void resize(int x,int y) { mx=x; my=y; }
    void update() { ++updates; }
};
struct TilesFramework {
    Region *m_region_quick_spl, *m_region_quick_abl;
    struct { int x=0; } m_windowsz;
    void place_quick_row(int row_y,bool spells,bool abilities)
''' + body("tilesdl.cc", "void TilesFramework::place_quick_row") + r'''
};
int main() {
    Region spells, abilities;
    TilesFramework tiles;
    tiles.m_region_quick_spl=&spells; tiles.m_region_quick_abl=&abilities;
    for(int cells=0;cells<=25;++cells)
        for(int ns=0;ns<=30;++ns)
            for(int na=0;na<=30;++na) {
                you.spell_no=ns; talents.resize(na); tiles.m_windowsz.x=cells*48+5;
                tiles.place_quick_row(100,ns>0,na>0);
                assert(spells.mx+abilities.mx==min(cells,min(23,ns)+na));
                assert(spells.mx>=0 && spells.mx<=min(23,ns));
                assert(abilities.mx>=0 && abilities.mx<=na);
                assert(abilities.sx==spells.mx*48 && spells.sy==100 && abilities.sy==100);
                if(cells>=2 && ns && na) assert(spells.mx && abilities.mx);
            }
}
''')

    def test_real_item_identity_order_capacity_and_overflow(self):
        self.run_cpp(r'''
#include <algorithm>
#include <cassert>
#include <vector>
using namespace std;
using spell_type=int;
using ability_type=int;
enum { SPELL_NO_SPELL=-1, CMD_CAST_SPELL=1, TILEI_FLAG_INVALID=2,
       TILEG_MENU_SPELLS=100, TILEG_MENU_ABILITIES=101 };
struct { int spell_no=0; } you;
char index_to_letter(int i) { return i; }
spell_type get_spell_by_letter(char c) { return c<you.spell_no ? int(c) : int(SPELL_NO_SPELL); }
int tileidx_spell(int sk) { return sk+1; }
int spell_mana(int sk) { return sk; }
bool tile_command_not_applicable(int,bool) { return false; }
bool spell_is_useless(int sk,bool,bool) { return sk%2; }
struct talent { int which; bool is_invocation; };
vector<talent> talents;
vector<talent> your_talents(bool) { return talents; }
struct InventoryTile { int idx=-1,tile=0,quantity=-1,flag=0; };
InventoryTile _tile_for_ability(ability_type sk) {
    InventoryTile tile; tile.idx=sk; return tile;
}
struct SpellRegion {
    vector<InventoryTile> m_items;
    bool m_dirty=false, m_quick_access=false;
    int mx=0,my=1;
    void update()
''' + body("tilereg-spl.cc", "void SpellRegion::update()") + r'''
};
struct AbilityRegion {
    vector<InventoryTile> m_items;
    bool m_dirty=false, m_quick_access=false;
    int mx=0,my=1;
    int get_max_slots() { return 15; }
    void update()
''' + body("tilereg-abl.cc", "void AbilityRegion::update()") + r'''
};
int main() {
    SpellRegion spells; AbilityRegion abilities;
    for(bool quick : {false,true})
        for(int cells=0;cells<=26;++cells)
            for(int count=0;count<=30;++count) {
                you.spell_no=count;
                spells.mx=abilities.mx=cells;
                spells.m_quick_access=abilities.m_quick_access=quick;
                spells.update();
                bool overflow=quick && cells && count>min(22,cells);
                int real=cells ? min(count,min(22,cells-(overflow?1:0))) : 0;
                assert(spells.m_items.size()==static_cast<size_t>(real+overflow));
                for(int i=0;i<real;++i) {
                    assert(spells.m_items[i].idx==i);
                    assert(bool(spells.m_items[i].flag&TILEI_FLAG_INVALID)==bool(i%2));
                }
                if(overflow) assert(spells.m_items.back().idx==-1 && spells.m_items.back().tile==TILEG_MENU_SPELLS);
                talents.clear(); vector<int> expected;
                for(int i=0;i<count;++i) talents.push_back({i,i%3==0});
                for(const auto& t:talents) if(!t.is_invocation) expected.push_back(t.which);
                for(const auto& t:talents) if(t.is_invocation) expected.push_back(t.which);
                abilities.update();
                overflow=quick && cells && count>cells;
                real=cells ? min(count,quick ? cells-(overflow?1:0) : min(15,cells)) : 0;
                assert(abilities.m_items.size()==static_cast<size_t>(real+overflow));
                for(int i=0;i<real;++i) assert(abilities.m_items[i].idx==expected[i]);
                if(overflow) assert(abilities.m_items.back().idx==-1 && abilities.m_items.back().tile==TILEG_MENU_ABILITIES);
            }
}
''')

    def test_overflow_sentinel_cannot_reach_cast_or_ability_apis(self):
        self.run_cpp(r'''
#include <cassert>
#include <climits>
#include <vector>
using namespace std;
struct coord_def { int x,y; coord_def(int xx,int yy):x(xx),y(yy){} };
const coord_def NO_CURSOR(-1,-1);
enum { MOUSE_MODE_COMMAND=1, CMD_CAST_SPELL=2, CMD_USE_ABILITY=3,
       CK_MOUSE_CMD=4, FLUSH_ON_FAILURE=5, NUM_SPELLS=99, NUM_ABILITIES=99,
       ABIL_NON_ABILITY=-1 };
namespace mouse_control { int mode=MOUSE_MODE_COMMAND; int current_mode(){return mode;} }
struct wm_mouse_event {
    enum { PRESS, RELEASE, MOVE };
    enum { LEFT, RIGHT, MIDDLE };
    int event=PRESS,button=LEFT,px=0,py=0;
};
struct { bool get_map_display(){return false;} void set_need_redraw(){} } tiles;
bool blocked=false;
bool tile_command_not_applicable(int,bool){return blocked;}
using spell_type=int; using ability_type=int;
namespace spret { enum result { abort,success }; }
int casts=0,activations=0,descriptions=0,opens=0;
spret::result cast_a_spell(bool check,int sk){assert(check && sk>=0);++casts;return spret::success;}
void describe_spell(int sk){assert(sk>=0);++descriptions;}
void describe_ability(int sk){assert(sk>=0);++descriptions;}
void redraw_screen(){} void update_screen(){} void flush_input_buffer(int){}
struct talent { int which; };
talent get_talent(int sk){assert(sk>=0);return {sk};}
bool activate_talent(talent){++activations;return true;}
enum class CommandMenuSection {SPELLS,ABILITIES};
void show_topbar_command_menu(void*,CommandMenuSection){++opens;}
struct InventoryTile { int idx=-1; bool empty()const{return idx==-1;} };
struct GridRegion {
    vector<InventoryTile> m_items;
    coord_def cursor{0,0};
    bool mouse_pos(int x,int y,int& cx,int& cy){cx=x;cy=y;return x==0 && y==0;}
    void place_cursor(coord_def c){cursor=c;}
    unsigned cursor_index(){return cursor.x;}
    bool place_cursor(wm_mouse_event& event,unsigned int& item_idx)
''' + body("tilereg-grid.cc", "bool GridRegion::place_cursor(wm_mouse_event") + r'''
};
struct SpellRegion : GridRegion {
    bool m_quick_access=true, m_check_range=true;
    int m_last_clicked_item=-1;
    int handle_mouse(wm_mouse_event& event)
''' + body("tilereg-spl.cc", "int SpellRegion::handle_mouse") + r'''
};
struct AbilityRegion : GridRegion {
    bool m_quick_access=true;
    int m_last_clicked_item=-1;
    int handle_mouse(wm_mouse_event& event)
''' + body("tilereg-abl.cc", "int AbilityRegion::handle_mouse") + r'''
};
int main(){
    SpellRegion spells; AbilityRegion abilities;
    spells.m_items.resize(1); abilities.m_items.resize(1);
    wm_mouse_event event;
    for(bool quick:{false,true})
        for(int index:{-1,7})
            for(int kind:{wm_mouse_event::PRESS,wm_mouse_event::RELEASE,wm_mouse_event::MOVE})
                for(int button:{wm_mouse_event::LEFT,wm_mouse_event::RIGHT,wm_mouse_event::MIDDLE})
                    for(bool command:{false,true})
                        for(bool outside:{false,true})
                            for(bool unavailable:{false,true}){
                                spells.m_quick_access=abilities.m_quick_access=quick;
                                spells.m_items[0].idx=abilities.m_items[0].idx=index;
                                event.event=kind;event.button=button;event.px=outside?1:0;
                                mouse_control::mode=command?MOUSE_MODE_COMMAND:0;blocked=unavailable;
                                casts=activations=descriptions=opens=0;
                                spells.handle_mouse(event);abilities.handle_mouse(event);
                                bool valid=command && !outside && kind==wm_mouse_event::PRESS;
                                bool overflow=valid && quick && index==-1 && button!=wm_mouse_event::MIDDLE;
                                assert(opens==(overflow?2:0));
                                bool real=valid && index>=0 && !unavailable;
                                assert(casts==(real && button==wm_mouse_event::LEFT?1:0));
                                assert(activations==casts);
                                assert(descriptions==(real && button==wm_mouse_event::RIGHT?2:0));
                            }
}
''')

    def test_quiver_all_available_commands_survive_spill_once(self):
        quiver = (SRC / "quiver.cc").read_text()
        actions = regression.block_after(quiver[quiver.index("class ActionSelectMenu"):],
                                         "keyboard_actions() override")
        self.run_cpp(r'''
#include <array>
#include <cassert>
#include <string>
#include <vector>
#include <algorithm>
using namespace std;
const char* T_(const char* text){return text;}
namespace ui {
struct InputAction { string label; int key; InputAction(string s="",int k=0):label(s),key(k){} };
const int INPUT_MORE_KEY=1000;
void spill_input_actions(array<InputAction,6>& actions,size_t first,
                         vector<InputAction> candidates,vector<InputAction>& more)
''' + body("ui.cc", "void spill_input_actions") + r'''
}
struct ActionSelectMenu {
    bool any_items=false,any_spells=false,any_abilities=false,allow_empty=false;
    vector<ui::InputAction> m_keyboard_more;
    array<ui::InputAction,6> keyboard_actions()
''' + actions + r'''
};
int main(){
    ActionSelectMenu menu;
    for(int mask=0;mask<16;++mask){
        menu.any_items=mask&1;menu.any_spells=mask&2;
        menu.any_abilities=mask&4;menu.allow_empty=mask&8;
        auto actions=menu.keyboard_actions();
        vector<int> actual,expected={'!'};
        for(const auto& action:actions)
            if(action.key && action.key!=ui::INPUT_MORE_KEY) actual.push_back(action.key);
        for(const auto& action:menu.m_keyboard_more){assert(!action.label.empty());actual.push_back(action.key);}
        if(menu.any_items) expected.push_back('*');
        if(menu.any_spells) expected.push_back('&');
        if(menu.any_abilities) expected.push_back('^');
        if(menu.allow_empty) expected.push_back('-');
        assert(actual==expected);
        assert((actions.back().key==ui::INPUT_MORE_KEY)==(mask==15));
    }
}
''')


if __name__ == "__main__":
    unittest.main()
