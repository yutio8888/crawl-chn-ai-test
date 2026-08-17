/**
 * @file
 * @brief Functions to handle speaking monsters
**/

#pragma once

#include "mpr.h"

struct mon_speech_final_emission
{
    mon_speech_final_emission(monster *source_, const string &line_,
                              msg_channel_type channel_,
                              bool effective_silence_,
                              bool already_rendered_)
        : source(source_), line(line_), channel(channel_),
          effective_silence(effective_silence_),
          already_rendered(already_rendered_)
    {
    }

    monster *source;
    string line;
    msg_channel_type channel;
    bool effective_silence;
    bool already_rendered;
};

using mon_speech_emission_observer_fn =
    void (*)(const mon_speech_final_emission &, void *);

struct mon_speech_emission_observer
{
    mon_speech_emission_observer(
        mon_speech_emission_observer_fn function_ = nullptr,
        void *context_ = nullptr)
        : function(function_), context(context_)
    {
    }

    mon_speech_emission_observer_fn function;
    void *context;
};

struct mon_speech_applicability
{
    const actor *foe = nullptr;
    const actor *replacement_foe = nullptr;
    bool no_player = false;
    bool no_foe = false;
    bool no_foe_name = false;
    bool no_god = false;
    bool unseen = false;
};

void maybe_mons_speaks(monster* mons);
// Production seam for the Issue #70 monspeak tests: ``mons_speaks`` is the
// real production entry (prefix construction, exact/genus/glyph/shape
// fallback chain, weighted picks and final emission); the optional observer
// captures the final emission exactly like ``mons_speaks_msg`` does, so the
// zh translation tests drive the full production path instead of rebuilding
// the lookup chain by hand. Kept on a single declaration line so the
// baseline-frozen producer/consumer anchors of monspeak_inventory.py never
// drift.
bool mons_speaks(monster* mons,
                 const mon_speech_emission_observer *observer = nullptr);
bool resolve_mon_speech_line_channel(string &line, msg_channel_type &channel,
                                     bool silence, bool already_rendered);
bool mons_speaks_msg(monster* mons, const string &msg,
                     const msg_channel_type def_chan = MSGCH_TALK,
                     const bool silence = false,
                     const bool already_rendered = false,
                     const mon_speech_emission_observer *observer = nullptr);
bool invalid_msg(const monster &mon, string msg);
mon_speech_applicability resolve_mon_speech_applicability(
    const monster &mon);
