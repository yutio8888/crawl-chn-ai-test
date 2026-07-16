/**
 * @file
 * database.cc
**/

#include "AppHdr.h"

#include "database.h"
#include "i18n.h"

#include <cstdlib>
#include <deque>
#include <fcntl.h>
#include <functional>
#include <fstream>
#include <map>
#include <sys/stat.h>
#include <sys/types.h>
#if defined(UNIX) || defined(TARGET_COMPILER_MINGW)
#include <unistd.h>
#endif

#include "clua.h"
#include "end.h"
#include "files.h"
#include "fork-message-overlay.h"
#include "libutil.h"
#include "options.h"
#include "random.h"
#include "stringutil.h"
#include "syscalls.h"
#include "unicode.h"

// TextDB handles dependency checking the db vs text files, creating the
// db, loading, and destroying the DB.
class TextDB
{
public:
    // db_name is the savedir-relative name of the db file,
    // minus the "db" extension.
    TextDB(const char* db_name, const char* dir, vector<string> files);
    TextDB(TextDB *parent);
    ~TextDB() { shutdown(true); delete translation; }
    void init();
    void shutdown(bool recursive = false);
    DBM* get() { return _db; }

    // Phase 0 audit only: provenance cannot be recovered from DBM, so the
    // canonical dump must re-read the production input sequence.
    const string &phase0_directory() const { return _directory; }
    const vector<string> &phase0_input_files() const { return _input_files; }

    // Make it easier to migrate from raw DBM* to TextDB
    operator bool() const { return _db != 0; }
    operator DBM*() const { return _db; }

 private:
    bool _needs_update() const;
    void _regenerate_db();

 private:
    bool open_db();
    const char* const _db_name;
    string _directory;
    vector<string> _input_files;
    DBM* _db;
    string timestamp;
    TextDB *_parent;
    const char* lang() { return _parent ? Options.lang_name : 0; }
public:
    TextDB *translation;
};

// Convenience functions for (read-only) access to generic
// berkeley DB databases.
static void _store_text_db(const string &in, DBM *db, bool trim_keys = true);

static string _query_database(TextDB &db, string key, bool canonicalise_key,
                              bool run_lua, bool untranslated = false);
static void _add_entry(DBM *db, const string &k, const string &v);

static TextDB AllDBs[] =
{
    TextDB("descriptions", "descript/",
          { "features.txt",
            "items.txt",
            "unident.txt",
            "unrand.txt",
            "monsters.txt",
            "spells.txt",
            "gods.txt",
            "branches.txt",
            "skills.txt",
            "ability.txt",
            "cards.txt",
            "commands.txt",
            "clouds.txt",
            "status.txt",
            "monstatus.txt",
            "mutations.txt",
            "passives.txt", }),

    TextDB("gamestart", "descript/",
          { "species.txt",
            "backgrounds.txt" }),

    TextDB("randart", "database/",
          { "randname.txt",
            "rand_wpn.txt", // mostly weapons
            "rand_arm.txt", // mostly armour
            "rand_all.txt", // jewellery and general
            "randbook.txt", // artefact books
            }),

    TextDB("speak", "database/",
          { "monspeak.txt", // monster speech
            "monspell.txt", // monster spellcasting speech
            "monflee.txt",  // monster fleeing speech
            "wpnnoise.txt", // noisy weapon speech
            "insult.txt",   // imp/demon taunts
            "godspeak.txt", // god speech
            "monname.txt",  // names for Beogh apostles and Hep ancestors
                            // and weapon spirits, plus graffiti authors
            "colourname.txt", // colour/colour pattern names
            "graffiti.txt", // graffiti
            "miscast.txt",  // spell miscasts
            }),

    TextDB("shout", "database/",
          { "shout.txt",
            "insult.txt"    // imp/demon taunts, again
            }),

    TextDB("misc", "database/",
          { "miscname.txt", // names for miscellaneous things
            "godname.txt",  // god-related names (mostly His Xomminess)
            "montitle.txt", // titles for monsters (i.e. uniques)
            "decorlines.txt", // miscellaneous lines for walking on decoration
            "monname.txt",  // names for Beogh apostles and Hep ancestors
                            // and weapon spirits, plus graffiti authors, again
            "colourname.txt", // colour/colour pattern names, again
            "graffiti.txt", // graffiti, again
            "gizmo.txt",    // name-assembling for gizmos
            }),

    TextDB("quotes", "descript/",
          { "quotes.txt"    // quotes for items and monsters
            }),

    TextDB("help", "database/",
          { "help.txt"      // database for outsourced help texts
            }),

    TextDB("FAQ", "database/",
          { "FAQ.txt",      // database for Frequently Asked Questions
            }),

    TextDB("hints", "descript/",
          { "hints.txt",    // hints mode
            "tutorial.txt", // tutorial mode
            }),

    TextDB("egos", "descript/",
          { "egos.txt",     // weapon/armour/missile egos
            }),

    TextDB("source", "i18n/",
          { "source.txt",   // C++ source string i18n (T_() macro)
            }),
};

static TextDB& DescriptionDB = AllDBs[0];
static TextDB& GameStartDB   = AllDBs[1];
static TextDB& RandartDB     = AllDBs[2];
static TextDB& SpeakDB       = AllDBs[3];
static TextDB& ShoutDB       = AllDBs[4];
static TextDB& MiscDB        = AllDBs[5];
static TextDB& QuotesDB      = AllDBs[6];
static TextDB& HelpDB        = AllDBs[7];
static TextDB& FAQDB         = AllDBs[8];
static TextDB& HintsDB       = AllDBs[9];
static TextDB& EgosDB        = AllDBs[10];
static TextDB& SourceDB      = AllDBs[11];

static string _db_cache_path(string db, const char *lang)
{
    if (lang)
        db = db + "." + lang;
    return savedir_versioned_path("db/" + db);
}

// ----------------------------------------------------------------------
// TextDB
// ----------------------------------------------------------------------

TextDB::TextDB(const char* db_name, const char* dir, vector<string> files)
    : _db_name(db_name), _directory(dir), _input_files(files),
      _db(nullptr), timestamp(""), _parent(0), translation(0)
{
}

TextDB::TextDB(TextDB *parent)
    : _db_name(parent->_db_name),
      _directory(parent->_directory + Options.lang_name + "/"),
      _input_files(parent->_input_files), // FIXME: pointless copy
      _db(nullptr), timestamp(""), _parent(parent), translation(nullptr)
{
    // For language-specific child DBs, scan the directory for all .txt
    // files. This allows translation data to be split across multiple
    // files (e.g. source.txt + spells.txt + monsters.txt) so that
    // parallel agent work doesn't cause append-only merge conflicts.
    // source.txt is sorted first so domain-specific files can override
    // entries when keys are intentionally moved.
    if (Options.lang_name && *Options.lang_name)
    {
        // Resolve through datafile_path: _directory is a relative path
        // like "i18n/zh/" but actual files live under "dat/i18n/zh/".
        string test_path = datafile_path(_directory + "source.txt", false);
        if (!test_path.empty())
        {
            string dir = get_parent_directory(test_path);
            vector<string> found = get_dir_files_ext(dir, "txt");
            if (!found.empty())
            {
                // Ensure source.txt is always first
                vector<string> ordered;
                for (const string &f : found)
                    if (f == "source.txt")
                        ordered.push_back(f);
                for (const string &f : found)
                    if (f != "source.txt")
                        ordered.push_back(f);
                _input_files = ordered;
            }
        }
    }
}

bool TextDB::open_db()
{
    if (_db)
        return true;

    const string full_db_path = _db_cache_path(_db_name, lang());
    _db = dbm_open(full_db_path.c_str(), O_RDONLY, 0660);
    if (!_db)
        return false;

    timestamp = _query_database(*this, "TIMESTAMP", false, false, true);
    if (timestamp.empty())
        return false;

    return true;
}

void TextDB::init()
{
    if (Options.lang_name && !_parent)
    {
        translation = new TextDB(this);
        translation->init();
    }

    open_db();

    if (!_needs_update())
        return;
    _regenerate_db();

    if (!open_db())
    {
        end(1, true, "Failed to open DB: %s",
            _db_cache_path(_db_name, lang()).c_str());
    }
}

void TextDB::shutdown(bool recursive)
{
    if (_db)
    {
        dbm_close(_db);
        _db = nullptr;
    }
    if (recursive && translation)
        translation->shutdown(recursive);
}

bool TextDB::_needs_update() const
{
    string ts;
    bool no_files = true;

    for (const string &file : _input_files)
    {
        string full_input_path = _directory + file;
        full_input_path = datafile_path(full_input_path, !_parent);
        // packagers who mess with mtime beware: you shouldn't put the db in
        // a shared folder, as a fixed mtime will break this check.
        time_t mtime = file_modtime(full_input_path);
        const bool exists = file_exists(full_input_path);
        if (exists || !_parent)
        {
            if (exists)
                no_files = false;
            char buf[20];
            snprintf(buf, sizeof(buf), ":%" PRId64, (int64_t)mtime);
            ts += buf;
        }
    }

    if (no_files)
    {
        // No point in empty databases, although for simplicity keep ones
        // for disappeared translations for now.
        ASSERTM(_parent,
            "No readable database files in `%s` (internal error).",
            _directory.c_str());
        TextDB *en = _parent;
        delete en->translation; // ie, ourself
        en->translation = 0;
        return false;
    }

    return ts != timestamp;
}

void TextDB::_regenerate_db()
{
    shutdown();
    if (_parent)
    {
#if defined(DEBUG_DIAGNOSTICS) && !(defined(TARGET_COMPILER_VC) && defined(USE_TILE))
        printf("Regenerating db: %s [%s]\n", _db_name, Options.lang_name);
#endif
        mprf(MSGCH_PLAIN, T_("Regenerating db: %s [%s]"), _db_name, Options.lang_name);
    }
    else
    {
#if defined(DEBUG_DIAGNOSTICS) && !(defined(TARGET_COMPILER_VC) && defined(USE_TILE))
        printf("Regenerating db: %s\n", _db_name);
#endif
        mprf(MSGCH_PLAIN, T_("Regenerating db: %s"), _db_name);
    }

    string db_path = _db_cache_path(_db_name, lang());
    string full_db_path = db_path + ".db";

    {
        string output_dir = get_parent_directory(db_path);
        if (!check_mkdir("DB directory", &output_dir))
            end(1, false, "Cannot create db directory '%s'.", output_dir.c_str());
    }

    file_lock lock(db_path + ".lk", "wb");
#ifndef DGL_REWRITE_PROTECT_DB_FILES
    unlink_u(full_db_path.c_str());
#endif

    string ts;
    if (!(_db = dbm_open(db_path.c_str(), O_RDWR | O_CREAT, 0660)))
        end(1, true, "Unable to open DB: %s", db_path.c_str());
    for (const string &file : _input_files)
    {
        string full_input_path = _directory + file;
        full_input_path = datafile_path(full_input_path, !_parent);
        char buf[20];
        time_t mtime = file_modtime(full_input_path);
        if (file_exists(full_input_path)
            || !_parent) // english is mandatory
        {
            snprintf(buf, sizeof(buf), ":%" PRId64, (int64_t)mtime);
            ts += buf;
            bool is_source = (string(_db_name) == "source");
            _store_text_db(full_input_path, _db, !is_source);
        }
    }
    _add_entry(_db, "TIMESTAMP", ts);

    dbm_close(_db);
    _db = 0;
}

// ----------------------------------------------------------------------
// DB system
// ----------------------------------------------------------------------

#define NUM_DB ARRAYSZ(AllDBs)

void databaseSystemInit()
{
    for (unsigned int i = 0; i < NUM_DB; i++)
        AllDBs[i].init();
    // Validate the compiled monspell catalog against the canonical English
    // source snapshot before any speech query can consume RNG or run Lua.
    fork_message_overlay::load_monspell_overlay(
        textdb_phase0::dump_canonical_english_speakdb());
    i18n_cache_clear();
}

void databaseSystemShutdown()
{
    for (unsigned int i = 0; i < NUM_DB; i++)
        AllDBs[i].shutdown(true);
}

////////////////////////////////////////////////////////////////////////////
// Main DB functions

static datum _database_fetch(DBM *database, const string &key)
{
    datum result;
    result.dptr = nullptr;
    result.dsize = 0;
    datum dbKey;

    dbKey.dptr = (DPTR_COERCE) key.c_str();
    dbKey.dsize = key.length();

    // Don't use the database if called from "monster".
    if (database)
        result = dbm_fetch(database, dbKey);

    return result;
}

static bool _database_has_entry(const datum &result)
{
    return result.dptr != nullptr;
}

static vector<string> _database_find_keys(DBM *database,
                                          const string &regex,
                                          bool ignore_case,
                                          db_find_filter filter = nullptr)
{
    text_pattern             tpat(regex, ignore_case);
    vector<string> matches;

    datum dbKey = dbm_firstkey(database);

    while (dbKey.dptr != nullptr)
    {
        string key((const char *)dbKey.dptr, dbKey.dsize);

        if (tpat.matches(key)
            && key.find("__") == string::npos
            && (filter == nullptr || !(*filter)(key, "")))
        {
            matches.push_back(key);
        }

        dbKey = dbm_nextkey(database);
    }

    return matches;
}

static vector<string> _database_find_bodies(DBM *database,
                                            const string &regex,
                                            bool ignore_case,
                                            db_find_filter filter = nullptr)
{
    text_pattern             tpat(regex, ignore_case);
    vector<string> matches;

    datum dbKey = dbm_firstkey(database);

    while (dbKey.dptr != nullptr)
    {
        string key((const char *)dbKey.dptr, dbKey.dsize);

        datum dbBody = dbm_fetch(database, dbKey);
        string body((const char *)dbBody.dptr, dbBody.dsize);

        if (tpat.matches(body)
            && key.find("__") == string::npos
            && (filter == nullptr || !(*filter)(key, body)))
        {
            matches.push_back(key);
        }

        dbKey = dbm_nextkey(database);
    }

    return matches;
}

///////////////////////////////////////////////////////////////////////////
// Internal DB utility functions
static textdb_phase0::rng_observation _observe_rng()
{
    textdb_phase0::rng_observation result;
    result.current_state = rng::current_generator().get_state();
    result.current_count = rng::current_generator().get_count();
    result.global_counts = rng::get_states();
    return result;
}

static bool _execute_embedded_lua(
    string &str, textdb_phase0::selection_trace *trace = nullptr)
{
    // Execute any lua code found between "{{" and "}}". The lua code
    // is expected to return a string, with which the lua code and
    // braces will be replaced.
    string::size_type pos = str.find("{{");
    size_t ordinal = 0;
    while (pos != string::npos)
    {
        size_t event_index = 0;
        if (trace)
        {
            textdb_phase0::lua_site_trace site;
            site.ordinal = ordinal;
            site.before = _observe_rng();
            event_index = trace->lua_sites.size();
            trace->lua_sites.push_back(site);
        }
        ++ordinal;
        string::size_type end = str.find("}}", pos + 2);
        if (end == string::npos)
        {
            if (trace)
            {
                textdb_phase0::lua_site_trace &site =
                    trace->lua_sites[event_index];
                site.source = str.substr(pos + 2);
                site.status = textdb_phase0::lua_site_status::UNBALANCED;
                site.after = _observe_rng();
            }
            mprf(MSGCH_DIAGNOSTICS, "Unbalanced {{, bailing.");
            return true;
        }

        string lua_full = str.substr(pos, end - pos + 2);
        string lua      = str.substr(pos + 2, end - pos - 2);
        if (trace)
            trace->lua_sites[event_index].source = lua;

        if (clua.execstring(lua.c_str(), "db_embedded_lua", 1))
        {
            string err = "{{" + clua.error + "}}";
            str.replace(pos, lua_full.length(), err);
            if (trace)
            {
                textdb_phase0::lua_site_trace &site =
                    trace->lua_sites[event_index];
                site.result = err;
                site.status = textdb_phase0::lua_site_status::ERROR;
                site.after = _observe_rng();
            }
            return true;
        }

        string result;
        clua.fnreturns(">s", &result);

        str.replace(pos, lua_full.length(), result);
        if (trace)
        {
            textdb_phase0::lua_site_trace &site =
                trace->lua_sites[event_index];
            site.result = result;
            site.status = textdb_phase0::lua_site_status::EXECUTED;
            site.after = _observe_rng();
        }

        pos = str.find("{{", pos + result.length());
    }
    return false;
}

static void _substitute_descriptions(TextDB &db, string &str,
                                     bool canonicalise_key, bool run_lua,
                                     bool untranslated)
{
    // Replace all keys found between "[[" and "]]" with corresponding
    // descriptions from the database.
    string::size_type pos = str.find("[[");
    while (pos != string::npos)
    {
        string::size_type end = str.find("]]", pos + 2);
        if (end == string::npos)
        {
            mprf(MSGCH_DIAGNOSTICS, "Unbalanced [[, bailing.");
            break;
        }

        string key = str.substr(pos + 2, end - pos - 2);
        string result = _query_database(db, key, canonicalise_key,
                                        run_lua, untranslated);
        str.replace(pos, key.length() + 4, trim_string_right(result));

        pos = str.find("[[", pos + result.length());
    }
}

static void _trim_leading_newlines(string &s)
{
    s.erase(0, s.find_first_not_of("\n"));
}

static void _add_entry(DBM *db, const string &k, const string &v)
{
    datum key, value;
    key.dptr = (char *) k.c_str();
    key.dsize = k.length();

    value.dptr = (char *) v.c_str();
    value.dsize = v.length();

    if (dbm_store(db, key, value, DBM_REPLACE))
        end(1, true, "Error storing %s", k.c_str());
}

using textdb_entry_consumer =
    std::function<void(const string &, const string &)>;

static void _parse_text_db(LineInput &inf,
                           const textdb_entry_consumer &consume,
                           bool trim_keys = true)
{
    string key;
    string value;

    bool in_entry = false;
    while (!inf.eof())
    {
        string line = inf.get_line();

        if (!line.empty() && line[0] == '#')
            continue;

        if (!line.compare(0, 4, "%%%%"))
        {
            if (!key.empty())
            {
                _trim_leading_newlines(value);
                consume(key, value);
            }
            key.clear();
            value.clear();
            in_entry = true;
            continue;
        }

        if (!in_entry)
            continue;

        if (key.empty())
        {
            key = line;
            if (trim_keys) trim_string(key);
            lowercase(key);
        }
        else
        {
            trim_string_right(line);
            value += line + "\n";
        }
    }

    if (!key.empty())
    {
        _trim_leading_newlines(value);
        consume(key, value);
    }
}

static void _parse_text_db(LineInput &inf, DBM *db, bool trim_keys = true)
{
    _parse_text_db(inf,
        [db](const string &key, const string &value)
        {
            _add_entry(db, key, value);
        }, trim_keys);
}

static void _store_text_db(const string &in, DBM *db, bool trim_keys)
{
    UTF8FileLineInput inf(in.c_str());
    if (inf.error())
        end(1, true, "Unable to open input file: %s", in.c_str());

    _parse_text_db(inf, db, trim_keys);
}

namespace
{
class textdb_string_line_input : public LineInput
{
public:
    explicit textdb_string_line_input(const string &text)
        : _text(text), _position(0), _seen_eof(false)
    {
    }

    bool eof() override { return _seen_eof; }

    string get_line() override
    {
        if (_position >= _text.size())
        {
            _seen_eof = true;
            return "";
        }

        const size_t newline = _text.find('\n', _position);
        if (newline == string::npos)
        {
            const string result = _text.substr(_position);
            _position = _text.size();
            return result;
        }

        const string result = _text.substr(_position, newline - _position);
        _position = newline + 1;
        return result;
    }

private:
    const string &_text;
    size_t _position;
    bool _seen_eof;
};

struct effective_textdb_entry
{
    string body;
    textdb_phase0::source_provenance provenance;
    vector<textdb_phase0::source_provenance> history;
};

using effective_textdb_entries = map<string, effective_textdb_entry>;

static void _record_canonical_entries(LineInput &input,
                                      const string &source_name,
                                      size_t load_index,
                                      effective_textdb_entries &entries,
                                      bool trim_keys)
{
    size_t definition_ordinal = 0;
    _parse_text_db(input,
        [&entries, &source_name, load_index, &definition_ordinal]
        (const string &key, const string &body)
        {
            effective_textdb_entry &entry = entries[key];
            entry.body = body;
            entry.provenance.source_name = source_name;
            entry.provenance.load_index = load_index;
            entry.provenance.definition_ordinal = definition_ordinal++;
            entry.history.push_back(entry.provenance);
        }, trim_keys);
}

static textdb_phase0::source_normalization_result
_normalize_textdb_source(string text)
{
    if (text.size() >= 3
        && static_cast<unsigned char>(text[0]) == 0xef
        && static_cast<unsigned char>(text[1]) == 0xbb
        && static_cast<unsigned char>(text[2]) == 0xbf)
    {
        text.erase(0, 3);
    }

    string normalized;
    normalized.reserve(text.size());
    for (size_t i = 0; i < text.size(); ++i)
    {
        if (text[i] == '\r')
        {
            if (i + 1 < text.size() && text[i + 1] == '\n')
                ++i;
            normalized += '\n';
        }
        else
            normalized += text[i];
    }
    textdb_phase0::source_normalization_result result;
    result.valid = false;
    if (normalized.find('\0') != string::npos)
    {
        result.error = "source contains an embedded NUL byte";
        return result;
    }

    string validated;
    validated.reserve(normalized.size());
    const char *cursor = normalized.c_str();
    while (*cursor)
    {
        char32_t character;
        const int consumed = utf8towc(&character, cursor);
        if (consumed <= 0)
            break;
        cursor += consumed;

        char encoded[4];
        const int encoded_size = wctoutf8(encoded, character);
        validated.append(encoded, encoded_size);
    }
    if (validated != normalized)
    {
        result.error = "source contains invalid UTF-8";
        return result;
    }

    result.valid = true;
    result.normalized_utf8 = normalized;
    return result;
}

static string _read_normalized_textdb_source(const string &path)
{
    std::ifstream input(path, std::ios::binary);
    if (!input)
        end(1, true, "Unable to open input file: %s", path.c_str());
    const string bytes((std::istreambuf_iterator<char>(input)),
                       std::istreambuf_iterator<char>());
    const textdb_phase0::source_normalization_result normalized =
        _normalize_textdb_source(bytes);
    if (!normalized.valid)
    {
        end(1, false, "Invalid TextDB source '%s': %s", path.c_str(),
            normalized.error.c_str());
    }
    return normalized.normalized_utf8;
}

static vector<textdb_phase0::canonical_entry>
_materialize_canonical_entries(const effective_textdb_entries &effective)
{
    vector<textdb_phase0::canonical_entry> result;
    result.reserve(effective.size());
    for (const auto &item : effective)
    {
        textdb_phase0::canonical_entry entry;
        entry.canonical_key = item.first;
        entry.provenance = item.second.provenance;
        entry.source_history = item.second.history;
        entry.raw_body = item.second.body;
        entry.body_empty = item.second.body.empty();

        const textdb_phase0::weighted_parse_result parsed =
            textdb_phase0::parse_weighted_entry_result(item.second.body);
        entry.parse_error = parsed.parse_error;
        entry.variants.reserve(parsed.variants.size());
        for (const textdb_phase0::weighted_variant &weighted
             : parsed.variants)
        {
            textdb_phase0::canonical_variant variant;
            variant.locator.canonical_key = item.first;
            variant.locator.variant_ordinal = weighted.variant_ordinal;
            variant.provenance = item.second.provenance;
            variant.weight = weighted.weight;
            variant.raw_pattern = weighted.raw_pattern;
            entry.variants.push_back(variant);
        }
        result.push_back(entry);
    }
    return result;
}
}

vector<textdb_phase0::canonical_entry>
textdb_phase0::canonicalise_sources(const vector<source> &sources,
                                    bool trim_keys)
{
    return canonicalise_source_dump(sources, trim_keys).entries;
}

textdb_phase0::source_normalization_result
textdb_phase0::normalize_textdb_source(const string &text)
{
    return _normalize_textdb_source(text);
}

textdb_phase0::canonical_speakdb_dump
textdb_phase0::canonicalise_source_dump(const vector<source> &sources,
                                        bool trim_keys)
{
    canonical_speakdb_dump dump;
    dump.schema_version = 1;
    dump.database_name = "speak";
    effective_textdb_entries effective;
    for (size_t i = 0; i < sources.size(); ++i)
    {
        source_snapshot snapshot;
        snapshot.source_name = sources[i].name;
        snapshot.load_index = i;
        const source_normalization_result normalized =
            normalize_textdb_source(sources[i].text);
        if (!normalized.valid)
        {
            end(1, false, "Invalid TextDB source '%s': %s",
                sources[i].name.c_str(), normalized.error.c_str());
        }
        snapshot.normalized_utf8 = normalized.normalized_utf8;
        dump.sources.push_back(snapshot);
        textdb_string_line_input input(dump.sources.back().normalized_utf8);
        _record_canonical_entries(input, sources[i].name, i, effective,
                                  trim_keys);
    }
    dump.entries = _materialize_canonical_entries(effective);
    return dump;
}

textdb_phase0::canonical_speakdb_dump
textdb_phase0::dump_canonical_english_speakdb_typed()
{
    canonical_speakdb_dump dump;
    dump.schema_version = 1;
    dump.database_name = "speak";
    dump.source_directory = SpeakDB.phase0_directory();
    effective_textdb_entries effective;
    const vector<string> &files = SpeakDB.phase0_input_files();
    for (size_t i = 0; i < files.size(); ++i)
    {
        const string relative = SpeakDB.phase0_directory() + files[i];
        const string path = datafile_path(relative, true);
        source_snapshot snapshot;
        snapshot.source_name = relative;
        snapshot.load_index = i;
        snapshot.normalized_utf8 = _read_normalized_textdb_source(path);
        dump.sources.push_back(snapshot);
        UTF8FileLineInput input(path.c_str());
        if (input.error())
            end(1, true, "Unable to open input file: %s", path.c_str());
        _record_canonical_entries(input, relative, i, effective, true);
    }
    dump.entries = _materialize_canonical_entries(effective);
    return dump;
}

vector<textdb_phase0::canonical_entry>
textdb_phase0::dump_canonical_english_speakdb()
{
    return dump_canonical_english_speakdb_typed().entries;
}

bool textdb_phase0::is_valid_textdb_locale(const string &language)
{
    const auto ascii_alpha = [](unsigned char c)
    {
        return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z');
    };
    const auto ascii_digit = [](unsigned char c)
    {
        return c >= '0' && c <= '9';
    };
    if (language.empty()
        || !ascii_alpha(static_cast<unsigned char>(language[0])))
    {
        return false;
    }
    for (const unsigned char c : language)
    {
        if (!ascii_alpha(c) && !ascii_digit(c) && c != '_' && c != '-')
            return false;
    }
    return true;
}

vector<string> textdb_phase0::order_localized_speakdb_sources(
    vector<string> files)
{
    files.erase(std::remove_if(files.begin(), files.end(),
        [](const string &file)
        {
            return file.size() < 3
                || file.compare(file.size() - 3, 3, "txt") != 0;
        }), files.end());
    // Mirror get_dir_files_ext(..., "txt"): project-default string sort.
    std::sort(files.begin(), files.end());
    const auto source = std::find(files.begin(), files.end(), "source.txt");
    if (source != files.end())
        std::rotate(files.begin(), source, source + 1);
    return files;
}

textdb_phase0::canonical_speakdb_dump
textdb_phase0::dump_localized_speakdb_typed(const string &language)
{
    if (!is_valid_textdb_locale(language))
    {
        end(1, false, "Invalid TextDB locale identifier: '%s'",
            language.c_str());
    }

    canonical_speakdb_dump dump;
    dump.schema_version = 1;
    dump.database_name = "speak";
    dump.source_directory = SpeakDB.phase0_directory() + language + "/";
    const string physical_directory = datafile_path(
        dump.source_directory, false, true, dir_exists);
    if (physical_directory.empty())
    {
        end(1, false, "Cannot find localized TextDB directory '%s'",
            dump.source_directory.c_str());
    }

    const vector<string> files = order_localized_speakdb_sources(
        get_dir_files_ext(physical_directory, "txt"));
    effective_textdb_entries effective;
    for (size_t i = 0; i < files.size(); ++i)
    {
        const string relative = dump.source_directory + files[i];
        const string path = datafile_path(relative, false);
        source_snapshot snapshot;
        snapshot.source_name = relative;
        snapshot.load_index = i;
        snapshot.normalized_utf8 = _read_normalized_textdb_source(path);
        dump.sources.push_back(snapshot);
        UTF8FileLineInput input(path.c_str());
        if (input.error())
            end(1, true, "Unable to open input file: %s", path.c_str());
        _record_canonical_entries(input, relative, i, effective, true);
    }
    dump.entries = _materialize_canonical_entries(effective);
    return dump;
}

namespace
{
struct parsed_weighted_entry
{
    vector<textdb_phase0::weighted_variant> variants;
    string error;
};

static parsed_weighted_entry _parse_weighted_entry(const string &entry)
{
    parsed_weighted_entry parsed;
    vector<string> lines = split_string("\n", entry, false, true);

    for (int i = 0, size = lines.size(); i < size; i++)
    {
        // Skip over multiple blank lines, and leading and trailing
        // blank lines.
        while (i < size && lines[i].empty())
            i++;

        if (i == size)
            break;

        int         weight;
        string part = "";

        if (sscanf(lines[i].c_str(), "w:%d", &weight))
        {
            i++;
            if (i == size)
            {
                parsed.error = "BUG, WEIGHT AT END OF ENTRY";
                return parsed;
            }
        }
        else
            weight = 10;

        while (i < size && !lines[i].empty())
        {
            part += lines[i++];
            part += "\n";
        }
        trim_string(part);

        textdb_phase0::weighted_variant variant;
        variant.variant_ordinal = parsed.variants.size();
        variant.weight = weight;
        variant.raw_pattern = part;
        parsed.variants.push_back(variant);
    }

    if (parsed.variants.empty())
        parsed.error = "BUG, EMPTY ENTRY";
    return parsed;
}

struct weighted_trace_context
{
    textdb_phase0::selection_trace *trace = nullptr;
    string requested_key;
    string resolved_key;
    vector<size_t> recursion_path;
    int recursion_depth = 0;
    int replacement_count = 0;
};

struct weighted_choice_result
{
    bool selected = false;
    string pattern;
    size_t variant_ordinal = static_cast<size_t>(-1);
    int weight = 0;
};

static weighted_choice_result _choose_weighted_variants(
    const vector<textdb_phase0::weighted_variant> &variants,
    int fixed_weight, const weighted_trace_context *context = nullptr)
{
    int total_weight = 0;
    for (const textdb_phase0::weighted_variant &variant : variants)
        total_weight += variant.weight;

    size_t event_index = 0;
    if (context && context->trace)
    {
        textdb_phase0::weighted_choice_trace event;
        event.requested_key = context->requested_key;
        event.resolved_canonical_key = context->resolved_key;
        event.recursion_path = context->recursion_path;
        event.recursion_depth = context->recursion_depth;
        event.replacement_count = context->replacement_count;
        event.variant_ordinal = static_cast<size_t>(-1);
        event.weight = 0;
        event.total_bound = total_weight;
        event.before = _observe_rng();
        event_index = context->trace->weighted_choices.size();
        context->trace->weighted_choices.push_back(event);
    }

    int choice = 0;
    if (fixed_weight != -1)
        choice = fixed_weight % total_weight;
    else
        choice = random2(total_weight);
    if (context && context->trace)
    {
        textdb_phase0::weighted_choice_trace &event =
            context->trace->weighted_choices[event_index];
        event.random_result = choice;
        event.after = _observe_rng();
    }

    int cumulative_weight = 0;
    for (const textdb_phase0::weighted_variant &variant : variants)
    {
        cumulative_weight += variant.weight;
        if (choice < cumulative_weight)
        {
            weighted_choice_result result;
            result.selected = true;
            result.pattern = variant.raw_pattern;
            result.variant_ordinal = variant.variant_ordinal;
            result.weight = variant.weight;
            if (context && context->trace)
            {
                textdb_phase0::weighted_choice_trace &event =
                    context->trace->weighted_choices[event_index];
                event.variant_ordinal = variant.variant_ordinal;
                event.weight = variant.weight;
            }
            return result;
        }
    }
    weighted_choice_result result;
    result.pattern = "BUG, NO STRING CHOSEN";
    return result;
}
}

vector<textdb_phase0::weighted_variant>
textdb_phase0::parse_weighted_entry(const string &entry)
{
    return parse_weighted_entry_result(entry).variants;
}

textdb_phase0::weighted_parse_result
textdb_phase0::parse_weighted_entry_result(const string &entry)
{
    const parsed_weighted_entry parsed = _parse_weighted_entry(entry);
    weighted_parse_result result;
    result.variants = parsed.variants;
    result.parse_error = parsed.error;
    return result;
}

string textdb_phase0::choose_weighted_entry(const string &entry,
                                             int fixed_weight)
{
    const parsed_weighted_entry parsed = _parse_weighted_entry(entry);

    if (!parsed.error.empty())
        return parsed.error;
    return _choose_weighted_variants(parsed.variants, fixed_weight).pattern;
}

#define MAX_RECURSION_DEPTH 10
#define MAX_REPLACEMENTS    100

struct weighted_lookup_result
{
    textdb_phase0::raw_selection_status status =
        textdb_phase0::raw_selection_status::MISSING;
    string pattern;
    string resolved_key;
    size_t variant_ordinal = static_cast<size_t>(-1);
    int weight = 0;
};

static weighted_lookup_result _getWeightedSelection(
    TextDB &db, const string &key, const string &suffix,
    bool base_only, textdb_phase0::selection_trace *trace,
    const vector<size_t> &recursion_path, int recursion_depth,
    int replacement_count)
{
    // We have to canonicalise the key (in case the user typed it
    // in and got the case wrong.)
    string canonical_key = key + suffix;
    lowercase(canonical_key);

    // Query the DB.
    datum result;
    result.dptr = nullptr;
    result.dsize = 0;

    if (!base_only && db.translation)
        result = _database_fetch(db.translation->get(), canonical_key);
    // _database_has_entry returns true even for zero-length (dsize == 0)
    // entries — treat those as not found so we fall back to the base DB.
    if (!_database_has_entry(result) || result.dsize == 0)
        result = _database_fetch(db.get(), canonical_key);

    if (!_database_has_entry(result) || result.dsize == 0)
    {
        // Try ignoring the suffix.
        canonical_key = key;
        lowercase(canonical_key);

        // Query the DB.
        if (!base_only && db.translation)
            result = _database_fetch(db.translation->get(), canonical_key);
        if (!_database_has_entry(result) || result.dsize == 0)
            result = _database_fetch(db.get(), canonical_key);

        if (!_database_has_entry(result) || result.dsize == 0)
            return weighted_lookup_result();
    }

    // Cons up a (C++) string to return. The caller must release it.
    string str = string((const char *)result.dptr, result.dsize);
    if (str.empty())
        return weighted_lookup_result();

    weighted_lookup_result result_value;
    result_value.resolved_key = canonical_key;
    const parsed_weighted_entry parsed = _parse_weighted_entry(str);
    if (!parsed.error.empty())
    {
        result_value.status = textdb_phase0::raw_selection_status::CORRUPT;
        result_value.pattern = parsed.error;
        return result_value;
    }

    weighted_trace_context context;
    weighted_trace_context *context_ptr = nullptr;
    if (trace)
    {
        // Keep the legacy no-observer path free of trace-only string/vector
        // copies; all identity data is populated only when requested.
        context.trace = trace;
        context.requested_key = key;
        context.resolved_key = canonical_key;
        context.recursion_path = recursion_path;
        context.recursion_depth = recursion_depth;
        context.replacement_count = replacement_count;
        context_ptr = &context;
    }
    const weighted_choice_result chosen =
        _choose_weighted_variants(parsed.variants, -1, context_ptr);
    result_value.pattern = chosen.pattern;
    result_value.variant_ordinal = chosen.variant_ordinal;
    result_value.weight = chosen.weight;
    result_value.status = chosen.selected
        ? textdb_phase0::raw_selection_status::SELECTED
        : textdb_phase0::raw_selection_status::CORRUPT;
    return result_value;
}

template <typename Lookup>
static bool _call_recursive_replacement(
                                        string &str,
                                        const Lookup &lookup,
                                        const string &suffix,
                                        int &num_replacements,
                                        int recursion_depth,
                                        const vector<size_t> &recursion_path,
                                        textdb_phase0::selection_trace *trace);

template <typename Lookup>
static string _getRandomisedStr(const Lookup &lookup,
                                const string &key,
                                const string &suffix,
                                int &num_replacements,
                                int recursion_depth,
                                const vector<size_t> &recursion_path,
                                textdb_phase0::selection_trace *trace,
                                textdb_phase0::recursive_site_status *status,
                                bool *corrupt_found = nullptr)
{
    recursion_depth++;
    if (recursion_depth > MAX_RECURSION_DEPTH)
    {
        if (status)
            *status = textdb_phase0::recursive_site_status::DEPTH_LIMIT;
        mprf(MSGCH_DIAGNOSTICS, "Too many nested replacements, bailing.");
        if (corrupt_found)
            *corrupt_found = true;

        return "TOO MUCH RECURSION";
    }

    const weighted_lookup_result selected =
        lookup(key, suffix, trace, recursion_path, recursion_depth,
               num_replacements);
    if (status)
    {
        switch (selected.status)
        {
        case textdb_phase0::raw_selection_status::SELECTED:
            *status = textdb_phase0::recursive_site_status::SELECTED;
            break;
        case textdb_phase0::raw_selection_status::CORRUPT:
            *status = textdb_phase0::recursive_site_status::CORRUPT;
            break;
        case textdb_phase0::raw_selection_status::MISSING:
            *status = textdb_phase0::recursive_site_status::MISSING;
            break;
        }
    }
    string str = selected.pattern;

    const bool nested_corrupt = _call_recursive_replacement(
        str, lookup, suffix, num_replacements, recursion_depth,
        recursion_path, trace);
    if (corrupt_found)
    {
        *corrupt_found = selected.status
                             == textdb_phase0::raw_selection_status::CORRUPT
                         || nested_corrupt;
    }

    return str;
}

// Replace any "@foo@" markers that can be found in this database.
// Those that can't be found are left alone for the caller to deal with.
template <typename Lookup>
static bool _call_recursive_replacement(string &str,
                                        const Lookup &lookup,
                                        const string &suffix,
                                        int &num_replacements,
                                        int recursion_depth,
                                        const vector<size_t> &recursion_path,
                                        textdb_phase0::selection_trace *trace)
{
    bool corrupt_found = false;
    string::size_type pos = str.find("@");
    size_t site_ordinal = 0;
    while (pos != string::npos)
    {
        const size_t current_site = site_ordinal++;
        num_replacements++;
        if (num_replacements > MAX_REPLACEMENTS)
        {
            if (trace)
            {
                textdb_phase0::recursive_site_trace event;
                const string::size_type limit_end = str.find("@", pos + 1);
                event.marker = limit_end == string::npos
                    ? str.substr(pos + 1)
                    : str.substr(pos + 1, limit_end - pos - 1);
                event.recursion_path = recursion_path;
                event.recursion_path.push_back(current_site);
                event.recursion_depth = recursion_depth + 1;
                event.replacement_count = num_replacements;
                event.status = textdb_phase0::recursive_site_status::
                    REPLACEMENT_LIMIT;
                trace->recursive_sites.push_back(event);
            }
            mprf(MSGCH_DIAGNOSTICS, "Too many string replacements, bailing.");
            return true;
        }

        string::size_type end = str.find("@", pos + 1);
        if (end == string::npos)
        {
            if (trace)
            {
                textdb_phase0::recursive_site_trace event;
                event.marker = str.substr(pos + 1);
                event.recursion_path = recursion_path;
                event.recursion_path.push_back(current_site);
                event.recursion_depth = recursion_depth + 1;
                event.replacement_count = num_replacements;
                event.status =
                    textdb_phase0::recursive_site_status::UNBALANCED;
                trace->recursive_sites.push_back(event);
            }
            mprf(MSGCH_DIAGNOSTICS, "Unbalanced @, bailing.");
            corrupt_found = true;
            break;
        }

        string marker_full = str.substr(pos, end - pos + 1);
        string marker      = str.substr(pos + 1, end - pos - 1);

        // Legacy callers have no observer and carry the same empty path
        // through recursion, avoiding a vector copy/allocation per marker.
        const vector<size_t> *child_path = &recursion_path;
        vector<size_t> traced_child_path;
        size_t event_index = 0;
        if (trace)
        {
            traced_child_path = recursion_path;
            traced_child_path.push_back(current_site);
            child_path = &traced_child_path;
            textdb_phase0::recursive_site_trace event;
            event.recursion_path = traced_child_path;
            event.marker = marker;
            event.recursion_depth = recursion_depth + 1;
            event.replacement_count = num_replacements;
            event.status = textdb_phase0::recursive_site_status::MISSING;
            event_index = trace->recursive_sites.size();
            trace->recursive_sites.push_back(event);
        }

        textdb_phase0::recursive_site_status child_status =
            textdb_phase0::recursive_site_status::MISSING;
        bool child_corrupt = false;
        string replacement =
            _getRandomisedStr(lookup, marker, suffix, num_replacements,
                              recursion_depth, *child_path, trace,
                              &child_status, &child_corrupt);
        corrupt_found = corrupt_found || child_corrupt;
        if (trace)
            trace->recursive_sites[event_index].status = child_status;

        if (replacement.empty())
        {
            // Nothing in database, leave it alone and go onto next @foo@
            pos = str.find("@", end + 1);
        }
        else
        {
            str.replace(pos, marker_full.length(), replacement);

            // Start search from pos rather than end + 1, so that if
            // the replacement contains its own @foo@, we can replace
            // that too.
            pos = str.find("@", pos);
        }
    } // while (pos != string::npos)
    return corrupt_found;
}

static string _getRandomisedStr(TextDB &db, const string &key,
                                const string &suffix,
                                int &num_replacements,
                                int recursion_depth = 0)
{
    const auto lookup =
        [&db](const string &lookup_key, const string &lookup_suffix,
              textdb_phase0::selection_trace *trace,
              const vector<size_t> &path, int depth, int replacements)
        {
            return _getWeightedSelection(db, lookup_key, lookup_suffix,
                                         false, trace, path, depth,
                                         replacements);
        };
    const vector<size_t> path;
    return _getRandomisedStr(lookup, key, suffix, num_replacements,
                             recursion_depth, path, nullptr, nullptr);
}

using canonical_weighted_lookup = std::function<weighted_lookup_result(
    const string &, const string &, textdb_phase0::selection_trace *,
    const vector<size_t> &, int, int)>;

static canonical_weighted_lookup _canonical_weighted_lookup(
    const vector<textdb_phase0::canonical_entry> &entries)
{
    const auto find_entry = [&entries](string canonical_key)
        -> const textdb_phase0::canonical_entry *
    {
        lowercase(canonical_key);
        const auto found = std::lower_bound(entries.begin(), entries.end(),
            canonical_key,
            [](const textdb_phase0::canonical_entry &entry,
               const string &candidate)
            {
                return entry.canonical_key < candidate;
            });
        if (found == entries.end() || found->canonical_key != canonical_key)
        {
            return nullptr;
        }
        // Only a zero-length TextDB value is MISSING before the chooser. A
        // non-empty body that parses to no variants must return its BUG text.
        if (found->body_empty)
            return nullptr;
        if (found->variants.empty() && found->parse_error.empty())
            return nullptr;
        return &*found;
    };

    return [find_entry](const string &lookup_key, const string &suffix,
                        textdb_phase0::selection_trace *trace,
                        const vector<size_t> &path, int depth,
                        int replacements)
        {
            const textdb_phase0::canonical_entry *entry =
                find_entry(lookup_key + suffix);
            if (!entry)
                entry = find_entry(lookup_key);
            if (!entry)
                return weighted_lookup_result();

            weighted_lookup_result result;
            result.resolved_key = entry->canonical_key;
            if (!entry->parse_error.empty())
            {
                result.status = textdb_phase0::raw_selection_status::CORRUPT;
                result.pattern = entry->parse_error;
                return result;
            }

            vector<textdb_phase0::weighted_variant> variants;
            variants.reserve(entry->variants.size());
            for (const textdb_phase0::canonical_variant &canonical
                 : entry->variants)
            {
                textdb_phase0::weighted_variant variant;
                variant.variant_ordinal = canonical.locator.variant_ordinal;
                variant.weight = canonical.weight;
                variant.raw_pattern = canonical.raw_pattern;
                variants.push_back(variant);
            }
            weighted_trace_context context;
            context.trace = trace;
            context.requested_key = lookup_key;
            context.resolved_key = entry->canonical_key;
            context.recursion_path = path;
            context.recursion_depth = depth;
            context.replacement_count = replacements;
            const weighted_choice_result chosen =
                _choose_weighted_variants(variants, -1, &context);
            result.pattern = chosen.pattern;
            result.variant_ordinal = chosen.variant_ordinal;
            result.weight = chosen.weight;
            result.status = chosen.selected
                ? textdb_phase0::raw_selection_status::SELECTED
                : textdb_phase0::raw_selection_status::CORRUPT;
            return result;
        };
}

textdb_phase0::raw_selection textdb_phase0::select_canonical_english(
    const vector<canonical_entry> &entries, const string &key)
{
    raw_selection result;
    result.status = raw_selection_status::MISSING;
    const vector<size_t> path;
    const weighted_lookup_result selected =
        _canonical_weighted_lookup(entries)(key, "", &result.trace, path,
                                             1, 0);
    result.status = selected.status;
    result.raw_pattern = selected.pattern;
    result.locator.canonical_key = selected.resolved_key;
    result.locator.variant_ordinal = selected.variant_ordinal;
    return result;
}

textdb_phase0::expanded_selection textdb_phase0::expand_canonical_selection(
    const vector<canonical_entry> &entries, const raw_selection &selection)
{
    expanded_selection result;
    result.status = selection.status;
    result.text = selection.raw_pattern;
    result.trace = selection.trace;
    int num_replacements = 0;
    if (selection.status == raw_selection_status::SELECTED)
    {
        const vector<size_t> path;
        const bool recursive_corrupt = _call_recursive_replacement(
            result.text, _canonical_weighted_lookup(entries), "",
            num_replacements, 1, path, &result.trace);
        // Preserve the legacy expansion/Lua output and RNG trace even when a
        // recursive entry is corrupt. The typed state below prevents any
        // later target binding or bracket materialization.
        const bool lua_corrupt = _execute_embedded_lua(result.text,
                                                       &result.trace);
        if (recursive_corrupt || lua_corrupt)
            result.status = raw_selection_status::CORRUPT;
    }
    result.trace.final_replacement_count = num_replacements;
    return result;
}

string textdb_phase0::expand_canonical_speakdb(
    const vector<canonical_entry> &entries, const string &key)
{
    return expand_canonical_selection(entries,
               select_canonical_english(entries, key)).text;
}

textdb_phase0::expanded_selection textdb_phase0::materialize_embedded_lua(
    const string &pattern)
{
    expanded_selection result;
    result.status = raw_selection_status::SELECTED;
    result.text = pattern;
    if (_execute_embedded_lua(result.text, &result.trace))
        result.status = raw_selection_status::CORRUPT;
    return result;
}

textdb_phase0::message_candidate_evaluation
textdb_phase0::evaluate_message_candidate(
    const vector<canonical_entry> &entries, const string &key,
    message_attempt attempt, bool manifest_applicable)
{
    message_candidate_evaluation result;
    result.result = message_result::MISSING;
    result.applicability_checked = false;
    result.post_expansion_materialized = false;

    const raw_selection raw = select_canonical_english(entries, key);
    result.trace = raw.trace;
    if (raw.status == raw_selection_status::MISSING)
        return result;
    if (raw.status == raw_selection_status::CORRUPT)
    {
        result.result = message_result::CORRUPT;
        return result;
    }

    const expanded_selection expanded =
        expand_canonical_selection(entries, raw);
    result.expanded_text = expanded.text;
    result.trace = expanded.trace;
    if (expanded.status == raw_selection_status::CORRUPT)
    {
        result.result = message_result::CORRUPT;
        return result;
    }
    if (result.expanded_text == "__NONE")
    {
        result.result = message_result::SUPPRESS;
        return result;
    }

    if (attempt == message_attempt::SILENT_UNPREFIXED_FALLBACK)
    {
        result.result = result.expanded_text.empty()
            ? message_result::INAPPLICABLE : message_result::RENDERED;
        return result;
    }

    result.applicability_checked = true;
    result.result = !result.expanded_text.empty() && manifest_applicable
        ? message_result::RENDERED : message_result::INAPPLICABLE;
    return result;
}

textdb_phase0::message_search_action
textdb_phase0::transition_message_candidate(message_attempt attempt,
                                             message_result result)
{
    switch (result)
    {
    case message_result::SUPPRESS:
        return message_search_action::STOP_SILENT;
    case message_result::RENDERED:
        return message_search_action::STOP_RENDERED;
    case message_result::CORRUPT:
        return message_search_action::STOP_CORRUPT;
    case message_result::MISSING:
    case message_result::INAPPLICABLE:
        return attempt == message_attempt::SILENT_PREFIXED
            ? message_search_action::RETRY_UNPREFIXED
            : message_search_action::NEXT_CANDIDATE;
    }
    die("Invalid Phase 0 message result");
}

namespace
{
struct legacy_random_trace_context
{
    textdb_phase0::legacy_materialization *result;
    const textdb_phase0::canonical_pre_random_pattern *pattern;
    const vector<textdb_phase0::selected_recursive_variant>
        *recursive_variants;
};

static void _record_legacy_random_site(
    const random_substring_choice_trace &choice, void *opaque)
{
    legacy_random_trace_context &context =
        *static_cast<legacy_random_trace_context *>(opaque);
    textdb_phase0::legacy_random_site site;
    site.identity.top_locator = context.pattern->top_locator;
    site.identity.recursive_variants = *context.recursive_variants;
    site.identity.expanded_site_ordinal = choice.site_ordinal;
    site.option_count = choice.random_bound;
    site.option_index = choice.selected_index;
    context.result->sites.push_back(site);
}
}

textdb_phase0::legacy_materialization
textdb_phase0::materialize_legacy_randomness(
    const canonical_pre_random_pattern &pattern)
{
    legacy_materialization result;
    result.status = legacy_materialization_status::CORRUPT;
    result.randomized_pattern_en = pattern.pattern_en;
    result.before = _observe_rng();

    static const char *runtime_tokens[] =
    {
        "@at@",
        "@target@",
        "@beam@",
    };
    for (const char *token : runtime_tokens)
    {
        if (pattern.pattern_en.find(token) != string::npos)
        {
            result.error = "unbound runtime token: " + string(token);
            result.after = _observe_rng();
            return result;
        }
    }

    vector<selected_recursive_variant> recursive_variants;
    for (const weighted_choice_trace &choice
         : pattern.selection.weighted_choices)
    {
        if (choice.recursion_path.empty()
            || choice.variant_ordinal == static_cast<size_t>(-1))
        {
            continue;
        }
        selected_recursive_variant selected;
        selected.locator.canonical_key = choice.resolved_canonical_key;
        selected.locator.variant_ordinal = choice.variant_ordinal;
        selected.recursion_path = choice.recursion_path;
        recursive_variants.push_back(selected);
    }

    legacy_random_trace_context trace_context =
        { &result, &pattern, &recursive_variants };
    random_substring_trace_observer observer;
    observer.function = _record_legacy_random_site;
    observer.context = &trace_context;
    result.randomized_pattern_en = maybe_pick_random_substring(
        pattern.pattern_en, &observer);
    result.status = legacy_materialization_status::MATERIALIZED;
    result.after = _observe_rng();
    return result;
}

namespace
{
canonical_textdb::rng_observation _production_rng_observation(
    const textdb_phase0::rng_observation &source)
{
    canonical_textdb::rng_observation result;
    result.current_state = source.current_state;
    result.current_count = source.current_count;
    result.global_counts = source.global_counts;
    return result;
}

canonical_textdb::recursive_site_status _production_recursive_status(
    textdb_phase0::recursive_site_status status)
{
    using source = textdb_phase0::recursive_site_status;
    using target = canonical_textdb::recursive_site_status;
    switch (status)
    {
    case source::SELECTED:          return target::SELECTED;
    case source::CORRUPT:           return target::CORRUPT;
    case source::MISSING:           return target::MISSING;
    case source::UNBALANCED:        return target::UNBALANCED;
    case source::DEPTH_LIMIT:       return target::DEPTH_LIMIT;
    case source::REPLACEMENT_LIMIT: return target::REPLACEMENT_LIMIT;
    }
    return target::CORRUPT;
}

canonical_textdb::lua_site_status _production_lua_status(
    textdb_phase0::lua_site_status status)
{
    using source = textdb_phase0::lua_site_status;
    using target = canonical_textdb::lua_site_status;
    switch (status)
    {
    case source::EXECUTED:   return target::EXECUTED;
    case source::ERROR:      return target::ERROR;
    case source::UNBALANCED: return target::UNBALANCED;
    }
    return target::ERROR;
}

void _append_signature_string(string &signature, const string &value)
{
    signature += std::to_string(value.size());
    signature += ':';
    signature += value;
}

string _production_materialization_signature(
    const canonical_textdb::loaded_candidate &candidate,
    const canonical_textdb::randomized_pattern &materialized)
{
    if (candidate.selected_variants.size() == 1
        && candidate.trace.lua_sites.empty() && materialized.sites.empty())
    {
        return "NONE";
    }

    string signature = "materialization-v1|variants=";
    signature += std::to_string(candidate.selected_variants.size());
    for (const canonical_textdb::selected_variant &selected
         : candidate.selected_variants)
    {
        signature += '|';
        _append_signature_string(signature,
                                 selected.locator.canonical_key);
        signature += ':' + std::to_string(selected.locator.variant_ordinal);
        signature += ':' + std::to_string(selected.recursion_path.size());
        for (const size_t step : selected.recursion_path)
            signature += ':' + std::to_string(step);
    }
    signature += "|lua=" +
                 std::to_string(candidate.trace.lua_sites.size());
    for (const canonical_textdb::lua_site_trace &site
         : candidate.trace.lua_sites)
    {
        signature += '|';
        signature += std::to_string(site.ordinal);
        signature += ':' + std::to_string(static_cast<int>(site.status));
        signature += ':';
        _append_signature_string(signature, site.source);
        signature += ':';
        _append_signature_string(signature, site.result);
    }
    signature += "|sites=" + std::to_string(materialized.sites.size());
    for (const canonical_textdb::randomized_pattern::site &site
         : materialized.sites)
    {
        signature += '|';
        _append_signature_string(signature, site.top_locator.canonical_key);
        signature += ':' +
                     std::to_string(site.top_locator.variant_ordinal);
        signature += ':' + std::to_string(site.expanded_site_ordinal);
        signature += ':' + std::to_string(site.option_count);
        signature += ':' + std::to_string(site.option_index);
    }
    return signature;
}
}

canonical_textdb::loaded_candidate
canonical_textdb::expand_loaded_english_candidate(const string &key)
{
    loaded_candidate result;
    result.before = _production_rng_observation(_observe_rng());
    const textdb_phase0::expanded_selection expanded =
        textdb_phase0::expand_loaded_canonical_english_speakdb_traced(key);
    result.expanded_pattern_en = expanded.text;
    result.recursive_site_count = expanded.trace.recursive_sites.size();
    result.lua_site_count = expanded.trace.lua_sites.size();
    result.trace.final_replacement_count =
        expanded.trace.final_replacement_count;
    switch (expanded.status)
    {
    case textdb_phase0::raw_selection_status::MISSING:
        result.status = candidate_status::MISSING;
        result.error = "canonical key missing";
        break;
    case textdb_phase0::raw_selection_status::CORRUPT:
        result.status = candidate_status::CORRUPT;
        result.error = "canonical expansion corrupt";
        break;
    case textdb_phase0::raw_selection_status::SELECTED:
        result.status = candidate_status::SELECTED;
        break;
    }
    for (const textdb_phase0::weighted_choice_trace &choice
         : expanded.trace.weighted_choices)
    {
        weighted_choice_trace event;
        event.requested_key = choice.requested_key;
        event.resolved_canonical_key = choice.resolved_canonical_key;
        event.recursion_path = choice.recursion_path;
        event.recursion_depth = choice.recursion_depth;
        event.replacement_count = choice.replacement_count;
        event.variant_ordinal = choice.variant_ordinal;
        event.weight = choice.weight;
        event.total_bound = choice.total_bound;
        event.random_result = choice.random_result;
        event.before = _production_rng_observation(choice.before);
        event.after = _production_rng_observation(choice.after);
        result.trace.weighted_choices.push_back(event);
        selected_variant selected;
        selected.locator.canonical_key = choice.resolved_canonical_key;
        selected.locator.variant_ordinal = choice.variant_ordinal;
        selected.recursion_path = choice.recursion_path;
        result.selected_variants.push_back(selected);
        if (choice.recursion_path.empty()
            && result.top_locator.canonical_key.empty())
        {
            result.top_locator = selected.locator;
        }
    }
    for (const textdb_phase0::recursive_site_trace &site
         : expanded.trace.recursive_sites)
    {
        recursive_site_trace event;
        event.recursion_path = site.recursion_path;
        event.marker = site.marker;
        event.recursion_depth = site.recursion_depth;
        event.replacement_count = site.replacement_count;
        event.status = _production_recursive_status(site.status);
        result.trace.recursive_sites.push_back(event);
    }
    for (const textdb_phase0::lua_site_trace &site
         : expanded.trace.lua_sites)
    {
        lua_site_trace event;
        event.ordinal = site.ordinal;
        event.source = site.source;
        event.result = site.result;
        event.status = _production_lua_status(site.status);
        event.before = _production_rng_observation(site.before);
        event.after = _production_rng_observation(site.after);
        result.trace.lua_sites.push_back(event);
    }
    if (result.status == candidate_status::SELECTED
        && result.top_locator.canonical_key.empty())
    {
        result.status = candidate_status::CORRUPT;
        result.error = "canonical top-level locator missing";
    }
    result.after = _production_rng_observation(_observe_rng());
    return result;
}

canonical_textdb::randomized_pattern
canonical_textdb::materialize_bound_legacy_randomness(
    const loaded_candidate &candidate, const string &bound_pattern_en)
{
    randomized_pattern result;
    result.before = _production_rng_observation(_observe_rng());
    if (candidate.status != candidate_status::SELECTED
        || candidate.top_locator.canonical_key.empty())
    {
        result.error = "canonical candidate is not selected";
        result.after = _production_rng_observation(_observe_rng());
        return result;
    }
    static const char *const runtime_tokens[] =
    {
        "@at@", "@target@", "@beam@",
    };
    for (const char *token : runtime_tokens)
    {
        if (bound_pattern_en.find(token) != string::npos)
        {
            result.error = "unbound runtime token: " + string(token);
            result.after = _production_rng_observation(_observe_rng());
            return result;
        }
    }
    ASSERT(bound_pattern_en.find("@at@") == string::npos);
    ASSERT(bound_pattern_en.find("@target@") == string::npos);
    ASSERT(bound_pattern_en.find("@beam@") == string::npos);

    textdb_phase0::canonical_pre_random_pattern pattern;
    pattern.top_locator.canonical_key = candidate.top_locator.canonical_key;
    pattern.top_locator.variant_ordinal =
        candidate.top_locator.variant_ordinal;
    pattern.pattern_en = bound_pattern_en;
    for (const selected_variant &selected : candidate.selected_variants)
    {
        textdb_phase0::weighted_choice_trace choice;
        choice.resolved_canonical_key = selected.locator.canonical_key;
        choice.variant_ordinal = selected.locator.variant_ordinal;
        choice.recursion_path = selected.recursion_path;
        pattern.selection.weighted_choices.push_back(choice);
    }
    const textdb_phase0::legacy_materialization materialized =
        textdb_phase0::materialize_legacy_randomness(pattern);
    result.pattern_en = materialized.randomized_pattern_en;
    result.random_site_count = materialized.sites.size();
    for (const textdb_phase0::legacy_random_site &site : materialized.sites)
    {
        randomized_pattern::site event;
        event.top_locator.canonical_key =
            site.identity.top_locator.canonical_key;
        event.top_locator.variant_ordinal =
            site.identity.top_locator.variant_ordinal;
        for (const textdb_phase0::selected_recursive_variant &recursive
             : site.identity.recursive_variants)
        {
            selected_variant selected;
            selected.locator.canonical_key =
                recursive.locator.canonical_key;
            selected.locator.variant_ordinal =
                recursive.locator.variant_ordinal;
            selected.recursion_path = recursive.recursion_path;
            event.recursive_variants.push_back(selected);
        }
        event.expanded_site_ordinal = site.identity.expanded_site_ordinal;
        event.option_count = site.option_count;
        event.option_index = site.option_index;
        result.sites.push_back(event);
    }
    result.before = _production_rng_observation(materialized.before);
    result.after = _production_rng_observation(materialized.after);
    result.error = materialized.error;
    if (materialized.status
        == textdb_phase0::legacy_materialization_status::MATERIALIZED)
    {
        result.status = candidate_status::SELECTED;
        result.signature = _production_materialization_signature(candidate,
                                                                  result);
    }
    else
        result.status = candidate_status::CORRUPT;
    return result;
}

canonical_textdb::rng_observation canonical_textdb::observe_rng()
{
    return _production_rng_observation(_observe_rng());
}

textdb_phase0::structured_message_materialization
textdb_phase0::materialize_structured_message(
    const vector<canonical_entry> &entries, const string &key,
    message_runtime_binding_resolver resolve_bindings, void *context)
{
    structured_message_materialization result;
    result.total_before = _observe_rng();

    const raw_selection raw = select_canonical_english(entries, key);
    result.top_locator = raw.locator;
    const expanded_selection expanded =
        expand_canonical_selection(entries, raw);
    result.status = expanded.status;
    result.expanded_pattern_en = expanded.text;
    result.database_trace = expanded.trace;
    result.database_after = _observe_rng();
    if (expanded.status != raw_selection_status::SELECTED)
    {
        result.error = expanded.status == raw_selection_status::MISSING
            ? "canonical key missing" : "canonical expansion corrupt";
        result.total_after = _observe_rng();
        return result;
    }

    result.binding_trace.before = _observe_rng();
    if (!resolve_bindings)
    {
        result.status = raw_selection_status::CORRUPT;
        result.error = "runtime binding resolver missing";
        result.binding_trace.after = _observe_rng();
        result.total_after = result.binding_trace.after;
        return result;
    }
    result.binding_trace.values = resolve_bindings(context);
    result.binding_trace.after = _observe_rng();

    const message_runtime_bindings &bindings = result.binding_trace.values;
    result.bound_pattern_en = replace_all(
        result.expanded_pattern_en, "@The_monster@",
        bindings.actor_sentence_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@the_monster@", bindings.actor_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@at@", bindings.relation_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@target@", bindings.target_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@beam@", bindings.beam_en);

    canonical_pre_random_pattern pre_random;
    pre_random.top_locator = result.top_locator;
    pre_random.selection = result.database_trace;
    pre_random.pattern_en = result.bound_pattern_en;
    result.substring_trace = materialize_legacy_randomness(pre_random);
    if (result.substring_trace.status !=
        legacy_materialization_status::MATERIALIZED)
    {
        result.status = raw_selection_status::CORRUPT;
        result.error = result.substring_trace.error;
    }
    else
    {
        result.randomized_message_en =
            result.substring_trace.randomized_pattern_en;
    }
    result.total_after = _observe_rng();
    return result;
}

string textdb_phase0::expand_loaded_canonical_english_speakdb(
    const string &key)
{
    return expand_loaded_canonical_english_speakdb_traced(key).text;
}

textdb_phase0::expanded_selection
textdb_phase0::expand_loaded_canonical_english_speakdb_traced(
    const string &key)
{
    const auto lookup =
        [](const string &lookup_key, const string &suffix,
           selection_trace *trace, const vector<size_t> &path,
           int depth, int replacements)
        {
            return _getWeightedSelection(SpeakDB, lookup_key, suffix, true,
                                         trace, path, depth, replacements);
        };
    int num_replacements = 0;
    const vector<size_t> path;
    expanded_selection result;
    recursive_site_status top_status = recursive_site_status::MISSING;
    bool recursive_corrupt = false;
    result.text = _getRandomisedStr(
        lookup, key, "", num_replacements, 0, path, &result.trace,
        &top_status, &recursive_corrupt);
    switch (top_status)
    {
    case recursive_site_status::SELECTED:
        result.status = raw_selection_status::SELECTED;
        break;
    case recursive_site_status::MISSING:
        result.status = raw_selection_status::MISSING;
        break;
    case recursive_site_status::CORRUPT:
    case recursive_site_status::UNBALANCED:
    case recursive_site_status::DEPTH_LIMIT:
    case recursive_site_status::REPLACEMENT_LIMIT:
        result.status = raw_selection_status::CORRUPT;
        break;
    }
    const bool lua_corrupt = _execute_embedded_lua(result.text, &result.trace);
    if (recursive_corrupt || lua_corrupt)
        result.status = raw_selection_status::CORRUPT;
    result.trace.final_replacement_count = num_replacements;
    return result;
}

static string _query_database(TextDB &db, string key, bool canonicalise_key,
                              bool run_lua, bool untranslated)
{
    if (canonicalise_key)
    {
        // We have to canonicalise the key (in case the user typed it
        // in and got the case wrong.)
        lowercase(key);
    }

    // Query the DB.
    datum result;

    if (db.translation && !untranslated)
        result = _database_fetch(db.translation->get(), key);
    if (!_database_has_entry(result))
        result = _database_fetch(db.get(), key);

    if (!_database_has_entry(result))
        return "";

    string str((const char *)result.dptr, result.dsize);
    if (str.empty())
        return "";

    // <foo> is an alias to key foo
    if (str[0] == '<' && str[str.size() - 2] == '>'
        && str.find('<', 1) == str.npos
        && str.find('\n') == str.size() - 1)
    {
        return _query_database(db, str.substr(1, str.size() - 3),
                               canonicalise_key, run_lua, untranslated);
    }

    _substitute_descriptions(db, str, canonicalise_key, run_lua, untranslated);

    if (run_lua)
        _execute_embedded_lua(str);

    return str;
}

/////////////////////////////////////////////////////////////////////////////
// Quote DB specific functions.

string getQuoteString(const string &key)
{
    return unwrap_desc(_query_database(QuotesDB, key, true, true));
}

/////////////////////////////////////////////////////////////////////////////
// Description DB specific functions.

string getLongDescription(const string &key)
{
    return unwrap_desc(_query_database(DescriptionDB, key, true, true));
}

vector<string> getLongDescKeysByRegex(const string &regex,
                                      db_find_filter filter)
{
    if (!DescriptionDB.get())
    {
        vector<string> empty;
        return empty;
    }

    // FIXME: need to match regex against translated keys, which can't
    // be done by db only.
    return _database_find_keys(DescriptionDB.get(), regex, true, filter);
}

vector<string> getLongDescBodiesByRegex(const string &regex,
                                        db_find_filter filter)
{
    if (!DescriptionDB.get())
    {
        vector<string> empty;
        return empty;
    }

    // On partial translations, this will match only translated descriptions.
    // Not good, but otherwise we'd have to check hundreds of keys, with
    // two queries for each.
    // SQL can do this in one go, DBM can't.
    DBM *database = DescriptionDB.translation ?
        DescriptionDB.translation->get() : DescriptionDB.get();
    return _database_find_bodies(database, regex, true, filter);
}

/////////////////////////////////////////////////////////////////////////////
// GameStart DB specific functions.
string getGameStartDescription(const string &key)
{
    return _query_database(GameStartDB, key, true, true);
}

/////////////////////////////////////////////////////////////////////////////
// Shout DB specific functions.
string getShoutString(const string &monst, const string &suffix)
{
    int num_replacements = 0;

    return _getRandomisedStr(ShoutDB, monst, suffix, num_replacements);
}

/////////////////////////////////////////////////////////////////////////////
// Speak DB specific functions.
string getSpeakString(const string &key)
{
    int num_replacements = 0;

#ifdef DEBUG_MONSPEAK
    dprf(DIAG_SPEECH, "monster speech lookup for %s", key.c_str());
#endif
    string txt = _getRandomisedStr(SpeakDB, key, "", num_replacements);
    _execute_embedded_lua(txt);

    return txt;
}

string getRandMonNameString(const string &montype)
{
    int num_replacements = 0;

    return _getRandomisedStr(SpeakDB, montype, " name", num_replacements);
}

/////////////////////////////////////////////////////////////////////////////
// Randname DB specific functions.
string getRandNameString(const string &itemtype, const string &suffix)
{
    int num_replacements = 0;

    return _getRandomisedStr(RandartDB, itemtype, suffix, num_replacements);
}

/////////////////////////////////////////////////////////////////////////////
// Help DB specific functions.

string getHelpString(const string &topic)
{
    string help = _query_database(HelpDB, topic, false, true);
    if (help.empty())
        help = make_stringf(T_("Error! The help for \"%s\" is missing!"), topic.c_str());
    return help;
}

/////////////////////////////////////////////////////////////////////////////
// FAQ DB specific functions.
vector<string> getAllFAQKeys()
{
    if (!FAQDB.get())
    {
        vector<string> empty;
        return empty;
    }

    return _database_find_keys(FAQDB.get(), "^q.+", false);
}

string getFAQ_Question(const string &key)
{
    return _query_database(FAQDB, key, false, true);
}

string getFAQ_Answer(const string &question)
{
    string key = "a" + question.substr(1, question.length()-1);
    string val = unwrap_desc(_query_database(FAQDB, key, false, true));

    // Remove blank lines between items on a bulleted list, for small
    // terminals' sake. Far easier to store them as separated paragraphs
    // in the source.
    // Also, use a nicer bullet as we're already here.
    val = replace_all(val, "\n\n*", "\n•");

    return val;
}

/////////////////////////////////////////////////////////////////////////////
// Miscellaneous DB specific functions.

string getMiscString(const string &misc, const string &suffix)

{
    int num_replacements = 0;

    string txt = _getRandomisedStr(MiscDB, misc, suffix, num_replacements);
    _execute_embedded_lua(txt);

    return txt;
}

/////////////////////////////////////////////////////////////////////////////
// Hints DB specific functions.

string getHintString(const string &key)
{
    return unwrap_desc(_query_database(HintsDB, key, true, true));
}

/////////////////////////////////////////////////////////////////////////////
// Egos DB specific functions.

string getEgoString(const string &key)
{
    return unwrap_desc(_query_database(EgosDB, key, true, true));
}

// i18n_escape_key(): normalize C++ runtime strings to source.txt key format.
//
// C++ string literals like "text\n" compile escape sequences to control chars:
//   \n → 0x0A   \r → 0x0D   \t → 0x09
// source.txt stores keys as single lines with literal backslash-escapes.
// This function converts actual control chars back to their escape notation
// so lookup keys match source.txt storage format.
//
// \\ (backslash) MUST be escaped first: it is the escape introducer in
// source.txt. Without it, "path\name" (literal backslash) and
// "path<0x0A>ame" would both normalize to "path\name" — a collision.
// With \\ → \\\\ first, they become "path\\name" and "path\name".
//
// \" (quote) is NOT escaped: source.txt keys are bare lines without
// outer quote delimiters, so " is a regular character.
//
// Extraction scripts MUST use identical logic when writing keys to source.txt.
static string i18n_escape_key(const string &raw)
{
    string s = raw;
    s = replace_all(s, "\\", "\\\\");  // 1st: backslash first — escape introducer
    s = replace_all(s, "\r", "\\r");
    s = replace_all(s, "\n", "\\n");
    s = replace_all(s, "\t", "\\t");
    return s;
}

// i18n_unescape_value(): convert source.txt escape notation back to runtime chars.
//
// Mirrors i18n_escape_key() in reverse. Uses single-pass left-to-right scan
// (NOT sequential replace_all) because the same ambiguity that cpp_unescape
// faces in Python exists here: "\\n" could mean backslash+n (\\ + n) or
// backslash+newline (\ + \n). Only a single-pass scanner can disambiguate.
//
// Unknown escapes (e.g. \% ) keep the character after backslash as-is.
static string i18n_unescape_value(const string &s)
{
    string out;
    out.reserve(s.size());
    for (size_t i = 0; i < s.size(); )
    {
        if (s[i] == '\\' && i + 1 < s.size())
        {
            switch (s[i + 1])
            {
            case '\\': out += '\\'; break;
            case 'n':  out += '\n'; break;
            case 'r':  out += '\r'; break;
            case 't':  out += '\t'; break;
            default:   out += s[i + 1]; break; // unknown: keep char
            }
            i += 2;
        }
        else
            out += s[i++];
    }
    return out;
}

// i18n_source_lookup(): T_()/C_() backend — i18n lookup for C++ source strings.
// Queries the 12th TextDB instance (SourceDB) in dat/i18n/<lang>/source.txt.
// When ctx is non-null, uses composite key "ctx|en" for context disambiguation.
// Falls back to "en" (without context), then to the English key itself.
//
// String lifetime: deque guarantees push_back never invalidates references
// to existing elements. However, i18n_cache_clear() destroys every stored
// string. Returned const char* values are borrowed until the next cache clear;
// callers that retain a value must copy it into an owning string.

static map<string, const char*> i18n_index;
static deque<string> i18n_storage;

void i18n_cache_clear()
{
    i18n_index.clear();
    i18n_storage.clear();
}

const char* i18n_source_lookup(const char* ctx, const char* en)
{
    if (Options.language == lang_t::EN || !en || !en[0])
        return en;

    string lookup_key = (ctx && ctx[0])
        ? make_stringf("%s|%s", ctx, en)
        : string(en);
    lookup_key = i18n_escape_key(lookup_key);
    string en_key = i18n_escape_key(en);

    auto it = i18n_index.find(lookup_key);
    if (it != i18n_index.end())
        return it->second;    // pointer into deque — guaranteed stable

    // Try context-qualified key first (if applicable)
    string zh;
    bool have_translation = false;
    if (SourceDB.translation)
    {
        auto fetch_translation = [&](const string &key)
        {
            string canon_key = key;
            lowercase(canon_key);
            datum result = _database_fetch(SourceDB.translation->get(), canon_key);
            if (!_database_has_entry(result))
                return false;
            zh.assign((const char *)result.dptr, result.dsize);
            return !zh.empty();
        };

        if (ctx && ctx[0])
            have_translation = fetch_translation(lookup_key);

        // Fall back to unqualified key only when the qualified key is missing,
        // not when it is explicitly present with an empty translation.
        if (!have_translation)
            have_translation = fetch_translation(en_key);
    }

    // Final fallback: return English original.
    // Only DB-retrieved values go through unescape (source.txt values use
    // escape notation like \n for newlines). The EN fallback string is
    // already a C++ runtime value with actual control characters.
    // _parse_text_db appends \n (0x0A) to every stored value — strip only
    // that trailing artifact. Do NOT strip leading/trailing spaces: they
    // are semantically significant for fragment concatenation in message
    // assembly (e.g. T_(" wielding ") returns " 挥舞着 " with spaces).
    if (have_translation)
    {
        while (!zh.empty() && (zh.back() == '\n' || zh.back() == '\r'))
            zh.pop_back();
        zh = i18n_unescape_value(zh);
    }
    else
        zh = en;

    // Store for this cache generation. deque::push_back never invalidates
    // references to existing elements, but i18n_cache_clear() invalidates all
    // returned pointers. Do not persist this borrowed pointer across a clear.
    i18n_storage.push_back(zh);
    const char* ptr = i18n_storage.back().c_str();
    i18n_index[lookup_key] = ptr;
    return ptr;
}

// T_() — inline in i18n.h calls i18n_source_lookup(nullptr, en)
// C_() — inline in i18n.h calls i18n_source_lookup(ctx, en)
