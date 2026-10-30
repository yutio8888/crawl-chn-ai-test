#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "database.h"
#include "directn.h"
#include "describe.h"
#include "mon-util.h"
#include "mutation.h"
#include "notes.h"
#include "ng-init.h"
#include "transform.h"
#include "english.h"
#include "item-name.h"
#include "item-prop.h"
#include "item-status-flag-type.h"
#include "lang-en-guard.h"
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
        { "它们", "它们的", "它们自己", "它们" },
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
                 "[zh-translation][issue-6][grammar]")
{
    // Freeze existing grouping, including its established 110 and 10000 forms.
    const pair<unsigned, const char *> cases[] =
    {
        { 0, "零" }, { 1, "一" }, { 9, "九" }, { 10, "十" },
        { 11, "十一" }, { 19, "十九" }, { 20, "二十" }, { 21, "二十一" },
        { 99, "九十九" }, { 100, "一百" }, { 101, "一百零一" },
        { 109, "一百零九" }, { 110, "一百十" }, { 119, "一百十九" },
        { 120, "一百二十" }, { 999, "九百九十九" }, { 1000, "一千" },
        { 1001, "一千零一" }, { 1010, "一千零十" },
        { 1100, "一千一百" }, { 9999, "九千九百九十九" }, { 10000, "十千" },
    };
    for (const auto &test : cases)
    {
        INFO("number=" << test.first);
        CHECK(number_in_words(test.first) == test.second);
        const string canonical = number_in_words_en(test.first);
        ScopedLangEn english;
        CHECK(number_in_words(test.first) == canonical);
    }
    CHECK(number_in_words_en(8) == "eight");
    CHECK(number_in_words_en(20) == "twenty");
    CHECK(number_in_words_en(101) == "one hundred and one");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 6 skin display preserves canonical anatomy",
                 "[zh-translation][issue-6][skin]")
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
        { SP_HUMAN, "skin", "fleshy", "皮肤", "皮肤的" },
        { SP_RED_DRACONIAN, "scales", "scaled", "鳞片", "鳞片的" },
        { SP_NAGA, "scales", "scaled", "鳞片", "鳞片的" },
        { SP_TENGU, "feathers", "feathered", "羽毛", "羽毛的" },
        { SP_FELID, "fur", "furry", "毛皮", "毛茸茸的" },
        { SP_MUMMY, "bandages", "bandage-wrapped", "绷带", "绷带包裹的" },
        { SP_GARGOYLE, "stone", "stony", "石头", "石质的" },
        { SP_POLTERGEIST, "ectoplasm", "ectoplasmic", "灵质", "灵质的" },
        { SP_REVENANT, "bones", "bony", "骨头", "骨质的" },
    };
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
