#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "test_zh_fixture.h"
#include "test_zh_helpers.h"

#include "i18n.h"            // T_()
#include "database.h"        // getLongDescription, getMiscString
#include "religion.h"        // _god_name_en, get_god_powers, god_power
#include "god-type.h"
#include "ability.h"        // ability_type, ability_name, get_ability_names
#include "ability-type.h"
#include "spl-util.h"       // spell_type, spell_title, spell_english_name,
                            // init_spell_descs, init_spell_name_cache
#include "spell-type.h"
#include "mon-util.h"       // mons_type_name, init_monsters
#include "monster-type.h"
#include "description-level-type.h"
#include "feature.h"         // get_feature_def
#include "dungeon-feature-type.h"
#include "cloud.h"           // cloud_type_name
#include "cloud-type.h"
#include "mutation.h"        // mutation_name
#include "mutation-type.h"
#include "terrain.h"         // init_feat_desc_cache

#include <cstring>
#include <string>
#include <vector>

namespace {

// Convenience: collect issues into a unary REQUIRE-friendly form. Each scan
// returns the issues pushed by the scan into the supplied vector; the
// enumerator TEST_CASE wraps the test with a diagnostic WARN summary.
// Per-issue samples are dumped to stderr (so M5 aggregator / log parser can
// pick them up even when the catch2 test case itself passes), and a single
// WARN line emits the per-enumerator total — this is the line the M5
// aggregator parses to compare against the per-sha baseline.
void scan_one(const char* translated, const std::string& key,
              const std::string& source_tag, std::vector<ZhIssue>& out)
{
    auto issues = scan_translation(translated, key, source_tag);
    for (auto& iss : issues)
    {
        // Machine-parseable stderr marker for M5 aggregator output parsing.
        fprintf(stderr, "ZH_ISSUE: %d | %s | %s | %s\n",
                static_cast<int>(iss.kind), iss.source.c_str(),
                iss.key.c_str(), iss.sample.c_str());
        out.push_back(std::move(iss));
    }
}

// Wrap T_(...) result scanning with the English key as the lookup target.
void scan_T_key(const char* english_key, const std::string& source_tag,
                std::vector<ZhIssue>& out)
{
    const char* tr = T_(english_key);
    scan_one(tr, english_key, source_tag, out);
}

} // anonymous namespace

// =============================================================================
// Enumerator 1 — gods: powers/wrath/extra + per-god ability gain/loss strings.
//
// Plan v2 §2.4 (#1). Bypasses describe_god(g) (void) by querying the
// public TextDB keys directly:
//   getLongDescription("<God>"             ) — main description (gods.txt)
//   getLongDescription("<God> powers"      ) — _describe_god_powers
//   getLongDescription("<God> wrath"       ) — _god_wrath_description
//   getLongDescription("<God> extra"       ) — _god_extra_description
// plus get_god_powers(g).gain / .loss strings (god-power.h), which are
// also T_() wrapped at runtime in the religion panel.
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: gods — powers/wrath/extra",
                 "[zh-translation]")
{
    std::vector<ZhIssue> issues;
    for (int gi = GOD_NO_GOD + 1; gi < NUM_GODS; ++gi)
    {
        const god_type g = static_cast<god_type>(gi);
        const std::string god = _god_name_en(g);
        if (god.empty())
            continue;

        // Main description ("Trog") and three suffix-keyed sub-descriptions
        // used by describe-god.cc.
        scan_one(getLongDescription(god).c_str(),                god,           "gods.txt",   issues);
        scan_one(getLongDescription(god + " powers").c_str(),    god + " powers",  "gods.txt",   issues);
        scan_one(getLongDescription(god + " wrath").c_str(),     god + " wrath",   "gods.txt",   issues);
        scan_one(getLongDescription(god + " extra").c_str(),     god + " extra",   "gods.txt",   issues);

        // gain/loss strings from god_power entries.
        const auto powers = get_god_powers(g);
        for (const auto& p : powers)
        {
            if (p.gain && p.gain[0])
                scan_T_key(p.gain, "god_power.gain", issues);
            if (p.loss && p.loss[0])
                scan_T_key(p.loss, "god_power.loss", issues);
        }
    }
    // Per-enumerator summary line is the M5 aggregator input. Per-issue
    // samples were already emitted to stderr via scan_one() helper.
    WARN("zh enumerator summary: gods -> " << issues.size() << " issues");
    REQUIRE(true);
}

// =============================================================================
// Enumerator 2 — god abilities (ABIL_*). ability_name(abil, true) returns the
// T_()-wrapped display name of an ability; the dbname=true path queries
// getLongDescription(name + " ability"). Plan v2 §2.4 (#2, also N4).
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: god abilities",
                 "[zh-translation]")
{
    std::vector<ZhIssue> issues;
    for (int ai = 0; ai < NUM_ABILITIES; ++ai)
    {
        const ability_type a = static_cast<ability_type>(ai);

        // dbname=true returns the English bare key (ability.cc default case);
        // dbname=false goes through T_() and returns either the translated
        // display name or the English fallback.
        const std::string en_name = ability_name(a, true);
        if (en_name.empty())
            continue;

        const std::string display = ability_name(a, false);

        // The long description lives in dat/descript/zh/ability.txt, keyed by
        // "<English basename> ability".
        const std::string key = en_name + " ability";
        const std::string tr  = getLongDescription(key);
        if (!tr.empty())
            scan_one(tr.c_str(), key, "ability.txt", issues);

        // Display name: scan its T_() result against the English baseline so
        // UNTRANSLATED only fires when T_() actually fell back to the key.
        scan_one(display.c_str(), en_name, "source.txt", issues);
    }
    // Per-enumerator summary line is the M5 aggregator input. Per-issue
    // samples were already emitted to stderr via scan_one() helper.
    WARN("zh enumerator summary: god abilities -> " << issues.size() << " issues");
    REQUIRE(true);
}

// =============================================================================
// Enumerator 6 — spells. spell_title(spell) is the canonical Type II wrapper
// (CLAUDE.md "Type II wrappers"); the description lives in
// dat/descript/zh/spells.txt, keyed by "<English spell name> spell".
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: spells",
                 "[zh-translation]")
{
    init_spell_descs();
    init_spell_name_cache();

    std::vector<ZhIssue> issues;
    for (int si = 0; si < NUM_SPELLS; ++si)
    {
        const spell_type s = static_cast<spell_type>(si);
        if (s == SPELL_NO_SPELL)
            continue;

        const char* title = spell_title(s);
        if (title && title[0])
            scan_one(title, title, "source.txt", issues);

        const char* en_name = spell_english_name(s);
        if (!en_name || !en_name[0])
            continue;
        const std::string key = std::string(en_name) + " spell";
        const std::string tr   = getLongDescription(key);
        if (!tr.empty())
            scan_one(tr.c_str(), key, "spells.txt", issues);
    }
    // Per-enumerator summary line is the M5 aggregator input. Per-issue
    // samples were already emitted to stderr via scan_one() helper.
    WARN("zh enumerator summary: spells -> " << issues.size() << " issues");
    REQUIRE(true);
}

// =============================================================================
// Enumerator 7 — monsters. mons_type_name(mc, DESC_PLAIN) is the Type II
// wrapper (mon-util.h:212); descriptions live in dat/descript/zh/monsters.txt
// keyed by English monster name. See plan v2 §2.4 (#7, suggestion S3).
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: monsters name+desc",
                 "[zh-translation]")
{
    init_monsters();

    std::vector<ZhIssue> issues;
    for (int mi = 0; mi < NUM_MONSTERS; ++mi)
    {
        const monster_type m = static_cast<monster_type>(mi);
        // No SENTINEL enum; skip ones whose name resolves to "" (e.g. enums
        // like MONS_PROGRAM_BUG that don't have a translatable name).
        const std::string name = mons_type_name(m, DESC_PLAIN);
        if (name.empty())
            continue;
        scan_one(name.c_str(), name, "source.txt", issues);

        const std::string tr = getLongDescription(name);
        if (!tr.empty())
            scan_one(tr.c_str(), name, "monsters.txt", issues);
    }
    // Per-enumerator summary line is the M5 aggregator input. Per-issue
    // samples were already emitted to stderr via scan_one() helper.
    WARN("zh enumerator summary: monsters -> " << issues.size() << " issues");
    REQUIRE(true);
}

// =============================================================================
// Enumerator 8 — features. Direct enum loop, get_feature_def(feat).name +
// T_(), bypassing feature_description_at which needs a coord_def. Plan v2
// §2.4 (#8, N2).
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: features",
                 "[zh-translation]")
{
    init_feat_desc_cache();

    std::vector<ZhIssue> issues;
    for (int fi = 0; fi < NUM_FEATURES; ++fi)
    {
        const dungeon_feature_type f = static_cast<dungeon_feature_type>(fi);
        if (!is_valid_feature_type(f))
            continue;
        const feature_def& def = get_feature_def(f);
        if (!def.name || !def.name[0])
            continue;
        scan_T_key(def.name, "features.txt", issues);
    }
    // Per-enumerator summary line is the M5 aggregator input. Per-issue
    // samples were already emitted to stderr via scan_one() helper.
    WARN("zh enumerator summary: features -> " << issues.size() << " issues");
    REQUIRE(true);
}

// =============================================================================
// Enumerator 9 — clouds. cloud_type_name(ct, false) returns the long-form
// lookup name; description is in dat/descript/zh/clouds.txt keyed by
// "<Name> cloud". Plan v2 §2.4 (#9).
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: clouds",
                 "[zh-translation]")
{
    std::vector<ZhIssue> issues;
    for (int ci = 0; ci < NUM_CLOUD_TYPES; ++ci)
    {
        const cloud_type c = static_cast<cloud_type>(ci);
        const std::string name = cloud_type_name(c, false);
        if (name.empty())
            continue;
        const std::string key = name + " cloud";
        scan_one(name.c_str(), name, "source.txt", issues);
        const std::string tr = getLongDescription(key);
        if (!tr.empty())
            scan_one(tr.c_str(), key, "clouds.txt", issues);
    }
    // Per-enumerator summary line is the M5 aggregator input. Per-issue
    // samples were already emitted to stderr via scan_one() helper.
    WARN("zh enumerator summary: clouds -> " << issues.size() << " issues");
    REQUIRE(true);
}

// =============================================================================
// Enumerator 10 — mutations. mutation_name(mut) (mutation.h:73) is the Type II
// wrapper; description in dat/descript/zh/mutations.txt keyed by "<Name>
// mutation". Plan v2 §2.4 (#10).
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: mutations",
                 "[zh-translation]")
{
    std::vector<ZhIssue> issues;
    for (int mi = 0; mi < NUM_MUTATIONS; ++mi)
    {
        const mutation_type m = static_cast<mutation_type>(mi);
        const char* name = mutation_name(m);
        if (!name || !name[0])
            continue;
        scan_one(name, name, "source.txt", issues);

        const std::string key = std::string(name) + " mutation";
        const std::string tr  = getLongDescription(key);
        if (!tr.empty())
            scan_one(tr.c_str(), key, "mutations.txt", issues);
    }
    // Per-enumerator summary line is the M5 aggregator input. Per-issue
    // samples were already emitted to stderr via scan_one() helper.
    WARN("zh enumerator summary: mutations -> " << issues.size() << " issues");
    REQUIRE(true);
}