/**
 * @file
 * @brief Functions for handling player mutations.
**/

#include "AppHdr.h"

#include "mutation.h"

#include <algorithm>
#include <cmath>
#include <map>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sstream>

#include "act-iter.h"
#include "art-enum.h"
#include "ability.h"
#include "areas.h"
#include "cio.h"
#include "coordit.h"
#include "dactions.h"
#include "database.h" // getLongDescription
#include "delay.h"
#include "describe.h"
#include "english.h"
#include "env.h"
#include "god-abil.h"
#include "god-passive.h"
#include "hints.h"
#include "item-prop.h"
#include "items.h"
#include "libutil.h"
#include "melee-attack.h" // mut_aux_attack_desc
#include "menu.h"
#include "message.h"
#include "mon-place.h"
#include "notes.h"
#include "options.h"
#include "output.h"
#include "player-stats.h"
#include "religion.h"
#include "skills.h"
#include "state.h"
#include "stringutil.h"
#include "tag-version.h"
#include "terrain.h"
#include "transform.h"
#include "unicode.h"
#include "view.h"
#include "xom.h"

using namespace ui;

static string _future_mutation_description(mutation_type mut, int levels);

struct body_facet_def
{
    equipment_slot slot;
    mutation_type mut;
};

struct facet_def
{
    int tier;
    mutation_type muts[3];
    int when[3];
};

struct demon_mutation_info
{
    mutation_type mut;
    int when;
    int facet;

    demon_mutation_info(mutation_type m, int w, int f)
        : mut(m), when(w), facet(f) { }
};

enum class mutflag
{
    good    = 1 << 0, // used by benemut etc
    bad     = 1 << 1, // used by malmut etc
    jiyva   = 1 << 2, // jiyva-only muts
    makhleb = 1 << 3, // makhleb capstone marks

    // Flags controlling how mutations are suppressed by various forms, as well
    // as which a given species is allowed to mutate naturally.
    need_blood = 1 << 4,   // requires the player to have blood
    need_bones = 1 << 5,   // requires the player to have bones
    need_hands = 1 << 6,   // requires the player to have hands (or similar limbs)
    need_feet  = 1 << 7,   // requires the player to have feet
    substance  = 1 << 8,   // supressed if the player's substance changes
                           // (ie: a gargoyle becoming a wisp, but NOT death form)
    anatomy    = 1 << 9,   // suppressed if the player's shape/body-plan changes
                           // (ie: most full body transformations)
    scales     = 1 << 10,  // conflicts with other scales mutations
                           // (implies substance and anatomy)

    last = scales
};
DEF_BITFIELD(mutflags, mutflag, 10);
COMPILE_CHECK(mutflags::exponent(mutflags::last_exponent) == mutflag::last);

#include "mutation-data.h"
#include "bane-data.h"

// XXX: Any normal mutation which removes a slot should be in this list, whether
//      or not it is actually part of a demonspawn facet, as this is used in
//      code which protects against mutations shattering cursed equipment, as
//      well as preventing multiple different mutations that affect the same
//      slot coexisting.
static const body_facet_def _body_facets[] =
{
    { SLOT_HELMET, MUT_HORNS },
    { SLOT_HELMET, MUT_ANTENNAE },
    { SLOT_HELMET, MUT_BEAK },
    { SLOT_GLOVES, MUT_CLAWS },
    { SLOT_GLOVES, MUT_DEMONIC_TOUCH },
    { SLOT_BOOTS, MUT_HOOVES },
    { SLOT_BOOTS, MUT_TALONS },
    { SLOT_CLOAK, MUT_WEAKNESS_STINGER }
};

vector<mutation_type> get_removed_mutations()
{
    static vector<mutation_type> removed_mutations =
    {
#if TAG_MAJOR_VERSION == 34
        MUT_ROUGH_BLACK_SCALES,
        MUT_BREATHE_FLAMES,
        MUT_BREATHE_POISON,
        MUT_CARNIVOROUS,
        MUT_CLING,
        MUT_CONSERVE_POTIONS,
        MUT_CONSERVE_SCROLLS,
        MUT_EXOSKELETON,
        MUT_FAST_METABOLISM,
        MUT_FLEXIBLE_WEAK,
        MUT_FOOD_JELLY,
        MUT_FUMES,
        MUT_HERBIVOROUS,
        MUT_JUMP,
        MUT_SAPROVOROUS,
        MUT_SLOW_METABOLISM,
        MUT_STRONG_STIFF,
        MUT_SUSTAIN_ATTRIBUTES,
        MUT_TELEPORT_CONTROL,
        MUT_TRAMPLE_RESISTANCE,
        MUT_MUMMY_RESTORATION,
        MUT_NO_CHARM_MAGIC,
        MUT_MIASMA_IMMUNITY,
        MUT_BLURRY_VISION,
        MUT_BLINK,
        MUT_UNBREATHING,
        MUT_GOURMAND,
        MUT_AWKWARD_TONGUE,
        MUT_NOISE_DAMPENING,
        MUT_BERSERK,
        MUT_STOCHASTIC_TORMENT_RESISTANCE,
        MUT_ROLL,
        MUT_CURL,
        MUT_NO_CHARM_MAGIC,
        MUT_NO_TRANSMUTATION_MAGIC,
        MUT_VAMPIRISM,
#endif
    };

    return removed_mutations;
}

struct mutation_conflict
{
    mutation_type   mut1;
    mutation_type   mut2;
    bool            is_inverse;

    // Gets which of these two mutations conflicts with a given mutation (or
    // MUT_NON_MUTATION if neither do).
    mutation_type get_conflict(mutation_type mut) const
    {
        if (mut == mut1)
            return mut2;
        else if (mut == mut2)
            return mut1;
        else
            return MUT_NON_MUTATION;
    }
};

/**
 * Conflicting mutation pairs. Entries are symmetric (so if A conflicts
 * with B, B conflicts with A in the same way).
 *
 * There are two types of conflict, indicated by the is_inverse member:
 *   -If true, this pair of mutations are considered 'inverse' of each other.
 *    (eg: Dex + 2 and Dex - 2, or rF+ and rF-). Attempting to gain one while
 *    having levels of the other will subtract a level of the existing mutation
 *    instead. (If one of the two mutations are transient, they are allowed to
 *    coexist.)
 *
 *   -If false, this part of mutations is considered semantically incompatible
 *    (eg: having hooves for feet and also talons for feet). Neither is more
 *    or less than the other, but it makes no sense (either mechanically or
 *    flavor-wise) for them to coexist. Attempting to gain one while having the
 *    other will fail outright.
 */
static const mutation_conflict mut_conflicts[] =
{
    { MUT_STRONG,              MUT_WEAK,                    true},
    { MUT_CLEVER,              MUT_DOPEY,                   true},
    { MUT_AGILE,               MUT_CLUMSY,                  true},
    { MUT_ROBUST,              MUT_FRAIL,                   true},
    { MUT_HIGH_MAGIC,          MUT_LOW_MAGIC,               true},
    { MUT_WILD_MAGIC,          MUT_SUBDUED_MAGIC,           true},
    { MUT_REGENERATION,        MUT_INHIBITED_REGENERATION,  true},
    { MUT_FAST,                MUT_SLOW,                    true},
    { MUT_HEAT_RESISTANCE,     MUT_HEAT_VULNERABILITY,      true},
    { MUT_COLD_RESISTANCE,     MUT_COLD_VULNERABILITY,      true},
    { MUT_SHOCK_RESISTANCE,    MUT_SHOCK_VULNERABILITY,     true},
    { MUT_STRONG_WILLED,       MUT_WEAK_WILLED,             true},
    { MUT_MUTATION_RESISTANCE, MUT_DEVOLUTION,              true},
    { MUT_EVOLUTION,           MUT_DEVOLUTION,              true},
    { MUT_MUTATION_RESISTANCE, MUT_EVOLUTION,               true},

    { MUT_FANGS,               MUT_BEAK,                   false},
    { MUT_ANTENNAE,            MUT_HORNS,                  false},
    { MUT_BEAK,                MUT_HORNS,                  false},
    { MUT_BEAK,                MUT_ANTENNAE,               false},
    { MUT_HOOVES,              MUT_TALONS,                 false},
    { MUT_HOOVES,              MUT_MERTAIL,                false},
    { MUT_TALONS,              MUT_MERTAIL,                false},
    { MUT_CLAWS,               MUT_DEMONIC_TOUCH,          false},
    { MUT_STINGER,             MUT_WEAKNESS_STINGER,       false},
    { MUT_STINGER,             MUT_MERTAIL,                false},
    { MUT_TRANSLUCENT_SKIN,    MUT_CAMOUFLAGE,             false},
    { MUT_ANTIMAGIC_BITE,      MUT_ACIDIC_BITE,            false},
    { MUT_HP_CASTING,          MUT_HIGH_MAGIC,             false},
    { MUT_HP_CASTING,          MUT_LOW_MAGIC,              false},
    { MUT_HP_CASTING,          MUT_EFFICIENT_MAGIC,        false},
    { MUT_ROLLPAGE,            MUT_INHIBITED_REGENERATION, false},

#if TAG_MAJOR_VERSION == 34
    { MUT_NO_REGENERATION,     MUT_INHIBITED_REGENERATION, false},
    { MUT_NO_REGENERATION,     MUT_REGENERATION,           false},
#endif

};

static int _mut_weight(const mutation_def &mut, mutflag flag)
{
    switch (flag)
    {
        case mutflag::jiyva:
            return 1;
        case mutflag::good:
        case mutflag::bad:
        default:
            return mut.weight;
    }
}

static int mut_index[NUM_MUTATIONS];
static int category_mut_index[MUT_NON_MUTATION - CATEGORY_MUTATIONS];
static map<mutflag, int> total_weight;

static int bane_index[NUM_BANES];

static const mutation_def& _get_mutation_def(mutation_type mut)
{
    ASSERT_RANGE(mut, 0, NUM_MUTATIONS);
    ASSERT(mut_index[mut] != -1);
    return mut_data[mut_index[mut]];
}

static bool _mut_has_flag(const mutation_def &mut, mutflag flag)
{
    return bool(mut.flags & flag);
}

static bool _mut_has_flag(mutation_type mut, mutflag flag)
{
    return bool(_get_mutation_def(mut).flags & flag);
}

void init_mut_index()
{
    total_weight.clear();
    for (int i = 0; i < NUM_MUTATIONS; ++i)
        mut_index[i] = -1;

    for (unsigned int i = 0; i < ARRAYSZ(mut_data); ++i)
    {
        const mutation_type mut = mut_data[i].mutation;
        ASSERT_RANGE(mut, 0, NUM_MUTATIONS);
        ASSERT(mut_index[mut] == -1);
        mut_index[mut] = i;
        for (const auto flag : mutflags::range())
        {
            if (_mut_has_flag(mut_data[i], flag))
                total_weight[flag] += _mut_weight(mut_data[i], flag);
        }
    }

    // Add dummy data for removed mutations
    vector<mutation_type> removed_muts = get_removed_mutations();
    for (unsigned int i = 0; i < removed_muts.size(); ++i)
        mut_index[removed_muts[i]] = ARRAYSZ(mut_data) - 1;

    // this is all a bit silly but ok
    for (int i = 0; i < MUT_NON_MUTATION - CATEGORY_MUTATIONS; ++i)
        category_mut_index[i] = -1;

    for (unsigned int i = 0; i < ARRAYSZ(category_mut_data); ++i)
    {
        const mutation_type mut = category_mut_data[i].mutation;
        ASSERT_RANGE(mut, CATEGORY_MUTATIONS, MUT_NON_MUTATION);
        ASSERT(category_mut_index[mut-CATEGORY_MUTATIONS] == -1);
        category_mut_index[mut-CATEGORY_MUTATIONS] = i;
    }

    for (int i = 0; i < NUM_BANES; ++i)
        bane_index[i] = -1;
    for (unsigned int i = 0; i < ARRAYSZ(bane_data); ++i)
        bane_index[bane_data[i].type] = i;
}

/*
 * Get the max number of possible levels for mutation `mut`. This is typically 1 or 3.
 *
 * @return the mutation cap.
 */
int get_mutation_cap(mutation_type mut)
{
    return _get_mutation_def(mut).levels;
}

static const mutation_category_def& _get_category_mutation_def(mutation_type mut)
{
    ASSERT_RANGE(mut, CATEGORY_MUTATIONS, MUT_NON_MUTATION);
    ASSERT(category_mut_index[mut-CATEGORY_MUTATIONS] != -1);
    return category_mut_data[category_mut_index[mut-CATEGORY_MUTATIONS]];
}

static bool _is_valid_mutation(mutation_type mut)
{
    return mut >= 0 && mut < NUM_MUTATIONS && mut_index[mut] != -1;
}

bool is_bad_mutation(mutation_type mut)
{
    return _mut_has_flag(mut_data[mut_index[mut]], mutflag::bad);
}

bool is_good_mutation(mutation_type mut)
{
    return _mut_has_flag(mut_data[mut_index[mut]], mutflag::good);
}

bool is_body_facet(mutation_type mut)
{
    return any_of(begin(_body_facets), end(_body_facets),
                  [=](const body_facet_def &facet)
                  { return facet.mut == mut; });
}

static string _suppressedmut(string desc, bool terse=false)
{
    return terse ? "(" + desc + ")" : "<darkgrey>((" + desc + "))</darkgrey>";
}

static string _innatemut(string desc, bool terse=false)
{
    return terse ? desc : "<lightblue>" + desc + "</lightblue>";
}

static string _formmut(string desc, bool terse=false)
{
    return terse ? desc : "<green>" + desc + "</green>";
}

static const char* _zh_mutation_name(const char* en);

static string _badmut(string desc, bool terse=false)
{
    return terse ? desc : "<lightred>" + desc + "</lightred>";
}

static pair<string, string> _annotate_form_based(pair<string, string> desc, bool suppressed)
{
    if (suppressed)
        return {_suppressedmut(desc.first, true), _suppressedmut(desc.second, false)};
    return {_innatemut(desc.first, true), _innatemut(desc.second, false)};
}

tileidx_t get_mutation_tile(mutation_type mut)
{
    return _get_mutation_def(mut).tile;
}

/*
 * Does the player have mutation `mut` with at least one temporary level?
 *
 * Reminder: temporary mutations can coexist with innate or normal mutations.
 */
bool player::has_temporary_mutation(mutation_type mut) const
{
    return you.temp_mutation[mut] > 0;
}

/*
 * Does the player have mutation `mut` with at least one innate level?
 *
 * Reminder: innate mutations can coexist with temporary or normal mutations.
 */
bool player::has_innate_mutation(mutation_type mut) const
{
    return you.innate_mutation[mut] > 0;
}

/*
 * How much of mutation `mut` does the player have? This ignores form changes.
 * If all three bool arguments are false, this should always return 0.
 *
 * @param temp   include temporary mutation levels. defaults to true.
 * @param innate include innate mutation levels. defaults to true.
 * @param normal include normal (non-temp, non-innate) mutation levels. defaults to true.
 *
 * @return the total levels of the mutation.
 */
int player::get_base_mutation_level(mutation_type mut, bool innate, bool temp, bool normal) const
{
    ASSERT_RANGE(mut, 0, NUM_MUTATIONS);
    // you.mutation stores the total levels of all mutations
    int level = you.mutation[mut];
    if (!temp)
        level -= you.temp_mutation[mut];
    if (!innate)
        level -= you.innate_mutation[mut];
    if (!normal)
        level -= (you.mutation[mut] - (you.temp_mutation[mut] + you.innate_mutation[mut]));
    ASSERT(level >= 0);
    return level;
}

/*
 * How much of mutation `mut` does the player have innately?
 *
 */
int player::get_innate_mutation_level(mutation_type mut) const
{
    ASSERT_RANGE(mut, 0, NUM_MUTATIONS);
    return you.innate_mutation[mut];
}

/*
 * How much of mutation `mut` does the player have temporarily?
 *
 */
int player::get_temp_mutation_level(mutation_type mut) const
{
    ASSERT_RANGE(mut, 0, NUM_MUTATIONS);
    return you.temp_mutation[mut];
}

/*
 * Get the current player mutation level for `mut`, possibly accounting for
 * mutation suppression due to transformations or circumstance.
 *
 * @param mut           The mutation to check
 * @param active_only   Whether to count only fully active mutations. Defaults to true.
 *
 * @return A mutation level; 0 if the mutation doesn't exist or is suppressed.
 */
int player::get_mutation_level(mutation_type mut, bool active_only) const
{
    ASSERT_RANGE(mut, 0, NUM_MUTATIONS);
    if (const int level = get_base_mutation_level(mut, true, true))
    {
        if (level == 0)
            return 0;

        if (!active_only || mut_is_compatible(mut))
            return level;
    }

    return 0;
}

/*
 * Does the player have mutation `mut` at the moment?
 */
bool player::has_mutation(mutation_type mut, bool active_only) const
{
    return get_mutation_level(mut, active_only) > 0;
}

bool player::has_bane(bane_type bane) const
{
    return you.banes[bane] > 0;
}

/*
 * Test the validity of the player mutation structures, using ASSERTs.
 * Will crash on a failure.
 *
 * @debug_msg whether to output diagnostic `dprf`s in the process.
 */
void validate_mutations(bool debug_msg)
{
    if (debug_msg)
        dprf("Validating player mutations");
    int total_temp = 0;

    for (int i = 0; i < NUM_MUTATIONS; i++)
    {
        mutation_type mut = static_cast<mutation_type>(i);
        if (debug_msg && you.mutation[mut] > 0)
        {
            dprf("mutation %s: total %d innate %d temp %d",
                mutation_name(mut), you.mutation[mut],
                you.innate_mutation[mut], you.temp_mutation[mut]);
        }
        ASSERT(you.get_base_mutation_level(mut) == you.mutation[mut]);
        ASSERT(you.mutation[i] >= you.innate_mutation[mut] + you.temp_mutation[mut]);
        total_temp += you.temp_mutation[mut];

        const mutation_def& mdef = _get_mutation_def(mut);
        ASSERT(you.mutation[mut] <= mdef.levels);

        // reconstruct what the innate mutations should be based on Ds mutation schedule
        // TODO generalize to all innate muts
        if (you.species == SP_DEMONSPAWN)
        {
            bool is_trait = false;
            int trait_level = 0;
            // If the player has sacrificed xp, use the pre-sac xl; sac xp
            // doesn't remove Ds mutations.
            // You can still trick wizmode into crashing here.
            const int check_xl = (you.get_mutation_level(MUT_INEXPERIENCED)
                            && you.max_level <= you.get_experience_level() + 2)
                                ? you.max_level
                                : you.get_experience_level();
            for (player::demon_trait trait : you.demonic_traits)
            {
                if (trait.mutation == mut)
                {
                    is_trait = true;
                    if (check_xl >= trait.level_gained)
                        trait_level += 1;
                }
            }

            if (debug_msg && is_trait)
            {
                dprf("scheduled innate for %s: %d, actual %d", mutation_name(mut),
                     trait_level, you.innate_mutation[mut]);
            }
            if (is_trait)
                ASSERT(you.innate_mutation[mut] == trait_level);
        }
    }
    ASSERT(total_temp == you.attribute[ATTR_TEMP_MUTATIONS]);

// #define DEBUG_MUTATIONS
#ifdef DEBUG_MUTATIONS
    if (debug_msg)
    {
        auto removed_v = get_removed_mutations();
        unordered_set<mutation_type, hash<int>> removed(removed_v.begin(), removed_v.end());
        vector<string> no_desc;

        for (int i = 0; i < NUM_MUTATIONS; i++)
        {
            mutation_type mut = static_cast<mutation_type>(i);
            if (removed.count(mut))
                continue;
            const string name = mutation_name(mut);
            string lookup = getLongDescription(name + " mutation");
            if (lookup.empty())
                no_desc.push_back(name);
        }
        dprf("Mutations with no description: %s",
                    join_strings(no_desc.begin(), no_desc.end(), ", ").c_str());
    }
#endif
}

static string _terse_mut_name(mutation_type mut)
{
    const int current_level = you.get_mutation_level(mut);
    const int base_level = you.get_base_mutation_level(mut);
    const bool lowered = current_level < base_level;
    const int temp_levels = you.get_base_mutation_level(mut, false, true, false); // only temp levels
    const int ordinary_levels = you.get_base_mutation_level(mut, true, false, true); // excluding temp levels

    const int max_levels = mutation_max_levels(mut);

    string current = mutation_name(mut);

    if (max_levels > 1)
    {
        // add on any numeric levels
        ostringstream ostr;
        ostr << " ";
        if (ordinary_levels == 0) // only temporary levels are present
            ostr << temp_levels;
        else
        {
            // at least some non-temporary levels
            ostr << ordinary_levels;
            if (temp_levels)
                ostr << "[+" << temp_levels << "]";
        }
        current += ostr.str();
    }

    // bracket the whole thing
    if (ordinary_levels == 0)
        current = "[" + current + "]";

    if (!current.empty())
    {
        if (current_level == 0) // suppressed by form
            current = "(" + current + ")";
        if (lowered)
            current = "<darkgrey>" + current + "</darkgrey>";
    }
    return current;
}

static vector<pair<string,string>> _get_form_fakemuts()
{
    vector<pair<string,string>> result;
    const auto *form = get_form(you.form);
    ASSERT(form);
    // The terse name for your transformation is not included in the normal
    // mutation list, but is used as an identifier for the mutation menu.
    result.push_back({"--transformation--", "<lightgreen>" + form->get_description() + "</lightgreen>"});

    vector<pair<string,string>> form_fakemuts = form->get_fakemuts();
    for (const auto &p : form_fakemuts)
            result.push_back({p.first, _formmut(p.second)});

    if (you.form == transformation::dragon)
    {
        if (!species::is_draconian(you.species)
            || you.species == SP_BASE_DRACONIAN) // ugh
        {
            result.push_back({ "golden breath", _formmut(T_("You can breathe a blast of fire, cold, and poison."))});
        }
        else if (species::draconian_breath(you.species) != ABIL_NON_ABILITY)
            result.push_back({ "", _formmut(T_("Your breath weapon is enhanced in this form."))});
    }

    // form-based flying can't be stopped, so don't print amphibiousness
    if (form->player_can_fly())
        result.push_back({"flying", _formmut(T_("You are flying."))});
    // n.b. this could cause issues for non-dragon giant forms if they exist
    else if (form->player_can_swim() && !species::can_swim(you.species))
        result.push_back({"amphibious", _formmut(T_("You are amphibious."))});

    const int hp_mod = form->mult_hp(10);
    if (hp_mod > 10)
    {
        result.push_back({"boosted hp",
                            _formmut(make_stringf(T_("Your maximum health is %sincreased."),
                                                    hp_mod < 13 ? "" : "greatly "))});
    } // see badmuts section below for max health reduction

    // Bad effects
    // Try to put all `_badmut`s together.

    if (hp_mod < 10)
    {
        result.push_back({"reduced hp",
                            _badmut(make_stringf(T_("Your maximum health is decreased%s."),
                                form->underskilled() ? ", since you lack skill for your form"
                                : ""))});
    }

    if (!form->can_cast)
        result.push_back({"no casting", _badmut(T_("You cannot cast spells."))});

    vector<pair<string,string>> form_badmuts = form->get_bad_fakemuts();
    for (const auto &p : form_badmuts)
            result.push_back({p.first, _badmut(p.second)});

    // Note: serpent form suppresses any innate cold-bloodedness
    if (you.form == transformation::serpent)
    {
        // XXX Hacky suppression with rC+
        if (you.res_cold())
        {
            result.push_back({"(cold-blooded)",
                "<darkgray>((You are cold-blooded and may be slowed by cold attacks.))</darkgray>"});
        }
        else
        {
            result.push_back({"cold-blooded",
                _badmut(T_("You are cold-blooded and may be slowed by cold attacks."))});
        }
    }

    if (you.form == transformation::blade
        && you_can_wear(SLOT_BODY_ARMOUR, false) != false)
    {
        const int penalty_percent = form->get_body_ac_mult();
        if (penalty_percent < 0)
        {
            result.push_back({"blade armour",
                    _badmut(make_stringf(T_("Your body armour is %s at protecting you."),
                          penalty_percent <=  -45 ? "much less effective"
                        : penalty_percent <   -20 ? "less effective"
                                                  : "slightly less effective"
            ))});
        }
    }

    if (!form->can_wield() && !you.has_mutation(MUT_NO_GRASPING))
    {
        // same as MUT_NO_GRASPING
        result.push_back({"", _badmut(T_("You are incapable of wielding weapons or throwing items."))});
    }

    // XX say something about AC? Best would be to compare it to AC without
    // the form, but I'm not sure if that's possible
    // AC is currently dealt with via the `A!` "form properties" screen.

    // XX better synchronizing with various base armour/eq possibilities
    if (!you.has_mutation(MUT_NO_ARMOUR))
    {
        const string melding_desc = form->melding_description(false);
        if (!melding_desc.empty())
            result.push_back({"", _badmut(melding_desc)});
    }

    return result;
}

static vector<pair<string, string>> _get_fakemuts()
{
    vector<pair<string, string>> result;

    // non-permanent and form-based stuff
    if (you.form != transformation::none)
    {
        vector<pair<string, string>> form_fakemuts = _get_form_fakemuts();
        result.insert(result.end(), form_fakemuts.begin(), form_fakemuts.end());
    }

    // divine effects
    if (you.can_water_walk())
    {
        result.push_back({"walk on water",
                    have_passive(passive_t::water_walk)
                        ? _formmut(T_("You can walk on water."))
                        : _formmut(T_("You can walk on water until reaching land."))});
    }

    if (you.props.exists(ORCIFICATION_LEVEL_KEY))
    {
        result.push_back({"",
                    you.props[ORCIFICATION_LEVEL_KEY].get_int() == 1
                        ? _formmut(T_("Your facial features look somewhat orcish."))
                        : _formmut(T_("Your facial features are unmistakably orcish."))});
    }

    if (have_passive(passive_t::frail)
        || player_under_penance(GOD_HEPLIAKLQANA))
    {
        // XX message is probably wrong for penance?
        result.push_back({"reduced essence",
                          _badmut("Your life essence is reduced to manifest your ancestor. (-10% HP)")});
    }

    // Innate abilities which haven't been implemented as mutations yet.
    vector<string> short_fakemut = species::fake_mutations(you.species, true);
    vector<string> long_fakemut = species::fake_mutations(you.species, false);
    for (size_t i = 0; i < long_fakemut.size(); ++i)
    {
        if (species::is_draconian(you.species))
        {
            result.push_back(_annotate_form_based({short_fakemut[i], long_fakemut[i]},
                                form_changes_anatomy() && you.form != transformation::dragon));
        }
        else
        {
            result.push_back({_innatemut(short_fakemut[i], true),
                              _innatemut(long_fakemut[i], false)});
        }
    }

    if (you.racial_ac(false) > 0)
    {
        const int ac = you.racial_ac(false) / 100;

        // XX generalize this code somehow?
        const string scale_clause = string(species::scale_type(you.species))
                  + " scales are hard";

        string ac_str = make_stringf("Your %s. (AC +%d)", you.species == SP_NAGA
                                        ? "serpentine skin is tough"
                                        : scale_clause.c_str(),
                                        ac);
        result.push_back(_annotate_form_based({"AC +" + to_string(ac), ac_str},
                            (form_changes_anatomy() || form_changes_substance())
                                && !(species::is_draconian(you.species)
                                && you.form == transformation::dragon)));
    }

    // player::can_swim includes other cases, e.g. extra-balanced species that
    // are not truly amphibious. Mertail has its own description that implies
    // amphibiousness.
    if (species::can_swim(you.species) && !you.has_innate_mutation(MUT_MERTAIL))
    {
        result.push_back(_annotate_form_based({"amphibious", T_("You are amphibious.")},
                                              !form_can_swim()));
    }

    if (species::arm_count(you.species) > 2)
    {
        const bool rings_melded = get_form()->slot_is_blocked(SLOT_RING);
        const int arms = you.arm_count();
        result.push_back(_annotate_form_based(
            {
                make_stringf("%d rings", arms),
                make_stringf("You can wear up to %s rings at the same time.",
                        number_in_words(arms).c_str())
            }, rings_melded));
    }

    // in the terse list, this adj + a minimal size-derived desc covers the
    // same ground as the detailed size-derived desc; so no need for the size
    // itself in the long form.
    const char* size_adjective = get_size_adj(you.body_size(PSIZE_BODY), true);
    if (size_adjective)
        result.push_back({size_adjective, ""});

    // XX is there a cleaner approach?
    pair<string, string> armour_mut;
    pair<string, string> weapon_mut;

    switch (you.body_size(PSIZE_TORSO, true))
    {
    case SIZE_LITTLE:
        armour_mut = {"unfitting armour",
                      _innatemut("You are too small for most types of armour.")};
        weapon_mut = {"no large weapons",
                      _innatemut("You are very small and have problems with some larger weapons.")};
        break;
    case SIZE_SMALL:
        weapon_mut = {"no large weapons",
                      _innatemut("You are small and have problems with some larger weapons.")};
        break;
    case SIZE_LARGE:
        armour_mut = {"unfitting armour",
                      _innatemut("You are too large for most types of armour.")};
        break;
    default: // no giant species
        break;
    }
    // Could move this into species-data, but then the hack that assumes
    // _dragon_abil should get called on all draconian fake muts would break.
    if (species::is_draconian(you.species))
    {
        armour_mut = {"unfitting armour",
                      _innatemut("You cannot fit into any form of body armour or wear helmets.")};
    }
    if (!weapon_mut.first.empty() && !you.has_mutation(MUT_NO_GRASPING))
        result.push_back(weapon_mut);
    if (!armour_mut.first.empty() && !you.has_mutation(MUT_NO_ARMOUR))
        result.push_back(armour_mut);

    if (player_res_poison(false, false, false, false) == 3)
        result.push_back({"", _innatemut("You are immune to poison.")});

    return result;
}

static vector<mutation_type> _get_ordered_mutations()
{
    vector<mutation_type> muts;

    // First add (non-removable) inborn abilities and demon powers.
    for (int i = 0; i < NUM_MUTATIONS; i++)
    {
        mutation_type mut = static_cast<mutation_type>(i);
        if (you.has_innate_mutation(mut))
            muts.push_back(mut);
    }

    // Now add removable mutations.
    for (int i = 0; i < NUM_MUTATIONS; i++)
    {
        mutation_type mut = static_cast<mutation_type>(i);
        if (you.get_base_mutation_level(mut, false, false, true) > 0
            && !you.has_innate_mutation(mut)
            && !you.has_temporary_mutation(mut))
        {
            muts.push_back(mut);
        }
    }

    //Finally, temporary mutations.
    for (int i = 0; i < NUM_MUTATIONS; i++)
    {
        mutation_type mut = static_cast<mutation_type>(i);
        if (you.has_temporary_mutation(mut))
            muts.push_back(mut);
    }

    return muts;
}

static vector<bane_type> _get_active_banes()
{
    vector<bane_type> banes;
    for (int i = 0; i < NUM_BANES; ++i)
        if (you.banes[i])
            banes.push_back(static_cast<bane_type>(i));

    return banes;
}

static vector<string> _get_mutations_descs(bool terse)
{
    vector<pair<string, string>> fakemuts = _get_fakemuts();
    vector<string> result;
    for (const auto& p : fakemuts)
    {
        const string& mut = terse ? p.first : p.second;
        if (!mut.empty() && mut != "--transformation--")
        {
            // TODO: Issue 32 Phase 2 — migrate _zh_mutation_name to T_()
            // Translate fakemut terse names for Chinese
            if (terse && Options.language == lang_t::ZH)
                result.push_back(_zh_mutation_name(mut.c_str()));
            else
                result.push_back(mut);
        }
    }

    for (mutation_type mut : _get_ordered_mutations())
    {
        result.push_back(terse ? _terse_mut_name(mut)
                               : mutation_desc(mut, -1, true,
                                               you.sacrifices[mut] != 0));
    }

    return result;
}

string terse_mutation_list()
{
    const vector<string> mutations = _get_mutations_descs(true);

    if (mutations.empty())
        return T_("no striking features");
    else
    {
        return comma_separated_line(mutations.begin(), mutations.end(),
                                     ", ", ", ");
    }
}

string describe_mutations(bool drop_title)
{
#ifdef DEBUG
#ifndef USE_TILE_LOCAL
    validate_mutations(!crawl_state.smallterm);
#else
    validate_mutations(true);
#endif
#endif
    string result;

    if (!drop_title)
    {
        result += "<white>";
        result += T_("Innate Abilities, Weirdness & Mutations");
        result += "</white>\n\n";
    }

    const vector<string> mutations = _get_mutations_descs(false);

    if (mutations.empty())
        result += T_("You are rather mundane.\n");
    else
        result += join_strings(mutations.begin(), mutations.end(), "\n");

    return result;
}

static bool _has_suppressed_muts()
{
    for (int i = 0; i < NUM_MUTATIONS; ++i)
    {
        mutation_type mut = static_cast<mutation_type>(i);
        if (!you.get_base_mutation_level(mut))
            continue;
        if (!mut_is_compatible(mut))
            return true;
    }
    return false;
}

static bool _has_transient_muts()
{
    for (int i = 0; i < NUM_MUTATIONS; ++i)
        if (you.has_temporary_mutation(static_cast<mutation_type>(i)))
            return true;
    return false;
}

static bool _fakemut_has_description(string fakemut_name)
{
    const string key = make_stringf("%s mutation", fakemut_name.c_str());
    string lookup = getLongDescription(key);

    return !lookup.empty();
}

enum mutation_entry_type
{
    MUT_ENTRY_MUTATION,
    MUT_ENTRY_FAKEMUT,
    MUT_ENTRY_TALISMAN,
    MUT_ENTRY_BANE,
};

class MutationMenu : public Menu
{
private:
    vector<pair<string, string>> fakemuts;
    vector<mutation_type> muts;
    vector<bane_type> banes;
    bool has_future_muts;
public:
    MutationMenu()
        : Menu(MF_SINGLESELECT | MF_ANYPRINTABLE | MF_ALLOW_FORMATTING
            | MF_ARROWS_SELECT),
          fakemuts(_get_fakemuts()),
          muts( _get_ordered_mutations()),
          banes(_get_active_banes())
    {
        set_highlighter(nullptr);
        set_title(new MenuEntry(
            T_("Innate Abilities, Weirdness & Mutations"),
            MEL_TITLE));
        menu_action = ACT_EXAMINE;
        update_muts();
        update_more();
    }

private:
    void update_muts()
    {
        menu_letter hotkey;
        for (auto &fakemut : fakemuts)
        {
            // Skip fakemuts that are terse-only.
            if (fakemut.second.empty())
                continue;

            MenuEntry* me;
            // Special-case the transformation fakemut to put an item popup
            // behind it, so the player can examine form details and artprops
            if (fakemut.first == "--transformation--"
                && ((you.form == you.default_form && you.active_talisman())
                    || you.form == transformation::flux))
            {
                me = new MenuEntry(fakemut.second, MEL_ITEM, MUT_ENTRY_TALISMAN, hotkey);
                ++hotkey;
            }
            // Add a full clickable entry if there's a long description for this
            // fakemut, and a non-clickable one otherwise.
            else if (_fakemut_has_description(fakemut.first))
            {
                me = new MenuEntry(fakemut.second, MEL_ITEM, MUT_ENTRY_FAKEMUT, hotkey);
                me->data = &fakemut.first;
                ++hotkey;
            }
            else
            {
                me = new MenuEntry(fakemut.second, MEL_ITEM, MUT_ENTRY_FAKEMUT, 0);
                me->indent_no_hotkeys = !muts.empty();
            }

            add_entry(me);
        }

        for (mutation_type &mut : muts)
        {
            const string desc = mutation_desc(mut, -1, true,
                                              you.sacrifices[mut] != 0);
            MenuEntry* me = new MenuEntry(desc, MEL_ITEM, MUT_ENTRY_MUTATION, hotkey);
            ++hotkey;
            me->data = &mut;
#ifdef USE_TILE
            const tileidx_t tile = get_mutation_tile(mut);
            if (tile != 0)
                me->add_tile(tile_def(tile + you.get_mutation_level(mut, false) - 1));
#endif
            add_entry(me);
        }

        const vector<level_up_mutation> &xl_muts = get_species_def(you.species).level_up_mutations;
        has_future_muts = false;
        if (!xl_muts.empty())
        {
            vector<pair<mutation_type, int>> gained_muts;
            for (auto& mut : get_species_def(you.species).level_up_mutations)
            {
                if (you.experience_level < mut.xp_level)
                {
                    // Tally how many levels of this mutation we will have by the
                    // time we gain this instance of it (so that mutations
                    // scheduled to be gotten progressively will name each step
                    // correctly).
                    gained_muts.emplace_back(mut.mut, mut.mut_level);
                    int mut_lv = 0;
                    for (auto& gained_mut : gained_muts)
                        if (gained_mut.first == mut.mut)
                            mut_lv += gained_mut.second;

                    string mut_desc = _future_mutation_description(mut.mut, mut_lv);
#ifndef USE_TILE
                    chop_string(mut_desc, crawl_view.termsz.x - 15, false);
#endif

                    const string desc = make_stringf("<darkgrey>[%s]</darkgrey> XL %d",
                                                        mut_desc.c_str(),
                                                        mut.xp_level);
                    MenuEntry* me = new MenuEntry(desc, MEL_ITEM, MUT_ENTRY_MUTATION, hotkey);
                    ++hotkey;
                    // XXX: Ugh...
                    me->data = (void*)&mut.mut;
                    add_entry(me);

                    has_future_muts = true;
                }
            }
        }

        for (bane_type &bane : banes)
        {
            const string desc = make_stringf("<lightmagenta>%s [%.1f]</lightmagenta>",
                bane_desc(bane).c_str(), (float)xl_to_remove_bane(bane) / 10.0f);

            MenuEntry* me = new MenuEntry(desc, MEL_ITEM, MUT_ENTRY_BANE, hotkey);
            ++hotkey;
            me->data = &bane;
            add_entry(me);
        }

        if (items.empty())
        {
            add_entry(new MenuEntry("You are rather mundane.",
                                    MEL_ITEM, 1, 0));
        }
    }

    void update_more()
    {
        string extra = "";
        // TODO: also handle suppressed fakemuts
        if (_has_suppressed_muts())
            extra += "<darkgrey>()</darkgrey>: Suppressed.\n";
        if (_has_transient_muts())
            extra += "<magenta>[]</magenta>: Transient mutations.\n";
        if (has_future_muts)
            extra += "<darkgrey>[]</darkgrey>: Gained at a future XL.\n";
        set_more(extra);
    }

    bool examine_index(int i) override
    {
        ASSERT(i >= 0 && i < static_cast<int>(items.size()));
        if (items[i]->data)
        {
            // XXX: Sinful hack: mutation entry type is encoded in the quantity
            //      field (which is otherwise unused)
            if (items[i]->quantity == MUT_ENTRY_MUTATION)
            {
                // XX don't use C casts
                const mutation_type mut = *((mutation_type*)(items[i]->data));
                describe_mutation(mut);
            }
            else if (items[i]->quantity == MUT_ENTRY_BANE)
            {
                const bane_type bane = *((bane_type*)(items[i]->data));
                describe_bane(bane);
            }
            else if (items[i]->quantity == MUT_ENTRY_FAKEMUT)
            {
                const string* mut = (string*)(items[i]->data);
                describe_info inf;
                inf.title = uppercase_first(*mut).c_str();

                const string key = make_stringf("%s mutation", mut->c_str());
                string lookup = getLongDescription(key);
                hint_replace_cmds(lookup);
                inf.body << lookup;
                show_description(inf);
            }
        }
        else if (items[i]->quantity == MUT_ENTRY_TALISMAN)
        {
            if (you.form == you.default_form && you.active_talisman())
                describe_item_popup(*you.active_talisman());
            else if (you.form == transformation::flux)
            {
                item_def bauble;
                bauble.base_type = OBJ_BAUBLES;
                bauble.sub_type = BAUBLE_FLUX;
                bauble.quantity = 1;
                describe_item_popup(bauble);
            }
        }

        return true;
    }
};

void display_mutations()
{
#ifdef DEBUG
    validate_mutations(true);
#endif

    MutationMenu mut_menu;
    mut_menu.show();
}

static int _calc_mutation_amusement_value(mutation_type which_mutation)
{
    int amusement = 12 * (11 - _get_mutation_def(which_mutation).weight);

    if (is_good_mutation(which_mutation))
        amusement /= 2;
    else if (is_bad_mutation(which_mutation))
        amusement *= 2;
    // currently is only ever one of these, but maybe that'll change?

    return amusement;
}

static bool _accept_mutation(mutation_type mutat, bool temp)
{
    if (!_is_valid_mutation(mutat))
        return false;

    if (!mut_is_compatible(mutat, true))
        return false;

    // Devolution gives out permanent badmuts, so we don't want to give it as
    // a temporary mut. Stat mutations are too boring to have a relevant effect
    // on this timescale, too.
    if (temp
        && (mutat == MUT_DEVOLUTION
            || mutat == MUT_WEAK
            || mutat == MUT_CLUMSY
            || mutat == MUT_DOPEY))
    {
        return false;
    }

    const mutation_def& mdef = _get_mutation_def(mutat);

    if (you.get_base_mutation_level(mutat) >= mdef.levels)
        return false;

    // don't let random good mutations cause stat 0. Note: various code paths,
    // including jiyva-specific muts, and innate muts, don't include this check!
    if (_mut_has_flag(mdef, mutflag::good) && mutation_causes_stat_zero(mutat))
        return false;

    return true;
}

static mutation_type _get_mut_with_flag(mutflag flag)
{
    const int tweight = lookup(total_weight, flag, 0);
    ASSERT(tweight);

    int cweight = random2(tweight);
    for (const mutation_def &mutdef : mut_data)
    {
        if (!_mut_has_flag(mutdef, flag))
            continue;

        cweight -= _mut_weight(mutdef, flag);
        if (cweight >= 0)
            continue;

        return mutdef.mutation;
    }

    die("Error while selecting mutations");
}

static mutation_type _get_random_slime_mutation()
{
    return _get_mut_with_flag(mutflag::jiyva);
}

bool is_slime_mutation(mutation_type mut)
{
    return _mut_has_flag(mut_data[mut_index[mut]], mutflag::jiyva);
}

bool is_makhleb_mark(mutation_type mut)
{
    return _mut_has_flag(mut_data[mut_index[mut]], mutflag::makhleb);
}

static mutation_type _get_random_mutation(mutation_type mutclass,
                                          mutation_permanence_class perm)
{
    mutflag mt;
    switch (mutclass)
    {
        case RANDOM_MUTATION:
            // maintain an arbitrary ratio of good to bad muts to allow easier
            // weight changes within categories - 60% good seems to be about
            // where things are right now
            mt = x_chance_in_y(3, 5) ? mutflag::good : mutflag::bad;
            break;
        case RANDOM_XOM_MUTATION:
            // similar to random mutation, but slightly less likely to be good!
            mt = coinflip() ? mutflag::good : mutflag::bad;
            break;
        case RANDOM_BAD_MUTATION:
        case RANDOM_CORRUPT_MUTATION:
            mt = mutflag::bad;
            break;
        case RANDOM_GOOD_MUTATION:
            mt = mutflag::good;
            break;
        default:
            die("invalid mutation class: %d", mutclass);
    }

    for (int attempt = 0; attempt < 100; ++attempt)
    {
        mutation_type mut = _get_mut_with_flag(mt);
        if (_accept_mutation(mut, perm == MUTCLASS_TEMPORARY))
            return mut;
    }

    return NUM_MUTATIONS;
}

/**
 * Does the player have a mutation that conflicts with the given mutation?
 *
 * @param mut           A mutation. (E.g. MUT_INHIBITED_REGENERATION, ...)
 * @param innate_only   Whether to only check innate mutations (from e.g. race)
 * @return              The level of the conflicting mutation.
 *                      E.g., if MUT_INHIBITED_REGENERATION is passed in and the
 *                      player has 2 levels of MUT_REGENERATION, 2 will be
 *                      returned.
 *
 *                      No guarantee is offered on ordering if there are
 *                      multiple conflicting mutations with different levels.
 */
int mut_check_conflict(mutation_type mut, bool innate_only)
{
    for (const mutation_conflict& conflict : mut_conflicts)
    {
        mutation_type confl_mut = conflict.get_conflict(mut);
        if (confl_mut == MUT_NON_MUTATION)
            continue;

        const int level = you.get_base_mutation_level(confl_mut, true, !innate_only, !innate_only);
        if (level)
            return level;
    }

    return 0;
}

static void _maybe_remove_equipment(mutation_type mut)
{
    vector<item_def*> to_remove = you.equipment.get_forced_removal_list();

    for (item_def* item : to_remove)
    {
        if (mut == MUT_MISSING_HAND)
        {
            mprf(T_("You can no longer %s %s!"),
                    item->base_type == OBJ_JEWELLERY ? "wear" : "hold",
                    item->name(DESC_YOUR).c_str());
        }
        else
        {
            if (item_is_melded(*item))
            {
                mprf(T_("%s is forcibly removed from your body%s!"),
                        item->name(DESC_YOUR).c_str(),
                        item->cursed() ? ", shattering the curse!" : "");
            }
            else
            {
                mprf(T_("%s%s falls off!"), item->name(DESC_YOUR).c_str(),
                        item->cursed() ? ", shattering the curse!" : "");
            }

            // A mutation made us not only lose an equipment slot
            // but actually removed a worn item: Funny!
            xom_is_stimulated(is_artefact(*item) ? 200 : 100);
        }

        unequip_item(*item, false);
    }

    // Update slot counts, even if no item was changed.
    you.equipment.update();
}

// Tries to give you the mutation by deleting a conflicting
// one, or clears out conflicting mutations if we should give
// you the mutation anyway.
// Return:
//  1 if we should stop processing (success);
//  0 if we should continue processing;
// -1 if we should stop processing (failure).
static int _handle_conflicting_mutations(mutation_type mutation,
                                         bool override,
                                         const string &reason,
                                         bool temp = false)
{
    // If we have one of the pair, delete all levels of the other,
    // and continue processing.
    for (const mutation_conflict& conflict : mut_conflicts)
    {
        const mutation_type confl_mut = conflict.get_conflict(mutation);
        if (confl_mut == MUT_NON_MUTATION || you.get_base_mutation_level(confl_mut) == 0)
            continue;

        const bool innate_only = you.get_base_mutation_level(confl_mut, true, false, false)
                                        == you.get_base_mutation_level(confl_mut);

        // We can never delete innate mutations this way, so if there are no
        // non-innate mutations (and we're not trying to apply to temporary
        // invertable mutation, which is allowed), immediately fail.
        if (innate_only && !conflict.is_inverse && !temp)
        {
            dprf("Delete mutation failed: %s conflicting with innate mutation %s.",
                    mutation_name(mutation), mutation_name(confl_mut));
            return -1;
        }

        // Check if at least one level of the conflicting mutation is temporary.
        const bool temp_b = you.has_temporary_mutation(confl_mut);

        // If these are fundamentally incompatible mutations, fail unless
        // this is a forced mutation. But if it is, delete all levels of
        // the conflicting mutation instead, and continue on.
        if (!conflict.is_inverse)
        {
            if (!override)
                return -1;
            else
            {
                while (_delete_single_mutation_level(confl_mut, reason, true));
                return 0;
            }
        }

        // For inverse mutations, delete one level of the conflicting
        // mutation and stop there.
        //
        // Temporary mutations can co-exist with things they would
        // ordinarily conflict with. But if both mutations are temporary,
        // mark the older one for deletion.
        if ((temp || temp_b) && !(temp && temp_b))
            return 0;       // Allow conflicting transient mutations.
        else
        {
            _delete_single_mutation_level(confl_mut, reason, true);
            return 1;       // Nothing more to do.
        }
    }

    return 0;
}

static equipment_slot _eq_type_for_mut(mutation_type mutat)
{
    if (!is_body_facet(mutat))
        return SLOT_UNUSED;
    for (const body_facet_def &facet : _body_facets)
        if (mutat == facet.mut)
            return facet.slot;
    return SLOT_UNUSED;
}

// Make Ashenzari suppress mutations that would shatter your cursed item.
static bool _ashenzari_blocks(mutation_type mutat)
{
    if (GOD_ASHENZARI != you.religion)
        return false;

    if (!is_body_facet(mutat))
        return false;

    // Temporarily give the player this mutation, then test if doing so would
    // remove a cursed item.
    you.mutation[mutat] += 1;

    item_def* cursed_item = nullptr;
    vector<item_def*> items = you.equipment.get_forced_removal_list();
    for (item_def* item : items)
    {
        if (item->cursed())
        {
            cursed_item = item;
            break;
        }
    }

    // Remember to remove it again!
    you.mutation[mutat] -= 1;

    if (!cursed_item)
        return false;

    const string msg = make_stringf(" prevents a mutation which would have shattered %s.",
                                    cursed_item->name(DESC_YOUR).c_str());
    simple_god_message(msg.c_str());
    return true;
}

/// Do you have an existing mutation in the same body slot? (E.g., gloves, helmet...)
static bool _body_facet_blocks(mutation_type mutat)
{
    const equipment_slot eq_type = _eq_type_for_mut(mutat);
    if (eq_type == SLOT_UNUSED)
        return false;

    for (const body_facet_def &facet : _body_facets)
    {
        if (eq_type == facet.slot
            && mutat != facet.mut
            && you.get_base_mutation_level(facet.mut))
        {
            return true;
        }
    }
    return false;
}

static bool _exoskeleton_incompatible(mutation_type mutat)
{
    // Coglins attack with and wear aux armour on their exoskeleton-limbs,
    // not their fleshy, mutation-prone hands. Disable mutations that would
    // make no sense in this scheme.
    switch (mutat)
    {
    case MUT_HOOVES:
    case MUT_CLAWS:
    case MUT_TALONS:
        return true;
    default:
        return false;
    }
}

// Is this mutation allowed to bypass normal suppression rules in dragon form?
static bool _draconian_dragon_form_exception(mutation_type mut)
{
    if (you.form == transformation::dragon)
    {
        if (mut == MUT_ARMOURED_TAIL)
            return true;

        monster_type drag = species::dragon_form(you.species);
        if (mut == MUT_SHOCK_RESISTANCE && drag == MONS_STORM_DRAGON)
            return true;
        if ((mut == MUT_ACIDIC_BITE || mut == MUT_ACID_RESISTANCE) && drag == MONS_ACID_DRAGON)
            return true;
        if (mut == MUT_STINGER && drag == MONS_SWAMP_DRAGON)
            return true;
        if (mut == MUT_STEAM_RESISTANCE && drag == MONS_STEAM_DRAGON)
            return true;
        if (mut == MUT_IRON_FUSED_SCALES && drag == MONS_IRON_DRAGON)
            return true;
    }

    return false;
}

/**
 * Is a given mutation compatible with the player's current (or base) state?
 *
 * This includes physiological conflicts with the player's species, as well as
 * mutations suppressed by forms or even current location (ie: Teleportitis
 * being inactive in the Abyss, or Nimble Swimmer only being active over water)
 *
 * @param mut           The mutation to check.
 * @param base_only     Whether to consider only the player's untransformed
 *                      state, without any other temporary effects.
 *
 * @return  Whether the given mutation is compatible.
 *
 *          (Mutations incompatible with the player's base form should never be
 *           given, while mutations merely incompatible with their current
 *           status should be suppressed.)
 */

bool mut_is_compatible(mutation_type mut, bool base_only)
{
    const mutation_def& def = _get_mutation_def(mut);

    // Suppress all general 'anatomy' mutations in most full-body forms (except
    // for allowing draconians to keep species mutations in dragon form).
    if (!base_only && _mut_has_flag(def, mutflag::anatomy) && form_changes_anatomy()
        && !_draconian_dragon_form_exception(mut))
    {
        return false;
    }
    // Likewise suppress 'substance' mutations in substance-changing forms, like
    // statue form.
    if (!base_only && _mut_has_flag(def, mutflag::substance) && form_changes_substance())
        return false;

    // Basic physiological conflicts (applies to some forms and also species)
    if (_mut_has_flag(def, mutflag::need_blood) && !you.has_blood(!base_only))
        return false;
    if (_mut_has_flag(def, mutflag::need_bones) && !you.has_bones(!base_only))
        return false;
    if (_mut_has_flag(def, mutflag::need_hands)
        && (you.has_mutation(MUT_TENTACLE_ARMS)
            || (!base_only && you.form == transformation::eel_hands)))
    {
        return false;
    }
    if (_mut_has_flag(def, mutflag::need_feet) && !player_has_feet(!base_only, false))
        return false;
    if (base_only && _mut_has_flag(def, mutflag::scales))
    {
        // No extra scales for demonspawn already scheduled to get a different kind.
        if (you.species == SP_DEMONSPAWN)
        {
            return any_of(begin(you.demonic_traits), end(you.demonic_traits),
                          [=](const player::demon_trait &t) {
                              return _mut_has_flag(t.mutation, mutflag::scales);});
        }

        // No extra scales for draconians.
        if (species::is_draconian(you.species))
            return true;
    }

    // Mutation-specific cases that do not depend on forms:
    if (base_only)
    {
        // Only species that already have tails can get this one. For merfolk it
        // would only work in the water, so skip it.
        if (mut == MUT_STINGER && !you.has_tail(false))
            return false;

        // Need tentacles to grow something on them.
        if (mut == MUT_TENTACLE_SPIKE && !you.has_innate_mutation(MUT_TENTACLE_ARMS))
            return false;

        // To get upgraded spit poison, you must have it innately
        if (mut == MUT_SPIT_POISON && !you.has_innate_mutation(MUT_SPIT_POISON))
            return false;

        // Only Draconians (and gargoyles) can get wings.
        if (mut == MUT_BIG_WINGS
                && !species::is_draconian(you.species) && you.species != SP_GARGOYLE)
        {
            return false;
        }

        // Only species that have innate tough skin can mutate more.
        if (mut == MUT_TOUGH_SKIN && !you.has_innate_mutation(MUT_TOUGH_SKIN))
            return false;

        // Only species that have innate fur can mutate more.
        if (mut == MUT_SHAGGY_FUR && !you.has_innate_mutation(MUT_SHAGGY_FUR))
            return false;

        // Formicids have stasis and so prevent mutations that would do nothing.
        if (mut == MUT_TELEPORTITIS && you.stasis())
            return false;

        if (mut == MUT_ACUTE_VISION && you.innate_sinv())
            return false;

        // Already immune.
        if (mut == MUT_POISON_RESISTANCE && you.is_nonliving(!base_only, !base_only))
            return false;

        // We can't use is_useless_skill() here, since species that can still wear
        // body armour can sacrifice armour skill with Ru.
        if ((mut == MUT_DEFORMED || mut == MUT_STURDY_FRAME)
                && species_apt(SK_ARMOUR) == UNUSABLE_SKILL)
        {
            return false;
        }

        // Mutations of the same slot conflict
        if (_body_facet_blocks(mut))
            return false;

        if (you.species == SP_COGLIN && _exoskeleton_incompatible(mut))
            return false;

        // All remaining conflicts concern temporary status only
        return true;
    }

    // Makhleb's marks are only active while worshipping (but you stay branded forever).
    if (_mut_has_flag(def, mutflag::makhleb) && !you_worship(GOD_MAKHLEB))
        return false;

    if (mut == MUT_TELEPORTITIS && (base_only ? you.stasis() : you.no_tele(false) || player_in_branch(BRANCH_ABYSS)))
        return false;

    if (mut == MUT_SPATIAL_ENTANGLEMENT && you.stasis())
        return false;

    if (mut == MUT_DEMONIC_GUARDIAN && you.allies_forbidden())
        return false;

    if (mut == MUT_TIME_WARPED_BLOOD && you_worship(GOD_CHEIBRIADOS))
        return false;

    if (mut == MUT_NIMBLE_SWIMMER && !feat_is_water(env.grid(you.pos())))
        return false;

    return true;
}

static const char* _stat_mut_desc(mutation_type mut, bool gain)
{
    stat_type stat = STAT_STR;
    bool positive = gain;
    switch (mut)
    {
    case MUT_WEAK:
        positive = !positive;
    case MUT_STRONG:
        stat = STAT_STR;
        break;

    case MUT_DOPEY:
        positive = !positive;
    case MUT_CLEVER:
        stat = STAT_INT;
        break;

    case MUT_CLUMSY:
        positive = !positive;
    case MUT_AGILE:
        stat = STAT_DEX;
        break;

    default:
        die("invalid stat mutation: %d", mut);
    }
    return stat_desc(stat, positive ? SD_INCREASE : SD_DECREASE);
}

/**
 * Do a resistance check for the given mutation permanence class.
 * Does not include divine intervention!
 *
 * @param mutclass The type of mutation that is checking resistance
 * @param beneficial Is the mutation beneficial?
 *
 * @return True if a mutation is successfully resisted, false otherwise.
**/
static bool _resist_mutation(mutation_permanence_class mutclass,
                             bool beneficial)
{
    if (you.get_mutation_level(MUT_MUTATION_RESISTANCE) == 3)
        return true;

    const int mut_resist_chance = mutclass == MUTCLASS_TEMPORARY ? 2 : 3;
    if (you.get_mutation_level(MUT_MUTATION_RESISTANCE)
        && !one_chance_in(mut_resist_chance))
    {
        return true;
    }

    // To be nice, beneficial mutations go through removable sources of rMut.
    if (you.rmut_from_item() && !beneficial
        && !one_chance_in(mut_resist_chance))
    {
        return true;
    }

    return false;
}

/*
 * Try to mutate the player, along with associated bookkeeping. This accepts mutation categories as well as particular mutations.
 *
 * In many cases this will produce only 1 level of mutation at a time, but it may mutate more than one level if the mutation category is corrupt.
 *
 * If the player is at the mutation cap, this may fail.
 *   1. If mutclass is innate, this will attempt to replace temporary and normal mutations (in that order) and will fail if this isn't possible (e.g. there are only innate levels).
 *   2. Otherwise, this will fail. This means that a temporary mutation can block a permanent mutation of the same type in some circumstances.
 *
 * If the mutation conflicts with an existing one it may fail. See `_handle_conflicting_mutations`.
 *
 * If the player is undead, this may drain max HP instead. Draining count as success.
 *
 * @param which_mutation    the mutation to use.
 * @param reason            the explanation for how the player got mutated.
 * @param failMsg           whether to do any messaging if this fails.
 * @param force_mutation    whether to override mutation protection and the like.
 * @param god_gift          is this a god gift? Entails overriding mutation resistance if not forced.
 * @param mutclass          is the mutation temporary, regular, or permanent (innate)? permanent entails force_mutation.
 *
 * @return whether the mutation succeeded.
 */
bool mutate(mutation_type which_mutation, const string &reason, bool failMsg,
            bool force_mutation, bool god_gift, bool beneficial,
            mutation_permanence_class mutclass)
{
    if (which_mutation == RANDOM_BAD_MUTATION
        && mutclass == MUTCLASS_NORMAL
        && crawl_state.disables[DIS_AFFLICTIONS])
    {
        return true; // no fallbacks
    }

    god_gift |= crawl_state.is_god_acting();

    if (mutclass == MUTCLASS_INNATE)
        force_mutation = true;

    mutation_type mutat = which_mutation;

    if (!force_mutation)
    {
        // God gifts override all sources of mutation resistance other
        // than divine protection.
        if (!god_gift && _resist_mutation(mutclass, beneficial))
        {
            if (failMsg)
                mprf(MSGCH_MUTATION, "你短暂地感到奇怪。");
            return false;
        }

        // Zin's protection.
        if (have_passive(passive_t::resist_mutation)
            && x_chance_in_y(you.piety(), piety_breakpoint(5)))
        {
            simple_god_message(" protects your body from mutation!");
            return false;
        }
    }

    // Undead bodies don't mutate, they fall apart. -- bwr
    if (!you.can_safely_mutate())
    {
        switch (mutclass)
        {
        case MUTCLASS_TEMPORARY:
            if (coinflip())
                return false;
            // fallthrough to normal mut
        case MUTCLASS_NORMAL:
            mprf(MSGCH_MUTATION, "你的身体腐烂了！");
            drain_player(30, false, true, true);
            return true;
        case MUTCLASS_INNATE:
            // You can't miss out on innate mutations just because you're
            // temporarily undead.
            break;
        default:
            die("bad fall through");
            return false;
        }
    }

    if (mutclass == MUTCLASS_NORMAL
        && (which_mutation == RANDOM_MUTATION
            || which_mutation == RANDOM_XOM_MUTATION)
        && x_chance_in_y(you.how_mutated(), 15))
    {
        // God gifts override mutation loss due to being heavily
        // mutated.
        if (!one_chance_in(3) && !god_gift && !force_mutation)
            return false;
        else
            return delete_mutation(RANDOM_MUTATION, reason, failMsg,
                                   force_mutation, false);
    }

    mutat = concretize_mut(which_mutation, mutclass);
    if (!_is_valid_mutation(mutat))
        return false;

    // [Cha] don't allow teleportitis in sprint
    if (mutat == MUT_TELEPORTITIS && crawl_state.game_is_sprint())
        return false;

    if (!mut_is_compatible(mutat, true))
        return false;

    if (mutclass != MUTCLASS_INNATE && _ashenzari_blocks(mutat))
        return false;

    const mutation_def& mdef = _get_mutation_def(mutat);

    bool gain_msg = true;

    if (mutclass == MUTCLASS_INNATE)
    {
        // are there any non-innate instances to replace?  Prioritize temporary mutations over normal.
        // Temporarily decrement the mutation value so it can be silently regained in the while loop below.
        if (you.mutation[mutat] > you.innate_mutation[mutat])
        {
            if (you.temp_mutation[mutat] > 0)
            {
                you.temp_mutation[mutat]--;
                you.attribute[ATTR_TEMP_MUTATIONS]--;
                if (you.attribute[ATTR_TEMP_MUTATIONS] == 0)
                    you.attribute[ATTR_TEMP_MUT_KILLS] = 0;
            }
            you.mutation[mutat]--;
            mprf(MSGCH_MUTATION, T_("Your %s mutation feels more permanent."),
                                  mutation_name(mutat));
            take_note(Note(NOTE_PERM_MUTATION, mutat,
                    you.get_base_mutation_level(mutat), reason.c_str()));
            gain_msg = false;
        }
    }
    if (you.mutation[mutat] >= mdef.levels)
        return false;

    // God gifts and forced mutations clear away conflicting mutations.
    int rc = _handle_conflicting_mutations(mutat, god_gift || force_mutation,
                                           reason,
                                           mutclass == MUTCLASS_TEMPORARY);
    if (rc == 1)
        return true;
    if (rc == -1)
        return false;

    ASSERT(rc == 0);

#ifdef USE_TILE_LOCAL
    const unsigned int old_talents = your_talents().size();
#endif

    const int levels = (which_mutation == RANDOM_CORRUPT_MUTATION
                       ? min(2, mdef.levels - you.get_base_mutation_level(mutat))
                       : 1);
    ASSERT(levels > 0); //TODO: is > too strong?

    int count = levels;

    while (count-- > 0)
    {
        // no fail condition past this point, so it is safe to do bookkeeping
        you.mutation[mutat]++;
        if (mutclass == MUTCLASS_TEMPORARY)
        {
            // do book-keeping for temporary mutations
            you.temp_mutation[mutat]++;
            you.attribute[ATTR_TEMP_MUTATIONS]++;
        }
        else if (mutclass == MUTCLASS_INNATE)
            you.innate_mutation[mutat]++;

        const int cur_base_level = you.get_base_mutation_level(mutat);

        // More than three messages, need to give them by hand.
        switch (mutat)
        {
        case MUT_STRONG: case MUT_AGILE:  case MUT_CLEVER:
        case MUT_WEAK:   case MUT_CLUMSY: case MUT_DOPEY:
            mprf(MSGCH_MUTATION, T_("You feel %s."), _stat_mut_desc(mutat, true));
            gain_msg = false;
            break;

        case MUT_LARGE_BONE_PLATES:
            {
                const string arms = pluralise(species::arm_name(you.species));
                mprf(MSGCH_MUTATION, "%s",
                     replace_all(mdef.gain[cur_base_level - 1], "arms",
                                 arms).c_str());
                gain_msg = false;
            }
            break;

        case MUT_MISSING_HAND:
            {
                // n.b. we cannot use the built in pluralisation, because at
                // this point the mut has already applied, and hand_name takes
                // it into account.
                const string hands = pluralise(you.hand_name(false));
                mprf(MSGCH_MUTATION, "%s",
                     replace_all(mdef.gain[cur_base_level - 1], "hands",
                                 hands).c_str());
                gain_msg = false;
            }
            break;

        case MUT_SPIT_POISON:
            // Breathe poison replaces spit poison (so it takes the slot).
            if (cur_base_level >= 2)
                for (int i = 0; i < 52; ++i)
                    if (you.ability_letter_table[i] == ABIL_SPIT_POISON)
                        you.ability_letter_table[i] = ABIL_BREATHE_POISON;
            break;

        default:
            break;
        }

        // For all those scale mutations.
        you.redraw_armour_class = true;

        notify_stat_change();

        if (gain_msg)
            mprf(MSGCH_MUTATION, "%s", mdef.gain[cur_base_level - 1]);

        // Do post-mutation effects.
        switch (mutat)
        {
        case MUT_FRAIL:
        case MUT_ROBUST:
        case MUT_RUGGED_BROWN_SCALES:
            calc_hp();
            break;

        case MUT_LOW_MAGIC:
        case MUT_HIGH_MAGIC:
            calc_mp();
            break;

        case MUT_PASSIVE_MAPPING:
            add_daction(DACT_REAUTOMAP);
            break;

        case MUT_ACUTE_VISION:
            // We might have to turn autopickup back on again.
            autotoggle_autopickup(false);
            break;

        case MUT_NIGHTSTALKER:
            update_vision_range();
            break;

        case MUT_BIG_WINGS:
#ifdef USE_TILE
            init_player_doll();
#endif
            break;

        case MUT_SILENCE_AURA:
        case MUT_FOUL_SHADOW:
            invalidate_agrid(true);
            break;

        case MUT_EVOLUTION:
        case MUT_DEVOLUTION:
            if (cur_base_level == 1)
            {
                you.props[EVOLUTION_MUTS_KEY] = 0;
                set_evolution_mut_xp(mutat == MUT_DEVOLUTION);
            }
            break;

        default:
            break;
        }

        _maybe_remove_equipment(mutat);
        ash_check_bondage();

        xom_is_stimulated(_calc_mutation_amusement_value(mutat));

        if (mutclass != MUTCLASS_TEMPORARY)
        {
            take_note(Note(NOTE_GET_MUTATION, mutat, cur_base_level,
                           reason.c_str()));
        }
        else
        {
            // only do this once regardless of how many levels got added
            you.attribute[ATTR_TEMP_MUT_KILLS] =
                max(you.attribute[ATTR_TEMP_MUT_KILLS], random_range(4, 7));
        }

        if (you.hp <= 0)
        {
            ouch(0, KILLED_BY_FRAILTY, MID_NOBODY,
                 make_stringf("gaining the %s mutation",
                              mutation_name(mutat)).c_str());
        }
    }

#ifdef USE_TILE_LOCAL
    if (your_talents().size() != old_talents)
    {
        tiles.layout_statcol();
        redraw_screen();
        update_screen();
    }
#endif
#ifdef DEBUG
    if (mutclass != MUTCLASS_INNATE) // taken care of in perma_mutate. Skipping this here avoids validation issues in doing repairs.
        validate_mutations(false);
#endif
    return true;
}

/**
 * If the given mutation is a 'random' type (e.g. RANDOM_GOOD_MUTATION),
 * turn it into a specific appropriate mut (e.g. MUT_HORNS). Otherwise, return
 * the given mut as-is.
 */
mutation_type concretize_mut(mutation_type mut,
                             mutation_permanence_class mutclass)
{
    switch (mut)
    {
    case RANDOM_MUTATION:
    case RANDOM_GOOD_MUTATION:
    case RANDOM_BAD_MUTATION:
    case RANDOM_CORRUPT_MUTATION:
    case RANDOM_XOM_MUTATION:
        return _get_random_mutation(mut, mutclass);
    case RANDOM_SLIME_MUTATION:
        return _get_random_slime_mutation();
    default:
        return mut;
    }
}

/**
 * Delete a single mutation level of fixed type `mutat`.
 * If `transient` is set, allow deleting temporary mutations, and prioritize them.
 * Note that if `transient` is true and there are no temporary mutations, this can delete non-temp mutations.
 * If `transient` is false, and there are only temp mutations, this will fail; otherwise it will delete a non-temp mutation.
 *
 * @mutat     the mutation to delete
 * @reason    why is it being deleted
 * @transient whether to allow (and prioritize) deletion of temporary mutations
 *
 * @return whether a mutation was deleted.
 */
bool _delete_single_mutation_level(mutation_type mutat,
                                   const string &reason,
                                   bool transient)
{
    // are there some non-innate mutations to delete?
    if (you.get_base_mutation_level(mutat, false, true, true) == 0)
        return false;

    bool was_transient = false;
    if (you.has_temporary_mutation(mutat))
    {
        if (transient)
            was_transient = true;
        else if (you.get_base_mutation_level(mutat, false, false, true) == 0) // there are only temporary mutations to delete
            return false;

        // fall through: there is a non-temporary mutation level that can be deleted.
    }

    const mutation_def& mdef = _get_mutation_def(mutat);

    bool lose_msg = true;

    you.mutation[mutat]--;

    switch (mutat)
    {
    case MUT_STRONG: case MUT_AGILE:  case MUT_CLEVER:
    case MUT_WEAK:   case MUT_CLUMSY: case MUT_DOPEY:
        mprf(MSGCH_MUTATION, T_("You feel %s."), _stat_mut_desc(mutat, false));
        lose_msg = false;
        break;

    case MUT_SPIT_POISON:
        // Breathe poison replaces spit poison (so it takes the slot).
        if (you.mutation[mutat] < 2)
            for (int i = 0; i < 52; ++i)
                if (you.ability_letter_table[i] == ABIL_SPIT_POISON)
                    you.ability_letter_table[i] = ABIL_BREATHE_POISON;
        break;

    case MUT_NIGHTSTALKER:
        update_vision_range();
        break;

    case MUT_BIG_WINGS:
        land_player();
#ifdef USE_TILE
        init_player_doll();
#endif
        break;

    case MUT_HORNS:
    case MUT_ANTENNAE:
    case MUT_BEAK:
    case MUT_CLAWS:
    case MUT_HOOVES:
    case MUT_TALONS:
        // Recheck Ashenzari bondage in case our available slots changed.
        ash_check_bondage();
        break;

    case MUT_SILENCE_AURA:
    case MUT_FOUL_SHADOW:
        invalidate_agrid(true);
        break;

    case MUT_EVOLUTION:
    case MUT_DEVOLUTION:
        if (!you.mutation[mutat])
            you.props[EVOLUTION_MUTS_KEY] = 0;
        break;

    default:
        break;
    }

    // For all those scale mutations.
    you.redraw_armour_class = true;

    notify_stat_change();

    you.equipment.update();

    if (lose_msg)
        mprf(MSGCH_MUTATION, "%s", mdef.lose[you.mutation[mutat]]);

    // Do post-mutation effects.
    if (mutat == MUT_FRAIL || mutat == MUT_ROBUST
        || mutat == MUT_RUGGED_BROWN_SCALES)
    {
        calc_hp();
    }
    if (mutat == MUT_LOW_MAGIC || mutat == MUT_HIGH_MAGIC)
        calc_mp();

    if (was_transient)
    {
        --you.temp_mutation[mutat];
        --you.attribute[ATTR_TEMP_MUTATIONS];
    }
    else
        take_note(Note(NOTE_LOSE_MUTATION, mutat, you.mutation[mutat], reason));

    if (you.hp <= 0)
    {
        ouch(0, KILLED_BY_FRAILTY, MID_NOBODY,
             make_stringf("losing the %s mutation", mutation_name(mutat)).c_str());
    }

    return true;
}

/// Returns the mutflag corresponding to a given class of random mutations, or 0.
static mutflag _mutflag_for_random_type(mutation_type mut_type)
{
    switch (mut_type)
    {
    case RANDOM_GOOD_MUTATION:
        return mutflag::good;
    case RANDOM_BAD_MUTATION:
    case RANDOM_CORRUPT_MUTATION:
        return mutflag::bad;
    case RANDOM_SLIME_MUTATION:
        return mutflag::jiyva;
    case RANDOM_MUTATION:
    case RANDOM_XOM_MUTATION:
    default:
        return (mutflag)0;
    }
}

/**
 * Given a type of 'random mutation' (eg RANDOM_XOM_MUTATION), return a mutation of that type that
 * we can delete from the player, or else NUM_MUTATIONS.
 */
static mutation_type _concretize_mut_deletion(mutation_type mut_type)
{
    switch (mut_type)
    {
        case RANDOM_MUTATION:
        case RANDOM_GOOD_MUTATION:
        case RANDOM_BAD_MUTATION:
        case RANDOM_CORRUPT_MUTATION:
        case RANDOM_XOM_MUTATION:
        case RANDOM_SLIME_MUTATION:
            break;
        default:
            return mut_type;
    }

    const mutflag mf = _mutflag_for_random_type(mut_type);
    int seen = 0;
    mutation_type chosen = NUM_MUTATIONS;
    for (const mutation_def &mutdef : mut_data)
    {
        if (mf != (mutflag)0 && !_mut_has_flag(mutdef, mf))
            continue;
        // Check whether we have a non-innate, permanent level of this mut
        if (you.get_base_mutation_level(mutdef.mutation, false, false) == 0)
            continue;

        ++seen;
        if (one_chance_in(seen))
            chosen = mutdef.mutation;
    }
    return chosen;
}

/*
 * Delete a mutation level, accepting random mutation types and checking mutation resistance.
 * This will not delete temporary or innate mutations.
 *
 * @param which_mutation    a mutation, including random
 * @param reason            the reason for deletion
 * @param failMsg           whether to message the player on failure
 * @param force_mutation    whether to try to override mut resistance & undeadness
 * @param god_gift          is the mutation a god gift & thus ignores mut resistance?
 * @return true iff a mutation was deleted.
 */
bool delete_mutation(mutation_type which_mutation, const string &reason,
                     bool failMsg,
                     bool force_mutation, bool god_gift)
{
    god_gift |= crawl_state.is_god_acting();

    if (!force_mutation)
    {
        if (!god_gift)
        {
            if (you.get_mutation_level(MUT_MUTATION_RESISTANCE) > 1
                && (you.get_mutation_level(MUT_MUTATION_RESISTANCE) == 3
                    || coinflip()))
            {
                if (failMsg)
                    mprf(MSGCH_MUTATION, "你短暂地感到相当奇怪。");
                return false;
            }
        }

        if (!you.can_safely_mutate())
            return false;
    }

    const mutation_type mutat = _concretize_mut_deletion(which_mutation);
    if (mutat == NUM_MUTATIONS)
        return false;
    return _delete_single_mutation_level(mutat, reason, false); // won't delete temp mutations
}

/*
 * Delete all (non-innate) mutations.
 *
 * If you really need to delete innate mutations as well, have a look at `change_species_to` in species.cc.
 * Changing species to human, for example, is a safe way to clear innate mutations entirely. For a
 * demonspawn, you could also use wizmode code to set the level to 1.
 *
 * @return  Whether the function found mutations to delete.
 */
bool delete_all_mutations(const string &reason)
{
    bool found = false;
    for (int i = 0; i < NUM_MUTATIONS; ++i)
    {
        while (_delete_single_mutation_level(static_cast<mutation_type>(i), reason, true))
            found = true;
    }
    ASSERT(you.attribute[ATTR_TEMP_MUTATIONS] == 0);
    ASSERT(you.how_mutated(true, false, false, true) == 0);
    you.attribute[ATTR_TEMP_MUT_KILLS] = 0;

    return found;
}

/*
 * Delete all temporary mutations.
 *
 * @return  Whether the function found mutations to delete.
 */
bool delete_all_temp_mutations(const string &reason)
{
    bool found = false;
    for (int i = 0; i < NUM_MUTATIONS; ++i)
    {
        while (you.has_temporary_mutation(static_cast<mutation_type>(i)))
            if (_delete_single_mutation_level(static_cast<mutation_type>(i), reason, true))
                found = true;
    }
    // the rest of the bookkeeping is handled in _delete_single_mutation_level
    you.attribute[ATTR_TEMP_MUT_KILLS] = 0;
    return found;
}

/*
 * Delete a single level of a random temporary mutation.
 * This function does not itself do XP-related bookkeeping; see `temp_mutation_wanes()`.
 *
 * @return          Whether the function found a mutation to delete.
 */
bool delete_temp_mutation()
{
    if (you.attribute[ATTR_TEMP_MUTATIONS] > 0)
    {
        mutation_type mutat = NUM_MUTATIONS;

        int count = 0;
        for (int i = 0; i < NUM_MUTATIONS; i++)
            if (you.has_temporary_mutation(static_cast<mutation_type>(i)) && one_chance_in(++count))
                mutat = static_cast<mutation_type>(i);

#if TAG_MAJOR_VERSION == 34
        // We had a brief period (between 0.14-a0-1589-g48c4fed and
        // 0.14-a0-1604-g40af2d8) where we corrupted attributes in transferred
        // games.
        if (mutat == NUM_MUTATIONS)
        {
            mprf(MSGCH_ERROR, "未发现临时变异，正在清除。");
            you.attribute[ATTR_TEMP_MUTATIONS] = 0;
            return false;
        }
#else
        ASSERTM(mutat != NUM_MUTATIONS, "Found no temp mutations, expected %d",
                                        you.attribute[ATTR_TEMP_MUTATIONS]);
#endif

        if (_delete_single_mutation_level(mutat, "temp mutation expiry", true))
            return true;
    }

    return false;
}

/// Attempt to look up a description of this mutation in the database.
/// Not to be confused with mutation_desc().
string get_mutation_desc(mutation_type mut)
{
    const char* const name = mutation_name(mut);
    const string key = make_stringf("%s mutation", name);
    string lookup = getLongDescription(key);
    hint_replace_cmds(lookup);

    ostringstream desc;
    desc << lookup;
    if (lookup.empty()) // Nothing found?
        desc << mutation_desc(mut, -1, false) << "\n";

    desc << mut_aux_attack_desc(mut);

    string mut_tags = get_mutation_tags(mut);
    if (!mut_tags.empty())
    {
        mut_tags = "Category: " + mut_tags;
        const int spacing = 80 - formatted_string::parse_string(mut_tags).width();
        desc << "\n" << string(spacing, ' ') << mut_tags;
    }

    // TODO: consider adding other fun facts here
        // _get_mutation_def(mut).form_based
        // type of mutation (species, etc)
        // if we tracked it: source (per level, I guess?)
        // gain/loss messages (to clarify to players when they get a
        //                     confusing message)

    const string quote = getQuoteString(key);
    if (!quote.empty())
        desc << "\n_________________\n\n<darkgrey>" << quote << "</darkgrey>";
    return desc.str();
}

static void _add_mut_tag(vector<string>& tags, string str, bool disabled)
{
    const string colour = disabled ? "red" : "darkgrey";
    tags.push_back(make_stringf("<%s>%s</%s>", colour.c_str(), str.c_str(), colour.c_str()));
}

string get_mutation_tags(mutation_type mut)
{
    vector<string> tags;
    const mutation_def& def = _get_mutation_def(mut);

    const bool disabled = you.has_mutation(mut, false) && !mut_is_compatible(mut);

    if (_mut_has_flag(def, mutflag::anatomy))
    {
        _add_mut_tag(tags, "Anatomy", disabled && form_changes_anatomy()
                                               && !_draconian_dragon_form_exception(mut));
    }
    if (_mut_has_flag(def, mutflag::substance))
        _add_mut_tag(tags, "Substance", disabled && form_changes_substance());
    if (_mut_has_flag(def, mutflag::need_blood))
        _add_mut_tag(tags, "Blood", disabled && !you.has_blood());
    if (_mut_has_flag(def, mutflag::need_bones))
        _add_mut_tag(tags, "Bones", disabled && !you.has_bones());
    if (_mut_has_flag(def, mutflag::need_hands))
        _add_mut_tag(tags, "Hands", disabled && you.form == transformation::eel_hands);

    if (tags.empty())
        return "";

    return make_stringf("[%s]", comma_separated_line(tags.begin(), tags.end(), ", ").c_str());
}

// TODO: Issue 32 Phase 2 — migrate to T_()
// Translate mutation short_desc for Chinese
static const char* _zh_mutation_name(const char* en)
{
    if (Options.language != lang_t::ZH || !en || !en[0])
        return en;

    static const map<string, const char*> zh_names = {
        { "+LOS", "+视野" }, { "Cocytus destruction", "科塞特斯毁灭" },
        { "Dis destruction", "迪斯毁灭" }, { "East Wind's embodiment", "东风化身" },
        { "Gehenna destruction", "基希纳毁灭" }, { "HP casting", "生命施法" },
        { "MP-powered wands", "魔杖消耗魔力" }, { "Mark of Annihilation", "湮灭印记" },
        { "Mark of Atrocity", "暴行印记" }, { "Mark of Carnage", "杀戮印记" },
        { "Mark of Execution", "处决印记" }, { "Mark of Haemoclasm", "血破印记" },
        { "Mark of the Celebrant", "颂礼者印记" }, { "Mark of the Fanatic", "狂热者印记" },
        { "Mark of the Legion", "军团印记" }, { "Mark of the Tyrant", "暴君印记" },
        { "North Wind's embodiment", "北风化身" }, { "South Wind's embodiment", "南风化身" },
        { "Tartarus destruction", "塔耳塔洛斯毁灭" }, { "West Wind's embodiment", "西风化身" },
        { "accursed", "被诅咒" }, { "acid resistance", "酸蚀抗性" },
        { "acidic bite", "酸蚀咬击" }, { "acrobatic", "特技" }, { "agile", "敏捷" },
        { "antennae", "触角" }, { "antimagic bite", "禁魔咬击" },
        { "armoured tail", "装甲尾巴" }, { "artefact enchanting", "神器附魔" },
        { "augmentation", "增强" }, { "aura of silence", "沉默光环" },
        { "beak", "喙" }, { "bedevilling", "纠缠" }, { "big brain", "大型大脑" },
        { "big wings", "大翅膀" }, { "black mark", "黑色印记" },
        { "booming voice", "洪亮嗓音" }, { "camouflage", "伪装" }, { "clarity", "清晰" },
        { "claws", "爪" }, { "clever", "聪明" }, { "clumsy", "笨拙" },
        { "cold resistance", "寒冷抗性" }, { "cold vulnerability", "寒冷弱点" },
        { "cold-blooded", "冷血" }, { "condensation shield", "凝结护盾" },
        { "contamination susceptible", "易受污染" }, { "corrupting presence", "腐败存在" },
        { "cowardly", "懦弱" }, { "deformed body", "变形身体" }, { "demonic guardian", "恶魔守护者" },
        { "demonic magic", "恶魔魔法" }, { "demonic touch", "恶魔之触" },
        { "demonic willpower", "恶魔意志" }, { "devolution", "退化" }, { "devour on kill", "击杀吞噬" },
        { "disrupted magic", "干扰魔法" }, { "distributed training", "分散训练" },
        { "divine attributes", "神圣属性" }, { "dopey", "迟钝" },
        { "double potion healing", "双倍药水治疗" }, { "drunken brawling", "醉拳" },
        { "efficient magic", "高效魔法" }, { "electricity resistance", "电击抗性" },
        { "electricity vulnerability", "电击弱点" }, { "ephemeral shield", "短暂护盾" },
        { "evasive flight", "闪避飞行" }, { "evolution", "进化" },
        { "explore regen", "探索再生" }, { "extra vitality", "额外活力" },
        { "eyeballs", "眼球" }, { "faith", "信仰" }, { "fangs", "獠牙" },
        { "feed off suffering", "以痛苦为食" }, { "fire resistance", "火焰抗性" },
        { "flame cloud immunity", "火焰云免疫" }, { "float", "漂浮" },
        { "forlorn", "凄凉" }, { "formless", "无形" }, { "foul shadow", "污秽之影" },
        { "foul stench", "恶臭" }, { "four strong arms", "四条强壮手臂" },
        { "frail", "脆弱" }, { "freezing cloud immunity", "冰冻云免疫" },
        { "frog-like legs", "蛙腿" }, { "gelatinous body", "凝胶身体" },
        { "hated by all", "被所有生物憎恨" }, { "heat vulnerability", "炎热弱点" },
        { "high MP", "高魔力" }, { "hooves", "蹄" }, { "horns", "角" },
        { "hurl damnation", "投掷诅咒" }, { "icemail", "冰甲" },
        { "icy blue scales", "冰蓝鳞片" }, { "ignite blood", "点燃血液" },
        { "in touch with death", "与死亡接触" }, { "inability to train armour", "无法训练护甲" },
        { "inability to train dodging", "无法训练闪避" }, { "inability to use devices", "无法使用装置" },
        { "inhibited regeneration", "再生抑制" }, { "initially attractive", "初始吸引力" },
        { "innate caster", "天生施法者" }, { "inviolate magic", "不可侵犯魔法" },
        { "iridescent scales", "虹彩鳞片" }, { "iron-fused scales", "铁融鳞片" },
        { "jelly absorbing missiles", "果冻吸收飞弹" }, { "jelly sensing items", "果冻感知物品" },
        { "large bone plates", "大型骨板" }, { "low MP", "低魔力" },
        { "magic link", "魔力链接" }, { "magic regeneration", "魔力再生" },
        { "magic shield", "魔法护盾" }, { "meek", "懦弱" }, { "mertail", "人鱼尾" },
        { "missing a hand", "缺失一只手" }, { "missing an eye", "缺失一只眼" },
        { "molten scales", "熔岩鳞片" }, { "multi-lived", "多条命" },
        { "mutation resistance", "变异抗性" }, { "naga tail", "纳迦尾巴" },
        { "negative energy resistance", "负能量抗性" }, { "nightstalker", "夜行者" },
        { "nimble swimmer", "敏捷游泳者" }, { "no air magic", "无法使用空气魔法" },
        { "no alchemy magic", "无法使用炼金魔法" }, { "no armour", "无法穿甲" },
        { "no conjurations magic", "无法使用咒法魔法" }, { "no earth magic", "无法使用大地魔法" },
        { "no fire magic", "无法使用火焰魔法" }, { "no forgecraft magic", "无法使用锻造魔法" },
        { "no forms", "无法变形" }, { "no hexes magic", "无法使用诅咒魔法" },
        { "no ice magic", "无法使用寒冰魔法" }, { "no jewellery", "无法佩戴珠宝" },
        { "no necromancy magic", "无法使用死灵魔法" }, { "no potion heal", "无法用药水治疗" },
        { "no potions", "无法饮用药水" }, { "no regeneration", "无法再生" },
        { "no stealth", "无法潜行" }, { "no summoning magic", "无法使用召唤魔法" },
        { "no translocations magic", "无法使用位移魔法" }, { "no weapons or thrown items", "无法使用武器或投掷物" },
        { "off-hand wielding", "副手持有" }, { "ooze flood", "软泥洪流" },
        { "otherworldly", "异界" }, { "passive freeze", "被动冻结" },
        { "persistent drain", "持续虚弱" }, { "poison resistance", "毒素抗性" },
        { "poor constitution", "体质虚弱" }, { "potion fungus", "药水真菌" },
        { "powered by death", "死亡赋能" }, { "powered by pain", "痛苦赋能" },
        { "pseudopods", "伪足" }, { "reduced AC", "降低防御" }, { "reduced EV", "降低闪避" },
        { "regeneration", "再生" }, { "renounce potions", "放弃药水" },
        { "renounce scrolls", "放弃卷轴" }, { "repulsion field", "排斥场" },
        { "retaliatory headbutt", "报复性头槌" }, { "robust", "强健" },
        { "rugged brown scales", "粗糙棕鳞" }, { "runic magic", "符文魔法" },
        { "sanguine armour", "血之护甲" }, { "screaming", "尖叫" },
        { "see invisible", "看破隐形" }, { "sense surroundings", "感知环境" },
        { "shaggy fur", "蓬松毛发" }, { "sharp scales", "锋利鳞片" },
        { "slime shroud", "黏液护罩" }, { "slimy green scales", "黏滑绿鳞" },
        { "slow wielding", "缓慢持武" }, { "slowness", "缓慢" },
        { "spark swarm", "火花群" }, { "spatial entanglement", "空间纠缠" },
        { "speed", "速度" }, { "spiny", "尖刺" }, { "spit poison", "喷吐毒素" },
        { "spiteful blood", "怨恨之血" }, { "stampede", "奔踏" },
        { "stealthy paws", "潜行爪垫" }, { "steam resistance", "蒸汽抗性" },
        { "stinger", "毒刺" }, { "stone body", "石质身体" }, { "strong", "强壮" },
        { "strong-willed", "坚强意志" }, { "sturdy frame", "健壮体格" },
        { "subdued magic", "压制魔法" }, { "talons", "利爪" },
        { "teleportitis", "传送症" }, { "temperature sensitive", "温度敏感" },
        { "tendrils", "卷须" }, { "tentacle spike", "触手尖刺" },
        { "tentacles", "触手" }, { "thin metallic scales", "薄金属鳞片" },
        { "thin skeletal structure", "薄骨骼结构" }, { "time-warped blood", "时间扭曲之血" },
        { "torment resistance", "折磨抗性" }, { "tough skin", "坚韧皮肤" },
        { "translucent skin", "半透明皮肤" }, { "treasure sense", "宝物感知" },
        { "trickster", "戏法者" }, { "unskilled", "无技能" },
        { "warmup strikes", "预热打击" }, { "weak", "虚弱" },
        { "weak-willed", "意志薄弱" }, { "weakness stinger", "虚弱毒刺" },
        { "wild magic", "狂野魔法" }, { "word of chaos", "混沌之语" },
        { "yellow scales", "黄色鳞片" },
        // Fakemut terse names (form, divine, species)
        { "(cold-blooded)", "（冷血）" }, { "AC +", "防御 +" },
        { "blade armour", "刃甲" }, { "boosted hp", "生命提升" },
        { "flying", "飞行" }, { "golden breath", "金龙吐息" },
        { "no casting", "无法施法" }, { "no large weapons", "无法使用大型武器" },
        { "reduced essence", "生命精华减少" }, { "reduced hp", "生命减少" },
        { "size adjective", "体型" }, { "unfitting armour", "不合身护甲" },
        { "walk on water", "水上行走" },
    };
    auto it = zh_names.find(en);
    return it != zh_names.end() ? it->second : en;
}

const char* mutation_name(mutation_type mut, bool allow_category)
{
    const char* en;
    if (allow_category && mut >= CATEGORY_MUTATIONS && mut < MUT_NON_MUTATION)
        en = _get_category_mutation_def(mut).short_desc;
    // note -- this can produce crashes if fed invalid mutations, e.g. if allow_category is false and mut is a category mutation
    else if (!_is_valid_mutation(mut))
        return nullptr;
    else
        en = _get_mutation_def(mut).short_desc;

    return _zh_mutation_name(en);
}

const char* category_mutation_name(mutation_type mut)
{
    if (mut < CATEGORY_MUTATIONS || mut >= MUT_NON_MUTATION)
        return nullptr;
    return _get_category_mutation_def(mut).short_desc;
}

/*
 * Given some name, return a mutation type. Tries to match the short description as found in `mutation-data.h`.
 * If `partial_matches` is set, it will fill the vector with any partial matches it finds. If there is exactly one,
 * will return this mutation, otherwise, will fail.
 *
 * @param allow_category    whether to include category mutation types (e.g. RANDOM_GOOD)
 * @param partial_matches   an optional pointer to a vector, in case the consumer wants to do something
 *                          with the partial match results (e.g. show them to the user). If this is `nullptr`,
 *                          will accept only exact matches.
 *
 * @return the mutation type if successful, otherwise NUM_MUTATIONS if it can't find a single match.
 */
mutation_type mutation_from_name(string name, bool allow_category, vector<mutation_type> *partial_matches)
{
    mutation_type mutat = NUM_MUTATIONS;

    string spec = lowercase_string(name);

    if (allow_category)
    {
        for (int i = CATEGORY_MUTATIONS; i < MUT_NON_MUTATION; ++i)
        {
            mutation_type mut = static_cast<mutation_type>(i);
            const char* mut_name_c = category_mutation_name(mut);
            if (!mut_name_c)
                continue;
            const string mut_name = lowercase_string(mut_name_c);

            if (spec == mut_name)
                return mut; // note, won't fully populate partial_matches

            if (partial_matches && strstr(mut_name.c_str(), spec.c_str()))
                partial_matches->push_back(mut);
        }
    }

    for (int i = 0; i < NUM_MUTATIONS; ++i)
    {
        mutation_type mut = static_cast<mutation_type>(i);
        const char *mut_name_c = mutation_name(mut);
        if (!mut_name_c)
            continue;
        const string mut_name = lowercase_string(mut_name_c);

        if (spec == mut_name)
        {
            mutat = mut;
            break;
        }

        // Also match against English short_desc for .des file compatibility
        if (_is_valid_mutation(mut))
        {
            const char *en_name = _get_mutation_def(mut).short_desc;
            if (en_name && spec == lowercase_string(en_name))
            {
                mutat = mut;
                break;
            }
            if (partial_matches && en_name
                && strstr(lowercase_string(en_name).c_str(), spec.c_str()))
            {
                partial_matches->push_back(mut);
            }
        }

        if (partial_matches && strstr(mut_name.c_str(), spec.c_str()))
            partial_matches->push_back(mut);
    }

    // If only one matching mutation, use that.
    if (partial_matches && mutat == NUM_MUTATIONS && partial_matches->size() == 1)
        mutat = (*partial_matches)[0];
    return mutat;
}

/**
 * A summary of what the next level of a mutation does.
 *
 * @param mut   The mutation_type in question; e.g. MUT_FRAIL.
 * @return      The mutation's description, helpfully trimmed.
 *              e.g. "you are frail (-10% HP)".
 */
string mut_upgrade_summary(mutation_type mut)
{
    if (!_is_valid_mutation(mut))
        return "";

    string mut_desc =
        lowercase_first(mutation_desc(mut, you.mutation[mut] + 1));
    strip_suffix(mut_desc, ".");
    return mut_desc;
}

int mutation_max_levels(mutation_type mut)
{
    if (!_is_valid_mutation(mut))
        return 0;

    return _get_mutation_def(mut).levels;
}

/// Return a string describing the mutation.
/// If colour is true, also add the colour annotation.
/// Not to be confused with get_mutation_desc().
// TODO: Issue 32 Phase 2 — migrate to T_()
// Translate mutation have[] long descriptions for Chinese
static const char* _zh_mutation_desc(const string& en)
{
    if (Options.language != lang_t::ZH || en.empty())
        return nullptr;

    static const map<string, const char*> zh_names = {
        { "A demonic guardian rushes to your aid.", "一个恶魔守护者冲来援助你。" },
        { "A fragile, slimy shroud covers you, deflecting attacks.", "一层脆弱的黏液护罩覆盖着你，偏转攻击。" },
        { "A frigid envelope surrounds you and freezes all who hurt you.", "一层寒气包裹环绕着你，冻结所有伤害你的人。" },
        { "A meltable icy envelope protects you from harm. (AC +", "一层可融化的冰封包裹保护你免受伤害。（防御+" },
        { "A meltable shield of frost defends you. (SH +", "一层可融化的冰霜护盾保护你。（盾挡+" },
        { "A powerful demonic guardian rushes to your aid.", "一个强大的恶魔守护者冲来援助你。" },
        { "A shield forms around you when casting spells or using Invocations. (SH +7)", "当你施放法术或使用祈祷时，周围会形成一个护盾。（盾挡+7）" },
        { "A thick, meltable icy envelope protects you from harm. (AC +", "一层厚实可融化的冰封包裹保护你免受伤害。（防御+" },
        { "A weak demonic guardian rushes to your aid.", "一个弱小的恶魔守护者冲来援助你。" },
        { "Armour fits poorly on your large pseudopods.", "护甲在你较大的伪足上不合身。" },
        { "Armour fits poorly on your massive pseudopods.", "护甲在你巨大的伪足上不合身。" },
        { "Armour fits poorly on your pseudopods.", "护甲在你的伪足上不合身。" },
        { "Armour fits poorly on your strangely shaped body.", "护甲在你变形奇怪的身体上不合身。" },
        { "Foes burned or shocked in your presence are regularly outlined in light.", "在你面前被烧伤或电击的敌人经常会被光线勾勒出来。" },
        { "Foes burned or shocked in your presence may be outlined in light.", "在你面前被烧伤或电击的敌人可能会被光线勾勒出来。" },
        { "It takes a long time for you to wield or remove held weapons.", "你持握或移除武器需要很长时间。" },
        { "One of your tentacles bears a large vicious spike.", "你的一条触手上有一根巨大的凶猛尖刺。" },
        { "One of your tentacles bears a nasty spike.", "你的一条触手上有一根锐利的尖刺。" },
        { "One of your tentacles bears a spike.", "你的一条触手上有一根尖刺。" },
        { "Potions are less effective at restoring your health.", "药水恢复你生命的效果降低。" },
        { "Potions cannot restore your health.", "药水无法恢复你的生命。" },
        { "Spells you cast and wands you use may paralyse nearby enemies.", "你施放的法术和使用的魔杖可能会麻痹附近的敌人。" },
        { "Spells you cast cost 1 less MP (to a minimum of 1).", "你施放的法术消耗减少1点魔力（最低为1）。" },
        { "Spells you cast cost 2 less MP (to a minimum of 1).", "你施放的法术消耗减少2点魔力（最低为1）。" },
        { "Spells you cast may paralyse adjacent enemies.", "你施放的法术可能会麻痹相邻的敌人。" },
        { "Spells you cast may paralyse nearby enemies.", "你施放的法术可能会麻痹附近的敌人。" },
        { "The East Wind leaves your foes to susceptible to magic after you Rampage.", "东风使你在狂暴后敌人更容易受到魔法影响。" },
        { "The North Wind lets you shrug off injuries taken while stampeding.", "北风让你能够无视奔踏时受到的伤害。" },
        { "The South Wind quickens your rampage movements after stabbing.", "南风在刺击后加速你的狂暴移动。" },
        { "The West Wind empowers your ranged attacks as you Rampage.", "西风在你狂暴时增强你的远程攻击。" },
        { "When hurt, damage is shared between your health and your magic reserves.", "受伤时，伤害在你的生命和魔力储备之间分摊。" },
        { "When low on magic, you restore magic in place of health.", "当魔力不足时，你以消耗生命为代价恢复魔力。" },
        { "When seriously injured, your blood forms armour. (AC +", "当你严重受伤时，血液会形成护甲。（防御+" },
        { "When seriously injured, your blood forms thick armour. (AC +", "当你严重受伤时，血液会形成厚实的护甲。（防御+" },
        { "When seriously injured, your blood forms very thick armour. (AC +", "当你严重受伤时，血液会形成非常厚实的护甲。（防御+" },
        { "When you translocate, a monster is sometimes pulled along with you.", "当你位移时，有时会将一个怪物一起拉过去。" },
        { "Whenever you drink a healing potion, you attack all around you.", "每当你饮用治疗药水时，你会攻击周围的所有敌人。" },
        { "You absorb twice as much mutagenic energy from being contaminated.", "你从污染中吸收双倍的变异能量。" },
        { "You are agile. (Dex +4, Str/Int -1)", "你很敏捷。（敏捷+4，力量/智力-1）" },
        { "You are almost entirely resistant to further mutation and mutation removal.", "你几乎完全抵抗进一步变异和变异移除。" },
        { "You are almost immune to the effects of cold. (rC+++)", "你几乎对寒冷效果免疫。（冰抗+++）" },
        { "You are almost immune to the effects of heat. (rF+++)", "你几乎对火焰效果免疫。（火抗+++）" },
        { "You are camouflaged when in or above water. (Stealth+)", "你在水中或水上时获得伪装。（潜行+）" },
        { "You are clumsy. (Dex -3)", "你很笨拙。（敏捷-3）" },
        { "You are cold resistant. (rC+)", "你耐寒。（冰抗+）" },
        { T_("You are cold-blooded and may be slowed by cold attacks."), "你是冷血动物，可能被寒冷攻击减速。" },
        { "You are completely attuned to the shadows.", "你完全与暗影同调。" },
        { "You are completely covered in icy blue scales. (AC +4, rC+)", "你完全覆盖着冰蓝鳞片。（防御+4，冰抗+）" },
        { "You are completely covered in iridescent scales. (AC +6)", "你完全覆盖着虹彩鳞片。（防御+6）" },
        { "You are completely covered in large bone plates. (SH +8)", "你完全覆盖着大型骨板。（盾挡+8）" },
        { "You are completely covered in molten scales. (AC +4, rF+)", "你完全覆盖着熔岩鳞片。（防御+4，火抗+）" },
        { "You are completely covered in razor-sharp scales. (AC +3, Slay +3)", "你完全覆盖着锋利鳞片。（防御+3，杀戮+3）" },
        { "You are completely covered in rugged brown scales. (AC +3, +7% HP)", "你完全覆盖着粗糙棕鳞。（防御+3，+7%生命）" },
        { "You are completely covered in sharp spines.", "你完全覆盖着锋利的尖刺。" },
        { "You are completely covered in slimy green scales. (AC +4, rPois)", "你完全覆盖着黏滑绿鳞。（防御+4，毒抗）" },
        { "You are completely covered in thin metallic scales. (AC +4, rElec)", "你完全覆盖着薄金属鳞片。（防御+4，电抗）" },
        { "You are completely covered in yellow scales. (AC +4, rCorr)", "你完全覆盖着黄色鳞片。（防御+4，酸抗）" },
        { "You are covered in fur. (AC +1)", "你覆盖着毛发。（防御+1）" },
        { "You are covered in slimy tendrils that may disarm your opponents.", "你覆盖着黏液卷须，可能缴械对手。" },
        { "You are covered in thick fur. (AC +2)", "你覆盖着浓密毛发。（防御+2）" },
        { "You are darkly shadowed, frequently releasing foul flame when damaged in melee.", "你被深沉的阴影笼罩，在近战受伤时经常会释放污秽火焰。" },
        { "You are dopey. (Int -3)", "你很迟钝。（智力-3）" },
        { "You are easily found by Zot.", "你很容易被佐特发现。" },
        { "You are empowered by your non-innate mutations. (+", "你被你非先天变异所增强。（+" },
        { "You are extremely frail. (-30% HP)", "你极其脆弱。（-30%生命）" },
        { "You are extremely inexperienced. (-3 XL)", "你极其缺乏经验。（-3级）" },
        { "You are extremely robust. (+30% HP)", "你极其健壮。（+30%生命）" },
        { "You are extremely strong-willed. (Will+++)", "你意志极其坚强。（意志+++）" },
        { "You are extremely unskilled. (-3 Apt)", "你天赋极其不足。（-3资质）" },
        { "You are extremely vulnerable to cold. (rC---)", "你极其怕冷。（冰抗---）" },
        { "You are extremely vulnerable to heat. (rF---)", "你极其怕热。（火抗---）" },
        { "You are extremely weak-willed. (Will---)", "你意志极其薄弱。（意志---）" },
        { "You are faintly shadowed, very rarely releasing foul flame when damaged in melee.", "你被淡淡的阴影笼罩，在近战受伤时极少释放污秽火焰。" },
        { "You are frail. (-10% HP)", "你很脆弱。（-10%生命）" },
        { "You are hated by all.", "你被所有生物憎恨。" },
        { "You are heat resistant. (rF+)", "你耐热。（火抗+）" },
        { "You are highly strong-willed. (Will++)", "你意志非常坚强。（意志++）" },
        { "You are immune to clouds of flame.", "你对火焰云免疫。" },
        { "You are immune to freezing clouds.", "你对冰冻云免疫。" },
        { "You are immune to negative energy. (rN+++)", "你对负能量免疫。（负抗+++）" },
        { "You are immune to poison.", "你对毒素免疫。" },
        { "You are immune to the effects of steam.", "你对蒸汽效果免疫。" },
        { "You are immune to unholy pain and torment.", "你对邪恶痛苦和折磨免疫。" },
        { "You are in touch with the powers of death.", "你与死亡的力量相通。" },
        { T_("You are incapable of wielding weapons or throwing items."), "你无法持握武器或投掷物品。" },
        { "You are inexperienced. (-2 XL)", "你缺乏经验。（-2级）" },
        { "You are missing a hand.", "你缺少一只手。" },
        { "You are missing an eye, making it more difficult to aim.", "你缺少一只眼睛，瞄准更加困难。" },
        { "You are mostly covered in icy blue scales. (AC +3)", "你大部分覆盖着冰蓝鳞片。（防御+3）" },
        { "You are mostly covered in iridescent scales. (AC +4)", "你大部分覆盖着虹彩鳞片。（防御+4）" },
        { "You are mostly covered in large bone plates. (SH +6)", "你大部分覆盖着大型骨板。（盾挡+6）" },
        { "You are mostly covered in molten scales. (AC +3)", "你大部分覆盖着熔岩鳞片。（防御+3）" },
        { "You are mostly covered in razor-sharp scales. (AC +2, Slay +2)", "你大部分覆盖着锋利鳞片。（防御+2，杀戮+2）" },
        { "You are mostly covered in rugged brown scales. (AC +2, +5% HP)", "你大部分覆盖着粗糙棕鳞。（防御+2，+5%生命）" },
        { "You are mostly covered in sharp spines.", "你大部分覆盖着锋利的尖刺。" },
        { "You are mostly covered in slimy green scales. (AC +3)", "你大部分覆盖着黏滑绿鳞。（防御+3）" },
        { "You are mostly covered in thin metallic scales. (AC +3)", "你大部分覆盖着薄金属鳞片。（防御+3）" },
        { "You are mostly covered in yellow scales. (AC +3)", "你大部分覆盖着黄色鳞片。（防御+3）" },
        { "You are occasionally teleported next to monsters.", "你偶尔会被传送到怪物旁边。" },
        { "You are often teleported next to monsters.", "你经常会被传送到怪物旁边。" },
        { "You are partially covered in icy blue scales. (AC +2)", "你部分覆盖着冰蓝鳞片。（防御+2）" },
        { "You are partially covered in iridescent scales. (AC +2)", "你部分覆盖着虹彩鳞片。（防御+2）" },
        { "You are partially covered in large bone plates. (SH +4)", "你部分覆盖着大型骨板。（盾挡+4）" },
        { "You are partially covered in molten scales. (AC +2)", "你部分覆盖着熔岩鳞片。（防御+2）" },
        { "You are partially covered in razor-sharp scales. (AC +1, Slay +1)", "你部分覆盖着锋利鳞片。（防御+1，杀戮+1）" },
        { "You are partially covered in rugged brown scales. (AC +1, +3% HP)", "你部分覆盖着粗糙棕鳞。（防御+1，+3%生命）" },
        { "You are partially covered in sharp spines.", "你部分覆盖着锋利的尖刺。" },
        { "You are partially covered in slimy green scales. (AC +2)", "你部分覆盖着黏滑绿鳞。（防御+2）" },
        { "You are partially covered in thin metallic scales. (AC +2)", "你部分覆盖着薄金属鳞片。（防御+2）" },
        { "You are partially covered in yellow scales. (AC +2)", "你部分覆盖着黄色鳞片。（防御+2）" },
        { "You are powered by pain.", "你被痛苦所赋能。" },
        { "You are quite resistant to negative energy. (rN++)", "你相当抵抗负能量。（负抗++）" },
        { "You are resistant to acid. (rCorr)", "你对酸蚀有抗性。（酸抗）" },
        { "You are resistant to electric shocks. (rElec)", "你对电击有抗性。（电抗）" },
        { "You are resistant to poisons. (rPois)", "你对毒素有抗性。（毒抗）" },
        { "You are resistant to unholy torment.", "你抵抗邪恶折磨。" },
        { "You are robust. (+10% HP)", "你很健壮。（+10%生命）" },
        { "You are sensitive to extremes of temperature. (rF-, rC-)", "你对极端温度敏感。（火抗-，冰抗-）" },
        { "You are shadowed, sometimes releasing foul flame when damaged in melee.", "你被阴影笼罩，在近战受伤时有时会释放污秽火焰。" },
        { "You are significantly more attuned to the shadows.", "你与暗影的同调显著增强。" },
        { "You are slightly more attuned to the shadows.", "你与暗影的同调略微增强。" },
        { "You are slightly weak-willed. (Will-)", "你意志略微薄弱。（意志-）" },
        { "You are somewhat inexperienced. (-1 XL)", "你有些缺乏经验。（-1级）" },
        { "You are somewhat resistant to both further mutation and mutation removal.", "你对进一步变异和变异移除都有一定抗性。" },
        { "You are somewhat resistant to further mutation.", "你对进一步变异有一定抗性。" },
        { "You are somewhat unskilled. (-1 Apt)", "你天赋有些不足。（-1资质）" },
        { "You are strong-willed. (Will+)", "你意志坚强。（意志+）" },
        { "You are strong. (Str +4, Int/Dex -1)", "你很强壮。（力量+4，智力/敏捷-1）" },
        { "You are strongly in touch with the powers of death.", "你与死亡的力量深度相通。" },
        { "You are surrounded by a mild repulsion field. (EV +2)", "你被一个温和的排斥场包围。（闪避+2）" },
        { "You are surrounded by a moderate repulsion field. (EV +3)", "你被一个中等的排斥场包围。（闪避+3）" },
        { "You are surrounded by a strong repulsion field. (EV +4, RMsl)", "你被一个强大的排斥场包围。（闪避+4，弹飞弹）" },
        { "You are surrounded by an aura of silence.", "你被一个沉默光环包围。" },
        { "You are unskilled. (-2 Apt)", "你天赋不足。（-2资质）" },
        { "You are very agile. (Dex +8, Str/Int -2)", "你非常敏捷。（敏捷+8，力量/智力-2）" },
        { "You are very clumsy. (Dex -6)", "你非常笨拙。（敏捷-6）" },
        { "You are very cold resistant. (rC++)", "你非常耐寒。（冰抗++）" },
        { "You are very dopey. (Int -6)", "你非常迟钝。（智力-6）" },
        { "You are very frail. (-20% HP)", "你非常脆弱。（-20%生命）" },
        { "You are very heat resistant. (rF++)", "你非常耐热。（火抗++）" },
        { "You are very nimble when in or above water. (Stealth+, EV+, Speed+++)", "你在水中或水上非常灵活。（潜行+，闪避+，速度+++）" },
        { "You are very robust. (+20% HP)", "你非常健壮。（+20%生命）" },
        { "You are very strong. (Str +8, Int/Dex -2)", "你非常强壮。（力量+8，智力/敏捷-2）" },
        { "You are very vulnerable to cold. (rC--)", "你非常怕冷。（冰抗--）" },
        { "You are very vulnerable to heat. (rF--)", "你非常怕热。（火抗--）" },
        { "You are very weak. (Str -6)", "你非常虚弱。（力量-6）" },
        { "You are vulnerable to cold. (rC-)", "你怕冷。（冰抗-）" },
        { "You are vulnerable to electric shocks. (rElec-)", "你容易被电击。（电抗-）" },
        { "You are vulnerable to heat. (rF-)", "你怕热。（火抗-）" },
        { "You are weak-willed. (Will--)", "你意志薄弱。（意志--）" },
        { "You are weak. (Str -3)", "你很虚弱。（力量-3）" },
        { "You bear the Mark of Annihilation.", "你携带着湮灭印记。" },
        { "You bear the Mark of Atrocity.", "你携带着暴行印记。" },
        { "You bear the Mark of Carnage.", "你携带着杀戮印记。" },
        { "You bear the Mark of Execution.", "你携带着处决印记。" },
        { "You bear the Mark of Haemoclasm.", "你携带着血破印记。" },
        { "You bear the Mark of the Celebrant.", "你携带着颂礼者印记。" },
        { "You bear the Mark of the Fanatic.", "你携带着狂热者印记。" },
        { "You bear the Mark of the Legion.", "你携带着军团印记。" },
        { "You bear the Mark of the Tyrant.", "你携带着暴君印记。" },
        { "You begin to heal more quickly.", "你开始恢复得更快。" },
        { "You can enhance your damage-dealing spells by burning harvested memories.", "你可以通过燃烧收集的记忆来增强你的伤害法术。" },
        { "You can equip up to 6 pieces of aux armour in any combination and unleash them.", "你最多可以装备6件辅助护甲任意组合并释放它们。" },
        { "You can equip up to 6 pieces of aux armour in any combination.", "你最多可以装备6件辅助护甲任意组合。" },
        { "You can exhale a cloud of poison.", "你可以喷吐一团毒雾。" },
        { "You can hop long distances, but move slowly.", "你可以长距离跳跃，但移动缓慢。" },
        { "You can hop short distances, but move slowly.", "你可以短距离跳跃，但移动缓慢。" },
        { "You can hurl damnation.", "你可以投掷诅咒之火。" },
        { "You can magically evade attacks while moving or waiting.", "你可以在移动或等待时魔法般地闪避攻击。" },
        { "You can regularly gain power from killing poisoned or drained foes.", "你经常可以通过杀死中毒或虚弱的敌人获得力量。" },
        { "You can sometimes gain power from killing poisoned or drained foes.", "你有时可以通过杀死中毒或虚弱的敌人获得力量。" },
        { "You can speak a Word of Chaos.", "你可以说出混沌之语。" },
        { "You can spit poison.", "你可以喷吐毒素。" },
        { "You can wield a second weapon in your off-hand.", "你可以在副手持有第二把武器。" },
        { "You cannot be stealthy.", "你无法潜行。" },
        { "You cannot drink.", "你无法饮用。" },
        { "You cannot equip rings or amulets.", "你无法佩戴戒指或护身符。" },
        { "You cannot study or cast Air magic.", "你无法学习或施放空气魔法。" },
        { "You cannot study or cast Alchemy magic.", "你无法学习或施放炼金魔法。" },
        { "You cannot study or cast Conjurations magic.", "你无法学习或施放咒法魔法。" },
        { "You cannot study or cast Earth magic.", "你无法学习或施放大地魔法。" },
        { "You cannot study or cast Fire magic.", "你无法学习或施放火焰魔法。" },
        { "You cannot study or cast Forgecraft magic.", "你无法学习或施放锻造魔法。" },
        { "You cannot study or cast Hexes magic.", "你无法学习或施放诅咒魔法。" },
        { "You cannot study or cast Ice magic.", "你无法学习或施放寒冰魔法。" },
        { "You cannot study or cast Necromancy magic.", "你无法学习或施放死灵魔法。" },
        { "You cannot study or cast Summoning magic.", "你无法学习或施放召唤魔法。" },
        { "You cannot study or cast Translocations magic.", "你无法学习或施放位移魔法。" },
        { "You cannot study or use magical devices.", "你无法学习或使用魔法装置。" },
        { "You cannot train Armour skill.", "你无法训练护甲技能。" },
        { "You cannot train Dodging skill.", "你无法训练闪避技能。" },
        { "You cannot voluntarily change form.", "你无法自愿改变形态。" },
        { "You cannot wear armour.", "你无法穿戴护甲。" },
        { "You cover ground extremely slowly.", "你移动极其缓慢。" },
        { "You cover ground slowly.", "你移动缓慢。" },
        { "You cover ground very slowly.", "你移动非常缓慢。" },
        { "You discover more artefacts.", "你发现的神器增多。" },
        { "You discover slightly more artefacts.", "你发现的神器略微增多。" },
        { "You do not regenerate naturally.", "你无法自然再生。" },
        { "You do not regenerate when monsters are visible.", "当怪物在视野中时你无法再生。" },
        { "You do not regenerate.", "你无法再生。" },
        { "You draw destruction from the endless fires of Gehenna.", "你从基希纳的无尽火焰中汲取毁灭之力。" },
        { "You draw destruction from the frigid wastes of Cocytus.", "你从科塞特斯的冰冷荒原中汲取毁灭之力。" },
        { "You draw destruction from the ruthless spite of Dis.", "你从迪斯的无情怨恨中汲取毁灭之力。" },
        { "You draw destruction from the wailing grief of Tartarus.", "你从塔耳塔洛斯的哀嚎悲伤中汲取毁灭之力。" },
        { "You expend magic power (3 MP) to strengthen your wands.", "你消耗魔力（3点）来增强你的魔杖。" },
        { "You float through the air rather than walking.", "你在空中漂浮，而非行走。" },
        { "You frequently emit foul miasma when damaged in melee.", "你在近战受伤时经常会散发出恶臭的瘴气。" },
        { "You frequently pull newly seen creatures towards you.", "你经常将新看到的生物拉向你。" },
        { "You frequently scream uncontrollably at those who injure you.", "你经常不受控制地对伤害你的人尖叫。" },
        { "You gain AC when you inflict magical misfortune on nearby enemies.", "当你对附近的敌人施加魔法灾厄时，你获得防御。" },
        { "You gain doubled healing and magic from potions.", "你从药水中获得双倍的治疗和魔力恢复。" },
        { "You gain extra lives every three experience levels.", "你每三级获得一条额外生命。" },
        { "You generate static electricity when injured, which occasionally lashes out at nearby attackers.", "你受伤时产生静电，偶尔会攻击附近的敌人。" },
        { "You have a beak for a mouth.", "你有一张喙状的嘴。" },
        { "You have a considerably increased reservoir of magic. (+20% MP)", "你的魔力储备大幅增加。（+20%魔力）" },
        { "You have a greatly increased reservoir of magic. (+30% MP)", "你的魔力储备极大增加。（+30%魔力）" },
        { "You have a heavy armoured tail.", "你有一条沉重的装甲尾巴。" },
        { "You have a moderately thin skeletal structure. (Dex +4, Stealth++)", "你的骨骼结构相当纤细。（敏捷+4，潜行++）" },
        { "You have a pair of antennae on your head.", "你头上有一对触角。" },
        { "You have a pair of horns on your head.", "你头上有一对角。" },
        { "You have a pair of large antennae on your head. (SInv)", "你头上有一对大触角。（看破隐形）" },
        { "You have a pair of large horns on your head.", "你头上有一对大角。" },
        { "You have a pair of small antennae on your head.", "你头上有一对小触角。" },
        { "You have a pair of small horns on your head.", "你头上有一对小角。" },
        { "You have a sharp stinger which inflicts weakening toxins.", "你有一根锋利的毒刺，能造成虚弱毒素。" },
        { "You have a small jelly attached to you that may absorb projectiles.", "你身上附着一个小果冻，可能吸收飞弹。" },
        { "You have a small jelly attached to you that senses nearby items.", "你身上附着一个小果冻，能够感知附近的物品。" },
        { "You have a small tail.", "你有一条小尾巴。" },
        { "You have a somewhat thin skeletal structure. (Dex +2, Stealth+)", "你的骨骼结构有些纤细。（敏捷+2，潜行+）" },
        { "You have a special connection with the divine. (Faith)", "你与神圣有特殊的联系。（信仰）" },
        { "You have a tail ending in a sharp stinger.", "你的尾巴末端是一根锋利的毒刺。" },
        { "You have acidic saliva.", "你有酸性唾液。" },
        { "You have an absolutely massive brain. (Int +6, Wiz)", "你有一个绝对庞大无比的大脑。（智力+6，巫术）" },
        { "You have an armoured tail.", "你有一条装甲尾巴。" },
        { "You have an extended range of vision and can be seen from far away.", "你的视野范围扩大，也可以从远处被看到。" },
        { "You have an extremely huge brain. (Int +4)", "你有一个极其巨大的大脑。（智力+4）" },
        { "You have an increased reservoir of magic. (+10% MP)", "你的魔力储备增加。（+10%魔力）" },
        { "You have an uncanny knack for detecting items.", "你有探测物品的奇特能力。" },
        { "You have an unnaturally thin skeletal structure. (Dex +6, Stealth+++)", "你的骨骼结构异常纤细。（敏捷+6，潜行+++）" },
        { "You have an unusually large brain. (Int +2)", "你有一个异常大的大脑。（智力+2）" },
        { "You have claws for feet.", "你脚上有爪子。" },
        { "You have claws for hands.", "你手上有爪子。" },
        { "You have exceptionally superior vitality. (+12 MHP)", "你拥有异常出众的活力。（+12最大生命）" },
        { "You have extremely sharp teeth.", "你有极其锋利的牙齿。" },
        { "You have extremely tough skin. (AC +3)", "你拥有极其坚韧的皮肤。（防御+3）" },
        { "You have great hidden genetic potential.", "你拥有巨大的隐藏基因潜力。" },
        { "You have hidden genetic defects.", "你拥有隐藏的基因缺陷。" },
        { "You have hidden genetic potential.", "你拥有隐藏的基因潜力。" },
        { "You have hoof-like feet.", "你有蹄状脚。" },
        { "You have hooves in place of feet.", "你的脚变成了蹄子。" },
        { "You have large cloven feet.", "你有大型分趾蹄。" },
        { "You have much superior vitality. (+8 MHP)", "你拥有非常出众的活力。（+8最大生命）" },
        { "You have razor-sharp teeth.", "你有剃刀般锋利的牙齿。" },
        { "You have razor-sharp toenails.", "你有剃刀般锋利的趾甲。" },
        { "You have sharp fingernails.", "你有锋利的指甲。" },
        { "You have sharp toenails.", "你有锋利的趾甲。" },
        { "You have slow reflexes. (EV -10)", "你的反应迟钝。（闪避-10）" },
        { "You have somewhat slow reflexes. (EV -5)", "你的反应有些迟钝。（闪避-5）" },
        { "You have superior vitality. (+4 MHP)", "你拥有出众的活力。（+4最大生命）" },
        { "You have supernaturally acute vision. (SInv)", "你拥有超自然的敏锐视觉。（看破隐形）" },
        { "You have tentacles for arms and can constrict enemies.", "你的手臂是触手，可以缠绕敌人。" },
        { "You have terrible hidden genetic defects.", "你拥有可怕的隐藏基因缺陷。" },
        { "You have tough skin. (AC +1)", "你拥有坚韧的皮肤。（防御+1）" },
        { "You have very sharp fingernails.", "你有非常锋利的指甲。" },
        { "You have very sharp teeth.", "你有非常锋利的牙齿。" },
        { "You have very slow reflexes. (EV -15)", "你的反应非常迟钝。（闪避-15）" },
        { "You have very tough skin. (AC +2)", "你拥有非常坚韧的皮肤。（防御+2）" },
        { "You heal very quickly.", "你恢复得非常快。" },
        { "You heal yourself by feeding off the suffering of those around you.", "你通过汲取周围生物的苦难来治愈自己。" },
        { "You learn spells naturally, not from books.", "你自然地学习法术，不需要书籍。" },
        { "You may rarely emit foul miasma when damaged in melee.", "你在近战受伤时可能极少散发出恶臭的瘴气。" },
        { "You may spread the effect of potions you drink to nearby monsters.", "你饮用药水的效果可能会传播到附近的怪物。" },
        { "You move with supernatural speed. (Speed+)", "你以超自然的速度移动。（速度+）" },
        { "You move with supernatural speed. (Speed++)", "你以非常超自然的速度移动。（速度++）" },
        { "You move with supernatural speed. (Speed+++)", "你以极其超自然的速度移动。（速度+++）" },
        { "You occasionally shout uncontrollably at those who injure you.", "你偶尔不受控制地对伤害你的人大喊。" },
        { "You passively map a large area around you.", "你被动地绘制周围大片区域的地图。" },
        { "You passively map the area around you.", "你被动地绘制周围区域的地图。" },
        { "You perform a melee attack whenever you cast damage-dealing spells.", "每当你施放伤害法术时，你会进行一次近战攻击。" },
        { "You possess an exceptional clarity of mind.", "你拥有非凡的心智清晰。" },
        { "You punish those that try to bend your will. (Will+)", "你惩罚那些试图扭曲你意志的人。（意志+）" },
        { "You read scrolls incredibly loudly when enemies are in sight.", "你在敌人视野中时，阅读卷轴的声音异常响亮。" },
        { "You recover more slowly from Doom and Banes.", "你从厄运和灾祸中恢复得更慢。" },
        { "You reflexively headbutt those who attack you in melee.", "你会反射性地用头槌反击近战攻击你的敌人。" },
        { "You refuse to drink potions in combat unless seriously injured.", "除非严重受伤，否则你在战斗中拒绝饮用药水。" },
        { "You refuse to read scrolls in combat unless seriously injured.", "除非严重受伤，否则你在战斗中拒绝阅读卷轴。" },
        { "You regain HP and MP as you explore.", "你在探索时恢复生命和魔力。" },
        { "You regenerate a little health from kills.", "你通过击杀恢复少量生命。" },
        { "You regenerate a lot of health from kills.", "你通过击杀恢复大量生命。" },
        { "You regenerate health from kills.", "你通过击杀恢复生命。" },
        { "You regenerate magic rapidly.", "你快速恢复魔力。" },
        { "You regenerate.", "你具有再生能力。" },
        { "You resist negative energy. (rN+)", "你抵抗负能量。（负抗+）" },
        { "You shall have no god before yourself.", "你将自己置于神之前。" },
        { "You sometimes emit foul miasma when damaged in melee.", "你在近战受伤时有时会散发出恶臭的瘴气。" },
        { "You sometimes gain a little power by taking damage.", "你有时通过承受伤害获得少量力量。" },
        { "You sometimes gain power by taking damage.", "你有时通过承受伤害获得力量。" },
        { "You sometimes pull newly seen creatures towards you.", "你有时将新看到的生物拉向你。" },
        { "You stampede swiftly towards enemies and can push them backward.", "你向敌人猛冲，可以将他们推回去。" },
        { "You take considerably more damage. (AC -15)", "你受到相当多的伤害。（防御-15）" },
        { "You take more damage. (AC -10)", "你受到更多伤害。（防御-10）" },
        { "You take slightly more damage. (AC -5)", "你受到稍微更多的伤害。（防御-5）" },
        { "You thrive by killing the living.", "你通过杀戮活物而茁壮成长。" },
        { "You use scrolls of enchantment on lesser artefacts.", "你可以使用附魔卷轴来增强低级神器。" },
        { "Your SH is halved, but you deal more damage with two-handed weapons.", "你的盾挡减半，但双手武器造成更多伤害。" },
        { "Your attacks are a little less effective. (Slay -3)", "你的攻击效果略微降低。（杀戮-3）" },
        { "Your attacks are less effective. (Slay -5)", "你的攻击效果降低。（杀戮-5）" },
        { "Your attacks are much less effective. (Slay -7)", "你的攻击效果大幅降低。（杀戮-7）" },
        { "Your bite disrupts and absorbs the magic of your enemies.", "你的咬击能干扰并吸收敌人的魔法。" },
        { "Your blood hastes a few of your allies when you are sufficiently damaged.", "当你受到足够伤害时，你的血液会加速少数盟友。" },
        { "Your blood hastes several of your allies when you are sufficiently damaged.", "当你受到足够伤害时，你的血液会加速数名盟友。" },
        { "Your body has grown eyes which may confuse attackers. (Acc +3)", "你的身体长出了可能迷惑攻击者的眼睛。（精准+3）" },
        { "Your body has grown many eyes which may confuse attackers. (Acc +5)", "你的身体长出了许多可能迷惑攻击者的眼睛。（精准+5）" },
        { "Your body is covered in eyes which may confuse attackers. (Acc +7, SInv)", "你的身体遍布可能迷惑攻击者的眼睛。（精准+7，看破隐形）" },
        { "Your body sometimes grows weak and slow upon taking damage.", "你的身体有时在受伤后会变得虚弱和缓慢。" },
        { "Your body sometimes grows weak upon taking damage.", "你的身体有时在受伤后会变得虚弱。" },
        { "Your casting is disrupted.", "你的施法受到干扰。" },
        { "Your casting is seriously disrupted.", "你的施法受到严重干扰。" },
        { "Your casting is slightly disrupted.", "你的施法受到轻微干扰。" },
        { "Your cowardice makes you less effective in combat with threatening foes.", "你的懦弱使你在面对有威胁的敌人时战斗效率降低。" },
        { "Your demonic aura causes all spilled blood to erupt in flames.", "你的恶魔光环会让所有流出的血液燃烧起来。" },
        { "Your demonic aura often causes spilled blood to erupt in flames.", "你的恶魔光环经常会让流出的血液燃烧起来。" },
        { "Your demonic aura sometimes causes spilled blood to erupt in flames.", "你的恶魔光环有时会让流出的血液燃烧起来。" },
        { "Your demonic guardian is weakened.", "你的恶魔守护者变弱了。" },
        { "Your divine heritage dramatically boosts your attributes as you level up.", "你的神圣血统在升级时大幅提升你的属性。" },
        { "Your experience applies equally to all skills.", "你的经验平均分配于所有技能。" },
        { "Your first few attacks do less damage.", "你的前几次攻击造成较少伤害。" },
        { "Your four strong arms can wield two-handed weapons with a shield.", "你的四条强壮手臂可以持盾使用双手武器。" },
        { "Your gelatinous body deflects attacks. (AC +3, EV +3)", "你凝胶般的身体偏转攻击。（防御+3，闪避+3）" },
        { "Your guardian grows in power.", "你的守护者力量增长了。" },
        { "Your health recovers twice as slowly from being drained.", "你被虚弱后生命恢复速度减半。" },
        { "Your hexes are more powerful.", "你的诅咒更加强大。" },
        { "Your large and strong wings let you fly.", "你大而强壮的翅膀让你能够飞行。" },
        { "Your lower body shifts to a powerful aquatic tail in water.", "在水中你的下半身会变成一条强大的水生尾巴。" },
        { "Your magical and physical power is enhanced at high health.", "你在高生命时魔法和物理力量增强。" },
        { "Your magical and physical power is greatly enhanced at high health.", "你在高生命时魔法和物理力量大幅增强。" },
        { "Your magical and physical power is slightly enhanced at high health.", "你在高生命时魔法和物理力量略微增强。" },
        { "Your magical capacity is extremely low. (-30% MP)", "你的魔力容量极低。（-30%魔力）" },
        { "Your magical capacity is low. (-10% MP)", "你的魔力容量较低。（-10%魔力）" },
        { "Your magical capacity is very low. (-20% MP)", "你的魔力容量很低。（-20%魔力）" },
        { "Your magical flight helps you evade attacks. (EV +4)", "你的魔法飞行帮助你闪避攻击。（闪避+4）" },
        { "Your magical power and effects resist disruption.", "你的魔法力量和效果能够抵抗干扰。" },
        { "Your magical power is your life essence.", "你的魔力就是你的生命精华。" },
        { "Your melee attacks may debilitate your foes.", "你的近战攻击可能会削弱你的敌人。" },
        { "Your melee attacks may flood your foes with ooze.", "你的近战攻击可能会用软泥淹没你的敌人。" },
        { "Your metabolism doubles the duration of potion status effects.", "你的新陈代谢使药水状态效果持续时间翻倍。" },
        { "Your mind is acute. (Int +4, Str/Dex -1)", "你的头脑敏锐。（智力+4，力量/敏捷-1）" },
        { "Your mind is very acute. (Int +8, Str/Dex -2)", "你的头脑非常敏锐。（智力+8，力量/敏捷-2）" },
        { "Your movements are less encumbered by armour. (ER -4)", "护甲对你的移动阻碍减少。（负重-4）" },
        { "Your movements are significantly less encumbered by armour. (ER -6)", "护甲对你的移动阻碍显著减少。（负重-6）" },
        { "Your movements are slightly less encumbered by armour. (ER -2)", "护甲对你的移动阻碍略微减少。（负重-2）" },
        { "Your natural rate of healing is unusually fast.", "你的自然恢复速度异常快。" },
        { "Your paws help you pounce on unaware monsters.", "你的爪垫帮助你扑向毫无防备的怪物。" },
        { "Your pliable body absorbs attacks. (AC +2, EV +2)", "你柔韧的身体吸收攻击。（防御+2，闪避+2）" },
        { "Your presence sometimes corrodes or deforms those you injure.", "你的存在有时会腐蚀或变形你伤害的人。" },
        { "Your presence sometimes corrodes those you injure.", "你的存在有时会腐蚀你伤害的人。" },
        { "Your rate of healing slows.", "你的恢复速度变慢。" },
        { "Your rubbery body absorbs attacks. (AC +1, EV +1)", "你橡胶般的身体吸收攻击。（防御+1，闪避+1）" },
        { "Your scales are fused with iron. (AC + 5)", "你的鳞片与铁融合。（防御+5）" },
        { "Your shed blood may rise up to attack you as a group.", "你流出的血液可能会成群地起来攻击你。" },
        { "Your shed blood may rise up to attack you.", "你流出的血液可能会起来攻击你。" },
        { "Your skin blends seamlessly with your surroundings (Stealth++).", "你的皮肤与周围环境完美融合。（潜行++）" },
        { "Your skin changes colour to match your surroundings (Stealth+).", "你的皮肤会变色以匹配环境。（潜行+）" },
        { "Your skin perfectly mimics your surroundings (Stealth+++).", "你的皮肤完美模拟周围环境。（潜行+++）" },
        { "Your snake-like lower body moves slowly, but can constrict enemies.", "你的蛇形下半身移动缓慢，但可以缠绕敌人。" },
        { "Your snake-like lower body moves slowly.", "你的蛇形下半身移动缓慢。" },
        { "Your spellcasting is much less encumbered by armour.", "你的法术施放受护甲的阻碍大大减少。" },
        { "Your spells are a little easier to cast, but a little less powerful.", "你的法术施放稍微更容易，但威力稍微更弱。" },
        { "Your spells are a little harder to cast, but a little more powerful.", "你的法术施放稍微更困难，但威力稍微更强。" },
        { "Your spells are easier to cast, but less powerful.", "你的法术施放更容易，但威力更弱。" },
        { "Your spells are harder to cast, but more powerful.", "你的法术施放更困难，但威力更强。" },
        { "Your spells are much easier to cast, but much less powerful.", "你的法术施放容易得多，但威力弱得多。" },
        { "Your spells are much harder to cast, but much more powerful.", "你的法术施放困难得多，但威力强得多。" },
        { "Your stone body is resiliant and immune to petrification. (AC +", "你的石质身体坚韧且免疫石化。（防御+" },
        { "Your system is resistant to poisons. (rPois+)", "你的身体对毒素有抗性。（毒抗+）" },
        { "Your tail ends in a sharp venomous barb.", "你的尾巴末端是一根锋利的毒刺。" },
        { "Your tail ends in a venomous barb.", "你的尾巴末端是一根毒刺。" },
        { "Your tail ends in a wickedly sharp and venomous barb.", "你的尾巴末端是一根极其锋利的毒刺。" },
        { "Your thick and shaggy fur keeps you warm. (AC +3, rC+)", "你浓密蓬松的毛发让你保持温暖。（防御+3，冰抗+）" },
        { "Your touch may inflict irresistible damage on your foes.", "你的触碰可能对敌人造成不可抵抗的伤害。" },
        { "Your touch may inflict minor irresistible damage on your foes.", "你的触碰可能对敌人造成少量不可抵抗的伤害。" },
        { "Your touch may irresistibly damage your foes and sap their willpower.", "你的触碰可能对敌人造成不可抵抗的伤害并削弱他们的意志力。" },
        { "Your translucent skin reduces your foes' accuracy. (Stealth+)", "你半透明的皮肤降低了敌人的精准度。（潜行+）" },
        { "Your translucent skin slightly reduces your foes' accuracy. (Stealth+)", "你半透明的皮肤略微降低了敌人的精准度。（潜行+）" },
        { "Your transparent skin significantly reduces your foes' accuracy. (Stealth+)", "你透明的皮肤显著降低了敌人的精准度。（潜行+）" }
    };
    auto it = zh_names.find(en);
    return it != zh_names.end() ? it->second : nullptr;
}

string mutation_desc(mutation_type mut, int level, bool colour,
        bool is_sacrifice)
{
    // Ignore the player's forms, etc.
    const bool ignore_player = (level != -1);

    const bool active = mut_is_compatible(mut);
    const bool temporary = you.has_temporary_mutation(mut);

    // level == -1 means using the player's current level of this mutation
    if (level == -1)
        level = you.get_base_mutation_level(mut);

    string result;

    const mutation_def& mdef = _get_mutation_def(mut);

    // Helper to append dynamic value with Chinese base string support
    auto _get_base = [](const char* en) -> string {
        if (Options.language == lang_t::ZH)
        {
            const char* zh = _zh_mutation_desc(en);
            return zh ? zh : en;
        }
        return en;
    };

    if (mut == MUT_ICEMAIL)
    {
        ostringstream ostr;
        ostr << _get_base(mdef.have[0]) << player_icemail_armour_class() << ")";
        result = ostr.str();
    }
    else if (mut == MUT_CONDENSATION_SHIELD)
    {
        ostringstream ostr;
        ostr << _get_base(mdef.have[0]) << player_condensation_shield_class() << ")";
        result = ostr.str();
    }
    else if (mut == MUT_SANGUINE_ARMOUR)
    {
        ostringstream ostr;
        ostr << _get_base(mdef.have[level - 1]) << sanguine_armour_bonus() / 100 << ")";
        result = ostr.str();
    }
    else if (mut == MUT_STONE_BODY)
    {
        ostringstream ostr;
        ostr << _get_base(mdef.have[0]) << stone_body_armour_bonus() / 100 << ")";
        result = ostr.str();
    }
    else if (mut == MUT_PROTEAN_GRACE)
    {
        ostringstream ostr;
        int num = protean_grace_amount();
        ostr << _get_base(mdef.have[0]) << num << (T_(" EV, Slay +")) << num << ")";
        result = ostr.str();
    }
    else if (mut == MUT_MP_WANDS && you.has_mutation(MUT_HP_CASTING))
        result = T_("You expend health (3 HP) to strengthen your wands.");
    else if (!ignore_player && mut == MUT_TENTACLE_ARMS)
    {
        const string num_tentacles = number_in_words(you.has_tentacles(false));
        result = make_stringf(
            T_("You have tentacles for arms and can constrict up to %s enemies at once."),
            num_tentacles.c_str());
    }
    else if (!ignore_player && you.has_innate_mutation(MUT_PAWS) && mut == MUT_CLAWS)
        result = T_("You have sharp claws."); // XX ugly override
    else if (result.empty() && level > 0)
        result = mdef.have[level - 1];

    // Translate for Chinese mode — must happen before formatting wrappers
    // because colour/parens/brackets are added below.
    if (Options.language == lang_t::ZH && !result.empty())
    {
        const char* zh = _zh_mutation_desc(result);
        if (zh)
            result = zh;
    }

    if (!ignore_player && !active)
        result = "(" + result + ")";

    if (temporary)
        result = "[" + result + "]";

    if (colour)
    {
        const char* colourname = (is_bad_mutation(mut) ? "red" : "lightgrey");
        const bool permanent   = you.has_innate_mutation(mut);

        if (permanent)
        {
            const bool demonspawn = (you.species == SP_DEMONSPAWN);
            const bool extra = you.get_base_mutation_level(mut, false, true, true) > 0;

            if (!active || (mut == MUT_COLD_BLOODED && player_res_cold(false) > 0))
                colourname = "darkgrey";
            else if (is_sacrifice)
                colourname = "lightred";
            else if (extra)
                colourname = demonspawn ? "lightcyan" : "cyan";
            else
                colourname = demonspawn ? "cyan"      : "lightblue";
        }
        else if (!active)
            colourname = "darkgrey";
        else if (is_slime_mutation(mut))
            colourname = "lightgreen";
        else if (temporary)
            colourname = (you.get_base_mutation_level(mut, true, false, true) > 0) ?
                         "lightmagenta" : "magenta";

        // Build the result
        ostringstream ostr;
        ostr << '<' << colourname << '>' << result
             << "</" << colourname << '>';
        result = ostr.str();
    }

    return result;
}

// Get a description for a mutation the player will gain at a future XL,
// reworded slightly to sound like they do not currently have it.
static string _future_mutation_description(mutation_type mut_type, int levels)
{
    levels += you.innate_mutation[mut_type];
    string mut_desc = mutation_desc(mut_type, levels);

    // If we have a custom message defined for this future mutation, use it.
    const char* const* future_desc = _get_mutation_def(mut_type).will_gain;
    if (future_desc[levels - 1] != NULL)
        return string(future_desc[levels - 1]);

    // Otherwise do some simple string replacements to cover common cases.
    mut_desc = replace_all(mut_desc, " can ", " will be able to ");
    mut_desc = replace_all(mut_desc, " have ", " will have ");
    mut_desc = replace_all(mut_desc, " are ", " will be ");
    mut_desc = replace_all(mut_desc, " is ", " will be ");

    return mut_desc;
}

// The "when" numbers indicate the range of times in which the mutation tries
// to place itself; it will be approximately placed between when% and
// (when + 100)% of the way through the mutations. For example, you should
// usually get all your body slot mutations in the first 2/3 of your
// mutations and you should usually only start your tier 3 facet in the second
// half of your mutations. See _order_ds_mutations() for details.
static const facet_def _demon_facets[] =
{
    // Body Slot facets
    { 0, { MUT_CLAWS, MUT_CLAWS, MUT_CLAWS },
      { -33, -33, -33 } },
    { 0, { MUT_HORNS, MUT_HORNS, MUT_HORNS },
      { -33, -33, -33 } },
    { 0, { MUT_ANTENNAE, MUT_ANTENNAE, MUT_ANTENNAE },
      { -33, -33, -33 } },
    { 0, { MUT_HOOVES, MUT_HOOVES, MUT_HOOVES },
      { -33, -33, -33 } },
    { 0, { MUT_WEAKNESS_STINGER, MUT_WEAKNESS_STINGER, MUT_WEAKNESS_STINGER },
      { -33, -33, -33 } },
    { 0, { MUT_DEMONIC_TOUCH, MUT_DEMONIC_TOUCH, MUT_DEMONIC_TOUCH },
      { -33, -33, -33 } },
    // Scale mutations
    { 1, { MUT_DISTORTION_FIELD, MUT_DISTORTION_FIELD, MUT_DISTORTION_FIELD },
      { -33, -33, 0 } },
    { 1, { MUT_ICY_BLUE_SCALES, MUT_ICY_BLUE_SCALES, MUT_ICY_BLUE_SCALES },
      { -33, -33, 0 } },
    { 1, { MUT_LARGE_BONE_PLATES, MUT_LARGE_BONE_PLATES, MUT_LARGE_BONE_PLATES },
      { -33, -33, 0 } },
    { 1, { MUT_MOLTEN_SCALES, MUT_MOLTEN_SCALES, MUT_MOLTEN_SCALES },
      { -33, -33, 0 } },
    { 1, { MUT_RUGGED_BROWN_SCALES, MUT_RUGGED_BROWN_SCALES,
           MUT_RUGGED_BROWN_SCALES },
      { -33, -33, 0 } },
    { 1, { MUT_SLIMY_GREEN_SCALES, MUT_SLIMY_GREEN_SCALES, MUT_SLIMY_GREEN_SCALES },
      { -33, -33, 0 } },
    { 1, { MUT_THIN_METALLIC_SCALES, MUT_THIN_METALLIC_SCALES,
        MUT_THIN_METALLIC_SCALES },
      { -33, -33, 0 } },
    { 1, { MUT_THIN_SKELETAL_STRUCTURE, MUT_THIN_SKELETAL_STRUCTURE,
           MUT_THIN_SKELETAL_STRUCTURE },
      { -33, -33, 0 } },
    { 1, { MUT_YELLOW_SCALES, MUT_YELLOW_SCALES, MUT_YELLOW_SCALES },
      { -33, -33, 0 } },
    { 1, { MUT_STURDY_FRAME, MUT_STURDY_FRAME, MUT_STURDY_FRAME },
      { -33, -33, 0 } },
    { 1, { MUT_SANGUINE_ARMOUR, MUT_SANGUINE_ARMOUR, MUT_SANGUINE_ARMOUR },
      { -33, -33, 0 } },
    { 1, { MUT_BIG_BRAIN, MUT_BIG_BRAIN, MUT_BIG_BRAIN },
      { -33, -33, 0 } },
    { 1, { MUT_SHARP_SCALES, MUT_SHARP_SCALES, MUT_SHARP_SCALES },
      { -33, -33, 0 } },
    // Tier 2 facets
    { 2, { MUT_IGNITE_BLOOD, MUT_IGNITE_BLOOD, MUT_IGNITE_BLOOD },
      { -33, 0, 0 } },
    { 2, { MUT_CONDENSATION_SHIELD, MUT_ICEMAIL, MUT_ICEMAIL },
      { -33, 0, 0 } },
    { 2, { MUT_DEMONIC_MAGIC, MUT_DEMONIC_MAGIC, MUT_DEMONIC_MAGIC },
      { -33, 0, 0 } },
    { 2, { MUT_POWERED_BY_DEATH, MUT_POWERED_BY_DEATH, MUT_POWERED_BY_DEATH },
      { -33, 0, 0 } },
    { 2, { MUT_DEMONIC_GUARDIAN, MUT_DEMONIC_GUARDIAN, MUT_DEMONIC_GUARDIAN },
      { -33, 0, 0 } },
    { 2, { MUT_SPINY, MUT_SPINY, MUT_SPINY },
      { -33, 0, 0 } },
    { 2, { MUT_POWERED_BY_PAIN, MUT_POWERED_BY_PAIN, MUT_POWERED_BY_PAIN },
      { -33, 0, 0 } },
    { 2, { MUT_FOUL_STENCH, MUT_FOUL_STENCH, MUT_FOUL_STENCH },
      { -33, 0, 0 } },
    { 2, { MUT_MANA_REGENERATION, MUT_MANA_SHIELD, MUT_MANA_LINK },
      { -33, 0, 0 } },
    { 2, { MUT_FOUL_SHADOW, MUT_FOUL_SHADOW, MUT_FOUL_SHADOW },
      { -33, 0, 0 } },
    // Tier 3 facets
    { 3, { MUT_DEMONIC_WILL, MUT_TORMENT_RESISTANCE, MUT_HURL_DAMNATION },
      { 50, 50, 50 } },
    { 3, { MUT_ROBUST, MUT_ROBUST, MUT_ROBUST },
      { 50, 50, 50 } },
    { 3, { MUT_HEX_ENHANCER, MUT_BLACK_MARK, MUT_SILENCE_AURA },
      { 50, 50, 50 } },
    { 3, { MUT_AUGMENTATION, MUT_AUGMENTATION, MUT_AUGMENTATION },
      { 50, 50, 50 } },
    { 3, { MUT_CORRUPTING_PRESENCE, MUT_CORRUPTING_PRESENCE, MUT_WORD_OF_CHAOS },
      { 50, 50, 50 } },
};

static bool _works_at_tier(const facet_def& facet, int tier)
{
    return facet.tier == tier;
}

typedef decltype(facet_def().muts) mut_array_t;
static bool _slot_is_unique(const mut_array_t &mut,
                            set<const facet_def *> facets_used)
{
    set<equipment_slot> slots;

    // find the equipment slot(s) used by mut
    for (const body_facet_def &facet : _body_facets)
    {
        for (mutation_type slotmut : mut)
            if (facet.mut == slotmut)
                slots.insert(facet.slot);
    }

    if (slots.empty())
        return true;

    for (const facet_def *used : facets_used)
    {
        for (const body_facet_def &facet : _body_facets)
            if (facet.mut == used->muts[0] && slots.count(facet.slot))
                return false;
    }

    return true;
}

static vector<demon_mutation_info> _select_ds_mutations()
{
    int ct_of_tier[] = { 1, 1, 2, 1 };
    // 1 in 10 chance to create a monstrous set
    if (one_chance_in(10))
    {
        ct_of_tier[0] = 3;
        ct_of_tier[1] = 0;
    }

try_again:
    vector<demon_mutation_info> ret;

    ret.clear();
    int absfacet = 0;
    int elemental = 0;
    int cloud_producing = 0;
    int retaliation = 0;

    set<const facet_def *> facets_used;

    for (int tier = ARRAYSZ(ct_of_tier) - 1; tier >= 0; --tier)
    {
        for (int nfacet = 0; nfacet < ct_of_tier[tier]; ++nfacet)
        {
            const facet_def* next_facet;

            do
            {
                next_facet = &RANDOM_ELEMENT(_demon_facets);
            }
            while (!_works_at_tier(*next_facet, tier)
                   || facets_used.count(next_facet)
                   || !_slot_is_unique(next_facet->muts, facets_used));

            facets_used.insert(next_facet);

            for (int i = 0; i < 3; ++i)
            {
                mutation_type m = next_facet->muts[i];

                ret.emplace_back(m, next_facet->when[i], absfacet);

                if (i==0)
                {
                    if (m == MUT_CONDENSATION_SHIELD || m == MUT_IGNITE_BLOOD)
                        elemental++;

                    if (m == MUT_FOUL_STENCH || m == MUT_IGNITE_BLOOD)
                        cloud_producing++;

                    if (m == MUT_SPINY
                        || m == MUT_FOUL_STENCH
                        || m == MUT_FOUL_SHADOW)
                    {
                        retaliation++;
                    }
                }
            }

            ++absfacet;
        }
    }

    if (elemental > 1)
        goto try_again;

    if (cloud_producing > 1)
        goto try_again;

    if (retaliation > 1)
        goto try_again;

    return ret;
}

static vector<mutation_type>
_order_ds_mutations(vector<demon_mutation_info> muts)
{
    vector<mutation_type> out;
    vector<int> times;
    FixedVector<int, 1000> time_slots;
    time_slots.init(-1);
    for (unsigned int i = 0; i < muts.size(); i++)
    {
        int first = max(0, muts[i].when);
        int last = min(100, muts[i].when + 100);
        int k;
        do
        {
            k = 10 * first + random2(10 * (last - first));
        }
        while (time_slots[k] >= 0);
        time_slots[k] = i;
        times.push_back(k);

        // Don't reorder mutations within a facet.
        for (unsigned int j = i; j > 0; j--)
        {
            if (muts[j].facet == muts[j-1].facet && times[j] < times[j-1])
            {
                int earlier = times[j];
                int later = times[j-1];
                time_slots[earlier] = j-1;
                time_slots[later] = j;
                times[j-1] = earlier;
                times[j] = later;
            }
            else
                break;
        }
    }

    for (int time = 0; time < 1000; time++)
        if (time_slots[time] >= 0)
            out.push_back(muts[time_slots[time]].mut);

    return out;
}

static vector<player::demon_trait>
_schedule_ds_mutations(vector<mutation_type> muts)
{
    list<mutation_type> muts_left(muts.begin(), muts.end());

    list<int> slots_left;

    vector<player::demon_trait> out;

    for (int level = 2; level <= 27; ++level)
        slots_left.push_back(level);

    while (!muts_left.empty())
    {
        if (out.empty() // always give a mutation at XL 2
            || x_chance_in_y(muts_left.size(), slots_left.size()))
        {
            player::demon_trait dt;

            dt.level_gained = slots_left.front();
            dt.mutation     = muts_left.front();

            dprf("Demonspawn will gain %s at level %d",
                    _get_mutation_def(dt.mutation).short_desc, dt.level_gained);

            out.push_back(dt);

            muts_left.pop_front();
        }
        slots_left.pop_front();
    }

    return out;
}

void roll_demonspawn_mutations()
{
    // intentionally create the subgenerator either way, so that this has the
    // same impact on the current main rng for all chars.
    rng::subgenerator ds_rng;

    if (you.species != SP_DEMONSPAWN)
        return;
    you.demonic_traits = _schedule_ds_mutations(
                         _order_ds_mutations(
                         _select_ds_mutations()));
}

bool perma_mutate(mutation_type which_mut, int how_much, const string &reason)
{
    ASSERT(_is_valid_mutation(which_mut));
    ASSERT(!mut_check_conflict(which_mut, true));

    int cap = get_mutation_cap(which_mut);
    how_much = min(how_much, cap);

    int rc = 1;
    // clear out conflicting mutations
    int count = 0;
    while (rc == 1 && ++count < 100)
        rc = _handle_conflicting_mutations(which_mut, true, reason);
    ASSERT(rc == 0);

    int levels = 0;
    while (how_much-- > 0)
    {
        dprf("Perma Mutate %s: cap %d, total %d, innate %d", mutation_name(which_mut), cap,
            you.get_base_mutation_level(which_mut), you.get_innate_mutation_level(which_mut));
        if (you.get_base_mutation_level(which_mut, true, false, false) < cap
            && !mutate(which_mut, reason, false, true, false, false, MUTCLASS_INNATE))
        {
            dprf("Innate mutation failed.");
            break;
        }
        levels++;
    }

#ifdef DEBUG
    // don't validate permamutate directly on level regain; this is so that wizmode level change
    // functions can work correctly.
    if (you.experience_level >= you.max_level)
        validate_mutations(false);
#endif
    return levels > 0;
}

bool temp_mutate(mutation_type which_mut, const string &reason)
{
    return mutate(which_mut, reason, false, false, false, false, MUTCLASS_TEMPORARY);
}

bool temp_mutation_wanes()
{
    const int starting_tmuts = you.attribute[ATTR_TEMP_MUTATIONS];
    if (starting_tmuts == 0)
        return false;

    const int num_remove = min(starting_tmuts, random_range(2, 3));

    mprf(MSGCH_DURATION, T_("You feel the corruptions in your body subside %s."),
        (num_remove >= starting_tmuts ? "completely" : "somewhat"));

    for (int i = 0; i < num_remove; ++i)
        delete_temp_mutation(); // chooses randomly

    if (you.attribute[ATTR_TEMP_MUTATIONS] > 0)
        you.attribute[ATTR_TEMP_MUT_KILLS] = random_range(4, 7);
    else
        you.attribute[ATTR_TEMP_MUT_KILLS] = 0;
    ASSERT(you.attribute[ATTR_TEMP_MUTATIONS] < starting_tmuts);
    return true;
}

// Returns the number of *distinct* types of temporary mutations the player currently has.
int temp_mutation_count()
{
    int count = 0;
    for (int i = 0; i < NUM_MUTATIONS && count < you.attribute[ATTR_TEMP_MUTATIONS]; ++i)
        if (you.temp_mutation[i] > 0)
            ++count;

    return count;
}

/**
 * How mutated is the player?
 *
 * @param normal Whether to count normal mutations (default true).
 * @param silver Whether to count innate mutations that affect silver vulnerability (default false).
 * @param all_innate Whether to count all innate mutations (default false). Includes and supercedes \c silver.
 * @param temp Whether to count temporary mutations (default false).
 * @param levels Whether to add up mutation levels, as opposed to just counting number of mutations (default true).
 *
 * @return Either the number of matching mutations, or the sum of their levels, depending on \c levels.
 */
int player::how_mutated(bool normal, bool silver, bool all_innate, bool temp, bool levels) const
{
    int result = 0;

    for (int i = 0; i < NUM_MUTATIONS; ++i)
    {
        if (you.mutation[i])
        {
            // Infernal Marks should count for silver vulnerability despite
            // being permanent mutations.
            const bool innate = all_innate
                                 || silver
                                     && (is_makhleb_mark(static_cast<mutation_type>(i))
                                         || you.species == SP_DEMONSPAWN);
            int mut_level = get_base_mutation_level(static_cast<mutation_type>(i),
                                                    innate, temp, normal);

            // Ru sacrifices count as innate mutations, but should not make
            // demonspawn extra-vulnerable to silver.
            if (silver && !all_innate && mut_level > 0)
                mut_level -= you.sacrifices[i];

            if (levels)
                result += mut_level;
            else if (mut_level > 0)
                result++;
        }
    }

    ASSERT(result >= 0);
    return result;
}

bool player::has_any_mutations() const
{
    return how_mutated(true, true, true, true, true) > 0;
}

// Primary function to handle demonic guardians.
// Guardian tier is partially based on player experience level. This should
// allow players to get the mutation early without it going totally out of
// control.
void check_demonic_guardian()
{
    // Players hated by all monsters don't get guardians, so that they aren't
    // swarmed by hostile executioners whenever things get rough.
    if (you.allies_forbidden())
        return;

    const int mutlevel = you.get_mutation_level(MUT_DEMONIC_GUARDIAN);

    if (you.duration[DUR_DEMONIC_GUARDIAN] == 0)
    {
        monster_type mt;
        int guardian_str = mutlevel + div_rand_round(you.experience_level - 9, 9);

        switch (guardian_str)
        {
        case 1:
            mt = random_choose(MONS_WHITE_IMP, MONS_UFETUBUS,
                               MONS_IRON_IMP, MONS_SHADOW_IMP);
            break;
        case 2:
            mt = random_choose(MONS_ORANGE_DEMON, MONS_ICE_DEVIL,
                               MONS_RUST_DEVIL, MONS_HELLWING);
            break;
        case 3:
            mt = random_choose(MONS_SOUL_EATER, MONS_SMOKE_DEMON,
                               MONS_SIXFIRHY, MONS_SUN_DEMON);
            break;
        case 4:
            mt = random_choose(MONS_BALRUG, MONS_CACODEMON, MONS_SIN_BEAST,
                               MONS_ZYKZYL);
            break;
        case 5:
            mt = random_choose(MONS_EXECUTIONER, MONS_HELL_SENTINEL,
                               MONS_BRIMSTONE_FIEND);
            break;
        default:
            die("Invalid demonic guardian level: %d", mutlevel);
        }

        monster *guardian = create_monster(
            mgen_data(mt, BEH_FRIENDLY, you.pos(), MHITYOU,
                      MG_FORCE_BEH | MG_AUTOFOE).set_summoned(&you, 0, summ_dur(2)));

        if (!guardian)
            return;

        guardian->flags |= MF_NO_REWARD;
        guardian->flags |= MF_DEMONIC_GUARDIAN;

        // no more guardians for mutlevel+1 to mutlevel+20 turns
        you.duration[DUR_DEMONIC_GUARDIAN] = 10*(mutlevel + random2(20));

        mpr("一个恶魔守护者出现了！");
    }
}

/**
 * Update the map knowledge based on any monster detection sources the player
 * has.
 */
void check_monster_detect()
{
    int radius = player_monster_detect_radius();
    if (radius <= 0)
        return;

    for (radius_iterator ri(you.pos(), radius, C_SQUARE); ri; ++ri)
    {
        monster* mon = monster_at(*ri);
        map_cell& cell = env.map_knowledge(*ri);
        if (!mon)
        {
            if (cell.detected_monster())
                cell.clear_monster();
            continue;
        }
        if (mon->is_firewood())
            continue;

        // [ds] If the PC remembers the correct monster at this
        // square, don't trample it with MONS_SENSED. Forgetting
        // legitimate monster memory affects travel, which can
        // path around mimics correctly only if it can actually
        // *see* them in monster memory -- overwriting the mimic
        // with MONS_SENSED causes travel to bounce back and
        // forth, since every time it leaves LOS of the mimic, the
        // mimic is forgotten (replaced by MONS_SENSED).
        // XXX: since mimics were changed, is this safe to remove now?
        const monster_type remembered_monster = cell.monster();
        if (remembered_monster == mon->type)
            continue;

        const monster_type mc = mon->friendly() ? MONS_SENSED_FRIENDLY
            : have_passive(passive_t::detect_montier)
            ? ash_monster_tier(mon)
            : MONS_SENSED;

        env.map_knowledge(*ri).set_detected_monster(mc);

        // Don't bother warning the player (or interrupting autoexplore) about
        // friendly monsters or those known to be easy, or those recently
        // warned about
        if (mc == MONS_SENSED_TRIVIAL || mc == MONS_SENSED_EASY
            || mc == MONS_SENSED_FRIENDLY || mon->wont_attack()
            || testbits(mon->flags, MF_SENSED))
        {
            continue;
        }

        for (radius_iterator ri2(mon->pos(), 2, C_SQUARE); ri2; ++ri2)
        {
            if (you.see_cell(*ri2))
            {
                mon->flags |= MF_SENSED;
                interrupt_activity(activity_interrupt::sense_monster);
                break;
            }
        }
    }
}

int augmentation_amount()
{
    int amount = 0;
    const int level = you.get_mutation_level(MUT_AUGMENTATION);

    for (int i = 0; i < level; ++i)
    {
        if (you.hp >= ((i + level) * you.hp_max) / (2 * level))
            amount++;
    }

    return amount;
}

void reset_powered_by_death_duration()
{
    const int pbd_dur = random_range(2, 5);
    you.set_duration(DUR_POWERED_BY_DEATH, pbd_dur);
}

/// How much XP is required for your next [d]evolution mutation?
static int _evolution_mut_xp(bool malignant)
{
    int xp = exp_needed(you.experience_level + 1)
             - exp_needed(you.experience_level);
    if (malignant)
        return xp / 4;
    return xp;
}

/// Update you.attribute[ATTR_EVOL_XP].
void set_evolution_mut_xp(bool malignant)
{
    // Intentionally erase any 'excess' XP to avoid this triggering
    // too quickly in the early game after big XP gains.
    you.attribute[ATTR_EVOL_XP] = _evolution_mut_xp(malignant);
    dprf("setting evol XP to %d", you.attribute[ATTR_EVOL_XP]);
}

int protean_grace_amount()
{
    return min(you.how_mutated(true, false, false, true, false) - 1, 7);
}

const string bane_name(bane_type bane, bool dbkey)
{
    string short_name = bane_data[bane_index[bane]].name;

    if (dbkey)
    {
        if (starts_with(short_name, "the"))
            short_name = short_name.substr(4, short_name.length());

        return lowercase(short_name);
    }
    else
        return make_stringf("Bane of %s", short_name.c_str());
}

int bane_base_duration(bane_type bane)
{
    return bane_data[bane_index[bane]].duration;
}

const string bane_desc(bane_type bane)
{
    if (bane == BANE_DILETTANTE && you.banes[bane])
    {
        CrawlVector& vec = you.props[DILETTANTE_SKILL_KEY].get_vector();
        return make_stringf("Your skill with %s, %s, and %s is reduced.",
                    skill_name(static_cast<skill_type>(vec[0].get_int())),
                    skill_name(static_cast<skill_type>(vec[1].get_int())),
                    skill_name(static_cast<skill_type>(vec[2].get_int())));
    }

    return bane_data[bane_index[bane]].description;
}

/*
 * Given some name, return a bane type. Tries to match the short description as found in `bane-data.h`.
 * If `partial_matches` is set, it will fill the vector with any partial matches it finds. If there is exactly one,
 * will return this bane, otherwise, will fail.
 *
 * @param partial_matches   an optional pointer to a vector, in case the consumer wants to do something
 *                          with the partial match results (e.g. show them to the user). If this is `nullptr`,
 *                          will accept only exact matches.
 *
 * @return the bane type if successful, otherwise NUM_BANES if it can't find a single match.
 */
bane_type bane_from_name(string name, vector<bane_type> *partial_matches)
{
    bane_type bane = NUM_BANES;

    string spec = lowercase_string(name);

    for (int i = 0; i < NUM_BANES; ++i)
    {
        bane_type ban = static_cast<bane_type>(i);
        const string ban_name_c = bane_name(ban, true);
        if (ban_name_c.empty())
            continue;
        const string ban_name = lowercase_string(ban_name_c);

        if (spec == ban_name)
        {
            bane = ban;
            break;
        }

        if (partial_matches && strstr(ban_name.c_str(), spec.c_str()))
            partial_matches->push_back(ban);
    }

    // If only one matching bane, use that.
    if (partial_matches && bane == NUM_BANES && partial_matches->size() == 1)
        return (*partial_matches)[0];

    return bane;
}

static bool _bane_is_compatible(bane_type bane)
{
#if TAG_MAJOR_VERSION == 34
    if (bane == BANE_RECKLESS_REMOVED)
        return false;
#endif
    return true;
}

static bool _skill_sorter(const pair<skill_type, int>& a,
                          const pair<skill_type, int>& b)
{
    return a.second > b.second;
}

// Select skills to penalize by the Bane of the Dilettante.
// We select the highest weapon skill and the 2 highest 'magic' skills
// (including invocations and evocations, but not spellcasting).
static void _init_bane_dilettante()
{
    CrawlVector& sk = you.props[DILETTANTE_SKILL_KEY].get_vector();
    sk.clear();

    vector<pair<skill_type, int>> wp_skills;
    for (skill_type skill = SK_FIRST_WEAPON; skill <= SK_LAST_WEAPON; ++skill)
    {
        if (is_removed_skill(skill))
            continue;

        wp_skills.push_back({skill, you.skill(skill, 100, true, false)});
    }
    wp_skills.push_back({SK_UNARMED_COMBAT, you.skill(SK_UNARMED_COMBAT, 100, true, false)});

    vector<pair<skill_type, int>> mag_skills;
    for (skill_type skill = SK_FIRST_MAGIC_SCHOOL; skill <= SK_LAST_MAGIC; ++skill)
    {
        if (is_removed_skill(skill))
            continue;

        mag_skills.push_back({skill, you.skill(skill, 100, true, false)});
    }
    mag_skills.push_back({SK_EVOCATIONS, you.skill(SK_EVOCATIONS, 100, true, false)});
    mag_skills.push_back({SK_INVOCATIONS, you.skill(SK_INVOCATIONS, 100, true, false)});

    shuffle_array(wp_skills);
    shuffle_array(mag_skills);

    sort(wp_skills.begin(), wp_skills.end(), _skill_sorter);
    sort(mag_skills.begin(), mag_skills.end(), _skill_sorter);

    sk.push_back(wp_skills[0].first);
    sk.push_back(mag_skills[0].first);
    sk.push_back(mag_skills[1].first);
}

/**
 * Give the player a bane. If the player already suffers from the bane in
 * question, extend its duration.
 *
 * @param bane      The type of bane to give. If NUM_BANES, give an entirely
 *                  random bane that the player does not already have.
 * @param reason    The source of this bane (for note-taking)
 * @param duration  The duration (in XP-units) this bane will last. If 0, use
 *                  the default duration for this type of bane.
 * @param mult      A multiplier to the base duration this bane will last, as a
 *                  percentage. Defaults to 100.
 *
 * @return  Whether a bane was successfully added.
 */
bool add_bane(bane_type bane, string reason, int duration, int mult)
{
    if (bane == NUM_BANES)
    {
        vector<bane_type> candidates;
        for (int i = 0; i < NUM_BANES; ++i)
            if (you.banes[i] == 0 && _bane_is_compatible(static_cast<bane_type>(i)))
                candidates.push_back(static_cast<bane_type>(i));

        if (candidates.empty())
        {
            mprf("你已经受到了最大程度的折磨。");
            return false;
        }

        bane = candidates[random2(candidates.size())];
    }
    if (duration == 0)
        duration = bane_data[bane_index[bane]].duration;

    duration = duration * mult / 100;

    if (you.banes[bane] == 0)
        mprf(MSGCH_WARN, T_("%s torments you."), bane_name(bane).c_str());
    else
        mprf(MSGCH_WARN, T_("Your %s grows stronger."), bane_name(bane).c_str());

    you.banes[bane] += duration;

    // Choose which skills to penalty
    if (bane == BANE_DILETTANTE)
        _init_bane_dilettante();

    take_note(Note(NOTE_GET_BANE, bane, 0, reason));

    return true;
}

void remove_bane(bane_type bane)
{
    mprf(MSGCH_RECOVERY, T_("%s is lifted from you."), bane_name(bane).c_str());
    you.banes[bane] = 0;

    if (bane == BANE_MORTALITY)
        add_daction(DACT_BANE_MORTALITY_CLEANUP);

    take_note(Note(NOTE_LOSE_BANE, bane));
}

// Calculate how many XLs worth of XP it would take for the player to remove a
// specified bane. If they do not have the bane, this is calculated as if they
// had it for its default duration (as affected by mult)
int xl_to_remove_bane(bane_type bane, int mult)
{
    int progress = 0;
    int you_skill_cost_level = you.skill_cost_level;
    int you_xp = you.total_experience;

    const int cost_factor =
        (you.has_mutation(MUT_ACCURSED) || you.undead_state() != US_ALIVE) ? 2
                                                                           : 1;

    const int amount = you.banes[bane] > 0 ? you.banes[bane]
                                           : bane_data[bane_index[bane]].duration * mult / 100;
    const int bane_xp = amount * cost_factor;

    while (progress < bane_xp)
    {
        const int next_level = skill_cost_needed(you_skill_cost_level + 1);

        // max xp that can be added (or subtracted) in one pass of the loop
        int max_xp = abs(next_level - you_xp);
        const int cost = calc_skill_cost(you_skill_cost_level);
        // Maximum number of points to transfer in one go.
        // It's max_xp/cost rounded up.
        const int max_skp = max((max_xp + cost - 1) / cost, 1);

        skill_diff delta;
        delta.skill_points = min<int>(abs((bane_xp - progress)),
                                 max_skp);
        delta.experience = delta.skill_points * cost;

        progress += delta.skill_points;
        you_xp += delta.experience;
        you_skill_cost_level = calc_skill_cost_level(you_xp, you_skill_cost_level);
    }

    const int xp_diff = you_xp - you.total_experience;
    const int level_diff = xp_to_level_diff(xp_diff / 10, 10);

    return level_diff;
}

bool skill_has_dilettante_penalty(skill_type skill)
{
    if (!you.has_bane(BANE_DILETTANTE))
        return false;

    CrawlVector& sk = you.props[DILETTANTE_SKILL_KEY].get_vector();
    for (int i = 0; i < sk.size(); ++i)
        if (sk[i].get_int() == skill)
            return true;

    return false;
}

// Potentially apply one of several banes that have a chance to affect any new
// monster the player encounters.
void maybe_apply_bane_to_monster(monster& mons)
{
    if (mons.is_peripheral()
        || mons.is_summoned()
        || mons.attitude != ATT_HOSTILE
        || mons.temp_attitude() != ATT_HOSTILE)
    {
        return;
    }

    if (you.has_bane(BANE_PARADOX) && !mons.has_spell(SPELL_MANIFOLD_ASSAULT)
        && mons_has_attacks(mons)
        && one_chance_in(7))
    {
        simple_monster_message(mons, " is touched by paradox!");
        mons.add_ench(mon_enchant(ENCH_PARADOX_TOUCHED, nullptr, INFINITE_DURATION));
    }

    // Give this one out to entire groups at once, since it does surprisingly
    // little to be given to just one monster in an entire group, on average.
    if (you.has_bane(BANE_WARDING) && one_chance_in(6))
    {
        mons.add_ench(mon_enchant(ENCH_WARDING, nullptr, INFINITE_DURATION));

        // Cap the magnitude of number of things affects in extremely dense
        // situations, preferring
        int max_affected = 8;
        for (distance_iterator di(mons.pos(), true, true, LOS_RADIUS); di; ++di)
        {
            if (!mons.see_cell_no_trans(*di))
                continue;

            if (monster* mon2 = monster_at(*di))
            {
                if (!testbits(mon2->flags, MF_SEEN) && !mon2->is_peripheral()
                    && mon2->attitude == ATT_HOSTILE)
                {
                    mon2->add_ench(mon_enchant(ENCH_WARDING, nullptr, INFINITE_DURATION));
                    if (--max_affected == 0)
                        break;
                }
            }
        }
    }
}
