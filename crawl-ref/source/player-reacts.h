#pragma once

void check_trapped();

// Used only in world_reacts()
void player_reacts();
void player_reacts_to_monsters();

// Also used in places where we skip world_reacts for instant turns.
void player_takes_instant_action();
void player_reacts_to_instant_action();

// Only function other than decrement_durations() which uses decrement_a_duration()
void extract_barbs(const char* endmsg);
int current_horror_level(); // XXX: move?

// Eel-hands flavour message: real SpeakDB roots, runtime token replacement
// and exactly one random-substring expansion before the MSGCH_TALK sink.
// Non-static so targeted i18n tests can drive the real production path
// without the player_reacts 1-in-500 gate.
void do_eel_flavour_msg();
