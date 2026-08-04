#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "i18n.h"                // T_()
#include "ability.h"
#include "ability-type.h"
#include "acquire.h"
#include "art-enum.h"
#include "artefact.h"
#include "database.h"
#include "decks.h"
#include "describe.h"
#include "describe-god.h"
#include "directn.h"
#include "dungeon.h"
#include "duration-type.h"
#include "env.h"
#include "english.h"
#include "feature.h"
#include "hiscores.h"
#include "item-status-flag-type.h"
#include "item-name.h"
#include "item-prop.h"
#include "item-prop-enum.h"
#include "jobs.h"
#include "losglobal.h"
#include "macro.h"
#include "mapdef.h"
#include "message.h"
#include "mgen-data.h"
#include "mon-place.h"
#include "mon-speak.h"
#include "mon-util.h"
#include "movement-i18n.h"
#include "mutation.h"
#include "nearby-danger.h"
#include "notes.h"
#include "options.h"
#include "player.h"
#include "player-reacts.h"
#include "positional_format.h"
#include "random.h"
#include "religion.h"
#include "skills.h"
#include "shout.h"
#include "species.h"
#include "species-type.h"
#include "spl-util.h"
#include "spell-type.h"
#include "state.h"
#include "stringutil.h"
#include "status.h"
#include "tags.h"
#include "terrain.h"
#include "transform.h"
#include "unicode.h"
#include "test_zh_fixture.h"
#include "test_zh_helpers.h"
#include "unwind.h"
#include "xom.h"

#include <cstring>
#include <array>
#include <string>
#include <tuple>
#ifdef UNIX
#include <fcntl.h>
#include <unistd.h>
#endif

string bind_random_body_part_message(string msg, bool plural);

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
                 "zh: playtest combat and morgue formats are complete",
                 "[zh-translation][combat][morgue][android-playtest]")
{
    CHECK(make_stringf(T_("%s blocks %s attack."), "你", "兽人的")
          == "你格挡了兽人的攻击。");
    CHECK(make_stringf_p(T_("%1$s attacks as %2$s pursue you!"), "它", "s")
          == "在追击你时发动攻击！");

    CHECK(std::string(T_("Vanquished Creatures")) == "已消灭的生物");
    CHECK(make_stringf(T_("%d creature vanquished.\n"), 1)
          == "已消灭1只生物。\n");
    CHECK(make_stringf(T_("%d creatures vanquished.\n"), 2)
          == "已消灭2只生物。\n");
    CHECK(std::string(C_("morgue item inscription", "unknown")) == "未鉴定");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: Android shell help and touch menu are complete",
                 "[zh-translation][android-playtest][touch-menu]")
{
    CHECK(std::string(T_("Menu")) == "菜单");
    CHECK(std::string(T_("Tap <w>Menu</w> in the top bar to open inventory "
                         "and character pages. Use <w>123</w> on the full "
                         "keyboard for symbols."))
          == "点按顶部栏中的<w>菜单</w>可打开背包和角色页面。"
             "完整键盘中的符号位于<w>123</w>层。");
    CHECK(std::string(T_("\n<h>Android Controls\n"
                         "\n"
                         "<w>Back key</w>: Alias for escape\n"
                         "<w>Volume keys</w>: Zoom dungeon & map\n"
                         "Long press for right click.\n"
                         "Touch with two fingers for scrolling.\n"
                         "Toggle keyboard icon controls the\n"
                         "virtual keyboard visibility.\n"))
          == "\n<h>Android 操作\n"
             "\n"
             "<w>返回键</w>：等同于 Esc\n"
             "<w>音量键</w>：缩放地牢与地图\n"
             "长按等同于右键单击。\n"
             "双指触摸可以滚动。\n"
             "键盘图标用于切换\n"
             "虚拟键盘的显示状态。\n");

    CHECK(trim_string_right(getLongDescription("android command menu|Auto-explore"))
          == "自动探索");
    CHECK(trim_string_right(getLongDescription("android command menu|Enter Shop"))
          == "进入商店");
    CHECK(trim_string_right(getLongDescription("android command menu|Go Downstairs"))
          == "下楼");
    CHECK(trim_string_right(getLongDescription("android command menu|Go Upstairs"))
          == "上楼");
    CHECK(trim_string_right(getLongDescription("android command menu|Pick Up"))
          == "拾取");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: localized note snapshots survive save roundtrip",
                 "[zh-translation][notes][persistence]")
{
    const string snapshot = "进入了云中法师的密室";
    const Note original(NOTE_MESSAGE, 0, 0, snapshot);

    vector<unsigned char> bytes;
    writer output(&bytes);
    original.save(output);

    reader input(bytes);
    input.setMinorVersion(TAG_MINOR_VERSION);
    Note loaded;
    loaded.load(input);

    CHECK(loaded.name == snapshot);
    CHECK(loaded.describe(false, false, true) == snapshot);

    Options.language = lang_t::EN;
    i18n_cache_clear();
    CHECK(loaded.describe(false, false, true) == snapshot);
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
                 "zh: graffiti production preserves every root and display RNG",
                 "[zh-translation][graffiti][issue-66][rng]")
{
    array<bool, 15> seen{};
    size_t seen_count = 0;
    for (int attempt = 0; attempt < 4096; ++attempt)
    {
        const uint64_t state_seed = 0x6601000000000000ULL
                                    + static_cast<uint64_t>(attempt);
        const uint64_t sequence_seed = 0x6602000000000000ULL;
        misc_string_recipe recipe;
        {
            rng::subgenerator recipe_rng(state_seed, sequence_seed);
            recipe = selectMiscStringRecipe("any_graffiti");
        }
        REQUIRE_FALSE(recipe.locator.empty());
        REQUIRE_FALSE(recipe.english.empty());
        INFO("locator=" << recipe.locator);

        const string prefix = "v1:any_graffiti:";
        REQUIRE(starts_with(recipe.locator, prefix));
        const size_t comma = recipe.locator.find(',', prefix.size());
        const size_t root_ordinal = static_cast<size_t>(stoul(
            recipe.locator.substr(prefix.size(), comma - prefix.size())));
        REQUIRE(root_ordinal < seen.size());
        if (!seen[root_ordinal])
        {
            seen[root_ordinal] = true;
            ++seen_count;
        }

        string en_display;
        string zh_display;
        uint64_t en_state;
        uint64_t en_count;
        uint64_t zh_state;
        uint64_t zh_count;
        {
            rng::subgenerator display_rng(state_seed, sequence_seed);
            Options.language = lang_t::EN;
            Options.lang_name = nullptr;
            en_display = do_mon_name_replacements(
                maybe_pick_random_substring(getMiscString("any_graffiti")));
            en_state = rng::current_generator().get_state();
            en_count = rng::current_generator().get_count();
        }
        {
            rng::subgenerator display_rng(state_seed, sequence_seed);
            Options.language = lang_t::ZH;
            Options.lang_name = "zh";
            zh_display = do_mon_name_replacements(
                maybe_pick_random_substring(getMiscString("any_graffiti")));
            zh_state = rng::current_generator().get_state();
            zh_count = rng::current_generator().get_count();
        }
        INFO("english=" << en_display);
        INFO("chinese=" << zh_display);
        REQUIRE_FALSE(en_display.empty());
        REQUIRE_FALSE(zh_display.empty());
        REQUIRE(en_state == zh_state);
        REQUIRE(en_count == zh_count);
        REQUIRE(en_display.find('@') == string::npos);
        REQUIRE(zh_display.find('@') == string::npos);
        REQUIRE(en_display.find('[') == string::npos);
        REQUIRE(zh_display.find('[') == string::npos);
    }
    REQUIRE(seen_count == seen.size());
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
                 "zh: announcing after legacy gizmo names preserves indices",
                 "[zh-translation][gizmo][compat]")
{
    unwind_var<player> restore_player(you);
    you = player();
    CrawlVector &names = you.props[COGLIN_GIZMO_NAMES_KEY].get_vector();
    CrawlVector &recipes = you.props[COGLIN_GIZMO_RECIPES_KEY].get_vector();
    names.push_back("legacy locale name");
    REQUIRE(recipes.empty());

    coglin_announce_gizmo_name();

    REQUIRE(names.size() == 2);
    REQUIRE(recipes.size() == names.size());
    REQUIRE(recipes[0].get_string().empty());
    REQUIRE_FALSE(recipes[1].get_string().empty());

    item_def legacy;
    legacy.base_type = OBJ_GIZMOS;
    legacy.quantity = 1;
    legacy.rnd = 1;
    legacy.props[ARTEFACT_NAME_KEY].get_string() = names[0].get_string();
    legacy.props[GIZMO_NAME_RECIPE_KEY].get_string() =
        recipes[0].get_string();
    REQUIRE(get_gizmo_name(legacy) == "legacy locale name");

    item_def announced;
    announced.base_type = OBJ_GIZMOS;
    announced.quantity = 1;
    announced.rnd = 1;
    announced.props[ARTEFACT_NAME_KEY].get_string() = names[1].get_string();
    announced.props[GIZMO_NAME_RECIPE_KEY].get_string() =
        recipes[1].get_string();
    REQUIRE_FALSE(get_gizmo_name(announced).empty());
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
    REQUIRE(might_potion.name(DESC_PLAIN) == "力量药水");
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
                 "zh: mouse-only partial pickup tooltip has no unbound key slot",
                 "[zh-translation][tiles][tooltip]")
{
    string partial_tip =
        T_("\n[Ctrl + L-Click] Partial pick up (%)");
    insert_commands(partial_tip, { CMD_PICKUP_QUANTITY });
    REQUIRE(partial_tip == "\n[Ctrl + 左键] 部分拾取");
    REQUIRE(partial_tip.find("NULL") == string::npos);
    REQUIRE(partial_tip.find('%') == string::npos);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: artefact text uses canonical skill terminology",
                 "[zh-translation][artefact][skill-name]")
{
    REQUIRE(std::string(T_("Evocations")) == "魔力释放");
    REQUIRE(std::string(T_("You are briefly shielded after casting or "
                           "invoking."))
            == "你施法或使用祈神能力后会短暂获得护盾。");
    REQUIRE(std::string(T_("Invo=14 Evo=0"))
            == "祈神=14 魔力释放=0");
    REQUIRE(std::string(T_("Invo=14")) == "祈神=14");
    REQUIRE(std::string(T_("Evo=0")) == "魔力释放=0");
    REQUIRE(std::string(T_("It sets your Invocations skill to 14."))
            == "将你的祈神技能设为14。");
    REQUIRE(std::string(T_("It sets your Evocations skill to 0."))
            == "将你的魔力释放技能设为0。");
    REQUIRE(std::string(T_("It can be activated via the 'a'bility menu to "
                           "radiate toxic energy, with effectiveness "
                           "depending on Evocations skill."))
            == "可以通过能力菜单激活，释放毒素能量，其效果取决于"
               "魔力释放技能。");
    REQUIRE(std::string(T_("It occasionally summons a dragon when using "
                           "Invocations with hostile monsters in sight. "
                           "Chance is 10% + twice the piety cost of the "
                           "ability used."))
            == "视野内有敌对怪物时使用祈神能力，偶尔会召唤一条龙。"
               "触发几率为10% + 所使用能力的虔诚消耗的两倍。");
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

TEST_CASE("MIXED_CN_EN exact command technical literals",
          "[zh-translation][zh-helpers]")
{
    using Row = std::tuple<std::string, bool>;
    auto row = GENERATE(table<std::string, bool>({
        // Exact technical literals required by command descriptions.
        Row{"写入 morgue 目录。",                         false},
        Row{"运行 CMD_EXPLORE 命令。",                   false},
        Row{"将 explore_auto_rest 视为 false。",         false},
        Row{"读取 explore_auto_rest_status 配置。",      false},
        // Legal command templates are syntax, not display-language leaks.
        Row{"按 $cmd[CMD_REPLAY_MESSAGES] 查看消息。",    false},
        Row{"按 $cmd[CMD_0_A] 查看消息。",              false},
        Row{"按 $cmd[CMD_EXPLORE]$cmd[CMD_WAIT] 自动探索。", false},
        Row{"按 $cmd[CMD_LEFT]$cmd[CMD_WAIT]$cmd[CMD_RIGHT] 移动。", false},
        Row{"按 CMD 查看命令。",                        false},
        // File names and Lua member calls are non-display technical syntax.
        Row{"请查阅 options_guide.txt 文件。",           false},
        Row{"第{{ return you.experience_level() }}级。", false},
        Row{"第{{you.experience_level()}}{{you.experience_level()}}级。", false},
        // Minimal mutations must not inherit the exception.
        Row{"写入 morgues 目录。",                        true},
        Row{"运行 CMD_EXPLORES 命令。",                  true},
        Row{"将 explore_auto_resting 视为 false。",      true},
        Row{"读取 explore_auto_rest_statuses 配置。",    true},
        Row{"将 falsey 视为 false。",                    true},
        Row{"将 true 视为 false。",                      true},
        // Compound identifiers are classified whole and case-sensitively.
        Row{"运行 cmd_explore 命令。",                   true},
        Row{"运行 Cmd_Explore 命令。",                   true},
        Row{"运行 X_CMD_EXPLORE 命令。",                 true},
        Row{"运行 CMD_EXPLORE_X 命令。",                 true},
        Row{"运行 _CMD_EXPLORE 命令。",                  true},
        Row{"运行 CMD_EXPLORE_ 命令。",                  true},
        Row{"运行 1CMD_EXPLORE 命令。",                  true},
        Row{"运行 CMD_EXPLORE1 命令。",                  true},
        Row{"按 $cmd[cmd_explore] 自动探索。",           true},
        Row{"按 $cmd[CMD_explore] 自动探索。",           true},
        Row{"按 $cmd[CMD_EXPLORe] 自动探索。",           true},
        Row{"按 $cmd[] 自动探索。",                      true},
        Row{"按 $cmd[CMD_] 自动探索。",                  true},
        Row{"按 $cmd[CMD_REPLAY_MESSAGES 查看消息。",    true},
        Row{"按 $cmd[CMD_EXPLORE-A] 自动探索。",         true},
        Row{"按 $cmd[CMD_EXPLORE]tail 自动探索。",       true},
        Row{"按 $cmd[CMD_EXPLORE]1 自动探索。",          true},
        Row{"按 $cmd[CMD_EXPLORE]_ 自动探索。",          true},
        Row{"按 $cmd[CMD_EXPLORE]$ 自动探索。",          true},
        Row{"按 $cmd[CMD_EXPLORE]$cmd[CMD_WAIT 自动探索。", true},
        Row{"按 $cmd[CMD_EXPLORE]$cmd[cmd_wait] 自动探索。", true},
        Row{"按 cmd[CMD_EXPLORE] 自动探索。",            true},
        Row{"按 $CMD[CMD_EXPLORE] 自动探索。",           true},
        Row{"按 $Cmd[CMD_EXPLORE] 自动探索。",           true},
        Row{"按 $cmd [CMD_EXPLORE] 自动探索。",          true},
        Row{"按 $cmd.[CMD_EXPLORE] 自动探索。",          true},
        Row{"按 $cmd\n[CMD_EXPLORE] 自动探索。",         true},
        Row{"按 $cmd\r[CMD_EXPLORE] 自动探索。",         true},
        Row{"按 $cmd\v[CMD_EXPLORE] 自动探索。",         true},
        Row{"按 $cmd(CMD_EXPLORE) 自动探索。",           true},
        Row{"按 $cmd{CMD_EXPLORE} 自动探索。",           true},
        Row{"按 $cmd",                                 true},
        Row{"按 $$cmd[CMD_EXPLORE] 自动探索。",          true},
        Row{"按 x$cmd[CMD_EXPLORE] 自动探索。",          true},
        Row{"按 1$cmd[CMD_EXPLORE] 自动探索。",          true},
        Row{"按 _$cmd[CMD_EXPLORE] 自动探索。",          true},
        Row{"这是 options_guide 示例。",                 true},
        Row{"这是 you.experience_level 示例。",          true},
        Row{"第{{ return other.experience_level() }}级。", true},
        Row{"第{{ return you.other() }}级。",            true},
        Row{"第{{ return experience_level() }}级。",     true},
        Row{"第{{ return you..experience_level() }}级。", true},
        Row{"第{{ return .you.experience_level() }}级。", true},
        Row{"第{{ return xyou.experience_level() }}级。", true},
        Row{"第{{ return 1you.experience_level() }}级。", true},
        Row{"第{{ return _you.experience_level() }}级。", true},
        Row{"第{{ return you.experience_level().x }}级。", true},
        Row{"第{{ return you.experience_level()x }}级。", true},
        Row{"第{{ return you.experience_level()1 }}级。", true},
        Row{"第{{ return you.experience_level()_ }}级。", true},
        Row{"第{{ return you.experience_level( }}级。",  true},
        Row{"第{{ return you.experience_level }}级。",   true},
        Row{"第{{ return you.experience_level () }}级。", true},
        Row{"第{{ return you.experience_level( ) }}级。", true},
        Row{"第{{ return you.experience_level(value) }}级。", true},
        Row{"第{{ return you.experience_level( }}级{{ ) }}。", true},
        Row{"第{{ return you. }}级{{ experience_level() }}。", true},
        Row{"第{{ return {{ you.experience_level() }} }}级。", true},
        Row{"第{{ return you.experience_level() }级。", true},
        Row{"第{ return you.experience_level() }}级。", true},
        Row{"第}} {{ return you.experience_level() }}级。", true},
        Row{"第{{ return you.experience_level() }} }}级。", true},
        Row{"第{{ return you.experience_level() }} {{级。", true},
        Row{"这是 ordinary_english_leak 示例。",          true},
    }));
    const std::string& text = std::get<0>(row);
    const bool expect_issue = std::get<1>(row);
    INFO("text=\"" << text << "\"");
    REQUIRE(rule_mixed_cn_en(text) == expect_issue);
}

TEST_CASE("MIXED_CN_EN command template chains are linear and fail closed",
          "[zh-translation][zh-helpers]")
{
    constexpr size_t chain_length = 256;
    std::string chain = "按 ";
    for (size_t i = 0; i < chain_length; ++i)
        chain += "$cmd[CMD_WAIT]";

    SECTION("complete long chain")
    {
        REQUIRE_FALSE(rule_mixed_cn_en(chain + " 自动探索。"));
    }
    SECTION("isolated dollar after long chain")
    {
        REQUIRE(rule_mixed_cn_en(chain + "$ 自动探索。"));
    }
    SECTION("malformed template after long chain")
    {
        REQUIRE(rule_mixed_cn_en(chain + "$cmd[CMD_WAIT 自动探索。"));
    }
}

TEST_CASE("MIXED_CN_EN exact hint item templates and technical literals",
          "[zh-translation][zh-helpers]")
{
    using Row = std::tuple<std::string, bool>;
    auto row = GENERATE(table<std::string, bool>({
        // Exact item templates are TextDB protocol, including multiword keys.
        Row{"你捡到了 $item[gold]。",                  false},
        Row{"你捡到了 $item[jewellery]。",            false},
        Row{"你捡到了 $item[potion]。",               false},
        Row{"你捡到了 $item[scroll]。",               false},
        Row{"你捡到了 $item[magical staff]。",        false},
        Row{"你捡到了 $item[wand]。",                 false},
        Row{"你捡到了 $item[gold]$item[magical staff]。", false},
        // Exact Hints literals are display-preserved technical values.
        Row{"请查阅 <w>docs/</w> 目录。",              false},
        Row{"请查阅 <w>docs</w> 目录。",               false},
        Row{"设置 <w>auto_exclude</w> 选项。",         false},
        Row{"按 <w>Shift-right-click</w> 查看。",      false},
        Row{"按 <w>shift-numpad-5</w> 休息。",         false},
        Row{"请访问 http://crawl.develz.org/。",       false},

        // Item protocol mutations fail closed.
        Row{"你捡到了 $item[]。",                      true},
        Row{"你捡到了 $Item[gold]。",                  true},
        Row{"你捡到了 $item[Gold]。",                  true},
        Row{"你捡到了 $item[gold。",                   true},
        Row{"你捡到了 $item[gold]tail。",              true},
        Row{"你捡到了 $items[gold]。",                 true},
        Row{"你捡到了 item[gold]。",                   true},
        Row{"你捡到了 $item [gold]。",                 true},
        Row{"你捡到了 $$item[gold]。",                 true},
        Row{"你捡到了 x$item[gold]。",                 true},
        Row{"你捡到了 $item[ magical staff]。",       true},
        Row{"你捡到了 $item[magical staff ]。",       true},
        Row{"你捡到了 $item[magical  staff]。",       true},
        Row{"你捡到了 $item[magical\tstaff]。",       true},
        Row{"你捡到了 $item[magic_staff]。",           true},
        Row{"你捡到了 $item[magic-staff]。",           true},
        Row{"你捡到了 $item[wand2]。",                 true},
        Row{"你捡到了 $item[gold]$。",                 true},
        Row{"你捡到了 $item[gold]$item[wand。",       true},
        Row{"你捡到了 $item[gold]$Item[wand]。",       true},

        // Literal near-matches must not inherit the narrow exceptions.
        Row{"请查阅 <w>Docs/</w> 目录。",              true},
        Row{"请查阅 <w>Docs</w> 目录。",               true},
        Row{"请查阅 <w>doc</w> 目录。",                true},
        Row{"请查阅 <w>docs2</w> 目录。",              true},
        Row{"请查阅 <w>docs2/</w> 目录。",             true},
        Row{"请查阅 <w>docs_guide</w> 目录。",         true},
        Row{"请查阅 <w>docs/guide</w> 目录。",         true},
        Row{"请查阅 <w>docs//</w> 目录。",             true},
        Row{"设置 <w>Auto_exclude</w> 选项。",         true},
        Row{"设置 <w>auto_excludes</w> 选项。",        true},
        Row{"设置 <w>auto-exclude</w> 选项。",         true},
        Row{"设置 <w>auto_exclude/path</w> 选项。",    true},
        Row{"按 <w>shift-right-click</w> 查看。",      true},
        Row{"按 <w>Shift-right-click2</w> 查看。",     true},
        Row{"按 <w>Shift-numpad-5</w> 休息。",         true},
        Row{"按 <w>shift-numpad-50</w> 休息。",        true},
        Row{"按 <w>shift-numpad-5/path</w> 休息。",    true},
        Row{"请访问 https://crawl.develz.org/。",      true},
        Row{"请访问 http://crawl.develz.org。",        true},
        Row{"请访问 http://crawl.develz.com/。",       true},
        Row{"请访问 http://crawl.develz.org/docs。",   true},
        Row{"请访问 http://crawl.develz.org/?lang=zh。", true},
        Row{"请访问 xhttp://crawl.develz.org/。",      true},
        // The new protocol and literals must not mask normal English leaks.
        Row{"这是 ordinary English leak 示例。",       true},
    }));
    const std::string& text = std::get<0>(row);
    const bool expect_issue = std::get<1>(row);
    INFO("text=\"" << text << "\"");
    REQUIRE(rule_mixed_cn_en(text) == expect_issue);
}

TEST_CASE("MIXED_CN_EN item template chains are linear and fail closed",
          "[zh-translation][zh-helpers]")
{
    constexpr size_t chain_length = 256;
    std::string chain = "你捡到了 ";
    for (size_t i = 0; i < chain_length; ++i)
        chain += "$item[magical staff]";

    SECTION("complete long chain")
    {
        REQUIRE_FALSE(rule_mixed_cn_en(chain + "。"));
    }
    SECTION("isolated dollar after long chain")
    {
        REQUIRE(rule_mixed_cn_en(chain + "$。"));
    }
    SECTION("malformed template after long chain")
    {
        REQUIRE(rule_mixed_cn_en(chain + "$item[wand。"));
    }
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

// =============================================================================
// Issue #61 — item_noise central grammar layer.
//
// item_noise()'s @The_weapon@/@the_weapon@/@Your_weapon@/@your_weapon@/@weapon@
// tokens now run through apply_description() (the central grammar layer):
//   EN: The/the/Your/your keep the byte-identical legacy prefixes.
//   ZH: The/the render the bare localized basename; Your/your render
//       你的 + basename. Unrands first map Your/your to The/the (existing
//       behaviour), so they render the bare localized basename in ZH and
//       "The/the" in EN.
// Each test captures both the raw msg::tee stream (which observes before the
// final capitalize()/filtering, with a leading colour tag) and the final
// message-store buffer, so final-display claims are asserted against the real
// store.
// =============================================================================

namespace
{
// msg::tee observes messages before final capitalization/filtering and with a
// leading <colour> tag; strip that tag for semantic comparison.
string strip_tee_colour_tag(const string &raw)
{
    if (!raw.empty() && raw[0] == '<')
    {
        const string::size_type gt = raw.find('>');
        if (gt != string::npos)
            return raw.substr(gt + 1);
    }
    return raw;
}

// Find a deterministic subgenerator seed for which the real SpeakDB root
// expands to a message containing the intended item_noise token. When
// require_no_random_sites is set, the selected fixture must also have no
// [a|b] random-substring sites, so the final display is fully deterministic.
// Returns 0 when no seed is found within the bound (fail closed).
uint64_t find_speak_seed(const char *key, const char *intended_token,
                         bool require_no_random_sites)
{
    for (uint64_t candidate = 1; candidate < 20000; ++candidate)
    {
        rng::subgenerator probe(candidate, 0x6100610061006100ULL);
        const string text = getSpeakString(key);
        if (text.find(intended_token) != string::npos
            && (!require_no_random_sites || text.find('[') == string::npos))
        {
            return candidate;
        }
    }
    return 0;
}

// RAII guard: restore the unique-item status of one unrand after a test.
struct unique_item_status_guard
{
    int unrand;
    unique_item_status_type saved;

    unique_item_status_guard(int which_unrand)
        : unrand(which_unrand), saved(get_unique_item_status(which_unrand))
    {
    }

    ~unique_item_status_guard()
    {
        item_def item;
        item.flags = ISFLAG_UNRANDART;
        item.unrand_idx = unrand;
        set_unique_item_status(item, saved);
    }
};

struct item_noise_observation
{
    string basename; // item.name(DESC_BASENAME) in the observed language
    string raw;      // message handed to item_noise (pre-token-expansion)
    string tee;      // raw msg::tee stream, colour tag stripped
    string store;    // final message-store buffer text
};

// Observe one item_noise() call with a fully synthetic message (no SpeakDB
// selection, no RNG sites).
item_noise_observation observe_synthetic_noise(lang_t language,
                                               const item_def &item,
                                               const string &msg, int loudness)
{
    Options.language = language;
    Options.lang_name = language == lang_t::ZH ? "zh" : nullptr;
    // Reload the language-specific TextDB layer (item.name(DESC_BASENAME)
    // consults it; getSpeakString needs it for the real-root variant).
    databaseSystemInit();

    item_noise_observation obs;
    obs.basename = item.name(DESC_BASENAME);
    obs.raw = msg;
    {
        msg::tee tee(obs.tee);
        item_noise(item, you, msg, loudness);
        obs.store = get_last_messages(1, true);
    }
    obs.tee = strip_tee_colour_tag(obs.tee);
    return obs;
}

// Observe the real production sequence for one root: getSpeakString() under
// the fixed subgenerator, then item_noise() under the same generator, so the
// weighted picks and any [a|b] sites share one deterministic RNG stream.
item_noise_observation observe_real_root(lang_t language, const item_def &item,
                                         const char *key,
                                         const char *intended_token,
                                         int loudness, uint64_t seed)
{
    Options.language = language;
    Options.lang_name = language == lang_t::ZH ? "zh" : nullptr;
    // Reload the language-specific TextDB layer so getSpeakString selects
    // the fixture in the observed language.
    databaseSystemInit();

    item_noise_observation obs;
    obs.basename = item.name(DESC_BASENAME);
    {
        rng::subgenerator scoped_rng(seed, 0x6100610061006100ULL);
        obs.raw = getSpeakString(key);
        REQUIRE_FALSE(obs.raw.empty());
        // The selected real fixture must actually contain the intended token
        // (guards against a fixture whose expansion drops the weapon token).
        REQUIRE(obs.raw.find(intended_token) != string::npos);
        msg::tee tee(obs.tee);
        item_noise(item, you, obs.raw, loudness);
        obs.store = get_last_messages(1, true);
    }
    obs.tee = strip_tee_colour_tag(obs.tee);
    return obs;
}
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 61 item_noise token matrix keeps EN articles and drops ZH articles",
                 "[zh-translation][item-noise][issue-61]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.set_position(coord_def(20, 20));

    item_def item;
    item.base_type = OBJ_WEAPONS;
    item.sub_type = WPN_DAGGER;
    item.quantity = 1;
    item.plus = 0;
    item.flags = ISFLAG_IDENTIFIED;

    // Four-token matrix: capital tokens at sentence start, lowercase tokens
    // mid-sentence (so sentence-capitalization cannot mask the token layer),
    // plus the bare @weapon@ token.
    const string msg = "VISUAL:@the_weapon@ A @The_weapon@ B "
                       "@your_weapon@ C @Your_weapon@ D @weapon@.";

    const item_noise_observation en =
        observe_synthetic_noise(lang_t::EN, item, msg, 0);
    const item_noise_observation zh =
        observe_synthetic_noise(lang_t::ZH, item, msg, 0);

    // DESC_BASENAME keeps the actual (plus-bearing) basename; pin it so the
    // exact expectations below cannot silently shift.
    REQUIRE(en.basename == "+0 dagger");
    REQUIRE(zh.basename == "+0 匕首");
    REQUIRE(en.basename != zh.basename);

    // EN: byte-identical legacy semantics (The/the/Your/your + basename).
    const string en_expected =
        "the " + en.basename + " A The " + en.basename + " B "
        + "your " + en.basename + " C Your " + en.basename + " D "
        + en.basename + ".";
    // The final message store additionally applies capitalize().
    const string en_store_expected =
        "The " + en.basename + " A The " + en.basename + " B "
        + "your " + en.basename + " C Your " + en.basename + " D "
        + en.basename + ".";
    CHECK(en.tee == en_expected + "\n");
    CHECK(en.store == en_store_expected + "\n\n");
    CHECK(en.store.find("@") == string::npos);
    CHECK(en.store.find("Your " + en.basename) != string::npos);

    // ZH: The/the -> bare localized basename, Your/your -> 你的 + basename.
    const string zh_expected =
        zh.basename + " A " + zh.basename + " B "
        + "你的" + zh.basename + " C 你的" + zh.basename + " D "
        + zh.basename + ".";
    CHECK(zh.tee == zh_expected + "\n");
    CHECK(zh.store == zh_expected + "\n\n");
    CHECK(zh.store.find("@") == string::npos);
    CHECK(zh.store.find("The ") == string::npos);
    CHECK(zh.store.find("the ") == string::npos);
    CHECK(zh.store.find("Your ") == string::npos);
    CHECK(zh.store.find("your ") == string::npos);
    CHECK(zh.store.find("你的" + zh.basename) != string::npos);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 61 noisy randart renders the real noisy weapon root",
                 "[zh-translation][item-noise][issue-61]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.set_position(coord_def(20, 20));

    item_def item;
    item.base_type = OBJ_WEAPONS;
    item.sub_type = WPN_DAGGER;
    item.quantity = 1;
    item.plus = 3;
    // Fixed display name; production randart property initialization gives the
    // item a valid ARTEFACT_PROPS_KEY vector (item.name() asserts on it).
    item.props[ARTEFACT_NAME_KEY].get_string() = "noise test blade";
    REQUIRE(make_item_randart(item, true));
    item.flags |= ISFLAG_IDENTIFIED;

    const uint64_t seed =
        find_speak_seed("noisy weapon", "@Your_weapon@", true);
    REQUIRE(seed != 0);

    // Non-visual root (TALK channel): item_noise still routes through noisy(),
    // which asserts an in-bounds origin even at loudness 0; the player
    // position was set above and is restored by unwind_var.
    const item_noise_observation en = observe_real_root(
        lang_t::EN, item, "noisy weapon", "@Your_weapon@", 0, seed);
    const item_noise_observation zh = observe_real_root(
        lang_t::ZH, item, "noisy weapon", "@Your_weapon@", 0, seed);

    // The seed search ran under the ZH fixture; prove the same seed selects a
    // fixture with the intended token and no random sites in both languages.
    REQUIRE(en.raw.find('[') == string::npos);
    REQUIRE(zh.raw.find('[') == string::npos);

    // EN: Your -> "Your " + actual basename (unchanged semantics).
    const string en_expected =
        replace_all(en.raw, "@Your_weapon@", "Your " + en.basename);
    CHECK(en.tee == en_expected + "\n");
    CHECK(en.store == en_expected + "\n\n");
    CHECK(en.store.find("@") == string::npos);

    // ZH: Your -> 你的 + localized basename; no English articles leak.
    const string zh_expected =
        replace_all(zh.raw, "@Your_weapon@", "你的" + zh.basename);
    CHECK(zh.tee == zh_expected + "\n");
    CHECK(zh.store == zh_expected + "\n\n");
    CHECK(zh.store.find("@") == string::npos);
    CHECK(zh.store.find("Your ") == string::npos);
    CHECK(zh.store.find("The ") == string::npos);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 61 singing sword silenced renders The through the grammar layer",
                 "[zh-translation][item-noise][issue-61]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.set_position(coord_def(20, 20));

    item_def item;
    item.base_type = OBJ_WEAPONS;
    item.sub_type = WPN_DOUBLE_SWORD;
    item.quantity = 1;
    item.plus = 11;
    item.flags = ISFLAG_UNRANDART | ISFLAG_IDENTIFIED;
    item.unrand_idx = UNRAND_SINGING_SWORD;

    const uint64_t seed =
        find_speak_seed("singing sword silenced", "@The_weapon@", true);
    REQUIRE(seed != 0);

    // All silenced-tier fixtures are VISUAL: roots (no noisy() call), but the
    // position is still set uniformly.
    const item_noise_observation en = observe_real_root(
        lang_t::EN, item, "singing sword silenced", "@The_weapon@", 0, seed);
    const item_noise_observation zh = observe_real_root(
        lang_t::ZH, item, "singing sword silenced", "@The_weapon@", 0, seed);

    REQUIRE(en.raw.find('[') == string::npos);
    REQUIRE(zh.raw.find('[') == string::npos);
    // The silenced tier is a VISUAL: root; item_noise strips the control
    // prefix before display, so expectations use the post-prefix body.
    REQUIRE(en.raw.find("VISUAL:") == 0);
    REQUIRE(zh.raw.find("VISUAL:") == 0);
    const string en_body = en.raw.substr(strlen("VISUAL:"));
    const string zh_body = zh.raw.substr(strlen("VISUAL:"));

    // EN: sentence-initial @The_weapon@ -> "The " + basename.
    const string en_expected =
        replace_all(en_body, "@The_weapon@", "The " + en.basename);
    CHECK(en.tee == en_expected + "\n");
    CHECK(en.store == en_expected + "\n\n");
    CHECK(en.store.find("@") == string::npos);

    // ZH: The -> bare localized basename (Singing Sword is an unrand, so the
    // actual basename is the localized artefact name, not a base item).
    const string zh_expected =
        replace_all(zh_body, "@The_weapon@", zh.basename);
    CHECK(zh.tee == zh_expected + "\n");
    CHECK(zh.store == zh_expected + "\n\n");
    CHECK(zh.store.find("@") == string::npos);
    CHECK(zh.store.find("The ") == string::npos);
    CHECK(zh.store.find("your ") == string::npos);
    CHECK(zh.basename != en.basename);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 61 noisy unrand maps Your to The before the grammar layer",
                 "[zh-translation][item-noise][issue-61]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.set_position(coord_def(20, 20));
    unique_item_status_guard restore_status(UNRAND_CONDEMNATION);

    item_def item;
    item.base_type = OBJ_WEAPONS;
    item.sub_type = WPN_TRISHULA;
    item.quantity = 1;
    item.plus = 8;
    item.flags = ISFLAG_UNRANDART | ISFLAG_IDENTIFIED;
    item.unrand_idx = UNRAND_CONDEMNATION;

    // The trishula fixture always contains [a|b] sites, so the seed search
    // only requires the intended token here.
    const uint64_t seed =
        find_speak_seed("trishula \"Condemnation\"", "@Your_weapon@", false);
    REQUIRE(seed != 0);

    // Non-visual root (TALK channel); position was set above.
    const item_noise_observation en = observe_real_root(
        lang_t::EN, item, "trishula \"Condemnation\"", "@Your_weapon@", 0,
        seed);
    const item_noise_observation zh = observe_real_root(
        lang_t::ZH, item, "trishula \"Condemnation\"", "@Your_weapon@", 0,
        seed);

    // Real trishula fixture: @Your_weapon@ was mapped to @The_weapon@ before
    // the grammar layer, so EN renders "The " + basename and never "Your ".
    CHECK(en.store.find("The " + en.basename) != string::npos);
    CHECK(en.store.find("Your " + en.basename) == string::npos);
    CHECK(en.store.find("@") == string::npos);
    // ZH: Your -> The -> bare localized basename (no 你的, no articles).
    CHECK(zh.store.find(zh.basename) != string::npos);
    CHECK(zh.store.find("你的" + zh.basename) == string::npos);
    CHECK(zh.store.find("Your ") == string::npos);
    CHECK(zh.store.find("The ") == string::npos);
    CHECK(zh.store.find("@") == string::npos);
    CHECK(zh.basename != en.basename);

    // Lowercase unrand variant: @your_weapon@ -> @the_weapon@ -> "the " +
    // basename in EN, bare basename in ZH (exact and deterministic).
    const item_noise_observation en_lower = observe_synthetic_noise(
        lang_t::EN, item, "VISUAL:@your_weapon@ tail.", 0);
    const item_noise_observation zh_lower = observe_synthetic_noise(
        lang_t::ZH, item, "VISUAL:@your_weapon@ tail.", 0);
    CHECK(en_lower.tee == "the " + en_lower.basename + " tail.\n");
    CHECK(en_lower.store == "The " + en_lower.basename + " tail.\n\n");
    CHECK(zh_lower.tee == zh_lower.basename + " tail.\n");
    CHECK(zh_lower.store == zh_lower.basename + " tail.\n\n");
    CHECK(en_lower.store.find("@") == string::npos);
    CHECK(zh_lower.store.find("@") == string::npos);
}

// =============================================================================
// Issue #62 — eel-hand flavour message boundary.
//
// do_eel_flavour_msg() (player-reacts.cc) drives the real SpeakDB roots
// "eel hand actions" / "eel hand solo actions":
//   - @head@ is replaced with the contextual C_("body part", ...) value
//     (EN "head"/"form", ZH 头/形体), copied into an owned string;
//   - @skin@ keeps the localized species::skin_name() path;
//   - exactly one maybe_pick_random_substring() expansion runs after the
//     runtime token replacements and immediately before the MSGCH_TALK sink.
// Each test finds a deterministic seed with a bounded probe that replays the
// production RNG sequence (SpeakDB weighted pick + single random-substring
// expansion) under a two-argument rng::subgenerator(seed, fixed_sequence),
// then replays the real production function under the same generator. The
// final message store and a file-local msg::tee subclass (the base tee
// discards the channel and get_last_messages has no channel access) are
// asserted for the exact text, the exact chosen alternative, the positive
// localized head/form/skin values, exactly one emission, MSGCH_TALK, no
// residual tokens/brackets, and unchanged parent RNG. Before every replay
// the production guard precondition is proven empty (no nearby dangerous
// visible monster, fail closed). Every observed emission runs inside the
// existing msgwin_temporary_mode with an RAII rollback
// (msgwin_clear_temporary()) on the normal and REQUIRE-unwinding paths, so
// the process-global message store is never contaminated: after the
// rollback the complete retained history snapshot
// (get_last_messages(NUM_STORED_MESSAGES, true)) is proven byte-identical
// to the pre-call snapshot. Player state is restored by unwind_var; the
// fixture restores language state. The tests mutate no env cells, so no
// world snapshot/restore is needed.
// =============================================================================

namespace
{
// Fixed sequence discriminator for every probe and replay; the two-argument
// subgenerator constructor fully determines the stream without touching the
// parent RNG.
constexpr uint64_t EEL_RNG_SEQUENCE = 0x6100610061006100ULL;

// File-local msg::tee subclass capturing the append channel and count; no
// production observer is added.
struct channel_capturing_tee : msg::tee
{
    msg_channel_type channel = MSGCH_PLAIN;
    int appends = 0;

    channel_capturing_tee(string &target) : msg::tee(target) {}

    void append(const string &s, msg_channel_type ch) override
    {
        ++appends;
        channel = ch;
        msg::tee::append(s, ch);
    }
};

// RAII cleanup installed after msgwin_temporary_mode: rolls back the
// temporary messages with msgwin_clear_temporary() on the normal path and
// on REQUIRE unwinding, so an observed emission never survives into the
// process-global message store.
struct temporary_message_rollback
{
    ~temporary_message_rollback()
    {
        msgwin_clear_temporary();
    }
};

// Switch the display language and reload the language-specific TextDB layer
// (getSpeakString and the C_/species lookups both consult it).
void set_eel_language(lang_t language)
{
    Options.language = language;
    Options.lang_name = language == lang_t::ZH ? "zh" : nullptr;
    databaseSystemInit();
}

// Probe the exact RNG-consuming sequence of do_eel_flavour_msg() under a
// fixed two-argument subgenerator, without touching the message sink: the
// SpeakDB weighted pick, the runtime token replacements, then the single
// random-substring expansion. Used only to find deterministic seeds and to
// compute the exact expected final text for the real-function replay.
struct eel_probe_result
{
    string raw;   // SpeakDB root text before token replacement
    string final; // after @head@/@skin@ replacement and one random pick
};

eel_probe_result probe_eel_flavour(const char *key, uint64_t seed)
{
    eel_probe_result out;
    rng::subgenerator probe(seed, EEL_RNG_SEQUENCE);
    string msg = getSpeakString(key);
    out.raw = msg;
    msg = replace_all(msg, "@head@",
                      you.has_mutation(MUT_FORMLESS) ? C_("body part", "form")
                                                     : C_("body part", "head"));
    msg = replace_all(msg, "@skin@", species::skin_name(you.species));
    out.final = maybe_pick_random_substring(msg);
    return out;
}

// Bounded deterministic seed search over the real SpeakDB root; the probe's
// raw root text must contain `needle`. Returns 0 when no seed is found within
// the bound (fail closed).
uint64_t find_eel_raw_seed(const char *key, const string &needle)
{
    for (uint64_t candidate = 1; candidate < 20000; ++candidate)
        if (probe_eel_flavour(key, candidate).raw.find(needle) != string::npos)
            return candidate;
    return 0;
}

// Bounded deterministic seed search over the real SpeakDB root; the probe's
// expanded final text must contain `needle` (e.g. one random alternative).
uint64_t find_eel_final_seed(const char *key, const string &needle)
{
    for (uint64_t candidate = 1; candidate < 20000; ++candidate)
        if (probe_eel_flavour(key, candidate).final.find(needle) != string::npos)
            return candidate;
    return 0;
}

// One replay of the real do_eel_flavour_msg() under a fixed two-argument
// subgenerator, with player/world state set by the caller.
struct eel_observation
{
    string store;             // get_last_messages(1, true) while active
    string tee_raw;           // raw msg::tee stream (colour tag + text + newline)
    msg_channel_type channel = MSGCH_PLAIN;
    int appends = 0;
    bool history_restored = false; // complete retained history == pre-call
    bool parent_rng_unchanged = false;
};

eel_observation observe_eel_flavour(lang_t language, uint64_t seed)
{
    set_eel_language(language);

    // Fail closed: the production guard of do_eel_flavour_msg() must see no
    // nearby dangerous visible monster, otherwise it silently returns and no
    // emission happens (an empty observation would prove nothing).
    REQUIRE_FALSE(there_are_monsters_nearby(true, true, false));

    eel_observation obs;
    const string history_before = get_last_messages(NUM_STORED_MESSAGES, true);
    const uint64_t parent_before = rng::peek_uint64();
    {
        // Every observed emission runs inside the existing temporary mode;
        // the rollback guard clears it on the normal path and on REQUIRE
        // unwinding, so the emission never survives this scope.
        msgwin_temporary_mode temporary;
        temporary_message_rollback rollback;
        rng::subgenerator scoped_rng(seed, EEL_RNG_SEQUENCE);
        channel_capturing_tee tee(obs.tee_raw);
        do_eel_flavour_msg();
        // Capture the exact emission while it is still active in the store,
        // the tee and the channel, before the rollback at scope exit.
        obs.store = get_last_messages(1, true);
        obs.channel = tee.channel;
        obs.appends = tee.appends;
    }
    // Rollback already ran at scope exit; prove the complete retained
    // message history equals the pre-call snapshot (isolation from later
    // cases and helper calls).
    obs.history_restored =
        get_last_messages(NUM_STORED_MESSAGES, true) == history_before;
    obs.parent_rng_unchanged = rng::peek_uint64() == parent_before;
    return obs;
}

// Shared final-display assertions for one observation of the real production
// function under a fixed subgenerator.
void check_eel_observation(const eel_observation &obs,
                           const string &expected_final)
{
    // Exact final message-store text (proves exactly one emitted message
    // with exactly the expected content).
    CHECK(obs.store == expected_final + "\n\n");
    // msg::tee observes before final capitalization/filtering: colour tag
    // stripped, text plus the single appended newline.
    CHECK(strip_tee_colour_tag(obs.tee_raw) == expected_final + "\n");
    // No residual tokens or brackets in the final display.
    CHECK(obs.store.find("@") == string::npos);
    CHECK(obs.store.find("[") == string::npos);
    CHECK(obs.store.find("]") == string::npos);
    // Channel and single-emission proof via the file-local tee.
    CHECK(obs.channel == MSGCH_TALK);
    CHECK(obs.appends == 1);
    // The replay drew only from the fixed subgenerator, never the parent RNG.
    CHECK(obs.parent_rng_unchanged);
    // Full isolation: after the temporary-mode rollback, the complete
    // retained message history is byte-identical to the pre-call snapshot,
    // so no later case or helper call can see this emission.
    CHECK(obs.history_restored);
}

// ZH final displays must not leak any English head/form/skin text.
void check_zh_no_english_leak(const string &store)
{
    CHECK(store.find("head") == string::npos);
    CHECK(store.find("form") == string::npos);
    CHECK(store.find("skin") == string::npos);
}
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 62 eel normal head renders the localized body-part value",
                 "[zh-translation][eel-flavour][issue-62]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.set_position(coord_def(20, 20));
    you.species = SP_HUMAN;
    you.form = transformation::eel_hands;

    // Bounded deterministic seed search over the real SpeakDB root; the
    // selected fixture must contain the @head@ token.
    set_eel_language(lang_t::EN);
    const uint64_t seed = find_eel_raw_seed("eel hand actions", "@head@");
    REQUIRE(seed != 0);

    set_eel_language(lang_t::EN);
    const eel_probe_result en_expected =
        probe_eel_flavour("eel hand actions", seed);
    REQUIRE(en_expected.raw.find("@head@") != string::npos);
    set_eel_language(lang_t::ZH);
    const eel_probe_result zh_expected =
        probe_eel_flavour("eel hand actions", seed);
    REQUIRE(zh_expected.raw.find("@head@") != string::npos);

    // Positive owned C_ head values in each language (EN fallback exact, ZH
    // the translator-approved value).
    set_eel_language(lang_t::EN);
    const string en_head = C_("body part", "head");
    set_eel_language(lang_t::ZH);
    const string zh_head = C_("body part", "head");
    CHECK(en_head == "head");
    CHECK(zh_head == "头");

    const eel_observation en = observe_eel_flavour(lang_t::EN, seed);
    check_eel_observation(en, en_expected.final);
    CHECK(en.store.find(en_head) != string::npos);

    const eel_observation zh = observe_eel_flavour(lang_t::ZH, seed);
    check_eel_observation(zh, zh_expected.final);
    CHECK(zh.store.find(zh_head) != string::npos);
    check_zh_no_english_leak(zh.store);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 62 eel FORMLESS head renders the localized form value",
                 "[zh-translation][eel-flavour][issue-62]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.set_position(coord_def(20, 20));
    you.species = SP_HUMAN;
    you.form = transformation::eel_hands;
    // FORMLESS may be unreachable together with eel_hands today, but the
    // directly preserved helper branch must still display the localized
    // body-part form value.
    you.mutation[MUT_FORMLESS] = 1;

    set_eel_language(lang_t::EN);
    const uint64_t seed = find_eel_raw_seed("eel hand actions", "@head@");
    REQUIRE(seed != 0);

    set_eel_language(lang_t::EN);
    const eel_probe_result en_expected =
        probe_eel_flavour("eel hand actions", seed);
    REQUIRE(en_expected.raw.find("@head@") != string::npos);
    set_eel_language(lang_t::ZH);
    const eel_probe_result zh_expected =
        probe_eel_flavour("eel hand actions", seed);
    REQUIRE(zh_expected.raw.find("@head@") != string::npos);

    set_eel_language(lang_t::EN);
    const string en_form = C_("body part", "form");
    set_eel_language(lang_t::ZH);
    const string zh_form = C_("body part", "form");
    CHECK(en_form == "form");
    CHECK(zh_form == "形体");

    const eel_observation en = observe_eel_flavour(lang_t::EN, seed);
    check_eel_observation(en, en_expected.final);
    CHECK(en.store.find(en_form) != string::npos);

    const eel_observation zh = observe_eel_flavour(lang_t::ZH, seed);
    check_eel_observation(zh, zh_expected.final);
    CHECK(zh.store.find(zh_form) != string::npos);
    check_zh_no_english_leak(zh.store);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 62 eel @skin@ variant keeps the localized skin name",
                 "[zh-translation][eel-flavour][issue-62]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.set_position(coord_def(20, 20));
    you.species = SP_HUMAN;
    you.form = transformation::eel_hands;

    set_eel_language(lang_t::EN);
    const uint64_t seed = find_eel_raw_seed("eel hand actions", "@skin@");
    REQUIRE(seed != 0);

    set_eel_language(lang_t::EN);
    const eel_probe_result en_expected =
        probe_eel_flavour("eel hand actions", seed);
    REQUIRE(en_expected.raw.find("@skin@") != string::npos);
    set_eel_language(lang_t::ZH);
    const eel_probe_result zh_expected =
        probe_eel_flavour("eel hand actions", seed);
    REQUIRE(zh_expected.raw.find("@skin@") != string::npos);

    set_eel_language(lang_t::EN);
    const string en_skin = species::skin_name(you.species);
    set_eel_language(lang_t::ZH);
    const string zh_skin = species::skin_name(you.species);
    CHECK(en_skin == "skin");
    CHECK(zh_skin == "皮肤");

    const eel_observation en = observe_eel_flavour(lang_t::EN, seed);
    check_eel_observation(en, en_expected.final);
    CHECK(en.store.find(en_skin) != string::npos);

    const eel_observation zh = observe_eel_flavour(lang_t::ZH, seed);
    check_eel_observation(zh, zh_expected.final);
    CHECK(zh.store.find(zh_skin) != string::npos);
    check_zh_no_english_leak(zh.store);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 62 eel solo expands exactly one random alternative",
                 "[zh-translation][eel-flavour][issue-62]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.set_position(coord_def(20, 20));
    you.species = SP_HUMAN;
    you.form = transformation::eel_hands;
    // One arm selects the "eel hand solo actions" root (arm_count()==1).
    you.mutation[MUT_MISSING_HAND] = 1;

    // Bounded deterministic search: one seed per alternative of the
    // ordinal-0 random site, driven by the real SpeakDB root.
    set_eel_language(lang_t::EN);
    const uint64_t seed_a =
        find_eel_final_seed("eel hand solo actions", "frantically");
    const uint64_t seed_b =
        find_eel_final_seed("eel hand solo actions", "wistfully");
    REQUIRE(seed_a != 0);
    REQUIRE(seed_b != 0);
    REQUIRE(seed_a != seed_b);

    // Same weights in the ZH layer: the same seeds must select the same
    // ordinal-0 variant and the Chinese alternatives.
    set_eel_language(lang_t::ZH);
    const eel_probe_result zh_probe_a =
        probe_eel_flavour("eel hand solo actions", seed_a);
    const eel_probe_result zh_probe_b =
        probe_eel_flavour("eel hand solo actions", seed_b);
    REQUIRE(zh_probe_a.raw.find("[") != string::npos);
    REQUIRE(zh_probe_b.raw.find("[") != string::npos);
    REQUIRE(zh_probe_a.final.find("疯狂地") != string::npos);
    REQUIRE(zh_probe_b.final.find("惆怅地") != string::npos);

    // Alternative A: frantically / 疯狂地.
    set_eel_language(lang_t::EN);
    const eel_probe_result en_expected_a =
        probe_eel_flavour("eel hand solo actions", seed_a);
    const eel_observation en_a = observe_eel_flavour(lang_t::EN, seed_a);
    check_eel_observation(en_a, en_expected_a.final);
    CHECK(en_a.store.find("frantically") != string::npos);
    CHECK(en_a.store.find("wistfully") == string::npos);

    const eel_observation zh_a = observe_eel_flavour(lang_t::ZH, seed_a);
    check_eel_observation(zh_a, zh_probe_a.final);
    CHECK(zh_a.store.find("疯狂地") != string::npos);
    CHECK(zh_a.store.find("惆怅地") == string::npos);
    check_zh_no_english_leak(zh_a.store);

    // Alternative B: wistfully / 惆怅地.
    set_eel_language(lang_t::EN);
    const eel_probe_result en_expected_b =
        probe_eel_flavour("eel hand solo actions", seed_b);
    const eel_observation en_b = observe_eel_flavour(lang_t::EN, seed_b);
    check_eel_observation(en_b, en_expected_b.final);
    CHECK(en_b.store.find("wistfully") != string::npos);
    CHECK(en_b.store.find("frantically") == string::npos);

    const eel_observation zh_b = observe_eel_flavour(lang_t::ZH, seed_b);
    check_eel_observation(zh_b, zh_probe_b.final);
    CHECK(zh_b.store.find("惆怅地") != string::npos);
    CHECK(zh_b.store.find("疯狂地") == string::npos);
    check_zh_no_english_leak(zh_b.store);
}

// =============================================================================
// Issue #63 — Xom pseudo-miscast worn-item ownership/body-part boundary.
//
// _xom_pseudo_miscast() (xom.cc) builds nine worn-item SpeakDB candidates
// ("offhand slot", "cloak slot", "helmet slot", "gloves slot", "boots slot",
// "amulet slot", "gizmo slot", "ring slot", plus the five body-armour roots
// "dragon armour"/"animal skin"/"leather armour"/"robe"/"metal armour") by
// routing the already selected candidate and the already materialized item
// basename/qualname through the single deterministic seam
// xom_bind_worn_item_message(). The seam applies the central DESC_YOUR
// grammar layer (apply_description), replaces @your_item@/@Your_item@ and,
// for the three head roots (cloak/helmet/amulet), copies the C_("body part",
// ...) value into an owned string and replaces @head@. EN output stays
// byte-equivalent to the legacy "your "/"Your " + item name and "head"/"form";
// ZH renders 你的<localized item> and 头/形体 with no English owner or body
// part leaking into the final display.
//
// The seam consumes no RNG (SpeakDB selection and final display stay at the
// call sites), so every replay runs under an identical two-argument
// rng::subgenerator with a control replay (SpeakDB selection only) capturing
// the exact consumed state/count, and the parent RNG is proven untouched.
// The seam emits no message, so the process-global message store is never
// touched. All 13 affected roots have no [a|b] random-substring sites in
// either language, so the final display is fully deterministic once the
// candidate is selected; the tests fail closed (seed == 0) when the expected
// token or topology is unavailable. Player state is restored by unwind_var
// and the fixture restores language/TextDB state. Seeds are searched per
// language and never assume the same ordinal in both languages.
// =============================================================================

namespace
{
constexpr uint64_t XOM_RNG_SEQUENCE = 0x6100610061006100ULL;

void set_xom_language(lang_t language)
{
    Options.language = language;
    Options.lang_name = language == lang_t::ZH ? "zh" : nullptr;
    databaseSystemInit();
}

struct xom_root_spec
{
    const char *key;      // SpeakDB root after "Xom "
    const char *token;    // item token the selected fixture must contain
    bool supports_head;   // cloak/helmet/amulet roots carry @head@
};

// All nine worn-item producer sites / 13 real roots. Lowercase and uppercase
// item tokens both occur in the real variants (dragon armour/animal
// skin/robe use @your_item@; the rest use @Your_item@).
const xom_root_spec xom_worn_item_roots[] = {
    { "offhand slot",   "@Your_item@", false },
    { "cloak slot",     "@Your_item@", true  },
    { "helmet slot",    "@Your_item@", true  },
    { "gloves slot",    "@Your_item@", false },
    { "boots slot",     "@Your_item@", false },
    { "amulet slot",    "@Your_item@", true  },
    { "gizmo slot",     "@Your_item@", false },
    { "ring slot",      "@Your_item@", false },
    { "dragon armour",  "@your_item@", false },
    { "animal skin",    "@your_item@", false },
    { "leather armour", "@Your_item@", false },
    { "robe",           "@your_item@", false },
    { "metal armour",   "@Your_item@", false },
};

const size_t NUM_XOM_WORN_ITEM_ROOTS = ARRAYSZ(xom_worn_item_roots);

item_def make_xom_armour(armour_type sub)
{
    item_def item;
    item.base_type = OBJ_ARMOUR;
    item.sub_type = sub;
    item.quantity = 1;
    item.plus = 0;
    item.flags = ISFLAG_IDENTIFIED;
    return item;
}

item_def make_xom_ring()
{
    item_def item;
    item.base_type = OBJ_JEWELLERY;
    item.sub_type = RING_PROTECTION;
    item.quantity = 1;
    item.plus = 3;
    item.flags = ISFLAG_IDENTIFIED;
    return item;
}

item_def make_xom_amulet()
{
    item_def item;
    item.base_type = OBJ_JEWELLERY;
    item.sub_type = AMU_ACROBAT;
    item.quantity = 1;
    item.flags = ISFLAG_IDENTIFIED;
    return item;
}

item_def make_xom_gizmo()
{
    // Established recipe-name fixture (same construction as the gizmo tests
    // above): a fixed two-argument subgenerator isolates the recipe picks.
    rng::subgenerator recipe_rng(0x63c063c063c063c0ULL, XOM_RNG_SEQUENCE);
    const misc_string_recipe noun = selectMiscStringRecipe("gizmo_noun");
    const misc_string_recipe modifier =
        selectMiscStringRecipe("gizmo_modifier");
    REQUIRE_FALSE(noun.locator.empty());
    REQUIRE_FALSE(modifier.locator.empty());

    item_def item;
    item.base_type = OBJ_GIZMOS;
    item.quantity = 1;
    item.rnd = 1;
    item.props[ARTEFACT_NAME_KEY].get_string() =
        modifier.english + noun.english + " Mk.1";
    item.props[GIZMO_NAME_RECIPE_KEY].get_string() =
        "v1|0|" + noun.locator + "|" + modifier.locator + "|-|Mk.1";
    return item;
}

// One actual identified item fixture per producer site, mirroring the slot
// the production block reads (the ring keeps DESC_QUALNAME below).
item_def xom_fixture_for_root(const xom_root_spec &root)
{
    if (string(root.key) == "offhand slot")
        return make_xom_armour(ARM_BUCKLER);
    if (string(root.key) == "cloak slot")
        return make_xom_armour(ARM_CLOAK);
    if (string(root.key) == "helmet slot")
        return make_xom_armour(ARM_HELMET);
    if (string(root.key) == "gloves slot")
        return make_xom_armour(ARM_GLOVES);
    if (string(root.key) == "boots slot")
        return make_xom_armour(ARM_BOOTS);
    if (string(root.key) == "amulet slot")
        return make_xom_amulet();
    if (string(root.key) == "gizmo slot")
        return make_xom_gizmo();
    if (string(root.key) == "ring slot")
        return make_xom_ring();
    if (string(root.key) == "dragon armour")
        return make_xom_armour(ARM_FIRE_DRAGON_ARMOUR);
    if (string(root.key) == "animal skin")
        return make_xom_armour(ARM_ANIMAL_SKIN);
    if (string(root.key) == "leather armour")
        return make_xom_armour(ARM_LEATHER_ARMOUR);
    if (string(root.key) == "robe")
        return make_xom_armour(ARM_ROBE);
    if (string(root.key) == "metal armour")
        return make_xom_armour(ARM_PLATE_ARMOUR);
    FAIL("unknown issue-63 root");
    return item_def();
}

// Head roots must select a fixture carrying both the item token and @head@.
vector<string> xom_required_tokens(const xom_root_spec &root)
{
    vector<string> tokens = { root.token };
    if (root.supports_head)
        tokens.push_back("@head@");
    return tokens;
}

// Bounded deterministic seed search over the real SpeakDB root in the
// current language; the selected fixture must contain every required token
// and no [a|b] random-substring site (all 13 affected roots have none).
// Returns 0 when no seed is found within the bound (fail closed).
uint64_t find_xom_root_seed(const char *key, const vector<string> &tokens)
{
    for (uint64_t candidate = 1; candidate < 20000; ++candidate)
    {
        rng::subgenerator probe(candidate, XOM_RNG_SEQUENCE);
        const string text = getSpeakString("Xom " + string(key));
        bool all_found = true;
        for (const string &token : tokens)
            if (text.find(token) == string::npos)
                all_found = false;
        if (all_found && text.find('[') == string::npos)
            return candidate;
    }
    return 0;
}

// One binder replay under a fixed two-argument subgenerator: SpeakDB
// selection, then xom_bind_worn_item_message() with exactly the arguments
// the production site passes. A control replay with an identical subgenerator
// performs the SpeakDB selection only and captures the exact RNG state/count
// it consumes; equality proves the seam consumes zero RNG.
struct xom_binder_observation
{
    string item_name;  // name(DESC_BASENAME/QUALNAME) in the observed language
    string raw;        // SpeakDB candidate before binding
    string control_raw;// control replay candidate (must equal raw)
    string bound;      // xom_bind_worn_item_message() output
    bool rng_isolated; // binder replay consumed exactly the control RNG
    bool parent_rng_unchanged;
};

xom_binder_observation observe_xom_binder(lang_t language, const char *key,
                                          const item_def &item,
                                          bool supports_head,
                                          bool desc_qualname,
                                          bool formless,
                                          uint64_t seed)
{
    set_xom_language(language);
    you.mutation[MUT_FORMLESS] = formless ? 1 : 0;

    xom_binder_observation obs;
    obs.item_name = item.name(desc_qualname ? DESC_QUALNAME : DESC_BASENAME,
                              false, false, false);
    REQUIRE_FALSE(obs.item_name.empty());

    uint64_t control_state = 0;
    uint64_t control_count = 0;
    {
        rng::subgenerator control(seed, XOM_RNG_SEQUENCE);
        obs.control_raw = getSpeakString("Xom " + string(key));
        control_state = rng::current_generator().get_state();
        control_count = rng::current_generator().get_count();
    }

    const uint64_t parent_before = rng::peek_uint64();
    {
        rng::subgenerator probe(seed, XOM_RNG_SEQUENCE);
        obs.raw = getSpeakString("Xom " + string(key));
        obs.bound = xom_bind_worn_item_message(obs.raw, obs.item_name,
                                               supports_head);
        REQUIRE_FALSE(obs.bound.empty());
        obs.rng_isolated =
            rng::current_generator().get_state() == control_state
            && rng::current_generator().get_count() == control_count;
    }
    obs.parent_rng_unchanged = rng::peek_uint64() == parent_before;
    return obs;
}
} // namespace

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 63 EN binder byte-equals legacy replacements across all 13 roots",
                 "[zh-translation][xom][issue-63]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.set_position(coord_def(20, 20));

    for (const xom_root_spec &root : xom_worn_item_roots)
    {
        INFO("EN root: " << root.key);
        set_xom_language(lang_t::EN);
        const item_def item = xom_fixture_for_root(root);
        const uint64_t seed =
            find_xom_root_seed(root.key, xom_required_tokens(root));
        REQUIRE(seed != 0);

        const xom_binder_observation obs = observe_xom_binder(
            lang_t::EN, root.key, item, root.supports_head, false, false,
            seed);
        REQUIRE(obs.raw == obs.control_raw);

        // Legacy replacements: "your " + item name, "Your " +
        // uppercase_first, English "head" for the three head roots (normal
        // state). The binder must be byte-identical to them.
        string legacy = replace_all(obs.raw, "@your_item@",
                                    "your " + obs.item_name);
        legacy = replace_all(legacy, "@Your_item@",
                             "Your " + obs.item_name);
        if (root.supports_head)
            legacy = replace_all(legacy, "@head@", "head");
        CHECK(obs.bound == legacy);
        CHECK(obs.bound.find("@") == string::npos);
        CHECK(obs.bound.find("[") == string::npos);
        CHECK(obs.bound.find("]") == string::npos);
        CHECK(obs.rng_isolated);
        CHECK(obs.parent_rng_unchanged);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 63 ZH binder localizes all 13 worn-item roots",
                 "[zh-translation][xom][issue-63]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.set_position(coord_def(20, 20));

    for (const xom_root_spec &root : xom_worn_item_roots)
    {
        INFO("ZH root: " << root.key);
        set_xom_language(lang_t::ZH);
        const item_def item = xom_fixture_for_root(root);
        const uint64_t seed =
            find_xom_root_seed(root.key, xom_required_tokens(root));
        REQUIRE(seed != 0);

        const xom_binder_observation obs = observe_xom_binder(
            lang_t::ZH, root.key, item, root.supports_head, false, false,
            seed);
        REQUIRE(obs.raw == obs.control_raw);

        // apply_description(DESC_YOUR) must produce the documented 你的
        // prefix in ZH and the binder must use exactly it.
        const string zh_owned = "你的" + obs.item_name;
        CHECK(apply_description(DESC_YOUR, obs.item_name) == zh_owned);

        string expected = replace_all(obs.raw, "@your_item@", zh_owned);
        expected = replace_all(expected, "@Your_item@", zh_owned);
        if (root.supports_head)
            expected = replace_all(expected, "@head@", "头");
        CHECK(obs.bound == expected);
        CHECK(obs.bound.find("@") == string::npos);
        CHECK(obs.bound.find("[") == string::npos);
        CHECK(obs.bound.find("]") == string::npos);
        CHECK(obs.bound.find("your ") == string::npos);
        CHECK(obs.bound.find("Your ") == string::npos);
        CHECK(obs.bound.find("head") == string::npos);
        CHECK(obs.bound.find("form") == string::npos);
        CHECK(obs.rng_isolated);
        CHECK(obs.parent_rng_unchanged);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 63 head roots render localized head/form in normal and FORMLESS states",
                 "[zh-translation][xom][issue-63]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.set_position(coord_def(20, 20));

    for (const xom_root_spec &root : xom_worn_item_roots)
    {
        if (!root.supports_head)
            continue;
        for (const lang_t language : { lang_t::EN, lang_t::ZH })
        {
            INFO("head root: " << root.key << ", language: "
                 << (language == lang_t::ZH ? "zh" : "en"));
            set_xom_language(language);
            const item_def item = xom_fixture_for_root(root);
            const uint64_t seed =
                find_xom_root_seed(root.key, xom_required_tokens(root));
            REQUIRE(seed != 0);

            for (const bool formless : { false, true })
            {
                INFO("formless: " << (formless ? "yes" : "no"));
                const xom_binder_observation obs = observe_xom_binder(
                    language, root.key, item, true, false, formless, seed);
                REQUIRE(obs.raw == obs.control_raw);

                if (language == lang_t::EN)
                {
                    const string en_head = C_("body part", "head");
                    const string en_form = C_("body part", "form");
                    CHECK(en_head == "head");
                    CHECK(en_form == "form");

                    string expected = replace_all(
                        obs.raw, "@your_item@", "your " + obs.item_name);
                    expected = replace_all(expected, "@Your_item@",
                                           "Your " + obs.item_name);
                    expected = replace_all(expected, "@head@",
                                           formless ? "form" : "head");
                    CHECK(obs.bound == expected);
                    CHECK(obs.bound.find("@") == string::npos);
                }
                else
                {
                    const string zh_head = C_("body part", "head");
                    const string zh_form = C_("body part", "form");
                    CHECK(zh_head == "头");
                    CHECK(zh_form == "形体");

                    const string zh_owned = "你的" + obs.item_name;
                    string expected = replace_all(obs.raw, "@your_item@",
                                                  zh_owned);
                    expected = replace_all(expected, "@Your_item@",
                                           zh_owned);
                    expected = replace_all(expected, "@head@",
                                           formless ? zh_form : zh_head);
                    CHECK(obs.bound == expected);
                    CHECK(obs.bound.find("@") == string::npos);
                    CHECK(obs.bound.find("your ") == string::npos);
                    CHECK(obs.bound.find("Your ") == string::npos);
                    CHECK(obs.bound.find("head") == string::npos);
                    CHECK(obs.bound.find("form") == string::npos);
                }
                CHECK(obs.rng_isolated);
                CHECK(obs.parent_rng_unchanged);
            }
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 63 ring root supplies DESC_QUALNAME not the basename",
                 "[zh-translation][xom][issue-63]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.set_position(coord_def(20, 20));

    const item_def ring = make_xom_ring();

    for (const lang_t language : { lang_t::EN, lang_t::ZH })
    {
        INFO("ring language: " << (language == lang_t::ZH ? "zh" : "en"));
        set_xom_language(language);
        const string basename = ring.name(DESC_BASENAME, false, false, false);
        const string qualname = ring.name(DESC_QUALNAME, false, false, false);
        REQUIRE_FALSE(qualname.empty());
        REQUIRE(qualname != basename);

        const uint64_t seed = find_xom_root_seed("ring slot",
                                                 { "@Your_item@" });
        REQUIRE(seed != 0);

        const xom_binder_observation obs = observe_xom_binder(
            language, "ring slot", ring, false, true, false, seed);
        REQUIRE(obs.raw == obs.control_raw);
        // The binder must have received the DESC_QUALNAME string.
        REQUIRE(obs.item_name == qualname);

        if (language == lang_t::EN)
        {
            const string expected = replace_all(
                replace_all(obs.raw, "@your_item@", "your " + qualname),
                "@Your_item@", "Your " + qualname);
            CHECK(obs.bound == expected);
            // The qualname-based owner text is present; the bare-basename
            // owner text cannot appear (EN "Your ring" never occurs).
            CHECK(obs.bound.find("Your " + qualname) != string::npos);
            CHECK(obs.bound.find("Your " + basename) == string::npos);
        }
        else
        {
            const string zh_owned = "你的" + qualname;
            const string expected = replace_all(
                replace_all(obs.raw, "@your_item@", zh_owned),
                "@Your_item@", zh_owned);
            CHECK(obs.bound == expected);
            CHECK(obs.bound.find(zh_owned) != string::npos);
            CHECK(obs.bound.find("your ") == string::npos);
            CHECK(obs.bound.find("Your ") == string::npos);
            CHECK(obs.bound.find("@") == string::npos);
        }
        CHECK(obs.rng_isolated);
        CHECK(obs.parent_rng_unchanged);
    }
}

// =============================================================================
// Issue #64 — Xom pseudo-miscast fallback and random body-part display.
// =============================================================================

namespace
{
constexpr uint64_t XOM_BODY_RNG_SEQUENCE = 0x6400640064006400ULL;

bool contains_ascii_alpha(const string &text)
{
    return text.find_first_of(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz") != string::npos;
}

void reset_xom_body_player(species_type species, transformation form
                                                = transformation::none)
{
    you = player();
    you.set_position(coord_def(20, 20));
    you.species = species;
    you.form = form;
}

struct body_rng_observation
{
    vector<string> parts;
    uint64_t state;
    uint64_t count;
};

body_rng_observation observe_body_rng(lang_t language, species_type species,
                                      int part_class, uint64_t seed)
{
    set_xom_language(language);
    reset_xom_body_player(species);

    body_rng_observation obs;
    rng::subgenerator scoped_rng(seed, XOM_BODY_RNG_SEQUENCE);
    // Exercise the same plural/singular alternation repeatedly so rejection
    // sampling, rather than a single lucky draw, determines the final state.
    for (int repeat = 0; repeat < 4; ++repeat)
    {
        obs.parts.push_back(random_body_part_name(true, part_class));
        obs.parts.push_back(random_body_part_name(false, part_class));
    }
    obs.state = rng::current_generator().get_state();
    obs.count = rng::current_generator().get_count();
    return obs;
}

uint64_t find_body_part_seed(species_type species, transformation form,
                             bool plural, int part_class,
                             const string &expected)
{
    set_xom_language(lang_t::EN);
    reset_xom_body_player(species, form);
    for (uint64_t seed = 1; seed < 20000; ++seed)
    {
        rng::subgenerator probe(seed, XOM_BODY_RNG_SEQUENCE);
        if (random_body_part_name(plural, part_class) == expected)
            return seed;
    }
    return 0;
}

struct binding_observation
{
    string result;
    uint64_t state;
    uint64_t count;
};

template <typename Binder>
binding_observation observe_binding(lang_t language, species_type species,
                                    uint64_t seed, Binder binder)
{
    set_xom_language(language);
    reset_xom_body_player(species);
    binding_observation obs;
    rng::subgenerator scoped_rng(seed, XOM_BODY_RNG_SEQUENCE);
    obs.result = binder();
    obs.state = rng::current_generator().get_state();
    obs.count = rng::current_generator().get_count();
    return obs;
}

const char * const all_body_tokens =
    "@random_body_part_any_singular@/"
    "@random_body_part_internal_singular@/"
    "@random_body_part_external_singular@/"
    "@random_body_part_any_plural@/"
    "@random_body_part_internal_plural@/"
    "@random_body_part_external_plural@";

string legacy_bind_body_parts(string msg, bool plural)
{
    const char *suffix = plural ? "plural" : "singular";
    msg = replace_all(msg,
        "@random_body_part_any_" + string(suffix) + "@",
        random_body_part_name(plural, BPART_ANY));
    msg = replace_all(msg,
        "@random_body_part_internal_" + string(suffix) + "@",
        random_body_part_name(plural, BPART_INTERNAL));
    msg = replace_all(msg,
        "@random_body_part_external_" + string(suffix) + "@",
        random_body_part_name(plural, BPART_EXTERNAL));
    return msg;
}

monster make_xom_body_monster()
{
    monster mons;
    // Exact fake-monster shape constructed by god_speaks(), the production
    // entry used by Xom's send-in-the-clones speech path.
    mons.type = MONS_PROGRAM_BUG;
    mons.mid = MID_NOBODY;
    mons.hit_points = 1;
    mons.god = GOD_XOM;
    mons.foe = MHITYOU;
    mons.mname = "FAKE GOD MONSTER";
    mons.set_position(you.pos());
    return mons;
}
} // namespace

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 64 fallback foot and arm preserve EN and localize ZH",
                 "[zh-translation][xom][issue-64]")
{
    init_properties();
    unwind_var<player> restore_player(you);

    set_xom_language(lang_t::EN);
    reset_xom_body_player(SP_HUMAN);
    CHECK(string(T_("Nothing appears to happen... Ominous!"))
          == "Nothing appears to happen... Ominous!");
    CHECK(you.foot_name(false) == "foot");
    CHECK(you.foot_name(true) == "feet");
    you.mutation[MUT_HOOVES] = 3;
    CHECK(you.foot_name(false) == "hoof");
    CHECK(you.foot_name(true) == "hooves");
    reset_xom_body_player(SP_NAGA);
    CHECK(you.foot_name(false) == "underbelly");
    CHECK(you.arm_name(false) == "scaled arm");
    CHECK(you.arm_name(true) == "scaled arms");
    you.species = SP_HUMAN;
    you.form = transformation::death;
    CHECK(you.arm_name(false) == "fossilised arm");
    CHECK(you.arm_name(true) == "fossilised arms");

    set_xom_language(lang_t::ZH);
    reset_xom_body_player(SP_HUMAN);
    CHECK(string(T_("Nothing appears to happen... Ominous!"))
          == "似乎什么都没有发生……不祥之兆！");
    CHECK(you.foot_name(false) == "脚");
    CHECK(you.foot_name(true) == "脚");
    you.mutation[MUT_HOOVES] = 3;
    CHECK(you.foot_name(false) == "蹄");
    CHECK(you.foot_name(true) == "蹄");
    reset_xom_body_player(SP_NAGA);
    CHECK(you.foot_name(false) == "腹部");
    CHECK(you.arm_name(false) == "鳞片覆盖的手臂");
    CHECK(you.arm_name(true) == "鳞片覆盖的手臂");
    you.species = SP_HUMAN;
    you.form = transformation::death;
    CHECK(you.arm_name(false) == "化石般的手臂");
    CHECK(you.arm_name(true) == "化石般的手臂");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 64 body RNG topology is language invariant for all classes and plural skins",
                 "[zh-translation][xom][issue-64]")
{
    init_properties();
    unwind_var<player> restore_player(you);

    const species_type skin_species[] = {
        SP_NAGA, SP_TENGU, SP_MUMMY, SP_REVENANT
    };
    const int part_classes[] = {
        BPART_INTERNAL, BPART_EXTERNAL, BPART_ANY
    };

    for (const species_type species : skin_species)
    {
        for (const int part_class : part_classes)
        {
            INFO("species=" << static_cast<int>(species)
                 << ", class=" << part_class);
            const body_rng_observation en = observe_body_rng(
                lang_t::EN, species, part_class, 0x64b0d1ULL);
            const body_rng_observation zh = observe_body_rng(
                lang_t::ZH, species, part_class, 0x64b0d1ULL);
            REQUIRE(en.parts.size() == zh.parts.size());
            CHECK(en.state == zh.state);
            CHECK(en.count == zh.count);
            for (const string &part : zh.parts)
            {
                CHECK_FALSE(part.empty());
                CHECK_FALSE(contains_ascii_alpha(part));
                CHECK(part.find('@') == string::npos);
            }
        }
    }

    const struct
    {
        species_type species;
        const char *english;
        const char *chinese;
    } skin_cases[] = {
        { SP_NAGA, "scales", "鳞片" },
        { SP_TENGU, "feathers", "羽毛" },
        { SP_MUMMY, "bandages", "绷带" },
        { SP_REVENANT, "bones", "骨骼" },
    };

    for (const auto &skin : skin_cases)
    {
        INFO("skin species=" << static_cast<int>(skin.species));
        const uint64_t seed = find_body_part_seed(
            skin.species, transformation::none, true, BPART_EXTERNAL,
            skin.english);
        REQUIRE(seed != 0);
        const body_rng_observation en = observe_body_rng(
            lang_t::EN, skin.species, BPART_EXTERNAL, seed);
        const body_rng_observation zh = observe_body_rng(
            lang_t::ZH, skin.species, BPART_EXTERNAL, seed);
        // The first draw is the specifically selected plural skin candidate;
        // all subsequent rejection draws must still leave identical topology.
        CHECK(en.parts.front() == skin.english);
        CHECK(zh.parts.front() == skin.chinese);
        CHECK(en.state == zh.state);
        CHECK(en.count == zh.count);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 64 fixed form and skin candidates localize at the body-part sink",
                 "[zh-translation][xom][issue-64]")
{
    init_properties();
    unwind_var<player> restore_player(you);

    const struct
    {
        species_type species;
        transformation form;
        bool plural;
        int part_class;
        const char *english;
        const char *chinese;
    } cases[] = {
        { SP_HUMAN, transformation::none, false, BPART_INTERNAL,
          "soul", "灵魂" },
        { SP_HUMAN, transformation::jelly, false, BPART_EXTERNAL,
          "jelly", "胶质" },
        { SP_NAGA, transformation::none, true, BPART_EXTERNAL,
          "scales", "鳞片" },
    };

    for (const auto &test : cases)
    {
        INFO("candidate=" << test.english);
        const uint64_t seed = find_body_part_seed(
            test.species, test.form, test.plural, test.part_class,
            test.english);
        REQUIRE(seed != 0);

        set_xom_language(lang_t::EN);
        reset_xom_body_player(test.species, test.form);
        string en;
        uint64_t en_state;
        uint64_t en_count;
        {
            rng::subgenerator scoped_rng(seed, XOM_BODY_RNG_SEQUENCE);
            en = random_body_part_name(test.plural, test.part_class);
            en_state = rng::current_generator().get_state();
            en_count = rng::current_generator().get_count();
        }

        set_xom_language(lang_t::ZH);
        reset_xom_body_player(test.species, test.form);
        string zh;
        uint64_t zh_state;
        uint64_t zh_count;
        {
            rng::subgenerator scoped_rng(seed, XOM_BODY_RNG_SEQUENCE);
            zh = random_body_part_name(test.plural, test.part_class);
            zh_state = rng::current_generator().get_state();
            zh_count = rng::current_generator().get_count();
        }

        CHECK(en == test.english);
        CHECK(zh == test.chinese);
        CHECK(en_state == zh_state);
        CHECK(en_count == zh_count);
        CHECK_FALSE(contains_ascii_alpha(zh));
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 64 pseudo brain and monster replacement paths preserve binding order",
                 "[zh-translation][xom][issue-64]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    const uint64_t seed = 0x64b1adULL;

    for (const lang_t language : { lang_t::EN, lang_t::ZH })
    {
        INFO("language=" << (language == lang_t::ZH ? "zh" : "en"));

        const binding_observation pseudo = observe_binding(
            language, SP_NAGA, seed, [] {
                string result = xom_bind_pseudo_body_parts(
                    all_body_tokens, false);
                return xom_bind_pseudo_body_parts(result, true);
            });
        const binding_observation pseudo_control = observe_binding(
            language, SP_NAGA, seed, [] {
                string result = legacy_bind_body_parts(all_body_tokens, false);
                return legacy_bind_body_parts(result, true);
            });
        CHECK(pseudo.result == pseudo_control.result);
        CHECK(pseudo.state == pseudo_control.state);
        CHECK(pseudo.count == pseudo_control.count);
        CHECK(pseudo.result.find("@random_body_part") == string::npos);

        const string branch = language == lang_t::ZH ? " [左|右]"
                                                     : " [left|right]";
        const string brain_input = string(all_body_tokens) + branch;
        const binding_observation brain = observe_binding(
            language, SP_NAGA, seed, [&brain_input] {
                return xom_bind_brain_drain_body_parts(brain_input);
            });
        const binding_observation brain_control = observe_binding(
            language, SP_NAGA, seed, [&brain_input] {
                string result = legacy_bind_body_parts(brain_input, false);
                result = legacy_bind_body_parts(result, true);
                return maybe_pick_random_substring(result);
            });
        CHECK(brain.result == brain_control.result);
        CHECK(brain.state == brain_control.state);
        CHECK(brain.count == brain_control.count);
        CHECK(brain.result.find("@random_body_part") == string::npos);
        CHECK(brain.result.find('[') == string::npos);

        const monster mons = make_xom_body_monster();
        const binding_observation mon = observe_binding(
            language, SP_NAGA, seed, [&brain_input, &mons] {
                return do_mon_str_replacements(brain_input, mons, S_SILENT);
            });
        const binding_observation mon_control = observe_binding(
            language, SP_NAGA, seed, [&brain_input] {
                string result = maybe_pick_random_substring(brain_input);
                result = legacy_bind_body_parts(result, false);
                return legacy_bind_body_parts(result, true);
            });
        CHECK(mon.result == mon_control.result);
        CHECK(mon.state == mon_control.state);
        CHECK(mon.count == mon_control.count);
        CHECK(mon.result.find("@random_body_part") == string::npos);
        CHECK(mon.result.find('[') == string::npos);

        const binding_observation no_token = observe_binding(
            language, SP_NAGA, seed, [&mons] {
                return do_mon_str_replacements("plain body text", mons,
                                               S_SILENT);
            });
        CHECK(no_token.result == "plain body text");
        CHECK(no_token.count == 0);

        if (language == lang_t::ZH)
        {
            CHECK_FALSE(contains_ascii_alpha(pseudo.result));
            CHECK_FALSE(contains_ascii_alpha(brain.result));
            CHECK_FALSE(contains_ascii_alpha(mon.result));
            CHECK(brain.result.find('@') == string::npos);
            CHECK(mon.result.find('@') == string::npos);
        }
    }
}

// =============================================================================
// Issue #65 — Xom dragon-armour classification must use canonical identity.
// =============================================================================

namespace
{
struct xom_dragon_armour_case
{
    armour_type type;
    const char *english;
    const char *chinese;
};

const xom_dragon_armour_case xom_dragon_armours[] = {
    { ARM_FIRE_DRAGON_ARMOUR,        "+0 fire dragon scales",       "+0 火龙鳞甲" },
    { ARM_ICE_DRAGON_ARMOUR,         "+0 ice dragon scales",        "+0 冰龙鳞甲" },
    { ARM_STEAM_DRAGON_ARMOUR,       "+0 steam dragon scales",      "+0 蒸汽龙鳞甲" },
    { ARM_ACID_DRAGON_ARMOUR,        "+0 acid dragon scales",       "+0 酸龙鳞甲" },
    { ARM_STORM_DRAGON_ARMOUR,       "+0 storm dragon scales",      "+0 风暴龙鳞甲" },
    { ARM_GOLDEN_DRAGON_ARMOUR,      "+0 golden dragon scales",     "+0 金龙鳞甲" },
    { ARM_SWAMP_DRAGON_ARMOUR,       "+0 swamp dragon scales",      "+0 沼泽龙鳞甲" },
    { ARM_PEARL_DRAGON_ARMOUR,       "+0 pearl dragon scales",      "+0 珍珠龙鳞甲" },
    { ARM_SHADOW_DRAGON_ARMOUR,      "+0 shadow dragon scales",     "+0 暗影龙鳞甲" },
    { ARM_QUICKSILVER_DRAGON_ARMOUR, "quicksilver dragon scales", "水银龙鳞甲" },
};

struct xom_armour_candidate_observation
{
    string key;
    string item_name;
    string raw;
    string bound;
    size_t candidate_count;
    uint64_t state;
    uint64_t count;
    bool classifier_rng_unchanged;
    bool parent_rng_unchanged;
};

xom_armour_candidate_observation observe_xom_armour_candidate(
    lang_t language, const item_def &item, uint64_t seed)
{
    set_xom_language(language);

    xom_armour_candidate_observation obs;
    obs.item_name = item.name(DESC_BASENAME, false, false, false);
    obs.candidate_count = 0;

    const uint64_t parent_before = rng::peek_uint64();
    {
        rng::subgenerator scoped_rng(seed, XOM_RNG_SEQUENCE);
        const uint64_t classifier_state = rng::current_generator().get_state();
        const uint64_t classifier_count = rng::current_generator().get_count();

        obs.key = xom_body_armour_speech_key(item);
        obs.classifier_rng_unchanged =
            rng::current_generator().get_state() == classifier_state
            && rng::current_generator().get_count() == classifier_count;

        if (!obs.key.empty())
        {
            ++obs.candidate_count;
            obs.raw = getSpeakString("Xom " + obs.key);
            REQUIRE_FALSE(obs.raw.empty());
            obs.bound = xom_bind_worn_item_message(obs.raw, obs.item_name,
                                                   false);
        }
        obs.state = rng::current_generator().get_state();
        obs.count = rng::current_generator().get_count();
    }
    obs.parent_rng_unchanged = rng::peek_uint64() == parent_before;
    return obs;
}
} // namespace

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 65 body armour keys cover current compat and non-dragon subtypes",
                 "[zh-translation][xom][issue-65]")
{
    init_monsters();
    init_properties();

    for (const xom_dragon_armour_case &test : xom_dragon_armours)
    {
        INFO("current dragon armour subtype=" << static_cast<int>(test.type));
        const item_def item = make_xom_armour(test.type);
        CHECK_FALSE(item_type_removed(OBJ_ARMOUR, test.type));
        REQUIRE(armour_type_is_hide(test.type));
        CHECK(mons_genus(monster_for_hide(test.type)) == MONS_DRAGON);
        CHECK(xom_body_armour_speech_key(item) == "dragon armour");
    }

#if TAG_MAJOR_VERSION == 34
    const armour_type removed_dragon_hides[] = {
        ARM_FIRE_DRAGON_HIDE,
        ARM_ICE_DRAGON_HIDE,
        ARM_STEAM_DRAGON_HIDE,
        ARM_ACID_DRAGON_HIDE,
        ARM_STORM_DRAGON_HIDE,
        ARM_GOLDEN_DRAGON_HIDE,
        ARM_SWAMP_DRAGON_HIDE,
        ARM_PEARL_DRAGON_HIDE,
        ARM_SHADOW_DRAGON_HIDE,
        ARM_QUICKSILVER_DRAGON_HIDE,
    };
    for (const armour_type type : removed_dragon_hides)
    {
        INFO("removed dragon hide subtype=" << static_cast<int>(type));
        const item_def item = make_xom_armour(type);
        CHECK(item_type_removed(OBJ_ARMOUR, type));
        CHECK_FALSE(armour_type_is_hide(type));
        CHECK(xom_body_armour_speech_key(item).empty());
    }
#endif

    const struct
    {
        armour_type type;
        const char *key;
    } non_dragon_cases[] = {
        { ARM_ANIMAL_SKIN,          "animal skin" },
        { ARM_LEATHER_ARMOUR,       "leather armour" },
        { ARM_ROBE,                 "robe" },
        { ARM_RING_MAIL,            "metal armour" },
        { ARM_SCALE_MAIL,           "metal armour" },
        { ARM_CHAIN_MAIL,           "metal armour" },
        { ARM_PLATE_ARMOUR,         "metal armour" },
        { ARM_TROLL_LEATHER_ARMOUR, "" },
        { ARM_CRYSTAL_PLATE_ARMOUR, "" },
    };
    for (const auto &test : non_dragon_cases)
    {
        INFO("non-dragon armour subtype=" << static_cast<int>(test.type));
        const item_def item = make_xom_armour(test.type);
        CHECK(xom_body_armour_speech_key(item) == test.key);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 65 dragon candidates keep EN ZH names and RNG topology aligned",
                 "[zh-translation][xom][issue-65]")
{
    init_monsters();
    init_properties();
    constexpr uint64_t seed = 0x6500650065006500ULL;

    for (const xom_dragon_armour_case &test : xom_dragon_armours)
    {
        INFO("dragon armour subtype=" << static_cast<int>(test.type));
        const item_def item = make_xom_armour(test.type);
        const xom_armour_candidate_observation en =
            observe_xom_armour_candidate(lang_t::EN, item, seed);
        const xom_armour_candidate_observation zh =
            observe_xom_armour_candidate(lang_t::ZH, item, seed);

        CHECK(en.key == "dragon armour");
        CHECK(zh.key == en.key);
        CHECK(en.candidate_count == 1);
        CHECK(zh.candidate_count == en.candidate_count);
        CHECK(en.item_name == test.english);
        CHECK(zh.item_name == test.chinese);
        CHECK(en.raw == "The scales on @your_item@ wiggle briefly.");
        CHECK(zh.raw == "@your_item@ 上的鳞片短暂地扭动了一下。");
        CHECK(en.bound == "The scales on your " + string(test.english)
                          + " wiggle briefly.");
        CHECK(zh.bound == "你的" + string(test.chinese)
                          + " 上的鳞片短暂地扭动了一下。");
        CHECK(en.bound.find('@') == string::npos);
        CHECK(zh.bound.find('@') == string::npos);
        CHECK(en.classifier_rng_unchanged);
        CHECK(zh.classifier_rng_unchanged);
        CHECK(en.state == zh.state);
        CHECK(en.count == zh.count);
        CHECK(en.count > 0);
        CHECK(en.parent_rng_unchanged);
        CHECK(zh.parent_rng_unchanged);
    }
}

// =============================================================================
// Issue #67 — decorlines species prefix lookup identity (I67-CODE-006).
//
// directn.cc::_walk_on_decor queries food-cache keys with a form wiz_name
// prefix, then a species raw-name prefix, then the bare key. The species
// prefix must stay the English raw name in ZH mode too: the canonical
// TextDB keys (EN and ZH decorlines.txt) are English, so a localized
// prefix (e.g. "小精灵 fruit cache") can never match and all 29 species
// cache keys would silently fall back to the generic line.
// =============================================================================

namespace
{
bool contains_non_ascii(const string &text)
{
    for (unsigned char c : text)
        if (c >= 0x80)
            return true;
    return false;
}
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: decorlines cache lookup resolves through the production chain",
                 "[zh-translation][decorlines][issue-67]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.set_position(coord_def(20, 20));

    struct decor_cache_case
    {
        species_type species;
        transformation form;
        const char *english_raw_name;
        const char *lookup;
        decor_cache_hit expected_hit;
    };
    const array<decor_cache_case, 3> cases = {{
        // form-hit: the serpent form wiz_name "amphisbaena" prefixes the
        // canonical key before any species prefix is tried.
        { SP_SPRIGGAN, transformation::serpent, "Spriggan", "fruit cache",
          decor_cache_hit::form },
        // species-hit: the "none" form misses, then the raw English
        // species name hits the canonical key.
        { SP_SPRIGGAN, transformation::none, "Spriggan", "fruit cache",
          decor_cache_hit::species },
        // generic-fallback: Armataur has no cache key, so the bare
        // generic key resolves the line.
        { SP_ARMATAUR, transformation::none, "Armataur", "fruit cache",
          decor_cache_hit::generic },
    }};

    for (const decor_cache_case &test : cases)
    {
        INFO("species=" << test.english_raw_name
             << " form=" << static_cast<int>(test.form)
             << " lookup=" << test.lookup);
        you.species = test.species;
        you.form = test.form;

        // The raw plain name is the English lookup identity even under ZH.
        REQUIRE(species::name(you.species, species::SPNAME_PLAIN, true)
                == test.english_raw_name);

        // Real production chain: decor_cache_lookup() is the exact helper
        // directn.cc::_walk_on_decor calls, and the hit proves which
        // branch resolved the key. If the species prefix were reverted
        // to raw=false, the localized key would miss and the chain would
        // silently fall back to the generic line - the hit assertion
        // below then fails even though a Chinese line is returned.
        string line;
        decor_cache_hit hit = decor_cache_hit::none;
        {
            rng::subgenerator scoped_rng(
                0x6701000000000000ULL + static_cast<uint64_t>(test.species),
                0x6702000000000000ULL);
            const decor_cache_result result =
                decor_cache_lookup(test.lookup);
            line = result.line;
            hit = result.hit;
        }
        INFO("hit=" << static_cast<int>(hit) << " line=" << line);
        REQUIRE(hit == test.expected_hit);
        REQUIRE_FALSE(line.empty());
        REQUIRE(contains_non_ascii(line));

        // The bare generic key is the documented final fallback and must
        // exist in ZH as well.
        string generic;
        {
            rng::subgenerator scoped_rng(
                0x6703000000000000ULL + static_cast<uint64_t>(test.species),
                0x6704000000000000ULL);
            generic = getMiscString(test.lookup);
        }
        INFO("generic=" << generic);
        REQUIRE_FALSE(generic.empty());

        // Anti-regression: the localized species prefix key (what
        // raw=false produces under ZH) must not match any TextDB key, so
        // reverting the consumer to species::name(you.species) fails here.
        const string localized_key =
            string(species::name(test.species)) + " " + test.lookup;
        INFO("localized key=" << localized_key);
        REQUIRE(getMiscString(localized_key) == "");
    }
}

// =============================================================================
// Issue #69 — ShoutDB lookup identity (I69-R4-CODE-001 / I69-R5-CODE-001).
//
// shout.cc::_shout_key builds the monster shout key from
// mons_type_name(mc, DESC_DBNAME), which under ZH returns the localized
// monster name (zh_monster_name); the shout.txt keys are English in every
// language, so a localized key can never match and every monster shout
// silently falls back to the default region. The key must use the
// canonical English accessor mons_type_name_en(). The same defect exists
// on the SpeakDB species-insult path: do_mon_str_replacements() feeds
// _get_species_insult() with the localized foe genus (species::name(...,
// SPNAME_GENUS) for players, mons_type_name(mons_genus(...), DESC_PLAIN)
// for monsters), so "insult <genus> <type>" becomes a Chinese key and
// every species-specific insult silently falls back to the generic ones.
// The canonical genus (raw=true / mons_type_name_en) is the lookup
// identity; the localized genus stays a display token.
//
// I69-R5-CODE-001: the tests drive the real production seams with real
// actor state instead of rebuilding the keys by hand: _shout_key() is the
// exact function monster_shout() calls, and do_mon_str_replacements() is
// exercised with a real player foe (hostile monster with foe == MHITYOU,
// the monster constructor default) and with real monster foes placed in
// env.mons slots through the production allocator. A revert of any
// production accessor to the localized one changes the DB keys under ZH
// and fails the assertions below even though every resolved line still
// contains Chinese text.
// =============================================================================

namespace
{
// I69-R5-CODE-001 shared body for the ShoutDB seam; runs under both
// display languages.  `zh` selects the language-specific expectations.
void check_shout_key_production_chain(bool zh)
{
    init_monsters();
    init_mon_name_cache();

    struct shout_key_case
    {
        monster_type type;
        const char *english_db_name;
        bool resolves_in_db; // the key resolves a shout.txt entry
    };
    const array<shout_key_case, 4> cases = {{
        // A simple VISUAL-only entry.
        { MONS_MOTH_OF_WRATH, "moth of wrath", true },
        // Another plain entry, from a different creature family.
        { MONS_BALLISTOMYCETE_SPORE, "ballistomycete spore", true },
        // The imp chain: the English key drives the @imp@ recursion.
        { MONS_IRON_IMP, "iron imp", true },
        // Special branch: pandemonium lords use the fixed key, never the
        // monster DB name.  shout.txt has no "pandemonium lord" entry, so
        // monster_shout() resolves it through the glyph/default fallback;
        // only the seam key is pinned here.
        { MONS_PANDEMONIUM_LORD, "pandemonium lord", false },
    }};

    for (const shout_key_case &test : cases)
    {
        INFO("monster=" << test.english_db_name);

        // Real producer: monster_shout() calls _shout_key(mons); the
        // monster object drives the seam exactly as the production
        // consumer does.
        monster mons;
        mons.type = test.type;
        const string key = _shout_key(mons);
        REQUIRE(key == test.english_db_name);
        REQUIRE_FALSE(contains_non_ascii(key));

        if (!test.resolves_in_db)
            continue;

        // The DB lookup with the seam-selected key must resolve the line
        // in the current display language (the ZH shout.txt keeps
        // English keys with Chinese bodies).
        string line;
        {
            rng::subgenerator scoped_rng(
                0x6901000000000000ULL + static_cast<uint64_t>(test.type),
                0x6902000000000000ULL);
            line = getShoutString(key, " seen");
        }
        INFO("shout line=" << line);
        REQUIRE_FALSE(line.empty());
        if (zh)
            REQUIRE(contains_non_ascii(line));

        // The display-mode DESC_DBNAME name is localized under ZH; a
        // revert of _shout_key() to mons_type_name() would query this
        // Chinese string and silently fall back to the default region.
        const string localized_db_name =
            mons_type_name(test.type, DESC_DBNAME);
        if (zh)
        {
            INFO("localized db name=" << localized_db_name);
            REQUIRE(contains_non_ascii(localized_db_name));
            string localized_lookup;
            {
                rng::subgenerator scoped_rng(
                    0x6903000000000000ULL + static_cast<uint64_t>(test.type),
                    0x6904000000000000ULL);
                localized_lookup =
                    getShoutString(localized_db_name, " seen");
            }
            INFO("localized lookup=" << localized_lookup);
            REQUIRE(localized_lookup.empty());
        }
        else
            REQUIRE(localized_db_name == test.english_db_name);
    }
}

// RAII holder for one real monster placed in an env.mons slot through the
// production allocator, restoring the affected env/player state on exit.
struct scoped_env_monster_slot
{
    const coord_def pos;
    const unsigned short old_mgrid;
    const int old_max_mon_index;
    const uint32_t old_last_mid;
    map<uint32_t, unsigned short> old_mid_cache;
    monster *placed;

    explicit scoped_env_monster_slot(const coord_def &p)
        : pos(p), old_mgrid(env.mgrid(p)),
          old_max_mon_index(env.max_mon_index),
          old_last_mid(you.last_mid),
          old_mid_cache(env.mid_cache), placed(nullptr)
    {
    }

    ~scoped_env_monster_slot()
    {
        if (placed)
        {
            env.mid_cache.erase(placed->mid);
            placed->reset();
        }
        env.mgrid(pos) = old_mgrid;
        env.max_mon_index = old_max_mon_index;
        you.last_mid = old_last_mid;
        env.mid_cache = old_mid_cache;
    }

    monster *place(monster_type type)
    {
        placed = get_free_monster();
        if (!placed)
            return nullptr;
        placed->type = type;
        placed->set_hit_dice(1);
        placed->hit_points = placed->max_hit_points = 5;
        placed->speed = 10;
        placed->attitude = ATT_HOSTILE;
        placed->behaviour = BEH_SEEK;
        placed->set_position(pos);
        placed->set_new_monster_id();
        env.mgrid(pos) = placed->mindex();
        return placed;
    }
};

// Mirrors mon-util.cc::_get_species_insult's RNG consumption for one
// feed: the species-specific SpeakDB entry when present, otherwise the
// generic fallback entry. The production chain evaluates all three
// feeds (adj1, adj2, noun) eagerly as replace_all() arguments, so tests
// that assert on the adj2/noun feed must replay the earlier draws first.
string species_insult_at_consumed_position(const string &species,
                                           const string &type)
{
    string lookup = "insult " + species + " " + type;
    string line = getSpeakString(lowercase(lookup));
    if (line.empty())
        line = getSpeakString("insult general " + type);
    return line;
}

// I69-R5-CODE-001 shared body for the SpeakDB species-insult seam; runs
// under both display languages.
void check_species_insult_production_chain(bool zh)
{
    init_monsters();
    init_properties();

    unwind_var<player> restore_player(you);
    you = player();
    you.set_position(coord_def(20, 20));

    // --- Player-foe path: for a hostile monster with foe == MHITYOU (the
    // monster constructor default) do_mon_str_replacements() resolves the
    // foe to the player and feeds the canonical English genus
    // species::name(SP_DEEP_ELF, SPNAME_GENUS, true) == "Elf" to
    // _get_species_insult(), which must select the species-specific
    // "insult elf adj1" SpeakDB entry.
    REQUIRE(species::name(SP_DEEP_ELF, species::SPNAME_GENUS, true)
            == "Elf");
    you.species = SP_DEEP_ELF;

    monster speaker;
    speaker.type = MONS_ORC;

    string player_result;
    {
        rng::subgenerator scoped_rng(0x690b000000000000ULL,
                                     0x690c000000000000ULL);
        player_result = do_mon_str_replacements("@species_insult_adj1@",
                                                speaker, S_SHOUT);
    }
    INFO("player-foe species insult=" << player_result);
    REQUIRE_FALSE(player_result.empty());
    if (zh)
        REQUIRE(contains_non_ascii(player_result));

    // Same RNG state, same key: the production result must be exactly
    // the elf-specific entry (the adj1 feed is the first draw of the
    // eager adj1/adj2/noun sequence), and that entry must differ from
    // the generic fallback line, so a revert to the localized or
    // raw=false genus (or a missing canonical feed) would select the
    // generic line and fail the equality below.
    string elf_insult;
    string generic_adj1;
    {
        rng::subgenerator scoped_rng(0x690b000000000000ULL,
                                     0x690c000000000000ULL);
        elf_insult = species_insult_at_consumed_position("Elf", "adj1");
    }
    {
        rng::subgenerator scoped_rng(0x690b000000000000ULL,
                                     0x690c000000000000ULL);
        generic_adj1 = getSpeakString("insult general adj1");
    }
    INFO("elf insult=" << elf_insult);
    INFO("generic adj1=" << generic_adj1);
    REQUIRE_FALSE(elf_insult.empty());
    REQUIRE_FALSE(generic_adj1.empty());
    REQUIRE(elf_insult != generic_adj1);
    REQUIRE(player_result == elf_insult);

    // Species-genus display split: the felid genus display is localized
    // under ZH (T_("Cat") == 猫) while the raw identity stays "Cat"; the
    // localized genus is a display token and must never become a SpeakDB
    // key.
    REQUIRE(species::name(SP_FELID, species::SPNAME_GENUS, true) == "Cat");
    const string localized_player_genus =
        species::name(SP_FELID, species::SPNAME_GENUS);
    INFO("localized player genus=" << localized_player_genus);
    if (zh)
    {
        REQUIRE(contains_non_ascii(localized_player_genus));
        REQUIRE(localized_player_genus
                != species::name(SP_FELID, species::SPNAME_GENUS, true));
        string felid_miss;
        {
            rng::subgenerator scoped_rng(0x690d000000000000ULL,
                                         0x690e000000000000ULL);
            string felid_lookup = "insult "
                + localized_player_genus + " adj1";
            felid_miss = getSpeakString(lowercase(felid_lookup));
        }
        INFO("felid localized key lookup=" << felid_miss);
        REQUIRE(felid_miss.empty());
    }

    // --- Monster-foe path: a real mummy in an env.mons slot is the
    // speaker's foe; production feeds
    // mons_type_name_en(mons_genus(MONS_MUMMY), DESC_PLAIN) == "mummy"
    // and must select "insult mummy adj2".
    REQUIRE(mons_type_name_en(mons_genus(MONS_MUMMY), DESC_PLAIN)
            == "mummy");
    {
        scoped_env_monster_slot slot(coord_def(20, 21));
        monster *foe_mons = slot.place(MONS_MUMMY);
        REQUIRE(foe_mons != nullptr);

        monster speaker_mummy;
        speaker_mummy.type = MONS_ORC_WARRIOR;
        speaker_mummy.foe = foe_mons->mindex();

        string monster_result;
        {
            rng::subgenerator scoped_rng(0x690f000000000000ULL,
                                         0x6910000000000000ULL);
            monster_result = do_mon_str_replacements(
                "@species_insult_adj2@", speaker_mummy, S_SHOUT);
        }
        INFO("monster-foe species insult=" << monster_result);
        REQUIRE_FALSE(monster_result.empty());
        if (zh)
            REQUIRE(contains_non_ascii(monster_result));

        // The species-specific SpeakDB entry exists and differs from the
        // generic line, so the equality below really pins the
        // species-specific selection.
        string mummy_insult;
        string generic_adj2;
        {
            rng::subgenerator scoped_rng(0x690f000000000000ULL,
                                         0x6910000000000000ULL);
            mummy_insult = species_insult_at_consumed_position(
                "mummy", "adj2");
        }
        {
            rng::subgenerator scoped_rng(0x690f000000000000ULL,
                                         0x6910000000000000ULL);
            generic_adj2 = getSpeakString("insult general adj2");
        }
        INFO("mummy insult=" << mummy_insult);
        INFO("generic adj2=" << generic_adj2);
        REQUIRE_FALSE(mummy_insult.empty());
        REQUIRE_FALSE(generic_adj2.empty());
        REQUIRE(mummy_insult != generic_adj2);

        // The adj2 feed is the second eager draw (the adj1 feed misses
        // and falls back to "insult general adj1" first), so replay the
        // preceding draw before comparing.
        string expected_mummy;
        {
            rng::subgenerator scoped_rng(0x690f000000000000ULL,
                                         0x6910000000000000ULL);
            (void)species_insult_at_consumed_position("mummy", "adj1");
            expected_mummy = species_insult_at_consumed_position(
                "mummy", "adj2");
        }
        REQUIRE(monster_result == expected_mummy);

        // Anti-regression under ZH: the display-mode genus of the mummy
        // is the localized name; the localized key must miss SpeakDB.
        const string localized_mummy_genus =
            mons_type_name(mons_genus(MONS_MUMMY), DESC_PLAIN);
        if (zh)
        {
            INFO("localized mummy genus=" << localized_mummy_genus);
            REQUIRE(contains_non_ascii(localized_mummy_genus));
            string localized_miss;
            {
                rng::subgenerator scoped_rng(0x6911000000000000ULL,
                                             0x6912000000000000ULL);
                string mummy_lookup = "insult "
                    + localized_mummy_genus + " adj2";
                localized_miss =
                    getSpeakString(lowercase(mummy_lookup));
            }
            INFO("localized mummy key lookup=" << localized_miss);
            REQUIRE(localized_miss.empty());
        }
        else
            REQUIRE(localized_mummy_genus == "mummy");
    }

    // --- Generic fallback: the orc genus has no species-specific SpeakDB
    // entry ("insult orc noun" misses), so _get_species_insult() falls
    // back to the real "insult general noun" entry.
    REQUIRE(mons_type_name_en(mons_genus(MONS_ORC_WARRIOR), DESC_PLAIN)
            == "orc");
    {
        scoped_env_monster_slot slot(coord_def(20, 22));
        monster *orc_foe = slot.place(MONS_ORC_WARRIOR);
        REQUIRE(orc_foe != nullptr);

        monster speaker_orc;
        speaker_orc.type = MONS_ORC_WARRIOR;
        speaker_orc.foe = orc_foe->mindex();

        // The species-specific key genuinely misses SpeakDB in both
        // display languages, which is what forces the fallback.
        string orc_species_miss;
        {
            rng::subgenerator scoped_rng(0x6913000000000000ULL,
                                         0x6914000000000000ULL);
            orc_species_miss = getSpeakString("insult orc noun");
        }
        INFO("orc species key lookup=" << orc_species_miss);
        REQUIRE(orc_species_miss.empty());

        string fallback_result;
        {
            rng::subgenerator scoped_rng(0x6915000000000000ULL,
                                         0x6916000000000000ULL);
            fallback_result = do_mon_str_replacements(
                "@species_insult_noun@", speaker_orc, S_SHOUT);
        }
        INFO("generic-fallback species insult=" << fallback_result);
        REQUIRE_FALSE(fallback_result.empty());
        if (zh)
            REQUIRE(contains_non_ascii(fallback_result));

        // All three feeds miss for the orc genus, so the noun feed is
        // the third eager draw (after the two generic fallback draws);
        // replay the full consumption and compare the last draw.
        string expected_fallback;
        {
            rng::subgenerator scoped_rng(0x6915000000000000ULL,
                                         0x6916000000000000ULL);
            (void)species_insult_at_consumed_position("orc", "adj1");
            (void)species_insult_at_consumed_position("orc", "adj2");
            expected_fallback =
                species_insult_at_consumed_position("orc", "noun");
        }
        INFO("expected fallback=" << expected_fallback);
        REQUIRE_FALSE(expected_fallback.empty());
        REQUIRE(fallback_result == expected_fallback);

        // Anti-regression under ZH: the localized orc genus key misses.
        const string localized_orc_genus =
            mons_type_name(mons_genus(MONS_ORC_WARRIOR), DESC_PLAIN);
        if (zh)
        {
            INFO("localized orc genus=" << localized_orc_genus);
            REQUIRE(contains_non_ascii(localized_orc_genus));
            string localized_miss;
            {
                rng::subgenerator scoped_rng(0x6917000000000000ULL,
                                             0x6918000000000000ULL);
                string orc_lookup = "insult "
                    + localized_orc_genus + " noun";
                localized_miss =
                    getSpeakString(lowercase(orc_lookup));
            }
            INFO("localized orc key lookup=" << localized_miss);
            REQUIRE(localized_miss.empty());
        }
        else
            REQUIRE(localized_orc_genus == "orc");
    }
}
} // namespace

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: ShoutDB monster keys resolve through the production seam",
                 "[zh-translation][shout][issue-69]")
{
    check_shout_key_production_chain(true);
}

TEST_CASE_METHOD(EnTranslationFixture,
                 "en: ShoutDB monster keys resolve through the production seam",
                 "[zh-translation][shout][issue-69]")
{
    check_shout_key_production_chain(false);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: species-insult SpeakDB keys resolve through the production seam",
                 "[zh-translation][shout][issue-69]")
{
    check_species_insult_production_chain(true);
}

TEST_CASE_METHOD(EnTranslationFixture,
                 "en: species-insult SpeakDB keys resolve through the production seam",
                 "[zh-translation][shout][issue-69]")
{
    check_species_insult_production_chain(false);
}

// Issue #70 — mons_speaks genus fallback (I70-R4-CODE-001 / CR-005).
//
// mon-speak.cc::mons_speaks resolves the genus fallback with
// mons_type_name_en(mons_genus(mons->type), DESC_DBNAME). Under ZH the old
// localized accessor returned the Chinese genus name, which can never match
// the English monspeak keys, so the orc genus speech silently fell through
// to the (absent) glyph/shape keys and the monster stayed silent. These
// tests drive the real mons_speaks() production entry with real monsters
// whose exact DB-name keys are absent while the genus key ("orc") or the
// glyph key ("'l'") exists, and capture the final emission through the
// production observer seam: canonical-English genus hit, localized key
// miss, EN output unchanged (the emission equals the direct "orc"
// production rendering replayed at the same RNG position), RNG state/count
// topology identical between languages, and the glyph/shape fallback still
// fires consistently when the genus genuinely misses.
// =============================================================================

namespace
{
// Final-emission capture through mon_speech_emission_observer plus the RNG
// state/count after the production path (mirrors test_mon_cast_target).
struct monspeak_capture
{
    vector<mon_speech_final_emission> emissions;
    uint64_t state = 0;
    uint64_t count = 0;

    static void observe(const mon_speech_final_emission &emission,
                        void *context)
    {
        static_cast<monspeak_capture *>(context)->emissions.push_back(
            emission);
    }
};

// Re-init the TextDB layers in the requested display language (mirrors
// scoped_zh_database; scoped_test_language alone cannot swap the loaded
// SpeakDB translation layer).
struct scoped_monspeak_database
{
    lang_t saved_language = Options.language;
    const char *saved_name = Options.lang_name;

    explicit scoped_monspeak_database(lang_t language)
    {
        databaseSystemShutdown();
        Options.language = language;
        Options.lang_name = language == lang_t::ZH ? "zh" : nullptr;
        databaseSystemInit();
        i18n_cache_clear();
    }

    ~scoped_monspeak_database()
    {
        databaseSystemShutdown();
        Options.language = saved_language;
        Options.lang_name = saved_name;
        databaseSystemInit();
        i18n_cache_clear();
    }
};

// Minimal real world for mons_speaks: a lit floor around the player, wizard
// vision (the lightweight player fixture has no populated LOS cache), and
// one real monster in an env.mons slot through the production allocator.
struct scoped_monspeak_world
{
    const coord_def player_pos;
    const bool old_test;
    const coord_def old_player_position;
    const bool old_on_current_level;
    const uint8_t old_current_vision;
    const bool old_wizard_vision;
    const mid_t old_last_mid;
    const int old_max_mon_index;
    const map<mid_t, unsigned short> old_mid_cache;
    vector<tuple<coord_def, dungeon_feature_type, unsigned short,
                 uint32_t>> cells;
    monster *placed = nullptr;

    explicit scoped_monspeak_world(coord_def p = coord_def(20, 20))
        : player_pos(p), old_test(crawl_state.test),
          old_player_position(you.pos()),
          old_on_current_level(you.on_current_level),
          old_current_vision(you.current_vision),
          old_wizard_vision(you.wizard_vision),
          old_last_mid(you.last_mid),
          old_max_mon_index(env.max_mon_index),
          old_mid_cache(env.mid_cache)
    {
        crawl_state.test = true;
        you.on_current_level = true;
        you.current_vision = LOS_DEFAULT_RANGE;
        you.wizard_vision = true;
        for (int x = 15; x <= 30; ++x)
            for (int y = 15; y <= 30; ++y)
            {
                const coord_def position(x, y);
                cells.emplace_back(position, env.grid(position),
                                   env.mgrid(position),
                                   env.level_map_ids(position));
                env.grid(position) = DNGN_FLOOR;
                env.mgrid(position) = NON_MONSTER;
                env.level_map_ids(position) = INVALID_MAP_INDEX;
            }
        you.set_position(player_pos);
        invalidate_los();
    }

    ~scoped_monspeak_world()
    {
        if (placed)
        {
            env.mid_cache.erase(placed->mid);
            placed->reset();
        }
        for (const auto &cell : cells)
        {
            env.grid(get<0>(cell)) = get<1>(cell);
            env.mgrid(get<0>(cell)) = get<2>(cell);
            env.level_map_ids(get<0>(cell)) = get<3>(cell);
        }
        you.set_position(old_player_position);
        you.on_current_level = old_on_current_level;
        you.current_vision = old_current_vision;
        you.wizard_vision = old_wizard_vision;
        you.last_mid = old_last_mid;
        env.max_mon_index = old_max_mon_index;
        env.mid_cache = old_mid_cache;
        crawl_state.test = old_test;
        invalidate_los();
    }

    monster *place(monster_type type, coord_def position = coord_def(20, 21))
    {
        placed = get_free_monster();
        if (!placed)
            return nullptr;
        placed->type = type;
        placed->set_hit_dice(1);
        placed->hit_points = placed->max_hit_points = 5;
        placed->speed = 10;
        placed->attitude = ATT_HOSTILE;
        placed->behaviour = BEH_SEEK;
        placed->foe = MHITYOU;
        placed->set_position(position);
        placed->set_new_monster_id();
        env.mgrid(position) = placed->mindex();
        return placed;
    }
};

// One production mons_speaks run in one display language: the genus/glyph
// scenario monster is placed in a fresh world and the final emission is
// captured with the RNG state/count after the path.
struct monspeak_run_result
{
    monspeak_capture capture;
    string line;
    bool spoke = false;
};

monspeak_run_result observe_mons_speaks(
    lang_t language, monster_type type,
    uint64_t seed, uint64_t sequence)
{
    scoped_monspeak_database database(language);
    scoped_monspeak_world world;
    monster *mons = world.place(type);
    REQUIRE(mons != nullptr);

    monspeak_run_result result;
    const mon_speech_emission_observer observer = {
        monspeak_capture::observe, &result.capture };
    rng::subgenerator scoped_rng(seed, sequence);
    result.spoke = mons_speaks(mons, &observer);
    result.capture.state = rng::current_generator().get_state();
    result.capture.count = rng::current_generator().get_count();
    if (!result.capture.emissions.empty())
        result.line = result.capture.emissions[0].line;
    return result;
}

void check_mons_speaks_genus_fallback()
{
    init_monsters();
    init_mon_name_cache();
    unwind_var<player> restore_player(you);
    you = player();
    you.hp = you.hp_max = 10;
    // A real religion (not GOD_NO_GOD, whose _god_name_en() is the empty
    // string and would insert a stray space prefix that breaks the skip-all
    // fallback chain exactly like production for no-god players). Makhleb
    // is not a good god, so no extra coinflip is drawn while building the
    // prefix list.
    you.religion = GOD_MAKHLEB;

    // Canonical-English genus identity: the exact DB name, glyph and shape
    // keys of the orc warrior all miss monspeak, so the genus fallback is
    // the only possible speech source.
    REQUIRE(mons_type_name_en(mons_genus(MONS_ORC_WARRIOR), DESC_DBNAME)
            == "orc");
    REQUIRE(getSpeakString("orc warrior").empty());
    REQUIRE(getSpeakString("'o'").empty());
    REQUIRE(getSpeakString("humanoid").empty());

    // Localized key miss: under ZH the display-mode genus is the Chinese
    // name and must miss SpeakDB; under EN it equals the canonical key.
    const string localized_genus =
        mons_type_name(mons_genus(MONS_ORC_WARRIOR), DESC_DBNAME);
    if (Options.language == lang_t::ZH)
    {
        INFO("localized orc genus=" << localized_genus);
        REQUIRE(contains_non_ascii(localized_genus));
        REQUIRE(getSpeakString(localized_genus).empty());
    }
    else
        REQUIRE(localized_genus == "orc");

    // The seed is chosen so that the third production draw (the "orc"
    // weighted pick, random2(20) over the w:19 __NONE / w:1
    // @_generic_orc_speech_@ variants) selects the w:1 speak variant; the
    // replay below pins the exact draw position (verified against a PCG
    // re-implementation: draws 1,1,19 for this seed/sequence pair).
    constexpr uint64_t seed = 0x7000003aULL;
    constexpr uint64_t sequence = 0x47554e55ULL;

    const monspeak_run_result english =
        observe_mons_speaks(lang_t::EN, MONS_ORC_WARRIOR, seed, sequence);
    const monspeak_run_result chinese =
        observe_mons_speaks(lang_t::ZH, MONS_ORC_WARRIOR, seed, sequence);

    // Both languages reach the genus key and emit exactly one line; a
    // reverted localized genus accessor under ZH would miss "orc" (and the
    // glyph/shape keys), so mons_speaks would return false with no
    // emission.
    REQUIRE(english.spoke);
    REQUIRE(chinese.spoke);
    REQUIRE(english.capture.emissions.size() == 1);
    REQUIRE(chinese.capture.emissions.size() == 1);
    REQUIRE_FALSE(english.line.empty());
    REQUIRE_FALSE(chinese.line.empty());
    REQUIRE(english.line.find('@') == string::npos);
    REQUIRE(chinese.line.find('@') == string::npos);
    CHECK(english.capture.emissions[0].channel == MSGCH_TALK);
    CHECK(chinese.capture.emissions[0].channel == MSGCH_TALK);
    REQUIRE(contains_non_ascii(chinese.line));

    // RNG state/count topology: both languages consume exactly the same
    // draws through the production path (the exact-name miss, the genus
    // fallback and the nested token expansions), so the generator state and
    // count after the emission must be identical.
    CHECK(english.capture.state == chinese.capture.state);
    CHECK(english.capture.count == chinese.capture.count);

    // EN output unchanged + canonical-English genus hit: replaying the two
    // production coinflip draws before the "orc" lookup and rendering the
    // direct getSpeakString("orc") result through the production
    // replacement pipeline must reproduce the emission byte-for-byte in
    // each display language.
    for (const lang_t language : { lang_t::EN, lang_t::ZH })
    {
        scoped_monspeak_database database(language);
        scoped_monspeak_world world;
        monster *orc = world.place(MONS_ORC_WARRIOR);
        REQUIRE(orc != nullptr);
        rng::subgenerator scoped_rng(seed, sequence);
        (void)random2(2);   // exact-name miss coinflip
        (void)random2(2);   // genus __try_exact_string coinflip
        const string expected =
            do_mon_str_replacements(getSpeakString("orc"), *orc);
        const string &emitted = language == lang_t::EN
            ? english.line : chinese.line;
        INFO("language=" << (language == lang_t::ZH ? "zh" : "en"));
        CHECK(expected == emitted);
    }
}

void check_mons_speaks_glyph_fallback()
{
    init_monsters();
    init_mon_name_cache();
    unwind_var<player> restore_player(you);
    you = player();
    you.hp = you.hp_max = 10;
    // Same real-religion setup as the genus scenario (see above).
    you.religion = GOD_MAKHLEB;

    // MONS_BASILISK: exact "basilisk" and genus "giant lizard" keys both
    // miss monspeak in every language, so the glyph key "'l'" is the next
    // fallback; the shape key "humanoid" also misses, so the glyph path is
    // the only possible speech source.
    REQUIRE(mons_type_name_en(MONS_BASILISK, DESC_DBNAME) == "basilisk");
    REQUIRE(mons_type_name_en(mons_genus(MONS_BASILISK), DESC_DBNAME)
            == "giant lizard");
    REQUIRE(getSpeakString("basilisk").empty());
    REQUIRE(getSpeakString("giant lizard").empty());
    REQUIRE_FALSE(getSpeakString("'l'").empty());

    constexpr uint64_t seed = 0x70474c59ULL;
    constexpr uint64_t sequence = 0x5048454eULL;

    const monspeak_run_result english =
        observe_mons_speaks(lang_t::EN, MONS_BASILISK, seed, sequence);
    const monspeak_run_result chinese =
        observe_mons_speaks(lang_t::ZH, MONS_BASILISK, seed, sequence);

    REQUIRE(english.spoke);
    REQUIRE(chinese.spoke);
    REQUIRE(english.capture.emissions.size() == 1);
    REQUIRE(chinese.capture.emissions.size() == 1);
    REQUIRE_FALSE(english.line.empty());
    REQUIRE_FALSE(chinese.line.empty());
    REQUIRE(english.line.find('@') == string::npos);
    REQUIRE(chinese.line.find('@') == string::npos);
    CHECK(english.capture.emissions[0].channel == MSGCH_TALK);
    CHECK(chinese.capture.emissions[0].channel == MSGCH_TALK);
    REQUIRE(contains_non_ascii(chinese.line));
    CHECK(english.capture.state == chinese.capture.state);
    CHECK(english.capture.count == chinese.capture.count);

    // Glyph/shape fallback consistency: replaying the three production
    // coinflip draws (exact miss, genus miss, glyph-path miss) before the
    // "'l'" lookup must reproduce the emission in each display language.
    for (const lang_t language : { lang_t::EN, lang_t::ZH })
    {
        scoped_monspeak_database database(language);
        scoped_monspeak_world world;
        monster *basilisk = world.place(MONS_BASILISK);
        REQUIRE(basilisk != nullptr);
        rng::subgenerator scoped_rng(seed, sequence);
        (void)random2(2);   // exact-name miss coinflip
        (void)random2(2);   // genus miss coinflip
        (void)random2(2);   // glyph-path __try_exact_string coinflip
        const string expected =
            do_mon_str_replacements(getSpeakString("'l'"), *basilisk);
        const string &emitted = language == lang_t::EN
            ? english.line : chinese.line;
        INFO("language=" << (language == lang_t::ZH ? "zh" : "en"));
        CHECK(expected == emitted);
    }
}
} // namespace

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: mons_speaks genus fallback resolves through the production seam",
                 "[zh-translation][monspeak][issue-70]")
{
    check_mons_speaks_genus_fallback();
    check_mons_speaks_glyph_fallback();
}

TEST_CASE_METHOD(EnTranslationFixture,
                 "en: mons_speaks genus fallback resolves through the production seam",
                 "[zh-translation][monspeak][issue-70]")
{
    check_mons_speaks_genus_fallback();
    check_mons_speaks_glyph_fallback();
}
