// Reproducible production samples for the bounded Chinese randart naming review.
#include "AppHdr.h"
#include "catch_amalgamated.hpp"
#include "test_zh_fixture.h"

#include <fstream>
#include <clocale>
#include "english.h"
#include <cstdio>
#include <cstdlib>
#include <vector>
#include "artefact.h"
#include "database.h"
#include "item-prop.h"
#include "item-status-flag-type.h"
#include "items.h"
#include "options.h"
#include "player.h"
#include "random.h"
#include "randbook.h"
#include "mon-util.h"
#include "spl-util.h"
#include "spl-book.h"
#include "unwind.h"
#include "stringutil.h"
#include "syscalls.h"
#include "god-type.h"
#include "unicode.h"

namespace {
struct RandartNameLocale
{
    string saved = setlocale(LC_CTYPE, nullptr);
    RandartNameLocale()
    {
#if defined(UNIX) && !defined(__ANDROID__)
        REQUIRE(ensure_utf8_ctype());
#endif
        REQUIRE(strwidth("中文") == 4);
    }
    ~RandartNameLocale() { setlocale(LC_CTYPE, saved.c_str()); }
};

// Escape control characters so malformed library entries cannot split records.
static string sample_field(string value)
{
    value = replace_all(value, "\\", "\\\\");
    value = replace_all(value, "\t", "\\t");
    value = replace_all(value, "\n", "\\n");
    return replace_all(value, "\r", "\\r");
}

struct Spec { object_class_type cls; int sub; };

static void dump(FILE* f, const char* cat, const vector<Spec>& specs, int count,
                 uint32_t base_seed, int god, rng::PcgRNG& streams)
{
    for (int i = 0; i < count; ++i)
    {
        const Spec& s = specs[i % specs.size()];
        const uint32_t seed = base_seed + i;
        rng::subgenerator det(seed, streams.get_uint64());
        item_def item;
        item.base_type = s.cls;
        item.sub_type = s.sub;
        item.quantity = 1;
        if (god)
            item.orig_monnum = -god;
        REQUIRE(make_item_randart(item, true));
        const uint64_t next_rng = rng::peek_uint64();
        artefact_properties_t properties;
        artefact_properties(item, properties);
        string property_text;
        for (int p = 0; p < ART_PROPERTIES; ++p)
            property_text += make_stringf("%d,", properties[p]);
        item.flags |= ISFLAG_IDENTIFIED;
        const string stored = item.props.exists(ARTEFACT_NAME_KEY)
            ? item.props[ARTEFACT_NAME_KEY].get_string() : "";
        const string idn = item.name(DESC_PLAIN, false, true);
        item.flags &= ~ISFLAG_IDENTIFIED;
        const string unid = item.name(DESC_PLAIN, false, false);
        fprintf(f, "%s\t%u\t%d\t%d\t%s\t%d\t%s\t%s\n", cat, seed,
                (int)s.cls, s.sub, sample_field(stored).c_str(), strwidth(idn),
                sample_field(idn).c_str(), sample_field(unid).c_str());
        fprintf(f, "META\t%u\t%llu\t%s\t%s\n", seed,
                static_cast<unsigned long long>(next_rng),
                property_text.c_str(),
                sample_field(item.props[ARTEFACT_APPEAR_KEY].get_string()).c_str());
    }
}
}

TEST_CASE("randart naming sample dump", "[.randart-names-dump]")
{
    RandartNameLocale locale;
    const char* out = getenv("RANDART_DUMP_OUT");
    REQUIRE(out);
    const char* langenv = getenv("RANDART_DUMP_LANG");
    const bool zh = !langenv || string(langenv) == "zh";
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.species = SP_HUMAN;
    you.your_name = zh ? "小明" : "Mingo";
    you.game_seed = 20261115ULL;
    TranslationFixture tr(zh ? lang_t::ZH : lang_t::EN, zh ? "zh" : nullptr);
    FILE* f = fopen(out, "w");
    REQUIRE(f);
    fprintf(f, "category\tseed\tbase_type\tsub_type\tstored_name\tstrwidth_identified\tidentified_display\tunidentified_display\n");

    vector<Spec> weapons = {
        {OBJ_WEAPONS, WPN_LONG_SWORD}, {OBJ_WEAPONS, WPN_DAGGER},
        {OBJ_WEAPONS, WPN_BATTLEAXE}, {OBJ_WEAPONS, WPN_SPEAR},
        {OBJ_WEAPONS, WPN_MACE}, {OBJ_WEAPONS, WPN_SHORTBOW},
        {OBJ_WEAPONS, WPN_EXECUTIONERS_AXE}, {OBJ_WEAPONS, WPN_QUARTERSTAFF},
        {OBJ_WEAPONS, WPN_SCIMITAR}, {OBJ_WEAPONS, WPN_HAND_CANNON},
        {OBJ_WEAPONS, WPN_GIANT_SPIKED_CLUB}, {OBJ_WEAPONS, WPN_TRIPLE_CROSSBOW},
        {OBJ_WEAPONS, WPN_RAPIER}, {OBJ_WEAPONS, WPN_GLAIVE},
        {OBJ_WEAPONS, WPN_WHIP}, {OBJ_WEAPONS, WPN_DOUBLE_SWORD},
    };
    vector<Spec> armour = {
        {OBJ_ARMOUR, ARM_ROBE}, {OBJ_ARMOUR, ARM_LEATHER_ARMOUR},
        {OBJ_ARMOUR, ARM_SCALE_MAIL}, {OBJ_ARMOUR, ARM_PLATE_ARMOUR},
        {OBJ_ARMOUR, ARM_KITE_SHIELD}, {OBJ_ARMOUR, ARM_BUCKLER},
        {OBJ_ARMOUR, ARM_HELMET}, {OBJ_ARMOUR, ARM_HAT},
        {OBJ_ARMOUR, ARM_CLOAK}, {OBJ_ARMOUR, ARM_GLOVES},
        {OBJ_ARMOUR, ARM_BOOTS}, {OBJ_ARMOUR, ARM_FIRE_DRAGON_ARMOUR},
        {OBJ_ARMOUR, ARM_TOWER_SHIELD}, {OBJ_ARMOUR, ARM_SCARF},
    };
    vector<Spec> rings = {
        {OBJ_JEWELLERY, RING_PROTECTION}, {OBJ_JEWELLERY, RING_EVASION},
        {OBJ_JEWELLERY, RING_STRENGTH}, {OBJ_JEWELLERY, RING_INTELLIGENCE},
        {OBJ_JEWELLERY, RING_SLAYING}, {OBJ_JEWELLERY, RING_FIRE},
        {OBJ_JEWELLERY, RING_ICE}, {OBJ_JEWELLERY, RING_POSITIVE_ENERGY},
        {OBJ_JEWELLERY, RING_WIZARDRY}, {OBJ_JEWELLERY, RING_SEE_INVISIBLE},
    };
    vector<Spec> amulets = {
        {OBJ_JEWELLERY, AMU_REGENERATION}, {OBJ_JEWELLERY, AMU_REFLECTION},
        {OBJ_JEWELLERY, AMU_MANA_REGENERATION}, {OBJ_JEWELLERY, AMU_ACROBAT},
        {OBJ_JEWELLERY, AMU_GUARDIAN_SPIRIT}, {OBJ_JEWELLERY, AMU_FAITH},
    };
    // Reproduce a fresh process's default PCG stream explicitly, independent
    // of other tests. Each item receives one successive sequence identifier.
    rng::PcgRNG streams;
    const int N = 300;
    dump(f, "weapon", weapons, N, 1000000, 0, streams);
    dump(f, "armour", armour, N, 2000000, 0, streams);
    dump(f, "ring", rings, N, 3000000, 0, streams);
    dump(f, "amulet", amulets, N, 4000000, 0, streams);
    dump(f, "gift-trog-weapon", weapons, 60, 5000000, GOD_TROG, streams);
    dump(f, "gift-okawaru-armour", armour, 60, 6000000, GOD_OKAWARU, streams);
    dump(f, "gift-xom-ring", rings, 60, 7000000, GOD_XOM, streams);
    fclose(f);
}

TEST_CASE("randart names: scoped grammar survives production generation",
          "[zh-translation][randart-names]")
{
    RandartNameLocale locale;
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.species = SP_HUMAN;
    you.your_name = "小明";
    you.game_seed = 20261115ULL;
    const lang_t language = GENERATE(lang_t::ZH, lang_t::EN);
    TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
    const bool zh = language == lang_t::ZH;
    for (const Spec spec : {Spec{OBJ_WEAPONS, WPN_LONG_SWORD},
                            Spec{OBJ_ARMOUR, ARM_ROBE},
                            Spec{OBJ_JEWELLERY, RING_PROTECTION},
                            Spec{OBJ_JEWELLERY, AMU_REGENERATION}})
    {
        for (uint32_t seed = 2000100; seed < 2000132; ++seed)
        {
            rng::subgenerator fixed(seed, 0x72616e64617274ULL);
            item_def item;
            item.base_type = spec.cls;
            item.sub_type = spec.sub;
            item.quantity = 1;
            REQUIRE(make_item_randart(item, true));
            const string saved = item.props[ARTEFACT_NAME_KEY].get_string();
            const string appearance = item.props[ARTEFACT_APPEAR_KEY].get_string();
            CAPTURE(language, seed, saved, appearance);
            // English retains its pre-existing library behaviour.
            if (zh)
                CHECK(saved.find('\n') == string::npos);
            CHECK(saved.find('@') == string::npos);
            CHECK(saved.find("的的") == string::npos);
            CHECK(appearance.find('\n') == string::npos);
            if (zh && spec.cls == OBJ_JEWELLERY)
            {
                CHECK(appearance.find(' ') == string::npos);
                CHECK(appearance.find("的的") == string::npos);
            }
            item.flags &= ~ISFLAG_IDENTIFIED;
            const string unidentified = item.name(DESC_PLAIN);
            CHECK(unidentified.find(saved) == string::npos);
            CHECK(unidentified.find("「") == string::npos);
            // True-name/attribute mutations must not reveal themselves through
            // the already generated, independently stored appearance.
            item.props[ARTEFACT_NAME_KEY] = "HIDDEN_TRUE_NAME";
            artefact_set_property(item, ARTP_STRENGTH, 12);
            CHECK(item.name(DESC_PLAIN) == unidentified);
            item.props[ARTEFACT_NAME_KEY] = saved;
            item.flags |= ISFLAG_IDENTIFIED;
            const string display = item.name(DESC_PLAIN);
            CHECK(display.find("HIDDEN_TRUE_NAME") == string::npos);
            CHECK(zh == (display.find("「") != string::npos));
            // The 25-cell motif cap does not include the base type, enchantment,
            // intrinsic quote conversion or outer display quotes. Check the
            // complete name's measured width against its undecorated counterpart.
            if (zh)
                CHECK(strwidth(display) >= strwidth(saved));
            // Existing generated names and appearances are not regenerated.
            CHECK(make_item_randart(item, true));
            CHECK(item.props[ARTEFACT_NAME_KEY].get_string() == saved);
            CHECK(item.props[ARTEFACT_APPEAR_KEY].get_string() == appearance);
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "randart names: branch and scoped library consumers",
                 "[zh-translation][randart-names]")
{
    RandartNameLocale locale;
    init_properties();
    item_def item;
    item.base_type = OBJ_WEAPONS;
    item.sub_type = WPN_LONG_SWORD;
    item.quantity = 1;
    const pair<const char*, const char*> branches[] = {
        {"the Dwarven Hall", "矮人大厅"},
        {"the Hall of Blades", "刀锋殿堂"},
        {"the Enchanted Forest", "附魔森林"},
        {"the Arena", "竞技场"},
    };
    for (const auto& branch : branches)
        CHECK(string(T_(branch.first)) == branch.second);
    for (uint32_t seed = 0; seed < 128; ++seed)
    {
        rng::subgenerator fixed(seed, 0x72616e64617274ULL);
        const string branch = replace_name_parts("@branch_name@", item);
        CAPTURE(seed, branch);
        CHECK(branch.find('@') == string::npos);
        CHECK(branch.find("the ") == string::npos);
        const string quantity = getRandNameString("_randart_quantity_motif_");
        const string predicate = getRandNameString("_randart_predicate_");
        CHECK_FALSE(quantity.empty());
        CHECK(quantity.find('@') == string::npos);
        CHECK(quantity.find("的的") == string::npos);
        CHECK_FALSE(predicate.empty());
        CHECK(predicate.find('@') == string::npos);
    }
    // Raw intrinsic quotes stay in the generated identity. Their conversion
    // to display markers belongs to item::name, never to name storage.
    rng::subgenerator fixed(0x1234, 0x72616e64617274ULL);
    REQUIRE(make_item_randart(item, true));
    const string raw = "「测试名字」长剑";
    item.props[ARTEFACT_NAME_KEY] = raw;
    item.flags |= ISFLAG_IDENTIFIED;
    CHECK(item.name(DESC_PLAIN).find("「测试名字」长剑") != string::npos);
    CHECK(item.props[ARTEFACT_NAME_KEY].get_string() == raw);
    unwind_var<string> long_name(you.your_name,
        "非常非常非常非常长的角色名字");
    const string long_identity = replace_name_parts("@player_doom@", item);
    CHECK(long_identity.find(you.your_name) != string::npos);
    CHECK(long_identity.find(' ') == string::npos);
    CHECK(long_identity.find('@') == string::npos);
    for (uint64_t seed = 1; seed <= 16; ++seed)
    {
        rng::subgenerator sequence(seed, 0x10a6);
        item_def generated;
        generated.base_type = OBJ_WEAPONS;
        generated.sub_type = WPN_LONG_SWORD;
        generated.quantity = 1;
        REQUIRE(make_item_randart(generated, true));
        const string raw = generated.props[ARTEFACT_NAME_KEY].get_string();
        // The actual generator retries an overlong motif rather than cutting
        // the player name or the UTF-8 string in the saved result.
        CHECK(strwidth(raw) <= 25 + strwidth(T_("long sword")));
        CHECK(raw.find('@') == string::npos);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "randart names: reported grammar examples use real generation",
                 "[zh-translation][randart-names]")
{
    RandartNameLocale locale;
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.species = SP_HUMAN;
    you.your_name = "小明";
    you.game_seed = 20261115ULL;
    struct Example
    {
        uint32_t seed;
        object_class_type cls;
        int subtype;
        const char* expected;
    };
    const Example examples[] = {
        {2000038, OBJ_ARMOUR, ARM_BOOTS, "一百头野兽之靴子"},
        {2000066, OBJ_ARMOUR, ARM_BOOTS, "百万份最后通牒之靴子"},
        {3000127, OBJ_JEWELLERY, RING_POSITIVE_ENERGY, "知名的青年之戒指"},
        {1000059, OBJ_WEAPONS, WPN_TRIPLE_CROSSBOW, "正在进食的蝎子之三弦弩"},
        {2000126, OBJ_ARMOUR, ARM_ROBE, "装饰华丽的水手长袍"},
    };
    for (const auto& example : examples)
    {
        const unsigned offset = example.seed / 1000000 == 1 ? 0
                                : example.seed / 1000000 == 2 ? 300 : 600;
        rng::PcgRNG streams;
        uint64_t sequence = 0;
        for (unsigned i = 0; i <= offset + example.seed % 1000000; ++i)
            sequence = streams.get_uint64();
        rng::subgenerator fixed(example.seed, sequence);
        item_def item;
        item.base_type = example.cls;
        item.sub_type = example.subtype;
        item.quantity = 1;
        REQUIRE(make_item_randart(item, true));
        CAPTURE(example.seed);
        CHECK(item.props[ARTEFACT_NAME_KEY].get_string() == example.expected);
    }
    rng::PcgRNG streams;
    uint64_t sequence = 0;
    for (unsigned i = 0; i <= 600; ++i)
        sequence = streams.get_uint64();
    rng::subgenerator fixed(3000000, sequence);
    item_def ring;
    ring.base_type = OBJ_JEWELLERY;
    ring.sub_type = RING_PROTECTION;
    ring.quantity = 1;
    REQUIRE(make_item_randart(ring, true));
    CHECK(ring.props[ARTEFACT_APPEAR_KEY].get_string() == "精良的青金石戒指");
    CHECK(ring.name(DESC_PLAIN) == "精良的青金石戒指");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "randart names: genitive branch motifs use intrinsic quotes",
                 "[zh-translation][randart-names]")
{
    RandartNameLocale locale;
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    you.species = SP_HUMAN;
    you.your_name = "小明";
    you.game_seed = 20261115ULL;
    const pair<uint64_t, const char*> examples[] = {
        {370, "盐之荒原"}, {5633, "百兽之巢"}, {7521, "史莱姆之坑"},
    };
    for (const auto& example : examples)
    {
        rng::subgenerator sequence(example.first, 0x4231);
        item_def item;
        item.base_type = OBJ_WEAPONS;
        item.sub_type = WPN_LONG_SWORD;
        item.quantity = 1;
        REQUIRE(make_item_randart(item, true));
        const string place = example.second;
        const string raw = item.props[ARTEFACT_NAME_KEY].get_string();
        CAPTURE(example.first, raw);
        CHECK(raw == "「" + place + "」长剑");
        item.flags |= ISFLAG_IDENTIFIED;
        CHECK(item.name(DESC_PLAIN).find("「" + place + "」长剑") != string::npos);
        CHECK(item.props[ARTEFACT_NAME_KEY].get_string() == raw);
    }
}

TEST_CASE("replay frozen randart display names", "[.artefact-name-replay]")
{
    RandartNameLocale locale;
    const char *input_path = getenv("ARTEFACT_REPLAY_INPUT");
    const char *output_path = getenv("ARTEFACT_REPLAY_OUTPUT");
    REQUIRE(input_path);
    REQUIRE(output_path);
    ifstream input(input_path);
    REQUIRE(input.good());
    FILE *output = fopen(output_path, "w");
    REQUIRE(output);
    unwinder close_output([&]() { fclose(output); });
    init_properties();
    unwind_var<player> restore_player(you);
    you = player();
    const char *language = getenv("ARTEFACT_REPLAY_LANGUAGE");
    const bool zh = !language || string(language) != "en";
    TranslationFixture mode(zh ? lang_t::ZH : lang_t::EN, zh ? "zh" : nullptr);
    string line;
    REQUIRE(static_cast<bool>(getline(input, line)));
    fprintf(output, "seed\tcore_before_width\tcore_after_width\tprefix_width\tproperties_width\tfull_before_width\tfull_after_width\tbefore\tafter\n");
    int count = 0;
    while (getline(input, line))
    {
        const auto fields = split_string("\t", line, false);
        REQUIRE(fields.size() == 8);
        REQUIRE(static_cast<bool>(getline(input, line)));
        const auto meta = split_string("\t", line, false);
        REQUIRE(meta.size() == 5);
        REQUIRE(meta[0] == "META");
        item_def item;
        item.base_type = static_cast<object_class_type>(atoi(fields[2].c_str()));
        item.sub_type = atoi(fields[3].c_str());
        item.quantity = 1;
        item.rnd = 1;
        item.flags = ISFLAG_IDENTIFIED;
        REQUIRE(make_item_randart(item, true));
        item.props[ARTEFACT_NAME_KEY].get_string() = fields[4];
        const auto properties = split_string(",", meta[3], true, false);
        REQUIRE(properties.size() == ART_PROPERTIES);
        for (int i = 0; i < ART_PROPERTIES; ++i)
        {
            artefact_set_property(item, static_cast<artefact_prop_type>(i),
                                  atoi(properties[i].c_str()));
        }
        const string core = get_artefact_name(item, true);
        const string without_properties = item.name(DESC_PLAIN, false, true, false);
        const string full = item.name(DESC_PLAIN, false, true);
        if (!zh)
            CHECK(full == fields[6]);
        const int core_before = strwidth(quote_special_name(core));
        const int core_after = strwidth(quote_artefact_name(core));
        const int prefix = strwidth(without_properties) - core_after;
        const int props = strwidth(full) - strwidth(without_properties);
        fprintf(output, "%s\t%d\t%d\t%d\t%d\t%s\t%d\t%s\t%s\n",
                fields[1].c_str(), core_before, core_after, prefix, props,
                fields[5].c_str(), strwidth(full), fields[6].c_str(),
                sample_field(full).c_str());
        ++count;
    }
    CHECK(count == 1380);
}

// Use the real themed-book constructor for both review evidence and regressions.
static void r54_theme_books(FILE *output, bool check_chinese)
{
    RandartNameLocale locale;
    init_properties();
    init_spell_descs();
    unwind_var<player> restore_player(you);
    you = player();
    you.species = SP_HUMAN;
    you.experience_level = 27;
    you.your_name = "Mingo";
    for (int god : {GOD_NO_GOD, GOD_SIF_MUNA, GOD_XOM})
        for (int level = 1; level <= 9; ++level)
            for (int seed = 0; seed < 16; ++seed)
            {
                rng::subgenerator fixed(seed, 0x54b00c);
                item_def book;
                book.base_type = OBJ_BOOKS;
                book.quantity = 1;
                book.orig_monnum = -god;
                build_themed_book(book, capped_spell_filter(level * 3));
                const string title = book.props[ARTEFACT_NAME_KEY].get_string();
                CAPTURE(god, level, seed, title);
                if (check_chinese)
                {
                    CHECK(title.find('@') == string::npos);
                    CHECK(title.find("TOO MUCH RECURSION") == string::npos);
                    CHECK(strip_cjk_spaces(title) == title);
                    // Proper names may be Latin; the title itself must be localized.
                    CHECK(std::any_of(title.begin(), title.end(),
                                      [](unsigned char c) { return c >= 128; }));
                }
                if (output)
                {
                    string spells;
                    for (spell_type spell : spells_in_book(book))
                        spells += make_stringf("%d,", static_cast<int>(spell));
                    book.flags |= ISFLAG_IDENTIFIED;
                    fprintf(output, "%d\t%d\t%d\t%s\t%llu\t%s\t%s\n",
                            god, level, seed, sample_field(title).c_str(),
                            static_cast<unsigned long long>(rng::peek_uint64()),
                            spells.c_str(), sample_field(book.name(DESC_PLAIN)).c_str());
                }
            }
}

TEST_CASE("R54 themed book production samples", "[.r54-books-dump]")
{
    const char *output = getenv("R54_BOOK_OUT");
    REQUIRE(output);
    const char *language = getenv("R54_BOOK_LANG");
    REQUIRE(language);
    const bool chinese = string(language) == "zh";
    TranslationFixture translation(chinese ? lang_t::ZH : lang_t::EN,
                                   chinese ? "zh" : nullptr);
    FILE *file = fopen(output, "w");
    REQUIRE(file);
    r54_theme_books(file, false);
    fclose(file);
}

TEST_CASE("R54 themed books resolve localized production roots",
          "[zh-translation][r54-books]")
{
    ZhTranslationFixture translation;
    r54_theme_books(nullptr, true);
}
