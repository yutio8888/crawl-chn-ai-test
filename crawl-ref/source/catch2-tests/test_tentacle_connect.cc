/**
 * @file
 * @brief Regression coverage for tentacle body construction.
 *
 * _try_tentacle_connect()/_establish_connection() used to report success after
 * a partial body layout: a body could be grafted onto a monster that is not
 * part of the tentacle, and a connector that could not be placed was silently
 * skipped. These cases pin the construction contract on the production entry
 * points (move_solo_tentacle / move_child_tentacles).
**/

#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "act-iter.h"
#include "coordit.h"
#include "defines.h"
#include "env.h"
#include "fineff.h"
#include "mon-death.h"
#include "mon-place.h"
#include "mon-tentacle.h"
#include "monster.h"
#include "player.h"
#include "state.h"

#include "test_player_fixture.h"

namespace
{

struct saved_tentacle_cell
{
    coord_def position;
    dungeon_feature_type feature;
    unsigned short monster_index;
};

const coord_def ARENA_MIN(10, 12);
const coord_def ARENA_MAX(24, 24);

// A one-wide corridor with rock on both sides, so a body laid out here has no
// room to route around anything.
const int CORRIDOR_Y = 20;
const int CORRIDOR_MIN_X = 12;
const int CORRIDOR_MAX_X = 18;

const coord_def BASE_POS(CORRIDOR_MIN_X, CORRIDOR_Y);
const coord_def INNER_SEGMENT_POS(CORRIDOR_MIN_X + 1, CORRIDOR_Y);
const coord_def OUTER_SEGMENT_POS(CORRIDOR_MIN_X + 2, CORRIDOR_Y);
const coord_def TIP_POS(CORRIDOR_MIN_X + 3, CORRIDOR_Y);

// A tentacle body is capped by the layout's string distance; keep the check
// loose but finite so an accidentally endless chain is still caught.
const size_t MAX_EXPECTED_BODY = 9;

/**
 * Carves a small floor patch out of the fixture's level and registers monsters
 * directly, so each case controls the exact tentacle layout.
 *
 * Monsters created by the production calls under test (body connectors) are not
 * registered here: they are removed again before the fixture's monster index
 * state is restored, so no live body segment is left behind with a rolled-back
 * mid/grid.
 */
class scoped_tentacle_arena
{
public:
    scoped_tentacle_arena()
        : old_test(crawl_state.test), old_last_mid(you.last_mid),
          old_max_mon_index(env.max_mon_index), old_mid_cache(env.mid_cache)
    {
        crawl_state.test = true;
        for (int x = ARENA_MIN.x; x <= ARENA_MAX.x; ++x)
        {
            for (int y = ARENA_MIN.y; y <= ARENA_MAX.y; ++y)
            {
                const coord_def pos(x, y);
                cells.push_back({pos, env.grid(pos), env.mgrid(pos)});
                env.grid(pos) = DNGN_ROCK_WALL;
                env.mgrid(pos) = NON_MONSTER;
            }
        }
        for (int x = CORRIDOR_MIN_X; x <= CORRIDOR_MAX_X; ++x)
            env.grid(coord_def(x, CORRIDOR_Y)) = DNGN_FLOOR;

        // Catch2 randomises test order, so the monster tables may not have
        // been initialised by another fixture yet.
        init_show_table();
        init_monsters();
    }

    ~scoped_tentacle_arena()
    {
        cleanup_production_bodies();

        for (monster *mon : registered)
        {
            if (mon && mon->type != MONS_NO_MONSTER)
            {
                mon->destroy_inventory();
                env.mid_cache.erase(mon->mid);
                mon->reset();
            }
        }

        // Death cleanup queues deferred effects and pending monster resets;
        // finish them here so slots are freed and nothing leaks into later
        // test cases.
        fire_final_effects();

        for (const saved_tentacle_cell &cell : cells)
        {
            env.grid(cell.position) = cell.feature;
            env.mgrid(cell.position) = cell.monster_index;
        }

        you.last_mid = old_last_mid;
        env.max_mon_index = old_max_mon_index;
        env.mid_cache = old_mid_cache;
        crawl_state.test = old_test;
    }

    /**
     * Removes the body connectors that the production calls under test created
     * for this arena's tentacles. Monsters created by other fixtures are never
     * touched: only bodies anchored on a mid this arena owns are removed.
     */
    void cleanup_production_bodies()
    {
        for (monster_iterator mi; mi; ++mi)
        {
            monster *mon = *mi;
            if (mon->tentacle_connect == MID_NOBODY)
                continue;
            if (find(owned_mids.begin(), owned_mids.end(),
                     mon->tentacle_connect) == owned_mids.end())
            {
                continue;
            }
            if (find(registered.begin(), registered.end(), mon)
                != registered.end())
            {
                continue;
            }
            monster_die(*mon, KILL_TENTACLE_CLEANUP, NON_MONSTER, true);
        }
    }

    monster *add_monster(monster_type type, const coord_def &pos)
    {
        monster *mon = get_free_monster();
        REQUIRE(mon != nullptr);
        mon->type = type;
        mon->set_hit_dice(1);
        mon->hit_points = mon->max_hit_points = 40;
        mon->speed = 10;
        mon->base_attitude = ATT_HOSTILE;
        mon->behaviour = BEH_SEEK;
        mon->foe = MHITNOT;
        mon->set_position(pos);
        mon->set_new_monster_id();
        env.mgrid(pos) = mon->mindex();
        registered.push_back(mon);
        owned_mids.push_back(mon->mid);
        return mon;
    }

    /**
     * Fills monster slots without placing them, so a case can reach the level's
     * monster cap (an existing generation constraint) deterministically.
     */
    void fill_monster_slots(size_t count)
    {
        for (size_t i = 0; i < count; ++i)
        {
            monster *mon = get_free_monster();
            if (!mon)
                FAIL("monster slots exhausted below the expected cap");
            mon->type = MONS_RAT;
            mon->set_hit_dice(1);
            mon->hit_points = mon->max_hit_points = 5;
            mon->speed = 10;
            mon->base_attitude = ATT_HOSTILE;
            mon->behaviour = BEH_SEEK;
            mon->foe = MHITNOT;
            mon->set_new_monster_id();
            registered.push_back(mon);
            owned_mids.push_back(mon->mid);
        }
    }

    /**
     * Build a solo tentacle with its body laid out from @p tip_to_body[0] (the
     * tip) inwards; @p base is the recorded (anchored) base cell.
     */
    monster *build_solo_tentacle(monster_type head_type,
                                 monster_type segment_type,
                                 const vector<coord_def> &tip_to_body,
                                 const coord_def &base)
    {
        ASSERT(!tip_to_body.empty());
        monster *head = add_monster(head_type, tip_to_body[0]);
        head->props[BASE_POSITION_KEY].get_coord() = base;

        vector<monster *> segments;
        for (size_t i = 1; i < tip_to_body.size(); ++i)
            segments.push_back(add_monster(segment_type, tip_to_body[i]));

        for (size_t i = 0; i < segments.size(); ++i)
        {
            segments[i]->tentacle_connect = head->mid;
            const mid_t inward = i + 1 < segments.size()
                                    ? segments[i + 1]->mid : MID_NOBODY;
            segments[i]->props[INWARDS_KEY].get_int() = inward;
            if (i > 0)
                segments[i - 1]->props[OUTWARDS_KEY].get_int() = segments[i]->mid;
        }

        head->props[INWARDS_KEY].get_int() =
            segments.empty() ? MID_NOBODY : segments[0]->mid;
        return head;
    }

private:
    bool old_test;
    mid_t old_last_mid;
    int old_max_mon_index;
    map<mid_t, unsigned short> old_mid_cache;
    vector<saved_tentacle_cell> cells;
    vector<monster *> registered;
    vector<mid_t> owned_mids;
};

vector<coord_def> corridor_body()
{
    return {TIP_POS, OUTER_SEGMENT_POS, INNER_SEGMENT_POS};
}

// Follows the body inwards from the head; every link must be an adjacent
// monster of this body and the walk must end at @p base. Returns the number of
// monsters in the chain (the head included), or 0 if the chain is broken or
// leads through a monster that is not part of this body.
size_t checked_body_length(const monster &head, const coord_def &base)
{
    size_t length = 1;
    coord_def pos = head.pos();
    mid_t inward = head.props[INWARDS_KEY].get_int();
    while (inward != MID_NOBODY)
    {
        const monster *segment = monster_by_mid(inward);
        REQUIRE(segment != nullptr);
        // Would be a body grafted onto something that is not this tentacle.
        if (segment->tentacle_connect != head.mid)
            return 0;
        CHECK(grid_distance(pos, segment->pos()) == 1);
        pos = segment->pos();
        if (!segment->props.exists(INWARDS_KEY))
            return 0;
        inward = segment->props[INWARDS_KEY].get_int();
        ++length;
    }
    return pos == base ? length : 0;
}

// Is a living body segment anchored on @p head left in the level?
bool has_live_body_segment(const monster &head)
{
    for (monster_iterator mi; mi; ++mi)
        if (mi->alive() && mi->tentacle_connect == head.mid)
            return true;
    return false;
}

} // namespace

TEST_CASE_METHOD(MockPlayerYouTestsFixture,
                 "A tentacle body is never grafted onto a foreign monster",
                 "[single-file]")
{
    scoped_tentacle_arena arena;

    // The recorded base cell is occupied by something that is not part of this
    // tentacle. The body layout must not adopt it as its base segment: that
    // would rewrite the tentacle's links and leave a body that the next move
    // cannot walk.
    monster *vine = arena.build_solo_tentacle(MONS_SNAPLASHER_VINE,
                                              MONS_SNAPLASHER_VINE_SEGMENT,
                                              corridor_body(), BASE_POS);
    monster *intruder = arena.add_monster(MONS_RAT, BASE_POS);
    const mid_t intruder_mid = intruder->mid;

    move_solo_tentacle(vine);

    // The unrelated monster's connection props are untouched.
    CHECK_FALSE(intruder->props.exists(INWARDS_KEY));
    CHECK_FALSE(intruder->props.exists(OUTWARDS_KEY));

    // The vine is either removed by the existing cleanup or keeps a body that
    // really leads to its base; it is never linked through the intruder.
    CHECK(vine->props[INWARDS_KEY].get_int() != intruder_mid);
    if (vine->alive())
        CHECK(checked_body_length(*vine, BASE_POS) > 0);
    else
        CHECK_FALSE(has_live_body_segment(*vine));
}

TEST_CASE_METHOD(MockPlayerYouTestsFixture,
                 "A healthy vine body is laid out to its base and stays put",
                 "[single-file]")
{
    scoped_tentacle_arena arena;

    monster *vine = arena.build_solo_tentacle(MONS_SNAPLASHER_VINE,
                                              MONS_SNAPLASHER_VINE_SEGMENT,
                                              corridor_body(), BASE_POS);
    // A bystander monster far away from the corridor must stay untouched.
    monster *bystander = arena.add_monster(MONS_RAT,
                                          coord_def(ARENA_MAX.x - 1,
                                                    ARENA_MIN.y + 1));
    const coord_def root = vine->props[BASE_POSITION_KEY].get_coord();
    CHECK(root == BASE_POS);

    move_solo_tentacle(vine);

    REQUIRE(vine->alive());
    // The anchored base is unchanged and the re-laid body reaches it within the
    // layout's distance budget.
    CHECK(vine->props[BASE_POSITION_KEY].get_coord() == root);
    const size_t length = checked_body_length(*vine, root);
    CHECK(length >= 2);
    CHECK(length <= MAX_EXPECTED_BODY);

    // No unrelated monster was touched by the layout.
    CHECK_FALSE(bystander->props.exists(INWARDS_KEY));
    CHECK_FALSE(bystander->props.exists(OUTWARDS_KEY));

    // The connectors this case produced are owned by the arena and are removed
    // again, so the fixture's monster indices stay consistent.
    arena.cleanup_production_bodies();
    CHECK_FALSE(has_live_body_segment(*vine));
    // The cleanup only removes bodies owned by this arena's tentacles.
    CHECK(bystander->alive());
}

TEST_CASE_METHOD(MockPlayerYouTestsFixture,
                 "A partially built body is rolled back",
                 "[single-file]")
{
    scoped_tentacle_arena arena;

    // Two body segments mean the layout starts by placing the base connector
    // and only then fills the cells towards the tip.
    monster *vine = arena.build_solo_tentacle(MONS_SNAPLASHER_VINE,
                                              MONS_SNAPLASHER_VINE_SEGMENT,
                                              corridor_body(), BASE_POS);
    const mid_t vine_mid = vine->mid;

    // Reach the level's monster cap so that only one more monster can be
    // placed: the base connector is created, the next one is refused.
    arena.fill_monster_slots(MAX_MONSTERS - 2 - 3);
    CHECK(vine_mid != MID_NOBODY);

    move_solo_tentacle(vine);

    // Only the base connector could be placed before the cap refused the rest,
    // so the connection has to report failure: the existing cleanup removes the
    // tentacle and the already created connector is not left behind. (Before
    // the construction fix this case kept a live orphan body segment.)
    CHECK_FALSE(vine->alive());
    CHECK_FALSE(has_live_body_segment(*vine));
}

TEST_CASE_METHOD(MockPlayerYouTestsFixture,
                 "Child tentacles may still connect to their own head",
                 "[single-file]")
{
    scoped_tentacle_arena arena;

    // move_child_tentacles() passes the head itself as the end position; that
    // shared call site must keep working, since the head is a legitimate body
    // anchor rather than a foreign monster.
    monster *kraken = arena.add_monster(MONS_KRAKEN, TIP_POS);
    monster *tentacle = arena.add_monster(MONS_KRAKEN_TENTACLE, BASE_POS);
    tentacle->tentacle_connect = kraken->mid;
    monster *inner = arena.add_monster(MONS_KRAKEN_TENTACLE_SEGMENT,
                                       INNER_SEGMENT_POS);
    monster *outer = arena.add_monster(MONS_KRAKEN_TENTACLE_SEGMENT,
                                       OUTER_SEGMENT_POS);
    for (monster *segment : {inner, outer})
        segment->tentacle_connect = tentacle->mid;
    inner->props[INWARDS_KEY].get_int() = outer->mid;
    outer->props[INWARDS_KEY].get_int() = kraken->mid;
    inner->props[OUTWARDS_KEY].get_int() = tentacle->mid;
    outer->props[OUTWARDS_KEY].get_int() = inner->mid;
    tentacle->props[INWARDS_KEY].get_int() = inner->mid;

    move_child_tentacles(kraken);

    REQUIRE(tentacle->alive());
    // The body is anchored on the tentacle's own head, through adjacent body
    // segments only.
    coord_def pos = tentacle->pos();
    mid_t inward = tentacle->props[INWARDS_KEY].get_int();
    size_t links = 0;
    while (inward != MID_NOBODY && inward != kraken->mid
           && links++ < MAX_EXPECTED_BODY)
    {
        const monster *segment = monster_by_mid(inward);
        REQUIRE(segment != nullptr);
        CHECK(segment->tentacle_connect == tentacle->mid);
        CHECK(grid_distance(pos, segment->pos()) == 1);
        pos = segment->pos();
        inward = segment->props[INWARDS_KEY].get_int();
    }
    CHECK(inward == kraken->mid);
}
