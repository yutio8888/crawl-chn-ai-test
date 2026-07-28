# 角色机制显示全量校对结果

本文件是 GitHub Issue #27 的逐项审计记录。每一行是一张规范证据卡：身份、
生命周期、英文/中文显示、生产事实和唯一终态结论均来自冻结 inventory。
全量 696 个身份均有且仅有一张证据卡；审计器机械证明 inventory 与结果集合相等。

## 冻结与当前进度

- 基线：`76c815b2ac79d11a8066597ad04d127a1636e153`
- 结构校准后 inventory：
  `9a3576f3b1f62aa8856654129aec02c6a699725b5ede3b1c032fd844479ed1cd`
- 技能清单补全特殊称号并完成本批修订后的 inventory：
  `1988187abe0fb06dbf36d82948a1df5e3b668aa51720f3a49876c078da4b49d1`
- 非神祇能力批次完成后的 inventory：
  `353aa2e478deb968c5dfbfb0b5b847570c8e4ac35de44b65f6a09331e1a1be82`
- 全量变异、时长状态、附加状态与怪物状态完成后的 inventory：
  `2f0d20bbb5ce9829af7f7f0f683f36620cc31513f6825765ab39e212cd8000f5`
- 术语表 SHA-256：
  `4070a396e65a4bdf1fd2dfbc9e95bcc40053391e65441053f73c08146ed31d9e`
- 当前证据卡：变异 213、时长状态 223、附加状态 49、怪物状态 139、
  非神祇能力 35、技能 34、属性 3，共 696。
- 结构结果：重复、漏译、描述缺失、描述重复与陈旧描述键均为零。

技能的五档常规称号继续采用有效裁定 D-C-001：生产称号输入在本候选中未改，
现役技能的翻译均完整。徒手格斗另核对两组各五项的特殊称号。五个已移除技能
是 TAG 34 存档兼容身份；“保留：兼容身份”是终态结论，不补造现役说明，若其
生命周期恢复则必须重新审阅。

## 属性证据卡（3）

| 身份 | 生命周期 | 名称与显示形式 | 生产事实 | 终态结论 |
|---|---|---|---|---|
| `attribute:STAT_DEX` | current | dexterity → 敏捷；clumsy → 变笨拙；agile → 敏捷 | `player-stats.cc` 四个显示槽完整；两个 clumsy 槽同义复用 | 保留：名称与增减状态词准确 |
| `attribute:STAT_INT` | current | intelligence → 智力；dopey → 变迟钝；stupid → 变笨；clever → 变聪明 | `player-stats.cc` 四个显示槽完整 | 保留：名称与增减状态词准确 |
| `attribute:STAT_STR` | current | strength → 力量；weakened → 变虚弱；weaker → 变弱；stronger → 变强壮 | `player-stats.cc` 四个显示槽完整 | 保留：名称与增减状态词准确 |

## 技能证据卡（34）

“五档完整”表示五个生产称号均有中文，且本候选未改称号输入，复用 D-C-001。

| 身份 | 生命周期 | 名称与显示形式 | 生产事实 | 终态结论 |
|---|---|---|---|---|
| `skill:SK_AIR_MAGIC` | current | Air Magic → 空气魔法 | abbr Air；五档完整；说明与英文生产描述逐句核对 | 修订：统一“空气魔法／诅咒系／法术威力” |
| `skill:SK_ALCHEMY` | current | Alchemy → 炼金术 | abbr Alch；五档完整；原名称误落到小写通用词“炼金” | 修订：名称与说明统一为“炼金术” |
| `skill:SK_ARMOUR` | current | Armour → 护甲 | abbr Arm；五档完整；说明覆盖 AC 与重甲惩罚 | 修订：补明护甲值并校准重甲语义 |
| `skill:SK_AXES` | current | Axes → 斧类 | abbr Axs；五档完整；交叉训练 Maces & Flails、Polearms | 修订：统一三项技能专名 |
| `skill:SK_CHARMS` | compatibility | Charms → — | abbr Chrm；TAG 34 已移除；无现役名称或说明消费者 | 保留：兼容身份 |
| `skill:SK_CONJURATIONS` | current | Conjurations → 咒法系 | abbr Conj；五档完整；说明覆盖伤害、命中、射程与范围 | 修订：统一技能自指与法术威力 |
| `skill:SK_CROSSBOWS` | compatibility | Crossbows → — | abbr Crb；TAG 34 已移除；无现役名称或说明消费者 | 保留：兼容身份 |
| `skill:SK_DODGING` | current | Dodging → 闪避 | abbr Ddg；五档完整；附魔效果与爆炸不可闪避 | 修订：消除将通用 enchantments 误写成旧称“妖术” |
| `skill:SK_EARTH_MAGIC` | current | Earth Magic → 大地魔法 | abbr Erth；五档完整；说明覆盖物理伤害、抗性与炼金术关联 | 修订：统一“大地魔法”及法术威力 |
| `skill:SK_EVOCATIONS` | current | Evocations → 魔力释放 | abbr Evo；五档完整；说明覆盖魔杖等魔法物品 | 修订：按技能域统一自指“魔力释放技能” |
| `skill:SK_FIGHTING` | current | Fighting → 格斗 | abbr Fgt；五档完整；说明覆盖命中、伤害与生命上限 | 修订：精确区分物理战斗与生命上限 |
| `skill:SK_FIRE_MAGIC` | current | Fire Magic → 火焰魔法 | abbr Fire；五档完整；说明覆盖远程火焰伤害与咒法系 | 修订：统一“火焰魔法”及法术威力 |
| `skill:SK_FORGECRAFT` | current | Forgecraft → 锻造术 | abbr Frge；五档完整；说明覆盖机械生物、陷阱、路障与护甲转武器 | 保留：现译完整准确 |
| `skill:SK_HEXES` | current | Hexes → 诅咒系 | abbr Hex；五档完整；说明覆盖非直接伤害与意志力检定 | 重译：移除旧称“妖术”，恢复完整机制语义 |
| `skill:SK_ICE_MAGIC` | current | Ice Magic → 寒冰魔法 | abbr Ice；五档完整；说明覆盖直接伤害与冰制护甲 | 修订：统一“寒冰魔法”及法术威力 |
| `skill:SK_INVOCATIONS` | current | Invocations → 祈神 | abbr Invo；五档完整；说明含灯神条件分支与法力贡献取高值 | 修订：统一“祈神／法力／施法能力”并澄清取高规则 |
| `skill:SK_LONG_BLADES` | current | Long Blades → 长刃 | abbr LBl；五档完整；与短刃双向交叉训练 | 保留：名称、说明与交叉训练准确 |
| `skill:SK_MACES_FLAILS` | current | Maces & Flails → 锤与链枷 | abbr M&F；五档完整；交叉训练 Axes、Staves | 修订：移除旧称“棍棒技能”并统一交叉技能专名 |
| `skill:SK_NECROMANCY` | current | Necromancy → 死灵术 | abbr Necr；五档完整；原名称误落到小写通用词“死灵” | 修订：名称、技能自指与法术威力 |
| `skill:SK_POLEARMS` | current | Polearms → 长柄武器 | abbr Pla；五档完整；两格攻击；交叉训练 Axes、Staves | 修订：统一交叉技能专名 |
| `skill:SK_RANGED_WEAPONS` | current | Ranged Weapons → 远程武器 | abbr Rng；五档完整；说明覆盖弓、弩和投石索 | 保留：名称与说明准确 |
| `skill:SK_SHAPESHIFTING` | current | Shapeshifting → 变形术 | abbr Shft；五档完整；说明覆盖护符、形态门槛、生命损失与强化 | 重译：移除“变身／符咒”旧称并恢复机制对象 |
| `skill:SK_SHIELDS` | current | Shields → 盾牌 | abbr Shd；五档完整；说明覆盖格挡与盾牌惩罚 | 修订：技能自指由“格挡技能”改为“盾牌技能” |
| `skill:SK_SHORT_BLADES` | current | Short Blades → 短刃 | abbr SBl；五档完整；无力反抗目标；与长刃双向交叉训练 | 修订：把 helpless 与仅“未警觉”准确区分 |
| `skill:SK_SLINGS` | compatibility | Slings → — | abbr Slg；TAG 34 已移除；无现役名称或说明消费者 | 保留：兼容身份 |
| `skill:SK_SPELLCASTING` | current | Spellcasting → 施法能力 | abbr Spc；五档完整；灯神与非灯神 Lua 分支保持不变 | 修订：修复重复“和”，恢复略微加成、法力与法术槽语义 |
| `skill:SK_STABBING` | compatibility | Stabbing → — | abbr Stb；TAG 34 已移除；无现役名称或说明消费者 | 保留：兼容身份 |
| `skill:SK_STAVES` | current | Staves → 杖类 | abbr Stv；五档完整；交叉训练 Maces & Flails、Polearms | 修订：统一杖类与锤与链枷专名 |
| `skill:SK_STEALTH` | current | Stealth → 潜行 | abbr Sth；五档完整；说明覆盖察觉、追踪、重创几率与额外伤害 | 修订：恢复 distracted/helpless 区别及额外伤害量 |
| `skill:SK_SUMMONINGS` | current | Summonings → 召唤系 | abbr Summ；五档完整；说明覆盖持续时间、盟友、尸体、经验与临时装备 | 修订：恢复装备消散语义并统一技能自指 |
| `skill:SK_THROWING` | current | Throwing → 投掷 | abbr Thr；五档完整；生产说明只含命中、伤害与魔法飞镖 | 修订：删除已不存在的回旋镖返回机制 |
| `skill:SK_TRANSLOCATIONS` | current | Translocations → 传送系 | abbr Tloc；五档完整；说明覆盖短距自移与传走敌人 | 重译：移除旧称“移位系”并统一法术威力 |
| `skill:SK_TRAPS` | compatibility | Traps → — | abbr Trp；TAG 34 已移除；无现役名称或说明消费者 | 保留：兼容身份 |
| `skill:SK_UNARMED_COMBAT` | current | Unarmed Combat → 徒手格斗 | abbr UC；五档完整；武术与爪牙特殊称号各五项均完整 | 保留：名称、说明与两组特殊称号准确 |

## 非神祇能力证据卡（35）

生产事实摘要列记录 `Ability_List` 的关键费用、失败依据、射程或 flags；完整初始化器
仍由 inventory 保存。Issue #25 拥有的 124 个神祇能力身份已机械排除。

| 身份 | 生命周期 | 名称与显示形式 | 生产事实 | 终态结论 |
|---|---|---|---|---|
| `ability:ABIL_BAT_SWARM` | current | Bat Swarm → 蝙蝠群 | instant；经验充能；变形术提高充能速度 | 修订：将 evasively 准确译为灵活闪避 |
| `ability:ABIL_BESTIAL_TAKEDOWN` | current | Bestial Takedown → 兽性扑倒 | target；恐惧目标；变形术伤害倍率；击杀触发嚎叫 | 保留：名称、目标限制与效果准确 |
| `ability:ABIL_BLINKBOLT` | current | Blinkbolt → 闪烁箭 | LOS 射程；路径电击；位移至箭矢终点；短冷却 | 修订：消除“物体／它”的指代歧义 |
| `ability:ABIL_BREATHE_POISON` | current | Breathe Poison Gas → 吐息毒气 | XL 失败率；breath；方向或目标；射程 6 | 修订：按能力术语统一名称 |
| `ability:ABIL_BREATHE_RUST` | current | Breathe Rust → 喷吐铁锈 | 法力费用缩放；持续腐蚀、削弱攻击；极少伤害 | 修订：校准 minimal damage |
| `ability:ABIL_CACOPHONY` | current | Cacophony → 杂音 | 经验充能；附身护甲独立攻击；短距离牵引；负面状态 | 重译：恢复持续时间、牵引距离、穿透射击与 maladies 语义 |
| `ability:ABIL_CAUSTIC_BREATH` | current | Caustic Breath → 腐蚀吐息 | XL 失败率；龙息充能；酸液与腐蚀云 | 保留：名称与说明准确 |
| `ability:ABIL_COMBUSTION_BREATH` | current | Combustion Breath → 爆燃吐息 | XL 失败率；龙息充能；触敌爆炸；使用者免疫 | 保留：名称与说明准确 |
| `ability:ABIL_DAMNATION` | current | Hurl Damnation → 投掷天谴 | XL 失败率；生命费用 150；射程 6；无视护甲抗性 | 保留：名称与说明准确 |
| `ability:ABIL_DIG` | current | Dig → 挖掘 | instant；max_hp_drain；松软岩石与锈蚀栅栏；移动取消规则 | 重译：恢复准备、挖掘触发、生命上限与取消条件 |
| `ability:ABIL_END_TRANSFORMATION` | current | End Transformation → 结束变形 | 无费用；恢复正常形态 | 保留：名称与说明准确 |
| `ability:ABIL_ENKINDLE` | current | Enkindle → 点燃 | instant；记忆资源；伤害法术免法力；成功率与法术威力加成 | 修订：统一法力与法术威力术语 |
| `ability:ABIL_EVOKE_BLINK` | current | Evoke Blink → 激发闪烁 | Evocations 失败依据；随机短距传送；技能影响冷却 | 重译：移除“移位／激活技能”旧称并澄清冷却 |
| `ability:ABIL_EVOKE_DISPATER` | current | Evoke Damnation → 激发天谴 | 生命费用 100；射程 6；威力随 Evocations；无视保护 | 重译：修复“诅咒／天遣／盔甲”三处术语错误 |
| `ability:ABIL_EVOKE_OLGREB` | current | Evoke the Staff of Olgreb → 激发奥尔格雷布之杖 | 持握限定；毒素光环；威力随 Evocations | 修订：统一物品名、技能名与中毒效果 |
| `ability:ABIL_EVOKE_TURN_INVISIBLE` | current | Evoke Invisibility → 激发隐形 | Evocations 失败依据；max_hp_drain；短暂隐形 | 修订：删除重复句 |
| `ability:ABIL_GALVANIC_BREATH` | current | Galvanic Breath → 电击吐息 | XL 失败率；龙息充能；连锁电弧 | 修订：澄清电弧传播 |
| `ability:ABIL_GLACIAL_BREATH` | current | Glacial Breath → 冰川吐息 | XL 失败率；龙息充能；击杀目标封入耐久冰块 | 修订：恢复 durable 与击杀目标指代 |
| `ability:ABIL_GOLDEN_BREATH` | current | Golden Breath → 金龙吐息 | 龙息充能；火焰与寒冷伤害；毒气云 | 保留：名称与说明准确 |
| `ability:ABIL_HEAL_WOUNDS` | current | Heal Wounds → 治疗创伤 | XL 失败率；显著治疗；概率永久损失 1 点法力上限 | 修订：按能力术语更名并校准 HP/MP |
| `ability:ABIL_HOP` | current | Hop → 跳跃 | 目的地附近落点；不移动一段时间后恢复 | 修订：统一动作名称并澄清其他动作允许 |
| `ability:ABIL_IMBUE_SERVITOR` | current | Imbue Servitor → 灌注仆从 | delay；选择破坏性法术；失败率上限 20%；替换旧法术 | 保留：名称、限制与延迟效果准确 |
| `ability:ABIL_IMPRINT_WEAPON` | current | Imprint Weapon → 烙印武器 | delay；神器近战武器；白金典范复制品 | 修订：消除 one 的指代歧义 |
| `ability:ABIL_INVENT_GIZMO` | current | Invent Gizmo → 发明装置 | 齿轮地精一次性永久装备安装 | 修订：补全 coglin 物种语义 |
| `ability:ABIL_MUD_BREATH` | current | Mud Breath → 泥浆吐息 | XL 失败率；龙息充能；击退、泥泞与攻击失手 | 保留：名称与说明准确 |
| `ability:ABIL_NON_ABILITY` | internal | No ability → 无能力 | 内部哨兵；显示即程序错误 | 保留：内部身份与诊断说明准确 |
| `ability:ABIL_NOXIOUS_BREATH` | current | Noxious Breath → 毒瘴吐息 | XL 失败率；龙息充能；毒素抗性判定；高等级扩大云雾 | 修订：修复条件从句歧义 |
| `ability:ABIL_NULLIFYING_BREATH` | current | Nullifying Breath → 消魔吐息 | XL 失败率；龙息充能；驱散效果并干扰施法；使用者免疫 | 修订：补全施法能力语法关系 |
| `ability:ABIL_SHAFT_SELF` | current | Shaft Self → 自掘竖井 | delay；下落一至三层随机位置；挖掘需时间 | 重译：现役恢复后重新裁定名称与说明 |
| `ability:ABIL_SIPHON_ESSENCE` | current | Siphon Essence → 吸取精华 | 折磨附近活物；治疗量随变形术；短冷却 | 修订：移除“变身技能”旧称 |
| `ability:ABIL_SPIDER_JUMP` | current | Jump → 跳跃 | 不可控落点；行动前免受攻击；可能摆脱追踪；短恢复 | 修订：修复“失去你的位置”误译 |
| `ability:ABIL_SPIT_POISON` | current | Spit Poison → 喷吐毒液 | XL 失败率；breath；方向或目标；不可对自身 | 保留：名称与说明准确 |
| `ability:ABIL_STEAM_BREATH` | current | Steam Breath → 蒸汽吐息 | XL 失败率；龙息充能；烫伤与遮蔽视线云雾 | 保留：名称与说明准确 |
| `ability:ABIL_WATERY_GRAVE` | current | Watery Grave → 水葬 | 经验充能；水域潮汐；淹没、沉默法术限制与窒息伤害 | 修订：修复目标指代与“无法施放”语义 |
| `ability:ABIL_WORD_OF_CHAOS` | current | Word of Chaos → 混沌之语 | XL 失败率；max_hp_drain；闪烁远离；减速、束缚或恐惧 | 重译：恢复 blink away、ensnared 与生命上限代价 |

## 变异证据卡（213）

| 身份 | 生命周期 | 名称与显示形式 | 生产事实 | 终态结论 |
|---|---|---|---|---|
| `mutation:MUT_ACCURSED` | current | accursed → 被诅咒；显示：被诅咒；你从厄运和灾祸中恢复得更慢。；你感到被诅咒了。；你感到诅咒减轻了。 | 1 级；weight 0；flags mutflag::bad；说明：你的诅咒本质使得驱散你身上的恶毒能量更加困难， 降低了你能从厄运和灾祸中恢复的速度。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_ACIDIC_BITE` | current | acidic bite → 酸性撕咬；显示：酸性撕咬；你有酸性唾液。；酸液开始从你的口中滴落。；你的嘴感到干燥。 | 1 级；weight 0；flags mutflag::good ／ mutflag::ji…；说明：你有了酸性唾液，在近战时能够咬伤敌人，并对其造成腐蚀。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_ACID_RESISTANCE` | current | acid resistance → 酸蚀抗性；显示：酸蚀抗性；你对酸蚀有抗性。（酸抗）；你感到对酸液有抗性。；你感到对酸液的抗性减弱了。 | 1 级；weight 0；flags mutflag::good ／ mutflag::su…；说明：你抵抗酸（rCorr），酸对你造成的伤害变弱。你也变得更难被腐蚀。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_ACROBATIC` | current | acrobatic → 杂技；显示：杂技；你可以在移动或等待时魔法般地闪避攻击。 | 1 级；weight 0；flags mutflag::good；说明：你那神奇的天性有助于你杂技般地翻滚你的空心骨头，从而能在移动或等待时躲避攻击。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_ACUTE_VISION` | current | see invisible → 识破隐形；显示：识破隐形；你拥有超自然的敏锐视觉。（看破隐形）；你的视力变敏锐了。；你的视力似乎变迟钝了。 | 1 级；weight 2；flags mutflag::good；说明：你有着超乎寻常的敏锐视力，可以看到隐藏在世俗眼界之外的怪物。 然而，它对你的命中率没有影响。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_AGILE` | current | agile → 敏捷；显示：敏捷；你很敏捷。（敏捷+4，力量/智力-1）；你非常敏捷。（敏捷+8，力量/智力-2） | 2 级；weight 7；flags mutflag::good；说明：你的反应变得异常迅捷。这个变异每升一级会加4点敏捷， 但你身体的其他部分无法跟上你的速度，每升一级，你的力量和智力会减1点。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_ANTENNAE` | current | antennae → 触角；显示：触角；你头上有一对小触角。；你头上有一对触角。；你头上有一对大触角。（看破隐形）；一对触角从你的头上长了出来！；你头上的触角又长大了一些。；你头上的触角缩没了。；你头上的触角缩小了一些。 | 3 级；weight 4；flags mutflag::good ／ mutflag::an…；说明：你长出触角，可以感知周围的怪物，但无法戴头盔。这个变异每升一级， 你会感知到更远的怪物。这个变异达到第三级， 能看到隐形的怪物，但你将无法戴任… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_ANTIMAGIC_BITE` | current | antimagic bite → 禁魔咬击；显示：禁魔咬击；你的咬击能干扰并吸收敌人的魔法。；你突然渴望魔法。；你的魔力需求减少了。 | 1 级；weight 0；flags mutflag::good ／ mutflag::an…；说明：你对魔法有着渴求，在近战时能够咬伤敌人。 这可以恢复你的法力并扰乱使用魔法的敌人，有时会让他们无法行动。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_ANTI_WIZARDRY` | current | disrupted magic → 干扰魔法；显示：干扰魔法；你的施法受到轻微干扰。；你的施法受到干扰。；你的施法受到严重干扰。；你控制魔法的能力受到了干扰。；你控制魔法的能力受到了更严重的干扰。；你控制魔法的能力不再受到干扰。；你控制魔法的能力受到的干扰减轻了。 | 3 级；weight 0；flags mutflag::bad；说明：你施法的失误几率会更高。这个舍弃每升一级，施法就越容易失误。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_ARMOURED_TAIL` | current | armoured tail → 装甲尾巴；显示：装甲尾巴；你有一条装甲尾巴。；你有一条沉重的装甲尾巴。 | 2 级；weight 0；flags mutflag::good ／ mutflag::an…；说明：你长出一条披着甲的大尾巴，在近战时能够扫打敌人。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_ARTEFACT_ENCHANTING` | current | artefact enchanting → 神器附魔；显示：神器附魔；你可以使用附魔卷轴强化次级神器。；你现在可以对低级神器使用附魔卷轴了。；你无法再对低级神器使用附魔卷轴了。 | 1 级；weight 0；flags mutflag::good；说明：你可以对随机生成的神器使用武器附魔卷轴和护甲附魔卷轴。 附魔等级不能超过同类普通物品通常可达到的上限，特别奇异的神器则完全无法附魔。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_AUGMENTATION` | current | augmentation → 增强；显示：增强；你在高生命时魔法和物理力量略微增强。；你在高生命时魔法和物理力量增强。；你在高生命时魔法和物理力量大幅增强。；你感到力量流入体内。；你感到力量涌入体内。；你感到被力量充满。 | 3 级；weight 0；flags mutflag::good；说明：在健康状况良好的情况下，你会更有能量，更有效地施展法术并杀死敌人。 这个变异每升一级，其效果都会增强。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_BEAK` | current | beak → 鸟喙；显示：鸟喙；你有一张喙状的嘴。；你的嘴变长变硬，成了一只喙！；你的喙变短变软，成了正常的嘴。 | 1 级；weight 1；flags mutflag::good ／ mutflag::an…；说明：你的嘴成了鸟喙，在近战时能够啄击敌人，但无法戴头盔。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_BIG_BRAIN` | current | big brain → 大型大脑；显示：大型大脑；你有一个异常大的大脑。（智力+2）；你有一个极其巨大的大脑。（智力+4）；你有一个绝对庞大无比的大脑。（智力+6，巫术）；你的大脑膨胀了。；你的大脑膨胀到了惊人的大小。；你的大脑恢复了正常大小。；你的大脑缩小了。 | 3 级；weight 0；flags mutflag::good；说明：出什么事了？你有一个大脑袋。这个变异每升一级会加2点智力。 这个变异达到第三级，你在施法时就更不容易失误。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_BIG_WINGS` | current | big wings → 大翅膀；显示：大翅膀；你大而强壮的翅膀让你能够飞行。；你的翅膀长得更大更强壮。；你的翅膀萎缩变弱了。 | 1 级；weight 4；flags mutflag::good ／ mutflag::an…；说明：你长出巨大、强壮的翅膀，它能够承载你在空中飞行。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_BLACK_MARK` | current | black mark → 黑色印记；显示：黑色印记；你的近战攻击可能会削弱你的敌人。；一个不祥的黑色印记在你身上形成。 | 1 级；weight 0；flags mutflag::good；说明：当你近战攻击敌人时，你身上的黑色标记可能会削弱敌人。 它能够虚弱敌人、汲取他们的生命力，或扰乱他们的魔法。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_BOOMING_VOICE` | current | booming voice → 洪亮嗓音；显示：洪亮嗓音；你在敌人视野中时，阅读卷轴的声音异常响亮。；你感到声音膨胀到雷鸣般的音量。；你的声音安静到了合理的音量。 | 1 级；weight 3；flags mutflag::bad；说明：当你在敌对怪物的视线范围内阅读卷轴时，你的声音会以惊人的音量响起。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_CAMOUFLAGE` | current | camouflage → 伪装；显示：伪装；你的皮肤会变色以匹配环境。（潜行+）；你的皮肤与周围环境完美融合。（潜行++）；你的皮肤完美模拟周围环境。（潜行+++）；你的皮肤成为了天然伪装。；你的天然伪装更加有效了。；你的皮肤不再是天然伪装了。；你的天然伪装效果减弱了。 | 3 级；weight 1；flags mutflag::good ／ mutflag::su…；说明：你的皮肤会根据周围环境而变色。这个变异每升一级会提升潜行。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_CLARITY` | current | clarity → 清晰；显示：清晰；你拥有非凡的心智清晰。；你的思维似乎更清晰了。；你的思维似乎混乱了。 | 1 级；weight 6；flags mutflag::good；说明：你的头脑异常清晰，你不会被混乱、迷惑或产生超自然的恐惧。 你也不会不由自主地狂暴。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_CLAWS` | current | claws → 利爪；显示：利爪；你有锋利的指甲。；你有非常锋利的指甲。；你手上有爪子。；你的指甲变长了。；你的指甲变锋利了。；你的双手扭曲成了爪子。；你的指甲缩回了正常大小。；你的指甲看起来变钝了。；你的双手感觉更有肉了。 | 3 级；weight 2；flags mutflag::good ／ mutflag::an…；说明：你长出锋利的指甲，如果不戴手套，会增加主手的徒手攻击强度。 如果你的副手没有装备东西，也会增强其拳击强度。这个变异每升一级， 你的指甲就会更尖… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_CLEVER` | current | clever → 聪慧；显示：聪慧；你的头脑敏锐。（智力+4，力量/敏捷-1）；你的头脑非常敏锐。（智力+8，力量/敏捷-2） | 2 级；weight 7；flags mutflag::good；说明：你的心智变得异常敏锐。这个变异每升一级会加4点智力， 但所有的血液都供向了头部，因而削弱了你的体质， 每升一级，你的力量和敏捷会减1点。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_CLUMSY` | current | clumsy → 笨拙；显示：笨拙；你很笨拙。（敏捷-3）；你非常笨拙。（敏捷-6） | 2 级；weight 8；flags mutflag::bad；说明：你的反应变得异常笨拙。这个变异每升一级会减3点敏捷。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_COLD_BLOODED` | current | cold-blooded → 冷血；显示：冷血；你是冷血动物，可能被寒冷攻击减速。；你变得冷血了。；你变得温血了。 | 1 级；weight 0；flags mutflag::bad ／ mutflag::nee…；说明：当受到寒冷攻击时，你可能会变慢，直到你的血液再次变暖。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_COLD_RESISTANCE` | current | cold resistance → 寒冷抗性；显示：寒冷抗性；你耐寒。（冰抗+）；你非常耐寒。（冰抗++）；你几乎对寒冷效果免疫。（冰抗+++）；你感到对寒冷有抵抗力。；你感到对寒冷的抗性增强了。；你不再感到对寒冷有抗性。；你感到对寒冷的抗性减弱了。 | 3 级；weight 4；flags mutflag::good ／ mutflag::su…；说明：你抵抗寒冷。这个变异每升一级，就会削弱寒冷对你造成的伤害。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_COLD_VULNERABILITY` | current | cold vulnerability → 寒冷弱点；显示：寒冷弱点；你怕冷。（冰抗-）；你非常怕冷。（冰抗--）；你极其怕冷。（冰抗---）；你感到易受寒冷伤害。；你不再感到易受寒冷伤害。；你感到对寒冷的脆弱减轻了。 | 3 级；weight 3；flags mutflag::bad ／ mutflag::sub…；说明：寒冷很容易对你造成伤害，并会对你造成更多伤害。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_CONDENSATION_SHIELD` | current | condensation shield → 凝结护盾；显示：凝结护盾；一层可融化的冰霜护盾保护你。（盾挡+；冰霜在你面前凝结成盾。 | 1 级；weight 0；flags mutflag::good；说明：一个冰霜盾守护着你，阻挡着一些来袭的攻击。火焰攻击能暂时融化此盾。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_CONSTRICTING_TAIL` | current | naga tail → 纳迦尾巴；显示：纳迦尾巴；你的蛇形下半身移动缓慢。；你的蛇形下半身移动缓慢，但可以缠绕敌人。；你的下半身变成了一条蛇尾。；你的尾巴变得足够强壮，可以勒住敌人。；你的下半身恢复了正常。；你的蛇尾变弱了，无法再勒住敌人。；你的尾巴将变得足够有力，可以束缚敌人。 | 2 级；weight 0；flags mutflag::good ／ mutflag::an…；说明：你的脚变成一条长长的蛇状尾巴，使你能在水中保持稳定， 但移动速度会比大多数物种慢得多。这个变异达到第二级， 你在近战时可以用尾巴束缚敌人。你的… | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_CONTAMINATION_SUSCEPTIBLE` | current | contamination susceptible → 易受污染；显示：易受污染；你从污染中吸收双倍的变异能量。；你感到更易受污染了。；你感到不易受污染了。 | 1 级；weight 0；flags mutflag::bad；说明：你更容易受到魔法污染的影响，使其更快积累。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_CORRUPTING_PRESENCE` | current | corrupting presence → 腐败存在；显示：腐败存在；你的存在有时会腐蚀你伤害的人。；你的存在有时会腐蚀或变形你伤害的人。；你感到腐化。；你的腐化存在变得更加强烈。 | 2 级；weight 0；flags mutflag::good；说明：当你伤害到敌人时，攻击力可能会增强，并能腐蚀他们的武器和防具。 这个变异达到第二级，事态会更为严重，你那可怜的受害者将有可能被变异、变形。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_COWARDICE` | current | cowardly → 懦弱；显示：懦弱；你的懦弱使你在面对有威胁的敌人时战斗效率降低。；你失去了勇气。；你重新获得了勇气。 | 1 级；weight 0；flags mutflag::bad；说明：看到有威胁的怪物会让你充满恐惧， 你的法术威力、近战和远程攻击杀怪物的能力都会受到削弱。 一次看到多个这样的怪物，或极其危险的怪物，会让情况变… | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_DAYSTALKER` | current | +LOS → +视野；显示：+视野；你的视野范围扩大，也可以从远处被看到。；黑暗在你接近时四散逃逸。；阴影再次变得大胆。 | 1 级；weight 0；flags mutflag::good；说明：在你的道路上黑暗会遁形，从而扩大了视野和远程攻击范围（+1视线）， 但也使得你能从更远的地方被发现并成为潜在目标。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_DEFORMED` | current | deformed body → 变形身体；显示：变形身体；护甲在你变形奇怪的身体上不合身。；你的身体扭曲变形。；你的身体形状似乎正常了一些。 | 1 级；weight 8；flags mutflag::bad ／ mutflag::ana…；说明：你的身体被一种非人的方式塑造，这在一定程度上削弱了铠甲提供的防护。 这对护甲附魔提供的防护没有影响，也不会影响训练的护甲技能的防御效果。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_DEMONIC_GUARDIAN` | current | demonic guardian → 恶魔守护者；显示：恶魔守护者；一个弱小的恶魔守护者冲来援助你。；一个恶魔守护者冲来援助你。；一个强大的恶魔守护者冲来援助你。；你感到有一位恶魔守护者存在。；你的守护者力量增长了。；你的恶魔守护者消失了。；你的恶魔守护者变弱了。 | 3 级；weight 0；flags mutflag::good；说明：当你受到伤害时，可能会有恶魔守卫冲过来帮助你。受到的伤害越大，离死亡越近， 其可能性就越大。这个变异每升一级，就会增加你的守卫的力量。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_DEMONIC_MAGIC` | current | demonic magic → 恶魔魔法；显示：恶魔魔法；你施放的法术可能会麻痹相邻的敌人。；你施放的法术可能会麻痹附近的敌人。；你施放的法术和使用的魔杖可能会麻痹附近的敌人。；一股凶险的气息注入了你的魔法。；你的魔法变得更加凶险。；你的魔杖被你的凶险气息所灌注。 | 3 级；weight 0；flags mutflag::good；说明：当你施放法术时，相邻的怪物可能会麻痹。在施放更高等级的法术时， 效果会更为强大，但具有更强意志力的怪物能够抵御它。这个变异每升一级， 就能影响… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_DEMONIC_TOUCH` | current | demonic touch → 恶魔之触；显示：恶魔之触；你的触碰可能对敌人造成少量不可抵抗的伤害。；你的触碰可能对敌人造成不可抵抗的伤害。；你的触碰可能对敌人造成不可抵抗的伤害并削弱他们的意志力。；你的双手开始散发出微弱的邪恶光芒。；你的双手散发出更亮的邪恶光芒。；你的双手扭曲并开始散发出强大的邪恶气息。 | 3 级；weight 0；flags mutflag::good ／ mutflag::an…；说明：你的手散发着邪恶的能量，只要你的副手没有装备东西， 在近战时就能造成无法抵御的伤害。你的触碰攻击会造成无视护甲的伤害， 并且这个变异每升一级会… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_DEMONIC_WILL` | current | demonic willpower → 恶魔意志；显示：恶魔意志；你惩罚那些试图扭曲你意志的人。（意志+）；你感到任性。 | 1 级；weight 0；flags mutflag::good；说明：你的意志力有了自己的意图，有时它会伤害那些试图给你下咒的人。 这个变异还会增强你的意志力。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_DEVOLUTION` | current | devolution → 退化；显示：退化；你拥有隐藏的基因缺陷。；你拥有可怕的隐藏基因缺陷。；你感到体内有一种隐藏的恶念正在成长。；你体内的恶念增长了。；你不再感到体内有恶念。；你基因的恶念减弱了。 | 2 级；weight 4；flags mutflag::bad；说明：当你获得经验时，你身体的隐藏特质会导致新的有害变异。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_DEVOUR_ON_KILL` | current | devour on kill → 击杀吞噬；显示：击杀吞噬；你通过杀戮活物而茁壮成长。；你感到渴望血肉。；你感到不那么渴望血肉了。 | 1 级；weight 0；flags mutflag::good；说明：当你杀死生物时，你有机会吞噬它们的生命力并恢复健康。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_DISTORTION_FIELD` | current | repulsion field → 排斥力场；显示：排斥力场；你被一个温和的排斥场包围。（闪避+2）；你被一个中等的排斥场包围。（闪避+3）；你被一个强大的排斥场包围。（闪避+4，排斥飞弹）；你开始散发出排斥能量。；你的排斥辐射变强了。；你感到不那么排斥他人了。 | 3 级；weight 0；flags mutflag::good；说明：你被排斥力场围绕，这会提供少量闪避。 这个变异每升一级会提供更多闪避。 这个变异达到第三级也会使射向你的远程攻击的命中率减半。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_DISTRIBUTED_TRAINING` | current | distributed training → 分散训练；显示：分散训练；你的经验平均分配于所有技能。；你的经验现在均等地应用于所有技能。；你的经验不再均等地应用于所有技能。 | 1 级；weight 0；flags mutflag::good；说明：无论你何时获得经验，它都会分配到你的所有技能之中。 你无法选择技能进行着重训练。 此效果让你无法训练特定技能，仿佛是神的限制，不会让你的其他技… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_DIVINE_ATTRS` | current | divine attributes → 神圣属性；显示：神圣属性；你的神圣血统在升级时大幅提升你的属性。；你感到更加神圣。；你感到更加凡俗。 | 1 级；weight 0；flags mutflag::good；说明：当你与其他物种相比，无论是在数值还是在发育程度的掌控上， 神圣属性都显著提升了你的属性增益（力量、智力和敏捷）。 每过三级，你可以选一个属性，… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_DOPEY` | current | dopey → 愚钝；显示：愚钝；你很迟钝。（智力-3）；你非常迟钝。（智力-6） | 2 级；weight 8；flags mutflag::bad；说明：你的心智变得异常愚钝。这个变异每升一级会减3点智力。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_DOUBLE_POTION_HEAL` | current | double potion healing → 双倍药水治疗；显示：双倍药水治疗；你从药水中获得双倍的治疗和魔力恢复。；你从药水中获得的治疗量翻倍了。；你不再从药水中获得双倍治疗。 | 1 级；weight 0；flags mutflag::good；说明：每当药水恢复你的生命值或法力时，其恢复量是原先的两倍。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_DRUNKEN_BRAWLING` | current | drunken brawling → 醉拳；显示：醉拳；每当你饮用治疗药水时，你会攻击周围的所有敌人。；你每次喝治疗药水都会引发斗殴。；你不再因喝治疗药水而斗殴。 | 1 级；weight 0；flags mutflag::good；说明：当你喝下恢复健康或法力的药水时，你会立即攻击附近的所有敌人。 （这包括治疗、愈伤、法力和琼浆药水。） | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_EFFICIENT_MAGIC` | current | efficient magic → 高效魔法；显示：高效魔法；你施放的法术消耗减少1点魔力（最低为1）。；你施放的法术消耗减少2点魔力（最低为1）。；你获得了对魔法流动的新掌控。；你对魔法流动的掌控增强了。；魔法的流动从你的掌控中滑落了。；魔法的流动开始从你的掌控中滑落。 | 2 级；weight 4；flags mutflag::good；说明：你天生理解并能更精确地掌控法力流动，因此施法效率更高。 这个变异每升一级会使法术消耗减少 1 点法力，最低仍为 1 点法力。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_EFFICIENT_METABOLISM` | current | efficient metabolism → 高效代谢；显示：高效代谢；你的新陈代谢使药水状态效果持续时间翻倍。；你的身体翻腾，使你异常干渴。；你的身体翻腾，使你异常解渴。 | 1 级；weight 3；flags mutflag::good；说明：你改变后的消化系统能从特定种类的药水中汲取额外效力， 使通过药水获得的所有状态效果持续时间翻倍。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_EPHEMERAL_SHIELD` | current | ephemeral shield → 短暂护盾；显示：短暂护盾；当你施放法术或使用祈祷时，周围会形成一个护盾。（盾挡+7）；周围的过剩能量开始聚集在你身边。；你周围的过剩能量消散了。 | 1 级；weight 4；flags mutflag::good；说明：每当你使用有消耗的法术或神圣能力时，逸散的魔法或精神能量都会形成盾牌保护你。 法术产生的魔法能量只能维持盾牌片刻，而使用神圣能力产生的精神能量… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_EVOLUTION` | current | evolution → 进化；显示：进化；你拥有隐藏的基因潜力。；你拥有巨大的隐藏基因潜力。；你感到体内有一种隐藏的潜能正在成长。；你隐藏的基因潜能增长了。；你不再感到体内有隐藏的潜能。；你隐藏的基因潜能衰退了。 | 2 级；weight 4；flags mutflag::good；说明：当你获得经验时，你身体的隐藏特质会导致新的有益变异。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_EXPLORE_REGEN` | current | explore regen → 探索再生；显示：探索再生；你在探索时恢复生命和魔力。；你感到强烈的漫游欲望。；你感到恋家。 | 1 级；weight 0；flags mutflag::good；说明：探索未知会让你精神振奋。当你探索地牢时，你的伤口会愈合，你的法力会恢复。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_EYEBALLS` | current | eyeballs → 眼球；显示：眼球；你的身体长出了可能迷惑攻击者的眼睛。（精准+3）；你的身体长出了许多可能迷惑攻击者的眼睛。（精准+5）；你的身体遍布可能迷惑攻击者的眼睛。（精准+7，看破隐形）；眼球从你身体的部分部位长出。；眼球覆盖了你身体的大部分。；眼球完全覆盖了你。；你身体上的眼球消失了。；你身体上的眼球有所消退。 | 3 级；weight 0；flags mutflag::good ／ mutflag::ji…；说明：金色的眼球像蘑菇一样从你的肉里长出来，能够混乱你的敌人。 这个变异每升一级，就能提升你的武器、徒手攻击、辅助攻击和法术的命中率。 这个变异达到… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_FAITH` | current | faith → 信仰；显示：信仰；你与神圣有特殊的联系。（信仰）；你感到与某种比你更伟大的存在相连。；你感到叛逆。 | 1 级；weight 0；flags mutflag::good；说明：你被熏了圣油和圣香料，被蒙福的布裹着。 现在你与神有一种特殊的联系，你会更快被你皈依的神所赏识。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_FANGS` | current | fangs → 尖牙；显示：尖牙；你有非常锋利的牙齿。；你有极其锋利的牙齿。；你有剃刀般锋利的牙齿。；你的牙齿变长变锋利了。；你的牙齿又变长变锋利了一些。；你的牙齿长得极长且锋利如刀。；你的牙齿缩回了正常大小。；你的牙齿缩小且变钝了。 | 3 级；weight 1；flags mutflag::good ／ mutflag::an…；说明：你长出锋利的牙齿，在近战时能够撕咬敌人。 这个变异每升一级，你的牙齿就会更尖、更长、更强。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_FAST` | current | speed → 疾速；显示：疾速；你以超自然的速度移动。（速度+）；你以非常超自然的速度移动。（速度++）；你以极其超自然的速度移动。（速度+++）；你感到敏捷。；你感觉迟缓。 | 3 级；weight 0；flags mutflag::good；说明：你行进得很快——移动到新位置所需的时间会更短。它对其他类型的动作没有影响， 比如攻击或施法。这个变异每升一级，你移动得会更快。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_FEED_OFF_SUFFERING` | current | feed off suffering → 以痛苦为食；显示：以痛苦为食；你有时可以通过杀死中毒或虚弱的敌人获得力量。；你经常可以通过杀死中毒或虚弱的敌人获得力量。；邪恶的能量愉快地在你灵魂中回旋。；邪恶的能量在你灵魂中回旋得更加猛烈。；在你灵魂中回旋的邪恶能量消散了。；在你灵魂中回旋的邪恶能量减弱了。 | 2 级；weight 4；flags mutflag::good；说明：一股邪恶却振奋人心的能量弥漫在你的灵魂中，与死亡瞬间释放的某些能量产生共鸣。 每当中毒或被汲取的敌人在你视野内死亡时，你有概率吸取其少量生命力… | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_FLAME_CLOUD_IMMUNITY` | current | flame cloud immunity → 火焰云免疫；显示：火焰云免疫；你对火焰云免疫。；你感到不那么受高温影响了。 | 1 级；weight 0；flags mutflag::good；说明：你免疫火焰云。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_FLAT_HP` | current | extra vitality → 额外活力；显示：额外活力；你拥有出众的活力。（+4最大生命）；你拥有非常出众的活力。（+8最大生命）；你拥有异常出众的活力。（+12最大生命）；你感到更有活力。；你感到活力不足。 | 3 级；weight 0；flags mutflag::good；说明：你的身体结构与大多数物种不同，这让你略难被杀死。 这个变异每升一级，你的生命值上限就会增加4点。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_FLOAT` | current | float → 漂浮；显示：漂浮；你在空中漂浮，而非行走。；你感到既失重又失腿。；你感到世界的重负将你向下拖拽。 | 1 级；weight 0；flags mutflag::good；说明：你在空中悬浮，永远摆脱了大地的束缚。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_FORLORN` | current | forlorn → 凄凉；显示：凄凉；你将自己置于神之前。；你感到孤苦。；你感到更加灵性。 | 1 级；weight 0；flags mutflag::bad；说明：你不能、不会、也永远无法皈依任何神。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_FORMLESS` | current | formless → 无形；显示：无形；你最多可以装备6件辅助护甲任意组合。；你最多可以装备6件辅助护甲任意组合并释放它们。；你感到准备好释放真正的刺耳之音。；你将能够发动装备的护甲。 | 2 级；weight 0；flags mutflag::good；说明：你没有实体，而是通过附身物品与世界互动。因此，你可以用任意组合“装备”最多 6 件 靴子、手套、斗篷或头盔，但身体护甲太大，无法以这种方式有效… | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_FOUL_SHADOW` | current | foul shadow → 污秽之影；显示：污秽之影；你被淡淡的阴影笼罩，在近战受伤时极少释放污秽火焰。；你被阴影笼罩，在近战受伤时有时会释放污秽火焰。；你被深沉的阴影笼罩，在近战受伤时经常会释放污秽火焰。；你的身体因邪恶火焰而变暗。；你的身体因邪恶火焰而变得更暗。；你身体的暗色完全褪去了。；你身体的暗色褪去了。 | 3 级；weight 0；flags mutflag::good；说明：你的身体笼罩着污秽之焰。敌人更难命中你，你的潜行也大幅增强。 近战攻击你的敌人有时会被污秽之焰灼烧；亡灵和恶魔受到的伤害较少， 神圣生物和善神… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_FOUL_STENCH` | current | foul stench → 恶臭；显示：恶臭；你在近战受伤时可能极少散发出恶臭的瘴气。；你在近战受伤时有时会散发出恶臭的瘴气。；你在近战受伤时经常会散发出恶臭的瘴气。；你开始散发腐败与朽烂的恶臭。；你的恶臭变得更加强烈。；你开始散发瘴气。 | 3 级；weight 0；flags mutflag::good；说明：敌人的近战攻击有时会让你发出一团恶臭的瘴气， 卷入其中的怪物会变慢并受到严重毒害。 这个变异还能让你对（任何来源的）瘴气免疫。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_FRAIL` | current | frail → 脆弱；显示：脆弱；你很脆弱。（-10%生命）；你非常脆弱。（-20%生命）；你极其脆弱。（-30%生命）；你感到脆弱。；你感到强健。 | 3 级；weight 10；flags mutflag::bad；说明：你的健康状况很差。这个变异每升一级，你的健康状况会恶化（-10%生命值）。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_FREEZING_CLOUD_IMMUNITY` | current | freezing cloud immunity → 冰冻云免疫；显示：冰冻云免疫；你对冰冻云免疫。；你感到不那么受寒冷影响了。 | 1 级；weight 0；flags mutflag::good；说明：你免疫冰汽云。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_FROG_LEGS` | current | frog-like legs → 蛙腿；显示：蛙腿；你可以短距离跳跃，但移动缓慢。；你可以长距离跳跃，但移动缓慢。；你的双腿感到更强壮了。 | 2 级；weight 0；flags mutflag::good ／ mutflag::an…；说明：你异常强健的双腿让你可以用 <input>$cmd[CMD_USE_ABILITY]</input> 在眨眼间跳过短距离， 但步行速度低于平均… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_GELATINOUS_BODY` | current | gelatinous body → 凝胶身体；显示：凝胶身体；你橡胶般的身体吸收攻击。（防御+1，闪避+1）；你柔韧的身体吸收攻击。（防御+2，闪避+2）；你凝胶般的身体偏转攻击。（防御+3，闪避+3）；你的身体变得有弹性。；你的身体变得更加可塑。；你的身体变得粘稠。；你的身体恢复了正常的质地。；你的身体不那么可塑了。；你的身体不那么粘稠了。 | 3 级；weight 0；flags mutflag::good ／ mutflag::ji…；说明：你的身体富有弹性，你的敌人就像胶水。这个变异每升一级会加1点防护和1点闪避。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_HEAT_RESISTANCE` | current | fire resistance → 火焰抗性；显示：火焰抗性；你耐热。（火抗+）；你非常耐热。（火抗++）；你几乎对火焰效果免疫。（火抗+++）；你感到对高温有抗性。；你感到对高温的抗性增强了。；你不再感到对高温有抗性。；你感到对高温的抗性减弱了。 | 3 级；weight 4；flags mutflag::good ／ mutflag::su…；说明：你抵抗热。这个变异每升一级，就会削弱火对你造成的伤害。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_HEAT_VULNERABILITY` | current | heat vulnerability → 炎热弱点；显示：炎热弱点；你怕热。（火抗-）；你非常怕热。（火抗--）；你极其怕热。（火抗---）；你感到易受高温伤害。；你不再感到易受高温伤害。；你感到对高温的脆弱减轻了。 | 3 级；weight 3；flags mutflag::bad ／ mutflag::sub…；说明：火很容易对你造成伤害，并会对你造成更多伤害。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_HEX_ENHANCER` | current | bedevilling → 纠缠；显示：纠缠；你的诅咒更加强大。；你感到如恶魔般。 | 1 级；weight 0；flags mutflag::good；说明：你施放的诅咒系法术威力增强。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_HIGH_MAGIC` | current | high MP → 高魔力；显示：高魔力；你的魔力储备增加。（+10%魔力）；你的魔力储备大幅增加。（+20%魔力）；你的魔力储备极大增加。（+30%魔力）；你感到精力充沛。；你感到精力不足。 | 3 级；weight 2；flags mutflag::good；说明：你的法力储备会增加。这个变异每升一级会使法力上限提高 10%。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_HOOVES` | current | hooves → 蹄；显示：蹄；你有大型分趾蹄。；你有蹄状脚。；你的脚变成了蹄子。；你的双脚变厚变形了。；你的双脚变异成了蹄子。；你的蹄子扩展长成了脚！；你的蹄子看起来更像脚了。 | 3 级；weight 5；flags mutflag::good ／ mutflag::an…；说明：你长出蹄子，如果不穿靴子，在近战时能够踢击敌人。这个变异每升一级， 你的蹄子就会更硬、更强。这个变异达到第三级，你将无法穿靴子。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_HORNS` | current | horns → 角；显示：角；你头上有一对小角。；你头上有一对角。；你头上有一对大角。；一对角从你的头上长了出来！；你头上的角又长大了一些。；你头上的角缩没了。；你头上的角缩小了一些。 | 3 级；weight 7；flags mutflag::good ／ mutflag::an…；说明：你的头上长出角，在近战时会尝试顶伤敌人，但无法戴头盔。这个变异每升一级， 就会增加你顶撞的攻击力。这个变异达到第三级，你将无法戴任何帽子。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_HP_CASTING` | current | HP casting → 生命施法；显示：生命施法；你的魔力就是你的生命精华。；你的魔力和生命融合在了一起。；你的生命与法力不再相连。 | 1 级；weight 0；flags mutflag::good；说明：你没有独立的法力储备，任何会影响法力的效果都将对你失效。 当施展法术、使用能力或做任何对其他物种来说需要花费法力的事时， 你将转而消耗生命值。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_HURL_DAMNATION` | current | hurl damnation → 投掷天谴；显示：投掷天谴；你可以投掷诅咒之火。；你闻到一丝硫磺味。 | 1 级；weight 0；flags mutflag::good；说明：你可以通过<input>$cmd[CMD_USE_ABILITY]</input>发动天遣。敌人们可要当心了！ | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_ICEMAIL` | current | icemail → 冰甲；显示：冰甲；一层可融化的冰封包裹保护你免受伤害。（防御+；一层厚实可融化的冰封包裹保护你免受伤害。（防御+；一层冰霜外壳在你周围形成。；你的冰霜外壳变厚了。 | 2 级；weight 0；flags mutflag::good；说明：你身上覆盖着一层起保护作用的冰。火焰攻击能暂时融化冰层， 在冰层重新形成之前会消除保护。这个变异每升一级，就会提升获得的保护。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_ICY_BLUE_SCALES` | current | icy blue scales → 冰蓝鳞片；显示：冰蓝鳞片；你部分覆盖着冰蓝鳞片。（防御+2）；你大部分覆盖着冰蓝鳞片。（防御+3）；你完全覆盖着冰蓝鳞片。（防御+4，冰抗+）；冰蓝色的鳞片覆盖了你身体的一部分。；冰蓝色的鳞片蔓延到你身体的更多部位。；冰蓝色的鳞片完全覆盖了你的身体。；你冰蓝色的鳞片消失了。；你冰蓝色的鳞片有所消退。 | 3 级；weight 0；flags mutflag::good ／ mutflag::su…；说明：你被蓝色鳞片覆盖，这会提供少量保护。这个变异每升一级会提供更多防护。 这个变异达到第三级会提供寒抗。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_IGNITE_BLOOD` | current | ignite blood → 点燃血液；显示：点燃血液；你的恶魔光环有时会让流出的血液燃烧起来。；你的恶魔光环经常会让流出的血液燃烧起来。；你的恶魔光环会让所有流出的血液燃烧起来。；你的血液升温了。；你的血液变得炽热！；你的血液燃烧得更加炽热！ | 3 级；weight 0；flags mutflag::good；说明：每当你看到（你的或他人的）飞溅的血液，它可能会燃烧，爆发成火焰云。 这个变异每升一级，这种可能性就越大。这个变异还能让你免疫火焰云。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_INEXPERIENCED` | current | inexperienced → 经验不足；显示：经验不足；你有些缺乏经验。（-1级）；你缺乏经验。（-2级）；你极其缺乏经验。（-3级）；你感到经验不足。；你恢复了全部潜能。；你恢复了一些潜能。 | 3 级；weight 0；flags mutflag::bad；说明：你缺乏经验，无法完全升到27级。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_INHIBITED_REGENERATION` | current | inhibited regeneration → 再生抑制；显示：再生抑制；当怪物在视野中时你无法再生。；你在怪物附近时停止了再生。；无论附近是否有怪物，你都开始再生了。 | 1 级；weight 3；flags mutflag::bad；说明：当敌人出现时，你不会随着时间推移而痊愈。其他治疗来源，如药水，不受此影响。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_INITIALLY_ATTRACTIVE` | current | initially attractive → 初始吸引力；显示：初始吸引力；你有时将新看到的生物拉向你。；你经常将新看到的生物拉向你。；你感到有种奇特的魅力。；你感到更加有魅力。；你感到不那么有魅力了。；你感到魅力减退了。 | 2 级；weight 4；flags mutflag::bad；说明：当你第一次看到某只怪物时，它可能会被魔法拉向你。 这有概率惊醒沉睡的怪物，但它们不一定会察觉你的位置。 这个变异达到第二级后，触发概率会提高。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_INNATE_CASTER` | current | innate caster → 天生施法者；显示：天生施法者；你自然地学习法术，不需要书籍。；你感到神秘力量在体内涌起。；你开始更加尊重书本知识。 | 1 级；weight 0；flags mutflag::good；说明：你无法从书本习得法术。取而代之的是，随着你经验的增加， 越来越高级的法术从你炽热的内心中涌现。 这些法术是不可预知的，且不受你皈依的神影响。 … | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_INVIOLATE_MAGIC` | current | inviolate magic → 不可侵犯魔法；显示：不可侵犯魔法；你的魔法力量和效果能够抵抗干扰。；你的魔力变得能够抵御干扰。；你的魔力失去了抵御干扰的能力。；你的魔力将会变得能够抵御干扰。 | 1 级；weight 0；flags mutflag::good；说明：你的魔法能抵抗外力干扰。敌对效果对你汲取的法力只有正常的三分之一， 而且除你自己以外，任何人都无法移除你的魔法效果。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_IRIDESCENT_SCALES` | current | iridescent scales → 虹彩鳞片；显示：虹彩鳞片；你部分覆盖着虹彩鳞片。（防御+2）；你大部分覆盖着虹彩鳞片。（防御+4）；你完全覆盖着虹彩鳞片。（防御+6）；虹彩色的鳞片覆盖了你身体的一部分。；虹彩色的鳞片蔓延到你身体的更多部位。；虹彩色的鳞片完全覆盖了你的身体。；你虹彩色的鳞片消失了。；你虹彩色的鳞片有所消退。 | 3 级；weight 10；flags mutflag::good ／ mutflag::su…；说明：你被彩色鳞片覆盖，这会提供少量保护。这个变异每升一级会加2点防护。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_IRON_FUSED_SCALES` | current | iron-fused scales → 铁融鳞片；显示：铁融鳞片；你的鳞片与铁融合。（防御+5）；铁质融入了你的鳞片。；铁质从你的鳞片上剥落了。；铁质将融入你的鳞片。（AC + 5） | 1 级；weight 0；flags mutflag::good ／ mutflag::an…；说明：你的鳞片与厚重铁层融合，坚韧程度如同一套护甲（AC +5）。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_JELLY_GROWTH` | current | jelly sensing items → 果冻感知物品；显示：果冻感知物品；你身上附着一个小果冻，能够感知附近的物品。；你的身体部分分裂成一个小凝胶体。；凝胶增生被你的身体重新吸收了。 | 1 级；weight 0；flags mutflag::good ／ mutflag::ji…；说明：你身上附有一个小胶冻，它可以感知周围物品。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_JELLY_MISSILE` | current | jelly absorbing missiles → 果冻吸收飞弹；显示：果冻吸收飞弹；你身上附着一个小果冻，可能吸收飞弹。；你的身体部分分裂成一个小凝胶体。；凝胶增生被你的身体重新吸收了。 | 1 级；weight 0；flags mutflag::good ／ mutflag::ji…；说明：当你被飞弹击中时（比如箭或弩箭），你身上的胶冻可能会吞掉它，并进行一定治疗。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_LARGE_BONE_PLATES` | current | large bone plates → 大型骨板；显示：大型骨板；你部分覆盖着大型骨板。（盾挡+4）；你大部分覆盖着大型骨板。（盾挡+6）；你完全覆盖着大型骨板。（盾挡+8）；巨大的骨板覆盖了你的手臂。；巨大的骨板蔓延到你手臂的更多部位。；巨大的骨板完全覆盖了你的手臂。；你巨大的骨板消失了。；你巨大的骨板有所消退。 | 3 级；weight 2；flags mutflag::good ／ mutflag::su…；说明：你被大骨板保护着，这会提供少量格挡。这个变异每升一级会提供更多格挡。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_LOW_MAGIC` | current | low MP → 低魔力；显示：低魔力；你的魔力容量较低。（-10%魔力）；你的魔力容量很低。（-20%魔力）；你的魔力容量极低。（-30%魔力）；你感到精力不足。；你感到精力充沛。 | 3 级；weight 9；flags mutflag::bad；说明：你的法力容量较低。这个变异每升一级会使法力上限降低 10%。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_LUCKY` | current | lucky → 幸运；显示：幸运；你发现的神器略微增多。；你发现的神器增多。；你感到幸运之神的眷顾。；你感到幸运之神更加明亮地眷顾着你。；你感到好运已经用尽。；你感到运气变差了。 | 2 级；weight 4；flags mutflag::good；说明：你有一种不可思议的直觉，能发现别人可能当作凡品忽略的物品的隐藏属性。 每当你第一次遇到地上的新物品时，都有极小概率发现它其实是神器。 这个变异… | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_MAKHLEB_DESTRUCTION_COC` | current | Cocytus destruction → 科塞特斯毁灭；显示：科塞特斯毁灭；你从科塞特斯的冰冷荒原中汲取毁灭之力。；你感到灵魂因科赛特斯的严寒毁灭而变冷。 | 1 级；weight 0；flags mutflag::good；说明：你的释放毁灭能力被冰狱强化。你能够投掷寒冰束而不是火焰， 你的寒冷束将受害者冻结成固体，减慢其移动。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_MAKHLEB_DESTRUCTION_DIS` | current | Dis destruction → 迪斯毁灭；显示：迪斯毁灭；你从迪斯的无情怨恨中汲取毁灭之力。；你感到灵魂因狄斯的腐蚀毁灭而变苦。 | 1 级；weight 0；flags mutflag::good；说明：你的释放毁灭能力被铁城强化。你能够投掷腐蚀性酸液束和金属碎片束 而不是负能量。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_MAKHLEB_DESTRUCTION_GEH` | current | Gehenna destruction → 基希纳毁灭；显示：基希纳毁灭；你从基希纳的无尽火焰中汲取毁灭之力。；你感到灵魂因基赫纳的烈焰毁灭而变热。 | 1 级；weight 0；flags mutflag::good；说明：你的释放毁灭能力被火焚地狱强化。你能够投掷岩浆束而不是寒冷， 你的火焰束可以剥离受害者的火焰抗性。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_MAKHLEB_DESTRUCTION_TAR` | current | Tartarus destruction → 塔耳塔洛斯毁灭；显示：塔耳塔洛斯毁灭；你从塔耳塔洛斯的哀嚎悲伤中汲取毁灭之力。；你感到灵魂因塔塔罗斯的死亡毁灭而变得污浊。 | 1 级；weight 0；flags mutflag::good；说明：你的释放毁灭能力被悲叹地狱强化。你能够投掷毁灭束而不是闪电， 它会降低受害者的意志力，且你的负能量束更加强大。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_MAKHLEB_MARK_ANNIHILATION` | current | Mark of Annihilation → 湮灭印记；显示：湮灭印记；你携带着湮灭印记。；你感到体内的毁灭能量猛烈涌动。 | 1 级；weight 0；flags mutflag::makhleb；说明：你的地狱仆从能力被替换为湮灭之球，允许你投掷缓慢移动的强烈毁灭力球体， 它们会以你特征性的毁灭能量引爆为巨大的爆炸。 （你的湮灭之球释放{{ … | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_MAKHLEB_MARK_ATROCITY` | current | Mark of Atrocity → 暴行印记；显示：暴行印记；你携带着暴行印记。；你将净化这个世界。 | 1 级；weight 0；flags mutflag::makhleb；说明：你的释放毁灭在连续使用不中断时会变得更加强大，伤害和生命消耗都会增加。 连续使用第四次时，你将自动向随机目标释放一阵狂野的额外弩箭齐射， 并重… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_MAKHLEB_MARK_CARNAGE` | current | Mark of Carnage → 杀戮印记；显示：杀戮印记；你携带着杀戮印记。；你的仆从们渴望释放毁灭。 | 1 级；weight 0；flags mutflag::makhleb；说明：你的地狱仆从现在被召唤到随机敌人旁边而不是你附近。当它们出现时， 它们会以你特征性的毁灭能量爆发出现（不会伤害你或其他盟友）。 （你的仆从释放… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_MAKHLEB_MARK_CELEBRANT` | current | Mark of the Celebrant → 颂礼者印记；显示：颂礼者印记；你携带着颂礼者印记。；你的苦难将以鲜血偿还。 | 1 级；weight 0；flags mutflag::makhleb；说明：每当你的生命值降至最大生命值的50%以下时，你进行一次地狱仪式， 向附近的敌人释放一阵血箭齐射。你将为每个有效目标至少射出一支箭， 但如果目标… | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_MAKHLEB_MARK_EXECUTION` | current | Mark of Execution → 处决印记；显示：处决印记；你携带着处决印记。；杀戮在你灵魂中扎下了根。 | 1 级；weight 0；flags mutflag::makhleb；说明：一个谋杀之恶魔化身潜伏在你的灵魂中。每当你用近战击杀一个敌人时， 有很小概率它会醒来并显现为包围你的镰刀刀锋漩涡。这些刀锋会在你 攻击时一起攻… | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_MAKHLEB_MARK_FANATIC` | current | Mark of the Fanatic → 狂热者印记；显示：狂热者印记；你携带着狂热者印记。；你将成为马科列布意志的工具。 | 1 级；weight 0；flags mutflag::makhleb；说明：赋予你杀戮化身能力，允许你在短时间内变身为一个强大的恶魔化身， 大幅提升攻击和防御，代价是之后被拖入血肉熔炉并被迫为自由而战。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_MAKHLEB_MARK_HAEMOCLASM` | current | Mark of Haemoclasm → 血破印记；显示：血破印记；你携带着血破印记。；血雨将降在你敌人头上。 | 1 级；weight 0；flags mutflag::makhleb；说明：当你击杀敌人时，它们有很小概率爆炸为一阵猛烈的血雨，对相邻的敌人造成 与受害者最大生命值成比例的伤害。 死于这种爆炸的敌人自身也总是会爆炸。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_MAKHLEB_MARK_LEGION` | current | Mark of the Legion → 军团印记；显示：军团印记；你携带着军团印记。；混沌大军现在由你统领。 | 1 级；weight 0；flags mutflag::makhleb；说明：你的地狱仆从能力被替换为地狱军团，允许你随时间召唤一小支恶魔军队。 虽然个体存活短暂，但只要状态持续，它们的数量无穷无尽， 并且永远不会对你敌… | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_MAKHLEB_MARK_TYRANT` | current | Mark of the Tyrant → 暴君印记；显示：暴君印记；你携带着暴君印记。；即使是恶魔现在也会在你面前下跪。 | 1 级；weight 0；flags mutflag::makhleb；说明：你的地狱仆从持续时间更长，在非常高的祈神技能下你甚至可以 召唤更强大的仆从（以额外的虔诚值为代价）。当你杀死敌人时， 一个随机仆从可能获得以下… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_MANA_LINK` | current | magic link → 魔力链接；显示：魔力链接；当魔力不足时，你以消耗生命为代价恢复魔力。；你感到生命力和魔法精华融合了。 | 1 级；weight 0；flags mutflag::good；说明：当法力不足时，你会恢复法力而不是生命值。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_MANA_REGENERATION` | current | magic regeneration → 法力再生；显示：法力再生；你快速恢复魔力。；你的魔力开始快速再生。 | 1 级；weight 0；flags mutflag::good；说明：你的法力储备的恢复速度变快。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_MANA_SHIELD` | current | magic shield → 魔法护盾；显示：魔法护盾；受伤时，伤害在你的生命和魔力储备之间分摊。；你感到魔法精华在你的肉体周围形成了一层保护罩。 | 1 级；weight 0；flags mutflag::good；说明：当你受到伤害时，一些伤害会转而消耗你的法力储备。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_MEEK` | current | meek → 懦弱；显示：懦弱；你的攻击效果略微降低。（杀戮-3）；你的攻击效果降低。（杀戮-5）；你的攻击效果大幅降低。（杀戮-7）；你感到温顺。；你感到更加温顺。；你感到如羔羊般温顺。；你感到攻击性回归了。；你感到不那么温顺了。 | 3 级；weight 3；flags mutflag::bad；说明：你的所有攻击都会变弱，伤害降低，命中率也会略微下降。 这个变异每升一级，负面效果都会加重。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_MERTAIL` | current | mertail → 人鱼尾；显示：人鱼尾；在水中你的下半身会变成一条强大的水生尾巴。；你的双腿感到适应水栖。；你的双腿不再适应水中生活。 | 1 级；weight 0；flags mutflag::good ／ mutflag::an…；说明：你的基体形态不稳定，当你在浅水或深水中， 你的下半身会变成强有力的水生生物的尾巴。一旦你离开水面，它会很快变成腿。 处于人鱼形态时，你的尾巴在… | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_MISSING_EYE` | current | missing an eye → 缺失一只眼；显示：缺失一只眼；你缺少一只眼睛，瞄准更加困难。；你的右眼消失了！世界失去了深度感。；你的右眼突然重新出现了！世界恢复了深度感。 | 1 级；weight 0；flags mutflag::bad；说明：你失去了一只眼睛，降低了你的物理和魔法攻击的命中率。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_MISSING_HAND` | current | missing a hand → 缺失一只手；显示：缺失一只手；你缺少一只手。；你的一只手消失了，只剩下一个残桩！；你的残桩重新长成了一只手！ | 1 级；weight 0；flags mutflag::bad；说明：你的手要比以前不方便得多。 你不能使用双手武器、装备盾牌、发动副手攻击或一次使用多个魔法戒指。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_MNEMOPHAGE` | current | mnemnophage → 噬忆；显示：噬忆；你可以通过燃烧收集的记忆来增强你的伤害法术。；你的火焰饥渴地闪烁着。；你的火焰变得不那么贪婪了。；你将能够燃烧记忆来强化伤害类法术。 | 1 级；weight 0；flags mutflag::good；说明：你吞噬被你杀死者的记忆乃至存在本身，将其融入环绕身体的不洁火焰。 积累足够记忆后，你可以选择将其全部燃烧为燃料，短时间内大幅增强施法能力。 以… | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_MOLTEN_SCALES` | current | molten scales → 熔融鳞片；显示：熔融鳞片；你部分覆盖着熔岩鳞片。（防御+2）；你大部分覆盖着熔岩鳞片。（防御+3）；你完全覆盖着熔岩鳞片。（防御+4，火抗+）；熔岩般的鳞片覆盖了你身体的一部分。；熔岩般的鳞片蔓延到你身体的更多部位。；熔岩般的鳞片完全覆盖了你的身体。；你熔岩般的鳞片消失了。；你熔岩般的鳞片有所消退。 | 3 级；weight 0；flags mutflag::good ／ mutflag::su…；说明：你被熔融的鳞片覆盖，这会提供少量保护。这个变异每升一级会提供更多防护。 这个变异达到第三级会提供火抗。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_MP_WANDS` | current | MP-powered wands → 魔杖消耗魔力；显示：魔杖消耗魔力；你消耗魔力（3点）来增强你的魔杖。；你感到魔法精华与地牢的魔杖链接了。；你的魔法精华不再与地牢的魔杖链接。 | 1 级；weight 7；flags mutflag::good；说明：你的魔杖会汲取你的法力，在这个过程中会变得更强大。 如果你没有法力了，你的魔杖的效果会恢复正常。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_MULTILIVED` | current | multi-lived → 多条命；显示：多条命；你每三级获得一条额外生命。；你不再是多重生命了。；你现在可以获得额外生命。 | 1 级；weight 0；flags mutflag::good；说明：每过三级，你将获得额外的生命。 如果你被杀的时候还有一条命，你会在当前楼层的其他地方重新出现。 即使你达到了最高的经验等级，你也可以继续获得额… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_MUTATION_RESISTANCE` | current | mutation resistance → 变异抗性；显示：变异抗性；你对进一步变异有一定抗性。；你对进一步变异和变异移除都有一定抗性。；你几乎完全抵抗进一步变异和变异移除。；你感到基因稳定。；你感到基因不可改变。；你感到基因不稳定。 | 3 级；weight 4；flags mutflag::good；说明：你的遗传密码出奇地稳定，使你不太可能发生变异（或消除现有变异）。 这个变异每升一级，你就会有更强的抵抗力。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_NECRO_ENHANCER` | current | in touch with death → 与死亡接触；显示：与死亡接触；你与死亡的力量相通。；你与死亡的力量深度相通。；你感到与死亡之力更加紧密相连。 | 2 级；weight 0；flags mutflag::good；说明：你的死灵法术变得更为强大。这个变异达到第二级，就会增强你的死灵术的法术威力。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_NEGATIVE_ENERGY_RESISTANCE` | current | negative energy resistance → 负能量抗性；显示：负能量抗性；你抵抗负能量。（负抗+）；你相当抵抗负能量。（负抗++）；你对负能量免疫。（负抗+++）；你感到对负能量有抗性。；你感到对负能量的抗性增强了。 | 3 级；weight 0；flags mutflag::good ／ mutflag::su…；说明：你抵抗负能量。 这个变异每升一级，就会减小负能量对你造成的伤害和从你身上汲取的生命值。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_NIGHTSTALKER` | current | nightstalker → 夜行者；显示：夜行者；你与暗影的同调略微增强。；你与暗影的同调显著增强。；你完全与暗影同调。；你滑入了地牢的黑暗之中。；你更深地滑入了黑暗之中。；你被黑暗包围。；你对黑暗的亲和力消失了。；你对黑暗的亲和力减弱了。 | 3 级；weight 0；flags mutflag::good；说明：你适应了阴影，减小了你能看到和被看到的距离。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_NIMBLE_SWIMMER` | current | nimble swimmer → 敏捷游泳者；显示：敏捷游泳者；你在水中或水上时获得伪装。（潜行+）；你在水中或水上非常灵活。（潜行+，闪避+，速度+++）；你在水边感到舒适。；你在水边感到非常舒适。；你在水边感到不那么舒适了。 | 2 级；weight 0；flags mutflag::good ／ mutflag::an…；说明：你在水中游泳或在水面上飞行时能融入波浪，潜行获得加成。 这个变异达到第二级，还会提升你在水中或水上的闪避能力和移动速度。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_NO_AIR_MAGIC` | current | no air magic → 无法使用空气魔法；显示：无法使用空气魔法；你无法学习或施放空气魔法。；你无法再学习或施放空气魔法。；你可以重新学习和施放空气魔法。 | 1 级；weight 0；flags mutflag::bad；说明：你的空气魔法技能等级为 0，你也无法训练它。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_NO_ALCHEMY_MAGIC` | current | no alchemy magic → 无法使用炼金魔法；显示：无法使用炼金魔法；你无法学习或施放炼金魔法。；你无法再学习或施放炼金魔法。；你可以重新学习和施放炼金魔法。 | 1 级；weight 0；flags mutflag::bad；说明：你的炼金术技能等级为0，你也无法训练它。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_NO_ARMOUR` | current | no armour → 无法穿甲；显示：无法穿甲；你无法穿戴护甲。；你无法再穿戴护甲。；你现在可以穿戴护甲了。 | 1 级；weight 0；flags mutflag::bad；说明：你无法穿戴护甲。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_NO_ARMOUR_SKILL` | current | inability to train armour → 无法训练护甲；显示：无法训练护甲；你无法训练护甲技能。；你无法再训练护甲技能。；你可以重新训练护甲技能。 | 1 级；weight 0；flags mutflag::bad；说明：你的护甲技能等级为0，你也无法训练它。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_NO_ARTIFICE` | current | inability to use devices → 无法使用装置；显示：无法使用装置；你无法学习或使用魔法装置。；你无法再学习或使用魔法装置。；你可以重新学习和使用魔法装置。 | 1 级；weight 0；flags mutflag::bad；说明：你无法使用魔法设备。 其中包括魔杖和大多数需要通过<input>$cmd[CMD_EVOKE]</input>激活的物品， 但不包括触及武器、… | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_NO_CONJURATION_MAGIC` | current | no conjurations magic → 无法使用咒法魔法；显示：无法使用咒法魔法；你无法学习或施放咒法魔法。；你无法再学习或施放咒法魔法。；你可以重新学习和施放咒法魔法。 | 1 级；weight 0；flags mutflag::bad；说明：你的咒法系技能等级为 0，你也无法训练它。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_NO_DODGING` | current | inability to train dodging → 无法训练闪避；显示：无法训练闪避；你无法训练闪避技能。；你无法再训练闪避技能。；你可以重新训练闪避技能。 | 1 级；weight 0；flags mutflag::bad；说明：你的闪避技能等级为0，你也无法训练它。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_NO_DRINK` | current | no potions → 无法饮用药水；显示：无法饮用药水；你无法饮用。；你的嘴干如灰烬。；你获得了饮酒的能力。 | 1 级；weight 0；flags mutflag::bad；说明：你无法饮用药水。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_NO_EARTH_MAGIC` | current | no earth magic → 无法使用大地魔法；显示：无法使用大地魔法；你无法学习或施放大地魔法。；你无法再学习或施放大地魔法。；你可以重新学习和施放大地魔法。 | 1 级；weight 0；flags mutflag::bad；说明：你的大地魔法技能等级为 0，你也无法训练它。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_NO_FIRE_MAGIC` | current | no fire magic → 无法使用火焰魔法；显示：无法使用火焰魔法；你无法学习或施放火焰魔法。；你无法再学习或施放火焰魔法。；你可以重新学习和施放火焰魔法。 | 1 级；weight 0；flags mutflag::bad；说明：你的火焰魔法技能等级为 0，你也无法训练它。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_NO_FORGECRAFT_MAGIC` | current | no forgecraft magic → 无法使用锻造魔法；显示：无法使用锻造魔法；你无法学习或施放锻造魔法。；你无法再学习或施放锻造魔法。；你可以重新学习和施放锻造魔法。 | 1 级；weight 0；flags mutflag::bad；说明：你的锻造术技能固定为 0，且无法训练该技能。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_NO_FORMS` | current | no forms → 无法变形；显示：无法变形；你无法自愿改变形态。；你无法再主动变形。；你可以重新变形了。 | 1 级；weight 0；flags mutflag::bad；说明：你无法通过护符、药水或其他任何方式自行改变形态。 但你仍有可能会被变形魔杖等方式不由自主地改变形态。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_NO_GRASPING` | current | no weapons or thrown items → 无法使用武器或投掷物；显示：无法使用武器或投掷物；你无法持握武器或投掷物品。；你无法再抓取物品。；你现在可以抓取物品了。 | 1 级；weight 0；flags mutflag::bad；说明：你无法装备武器或投掷物品。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_NO_HEXES_MAGIC` | current | no hexes magic → 无法使用诅咒魔法；显示：无法使用诅咒魔法；你无法学习或施放诅咒魔法。；你无法再学习或施放诅咒魔法。；你可以重新学习和施放诅咒魔法。 | 1 级；weight 0；flags mutflag::bad；说明：你的诅咒系技能等级为 0，你也无法训练它。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_NO_ICE_MAGIC` | current | no ice magic → 无法使用寒冰魔法；显示：无法使用寒冰魔法；你无法学习或施放寒冰魔法。；你无法再学习或施放寒冰魔法。；你可以重新学习和施放寒冰魔法。 | 1 级；weight 0；flags mutflag::bad；说明：你的寒冰魔法技能等级为 0，你也无法训练它。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_NO_JEWELLERY` | current | no jewellery → 无法佩戴珠宝；显示：无法佩戴珠宝；你无法佩戴戒指或项链。 | 1 级；weight 0；flags mutflag::bad；说明：你无法装备戒指或项链。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_NO_LOVE` | current | hated by all → 被所有生物憎恨；显示：被所有生物憎恨；你被所有生物憎恨。；你现在被所有人憎恨。；你不再被所有人憎恨。 | 1 级；weight 0；flags mutflag::bad；说明：你被所有怪物憎恨，无法以任何方式获得暂时或永久的盟友。 简单、没有意识的魔法造物，比如幽灵武器、毁灭球和作战球则不受此影响。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_NO_NECROMANCY_MAGIC` | current | no necromancy magic → 无法使用死灵魔法；显示：无法使用死灵魔法；你无法学习或施放死灵魔法。；你无法再学习或施放死灵魔法。；你可以重新学习和施放死灵魔法。 | 1 级；weight 0；flags mutflag::bad；说明：你的死灵术技能等级为0，你也无法训练它。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_NO_POTION_HEAL` | current | no potion heal → 无法用药水治疗；显示：无法用药水治疗；药水恢复你生命的效果降低。；药水无法恢复你的生命。；你的身体部分排斥药水的治疗效果。；你的身体完全排斥药水的治疗效果。；你的身体完全接受了药水的治疗效果。；你的身体部分接受了药水的治疗效果。 | 2 级；weight 3；flags mutflag::bad；说明：你的系统会抗拒饮用的灵丹妙药，削弱了各种治疗药水的效果。 这个变异达到第二级，会完全阻断药水的疗效。（哥萨戈神的援助不受影响。） | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_NO_REGENERATION` | current | no regeneration → 无法再生；显示：无法再生；你无法再生。；你停止了再生。；你开始再生。 | 1 级；weight 0；flags mutflag::bad；说明：你在休息时无法恢复健康，也无法获得提升恢复速度的魔法效果。 至于提升生命力的手段，像药水和虔诚的祈祷仍能治疗你， 某些神圣祈祷能力可以短暂赋予… | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_NO_STEALTH` | current | no stealth → 无法潜行；显示：无法潜行；你无法潜行。；你无法再潜行。；你可以重新潜行了。 | 1 级；weight 0；flags mutflag::bad；说明：你无法潜行。 当敌人能看到你时，你总是能引起他们的警觉，并且他们能够轻易追踪你。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_NO_SUMMONING_MAGIC` | current | no summoning magic → 无法使用召唤魔法；显示：无法使用召唤魔法；你无法学习或施放召唤魔法。；你无法再学习或施放召唤魔法。；你可以重新学习和施放召唤魔法。 | 1 级；weight 0；flags mutflag::bad；说明：你的召唤系技能等级为 0，你也无法训练它。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_NO_TRANSLOCATION_MAGIC` | current | no translocations magic → 无法使用位移魔法；显示：无法使用位移魔法；你无法学习或施放位移魔法。；你无法再学习或施放位移魔法。；你可以重新学习和施放位移魔法。 | 1 级；weight 0；flags mutflag::bad；说明：你的传送系技能等级为0，你也无法训练它。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_OOZE_FLOOD` | current | ooze flood → 软泥洪流；显示：软泥洪流；你的近战攻击可能会用软泥淹没你的敌人。；你开始渗出软泥。；你停止了渗出软泥。 | 1 级；weight 0；flags mutflag::good ／ mutflag::ji…；说明：你的近战攻击可能用软泥灌满敌人的呼吸道。需要呼吸空气的敌人会被沉默， 并随时间受到窒息伤害。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_PASSIVE_FREEZE` | current | passive freeze → 被动冻结；显示：被动冻结；一层寒气包裹环绕着你，冻结所有伤害你的人。；你的皮肤感到极寒。；你的皮肤暖和起来了。 | 1 级；weight 1；flags mutflag::good；说明：近战攻击你的敌人会被冻结，并受到伤害。 如果敌人造成了任何伤害，这个效果就必会触发。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_PASSIVE_MAPPING` | current | sense surroundings → 感知环境；显示：感知环境；你被动地绘制周围区域的地图。；你被动地绘制周围大片区域的地图。；你感到与地牢结构有种奇特的调谐。；你与地牢结构的调谐进一步增强了。；你感到有些迷失方向。 | 2 级；weight 3；flags mutflag::good；说明：你对地牢有第二种感知，可以感知到你还没有看到的地形。 这个变异每升一级，你的感知就越来越全面。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_PAWS` | current | stealthy paws → 潜行爪垫；显示：潜行爪垫；你的爪垫帮助你扑向毫无防备的怪物。 | 1 级；weight 0；flags mutflag::good ／ mutflag::an…；说明：当你攻击没有意识或失去行动能力的敌人时，你会造成额外的伤害， 就像人类使用短刀一样。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_PERSISTENT_DRAIN` | current | persistent drain → 持续虚弱；显示：持续虚弱；你被虚弱后生命恢复速度减半。；你开始更慢地从吸取效果中恢复。；你从吸取效果中恢复的速度恢复正常了。 | 1 级；weight 5；flags mutflag::bad；说明：你衰竭后，恢复正常所用的时间是原先的两倍。（所需的总经验值增加了一倍。） | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_PHYSICAL_VULNERABILITY` | current | reduced AC → 降低防御；显示：降低防御；你受到稍微更多的伤害。（防御-5）；你受到更多伤害。（防御-10）；你受到相当多的伤害。（防御-15）；你感到更易受到伤害。；你不再感到特别容易受到伤害。；你感到对伤害的脆弱减轻了。 | 3 级；weight 0；flags mutflag::bad；说明：你很容易受到创伤，你从护甲获得的增益会被削弱。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_POISON_RESISTANCE` | current | poison resistance → 抗毒；显示：抗毒；你对毒素有抗性。（毒抗）；你感到对毒素有抗性。；你感到对毒素的抗性减弱了。 | 1 级；weight 4；flags mutflag::good ／ mutflag::su…；说明：你对毒物、毒素和其他污染物有着抗性。 它不会赋予完全的免疫力，但你中毒的几率会降低到原先的三分之一左右。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_POOR_CONSTITUTION` | current | poor constitution → 体质虚弱；显示：体质虚弱；你的身体有时在受伤后会变得虚弱。；你的身体有时在受伤后会变得虚弱和缓慢。；你感到体质变弱了。；你感到体质变得更加虚弱。；你感到体质恢复了正常。；你感到体质略有改善。 | 2 级；weight 10；flags mutflag::bad；说明：你的身体难以承受伤势；受到伤害时，攻击有概率在短时间内被削弱。 这个变异达到第二级后，有时还会同时使你减速。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_POTION_FUNGUS` | current | potion fungus → 药水真菌；显示：药水真菌；你饮用药水的效果可能会传播到附近的怪物。；一种共生真菌蔓延到你全身。；遍布你全身的真菌枯萎脱落了。 | 1 级；weight 4；flags mutflag::bad；说明：你的身体覆盖着一种真菌，它会代谢你喝下的有益药水，并有时释放孢子， 将这些药水的效果传给附近的怪物——无论敌友。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_POWERED_BY_DEATH` | current | powered by death → 死亡赋能；显示：死亡赋能；你通过击杀恢复少量生命。；你通过击杀恢复生命。；你通过击杀恢复大量生命。；一波死亡之潮席卷了你。；死亡之潮的力量增长了。；你对周围生命力的控制消失了。；你对周围生命力的控制减弱了。 | 3 级；weight 0；flags mutflag::good；说明：死亡滋养着你，你每夺取一条生命，就能得到一定程度的治疗。 这个变异每升一级，治疗效果就会增强。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_POWERED_BY_PAIN` | current | powered by pain → 痛苦赋能；显示：痛苦赋能；你有时通过承受伤害获得少量力量。；你有时通过承受伤害获得力量。；你被痛苦所赋能。；你因痛苦而感到充满能量。；你因痛苦而感到更加充满能量。；你因痛苦而感到完全充满能量。 | 3 级；weight 0；flags mutflag::good；说明：当你受伤时，有时会获得以下一种效果：补充法力储备，或暂时获得敏捷或强效状态。 这个变异每升一级，效果的幅度都会提高。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_PROTEAN_GRACE` | current | protean grace → 百变灵巧；显示：百变灵巧；你被你非先天变异所增强。（+；突变能量在你四肢中涌动。；在你四肢中涌动的突变能量消散了。 | 1 级；weight 2；flags mutflag::good；说明：你的四肢充满了变形之力，引导着你的一举一动。 你拥有的每项其他非先天突变还会提供 +1 闪避和 +1 杀戮加成（上限为 7）， 提高你的近战和… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_PSEUDOPODS` | current | pseudopods → 伪足；显示：伪足；护甲在你的伪足上不合身。；护甲在你较大的伪足上不合身。；护甲在你巨大的伪足上不合身。；伪足从你的身体长出。；你的伪足变大了。；你的伪足缩回了体内。；你的伪足变小了。 | 3 级；weight 0；flags mutflag::good ／ mutflag::ji…；说明：你身上长满了伪足，在近战时能够扫打敌人，但在一定程度上会削弱护甲提供的防护。 这对护甲附魔提供的防护没有影响，也不会影响训练的护甲技能的防御效… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_QUADRUMANOUS` | current | four strong arms → 四条强壮手臂；显示：四条强壮手臂；你的四条强壮手臂可以持盾使用双手武器。；你的两只手臂萎缩消失了。；你长出了两只额外的手臂。 | 1 级；weight 0；flags mutflag::good；说明：你有两对双臂，可以一对手持双手武器，另一对手持盾牌。 你甚至可以挥舞极其巨大的武器，比如大棒，不过这需要两对手臂的配合。 每对手臂的副臂的形状… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_RECKLESS` | current | reckless → 鲁莽；显示：鲁莽；你的盾挡减半，但双手武器造成更多伤害。；你突然不顾自身安全。；你感到不那么鲁莽了。 | 1 级；weight 2；flags mutflag::bad；说明：你的盾牌强度减半，但使用双手近战武器时伤害 +15%。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_REFLEXIVE_HEADBUTT` | current | retaliatory headbutt → 报复性头槌；显示：报复性头槌；你会反射性地用头槌反击近战攻击你的敌人。；你的反击反射感到敏锐。；你的反击反射感到迟钝。 | 1 级；weight 0；flags mutflag::good ／ mutflag::an…；说明：当敌人的近战攻击未命中你时，你可能会本能地反击，尝试用角顶伤攻击者。 每次玩家行动中，对同一个敌人最多只能发动一次这种反击。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_REGENERATION` | current | regeneration → 再生；显示：再生；你的自然恢复速度异常快。；你恢复得非常快。；你具有再生能力。；你开始恢复得更快。；你开始再生。；你的恢复速度变慢。 | 3 级；weight 2；flags mutflag::good；说明：你愈合得很快。这个变异每升一级，就会增加你的愈合速率。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_REMOVED_MUTATION` | internal | Removed Mutation → — | 0 级；weight 0；flags mutflag::good；说明：— | 保留：内部哨兵身份 |
| `mutation:MUT_RENOUNCE_POTIONS` | current | renounce potions → 放弃药水；显示：放弃药水；除非严重受伤，否则你在战斗中拒绝饮用药水。；你放弃了不加节制饮酒的享乐主义。；你再次感到可以随意使用药水。 | 1 级；weight 0；flags mutflag::bad；说明：你拒绝在战斗中饮用药水，除非身受重伤。当敌人处于你的视野中时 （以及之后的数回合内），除非你的生命值低于上限的 50%，否则你无法饮用任何东西。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_RENOUNCE_SCROLLS` | current | renounce scrolls → 放弃卷轴；显示：放弃卷轴；除非严重受伤，否则你在战斗中拒绝阅读卷轴。；你放弃了世俗文字之轻浮。；你又愿意自由使用卷轴了。 | 1 级；weight 0；flags mutflag::bad；说明：你拒绝在战斗中阅读卷轴，除非身受重伤。当敌人处于你的视野中时 （以及之后的数回合内），除非你的生命值低于上限的 50%，否则你无法阅读任何东西。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_ROBUST` | current | robust → 强健；显示：强健；你很健壮。（+10%生命）；你非常健壮。（+20%生命）；你极其健壮。（+30%生命）；你感到强健。；你感到脆弱。 | 3 级；weight 5；flags mutflag::good；说明：你承受得住打击。这个变异每升一级，你的健康状况会改善（+10%生命值）。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_ROLLPAGE` | current | rollpage → 翻滚冲锋；显示：翻滚冲锋；你向敌人翻滚时会恢复法力。（冲锋法力再生）；你向敌人翻滚时会恢复法力和生命。（冲锋再生）；你向敌人翻滚时开始恢复魔力。；你向敌人翻滚时开始恢复生命。；你无法再向敌人翻滚。；你不再能通过向敌人翻滚恢复生命。 | 2 级；weight 0；flags mutflag::good；说明：当你移向敌人时会本能地翻滚，会向前再冲出一格。 这个变异能在你滚动时提升法力恢复速度； 这个变异达到第二级，法力和生命值的恢复速度会同时提升。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_RUGGED_BROWN_SCALES` | current | rugged brown scales → 粗糙褐鳞；显示：粗糙褐鳞；你部分覆盖着粗糙棕鳞。（防御+1，+3%生命）；你大部分覆盖着粗糙棕鳞。（防御+2，+5%生命）；你完全覆盖着粗糙棕鳞。（防御+3，+7%生命）；粗糙的棕色的鳞片覆盖了你身体的一部分。；粗糙的棕色的鳞片蔓延到你身体的更多部位。；粗糙的棕色的鳞片完全覆盖了你的身体。；你粗糙的棕色鳞片消失了。；你粗糙的棕色鳞片有所消退。 | 3 级；weight 0；flags mutflag::good ／ mutflag::su…；说明：你被褐色鳞片覆盖，这会提供少量保护。 这个变异每升一级会加1点防护，并会稍稍提升你的生命力。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_RUNIC_MAGIC` | current | runic magic → 符文魔法；显示：符文魔法；你的法术施放受护甲的阻碍大大减少。；你的施法受到护甲的阻碍减小了。；你的施法不再受到护甲的阻碍。 | 1 级；weight 0；flags mutflag::good；说明：你借助刻在护甲上的符文施法，大幅减少原本需要的复杂动作。 （计算施法成功率时，你穿戴的所有护甲的负重评级减半。） | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_SANGUINE_ARMOUR` | current | sanguine armour → 血之护甲；显示：血之护甲；当你严重受伤时，血液会形成护甲。（防御+；当你严重受伤时，血液会形成厚实的护甲。（防御+；当你严重受伤时，血液会形成非常厚实的护甲。（防御+；你感到血液准备好保护你了。；你感到血液变浓了。；你感到血液完全平息了。；你感到血液变稀了。 | 3 级；weight 0；flags mutflag::good ／ mutflag::ne…；说明：当受重伤时，你的血液会在你周围凝结，形成护甲。这个变异每升一级就会提升防护。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_SCREAM` | current | screaming → 尖叫；显示：尖叫；你偶尔不受控制地对伤害你的人大喊。；你经常不受控制地对伤害你的人尖叫。；你感到想要大喊。；你感到强烈的尖叫冲动。；你想要大喊的冲动消失了。；你尖叫的冲动减轻了。 | 2 级；weight 6；flags mutflag::bad；说明：当敌人第一次出现在你的视线中时，有时你会有种无法克制的冲动，要冲他们喊叫。 你的喊叫声也都比平时更大。这个变异达到第二级，你将更难克制那股冲动… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_SHAGGY_FUR` | current | shaggy fur → 浓密皮毛；显示：浓密皮毛；你覆盖着毛发。（防御+1）；你覆盖着浓密毛发。（防御+2）；你浓密蓬松的毛发让你保持温暖。（防御+3，冰抗+）；全身长出了毛发。；你的毛发长成了厚密的鬃毛。；你的厚密毛发长得蓬松而温暖。；你褪去了所有毛发。；你的厚密毛发有所消退。；你的蓬松毛发有所消退。；你的浓密皮毛将为你保暖。（AC + 3, rC+） | 3 级；weight 2；flags mutflag::good ／ mutflag::an…；说明：你被皮毛覆盖，这会提供少量保护。这个变异每升一级会加1点防护。 这个变异达到第三级会提供寒抗。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_SHARP_SCALES` | current | sharp scales → 锐利鳞片；显示：锐利鳞片；你部分覆盖着锋利鳞片。（防御+1，杀戮+1）；你大部分覆盖着锋利鳞片。（防御+2，杀戮+2）；你完全覆盖着锋利鳞片。（防御+3，杀戮+3）；锐利的鳞片覆盖了你身体的一部分。；锐利的鳞片蔓延到你身体的更多部位。；锐利的鳞片完全覆盖了你的身体。；你锐利的鳞片消失了。；你锐利的鳞片有所消退。 | 3 级；weight 0；flags mutflag::good ／ mutflag::su…；说明：你被尖锐的鳞片覆盖，这会提供少量保护。这个变异每升一级会加1点防护和1点杀戮， 这会提升你在近身和远程攻击中的命中率和伤害。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_SHOCK_RESISTANCE` | current | electricity resistance → 电击抗性；显示：电击抗性；你对电击有抗性。（电抗）；你感到绝缘。；你感到导电。 | 1 级；weight 2；flags mutflag::good ／ mutflag::su…；说明：你抵抗电（rElec），电对你造成的伤害变弱。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_SHOCK_VULNERABILITY` | current | electricity vulnerability → 电击弱点；显示：电击弱点；你容易被电击。（电抗-）；你感到易受电击伤害。；你感到对电击的脆弱减轻了。 | 1 级；weight 2；flags mutflag::bad ／ mutflag::sub…；说明：电很容易对你造成伤害，并会对你造成更多伤害。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_SHORT_LIFESPAN` | current | otherworldly → 异界；显示：异界；你很容易被佐特发现。；你感到时间不多了。；你感到长寿。 | 1 级；weight 0；flags mutflag::bad；说明：你与这个世界格格不入，很容易被黑暗势力察觉。 在佐特找到你并永久降低你的生命值之前，你在每层地牢的时间只有正常时间的十分之一。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_SILENCE_AURA` | current | aura of silence → 沉默光环；显示：沉默光环；你被一个沉默光环包围。；一种不自然的寂静笼罩了你。 | 1 级；weight 0；flags mutflag::good；说明：你被沉默力场所围绕。与你相邻的怪物无法发出任何声音。 它可以阻止大多数形式的施法和祈祷，但恶魔的魔法是无声的，不受此影响。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_SLIME_SHROUD` | current | slime shroud → 黏液护罩；显示：黏液护罩；一层脆弱的黏液护罩覆盖着你，偏转攻击。；一层薄薄的黏液覆盖了你的身体。；你的黏液膜干涸了。 | 1 级；weight 0；flags mutflag::good ／ mutflag::ji…；说明：覆盖身体的黏液护罩在你受到近战攻击时可能将其偏转。 但偏转会破坏护罩，需要一段时间才能重新形成。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_SLIMY_GREEN_SCALES` | current | slimy green scales → 黏滑绿鳞；显示：黏滑绿鳞；你部分覆盖着黏滑绿鳞。（防御+2）；你大部分覆盖着黏滑绿鳞。（防御+3）；你完全覆盖着黏滑绿鳞。（防御+4，毒抗）；黏滑的绿色的鳞片覆盖了你身体的一部分。；黏滑的绿色的鳞片蔓延到你身体的更多部位。；黏滑的绿色的鳞片完全覆盖了你的身体。；你黏滑的绿色鳞片消失了。；你黏滑的绿色鳞片有所消退。 | 3 级；weight 0；flags mutflag::good ／ mutflag::su…；说明：你被绿色鳞片覆盖，这会提供少量保护。这个变异每升一级会提供更多防护。 这个变异达到第三级会提供毒抗。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_SLOW` | current | slowness → 缓慢；显示：缓慢；你移动缓慢。；你移动非常缓慢。；你移动极其缓慢。；你感觉迟缓。；你感到敏捷。 | 3 级；weight 0；flags mutflag::bad；说明：你行进得很慢——移动到新位置所需的时间会更长。它对其他类型的动作没有影响， 比如攻击或施法。这个变异每升一级，你移动得会更慢。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_SLOW_REFLEXES` | current | reduced EV → 降低闪避；显示：降低闪避；你的反应有些迟钝。（闪避-5）；你的反应迟钝。（闪避-10）；你的反应非常迟钝。（闪避-15）；你的反应变慢了。；你的反应变得更慢了。；你的反应恢复了正常。；你的反应速度恢复了。 | 3 级；weight 0；flags mutflag::bad；说明：你的反应很慢，敌人很容易攻击你。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_SLOW_WIELD` | current | slow wielding → 缓慢持武；显示：缓慢持武；你持握或移除武器需要很长时间。 | 1 级；weight 0；flags mutflag::bad；说明：装备或卸下武器时，你必须重新校准抓握手臂，所需时间与穿戴护甲相同。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_SPATIAL_ENTANGLEMENT` | current | spatial entanglement → 空间纠缠；显示：空间纠缠；当你位移时，有时会将一个怪物一起拉过去。；你感到周围的空间开始纠结在一起。；你感到空间从你身上解开了纠缠。 | 1 级；weight 2；flags mutflag::bad；说明：每当你发生传送时，都有概率将另一只怪物一同拉到你的新位置。 短距离传送只会拉走你原位置视野内的怪物，长距离传送则可能拉来本层任何地方的怪物。 … | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_SPELLCLAWS` | current | spellclaws → 法术之爪；显示：法术之爪；每当你施放伤害法术时，你会进行一次近战攻击。；你感到毁灭魔法在爪间流淌。；你不再感到毁灭魔法在爪间流淌。 | 1 级；weight 0；flags mutflag::good；说明：你会本能地通过利爪引导破坏性魔法。施放伤害法术时， 你还会对攻击范围内生命值最高的敌人发动一次近战攻击。 如果你的攻击速度慢于施法速度，此次攻… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_SPINY` | current | spiny → 尖刺；显示：尖刺；你部分覆盖着锋利的尖刺。；你大部分覆盖着锋利的尖刺。；你完全覆盖着锋利的尖刺。；锐利的尖刺从你身体的部分部位长出。；锐利的尖刺从你身体的更多部位长出。；锐利的尖刺从你的全身长出。；你锐利的尖刺完全消失了。；你锐利的尖刺有所收缩。 | 3 级；weight 0；flags mutflag::good ／ mutflag::an…；说明：近战击中你的敌人有50%的几率被你的尖刺刺穿并受到伤害。 这个变异每升一级，尖刺造成的伤害都会提高。此变异还使你免疫束缚。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_SPITEFUL_BLOOD` | current | spiteful blood → 怨恨之血；显示：怨恨之血；你流出的血液可能会起来攻击你。；你流出的血液可能会成群地起来攻击你。；你感到血液中积聚着一股任性的愤怒。；你感到血液中的怨恨更加强烈了。；你的血液再次平静下来。；你感到血液中的怨恨少了一些。 | 2 级；weight 2；flags mutflag::bad ／ mutflag::nee…；说明：你的血液涌动着奇异的捕食恶意。当你受到重伤时，一部分血液可能会升起并攻击你—— 但在你完全恢复前，此事不会再次发生。 此变异的第二级会同时产生… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_SPIT_POISON` | current | spit poison → 喷吐毒液；显示：喷吐毒液；你可以喷吐毒素。；你可以喷吐一团毒雾。；你口中一时有种恶心的味道。；你感到喉咙疼痛。 | 2 级；weight 8；flags mutflag::good ／ mutflag::an…；说明：你可以通过<input>$cmd[CMD_USE_ABILITY]</input>喷吐毒液。 这个变异达到第二级，毒素会从一小团毒液，变成一大… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_STEAM_RESISTANCE` | current | steam resistance → 蒸汽抗性；显示：蒸汽抗性；你对蒸汽效果免疫。；你现在对蒸汽效果免疫了。；你不再对蒸汽效果免疫。 | 1 级；weight 0；flags mutflag::good ／ mutflag::su…；说明：你对蒸汽吐息和蒸汽云的伤害免疫。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_STINGER` | current | stinger → 毒刺；显示：毒刺；你的尾巴末端是一根毒刺。；你的尾巴末端是一根锋利的毒刺。；你的尾巴末端是一根极其锋利的毒刺。；你尾巴的末端形成了一根毒钩。；你尾巴上的毒钩看起来更锋利了。；你尾巴上的毒钩看起来非常锋利。；你尾巴上的毒钩消失了。；你尾巴上的毒钩似乎不那么锋利了。 | 3 级；weight 8；flags mutflag::good ／ mutflag::an…；说明：你的尾部长出一个毒刺，在近战时能够蛰刺敌人。 这个变异每升一级，你的螫刺就会更尖、更长、更强。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_STONE_BODY` | current | stone body → 石质身体；显示：石质身体；你的石质身体坚韧且免疫石化。（防御+；你的身体在震动。；你短暂地停止了移动。 | 1 级；weight 0；flags mutflag::good ／ mutflag::su…；说明：你由极为耐受伤害的活石构成。你会获得大量护甲等级加成， 且加成随经验等级提高；你还免疫石化、中毒、疾病、睡眠及其他某些效果。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_STRONG` | current | strong → 强壮；显示：强壮；你很强壮。（力量+4，智力/敏捷-1）；你非常强壮。（力量+8，智力/敏捷-2） | 2 级；weight 7；flags mutflag::good；说明：你的肌肉变得异常强壮。这个变异每升一级会加4点力量， 但额外的肌肉会让你的动作和思维变得迟钝，每升一级，你的智力和敏捷会减1点。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_STRONG_WILLED` | current | strong-willed → 意志坚强；显示：意志坚强；你意志坚强。（意志+）；你意志非常坚强。（意志++）；你意志极其坚强。（意志+++）；你感到意志坚定。；你感到意志更加坚定。；你感到意志几乎牢不可破。；你不再感到意志坚定。；你感到意志不再那么坚定。 | 3 级；weight 5；flags mutflag::good；说明：你有着异常强大的意志，提升了对某类敌对魔法的抵抗力。 这个变异每升一级，就会增加你的意志力。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_STURDY_FRAME` | current | sturdy frame → 健壮体格；显示：健壮体格；护甲对你的移动阻碍略微减少。（负重-2）；护甲对你的移动阻碍减少。（负重-4）；护甲对你的移动阻碍显著减少。（负重-6）；你感到护甲不那么累赘了。；你感到护甲更加累赘了。 | 3 级；weight 2；flags mutflag::good；说明：你的行动将少受到护甲的阻碍， 并减少了护甲对施法成功率、闪避和远程武器攻击速度的负面影响。 这个变异每升一级，就会减少2点护甲的妨碍等级。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_SUBDUED_MAGIC` | current | subdued magic → 压制魔法；显示：压制魔法；你的法术施放稍微更容易，但威力稍微更弱。；你的法术施放更容易，但威力更弱。；你的法术施放容易得多，但威力弱得多。；你与魔法的连接感到被抑制了。；你与魔法的连接感到更加被抑制了。；你与魔法的连接几乎沉睡。；你的魔法恢复了正常的活力。；你与魔法的连接不那么被抑制了。 | 3 级；weight 6；flags mutflag::bad；说明：你的法术将略易施放（减少了失误率和判定的严苛程度），但威力会变弱。 这个变异每升一级，两方面的效果都会增强。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_TALONS` | current | talons → 爪；显示：爪；你有锋利的趾甲。；你有剃刀般锋利的趾甲。；你脚上有爪子。；你的趾甲变长变锋利了。；你的双脚伸成了利爪。；你的利爪变钝缩成了脚。；你的利爪看起来更像脚了。 | 3 级；weight 5；flags mutflag::good ／ mutflag::an…；说明：你长出锋利的趾甲，如果不穿靴子，在近战时能够踢击敌人。这个变异每升一级， 你的趾甲就会更尖、更长、更强。这个变异达到第三级，你将无法穿靴子。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_TELEPORTITIS` | current | teleportitis → 传送症；显示：传送症；你偶尔会被传送到怪物旁边。；你经常会被传送到怪物旁边。；你感到莫名的不确定。；你感到更加莫名的不确定。；你感到稳定。 | 2 级；weight 3；flags mutflag::bad；说明：你会周期性地传送到敌对怪物附近。传送发生前数回合，你会感觉自身开始变得不稳定； 阅读传送卷轴可以暂时抑制这种情况。 这个变异每升一级，开始传送… | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_TEMPERATURE_SENSITIVITY` | current | temperature sensitive → 温度敏感；显示：温度敏感；你对极端温度敏感。（火抗-，冰抗-）；你感到对极端温度敏感。；你不再对极端温度敏感。 | 1 级；weight 0；flags mutflag::bad；说明：寒冷和火都很容易对你造成伤害，并会对你造成更多伤害。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_TENDRILS` | current | tendrils → 卷须；显示：卷须；你覆盖着黏液卷须，可能缴械对手。；细细的黏滑触须从你的身体长出。；你的触须缩回了体内。 | 1 级；weight 0；flags mutflag::good ／ mutflag::ji…；说明：受到近战伤害时，覆盖在你身体上的黏稠卷须可能会抓住攻击者的武器， 并从他手上将其拽出，解除他们的武装。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_TENGU_FLIGHT` | current | evasive flight → 闪避飞行；显示：闪避飞行；你的魔法飞行帮助你闪避攻击。（闪避+4）；你的魔法本质发展了，使你能以闪避之姿飞行。；你的魔法飞行将帮助你躲避攻击。（EV + 4） | 1 级；weight 0；flags mutflag::good；说明：你地在空中扑闪，闪避能力得到一定提升。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_TENTACLE_ARMS` | current | tentacles → 触手；显示：触手；你的手臂是触手，可以缠绕敌人。；你的手臂感到如触手般。；你的手臂不再感到如触手般了。 | 1 级；weight 0；flags mutflag::good ／ mutflag::an…；说明：你的胶状身体有八个触手，可以帮助你在浅水或深水中移动，并能在近战时束缚敌人。 每只触手都可以戴上戒指，但你需要四只触手用来移动，根据武器的大小… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_TENTACLE_SPIKE` | current | tentacle spike → 触手尖刺；显示：触手尖刺；你的一条触手上有一根尖刺。；你的一条触手上有一根锐利的尖刺。；你的一条触手上有一根巨大的凶猛尖刺。；你的一根下方触手长出了一根锐利的尖刺。；你的触手尖刺变大了。；你的触手尖刺变得更大了。；你的触手尖刺消失了。；你的触手尖刺变小了。；你的触手尖刺有所消退。 | 3 级；weight 10；flags mutflag::good ／ mutflag::an…；说明：你长出一个带有尖刺的触手，在近战时能够刺穿敌人。 这个变异每升一级，你的刺就会更尖、更长、更强。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_THIN_METALLIC_SCALES` | current | thin metallic scales → 薄金属鳞片；显示：薄金属鳞片；你部分覆盖着薄金属鳞片。（防御+2）；你大部分覆盖着薄金属鳞片。（防御+3）；你完全覆盖着薄金属鳞片。（防御+4，电抗）；薄金属的鳞片覆盖了你身体的一部分。；薄金属的鳞片蔓延到你身体的更多部位。；薄金属的鳞片完全覆盖了你的身体。；你薄金属鳞片消失了。；你薄金属鳞片有所消退。 | 3 级；weight 0；flags mutflag::good ／ mutflag::su…；说明：你被金属鳞片覆盖，这会提供少量保护。 这个变异每升一级会提供更多防护。这个变异达到第三级会提供电抗。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_THIN_SKELETAL_STRUCTURE` | current | thin skeletal structure → 纤细骨骼；显示：纤细骨骼；你的骨骼结构有些纤细。（敏捷+2，潜行+）；你的骨骼结构相当纤细。（敏捷+4，潜行++）；你的骨骼结构异常纤细。（敏捷+6，潜行+++）；你的骨骼密度略有降低。；你的骨骼密度有所降低。；你的骨骼密度降低了。；你的骨骼结构恢复了正常。；你的骨骼结构变密了。 | 3 级；weight 2；flags mutflag::good ／ mutflag::ne…；说明：你的骨头变得轻巧、多孔。这个变异每升一级会加2点敏捷和潜行。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_TIME_WARPED_BLOOD` | current | time-warped blood → 时间扭曲之血；显示：时间扭曲之血；当你受到足够伤害时，你的血液会加速少数盟友。；当你受到足够伤害时，你的血液会加速数名盟友。；你血液的流动与时间本身不同步了。；你血液的流动脱离了时间。；你的血液流动再次与正常的时间流逝同步了。；你的血液流动开始与正常的时间流逝同步。 | 2 级；weight 2；flags mutflag::good ／ mutflag::ne…；说明：你的血液已经与时间流动失去同步。每当你的生命值降至上限的 50% 以下， 流出的血液就会奇异地涌过周围，使视野内最强的盟友加速；每级此变异会影… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_TORMENT_RESISTANCE` | current | torment resistance → 折磨抗性；显示：折磨抗性；你抵抗邪恶折磨。；你对邪恶痛苦和折磨免疫。；你感到一种奇怪的麻木。；你感到一种非常奇怪的麻木。 | 2 级；weight 0；flags mutflag::good ／ mutflag::su…；说明：折磨对你的影响较弱，否则这会让你的生命值减半。 这个变异达到第二级，你将完全免疫折磨。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_TOUGH_SKIN` | current | tough skin → 硬化表皮；显示：硬化表皮；你拥有坚韧的皮肤。（防御+1）；你拥有非常坚韧的皮肤。（防御+2）；你拥有极其坚韧的皮肤。（防御+3）；你的皮肤变坚韧了。；你的皮肤变得娇嫩了。 | 3 级；weight 2；flags mutflag::good ／ mutflag::an…；说明：你的表皮已经硬化，这会提供少量保护。这个变异每升一级会加1点防护。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_TRANSLUCENT_SKIN` | current | translucent skin → 半透明皮肤；显示：半透明皮肤；你半透明的皮肤略微降低了敌人的精准度。（潜行+）；你半透明的皮肤降低了敌人的精准度。（潜行+）；你透明的皮肤显著降低了敌人的精准度。（潜行+）；你的皮肤变得部分半透明。；你的皮肤变得更加半透明。；你的皮肤变得完全透明。；你的皮肤恢复了正常的不透明度。；你的皮肤不再半透明了。；你的皮肤不再透明了。 | 3 级；weight 0；flags mutflag::good ／ mutflag::ji…；说明：你的皮肤是透明的，你的潜行能力得到提升，敌人攻击你的命中率会降低。 这个变异每升一级，就会削弱你的敌人的命中率。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_TREASURE_SENSE` | current | treasure sense → 宝物感知；显示：宝物感知；你有探测物品的奇特能力。；你突然感到能感知宝物。；你不再感到能感知宝物。 | 1 级；weight 0；flags mutflag::good；说明：你对物品所在位置有不可思议的感知。探索地牢时， 附近那些你无法直接看见、尚未发现的物品位置会在地图上获得标记。 | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_TRICKSTER` | current | trickster → 戏法者；显示：戏法者；当你对附近的敌人施加魔法灾厄时，你获得防御。 | 1 级；weight 0；flags mutflag::good；说明：你散播不幸时，与生者领域的联系会变强。 每当你或盟友对附近敌人施加新的负面状态（中毒除外）时，你的护甲等级会暂时提高。 受影响的不同敌人越多，… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_UNSKILLED` | current | unskilled → 无技能；显示：无技能；你天赋有些不足。（-1资质）；你天赋不足。（-2资质）；你天赋极其不足。（-3资质）；你感到技能减退了。；你恢复了全部技能。；你恢复了一些技能。 | 3 级；weight 0；flags mutflag::bad；说明：你提升技能需要更多经验。这个舍弃每升一级，技能成本就会更高。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_WARMUP_STRIKES` | current | warmup strikes → 预热打击；显示：预热打击；你的前几次攻击造成较少伤害。 | 1 级；weight 0；flags mutflag::bad ／ mutflag::ana…；说明：你的抓握手臂需要时间活动开，因此每场战斗最初几次攻击效果较差。 缓慢而沉重的攻击比快速攻击更有助于热身。武器攻击和徒手攻击都会受影响。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_WEAK` | current | weak → 虚弱；显示：虚弱；你很虚弱。（力量-3）；你非常虚弱。（力量-6） | 2 级；weight 8；flags mutflag::bad；说明：你的肌肉变得异常虚弱。这个变异每升一级会减3点力量。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_WEAKNESS_STINGER` | current | weakness stinger → 虚弱毒刺；显示：虚弱毒刺；你有一条小尾巴。；你的尾巴末端是一根锋利的毒刺。；你有一根锋利的毒刺，能造成虚弱毒素。；你长出了一条小尾巴。；你的尾巴长出了一根锋利的毒刺。；你的毒刺变得更大并开始产生衰弱毒素。 | 3 级；weight 0；flags mutflag::good ／ mutflag::an…；说明：你长出一条细长的红色尾巴，在近战时能够扫打敌人。 这个变异每升一级会增强你的尾巴的力量，并使其变成尖锐的螫刺。 这个变异达到第三级，那些不幸被… | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_WEAK_WILLED` | current | weak-willed → 意志薄弱；显示：意志薄弱；你意志略微薄弱。（意志-）；你意志薄弱。（意志--）；你意志极其薄弱。（意志---）；你感到意志薄弱。；你感到意志更加薄弱。；你不再感到意志薄弱。；你感到意志不那么薄弱了。 | 3 级；weight 0；flags mutflag::bad；说明：你有着异常疲弱的意志，削弱了对某类敌对魔法的抵抗力。 这个变异每升一级，就会削弱你的意志力。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_WIELD_OFFHAND` | current | off-hand wielding → 副手持有；显示：副手持有；你可以在副手持有第二把武器。 | 1 级；weight 0；flags mutflag::good；说明：只要没有持握双手武器，也没有装备盾牌或魔法球，你就可以在副手持握一件单手武器。 主手攻击后会追加一次副手攻击，攻击延迟由两件武器的平均值决定。… | 修订：校准名称、术语或机制说明 |
| `mutation:MUT_WILD_MAGIC` | current | wild magic → 狂野魔法；显示：狂野魔法；你的法术施放稍微更困难，但威力稍微更强。；你的法术施放更困难，但威力更强。；你的法术施放困难得多，但威力强得多。；你感到对魔法的控制力减弱了。；你感到魔力失控了！；你恢复了对魔法的控制。；你感到对魔法的控制力增强了。 | 3 级；weight 6；flags mutflag::good；说明：你的法术将略难施放（增加了失误率和判定的严苛程度），但威力会变强。 这个变异每升一级，两方面的效果都会增强。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_WORD_OF_CHAOS` | current | word of chaos → 混沌之语；显示：混沌之语；你可以说出混沌之语。；你的舌头扭曲了。 | 1 级；weight 0；flags mutflag::good；说明：你可以通过<input>$cmd[CMD_USE_ABILITY]</input>念出混沌之语。 | 保留：名称、等级显示与机制说明准确 |
| `mutation:MUT_YELLOW_SCALES` | current | yellow scales → 黄色鳞片；显示：黄色鳞片；你部分覆盖着黄色鳞片。（防御+2）；你大部分覆盖着黄色鳞片。（防御+3）；你完全覆盖着黄色鳞片。（防御+4，酸抗）；黄色的鳞片覆盖了你身体的一部分。；黄色的鳞片蔓延到你身体的更多部位。；黄色的鳞片完全覆盖了你的身体。；你黄色的鳞片消失了。；你黄色的鳞片有所消退。 | 3 级；weight 0；flags mutflag::good ／ mutflag::su…；说明：你被黄色鳞片覆盖，这会提供少量保护。这个变异每升一级会提供更多防护。 这个变异达到第三级会提供酸抗和腐蚀抗。 | 保留：名称、等级显示与机制说明准确 |

## 时长状态证据卡（223）

| 身份 | 生命周期 | 名称与显示形式 | 生产事实 | 终态结论 |
|---|---|---|---|---|
| `duration:DUR_ABJURATION_AURA` | internal | old abjuration → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old abjuration | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_ACROBAT` | current | acrobatic → 身手敏捷；显示：身手敏捷；你身手敏捷，闪避能力提高。 | `duration_data` 显示槽 2/3；flags D_NO_FLAGS；内部名 acrobat | 修订：补齐显示翻译或统一相关说明术语 |
| `duration:DUR_AFRAID` | current | afraid → 恐惧；显示：恐惧；你惊恐万分。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_EXPIRES ／ D…；内部名 — | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_AGILITY` | current | agile → 敏捷；显示：敏捷；你身手敏捷。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE；内部名 agility | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_ALLY_RESET_TIMER` | internal | ally reset timer → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 ally reset timer | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_AMBROSIA` | current | ambrosia-drunk → 仙酒醉；显示：仙酒；仙酒醉；你正在仙酿的作用下再生。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE；内部名 ambrosia | 修订：补齐显示翻译或统一相关说明术语 |
| `duration:DUR_ANCESTOR_DELAY` | internal | ancestor delay → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 ancestor delay | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_ANIMATE_DEAD` | current | animating dead → 复活死者；显示：收割；复活死者；你正在复活死者。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_EXPIRES；内部名 animating dead | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_ANTENNAE_EXTEND` | internal | old antennae extend → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old antennae extend | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_ANTIMAGIC` | internal | old antimagic → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old antimagic | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_ATTRACTIVE` | current | attractive → 吸引怪物；显示：吸引；吸引怪物；你吸引怪物向你靠近。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 attract | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_AUTODODGE` | internal | autododge → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 autododge | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_BARBS` | current | spiked → 被刺穿；显示：尖刺；被刺穿；倒刺尖刺嵌在了你的身体里。 | `duration_data` 显示槽 3/3；flags D_NEGATIVE；内部名 barbed spikes | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_BARGAIN` | internal | old bargain → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old bargain | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_BATTLESPHERE` | internal | old battlesphere → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old battlesphere | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_BEOGH_CAN_RECRUIT` | current | Recruit → 招募；显示：招募；你可以将击败的使徒招募到麾下。 | `duration_data` 显示槽 2/3；flags D_EXPIRES；内部名 can recruit | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_BEOGH_DIVINE_CHALLENGE` | current | Challenge → 挑战；显示：挑战；一位贝欧格的仆从来挑战你了。 | `duration_data` 显示槽 2/3；flags D_NO_FLAGS；内部名 apostle challenge | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_BEOGH_SEEKING_VENGEANCE` | current | Vengeance → 复仇；显示：复仇；你正在为同胞之死寻求复仇。 | `duration_data` 显示槽 2/3；flags D_NO_FLAGS；内部名 vengeance | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_BERSERK` | current | berserking → 狂暴中；显示：狂暴；狂暴中；你被狂暴之怒所控制。 | `duration_data` 显示槽 3/3；flags D_EXPIRES；内部名 berserk | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_BERSERK_COOLDOWN` | current | on berserk cooldown → 狂暴冷却；显示：-狂暴；狂暴冷却；你无法进入狂暴状态。 | `duration_data` 显示槽 3/3；flags D_COOLDOWN；内部名 berserk cooldown | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_BINDING_SIGIL_WARNING` | internal | old binding sigil → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old binding sigil | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_BLIND` | current | blinded → 致盲；显示：致盲；目标越远，你的命中率越低。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_EXPIRES ／ D…；内部名 blindness | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_BLINKBOLT_COOLDOWN` | current | blinkbolt cooldown → 电闪冷却；显示：-电闪；电闪冷却 | `duration_data` 显示槽 2/3；flags D_COOLDOWN；内部名 no blinkbolt | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_BLINKITIS` | current | blinking rapidly → 快速闪烁；显示：不稳；快速闪烁；你在空间中不受束缚。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 blinkitis | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_BLINK_COOLDOWN` | current | on blink cooldown → 闪烁冷却；显示：-闪烁；闪烁冷却；你无法闪烁。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS ／ D_COOLDOWN；内部名 blink cooldown | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_BLOOD_FOR_BLOOD` | current | chanting a vengeful prayer → 吟唱复仇祈祷；显示：祈祷；吟唱复仇祈祷；你正在吟唱复仇祷文。 | `duration_data` 显示槽 3/3；flags D_EXPIRES；内部名 blood for blood | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_BRAINLESS` | internal | old brainless → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old brainless | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_BREATH_WEAPON` | current | short of breath → 喘息中；显示：-吐息；喘息中；你喘不过气来。 | `duration_data` 显示槽 3/3；flags D_COOLDOWN；内部名 breath weapon | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_BRILLIANCE` | current | brilliant → 聪慧；显示：聪慧；你正处于聪慧状态。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE；内部名 brilliance | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_BUILDING_RAGE` | internal | old building rage → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old building rage | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_CACOPHONY` | current | making a cacophony → 制造噪音；显示：噪音；制造噪音；你被诅咒的护甲正在发出不洁的噪音。 | `duration_data` 显示槽 3/3；flags D_EXPIRES；内部名 cacophony | 修订：补齐显示翻译或统一相关说明术语 |
| `duration:DUR_CANINE_FAMILIAR_DEAD` | current | unable to call your familiar → 无法召唤使魔；显示：-犬灵；无法召唤使魔；你无法召唤你的犬类伙伴。 | `duration_data` 显示槽 3/3；flags D_EXPIRES；内部名 canine familiar cooldown | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_CELEBRANT_COOLDOWN` | current | on bloodrite cooldown → 血祭冷却；显示：-血祭；血祭冷却；你无法进行血之仪式。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 bloodrite cooldown | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_CHANNEL_ENERGY` | current | channelling → 引导中；显示：引导；引导中；你的魔力正在快速再生。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 channel | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_CLEAVE` | current | cleaving → 横扫中；显示：横扫；横扫中；你正在劈砍敌人。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 cleave | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_CLOUD_TRAIL` | internal | cloud trail → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 cloud trail | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_CLUMSY` | internal | old clumsy → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old clumsy | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_COLLAPSE` | internal | old collapse → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old collapse | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_CONDENSATION_SHIELD` | internal | old condensation shield → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old condensation shield | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_CONF` | current | confused → 困惑；显示：混乱；困惑；你处于混乱状态。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 conf | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_CONFUSING_TOUCH` | current | confusing by touch → 触之迷惑；显示：触碰；触之迷惑 | `duration_data` 显示槽 2/3；flags D_DISPELLABLE；内部名 confusing touch | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_CONSTRICTED` | internal | constricted → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 constricted | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_CONSTRICTION_IMMUNITY` | internal | constrict immune → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 constrict immune | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_CONTROLLED_FLIGHT` | internal | old controlled flight → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old controlled flight | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_CONTROL_TELEPORT` | internal | old control teleport → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old control teleport | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_CORONA` | current | lit by a corona → 被光晕照亮；显示：光晕；被光晕照亮 | `duration_data` 显示槽 2/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 corona | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_CORPSE_ROT` | internal | old corpse rot → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old corpse rot | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_CORROSION` | current | corroded → 腐蚀；显示：腐蚀；你被腐蚀了。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 corrosion | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_DARKNESS` | internal | old darkness → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old darkness | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_DAZED` | internal | dazed → — | `duration_data` 显示槽 0/3；flags D_NEGATIVE；内部名 dazed | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_DEATHS_DOOR` | current | in death's door → 死亡之门中；显示：死门；死亡之门中；你正站在死亡之门中。 | `duration_data` 显示槽 3/3；flags D_EXPIRES；内部名 deaths door | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_DEATHS_DOOR_COOLDOWN` | current | on death's door cooldown → 死亡之门冷却；显示：-死门；死亡之门冷却；你无法进入死门状态。 | `duration_data` 显示槽 3/3；flags D_COOLDOWN；内部名 deaths door cooldown | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_DEATH_CHANNEL` | current | death channelling → 引导死亡；显示：亡道；引导死亡；你正在引导亡灵。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_EXPIRES；内部名 death channel | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_DEFLECT_MISSILES` | internal | old deflect missiles → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old deflect missiles | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_DEMONIC_GUARDIAN` | internal | demonic guardian → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 demonic guardian | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_DETONATION_CATALYST` | current | catalyst → 催化；显示：催化；你的打击点燃了爆炸催化剂。 | `duration_data` 显示槽 3/3；flags D_EXPIRES ／ D_ATTACK_EXTENDED；内部名 catalyst | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_DEVICE_SURGE` | internal | old device surge → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old device surge | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_DEVIOUS` | current | devious → 狡诈；显示：狡诈；你感到十分狡诈。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_EXPIRES ／ D…；内部名 devious | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_DIMENSIONAL_BULLSEYE` | current | portalling projectiles → 传送飞弹中；显示：靶心；传送飞弹中；你正在将弹射物传送至目标。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE；内部名 bullseye | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_DIMENSION_ANCHOR` | current | untranslocatable → 无法位移；显示：-传送；无法位移；你被牢固地锚定在这个位面。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 dimension anchor | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_DIMINISHED_SPELLS` | current | diminished spells → 法术减弱；显示：暗淡；法术减弱；你的法术威力减弱了。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 diminished spells | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_DISJUNCTION` | current | disjoining → 位移中；显示：位移；位移中；你正在与周围环境隔离。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_EXPIRES；内部名 disjunction | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_DIVINE_SHIELD` | current | divinely shielded → 神圣护盾；显示：神圣护盾；你受到光辉者之力的护佑。 | `duration_data` 显示槽 2/3；flags D_NO_FLAGS；内部名 divine shield | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_DIVINE_STAMINA` | current | vitalised → 生命活力；显示：活力；生命活力；你被神圣力量注入了活力。 | `duration_data` 显示槽 3/3；flags D_EXPIRES；内部名 divine stamina | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_DIVINE_VIGOUR` | current | divinely vigorous → 神圣活力；显示：神圣活力；你被注入了神圣活力。 | `duration_data` 显示槽 2/3；flags D_NO_FLAGS；内部名 divine vigour | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_DRAGON_CALL` | current | calling dragons → 召唤龙群；显示：龙召；召唤龙群；你正在召唤一群巨龙。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 dragon call | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_DRAGON_CALL_COOLDOWN` | current | on dragon call cooldown → 龙群召唤冷却；显示：-龙召；龙群召唤冷却；你无法召唤龙。 | `duration_data` 显示槽 3/3；flags D_COOLDOWN；内部名 dragon call cooldown | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_DROWSY` | current | Drowsy → 困倦 | `duration_data` 显示槽 1/3；flags D_NEGATIVE；内部名 drowsy | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_DUEL_COMPLETE` | internal | old duel complete → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old duel complete | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_EELJOLT_COOLDOWN` | current | on eeljolt cooldown → 电鳗冲击冷却；显示：-电冲；电鳗冲击冷却；你的双手最近已释放了全部电压。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 eeljolt cooldown | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_ELIXIR` | current | elixired → 灵药生效；显示：灵药；灵药生效；你的生命和魔力正在快速再生。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 elixir | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_ELIXIR_MAGIC` | internal | old elixir magic → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old elixir magic | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_ENGORGED` | current | engorged → 饱食；显示：饱食；你的大嘴正在消化一顿美味大餐。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 engorged | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_ENKINDLED` | current | enkindled → 点燃；显示：点燃；你的火焰因追忆而燃烧得更加明亮。 | `duration_data` 显示槽 3/3；flags D_EXPIRES；内部名 enkindled | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_ENLIGHTENED` | current | enlightened → 启迪；显示：意志+；启迪；你处于顿悟状态。（意志+） | `duration_data` 显示槽 3/3；flags D_DISPELLABLE；内部名 — | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_EPHEMERAL_SHIELD` | current | ephemerally shielded → 短暂护盾；显示：短暂护盾；你施法或祈唤后会短暂获得护盾。 | `duration_data` 显示槽 2/3；flags D_DISPELLABLE ／ D_EXPIRES；内部名 ephemeral shield | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_EXCRUCIATING_WOUNDS` | internal | old excruciating wounds → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old excruciating wounds | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_EXECUTION` | current | surrounded by blades → 刃之旋风；显示：处刑；刃之旋风；你被利刃旋风包围着。 | `duration_data` 显示槽 3/3；flags D_EXPIRES ／ D_ATTACK_EXTENDED；内部名 execution | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_EXHAUSTED` | current | exhausted → 力竭；显示：力竭；你精疲力竭了。 | `duration_data` 显示槽 3/3；flags D_COOLDOWN；内部名 — | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_FATHOMLESS_SHACKLES` | current | enshackling → 束缚中；显示：镣铐；束缚中；你正在引导伊雷德勒姆努尔的无情掌控。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 fathomless shackles | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_FIERY_ARMOUR` | current | fiery-armoured → 火焰护甲；显示：火焰护甲；你被烈焰斗篷所保护。 | `duration_data` 显示槽 2/3；flags D_EXPIRES；内部名 fiery armour | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_FINESSE` | current | finesse-ful → 精准；显示：精准；你的打击快如闪电。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 finesse | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_FIRE_SHIELD` | internal | old ring of flames → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old ring of flames | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_FIRE_VULN` | current | fire vulnerable → 火焰易伤；显示：抗火-；火焰易伤；你更容易受到火焰伤害。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 fire vulnerability | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_FLAYED` | current | flayed → 剥皮；显示：剥皮；你身负可怕的创伤。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_EXPIRES ／ D…；内部名 — | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_FLIGHT` | internal | flight → — | `duration_data` 显示槽 0/3；flags D_DISPELLABLE；内部名 flight | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_FLOODED` | current | Flooded → 淹水 | `duration_data` 显示槽 1/3；flags D_NEGATIVE；内部名 flooded | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_FLOODED_IMMUNITY` | internal | flood immunity → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 flood immunity | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_FORESTED` | current | forested → 召唤森林；显示：森林；召唤森林；你正在召唤森林。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 — | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_FORTITUDE` | internal | old fortitude → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old fortitude | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_FORTRESS_BLAST_TIMER` | internal | fortress blast charging → — | `duration_data` 显示槽 0/3；flags D_DISPELLABLE；内部名 fortress blast charging | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_FROZEN` | current | frozen → 冰封；显示：冰封；你被部分冰封了。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 — | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_FROZEN_RAMPARTS` | current | freezing walls → 冻结墙壁；显示：壁垒；冻结墙壁；你已用冰霜伏击覆盖了附近的墙壁。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE；内部名 frozen ramparts | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_FUGUE` | current | fugue → 赋格；显示：赋格；你的近战和远程攻击被亡者的灵魂所增强。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_EXPIRES；内部名 fugue of the fallen | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_FUSILLADE` | current | raining reagents → 倾泻试剂；显示：齐射；倾泻试剂；你正在释放一连串炼金试剂。 | `duration_data` 显示槽 3/3；flags D_EXPIRES；内部名 fusillade | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_GAVOTTE_COOLDOWN` | current | on gavotte cooldown → 加沃特冷却；显示：-舞步；加沃特冷却；你无法施放加沃特舞曲。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS ／ D_COOLDOWN；内部名 gavotte cooldown | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_GOURMAND` | internal | old gourmand → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old gourmand | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_GOZAG_GOLD_AURA` | current | gold aura → 金币光环笼罩 | `duration_data` 显示槽 1/3；flags D_NO_FLAGS；内部名 — | 修订：补齐显示翻译或统一相关说明术语 |
| `duration:DUR_GRAVE_CLAW_RECHARGE` | internal | grave claw recharging → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 grave claw recharging | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_GROWING_DESTRUCTION` | current | growing destruction → 毁灭增长；显示：毁灭；毁灭增长；你的毁灭之力正变得越来越狂野。 | `duration_data` 显示槽 3/3；flags D_EXPIRES；内部名 growing destruction | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_HASTE` | internal | haste → — | `duration_data` 显示槽 0/3；flags D_DISPELLABLE；内部名 haste | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_HEAVENLY_STORM` | current | in a heavenly storm → 身处天界风暴；显示：身处天界风暴；天界之云正在增强你的精准度和伤害。 | `duration_data` 显示槽 2/3；flags D_NO_FLAGS；内部名 heavenly storm | 修订：补齐显示翻译或统一相关说明术语 |
| `duration:DUR_HELLFIRE_MORTAR_COOLDOWN` | current | on hellfire mortar cooldown → 地狱火迫击炮冷却；显示：-狱火；地狱火迫击炮冷却；你无法施放地狱火迫击炮。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS ／ D_COOLDOWN；内部名 hellfire mortar cooldown | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_HEROISM` | current | heroic → 英雄；显示：英雄；你拥有强大英雄的技能。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 heroism | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_HIVE_COOLDOWN` | current | on swarm cooldown → 虫群冷却；显示：-虫群；虫群冷却；你的蜂群最近来保护你了。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 swarm cooldown | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_HORROR` | current | horrified → 恐惧；显示：恐惧；你感到恐惧，攻击和法术被削弱了。 | `duration_data` 显示槽 3/3；flags D_NEGATIVE；内部名 horror | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_ICEMAIL_DEPLETED` | internal | icemail depleted → — | `duration_data` 显示槽 0/3；flags D_COOLDOWN；内部名 icemail depleted | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_ICY_ARMOUR` | current | ice-armoured → 冰甲；显示：冰甲；你被一层冰霜护甲保护着。 | `duration_data` 显示槽 2/3；flags D_DISPELLABLE ／ D_EXPIRES；内部名 icy armour | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_INFERNAL_LEGION` | current | unleashing the legion → 释放军团；显示：军团；释放军团；你正在召唤混沌军团。 | `duration_data` 显示槽 3/3；flags D_EXPIRES；内部名 infernal legion | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_INFUSION` | internal | old infusion → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old infusion | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_INSULATION` | internal | old insulation → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old insulation | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_INVIS` | internal | invis → — | `duration_data` 显示槽 0/3；flags D_DISPELLABLE；内部名 invis | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_JELLY_PRAYER` | internal | old jelly prayer → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old jelly prayer | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_JINXBITE` | current | jinxed → 厄运缠身；显示：厄运；厄运缠身；你被诅咒精灵包围着。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_EXPIRES；内部名 jinxbite | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_JINXBITE_LOST_INTEREST` | internal | — → — | `duration_data` 显示槽 0/3；flags D_EXPIRES；内部名 — | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_LIFESAVING` | internal | old lifesaving → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old lifesaving | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_LIQUEFYING` | current | liquefying → 液化地面；显示：液化；液化地面；你正在液化脚下的地面。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE；内部名 — | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_LOCKED_DOWN` | internal | old stuck → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old stuck | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_LOWERED_WL` | current | weak-willed → 意志薄弱；显示：意志/2；意志薄弱；你意志薄弱。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 lowered wl | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_MAGIC_ARMOUR` | internal | old magic armour → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old magic armour | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_MAGIC_SAPPED` | internal | old magic sapped → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old magic sapped | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_MAGIC_SHIELD` | internal | old magic shield → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old magic shield | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_MEDUSA_COOLDOWN` | current | on lithotoxin cooldown → 石毒素冷却；显示：-石毒；石毒素冷却；你的石化毒素最近已被激活。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 lithotoxin cooldown | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_MESMERISED` | internal | mesmerised → — | `duration_data` 显示槽 0/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 mesmerised | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_MESMERISE_IMMUNE` | internal | mesmerisation immunity → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 mesmerisation immunity | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_MESMERISM_COOLDOWN` | current | on mesmerism cooldown → 迷魂冷却；显示：-迷魂；迷魂冷却；你的迷魂宝珠暂时耗尽了魔力。 | `duration_data` 显示槽 3/3；flags D_COOLDOWN；内部名 mesmerism cooldown | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_MIGHT` | current | mighty → 强力；显示：强效；强力；你力大无穷。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE；内部名 might | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_MIRROR_DAMAGE` | internal | old injury mirror → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old injury mirror | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_MISLED` | internal | old misled → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old misled | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_NAUSEA` | internal | old nausea → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old nausea | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_NEGATIVE_VULN` | internal | old negative vuln → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old negative vuln | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_NOXIOUS_BOG` | current | spewing sludge → 喷吐泥沼；显示：沼泽；喷吐泥沼；你正在喷射毒沼。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE；内部名 noxious bog | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_NO_CAST` | current | unable to cast spells → 无法施法；显示：-施法；无法施法；你无法施法。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 no cast | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_NO_HOP` | current | unable to hop → 无法跳跃；显示：-跳跃；无法跳跃；你无法跳跃。 | `duration_data` 显示槽 3/3；flags D_COOLDOWN；内部名 no hop | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_NO_MOMENTUM` | current | immotile → 无法移动；显示：-移动；无法移动；你无法移动。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 — | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_NO_POTIONS` | internal | no potions → — | `duration_data` 显示槽 0/3；flags D_NEGATIVE；内部名 no potions | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_NO_SCROLLS` | internal | no scrolls → — | `duration_data` 显示槽 0/3；flags D_NEGATIVE；内部名 no scrolls | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_OBLIVION_HOWL` | current | oblivion-hounded → 被湮灭追逐；显示：嚎叫；被湮灭追逐；一阵可怕的嚎叫在你脑海中回响。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 howl | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_OBLIVION_HOWL_IMMUNITY` | internal | old howl immunity → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old howl immunity | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_OOZEMANCY` | current | calling ooze → 召唤软泥；显示：软泥；召唤软泥；你正在从附近墙壁中召唤软泥。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 oozemancy | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_OOZE_REGEN` | current | ooze regen → 软泥恢复；显示：泥恢；软泥恢复；你被再生软泥覆盖。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 ooze regen | 修订：补齐显示翻译或统一相关说明术语 |
| `duration:DUR_PARAGON_ACTIVE` | internal | paragon active → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 paragon active | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_PARALYSIS` | current | paralysed → 麻痹；显示：麻痹；你处于麻痹状态。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 paralysis | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_PARRYING` | current | parry → 招架中；显示：招架中；你正在格挡攻击，盾牌强度提高。 | `duration_data` 显示槽 2/3；flags D_NO_FLAGS；内部名 parrying | 修订：补齐显示翻译或统一相关说明术语 |
| `duration:DUR_PETRIFIED` | current | petrified → 石化；显示：石化；你被石化了。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 — | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_PETRIFYING` | current | petrifying → 石化中；显示：石化中；你正在变为石像。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_EXPIRES ／ D…；内部名 — | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_PHALANX_BARRIER` | current | phalanx barrier → 方阵屏障 | `duration_data` 显示槽 1/3；flags D_NO_FLAGS；内部名 phalanx barrier | 修订：补齐显示翻译或统一相关说明术语 |
| `duration:DUR_PHASE_SHIFT` | internal | old phase shift → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old phase shift | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_PIETY_POOL` | internal | piety pool → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 piety pool | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_POISONING` | internal | poisoning → — | `duration_data` 显示槽 0/3；flags D_NEGATIVE；内部名 poisoning | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_POISON_VULN` | current | poison vulnerable → 毒素易伤；显示：抗毒-；毒素易伤；你更容易中毒。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 poison vulnerability | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_POWERED_BY_DEATH` | internal | pbd → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 pbd | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_PRIMORDIAL_NIGHTFALL` | current | nightfall → 夜幕降临；显示：夜幕降临；你被原初黑暗包围了。 | `duration_data` 显示槽 3/3；flags D_EXPIRES；内部名 nightfall | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_QAZLAL_AC` | current | protected from physical damage → 物理防护；显示：物理防护；卡兹拉尔正在保护你免受物理伤害。 | `duration_data` 显示槽 2/3；flags D_NO_FLAGS；内部名 qazlal ac | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_QAZLAL_COLD_RES` | current | protected from cold → 寒冷防护；显示：抗寒+；寒冷防护；卡兹拉尔正在保护你免受寒冷伤害。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 qazlal cold resistance | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_QAZLAL_ELEC_RES` | current | protected from electricity → 电击防护；显示：抗电+；电击防护；卡兹拉尔正在保护你免受电击伤害。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 qazlal elec resistance | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_QAZLAL_FIRE_RES` | current | protected from fire → 火焰防护；显示：抗火+；火焰防护；卡兹拉尔正在保护你免受火焰伤害。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 qazlal fire resistance | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_QUAD_DAMAGE` | current | quad damage → 四倍伤害；显示：四倍；四倍伤害 | `duration_data` 显示槽 2/3；flags D_EXPIRES；内部名 — | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_RAMPAGE_HEAL` | internal | rampage heal → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 rampage heal | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_RECITE` | current | reciting → 吟诵中；显示：吟诵；吟诵中；你正在诵读辛的法律公理。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 recite | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_RECITE_COOLDOWN` | current | on recite cooldown → 吟诵冷却；显示：-吟诵；吟诵冷却；你无法诵读。 | `duration_data` 显示槽 3/3；flags D_COOLDOWN；内部名 — | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_REGENERATION` | internal | old regeneration → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old regeneration | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_REPEL_MISSILES` | internal | old repel missiles → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old repel missiles | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_REPEL_STAIRS_CLIMB` | internal | repel stairs climb → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 repel stairs climb | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_REPEL_STAIRS_MOVE` | internal | repel stairs move → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 repel stairs move | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_RESISTANCE` | current | resistant → 抗性；显示：抗性；你对元素有抗性。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_EXPIRES；内部名 resistance | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_RETCHING` | internal | old retching → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old retching | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_REVELATION` | internal | revelation → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 revelation | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_RIME_YAK_AURA` | internal | cold aura → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 cold aura | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_RISING_FLAME` | current | rising → 上升中；显示：升起；上升中；你正在向天花板上升。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 rise | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_SANGUINE_ARMOUR` | current | sanguine armoured → 血甲护体；显示：血甲；血甲护体；你流出的血液附着并保护着你。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 sanguine armour | 修订：补齐显示翻译或统一相关说明术语 |
| `duration:DUR_SAP_MAGIC` | current | magic-sapped → 魔力枯竭；显示：枯竭；魔力枯竭；施法可能导致你失去使用魔法的能力。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 sap magic | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_SCRYING` | internal | old scrying → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old scrying | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_SEE_INVISIBLE` | internal | old see invisible → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old see invisible | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_SENTINEL_MARK` | current | marked → 被标记；显示：标记；被标记；哨兵的标记正在向敌人揭示你的位置。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_EXPIRES ／ D…；内部名 sentinel's mark | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_SHAFT_IMMUNITY` | internal | old shaft immunity → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old shaft immunity | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_SHROUD_OF_GOLUBRIA` | internal | old shroud → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old shroud | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_SHROUD_TIMEOUT` | current | shroud timeout → 黏液护罩破损；显示：护罩；黏液护罩破损；你的黏液屏障已破裂，需要时间修复。 | `duration_data` 显示槽 3/3；flags D_EXPIRES ／ D_COOLDOWN；内部名 shroud timeout | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_SICKENING` | internal | sickening → — | `duration_data` 显示槽 0/3；flags D_NEGATIVE；内部名 sickening | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_SICKNESS` | current | sick → 患病；显示：患病；你的疾病阻止了生命再生。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 sickness | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_SIGN_OF_RUIN` | current | sign of ruin → 毁灭印记；显示：毁灭；毁灭印记；毁灭之印在你受到攻击时使你衰弱。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 ruin | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_SILENCE` | current | silenced → 沉默；显示：沉默；你散发出沉默光环。 | `duration_data` 显示槽 2/3；flags D_DISPELLABLE ／ D_EXPIRES；内部名 silence | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_SIPHON_COOLDOWN` | current | on siphon cooldown → 虹吸冷却；显示：-虹吸；虹吸冷却；你无法吸取精华。 | `duration_data` 显示槽 3/3；flags D_COOLDOWN；内部名 siphon cooldown | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_SLAYING` | internal | old slaying → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old slaying | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_SLEEP` | current | sleeping → 睡眠；显示：睡眠；你正在沉睡。 | `duration_data` 显示槽 2/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 sleep | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_SLEEP_IMMUNITY` | internal | old sleep immunity → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old sleep immunity | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_SLIMIFY` | current | slimy → 粘滑；显示：黏液；粘滑 | `duration_data` 显示槽 2/3；flags D_EXPIRES；内部名 slimify | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_SLIMIFYING` | current | Slimifying → 软化 | `duration_data` 显示槽 1/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 slimifying | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_SLOW` | internal | slow → — | `duration_data` 显示槽 0/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 slow | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_SONG_OF_SHIELDING` | internal | old song of shielding → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old song of shielding | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_SPIKE_LAUNCHER_ACTIVE` | internal | spike launcher → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 spike launcher | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_SPIRIT_HOWL` | internal | old spirit howl → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old spirit howl | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_SPITEFUL_BLOOD_COOLDOWN` | internal | spiteful_blood → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 spiteful_blood | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_SPWPN_PROTECTION` | current | under a protective aura → 受到防护光环保护；显示：受到防护光环保护；你的武器正在散发保护光环。 | `duration_data` 显示槽 2/3；flags D_NO_FLAGS；内部名 protection aura | 修订：补齐显示翻译或统一相关说明术语 |
| `duration:DUR_STABBING` | internal | old stabbing → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old stabbing | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_STARDUST_COOLDOWN` | current | on stardust cooldown → 星尘冷却；显示：-星尘；星尘冷却；你的星尘宝珠暂时耗尽了魔力。 | `duration_data` 显示槽 3/3；flags D_COOLDOWN；内部名 stardust cooldown | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_STEALTH` | current | especially stealthy → 极度潜行；显示：潜行；极度潜行；你特别善于潜行。 | `duration_data` 显示槽 3/3；flags D_NO_FLAGS；内部名 stealth | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_STICKY_FLAME` | current | on fire → 燃烧中；显示：着火；燃烧中；你被液态火焰覆盖了。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 liquid fire | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_STUN_IMMUNITY` | internal | immune to disabling effects → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 immune to disabling effects | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_SURE_BLADE` | internal | old sure blade → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old sure blade | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_SWIFTNESS` | current | swift → 迅捷；显示：迅捷；你可以快速移动。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_EXPIRES；内部名 swiftness | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_TELEPATHY` | internal | old telepathy → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old telepathy | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_TELEPORT` | current | about to teleport → 即将传送；显示：传送；即将传送；你即将传送。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE；内部名 teleport | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_TEMP_CLOUD_IMMUNITY` | internal | temp cloud immunity → — | `duration_data` 显示槽 0/3；flags D_EXPIRES；内部名 temp cloud immunity | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_TEMP_MUTATIONS` | internal | old temporary mutations → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old temporary mutations | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_TIME_STEP` | internal | time step → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 time step | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_TIME_WARPED_BLOOD_COOLDOWN` | internal | time-warped blood cooldown → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 time-warped blood cooldown | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_TOXIC_RADIANCE` | current | radiating poison → 辐射毒素；显示：毒辉；辐射毒素；你正在散发毒性能量。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE；内部名 toxic radiance | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_TRANSFORMATION` | internal | transformation → — | `duration_data` 显示槽 0/3；flags D_DISPELLABLE；内部名 transformation | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_TRICKSTER_GRACE` | internal | trickster → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 trickster | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_TROGS_HAND` | current | strong-willed → 意志坚定；显示：意志坚定；你的意志力大幅增强了。 | `duration_data` 显示槽 2/3；flags D_EXPIRES；内部名 trogs hand | 修订：补齐显示翻译或统一相关说明术语 |
| `duration:DUR_VAINGLORY` | current | no stairs → 拒绝楼梯；显示：虚荣；拒绝楼梯；你拒绝在宣告自己后如此迅速地离开这一层。 | `duration_data` 显示槽 3/3；flags D_EXPIRES ／ D_NEGATIVE；内部名 — | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_VEHUMET_GIFT` | internal | vehumet gift → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 vehumet gift | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_VERTIGO` | current | vertiginous → 眩晕；显示：眩晕；眩晕使你的攻击、施法和闪避更加困难。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 vertigo | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_VEXED` | current | vexed → 恼怒；显示：恼怒；你焦躁不安。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 vex | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_VILE_CLUTCH_OLD` | internal | old vile clutch → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old vile clutch | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_VITRIFIED` | current | fragile (+50% incoming damage) → 脆弱（+50%受伤）；显示：脆弱；脆弱（+50%受伤）；你如玻璃般脆弱。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 vitrified | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_VORTEX` | current | in a vortex → 极地漩涡中；显示：漩涡；极地漩涡中；你正处于极地漩涡的中央。 | `duration_data` 显示槽 3/3；flags D_EXPIRES；内部名 vortex | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_VORTEX_COOLDOWN` | current | on vortex cooldown → 漩涡冷却；显示：-漩涡；漩涡冷却；你无法创造极地漩涡。 | `duration_data` 显示槽 3/3；flags D_COOLDOWN；内部名 vortex cooldown | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_WATER_HOLD_IMMUNITY` | internal | old drowning immunity → — | `duration_data` 显示槽 0/3；flags D_NO_FLAGS；内部名 old drowning immunity | 保留：无玩家显示槽的内部计时身份 |
| `duration:DUR_WEAK` | current | weakened → 虚弱；显示：脆弱；虚弱；你的攻击被削弱了。 | `duration_data` 显示槽 3/3；flags D_DISPELLABLE ／ D_NEGATIVE；内部名 weak | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_WEREFURY` | current | full of bloodlust → 充满嗜血；显示：杀戮；充满嗜血；你的近战攻击被原始嗜血所增强。 | `duration_data` 显示槽 3/3；flags D_EXPIRES ／ D_ATTACK_EXTENDED；内部名 bloodlust | 保留：显示槽、颜色标记与说明准确 |
| `duration:DUR_WORD_OF_CHAOS_COOLDOWN` | current | on word of chaos cooldown → 混沌之语冷却；显示：-混沌；混沌之语冷却；你无法说出混沌之语。 | `duration_data` 显示槽 3/3；flags D_COOLDOWN；内部名 word of chaos cooldown | 保留：显示槽、颜色标记与说明准确 |

## 附加状态证据卡（49）

| 身份 | 生命周期 | 名称与显示形式 | 生产事实 | 终态结论 |
|---|---|---|---|---|
| `status:STATUS_AIRBORNE` | current | Fly → 飞行；显示：飞行；飞行中；你正在飞行。 | `fill_status_info` producer=true；db_key Fly；显示字面量 3 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_AUGMENTED` | current | Aug → 增幅 | `fill_status_info` producer=true；db_key Aug；显示字面量 1 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_BACKLIT` | current | STATUS_BACKLIT → —；显示：发光；你在发光。 | `fill_status_info` producer=true；db_key 动态/无 TextDB 键；显示字面量 2 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_BEHELD` | current | Mesm → 迷魂；显示：迷魂；被迷住；你陷入了迷魂状态。 | `fill_status_info` producer=true；db_key Mesm；显示字面量 3 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_BEOGH` | current | Beogh → 贝奥 | `fill_status_info` producer=true；db_key Beogh；显示字面量 1 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_BLACK_TORCH` | current | Torch → 火炬；显示：火炬；火炬(%d)；火炬点燃 | `fill_status_info` producer=true；db_key Torch；显示字面量 3 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_BRIBE` | current | Bribe → 贿赂；显示：贿赂；贿赂[%s]；、；你正在贿赂：；。 | `fill_status_info` producer=true；db_key Bribe；显示字面量 5 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_CANINE_FAMILIAR_ACTIVE` | current | Dog → 犬灵；显示：犬灵；犬神已召；你的犬神已被召唤。 | `fill_status_info` producer=true；db_key Dog；显示字面量 3 | 修订：长文本纳入 status 上下文翻译 |
| `status:STATUS_CHANNELLING_SPELL` | current | Ray → 射线；显示：火焰波；射线；缠绕 | `fill_status_info` producer=true；db_key Ray、Wave、Winding；显示字面量 3 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_CLAUSTROPHOBIA` | current | STATUS_CLAUSTROPHOBIA → —；显示：恐惧(-%d) | `fill_status_info` producer=true；db_key 动态/无 TextDB 键；显示字面量 1 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_CLOUD` | current | Cloud → 云雾 | `fill_status_info` producer=true；db_key Cloud；显示字面量 1 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_CONSTRICTED` | current | Constr → 束缚；显示：束缚；被根缠绕；被尸手缠绕；被缠绕 | `fill_status_info` producer=true；db_key Constr；显示字面量 4 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_CONTAMINATION` | current | Contam → 诱变辐射 | `fill_status_info` producer=true；db_key Contam；显示字面量 1 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_CORROSION` | current | Corr → 腐蚀；显示：腐蚀(%d)；腐蚀；你被腐蚀了。 | `fill_status_info` producer=true；db_key Corr；显示字面量 5 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_CRUCIBLE_DEBT` | current | Escape! → 逃脱!；显示：契约；逃脱! | `fill_status_info` producer=true；db_key Escape!、Pact；显示字面量 2 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_DIG` | current | Dig → 挖掘 | `fill_status_info` producer=true；db_key Dig；显示字面量 1 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_DRACONIAN_BREATH` | current | Breath → 吐息 | `fill_status_info` producer=true；db_key Breath；显示字面量 1 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_DRAINED` | current | Drain → 衰竭；显示：衰竭；极度削命；你的生命力被极度削弱了。；严重削命；你的生命力被严重削弱了。；重度削命；你的生命力被大幅削弱了。；削命；你的生命力被削弱了。；轻度削命；你的生命力被轻度削弱了。 | `fill_status_info` producer=true；db_key Drain；显示字面量 11 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_DUEL` | current | Duel → 决斗；显示：决斗；决斗中；你正在单挑中。 | `fill_status_info` producer=true；db_key Duel；显示字面量 3 | 修订：长文本纳入 status 上下文翻译 |
| `status:STATUS_GEM` | current | Gem → 远古宝石；显示：宝石(*)；宝石(%d) | `fill_status_info` producer=true；db_key Gem；显示字面量 2 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_GRAVE_CLAW_UNAVAILABLE` | current | -GClaw → -巨爪 | `fill_status_info` producer=true；db_key -GClaw；显示字面量 1 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_HEAVENLY_STORM` | current | STATUS_HEAVENLY_STORM → —；显示：天威(%d) | `fill_status_info` producer=true；db_key 动态/无 TextDB 键；显示字面量 1 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_INVISIBLE` | current | Invis → 隐形；显示：隐形；你现在；。 | `fill_status_info` producer=true；db_key Invis；显示字面量 4 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_IN_DEBT` | internal | STATUS_IN_DEBT → — | `fill_status_info` producer=false；db_key 动态/无 TextDB 键；显示字面量 0 | 保留：枚举保留、无独立 producer |
| `status:STATUS_LIQUEFIED` | current | SlowM → 慢移；显示：慢移；移动减速；在液化地面上你的移动减缓了。 | `fill_status_info` producer=true；db_key SlowM；显示字面量 3 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_LOWERED_WL` | current | Will/2 → 意志/2；显示：意志/2；意志薄弱；你意志薄弱。 | `fill_status_info` producer=true；db_key Will/2；显示字面量 3 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_MANUAL` | current | STATUS_MANUAL → —；显示：学习中；你正在学习：；。 | `fill_status_info` producer=true；db_key 动态/无 TextDB 键；显示字面量 3 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_MNEMOPHAGE` | current | Memories → —；显示：记忆(%d) | `fill_status_info` producer=true；db_key Memories；显示字面量 1 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_NET` | current | Held → 受困；显示：受困；你被%s了。 | `fill_status_info` producer=true；db_key Held；显示字面量 3 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_NO_POTIONS` | current | -Potion → -药水；显示：-药水；无法饮用药水；你无法饮用药水。 | `fill_status_info` producer=true；db_key -Potion；显示字面量 3 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_NO_SCROLL` | current | -Scroll → -卷轴；显示：-卷轴；无法阅读；你无法阅读卷轴。 | `fill_status_info` producer=true；db_key -Scroll；显示字面量 3 | 修订：长文本纳入 status 上下文翻译 |
| `status:STATUS_ORB` | current | Orb → 宝珠；显示：宝珠；宝珠? | `fill_status_info` producer=true；db_key Orb；显示字面量 2 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_OSTRACISM` | current | Ostracised → 被排斥 | `fill_status_info` producer=true；db_key Ostracised；显示字面量 1 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_PEEKING` | current | Peek → 窥视；显示：窥视；窥视中；你正在朝楼梯下窥视。 | `fill_status_info` producer=true；db_key Peek；显示字面量 3 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_REGENERATION` | current | -Regen → -再生；显示：再生 意志++；再生中；你正在恢复生命。；-再生；恢复受阻；你的恢复被附近的怪物抑制了。 | `fill_status_info` producer=true；db_key -Regen、Regen Will++；显示字面量 6 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_REV` | current | Rev → 暖机；显示：暖机；加速中；你开始热身。；暖机+；你正在热身。；暖机*；运转中；你已完全热身。 | `fill_status_info` producer=true；db_key Rev；显示字面量 8 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_RF_ZERO` | current | rF0 → 无抗火；显示：无抗火；火焰易伤；你无法抵抗火焰。 | `fill_status_info` producer=true；db_key rF0；显示字面量 3 | 修订：长文本纳入 status 上下文翻译 |
| `status:STATUS_SERPENTS_LASH` | current | STATUS_SERPENTS_LASH → —；显示：鞭击(%u)；蛇之鞭；你以超自然速度移动。 | `fill_status_info` producer=true；db_key 动态/无 TextDB 键；显示字面量 3 | 修订：长文本纳入 status 上下文翻译 |
| `status:STATUS_SHROUD` | current | Shroud → 护罩；显示：护罩；黏液护罩 | `fill_status_info` producer=true；db_key Shroud；显示字面量 2 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_SILENCE` | current | Sil → 沉默；显示：沉默；你被沉默了。 | `fill_status_info` producer=true；db_key Sil；显示字面量 3 | 修订：长文本纳入 status 上下文翻译 |
| `status:STATUS_SPEED` | current | Fast → 加速；显示：加速+减速；加速且减速；你同时受到减速和加速效果。；减速；你被减速了。；加速；加速中；你的行动被加速了。 | `fill_status_info` producer=true；db_key Fast、Fast+Slow、Slow；显示字面量 9 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_STAT_ZERO` | current | Crippled → 残废；显示：残废；迷失%s；你已经没有%s了！ | `fill_status_info` producer=true；db_key Crippled；显示字面量 3 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_STILL_WINDS` | current | -Clouds → -云雾 | `fill_status_info` producer=true；db_key -Clouds；显示字面量 1 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_SUNDER_READY` | current | Sunder → 碎裂 | `fill_status_info` producer=true；db_key Sunder；显示字面量 1 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_TERRAIN` | current | Lava → 熔岩；显示：水域；熔岩 | `fill_status_info` producer=true；db_key Lava、Water；显示字面量 2 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_TESSERACT` | current | Tesseract → 超立方体 | `fill_status_info` producer=true；db_key Tesseract；显示字面量 1 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_TRICKSTER` | current | STATUS_TRICKSTER → —；显示：诡术(+%d甲)；散布的厄运强化了你（AC +%d） | `fill_status_info` producer=true；db_key 动态/无 TextDB 键；显示字面量 2 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_UMBRA` | current | STATUS_UMBRA → —；显示：暗影缠绕；你被暗影环绕着。 | `fill_status_info` producer=true；db_key 动态/无 TextDB 键；显示字面量 2 | 保留：生产条件、显示文本与 TextDB 键准确 |
| `status:STATUS_ZOT` | current | Zot → 佐特领域；显示：沉醉；佐特正在逼近！；佐特(%d) | `fill_status_info` producer=true；db_key Zot；显示字面量 3 | 保留：生产条件、显示文本与 TextDB 键准确 |

## 怪物状态证据卡（139）

| 身份 | 生命周期 | 名称与显示形式 | 生产事实 | 终态结论 |
|---|---|---|---|---|
| `monster_status:ablaze with memories monstatus` | current | ablaze with memories monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物暂时获得了施放特定法术的能力。 一旦受到足够伤害，它将再次失去这些能力。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:about to teleport monstatus` | current | about to teleport monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：短暂延迟后，这个生物将被传送到当前楼层的其他地方。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:afflicted by rimeblight monstatus` | current | afflicted by rimeblight monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物每回合受到无视AC的寒冷伤害，有时会爆发出寒冰冲击，伤害附近的盟友。 当它死亡时，可能会将霜疫传播给其他附近的盟友。 自然、恶魔或神圣… | 保留：状态语义、效果说明与术语准确 |
| `monster_status:ally target monstatus` | current | ally target monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物正被你的一个或多个盟友锁定为目标。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:anguished monstatus` | current | anguished monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：当这个生物造成伤害时，它将受到等同于其所造成伤害量的伤害。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:asleep monstatus` | current | asleep monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物无法移动、行动、格挡或闪避。任何敌对行为都会唤醒它， 但对它的近战攻击（即使是来自其他怪物的）会造成更高的伤害。 [[high-tie… | 保留：状态语义、效果说明与术语准确 |
| `monster_status:berserk monstatus` | current | berserk monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的生命值提升50%，近战攻击伤害提升50%，移动和行动速度提升50%。 除了移动和攻击之外，它们无法执行任何其他动作。 当狂暴消退后，… | 保留：状态语义、效果说明与术语准确 |
| `monster_status:blind monstatus` | current | blind monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物无法正常视物。其命中率大幅降低，无法进行借机攻击， 施放的法术有时可能会瞄准错误的位置。 它也可能会踉跄而行，最终失去对目标的追踪，尤… | 保留：状态语义、效果说明与术语准确 |
| `monster_status:bound in place monstatus` | current | bound in place monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物无法依靠自身力量移动，但仍可以使用传送或被他者强行位移。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:called by a tesseract monstatus` | current | called by a tesseract monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个怪物是从平行现实召唤而来的。击杀它不会获得经验值， 但当超立方体被摧毁后，它会被立即送回原来的现实。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:catching her breath monstatus` | current | catching her breath monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：[[catching its breath monstatus]] | 保留：状态语义、效果说明与术语准确 |
| `monster_status:catching his breath monstatus` | current | catching his breath monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：[[catching its breath monstatus]] | 保留：状态语义、效果说明与术语准确 |
| `monster_status:catching its breath monstatus` | current | catching its breath monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物最近使用过吐息能力，短时间内无法再次使用。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:catching their breath monstatus` | current | catching their breath monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：[[catching its breath monstatus]] | 保留：状态语义、效果说明与术语准确 |
| `monster_status:chanting recall monstatus` | current | chanting recall monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物正在吟唱召回之词。这会在短暂延迟后将楼层中其他地方的 有智力的盟友召唤到施法者附近，但可以被大多数阻止施法的效果打断。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:charmed monstatus` | current | charmed monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被魅惑了，会短暂地为你的目标而战。如果你以任何方式试图伤害它， 效果会立即消失。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:concentrated venom monstatus` | current | concentrated venom monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的天然毒液被强化了，使其通过攻击或吐息武器施加的毒素 有概率减速和窒息易受影响的目標。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:confused monstatus` | current | confused monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物无法格挡或使用法术和能力，会随机踉跄而行，攻击撞到的任何东西—— 无论是友方、敌方，有时甚至是它们自己。 [[low-tier sta… | 保留：状态语义、效果说明与术语准确 |
| `monster_status:constricted by roots monstatus` | current | constricted by roots monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物正被树根缠绕，降低了它们的闪避并每回合造成一些伤害。 也可能阻止它们移动，但每次尝试移动都有概率完全打破此效果。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:constricted by zombie hands monstatus` | current | constricted by zombie hands monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物正被从地底深处伸出的死尸之手缠绕，降低了它们的闪避并每回合 造成一些伤害。也可能阻止它们移动，但每次尝试移动都有概率完全打破此效果。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:contaminated monstatus` | current | contaminated monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物已被变形能量污染，每当第三次被施加此类能量时将受到显著伤害。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:control wrested from you monstatus` | current | control wrested from you monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个原本友好的生物被其他生物魅惑了，加入了对方阵营。 如果你杀死魅惑的来源，它会恢复神智。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:corroded monstatus` | current | corroded monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的AC降低了8点。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:covered in liquid flames monstatus` | current | covered in liquid flames monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被粘性火焰覆盖，每回合受到无视AC的火焰伤害。 移动会甩掉火焰，使其更快熄灭；踏入水中则会完全熄灭火焰。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:covered in magnetic dust monstatus` | current | covered in magnetic dust monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物无法闪避攻击或隐身。如果它死亡，会留下一团磁化碎片云。 每次施放磁暴时，会向这个生物自动射出一道闪电束。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:covered in terrible wounds monstatus` | current | covered in terrible wounds monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被剥皮幽灵施加了幻觉伤口。这些伤口会随着时间流逝消失， 或者在剥皮幽灵被摧毁时消失。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:covering ground quickly monstatus` | current | covering ground quickly monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的移动速度略微加快。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:covering ground slowly monstatus` | current | covering ground slowly monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物陷入液化地面中，移动速度减慢，其25%的近战攻击会失手。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:crumbling away monstatus` | current | crumbling away monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物将在几回合后自动被摧毁。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:cursed with the promise of agony monstatus` | current | cursed with the promise of agony monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被诅咒了，在诅咒来源的下一次近战攻击命中后将失去其当前生命值的一半。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:damage-immune at range monstatus` | current | damage-immune at range monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：除非伤害的原始来源与这个生物相邻，否则无论以何种方式都无法对其造成伤害。 不造成伤害的附带效果仍会正常发生。 （云雾和狐火等类投射物怪物的伤害… | 保留：状态语义、效果说明与术语准确 |
| `monster_status:dazed monstatus` | current | dazed monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物暂时无法行动，但任何敌对行为将使其立即恢复神智。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:diminished spells monstatus` | current | diminished spells monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的法术威力降低——造成的伤害更少，更难以克服目标的意志力， 并在其他方面偶尔变弱。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:dormant monstatus` | current | dormant monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：[[asleep monstatus]] | 保留：状态语义、效果说明与术语准确 |
| `monster_status:doubled in vigour monstatus` | current | doubled in vigour monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个怪物的当前和最大生命值暂时翻倍。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:empowered by the touch of beogh monstatus` | current | empowered by the touch of beogh monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被贝奥格赋予了强大的力量来挑战你。它们的近战和远程攻击伤害 提升33%，生命值增加，施法更频繁。它们还能追踪你，无论你逃到当前楼层 的… | 保留：状态语义、效果说明与术语准确 |
| `monster_status:encased in ice monstatus` | current | encased in ice monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被瞬间冻结，其移动速度在短时间内大幅降低。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:entangled in a net monstatus` | current | entangled in a net monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被网缠住了，大大降低了闪避能力并阻止其格挡。 任何移动或攻击的尝试都会转而挣扎于网中，最终可能摧毁网。 施法不受影响。 [[low-t… | 保留：状态语义、效果说明与术语准确 |
| `monster_status:entangled in a web monstatus` | current | entangled in a web monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被蜘蛛网缠住了，大大降低了闪避能力并阻止其格挡。 任何移动或攻击的尝试都会转而挣扎于网中，最终可能摧毁网。 施法不受影响。 [[low… | 保留：状态语义、效果说明与术语准确 |
| `monster_status:extremely poisoned monstatus` | current | extremely poisoned monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物每回合受到毒素伤害，且无法被进一步中毒。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:fast monstatus` | current | fast monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的行动和移动速度提升50%。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:feeble figment monstatus` | current | feeble figment monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物只是另一个生物的脆弱复制体。其生命值减少66%，攻击伤害减少33%， 法术威力显著减弱。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:flame-wreathed monstatus` | current | flame-wreathed monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被曳焰的火焰强化了。其近战攻击造成额外火焰伤害，移动速度提升33%， AC和火焰抗性提高。 | 修订：神名与状态术语已校准 |
| `monster_status:fleeing monstatus` | current | fleeing monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物因恐惧而逃跑，每回合都会尝试远离恐惧来源。除移动外， 它只能施放认为有助于逃跑的法术，比如闪烁。 如果被直接伤害或被地形逼入绝境，它会… | 保留：状态语义、效果说明与术语准确 |
| `monster_status:fragile as glass monstatus` | current | fragile as glass monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物受到的所有来源伤害增加50%。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:frenzied and wild monstatus` | current | frenzied and wild monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物近战攻击伤害提升50%，移动和攻击速度提升50%。它无法施法， 每回合会优先攻击最近的生物，无论对方是友方还是敌方。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:fully charged monstatus` | current | fully charged monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物已积攒了施法所需的全部能量。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:grapneled monstatus` | current | grapneled monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被动能抓钩击中了。来自抓钩来源的下一次近战攻击将必定命中 并造成略微增加的伤害。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:heavily contaminated monstatus` | current | heavily contaminated monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：[[contaminated monstatus]] | 保留：状态语义、效果说明与术语准确 |
| `monster_status:heavily drained monstatus` | current | heavily drained monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被严重削弱，其近战攻击命中率降低，法术和特殊攻击属性威力降低， 并且更容易受到许多状态效果的影响。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:high-tier stab monstatus` | current | high-tier stab monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：<blue>你对该生物进行的近战攻击将造成大幅增加的伤害，使用短剑时效果尤佳。</blue> | 保留：状态语义、效果说明与术语准确 |
| `monster_status:idealised monstatus` | current | idealised monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物闪耀着完美自我的光辉。其近战攻击伤害提升100%，拥有额外的AC， 施法威力大幅增强。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:incited by gozag monstatus` | current | incited by gozag monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物因戈扎格·伊姆·萨戈兹之怒而被激发至极高的速度。 它们的加速或狂暴状态是永久的，不会随时间或通过刻意的魔法干预而消退。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:indifferent monstatus` | current | indifferent monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物既不敌对也不友好，如果碰到任何生物，无论对方的立场如何都可能攻击。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:infested monstatus` | current | infested monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被一只死亡圣甲虫寄生，虫将在其死后从尸体中钻出。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:inner flame monstatus` | current | inner flame monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：每当这个生物受到伤害时，其身下会短暂出现一团火焰云。 当它死亡时，会爆发出猛烈的火焰爆炸，伤害附近的一切并留下更多火焰云。 巨型生物死亡时会引… | 保留：状态语义、效果说明与术语准确 |
| `monster_status:inspiring fear monstatus` | current | inspiring fear monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：你当前对这个生物感到极度恐惧，无法故意靠近它，你对其33%的近战攻击会失败。 如果你失去这个生物的视野，此效果会消失。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:interlaced with chaos monstatus` | current | interlaced with chaos monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的近战攻击可能会造成随机元素的额外伤害，或引发各种不可抵抗的状态效果。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:lashing out in frustration monstatus` | current | lashing out in frustration monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被魔法激怒了，每回合被迫攻击一个随机的相邻位置，而不是执行其他动作。 它更可能攻击有生物的位置而非空格，但会同样毫不犹豫地攻击自己的盟… | 保留：状态语义、效果说明与术语准确 |
| `monster_status:lightly drained monstatus` | current | lightly drained monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被轻度削弱，其近战攻击命中率略有下降，法术和特殊攻击属性威力有所降低， 并且稍微更容易受到许多状态效果的影响。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:lost in madness monstatus` | current | lost in madness monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被辛的力量逼疯了。它将再也不会使用法术或能力，会随机踉跄而行， 攻击撞到的任何东西——无论是友方、敌方，有时甚至是它们自己。 | 修订：神名统一为“辛” |
| `monster_status:low-tier stab monstatus` | current | low-tier stab monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：<blue>你对该生物进行的近战攻击有概率（与你的潜行和武器技能成正比）使其措手不及， 造成额外伤害，使用短剑时效果尤佳。</blue> | 保留：状态语义、效果说明与术语准确 |
| `monster_status:magic disrupted monstatus` | current | magic disrupted monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的法术和魔法能力已被打断，使用时有概率失败。 失败概率取决于此效果的剩余持续时间。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:magic-sapped monstatus` | current | magic-sapped monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的魔法通道被污染了。每当它施放法术时，其魔法会被严重打断， 使其后续施放的法术很可能失败。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:marked with the sign of ruin monstatus` | current | marked with the sign of ruin monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被诅咒为注定的衰败与毁灭。每当其受到近战攻击伤害时， 将被严重削弱，并且被减速、虚弱或致盲。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:mesmerising monstatus` | current | mesmerising monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物已经迷住了你，使你无法主动远离它。 如果你失去这个生物的视野，此效果会消失。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:minion monstatus` | current | minion monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物是由魔法创造的，一旦其创造者死亡就会消失。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:misshapen and mutated monstatus` | current | misshapen and mutated monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的AC降低了8点，其命中率、法术威力、武器特效伤害和意志力均中度降低。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:missing a shadow monstatus` | current | missing a shadow monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的影子被夺走了，它再也无法受到无光傀儡的影响。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:more vulnerable to fire monstatus` | current | more vulnerable to fire monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的火焰抗性降低了一级。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:more vulnerable to poison monstatus` | current | more vulnerable to poison monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的毒素抗性降低了一级。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:mute monstatus` | current | mute monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被辛的力量永久地沉默了。这将阻止该生物发出的一切噪音， 包括大多数生物施法所需的发声。 | 修订：神名统一为“辛” |
| `monster_status:not watching you monstatus` | current | not watching you monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被其他事物短暂地分散了注意力。 [[low-tier stab monstatus]] | 保留：状态语义、效果说明与术语准确 |
| `monster_status:paralysed monstatus` | current | paralysed monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物无法移动、行动、格挡或闪避攻击。 [[high-tier stab monstatus]] | 保留：状态语义、效果说明与术语准确 |
| `monster_status:paralysed with fear monstatus` | current | paralysed with fear monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：[[paralysed monstatus]] | 保留：状态语义、效果说明与术语准确 |
| `monster_status:partially charged monstatus` | current | partially charged monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物已积攒了施放法术或激活能力所需的部分能量。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:peaceful monstatus` | current | peaceful monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物永远不会攻击你，可能会攻击对你敌对的生物，但既不会跟随你， 也不会服从任何直接指令。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:petrified monstatus` | current | petrified monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物无法移动、行动、格挡或闪避攻击。由于变成了石头，它受到的伤害 减少50%，免疫负能量和毒素，但变得容易被瓦解伤害。 [[high-ti… | 保留：状态语义、效果说明与术语准确 |
| `monster_status:petrifying slowly monstatus` | current | petrifying slowly monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物很快就会完全石化。其移动和行动速度减慢50%，几乎无法闪避攻击， 但也受到33%的伤害减免。 [[low-tier stab mons… | 保留：状态语义、效果说明与术语准确 |
| `monster_status:poisoned monstatus` | current | poisoned monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物每回合受到毒素伤害。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:radiating silence monstatus` | current | radiating silence monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被一圈不自然的沉默力场环绕，力场内消除所有噪音， 阻止许多生物（包括你）阅读卷轴、施法或祈求神助所需的发声。 如果此效果是由法术引起的… | 保留：状态语义、效果说明与术语准确 |
| `monster_status:radiating toxic energy monstatus` | current | radiating toxic energy monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物闪耀着奥尔格雷布之毒辐射的光芒，将在数回合内持续对视野中的所有 敌人造成毒素伤害。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:ready to become your apostle monstatus` | current | ready to become your apostle monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物在光荣的战斗中被击败，可以通过能力菜单招募为你的使徒。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:ready to howl monstatus` | current | ready to howl monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物尚未对你施加湮灭嚎叫，可能会尝试这样做。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:ready to sunder monstatus` | current | ready to sunder monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的崩裂武器已完全充能，其下一次攻击将更加精准、造成大幅增加的伤害、 并且劈砍范围扩大。如果它移动了，此效果将消失。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:reflecting blocked projectiles monstatus` | current | reflecting blocked projectiles monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物将任何被格挡的投射物反射回其原始来源。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:reflecting injuries monstatus` | current | reflecting injuries monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：每当这个生物受到伤害时，它会将伤害量的三分之二反射回造成伤害的来源。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:regenerating monstatus` | current | regenerating monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物以与其最大生命值成比例的大幅提高的速度恢复生命值。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:repelling missiles monstatus` | current | repelling missiles monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物在闪避投射物（无论是物理还是魔法）时拥有+15 EV。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:retreating monstatus` | current | retreating monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被命令向指定方向撤退，在获得新指示或行进足够距离之前， 它不会攻击或回到你身边。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:rolling monstatus` | current | rolling monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物蜷成了一个球，移动速度和近战伤害提升100%， 直到下一次攻击某物（或无法移动为止）。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:sharing her pain monstatus` | current | sharing her pain monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：[[sharing its pain monstatus]] | 保留：状态语义、效果说明与术语准确 |
| `monster_status:sharing his pain monstatus` | current | sharing his pain monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：[[sharing its pain monstatus]] | 保留：状态语义、效果说明与术语准确 |
| `monster_status:sharing its pain monstatus` | current | sharing its pain monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物将所受伤害的一部分分摊给附近的盟友，离它越近的盟友承受越多。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:sharing their pain monstatus` | current | sharing their pain monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：[[sharing its pain monstatus]] | 保留：状态语义、效果说明与术语准确 |
| `monster_status:sheltered from injuries monstatus` | current | sheltered from injuries monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物受到的一半伤害被转移到保护它的盟友身上。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:sick monstatus` | current | sick monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物生病了，无法自然恢复生命值。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:silenced monstatus` | current | silenced monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被一片不自然的沉默力场吞没了，阻止其发出任何噪音， 包括大多数生物施法所需的发声。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:skewered by barbs monstatus` | current | skewered by barbs monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物在移动时都会受到少量伤害。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:slightly transparent monstatus` | current | slightly transparent monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物通常是隐形的，但你的魔法视力让你仍然可以看到它。 这对你没有任何影响，但你的盟友可能无法像你一样看到它。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:slow monstatus` | current | slow monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物以正常速度的66%移动和行动。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:softly glowing monstatus` | current | softly glowing monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被光环勾勒出来，更容易被击中，如果是隐形状态也会暴露出来。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:soul bound monstatus` | current | soul bound monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的灵魂被束缚在寒冰中。当它死亡时，一个其原形态的拟像将从其 所在位置升起。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:soul-gripped monstatus` | current | soul-gripped monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的灵魂将在死后被迫为你服务，但如果它超出你的视线范围 超过短暂的一瞬，你将失去对它的掌控。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:soul-splintered monstatus` | current | soul-splintered monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的一部分灵魂被提取成了灵魂光球，在光球重新与它结合之前， 无法再次使用此法术。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:spells diminished monstatus` | current | spells diminished monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的法术威力显著减弱。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:spells empowered monstatus` | current | spells empowered monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的法术被增强了，施法频率也会增加。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:stilling the winds monstatus` | current | stilling the winds monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物正在阻止当前楼层产生任何云雾。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:strong monstatus` | current | strong monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的近战攻击伤害提升50%。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:strong-willed monstatus` | current | strong-willed monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的意志力提升了2档。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:stupefied monstatus` | current | stupefied monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物被辛的力量震慑而无法行动。 [[high-tier stab monstatus]] | 修订：神名统一为“辛” |
| `monster_status:surrounded by a freezing vortex monstatus` | current | surrounded by a freezing vortex monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物是毁灭性极地漩涡的中心。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:surrounded by acidic fog monstatus` | current | surrounded by acidic fog monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物周围环绕着一圈酸性雾气云。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:surrounded by chaotic energy monstatus` | current | surrounded by chaotic energy monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物周围环绕着一圈沸腾的混沌云。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:surrounded by flames monstatus` | current | surrounded by flames monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物周围环绕着一圈火焰云。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:surrounded by fog monstatus` | current | surrounded by fog monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物周围环绕着一圈紫色烟雾。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:surrounded by foul miasma monstatus` | current | surrounded by foul miasma monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物周围环绕着一圈恶臭瘴气。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:surrounded by freezing clouds monstatus` | current | surrounded by freezing clouds monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物周围环绕着一圈冰冻云。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:surrounded by mutagenic energy monstatus` | current | surrounded by mutagenic energy monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物周围环绕着一圈变异雾气。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:surrounded by negative energy monstatus` | current | surrounded by negative energy monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物周围环绕着一圈极度痛苦的负能量云。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:surrounded by restless winds monstatus` | current | surrounded by restless winds monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物最近施放了极地漩涡，短时间内无法再次施放。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:surrounded by thunder monstatus` | current | surrounded by thunder monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物周围环绕着一圈雷电云。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:target of orcish vengeance monstatus` | current | target of orcish vengeance monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物参与了杀害你的一位使徒。击败所有兽人复仇目标将显著加快 贝奥格复活你使徒的时间。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:targeted by your dimensional bullseye monstatus` | current | targeted by your dimensional bullseye mon…；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：每当你对另一个生物进行远程攻击时，投射物的一个副本将在其飞行结束时 被传送到这个生物身上。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:tempered monstatus` | current | tempered monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的近战攻击伤害提升25%，命中率略微提高，法术和能力被轻度增强。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:touched by paradox monstatus` | current | touched by paradox monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物在空间中失去了锚定，使其能够将多重攻击作为天生能力使用。 每当它这样做时，有33%的概率也会闪烁到附近随机位置。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:unable to breathe monstatus` | current | unable to breathe monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物无法呼吸，不能施法或祈求神助。每回合还会受到少量窒息伤害。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:unable to see you monstatus` | current | unable to see you monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物因为你隐身而看不到你。它对你的命中率大幅降低，无法进行借机攻击， 施放的法术有时可能会瞄准错误的位置。 它也可能会踉跄而行，最终失去对… | 保留：状态语义、效果说明与术语准确 |
| `monster_status:unable to translocate monstatus` | current | unable to translocate monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物无法闪烁或传送。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:unaffected by silence monstatus` | current | unaffected by silence monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：尽管被不自然的沉默力场吞没，这个生物的魔法不需要发声，因此不受影响。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:unrewarding monstatus` | current | unrewarding monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物在被杀死时不提供经验值或虔诚值。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:untethered in space monstatus` | current | untethered in space monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：每回合，这个生物会向远离你的方向闪烁一小段距离，并受到少量伤害。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:unusually agile monstatus` | current | unusually agile monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的闪避略微提升。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:unusually resistant monstatus` | current | unusually resistant monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物对火焰、寒冷、毒素、电击和腐蚀的抗性都提升了一级。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:very poisoned monstatus` | current | very poisoned monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物中毒了，每回合将受到伤害。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:weak monstatus` | current | weak monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的近战攻击伤害降低33%。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:weak-willed monstatus` | current | weak-willed monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物的意志力降低了一半。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:winding a clockwork bee monstatus` | current | winding a clockwork bee monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物正在准备发射一只发条蜜蜂，必须专注于这个任务数回合。 大多数阻止该生物施法的效果也会中断这个进程。 | 保留：状态语义、效果说明与术语准确 |
| `monster_status:withering away monstatus` | current | withering away monstatus；中文说明已配对 | 英文/中文 TextDB 一一配对；说明：这个生物将在几回合后死亡。 | 保留：状态语义、效果说明与术语准确 |

<!-- BEGIN STRICT REVIEW EVIDENCE v1 -->
{"baseline":"76c815b2ac79d11a8066597ad04d127a1636e153","glossary_sha256":"4070a396e65a4bdf1fd2dfbc9e95bcc40053391e65441053f73c08146ed31d9e","identity_count":696,"inventory_sha256":"0ae072d63a8a7606a48760b5391aebd0913498c178c59df62f2511421b408639"}
```jsonl
{"fact_sha256":"f666db6e05027d87e75f2accbe661c0bcef11a0e22e07854dbff254e18b1ad20","identity":"ability:ABIL_BAT_SWARM","terminal_conclusion":"adjust"}
{"fact_sha256":"e7f4f548944e3af58d29ceb28bb38907262ac568622f5bd3e4fe30c219feedb5","identity":"ability:ABIL_BESTIAL_TAKEDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"a4a1cf5d9d337e4bf4b434e11f97e2258a6dd69c278a24ed72d33fc134c9d0bf","identity":"ability:ABIL_BLINKBOLT","terminal_conclusion":"adjust"}
{"fact_sha256":"238b50a6aabff588a36e28984749a93256626d9696e937123ab4cbb470a5dde4","identity":"ability:ABIL_BREATHE_POISON","terminal_conclusion":"adjust"}
{"fact_sha256":"907112d7397994f76c8a502375ba6cb79ac7876b5d1dce28f15b259bbdd6f11c","identity":"ability:ABIL_BREATHE_RUST","terminal_conclusion":"adjust"}
{"fact_sha256":"d5ba03ca31cb5c3a84aa1c2cb43e346e9fa1f9c2ebb54796b7bb5dfac9fbb131","identity":"ability:ABIL_CACOPHONY","terminal_conclusion":"retranslate"}
{"fact_sha256":"a5ddcf286d3b0e40733e364aadd1806a4a50396a4267a805455d46d3c90ee55d","identity":"ability:ABIL_CAUSTIC_BREATH","terminal_conclusion":"keep"}
{"fact_sha256":"d82bfae053aba3dbb3adf2236b9b9a14c16e36a077ab459c7cac372c06120988","identity":"ability:ABIL_COMBUSTION_BREATH","terminal_conclusion":"keep"}
{"fact_sha256":"1db917b21dfad6d4edf078bb6f142945a0d3571ad3014b6b9cbcad3127b8c8b0","identity":"ability:ABIL_DAMNATION","terminal_conclusion":"keep"}
{"fact_sha256":"d9f454a5c306d6e330bac49c4010b2627a826a884d048b293df27c90feb9c07c","identity":"ability:ABIL_DIG","terminal_conclusion":"retranslate"}
{"fact_sha256":"03c05b28141d41af1f9a4c61b5c7b7294ad7582bead9c13de37c47f2067ed11a","identity":"ability:ABIL_END_TRANSFORMATION","terminal_conclusion":"keep"}
{"fact_sha256":"4ca76e38e2d59bb42458147bcc2b79676678a5809044af330f93642a1f01417a","identity":"ability:ABIL_ENKINDLE","terminal_conclusion":"adjust"}
{"fact_sha256":"727f2631219c6b14bc86a88e7a001980fd42aea91a4f6404b5cbd3decc3165c7","identity":"ability:ABIL_EVOKE_BLINK","terminal_conclusion":"retranslate"}
{"fact_sha256":"2b18648c8aa6e876b3c72d006fa9cf6094196abed65aad716b9915b2e12062c1","identity":"ability:ABIL_EVOKE_DISPATER","terminal_conclusion":"retranslate"}
{"fact_sha256":"c8d7e1b5be3d6b3598aba508308cd7cebe057f777646ac201e078747cef1789b","identity":"ability:ABIL_EVOKE_OLGREB","terminal_conclusion":"adjust"}
{"fact_sha256":"0f02216a1e62de1ecbad93eac8138637a370f19f3d6be88e3c2391c3cc0f98a7","identity":"ability:ABIL_EVOKE_TURN_INVISIBLE","terminal_conclusion":"adjust"}
{"fact_sha256":"ef73e50b96b97578699acf0a6ca78166667a0070a7b897f3678c351622d19ae4","identity":"ability:ABIL_GALVANIC_BREATH","terminal_conclusion":"adjust"}
{"fact_sha256":"ce604fe9e1f65288323a608cb4bfa30a0f6275e9c7eca266dc0dd39940cdac6a","identity":"ability:ABIL_GLACIAL_BREATH","terminal_conclusion":"adjust"}
{"fact_sha256":"dffecd7d3ebd573a54131388dc236a312c94183d2e40c984503aa0910dcf9abe","identity":"ability:ABIL_GOLDEN_BREATH","terminal_conclusion":"keep"}
{"fact_sha256":"b246a4cfd06c9a2c52e3e385f0984f67faadd9e0b103d252ea3d71cfe80e9064","identity":"ability:ABIL_HEAL_WOUNDS","terminal_conclusion":"adjust"}
{"fact_sha256":"1978bd09cabe09a4d03f253f6756fadc27757d2e615f76d919db18a7c076f34a","identity":"ability:ABIL_HOP","terminal_conclusion":"adjust"}
{"fact_sha256":"01e6394517a95c37a2b28d77a0389b7c22760c41a00c15c894571ea7f2f78aa2","identity":"ability:ABIL_IMBUE_SERVITOR","terminal_conclusion":"keep"}
{"fact_sha256":"19b1b82b81c882024385cf39835ebc52ad92fbc721de75464b785a40f090b09e","identity":"ability:ABIL_IMPRINT_WEAPON","terminal_conclusion":"adjust"}
{"fact_sha256":"76e74f7573999c81d943e6fe8be7ff5a01968e43faa3911fda0a26beaa31bdf3","identity":"ability:ABIL_INVENT_GIZMO","terminal_conclusion":"adjust"}
{"fact_sha256":"d65aed4ae3110d7737a85ecc67bdfc7f293f9bbce34e90db6f12cb82a948dcbb","identity":"ability:ABIL_MUD_BREATH","terminal_conclusion":"keep"}
{"fact_sha256":"7b128eede6d6ea9aabc5524449fb482aa4f71aaab6d419f5ed13572928cfda92","identity":"ability:ABIL_NON_ABILITY","terminal_conclusion":"keep"}
{"fact_sha256":"d2709f82b258ae5a6bf666c3de77437996dd3e371f29129ec55692cea2249c91","identity":"ability:ABIL_NOXIOUS_BREATH","terminal_conclusion":"adjust"}
{"fact_sha256":"918e3df063e1548f3d097d5bddf29217dd72c5fa534b4eccf1e017bdf941309c","identity":"ability:ABIL_NULLIFYING_BREATH","terminal_conclusion":"adjust"}
{"fact_sha256":"40ea5e6ddcdd1f79df9183396aa32648f3dbcc761ad707dbb8a07f8c7902e23b","identity":"ability:ABIL_SHAFT_SELF","terminal_conclusion":"retranslate"}
{"fact_sha256":"d044c212bc1091c1c3cb33b3410eb5b7fe62b629d8b5da9b631af91c001c0fe7","identity":"ability:ABIL_SIPHON_ESSENCE","terminal_conclusion":"adjust"}
{"fact_sha256":"f6e83cbabbf41398eaae3662b332fa71fc160f6eff1f2bcc610325a7a336bc32","identity":"ability:ABIL_SPIDER_JUMP","terminal_conclusion":"adjust"}
{"fact_sha256":"f60378d763e15f21a28a42dc6e5583ffa9ccf81df058773e9801728ab040636a","identity":"ability:ABIL_SPIT_POISON","terminal_conclusion":"keep"}
{"fact_sha256":"579b76b46565cc4ebbc6d20f3d68acf325ef92f864afb9e0106b2b507b5c0c3c","identity":"ability:ABIL_STEAM_BREATH","terminal_conclusion":"keep"}
{"fact_sha256":"1c57c8c34914ae3b305458fb954ed84b25749c5c92afa84383b47e0f215838c9","identity":"ability:ABIL_WATERY_GRAVE","terminal_conclusion":"adjust"}
{"fact_sha256":"0ecda84192ec1bc606856b49e9deebbb29eec5204e73d4c994a5b39d61edd70b","identity":"ability:ABIL_WORD_OF_CHAOS","terminal_conclusion":"retranslate"}
{"fact_sha256":"ec28300db1da3f08e8e38792ef9cc135c60e5e8b8d08a6e1ed9ba307a17029a6","identity":"attribute:STAT_DEX","terminal_conclusion":"keep"}
{"fact_sha256":"515e8676215aef774b18530c1a7e19f8b5d01a93e2f5a294df975639df6ecab9","identity":"attribute:STAT_INT","terminal_conclusion":"keep"}
{"fact_sha256":"6ed1df501603b43763bae88ac4e7bbb3c917521e70de09f98e6f9168d49abdab","identity":"attribute:STAT_STR","terminal_conclusion":"keep"}
{"fact_sha256":"223792c280ccc539836d6a6c1bd7a1481fbac7b31f06176b82df58aab90ea374","identity":"duration:DUR_ABJURATION_AURA","terminal_conclusion":"keep"}
{"fact_sha256":"1d8a8e4263e2411b87d927f653d125624a8549dbaf66a8567712be8cca6a0c05","identity":"duration:DUR_ACROBAT","terminal_conclusion":"adjust"}
{"fact_sha256":"e1a1e70526d19e351118b8f009ac20c190bc1cd79914a0c12054f77902946c16","identity":"duration:DUR_AFRAID","terminal_conclusion":"keep"}
{"fact_sha256":"d0d82f962d51a73dbb27f1e8bacd347300ea5e331582d44d31811a0f85bd9ab5","identity":"duration:DUR_AGILITY","terminal_conclusion":"keep"}
{"fact_sha256":"5f1ee5b2da679287f094fa2b28f2a2030087a1bc39e5e1b07f262d233d425a1f","identity":"duration:DUR_ALLY_RESET_TIMER","terminal_conclusion":"keep"}
{"fact_sha256":"c127a78cc8e7807de22da86efca16e65c3fb6a972ac0f6e2a9810205d41a9e78","identity":"duration:DUR_AMBROSIA","terminal_conclusion":"adjust"}
{"fact_sha256":"a17600d52dd316f90a7efa01f6ef461e4b98ff254d45030c20d8382344e6ee38","identity":"duration:DUR_ANCESTOR_DELAY","terminal_conclusion":"keep"}
{"fact_sha256":"c21b5539437298901ed438f116457efb4590406bac7d5cf469b686f84204a461","identity":"duration:DUR_ANIMATE_DEAD","terminal_conclusion":"keep"}
{"fact_sha256":"d54d66260548f31fcea3e48bbde45528de33a603b0e210c0d69a91cf5c918416","identity":"duration:DUR_ANTENNAE_EXTEND","terminal_conclusion":"keep"}
{"fact_sha256":"4173f852dce7a8ebb1b08aaa3e548c24134435de2a34513f20345fd072c427d2","identity":"duration:DUR_ANTIMAGIC","terminal_conclusion":"keep"}
{"fact_sha256":"683dec7e4969fe91c713b912b61c8948f9d57302454b6667919d87c405f54f9a","identity":"duration:DUR_ATTRACTIVE","terminal_conclusion":"keep"}
{"fact_sha256":"79a010b5b3d3b9a84ae1f59aa2ae6a89e11f0210aaa8ac512eec83460121a973","identity":"duration:DUR_AUTODODGE","terminal_conclusion":"keep"}
{"fact_sha256":"95f74f67af3f5a052d2e4f01f6ce8b71c5398b3df56f740c371679168904f11f","identity":"duration:DUR_BARBS","terminal_conclusion":"keep"}
{"fact_sha256":"0dc856244725d79c367103d57d1db288e2b965caa843d7233acc97fdf78fae0c","identity":"duration:DUR_BARGAIN","terminal_conclusion":"keep"}
{"fact_sha256":"15419baeeaa10dd15354b6524e59ef8d73f625fb44896b87afe44ebb79d29341","identity":"duration:DUR_BATTLESPHERE","terminal_conclusion":"keep"}
{"fact_sha256":"742fb5fa8f85c7b1a7eb65dac119c769e3ef81b52afbffa4afdc53cb70461180","identity":"duration:DUR_BEOGH_CAN_RECRUIT","terminal_conclusion":"keep"}
{"fact_sha256":"aaed3474e88db20afc0cb36084d6c1c7cf8605e555a7cb179ffe4952109acabc","identity":"duration:DUR_BEOGH_DIVINE_CHALLENGE","terminal_conclusion":"keep"}
{"fact_sha256":"5523999d6f4c51f25ef0e498d0c8e829d5d27150c724b7ae11ebae21870fc45d","identity":"duration:DUR_BEOGH_SEEKING_VENGEANCE","terminal_conclusion":"keep"}
{"fact_sha256":"3192b92220751d6b3ad91dc78b96b21803061207501bd8d4e7f3517c65ccf92f","identity":"duration:DUR_BERSERK","terminal_conclusion":"keep"}
{"fact_sha256":"9d18afb0047942aeeee4d74fabae82eef098fe3c92e68284420f2491c18b2ad9","identity":"duration:DUR_BERSERK_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"a869f562528085971d6d1950bb14ada656c73294143caa18bbedd2a10f85408d","identity":"duration:DUR_BINDING_SIGIL_WARNING","terminal_conclusion":"keep"}
{"fact_sha256":"24387b2592de16e9153b51f4157ca3b4538afb0f21b3436ebb0779dba2cb738b","identity":"duration:DUR_BLIND","terminal_conclusion":"keep"}
{"fact_sha256":"37b90b256f07c9402e485638a95f3346d9c980b66761ebef9bdc173a2228e5cc","identity":"duration:DUR_BLINKBOLT_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"28821c4cd374afac26a0aca237f10426712e71266146afef9e574c9c2cd513b0","identity":"duration:DUR_BLINKITIS","terminal_conclusion":"keep"}
{"fact_sha256":"7999e8e15b04685ac4207ca4d10eb3c8f7cd4c827fe16758e9786d2a57abf93b","identity":"duration:DUR_BLINK_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"1d70bb63ff1cb4293c193a9de053c68f472aa1234f612afdf0e1dc1a74045aeb","identity":"duration:DUR_BLOOD_FOR_BLOOD","terminal_conclusion":"keep"}
{"fact_sha256":"a3cfb62672a0cb7b2085e1ad3d6b36e8959199d5d56018ba46462b3ad87a5dad","identity":"duration:DUR_BRAINLESS","terminal_conclusion":"keep"}
{"fact_sha256":"bfc64cee999593825f6ea919870a54538bf00e9ec79461f626400bbaa803d41c","identity":"duration:DUR_BREATH_WEAPON","terminal_conclusion":"keep"}
{"fact_sha256":"0963ea02304385cadd8fbbb8970b7bcaa4227fff4e4b99bfa76fbbbdaf10e22a","identity":"duration:DUR_BRILLIANCE","terminal_conclusion":"keep"}
{"fact_sha256":"31a9655316ff77e3429877f5622d102c3810f9268d4a152ac4bd8b2fbc57c526","identity":"duration:DUR_BUILDING_RAGE","terminal_conclusion":"keep"}
{"fact_sha256":"8183b529d017811ca6e79e8604f1ddfc09289a90f173eff47faecaeefdeb1626","identity":"duration:DUR_CACOPHONY","terminal_conclusion":"adjust"}
{"fact_sha256":"7e3ff1aa5e6137a7976eb91fd2bcbf3694e274b25e3902b90cfb2235b054f90c","identity":"duration:DUR_CANINE_FAMILIAR_DEAD","terminal_conclusion":"keep"}
{"fact_sha256":"c4d02692e277dde6e009a39724a7a1685af5fa6e6e4e7f6a0b1942bbaea16452","identity":"duration:DUR_CELEBRANT_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"04c50e35a11a1b267ba02ee82935d0dfbb68758820a752fa5d097a1f44945cfd","identity":"duration:DUR_CHANNEL_ENERGY","terminal_conclusion":"keep"}
{"fact_sha256":"73ea0490ab24a1b50aa8c7c6b1d65626d66c67745f6f5f823ca41c6b217e1e0a","identity":"duration:DUR_CLEAVE","terminal_conclusion":"keep"}
{"fact_sha256":"93011333a0215d61abbfcdbace2fec89b741f5238ad608ee36191fcaed411f55","identity":"duration:DUR_CLOUD_TRAIL","terminal_conclusion":"keep"}
{"fact_sha256":"0c96fa165263e52d75aa04292435951d1d4992556a37be1c37c90c40763a1337","identity":"duration:DUR_CLUMSY","terminal_conclusion":"keep"}
{"fact_sha256":"78a02db00a28c2ef90ac254e60435cde6781d50a6997b36717609cbc00d4c177","identity":"duration:DUR_COLLAPSE","terminal_conclusion":"keep"}
{"fact_sha256":"e671ebe355367514fa3c904cddbee4356bf66fa4ba5061e3a7704feaa0627acc","identity":"duration:DUR_CONDENSATION_SHIELD","terminal_conclusion":"keep"}
{"fact_sha256":"a356d394f7d3b9d9e58e4c061c416f5fbc0b53b174c7b86162d21319380f38f5","identity":"duration:DUR_CONF","terminal_conclusion":"keep"}
{"fact_sha256":"ddcb0159f9d14ad528fb5703aa09d0b805ed748c5015ed2f1403acd47a43badc","identity":"duration:DUR_CONFUSING_TOUCH","terminal_conclusion":"keep"}
{"fact_sha256":"a2531e3514b9039cf24cd9cdb3bf0a107699ead8a866d9ee5f6986dd9b4e8f84","identity":"duration:DUR_CONSTRICTED","terminal_conclusion":"keep"}
{"fact_sha256":"380844239af9c2e799b816341a3c954abaebd9305769df88ba074e490ff653d3","identity":"duration:DUR_CONSTRICTION_IMMUNITY","terminal_conclusion":"keep"}
{"fact_sha256":"7a3c8a8230a25299460f819c4083ff40da4e5968ee86987d1af11348a9c8b35f","identity":"duration:DUR_CONTROLLED_FLIGHT","terminal_conclusion":"keep"}
{"fact_sha256":"ca7979d19688cfac88c7c8a089241da2210454e84202ecd9ece4699a2274aa23","identity":"duration:DUR_CONTROL_TELEPORT","terminal_conclusion":"keep"}
{"fact_sha256":"8e373214cf5bf0af3eed113f2a9d861c50638867e2e9b94cba4ec903726da846","identity":"duration:DUR_CORONA","terminal_conclusion":"keep"}
{"fact_sha256":"7f1368efaf5c60a09d984be77272dbaa5a658d2cae716a8a4b88339f994ed519","identity":"duration:DUR_CORPSE_ROT","terminal_conclusion":"keep"}
{"fact_sha256":"17562522120125286e65789e1dfcb8d3fb01a968e89379590afe621c842e1079","identity":"duration:DUR_CORROSION","terminal_conclusion":"keep"}
{"fact_sha256":"2d4ce17198f5c07125295d31fb3dadaf40e4d45b80826a9d5971a72f5deb9894","identity":"duration:DUR_DARKNESS","terminal_conclusion":"keep"}
{"fact_sha256":"54a65353d6e890cd5901eea31400fae20dd66fe3230349094cc835f761fa63e6","identity":"duration:DUR_DAZED","terminal_conclusion":"keep"}
{"fact_sha256":"73d1e11f6840ba786eec2fe99d346829ffa225e7a332cb6ad2107a893819b316","identity":"duration:DUR_DEATHS_DOOR","terminal_conclusion":"keep"}
{"fact_sha256":"58e345d28188b9eb1abf5e83f03cce8e0acf49f7cb8379e8f2ed9d49aff66cfa","identity":"duration:DUR_DEATHS_DOOR_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"f04324843b8f36efb257dd6afcced5ad9066cd0c894c1dbf3b89a9ea65f1f629","identity":"duration:DUR_DEATH_CHANNEL","terminal_conclusion":"keep"}
{"fact_sha256":"241ca8b38fa2c64b49ffb6086db8fd11a2874c577437e1d278d9437858bdb8c9","identity":"duration:DUR_DEFLECT_MISSILES","terminal_conclusion":"keep"}
{"fact_sha256":"00994148c912e8a0e3ab3e2b499d3ed005fadec7e4662665fcd36442d98ce035","identity":"duration:DUR_DEMONIC_GUARDIAN","terminal_conclusion":"keep"}
{"fact_sha256":"1067f137b36e3d9be371f666b43d951ff7c880a38f68386b0c2c99939e45e760","identity":"duration:DUR_DETONATION_CATALYST","terminal_conclusion":"keep"}
{"fact_sha256":"e158c49892e0ba496874d66027321507fb72b8dfac03226d2a501aac4d7128ab","identity":"duration:DUR_DEVICE_SURGE","terminal_conclusion":"keep"}
{"fact_sha256":"13f85f843028880ee038334ab33070196cba6d84dab47a5a124a4b74e4fdb617","identity":"duration:DUR_DEVIOUS","terminal_conclusion":"keep"}
{"fact_sha256":"be9968aaf044e21cd36c73e144905ef9f4b36fcdd669087e5f086f1f15272aa9","identity":"duration:DUR_DIMENSIONAL_BULLSEYE","terminal_conclusion":"keep"}
{"fact_sha256":"7bc238f991d39e9bfd60fcb98060538e5f993d90b3ee1a3bdfe3f76a15559b6f","identity":"duration:DUR_DIMENSION_ANCHOR","terminal_conclusion":"keep"}
{"fact_sha256":"5ce42703bfedee13dcb61c06e98efa835423797c55e48ce2212eee165dcacd5a","identity":"duration:DUR_DIMINISHED_SPELLS","terminal_conclusion":"keep"}
{"fact_sha256":"d9f1d3bb5329007a7f2211bcbbd1e26c8dd0f8d7ba03eb1346687679706fb0ea","identity":"duration:DUR_DISJUNCTION","terminal_conclusion":"keep"}
{"fact_sha256":"b0e71c5ec6db8801880926248d8b0eb06429e58a55ae4ff47317b35c58013ead","identity":"duration:DUR_DIVINE_SHIELD","terminal_conclusion":"keep"}
{"fact_sha256":"3d1de28646b6e101e34c59c61513ca60def2251359da6e979018d656e0de1bf2","identity":"duration:DUR_DIVINE_STAMINA","terminal_conclusion":"keep"}
{"fact_sha256":"2661367a29fb66588be198f55fff63ae04e771cf673692788d850d52f4a729d8","identity":"duration:DUR_DIVINE_VIGOUR","terminal_conclusion":"keep"}
{"fact_sha256":"d0307cbb53491b9161f0d7771f33ef1c42548e8339b420054571038f976e2613","identity":"duration:DUR_DRAGON_CALL","terminal_conclusion":"keep"}
{"fact_sha256":"16c0d19f742171315383b9683d6494b8a824336edaafbc0e9214868a39680913","identity":"duration:DUR_DRAGON_CALL_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"1bab0687c6aef067375640772621f4d6664172585f4c8f3cacbf2a5799b7d170","identity":"duration:DUR_DROWSY","terminal_conclusion":"keep"}
{"fact_sha256":"84f9f5d231c3f0fbf193bcd9c1fe1626006578e6870344b37ee5ef465e27db0f","identity":"duration:DUR_DUEL_COMPLETE","terminal_conclusion":"keep"}
{"fact_sha256":"aeabbf63f1a1367994da7f2f9cb73e4b07d78d076350d927e04be9456875c8e6","identity":"duration:DUR_EELJOLT_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"47266604a36a79c8eb8a1cd1fbf85047a558614cdea3d93736a5f71253c90f41","identity":"duration:DUR_ELIXIR","terminal_conclusion":"keep"}
{"fact_sha256":"b8bbc0f68d858fab3e911bb3d493629160fe486671f2b2410d34314ad5644f77","identity":"duration:DUR_ELIXIR_MAGIC","terminal_conclusion":"keep"}
{"fact_sha256":"640d3aad6e51727c5d98fa5d8575de22c483046f3dc01249c9960d477be193e8","identity":"duration:DUR_ENGORGED","terminal_conclusion":"keep"}
{"fact_sha256":"5f9c68fc3315b6174f4b4cc19a0ccbbb2cc3cbe4b5b06863d0ecc855276489e1","identity":"duration:DUR_ENKINDLED","terminal_conclusion":"keep"}
{"fact_sha256":"dd553789a3f8383d9a200ad0433081248bd7cb277545d0189604968f35fd5b4b","identity":"duration:DUR_ENLIGHTENED","terminal_conclusion":"keep"}
{"fact_sha256":"8c2f3584adca6b8201ab9d5ba7da09d8086960ac61be19adae14540178319632","identity":"duration:DUR_EPHEMERAL_SHIELD","terminal_conclusion":"keep"}
{"fact_sha256":"16b48248943c082660cb1c26d646f9fb264d9f0b80ff810027f16a8c7fdb8832","identity":"duration:DUR_EXCRUCIATING_WOUNDS","terminal_conclusion":"keep"}
{"fact_sha256":"2f52845ed52512b2402bc33b7b408d75760208163c43425410c02c9e653dad2d","identity":"duration:DUR_EXECUTION","terminal_conclusion":"keep"}
{"fact_sha256":"575397d9debebcc6a76f7541ea91a619f87b3c3a8c3483b3ebd059579050307a","identity":"duration:DUR_EXHAUSTED","terminal_conclusion":"keep"}
{"fact_sha256":"2605b35070e472cb28ab2f040fb0fc3e5920bf7644c3600706b6b14fa38a553c","identity":"duration:DUR_FATHOMLESS_SHACKLES","terminal_conclusion":"keep"}
{"fact_sha256":"bb59e95312af2aa2b6ffc9c5d775ee951fa4c7b03faf46dee0fdf7109354bd85","identity":"duration:DUR_FIERY_ARMOUR","terminal_conclusion":"keep"}
{"fact_sha256":"d888ee0ecf3af8527c38c722d331a68defea0a5b38c58b3ca1fe4d666139890e","identity":"duration:DUR_FINESSE","terminal_conclusion":"keep"}
{"fact_sha256":"ecc5c8ed6b5a47c59994eb27c9a4e322da9aae99a504b3d355b17b4644cbce3b","identity":"duration:DUR_FIRE_SHIELD","terminal_conclusion":"keep"}
{"fact_sha256":"f32e7329431898f68b9148f57c597fed861be866e310bc0ca76d5281c660d246","identity":"duration:DUR_FIRE_VULN","terminal_conclusion":"keep"}
{"fact_sha256":"dc22be43d1a7dc9c3cd447fe14cab70d6f83de2cfe9eec967c764f2895076432","identity":"duration:DUR_FLAYED","terminal_conclusion":"keep"}
{"fact_sha256":"1e6787558e59014134dc703db2130d0e9652f064231b1a472b603cf1692ba45c","identity":"duration:DUR_FLIGHT","terminal_conclusion":"keep"}
{"fact_sha256":"ef6f9cf484038578cde8172958fafd801c95d5c974764da424d44e8e0e605eaf","identity":"duration:DUR_FLOODED","terminal_conclusion":"keep"}
{"fact_sha256":"c173f3c084378d2aaa8f6ca0e01607c451ed974797b57c651d1775ac7bc6c3e1","identity":"duration:DUR_FLOODED_IMMUNITY","terminal_conclusion":"keep"}
{"fact_sha256":"ef6c84cad5303a3ce41502f65e370457105be74a71b544884b70ce4532c52c46","identity":"duration:DUR_FORESTED","terminal_conclusion":"keep"}
{"fact_sha256":"9296a475e7977c90b6dc2a674c818a55babdf1ff47ba767d7a10f586c4c3b743","identity":"duration:DUR_FORTITUDE","terminal_conclusion":"keep"}
{"fact_sha256":"d7015234908ddd7f45c8b551ba6070b66771b790b12d2e6559b51466bd8a91c6","identity":"duration:DUR_FORTRESS_BLAST_TIMER","terminal_conclusion":"keep"}
{"fact_sha256":"c4453b79fff1baec40dc4ba0c8f5fe1707ecc81295095664553ee0aac376f8fe","identity":"duration:DUR_FROZEN","terminal_conclusion":"keep"}
{"fact_sha256":"ab2a7f78dab9d138973693f9e3fad21646b72bf15b1e82538dc9e59ff472ee69","identity":"duration:DUR_FROZEN_RAMPARTS","terminal_conclusion":"keep"}
{"fact_sha256":"e1ecb4e5b6d995d2ad6de720aa1411469d08e7dcf30c2c7cb5bb3d408738d1ee","identity":"duration:DUR_FUGUE","terminal_conclusion":"keep"}
{"fact_sha256":"7f1f053b797cb26b728c72ded499da6952ffabd149b34a5a1198d58d41f9cc6a","identity":"duration:DUR_FUSILLADE","terminal_conclusion":"keep"}
{"fact_sha256":"4042fba91cb896651f1350ed8d61850e1883b24853dd2f1e0eb035cc2e952bb9","identity":"duration:DUR_GAVOTTE_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"6daeeeab1e26ec1aa37e3d276485c11f120bcf67cf49234306e2ee5818d75b5a","identity":"duration:DUR_GOURMAND","terminal_conclusion":"keep"}
{"fact_sha256":"b187533cf97d859003b0491fe762a32a6f324a6efb131af86d8a0e52518fe9cf","identity":"duration:DUR_GOZAG_GOLD_AURA","terminal_conclusion":"adjust"}
{"fact_sha256":"ee01e54e920f4845f4571a7f9bc5cada010f71e95539b1ee776cfabf09c21559","identity":"duration:DUR_GRAVE_CLAW_RECHARGE","terminal_conclusion":"keep"}
{"fact_sha256":"c6432e59fd5799ac3041c2b7eda2a2097e3717c9439cd31a21f75dbdfb9a3c83","identity":"duration:DUR_GROWING_DESTRUCTION","terminal_conclusion":"keep"}
{"fact_sha256":"8a15a8fa324b3f73c7eb35e67e058f7e9cf7b234e8728e93f1cbd68f74a3abad","identity":"duration:DUR_HASTE","terminal_conclusion":"keep"}
{"fact_sha256":"6a44d079418b2e88fd2153ada94a2b4ef62e454a7a94dc3774c62fc62639561a","identity":"duration:DUR_HEAVENLY_STORM","terminal_conclusion":"adjust"}
{"fact_sha256":"ea13dc14e2bb313fdf54f9f9d1b38a5b60f47dc2fcb2895f456ed59955056212","identity":"duration:DUR_HELLFIRE_MORTAR_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"8e8b6b34691801114e52d33a40848308f41482f5167ddf15380339186a1eb186","identity":"duration:DUR_HEROISM","terminal_conclusion":"keep"}
{"fact_sha256":"a0560e4269405967939b55195e7a928312fe000667deadb8fbae97cd0e9171e9","identity":"duration:DUR_HIVE_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"ea6986af85f42aea186c96fe31025bb1f455eeebe1614dbc2c5c5941ec977b93","identity":"duration:DUR_HORROR","terminal_conclusion":"keep"}
{"fact_sha256":"427780f63ce06f35a514abb7d9e56e86d7b7e0cf6bc87a64cd30e82341a0656f","identity":"duration:DUR_ICEMAIL_DEPLETED","terminal_conclusion":"keep"}
{"fact_sha256":"cc891c038782c59928be7c00a342271bee37474f9eb4f277a11c0877b75b1321","identity":"duration:DUR_ICY_ARMOUR","terminal_conclusion":"keep"}
{"fact_sha256":"5c41b56d62f7c7ba83720df5c6a2fdfb3162226090e9ee737d81218b5ed12c1e","identity":"duration:DUR_INFERNAL_LEGION","terminal_conclusion":"keep"}
{"fact_sha256":"690d350d8b442909dc7c0c76c5b3c4cf989e82c95d594c966d1c2879b3c572b5","identity":"duration:DUR_INFUSION","terminal_conclusion":"keep"}
{"fact_sha256":"db927b71845c4fdcbde43955a8d3269e4609501a3831586f8ce0dabbb3a31670","identity":"duration:DUR_INSULATION","terminal_conclusion":"keep"}
{"fact_sha256":"604707664f25e43a3c3242614b071c2788d93e36d1f4f02b3e64b530eece210d","identity":"duration:DUR_INVIS","terminal_conclusion":"keep"}
{"fact_sha256":"4bc96fde8a40a8ccdbbacff0f16cfb4c3e947a7e412c0bf0ccbc966c2715b6ff","identity":"duration:DUR_JELLY_PRAYER","terminal_conclusion":"keep"}
{"fact_sha256":"d4ec0f412c588e7b79e2b81ddca9a46a8805340702b1f3d7194b77382cfff577","identity":"duration:DUR_JINXBITE","terminal_conclusion":"keep"}
{"fact_sha256":"f294620ac04c0e39417054ec2cda261e4e20ec54af5e956d04a9066c7341fa0e","identity":"duration:DUR_JINXBITE_LOST_INTEREST","terminal_conclusion":"keep"}
{"fact_sha256":"021aa521dec16e78973aa47690e9694c0bd1312693a464913120fa400342e731","identity":"duration:DUR_LIFESAVING","terminal_conclusion":"keep"}
{"fact_sha256":"b16b36b9414e221bd8857b42d34d3abe5c2eefdc3dd45a935230a8a0b14930c9","identity":"duration:DUR_LIQUEFYING","terminal_conclusion":"keep"}
{"fact_sha256":"5fca349d959afb70b363701b42cec1e68265570c4129362b048e65f94d55bc40","identity":"duration:DUR_LOCKED_DOWN","terminal_conclusion":"keep"}
{"fact_sha256":"41eb7d2d8b03552bd79339fec133db7fdbfbb8974bc6f4bc592aeb1d5764f90d","identity":"duration:DUR_LOWERED_WL","terminal_conclusion":"keep"}
{"fact_sha256":"65f20a08fc021911f1fc03b93bc46ec129b08a16feefa6e35ad85e1f65d21017","identity":"duration:DUR_MAGIC_ARMOUR","terminal_conclusion":"keep"}
{"fact_sha256":"e71b6428c5cf16f72f53b7a13ab22f5e8a979992cd95a0ecd22dc54000b16f7f","identity":"duration:DUR_MAGIC_SAPPED","terminal_conclusion":"keep"}
{"fact_sha256":"0aba62ddd80cb24bf496f2c9921a83b05d64fdc825a4f5f56c51a8ed84817b1a","identity":"duration:DUR_MAGIC_SHIELD","terminal_conclusion":"keep"}
{"fact_sha256":"0676e6b5022e2ae648a5105f59daa97d13458c677fe0e76fbb4304cdf4f140c1","identity":"duration:DUR_MEDUSA_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"d070f2f6107f5d0c349a3f0731e2c6aba072163091b3c737f6c7958ce3693b0e","identity":"duration:DUR_MESMERISED","terminal_conclusion":"keep"}
{"fact_sha256":"bc3f8ed61afc2d57060f9f27ac1f1b25efb60c0b61be0275edbcceb9886816b4","identity":"duration:DUR_MESMERISE_IMMUNE","terminal_conclusion":"keep"}
{"fact_sha256":"3c70d68b3974f3a77dff051c3b296b19abebb35ed6a9d0c8f6d7b32334b10b0c","identity":"duration:DUR_MESMERISM_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"2c32710ceaa527e617cd664c5a96255a50aacab98c92e1b847115074f5f0cf69","identity":"duration:DUR_MIGHT","terminal_conclusion":"keep"}
{"fact_sha256":"8f25c1917b9c5727c4ed88741dea706ce06732d592bc114af503c8a4fc69206c","identity":"duration:DUR_MIRROR_DAMAGE","terminal_conclusion":"keep"}
{"fact_sha256":"de53228fabb827f977844b990303112a247491cce7c3ead4e16ca57f60aac0d4","identity":"duration:DUR_MISLED","terminal_conclusion":"keep"}
{"fact_sha256":"06c56e2f1779027340611a4d5ab6430d74049993d4715f55277f9f5b9f2c037a","identity":"duration:DUR_NAUSEA","terminal_conclusion":"keep"}
{"fact_sha256":"fd27f245f1bb187b311104277831d4ec614213cd33d71bdaa8252a78b890a347","identity":"duration:DUR_NEGATIVE_VULN","terminal_conclusion":"keep"}
{"fact_sha256":"a7252040eaea28ce99e4abf3179a613cba685e0e03b29187d8912bd05faa097e","identity":"duration:DUR_NOXIOUS_BOG","terminal_conclusion":"keep"}
{"fact_sha256":"cb790ab12e3ee23fd1cfe3660e4a3f8ba536a1828d13537fd47354914c3f828f","identity":"duration:DUR_NO_CAST","terminal_conclusion":"keep"}
{"fact_sha256":"7cff32680ac1e084896c4f301eaf3bc1998042de49d0f18a8a2f690b6c09da63","identity":"duration:DUR_NO_HOP","terminal_conclusion":"keep"}
{"fact_sha256":"f7a05e54e9ebcb063dc385e5c0ed0ef820ba3a50f387447dfc55c80a533c4762","identity":"duration:DUR_NO_MOMENTUM","terminal_conclusion":"keep"}
{"fact_sha256":"4e697bc9bd397f08f99a91f404eca253af7947ae576129cb92f688ccf442940d","identity":"duration:DUR_NO_POTIONS","terminal_conclusion":"keep"}
{"fact_sha256":"c9878579b88d3c200f96927de3cd3e826bfb2a2c265f8424c8f07c1f78881bc1","identity":"duration:DUR_NO_SCROLLS","terminal_conclusion":"keep"}
{"fact_sha256":"6e6dcfe7ba43f71cdc64d3d1c37e5910cfdb3919f023d6fc9261ac2ecf93dab1","identity":"duration:DUR_OBLIVION_HOWL","terminal_conclusion":"keep"}
{"fact_sha256":"07b0b9324d0bf0b784e60d000b7890d96c4b33a304ec9c5d9723b804deab5b75","identity":"duration:DUR_OBLIVION_HOWL_IMMUNITY","terminal_conclusion":"keep"}
{"fact_sha256":"3f9fdc27f120b5ceecfba5253e3804fff340eac9ba543da6e17b288bd2015185","identity":"duration:DUR_OOZEMANCY","terminal_conclusion":"keep"}
{"fact_sha256":"7a9ee5079b2b861adf95ef19597a06b003e466d280bba5e68ad2e933940caeeb","identity":"duration:DUR_OOZE_REGEN","terminal_conclusion":"adjust"}
{"fact_sha256":"d714d308aa8c77659966afeabbb86e3ebe4c4ee80a3a082d422631550c2f06a5","identity":"duration:DUR_PARAGON_ACTIVE","terminal_conclusion":"keep"}
{"fact_sha256":"5232749ebb50ab3b3a108c5e6cd32dd27761fd0aa3f861366c2a049f2e37d01c","identity":"duration:DUR_PARALYSIS","terminal_conclusion":"keep"}
{"fact_sha256":"ff4dba592ceb600d27cbbca9f3c3d4c01bae7c000708d90f38be2b1cb71ce7a6","identity":"duration:DUR_PARRYING","terminal_conclusion":"adjust"}
{"fact_sha256":"1c7b8c8dec916b87c2805842e486a01e4aeff5a62134c1cae9f96f2bb2f2a6ea","identity":"duration:DUR_PETRIFIED","terminal_conclusion":"keep"}
{"fact_sha256":"130c3e7aee6fe173174233a79de3c33ba0dce63d3c4dba9ca375a9126974c33d","identity":"duration:DUR_PETRIFYING","terminal_conclusion":"keep"}
{"fact_sha256":"7b677e07e8f3ef5d80625c900306c3f7c56c411235f3d574d1dc48a58d66a9a2","identity":"duration:DUR_PHALANX_BARRIER","terminal_conclusion":"adjust"}
{"fact_sha256":"e1c5de1502d84f63f830cd2b0ce1634d97580705ceb1a05e9dc2ae362b4ad5a1","identity":"duration:DUR_PHASE_SHIFT","terminal_conclusion":"keep"}
{"fact_sha256":"8c5a6970ddab66e8f8f6a5df5a01f9166cb10208bdf59b41624a24888cb8ef25","identity":"duration:DUR_PIETY_POOL","terminal_conclusion":"keep"}
{"fact_sha256":"c23db9a0aa2bcf911e138281dd4c90df30ac95df49cf166c5ed5dab68c6134e5","identity":"duration:DUR_POISONING","terminal_conclusion":"keep"}
{"fact_sha256":"13c6269f10af5ff46b2660c4f8a120f1dc4cbb8fbb00ac1bedf173a99cee16ad","identity":"duration:DUR_POISON_VULN","terminal_conclusion":"keep"}
{"fact_sha256":"9304e786805077446c1162df93bfbb26572965078830fb3d335d51e4626e1d57","identity":"duration:DUR_POWERED_BY_DEATH","terminal_conclusion":"keep"}
{"fact_sha256":"b9a82f8316b41f211a23291b0be0e8a7fec4bf8e3863d13e61e49710d9c2f5b7","identity":"duration:DUR_PRIMORDIAL_NIGHTFALL","terminal_conclusion":"keep"}
{"fact_sha256":"0134d1bcf7387e8db9283b17305e72f1699f28749e258651d232bc0c1961fed2","identity":"duration:DUR_QAZLAL_AC","terminal_conclusion":"keep"}
{"fact_sha256":"6f9775312eb1bbf15a14fedca3d315fe81d48eb76241bd9e3698f0193c5b6ade","identity":"duration:DUR_QAZLAL_COLD_RES","terminal_conclusion":"keep"}
{"fact_sha256":"434412fe7d9de1238afe5a2156110cce35939ef5068ae932771a541afd4e2c62","identity":"duration:DUR_QAZLAL_ELEC_RES","terminal_conclusion":"keep"}
{"fact_sha256":"e1cdbeacbb9ee1c5db98c16387ccabaee47871a84c594e0174b3f3c3d4916c7b","identity":"duration:DUR_QAZLAL_FIRE_RES","terminal_conclusion":"keep"}
{"fact_sha256":"daeab40548c45f7fadcaf47b8e60594a5106303b2d50d94af4d354adbc5bf60a","identity":"duration:DUR_QUAD_DAMAGE","terminal_conclusion":"keep"}
{"fact_sha256":"bfc58278b2d75295db7fbdc7e920ecd352aa311e27cfb4389e3fa275eab429f3","identity":"duration:DUR_RAMPAGE_HEAL","terminal_conclusion":"keep"}
{"fact_sha256":"a41dbcd8787e8e6207a4edffd47d26993d1ea5addf7b759c6a2c77f3be014ca0","identity":"duration:DUR_RECITE","terminal_conclusion":"keep"}
{"fact_sha256":"2115bb277ff97b64e9c6566e5be41503adca9339073af672f7b4b1c28460bd59","identity":"duration:DUR_RECITE_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"be83bbd2ec0c3df43ea5cb0ec838303ffe2b129a2d574eacf2923bd0de0e5eec","identity":"duration:DUR_REGENERATION","terminal_conclusion":"keep"}
{"fact_sha256":"0d0bf0d0342274da0be51cd5121cc8d62ceb7c162183d2dc96d05b30ab54168c","identity":"duration:DUR_REPEL_MISSILES","terminal_conclusion":"keep"}
{"fact_sha256":"2c818cf434d5f76102d894134c12cea18c211501721e379061f37cb553f3c559","identity":"duration:DUR_REPEL_STAIRS_CLIMB","terminal_conclusion":"keep"}
{"fact_sha256":"9b087c42896e871e7c9584fc48fca221509dcc4994953b05d57ce0fb4fee5959","identity":"duration:DUR_REPEL_STAIRS_MOVE","terminal_conclusion":"keep"}
{"fact_sha256":"d3fc1e08fde37edd7300181ae067da7e5d959fcb3aabb1b0a498dea592492750","identity":"duration:DUR_RESISTANCE","terminal_conclusion":"keep"}
{"fact_sha256":"698202154dd39374e3655ee16638cbba94778d7a4bd122e73525f5fccf53423a","identity":"duration:DUR_RETCHING","terminal_conclusion":"keep"}
{"fact_sha256":"32202c3c702304f2e62f600f5d45878d39c4e1ecd4628b081aa7ac35887b6f98","identity":"duration:DUR_REVELATION","terminal_conclusion":"keep"}
{"fact_sha256":"c65ff40e64ca66a9eecddde2cd1c98cdb8415964218db1664b383a07e4e86755","identity":"duration:DUR_RIME_YAK_AURA","terminal_conclusion":"keep"}
{"fact_sha256":"decd4005c0b79f358c32f5ce2a6cf8dbe7cf64ea2ebfa1ebd490629d7909a4b9","identity":"duration:DUR_RISING_FLAME","terminal_conclusion":"keep"}
{"fact_sha256":"06d8ad2b96e68bf4c6ac41b46b19ec61db9c1edfd1a4709295b2d061cb9b4a7e","identity":"duration:DUR_SANGUINE_ARMOUR","terminal_conclusion":"adjust"}
{"fact_sha256":"7597311806fba65296b5271e9db2eaab50e9de04dc72bba23989100420df08ac","identity":"duration:DUR_SAP_MAGIC","terminal_conclusion":"keep"}
{"fact_sha256":"20dca303046b8bfb5478fbc9780e726fe58b43a435bcb6c5e169b8d0a990f494","identity":"duration:DUR_SCRYING","terminal_conclusion":"keep"}
{"fact_sha256":"f5b42ad7323568caf5d52c1cc1121abaa69901913a8870f34b7bca057ef8c2ae","identity":"duration:DUR_SEE_INVISIBLE","terminal_conclusion":"keep"}
{"fact_sha256":"b8ac9964d1f1c26ec219070f57d2d842dc054c884d18015ceedbfac219af74c3","identity":"duration:DUR_SENTINEL_MARK","terminal_conclusion":"keep"}
{"fact_sha256":"204afa9fca67833b3c3d58c66cc085fee9f0fa26cb29f9bd3320d26db1a3be40","identity":"duration:DUR_SHAFT_IMMUNITY","terminal_conclusion":"keep"}
{"fact_sha256":"30f9a5b9fe4dbc71073791f04d9d865e19006ff80b7ceddbd512fb59d0ed449d","identity":"duration:DUR_SHROUD_OF_GOLUBRIA","terminal_conclusion":"keep"}
{"fact_sha256":"2b189435d7db055c6b5b054ed51562eaff650ac8c2cd8409b0dbed8af1fe0920","identity":"duration:DUR_SHROUD_TIMEOUT","terminal_conclusion":"keep"}
{"fact_sha256":"145d2a9c6ad6b9f7b4e18f9b8ff153715cc6786bd381d5add41c51d4792b43e5","identity":"duration:DUR_SICKENING","terminal_conclusion":"keep"}
{"fact_sha256":"7df3cfff01cf7d502a1d0d6610f512a16c44d95a5917c8297e44abb62bcfa95c","identity":"duration:DUR_SICKNESS","terminal_conclusion":"keep"}
{"fact_sha256":"f2dba942b5b16920fdffebbd3cdbc48081e1c89d17d0a146432f2f790adcb635","identity":"duration:DUR_SIGN_OF_RUIN","terminal_conclusion":"keep"}
{"fact_sha256":"63be65f8cbded0d1447b1c3b482ec907e137398add365b900ef4458ba6748d14","identity":"duration:DUR_SILENCE","terminal_conclusion":"keep"}
{"fact_sha256":"4c1e159a10b4f2ccb0990aea03b079b60d696dc07daee28d40e1a04803698ad7","identity":"duration:DUR_SIPHON_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"c4ba1225c19d0e71f830a68563d0a58335ad117a0dd43e25aa57b9e006af6d70","identity":"duration:DUR_SLAYING","terminal_conclusion":"keep"}
{"fact_sha256":"21aaa9870e4bbde1741066a6305a9b15d1a214d403eba83ddbc6fc95fda9b792","identity":"duration:DUR_SLEEP","terminal_conclusion":"keep"}
{"fact_sha256":"ddbdad9d400c2ba138cf0d41236bb1bca7cbc5bb7a886e02e48ecf78d047b5f3","identity":"duration:DUR_SLEEP_IMMUNITY","terminal_conclusion":"keep"}
{"fact_sha256":"b44ca4cf221358c414d94f67037edd3b19f592bc2a318b373c46371b916d65b1","identity":"duration:DUR_SLIMIFY","terminal_conclusion":"keep"}
{"fact_sha256":"573f385083729db4031bb6dff3e908fd562d61bac679f62e63ace93ca4de0e43","identity":"duration:DUR_SLIMIFYING","terminal_conclusion":"keep"}
{"fact_sha256":"93c25d2d1788e06274939810e8315f5a52627b5509caa32dd68909a0a2031f78","identity":"duration:DUR_SLOW","terminal_conclusion":"keep"}
{"fact_sha256":"b02074fddfa1f1c995b6d1c40f3161b9aeb07c02265aa71d639f353a3ca7b252","identity":"duration:DUR_SONG_OF_SHIELDING","terminal_conclusion":"keep"}
{"fact_sha256":"3b239643b34cee8c740432271a121478c7bffa4b1efcf0b25c6454569be9cfda","identity":"duration:DUR_SPIKE_LAUNCHER_ACTIVE","terminal_conclusion":"keep"}
{"fact_sha256":"f3f84edf9d5dba907ee64e129c221d78b84c07f266594947dd0e6dcd89d32392","identity":"duration:DUR_SPIRIT_HOWL","terminal_conclusion":"keep"}
{"fact_sha256":"b5a83bc936439ce079241e5a12871d6605a7649b2e0203b6999a69a942d42cc3","identity":"duration:DUR_SPITEFUL_BLOOD_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"c367904495b52370f4837150be7d3b31d270a394c79fef2eb65577bf942a5401","identity":"duration:DUR_SPWPN_PROTECTION","terminal_conclusion":"adjust"}
{"fact_sha256":"0d04c3b7350993e255c40780f2aa6871f4f5f2e67be628def28c88379dcd9397","identity":"duration:DUR_STABBING","terminal_conclusion":"keep"}
{"fact_sha256":"7e82173e50599ee9419b0a15d313a76f1ffa8cbf654611df7173e7b8c20cec3f","identity":"duration:DUR_STARDUST_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"bdb019b2f2f4dd1050bb1adbb4854a3321180642dee9a9f776601847a8d35a51","identity":"duration:DUR_STEALTH","terminal_conclusion":"keep"}
{"fact_sha256":"f33d7e9a771d8a034ed2e85e245ab786359c8fa7a9c6094c1406201623bd1031","identity":"duration:DUR_STICKY_FLAME","terminal_conclusion":"keep"}
{"fact_sha256":"935b4921ac101726a6b30bd7193309f529e91470cf691a57363f453e5062aaa7","identity":"duration:DUR_STUN_IMMUNITY","terminal_conclusion":"keep"}
{"fact_sha256":"14ad2081feb931de47dc89c47143ac0fcf62944659bd06daf80d3784c4d691cf","identity":"duration:DUR_SURE_BLADE","terminal_conclusion":"keep"}
{"fact_sha256":"79e1868938dd7344c8deac126e34afb6d0a11118005486fdaff7d22f41ccb64f","identity":"duration:DUR_SWIFTNESS","terminal_conclusion":"keep"}
{"fact_sha256":"a4d7e884aa2fe2d4130904142f710c1a6a2fa5dfd1a43c977e0ba69c58d71c2a","identity":"duration:DUR_TELEPATHY","terminal_conclusion":"keep"}
{"fact_sha256":"a633d953fa3b1bcd728037b5bdba90363e6f4e996e84706a04647625c564102a","identity":"duration:DUR_TELEPORT","terminal_conclusion":"keep"}
{"fact_sha256":"0196c7d351f5320827a4ebf5ee5b29f30d89e30e4a75f8adcc9d350a5e0806f9","identity":"duration:DUR_TEMP_CLOUD_IMMUNITY","terminal_conclusion":"keep"}
{"fact_sha256":"74153493086c374e306eb4333585137f2cafc49cb339b5851f4382e7ef5e17a0","identity":"duration:DUR_TEMP_MUTATIONS","terminal_conclusion":"keep"}
{"fact_sha256":"5dc5d3e78d36d43b58d38673ac95440be2b096464827f387fb8f32951cf809db","identity":"duration:DUR_TIME_STEP","terminal_conclusion":"keep"}
{"fact_sha256":"89f5dfdd343443d634d1ed9cac179bebb701341e2f6d4e99c292e7483cf17d93","identity":"duration:DUR_TIME_WARPED_BLOOD_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"ee9f3e68447c9a3c80a20e134ada1f93f5ad0ec0bc5ee3e67e237ef8c06fe64b","identity":"duration:DUR_TOXIC_RADIANCE","terminal_conclusion":"keep"}
{"fact_sha256":"50961e79613965972dfa9640c09a4c793385366c91a5b979655cc66856000548","identity":"duration:DUR_TRANSFORMATION","terminal_conclusion":"keep"}
{"fact_sha256":"55ace86f22fe5e8465e55a0d4d2e2af938df9273b30bd8cebdc7c96bd7ad01b2","identity":"duration:DUR_TRICKSTER_GRACE","terminal_conclusion":"keep"}
{"fact_sha256":"b200b8f52dd8f516104c4dda1148f3dbf3b5c83ca1b1e9ff384b683d4af1620b","identity":"duration:DUR_TROGS_HAND","terminal_conclusion":"adjust"}
{"fact_sha256":"76ba9e08ad03886ff83f71715c93ba01c76519fa57ba0b7229c6bc42f5963735","identity":"duration:DUR_VAINGLORY","terminal_conclusion":"keep"}
{"fact_sha256":"bec1bda1263448f79a28f98d995f5733e538c3bc79a2cd69f15c543f3199ae49","identity":"duration:DUR_VEHUMET_GIFT","terminal_conclusion":"keep"}
{"fact_sha256":"45bf9de636634d50dcdbd4e998fc6d40b4fe791964f8fa27d378169003e01400","identity":"duration:DUR_VERTIGO","terminal_conclusion":"keep"}
{"fact_sha256":"a65e8ede828eb893fa516daa4dc42c5f8fe704f8081138b55d67ecc954f126b8","identity":"duration:DUR_VEXED","terminal_conclusion":"keep"}
{"fact_sha256":"3fdcea7d0daa05c99c0e883eb4902b501924f54609816895486711bbd0872f87","identity":"duration:DUR_VILE_CLUTCH_OLD","terminal_conclusion":"keep"}
{"fact_sha256":"2ce8b23b9bbc5088a6124cbc0d1f56b7bf3e95450b369acbdd1eaa69285adb0e","identity":"duration:DUR_VITRIFIED","terminal_conclusion":"keep"}
{"fact_sha256":"30bcdacd5751d7be2a0758b19c0503d9c13c302599bdb8a1e3a6dcec16b3cc87","identity":"duration:DUR_VORTEX","terminal_conclusion":"keep"}
{"fact_sha256":"e24f4d0aab024b8b470c151bfdae6f7bf05067e5db01e83b4336266facf98e70","identity":"duration:DUR_VORTEX_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"9ba86bda765a386622bac53e84df897daa7eacab34347d4e6435296a6dc708a8","identity":"duration:DUR_WATER_HOLD_IMMUNITY","terminal_conclusion":"keep"}
{"fact_sha256":"cfe8a609ffc223618a8a2d3e79abd5d1c4831fd839a4ff656d190c3e50efcc47","identity":"duration:DUR_WEAK","terminal_conclusion":"keep"}
{"fact_sha256":"71fa45af0fc392d543a59e8acbec265768cf334df881c5ffecb463e5b1390b94","identity":"duration:DUR_WEREFURY","terminal_conclusion":"keep"}
{"fact_sha256":"b47958fa90b32220d02a66831a671733f3a3229c965bbaf30ec87c6c7a338505","identity":"duration:DUR_WORD_OF_CHAOS_COOLDOWN","terminal_conclusion":"keep"}
{"fact_sha256":"c3a30e2c87e9f8d26fc1c9d2e8321688af2a32e113fc906f210267fe68005fe4","identity":"monster_status:ablaze with memories monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"499a6f615c76650988326d32d20c940bf35ffd8b741c611335112918484608ce","identity":"monster_status:about to teleport monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"595a5ee7c0085f39241b39821d41834f2472beaedae14e3cec1cec5d66cf352e","identity":"monster_status:afflicted by rimeblight monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"15898f09430a62ca9c99edfcc73437b6f1aa3e2b2aea8e82f19692cb344fb87d","identity":"monster_status:ally target monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"c6ed27e2b62e9eb28c81b02a4281700fb1f56cfe4136e03fed923fd13e724295","identity":"monster_status:anguished monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"1a490070fae47720eb9b768ffcef72043e28958aef0aa9dc9b438c86af5ab290","identity":"monster_status:asleep monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"8e743167e2710156e27f90a212bd53dbde287a6a7d4c38abb60c5ac3af659835","identity":"monster_status:berserk monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"6f0a4f0bd8ecbcb062d5500f1c049a04ac5c21d2ab486f5a6489fcd4e0d9032b","identity":"monster_status:blind monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"f5b3bf7df0a4f7ee0fbaf393b35897ee6f6c9a8e2d5c25ce3a92a1203ac9ccb0","identity":"monster_status:bound in place monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"7cdc595f59d27142c8f83dd95c82c302ad4665f57c7db03c65387abb3399f4a0","identity":"monster_status:called by a tesseract monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"ccca5c80c9786f520a2e8f9b69d16853dc468a5c6c11118cd12d544bdb4586d8","identity":"monster_status:catching her breath monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"90f11a21159b34f36b5ef5cb5c25d09eaf79c3335c281713eb809cf1903c42d4","identity":"monster_status:catching his breath monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"613b76ae5f5d7d40478db94871b8faa7535aa0346a9a98964aa43e917ecce964","identity":"monster_status:catching its breath monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"29a6ea98bf66f21b7a92138dbb5f3f2a95b9c30d657f5279e67537cfa43f201b","identity":"monster_status:catching their breath monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"e2343ae1702de32331d146efdb2f492e943a52e43f81ddafaf0c92cd93e74929","identity":"monster_status:chanting recall monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"c6747c192532ec8c322dd5dff8af4a07ead68debe293fff33cd81c8046ce104f","identity":"monster_status:charmed monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"614f4261f144384db0207bc119ce95ae564d53445a5aafa1557b9868ef230f79","identity":"monster_status:concentrated venom monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"307dd279c46b319e7b806945f23504e1a090d6e8ca59c3cccd5cbd2b92bc8e0a","identity":"monster_status:confused monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"588c1f7a5cecac1606583bc72429a773be5b7e25cf54925453f2b3bce88e1cf6","identity":"monster_status:constricted by roots monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"aed430c8bf8bb79adc1a8b7f73863d13169747db1472b27ddc6646307dbea8f3","identity":"monster_status:constricted by zombie hands monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"3164bd2e56948610d6e93b196a789ba1ec19bfa7f52ebead14fdea70bec5363f","identity":"monster_status:contaminated monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"14956c7205720d938bc5ac5c647bae2489931568681228d027248f0ed1c293dc","identity":"monster_status:control wrested from you monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"9ba1000b38af2e213cb5bf04c0d0127fc92637458c0cdccea7c665f05c567706","identity":"monster_status:corroded monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"2d6710c77a35cf98b63714d8cc4f64d75deab1bf5657c82a851994154071e087","identity":"monster_status:covered in liquid flames monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"6dd3af23a2851089bdf7df09f8534435a43c264ebcde439b167fd1728bd5263d","identity":"monster_status:covered in magnetic dust monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"8f4b87fc9ddf5e00c0cee43d450308292424323f256c1e1a48a05f516b5a80e4","identity":"monster_status:covered in terrible wounds monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"28e01e1f9d074d1a3a987ea8da26369a8b961d03b4f3ae28634d67ac1120c4b5","identity":"monster_status:covering ground quickly monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"516f8a1f4abe3c9c9bf868c0cc5d4e578d00d0ed7a949104bada67d00e180910","identity":"monster_status:covering ground slowly monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"b9b63d077ea9da081edf6a6d082738bab7e7a4956c2ca2acc7b2c4912f4e670f","identity":"monster_status:crumbling away monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"c301f0b65f52b5fce44f3740ea6cefec7d25beddbe215d97c2e4d33464aa1ac7","identity":"monster_status:cursed with the promise of agony monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"5efe8e9ce1468ff8225e1e5b5e3acc3dfeac5b63eb5bb0304692efa4273dfd1e","identity":"monster_status:damage-immune at range monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"f842f459abf1d2e258e0a2678023b3bccdbe74e68f92bd641a9c1932ec7b8638","identity":"monster_status:dazed monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"25e73ca7778c0f85f7a5a1e98607bb9a44541067f301e9ff45d2a57f75073415","identity":"monster_status:diminished spells monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"1890be094b41d648061a53593183f0146e66d1d5144a72803b983b31df2c2f3b","identity":"monster_status:dormant monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"971fec82c5bb3c0c0fd15b6f65f78425b86024059b919efcfd9966d39560929c","identity":"monster_status:doubled in vigour monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"337af0f79ebc09853a248568e14e6624056273a448f24a2528633ca71581ea69","identity":"monster_status:empowered by the touch of beogh monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"3496180467af26c6e34578bcf70669997da46348c482cc6462cf516f3eab08a4","identity":"monster_status:encased in ice monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"557600720d92fc589d9a63ba5fe7cca3a77aa9c2c2c32a82f6bcb275140bc270","identity":"monster_status:entangled in a net monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"87a5816cdb2faa2fa5f0f6b1052f0888bcd93002f80612b71b495e74174ce587","identity":"monster_status:entangled in a web monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"08211467a58051e5722284f4a851ac61bc2dc375a7ac42185e7af66661db85da","identity":"monster_status:extremely poisoned monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"95ca52922ed4ac9f934e6b8d659853684d5e6bad0c7e70b20b774e716f52ca5e","identity":"monster_status:fast monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"f3f53db10c2ded6a007f5e7b4a39e8d8716a93e38687eb69796b309c09c64a75","identity":"monster_status:feeble figment monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"b567bbfdedde7247bad0f88a5b7489115d5ee48ca0d956120dc8291acb1289d6","identity":"monster_status:flame-wreathed monstatus","terminal_conclusion":"adjust"}
{"fact_sha256":"6219b179f6951d6c3bc8e5695729838a60ac8fbda095dacf979a265cbfe80be2","identity":"monster_status:fleeing monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"bcac8e513a88a4f7d21efccbc4322552b8eed28347ce1bdac13cef47fa1148f1","identity":"monster_status:fragile as glass monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"71ba754d4dbfb131377934a6f83ecba72520bf4f329371da90319849e4ec051e","identity":"monster_status:frenzied and wild monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"41ca7ae0c9ed63bd7d037e49b5762da85e49d013b5b296116396011cfc5407da","identity":"monster_status:fully charged monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"192b188ede5df0e15ca5d54e71fe9d5c0b89171379827cd483618698057d7aa5","identity":"monster_status:grapneled monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"6a0d2e259ccbaf6b4290c1a2cd24268ab3de163563502986bada0ff060838b2a","identity":"monster_status:heavily contaminated monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"8ec7dabbb6c496062962349f836bad474c16ecdc32abb59c49e285cdf99b03c3","identity":"monster_status:heavily drained monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"42e7f72bfca386ad87c8086f55e06cc448c6a66ce94aa54dd96d079207d53fcd","identity":"monster_status:high-tier stab monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"4f9ad1d297b8622f24fd23c2434b4975230a39b2c2844bffd30a4f3771b173c1","identity":"monster_status:idealised monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"adade7becff6f74571bf34a51e15537c5f88872249fc5fe9c8c0289ceac5a761","identity":"monster_status:incited by gozag monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"7f86a5882bdd52b110ec21f65b67088d4530d2adbb6decfe88ebbda3871cb0e4","identity":"monster_status:indifferent monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"622c44d4f9e6438982266bb34a32ecfc3c7f2f43d11913ff51ce914076585851","identity":"monster_status:infested monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"ab6f7a8b4385b0b4b2462bc6dd59cd02dfc61c3383b5e545ae22db9929106573","identity":"monster_status:inner flame monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"5e017cf0b08641687c83509c89dd01daf9ae094b34548a1e3811503879e090b9","identity":"monster_status:inspiring fear monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"cbe6b4ff3ccd087caa5228627c57a8598dfb9361b56ba99cacdbf055015ebd8b","identity":"monster_status:interlaced with chaos monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"3511e8e14da23962bd6e9b51a0596dd091b23a4cac73b75fb57238fa425517ee","identity":"monster_status:lashing out in frustration monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"f4aaf919933514fb2f04dac3d42e907d0964e52fe30abbb3bff1f276d197fc45","identity":"monster_status:lightly drained monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"09a0d8bd09270e9e1268d26d86378fe3d48016e6e81ba47cacf010c878126d31","identity":"monster_status:lost in madness monstatus","terminal_conclusion":"adjust"}
{"fact_sha256":"c4fdea03a302fb1059d251b82d47ef746d164f4f8df567fe96a6ef73786d8eb9","identity":"monster_status:low-tier stab monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"f49854258cc73e96f7da32a9a2113b7c7a3d003239c8b8e70d09343104f4513c","identity":"monster_status:magic disrupted monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"d5e9bef8e9e8080490970846cebbee26ed71564022f1becb6c061a40644770ac","identity":"monster_status:magic-sapped monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"3f055eb2e1952e33c66c4964845661938b69598283cb1f0fff80e4ee8cc74e22","identity":"monster_status:marked with the sign of ruin monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"2d877e7c0e4d22b3b54d975d30513ceccc567674ac9aa87935a61a456e14a307","identity":"monster_status:mesmerising monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"5fa79cd80b3e43a9bbb0b1b7e6573c03dcf296422bf2be4b0f849b4fde83d8a5","identity":"monster_status:minion monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"5eb1357a51e607d485ce029bfcec3da8ce4894913947d5f22e3c35db44dc316f","identity":"monster_status:misshapen and mutated monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"683c8c6c1199a274c7eb65886856522ef7e364e6c91170c8fb9c55e5ef181f3a","identity":"monster_status:missing a shadow monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"17b245935b8ef140664021453dd7987271d1bc2919ffec5b2f59880fcc970f7f","identity":"monster_status:more vulnerable to fire monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"1599e826233417f108ea847d60a4f4aa9a51b1dbff7227f298efa14f565f4b1b","identity":"monster_status:more vulnerable to poison monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"82494c3a118478265913d2074576007634db3a29e6ff4896f5f12f45da2b645c","identity":"monster_status:mute monstatus","terminal_conclusion":"adjust"}
{"fact_sha256":"86aa95197b162c627bfba9af4f7d8d0f4bb3835e76e892a9d3c49226acf4ad2d","identity":"monster_status:not watching you monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"b2983486a2904b40ef2b096d2d674061f44b75872b768f66f5a37b631dac16dc","identity":"monster_status:paralysed monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"068419b51b3bcef55a29f38a7aac660b6e6470b898f9a14d2ee220cf9a7d6eb4","identity":"monster_status:paralysed with fear monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"d3c36ee9409d1b1e7bf89b1ec1275e7e2016d404459af5664e2dba975ec76168","identity":"monster_status:partially charged monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"2d68e28ccd3aae122185597a73a5ac4f1f6e302b9481dc6dca4cdd919b183c8b","identity":"monster_status:peaceful monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"75291f0101abfc98fea4150db942630fc9021cb008e8380a9627e01b0c701d49","identity":"monster_status:petrified monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"588fc253b20fc7855a9ccf44d4ef4c1ad0564d32b5d552cbcec2b39474d91a01","identity":"monster_status:petrifying slowly monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"861fc2c17fdfc4333fb9b2d07be5356bc4baa28928a928d68133089d348d12dc","identity":"monster_status:poisoned monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"f9c34c9e0548b356b9bd62964f4d7b5c3733a0704359760e9a094a15ea2ecc89","identity":"monster_status:radiating silence monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"16e94b9c180585b6d3e89bcb8fe6e04125bbbd096d93d548b0bae1c7d39f6e6d","identity":"monster_status:radiating toxic energy monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"0cb09beda273c61a0624ead2a9066a8edbae8165306b2e1b014fe5d187ee066b","identity":"monster_status:ready to become your apostle monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"efa35229657b5bc6e19979e1e699bdc169a4a1499bbee8c208f6be1e115a2523","identity":"monster_status:ready to howl monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"39dac682937ae7aae3385279c195ef7906b433d9b33df67848b039472e932341","identity":"monster_status:ready to sunder monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"16f3e92d42cb473e3e3fb5a5d90ab5b161c80676899975dac753e5221613230e","identity":"monster_status:reflecting blocked projectiles monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"735762f1249fad0e40943617a58767db022a9e65ab73ff0f0e69fe867d86319e","identity":"monster_status:reflecting injuries monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"2ee87380eb4b4be15de7cecf2be9fa309e86781536d50e0d88e71ca15023b8cd","identity":"monster_status:regenerating monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"ac3ec04de2dc6d3f16c38b5ec5ada72d30b8dbc6c753e7efa63e6e76885275a3","identity":"monster_status:repelling missiles monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"2746203f0dad4c9c58cc09092e217f1a0c5da973e2f68998b8d26848d74bba47","identity":"monster_status:retreating monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"4eea9db74ef3d94aed43bf990c99b0cccb103413c8927601a1db7f6d74333678","identity":"monster_status:rolling monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"d71b336047d2ccb533b995d73b5b2349180fe2c9a342457e2b1d55c17b4540c0","identity":"monster_status:sharing her pain monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"f5133622dd9bc8e87a4b2c70f45b8819ab8b458b84ecb91846eb896740818ec1","identity":"monster_status:sharing his pain monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"cc06570cf6efdd41641e0dd40720906a8be0b6e333eb60e2f6330d243ff4c79c","identity":"monster_status:sharing its pain monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"b484422db67a3c3481ea3426ba837b66396ea369bd756b1f44e62c688f1141c5","identity":"monster_status:sharing their pain monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"6f58c2084410a07fb6fe30a2c95ff66f6d9649d8a2c78fd137d77f47279b483b","identity":"monster_status:sheltered from injuries monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"61aec2f80a32585edce249447c3ab0c4fb56f5c44bf5a01b2dad3d69c31f56c7","identity":"monster_status:sick monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"ace207be00272acc0d5f8813b03f30e869c1831387aa3d2ca707009148b68397","identity":"monster_status:silenced monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"77593643769d3f14863d8042c6e1eb2436d2f77c98fbe83225e2272b3188c45b","identity":"monster_status:skewered by barbs monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"8396e09729909059069190eab11ae5ab1da025d03df77cf858ece17724bf0324","identity":"monster_status:slightly transparent monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"7ad9757048c984ad0dc8e5a5a1ef0dd1479cd3dd5345586be73418af3e4b235b","identity":"monster_status:slow monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"08c29749fcc7fc8afdbe95d6f3f01cc5a25291ff1ace6a18cbebd334a25b5073","identity":"monster_status:softly glowing monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"4f55bc67762c80e0bcd3d1b46e06ba7147e93110c533eab6e915455b5ee1deaf","identity":"monster_status:soul bound monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"c5dbe68ef3b2e1b44ffe8f21e3668ee3166d45382c7bda34d8bd203cc78fe047","identity":"monster_status:soul-gripped monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"ce15c52944af34053b7cc8e5b793faeecc42c36894ef6a75e1182cd4dec61d08","identity":"monster_status:soul-splintered monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"cfbece95bd446e94b93cbfdcab0a8e18dab76cbb2e5821fb0332200754b9a724","identity":"monster_status:spells diminished monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"d3a6fdc78f090b0ed1f1f8cf5d7a88bc2e5d39bcbcb4e1cfb0395f3af5c10d73","identity":"monster_status:spells empowered monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"09a8a931110e67a6cac5222f25b8226a483bed799306bc101b3a5c0a4d52137d","identity":"monster_status:stilling the winds monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"c9f753504ef445e9f29d7da3c3551c40ec46ed504f11f9dba57faf17fc682758","identity":"monster_status:strong monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"6a1428f45ad94b90a2c1f6c7d4b72a971e5d7e3439e60f7e5fb779bf92f2e3b7","identity":"monster_status:strong-willed monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"72f728c7ce849bfe2d272998654658e60daaa6b1fa1a3fdf42553ce61042a269","identity":"monster_status:stupefied monstatus","terminal_conclusion":"adjust"}
{"fact_sha256":"c1bf56da9523030690dae76bad6499ba8880381b1fa8b95884827227fecc9e96","identity":"monster_status:surrounded by a freezing vortex monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"c03a10940b59ef9296e2ec3bea15c1830700d0c0997be47a021b77e0c2080a11","identity":"monster_status:surrounded by acidic fog monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"15e1e1bb8d9c4d705f9750311a53a6b609f6531e80bb031733e8b6c713b4b021","identity":"monster_status:surrounded by chaotic energy monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"c0d9cd443adc715d2a9e8ada411df0b1160093330eaf748588d767a5262d10ee","identity":"monster_status:surrounded by flames monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"dd87b63bd75e69e9146fde60a8be42cd5f90a0e78a657067133f1749b1ef9341","identity":"monster_status:surrounded by fog monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"b0a3ba96b32a06330a003c01cd41fc9b2e11a0e4696b442689ad685bcc84c6ac","identity":"monster_status:surrounded by foul miasma monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"ea91efde65dfd0df4b14c095dadc8b1a684da8c4e7af7841e87a98b20e5799f5","identity":"monster_status:surrounded by freezing clouds monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"5832ece7de33bc46f703bfe0a87feef73e758973d6ac577db3ebe94afe15e18a","identity":"monster_status:surrounded by mutagenic energy monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"e917069f539232d26abca5b810ad2ce137ef393cec1709bf2a7d1ffd0e1260ab","identity":"monster_status:surrounded by negative energy monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"f67ba1424b728d53ab6f208dc35471f249b1ab7fc8df07c5b0f2ae09af014f91","identity":"monster_status:surrounded by restless winds monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"9fa872a38cfae6a544f6fba1a41be0662d4707e603495703e823a271e3611a04","identity":"monster_status:surrounded by thunder monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"ccbfbbdfe43b0fa3009ff1943debbeeb03b608086530bdc53a71e3b2e569350d","identity":"monster_status:target of orcish vengeance monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"5b218bd7a2d511ad2cb300b2c668614670ad4f13782ba3ac5bf6d40a5a1e520d","identity":"monster_status:targeted by your dimensional bullseye monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"082f843974e92d3c89655cdd79dd29e378b28b7c395233710fb3bf7b96a8d14c","identity":"monster_status:tempered monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"dbcc0e8bdffed984a3ad1ecd89a6ce5b65876ce6f59cb9c237b30b6ce9a88b97","identity":"monster_status:touched by paradox monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"2c53de1ef94b5ed2dbbba77e7a2d814151f5bbe48473527fc8400cf39ed8784a","identity":"monster_status:unable to breathe monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"dcf10667b8fb82c196a0fb9bd0b501d031b9fdb460ba9ef4cd1ed2d74329981f","identity":"monster_status:unable to see you monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"7aa8edd02c2263bb31f382905e2dd5742fc410a7ac5274f536e443107434372a","identity":"monster_status:unable to translocate monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"5db0df097ab678c403cf6e179b1bc9cd5a56163f6381e9559f2e047cde8489b5","identity":"monster_status:unaffected by silence monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"7a883b890c344e9696b211130dc5a25e9c3a046b76b88ac5c8398750f087c906","identity":"monster_status:unrewarding monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"431cbab63c4a33b94662cd4c473807f1a7e65754806500913052d924edfd1740","identity":"monster_status:untethered in space monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"a1828b3b5b2a9a71eec66964cf8767008aeab90f1003a99c5926beaccda14c96","identity":"monster_status:unusually agile monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"3fbf6d85f8c06d1cc0ff5eb5516baa78475f98f8ed68b3a0ff70e5d08926b17d","identity":"monster_status:unusually resistant monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"a5aabf28d15ea12ff6f255ac8c1344ed1e2f641ced53919ed1cdaa02f3ff10c0","identity":"monster_status:very poisoned monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"77d78321812c685699a6673e10f82d686b52fd32ef1958c3a46009965a1353df","identity":"monster_status:weak monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"c194eec4d5e6249aace228956168b4d1621308e39d8aeecd6c587b562977547e","identity":"monster_status:weak-willed monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"1364c33b0dd481d5176a5cb114f4f314a6e341a0553e79153e82c70ced5e7b0a","identity":"monster_status:winding a clockwork bee monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"30c8dbcce83729cb3f04caa1b5554ad1906b4c756344d2a59bcab6094f33233e","identity":"monster_status:withering away monstatus","terminal_conclusion":"keep"}
{"fact_sha256":"4fcac30ccd576417434d75d5ea193fc081e060c2a32c7c3fac01f97c199f2b48","identity":"mutation:MUT_ACCURSED","terminal_conclusion":"keep"}
{"fact_sha256":"859c6377a7e4c507b5dab9a170b42279ed7ab0b4d582dee18f41cfa93118640c","identity":"mutation:MUT_ACIDIC_BITE","terminal_conclusion":"adjust"}
{"fact_sha256":"82bb53ec4c69a6320c63b1c65fedf34a9de02dfdb6fbf5cf614fff31eba3799f","identity":"mutation:MUT_ACID_RESISTANCE","terminal_conclusion":"keep"}
{"fact_sha256":"fd70339d7cae8d2536ba0ab091342bdd062c5466f14c48c3faa8cdf425615a75","identity":"mutation:MUT_ACROBATIC","terminal_conclusion":"keep"}
{"fact_sha256":"7e53506b5f045a75ce57487af12f2be1a29194bd0a0f23c21019d5c2e88429f1","identity":"mutation:MUT_ACUTE_VISION","terminal_conclusion":"keep"}
{"fact_sha256":"0b2eb65bf714cade197be7d9e5d215300c054ff1a301ca3d7bbe5719ecf94f14","identity":"mutation:MUT_AGILE","terminal_conclusion":"keep"}
{"fact_sha256":"7a7bb6debee21fbabca71b711f7f2bd7de7618432177effdae1bbe8bbf9adf9f","identity":"mutation:MUT_ANTENNAE","terminal_conclusion":"keep"}
{"fact_sha256":"5904945e0425875a04b1171daeafbcb8e407370767695a49f6a454ee65293ba4","identity":"mutation:MUT_ANTIMAGIC_BITE","terminal_conclusion":"adjust"}
{"fact_sha256":"4dec02982e4df90d4694bf1da90c008cccae101b4f6b54927a137c4ff384ed8e","identity":"mutation:MUT_ANTI_WIZARDRY","terminal_conclusion":"adjust"}
{"fact_sha256":"30d6a59a7d1011c9d774886296a9c09ed566bb3593bedfaa00072944a337a530","identity":"mutation:MUT_ARMOURED_TAIL","terminal_conclusion":"keep"}
{"fact_sha256":"c09a75ad368b51244dcac30830d7b53eb06628f9f73f07fedbd91bc72b4a0201","identity":"mutation:MUT_ARTEFACT_ENCHANTING","terminal_conclusion":"adjust"}
{"fact_sha256":"9457c2319f16eeae1b6fd4e4c75ae3b42770ef2c9cee2a3e825771e9d6d62253","identity":"mutation:MUT_AUGMENTATION","terminal_conclusion":"keep"}
{"fact_sha256":"3aa20ed3e6f6f3f3b385b969eede44ffb0b8fd00ee7543b698cfc40ec5838e06","identity":"mutation:MUT_BEAK","terminal_conclusion":"adjust"}
{"fact_sha256":"5d90c37eb5d7e4f60b69eba1db428791f4c5c1c9bae1fc3ae8386f767b55e999","identity":"mutation:MUT_BIG_BRAIN","terminal_conclusion":"keep"}
{"fact_sha256":"f792e40c6bd18d29974adc0b17b2c95dadbd615b23d603360c34772cb81dbad0","identity":"mutation:MUT_BIG_WINGS","terminal_conclusion":"keep"}
{"fact_sha256":"4a8eebfb08f73d030737020619171d464fb192544eb950ab8ea083365a17d28b","identity":"mutation:MUT_BLACK_MARK","terminal_conclusion":"keep"}
{"fact_sha256":"6b382fe2edc1ff9341a4323cb91ace4edad109e7f5489c77657ebad75ca2582e","identity":"mutation:MUT_BOOMING_VOICE","terminal_conclusion":"keep"}
{"fact_sha256":"c9137915921198c7b3efabfca89a4d6980b1d2260caf5adb70bed6ed5c64a6ea","identity":"mutation:MUT_CAMOUFLAGE","terminal_conclusion":"keep"}
{"fact_sha256":"062a56b11408dce92a0308af04ac4e695c2e56bc8fdd59084296c6aec63ac0dc","identity":"mutation:MUT_CLARITY","terminal_conclusion":"keep"}
{"fact_sha256":"313378dbd926e85f721a30ee0215fba14fafaef5d0e385bdf1b95541fae4abf9","identity":"mutation:MUT_CLAWS","terminal_conclusion":"keep"}
{"fact_sha256":"259829e12aa51d95a73617e05caa58af0e5584b25ab3516ecb0f7ccf4c81e94c","identity":"mutation:MUT_CLEVER","terminal_conclusion":"adjust"}
{"fact_sha256":"d314735acbf6a824a4bc96fe23b4f5a95dd745e8067837da0778df1c3c43105b","identity":"mutation:MUT_CLUMSY","terminal_conclusion":"adjust"}
{"fact_sha256":"f6a52c0dfd74865227c3d72844e045b6811c096741bcbe77364dff25288b5187","identity":"mutation:MUT_COLD_BLOODED","terminal_conclusion":"keep"}
{"fact_sha256":"72e06fb117cf58f970b76d80ed742115f961c83b946b6e8a41fa23bafb64e387","identity":"mutation:MUT_COLD_RESISTANCE","terminal_conclusion":"keep"}
{"fact_sha256":"b8361cf4bfaade9a8dfc1de218116b9b3a002b082fef42a976a67294187b8e9f","identity":"mutation:MUT_COLD_VULNERABILITY","terminal_conclusion":"keep"}
{"fact_sha256":"b54379cf3eb416b8a4b0c12bbaf7df3a4cb65d78f06a8af77ff2a5d84f433762","identity":"mutation:MUT_CONDENSATION_SHIELD","terminal_conclusion":"keep"}
{"fact_sha256":"d1350a6e30c238ea7decc79d534a91e6f5338855716a16cf08c049e45b32db71","identity":"mutation:MUT_CONSTRICTING_TAIL","terminal_conclusion":"adjust"}
{"fact_sha256":"f467a9714360c981243d10cd1c9150b0b73d59df2f3e1c79c318e78f98b46029","identity":"mutation:MUT_CONTAMINATION_SUSCEPTIBLE","terminal_conclusion":"keep"}
{"fact_sha256":"7a674d2ddfae923c51957856363895ff2ad593b3091305da4ed2545775ff867d","identity":"mutation:MUT_CORRUPTING_PRESENCE","terminal_conclusion":"keep"}
{"fact_sha256":"2bbcd61af1a4574982b52944d18ecd35c87dea007b4d49eb828393acd77abff7","identity":"mutation:MUT_COWARDICE","terminal_conclusion":"adjust"}
{"fact_sha256":"0d56234d679c41e7bc366691493a7c2e458ee07df3cc20ee6bea4b5c2703d29d","identity":"mutation:MUT_DAYSTALKER","terminal_conclusion":"keep"}
{"fact_sha256":"493fafa35ca685c21f5b8eda264235ea1993428a22f0d73e66c3459301fc0d04","identity":"mutation:MUT_DEFORMED","terminal_conclusion":"keep"}
{"fact_sha256":"273f455b8ad4dcf084764e8dbe1204dfc2e5ba36eca7c05582581991ffcb93b1","identity":"mutation:MUT_DEMONIC_GUARDIAN","terminal_conclusion":"keep"}
{"fact_sha256":"0712103cf5b8fd27808b8d4af65d65cfc97cc6a683d3050475b96dfda63003ff","identity":"mutation:MUT_DEMONIC_MAGIC","terminal_conclusion":"keep"}
{"fact_sha256":"e2a6312727d6ed301a912fee75a75d150c52e1aff2898b15509eff5d8554f7d7","identity":"mutation:MUT_DEMONIC_TOUCH","terminal_conclusion":"keep"}
{"fact_sha256":"d7bd6a172b67e30424d33772a3a8b28d6652f4bfc85dddd7e528bbc59bb5cd6a","identity":"mutation:MUT_DEMONIC_WILL","terminal_conclusion":"keep"}
{"fact_sha256":"6bfb181bff4c35df4b7fe66c26c4c46e4e92f09d592c835cbeb9a39a2459ff3e","identity":"mutation:MUT_DEVOLUTION","terminal_conclusion":"keep"}
{"fact_sha256":"603a71555cc2e287908ef6d873f137eba4776bfb877b7abf4d3af6f50c57dc0d","identity":"mutation:MUT_DEVOUR_ON_KILL","terminal_conclusion":"keep"}
{"fact_sha256":"6fa33cd9dc275a167b8c85cc4d9ab697f4f4b0d8adda24a40222b8a625d1308e","identity":"mutation:MUT_DISTORTION_FIELD","terminal_conclusion":"adjust"}
{"fact_sha256":"3b34af489d0e906a8b65351396de414dc0856806eab097a05c907350f8c81a18","identity":"mutation:MUT_DISTRIBUTED_TRAINING","terminal_conclusion":"keep"}
{"fact_sha256":"68dd0f551318647ed049012002c2403c7030eb59638b01838a870f31d3c6e489","identity":"mutation:MUT_DIVINE_ATTRS","terminal_conclusion":"keep"}
{"fact_sha256":"2e59a7d302f327671b7822be17ea88f49e73fd601e9c323b9f1d56783a366cc4","identity":"mutation:MUT_DOPEY","terminal_conclusion":"adjust"}
{"fact_sha256":"45ba8995bcd160ad8c9a5004e2cab5733fd3d5165b0959de695746057f5c75bb","identity":"mutation:MUT_DOUBLE_POTION_HEAL","terminal_conclusion":"adjust"}
{"fact_sha256":"19f00514c3842a653d025e7ceb5e577b7a9ab6c37ff9884351a91219febb3d9d","identity":"mutation:MUT_DRUNKEN_BRAWLING","terminal_conclusion":"adjust"}
{"fact_sha256":"9904f562cb9f202b6aaeb281b0c556927b0f771466c904c120c7733ee9888343","identity":"mutation:MUT_EFFICIENT_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"2c704ea69b2aa43491db86b581ddf6b4952d93d57e90901d2707779ce251bd48","identity":"mutation:MUT_EFFICIENT_METABOLISM","terminal_conclusion":"keep"}
{"fact_sha256":"ab3aee75af68e0f9b66a804ab566735282dd32255ac9dd388d750768acd1e114","identity":"mutation:MUT_EPHEMERAL_SHIELD","terminal_conclusion":"keep"}
{"fact_sha256":"148e51b456c8a8d8f2a55b7d88a6ccb36114a80edb378fef812d4c7fc28466ba","identity":"mutation:MUT_EVOLUTION","terminal_conclusion":"keep"}
{"fact_sha256":"26b60615438b13fed37a2d973cab960693ceffa8a756bc2d09e863d3adde5692","identity":"mutation:MUT_EXPLORE_REGEN","terminal_conclusion":"adjust"}
{"fact_sha256":"4e86a3542c9eb24f786530507c77ef37a5de25b617576754b060684ce40da397","identity":"mutation:MUT_EYEBALLS","terminal_conclusion":"keep"}
{"fact_sha256":"a2632cf7496bb8ab015350403ab1e451c9f7a9a305ba662b4797137718205b84","identity":"mutation:MUT_FAITH","terminal_conclusion":"keep"}
{"fact_sha256":"16397588967245464ec1c5c1ddd9e81b05670524658702d86d258a96e66aab55","identity":"mutation:MUT_FANGS","terminal_conclusion":"adjust"}
{"fact_sha256":"e40b8d22fabe7b40e86a8a4adaef6a051b911c7febada5feb0ba7b834b0dcb6f","identity":"mutation:MUT_FAST","terminal_conclusion":"keep"}
{"fact_sha256":"cf60b1bf2266ee34ddfe5095006273a69a19d337296a4de5a2b1d221c07cbab7","identity":"mutation:MUT_FEED_OFF_SUFFERING","terminal_conclusion":"adjust"}
{"fact_sha256":"96115e231b15b1fc1adb8ded1a621be472d185eab7965ba82f3bcd825021d31a","identity":"mutation:MUT_FLAME_CLOUD_IMMUNITY","terminal_conclusion":"keep"}
{"fact_sha256":"64ac3f58ef80a3988b69f3011c0934baafb973804f952d09e9b6c60a709d59fb","identity":"mutation:MUT_FLAT_HP","terminal_conclusion":"keep"}
{"fact_sha256":"e1b17fe60256ab8ae6850239bbd3620fefcce0a1960957c4a12af5e1723fc417","identity":"mutation:MUT_FLOAT","terminal_conclusion":"keep"}
{"fact_sha256":"a8bdeee8a0c6c2020ee4ff377b70cb51cc27f1d64b092783ad3538fe2384d2d7","identity":"mutation:MUT_FORLORN","terminal_conclusion":"keep"}
{"fact_sha256":"44e150809bd651e79a94564f7db782b76793f1416abeef9cde49c2dfc9d03a0b","identity":"mutation:MUT_FORMLESS","terminal_conclusion":"adjust"}
{"fact_sha256":"c6cdba104cc0c8aaee278aa1b229a2405d0a2423524c2f1e30a29f8268f75e82","identity":"mutation:MUT_FOUL_SHADOW","terminal_conclusion":"keep"}
{"fact_sha256":"5562e78573aad209521c7369f21c4c38376dd00c19f69d944edc24008c99990a","identity":"mutation:MUT_FOUL_STENCH","terminal_conclusion":"adjust"}
{"fact_sha256":"6da8433f305eb072a1da05c0c4870ada61b459e72aa6acdc16f39f3feb51ed71","identity":"mutation:MUT_FRAIL","terminal_conclusion":"adjust"}
{"fact_sha256":"414136fc296c3aef1d5a37466d86801a9af5c59d099a21032280744fce86a6fb","identity":"mutation:MUT_FREEZING_CLOUD_IMMUNITY","terminal_conclusion":"keep"}
{"fact_sha256":"8b9a94338a06fe5d372a803c50545321af964fab066581276341971f15c0b615","identity":"mutation:MUT_FROG_LEGS","terminal_conclusion":"keep"}
{"fact_sha256":"6ccbd654f1d2b4f7e31bcb2449c7051b7db9c1f3cd6da33514444412d1080156","identity":"mutation:MUT_GELATINOUS_BODY","terminal_conclusion":"keep"}
{"fact_sha256":"48d2fba35a66bf40f0d1749672274475bb6f76b8aff4288ff7cb6f60031c75fa","identity":"mutation:MUT_HEAT_RESISTANCE","terminal_conclusion":"keep"}
{"fact_sha256":"6f601efae5e3410ac2cc01d56d5a6a90e02c9605b7e7186366ffb4142d25b422","identity":"mutation:MUT_HEAT_VULNERABILITY","terminal_conclusion":"keep"}
{"fact_sha256":"1c32fa5c4186459641d44cfa27d118794a40609295bbba5389c522859cac8244","identity":"mutation:MUT_HEX_ENHANCER","terminal_conclusion":"adjust"}
{"fact_sha256":"f97ec8966f451f706b51e3b315c5c20b0bfba11b240e4ec4888b7c2772667232","identity":"mutation:MUT_HIGH_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"5584d1116cea7c695abc0ebe1fdacfeb5f191e9bdf0d9a5d327ef120c0af2c4f","identity":"mutation:MUT_HOOVES","terminal_conclusion":"keep"}
{"fact_sha256":"14c3bba7c47b0f50d071ec38abe0e96cf5501c1280e1ddc31b098b5b61197c97","identity":"mutation:MUT_HORNS","terminal_conclusion":"adjust"}
{"fact_sha256":"a50cca7b6f94a1ed63dbf1885141e55e1d60e3850ab0731e80797cf271520427","identity":"mutation:MUT_HP_CASTING","terminal_conclusion":"adjust"}
{"fact_sha256":"b458a3f8282c565293ce46197836d62df2f2a5d6e4e32c603a4d3556fbf45dec","identity":"mutation:MUT_HURL_DAMNATION","terminal_conclusion":"keep"}
{"fact_sha256":"77cf71f5b8fa3417193d684908335dbb7156d8163eead6953bd424e4b530dda8","identity":"mutation:MUT_ICEMAIL","terminal_conclusion":"keep"}
{"fact_sha256":"dcd44641e96951a0ba99bbf2ce5c53daa24636df540d961a02b6ab7763c604a5","identity":"mutation:MUT_ICY_BLUE_SCALES","terminal_conclusion":"keep"}
{"fact_sha256":"9da94cf2d3ee6241c00a12465788fbb8342f8be93efe943fa2f71e0fe308f869","identity":"mutation:MUT_IGNITE_BLOOD","terminal_conclusion":"adjust"}
{"fact_sha256":"ec2c48cac45dbbe676a803b73eefed0c3f29b6bbfbe450af619b67ec1aff9b64","identity":"mutation:MUT_INEXPERIENCED","terminal_conclusion":"keep"}
{"fact_sha256":"99ab216ba705f4f45a044da0c2af15d5eb74bae998126f9ff56450984e3ea42c","identity":"mutation:MUT_INHIBITED_REGENERATION","terminal_conclusion":"keep"}
{"fact_sha256":"4f38ad86e0890b5393a914f5f1dec284c5378b85b5698112c603a882038486d4","identity":"mutation:MUT_INITIALLY_ATTRACTIVE","terminal_conclusion":"adjust"}
{"fact_sha256":"c9f2424a4d595b4de55c376f2832f05246dc3dd3f59f5219f0cd163f38c0241f","identity":"mutation:MUT_INNATE_CASTER","terminal_conclusion":"keep"}
{"fact_sha256":"6c521b044e4a0e4ee5a70aafadc789a586e11ed328e02ee8c41bf6d9ff7f8924","identity":"mutation:MUT_INVIOLATE_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"6fda396fb0fa5d0b800f38ce928ffdf34d76e8982eef2e250f6256f729412346","identity":"mutation:MUT_IRIDESCENT_SCALES","terminal_conclusion":"keep"}
{"fact_sha256":"e7b04d6baac610454ad9ea222da6a4a51bcc8b7a7bcbaeafcc60af8c0fad4939","identity":"mutation:MUT_IRON_FUSED_SCALES","terminal_conclusion":"adjust"}
{"fact_sha256":"70d0a679158a7b3c73f0b4bea821be2444799808b98a5a0c625570f322ccd3e3","identity":"mutation:MUT_JELLY_GROWTH","terminal_conclusion":"keep"}
{"fact_sha256":"87a8361d3a4b6d2ccad288670b370881fee7eb3e30d3707612934de9cb1aad12","identity":"mutation:MUT_JELLY_MISSILE","terminal_conclusion":"keep"}
{"fact_sha256":"738576edf1962f2dd4bddea9538ebc847fb2388b037e942f6e0a4bd7bebff4b3","identity":"mutation:MUT_LARGE_BONE_PLATES","terminal_conclusion":"keep"}
{"fact_sha256":"d7d2be9f574118176dc03dc4be0e9953add6bdcbc87b8a106edbdafc2df5e2f6","identity":"mutation:MUT_LOW_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"c288215305dc59fc2b4212c4ae3b0b4b92034f5e6c6186d7aac7cd9a49795fa3","identity":"mutation:MUT_LUCKY","terminal_conclusion":"adjust"}
{"fact_sha256":"b33015a9c4ff50848a7e28d75026ca8c84d130a2e381ae1cee1e084e005b3237","identity":"mutation:MUT_MAKHLEB_DESTRUCTION_COC","terminal_conclusion":"keep"}
{"fact_sha256":"6ebde81121d7b41f82fb95d26a351dd1b434ec9068266cf804495c895d77c4b3","identity":"mutation:MUT_MAKHLEB_DESTRUCTION_DIS","terminal_conclusion":"keep"}
{"fact_sha256":"2e47e5a0773ce64d771ae2533416c44889f30a75702c808371f1d3f2c67f76c4","identity":"mutation:MUT_MAKHLEB_DESTRUCTION_GEH","terminal_conclusion":"keep"}
{"fact_sha256":"a60d977a82fed05971479165bc0543510ff6e6945b9d0043a69f36c5e0df45bd","identity":"mutation:MUT_MAKHLEB_DESTRUCTION_TAR","terminal_conclusion":"keep"}
{"fact_sha256":"074d54b1b177c12cc36065317b8c9737e87a3c79be31a29b1b52f6d3607db8dc","identity":"mutation:MUT_MAKHLEB_MARK_ANNIHILATION","terminal_conclusion":"keep"}
{"fact_sha256":"aed67da33408df5e47393be199580c33ba0e94d79812fe1782043532de5c04b5","identity":"mutation:MUT_MAKHLEB_MARK_ATROCITY","terminal_conclusion":"keep"}
{"fact_sha256":"42b837b92c7bf5b998363315642c2936747af8cb9084d5a278232caea58be3ea","identity":"mutation:MUT_MAKHLEB_MARK_CARNAGE","terminal_conclusion":"keep"}
{"fact_sha256":"13c96a1cc56ca294e5b19353e044709dd13db73d8aeb05f38b49f2a1d56abdb3","identity":"mutation:MUT_MAKHLEB_MARK_CELEBRANT","terminal_conclusion":"adjust"}
{"fact_sha256":"74dae63ba161720a8e3f7a652252266fd1fefbada566a8bcd1ae21a21afc9150","identity":"mutation:MUT_MAKHLEB_MARK_EXECUTION","terminal_conclusion":"adjust"}
{"fact_sha256":"cbfe9046d367ea57c1740d3354ab9ebb358936790af2c4bfbee5ad86a3c70304","identity":"mutation:MUT_MAKHLEB_MARK_FANATIC","terminal_conclusion":"adjust"}
{"fact_sha256":"971a586b8dfc64891d41485f0e18ec42dfc842fb4cf1026e07ed2774c0b68edf","identity":"mutation:MUT_MAKHLEB_MARK_HAEMOCLASM","terminal_conclusion":"keep"}
{"fact_sha256":"2f85a620ad441fbae324e1698d3c637bfe99548777372bcfba523f9fa087b003","identity":"mutation:MUT_MAKHLEB_MARK_LEGION","terminal_conclusion":"adjust"}
{"fact_sha256":"6b2d4808022732703e970a8bfb8e0c9216e3bdcfe9b2efba3df0a8a20c07a04b","identity":"mutation:MUT_MAKHLEB_MARK_TYRANT","terminal_conclusion":"keep"}
{"fact_sha256":"8e19dc7976d5191094ed470f1682b36454c9f9fd0dea7a0dfc4541faa482387c","identity":"mutation:MUT_MANA_LINK","terminal_conclusion":"adjust"}
{"fact_sha256":"cbf95ca8a7e5c0d2e507e59dc03fc1cd75ab3b199a0e9e038810953134e44ffc","identity":"mutation:MUT_MANA_REGENERATION","terminal_conclusion":"adjust"}
{"fact_sha256":"0f8eeda7404d7f65f1d7b9b10ea7dbf17562652019c95300ae3b4aed2f71b449","identity":"mutation:MUT_MANA_SHIELD","terminal_conclusion":"adjust"}
{"fact_sha256":"245fa31dd2625f326057a766de1224bddd7b7f53b490eeaa07cfa0a978c0efb8","identity":"mutation:MUT_MEEK","terminal_conclusion":"adjust"}
{"fact_sha256":"ef65e04c8490dd91dde7f6b515074867e756e776d76956225292420cb882511c","identity":"mutation:MUT_MERTAIL","terminal_conclusion":"adjust"}
{"fact_sha256":"270992bffe48203c5d91b58baf116c2fca9dc559650ae39c33fabfb374453adc","identity":"mutation:MUT_MISSING_EYE","terminal_conclusion":"keep"}
{"fact_sha256":"74f177d389b5479f4f18137a1db0f90d5ddeece52c9a959224d65f7ae5400e05","identity":"mutation:MUT_MISSING_HAND","terminal_conclusion":"adjust"}
{"fact_sha256":"91011dda40d21d0a65c032a0e851d492307a4d631e75d32818268588a57e0718","identity":"mutation:MUT_MNEMOPHAGE","terminal_conclusion":"adjust"}
{"fact_sha256":"7bc60d5f9170394ffb6f408c8bf955d7937a0f8935c81b0758737b8a36c1c094","identity":"mutation:MUT_MOLTEN_SCALES","terminal_conclusion":"adjust"}
{"fact_sha256":"a040a34fb626eba3190679609c88ccc0f78f1a39a8e3586b1bd96623db5b1424","identity":"mutation:MUT_MP_WANDS","terminal_conclusion":"adjust"}
{"fact_sha256":"f67d732b0a782bd0360aaf530da426077a63081ab058d1d905c73730bf99b0a2","identity":"mutation:MUT_MULTILIVED","terminal_conclusion":"keep"}
{"fact_sha256":"9063104287c4c102b1a62fa966b9447759a342e07e00f2386db490fb202b1958","identity":"mutation:MUT_MUTATION_RESISTANCE","terminal_conclusion":"keep"}
{"fact_sha256":"fc5d7fbf347910d212f4eea6b3230d03b1b6097ea478deaa825cd5b297625b0b","identity":"mutation:MUT_NECRO_ENHANCER","terminal_conclusion":"keep"}
{"fact_sha256":"f6d81077b7ffc4bb21ae6fb6496276e6c5ad3a204028fe03f0486241f86175f1","identity":"mutation:MUT_NEGATIVE_ENERGY_RESISTANCE","terminal_conclusion":"keep"}
{"fact_sha256":"b7c20326532051f8126c26eb7e03c8a3195f46ffe8b1a9598aab47dc0cd6654a","identity":"mutation:MUT_NIGHTSTALKER","terminal_conclusion":"keep"}
{"fact_sha256":"495f471fc0f3ed7d28080b29de1145cf7bd5b2778d104c35d837f0232bf22720","identity":"mutation:MUT_NIMBLE_SWIMMER","terminal_conclusion":"keep"}
{"fact_sha256":"47bd93fa14cb5bee3ff168255f2e1f482b71e60c9b27ab1850cdef706dc2e2df","identity":"mutation:MUT_NO_AIR_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"09a92ff5d57423575a4016faaaca9e73a49d46bf47c947185ae6a95aa4ebd1d2","identity":"mutation:MUT_NO_ALCHEMY_MAGIC","terminal_conclusion":"keep"}
{"fact_sha256":"99f6854d0509694f56371b1af5078aae7a4f1b14133c502f1fc0006a91d5bee9","identity":"mutation:MUT_NO_ARMOUR","terminal_conclusion":"adjust"}
{"fact_sha256":"988a7f3ff13cf93c0250e2c46bcdd9f6e21cff0f716c25c95eab71d6f1f084d6","identity":"mutation:MUT_NO_ARMOUR_SKILL","terminal_conclusion":"adjust"}
{"fact_sha256":"9c1916ed37a3e0cc8fe0c7ec1b266372199984377339edcdd957bbc2da88d51c","identity":"mutation:MUT_NO_ARTIFICE","terminal_conclusion":"adjust"}
{"fact_sha256":"0bef8dde75e5d40d548636f4a26c3b07b7e2fe64ba1c893eaac06964f961d3e8","identity":"mutation:MUT_NO_CONJURATION_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"9580e283d10192e0d356dd179ca7341bf794062b3e9f75768d5a929f2da81673","identity":"mutation:MUT_NO_DODGING","terminal_conclusion":"keep"}
{"fact_sha256":"90909542183c6f16bafc5fa11dd16a0b79977a8eafaa7c25e7c622d69988f1e7","identity":"mutation:MUT_NO_DRINK","terminal_conclusion":"keep"}
{"fact_sha256":"42ea828630ae6c8408e144dbfb26c0167e5e6ae4c6fbf84c0c1f01fbde3844b1","identity":"mutation:MUT_NO_EARTH_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"26bf2bc7d3b4a3700c84c0115a71ab9c3f54afa25347a9251ad7aea1a93b4ba5","identity":"mutation:MUT_NO_FIRE_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"81c5bcb04014b80663710b28b0787cf7451cce75e2d2907f5f25cdda0ae459c8","identity":"mutation:MUT_NO_FORGECRAFT_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"8476e69e1b83bd8f6ed09c033cac5904e1dc74ccdbdbb17473a0470093d888fa","identity":"mutation:MUT_NO_FORMS","terminal_conclusion":"adjust"}
{"fact_sha256":"624c789b8cf1af606d8789ed8b0d50bade5309845cc8dac6930ce3d948080b63","identity":"mutation:MUT_NO_GRASPING","terminal_conclusion":"keep"}
{"fact_sha256":"fe4a32a54d0689de9d3858f9414a80c836f3a961720a836073503f3f9c3fbb50","identity":"mutation:MUT_NO_HEXES_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"928cf5776907a1b4507b7286534e30c8b51f8d5b9a7affa514604ec545e8021b","identity":"mutation:MUT_NO_ICE_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"4ee4fac37537fdee89d6e47b485c5ec631c5afd045306b323ea4d36b5f86f3da","identity":"mutation:MUT_NO_JEWELLERY","terminal_conclusion":"adjust"}
{"fact_sha256":"9480c5e775e9b3d8c4a23f05d3e3f74ffdf809aba14fcc6d04fdec1c7d265f96","identity":"mutation:MUT_NO_LOVE","terminal_conclusion":"keep"}
{"fact_sha256":"63bec44c218c39a34e6e5f2ede6a407ba7c16b7e45b65761fb71713b904e0de9","identity":"mutation:MUT_NO_NECROMANCY_MAGIC","terminal_conclusion":"keep"}
{"fact_sha256":"a5b37454017e8c15fdfb15a4378c69f974170570970a3867a987d5ef1b309cd6","identity":"mutation:MUT_NO_POTION_HEAL","terminal_conclusion":"keep"}
{"fact_sha256":"a14e2e97240182994a5aa4f755fcdd5fbfceaf9699af5b99dd2b9eb194e36f54","identity":"mutation:MUT_NO_REGENERATION","terminal_conclusion":"adjust"}
{"fact_sha256":"adbd2d6b3ba648cb6dc616ac2daec6e5c3c236de38f64693dec0356c47124008","identity":"mutation:MUT_NO_STEALTH","terminal_conclusion":"keep"}
{"fact_sha256":"661bd977889f5741b57fbf6a335e17d9a7905ec7b353035f9e3d993ae2eeea34","identity":"mutation:MUT_NO_SUMMONING_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"91f8e10ddbe92bdd0d9532474a1a10eef548d8f91945ffd121bf3ba835fa453b","identity":"mutation:MUT_NO_TRANSLOCATION_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"142adabf53dbeffc7e91210f4a9fb4e0915d347d7e26f0a4b099c3dae59ce257","identity":"mutation:MUT_OOZE_FLOOD","terminal_conclusion":"keep"}
{"fact_sha256":"47fb22064162980f6c5494ba5067a03a21ab15d31a06f03f0708c2de228f5f6f","identity":"mutation:MUT_PASSIVE_FREEZE","terminal_conclusion":"keep"}
{"fact_sha256":"8c83fdca8d912e9056c828ca11dfaa792d03ff1ae53812aad26e8342509c0a81","identity":"mutation:MUT_PASSIVE_MAPPING","terminal_conclusion":"keep"}
{"fact_sha256":"cd236dc36f990d653b123c1dc0d4f4d64ae7e3a505d59efbe4fb06ba05bec4eb","identity":"mutation:MUT_PAWS","terminal_conclusion":"keep"}
{"fact_sha256":"c76f9629a355bcdb802639019c22af718f0f4e665403e1de611666356509fbe0","identity":"mutation:MUT_PERSISTENT_DRAIN","terminal_conclusion":"keep"}
{"fact_sha256":"1d4268c8ec6abb32e4e49a58560e3259e54a162505242c494871bd0d8b239784","identity":"mutation:MUT_PHYSICAL_VULNERABILITY","terminal_conclusion":"keep"}
{"fact_sha256":"4b04fd283fa78bc7c1f73ea4ea45e1a51ddc01afee89f4a622fecf1cd94bd6f7","identity":"mutation:MUT_POISON_RESISTANCE","terminal_conclusion":"keep"}
{"fact_sha256":"2e506bc899848325f08381628f96a544175daa51f59c64a451a4a8f168005c64","identity":"mutation:MUT_POOR_CONSTITUTION","terminal_conclusion":"adjust"}
{"fact_sha256":"cd6dea986ad3ea43904bfeee7a960e27c2556f499ed85c84c2dc5b1d1bad2fd5","identity":"mutation:MUT_POTION_FUNGUS","terminal_conclusion":"keep"}
{"fact_sha256":"6cc932bd09fc8f8424157a956d85caf466dda48551efd525a229d32bfb06b24f","identity":"mutation:MUT_POWERED_BY_DEATH","terminal_conclusion":"keep"}
{"fact_sha256":"4f0efe08c17dea4cbb1636451051d0d66b16eb27784aee9b1afc7ef929593873","identity":"mutation:MUT_POWERED_BY_PAIN","terminal_conclusion":"adjust"}
{"fact_sha256":"218f6f5bb2361772ce34d29886363f2987c15ab224587e08c7f97cd4e80cff58","identity":"mutation:MUT_PROTEAN_GRACE","terminal_conclusion":"keep"}
{"fact_sha256":"d6f788a74d75cef4900c5d4f9eadfe3181a83767f3b2e10a2c9f03485820369f","identity":"mutation:MUT_PSEUDOPODS","terminal_conclusion":"keep"}
{"fact_sha256":"eb3e3e75b26bea59e9645abd109ed776b93734b7d4f3a874298956a4988fc6b1","identity":"mutation:MUT_QUADRUMANOUS","terminal_conclusion":"keep"}
{"fact_sha256":"fed03c777ac7d371a47f34e246840bcdc650cc29b94e73e06281e478c7f8054f","identity":"mutation:MUT_RECKLESS","terminal_conclusion":"keep"}
{"fact_sha256":"efaf63702c0cee85680535410aa7dcc9d282a3be77a7af3e8ca2a77b8c3381dc","identity":"mutation:MUT_REFLEXIVE_HEADBUTT","terminal_conclusion":"adjust"}
{"fact_sha256":"17565a19fb0e43cb67476759fd59973c7fd604ff11d6628052f7b4e2fa0353da","identity":"mutation:MUT_REGENERATION","terminal_conclusion":"keep"}
{"fact_sha256":"bb1309d717b98babcbfc675bd09ff163caa907907f7715e30ad09a42a6867643","identity":"mutation:MUT_REMOVED_MUTATION","terminal_conclusion":"keep"}
{"fact_sha256":"8e925a2f303c225ed7a2c50517d5223a7cb8840d896d3a23357bad10f7f9160d","identity":"mutation:MUT_RENOUNCE_POTIONS","terminal_conclusion":"keep"}
{"fact_sha256":"f92a4dbe3d793503fcc0f81f5e035fdb4af3cf0e552be1aa7b9039898406a874","identity":"mutation:MUT_RENOUNCE_SCROLLS","terminal_conclusion":"adjust"}
{"fact_sha256":"8aa8a10c5970ea5e7d5aa39aff4a837271cc18fc40bbcd19907e10495c9d67e7","identity":"mutation:MUT_ROBUST","terminal_conclusion":"keep"}
{"fact_sha256":"71ef837f0a9e3c07212b65fe96425137e6ad8b9eb374c7cee048688d71f81742","identity":"mutation:MUT_ROLLPAGE","terminal_conclusion":"adjust"}
{"fact_sha256":"c2fd6ab9621d7e50faf433c7f81742481146b205a12414cf5fd3107b98f681cf","identity":"mutation:MUT_RUGGED_BROWN_SCALES","terminal_conclusion":"adjust"}
{"fact_sha256":"7126a2623747dc1e1f3bb58a620c7988d31def82ca40cfe84ded49386a666ea3","identity":"mutation:MUT_RUNIC_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"a8653830baf7d9d27efcde5e180208e55ba494a8ebbe9370772f60d5308cab89","identity":"mutation:MUT_SANGUINE_ARMOUR","terminal_conclusion":"keep"}
{"fact_sha256":"39c55fa02b990e562bbafa1210fc3dbb377890dcb94aca17c4da42e7bbee737d","identity":"mutation:MUT_SCREAM","terminal_conclusion":"keep"}
{"fact_sha256":"1e7a117cf5f5c96642aa7a9804cea3afd89fdab8f2ff705964545124955a32a4","identity":"mutation:MUT_SHAGGY_FUR","terminal_conclusion":"adjust"}
{"fact_sha256":"dc308444f7ec1b31b3f25f5681a1da9f7f3756453e4a91e560be0ba999c240af","identity":"mutation:MUT_SHARP_SCALES","terminal_conclusion":"adjust"}
{"fact_sha256":"372cc9f15e51737dac66a50e8d4e4c3e68ba8ebc455618a31b1c477ac9b460d6","identity":"mutation:MUT_SHOCK_RESISTANCE","terminal_conclusion":"keep"}
{"fact_sha256":"3dc65a5314b4f458989ff4edefbc1b99635852d5f9309c1d4a341099c219e1ed","identity":"mutation:MUT_SHOCK_VULNERABILITY","terminal_conclusion":"keep"}
{"fact_sha256":"a29f5e51280510ba999d44e43d7327fdf578bc353551651749af56a90e14f8f1","identity":"mutation:MUT_SHORT_LIFESPAN","terminal_conclusion":"keep"}
{"fact_sha256":"04d1f5a754a7ba0b1b86c5e7bd806cdc6c52a6288aafb1a0cc35e05a6293d2e5","identity":"mutation:MUT_SILENCE_AURA","terminal_conclusion":"keep"}
{"fact_sha256":"8cac3d8f9399622046a383039ea9d7d014d3114bcef108c05153546ce204315b","identity":"mutation:MUT_SLIME_SHROUD","terminal_conclusion":"adjust"}
{"fact_sha256":"cdb11c88febee13981d1af85a4e0689056fb5070c347f2913f7509800a9c07e0","identity":"mutation:MUT_SLIMY_GREEN_SCALES","terminal_conclusion":"keep"}
{"fact_sha256":"1c0c60d69f255bd063a8dfc0a253e830a05d1dca1f113292af87f9bab5a01bbb","identity":"mutation:MUT_SLOW","terminal_conclusion":"keep"}
{"fact_sha256":"f4880f786ff640282eb3a63e715bcbd1c3428eeb1e1fa6d06cbb6a989b5f7198","identity":"mutation:MUT_SLOW_REFLEXES","terminal_conclusion":"keep"}
{"fact_sha256":"a5648baa19ab99b544fcd8a108ab1128eda017d7417b4989fc875c1715a3b255","identity":"mutation:MUT_SLOW_WIELD","terminal_conclusion":"keep"}
{"fact_sha256":"0b862057c981ebf99ad7e14f0e873df5d621cab4ab4ad0e4729258587403d100","identity":"mutation:MUT_SPATIAL_ENTANGLEMENT","terminal_conclusion":"adjust"}
{"fact_sha256":"f790f2ac238d5008ff2eedd536ef99a7f72ff6eb43033dc25cd5f7f88e480eda","identity":"mutation:MUT_SPELLCLAWS","terminal_conclusion":"keep"}
{"fact_sha256":"094df52215714603f1aac6636ff125709485185888bc8fea79511fef98b9e8de","identity":"mutation:MUT_SPINY","terminal_conclusion":"adjust"}
{"fact_sha256":"592215ce6ecf718de50483329d637f06ccdc0d2401a50f810046d5b9063dc190","identity":"mutation:MUT_SPITEFUL_BLOOD","terminal_conclusion":"keep"}
{"fact_sha256":"7e981f630eef0777dfba4f8521efca8b99bc69e07d521a78fdff4851d8a4cb54","identity":"mutation:MUT_SPIT_POISON","terminal_conclusion":"keep"}
{"fact_sha256":"0424178b8aa9687c0c9e89e3e2c19286a5ce248f64ca18d749e6cdae4bd23fa8","identity":"mutation:MUT_STEAM_RESISTANCE","terminal_conclusion":"keep"}
{"fact_sha256":"e628f95e557c4c3cb14d45f998ac029b3228bd47128591315469f2503c12e0a2","identity":"mutation:MUT_STINGER","terminal_conclusion":"keep"}
{"fact_sha256":"d3a3bb58583cfd109f2dd1d9aa37c4c28726fc26b7f279173af4643854c428c3","identity":"mutation:MUT_STONE_BODY","terminal_conclusion":"keep"}
{"fact_sha256":"f3db6a2f61c9644f92040542a699544a02209062555148eac886e4b945db4a76","identity":"mutation:MUT_STRONG","terminal_conclusion":"keep"}
{"fact_sha256":"d1881d92cdf29afb8a170a81fd72fbb15d62b91ebd15b3b6ccda21db68e365e6","identity":"mutation:MUT_STRONG_WILLED","terminal_conclusion":"keep"}
{"fact_sha256":"911dcf3d1bc149f747e7b9430aebff54c082896d4b7760fb685b2d701b6c217d","identity":"mutation:MUT_STURDY_FRAME","terminal_conclusion":"adjust"}
{"fact_sha256":"07c58a92f642810e936a05468c2c01f059c6cbfba4a8142e9b53122beacdc6d6","identity":"mutation:MUT_SUBDUED_MAGIC","terminal_conclusion":"keep"}
{"fact_sha256":"61e6a1e08a275a31bfac1f841ab01a20f496fbf7392cd02ecbe00b4e92d7fdc1","identity":"mutation:MUT_TALONS","terminal_conclusion":"keep"}
{"fact_sha256":"5f6a2d743944525461fc52860cfab057d480f5bb59da2b7110923c19bb319532","identity":"mutation:MUT_TELEPORTITIS","terminal_conclusion":"adjust"}
{"fact_sha256":"996fa210031aae38e8c42b6f3914e0b2d60de6810333040b5872379ee25736f3","identity":"mutation:MUT_TEMPERATURE_SENSITIVITY","terminal_conclusion":"keep"}
{"fact_sha256":"3ff5cc02921c3aa59615b3afa663caefdbe5afc13af54ef3d1c208fd36e2d6e8","identity":"mutation:MUT_TENDRILS","terminal_conclusion":"keep"}
{"fact_sha256":"fcd8f2c9fd3ca6ebe085ded6e0f454433ceadd799567125123ceb0aac4f6e3ec","identity":"mutation:MUT_TENGU_FLIGHT","terminal_conclusion":"keep"}
{"fact_sha256":"a25955552d5e051aaeceabee2ac45e1d0334f5e23e972ba84b4f7b6d361bfffc","identity":"mutation:MUT_TENTACLE_ARMS","terminal_conclusion":"keep"}
{"fact_sha256":"21aa9a8303d8a232ed48e8d8000a260c3179c3a1c6ec205e846522e3a4d9e290","identity":"mutation:MUT_TENTACLE_SPIKE","terminal_conclusion":"keep"}
{"fact_sha256":"2533167af17186dd19db96dfc4b1e73aed55bc502d2239931e44652ffcd05d42","identity":"mutation:MUT_THIN_METALLIC_SCALES","terminal_conclusion":"keep"}
{"fact_sha256":"2170f1c3005752da39136c7dcb7828fe5de80769a6e1cd8e4e5d6f3a1a0bd358","identity":"mutation:MUT_THIN_SKELETAL_STRUCTURE","terminal_conclusion":"adjust"}
{"fact_sha256":"0e075d6c00b2474ed7e4be40ceb20f04d88cfcfe31c603ba462cba4f828039f2","identity":"mutation:MUT_TIME_WARPED_BLOOD","terminal_conclusion":"keep"}
{"fact_sha256":"fdab202770ec6eab99129131dcf2618a2cb743da441a7263a9c1ce977e2e0d22","identity":"mutation:MUT_TORMENT_RESISTANCE","terminal_conclusion":"keep"}
{"fact_sha256":"17b7cdae565c90da406b7d78b95333669eec97fad895215df74418b3e20e7943","identity":"mutation:MUT_TOUGH_SKIN","terminal_conclusion":"adjust"}
{"fact_sha256":"9bdd4b168a1976744dcc9d1e08592bc02fad79b7f8b1b638bc7da333ccd34667","identity":"mutation:MUT_TRANSLUCENT_SKIN","terminal_conclusion":"keep"}
{"fact_sha256":"c5285ce8c5dd763f17887b0714976a1a32d3c7a3bb36e31545314f7fc2d8c6cf","identity":"mutation:MUT_TREASURE_SENSE","terminal_conclusion":"adjust"}
{"fact_sha256":"9dd22b7365cf1099c47cce5dedd5e85c3d2416a8264f4c7e8bae483303e128f4","identity":"mutation:MUT_TRICKSTER","terminal_conclusion":"keep"}
{"fact_sha256":"f1a9e58b2e58459790c94a412dc626f5e805ad615f2cc4fc5dbf54e3d41e8b91","identity":"mutation:MUT_UNSKILLED","terminal_conclusion":"keep"}
{"fact_sha256":"ed50348e626fbef759eec219488b5d91a95bf4a3b5b59b18d780ae3ae7e55090","identity":"mutation:MUT_WARMUP_STRIKES","terminal_conclusion":"keep"}
{"fact_sha256":"d965623e81f2a94f6f98b67ab86ff3548662b967a95ea88d2225275a31598f6b","identity":"mutation:MUT_WEAK","terminal_conclusion":"keep"}
{"fact_sha256":"5e459b62f61cd324f7dd0c86c6ca7b40f56f2ebdc7f32c42ae69e822fe3780bf","identity":"mutation:MUT_WEAKNESS_STINGER","terminal_conclusion":"keep"}
{"fact_sha256":"dabcb46d529b4ac0f7bf4ba1f3527a28b8b322c6b3558bab07ecbf1ce952a085","identity":"mutation:MUT_WEAK_WILLED","terminal_conclusion":"keep"}
{"fact_sha256":"1b28eb0eadf3136eecea8ba214cca297c91b80d563a198449ca544c8956bb3bd","identity":"mutation:MUT_WIELD_OFFHAND","terminal_conclusion":"adjust"}
{"fact_sha256":"250c27a0924bc5f3aabe820e182040be60920a0a32c0bdf001525578d8672c3d","identity":"mutation:MUT_WILD_MAGIC","terminal_conclusion":"keep"}
{"fact_sha256":"2e44c9639d576479f15dcb02a4f76494cb22c8d6c6fb4fbd1f074e39d467ce93","identity":"mutation:MUT_WORD_OF_CHAOS","terminal_conclusion":"keep"}
{"fact_sha256":"8949e516aefc207f8df8cdf2088611fadaf472e0fb0ef848d90e1e1d4ae319a3","identity":"mutation:MUT_YELLOW_SCALES","terminal_conclusion":"keep"}
{"fact_sha256":"a85900a8cb09dab214c1c567525a2c158ea89f85b8b71e0fba2f6321ea805f6f","identity":"skill:SK_AIR_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"5b698bb25143f66b43fc3b69eb597e961aa80d8cc09141d368e4c2fa0bdec758","identity":"skill:SK_ALCHEMY","terminal_conclusion":"adjust"}
{"fact_sha256":"345ad11f647fa5cdc4e7819838ef4daa6ae60d10ab8df4689749562b117c0982","identity":"skill:SK_ARMOUR","terminal_conclusion":"adjust"}
{"fact_sha256":"9b5423ff41ac1c18e08707598e27a6adf1a63e00859ca0f584f1945ec580da49","identity":"skill:SK_AXES","terminal_conclusion":"adjust"}
{"fact_sha256":"853921845b5cf1e13c8bc233136c5cb3aa8447240c0196cdd2ed88ef77fe0e21","identity":"skill:SK_CHARMS","terminal_conclusion":"keep"}
{"fact_sha256":"128dbf362346bf253a716aa62318460a471a678b799be9dfdc16283293242bb2","identity":"skill:SK_CONJURATIONS","terminal_conclusion":"adjust"}
{"fact_sha256":"007740c1551ffb86664cb86a7220bdecf8de46493bf7bb7a8612b51a0bae59e0","identity":"skill:SK_CROSSBOWS","terminal_conclusion":"keep"}
{"fact_sha256":"6e67fd17cf737f81ed4135e8341cf5af5e93eed6229e842924584b5ee1ba931f","identity":"skill:SK_DODGING","terminal_conclusion":"adjust"}
{"fact_sha256":"b54b117f8f55a90dcebb84b4417761bab1ace5a6c5db8f4a5bc04f2f0c8e2cd7","identity":"skill:SK_EARTH_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"917473fbddcd787b0333bff8648c4ebfbb951fb1d9a5b4339f27c03db6c54a25","identity":"skill:SK_EVOCATIONS","terminal_conclusion":"adjust"}
{"fact_sha256":"fc8414aae2cc1827b124d4b9a5787412aae8721905277231124e8731fd0b7c1b","identity":"skill:SK_FIGHTING","terminal_conclusion":"adjust"}
{"fact_sha256":"ebae98f01548f5e2d58a4e3e7740cd178c87b4de340f92ad2de964e44a4be813","identity":"skill:SK_FIRE_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"189b424ad8dff236c7f4d56e24d658b0b9a7b8b524f26df329be9f123409fdf5","identity":"skill:SK_FORGECRAFT","terminal_conclusion":"keep"}
{"fact_sha256":"7a8070402e0d1a80e0147292c8c2496284f6fc15c5c1dd19f073b87fb4bc1b1f","identity":"skill:SK_HEXES","terminal_conclusion":"retranslate"}
{"fact_sha256":"12e9fde4aeab95c55ee6559f8be812f45d21f2c859f0126871b7de84583f9ac4","identity":"skill:SK_ICE_MAGIC","terminal_conclusion":"adjust"}
{"fact_sha256":"5b0c93e5252f3f26a500300d136b4757fccb5ffc1d0247fc9a7a0278e5e36e8e","identity":"skill:SK_INVOCATIONS","terminal_conclusion":"adjust"}
{"fact_sha256":"d95d33fe8ab4d108a2370ef61177e6fc48a425ab7c83d9758b8c39239d0fa1ff","identity":"skill:SK_LONG_BLADES","terminal_conclusion":"keep"}
{"fact_sha256":"38f7b636b87d0939e991641497f402a42d177c1302484b802d24f0b0c1664ac9","identity":"skill:SK_MACES_FLAILS","terminal_conclusion":"adjust"}
{"fact_sha256":"516ee17cd6159c60de774a20b36f77a4d6422bb0f259abdb090894df73cc5a03","identity":"skill:SK_NECROMANCY","terminal_conclusion":"adjust"}
{"fact_sha256":"6ff2a5d99103f67cd9f2e1b460827a5dfc5c69d554d991ad6b742f0a91cb4b0f","identity":"skill:SK_POLEARMS","terminal_conclusion":"adjust"}
{"fact_sha256":"707531ef19d3cb4abb34bf466723d9506cc5bc7e382539b155bf14950388358a","identity":"skill:SK_RANGED_WEAPONS","terminal_conclusion":"keep"}
{"fact_sha256":"e3453414f1d88c45e06a4b2c3081f668e7a1316107f619622120c84f60a0701d","identity":"skill:SK_SHAPESHIFTING","terminal_conclusion":"retranslate"}
{"fact_sha256":"c93f8c84b66573c4458f07648fad5e1223e008bd8aac3bb71dbe2c685ac83c1f","identity":"skill:SK_SHIELDS","terminal_conclusion":"adjust"}
{"fact_sha256":"00a6783ca4efbf9a3f99164e19510c46515c63d8c3e028813987ca9378247152","identity":"skill:SK_SHORT_BLADES","terminal_conclusion":"adjust"}
{"fact_sha256":"33c63c49208c5feca79a683ffaa22d9b06fb18bd92592405da0c943bc677f3a2","identity":"skill:SK_SLINGS","terminal_conclusion":"keep"}
{"fact_sha256":"443a000621007b4d6da30a0b71aaaf26d984d07356604a83273a5ea59860d410","identity":"skill:SK_SPELLCASTING","terminal_conclusion":"adjust"}
{"fact_sha256":"94f008645d29b0a3f5f89977ad6fceeeeb867835dfbedc89a10ed55e2e5f1b1b","identity":"skill:SK_STABBING","terminal_conclusion":"keep"}
{"fact_sha256":"42ef1caa67fb9075bedb2b01e29b9398f0c95821a050010bdec14341e9730d7e","identity":"skill:SK_STAVES","terminal_conclusion":"adjust"}
{"fact_sha256":"514c937e3480111c550da1c2f3683f7d4ba8b637c898d937679fc6cf1ef21ae6","identity":"skill:SK_STEALTH","terminal_conclusion":"adjust"}
{"fact_sha256":"4c82d2f138950cab02df1deb7be775c73d4305b9d13d6cffdc391fbabc43f976","identity":"skill:SK_SUMMONINGS","terminal_conclusion":"adjust"}
{"fact_sha256":"b7f66a51352e3e8f0ceffdd4f768462bf423175d796d1799664bb790edcfe17b","identity":"skill:SK_THROWING","terminal_conclusion":"adjust"}
{"fact_sha256":"b5870354c165ddaaaf64934c30c725a96bb5acb77b34a29aef1fa5bf3c3fbee8","identity":"skill:SK_TRANSLOCATIONS","terminal_conclusion":"retranslate"}
{"fact_sha256":"31e5c0b23043871c1e78d321035cfa5e98724d81b80a7c28757903c978c2ff4e","identity":"skill:SK_TRAPS","terminal_conclusion":"keep"}
{"fact_sha256":"eb90551d35fb5102b5d7286db797579cffd68122b08af5bdb62fa799f06f5ff6","identity":"skill:SK_UNARMED_COMBAT","terminal_conclusion":"keep"}
{"fact_sha256":"7efe488ce29c00d90f3254fb20da414ec54b361254cd906830929f414f44c99d","identity":"status:STATUS_AIRBORNE","terminal_conclusion":"keep"}
{"fact_sha256":"37b3b9eaf845f264512502b467cc0cf92d74ab33d04b23bec0042222da29cea4","identity":"status:STATUS_AUGMENTED","terminal_conclusion":"keep"}
{"fact_sha256":"71782144e93038243c18621536c94c67774b1394f5f8d1ae2100aa1862dba71a","identity":"status:STATUS_BACKLIT","terminal_conclusion":"keep"}
{"fact_sha256":"ec79bd1da78ce5228d47b0640dc4ccdde13efcfac74beb3f03e48da5277099ac","identity":"status:STATUS_BEHELD","terminal_conclusion":"keep"}
{"fact_sha256":"d9416d739cdd2cb8b86c45dfef0ede5c334ffa47b9ce17672b1dc5c9e016fd4c","identity":"status:STATUS_BEOGH","terminal_conclusion":"keep"}
{"fact_sha256":"4e8e2ec1ea03c85ae4e6c17b277c23dfec6236793d2d6a3111620d6c90e10e47","identity":"status:STATUS_BLACK_TORCH","terminal_conclusion":"keep"}
{"fact_sha256":"b2d00e3d687b265435cc3e164f467a1d74e255fd690f45a6a8b0ff11146932c7","identity":"status:STATUS_BRIBE","terminal_conclusion":"keep"}
{"fact_sha256":"f85bc00d7b40a7a0f3babf96420b2a26fd7ccfca422ea5ce875d7c946fd91100","identity":"status:STATUS_CANINE_FAMILIAR_ACTIVE","terminal_conclusion":"adjust"}
{"fact_sha256":"ed1a8d4636b4438597acbd18de9c80b693e80410d3574eba62ec7b9cce459870","identity":"status:STATUS_CHANNELLING_SPELL","terminal_conclusion":"keep"}
{"fact_sha256":"f1621fb418608a6d44675a065bbe40ef7a14a1f41ab3c416b525cf0de641af98","identity":"status:STATUS_CLAUSTROPHOBIA","terminal_conclusion":"keep"}
{"fact_sha256":"959bd84e74be7539bc5f991bb147eed7509074aff0eae046e9ac54a206a287fc","identity":"status:STATUS_CLOUD","terminal_conclusion":"keep"}
{"fact_sha256":"720e6e6b3f806410a7eb9a7ebb6eae61edfeb3b811d2d21b93f3a5117476995f","identity":"status:STATUS_CONSTRICTED","terminal_conclusion":"keep"}
{"fact_sha256":"5663efd7bfab02639b404be045e3751f6d2eda490a5695437e9f0fad661f151f","identity":"status:STATUS_CONTAMINATION","terminal_conclusion":"keep"}
{"fact_sha256":"65dbdde6b52ecb929be8f8890b5369be8e2834e6bfcaf67043389f3737030490","identity":"status:STATUS_CORROSION","terminal_conclusion":"keep"}
{"fact_sha256":"63f46588276cd8c3017e637099a4344dff7be9e667798a0b897277d79677d3f0","identity":"status:STATUS_CRUCIBLE_DEBT","terminal_conclusion":"keep"}
{"fact_sha256":"a6d1c7713ce74ef9288c6b7f798243e88a20e4e53d1e7ab806de6479cb9b1598","identity":"status:STATUS_DIG","terminal_conclusion":"keep"}
{"fact_sha256":"4b8ba4a2f277eed7fa545b4a58965152f006c3c3d78bdaa36533c1d2b7621f39","identity":"status:STATUS_DRACONIAN_BREATH","terminal_conclusion":"keep"}
{"fact_sha256":"55b41ddc073a2a08155c18482efd328c86f7da5ed9f5a1857d653aa97e4347d0","identity":"status:STATUS_DRAINED","terminal_conclusion":"keep"}
{"fact_sha256":"a74f203413ceddcaaf10f328065f4080d76de225b845bdff3917d3ab537f3f75","identity":"status:STATUS_DUEL","terminal_conclusion":"adjust"}
{"fact_sha256":"70ce5d7225d038b77cf0d3d280ca7512078d61339249c6e19ca4990e2a3e6d86","identity":"status:STATUS_GEM","terminal_conclusion":"keep"}
{"fact_sha256":"ccb66aa873fb4d04408587196f6e8d11cfb9e13c9d3017bba1f76938e357880a","identity":"status:STATUS_GRAVE_CLAW_UNAVAILABLE","terminal_conclusion":"keep"}
{"fact_sha256":"a9dd3c845d26e61f8bb3c6e48cc7c0ef56ca0f4d4e7ea718ee4d0d7261a09d89","identity":"status:STATUS_HEAVENLY_STORM","terminal_conclusion":"keep"}
{"fact_sha256":"700d8a321a449207efb2f07fdddbec5bda6d8b3b04033128aad9626830bc85a5","identity":"status:STATUS_INVISIBLE","terminal_conclusion":"keep"}
{"fact_sha256":"98cd1b0d7f478d08887ec21090c84ba58ad4bfe57e5784deaac85a030774d1a2","identity":"status:STATUS_IN_DEBT","terminal_conclusion":"keep"}
{"fact_sha256":"9358e242ae124919962e2f244fd9394dc25d98fcf61ae02467efe4d3c5224f4a","identity":"status:STATUS_LIQUEFIED","terminal_conclusion":"keep"}
{"fact_sha256":"25eeb1a0b95a2cd0b3176537beee26a910061f04ef5a1cfd95f98efb67765dd4","identity":"status:STATUS_LOWERED_WL","terminal_conclusion":"keep"}
{"fact_sha256":"43901a7f896b28bf3d61e73303e120b088e5efe0d07824a4bb3c7fe78f3499ee","identity":"status:STATUS_MANUAL","terminal_conclusion":"keep"}
{"fact_sha256":"d94afe773ca30365529e50fa52b99fb1e3c56c1d45ec02279bb50756ed5d2fd6","identity":"status:STATUS_MNEMOPHAGE","terminal_conclusion":"keep"}
{"fact_sha256":"9fe415f27e8f78318548eadfebef672ab753a12adfca5c501f74b206fd7a0090","identity":"status:STATUS_NET","terminal_conclusion":"keep"}
{"fact_sha256":"52f85c40a1e11a9395abdf13d2c9cb2088264446303075219a9bc730b3ef30a0","identity":"status:STATUS_NO_POTIONS","terminal_conclusion":"keep"}
{"fact_sha256":"2023a6b256666d046e9bac6331330ba69fc7e91f4181e9b4371789cf9c6df41d","identity":"status:STATUS_NO_SCROLL","terminal_conclusion":"adjust"}
{"fact_sha256":"3f3f5a5e4035836a13b9a08fea1c544544a937a31b9b492796729cba29d6c0f0","identity":"status:STATUS_ORB","terminal_conclusion":"keep"}
{"fact_sha256":"98f0ea5ab23b441e95426c9d49e1c49d455c4c41247f312bcd33e38663301e10","identity":"status:STATUS_OSTRACISM","terminal_conclusion":"keep"}
{"fact_sha256":"b6a7a15f3dac8176ce32bf4d7d7e9dc0991eb4c6a80bb8363f2e733283800b29","identity":"status:STATUS_PEEKING","terminal_conclusion":"keep"}
{"fact_sha256":"bf0e6de02e49a9cf862d26dc34b10751cae9997b8f5528779da699642385ba32","identity":"status:STATUS_REGENERATION","terminal_conclusion":"keep"}
{"fact_sha256":"17b7d92301915b6078befac159cef3fe05295344543730fe02428beaaf60799c","identity":"status:STATUS_REV","terminal_conclusion":"keep"}
{"fact_sha256":"a39b329a16046afffaa9dab41f00e5a05d5955d4806e131696f3012db9ffae7e","identity":"status:STATUS_RF_ZERO","terminal_conclusion":"adjust"}
{"fact_sha256":"803d22f71a1e71d52726cbc8a8195f813949e79477879796ba8dc32964f0c5c9","identity":"status:STATUS_SERPENTS_LASH","terminal_conclusion":"adjust"}
{"fact_sha256":"1fce445b368e93c5d77e6de1a1ec870696bca7399b37e39da4c66fd8c43f1a8f","identity":"status:STATUS_SHROUD","terminal_conclusion":"keep"}
{"fact_sha256":"1a720e3e664d90cdbdac75de0fa73d1cdb5cd758e6c8acfd4e51c5a00a8d7f5a","identity":"status:STATUS_SILENCE","terminal_conclusion":"adjust"}
{"fact_sha256":"2bf6d2a15d40cbf947cff5b28eb0ca872e2e67dd0b9b9af6e949af0a3ad8affc","identity":"status:STATUS_SPEED","terminal_conclusion":"keep"}
{"fact_sha256":"bc6c994fb7408046118e98d81d07a62e40ad0d5826ad99aecedade6c3cbaa150","identity":"status:STATUS_STAT_ZERO","terminal_conclusion":"keep"}
{"fact_sha256":"14a15c6466207dd89bce64c7b4da37fc162313159c1975ad250b09a284640d61","identity":"status:STATUS_STILL_WINDS","terminal_conclusion":"keep"}
{"fact_sha256":"2df14c65a76a05fce8d65fecd297f99c56d3f5c6ae2b02557fed3c1a39a16799","identity":"status:STATUS_SUNDER_READY","terminal_conclusion":"keep"}
{"fact_sha256":"92b64698d08706973e2071218ea056e9285ad6cd06b6f41189dac629060319a1","identity":"status:STATUS_TERRAIN","terminal_conclusion":"keep"}
{"fact_sha256":"ea9ca86c833d7ae25d4bfab0ba29232c8b5989b8fd60887b29f13cef0b65c678","identity":"status:STATUS_TESSERACT","terminal_conclusion":"keep"}
{"fact_sha256":"980c62ea480b6f1614b1a6cf465e56db531367a484199666c1ae83ee86120bbd","identity":"status:STATUS_TRICKSTER","terminal_conclusion":"keep"}
{"fact_sha256":"cb112662e5e63d3062a0005ef2954cf0e285cb47f29d399c4407671226939a37","identity":"status:STATUS_UMBRA","terminal_conclusion":"keep"}
{"fact_sha256":"b81654444c324a17ed2fd06f86951036805e46ef2e423d8f70ff5c1750c92a7f","identity":"status:STATUS_ZOT","terminal_conclusion":"keep"}
```
<!-- END STRICT REVIEW EVIDENCE v1 -->
