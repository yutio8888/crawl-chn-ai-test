/**
 * @file
 * @brief Functions used to print information about gods.
 **/

#include "AppHdr.h"

#include "describe-god.h"

#include <iomanip>

#include "act-iter.h"
#include "ability.h"
#include "branch.h"
#include "cio.h"
#include "database.h"
#include "decks.h"
#include "describe.h"
#include "english.h"
#include "env.h"
#include "god-abil.h"
#include "god-companions.h"
#include "god-conduct.h"
#include "god-passive.h"
#include "god-type.h"
#include "items.h"
#include "item-name.h"
#include "libutil.h"
#include "menu.h"
#include "message.h"
#include "options.h"
#include "religion.h"
#include "skills.h"
#include "spl-util.h"
#include "stringutil.h"
#include "tag-version.h"
#include "terrain.h"
#include "tilepick.h"
#include "unicode.h"
#include "xom.h"

using namespace ui;

static int _piety_level(int piety)
{
    return (piety >= piety_breakpoint(5)) ? 7 :
           (piety >= piety_breakpoint(4)) ? 6 :
           (piety >= piety_breakpoint(3)) ? 5 :
           (piety >= piety_breakpoint(2)) ? 4 :
           (piety >= piety_breakpoint(1)) ? 3 :
           (piety >= piety_breakpoint(0)) ? 2 :
           (piety >                    0) ? 1
                                          : 0;
}

static int _gold_level()
{
    return (you.gold >= 50000) ? 7 :
           (you.gold >= 10000) ? 6 :
           (you.gold >=  5000) ? 5 :
           (you.gold >=  1000) ? 4 :
           (you.gold >=   500) ? 3 :
           (you.gold >=   100) ? 2 : 1;
}

static int _invocations_level()
{
    int invo = you.skills[SK_INVOCATIONS];
    return (invo == 27) ? 7 :
           (invo >= 24) ? 6 :
           (invo >= 20) ? 5 :
           (invo >= 16) ? 4 :
           (invo >= 12) ? 3 :
           (invo >= 8)  ? 2
                        : 1;
}

int god_favour_rank(god_type which_god)
{
    if (which_god == GOD_GOZAG)
        return _gold_level();
    else if (which_god == GOD_USKAYAW)
        return _invocations_level();
    else
        return _piety_level(you.raw_piety);
}

static string _describe_favour(god_type which_god)
{
    if (player_under_penance())
    {
        const int penance = you.penance[which_god];
        return (penance >= 50) ? T_("Godly wrath is upon you!") :
               (penance >= 20) ? T_("You've transgressed heavily! Be penitent!") :
               (penance >=  5) ? T_("You are under penance.")
                               : T_("You should show more discipline.");
    }

    if (which_god == GOD_XOM)
        return uppercase_first(describe_xom_favour());

    const string godname = god_name(which_god);
    switch (god_favour_rank(which_god))
    {
        case 7:
            return make_stringf(T_("A prized avatar of %s."), godname.c_str());
        case 6:
            return make_stringf(T_("A favoured servant of %s."), godname.c_str());
        case 5:
            if (you_worship(GOD_DITHMENOS))
                return make_stringf(T_("A glorious shadow in the eyes of %s."), godname.c_str());
            else
                return make_stringf(T_("A shining star in the eyes of %s."), godname.c_str());
        case 4:
            if (you_worship(GOD_DITHMENOS))
                return make_stringf(T_("A rising shadow in the eyes of %s."), godname.c_str());
            else
                return make_stringf(T_("A rising star in the eyes of %s."), godname.c_str());
        case 3:
            return make_stringf(T_("%s is pleased with you."), uppercase_first(godname).c_str());
        case 2:
            return make_stringf(T_("%s is aware of your devotion."), uppercase_first(godname).c_str());
        default:
            return make_stringf(T_("%s is noncommittal."), uppercase_first(godname).c_str());
    }
}

// The various titles granted by the god of your choice. Note that Xom
// doesn't use piety the same way as the other gods, so these are just
// placeholders.
static const char *divine_title[][8] =
{

    // No god.
    {T_("Buglet"),             T_("Firebug"),               T_("Bogeybug"),                 T_("Bugger"),
        T_("Bugbear"),            T_("Bugged One"),            T_("Giant Bug"),                T_("Lord of the Bugs")},

    // Zin.
    {T_("Blasphemer"),         T_("Anchorite"),             T_("Apologist"),                T_("Pious"),
        T_("Devout"),             T_("Orthodox"),              T_("Immaculate"),               T_("Bringer of Law")},

    // The Shining One.
    {T_("Honourless"),         T_("Acolyte"),               T_("Righteous"),                T_("Unflinching"),
        T_("Holy Warrior"),       T_("Exorcist"),              T_("Demon Slayer"),             T_("Bringer of Light")},

    // Kikubaaqudgha -- death scholar theme.
    {T_("Tormented"),          T_("Purveyor of Pain"),       T_("Pupil of Sorrows"),        T_("Merchant of Misery"),
     T_("Scholar of Souls"),   T_("Artisan of Death"),       T_("Demagogue of Despair"),    T_("Lord of Darkness")},

    // Yredelemnul -- fervent death knight theme.
    {T_("Traitor"),            T_("Torchbearer"),            T_("Despoiler"),               T_("Black Crusader"),
     T_("Fallen @Genus@"),     T_("Harbinger of Doom"),      T_("Inexorable Tide"),         T_("Bringer of Blasphemy")},

    // Xom.
    {T_("Toy"),                T_("Toy"),                   T_("Toy"),                      T_("Toy"),
        T_("Toy"),                T_("Toy"),                   T_("Toy"),                      T_("Toy")},

    // Vehumet -- battle mage theme.
    {T_("Meek"),               T_("Sorcerer's Apprentice"), T_("Scholar of Destruction"),   T_("Caster of Ruination"),
        T_("Traumaturge"),        T_("Battlemage"),            T_("Warlock"),                  T_("Luminary of Lethal Lore")},

    // Okawaru -- battle theme.
    {T_("Coward"),             T_("Struggler"),             T_("Combatant"),                T_("@Genus@-At-Arms"),
        T_("Knight"),             T_("Myrmidon"),             T_("Warmonger"),                T_("Victor of a Thousand Battles")},

    // Makhleb -- chaos theme.
    {T_("Orderly"),            T_("Spawn of Chaos"),        T_("Disciple of Destruction"),  T_("Fanfare of Bloodshed"),
        T_("Fiendish"),           T_("Demolition @Genus@"),    T_("Pandemonic"),               T_("Champion of Chaos")},

    // Sif Muna -- generalist scholarly theme.
    {T_("Ignorant"),           T_("Disciple"),              T_("Student"),                  T_("Adept"),
        T_("Scribe"),             T_("Scholar"),               T_("Sage"),                     T_("Genius of the Arcane")},

    // Trog -- anger theme.
    {T_("Puny"),               T_("Troglodyte"),            T_("Angry Troglodyte"),         T_("Frenzied"),
        T_("@Genus@ of Prey"),    T_("Rampant"),               T_("Wild @Genus@"),             T_("Bane of Scribes")},

    // Nemelex Xobeh -- alluding to Tarot and cards.
    {T_("Unlucky @Genus@"),    T_("Pannier"),               T_("Jester"),                   T_("Fortune-Teller"),
        T_("Soothsayer"),         T_("Magus"),                 T_("Cardsharp"),                T_("Hand of Fortune")},

    // Elyvilon.
    {T_("Sinner"),                T_("Practitioner"),       T_("Comforter"),             T_("Caregiver"),
        T_("Mender"),           T_("Pacifist"),                T_("Purifying @Genus@"),        T_("Bringer of Life")},

    // Lugonu -- distortion theme.
    {T_("Pure"),               T_("Abyss-Baptised"),        T_("Unweaver"),                 T_("Distorting @Genus@"),
        T_("Agent of Entropy"),   T_("Schismatic"),            T_("Envoy of Void"),            T_("Corrupter of Planes")},

    // Beogh -- messiah theme.
    {T_("Apostate"),           T_("Convert"),               T_("Proselytiser"),             T_("Priest"),
        T_("Missionary"),         T_("Evangelist"),            T_("Unifier"),                  T_("Messiah")},

    // Jiyva -- slime and jelly theme.
    {T_("Scum"),               T_("Squelcher"),             T_("Ooze"),                     T_("Jelly"),
        T_("Slime Creature"),     T_("Dissolving @Genus@"),    T_("Blob"),                     T_("Royal Jelly")},

    // Fedhas Madash -- nature theme.
    {T_("@Walking@ Fertiliser"), T_("Fungal"),              T_("Green @Genus@"),            T_("Cultivator"),
        T_("Fruitful"),           T_("Photosynthesist"),       T_("Green Death"),              T_("Force of Nature")},

    // Cheibriados -- slow theme
    {T_("Hasty"),              T_("Sluggish @Genus@"),      T_("Deliberate"),               T_("Unhurried"),
     T_("Contemplative"),         T_("Epochal"),               T_("Timeless"),                 T_("@Adj@ Aeon")},

    // Ashenzari -- divination theme
    {T_("Star-crossed"),       T_("Cursed"),                T_("Initiated"),                T_("Seer"),
        T_("Oracle"),            T_("Illuminatus"),            T_("Prince of Secrets"),        T_("Omniscient")},

    // Dithmenos -- darkness theme
    {T_("Conspicuous"),         T_("Nocturnal"),            T_("Bump in the Night"),        T_("Thespian"),
        T_("Tenebrous"),          T_("Puppetmaster"),          T_("@Walking@ Midnight"),       T_("Who Hides the Stars")},

    // Gozag -- entrepreneur theme
    {T_("Profligate"),         T_("Pauper"),                T_("Entrepreneur"),             T_("Capitalist"),
        T_("Rich"),               T_("Opulent"),               T_("Tycoon"),                   T_("Plutocrat")},

    // Qazlal -- natural disaster theme
    {T_("Unspoiled"),          T_("@Adj@ Mishap"),          T_("Lightning Rod"),            T_("@Adj@ Disaster"),
        T_("Eye of the Storm"),   T_("@Adj@ Catastrophe"),     T_("@Adj@ Cataclysm"),          T_("End of an Era")},

    // Ru -- enlightenment theme
    {T_("Sleeper"),           T_("Questioner"),             T_("Initiate"),                 T_("Seeker of Truth"),
        T_("@Walker@ of the Path"),T_("Lifter of the Veil"),     T_("Transcendent"),     T_("Drop of Water")},

#if TAG_MAJOR_VERSION == 34
    // Pakellas -- inventor theme
    {T_("Reactionary"),       T_("Apprentice"),             T_("Inquisitive"),              T_("Experimenter"),
        T_("Inventor"),           T_("Pioneer"),               T_("Brilliant"),                T_("Grand Gadgeteer")},
#endif

    // Uskayaw -- reveler theme
    {T_("Prude"),             T_("Wallflower"),             T_("Party-goer"),              T_("Dancer"),
        T_("Impassioned"),        T_("Rapturous"),             T_("Ecstatic"),                T_("Rhythm of Life and Death")},

    // Hepliaklqana -- memory/ancestry theme
    {T_("Damnatio Memoriae"),       T_("Hazy"),             T_("@Adj@ @Child@"),              T_("Storyteller"),
        T_("Brooding"),           T_("Anamnesiscian"),               T_("Grand Scion"),                T_("Unforgettable")},

    // Wu Jian -- animal/chinese martial arts monk theme
    {T_("Wooden Rat"),          T_("Young Dog"),             T_("Young Crane"),              T_("Young Tiger"),
        T_("Young Dragon"),     T_("Red Sash"),               T_("Golden Sash"),              T_("Sifu")},

    // Ignis -- fire/candles theme
    {T_("Extinguished"),          T_("Last Ember"),             T_("Glowing Coal"),              T_("Thurifer"),
        T_("Hearthfire"),     T_("Furnace"),               T_("Raging Flame"),              T_("Inferno")},

};
COMPILE_CHECK(ARRAYSZ(divine_title) == NUM_GODS);

string god_title(god_type which_god, species_type which_species, int piety)
{
    string title;
    if (player_under_penance(which_god))
        title = T_(divine_title[which_god][0]);
    else if (which_god == GOD_USKAYAW)
        title = T_(divine_title[which_god][_invocations_level()]);
    else if (which_god == GOD_GOZAG)
        title = T_(divine_title[which_god][_gold_level()]);
    else
        title = T_(divine_title[which_god][_piety_level(piety)]);

    const map<string, string> replacements =
    {
        { "Adj", species::name(which_species, species::SPNAME_ADJ) },
        { "Genus", species::name(which_species, species::SPNAME_GENUS) },
        { "Walking", species::walking_title(which_species) + "ing" },
        { "Walker", species::walking_title(which_species) + "er" },
        { "Child", species::child_name(which_species) },
        { "Orc", species::orc_name(which_species) },
    };

    return replace_keys(title, replacements);
}

static string _describe_item_curse(const item_def& item)
{
    if (!item.props.exists(CURSE_KNOWLEDGE_KEY))
        return T_("None");

    const CrawlVector &curses = item.props[CURSE_KNOWLEDGE_KEY].get_vector();

    if (curses.empty())
        return T_("None");

    return comma_separated_fn(curses.begin(), curses.end(),
            curse_name, ", ", ", ");
}

static string _describe_ash_skill_boost()
{
    ostringstream desc;
    desc.setf(ios::left);
    desc << "<white>";
    desc << setw(40) << T_("Bound item");
    desc << setw(30) << T_("Curse bonuses");
    desc << "</white>\n";

    vector<item_def*> eq = you.equipment.get_slot_items(SLOT_ALL_EQUIPMENT, true);
    for (item_def* item : eq)
    {
        if (item->cursed())
        {
            const bool meld = item_is_melded(*item);
            desc << (meld ? "<darkgrey>" : "<lightred>");
            desc << setw(40) << item->name(DESC_QUALNAME, true, false, false);
            desc << setw(30) << (meld
                ? (T_("melded"))
                : _describe_item_curse(*item));
            desc << (meld ? "</darkgrey>" : "</lightred>");
            desc << "\n";
        }
    }

    return desc.str();
}

typedef pair<int, string> ancestor_upgrade;

static const map<monster_type, vector<ancestor_upgrade> > ancestor_data =
{
    { MONS_ANCESTOR_KNIGHT,
      { { 1,  "Flail" },
        { 1,  "Shield" },
        { 1,  "Chain mail (+AC)" },
        { 15, "Broad axe (flame)" },
        { 19, "Tower shield (reflect)" },
        { 19, "Haste" },
        { 24, "Broad axe (speed)" },
      }
    },
    { MONS_ANCESTOR_BATTLEMAGE,
      { { 1,  "Quarterstaff" },
        { 1,  "Throw Frost" },
        { 1,  "Stone Arrow" },
        { 1,  "Increased melee damage" },
        { 15, "Bolt of Magma" },
        { 19, "Lajatang (freeze)" },
        { 19, "Haste" },
        { 24, "Lehudib's Crystal Spear" },
      }
    },
    { MONS_ANCESTOR_HEXER,
      { { 1,  "Dagger (drain)" },
        { 1,  "Slow" },
        { 1,  "Confuse" },
        { 15, "Paralyse" },
        { 19, "Mass Confusion" },
        { 19, "Haste" },
        { 24, "Quick blade (antimagic)" },
      }
    },
};

/// Translate ancestor upgrade name to Chinese (via T_()).
static const char* _zh_ancestor_upgrade(const char* en)
{
    if (!en || !en[0])
        return en;
    return T_(en);
}

/// Build & return a table of Hep's upgrades for your chosen ancestor type.
static string _describe_ancestor_upgrades()
{
    if (!you.props.exists(HEPLIAKLQANA_ALLY_TYPE_KEY))
        return "";

    string desc;
    const monster_type ancestor =
        static_cast<monster_type>(you.props[HEPLIAKLQANA_ALLY_TYPE_KEY].get_int());
    const vector<ancestor_upgrade> *upgrades = map_find(ancestor_data,
                                                        ancestor);

    if (upgrades)
    {
        desc = T_("Ancestor Upgrades:\n\n<white>XL              Upgrade\n</white>");
        for (auto &entry : *upgrades)
        {
            const char* name = _zh_ancestor_upgrade(entry.second.c_str());
            desc += make_stringf("%s%2d              %s%s\n",
                                 you.experience_level < entry.first
                                     ? "<darkgrey>" : "",
                                 entry.first,
                                 name,
                                 you.experience_level < entry.first
                                     ? "</darkgrey>" : "");
        }
    }

    // XXX: maybe it'd be nice to let you see other ancestor types'...?
    return desc;
}

// from dgn-overview.cc
extern map<branch_type, set<level_id> > stair_level;

/**
 * Populate a provided vector with a list of bribable branches which are known
 * to the player.
 *
 * @param[out] targets      A list of bribable branches.
 */
static void _list_bribable_branches(vector<branch_type> &targets)
{
    for (branch_iterator it; it; ++it)
    {
        const branch_type br = it->id;
        if (!gozag_branch_bribable(br))
            continue;

        // Only list the Hells once.
        if (is_hell_subbranch(br))
            continue;

        // If you don't know the branch exists, don't list it;
        // this mainly plugs info leaks about Lair branch structure.
        if (!stair_level.count(br))
            continue;

        targets.push_back(br);
    }
}

/**
 * Describe the current options for Gozag's bribe branch ability.
 *
 * @return      A description of branches' bribe status.
 */
static string _describe_branch_bribability()
{
    string ret = T_("You can bribe the following branches of the dungeon:\n");
    vector<branch_type> targets;
    _list_bribable_branches(targets);

    size_t width = 0;
    for (branch_type br : targets)
        width = max(width, (size_t)strwidth(T_(branches[br].shortname)));

    for (branch_type br : targets)
    {
        string line = " ";
        line += T_(branches[br].shortname);
        line += string(width + 3 - strwidth(line), ' ');

        if (!branch_bribe[br])
            line += T_("not bribed");
        else
            line += make_stringf("$%d", branch_bribe[br]);

        ret += line + "\n";
    }

    return ret;
}

static inline void _add_par(formatted_string &desc, const string &str)
{
    if (!str.empty())
        desc += formatted_string::parse_string(trimmed_string(str) + "\n\n");
}

/**
 * Describe the causes of the given god's wrath.
 *
 * @param which_god     The god in question.
 * @return              A description of the actions that cause this god's
 *                      wrath.
 */
static string _describe_god_wrath_causes(god_type which_god)
{
    if (which_god == GOD_RU)
        return ""; // no wrath
    vector<god_type> evil_gods;
    vector<god_type> chaotic_gods;
    for (god_iterator it; it; ++it)
    {
        const god_type god = *it;
        if (is_evil_god(god))
            evil_gods.push_back(god);
        else if (is_chaotic_god(god)) // intentionally not including evil!
            chaotic_gods.push_back(god);
        // XXX: refactor this if any god hates chaotic but not evil gods
    }

    // RETAIN: Language-appropriate delimiters for list joining — UI formatting, not translation text
    const char* and_word = Options.language == lang_t::ZH ? "和" : " and ";
    const char* sep_word = Options.language == lang_t::ZH ? "、" : ", ";

    switch (which_god)
    {
        case GOD_SHINING_ONE:
        case GOD_ELYVILON:
        {
            string evil_list = comma_separated_fn(
                begin(evil_gods), end(evil_gods),
                bind(god_name, placeholders::_1, false),
                and_word, sep_word);
            return make_stringf(
                T_("%s forgives followers for abandonment; however, those who "
                   "later take up the worship of an evil god will be "
                   "punished. (%s are evil gods.)"),
                uppercase_first(god_name(which_god)).c_str(),
                evil_list.c_str());
        }

        case GOD_ZIN:
        {
            string evil_list = comma_separated_fn(
                begin(evil_gods), end(evil_gods),
                bind(god_name, placeholders::_1, false),
                and_word, sep_word);
            string chaotic_list = comma_separated_fn(
                begin(chaotic_gods), end(chaotic_gods),
                bind(god_name, placeholders::_1, false),
                and_word, sep_word);
            return make_stringf(
                T_("%s forgives followers for abandonment; however, those who "
                   "later take up the worship of an evil or chaotic god will "
                   "be scourged. (%s are evil, and %s are chaotic.)"),
                uppercase_first(god_name(which_god)).c_str(),
                evil_list.c_str(),
                chaotic_list.c_str());
        }

        default:
            return make_stringf(
                T_("%s does not appreciate abandonment, and will call down "
                   "fearful punishments on disloyal followers!"),
                uppercase_first(god_name(which_god)).c_str());
    }
}

/**
 * Print a description of the given god's dislikes & wrath effects.
 *
 * @param which_god     The god in question.
 */
static formatted_string _god_wrath_description(god_type which_god)
{
    formatted_string desc;

    _add_par(desc, get_god_dislikes(which_god));
    _add_par(desc, _describe_god_wrath_causes(which_god));
    _add_par(desc, getLongDescription(string(_god_name_en(which_god)) + " wrath"));

    if (which_god != GOD_RU) // Permanent wrath.
    {
        const bool long_wrath = initial_wrath_penance_for(which_god) > 30;
        // ZH uses "的" genitive, EN uses apostrophise() + uppercase_first()
        string wrath_god_label;
        if (Options.language == lang_t::ZH)
            wrath_god_label = god_name(which_god);
        else
            wrath_god_label = uppercase_first(apostrophise(god_name(which_god)));
        _add_par(desc,
            make_stringf(T_("%s wrath lasts for a relatively %s duration."),
                wrath_god_label.c_str(),
                long_wrath ? T_("long") : T_("short")));
    }

    return desc;
}

static formatted_string _beogh_extra_description()
{
    formatted_string desc;

    for (int i = 1; i <= get_num_apostles(); ++i)
        _add_par(desc, apostle_short_description(i));

    if (you.duration[DUR_BEOGH_CAN_RECRUIT])
    {
        _add_par(desc, "-----------------------------------\n");
        _add_par(desc, apostle_short_description(0));
    }

    return desc;
}

static string _describe_deck_summary()
{
    ostringstream desc;
    desc << (T_("Decks of power:\n"));
    for (int i = FIRST_PLAYER_DECK; i <= LAST_PLAYER_DECK; i++)
        desc << " " << deck_status((deck_type) i) << "\n";

    string stack = stack_contents();
    if (!stack.empty())
        desc << (T_("\n stacked deck: "))
             << stack << "\n";

    return desc.str();
}

static formatted_string _god_extra_description(god_type which_god)
{
    formatted_string desc;

    switch (which_god)
    {
        case GOD_ASHENZARI:
            desc = formatted_string::parse_string(
                       getLongDescription(string(_god_name_en(which_god)) + " extra"));
            if (have_passive(passive_t::bondage_skill_boost))
            {
                desc.cprintf("\n");
                _add_par(desc, T_("Ashenzari supports the following skill groups because of your curses:"));
                _add_par(desc,  _describe_ash_skill_boost());
            }
            break;
        case GOD_BEOGH:
            if (you_worship(GOD_BEOGH))
                desc = _beogh_extra_description();
            break;
        case GOD_GOZAG:
            if (you_worship(GOD_GOZAG))
                _add_par(desc, _describe_branch_bribability());
            break;
        case GOD_HEPLIAKLQANA:
            if (you_worship(GOD_HEPLIAKLQANA))
                desc = formatted_string::parse_string(_describe_ancestor_upgrades());
            break;
        case GOD_NEMELEX_XOBEH:
            if (you_worship(GOD_NEMELEX_XOBEH))
                _add_par(desc, _describe_deck_summary());
            break;
        case GOD_WU_JIAN:
            _add_par(desc, T_("Martial attacks:"));
            desc += formatted_string::parse_string(
                        getLongDescription(string(_god_name_en(which_god)) + " extra"));
            break;
        default:
            break;
    }

    return desc;
}

/**
 * Describe miscellaneous information about the given god.
 *
 * @param which_god     The god in question.
 * @return              Info about gods which isn't covered by their powers,
 *                      likes, or dislikes.
 */
static string _get_god_misc_info(god_type which_god)
{
    string info = "";
    skill_type skill = invo_skill(which_god);

    // T_() format string with %s for god_name and skill_name
    // Minimal genitive wrapper: ZH uses god_name() directly, EN uses apostrophise()
    switch (skill)
    {
        case SK_INVOCATIONS:
            break;
        case SK_NONE:
        {
            const string god_label = Options.language == lang_t::ZH
                ? god_name(which_god)
                : uppercase_first(apostrophise(god_name(which_god)));
            info += make_stringf(T_("%s powers are not affected by the %s skill."),
                         god_label.c_str(),
                         skill_name(SK_INVOCATIONS));
            break;
        }
        default:
        {
            const string god_label = Options.language == lang_t::ZH
                ? god_name(which_god)
                : uppercase_first(apostrophise(god_name(which_god)));
            info += make_stringf(T_("%s powers are based on %s instead of %s skill."),
                         god_label.c_str(),
                         skill_name(skill),
                         skill_name(SK_INVOCATIONS));
            break;
        }
    }

    if (!info.empty())
        info += "\n\n";

    return info;
}

/**
 * Print a detailed description of the given god's likes and powers.
 *
 * @param god       The god in question.
 */
static formatted_string _detailed_god_description(god_type which_god)
{
    formatted_string desc;
    _add_par(desc, getLongDescription(string(_god_name_en(which_god)) + " powers"));
    _add_par(desc, get_god_likes(which_god));
    _add_par(desc, _get_god_misc_info(which_god));
    return desc;
}

/**
 * Describe the given god's level of irritation at the player.
 *
 * Player may or may not be currently under penance.
 *
 * @param which_god     The god in question.
 * @return              A format string, describing the god's ire (or lack of).
 */
static string _raw_penance_message(god_type which_god)
{
    const int penance = you.penance[which_god];

    // Give more appropriate message for the good gods.
    if (penance > 0 && is_good_god(which_god))
    {
        if (is_good_god(you.religion))
            return T_("%s is ambivalent towards you.");
        if (!god_hates_your_god(which_god))
        {
            return T_("%s is almost ready to forgive your sins.");
                 // == "Come back to the one true church!"
        }
    }

    const int initial_penance = initial_wrath_penance_for(which_god);
    // could do some math tricks to turn this into a table, but it seems fiddly
    if (penance > initial_penance * 3 / 4)
        return T_("%s's wrath is upon you!");
    if (penance > initial_penance / 2)
        return T_("%s well remembers your sins.");
    if (penance > initial_penance / 4)
        return T_("%s's wrath is beginning to fade.");
    if (penance > 0)
    {
        if (which_god == GOD_IGNIS)
            return T_("%s' wrath will not burn much longer.");
        return T_("%s is almost ready to forgive your sins.");
    }
    return T_("%s is neutral towards you.");
}

/**
 * Describe the given god's level of irritation at the player.
 *
 * Player may or may not be currently under penance.
 *
 * @param which_god     The god in question.
 * @return              A description of the god's ire (or lack thereof).
 */
static string _god_penance_message(god_type which_god)
{
    const string message = _raw_penance_message(which_god);
    return make_stringf(message.c_str(),
                        uppercase_first(god_name(which_god)).c_str());
}

/**
 * Print a description of the powers & abilities granted to the player by the
 * given god. If player worships the god, the currently available powers are
 * highlighted.
 *
 * @param which_god     The god in question.
 */
static formatted_string _describe_god_powers(god_type which_god)
{
    formatted_string desc;

    int piety = you_worship(which_god) ? you.piety() : 0;

    desc.textcolour(LIGHTGREY);
    const char *header = T_("Granted powers:");
    const char *cost   = T_("(Cost)");
    desc.cprintf("\n\n%s%*s%s\n", header,
            80 - strwidth(header) - strwidth(cost),
            "", cost);

    bool have_any = false;

    // set default color here, so we don't have to set in multiple places for
    // always available passive abilities
    if (!you_worship(which_god))
        desc.textcolour(DARKGREY);
    else
        desc.textcolour(god_colour(which_god));

    // mv: Some gods can protect you from harm.
    // The god isn't really protecting the player - only sometimes saving
    // their life.
    if (god_gives_passive(which_god, passive_t::protect_from_harm)
        || god_gives_passive(which_god, passive_t::lifesaving))
    {
        have_any = true;

        const char *how = "";

        if (god_gives_passive(which_god, passive_t::lifesaving))
        {
            // Category B fix: T_() adverb fragments for different EN/ZH positions
            how = (piety >= piety_breakpoint(5)) ? T_("carefully") :
                  (piety >= piety_breakpoint(3)) ? T_("often") :
                  (piety >= piety_breakpoint(1)) ? T_("sometimes")
                                                 : T_("occasionally");
        }
        else
        {
            // Category B fix: T_() adverb fragments
            how = (piety >= piety_breakpoint(5)) ? T_("sometimes")
                                                 : T_("occasionally");
        }

        desc.cprintf(T_("%s%s protects your life.\n"),
                uppercase_first(god_name(which_god)).c_str(),
                how);
    }

    switch (which_god)
    {
    case GOD_BEOGH:
    {
        have_any = true;
        if (have_passive(passive_t::convert_orcs))
            desc.textcolour(god_colour(which_god));
        else
            desc.textcolour(DARKGREY);

        if (piety >= piety_breakpoint(5))
            desc.cprintf(T_("Orcs frequently recognise you as Beogh's chosen one.\n"));
        else
            desc.cprintf(T_("Orcs sometimes recognise you as one of them.\n"));
    }
    break;

    case GOD_ZIN:
    {
        have_any = true;
        // Category B fix: T_() adverb fragments for different EN/ZH positions
        const char *how =
            (piety >= piety_breakpoint(5)) ? T_("always") :
            (piety >= piety_breakpoint(3)) ? T_("often") :
            (piety >= piety_breakpoint(1)) ? T_("sometimes") :
                                             T_("occasionally");

        desc.cprintf(T_("%s%s protects you from harm by chaos.\n"),
                uppercase_first(god_name(which_god)).c_str(), how);

        how =
            (piety >= piety_breakpoint(5)) ? T_("often") :
            (piety >= piety_breakpoint(3)) ? T_("sometimes") :
            (piety >= piety_breakpoint(1)) ? T_("occasionally") :
                                             T_("rarely");
        desc.cprintf(T_("%s%s protects you from hellish harm.\n"),
                uppercase_first(god_name(which_god)).c_str(), how);
        break;
    }

    case GOD_SHINING_ONE:
    {
        have_any = true;
        // TSO section: all format strings have different ARG positions between EN/ZH
        desc.cprintf(T_("%s prevents you from sneaking up on the defenceless.\n"),
                uppercase_first(god_name(which_god)).c_str());

        const int halo_size = you_worship(which_god) ? you.halo_radius() : -1;
        if (halo_size < 0)
            desc.textcolour(DARKGREY);
        else
            desc.textcolour(god_colour(which_god));
        // T_() format string with embedded adjective (large/small/none)
        desc.cprintf(T_("You radiate a%s aura of righteousness, "
                    "making those within it easier to hit.\n"),
                    halo_size > 5 ? T_(" large") :
                    halo_size > 3 ? "" :
                                    T_(" small"));

        if (piety >= piety_breakpoint(1))
            desc.textcolour(god_colour(which_god));
        else
            desc.textcolour(DARKGREY);
        // T_() adverb fragments for intensity; format string via T_()
        const char *how =
            (piety >= piety_breakpoint(5)) ? T_("completely") :
            (piety >= piety_breakpoint(3)) ? T_("mostly") :
                                             T_("partially");
        desc.cprintf(T_("%s%s protects you from negative energy.\n"),
                uppercase_first(god_name(which_god)).c_str(), how);
        break;
    }

    case GOD_JIYVA:
        have_any = true;
        desc.cprintf(T_("Jellies are peaceful and will eat items on the floor.\n"));
        desc.cprintf(T_("Jiyva prevents you from harming jellies.\n"));

        if (have_passive(passive_t::jelly_regen))
            desc.textcolour(god_colour(which_god));
        else
            desc.textcolour(DARKGREY);
        desc.cprintf(T_("Your life and magic regeneration are%s increased.\n"),
                     piety >= piety_breakpoint(5)
                        ? (T_("very greatly "))
                        : piety >= piety_breakpoint(3)
                        ? (T_("greatly "))
                        : "");
        break;

    case GOD_CHEIBRIADOS:
        have_any = true;
        if (have_passive(passive_t::stat_boost))
            desc.textcolour(god_colour(which_god));
        else
            desc.textcolour(DARKGREY);
        desc.cprintf(T_("%s%s slows your movement.\n"),
                uppercase_first(god_name(which_god)).c_str(),
                piety >= piety_breakpoint(5)
                    ? (T_("greatly "))
                    : piety >= piety_breakpoint(2)
                    ? ""
                    : (T_("slightly ")));
        desc.cprintf(T_("%s boosts your attributes. (+%d)\n"),
                uppercase_first(god_name(which_god)).c_str(),
                chei_stat_boost(piety));
        break;

    case GOD_VEHUMET:
        have_any = true;
        if (const int numoffers = you.vehumet_gifts.size())
        {
            const char* offer = numoffers == 1
                               ? spell_title(*you.vehumet_gifts.begin())
                               : (T_("some of Vehumet's most lethal spells"));
            desc.cprintf(T_("You can memorise %s.\n"), offer);
        }
        else if (!you.has_mutation(MUT_INNATE_CASTER))
        {
            desc.textcolour(DARKGREY);
            desc.cprintf(T_("You can memorise some of Vehumet's spells.\n"));
        }
        break;

    case GOD_YREDELEMNUL:
        // TODO: Vary the text depending on the size of the umbra.
        desc.cprintf(T_("You are surrounded by an umbra.\n"
                     "Enemies who die within your umbra may be risen as undead servants.\n"));
        break;

    case GOD_HEPLIAKLQANA:
        // Frailty occurs even under penance post-abandonment, so we can't put
        // this in the usual god_powers block.
        have_any = true;
    {
        const auto textcol = have_passive(passive_t::frail) ? god_colour(which_god) : DARKGREY;
        // We need to set textcolour before each line so that it'll display
        // correctly in webtiles. (It works fine locally regardless.)
        // Feature request: not this.
        desc.textcolour(textcol);
        desc.cprintf(T_("Your life essence is reduced. (-10%% HP)\n"));
    }
        break;

    default:
        break;
    }

    for (const auto& power : get_god_powers(which_god))
    {
        // hack: don't mention the necronomicon alone unless it
        // wasn't already mentioned by the other description
        if (power.abil == ABIL_KIKU_GIFT_CAPSTONE_SPELLS
            && !you.has_mutation(MUT_NO_GRASPING))
        {
            continue;
        }
        // Skip over Makhleb's brand options after the first one, since
        // only the first one has an associated god ability.
        if (power.abil == ABIL_MAKHLEB_BRAND_SELF_2
            || power.abil == ABIL_MAKHLEB_BRAND_SELF_3)
        {
            continue;
        }
        have_any = true;

        if (you_worship(which_god)
            && (power.rank <= 0
                || power.rank == 7 && can_do_capstone_ability(which_god)
                || piety_rank(piety) >= power.rank)
            && (!player_under_penance()
                || power.rank == -1))
        {
            desc.textcolour(god_colour(which_god));
        }
        else
            desc.textcolour(DARKGREY);

        // XXX: I don't like this, but there's no other obvious way to
        //      slot the destruction upgrade mutations in at the right piety
        //      point in the list for them.
        if (which_god == GOD_MAKHLEB && power.rank == 4)
        {
            desc.textcolour(god_colour(which_god));
            if (you.has_mutation(MUT_MAKHLEB_DESTRUCTION_GEH))
                desc.cprintf(T_("Your destruction is augmented by the fires of Gehenna.\n"));
            else if (you.has_mutation(MUT_MAKHLEB_DESTRUCTION_COC))
                desc.cprintf(T_("Your destruction is augmented by the ice of Cocytus.\n"));
            else if (you.has_mutation(MUT_MAKHLEB_DESTRUCTION_TAR))
                desc.cprintf(T_("Your destruction is augmented by the lamentations of Tartarus.\n"));
            else if (you.has_mutation(MUT_MAKHLEB_DESTRUCTION_DIS))
                desc.cprintf(T_("Your destruction is augmented by the Iron City of Dis.\n"));
            else
            {
                desc.textcolour(DARKGREY);
                desc.cprintf(T_("Your destruction will be augmented by one of the four Hells.\n"));
            }

            continue;
        }

        if (power.abil == ABIL_MAKHLEB_BRAND_SELF_1
            && !makhleb_mark_name().empty())
        {
                desc.textcolour(god_colour(which_god));
                desc.cprintf(T_("You are marked with %s.\n"), makhleb_mark_name().c_str());
                continue;
        }

        string buf = T_(power.general);

        // Skip listing powers with no description (they are intended to be hidden)
        if (buf.length() == 0)
        {
            have_any = false;
            continue;
        }

        // RETAIN: Only wrap with "You can" for English; Chinese translations are full sentences.
        if (Options.language != lang_t::ZH && !isupper(buf[0]))
            buf = "You can " + buf + ".";
        const int desc_len = strwidth(buf);

        string abil_cost = "(" + make_cost_description(power.abil) + ")";
        if (abil_cost == "(" + string(T_("None")) + ")")
            abil_cost = "";

        desc.cprintf("%s%*s%s\n", buf.c_str(), 80 - desc_len - (int)strwidth(abil_cost),
                "", abil_cost.c_str());
    }

    if (!have_any)
        desc.cprintf("%s\n", T_("None."));

    // Show Jiyva's opening of the Slime Pits at the bottom of the list
    // We want this to stay green permanently once the player hits 6*
    if (which_god == GOD_JIYVA)
    {
        if (you.one_time_ability_used[which_god])
            desc.textcolour(god_colour(which_god));
        else
            desc.textcolour(DARKGREY);
        desc.cprintf(T_("Jiyva will unlock the Slime Pits vault.\n"));
    }

    return desc;
}

static formatted_string _god_overview_description(god_type which_god)
{
    formatted_string desc;

    // Print god's description.
    const string god_desc = getLongDescription(_god_name_en(which_god));
    desc += trimmed_string(god_desc) + "\n";

    // Title only shown for our own god.
    if (you_worship(which_god))
    {
        // Print title based on piety.
        desc.cprintf(T_("\nTitle - "));
        desc.textcolour(god_colour(which_god));

        string title = god_title(which_god, you.species, you.raw_piety);
        desc.cprintf("%s", title.c_str());
    }

    // mv: Now let's print favour as Brent suggested.
    // I know these messages aren't perfect so if you can think up
    // something better, do it.

    desc.textcolour(LIGHTGREY);
    desc.cprintf(T_("\nFavour - "));
    desc.textcolour(god_colour(which_god));

    if (!you_worship(which_god))
        desc.cprintf("%s", _god_penance_message(which_god).c_str());
    else
        desc.cprintf("%s", _describe_favour(which_god).c_str());
    desc += _describe_god_powers(which_god);
    desc.cprintf("\n\n");

    return desc;
}

static void build_partial_god_ui(god_type which_god, shared_ptr<ui::Popup>& popup, shared_ptr<Switcher>& desc_sw, shared_ptr<Switcher>& more_sw)
{
    formatted_string topline;
    topline.textcolour(god_colour(which_god));
    topline += formatted_string(uppercase_first(god_name(which_god, true)));

    auto vbox = make_shared<Box>(Widget::VERT);
    vbox->set_cross_alignment(Widget::STRETCH);
    auto title_hbox = make_shared<Box>(Widget::HORZ);

#ifdef USE_TILE
    auto icon = make_shared<Image>();
    const tileidx_t idx = tileidx_feature_base(altar_for_god(which_god));
    icon->set_tile(tile_def(idx));
    title_hbox->add_child(std::move(icon));
#endif

    auto title = make_shared<Text>(topline.trim());
    title->set_margin_for_sdl(0, 0, 0, 16);
    title_hbox->add_child(std::move(title));

    title_hbox->set_main_alignment(Widget::CENTER);
    title_hbox->set_cross_alignment(Widget::CENTER);
    vbox->add_child(std::move(title_hbox));

    desc_sw = make_shared<Switcher>();
    more_sw = make_shared<Switcher>();
    desc_sw->current() = 0;
    more_sw->current() = 0;

    const formatted_string descs[4] = {
        _god_overview_description(which_god),
        _detailed_god_description(which_god),
        _god_wrath_description(which_god),
        _god_extra_description(which_god)
    };

    int mores_index = descs[3].empty() ? 0 : 1;
    const char* mores[2][4] =
    {
        {
            T_("[<w>!</w>]: <w>Overview</w>|Powers|Wrath"),
            T_("[<w>!</w>]: Overview|<w>Powers</w>|Wrath"),
            T_("[<w>!</w>]: Overview|Powers|<w>Wrath</w>"),
            T_("[<w>!</w>]: Overview|Powers|Wrath")
        },
        {
            T_("[<w>!</w>]: <w>Overview</w>|Powers|Wrath|Extra"),
            T_("[<w>!</w>]: Overview|<w>Powers</w>|Wrath|Extra"),
            T_("[<w>!</w>]: Overview|Powers|<w>Wrath</w>|Extra"),
            T_("[<w>!</w>]: Overview|Powers|Wrath|<w>Extra</w>")
        }
    };

    for (int i = 0; i < 4; i++)
    {
        const auto &desc = descs[i];
        if (desc.empty())
            continue;

        auto scroller = make_shared<Scroller>();
        auto text = make_shared<Text>(desc.trim());
        text->set_wrap_text(true);
        scroller->set_child(text);
        desc_sw->add_child(std::move(scroller));

        more_sw->add_child(make_shared<Text>(
                formatted_string::parse_string(mores[mores_index][i])));
    }

    desc_sw->set_margin_for_sdl(20, 0);
    desc_sw->set_margin_for_crt(1, 0);
    desc_sw->expand_h = false;
#ifdef USE_TILE_LOCAL
    desc_sw->max_size().width = tiles.get_crt_font()->char_width()*80;
#endif
    vbox->add_child(desc_sw);

    vbox->add_child(more_sw);

    popup = make_shared<ui::Popup>(vbox);
}

static const string _god_service_fee_description(god_type which_god)
{
    const int fee = (which_god == GOD_GOZAG) ? gozag_service_fee() : 0;

    if (which_god == GOD_GOZAG)
    {
        if (fee == 0)
        {
            const char* fees[] = { T_(" (no fee if you act now)"),
                                   T_(" (no fee if you join today)") };
            return RANDOM_ELEMENT(fees);
        }
        else
        {
            return make_stringf(T_(" (%d gold; you have %d)"), fee, you.gold);
        }
    }

    return "";
}

#ifdef USE_TILE_WEB
static void _send_god_ui(god_type god, bool is_altar)
{
    tiles.json_open_object();

    const tileidx_t idx = tileidx_feature_base(altar_for_god(god));
    tiles.json_open_object("tile");
    tiles.json_write_int("t", idx);
    tiles.json_write_int("tex", get_tile_texture(idx));
    tiles.json_close_object();

    tiles.json_write_int("colour", god_colour(god));
    tiles.json_write_string("name", god_name(god, true));
    tiles.json_write_bool("is_altar", is_altar);

    tiles.json_write_string("description", getLongDescription(_god_name_en(god)));
    if (you_worship(god))
        tiles.json_write_string("title", god_title(god, you.species, you.piety()));
    tiles.json_write_string("favour", you_worship(god) ?
            _describe_favour(god) : _god_penance_message(god));
    tiles.json_write_string("powers_list",
            _describe_god_powers(god).to_colour_string(LIGHTGREY));
    tiles.json_write_string("info_table", "");

    tiles.json_write_string("powers",
            _detailed_god_description(god).to_colour_string(LIGHTGREY));
    tiles.json_write_string("wrath",
            _god_wrath_description(god).to_colour_string(LIGHTGREY));
    tiles.json_write_string("extra",
            _god_extra_description(god).to_colour_string(LIGHTGREY));
    tiles.json_write_string("service_fee",
            _god_service_fee_description(god));
    tiles.push_ui_layout("describe-god", 1);
}
#endif

void describe_god(god_type which_god)
{
    if (which_god == GOD_NO_GOD) //mv: No god -> say it and go away.
    {
        mpr(T_("You have no religion."));
        return;
    }

    shared_ptr<ui::Popup> popup;
    shared_ptr<Switcher> desc_sw;
    shared_ptr<Switcher> more_sw;
    build_partial_god_ui(which_god, popup, desc_sw, more_sw);

    bool done = false;
    popup->on_keydown_event([&](const KeyEvent& ev) {
        const auto key = ev.key();
        if (key == '!' || key == '^')
        {
            int n = (desc_sw->current() + 1) % desc_sw->num_children();
            desc_sw->current() = more_sw->current() = n;
#ifdef USE_TILE_WEB
                tiles.json_open_object();
                tiles.json_write_int("pane", n);
                tiles.ui_state_change("describe-god", 0);
#endif
            return true;
        }
        if (desc_sw->current_widget()->on_event(ev))
            return true;
        return done = ui::key_exits_popup(key, false);
    });

#ifdef USE_TILE_WEB
    _send_god_ui(which_god, false);
    popup->on_layout_pop([](){ tiles.pop_ui_layout(); });
#endif

    ui::run_layout(popup, done);
}

bool describe_god_with_join(god_type which_god)
{
    const string service_fee = _god_service_fee_description(which_god);

    shared_ptr<ui::Popup> popup;
    shared_ptr<Switcher> desc_sw;
    shared_ptr<Switcher> more_sw;
    build_partial_god_ui(which_god, popup, desc_sw, more_sw);

    for (auto& child : *more_sw)
    {
        Text* label = static_cast<Text*>(child.get());
        formatted_string text = label->get_text();
        text += formatted_string::parse_string(
            T_("  [<w>J</w>/<w>回车</w>]: join"));

        // We assume that a player who has enough gold such that
        // the join fee plus accumulated gold overflows knows what this menu
        // does.
        if (text.width() + strwidth(service_fee) + 9 <= MIN_COLS)
            text += T_(" religion");
        if (!service_fee.empty())
            text += service_fee;
        label->set_text(text);
    }

    // States for the state machine
    enum join_step_type {
        SHOW = -1, // Show the usual god UI
        ABANDON, // Ask whether to abandon god, if applicable
    };

    // Add separate text widgets the possible abandon-god prompts;
    // then when a different prompt needs to be shown, we switch to that prompt.
    // This is somewhat brittle, but ensures that the UI doesn't resize when
    // switching between prompts.
    const string abandon_prompt = make_stringf(
            T_("Are you sure you want to abandon %s?"),
            god_name(you.religion).c_str());
    formatted_string prompt_fs(abandon_prompt, channel_to_colour(MSGCH_PROMPT));

    more_sw->add_child(make_shared<Text>(prompt_fs));

    prompt_fs.cprintf(T_(" Please press [Y]es or [n]no."));
    more_sw->add_child(make_shared<Text>(prompt_fs));

    join_step_type step = SHOW;
    bool yesno_only = false;
    bool done = false, join = false;

    // The join-god UI state machine transition function
    popup->on_keydown_event([&](const KeyEvent& ev) {
        const auto keyin = ev.key();

        // Always handle escape and pane-switching keys the same way
        if (ui::key_exits_popup(keyin, false))
            return done = true;
        if (keyin == '!' || keyin == '^')
        {
            int n = (desc_sw->current() + 1) % desc_sw->num_children();
            desc_sw->current() = n;
#ifdef USE_TILE_WEB
            tiles.json_open_object();
            tiles.json_write_int("pane", n);
            tiles.ui_state_change("describe-god", 0);
#endif
            if (step == SHOW)
            {
                more_sw->current() = n;
                return true;
            }
            else
                yesno_only = false;
        }

        // Next, allow child widgets to handle scrolling keys
        // NOTE: these key exceptions are also specified in ui-layouts.js
        if (keyin != 'J' && keyin != CK_ENTER)
            if (desc_sw->current_widget()->on_event(ev))
                return true;

        if (step == ABANDON)
        {
            if (keyin != 'Y' && toupper_safe(keyin) != 'N')
                yesno_only = true;
            else
                yesno_only = false;

            if (toupper_safe(keyin) == 'N')
            {
                canned_msg(MSG_OK);
                return done = true;
            }

            if (keyin == 'Y')
                return done = join = true;
        }
        else if ((keyin == 'J' || keyin == CK_ENTER) && step == SHOW)
        {
            if (you_worship(GOD_NO_GOD))
                return done = join = true;

            step = ABANDON;
        }
        else
            return done = true;

#ifdef USE_TILE_WEB
        tiles.json_open_object();
        string prompt = abandon_prompt + (yesno_only ? T_(" Enter [Y]es or [n]o.") : "");
        tiles.json_write_string("prompt", prompt);
        tiles.json_write_int("pane", desc_sw->current());
        tiles.ui_state_change("describe-god", 0);
#endif
        if (step == ABANDON)
            more_sw->current() = desc_sw->num_children() + step*2 + yesno_only;
        return true;
    });

#ifdef USE_TILE_WEB
    _send_god_ui(which_god, true);
    popup->on_layout_pop([](){ tiles.pop_ui_layout(); });
#endif

    ui::run_layout(popup, done);

    return join;
}
