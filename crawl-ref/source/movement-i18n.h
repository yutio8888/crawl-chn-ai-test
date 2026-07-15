#pragma once

#include "debug.h"
#include "i18n.h"
#include "stringutil.h"

// Chinese movement verbs need different directional complements depending on
// the grammar of the surrounding sentence. Keep the runtime verb in English
// and translate it only at the final display sink with one of these contexts.
enum class move_phrase_context
{
    bare,
    enter_area,
    onto_surface,
    onto_actor,
    through_obstacle,
    toward_target,
    over_terrain,
    num_contexts,
};

static_assert(static_cast<int>(move_phrase_context::over_terrain) + 1
              == static_cast<int>(move_phrase_context::num_contexts),
              "move phrase contexts must remain contiguous");

inline const char* move_phrase_context_key(move_phrase_context context)
{
    switch (context)
    {
    case move_phrase_context::bare:
        return "move.bare";
    case move_phrase_context::enter_area:
        return "move.enter-area";
    case move_phrase_context::onto_surface:
        return "move.onto-surface";
    case move_phrase_context::onto_actor:
        return "move.onto-actor";
    case move_phrase_context::through_obstacle:
        return "move.through-obstacle";
    case move_phrase_context::toward_target:
        return "move.toward-target";
    case move_phrase_context::over_terrain:
        return "move.over-terrain";
    case move_phrase_context::num_contexts:
        break;
    }

    die("invalid move phrase context: %d", static_cast<int>(context));
}

inline const char* translated_move_phrase(const char* english_verb,
                                           move_phrase_context context)
{
    return C_(move_phrase_context_key(context), english_verb);
}

// Prompt variants for movement that may be forced by another action. Keeping
// these complete sentences together avoids treating uncertainty and backward
// motion as an ordinary move verb, and makes every branch directly testable.
enum class possible_forced_prompt_context
{
    cloud,
    zot_trap,
    onto_trap,
    into_trap,
    binding_sigil,
    toxic_bog,
    exclusion,
    over_losing_buoyancy,
    into_losing_buoyancy,
    over_expiring_transformation,
    into_expiring_transformation,
    num_contexts,
};

static_assert(
    static_cast<int>(possible_forced_prompt_context::into_expiring_transformation) + 1
        == static_cast<int>(possible_forced_prompt_context::num_contexts),
    "possible forced prompt contexts must remain contiguous");

inline string possible_forced_move_prompt(
    possible_forced_prompt_context context, const char* subject = "")
{
    switch (context)
    {
    case possible_forced_prompt_context::cloud:
        return make_stringf(T_("This might make you stumble backwards into "
                               "that cloud of %s. Continue?"), subject);
    case possible_forced_prompt_context::zot_trap:
        return T_("This might make you stumble backwards into the Zot trap. "
                  "Continue?");
    case possible_forced_prompt_context::onto_trap:
        return make_stringf(T_("This might make you stumble backwards onto "
                               "that %s. Continue?"), subject);
    case possible_forced_prompt_context::into_trap:
        return make_stringf(T_("This might make you stumble backwards into "
                               "that %s. Continue?"), subject);
    case possible_forced_prompt_context::binding_sigil:
        return T_("This might make you stumble backwards onto a binding "
                  "sigil. Continue?");
    case possible_forced_prompt_context::toxic_bog:
        return T_("This might make you stumble backwards into a toxic bog. "
                  "Continue?");
    case possible_forced_prompt_context::exclusion:
        return T_("This might make you stumble backwards into a "
                  "travel-excluded area. Continue?");
    case possible_forced_prompt_context::over_losing_buoyancy:
        return make_stringf(T_("This might make you stumble backwards over %s "
                               "while you are losing your buoyancy. Continue?"),
                            subject);
    case possible_forced_prompt_context::into_losing_buoyancy:
        return make_stringf(T_("This might make you stumble backwards into %s "
                               "while you are losing your buoyancy. Continue?"),
                            subject);
    case possible_forced_prompt_context::over_expiring_transformation:
        return make_stringf(T_("This might make you stumble backwards over %s "
                               "while your transformation is expiring. Continue?"),
                            subject);
    case possible_forced_prompt_context::into_expiring_transformation:
        return make_stringf(T_("This might make you stumble backwards into %s "
                               "while your transformation is expiring. Continue?"),
                            subject);
    case possible_forced_prompt_context::num_contexts:
        break;
    }

    die("invalid possible forced prompt context: %d",
        static_cast<int>(context));
}
