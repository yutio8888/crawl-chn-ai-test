#include "catch_amalgamated.hpp"
#include "AppHdr.h"

#include "artefact.h"
#include "english.h"
#include "database.h"
#include "describe.h"
#include "format.h"
#include "invent.h"
#include "item-name.h"
#include "item-prop.h"
#include "items.h"
#include "lang-en-guard.h"
#include "message.h"
#include "mon-info.h"
#include "mon-util.h"
#include "monster.h"
#include "options.h"
#include "operation-types.h"
#include "pattern.h"
#include "player.h"
#include "player-equip.h"
#include "player-reacts.h"
#include "random.h"
#include "stash.h"
#include "stringutil.h"
#include "tags.h"
#include "tag-version.h"
#include "test_zh_fixture.h"
#include "unwind.h"

TEST_CASE_METHOD(ZhTranslationFixture, "special names: monster display and storage boundaries",
                 "[zh-translation][special-name-quotes]")
{
    init_properties();
    init_monsters();
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        INFO(static_cast<int>(language));
        for (monster_type type : {MONS_SIGMUND, MONS_RAT,
                                  MONS_PANDEMONIUM_LORD, MONS_PLAYER_GHOST,
                                  MONS_PLAYER_ILLUSION})
        {
            INFO(static_cast<int>(type));
            monster_info info(type);
            if (type != MONS_SIGMUND && type != MONS_RAT)
                info.mname = "Test Identity";
            for (description_level_type desc : {DESC_PLAIN, DESC_THE, DESC_A, DESC_ITS})
            {
                INFO(static_cast<int>(desc));
                string raw;
                {
                    ScopedUnquotedNames unquoted;
                    raw = info.full_name(desc);
                }
                const string display = info.full_name(desc);
                if (language == lang_t::EN || type == MONS_RAT)
                    CHECK(display == raw);
                else
                {
                    CHECK(display.find("「") != string::npos);
                    CHECK(display.find("「", display.find("「") + 3) == string::npos);
                    CHECK(display.find("」") != string::npos);
                }
            }
            CHECK(info.db_name().find("「") == string::npos);
        }
        const auto expected_title_rng = [&]() {
            rng::subgenerator sequence(73518041, 719);
            getMiscString("Sigmund title");
            return rng::peek_uint64();
        }();
        {
            rng::subgenerator sequence(73518041, 719);
            monster_info(MONS_SIGMUND).title_name();
            CHECK(rng::peek_uint64() == expected_title_rng);
        }
        const auto before_format = rng::peek_uint64();
        const string narrative_title = language == lang_t::ZH
            ? "可怕的西格蒙德" : "the dreaded Sigmund";
        monster_info(MONS_SIGMUND).title_name(narrative_title);
        CHECK(rng::peek_uint64() == before_format);
        monster_info helpless(MONS_SIGMUND);
        helpless.props[HELPLESS_KEY] = true;
        if (language == lang_t::ZH)
        {
            CHECK(helpless.common_name(DESC_PLAIN) == "无助的「西格蒙德」");
            CHECK(monster_info(MONS_SIGMUND).title_name() == "可怕的「西格蒙德」");
        }
        else
        {
            ScopedUnquotedNames unquoted;
            CHECK(helpless.common_name(DESC_PLAIN) == "helpless Sigmund");
        }
        monster sigmund;
        sigmund.type = MONS_SIGMUND;
        const string stored = name_for_storage(sigmund, DESC_A, true);
        CHECK(stored.find("「") == string::npos);
        CHECK(sigmund.mname.empty());
        if (language == lang_t::EN)
        {
            CHECK(stored == "Sigmund");
            CHECK(sigmund.name(DESC_A, true) == "Sigmund");
        }
        else
        {
            CHECK(sigmund.name(DESC_A, true) == "「西格蒙德」");
            CHECK(make_stringf(T_("You hit %s."), sigmund.name(DESC_THE, true).c_str())
                  == "你击中了「西格蒙德」。");
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture, "special names: artefact rendering preserves identities and queries",
                 "[zh-translation][special-name-quotes]")
{
    init_properties();
    init_monsters();
    unwind_var<player> restore_player(you);
    you = player();
    you.where_are_you = BRANCH_DUNGEON;
    you.depth = 1;
    item_def& item = you.inv[0];
    item.base_type = OBJ_WEAPONS;
    item.sub_type = WPN_LONG_SWORD;
    item.quantity = 1;
    item.rnd = 1;
    item.flags = ISFLAG_IDENTIFIED;
    item.pos = ITEM_IN_INVENTORY;
    item.link = 0;
    item.slot = 'a';
    REQUIRE(make_item_randart(item, true));
    item.plus = 9;
    const string identity = "「巨人杀手」长剑";
    item.props[ARTEFACT_NAME_KEY].get_string() = identity;
    item.inscription = "!w @w7";
    const string appearance = item.props[ARTEFACT_APPEAR_KEY].get_string();
    vector<unsigned char> identity_bytes;
    writer identity_output(&identity_bytes);
    marshallItem(identity_output, item, true);
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        string raw;
        {
            ScopedUnquotedNames unquoted;
            raw = item.name(DESC_PLAIN);
        }
        const string display = item.name(DESC_PLAIN);
        if (language == lang_t::ZH)
        {
            CHECK(display.find("「巨人杀手」长剑") != string::npos);
            CHECK(display.find("「「") == string::npos);
            CHECK(starts_with(display, "+9 「"));
            CHECK(display.find("长剑 {") != string::npos);
            CHECK(display.find("!w @w7") > display.find("」"));
        }
        else
            CHECK(display == raw);
        CHECK(item.props[ARTEFACT_NAME_KEY].get_string() == identity);
        CHECK(item.props[ARTEFACT_APPEAR_KEY].get_string() == appearance);
        CHECK(item.inscription == "!w @w7");
        // History is an existing display snapshot, distinct from object identity.
        get_last_messages(NUM_STORED_MESSAGES, true);
        vector<unsigned char> saved_history;
        writer caller_output(&saved_history);
        save_messages(caller_output);
        {
            unwinder restore_history([&saved_history]() {
                clear_message_store();
                reader caller_input(saved_history);
                caller_input.setMinorVersion(TAG_MINOR_VERSION);
                load_messages(caller_input);
            });
            clear_message_store();
            mprf(T_("You drop %s."), item.name(DESC_A).c_str());
            // An older display snapshot with intrinsic 「」 must also survive.
            mpr(identity);
            const string before = get_last_messages(NUM_STORED_MESSAGES, true);
            vector<unsigned char> bytes;
            writer output(&bytes);
            save_messages(output);
            clear_message_store();
            reader input(bytes);
            input.setMinorVersion(TAG_MINOR_VERSION);
            load_messages(input);
            CHECK(get_last_messages(NUM_STORED_MESSAGES, true) == before);
            CHECK(before.find(identity) != string::npos);
            vector<unsigned char> after;
            writer second_output(&after);
            save_messages(second_output);
            CHECK(after == bytes);
            CHECK(item.props[ARTEFACT_NAME_KEY].get_string() == identity);
        }
        InvEntry entry(item);
        CHECK(entry.get_filter_text().find(identity) != string::npos);
        CHECK(digit_inscription_to_item('7', OPER_WIELD) == &item);
        struct decorated_entry : InvEntry
        {
            explicit decorated_entry(const item_def &i) : InvEntry(i) {}
            string get_text() const override
            {
                return "<red>100 gold " + InvEntry::get_text() + "</red>";
            }
        } shop_label(item);
        CHECK(shop_label.get_filter_text().find("100 gold") != string::npos);
        CHECK(shop_label.get_filter_text().find(identity) != string::npos);
        const auto results = inventory_search(plaintext_pattern(identity, true));
        REQUIRE(results.size() == 1);
        CHECK(results[0].item.props[ARTEFACT_NAME_KEY].get_string() == identity);
        CHECK(results[0].match == Stash::stash_item_name(item));
        CHECK(item.name(DESC_A, false, false, true, false, false).find("『")
              == string::npos);
        vector<unsigned char> after_display;
        writer identity_after(&after_display);
        marshallItem(identity_after, item, true);
        CHECK(after_display == identity_bytes);
        reader identity_input(after_display);
        identity_input.setMinorVersion(TAG_MINOR_VERSION);
        item_def loaded;
        unmarshallItem(identity_input, loaded);
        CHECK(loaded.props[ARTEFACT_NAME_KEY].get_string() == identity);
        CHECK(loaded.inscription == item.inscription);
        item_def unknown = item;
        unknown.flags &= ~ISFLAG_IDENTIFIED;
        // No new identity marker may appear before the item's real name is known.
        if (!unknown.is_identified())
        {
            const string unidentified = unknown.name(DESC_A);
            string unquoted_appearance;
            {
                ScopedUnquotedNames raw_mode;
                unquoted_appearance = unknown.name(DESC_A);
            }
            CHECK(unidentified == unquoted_appearance);
        }
    }
    item_def unrand;
    unrand.quantity = 1;
    const auto prior_status = get_unique_item_status(UNRAND_WYRMBANE);
    REQUIRE(make_item_unrandart(unrand, UNRAND_WYRMBANE));
    unwinder restore_status([&unrand, prior_status]() {
        set_unique_item_status(unrand, prior_status);
    });
    unrand.flags |= ISFLAG_IDENTIFIED;
    CHECK(unrand.name(DESC_PLAIN).find("+8 「屠龙者」骑枪") == 0);
    CHECK(unrand.name(DESC_PLAIN).find("「屠龙者」骑枪") != string::npos);
    InvEntry unrand_entry(unrand);
    CHECK(unrand_entry.get_filter_text().find("「屠龙者」骑枪") != string::npos);
    you.inv[1] = unrand;
    you.inv[1].pos = ITEM_IN_INVENTORY;
    you.inv[1].link = 1;
    you.inv[1].slot = 'b';
    const auto unrand_search = inventory_search(
        plaintext_pattern("「屠龙者」骑枪", true));
    REQUIRE(unrand_search.size() == 1);
    CHECK(unrand_search[0].item.special == UNRAND_WYRMBANE);
    CHECK(get_unrand_name_en(unrand) == string("lance \"Wyrmbane\""));
    CHECK(get_artefact_name(unrand) == "「屠龙者」骑枪");
    item_def boots;
    boots.quantity = 1;
    const auto boots_status = get_unique_item_status(UNRAND_SEVEN_LEAGUE_BOOTS);
    REQUIRE(make_item_unrandart(boots, UNRAND_SEVEN_LEAGUE_BOOTS));
    unwinder restore_boots([&]() { set_unique_item_status(boots, boots_status); });
    boots.flags |= ISFLAG_IDENTIFIED;
    boots.plus = 4;
    CHECK(starts_with(boots.name(DESC_PLAIN), "+4 「七里格靴」"));
    CHECK(quote_special_name("<red>「西格蒙德」</red>")
          == "<red>「西格蒙德」</red>");
}

TEST_CASE_METHOD(ZhTranslationFixture, "special names: poison identity remains undecorated",
                 "[zh-translation][special-name-quotes]")
{
    init_properties();
    init_monsters();
    unwind_var<player> restore_player(you);
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        you = player();
        you.species = SP_HUMAN;
        you.hp = you.hp_max = 50;
        monster source;
        source.type = MONS_SIGMUND;
        REQUIRE(you.poison(&source, 5, true));
        CHECK(you.props[POISONER_KEY].get_string()
              == (language == lang_t::ZH ? "西格蒙德" : "Sigmund"));
        CHECK(source.mname.empty());
        CHECK(source.name(DESC_A, true)
              == (language == lang_t::ZH ? "「西格蒙德」" : "Sigmund"));
    }
}

TEST_CASE_METHOD(ZhTranslationFixture, "special names: actual artefact attunement decorates only display",
                 "[zh-translation][special-name-quotes]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        you = player();
        you.species = SP_HUMAN;
        you.hp = you.hp_max = 100;
        you.magic_points = you.max_magic_points = 20;
        item_def& item = you.inv[0];
        item.quantity = 1;
        const auto prior_status = get_unique_item_status(UNRAND_VITALITY);
        REQUIRE(make_item_unrandart(item, UNRAND_VITALITY));
        unwinder restore_status([&item, prior_status]() {
            set_unique_item_status(item, prior_status);
        });
        item.flags |= ISFLAG_IDENTIFIED;
        item.link = 0;
        item.pos = ITEM_IN_INVENTORY;
        const string identity = get_artefact_name(item);
        you.equipment.add(item, SLOT_AMULET);
        you.check_hp_regen_attunement = true;
        you.check_mp_regen_attunement = true;
        msg::tee messages;
        maybe_attune_regen_items();
        const string text = messages.get_store();
        CHECK(text.find(quote_special_name(identity)) != string::npos);
        CHECK(get_artefact_name(item) == identity);
        CHECK_FALSE(you.check_hp_regen_attunement);
        if (language == lang_t::EN)
        {
            CHECK(text.find("Your " + identity + " attunes itself to your body")
                  != string::npos);
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture, "special names: paired inner punctuation is display only",
                 "[zh-translation][special-name-quotes]")
{
    const vector<pair<string, string>> cases = {
        {"plain name", "「plain name」"},
        {"blade \"Wyrmbane\"", "「blade 『Wyrmbane』」"},
        {"blade 「Giant Slayer」", "「blade 『Giant Slayer』」"},
        {"blade \"A\" and \"B\"", "「blade 『A』 and 『B』」"},
        {"blade \"unpaired", "「blade \"unpaired」"},
        {"blade 「unpaired", "「blade 「unpaired」"},
        {"blade unpaired」", "「blade unpaired」」"},
        {"blade \"pair\" \"unpaired", "「blade 『pair』 \"unpaired」"},
        {"blade 「outer「inner」end」", "「blade 『outer『inner』end』」"},
        {"<red>blade \"Wyrmbane\"</red>", "「<red>blade 『Wyrmbane』</red>」"},
        {"<red>「blade \"Wyrmbane\"」</red>", "<red>「blade 『Wyrmbane』」</red>"},
    };
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (const auto &entry : cases)
        {
            INFO(entry.first);
            CHECK(quote_special_name(entry.first)
                  == (language == lang_t::ZH ? entry.second : entry.first));
        }
        const string name = quote_special_name("blade \"Wyrmbane\"");
        CHECK(make_stringf("%s says \"outside\".", name.c_str())
              == name + " says \"outside\".");
    }
    CHECK(quote_special_name("「blade 『Wyrmbane』」") == "「blade 『Wyrmbane』」");
}

TEST_CASE_METHOD(ZhTranslationFixture, "artefact cores use one name marker outside modifiers",
                 "[zh-translation][special-name-quotes][artefact-core-quotes]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    item_def item;
    item.base_type = OBJ_WEAPONS;
    item.sub_type = WPN_LONG_SWORD;
    item.quantity = 1;
    item.rnd = 1;
    item.flags = ISFLAG_IDENTIFIED;
    REQUIRE(make_item_randart(item, true));
    item.plus = 9;
    item.inscription = "!w";
    const vector<pair<string, string>> names = {
        {"「巨人杀手」长剑", "「巨人杀手」长剑"},
        {"\"Old Slayer\"长剑", "「Old Slayer」长剑"},
        {"毒菌之匕首", "「毒菌之匕首」"},
        {"Latin's blade", "「Latin's blade」"},
        {"unpaired\" blade", "「unpaired\" blade」"},
        {"「甲」与\"乙\"长剑", "「甲」与「乙」长剑"},
        {"<red>「巨人杀手」</red>长剑", "<red>「巨人杀手」</red>长剑"},
    };
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (const auto &entry : names)
        {
            INFO(entry.first);
            item.props[ARTEFACT_NAME_KEY].get_string() = entry.first;
            const string expected = "+9 "
                + (language == lang_t::ZH ? entry.second : entry.first);
            CHECK(starts_with(item.name(DESC_PLAIN), expected));
            InvEntry menu_entry(item);
            CHECK(menu_entry.get_text().find(expected) != string::npos);
            CHECK(menu_entry.get_filter_text().find(entry.first) != string::npos);
            describe_info inspection;
            get_item_desc(item, inspection);
            CHECK(inspection.body.str().find(expected) != string::npos);
            you.inv[0] = item;
            you.inv[0].pos = ITEM_IN_INVENTORY;
            you.inv[0].link = 0;
            you.inv[0].slot = 'a';
            CHECK(starts_with(you.inv[0].name(DESC_INVENTORY),
                              string(language == lang_t::ZH ? "a - " : "a - the ")
                              + expected));
            CHECK(item.name(DESC_PLAIN).find("!w") > expected.size());
            CHECK(item.props[ARTEFACT_NAME_KEY].get_string() == entry.first);
            const string before = item.name(DESC_PLAIN);
            vector<unsigned char> bytes;
            writer output(&bytes);
            marshallItem(output, item, true);
            reader input(bytes);
            input.setMinorVersion(TAG_MINOR_VERSION);
            item_def loaded;
            unmarshallItem(input, loaded);
            CHECK(loaded.props[ARTEFACT_NAME_KEY].get_string() == entry.first);
            CHECK(loaded.name(DESC_PLAIN) == before);
            {
                ScopedUnquotedNames storage;
                CHECK(starts_with(item.name(DESC_PLAIN), "+9 " + entry.first));
            }
            item.flags |= ISFLAG_CHAOTIC | ISFLAG_REPLICA;
            const string modified = item.name(DESC_PLAIN);
            CHECK(modified.find(expected) == string::npos);
            CHECK(modified.find(language == lang_t::ZH ? entry.second : entry.first)
                  > modified.find("+9 "));
            item.flags &= ~(ISFLAG_CHAOTIC | ISFLAG_REPLICA);
        }
        item_def ordinary = item;
        ordinary.flags &= ~ISFLAG_ARTEFACT_MASK;
        CHECK(ordinary.name(DESC_PLAIN).find("「") == string::npos);
        // Equipped gizmos are artefacts too; legacy names have no recipe.
        item_def gizmo;
        gizmo.base_type = OBJ_GIZMOS;
        gizmo.quantity = 1;
        gizmo.rnd = 1;
        gizmo.flags = ISFLAG_RANDART | ISFLAG_IDENTIFIED;
        gizmo.props[ARTEFACT_NAME_KEY].get_string() = "prototype device";
        CHECK(gizmo.name(DESC_PLAIN, false, false, false)
              == (language == lang_t::ZH ? "「prototype device」" : "prototype device"));
        CHECK(gizmo.props[ARTEFACT_NAME_KEY].get_string() == "prototype device");
    }
}
