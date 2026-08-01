#include "catch_amalgamated.hpp"
#include <vector>
#include <list>
#include <functional>
#include <cstring>
#include <locale.h>

#include "random.h"
#include "stringutil.h"
#include "unicode.h"

namespace
{
struct random_substring_run
{
    string output;
    uint64_t rng_state;
    uint64_t rng_count;
    vector<random_substring_choice_trace> trace;
};

void record_random_substring_choice(
    const random_substring_choice_trace &choice, void *context)
{
    static_cast<vector<random_substring_choice_trace> *>(context)
        ->push_back(choice);
}

random_substring_run run_random_substring(const string &input, bool traced)
{
    random_substring_run result;
    rng::subgenerator scoped_rng(0x123456789abcdef0ULL,
                                 0x0fedcba987654321ULL);
    if (traced)
    {
        const random_substring_trace_observer observer =
            { record_random_substring_choice, &result.trace };
        result.output = maybe_pick_random_substring(
            input, &observer);
    }
    else
        result.output = maybe_pick_random_substring(input);

    result.rng_state = rng::current_generator().get_state();
    result.rng_count = rng::current_generator().get_count();
    return result;
}

random_substring_run run_random_substring_default_observer(
    const string &input)
{
    random_substring_run result;
    rng::subgenerator scoped_rng(0x123456789abcdef0ULL,
                                 0x0fedcba987654321ULL);
    random_substring_trace_observer observer;
    result.output = maybe_pick_random_substring(input, &observer);
    result.rng_state = rng::current_generator().get_state();
    result.rng_count = rng::current_generator().get_count();
    return result;
}
}

TEST_CASE( "maybe_pick_random_substring tracing preserves behaviour",
           "[single-file][textdb][phase0]" )
{
    const vector<string> patterns =
    {
        "[casts|pitches]",
        "[casts|pitches] and [pulses|vibrates]",
        "[|casts|]",
        "an unfinished [choice",
        // The first one-option site materializes to a string containing '['.
        // The existing algorithm searches again from the replacement position,
        // so the resulting [only|a|b] site must also be materialized.
        "[[only]|a|b]",
    };

    for (const string &pattern : patterns)
    {
        DYNAMIC_SECTION( pattern )
        {
            const random_substring_run legacy =
                run_random_substring(pattern, false);
            const random_substring_run traced =
                run_random_substring(pattern, true);
            const random_substring_run default_observer =
                run_random_substring_default_observer(pattern);

            CHECK(traced.output == legacy.output);
            CHECK(traced.rng_state == legacy.rng_state);
            CHECK(traced.rng_count == legacy.rng_count);
            CHECK(default_observer.output == legacy.output);
            CHECK(default_observer.rng_state == legacy.rng_state);
            CHECK(default_observer.rng_count == legacy.rng_count);
            CHECK(default_observer.trace.empty());

            for (size_t i = 0; i < traced.trace.size(); ++i)
            {
                CHECK(traced.trace[i].site_ordinal == i);
                CHECK(traced.trace[i].random_bound > 0);
                CHECK(traced.trace[i].selected_index >= 0);
                CHECK(traced.trace[i].selected_index
                      < traced.trace[i].random_bound);
            }
        }
    }
}

TEST_CASE( "maybe_pick_random_substring reports materialized sites",
           "[single-file][textdb][phase0]" )
{
    const random_substring_run multiple = run_random_substring(
        "[casts|pitches] [pulses|vibrates]", true);
    REQUIRE(multiple.trace.size() == 2);
    CHECK(multiple.trace[0].random_bound == 2);
    CHECK(multiple.trace[1].random_bound == 2);

    const random_substring_run empty_options =
        run_random_substring("[|casts|]", true);
    REQUIRE(empty_options.trace.size() == 1);
    CHECK(empty_options.trace[0].random_bound == 3);

    const random_substring_run unfinished =
        run_random_substring("an unfinished [choice", true);
    CHECK(unfinished.trace.empty());

    const random_substring_run replacement_contains_site =
        run_random_substring("[[only]|a|b]", true);
    REQUIRE(replacement_contains_site.trace.size() == 2);
    CHECK(replacement_contains_site.trace[0].random_bound == 1);
    CHECK(replacement_contains_site.trace[1].random_bound == 3);
}

// Test plain arrays, vectors, and lists (not random-access), with const variants of both
TEMPLATE_TEST_CASE( "comma_separated_*", "[single-file]",
                    const char *[], string[], const string[],
                    vector<const char *>, const vector<string>,
                    list<const char *>, const list<const char *> )
{
    TestType several = { "foo", "bar", "baz" };
    TestType two = { "foo", "bar" };
    TestType one = { "foo" };

    CHECK(comma_separated_line(begin(several), end(several)) == "foo, bar and baz");
    CHECK(comma_separated_line(begin(two), end(two)) == "foo and bar");
    CHECK(comma_separated_line(begin(one), end(one)) == *begin(one));
    // N.b. begin() twice is intentional, to get an empty range (likewise below)
    CHECK(comma_separated_line(begin(one), begin(one)) == "");

    CHECK(comma_separated_line(begin(several), end(several), "&", "+") == "foo+bar&baz");
    CHECK(comma_separated_line(begin(two), end(two), "&", "+") == "foo&bar");
    CHECK(comma_separated_line(begin(one), end(one), "&", "+") == *begin(one));
    CHECK(comma_separated_line(begin(one), begin(one), "&", "+") == "");

    CHECK(join_strings(begin(several), end(several)) == "foo bar baz");
    CHECK(join_strings(begin(two), end(two)) == "foo bar");
    CHECK(join_strings(begin(one), end(one)) == *begin(one));
    CHECK(join_strings(begin(one), begin(one)) == "");

    CHECK(comma_separated_fn(begin(several), end(several), uppercase_string)
            == "FOO, BAR and BAZ");
    CHECK(comma_separated_fn(begin(two), end(two), uppercase_string) == "FOO and BAR");
    CHECK(comma_separated_fn(begin(one), end(one), uppercase_string)
            == uppercase_string(*begin(one)));
    CHECK(comma_separated_fn(begin(one), begin(one), uppercase_string) == "");

    CHECK(comma_separated_fn(begin(several), end(several), uppercase_string, "&", "+")
            == "FOO+BAR&BAZ");
    CHECK(comma_separated_fn(begin(two), end(two), uppercase_string, "&", "+") == "FOO&BAR");
    CHECK(comma_separated_fn(begin(one), end(one), uppercase_string, "&", "+")
            == uppercase_string(*begin(one)));
    CHECK(comma_separated_fn(begin(one), begin(one), uppercase_string, "&", "+") == "");

}

TEST_CASE( "comma_separated_fn with a non-string", "[single-file]")
{
    int numlist[] = { 1, 2, 3, 4 };
    // Select a specific overload of std::to_string.
    string (*fn)(int) = to_string;
    // Also with a std::function
    function<string(int)> fn_func{fn};

    CHECK(comma_separated_fn(begin(numlist), end(numlist), fn) == "1, 2, 3 and 4");
    CHECK(comma_separated_fn(begin(numlist), end(numlist), fn_func) == "1, 2, 3 and 4");
}

TEST_CASE( "uppercase and lowercase", "[single-file]")
{
    for (int i = 0; i < 2; ++i) {
        // Also try with a Turkish locale, where tolower("I") is not "i". Our uppercase
        // and lowercase functions should ignore the locale for ASCII characters, because
        // they are also used for things that aren't exactly "text".
        if (i > 0)
            setlocale(LC_ALL, "tr_TR");

        // N.b. includes a capital I
        const char orig[] = "mIxEdCaSe";
        string in_s(orig);
        const string in_cs(orig);
        const char *in = in_s.c_str();

        // First, the non-mutating versions.
        CHECK(lowercase_string(in) == "mixedcase");
        CHECK(lowercase_string(in_s) == "mixedcase");
        CHECK(lowercase_string(in_cs) == "mixedcase");

        // Ensure they didn't mutate the input, and abort the test case if they did.
        REQUIRE(in_s == orig);
        REQUIRE(strcmp(in, orig) == 0);

        // Again for uppercasing
        CHECK(uppercase_string(in) == "MIXEDCASE");
        CHECK(uppercase_string(in_s) == "MIXEDCASE");
        CHECK(uppercase_string(in_cs) == "MIXEDCASE");

        REQUIRE(in_s == orig);
        REQUIRE(strcmp(in, orig) == 0);

        // Again for title-casing
        CHECK(uppercase_first(in) == "MIxEdCaSe");
        CHECK(uppercase_first(in_s) == "MIxEdCaSe");
        CHECK(uppercase_first(in_cs) == "MIxEdCaSe");

        REQUIRE(in_s == orig);
        REQUIRE(strcmp(in, orig) == 0);

        // Now the mutating versions
        string s1(orig);
        string &result = uppercase(s1);
        CHECK(result == "MIXEDCASE");
        // Verify identity
        CHECK(&result == &s1);

        string &result2 = lowercase(result);
        CHECK(result2 == "mixedcase");
        // Verify identity
        CHECK(&result2 == &s1);
    }
}

TEST_CASE( "Unicode display width is independent of the process locale",
           "[single-file][unicode]" )
{
    const char *old_locale = setlocale(LC_CTYPE, nullptr);
    const string saved_locale = old_locale ? old_locale : "";

    CHECK(setlocale(LC_CTYPE, "C") != nullptr);
    CHECK(wcwidth(U'法') == 2);
    CHECK(strwidth("法术") == 4);
    CHECK(chop_string("法术", 6) == "法术  ");

    if (!saved_locale.empty())
        CHECK(setlocale(LC_CTYPE, saved_locale.c_str()) != nullptr);
}
