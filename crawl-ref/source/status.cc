#include "AppHdr.h"

#include "status.h"

#include "ability.h"
#include <map>

#include "art-enum.h" // bearserk
#include "artefact.h"
#include "branch.h"
#include "dungeon.h" // DESCENT_STAIRS_KEY
#include "duration-type.h"
#include "env.h"
#include "evoke.h"
#include "fight.h" // weapon_cleaves
#include "item-prop.h"
#include "level-state-type.h"
#include "mon-abil.h"
#include "mutation.h"
#include "options.h"
#include "orb.h" // orb_limits_translocation in fill_status_info
#include "player-stats.h"
#include "religion.h"
#include "spl-damage.h" // COUPLING_TIME_KEY
#include "state.h" // crawl_state
#include "stringutil.h"
#include "throw.h"
#include "transform.h"
#include "traps.h"
#include "zot.h" // bezotting_level

#include "duration-data.h"
#include "database.h"

static int duration_index[NUM_DURATIONS];

void init_duration_index()
{
    COMPILE_CHECK(ARRAYSZ(duration_data) == NUM_DURATIONS);
    for (int i = 0; i < NUM_DURATIONS; ++i)
        duration_index[i] = -1;

    for (unsigned i = 0; i < ARRAYSZ(duration_data); ++i)
    {
        duration_type dur = duration_data[i].dur;
        ASSERT_RANGE(dur, 0, NUM_DURATIONS);
        // Catch redefinitions.
        ASSERT(duration_index[dur] == -1);
        duration_index[dur] = i;
    }
}

static const duration_def* _lookup_duration(duration_type dur)
{
    ASSERT_RANGE(dur, 0, NUM_DURATIONS);
    if (duration_index[dur] == -1)
        return nullptr;
    else
        return &duration_data[duration_index[dur]];
}

const char *duration_name(duration_type dur)
{
    return _lookup_duration(dur)->name();
}

duration_type duration_by_name(const string &name)
{
    string match_str = lowercase_string(name);
    for (int i = 0; i < NUM_DURATIONS; i++)
    {
        const duration_def& def = duration_data[i];

        string light_text = def.light_text;
        string short_text = def.short_text;
        string name_text  = def.name_text;

        lowercase(light_text);
        lowercase(short_text);
        lowercase(name_text);

        if (match_str == short_text
            || match_str == name_text
            || match_str == light_text
            || light_text.find(match_str) != string::npos
            || short_text.find(match_str) != string::npos
            || name_text.find(match_str) != string::npos)
        {
            return def.dur;
        }
    }
    return NUM_DURATIONS;
}

/**
 * Vector of all durations with flag
 *
 */
vector<duration_type> all_duration_with_flag(uint64_t flag)
{
    vector<duration_type> durations_with_flag = {};
    for (int i = 0; i < NUM_DURATIONS; i++)
    {
        duration_type type = (duration_type) duration_index[i];
        const duration_def* def = _lookup_duration(type);
        if (def && def->duration_has_flag(flag)) {
            durations_with_flag.push_back(type);
        }
    }
    return durations_with_flag;
}

bool duration_dispellable(duration_type dur)
{
    return _lookup_duration(dur)->duration_has_flag(D_DISPELLABLE);
}

bool duration_negative(duration_type dur)
{
    return _lookup_duration(dur)->duration_has_flag(D_NEGATIVE);
}

bool duration_extended_by_attacks(duration_type dur)
{
    return _lookup_duration(dur)->duration_has_flag(D_ATTACK_EXTENDED);
}

static int _bad_ench_colour(int lvl, int orange, int red)
{
    if (lvl >= red)
        return RED;
    else if (lvl >= orange)
        return LIGHTRED;

    return YELLOW;
}

static int _dur_colour(int exp_colour, bool expiring)
{
    if (expiring)
        return exp_colour;
    else
    {
        switch (exp_colour)
        {
        case GREEN:
            return LIGHTGREEN;
        case BLUE:
            return LIGHTBLUE;
        case MAGENTA:
            return LIGHTMAGENTA;
        case LIGHTGREY:
            return WHITE;
        default:
            return exp_colour;
        }
    }
}

static void _mark_expiring(status_info& inf, bool expiring)
{
    if (expiring)
    {
        if (!inf.short_text.empty())
            inf.short_text += T_(" (expiring)");
        if (!inf.long_text.empty())
            inf.long_text = (T_("Expiring: ")) + inf.long_text;
    }
}

/**
 * Populate a status_info struct from the duration_data struct corresponding
 * to the given duration_type.
 *
 * @param[in] dur    The duration in question.
 * @param[out] inf   The status_info struct to be filled.
 * @return           Whether a duration_data struct was found.
 */
// Translate common status short_text for Chinese
static const char* _zh_status_short(const char* en)
{
    if (Options.language != lang_t::ZH || !en || !en[0])
        return en;

    static const map<string, const char*> zh_names = {
        { "agile", "敏捷" }, { "berserking", "狂暴中" }, { "confused", "困惑" },
        { "slowed", "减速" }, { "quick", "加速" }, { "invisible", "隐形" },
        { "flying", "飞行中" }, { "poisoned", "中毒" }, { "mighty", "强力" },
        { "regenerating", "再生中" }, { "swift", "迅捷" }, { "corroded", "腐蚀" },
        { "petrifying", "石化中" }, { "teleporting", "传送中" }, { "drained", "虚弱" },
        { "on fire", "燃烧中" }, { "paralysed", "麻痹" }, { "transformed", "变形" },
        { "exhausted", "力竭" }, { "silenced", "沉默" }, { "mesmerised", "被催眠" },
        { "sleeping", "睡眠" }, { "resistant", "抗性" }, { "protected", "防护" },
        { "brilliant", "聪慧" }, { "diminished spells", "法术减弱" },
        { "on berserk cooldown", "狂暴冷却" }, { "short of breath", "喘息中" },
        { "lit by a corona", "被光晕照亮" }, { "reflecting", "反射中" },
        { "repelling missiles", "弹开飞弹" }, { "infused", "魔法注入" },
        { "nauseated", "恶心" }, { "weak", "脆弱" }, { "sapped magic", "魔力枯竭" },
        { "breath weapon", "吐息冷却" }, { "berserk cooldown", "狂暴冷却" },
        { "conf", "困惑" }, { "slow", "减速" }, { "haste", "加速" },
        { "invis", "隐形" }, { "fly", "飞行" }, { "might", "强力" },
        { "regen", "再生" }, { "petrify", "石化" }, { "tele", "传送" },
        { "drain", "虚弱" }, { "corr", "腐蚀" }, { "para", "麻痹" },
        { "silence", "沉默" }, { "exhaust", "力竭" }, { "nausea", "恶心" },
        { "weakness", "脆弱" }, { "sap", "枯竭" }, { "infuse", "注入" },
        { "reflect", "反射" }, { "rmissile", "弹飞弹" }, { "sleep", "睡眠" },
        { "mesm", "催眠" }, { "transform", "变形" }, { "fire", "着火" },
        { "about to teleport", "即将传送" }, { "afraid", "恐惧" },
        { "animating dead", "复活死者" }, { "attractive", "吸引怪物" },
        { "calling dragons", "召唤龙群" }, { "calling ooze", "召唤软泥" },
        { "chanting a vengeful prayer", "吟唱复仇祈祷" }, { "cleaving", "横扫中" },
        { "death channelling", "引导死亡" }, { "devious", "狡诈" },
        { "disjoining", "位移中" }, { "divinely shielded", "神圣护盾" },
        { "divinely vigorous", "神圣活力" }, { "engorged", "饱食" },
        { "enlightened", "启迪" }, { "enshackling", "束缚中" },
        { "ephemerally shielded", "短暂护盾" }, { "especially stealthy", "极度潜行" },
        { "fiery-armoured", "火焰护甲" }, { "finesse-ful", "精准" },
        { "fire vulnerable", "火焰易伤" }, { "flayed", "剥皮" },
        { "forested", "召唤森林" }, { "fragile (+50% incoming damage)", "脆弱（+50%受伤）" },
        { "frozen", "冰冻" }, { "fugue", "赋格" }, { "full of bloodlust", "充满嗜血" },
        { "growing destruction", "毁灭增长" }, { "heroic", "英雄" },
        { "horrified", "恐惧" }, { "ice-armoured", "冰甲" },
        { "immotile", "无法移动" }, { "in a vortex", "极地漩涡中" },
        { "in death's door", "死亡之门中" }, { "liquefying", "液化地面" },
        { "making a cacophony", "制造噪音" }, { "marked", "被标记" },
        { "no stairs", "拒绝楼梯" }, { "oblivion-hounded", "被湮灭追逐" },
        { "on blink cooldown", "闪烁冷却" }, { "on bloodrite cooldown", "血祭冷却" },
        { "on death's door cooldown", "死亡之门冷却" },
        { "on dragon call cooldown", "龙群召唤冷却" },
        { "on eeljolt cooldown", "电鳗冲击冷却" },
        { "on gavotte cooldown", "加沃特冷却" },
        { "on hellfire mortar cooldown", "地狱火迫击炮冷却" },
        { "on lithotoxin cooldown", "石毒素冷却" },
        { "on mesmerism cooldown", "催眠冷却" }, { "on recite cooldown", "吟诵冷却" },
        { "on siphon cooldown", "虹吸冷却" }, { "on stardust cooldown", "星尘冷却" },
        { "on swarm cooldown", "虫群冷却" }, { "on vortex cooldown", "漩涡冷却" },
        { "on word of chaos cooldown", "混沌之语冷却" }, { "petrified", "石化" },
        { "poison vulnerable", "毒素易伤" }, { "portalling projectiles", "传送飞弹中" },
        { "protected from cold", "寒冷防护" }, { "protected from electricity", "电击防护" },
        { "protected from fire", "火焰防护" }, { "protected from physical damage", "物理防护" },
        { "quad damage", "四倍伤害" }, { "radiating poison", "辐射毒素" },
        { "raining reagents", "倾泻试剂" }, { "reciting", "吟诵中" },
        { "rising", "上升中" }, { "shroud timeout", "黏液护罩破损" },
        { "sick", "疾病" }, { "spewing sludge", "喷吐泥沼" }, { "spiked", "被刺穿" },
        { "surrounded by blades", "刃之旋风" }, { "unleashing the legion", "释放军团" },
        { "untranslocatable", "无法位移" }, { "vexed", "恼怒" },
        { "vitalised", "生命活力" }, { "weak-willed", "意志薄弱" },
        { "weakened", "虚弱" },
        { "Barbs", "尖刺" },
        { "Forest", "森林" },
        { "-Star", "-星" },
        { "on stardust cooldown", "星尘冷却" },
        { "Breath", "吐息" }, { "Tesseract", "超立方体" }, { "Sunder", "碎裂" },
        { "Shroud", "护罩" }, { "slimy shroud", "黏液护罩" },
        { "Ostracised", "被排斥" }, { "Missing", "缺失" }, { "missing status", "缺失状态" },
    };
    auto it = zh_names.find(en);
    return it != zh_names.end() ? it->second : en;
}

static bool _fill_inf_from_ddef(duration_type dur, status_info& inf)
{
    const duration_def* ddef = _lookup_duration(dur);
    if (!ddef)
        return false;

    inf.light_colour = ddef->light_colour;
    inf.db_key       = ddef->light_text; // English TextDB key (before translation)
    inf.light_text   = _zh_status_short(ddef->light_text);
    inf.short_text   = _zh_status_short(ddef->short_text);
    inf.long_text    = T_(ddef->long_text);
    if (ddef->duration_has_flag(D_EXPIRES))
    {
        inf.light_colour = _dur_colour(inf.light_colour, dur_expiring(dur));
        _mark_expiring(inf, dur_expiring(dur));
    }

    return true;
}

static void _describe_airborne(status_info& inf);
static void _describe_glow(status_info& inf);
static void _describe_regen(status_info& inf);
static void _describe_speed(status_info& inf);
static void _describe_poison(status_info& inf);
static void _describe_transform(status_info& inf);
static void _describe_terrain(status_info& inf);
static void _describe_invisible(status_info& inf);
static void _describe_zot(status_info& inf);
static void _describe_gem(status_info& inf);
static void _describe_rev(status_info& inf);
static void _describe_channelled_spell(status_info& inf);

bool fill_status_info(int status, status_info& inf)
{
    inf = status_info();

    bool found = false;

    // Sort out inactive durations, and fill in data from duration_data
    // for the simple durations.
    if (status >= 0 && status < NUM_DURATIONS)
    {
        duration_type dur = static_cast<duration_type>(status);

        if (!you.duration[dur])
            return false;

        found = _fill_inf_from_ddef(dur, inf);
    }

    // Now treat special status types and durations, possibly
    // completing or overriding the defaults set above.
    switch (status)
    {
    case STATUS_STAT_ZERO:
    {
        if (!you.attribute[ATTR_STAT_ZERO])
            break;

        vector<string> stat_str;
        for (int i = STAT_STR; i <= STAT_DEX; ++i)
        {
            stat_type stat = static_cast<stat_type>(i);
            if (you.stat(stat, false) <= 0)
                stat_str.emplace_back(stat_desc(stat, SD_NAME));
        }

        string msg = comma_separated_line(stat_str.begin(), stat_str.end());

        inf.light_text   = T_("Crippled");
        inf.db_key       = "Crippled";
        inf.light_colour = LIGHTRED;
        inf.short_text   = make_stringf(T_("lost %s"), msg.c_str());
        inf.long_text    = make_stringf(T_("You have no %s!"), msg.c_str());
    }
    break;

    case STATUS_DRACONIAN_BREATH:
    {
        if ((!species::is_draconian(you.species) || you.experience_level < 7)
                && you.form != transformation::dragon)
        {
            break;
        }

        inf.light_text = "Breath";
        inf.db_key     = "Breath";

        const int num = draconian_breath_uses_available();
        if (num == 0)
            inf.light_colour = DARKGREY;
        else
        {
            inf.light_colour = LIGHTCYAN;
            if (num == 2)
                inf.light_text += "+";
            else if (num == 3)
                inf.light_text += "++";
        }
        break;
    }

    case STATUS_BLACK_TORCH:
        if (!you_worship(GOD_YREDELEMNUL))
            break;

        if (!yred_torch_is_raised())
        {
            if (yred_cannot_light_torch_reason().empty())
            {
                inf.light_colour = DARKGRAY;
                inf.light_text = T_("Torch");
                inf.db_key     = "Torch";
            }
        }
        else
        {
            inf.light_colour = MAGENTA;

            if (player_has_ability(ABIL_YRED_HURL_TORCHLIGHT))
            {
                inf.light_text = make_stringf(T_("Torch (%d)"),
                                    yred_get_torch_power());
            }
            else
                inf.light_text = T_("Torch");

            inf.db_key     = "Torch";
            inf.short_text = T_("lit torch");
        }
    break;

    case DUR_DIVINE_SHIELD:
    {
        inf.light_text = make_stringf(T_("Shield (%d)"),
                                        you.duration[DUR_DIVINE_SHIELD]);
        inf.db_key     = "Shield";
    }
    break;

    case STATUS_CORROSION:
        // No blank or double lights
        if (you.corrosion_amount() == 0 || you.duration[DUR_CORROSION])
            break;
        _fill_inf_from_ddef(DUR_CORROSION, inf);
        // Intentional fallthrough
    case DUR_CORROSION:
        inf.light_text = make_stringf(T_("Corr (%d)"),
                          (-1 * you.corrosion_amount()));
        inf.db_key     = "Corr";
        inf.short_text = make_stringf(T_("corroded (%d)"), (-1 * you.corrosion_amount()));
        break;

    case DUR_FLAYED:
        inf.light_text = make_stringf(T_("Flay (%d)"),
                          (-1 * you.props[FLAY_DAMAGE_KEY].get_int()));
        inf.db_key     = "Flay";
        break;

    case DUR_BERSERK:
        if (you.unrand_equipped(UNRAND_BEAR_SPIRIT))
        {
            inf.light_text = T_("Bearserk");
            inf.db_key     = "Bearserk";
        }
        break;

    case STATUS_NO_POTIONS:
        if (you.duration[DUR_NO_POTIONS] || player_in_branch(BRANCH_COCYTUS)
            || (you.has_mutation(MUT_RENOUNCE_POTIONS)
                && you.props.exists(RENOUNCE_POTIONS_TIMER_KEY)))
        {
            inf.light_colour = !you.can_drink(false) ? DARKGREY : RED;
            inf.light_text   = T_("-Potion");
            inf.db_key       = "-Potion";
            inf.short_text   = T_("unable to drink");
            inf.long_text    = T_("You cannot drink potions.");
        }
        break;

    case DUR_SWIFTNESS:
        if (you.attribute[ATTR_SWIFTNESS] < 0)
        {
            inf.light_text   = T_("-Swift");
            inf.db_key       = "-Swift";
            inf.light_colour = RED;
            inf.short_text   = T_("unswift");
            inf.long_text    = T_("You are covering ground slowly.");
        }
        break;

    case STATUS_ZOT:
        _describe_zot(inf);
        break;

    case STATUS_GEM:
        _describe_gem(inf);
        break;

    case STATUS_REV:
        _describe_rev(inf);
        break;

    case STATUS_AIRBORNE:
        _describe_airborne(inf);
        break;

    case STATUS_BEHELD:
        if (you.beheld())
        {
            inf.light_colour = RED;
            inf.light_text   = T_("Mesm");
            inf.db_key       = "Mesm";
            inf.short_text   = T_("mesmerised");
            inf.long_text    = T_("You are mesmerised.");
        }
        break;

    case STATUS_PEEKING:
        if (crawl_state.game_is_descent() && !env.properties.exists(DESCENT_STAIRS_KEY)
            && you.elapsed_time > 0)
        {
            inf.light_colour = WHITE;
            inf.light_text   = T_("Peek");
            inf.db_key       = "Peek";
            inf.short_text   = T_("peeking");
            inf.long_text    = T_("You are peeking down the stairs.");
        }
        break;

    case STATUS_CONTAMINATION:
        _describe_glow(inf);
        break;

    case STATUS_BACKLIT:
        if (you.backlit())
        {
            inf.short_text = T_("glowing");
            inf.long_text  = T_("You are glowing.");
        }
        break;

    case STATUS_UMBRA:
        if (you.umbra())
        {
            inf.short_text   = T_("wreathed by umbra");
            inf.long_text    = T_("You are wreathed by an umbra.");
        }
        break;

    case STATUS_NET:
        if (you.attribute[ATTR_HELD])
        {
            inf.light_colour = RED;
            inf.light_text   = T_("Held");
            inf.db_key       = "Held";
            inf.short_text   = T_("held");
            inf.long_text    = make_stringf(T_("You are %s."), held_status());
        }
        break;

    case STATUS_REGENERATION:
        // DUR_TROGS_HAND and inhibited regeneration
        _describe_regen(inf);
        break;

    case STATUS_SPEED:
        _describe_speed(inf);
        break;

    case STATUS_LIQUEFIED:
    {
        if (you.liquefied_ground() || you.duration[DUR_LIQUEFYING])
        {
            inf.light_colour = BROWN;
            inf.light_text   = T_("SlowM");
            inf.db_key       = "SlowM";
            inf.short_text   = T_("slowed movement");
            inf.long_text    = T_("Your movement is slowed on this liquid ground.");
        }
        break;
    }

    case STATUS_AUGMENTED:
    {
        int level = augmentation_amount();

        if (level > 0)
        {
            inf.light_colour = (level == 3) ? WHITE :
                               (level == 2) ? LIGHTBLUE
                                            : BLUE;

            inf.light_text = "Aug";
            inf.db_key     = "Aug";
        }
        break;
    }

    case DUR_CONFUSING_TOUCH:
    {
        inf.long_text = you.hands_act("are", "glowing red.");
        break;
    }

    case DUR_SLIMIFY:
    {
        inf.long_text = you.hands_act("are", "covered in slime.");
        break;
    }

    case DUR_POISONING:
        _describe_poison(inf);
        break;

    case DUR_POWERED_BY_DEATH:
    {
        const int pbd_str = you.props[POWERED_BY_DEATH_KEY].get_int();
        if (pbd_str > 0)
        {
            inf.light_colour = LIGHTMAGENTA;
            inf.light_text   = make_stringf(T_("Regen (%d)"), pbd_str);
            inf.db_key       = "Regen";
        }
        break;
    }

    case DUR_RAMPAGE_HEAL:
    {
        const int rh_pwr = you.props[RAMPAGE_HEAL_KEY].get_int();
        if (rh_pwr > 0)
        {
            const int rh_lvl = you.get_mutation_level(MUT_ROLLPAGE);
            inf.light_colour = rh_lvl < 2 ? LIGHTBLUE : LIGHTMAGENTA;
            inf.light_text   = make_stringf(rh_lvl < 2 ? T_("MPRegen (%d)")
                                                       : T_("Regen (%d)"), rh_pwr);
            inf.db_key       = rh_lvl < 2 ? "MPRegen" : "Regen";
        }
        break;
    }

    case STATUS_INVISIBLE:
        _describe_invisible(inf);
        break;

    case STATUS_MANUAL:
    {
        string skills = manual_skill_names();
        if (!skills.empty())
        {
            inf.short_text = T_("studying ") + manual_skill_names(true);
            inf.long_text = T_("You are studying ") + skills + T_(".");
        }
        break;
    }

    case DUR_TRANSFORMATION:
        _describe_transform(inf);
        break;

    case STATUS_CONSTRICTED:
        if (you.is_constricted())
        {
            // Our constrictor isn't, valid so don't report this status.
            if (you.has_invalid_constrictor())
                return false;

            const monster * const cstr = monster_by_mid(you.constricted_by);
            ASSERT(cstr);

            inf.light_colour = YELLOW;
            inf.light_text   = "Constr";
            inf.db_key       = "Constr";

            if (you.constricted_type == CONSTRICT_ROOTS)
                inf.short_text   = "constricted (roots)";
            else if (you.constricted_type == CONSTRICT_BVC)
                inf.short_text   = "constricted (zombie hands)";
            else
                inf.short_text   = "constricted";
        }
        break;

    case STATUS_TERRAIN:
        _describe_terrain(inf);
        break;

    // Also handled by DUR_SILENCE, see duration-data.h
    case STATUS_SILENCE:
        if (silenced(you.pos()) && !you.duration[DUR_SILENCE])
        {
            // Only display the status light if not using the noise bar.
            if (Options.equip_bar)
            {
                inf.light_colour = LIGHTRED;
                inf.light_text   = "Sil";
                inf.db_key       = "Sil";
            }
            inf.short_text   = "silenced";
            inf.long_text    = "You are silenced.";
        }
        if (Options.equip_bar && you.duration[DUR_SILENCE])
        {
            inf.light_colour = LIGHTMAGENTA;
            inf.light_text = "Sil";
            inf.db_key     = "Sil";
        }
        break;

    case STATUS_SERPENTS_LASH:
        if (you.attribute[ATTR_SERPENTS_LASH] > 0)
        {
            inf.light_colour = WHITE;
            inf.light_text
               = make_stringf(T_("Lash (%u)"),
                              you.attribute[ATTR_SERPENTS_LASH]);
            inf.short_text = "serpent's lash";
            inf.long_text = "You are moving at supernatural speed.";
        }
        break;

    case STATUS_HEAVENLY_STORM:
        if (you.props.exists(WU_JIAN_HEAVENLY_STORM_KEY))
        {
            inf.light_colour = WHITE;
            inf.light_text
                = make_stringf(T_("Heavenly (%d)"),
                               you.props[WU_JIAN_HEAVENLY_STORM_KEY].get_int());
        }
        break;

    case DUR_FUGUE:
    {
        int fugue_pow = you.props[FUGUE_KEY].get_int();
        // Hey now / you're a damned star / get your fugue on / go slay
        const char* fugue_star = fugue_pow == FUGUE_MAX_STACKS ? "*" : "";
        inf.light_text = make_stringf(T_("Fugue (%s%u%s)"),
                                      fugue_star, fugue_pow, fugue_star);
        inf.db_key     = "Fugue";
    }
    break;

    case DUR_WEREFURY:
        inf.light_text = make_stringf(T_("Slay +%d"), you.props[WEREFURY_KEY].get_int());
        // No status.txt entry for "Slay" — keep db_key empty
    break;

    case DUR_DEVIOUS:
    {
        const int stacks = you.props[DEVIOUS_KEY].get_int();
        if (stacks == 1)
            inf.light_colour = BLUE;
        else if (stacks == 2)
            inf.light_colour = LIGHTBLUE;
        else
            inf.light_colour = WHITE;
    }
    break;

    case STATUS_CLAUSTROPHOBIA:
        if (you.has_bane(BANE_CLAUSTROPHOBIA))
        {
            const int stacks = you.props[CLAUSTROPHOBIA_KEY].get_int();
            if (stacks > 0)
            {
                inf.light_colour = LIGHTRED;
                inf.light_text = make_stringf(T_("Phobia (-%d)"), stacks);
            }
        }
    break;

    case DUR_STICKY_FLAME:
    {
        int intensity = you.props[STICKY_FLAME_POWER_KEY].get_int();

        // These thresholds are fairly arbitrary and likely could use adjusting.
        if (intensity >= 13)
        {
            inf.light_colour = LIGHTRED;
            inf.light_text = "Fire++";
            inf.db_key     = "Fire++";
        }
        else if (intensity > 7)
        {
            inf.light_text = "Fire+";
            inf.db_key     = "Fire+";
        }
        else
        {
            inf.light_text = "Fire";
            inf.db_key     = "Fire";
        }
    }

    case STATUS_BEOGH:
        if (env.level_state & LSTATE_BEOGH && can_convert_to_beogh())
        {
            inf.light_colour = WHITE;
            inf.light_text = "Beogh";
            inf.db_key     = "Beogh";
        }
        break;

    case DUR_FLOODED:
        inf.light_text  = "Flooded";
        inf.db_key      = "Flooded";
        inf.short_text  = "flooded lungs";
        inf.long_text   = make_stringf(T_("Your lungs are flooded with %s and you "
                                       "cannot breathe."),
                                       you.props[WATER_HOLD_SUBSTANCE_KEY].get_string().c_str());
        break;

    case STATUS_DRAINED:
    {
        const int drain_perc = 100 * -you.hp_max_adj_temp / get_real_hp(false, false);

        if (drain_perc >= 50)
        {
            inf.light_colour = MAGENTA;
            inf.light_text   = C_("status", "Drain");
            inf.db_key       = "Drain";
            inf.short_text   = C_("status", "extremely drained");
            inf.long_text    = C_("status", "Your life force is extremely drained.");
        }
        else if (drain_perc >= 30)
        {
            inf.light_colour = RED;
            inf.light_text   = C_("status", "Drain");
            inf.db_key       = "Drain";
            inf.short_text   = C_("status", "very heavily drained");
            inf.long_text    = C_("status", "Your life force is very heavily drained.");
        }
        else if (drain_perc >= 20)
        {
            inf.light_colour = LIGHTRED;
            inf.light_text   = C_("status", "Drain");
            inf.db_key       = "Drain";
            inf.short_text   = C_("status", "heavily drained");
            inf.long_text    = C_("status", "Your life force is heavily drained.");
        }
        else if (drain_perc >= 10)
        {
            inf.light_colour = YELLOW;
            inf.light_text   = C_("status", "Drain");
            inf.db_key       = "Drain";
            inf.short_text   = C_("status", "drained");
            inf.long_text    = C_("status", "Your life force is drained.");
        }
        else if (you.hp_max_adj_temp)
        {
            inf.light_colour = LIGHTGREY;
            inf.light_text   = C_("status", "Drain");
            inf.db_key       = "Drain";
            inf.short_text   = C_("status", "lightly drained");
            inf.long_text    = C_("status", "Your life force is lightly drained.");
        }
        break;

    }
    case STATUS_CHANNELLING_SPELL:
        _describe_channelled_spell(inf);
        break;

    case STATUS_DIG:
        if (you.digging)
        {
            inf.light_colour = WHITE;
            inf.light_text   = "Dig";
            inf.db_key       = "Dig";
        }
        break;

    case STATUS_BRIBE:
    {
        int bribe = 0;
        vector<const char *> places;
        for (int i = 0; i < NUM_BRANCHES; i++)
        {
            branch_type br = gozag_fixup_branch(static_cast<branch_type>(i));

            if (branch_bribe[br] > 0)
            {
                if (player_in_branch(static_cast<branch_type>(i)))
                    bribe = branch_bribe[br];

                places.push_back(branches[static_cast<branch_type>(i)]
                                 .longname);
            }
        }

        if (bribe > 0)
        {
            inf.light_colour = (bribe >= 2000) ? WHITE :
                                (bribe >= 1000) ? LIGHTBLUE
                                                : BLUE;

            inf.light_text = "Bribe";
            inf.db_key     = "Bribe";
            inf.short_text = make_stringf(T_("bribing [%s]"),
                                           comma_separated_line(places.begin(),
                                                                places.end(),
                                                                ", ", ", ")
                                                                .c_str());
            inf.long_text = T_("You are bribing ")
                             + comma_separated_line(places.begin(),
                                                    places.end())
                             + T_(".");
        }
        break;
    }

    case DUR_HORROR:
    {
        const int horror = you.props[HORROR_PENALTY_KEY].get_int();
        inf.light_text = make_stringf(T_("Horr (%d)"), -1 * horror);
        inf.db_key     = "Horr";
        if (horror >= HORROR_LVL_OVERWHELMING)
        {
            inf.light_colour = RED;
            inf.short_text   = "overwhelmed with horror";
            inf.long_text    = "Horror overwhelms you!";
        }
        else if (horror >= HORROR_LVL_EXTREME)
        {
            inf.light_colour = LIGHTRED;
            inf.short_text   = "extremely horrified";
            inf.long_text    = "You are extremely horrified!";
        }
        else if (horror)
        {
            inf.light_colour = YELLOW;
            inf.short_text   = "horrified";
            inf.long_text    = "You are horrified!";
        }
        break;
    }

    case STATUS_CLOUD:
    {
        cloud_type cloud = cloud_type_at(you.pos());
        if (Options.cloud_status && cloud != CLOUD_NONE)
        {
            inf.light_text = "Cloud";
            inf.db_key     = "Cloud";
            // TODO: make the colour based on the cloud's color; requires elemental
            // status lights, though.
            const bool yours = cloud_is_yours_at(you.pos());
            const bool danger = cloud_damages_over_time(cloud, true, yours);
            inf.light_colour = danger ? LIGHTRED : DARKGREY;
        }
        break;
    }

    case DUR_CLEAVE:
    {
        const item_def* weapon = you.weapon();
        if (weapon && weapon_cleaves(*weapon))
            inf.light_colour = DARKGREY;
        break;
    }

    case STATUS_ORB:
    {
        if (player_has_orb())
        {
            inf.light_colour = LIGHTMAGENTA;
            inf.light_text = "Orb";
            inf.db_key     = "Orb";
        }
        else if (you.unrand_equipped(UNRAND_CHARLATANS_ORB))
        {
            inf.light_colour = LIGHTMAGENTA;
            inf.light_text = "Orb?";
            inf.db_key     = "Orb";
        }
        else if (orb_limits_translocation())
        {
            inf.light_colour = MAGENTA;
            inf.light_text = "Orb";
            inf.db_key     = "Orb";
        }

        break;
    }

    case STATUS_STILL_WINDS:
        if (env.level_state & LSTATE_STILL_WINDS)
        {
            inf.light_colour = BROWN;
            inf.light_text = "-Clouds";
            inf.db_key     = "-Clouds";
        }
        break;

    case STATUS_DUEL:
        if (okawaru_duel_active())
        {
            inf.light_colour = WHITE;
            inf.light_text   = "Duel";
            inf.db_key       = "Duel";
            inf.short_text   = "duelling";
            inf.long_text    = "You are engaged in single combat.";
        }
        break;

    case STATUS_CANINE_FAMILIAR_ACTIVE:
        if (canine_familiar_is_alive())
        {
            inf.light_colour = WHITE;
            inf.light_text   = "Dog";
            inf.db_key       = "Dog";
            inf.short_text   = "inugami summoned";
            inf.long_text    = "Your inugami has been summoned.";
        }
        break;

    case STATUS_NO_SCROLL:
        if (you.duration[DUR_NO_SCROLLS] || player_in_branch(BRANCH_GEHENNA)
            || (you.has_mutation(MUT_RENOUNCE_SCROLLS)
                && you.props.exists(RENOUNCE_SCROLLS_TIMER_KEY)))
        {
            inf.light_colour = RED;
            inf.light_text   = "-Scroll";
            inf.db_key       = "-Scroll";
            inf.short_text   = "unable to read";
            inf.long_text    = "You cannot read scrolls.";
        }
        break;

    case STATUS_RF_ZERO:
        if (!you.penance[GOD_IGNIS]
            || player_res_fire(false, true, true) < 0)
        {
            // XXX: would it be better to only show this
            // if you would otherwise have rF+ & to warn
            // on using a potion of resistance..?
            break;
        }
        inf.light_colour = RED;
        inf.light_text   = "rF0";
        inf.db_key       = "rF0";
        inf.short_text   = "fire susceptible";
        inf.long_text    = "You cannot resist fire.";
        break;

    case STATUS_LOWERED_WL:
        // Don't double the light if under a duration
        if (!player_in_branch(BRANCH_TARTARUS) || you.duration[DUR_LOWERED_WL])
            break;
        if (player_in_branch(BRANCH_TARTARUS))
            _fill_inf_from_ddef(DUR_LOWERED_WL, inf);
        break;

    case DUR_FUSILLADE:
        if (!enough_mp(2, true))
            inf.light_colour = DARKGREY;
        break;

    case STATUS_GRAVE_CLAW_UNAVAILABLE:
        if (you.has_spell(SPELL_GRAVE_CLAW)
            && you.props[GRAVE_CLAW_CHARGES_KEY].get_int() == 0)
        {
            inf.light_colour = DARKGREY;
            inf.light_text = "-GClaw";
            inf.db_key     = "-GClaw";
        }
        break;

    case DUR_GROWING_DESTRUCTION:
    {
        inf.light_text = "Destr";
        const int stacks = you.props[MAKHLEB_ATROCITY_STACKS_KEY].get_int();
        for (int i = 0; i < stacks - 1; ++i)
            inf.light_text += "+";
        if (stacks == MAKHLEB_ATROCITY_MAX_STACKS)
            inf.light_colour = LIGHTBLUE;
    }
    break;

    case STATUS_CRUCIBLE_DEBT:
    {
        if (player_in_branch(BRANCH_CRUCIBLE))
        {
            inf.light_text = "Pact";
            inf.db_key     = "Pact";
            const int debt = you.props[MAKHLEB_CRUCIBLE_DEBT_KEY].get_int();
            if (debt > 20)
                inf.light_colour = MAGENTA;
            else if (debt > 10)
                inf.light_colour = RED;
            else if (debt > 5)
                inf.light_colour = LIGHTRED;
            else if (debt > 0)
                inf.light_colour = YELLOW;
            else
            {
                inf.light_text = "Escape!";
                inf.db_key     = "Escape!";
                inf.light_colour = WHITE;
            }
        }
        break;
    }

    case DUR_PARAGON_ACTIVE:
    {
        if (paragon_defense_bonus_active())
        {
            inf.light_colour = WHITE;
            inf.light_text = "Protected";
            inf.db_key     = "Protected";
        }
        break;
    }

    case DUR_FORTRESS_BLAST_TIMER:
        inf.light_colour = WHITE;
        inf.light_text = T_("Blast") + string(max(0, (40 - you.duration[DUR_FORTRESS_BLAST_TIMER]) / 10), '.');
        inf.db_key     = "Blast";
        inf.short_text = T_("fortress blast");
        inf.long_text = T_("Preparing a Fortress Blast.");
        break;

    case DUR_TELEPORT:
        if (you.props.exists(TELEPORTITIS_SOURCE))
        {
            inf.light_text   = "!Tele!";
            inf.db_key       = "!Tele!";
            inf.light_colour = RED;
            inf.short_text   = "teleporting to hostiles";
            inf.long_text    = "You are about to teleport to other enemies.";
        }
        break;

    case STATUS_TRICKSTER:
        if (you.has_mutation(MUT_TRICKSTER))
        {
            const int bonus = trickster_bonus();
            if (bonus > 0)
            {
                inf.short_text = make_stringf(T_("trickster (+%d AC)"), bonus);
                inf.long_text = make_stringf(T_("You are bolstered by spread misfortune (+%d AC)"), bonus);
            }
        }
        break;

    case DUR_DROWSY:
        if (you.duration[DUR_DROWSY] > 70)
            inf.light_colour = LIGHTRED;
        else if (you.duration[DUR_DROWSY] >= 35)
            inf.light_colour = RED;
        else
            inf.light_colour = LIGHTGREY;
        break;

    case DUR_SLIMIFYING:
        if (you.duration[DUR_SLIMIFYING] > 140)
            inf.light_colour = LIGHTMAGENTA;
        else if (you.duration[DUR_SLIMIFYING] >= 75)
            inf.light_colour = RED;
        else
            inf.light_colour = YELLOW;
        break;

    case STATUS_MNEMOPHAGE:
        if (!you.duration[DUR_ENKINDLED] && you.has_mutation(MUT_MNEMOPHAGE))
        {
            inf.light_colour = CYAN;
            inf.light_text = make_stringf(T_("Memories (%d)"), you.props[ENKINDLE_CHARGES_KEY].get_int());
            inf.db_key     = "Memories";
        }
        break;

    case DUR_ENKINDLED:
        inf.light_text = make_stringf(T_("Enkindled (%d)"), you.props[ENKINDLE_CHARGES_KEY].get_int());
        inf.db_key     = "Enkindled";
        break;

    case STATUS_SHROUD:
        if (you.has_mutation(MUT_SLIME_SHROUD)
                && !you.duration[DUR_SHROUD_TIMEOUT])
        {
            inf.light_colour = GREEN;
            inf.light_text   = "Shroud";
            inf.db_key       = "Shroud";
            inf.short_text   = "slimy shroud";
        }
        break;

    case STATUS_OSTRACISM:
        if (you.attribute[ATTR_OSTRACISM] > 0)
        {
            inf.light_text = "Ostracised";
            inf.db_key     = "Ostracised";
            if (!god_cares_about_ostracism())
                inf.light_colour = DARKGREY;
            else if (you.attribute[ATTR_OSTRACISM] > 120)
                inf.light_colour = MAGENTA;
            else if (you.attribute[ATTR_OSTRACISM] > 80)
                inf.light_colour = RED;
            else
                inf.light_colour = YELLOW;
        }
        break;

    case STATUS_TESSERACT:
        if (level_id::current() == level_id(BRANCH_ZOT, 5)
            && you.props.exists(TESSERACT_SPAWN_COUNTER_KEY))
        {
            const int count = you.props[TESSERACT_SPAWN_COUNTER_KEY].get_int();
            if (count >= 50)
                inf.light_colour = LIGHTMAGENTA;
            else
                inf.light_colour = RED;

            inf.light_text = "Tesseract";
            inf.db_key     = "Tesseract";
        }
        break;

    case STATUS_SUNDER_READY:
        if (you.sunder_is_ready())
        {
            inf.light_colour = WHITE;
            inf.light_text = "Sunder";
            inf.db_key     = "Sunder";
        }
        break;

    default:
        if (!found)
        {
            inf.light_colour = RED;
            inf.light_text   = "Missing";
            inf.db_key       = "Missing";
            inf.short_text   = "missing status";
            inf.long_text    = "Missing status description.";
            return false;
        }
        else
            break;
    }
    // Translate any remaining English text for Chinese mode
    if (Options.language == lang_t::ZH)
    {
        if (!inf.light_text.empty())
            inf.light_text = _zh_status_short(inf.light_text.c_str());
        if (!inf.short_text.empty())
            inf.short_text = _zh_status_short(inf.short_text.c_str());
    }
    return true;
}

static colour_t _gem_light_colour(int d_aut_left)
{
    if (d_aut_left < 100)
        return LIGHTMAGENTA;
    if (d_aut_left < 250)
        return RED;
    if (d_aut_left < 500)
        return YELLOW;
    return WHITE;
}

static void _describe_gem(status_info& inf)
{
    if (!Options.always_show_gems)
        return;

    const gem_type gem = gem_for_branch(you.where_are_you);
    if (gem == NUM_GEM_TYPES)
        return;

    if (!Options.more_gem_info && you.gems_found[gem])
        return;

    const int time_taken = you.gem_time_spent[gem];
    const int limit = gem_time_limit(gem);
    if (time_taken >= limit)
        return; // already lost...

    if (!gem_clock_active() && !you.gems_found[gem])
    {
        // player has picked up the orb, but the gem has not yet shattered
        inf.light_text = T_(" Gem (*)");
        inf.db_key     = "Gem";
        inf.light_colour = CYAN;
        return;
    }
    const int d_aut_left = (limit - time_taken + 9) / 10;
    inf.light_text = make_stringf(T_("Gem (%d)"), d_aut_left);
    inf.db_key     = "Gem";
    inf.light_colour = _gem_light_colour(d_aut_left);
}

static void _describe_zot(status_info& inf)
{
    const int lvl = bezotting_level();
    if (lvl > 0)
    {
        inf.short_text = T_("bezotted");
        inf.long_text = T_("Zot is approaching!");
    }
    else if (!Options.always_show_zot && !you.has_mutation(MUT_SHORT_LIFESPAN)
             || !zot_clock_active())
    {
        return;
    }

    // XX code dup with overview screen
    inf.light_text = make_stringf(T_("Zot (%d)"), turns_until_zot());
    inf.db_key     = "Zot";
    switch (lvl)
    {
        case 0:
            inf.light_colour = WHITE;
            break;
        case 1:
            inf.light_colour = YELLOW;
            break;
        case 2:
            inf.light_colour = RED;
            break;
        case 3:
        default:
            inf.light_colour = LIGHTMAGENTA;
            break;
    }
}

static void _describe_glow(status_info& inf)
{
    // Don't show a status light until we have contam that does something.
    if (!player_harmful_contamination())
        return;

    if (you.magic_contamination >= 2000)
        inf.light_colour = RED;
    else
        inf.light_colour = YELLOW;
    inf.light_text = T_("Contam");
    inf.db_key     = "Contam";

    inf.short_text = describe_contamination(false);
    inf.long_text = describe_contamination();
}

static void _describe_rev(status_info& inf)
{
    if (!you.has_mutation(MUT_WARMUP_STRIKES) || !you.rev_percent())
        return;

    const int tier = you.rev_tier();
    switch (tier)
    {
        case 1:
            inf.light_colour = BLUE;
            inf.light_text   = "Rev";
            inf.db_key       = "Rev";
            inf.short_text   = "revving";
            inf.long_text    = "You're starting to limber up.";
            return;

        case 2:
            inf.light_colour = LIGHTBLUE;
            inf.light_text   = "Rev+";
            inf.db_key       = "Rev";
            inf.short_text   = "revving";
            inf.long_text    = "You're limbering up.";
            return;

        case 3:
            inf.light_colour = WHITE;
            inf.light_text   = "Rev*";
            inf.db_key       = "Rev";
            inf.short_text   = "revved";
            inf.long_text    = "You're fully limbered up.";
            return;
    }
}

static void _describe_regen(status_info& inf)
{
    if (you.duration[DUR_TROGS_HAND])
    {
        inf.light_colour = _dur_colour(BLUE, dur_expiring(DUR_TROGS_HAND));
        inf.light_text = "Regen Will++";
        inf.db_key     = "Regen Will++";
        inf.short_text = "regenerating";
        inf.long_text  = "You are regenerating.";
        _mark_expiring(inf, dur_expiring(DUR_TROGS_HAND));
    }
    else if (regeneration_is_inhibited())
    {
        inf.light_colour = RED;
        inf.light_text = "-Regen";
        inf.db_key     = "-Regen";
        inf.short_text = "inhibited regen";
        inf.long_text = "Your regeneration is inhibited by nearby monsters.";
    }
}

static void _describe_poison(status_info& inf)
{
    int pois_perc = (you.hp <= 0) ? 100
                                  : ((you.hp - max(0, poison_survival())) * 100 / you.hp);
    inf.light_colour = (player_res_poison(false) >= 3
                        ? DARKGREY : _bad_ench_colour(pois_perc, 35, 100));
    inf.light_text   = T_("Pois");
    inf.db_key       = "Pois";
    const bool zh = Options.language == lang_t::ZH;
    const string adj =
         (pois_perc >= 100) ? (T_("lethally")) :
         (pois_perc > 65)   ? (T_("seriously")) :
         (pois_perc > 35)   ? (T_("quite"))
                            : (T_("mildly"));
    inf.short_text   = zh ? adj + "中毒" : adj + T_(" poisoned");
    inf.short_text  += make_stringf(T_(" (%d -> %d)"), you.hp, poison_survival());
    inf.long_text    = T_("You are ") + inf.short_text + T_(".");
}

static void _describe_speed(status_info& inf)
{
    bool slow = you.duration[DUR_SLOW] || have_stat_zero();
    bool fast = you.duration[DUR_HASTE];

    if (slow && fast)
    {
        inf.light_colour = MAGENTA;
        inf.light_text   = "Fast+Slow";
        inf.short_text   = "hasted and slowed";
        inf.long_text = "You are under both slowing and hasting effects.";
    }
    else if (slow)
    {
        inf.light_colour = RED;
        inf.light_text   = "Slow";
        inf.db_key       = "Slow";
        inf.short_text   = "slowed";
        inf.long_text    = "You are slowed.";
    }
    else if (fast)
    {
        inf.light_colour = _dur_colour(BLUE, dur_expiring(DUR_HASTE));
        inf.light_text   = "Fast";
        inf.db_key       = "Fast";
        inf.short_text = "hasted";
        inf.long_text = "Your actions are hasted.";
        _mark_expiring(inf, dur_expiring(DUR_HASTE));
    }
}

static void _describe_airborne(status_info& inf)
{
    if (!you.airborne())
        return;

    const bool perm      = you.permanent_flight();
    const bool expiring  = (!perm && dur_expiring(DUR_FLIGHT));
    const bool emergency = you.props[EMERGENCY_FLIGHT_KEY].get_bool();

    inf.light_colour = perm ? WHITE : emergency ? LIGHTRED : BLUE;
    inf.light_text   = "Fly";
    inf.db_key       = "Fly";
    inf.short_text   = "flying";
    inf.long_text    = "You are flying.";
    inf.light_colour = _dur_colour(inf.light_colour, expiring);
    _mark_expiring(inf, expiring);
}

/**
 * Populate a status info struct with a description of the player's current
 * form.
 *
 * @param[out] inf  The status info struct to be populated.
 */
static void _describe_transform(status_info& inf)
{
    if (you.form == transformation::none)
        return;

    const Form * const form = get_form();
    inf.light_text = form->short_name;
    inf.short_text = form->get_long_name();
    inf.long_text = form->get_description();

    const bool expire  = dur_expiring(DUR_TRANSFORMATION);
    inf.light_colour = _dur_colour(GREEN, expire);
    _mark_expiring(inf, expire);
}

static void _describe_terrain(status_info& inf)
{
    switch (env.grid(you.pos()))
    {
    case DNGN_SHALLOW_WATER:
        inf.light_colour = LIGHTBLUE;
        inf.light_text = "Water";
        inf.db_key     = "Water";
        break;
    case DNGN_DEEP_WATER:
        inf.light_colour = BLUE;
        inf.light_text = "Water";
        inf.db_key     = "Water";
        break;
    case DNGN_LAVA:
        inf.light_colour = RED;
        inf.light_text = "Lava";
        inf.db_key     = "Lava";
        break;
    default:
        ;
    }
}

static void _describe_invisible(status_info& inf)
{
    if (!you.duration[DUR_INVIS])
        return;

    inf.light_colour = _dur_colour(BLUE, dur_expiring(DUR_INVIS));
    inf.light_text   = "Invis";
    inf.db_key       = "Invis";
    inf.short_text   = "invisible";
    if (you.backlit())
    {
        inf.light_colour = DARKGREY;
        inf.short_text += T_(" (but backlit and visible)");
    }
    inf.long_text = T_("You are ") + inf.short_text + T_(".");
    _mark_expiring(inf, dur_expiring(DUR_INVIS));
}

static vector<string> _charge_strings = { "Charge-", "Charge/",
                                          "Charge|", "Charge\\"};

static string _charge_text()
{
    static int charge_index = 0;
    charge_index = (charge_index + 1) % 4;
    return _charge_strings[charge_index];
}

static void _describe_channelled_spell(status_info& inf)
{
    const spell_type spell = (spell_type)you.attribute[ATTR_CHANNELLED_SPELL];
    if (spell == SPELL_NO_SPELL)
        return;

    const int turns = you.attribute[ATTR_CHANNEL_DURATION];

    switch (spell)
    {
        // It's only possible to hit the prop = 0 case if we reprint the
        // screen after the spell was cast but before the end of the
        // player's turn, which mostly happens in webtiles. Great!
        case SPELL_FLAME_WAVE:
            inf.light_colour = WHITE;
            inf.light_text   = T_("Wave") + string(max(turns - 1, 0), '+');
            inf.db_key       = "Wave";
            break;

        case SPELL_SEARING_RAY:
            inf.light_colour = WHITE;
            inf.light_text   = T_("Ray") + string(max(turns - 1, 0), '+');
            inf.db_key       = "Ray";
            break;

        case SPELL_MAXWELLS_COUPLING:
            inf.light_colour = LIGHTCYAN;
            inf.light_text   = _charge_text().c_str();
            break;

        case SPELL_CLOCKWORK_BEE:
            inf.light_colour = CYAN;
            inf.light_text = T_("Winding") + string(max(turns - 1, 0), '.');
            inf.db_key     = "Winding";
            break;

        default:
            break;
    }
}

/**
 * Does a given duration tick down simply over time?
 *
 * @param dur   The duration in question (e.g. DUR_PETRIFIED).
 * @return      Whether the duration's end_msg is non-null.
 */
bool duration_decrements_normally(duration_type dur)
{
    return _lookup_duration(dur)->decr.end.msg != nullptr;
}

/**
 * What message should a given duration print when it expires, if any?
 *
 * @param dur   The duration in question (e.g. DUR_PETRIFIED).
 * @return      A message to print for the duration when it ends.
 */
const char *duration_end_message(duration_type dur)
{
    return _lookup_duration(dur)->decr.end.msg;
}

/**
 * What message should a given duration print when it passes its
 * expiring threshold, if any?
 *
 * @param dur   The duration in question (e.g. DUR_PETRIFIED).
 * @return      A message to print.
 */
const char *duration_expire_message(duration_type dur)
{
    return _lookup_duration(dur)->decr.expire_msg.msg;
}

/**
 * How much should the duration be decreased by when it passes its
 * expiring threshold (to fuzz the remaining time), if at all?
 *
 * @param dur   The duration in question (e.g. DUR_PETRIFIED).
 * @return      A random value to reduce the remaining duration by; may be 0.
 */
int duration_expire_offset(duration_type dur)
{
    return _lookup_duration(dur)->decr.expire_msg.offset();
}

/**
 * At what number of turns remaining is the given duration considered to be
 * 'expiring', for purposes of messaging & status light colouring?
 *
 * @param dur   The duration in question (e.g. DUR_PETRIFIED).
 * @return      The maximum number of remaining turns at which the duration
 *              is considered 'expiring'; may be 0.
 */
int duration_expire_point(duration_type dur)
{
    return _lookup_duration(dur)->expire_threshold * BASELINE_DELAY;
}

/**
 * What channel should the duration messages be printed in?
 *
 * @param dur   The duration in question (e.g. DUR_PETRIFIED).
 * @return      The appropriate message channel, e.g. MSGCH_RECOVERY.
 */
msg_channel_type duration_expire_chan(duration_type dur)
{
    return _lookup_duration(dur)->decr.recovery ? MSGCH_RECOVERY
                                                : MSGCH_DURATION;
}

/**
 * If a duration has some special effect when ending, trigger it.
 *
 * @param dur   The duration in question (e.g. DUR_PETRIFIED).
 */
void duration_end_effect(duration_type dur)
{
    if (_lookup_duration(dur)->decr.end.on_end)
        _lookup_duration(dur)->decr.end.on_end();
}
