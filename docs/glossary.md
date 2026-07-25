# DCSS 中文翻译术语表

> 统一人工维护 SSOT——翻译 Agent 在翻译前必须查阅此文件。
> 物品显示名称区域另可导出为 OmegaT UTF-8 TSV：第一列源语、第二列译语、第三列作用域/备注。
> 来源合并：`docs/decisions.md` + [legacy issue 12 glossary][legacy-12-glossary] + `zh-translator.md` prompt
> 维护规则：术语变更必须同步更新此文件和相关 decisions.md 裁决。

---

<!-- domain:gods -->
## 一、神祇名（God Names）

| EN | ZH | 类型 | 裁决 |
|----|----|------|------|
| Zin | 辛 | 单字音译 | — |
| Yredelemnul | 伊莱德莱姆努尔 | 音译 | — |
| Okawaru | 奥卡瓦鲁 | 音译 | — |
| Makhleb | 马科列布 | 音译 | — |
| Sif Muna | 西芙·穆娜 | 音译·U+00B7 | [D-A-001] |
| Trog | 特洛格 | 音译 | [D-A-002] |
| Elyvilon | 艾利维隆 | 音译 | — |
| Lugonu | 卢格努 | 音译 | — |
| Beogh | 比欧弗 | 音译 | — |
| Fedhas | 费德哈 | 音译 | — |
| Cheibriados | 切布理亚多 | 音译 | — |
| Ashenzari | 艾申扎利 | 音译 | — |
| Dithmenos | 迪斯姆诺 | 音译 | — |
| Nemelex Xobeh | 尼姆雷斯·索布 | 音译·U+00B7 | [D-A-004] |
| Gozag | 哥萨戈·亿·赛格斯 | 音译 | — |
| Qazlal | 卡兹拉尔 | 音译 | — |
| Ru | 入 | 意译（"enter"） | — |
| Pakellas | 帕克拉斯 | 音译 | — |
| Uskayaw | 乌斯卡亚 | 音译 | — |
| Hepliaklqana | 惠普利亚卡纳 | 音译 | — |
| Ignis | 曳焰 | 意译 | — |
| Wu Jian | 无间门派 | 意译（门派=sect） | — |
| Xom | 佐姆 | 音译 | — |
| Zot | 佐特 | 音译 | — |
| Jiyva | 吉瓦 | 音译 | — |
| Kikubaaqudgha | 奇库巴库哈 | 音译 | [D-A-003] |
| Vehumet | 维胡梅特 | 音译 | [D-A-005] |
| The Shining One | 光辉者 | 意译 | [D-A-006] |

**废弃译名（永远不要使用）**：席夫·穆纳 → 西芙·穆娜 / 特洛戈 → 特洛格 / 奇库巴库加 → 奇库巴库哈

**中圆点规范**：始终使用 U+00B7（·），不使用 U+30FB（・）

---

<!-- domain:god-titles -->
## 二、神祇称号模式

| 模式 | 示例 |
|------|------|
| -者 后缀 | 堕落者（Lugonu）、被缚者（Ashenzari）、发明者（Pakellas） |
| -之主 后缀 | 战争之主（Okawaru）、学识之主（Sif Muna）、混沌之主（Xom） |
| -之神 后缀 | 复仇之神 |
| 自由形式 | 曳焰（Ignis）、无间门派（Wu Jian） |

---

<!-- domain:magic -->
## 三、魔法学派

| EN | ZH |
|----|----|
| Conjuration / Conjurations | 咒法系 |
| Hexes | 诅咒系 |
| Summoning / Summonings | 召唤系 |
| Necromancy | 死灵术 |
| Translocation | 传送系 |
| Forgecraft | 锻造术 |
| Fire Magic | 火焰魔法 |
| Ice Magic | 寒冰魔法 |
| Air Magic | 空气魔法 |
| Earth Magic | 大地魔法 |
| Poison Magic | 毒素魔法 |
| Alchemy | 炼金术 |
| Shapeshifting | 变形术 |

### 法术命名高频词根

系列词根经批次审阅后在此登记。当前已确认的稳定译法：

| 词根 | 译法 | 状态 |
|------|------|------|
| Blink | 闪烁 | ✅ 已确认（现行 8 项；另有 1 项已移除／TAG 34 兼容记录） |
| Bolt | 箭 | ✅ 已确认（常规现行法术；Blinkbolt 保留“闪烁箭”，Thunderbolt 采用“雷击”例外） |
| Cloud | 云 | ✅ 已确认（现行 `X Cloud` 后缀系列 8 项；另有 4 项已移除兼容记录） |
| Summon | 召唤 | ✅ 已确认 |
| Breath | 吐息 | ✅ 已确认（20 项现行；另有 2 项已移除／TAG 34 兼容记录） |
| Dart | 飞镖 | ✅ 已确认（`Magic Dart → 魔法飞弹` 为固定词形例外） |
| Shadow | 暗影 | ✅ 已确认（12 项现行；另有 1 项已移除／TAG 34 兼容记录） |
| Throw | 投掷 | ✅ 已确认（7 项现行；另有 1 项已移除／TAG 34 兼容记录） |
| Beam | 光束 | ✅ 已确认（2 项现行；`Shadow Beam` 已在 Shadow 批次审阅） |
| Gaze | 凝视 | ✅ 已确认（7 项现行） |
| Arrow | 箭 | ✅ 已确认（4 项现行；`Mercury Arrow → 汞矢` 为消除重名的辨识性例外） |
| Flame / Flames | 火焰 / 焰 | ✅ 已确认（7 项现行；另有 3 项已移除兼容；复合标题允许“焰／烈焰”） |
| Touch | 触 | ✅ 已确认（2 项现行） |
| Form | 变形 | ⚠️ 已审阅（6 项均为已移除／TAG 34 兼容记录；机制证据不足，暂沿用） |
| Poison / Poisonous | 毒素 / 毒 / 淬毒 | ✅ 已确认（5 项现行；另有 4 项已移除兼容；`Spit Poison → 喷吐毒液`） |
| Dispel | 驱散 | ✅ 已确认（2 项现行；指破坏维系亡灵形体的魔力） |
| Awaken | 唤醒 | ✅ 已确认（4 项现行；另有 1 项已移除兼容） |
| Forge | 锻造 | ✅ 已确认（4 项现行） |

其他词根将在逐批审阅中确认并补充。
强度审查标签定义见 `docs/spell-naming-rules.md` Section 四。

---

<!-- domain:core -->
## 四、核心游戏术语

| EN | ZH | 注意事项 |
|----|----|---------|
| spell | 法术 | 泛指 |
| spellpower | 法术威力 | **绝不**译为"法力"——法力 = MP |
| Bane / bane | 灾祸 | 负面游戏机制；专名 `Bane of X` 可按语境译为“X之灾” |
| MP / magic points | 法力 | 施法资源 |
| cast | 施法（通用）/ 吟诵（仪式）/ 咏唱（神圣） | 按语境选择 |
| miscast | 施法失误 | 非"施法失败"（后者指被中断） |
| monster | 怪物 | 通用 |
| demon | 恶魔 | — |
| undead | 亡灵 | — |
| dragon | 龙 | — |
| god | 神祇 / 神 | 正式语境用"神祇"，口语可用"神" |
| penance | 惩戒（律法神）/ 苦修（自我牺牲神） | 按神祇类型选择 |
| flee | 逃跑 | — |
| shout | 喊叫 | 非"吼叫"（那是 roar） |
| curse | 诅咒 | — |
| soul | 灵魂 | — |
| blood | 鲜血 / 血 | 强调用"鲜血"，普通用"血" |
| Abyss | 深渊 | — |
| Dungeon | 地牢 | — |
| Orb of Zot | 佐特宝珠 / 力量宝珠 | 两种译法均可 |
| player ghost | 玩家鬼魂 | — |
| skill | 技能 | — |
| experience / XP | 经验值 | — |
| level | 等级 / 层 | 角色用"等级"，楼层用"层" |
| Evocations | 激活技能 | **绝不**译为"召唤术"——那是 Summoning |

### 常用状态与效果

| EN | ZH | 注意事项 |
|----|----|---------|
| Might | 强效 | +10% 伤害 |
| Haste | 加速 | 行动速度 +50% |
| Berserk | 狂暴 | 近战加成但结束后减速 |
| Rampage | 冲锋 | 攻击时自动向敌人移动一步 |
| Teleport | 传送 | 位移效果 |
| Invisibility | 隐形 | 不可被看见 |
| Silence | 沉默 | 禁止施法/阅读卷轴 |

---

<!-- domain:combat -->
## 五、战斗与伤害

| EN | ZH |
|----|----|
| damage | 伤害 |
| attack | 攻击 |
| hit | 击中 |
| miss | 未命中 |
| block | 格挡 |
| dodge | 闪避 |
| armour / armor | 护甲 |
| shield | 盾牌 |
| critical hit | 暴击 |
| resist | 抵抗 |
| Drain | 汲取 | 生命/魔力吸取效果 |
| Torment | 折磨 | 按比例造成伤害 |
| vulnerable | 脆弱 |
| immune | 免疫 |

---

<!-- domain:items -->
## 六、物品与装备

| EN | ZH |
|----|----|
| weapon | 武器 |
| armour | 护甲 |
| ring | 戒指 |
| amulet | 项链 |
| scroll | 卷轴 |
| potion | 药水 |
| wand | 魔杖 |
| artefact | 神器 |
| brand | 铭印 |
| ego |  ego 装备 / 附魔装备 |
| wield | 持握 |
| wear | 穿戴 |
| remove | 卸下 |
| identify | 鉴定 |
| enchant | 附魔 |
| curse | 诅咒 |

### 基础物品显示名称（脚本 SSOT）

<!-- item-name-terms -->
| EN | ZH | Scope / comment |
|----|----|----------------|
| arbalest | 重弩 | weapon; decision=D-B-017 |
| Barding | 马铠 | armour; decision=D-B-019 |
| broad axe | 阔刃斧 | weapon; decision=D-B-018 |
| dragon-coil talisman | 盘龙护符 | talisman; decision=D-B-018 |
| dire flail | 双头链枷 | weapon; decision=D-B-017 |
| falchion | 弯刃剑 | weapon; decision=D-B-018 |
| great mace | 巨型钉头锤 | weapon; decision=D-B-017 |
| morningstar | 晨星锤 | weapon; paired with eveningstar; decision=D-B-017 |
| eveningstar | 暮星锤 | weapon; paired with morningstar; decision=D-B-017 |
| old falchion | 旧弯刃剑 | legacy weapon key; decision=D-B-018 |
| partisan | 阔头枪 | weapon; decision=D-B-018 |
| quarterstaff | 长棍 | weapon; decision=D-B-017 |
| sanguine talisman | 血色护符 | talisman; decision=D-B-018 |
| shadows | 暗影 | armour ego; decision=D-B-018 |
| triple crossbow | 三弦弩 | weapon; decision=D-B-018 |
| executioner's axe | 刽子手斧 | weapon; decision=D-B-017 |

---

<!-- domain:dialogue -->
## 七、对话动词（按语境选择）

| EN | ZH | 适用角色 |
|----|----|---------|
| says | 说 / 说道 | 通用 |
| whispers | 低语 / 轻声说 | 幽灵、潜行角色 |
| shouts / yells | 喊道 / 大喊 | 战士、兽人 |
| growls / snarls | 咆哮道 | 野兽、狼人 |
| mutters / mumbles | 咕哝道 / 嘟囔道 | 疯狂角色（Crazy Yiuf） |
| laughs / chuckles | 笑道 / 咯咯笑着 | Xom、小恶魔 |
| taunts | 嘲讽道 | 高等恶魔、反派 |
| begs / pleads | 乞求道 / 恳求道 | 濒死角色 |
| roars | 咆哮道 / 吼道 | 龙、大型怪物 |

---

<!-- domain:shouts -->
## 八、怪物喊叫类型（__SHOUT 等）

| EN | ZH |
|--------|----|
| `__SHOUT` | 喊叫 |
| `__BARK` | 吠叫 |
| `__HOWL` | 嚎叫 |
| `__ROAR` | 咆哮 |
| `__SCREAM` | 尖叫 |
| `__BELLOW` | 吼叫 |
| `__MOAN` | 呻吟 |
| `__HISS` | 嘶嘶声 |
| `__BUZZ` | 嗡嗡声 |
| `__CROAK` | 呱呱叫 |
| `__SKITTER` | 窸窣声 |

---

<!-- domain:rules -->
## 九、翻译规则速查

### 语法（不可违反）
1. 无冠词（a/an/the）
2. 无复数标记
3. 副词在动词前：`快速地跑` 不是 `跑快速地`
4. 了 用于完成态：`has fled` → `逃跑了`
5. 修饰语在前：`X of Y` → `Y之X`（名词-名词）/ `Y的X`（形容词-名词）

### 法术命名规则
- 法术名翻译遵循 `docs/spell-naming-rules.md`
- 系列词根审阅完毕后在本文件 Section 三登记

### 格式保留（不可违反）
- `@keyword@` 标识符——原样保留
- `w:N` 权重标记——原样保留
- `VISUAL:` / `SOUND:` 前缀——原样保留
- `%%%%` 分隔符——原样保留
- `{{ }}` Lua 代码块——原样保留（仅翻译内部字符串字面量）
- `[variant|choice]` 选择语法——保留括号，翻译选项

### 不可翻译
- Lua 比较字符串：`"Mummy"`、`"Zin"`、`"Trog"` 等
- JSON 键、.des 文件标签
- 函数名、变量名、文件路径
- DB 查找键

---

<!-- domain:characters -->
## 十、角色声音速查

| 角色 | 自称 | 称呼玩家 | 句式长度 | 特征词 |
|------|------|---------|---------|--------|
| 地精/兽人 | 老子/俺 | 你/小子 | <10 字 | 哼！杀！砸！ |
| 龙 | 吾/本座 | 汝/蝼蚁/凡人 | 10-25 字 | 半文言 |
| 小恶魔 | 老子/俺 | 你 | <12 字 | 嬉皮笑脸 |
| 高等恶魔 | 本尊/吾 | 汝 | 10-25 字 | 冷傲、嗜魂 |
| 幽灵 | — | — | 3-6 字 | 冷……好冷…… |
| 巫妖 | 吾/本巫 | 凡人/生者 | 10-20 字 | 冷智 |
| Xom | — | — | 3-15 字 | 嘻嘻！跳跃无因果 |
| Trog | — | — | <8 字 | 命令式、第三人称自指 |
| Sif Muna | 吾/求知者 | — | 10-30 字 | 学术长句 |
| Vehumet | — | — | 8-20 字 | 半文言毁灭意象 |
| Cheibriados | — | — | 10-25 字 | 逗号停顿、时间意象 |
| Beogh | — | — | 混合 | 兽人救世主狂热 |

---

<!-- domain:culture -->
## 十一、文化适配

| 场景 | 策略 |
|------|------|
| 英文侮辱语 | 找中文武侠/仙侠等价侮辱，不直译 |
| 孙子兵法引用 | 使用真实古文原文 |
| 莎士比亚/文学引用 | 使用已知中文译本 |
| 奇幻套话 | 适配武侠/仙侠惯例 |
| 谚语 | 找中文等价谚语，不直译 |

---

<!-- domain:species -->
## 十二、种族/物种名称

| EN | ZH | 裁决 | 复合格式 |
|----|----|------|---------|
| deep elf | 精灵 | [D-A-008] | 精灵 + 职业（精灵剑圣、精灵湮灭者） |
| spriggan | 小精灵 | [D-A-011] | 小精灵 + 职业（小精灵气法师、小精灵狂战士） |
| naga / nagaraja | 纳迦 / 纳迦王 | [D-A-012] | 纳迦 + 职业（纳迦法师、纳迦神射手） |
| draconian | 龙人 | [D-A-007] | 颜色 + 龙人（黑龙人、绿龙人） |
| orc | 兽人 | — | 兽人 + 职业（兽人骑士、兽人大祭司） |
| tengu | 天狗 | — | 天狗 + 职业（天狗咒术师） |
| merfolk | 人鱼 | — | 人鱼 + 职业（人鱼水法师） |
| centaur | 半人马 | — | 半人马 + 职业 |
| yaktaur | 牦牛人马 | — | 牦牛人马 + 职业 |
| goblin | 地精 | — | 地精 + 职业 |
| kobold | 狗头人 | — | 狗头人 + 职业 |
| troll | 巨魔 | — | 巨魔 + 职业 |
| ogre | 食人魔 | — | 食人魔 + 职业 |
| gnoll | 豺狼人 | — | 豺狼人 + 职业 |
| vampire | 吸血鬼 | — | 吸血鬼 + 职业（吸血鬼骑士、吸血鬼法师） |
| mummy | 木乃伊 | — | 木乃伊 + 职业 |
| ghoul | 食尸鬼 | — | 食尸鬼 + 职业 |
| demonspawn | 恶魔裔 | — | 恶魔裔 + 职业 |
| minotaur | 牛头人 | — | — |
| felid | 猫 | [D-A-039] | — |
| octopode | 章鱼 | [D-A-040] | — |
| gargoyle | 石像鬼 | — | — |
| formicid | 蚁人 | — | — |
| barachi | 蛙人 | — | — |
| vine stalker | 藤蔓行者 | — | — |
| armataur | 甲马人 | — | — |
| faun | 牧神 | — | — |

**复合命名规则**：`[种族基词] + [职业/角色名]`，不使用斜杠、破折号或空格分隔。

---

<!-- domain:skills -->
## 十三、技能名

| EN | ZH | Scope / comment |
|----|----|----------------|
| Fighting | 格斗 | skill; source=source.txt; decision=D-C-001 |
| Short Blades | 短刃 | skill; source=source.txt; decision=D-C-001 |
| Long Blades | 长刃 | skill; source=source.txt; decision=D-C-001 |
| Axes | 斧类 | skill; source=source.txt; decision=D-C-001 |
| Maces & Flails | 锤与链枷 | skill; source=source.txt; decision=D-C-001 |
| Polearms | 长柄武器 | skill; source=source.txt; decision=D-C-001 |
| Staves | 杖类 | skill; source=source.txt; decision=D-C-001 |
| Ranged Weapons | 远程武器 | skill; source=source.txt; decision=D-C-001 |
| Throwing | 投掷 | skill; source=source.txt; decision=D-C-001 |
| Armour | 护甲 | skill; source=source.txt; decision=D-C-001 |
| Dodging | 闪避 | skill; source=source.txt; decision=D-C-001 |
| Shields | 盾牌 | skill; source=source.txt; decision=D-C-001 |
| Unarmed Combat | 徒手格斗 | skill; source=source.txt; decision=D-C-001 |
| Spellcasting | 施法能力 | skill; source=source.txt; decision=D-C-001 |
| Summonings | 召唤系 | skill; source=source.txt; decision=D-C-001 |
| Translocations | 传送系 | skill; source=source.txt; decision=D-C-001 |
| Forgecraft | 锻造术 | skill; source=source.txt; decision=D-C-001 |
| Fire Magic | 火焰魔法 | skill; source=source.txt; decision=D-C-001 |
| Ice Magic | 寒冰魔法 | skill; source=source.txt; decision=D-C-001 |
| Air Magic | 空气魔法 | skill; source=source.txt; decision=D-C-001 |
| Earth Magic | 大地魔法 | skill; source=source.txt; decision=D-C-001 |
| Invocations | 祈神 | skill; source=source.txt; decision=D-C-001 |
| Evocations | 魔力释放 | skill; source=source.txt; decision=D-C-001 |
| Shapeshifting | 变形术 | skill; source=source.txt; decision=D-C-001 |

<!-- domain:status -->
## 十四、状态与效果

| EN | ZH | Scope / comment |
|----|----|----------------|
| Haste | 加速 | status; source=status.txt |
| Invisibility | 隐形 | status; source=status.txt |
| Might | 强效 | status; source=status.txt |
| Berserk | 狂暴 | status; source=status.txt |
| Poison | 中毒 | status; source=status.txt |
| Confusion | 混乱 | status; source=status.txt |
| Contamination | 诱变辐射 | status; source=status.txt |
| Drain | 衰竭 | status; source=status.txt |
| Slow | 减速 | status; source=status.txt |
| Paralysis | 麻痹 | status; source=status.txt |
| Sleep | 睡眠 | status; source=status.txt |
| Held | 受困 | status; source=status.txt |
| Constriction | 束缚 | status; source=status.txt |
| Fear | 恐惧 | status; source=status.txt |
| Fire | 着火 | status; source=status.txt |
| Sick | 患病 | status; source=status.txt |
| Corrosion | 腐蚀 | status; source=status.txt |
| Frozen | 冰封 | status; source=status.txt |
| Petrification | 石化 | status; source=status.txt |
| Resistance | 抗性 | status; source=status.txt |

<!-- domain:backgrounds -->
## 十五、角色背景

| EN | ZH | Scope / comment |
|----|----|----------------|
| Air Elementalist | 气元素使 | background; source=backgrounds.txt |
| Artificer | 技师 | background; source=backgrounds.txt |
| Berserker | 狂战士 | background; source=backgrounds.txt |
| Brigand | 强盗 | background; source=backgrounds.txt |
| Chaos Knight | 混沌骑士 | background; source=backgrounds.txt |
| Conjurer | 塑能师 | background; source=backgrounds.txt |
| Delver | 挖掘者 | background; source=backgrounds.txt |
| Earth Elementalist | 土元素使 | background; source=backgrounds.txt |
| Enchanter | 惑控师 | background; source=backgrounds.txt |
| Fighter | 战士 | background; source=backgrounds.txt |
| Fire Elementalist | 火元素使 | background; source=backgrounds.txt |
| Gladiator | 角斗士 | background; source=backgrounds.txt |
| Hedge Wizard | 杂学巫师 | background; source=backgrounds.txt |
| Hunter | 猎手 | background; source=backgrounds.txt |
| Monk | 武僧 | background; source=backgrounds.txt |
| Necromancer | 死灵法师 | background; source=backgrounds.txt |
| Reaver | 掠夺者 | background; source=backgrounds.txt |
| Summoner | 召唤师 | background; source=backgrounds.txt |
| Shapeshifter | 变形人 | background; source=backgrounds.txt |
| Alchemist | 炼金术士 | background; source=backgrounds.txt |
| Wanderer | 漫游者 | background; source=backgrounds.txt |
| Warper | 折跃者 | background; source=backgrounds.txt |
| Forgewright | 锻造师 | background; source=backgrounds.txt |

<!-- domain:abilities -->
## 十六、能力名

| EN | ZH | Scope / comment |
|----|----|----------------|
| Spit Poison | 喷吐毒液 | ability; source=ability.txt |
| Breathe Fire | 吐息火焰 | ability; source=ability.txt |
| Breathe Frost | 吐息寒霜 | ability; source=ability.txt |
| Breathe Poison Gas | 吐息毒气 | ability; source=ability.txt |
| Breathe Lightning | 吐息闪电 | ability; source=ability.txt |
| Breathe Acid | 吐息酸液 | ability; source=ability.txt |
| Breathe Steam | 吐息蒸汽 | ability; source=ability.txt |
| Hurl Damnation | 投掷天谴 | ability; source=ability.txt |
| Word of Chaos | 混沌之语 | ability; source=ability.txt |
| Heal Wounds | 治疗创伤 | ability; source=ability.txt |
| Dig | 挖掘 | ability; source=ability.txt |
| Recite | 吟诵 | ability; source=ability.txt |
| Vitalisation | 活力再生 | ability; source=ability.txt |
| Imprison | 监禁 | ability; source=ability.txt |
| Sanctuary | 庇护所 | ability; source=ability.txt |

<!-- domain:mutations -->
## 十七、变异名

| EN | ZH | Scope / comment |
|----|----|----------------|
| tough skin | 硬化表皮 | mutation; source=mutations.txt |
| shaggy fur | 浓密皮毛 | mutation; source=mutations.txt |
| repulsion field | 排斥力场 | mutation; source=mutations.txt |
| icy blue scales | 冰蓝鳞片 | mutation; source=mutations.txt |
| molten scales | 熔融鳞片 | mutation; source=mutations.txt |
| slimy green scales | 黏滑绿鳞 | mutation; source=mutations.txt |
| yellow scales | 黄色鳞片 | mutation; source=mutations.txt |
| thin metallic scales | 薄金属鳞片 | mutation; source=mutations.txt |
| rugged brown scales | 粗糙褐鳞 | mutation; source=mutations.txt |
| sharp scales | 锐利鳞片 | mutation; source=mutations.txt |
| large bone plates | 大型骨板 | mutation; source=mutations.txt |
| thin skeletal structure | 纤细骨骼 | mutation; source=mutations.txt |
| strong | 强壮 | mutation; source=mutations.txt |
| clever | 聪慧 | mutation; source=mutations.txt |
| agile | 敏捷 | mutation; source=mutations.txt |
| weak | 虚弱 | mutation; source=mutations.txt |
| dopey | 愚钝 | mutation; source=mutations.txt |
| clumsy | 笨拙 | mutation; source=mutations.txt |
| high mp | 高魔力 | mutation; source=mutations.txt |
| low mp | 低魔力 | mutation; source=mutations.txt |
| camouflage | 伪装 | mutation; source=mutations.txt |
| horns | 角 | mutation; source=mutations.txt |
| beak | 鸟喙 | mutation; source=mutations.txt |
| fangs | 尖牙 | mutation; source=mutations.txt |
| acidic bite | 酸性撕咬 | mutation; source=mutations.txt |
| claws | 利爪 | mutation; source=mutations.txt |
| hooves | 蹄 | mutation; source=mutations.txt |
| antennae | 触角 | mutation; source=mutations.txt |
| stinger | 毒刺 | mutation; source=mutations.txt |

<!-- domain:monsters -->
## 十八、怪物名称（首批）

> 名称来源：`dat/i18n/zh/source.txt`；只登记显示名称，不登记描述文本中的代码键。

| EN | ZH | Scope / comment |
|----|----|----------------|
| acid blob | 酸液团 | monster; source=source.txt |
| acid dragon | 酸龙 | monster; source=source.txt |
| adder | 蝰蛇 | monster; source=source.txt |
| air elemental | 气元素 | monster; source=source.txt |
| alligator | 短吻鳄 | monster; source=source.txt |
| alligator snapping turtle | 巨鳄龟 | monster; source=source.txt; distinguished from snapping turtle → 鳄龟 |
| anaconda | 水蟒 | monster; source=source.txt |
| ancestor | 先祖 | monster; source=source.txt |
| ancient champion | 远古冠军 | monster; source=source.txt |
| ancient lich | 远古巫妖 | monster; source=source.txt |
| ancient zyme | 古酶 | monster; source=source.txt |
| angel | 天使 | monster; source=source.txt |
| armataur | 甲马人 | monster; source=source.txt |
| armour echo | 铠甲回响 | monster; source=source.txt |
| apis | 阿匹斯 | monster; source=source.txt |
| apocalypse crab | 天启螃蟹 | monster; source=source.txt |
| arcanist | 奥术师 | monster; source=source.txt |
| aspiring flesh | 渴望之肉 | monster; source=source.txt |
| azure jelly | 天蓝果冻怪 | monster; source=source.txt |
| ball lightning | 球形闪电 | monster; source=source.txt |
| ball python | 球蟒 | monster; source=source.txt |
| ballistomycete | 孢子炮菌 | monster; source=source.txt |
| ballistomycete spore | 孢子炮菌孢子 | monster; source=source.txt |
| balrug | 巴鲁格 | monster; source=source.txt |
| barachi | 蛙人 | monster; source=source.txt |
| basilisk | 石化蜥蜴 | monster; source=source.txt |
| bat | 蝙蝠 | monster; source=source.txt |
| battlesphere | 战斗法球 | monster; source=source.txt |
| bennu | 贝努鸟 | monster; source=source.txt |
| black bear | 黑熊 | monster; source=source.txt |
| black draconian | 黑龙人 | monster; source=source.txt |
| black mamba | 黑曼巴蛇 | monster; source=source.txt |
| blazeheart core | 焰心核心 | monster; source=source.txt |
| blazeheart golem | 焰心魔像 | monster; source=source.txt |
| blink frog | 闪烁蛙 | monster; source=source.txt |
| blizzard demon | 暴雪恶魔 | monster; source=source.txt |
| bloated husk | 肿胀尸壳 | monster; source=source.txt |
| block of ice | 冰块 | monster; source=source.txt |
| bog body | 沼泽之躯 | monster; source=source.txt |
| boggart | 博加特 | monster; source=source.txt |
| bombardier beetle | 投弹甲虫 | monster; source=source.txt |
| bone dragon | 骨龙 | monster; source=source.txt |
| gnoll bouda | 豺狼人布达 | monster; source=source.txt |
| boulder | 巨石 | monster; source=source.txt |
| boulder beetle | 巨砾甲虫 | monster; source=source.txt |
| bound soul | 缚魂 | monster; source=source.txt |
| brain worm | 脑虫 | monster; source=source.txt |
| briar patch | 荆棘丛 | monster; source=source.txt |
| Brimstone Fiend | 硫磺邪魔 | monster; source=source.txt |
| broodmother | 育母蜘蛛 | monster; source=source.txt |
| burial acolyte | 殡葬侍僧 | monster; source=source.txt |
| bush | 灌木 | monster; source=source.txt |
| bullfrog | 牛蛙 | monster; source=source.txt |
| bunyip | 本耶普 | monster; source=source.txt |
| butterfly | 蝴蝶 | monster; source=source.txt |
| cactus giant | 仙人掌巨人 | monster; source=source.txt |
| cacodemon | 恶灵恶魔 | monster; source=source.txt |
| cane toad | 海蟾蜍 | monster; source=source.txt |
| catoblepas | 卡托布勒帕斯 | monster; source=source.txt |
| caustic shrike | 腐蚀伯劳 | monster; source=source.txt |
| centaur | 半人马 | monster; source=source.txt |
| centaur warrior | 半人马战士 | monster; source=source.txt |
| cerulean imp | 蔚蓝小恶魔 | monster; source=source.txt |
| chaos spawn | 混沌之子 | monster; source=source.txt |
| cherub | 智天使 | monster; source=source.txt |
| creeping inferno | 蔓延地狱火 | monster; source=source.txt |
| crimson imp | 深红小恶魔 | monster; source=source.txt |
| crocodile | 鳄鱼 | monster; source=source.txt |
| crystal echidna | 水晶针鼹 | monster; source=source.txt |
| crystal guardian | 水晶守护者 | monster; source=source.txt |
| culicivora | 库蚊蛛 | monster; source=source.txt |
| curse skull | 诅咒颅骨 | monster; source=source.txt |
| curse toe | 诅咒趾 | monster; source=source.txt |
| cyclops | 独眼巨人 | monster; source=source.txt |
| daeva | 德瓦 | monster; source=source.txt |
| Jiangshi | 僵尸 | monster; source=source.txt; Chinese hopping-vampire name, distinguished from zombie → 丧尸 |
| orc sorcerer | 兽人术士 | monster; source=source.txt; distinguished from orc wizard → 兽人巫师 |
| orc wizard | 兽人巫师 | monster; source=source.txt |
| snapping turtle | 鳄龟 | monster; source=source.txt; distinguished from alligator snapping turtle → 巨鳄龟 |
| Spatial Maelstrom | 空间乱流 | monster; source=source.txt; distinguished from spatial vortex → 空间漩涡 |
| spatial vortex | 空间漩涡 | monster; source=source.txt |
| zombie | 丧尸 | monster; source=source.txt; distinguished from Jiangshi → 僵尸; established work titles may retain “僵尸” |

| Serpent of Hell | 地狱巨蛇 | monster; source=source.txt; shared display name |
| Serpent of Hell gehenna | 欣嫩谷地狱巨蛇 | unique-monster; source=monsters.txt; branch-qualified display name |
| Serpent of Hell cocytus | 悲叹河地狱巨蛇 | unique-monster; source=monsters.txt; branch-qualified display name |
| Serpent of Hell dis | 铁城地狱巨蛇 | unique-monster; source=monsters.txt; branch-qualified display name |
| Serpent of Hell tartarus | 塔尔塔罗斯地狱巨蛇 | unique-monster; source=monsters.txt; branch-qualified display name |

<!-- domain:unique-monsters -->
## 十九、独特怪物名称

| EN | ZH | Scope / comment |
|----|----|----------------|
| Agnes | 艾格尼丝 | unique-monster; source=source.txt |
| Aizul | 艾祖尔 | unique-monster; source=source.txt |
| Amaemon | 亚麦蒙 | unique-monster; source=source.txt |
| Antaeus | 安泰俄斯 | unique-monster; source=source.txt |
| Arachne | 阿拉克涅 | unique-monster; source=source.txt |
| Asmodeus | 阿斯摩蒂斯 | unique-monster; source=source.txt |
| Asterion | 阿斯忒里翁 | unique-monster; source=source.txt |
| Azrael | 阿兹瑞尔 | unique-monster; source=source.txt |
| Bai Suzhen | 白素贞 | unique-monster; source=source.txt |
| Boris | 鲍里斯 | unique-monster; source=source.txt |
| Cerebov | 塞雷波夫 | unique-monster; source=source.txt |
| Chuck | 查克 | unique-monster; source=source.txt |
| Crazy Yiuf | 疯狂的尤夫 | unique-monster; source=source.txt |
| Dispater | 迪斯帕特 | unique-monster; source=source.txt |
| Dissolution | 分解者 | unique-monster; source=source.txt |
| Donald | 唐纳德 | unique-monster; source=source.txt |
| Dowan | 多万 | unique-monster; source=source.txt |
| Duvessa | 杜维莎 | unique-monster; source=source.txt |
| Edmund | 埃德蒙 | unique-monster; source=source.txt |
| Enchantress | 妖术女王 | unique-monster; source=source.txt |
| Ereshkigal | 埃列什基伽勒 | unique-monster; source=source.txt |
| Erica | 艾丽卡 | unique-monster; source=source.txt |
| Erolcha | 伊罗查 | unique-monster; source=source.txt |
| Eustachio | 尤斯塔奇奥 | unique-monster; source=source.txt |
| Fannar | 凡纳尔 | unique-monster; source=source.txt |
| Frances | 弗朗西斯 | unique-monster; source=source.txt |
| Frederick | 弗雷德里克 | unique-monster; source=source.txt |
| Gastronok | 加斯特罗诺克 | unique-monster; source=source.txt |
| Geryon | 格律翁 | unique-monster; source=source.txt |
| Gloorx Vloq | 格洛克斯·弗洛克 | unique-monster; source=source.txt |
| Grinder | 格林德 | unique-monster; source=source.txt |
| Grum | 格拉姆 | unique-monster; source=source.txt |
| Grunn | 格伦 | unique-monster; source=source.txt |
| Harold | 哈罗德 | unique-monster; source=source.txt |
| Ignacio | 伊格纳西奥 | unique-monster; source=source.txt |
| Ijyb | 艾吉布 | unique-monster; source=source.txt |
| Ilsuiw | 伊尔苏伊 | unique-monster; source=source.txt |
| Jeremiah | 耶利米 | unique-monster; source=source.txt |
| Jessica | 杰西卡 | unique-monster; source=source.txt |
| Jorgrun | 约格伦 | unique-monster; source=source.txt |
| Jory | 乔里 | unique-monster; source=source.txt |
| Joseph | 约瑟夫 | unique-monster; source=source.txt |
| Josephina | 约瑟菲娜 | unique-monster; source=source.txt |
| Josephine | 约瑟芬 | unique-monster; source=source.txt |
| Khufu | 胡夫 | unique-monster; source=source.txt |
| Kirke | 喀耳刻 | unique-monster; source=source.txt |
| Lernaean hydra | 勒拿多头蛇 | unique-monster; source=source.txt |
| Lodul | 洛杜尔 | unique-monster; source=source.txt |
| Lom Lobon | 洛姆·洛邦 | unique-monster; source=source.txt |
| Louise | 路易丝 | unique-monster; source=source.txt |
| Mara | 玛拉 | unique-monster; source=source.txt |
| Maggie | 玛吉 | unique-monster; source=source.txt |
| Margery | 玛杰丽 | unique-monster; source=source.txt |
| Maurice | 莫里斯 | unique-monster; source=source.txt |
| Menkaure | 门卡拉 | unique-monster; source=source.txt |
| Mennas | 门纳斯 | unique-monster; source=source.txt |
| Mlioglotl | 姆利奥格洛特尔 | unique-monster; source=source.txt |
| Mnoleg | 姆诺雷格 | unique-monster; source=source.txt |
| Murray | 默里 | unique-monster; source=source.txt |
| Natasha | 娜塔莎 | unique-monster; source=source.txt |
| Nellie | 内莉 | unique-monster; source=source.txt |
| Nergalle | 内尔加勒 | unique-monster; source=source.txt |
| Nessos | 涅索斯 | unique-monster; source=source.txt |
| Nikola | 尼古拉 | unique-monster; source=source.txt |
| Norris | 诺里斯 | unique-monster; source=source.txt |
| Pargi | 帕尔吉 | unique-monster; source=source.txt |
| Parghit | 帕吉特 | unique-monster; source=source.txt |
| Pikel | 皮克尔 | unique-monster; source=source.txt |
| Polyphemus | 波吕斐摩斯 | unique-monster; source=source.txt |
| Prince Ribbit | 蛙王子 | unique-monster; source=source.txt |
| Robin | 罗宾 | unique-monster; source=source.txt |
| Roxanne | 罗克珊 | unique-monster; source=source.txt |
| Rupert | 鲁珀特 | unique-monster; source=source.txt |
| Saint Roka | 圣罗卡 | unique-monster; source=source.txt |
| Sigmund | 西格蒙德 | unique-monster; source=source.txt |
| Snorg | 斯诺格 | unique-monster; source=source.txt |
| Sojobo | 索乔波 | unique-monster; source=source.txt |
| Sonja | 索尼娅 | unique-monster; source=source.txt |
| Terence | 特伦斯 | unique-monster; source=source.txt |
| Tiamat | 提亚马特 | unique-monster; source=source.txt |
| Urug | 乌鲁格 | unique-monster; source=source.txt |
| Vashnia | 瓦什妮亚 | unique-monster; source=source.txt |
| Vv | 芙芙 | unique-monster; source=source.txt |
| Xtahua | 扎塔瓦 | unique-monster; source=source.txt |
| Zenata | 泽娜塔 | unique-monster; source=source.txt |

<!-- domain:monster-titles -->
## 二十、独特怪物称号（首批）

| EN | ZH | Scope / comment |
|----|----|----------------|
| Agnes title | 漫游者艾格尼丝 | monster-title; source=database/zh/montitle.txt |
| Aizul title | 疏忽的守卫艾祖尔 | monster-title; source=database/zh/montitle.txt |
| Amaemon title | 恶魔投毒者亚麦蒙 | monster-title; source=database/zh/montitle.txt |
| Antaeus title | 安泰俄斯，悲叹河的守卫 | monster-title; source=database/zh/montitle.txt |
| Arachne title | 编织者阿拉克涅 | monster-title; source=database/zh/montitle.txt |
| Asmodeus title | 阿斯摩蒂斯，欣嫩谷的王子 | monster-title; source=database/zh/montitle.txt |
| Asterion title | 堕落之王阿斯忒里翁 | monster-title; source=database/zh/montitle.txt |
| Azrael title | 无边烈焰阿兹瑞尔 | monster-title; source=database/zh/montitle.txt |
| Bai Suzhen title | 白素贞，白蛇夫人 | monster-title; source=database/zh/montitle.txt |
| Boris title | 鲍里斯，生死大师 | monster-title; source=database/zh/montitle.txt |
| Cerebov title | 塞雷波夫，火与钢之恶魔领主 | monster-title; source=database/zh/montitle.txt |
| Chuck title | 收集者查克 | monster-title; source=database/zh/montitle.txt |
| Crazy Yiuf title | 开悟者疯狂的尤夫 | monster-title; source=database/zh/montitle.txt |
| Dispater title | 迪斯帕特，铁城领主 | monster-title; source=database/zh/montitle.txt |
| Dissolution title | 分解者，吉瓦的高级祭司 | monster-title; source=database/zh/montitle.txt |

<!-- domain:spells -->
## 二十一、法术名全表

> 最终译名依据 `docs/spell-naming-rules.md` 审阅确定。
> 修订标记：✅ 保留原译，📝 修订，🆕 新增。

### Blink（现行 8；已移除／TAG 34 兼容 1）

| EN | ZH | 备注 |
|---------|------|------|
| Blink | 闪烁 | ✅ 现行 |
| Blink Allies Away | 使盟友闪烁远离 | 📝 现行 |
| Blink Allies Encircling | 使盟友闪烁合围 | 📝 现行 |
| Blink Away | 远离闪烁 | ✅ 现行 |
| Blink Close | 接近闪烁 | ✅ 现行 |
| Blink Other | 使他人闪烁 | 📝 现行 |
| Blink Other Close | 使他人闪烁靠近 | 📝 现行 |
| Blink Range | 退避闪烁 | ✅ 现行 |
| Controlled Blink | 受控闪烁 | ✅ 已移除／TAG 34 兼容 |

### Bolt（现行 16；已移除／TAG 34 兼容 3）

| EN | ZH | 备注 |
|---------|------|------|
| Blinkbolt | 闪烁箭 | ✅ 现行；复合词形保留 |
| Bolt of Cold | 寒冰箭 | ✅ 现行 |
| Bolt of Devastation | 毁灭箭 | ✅ 现行 |
| Bolt of Draining | 衰竭箭 | 📝 现行；Drain 状态，不表示生命／魔力转移 |
| Bolt of Fire | 火焰箭 | ✅ 现行 |
| Bolt of Flesh | 血肉箭 | ✅ 现行 |
| Bolt of Light | 光箭 | ✅ 现行 |
| Bolt of Magma | 岩浆箭 | ✅ 现行 |
| Corrosive Bolt | 腐蚀箭 | ✅ 现行 |
| Doom Bolt | 厄运箭 | ✅ 现行 |
| Electrical Bolt | 电击箭 | ✅ 现行 |
| Lightning Bolt | 闪电箭 | ✅ 现行 |
| Quicksilver Bolt | 水银箭 | ✅ 现行 |
| Sojourning Bolt | 羁旅箭 | 📝 现行 |
| Thunderbolt | 雷击 | ✅ 现行；固定词形例外 |
| Venom Bolt | 毒液箭 | ✅ 现行 |
| Bolt of Inaccuracy | 偏差箭矢 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Explosive Bolt | 爆裂弩矢 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Random Bolt | 随机箭矢 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |

### Summon（57）

| EN | ZH | 备注 |
|---------|------|------|
| Call Canine Familiar | 呼唤犬类使魔 | ✅ |
| Call Down Damnation | 降下天谴 | ✅；`Call Down` 为“降下”，不属于呼唤词根 |
| Call Down Lightning | 降下闪电 | ✅ |
| Call Imp | 呼唤小恶魔 | ✅ |
| Call Lost Souls | 呼唤迷失灵魂 | ✅ |
| Call Tide | 呼唤潮汐 | ✅ |
| Call of Chaos | 混沌呼唤 | ✅ |
| Demonic Horde | 恶魔大军 | ✅ |
| Hunting Call | 狩猎呼唤 | ✅ |
| Malign Gateway | 邪恶传送门 | ✅ |
| Mara Summon | 玛拉召唤 | ✅ |
| Monstrous Menagerie | 怪物动物园 | ✅ |
| Rakshasa Summon | 召唤罗刹 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Recall | 召回术 | ✅ |
| Shadow Creatures | 暗影生物 | ✅ |
| Spawn Tentacles | 生成触须 | ✅ |
| Summon Air Elementals | 召唤气元素 | ✅ |
| Summon Butterflies | 召唤蝴蝶 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Summon Cactus Giant | 召唤仙人掌巨人 | ✅ |
| Summon Demon | 召唤恶魔 | ✅ |
| Summon Dragon | 召唤巨龙 | ✅ |
| Summon Drakes | 召唤幼龙 | ✅ |
| Summon Earth Elementals | 召唤地元素 | ✅ |
| Summon Elemental | 召唤元素 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Summon Emperor Scorpions | 召唤帝王蝎 | ✅；复用实体 `emperor scorpion → 帝王蝎` |
| Summon Executioners | 召唤处刑人 | ✅；复用实体 `Executioner → 处刑人` |
| Summon Eyeballs | 召唤眼球 | ✅ |
| Summon Fire Elementals | 召唤火元素 | ✅ |
| Summon Forest | 召唤森林 | ✅ |
| Summon Greater Demon | 召唤高等恶魔 | ✅ |
| Summon Hell Sentinel | 召唤地狱哨兵 | ✅ |
| Summon Holies | 召唤神圣生物 | ✅；召出天使等神圣生物，非灵体 |
| Summon Horrible Things | 召唤恐怖之物 | ✅ |
| Summon Hydra | 召唤多头蛇 | ✅ |
| Summon Ice Beast | 召唤冰兽 | ✅ |
| Summon Illusion | 召唤幻象 | ✅ |
| Summon Iron Elementals | 召唤铁元素 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Summon Mana Viper | 召唤魔力毒蛇 | ✅；复用实体 `mana viper → 魔力毒蛇` |
| Summon Minor Demon | 召唤次级恶魔 | ✅ |
| Summon Mortal Champion | 召唤凡人冠军 | ✅ |
| Summon Mushrooms | 召唤蘑菇 | ✅ |
| Summon Rakshasa | 召唤罗刹 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Summon Scarabs | 召唤圣甲虫 | ✅ |
| Summon Scorpions | 召唤蝎子 | ✅ |
| Summon Seismosaurus Egg | 召唤地震龙蛋 | ✅；复用实体 `seismosaurus egg → 地震龙蛋` |
| Summon Sin Beast | 召唤罪孽兽 | ✅；复用实体 `sin beast → 罪孽兽` |
| Summon Small Mammal | 召唤小型哺乳动物 | ✅ |
| Summon Spiders | 召唤蜘蛛 | ✅ |
| Summon Twister | 召唤旋风 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Summon Tzitzimitl | 召唤齐齐米特尔 | ✅ |
| Summon Ufetubus | 召唤乌菲特布斯 | ✅；复用实体 `ufetubus → 乌菲特布斯` |
| Summon Undead | 召唤亡灵 | ✅ |
| Summon Vermin | 召唤害虫 | ✅ |
| Summon Water Elementals | 召唤水元素 | ✅ |
| Summon swarm | 召唤虫群 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Vampire Summon | 召唤吸血鬼 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Word of Recall | 召回之言 | ✅ |

### X Cloud 后缀系列（现行 8；已移除／TAG 34 兼容 4）

| EN | ZH | 备注 |
|---------|------|------|
| Flaming Cloud | 燃烧云 | ✅ 现行 |
| Freezing Cloud | 冰冻云 | ✅ 现行 |
| Ink Cloud | 墨云 | ✅ 现行 |
| Mephitic Cloud | 迷瘴云 | ✅ 现行 |
| Noxious Cloud | 毒瘴云 | ✅ 现行 |
| Petrifying Cloud | 石化云 | ✅ 现行 |
| Poisonous Cloud | 毒云 | ✅ 现行 |
| Spectral Cloud | 幽灵云 | ✅ 现行 |
| Fire cloud | 火云 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Miasma cloud | 瘴气云 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Poison cloud | 毒气云 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Steam cloud | 蒸汽云 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |

### Breath（22）

| EN | ZH | 备注 |
|---------|------|------|
| Caustic Breath | 腐蚀吐息 | ✅ |
| Chaos Breath | 混沌吐息 | ✅ |
| Cold Breath | 寒霜吐息 | ✅；与 `Breathe Frost → 吐息寒霜` 复用元素词 |
| Combustion Breath | 爆燃吐息 | ✅；射出的挥发余烬会在每个触及生物周围爆炸 |
| Draconian Breath | 龙人吐息 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Fire Breath | 火焰吐息 | ✅ |
| Galvanic Breath | 电击吐息 | ✅ |
| Glacial Breath | 冰川吐息 | ✅ |
| Golden Breath | 金龙吐息 | 🆕 |
| Holy Breath | 神圣吐息 | ✅ |
| Miasma Breath | 瘴气吐息 | ✅ |
| Mud Breath | 泥浆吐息 | ✅ |
| Noxious Breath | 毒瘴吐息 | ✅ |
| Nullifying Breath | 消魔吐息 | ✅ |
| Old serpent of hell breath | 地狱古蛇吐息 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Rust Breath | 锈蚀吐息 | ✅ |
| Searing Breath | 灼热吐息 | 📝 |
| Steam Breath | 蒸汽吐息 | ✅ |
| cocytus serpent of hell breath | 悲叹河地狱巨蛇吐息 | ✅；复用分支限定实体名 |
| dis serpent of hell breath | 铁城地狱巨蛇吐息 | ✅；复用分支限定实体名 |
| gehenna serpent of hell breath | 欣嫩谷地狱巨蛇吐息 | ✅；复用分支限定实体名 |
| tartarus serpent of hell breath | 塔尔塔罗斯地狱巨蛇吐息 | ✅；复用分支限定实体名 |

### Gaze（7）

| EN | ZH | 备注 |
|---------|------|------|
| Antimagic Gaze | 反魔法凝视 | ✅ |
| Confusion Gaze | 困惑凝视 | ✅ |
| Draining Gaze | 衰竭凝视 | ✅；施加 Drain/衰竭，不治疗施法者 |
| Mutagenic Gaze | 变异凝视 | ✅ |
| Paralysis Gaze | 麻痹凝视 | ✅ |
| Vitrifying Gaze | 玻璃化凝视 | ✅ |
| Weakening Gaze | 虚弱凝视 | ✅ |

### Touch（2）

| EN | ZH | 备注 |
|---------|------|------|
| Agonising Touch | 剧痛之触 | ✅ |
| Confusing Touch | 困惑之触 | ✅ |

### Flame / Flames（10）

| EN | ZH | 备注 |
|---------|------|------|
| Throw Flame | 投掷火焰 | ✅；复用 Throw 系列证据 |
| Sticky Flame | 黏着火焰 | ✅ |
| Holy Flames | 神圣火焰 | ✅ |
| Inner Flame | 内焰 | ✅ |
| Cleansing Flame | 净化之焰 | ✅ |
| Stoke Flames | 煽旺火焰 | 📝；`stoke` 指添燃料使火势更旺，并召出蔓延炼狱 |
| Flame Wave | 火焰波 | ✅ |
| Ring of Flames | 烈焰之环 | ⚠️ 已移除／TAG 34 兼容 |
| Conjure Flame | 召唤火焰 | ⚠️ 已移除／TAG 34 兼容 |
| Flame Tongue | 火焰之舌 | ⚠️ 已移除／TAG 34 兼容 |

### Form（6）

| EN | ZH | 备注 |
|---------|------|------|
| Dragon Form | 巨龙变形 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Hydra Form | 多头蛇变形 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Ice Form | 寒冰变形 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Spider Form | 蜘蛛变形 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Statue Form | 石像变形 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Storm Form | 风暴变形 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |

### Poison / Poisonous（9）

| EN | ZH | 备注 |
|---------|------|------|
| Poisonous Cloud | 毒云 | ✅；复用 Cloud 系列证据 |
| Poison Arrow | 毒箭 | ✅；复用 Arrow 系列证据 |
| Ignite Poison | 点燃毒素 | ✅ |
| Spit Poison | 喷吐毒液 | 📝；与同名能力及其描述统一 |
| Poisonous Vapours | 毒气 | ✅；瞬时气体，不形成持续云 |
| Cure Poison | 解毒术 | ⚠️ 已移除／TAG 34 兼容 |
| Localized Ignite Poison | 局部引爆毒素 | ⚠️ 已移除／TAG 34 兼容 |
| Poison Weapon | 淬毒武器 | ⚠️ 已移除／TAG 34 兼容 |
| Poison cloud | 毒气云 | ⚠️ 已移除／TAG 34 兼容 |

### Awaken（5）

| EN | ZH | 备注 |
|---------|------|------|
| Awaken Armour | 唤醒护甲 | ✅ |
| Awaken Flesh | 唤醒血肉 | ✅ |
| Awaken Forest | 唤醒森林 | ✅ |
| Awaken Vines | 唤醒藤蔓 | ✅ |
| Awaken Earth | 唤醒大地 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |

### Forge（4）

| EN | ZH | 备注 |
|---------|------|------|
| Forge Blazeheart Golem | 锻造炽心魔像 | ✅ |
| Forge Lightning Spire | 锻造闪电尖塔 | ✅ |
| Forge Monarch Bomb | 锻造君主炸弹 | ✅ |
| Forge Phalanx Beetle | 锻造方阵甲虫 | ✅ |

### Possessive（35）

| EN | ZH | 备注 |
|---------|------|------|
| Alistair's Intoxication | 阿利斯泰尔之醉 | ✅；混乱视野内智慧生物，成功时施法者短暂眩晕 |
| Alistair's Walking Alembic | 阿利斯泰尔之行走蒸馏器 | ✅；战斗构装酿造并分发药水 |
| Borgnjor's Revivification | 博格尼尔之复苏 | 🆕；完全治愈仍活着的施法者，不会复活死者 |
| Borgnjor's Vile Clutch | 博格尼尔之邪恶抓握 | ✅ |
| Brom's Barrelling Boulder | 布罗姆之碾压巨石 | ✅；滚石碾过死者并推动幸存者 |
| Cigotuvi's Degeneration | 西格图维之退化 | ✅；已移除兼容标题，无当前机制可供反推 |
| Cigotuvi's Embrace | 西格图维之拥抱 | ✅；已移除兼容标题，无当前机制可供反推 |
| Cigotuvi's Putrefaction | 西格图维之腐烂 | ✅；使重伤活物持续涌出瘴气，施法者承受暂时生命汲取 |
| Death's Door | 死亡之门 | ✅；近乎免疫伤害但将生命降至濒死状态 |
| Dragon's Call | 龙之呼唤 | ✅ |
| Druid's Call | 德鲁伊呼唤 | ✅；召回同层已有林地生物，非创造召唤物 |
| Eringya's Noxious Bog | 埃林吉亚之毒沼 | ✅；有毒污泥将附近坚实地面暂时转为毒沼 |
| Eringya's Surprising Crocodile | 埃林吉亚之意外鳄鱼 | ✅；保留原名刻意突兀的戏谑语气 |
| Gell's Gavotte | 盖尔之加沃特 | ✅；重定向局部重力，使视野内生物随方向翻滚 |
| Gell's Gravitas | 盖尔之重力 | ✅；重力铃鼓专用效果，将怪物拉拢并固定 |
| Iskenderun's Battlesphere | 伊斯肯德伦之战斗法球 | 🆕；与实体及运行时 `battlesphere → 战斗法球` 统一 |
| Iskenderun's Mystic Blast | 伊斯肯德伦之神秘冲击 | ✅ |
| Leda's Liquefaction | 勒达之液化 | ✅；液化施法者周围地面 |
| Lee's Rapid Deconstruction | 李之快速解构 | ✅；粉碎墙壁或脆性目标形成爆炸碎片 |
| Lehudib's Crystal Spear | 勒胡迪布之水晶矛 | ✅；短射程高伤害水晶投射物 |
| Martyr's Knell | 殉道者之丧钟 | ✅；殉道者灵魂替盟友分担伤害 |
| Maxwell's Capacitive Coupling | 麦克斯韦之电容耦合 | ✅；专名统一为“麦克斯韦” |
| Maxwell's Portable Piledriver | 麦克斯韦之便携打桩机 | ✅；空间压缩后将整列生物推向障碍物 |
| Nazja's All-Purpose Tempering | 纳兹亚之通用淬炼 | ✅；可修复并强化附近任意构装体 |
| Nazja's Percussive Tempering | 纳兹亚之冲击淬炼 | ✅；修复并强化施法者锻造的构装体 |
| Olgreb's Toxic Radiance | 奥尔格雷布之毒辐射 | ✅；持续毒害视线内所有生物 |
| Ozocubu's Armour | 奥佐库布之护甲 | ✅；厚冰护体并提高护甲，移动后消失 |
| Ozocubu's Refrigeration | 奥佐库布之制冷 | ✅；冻结视野内其他生物，邻接盟友可减伤 |
| Sentinel's Mark | 哨兵印记 | ✅；向同层所有生物暴露目标的位置 |
| Sheza's Dance | 谢扎之舞 | ✅；从各处召来并活化武器 |
| Trog's Hand | 特洛格之手 | ✅；提供强力恢复与意志力 |
| Tukima's Dance | 图基玛之舞 | ✅；活化敌方武器使其倒戈 |
| Vhi's Electric Charge | 维之电击冲锋 | 🆕；`charge` 是向敌人冲锋，不是静态“电荷” |
| Vhi's Electrolunge | 维之电击突进 | 🆕；怪物版近身突进，与玩家版“冲锋”区分 |
| Yara's Violent Unravelling | 亚拉之猛烈解构 | ✅；撕裂附魔并转化为诱变爆炸 |

### Projectile（7）

| EN | ZH | 备注 |
|---------|------|------|
| Magic Dart | 魔法飞弹 | ✅ |
| Mercury Arrow | 汞矢 | ✅；与 `Quicksilver Bolt → 水银箭` 区分的辨识性例外 |
| Poison Arrow | 毒箭 | ✅ |
| Poisonous Vapours | 毒气 | ✅ |
| Pyre Arrow | 烈火箭 | ✅；液态火焰附着目标并持续灼烧 |
| Slug Dart | 蛞蝓飞镖 | ✅；由飞镖蛞蝓发射硬化甲壳质尖镖 |
| Stone Arrow | 石箭 | ✅ |

### Arrow（4）

| EN | ZH | 备注 |
|---------|------|------|
| Mercury Arrow | 汞矢 | ✅；为避免与 `Quicksilver Bolt → 水银箭` 重名，不套用常规“箭”词尾 |
| Poison Arrow | 毒箭 | ✅ |
| Pyre Arrow | 烈火箭 | ✅；液态火焰附着目标并持续灼烧 |
| Stone Arrow | 石箭 | ✅ |

### Beam（1）

| EN | ZH | 备注 |
|---------|------|------|
| Plasma Beam | 等离子光束 | ✅；电击束无视一半护甲，随后追加同路径火焰束 |

### Shadow（13）

| EN | ZH | 备注 |
|---------|------|------|
| Creeping Shadow | 蔓延暗影 | ✅ |
| Shadow Beam | 暗影光束 | ✅ |
| Shadow Bind | 暗影束缚 | ✅ |
| Shadow Draining | 暗影吸取 | ✅ |
| Shadow Prism | 暗影棱镜 | ✅ |
| Shadow Puppet | 暗影傀儡 | ✅ |
| Shadow Shard | 暗影碎片 | ✅ |
| Shadow Shot | 暗影射击 | ✅ |
| Shadow Tempest | 暗影风暴 | ✅ |
| Shadow Torpor | 暗影麻木 | ✅ |
| Shadow Turret | 暗影炮塔 | ✅ |
| Shadowball | 暗影球 | ✅ |
| Weave Shadows | 编织暗影 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |

### Dispel（2）

| EN | ZH | 备注 |
|---------|------|------|
| Dispel Undead | 驱散亡灵 | ✅；相邻目标 |
| Dispel Undead Range | 远程驱散亡灵 | ✅；射程 4 的怪物版本 |

### Other（316）

| EN | ZH | 备注 |
|---------|------|------|
| Abjuration | 驱逐术 | ✅；缩短附近所有敌对召唤生物的剩余存续时间 |
| Acid Ball | 酸液球 | ✅；投掷后爆炸的腐蚀性酸液球 |
| Agony | 剧痛 | 🆕 |
| Airstrike | 空袭 | ✅ |
| Anguish | 哀痛 | 📝 |
| Animate Dead | 操纵死尸 | ✅ |
| Animate Skeleton | 召唤骷髅 | ✅ |
| Apportation | 隔空取物 | ✅ |
| Arcjolt | 电弧震击 | ✅ |
| Aura of Abjuration | 驱逐灵气 | ✅；已移除兼容标题 |
| Avatar Song | 化身之歌 | ✅；限制冒险者远离、眩晕其他生物并可能召来溺魂 |
| Awaken Armour | 唤醒护甲 | ✅ |
| Awaken Earth | 唤醒大地 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Awaken Flesh | 唤醒血肉 | ✅ |
| Awaken Forest | 唤醒森林 | ✅ |
| Awaken Vines | 唤醒藤蔓 | ✅ |
| Banishment | 放逐 | ✅ |
| Battlecry | 战吼 | ✅ |
| Beckoning Gale | 召唤强风 | ✅ |
| Berserk Other | 狂暴他人 | ✅ |
| Berserker Rage | 狂暴之怒 | ✅ |
| Bestow Arms | 赐予武器 | ✅ |
| Bind Souls | 绑定灵魂 | ✅ |
| Bombard | 炮击 | ✅ |
| Brain Bite | 脑噬 | ✅ |
| Brothers in Arms | 战友 | 📝 |
| Cantrip | 小戏法 | ✅ |
| Cause Fear | 恐惧术 | ✅ |
| Chain Lightning | 连锁闪电 | ✅；从最近生物开始向外连锁，距离越远伤害越低 |
| Chain of Chaos | 混沌之链 | ✅ |
| Chant Fire Storm | 咏唱火焰风暴 | ✅；已移除／TAG 34 兼容标题 |
| Charm | 魅惑 | ✅ |
| Cleansing Flame | 净化之焰 | ✅ |
| Cloud Cone | 云雾锥 | ⚠️ 已移除／TAG 34 兼容；非 `X Cloud` 后缀成员，机制证据不足，暂沿用 |
| Concentrate Venom | 浓缩毒液 | ✅ |
| Condensation Shield | 凝结之盾 | 🆕 |
| Confuse | 混乱 | ✅ |
| Conjure Ball Lightning | 召唤球形闪电 | ✅；创造会追敌并爆炸的球状闪电 |
| Conjure Flame | 召唤火焰 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Conjure Living Spells | 召唤活体法术 | ✅ |
| Construct Spike Launcher | 构建尖刺发射器 | ✅ |
| Control Teleport | 控制传送 | 🆕；已移除兼容标题，修正中文倒装 |
| Control Undead | 控制亡灵 | 🆕；已移除兼容标题，修正中文倒装 |
| Control Winds | 控风术 | ✅；已移除兼容标题 |
| Corona | 怪异发光球 | ✅ |
| Corpse Rot | 尸体腐烂 | ✅ |
| Corrupt | 腐化 | ✅ |
| Corrupt Body | 腐化躯体 | ✅ |
| Corrupting Pulse | 腐化脉冲 | ✅ |
| Creeping Frost | 蔓延冰霜 | ✅；从墙壁唤出冻气，冻结并减速墙边敌人 |
| Crystallising Shot | 结晶射击 | ✅ |
| Cure Poison | 解毒术 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Curse of Agony | 痛苦诅咒 | ✅ |
| Darkness | 黑暗术 | ✅ |
| Death Channel | 死亡通道 | ✅；引导期间令被杀的活物、恶魔和神圣生物留下幽魂作战 |
| Death Rattle | 死亡之响 | ✅；呼出垂死精粹并生成瘴气云 |
| Debugging Ray | 调试射线 | ✅ |
| Deflect Missiles | 偏转飞弹 | ✅ |
| Delayed Fireball | 延迟火球 | ✅；已移除兼容标题 |
| Detonation Catalyst | 引爆催化剂 | ✅ |
| Diamond Sawblades | 钻石锯片 | ✅ |
| Dig | 挖掘 | ✅ |
| Dimension Anchor | 维度锚定 | ✅ |
| Dimensional Bullseye | 维度靶心 | ✅ |
| Diminish Spells | 削弱法术 | ✅ |
| Discord | 纷乱 | 📝 |
| Disjunction | 空间分离 | ✅ |
| Dispersal | 空间驱离 | ✅；传送系法术，将附近生物传送或闪送离开；与 Dispel「驱散」区分 |
| Divine Armament | 神圣武装 | ✅ |
| Dominate Undead | 支配亡灵 | ✅ |
| Doomsaying | 宣告厄运 | ✅ |
| Drain Life | 吸取生命 | ✅ |
| Drain Magic | 汲取魔力 | ✅ |
| Dream Dust | 梦尘 | ✅ |
| Enfeeble | 衰弱 | ✅ |
| Ensnare | 束缚 | ✅ |
| Ensorcelled Hibernation | 冬眠 | ✅ |
| Entropic Weave | 熵之编织 | ✅ |
| Ephemeral Infusion | 短暂灌注 | ✅；已移除兼容标题 |
| Eruption | 喷发 | ✅ |
| Evaporate | 蒸发术 | ✅ |
| Excruciating Wounds | 剧痛之伤 | ✅ |
| Fastroot | 快速扎根 | ✅ |
| Fire Brand | 火焰烙印 | ✅ |
| Fire Storm | 火焰风暴 | ✅；9 级大范围定点火焰爆炸，并留下短暂火旋涡 |
| Fireball | 火球 | ✅；投掷会爆炸的火焰球 |
| Flame Tongue | 火焰之舌 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Flame Wave | 火焰波 | ✅ |
| Flash Freeze | 急冻 | ✅；对目标造成高额伤害和短时减速，一半伤害无视寒冷抗性 |
| Flashing Balestra | 闪光弩击 | ✅ |
| Flay | 剥皮 | ✅ |
| Fleetfoot | 轻快脚步 | ✅ |
| Flight | 飞行术 | ✅ |
| Force Lance | 力量之矛 | ✅ |
| Forceful Dismissal | 强制驱逐 | ✅ |
| Forceful Invitation | 强制邀请 | ✅ |
| Forge Blazeheart Golem | 锻造炽心魔像 | ✅ |
| Forge Lightning Spire | 锻造闪电尖塔 | ✅ |
| Forge Monarch Bomb | 锻造君主炸弹 | ✅ |
| Forge Phalanx Beetle | 锻造方阵甲虫 | ✅ |
| Fortress Blast | 堡垒冲击 | ✅ |
| Foxfire | 狐火 | 🆕 |
| Freeze | 冰冻 | ✅；相邻单体寒冷攻击，伤害无视护甲 |
| Freezing Aura | 冰封灵气 | ✅；已移除兼容标题 |
| Freezing Gust | 冰冻阵风 | 🆕；穿透性严寒气流，沿途留下寒气云 |
| Frenzy | 狂乱术 | ✅ |
| Frozen Ramparts | 冰冻壁垒 | ✅；短暂冰封周围墙壁并伤害邻近敌人 |
| Fugue of the Fallen | 亡灵赋格 | ✅ |
| Fulminant Prism | 爆裂棱镜 | ✅ |
| Fulsome Distillation | 精华蒸馏 | ✅ |
| Fulsome Fusillade | 猛烈连射 | ✅ |
| Funeral Dirge | 葬礼哀歌 | ✅ |
| Ghostly Fireball | 幽灵火球 | ✅；负能量爆炸使范围内活物衰竭 |
| Ghostly Sacrifice | 幽灵献祭 | ✅ |
| Glaciate | 冰封 | 🆕；锥形寒冰冲击会冰封并减速目标 |
| Gloom | 阴郁 | ✅ |
| Goad Beasts | 激怒野兽 | ✅ |
| Grand Avatar | 大化身 | ✅ |
| Grasping Roots | 抓握根须 | ✅ |
| Grave Claw | 墓爪 | ✅ |
| Greater Ensnare | 强力束缚 | ✅ |
| Hailstorm | 冰雹风暴 | ✅；环形冰雹避开紧邻施法者的目标 |
| Harpoon Shot | 鱼叉射击 | ✅ |
| Haste | 加速 | ✅；提高施法者行动速度 |
| Haste Other | 加速他人 | ✅；提高附近盟友行动速度 |
| Haste Plants | 加速植物 | ✅；已移除兼容标题 |
| Haunt | 鬼魂缠身 | ✅ |
| Heal Other | 治愈他人 | ✅ |
| Hellfire Court | 地狱火法庭 | ✅ |
| Hellfire Mortar | 地狱火迫击炮 | ✅ |
| Hoarfrost Bullet | 白霜弹 | ✅；火炮发射的冰霜碎片，命中后施加脆霜减速 |
| Hoarfrost Cannonade | 白霜炮击 | ✅；塑造两座自耗式远程冰霜火炮 |
| Holy Flames | 神圣火焰 | ✅ |
| Holy Light | 圣光术 | ✅ |
| Holy word | 圣言术 | ✅ |
| Homunculus | 人造人 | ✅ |
| Hunting Cry | 狩猎战吼 | ✅ |
| Hurl Damnation | 投掷诅咒 | ✅ |
| Hurl Sludge | 投掷污泥 | ✅ |
| Hurl Torchlight | 投掷火炬之光 | ✅ |
| Iceblast | 冰爆 | ✅；冰块撞击后爆炸，一半伤害无视寒冷抗性 |
| Ignite Poison | 点燃毒素 | ✅ |
| Ignition | 点火 | ✅ |
| Ill Omen | 凶兆 | ✅ |
| Infernal Servant | 地狱仆从 | ✅ |
| Infestation | 虫群侵扰 | ✅ |
| Infusion | 灌注术 | ✅；已移除兼容标题 |
| Injury Bond | 伤害链接 | ✅ |
| Injury Mirror | 伤害反射 | ✅ |
| Inner Flame | 内焰 | ✅ |
| Insulation | 绝缘术 | ✅ |
| Invisibility | 隐身术 | ✅；使施法者隐形 |
| Invisibility Other | 使他人隐形 | 🆕；使附近盟友隐形 |
| Iron Shot | 铁弹 | ✅ |
| Irradiate | 辐射 | ✅ |
| Jinxbite | 厄运之咬 | ✅ |
| Kinetic Grapnel | 动力抓钩 | ✅ |
| Kiss of Death | 死亡之吻 | ✅；衰竭目标并暂时降低施法者生命值 |
| Landbreaker | 裂地 | ✅ |
| Launch Bomblet | 发射小型炸弹 | ✅ |
| Launch Clockwork Bee | 发射发条蜜蜂 | ✅ |
| Launch Sporangium | 发射孢子囊 | ✅ |
| Legendary Destruction | 传奇毁灭 | ✅ |
| Lesser Beckoning | 次级召唤 | ✅ |
| Lethal Infusion | 致命灌注 | ✅；已移除兼容标题 |
| Localized Ignite Poison | 局部引爆毒素 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Magma Barrage | 岩浆弹幕 | ✅ |
| Magnavolt | 磁暴 | ✅ |
| Major Destruction | 大型毁灭 | ✅ |
| Major Healing | 大型治疗 | ✅ |
| Malign Offering | 邪恶献祭 | ✅ |
| Malmutate | 恶性变异 | ✅ |
| Manifold Assault | 多重攻击 | ✅ |
| March of Sorrows | 悲伤行军 | ✅ |
| Marshlight | 沼泽之光 | ✅ |
| Mass Confusion | 群体混乱 | ✅ |
| Mass Regeneration | 群体再生 | ✅ |
| Melee | 近战 | ✅ |
| Mesmerise | 迷魂 | ✅；5 级怪物诅咒法术，使冒险者无法主动远离施法者、使其他生物眩晕；与 Sleep「沉睡」及 Charm「魅惑」区分；裁决=[D-A-043] |
| Metabolic Englaciation | 深度冻结 | ✅ |
| Metal Splinters | 金属碎片 | ✅ |
| Might | 强壮 | ✅ |
| Might Other | 强壮他人 | ✅ |
| Mindburst | 心智爆发 | ✅ |
| Minor Healing | 小型治疗 | ✅ |
| Mislead | 误导术 | ✅ |
| Momentum Strike | 动量打击 | ✅ |
| Mourning Wail | 哀悼嚎哭 | ✅ |
| Oblivion Howl | 湮灭嚎叫 | ✅ |
| Old Deflect Missiles | 旧版偏转飞弹 | ✅ |
| Orb of Destruction | 毁灭之球 | ✅ |
| Orb of Electricity | 电光球 | ✅；命中时产生大型电能爆炸 |
| Ostracise | 排斥 | ✅ |
| Pain | 痛苦 | ✅ |
| Paralyse | 麻痹 | ✅ |
| Passage of Golubria | 戈卢布里亚之通道 | ✅ |
| Passwall | 穿墙术 | ✅ |
| Permafrost Eruption | 永冻爆发 | ✅；地底严寒与落石轰击敌人最密集处，不在施法者身旁爆发 |
| Petrify | 石化 | ✅ |
| Phantom Blitz | 幻影突击 | ✅ |
| Phantom Mirror | 幻影镜 | ✅ |
| Phase Shift | 相位变换 | ✅ |
| Planar Overlay | 位面叠加 | ✅ |
| Plane Rend | 位面撕裂 | ✅ |
| Platinum Paragon | 白金典范 | ✅ |
| Poison Weapon | 淬毒武器 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Polar Vortex | 极地漩涡 | ✅ |
| Polymorph | 变形术 | ✅ |
| Porkalator | 变猪术 | ✅ |
| Portal Projectile | 传送投射物 | ✅ |
| Prayer of Brilliance | 聪慧祈祷 | ✅ |
| Primal Wave | 原始波浪 | ✅ |
| Pyroclastic Surge | 火山碎屑涌 | ✅ |
| Pyrrhic Recollection | 惨胜回忆 | ✅ |
| Random Effects | 随机效果 | ✅ |
| Ravenous Swarm | 贪婪虫群 | ✅ |
| Rearrange the Pieces | 重新布局 | ✅ |
| Rebounding Blaze | 弹跳烈焰 | ✅ |
| Rebounding Chill | 弹跳寒流 | 🆕；穿透性寒气束可从墙壁反弹并命中两次 |
| Regenerate Other | 再生他人 | 📝 |
| Regeneration | 快速再生 | ✅ |
| Rending Blade | 撕裂之刃 | ✅ |
| Resonance Strike | 共鸣打击 | ✅ |
| Resurrect | 复活术 | ✅ |
| Rimeblight | 霜疫 | ✅；从体内冻结宿主并可能在死亡时传播 |
| Ring of Flames | 烈焰之环 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Ring of Thunder | 雷霆之环 | ✅；已移除兼容标题 |
| Roll | 翻滚 | ✅ |
| Sacrifice | 献祭 | ✅ |
| Sandblast | 沙爆 | 📝 |
| Sap Magic | 削弱魔法 | ✅ |
| Scattershot | 散射术 | ✅ |
| Scorch | 烧焦 | ✅ |
| Sculpt Simulacrum | 塑造拟像 | ✅ |
| Seal Doors | 封印门 | ✅ |
| Searing Ray | 灼热射线 | ✅ |
| See Invisible | 侦测隐形 | 🆕 |
| Seismic Stomp | 地震践踏 | ✅ |
| Seracfall | 冰塔崩塌 | ✅ |
| Shaft Self | 自我竖井 | ✅ |
| Shatter | 粉碎 | ✅ |
| Shock | 震击 | ✅ |
| Shred | 撕裂 | ✅ |
| Shroud of Golubria | 戈卢布里亚之幕 | ✅ |
| Sigil of Binding | 束缚符文 | ✅ |
| Sign of Ruin | 毁灭征兆 | 🆕 |
| Silence | 沉默 | 🆕 |
| Silver Blast | 白银冲击 | ✅ |
| Singularity | 奇点术 | ✅ |
| Siphon Essence | 吸取精华 | ✅ |
| Siren Song | 塞壬之歌 | ✅；迷魂附近听众，离开施法者视野后解除移动限制 |
| Sleep | 睡眠 | ✅ |
| Sleetstrike | 冰雨打击 | ✅ |
| Slow | 减速 | 📝 |
| Smiting | 惩击 | ✅ |
| Song of Shielding | 护盾之歌 | ✅；已移除兼容标题 |
| Sonic wave | 音波 | ✅ |
| Soul Splinter | 灵魂分裂 | ✅ |
| Spectral Weapon | 灵体武器 | ✅ |
| Spellspark Servitor | 法术火花仆从 | ✅ |
| Sphinx Sisters | 斯芬克斯姐妹 | ✅ |
| Spit Acid | 喷吐酸液 | ✅；向单个目标喷吐酸液 |
| Spit Lava | 喷吐岩浆 | ✅ |
| Spit Poison | 喷吐毒液 | 📝；与同名能力及其描述统一 |
| Splinterfrost Shell | 碎霜之壳 | ✅；半圆冰障破裂时向破坏者齐射冰片 |
| Splinterspray | 碎片喷射 | ✅ |
| Sporulate | 产孢 | ✅ |
| Starburst | 星爆 | ✅ |
| Static Discharge | 静电释放 | ✅ |
| Steam Ball | 蒸汽球 | ✅ |
| Sticks to Snakes | 棍变蛇 | ✅ |
| Sticky Flame | 黏着火焰 | ✅ |
| Still Winds | 静止风 | ✅ |
| Sting | 毒刺 | 🆕 |
| Stoke Flames | 煽旺火焰 | 📝；`stoke` 指添燃料使火势更旺 |
| Stoneskin | 石肤术 | ✅ |
| Striking | 打击术 | ✅ |
| Strip Willpower | 剥离意志力 | ✅ |
| Stunning Burst | 眩晕爆发 | ✅ |
| Sublimation of Blood | 血液升华 | ✅ |
| Sunray | 阳光射线 | ✅ |
| Sure Blade | 精准之刃 | ✅ |
| Swiftness | 迅捷 | ✅ |
| Symbol of Torment | 折磨之符 | ✅ |
| Teleport Other | 传送他人 | ✅；短暂延迟后尝试将目标传送出施法者视野 |
| Teleport Self | 自我传送 | ✅；已移除兼容标题 |
| Throw | 投掷 | ⚠️ 已移除／TAG 34 兼容；机制证据不足，暂沿用 |
| Throw Ally | 投掷盟友 | ✅ |
| Throw Barbs | 投掷倒刺 | ✅ |
| Throw Bolas | 投掷流星索 | ✅ |
| Throw Flame | 投掷火焰 | ✅ |
| Throw Frost | 投掷冰霜 | ✅ |
| Throw Icicle | 投掷冰柱 | ✅ |
| Throw Klown Pie | 投掷小丑派 | ✅ |
| Tomb of Doroklohe | 多洛克洛之墓 | ✅ |
| Tremorstone | 震石 | ✅ |
| Twisted Resurrection | 扭曲复活 | ✅ |
| Unleash Destruction | 释放毁灭 | ✅ |
| Upheaval | 剧变 | ✅ |
| Vampiric Draining | 吸血术 | ✅ |
| Vanquished Vanguard | 败军先锋 | 📝 |
| Vex | 激怒 | ✅ |
| Virulence | 毒性 | ✅ |
| Vitrify | 玻璃化 | ✅ |
| Volatile Blastmotes | 不稳定爆尘 | ✅ |
| Volley of Thorns | 荆棘齐射 | ✅ |
| Vortex | 漩涡 | 🆕 |
| Wall of Brambles | 荆棘之墙 | ✅ |
| Warning Cry | 警告之嚎 | ✅ |
| Warp Body | 扭曲身体 | ✅ |
| Warp Space | 扭曲空间 | ✅ |
| Warp Weapon | 扭曲武器 | ✅ |
| Waterstrike | 水击 | ✅ |
| Wind Blast | 风击 | ✅ |
| Woodweal | 木质愈合 | ✅ |
| nonexistent spell | 不存在的法术 | ✅ |

**汇总**：511 法术，✅ 保留 469，📝 修订 30，🆕 新增 12。

---

*最后更新：2026-07-12 | 来源：docs/decisions.md + docs/spell-naming-rules.md + [legacy issue 12 glossary][legacy-12-glossary] + zh-translator.md*

[legacy-12-glossary]: https://github.com/yutio8888/crawl-chn-issues-archive/blob/d31fccd3eb2c2cd612739646769ee1b45b6dfb01/12/glossary_and_style.md
