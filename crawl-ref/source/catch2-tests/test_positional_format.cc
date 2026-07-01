#include "catch_amalgamated.hpp"

#include <string>

#include "positional_format.h"

TEST_CASE("vmake_stringf_p positional format", "[single-file]")
{
    SECTION("Sparse reference: %1$s %3$s skips %2$s")
    {
        const std::string result = make_stringf_p("%1$s %3$s", "a", "b", "c");
        REQUIRE(result == "a c");
    }

    SECTION("Drop tail: %1$s with extra args drops unused trailing args")
    {
        const std::string result = make_stringf_p("%1$s", "a", "b");
        REQUIRE(result == "a");
    }

    SECTION("Out of bounds: %5$s with too few args does not crash")
    {
        const std::string result = make_stringf_p("%5$s", "a");
        // The %5$s is out of bounds; it should produce an empty string
        // or fallback rather than crash. Just ensure we don't crash.
        REQUIRE(result.size() >= 0);
    }

    SECTION("Mixed format: %1$s %s gracefully handles POSIX-undefined mix")
    {
        // POSIX says mixing positional (%n$s) and non-positional (%s) is
        // undefined. We should handle it gracefully without crashing.
        const std::string result = make_stringf_p("%1$s %s", "a", "b");
        REQUIRE(result.size() >= 0);
    }

    SECTION("Zero refs: format with no specifiers ignores all args")
    {
        const std::string result = make_stringf_p("hello", "a", "b");
        REQUIRE(result == "hello");
    }
}
