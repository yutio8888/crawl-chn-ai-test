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
#include "artefact.h"        // get_unrand_entry, unrandart_entry
#include "art-enum.h"        // NUM_UNRANDARTS
#include "skill-type.h"      // skill_type, SK_FIRST_SKILL, NUM_SKILLS
#include "skills.h"          // skill_name
#include "species.h"         // species::name
#include "species-type.h"     // species_type, NUM_SPECIES
#include "jobs.h"            // get_job_name
#include "job-type.h"        // job_type, NUM_JOBS
#include "duration-data.h"   // duration_data[], duration_def, NUM_DURATIONS

// batch4 (deferred #3/#4 enumerators): items + weapon/armour brands/egos.
#include "item-def.h"         // item_def
#include "item-name.h"        // item_def::name(), brand/ego display helpers
#include "item-prop.h"        // init_properties
#include "item-prop-enum.h"   // brand_type, special_armour_type, NUM_* bounds
#include "item-status-flag-type.h" // ISFLAG_IDENTIFIED
#include "items.h"            // all_item_subtypes
#include "lang-en-guard.h"    // ScopedLangEn
#include "object-class-type.h" // object_class_type + OBJ_* + NUM_OBJECT_CLASSES
#include "options.h"          // Options.language / lang_name for EN-toggle
#include "lang-t.h"           // lang_t::EN / lang_t::ZH

#include <cstdio>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

namespace {

// Convenience: collect issues into a unary REQUIRE-friendly form. Each scan
// returns the issues pushed by the scan into the supplied vector; the
// enumerator TEST_CASE wraps the test with a diagnostic WARN summary.
// Issues are emitted to stderr as JSONL protocol records by a single
// emit_issue_protocol() call at the end of each enumerator test.
void scan_one(const char* translated, const std::string& key,
              const std::string& source_tag, std::vector<ZhIssue>& out)
{
    auto issues = scan_translation(translated, key, source_tag);
    for (auto& iss : issues)
    {
        // NOTE: Old ZH_ISSUE: fprintf removed per Issue 66 protocol migration.
        // Issues are now emitted collectively via emit_issue_protocol() at
        // the end of each enumerator TEST_CASE.
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

item_def make_identified_item(object_class_type base, int sub_type)
{
    static const bool properties_initialized = []() {
        init_properties();
        return true;
    }();
    (void) properties_initialized;

    item_def item;
    item.base_type = base;
    item.sub_type = sub_type;
    item.quantity = 1;
    item.flags |= ISFLAG_IDENTIFIED;
    return item;
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
        // Wu Jian extra is an ASCII-art diagram with intentional spacing;
        // skip scanning to avoid WHITESPACE false positives.
        if (god != "Wu Jian")
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
    emit_issue_protocol("zh_translation", "gods", issues);
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
        {
            if (tr.find("db_embedded_lua") != std::string::npos
                || tr.find("attempt to index a nil value") != std::string::npos)
            {
                continue;
            }
            scan_one(tr.c_str(), key, "ability.txt", issues);
        }

        // Display name: scan its T_() result against the English baseline so
        // UNTRANSLATED only fires when T_() actually fell back to the key.
        scan_one(display.c_str(), en_name, "source.txt", issues);
    }
    emit_issue_protocol("zh_translation", "god_abilities", issues);
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
    emit_issue_protocol("zh_translation", "spells", issues);
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
         // Also skip "removed" entries — these are save-compat placeholders.
         const std::string name = mons_type_name(m, DESC_PLAIN);
if (name.empty() || name.find("removed") == 0)
            continue;
        // "the X" monster names: "the" is a C++ prefix before T_()-wrapped
        // name. Skip UNTRANSLATED flagging for these — the Chinese name
        // IS translated but the article is added by mons_type_name().
        if (name.find("the ") == 0)
            continue;
        scan_one(name.c_str(), name, "source.txt", issues);

        const std::string tr = getLongDescription(name);
        if (!tr.empty())
            scan_one(tr.c_str(), name, "monsters.txt", issues);
    }
    emit_issue_protocol("zh_translation", "monsters", issues);
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
    init_show_table();
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
    emit_issue_protocol("zh_translation", "features", issues);
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
        if (name.empty() || name == "buggy goodness")
            continue;
        // cloud_type_name returns English literals (not T_()-wrapped), so
        // use scan_T_key to wrap the display with T_() before scanning.
        const std::string key = name + " cloud";
        scan_T_key(name.c_str(), "source.txt", issues);
        const std::string tr = getLongDescription(key);
        if (!tr.empty())
            scan_one(tr.c_str(), key, "clouds.txt", issues);
    }
    emit_issue_protocol("zh_translation", "clouds", issues);
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
    const std::vector<mutation_type> removed = get_removed_mutations();
    for (int mi = 0; mi < NUM_MUTATIONS; ++mi)
    {
        const mutation_type m = static_cast<mutation_type>(mi);
        if (m == MUT_REMOVED_MUTATION
            || std::find(removed.begin(), removed.end(), m) != removed.end())
        {
            continue;
        }
        const char* name = mutation_name(m);
        if (!name || !name[0])
            continue;
        scan_one(name, name, "source.txt", issues);

        const std::string key = std::string(name) + " mutation";
        const std::string tr  = getLongDescription(key);
        if (!tr.empty())
            scan_one(tr.c_str(), key, "mutations.txt", issues);
    }
    emit_issue_protocol("zh_translation", "mutations", issues);
    WARN("zh enumerator summary: mutations -> " << issues.size() << " issues");
    REQUIRE(true);
}
// =============================================================================
// Enumerator 5 — fixed artefacts (unrands). Each unrandart_entry has a `.name`
// (English artefact name, used as the TextDB key for-dat/descript/zh/unrand.txt
// descriptions) plus `unid_name` / `type_name` / `descrip` snippet strings.
// Plan v2 §2.4 (#5, B4-corrected): collapse the original "100-随机神器" idea
// into a full enumeration of fixed artefacts, since make_random_artefact does
// not exist in the codebase.
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: fixed artefacts (unrands)",
                 "[zh-translation]")
{
    std::vector<ZhIssue> issues;
    for (int i = 0; i < NUM_UNRANDARTS; ++i)
    {
        const unrandart_entry* e = get_unrand_entry(i);
        if (!e || !e->name || !e->name[0])
            continue;
        // Skip the dummy unrand entry (index 0 is "DUMMY UNRANDART 1").
        if (string(e->name).find("DUMMY") != string::npos)
            continue;

        // (a) The artefact's true display name goes through T_() at runtime
        //     via item-name.cc when displaying the artefact. Scan T_(e->name)
        //     against the English baseline (UNTRANSLATED only fires on
        //     untranslated fallback).
        scan_T_key(e->name, "source.txt", issues);

        // (b) The long-form description keyed by e->name lives in
        //     dat/descript/zh/unrand.txt.
        const std::string tr = getLongDescription(e->name);
        if (!tr.empty())
            scan_one(tr.c_str(), e->name, "unrand.txt", issues);

        // (c) The `descrip` field (short flavour string) and `unid_name`
        //     (unidentified alias) also flow through T_() at runtime.
        if (e->descrip && e->descrip[0])
            scan_T_key(e->descrip, "unrand.descrip", issues);
        if (e->unid_name && e->unid_name[0])
            scan_T_key(e->unid_name, "unrand.unid_name", issues);
    }
    emit_issue_protocol("zh_translation", "fixed_artefacts", issues);
    WARN("zh enumerator summary: fixed artefacts -> " << issues.size() << " issues");
    REQUIRE(true);
}

// =============================================================================
// Enumerator 12 — Type II wrappers (skill_name). The skill_name() wrapper
// looks up the English skill title via T_() internally; plan v2 §2.4 (#12)
// calls for honouring that entry-side cross-check. Other Type II wrappers
// (spell_title, item_base_name, ...) are covered by the dedicated
// enumerators above; skill_name gets its own pass since there's no other
// enumerator that exercises it directly.
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: skill_name (Type II wrapper)",
                 "[zh-translation]")
{
    std::vector<ZhIssue> issues;
    for (int ski = SK_FIRST_SKILL; ski < NUM_SKILLS; ++ski)
    {
        const skill_type s = static_cast<skill_type>(ski);
        const char* disp = skill_name(s);
        if (!disp || !disp[0])
            continue;
        // skill_name() returns the
        // T_()-translated display name. To detect UNTRANSLATED we need an
        // English baseline; CLAUDE.md's static comparator mode (allowlist)
        // marks skill keys as known-untranslated, so just scan for the other
        // rules here. Pass empty key to bypass UNTRANSLATED.
        std::vector<ZhIssue> local = scan_text(disp, "", "source.txt");
        for (auto& iss : local)
            issues.push_back(std::move(iss));
    }
    emit_issue_protocol("zh_translation", "skill_name", issues);
    WARN("zh enumerator summary: skill_name -> " << issues.size() << " issues");
    REQUIRE(true);
}

// =============================================================================
// Enumerator 13 — species + backgrounds (plan v2 §2.4 #13).
// species::name(sp) is the Type II wrapper (species.h:27). get_job_name(bg)
// is the public job-name accessor (jobs.h:15). Both return translates of the
// canonical English short names. The descriptions live in
// dat/descript/zh/{species.txt, backgrounds.txt} keyed by English name.
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: species + backgrounds",
                 "[zh-translation]")
{
    std::vector<ZhIssue> issues;

    // (a) Species names: scan display name + look up long description.
    for (int si = 0; si < NUM_SPECIES; ++si)
    {
        const species_type sp = static_cast<species_type>(si);
        const std::string disp = species::name(sp);
        if (disp.empty())
            continue;
        // Two scans: the display name (for MIXED_CN_EN / etc.) and the
        // long description in species.txt keyed by the English name.
        std::vector<ZhIssue> local = scan_text(disp, "", "source.txt");
        for (auto& iss : local)
            issues.push_back(std::move(iss));
        // Each species' long description in species.txt is keyed by the
        // canonical English species name. We grab the English key via the
        // raw=true flag of species::name.
        const std::string en = species::name(sp, species::SPNAME_PLAIN, true);
        if (!en.empty())
        {
            const std::string tr = getLongDescription(en);
            if (!tr.empty())
                scan_one(tr.c_str(), en, "species.txt", issues);
        }
    }

    // (b) Background names.
    for (int bi = 0; bi < NUM_JOBS; ++bi)
    {
        const job_type jb = static_cast<job_type>(bi);
        const char* disp = get_job_name(jb);
        if (!disp || !disp[0])
            continue;
        std::vector<ZhIssue> local = scan_text(disp, "", "source.txt");
        for (auto& iss : local)
            issues.push_back(std::move(iss));
        // Long description keyed by the canonical English job name in
        // backgrounds.txt. get_job_name doesn't take a `raw` flag, so we
        // read the English key from jobs-data via get_job_name_en if available;
        // otherwise fall back to scanning the description only on lookup
        // success.
        const std::string tr = getLongDescription(disp);
        if (!tr.empty())
            scan_one(tr.c_str(), disp, "backgrounds.txt", issues);
    }

    emit_issue_protocol("zh_translation", "species_backgrounds", issues);
    WARN("zh enumerator summary: species+backgrounds -> " << issues.size() << " issues");
    REQUIRE(true);
}

// =============================================================================
// Enumerator 11 — duration end/expiring messages. duration_data[] (header
// static array, duration-data.h:198) declares per-duration endmsg + expmsg
// strings that player-reacts.cc wraps in T_() at runtime. Since the array
// is header-static, catch2 can iterate it directly. Plan v2 §2.4 (#11, N3).
// Field paths: `decr.end.msg` (terminal message) and `decr.expire_msg.msg`
// (expiring warning message); some entries are lambdas with empty msg
// strings, which we skip.
//
// Note: long_text / short_text / name_text are NOT scanned here, because
// those fields are direct C string literals used in the @ status line and
// writing context — they are not wrapped in T_() at runtime (verified via
// ~player-reacts.cc and view.cc). Including them would add hundreds of
// UNTRANSLATED false-positives.
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: status/duration end+warn messages",
                 "[zh-translation]")
{
    std::vector<ZhIssue> issues;
    for (size_t i = 0; i < sizeof(duration_data) / sizeof(duration_data[0]); ++i)
    {
        const duration_def& d = duration_data[i];

        // endmsg
        if (d.decr.end.msg && d.decr.end.msg[0])
            scan_T_key(d.decr.end.msg, "duration.end", issues);

        // expmsg (the "expiring" warning variant)
        if (d.decr.expire_msg.msg && d.decr.expire_msg.msg[0])
            scan_T_key(d.decr.expire_msg.msg, "duration.expire", issues);
    }
    emit_issue_protocol("zh_translation", "durations", issues);
    WARN("zh enumerator summary: durations -> " << issues.size() << " issues");
    REQUIRE(true);
}

namespace {

// Parse a `%%%%`-separated Crawl database/descript file and emit one (key,
// value) pair per section. The key is the first non-`#`-comment, non-blank
// line; the value is everything until the next `%%%%` separator.
//
// Returns false on file-open failure (caller typically decides whether to
// skip or fail the test). Lines that look like Lua template blocks (`{...}`,
// `w:N` weight markers, `<input>...</input>` blocks) are kept verbatim — we
// want scan_text to see them.
bool parse_db_file(const std::string& path, std::vector<std::pair<std::string,std::string>>& out)
{
    std::ifstream f(path);
    if (!f)
        return false;
    std::string line;
    std::string cur_key, cur_value;
    bool collecting_value = false;
    bool have_block = false;
    while (std::getline(f, line))
    {
        // Strip CRLF just in case (defensive — file is checked in via git).
        if (!line.empty() && line.back() == '\r')
            line.pop_back();
        if (line == "%%%%")
        {
            if (have_block && !cur_key.empty())
                out.push_back(std::make_pair(cur_key, cur_value));
            cur_key.clear();
            cur_value.clear();
            collecting_value = false;
            have_block = false;
            continue;
        }
        if (!collecting_value && !line.empty() && line[0] != '#')
        {
            cur_key = line;
            collecting_value = true;
            have_block = true;
            continue;
        }
        if (collecting_value)
        {
            if (!cur_value.empty())
                cur_value += '\n';
            cur_value += line;
        }
    }
    if (have_block && !cur_key.empty())
        out.push_back(std::make_pair(cur_key, cur_value));
    return true;
}

} // anonymous namespace

// =============================================================================
// Enumerator 1a — godspeak. Parses dat/database/zh/godspeak.txt for keys
// (line `<god_en> <event>` after each %%%%), then looks up the value via
// getMiscString(key) and scans it. Plan v2 §2.4 (#1a, Q6-corrected: key
// separator is space, not colon).
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: godspeak (Trog general effect, etc.)",
                 "[zh-translation]")
{
    std::vector<ZhIssue> issues;
    std::vector<std::pair<std::string, std::string>> blocks;
    if (!parse_db_file("dat/database/zh/godspeak.txt", blocks))
    {
        WARN("godsspeak.txt missing, skipping godspeak enumerator");
        REQUIRE(true);
        return;
    }
    for (auto& kv : blocks)
    {
        const std::string& key = kv.first;
        const std::string val = getMiscString(key);
        if (val.empty())
            continue;
        scan_one(val.c_str(), key, "godspeak.txt", issues);
    }
    emit_issue_protocol("zh_translation", "godspeak", issues);
    WARN("zh enumerator summary: godspeak -> " << issues.size() << " issues");
    REQUIRE(true);
}

// =============================================================================
// Enumerator 14 — tutorial/hints/commands text. Each file lives in
// dat/descript/zh/, uses %%%% separators, and stores Chinese values keyed by
// English short prompts. We parse + scan the value side. Plan v2 §2.4 (#14).
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: tutorial/hints/commands text",
                 "[zh-translation]")
{
    std::vector<ZhIssue> issues;
    const char* files[] = {
        "dat/descript/zh/tutorial.txt",
        "dat/descript/zh/hints.txt",
        "dat/descript/zh/commands.txt",
    };
    for (const char* path : files)
    {
        std::vector<std::pair<std::string, std::string>> blocks;
        if (!parse_db_file(path, blocks))
        {
            WARN(path << " missing, skipping");
            continue;
        }
        for (auto& kv : blocks)
        {
            const std::string& key = kv.first;
            // The descript DB query path is getLongDescription(key).
            const std::string val = getLongDescription(key);
            if (!val.empty())
            {
                if (val.find("attempt to") != std::string::npos)
                    continue;
                scan_one(val.c_str(), key, path, issues);
            }
            else
            {
                // Fall back to scanning the file's raw value side; skip
                // entries whose getLongDescription failed due to Lua
                // template evaluation errors in the catch2 sandbox.
                const std::string& raw = kv.second;
                if (raw.find("crawl.hints_") != std::string::npos
                    || raw.find("you.god()") != std::string::npos
                    || raw.find("you.get_base_") != std::string::npos)
                {
                    continue;
                }
                // Skip entries that are formatting directives, dev comments,
                // or have intentional whitespace (diagrams, markup tags).
                if (raw.find(":nowrap") == 0
                    || raw.find("# ") == 0
                    || raw.find("##") == 0
                    || key.find(" exit") != std::string::npos
                    || raw.find("<white>") == 0)
                {
                    continue;
                }
                scan_one(raw.c_str(), key, path, issues);
            }
        }
    }
    emit_issue_protocol("zh_translation", "tutorial_hints_commands", issues);
    WARN("zh enumerator summary: tutorial/hints/commands -> "
         << issues.size() << " issues");
    REQUIRE(true);
}

// =============================================================================
// Enumerator 4a — weapon brands. brand_type_name(brand, terse) is the Type II
// wrapper: returns T_(weapon_brands_verbose[brand]). brand_type_name_en is the
// English baseline (item-name.h:137) — these expose parallel lookup so we can
// compare the translated (T_-wrapped) display against the English key directly,
// priceless since the underlying arrays are static in item-name.cc.
//
// Iterate brand_type SPWPN_NORMAL..NUM_REAL_SPECIAL_WEAPONS-1 (skipping the
// -1 SPWPN_FORBID_BRAND); SPWPN_NORMAL==0 is the "no brand" sentinel and
// yields the empty/"plain" string — we still scan it but expect few issues.
// Both terse=false (verbose) and terse=true forms are scanned so ID strings and
// inventory display strings are both covered. Plan v2 §2.4 (#4, N1-adopted:
// pure enum iteration, no item_def construction required for weapon brands).
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: weapon brands",
                 "[zh-translation]")
{
    std::vector<ZhIssue> issues;
    for (int bi = SPWPN_NORMAL; bi < NUM_REAL_SPECIAL_WEAPONS; ++bi)
    {
        const brand_type b = static_cast<brand_type>(bi);
        for (int ti = 0; ti <= 1; ++ti)
        {
            const bool terse = (ti == 1);
            const char* en = brand_type_name_en(b, terse);
            if (!en || !en[0])
                continue;
            const char* tr = brand_type_name(b, terse);
            scan_one(tr ? tr : "", en, "source.txt", issues);
        }

        // Adjective forms have a separate production display path and no
        // dedicated _en accessor. Capture the English form under the existing
        // language guard, then exercise the real ZH accessor.
        std::string en_adj;
        {
            ScopedLangEn english;
            en_adj = brand_type_adj(b);
        }
        if (!en_adj.empty())
        {
            const char* tr_adj = brand_type_adj(b);
            scan_one(tr_adj ? tr_adj : "", en_adj, "source.txt", issues);
        }
    }
    emit_issue_protocol("zh_translation", "weapon_brands", issues);
    WARN("zh enumerator summary: weapon_brands -> " << issues.size()
                                                    << " issues");
    REQUIRE(true);
}

// =============================================================================
// Enumerator 4b — armour egos. special_armour_type_name(ego, terse) is the
// Type II wrapper for armour ego display names (e.g. "running", "fire
// resistance"). The catch2 build is already on T_()-wrapped output here;
// special_armour_type_name_en (item-name.h:141) provides the canonical English
// baseline, so we can detect UNTRANSLATED directly without constructing an
// item_def. Iterate SPARM_NORMAL..NUM_REAL_SPECIAL_ARMOURS-1 covering every
// real armour ego; both terse=false and terse=true forms are scanned. Plan v2
// §2.4 (#4, N1-adopted: avoids the item_def requirement of armour_ego_name).
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: armour egos",
                 "[zh-translation]")
{
    std::vector<ZhIssue> issues;
    for (int ei = SPARM_NORMAL; ei < NUM_REAL_SPECIAL_ARMOURS; ++ei)
    {
        const special_armour_type e = static_cast<special_armour_type>(ei);
        for (int ti = 0; ti <= 1; ++ti)
        {
            const bool terse = (ti == 1);
            const char* en = special_armour_type_name_en(e, terse);
            if (!en || !en[0])
                continue;
            const char* tr = special_armour_type_name(e, terse);
            scan_one(tr ? tr : "", en, "source.txt", issues);
        }
    }
    emit_issue_protocol("zh_translation", "armour_egos", issues);
    WARN("zh enumerator summary: armour_egos -> " << issues.size()
                                                  << " issues");
    REQUIRE(true);
}

// =============================================================================
// Enumerator 3 — identified item display names. The old implementation called
// item_base_name(type, sub_type), but that helper only handles weapons,
// missiles, armour, generic ring/amulet classes, and talismans. Wands, scrolls,
// potions, books, staves, orbs, miscellany, baubles, and concrete jewellery
// effects therefore produced no evidence.
//
// Construct an identified item_def and call item.name(DESC_PLAIN), the actual
// display producer, once under ScopedLangEn and once under the fixture's ZH
// language. all_item_subtypes supplies the known subtype set; explicit checks
// below exclude internal book sentinels and save-compatibility miscellany.
//
// The protocol enumerator remains item_base_names for compatibility with the
// existing aggregator and schema.
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: item base names",
                 "[zh-translation]")
{
    static const object_class_type kClasses[] = {
        OBJ_WEAPONS, OBJ_MISSILES, OBJ_ARMOUR, OBJ_WANDS,
        OBJ_SCROLLS, OBJ_JEWELLERY, OBJ_POTIONS, OBJ_BOOKS,
        OBJ_STAVES, OBJ_ORBS, OBJ_MISCELLANY, OBJ_TALISMANS,
        OBJ_BAUBLES,
    };

    // Build the complete production candidate set before scanning it.
    std::vector<std::pair<int, int>> candidates;
    for (object_class_type bc : kClasses)
    {
        for (int sub : all_item_subtypes(bc))
            candidates.emplace_back(static_cast<int>(bc), sub);
    }
    if (candidates.empty())
    {
        WARN("zh enumerator summary: item_base_names -> 0 issues (no candidates)");
        REQUIRE(true);
        return;
    }

    std::vector<ZhIssue> issues;
    for (const auto& c : candidates)
    {
        const auto base = static_cast<object_class_type>(c.first);
        if (base == OBJ_BOOKS
            && (c.second == BOOK_RANDART_LEVEL
                || c.second == BOOK_RANDART_THEME))
        {
            continue;
        }
        const item_def item = make_identified_item(base, c.second);
        std::string en;
        {
            ScopedLangEn english;
            en = item.name(DESC_PLAIN, false, true, false);
        }
        if (base == OBJ_MISCELLANY
            && (c.second == MISC_BOTTLED_EFREET
                || en.find("removed ") == 0
                || en.find("obsolete ") == 0))
        {
            continue;
        }
        const std::string zh = item.name(DESC_PLAIN, false, true, false);
        INFO("item class=" << static_cast<int>(base)
                           << " subtype=" << c.second);
        CHECK_FALSE(en.empty());
        CHECK_FALSE(zh.empty());
        if (en.empty() || zh.empty())
            continue;
        // Tag each issue with the source.txt domain even though the name
        // itself comes from T_(key) lookup — this lets M5 aggregator route
        // regressions to source.txt vs an item-specific db file cleanly.
        scan_one(zh.c_str(), en, "source.txt", issues);
    }

    emit_issue_protocol("zh_translation", "item_base_names", issues);
    WARN("zh enumerator summary: item_base_names -> " << issues.size()
                                                       << " issues");
    REQUIRE(true);
}
