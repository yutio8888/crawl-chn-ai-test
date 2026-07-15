#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "beam.h"
#include "coordit.h"
#include "env.h"
#include "feature.h"
#include "losglobal.h"
#include "mon-cast-target.h"
#include "mon-ench.h"
#include "mon-place.h"
#include "mon-util.h"
#include "monster.h"
#include "player.h"
#include "random.h"
#include "state.h"
#include "spl-util.h"

#include "test_player_fixture.h"

namespace
{
struct saved_cell
{
    coord_def position;
    dungeon_feature_type feature;
    unsigned short monster_index;
};

class scoped_target_world
{
public:
    scoped_target_world()
        : old_test(crawl_state.test), old_player_position(you.pos())
    {
        crawl_state.test = true;
        for (int x = 15; x <= 30; ++x)
        {
            for (int y = 15; y <= 30; ++y)
            {
                const coord_def position(x, y);
                cells.push_back({ position, env.grid(position),
                                  env.mgrid(position) });
                env.grid(position) = DNGN_FLOOR;
                env.mgrid(position) = NON_MONSTER;
            }
        }
        you.set_position(coord_def(20, 22));
    }

    ~scoped_target_world()
    {
        you.set_position(old_player_position);
        for (const saved_cell &cell : cells)
        {
            env.grid(cell.position) = cell.feature;
            env.mgrid(cell.position) = cell.monster_index;
        }
        crawl_state.test = old_test;
    }

private:
    bool old_test;
    coord_def old_player_position;
    vector<saved_cell> cells;
};

class scoped_past_target_world
{
public:
    scoped_past_target_world()
        : old_test(crawl_state.test), old_player_position(you.pos()),
          old_on_current_level(you.on_current_level),
          old_current_vision(you.current_vision),
          old_wizard_vision(you.wizard_vision),
          old_last_mid(you.last_mid), old_max_mon_index(env.max_mon_index),
          old_mid_cache(env.mid_cache),
          parent_state_before(rng::current_generator().get_state()),
          parent_count_before(rng::current_generator().get_count())
    {
        crawl_state.test = true;
        you.on_current_level = true;
        you.current_vision = LOS_DEFAULT_RANGE;
        // The lightweight player fixture has no populated global LOS cache.
        // Wizard vision still exercises the production you.can_see(actor)
        // predicate while making the fixture independent of level startup.
        you.wizard_vision = true;

        for (int x = 15; x <= 30; ++x)
        {
            for (int y = 15; y <= 30; ++y)
            {
                const coord_def position(x, y);
                cells.push_back({ position, env.grid(position),
                                  env.mgrid(position) });
                env.grid(position) = DNGN_FLOOR;
                env.mgrid(position) = NON_MONSTER;
            }
        }
        you.set_position(coord_def(18, 25));
        invalidate_los();

        {
            rng::subgenerator placement_rng(0x81f3a2964c5d7e08ULL,
                                             0x17395bdf2468ace0ULL);
            // Catch2 randomises test order, so the monster data lookup table
            // may not yet have been initialised by another fixture.
            init_show_table();
            init_monsters();
            init_spell_descs();
            source = add_monster(MONS_ORC, coord_def(20, 20));
            candidates.push_back(add_monster(MONS_RAT, coord_def(25, 22)));
            candidates.push_back(add_monster(MONS_RAT, coord_def(25, 24)));
        }

        parent_state_after = rng::current_generator().get_state();
        parent_count_after = rng::current_generator().get_count();
        invalidate_los();
    }

    ~scoped_past_target_world()
    {
        for (monster *candidate : registered_monsters)
        {
            if (candidate && candidate->type != MONS_NO_MONSTER)
            {
                candidate->destroy_inventory();
                env.mid_cache.erase(candidate->mid);
                candidate->reset();
            }
        }

        you.set_position(old_player_position);
        you.on_current_level = old_on_current_level;
        you.current_vision = old_current_vision;
        you.wizard_vision = old_wizard_vision;
        you.last_mid = old_last_mid;
        for (const saved_cell &cell : cells)
        {
            env.grid(cell.position) = cell.feature;
            env.mgrid(cell.position) = cell.monster_index;
        }
        env.max_mon_index = old_max_mon_index;
        env.mid_cache = old_mid_cache;
        crawl_state.test = old_test;
        invalidate_los();
    }

    bool valid() const
    {
        return candidates.size() == 2
            && source != nullptr
            && candidates[0] != nullptr && candidates[1] != nullptr
            && source->pos() == coord_def(20, 20)
            && candidates[0]->pos() == coord_def(25, 22)
            && candidates[1]->pos() == coord_def(25, 24);
    }

    bool parent_rng_preserved() const
    {
        return parent_state_before == parent_state_after
            && parent_count_before == parent_count_after;
    }

    const vector<monster *> &placed_candidates() const
    {
        return candidates;
    }

    monster *placed_source() const
    {
        return source;
    }

private:
    monster *add_monster(monster_type type, const coord_def &position)
    {
        // The lightweight Catch2 player fixture has no fully constructed
        // level, so create_monster() can legitimately reject placement. Use
        // the production monster-slot allocator and register the minimum real
        // actor state needed by monster_at(), LOS and the tracer instead.
        monster *candidate = get_free_monster();
        if (!candidate)
            return nullptr;

        candidate->type = type;
        candidate->set_hit_dice(1);
        candidate->hit_points = candidate->max_hit_points = 5;
        candidate->speed = 10;
        candidate->attitude = ATT_HOSTILE;
        candidate->behaviour = BEH_SEEK;
        candidate->foe = MHITYOU;
        candidate->set_position(position);
        candidate->set_new_monster_id();
        env.mgrid(position) = candidate->mindex();
        registered_monsters.push_back(candidate);
        return candidate;
    }

    bool old_test;
    coord_def old_player_position;
    bool old_on_current_level;
    uint8_t old_current_vision;
    bool old_wizard_vision;
    mid_t old_last_mid;
    int old_max_mon_index;
    map<mid_t, unsigned short> old_mid_cache;
    uint64_t parent_state_before;
    uint64_t parent_count_before;
    uint64_t parent_state_after;
    uint64_t parent_count_after;
    vector<saved_cell> cells;
    monster *source = nullptr;
    vector<monster *> candidates;
    vector<monster *> registered_monsters;
};

monster make_source_monster()
{
    monster source;
    source.type = MONS_ORC;
    source.set_hit_dice(1);
    source.hit_points = 10;
    source.max_hit_points = 10;
    source.speed = 10;
    source.mid = 1234;
    source.foe = MHITYOU;
    source.attitude = ATT_HOSTILE;
    source.set_position(coord_def(20, 20));
    return source;
}

bolt make_target_beam(const coord_def &target)
{
    bolt beam;
    beam.name = "Phase 0 target seam tracer";
    beam.range = 8;
    beam.target = target;
    beam.hit = AUTOMATIC_HIT;
    beam.damage = dice_def(1, 1);
    beam.flavour = BEAM_MAGIC;
    beam.thrower = KILL_MON_MISSILE;
    return beam;
}

void observe_target_event(const speech_target_observer_event &event,
                          void *context)
{
    static_cast<vector<speech_target_observer_event> *>(context)
        ->push_back(event);
}

bool same_target(const resolved_speech_target &lhs,
                 const resolved_speech_target &rhs)
{
    return lhs.relation == rhs.relation
        && lhs.kind == rhs.kind
        && lhs.source == rhs.source
        && lhs.preposition_display == rhs.preposition_display
        && lhs.display == rhs.display
        && lhs.position == rhs.position
        && lhs.mid == rhs.mid
        && lhs.feature == rhs.feature
        && lhs.error == rhs.error;
}

}

TEST_CASE("speech target typed value has safe owning defaults",
          "[single-file][mon-cast-target][phase0]")
{
    const resolved_speech_target target;
    CHECK(target.relation == speech_target_relation::AT);
    CHECK(target.kind == speech_target_kind::ERROR);
    CHECK(target.source == speech_target_source::UNRESOLVED);
    CHECK(target.position == INVALID_COORD);
    CHECK(target.mid == MID_NOBODY);
    CHECK(target.feature == DNGN_UNSEEN);
    CHECK(target.error.empty());
    CHECK_FALSE(target.preposition_display.empty());
    CHECK(target.display == "nothing");
}

TEST_CASE("speech beam typed seam preserves all legacy branches and RNG",
          "[single-file][mon-cast-target][phase0]")
{
    bolt beam = make_target_beam(coord_def(24, 20));
    beam.name = "Phase 0 configured beam";
    beam.short_name = "Phase 0 short beam";
    beam.origin_spell = SPELL_MAGIC_DART;
    beam.flavour = BEAM_FIRE;
    beam.real_flavour = BEAM_CHAOS;
    beam.pierce = true;

    const auto resolve_without_rng =
        [&beam](bool targeted)
        {
            rng::subgenerator scoped_rng(0x71425364, 0x18273645);
            const uint64_t state_before =
                rng::current_generator().get_state();
            const uint64_t count_before =
                rng::current_generator().get_count();
            const resolved_beam result =
                resolve_speech_beam(beam, targeted);
            CHECK(rng::current_generator().get_state() == state_before);
            CHECK(rng::current_generator().get_count() == count_before);
            return result;
        };

    SECTION("valid targeted beam delegates to get_short_name")
    {
        const string legacy_display = beam.get_short_name();
        const resolved_beam result = resolve_without_rng(true);
        CHECK(result.status == resolved_beam_status::RESOLVED);
        CHECK(result.display_text == legacy_display);
        CHECK(result.configured_name_en == beam.name);
        CHECK(result.configured_short_name_en == beam.short_name);
        CHECK(result.origin_spell == beam.origin_spell);
        CHECK(result.flavour == beam.flavour);
        CHECK(result.real_flavour == beam.real_flavour);
        CHECK(result.pierces == beam.pierce);
        CHECK_FALSE(result.has_ranged_attack);

        beam.name = "mutated after resolution";
        beam.short_name = "also mutated";
        CHECK(result.configured_name_en == "Phase 0 configured beam");
        CHECK(result.configured_short_name_en == "Phase 0 short beam");
        CHECK(result.display_text == legacy_display);
    }

    SECTION("non-targeted beam keeps sentinel output")
    {
        const resolved_beam result = resolve_without_rng(false);
        CHECK(result.status == resolved_beam_status::NON_TARGETED);
        CHECK(result.display_text == "NON TARGETED BEAM");
    }

    SECTION("empty configured name remains invalid before short-name lookup")
    {
        beam.name.clear();
        // Legacy checks name before get_short_name(), even when short_name is
        // populated. Preserve that seemingly surprising ordering exactly.
        REQUIRE_FALSE(beam.short_name.empty());
        const resolved_beam result = resolve_without_rng(true);
        CHECK(result.status == resolved_beam_status::INVALID);
        CHECK(result.display_text == "INVALID BEAM");
        CHECK(result.configured_short_name_en == beam.short_name);
    }
}

TEST_CASE_METHOD(MockPlayerYouTestsFixture,
                 "speech target player and self use a real tracer",
                 "[single-file][mon-cast-target][phase0]")
{
    scoped_target_world world;
    monster source = make_source_monster();

    const bolt player_beam = make_target_beam(you.pos());
    resolved_speech_target unobserved;
    uint64_t unobserved_state;
    uint64_t unobserved_count;
    {
        rng::subgenerator scoped_rng(0x12345678, 0xabcdef01);
        unobserved = resolve_speech_target(&source, player_beam, false);
        unobserved_state = rng::current_generator().get_state();
        unobserved_count = rng::current_generator().get_count();
    }

    vector<speech_target_observer_event> events;
    const speech_target_observer observer =
        { observe_target_event, &events };
    resolved_speech_target observed;
    uint64_t observed_state;
    uint64_t observed_count;
    {
        rng::subgenerator scoped_rng(0x12345678, 0xabcdef01);
        observed = resolve_speech_target(&source, player_beam, false,
                                         &observer);
        observed_state = rng::current_generator().get_state();
        observed_count = rng::current_generator().get_count();
    }

    CHECK(same_target(unobserved, observed));
    CHECK(observed.kind == speech_target_kind::PLAYER);
    CHECK(observed.source == speech_target_source::DIRECT_TARGET);
    CHECK(observed.relation == speech_target_relation::AT);
    CHECK(observed.position == you.pos());
    CHECK(observed.mid == MID_PLAYER);
    CHECK(observed_state == unobserved_state);
    CHECK(observed_count == unobserved_count);
    REQUIRE(events.size() == 1);
    CHECK(events[0].kind == speech_target_observer_event_kind::FIRE_TRACER);
    CHECK(events[0].rng_state_before == events[0].rng_state_after);
    CHECK(events[0].rng_count_before == events[0].rng_count_after);

    speech_target_observer disabled_observer;
    CHECK(disabled_observer.function == nullptr);
    CHECK(disabled_observer.context == nullptr);
    uint64_t disabled_state;
    uint64_t disabled_count;
    resolved_speech_target disabled;
    {
        rng::subgenerator scoped_rng(0x12345678, 0xabcdef01);
        disabled = resolve_speech_target(&source, player_beam, false,
                                         &disabled_observer);
        disabled_state = rng::current_generator().get_state();
        disabled_count = rng::current_generator().get_count();
    }
    CHECK(same_target(unobserved, disabled));
    CHECK(disabled_state == unobserved_state);
    CHECK(disabled_count == unobserved_count);
    CHECK(events.size() == 1);

    const resolved_speech_target self = resolve_speech_target(
        &source, make_target_beam(source.pos()), false);
    CHECK(self.kind == speech_target_kind::SELF);
    CHECK(self.source == speech_target_source::DIRECT_TARGET);
    CHECK(self.position == source.pos());
    CHECK(self.mid == source.mid);
}

TEST_CASE_METHOD(MockPlayerYouTestsFixture,
                 "speech target adjacent spot resolves thin air",
                 "[single-file][mon-cast-target][phase0]")
{
    // PAST reservoir selection requires registered visible monsters and a
    // stable repeated tracer path; MockPlayer has no dungeon fixture, so this
    // slice deliberately does not fabricate that integration scenario.
    scoped_target_world world;
    monster source = make_source_monster();

    bolt player_adjacent = make_target_beam(coord_def(21, 22));
    player_adjacent.aimed_at_spot = true;
    const resolved_speech_target next_to_player =
        resolve_speech_target(&source, player_adjacent, false);
    CHECK(next_to_player.kind == speech_target_kind::PLAYER);
    CHECK(next_to_player.source == speech_target_source::ADJACENT_SPOT);
    CHECK(next_to_player.relation == speech_target_relation::NEXT_TO);
    CHECK(next_to_player.position == you.pos());
    CHECK(next_to_player.mid == MID_PLAYER);

    bolt beam = make_target_beam(coord_def(26, 20));
    beam.aimed_at_spot = true;
    const resolved_speech_target target =
        resolve_speech_target(&source, beam, false);
    CHECK(target.kind == speech_target_kind::THIN_AIR);
    CHECK(target.source == speech_target_source::ADJACENT_SPOT);
    CHECK(target.position == beam.target);
    CHECK(target.mid == MID_NOBODY);
    CHECK(target.feature == DNGN_UNSEEN);

    env.grid(beam.target) = DNGN_STONE_WALL;
    const resolved_speech_target feature =
        resolve_speech_target(&source, beam, false);
    CHECK(feature.kind == speech_target_kind::FEATURE);
    CHECK(feature.source == speech_target_source::ADJACENT_SPOT);
    CHECK(feature.position == beam.target);
    CHECK(feature.feature == DNGN_STONE_WALL);

    source.foe = MHITNOT;
    source.add_ench(mon_enchant(ENCH_CONFUSION, &source));
    bolt indefinite_beam = make_target_beam(coord_def(26, 21));
    indefinite_beam.glyph = 0;
    const resolved_speech_target indefinite =
        resolve_speech_target(&source, indefinite_beam, false);
    CHECK(indefinite.kind == speech_target_kind::INDEFINITE);
    CHECK(indefinite.source == speech_target_source::FINAL_FALLBACK);
    CHECK(indefinite.relation == speech_target_relation::AT);
    CHECK(indefinite.mid == MID_NOBODY);
}

TEST_CASE_METHOD(MockPlayerYouTestsFixture,
                 "speech target past scan reservoirs visible monsters",
                 "[single-file][mon-cast-target][phase0]")
{
    const bool test_before = crawl_state.test;
    const coord_def player_position_before = you.pos();
    const bool on_current_level_before = you.on_current_level;
    const uint8_t current_vision_before = you.current_vision;
    const bool wizard_vision_before = you.wizard_vision;
    const mid_t last_mid_before = you.last_mid;
    const int max_mon_index_before = env.max_mon_index;
    const map<mid_t, unsigned short> mid_cache_before = env.mid_cache;
    const uint64_t parent_state_before =
        rng::current_generator().get_state();
    const uint64_t parent_count_before =
        rng::current_generator().get_count();
    vector<saved_cell> cells_before;
    for (int x = 15; x <= 30; ++x)
    {
        for (int y = 15; y <= 30; ++y)
        {
            const coord_def position(x, y);
            cells_before.push_back({ position, env.grid(position),
                                     env.mgrid(position) });
        }
    }

    {
        scoped_past_target_world world;
        REQUIRE(world.valid());
        REQUIRE(world.parent_rng_preserved());

        const vector<monster *> &candidates = world.placed_candidates();
        for (const monster *candidate : candidates)
        {
            REQUIRE(monster_at(candidate->pos()) == candidate);
            REQUIRE(you.can_see(*candidate));
            for (int slot = 0; slot < NUM_MONSTER_SLOTS; ++slot)
                REQUIRE(candidate->inv[slot] == NON_ITEM);
        }

        monster *source = world.placed_source();
        REQUIRE(source != nullptr);
        bolt beam = make_target_beam(coord_def(25, 23));
        beam.range = grid_distance(source->pos(), beam.target);
        beam.source = source->pos();
        beam.source_id = source->mid;
        beam.glyph = '*';

        vector<const monster *> reservoir_order;
        for (adjacent_iterator ai(beam.target); ai; ++ai)
        {
            const monster *candidate = monster_at(*ai);
            if (candidate && candidate != source && you.can_see(*candidate))
                reservoir_order.push_back(candidate);
        }
        REQUIRE(reservoir_order.size() == 2);

        resolved_speech_target unobserved;
        uint64_t unobserved_state;
        uint64_t unobserved_count;
        {
            rng::subgenerator scoped_rng(0x6a09e667f3bcc909ULL,
                                         0xbb67ae8584caa73bULL);
            unobserved = resolve_speech_target(source, beam, false);
            unobserved_state = rng::current_generator().get_state();
            unobserved_count = rng::current_generator().get_count();
        }

        vector<speech_target_observer_event> events;
        const speech_target_observer observer =
            { observe_target_event, &events };
        resolved_speech_target observed;
        uint64_t observed_state;
        uint64_t observed_count;
        {
            rng::subgenerator scoped_rng(0x6a09e667f3bcc909ULL,
                                         0xbb67ae8584caa73bULL);
            observed = resolve_speech_target(source, beam, false, &observer);
            observed_state = rng::current_generator().get_state();
            observed_count = rng::current_generator().get_count();
        }

        CHECK(same_target(unobserved, observed));
        CHECK(observed_state == unobserved_state);
        CHECK(observed_count == unobserved_count);
        CHECK(observed.kind == speech_target_kind::MONSTER);
        CHECK(observed.source == speech_target_source::PAST_SCAN);
        CHECK(observed.relation == speech_target_relation::PAST);

        int tracer_events = 0;
        vector<speech_target_observer_event> past_events;
        for (const speech_target_observer_event &event : events)
        {
            if (event.kind == speech_target_observer_event_kind::FIRE_TRACER)
                ++tracer_events;
            else if (event.kind
                     == speech_target_observer_event_kind::PAST_RESERVOIR)
            {
                past_events.push_back(event);
            }
        }
        CHECK(tracer_events == 1);
        REQUIRE(past_events.size() == 2);
        CHECK(past_events[0].bound == 1);
        CHECK(past_events[0].selected == 1);
        CHECK(past_events[1].bound == 2);

        const monster *expected = past_events[1].selected
            ? reservoir_order[1] : reservoir_order[0];
        CHECK(observed.mid == expected->mid);
        CHECK(observed.position == expected->pos());
    }

    CHECK(crawl_state.test == test_before);
    CHECK(you.pos() == player_position_before);
    CHECK(you.on_current_level == on_current_level_before);
    CHECK(you.current_vision == current_vision_before);
    CHECK(you.wizard_vision == wizard_vision_before);
    CHECK(you.last_mid == last_mid_before);
    CHECK(env.max_mon_index == max_mon_index_before);
    CHECK((env.mid_cache == mid_cache_before));
    CHECK(rng::current_generator().get_state() == parent_state_before);
    CHECK(rng::current_generator().get_count() == parent_count_before);
    for (const saved_cell &cell : cells_before)
    {
        CHECK(env.grid(cell.position) == cell.feature);
        CHECK(env.mgrid(cell.position) == cell.monster_index);
    }
}
