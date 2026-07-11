# DCSS 中文翻译术语表

> 统一 SSOT——翻译 Agent 在翻译前必须查阅此文件。
> 来源合并：`docs/decisions.md` + `issues/12/glossary_and_style.md` + `zh-translator.md` prompt
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

### 常用法术/效果名

| EN | ZH | 注意事项 |
|----|----|---------|
| Orb of Destruction | 毁灭之球 | 法术名 |
| Might | 强效 | +10% 伤害 |
| Haste | 加速 | 行动速度 +50% |
| Berserk | 狂暴 | 近战加成但结束后减速 |
| Rampage | 冲锋 | 攻击时自动向敌人移动一步 |
| Teleport | 传送 | 位移效果 |
| Invisibility | 隐形 | 不可被看见 |
| Confusing Touch | 混乱之触 | 接触混乱效果 |
| Silence | 沉默 | 禁止施法/阅读卷轴 |

---

<!-- domain:core -->
## 四、核心游戏术语

| EN | ZH | 注意事项 |
|----|----|---------|
| spell | 法术 | 泛指 |
| spellpower | 法术威力 | **绝不**译为"法力"——法力 = MP |
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

| EN Key | ZH |
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
| demonspawn | 恶魔后裔 | — | 恶魔后裔 + 职业 |
| minotaur | 牛头人 | — | — |
| felid | 猫人 | — | — |
| octopode | 章鱼人 | — | — |
| gargoyle | 石像鬼 | — | — |
| formicid | 蚁人 | — | — |
| barachi | 蛙人 | — | — |
| vine stalker | 藤蔓行者 | — | — |
| armataur | 甲龙兽人 | — | — |
| faun | 牧神 | — | — |

**复合命名规则**：`[种族基词] + [职业/角色名]`，不使用斜杠、破折号或空格分隔。

---

*最后更新：2026-07-07 | 来源：docs/decisions.md + issues/12/glossary_and_style.md + zh-translator.md*
