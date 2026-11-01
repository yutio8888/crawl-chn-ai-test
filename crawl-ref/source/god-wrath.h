/**
 * @file
 * @brief Divine retribution.
**/

#pragma once

#include "god-type.h"

// Display-only: recognize canonical wrath identities; never use for storage.
string god_wrath_display_name(const string& canonical);

bool divine_retribution(god_type god, bool no_bonus = false, bool force = false);
void reduce_xp_penance(god_type god, int amount);

void gozag_incite(monster *mon);
void gozag_abandon_shops_on_level();
void lucy_check_meddling();
