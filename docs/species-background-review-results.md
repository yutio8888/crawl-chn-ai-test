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
  `07eaf4d7f33cb4b982d54ebce05efbc4c28d8edb61b1b35db441605cd5d8efb9`
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
