#ifdef USE_TILE_LOCAL
#pragma once

#include "command-type.h"

// Show the modal status-details drawer used by the compact Android top HUD.
void show_topbar_status_drawer();

// Show the compact Android command drawer and return the selected command.
// Cancellation returns CMD_NO_CMD.
command_type show_topbar_command_menu();

#endif
