#include "AppHdr.h"

#include "god-conduct.h"

#include "areas.h"
#include "fprop.h"
#include "god-abil.h" // ru sac key
#include "god-item.h" // is_*_spell
#include "libutil.h"
#include "message.h"
#include "monster.h"
#include "options.h"
#include "mon-util.h"
#include "religion.h"
#include "state.h"
#include "stringutil.h" // uppercase_first
#include "tag-version.h"
#include "database.h"

#include <functional>

// Forward declarations.
static bool _god_likes_killing(const monster& victim);

/////////////////////////////////////////////////////////////////////
// god_conduct_trigger

god_conduct_trigger::god_conduct_trigger(
    conduct_type c, int pg, bool kn, const monster* vict)
  : conduct(c), pgain(pg), known(kn), victim(nullptr)
{
    if (vict)
    {
        victim.reset(new monster);
        *(victim.get()) = *vict;
    }
}

void god_conduct_trigger::set(conduct_type c, int pg, bool kn,
                              const monster* vict)
{
    conduct = c;
    pgain = pg;
    known = kn;
    victim.reset(nullptr);
    if (vict)
    {
        victim.reset(new monster);
        *victim.get() = *vict;
    }
}

god_conduct_trigger::~god_conduct_trigger()
{
    if (conduct != NUM_CONDUCTS)
        did_god_conduct(conduct, pgain, known, victim.get());
}

static const char *conducts[] =
{
    "",
    "Evil", "Holy", "Attack Holy", "Attack Neutral", "Attack Friend",
    "Kill Living", "Kill Undead", "Kill Demon", "Kill Natural Evil",
    "Kill Unclean", "Kill Chaotic", "Kill Wizard", "Kill Priest", "Kill Holy",
    "Kill Fast", "Banishment", "Spell Memorise", "Spell Cast",
    "Spell Practise", "Cannibalism", "Deliberate Mutation",
    "Cause Glowing", "Use Unclean", "Use Chaos",
#if TAG_MAJOR_VERSION == 34
    "Desecrate Orcish Remains", "Kill Slime",
#endif
    "Was Hasty",
#if TAG_MAJOR_VERSION == 34
    "Attack In Sanctuary",
#endif
    "Kill Nonliving", "Exploration",
    "Seen Monster", "Sacrificed Love", "Hurt Foe", "Use Wizardly Item",
};
COMPILE_CHECK(ARRAYSZ(conducts) == NUM_CONDUCTS);

string conduct_description(conduct_type conduct)
{
    return conducts[conduct];
}

/**
 * Change piety & add penance in response to a conduct.
 *
 * @param piety_change      The change in piety (+ or -) the conduct caused.
 * @param piety_denom       ???
 * @param penance           Penance caused by the conduct.
 * @param thing_done        The conduct in question. Used for debug info.
 */
static void _handle_piety_penance(int piety_change, int piety_denom,
                                  int penance, conduct_type thing_done)
{
    const int old_piety = you.raw_piety;
#ifndef DEBUG_DIAGNOSTICS
    UNUSED(thing_done);
    UNUSED(old_piety);
#endif

    if (piety_change > 0)
        gain_piety(piety_change, piety_denom);
    else
        dock_piety(div_rand_round(-piety_change, piety_denom), penance);

    // don't announce exploration piety unless you actually got a boost
    if ((piety_change || penance)
        && thing_done != DID_EXPLORATION || old_piety != you.raw_piety)
    {
        dprf("conduct: %s; piety: %d (%+d/%d); penance: %d (%+d)",
             conducts[thing_done],
             you.piety(), piety_change, piety_denom,
             you.penance[you.religion], penance);

    }
}

/**
 * Whether good gods that you follow are offended by you attacking a specific
 * holy monster.
 *
 * @param victim    The holy in question. (May be nullptr.)
 * @return          Whether DID_ATTACK_HOLY applies.
 */
static bool _attacking_holy_matters(const monster* victim)
{
    // Don't penalise the player for killing holies unless they were once
    // neutral, or were no-reward (e.g. created by wrath).
    return !victim
            || testbits(victim->flags, MF_NO_REWARD)
            || testbits(victim->flags, MF_WAS_NEUTRAL);
}

#if (__GNUC__ * 100 + __GNUC_MINOR__ < 408) && !defined(__clang__)
// g++ 4.7 incorrectly treats a function<> initialised from a null function
// pointer as non-empty.
typedef bool (*valid_victim_t)(const monster *);
typedef void (*special_piety_t)(int &piety, int &denom, const monster* victim);
#else
// But g++ 5.x seems to have problems converting lambdas into function pointers?
typedef function<bool (const monster *)> valid_victim_t;
typedef function<void (int &piety, int &denom, const monster* victim)>
    special_piety_t;
#endif

/// A definition of the way in which a god dislikes a conduct being taken.
struct dislike_response
{
    /// Description on god desc screen.
    const char* desc;
    /// Whether the god "strongly" dislikes doing this.
    bool really_dislike;
    /// Loss in piety for triggering this conduct; multiplied by 'level'.
    int piety_factor;
    /// Penance for triggering this conduct; multiplied by 'level'.
    int penance_factor;
    /// Something your god says when you accidentally triggered the conduct.
    /// Implies that unknowingly triggering the conduct is forgiven.
    const char *forgiveness_message;
    /// Something your god says when you trigger this conduct. May be nullptr.
    const char *message;
    /// A function that checks the victim of the conduct to see if the conduct
    /// should actually, really apply to it. If nullptr, all victims are valid.
    valid_victim_t valid_victim;
    /// A flat decrease to penance, after penance_factor is applied.
    int penance_offset;

    /// Apply this response to a given conduct, severity level, and victim.
    /// @param victim may be null.
    void operator()(conduct_type thing_done, int level, bool known,
                    const monster *victim)
    {
        // if the conduct filters on affected monsters, & the relevant monster
        // isn't valid, don't trigger the conduct's consequences.
        if (valid_victim && !valid_victim(victim))
            return;

        god_acting gdact;

        // If the player didn't have a way to know they were going to trigger
        // the conduct, and the god cares, print a message & bail.
        if (!known && forgiveness_message)
        {
            if (Options.language == lang_t::ZH)
            {
                string zh_msg = forgiveness_message;
                if (strstr(forgiveness_message, "inadvertent evil act"))
                    zh_msg = " 原谅了你无意中的邪恶行为，下不为例。";
                else if (strstr(forgiveness_message, "inadvertent chaotic act"))
                    zh_msg = " 原谅了你无意中的混乱行为，下不为例。";
                else if (strstr(forgiveness_message, "inadvertent holy act"))
                    zh_msg = " 原谅了你无意中的神圣行为，下不为例。";
                else if (strstr(forgiveness_message, "accidental hurry"))
                    zh_msg = " 原谅了你意外的匆忙行为，下不为例。";
                else if (strstr(forgiveness_message, "inadvertent attack on a neutral"))
                    zh_msg = " 原谅了你对中立者的无意攻击，下不为例。";
                else if (strstr(forgiveness_message, "inadvertent attack on an ally"))
                    zh_msg = " 原谅了你对盟友的无意攻击，下不为例。";
                simple_god_message(zh_msg.c_str());
            }
            else
                simple_god_message(forgiveness_message);
            return;
        }

        // trigger the actual effects of the conduct.

        // weird hack (to prevent spam?)
        if (you_worship(GOD_ZIN) && thing_done == DID_CAUSE_GLOWING)
        {
            static int last_glowing_lecture = -1;
            if (!level)
            {
                if (Options.language == lang_t::ZH)
                    simple_god_message(" 对你周围的变异光芒不太感兴趣。");
                else
                    simple_god_message(" is not enthusiastic about the "
                                       "mutagenic glow surrounding you.");
            }
            else if (last_glowing_lecture != you.num_turns)
            {
                last_glowing_lecture = you.num_turns;
                // Increase contamination within yellow glow.
                if (Options.language == lang_t::ZH)
                    simple_god_message(" 对你周围额外的变异光芒感到不满！");
                else
                    simple_god_message(" does not appreciate the extra "
                                       "mutagenic glow surrounding you!");
            }
        }

        // a message, if we have one...
        if (message)
            simple_god_message(message);

        // ...and piety/penance.
        const int piety_loss = max(0, piety_factor * level);
        const int penance = max(0, penance_factor * level
                                   + penance_offset);
        _handle_piety_penance(-piety_loss, 1, penance, thing_done);
    }
};

/// Zin and Ely's responses to evil actions. TODO: parameterize & merge w/TSO
static const dislike_response GOOD_EVIL_RESPONSE = {
    "you use evil magic or items", true,
    1, 1, " forgives your inadvertent evil act, just this once."
};

/// Zin and Ely's responses to the player attacking holy creatures.
static const dislike_response GOOD_ATTACK_HOLY_RESPONSE = {
    "you attack non-hostile holy beings", true,
    1, 1, nullptr, nullptr, _attacking_holy_matters
};

/// Good gods' response to the player killing holy creatures.
static const dislike_response GOOD_KILL_HOLY_RESPONSE = {
    "you kill non-hostile holy beings", true,
    3, 3, nullptr, nullptr, _attacking_holy_matters
};

/// TSO and Ely's response to the player attacking neutral monsters.
static const dislike_response GOOD_ATTACK_NEUTRAL_RESPONSE = {
    "you attack neutral beings", true,
    1, 1, " forgives your inadvertent attack on a neutral, just this once."
};

/// Various gods' response to attacking a pal.
static dislike_response _on_attack_friend(const char* desc)
{
    return
    {
        desc, true,
        1, 3, " forgives your inadvertent attack on an ally, just this once.",
        nullptr, [] (const monster* victim) -> bool {
            dprf("hates friend : %d", god_hates_attacking_friend(you.religion, *victim));
            return god_hates_attacking_friend(you.religion, *victim);
        }
    };
}

typedef map<conduct_type, dislike_response> peeve_map;

/// a per-god map of conducts to that god's angry reaction to those conducts.
static peeve_map divine_peeves[] =
{
    // GOD_NO_GOD
    peeve_map(),
    // GOD_ZIN,
    {
        { DID_ATTACK_HOLY, GOOD_ATTACK_HOLY_RESPONSE },
        { DID_KILL_HOLY, GOOD_KILL_HOLY_RESPONSE },
        { DID_EVIL, GOOD_EVIL_RESPONSE },
        { DID_ATTACK_FRIEND, _on_attack_friend("you attack allies") },
        { DID_ATTACK_NEUTRAL, {
            "you attack neutral beings", false,
            1, 0,
            " forgives your inadvertent attack on a neutral, just this once."
        } },
        { DID_UNCLEAN, {
            "you use unclean or chaotic magic or items", true,
            1, 1, " forgives your inadvertent unclean act, just this once."
        } },
        { DID_CHAOS, {
            "you polymorph monsters", true,
            1, 1, " forgives your inadvertent chaotic act, just this once."
        } },
        { DID_DELIBERATE_MUTATING, {
            "you deliberately mutate or transform yourself", true,
            1, 0, " forgives your inadvertent chaotic act, just this once."
        } },
        { DID_CAUSE_GLOWING, { nullptr, false, 1 } },
    },
    // GOD_SHINING_ONE,
    {
        { DID_ATTACK_HOLY, {
            "you attack non-hostile holy beings", true,
            1, 2, nullptr, nullptr, _attacking_holy_matters
        } },
        { DID_KILL_HOLY, GOOD_KILL_HOLY_RESPONSE },
        { DID_EVIL, {
            "you use evil magic or items", true,
            1, 2, " forgives your inadvertent evil act, just this once."
        } },
        { DID_ATTACK_NEUTRAL, GOOD_ATTACK_NEUTRAL_RESPONSE },
        { DID_ATTACK_FRIEND, _on_attack_friend("you attack allies") },
    },
    // GOD_KIKUBAAQUDGHA,
    peeve_map(),
    // GOD_YREDELEMNUL,
    {
        { DID_HOLY, {
            "you use holy magic or items", true,
            1, 2, " forgives your inadvertent holy act, just this once."
        } },
    },
    // GOD_XOM,
    peeve_map(),
    // GOD_VEHUMET,
    peeve_map(),
    // GOD_OKAWARU,
    peeve_map(),
    // GOD_MAKHLEB,
    peeve_map(),
    // GOD_SIF_MUNA,
    peeve_map(),
    // GOD_TROG,
    {
        { DID_SPELL_MEMORISE, {
            "you memorise spells", true,
            10, 10
        } },
        { DID_SPELL_CASTING, {
            "you attempt to cast spells", true,
            1, 5,
        } },
        { DID_SPELL_PRACTISE, {
            "you train magic skills", true,
            1, 0, nullptr, " does not appreciate your training of magic skills!"
        } },
        { DID_WIZARDLY_ITEM, {
            "you use magical staves or other wizardly items", true,
            1, 0, nullptr, " does not appreciate your use of wizardly items!"
        } },
    },
    // GOD_NEMELEX_XOBEH,
    peeve_map(),
    // GOD_ELYVILON,
    {
        { DID_ATTACK_HOLY, GOOD_ATTACK_HOLY_RESPONSE },
        { DID_KILL_HOLY, GOOD_KILL_HOLY_RESPONSE },
        { DID_EVIL, GOOD_EVIL_RESPONSE },
        { DID_ATTACK_NEUTRAL, GOOD_ATTACK_NEUTRAL_RESPONSE },
        { DID_ATTACK_FRIEND, _on_attack_friend("you attack allies") },
    },
    // GOD_LUGONU,
    peeve_map(),
    // GOD_BEOGH,
    {
        { DID_ATTACK_NEUTRAL, {
            "you attack non-hostile orcs", true,
            1, 1, nullptr, nullptr, [] (const monster* victim) -> bool {
                return victim
                    && mons_genus(victim->type) == MONS_ORC
                    && !victim->is_shapeshifter();
            }
        } },
        { DID_ATTACK_FRIEND, _on_attack_friend("you attack your followers") },
    },
    // GOD_JIYVA,
    peeve_map(),
    // GOD_FEDHAS,
    peeve_map(),
    // GOD_CHEIBRIADOS,
    {
        { DID_HASTY, {
            "you hasten yourself or others", true,
            1, 1, " forgives your accidental hurry, just this once.",
            " thinks you should slow down.", nullptr, -5
        } },
    },
    // GOD_ASHENZARI,
    peeve_map(),
    // GOD_DITHMENOS,
    peeve_map(),
    // GOD_GOZAG,
    peeve_map(),
    // GOD_QAZLAL,
    peeve_map(),
    // GOD_RU,
    peeve_map(),
#if TAG_MAJOR_VERSION == 34
    // GOD_PAKELLAS
    peeve_map(),
#endif
    // GOD_USKAYAW,
    peeve_map(),
    // GOD_HEPLIAKLQANA,
    peeve_map(),
    // GOD_WU_JIAN,
    peeve_map(),
    // GOD_IGNIS,
    peeve_map(),
};

/// Map of English conduct descriptions to Chinese translations.
static const map<string, string> _conduct_desc_zh = {
    // divine_prohibitions desc
    {"using evil magic or items", "使用邪恶魔法或物品"},
    {"using chaotic magic or items", "使用混乱魔法或物品"},
    {"mutating or transforming yourself or others", "变异或变形自己或他人"},
    {"using holy magic or items", "使用神圣魔法或物品"},
    {"casting or memorising spells", "施放或记忆法术"},
    {"training magic skills", "训练魔法技能"},
    {"using magical staves or other wizardly items", "使用魔法法杖或其他法师物品"},
    {"hastening yourself or using unnaturally quick items", "加速自己或使用异常快速的物品"},
    // divine_peeves desc
    {"you attack non-hostile holy beings", "你攻击非敌意的神圣生物"},
    {"you kill non-hostile holy beings", "你杀死非敌意的神圣生物"},
    {"you attack neutral beings", "你攻击中立生物"},
    {"you attack allies", "你攻击盟友"},
    {"you attack your followers", "你攻击你的追随者"},
    {"you attack non-hostile orcs", "你攻击非敌意的兽人"},
    // divine_likes desc
    {"you kill living beings", "你杀死活物"},
    {"you destroy the undead", "你摧毁亡灵"},
    {"you kill demons", "你杀死恶魔"},
    {"you kill holy beings", "你杀死神圣生物"},
    {"you destroy nonliving beings", "你摧毁非生物体"},
    {"you kill unclean or chaotic beings", "你杀死不洁或混乱生物"},
    {"you kill the undead", "你杀死亡灵"},
    {"you kill evil beings", "你杀死邪恶生物"},
    {"you encounter other hostile creatures", "你遭遇其他敌意生物"},
    {"you explore the world", "你探索世界"},
    {"you explore the world outside of the Slime Pits", "你探索黏坑之外的世界"},
    {"you hurt your foes; however, effects that cause damage over "
     "time do not interest Uskayaw", "你伤害敌人；然而，持续伤害效果不引起乌斯卡亚的兴趣"},
    {"you kill the priests of other religions", "你杀死其他宗教的祭司"},
    {"you kill wizards and other users of magic", "你杀死法师和其他魔法使用者"},
    {"you kill non-sluggish things", "你杀死不迟缓的生物"},
    {"you banish creatures to the Abyss", "你将生物放逐到深渊"},
};

/// Look up the Chinese translation for a conduct description, if available.
static const char* _zh_conduct(const char* en)
{
    if (!en || !en[0] || Options.language != lang_t::ZH)
        return en;
    auto it = _conduct_desc_zh.find(en);
    return it != _conduct_desc_zh.end() ? it->second.c_str() : en;
}

string get_god_dislikes(god_type which_god)
{
    // Return early for the special cases.
    if (which_god == GOD_NO_GOD || which_god == GOD_XOM)
        return "";

    string text;
    vector<string> dislikes;        // Piety loss
    vector<string> really_dislikes; // Penance

    for (const auto& entry : divine_peeves[which_god])
    {
        // Trog forgives Gnolls practising spellcasting since they do it
        // without choice. XXX: Rework the peeve_map to allow checking this.
        if (which_god == GOD_TROG
            && you.has_mutation(MUT_DISTRIBUTED_TRAINING)
            && entry.first == DID_SPELL_PRACTISE)
        {
            continue;
        }

        if (entry.second.desc)
        {
            const char* desc = _zh_conduct(entry.second.desc);
            if (entry.second.really_dislike)
                really_dislikes.emplace_back(desc);
            else
                dislikes.emplace_back(desc);
        }
    }

    if (which_god == GOD_CHEIBRIADOS)
        really_dislikes.emplace_back("use unnaturally quick items");

    if (dislikes.empty() && really_dislikes.empty())
        return "";

    if (!dislikes.empty())
    {
        text += uppercase_first(god_name(which_god));
        if (Options.language == lang_t::ZH)
        {
            text += "讨厌当";
            text += comma_separated_line(dislikes.begin(), dislikes.end(),
                                         "或", "、");
            text += "。";
        }
        else
        {
            text += " dislikes it when ";
            text += comma_separated_line(dislikes.begin(), dislikes.end(),
                                         " or ", ", ");
            text += ".";
        }

        if (!really_dislikes.empty())
            text += " ";
    }

    if (!really_dislikes.empty())
    {
        text += uppercase_first(god_name(which_god));
        if (Options.language == lang_t::ZH)
        {
            text += "非常讨厌当";
            text += comma_separated_line(really_dislikes.begin(),
                                         really_dislikes.end(),
                                         "或", "、");
            text += "。";
        }
        else
        {
            text += " strongly dislikes it when ";
            text += comma_separated_line(really_dislikes.begin(),
                                         really_dislikes.end(),
                                         " or ", ", ");
            text += ".";
        }
    }

    return text;
}

/// A definition of the way in which a god likes a conduct being taken.
struct like_response
{
    /// How to describe this conduct on the god description screen.
    const char* desc;
    /// Whether the god should be described as "especially" liking it.
    bool really_like;
    /** Gain in piety for triggering this conduct; added to calculated denom.
     *
     * This number is usually negative. In that case, the maximum piety gain
     * is one point, and the chance of *not* getting that point is:
     *    -piety_bonus/(piety_denom_bonus + level - you.xl/xl_denom)
     * (omitting the you.xl term if xl_denom is zero)
     */
    int piety_bonus;
    /// Divider for piety gained by this conduct; added to 'level'.
    int piety_denom_bonus;
    /// Degree to which your XL modifies piety gained. If zero, do not
    /// modify piety by XL; otherwise divide player XL by this value.
    int xl_denom;
    /// Something your god says when you trigger this conduct. May be nullptr.
    const char *message;
    /// Special-case code for weird likes. May modify piety bonus/denom, or
    /// may have other side effects. If nullptr, doesn't trigger, ofc.
    special_piety_t special;

    /// Apply this response to a given conduct, severity level, and victim.
    /// @param victim may be null.
    void operator()(conduct_type thing_done, int level, bool /*known*/,
                    const monster *victim)
    {
        // if the conduct filters on affected monsters, & the relevant monster
        // isn't valid, don't trigger the conduct's consequences.
        if (victim && !_god_likes_killing(*victim))
            return;

        god_acting gdact;

        if (message)
        {
            if (Options.language == lang_t::ZH)
            {
                string zh_msg = message;
                if (strstr(message, "accepts your kill"))
                    zh_msg = " 接受了你的杀戮。";
                else if (strstr(message, "killing of a magic user"))
                    zh_msg = " 对你杀死魔法使用者表示赞赏。";
                else if (strstr(message, "claims a new guest"))
                    zh_msg = " 又收纳了一位新客人。";
                else if (strstr(message, "killing of a heretic priest"))
                    zh_msg = " 对你杀死异端牧师表示赞赏。";
                simple_god_message(zh_msg.c_str());
            }
            else
                simple_god_message(message);
        }

        // this is all very strange, but replicates legacy behaviour.
        // See the comment on piety_bonus above.
        int denom = piety_denom_bonus + level;
        if (xl_denom)
            denom -= you.get_experience_level() / xl_denom;

        int gain = denom + piety_bonus;

        // handle weird special cases
        // may modify gain/denom
        if (special)
            special(gain, denom, victim);
        you.piety_info.record_conduct_like(thing_done, gain, denom);

        _handle_piety_penance(max(0, gain), max(1, denom), 0, thing_done);
    }
};

/**
 * The piety bonus that is given for killing monsters of the appropriate
 * holiness.
 *
 * Gets slotted into a very strange equation. It's weird.
 */
static int _piety_bonus_for_holiness(mon_holy_type holiness)
{
    if (holiness & (MH_NATURAL | MH_PLANT | MH_NONLIVING))
        return -6;
    else if (holiness & MH_UNDEAD)
        return -5;
    else if (holiness & MH_DEMONIC)
        return -4;
    else if (holiness & MH_HOLY)
        return -3;
    else
        die("unknown holiness type; can't give a bonus");
}

/**
 * Generate an appropriate kill response (piety gain scaling, message, &c),
 * for gods that like killing this sort of thing.
 *
 * @param holiness      The holiness of the relevant type of monsters.
 * @param god_is_good   Whether this is a good god.
 *                      (They don't scale piety with XL in the same way...?)
 * @param special       A special-case function.
 * @return              An appropriate like_response.
 */
static like_response _on_kill(const char* desc, mon_holy_type holiness,
                              bool god_is_good = false,
                              special_piety_t special = nullptr,
                              bool really_like = false)
{
    return {
        desc,
        really_like,
        _piety_bonus_for_holiness(holiness),
        18,
        god_is_good ? 0 : 2,
        " accepts your kill.",
        special
    };
}

/// Response for gods that like killing the living.
static const like_response KILL_LIVING_RESPONSE =
    _on_kill("you kill living beings", MH_NATURAL);

/// Response for non-good gods that like killing (?) undead.
static const like_response KILL_UNDEAD_RESPONSE =
    _on_kill("you destroy the undead", MH_UNDEAD);

/// Response for non-good gods that like killing (?) demons.
static const like_response KILL_DEMON_RESPONSE =
    _on_kill("you kill demons", MH_DEMONIC);

/// Response for non-good gods that like killing (?) holies.
static const like_response KILL_HOLY_RESPONSE =
    _on_kill("you kill holy beings", MH_HOLY);

/// Response for non-good gods that like killing (?) nonliving enemies.
static const like_response KILL_NONLIVING_RESPONSE =
    _on_kill("you destroy nonliving beings", MH_NONLIVING);

// Note that holy deaths are special - they're always noticed...
// If you or any friendly kills one, you'll get the credit/blame.

static like_response okawaru_kill(const char* desc)
{
    return
    {
        desc, false,
        0, 0, 0, nullptr, [] (int &piety, int &denom, const monster* victim)
        {
            piety = get_fuzzied_monster_difficulty(*victim);
            dprf("fuzzied monster difficulty: %4.2f", piety * 0.01);
            denom = 550;

            if (piety > 3200)
            {
                if (Options.language == lang_t::ZH)
                    mprf(MSGCH_GOD, you.religion,
                         "<white>%s因你的杀戮而感到荣耀。</white>",
                         uppercase_first(god_name(you.religion)).c_str());
                else
                    mprf(MSGCH_GOD, you.religion,
                         "<white>%s is honoured by your kill.</white>",
                         uppercase_first(god_name(you.religion)).c_str());
            }
            else if (piety > 9) // might still be miniscule
            {
                if (Options.language == lang_t::ZH)
                    simple_god_message(" 接受了你的杀戮。");
                else
                    simple_god_message(" accepts your kill.");
            }
        }
    };
}

static const like_response _fedhas_kill_living_response()
{
    return
    {
        "you kill living beings", false,
        _piety_bonus_for_holiness(MH_NATURAL), 18, 0,
        nullptr, [] (int &, int &, const monster* victim)
        {
            if (victim && mons_class_can_leave_corpse(mons_species(victim->type)))
            {
                if (Options.language == lang_t::ZH)
                    simple_god_message(" 对你为生态系统做出的贡献表示赞赏。");
                else
                    simple_god_message(" appreciates your contribution to the ecosystem.");
            }
            else
            {
                if (Options.language == lang_t::ZH)
                    simple_god_message(" 接受了你的杀戮。");
                else
                    simple_god_message(" accepts your kill.");
            }
        }
    };
}

static const like_response _yred_kill_response()
{
    return
    {
        nullptr, false,
        _piety_bonus_for_holiness(MH_NATURAL), 18, 0,
        nullptr, [] (int &piety, int &, const monster* victim)
        {
            if (victim)
            {
                if (!yred_torch_is_raised())
                {
                    piety = 0;
                    //Print a reminder if the torch isn't lit, but *could* be
                    if (yred_cannot_light_torch_reason().empty())
                    {
                        if (Options.language == lang_t::ZH)
                            mprf(MSGCH_GOD, "你的火炬未点燃，%s的灵魂白白浪费了……",
                                 you.can_see(*victim) ? victim->pronoun(PRONOUN_POSSESSIVE).c_str() : "一个");
                        else
                            mprf(MSGCH_GOD, "With your torch unlit, %s soul goes wasted...",
                                 you.can_see(*victim) ? victim->pronoun(PRONOUN_POSSESSIVE).c_str() : "a");
                    }
                }
                else
                {
                    if (Options.language == lang_t::ZH)
                    {
                        const string zh_prefix = you.can_see(*victim)
                            ? "其" : "一个";
                        const char* zh_adj = mons_is_unique(victim->type)
                            ? "强大的" : victim->holiness() & MH_HOLY
                            ? "未被玷污的" : "";
                        mprf(MSGCH_GOD, "%s%s灵魂化为了火炬的燃料。",
                             zh_prefix.c_str(), zh_adj);
                    }
                    else
                        mprf(MSGCH_GOD, "%s %ssoul becomes fuel for the torch.",
                             you.can_see(*victim) ? victim->pronoun(PRONOUN_POSSESSIVE).c_str() : "A",
                             mons_is_unique(victim->type) ? "potent "
                                 : victim->holiness() & MH_HOLY ? "unsullied " : "");

                    if (mons_is_unique(victim->type))
                        piety *= 3;

                    if (victim->holiness() & MH_HOLY)
                        piety *= 2;
                }
            }
        }
    };
}

static const like_response EXPLORE_RESPONSE = {
    "you explore the world", false,
    0, 0, 0, nullptr,
    [] (int &piety, int &/*denom*/, const monster* /*victim*/)
    {
        // piety = denom = level at the start of the function
        piety = 14;
    }
};


typedef map<conduct_type, like_response> like_map;

/// a per-god map of conducts to piety rewards given by that god.
static like_map divine_likes[] =
{
    // GOD_NO_GOD
    like_map(),
    // GOD_ZIN,
    {
        { DID_KILL_UNCLEAN, _on_kill("you kill unclean or chaotic beings", MH_DEMONIC, true) },
        { DID_KILL_CHAOTIC, _on_kill(nullptr, MH_DEMONIC, true) },
    },
    // GOD_SHINING_ONE,
    {
        { DID_KILL_UNDEAD, _on_kill("you kill the undead", MH_UNDEAD, true) },
        { DID_KILL_DEMON, _on_kill("you kill demons", MH_DEMONIC, true) },
        { DID_KILL_NATURAL_EVIL, _on_kill("you kill evil beings", MH_DEMONIC, true) },
        { DID_SEE_MONSTER, {
            "you encounter other hostile creatures", false,
            0, 0, 0, nullptr, [] (int &piety, int &denom, const monster* victim)
            {
                // don't give piety for seeing things we get piety for killing.
                if (victim && victim->evil())
                    return;

                const int level = denom; // also = piety
                denom = level / 2 + 6 - you.experience_level / 4;
                piety = denom - 4;
            }
        } },
    },
    // GOD_KIKUBAAQUDGHA,
    {
        { DID_KILL_LIVING, KILL_LIVING_RESPONSE },
        { DID_KILL_UNDEAD, KILL_UNDEAD_RESPONSE },
        { DID_KILL_DEMON, KILL_DEMON_RESPONSE },
        { DID_KILL_HOLY, KILL_HOLY_RESPONSE },
        { DID_KILL_NONLIVING, KILL_NONLIVING_RESPONSE },
    },
    // GOD_YREDELEMNUL,
    {
        { DID_KILL_LIVING, _yred_kill_response() },
        { DID_KILL_DEMON, _yred_kill_response() },
        { DID_KILL_HOLY, _yred_kill_response() },
    },
    // GOD_XOM,
    like_map(),
    // GOD_VEHUMET,
    {
        { DID_KILL_LIVING, KILL_LIVING_RESPONSE },
        { DID_KILL_UNDEAD, KILL_UNDEAD_RESPONSE },
        { DID_KILL_DEMON, KILL_DEMON_RESPONSE },
        { DID_KILL_HOLY, KILL_HOLY_RESPONSE },
        { DID_KILL_NONLIVING, KILL_NONLIVING_RESPONSE },
    },
    // GOD_OKAWARU,
    {
        { DID_KILL_LIVING, okawaru_kill("you kill living beings") },
        { DID_KILL_UNDEAD, okawaru_kill("you destroy the undead") },
        { DID_KILL_DEMON, okawaru_kill("you kill demons") },
        { DID_KILL_HOLY, okawaru_kill("you kill holy beings") },
        { DID_KILL_NONLIVING, okawaru_kill("you destroy nonliving beings") },
    },
    // GOD_MAKHLEB,
    {
        { DID_KILL_LIVING, KILL_LIVING_RESPONSE },
        { DID_KILL_UNDEAD, KILL_UNDEAD_RESPONSE },
        { DID_KILL_DEMON, KILL_DEMON_RESPONSE },
        { DID_KILL_HOLY, KILL_HOLY_RESPONSE },
        { DID_KILL_NONLIVING, KILL_NONLIVING_RESPONSE },
    },
    // GOD_SIF_MUNA,
    {
        { DID_KILL_LIVING, KILL_LIVING_RESPONSE },
        { DID_KILL_UNDEAD, KILL_UNDEAD_RESPONSE },
        { DID_KILL_DEMON, KILL_DEMON_RESPONSE },
        { DID_KILL_HOLY, KILL_HOLY_RESPONSE },
        { DID_KILL_NONLIVING, KILL_NONLIVING_RESPONSE },
    },
    // GOD_TROG,
    {
        { DID_KILL_LIVING, KILL_LIVING_RESPONSE },
        { DID_KILL_UNDEAD, KILL_UNDEAD_RESPONSE },
        { DID_KILL_DEMON, KILL_DEMON_RESPONSE },
        { DID_KILL_HOLY, KILL_HOLY_RESPONSE },
        { DID_KILL_NONLIVING, KILL_NONLIVING_RESPONSE },
        { DID_KILL_WIZARD, {
            "you kill wizards and other users of magic", true,
            -6, 10, 0, " appreciates your killing of a magic user."
        } },
    },
    // GOD_NEMELEX_XOBEH,
    {
        { DID_EXPLORATION, EXPLORE_RESPONSE },
    },
    // GOD_ELYVILON,
    {
        { DID_EXPLORATION, {
            "you explore the world", false,
            0, 0, 0, nullptr,
            [] (int &piety, int &/*denom*/, const monster* /*victim*/)
            {
                // piety = denom = level at the start of the function
                piety = 20;
            }
        } },
    },
    // GOD_LUGONU,
    {
        { DID_KILL_LIVING, KILL_LIVING_RESPONSE },
        { DID_KILL_UNDEAD, KILL_UNDEAD_RESPONSE },
        { DID_KILL_DEMON, KILL_DEMON_RESPONSE },
        { DID_KILL_HOLY, KILL_HOLY_RESPONSE },
        { DID_KILL_NONLIVING, KILL_NONLIVING_RESPONSE },
        { DID_BANISH, {
            "you banish creatures to the Abyss", false,
            -6, 18, 2, " claims a new guest."
        } },
    },
    // GOD_BEOGH,
    {
        { DID_KILL_LIVING, KILL_LIVING_RESPONSE },
        { DID_KILL_UNDEAD, KILL_UNDEAD_RESPONSE },
        { DID_KILL_DEMON, KILL_DEMON_RESPONSE },
        { DID_KILL_HOLY, KILL_HOLY_RESPONSE },
        { DID_KILL_NONLIVING, KILL_NONLIVING_RESPONSE },
        { DID_KILL_PRIEST, {
            "you kill the priests of other religions", true,
            -6, 18, 0, " appreciates your killing of a heretic priest."
        } },
    },
    // GOD_JIYVA,
    {
        { DID_EXPLORATION, {
            "you explore the world outside of the Slime Pits", false,
            0, 0, 0, nullptr,
            [] (int &piety, int &/*denom*/, const monster* /*victim*/)
            {
                // piety = denom = level at the start of the function
                piety = 26;
            }
        } },
    },
    // GOD_FEDHAS,
    {
        { DID_KILL_LIVING, _fedhas_kill_living_response() },
        { DID_KILL_UNDEAD, KILL_UNDEAD_RESPONSE },
        { DID_KILL_DEMON, KILL_DEMON_RESPONSE },
        { DID_KILL_HOLY, KILL_HOLY_RESPONSE },
        { DID_KILL_NONLIVING, KILL_NONLIVING_RESPONSE },
    },
    // GOD_CHEIBRIADOS,
    {
        { DID_KILL_FAST, {
            "you kill non-sluggish things", false,
            -6, 18, 2, nullptr,
            [] (int &piety, int &/*denom*/, const monster* victim)
            {
                const int mons_speed = mons_base_speed(*victim);
                dprf("Chei DID_KILL_FAST: %s base speed: %d",
                     victim->name(DESC_PLAIN, true).c_str(),
                     mons_speed);

                // Scale piety up a bit in general.
                piety = div_rand_round(4 * piety, 3);

                // Double piety for speedy monsters sometimes
                if (mons_speed > 10 && x_chance_in_y(mons_speed - 10, 10))
                {
                    if (Options.language == lang_t::ZH)
                        simple_god_message(" 非常欣赏这种节奏的变化。");
                    else
                        simple_god_message(" thoroughly appreciates the change of pace.");
                    piety *= 2;
                }
                else
                {
                    if (Options.language == lang_t::ZH)
                        simple_god_message(" 欣赏这种节奏的变化。");
                    else
                        simple_god_message(" appreciates the change of pace.");
                }
            }
        } }
    },
    // GOD_ASHENZARI,
    {
        { DID_EXPLORATION, {
            nullptr, false, 0, 0, 0, nullptr,
            [] (int &piety, int &denom, const monster* /*victim*/)
            {
                piety = 0;
                denom = 1;

                ASSERT(you.props.exists(ASHENZARI_CURSE_PROGRESS_KEY));

                if (one_chance_in(100))
                    you.props[ASHENZARI_CURSE_PROGRESS_KEY].get_int()++;
            }
        } },
    },
    // GOD_DITHMENOS,
    {
        { DID_EXPLORATION, {
            "you explore the world", false,
            0, 0, 0, nullptr,
            [] (int &piety, int &/*denom*/, const monster* /*victim*/)
            {
                // piety = denom = level at the start of the function
                piety = 18;
            }
        } },
    },
    // GOD_GOZAG,
    like_map(),
    // GOD_QAZLAL,
    {
        { DID_KILL_LIVING, KILL_LIVING_RESPONSE },
        { DID_KILL_UNDEAD, KILL_UNDEAD_RESPONSE },
        { DID_KILL_DEMON, KILL_DEMON_RESPONSE },
        { DID_KILL_HOLY, KILL_HOLY_RESPONSE },
        { DID_KILL_NONLIVING, KILL_NONLIVING_RESPONSE },
    },
    // GOD_RU,
    {
        { DID_EXPLORATION, {
            nullptr, false, 0, 0, 0, nullptr,
            [] (int &piety, int &denom, const monster* /*victim*/)
            {
                piety = 0;
                denom = 1;

                ASSERT(you.props.exists(RU_SACRIFICE_PROGRESS_KEY));

                if (one_chance_in(100))
                    you.props[RU_SACRIFICE_PROGRESS_KEY].get_int()++;
            }
        } },
    },
#if TAG_MAJOR_VERSION == 34
    // GOD_PAKELLAS,
    {
        { DID_KILL_LIVING, _on_kill("you kill living beings", MH_NATURAL, false,
                                  [](int &piety, int &denom,
                                     const monster* /*victim*/)
            {
                piety *= 4;
                denom *= 3;
            }
        ) },
        { DID_KILL_UNDEAD, KILL_UNDEAD_RESPONSE },
        { DID_KILL_DEMON, KILL_DEMON_RESPONSE },
        { DID_KILL_HOLY, KILL_HOLY_RESPONSE },
        { DID_KILL_NONLIVING, KILL_NONLIVING_RESPONSE },
    },
#endif
    // GOD_USKAYAW
    {
        { DID_HURT_FOE, {
            "you hurt your foes; however, effects that cause damage over "
            "time do not interest Uskayaw", true, 1, 1, 0, nullptr,
            [] (int &/*piety*/, int &denom, const monster* /*victim*/)
            {
                denom = 1;
            }
        } },
    },
    // GOD_HEPLIAKLQANA
    {
        { DID_EXPLORATION, EXPLORE_RESPONSE },
    },
    // GOD_WU_JIAN
    {
        { DID_KILL_LIVING, KILL_LIVING_RESPONSE },
        { DID_KILL_UNDEAD, KILL_UNDEAD_RESPONSE },
        { DID_KILL_DEMON, KILL_DEMON_RESPONSE },
        { DID_KILL_HOLY, KILL_HOLY_RESPONSE },
        { DID_KILL_NONLIVING, KILL_NONLIVING_RESPONSE },
    },
    // GOD_IGNIS,
    like_map(),
};

/**
 * Will your god give you piety for killing the given monster, assuming that
 * its death triggers a conduct that the god sometimes likes?
 */
static bool _god_likes_killing(const monster& victim)
{
    return !god_hates_attacking_friend(you.religion, victim);
}

static void _handle_your_gods_response(conduct_type thing_done, int level,
                                       bool known, const monster* victim)
{
    COMPILE_CHECK(ARRAYSZ(divine_peeves) == NUM_GODS);
    COMPILE_CHECK(ARRAYSZ(divine_likes) == NUM_GODS);

    // Lucy gives no piety in Abyss. :(
    // XXX: make this not a hack...? (or remove it?)
    if (you_worship(GOD_LUGONU) && player_in_branch(BRANCH_ABYSS))
        return;

    // Trog forgives Gnolls practising spellcasting since they do it without
    // choice. XXX: Rework the peeve_map to allow checking this.
    if (you_worship(GOD_TROG)
        && you.has_mutation(MUT_DISTRIBUTED_TRAINING)
        && thing_done == DID_SPELL_PRACTISE)
    {
        return;
    }

    // If your god disliked the action, evaluate its response.
    if (auto peeve = map_find(divine_peeves[you.religion], thing_done))
        (*peeve)(thing_done, level, known, victim);

    // If your god liked the action, evaluate its response.
    if (auto like = map_find(divine_likes[you.religion], thing_done))
        (*like)(thing_done, level, known, victim);
}

/**
 * Handle god conducts triggered by killing a monster.
 *
 * @param thing_done        The conduct in question.
 * @param victim            The deceased. (RIP.)
 */
void did_kill_conduct(conduct_type thing_done, const monster &victim)
{
    did_god_conduct(thing_done, victim.get_experience_level(), true, &victim);
}

// This function is the merger of done_good() and naughty().
void did_god_conduct(conduct_type thing_done, int level, bool known,
                     const monster* victim)
{
    ASSERT(!crawl_state.game_is_arena());

    _handle_your_gods_response(thing_done, level, known, victim);
}

// A Beogh worshipper zapping an orc with lightning might cause it to become a
// follower on the first hit, and the second hit would be against a friendly
// orc. Don't cause penance in this case.
static set<mid_t> _first_attack_conduct;
static set<mid_t> _first_attack_was_friendly;

void god_conduct_turn_start()
{
    _first_attack_conduct.clear();
    _first_attack_was_friendly.clear();
}

void set_attack_conducts(god_conduct_trigger conduct[3], const monster &mon,
                         bool known)
{
    // We need to examine the monster before it has been reset.
    ASSERT(mon.alive());

    const mid_t mid = mon.mid;

    if (mon.friendly())
    {
        if (_first_attack_conduct.find(mid) == _first_attack_conduct.end()
            || _first_attack_was_friendly.find(mid)
               != _first_attack_was_friendly.end())
        {
            conduct[0].set(DID_ATTACK_FRIEND, 5, known, &mon);
            _first_attack_was_friendly.insert(mid);
        }
    }
    else if (mon.neutral() && !mon.has_ench(ENCH_FRENZIED))
        conduct[0].set(DID_ATTACK_NEUTRAL, 5, known, &mon);

    if (mon.is_holy() && !mon.is_illusion())
    {
        conduct[2].set(DID_ATTACK_HOLY, mon.get_experience_level(), known,
                       &mon);
    }

    _first_attack_conduct.insert(mid);
}

string get_god_likes(god_type which_god)
{
    switch (which_god)
    {
    case GOD_NO_GOD:
    case GOD_XOM:
    case GOD_IGNIS:
        return "";
    default:
        break;
    }

    string text = uppercase_first(god_name(which_god));
    vector<string> likes;
    vector<string> really_likes;

    // Unique/unusual piety gain methods first.
    switch (which_god)
    {
    case GOD_ASHENZARI:
        likes.emplace_back(T_("you bind yourself with curses"));
        break;
    case GOD_GOZAG:
        likes.emplace_back(T_("you collect gold"));
        break;
    case GOD_RU:
        likes.emplace_back(T_("you make personal sacrifices"));
        break;
    case GOD_YREDELEMNUL:
        likes.emplace_back(T_("you kill living or demonic beings while their torch is lit"));
        really_likes.emplace_back(T_("you kill holy or unique beings while their torch is lit"));
        break;
    case GOD_ZIN:
        likes.emplace_back(T_("you donate money"));
        break;
    case GOD_OKAWARU:
        really_likes.emplace_back(T_("you kill challenging foes"));
        break;
    default:
        break;
    }


    for (const auto& entry : divine_likes[which_god])
    {
        if (entry.second.desc)
        {
            const char* desc = _zh_conduct(entry.second.desc);
            if (entry.second.really_like)
                really_likes.emplace_back(desc);
            else
                likes.emplace_back(desc);
        }
    }

    if (likes.empty() && really_likes.empty())
    {
        text += Options.language == lang_t::ZH
            ? "没有喜好？这是一个bug，请报告。"
            : " doesn't like anything? This is a bug; please report it.";
    }
    else
    {
        if (!likes.empty())
        {
            if (Options.language == lang_t::ZH)
            {
                text += "喜欢当";
                text += comma_separated_line(likes.begin(), likes.end(),
                                             "、", "、");
                text += "。";
            }
            else
            {
                text += " likes it when ";
                text += comma_separated_line(likes.begin(), likes.end());
                text += ".";
            }
            if (!really_likes.empty())
            {
                text += " ";
                text += uppercase_first(god_name(which_god));
            }
        }

        if (!really_likes.empty())
        {
            if (Options.language == lang_t::ZH)
            {
                text += "特别喜欢当";
                text += comma_separated_line(really_likes.begin(),
                                             really_likes.end(),
                                             "、", "、");
                text += "。";
            }
            else
            {
                text += " especially likes it when ";
                text += comma_separated_line(really_likes.begin(),
                                             really_likes.end());
                text += ".";
            }
        }
    }

    return text;
}

conduct_type god_hates_item_handling(const item_def& item)
{
    for (conduct_type conduct : item_conducts(item))
        if (divine_peeves[you.religion].count(conduct))
            return conduct;
    return DID_NOTHING;
}

/**
 * Handle passive effects triggered by hurting a monster (eg: Uskayaw piety,
 * Beogh healing)
 *
 * @param victim            The victim being harmed.
 * @param damage_done       The amount of damage done.
 * @param flavor            The flavour of damage done
 * @param kill_type         The category of damage source (eg: clouds)
 */
void did_hurt_monster(const monster &victim, int damage_done,
                      beam_type flavour, kill_method_type kill_type)
{
    if (flavour == BEAM_SHARED_PAIN
        || flavour == BEAM_STICKY_FLAME
        || kill_type == KILLED_BY_POISON
        || kill_type == KILLED_BY_CLOUD
        || kill_type == KILLED_BY_BEOGH_SMITING)
    {
        return;
    }

    if (you_worship(GOD_USKAYAW))
    {
        // Give a "value" for the percent of the monster's hp done in damage,
        // scaled by the monster's threat level.11
        int value = random2(3) + sqr((mons_threat_level(victim) + 1) * 2)
                * damage_done / (victim.max_hit_points);

        you.props[USKAYAW_NUM_MONSTERS_HURT].get_int() += 1;
        you.props[USKAYAW_MONSTER_HURT_VALUE].get_int() += value;
    }
    else if (you_worship(GOD_BEOGH) && you.piety() >= piety_breakpoint(2))
    {
        // Cap the damage we give points for by the target's max hp to reduce rat value
        int bonus = min(victim.hit_points, min(damage_done, victim.max_hit_points / 2));
        you.props[BEOGH_DAMAGE_DONE_KEY].get_int() += bonus;
    }
}

/**
 * Will this god definitely be upset if you memorise spells?
 *
 * This is as opposed to a likelihood.
 *
 * @param spell the spell to be cast
 * @param god   the god to check against
 * @returns true if you will definitely lose piety/get penance/be excommunicated
 */
bool god_punishes_memorising_spells(god_type god)
{
    if (map_find(divine_peeves[god], DID_SPELL_MEMORISE))
        return true;

    return false;
}

/**
 * Will this god definitely be upset if you cast this spell?
 *
 * This is as opposed to a likelihood.
 * TODO: deduplicate with spl-cast.cc:_spellcasting_god_conduct
 *
 * @param spell the spell to be cast
 * @param god   the god to check against
 * @returns true if you will definitely lose piety/get penance/be excommunicated
 */
bool god_punishes_spell(spell_type spell, god_type god)
{
    if (map_find(divine_peeves[god], DID_SPELL_CASTING))
        return true;

    if (map_find(divine_peeves[god], DID_EVIL)
        && (is_evil_spell(spell) || you.spellcasting_unholy()))
    {
        return true;
    }

    if (map_find(divine_peeves[god], DID_UNCLEAN) && is_unclean_spell(spell))
        return true;

    if (map_find(divine_peeves[god], DID_CHAOS) && is_chaotic_spell(spell))
        return true;

    // not is_hasty_spell: see spl-cast.cc:_spellcasting_god_conduct
    if (map_find(divine_peeves[god], DID_HASTY) && spell == SPELL_SWIFTNESS)
        return true;

    return false;
}
