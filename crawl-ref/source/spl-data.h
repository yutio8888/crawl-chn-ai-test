/**
 * @file
 * @brief Spell definitions and descriptions. See spell_desc struct in
 *        spl-util.cc.
 * Flag descriptions are in spl-cast.h.
**/

#pragma once

/*
struct spell_desc
{
    enum, spell name,
    spell schools,
    flags,
    level,
    power_cap,
    min_range, max_range, (-1 if not applicable)
    effect_noise
    tile
}
*/

#include "tag-version.h"

static const struct spell_desc spelldata[] =
{

{
    SPELL_CAUSE_FEAR, "引发恐惧",
    spschool::hexes,
    spflag::WL_check,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_CAUSE_FEAR,
},

{
    SPELL_MAGIC_DART, "魔法飞镖",
    spschool::conjuration,
    spflag::dir_or_target | spflag::needs_tracer,
    1,
    25,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_MAGIC_DART,
},

{
    SPELL_FIREBALL, "火球术",
    spschool::conjuration | spschool::fire,
    spflag::dir_or_target | spflag::needs_tracer,
    5,
    200,
    5, 5,
    0,
    TILEG_FIREBALL,
},

{
    SPELL_APPORTATION, "隔空取物",
    spschool::translocation,
    spflag::target | spflag::obj | spflag::not_self,
    1,
    50,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_APPORTATION,
},

{
    SPELL_BLASTMOTE, "不稳定爆尘",
    spschool::fire | spschool::translocation,
    spflag::destructive,
    3,
    50,
    -1, -1,
    0,
    TILEG_BLASTMOTE,
},

{
    SPELL_DIG, "挖掘",
    spschool::earth,
    spflag::dir_or_target | spflag::not_self | spflag::aim_at_space,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    4,
    TILEG_DIG,
},

{
    SPELL_BOLT_OF_FIRE, "火焰箭",
    spschool::conjuration | spschool::fire,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    6,
    200,
    6, 6,
    0,
    TILEG_BOLT_OF_FIRE,
},

{
    SPELL_BOLT_OF_COLD, "寒冰箭",
    spschool::conjuration | spschool::ice,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    6,
    200,
    5, 5,
    0,
    TILEG_BOLT_OF_COLD,
},

{
    SPELL_LIGHTNING_BOLT, "闪电箭",
    spschool::conjuration | spschool::air,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    20,
    TILEG_LIGHTNING_BOLT,
},

{
    SPELL_ARCJOLT, "电弧震击",
    spschool::conjuration | spschool::air,
    spflag::none,
    5,
    200,
    2, 2,
    10,
    TILEG_ARCJOLT,
},

{
    SPELL_PLASMA_BEAM, "等离子光束",
    spschool::fire | spschool::air,
    spflag::noisy | spflag::destructive,
    6,
    200,
    LOS_RADIUS, LOS_RADIUS,
    20,
    TILEG_PLASMA_BEAM,
},

{
    SPELL_PERMAFROST_ERUPTION, "永冻爆发",
    spschool::ice | spschool::earth,
    spflag::destructive,
    6,
    200,
    6, 6, // reduce cases of hitting something outside LOS
    0,
    TILEG_PERMAFROST_ERUPTION,
},

{
    SPELL_BLINKBOLT, "闪雷",
    spschool::air | spschool::translocation,
    spflag::dir_or_target | spflag::monster | spflag::noisy
        | spflag::needs_tracer,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_BLINKBOLT,
},

{
    SPELL_ELECTRIC_CHARGE, "维之电荷",
    spschool::air | spschool::translocation,
    spflag::noisy | spflag::dir_or_target, // hack - should have spflag::needs_tracer
                   // and maybe spflag::hasty?
    4,
    50,
    4, 4,
    0,
    TILEG_ELECTRIC_CHARGE,
},

{
    SPELL_ELECTROLUNGE, "维之电冲",
    spschool::air | spschool::translocation,
    spflag::noisy | spflag::target | spflag::monster,
    4,
    100,
    5, 5,
    0,
    TILEG_ELECTRIC_CHARGE,
},

{
    SPELL_BOLT_OF_MAGMA, "岩浆箭",
    spschool::conjuration | spschool::fire | spschool::earth,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    5,
    200,
    4, 4,
    0,
    TILEG_BOLT_OF_MAGMA,
},

{
    SPELL_POLYMORPH, "变形",
    spschool::alchemy | spschool::hexes,
    spflag::dir_or_target | spflag::chaotic
        | spflag::needs_tracer | spflag::WL_check,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_POLYMORPH,
},

{
    SPELL_SLOW, "减速",
    spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer | spflag::WL_check,
    1,
    25,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SLOW,
},

{
    SPELL_HASTE, "加速",
    spschool::hexes,
    spflag::helpful | spflag::hasty | spflag::selfench | spflag::monster,
    6,
    200,
    -1, -1,
    0,
    TILEG_HASTE,
},

{
    SPELL_PETRIFY, "石化",
    spschool::alchemy | spschool::earth,
    spflag::dir_or_target | spflag::needs_tracer | spflag::WL_check,
    4,
    200,
    6, 6,
    0,
    TILEG_PETRIFY,
},

{
    SPELL_CONFUSE, "困惑",
    spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer | spflag::WL_check
        | spflag::monster,
    3,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_CONFUSE,
},

{
    SPELL_INVISIBILITY, "隐身术",
    spschool::hexes,
    spflag::helpful | spflag::selfench | spflag::escape | spflag::monster,
    6,
    200,
    -1, -1,
    0,
    TILEG_INVISIBILITY,
},

{
    SPELL_THROW_FLAME, "火焰投掷",
    spschool::conjuration | spschool::fire,
    spflag::dir_or_target | spflag::needs_tracer,
    2,
    50,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_THROW_FLAME,
},

{
    SPELL_THROW_FROST, "冰霜投掷",
    spschool::conjuration | spschool::ice,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    2,
    50,
    6, 6,
    0,
    TILEG_THROW_FROST,
},

{
    SPELL_DISJUNCTION, "空间分离",
    spschool::translocation,
    spflag::escape,
    8,
    200,
    4, 4,
    0,
    TILEG_DISJUNCTION,
},

{
    SPELL_FREEZING_CLOUD, "冰冻云",
    spschool::conjuration | spschool::ice | spschool::air,
    spflag::target | spflag::needs_tracer | spflag::cloud,
    5,
    200,
    5, 5,
    2,
    TILEG_FREEZING_CLOUD,
},

{
    SPELL_FREEZING_GUST, "冰冻阵风",
    spschool::conjuration | spschool::ice | spschool::air,
    spflag::target | spflag::needs_tracer | spflag::cloud | spflag::monster,
    5,
    200,
    5, 5,
    2,
    TILEG_FREEZING_CLOUD,
},

{
    SPELL_MEPHITIC_CLOUD, "瘴气云",
    spschool::conjuration | spschool::alchemy | spschool::air,
    spflag::dir_or_target | spflag::needs_tracer | spflag::cloud,
    3,
    100,
    4, 4,
    0,
    TILEG_MEPHITIC_CLOUD,
},

{
    SPELL_VENOM_BOLT, "毒液箭",
    spschool::conjuration | spschool::alchemy,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    5,
    200,
    5, 5,
    0,
    TILEG_VENOM_BOLT,
},

{
    SPELL_OLGREBS_TOXIC_RADIANCE, "奥尔格雷布之毒辐射",
    spschool::alchemy,
    spflag::destructive,
    4,
    100,
    -1, -1,
    0,
    TILEG_OLGREBS_TOXIC_RADIANCE,
},

{
    SPELL_TELEPORT_OTHER, "传送他人",
    spschool::translocation,
    spflag::target | spflag::not_self | spflag::escape | spflag::WL_check,
    3,
    100,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_TELEPORT_OTHER,
},

{
    SPELL_DEATHS_DOOR, "死亡之门",
    spschool::necromancy,
    spflag::no_ghost,
    9,
    200,
    -1, -1,
    0,
    TILEG_DEATHS_DOOR,
},

{
    SPELL_MASS_CONFUSION, "群体困惑",
    spschool::hexes,
    spflag::WL_check | spflag::monster,
    6,
    200,
    -1, -1,
    0,
    TILEG_MASS_CONFUSION,
},

{
    SPELL_SMITING, "惩击",
    spschool::none,
    spflag::target | spflag::not_self,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SMITING,
},

{
    SPELL_SUMMON_SMALL_MAMMAL, "召唤小型哺乳动物",
    spschool::summoning,
    spflag::none,
    1,
    25,
    -1, -1,
    0,
    TILEG_SUMMON_SMALL_MAMMAL,
},

// Used indirectly, by monsters abjuring via other summon spells.
// And used directly by summoning miscast monsters (nameless horrors).
{
    SPELL_ABJURATION, "驱逐术",
    spschool::summoning,
    spflag::monster,
    3,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_MASS_ABJURATION,
},

{
    SPELL_BOLT_OF_DRAINING, "吸取之箭",
    spschool::conjuration | spschool::necromancy,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    5,
    200,
    5, 5,
    0,
    TILEG_BOLT_OF_DRAINING,
},

{
    SPELL_LEHUDIBS_CRYSTAL_SPEAR, "勒胡迪布之水晶矛",
    spschool::conjuration | spschool::earth,
    spflag::dir_or_target | spflag::needs_tracer,
    8,
    200,
    3, 3,
    0,
    TILEG_LEHUDIBS_CRYSTAL_SPEAR,
},

{
    SPELL_POLAR_VORTEX, "极地漩涡",
    spschool::ice,
    spflag::destructive,
    9,
    200,
    POLAR_VORTEX_RADIUS, POLAR_VORTEX_RADIUS,
    0,
    TILEG_POLAR_VORTEX,
},

{
    SPELL_POISONOUS_CLOUD, "毒云",
    spschool::conjuration | spschool::alchemy | spschool::air,
    spflag::target | spflag::needs_tracer | spflag::cloud | spflag::monster,
    5,
    200,
    5, 5,
    2,
    TILEG_POISONOUS_CLOUD,
},

{
    SPELL_FIRE_STORM, "火焰风暴",
    spschool::conjuration | spschool::fire,
    spflag::target | spflag::needs_tracer,
    9,
    200,
    5, 5,
    0,
    TILEG_FIRE_STORM,
},

{
    SPELL_CALL_DOWN_DAMNATION, "降下诅咒",
    spschool::conjuration,
    spflag::target | spflag::unholy | spflag::needs_tracer | spflag::monster,
    9,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_CALL_DOWN_DAMNATION,
},

{
    SPELL_CALL_DOWN_LIGHTNING, "降下闪电",
    spschool::conjuration | spschool::air,
    spflag::target | spflag::monster,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_CALL_DOWN_LIGHTNING,
},

{
    SPELL_BLINK, "闪烁",
    spschool::translocation,
    spflag::escape | spflag::selfench,
    2,
    50,
    -1, -1,
    0,
    TILEG_BLINK,
},

{
    SPELL_BLINK_RANGE, "退避闪烁", // XXX needs better name
    spschool::translocation,
    spflag::escape | spflag::monster | spflag::selfench,
    2,
    0,
    -1, -1,
    0,
    TILEG_BLINK,
},

{
    SPELL_BLINK_AWAY, "远离闪烁",
    spschool::translocation,
    spflag::escape | spflag::monster | spflag::selfench,
    2,
    0,
    -1, -1,
    0,
    TILEG_BLINK,
},

{
    SPELL_BLINK_CLOSE, "接近闪烁",
    spschool::translocation,
    spflag::monster | spflag::target,
    2,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_BLINK,
},

// The following name was found in the hack.exe file of an early version
// of PCHACK - credit goes to its creator (whoever that may be):
{
    SPELL_ISKENDERUNS_MYSTIC_BLAST, "伊斯肯德伦之神秘冲击",
    spschool::conjuration | spschool::translocation,
    spflag::none,
    4,
    100,
    2, 2,
    10,
    TILEG_ISKENDERUNS_MYSTIC_BLAST,
},

{
    SPELL_SUMMON_HORRIBLE_THINGS, "召唤恐怖之物",
    spschool::summoning,
    spflag::unholy | spflag::chaotic | spflag::mons_abjure,
    8,
    200,
    -1, -1,
    0,
    TILEG_SUMMON_HORRIBLE_THINGS,
},

{
    SPELL_MALIGN_GATEWAY, "邪恶传送门",
    spschool::summoning | spschool::translocation,
    spflag::unholy | spflag::chaotic,
    7,
    200,
    -1, -1,
    15,
    TILEG_MALIGN_GATEWAY,
},

{
    SPELL_CHARMING, "魅惑",
    spschool::hexes,
    spflag::dir_or_target | spflag::not_self | spflag::needs_tracer
        | spflag::WL_check,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_CHARMING,
},

{
    SPELL_ANIMATE_DEAD, "操纵死尸",
    spschool::necromancy,
    spflag::helpful | spflag::no_ghost,
    4,
    100,
    -1, -1,
    0,
    TILEG_ANIMATE_DEAD,
},

{
    SPELL_PAIN, "痛苦",
    spschool::necromancy,
    spflag::dir_or_target | spflag::needs_tracer | spflag::WL_check
        | spflag::monster,
    1,
    25,
    5, 5,
    0,
    TILEG_PAIN,
},

{
    SPELL_SOUL_SPLINTER, "灵魂分裂",
    spschool::necromancy,
    spflag::dir_or_target | spflag::needs_tracer | spflag::WL_check
        | spflag::not_self,
    1,
    25,
    5, 5,
    0,
    TILEG_NECROTISE,
},

{
    SPELL_VAMPIRIC_DRAINING, "吸血之蚀",
    spschool::necromancy,
    spflag::dir_or_target | spflag::not_self,
    3,
    100,
    1, 1,
    0,
    TILEG_VAMPIRIC_DRAINING,
},

{
    SPELL_HAUNT, "鬼魂缠身",
    spschool::summoning | spschool::necromancy,
    spflag::target | spflag::not_self | spflag::mons_abjure,
    7,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_HAUNT,
},

{
    SPELL_MARTYRS_KNELL, "殉道者之丧钟",
    spschool::summoning | spschool::necromancy,
    spflag::none,
    4,
    100,
    -1, -1,
    0,
    TILEG_MARTYRS_KNELL,
},

{
    SPELL_BORGNJORS_REVIVIFICATION, "博格尼尔之复活",
    spschool::necromancy,
    spflag::none,
    8,
    200,
    -1, -1,
    0,
    TILEG_BORGNJORS_REVIVIFICATION,
},

{
    SPELL_FREEZE, "冰冻",
    spschool::ice,
    spflag::dir_or_target | spflag::not_self | spflag::destructive,
    1,
    25,
    1, 1,
    0,
    TILEG_FREEZE,
},

{
    SPELL_OZOCUBUS_REFRIGERATION, "奥佐库布之制冷",
    spschool::ice,
    spflag::destructive,
    7,
    200,
    -1, -1,
    0,
    TILEG_OZOCUBUS_REFRIGERATION,
},

{
    SPELL_STICKY_FLAME, "粘性火焰",
    spschool::alchemy | spschool::fire,
    spflag::dir_or_target | spflag::needs_tracer | spflag::destructive,
    4,
    100,
    1, 1,
    0,
    TILEG_STICKY_FLAME,
},

{
    SPELL_SUMMON_ICE_BEAST, "召唤冰兽",
    spschool::ice | spschool::summoning,
    spflag::none,
    3,
    100,
    -1, -1,
    0,
    TILEG_SUMMON_ICE_BEAST,
},

{
    SPELL_OZOCUBUS_ARMOUR, "奥佐库布之护甲",
    spschool::ice,
    spflag::no_ghost,
    3,
    100,
    -1, -1,
    0,
    TILEG_OZOCUBUS_ARMOUR,
},

{
    SPELL_CALL_IMP, "召唤小恶魔",
    spschool::summoning,
    spflag::unholy,
    2,
    50,
    -1, -1,
    0,
    TILEG_CALL_IMP,
},

{
    SPELL_DEFLECT_MISSILES, "偏转投射物",
    spschool::air,
    spflag::monster | spflag::selfench,
    6,
    50,
    -1, -1,
    0,
    TILEG_DEFLECT_MISSILES,
},

{
    SPELL_BERSERKER_RAGE, "狂暴之怒",
    spschool::earth,
    spflag::hasty | spflag::monster | spflag::selfench,
    3,
    0,
    -1, -1,
    0,
    TILEG_BERSERKER_RAGE,
},

{
    SPELL_DISPEL_UNDEAD, "驱散亡灵",
    spschool::necromancy,
    spflag::dir_or_target | spflag::needs_tracer,
    4,
    100,
    1, 1,
    0,
    TILEG_DISPEL_UNDEAD,
},

{
    SPELL_POISON_ARROW, "毒箭",
    spschool::conjuration | spschool::alchemy,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    6,
    200,
    6, 6,
    0,
    TILEG_POISON_ARROW,
},

// Monster-only, players can use Lugonu's ability
{
    SPELL_BANISHMENT, "放逐",
    spschool::translocation,
    spflag::dir_or_target | spflag::unholy | spflag::chaotic | spflag::monster
        | spflag::needs_tracer | spflag::WL_check,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_BANISHMENT,
},

{
    SPELL_STING, "刺击",
    spschool::conjuration | spschool::alchemy,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    1,
    25,
    4, 4,
    0,
    TILEG_STING,
},

{
    SPELL_SUBLIMATION_OF_BLOOD, "血液升华",
    spschool::necromancy,
    spflag::none,
    2,
    100,
    -1, -1,
    0,
    TILEG_SUBLIMATION_OF_BLOOD,
},

{
    SPELL_TUKIMAS_DANCE, "图基玛之舞",
    spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer | spflag::WL_check
        | spflag::not_self,
    3,
    100,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_TUKIMAS_DANCE,
},

{
    SPELL_SUMMON_DEMON, "召唤恶魔",
    spschool::summoning,
    spflag::unholy
    | spflag::mons_abjure | spflag::monster,
    5,
    200,
    -1, -1,
    0,
    TILEG_SUMMON_DEMON,
},

{
    SPELL_SUMMON_GREATER_DEMON, "召唤高级恶魔",
    spschool::summoning,
    spflag::unholy
    | spflag::mons_abjure  | spflag::monster,
    7,
    200,
    -1, -1,
    0,
    TILEG_SUMMON_GREATER_DEMON,
},

{
    SPELL_PUTREFACTION, "西格图维之腐烂",
    spschool::necromancy | spschool::air,
    spflag::target | spflag::unclean,
    4,
    100,
    5, 5,
    0,
    TILEG_CORPSE_ROT,
},

{
    SPELL_IRON_SHOT, "铁弹",
    spschool::conjuration | spschool::earth,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    6,
    200,
    4, 4,
    0,
    TILEG_IRON_SHOT,
},

{
    SPELL_BOMBARD, "炮击",
    spschool::conjuration | spschool::earth,
    spflag::dir_or_target | spflag::needs_tracer,
    6,
    200,
    4, 4,
    0,
    TILEG_IRON_SHOT,
},

{
    SPELL_STONE_ARROW, "石箭",
    spschool::conjuration | spschool::earth,
    spflag::dir_or_target | spflag::needs_tracer,
    3,
    50,
    4, 4,
    0,
    TILEG_STONE_ARROW,
},

{
    SPELL_SHOCK, "电击",
    spschool::conjuration | spschool::air,
    spflag::dir_or_target | spflag::needs_tracer,
    1,
    25,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SHOCK,
},

{
    SPELL_SWIFTNESS, "迅捷",
    spschool::air,
    spflag::hasty | spflag::selfench,
    3,
    100,
    -1, -1,
    0,
    TILEG_SWIFTNESS,
},

{
    SPELL_DEBUGGING_RAY, "调试射线",
    spschool::conjuration,
    spflag::dir_or_target | spflag::testing,
    7,
    100,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_DEBUGGING_RAY,
},

{
    SPELL_AGONISING_TOUCH, "剧痛之触",
    spschool::necromancy,
    spflag::dir_or_target | spflag::needs_tracer
        | spflag::WL_check | spflag::monster,
    5,
    200,
    1, 1,
    0,
    TILEG_AGONY,
},

{
    SPELL_CURSE_OF_AGONY, "痛苦诅咒",
    spschool::necromancy,
    spflag::dir_or_target | spflag::not_self | spflag::needs_tracer
        | spflag::WL_check,
    5,
    100,
    4, 4,
    0,
    TILEG_AGONY,
},

{
    SPELL_MINDBURST, "心智爆发",
    spschool::conjuration,
    spflag::dir_or_target | spflag::not_self | spflag::needs_tracer
        | spflag::WL_check,
    6,
    200,
    LOS_RADIUS, LOS_RADIUS,
    6,
    TILEG_MINDBURST,
},

{
    SPELL_DEATH_CHANNEL, "死亡通道",
    spschool::necromancy,
    spflag::helpful | spflag::selfench,
    6,
    200,
    -1, -1,
    0,
    TILEG_DEATH_CHANNEL,
},

// Monster-only, players can use Kiku's ability
{
    SPELL_SYMBOL_OF_TORMENT, "折磨之符",
    spschool::necromancy,
    spflag::monster,
    6,
    0,
    -1, -1,
    0,
    TILEG_SYMBOL_OF_TORMENT,
},

{
    SPELL_SIPHON_ESSENCE, "吸取精华",
    spschool::necromancy,
    spflag::monster,
    7,
    0,
    2, 2,
    0,
    TILEG_SIPHON_ESSENCE,
},

{
    SPELL_THROW_ICICLE, "投掷冰柱",
    spschool::conjuration | spschool::ice,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    4,
    100,
    5, 5,
    0,
    TILEG_THROW_ICICLE,
},

{
    SPELL_AIRSTRIKE, "空袭",
    spschool::air,
    spflag::target | spflag::not_self | spflag::destructive,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    4,
    TILEG_AIRSTRIKE,
},

{
    SPELL_MOMENTUM_STRIKE, "动量打击",
    spschool::conjuration | spschool::translocation,
    spflag::target | spflag::not_self,
    2,
    50,
    4, 4,
    0,
    TILEG_MOMENTUM_STRIKE,
},

{
    SPELL_SHADOW_CREATURES, "暗影生物",
    spschool::summoning,
    spflag::mons_abjure | spflag::monster,
    6,
    0,
    -1, -1,
    0,
    TILEG_SUMMON_SHADOW_CREATURES,
},

{
    SPELL_CONFUSING_TOUCH, "困惑之触",
    spschool::hexes,
    spflag::selfench | spflag::WL_check, // Show success in the static targeter
    3,
    100,
    -1, -1,
    0,
    TILEG_CONFUSING_TOUCH,
},

{
    SPELL_PASSWALL, "穿墙术",
    spschool::earth,
    spflag::target | spflag::escape | spflag::not_self | spflag::silent,
    3,
    100,
    3, 3,
    0,
    TILEG_PASSWALL,
},

{
    SPELL_IGNITE_POISON, "点燃毒素",
    spschool::fire | spschool::alchemy,
    spflag::destructive,
    4,
    100,
    -1, -1,
    0,
    TILEG_IGNITE_POISON,
},

{
    SPELL_CALL_CANINE_FAMILIAR, "召唤犬类使魔",
    spschool::summoning,
    spflag::none,
    3,
    100,
    -1, -1,
    0,
    TILEG_CALL_CANINE_FAMILIAR,
},

{
    SPELL_SUMMON_DRAGON, "召唤巨龙", // see also, SPELL_DRAGON_CALL
    spschool::summoning,
    spflag::mons_abjure | spflag::monster,
    9,
    200,
    -1, -1,
    0,
    TILEG_SUMMON_DRAGON,
},

{
    SPELL_HIBERNATION, "冬眠",
    spschool::hexes | spschool::ice,
    spflag::dir_or_target | spflag::not_self | spflag::needs_tracer
        | spflag::WL_check | spflag::silent,
    2,
    50,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_ENSORCELLED_HIBERNATION,
},

{
    SPELL_ENGLACIATION, "深度冻结",
    spschool::hexes | spschool::ice,
    spflag::none,
    5,
    200,
    -1, -1,
    0,
    TILEG_METABOLIC_ENGLACIATION,
},

{
    SPELL_SILENCE, "沉默",
    spschool::hexes | spschool::air,
    spflag::silent, // of course!
    5,
    200,
    -1, -1,
    0,
    TILEG_SILENCE,
},

{
    SPELL_SHATTER, "粉碎",
    spschool::earth,
    spflag::destructive,
    9,
    200,
    -1, -1,
    30,
    TILEG_SHATTER,
},

{
    SPELL_DISPERSAL, "驱散",
    spschool::translocation,
    spflag::escape,
    6,
    200,
    1, 4,
    0,
    TILEG_DISPERSAL,
},

{
    SPELL_DISCHARGE, "静电释放",
    spschool::conjuration | spschool::air,
    spflag::none,
    2,
    50,
    1, 1,
    0,
    TILEG_STATIC_DISCHARGE,
},

{
    SPELL_CORONA, "日冕",
    spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer
        | spflag::WL_check | spflag::monster,
    1,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_CORONA,
},

{
    SPELL_INTOXICATE, "阿利斯泰尔之醉",
    spschool::alchemy,
    spflag::none,
    5,
    150,
    -1, -1,
    0,
    TILEG_ALISTAIRS_INTOXICATION,
},

{
    SPELL_LRD, "李之快速解构",
    spschool::earth,
    spflag::target | spflag::destructive,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_LEES_RAPID_DECONSTRUCTION,
},

{
    SPELL_SANDBLAST, "沙暴",
    spschool::earth,
    spflag::dir_or_target | spflag::not_self | spflag::needs_tracer
        | spflag::destructive,
    1,
    50,
    4, 4,
    0,
    TILEG_SANDBLAST,
},

{
    SPELL_SIMULACRUM, "塑造拟像",
    spschool::ice | spschool::alchemy,
    spflag::target | spflag::not_self | spflag::needs_tracer
        | spflag::unholy,
    6,
    200,
    1, 1,
    0,
    TILEG_SIMULACRUM,
},

{
    SPELL_CONJURE_BALL_LIGHTNING, "召唤球形闪电",
    spschool::air | spschool::conjuration,
    spflag::none,
    6,
    200,
    -1, -1,
    0,
    TILEG_CONJURE_BALL_LIGHTNING,
},

{
    SPELL_CHAIN_LIGHTNING, "连锁闪电",
    spschool::air | spschool::conjuration,
    spflag::none,
    9,
    200,
    -1, -1,
    25,
    TILEG_CHAIN_LIGHTNING,
},

{
    SPELL_PORTAL_PROJECTILE, "传送投射物",
    spschool::translocation,
    spflag::target | spflag::monster,
    3,
    50,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_PORTAL_PROJECTILE,
},

{
    SPELL_MONSTROUS_MENAGERIE, "怪物动物园",
    spschool::summoning,
    spflag::mons_abjure | spflag::monster,
    7,
    200,
    -1, -1,
    0,
    TILEG_MONSTROUS_MENAGERIE,
},

{
    SPELL_GOLUBRIAS_PASSAGE, "戈卢布里亚之通道",
    spschool::translocation,
    spflag::target | spflag::aim_at_space | spflag::escape | spflag::selfench,
    4,
    100,
    2, LOS_RADIUS,
    8, // when it closes
    TILEG_PASSAGE_OF_GOLUBRIA,
},

{
    SPELL_FULMINANT_PRISM, "爆裂棱镜",
    spschool::conjuration | spschool::alchemy,
    spflag::target | spflag::not_self | spflag::no_ghost,
    4,
    200,
    4, 4,
    0,
    TILEG_FULMINANT_PRISM,
},

{
    SPELL_PARALYSE, "麻痹",
    spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer
        | spflag::WL_check,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_PARALYSE,
},

{
    SPELL_MINOR_HEALING, "小型治疗",
    spschool::none,
    spflag::recovery | spflag::helpful | spflag::monster | spflag::selfench,
    2,
    0,
    -1, -1,
    0,
    TILEG_MINOR_HEALING,
},

{
    SPELL_MAJOR_HEALING, "大型治疗",
    spschool::none,
    spflag::recovery | spflag::helpful | spflag::monster | spflag::selfench,
    6,
    0,
    -1, -1,
    0,
    TILEG_MAJOR_HEALING,
},

{
    SPELL_WOODWEAL, "木质愈合",
    spschool::none,
    spflag::recovery | spflag::helpful | spflag::monster | spflag::selfench,
    4,
    0,
    1, 1,
    0,
    TILEG_WOODWEAL,
},

{
    SPELL_HURL_DAMNATION, "投掷诅咒",
    spschool::conjuration,
    spflag::dir_or_target | spflag::unholy
        | spflag::needs_tracer,
    // plus DS ability, staff of Dispater & Sceptre of Asmodeus
    9,
    200,
    6, 6,
    0,
    TILEG_HURL_DAMNATION,
},

{
    SPELL_BRAIN_BITE, "脑噬",
    spschool::necromancy | spschool::hexes,
    spflag::target | spflag::monster,
    3,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_BRAIN_BITE,
},

{
    SPELL_NOXIOUS_CLOUD, "毒云",
    spschool::conjuration | spschool::alchemy | spschool::air,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer
        | spflag::cloud,
    5,
    200,
    5, 5,
    2,
    TILEG_NOXIOUS_CLOUD,
},

{
    SPELL_STEAM_BALL, "蒸汽球",
    spschool::conjuration,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer,
    4,
    0,
    6, 6,
    0,
    TILEG_STEAM_BALL,
},

{
    SPELL_SUMMON_UFETUBUS, "Summon Ufetubus",
    spschool::summoning,
    spflag::unholy | spflag::monster,
    4,
    0,
    -1, -1,
    0,
    TILEG_SUMMON_UFETUBUS,
},

{
    SPELL_SUMMON_SIN_BEAST, "召唤罪兽",
    spschool::summoning,
    spflag::unholy | spflag::monster,
    4,
    0,
    -1, -1,
    0,
    TILEG_SUMMON_SIN_BEAST,
},

{
    SPELL_BOLT_OF_DEVASTATION, "毁灭之箭",
    spschool::conjuration,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer,
    5,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_ENERGY_BOLT,
},

{
    SPELL_SPIT_POISON, "喷吐毒素",
    spschool::alchemy,
    spflag::dir_or_target | spflag::monster | spflag::noisy
        | spflag::needs_tracer,
    2,
    0,
    6, 6,
    0,
    TILEG_SPIT_POISON,
},

{
    SPELL_SUMMON_UNDEAD, "召唤亡灵",
    spschool::summoning | spschool::necromancy,
    spflag::monster | spflag::mons_abjure,
    7,
    0,
    -1, -1,
    0,
    TILEG_SUMMON_UNDEAD,
},

{
    SPELL_CANTRIP, "小戏法",
    spschool::none,
    spflag::monster,
    1,
    0,
    -1, -1,
    0,
    TILEG_CANTRIP,
},

{
    SPELL_QUICKSILVER_BOLT, "水银箭",
    spschool::conjuration,
    spflag::dir_or_target | spflag::needs_tracer | spflag::not_self,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_QUICKSILVER_BOLT,
},

{
    SPELL_METAL_SPLINTERS, "金属碎片",
    spschool::conjuration,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer,
    5,
    0,
    4, 4,
    0,
    TILEG_METAL_SPLINTERS,
},

{
    SPELL_SPLINTERSPRAY, "碎片喷射",
    spschool::conjuration,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer,
    4,
    0,
    3, 3,
    0,
    TILEG_METAL_SPLINTERS, // close enough
},

{
    SPELL_MIASMA_BREATH, "瘴气吐息",
    spschool::conjuration,
    spflag::dir_or_target | spflag::unclean | spflag::monster
        | spflag::needs_tracer | spflag::cloud,
    6,
    0,
    5, 5,
    2,
    TILEG_MIASMA_BREATH,
},

{
    SPELL_SUMMON_DRAKES, "召唤小龙",
    spschool::summoning | spschool::necromancy, // since it can summon shadow dragons
    spflag::unclean | spflag::monster | spflag::mons_abjure,
    6,
    0,
    -1, -1,
    0,
    TILEG_SUMMON_DRAKES,
},

{
    SPELL_BLINK_OTHER, "闪烁他人",
    spschool::translocation,
    spflag::dir_or_target | spflag::escape | spflag::monster
        | spflag::needs_tracer,
    2,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_BLINK_OTHER,
},

{
    SPELL_BLINK_OTHER_CLOSE, "闪烁他人接近",
    spschool::translocation,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer,
    2,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_BLINK_OTHER,
},

{
    SPELL_SUMMON_MUSHROOMS, "召唤蘑菇",
    spschool::summoning,
    spflag::monster | spflag::mons_abjure,
    4,
    0,
    -1, -1,
    0,
    TILEG_SUMMON_MUSHROOMS,
},

{
    SPELL_SPIT_ACID, "喷吐酸液",
    spschool::alchemy,
    spflag::dir_or_target | spflag::monster | spflag::noisy
        | spflag::needs_tracer,
    5,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SPIT_ACID,
},

{
    SPELL_CAUSTIC_BREATH, "腐蚀吐息",
    spschool::conjuration | spschool::alchemy,
    spflag::dir_or_target | spflag::noisy | spflag::needs_tracer,
    5,
    0,
    6, 6,
    0,
    TILEG_SPIT_ACID,
},

{
    SPELL_PYRE_ARROW, "火葬之箭",
    spschool::conjuration | spschool::fire,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer,
    4,
    100,
    5, 5,
    0,
    TILEG_STICKY_FLAME_RANGE,
},

{
    SPELL_FIRE_BREATH, "火焰吐息",
    spschool::conjuration | spschool::fire,
    spflag::dir_or_target | spflag::monster | spflag::noisy
        | spflag::needs_tracer,
    5,
    0,
    5, 5,
    0,
    TILEG_FIRE_BREATH,
},

{
    SPELL_SEARING_BREATH, "灼热之息",
    spschool::conjuration | spschool::fire,
    spflag::dir_or_target | spflag::monster | spflag::noisy
        | spflag::needs_tracer,
    5,
    0,
    5, 5,
    0,
    TILEG_FIRE_BREATH,
},

{
    SPELL_CHAOS_BREATH, "混沌吐息",
    spschool::conjuration | spschool::random,
    spflag::dir_or_target | spflag::monster | spflag::noisy
        | spflag::needs_tracer | spflag::cloud,
    5,
    0,
    5, 5,
    2,
    TILEG_CHAOS_BREATH,
},

{
    SPELL_COLD_BREATH, "寒冷吐息",
    spschool::conjuration | spschool::ice,
    spflag::dir_or_target | spflag::monster | spflag::noisy
        | spflag::needs_tracer,
    5,
    0,
    5, 5,
    0,
    TILEG_COLD_BREATH,
},

{
    SPELL_GLACIAL_BREATH, "冰川吐息",
    spschool::conjuration | spschool::ice,
    spflag::dir_or_target | spflag::noisy | spflag::needs_tracer,
    5,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_COLD_BREATH,
},

{
    SPELL_WATER_ELEMENTALS, "召唤水元素",
    spschool::summoning,
    spflag::monster | spflag::mons_abjure,
    5,
    0,
    -1, -1,
    0,
    TILEG_WATER_ELEMENTALS,
},

{
    SPELL_PORKALATOR, "变猪术",
    spschool::hexes | spschool::alchemy,
    spflag::dir_or_target | spflag::chaotic | spflag::needs_tracer
        | spflag::WL_check | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_PORKALATOR,
},

{
    SPELL_CREATE_TENTACLES, "生成触须",
    spschool::none,
    spflag::monster,
    5,
    0,
    -1, -1,
    0,
    TILEG_CREATE_TENTACLES,
},

{
    SPELL_SUMMON_EYEBALLS, "召唤眼球",
    spschool::summoning,
    spflag::monster | spflag::mons_abjure,
    5,
    0,
    -1, -1,
    0,
    TILEG_SUMMON_EYEBALLS,
},

{
    SPELL_HASTE_OTHER, "加速他人",
    spschool::hexes,
    spflag::dir_or_target | spflag::helpful
        | spflag::hasty | spflag::needs_tracer | spflag::monster,
    6,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_HASTE_OTHER,
},

{
    SPELL_EARTH_ELEMENTALS, "召唤大地元素",
    spschool::summoning,
    spflag::monster | spflag::mons_abjure,
    5,
    0,
    -1, -1,
    0,
    TILEG_EARTH_ELEMENTALS,
},

{
    SPELL_AIR_ELEMENTALS, "召唤空气元素",
    spschool::summoning,
    spflag::monster | spflag::mons_abjure,
    5,
    0,
    -1, -1,
    0,
    TILEG_AIR_ELEMENTALS,
},

{
    SPELL_FIRE_ELEMENTALS, "召唤火焰元素",
    spschool::summoning,
    spflag::monster | spflag::mons_abjure,
    5,
    0,
    -1, -1,
    0,
    TILEG_FIRE_ELEMENTALS,
},

{
    SPELL_SLEEP, "睡眠",
    spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer
        | spflag::WL_check | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SLEEP,
},

{
    SPELL_FAKE_MARA_SUMMON, "玛拉召唤",
    spschool::summoning,
    spflag::monster,
    5,
    0,
    -1, -1,
    0,
    TILEG_FAKE_MARA_SUMMON,
},

{
    SPELL_SUMMON_ILLUSION, "召唤幻象",
    spschool::summoning,
    spflag::monster | spflag::target,
    5,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SUMMON_ILLUSION,
},

{
    SPELL_PRIMAL_WAVE, "原始波浪",
    spschool::conjuration | spschool::ice,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    6,
    200,
    6, 6,
    25,
    TILEG_PRIMAL_WAVE,
},

{
    SPELL_CALL_TIDE, "召唤潮汐",
    spschool::translocation,
    spflag::monster,
    7,
    0,
    -1, -1,
    0,
    TILEG_CALL_TIDE,
},

{
    SPELL_IOOD, "毁灭之球",
    spschool::conjuration,
    spflag::dir_or_target | spflag::not_self | spflag::needs_tracer,
    7,
    200,
    8, 8,
    0,
    TILEG_IOOD,
},

{
    SPELL_INK_CLOUD, "墨云",
    spschool::conjuration | spschool::ice, // it's a water spell
    spflag::monster | spflag::escape,
    7,
    0,
    -1, -1,
    0,
    TILEG_INK_CLOUD,
},

{
    SPELL_MIGHT, "强壮",
    spschool::hexes,
    spflag::helpful | spflag::selfench | spflag::monster,
    3,
    200,
    -1, -1,
    0,
    TILEG_MIGHT,
},

{
    SPELL_MIGHT_OTHER, "强壮他人",
    spschool::hexes,
    spflag::dir_or_target | spflag::helpful | spflag::needs_tracer | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_MIGHT,
},

{
    SPELL_AWAKEN_FOREST, "唤醒森林",
    spschool::hexes | spschool::summoning,
    spflag::monster,
    6,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_AWAKEN_FOREST,
},

{
    SPELL_DRUIDS_CALL, "德鲁伊召唤",
    spschool::summoning,
    spflag::monster,
    6,
    0,
    -1, -1,
    0,
    TILEG_DRUIDS_CALL,
},

{
    SPELL_BROTHERS_IN_ARMS, "战友召唤",
    spschool::summoning,
    spflag::monster,
    6,
    0,
    -1, -1,
    0,
    TILEG_BROTHERS_IN_ARMS,
},

{
    SPELL_TROGS_HAND, "特洛格之手",
    spschool::none,
    spflag::monster | spflag::selfench | spflag::recovery,
    3,
    0,
    -1, -1,
    0,
    TILEG_TROGS_HAND,
},

{
    SPELL_SUMMON_MORTAL_CHAMPION, "召唤凡人冠军",
    spschool::summoning,
    spflag::monster,
    7,
    0,
    -1, -1,
    0,
    TILEG_SUMMON_MORTAL_CHAMPION,
},

{
    SPELL_VANQUISHED_VANGUARD, "被征服的先锋",
    spschool::necromancy | spschool::summoning,
    spflag::monster | spflag::target,
    4,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SUMMON_SPECTRAL_ORCS,
},

{
    SPELL_SUMMON_HOLIES, "召唤圣灵",
    spschool::summoning,
    spflag::monster | spflag::mons_abjure | spflag::holy,
    5,
    0,
    -1, -1,
    0,
    TILEG_SUMMON_HOLIES,
},

{
    SPELL_HEAL_OTHER, "治愈他人",
    spschool::none,
    spflag::dir_or_target | spflag::helpful | spflag::needs_tracer
        | spflag::monster | spflag::recovery,
    6,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_HEAL_OTHER,
},

{
    SPELL_HOLY_FLAMES, "神圣火焰",
    spschool::none,
    spflag::target | spflag::not_self | spflag::holy | spflag::monster,
    7,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_HOLY_FLAMES,
},

{
    SPELL_HOLY_BREATH, "神圣吐息",
    spschool::conjuration,
    spflag::dir_or_target | spflag::needs_tracer | spflag::cloud
        | spflag::holy | spflag::monster,
    5,
    200,
    5, 5,
    2,
    TILEG_HOLY_BREATH,
},

{
    SPELL_INJURY_MIRROR, "伤害反射",
    spschool::none,
    spflag::selfench | spflag::monster,
    4,
    200,
    -1, -1,
    0,
    TILEG_INJURY_MIRROR,
},

{
    SPELL_DRAIN_LIFE, "吸取生命",
    spschool::necromancy,
    spflag::monster,
    6,
    0,
    -1, -1,
    0,
    TILEG_DRAIN_LIFE,
},

{
    SPELL_LEDAS_LIQUEFACTION, "勒达之液化",
    spschool::earth | spschool::alchemy,
    spflag::none,
    4,
    200,
    -1, -1,
    0,
    TILEG_LEDAS_LIQUEFACTION,
},

{
    SPELL_SUMMON_HYDRA, "召唤九头蛇",
    spschool::summoning,
    spflag::mons_abjure,
    7,
    200,
    -1, -1,
    0,
    TILEG_SUMMON_HYDRA,
},

{
    SPELL_MESMERISE, "迷惑",
    spschool::hexes,
    spflag::WL_check | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_MESMERISE,
},

{
    SPELL_HELLFIRE_COURT, "地狱火法庭",
    spschool::summoning | spschool::fire,
    spflag::monster | spflag::mons_abjure,
    8,
    0,
    -1, -1,
    0,
    TILEG_HELLFIRE_COURT,
},

{
    SPELL_PETRIFYING_CLOUD, "石化云",
    spschool::conjuration | spschool::earth | spschool::air,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer,
    5,
    0,
    LOS_RADIUS, LOS_RADIUS,
    2,
    TILEG_PETRIFYING_CLOUD,
},

{
    SPELL_INNER_FLAME, "内焰",
    spschool::hexes | spschool::fire,
    spflag::target | spflag::not_self | spflag::WL_check | spflag::destructive,
    3,
    100,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_INNER_FLAME,
},

{
    SPELL_ENSNARE, "束缚",
    spschool::conjuration | spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    6,
    200,
    5, 5,
    0,
    TILEG_ENSNARE,
},

{
    SPELL_GREATER_ENSNARE, "强力束缚",
    spschool::conjuration | spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    6,
    200,
    5, 5,
    0,
    TILEG_ENSNARE,
},

{
    SPELL_THUNDERBOLT, "雷击",
    spschool::conjuration | spschool::air,
    spflag::dir_or_target | spflag::not_self,
    2, // 2-5, sort of
    200,
    5, 5,
    15,
    TILEG_THUNDERBOLT,
},

{
    SPELL_BATTLESPHERE, "伊斯肯德伦之战斗球",
    spschool::conjuration | spschool::forgecraft,
    spflag::none,
    4,
    100,
    -1, -1,
    0,
    TILEG_BATTLESPHERE,
},

{
    SPELL_SUMMON_MINOR_DEMON, "召唤小恶魔",
    spschool::summoning,
    spflag::unholy | spflag::monster,
    2,
    200,
    -1, -1,
    0,
    TILEG_SUMMON_MINOR_DEMON,
},

{
    SPELL_STICKS_TO_SNAKES, "棍变蛇",
    spschool::summoning,
    spflag::monster,
    2,
    200,
    -1, -1,
    0,
    TILEG_STICKS_TO_SNAKES,
},

{
    SPELL_MALMUTATE, "恶性变异",
    spschool::alchemy | spschool::hexes,
    spflag::dir_or_target | spflag::chaotic | spflag::needs_tracer
        | spflag::monster,
    6,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_MALMUTATE,
},

{
    SPELL_GLOOM, "阴郁",
    spschool::hexes | spschool::necromancy,
    spflag::silent,
    3,
    50,
    2, 3,
    0,
    TILEG_GLOOM,
},

{
    SPELL_BECKONING_GALE, "召唤强风",
    spschool::air,
    spflag::target | spflag::not_self | spflag::monster,
    3,
    100,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_BECKONING_GALE,
},

{
    SPELL_FORCE_LANCE, "力量之矛",
    spschool::conjuration | spschool::translocation,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    4,
    100,
    3, 3,
    0,
    TILEG_FORCE_LANCE,
},

{
    SPELL_SENTINEL_MARK, "哨兵印记",
    spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer | spflag::WL_check
                          | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SENTINEL_MARK,
},

// Ironbrand Convoker version (delayed activation, recalls only humanoids)
{
    SPELL_WORD_OF_RECALL, "召回之言",
    spschool::summoning | spschool::translocation,
    spflag::monster,
    3,
    0,
    -1, -1,
    0,
    TILEG_RECALL,
},

{
    SPELL_INJURY_BOND, "伤害链接",
    spschool::hexes,
    spflag::helpful | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_INJURY_BOND,
},

{
    SPELL_SPECTRAL_CLOUD, "幽灵云",
    spschool::conjuration | spschool::necromancy,
    spflag::dir_or_target | spflag::monster | spflag::cloud,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SPECTRAL_CLOUD,
},

{
    SPELL_GHOSTLY_FIREBALL, "幽灵火球",
    spschool::conjuration | spschool::necromancy,
    spflag::dir_or_target | spflag::monster | spflag::unholy
        | spflag::needs_tracer,
    5,
    200,
    5, 5,
    0,
    TILEG_GHOSTLY_FIREBALL,
},

{
    SPELL_CALL_LOST_SOULS, "召唤迷失灵魂",
    spschool::summoning | spschool::necromancy,
    spflag::unholy | spflag::monster,
    5,
    200,
    -1, -1,
    0,
    TILEG_CALL_LOST_SOULS,
},

{
    SPELL_DIMENSION_ANCHOR, "维度锚定",
    spschool::translocation | spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer | spflag::WL_check
                          | spflag::monster,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_DIMENSIONAL_ANCHOR,
},

{
    SPELL_BLINK_ALLIES_ENCIRCLE, "闪烁盟友包围",
    spschool::translocation,
    spflag::target | spflag::monster,
    6,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_BLINK_ALLIES_ENCIRCLING,
},

{
    SPELL_AWAKEN_VINES, "唤醒藤蔓",
    spschool::hexes | spschool::summoning,
    spflag::monster | spflag::target,
    6,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_AWAKEN_VINES,
},

{
    SPELL_THORN_VOLLEY, "荆棘齐射",
    spschool::conjuration | spschool::earth,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    4,
    100,
    5, 5,
    0,
    TILEG_THORN_VOLLEY,
},

{
    SPELL_WALL_OF_BRAMBLES, "Wall of Brambles",
    spschool::conjuration | spschool::earth,
    spflag::monster,
    5,
    100,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_WALL_OF_BRAMBLES,
},

{
    SPELL_WATERSTRIKE, "水击",
    spschool::ice,
    spflag::target | spflag::not_self | spflag::monster,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_WATERSTRIKE,
},

{
    SPELL_WIND_BLAST, "风击",
    spschool::air,
    spflag::target | spflag::monster, // wind blast is targeted when used as a (monster) spell, but not from the storm card
    3,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_WIND_BLAST,
},

{
    SPELL_STRIP_WILLPOWER, "剥离意志力",
    spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer | spflag::WL_check
                          | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_STRIP_WILLPOWER,
},

{
    SPELL_FUGUE_OF_THE_FALLEN, "亡灵赋格",
    spschool::necromancy,
    spflag::selfench,
    3,
    100,
    -1, -1,
    8,
    TILEG_FUGUE_OF_THE_FALLEN,
},

{
    SPELL_SUMMON_VERMIN, "召唤害虫",
    spschool::summoning,
    spflag::monster | spflag::unholy | spflag::mons_abjure,
    5,
    0,
    -1, -1,
    0,
    TILEG_SUMMON_VERMIN,
},

{
    SPELL_MALIGN_OFFERING, "邪恶献祭",
    spschool::necromancy,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_MALIGN_OFFERING,
},

{
    SPELL_SEARING_RAY, "灼热射线",
    spschool::conjuration,
    spflag::dir_or_target | spflag::needs_tracer,
    2,
    50,
    4, 4,
    0,
    TILEG_SEARING_RAY,
},

{
    SPELL_DISCORD, "混乱",
    spschool::hexes,
    spflag::hasty | spflag::WL_check,
    8,
    200,
    -1, -1,
    0,
    TILEG_DISCORD,
},

{
    SPELL_INVISIBILITY_OTHER, "隐身他人",
    spschool::hexes,
    spflag::dir_or_target | spflag::helpful | spflag::monster,
    6,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_INVISIBILITY,
},

{
    SPELL_VIRULENCE, "毒性",
    spschool::alchemy | spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer | spflag::WL_check
                          | spflag::monster,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_VIRULENCE,
},

{
    SPELL_ORB_OF_ELECTRICITY, "电击之球",
    spschool::conjuration | spschool::air,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer,
    7,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_ORB_OF_ELECTRICITY,
},

{
    SPELL_FLASH_FREEZE, "瞬间冻结",
    spschool::conjuration | spschool::ice,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer,
    7,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_FLASH_FREEZE,
},

{
    SPELL_CREEPING_FROST, "蔓延冰霜",
    spschool::conjuration | spschool::ice,
    spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_CREEPING_FROST,
},

{
    SPELL_LEGENDARY_DESTRUCTION, "传奇毁灭",
    spschool::conjuration,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer,
    8,
    200,
    5, 5,
    0,
    TILEG_LEGENDARY_DESTRUCTION,
},

{
    SPELL_FORCEFUL_INVITATION, "强制邀请",
    spschool::summoning,
    spflag::monster,
    4,
    200,
    -1, -1,
    0,
    TILEG_FORCEFUL_INVITATION,
},

{
    SPELL_PLANEREND, "位面撕裂",
    spschool::summoning,
    spflag::monster,
    8,
    200,
    -1, -1,
    0,
    TILEG_PLANE_REND,
},

{
    SPELL_CHAIN_OF_CHAOS, "混沌之链",
    spschool::conjuration,
    spflag::monster | spflag::chaotic,
    8,
    200,
    -1, -1,
    0,
    TILEG_CHAIN_OF_CHAOS,
},

{
    SPELL_CALL_OF_CHAOS, "混沌召唤",
    spschool::hexes,
    spflag::chaotic | spflag::monster,
    7,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_CALL_OF_CHAOS,
},

{
    SPELL_SIGN_OF_RUIN, "毁灭之印",
    spschool::necromancy,
    spflag::monster,
    7,
    200,
    -1, -1,
    0,
    TILEG_ABILITY_KIKU_SIGN_OF_RUIN,
},

{
    SPELL_SAP_MAGIC, "削弱魔法",
    spschool::hexes,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SAP_MAGIC,
},

{
    SPELL_MAJOR_DESTRUCTION, "大型毁灭",
    spschool::conjuration,
    spflag::dir_or_target | spflag::chaotic | spflag::needs_tracer
                          | spflag::monster,
    7,
    200,
    6, 6,
    0,
    TILEG_MAJOR_DESTRUCTION,
},

{
    SPELL_BLINK_ALLIES_AWAY, "闪烁盟友远离",
    spschool::translocation,
    spflag::target | spflag::monster,
    6,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_BLINK_ALLIES_AWAY,
},

{
    SPELL_SUMMON_FOREST, "召唤森林",
    spschool::summoning | spschool::translocation,
    spflag::none,
    5,
    200,
    -1, -1,
    10,
    TILEG_SUMMON_FOREST,
},

{
    SPELL_FORGE_LIGHTNING_SPIRE, "锻造闪电尖塔",
    spschool::forgecraft | spschool::air,
    spflag::none,
    4,
    100,
    -1, -1,
    0,
    TILEG_FORGE_LIGHTNING_SPIRE,
},

{
    SPELL_FORGE_BLAZEHEART_GOLEM, "锻造炽心魔像",
    spschool::forgecraft | spschool::fire,
    spflag::none,
    4,
    100,
    -1, -1,
    0,
    TILEG_FORGE_BLAZEHEART_GOLEM,
},

{
    SPELL_REBOUNDING_BLAZE, "弹跳烈焰",
    spschool::conjuration | spschool::fire,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    7,
    200,
    6, 6,
    0,
    TILEG_REBOUNDING_BLAZE,
},

{
    SPELL_REBOUNDING_CHILL, "弹跳寒冷",
    spschool::conjuration | spschool::ice,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    7,
    200,
    6, 6,
    0,
    TILEG_REBOUNDING_CHILL,
},

{
    SPELL_GLACIATE, "冰川",
    spschool::conjuration | spschool::ice,
    spflag::dir_or_target | spflag:: monster,
    9,
    200,
    6, 6,
    25,
    TILEG_ICE_STORM,
},

{
    SPELL_DRAGON_CALL, "龙之呼唤",
    spschool::summoning,
    spflag::none,
    9,
    200,
    -1, -1,
    15,
    TILEG_SUMMON_DRAGON,
},

{
    SPELL_SPELLSPARK_SERVITOR, "法术火花仆从",
    spschool::conjuration | spschool::forgecraft,
    spflag::none,
    7,
    200,
    -1, -1,
    0,
    TILEG_SPELLSPARK_SERVITOR,
},

{
    SPELL_SUMMON_MANA_VIPER, "召唤魔力蝰蛇",
    spschool::summoning | spschool::hexes,
    spflag::mons_abjure,
    5,
    100,
    -1, -1,
    0,
    TILEG_SUMMON_MANA_VIPER,
},

{
    SPELL_PHANTOM_MIRROR, "幻影镜",
    spschool::hexes,
    spflag::none,
    5,
    200,
    -1, -1,
    0,
    TILEG_PHANTOM_MIRROR,
},

{
    SPELL_DIMINISH_SPELLS, "削弱法术",
    spschool::hexes,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer,
    3,
    200,
    LOS_RADIUS, LOS_RADIUS,
    4,
    TILEG_DIMINISH_SPELLS,
},

{
    SPELL_CORROSIVE_BOLT, "腐蚀箭",
    spschool::conjuration | spschool::alchemy,
    spflag::dir_or_target | spflag::needs_tracer,
    6,
    200,
    5, 5,
    0,
    TILEG_CORROSIVE_BOLT,
},

{
    SPELL_BOLT_OF_LIGHT, "光之箭",
    spschool::conjuration | spschool::fire | spschool::air,
    spflag::dir_or_target | spflag::needs_tracer,
    6,
    200,
    5, 5,
    0,
    TILEG_BOLT_OF_LIGHT,
},

{
    SPELL_BOLT_OF_FLESH, "血肉之箭",
    spschool::conjuration | spschool::necromancy | spschool::summoning,
    spflag::dir_or_target | spflag::needs_tracer| spflag::monster
                          | spflag::chaotic,
    6,
    200,
    5, 5,
    0,
    TILEG_BOLT_OF_FLESH,
},

{
    SPELL_AWAKEN_FLESH, "唤醒血肉",
    spschool::conjuration | spschool::necromancy | spschool::hexes,
    spflag::chaotic | spflag::monster,
    6,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_AWAKEN_FLESH,
},

{
    SPELL_SERPENT_OF_HELL_GEH_BREATH, "火焚地狱蛇之吐息",
    spschool::conjuration,
    spflag::dir_or_target | spflag::monster | spflag::noisy
        | spflag::needs_tracer,
    5,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_FIRE_BREATH,
},

{
    SPELL_SERPENT_OF_HELL_COC_BREATH, "冰狱蛇之吐息",
    spschool::conjuration,
    spflag::dir_or_target | spflag::monster | spflag::noisy
        | spflag::needs_tracer,
    5,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_COLD_BREATH,
},

{
    SPELL_SERPENT_OF_HELL_DIS_BREATH, "铁城蛇之吐息",
    spschool::conjuration,
    spflag::dir_or_target | spflag::monster | spflag::noisy
        | spflag::needs_tracer,
    5,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_LEHUDIBS_CRYSTAL_SPEAR,
},

{
    SPELL_SERPENT_OF_HELL_TAR_BREATH, "悲叹地狱蛇之吐息",
    spschool::conjuration,
    spflag::dir_or_target | spflag::monster | spflag::noisy
        | spflag::needs_tracer,
    5,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_MIASMA_BREATH,
},

{
    SPELL_SUMMON_EMPEROR_SCORPIONS, "召唤帝蝎",
    spschool::summoning | spschool::alchemy,
    spflag::mons_abjure | spflag::monster,
    7,
    100,
    -1, -1,
    0,
    TILEG_SUMMON_EMPEROR_SCORPIONS,
},

{
    SPELL_IRRADIATE, "辐射",
    spschool::conjuration | spschool::alchemy,
    spflag::chaotic,
    5,
    200,
    1, 1,
    0,
    TILEG_IRRADIATE,
},

{
    SPELL_SPIT_LAVA, "喷吐岩浆",
    spschool::conjuration | spschool::fire | spschool::earth,
    spflag::dir_or_target | spflag::monster | spflag::noisy
        | spflag::needs_tracer,
    5,
    0,
    5, 5,
    0,
    TILEG_SPIT_LAVA,
},

{
    SPELL_ELECTRICAL_BOLT, "电击箭",
    spschool::conjuration | spschool::air,
    spflag::dir_or_target | spflag::monster | spflag::noisy
        | spflag::needs_tracer,
    5,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_LIGHTNING_BOLT,
},

{
    SPELL_FLAMING_CLOUD, "燃烧云",
    spschool::conjuration | spschool::fire,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer
        | spflag::cloud,
    5,
    0,
    5, 5,
    0,
    TILEG_FLAMING_CLOUD,
},

{
    SPELL_THROW_BARBS, "投掷倒刺",
    spschool::conjuration,
    spflag::dir_or_target | spflag::monster | spflag::noisy
        | spflag::needs_tracer,
    5,
    0,
    5, 5,
    0,
    TILEG_THROW_BARBS,
},

{
    SPELL_BATTLECRY, "战吼",
    spschool::hexes,
    spflag::monster | spflag::selfench,
    6,
    0,
    -1, -1,
    0,
    TILEG_BATTLECRY,
},

{
    SPELL_WARNING_CRY, "警告之嚎",
    spschool::hexes,
    spflag::monster | spflag::selfench | spflag::noisy,
    6,
    0,
    -1, -1,
    25,
    TILEG_WARNING_CRY,
},

{
    SPELL_HUNTING_CALL, "狩猎呼唤",
    spschool::hexes,
    spflag::monster | spflag::selfench,
    6,
    0,
    -1, -1,
    0,
    TILEG_HUNTING_CALL,
},

{
    SPELL_FUNERAL_DIRGE, "葬礼哀歌",
    spschool::necromancy,
    spflag::monster,
    4,
    200,
    -1, -1,
    0,
    TILEG_FUNERAL_DIRGE,
},

{
    SPELL_SEAL_DOORS, "封印门",
    spschool::hexes,
    spflag::monster | spflag::selfench,
    6,
    0,
    -1, -1,
    0,
    TILEG_SEAL_DOORS,
},

{
    SPELL_FLAY, "剥皮",
    spschool::necromancy,
    spflag::target | spflag::monster,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_FLAY,
},

{
    SPELL_BERSERK_OTHER, "狂暴他人",
    spschool::hexes,
    spflag::hasty | spflag::monster | spflag::helpful,
    3,
    0,
    3, 3,
    0,
    TILEG_BERSERK_OTHER,
},

{
    SPELL_CORRUPTING_PULSE, "腐化脉冲",
    spschool::hexes | spschool::alchemy,
    spflag::monster,
    6,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_CORRUPTING_PULSE,
},

{
    SPELL_SIREN_SONG, "塞壬之歌",
    spschool::hexes,
    spflag::WL_check | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SIREN_SONG,
},

{
    SPELL_AVATAR_SONG, "化身之歌",
    spschool::hexes,
    spflag::WL_check | spflag::monster,
    7,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_AVATAR_SONG,
},

{
    SPELL_PARALYSIS_GAZE, "麻痹凝视",
    spschool::hexes,
    spflag::target | spflag::monster,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_PARALYSIS_GAZE,
},

{
    SPELL_CONFUSION_GAZE, "困惑凝视",
    spschool::hexes,
    spflag::target | spflag::monster | spflag::WL_check,
    3,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_CONFUSION_GAZE,
},

{
    SPELL_ANTIMAGIC_GAZE, "反魔法凝视",
    spschool::hexes,
    spflag::target | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_ANTIMAGIC_GAZE,
},

{
    SPELL_DRAINING_GAZE, "吸取凝视",
    spschool::necromancy,
    spflag::target | spflag::monster,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_DRAINING_GAZE,
},


{
    SPELL_WEAKENING_GAZE, "虚弱凝视",
    spschool::hexes,
    spflag::target | spflag::monster,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_WEAKENING_GAZE,
},

{
    SPELL_MOURNING_WAIL, "哀悼嚎哭",
    spschool::necromancy,
    spflag::dir_or_target | spflag::monster,
    3,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_MOURNING_WAIL,
},

{
    SPELL_DEATH_RATTLE, "死亡之响",
    spschool::conjuration | spschool::necromancy | spschool::air,
    spflag::dir_or_target | spflag::monster,
    7,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_DEATH_RATTLE,
},

{
    SPELL_MARCH_OF_SORROWS, "悲伤行军",
    spschool::conjuration | spschool::necromancy | spschool::air,
    spflag::dir_or_target | spflag::monster,
    7,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_MARCH_OF_SORROWS,
},

{
    SPELL_SUMMON_SCARABS, "召唤圣甲虫",
    spschool::summoning | spschool::necromancy,
    spflag::mons_abjure | spflag::monster,
    7,
    100,
    -1, -1,
    0,
    TILEG_SUMMON_SCARABS,
},

{
    SPELL_THROW_ALLY, "投掷盟友",
    spschool::translocation,
    spflag::target | spflag::monster,
    2,
    50,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_THROW_ALLY,
},

{
    SPELL_CLEANSING_FLAME, "净化之焰",
    spschool::none,
    spflag::monster | spflag::holy,
    8,
    200,
    -1, -1,
    0,
    TILEG_CLEANSING_FLAME,
},

// Evoker-only now
{
    SPELL_GRAVITAS, "盖尔之重力",
    spschool::translocation,
    spflag::target | spflag::needs_tracer | spflag::no_ghost,
    3,
    100,
    LOS_RADIUS, LOS_RADIUS,
    8,
    TILEG_GRAVITAS,
},

{
    SPELL_VIOLENT_UNRAVELLING, "亚拉之猛烈解构",
    spschool::hexes | spschool::alchemy,
    spflag::target | spflag::no_ghost | spflag::chaotic | spflag::destructive,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_VIOLENT_UNRAVELLING,
},

{
    SPELL_ENTROPIC_WEAVE, "熵之编织",
    spschool::hexes,
    spflag::target | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_ENTROPIC_WEAVE,
},

{
    SPELL_SUMMON_EXECUTIONERS, "召唤行刑者",
    spschool::summoning,
    spflag::unholy | spflag::mons_abjure | spflag::monster,
    9,
    200,
    -1, -1,
    0,
    TILEG_SUMMON_EXECUTIONERS,
},

{
    SPELL_OBLIVION_HOWL, "湮灭嚎叫",
    spschool::translocation | spschool::hexes,
    spflag::target | spflag::monster | spflag::WL_check,
    3,
    200,
    LOS_RADIUS, LOS_RADIUS,
    15,
    TILEG_OBLIVION_HOWL,
},

{
    SPELL_PRAYER_OF_BRILLIANCE, "聪慧祈祷",
    spschool::conjuration,
    spflag::helpful | spflag::monster,
    5,
    200,
    -1, -1,
    0,
    TILEG_PRAYER_OF_BRILLIANCE,
},

{
    SPELL_ICEBLAST, "冰爆",
    spschool::conjuration | spschool::ice,
    spflag::dir_or_target | spflag::needs_tracer,
    5,
    200,
    5, 5,
    0,
    TILEG_ICEBLAST,
},

{
    SPELL_SLUG_DART, "蛞蝓飞镖",
    spschool::conjuration,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    1,
    25,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SLUG_DART,
},

{
    SPELL_FLEETFOOT, "轻快脚步",
    spschool::air,
    spflag::hasty | spflag::selfench | spflag::monster,
    2,
    100,
    -1, -1,
    0,
    TILEG_SWIFTNESS,
},

{
    SPELL_GREATER_SERVANT_MAKHLEB, "地狱仆从",
    spschool::summoning,
    spflag::unholy | spflag::mons_abjure | spflag::monster,
    7,
    200,
    -1, -1,
    0,
    TILEG_ABILITY_MAKHLEB_GREATER_SERVANT,
},

{
    SPELL_BIND_SOULS, "绑定灵魂",
    spschool::necromancy | spschool::ice,
    spflag::monster,
    6,
    200,
    -1, -1,
    0,
    TILEG_DEATH_CHANNEL,
},

{
    SPELL_INFESTATION, "虫群侵扰",
    spschool::necromancy,
    spflag::target | spflag::unclean,
    8,
    200,
    LOS_RADIUS, LOS_RADIUS,
    4,
    TILEG_INFESTATION,
},

{
    SPELL_STILL_WINDS, "静止风",
    spschool::hexes | spschool::air,
    spflag::monster | spflag::selfench,
    6,
    200,
    -1, -1,
    0,
    TILEG_STILL_WINDS,
},

{
    SPELL_RESONANCE_STRIKE, "共鸣打击",
    spschool::earth,
    spflag::target | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_RESONANCE_STRIKE,
},

{
    SPELL_GHOSTLY_SACRIFICE, "幽灵献祭",
    spschool::necromancy,
    spflag::target | spflag::monster,
    7,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_GHOSTLY_FIREBALL,
},

{
    SPELL_DREAM_DUST, "梦尘",
    spschool::hexes,
    spflag::target | spflag::monster,
    3,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_DREAM_DUST,
},

{
    SPELL_BECKONING, "次级召唤",
    spschool::translocation,
    spflag::dir_or_target | spflag::not_self | spflag::needs_tracer,
    2,
    50,
    3, 5,
    0,
    TILEG_BECKONING,
},

// Monster-only, players can use Qazlal's ability
{
    SPELL_UPHEAVAL, "剧变",
    spschool::conjuration,
    spflag::target | spflag::needs_tracer | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_ABILITY_QAZLAL_UPHEAVAL,
},

{
    SPELL_MERCURY_ARROW, "汞矢",
    spschool::alchemy | spschool::conjuration,
    spflag::dir_or_target | spflag::needs_tracer,
    2,
    50,
    4, 4,
    0,
    TILEG_STING,
},

{
    SPELL_POISONOUS_VAPOURS, "毒气",
    spschool::alchemy | spschool::air,
    spflag::target | spflag::destructive | spflag::not_self,
    1,
    25,
    3, 3,
    0,
    TILEG_POISONOUS_CLOUD,
},

{
    SPELL_IGNITION, "点火",
    spschool::fire,
    spflag::destructive,
    8,
    200,
    -1, -1,
    0,
    TILEG_IGNITION,
},

{
    SPELL_BORGNJORS_VILE_CLUTCH, "博格尼尔之邪恶抓握",
    spschool::necromancy | spschool::earth,
    spflag::dir_or_target | spflag::not_self | spflag::needs_tracer,
    5,
    200,
    6, 6,
    5,
    TILEG_BORGNJORS_VILE_CLUTCH,
},

{
    SPELL_FASTROOT, "快速扎根",
    spschool::hexes | spschool::earth,
    spflag::dir_or_target | spflag::needs_tracer,
    5,
    200,
    5, 5,
    0,
    TILEG_GRASPING_ROOTS,
},

{
    SPELL_WARP_SPACE, "扭曲空间",
    spschool::translocation,
    spflag::dir_or_target | spflag::needs_tracer,
    5,
    200,
    5, 5,
    0,
    TILEG_WARP_SPACE,
},

{
    SPELL_SOJOURNING_BOLT, "旅居之箭",
    spschool::conjuration | spschool::translocation,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    6,
    200,
    5, 5,
    0,
    TILEG_SOJOURNING_BOLT,
},

{
    SPELL_HARPOON_SHOT, "鱼叉射击",
    spschool::conjuration | spschool::earth,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    4,
    200,
    6, 6,
    0,
    TILEG_HARPOON_SHOT,
},

{
    SPELL_GRASPING_ROOTS, "抓握根须",
    spschool::earth,
    spflag::target | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_GRASPING_ROOTS,
},

{
    SPELL_THROW_BOLAS, "投掷流星索",
    spschool::conjuration,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    4,
    200,
    6, 6,
    0,
    TILEG_THROW_BOLAS,
},


{
    SPELL_THROW_PIE, "投掷小丑派",
    spschool::conjuration | spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_THROW_KLOWN_PIE,
},

{
    SPELL_SPORULATE, "产孢",
    spschool::conjuration | spschool::earth,
    spflag::monster,
    5,
    200,
    -1, -1,
    0,
    TILEG_SPORULATE,
},

{
    SPELL_LAUNCH_SPORANGIUM, "发射孢子囊",
    spschool::conjuration,
    spflag::monster,
    5,
    200,
    -1, -1,
    0,
    TILEG_LAUNCH_SPORANGIUM,
},

{
    SPELL_STARBURST, "星爆",
    spschool::conjuration | spschool::fire,
    spflag::none,
    6,
    200,
    5, 5,
    0,
    TILEG_STARBURST,
},

{
    SPELL_FOXFIRE, "狐火",
    spschool::conjuration | spschool::fire,
    spflag::none,
    1,
    25,
    -1, -1,
    0,
    TILEG_FOXFIRE,
},

{
    SPELL_MARSHLIGHT, "沼泽之光",
    spschool::conjuration | spschool::fire,
    spflag::monster,
    4,
    200,
    -1, -1,
    0,
    TILEG_FOXFIRE,
},

{
    SPELL_HAILSTORM, "冰雹风暴",
    spschool::conjuration | spschool::ice,
    spflag::none,
    3,
    100,
    3, 3, // Range special-cased in describe-spells
    0,
    TILEG_HAILSTORM,
},

{
    SPELL_NOXIOUS_BOG, "埃林吉亚之有毒沼泽",
    spschool::alchemy,
    spflag::no_ghost | spflag::destructive,
    6,
    200,
    4, 4,
    0,
    TILEG_NOXIOUS_BOG,
},

{
    SPELL_AGONY, "痛苦折磨",
    spschool::necromancy,
    spflag::dir_or_target | spflag::needs_tracer
        | spflag::monster | spflag::WL_check,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_AGONY,
},

{
    SPELL_DISPEL_UNDEAD_RANGE, "远程驱散亡灵",
    spschool::necromancy,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    5,
    100,
    4, 4,
    0,
    TILEG_DISPEL_UNDEAD,
},

{
    SPELL_FROZEN_RAMPARTS, "冰冻壁垒",
    spschool::ice,
    spflag::no_ghost | spflag::destructive,
    3,
    50,
    2, 2,
    8,
    TILEG_FROZEN_RAMPARTS,
},

{
    SPELL_MAXWELLS_COUPLING, "麦克斯韦之电容耦合",
    spschool::air,
    spflag::no_ghost | spflag::destructive,
    8,
    200,
    LOS_RADIUS, LOS_RADIUS,
    25,
    TILEG_MAXWELLS_COUPLING,
},

{
    // This "spell" is implemented in a way that ignores all this information,
    // and it is never triggered the way spells usually are, but it still has
    // a spell-type enum entry. So, use fake data in order to have a valid
    // entry here. If it ever were to be castable, this would need some updates.
    SPELL_SONIC_WAVE, "音波",
    spschool::none,
    spflag::noisy,
    7, 0, -1, -1, 0, TILEG_ERROR
},

{
    SPELL_ROLL, "滚动",
    spschool::earth,
    spflag::monster,
    5,
    0,
    -1, -1,
    0,
    TILEG_ROLL
},

{
    SPELL_HURL_SLUDGE, "投掷污泥",
    spschool::alchemy | spschool::conjuration,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    6,
    200,
    5, 5,
    0,
    TILEG_HURL_SLUDGE
},

{
    SPELL_SUMMON_TZITZIMITL, "召唤齐齐米特尔",
    spschool::summoning | spschool::necromancy,
    spflag::monster | spflag::mons_abjure,
    8,
    0,
    -1, -1,
    0,
    TILEG_SUMMON_TZITZIMITL,
},

{
    SPELL_SUMMON_HELL_SENTINEL, "召唤地狱哨兵",
    spschool::summoning,
    spflag::monster | spflag::mons_abjure,
    8,
    0,
    -1, -1,
    0,
    TILEG_SUMMON_HELL_SENTINEL,
},

{
    SPELL_AWAKEN_ARMOUR, "唤醒护甲",
    spschool::forgecraft | spschool::earth,
    spflag::none,
    4,
    50,
    -1, -1,
    0,
    TILEG_AWAKEN_ARMOUR,
},

{
    SPELL_MANIFOLD_ASSAULT, "多重攻击",
    spschool::translocation,
    spflag::none,
    7,
    200,
    -1, -1,
    0,
    TILEG_MANIFOLD_ASSAULT,
},

{
    SPELL_CONCENTRATE_VENOM, "浓缩毒液",
    spschool::alchemy,
    spflag::dir_or_target | spflag::helpful
        | spflag::needs_tracer | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_CONCENTRATE_VENOM,
},

{
    SPELL_ERUPTION, "喷发",
    spschool::conjuration | spschool::fire | spschool::earth,
    spflag::target | spflag::needs_tracer | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_ERUPTION,
},

{
    SPELL_PYROCLASTIC_SURGE, "火山碎屑涌",
    spschool::conjuration | spschool::fire | spschool::earth,
    spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_PYROCLASTIC_SURGE,
},

{
    SPELL_STUNNING_BURST, "眩晕爆发",
    spschool::conjuration | spschool::air,
    spflag::target | spflag::needs_tracer | spflag::monster,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_STUNNING_BURST,
},

{
    SPELL_CORRUPT_LOCALE, "腐化",
    spschool::translocation,
    spflag::monster,
    7,
    0,
    -1, -1,
    0,
    TILEG_CORRUPT,
},

{
    SPELL_CONJURE_LIVING_SPELLS, "召唤活体法术",
    spschool::conjuration,
    spflag::monster,
    6,
    200,
    -1, -1,
    0,
    TILEG_CONJURE_LIVING_SPELLS,
},

{
    SPELL_SUMMON_CACTUS, "召唤仙人掌巨人",
    spschool::summoning,
    spflag::none,
    6,
    200,
    -1, -1,
    0,
    TILEG_SUMMON_CACTUS_GIANT,
},

{
    SPELL_STOKE_FLAMES, "煽动火焰",
    spschool::fire | spschool::conjuration,
    spflag::monster,
    8,
    0,
    -1, -1,
    0,
    TILEG_STOKE_FLAMES,
},

{
    SPELL_SERACFALL, "冰塔崩塌",
    spschool::conjuration | spschool::ice,
    spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_ICEBLAST,
},

{
    SPELL_SCORCH, "烧焦",
    spschool::fire,
    spflag::destructive,
    2,
    50,
    3, 3,
    8,
    TILEG_SCORCH,
},

{
    SPELL_FLAME_WAVE, "火焰波",
    spschool::conjuration | spschool::fire,
    spflag::none,
    4,
    100,
    3, 3, // sort of...
    12, // increases as it's channeled
    TILEG_FLAME_WAVE,
},

{
    SPELL_ENFEEBLE, "虚弱",
    spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer | spflag::WL_check,
    7,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_ENFEEBLE,
},

{
    SPELL_SUMMON_SPIDERS, "召唤蜘蛛",
    spschool::summoning | spschool::alchemy,
    spflag::monster,
    6,
    200,
    -1, -1,
    0,
    TILEG_SUMMON_SPIDERS,
},

{
    SPELL_ANGUISH, "痛苦",
    spschool::hexes | spschool::necromancy,
    spflag::WL_check,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_ANGUISH,
},

{
    SPELL_SUMMON_SCORPIONS, "召唤蝎子",
    spschool::summoning | spschool::alchemy,
    spflag::mons_abjure | spflag::monster,
    4,
    200,
    -1, -1,
    0,
    TILEG_SUMMON_SCORPIONS,
},

{
    SPELL_SHEZAS_DANCE, "谢扎之舞",
    spschool::summoning | spschool::earth,
    spflag::mons_abjure | spflag::monster,
    5,
    200,
    -1, -1,
    0,
    TILEG_SHEZAS_DANCE,
},

{
    SPELL_DIVINE_ARMAMENT, "神圣武装",
    spschool::summoning,
    spflag::monster,
    4,
    200,
    -1, -1,
    0,
    TILEG_DIVINE_ARMAMENT,
},

{
    SPELL_KISS_OF_DEATH, "死亡之吻",
    spschool::conjuration | spschool::necromancy,
    spflag::dir_or_target | spflag::needs_tracer | spflag::not_self,
    1,
    25,
    1, 1,
    0,
    TILEG_KISS_OF_DEATH,
},

{
    SPELL_JINXBITE, "厄运之咬",
    spschool::hexes,
    spflag::selfench,
    2,
    50,
    -1, -1,
    0,
    TILEG_JINXBITE,
},

{
    SPELL_SIGIL_OF_BINDING, "束缚符文",
    spschool::hexes,
    spflag::none,
    3,
    100,
    -1, -1,
    0,
    TILEG_SIGIL_OF_BINDING,
},

{
    SPELL_DIMENSIONAL_BULLSEYE, "维度靶心",
    spschool::translocation | spschool::hexes,
    spflag::target | spflag::not_self | spflag::prefer_farthest,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_PORTAL_PROJECTILE,
},

{
    SPELL_BOULDER, "布罗姆之碾压巨石",
    spschool::earth | spschool::conjuration,
    spflag::target | spflag::not_self,
    4,
    100,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_BOULDER,
},

{
    SPELL_VITRIFY, "玻璃化",
    spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer | spflag::WL_check
                          | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_VITRIFY,
},

{
    SPELL_VITRIFYING_GAZE, "玻璃化凝视",
    spschool::hexes,
    spflag::target | spflag::monster,
    6,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_VITRIFYING_GAZE,
},

{
    SPELL_CRYSTALLISING_SHOT, "结晶射击",
    spschool::conjuration | spschool::earth | spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    6,
    50,
    4, 4,
    0,
    TILEG_CRYSTALLISING_SHOT,
},

{
    SPELL_TREMORSTONE, "震石",
    spschool::earth,
    spflag::none,
    2,
    200,
    -1, -1,
    15,
    TILEG_LEES_RAPID_DECONSTRUCTION, // close enough
},

{
    SPELL_REGENERATE_OTHER, "治愈他人",
    spschool::none,
    spflag::monster | spflag::helpful | spflag::recovery,
    4,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_REGENERATION,
},

{
    SPELL_MASS_REGENERATION, "群体再生",
    spschool::none,
    spflag::monster  | spflag::helpful | spflag::recovery,
    7,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_MASS_REGENERATION,
},

{
    SPELL_NOXIOUS_BREATH, "毒气吐息",
    spschool::conjuration | spschool::air | spschool:: alchemy,
    spflag::dir_or_target | spflag::noisy | spflag::needs_tracer,
    5,
    0,
    6, 6,
    0,
    TILEG_NOXIOUS_CLOUD,
},

// Dummy spell for the Makhleb ability.
{
    SPELL_UNLEASH_DESTRUCTION, "释放毁灭",
    spschool::conjuration,
    spflag::dir_or_target | spflag::chaotic | spflag::needs_tracer,
    3,
    0,
    LOS_RADIUS, LOS_RADIUS,
    6,
    TILEG_ERROR,
},

{
    SPELL_HURL_TORCHLIGHT, "投掷火炬之光",
    spschool::conjuration | spschool::necromancy,
    spflag::dir_or_target | spflag::needs_tracer,
    4,
    200,
    5, 5,
    0,
    TILEG_ABILITY_YRED_HURL_TORCHLIGHT,
},

{
    SPELL_COMBUSTION_BREATH, "燃烧吐息",
    spschool::conjuration | spschool::fire,
    spflag::dir_or_target | spflag::needs_tracer,
    5,
    0,
    5, 5,
    0,
    TILEG_FIRE_BREATH,
},

{
    SPELL_NULLIFYING_BREATH, "湮灭吐息",
    spschool::conjuration,
    spflag::dir_or_target | spflag::needs_tracer,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    5,
    TILEG_QUICKSILVER_BOLT,
},

{
    SPELL_STEAM_BREATH, "蒸汽吐息",
    spschool::conjuration,
    spflag::dir_or_target | spflag::needs_tracer,
    4,
    0,
    6, 6,
    0,
    TILEG_STEAM_BALL,
},

{
    SPELL_MUD_BREATH, "泥浆吐息",
    spschool::conjuration | spschool::earth,
    spflag::dir_or_target | spflag::needs_tracer,
    5,
    0,
    6, 6,
    10,
    TILEG_LEDAS_LIQUEFACTION,
},

{
    SPELL_GALVANIC_BREATH, "电流吐息",
    spschool::conjuration | spschool::air,
    spflag::dir_or_target | spflag::needs_tracer,
    5,
    0,
    LOS_RADIUS, LOS_RADIUS,
    10,
    TILEG_ARCJOLT,
},

{
    SPELL_PILEDRIVER, "麦克斯韦之便携打桩机",
    spschool::translocation,
    spflag::target,
    3,
    100,
    5, 5,
    0,
    TILEG_PILEDRIVER,
},

{
    SPELL_GELLS_GAVOTTE, "盖尔之加沃特",
    spschool::translocation,
    spflag::target | spflag::aim_at_space,
    6,
    200,
    1, 1,
    0,
    TILEG_GAVOTTE,
},

{
    SPELL_MAGNAVOLT, "磁暴",
    spschool::air | spschool::earth,
    spflag::target | spflag::needs_tracer | spflag::destructive
    | spflag::prefer_farthest,
    7,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_MAGNAVOLT,
},

{
    SPELL_FULSOME_FUSILLADE, "猛烈连射",
    spschool::alchemy | spschool::conjuration,
    spflag::destructive | spflag::chaotic,
    8,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_FULSOME_FUSILLADE,
},

{
    SPELL_RIMEBLIGHT, "霜疫",
    spschool::necromancy | spschool::ice,
    spflag::dir_or_target | spflag::unclean | spflag::destructive
    | spflag::not_self,
    7,
    200,
    5, 5,
    0,
    TILEG_RIMEBLIGHT,
},

{
    SPELL_HOARFROST_CANNONADE, "白霜炮击",
    spschool::forgecraft | spschool::ice,
    spflag::none,
    5,
    200,
    -1, -1,
    0,
    TILEG_HOARFROST_CANNONADE,
},

{
    SPELL_SEISMIC_STOMP, "地震践踏",
    spschool::earth,
    spflag::monster,
    5,
    200,
    4, 4,
    8,
    TILEG_SEISMIC_STOMP,
},

{
    SPELL_HOARFROST_BULLET, "白霜弹",
    spschool::conjuration | spschool::ice,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    5,
    200,
    6, 6,
    0,
    TILEG_HOARFROST_BULLET,
},

{
    SPELL_FLASHING_BALESTRA, "闪光弩击",
    spschool::conjuration,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    5,
    200,
    6, 6,
    0,
    TILEG_TUKIMAS_DANCE,
},

{
    SPELL_PHANTOM_BLITZ, "幻影突击",
    spschool::conjuration | spschool::summoning,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    7,
    200,
    5, 5,
    0,
    TILEG_PHANTOM_BLITZ,
},

{
    SPELL_BESTOW_ARMS, "赐予武器",
    spschool::hexes,
    spflag::helpful | spflag::monster,
    5,
    200,
    6, 6,
    0,
    TILEG_BESTOW_ARMS,
},

{
    SPELL_HELLFIRE_MORTAR, "地狱火迫击炮",
    spschool::earth | spschool::fire | spschool::forgecraft,
    spflag::dir_or_target | spflag::destructive,
    7,
    200,
    LOS_RADIUS, LOS_RADIUS,
    20,
    TILEG_HELLFIRE_MORTAR,
},

// Dithmenos shadow mimic spells
{
    SPELL_SHADOW_SHARD, "暗影碎片",
    spschool::earth,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer
    | spflag::silent,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SHADOW_SHARD,
},

{
    SPELL_SHADOW_BEAM, "暗影光束",
    spschool::conjuration,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer
    | spflag::silent,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SHADOW_BEAM,
},

{
    SPELL_SHADOW_BALL, "暗影球",
    spschool::fire,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer
    | spflag::silent,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SHADOWBALL,
},

{
    SPELL_CREEPING_SHADOW, "蔓延暗影",
    spschool::ice,
    spflag::monster | spflag::needs_tracer | spflag::silent,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_CREEPING_SHADOW,
},

{
    SPELL_SHADOW_TEMPEST, "暗影风暴",
    spschool::air,
    spflag::monster | spflag::needs_tracer | spflag::silent,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SHADOW_TEMPEST,
},

{
    SPELL_SHADOW_PRISM, "暗影棱镜",
    spschool::alchemy,
    spflag::target | spflag::monster | spflag::needs_tracer | spflag::silent,
    5,
    200,
    4, 4,
    0,
    TILEG_SHADOW_PRISM,
},


{
    SPELL_SHADOW_PUPPET, "暗影傀儡",
    spschool::summoning,
    spflag::monster | spflag::silent,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SHADOW_PUPPET,
},

{
    SPELL_SHADOW_TURRET, "暗影炮台",
    spschool::forgecraft,
    spflag::monster | spflag::silent,
    5,
    200,
    -1, -1,
    0,
    TILEG_SHADOW_TURRET,
},

{
    SPELL_SHADOW_SHOT, "暗影射击",
    spschool::forgecraft,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer
    | spflag::silent,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SHADOW_SHARD,
},

{
    SPELL_SHADOW_BIND, "暗影束缚",
    spschool::translocation,
    spflag::target | spflag::monster | spflag::silent,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SHADOW_BIND,
},

{
    SPELL_SHADOW_TORPOR, "暗影麻木",
    spschool::hexes,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer
    | spflag::silent,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_SHADOW_TORPOR,
},

{
    SPELL_SHADOW_DRAINING, "暗影吸取",
    spschool::necromancy,
    spflag::monster | spflag::needs_tracer | spflag::silent,
    5,
    200,
    2, 2,
    0,
    TILEG_SHADOW_DRAINING,
},

{
    SPELL_GRAVE_CLAW, "墓爪",
    spschool::necromancy,
    spflag::target | spflag::not_self,
    2,
    50,
    4, 4,
    0,
    TILEG_GRAVE_CLAW,
},

{
    SPELL_CLOCKWORK_BEE, "发射发条蜜蜂",
    spschool::forgecraft,
    spflag::target | spflag::not_self,
    3,
    100,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_CLOCKWORK_BEE,
},

{
    SPELL_SPIKE_LAUNCHER, "构建尖刺发射器",
    spschool::forgecraft,
    spflag::none,
    2,
    50,
    -1, -1,
    0,
    TILEG_SPIKE_LAUNCHER,
},

{
    SPELL_KINETIC_GRAPNEL, "动能抓钩",
    spschool::forgecraft,
    spflag::dir_or_target | spflag::needs_tracer | spflag::destructive,
    1,
    25,
    4, 4,
    0,
    TILEG_KINETIC_GRAPNEL,
},

{
    SPELL_DIAMOND_SAWBLADES, "钻石锯片",
    spschool::forgecraft,
    spflag::none,
    7,
    200,
    -1, -1,
    0,
    TILEG_DIAMOND_SAWBLADES,
},

{
    SPELL_SHRED, "撕裂",
    spschool::forgecraft,
    spflag::monster,
    1,
    200,
    1, 1,
    0,
    TILEG_DIAMOND_SAWBLADES,
},

{
    SPELL_SURPRISING_CROCODILE, "埃林吉亚之惊喜鳄鱼",
    spschool::summoning,
    spflag::target | spflag::not_self,
    4,
    100,
    1, 1,
    0,
    TILEG_SURPRISING_CROCODILE,
},

{
    SPELL_PLATINUM_PARAGON, "白金典范",
    spschool::forgecraft,
    spflag::target | spflag::not_self,
    9,
    200,
    3, 3,
    15, // XX: uses default explosion noise, this number is just used for UI
    TILEG_PLATINUM_PARAGON,
},

{
    SPELL_WALKING_ALEMBIC, "阿利斯泰尔之行走蒸馏器",
    spschool::forgecraft | spschool::alchemy,
    spflag::none,
    5,
    100,
    -1, -1,
    0,
    TILEG_WALKING_ALEMBIC,
},

{
    SPELL_MONARCH_BOMB, "锻造君主炸弹",
    spschool::forgecraft | spschool::fire,
    spflag::none,
    6,
    200,
    -1, -1,
    0,
    TILEG_MONARCH_BOMB,
},

{
    SPELL_DEPLOY_BOMBLET, "发射小型炸弹",
    spschool::forgecraft | spschool::fire,
    spflag::target | spflag::monster,
    6,
    200,
    4, 4,
    0,
    TILEG_LAUNCH_BOMBLET,
},

{
    SPELL_SPLINTERFROST_SHELL, "碎霜之壳",
    spschool::forgecraft | spschool::ice,
    spflag::target | spflag::not_self,
    7,
    200,
    1, 1,
    0,
    TILEG_SPLINTERFROST_SHELL,
},

{
    SPELL_PERCUSSIVE_TEMPERING, "纳兹亚之冲击淬炼",
    spschool::forgecraft,
    spflag::target | spflag::helpful | spflag::not_self | spflag::destructive,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_PERCUSSIVE_TEMPERING,
},

{
    SPELL_ALL_PURPOSE_TEMPERING, "纳兹亚之通用淬炼",
    spschool::forgecraft,
    spflag::target | spflag::helpful | spflag::destructive
    | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_PERCUSSIVE_TEMPERING,
},

{
    SPELL_FORTRESS_BLAST, "堡垒冲击波",
    spschool::forgecraft,
    spflag::destructive,
    6,
    75,
    3, 3,
    20,
    TILEG_FORTRESS_BLAST,
},

{
    SPELL_SUMMON_SEISMOSAURUS_EGG, "召唤震龙蛋",
    spschool::summoning | spschool::earth,
    spflag::none,
    4,
    100,
    -1, -1,
    0,
    TILEG_SUMMON_SEISMOSAURUS_EGG,
},

{
    SPELL_PHALANX_BEETLE, "锻造方阵甲虫",
    spschool::forgecraft,
    spflag::none,
    6,
    200,
    -1, -1,
    0,
    TILEG_PHALANX_BEETLE,
},

{
    SPELL_RENDING_BLADE, "撕裂之刃",
    spschool::conjuration | spschool::forgecraft,
    spflag::none,
    4,
    100,
    -1, -1,
    0,
    TILEG_RENDING_BLADE,
},

{
    SPELL_MAGMA_BARRAGE, "岩浆弹幕",
    spschool::conjuration | spschool::fire | spschool::earth,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    5,
    200,
    5, 5,
    0,
    TILEG_MAGMA_BARRAGE,
},

{
    SPELL_VEX, "激怒",
    spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer
        | spflag::WL_check | spflag::monster,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_VEX,
},

{
    SPELL_RAVENOUS_SWARM, "贪婪虫群",
    spschool::necromancy,
    spflag::dir_or_target | spflag::monster
        | spflag::needs_tracer | spflag::cloud,
    6,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_RAVENOUS_SWARM,
},

{
    SPELL_DOMINATE_UNDEAD, "支配亡灵",
    spschool::hexes | spschool::necromancy,
    spflag::WL_check | spflag::monster,
    6,
    200,
    -1, -1,
    0,
    TILEG_DOMINATE_UNDEAD,
},

{
    SPELL_DETONATION_CATALYST, "引爆催化剂",
    spschool::fire | spschool::alchemy,
    spflag::selfench,
    5,
    100,
    -1, -1,
    15,
    TILEG_DETONATION_CATALYST,
},

{
    SPELL_RUST_BREATH, "锈蚀吐息",
    spschool::conjuration | spschool::alchemy | spschool::air,
    spflag::dir_or_target | spflag::needs_tracer,
    5,
    200,
    4, 4,
    0,
    TILEG_MEPHITIC_CLOUD,
},

{
    SPELL_GOLDEN_BREATH, "黄金吐息",
    spschool::conjuration | spschool::fire | spschool::ice | spschool::alchemy,
    spflag::dir_or_target | spflag::needs_tracer,
    5,
    0,
    5, 5,
    0,
    TILEG_FIRE_BREATH,
},

{
    SPELL_SPHINX_SISTERS, "斯芬克斯姐妹",
    spschool::summoning | spschool::hexes,
    spflag::mons_abjure,
    7,
    200,
    -1, -1,
    0,
    TILEG_SPHINX_SISTERS,
},

{
    SPELL_ILL_OMEN, "凶兆",
    spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_ILL_OMEN,
},

{
    SPELL_DOOM_BOLT, "厄运之箭",
    spschool::conjuration | spschool::hexes,
    spflag::dir_or_target | spflag::monster | spflag::needs_tracer,
    5,
    0,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_DOOM_BOLT,
},

{
    SPELL_WARP_BODY, "扭曲身体",
    spschool::hexes,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster
    | spflag::chaotic,
    4,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_WARP_BODY,
},

{
    SPELL_OSTRACISE, "排斥",
    spschool::hexes,
    spflag::monster | spflag::target,
    7,
    200,
    3, 3,
    0,
    TILEG_OSTRACISE,
},

{
    SPELL_MUTAGENIC_GAZE, "变异凝视",
    spschool::hexes,
    spflag::target | spflag::monster | spflag::chaotic,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    0,
    TILEG_MUTAGENIC_GAZE,
},

{
    SPELL_ACID_BALL, "酸液球",
    spschool::conjuration | spschool::alchemy,
    spflag::dir_or_target | spflag::needs_tracer | spflag::monster,
    5,
    200,
    5, 5,
    0,
    TILEG_ACID_BALL,
},

{
    SPELL_NO_SPELL, "不存在的法术",
    spschool::none,
    spflag::testing,
    1,
    0,
    -1, -1,
    0,
    TILEG_ERROR,
},

// Dummy spells for description purposes
{
    SPELL_PYRRHIC_RECOLLECTION, "惨胜回忆",
    spschool::none,
    spflag::monster | spflag::dummy,
    6,
    200,
    -1, -1,
    0,
    TILEG_ABILITY_ENKINDLE,
},

{
    SPELL_PLANAR_OVERLAY, "位面叠加",
    spschool::none,
    spflag::monster | spflag::dummy,
    6,
    200,
    -1, -1,
    0,
    TILEG_PLANAR_OVERLAY,
},

{
    SPELL_DOOMSAYING, "宣告厄运",
    spschool::none,
    spflag::monster,
    6,
    200,
    -1, -1,
    0,
    TILEG_ILL_OMEN,
},

{
    SPELL_SLEETSTRIKE, "冰雨打击",
    spschool::air | spschool::ice,
    spflag::target | spflag::destructive | spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    4,
    TILEG_SLEETSTRIKE,
},

{
    SPELL_LANDBREAKER, "裂地",
    spschool::earth,
    spflag::monster,
    5,
    200,
    LOS_RADIUS, LOS_RADIUS,
    8,
    TILEG_SEISMIC_STOMP,
},

#if TAG_MAJOR_VERSION == 34
#define AXED_SPELL(tag, name) \
    { tag, name, spschool::none, spflag::none, 7, 0, -1, -1, 0, TILEG_ERROR },

AXED_SPELL(SPELL_AURA_OF_ABJURATION, "Aura of Abjuration")
AXED_SPELL(SPELL_BOLT_OF_INACCURACY, "Bolt of Inaccuracy")
AXED_SPELL(SPELL_CHANT_FIRE_STORM, "Chant Fire Storm")
AXED_SPELL(SPELL_CIGOTUVIS_DEGENERATION, "Cigotuvi's Degeneration")
AXED_SPELL(SPELL_CIGOTUVIS_EMBRACE, "Cigotuvi's Embrace")
AXED_SPELL(SPELL_CONDENSATION_SHIELD, "Condensation Shield")
AXED_SPELL(SPELL_CONTROLLED_BLINK, "Controlled Blink")
AXED_SPELL(SPELL_CONTROL_TELEPORT, "Control Teleport")
AXED_SPELL(SPELL_CONTROL_UNDEAD, "Control Undead")
AXED_SPELL(SPELL_CONTROL_WINDS, "Control Winds")
AXED_SPELL(SPELL_CORRUPT_BODY, "Corrupt Body")
AXED_SPELL(SPELL_CURE_POISON, "Cure Poison")
AXED_SPELL(SPELL_DARKNESS, "Darkness")
AXED_SPELL(SPELL_OLD_DEFLECT_MISSILES, "Old Deflect Missiles")
AXED_SPELL(SPELL_DELAYED_FIREBALL, "Delayed Fireball")
AXED_SPELL(SPELL_DEMONIC_HORDE, "Demonic Horde")
AXED_SPELL(SPELL_DRACONIAN_BREATH, "Draconian Breath")
AXED_SPELL(SPELL_EPHEMERAL_INFUSION, "Ephemeral Infusion")
AXED_SPELL(SPELL_EVAPORATE, "Evaporate")
AXED_SPELL(SPELL_EXPLOSIVE_BOLT, "Explosive Bolt")
AXED_SPELL(SPELL_FAKE_RAKSHASA_SUMMON, "Rakshasa Summon")
AXED_SPELL(SPELL_FIRE_BRAND, "Fire Brand")
AXED_SPELL(SPELL_FLY, "Flight")
AXED_SPELL(SPELL_FORCEFUL_DISMISSAL, "Forceful Dismissal")
AXED_SPELL(SPELL_FREEZING_AURA, "Freezing Aura")
AXED_SPELL(SPELL_FRENZY, "Frenzy")
AXED_SPELL(SPELL_FULSOME_DISTILLATION, "Fulsome Distillation")
AXED_SPELL(SPELL_GRAND_AVATAR, "Grand Avatar")
AXED_SPELL(SPELL_HASTE_PLANTS, "Haste Plants")
AXED_SPELL(SPELL_HOLY_LIGHT, "Holy Light")
AXED_SPELL(SPELL_HUNTING_CRY, "Hunting Cry")
AXED_SPELL(SPELL_IGNITE_POISON_SINGLE, "Localized Ignite Poison")
AXED_SPELL(SPELL_INSULATION, "Insulation")
AXED_SPELL(SPELL_INFUSION, "Infusion")
AXED_SPELL(SPELL_IRON_ELEMENTALS, "Summon Iron Elementals")
AXED_SPELL(SPELL_LETHAL_INFUSION, "Lethal Infusion")
AXED_SPELL(SPELL_MELEE, "Melee")
AXED_SPELL(SPELL_MISLEAD, "Mislead")
AXED_SPELL(SPELL_PHASE_SHIFT, "Phase Shift")
AXED_SPELL(SPELL_POISON_WEAPON, "Poison Weapon")
AXED_SPELL(SPELL_RANDOM_BOLT, "Random Bolt")
AXED_SPELL(SPELL_REARRANGE_PIECES, "Rearrange the Pieces")
AXED_SPELL(SPELL_RECALL, "Recall")
AXED_SPELL(SPELL_REGENERATION, "Regeneration")
AXED_SPELL(SPELL_RING_OF_FLAMES, "Ring of Flames")
AXED_SPELL(SPELL_SEE_INVISIBLE, "See Invisible")
AXED_SPELL(SPELL_SHAFT_SELF, "Shaft Self")
AXED_SPELL(SPELL_SHROUD_OF_GOLUBRIA, "Shroud of Golubria")
AXED_SPELL(SPELL_SILVER_BLAST, "Silver Blast")
AXED_SPELL(SPELL_SINGULARITY, "Singularity")
AXED_SPELL(SPELL_SONG_OF_SHIELDING, "Song of Shielding")
AXED_SPELL(SPELL_SPECTRAL_WEAPON, "Spectral Weapon")
AXED_SPELL(SPELL_STONESKIN, "Stoneskin")
AXED_SPELL(SPELL_SUMMON_BUTTERFLIES, "Summon Butterflies")
AXED_SPELL(SPELL_SUMMON_ELEMENTAL, "Summon Elemental")
AXED_SPELL(SPELL_SUMMON_RAKSHASA, "Summon Rakshasa")
AXED_SPELL(SPELL_SUMMON_TWISTER, "Summon Twister")
AXED_SPELL(SPELL_SUNRAY, "Sunray")
AXED_SPELL(SPELL_SURE_BLADE, "Sure Blade")
AXED_SPELL(SPELL_THROW, "Throw")
AXED_SPELL(SPELL_VAMPIRE_SUMMON, "Vampire Summon")
AXED_SPELL(SPELL_WARP_BRAND, "Warp Weapon")
AXED_SPELL(SPELL_WEAVE_SHADOWS, "Weave Shadows")
AXED_SPELL(SPELL_STRIKING, "Striking")
AXED_SPELL(SPELL_RESURRECT, "Resurrect")
AXED_SPELL(SPELL_HOLY_WORD, "Holy word")
AXED_SPELL(SPELL_SACRIFICE, "Sacrifice")
AXED_SPELL(SPELL_MIASMA_CLOUD, "Miasma cloud")
AXED_SPELL(SPELL_POISON_CLOUD, "Poison cloud")
AXED_SPELL(SPELL_FIRE_CLOUD, "Fire cloud")
AXED_SPELL(SPELL_STEAM_CLOUD, "Steam cloud")
AXED_SPELL(SPELL_HOMUNCULUS, "Homunculus")
AXED_SPELL(SPELL_SERPENT_OF_HELL_BREATH_REMOVED, "Old serpent of hell breath")
AXED_SPELL(SPELL_SCATTERSHOT, "Scattershot")
AXED_SPELL(SPELL_SUMMON_SWARM, "Summon swarm")
AXED_SPELL(SPELL_CLOUD_CONE, "Cloud Cone")
AXED_SPELL(SPELL_RING_OF_THUNDER, "Ring of Thunder")
AXED_SPELL(SPELL_TWISTED_RESURRECTION, "Twisted Resurrection")
AXED_SPELL(SPELL_RANDOM_EFFECTS, "Random Effects")
AXED_SPELL(SPELL_HYDRA_FORM, "Hydra Form")
AXED_SPELL(SPELL_VORTEX, "Vortex")
AXED_SPELL(SPELL_GOAD_BEASTS, "Goad Beasts")
AXED_SPELL(SPELL_TELEPORT_SELF, "Teleport Self")
AXED_SPELL(SPELL_TOMB_OF_DOROKLOHE, "Tomb of Doroklohe")
AXED_SPELL(SPELL_EXCRUCIATING_WOUNDS, "Excruciating Wounds")
AXED_SPELL(SPELL_CONJURE_FLAME, "Conjure Flame")
AXED_SPELL(SPELL_CORPSE_ROT, "Corpse Rot")
AXED_SPELL(SPELL_FLAME_TONGUE, "Flame Tongue")
AXED_SPELL(SPELL_BEASTLY_APPENDAGE, "Beastly Appendage")
AXED_SPELL(SPELL_SPIDER_FORM, "Spider Form")
AXED_SPELL(SPELL_ICE_FORM, "Ice Form")
AXED_SPELL(SPELL_BLADE_HANDS, "Blade Hands")
AXED_SPELL(SPELL_STATUE_FORM, "Statue Form")
AXED_SPELL(SPELL_STORM_FORM, "Storm Form")
AXED_SPELL(SPELL_DRAGON_FORM, "Dragon Form")
AXED_SPELL(SPELL_NECROMUTATION, "Necromutation")
AXED_SPELL(SPELL_AWAKEN_EARTH, "Awaken Earth")
AXED_SPELL(SPELL_ANIMATE_SKELETON, "Animate Skeleton")
AXED_SPELL(SPELL_DRAIN_MAGIC, "Drain Magic")
#endif

};
