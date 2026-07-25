# 法术名称全量复审修改说明

本文汇总“法术名称逐项复审”实际落地到游戏文本的修改。比较范围为复审计划
冻结基线 `5cb9aa27a224a81da780757f8445cfc07de09dfd` 到已提交候选
`8a5cb19202e1a2eb21bd32578b92e0aed97b86af`。

## 汇总

- 全量审阅 511/511 项：409 项现行法术、98 项已移除兼容记录、
  2 项描述专用 dummy、2 项内部 placeholder。
- 53 个法术标题发生修改，其中 50 个为现行法术，3 个为
  `TAG_MAJOR_VERSION == 34` 已移除兼容记录。
- 201 个 `crawl-ref/source/dat/descript/zh/spells.txt` 中文法术描述条目发生修改。
- 其中 22 个法术同时修改了标题和描述；另有 31 个只改标题、179 个只改描述。
- `crawl-ref/source/dat/i18n/zh/source.txt` 另有 19 个关联状态、提示语或通用词形
  修改；它们不计入 53 个法术标题。
- `Dispersal` 的标题“击退术”在冻结基线中已经存在，本轮没有再次改名；
  本轮修正的是其描述，使“远距传送、抵抗后仍短距闪送、独立意志检定导致混乱”
  三层效果表述清楚。

统计采用 TextDB 的 `%%%%` 条目作为单位。描述条目只要正文发生任何实际变化
就计入，因此既包括机制错误修正和完整重译，也包括术语统一、语序和语言润色。

## 法术名称修改

### 现行法术（50 项）

| 英文名 | 原译名 | 新译名 | 修改重点 |
|---|---|---|---|
| `Corona` | 怪异发光球 | 光晕 | 对应环绕、勾勒目标轮廓的效果，删除并不存在的“球” |
| `Freezing Gust` | 冰冻狂风 | 冰冻阵风 | `gust` 是阵风，避免夸大为持续狂风 |
| `Slug Dart` | 弹丸飞镖 | 蛞蝓飞镖 | `slug` 在此指施术生物/蛞蝓，不是泛指弹丸 |
| `Vhi's Electric Charge` | 维之电荷 | 维之电击冲锋 | 明确这是冲向敌人并近战攻击的位移法术 |
| `Vhi's Electrolunge` | 维之电冲 | 维之电击突进 | 保留电击与突进两层核心语义 |
| `Bolt of Draining` | 吸取箭 | 衰竭箭 | 效果是负能量伤害并施加衰竭，不是为施法者吸血 |
| `Borgnjor's Revivification` | 博格尼尔之复活 | 博格尼尔之复苏 | 法术治疗仍活着的施法者，并非死后复活 |
| `Summon Greater Demon` | 召唤高级恶魔 | 召唤高等恶魔 | 与恶魔等级术语统一 |
| `Metabolic Englaciation` | 深度冻结 | 代谢冻结 | 补回 `metabolic`，体现从代谢层面冻结生物 |
| `Woodweal` | 木质愈合 | 林木疗愈 | 表达借助林木恢复，而非“木质材料”本身愈合 |
| `Hurl Damnation` | 投掷诅咒 | 投掷天谴 | `Damnation` 统一为“天谴”伤害术语 |
| `Summon Ufetubus` | 召唤乌菲图布斯 | 召唤乌菲特布斯 | 统一怪物专名 |
| `Summon Sin Beast` | 召唤罪兽 | 召唤罪孽兽 | 统一 `Sin Beast` 实体名 |
| `Spit Poison` | 喷毒 | 喷吐毒液 | 与同名能力及吐息/喷吐动作术语统一 |
| `Blink Other` | 闪烁他人 | 使他人闪烁 | 修正中文论元关系：施法者使目标闪烁 |
| `Blink Other Close` | 闪烁他人接近 | 使他人闪烁靠近 | 修正中文论元关系并保留“靠近”结果 |
| `Cold Breath` | 寒冷吐息 | 寒霜吐息 | 改为自然的元素攻击名称 |
| `Primal Wave` | 原始波浪 | 原初浪潮 | `primal` 译为“原初”，并强化召出激流的法术感 |
| `Orb of Destruction` | 毁灭之球 | 毁灭法球 | `Orb` 法术实体统一为“法球” |
| `Druid's Call` | 德鲁伊召唤 | 德鲁伊呼唤 | `Call` 是呼唤盟友到场，不等同于凭空召唤 |
| `Summon Holies` | 召唤圣灵 | 召唤神圣生物 | 实际召来的是一类神圣战士，不是“圣灵” |
| `Drain Life` | 吸取生命 | 汲取生命 | 与 `Drain Magic → 汲取魔力` 系列统一 |
| `Mesmerise` | 催眠 | 迷魂 | 效果是限制目标远离施术者，并非睡眠状态 |
| `Iskenderun's Battlesphere` | 伊斯肯德伦之战斗球 | 伊斯肯德伦之战斗法球 | 明确其为跟随施法、协同攻击的魔法法球 |
| `Beckoning Gale` | 召唤强风 | 招引之风 | 核心是用风把目标拉近，不是召唤一阵普通强风 |
| `Injury Bond` | 伤害链接 | 伤害联结 | 改用更符合魔法关系的书面表达 |
| `Blink Allies Encircling` | 闪烁盟友包围 | 使盟友闪烁合围 | 修正施受关系，并说明盟友闪烁后的阵形 |
| `Invisibility Other` | 隐身他人 | 使他人隐形 | 修正中文论元关系，统一 `Invisibility → 隐形` |
| `Major Destruction` | 大型毁灭 | 强力毁灭 | `major` 表示强度而非物理尺寸 |
| `Blink Allies Away` | 闪烁盟友远离 | 使盟友闪烁远离 | 修正施受关系，保留远离结果 |
| `Rebounding Chill` | 弹跳寒冷 | 弹跳寒流 | `chill` 在此是会弹跳的寒冷攻击，不是抽象“寒冷” |
| `Glaciate` | 冰川 | 冰封 | 原译是名词“冰川”，新译表达锥形冰冻攻击 |
| `Summon Mana Viper` | 召唤魔力蝰蛇 | 召唤魔力毒蛇 | 与现行怪物实体名统一 |
| `gehenna serpent of hell breath` | 火焚地狱蛇之吐息 | 欣嫩谷地狱巨蛇吐息 | 统一地狱分支名和 `Serpent of Hell` 实体名 |
| `cocytus serpent of hell breath` | 冰狱蛇之吐息 | 悲叹河地狱巨蛇吐息 | 统一地狱分支名和 `Serpent of Hell` 实体名 |
| `dis serpent of hell breath` | 铁城蛇之吐息 | 铁城地狱巨蛇吐息 | 补全 `Serpent of Hell` 实体名 |
| `tartarus serpent of hell breath` | 悲叹地狱蛇之吐息 | 塔尔塔罗斯地狱巨蛇吐息 | 统一地狱分支名和 `Serpent of Hell` 实体名 |
| `Summon Emperor Scorpions` | 召唤帝蝎 | 召唤帝王蝎 | 与怪物实体名统一 |
| `Draining Gaze` | 吸取凝视 | 衰竭凝视 | 实际效果是按最大生命值比例施加衰竭，不是吸血 |
| `Mourning Wail` | 哀悼嚎哭 | 哀恸之嚎 | 改为自然、凝练的法术名 |
| `Summon Executioners` | 召唤行刑者 | 召唤处刑人 | 与恶魔实体名统一 |
| `Bind Souls` | 绑定灵魂 | 束缚灵魂 | 避免技术用语“绑定”，体现魔法束缚 |
| `Lesser Beckoning` | 次级召唤 | 次级招引 | 与 `Beckoning Gale` 统一词根，并准确表达拉近目标 |
| `Fastroot` | 快速扎根 | 速生根须 | 施法者并未扎根；法术让种子迅速生根缠住目标 |
| `Sojourning Bolt` | 旅居箭 | 羁旅箭 | 保留跨越、迁移和短暂停留的语感 |
| `Stoke Flames` | 煽动火焰 | 煽旺火焰 | `stoke` 指添燃料使火势更旺，不是抽象“煽动” |
| `Combustion Breath` | 燃烧吐息 | 爆燃吐息 | 体现命中后触发爆燃的效果 |
| `Flashing Balestra` | 闪光弩击 | 闪跃突刺 | `balestra` 是击剑中的前跃接突刺，不是弩箭 |
| `Summon Seismosaurus Egg` | 召唤震龙蛋 | 召唤地震龙蛋 | 与 `Seismosaurus` 实体名和地震冲击波效果统一 |
| `Ravenous Swarm` | 贪婪虫群 | 饥渴蝠群 | 实际召出吸血蝙蝠群；`ravenous` 表示极度饥饿 |

### 已移除兼容法术（3 项）

这些名称仍存在于 `TAG_MAJOR_VERSION == 34` 兼容数据中，不是当前版本可正常
获得的法术。修改只修正明确的中文语序或系列关系，不据缺失机制臆造新含义。

| 英文名 | 原译名 | 新译名 | 修改重点 |
|---|---|---|---|
| `Control Teleport` | 传送控制 | 控制传送 | 修正中文倒装 |
| `Control Undead` | 亡灵控制 | 控制亡灵 | 修正中文倒装 |
| `Animate Skeleton` | 召唤骷髅 | 操纵骷髅 | 与 `Animate Dead → 操纵死尸` 统一；不是召唤新生物 |

## 法术描述修改

共有 201 个中文法术描述条目发生变化。主要修改类型如下：

1. **机制纠错**：修正目标、范围、是否需要直达射线、抵抗方式、伤害类型、
   位移方向、召唤物种类和持续条件等事实。
2. **补全遗漏**：补回英文描述中已有但中文缺失的限制、例外、二阶段效果、
   威力缩放和玩法后果。
3. **术语统一**：统一“法术威力”“衰竭”“神圣生物”“恶魔”“活物”
   “寒气云”等现行术语。
4. **重译过期文本**：部分中文描述仍对应旧机制，已依据当前英文描述和实现
   重译，而不是只做字面润色。
5. **语言修整**：消除病句、错误指代和生硬直译，并保留 TextDB 换行及格式。

### 代表性机制修正

| 法术 | 修改前要点 | 修改后要点 |
|---|---|---|
| `Dispersal` | 笼统写成“传送掉近距离生物”，混淆抵抗和混乱判定 | 明确附近全体先远距传送；抵抗者仍短距闪送；怪物另做一次独立意志检定决定是否混乱 |
| `Bolt of Draining` | 只说“被击中的生物会衰竭” | 明确穿透、只对活物造成负能量伤害并施加衰竭 |
| `Draining Gaze` | 错写成“吸取生命力，无需直接视线” | 明确按最大生命值比例衰竭；需要视线，但无需直达射线 |
| `Deflect Missiles` | 错称单目标攻击比穿透攻击更容易回避 | 改为排斥力场提高对所有投射物的闪避，且无法行动时仍有效 |
| `Bind Souls` | 未说明排除施法者及目标必须是活物 | 明确影响附近其他活物，死后化为拟像 |
| `Flashing Balestra` | 误写成发射弩箭并击退 | 重译为军械库灵魂闪跃而出、持械攻击、短暂决斗后返回 |
| `Freezing Gust` | 误写成伤害并减速路径上的敌人 | 改为穿透性严寒气流，并沿途留下致命寒气云 |
| `Sojourning Bolt` | 误写成能量束在不同维度间弹跳 | 重译为不稳定双射冲击，以及延迟传送、向盟友移动和可能携施术者同行 |
| `Nazja's All-Purpose Tempering` | 误写成强化已装备武器或护甲 | 重译为修复并强化附近构装体，同时以火花、熔渣和冲击波伤害邻敌 |
| `Vhi's Electric Charge` | 将冲锋距离写成“蓄力长度”，伤害公式含糊 | 明确额外电击伤害取决于冲锋距离、法术威力和本次物理攻击伤害 |
| `Primal Wave` | “击倒目标”可能被理解成倒地状态 | 改为可能将目标击退，并留下短时浅水 |
| `Summon Seismosaurus Egg` | 实体名不统一，部分句子生硬 | 统一“地震龙”，并澄清孵化、相邻维持、冲击波和威力缩放 |
| `Death Channel` | 将 `living creatures, demons and holy beings` 误写成“生物、邪物和圣物” | 改为“活物、恶魔和神圣生物”，并明确引导期间留下幽魂 |
| `Borgnjor's Revivification` | 使用错误术语“法术力量” | 统一为“法术威力”；标题同时由“复活”改为“复苏” |

### 完整描述条目清单（201 项）

以下列出所有正文发生变化的 `spells.txt` 条目，按英文首字母分组。此处列的是
TextDB 条目名；每个条目的逐字修改可用文末命令复核。

- **A**：`Abjuration`、`Alistair's Intoxication`、`Animate Dead`、`Antimagic Gaze`、`Apportation`、`Arcjolt`
- **B**：`Berserk Other`、`Bind Souls`、`Blink Close`、`Bolt of Draining`、`Borgnjor's Revivification`、`Brom's Barrelling Boulder`
- **C**：`Call Canine Familiar`、`Call Down Damnation`、`Call Imp`、`Call Lost Souls`、`Call Tide`、`Chain Lightning`、`Charm`、`Confusing Touch`、`Confusion Gaze`、`Conjure Ball Lightning`、`Conjure Living Spells`、`Corrosive Bolt`、`Corrupting Pulse`、`Curse of Agony`、`Cigotuvi's Putrefaction`、`Creeping Shadow`、`Crystallising Shot`
- **D**：`Death Channel`、`Death's Door`、`Deflect Missiles`、`Dimension Anchor`、`Dispel Undead`、`Dispel Undead Range`、`Dispersal`、`Dragon's Call`、`Detonation Catalyst`、`Diamond Sawblades`、`Diminish Spells`、`Divine Armament`、`Dominate Undead`、`Doom Bolt`、`Draining Gaze`
- **E**：`Enfeeble`、`Eringya's Surprising Crocodile`
- **F**：`Fire Storm`、`Flaming Cloud`、`Flash Freeze`、`Fleetfoot`、`Forceful Invitation`、`Fulminant Prism`、`Forge Blazeheart Golem`、`Forge Lightning Spire`、`Flashing Balestra`、`Forge Monarch Bomb`、`Forge Phalanx Beetle`、`Fortress Blast`、`Freezing Gust`
- **G**：`Gloom`、`Ghostly Fireball`、`Ghostly Sacrifice`、`Glaciate`、`Grasping Roots`、`Grave Claw`、`Greater Ensnare`
- **H**：`Hailstorm`、`Heal Other`、`Hellfire Court`、`Hunting Call`、`Hellfire Mortar`、`Hoarfrost Cannonade`
- **I**：`Iceblast`、`Ignite Poison`、`Injury Bond`、`Inner Flame`、`Iskenderun's Battlesphere`、`Iskenderun's Mystic Blast`、`Ill Omen`
- **K**：`Kiss of Death`、`Kinetic Grapnel`
- **L**：`Lehudib's Crystal Spear`、`Landbreaker`、`Launch Bomblet`、`Launch Sporangium`
- **M**：`Major Healing`、`Malign Gateway`、`Malmutate`、`Manifold Assault`、`Mara Summon`、`Maxwell's Capacitive Coupling`、`Mephitic Cloud`、`Miasma Breath`、`Might Other`、`Might`、`Mindburst`、`Minor Healing`、`Monstrous Menagerie`、`Mercury Arrow`、`Magma Barrage`、`Magnavolt`、`Mass Regeneration`、`Maxwell's Portable Piledriver`、`Mutagenic Gaze`
- **N**：`Nazja's All-Purpose Tempering`、`Nazja's Percussive Tempering`
- **O**：`Olgreb's Toxic Radiance`、`Ostracise`
- **P**：`Pain`、`Paralysis Gaze`、`Passwall`、`Petrifying Cloud`、`Phantom Mirror`、`Plane Rend`、`Plasma Beam`、`Poison Arrow`、`Poisonous Cloud`、`Polar Vortex`、`Primal Wave`、`Pyre Arrow`、`Permafrost Eruption`、`Phantom Blitz`、`Poisonous Vapours`、`Pyrrhic Recollection`
- **Q**：`Quicksilver Bolt`
- **R**：`Rebounding Blaze`、`Rebounding Chill`、`Regenerate Other`、`Rending Blade`
- **S**：`Sentinel's Mark`、`Sap Magic`、`Sculpt Simulacrum`、`Seal Doors`、`Shadow Creatures`、`Sheza's Dance`、`Shock`、`Silence`、`Smiting`、`Spellspark Servitor`、`Spit Lava`、`Sporulate`、`Starburst`、`Static Discharge`、`Sticky Flame`、`Stone Arrow`、`Summon Cactus Giant`、`Summon Drakes`、`Summon Earth Elementals`、`Summon Emperor Scorpions`、`Summon Executioners`、`Summon Eyeballs`、`Summon Greater Demon`、`Summon Sin Beast`、`Summon Hell Sentinel`、`Summon Holies`、`Summon Horrible Things`、`Summon Hydra`、`Summon Illusion`、`Summon Mana Viper`、`Summon Minor Demon`、`Summon Mushrooms`、`Summon Tzitzimitl`、`Summon Ufetubus`、`Summon Undead`、`Summon Vermin`、`Symbol of Torment`、`Seismic Stomp`、`Shadow Bind`、`Shadow Draining`、`Shadow Prism`、`Shadow Puppet`、`Shadow Shot`、`Shadow Tempest`、`Shadow Torpor`、`Shadow Turret`、`Shred`、`Sign of Ruin`、`Siphon Essence`、`Sleetstrike`、`Sojourning Bolt`、`Sphinx Sisters`、`Splinterfrost Shell`、`Sticks to Snakes`、`Summon Mortal Champion`、`Summon Seismosaurus Egg`
- **T**：`Teleport Other`、`Throw Ally`、`Throw Barbs`、`Throw Icicle`、`Throw Klown Pie`、`Throw Bolas`
- **V**：`Volatile Blastmotes`、`Vanquished Vanguard`、`Vhi's Electric Charge`、`Vitrifying Gaze`、`Vex`、`Vhi's Electrolunge`
- **W**：`Weakening Gaze`、`Warp Body`、`Warp Space`
- **Y**：`Yara's Violent Unravelling`

> 注：同一个条目只应出现一次。上述清单以 TextDB 的实际差异为准，
> 与法术在复审结果文档中的系列归组无关。

## 关联状态和界面术语

除法术标题外，`source.txt` 还同步修正了 19 个关联条目：

- `Mesmerise` 系列状态和提示统一使用“迷魂／迷住”，不再误称“催眠”；
  涉及 `Mesm`、`mesmerised`、`mesmerising`、状态栏短名、冷却提示、
  凝视提示、宝珠充能提示和装备限制说明。
- `mana viper` 的出现提示由“魔力蝰蛇”统一为“魔力毒蛇”。
- `Serpent of Hell (%s)` 由“地狱蛇”统一为“地狱巨蛇”。
- 普通名词 `vortex` / `vortices` 由“涡流”统一为“漩涡”。

这些条目是法术名称复审引出的关联术语收口，但不是独立法术标题，故没有计入
前述 53 项。

## 复核方式

查看所有法术标题及关联 `source.txt` 修改：

```bash
git diff 5cb9aa27a224a81da780757f8445cfc07de09dfd..8a5cb19202e1a2eb21bd32578b92e0aed97b86af \
  -- crawl-ref/source/dat/i18n/zh/source.txt
```

查看所有中文法术描述修改：

```bash
git diff 5cb9aa27a224a81da780757f8445cfc07de09dfd..8a5cb19202e1a2eb21bd32578b92e0aed97b86af \
  -- crawl-ref/source/dat/descript/zh/spells.txt
```

逐项审阅证据、裁定和实现位置见 `docs/spell-name-review-results.md`；
复审范围、冻结基线和验收口径见 `docs/spell-name-review-plan.md`。
