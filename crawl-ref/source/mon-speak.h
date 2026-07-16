/**
 * @file
 * @brief Functions to handle speaking monsters
**/

#pragma once

#include "mpr.h"

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
bool mons_speaks(monster* mons);
bool resolve_mon_speech_line_channel(string &line, msg_channel_type &channel,
                                     bool silence, bool already_rendered);
bool mons_speaks_msg(monster* mons, const string &msg,
                     const msg_channel_type def_chan = MSGCH_TALK,
                     const bool silence = false,
                     const bool already_rendered = false);
bool invalid_msg(const monster &mon, string msg);
mon_speech_applicability resolve_mon_speech_applicability(
    const monster &mon);
