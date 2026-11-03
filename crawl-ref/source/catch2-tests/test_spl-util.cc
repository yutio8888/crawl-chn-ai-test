#include "catch_amalgamated.hpp"

#include "AppHdr.h"
#include "spl-util.h"
#include "item-prop.h"
#include "lang-en-guard.h"
#include "mapdef.h"
#include "test_zh_fixture.h"
#include "rltiles/tiledef-gui.h"

TEST_CASE("All spells are valid")
{
    // we require that all spells are `valid`: this means that they must have
    // a spell stub in spl-data.h, even if removed. (This is a change from the
    // past, before spell stubs existed.)
    init_spell_descs();

    for (int s = SPELL_FIRST_SPELL; s < NUM_SPELLS; s++)
    {
        const spell_type spell = static_cast<spell_type>(s);
        if (spell == SPELL_NO_SPELL)
            continue;
        // A fail here means that there is a removed spell with no data at all.
        // For consistency, add an AXED_SPELL line to spl-data.h.
        // n.b. if a spell is invalid, it won't have a name, and so if it's very
        // far into the enum, your best bet to find out what it is is to print
        // all the names before it.
        INFO("Testing validity for spell #" << s);
        REQUIRE(is_valid_spell(spell));
    }
}

// TODO: in principle many of the checks in init_spell_descs could be refactored
// as catch2 tests.
TEST_CASE("Removed spells and AXED_SPELLs are in sync" )
{
    // A spell should be AXED iff it is removed.
    // TODO: is there a way for SPELL_AXED to automatically set removed status,
    // making this test unnecessary?
    init_monsters();
    init_spell_descs();
    init_spell_name_cache();

    for (int s = SPELL_FIRST_SPELL; s < NUM_SPELLS; s++)
    {
        const spell_type spell = static_cast<spell_type>(s);
        // validity is tested separately: a completely invalid spell will
        // crash below this check.
        if (spell == SPELL_NO_SPELL || !is_valid_spell(spell))
            continue;

        // Use a heuristic to identify spells that have a stub set with
        // SPELL_AXED.
        // TODO: is it worth checking every field here?
        const bool spell_is_axed = get_spell_flags(spell) == spflag::none
            && get_spell_tile(spell) == TILEG_ERROR
            && get_spell_disciplines(spell) == spschool::none;

        INFO("Testing removedness for " << spell_title(spell));
        REQUIRE(spell_removed(spell) == spell_is_axed);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "School lookup accepts vault identities in both languages",
                 "[zh-translation][webtiles-screenshots]")
{
    init_properties();
    init_spell_descs();
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (int i = 0; i <= SPSCHOOL_LAST_EXPONENT + 1; ++i)
        {
            const auto school = spschools_type::exponent(i);
            string short_en, long_en;
            {
                ScopedLangEn canonical;
                short_en = spelltype_short_name(school);
                long_en = spelltype_long_name_en(school);
            }
            INFO("school=" << long_en);
            CHECK(school_by_name(short_en) == school);
            CHECK(school_by_name(long_en) == school);
            CHECK(school_by_name(spelltype_short_name(school)) == school);
            CHECK(school_by_name(spelltype_long_name(school)) == school);
        }
        CHECK(school_by_name("conjur") == spschool::conjuration);
        CHECK(school_by_name("not a school") == spschool::none);
        CHECK(school_by_name("a") == spschool::none);

        // Exercise the production .des item parser used by the failing trove.
        item_list items;
        item_spec spec;
        REQUIRE(items.parse_single_spec(spec,
            "randbook disc:earth disc2:conj numspells:5 w:4"));
        CHECK(spec.props[RANDBK_DISC1_KEY].get_short() == static_cast<short>(spschool::earth));
        CHECK(spec.props[RANDBK_DISC2_KEY].get_short() == static_cast<short>(spschool::conjuration));
        REQUIRE(items.parse_single_spec(spec,
            "randbook disc:summoning disc2:conj numspells:5 w:4"));
        REQUIRE(items.parse_single_spec(spec,
            "randbook disc:tloc disc2:frge numspells:5"));
        CHECK(spec.props[RANDBK_DISC1_KEY].get_short() == static_cast<short>(spschool::translocation));
        CHECK(spec.props[RANDBK_DISC2_KEY].get_short() == static_cast<short>(spschool::forgecraft));
        CHECK_FALSE(items.parse_single_spec(spec, "randbook disc:not_a_school"));
    }
}
