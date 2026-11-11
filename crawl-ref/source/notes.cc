/**
 * @file
 * @brief Notetaking stuff
**/

#include "AppHdr.h"
#include "god-wrath.h"

#include "database.h"
#include "notes.h"

#include <cstring>
#include <iomanip>
#include <sstream>
#include <vector>

#include "branch.h"
#include "english.h"
#include "hiscores.h"
#include "libutil.h"
#include "item-name.h"
#include "potion-type.h"
#include "item-prop.h" // gem_adj
#include "message.h"
#include "mutation.h"
#include "mon-util.h"
#include "lang-en-guard.h"
#include "options.h"
#include "positional_format.h"
#include "religion.h"
#include "skills.h"
#include "spl-util.h"
#include "state.h"
#include "stringutil.h"
#include "tag-version.h"
#include "unicode.h"
#include "view.h"

#define NOTES_VERSION_NUMBER 1002

vector<Note> note_list;
int last_screen_turn = -1;

bool is_highest_skill(int skill)
{
    for (int i = 0; i < NUM_SKILLS; ++i)
    {
        if (i == skill)
            continue;
        if (you.skills[i] >= you.skills[skill])
            return false;
    }
    return true;
}

bool is_noteworthy_hp(int hp, int maxhp)
{
    return hp > 0 && Options.note_hp_percent
           && hp <= (maxhp * Options.note_hp_percent) / 100;
}

static int _dungeon_branch_depth(uint8_t branch)
{
    if (branch >= NUM_BRANCHES)
        return -1;
    return brdepth[branch];
}

static bool _is_noteworthy_dlevel(level_id place)
{
    branch_type branch = place.branch;
    int lev = place.depth;

    // Entering the Abyss is noted a different way, since we care mostly about
    // the cause.
    if (branch == BRANCH_ABYSS)
        return lev == _dungeon_branch_depth(branch);

    // These get their note in the .des files.
    if (branch == BRANCH_WIZLAB || branch == BRANCH_TROVE)
        return false;

    // Other portal levels are always interesting.
    if (!is_connected_branch(branch))
        return true;

    return lev == _dungeon_branch_depth(branch)
           || branch == BRANCH_DUNGEON && (lev % 5) == 0
           || branch != BRANCH_DUNGEON && lev == 1;
}

// Is a note worth taking?
// This function assumes that game state has not changed since
// the note was taken, e.g. you.* is valid.
static bool _is_noteworthy(const Note& note)
{
    // Always noteworthy.
    if (note.type == NOTE_XP_LEVEL_CHANGE
        || note.type == NOTE_LEARN_SPELL
        || note.type == NOTE_GET_GOD
        || note.type == NOTE_GOD_GIFT
        || note.type == NOTE_GET_MUTATION
        || note.type == NOTE_LOSE_MUTATION
        || note.type == NOTE_PERM_MUTATION
        || note.type == NOTE_GET_ITEM
        || note.type == NOTE_ID_ITEM
        || note.type == NOTE_ACQUIRE_ITEM
        || note.type == NOTE_BUY_ITEM
        || note.type == NOTE_DONATE_MONEY
        || note.type == NOTE_SEEN_MONSTER
        || note.type == NOTE_DEFEAT_MONSTER
        || note.type == NOTE_POLY_MONSTER
        || note.type == NOTE_USER_NOTE
        || note.type == NOTE_MESSAGE
        || note.type == NOTE_LOSE_GOD
        || note.type == NOTE_PENANCE
        || note.type == NOTE_MOLLIFY_GOD
        || note.type == NOTE_DEATH
        || note.type == NOTE_XOM_REVIVAL
        || note.type == NOTE_SEEN_FEAT
        || note.type == NOTE_PARALYSIS
        || note.type == NOTE_VEXED
        || note.type == NOTE_RECRUITED_APOSTLE
        || note.type == NOTE_ALLY_DEATH
        || note.type == NOTE_FEAT_MIMIC
        || note.type == NOTE_OFFERED_SPELL
        || note.type == NOTE_ANCESTOR_TYPE
        || note.type == NOTE_FOUND_UNRAND
        || note.type == NOTE_ZOT_TOUCHED
        || note.type == NOTE_DREAMSHARD
        || note.type == NOTE_GEM_LOST
        || note.type == NOTE_GAIN_LIFE
        || note.type == NOTE_LOSE_LIFE
        || note.type == NOTE_FLED_CHALLENGE
        || note.type == NOTE_INFERNAL_MARK
        || note.type == NOTE_GET_BANE
        || note.type == NOTE_LOSE_BANE
        || note.type == NOTE_TESSERACT_ACTIVATED)
    {
        return true;
    }

    // Never noteworthy, hooked up for fun or future use.
    if (note.type == NOTE_MP_CHANGE
        || note.type == NOTE_MAXHP_CHANGE
        || note.type == NOTE_MAXMP_CHANGE)
    {
        return false;
    }

    // Xom effects are only noteworthy if the option is true.
    if (note.type == NOTE_XOM_EFFECT)
        return Options.note_xom_effects;

    // HP noteworthiness is handled in its own function.
    if (note.type == NOTE_HP_CHANGE
        && !is_noteworthy_hp(note.first, note.second))
    {
        return false;
    }

    // Skills are always noteworthy in order to construct the skill_gains table
    // in the chardump. The options to control display are used in
    // Note::hidden().
    if (note.type == NOTE_GAIN_SKILL || note.type == NOTE_LOSE_SKILL
        || note.type == NOTE_START_SKILL)
    {
        return true;
    }

    if (note.type == NOTE_DUNGEON_LEVEL_CHANGE)
        return _is_noteworthy_dlevel(note.place);

    for (const Note &oldnote : note_list)
    {
        if (oldnote.type != note.type)
            continue;

        const Note& rnote(oldnote);
        switch (note.type)
        {
        case NOTE_PIETY_RANK:
            if (rnote.first == note.first && rnote.second == note.second)
                return false;
            break;

        case NOTE_HP_CHANGE:
            // Not if we have a recent warning
            // unless we've lost half our HP since then.
            if (note.turn - rnote.turn < 5
                && note.first * 2 >= rnote.first)
            {
                return false;
            }
            break;

        default:
            mpr(T_("Buggy note passed: unknown note type"));
            // Return now, rather than give a "Buggy note passed" message
            // for each note of the matching type in the note list.
            return true;
        }
    }
    return true;
}

// These are existing canonical Xom note shapes, not a new persistence format.
// Parse only complete, known events. Malformed or unknown historical entries
// remain verbatim, and rendering never rewrites Note::name/desc.
static bool _xom_note_count(const string& text, int& value)
{
    return parse_int(text.c_str(), value) && value >= 0
           && text == make_stringf("%d", value);
}

static string _xom_note_monster_display(const string& name)
{
    return name == "something unseen" ? T_("something unseen")
                                      : death_source_display_name(name);
}

static string _xom_effect_note_display(const string& name)
{
    if (Options.language != lang_t::ZH)
        return name;
    if (name == "drained mp")
        return T_("drained mp");
    if (name == "drained mp, created monsters")
        return T_("drained mp, created monsters");
    if (name == NC_("Xom effect note", "draining")
        || name == NC_("Xom effect note", "reaching")
        || name == NC_("Xom effect note", "duel")
        || name == NC_("Xom effect note", "sneaky"))
    {
        return C_("Xom effect note", name.c_str());
    }
    const char* mutation_notes[] =
    {
        N_("give mutation"), N_("give mutations"),
        N_("give good mutation"), N_("give good mutations"),
        N_("give random mutation"), N_("give random mutations"),
        N_("made a garden"), N_("spooky wave of despair"),
        N_("divination: all"),
        N_("banished to a bazaar"),
        N_("confuse monster(s)"),
        N_("swap monsters"),
        N_("snakes to sticks"),
        N_("fake shatter"),
        N_("scenery: changed the scenery"),
        N_("scenery: summon butterflies"),
        N_("destruction"),
        N_("fake destruction"),
        N_("hasted everything in sight"),
        N_("hasted player and everything else in sight"),
        N_("slowed everything in sight"),
        N_("slowed player and everything else"),
        N_("paralysed everything in sight"),
        N_("paralysed player and everything else"),
        N_("fog"),
        N_("silly message"),
        N_("chaos upgrade"),
        N_("confusion"),
        N_("confusion (+ monsters)"),
        N_("confusion (+ might)"),
        N_("confusion (+ monsters) (+ might)"),
        N_("repel stairs"),
        N_("cloud trail"),
        N_("inflicting Doom"),
        N_("revert banishment"),
        N_("noise"),
        N_("blink monster(s)"),
        N_("made traps"),
        N_("chaos reinforcements"),
        N_("chaos cloud"),
        N_("floor lock"),
        N_("minibane"),
        N_("blessing of mannequins"),
        N_("blessing of battleshape"),
        N_("blessing of protean form"),
        N_("butterfly on damage"),
        N_("smoke on damage"),
    };
    for (const char* key : mutation_notes)
        if (name == key)
            return T_(key);

    const struct
    {
        const char* prefix;
        const char* suffix;
        const char* format;
    } count_notes[] =
    {
        { "warped sight and space for ", " monster", N_("warped sight and space for %d monster") },
        { "warped sight and space for ", " monsters", N_("warped sight and space for %d monsters") },
        { "chaos laced + vexed ", " monster", N_("chaos laced + vexed %d monster") },
        { "chaos laced + vexed ", " monsters", N_("chaos laced + vexed %d monsters") },
        { "divine lightning + ", " bolts", N_("divine lightning + %d bolts") },
        { "lit up ", " webs", N_("lit up %d webs") },
        { "summons ", " friend", N_("summons %d friend") },
        { "summons ", " friends", N_("summons %d friends") },
        { "", "-stop teleportation journey", N_("%d-stop teleportation journey") },
        { "", "-stop teleportation journey (dangerous)", N_("%d-stop teleportation journey (dangerous)") },
        { "charmed ", " monster", N_("charmed %d monster") },
        { "charmed ", " monsters", N_("charmed %d monsters") },
        { "summons ", " living force lance", N_("summons %d living force lance") },
        { "summons ", " living force lances", N_("summons %d living force lances") },
        { "summons ", " hostile shadow creature", N_("summons %d hostile shadow creature") },
        { "summons ", " hostile shadow creatures", N_("summons %d hostile shadow creatures") },
        { "summons ", " hostile chaos creature", N_("summons %d hostile chaos creature") },
        { "summons ", " hostile chaos creatures", N_("summons %d hostile chaos creatures") },
        { "made a ring of doors, pushed ", " other out", N_("made a ring of doors, pushed %d other out") },
        { "made a ring of doors, pushed ", " others out", N_("made a ring of doors, pushed %d others out") },
        { "made a ring of doors, pulled ", " other in", N_("made a ring of doors, pulled %d other in") },
        { "made a ring of doors, pulled ", " others in", N_("made a ring of doors, pulled %d others in") },
    };
    for (const auto& event : count_notes)
    {
        const size_t prefix = strlen(event.prefix), suffix = strlen(event.suffix);
        if (!starts_with(name, event.prefix) || !ends_with(name, event.suffix)
            || name.size() <= prefix + suffix)
        {
            continue;
        }
        int count;
        if (_xom_note_count(name.substr(prefix, name.size() - prefix - suffix), count))
        {
            if ((starts_with(name, "warped sight and space for ")
                 || starts_with(name, "chaos laced + vexed "))
                && string(event.suffix) != (count > 1 ? " monsters" : " monster"))
            {
                return name;
            }
            return make_stringf(T_(event.format), count);
        }
    }

    for (const char* key : { N_("cast spell '%s'"),
                            N_("blessing of eisegesis (%s)"),
                            N_("blessing of spellstride (%s)") })
    {
        const string format = key;
        const size_t slot = format.find("%s");
        const string prefix = format.substr(0, slot);
        const string suffix = format.substr(slot + 2);
        if (!starts_with(name, prefix) || !ends_with(name, suffix)
            || name.size() <= prefix.size() + suffix.size())
        {
            continue;
        }
        const string title = name.substr(prefix.size(),
            name.size() - prefix.size() - suffix.size());
        spell_type spell;
        {
            const ScopedLangEn english;
            spell = spell_by_name(title, false);
            if (spell != SPELL_NO_SPELL && title != spell_title(spell))
                spell = SPELL_NO_SPELL;
        }
        if (spell == SPELL_NO_SPELL)
        {
            for (int i = 0; i < NUM_SPELLS; ++i)
                if (is_valid_spell(static_cast<spell_type>(i))
                    && title == spell_title(static_cast<spell_type>(i)))
                {
                    spell = static_cast<spell_type>(i);
                    break;
                }
        }
        if (spell == SPELL_NO_SPELL)
            return name;
        return make_stringf(T_(key), spell_title(spell));
    }
    if (starts_with(name, "blessing of cleaving (") && ends_with(name, ")"))
    {
        const string title = name.substr(22, name.size() - 23);
        if (title.empty())
            return name;
        for (int i = SPWPN_NORMAL; i < NUM_REAL_SPECIAL_WEAPONS; ++i)
        {
            const brand_type brand = static_cast<brand_type>(i);
            if (title == brand_type_name_en(brand, false)
                || title == brand_type_name(brand, false))
            {
                return make_stringf(T_("blessing of cleaving (%s)"),
                                    brand_type_name(brand, false));
            }
        }
        return name;
    }
    if (starts_with(name, "blessing of guardians: "))
    {
        const size_t start = strlen("blessing of guardians: ");
        const size_t split = name.find(' ', start);
        int count;
        if (split == string::npos
            || !_xom_note_count(name.substr(start, split - start), count))
        {
            return name;
        }
        const string title = name.substr(split + 1);
        // This producer stores the monster type, never its generated name.
        for (int i = 0; i < NUM_MONSTERS; ++i)
        {
            const monster_type type = static_cast<monster_type>(i);
            if (invalid_monster_type(type))
                continue;
            string canonical;
            { const ScopedLangEn english; canonical = mons_type_name(type, DESC_PLAIN); }
            const string display = mons_type_name(type, DESC_PLAIN);
            if (title == canonical || title == display)
            {
                return make_stringf(T_("blessing of guardians: %d %s"),
                                    count, display.c_str());
            }
        }
        return name;
    }
    if (starts_with(name, "knowledge: "))
    {
        const string body = name.substr(11);
        // Reconstruct both producer languages exactly, rejecting stray
        // separators, unknown skills and malformed historical strings.
        for (bool english : { true, false })
        {
            vector<string> original, translated;
            string separator = T_(" and ");
            if (english)
                separator = " and ";
            const vector<string> parts = split_string(", ",
                replace_all(body, separator, ", "));
            for (const string& part : parts)
            {
                bool found = false;
                for (skill_type sk = SK_FIRST_SKILL; sk < NUM_SKILLS; ++sk)
                {
                    string canonical;
                    if (english)
                    { const ScopedLangEn en; canonical = skill_name(sk); }
                    else
                        canonical = skill_name(sk);
                    if (part == canonical)
                    {
                        original.push_back(canonical);
                        translated.push_back(skill_name(sk));
                        found = true;
                        break;
                    }
                }
                if (!found)
                    break;
            }
            if (!parts.empty() && original.size() == parts.size()
                && body == comma_separated_line(original.begin(), original.end(), separator, ", "))
            {
                const string display = comma_separated_line(
                    translated.begin(), translated.end(), T_(","), T_(","));
                return make_stringf(T_("knowledge: %s"), display.c_str());
            }
        }
        return name;
    }
    if (starts_with(name, "potion effect (") && ends_with(name, ")"))
    {
        const string prefix = "potion effect (";
        const string title = name.substr(prefix.size(), name.size() - prefix.size() - 1);
        for (const potion_type potion : potion_types)
        {
            string canonical;
            {
                const ScopedLangEn english;
                canonical = potion_type_name(potion);
            }
            if (title == canonical)
                return make_stringf(T_("potion effect (%s)"), potion_type_name(potion));
        }
        return name;
    }
    if (starts_with(name, "god gift: "))
    {
        const string item = name.substr(10);
        const string display = T_(item.c_str());
        const string format = T_("god gift: %s");
        // Full arbitrary item names cannot be safely reconstructed from text.
        // Only an exact catalog hit is supported; otherwise keep the full note.
        if (item.empty() || display == item || format == "god gift: %s")
            return name;
        return make_stringf(format.c_str(), display.c_str());
    }
    if (starts_with(name, "summons friendly "))
    {
        if (name.size() == 17)
            return name;
        const string monster = _xom_note_monster_display(name.substr(17));
        return make_stringf(T_("summons friendly %s"), monster.c_str());
    }

    if (starts_with(name, "made a ring of doors, pulled ") && ends_with(name, " out"))
    {
        const string prefix = "made a ring of doors, pulled ";
        const string separator = " in and pushed ";
        const size_t split = name.find(separator, prefix.size());
        int pulled, pushed;
        if (split != string::npos
            && _xom_note_count(name.substr(prefix.size(), split - prefix.size()), pulled)
            && _xom_note_count(name.substr(split + separator.size(),
                name.size() - split - separator.size() - 4), pushed))
        {
            return make_stringf(T_("made a ring of doors, pulled %d in and pushed %d out"),
                                pulled, pushed);
        }
        return name;
    }

    if (starts_with(name, "buffed friendly "))
    {
        const string suffix = ends_with(name, " times") ? " times" : " time";
        if (!ends_with(name, suffix))
            return name;
        const string body = name.substr(16, name.size() - 16 - suffix.size());
        const size_t space = body.rfind(' ');
        int count;
        if (space == string::npos || space == 0
            || !_xom_note_count(body.substr(space + 1), count))
        {
            return name;
        }
        const string monster = _xom_note_monster_display(body.substr(0, space));
        return make_stringf(T_("buffed friendly %s %d times"), monster.c_str(), count);
    }

    if (starts_with(name, "made ") && ends_with(name, " speak a word of recall"))
    {
        const string suffix = " speak a word of recall";
        if (name.size() <= 5 + suffix.size())
            return name;
        const string monster = _xom_note_monster_display(
            name.substr(5, name.size() - 5 - suffix.size()));
        return make_stringf(T_("made %s speak a word of recall"), monster.c_str());
    }

    if (starts_with(name, "good polymorph ") || starts_with(name, "bad polymorph "))
    {
        const bool good = starts_with(name, "good ");
        const size_t start = good ? 15 : 14;
        const size_t arrow = name.find(" -> ", start);
        if (arrow == string::npos || arrow == start || arrow + 4 == name.size())
            return name;
        const string before = _xom_note_monster_display(name.substr(start, arrow - start));
        string after_name = name.substr(arrow + 4);
        string debug;
        for (const char* suffix : { N_(" (upgrade)"), N_(" (downgrade)") })
        {
            if (ends_with(after_name, suffix))
            {
                after_name.resize(after_name.size() - strlen(suffix));
                debug = T_(suffix);
                break;
            }
        }
        if (after_name.empty())
            return name;
        const string after = _xom_note_monster_display(after_name);
        return make_stringf(T_("%s polymorph %s -> %s"), good ? T_("good") : T_("bad"),
                            before.c_str(), after.c_str()) + debug;
    }

    for (const char* key : { N_("enchant monster (%s, %s)"),
                            N_("enchant monsters (%s, %s)") })
    {
        const string format = key;
        const string prefix = format.substr(0, format.find('%'));
        if (!starts_with(name, prefix) || !ends_with(name, ")"))
            continue;
        const size_t comma = name.find(", ", prefix.size());
        if (comma == string::npos)
            return name;
        const string polarity = name.substr(prefix.size(), comma - prefix.size());
        if (polarity != "good" && polarity != "bad")
            return name;
        const string effect = name.substr(comma + 2, name.size() - comma - 3);
        if (effect.empty())
            return name;
        return make_stringf(T_(key), polarity == "good" ? T_("good") : T_("bad"),
                            C_("flag long", effect.c_str()));
    }

    static const char* const torment_notes[] =
    {
        N_("torment all (player (%d/%d hp)"),
        N_("torment player (%d/%d hp)"),
        N_("torment all (%d/%d hp)"),
        N_("torment (%d/%d hp)"),
    };
    for (const char* key : torment_notes)
    {
        const string format = key;
        const string prefix = format.substr(0, format.find('%'));
        if (!starts_with(name, prefix) || !ends_with(name, " hp)"))
            continue;
        const size_t slash = name.find('/', prefix.size());
        if (slash == string::npos)
            return name;
        int hp, max_hp;
        if (!_xom_note_count(name.substr(prefix.size(), slash - prefix.size()), hp)
            || !_xom_note_count(name.substr(slash + 1, name.size() - slash - 5), max_hp))
        {
            return name;
        }
        return make_stringf(T_(key), hp, max_hp);
    }

    if (starts_with(name, "summoned "))
    {
        istringstream input(name.substr(9));
        int hostile, friendly;
        string word1, kind1, plus, word2, kind2, extra;
        if (input >> hostile >> word1 >> kind1 >> plus >> friendly >> word2 >> kind2
            && !(input >> extra) && hostile >= 0 && friendly >= 0
            && word1 == "hostile" && plus == "+" && word2 == "friendly"
            && kind1 == (hostile == 1 ? "illusion" : "illusions")
            && kind2 == (friendly == 1 ? "illusion" : "illusions")
            && name == make_stringf("summoned %d hostile %s + %d friendly %s",
                                   hostile, kind1.c_str(), friendly, kind2.c_str()))
        {
            return make_stringf(T_("summoned %d hostile illusions + %d friendly illusions"),
                                hostile, friendly);
        }
    }

    if (starts_with(name, "scenery: "))
    {
        const struct { const char* suffix; const char* format; } events[] =
        {
            { " fountains blood", N_("%d fountains blood") },
            { " snacks swapped", N_("%d snacks swapped") },
            { " trees warped", N_("%d trees warped") },
            { " doors open", N_("%d doors open") },
            { " doors close", N_("%d doors close") },
        };
        vector<string> translated;
        for (const string& part : split_string(", ", name.substr(9)))
        {
            bool known = false;
            for (const auto& event : events)
            {
                const size_t suffix = strlen(event.suffix);
                int count;
                if (ends_with(part, event.suffix) && part.size() > suffix
                    && _xom_note_count(part.substr(0, part.size() - suffix), count))
                {
                    translated.push_back(make_stringf(T_(event.format), count));
                    known = true;
                    break;
                }
            }
            if (!known)
                return name;
        }
        if (!translated.empty())
        {
            return string(T_("scenery: ")) + join_strings(
                translated.begin(), translated.end(), C_("Xom scenery list", ", "));
        }
    }
    return name;
}

// Abyss entry notes are persisted as canonical English. Recognize only the
// exact producer format and known distortion causes. The caller also requires
// the producer's existing desc-field marker, so language-locked crawl.take_note
// snapshots and historical NOTE_MESSAGE records stay untouched.
static string _abyss_entry_note_display(const string& text)
{
    if (Options.language != lang_t::ZH)
        return text;

    const string prefix = "Cast into level ";
    const string suffix = " of the Abyss";
    if (!starts_with(text, prefix))
        return text;
    const size_t end_level = text.find(suffix, prefix.size());
    if (end_level == string::npos)
        return text;
    const string digits = text.substr(prefix.size(), end_level - prefix.size());
    // Canonical depth is a positive decimal integer. Bound parsing before
    // arithmetic so malformed/historical notes fail back without data loss.
    if (digits.empty() || digits.size() > 3 || digits[0] == '0'
        || digits.find_first_not_of("0123456789") != string::npos)
    {
        return text;
    }
    int depth = 0;
    for (const char digit : digits)
        depth = depth * 10 + digit - '0';

    const string tail = text.substr(end_level + suffix.size());
    if (tail.empty())
        return make_stringf(T_("Cast into level %d of the Abyss"), depth);
    if (tail != " (rebranding a weapon of distortion)"
        && tail != " (unwielding a weapon of distortion)")
    {
        return text;
    }

    const char* cause_key = tail == " (rebranding a weapon of distortion)"
        ? N_("rebranding a weapon of distortion")
        : N_("unwielding a weapon of distortion");
    const string cause = T_(cause_key);
    const string format = T_("Cast into level %d of the Abyss (%s)");
    // Do not form a mixed-language note if an asset is missing.
    if (cause.empty() || cause == cause_key
        || format == "Cast into level %d of the Abyss (%s)")
    {
        return text;
    }
    return make_stringf(format.c_str(), depth, cause.c_str());
}

// This producer already stores the actual affected level in Note::place.
// Validate its complete English name before using that typed display accessor;
// historical and Lua snapshots without this marker remain language-locked.
static string _corrupted_level_note_display(const Note& note)
{
    if (Options.language != lang_t::ZH || note.desc != "corrupted level"
        || note.place.branch < 0 || !note.place.is_valid())
    {
        return note.name;
    }
    string canonical;
    {
        ScopedLangEn canonical_language;
        canonical = make_stringf("Corrupted %s", note.place.describe().c_str());
    }
    if (note.name != canonical)
        return note.name;
    const string format = T_("Corrupted %s");
    if (format == "Corrupted %s")
        return note.name;
    return make_stringf(format.c_str(), note.place.describe(true, true).c_str());
}

// Only the two C++ theft producers mark these canonical NOTE_MESSAGE records.
// Legacy and crawl.take_note snapshots never enter this display conversion.
static string _theft_note_display(const Note& note)
{
    if (Options.language != lang_t::ZH)
        return note.name;
    string thief, item;
    if (note.desc == "gold theft" && note.first > 0)
    {
        const string suffix = make_stringf(" stole %d gold", note.first);
        if (!ends_with(note.name, suffix) || note.name.size() <= suffix.size())
            return note.name;
        thief = note.name.substr(0, note.name.size() - suffix.size());
    }
    else if (note.desc == "item theft")
    {
        const string separator = " stole ";
        const size_t split = note.name.find(separator);
        if (split == string::npos || split == 0 || split + separator.size() >= note.name.size())
            return note.name;
        thief = note.name.substr(0, split);
        const string canonical_item = note.name.substr(split + separator.size());
        item = T_(canonical_item.c_str());
        // Arbitrary saved full item names have no reversible item accessor.
        // An exact existing catalog hit is the only supported item conversion.
        if (item.empty() || item == canonical_item)
            return note.name;
    }
    else
        return note.name;

    string source = thief;
    if (starts_with(source, "A ") || starts_with(source, "An ") || starts_with(source, "The "))
        source[0] = tolower_safe(source[0]);
    const string display = death_source_display_name(source);
    if (display.empty() || display == source)
        return note.name;
    if (note.desc == "gold theft")
    {
        const string format = T_("%1$s stole %2$d gold");
        return format == "%1$s stole %2$d gold" ? note.name
            : make_stringf_p(format.c_str(), display.c_str(), note.first);
    }
    const string format = T_("%1$s stole %2$s");
    return format == "%1$s stole %2$s" ? note.name
        : make_stringf_p(format.c_str(), display.c_str(), item.c_str());
}

// Persisted mutation reasons remain canonical. Unknown historical causes pass
// through the existing wrath display gate, which also has a verbatim fallback.
static string _mutation_reason_display(const string& reason)
{
    if (Options.language == lang_t::ZH)
    {
        const char* reasons[] =
        {
            N_("hidden defects"), N_("hidden potential"),
            N_("hidden defects expressed"), N_("hidden potential expressed"),
            N_("breaking open a mutation catalyst"),
        };
        for (const char* key : reasons)
            if (reason == key)
                return T_(key);
    }
    return god_wrath_display_name(reason);
}

// Only these six complete C++ producer literals are recognized. In particular,
// arbitrary user notes and unrecognized historical messages are never parsed.
static string _world_message_note_display(const Note& note)
{
    if (Options.language == lang_t::ZH && note.desc.empty())
    {
        const char* messages[] =
        {
            N_("Voluntarily entered the Abyss."),
            N_("Took an exit into the Abyss."),
            N_("Escaped the Abyss"), N_("Escaped Pandemonium"),
            N_("Escaped into the Abyss"), N_("Glimpsed the power of Zot."),
        };
        for (const char* key : messages)
            if (note.name == key)
                return T_(key);
    }
    return _theft_note_display(note);
}

string Note::describe(bool when, bool where, bool what) const
{
    ostringstream result;

    if (when)
        result << setw(6) << turn << " ";

    if (where)
    {
        result << "| "
               << chop_string(place.describe(), MAX_NOTE_PLACE_LEN)
               << " | ";
    }

    if (what)
    {
        switch (type)
        {
        case NOTE_HP_CHANGE:
            // [ds] Shortened HP change note from "Had X hitpoints" to
            // accommodate the cause for the loss of hitpoints.
            result << T_("HP: ") << first << "/" << second
                   << " [" << name << "]";
            break;
        case NOTE_XOM_REVIVAL:
            result << T_("Xom revived you");
            break;
        case NOTE_MP_CHANGE:
            result << T_("Magic: ") << first << "/" << second;
            break;
        case NOTE_MAXHP_CHANGE:
            result << make_stringf(
                C_("maximum resource note", "Reached %d max health"), first);
            break;
        case NOTE_MAXMP_CHANGE:
            result << make_stringf(
                C_("maximum resource note", "Reached %d max magic points"), first);
            break;
        case NOTE_XP_LEVEL_CHANGE:
            result << T_("Reached XP level ") << first << ". " << name;
            break;
        case NOTE_DUNGEON_LEVEL_CHANGE:
            if (!desc.empty())
                result << desc;
            else
                result << T_("Entered ")
                       << place.describe(true, true);
            break;
        case NOTE_LEARN_SPELL:
            result << make_stringf(T_("Learned a level %d spell: %s"),
                spell_difficulty(static_cast<spell_type>(first)),
                spell_title(static_cast<spell_type>(first)));
            break;
        case NOTE_GET_GOD:
            result << T_("Became a worshipper of ")
                   << god_name(static_cast<god_type>(first), true);
            break;
        case NOTE_LOSE_GOD:
            result << make_stringf(T_("Fell from the grace of %s"),
                god_name(static_cast<god_type>(first)).c_str());
            break;
        case NOTE_PENANCE:
            result << make_stringf(T_("Was placed under penance by %s"),
                god_name(static_cast<god_type>(first)).c_str());
            break;
        case NOTE_MOLLIFY_GOD:
            result << make_stringf(T_("Was forgiven by %s"),
                god_name(static_cast<god_type>(first)).c_str());
            break;
        case NOTE_GOD_GIFT:
            result << make_stringf(T_("Received a gift from %s"),
                god_name(static_cast<god_type>(first)).c_str());
            if (!name.empty())
                result << " (" << name << ")";
            break;
        case NOTE_ID_ITEM:
            result << T_("Identified ") << name;
            if (!desc.empty())
                result << " (" << desc << ")";
            break;
        case NOTE_GET_ITEM:
            result << T_("Got ") << name;
            if (first != 0) // gems
            {
                const int turns = (first + 9) / 10;
                result << make_stringf(turns == 1
                    ? T_(" with %d turn to spare")
                    : T_(" with %d turns to spare"), turns);
            }
            break;
        case NOTE_ACQUIRE_ITEM:
            result << T_("Acquired ") << name;
            break;
        case NOTE_BUY_ITEM:
            result << T_("Bought ") << name << T_(" for ") << first << " "
                   << (first == 1 ? T_("gold piece") : T_("gold pieces"));
            break;
        case NOTE_DONATE_MONEY:
            result << T_("Donated ") << first << " "
                   << (first == 1 ? T_("gold piece") : T_("gold pieces"))
                   << T_(" to Zin");
            break;
        case NOTE_START_SKILL:
            result << make_stringf_p(
                C_("skill note", "Started with skill level %1$d in %2$s"),
                second, skill_name(static_cast<skill_type>(first)));
            break;
        case NOTE_GAIN_SKILL:
            result << make_stringf_p(
                C_("skill note", "Reached skill level %1$d in %2$s"),
                second, skill_name(static_cast<skill_type>(first)));
            break;
        case NOTE_LOSE_SKILL:
            result << make_stringf_p(
                C_("skill note", "Reduced skill %1$s to level %2$d"),
                skill_name(static_cast<skill_type>(first)), second);
            break;
        case NOTE_SEEN_MONSTER:
            result << T_("Encountered ") << name;
            break;
        case NOTE_DEFEAT_MONSTER:
            if (second)
            {
                result << make_stringf_p(
                    C_("monster defeat note", "%1$s (ally) was %2$s"),
                    name.c_str(), C_("monster defeat note", desc.c_str()));
            }
            else
            {
                const string verb = uppercase_first(
                    C_("monster defeat note", desc.c_str()));
                result << make_stringf_p(
                    C_("monster defeat note", "%1$s %2$s"),
                    verb.c_str(), name.c_str());
            }
            break;
        case NOTE_POLY_MONSTER:
            result << name << T_(" changed into ") << desc;
            break;
        case NOTE_PIETY_RANK:
        {
            const string rank(second, '*');
            const string god = god_name(static_cast<god_type>(first));
            result << make_stringf_p(
                C_("piety note", "Reached %1$s piety under %2$s"),
                rank.c_str(), god.c_str());
            break;
        }
        case NOTE_GET_MUTATION:
            result << T_("Gained mutation: ")
                   << mutation_desc(static_cast<mutation_type>(first),
                                    second == 0 ? 1 : second);
            if (!name.empty())
                result << " [" << _mutation_reason_display(name) << "]";
            break;
        case NOTE_LOSE_MUTATION:
            result << T_("Lost mutation: ")
                   << mutation_desc(static_cast<mutation_type>(first),
                                    second == 3 ? 3 : second+1);
            if (!name.empty())
                result << " [" << _mutation_reason_display(name) << "]";
            break;
        case NOTE_PERM_MUTATION:
            result << T_("Mutation became permanent: ")
                   << mutation_desc(static_cast<mutation_type>(first),
                                    second == 0 ? 1 : second);
            if (!name.empty())
                result << " [" << _mutation_reason_display(name) << "]";
            break;
        case NOTE_GET_BANE:
            result << T_("Gained bane: ")
                   << bane_name(static_cast<bane_type>(first));
            if (!name.empty())
            {
                const string reason = name == "Entering a Trove"
                    ? T_("Entering a Trove") : god_wrath_display_name(name);
                result << " [" << reason << "]";
            }
            break;
        case NOTE_LOSE_BANE:
            result << T_("Lost bane: ")
                   << bane_name(static_cast<bane_type>(first));
            break;
        case NOTE_DEATH:
            result << name;
            break;
        case NOTE_USER_NOTE:
            result << Options.user_note_prefix << name;
            break;
        case NOTE_MESSAGE:
            if (desc == "abyss entry")
                result << _abyss_entry_note_display(name);
            else if (desc == "corrupted level")
                result << _corrupted_level_note_display(*this);
            else if (name == "Prayed at the altar of an unknown god.")
                result << T_("Prayed at the altar of an unknown god.");
            else
                result << _world_message_note_display(*this);
            break;
        case NOTE_SEEN_FEAT:
            // The discovery producer stored a display snapshot with an ASCII
            // period. Localize only its frame; never rewrite the saved name.
            if (ends_with(name, "."))
            {
                const string feature = name.substr(0, name.size() - 1);
                result << make_stringf(C_("feature note", "Found %s."), feature.c_str());
            }
            else
                result << T_("Found ") << name;
            break;
        case NOTE_FEAT_MIMIC:
            result << name << T_(" was a mimic.");
            break;
        case NOTE_XOM_EFFECT:
        {
            const string display = _xom_effect_note_display(name);
            const bool gift_fallback = starts_with(name, "god gift: ") && display == name;
            result << (gift_fallback ? "XOM: " : T_("XOM: ")) << display;
#if defined(DEBUG_XOM) || defined(NOTE_DEBUG_XOM)
            // If debugging, also take note of severity and tension.
            result << " (severity: " << first;
            if (second >= 0)
                result << ", tension: " << second;
            result << ")";
#endif
            break;
        }
        case NOTE_PARALYSIS:
        {
            const double turns = first / 10.0;
            result << make_stringf(T_("Paralysed by %s for %.2g turns"),
                                   god_wrath_display_name(name).c_str(), turns);
        }
            break;
        case NOTE_VEXED:
            result << make_stringf(T_("Vexed by %s for %d turns"),
                                   death_source_display_name(name).c_str(), first);
            break;
        case NOTE_RECRUITED_APOSTLE:
            result << T_("Anointed ") << name << T_(" the ") << desc << T_(" as your apostle");
            break;
        case NOTE_ALLY_DEATH:
            result << T_("Your ally ") << name << T_(" died");
            break;
        case NOTE_OFFERED_SPELL:
            result << make_stringf(T_("Offered knowledge of %s by Vehumet."),
                spell_title(static_cast<spell_type>(first)));
            break;
        case NOTE_ANCESTOR_TYPE:
            result << T_("Remembered your ancestor ") << hepliaklqana_ally_name()
                   << T_(" as ") << C_("ancestor class", name.c_str());
            break;
#if TAG_MAJOR_VERSION == 34
        case NOTE_ANCESTOR_SPECIALIZATION:
            result << T_("Remembered your ancestor ") << hepliaklqana_ally_name()
                   << " " << name;
            break;
        case NOTE_ANCESTOR_DEATH:
            result << T_("Remembered your ancestor ")
                   << apostrophise(hepliaklqana_ally_name())
                   << " " << name << T_(" death");
            break;
#endif
          case NOTE_FOUND_UNRAND:
            result << T_("Found ") << name;
            break;
        case NOTE_ZOT_TOUCHED:
            result << T_("Touched by the power of Zot (MHP ") << first << " -> " << second << ")";
            break;
        case NOTE_DREAMSHARD:
            result << T_("Saved by the dreamshard amulet");
            break;
        case NOTE_GEM_LOST:
            result << T_("Lost the ")
                   << C_("gem appearance", gem_adj(static_cast<gem_type>(first)))
                   << T_(" gem through the power of Zot.");
            break;
        case NOTE_GAIN_LIFE:
            result << T_("Gained a life (") << first << (first == 1 ? T_(" life ") : T_(" lives ")) << T_("remaining)");
            break;
        case NOTE_LOSE_LIFE:
            result << T_("Lost a life (") << first << (first == 1 ? T_(" life ") : T_(" lives ")) << T_("remaining)");
            break;
        case NOTE_FLED_CHALLENGE:
            result << T_("Fled from a divine trial");
            break;
        case NOTE_INFERNAL_MARK:
        {
            mutation_type mark;
            {
                const ScopedLangEn english;
                mark = mutation_from_name(name, false);
            }
            const string display = mark < NUM_MUTATIONS && is_makhleb_mark(mark)
                ? mutation_name(mark) : name;
            result << make_stringf(T_("Branded self with the %s"), display.c_str());
            break;
        }
        case NOTE_TESSERACT_ACTIVATED:
            result << T_("Activated a boundless tesseract");
            break;
        default:
            result << "Buggy note description: unknown note type";
            break;
        }
    }

    if (type == NOTE_SEEN_MONSTER || type == NOTE_DEFEAT_MONSTER)
    {
        if (what && first == MONS_PANDEMONIUM_LORD)
            result << T_(" the pandemonium lord");
    }
    return result.str();
}

bool Note::hidden() const
{
    if (type == NOTE_START_SKILL)
        return !Options.note_starting_skills;
    // Hide skill gains that are not enabled by options.
    if (type == NOTE_GAIN_SKILL || type == NOTE_LOSE_SKILL)
    {
        return !(Options.note_all_skill_levels
                 || second <= 27 && Options.note_skill_levels[second]
                 || Options.note_skill_max && is_highest_skill(first));
    }
    // Hide gems being shattered by default.
    if (type == NOTE_GEM_LOST)
        return !Options.more_gem_info;
    return false;
}

void Note::check_milestone() const
{
    if (crawl_state.game_is_arena())
        return;

    if (type == NOTE_DUNGEON_LEVEL_CHANGE)
    {
        const int br = place.branch,
                 dep = place.depth;

        // Wizlabs report their milestones on their own.
        if (br != -1 && br != BRANCH_WIZLAB)
        {
            ASSERT_RANGE(br, 0, NUM_BRANCHES);
            string branch = place.describe(true, false);

            if (starts_with(branch, "The "))
                branch[0] = tolower_safe(branch[0]);

            if (dep == 1)
            {
                mark_milestone(br == BRANCH_ZIGGURAT ? "zig.enter" : "br.enter",
                               "entered " + branch + ".", "parent");
            }
            else if (dep == _dungeon_branch_depth(br)
                     || br == BRANCH_ZIGGURAT)
            {
                string level = place.describe(true, true);
                if (starts_with(level, "Level "))
                    level[0] = tolower_safe(level[0]);

                mark_milestone(br == BRANCH_ZIGGURAT ? "zig" : "br.end",
                               "reached " + level + ".");
            }
        }
    }
}

void Note::save(writer& outf) const
{
    marshallInt(outf, type);
    marshallInt(outf, turn);
    place.save(outf);
    marshallInt(outf, first);
    marshallInt(outf, second);
    marshallString4(outf, name);
    marshallString4(outf, desc);
    marshallString(outf, screen);
}

void Note::load(reader& inf)
{
    type = static_cast<NOTE_TYPES>(unmarshallInt(inf));
    turn = unmarshallInt(inf);
#if TAG_MAJOR_VERSION == 34
    if (inf.getMinorVersion() < TAG_MINOR_PLACE_UNPACK)
        place = level_id::from_packed_place(unmarshallShort(inf));
    else
        place.load(inf);
#else
    place.load(inf);
#endif
    first  = unmarshallInt(inf);
    second = unmarshallInt(inf);
    unmarshallString4(inf, name);
    unmarshallString4(inf, desc);
#if TAG_MAJOR_VERSION == 34
    if (inf.getMinorVersion() >= TAG_MINOR_MORGUE_SCREENSHOTS)
        screen = unmarshallString(inf);
#else
    screen = unmarshallString(inf);
#endif

}

static bool notes_active = false;

bool notes_are_active()
{
    return notes_active;
}

void take_note(const Note& note, bool force)
{
    if (notes_active && (force || _is_noteworthy(note)))
    {
        note_list.push_back(note);
        note.check_milestone();
    }
}

void activate_notes(bool active)
{
    notes_active = active;
}

void save_notes(writer& outf)
{
    marshallInt(outf, NOTES_VERSION_NUMBER);
    marshallInt(outf, note_list.size());
    for (const Note &note : note_list)
        note.save(outf);
}

void load_notes(reader& inf)
{
    if (unmarshallInt(inf) != NOTES_VERSION_NUMBER)
        return;

    const int num_notes = unmarshallInt(inf);
    for (int i = 0; i < num_notes; ++i)
    {
        Note new_note;
        new_note.load(inf);
        note_list.push_back(new_note);
    }
}

void make_user_note()
{
    char buf[400];
    const string prompt = string(T_("Enter note:")) + " ";
    bool validline = !msgwin_get_line(prompt, buf, sizeof(buf));
    if (!validline || (!*buf))
        return;
    Note unote(NOTE_USER_NOTE);
    unote.name = buf;
    // Only one screenshot a turn allowed
    if (last_screen_turn != unote.turn)
    {
        last_screen_turn = unote.turn;
        unote.screen = screenshot();
    }
    take_note(unote);
}
