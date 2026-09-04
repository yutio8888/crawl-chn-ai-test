#ifdef USE_TILE_LOCAL
#pragma once

#include "command-type.h"

// Show the modal status-details drawer used by the compact Android top HUD.
void show_topbar_status_drawer();

// Show the compact Android command drawer and return the selected command.
// Cancellation returns CMD_NO_CMD. A spell or ability picked from a
// quick-access page is used through its normal command path once the drawer
// has closed; that also returns CMD_NO_CMD, with *acted set so the caller can
// report the tap as already handled.
command_type show_topbar_command_menu(bool *acted = nullptr);

#endif
