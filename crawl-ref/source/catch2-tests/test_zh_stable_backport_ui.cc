// Stable-branch UI backport: producer/consumer regressions.
//
// These tests call the real public producers introduced or changed by the
// backport and assert the text they hand to the display sink. They are not
// template self-checks: every expectation is derived from the same helpers the
// production code uses, so a wrong key, a wrong argument order, a leftover
// format placeholder or a re-introduced concatenation fails the test.
//
// Translation rows that are still missing from the ZH SourceDB fall back to
// English at runtime; assertions that would otherwise be satisfied by that
// fallback are written as exact producer-output comparisons, and tests that
// really do require a translated row use REQUIRE on the row's presence first.

#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "branch.h"
#include "english.h"
#include "i18n.h"
#include "macro.h"
#include "notes.h"
#include "religion.h"
#include "shopping.h"
#include "spl-util.h"
#include "stringutil.h"
#include "test_zh_fixture.h"

#include <string>

namespace
{
// A shop with a saved display type/suffix, so shop_name() never needs the
// dungeon (env/branch tables) to compose its result.
shop_struct make_shop(const string &keeper)
{
    shop_struct shop;
    shop.pos = coord_def(10, 10);
    shop.type = SHOP_GENERAL;
    shop.level = 1;
    shop.shop_name = keeper;
    shop.shop_type_name = "General Store";
    shop.shop_suffix_name = "of Testing";
    return shop;
}
} // namespace

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: read_rc_file_macro returns completed error strings",
                 "[zh-translation][ui-backport][macro-rc]")
{
    // Regression for the #233 contract: the producer returns a display
    // string, never a format template. Input data may itself contain format
    // specifiers (%s, %n); those must be inserted as data, exactly once.
    SECTION("missing the second argument reports the whole field")
    {
        const string field = "M";
        const string result = read_rc_file_macro(field);
        REQUIRE_FALSE(result.empty());
        CHECK(result == make_stringf(
            T_("Cannot parse macros += %s, there is only one argument"),
            field.c_str()));
        CHECK(result.find("%s") == string::npos);
        CHECK(result.find(field) != string::npos);
    }

    SECTION("missing the third argument reports the whole field")
    {
        const string field = "M a";
        const string result = read_rc_file_macro(field);
        REQUIRE_FALSE(result.empty());
        CHECK(result == make_stringf(
            T_("Cannot parse macros += %s, there are only two arguments"),
            field.c_str()));
        CHECK(result.find("%s") == string::npos);
        CHECK(result.find(field) != string::npos);
    }

    SECTION("invalid context reports both context and field")
    {
        const string field = "Q x y";
        const string result = read_rc_file_macro(field);
        REQUIRE_FALSE(result.empty());
        CHECK(result == make_stringf(
            T_("'%s' is not a valid macro or keymap context (macros += %s)"),
            "Q", field.c_str()));
        CHECK(result.find("%s") == string::npos);
        CHECK(result.find("Q") != string::npos);
        CHECK(result.find(field) != string::npos);
    }

    SECTION("%s in the input data is inserted verbatim, not interpreted")
    {
        const string field = "%s";
        const string result = read_rc_file_macro(field);
        REQUIRE_FALSE(result.empty());
        CHECK(result == make_stringf(
            T_("Cannot parse macros += %s, there is only one argument"),
            field.c_str()));
        // Exactly one placeholder survives: the one that is input data.
        CHECK(result.find("%s") != string::npos);
        CHECK(result.find("%s", result.find("%s") + 2) == string::npos);
    }

    SECTION("%n in the input data cannot be used as a conversion")
    {
        const string field = "%n";
        const string result = read_rc_file_macro(field);
        REQUIRE_FALSE(result.empty());
        CHECK(result == make_stringf(
            T_("Cannot parse macros += %s, there is only one argument"),
            field.c_str()));
        CHECK(result.find("%n") != string::npos);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: shop_name translates fixed vault keepers only",
                 "[zh-translation][ui-backport][shop-name]")
{
    // The three fixed vault owners name gods; their display name is
    // translated at the sink while the saved identity stays untouched.
    const char *gods[] = { "Gozag", "Cheibriados", "Zin" };
    for (const char *god : gods)
    {
        CAPTURE(god);
        REQUIRE(string(T_(god)) != god);

        const shop_struct shop = make_shop(god);
        const string expected = apostrophise(string(T_(god))) + " "
                                + shop.shop_type_name + " "
                                + shop.shop_suffix_name;
        CHECK(shop_name(shop) == expected);
        CHECK(shop_name(shop).find(god) != 0);
    }

    SECTION("a custom keeper keeps its saved identity")
    {
        const shop_struct shop = make_shop("Bob");
        const string expected = apostrophise("Bob") + " "
                                + shop.shop_type_name + " "
                                + shop.shop_suffix_name;
        CHECK(shop_name(shop) == expected);
        CHECK(shop_name(shop).find("Bob") == 0);
    }

    SECTION("saved shop display strings are not re-translated")
    {
        // shop_type_name/shop_suffix_name come from the save and are copied
        // verbatim; only the keeper identity above goes through T_().
        const shop_struct shop = make_shop("Zin");
        const string result = shop_name(shop);
        CHECK(result.find(shop.shop_type_name) != string::npos);
        CHECK(result.find(shop.shop_suffix_name) != string::npos);
        CHECK(result.find(string(T_("Zin"))) != string::npos);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: reachable branch longnames are translated for UI sinks",
                 "[zh-translation][ui-backport][branch-keys]")
{
    // stairs.cc and lookup-help.cc wrap branch longnames in T_() at the
    // display sink. Unfinished legacy branches are never displayed and have
    // no ZH entry in either branch, so they are excluded rather than demanded.
    REQUIRE(string(T_("the Orcish Mines")) != "the Orcish Mines");
    REQUIRE(string(T_("the Lair of Beasts")) != "the Lair of Beasts");

    string untranslated;
    for (branch_iterator it; it; ++it)
    {
        if (branch_is_unfinished(it->id))
            continue;

        const char *longname = it->longname;
        if (!longname || !*longname)
            continue;
        if (string(T_(longname)) == longname)
            untranslated += string(untranslated.empty() ? "" : ", ") + longname;
    }

    INFO("branch longnames without a ZH entry: " << untranslated);
    CHECK(untranslated.empty());
}

// Game-history notes are displayed through Note::describe(); these tests bind
// the real producer (not just the T_ key) for the six complete templates that
// were moved off fragment concatenation.
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: note descriptions use complete templates and keep their subject",
                 "[zh-translation][ui-backport][notes]")
{
    SECTION("penance / forgiveness / loss of grace name the god inside the template")
    {
        const string zin = god_name(GOD_ZIN);
        REQUIRE(!zin.empty());

        const Note penance(NOTE_PENANCE, GOD_ZIN);
        CHECK(penance.describe(false, false, true)
              == make_stringf(T_("Was placed under penance by %s"), zin.c_str()));
        CHECK(penance.describe(false, false, true).find(zin) != string::npos);

        const Note forgiven(NOTE_MOLLIFY_GOD, GOD_ZIN);
        CHECK(forgiven.describe(false, false, true)
              == make_stringf(T_("Was forgiven by %s"), zin.c_str()));

        const Note fell(NOTE_LOSE_GOD, GOD_ZIN);
        CHECK(fell.describe(false, false, true)
              == make_stringf(T_("Fell from the grace of %s"), zin.c_str()));
        CHECK(fell.describe(false, false, true).find(zin) != string::npos);
    }

    SECTION("gift note appends the optional gift name after the template")
    {
        const Note gift(NOTE_GOD_GIFT, GOD_ZIN, 0, "a dagger");
        CHECK(gift.describe(false, false, true)
              == make_stringf(T_("Received a gift from %s"), god_name(GOD_ZIN).c_str())
                 + " (a dagger)");
    }

    SECTION("Vehumet's offered spell keeps the spell name in the sentence")
    {
        const string dart = spell_title(SPELL_MAGIC_DART);
        REQUIRE(!dart.empty());
        const Note offered(NOTE_OFFERED_SPELL, SPELL_MAGIC_DART);
        CHECK(offered.describe(false, false, true)
              == make_stringf(T_("Offered knowledge of %s by Vehumet."), dart.c_str()));
        CHECK(offered.describe(false, false, true).find(dart) != string::npos);
    }

    SECTION("learned-spell note keeps both the level and the spell name")
    {
        const int level = spell_difficulty(SPELL_MAGIC_DART);
        const string dart = spell_title(SPELL_MAGIC_DART);
        const Note learned(NOTE_LEARN_SPELL, SPELL_MAGIC_DART);
        const string desc = learned.describe(false, false, true);
        CHECK(desc == make_stringf(T_("Learned a level %d spell: %s"), level,
                                   dart.c_str()));
        const string level_str = make_stringf("%d", level);
        CHECK(desc.find(level_str) != string::npos);
        CHECK(desc.find(dart) != string::npos);
    }
}
