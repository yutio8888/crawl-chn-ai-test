/**
 * @file
 * @brief Divine retribution.
**/

#pragma once

#include <string>

#include "god-type.h"

bool divine_retribution(god_type god, bool no_bonus = false, bool force = false);
// Display-only: render a canonical wrath identity (see _god_wrath_name) in the
// current language. Never use the result for blame/death/xlog fields.
std::string god_wrath_display_name(const std::string& canonical);
void reduce_xp_penance(god_type god, int amount);

void gozag_incite(monster *mon);
void gozag_abandon_shops_on_level();
void lucy_check_meddling();
