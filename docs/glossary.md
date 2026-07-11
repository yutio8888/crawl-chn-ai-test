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

### 法术命名高频词根

系列词根经批次审阅后在此登记。当前已确认的稳定译法：

| 词根 | 译法 | 状态 |
|------|------|------|
| Blink | 闪烁 | ✅ 已确认（系列完整） |
| Summon | 召唤 | ✅ 已确认 |
| Dispel | 驱散 | ✅ 已确认 |

待审阅词根：Bolt、Cloud、Dart、Beam、Arrow、Touch 等——将在逐批审阅中确认并补充。
强度审查标签定义见 `docs/spell-naming-rules.md` Section 四。

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

## 十三、法术名全表

> 最终译名依据 `docs/spell-naming-rules.md` 审阅确定。
> 修订标记：✅ 保留原译，📝 修订，🆕 新增。

### Blink（9）

| English | 中文 | 备注 |
|---------|------|------|
| Blink | 闪烁 | ✅ |
| Blink Allies Away | 闪烁盟友远离 | ✅ |
| Blink Allies Encircling | 闪烁盟友包围 | ✅ |
| Blink Away | 远离闪烁 | ✅ |
| Blink Close | 接近闪烁 | ✅ |
| Blink Other | 闪烁他人 | ✅ |
| Blink Other Close | 闪烁他人接近 | ✅ |
| Blink Range | 退避闪烁 | ✅ |
| Controlled Blink | 受控闪烁 | ✅ |

### Bolt（19）

| English | 中文 | 备注 |
|---------|------|------|
| Blinkbolt | 闪烁箭 | ✅ |
| Bolt of Cold | 寒冰箭 | ✅ |
| Bolt of Devastation | 毁灭箭 | 📝 |
| Bolt of Draining | 吸取箭 | 📝 |
| Bolt of Fire | 火焰箭 | ✅ |
| Bolt of Flesh | 血肉箭 | 📝 |
| Bolt of Inaccuracy | 偏差箭矢 | ✅ |
| Bolt of Light | 光箭 | 📝 |
| Bolt of Magma | 岩浆箭 | ✅ |
| Corrosive Bolt | 腐蚀箭 | ✅ |
| Doom Bolt | 厄运箭 | 📝 |
| Electrical Bolt | 电击箭 | ✅ |
| Explosive Bolt | 爆裂弩矢 | ✅ |
| Lightning Bolt | 闪电箭 | ✅ |
| Quicksilver Bolt | 水银箭 | ✅ |
| Random Bolt | 随机箭矢 | ✅ |
| Sojourning Bolt | 旅居箭 | 📝 |
| Thunderbolt | 雷击 | ✅ |
| Venom Bolt | 毒液箭 | ✅ |

### Summon（57）

| English | 中文 | 备注 |
|---------|------|------|
| Call Canine Familiar | 呼唤犬类使魔 | 📝 |
| Call Down Damnation | 降下天谴 | 📝 |
| Call Down Lightning | 降下闪电 | ✅ |
| Call Imp | 呼唤小恶魔 | 📝 |
| Call Lost Souls | 呼唤迷失灵魂 | 📝 |
| Call Tide | 呼唤潮汐 | 📝 |
| Call of Chaos | 混沌呼唤 | 📝 |
| Demonic Horde | 恶魔大军 | ✅ |
| Hunting Call | 狩猎呼唤 | ✅ |
| Malign Gateway | 邪恶传送门 | ✅ |
| Mara Summon | 玛拉召唤 | ✅ |
| Monstrous Menagerie | 怪物动物园 | ✅ |
| Rakshasa Summon | 召唤罗刹 | ✅ |
| Recall | 召回术 | ✅ |
| Shadow Creatures | 暗影生物 | ✅ |
| Spawn Tentacles | 生成触须 | ✅ |
| Summon Air Elementals | 召唤气元素 | 📝 |
| Summon Butterflies | 召唤蝴蝶 | ✅ |
| Summon Cactus Giant | 召唤仙人掌巨人 | ✅ |
| Summon Demon | 召唤恶魔 | ✅ |
| Summon Dragon | 召唤巨龙 | ✅ |
| Summon Drakes | 召唤幼龙 | ✅ |
| Summon Earth Elementals | 召唤土元素 | 📝 |
| Summon Elemental | 召唤元素 | ✅ |
| Summon Emperor Scorpions | 召唤帝蝎 | ✅ |
| Summon Executioners | 召唤行刑者 | ✅ |
| Summon Eyeballs | 召唤眼球 | ✅ |
| Summon Fire Elementals | 召唤火元素 | 📝 |
| Summon Forest | 召唤森林 | ✅ |
| Summon Greater Demon | 召唤高级恶魔 | ✅ |
| Summon Hell Sentinel | 召唤地狱哨兵 | ✅ |
| Summon Holies | 召唤圣灵 | ✅ |
| Summon Horrible Things | 召唤恐怖之物 | ✅ |
| Summon Hydra | 召唤多头蛇 | ✅ |
| Summon Ice Beast | 召唤冰兽 | ✅ |
| Summon Illusion | 召唤幻象 | ✅ |
| Summon Iron Elementals | 召唤铁元素 | ✅ |
| Summon Mana Viper | 召唤魔力蝰蛇 | ✅ |
| Summon Minor Demon | 召唤次级恶魔 | 📝 |
| Summon Mortal Champion | 召唤凡人冠军 | ✅ |
| Summon Mushrooms | 召唤蘑菇 | ✅ |
| Summon Rakshasa | 召唤罗刹 | ✅ |
| Summon Scarabs | 召唤圣甲虫 | ✅ |
| Summon Scorpions | 召唤蝎子 | ✅ |
| Summon Seismosaurus Egg | 召唤震龙蛋 | ✅ |
| Summon Sin Beast | 召唤罪兽 | ✅ |
| Summon Small Mammal | 召唤小型哺乳动物 | ✅ |
| Summon Spiders | 召唤蜘蛛 | ✅ |
| Summon Twister | 召唤旋风 | ✅ |
| Summon Tzitzimitl | 召唤齐齐米特尔 | ✅ |
| Summon Ufetubus | 召唤乌菲图布斯 | ✅ |
| Summon Undead | 召唤亡灵 | ✅ |
| Summon Vermin | 召唤害虫 | ✅ |
| Summon Water Elementals | 召唤水元素 | ✅ |
| Summon swarm | 召唤虫群 | ✅ |
| Vampire Summon | 召唤吸血鬼 | ✅ |
| Word of Recall | 召回之言 | ✅ |

### Cloud（12）

| English | 中文 | 备注 |
|---------|------|------|
| Fire cloud | 火云 | ✅ |
| Flaming Cloud | 燃烧云 | ✅ |
| Freezing Cloud | 冰冻云 | ✅ |
| Ink Cloud | 墨云 | ✅ |
| Mephitic Cloud | 迷瘴云 | 📝 |
| Miasma cloud | 瘴气云 | ✅ |
| Noxious Cloud | 毒瘴云 | 📝 |
| Petrifying Cloud | 石化云 | ✅ |
| Poison cloud | 毒气云 | ✅ |
| Poisonous Cloud | 毒云 | ✅ |
| Spectral Cloud | 幽灵云 | ✅ |
| Steam cloud | 蒸汽云 | ✅ |

### Breath（22）

| English | 中文 | 备注 |
|---------|------|------|
| Caustic Breath | 腐蚀吐息 | ✅ |
| Chaos Breath | 混沌吐息 | ✅ |
| Cold Breath | 寒冷吐息 | ✅ |
| Combustion Breath | 燃烧吐息 | ✅ |
| Draconian Breath | 龙人吐息 | ✅ |
| Fire Breath | 火焰吐息 | ✅ |
| Galvanic Breath | 电击吐息 | ✅ |
| Glacial Breath | 冰川吐息 | ✅ |
| Golden Breath | 金龙吐息 | 🆕 |
| Holy Breath | 神圣吐息 | ✅ |
| Miasma Breath | 瘴气吐息 | ✅ |
| Mud Breath | 泥浆吐息 | ✅ |
| Noxious Breath | 毒瘴吐息 | ✅ |
| Nullifying Breath | 消魔吐息 | ✅ |
| Old serpent of hell breath | 地狱古蛇吐息 | ✅ |
| Rust Breath | 锈蚀吐息 | ✅ |
| Searing Breath | 灼热吐息 | 📝 |
| Steam Breath | 蒸汽吐息 | ✅ |
| cocytus serpent of hell breath | 冰狱蛇之吐息 | ✅ |
| dis serpent of hell breath | 铁城蛇之吐息 | ✅ |
| gehenna serpent of hell breath | 火焚地狱蛇之吐息 | ✅ |
| tartarus serpent of hell breath | 悲叹地狱蛇之吐息 | ✅ |

### Gaze（7）

| English | 中文 | 备注 |
|---------|------|------|
| Antimagic Gaze | 反魔法凝视 | ✅ |
| Confusion Gaze | 困惑凝视 | ✅ |
| Draining Gaze | 吸取凝视 | ✅ |
| Mutagenic Gaze | 变异凝视 | ✅ |
| Paralysis Gaze | 麻痹凝视 | ✅ |
| Vitrifying Gaze | 玻璃化凝视 | ✅ |
| Weakening Gaze | 虚弱凝视 | ✅ |

### Touch（2）

| English | 中文 | 备注 |
|---------|------|------|
| Agonising Touch | 剧痛之触 | ✅ |
| Confusing Touch | 困惑之触 | ✅ |

### Form（9）

| English | 中文 | 备注 |
|---------|------|------|
| Beastly Appendage | 野兽肢体 | ✅ |
| Blade Hands | 利刃之手 | ✅ |
| Dragon Form | 巨龙变形 | ✅ |
| Hydra Form | 多头蛇变形 | ✅ |
| Ice Form | 寒冰变形 | ✅ |
| Necromutation | 亡灵变形 | ✅ |
| Spider Form | 蜘蛛变形 | ✅ |
| Statue Form | 石像变形 | ✅ |
| Storm Form | 风暴变形 | ✅ |

### Possessive（35）

| English | 中文 | 备注 |
|---------|------|------|
| Alistair's Intoxication | 阿利斯泰尔之醉 | ✅ |
| Alistair's Walking Alembic | 阿利斯泰尔之行走蒸馏器 | ✅ |
| Borgnjor's Revivification | 博格尼尔之复活 | ✅ |
| Borgnjor's Vile Clutch | 博格尼尔之邪恶抓握 | ✅ |
| Brom's Barrelling Boulder | 布罗姆之碾压巨石 | ✅ |
| Cigotuvi's Degeneration | 西格图维之退化 | ✅ |
| Cigotuvi's Embrace | 西格图维之拥抱 | ✅ |
| Cigotuvi's Putrefaction | 西格图维之腐烂 | ✅ |
| Death's Door | 死亡之门 | ✅ |
| Dragon's Call | 龙之呼唤 | ✅ |
| Druid's Call | 德鲁伊召唤 | ✅ |
| Eringya's Noxious Bog | 埃林吉亚之毒沼 | 📝 |
| Eringya's Surprising Crocodile | 埃林吉亚之意外鳄鱼 | 📝 |
| Gell's Gavotte | 盖尔之加沃特 | ✅ |
| Gell's Gravitas | 盖尔之重力 | ✅ |
| Iskenderun's Battlesphere | 伊斯肯德伦之战斗球 | ✅ |
| Iskenderun's Mystic Blast | 伊斯肯德伦之神秘冲击 | ✅ |
| Leda's Liquefaction | 勒达之液化 | ✅ |
| Lee's Rapid Deconstruction | 李之快速解构 | ✅ |
| Lehudib's Crystal Spear | 勒胡迪布之水晶矛 | ✅ |
| Martyr's Knell | 殉道者之丧钟 | ✅ |
| Maxwell's Capacitive Coupling | 麦克斯韦之电容耦合 | ✅ |
| Maxwell's Portable Piledriver | 麦克斯韦之便携打桩机 | ✅ |
| Nazja's All-Purpose Tempering | 纳兹亚之通用淬炼 | ✅ |
| Nazja's Percussive Tempering | 纳兹亚之冲击淬炼 | ✅ |
| Olgreb's Toxic Radiance | 奥尔格雷布之毒辐射 | ✅ |
| Ozocubu's Armour | 奥佐库布之护甲 | ✅ |
| Ozocubu's Refrigeration | 奥佐库布之制冷 | ✅ |
| Sentinel's Mark | 哨兵印记 | ✅ |
| Sheza's Dance | 谢扎之舞 | ✅ |
| Trog's Hand | 特洛格之手 | ✅ |
| Tukima's Dance | 图基玛之舞 | ✅ |
| Vhi's Electric Charge | 维之电荷 | ✅ |
| Vhi's Electrolunge | 维之电冲 | ✅ |
| Yara's Violent Unravelling | 亚拉之猛烈解构 | ✅ |

### Projectile（7）

| English | 中文 | 备注 |
|---------|------|------|
| Magic Dart | 魔法飞弹 | ✅ |
| Mercury Arrow | 汞矢 | ✅ |
| Poison Arrow | 毒箭 | ✅ |
| Poisonous Vapours | 毒气 | ✅ |
| Pyre Arrow | 烈火箭 | 📝 |
| Slug Dart | 弹丸飞镖 | ✅ |
| Stone Arrow | 石箭 | ✅ |

### Beam（1）

| English | 中文 | 备注 |
|---------|------|------|
| Plasma Beam | 等离子光束 | ✅ |

### Shadow（13）

| English | 中文 | 备注 |
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
| Weave Shadows | 编织暗影 | ✅ |

### Dispel（2）

| English | 中文 | 备注 |
|---------|------|------|
| Dispel Undead | 驱散亡灵 | ✅ |
| Dispel Undead Range | 远程驱散亡灵 | ✅ |

### Other（316）

| English | 中文 | 备注 |
|---------|------|------|
| Abjuration | 驱逐术 | ✅ |
| Acid Ball | 酸液球 | ✅ |
| Agony | 剧痛 | 🆕 |
| Airstrike | 空袭 | ✅ |
| Anguish | 哀痛 | 📝 |
| Animate Dead | 操纵死尸 | ✅ |
| Animate Skeleton | 召唤骷髅 | ✅ |
| Apportation | 隔空取物 | ✅ |
| Arcjolt | 电弧震击 | ✅ |
| Aura of Abjuration | 驱逐灵气 | ✅ |
| Avatar Song | 化身之歌 | ✅ |
| Awaken Armour | 唤醒护甲 | ✅ |
| Awaken Earth | 唤醒大地 | ✅ |
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
| Chain Lightning | 连锁闪电 | ✅ |
| Chain of Chaos | 混沌之链 | ✅ |
| Chant Fire Storm | 咏唱火焰风暴 | ✅ |
| Charm | 魅惑 | ✅ |
| Cleansing Flame | 净化之焰 | ✅ |
| Cloud Cone | 云雾锥 | ✅ |
| Concentrate Venom | 浓缩毒液 | ✅ |
| Condensation Shield | 凝结之盾 | 🆕 |
| Confuse | 混乱 | ✅ |
| Conjure Ball Lightning | 召唤球形闪电 | ✅ |
| Conjure Flame | 召唤火焰 | ✅ |
| Conjure Living Spells | 召唤活体法术 | ✅ |
| Construct Spike Launcher | 构建尖刺发射器 | ✅ |
| Control Teleport | 传送控制 | ✅ |
| Control Undead | 亡灵控制 | ✅ |
| Control Winds | 控风术 | ✅ |
| Corona | 怪异发光球 | ✅ |
| Corpse Rot | 尸体腐烂 | ✅ |
| Corrupt | 腐化 | ✅ |
| Corrupt Body | 腐化躯体 | ✅ |
| Corrupting Pulse | 腐化脉冲 | ✅ |
| Creeping Frost | 蔓延冰霜 | ✅ |
| Crystallising Shot | 结晶射击 | ✅ |
| Cure Poison | 解毒术 | ✅ |
| Curse of Agony | 痛苦诅咒 | ✅ |
| Darkness | 黑暗术 | ✅ |
| Death Channel | 死亡通道 | ✅ |
| Death Rattle | 死亡之响 | ✅ |
| Debugging Ray | 调试射线 | ✅ |
| Deflect Missiles | 偏转飞弹 | ✅ |
| Delayed Fireball | 延迟火球 | ✅ |
| Detonation Catalyst | 引爆催化剂 | ✅ |
| Diamond Sawblades | 钻石锯片 | ✅ |
| Dig | 挖掘 | ✅ |
| Dimension Anchor | 维度锚定 | ✅ |
| Dimensional Bullseye | 维度靶心 | ✅ |
| Diminish Spells | 削弱法术 | ✅ |
| Discord | 纷乱 | 📝 |
| Disjunction | 空间分离 | ✅ |
| Dispersal | 驱散 | ✅ |
| Divine Armament | 神圣武装 | ✅ |
| Dominate Undead | 支配亡灵 | ✅ |
| Doomsaying | 宣告厄运 | ✅ |
| Drain Life | 吸取生命 | ✅ |
| Drain Magic | 汲取魔力 | ✅ |
| Dream Dust | 梦尘 | ✅ |
| Enfeeble | 虚弱术 | 📝 |
| Ensnare | 束缚 | ✅ |
| Ensorcelled Hibernation | 冬眠 | ✅ |
| Entropic Weave | 熵之编织 | ✅ |
| Ephemeral Infusion | 短暂灌注 | ✅ |
| Eruption | 喷发 | ✅ |
| Evaporate | 蒸发术 | ✅ |
| Excruciating Wounds | 剧痛之伤 | ✅ |
| Fastroot | 快速扎根 | ✅ |
| Fire Brand | 火焰烙印 | ✅ |
| Fire Storm | 火焰风暴 | ✅ |
| Fireball | 火球 | 🆕 |
| Flame Tongue | 火焰之舌 | ✅ |
| Flame Wave | 火焰波 | ✅ |
| Flash Freeze | 急冻 | ✅ |
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
| Freeze | 冰冻 | ✅ |
| Freezing Aura | 冰封灵气 | ✅ |
| Freezing Gust | 冰冻狂风 | ✅ |
| Frenzy | 狂乱术 | ✅ |
| Frozen Ramparts | 冰冻壁垒 | ✅ |
| Fugue of the Fallen | 亡灵赋格 | ✅ |
| Fulminant Prism | 爆裂棱镜 | ✅ |
| Fulsome Distillation | 精华蒸馏 | ✅ |
| Fulsome Fusillade | 猛烈连射 | ✅ |
| Funeral Dirge | 葬礼哀歌 | ✅ |
| Ghostly Fireball | 幽灵火球 | ✅ |
| Ghostly Sacrifice | 幽灵献祭 | ✅ |
| Glaciate | 冰川 | ✅ |
| Gloom | 阴郁 | ✅ |
| Goad Beasts | 激怒野兽 | ✅ |
| Grand Avatar | 大化身 | ✅ |
| Grasping Roots | 抓握根须 | ✅ |
| Grave Claw | 墓爪 | ✅ |
| Greater Ensnare | 强力束缚 | ✅ |
| Hailstorm | 冰雹风暴 | ✅ |
| Harpoon Shot | 鱼叉射击 | ✅ |
| Haste | 加速 | 🆕 |
| Haste Other | 加速他人 | ✅ |
| Haste Plants | 加速植物 | ✅ |
| Haunt | 鬼魂缠身 | ✅ |
| Heal Other | 治愈他人 | ✅ |
| Hellfire Court | 地狱火法庭 | ✅ |
| Hellfire Mortar | 地狱火迫击炮 | ✅ |
| Hoarfrost Bullet | 白霜弹 | ✅ |
| Hoarfrost Cannonade | 白霜炮击 | ✅ |
| Holy Flames | 神圣火焰 | ✅ |
| Holy Light | 圣光术 | ✅ |
| Holy word | 圣言术 | ✅ |
| Homunculus | 人造人 | ✅ |
| Hunting Cry | 狩猎战吼 | ✅ |
| Hurl Damnation | 投掷诅咒 | ✅ |
| Hurl Sludge | 投掷污泥 | ✅ |
| Hurl Torchlight | 投掷火炬之光 | ✅ |
| Iceblast | 冰爆 | ✅ |
| Ignite Poison | 点燃毒素 | ✅ |
| Ignition | 点火 | ✅ |
| Ill Omen | 凶兆 | ✅ |
| Infernal Servant | 地狱仆从 | ✅ |
| Infestation | 虫群侵扰 | ✅ |
| Infusion | 灌注术 | ✅ |
| Injury Bond | 伤害链接 | ✅ |
| Injury Mirror | 伤害反射 | ✅ |
| Inner Flame | 内焰 | ✅ |
| Insulation | 绝缘术 | ✅ |
| Invisibility | 隐身术 | ✅ |
| Invisibility Other | 隐身他人 | ✅ |
| Iron Shot | 铁弹 | ✅ |
| Irradiate | 辐射 | ✅ |
| Jinxbite | 厄运之咬 | ✅ |
| Kinetic Grapnel | 动力抓钩 | ✅ |
| Kiss of Death | 死亡之吻 | ✅ |
| Landbreaker | 裂地 | ✅ |
| Launch Bomblet | 发射小型炸弹 | ✅ |
| Launch Clockwork Bee | 发射发条蜜蜂 | ✅ |
| Launch Sporangium | 发射孢子囊 | ✅ |
| Legendary Destruction | 传奇毁灭 | ✅ |
| Lesser Beckoning | 次级召唤 | ✅ |
| Lethal Infusion | 致命灌注 | ✅ |
| Localized Ignite Poison | 局部引爆毒素 | ✅ |
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
| Mesmerise | 催眠 | 📝 |
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
| Orb of Electricity | 电光球 | ✅ |
| Ostracise | 排斥 | ✅ |
| Pain | 痛苦 | ✅ |
| Paralyse | 麻痹 | ✅ |
| Passage of Golubria | 戈卢布里亚之通道 | ✅ |
| Passwall | 穿墙术 | ✅ |
| Permafrost Eruption | 永冻爆发 | ✅ |
| Petrify | 石化 | ✅ |
| Phantom Blitz | 幻影突击 | ✅ |
| Phantom Mirror | 幻影镜 | ✅ |
| Phase Shift | 相位变换 | ✅ |
| Planar Overlay | 位面叠加 | ✅ |
| Plane Rend | 位面撕裂 | ✅ |
| Platinum Paragon | 白金典范 | ✅ |
| Poison Weapon | 淬毒武器 | ✅ |
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
| Rebounding Chill | 弹跳寒冷 | ✅ |
| Regenerate Other | 再生他人 | 📝 |
| Regeneration | 快速再生 | ✅ |
| Rending Blade | 撕裂之刃 | ✅ |
| Resonance Strike | 共鸣打击 | ✅ |
| Resurrect | 复活术 | ✅ |
| Rimeblight | 霜疫 | ✅ |
| Ring of Flames | 烈焰之环 | ✅ |
| Ring of Thunder | 雷霆之环 | ✅ |
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
| Siren Song | 塞壬之歌 | ✅ |
| Sleep | 睡眠 | ✅ |
| Sleetstrike | 冰雨打击 | ✅ |
| Slow | 减速 | 📝 |
| Smiting | 惩击 | ✅ |
| Song of Shielding | 护盾之歌 | ✅ |
| Sonic wave | 音波 | ✅ |
| Soul Splinter | 灵魂分裂 | ✅ |
| Spectral Weapon | 灵体武器 | ✅ |
| Spellspark Servitor | 法术火花仆从 | ✅ |
| Sphinx Sisters | 斯芬克斯姐妹 | ✅ |
| Spit Acid | 喷吐酸液 | ✅ |
| Spit Lava | 喷吐岩浆 | ✅ |
| Spit Poison | 喷毒 | ✅ |
| Splinterfrost Shell | 碎霜之壳 | ✅ |
| Splinterspray | 碎片喷射 | ✅ |
| Sporulate | 产孢 | ✅ |
| Starburst | 星爆 | ✅ |
| Static Discharge | 静电释放 | ✅ |
| Steam Ball | 蒸汽球 | ✅ |
| Sticks to Snakes | 棍变蛇 | ✅ |
| Sticky Flame | 黏着火焰 | ✅ |
| Still Winds | 静止风 | ✅ |
| Sting | 毒刺 | 🆕 |
| Stoke Flames | 煽动火焰 | ✅ |
| Stoneskin | 石肤术 | ✅ |
| Striking | 打击术 | ✅ |
| Strip Willpower | 剥离意志力 | ✅ |
| Stunning Burst | 眩晕爆发 | ✅ |
| Sublimation of Blood | 血液升华 | ✅ |
| Sunray | 阳光射线 | ✅ |
| Sure Blade | 精准之刃 | ✅ |
| Swiftness | 迅捷 | ✅ |
| Symbol of Torment | 折磨之符 | ✅ |
| Teleport Other | 传送他人 | ✅ |
| Teleport Self | 自我传送 | ✅ |
| Throw | 投掷 | 🆕 |
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

**汇总**：511 法术，✅ 保留 468，📝 修订 31，🆕 新增 12。

---

*最后更新：2026-07-12 | 来源：docs/decisions.md + docs/spell-naming-rules.md + issues/12/glossary_and_style.md + zh-translator.md*
