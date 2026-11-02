/**
 * @file
 * @brief Functions used to print information about gods.
 **/

#pragma once

#include "god-type.h"
#include "species-type.h"

#include <string>
#include <utility>
#include <vector>

int god_favour_rank(god_type which_god);
string god_title(god_type which_god, species_type which_species, int piety);
// Owning canonical-EN / current-display pairs from the finite divine title
// table. Display-only: never used for identity, saves or protocol fields.
std::vector<std::pair<std::string, std::string>>
    god_title_translation_pairs(species_type which_species);
void describe_god(god_type which_god);
bool describe_god_with_join(god_type which_god);
