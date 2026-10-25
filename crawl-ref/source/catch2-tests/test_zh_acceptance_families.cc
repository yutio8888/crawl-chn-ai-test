#include "catch_amalgamated.hpp"
#include "AppHdr.h"

#include <algorithm>

#include "artefact.h"
#include "command.h"
#include "database.h"
#include "invent.h"
#include "item-prop.h"
#include "item-status-flag-type.h"
#include "macro.h"
#include "message.h"
#include "mon-info.h"
#include "mon-util.h"
#include "player.h"
#include "random.h"
#include "state.h"
#include "stringutil.h"
#include "test_zh_fixture.h"
#include "throw.h"
#include "unwind.h"
#include "xp-evoker-data.h"

namespace
{
bool has_cjk(const string& text)
{
    return std::any_of(text.begin(), text.end(), [](unsigned char c) {
        return c >= 0xe0;
    });
}
}

TEST_CASE("acceptance: live key help localizes descriptions before key insertion",
          "[zh-translation][acceptance-fixes]")
{
    unwind_var<game_type> game(crawl_state.type, GAME_TYPE_NORMAL);
    const int old_ability_key = command_to_key(CMD_USE_ABILITY);
    const int replacement = command_to_key(CMD_EVOKE);
    const command_type old_command = key_to_command(replacement, KMC_DEFAULT);
    REQUIRE(old_ability_key != replacement);
    unwinder restore_bindings([=]() {
        bind_command_to_key(old_command, replacement);
        bind_command_to_key(CMD_USE_ABILITY, old_ability_key);
    });
    bind_command_to_key(CMD_USE_ABILITY, replacement);
    const string rebound = command_to_string(CMD_USE_ABILITY);
    const char* english_sections[] = {
        "Rest:", "Other Gameplay Actions:", "Non-Gameplay Commands / Info",
        "Game Saving and Quitting:", "Player Character Information:",
        "Dungeon Interaction and Information:", "Inventory management:",
        "Item Interaction:", "Additional help:",
    };
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        string header, text;
        REQUIRE(help_popup_state_for_test('?', 0, header, text) == '?');
        for (const char* section : english_sections)
        {
            INFO(section);
            CHECK((text.find(section) != string::npos) == (language == lang_t::EN));
        }
        CHECK((header.find("Key help") != string::npos) == (language == lang_t::EN));
        CHECK(text.find(rebound + "!") != string::npos);
        CHECK(command_to_string(CMD_USE_ABILITY) == rebound);
        CHECK(text.find("<w>%") == string::npos);
        CHECK((text.find("cast spell, abort without targets") != string::npos)
              == (language == lang_t::EN));
    }
}

TEST_CASE("acceptance: all inscription operations build one localized warning",
          "[zh-translation][acceptance-fixes]")
{
    init_properties();
    rng::subgenerator deterministic(425202680);
    unwind_var<player> restore_player(you);
    you = player();
    you.species = SP_HUMAN;
    item_def item;
    item.base_type = OBJ_JEWELLERY;
    item.sub_type = RING_PROTECTION;
    item.quantity = 1;
    item.flags = ISFLAG_IDENTIFIED;
    REQUIRE(make_item_randart(item, true));
    item.flags |= ISFLAG_IDENTIFIED;
    artefact_set_property(item, ARTP_PREVENT_TELEPORTATION, 1);
    const pair<operation_types, const char*> operations[] = {
        {OPER_WIELD, "wield"}, {OPER_QUAFF, "quaff"}, {OPER_DROP, "drop"},
        {OPER_TAKEOFF, "take off"}, {OPER_WEAR, "wear"}, {OPER_PUTON, "put on"},
        {OPER_REMOVE, "remove"}, {OPER_READ, "read"}, {OPER_MEMORISE, "memorise from"},
        {OPER_ZAP, "zap"}, {OPER_FIRE, "fire"}, {OPER_EVOKE, "evoke"},
        {OPER_QUIVER, "quiver"}, {OPER_EQUIP, "equip"}, {OPER_UNEQUIP, "unequip"},
        {OPER_ANY, "choose"},
    };
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        for (const auto& operation : operations)
        {
            INFO(operation.second);
            you.duration[DUR_TELEPORT] = 0;
            const string ordinary = item_warning_prompt(item, operation.first);
            CHECK(ordinary.find(item.name(DESC_A)) != string::npos);
            if (language == lang_t::EN)
                CHECK(ordinary == "Really " + string(operation.second) + " " + item.name(DESC_A) + "?");
            else
            {
                CHECK(ordinary.find("Really") == string::npos);
                CHECK(has_cjk(C_("item operation", operation.second)));
                CHECK(ordinary.find(C_("item operation", operation.second)) != string::npos);
            }
            you.duration[DUR_TELEPORT] = 2;
            const string teleporting = item_warning_prompt(item, operation.first);
            if (operation.first == OPER_EQUIP)
            {
                REQUIRE(needs_notele_warning(item, operation.first));
                CHECK(teleporting != ordinary);
                CHECK(teleporting.find(T_(" while about to teleport")) != string::npos);
            }
            else
                CHECK(teleporting == ordinary);
            CHECK(teleporting.find("%s") == string::npos);
        }
    }
}

TEST_CASE("acceptance: every XP evoker uses localized noisy silent and generic messages",
          "[zh-translation][acceptance-fixes]")
{
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        for (const auto& row : xp_evoker_data)
        for (bool silent : {false, true})
        for (int gained : {1, 2})
        {
            INFO("evoker=" << row.first << " silent=" << silent << " gained=" << gained);
            item_def item;
            item.base_type = OBJ_MISCELLANY;
            item.sub_type = row.first;
            item.quantity = 1;
            item.flags = ISFLAG_IDENTIFIED;
            const string original = silent ? row.second.recharge_msg.silent
                                           : row.second.recharge_msg.noisy;
            string expected;
            if (!original.empty())
            {
                CHECK((string(T_(original.c_str())) != original) == (language == lang_t::ZH));
                expected = make_stringf(T_(original.c_str()), item.name(DESC_YOUR).c_str());
            }
            else if (language == lang_t::EN)
                expected = item.name(DESC_YOUR) + (row.second.max_charges == 1
                    ? " has recharged." : " has regained " + std::to_string(gained)
                        + (gained == 1 ? " charge." : " charges."));
            msgwin_temporary_mode temporary;
            unwinder rollback([]() { msgwin_clear_temporary(); });
            msg::tee messages;
            print_xp_evoker_recharge(item, gained, silent);
            const string observed = messages.get_store();
            REQUIRE_FALSE(observed.empty());
            if (!expected.empty())
                CHECK(observed.find(expected) != string::npos);
            CHECK(observed.find("%s") == string::npos);
            CHECK(observed.find("%d") == string::npos);
            CHECK(has_cjk(observed) == (language == lang_t::ZH));
            if (language == lang_t::ZH && original.empty())
            {
                CHECK(observed.find("has regained") == string::npos);
                CHECK(observed.find("has recharged") == string::npos);
                if (row.second.max_charges > 1)
                    CHECK(observed.find(std::to_string(gained)) != string::npos);
            }
        }
    }
}

TEST_CASE("acceptance: missile annotations localize effects without changing probabilities",
          "[zh-translation][acceptance-fixes]")
{
    init_monsters();
    item_def item;
    item.base_type = OBJ_MISSILES;
    item.sub_type = MI_DART;
    item.quantity = 1;
    monster_info target(MONS_ORC);
    target.can_go_frenzy = true;
    target.hd = 1; // Both brands have an unconditional 100% chance against this HD.
    set_resist(target.mresists, MR_RES_POISON, 0);
    for (special_missile_type brand : {SPMSL_BLINDING, SPMSL_FRENZY})
    {
        item.brand = brand;
        for (lang_t language : {lang_t::ZH, lang_t::EN})
        {
            TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
            const auto description = missile_target_descriptions(target, item);
            REQUIRE(description.size() == 1);
            CHECK(description[0].find("100%") != string::npos);
            if (language == lang_t::EN)
                CHECK(description[0] == string("chance to ")
                    + (brand == SPMSL_FRENZY ? "frenzy" : "blind") + " on hit: 100%");
            else
            {
                CHECK(has_cjk(description[0]));
                CHECK(description[0].find("blind") == string::npos);
                CHECK(description[0].find("frenzy") == string::npos);
            }
            set_resist(target.mresists, MR_RES_POISON, 3);
            CHECK(missile_target_descriptions(target, item) == vector<string>{T_("immune")});
            set_resist(target.mresists, MR_RES_POISON, 0);
            if (brand == SPMSL_FRENZY)
            {
                target.can_go_frenzy = false;
                CHECK(missile_target_descriptions(target, item) == vector<string>{T_("immune")});
                target.can_go_frenzy = true;
            }
        }
    }
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        item.sub_type = MI_JAVELIN;
        item.brand = SPMSL_SILVER;
        target.mb.set(MB_CHAOTIC);
        CHECK(missile_target_descriptions(target, item) == vector<string>{T_("chaotic")});
        target.mb.set(MB_CHAOTIC, false);
        CHECK(missile_target_descriptions(target, item).empty());
        item.sub_type = MI_THROWING_NET;
        item.brand = SPMSL_NORMAL;
        monster_info insubstantial(MONS_WRAITH);
        CHECK(missile_target_descriptions(insubstantial, item)
              == vector<string>{T_("immune to nets")});
        monster_info blinker(MONS_BLINK_FROG);
        REQUIRE(blinker.net_escape_capable());
        CHECK(missile_target_descriptions(blinker, item)
              == vector<string>{T_("can blink free")});
        CHECK(has_cjk(T_("chaotic")) == (language == lang_t::ZH));
        CHECK(has_cjk(T_("immune to nets")) == (language == lang_t::ZH));
        CHECK(has_cjk(T_("can blink free")) == (language == lang_t::ZH));
    }
}
