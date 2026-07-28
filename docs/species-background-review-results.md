# 玩家种族与背景全量校对结果

本文件是 Issue #26 的逐项审计记录。每一行是一张规范证据卡：身份、生命周期、
英文/中文显示形式、生产事实摘要和唯一终态结论均来自冻结 inventory。完整适性、
变异、技能、装备和法术原始字段保存在 inventory 的 `production_data` 中；下表
给出足以定位该记录的摘要，而不是另建一份会漂移的手工数据源。

## 冻结与集合证明

- 基线：`05c1f1ff519450a8d1b29ec1df74a476042f4a23`
- 修订前 inventory：
  `0ec14d56abeab2738a5ffdef86a6686ddd75f03ae636bc822dbfb60b80401302`
- 修订后 inventory：
  `47ef0d83b4278e2a432668d0d1f8a2e54bc176fd3d9b46c84c188693d9e9d399`
- 最终术语表 SHA-256：
  `4070a396e65a4bdf1fd2dfbc9e95bcc40053391e65441053f73c08146ed31d9e`
- `inventory identities = evidence-card identities = terminal-conclusion identities = 80`
- 分类：种族 47，背景 33；生命周期：现役可选 53，现役变体 8，兼容 19。
- 结构结果：重复、漏项、意外身份、名称/形式缺译、描述缺失、描述重复和陈旧键
  均为零。

结论“兼容身份”是终态保留结论，不是无期限暂缓：这些身份仅用于 TAG 34
迁移/读取，生产源没有现役选择界面描述时不补造描述；若其生命周期恢复为现役，
必须以新的生产数据和描述重新进入全量校对。

## 种族证据卡（47）

“适性 N 项”指 inventory 中逐字段核过的完整 YAML 适性映射；括号列出显式禁用
项。等级特性列为生产数据中变异/固有特性生效等级。

| 身份 | 生命周期 | 名称与形式 | 生产事实 | 终态结论 |
|---|---|---|---|---|
| `species:SP_ARMATAUR` | current_playable | Armataur → 甲马人；plain:甲马人 | abbr At；STR/INT/DEX 13/8/5；XP/HP/MP/WL -1/1/0/3；适性 33 项；体形 large；flags small_torso,barding；等级特性 1,7 | 修订：描述 |
| `species:SP_BARACHI` | current_playable | Barachi → 蛙人；plain:蛙人/adjective:蛙人/genus:蛙 | abbr Ba；STR/INT/DEX 9/8/7；XP/HP/MP/WL 0/0/0/3；适性 27 项；体形 medium；flags no_hair,no_ears；等级特性 1,13 | 修订：形容词、描述 |
| `species:SP_BASE_DRACONIAN` | current_playable | Draconian → 龙人；plain:龙人 | abbr Dr；STR/INT/DEX 10/8/6；XP/HP/MP/WL -1/1/0/3；适性 13 项（禁用 armour）；flags draconian,no_hair；等级特性 1 | 修订：描述 |
| `species:SP_BLACK_DRACONIAN` | current_variant | Black Draconian → 黑龙人；plain/adjective/genus:黑龙人/龙人/龙人 | abbr Dr；STR/INT/DEX 10/8/6；XP/HP/MP/WL -1/1/0/3；适性 15 项（禁用 armour）；等级特性 1,7,14 | 保留：现役龙人变体 |
| `species:SP_CENTAUR` | compatibility | Centaur → 半人马 | abbr Ce；STR/INT/DEX 10/7/4；XP/HP/MP/WL -1/1/0/3；适性 29 项；体形 large；等级特性 1 | 保留：兼容身份 |
| `species:SP_COGLIN` | current_playable | Coglin → 齿轮地精；genus:地精 | abbr Co；STR/INT/DEX 8/7/9；XP/HP/MP/WL 0/0/0/5；适性 29 项；等级特性 1 | 修订：描述 |
| `species:SP_DEEP_DWARF` | compatibility | Deep Dwarf → 深矮人；adjective/genus:矮人/矮人 | abbr DD；STR/INT/DEX 11/8/8；XP/HP/MP/WL -1/2/0/6；适性 29 项；等级特性 1,9,14 | 修订：形容词 |
| `species:SP_DEEP_ELF` | current_playable | Deep Elf → 精灵；adjective/genus:精灵/精灵 | abbr DE；STR/INT/DEX 5/12/10；XP/HP/MP/WL -1/-2/2/4；适性 30 项；等级特性 1 | 修订：形容词、描述 |
| `species:SP_DEMIGOD` | current_playable | Demigod → 半神；adjective:神圣 | abbr Dg；STR/INT/DEX 9/10/9；XP/HP/MP/WL -2/1/2/4；适性 32 项（禁用 invocations）；等级特性 1 | 修订：描述 |
| `species:SP_DEMONSPAWN` | current_playable | Demonspawn → 恶魔裔；adjective:恶魔 | abbr Ds；STR/INT/DEX 8/8/8；XP/HP/MP/WL -1/0/0/3；适性 26 项；随机恶魔变异由生产实现分配 | 修订：描述 |
| `species:SP_DJINNI` | current_playable | Djinni → 灯神 | abbr Dj；STR/INT/DEX 7/9/8；XP/HP/MP/WL 1/-1/0/4；适性 27 项；flags no_feet,no_blood；等级特性 1 | 修订：描述 |
| `species:SP_FELID` | current_playable | Felid → 猫；adjective/genus:猫科/猫 | abbr Fe；STR/INT/DEX 4/11/11；XP/HP/MP/WL -1/-3/1/6；适性 28 项（禁用十类装备技能）；体形 little；等级特性 1,6,12 | 修订：描述；复用 D-A-039 |
| `species:SP_FORMICID` | current_playable | Formicid → 蚁人；genus:蚁 | abbr Fo；STR/INT/DEX 12/7/9；XP/HP/MP/WL 1/0/0/4；适性 18 项；flags no_bones,no_ears；等级特性 1 | 修订：描述 |
| `species:SP_GARGOYLE` | current_playable | Gargoyle → 石像鬼 | abbr Gr；STR/INT/DEX 11/8/5；XP/HP/MP/WL 0/-2/0/3；适性 27 项；flags no_hair,no_blood；等级特性 1,14 | 修订：描述 |
| `species:SP_GHOUL` | compatibility | Ghoul → 食尸鬼；adjective:食尸鬼 | abbr Gh；STR/INT/DEX 11/7/4；XP/HP/MP/WL 0/1/0/3；适性 32 项（禁用 shapeshifting）；等级特性 1 | 修订：形容词 |
| `species:SP_GNOLL` | current_playable | Gnoll → 豺狼人 | abbr Gn；STR/INT/DEX 7/7/7；XP/HP/MP/WL 0/0/0/3；适性 33 项；等级特性 1 | 修订：描述 |
| `species:SP_GREEN_DRACONIAN` | current_variant | Green Draconian → 绿龙人；adjective/genus:龙人/龙人 | abbr Dr；STR/INT/DEX 10/8/6；XP/HP/MP/WL -1/1/0/3；适性 14 项（禁用 armour）；等级特性 1,7,14 | 保留：现役龙人变体 |
| `species:SP_GREY_DRACONIAN` | current_variant | Grey Draconian → 灰龙人；adjective/genus:龙人/龙人 | abbr Dr；STR/INT/DEX 10/8/6；XP/HP/MP/WL -1/1/0/3；适性 15 项（禁用 armour）；等级特性 1,14 | 保留：现役龙人变体 |
| `species:SP_HALFLING` | compatibility | Halfling → 半身人 | abbr Ha；STR/INT/DEX 9/6/9；XP/HP/MP/WL 1/-1/0/3；适性 22 项；体形 small；等级特性 1 | 保留：兼容身份 |
| `species:SP_HIGH_ELF` | compatibility | High Elf → 高等精灵；adjective/genus:精灵/精灵 | abbr HE；STR/INT/DEX 7/11/10；XP/HP/MP/WL -1/-1/1/4；适性 25 项 | 修订：形容词 |
| `species:SP_HILL_ORC` | compatibility | Hill Orc → 丘陵兽人 | abbr HO；STR/INT/DEX 10/8/6；XP/HP/MP/WL 0/1/0/3；适性 25 项 | 保留：兼容身份 |
| `species:SP_HUMAN` | current_playable | Human → 人类 | abbr Hu；STR/INT/DEX 8/8/8；XP/HP/MP/WL 0/0/0/3；适性 8 项；等级特性 1 | 修订：描述 |
| `species:SP_KOBOLD` | current_playable | Kobold → 狗头人 | abbr Ko；STR/INT/DEX 5/9/10；XP/HP/MP/WL 1/-2/0/3；适性 20 项；体形 small；等级特性 1 | 修订：描述 |
| `species:SP_LAVA_ORC` | compatibility | Lava Orc → 熔岩兽人 | abbr LO；STR/INT/DEX 10/8/6；XP/HP/MP/WL -1/1/0/3；适性 26 项 | 保留：兼容身份 |
| `species:SP_MAYFLYTAUR` | compatibility | Mayflytaur → 蜉蝣半人马 | abbr My；STR/INT/DEX 9/9/9；XP/HP/MP/WL 0/2/1/5；适性 31 项；等级特性 1,6,9,12,14 | 保留：兼容身份 |
| `species:SP_MERFOLK` | current_playable | Merfolk → 人鱼；adjective:人鱼 | abbr Mf；STR/INT/DEX 8/7/9；XP/HP/MP/WL 0/0/0/3；适性 27 项；等级特性 1 | 修订：形容词、描述 |
| `species:SP_METEORAN` | compatibility | Meteoran → 流星人；adjective:流星 | abbr Me；STR/INT/DEX 9/9/9；XP/HP/MP/WL 2/1/1/5；适性 32 项；等级特性 1,9 | 修订：形容词 |
| `species:SP_MINOTAUR` | current_playable | Minotaur → 牛头人 | abbr Mi；STR/INT/DEX 12/5/5；XP/HP/MP/WL -1/1/-1/3；适性 32 项；等级特性 1 | 修订：描述 |
| `species:SP_MOTTLED_DRACONIAN` | compatibility | Mottled Draconian → 斑驳龙人；adjective/genus:龙人/龙人 | abbr Dr；STR/INT/DEX 10/8/6；XP/HP/MP/WL -1/1/0/3；适性 13 项（禁用 armour）；等级特性 1 | 保留：兼容身份 |
| `species:SP_MOUNTAIN_DWARF` | current_playable | Mountain Dwarf → 山矮人；adjective/genus:矮人/矮人 | abbr MD；STR/INT/DEX 10/8/5；XP/HP/MP/WL -1/1/0/4；适性 31 项；等级特性 1 | 修订：形容词、描述 |
| `species:SP_MUMMY` | current_playable | Mummy → 木乃伊 | abbr Mu；STR/INT/DEX 11/7/7；XP/HP/MP/WL -1/0/0/5；适性 31 项（禁用 shapeshifting）；flags no_blood；等级特性 1,13 | 修订：描述 |
| `species:SP_NAGA` | current_playable | Naga → 纳迦 | abbr Na；STR/INT/DEX 10/8/6；XP/HP/MP/WL 0/2/0/5；适性 14 项；体形 large；flags small_torso,barding,no_feet；等级特性 1,13 | 修订：描述 |
| `species:SP_OCTOPODE` | current_playable | Octopode → 章鱼；adjective/genus:章鱼形/章鱼 | abbr Op；STR/INT/DEX 7/10/7；XP/HP/MP/WL 0/-1/0/3；适性 11 项（禁用 armour）；flags no_hair,no_bones,no_feet,no_ears；等级特性 1 | 修订：描述；复用 D-A-040 |
| `species:SP_ONI` | current_playable | Oni → 鬼；adjective:鬼 | abbr On；STR/INT/DEX 11/9/4；XP/HP/MP/WL 0/3/0/4；适性 28 项；体形 large；等级特性 1 | 修订：描述 |
| `species:SP_PALE_DRACONIAN` | current_variant | Pale Draconian → 苍白龙人；adjective/genus:龙人/龙人 | abbr Dr；STR/INT/DEX 10/8/6；XP/HP/MP/WL -1/1/0/3；适性 16 项（禁用 armour）；等级特性 1,7 | 保留：现役龙人变体 |
| `species:SP_POLTERGEIST` | current_playable | Poltergeist → 骚灵；adjective/genus:鬼魅/幽灵 | abbr Po；STR/INT/DEX 4/10/9；XP/HP/MP/WL 0/-1/0/4；适性 30 项（禁用 armour,shapeshifting）；flags no_blood,no_bones,no_feet,no_hair,no_ears；等级特性 1,13 | 修订：名称、描述；执行 D-A-033 |
| `species:SP_PURPLE_DRACONIAN` | current_variant | Purple Draconian → 紫龙人；adjective/genus:龙人/龙人 | abbr Dr；STR/INT/DEX 10/8/6；XP/HP/MP/WL -1/1/0/3；适性 14 项（禁用 armour）；等级特性 1,7,14 | 保留：现役龙人变体 |
| `species:SP_RED_DRACONIAN` | current_variant | Red Draconian → 红龙人；adjective/genus:龙人/龙人 | abbr Dr；STR/INT/DEX 10/8/6；XP/HP/MP/WL -1/1/0/3；适性 15 项（禁用 armour）；等级特性 1,7 | 保留：现役龙人变体 |
| `species:SP_REVENANT` | current_playable | Revenant → 归来者 | abbr Re；STR/INT/DEX 11/7/4；XP/HP/MP/WL -1/1/1/3；适性 32 项（禁用 shapeshifting）；等级特性 1,3 | 修订：描述 |
| `species:SP_SLUDGE_ELF` | compatibility | Sludge Elf → 污泥精灵；adjective/genus:精灵/精灵 | abbr SE；STR/INT/DEX 8/8/8；XP/HP/MP/WL 0/-1/1/3；适性 26 项 | 修订：形容词 |
| `species:SP_SPRIGGAN` | current_playable | Spriggan → 小精灵 | abbr Sp；STR/INT/DEX 4/9/10；XP/HP/MP/WL -1/-3/1/7；适性 30 项；体形 little；等级特性 1 | 修订：描述 |
| `species:SP_TENGU` | current_playable | Tengu → 天狗 | abbr Te；STR/INT/DEX 8/8/9；XP/HP/MP/WL 0/-2/1/3；适性 29 项；flags no_hair,no_ears；等级特性 1,7 | 修订：描述 |
| `species:SP_TROLL` | current_playable | Troll → 巨魔；adjective:巨魔 | abbr Tr；STR/INT/DEX 15/4/5；XP/HP/MP/WL -1/3/-1/3；适性 32 项；体形 large；等级特性 1 | 修订：形容词、描述 |
| `species:SP_VAMPIRE` | compatibility | Vampire → 吸血鬼；adjective:吸血 | abbr Vp；STR/INT/DEX 7/10/9；XP/HP/MP/WL -1/0/0/4；适性 27 项；等级特性 1 | 保留：兼容身份 |
| `species:SP_VINE_STALKER` | current_playable | Vine Stalker → 藤蔓行者 | abbr VS；STR/INT/DEX 10/8/9；XP/HP/MP/WL 0/-3/1/5；适性 19 项；flags no_ears；等级特性 1,8 | 修订：描述 |
| `species:SP_WHITE_DRACONIAN` | current_variant | White Draconian → 白龙人；adjective/genus:龙人/龙人 | abbr Dr；STR/INT/DEX 10/8/6；XP/HP/MP/WL -1/1/0/3；适性 15 项（禁用 armour）；等级特性 1,7 | 保留：现役龙人变体 |
| `species:SP_YELLOW_DRACONIAN` | current_variant | Yellow Draconian → 黄龙人；adjective/genus:龙人/龙人 | abbr Dr；STR/INT/DEX 10/8/6；XP/HP/MP/WL -1/1/0/3；适性 14 项（禁用 armour）；等级特性 1,7,14 | 保留：现役龙人变体 |

## 背景证据卡（33）

| 身份 | 生命周期 | 名称 | 生产事实 | 终态结论 |
|---|---|---|---|---|
| `background:JOB_ABYSSAL_KNIGHT` | compatibility | Abyssal Knight → 深渊骑士 | abbr AK；TAG 34 迁移身份；无现役起始配置或描述 | 保留：兼容身份 |
| `background:JOB_AIR_ELEMENTALIST` | current_playable | Air Elementalist → 气元素使 | 0/7/5；技能 Dodging2/Stealth2/Spellcasting2/Conjurations1/Air3；robe、magic；Shock/Discharge/Swiftness/Airstrike | 修订：名称、描述 |
| `background:JOB_ALCHEMIST` | current_playable | Alchemist → 炼金术士 | 0/7/5；Dodging2/Stealth2/Spellcasting2/Conjurations1/Alchemy3；robe、magic；Poisonous Vapours 等 5 法术 | 修订：描述 |
| `background:JOB_ARTIFICER` | current_playable | Artificer → 技师 | 4/3/5；Fighting1/Armour1/Dodging1/Stealth1/Evocations3；club、leather armour、三类魔杖 | 修订：名称、描述 |
| `background:JOB_BERSERKER` | current_playable | Berserker → 狂战士 | 9/-1/4；Fighting3/Dodging2/Weapon3；animal skin；Trog 起始信仰由实现核对 | 修订：描述 |
| `background:JOB_BRIGAND` | current_playable | Brigand → 强盗 | 3/3/6；Fighting2/Dodging1/Stealth4/Throwing2/Weapon2；+2 dagger、robe、cloak、poison×9、curare×3 | 修订：描述 |
| `background:JOB_CHAOS_KNIGHT` | current_playable | Chaos Knight → 混沌骑士 | 4/4/4；Fighting3/Dodging1/Armour1/Weapon3；+2 leather armour、butterflies；Xom 起始信仰由实现核对 | 修订：描述 |
| `background:JOB_CINDER_ACOLYTE` | current_playable | Cinder Acolyte → 灰烬侍僧 | 6/6/0；Fighting3/Weapon3/Spellcasting1/Fire3；robe；Scorch；Ignis 引用按 #25 术语权威为“曳焰” | 修订：描述 |
| `background:JOB_CONJURER` | current_playable | Conjurer → 咒法师 | -1/10/3；Dodging2/Spellcasting2/Conjurations4/Stealth2；robe、magic；Magic Dart 等 4 法术 | 修订：描述 |
| `background:JOB_DEATH_KNIGHT` | compatibility | Death Knight → 死亡骑士 | abbr DK；TAG 34 迁移身份；无现役起始配置或描述 | 保留：兼容身份 |
| `background:JOB_DELVER` | current_playable | Delver → 挖掘者 | 4/2/6；Fighting3/Dodging2/Stealth5/Weapon2；leather armour、fog/revelation/fear、haste、digging | 修订：描述 |
| `background:JOB_EARTH_ELEMENTALIST` | current_playable | Earth Elementalist → 土元素使 | 0/7/5；Dodging2/Stealth2/Spellcasting2/Conjurations1/Earth3；robe、magic；Sandblast 等 5 法术 | 修订：名称、描述 |
| `background:JOB_ENCHANTER` | current_playable | Enchanter → 惑控师 | 0/7/5；Dodging2/Spellcasting2/Hexes3/Stealth3/Weapon1；+1 dagger、robe、invisibility×2；4 法术 | 修订：描述 |
| `background:JOB_FIGHTER` | current_playable | Fighter → 战士 | 8/0/4；Fighting3/Armour3/Shields3/Weapon2；scale mail、buckler、might×2 | 修订：描述 |
| `background:JOB_FIRE_ELEMENTALIST` | current_playable | Fire Elementalist → 火元素使 | 0/7/5；Dodging2/Stealth2/Spellcasting2/Conjurations1/Fire3；robe、magic；Foxfire 等 5 法术 | 修订：名称、描述 |
| `background:JOB_FORGEWRIGHT` | current_playable | Forgewright → 锻造师 | 2/7/3；Dodging2/Stealth2/Spellcasting2/Forgecraft4；hammer、robe、magic；Kinetic Grapnel 等 5 法术 | 修订：描述、移除空分隔块 |
| `background:JOB_GLADIATOR` | current_playable | Gladiator → 角斗士 | 6/0/6；Fighting2/Throwing2/Dodging3/Weapon3；leather armour、helmet、net×3 | 修订：描述 |
| `background:JOB_HEALER` | compatibility | Healer → 治疗师 | abbr He；TAG 34 迁移身份；无现役起始配置或描述 | 保留：兼容身份 |
| `background:JOB_HEDGE_WIZARD` | current_playable | Hedge Wizard → 杂学巫师 | 2/6/4；Dodging2/Stealth2/Spellcasting3/Conjurations2/Translocations1/Summonings1/Necromancy1；五件起始配置、5 法术 | 修订：名称、描述 |
| `background:JOB_HEXSLINGER` | current_playable | Hexslinger → 诅咒射手 | 0/5/7；Fighting1/Dodging2/Spellcasting1/Hexes3/Fire1/Weapon2；robe、poison scroll、+1 sling；5 法术 | 修订：名称、描述 |
| `background:JOB_HUNTER` | current_playable | Hunter → 猎手 | 3/1/8；Fighting2/Dodging2/Stealth1/Weapon4；shortbow、leather armour、butterflies | 修订：名称、描述 |
| `background:JOB_ICE_ELEMENTALIST` | current_playable | Ice Elementalist → 冰元素使 | 0/7/5；Dodging2/Stealth2/Spellcasting2/Ice4；robe、magic；Freeze 等 4 法术 | 修订：名称、描述 |
| `background:JOB_JESTER` | compatibility | Jester → 小丑 | abbr Jr；TAG 34 迁移身份；无现役起始配置或描述 | 保留：兼容身份 |
| `background:JOB_MONK` | current_playable | Monk → 武僧 | 3/2/7；Fighting3/Dodging3/Weapon3；robe、ambrosia、light orb；首位神祇额外虔诚由实现核对 | 修订：描述 |
| `background:JOB_NECROMANCER` | current_playable | Necromancer → 死灵法师 | 0/7/5；Dodging2/Stealth2/Spellcasting2/Necromancy4；dagger、robe、magic；Soul Splinter 等 5 法术 | 修订：描述 |
| `background:JOB_PRIEST` | compatibility | Priest → 祭司 | abbr Pr；TAG 34 迁移身份；无现役起始配置或描述 | 保留：兼容身份 |
| `background:JOB_REAVER` | current_playable | Reaver → 掠夺者 | 4/5/3；Fighting2/Dodging2/Spellcasting2/Conjurations3/Weapon3；leather armour；Kiss of Death 等 4 法术 | 修订：描述 |
| `background:JOB_SHAPESHIFTER` | current_playable | Shapeshifter → 变形人 | 6/2/4；Fighting2/Unarmed3/Dodging2/Shapeshifting3；animal skin、flux×3、lignification、quill/protean talisman | 修订：名称、描述 |
| `background:JOB_SKALD` | compatibility | Skald → 吟游诗人 | abbr Sk；TAG 34 迁移身份；无现役起始配置或描述 | 保留：兼容身份 |
| `background:JOB_STALKER` | compatibility | Stalker → 潜行者 | abbr St；TAG 34 迁移身份；无现役起始配置或描述 | 保留：兼容身份 |
| `background:JOB_SUMMONER` | current_playable | Summoner → 召唤师 | 0/7/5；Dodging2/Stealth2/Spellcasting2/Summonings4；robe、magic；Summon Small Mammal 等 5 法术 | 修订：描述 |
| `background:JOB_WANDERER` | current_playable | Wanderer → 漫游者 | 0/0/0；起始技能与装备由 wanderer 公式随机生成 | 修订：名称、描述 |
| `background:JOB_WARPER` | current_playable | Warper → 折跃者 | 3/5/4；Fighting2/Throwing1/Armour1/Dodging2/Spellcasting2/Translocations3/Weapon2；leather armour、blinking、disjunction×4；5 法术 | 修订：名称、描述 |

## 变更摘要

- 统一 11 个现役背景名，并补齐 `Cinder Acolyte`、`Hexslinger`、
  `Ice Elementalist` 的术语权威。
- 补齐 7 个种族形容词 key，覆盖 10 个生产身份。
- 执行既有 D-A-033，将玩家种族 `Poltergeist` 从“吵闹鬼”修为“骚灵”。
- 全量重校 27 个现役种族描述和 26 个现役背景描述；修复名称漂移、法术/物品
  引用错误、数量错误、语义缺失与不自然表达。
- 删除中文种族描述中的 3 个生产清单外键：`Gale Centaur`、`Hill Orc`、
  `Vampire`；移除背景描述中 `Forgewright` 前的空 `%%%%` 块。
- 物品/ego/法术引用复用现行审计结果：例如强效药水、闪烁卷轴、神食药水、
  移位飞镖、震击、毒气、魔法飞弹、灵魂分裂和召唤小型哺乳动物。

<!-- BEGIN STRICT REVIEW EVIDENCE v1 -->
{"baseline":"05c1f1ff519450a8d1b29ec1df74a476042f4a23","glossary_sha256":"4070a396e65a4bdf1fd2dfbc9e95bcc40053391e65441053f73c08146ed31d9e","identity_count":80,"inventory_sha256":"47ef0d83b4278e2a432668d0d1f8a2e54bc176fd3d9b46c84c188693d9e9d399"}
```jsonl
{"fact_sha256":"4f27bfcd700d145a6067d361f0d8c68e8bfd5b173a44c221cf248324da0553e2","identity":"background:JOB_ABYSSAL_KNIGHT","terminal_conclusion":"keep"}
{"fact_sha256":"adf55dd008dc54933c291947d92cf829ae40f1b560e07d27852a7cb2d6cd8c77","identity":"background:JOB_AIR_ELEMENTALIST","terminal_conclusion":"adjust"}
{"fact_sha256":"8e8179ac6c9ad2e5d97812e5f40b2e1d21b01d9261976600bc567a322dc4a8e2","identity":"background:JOB_ALCHEMIST","terminal_conclusion":"adjust"}
{"fact_sha256":"ba4be129d3cf69a5043b51e4ce659d971ba8029f806f66da65f72a05f48d8fac","identity":"background:JOB_ARTIFICER","terminal_conclusion":"adjust"}
{"fact_sha256":"0fd1d526f9010017de1e3aa5f19ce7a43c1d55b28ff147b7195217517d4c8d0d","identity":"background:JOB_BERSERKER","terminal_conclusion":"adjust"}
{"fact_sha256":"ab33fa69b82e58364cd906613843d98a405303c54de050ac39940c24ea43f297","identity":"background:JOB_BRIGAND","terminal_conclusion":"adjust"}
{"fact_sha256":"99ee614cb20e6bb2001f75dcc05b6330b01dfdf654b9334551587e8abf9cfdf1","identity":"background:JOB_CHAOS_KNIGHT","terminal_conclusion":"adjust"}
{"fact_sha256":"fc5901d82116b6263b621971696fb2ffd2297f01c49246be6a40f2207879a9b9","identity":"background:JOB_CINDER_ACOLYTE","terminal_conclusion":"adjust"}
{"fact_sha256":"3f3df19116ec125c534e9ccc681a6699ea8e38723ea066c2ac46a3f9ee7ca5f9","identity":"background:JOB_CONJURER","terminal_conclusion":"adjust"}
{"fact_sha256":"3b4dcc461e1acfc3c8b458e0cc83f8b3f0a73cd1a1143ef4027f6d89b6bfac18","identity":"background:JOB_DEATH_KNIGHT","terminal_conclusion":"keep"}
{"fact_sha256":"bf267bb313daa23e4ba43e0e8742f1ba0158f23ca80c5049a7a088090f1baba3","identity":"background:JOB_DELVER","terminal_conclusion":"adjust"}
{"fact_sha256":"2b846c3a4445b73b41ad3e5cb52a94266ed884ebbf5e9321360b22fe1a182d55","identity":"background:JOB_EARTH_ELEMENTALIST","terminal_conclusion":"adjust"}
{"fact_sha256":"334357029f6c429fb16f10350563f549e74a081e0fe790361347084d0502b9f6","identity":"background:JOB_ENCHANTER","terminal_conclusion":"adjust"}
{"fact_sha256":"6c1e311f2f3ad3c5ddb5c8296f220a302fe6ad2032737593c21b8e8014419312","identity":"background:JOB_FIGHTER","terminal_conclusion":"adjust"}
{"fact_sha256":"6d0ee5b73e504a2c45a33a2f3bc0fa4521e8d1ff6fc570c470a4fea4e18b9981","identity":"background:JOB_FIRE_ELEMENTALIST","terminal_conclusion":"adjust"}
{"fact_sha256":"4ae9821255fd35a63a79c380b8d7d12ce019d6ebcb393d5faee96841197cf310","identity":"background:JOB_FORGEWRIGHT","terminal_conclusion":"adjust"}
{"fact_sha256":"53670c61eb798768b471a6974e2d3d7bb6bb4d6a098546e9db27393a9783a4b9","identity":"background:JOB_GLADIATOR","terminal_conclusion":"adjust"}
{"fact_sha256":"fb2999ec11ebc4597d476c54b86bfcc6452701478b95500c20aab8fe594bdc5c","identity":"background:JOB_HEALER","terminal_conclusion":"keep"}
{"fact_sha256":"8e3130f0c3dbe0097e9497fc882189e19851dfeea07c46d5847d478d44d16201","identity":"background:JOB_HEDGE_WIZARD","terminal_conclusion":"adjust"}
{"fact_sha256":"182e402cb19b730d51aaadf3a138a1a72aa29235dd9746e9afbaebe4b3dc3628","identity":"background:JOB_HEXSLINGER","terminal_conclusion":"adjust"}
{"fact_sha256":"db2531150e97a785c6baa5ea35fc43092dc195d62ea6f98479e0956fb86a424f","identity":"background:JOB_HUNTER","terminal_conclusion":"adjust"}
{"fact_sha256":"ce1e95b34b3d6152c79532cef8e1ed1cfe5f76a8c44bd5d504e950a536a60e72","identity":"background:JOB_ICE_ELEMENTALIST","terminal_conclusion":"adjust"}
{"fact_sha256":"199b0a3867674757f6d4eb28b9f7aaa031df47ec229a75475f5c2ec558734732","identity":"background:JOB_JESTER","terminal_conclusion":"keep"}
{"fact_sha256":"85d73966eb322f0f334449f4891ae4253385309b718fb36a895810eaf95c4ea8","identity":"background:JOB_MONK","terminal_conclusion":"adjust"}
{"fact_sha256":"20851761b604020bdf02bf5be837b5e4fdee6a62cd29c4126522ea05558cc00d","identity":"background:JOB_NECROMANCER","terminal_conclusion":"adjust"}
{"fact_sha256":"3dca983f2b834f65cf8354e64323531e1695cb0625a7a6656e3345b90deeee0a","identity":"background:JOB_PRIEST","terminal_conclusion":"keep"}
{"fact_sha256":"ac729bb740c8e645107db306a06a91e872d55e59adc0964905359fcacb82b2ef","identity":"background:JOB_REAVER","terminal_conclusion":"adjust"}
{"fact_sha256":"e47f58c08cc71c33b3c57d6e13bb90586530eac9294123f6608212107e837a79","identity":"background:JOB_SHAPESHIFTER","terminal_conclusion":"adjust"}
{"fact_sha256":"b4b03ed36ea799f3f31b3ff8f21c64def0751aafe885dbb5f76d1d3a0c145a78","identity":"background:JOB_SKALD","terminal_conclusion":"keep"}
{"fact_sha256":"37005524190ca32dea11956c07f3e2b7028bd1127f0d71f41c7669278db67e3f","identity":"background:JOB_STALKER","terminal_conclusion":"keep"}
{"fact_sha256":"55af25fc4ab1b362a6cf76b2195fcab4f926bb8c33a9c7111bc9c6f409761d3a","identity":"background:JOB_SUMMONER","terminal_conclusion":"adjust"}
{"fact_sha256":"3ac2393919a9931c399c75a558aaa1e98ca8983a411377d3159c02abb903954a","identity":"background:JOB_WANDERER","terminal_conclusion":"adjust"}
{"fact_sha256":"e0648a5cf15361cd2f0f0d26a98b041439f722a296ee9c86e509109f6a029876","identity":"background:JOB_WARPER","terminal_conclusion":"adjust"}
{"fact_sha256":"846a056e4e306b92594ec3fac62357e930515d93283ffe5bf4d661511c30ec8b","identity":"species:SP_ARMATAUR","terminal_conclusion":"adjust"}
{"fact_sha256":"b6c152d294ed3426858248a39baa8f5680f5755f565431bbc2e027383c08ecd9","identity":"species:SP_BARACHI","terminal_conclusion":"adjust"}
{"fact_sha256":"23b6ec95ee02d5b228772ad130e877951a1ac3a266b1d6c97af38bc8940124b2","identity":"species:SP_BASE_DRACONIAN","terminal_conclusion":"adjust"}
{"fact_sha256":"041077e8fe78fdc8b8746b279a0cd058a598b3e261ee88c0f8a744a90681e905","identity":"species:SP_BLACK_DRACONIAN","terminal_conclusion":"keep"}
{"fact_sha256":"4dd5494d1a0e320517ddbece19ac338ee1dd7c16fc01fd8bf0e2a76469383b13","identity":"species:SP_CENTAUR","terminal_conclusion":"keep"}
{"fact_sha256":"a5b63c47acec9196067175c6df3806a992c3e05052975ccbf413f75bb744dab3","identity":"species:SP_COGLIN","terminal_conclusion":"adjust"}
{"fact_sha256":"f293b4523dc78cfbe4afb28cef86cc7d649433aa075fb18d890ebec9639f94ba","identity":"species:SP_DEEP_DWARF","terminal_conclusion":"adjust"}
{"fact_sha256":"a1d1755a1e5cd1189122da1e39dd04fcd851659b0d35039a1d15e32fb9688e19","identity":"species:SP_DEEP_ELF","terminal_conclusion":"adjust"}
{"fact_sha256":"7f372bf3c909cb37b6e1f93c92f5349ade2fa704e7d56354283886dbdfc3f784","identity":"species:SP_DEMIGOD","terminal_conclusion":"adjust"}
{"fact_sha256":"e1a8dd5141f916c7bd3b3edb05e6df8eb66d21f8bc86035e1a497db2dce58197","identity":"species:SP_DEMONSPAWN","terminal_conclusion":"adjust"}
{"fact_sha256":"c72d774b5a915104e47706b54d8bae3443100186f570573ff61c0ead41d58614","identity":"species:SP_DJINNI","terminal_conclusion":"adjust"}
{"fact_sha256":"bb8ed0644e048bbb7eb717bf3b9c96d280da0ecd1ff1699a676de705ce0111f8","identity":"species:SP_FELID","terminal_conclusion":"adjust"}
{"fact_sha256":"e127583c6e6ee9b608468dab44990a8e02dc7c2cddcea6d3d57737dee88f63e2","identity":"species:SP_FORMICID","terminal_conclusion":"adjust"}
{"fact_sha256":"0c6d304a65aa8e9edd1df4f440e6b81a94fa4fb34b2da1baa7b885a9f1521366","identity":"species:SP_GARGOYLE","terminal_conclusion":"adjust"}
{"fact_sha256":"1b0803e80e76460c3c01265f4d228a71e1dfca32e0c678a4534e58fdab843db8","identity":"species:SP_GHOUL","terminal_conclusion":"adjust"}
{"fact_sha256":"3568e64952c572235a624c27c99d8534e59d61140aa77e5dcc4fcc13d333f79a","identity":"species:SP_GNOLL","terminal_conclusion":"adjust"}
{"fact_sha256":"3dc9ae98e81aaa30f27852e35ec280a3a669a6fa7294d223ded5ec98f01f1e57","identity":"species:SP_GREEN_DRACONIAN","terminal_conclusion":"keep"}
{"fact_sha256":"d17c2d2f3a45983bf9a56bad96891c39c5e792a45be4658b188f97f196382b58","identity":"species:SP_GREY_DRACONIAN","terminal_conclusion":"keep"}
{"fact_sha256":"a3a684fe6554af6292d7a7f43ba7af860f792da9a9d348f3004947510e80dbd3","identity":"species:SP_HALFLING","terminal_conclusion":"keep"}
{"fact_sha256":"c5f006a20c13ca3aaf8f53d34d88d6083f9004956c0994b966c3dc200a786baf","identity":"species:SP_HIGH_ELF","terminal_conclusion":"adjust"}
{"fact_sha256":"dda1909266f041f51e2d339c933452ec855e1b917780863b1f079e53f34db54b","identity":"species:SP_HILL_ORC","terminal_conclusion":"keep"}
{"fact_sha256":"95f975d00b8a07834d9c6231f5d5b7a22a760076584ae5ea1e3f12c80d958663","identity":"species:SP_HUMAN","terminal_conclusion":"adjust"}
{"fact_sha256":"7f1846812bfa9879646de2986b5e1133fbac6238c81b2d2c211bb9ddaaf5d07b","identity":"species:SP_KOBOLD","terminal_conclusion":"adjust"}
{"fact_sha256":"a3643670b9dd34e5a6653b21954b92004be49c4abddf5e116e98c56a7a417639","identity":"species:SP_LAVA_ORC","terminal_conclusion":"keep"}
{"fact_sha256":"93309072e5f5247e4a47e46af3a87b1000dd9be5b0de2af76d38652873ebdaf6","identity":"species:SP_MAYFLYTAUR","terminal_conclusion":"keep"}
{"fact_sha256":"a952caadbcb1007ffa42400e3d17d7f86952648e03f15583be20dd3888fea6f3","identity":"species:SP_MERFOLK","terminal_conclusion":"adjust"}
{"fact_sha256":"1674d3240ce8af2433c60fb2d173509b8bc5d7b94c22130e80558130eafcf2e7","identity":"species:SP_METEORAN","terminal_conclusion":"adjust"}
{"fact_sha256":"43467ba9a77b2e8b8fa14651f1afbd499a4812f32d582402195125bce3ad3929","identity":"species:SP_MINOTAUR","terminal_conclusion":"adjust"}
{"fact_sha256":"903a503c28835939aa0045578aa6d752344f0f8960d1150de4004ea641a16ca1","identity":"species:SP_MOTTLED_DRACONIAN","terminal_conclusion":"keep"}
{"fact_sha256":"e1ed9cc281c5b3f667bcd45297238803c1842ef8c3cb4170d5e13f4f4ebe113d","identity":"species:SP_MOUNTAIN_DWARF","terminal_conclusion":"adjust"}
{"fact_sha256":"a63114db6fa9ddf0bacdc1b2f0fe8bd5b9557d652a139e4647524ce355306b4f","identity":"species:SP_MUMMY","terminal_conclusion":"adjust"}
{"fact_sha256":"e894e543364dba539356b305c776fb70d037bdc5511730062a751e167c58f7e2","identity":"species:SP_NAGA","terminal_conclusion":"adjust"}
{"fact_sha256":"45e377ce417c33f6cf9079fe1e10d7f18b73bd89d40860a1d9e2a5a8039c9d2d","identity":"species:SP_OCTOPODE","terminal_conclusion":"adjust"}
{"fact_sha256":"bce9edfac66ba49fe0a0953fa7452e8c5fc40933578c24c43c1b23e80e2096a9","identity":"species:SP_ONI","terminal_conclusion":"adjust"}
{"fact_sha256":"86c7b25c31d461e2ab826c6bc11925c6e189ad695ae5350fb5eba975188ea540","identity":"species:SP_PALE_DRACONIAN","terminal_conclusion":"keep"}
{"fact_sha256":"417e54a74cffcc610841a48e6d36ccba819abbe6112a11fe79860842a81b8fbe","identity":"species:SP_POLTERGEIST","terminal_conclusion":"adjust"}
{"fact_sha256":"18b10eee06946be6b4214ddf068529dad3bee1f905f0e17d636a8d17fb2ebe15","identity":"species:SP_PURPLE_DRACONIAN","terminal_conclusion":"keep"}
{"fact_sha256":"1d4caf5802fc08f2245902604bae35be51e4acb794e4e18611dd5e58e732058b","identity":"species:SP_RED_DRACONIAN","terminal_conclusion":"keep"}
{"fact_sha256":"d3c6acd0ef51238a435deb0d3c22c90a6162f063b43b794f2d9448e042613ae0","identity":"species:SP_REVENANT","terminal_conclusion":"adjust"}
{"fact_sha256":"3457536192131faec69bf080563ce721a620a962c5c775df4c342587808adbe4","identity":"species:SP_SLUDGE_ELF","terminal_conclusion":"adjust"}
{"fact_sha256":"7d86053d051065902b281cd06f3df6c437df55bf12941d46ac143dc22835851d","identity":"species:SP_SPRIGGAN","terminal_conclusion":"adjust"}
{"fact_sha256":"d0017749f15aab9a4ca7538dbf00f1186e48712b17046fd0e5f6f93e71e3d0fb","identity":"species:SP_TENGU","terminal_conclusion":"adjust"}
{"fact_sha256":"ef6b03a54673f89a9b04a12c7785fa4fb9a7f5171541a9c907e2f3bef8f82adf","identity":"species:SP_TROLL","terminal_conclusion":"adjust"}
{"fact_sha256":"93fe79e5e3fa3e17253ed2795b9107f98a362c6f6d9d50ad91dd598b6e4f1283","identity":"species:SP_VAMPIRE","terminal_conclusion":"keep"}
{"fact_sha256":"3bff8606a7c0748dad89b82f0bd2e2a5a0dc5dc4ce7def5cfc51c98bf85e4d90","identity":"species:SP_VINE_STALKER","terminal_conclusion":"adjust"}
{"fact_sha256":"c32e8305d27295d046a7fb55e550f99e79b3a3ddc2680c8b327447ae9ba5937c","identity":"species:SP_WHITE_DRACONIAN","terminal_conclusion":"keep"}
{"fact_sha256":"9fccea234c595b76421b194e736964474ff4f0f55a03896d13be3fce11fae358","identity":"species:SP_YELLOW_DRACONIAN","terminal_conclusion":"keep"}
```
<!-- END STRICT REVIEW EVIDENCE v1 -->
