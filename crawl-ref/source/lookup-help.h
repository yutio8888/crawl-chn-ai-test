/**
 * @file
 * @brief Let the player search for descriptions of monsters, items, etc.
 **/

#pragma once

#include <string>
#include <vector>

#include "command-type.h"
#include "lookup-help-type.h"

using std::string;

void keyhelp_query_descriptions(command_type where_from=CMD_NO_CMD);

string lookup_help_type_name(lookup_help_type lht);
std::vector<string> lookup_help_matching_keys(lookup_help_type lht,
                                            const string &regex,
                                            bool *exact_match = nullptr);
char lookup_help_type_shortcut(lookup_help_type lht);
bool find_description_of_type(lookup_help_type lht);
