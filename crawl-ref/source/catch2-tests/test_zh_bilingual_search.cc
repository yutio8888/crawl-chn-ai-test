/**
 * @file
 * @brief Bilingual Ctrl-F search — ZH-mode English keyword matching.
 *
 * Verifies that in ZH mode:
 *   1. item_english_name() returns the FULL English item name
 *      (not just the base category), enabling English keyword search
 *      for identified potions/scrolls/wands/jewellery/staves.
 *   2. ScopedLangEn forces English feature descriptions, enabling
 *      English terrain keyword search ("stairs", "altar", "door").
 *   3. The match text (display) stays Chinese — only the retrieval
 *      field is bilingual.
 *
 * @see stash.cc Stash::matches_search() feature branch
 * @see item-prop.cc item_english_name()
 **/

#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include <cstring>
#include <string>

#include "directn.h"                 // feature_description(feat,trap)
#include "dungeon-feature-type.h"    // DNGN_* feature types
#include "item-def.h"                 // item_def
#include "item-name.h"                // item_def::name()
#include "item-prop.h"                // item_english_name()
#include "item-prop-enum.h"           // item sub-types
#include "item-status-flag-type.h"    // ISFLAG_IDENTIFIED
#include "lang-en-guard.h"            // ScopedLangEn
#include "options.h"                  // Options, lang_t
#include "potion-type.h"              // POT_HEAL_WOUNDS
#include "test_zh_fixture.h"

// =========================================================================
// item_english_name — must return full English name when language is ZH
// =========================================================================

// Helper: create an identified item_def with the given base and sub types.
// The item is marked identified so DESC_PLAIN returns the full subtype name
// (e.g. "potion of heal wounds") rather than a generic descriptor.
static item_def _make_identified_item(object_class_type type, int sub_type)
{
    item_def item;
    item.base_type = type;
    item.sub_type  = sub_type;
    item.quantity  = 1;
    // Mark identified so name_aux includes both category and specific type.
    item.flags |= ISFLAG_IDENTIFIED;
    return item;
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-search: item_english_name returns full EN name under ZH",
                 "[zh-search][item_english_name]")
{
    SECTION("potion") {
        item_def pot = _make_identified_item(OBJ_POTIONS, POT_HEAL_WOUNDS);
        const string en = item_english_name(pot);
        INFO("potion en name: \"" << en << "\"");
        // Must contain "potion" (base category is always present).
        REQUIRE(en.find("potion") != string::npos);
        // Must contain English words beyond just "potion".
        REQUIRE(en.find("heal") != string::npos);
    }

    SECTION("scroll") {
        item_def sc = _make_identified_item(OBJ_SCROLLS, SCR_BLINKING);
        const string en = item_english_name(sc);
        INFO("scroll en name: \"" << en << "\"");
        REQUIRE(en.find("scroll") != string::npos);
        REQUIRE(en.find("blink") != string::npos);
    }

    SECTION("wand") {
        item_def wand = _make_identified_item(OBJ_WANDS, WAND_ACID);
        const string en = item_english_name(wand);
        INFO("wand en name: \"" << en << "\"");
        REQUIRE(en.find("wand") != string::npos);
    }

    SECTION("identified ring") {
        item_def ring = _make_identified_item(OBJ_JEWELLERY, RING_PROTECTION);
        const string en = item_english_name(ring);
        INFO("ring en name: \"" << en << "\"");
        REQUIRE(en.find("protection") != string::npos);
    }

    SECTION("identified amulet") {
        item_def amu = _make_identified_item(OBJ_JEWELLERY, AMU_REFLECTION);
        const string en = item_english_name(amu);
        INFO("amulet en name: \"" << en << "\"");
        REQUIRE(en.find("amulet") != string::npos);
        REQUIRE(en.find("reflect") != string::npos);
    }

    SECTION("magical staff") {
        item_def staff = _make_identified_item(OBJ_STAVES, STAFF_FIRE);
        const string en = item_english_name(staff);
        INFO("staff en name: \"" << en << "\"");
        REQUIRE(en.find("staff") != string::npos);
    }

    SECTION("weapon") {
        item_def wep = _make_identified_item(OBJ_WEAPONS, WPN_BROAD_AXE);
        const string en = item_english_name(wep);
        INFO("weapon en name: \"" << en << "\"");
        REQUIRE(en.find("broad") != string::npos);
        REQUIRE(en.find("axe") != string::npos);
    }
}

// =========================================================================
// Items should NOT contain Chinese characters in their English names
// =========================================================================

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-search: item_english_name has no CJK under ZH",
                 "[zh-search][item_english_name]")
{
    // Verify that the returned string doesn't contain CJK ideographs.
    // Rely on the known EN guard inside item_english_name().
    const auto items = {
        _make_identified_item(OBJ_POTIONS, POT_HEAL_WOUNDS),
        _make_identified_item(OBJ_SCROLLS, SCR_BLINKING),
        _make_identified_item(OBJ_WANDS,   WAND_ACID),
    };

    for (const auto &item : items)
    {
        const string en = item_english_name(item);
        INFO("item_english_name: \"" << en << "\"");
        for (char c : en)
        {
            // Any byte >= 0x80 suggests a multi-byte UTF-8 sequence (CJK).
            // English ASCII is strictly 0x00-0x7F.
            REQUIRE((static_cast<unsigned char>(c) & 0x80) == 0);
        }
    }
}

// =========================================================================
// item.name(DESC_PLAIN) without guard returns Chinese under ZH
// (proving the guard is what makes item_english_name English)
// =========================================================================

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-search: item.name(DESC_PLAIN) is Chinese under ZH mode",
                 "[zh-search][item_name]")
{
    item_def pot = _make_identified_item(OBJ_POTIONS, POT_HEAL_WOUNDS);
    const string zh_name = pot.name(DESC_PLAIN);
    INFO("Chinese item name: \"" << zh_name << "\"");
    // Under ZH, item.name() returns Chinese — look for a CJK byte (>= 0x80).
    bool has_cjk = false;
    for (char c : zh_name)
        if (static_cast<unsigned char>(c) >= 0x80)
            has_cjk = true;
    REQUIRE(has_cjk);
}

// =========================================================================
// ScopedLangEn forces English feature descriptions
// =========================================================================

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-search: ScopedLangEn forces EN feature descriptions",
                 "[zh-search][ScopedLangEn]")
{
    // Baseline: native ZH description should contain CJK.
    const string zh_stairs = ::feature_description(DNGN_STONE_STAIRS_DOWN_I,
                                                    NUM_TRAPS);
    INFO("ZH staircase: \"" << zh_stairs << "\"");
    bool zh_has_cjk = false;
    for (char c : zh_stairs)
        if (static_cast<unsigned char>(c) >= 0x80)
            zh_has_cjk = true;
    REQUIRE(zh_has_cjk);

    // Under ScopedLangEn: same feature returns English (ASCII-only).
    {
        ScopedLangEn en;
        const string en_stairs = ::feature_description(DNGN_STONE_STAIRS_DOWN_I,
                                                       NUM_TRAPS);
        INFO("EN staircase: \"" << en_stairs << "\"");
        bool en_has_cjk = false;
        for (char c : en_stairs)
            if (static_cast<unsigned char>(c) >= 0x80)
                en_has_cjk = true;
        REQUIRE(!en_has_cjk);
        // Must contain the expected English keyword.
        REQUIRE(en_stairs.find("staircase") != string::npos);
    }

    // After guard: back to ZH.
    const string zh_stairs2 = ::feature_description(DNGN_STONE_STAIRS_DOWN_I,
                                                    NUM_TRAPS);
    bool zh2_has_cjk = false;
    for (char c : zh_stairs2)
        if (static_cast<unsigned char>(c) >= 0x80)
            zh2_has_cjk = true;
    REQUIRE(zh2_has_cjk);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-search: EN terrain keywords match ZH features",
                 "[zh-search][terrain]")
{
    // Verify that common terrain types return English keywords under
    // ScopedLangEn that correspond to the Chinese display desc.

    auto check_bilingual = [](dungeon_feature_type feat,
                              const string &en_keyword) {
        INFO("feat: " << static_cast<int>(feat));

        const string zh_desc = ::feature_description(feat, NUM_TRAPS);
        INFO("ZH: \"" << zh_desc << "\"");

        {
            ScopedLangEn en;
            const string en_desc = ::feature_description(feat, NUM_TRAPS);
            INFO("EN: \"" << en_desc << "\"");
            REQUIRE(en_desc.find(en_keyword) != string::npos);
        }
    };

    SECTION("altar") {
        check_bilingual(DNGN_ALTAR_ZIN, "altar");
    }
    SECTION("closed door") {
        check_bilingual(DNGN_CLOSED_DOOR, "door");
    }
    SECTION("open door") {
        check_bilingual(DNGN_OPEN_DOOR, "door");
    }
    SECTION("stone staircase down") {
        check_bilingual(DNGN_STONE_STAIRS_DOWN_I, "staircase");
    }
    SECTION("stone staircase up") {
        check_bilingual(DNGN_STONE_STAIRS_UP_I, "staircase");
    }
    SECTION("escape hatch down") {
        check_bilingual(DNGN_ESCAPE_HATCH_DOWN, "hatch");
    }
    SECTION("escape hatch up") {
        check_bilingual(DNGN_ESCAPE_HATCH_UP, "hatch");
    }
}
