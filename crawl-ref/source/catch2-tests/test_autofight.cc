#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "env.h"
#include "losglobal.h"
#include "mon-info.h"
#include "mon-util.h"
#include "player.h"
#include "spl-util.h"
#include "throw.h"

#include "test_player_fixture.h"

namespace
{
// Map knowledge is sufficient for the aiming heuristic: remembered invisible
// monsters deliberately have no corresponding actor at their old position.
class scoped_autofight_corridor
{
public:
    scoped_autofight_corridor()
        : old_position(you.pos()), old_vision(you.current_vision)
    {
        for (int x = 12; x <= 28; ++x)
            for (int y = 12; y <= 28; ++y)
            {
                coord_def p(x, y);
                cells.push_back({p, env.grid(p), env.mgrid(p), env.map_knowledge(p)});
                env.grid(p) = y == 20 ? DNGN_FLOOR : DNGN_ROCK_WALL;
                env.mgrid(p) = NON_MONSTER;
                env.map_knowledge(p).clear();
            }
        you.set_position(coord_def(20, 20));
        you.current_vision = 7;
        invalidate_los();
    }

    ~scoped_autofight_corridor()
    {
        you.set_position(old_position);
        you.current_vision = old_vision;
        for (const auto& cell : cells)
        {
            env.grid(cell.pos) = cell.feature;
            env.mgrid(cell.pos) = cell.monster_index;
            env.map_knowledge(cell.pos) = cell.knowledge;
        }
        invalidate_los();
    }

    void put(const coord_def& pos, const monster_info& mi)
    {
        env.map_knowledge(pos).set_monster(mi);
    }

private:
    struct saved_cell
    {
        coord_def pos;
        dungeon_feature_type feature;
        unsigned short monster_index;
        map_cell knowledge;
    };
    vector<saved_cell> cells;
    coord_def old_position;
    int old_vision;
};
}

TEST_CASE_METHOD(MockPlayerYouTestsFixture,
                 "Autofire ignores old invisible monster positions",
                 "[autofight]")
{
    init_monsters();
    init_spell_descs();
    scoped_autofight_corridor world;
    const coord_def target(24, 20);
    const coord_def old_wizard_pos(22, 20);
    monster_info orc(MONS_ORC);
    orc.can_shoot_through_monster = false;
    world.put(target, orc);

    SECTION("an unobstructed enemy is reachable")
    {
        CHECK_FALSE(best_ranged_aim(target, false).origin());
    }

    SECTION("an invisible wizard's old position is empty")
    {
        monster_info remembered(MONS_ORC_WIZARD);
        remembered.mb.set(MB_REMEMBERED_INVIS);
        remembered.can_shoot_through_monster = false;
        world.put(old_wizard_pos, remembered);
        CHECK_FALSE(best_ranged_aim(target, false).origin());
        CHECK_FALSE(best_ranged_aim(target, false, true).origin());
    }

    SECTION("a friendly monster still blocks non-piercing shots")
    {
        orc.attitude = ATT_FRIENDLY;
        world.put(old_wizard_pos, orc);
        CHECK(best_ranged_aim(target, false).origin());
        CHECK_FALSE(best_ranged_aim(target, true).origin());
    }

    SECTION("a known invisible hostile remains a target")
    {
        orc.mb.set(MB_KNOWN_INVIS);
        world.put(target, orc);
        CHECK_FALSE(best_ranged_aim(target, false).origin());
    }
}
