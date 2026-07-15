#pragma once

#include "coord.h"
#include "beam-type.h"
#include "dungeon-feature-type.h"
#include "externs.h"
#include "spell-type.h"

#include <cstdint>
#include <string>

class monster;
struct bolt;

enum class resolved_beam_status
{
    RESOLVED,
    NON_TARGETED,
    INVALID,
};

// Owned Phase 0 snapshot of every public bolt input that can participate in
// get_short_name(), plus its already-resolved legacy display. ranged_atk is
// intentionally represented only as presence: this seam never retains it.
struct resolved_beam
{
    resolved_beam();

    resolved_beam_status status;
    std::string display_text;
    std::string configured_name_en;
    std::string configured_short_name_en;
    spell_type origin_spell;
    beam_type flavour;
    beam_type real_flavour;
    bool pierces;
    bool has_ranged_attack;
};

resolved_beam resolve_speech_beam(const bolt &pbolt, bool targeted);

enum class speech_target_relation
{
    AT,
    NEXT_TO,
    PAST,
};

enum class speech_target_kind
{
    PLAYER,
    SELF,
    MONSTER,
    FEATURE,
    THIN_AIR,
    INDEFINITE,
    ERROR,
};

enum class speech_target_source
{
    UNRESOLVED,
    DIRECT_TARGET,
    ADJACENT_SPOT,
    TRACER_PATH,
    PAST_SCAN,
    FOE_FALLBACK,
    FINAL_FALLBACK,
};

struct resolved_speech_target
{
    resolved_speech_target();

    speech_target_relation relation;
    speech_target_kind kind;
    speech_target_source source;
    std::string preposition_display;
    std::string display;
    coord_def position;
    mid_t mid;
    dungeon_feature_type feature;
    std::string error;
};

enum class speech_target_observer_event_kind
{
    FIRE_TRACER,
    ADJACENT_RESERVOIR,
    PAST_RESERVOIR,
};

// POD event: observers see already-completed calls and never choose again.
struct speech_target_observer_event
{
    speech_target_observer_event_kind kind;
    int bound;
    int selected;
    uint64_t rng_state_before;
    uint64_t rng_state_after;
    uint64_t rng_count_before;
    uint64_t rng_count_after;
};

using speech_target_observer_fn =
    void (*)(const speech_target_observer_event &, void *);

// Observer callbacks are diagnostic only: they must not throw or consume game
// RNG. A default-constructed observer is disabled and has no runtime cost.
struct speech_target_observer
{
    speech_target_observer_fn function = nullptr;
    void *context = nullptr;
};

// Phase 0 typed seam. The production caller remains a compatibility adapter.
resolved_speech_target resolve_speech_target(
    const monster *mons, const bolt &pbolt, bool gestured,
    const speech_target_observer *observer = nullptr);
