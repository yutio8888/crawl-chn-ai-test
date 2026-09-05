#ifdef USE_TILE_LOCAL
#pragma once

#include "command-type.h"

// Show the modal status-details drawer used by the compact Android top HUD.
void show_topbar_status_drawer(int selected_status = -1);

// Show the single-page Android command panel and return the selected command.
// Cancellation returns CMD_NO_CMD. A spell or ability picked from a
// inline quick-access section is used through its normal command path once the panel
// has closed; that also returns CMD_NO_CMD, with *acted set so the caller can
// report the tap as already handled.
command_type show_topbar_command_menu(bool *acted = nullptr);

#endif
