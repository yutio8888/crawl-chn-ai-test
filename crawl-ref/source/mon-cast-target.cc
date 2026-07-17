/**
 * @file
 * @brief Typed target and beam resolution for monster cast messages.
 **/

#include "AppHdr.h"

#include "mon-cast-target.h"

#include "actor.h"
#include "beam.h"
#include "coordit.h"
#include "directn.h"
#include "env.h"
#include "i18n.h"
#include "mon-util.h"
#include "monster.h"
#include "player.h"
#include "random.h"
#include "state.h"
#include "stringutil.h"
#include "terrain.h"

resolved_speech_actor resolve_speech_actor(const monster &mons)
{
    description_level_type desc = DESC_THE;
    if (mons.attitude == ATT_FRIENDLY
        && !mons_is_unique(mons.type)
        && !crawl_state.game_is_arena()
        && you.can_see(mons))
    {
        desc = DESC_YOUR;
    }

    resolved_speech_actor result;
    result.lower_display = mons.name(desc);
    result.sentence_display = mons.is_named() && you.can_see(mons)
        ? result.lower_display : uppercase_first(result.lower_display);
    return result;
}

resolved_speech_target::resolved_speech_target()
    : relation(speech_target_relation::AT),
      kind(speech_target_kind::ERROR),
      source(speech_target_source::UNRESOLVED),
      preposition_display(T_("at")),
      display("nothing"),
      position(INVALID_COORD),
      mid(MID_NOBODY),
      feature(DNGN_UNSEEN)
{
}

resolved_speech_target resolve_speech_target(
    const monster* mons, const bolt& pbolt, bool gestured,
    const speech_target_observer *observer)
{
    resolved_speech_target result;
    bool is_at_prep = true;

    bolt tracer_beam = pbolt;
    targeting_tracer tracer;
    // For a targeted but rangeless spell make the range positive so that
    // fire_tracer() will fill out path_taken.
    if (pbolt.range == 0 && pbolt.target != mons->pos())
        tracer_beam.range = ENV_SHOW_DIAMETER;
    uint64_t tracer_state_before = 0;
    uint64_t tracer_count_before = 0;
    if (observer && observer->function)
    {
        tracer_state_before = rng::current_generator().get_state();
        tracer_count_before = rng::current_generator().get_count();
    }
    fire_tracer(mons, tracer, tracer_beam);
    if (observer && observer->function)
    {
        speech_target_observer_event event;
        event.kind = speech_target_observer_event_kind::FIRE_TRACER;
        event.bound = 0;
        event.selected = 0;
        event.rng_state_before = tracer_state_before;
        event.rng_count_before = tracer_count_before;
        event.rng_state_after = rng::current_generator().get_state();
        event.rng_count_after = rng::current_generator().get_count();
        observer->function(event, observer->context);
    }

    if (pbolt.target == you.pos())
    {
        result.kind = speech_target_kind::PLAYER;
        result.source = speech_target_source::DIRECT_TARGET;
        result.display = T_("you");
        result.position = you.pos();
        result.mid = you.mid;
    }
    else if (pbolt.target == mons->pos())
    {
        result.kind = speech_target_kind::SELF;
        result.source = speech_target_source::DIRECT_TARGET;
        result.display = mons->pronoun(PRONOUN_REFLEXIVE);
        result.position = mons->pos();
        result.mid = mons->mid;
    }
    // Monsters should only use targeted spells while foe == MHITNOT
    // if they're targeting themselves.
    else if (mons->foe == MHITNOT && !mons_is_confused(*mons, true))
    {
        result.kind = speech_target_kind::ERROR;
        result.source = speech_target_source::DIRECT_TARGET;
        result.display = "NONEXISTENT FOE";
        result.error = result.display;
    }
    else if (!invalid_monster_index(mons->foe)
             && env.mons[mons->foe].type == MONS_NO_MONSTER)
    {
        result.kind = speech_target_kind::ERROR;
        result.source = speech_target_source::DIRECT_TARGET;
        result.display = "DEAD FOE";
        result.error = result.display;
    }
    else if (in_bounds(pbolt.target) && you.see_cell(pbolt.target))
    {
        if (const monster* mtarg = monster_at(pbolt.target))
        {
            if (you.can_see(*mtarg))
            {
                result.kind = speech_target_kind::MONSTER;
                result.source = speech_target_source::DIRECT_TARGET;
                result.display = mtarg->name(DESC_THE);
                result.position = mtarg->pos();
                result.mid = mtarg->mid;
            }
        }
    }

    const bool visible_path      = pbolt.visible() || gestured;

    // Monster might be aiming past the real target, or maybe some fuzz has
    // been applied because the target is invisible.
    if (result.display == "nothing")
    {
        if (pbolt.aimed_at_spot || pbolt.origin_spell == SPELL_DIG)
        {
            int count = 0;
            for (adjacent_iterator ai(pbolt.target); ai; ++ai)
            {
                const actor* act = actor_at(*ai);
                if (act && act != mons && you.can_see(*act))
                {
                    result.relation = speech_target_relation::NEXT_TO;
                    result.preposition_display = T_("next to");
                    is_at_prep = false;

                    bool selected = act->is_player();
                    if (!selected)
                    {
                        const int bound = ++count;
                        uint64_t state_before = 0;
                        uint64_t count_before = 0;
                        if (observer && observer->function)
                        {
                            state_before = rng::current_generator().get_state();
                            count_before = rng::current_generator().get_count();
                        }
                        selected = one_chance_in(bound);
                        if (observer && observer->function)
                        {
                            speech_target_observer_event event;
                            event.kind = speech_target_observer_event_kind::
                                ADJACENT_RESERVOIR;
                            event.bound = bound;
                            event.selected = selected;
                            event.rng_state_before = state_before;
                            event.rng_count_before = count_before;
                            event.rng_state_after =
                                rng::current_generator().get_state();
                            event.rng_count_after =
                                rng::current_generator().get_count();
                            observer->function(event, observer->context);
                        }
                    }
                    if (selected)
                    {
                        result.kind = act->is_player()
                            ? speech_target_kind::PLAYER
                            : speech_target_kind::MONSTER;
                        result.source = speech_target_source::ADJACENT_SPOT;
                        result.display = act->name(DESC_THE);
                        result.position = act->pos();
                        result.mid = act->mid;
                    }

                    if (act->is_player())
                        break;
                }
            }

            if (is_at_prep)
            {
                if (env.grid(pbolt.target) != DNGN_FLOOR)
                {
                    result.kind = speech_target_kind::FEATURE;
                    result.source = speech_target_source::ADJACENT_SPOT;
                    result.feature = env.grid(pbolt.target);
                    result.position = pbolt.target;
                    result.display = feature_description(
                        result.feature, NUM_TRAPS, "", DESC_THE);
                }
                else
                {
                    result.kind = speech_target_kind::THIN_AIR;
                    result.source = speech_target_source::ADJACENT_SPOT;
                    result.position = pbolt.target;
                    result.display = T_("thin air");
                }
            }

            return result;
        }

        bool mons_targ_aligned = false;

        for (const coord_def &pos : tracer_beam.path_taken)
        {
            if (pos == mons->pos())
                continue;

            const monster* m = monster_at(pos);
            if (pos == you.pos())
            {
                // Be egotistical and assume that the monster is aiming at
                // the player, rather than the player being in the path of
                // a beam aimed at an ally.
                if (!mons->wont_attack())
                {
                    result.relation = speech_target_relation::AT;
                    result.preposition_display = T_("at");
                    is_at_prep = true;
                    result.kind = speech_target_kind::PLAYER;
                    result.source = speech_target_source::TRACER_PATH;
                    result.display = T_("you");
                    result.position = you.pos();
                    result.mid = you.mid;
                    break;
                }
                // If the ally is confused or aiming at an invisible enemy,
                // with the player in the path, act like it's targeted at
                // the player if there isn't any visible target earlier
                // in the path.
                else if (result.display == "nothing")
                {
                    result.relation = speech_target_relation::AT;
                    result.preposition_display = T_("at");
                    is_at_prep = true;
                    result.kind = speech_target_kind::PLAYER;
                    result.source = speech_target_source::TRACER_PATH;
                    result.display = T_("you");
                    result.position = you.pos();
                    result.mid = you.mid;
                    mons_targ_aligned = true;
                }
            }
                else if (visible_path && m && you.can_see(*m))
            {
                bool is_aligned  = mons_aligned(m, mons);
                string name = m->name(DESC_THE);

                if (result.display == "nothing")
                {
                    mons_targ_aligned = is_aligned;
                    result.kind = speech_target_kind::MONSTER;
                    result.source = speech_target_source::TRACER_PATH;
                    result.display = name;
                    result.position = m->pos();
                    result.mid = m->mid;
                }
                // If the first target was aligned with the beam source then
                // the first subsequent non-aligned monster in the path will
                // take it's place.
                else if (mons_targ_aligned && !is_aligned)
                {
                    mons_targ_aligned = false;
                    result.kind = speech_target_kind::MONSTER;
                    result.source = speech_target_source::TRACER_PATH;
                    result.display = name;
                    result.position = m->pos();
                    result.mid = m->mid;
                }
                result.relation = speech_target_relation::AT;
                result.preposition_display = T_("at");
                is_at_prep = true;
            }
            else if (visible_path && result.display == "nothing")
            {
                int count = 0;
                for (adjacent_iterator ai(pbolt.target); ai; ++ai)
                {
                    const actor* act = monster_at(*ai);
                    if (act && act != mons && you.can_see(*act))
                    {
                        result.relation = speech_target_relation::PAST;
                        result.preposition_display = T_("past");
                        is_at_prep = false;
                        bool selected = act->is_player();
                        if (!selected)
                        {
                            const int bound = ++count;
                            uint64_t state_before = 0;
                            uint64_t count_before = 0;
                            if (observer && observer->function)
                            {
                                state_before =
                                    rng::current_generator().get_state();
                                count_before =
                                    rng::current_generator().get_count();
                            }
                            selected = one_chance_in(bound);
                            if (observer && observer->function)
                            {
                                speech_target_observer_event event;
                                event.kind = speech_target_observer_event_kind::
                                    PAST_RESERVOIR;
                                event.bound = bound;
                                event.selected = selected;
                                event.rng_state_before = state_before;
                                event.rng_count_before = count_before;
                                event.rng_state_after =
                                    rng::current_generator().get_state();
                                event.rng_count_after =
                                    rng::current_generator().get_count();
                                observer->function(event, observer->context);
                            }
                        }
                        if (selected)
                        {
                            result.kind = act->is_player()
                                ? speech_target_kind::PLAYER
                                : speech_target_kind::MONSTER;
                            result.source = speech_target_source::PAST_SCAN;
                            result.display = act->name(DESC_THE);
                            result.position = act->pos();
                            result.mid = act->mid;
                        }

                        if (act->is_player())
                            break;
                    }
                }
            }
        } // for (const coord_def pos : path)
    } // if (target == "nothing" && targeted)

    const actor* foe = mons->get_foe();

    // If we still can't find what appears to be the target, and the
    // monster isn't just throwing the spell in a random direction,
    // we should be able to tell what the monster was aiming for if
    // we can see the monster's foe and the beam (or the beam path
    // implied by gesturing). But only if the beam didn't actually hit
    // anything (but if it did hit something, why didn't that monster
    // show up in the beam's path?)
    if (result.display == "nothing"
        && (tracer.foe_info.count + tracer.friend_info.count) == 0
        && foe != nullptr
        && you.can_see(*foe)
        && !mons->confused()
        && visible_path)
    {
        result.kind = foe->is_player() ? speech_target_kind::PLAYER
                                       : speech_target_kind::MONSTER;
        result.source = speech_target_source::FOE_FALLBACK;
        result.display = foe->name(DESC_THE);
        result.position = foe->pos();
        result.mid = foe->mid;
        result.relation = pbolt.aimed_at_spot
            ? speech_target_relation::NEXT_TO : speech_target_relation::PAST;
        result.preposition_display =
            (pbolt.aimed_at_spot ? T_("next to") : T_("past"));
        is_at_prep = false;
    }

    // If the monster gestures to create an invisible beam then
    // assume that anything close to the beam is the intended target.
    // Also, if the monster gestures to create a visible beam but it
    // misses still say that the monster gestured "at" the target,
    // rather than "past".
    if (gestured || result.display == "nothing")
    {
        result.relation = speech_target_relation::AT;
        result.preposition_display = T_("at");
        is_at_prep = true;
    }

    // "throws whatever at something" is better than "at nothing"
    if (result.display == "nothing")
    {
        result.kind = speech_target_kind::INDEFINITE;
        result.source = speech_target_source::FINAL_FALLBACK;
        result.display = T_("something");
    }
    return result;
}

resolved_beam::resolved_beam()
    : status(resolved_beam_status::INVALID),
      display_text("INVALID BEAM"),
      origin_spell(SPELL_NO_SPELL),
      flavour(BEAM_MAGIC),
      real_flavour(BEAM_MAGIC),
      pierces(false),
      has_ranged_attack(false)
{
}

resolved_beam resolve_speech_beam(const bolt &pbolt, bool targeted)
{
    resolved_beam result;
    result.configured_name_en = pbolt.name;
    result.configured_short_name_en = pbolt.short_name;
    result.origin_spell = pbolt.origin_spell;
    result.flavour = pbolt.flavour;
    result.real_flavour = pbolt.real_flavour;
    result.pierces = pbolt.pierce;
    result.has_ranged_attack = pbolt.ranged_atk != nullptr;

    // Preserve the legacy branch order: in particular, get_short_name() is
    // never evaluated for non-targeted or invalid beams.
    if (!targeted)
    {
        result.status = resolved_beam_status::NON_TARGETED;
        result.display_text = "NON TARGETED BEAM";
    }
    else if (pbolt.name.empty())
    {
        result.status = resolved_beam_status::INVALID;
        result.display_text = "INVALID BEAM";
    }
    else
    {
        result.status = resolved_beam_status::RESOLVED;
        result.display_text = pbolt.get_short_name();
    }
    return result;
}
