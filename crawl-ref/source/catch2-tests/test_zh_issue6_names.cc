#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "database.h"
#include "dlua.h"
#include "files.h"
#include <fstream>
#include "directn.h"
#include "describe.h"
#include "mon-util.h"
#include "mutation.h"
#include "notes.h"
#include "ng-init.h"
#include "transform.h"
#include "english.h"
#include "item-name.h"
#include "hiscores.h"
#include "message.h"
#include "state.h"
#include "zot.h"
#include "item-prop.h"
#include "item-status-flag-type.h"
#include "lang-en-guard.h"
#include "mon-info.h"
#include "monster.h"
#include "religion.h"
#include "options.h"
#include "player.h"
#include "random.h"
#include "species.h"
#include "stringutil.h"
#include "tags.h"
#include "test_zh_fixture.h"
#include "unwind.h"
#include "zh-scroll-appearance.h"

namespace species
{
string skin_name_en(species_type species, bool adj = false);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 6 grammar keeps gender, case, and ownership output",
                 "[zh-translation][issue-6][grammar]")
{
    const char * const english[][NUM_PRONOUN_CASES] =
    {
        { "it", "its", "itself", "it" },
        { "he", "his", "himself", "him" },
        { "she", "her", "herself", "her" },
        { "you", "your", "yourself", "you" },
        { "they", "their", "themself", "them" },
    };
    const char * const chinese[][NUM_PRONOUN_CASES] =
    {
        { "它", "它的", "它自己", "它" },
        { "他", "他的", "他自己", "他" },
        { "她", "她的", "她自己", "她" },
        { "你", "你的", "你自己", "你" },
        { "他", "他的", "他自己", "他" },
    };
    for (int g = 0; g < NUM_GENDERS; ++g)
        for (int p = 0; p < NUM_PRONOUN_CASES; ++p)
        {
            const auto gender = static_cast<gender_type>(g);
            const auto variant = static_cast<pronoun_type>(p);
            const string display = decline_pronoun(gender, variant);
            CHECK(display == chinese[g][p]);
            i18n_cache_clear();
            CHECK(display == chinese[g][p]);
            CHECK(string(decline_pronoun(gender, variant)) == display);
            ScopedLangEn canonical;
            CHECK(string(decline_pronoun(gender, variant)) == english[g][p]);
        }

    CHECK(apostrophise("").empty());
    CHECK(apostrophise("hero") == "hero的");
    CHECK(apply_description(DESC_YOUR, "sword") == "你的sword");
    CHECK(apply_description(DESC_THE, "sword") == "sword");
    CHECK(apply_description(DESC_A, "sword") == "sword");
    ScopedLangEn canonical;
    CHECK(apostrophise("hero") == "hero's");
    CHECK(apostrophise("you") == "your");
    CHECK(apostrophise("herself") == "her own");
    CHECK(apply_description(DESC_YOUR, "sword") == "your sword");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 6 number vocabulary preserves grouping boundaries",
                 "[zh-translation][issue-6][grammar][interface-rereview]")
{
    // A leading ten omits one; ten following hundreds/thousands retains it.
    // Values beyond the finite zero..thousand vocabulary use whole digits.
    const pair<unsigned, const char *> cases[] =
    {
        { 0, "零" }, { 1, "一" }, { 9, "九" }, { 10, "十" },
        { 11, "十一" }, { 19, "十九" }, { 20, "二十" }, { 21, "二十一" },
        { 99, "九十九" }, { 100, "一百" }, { 101, "一百零一" },
        { 109, "一百零九" }, { 110, "一百一十" },
        { 111, "一百一十一" }, { 119, "一百一十九" },
        { 120, "一百二十" }, { 999, "九百九十九" }, { 1000, "一千" },
        { 1001, "一千零一" }, { 1010, "一千零一十" },
        { 1011, "一千零一十一" }, { 1110, "一千一百一十" },
        { 1100, "一千一百" }, { 9999, "九千九百九十九" },
        { 10000, "10000" }, { 10010, "10010" }, { 123456, "123456" },
    };
    for (const auto &test : cases)
    {
        INFO("number=" << test.first);
        CHECK(number_in_words(test.first) == test.second);
        const string canonical = number_in_words_en(test.first);
        ScopedLangEn english;
        CHECK(number_in_words(test.first) == canonical);
    }
    CHECK(number_in_words(~0U) == to_string(~0U));
    CHECK(number_in_words_en(8) == "eight");
    CHECK(number_in_words_en(20) == "twenty");
    CHECK(number_in_words_en(101) == "one hundred and one");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 6 skin display preserves canonical anatomy",
                 "[zh-translation][issue-6][skin][interface-rereview]")
{
    struct skin_case
    {
        species_type species;
        const char *noun_en;
        const char *adj_en;
        const char *noun_zh;
        const char *adj_zh;
    };
    const skin_case cases[] =
    {
        { SP_HUMAN, "skin", "fleshy", "皮肤", "肉质的" },
        { SP_RED_DRACONIAN, "scales", "scaled", "鳞片", "鳞片的" },
        { SP_NAGA, "scales", "scaled", "鳞片", "鳞片的" },
        { SP_TENGU, "feathers", "feathered", "羽毛", "羽毛的" },
        { SP_FELID, "fur", "furry", "毛皮", "毛茸茸的" },
        { SP_MUMMY, "bandages", "bandage-wrapped", "绷带", "绷带包裹的" },
        { SP_GARGOYLE, "stone", "stony", "石头", "石质的" },
        { SP_POLTERGEIST, "ectoplasm", "ectoplasmic", "灵质", "灵质的" },
        { SP_REVENANT, "bones", "bony", "骨头", "骨质的" },
    };
    // Adjective accessors are retained compatibility/helper coverage; this
    // table does not claim a current UI consumer uses every adjective.
    for (const auto &test : cases)
    {
        CHECK(species::skin_name(test.species) == test.noun_zh);
        CHECK(species::skin_name(test.species, true) == test.adj_zh);
        CHECK(species::skin_name_en(test.species) == test.noun_en);
        CHECK(species::skin_name_en(test.species, true) == test.adj_en);
        ScopedLangEn english;
        CHECK(species::skin_name(test.species) == test.noun_en);
        CHECK(species::skin_name(test.species, true) == test.adj_en);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 6 scroll display preserves seed, serialization, and RNG",
                 "[zh-translation][issue-6][scroll][tags][rng]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    item_def scroll;
    scroll.base_type = OBJ_SCROLLS;
    scroll.sub_type = SCR_BLINKING;
    scroll.quantity = 1;
    scroll.pos = coord_def(-1, -1);
    scroll.rnd = 1; // Required item identity byte, independent of subtype_rnd.

    // Seeds exercise every binding and seal, including SSE_NONE and high bits.
    const pair<uint32_t, const char *> cases[] =
    {
        { 0x00, "红绸带蜡封的卷轴" }, { 0x10, "蓝绸带蜡封的卷轴" },
        { 0x20, "麻绳蜡封的卷轴" }, { 0x30, "金丝线蜡封的卷轴" },
        { 0x40, "银丝线蜡封的卷轴" }, { 0x50, "皮绳蜡封的卷轴" },
        { 0x60, "绿绸带蜡封的卷轴" }, { 0x70, "紫绸带蜡封的卷轴" },
        { 0x80, "黑丝线蜡封的卷轴" }, { 0x90, "白绸带蜡封的卷轴" },
        { 0xa0, "铜链蜡封的卷轴" }, { 0xb0, "素色带蜡封的卷轴" },
        { 0x1000, "银丝线金箔封的卷轴" }, { 0x2000, "黑丝线银箔封的卷轴" },
        { 0x3000, "红绸带骨扣的卷轴" }, { 0x4000, "银丝线玉扣的卷轴" },
        { 0x5000, "黑丝线铜扣的卷轴" }, { 0x6000, "红绸带锡封的卷轴" },
        { 0x7000, "银丝线火漆印的卷轴" }, { 0x8000, "黑丝线符纸封的卷轴" },
        { 0x9000, "红绸带的卷轴" }, { 0xffffffff, "金丝线铜扣的卷轴" },
    };
    rng::subgenerator scoped_rng(0x6006600660066006ULL);
    const auto rng_state = rng::current_generator().get_state();
    const auto rng_count = rng::current_generator().get_count();
    for (const auto &test : cases)
    {
        INFO("seed=" << test.first);
        scroll.subtype_rnd = test.first;
        const string display = scroll.name(DESC_PLAIN);
        CHECK(display == test.second);
        CHECK(scroll.name(DESC_BASENAME) == "卷轴");
        CHECK(scroll.subtype_rnd == test.first);
        i18n_cache_clear();
        CHECK(scroll.name(DESC_PLAIN) == display);

        vector<unsigned char> bytes;
        writer output(&bytes);
        marshallItem(output, scroll, true);
        reader input(bytes);
        input.setMinorVersion(TAG_MINOR_VERSION);
        item_def loaded;
        unmarshallItem(input, loaded);
        CHECK(loaded.subtype_rnd == test.first);
        CHECK(loaded.name(DESC_PLAIN) == display);

        ScopedLangEn english;
        CHECK(scroll.name(DESC_PLAIN)
              == "scroll labelled " + make_name(test.first, MNAME_SCROLL));
        CHECK(scroll.name(DESC_BASENAME) == "scroll");
    }
    CHECK(rng::current_generator().get_state() == rng_state);
    CHECK(rng::current_generator().get_count() == rng_count);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 6 missing vocabulary uses complete English fallback",
                 "[zh-translation][issue-6][scroll][grammar][textdb]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    item_def scroll;
    scroll.base_type = OBJ_SCROLLS;
    scroll.sub_type = SCR_BLINKING;
    scroll.quantity = 1;
    scroll.subtype_rnd = 0x9000;
    string english_name;
    {
        ScopedLangEn english;
        english_name = scroll.name(DESC_PLAIN);
    }
    Options.lang_name = "zz-no-textdb";
    databaseSystemInit();
    CHECK(translated_scroll_appearance(scroll.subtype_rnd).empty());
    CHECK(scroll.name(DESC_PLAIN) == english_name);
    CHECK(number_in_words(101) == "one hundred and one");
    CHECK(species::skin_name(SP_REVENANT) == "bones");
    CHECK(string(decline_pronoun(GENDER_FEMALE, PRONOUN_POSSESSIVE)) == "her");
    CHECK(string(decline_pronoun(GENDER_FEMALE, PRONOUN_OBJECTIVE)) == "her");

    Options.lang_name = "zh";
    databaseSystemInit();
    CHECK(scroll.name(DESC_PLAIN) == "红绸带的卷轴");
    CHECK(number_in_words(101) == "一百零一");
    CHECK(species::skin_name(SP_REVENANT) == "骨头");
    CHECK(string(decline_pronoun(GENDER_FEMALE, PRONOUN_POSSESSIVE)) == "她的");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 6 item assembly keeps display and English lookup names",
                 "[zh-translation][issue-6][item-name]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    item_def item;
    item.quantity = 1;
    item.flags = ISFLAG_IDENTIFIED;
    item.base_type = OBJ_WANDS;
    item.sub_type = WAND_FLAME;
    CHECK(item.name(DESC_PLAIN) == "火焰魔杖");
    {
        ScopedLangEn english;
        CHECK(item.name(DESC_DBNAME) == "wand of flame");
    }
    item.base_type = OBJ_POTIONS;
    item.sub_type = POT_CURING;
    CHECK(item.name(DESC_PLAIN) == "治疗药水");
    {
        ScopedLangEn english;
        CHECK(item.name(DESC_DBNAME) == "potion of curing");
    }
    item.base_type = OBJ_STAVES;
    item.sub_type = STAFF_FIRE;
    CHECK(item.name(DESC_PLAIN) == string(staff_type_name(STAFF_FIRE)) + "法杖");
    {
        ScopedLangEn english;
        CHECK(item.name(DESC_DBNAME) == "staff of fire");
    }
    item.base_type = OBJ_BOOKS;
    item.sub_type = BOOK_NECROMANCY;
    CHECK(sub_type_string(item) == "死灵术之书");
    {
        ScopedLangEn english;
        CHECK(sub_type_string(item) == "book of Necromancy");
    }
    item.base_type = OBJ_WEAPONS;
    item.sub_type = WPN_DAGGER;
    item.brand = SPWPN_VENOM;
    const string brand = weapon_brand_name(item, false);
    CHECK(weapon_brand_desc("blade", item, false) == brand + "之blade");
    {
        ScopedLangEn english;
        CHECK(weapon_brand_desc("blade", item, false) == "blade of venom");
    }
    item.base_type = OBJ_MISSILES;
    item.sub_type = MI_JAVELIN;
    item.brand = SPMSL_CHAOS;
    const string missile = missile_name(MI_JAVELIN);
    const string missile_brand = missile_brand_name(item, MBN_NAME);
    CHECK(item.name(DESC_PLAIN) == missile_brand + "之" + missile);
    item.base_type = OBJ_ARMOUR;
    item.sub_type = ARM_ROBE;
    item.brand = SPARM_FIRE_RESISTANCE;
    const string ego = armour_ego_name(item, false);
    CHECK(item.name(DESC_PLAIN) == "+0 " + ego + "之" + item_base_name(item));
}


TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: round2 type display articles preserve English identity",
                 "[zh-translation][round2][names]")
{
    init_monsters();
    unwind_var<player> restore_player(you);
    you = player();
    const monster_type types[] = { MONS_ORB_OF_WINTER, MONS_ORC,
                                   MONS_ROYAL_JELLY, MONS_ENCHANTRESS };
    const description_level_type descriptions[] = { DESC_PLAIN, DESC_A, DESC_THE,
                                                   DESC_DBNAME };
    for (monster_type type : types)
    {
        for (description_level_type desc : descriptions)
        {
            const string display = mons_type_name(type, desc);
            CHECK(display == mons_type_name(type, DESC_PLAIN));
            const string identity = mons_type_name_en(type, desc);
            ScopedLangEn english;
            CHECK(mons_type_name(type, desc) == identity);
            CHECK(mons_type_name_en(type, desc) == identity);
        }
    }
    you.zot_orb_monster_known = true;
    you.zot_orb_monster = MONS_ORB_OF_WINTER;
    const string statue = feature_description(DNGN_ZOT_STATUE, "", DESC_A);
    CHECK(statue == "寒冬之球雕像");
    const Note note(NOTE_SEEN_FEAT, 0, 0, statue + ".");
    CHECK(note.describe(false, false).find("a ") == string::npos);
    CHECK(note.name == statue + ".");
    // Existing persisted snapshots are neither mutated nor retrotranslated.
    const Note historic(NOTE_SEEN_FEAT, 0, 0, "a historic statue.");
    CHECK(historic.name == "a historic statue.");
    {
        ScopedLangEn english;
        CHECK(feature_description(DNGN_ZOT_STATUE, "", DESC_A)
              == "a statue of an orb of winter");
        CHECK(note.name == statue + ".");
        CHECK(historic.name == "a historic statue.");
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: round2 clear potion appearance keeps action and identity",
                 "[zh-translation][round2][names]")
{
#if TAG_MAJOR_VERSION == 34
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    item_def potion;
    potion.base_type = OBJ_POTIONS;
    potion.sub_type = POT_MUTATION;
    potion.quantity = 1;
    potion.rnd = 1;
    potion.subtype_rnd = PDESCQ(PDQ_NONE, PDC_CLEAR);
    CHECK(potion.name(DESC_PLAIN) == "透明药水");
    CHECK(string(T_("clear")) == "清除");
    CHECK(potion.sub_type == POT_MUTATION);
    CHECK(potion.subtype_rnd == PDESCQ(PDQ_NONE, PDC_CLEAR));
    {
        ScopedLangEn english;
        CHECK(potion.name(DESC_PLAIN) == "clear potion");
        CHECK(potion.name(DESC_DBNAME, false, true) == "potion of mutation");
    }
    CHECK(potion.name(DESC_PLAIN) == "透明药水");
#endif
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: round2 morgue physiology summaries translate display only",
                 "[zh-translation][round2][names]")
{
    init_mut_index();
    unwind_var<player> restore_player(you);
    you = player();
    you.species = SP_HUMAN;
    you.form = transformation::tree;
    const string tree_summary = terse_mutation_list();
    CHECK(tree_summary.find("植物生理") != string::npos);
    CHECK(tree_summary.find("两栖") != string::npos);
    CHECK(tree_summary.find("plant physiology") == string::npos);
    CHECK(you.form == transformation::tree);
    {
        ScopedLangEn english;
        CHECK(terse_mutation_list().find("plant physiology") != string::npos);
        CHECK(terse_mutation_list().find("amphibious") != string::npos);
    }
    you.form = transformation::none;
    you.species = SP_GARGOYLE;
    CHECK(terse_mutation_list().find("无肉生理") != string::npos);
    CHECK(you.species == SP_GARGOYLE);
    {
        ScopedLangEn english;
        CHECK(terse_mutation_list().find("fleshless physiology") != string::npos);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "family: every missile brand keeps its modifier before the Chinese noun",
                 "[zh-translation][family-fixes][names]")
{
    init_properties();
    for (int brand = SPMSL_NORMAL; brand < NUM_SPECIAL_MISSILES; ++brand)
    for (int quantity : {1, 3})
    {
        item_def item;
        item.base_type = OBJ_MISSILES;
        item.sub_type = MI_DART;
        item.brand = brand;
        item.quantity = quantity;
        item.flags = ISFLAG_IDENTIFIED;
        const string noun = missile_name(MI_DART);
        const string full = item.name(DESC_PLAIN);
        const string terse = item.name(DESC_PLAIN, true);
        INFO("brand=" << brand << " full=" << full);
        REQUIRE(full.find(noun) != string::npos);
        if (brand != SPMSL_NORMAL)
        {
            const string modifier = missile_brand_name(item, MBN_NAME);
            REQUIRE(full.find(modifier) != string::npos);
            CHECK(full.find(modifier) < full.find(noun));
            CHECK(full.substr(full.size() - noun.size()) == noun);
            CHECK(terse.find(" (") != string::npos);
        }
        CHECK(item.name(DESC_BASENAME) == noun);
        CHECK(item.name(DESC_DBNAME) == noun);
        {
            ScopedLangEn english;
            const string en = item.name(DESC_PLAIN);
            CHECK(en.find(quantity == 1 ? "dart" : "darts") != string::npos);
            if (brand == SPMSL_DISJUNCTION)
                CHECK(en.find(" of disjunction") != string::npos);
            CHECK(item.name(DESC_DBNAME) == "dart");
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "acceptance: colliding scroll labels stay distinguishable across all saved types",
                 "[zh-translation][acceptance-fixes][scroll]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    // All these valid label seeds shared one physical appearance before the
    // fix. Keep a full type registry, including compatibility types.
    vector<uint32_t> seeds;
    for (int type = 0; type < NUM_SCROLLS; ++type)
    {
        const uint32_t seed = (OBJ_SCROLLS << 16) | (((type / 16) * 3) << 8) | (type % 16);
        you.item_description[IDESC_SCROLLS][type] = seed;
        seeds.push_back(seed);
    }
    rng::subgenerator scoped_rng(20261025);
    const auto state = rng::current_generator().get_state();
    const auto count = rng::current_generator().get_count();
    map<uint32_t, string> names;
    set<string> unique_names;
    for (uint32_t seed : seeds)
    {
        item_def scroll;
        scroll.base_type = OBJ_SCROLLS;
        scroll.sub_type = SCR_BLINKING;
        scroll.quantity = 1;
        scroll.rnd = 1;
        scroll.subtype_rnd = seed;
        const string display = scroll.name(DESC_PLAIN);
        REQUIRE_FALSE(display.empty());
        CHECK(unique_names.insert(display).second);
        names[seed] = display;
        vector<unsigned char> bytes;
        writer output(&bytes);
        marshallItem(output, scroll, true);
        reader input(bytes);
        input.setMinorVersion(TAG_MINOR_VERSION);
        item_def loaded;
        unmarshallItem(input, loaded);
        CHECK(loaded.subtype_rnd == seed);
        CHECK(loaded.name(DESC_PLAIN) == display);
        {
            ScopedLangEn english;
            CHECK(scroll.name(DESC_PLAIN) == "scroll labelled " + make_name(seed, MNAME_SCROLL));
        }
        CHECK(scroll.name(DESC_PLAIN) == display);
    }
    // Reordering the subtype entries cannot turn this into a subtype identity
    // leak. Unidentified and identified inventory order is never consulted.
    for (int type = 0; type < NUM_SCROLLS; ++type)
        you.item_description[IDESC_SCROLLS][type] = seeds[NUM_SCROLLS - type - 1];
    i18n_cache_clear();
    for (const auto &entry : names)
        CHECK(translated_scroll_appearance(entry.first) == entry.second);
    for (int type = 0; type < NUM_SCROLLS; ++type)
        CHECK(you.item_description[IDESC_SCROLLS][type] == seeds[NUM_SCROLLS - type - 1]);
    CHECK(rng::current_generator().get_state() == state);
    CHECK(rng::current_generator().get_count() == count);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "acceptance: generated scroll registries have unique stable physical appearances",
                 "[zh-translation][acceptance-fixes][scroll]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    for (uint64_t seed : {625102501ULL, 425202670ULL, 425202671ULL, 1ULL, 2ULL, 3ULL})
    {
        rng::subgenerator scoped_rng(seed);
        initialise_item_descriptions();
        vector<uint32_t> saved;
        for (int type = 0; type < NUM_SCROLLS; ++type)
            saved.push_back(you.item_description[IDESC_SCROLLS][type]);
        const auto state = rng::current_generator().get_state();
        const auto count = rng::current_generator().get_count();
        set<string> appearances;
        for (uint32_t label : saved)
        {
            const string display = translated_scroll_appearance(label);
            REQUIRE_FALSE(display.empty());
            CHECK(appearances.insert(display).second);
            CHECK(translated_scroll_appearance(label) == display);
        }
        for (int type = 0; type < NUM_SCROLLS; ++type)
            CHECK(you.item_description[IDESC_SCROLLS][type] == saved[type]);
        CHECK(rng::current_generator().get_state() == state);
        CHECK(rng::current_generator().get_count() == count);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Neutral singular actors retain gender across display languages",
                 "[zh-translation][neutral-singular]")
{
    init_monsters();
    const char * const chinese[] = { "他", "他的", "他自己", "他" };
    const char * const english[] = { "they", "their", "themself", "them" };
    for (monster_type type : {MONS_ROBIN, MONS_ANCESTOR})
    {
        monster mon;
        mon.type = type;
        monster_info info(type);
        if (type == MONS_ANCESTOR)
        {
            mon.props[MON_GENDER_KEY] = GENDER_NEUTRAL;
            info.props[MON_GENDER_KEY] = GENDER_NEUTRAL;
        }
        else
            REQUIRE(mons_class_gender(type) == GENDER_NEUTRAL);
        for (int p = 0; p < NUM_PRONOUN_CASES; ++p)
        {
            const auto pro = static_cast<pronoun_type>(p);
            CHECK(mon.pronoun(pro, true) == chinese[p]);
            CHECK(string(info.pronoun(pro)) == chinese[p]);
            ScopedLangEn canonical;
            CHECK(mon.pronoun(pro, true) == english[p]);
            CHECK(string(info.pronoun(pro)) == english[p]);
        }
        if (type == MONS_ANCESTOR)
        {
            CHECK(mon.props[MON_GENDER_KEY].get_int() == GENDER_NEUTRAL);
            CHECK(info.props[MON_GENDER_KEY].get_int() == GENDER_NEUTRAL);
        }
    }
}

TEST_CASE("legacy dynamic display: jewellery materials and potion colours stay distinct",
          "[zh-translation][legacy-rereview][jewellery-appearance]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH, lang_t::EN);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    struct appearance
    {
        int amulet_index;
        int ring_index;
        const char* english;
        const char* material;
        potion_description_colour_type potion_colour;
        const char* colour;
    };
    const appearance variants[] = {
        {0, 23, "sapphire", "蓝宝石", PDC_SAPPHIRE, "蓝宝石色"},
        {3, 17, "emerald", "祖母绿", PDC_EMERALD, "祖母绿色"},
        {8, 10, "ruby", "红宝石", PDC_RUBY, "红宝石色"},
        {14, -1, "amethyst", "紫水晶", PDC_AMETHYST, "紫晶色"},
        {1, -1, "zirconium", "锆", PDC_NCOLOURS, ""},
    };
    for (const auto& variant : variants)
    {
        CAPTURE(variant.english);
        for (bool amulet : {true, false})
        {
            const int index = amulet ? variant.amulet_index : variant.ring_index;
            if (index < 0)
                continue;
            item_def jewel;
            jewel.base_type = OBJ_JEWELLERY;
            jewel.sub_type = amulet ? AMU_REFLECTION : RING_PROTECTION;
            jewel.quantity = 1;
            jewel.rnd = 1;
            jewel.subtype_rnd = index;
            const string expected = language == lang_t::ZH
                ? string(amulet ? "凹陷的" : "") + variant.material
                    + (amulet ? "项链" : "戒指")
                : string(amulet ? "dented " : "") + variant.english
                    + (amulet ? " amulet" : " ring");
            CHECK(jewel.name(DESC_PLAIN) == expected);
            CHECK(jewel.subtype_rnd == index);
            CHECK(jewel.sub_type == (amulet ? AMU_REFLECTION : RING_PROTECTION));
            ScopedLangEn english;
            CHECK(jewel.name(DESC_DBNAME, false, true)
                  == (amulet ? "amulet of reflection" : "ring of protection"));
        }
        if (variant.potion_colour == PDC_NCOLOURS)
            continue;
        item_def potion;
        potion.base_type = OBJ_POTIONS;
        potion.sub_type = POT_MUTATION;
        potion.quantity = 1;
        potion.rnd = 1;
        potion.subtype_rnd = PDESCQ(PDQ_NONE, variant.potion_colour);
        CHECK(potion.name(DESC_PLAIN) == (language == lang_t::ZH
              ? string(variant.colour) + "药水" : string(variant.english) + " potion"));
        CHECK(potion.subtype_rnd == PDESCQ(PDQ_NONE, variant.potion_colour));
    }
    // Unambiguous appearance adjectives keep the existing unqualified fallback.
    item_def jewel;
    jewel.base_type = OBJ_JEWELLERY;
    jewel.sub_type = RING_PROTECTION;
    jewel.quantity = jewel.rnd = 1;
    jewel.subtype_rnd = 0;
    CHECK(jewel.name(DESC_PLAIN) == (language == lang_t::ZH ? "木戒指" : "wooden ring"));
}


TEST_CASE("legacy dynamic display: gem identity survives localized names and notes",
          "[zh-translation][legacy-rereview][gem-appearance]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH, lang_t::EN);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    unwind_var<game_type> mode(crawl_state.type, GAME_TYPE_NORMAL);
    unwind_var<bool> show_clock(Options.more_gem_info, true);
    struct gem_appearance
    {
        gem_type type;
        const char* english;
        const char* chinese;
    };
    const gem_appearance gems[] = {
        {GEM_DUNGEON, "smoky", "含烟"},
#if TAG_MAJOR_VERSION == 34
        {GEM_ORC, "glittering", "闪亮"},
#endif
        {GEM_ELF, "shimmering", "流光"},
        {GEM_LAIR, "earthy", "土色"},
        {GEM_SWAMP, "mossy", "覆苔"},
        {GEM_SHOALS, "azure", "湛蓝"},
        {GEM_SNAKE, "jade", "翠玉"},
        {GEM_SPIDER, "milky-white", "乳白"},
        {GEM_SLIME, "starry", "星辉"},
        {GEM_VAULTS, "shining", "闪耀"},
        {GEM_CRYPT, "ivory", "象牙色"},
        {GEM_TOMB, "sanguine", "血红"},
        {GEM_DEPTHS, "midnight", "午夜"},
        {GEM_ZOT, "prismatic", "虹彩"},
    };
    REQUIRE(ARRAYSZ(gems) == NUM_GEM_TYPES);
    for (const auto& gem : gems)
    {
        CAPTURE(gem.english);
        const string adjective = language == lang_t::ZH ? gem.chinese : gem.english;
        const string display = adjective + (language == lang_t::ZH ? "宝石" : " gem");
        item_def item;
        item.base_type = OBJ_GEMS;
        item.sub_type = gem.type;
        item.quantity = 1;
        CHECK(item.name(DESC_PLAIN) == display);
        CHECK(string(gem_adj(gem.type)) == gem.english);
        CHECK(item.sub_type == gem.type);
        Note note(NOTE_GEM_LOST, gem.type);
        CHECK(note.describe(false, false).find(display) != string::npos);
        CHECK(note.first == gem.type);
        CHECK(note.name.empty());
        CHECK(note.desc.empty());
        {
            ScopedLangEn canonical;
            CHECK(item.name(DESC_DBNAME, false, true) == string(gem.english) + " gem");
            CHECK(note.describe(false, false).find(string(gem.english) + " gem") != string::npos);
        }
        you.gems_found.set(gem.type);
        const int limit = gem_time_limit(gem.type);
        for (int threshold : {2700, 1000})
        {
            you.gem_time_spent[gem.type] = limit - threshold;
            clear_messages(true);
            print_gem_warnings(gem.type, limit - threshold - 1);
            CHECK(get_last_messages(1, true).find(display) != string::npos);
            CHECK(string(gem_adj(gem.type)) == gem.english);
        }
    }
}

TEST_CASE("legacy dynamic display: saved professions and species preserve xlog identities",
          "[zh-translation][legacy-rereview][old-professions]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH, lang_t::EN);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    vector<pair<string, string>> identities;
    for (const char* job : {"Thief", "Death Knight", "Paladin", "Reaver", "Stalker",
                            "Jester", "Priest", "Healer", "Skald"})
    {
        identities.emplace_back("Human", job);
    }
    for (const char* race : {"Elf", "Hill Dwarf", "Ogre-Mage", "Grey Elf", "Gnome",
                             "Mountain Dwarf", "Sludge Elf", "Djinni", "Lava Orc"})
    {
        identities.emplace_back(race, "Fighter");
    }
    // Same-name current entities deliberately use the parser's existing first
    // match. Do not manufacture private negative enum fields to bypass it.
    for (const auto& identity : identities)
    {
        const string& race = identity.first;
        const string& job = identity.second;
        CAPTURE(race, job);
        const string raw = "v=0.15:name=Legacy:race=" + race + ":cls=" + job
            + ":xl=1:sk=Fighting:title=Adventurer:br=D:lvl=1:god=No God:"
              "ktyp=quitting:start=20140001000000S:end=20140001010000S";
        scorefile_entry saved;
        REQUIRE(saved.parse(raw));
        const string display_job = T_(job.c_str());
        const string display_race = T_(race.c_str());
        if (language == lang_t::ZH)
        {
            REQUIRE(display_job != job);
            REQUIRE(display_race != race);
        }
        for (auto verbosity : {scorefile_entry::DDV_NORMAL, scorefile_entry::DDV_VERBOSE})
        {
            const string output = saved.character_description(verbosity);
            INFO(output);
            CHECK(output.find(display_job) != string::npos);
            CHECK(output.find(display_race) != string::npos);
            if (language == lang_t::ZH)
            {
                CHECK(output.find(job) == string::npos);
                CHECK(output.find(race) == string::npos);
            }
        }
        CHECK(saved.get_fields().str_field("cls") == job);
        CHECK(saved.get_fields().str_field("race") == race);
        CHECK(saved.raw_string() == raw);
        {
            ScopedLangEn canonical;
            const string output = saved.character_description(scorefile_entry::DDV_VERBOSE);
            CHECK(output.find(job) != string::npos);
            CHECK(output.find(race) != string::npos);
        }
        CHECK(Options.language == language);
    }
}

TEST_CASE("legacy dynamic display: real automagic script formats messages after lookup",
          "[zh-translation][legacy-rereview][automagic]")
{
    init_dungeon_lua();
    std::ifstream input(datafile_path("clua/automagic.lua"));
    REQUIRE(input.good());
    std::ostringstream contents;
    contents << input.rdbuf();
    const string source = contents.str();
    REQUIRE(source.find("]====]") == string::npos);
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        // Execute the production script in a private environment. Translation
        // stays real; input, terminal output and game-state bindings are stubs.
        const string script = R"lua(
local spoken, options, commands = {}, {}, {}
local spellbook = {a="Magic Dart"}
local mana, key = 0, string.byte("a")
local foe = {
    name=function() return "orc" end,
    attitude=function() return 0 end,
    is_firewood=function() return false end,
    is_safe=function() return false end,
    is_constricting_you=function() return false end,
    damage_level=function() return 0 end,
    threat=function() return 1 end,
}
local env = setmetatable({
    AUTOMAGIC_SPELL_SLOT="a", AUTOMAGIC_ACTIVE=true,
    chk_lua_save={}, chk_lua_option={},
    af_hp_is_low=function() return false end,
    af_mp_is_low=function() return false end,
    crawl=setmetatable({
        mpr=function(text) spoken[#spoken+1]=text end,
        getch=function() return key end,
        clear_messages=function() end,
        setopt=function(text) options[#options+1]=text end,
        process_keys=function(text) commands[#commands+1]=text end,
    }, {__index=crawl}),
    you={
        race=function() return "Human" end,
        hp=function() return 100 end,
        mp=function() return mana end,
        confused=function() return false end,
        los=function() return 1 end,
        spell_table=function() return spellbook end,
    },
    monster={get_monster_at=function(x,y)
        if x==1 and y==0 then return foe end
    end},
    spells={
        range=function(name) assert(name=="Magic Dart"); return 1 end,
        mana_cost=function(name) assert(name=="Magic Dart"); return 1 end,
    },
}, {__index=_G})
local chunk = assert(load([====[
)lua" + source + R"lua(
]====], "automagic real consumer", "t", env))
chunk()
local function expected(template, ...)
    local translated = crawl.t_(template)
    if crawl.language()=="zh" then assert(translated~=template) end
    return string.format(translated, ...)
end
env.mag_attack(false)
assert(spoken[#spoken]==expected("You don't have enough magic to cast %s!",
                                 crawl.t_("Magic Dart")))
assert(spellbook.a=="Magic Dart" and #commands==0)
mana=100
env.mag_attack(false)
assert(commands[1]=="zarlf", "translated or changed spell command")
for _, active in ipairs({true,false}) do
    for _, slot in ipairs({"a","b"}) do
        env.AUTOMAGIC_ACTIVE=active
        key=string.byte(slot)
        local before=#options
        env.am_set_spell()
        assert(env.AUTOMAGIC_SPELL_SLOT==slot)
        local template=active and "Automagic will cast spell in slot %s (%s)."
            or "Automagic enabled, will cast spell in slot %s (%s)."
        assert(spoken[#spoken]==expected(template, slot,
            crawl.t_(spellbook[slot] or "no spell currently")))
        if active then assert(#options==before)
        else assert(options[#options]=="automagic_enable = true") end
        assert(env.chk_lua_save[1]()=="AUTOMAGIC_SPELL_SLOT = '"..slot.."'\n")
    end
end
key=13
env.am_set_spell()
assert(options[#options]=="automagic_enable = false")
assert(spoken[#spoken]==crawl.t_("Deactivated automagic."))
local before=#options
key=27
env.am_set_spell()
assert(spoken[#spoken]==crawl.t_("Cancelled.") and #options==before)
key=string.byte("1")
env.am_set_spell()
assert(spoken[#spoken]==crawl.t_("Invalid spell slot.") and #options==before)
assert(spellbook.a=="Magic Dart" and spellbook.b==nil)
)lua";
        const int result = dlua.execstring(script.c_str(), "automagic real consumer regression");
        INFO(dlua.error);
        REQUIRE(result == 0);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "interface rereview: actual item quantities use complete Chinese numeric groups and whole-digit fallback",
                 "[zh-translation][interface-rereview][number-word-consumer]")
{
    item_def item;
    item.base_type = OBJ_MISSILES;
    item.sub_type = MI_STONE;
    item.flags = ISFLAG_IDENTIFIED;
    for (const auto& count : {std::make_pair(110, "一百一十"),
                              std::make_pair(111, "一百一十一"),
                              std::make_pair(1010, "一千零一十"),
                              std::make_pair(10000, "10000")})
    {
        item.quantity = count.first;
        CHECK(item.name(DESC_PLAIN, false, true, false, true).find(
                  string(count.second) + " ") == 0);
        {
            ScopedLangEn canonical;
            CHECK(item.name(DESC_PLAIN, false, true, false, true).find(
                      number_in_words_en(count.first) + " ") == 0);
        }
        CHECK(item.quantity == count.first);
    }
}
