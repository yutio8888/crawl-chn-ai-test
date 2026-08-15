#include "catch_amalgamated.hpp"

#include "AppHdr.h"
#include "textdb_phase0_artifact.h"

#include "beam.h"
#include "database.h"
#include "env.h"
#include "initfile.h"
#include "mon-cast-target.h"
#include "mon-speak.h"
#include "monster.h"
#include "player.h"
#include "random.h"
#include "state.h"
#include "stringutil.h"

#include "test_player_fixture.h"

#include <unistd.h>
#include <utility>

namespace
{
struct saved_phase0_cell
{
    coord_def position;
    dungeon_feature_type feature;
    unsigned short monster_index;
};

class scoped_phase0_target_world
{
public:
    scoped_phase0_target_world()
        : old_test(crawl_state.test), old_player_position(you.pos())
    {
        crawl_state.test = true;
        for (int x = 15; x <= 30; ++x)
        {
            for (int y = 15; y <= 30; ++y)
            {
                const coord_def position(x, y);
                cells.push_back({ position, env.grid(position),
                                  env.mgrid(position) });
                env.grid(position) = DNGN_FLOOR;
                env.mgrid(position) = NON_MONSTER;
            }
        }
        you.set_position(coord_def(20, 22));
    }

    ~scoped_phase0_target_world()
    {
        you.set_position(old_player_position);
        for (const saved_phase0_cell &cell : cells)
        {
            env.grid(cell.position) = cell.feature;
            env.mgrid(cell.position) = cell.monster_index;
        }
        crawl_state.test = old_test;
    }

private:
    bool old_test;
    coord_def old_player_position;
    vector<saved_phase0_cell> cells;
};

struct phase0_binding_context
{
    monster *source;
    const bolt *beam;
    resolved_speech_target target;
    resolved_beam resolved_beam_value;
    vector<speech_target_observer_event> target_events;
};

void observe_phase0_target_event(const speech_target_observer_event &event,
                                 void *opaque)
{
    static_cast<vector<speech_target_observer_event> *>(opaque)
        ->push_back(event);
}

void observe_phase0_substring_choice(
    const random_substring_choice_trace &event, void *opaque)
{
    static_cast<vector<random_substring_choice_trace> *>(opaque)
        ->push_back(event);
}

bool same_phase0_target_event(const speech_target_observer_event &lhs,
                              const speech_target_observer_event &rhs)
{
    return lhs.kind == rhs.kind
        && lhs.bound == rhs.bound
        && lhs.selected == rhs.selected
        && lhs.rng_state_before == rhs.rng_state_before
        && lhs.rng_state_after == rhs.rng_state_after
        && lhs.rng_count_before == rhs.rng_count_before
        && lhs.rng_count_after == rhs.rng_count_after;
}

textdb_phase0::message_runtime_bindings resolve_phase0_bindings(void *opaque)
{
    phase0_binding_context &context =
        *static_cast<phase0_binding_context *>(opaque);
    const speech_target_observer observer =
        { observe_phase0_target_event, &context.target_events };
    context.target = resolve_speech_target(
        context.source, *context.beam, false, &observer);
    context.resolved_beam_value = resolve_speech_beam(*context.beam, true);

    textdb_phase0::message_runtime_bindings result;
    result.actor_sentence_en = "The bone dragon";
    result.actor_en = "the bone dragon";
    switch (context.target.relation)
    {
    case speech_target_relation::AT:
        result.relation_en = "at";
        break;
    case speech_target_relation::NEXT_TO:
        result.relation_en = "next to";
        break;
    case speech_target_relation::PAST:
        result.relation_en = "past";
        break;
    }
    result.target_en = context.target.kind == speech_target_kind::PLAYER
        ? "you" : context.target.display;
    result.beam_en = context.resolved_beam_value.display_text;
    return result;
}

string bind_phase0_runtime_slots(
    string pattern, const textdb_phase0::message_runtime_bindings &bindings)
{
    pattern = replace_all(pattern, "@The_monster@",
                          bindings.actor_sentence_en);
    pattern = replace_all(pattern, "@the_monster@", bindings.actor_en);
    pattern = replace_all(pattern, "@at@", bindings.relation_en);
    pattern = replace_all(pattern, "@target@", bindings.target_en);
    return replace_all(pattern, "@beam@", bindings.beam_en);
}

struct weighted_run
{
    string output;
    uint64_t rng_state;
    uint64_t rng_count;
    textdb_phase0::selection_trace trace;
};

struct database_trace_run
{
    textdb_phase0::raw_selection_status status;
    textdb_phase0::selection_trace trace;
    uint64_t rng_state;
    uint64_t rng_count;
};

bool has_source_history(const textdb_phase0::canonical_entry &entry,
                        const string &source_name)
{
    return std::any_of(entry.source_history.begin(),
                       entry.source_history.end(),
        [&source_name](const textdb_phase0::source_provenance &source)
        {
            return source.source_name == source_name;
        });
}

uint64_t key_set_fingerprint(const set<string> &keys)
{
    uint64_t hash = 14695981039346656037ULL;
    for (const string &key : keys)
    {
        for (const unsigned char byte : key)
        {
            hash ^= byte;
            hash *= 1099511628211ULL;
        }
        hash ^= static_cast<unsigned char>('\n');
        hash *= 1099511628211ULL;
    }
    return hash;
}

bool same_rng_observation(const textdb_phase0::rng_observation &lhs,
                          const textdb_phase0::rng_observation &rhs)
{
    return lhs.current_state == rhs.current_state
        && lhs.current_count == rhs.current_count
        && lhs.global_counts == rhs.global_counts;
}

map<vector<size_t>, vector<size_t>> semantic_recursion_paths(
    const textdb_phase0::selection_trace &trace)
{
    map<vector<size_t>, vector<size_t>> normalized;
    map<vector<size_t>, size_t> next_child;
    for (const textdb_phase0::recursive_site_trace &site
         : trace.recursive_sites)
    {
        if (site.status == textdb_phase0::recursive_site_status::MISSING
            || site.recursion_path.empty())
        {
            continue;
        }
        vector<size_t> raw_parent = site.recursion_path;
        raw_parent.pop_back();
        vector<size_t> semantic_parent;
        if (!raw_parent.empty())
        {
            const auto parent = normalized.find(raw_parent);
            if (parent != normalized.end())
                semantic_parent = parent->second;
        }
        vector<size_t> semantic_path = semantic_parent;
        semantic_path.push_back(next_child[raw_parent]++);
        normalized[site.recursion_path] = semantic_path;
    }
    return normalized;
}

vector<size_t> semantic_recursion_path(
    const map<vector<size_t>, vector<size_t>> &paths,
    const vector<size_t> &raw_path)
{
    if (raw_path.empty())
        return {};
    const auto found = paths.find(raw_path);
    return found == paths.end() ? raw_path : found->second;
}

bool same_database_trace(const textdb_phase0::selection_trace &lhs,
                         const textdb_phase0::selection_trace &rhs)
{
    // Missing @foo@ sites are runtime slots from localized body text, not
    // successful database recursion. Their raw path/replacement counters are
    // therefore intentionally excluded from the semantic database trace.
    vector<const textdb_phase0::recursive_site_trace *> lhs_recursive;
    vector<const textdb_phase0::recursive_site_trace *> rhs_recursive;
    const map<vector<size_t>, vector<size_t>> lhs_paths =
        semantic_recursion_paths(lhs);
    const map<vector<size_t>, vector<size_t>> rhs_paths =
        semantic_recursion_paths(rhs);
    for (const textdb_phase0::recursive_site_trace &site : lhs.recursive_sites)
        if (site.status != textdb_phase0::recursive_site_status::MISSING)
            lhs_recursive.push_back(&site);
    for (const textdb_phase0::recursive_site_trace &site : rhs.recursive_sites)
        if (site.status != textdb_phase0::recursive_site_status::MISSING)
            rhs_recursive.push_back(&site);

    if (lhs.weighted_choices.size() != rhs.weighted_choices.size()
        || lhs_recursive.size() != rhs_recursive.size()
        || lhs.lua_sites.size() != rhs.lua_sites.size())
    {
        return false;
    }
    for (size_t i = 0; i < lhs.weighted_choices.size(); ++i)
    {
        const textdb_phase0::weighted_choice_trace &a = lhs.weighted_choices[i];
        const textdb_phase0::weighted_choice_trace &b = rhs.weighted_choices[i];
        if (a.requested_key != b.requested_key
            || a.resolved_canonical_key != b.resolved_canonical_key
            || semantic_recursion_path(lhs_paths, a.recursion_path)
                != semantic_recursion_path(rhs_paths, b.recursion_path)
            || a.recursion_depth != b.recursion_depth
            || a.variant_ordinal != b.variant_ordinal
            || a.weight != b.weight
            || a.total_bound != b.total_bound
            || a.random_result != b.random_result
            || !same_rng_observation(a.before, b.before)
            || !same_rng_observation(a.after, b.after))
        {
            return false;
        }
    }
    for (size_t i = 0; i < lhs_recursive.size(); ++i)
    {
        const textdb_phase0::recursive_site_trace &a = *lhs_recursive[i];
        const textdb_phase0::recursive_site_trace &b = *rhs_recursive[i];
        if (a.marker != b.marker
            || semantic_recursion_path(lhs_paths, a.recursion_path)
                != semantic_recursion_path(rhs_paths, b.recursion_path)
            || a.recursion_depth != b.recursion_depth
            || a.status != b.status)
        {
            return false;
        }
    }
    for (size_t i = 0; i < lhs.lua_sites.size(); ++i)
    {
        const textdb_phase0::lua_site_trace &a = lhs.lua_sites[i];
        const textdb_phase0::lua_site_trace &b = rhs.lua_sites[i];
        // Lua source/result text may be localized; compare only execution
        // topology, status, and RNG observations at this database stage.
        if (a.ordinal != b.ordinal || a.status != b.status
            || !same_rng_observation(a.before, b.before)
            || !same_rng_observation(a.after, b.after))
        {
            return false;
        }
    }
    return true;
}

database_trace_run run_database_trace(
    const vector<textdb_phase0::canonical_entry> &entries,
    const string &key, uint64_t seed)
{
    rng::subgenerator scoped_rng(seed, 0x5a17c0de12345678ULL);
    database_trace_run result;
    const textdb_phase0::raw_selection raw =
        textdb_phase0::select_canonical_english(entries, key);
    const textdb_phase0::expanded_selection expanded =
        textdb_phase0::expand_canonical_selection(entries, raw);
    result.status = expanded.status;
    result.trace = expanded.trace;
    result.rng_state = rng::current_generator().get_state();
    result.rng_count = rng::current_generator().get_count();
    return result;
}

vector<textdb_phase0::canonical_entry> merge_localized_speakdb(
    const vector<textdb_phase0::canonical_entry> &canonical,
    const vector<textdb_phase0::canonical_entry> &localized)
{
    map<string, textdb_phase0::canonical_entry> merged;
    for (const textdb_phase0::canonical_entry &entry : canonical)
        merged[entry.canonical_key] = entry;
    for (const textdb_phase0::canonical_entry &entry : localized)
    {
        // TextDB child lookup falls back to the parent for a zero-size body.
        if (!entry.body_empty)
            merged[entry.canonical_key] = entry;
    }
    vector<textdb_phase0::canonical_entry> result;
    result.reserve(merged.size());
    for (const auto &item : merged)
        result.push_back(item.second);
    return result;
}

void record_selected_variants(
    const textdb_phase0::selection_trace &trace,
    map<string, set<size_t>> &observed)
{
    for (const textdb_phase0::weighted_choice_trace &choice
         : trace.weighted_choices)
    {
        observed[choice.resolved_canonical_key].insert(choice.variant_ordinal);
    }
}

const textdb_phase0::canonical_entry *find_canonical_entry(
    const vector<textdb_phase0::canonical_entry> &entries,
    const string &key)
{
    const auto found = std::lower_bound(entries.begin(), entries.end(), key,
        [](const textdb_phase0::canonical_entry &entry,
           const string &candidate) { return entry.canonical_key < candidate; });
    return found == entries.end() || found->canonical_key != key
        ? nullptr : &*found;
}

textdb_phase0::canonical_entry *find_canonical_entry_mutable(
    vector<textdb_phase0::canonical_entry> &entries,
    const string &key)
{
    const auto found = std::lower_bound(entries.begin(), entries.end(), key,
        [](const textdb_phase0::canonical_entry &entry,
           const string &candidate) { return entry.canonical_key < candidate; });
    return found == entries.end() || found->canonical_key != key
        ? nullptr : &*found;
}

set<string> statically_reachable_weighted_keys(
    const vector<textdb_phase0::canonical_entry> &entries,
    const vector<string> &roots)
{
    set<string> reachable;
    vector<string> pending(roots.begin(), roots.end());
    while (!pending.empty())
    {
        const string key = pending.back();
        pending.pop_back();
        const textdb_phase0::canonical_entry *entry =
            find_canonical_entry(entries, key);
        if (!entry || entry->body_empty || !entry->parse_error.empty()
            || entry->variants.empty() || !reachable.insert(key).second)
        {
            continue;
        }

        for (const textdb_phase0::canonical_variant &variant
             : entry->variants)
        {
            string::size_type start = 0;
            while ((start = variant.raw_pattern.find('@', start))
                   != string::npos)
            {
                const string::size_type end =
                    variant.raw_pattern.find('@', start + 1);
                if (end == string::npos)
                    break;
                string child = variant.raw_pattern.substr(
                    start + 1, end - start - 1);
                lowercase(child);
                if (find_canonical_entry(entries, child)
                    && !reachable.count(child))
                {
                    pending.push_back(child);
                }
                start = end + 1;
            }
        }
    }
    return reachable;
}

bool observed_variants_cover_reachable(
    const vector<textdb_phase0::canonical_entry> &entries,
    const set<string> &reachable,
    const map<string, set<size_t>> &observed)
{
    for (const string &key : reachable)
    {
        const textdb_phase0::canonical_entry *entry =
            find_canonical_entry(entries, key);
        if (!entry)
            return false;
        set<size_t> expected;
        for (const textdb_phase0::canonical_variant &variant
             : entry->variants)
        {
            expected.insert(variant.locator.variant_ordinal);
        }
        const auto actual = observed.find(key);
        if (actual == observed.end() || actual->second != expected)
            return false;
    }
    for (const auto &item : observed)
    {
        if (!reachable.count(item.first))
            return false;
    }
    return true;
}

weighted_run run_production_choice(const string &entry)
{
    rng::subgenerator scoped_rng(0x13579bdf2468ace0ULL,
                                 0x02468ace13579bdfULL);
    weighted_run result;
    result.output = textdb_phase0::choose_weighted_entry(entry);
    result.rng_state = rng::current_generator().get_state();
    result.rng_count = rng::current_generator().get_count();
    return result;
}

weighted_run run_choice_from_parsed_variants(const string &entry)
{
    rng::subgenerator scoped_rng(0x13579bdf2468ace0ULL,
                                 0x02468ace13579bdfULL);
    const vector<textdb_phase0::weighted_variant> variants =
        textdb_phase0::parse_weighted_entry(entry);
    int total_weight = 0;
    for (const textdb_phase0::weighted_variant &variant : variants)
        total_weight += variant.weight;

    const int choice = random2(total_weight);
    int cumulative = 0;
    weighted_run result;
    for (const textdb_phase0::weighted_variant &variant : variants)
    {
        cumulative += variant.weight;
        if (choice < cumulative)
        {
            result.output = variant.raw_pattern;
            break;
        }
    }
    result.rng_state = rng::current_generator().get_state();
    result.rng_count = rng::current_generator().get_count();
    return result;
}

void ensure_test_data_root()
{
    if (!SysEnv.crawl_dir.empty())
        return;
    char cwd[4096];
    REQUIRE(getcwd(cwd, sizeof(cwd)) != nullptr);
    SysEnv.crawl_dir = cwd;
}

weighted_run run_legacy_speak_key(const string &key, uint64_t seed)
{
    rng::subgenerator scoped_rng(seed,
                                 0x1029384756abcdefULL);
    weighted_run result;
    result.output =
        textdb_phase0::expand_loaded_canonical_english_speakdb(key);
    result.rng_state = rng::current_generator().get_state();
    result.rng_count = rng::current_generator().get_count();
    return result;
}

weighted_run run_canonical_speak_key(
    const vector<textdb_phase0::canonical_entry> &entries,
    const string &key, uint64_t seed)
{
    rng::subgenerator scoped_rng(seed,
                                 0x1029384756abcdefULL);
    weighted_run result;
    const textdb_phase0::raw_selection raw =
        textdb_phase0::select_canonical_english(entries, key);
    const textdb_phase0::expanded_selection expanded =
        textdb_phase0::expand_canonical_selection(entries, raw);
    result.output = expanded.text;
    result.trace = expanded.trace;
    result.rng_state = rng::current_generator().get_state();
    result.rng_count = rng::current_generator().get_count();
    return result;
}

textdb_phase0::canonical_entry make_canonical_entry(const string &key,
                                                     const string &pattern)
{
    textdb_phase0::canonical_entry entry;
    entry.canonical_key = key;
    entry.body_empty = false;
    textdb_phase0::canonical_variant variant;
    variant.locator.canonical_key = key;
    variant.locator.variant_ordinal = 0;
    variant.weight = 10;
    variant.raw_pattern = pattern;
    entry.variants.push_back(variant);
    return entry;
}
}

TEST_CASE("Phase 0 TextDB parser exposes effective canonical entries",
          "[single-file][textdb][phase0]")
{
    const vector<textdb_phase0::source> sources =
    {
        {
            "first.txt",
            "ignored preamble\n"
            "%%%%% accepted delimiter suffix\n"
            "  Mixed KEY \t\n"
            "# ignored body comment\n"
            "old value   \t\n"
            "  # indented hash is body   \n"
            "%%%%\n"
            "Weighted\n"
            "w:7junk accepted by sscanf\n"
            "alpha   \n"
            "\n"
            "beta\n"
            "%%%%\n"
            "Empty Body\n"
            "%%%%\n"
            "Hash Body\n"
            "# ignored at column zero\n"
            "  # retained when indented   \n"
            "%%%%\n"
            "Mixed Key\n"
            "same-file replacement\n"
        },
        {
            "second.txt",
            "%%%%\n"
            " mixed key\n"
            "replacement\n"
            "%%%%\n"
            "z-last\n"
            "last\n"
            "%%%%\n"
            "A-first\n"
            "first\n"
            "%%%%\n"
            "EOF Weight\n"
            "valid\n"
            "\n"
            "w:5"
        },
        {
            "third.txt",
            "%%%%\n"
            "EOF Empty\n"
            "\n"
        },
    };

    const vector<textdb_phase0::canonical_entry> entries =
        textdb_phase0::canonicalise_sources(sources);
    REQUIRE(entries.size() == 8);

    CHECK(entries[0].canonical_key == "a-first");
    CHECK(entries[1].canonical_key == "empty body");
    CHECK(entries[2].canonical_key == "eof empty");
    CHECK(entries[3].canonical_key == "eof weight");
    CHECK(entries[4].canonical_key == "hash body");
    CHECK(entries[5].canonical_key == "mixed key");
    CHECK(entries[6].canonical_key == "weighted");
    CHECK(entries[7].canonical_key == "z-last");

    const textdb_phase0::canonical_entry &empty = entries[1];
    CHECK(empty.provenance.source_name == "first.txt");
    CHECK(empty.provenance.load_index == 0);
    CHECK(empty.variants.empty());
    CHECK(empty.parse_error == "BUG, EMPTY ENTRY");
    CHECK(empty.body_empty);
    const textdb_phase0::raw_selection empty_selection =
        textdb_phase0::select_canonical_english(entries, "empty body");
    CHECK(empty_selection.status
          == textdb_phase0::raw_selection_status::MISSING);
    CHECK(empty_selection.locator.variant_ordinal
          == static_cast<size_t>(-1));
    CHECK(textdb_phase0::expand_canonical_speakdb(entries, "empty body")
          == "");

    // Leading newline trimming makes an EOF/blank-only file body the same
    // zero-length DB value; canonical expansion must also treat it as MISSING.
    const textdb_phase0::canonical_entry &eof_empty = entries[2];
    CHECK(eof_empty.body_empty);
    CHECK(eof_empty.parse_error == "BUG, EMPTY ENTRY");
    CHECK(textdb_phase0::expand_canonical_speakdb(entries, "eof empty") == "");

    // The production LineInput path appends a trailing empty body line, so an
    // EOF w:N is an empty weighted variant rather than WEIGHT AT END.
    const textdb_phase0::canonical_entry &eof_weight = entries[3];
    CHECK_FALSE(eof_weight.body_empty);
    CHECK(eof_weight.parse_error.empty());
    REQUIRE(eof_weight.variants.size() == 2);
    CHECK(eof_weight.variants[0].raw_pattern == "valid");
    CHECK(eof_weight.variants[1].weight == 5);
    CHECK(eof_weight.variants[1].raw_pattern.empty());

    const textdb_phase0::canonical_entry &hash_body = entries[4];
    REQUIRE(hash_body.variants.size() == 1);
    CHECK(hash_body.variants[0].raw_pattern == "# retained when indented");

    const textdb_phase0::canonical_entry &overridden = entries[5];
    CHECK(overridden.provenance.source_name == "second.txt");
    CHECK(overridden.provenance.load_index == 1);
    CHECK(overridden.provenance.definition_ordinal == 0);
    CHECK(overridden.raw_body == "replacement\n");
    REQUIRE(overridden.source_history.size() == 3);
    CHECK(overridden.source_history[0].source_name == "first.txt");
    CHECK(overridden.source_history[0].definition_ordinal == 0);
    CHECK(overridden.source_history[1].source_name == "first.txt");
    CHECK(overridden.source_history[1].definition_ordinal == 4);
    CHECK(overridden.source_history[2].source_name == "second.txt");
    CHECK(overridden.source_history[2].definition_ordinal == 0);
    REQUIRE(overridden.variants.size() == 1);
    CHECK(overridden.variants[0].locator.canonical_key == "mixed key");
    CHECK(overridden.variants[0].locator.variant_ordinal == 0);
    CHECK(overridden.variants[0].provenance.source_name == "second.txt");
    CHECK(overridden.variants[0].provenance.load_index == 1);
    CHECK(overridden.variants[0].weight == 10);
    CHECK(overridden.variants[0].raw_pattern == "replacement");

    const textdb_phase0::canonical_entry &weighted = entries[6];
    REQUIRE(weighted.variants.size() == 2);
    CHECK(weighted.variants[0].weight == 7);
    CHECK(weighted.variants[0].raw_pattern == "alpha");
    CHECK(weighted.variants[1].weight == 10);
    CHECK(weighted.variants[1].raw_pattern == "beta");
}

TEST_CASE("Phase 0 weighted parser preserves legacy choice and RNG",
          "[single-file][textdb][phase0]")
{
    const string entry =
        "w:3 trailing text accepted by sscanf\ncasts\n\n"
        "w:11\npitches\n\n"
        "pulses\n";

    const weighted_run production = run_production_choice(entry);
    const weighted_run parsed = run_choice_from_parsed_variants(entry);
    CHECK(production.output == parsed.output);
    CHECK(production.rng_state == parsed.rng_state);
    CHECK(production.rng_count == parsed.rng_count);
    CHECK(production.rng_count == 1);

    CHECK(textdb_phase0::choose_weighted_entry(entry, 0) == "casts");
    CHECK(textdb_phase0::choose_weighted_entry(entry, 3) == "pitches");
    CHECK(textdb_phase0::choose_weighted_entry(entry, 14) == "pulses");
    CHECK(textdb_phase0::choose_weighted_entry("") == "BUG, EMPTY ENTRY");
    CHECK(textdb_phase0::choose_weighted_entry("w:5")
          == "BUG, WEIGHT AT END OF ENTRY");

    const textdb_phase0::weighted_parse_result malformed =
        textdb_phase0::parse_weighted_entry_result("valid\n\nw:5");
    REQUIRE(malformed.variants.size() == 1);
    CHECK(malformed.variants[0].raw_pattern == "valid");
    CHECK(malformed.parse_error == "BUG, WEIGHT AT END OF ENTRY");

    textdb_phase0::canonical_entry malformed_entry;
    malformed_entry.canonical_key = "malformed";
    malformed_entry.parse_error = malformed.parse_error;
    malformed_entry.body_empty = false;
    textdb_phase0::canonical_variant partial;
    partial.locator.canonical_key = "malformed";
    partial.locator.variant_ordinal = 0;
    partial.weight = malformed.variants[0].weight;
    partial.raw_pattern = malformed.variants[0].raw_pattern;
    malformed_entry.variants.push_back(partial);
    const vector<textdb_phase0::canonical_entry> malformed_catalog =
        { malformed_entry };

    const textdb_phase0::raw_selection malformed_selection =
        textdb_phase0::select_canonical_english(malformed_catalog,
                                                 "malformed");
    CHECK(malformed_selection.status
          == textdb_phase0::raw_selection_status::CORRUPT);
    CHECK(malformed_selection.locator.variant_ordinal
          == static_cast<size_t>(-1));

    rng::subgenerator malformed_rng(123, 456);
    const uint64_t before_state = rng::current_generator().get_state();
    const uint64_t before_count = rng::current_generator().get_count();
    CHECK(textdb_phase0::expand_canonical_speakdb(malformed_catalog,
                                                   "malformed")
          == textdb_phase0::choose_weighted_entry("valid\n\nw:5"));
    CHECK(rng::current_generator().get_state() == before_state);
    CHECK(rng::current_generator().get_count() == before_count);

    // A non-zero raw DB body containing only newlines is not MISSING even
    // though the weighted parser finds no variants. This state is unreachable
    // through _parse_text_db after leading-newline trimming, but the shared
    // chooser API retains the legacy error contract for direct DB values.
    textdb_phase0::canonical_entry nonzero_empty;
    nonzero_empty.canonical_key = "nonzero empty";
    nonzero_empty.parse_error = "BUG, EMPTY ENTRY";
    nonzero_empty.body_empty = false;
    const vector<textdb_phase0::canonical_entry> nonzero_catalog =
        { nonzero_empty };
    CHECK(textdb_phase0::expand_canonical_speakdb(nonzero_catalog,
                                                   "nonzero empty")
          == textdb_phase0::choose_weighted_entry("\n"));
    CHECK(rng::current_generator().get_state() == before_state);
    CHECK(rng::current_generator().get_count() == before_count);
}

TEST_CASE("Phase 0 typed dump normalizes source snapshots",
          "[single-file][textdb][phase0]")
{
    const string with_bom_and_cr =
        string("\xef\xbb\xbf") + "%%%%\r\nKey\rbody\r\n";
    const textdb_phase0::canonical_speakdb_dump dump =
        textdb_phase0::canonicalise_source_dump(
            { { "fixture.txt", with_bom_and_cr } });
    REQUIRE(dump.sources.size() == 1);
    CHECK(dump.schema_version == 1);
    CHECK(dump.database_name == "speak");
    CHECK(dump.sources[0].normalized_utf8 == "%%%%\nKey\nbody\n");

    const string literal_replacement_character =
        string("literal ") + "\xef\xbf\xbd";
    const textdb_phase0::source_normalization_result valid =
        textdb_phase0::normalize_textdb_source(
            literal_replacement_character);
    REQUIRE(valid.valid);
    CHECK(valid.normalized_utf8 == literal_replacement_character);
    CHECK(valid.error.empty());

    const textdb_phase0::source_normalization_result invalid_utf8 =
        textdb_phase0::normalize_textdb_source(string("\xc3\x28", 2));
    CHECK_FALSE(invalid_utf8.valid);
    CHECK(invalid_utf8.normalized_utf8.empty());
    CHECK_FALSE(invalid_utf8.error.empty());

    const textdb_phase0::source_normalization_result embedded_nul =
        textdb_phase0::normalize_textdb_source(string("ok\0bad", 6));
    CHECK_FALSE(embedded_nul.valid);
    CHECK(embedded_nul.normalized_utf8.empty());
    CHECK_FALSE(embedded_nul.error.empty());
}

TEST_CASE("Phase 0 localized SpeakDB discovery is controlled and stable",
          "[single-file][textdb][phase0]")
{
    CHECK(textdb_phase0::is_valid_textdb_locale("zh"));
    CHECK(textdb_phase0::is_valid_textdb_locale("pt_BR"));
    CHECK(textdb_phase0::is_valid_textdb_locale("zh-Hans"));
    for (const string &invalid
         : vector<string>{ "", "../zh", "zh/evil", "zh..", "_zh", "中文" })
    {
        INFO(invalid);
        CHECK_FALSE(textdb_phase0::is_valid_textdb_locale(invalid));
    }

    const vector<string> ordered =
        textdb_phase0::order_localized_speakdb_sources(
            { "z.txt", "source.txt", "A.txt", "ignored.txt.bak",
              "a.txt", "notxt", "\xc3\xa4.txt" });
    CHECK(ordered == (vector<string>{ "source.txt", "A.txt", "a.txt",
                                     "notxt", "z.txt", "\xc3\xa4.txt" }));
    CHECK(textdb_phase0::order_localized_speakdb_sources(
              { "z.txt", "a.txt" })
          == (vector<string>{ "a.txt", "z.txt" }));
}

TEST_CASE("Phase 0 artifact serializer has an exact stable shape",
          "[single-file][textdb][phase0]")
{
    textdb_phase0::canonical_speakdb_dump dump;
    dump.schema_version = 1;
    dump.database_name = "speak";
    dump.source_directory = "database/";
    dump.sources.push_back({ "database/a.txt", 0, "雪\n" });
    textdb_phase0::canonical_entry entry =
        make_canonical_entry("a\"key", "line\\one\n");
    entry.provenance = { "database/a.txt", 0, 2 };
    entry.source_history.push_back(entry.provenance);
    entry.raw_body = "line\\one\n";
    entry.variants[0].provenance = entry.provenance;
    dump.entries.push_back(entry);

    const string expected =
        "{\"schema_version\":1,\"database_name\":\"speak\","
        "\"source_directory\":\"database/\",\"sources\":[{"
        "\"source_name\":\"database/a.txt\",\"load_index\":0,"
        "\"normalized_utf8\":\"雪\\n\"}],\"entries\":[{"
        "\"canonical_key\":\"a\\\"key\",\"effective_provenance\":{"
        "\"source_name\":\"database/a.txt\",\"load_index\":0,"
        "\"definition_ordinal\":2},\"raw_body\":\"line\\\\one\\n\","
        "\"source_history\":[{\"source_name\":\"database/a.txt\","
        "\"load_index\":0,\"definition_ordinal\":2}],\"variants\":[{"
        "\"locator\":{\"canonical_key\":\"a\\\"key\","
        "\"variant_ordinal\":0},\"provenance\":{\"source_name\":"
        "\"database/a.txt\",\"load_index\":0,\"definition_ordinal\":2},"
        "\"weight\":10,\"raw_pattern\":\"line\\\\one\\n\"}],"
        "\"parse_error\":null,\"body_empty\":false}]}\n";
    CHECK(serialize_textdb_phase0_artifact(dump) == expected);
}

TEST_CASE("Phase 0 canonical English SpeakDB dump is deterministic",
          "[single-file][textdb][phase0]")
{
    ensure_test_data_root();
    const textdb_phase0::canonical_speakdb_dump first_dump =
        textdb_phase0::dump_canonical_english_speakdb_typed();
    const textdb_phase0::canonical_speakdb_dump second_dump =
        textdb_phase0::dump_canonical_english_speakdb_typed();
    const vector<textdb_phase0::canonical_entry> &first = first_dump.entries;
    const vector<textdb_phase0::canonical_entry> &second = second_dump.entries;
    REQUIRE_FALSE(first.empty());
    REQUIRE(first.size() == second.size());
    CHECK(serialize_textdb_phase0_artifact(first_dump)
          == serialize_textdb_phase0_artifact(second_dump));

    set<string> monspell_keys;
    size_t monspell_variants = 0;

    for (size_t i = 0; i < first.size(); ++i)
    {
        CHECK(first[i].canonical_key == second[i].canonical_key);
        CHECK(first[i].provenance.source_name
              == second[i].provenance.source_name);
        CHECK(first[i].provenance.load_index
              == second[i].provenance.load_index);
        CHECK(first[i].variants.size() == second[i].variants.size());
        CHECK(first[i].parse_error == second[i].parse_error);
        CHECK(first[i].body_empty == second[i].body_empty);
        if (i > 0)
            CHECK(first[i - 1].canonical_key < first[i].canonical_key);
        if (has_source_history(first[i], "database/monspell.txt"))
        {
            monspell_keys.insert(first[i].canonical_key);
            monspell_variants += first[i].variants.size();
        }
    }
    CHECK(monspell_keys.size() == 262);
    CHECK(monspell_variants == 355);
    CHECK(key_set_fingerprint(monspell_keys) == 0xc87868127106d293ULL);
}

TEST_CASE("Issue 16 repaired Chinese monspeak boundaries parse as intended",
          "[single-file][textdb][phase0][issue-16]")
{
    ensure_test_data_root();
    databaseSystemInit();
    const vector<textdb_phase0::canonical_entry> localized =
        textdb_phase0::dump_localized_speakdb_typed("zh").entries;

    const vector<string> restored_roots =
    {
        "aizul", "crazy yiuf", "harold", "robin", "joseph",
        "azrael", "menkaure", "dowan", "swamp donald",
    };
    for (const string &key : restored_roots)
    {
        INFO(key);
        const textdb_phase0::canonical_entry *entry =
            find_canonical_entry(localized, key);
        REQUIRE(entry != nullptr);
        CHECK(entry->parse_error.empty());
        CHECK_FALSE(entry->body_empty);
        CHECK(has_source_history(*entry, "database/zh/monspeak.txt"));
    }

    const textdb_phase0::canonical_entry *jory =
        find_canonical_entry(localized, "_jory_silent_");
    REQUIRE(jory != nullptr);
    REQUIRE(jory->parse_error.empty());
    REQUIRE(jory->variants.size() == 11);
    for (const textdb_phase0::canonical_variant &variant : jory->variants)
    {
        INFO(variant.locator.variant_ordinal);
        CHECK(variant.raw_pattern.rfind("VISUAL:", 0) == 0);
    }
}

// CR-008/CR-019/CR-023: the complete sorted-unique EN monspeak VISUAL
// (canonical key, variant ordinal, Lua return branch ordinal, line
// ordinal) identity set, frozen from the baseline EN dump
// (b3ad4425053c2175284d32441d67218df97035b0).  The Issue-16 contract
// compares the full set at the production sink granularity:
// mons_speaks_msg (mon-speak.cc) splits every selected pattern by '\n'
// and resolves each line through resolve_mon_speech_line_channel, so a
// VISUAL line that is not the first line of its pattern (e.g.
// ``_holy_being_`` #0) or a second VISUAL line inside one pattern (e.g.
// ``_margery_common_`` #2) is part of the contract.  The branch ordinal
// (CR-023) is the Lua return branch index: getSpeakString evaluates
// every ``{{...}}`` block before the sink, so each literal
// ``return "VISUAL:..."`` emission is a possible runtime line and
// participates in the frozen set (e.g. ``friendly shoals hound`` #2
// emits two VISUAL branches, ``nekomata`` #1 emits two of three).
// Patterns without Lua blocks have exactly one branch (ordinal 0).  An
// EN edit that moves a VISUAL line to another ordinal or line, changes a
// VISUAL prefix inside a Lua return or deletes a Lua return branch (even
// one jointly mirrored in ZH so the per-line ZH check still passes)
// changes this set and fails.
struct frozen_monspeak_visual_line
{
    const char *key;
    size_t ordinal;
    size_t branch;
    size_t line;
};

static const frozen_monspeak_visual_line FROZEN_MONSPEAK_EN_VISUAL[] = {
    {"'r'", 0, 0, 0},
    {"_agnes_common_", 0, 0, 0},
    {"_aizul_common_", 0, 0, 0},
    {"_aizul_common_", 3, 0, 0},
    {"_aizul_rare_", 2, 0, 0},
    {"_aizul_rare_", 8, 0, 0},
    {"_amaemon_common_", 1, 0, 0},
    {"_amaemon_common_", 2, 0, 0},
    {"_amaemon_common_", 3, 0, 0},
    {"_asterion_common_", 0, 0, 0},
    {"_asterion_common_", 1, 0, 0},
    {"_azrael_common_", 3, 0, 0},
    {"_azrael_common_", 4, 0, 0},
    {"_azrael_common_", 5, 0, 0},
    {"_azrael_rare_", 3, 0, 0},
    {"_bai_suzhen_common_", 4, 0, 0},
    {"_bai_suzhen_rare_", 5, 0, 0},
    {"_bennu_death_", 0, 0, 0},
    {"_blorkula_common_", 1, 0, 0},
    {"_blorkula_common_", 2, 0, 0},
    {"_blorkula_common_", 3, 0, 0},
    {"_blorkula_rare_", 5, 0, 0},
    {"_boris_common_", 0, 0, 0},
    {"_chuck_generic_", 6, 0, 0},
    {"_chuck_rare_", 1, 0, 0},
    {"_confused_humanoid_common_", 0, 0, 0},
    {"_confused_humanoid_common_", 2, 0, 0},
    {"_confused_humanoid_common_", 4, 0, 0},
    {"_confused_humanoid_common_", 5, 0, 0},
    {"_confused_humanoid_common_", 6, 0, 0},
    {"_confused_humanoid_common_", 7, 0, 0},
    {"_confused_humanoid_medium_", 0, 0, 0},
    {"_confused_humanoid_rare_", 4, 0, 0},
    {"_confused_humanoid_rare_", 5, 0, 0},
    {"_crazy_yiuf_speech_", 1, 0, 0},
    {"_crazy_yiuf_speech_", 3, 0, 0},
    {"_crazy_yiuf_speech_", 4, 0, 0},
    {"_crazy_yiuf_speech_", 5, 0, 0},
    {"_dissolution_common_", 3, 0, 0},
    {"_dissolution_common_", 4, 0, 0},
    {"_dowan_common_", 0, 0, 0},
    {"_dowan_rare_", 0, 0, 0},
    {"_dowan_rare_", 1, 0, 0},
    {"_dowan_rare_", 2, 0, 0},
    {"_dowan_rare_", 3, 0, 0},
    {"_duvessa_common_", 0, 0, 0},
    {"_edmund_common_", 0, 0, 0},
    {"_edmund_rare_", 0, 0, 0},
    {"_edmund_rare_", 1, 0, 0},
    {"_erica_common_", 0, 0, 0},
    {"_erolcha_common_", 2, 0, 0},
    {"_eustachio_rare_", 1, 0, 0},
    {"_fake_spell_effect_", 0, 0, 0},
    {"_fake_spell_effect_", 1, 0, 0},
    {"_fake_spell_effect_", 2, 0, 0},
    {"_fake_spell_effect_", 3, 0, 0},
    {"_fake_spell_effect_", 4, 0, 0},
    {"_fannar_common_", 0, 0, 0},
    {"_fannar_common_", 1, 0, 0},
    {"_fannar_common_", 2, 0, 0},
    {"_fleeing_humanoid_common_", 0, 0, 0},
    {"_fleeing_humanoid_common_", 2, 0, 0},
    {"_fleeing_humanoid_rare_", 5, 0, 0},
    {"_fleeing_humanoid_rare_", 7, 0, 0},
    {"_fleeing_humanoid_rare_", 9, 0, 0},
    {"_fleeing_humanoid_rare_", 11, 0, 0},
    {"_fleeing_silenced_common_", 0, 0, 0},
    {"_fleeing_silenced_common_", 1, 0, 0},
    {"_fleeing_silenced_rare_", 0, 0, 0},
    {"_fleeing_silenced_rare_", 1, 0, 0},
    {"_fleeing_silenced_rare_", 2, 0, 0},
    {"_frances_common_", 0, 0, 0},
    {"_frances_common_", 1, 0, 0},
    {"_frances_rare_", 0, 0, 0},
    {"_frederick_common_", 0, 0, 0},
    {"_frederick_common_", 1, 0, 0},
    {"_frederick_rare_", 0, 0, 0},
    {"_frederick_rare_", 1, 0, 0},
    {"_frederick_rare_", 2, 0, 0},
    {"_friendly_beogh_speech_rare_", 5, 0, 0},
    {"_friendly_confused_common_", 4, 0, 0},
    {"_friendly_confused_common_", 5, 0, 0},
    {"_friendly_confused_medium_", 4, 0, 0},
    {"_friendly_confused_medium_", 5, 0, 0},
    {"_friendly_confused_medium_", 6, 0, 0},
    {"_friendly_confused_rare_", 5, 0, 0},
    {"_friendly_fleeing_common_", 0, 0, 0},
    {"_friendly_humanoid_common_", 2, 0, 0},
    {"_friendly_humanoid_common_", 3, 0, 0},
    {"_friendly_humanoid_common_", 5, 0, 0},
    {"_friendly_humanoid_medium_", 4, 0, 0},
    {"_friendly_humanoid_rare_", 0, 0, 0},
    {"_friendly_imp_common_", 0, 0, 0},
    {"_friendly_imp_common_", 1, 0, 0},
    {"_friendly_imp_common_", 2, 0, 0},
    {"_friendly_imp_common_", 3, 0, 0},
    {"_friendly_silenced_common_", 0, 0, 0},
    {"_friendly_silenced_common_", 1, 0, 0},
    {"_friendly_silenced_rare_", 0, 0, 0},
    {"_friendly_silenced_rare_", 1, 0, 0},
    {"_friendly_silenced_rare_", 2, 0, 0},
    {"_friendly_silenced_rare_", 3, 0, 0},
    {"_friendly_silenced_rare_", 4, 0, 0},
    {"_gastronok_common_", 0, 0, 0},
    {"_gastronok_rare_", 0, 0, 0},
    {"_gastronok_rare_", 1, 0, 0},
    {"_gastronok_rare_", 2, 0, 0},
    {"_generic_donald_", 25, 0, 0},
    {"_generic_donald_", 26, 0, 0},
    {"_generic_donald_", 27, 0, 0},
    {"_grinder_common_", 0, 0, 0},
    {"_grinder_rare_", 5, 0, 0},
    {"_grum_common_", 0, 0, 0},
    {"_grum_common_", 4, 0, 0},
    {"_grum_rare_", 0, 0, 0},
    {"_grunn_rare_", 0, 0, 0},
    {"_grunn_rare_", 1, 0, 0},
    {"_harold_common_", 0, 0, 0},
    {"_harold_rare_", 0, 0, 0},
    {"_high_priest_medium_", 0, 0, 0},
    {"_holy_being_", 0, 0, 1},
    {"_hostile_imp_common_", 1, 0, 0},
    {"_hostile_imp_common_", 2, 0, 0},
    {"_hostile_imp_common_", 3, 0, 0},
    {"_hostile_imp_common_", 4, 0, 0},
    {"_hostile_imp_rare_", 0, 0, 0},
    {"_hostile_imp_rare_", 1, 0, 0},
    {"_hostile_imp_rare_", 3, 0, 0},
    {"_hostile_imp_rare_", 4, 0, 0},
    {"_hostile_orc_beogh_believer_speech_common_", 10, 0, 0},
    {"_hostile_orc_beogh_believer_speech_rare_", 5, 0, 0},
    {"_hostile_orc_beogh_believer_speech_rare_", 6, 0, 0},
    {"_ignacio_common_", 0, 0, 0},
    {"_ignacio_common_", 1, 0, 0},
    {"_ijyb_common_", 0, 0, 0},
    {"_ijyb_common_", 1, 0, 0},
    {"_ilsuiw_common_", 3, 0, 0},
    {"_ilsuiw_rare_", 0, 0, 0},
    {"_jeremiah_common_", 6, 0, 0},
    {"_jeremiah_common_", 7, 0, 0},
    {"_jeremiah_common_", 8, 0, 0},
    {"_jeremiah_common_", 9, 0, 0},
    {"_jeremiah_common_", 10, 0, 0},
    {"_jeremiah_common_", 11, 0, 0},
    {"_jeremiah_rare_", 12, 0, 0},
    {"_jessica_common_", 0, 0, 0},
    {"_jessica_common_", 1, 0, 0},
    {"_jessica_common_", 3, 0, 0},
    {"_jory_silent_", 0, 0, 0},
    {"_jory_silent_", 1, 0, 0},
    {"_jory_silent_", 2, 0, 0},
    {"_jory_silent_", 3, 0, 0},
    {"_jory_silent_", 4, 0, 0},
    {"_jory_silent_", 5, 0, 0},
    {"_jory_silent_", 6, 0, 0},
    {"_jory_silent_", 7, 0, 0},
    {"_jory_silent_", 8, 0, 0},
    {"_jory_silent_", 9, 0, 0},
    {"_jory_silent_", 10, 0, 0},
    {"_joseph_common_", 1, 0, 0},
    {"_joseph_common_", 2, 0, 0},
    {"_josephina_common_", 0, 0, 0},
    {"_josephina_common_", 1, 0, 0},
    {"_josephina_common_", 4, 0, 0},
    {"_josephina_rare_", 0, 0, 0},
    {"_josephina_rare_", 1, 0, 0},
    {"_killer_klown_common_", 2, 0, 0},
    {"_killer_klown_common_", 3, 0, 0},
    {"_killer_klown_common_", 4, 0, 0},
    {"_killer_klown_common_", 5, 0, 0},
    {"_killer_klown_common_", 6, 0, 0},
    {"_killer_klown_common_", 7, 0, 0},
    {"_killer_klown_common_", 8, 0, 0},
    {"_killer_klown_rare_", 1, 0, 0},
    {"_killer_klown_rare_", 2, 0, 0},
    {"_killer_klown_rare_", 3, 0, 0},
    {"_killer_klown_rare_", 4, 0, 0},
    {"_lodul_common_", 1, 0, 0},
    {"_lodul_common_", 4, 0, 0},
    {"_lodul_rare_", 2, 0, 0},
    {"_maggie_common_", 0, 0, 0},
    {"_maggie_common_", 1, 0, 0},
    {"_maggie_common_", 4, 0, 0},
    {"_mara_common_", 0, 0, 0},
    {"_mara_common_", 6, 0, 0},
    {"_mara_common_", 7, 0, 0},
    {"_mara_common_", 8, 0, 0},
    {"_margery_common_", 0, 0, 0},
    {"_margery_common_", 1, 0, 0},
    {"_margery_common_", 2, 0, 0},
    {"_margery_common_", 2, 0, 1},
    {"_margery_common_", 3, 0, 0},
    {"_margery_rare_", 1, 0, 0},
    {"_margery_spell_results_", 0, 0, 0},
    {"_margery_spell_results_", 1, 0, 0},
    {"_margery_spell_results_", 2, 0, 0},
    {"_maurice_common_", 0, 0, 0},
    {"_maurice_common_", 1, 0, 0},
    {"_maurice_medium_", 0, 0, 0},
    {"_menkaure_common_", 0, 0, 0},
    {"_menkaure_common_", 5, 0, 0},
    {"_menkaure_common_", 6, 0, 0},
    {"_menkaure_common_", 8, 0, 0},
    {"_menkaure_common_", 10, 0, 0},
    {"_menkaure_rare_", 1, 0, 0},
    {"_menkaure_rare_", 2, 0, 0},
    {"_menkaure_rare_", 7, 0, 0},
    {"_mercenary_guard_common_", 0, 0, 0},
    {"_mercenary_guard_common_", 1, 0, 0},
    {"_murray_common_", 0, 0, 0},
    {"_murray_common_", 1, 0, 0},
    {"_murray_common_", 2, 0, 0},
    {"_murray_common_", 3, 0, 0},
    {"_natasha_rare_", 3, 0, 0},
    {"_nellie_common_", 5, 0, 0},
    {"_nellie_common_", 6, 0, 0},
    {"_nellie_common_", 7, 0, 0},
    {"_norris_common_", 1, 0, 0},
    {"_norris_common_", 2, 0, 0},
    {"_norris_common_", 3, 0, 0},
    {"_norris_rare_", 0, 0, 0},
    {"_parghit_common_", 1, 0, 0},
    {"_parghit_rare_", 0, 0, 0},
    {"_parghit_rare_", 1, 0, 0},
    {"_pargi_common_", 1, 0, 0},
    {"_pargi_rare_", 0, 0, 0},
    {"_pargi_rare_", 1, 0, 0},
    {"_pargi_rare_", 4, 0, 0},
    {"_pikel_common_", 4, 0, 0},
    {"_pikel_rare_", 4, 0, 0},
    {"_pikel_rare_", 11, 0, 0},
    {"_player_ghost_common_", 0, 0, 0},
    {"_player_ghost_common_", 4, 0, 0},
    {"_player_ghost_medium_", 1, 0, 0},
    {"_polyphemus_common_", 0, 0, 0},
    {"_polyphemus_common_", 1, 0, 0},
    {"_polyphemus_rare_", 0, 0, 0},
    {"_polyphemus_rare_", 1, 0, 0},
    {"_polyphemus_rare_", 2, 0, 0},
    {"_prince_ribbit_common_", 2, 0, 0},
    {"_prince_ribbit_common_", 3, 0, 0},
    {"_prince_ribbit_rare_", 3, 0, 0},
    {"_robin_common_", 5, 0, 0},
    {"_robin_common_", 6, 0, 0},
    {"_robin_common_", 7, 0, 0},
    {"_rupert_common_", 0, 0, 0},
    {"_rupert_common_", 1, 0, 0},
    {"_rupert_common_", 2, 0, 0},
    {"_rupert_rare_", 0, 0, 0},
    {"_sigmund_common_", 1, 0, 0},
    {"_sigmund_common_", 12, 0, 0},
    {"_sigmund_common_", 13, 0, 1},
    {"_sigmund_common_", 14, 0, 0},
    {"_sigmund_rare_", 5, 0, 0},
    {"_silenced_humanoid_common_", 0, 0, 0},
    {"_silenced_humanoid_common_", 1, 0, 0},
    {"_silenced_humanoid_rare_", 0, 0, 0},
    {"_silenced_humanoid_rare_", 1, 0, 0},
    {"_silenced_humanoid_rare_", 2, 0, 0},
    {"_silenced_humanoid_rare_", 3, 0, 0},
    {"_snorg_common_", 0, 0, 0},
    {"_snorg_common_", 1, 0, 0},
    {"_snorg_common_", 2, 0, 0},
    {"_snorg_common_", 3, 0, 0},
    {"_snorg_common_", 4, 0, 0},
    {"_sojobo_common_", 0, 0, 0},
    {"_sojobo_common_", 2, 0, 0},
    {"_sojobo_common_", 4, 0, 0},
    {"_sonja_common_", 2, 0, 0},
    {"_sonja_common_", 3, 0, 0},
    {"_sonja_common_", 4, 0, 0},
    {"_spectator_speech_", 4, 0, 0},
    {"_spectator_speech_", 5, 0, 0},
    {"_spectator_speech_", 6, 0, 0},
    {"_spectator_speech_", 7, 0, 0},
    {"_spectator_speech_", 8, 0, 0},
    {"_terence_common_", 0, 0, 0},
    {"_terence_common_", 1, 0, 0},
    {"_terence_common_", 2, 0, 0},
    {"_tormentor_common_", 1, 0, 0},
    {"_tormentor_common_", 2, 0, 0},
    {"_tormentor_common_", 3, 0, 0},
    {"_urug_common_", 1, 0, 0},
    {"_urug_common_", 2, 0, 0},
    {"_urug_common_", 3, 0, 0},
    {"_urug_rare_", 0, 0, 0},
    {"_vashnia_common_", 0, 0, 0},
    {"_vashnia_common_", 1, 0, 0},
    {"_vashnia_common_", 2, 0, 0},
    {"_vashnia_common_", 3, 0, 0},
    {"_vashnia_common_", 4, 0, 0},
    {"_wiglaf_common_", 6, 0, 0},
    {"_wizard_medium_", 0, 0, 0},
    {"_wizard_medium_", 1, 0, 0},
    {"_xtahua_common_", 1, 0, 0},
    {"_zenata_common_", 0, 0, 0},
    {"_zenata_common_", 2, 0, 0},
    {"air magic player ghost", 0, 0, 0},
    {"alderking", 0, 0, 0},
    {"alderking", 1, 0, 0},
    {"bennu", 0, 0, 0},
    {"bennu", 1, 0, 0},
    {"bennu permanently killed", 0, 0, 0},
    {"brain worm", 0, 0, 0},
    {"brain worm", 1, 0, 0},
    {"brain worm", 2, 0, 0},
    {"catoblepas", 2, 0, 0},
    {"catoblepas", 3, 0, 0},
    {"centipede", 0, 0, 0},
    {"chaos spawn", 0, 0, 0},
    {"chaos spawn", 1, 0, 0},
    {"chaos spawn", 2, 0, 0},
    {"cognitogaunt", 0, 0, 0},
    {"confused crazy yiuf", 2, 0, 0},
    {"confused crazy yiuf", 8, 0, 0},
    {"confused ijyb", 7, 0, 0},
    {"confused zin angel", 3, 0, 0},
    {"conjurations player ghost", 0, 0, 0},
    {"conjurations player ghost", 3, 0, 0},
    {"conjurations player ghost", 4, 0, 0},
    {"crossbows player ghost", 1, 0, 0},
    {"crystal guardian", 0, 0, 0},
    {"crystal guardian", 1, 0, 0},
    {"default 'cap-g'", 0, 0, 0},
    {"default 'cap-j'", 0, 0, 0},
    {"default confused 'b'", 0, 0, 0},
    {"default confused 'r'", 0, 0, 0},
    {"default confused arachnid", 0, 0, 0},
    {"default confused centipede", 0, 0, 0},
    {"default confused centipede", 1, 0, 0},
    {"default confused insect", 0, 0, 0},
    {"default confused insect", 1, 0, 0},
    {"default confused winged insect", 0, 0, 0},
    {"default confused winged insect", 1, 0, 0},
    {"default confused winged insect", 2, 0, 0},
    {"default hoarfrost cannon", 0, 0, 0},
    {"default hoarfrost cannon", 1, 0, 0},
    {"default hostile confused donald", 9, 0, 0},
    {"default hostile confused donald", 10, 0, 0},
    {"default hostile confused donald", 11, 0, 0},
    {"default hostile confused donald", 12, 0, 0},
    {"default ice statue", 0, 0, 0},
    {"default insect", 0, 0, 0},
    {"default mennas", 0, 0, 0},
    {"default mennas", 1, 0, 0},
    {"default mennas", 2, 0, 0},
    {"default mennas", 3, 0, 0},
    {"default obsidian statue", 0, 0, 0},
    {"default orange crystal statue", 0, 0, 0},
    {"default silenced confused 'y'", 0, 0, 0},
    {"default silenced confused humanoid", 0, 0, 0},
    {"default silenced confused humanoid", 1, 0, 0},
    {"default silenced confused humanoid", 2, 0, 0},
    {"default silenced confused humanoid", 3, 0, 0},
    {"default silenced confused humanoid", 4, 0, 0},
    {"default silenced confused humanoid", 5, 0, 0},
    {"deformed humanoid", 0, 0, 0},
    {"deformed humanoid", 1, 0, 0},
    {"deformed humanoid", 2, 0, 0},
    {"deformed humanoid", 3, 0, 0},
    {"deformed humanoid", 5, 0, 0},
    {"deformed humanoid", 7, 0, 0},
    {"deformed humanoid", 8, 0, 0},
    {"deformed humanoid", 9, 0, 0},
    {"deformed humanoid", 12, 0, 0},
    {"deformed humanoid", 15, 0, 0},
    {"deformed humanoid", 19, 0, 0},
    {"deformed humanoid", 20, 0, 0},
    {"deformed humanoid", 21, 0, 0},
    {"deformed humanoid", 22, 0, 0},
    {"deformed humanoid", 23, 0, 0},
    {"deformed humanoid", 24, 0, 0},
    {"deformed humanoid", 25, 0, 0},
    {"deformed humanoid", 26, 0, 0},
    {"deformed humanoid", 28, 0, 0},
    {"dowan_duvessa_dies", 1, 0, 0},
    {"duvessa_dowan_dies", 2, 0, 0},
    {"earth magic player ghost", 2, 0, 0},
    {"elephant slug", 0, 0, 0},
    {"erythrospite", 0, 0, 0},
    {"eustachio triumphant", 0, 0, 0},
    {"fighting player ghost", 1, 0, 0},
    {"fleeing dowan", 0, 0, 0},
    {"friendly hound", 0, 0, 0},
    {"friendly hound", 1, 0, 0},
    {"friendly hound", 2, 0, 0},
    {"friendly hound", 3, 0, 0},
    {"friendly hound", 3, 1, 0},
    {"friendly hound", 4, 0, 0},
    {"friendly hound", 5, 0, 0},
    {"friendly hound", 6, 0, 0},
    {"friendly hound", 7, 0, 0},
    {"friendly shoals hound", 1, 0, 0},
    {"friendly shoals hound", 2, 0, 0},
    {"friendly shoals hound", 2, 1, 0},
    {"friendly shoals hound", 3, 0, 0},
    {"goblin sharper", 0, 0, 0},
    {"goblin sharper", 1, 0, 0},
    {"goblin sharper", 2, 0, 0},
    {"goblin sharper", 3, 0, 0},
    {"gozag player ghost", 0, 0, 0},
    {"holy_being_pacification", 0, 0, 0},
    {"holy_being_pacification_humanoid", 1, 0, 0},
    {"holy_being_pacification_humanoid", 2, 0, 0},
    {"hound", 0, 0, 0},
    {"ice magic player ghost", 0, 0, 0},
    {"ignis player ghost", 1, 0, 0},
    {"invocations player ghost", 5, 0, 0},
    {"josephine", 0, 0, 0},
    {"josephine", 1, 0, 0},
    {"josephine", 2, 0, 0},
    {"killer klown triumphant", 0, 0, 0},
    {"killer klown triumphant", 2, 0, 0},
    {"kirke", 0, 0, 0},
    {"kirke", 1, 0, 0},
    {"kobold blastminer", 0, 0, 0},
    {"kobold blastminer", 1, 0, 0},
    {"long blades player ghost", 0, 0, 0},
    {"maces & flails player ghost", 1, 0, 0},
    {"moth of wrath", 0, 0, 0},
    {"natasha triumphant", 0, 0, 0},
    {"natasha triumphant", 1, 0, 0},
    {"nekomata", 0, 1, 0},
    {"nekomata", 1, 1, 0},
    {"nekomata", 1, 2, 0},
    {"nekomata", 2, 1, 0},
    {"nergalle", 2, 0, 0},
    {"nergalle", 3, 0, 0},
    {"obsidian bat", 0, 0, 0},
    {"orc donald", 7, 0, 0},
    {"orc_apostle_unbanished", 0, 0, 0},
    {"orc_apostle_unbanished", 7, 0, 0},
    {"protean progenitor", 0, 0, 0},
    {"protean progenitor", 1, 0, 0},
    {"protean progenitor", 2, 0, 0},
    {"protean progenitor", 3, 0, 0},
    {"ranged weapons player ghost", 2, 0, 0},
    {"ranged weapons player ghost", 3, 0, 0},
    {"reaper", 1, 0, 0},
    {"reaper", 2, 0, 0},
    {"reaper", 6, 0, 0},
    {"sewer brain worm", 1, 0, 0},
    {"shapeshifting player ghost", 1, 0, 0},
    {"shapeshifting player ghost", 2, 0, 0},
    {"short blades player ghost", 2, 0, 0},
    {"sigmund triumphant", 0, 0, 0},
    {"silenced cognitogaunt", 0, 0, 0},
    {"silenced murray", 0, 0, 0},
    {"silenced murray", 1, 0, 0},
    {"silenced murray", 2, 0, 0},
    {"silenced murray", 3, 0, 0},
    {"silenced murray", 4, 0, 0},
    {"silenced murray", 5, 0, 0},
    {"silenced player ghost", 0, 0, 0},
    {"silenced player ghost", 1, 0, 0},
    {"silenced player ghost", 2, 0, 0},
    {"silenced silent spectre", 0, 0, 0},
    {"silenced silent spectre", 1, 0, 0},
    {"silenced silent spectre", 2, 0, 0},
    {"silenced silent spectre", 3, 0, 0},
    {"silenced silent spectre", 4, 0, 0},
    {"silenced silent spectre", 5, 0, 0},
    {"silenced zin angel", 0, 0, 0},
    {"silenced zin angel", 1, 0, 0},
    {"silenced zin angel", 2, 0, 0},
    {"silenced zin angel", 3, 0, 0},
    {"silent jory killed", 0, 0, 0},
    {"slings player ghost", 1, 0, 0},
    {"sonja triumphant", 0, 0, 0},
    {"sonja triumphant", 1, 0, 0},
    {"spellcasting player ghost", 4, 0, 0},
    {"spellcasting player ghost", 5, 0, 0},
    {"staves player ghost", 1, 0, 0},
    {"stealth player ghost", 0, 0, 0},
    {"stealth player ghost", 1, 0, 0},
    {"stealth player ghost", 2, 0, 0},
    {"stealth player ghost", 3, 0, 0},
    {"stealth player ghost", 5, 0, 0},
    {"summonings player ghost", 1, 0, 0},
    {"thermic dynamo", 0, 0, 0},
    {"thermic dynamo", 1, 0, 0},
    {"throwing player ghost", 0, 0, 0},
    {"translocations player ghost", 0, 0, 0},
    {"translocations player ghost", 1, 0, 0},
    {"translocations player ghost", 2, 0, 0},
    {"twin_banished dowan", 0, 0, 0},
    {"twin_banished duvessa", 0, 0, 0},
    {"twin_banished duvessa", 1, 0, 0},
    {"twin_died dowan", 0, 0, 0},
    {"twin_died duvessa", 0, 0, 0},
    {"twin_died duvessa", 1, 0, 0},
    {"twin_died duvessa", 6, 0, 0},
    {"twin_ikilled dowan", 0, 0, 0},
    {"twin_ikilled duvessa", 0, 0, 0},
    {"twin_slimified dowan", 0, 0, 0},
    {"unarmed combat player ghost", 1, 0, 0},
    {"unarmed combat player ghost", 2, 0, 0},
    {"unarmed combat player ghost", 4, 0, 0},
    {"unarmed combat player ghost", 5, 0, 0},
    {"xak'krixis", 4, 0, 0},
    {"xak'krixis", 5, 0, 0},
    {"xom crazy yiuf", 11, 0, 0},
    {"xom crazy yiuf", 12, 0, 0},
    {"xom crazy yiuf", 13, 0, 0},
    {"xom crazy yiuf", 14, 0, 0},
    {"xtahua triumphant", 1, 0, 0},
};

// CR-019/CR-023/CR-024: getSpeakString recursively expands every
// in-family ``@token@`` marker of the selected pattern -- including
// markers inside Lua return literals -- before evaluating the embedded
// Lua blocks and splicing the returned string into the message, so each
// literal ``return "..."`` branch of a ``{{...}}`` block is a fully
// expanded runtime message.  These helpers mirror
// monspeak_inventory._lua_return_branch_lines exactly: per-block branch
// extraction reuses the strict ``return`` scan of
// _lua_block_protocol (CR-002), per-branch expansion enumerates every
// reachable variant of every referenced in-family fragment with the
// production recursive-replacement semantics and limits (database.cc
// MAX_RECURSION_DEPTH 10 / MAX_REPLACEMENTS 100), and the sink layout
// resolves each line's channel through the production resolver.  Blocks
// without literal returns (the you.race()/you.genus() display mappings)
// keep the colon-free, newline-free ``{{LUA}}`` placeholder, identical
// to the pre-CR-023 neutralization.  Unsupported escapes fail the
// literal evaluation (REQUIRE at the call site) so the runtime text is
// never guessed.
static bool monspeak_unescape_lua_literal(const string &body, string &out)
{
    out.clear();
    for (size_t i = 0; i < body.size(); ++i)
    {
        if (body[i] != '\\')
        {
            out.push_back(body[i]);
            continue;
        }
        if (++i >= body.size())
            return false;
        switch (body[i])
        {
        case 'a': out.push_back('\a'); break;
        case 'b': out.push_back('\b'); break;
        case 'f': out.push_back('\f'); break;
        case 'n': out.push_back('\n'); break;
        case 'r': out.push_back('\r'); break;
        case 't': out.push_back('\t'); break;
        case 'v': out.push_back('\v'); break;
        case '\\': out.push_back('\\'); break;
        case '\'': out.push_back('\''); break;
        case '"': out.push_back('"'); break;
        case 'x':
        {
            if (i + 2 >= body.size())
                return false;
            auto hex = [](char c) -> int {
                if (c >= '0' && c <= '9') return c - '0';
                if (c >= 'a' && c <= 'f') return c - 'a' + 10;
                if (c >= 'A' && c <= 'F') return c - 'A' + 10;
                return -1;
            };
            const int hi = hex(body[i + 1]);
            const int lo = hex(body[i + 2]);
            if (hi < 0 || lo < 0)
                return false;
            out.push_back(static_cast<char>(hi * 16 + lo));
            i += 2;
            break;
        }
        case 'z':
            while (i + 1 < body.size()
                   && (body[i + 1] == ' ' || body[i + 1] == '\t'
                       || body[i + 1] == '\n' || body[i + 1] == '\r'
                       || body[i + 1] == '\f' || body[i + 1] == '\v'))
                ++i;
            break;
        default:
            if (body[i] >= '0' && body[i] <= '9')
            {
                int value = 0;
                size_t digits = 0;
                while (digits < 3 && i + digits < body.size()
                       && body[i + digits] >= '0'
                       && body[i + digits] <= '9')
                {
                    value = value * 10 + (body[i + digits] - '0');
                    ++digits;
                }
                if (value > 255)
                    return false;
                out.push_back(static_cast<char>(value));
                i += digits - 1;
                break;
            }
            return false;
        }
    }
    return true;
}

// The runtime string value of one Lua return expression: a ``[[ ]]``
// long string (no escape processing) or a quoted literal (escape
// processing); anything else (the declared display mappings) has no
// statically known text and yields false.
static bool monspeak_lua_literal_value(const string &expression,
                                       string &out)
{
    const string::size_type begin = expression.find_first_not_of(" \t");
    const string::size_type end = expression.find_last_not_of(" \t");
    if (begin == string::npos)
        return false;
    const string expr = expression.substr(begin, end - begin + 1);
    if (expr.size() >= 4 && expr.compare(0, 2, "[[") == 0)
    {
        if (expr.compare(expr.size() - 2, 2, "]]") != 0)
            return false;
        out = expr.substr(2, expr.size() - 4);
        return true;
    }
    if (expr.size() >= 2 && (expr[0] == '"' || expr[0] == '\'')
        && expr[expr.size() - 1] == expr[0])
    {
        return monspeak_unescape_lua_literal(
            expr.substr(1, expr.size() - 2), out);
    }
    return false;
}

// Runtime texts of the literal return branches of one ``{{...}}`` block,
// in source order (split_string trims every line, so the ``return``
// statement is detected on the trimmed line).  A multi-line ``[[ ]]``
// long string consumes its continuation lines.  Non-literal returns keep
// the ``{{LUA}}`` placeholder branch so branch counts stay aligned.
static vector<string> monspeak_lua_return_branch_texts(const string &block)
{
    vector<string> texts;
    const vector<string> lines = split_string("\n", block);
    size_t index = 0;
    while (index < lines.size())
    {
        if (!starts_with(lines[index], "return "))
        {
            ++index;
            continue;
        }
        string expression = lines[index].substr(strlen("return "));
        ++index;
        if (starts_with(expression, "[[")
            && expression.find("]]") == string::npos)
        {
            while (index < lines.size()
                   && lines[index].find("]]") == string::npos)
            {
                expression += "\n" + lines[index];
                ++index;
            }
            if (index < lines.size())
            {
                expression += "\n" + lines[index];
                ++index;
            }
        }
        string value;
        if (monspeak_lua_literal_value(expression, value))
            texts.push_back(value);
        else
            texts.push_back("{{LUA}}");
    }
    return texts;
}

// The production recursive-replacement limits and bail-out text
// (database.cc _getRandomisedStr / _call_recursive_replacement).
static constexpr int MONSPEAK_MAX_RECURSION_DEPTH = 10;
static constexpr int MONSPEAK_MAX_REPLACEMENTS = 100;
static const string MONSPEAK_TOO_MUCH_RECURSION = "TOO MUCH RECURSION";

// The same-language SpeakDB the production recursive expansion consults:
// canonical (lowercased) key -> variant raw patterns in ordinal order.
using monspeak_family_lookup = map<string, vector<string>>;

static monspeak_family_lookup monspeak_build_lookup(
    const vector<textdb_phase0::canonical_entry> &entries)
{
    monspeak_family_lookup lookup;
    for (const textdb_phase0::canonical_entry &entry : entries)
    {
        vector<string> patterns;
        for (const textdb_phase0::canonical_variant &variant
             : entry.variants)
            patterns.push_back(variant.raw_pattern);
        lookup[entry.canonical_key] = move(patterns);
    }
    return lookup;
}

// All fully expanded runtime texts of ``text`` under the production
// recursive-replacement semantics (CR-024), each with its replacement
// count: every ``@marker@`` site increments the replacement count and a
// site beyond MAX_REPLACEMENTS stops the scan; an unbalanced ``@`` stops
// the scan; a marker that is not an in-family key is left alone and the
// scan continues after it; an in-family marker is replaced by every
// reachable variant of its key (each fully expanded at depth + 1, with
// the bail-out text past MAX_RECURSION_DEPTH) and the scan resumes at
// the splice point.  Mirrors monspeak_inventory._family_expansions.
static void monspeak_family_expansions(
    const string &text, const monspeak_family_lookup &lookup,
    int depth, int replacements, vector<pair<string, int>> &out)
{
    if (depth > MONSPEAK_MAX_RECURSION_DEPTH)
    {
        out.emplace_back(MONSPEAK_TOO_MUCH_RECURSION, replacements);
        return;
    }
    const string::size_type pos = text.find("@");
    if (pos == string::npos)
    {
        out.emplace_back(text, replacements);
        return;
    }
    ++replacements;
    if (replacements > MONSPEAK_MAX_REPLACEMENTS)
    {
        out.emplace_back(text, replacements);
        return;
    }
    const string::size_type end = text.find("@", pos + 1);
    if (end == string::npos)
    {
        out.emplace_back(text, replacements);
        return;
    }
    const string marker = text.substr(pos + 1, end - pos - 1);
    const string canonical = lowercase_string(marker);
    const string marker_full = text.substr(pos, end - pos + 1);
    const string prefix = text.substr(0, pos);
    const string suffix = text.substr(end + 1);
    const auto found = lookup.find(canonical);
    if (found == lookup.end())
    {
        vector<pair<string, int>> rest;
        monspeak_family_expansions(suffix, lookup, depth, replacements,
                                   rest);
        for (const auto &item : rest)
            out.emplace_back(prefix + marker_full + item.first,
                             item.second);
        return;
    }
    for (const string &variant : found->second)
    {
        vector<pair<string, int>> children;
        monspeak_family_expansions(variant, lookup, depth + 1,
                                   replacements, children);
        for (const auto &child : children)
        {
            vector<pair<string, int>> rescanned;
            monspeak_family_expansions(prefix + child.first + suffix,
                                       lookup, depth, child.second,
                                       rescanned);
            for (auto &item : rescanned)
                out.push_back(move(item));
        }
    }
}

// Per-return-branch fully expanded runtime texts of one ``{{...}}``
// block, in source order (CR-024): the strict branch extraction of
// ``monspeak_lua_return_branch_texts``, then ``_family_expansions`` over
// the same-language in-family lookup for every literal return.  Each
// branch maps to its sorted-unique outcome text set (every reachable
// variant of every referenced fragment); a literal without in-family
// tokens maps to exactly one text; the declared display mappings keep
// the ``{{LUA}}`` placeholder branch so branch counts stay aligned.
static vector<vector<string>> monspeak_lua_return_branch_expansions(
    const string &block, const monspeak_family_lookup &lookup)
{
    vector<vector<string>> expansions;
    for (const string &text : monspeak_lua_return_branch_texts(block))
    {
        set<string> outcomes;
        vector<pair<string, int>> expanded;
        monspeak_family_expansions(text, lookup, 2, 0, expanded);
        for (const auto &item : expanded)
            outcomes.insert(item.first);
        expansions.push_back(vector<string>(outcomes.begin(),
                                            outcomes.end()));
    }
    return expansions;
}

// The per-line channel sequence of one fully expanded runtime message
// under the production sink split and resolver.
using monspeak_layout = vector<msg_channel_type>;

static monspeak_layout monspeak_message_layout(const string &message)
{
    monspeak_layout layout;
    for (const string &line : split_string("\n", message))
    {
        msg_channel_type channel = MSGCH_TALK;
        string rendered = line;
        resolve_mon_speech_line_channel(rendered, channel, false, false);
        layout.push_back(channel);
    }
    return layout;
}

// Per-branch-combination sorted-unique layout sets of one pattern
// (CR-023/CR-024): the branch combinations are the cross product over
// the per-site return branches (the last site varies fastest, matching
// the Python itertools.product), and each branch's layout set deduplicates
// over the per-branch outcome cross product.  An unbalanced ``{{`` site
// (a split-Lua fragment in isolation) keeps the placeholder branch.
using monspeak_layout_set = set<monspeak_layout>;

static void monspeak_join_outcomes_rec(
    const vector<vector<vector<string>>> &segments,
    const vector<size_t> &branch_choices, size_t segment_index,
    string &current, monspeak_layout_set &out)
{
    if (segment_index == segments.size())
    {
        out.insert(monspeak_message_layout(current));
        return;
    }
    const vector<string> &outcomes =
        segments[segment_index][branch_choices[segment_index]];
    const size_t base = current.size();
    for (const string &text : outcomes)
    {
        current += text;
        monspeak_join_outcomes_rec(segments, branch_choices,
                                   segment_index + 1, current, out);
        current.resize(base);
    }
}

static void monspeak_branch_combinations_rec(
    const vector<vector<vector<string>>> &segments, size_t index,
    vector<size_t> &choices, vector<monspeak_layout_set> &out)
{
    if (index == segments.size())
    {
        monspeak_layout_set layouts;
        string current;
        monspeak_join_outcomes_rec(segments, choices, 0, current,
                                   layouts);
        out.push_back(move(layouts));
        return;
    }
    for (size_t branch = 0; branch < segments[index].size(); ++branch)
    {
        choices.push_back(branch);
        monspeak_branch_combinations_rec(segments, index + 1, choices,
                                         out);
        choices.pop_back();
    }
}

static vector<monspeak_layout_set> monspeak_lua_branch_layouts(
    const string &pattern, const monspeak_family_lookup &lookup)
{
    vector<vector<vector<string>>> segments;
    string::size_type pos = 0;
    string::size_type site;
    while ((site = pattern.find("{{", pos)) != string::npos)
    {
        segments.push_back({{pattern.substr(pos, site - pos)}});
        const string::size_type end = pattern.find("}}", site + 2);
        if (end == string::npos)
        {
            segments.push_back({{"{{LUA}}"}});
            pos = pattern.size();
            break;
        }
        segments.push_back(monspeak_lua_return_branch_expansions(
            pattern.substr(site + 2, end - site - 2), lookup));
        pos = end + 2;
    }
    segments.push_back({{pattern.substr(pos)}});
    vector<monspeak_layout_set> layouts;
    vector<size_t> choices;
    monspeak_branch_combinations_rec(segments, 0, choices, layouts);
    return layouts;
}

TEST_CASE("Issue 16 monspeak VISUAL channels survive the review at EN-aligned lines",
          "[single-file][textdb][phase0][issue-16][issue-70][monspeak]")
{
    ensure_test_data_root();
    databaseSystemInit();
    const textdb_phase0::canonical_speakdb_dump english =
        textdb_phase0::dump_canonical_english_speakdb_typed();
    const vector<textdb_phase0::canonical_entry> localized =
        textdb_phase0::dump_localized_speakdb_typed("zh").entries;

    // CR-004/CR-008/CR-019/CR-023/CR-024: the Issue-16 monspeak VISUAL
    // contract is validated at the production sink granularity.
    // mons_speaks_msg splits every selected pattern by '\n' (split_string
    // with trimming and empty-segment dropping) and resolves each line
    // through resolve_mon_speech_line_channel with the MSGCH_TALK
    // default; the frozen identity is the (canonical key, variant
    // ordinal, Lua return branch ordinal, line ordinal) set of the EN
    // lines that resolve to the VISUAL channel.  The branch ordinal
    // (CR-023/CR-024) expands every literal ``return "VISUAL:..."``
    // emission of a ``{{...}}`` block: getSpeakString recursively
    // expands in-family @token@ markers -- including markers inside Lua
    // return literals -- before evaluating the block, so each fully
    // expanded branch is a possible runtime message and participates in
    // the frozen set.  The aligned ZH dump must reproduce the same
    // branch count and the same per-branch expanded layout set, and
    // resolve every corresponding line -- including non-VISUAL lines --
    // to the same channel.
    const monspeak_family_lookup en_lookup =
        monspeak_build_lookup(english.entries);
    const monspeak_family_lookup zh_lookup =
        monspeak_build_lookup(localized);
    set<string> frozen_visual;
    for (const frozen_monspeak_visual_line &position
             : FROZEN_MONSPEAK_EN_VISUAL)
    {
        frozen_visual.insert(string(position.key) + "\n"
                             + to_string(position.ordinal) + "\n"
                             + to_string(position.branch) + "\n"
                             + to_string(position.line));
    }
    REQUIRE(frozen_visual.size() == 506);

    set<string> derived_visual;
    for (const textdb_phase0::canonical_entry &entry : english.entries)
    {
        if (!has_source_history(entry, "database/monspeak.txt"))
            continue;
        const textdb_phase0::canonical_entry *zh_entry =
            find_canonical_entry(localized, entry.canonical_key);
        REQUIRE(zh_entry != nullptr);
        for (size_t ordinal = 0; ordinal < entry.variants.size();
             ++ordinal)
        {
            const vector<monspeak_layout_set> en_branches =
                monspeak_lua_branch_layouts(
                    entry.variants[ordinal].raw_pattern, en_lookup);
            bool has_visual = false;
            for (size_t branch = 0; branch < en_branches.size(); ++branch)
            {
                for (const monspeak_layout &layout
                     : en_branches[branch])
                {
                    for (size_t line = 0; line < layout.size(); ++line)
                    {
                        if (layout[line] != MSGCH_TALK_VISUAL)
                            continue;
                        has_visual = true;
                        derived_visual.insert(entry.canonical_key + "\n"
                                              + to_string(ordinal) + "\n"
                                              + to_string(branch) + "\n"
                                              + to_string(line));
                    }
                }
            }
            const bool lua_bearing =
                entry.variants[ordinal].raw_pattern.find("{{")
                != string::npos;
            if (!has_visual && !lua_bearing)
                continue;
            // CR-013: every EN VISUAL line must exist in ZH at the same
            // canonical key and ordinal.  A trailing EN-aligned VISUAL
            // ordinal deleted from ZH (the ZH variant list ends early)
            // must fail here instead of being silently skipped by a
            // min-range loop.
            REQUIRE(ordinal < zh_entry->variants.size());
            const vector<monspeak_layout_set> zh_branches =
                monspeak_lua_branch_layouts(
                    zh_entry->variants[ordinal].raw_pattern, zh_lookup);
            // CR-023/CR-024: the branch count must match EN.  A deleted
            // return branch (``friendly shoals hound`` #2) changes the
            // runtime branch topology and fails here even when every
            // remaining line is still VISUAL.
            REQUIRE(zh_branches.size() == en_branches.size());
            for (size_t branch = 0; branch < en_branches.size(); ++branch)
            {
                INFO(entry.canonical_key << " #" << ordinal
                     << " branch " << branch);
                if (en_branches[branch].size() == 1
                    && zh_branches[branch].size() == 1)
                {
                    // CR-019: the runtime newline layout must match line
                    // for line, and every corresponding line (including
                    // non-VISUAL lines and lines that strip to empty)
                    // must resolve to the same channel as the EN line
                    // through the production resolver.  A line shift
                    // inside a pattern, a newline position change or a
                    // changed VISUAL prefix in a Lua return (CR-023)
                    // fails here even when the frozen EN set is
                    // untouched.
                    const monspeak_layout &en_layout =
                        *en_branches[branch].begin();
                    const monspeak_layout &zh_layout =
                        *zh_branches[branch].begin();
                    REQUIRE(zh_layout.size() == en_layout.size());
                    for (size_t line = 0; line < en_layout.size(); ++line)
                    {
                        INFO(entry.canonical_key << " #" << ordinal
                             << " branch " << branch << " line " << line);
                        CHECK(zh_layout[line] == en_layout[line]);
                    }
                    continue;
                }
                // CR-024: expanded branches (literal returns referencing
                // in-family fragments) compare their complete sorted-
                // unique layout sets: every reachable variant of every
                // referenced fragment must resolve to the same set of
                // per-line channel sequences as EN.  A VISUAL prefix
                // added to one ZH variant of a referenced fragment
                // (``_Sprozz_common_``) fails here even though the
                // unexpanded return literal is identical on both sides.
                CHECK(zh_branches[branch] == en_branches[branch]);
            }
        }
    }
    // The complete EN VISUAL line set is frozen (CR-008/CR-019/CR-023):
    // a removed, reworded or moved EN VISUAL line, a changed VISUAL
    // prefix inside a Lua return or a deleted Lua return branch must fail
    // even when the total stays at 506 and the per-line ZH check is
    // mirrored.  Both set directions are required so a missing line
    // cannot be hidden by an extra one at another key/ordinal/branch/
    // line.
    CHECK(derived_visual.size() == frozen_visual.size());
    for (const string &position : derived_visual)
    {
        INFO(position);
        CHECK(frozen_visual.count(position) == 1);
    }
    for (const string &position : frozen_visual)
    {
        INFO(position);
        CHECK(derived_visual.count(position) == 1);
    }
}

TEST_CASE("Issue 70 recursive tokens inside Lua returns bind the expanded ZH topology",
          "[single-file][textdb][phase0][issue-70][monspeak]")
{
    ensure_test_data_root();
    databaseSystemInit();
    const textdb_phase0::canonical_speakdb_dump english =
        textdb_phase0::dump_canonical_english_speakdb_typed();
    vector<textdb_phase0::canonical_entry> localized =
        textdb_phase0::dump_localized_speakdb_typed("zh").entries;

    // CR-024: the reviewer probe.  ``Sprozz`` returns the in-family
    // fragments @_Sprozz_thief_@ / @_Sprozz_common_@ from its Lua block;
    // production (database.cc) expands every @token@ marker of the
    // selected pattern BEFORE evaluating the Lua block, so each return
    // branch's runtime layout set enumerates every reachable fragment
    // variant.  Adding a VISUAL prefix to one ZH variant of
    // _sprozz_common_ must change the ZH layout set while the unexpanded
    // return literal (and every pre-CR-024 fact) stays identical, so a
    // gate that does not expand recursive tokens cannot reject the
    // mutation.
    const monspeak_family_lookup en_lookup =
        monspeak_build_lookup(english.entries);
    textdb_phase0::canonical_entry *sprozz_common =
        find_canonical_entry_mutable(localized, "_sprozz_common_");
    REQUIRE(sprozz_common != nullptr);
    REQUIRE(!sprozz_common->variants.empty());
    sprozz_common->variants[0].raw_pattern =
        "VISUAL:" + sprozz_common->variants[0].raw_pattern;
    const monspeak_family_lookup zh_lookup =
        monspeak_build_lookup(localized);

    const textdb_phase0::canonical_entry *en_sprozz =
        find_canonical_entry(english.entries, "sprozz");
    const textdb_phase0::canonical_entry *zh_sprozz =
        find_canonical_entry(localized, "sprozz");
    REQUIRE(en_sprozz != nullptr);
    REQUIRE(zh_sprozz != nullptr);
    const vector<monspeak_layout_set> en_branches =
        monspeak_lua_branch_layouts(en_sprozz->variants[0].raw_pattern,
                                    en_lookup);
    const vector<monspeak_layout_set> zh_branches =
        monspeak_lua_branch_layouts(zh_sprozz->variants[0].raw_pattern,
                                    zh_lookup);
    REQUIRE(zh_branches.size() == en_branches.size());
    // The @_Sprozz_thief_@ branch is untouched on both sides: every EN
    // and ZH thief fragment resolves to a single talk layout.
    CHECK(zh_branches[0] == en_branches[0]);
    // The @_Sprozz_common_@ branch gains the talk_visual layout in ZH:
    // the mutated fragment variant starts with VISUAL: and production
    // expands it before the Lua block runs, so the return emits a VISUAL
    // channel line.  Without token expansion both branches' literals are
    // byte-identical, so this difference is exactly the CR-024 blind
    // spot the expanded topology closes.
    REQUIRE(en_branches[1].size() == 1);
    REQUIRE(en_branches[1].count(monspeak_layout(1, MSGCH_TALK)) == 1);
    REQUIRE(zh_branches[1].size() == 2);
    REQUIRE(zh_branches[1].count(monspeak_layout(1, MSGCH_TALK_VISUAL))
            == 1);
    CHECK(zh_branches[1] != en_branches[1]);
}

TEST_CASE("Phase 0 legacy EN and ZH database traces expose known drift",
          "[single-file][textdb][phase0]")
{
    ensure_test_data_root();
    databaseSystemInit();
    const vector<textdb_phase0::canonical_entry> canonical =
        textdb_phase0::dump_canonical_english_speakdb();
    const vector<textdb_phase0::canonical_entry> localized =
        textdb_phase0::dump_localized_speakdb_typed("zh").entries;
    const vector<textdb_phase0::canonical_entry> merged =
        merge_localized_speakdb(canonical, localized);

    vector<string> roots;
    for (const textdb_phase0::canonical_entry &entry : canonical)
    {
        if (std::any_of(entry.source_history.begin(),
                        entry.source_history.end(),
            [](const textdb_phase0::source_provenance &source)
            {
                return source.source_name == "database/monspell.txt";
            }))
        {
            roots.push_back(entry.canonical_key);
        }
    }
    REQUIRE(roots.size() == 262);
    const set<string> canonical_reachable =
        statically_reachable_weighted_keys(canonical, roots);
    const set<string> localized_reachable =
        statically_reachable_weighted_keys(merged, roots);
    REQUIRE_FALSE(canonical_reachable.empty());
    REQUIRE_FALSE(localized_reachable.empty());

    const set<string> guardian_roots =
    {
        "guardian serpent cast",
        "guardian serpent cast targeted",
    };
    const set<string> unseen_roots =
    {
        "unseen acid splash cast",
        "unseen chilling breath cast",
        "unseen cold breath cast",
        "unseen fire breath cast",
        "unseen searing breath cast",
        "unseen spit acid cast",
        "unseen spit poison cast",
    };
    set<string> expected_different = guardian_roots;
    expected_different.insert(unseen_roots.begin(), unseen_roots.end());

    set<string> dynamic_different;
    set<string> guardian_top_difference;
    set<string> unseen_recursive_rng_difference;
    map<string, set<size_t>> canonical_observed;
    map<string, set<size_t>> localized_observed;

    // This deliberately covers only database selection, @key@ recursion, and
    // embedded Lua. Target resolution and legacy [a|b] materialization occur
    // later and are not part of this dynamic-difference proof.
    for (uint64_t seed = 0; seed < 4096; ++seed)
    {
        for (const string &root : roots)
        {
            const database_trace_run en =
                run_database_trace(canonical, root, seed);
            const database_trace_run zh =
                run_database_trace(merged, root, seed);
            record_selected_variants(en.trace, canonical_observed);
            record_selected_variants(zh.trace, localized_observed);

            const bool same = en.status == zh.status
                && same_database_trace(en.trace, zh.trace)
                && en.rng_state == zh.rng_state
                && en.rng_count == zh.rng_count;
            if (same)
                continue;
            dynamic_different.insert(root);

            if (guardian_roots.count(root)
                && !en.trace.weighted_choices.empty()
                && !zh.trace.weighted_choices.empty())
            {
                const textdb_phase0::weighted_choice_trace &a =
                    en.trace.weighted_choices.front();
                const textdb_phase0::weighted_choice_trace &b =
                    zh.trace.weighted_choices.front();
                if (a.total_bound != b.total_bound
                    || a.variant_ordinal != b.variant_ordinal
                    || a.weight != b.weight
                    || a.random_result != b.random_result)
                {
                    guardian_top_difference.insert(root);
                }
            }

            if (unseen_roots.count(root))
            {
                const bool recursive_selection_changed =
                    en.trace.weighted_choices.size()
                        != zh.trace.weighted_choices.size()
                    || en.trace.recursive_sites.size()
                        != zh.trace.recursive_sites.size();
                const bool rng_changed = en.rng_state != zh.rng_state
                    && en.rng_count != zh.rng_count;
                if (recursive_selection_changed && rng_changed)
                    unseen_recursive_rng_difference.insert(root);
            }
        }
    }

    CHECK(dynamic_different == expected_different);
    CHECK(guardian_top_difference == guardian_roots);
    CHECK(unseen_recursive_rng_difference == unseen_roots);
    // The seed range is accepted only if every statically selectable key in
    // the complete recursive closure was observed, with every ordinal hit.
    // Iterating only the observed map would silently miss an unvisited key.
    CHECK(observed_variants_cover_reachable(
        canonical, canonical_reachable, canonical_observed));
    CHECK(observed_variants_cover_reachable(
        merged, localized_reachable, localized_observed));

    vector<string> canonical_driven_roots(expected_different.begin(),
                                          expected_different.end());
    canonical_driven_roots.push_back("orb of entropy cast");
    bool canonical_driven_equal = true;
    for (uint64_t seed = 0; seed < 128 && canonical_driven_equal; ++seed)
    {
        for (const string &root : canonical_driven_roots)
        {
            // Simulated EN and ZH structured paths share the same canonical
            // selection/expansion. Pure localized rendering happens after
            // this trace and must not draw RNG (covered by the CASE_MAP test).
            const database_trace_run simulated_en =
                run_database_trace(canonical, root, seed);
            const database_trace_run simulated_zh =
                run_database_trace(canonical, root, seed);
            canonical_driven_equal =
                simulated_en.status == simulated_zh.status
                && same_database_trace(simulated_en.trace, simulated_zh.trace)
                && simulated_en.rng_state == simulated_zh.rng_state
                && simulated_en.rng_count == simulated_zh.rng_count;
            if (!canonical_driven_equal)
                break;
        }
    }
    CHECK(canonical_driven_equal);
}

TEST_CASE("Phase 0 canonical selection matches the English legacy path",
          "[single-file][textdb][phase0]")
{
    ensure_test_data_root();
    // Do not switch language or tear global DBs down: the helper below reads
    // only the canonical English SpeakDB base and ignores translation layers.
    databaseSystemInit();
    const vector<textdb_phase0::canonical_entry> entries =
        textdb_phase0::dump_canonical_english_speakdb();

    const vector<string> keys =
    {
        // Two top-level variants.
        "unseen laughing skull cast",
        // A real recursive entry: basilisk -> floating eye; the final
        // @The_monster@ runtime slot remains unresolved on both paths.
        "basilisk cast",
    };

    for (const string &key : keys)
    {
        DYNAMIC_SECTION(key)
        {
            for (uint64_t seed = 0; seed < 4096; ++seed)
            {
                INFO("seed=" << seed);
                const weighted_run legacy = run_legacy_speak_key(key, seed);
                const weighted_run canonical =
                    run_canonical_speak_key(entries, key, seed);
                CHECK(canonical.output == legacy.output);
                CHECK(canonical.rng_state == legacy.rng_state);
                CHECK(canonical.rng_count == legacy.rng_count);
                REQUIRE_FALSE(canonical.trace.weighted_choices.empty());
                const textdb_phase0::weighted_choice_trace &top =
                    canonical.trace.weighted_choices.front();
                CHECK(top.requested_key == key);
                CHECK(top.recursion_depth == 1);
                CHECK(top.replacement_count == 0);
                CHECK(top.recursion_path.empty());
                CHECK(top.total_bound > 0);
                CHECK(top.random_result >= 0);
                CHECK(top.random_result < top.total_bound);
                CHECK(top.variant_ordinal < 2);
                CHECK(top.after.current_count >= top.before.current_count);
                CHECK(top.before.global_counts.size()
                      == top.after.global_counts.size());

                for (const textdb_phase0::weighted_choice_trace &choice
                     : canonical.trace.weighted_choices)
                {
                    CHECK(choice.total_bound > 0);
                    CHECK(choice.random_result >= 0);
                    CHECK(choice.random_result < choice.total_bound);
                    CHECK(choice.weight > 0);
                    if (choice.recursion_depth == 1)
                        CHECK(choice.recursion_path.empty());
                    else
                        CHECK_FALSE(choice.recursion_path.empty());
                }

                if (key == "basilisk cast")
                {
                    REQUIRE(canonical.trace.recursive_sites.size() >= 2);
                    CHECK(canonical.trace.recursive_sites[0].marker
                          == "floating eye cast");
                    CHECK(canonical.trace.recursive_sites[0].recursion_path
                          == vector<size_t>{ 0 });
                    CHECK(canonical.trace.recursive_sites[0].status
                          == textdb_phase0::recursive_site_status::SELECTED);
                    CHECK(canonical.trace.recursive_sites[1].marker
                          == "The_monster");
                    CHECK(canonical.trace.recursive_sites[1].recursion_path
                          == (vector<size_t>{ 0, 0 }));
                    CHECK(canonical.trace.recursive_sites[1].status
                          == textdb_phase0::recursive_site_status::MISSING);
                    CHECK(canonical.output == "@The_monster@ looks around.");
                }
            }
        }
    }
}

TEST_CASE("Phase 0 message candidate prototype preserves search states",
          "[single-file][textdb][phase0]")
{
    using textdb_phase0::message_attempt;
    using textdb_phase0::message_result;
    using textdb_phase0::message_search_action;

    rng::subgenerator scoped_rng(0x1234, 0x5678);

    const textdb_phase0::message_candidate_evaluation missing =
        textdb_phase0::evaluate_message_candidate(
            {}, "missing", message_attempt::NORMAL_OR_UNSEEN, true);
    CHECK(missing.result == message_result::MISSING);
    CHECK(missing.trace.weighted_choices.empty());
    CHECK(missing.trace.recursive_sites.empty());
    CHECK(missing.trace.lua_sites.empty());
    CHECK_FALSE(missing.applicability_checked);
    CHECK_FALSE(missing.post_expansion_materialized);

    textdb_phase0::canonical_entry corrupt =
        make_canonical_entry("corrupt", "must not execute {{return 'lua'}}");
    corrupt.variants.clear();
    corrupt.parse_error = "BUG, CORRUPT ENTRY";
    const textdb_phase0::message_candidate_evaluation corrupt_result =
        textdb_phase0::evaluate_message_candidate(
            { corrupt }, "corrupt", message_attempt::NORMAL_OR_UNSEEN, true);
    CHECK(corrupt_result.result == message_result::CORRUPT);
    CHECK(corrupt_result.trace.weighted_choices.empty());
    CHECK(corrupt_result.trace.recursive_sites.empty());
    CHECK(corrupt_result.trace.lua_sites.empty());
    CHECK_FALSE(corrupt_result.post_expansion_materialized);

    textdb_phase0::canonical_entry corrupt_child =
        make_canonical_entry("child", "unreachable");
    corrupt_child.variants.clear();
    corrupt_child.parse_error = "BUG, CORRUPT CHILD";
    const vector<textdb_phase0::canonical_entry> recursive_corrupt_entries =
    {
        corrupt_child,
        make_canonical_entry("recursive", "before @child@ [left|right]"),
    };
    const textdb_phase0::raw_selection recursive_raw =
        textdb_phase0::select_canonical_english(
            recursive_corrupt_entries, "recursive");
    REQUIRE(recursive_raw.status
            == textdb_phase0::raw_selection_status::SELECTED);
    const textdb_phase0::expanded_selection recursive_expanded =
        textdb_phase0::expand_canonical_selection(
            recursive_corrupt_entries, recursive_raw);
    CHECK(recursive_expanded.status
          == textdb_phase0::raw_selection_status::CORRUPT);
    CHECK(recursive_expanded.text
          == "before BUG, CORRUPT CHILD [left|right]");
    REQUIRE(recursive_expanded.trace.recursive_sites.size() == 1);
    CHECK(recursive_expanded.trace.recursive_sites[0].status
          == textdb_phase0::recursive_site_status::CORRUPT);

    const textdb_phase0::message_candidate_evaluation recursive_corrupt =
        textdb_phase0::evaluate_message_candidate(
            recursive_corrupt_entries, "recursive",
            message_attempt::NORMAL_OR_UNSEEN, true);
    CHECK(recursive_corrupt.result == message_result::CORRUPT);
    CHECK(recursive_corrupt.expanded_text
          == "before BUG, CORRUPT CHILD [left|right]");
    CHECK_FALSE(recursive_corrupt.applicability_checked);
    CHECK_FALSE(recursive_corrupt.post_expansion_materialized);

    for (const string &pattern : {
             string("before @broken"),
             string("{{error('candidate lua failure')}}"),
             string("before {{return 'unterminated'") })
    {
        const textdb_phase0::message_candidate_evaluation structural_corrupt =
            textdb_phase0::evaluate_message_candidate(
                { make_canonical_entry("structural corrupt", pattern) },
                "structural corrupt", message_attempt::NORMAL_OR_UNSEEN,
                true);
        CHECK(structural_corrupt.result == message_result::CORRUPT);
        CHECK_FALSE(structural_corrupt.applicability_checked);
        CHECK_FALSE(structural_corrupt.post_expansion_materialized);
    }

    const vector<textdb_phase0::canonical_entry> inapplicable_entries =
    {
        make_canonical_entry("candidate",
                             "@child@ {{return 'after lua'}}"),
        make_canonical_entry("child", "expanded"),
    };
    const textdb_phase0::message_candidate_evaluation inapplicable =
        textdb_phase0::evaluate_message_candidate(
            inapplicable_entries, "candidate",
            message_attempt::NORMAL_OR_UNSEEN, false);
    CHECK(inapplicable.result == message_result::INAPPLICABLE);
    CHECK(inapplicable.expanded_text == "expanded after lua");
    CHECK(inapplicable.trace.weighted_choices.size() == 2);
    CHECK(inapplicable.trace.recursive_sites.size() == 1);
    REQUIRE(inapplicable.trace.lua_sites.size() == 1);
    CHECK(inapplicable.trace.lua_sites[0].status
          == textdb_phase0::lua_site_status::EXECUTED);
    CHECK(inapplicable.applicability_checked);
    CHECK_FALSE(inapplicable.post_expansion_materialized);

    const textdb_phase0::message_candidate_evaluation rendered =
        textdb_phase0::evaluate_message_candidate(
            { make_canonical_entry("rendered", "visible message") },
            "rendered", message_attempt::NORMAL_OR_UNSEEN, true);
    CHECK(rendered.result == message_result::RENDERED);
    CHECK(rendered.expanded_text == "visible message");
    CHECK(rendered.applicability_checked);
    CHECK_FALSE(rendered.post_expansion_materialized);

    const textdb_phase0::message_candidate_evaluation suppressed =
        textdb_phase0::evaluate_message_candidate(
            { make_canonical_entry("suppressed", "__NONE") },
            "suppressed", message_attempt::SILENT_PREFIXED, false);
    CHECK(suppressed.result == message_result::SUPPRESS);
    CHECK_FALSE(suppressed.applicability_checked);

    // The unprefixed silent fallback accepts any selected non-empty text and
    // intentionally bypasses the manifest/invalid_msg applicability check.
    const textdb_phase0::message_candidate_evaluation fallback =
        textdb_phase0::evaluate_message_candidate(
            { make_canonical_entry("fallback", "fallback message") },
            "fallback", message_attempt::SILENT_UNPREFIXED_FALLBACK, false);
    CHECK(fallback.result == message_result::RENDERED);
    CHECK(fallback.expanded_text == "fallback message");
    CHECK_FALSE(fallback.applicability_checked);
    CHECK_FALSE(fallback.post_expansion_materialized);

    const textdb_phase0::message_candidate_evaluation fallback_suppressed =
        textdb_phase0::evaluate_message_candidate(
            { make_canonical_entry("fallback none", "__NONE") },
            "fallback none", message_attempt::SILENT_UNPREFIXED_FALLBACK,
            false);
    CHECK(fallback_suppressed.result == message_result::SUPPRESS);
    CHECK_FALSE(fallback_suppressed.applicability_checked);

    CHECK(textdb_phase0::transition_message_candidate(
              message_attempt::NORMAL_OR_UNSEEN, message_result::MISSING)
          == message_search_action::NEXT_CANDIDATE);
    CHECK(textdb_phase0::transition_message_candidate(
              message_attempt::NORMAL_OR_UNSEEN, message_result::INAPPLICABLE)
          == message_search_action::NEXT_CANDIDATE);
    CHECK(textdb_phase0::transition_message_candidate(
              message_attempt::SILENT_PREFIXED, message_result::MISSING)
          == message_search_action::RETRY_UNPREFIXED);
    CHECK(textdb_phase0::transition_message_candidate(
              message_attempt::SILENT_PREFIXED, message_result::INAPPLICABLE)
          == message_search_action::RETRY_UNPREFIXED);
    CHECK(textdb_phase0::transition_message_candidate(
              message_attempt::SILENT_UNPREFIXED_FALLBACK,
              message_result::MISSING)
          == message_search_action::NEXT_CANDIDATE);
    CHECK(textdb_phase0::transition_message_candidate(
              message_attempt::SILENT_UNPREFIXED_FALLBACK,
              message_result::INAPPLICABLE)
          == message_search_action::NEXT_CANDIDATE);

    const vector<message_attempt> attempts =
    {
        message_attempt::NORMAL_OR_UNSEEN,
        message_attempt::SILENT_PREFIXED,
        message_attempt::SILENT_UNPREFIXED_FALLBACK,
    };
    for (const message_attempt attempt : attempts)
    {
        CHECK(textdb_phase0::transition_message_candidate(
                  attempt, message_result::SUPPRESS)
              == message_search_action::STOP_SILENT);
        CHECK(textdb_phase0::transition_message_candidate(
                  attempt, message_result::RENDERED)
              == message_search_action::STOP_RENDERED);
        CHECK(textdb_phase0::transition_message_candidate(
                  attempt, message_result::CORRUPT)
              == message_search_action::STOP_CORRUPT);
    }
}

TEST_CASE("Phase 0 legacy bracket materialization exposes stable sites",
          "[single-file][textdb][phase0]")
{
    textdb_phase0::canonical_pre_random_pattern pattern;
    pattern.top_locator = { "top key", 3 };
    textdb_phase0::weighted_choice_trace recursive;
    recursive.resolved_canonical_key = "recursive key";
    recursive.recursion_path = { 0, 2 };
    recursive.variant_ordinal = 4;
    pattern.selection.weighted_choices.push_back(recursive);

    {
        rng::subgenerator scoped_rng(11, 12);
        pattern.pattern_en = "[only]";
        const textdb_phase0::legacy_materialization materialized =
            textdb_phase0::materialize_legacy_randomness(pattern);
        REQUIRE(materialized.status
                == textdb_phase0::legacy_materialization_status::MATERIALIZED);
        CHECK(materialized.randomized_pattern_en == "only");
        REQUIRE(materialized.sites.size() == 1);
        const textdb_phase0::legacy_random_site &site = materialized.sites[0];
        CHECK(site.option_count == 1);
        CHECK(site.option_index == 0);
        CHECK(site.identity.top_locator.canonical_key == "top key");
        CHECK(site.identity.top_locator.variant_ordinal == 3);
        CHECK(site.identity.expanded_site_ordinal == 0);
        REQUIRE(site.identity.recursive_variants.size() == 1);
        CHECK(site.identity.recursive_variants[0].locator.canonical_key
              == "recursive key");
        CHECK(site.identity.recursive_variants[0].locator.variant_ordinal == 4);
        CHECK(site.identity.recursive_variants[0].recursion_path
              == (vector<size_t>{ 0, 2 }));
        CHECK(materialized.before.current_state
              == materialized.after.current_state);
        CHECK(materialized.before.current_count
              == materialized.after.current_count);
    }

    {
        rng::subgenerator scoped_rng(21, 22);
        pattern.pattern_en = "[a|b] then [c|d|e]";
        const textdb_phase0::legacy_materialization materialized =
            textdb_phase0::materialize_legacy_randomness(pattern);
        REQUIRE(materialized.sites.size() == 2);
        CHECK(materialized.sites[0].identity.expanded_site_ordinal == 0);
        CHECK(materialized.sites[0].option_count == 2);
        CHECK(materialized.sites[1].identity.expanded_site_ordinal == 1);
        CHECK(materialized.sites[1].option_count == 3);
        CHECK(materialized.after.current_count
              == rng::current_generator().get_count());
    }

    {
        rng::subgenerator scoped_rng(31, 32);
        pattern.pattern_en = "unfinished [a|b";
        const textdb_phase0::legacy_materialization materialized =
            textdb_phase0::materialize_legacy_randomness(pattern);
        CHECK(materialized.status
              == textdb_phase0::legacy_materialization_status::MATERIALIZED);
        CHECK(materialized.randomized_pattern_en == pattern.pattern_en);
        CHECK(materialized.sites.empty());
        CHECK(materialized.before.current_state
              == materialized.after.current_state);
        CHECK(materialized.before.current_count
              == materialized.after.current_count);
    }

    const vector<string> unbound_tokens = { "@at@", "@target@", "@beam@" };
    for (const string &token : unbound_tokens)
    {
        DYNAMIC_SECTION(token)
        {
            rng::subgenerator scoped_rng(41, 42);
            pattern.pattern_en = "bound? " + token + " [a|b]";
            const textdb_phase0::legacy_materialization rejected =
                textdb_phase0::materialize_legacy_randomness(pattern);
            CHECK(rejected.status
                  == textdb_phase0::legacy_materialization_status::CORRUPT);
            CHECK(rejected.randomized_pattern_en == pattern.pattern_en);
            CHECK(rejected.sites.empty());
            CHECK_FALSE(rejected.error.empty());
            CHECK(rejected.before.current_state == rejected.after.current_state);
            CHECK(rejected.before.current_count == rejected.after.current_count);
        }
    }
}

TEST_CASE("Phase 0 orb of entropy CASE_MAP shares canonical randomness",
          "[single-file][textdb][phase0]")
{
    ensure_test_data_root();
    databaseSystemInit();
    const vector<textdb_phase0::canonical_entry> entries =
        textdb_phase0::dump_canonical_english_speakdb();
    const vector<string> english_cases =
    {
        "The orb of entropy pulses.",
        "The orb of entropy vibrates.",
    };
    const vector<string> chinese_cases =
    {
        "熵之球脉动。",
        "熵之球振动。",
    };
    bool saw_case[2] = { false, false };

    const auto bind_runtime_slots = [](string pattern)
    {
        pattern = replace_all(pattern, "@The_monster@",
                              "The orb of entropy");
        return replace_all(pattern, "@the_monster@",
                           "the orb of entropy");
    };

    for (uint64_t seed = 0; seed < 4096; ++seed)
    {
        string legacy_text;
        uint64_t legacy_state;
        uint64_t legacy_count;
        {
            rng::subgenerator scoped_rng(seed, 0xdecafbad12345678ULL);
            legacy_text = maybe_pick_random_substring(bind_runtime_slots(
                textdb_phase0::expand_loaded_canonical_english_speakdb(
                    "orb of entropy cast")));
            legacy_state = rng::current_generator().get_state();
            legacy_count = rng::current_generator().get_count();
        }

        textdb_phase0::legacy_materialization materialized;
        uint64_t canonical_state;
        uint64_t canonical_count;
        {
            rng::subgenerator scoped_rng(seed, 0xdecafbad12345678ULL);
            const textdb_phase0::raw_selection raw =
                textdb_phase0::select_canonical_english(
                    entries, "orb of entropy cast");
            REQUIRE(raw.status
                    == textdb_phase0::raw_selection_status::SELECTED);
            const textdb_phase0::expanded_selection expanded =
                textdb_phase0::expand_canonical_selection(entries, raw);
            textdb_phase0::canonical_pre_random_pattern pre_random;
            pre_random.top_locator = raw.locator;
            pre_random.selection = expanded.trace;
            pre_random.pattern_en = bind_runtime_slots(expanded.text);
            materialized =
                textdb_phase0::materialize_legacy_randomness(pre_random);
            REQUIRE(materialized.status
                    == textdb_phase0::legacy_materialization_status::MATERIALIZED);
            canonical_state = rng::current_generator().get_state();
            canonical_count = rng::current_generator().get_count();

            if (!materialized.sites.empty())
            {
                REQUIRE(materialized.sites.size() == 1);
                const textdb_phase0::legacy_random_site &site =
                    materialized.sites[0];
                REQUIRE(site.option_count == 2);
                REQUIRE(site.option_index >= 0);
                REQUIRE(site.option_index < 2);
                saw_case[site.option_index] = true;

                const uint64_t before_case_map_state =
                    rng::current_generator().get_state();
                const uint64_t before_case_map_count =
                    rng::current_generator().get_count();
                // Pure CASE_MAP: both languages use the already-selected
                // option index; neither template rendering path draws RNG.
                const string english = english_cases[site.option_index];
                const string chinese = chinese_cases[site.option_index];
                CHECK(english == legacy_text);
                CHECK_FALSE(chinese.empty());
                CHECK(rng::current_generator().get_state()
                      == before_case_map_state);
                CHECK(rng::current_generator().get_count()
                      == before_case_map_count);
            }
        }

        INFO("seed=" << seed);
        CHECK(materialized.randomized_pattern_en == legacy_text);
        CHECK(canonical_state == legacy_state);
        CHECK(canonical_count == legacy_count);
    }
    CHECK(saw_case[0]);
    CHECK(saw_case[1]);
}

TEST_CASE("Phase 0 all finite monspell dynamics preserve exact goldens",
          "[single-file][textdb][phase0]")
{
    ensure_test_data_root();
    databaseSystemInit();
    const vector<textdb_phase0::canonical_entry> entries =
        textdb_phase0::dump_canonical_english_speakdb();

    struct golden_case
    {
        const char *key;
        const char *actor;
        const char *actor_possessive;
        const char *possessive;
        vector<string> expected;
    };
    const vector<golden_case> cases =
    {
        {
            "roxanne cast", "Roxanne", "Roxanne's", "her",
            {
                "Roxanne mumbles some strange words.",
                "Roxanne casts a spell.",
            },
        },
        {
            "vex sphinx marauder cast", "The sphinx marauder",
            "The sphinx marauder's", "its",
            {
                "The sphinx marauder screeches an impossible riddle in a mystic tongue.",
                "The sphinx marauder screeches a nonsensical riddle in a mystic tongue.",
                "The sphinx marauder screeches a clich\u00e9 riddle in a mystic tongue.",
            },
        },
        {
            "confuse sphinx marauder cast", "The sphinx marauder",
            "The sphinx marauder's", "its",
            {
                "The sphinx marauder roars an obscure riddle with a strange tongue.",
                "The sphinx marauder roars a perplexing riddle with a strange tongue.",
            },
        },
        {
            "paralysis guardian sphinx cast", "The guardian sphinx",
            "The guardian sphinx's", "its",
            {
                "The guardian sphinx whispers a stupefying mystic riddle.",
                "The guardian sphinx whispers a staggering mystic riddle.",
            },
        },
        {
            "burial acolyte cast", "The burial acolyte",
            "The burial acolyte's", "its",
            {
                "The burial acolyte drones a funeral chant.",
                "The burial acolyte recites a funeral chant.",
            },
        },
        {
            "march of sorrows boris cast", "Boris", "Boris's", "his",
            {
                "Boris casts forth his victims' sorrows.",
                "Boris pitches forth his victims' sorrows.",
                "Boris rolls out his victims' laments.",
                "Boris rolls out his victims' suffering.",
            },
        },
        {
            "weeping skull cast", "The weeping skull",
            "The weeping skull's", "its",
            {
                "The weeping skull unleashes gushing sobs.",
                "The weeping skull releases gushing sobs.",
                "The weeping skull's misery bubbles over.",
                "The weeping skull's misery overflows.",
            },
        },
        {
            "silent weeping skull cast", "The weeping skull",
            "The weeping skull's", "its",
            {
                "The weeping skull's misery bubbles over.",
                "The weeping skull's misery overflows.",
            },
        },
        {
            "orb of winter cast", "The orb of winter",
            "The orb of winter's", "its",
            {
                "The orb of winter glitters with frost.",
                "The orb of winter swirls like a blizzard.",
                "The orb of winter glows icy blue.",
                "The orb of winter glows with a pale light.",
                "The orb of winter glows sapphire.",
            },
        },
    };

    for (const golden_case &golden : cases)
    {
        DYNAMIC_SECTION(golden.key)
        {
            const auto bind_slots = [&golden](string pattern)
            {
                pattern = replace_all(pattern, "@The_monster_possessive@",
                                      golden.actor_possessive);
                pattern = replace_all(pattern, "@The_monster@",
                                      golden.actor);
                return replace_all(pattern, "@possessive@",
                                   golden.possessive);
            };
            set<string> observed;

            for (uint64_t seed = 0; seed < 8192; ++seed)
            {
                string legacy_text;
                uint64_t legacy_state;
                uint64_t legacy_count;
                {
                    rng::subgenerator scoped_rng(seed,
                                                 0x6c8e9cf570932bd5ULL);
                    legacy_text = maybe_pick_random_substring(bind_slots(
                        textdb_phase0::
                            expand_loaded_canonical_english_speakdb(
                                golden.key)));
                    legacy_state = rng::current_generator().get_state();
                    legacy_count = rng::current_generator().get_count();
                }

                textdb_phase0::legacy_materialization materialized;
                uint64_t structured_state;
                uint64_t structured_count;
                {
                    rng::subgenerator scoped_rng(seed,
                                                 0x6c8e9cf570932bd5ULL);
                    const textdb_phase0::raw_selection raw =
                        textdb_phase0::select_canonical_english(entries,
                                                                golden.key);
                    REQUIRE(raw.status
                            == textdb_phase0::raw_selection_status::SELECTED);
                    const textdb_phase0::expanded_selection expanded =
                        textdb_phase0::expand_canonical_selection(entries,
                                                                  raw);
                    REQUIRE(expanded.status
                            == textdb_phase0::raw_selection_status::SELECTED);
                    textdb_phase0::canonical_pre_random_pattern pre_random;
                    pre_random.top_locator = raw.locator;
                    pre_random.selection = expanded.trace;
                    pre_random.pattern_en = bind_slots(expanded.text);
                    materialized =
                        textdb_phase0::materialize_legacy_randomness(
                            pre_random);
                    structured_state = rng::current_generator().get_state();
                    structured_count = rng::current_generator().get_count();
                }

                INFO("seed=" << seed);
                REQUIRE(materialized.status
                        == textdb_phase0::
                            legacy_materialization_status::MATERIALIZED);
                CHECK(materialized.randomized_pattern_en == legacy_text);
                CHECK(structured_state == legacy_state);
                CHECK(structured_count == legacy_count);
                observed.insert(materialized.randomized_pattern_en);
            }

            CHECK(observed == set<string>(golden.expected.begin(),
                                          golden.expected.end()));
        }
    }
}

TEST_CASE_METHOD(MockPlayerYouTestsFixture,
                 "Phase 0 canonical-driven message trace spans target and substring",
                 "[single-file][textdb][phase0]")
{
    ensure_test_data_root();
    databaseSystemInit();
    scoped_phase0_target_world world;

    monster source;
    source.type = MONS_BONE_DRAGON;
    source.set_hit_dice(1);
    source.hit_points = 10;
    source.max_hit_points = 10;
    source.speed = 10;
    source.mid = 4321;
    source.foe = MHITYOU;
    source.attitude = ATT_HOSTILE;
    source.set_position(coord_def(20, 20));

    bolt beam;
    beam.name = "collective despair";
    beam.short_name = "collective despair";
    beam.range = 8;
    beam.target = you.pos();
    beam.hit = AUTOMATIC_HIT;
    beam.damage = dice_def(1, 1);
    beam.flavour = BEAM_MAGIC;
    beam.thrower = KILL_MON_MISSILE;

    const vector<textdb_phase0::canonical_entry> entries =
        textdb_phase0::dump_canonical_english_speakdb();
    const vector<string> english_cases =
    {
        "The bone dragon breathes collective despair at you.",
        "The bone dragon breathes endless sorrows at you.",
    };
    // Phase 0 CASE_MAP outputs are final templates: no TextDB recursion or
    // localized [a|b] syntax survives into this pure projection.
    const vector<string> chinese_cases =
    {
        "骨龙朝你吐出集体的绝望。",
        "骨龙朝你吐出无尽的悲伤。",
    };
    bool saw_case[2] = { false, false };

    for (uint64_t seed = 0; seed < 1024; ++seed)
    {
        textdb_phase0::expanded_selection legacy_database;
        textdb_phase0::message_runtime_bindings legacy_bindings;
        string legacy_message;
        vector<random_substring_choice_trace> legacy_substring_sites;
        uint64_t legacy_database_state;
        uint64_t legacy_database_count;
        uint64_t legacy_total_before_state;
        uint64_t legacy_total_before_count;
        uint64_t legacy_binding_before_state;
        uint64_t legacy_binding_before_count;
        uint64_t legacy_binding_after_state;
        uint64_t legacy_binding_after_count;
        uint64_t legacy_final_state;
        uint64_t legacy_final_count;
        phase0_binding_context legacy_context = { &source, &beam };
        {
            rng::subgenerator scoped_rng(seed, 0x7edcba9876543210ULL);
            legacy_total_before_state = rng::current_generator().get_state();
            legacy_total_before_count = rng::current_generator().get_count();
            legacy_database =
                textdb_phase0::expand_loaded_canonical_english_speakdb_traced(
                    "march of sorrows bone dragon cast");
            legacy_database_state = rng::current_generator().get_state();
            legacy_database_count = rng::current_generator().get_count();
            legacy_binding_before_state =
                rng::current_generator().get_state();
            legacy_binding_before_count =
                rng::current_generator().get_count();
            legacy_bindings = resolve_phase0_bindings(&legacy_context);
            legacy_binding_after_state = rng::current_generator().get_state();
            legacy_binding_after_count = rng::current_generator().get_count();
            const random_substring_trace_observer substring_observer =
                { observe_phase0_substring_choice,
                  &legacy_substring_sites };
            legacy_message = maybe_pick_random_substring(
                bind_phase0_runtime_slots(legacy_database.text,
                                          legacy_bindings),
                &substring_observer);
            legacy_final_state = rng::current_generator().get_state();
            legacy_final_count = rng::current_generator().get_count();
        }

        textdb_phase0::structured_message_materialization structured;
        phase0_binding_context structured_context = { &source, &beam };
        {
            rng::subgenerator scoped_rng(seed, 0x7edcba9876543210ULL);
            structured = textdb_phase0::materialize_structured_message(
                entries, "march of sorrows bone dragon cast",
                resolve_phase0_bindings, &structured_context);
        }

        INFO("seed=" << seed);
        REQUIRE(legacy_database.status
                == textdb_phase0::raw_selection_status::SELECTED);
        REQUIRE(structured.status
                == textdb_phase0::raw_selection_status::SELECTED);
        CHECK(same_database_trace(legacy_database.trace,
                                  structured.database_trace));
        CHECK(structured.total_before.current_state
              == legacy_total_before_state);
        CHECK(structured.total_before.current_count
              == legacy_total_before_count);
        CHECK(structured.database_after.current_state
              == legacy_database_state);
        CHECK(structured.database_after.current_count
              == legacy_database_count);
        CHECK(structured.binding_trace.before.current_state
              == legacy_binding_before_state);
        CHECK(structured.binding_trace.before.current_count
              == legacy_binding_before_count);
        CHECK(structured.binding_trace.after.current_state
              == legacy_binding_after_state);
        CHECK(structured.binding_trace.after.current_count
              == legacy_binding_after_count);
        CHECK(structured_context.target.kind == speech_target_kind::PLAYER);
        CHECK(structured_context.target.relation == speech_target_relation::AT);
        CHECK(structured_context.target.position == you.pos());
        REQUIRE(structured_context.target_events.size() == 1);
        REQUIRE(legacy_context.target_events.size()
                == structured_context.target_events.size());
        CHECK(same_phase0_target_event(legacy_context.target_events[0],
                                       structured_context.target_events[0]));
        CHECK(structured_context.target_events[0].kind
              == speech_target_observer_event_kind::FIRE_TRACER);
        CHECK(structured_context.target_events[0].rng_state_before
              == structured_context.target_events[0].rng_state_after);
        CHECK(structured_context.target_events[0].rng_count_before
              == structured_context.target_events[0].rng_count_after);
        CHECK(structured.binding_trace.before.current_state
              == structured.binding_trace.after.current_state);
        CHECK(structured.binding_trace.before.current_count
              == structured.binding_trace.after.current_count);

        REQUIRE(structured.substring_trace.status
                == textdb_phase0::legacy_materialization_status::MATERIALIZED);
        REQUIRE(structured.substring_trace.sites.size() == 1);
        const textdb_phase0::legacy_random_site &site =
            structured.substring_trace.sites[0];
        REQUIRE(legacy_substring_sites.size()
                == structured.substring_trace.sites.size());
        CHECK(legacy_substring_sites[0].site_ordinal
              == site.identity.expanded_site_ordinal);
        CHECK(legacy_substring_sites[0].random_bound == site.option_count);
        CHECK(legacy_substring_sites[0].selected_index == site.option_index);
        REQUIRE(site.option_count == 2);
        REQUIRE(site.option_index >= 0);
        REQUIRE(site.option_index < 2);
        saw_case[site.option_index] = true;
        CHECK(structured.randomized_message_en == legacy_message);
        CHECK(structured.randomized_message_en
              == english_cases[site.option_index]);
        CHECK(structured.total_after.current_state == legacy_final_state);
        CHECK(structured.total_after.current_count == legacy_final_count);
        CHECK(same_rng_observation(structured.substring_trace.before,
                                   structured.binding_trace.after));
        CHECK(same_rng_observation(structured.substring_trace.after,
                                   structured.total_after));

        const uint64_t before_zh_state =
            rng::current_generator().get_state();
        const uint64_t before_zh_count =
            rng::current_generator().get_count();
        const string chinese = chinese_cases[site.option_index];
        CHECK_FALSE(chinese.empty());
        CHECK(rng::current_generator().get_state() == before_zh_state);
        CHECK(rng::current_generator().get_count() == before_zh_count);
    }
    CHECK(saw_case[0]);
    CHECK(saw_case[1]);
}

TEST_CASE("Phase 0 canonical expansion traces recursion limits",
          "[single-file][textdb][phase0]")
{
    {
        textdb_phase0::canonical_entry single =
            make_canonical_entry("bound one", "only");
        single.variants[0].weight = 1;
        rng::subgenerator scoped_rng(7, 8);
        const textdb_phase0::raw_selection raw =
            textdb_phase0::select_canonical_english({ single }, "bound one");
        CHECK(raw.status == textdb_phase0::raw_selection_status::SELECTED);
        CHECK(raw.locator.variant_ordinal == 0);
        REQUIRE(raw.trace.weighted_choices.size() == 1);
        CHECK(raw.trace.weighted_choices[0].total_bound == 1);
        CHECK(raw.trace.weighted_choices[0].random_result == 0);
        CHECK(raw.trace.weighted_choices[0].before.current_count
              == raw.trace.weighted_choices[0].after.current_count);
    }

    {
        textdb_phase0::canonical_entry zero =
            make_canonical_entry("bound zero", "unreachable");
        zero.variants[0].weight = 0;
        rng::subgenerator scoped_rng(7, 8);
        const textdb_phase0::raw_selection raw =
            textdb_phase0::select_canonical_english({ zero }, "bound zero");
        CHECK(raw.status == textdb_phase0::raw_selection_status::CORRUPT);
        CHECK(raw.locator.variant_ordinal == static_cast<size_t>(-1));
        CHECK(raw.raw_pattern == "BUG, NO STRING CHOSEN");
        REQUIRE(raw.trace.weighted_choices.size() == 1);
        CHECK(raw.trace.weighted_choices[0].total_bound == 0);
        CHECK(raw.trace.weighted_choices[0].variant_ordinal
              == static_cast<size_t>(-1));
        CHECK(raw.trace.weighted_choices[0].before.current_count
              == raw.trace.weighted_choices[0].after.current_count);
    }

    {
        const textdb_phase0::raw_selection missing =
            textdb_phase0::select_canonical_english({}, "absent");
        CHECK(missing.status == textdb_phase0::raw_selection_status::MISSING);
        CHECK(missing.locator.variant_ordinal == static_cast<size_t>(-1));
    }

    {
        textdb_phase0::raw_selection corrupt;
        corrupt.status = textdb_phase0::raw_selection_status::CORRUPT;
        corrupt.raw_pattern = "@child@{{return 'lua still runs'}}";
        const vector<textdb_phase0::canonical_entry> entries =
            { make_canonical_entry("child", "must not expand") };
        const textdb_phase0::expanded_selection expanded =
            textdb_phase0::expand_canonical_selection(entries, corrupt);
        CHECK(expanded.text == "@child@{{return 'lua still runs'}}");
        CHECK(expanded.trace.recursive_sites.empty());
        CHECK(expanded.trace.final_replacement_count == 0);
        CHECK(expanded.trace.lua_sites.empty());
    }

    const auto make_chain = [](int length)
    {
        vector<textdb_phase0::canonical_entry> entries;
        for (int i = 0; i < length; ++i)
        {
            const string key = make_stringf("depth-%02d", i);
            const string pattern = i + 1 == length
                ? "done"
                : make_stringf("@depth-%02d@", i + 1);
            entries.push_back(make_canonical_entry(key, pattern));
        }
        return entries;
    };

    {
        rng::subgenerator scoped_rng(1, 2);
        const vector<textdb_phase0::canonical_entry> entries = make_chain(10);
        const textdb_phase0::raw_selection raw =
            textdb_phase0::select_canonical_english(entries, "depth-00");
        REQUIRE(raw.trace.weighted_choices.size() == 1);
        const textdb_phase0::expanded_selection expanded =
            textdb_phase0::expand_canonical_selection(entries, raw);
        CHECK(expanded.text == "done");
        CHECK(expanded.trace.weighted_choices.size() == 10);
        CHECK(expanded.trace.recursive_sites.size() == 9);
        CHECK(std::count_if(expanded.trace.weighted_choices.begin(),
                            expanded.trace.weighted_choices.end(),
                            [](const textdb_phase0::weighted_choice_trace &c)
                            { return c.requested_key == "depth-00"; }) == 1);
    }

    {
        rng::subgenerator scoped_rng(1, 2);
        const vector<textdb_phase0::canonical_entry> entries = make_chain(11);
        const textdb_phase0::expanded_selection expanded =
            textdb_phase0::expand_canonical_selection(
                entries,
                textdb_phase0::select_canonical_english(entries, "depth-00"));
        CHECK(expanded.text == "TOO MUCH RECURSION");
        CHECK(expanded.status
              == textdb_phase0::raw_selection_status::CORRUPT);
        REQUIRE(expanded.trace.recursive_sites.size() == 10);
        CHECK(expanded.trace.recursive_sites.back().recursion_depth == 11);
        CHECK(expanded.trace.recursive_sites.back().status
              == textdb_phase0::recursive_site_status::DEPTH_LIMIT);
        CHECK(textdb_phase0::evaluate_message_candidate(
                  entries, "depth-00",
                  textdb_phase0::message_attempt::NORMAL_OR_UNSEEN, true).result
              == textdb_phase0::message_result::CORRUPT);
    }

    for (int sites : { 100, 101 })
    {
        DYNAMIC_SECTION("replacement sites=" << sites)
        {
            string pattern;
            for (int i = 0; i < sites; ++i)
                pattern += make_stringf("@runtime-%03d@", i);
            const vector<textdb_phase0::canonical_entry> entries =
                { make_canonical_entry("replacement root", pattern) };
            rng::subgenerator scoped_rng(3, 4);
            const textdb_phase0::expanded_selection expanded =
                textdb_phase0::expand_canonical_selection(
                    entries, textdb_phase0::select_canonical_english(
                                 entries, "replacement root"));
            CHECK(expanded.text == pattern);
            REQUIRE(expanded.trace.recursive_sites.size()
                    == static_cast<size_t>(sites));
            CHECK(expanded.trace.final_replacement_count == sites);
            CHECK(expanded.status
                  == (sites == 100
                      ? textdb_phase0::raw_selection_status::SELECTED
                      : textdb_phase0::raw_selection_status::CORRUPT));
            if (sites == 100)
            {
                CHECK(expanded.trace.recursive_sites.back().status
                      == textdb_phase0::recursive_site_status::MISSING);
            }
            else
            {
                CHECK(expanded.trace.recursive_sites.back().replacement_count
                      == 101);
                CHECK(expanded.trace.recursive_sites.back().status
                      == textdb_phase0::recursive_site_status::
                          REPLACEMENT_LIMIT);
            }
        }
    }

    {
        const vector<textdb_phase0::canonical_entry> entries =
            { make_canonical_entry("unbalanced root", "before @broken") };
        rng::subgenerator scoped_rng(5, 6);
        const textdb_phase0::expanded_selection expanded =
            textdb_phase0::expand_canonical_selection(
                entries, textdb_phase0::select_canonical_english(
                             entries, "unbalanced root"));
        CHECK(expanded.text == "before @broken");
        REQUIRE(expanded.trace.recursive_sites.size() == 1);
        CHECK(expanded.trace.recursive_sites[0].marker == "broken");
        CHECK(expanded.trace.recursive_sites[0].status
              == textdb_phase0::recursive_site_status::UNBALANCED);
        CHECK(expanded.status
              == textdb_phase0::raw_selection_status::CORRUPT);
    }

    {
        const vector<textdb_phase0::canonical_entry> entries =
        {
            make_canonical_entry("duplicate root", "@same@@same@"),
            make_canonical_entry("same", "leaf"),
        };
        rng::subgenerator scoped_rng(9, 10);
        const textdb_phase0::expanded_selection expanded =
            textdb_phase0::expand_canonical_selection(
                entries, textdb_phase0::select_canonical_english(
                             entries, "duplicate root"));
        CHECK(expanded.text == "leafleaf");
        REQUIRE(expanded.trace.recursive_sites.size() == 2);
        CHECK(expanded.trace.recursive_sites[0].recursion_path
              == vector<size_t>{ 0 });
        CHECK(expanded.trace.recursive_sites[0].replacement == "leaf");
        CHECK(expanded.trace.recursive_sites[1].recursion_path
              == vector<size_t>{ 1 });
        CHECK(expanded.trace.recursive_sites[1].replacement == "leaf");
    }

    {
        const vector<textdb_phase0::canonical_entry> entries =
        {
            make_canonical_entry("nested child", "@nested leaf@"),
            make_canonical_entry("nested leaf", "done"),
            make_canonical_entry("nested root", "@nested child@"),
        };
        rng::subgenerator scoped_rng(11, 12);
        const textdb_phase0::expanded_selection expanded =
            textdb_phase0::expand_canonical_selection(
                entries, textdb_phase0::select_canonical_english(
                             entries, "nested root"));
        CHECK(expanded.text == "done");
        REQUIRE(expanded.trace.recursive_sites.size() == 2);
        CHECK(expanded.trace.recursive_sites[0].recursion_path
              == vector<size_t>{ 0 });
        CHECK(expanded.trace.recursive_sites[0].replacement == "done");
        CHECK(expanded.trace.recursive_sites[1].recursion_path
              == (vector<size_t>{ 0, 0 }));
        CHECK(expanded.trace.recursive_sites[1].replacement == "done");
    }
}

TEST_CASE("Phase 0 embedded Lua materialization is observable",
          "[single-file][textdb][phase0]")
{
    {
        const textdb_phase0::expanded_selection result =
            textdb_phase0::materialize_embedded_lua(
                "A{{return 'one'}}B{{return 'two'}}C");
        CHECK(result.text == "AoneBtwoC");
        REQUIRE(result.trace.lua_sites.size() == 2);
        CHECK(result.trace.lua_sites[0].ordinal == 0);
        CHECK(result.trace.lua_sites[0].source == "return 'one'");
        CHECK(result.trace.lua_sites[0].result == "one");
        CHECK(result.trace.lua_sites[0].status
              == textdb_phase0::lua_site_status::EXECUTED);
        CHECK(result.trace.lua_sites[0].before.current_count
              == result.trace.lua_sites[0].after.current_count);
        CHECK(result.trace.lua_sites[1].ordinal == 1);
        CHECK(result.trace.lua_sites[1].result == "two");
    }

    {
        const textdb_phase0::expanded_selection result =
            textdb_phase0::materialize_embedded_lua(
                "{{error('phase0 boom')}}after");
        REQUIRE(result.trace.lua_sites.size() == 1);
        CHECK(result.trace.lua_sites[0].status
              == textdb_phase0::lua_site_status::ERROR);
        CHECK(result.trace.lua_sites[0].result.find("phase0 boom")
              != string::npos);
        CHECK(result.text.find("phase0 boom") != string::npos);
        CHECK(result.status == textdb_phase0::raw_selection_status::CORRUPT);
    }

    {
        const textdb_phase0::expanded_selection result =
            textdb_phase0::materialize_embedded_lua("before {{return 'x'");
        CHECK(result.text == "before {{return 'x'");
        REQUIRE(result.trace.lua_sites.size() == 1);
        CHECK(result.trace.lua_sites[0].status
              == textdb_phase0::lua_site_status::UNBALANCED);
        CHECK(result.status == textdb_phase0::raw_selection_status::CORRUPT);
    }

    // If this build exposes crawl.random2 to embedded Lua, its RNG movement is
    // captured without the observer performing any random call of its own.
    rng::subgenerator scoped_rng(0x1234, 0x5678);
    const textdb_phase0::expanded_selection random_result =
        textdb_phase0::materialize_embedded_lua(
            "{{return tostring(crawl.random2(7))}}");
    REQUIRE(random_result.trace.lua_sites.size() == 1);
    const textdb_phase0::lua_site_trace &random_site =
        random_result.trace.lua_sites[0];
    if (random_site.status == textdb_phase0::lua_site_status::EXECUTED)
    {
        CHECK(random_site.after.current_count
              == rng::current_generator().get_count());
        CHECK(random_site.after.current_count >= random_site.before.current_count);
    }
}

TEST_CASE("Phase 0 database expansion leaves bracket randomness untouched",
          "[single-file][textdb][phase0]")
{
    ensure_test_data_root();
    const vector<textdb_phase0::canonical_entry> entries =
        textdb_phase0::dump_canonical_english_speakdb();
    bool saw_bracket_site = false;
    for (uint64_t seed = 0; seed < 128 && !saw_bracket_site; ++seed)
    {
        rng::subgenerator scoped_rng(seed, 99);
        const textdb_phase0::expanded_selection expanded =
            textdb_phase0::expand_canonical_selection(
                entries, textdb_phase0::select_canonical_english(
                             entries, "March of Sorrows Boris cast"));
        saw_bracket_site = expanded.text.find("[casts|pitches]")
                           != string::npos;
    }
    CHECK(saw_bracket_site);
}

TEST_CASE("write production TextDB Phase 0 artifact",
          "[.textdb-phase0-dump]")
{
    const char *output_path = std::getenv("TEXTDB_PHASE0_DUMP");
    REQUIRE(output_path != nullptr);
    REQUIRE(*output_path != '\0');
    ensure_test_data_root();
    const char *database_env = std::getenv("TEXTDB_PHASE0_DB");
    const string database_name = (database_env && *database_env)
                                 ? database_env : "speak";
    REQUIRE((database_name == "speak" || database_name == "misc"
             || database_name == "shout"));
    const char *language = std::getenv("TEXTDB_PHASE0_LANGUAGE");
    const bool localized = language != nullptr && *language != '\0';
    const auto dump_english = [database_name]()
    {
        if (database_name == "misc")
            return textdb_phase0::dump_canonical_english_miscdb_typed();
        if (database_name == "shout")
            return textdb_phase0::dump_canonical_english_shoutdb_typed();
        return textdb_phase0::dump_canonical_english_speakdb_typed();
    };
    const auto dump_localized = [database_name](const string &db_language)
    {
        if (database_name == "misc")
            return textdb_phase0::dump_localized_miscdb_typed(db_language);
        if (database_name == "shout")
            return textdb_phase0::dump_localized_shoutdb_typed(db_language);
        return textdb_phase0::dump_localized_speakdb_typed(db_language);
    };
    const textdb_phase0::canonical_speakdb_dump dump =
        localized ? dump_localized(language) : dump_english();
    CHECK(dump.database_name == database_name);
    if (database_name == "misc")
    {
        const string decorlines_source = localized
            ? "database/" + string(language) + "/decorlines.txt"
            : "database/decorlines.txt";
        set<string> decorlines_keys;
        size_t decorlines_variants = 0;
        for (const textdb_phase0::canonical_entry &entry : dump.entries)
        {
            if (has_source_history(entry, decorlines_source))
            {
                decorlines_keys.insert(entry.canonical_key);
                decorlines_variants += entry.variants.size();
            }
        }
        if (!localized)
        {
            CHECK(decorlines_keys.size() == 132);
            CHECK(decorlines_variants == 209);
            CHECK(key_set_fingerprint(decorlines_keys) == 0x40d7ff2f876d3a10ULL);
        }
        else
        {
            CHECK(dump.source_directory
                  == "database/" + string(language) + "/");
            CHECK_FALSE(dump.sources.empty());
            CHECK_FALSE(dump.entries.empty());
        }
    }
    else if (database_name == "shout")
    {
        const string shout_source = localized
            ? "database/" + string(language) + "/shout.txt"
            : "database/shout.txt";
        set<string> shout_keys;
        size_t shout_variants = 0;
        for (const textdb_phase0::canonical_entry &entry : dump.entries)
        {
            if (has_source_history(entry, shout_source))
            {
                shout_keys.insert(entry.canonical_key);
                shout_variants += entry.variants.size();
            }
        }
        if (!localized)
        {
            // 93 dump entries: 92 real keys plus the zero-body artifact
            // "player sphinx riddle lines" (see below); 119 variants.
            CHECK(shout_keys.size() == 93);
            CHECK(shout_variants == 119);
            CHECK(key_set_fingerprint(shout_keys)
                  == 0x0dd1652a6c5f381fULL);
            // The "#### Player sphinx riddle lines" comment title block is
            // a production-parser artifact: comment lines starting with '#'
            // are skipped, but the title line itself is not, so it becomes a
            // zero-body key that can never be selected.  Freeze the artifact
            // shape explicitly so the shout inventory's identity filtering
            // stays consistent with this dump.
            const textdb_phase0::canonical_entry *artifact =
                find_canonical_entry(dump.entries,
                                     "player sphinx riddle lines");
            REQUIRE(artifact != nullptr);
            CHECK(artifact->body_empty);
            CHECK(artifact->parse_error == "BUG, EMPTY ENTRY");
            CHECK(artifact->variants.empty());
            size_t empty_count = 0;
            for (const textdb_phase0::canonical_entry &entry : dump.entries)
            {
                if (has_source_history(entry, shout_source)
                    && entry.body_empty)
                {
                    ++empty_count;
                }
            }
            CHECK(empty_count == 1);
        }
        else
        {
            CHECK(dump.source_directory
                  == "database/" + string(language) + "/");
            CHECK_FALSE(dump.sources.empty());
            CHECK_FALSE(dump.entries.empty());
        }
    }
    else
    {
        const string monspell_source = localized
            ? "database/" + string(language) + "/monspell.txt"
            : "database/monspell.txt";
        set<string> monspell_keys;
        size_t monspell_variants = 0;
        for (const textdb_phase0::canonical_entry &entry : dump.entries)
        {
            if (has_source_history(entry, monspell_source))
            {
                monspell_keys.insert(entry.canonical_key);
                monspell_variants += entry.variants.size();
            }
        }
        if (!localized)
        {
            CHECK(monspell_keys.size() == 262);
            CHECK(monspell_variants == 355);
            CHECK(key_set_fingerprint(monspell_keys)
                  == 0xc87868127106d293ULL);
        }
        else
        {
            CHECK(dump.source_directory
                  == "database/" + string(language) + "/");
            CHECK_FALSE(dump.sources.empty());
            CHECK_FALSE(dump.entries.empty());
        }
    }

    string error;
    REQUIRE(write_textdb_phase0_artifact_atomic(dump, output_path, error));
    // Exercise replace-existing semantics, including MoveFileExW on Windows.
    REQUIRE(write_textdb_phase0_artifact_atomic(dump, output_path, error));
}
