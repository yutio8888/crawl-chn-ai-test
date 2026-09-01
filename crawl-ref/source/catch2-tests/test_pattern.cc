#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "pattern.h"

TEST_CASE("PCRE text_pattern matches Android message rules",
          "[pattern][pcre-regression]")
{
    SECTION("ASCII message rule is caseless")
    {
        text_pattern pattern("Space warps( horribly)? around you", true);
        REQUIRE(pattern.valid());
        CHECK(pattern.matches("SPACE WARPS HORRIBLY AROUND YOU"));
        CHECK_FALSE(pattern.matches("SPACE REMAINS STABLE AROUND YOU"));
    }

    SECTION("Chinese message rule supports literals and alternation")
    {
        text_pattern pattern("感觉.*(抽干|虚弱|疲惫)", true);
        REQUIRE(pattern.valid());
        CHECK(pattern.matches("你感觉自己被抽干了"));
        CHECK(pattern.matches("感觉非常疲惫"));
        CHECK_FALSE(pattern.matches("感觉精神很好"));
    }

    SECTION("mixed UTF-8 and ASCII input remains caseless")
    {
        text_pattern pattern("^Something .* you", true);
        REQUIRE(pattern.valid());
        CHECK(pattern.matches("sOmEtHiNg 击中了 YOU"));
        CHECK_FALSE(pattern.matches("Nothing 击中了 you"));
    }
}

TEST_CASE("PCRE text_pattern owns compiled patterns across assignments",
          "[pattern][pcre-regression]")
{
    const string valid_rule = "^Something .* you";

    SECTION("invalid compilation repeatedly recovers by string assignment")
    {
        text_pattern pattern("(", true);
        for (int i = 0; i < 3; ++i)
        {
            CHECK_FALSE(pattern.valid());
            CHECK_FALSE(pattern.matches("anything"));
            pattern = valid_rule;
            REQUIRE(pattern.valid());
            CHECK(pattern.matches("something sees YOU"));
            pattern = string("(");
        }
        pattern = valid_rule;
        REQUIRE(pattern.valid());
        CHECK(pattern.matches("SOMETHING follows you"));
    }

    SECTION("copy construction has an independent compiled lifetime")
    {
        text_pattern source(valid_rule, true);
        REQUIRE(source.valid());
        {
            text_pattern copy(source);
            REQUIRE(copy.valid());
            CHECK(copy.matches("something finds YOU"));
        }
        CHECK(source.matches("SOMETHING follows you"));
    }

    SECTION("copy and self assignment preserve matching")
    {
        text_pattern assigned("Space warps( horribly)? around you", true);
        REQUIRE(assigned.valid());
        {
            text_pattern source("感觉.*(抽干|虚弱|疲惫)", true);
            REQUIRE(source.valid());
            assigned = source;
        }
        REQUIRE(assigned.valid());
        CHECK(assigned.matches("感觉十分虚弱"));
        assigned = assigned;
        REQUIRE(assigned.valid());
        CHECK(assigned.matches("感觉十分疲惫"));
    }

    SECTION("string assignment releases an existing compiled pattern")
    {
        text_pattern pattern("Space warps( horribly)? around you", true);
        REQUIRE(pattern.valid());
        pattern = valid_rule;
        REQUIRE(pattern.valid());
        CHECK(pattern.matches("something attacks YOU"));
        CHECK_FALSE(pattern.matches("space warps around you"));
    }
}
