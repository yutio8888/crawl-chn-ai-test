#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#ifdef USE_TILE_LOCAL

#include "layout-policy.h"

TEST_CASE("Android top HUD remains active in both orientations",
          "[layout-policy][android]")
{
    AndroidPortraitLayoutPolicy policy;

    policy.update(1080, 2400, 20, 20, maybe_bool::maybe);
    CHECK(policy.uses_compact_hud());
    CHECK(policy.uses_top_hud());

    policy.update(2400, 1080, 20, 20, maybe_bool::maybe);
    CHECK(policy.uses_compact_hud());
    CHECK(policy.uses_top_hud());
}

TEST_CASE("Android top HUD honours an explicit small-layout override",
          "[layout-policy][android]")
{
    AndroidPortraitLayoutPolicy policy;

    policy.update(2400, 1080, 20, 20, maybe_bool::f);
    CHECK_FALSE(policy.uses_compact_hud());
    CHECK_FALSE(policy.uses_top_hud());

    policy.update(2400, 1080, 20, 20, maybe_bool::t);
    CHECK(policy.uses_compact_hud());
    CHECK(policy.uses_top_hud());
}

#endif
