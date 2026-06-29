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
    // TODO: ARG-DIFF — structural sentence order: favour titles have completely different EN/ZH patterns with godname embedding
    const bool zh = Options.language == lang_t::ZH;

    if (player_under_penance())
    {
        const int penance = you.penance[which_god];
        if (zh)
        {
            return (penance >= 50) ? "神怒降临于你！" :
                   (penance >= 20) ? "你犯下了严重的罪过！忏悔吧！" :
                   (penance >=  5) ? "你正处于苦修中。"
                                   : "你应当更加自律。";
        }
        return (penance >= 50) ? "Godly wrath is upon you!" :
               (penance >= 20) ? "You've transgressed heavily! Be penitent!" :
               (penance >=  5) ? "You are under penance."
                               : "You should show more discipline.";
    }

    if (which_god == GOD_XOM)
        return uppercase_first(describe_xom_favour());

    const string godname = god_name(which_god);
    switch (god_favour_rank(which_god))
    {
        case 7:
            return zh ? (godname + "珍视的化身。")
                      : "A prized avatar of " + godname + ".";
        case 6:
            return zh ? (godname + "眷顾的仆人。")
                      : "A favoured servant of " + godname + ".";
        case 5:
            if (you_worship(GOD_DITHMENOS))
                return zh ? ("在" + godname + "眼中是辉煌的暗影。")
                          : "A glorious shadow in the eyes of " + godname + ".";
            else
                return zh ? ("在" + godname + "眼中是闪耀的明星。")
                          : "A shining star in the eyes of " + godname + ".";
        case 4:
            if (you_worship(GOD_DITHMENOS))
                return zh ? ("在" + godname + "眼中是初升的暗影。")
                          : "A rising shadow in the eyes of " + godname + ".";
            else
                return zh ? ("在" + godname + "眼中是冉冉升起的新星。")
                          : "A rising star in the eyes of " + godname + ".";
        case 3:
            return zh ? (uppercase_first(godname) + "对你感到满意。")
                      : uppercase_first(godname) + " is pleased with you.";
        case 2:
            return zh ? (uppercase_first(godname) + "察觉到了你的虔诚。")
                      : uppercase_first(godname) + " is aware of your devotion.";
        default:
            return zh ? (uppercase_first(godname) + "对你态度不明朗。")
                      : uppercase_first(godname) + " is noncommittal.";
    }
}

// The various titles granted by the god of your choice. Note that Xom
// doesn't use piety the same way as the other gods, so these are just
// placeholders.
static const char *divine_title[][8] =
{
    // No god.
    {"Buglet",             "Firebug",               "Bogeybug",                 "Bugger",
        "Bugbear",            "Bugged One",            "Giant Bug",                "Lord of the Bugs"},

    // Zin.
    {"Blasphemer",         "Anchorite",             "Apologist",                "Pious",
        "Devout",             "Orthodox",              "Immaculate",               "Bringer of Law"},

    // The Shining One.
    {"Honourless",         "Acolyte",               "Righteous",                "Unflinching",
        "Holy Warrior",       "Exorcist",              "Demon Slayer",             "Bringer of Light"},

    // Kikubaaqudgha -- death scholar theme.
    {"Tormented",          "Purveyor of Pain",       "Pupil of Sorrows",        "Merchant of Misery",
     "Scholar of Souls",   "Artisan of Death",       "Demagogue of Despair",    "Lord of Darkness"},

    // Yredelemnul -- fervent death knight theme.
    {"Traitor",            "Torchbearer",            "Despoiler",               "Black Crusader",
     "Fallen @Genus@",     "Harbinger of Doom",      "Inexorable Tide",         "Bringer of Blasphemy"},

    // Xom.
    {"Toy",                "Toy",                   "Toy",                      "Toy",
        "Toy",                "Toy",                   "Toy",                      "Toy"},

    // Vehumet -- battle mage theme.
    {"Meek",               "Sorcerer's Apprentice", "Scholar of Destruction",   "Caster of Ruination",
        "Traumaturge",        "Battlemage",            "Warlock",                  "Luminary of Lethal Lore"},

    // Okawaru -- battle theme.
    {"Coward",             "Struggler",             "Combatant",                "@Genus@-At-Arms",
        "Knight",             "Myrmidon",             "Warmonger",                "Victor of a Thousand Battles"},

    // Makhleb -- chaos theme.
    {"Orderly",            "Spawn of Chaos",        "Disciple of Destruction",  "Fanfare of Bloodshed",
        "Fiendish",           "Demolition @Genus@",    "Pandemonic",               "Champion of Chaos"},

    // Sif Muna -- generalist scholarly theme.
    {"Ignorant",           "Disciple",              "Student",                  "Adept",
        "Scribe",             "Scholar",               "Sage",                     "Genius of the Arcane"},

    // Trog -- anger theme.
    {"Puny",               "Troglodyte",            "Angry Troglodyte",         "Frenzied",
        "@Genus@ of Prey",    "Rampant",               "Wild @Genus@",             "Bane of Scribes"},

    // Nemelex Xobeh -- alluding to Tarot and cards.
    {"Unlucky @Genus@",    "Pannier",               "Jester",                   "Fortune-Teller",
        "Soothsayer",         "Magus",                 "Cardsharp",                "Hand of Fortune"},

    // Elyvilon.
    {"Sinner",                "Practitioner",       "Comforter",             "Caregiver",
        "Mender",           "Pacifist",                "Purifying @Genus@",        "Bringer of Life"},

    // Lugonu -- distortion theme.
    {"Pure",               "Abyss-Baptised",        "Unweaver",                 "Distorting @Genus@",
        "Agent of Entropy",   "Schismatic",            "Envoy of Void",            "Corrupter of Planes"},

    // Beogh -- messiah theme.
    {"Apostate",           "Convert",               "Proselytiser",             "Priest",
        "Missionary",         "Evangelist",            "Unifier",                  "Messiah"},

    // Jiyva -- slime and jelly theme.
    {"Scum",               "Squelcher",             "Ooze",                     "Jelly",
        "Slime Creature",     "Dissolving @Genus@",    "Blob",                     "Royal Jelly"},

    // Fedhas Madash -- nature theme.
    {"@Walking@ Fertiliser", "Fungal",              "Green @Genus@",            "Cultivator",
        "Fruitful",           "Photosynthesist",       "Green Death",              "Force of Nature"},

    // Cheibriados -- slow theme
    {"Hasty",              "Sluggish @Genus@",      "Deliberate",               "Unhurried",
     "Contemplative",         "Epochal",               "Timeless",                 "@Adj@ Aeon"},

    // Ashenzari -- divination theme
    {"Star-crossed",       "Cursed",                "Initiated",                "Seer",
        "Oracle",            "Illuminatus",            "Prince of Secrets",        "Omniscient"},

    // Dithmenos -- darkness theme
    {"Conspicuous",         "Nocturnal",            "Bump in the Night",        "Thespian",
        "Tenebrous",          "Puppetmaster",          "@Walking@ Midnight",       "Who Hides the Stars"},

    // Gozag -- entrepreneur theme
    {"Profligate",         "Pauper",                "Entrepreneur",             "Capitalist",
        "Rich",               "Opulent",               "Tycoon",                   "Plutocrat"},

    // Qazlal -- natural disaster theme
    {"Unspoiled",          "@Adj@ Mishap",          "Lightning Rod",            "@Adj@ Disaster",
        "Eye of the Storm",   "@Adj@ Catastrophe",     "@Adj@ Cataclysm",          "End of an Era"},

    // Ru -- enlightenment theme
    {"Sleeper",           "Questioner",             "Initiate",                 "Seeker of Truth",
        "@Walker@ of the Path","Lifter of the Veil",     "Transcendent",     "Drop of Water"},

#if TAG_MAJOR_VERSION == 34
    // Pakellas -- inventor theme
    {"Reactionary",       "Apprentice",             "Inquisitive",              "Experimenter",
        "Inventor",           "Pioneer",               "Brilliant",                "Grand Gadgeteer"},
#endif

    // Uskayaw -- reveler theme
    {"Prude",             "Wallflower",             "Party-goer",              "Dancer",
        "Impassioned",        "Rapturous",             "Ecstatic",                "Rhythm of Life and Death"},

    // Hepliaklqana -- memory/ancestry theme
    {"Damnatio Memoriae",       "Hazy",             "@Adj@ @Child@",              "Storyteller",
        "Brooding",           "Anamnesiscian",               "Grand Scion",                "Unforgettable"},

    // Wu Jian -- animal/chinese martial arts monk theme
    {"Wooden Rat",          "Young Dog",             "Young Crane",              "Young Tiger",
        "Young Dragon",     "Red Sash",               "Golden Sash",              "Sifu"},

    // Ignis -- fire/candles theme
    {"Extinguished",          "Last Ember",             "Glowing Coal",              "Thurifer",
        "Hearthfire",     "Furnace",               "Raging Flame",              "Inferno"},
};

// Chinese translations for divine titles
static const char *divine_title_zh[][8] =
{
    // 无神
    {"小虫",               "萤火虫",               "妖怪虫",                  "臭虫",
        "熊虫",               "被虫蛀者",             "巨虫",                    "虫之王"},

    // 辛
    {"亵渎者",             "隐修士",               "辩护者",                  "虔诚者",
        "虔信者",             "正统派",               "无垢者",                  "律法使者"},

    // 光辉者
    {"无耻之徒",           "侍僧",                 "正义者",                  "不屈者",
        "圣武士",             "驱魔师",               "恶魔杀手",                "光明使者"},

    // 奇库巴库德加 —— 死亡学者
    {"受折磨者",           "痛苦贩子",             "悲伤学徒",                "苦难商人",
        "灵魂学者",           "死亡工匠",             "绝望煽动者",              "黑暗之主"},

    // 伊雷德勒姆努 —— 狂热死亡骑士
    {"叛徒",               "火炬手",               "掠夺者",                  "黑色十字军",
        "堕落的@Genus@",     "末日先驱",             "不可阻挡之潮",            "亵渎使者"},

    // 佐姆
    {"玩具",               "玩具",                 "玩具",                    "玩具",
        "玩具",               "玩具",                 "玩具",                    "玩具"},

    // 维胡梅特 —— 战斗法师
    {"懦弱者",             "术士学徒",             "毁灭学者",                "毁灭施法者",
        "创伤师",             "战斗法师",             "术士",                    "致命学识之光"},

    // 奥卡瓦鲁 —— 战斗
    {"懦夫",               "挣扎者",               "战士",                    "武装@Genus@",
        "骑士",               "好战者",               "战争贩子",                "千战胜利者"},

    // 马克勒布 —— 混沌
    {"守序者",             "混沌之卵",             "毁灭信徒",                "杀戮赞歌",
        "恶魔般的",           "破坏@Genus@",          "万魔殿的",                "混沌斗士"},

    // 西芙穆娜 —— 博学学者
    {"无知者",             "门徒",                 "学生",                    "熟手",
        "抄写员",             "学者",                 "圣贤",                    "奥术天才"},

    // 特罗格 —— 愤怒
    {"弱小者",             "穴居者",               "愤怒的穴居者",            "狂暴者",
        "掠食@Genus@",       "暴怒者",               "狂野的@Genus@",           "文士之灾"},

    // 涅梅莱克斯·索贝 —— 塔罗牌
    {"不幸的@Genus@",      "牌筐",                 "小丑",                    "算命师",
        "预言师",             "魔术师",               "牌技高手",                "命运之手"},

    // 埃利维隆
    {"罪人",               "修行者",               "安慰者",                  "看护者",
        "修补者",             "和平主义者",           "净化@Genus@",             "生命使者"},

    // 卢戈努 —— 扭曲
    {"纯净者",             "深渊洗礼者",           "解织者",                  "扭曲@Genus@",
        "熵之使者",           "分裂者",               "虚空特使",                "位面腐化者"},

    // 比奥格 —— 弥赛亚
    {"背教者",             "皈依者",               "传教者",                  "牧师",
        "传教士",             "福音使者",             "统一者",                  "弥赛亚"},

    // 吉瓦 —— 史莱姆
    {"浮渣",               "踩踏者",               "软泥",                    "果冻",
        "史莱姆生物",         "溶解的@Genus@",        "凝胶团",                  "皇家果冻"},

    // 菲达斯·马达什 —— 自然
    {"@Walking@肥料",      "真菌",                 "绿色@Genus@",             "栽培者",
        "肥沃的",             "光合作用者",           "绿色死神",                "自然之力"},

    // 切布里亚多斯 —— 缓慢
    {"急躁者",             "迟缓的@Genus@",        "从容者",                  "不急者",
        "沉思者",             "划时代的",             "永恒者",                  "@Adj@ 永世者"},

    // 阿申扎里 —— 占卜
    {"厄运缠身者",         "受诅咒者",             "入门者",                  "预言者",
        "神谕者",             "启示者",               "奥秘王子",                "全知者"},

    // 迪斯米诺斯 —— 黑暗
    {"显眼者",             "夜行者",               "夜中怪声",                "演员",
        "晦暗者",             "傀儡师",               "@Walking@午夜",           "隐匿星辰者"},

    // 戈扎格 —— 企业家
    {"挥霍者",             "穷光蛋",               "企业家",                  "资本家",
        "富人",               "富豪",                 "大亨",                    "财阀"},

    // 卡兹拉尔 —— 自然灾害
    {"未损者",             "@Adj@小灾",            "避雷针",                  "@Adj@灾难",
        "风暴眼",             "@Adj@大灾",           "@Adj@巨灾",              "时代终结者"},

    // 鲁 —— 悟道
    {"沉睡者",             "提问者",               "入门者",                  "求真者",
        "行路@Walker@",      "揭纱者",               "超越者",                  "一滴水"},

#if TAG_MAJOR_VERSION == 34
    // 帕克拉斯 —— 发明家 (已移除)
    {"守旧者",             "学徒",                 "好奇者",                  "实验者",
        "发明家",             "先驱",                 "才华横溢者",              "伟大发明家"},
#endif

    // 乌斯卡亚 —— 狂欢
    {"假正经",             "壁花",                 "派对客",                  "舞者",
        "激情者",             "狂喜者",               "入迷者",                  "生死之韵律"},

    // 赫普利亚克娜 —— 记忆/先祖
    {"记忆抹除者",         "朦胧者",               "@Adj@@Child@",            "讲故事者",
        "沉思者",             "记忆学家",             "伟大后裔",                "不可忘怀者"},

    // 吴建 —— 中国武术
    {"木鼠",               "幼犬",                 "幼鹤",                    "幼虎",
        "幼龙",               "红带",                 "金带",                    "师父"},

    // 伊格尼斯 —— 火/蜡烛
    {"已熄灭者",           "最后余烬",             "发光煤块",                "持香者",
        "炉火",               "熔炉",                 "烈焰",                    "地狱之火"},
};
COMPILE_CHECK(ARRAYSZ(divine_title) == NUM_GODS);
COMPILE_CHECK(ARRAYSZ(divine_title_zh) == NUM_GODS);

string god_title(god_type which_god, species_type which_species, int piety)
{
    const bool zh = Options.language == lang_t::ZH;
    string title;
    if (player_under_penance(which_god))
        title = zh ? divine_title_zh[which_god][0] : divine_title[which_god][0];
    else if (which_god == GOD_USKAYAW)
        title = zh ? divine_title_zh[which_god][_invocations_level()]
                   : divine_title[which_god][_invocations_level()];
    else if (which_god == GOD_GOZAG)
        title = zh ? divine_title_zh[which_god][_gold_level()]
                   : divine_title[which_god][_gold_level()];
    else
        title = zh ? divine_title_zh[which_god][_piety_level(piety)]
                   : divine_title[which_god][_piety_level(piety)];

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

/// Translate ancestor upgrade name to Chinese.
static const char* _zh_ancestor_upgrade(const char* en)
{
    if (Options.language != lang_t::ZH || !en || !en[0])
        return en;
    static const map<string, string> zh_map = {
        {"Flail", "链枷"},
        {"Shield", "盾牌"},
        {"Chain mail (+AC)", "链甲（+AC）"},
        {"Broad axe (flame)", "阔斧（火焰）"},
        {"Binding melee attacks", "束缚近战攻击"},
        {"Tower shield (reflect)", "塔盾（反射）"},
        {"Bolster", "强化"},
        {"Broad axe (speed)", "阔斧（速度）"},
        {"Increased hit points", "提升生命值"},
        {"Staff", "法杖"},
        {"Shock", "震击"},
        {"Stone Arrow", "石箭术"},
        {"Deflect Missiles", "偏转飞弹"},
        {"Iceblast", "冰爆术"},
        {"Bolt of Magma", "岩浆箭"},
        {"Lee's Rapid Deconstruction", "李的快速分解"},
        {"Increased spell damage", "提升法术伤害"},
        {"Plasma Beam", "等离子束"},
        {"Permafrost Eruption", "永冻爆发"},
        {"Dagger (drain)", "匕首（吸取）"},
        {"Slow", "减速"},
        {"Confuse", "混乱"},
        {"Paralyse", "麻痹"},
        {"Mass Confusion", "群体混乱"},
        {"Haste", "加速"},
        {"Quick blade (antimagic)", "迅捷之刃（反魔）"},
    };
    auto it = zh_map.find(en);
    return it != zh_map.end() ? it->second.c_str() : en;
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

    const bool zh = Options.language == lang_t::ZH;
    if (upgrades)
    {
        desc = T_("Ancestor Upgrades:\n\n<white>XL              Upgrade\n</white>");
        for (auto &entry : *upgrades)
        {
            const char* name = zh ? _zh_ancestor_upgrade(entry.second.c_str())
                                  : entry.second.c_str();
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
        width = max(width, strlen(branches[br].shortname));

    for (branch_type br : targets)
    {
        string line = " ";
        line += branches[br].shortname;
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

    // TODO: ARG-DIFF — structural sentence order: god_name + comma_separated_fn multi-line sentences at different EN/ZH positions
    const bool zh = Options.language == lang_t::ZH;

    switch (which_god)
    {
        case GOD_SHINING_ONE:
        case GOD_ELYVILON:
            if (zh)
                return god_name(which_god) +
                       "原谅追随者的弃离；但那些后来信仰邪恶之神的人将受到惩罚。（" +
                       comma_separated_fn(begin(evil_gods), end(evil_gods),
                                          bind(god_name, placeholders::_1, false),
                                          "和", "、") +
                       "是邪恶之神。）";
            return uppercase_first(god_name(which_god)) +
                   " forgives followers for abandonment; however, those who"
                   " later take up the worship of an evil god will be"
                   " punished. (" +
                   comma_separated_fn(begin(evil_gods), end(evil_gods),
                                      bind(god_name, placeholders::_1, false)) +
                   " are evil gods.)";

        case GOD_ZIN:
            if (zh)
                return god_name(which_god) +
                       "原谅追随者的弃离；但那些后来信仰邪恶或混乱之神的人将被鞭笞。（" +
                       comma_separated_fn(begin(evil_gods), end(evil_gods),
                                          bind(god_name, placeholders::_1, false),
                                          "和", "、") +
                       "是邪恶的，" +
                       comma_separated_fn(begin(chaotic_gods), end(chaotic_gods),
                                          bind(god_name, placeholders::_1, false),
                                          "和", "、") +
                       "是混乱的。）";
            return uppercase_first(god_name(which_god)) +
                   " forgives followers for abandonment; however, those who"
                   " later take up the worship of an evil or chaotic god will"
                   " be scourged. (" +
                   comma_separated_fn(begin(evil_gods), end(evil_gods),
                                      bind(god_name, placeholders::_1, false)) +
                   " are evil, and " +
                   comma_separated_fn(begin(chaotic_gods), end(chaotic_gods),
                                      bind(god_name, placeholders::_1, false)) +
                   " are chaotic.)";
        default:
            if (zh)
                return god_name(which_god) +
                       "不欣赏弃离行为，并将对不忠的追随者降下可怕的惩罚！";
            return uppercase_first(god_name(which_god)) +
                   " does not appreciate abandonment, and will call down"
                   " fearful punishments on disloyal followers!";
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
        if (Options.language == lang_t::ZH)
        {
            _add_par(desc, god_name(which_god)
                          + "的愤怒持续时间相对较"
                          + (long_wrath ? "长" : "短") + "。");
        }
        else
        {
            _add_par(desc, apostrophise(uppercase_first(god_name(which_god)))
                                  + " wrath lasts for a relatively " +
                                  (long_wrath ? T_("long") : T_("short"))
                                  + " duration.");
        }
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

    // Category A fix: T_() format string with %s for god_name and skill_name
    const bool zh = Options.language == lang_t::ZH;

    switch (skill)
    {
        case SK_INVOCATIONS:
            break;
        case SK_NONE:
            info += make_stringf(T_("%s powers are not affected by the %s skill."),
                         zh ? god_name(which_god).c_str()
                            : uppercase_first(apostrophise(god_name(which_god))).c_str(),
                         skill_name(SK_INVOCATIONS));
            break;
        default:
            info += make_stringf(T_("%s powers are based on %s instead of %s skill."),
                         zh ? god_name(which_god).c_str()
                            : uppercase_first(apostrophise(god_name(which_god))).c_str(),
                         skill_name(skill),
                         skill_name(SK_INVOCATIONS));
            break;
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

        desc.cprintf("%s%s守护你的生命。\n",
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
            desc.cprintf("兽人经常认出你是贝奥格的选民。\n");
        else
            desc.cprintf("兽人有时认出你是他们的一员。\n");
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

        desc.cprintf("%s%s保护你免受混沌伤害。\n",
                uppercase_first(god_name(which_god)).c_str(), how);

        how =
            (piety >= piety_breakpoint(5)) ? T_("often") :
            (piety >= piety_breakpoint(3)) ? T_("sometimes") :
            (piety >= piety_breakpoint(1)) ? T_("occasionally") :
                                             T_("rarely");
        desc.cprintf("%s%s保护你免受地狱伤害。\n",
                uppercase_first(god_name(which_god)).c_str(), how);
        break;
    }

    case GOD_SHINING_ONE:
    {
        have_any = true;
        // TSO section: all format strings have different ARG positions between EN/ZH
        desc.cprintf("%s阻止你偷袭毫无防备的敌人。\n",
                uppercase_first(god_name(which_god)).c_str());

        const int halo_size = you_worship(which_god) ? you.halo_radius() : -1;
        if (halo_size < 0)
            desc.textcolour(DARKGREY);
        else
            desc.textcolour(god_colour(which_god));
        // Category D fix: T_() for embedded adjectives (large/small)
        if (Options.language == lang_t::ZH)
            desc.cprintf("你散发出%s正义光环，其中的敌人"
                    "更容易被击中。\n",
                    halo_size > 5 ? "强大的" :
                    halo_size > 3 ? "" :
                                    "微弱的");
        else
            desc.cprintf("You radiate a%s aura of righteousness, "
                    "making those within it easier to hit.\n",
                    halo_size > 5 ? T_(" large") :
                    halo_size > 3 ? "" :
                                    T_(" small"));

        if (piety >= piety_breakpoint(1))
            desc.textcolour(god_colour(which_god));
        else
            desc.textcolour(DARKGREY);
        // Category B fix: T_() adverb fragments
        const char *how =
            (piety >= piety_breakpoint(5)) ? T_("completely") :
            (piety >= piety_breakpoint(3)) ? T_("mostly") :
                                             T_("partially");
        desc.cprintf("%s%s保护你免受负能量伤害。\n",
                uppercase_first(god_name(which_god)).c_str(), how);
        break;
    }

    case GOD_JIYVA:
        have_any = true;
        desc.cprintf("果冻是和平的，会吃掉地上的物品。\n");
        desc.cprintf("吉瓦阻止你伤害果冻。\n");

        if (have_passive(passive_t::jelly_regen))
            desc.textcolour(god_colour(which_god));
        else
            desc.textcolour(DARKGREY);
        desc.cprintf("你的生命和魔力恢复速度%s加快。\n",
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
        desc.cprintf("%s%s减缓移动。\n",
                uppercase_first(god_name(which_god)).c_str(),
                piety >= piety_breakpoint(5)
                    ? (T_("greatly "))
                    : piety >= piety_breakpoint(2)
                    ? ""
                    : (T_("slightly ")));
        desc.cprintf("%s提升你的属性。(+%d)\n",
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
            desc.cprintf("你可以记忆%s。\n", offer);
        }
        else if (!you.has_mutation(MUT_INNATE_CASTER))
        {
            desc.textcolour(DARKGREY);
            desc.cprintf("你可以记忆一些维胡梅特的法术。\n");
        }
        break;

    case GOD_YREDELEMNUL:
        // TODO: Vary the text depending on the size of the umbra.
        desc.cprintf("你被本影环绕。\n"
                     "在你的本影中死去的敌人可能会被复活为亡灵仆从。\n");
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
        desc.cprintf("你的生命精华减少了。(-10%% 生命值)\n");
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
                desc.cprintf("你的毁灭被火焚地狱之力增强。\n");
            else if (you.has_mutation(MUT_MAKHLEB_DESTRUCTION_COC))
                desc.cprintf("你的毁灭被冰狱之力增强。\n");
            else if (you.has_mutation(MUT_MAKHLEB_DESTRUCTION_TAR))
                desc.cprintf("你的毁灭被悲叹地狱之力增强。\n");
            else if (you.has_mutation(MUT_MAKHLEB_DESTRUCTION_DIS))
                desc.cprintf("你的毁灭被铁城之力增强。\n");
            else
            {
                desc.textcolour(DARKGREY);
                desc.cprintf("你的毁灭将被四大地狱之一增强。\n");
            }

            continue;
        }

        if (power.abil == ABIL_MAKHLEB_BRAND_SELF_1
            && !makhleb_mark_name().empty())
        {
                desc.textcolour(god_colour(which_god));
                desc.cprintf("你被烙印了%s。\n", makhleb_mark_name().c_str());
                continue;
        }

        string buf = power.general;

        // TODO: ARG-DIFF — helper function pattern: zh_god_power translates god power descriptions; not simple T_() conversion
        if (Options.language == lang_t::ZH)
        {
            const char* zh = zh_god_power(buf.c_str());
            if (zh && zh[0])
                buf = zh;
        }

        // Skip listing powers with no description (they are intended to be hidden)
        if (buf.length() == 0)
        {
            have_any = false;
            continue;
        }

        // Only wrap with "You can" for English; Chinese translations are full sentences.
        if (Options.language != lang_t::ZH && !isupper(buf[0]))
            buf = "You can " + buf + ".";
        const int desc_len = strwidth(buf);

        string abil_cost = "(" + make_cost_description(power.abil) + ")";
        if (abil_cost == "(None)" || abil_cost == "（无）")
            abil_cost = "";

        desc.cprintf("%s%*s%s\n", buf.c_str(), 80 - desc_len - (int)strwidth(abil_cost),
                "", abil_cost.c_str());
    }

    if (!have_any)
        desc.cprintf("无。\n");

    // Show Jiyva's opening of the Slime Pits at the bottom of the list
    // We want this to stay green permanently once the player hits 6*
    if (which_god == GOD_JIYVA)
    {
        if (you.one_time_ability_used[which_god])
            desc.textcolour(god_colour(which_god));
        else
            desc.textcolour(DARKGREY);
        desc.cprintf("吉瓦将解锁软泥坑宝库。\n");
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
            // TODO: ARG-DIFF — structural sentence order: random_choose + format specifiers differ between EN and ZH
            return Options.language == lang_t::ZH
                ? string("（现在行动即可免费）")
                : string(" (no fee if you ")
                  + random_choose("act now", "join today") + ")";
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
        if (text.width() + service_fee.length() + 9 <= MIN_COLS)
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
        string prompt = abandon_prompt + (yesno_only ? " 请输入 [Y]是 或 [n]否。" : "");
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
