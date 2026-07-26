#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "i18n.h"                // T_()
#include "ability.h"
#include "ability-type.h"
#include "art-enum.h"
#include "artefact.h"
#include "database.h"
#include "decks.h"
#include "describe.h"
#include "describe-god.h"
#include "dungeon.h"
#include "duration-type.h"
#include "env.h"
#include "english.h"
#include "hiscores.h"
#include "item-status-flag-type.h"
#include "item-name.h"
#include "item-prop.h"
#include "item-prop-enum.h"
#include "jobs.h"
#include "mapdef.h"
#include "mgen-data.h"
#include "mon-util.h"
#include "movement-i18n.h"
#include "mutation.h"
#include "options.h"
#include "player.h"
#include "random.h"
#include "religion.h"
#include "skills.h"
#include "shout.h"
#include "species.h"
#include "species-type.h"
#include "spl-util.h"
#include "spell-type.h"
#include "stringutil.h"
#include "status.h"
#include "tags.h"
#include "terrain.h"
#include "transform.h"
#include "unicode.h"
#include "test_zh_fixture.h"
#include "test_zh_helpers.h"
#include "unwind.h"

#include <cstring>
#include <array>
#include <string>
#include <tuple>
#ifdef UNIX
#include <fcntl.h>
#include <unistd.h>
#endif

namespace
{
#ifdef UNIX
int count_open_file_descriptors()
{
    const long system_limit = sysconf(_SC_OPEN_MAX);
    const int scan_limit = system_limit > 0 && system_limit < 4096
                         ? static_cast<int>(system_limit) : 4096;
    int count = 0;
    for (int fd = 0; fd < scan_limit; ++fd)
    {
        if (fcntl(fd, F_GETFD) != -1)
            ++count;
    }
    return count;
}
#endif

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
                 "zh: repeated TextDB initialization keeps descriptor ownership stable",
                 "[zh-translation][textdb][fd-lifecycle]")
{
#ifdef UNIX
    const int before = count_open_file_descriptors();
    for (int i = 0; i < 4; ++i)
        databaseSystemInit();
    const int after = count_open_file_descriptors();

    CHECK(after == before);
#else
    SUCCEED("File-descriptor counting is only available on Unix builds.");
#endif
    CHECK(std::string(T_("You hit %s.")) != "You hit %s.");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: a language without TextDB inputs falls back safely",
                 "[zh-translation][textdb][language-lifecycle]")
{
    Options.language = lang_t::ZH;
    Options.lang_name = "zz-no-textdb";
    databaseSystemInit();
    CHECK(std::string(T_("You hit %s.")) == "You hit %s.");

    Options.lang_name = "zh";
    databaseSystemInit();
    CHECK(std::string(T_("You hit %s.")) != "You hit %s.");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: character mechanics use their display contexts",
                 "[zh-translation][character-mechanics][issue-27]")
{
    CHECK(std::string(mutation_name(MUT_CLEVER))
          == std::string(C_("mutation", "clever")));
    CHECK(std::string(mutation_name(MUT_CLEVER))
          != std::string(T_("clever")));

    unwind_var<player> restore_player(you);
    you = player();
    you.duration[DUR_NO_SCROLLS] = 10;

    status_info info;
    REQUIRE(fill_status_info(STATUS_NO_SCROLL, info));
    CHECK(info.short_text == C_("status", "unable to read"));
    CHECK(info.long_text == C_("status", "You cannot read scrolls."));
    CHECK(info.long_text != "You cannot read scrolls.");
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
                 "zh: Issue 16 identity accessors stay canonical at display boundaries",
                 "[zh-translation][issue-16][protocol]")
{
    init_spell_descs();
    init_spell_name_cache();

    REQUIRE(std::string(_god_name_en(GOD_ZIN)) == "Zin");
    REQUIRE(std::string(get_job_name_en(JOB_FIGHTER)) == "Fighter");
    REQUIRE(std::string(skill_name_en(SK_FIGHTING)) == "Fighting");
    REQUIRE(std::string(spelltype_long_name_en(spschool::fire)) == "Fire");
    REQUIRE(std::string(spell_english_name(SPELL_BLINK)) == "Blink");
#if TAG_MAJOR_VERSION == 34
    REQUIRE(std::string(_god_name_en(GOD_PAKELLAS)) == "Pakellas");
#endif

    CHECK(god_name(GOD_ZIN) != _god_name_en(GOD_ZIN));
    CHECK(std::string(get_job_name(JOB_FIGHTER))
          != get_job_name_en(JOB_FIGHTER));
    CHECK(std::string(skill_name(SK_FIGHTING)) != skill_name_en(SK_FIGHTING));
    CHECK(std::string(spelltype_long_name(spschool::fire))
          != spelltype_long_name_en(spschool::fire));
    CHECK(std::string(spell_title(SPELL_BLINK))
          != spell_english_name(SPELL_BLINK));
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: god titles use their display context with fallback",
                 "[zh-translation][god-title][i18n-context]")
{
    unwind_var<uint8_t> no_vehumet_penance(
        you.penance[GOD_VEHUMET], 0);
    unwind_var<uint8_t> no_trog_penance(you.penance[GOD_TROG], 0);
    unwind_var<uint8_t> no_jiyva_penance(you.penance[GOD_JIYVA], 0);
    unwind_var<uint8_t> no_ashenzari_penance(
        you.penance[GOD_ASHENZARI], 0);
    unwind_var<uint8_t> no_zin_penance(you.penance[GOD_ZIN], 0);

    REQUIRE(god_title(GOD_VEHUMET, SP_HUMAN, 0) == "温顺者");
    REQUIRE(god_title(GOD_TROG, SP_HUMAN, piety_breakpoint(1))
            == "狂乱者");
    REQUIRE(god_title(GOD_JIYVA, SP_HUMAN, piety_breakpoint(0))
            == "软泥");
    REQUIRE(god_title(GOD_ASHENZARI, SP_HUMAN, 1) == "受诅咒者");

    // Context-free legacy title keys remain valid through C_() fallback.
    REQUIRE(god_title(GOD_ZIN, SP_HUMAN, 0) == "亵渎者");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 16 TextDB lookup consumes identical gameplay RNG in EN and ZH",
                 "[zh-translation][issue-16][textdb][rng]")
{
    struct observation
    {
        string message;
        uint64_t state;
        uint64_t count;
        int next;
    };

    const auto observe = [](lang_t language, const string &key)
    {
        Options.language = language;
        Options.lang_name = language == lang_t::ZH ? "zh" : nullptr;
        i18n_cache_clear();
        rng::subgenerator scoped_rng(0x1600160016001600ULL,
                                     0xabcddcba12344321ULL);
        observation result;
        result.message = getSpeakString(key);
        result.state = rng::current_generator().get_state();
        result.count = rng::current_generator().get_count();
        result.next = random2(1000000);
        return result;
    };

    const observation english = observe(lang_t::EN, "Zin welcome");
    const observation chinese = observe(lang_t::ZH, "Zin welcome");
    REQUIRE_FALSE(english.message.empty());
    REQUIRE_FALSE(chinese.message.empty());
    CHECK(english.state == chinese.state);
    CHECK(english.count == chinese.count);
    CHECK(english.next == chinese.next);

    const observation en_missing = observe(lang_t::EN, "issue16 missing key");
    const observation zh_missing = observe(lang_t::ZH, "issue16 missing key");
    CHECK(en_missing.message.empty());
    CHECK(zh_missing.message.empty());
    CHECK(en_missing.state == zh_missing.state);
    CHECK(en_missing.count == zh_missing.count);
    CHECK(en_missing.next == zh_missing.next);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: Issue 16 god-only artefact fallback uses canonical keys",
                 "[zh-translation][issue-16][artefact]")
{
    item_def item;
    item.base_type = OBJ_WEAPONS;
    item.sub_type = WPN_DAGGER;
    item.quantity = 1;
    item.flags = ISFLAG_RANDART | ISFLAG_IDENTIFIED;
    item.orig_monnum = -GOD_ASHENZARI;

    const auto observe = [&item](lang_t language)
    {
        Options.language = language;
        Options.lang_name = language == lang_t::ZH ? "zh" : nullptr;
        i18n_cache_clear();

        // Pick a deterministic stream where _pick_db_name() succeeds and
        // Ashenzari's fallback produces a name within the production limit.
        uint64_t seed = 0;
        for (uint64_t candidate = 1; candidate < 10000; ++candidate)
        {
            rng::subgenerator candidate_rng(candidate, 0x16a57eULL);
            if (!coinflip())
                continue;
            REQUIRE(getRandNameString("Ashenzari weapon").empty());
            const string candidate_name = replace_name_parts(
                getRandNameString("Ashenzari"), item);
            if (!candidate_name.empty() && strwidth(candidate_name) <= 25)
            {
                seed = candidate;
                break;
            }
        }
        REQUIRE(seed != 0);

        string fallback_name;
        {
            rng::subgenerator expected_rng(seed, 0x16a57eULL);
            REQUIRE(coinflip());
            REQUIRE(getRandNameString("Ashenzari weapon").empty());
            fallback_name = replace_name_parts(
                getRandNameString("Ashenzari"), item);
        }
        REQUIRE_FALSE(fallback_name.empty());

        const string base_name = item_base_name(item);
        const string expected = language == lang_t::ZH
            ? fallback_name + base_name
            : base_name + " " + fallback_name;
        rng::subgenerator actual_rng(seed, 0x16a57eULL);
        return std::make_pair(make_artefact_name(item), expected);
    };

    const auto english = observe(lang_t::EN);
    const auto chinese = observe(lang_t::ZH);
    CHECK(english.first == english.second);
    CHECK(chinese.first == chinese.second);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: Issue 16 real score entries keep protocol fields English",
                 "[zh-translation][issue-16][hiscores]")
{
    unwind_var<player> restore_player(you);
    you = player();
    you.your_name = "Issue16";
    you.species = SP_HUMAN;
    you.char_class = JOB_MONK;
    you.chr_class_name = get_job_name(you.char_class);
    you.set_position(coord_def(20, 20));

    const coord_def player_position = you.pos();
    const unsigned old_map_id = env.level_map_ids(player_position);
    unwinder restore_map_id([player_position, old_map_id]() {
        env.level_map_ids(player_position) = old_map_id;
    });
    env.level_map_ids(player_position) = INVALID_MAP_INDEX;

    for (skill_type sk = SK_FIRST_SKILL; sk < NUM_SKILLS; ++sk)
        you.skills[sk] = 0;
    you.skills[SK_FIGHTING] = 27;
    you.skills[SK_AXES] = 15;
    you.duration[DUR_HASTE] = 100;

    REQUIRE(Options.language == lang_t::ZH);
    scorefile_entry entry;
    entry.init_death_cause(0, MID_NOBODY, KILLED_BY_QUITTING, "", nullptr);
    entry.init(1600000000);
    const string raw = entry.raw_string();
    REQUIRE_FALSE(raw.empty());

    const xlog_fields fields = entry.get_fields();
    CHECK(fields.str_field("title") == "Conqueror");
    CHECK(fields.str_field("maxskills") == "Fighting");
    CHECK(fields.str_field("fifteenskills") == "Fighting,Axes");
    CHECK(fields.str_field("status") == "agile,hasted");
    CHECK(raw.find("title=Conqueror") != string::npos);
    CHECK(raw.find("maxskills=Fighting") != string::npos);
    CHECK(raw.find("fifteenskills=Fighting,Axes") != string::npos);
    CHECK(raw.find("status=agile,hasted") != string::npos);

    CHECK(fields.str_field("title") != player_title(false));
    CHECK(fields.str_field("maxskills") != skill_name(SK_FIGHTING));
    CHECK(fields.str_field("fifteenskills")
          != string(skill_name(SK_FIGHTING)) + "," + skill_name(SK_AXES));
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
                 "zh: Issue 21 display boundaries translate ugly, shout, and wall keys",
                 "[zh-translation][issue-21][display-boundary]")
{
    const auto require_translated = [](const char* key)
    {
        INFO("key=\"" << key << "\"");
        REQUIRE(std::string(T_(key)) != key);
    };

    for (const char* key : {
             " basks in your mutagenic energy and changes!",
             " basks in the mutagenic energy from its kin and changes!",
             " basks in the mutagenic energy and changes!",
             "slime", "weird stuff", "rock"})
    {
        require_translated(key);
    }

    for (const char* key : {"shout", "yell", "scream", "meow", "yowl",
                            "caterwaul", "croak", "ribbit", "bellow",
                            "bark", "howl", "screech", "wail", "shriek",
                            "growl", "hiss", "sporulate"})
    {
        require_translated(key);
    }

    // Species and form verbs are translated at the display boundary. The
    // Chinese article helper must still avoid English articles.
    CHECK(species::shout_verb(SP_BARACHI, 2, false) == T_("bellow"));
    CHECK(species::shout_verb(SP_FELID, 0, true) == T_("hiss"));
    CHECK(species::shout_verb(SP_POLTERGEIST, 1, false) == T_("shriek"));
    const transformation saved_form = you.form;
    you.form = transformation::fungus;
    CHECK(you.shout_verb(false) == T_("sporulate"));
    CHECK(uppercase_first(you.shout_verb(false)) == T_("sporulate"));
    you.form = saved_form;
    CHECK(article_a("howl") == "howl");
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
            "塞雷波夫之剑"},
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
                 "zh: fixed artefact descriptions use canonical English keys",
                 "[zh-translation][artefact-description]")
{
    item_def item;
    item.quantity = 1;
    const unique_item_status_type prior_status =
        get_unique_item_status(UNRAND_CEREBOV);
    REQUIRE(make_item_unrandart(item, UNRAND_CEREBOV));
    unwinder restore_status([&item, prior_status]() {
        set_unique_item_status(item, prior_status);
    });
    item.flags |= ISFLAG_IDENTIFIED;

    REQUIRE(get_artefact_name(item) == "塞雷波夫之剑");
    REQUIRE(string(get_unrand_name_en(item)) == "sword of Cerebov");
    REQUIRE(getLongDescription(get_artefact_name(item)).empty());
    const string canonical = getLongDescription(get_unrand_name_en(item));
    REQUIRE_FALSE(canonical.empty());
    REQUIRE(get_item_description(item).find(trimmed_string(canonical))
            != string::npos);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: gizmo recipe identity localizes without consuming RNG",
                 "[zh-translation][gizmo][rng]")
{
    rng::subgenerator scoped_rng(0x2900290029002900ULL,
                                 0x29c09c09c09c09c0ULL);
    const misc_string_recipe noun = selectMiscStringRecipe("gizmo_noun");
    const misc_string_recipe modifier =
        selectMiscStringRecipe("gizmo_modifier");
    const misc_string_recipe adjective =
        selectMiscStringRecipe("gizmo_adjective");
    REQUIRE_FALSE(noun.locator.empty());
    REQUIRE_FALSE(modifier.locator.empty());
    REQUIRE_FALSE(adjective.locator.empty());

    item_def item;
    item.base_type = OBJ_GIZMOS;
    item.quantity = 1;
    item.rnd = 1;
    item.props[ARTEFACT_NAME_KEY].get_string() =
        adjective.english + " " + noun.english;
    item.props[GIZMO_NAME_RECIPE_KEY].get_string() =
        "v1|2|" + noun.locator + "|" + modifier.locator + "|"
        + adjective.locator + "|";

    const uint64_t before_state = rng::current_generator().get_state();
    const uint64_t before_count = rng::current_generator().get_count();
    const string zh = get_gizmo_name(item);
    REQUIRE_FALSE(zh.empty());
    REQUIRE(rng::current_generator().get_state() == before_state);
    REQUIRE(rng::current_generator().get_count() == before_count);

    Options.language = lang_t::EN;
    Options.lang_name = nullptr;
    const string en = get_gizmo_name(item);
    REQUIRE(en == item.props[ARTEFACT_NAME_KEY].get_string());
    REQUIRE(rng::current_generator().get_state() == before_state);
    REQUIRE(rng::current_generator().get_count() == before_count);

    Options.language = lang_t::ZH;
    Options.lang_name = "zh";
    REQUIRE(get_gizmo_name(item) == zh);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: gizmo recipe survives save and old saves fail safely",
                 "[zh-translation][gizmo][tags][compat]")
{
    rng::subgenerator scoped_rng(0x29aa29aa29aa29aaULL,
                                 0x29bb29bb29bb29bbULL);
    const misc_string_recipe noun = selectMiscStringRecipe("gizmo_noun");
    const misc_string_recipe modifier =
        selectMiscStringRecipe("gizmo_modifier");
    REQUIRE_FALSE(noun.locator.empty());
    REQUIRE_FALSE(modifier.locator.empty());

    item_def item;
    item.base_type = OBJ_GIZMOS;
    item.quantity = 1;
    item.rnd = 1;
    item.pos = coord_def(-1, -1);
    item.props[ARTEFACT_NAME_KEY].get_string() =
        modifier.english + noun.english + " Mk.1";
    item.props[GIZMO_NAME_RECIPE_KEY].get_string() =
        "v1|0|" + noun.locator + "|" + modifier.locator + "|-|Mk.1";

    vector<unsigned char> buffer;
    writer output(&buffer);
    marshallItem(output, item, true);
    reader input(buffer);
    input.setMinorVersion(TAG_MINOR_VERSION);
    item_def loaded;
    unmarshallItem(input, loaded);
    REQUIRE(loaded.props[GIZMO_NAME_RECIPE_KEY].get_string()
            == item.props[GIZMO_NAME_RECIPE_KEY].get_string());
    REQUIRE(get_gizmo_name(loaded) == get_gizmo_name(item));

    item_def legacy = item;
    legacy.props.erase(GIZMO_NAME_RECIPE_KEY);
    legacy.props[ARTEFACT_NAME_KEY].get_string() = "legacy locale name";
    REQUIRE(get_gizmo_name(legacy) == "legacy locale name");

    item_def corrupt = item;
    corrupt.props[GIZMO_NAME_RECIPE_KEY].get_string() =
        "v1|0|v1:gizmo_noun:999999|bad|-|Mk.1";
    REQUIRE(get_gizmo_name(corrupt)
            == item.props[ARTEFACT_NAME_KEY].get_string());
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
    REQUIRE(std::string(spell_title(SPELL_IOOD)) == "毁灭法球");
    REQUIRE(std::string(spell_title(SPELL_SIGN_OF_RUIN)) == "毁灭印记");
    REQUIRE(std::string(spell_title(SPELL_SUMMON_UNDEAD)) == "召唤亡灵");
    REQUIRE(ability_name(ABIL_KIKU_SIGN_OF_RUIN) == "毁灭印记");
    // The status display remains a separately qualified lowercase lookup.
    REQUIRE(std::string(C_("status", "sign of ruin")) == "毁灭印记");
    REQUIRE(species::name(SP_POLTERGEIST) == "骚灵");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: contextual item names do not overwrite spell or global terms",
                 "[zh-translation][item-name][context]")
{
    init_properties();

    const auto make_identified_item = [](object_class_type base_type,
                                         int sub_type)
    {
        item_def item;
        item.base_type = base_type;
        item.sub_type = sub_type;
        item.quantity = 1;
        item.flags |= ISFLAG_IDENTIFIED;
        return item;
    };

    item_def infusion_robe = make_identified_item(OBJ_ARMOUR, ARM_ROBE);
    infusion_robe.brand = SPARM_INFUSION;
    REQUIRE(infusion_robe.name(DESC_PLAIN) == "+0 灌注之长袍");

    item_def invisibility_robe = make_identified_item(OBJ_ARMOUR, ARM_ROBE);
    invisibility_robe.brand = SPARM_INVISIBILITY;
    REQUIRE(invisibility_robe.name(DESC_PLAIN) == "+0 隐形之长袍");

    const item_def invisibility_potion =
        make_identified_item(OBJ_POTIONS, POT_INVISIBILITY);
    const item_def might_potion =
        make_identified_item(OBJ_POTIONS, POT_MIGHT);
    const item_def necromancy_book =
        make_identified_item(OBJ_BOOKS, BOOK_NECROMANCY);
    const item_def flight_ring =
        make_identified_item(OBJ_JEWELLERY, RING_FLIGHT);
    REQUIRE(invisibility_potion.name(DESC_PLAIN) == "隐形药水");
    REQUIRE(might_potion.name(DESC_PLAIN) == "强效药水");
    REQUIRE(necromancy_book.name(DESC_PLAIN) == "死灵术之书");
    REQUIRE(flight_ring.name(DESC_PLAIN) == "飞行戒指");

    REQUIRE(std::string(brand_type_name(SPWPN_DRAINING, false)) == "汲取");
    REQUIRE(std::string(brand_type_name(SPWPN_DRAINING, true)) == "汲取");
    REQUIRE(std::string(brand_type_adj(SPWPN_DRAINING)) == "汲取");
    REQUIRE(std::string(T_("drain")) == "吸血");
    REQUIRE(std::string(T_("draining")) == "吸取");

    init_spell_descs();
    init_spell_name_cache();
    REQUIRE(std::string(spell_title(SPELL_INFUSION)) == "灌注术");
    REQUIRE(std::string(spell_title(SPELL_FLY)) == "飞行术");
    REQUIRE(std::string(spell_title(SPELL_INVISIBILITY)) == "隐身术");
    REQUIRE(std::string(spell_title(SPELL_MIGHT)) == "强壮");
}

TEST_CASE_METHOD(EnTranslationFixture,
                 "en: contextual book name keeps the canonical display",
                 "[zh-translation][item-name][context]")
{
    init_properties();
    item_def book;
    book.base_type = OBJ_BOOKS;
    book.sub_type = BOOK_NECROMANCY;
    book.quantity = 1;
    book.flags |= ISFLAG_IDENTIFIED;

    REQUIRE(book.name(DESC_PLAIN) == "book of Necromancy");
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

TEST_CASE("TextDB template masking preserves real English leak detection",
          "[zh-translation][zh-helpers][godspeak]")
{
    const std::set<std::string> canonical_tokens =
        textdb_template_tokens(
            "@The_feature@ [@singular_choice@|@plural_choice@]");
    const std::string legal = mask_textdb_template_tokens(
        "中文 @The_feature@ [@singular_choice@|@plural_choice@]。",
        canonical_tokens);
    CHECK_FALSE(rule_mixed_cn_en(legal));

    const std::string leaked = mask_textdb_template_tokens(
        "中文 @The_feature@ Butterfly。", canonical_tokens);
    CHECK(rule_mixed_cn_en(leaked));

    // Balanced but unknown controls and malformed controls are not hidden.
    CHECK(rule_mixed_cn_en(mask_textdb_template_tokens(
        "中文 @Butterfly prose@。", canonical_tokens)));
    CHECK(rule_mixed_cn_en(mask_textdb_template_tokens(
        "中文 @Butterfly。", canonical_tokens)));
}

TEST_CASE("embedded Lua errors are detected independently of CJK content",
          "[zh-translation][zh-helpers]")
{
    const std::string real_lua_error =
        "中文 {{[string \"db_embedded_lua\"]:2: attempt to index a nil "
        "value (global 'monster')}}";
    CHECK(rule_embedded_lua_error(real_lua_error));
    CHECK(rule_mixed_cn_en(real_lua_error));

    const auto issues = scan_text(real_lua_error, "dynamic status", "status.txt");
    REQUIRE(issues.size() == 1);
    CHECK(issues.front().kind == ZhIssue::EMBEDDED_LUA_ERROR);

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
