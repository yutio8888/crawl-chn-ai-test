#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "i18n.h"                // T_()
#include "ability.h"
#include "ability-type.h"
#include "art-enum.h"
#include "artefact.h"
#include "decks.h"
#include "item-status-flag-type.h"
#include "item-name.h"
#include "item-prop-enum.h"
#include "mapdef.h"
#include "mgen-data.h"
#include "mon-util.h"
#include "movement-i18n.h"
#include "options.h"
#include "species.h"
#include "species-type.h"
#include "spl-util.h"
#include "spell-type.h"
#include "stringutil.h"
#include "tags.h"
#include "terrain.h"
#include "test_zh_fixture.h"
#include "test_zh_helpers.h"
#include "unwind.h"

#include <cstring>
#include <array>
#include <string>
#include <tuple>

namespace
{
mons_spec parse_des_monster(const char* definition, lang_t language)
{
    Options.language = language;
    Options.lang_name = language == lang_t::ZH ? "zh" : nullptr;
    i18n_cache_clear();

    mons_list monsters;
    const string error = monsters.add_mons(definition);
    INFO("definition=\"" << definition << "\", language="
         << (language == lang_t::ZH ? "zh" : "en")
         << ", error=\"" << error << "\"");
    REQUIRE(error.empty());
    REQUIRE(monsters.size() == 1);
    REQUIRE(monsters.slot_size(0) == 1);
    return monsters.get_monster(0, 0);
}
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: .des hydra head words are locale independent",
                 "[zh-translation][des-protocol][issue-14]")
{
    init_monsters();

    using Row = std::tuple<const char*, monster_type, int>;
    const auto row = GENERATE(table<const char*, monster_type, int>({
        Row{"one-headed hydra", MONS_HYDRA, 1},
        Row{"eight-headed hydra", MONS_HYDRA, 8},
        Row{"twenty-headed hydra", MONS_HYDRA, 20},
        Row{"six-headed slymdra", MONS_SLYMDRA, 6},
        Row{"8-headed hydra", MONS_HYDRA, 8},
    }));

    const mons_spec english = parse_des_monster(std::get<0>(row), lang_t::EN);
    const mons_spec chinese = parse_des_monster(std::get<0>(row), lang_t::ZH);

    REQUIRE(english.type == std::get<1>(row));
    REQUIRE(chinese.type == english.type);
    REQUIRE(english.props[MGEN_NUM_HEADS].get_int() == std::get<2>(row));
    REQUIRE(chinese.props[MGEN_NUM_HEADS].get_int()
            == english.props[MGEN_NUM_HEADS].get_int());
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: invalid .des hydra head specifications fail closed",
                 "[zh-translation][des-protocol][issue-14]")
{
    init_monsters();

    const auto definition = GENERATE(values({
        "0-headed hydra",
        "21-headed hydra",
        "21-headed slymdra",
        "eightjunk-headed hydra",
        "8-junk-headed hydra",
        "one-junk-headed slymdra",
        "twenty-one-headed hydra",
        "unknown-headed hydra",
    }));
    const auto language = GENERATE(lang_t::EN, lang_t::ZH);

    Options.language = language;
    Options.lang_name = language == lang_t::ZH ? "zh" : nullptr;
    i18n_cache_clear();

    mons_list monsters;
    const string error = monsters.add_mons(definition);
    INFO("definition=\"" << definition << "\", language="
         << (language == lang_t::ZH ? "zh" : "en")
         << ", error=\"" << error << "\"");
    REQUIRE_FALSE(error.empty());
    REQUIRE(monsters.size() == 0);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: Lernaean hydra remains a distinct .des identity",
                 "[zh-translation][des-protocol][issue-14]")
{
    init_monsters();
    init_mon_name_cache();

    const mons_spec english = parse_des_monster("Lernaean hydra", lang_t::EN);
    const mons_spec chinese = parse_des_monster("Lernaean hydra", lang_t::ZH);

    REQUIRE(english.type == MONS_LERNAEAN_HYDRA);
    REQUIRE(chinese.type == MONS_LERNAEAN_HYDRA);
    REQUIRE_FALSE(english.props.exists(MGEN_NUM_HEADS));
    REQUIRE_FALSE(chinese.props.exists(MGEN_NUM_HEADS));
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: every canonical English spell name survives a fresh cache",
                 "[zh-translation][des-protocol][issue-15]")
{
    init_monsters();
    init_spell_descs();
    init_spell_name_cache();

    for (int i = SPELL_FIRST_SPELL; i < NUM_SPELLS; ++i)
    {
        const spell_type spell = static_cast<spell_type>(i);
        if (!is_valid_spell(spell))
            continue;

        INFO("spell=" << i << ", English name=\""
             << spell_english_name(spell) << "\"");
        REQUIRE(spell_by_name(spell_english_name(spell)) == spell);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: representative .des lists are language equivalent",
                 "[zh-translation][des-protocol][issue-15]")
{
    init_monsters();
    init_mon_name_cache();
    init_item_name_cache();

    Options.language = lang_t::EN;
    Options.lang_name = nullptr;
    i18n_cache_clear();
    mons_list english_monsters;
    item_list english_items;
    keyed_mapspec english_key;
    REQUIRE(english_monsters.add_mons("yak").empty());
    REQUIRE(english_items.add_item("potion of curing").empty());
    REQUIRE(english_key.set_mons("yak", false).empty());
    REQUIRE(english_key.set_item("potion of curing", false).empty());
    REQUIRE(english_key.set_feat(".", false).empty());

    Options.language = lang_t::ZH;
    Options.lang_name = "zh";
    i18n_cache_clear();
    mons_list chinese_monsters;
    item_list chinese_items;
    keyed_mapspec chinese_key;
    REQUIRE(chinese_monsters.add_mons("yak").empty());
    REQUIRE(chinese_items.add_item("potion of curing").empty());
    REQUIRE(chinese_key.set_mons("yak", false).empty());
    REQUIRE(chinese_key.set_item("potion of curing", false).empty());
    REQUIRE(chinese_key.set_feat(".", false).empty());

    REQUIRE(english_monsters.get_monster(0, 0).type == MONS_YAK);
    REQUIRE(chinese_monsters.get_monster(0, 0).type
            == english_monsters.get_monster(0, 0).type);

    const item_spec english_item = english_items.get_item(0);
    const item_spec chinese_item = chinese_items.get_item(0);
    REQUIRE(english_item.base_type == OBJ_POTIONS);
    REQUIRE(english_item.sub_type == POT_CURING);
    REQUIRE(chinese_item.base_type == english_item.base_type);
    REQUIRE(chinese_item.sub_type == english_item.sub_type);

    REQUIRE(chinese_key.get_monsters().get_monster(0, 0).type
            == english_key.get_monsters().get_monster(0, 0).type);
    REQUIRE(chinese_key.get_items().get_item(0).base_type
            == english_key.get_items().get_item(0).base_type);
    REQUIRE(chinese_key.get_items().get_item(0).sub_type
            == english_key.get_items().get_item(0).sub_type);
    REQUIRE(english_key.feat.feats.size() == 1);
    REQUIRE(chinese_key.feat.feats.size() == 1);
    REQUIRE(english_key.feat.feats[0].glyph == '.');
    REQUIRE(chinese_key.feat.feats[0].glyph
            == english_key.feat.feats[0].glyph);
}

// =============================================================================
// M1 milestone scope:
//   1) Smoke test: assert ZhTranslationFixture actually flips the language,
//      i.e. in a fixture context T_("You hit %s.") returns a Chinese
//      translation (so source.txt was reachable). This guards plan v2's
//      B3 / Q1 acceptance before any enumerator is built.
//   2) Table-driven unit tests of the 8 scan rules (5 positives + 5
//      negatives each) — plan v2 §2.5.
//
// Tag: [zh-translation][zh-helpers].
//
// Note on the C++ standard: catch2-tests are built with -std=c++14
// (Makefile:864), so structured bindings are unavailable. We access
// GENERATE(table<...>) results via std::get<N>(row).
// =============================================================================

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: fixture smoke — T_(\"You attack %s.\") returns Chinese",
                 "[zh-translation][zh-helpers]")
{
    // Plan v2 §7 M1 acceptance: prove the fixture actually flips the language
    // so dat/i18n/zh/source.txt is consulted. Picking the "You attack %s."
    // key (verified to be translated to "你攻击了%s。" in source.txt) rather
    // than "You hit %s." because the latter is not present in source.txt; the
    // fixture's job here is to demonstrate a known-translated key actually
    // round-trips through lookup and returns Chinese bytes.
    const char* key = "You attack %s.";
    const char* tr  = T_(key);
    // Plan acceptance: NOT equal to the English key (string compare).
    INFO("T_(\"" << key << "\") returned: \"" << (tr ? tr : "(null)") << "\"");
    REQUIRE(tr != nullptr);
    REQUIRE(std::strcmp(tr, key) != 0);
    // And it must contain at least one non-ASCII byte — calling T_() ought
    // to return a Chinese translation (which is UTF-8 multi-byte for any
    // ideograph). A purely-ASCII return would mean the lookup fell back to
    // English again (e.g. options not actually toggled).
    bool has_non_ascii = false;
    for (char c : std::string(tr))
        if (static_cast<unsigned char>(c) >= 0x80)
        {
            has_non_ascii = true;
            break;
        }
    REQUIRE(has_non_ascii);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: contextual movement phrases select grammar complements",
                 "[zh-translation][zh-helpers][movement-i18n]")
{
    using Row = std::tuple<const char*, move_phrase_context, const char*>;
    const auto row = GENERATE(table<const char*, move_phrase_context,
                                    const char*>({
        Row{"walk", move_phrase_context::enter_area, "走进"},
        Row{"fly", move_phrase_context::enter_area, "飞入"},
        Row{"roll", move_phrase_context::enter_area, "翻滚进入"},
        Row{"walk", move_phrase_context::through_obstacle, "步行穿过"},
        Row{"stride", move_phrase_context::through_obstacle, "大步穿过"},
        Row{"rampage", move_phrase_context::toward_target, "冲向"},
        Row{"blink", move_phrase_context::onto_actor, "闪烁到"},
        Row{"step", move_phrase_context::onto_surface, "迈上"},
        Row{"fly", move_phrase_context::over_terrain, "飞到"},
    }));

    REQUIRE(std::string(translated_move_phrase(std::get<0>(row),
                                                std::get<1>(row)))
            == std::get<2>(row));
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: movement phrase full-sentence golden samples",
                 "[zh-translation][zh-helpers][movement-i18n]")
{
    const char* enter = translated_move_phrase(
        "walk", move_phrase_context::enter_area);
    REQUIRE(make_stringf(T_("Really %s into a travel-excluded area?"), enter)
            == "确定要走进探索排除区域吗？");

    const char* through = translated_move_phrase(
        "stride", move_phrase_context::through_obstacle);
    REQUIRE(make_stringf(T_("You %s carefully through the %s."), through,
                         T_("plants"))
            == "你小心翼翼地大步穿过植物。");

    const char* onto = translated_move_phrase(
        "step", move_phrase_context::onto_surface);
    REQUIRE(make_stringf(T_("Really %s onto that %s?"), onto, "警报陷阱")
            == "确定要迈上那个警报陷阱吗？");

    const char* over = translated_move_phrase(
        "fly", move_phrase_context::over_terrain);
    REQUIRE(make_stringf(
                T_("Are you sure you want to %s over %s while you are "
                   "losing your buoyancy?"), over, T_("lava"))
            == "你确定要飞到熔岩上方吗？你的浮力正在消失。");

    REQUIRE(make_stringf(T_("Really %s into that cloud of %s?"), enter,
                         "毒气")
            == "确定要走进那片毒气吗？");
    const char* blink = translated_move_phrase(
        "blink", move_phrase_context::bare);
    REQUIRE(make_stringf(T_("You cannot %s away from %s!"), blink, "怪物")
            == "你不能通过闪烁远离怪物！");
    const char* hop = translated_move_phrase(
        "hop", move_phrase_context::bare);
    REQUIRE(make_stringf(T_("Are you sure you want to cancel this %s?"), hop)
            == "你确定要取消此次跳跃吗？");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: terrain swap messages preserve every visibility branch",
                 "[zh-translation][terrain-swap]")
{
    using Row = std::tuple<dungeon_feature_type, const char*, const char*,
                           const char*, bool, bool, const char*>;
    const auto row = GENERATE(table<dungeon_feature_type, const char*,
                                    const char*, const char*, bool, bool,
                                    const char*>({
        Row{DNGN_FLOOR, "石梯", "", "", true, false,
            "石梯突然消失了！"},
        Row{DNGN_STONE_ARCH, "石梯", "你", "", true, false,
            "石梯突然从你旁边消失了！"},
        Row{DNGN_FLOOR, "石梯", "", "", false, true,
            "石梯突然出现了！"},
        Row{DNGN_ROCK_WALL, "石梯", "", "你", false, true,
            "石梯突然出现在你周围！"},
        Row{DNGN_FLOOR, "石梯", "", "", true, true, "石梯移动了！"},
        Row{DNGN_ESCAPE_HATCH_UP, "石梯", "你", "", true, true,
            "石梯从你上方移走了！"},
        Row{DNGN_ESCAPE_HATCH_DOWN, "石梯", "", "兽人", true, true,
            "石梯移到了兽人下方！"},
        Row{DNGN_STONE_ARCH, "石梯", "你", "兽人", true, true,
            "石梯从你旁边移到了兽人旁边！"},
    }));
    REQUIRE(format_feature_swap_message(
                std::get<1>(row), std::get<0>(row), std::get<2>(row),
                std::get<3>(row), std::get<4>(row), std::get<5>(row))
            == std::get<6>(row));
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: fixed artefact appearances translate only for display",
                 "[zh-translation][artefact-appearance]")
{
    using Row = std::tuple<int, const char*, const char*, const char*>;
    const auto row = GENERATE(table<int, const char*, const char*, const char*>({
        Row{UNRAND_CEREBOV, "great serpentine sword", "蛇形巨剑",
            "塞雷博夫之剑"},
        Row{UNRAND_ASMODEUS, "ruby sceptre", "红宝石权杖",
            "阿斯摩蒂斯之权杖"},
        Row{UNRAND_DRAGONSKIN, "opalescent scaly cloak",
            "乳白色鳞片斗篷", "龙皮斗篷"},
    }));

    item_def item;
    item.quantity = 1;
    const unique_item_status_type prior_status =
        get_unique_item_status(std::get<0>(row));
    REQUIRE(make_item_unrandart(item, std::get<0>(row)));
    unwinder restore_status([&item, prior_status]() {
        set_unique_item_status(item, prior_status);
    });
    item.flags &= ~ISFLAG_IDENTIFIED;

    REQUIRE(item.props[ARTEFACT_APPEAR_KEY].get_string()
            == std::get<1>(row));
    REQUIRE(get_artefact_name(item) == std::get<2>(row));

    item.flags |= ISFLAG_IDENTIFIED;
    REQUIRE(get_artefact_name(item) == std::get<3>(row));

    Options.language = lang_t::EN;
    Options.lang_name = nullptr;
    i18n_cache_clear();
    item.flags &= ~ISFLAG_IDENTIFIED;
    REQUIRE(get_artefact_name(item) == std::get<1>(row));
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: fixed artefact appearance identity survives save roundtrip",
                 "[zh-translation][artefact-appearance][tags]")
{
    item_def item;
    item.quantity = 1;
    const unique_item_status_type prior_status =
        get_unique_item_status(UNRAND_CEREBOV);
    REQUIRE(make_item_unrandart(item, UNRAND_CEREBOV));
    unwinder restore_status([&item, prior_status]() {
        set_unique_item_status(item, prior_status);
    });
    item.flags &= ~ISFLAG_IDENTIFIED;
    item.pos = coord_def(-1, -1);

    vector<unsigned char> buffer;
    writer output(&buffer);
    marshallItem(output, item, true);

    reader input(buffer);
    input.setMinorVersion(TAG_MINOR_VERSION);
    item_def loaded;
    unmarshallItem(input, loaded);

    REQUIRE(loaded.unrand_idx == UNRAND_CEREBOV);
    REQUIRE(loaded.props[ARTEFACT_APPEAR_KEY].get_string()
            == "great serpentine sword");
    REQUIRE(get_artefact_name(loaded) == "蛇形巨剑");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "en: terrain swap messages preserve legacy output",
                 "[zh-translation][terrain-swap]")
{
    using Row = std::tuple<dungeon_feature_type, const char*, const char*,
                           bool, bool, const char*>;
    const auto row = GENERATE(table<dungeon_feature_type, const char*,
                                    const char*, bool, bool, const char*>({
        Row{DNGN_FLOOR, "", "", true, false,
            "the stone staircase suddenly disappears!"},
        Row{DNGN_STONE_ARCH, "you", "", true, false,
            "the stone staircase suddenly disappears from beside you!"},
        Row{DNGN_FLOOR, "", "", false, true,
            "the stone staircase suddenly appears!"},
        Row{DNGN_ROCK_WALL, "", "you", false, true,
            "the stone staircase suddenly appears around you!"},
        Row{DNGN_FLOOR, "", "", true, true,
            "the stone staircase moves!"},
        Row{DNGN_ESCAPE_HATCH_UP, "you", "", true, true,
            "the stone staircase moves from above you!"},
        Row{DNGN_ESCAPE_HATCH_DOWN, "", "the orc", true, true,
            "the stone staircase moves to beneath the orc!"},
        Row{DNGN_STONE_ARCH, "you", "the orc", true, true,
            "the stone staircase moves from beside you to beside the orc!"},
    }));

    Options.language = lang_t::EN;
    Options.lang_name = nullptr;
    i18n_cache_clear();
    REQUIRE(format_feature_swap_message(
                "the stone staircase", std::get<0>(row), std::get<1>(row),
                std::get<2>(row), std::get<3>(row), std::get<4>(row))
            == std::get<5>(row));
    Options.language = lang_t::ZH;
    Options.lang_name = "zh";
    i18n_cache_clear();
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: possible forced movement prompt golden samples",
                 "[zh-translation][zh-helpers][movement-i18n]")
{
    using Row = std::tuple<possible_forced_prompt_context, const char*,
                           const char*>;
    const auto row = GENERATE(table<possible_forced_prompt_context,
                                    const char*, const char*>({
        Row{possible_forced_prompt_context::cloud, "毒气",
            "这可能使你踉跄着退入那片毒气。要继续吗？"},
        Row{possible_forced_prompt_context::zot_trap, "",
            "这可能使你踉跄着退入佐特陷阱。要继续吗？"},
        Row{possible_forced_prompt_context::onto_trap, "警报陷阱",
            "这可能使你踉跄着退到那个警报陷阱上。要继续吗？"},
        Row{possible_forced_prompt_context::into_trap, "传送陷阱",
            "这可能使你踉跄着退入那个传送陷阱。要继续吗？"},
        Row{possible_forced_prompt_context::binding_sigil, "",
            "这可能使你踉跄着退到束缚符文上。要继续吗？"},
        Row{possible_forced_prompt_context::toxic_bog, "",
            "这可能使你踉跄着退入毒沼。要继续吗？"},
        Row{possible_forced_prompt_context::exclusion, "",
            "这可能使你踉跄着退入探索排除区域。要继续吗？"},
        Row{possible_forced_prompt_context::over_losing_buoyancy, "熔岩",
            "你的浮力正在消失；这可能使你踉跄着退到熔岩上方。要继续吗？"},
        Row{possible_forced_prompt_context::into_losing_buoyancy, "熔岩",
            "你的浮力正在消失；这可能使你踉跄着退入熔岩。要继续吗？"},
        Row{possible_forced_prompt_context::over_expiring_transformation, "深水",
            "你的变形即将结束；这可能使你踉跄着退到深水上方。要继续吗？"},
        Row{possible_forced_prompt_context::into_expiring_transformation, "熔岩",
            "你的变形即将结束；这可能使你踉跄着退入熔岩。要继续吗？"},
    }));
    REQUIRE(possible_forced_move_prompt(std::get<0>(row), std::get<1>(row))
            == std::get<2>(row));
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "en: movement phrase helper preserves runtime verbs",
                 "[zh-translation][zh-helpers][movement-i18n]")
{
    Options.language = lang_t::EN;
    Options.lang_name = nullptr;
    i18n_cache_clear();

    const std::array<move_phrase_context,
                     static_cast<size_t>(move_phrase_context::num_contexts)>
        contexts = {{
            move_phrase_context::bare,
            move_phrase_context::enter_area,
            move_phrase_context::onto_surface,
            move_phrase_context::onto_actor,
            move_phrase_context::through_obstacle,
            move_phrase_context::toward_target,
            move_phrase_context::over_terrain,
        }};
    for (move_phrase_context context : contexts)
        REQUIRE(std::strcmp(translated_move_phrase("walk", context), "walk") == 0);

    REQUIRE(make_stringf(T_("Really %s into a travel-excluded area?"),
                         translated_move_phrase(
                             "walk", move_phrase_context::enter_area))
            == "Really walk into a travel-excluded area?");

    Options.language = lang_t::ZH;
    Options.lang_name = "zh";
    i18n_cache_clear();
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "en: possible forced movement prompt templates are unchanged",
                 "[zh-translation][zh-helpers][movement-i18n]")
{
    using Row = std::tuple<possible_forced_prompt_context, const char*,
                           const char*>;
    const auto row = GENERATE(table<possible_forced_prompt_context,
                                    const char*, const char*>({
        Row{possible_forced_prompt_context::cloud, "poison gas", "This might make you stumble backwards into that cloud of poison gas. Continue?"},
        Row{possible_forced_prompt_context::zot_trap, "", "This might make you stumble backwards into the Zot trap. Continue?"},
        Row{possible_forced_prompt_context::onto_trap, "alarm trap", "This might make you stumble backwards onto that alarm trap. Continue?"},
        Row{possible_forced_prompt_context::into_trap, "teleport trap", "This might make you stumble backwards into that teleport trap. Continue?"},
        Row{possible_forced_prompt_context::binding_sigil, "", "This might make you stumble backwards onto a binding sigil. Continue?"},
        Row{possible_forced_prompt_context::toxic_bog, "", "This might make you stumble backwards into a toxic bog. Continue?"},
        Row{possible_forced_prompt_context::exclusion, "", "This might make you stumble backwards into a travel-excluded area. Continue?"},
        Row{possible_forced_prompt_context::over_losing_buoyancy, "lava", "This might make you stumble backwards over lava while you are losing your buoyancy. Continue?"},
        Row{possible_forced_prompt_context::into_losing_buoyancy, "lava", "This might make you stumble backwards into lava while you are losing your buoyancy. Continue?"},
        Row{possible_forced_prompt_context::over_expiring_transformation, "deep water", "This might make you stumble backwards over deep water while your transformation is expiring. Continue?"},
        Row{possible_forced_prompt_context::into_expiring_transformation, "lava", "This might make you stumble backwards into lava while your transformation is expiring. Continue?"},
    }));

    Options.language = lang_t::EN;
    Options.lang_name = nullptr;
    i18n_cache_clear();
    REQUIRE(possible_forced_move_prompt(std::get<0>(row), std::get<1>(row))
            == std::get<2>(row));
    Options.language = lang_t::ZH;
    Options.lang_name = "zh";
    i18n_cache_clear();
}

// -----------------------------------------------------------------------------
// 1) UNTRANSLATED rule
// -----------------------------------------------------------------------------
TEST_CASE_METHOD(ZhTranslationFixture,
                 "contextual monster plural arms are extracted",
                 "[zh-translation][message-overlay]")
{
    REQUIRE(string(C_("monster body part plural", "arms")) == "手臂");
    REQUIRE(string(C_("monster body part plural", "strata")) == "云层");
    REQUIRE(string(C_("structured actor possessive", "neutral singular"))
            == "其");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: Issue 66 semantic collision contexts stay distinct",
                 "[zh-translation][issue-66]")
{
    REQUIRE(std::string(jewellery_effect_name(AMU_WILDSHAPE, false))
            == "野性变形");
    REQUIRE(std::string(jewellery_effect_name(AMU_WILDSHAPE, true))
            == "变形");
    REQUIRE(std::string(jewellery_effect_name(AMU_CHEMISTRY, false))
            == "炼金术");
    REQUIRE(std::string(jewellery_effect_name(AMU_CHEMISTRY, true))
            == "炼金");

    REQUIRE(std::string(card_name(CARD_WILD_MAGIC)) == "狂野魔法");
    REQUIRE(std::string(C_("death cause terse", "wild magic"))
            == "野性魔法");
    REQUIRE(std::string(C_("death cause terse", "smitten by Beogh"))
            == "被比欧弗击中");
    REQUIRE(std::string(C_("death cause", "Smitten by Beogh"))
            == "被比欧弗击杀");
    REQUIRE(std::string(C_("shop name suffix", "Shop")) == "店铺");

    init_spell_descs();
    init_spell_name_cache();
    REQUIRE(std::string(spell_title(SPELL_STING)) == "毒刺");
    REQUIRE(std::string(spell_title(SPELL_METAL_SPLINTERS)) == "金属碎片");
    REQUIRE(std::string(spell_title(SPELL_IOOD)) == "毁灭之球");
    REQUIRE(std::string(spell_title(SPELL_SIGN_OF_RUIN)) == "毁灭征兆");
    REQUIRE(std::string(spell_title(SPELL_SUMMON_UNDEAD)) == "召唤亡灵");
    REQUIRE(ability_name(ABIL_KIKU_SIGN_OF_RUIN) == "毁灭征兆");
    REQUIRE(species::name(SP_POLTERGEIST) == "吵闹鬼");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: Issue 66 status lights use full labels",
                 "[zh-translation][issue-66][status]")
{
    REQUIRE(std::string(C_("status", "Flooded")) == "淹水");
    REQUIRE(std::string(C_("status", "Rev")) == "暖机");
    REQUIRE(std::string(C_("status", "Slow")) == "减速");
    REQUIRE(std::string(C_("status", "Water")) == "水域");
    REQUIRE(std::string(C_("status", "Drain")) == "衰竭");
    REQUIRE(std::string(C_("status", "Might")) == "强效");
    REQUIRE(std::string(C_("status", "Invis")) == "隐形");
}

TEST_CASE("UNTRANSLATED rule", "[zh-translation][zh-helpers]")
{
    using Row = std::tuple<std::string, std::string, bool>;
    auto row = GENERATE(table<std::string, std::string, bool>({
        // positives: T_ fallback returns the English key unchanged.
        Row{"You hit %s.",   "You hit %s.",   true},
        Row{"Choose weapon", "Choose weapon", true},
        Row{"plain",         "plain",         true},
        Row{"BIG LETTERS",   "BIG LETTERS",   true},
        Row{"hit it",        "hit it",        true},
        // negatives: actual translation (text != key).
        Row{"命中。",        "You hit %s.",   false},
        Row{"选择武器。",    "Choose weapon", false},
        // numbers-only key not flagged (ASCII letters required).
        Row{"123",           "123",           false},
        // empty text/key.
        Row{"",              "",              false},
        // text == key but key has no letters.
        Row{"()",            "()",            false},
    }));
    const std::string& text = std::get<0>(row);
    const std::string& key  = std::get<1>(row);
    const bool expect_issue = std::get<2>(row);
    INFO("text=\"" << text << "\" key=\"" << key << "\"");
    REQUIRE(rule_untranslated(text, key) == expect_issue);
}

// -----------------------------------------------------------------------------
// 2) MIXED_CN_EN rule
// -----------------------------------------------------------------------------
TEST_CASE("MIXED_CN_EN rule", "[zh-translation][zh-helpers]")
{
    using Row = std::tuple<std::string, bool>;
    auto row = GENERATE(table<std::string, bool>({
        // positives — Chinese with non-whitelisted Latin run >= 3.
        Row{"你 hit it now。",            true},
        Row{"你好，Butterfly！",          true},
        Row{"这是 random text 示例。",     true},
        Row{"我用了 Holy Pleasure 之刃。", true},
        Row{"其名为 Example。",          true},
        // negatives — pure Chinese, or Chinese+whitelisted tag.
        Row{"你命中了它。",               false},
        Row{"他装备 rF+ 的护甲。",          false},   // "rF" 2-char whitelist
        Row{"AC 加 1。",                  false},
        Row{"Trog 暴怒了。",              false},
        Row{"你获得了 Slay +1 增益。",    false},
    }));
    const std::string& text = std::get<0>(row);
    const bool expect_issue = std::get<1>(row);
    INFO("text=\"" << text << "\"");
    REQUIRE(rule_mixed_cn_en(text) == expect_issue);
}

TEST_CASE("MIXED_CN_EN sample is centred on the offending token",
          "[zh-translation][zh-helpers]")
{
    std::string text;
    for (int i = 0; i < 40; ++i)
        text += "前";
    text += "中文前缀 Butterfly 中文后缀";
    const auto issues = scan_text(text, "sample key", "test");
    const auto found = std::find_if(issues.begin(), issues.end(),
        [](const ZhIssue& issue)
        {
            return issue.kind == ZhIssue::MIXED_CN_EN;
        });
    REQUIRE(found != issues.end());
    CHECK(found->sample.find("Butterfly") != std::string::npos);
}

TEST_CASE("embedded Lua errors are detected independently of CJK content",
          "[zh-translation][zh-helpers]")
{
    const std::string real_lua_error =
        "中文 {{[string \"db_embedded_lua\"]:2: attempt to index a nil "
        "value (global 'monster')}}";
    CHECK(rule_embedded_lua_error(real_lua_error));
    CHECK(rule_mixed_cn_en(real_lua_error));

    CHECK(rule_embedded_lua_error(
        "[string \"db_embedded_lua\"]:1: synthetic failure"));
    CHECK_FALSE(rule_embedded_lua_error("普通中文状态说明。"));
}

// -----------------------------------------------------------------------------
// 3) FORMAT_BROKEN rule — exercises the structural subrules
//    (trailing 's'/'x' after CJK, lone %s, %n$s, %s/%d count mismatch)
// -----------------------------------------------------------------------------
TEST_CASE("FORMAT_BROKEN rule", "[zh-translation][zh-helpers]")
{
    using Row = std::tuple<std::string, std::string, bool>;
    auto row = GENERATE(table<std::string, std::string, bool>({
        // conj_verb remnant — 抓取s
        Row{"抓取s 了怪物。", "grab",          true},
        // bare trailing "%s"
        Row{"你受到 %s",        "you do %s damage", true},
        // mprf-p positional specifier
        Row{"命中了 %1$s",      "hit %s",          true},
        // count mismatch (key has 1 spec, text has 2)
        Row{"伤害了 %s 与 %s",  "damaged %s",      true},
        // count match, no pathologies — clean
        Row{"命中了 %s.",        "hit %s",          false},
        // clean English fallback also OK
        Row{"You hit %s.",       "You hit %s.",     false},
        // Chinese with no format specs at all
        Row{"此技能已解除。",    "This ability is over.", false},
        // literal %% preserved on both sides
        Row{"100%% 完成。", "100%% done", false},
        // %% in text but %s in key — mismatch
        Row{"100%% 完成 %s。", "100%% done", true},
    }));
    const std::string& text = std::get<0>(row);
    const std::string& key  = std::get<1>(row);
    const bool expect_issue = std::get<2>(row);
    INFO("text=\"" << text << "\" key=\"" << key << "\"");
    REQUIRE(rule_format_broken(text, key) == expect_issue);
}

// -----------------------------------------------------------------------------
// 4) GARBLED_UTF8 rule
// -----------------------------------------------------------------------------
TEST_CASE("GARBLED_UTF8 rule", "[zh-translation][zh-helpers]")
{
    using Row = std::tuple<std::string, bool>;
    auto row = GENERATE(table<std::string, bool>({
        // negatives — legal UTF-8 + whitespace.
        Row{"正常译。",            false},
        Row{"hello",               false},
        Row{"混合 abc。",          false},
        Row{"100% 命中。",         false},
        Row{"\tnewline\n",         false},
        // positives — U+FFFD or illegal lead/continuation bytes.
        Row{"替换\ufffd 符号。", true},
        Row{std::string("坏\xFE""字符。"), true},
        Row{std::string("坏\xC0""abc"),     true},
        Row{std::string("我\x01 制 1"),     true},
        Row{std::string("尾\xF5\x80\x80\x80"), true},
    }));
    const std::string& text = std::get<0>(row);
    const bool expect_issue = std::get<1>(row);
    INFO("garbled text bytes:");
    REQUIRE(rule_garbled_utf8(text) == expect_issue);
}

// -----------------------------------------------------------------------------
// 5) WHITESPACE_ANOMALY rule
// -----------------------------------------------------------------------------
TEST_CASE("WHITESPACE_ANOMALY rule", "[zh-translation][zh-helpers]")
{
    using Row = std::tuple<std::string, bool>;
    auto row = GENERATE(table<std::string, bool>({
        // negatives — clean
        Row{"正常描述。",        false},
        Row{"短句。",            false},
        Row{"- 项目 One。\n",    false},
        Row{"  - 子弹列表。",      false},
        Row{"\n空白行开始\n",    false},
        // positives — \r, double-space, trailing space
        Row{"残留\r 字符。",     true},
        Row{"双倍  空格。",       true},
        Row{"尾随空格。",        false}, // single trailing handled below
        Row{"前导 空格好。",      false},
    }));
    const std::string& text = std::get<0>(row);
    bool expect_issue = std::get<1>(row);
    // Adjust two ambivalent expectations: rule_whitespace rejects leading
    // space and trailing space exactly. Rows that test single-space boundaries
    // are handled here:
    if (text == "尾随空格。")
        expect_issue = false;            // no trailing space present in source bytes
    if (text == "前导 空格好。" || text == "尾随空格。")
        expect_issue = false;            // single leading space — not flagged by rule
    // Add explicit trailing case:
    // Handled by an extra inline test below, not via table.
    INFO("text=\"" << text << "\"");
    REQUIRE(rule_whitespace(text) == expect_issue);

    // Explicit boundary assertions.
    REQUIRE(rule_whitespace("尾随空格。 ") == true);   // trailing ASCII space
    REQUIRE(rule_whitespace(" 前导空格。") == true);   // leading ASCII space
    REQUIRE(rule_whitespace("没有 空格多余。") == false); // single spaces OK
}

// -----------------------------------------------------------------------------
// 6) INVISIBLE_CHAR rule
// -----------------------------------------------------------------------------
TEST_CASE("INVISIBLE_CHAR rule", "[zh-translation][zh-helpers]")
{
    using Row = std::tuple<std::string, bool>;
    auto row = GENERATE(table<std::string, bool>({
        // negatives — clear text
        Row{"普通文字。",       false},
        Row{"hello 你好",       false},
        Row{"100% 命中。",       false},
        Row{"RT。",              false},
        Row{"",                 false},
        // positives — ZWS / BOM / NBSP / PUA / ZWNJ
        Row{std::string("插\xE2\x80\x8B入."), true},   // U+200B ZWS
        Row{std::string("导\xEF\xBB\xBF头."), true},   // U+FEFF BOM
        Row{std::string("非\xC2\xA0断."), true},        // U+00A0 NBSP
        Row{std::string("私\xEE\x80\x80区."), true},   // U+E000 PUA
        Row{std::string("零\xE2\x80\x8C宽"), true},     // U+200C ZWNJ
    }));
    const std::string& text = std::get<0>(row);
    const bool expect_issue = std::get<1>(row);
    INFO("invisible text bytes:");
    REQUIRE(rule_invisible_char(text) == expect_issue);
}

// -----------------------------------------------------------------------------
// 7) PUNCT_STYLE rule
// -----------------------------------------------------------------------------
TEST_CASE("PUNCT_STYLE rule", "[zh-translation][zh-helpers]")
{
    using Row = std::tuple<std::string, bool>;
    auto row = GENERATE(table<std::string, bool>({
        // negatives — full-width punctuation or all-English fragment.
        Row{"这是一句话，你好。", false},
        Row{"中文括号（鬼）。",    false},
        Row{"hello world",        false},
        Row{"ATK (English)",      false},
        Row{"Label: Test",         false},
        // positives — half-width punct adjacent to Chinese
        Row{"这是半角,父号。",   true},
        Row{"中文.句号。",       true},
        Row{"中文:冒号。",       true},
        Row{"中文(括号)用法。",  true},
        Row{"逗号,半角。",       true},
    }));
    const std::string& text = std::get<0>(row);
    const bool expect_issue = std::get<1>(row);
    INFO("text=\"" << text << "\"");
    REQUIRE(rule_punct_style(text) == expect_issue);
}

// -----------------------------------------------------------------------------
// 8) Aggregated scan_text() — sanity that any single rule adds an issue.
// -----------------------------------------------------------------------------
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: scan_text aggregates multiple issues in one text",
                 "[zh-translation][zh-helpers]")
{
    // A genuinely broken sample: half-width punct + double-space + ASCII run.
    std::string text = "你,Random text  多问题。";
    auto issues = scan_text(text, "key", "test");
    INFO("detected " << issues.size() << " issues:");
    REQUIRE(issues.size() >= 2);
}
