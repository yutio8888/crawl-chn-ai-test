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
| Gozag | 哥萨戈 | 运行时短名 | — |
| Gozag Ym Sagoz the Greedy | 贪婪者哥萨戈·亿·赛格斯 | 神祇长名 | — |
| Qazlal | 卡兹拉尔 | 音译 | — |
| Ru | 入 | 意译（"enter"） | — |
| Pakellas | 帕克拉斯 | 音译 | — |
| Uskayaw | 乌斯卡亚 | 音译 | — |
| Hepliaklqana | 惠普利亚卡纳 | 音译 | — |
| Ignis | 伊格尼斯 | 音译 | [D-A-051] |
| Wu Jian | 无间 | 运行时短名 | — |
| the Wu Jian Council | 无间门派 | 实体／派别长名（门派=sect） | — |
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
| 自由形式 | 伊格尼斯（Ignis）、无间门派（Wu Jian） |

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
| Form | 变形 | ⚠️ 已审阅（6 项均为已移除／TAG 34 兼容记录；暂缓术语；恢复时复审） |
| Poison / Poisonous | 毒素 / 毒 / 淬毒 | ✅ 已确认（5 项现行；另有 4 项已移除兼容；`Spit Poison → 喷吐毒液`） |
| Dispel | 驱散 | ✅ 已确认（2 项现行；指破坏维系亡灵形体的魔力） |
| Awaken | 唤醒 | ✅ 已确认（4 项现行；另有 1 项已移除兼容） |
| Forge | 锻造 | ✅ 已确认（4 项现行） |

其他词根将在逐批审阅中确认并补充。
强度审查标签定义见 `docs/spell-naming-rules.md` Section 四。

---

### 新增变形（trunk B0）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| Vision | 灵视 | form/status; vision.yaml 与 status.txt；第三眼感知施法残余；decision=D-C-095 |
| Jademantle | 玉衣 | form; jademantle.yaml 与 Jade status；玉晶覆盖上身，mantle 意象；decision=D-C-095 |
| Hypnogecko | 迷魂壁虎 | form; hypnogecko.yaml 与 Gecko status；催眠性混种壁虎；decision=D-C-095 |
| Mistmane | 雾鬃 | form/status; mistmane.yaml；头部化为雾团，保留 mane 意象；decision=D-C-095 |
| Jade | 玉晶 | Jademantle 短名/status；四元素晶体；decision=D-C-095 |
| Gecko | 壁虎 | Hypnogecko 短名/status；不译成泛称蜥蜴；decision=D-C-095 |
| vision-form | 灵视形态 | form-gen.py 从短名派生的长名；与完整形态对应；decision=D-C-095 |
| jade-form | 玉衣形态 | form-gen.py 从短名派生的长名；与完整形态对应；decision=D-C-095 |
| gecko-form | 迷魂壁虎形态 | form-gen.py 从短名派生的长名；与完整形态对应；decision=D-C-095 |
| mistmane-form | 雾鬃形态 | form-gen.py 从短名派生的长名；与完整形态对应；decision=D-C-095 |
| banyan tree | 榕树 | tree.yaml 的新具体形体描述；Tree 形态身份未改名；decision=D-C-095 |
| Surge Dmg | 元素涌流伤害 | Jademantle 数据中的伤害标签；decision=D-C-095 |
| Glimmer Dmg | 微光伤害 | Vision 数据中的伤害标签；与 glimmer 云共用词根；decision=D-C-095 |

### 魔法地脉（B0-2）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| ley line / ley lines | 地脉 | Dragon Veins spell 与四种 dragon vein 地形；指贯穿地牢的魔法能量脉络；可写“元素能量地脉／土魔法地脉”等，不将“魔法地脉”另立术语；decision=D-C-096 |


### catalog 补登记（B0-4）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| Aqua | 水灵 | form 名称／伤害标签；aqua:short_name；decision=D-C-098 |
| aqua-form | 水灵形态 | form 名称／伤害标签；aqua:long_name；decision=D-C-098 |
| Watery Grave Dmg | 水葬伤害 | form 名称／伤害标签；aqua:special_damage_name；decision=D-C-098 |
| batswarm-form | 蝠群形态 | form 名称／伤害标签；bat-swarm:long_name；decision=D-C-098 |
| bat-form | 蝙蝠形态 | form 名称／伤害标签；bat:long_name；decision=D-C-098 |
| Blade | 刀刃 | form 名称／伤害标签；blade:short_name；decision=D-C-098 |
| blade-form | 刀刃形态 | form 名称／伤害标签；blade:long_name；decision=D-C-098 |
| death-form | 死亡形态 | form 名称／伤害标签；death:long_name；decision=D-C-098 |
| dragon-form | 龙形态 | form 名称／伤害标签；dragon:long_name；decision=D-C-098 |
| Breath Dmg | 吐息伤害 | form 名称／伤害标签；dragon:special_damage_name；decision=D-C-098 |
| Eel | 电鳗 | form 名称／伤害标签；eel-hands:short_name；decision=D-C-098 |
| Jolt damage | 放电伤害 | form 名称／伤害标签；eel-hands:special_damage_name；decision=D-C-098 |
| Flux | 变形 | form 名称／伤害标签；flux:short_name；decision=D-C-098 |
| flux-form | 变形形态 | form 名称／伤害标签；flux:long_name；decision=D-C-098 |
| Contam Dmg | 辐射伤害 | form 名称／伤害标签；flux:special_damage_name；decision=D-C-098 |
| crab-form | 蟹形态 | form 名称／伤害标签；fortress-crab:long_name；decision=D-C-098 |
| fungus-form | 菌类形态 | form 名称／伤害标签；fungus:long_name；decision=D-C-098 |
| Hive | 蜂巢 | form 名称／伤害标签；hive:short_name；decision=D-C-098 |
| hive-form | 蜂巢形态 | form 名称／伤害标签；hive:long_name；decision=D-C-098 |
| jelly-form | 果冻形态 | form 名称／伤害标签；jelly:long_name；decision=D-C-098 |
| maw-form | 巨口形态 | form 名称／伤害标签；maw:long_name；decision=D-C-098 |
| Medusa | 美杜莎 | form 名称／伤害标签；medusa:short_name；decision=D-C-098 |
| medusa-form | 美杜莎形态 | form 名称／伤害标签；medusa:long_name；decision=D-C-098 |
| Pig | 猪形 | form 名称／伤害标签；pig:short_name；decision=D-C-098 |
| pig-form | 猪形态 | form 名称／伤害标签；pig:long_name；decision=D-C-098 |
| Quill | 刺毛 | form 名称／伤害标签；quill:short_name；decision=D-C-098 |
| quill-form | 刺毛形态 | form 名称／伤害标签；quill:long_name；decision=D-C-098 |
| Quill Dmg | 刺毛伤害 | form 名称／伤害标签；quill:special_damage_name；decision=D-C-098 |
| yak-form | 牦牛形态 | form 名称／伤害标签；rime-yak:long_name；decision=D-C-098 |
| Frigid Wall Dmg | 冰墙伤害 | form 名称／伤害标签；rime-yak:special_damage_name；decision=D-C-098 |
| Serpent | 蛇形 | form 名称／伤害标签；serpent:short_name；decision=D-C-098 |
| amphisbaena-form | 双头蛇形态 | form 名称／伤害标签；serpent:long_name；decision=D-C-098 |
| Slaughter | 屠戮 | form 名称／伤害标签；slaughter:short_name；decision=D-C-098 |
| slaughter-form | 屠戮形态 | form 名称／伤害标签；slaughter:long_name；decision=D-C-098 |
| sphinx-form | 斯芬克斯形态 | form 名称／伤害标签；sphinx:long_name；decision=D-C-098 |
| spider-form | 蜘蛛形态 | form 名称／伤害标签；spider:long_name；decision=D-C-098 |
| spore-form | 孢子形态 | form 名称／伤害标签；spore:long_name；decision=D-C-098 |
| Burstshroom damage | 爆裂菇伤害 | form 名称／伤害标签；spore:special_damage_name；decision=D-C-098 |
| statue-form | 石像形态 | form 名称／伤害标签；statue:long_name；decision=D-C-098 |
| Storm | 风暴 | form 名称／伤害标签；storm:short_name；decision=D-C-098 |
| storm-form | 风暴形态 | form 名称／伤害标签；storm:long_name；decision=D-C-098 |
| Blinkbolt Dmg | 闪烁箭伤害 | form 名称／伤害标签；storm:special_damage_name；decision=D-C-098 |
| Scarab | 甲虫 | form 名称／伤害标签；sun-scarab:short_name；decision=D-C-098 |
| scarab-form | 甲虫形态 | form 名称／伤害标签；sun-scarab:long_name；decision=D-C-098 |
| Flare Dmg | 耀焰伤害 | form 名称／伤害标签；sun-scarab:special_damage_name；decision=D-C-098 |
| tree-form | 树形态 | form 名称／伤害标签；tree:long_name；decision=D-C-098 |
| vampire-form | 吸血鬼形态 | form 名称／伤害标签；vampire:long_name；decision=D-C-098 |
| scroll-form | 卷轴形态 | form 名称／伤害标签；walking-scroll:long_name；decision=D-C-098 |
| Werewolf | 狼人 | form 名称／伤害标签；werewolf:short_name；decision=D-C-098 |
| werewolf-form | 狼人形态 | form 名称／伤害标签；werewolf:long_name；decision=D-C-098 |
| Wisp | 鬼火 | form 名称／伤害标签；wisp:short_name；decision=D-C-098 |
| wisp-form | 鬼火形态 | form 名称／伤害标签；wisp:long_name；decision=D-C-098 |
| Distill rate | 凝雾速率 | describe.cc / FormMistmane 的凝制雾药水速率标签；非物品名，不添每回合或百分比单位；decision=D-C-098 |

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
| curse | 诅咒 | 真正的诅咒；Ashenzari 装备绑定显示用 bound → 已束缚；decision=D-C-095 |
| soul | 灵魂 | — |
| blood | 鲜血 / 血 | 强调用"鲜血"，普通用"血" |
| Abyss | 深渊 | — |
| Dungeon | 地牢 | — |
| Arena | 竞技场 | 分支、地下城特征与世界显示文本统一；裁决 [D-A-044] |
| Gauntlet | 试炼场 | 分支、地下城特征与世界显示文本统一；裁决 [D-A-045] |
| Pandemonium | 万魔殿 | 分支、世界与传说专名；裁决 [D-A-046] |
| Pandemonium lord | 万魔殿领主 | 怪物、称号与传说实体；裁决 [D-A-046] |
| Erebora | 埃雷博拉 | 世界与固定神器传说专名；裁决 [D-A-048] |
| Ereborans | 埃雷博拉人 | Erebora 居民；裁决 [D-A-048] |
| Zonguldrok | 宗古德洛克 | 巫师实验室与相关物品传说专名；裁决 [D-A-049] |
| Orb of Zot | 佐特宝珠 / 力量宝珠 | 两种译法均可 |
| player ghost | 玩家鬼魂 | — |
| skill | 技能 | — |
| experience / XP | 经验值 | — |
| level | 等级 / 层 | 角色用"等级"，楼层用"层" |
| Evocations | 魔力释放 | 技能名；普通动词 evoke/activate 仍按语境译为“激活/使用”；decision=D-A-052 |

### 常用状态与效果

| EN | ZH | 注意事项 |
|----|----|---------|
| Might | 强效 | 状态名；近战攻击额外增加 1–10 点伤害；药水名称见 D-B-022 |
| Haste | 加速 | 行动速度 +50% |
| Berserk | 狂暴 | 近战加成但结束后减速 |
| Rampage | 冲锋 | 攻击时自动向敌人移动一步 |
| Teleport | 传送 | 位移效果 |
| Invisibility | 隐形 | 不可被看见 |
| Silence | 沉默 | 禁止施法/阅读卷轴 |

---

### 地点、地形与模式（trunk B0）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| Gulch | 污渠 | branch-data.h / portals/gulch.des / branches.txt；宝库废物与诱变污水的排水空间；decision=D-C-095 |
| gutter gulch | 排污渠 | Gulch 分支长描述；普通称呼，不用山间峡谷意象；decision=D-C-095 |
| mutagenic drain | 诱变排水口 | feature-data.h；Gulch 入口，mutagenic 与诱变辐射共用词根；decision=D-C-095；词根统一见 D-C-096 |
| purified mutation catalyst | 净化诱变催化器 | feature-data.h / features.txt；可打破的实验装置，非背包药剂；decision=D-C-095 |
| empty mutation catalyst | 空诱变催化器 | features.txt；催化器被打开后排空的状态；decision=D-C-095 |
| patch of mould | 霉菌丛 | feature-data.h / features.txt；长出可再生菌类的地表；decision=D-C-095 |
| patch of ice thorns | 冰棘丛 | feature-data.h；与 Ice Thorns 同词根；decision=D-C-095 |
| airy dragon vein | 气龙脉 | feature-data.h；龙脉地形四元素系列；decision=D-C-095 |
| earthen dragon vein | 土龙脉 | feature-data.h；同系列；decision=D-C-095 |
| fiery dragon vein | 火龙脉 | feature-data.h；同系列；decision=D-C-095 |
| icy dragon vein | 冰龙脉 | feature-data.h；同系列；decision=D-C-095 |
| assortment of trash | 杂乱垃圾 | features.txt；垃圾装饰地形新描述标题，非掉落物品；decision=D-C-095 |
| Descent | 下行 | trunk ALPHA 可见模式名；向地牢深处推进的游戏模式，英文配置身份不变；decision=D-C-095 |

### 机制与地点补登记（B0-2）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| piety | 虔诚值 | 神祇好感资源／数值及界面标签；一般叙述可简称“虔诚”，神眷作为解释性释义；弃用数值名“虔诚度”；decision=D-C-096 |
| travel exclusion | 禁区 | 自动旅行／自动探索避开的地图标记；解释性限定可写“旅行禁区／移动禁区”，不会阻止玩家手动进入；decision=D-C-096 |
| spell library | 法术库 | hints、Divine Exegesis、记忆菜单与 catalog 一致；decision=D-C-096 |
| Spider Nest | 蜘蛛巢穴 | 分支名；沿用 catalog 与 branches；不缩写为“蜘蛛巢”；decision=D-C-096 |

### 界面机制参数（B0-3 归属整理）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| encumbrance rating | 负重等级 | 护甲对施法等的阻碍参数；不是物品重量或背包负重；弃用“负重评级／负担等级”；decision=D-C-096 |

### 神器传说专名与材料（B0-3 归属整理）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| Hana | 哈娜 | unrand lore proper name；与神器所有格统一；decision=D-C-095 |
| Zmysua | 兹米苏娅 | unrand lore proper name；火龙神秘学者，保守音译；decision=D-C-095 |
| Yntzoia | 因佐娅 | unrand lore proper name；冰龙奥术师，保守音译；decision=D-C-095 |
| Fimbulwinter | 芬布尔之冬 | unrand lore proper name；与武器专名统一；decision=D-C-095 |
| Carina | 船底座 | unrand 星空语境与 ShootingStar 效果确认星座指称；不作人名音译；decision=D-C-095 |
| coolibah | 库利巴木 | unrand material name；不以未确认分类学知识增补树种；decision=D-C-095 |

### 新增随机命名组件（trunk B0）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| Apeiromancy | 无穷术 | randname.txt；Ashenzari 随机神器词缀，apeiro 词根；由 Apeoromancy 拼写修正；decision=D-C-095 |
| Apeoromancy | 无穷术 | 旧拼写仅供兼容，不另造中文名；decision=D-C-095 |
| Armchairtaur | 扶手椅人马 | rand_arm.txt；armchair 与 -taur 的组合双关，不等同 Armataur 种族；decision=D-C-095 |
| Eucatastrophe | 转危为喜 | rand_arm.txt；灾厄突然转为幸福结局的文学名词；decision=D-C-095 |
| Orthopraxy | 正行 | rand_wpn.txt；正当宗教实践，区别 Orthodoxy 教义正统；decision=D-C-095 |
| nickel | 镍 | gizmo.txt；材料／工程组件；decision=D-C-095 |
| sivanium | 西瓦尼姆 | gizmo.txt；注释指 Shazam，虚构元素音译；decision=D-C-095 |
| valorium | 瓦洛里姆 | gizmo.txt；注释指 Legion of Super-Heroes，虚构元素音译；decision=D-C-095 |
| zarnium | 扎尼姆 | gizmo.txt；注释指 Calvin and Hobbes，虚构元素音译；decision=D-C-095 |
| zigzags | 之字纹 | colourname.txt；未鉴定外观花纹；decision=D-C-095 |
| deep | 深 | colourname.txt；颜色深浅修饰，不指楼层；decision=D-C-095 |
| Absolute Zero | 绝对零度 | randbook.txt 新增冰系随机书名主题；物理概念，不声称恢复同名法术；decision=D-C-095 |
| Frazil | 冰晶 | randbook.txt；湍流水中形成的小冰晶；decision=D-C-095 |
| Frigidity | 寒冷 | randbook.txt；冰系书名主题，采用温度义；decision=D-C-095 |
| Infrigidation | 致冷 | randbook.txt；致冷过程／状态；decision=D-C-095 |
| Kibes | 冻疮 | randbook.txt；寒冷所致疮肿，非新游戏状态；decision=D-C-095 |
| Névé | 粒雪 | randbook.txt；逐渐压实的粒状积雪，保留重音英文键；decision=D-C-095 |
| Perniones | 冻疮 | randbook.txt；pernio 复数，允许随机组件近义同译；decision=D-C-095 |
| the Cold Snap | 骤寒 | randbook.txt；寒冷突然到来；decision=D-C-095 |
| the Floe | 浮冰 | randbook.txt；漂浮冰块；decision=D-C-095 |
| the Frost Giant | 霜巨人 | randbook.txt；复用现行怪物名，不另造冰系称号；decision=D-C-095 |
| the Mountaintop | 山巅 | randbook.txt；冰系书名地貌意象；decision=D-C-095 |
| the Polar Bear | 北极熊 | randbook.txt；复用现行怪物名；decision=D-C-095 |
| the Shard Shrike | 碎片伯劳 | randbook.txt；复用现行怪物名；decision=D-C-095 |
| Algific | 酷寒的 | randbook.txt；冰系书名形容词；decision=D-C-095 |
| Benumbed | 冻僵的 | randbook.txt；寒冷麻木意象；decision=D-C-095 |
| Cauldrife | 寒冷的 | randbook.txt；苏格兰语冷／令人发冷；decision=D-C-095 |
| Encoldened | 变冷的 | randbook.txt；变冷结果；decision=D-C-095 |
| Hibernal | 冬日的 | randbook.txt；冬季意象，不是冬眠；decision=D-C-095 |
| Key-cold | 冰冷无温的 | randbook.txt；如金属钥匙般冰冷／失去生命温度；decision=D-C-095 |
| Nithering | 冻瑟的 | randbook.txt；苏格兰语寒冷蜷缩／发抖；decision=D-C-095 |
| Nivean | 雪白的 | randbook.txt；雪色意象；decision=D-C-095 |
| Nixious | 雪白的 | randbook.txt；古词如雪般白，非 noxious 有毒；decision=D-C-095 |
| Ourie | 凄冷的 | randbook.txt；苏格兰语阴郁寒冷；decision=D-C-095 |
| Shrammed | 冻僵的 | randbook.txt；英国方言受冻麻木；decision=D-C-095 |
| Snowblind | 雪盲的 | randbook.txt；雪光致盲意象；decision=D-C-095 |
| Subnivean | 雪下的 | randbook.txt；积雪下方，非零下温度；decision=D-C-095 |
| Brom | 布罗姆 | randbook.txt Earth owner；复用既有法术专名；decision=D-C-095 |
| Vhi | 维 | randbook.txt Air owner；复用既有法术专名；decision=D-C-095 |
| Nazja | 纳兹亚 | randbook.txt Forgecraft owner；复用既有法术专名；decision=D-C-095 |


### catalog 补登记（B0-4）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| hatch | 逃生口 | 自动探索发现类别；沿用既有 escape hatch 的逃生口，不混作普通门；decision=D-C-098 |
| gift timeout | 神赐等待计数 | wiz-you.cc 完整提示句中的神赐等待计数；范围 0–255，不擅设单位为回合；decision=D-C-098 |
| lonesome duellist | 孤高决斗者 | bazaar.des 完整消息中的称号；沿用共享旧 duelist 消息词根，duellist 拼写变化不另立中文名；decision=D-C-098 |
| Yara's Duellist Academy | 亚拉的决斗学院 | wizlab.des 巫师实验室名；Yara 沿用亚拉；旧 Duelist 拼写只作历史兼容；decision=D-C-098 |

### 组合物品显示名说明（B0-5）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| potion of mist | 雾药水 | 完整英文名用于 TextDB／协议查找；item-name.cc 的中文显示由 mist → 雾与 potion → 药水拼接，不是完整 catalog 键；Mistmane 产物；decision=D-C-098（B0-5 查找方式对齐） |

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

### 战斗机制补登记（B0-2）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| attack of opportunity / attacks of opportunity | 借机攻击 | player invis desc 与 blind／unable to see you 怪物状态；不译为普通的措手不及伤害；decision=D-C-096 |


### catalog 补登记（B0-4）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| psychic force | 精神冲击 | fineff.cc psychokinetic_burst 的击退原因／攻击效果，不当作独立法术名；decision=D-C-098 |
| glimmering dart | 微光飞镖 | zap-data.h 灵视攻击显示名；glimmer → 微光、Dart → 飞镖；decision=D-C-098 |
| surge of energy | 能量涌流 | zap-data.h 玉衣攻击显示名；复用 Surge Dmg 的涌流词根；decision=D-C-098 |
| fiery blast | 烈火冲击 | Dragon Veins 火元素射线显示名，不改法术名龙脉（火）；decision=D-C-098 |
| frigid blast | 酷寒冲击 | Dragon Veins 冰元素射线显示名，不改法术名龙脉（冰）；decision=D-C-098 |
| blast of wind | 狂风冲击 | Dragon Veins 气元素射线显示名，不改法术名龙脉（气）；decision=D-C-098 |
| blast of rock | 岩石冲击 | Dragon Veins 土元素射线显示名，不改法术名龙脉（土）；decision=D-C-098 |

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
| air | 空气 | item display fragment; armour ego, book, staff; decision=D-B-020 |
| arbalest | 重弩 | weapon; decision=D-B-017 |
| Barding | 马铠 | armour; decision=D-B-019 |
| `armour ego full name\|infusion` | 灌注 | armour ego context key; decision=D-B-020 |
| `armour ego full name\|invisibility` | 隐形 | armour ego context key; decision=D-B-020 |
| `book full name\|Necromancy` | 死灵术 | book context key; decision=D-B-020 |
| broad axe | 阔刃斧 | weapon; decision=D-B-018 |
| dragon-coil talisman | 盘龙护符 | talisman; decision=D-B-018 |
| dire flail | 双头链枷 | weapon; decision=D-B-017 |
| falchion | 弯刃剑 | weapon; decision=D-B-018 |
| flux bauble | 变形球 | bauble; decision=D-B-020 |
| great mace | 巨型钉头锤 | weapon; decision=D-B-017 |
| magic regeneration | 法力再生 | jewellery effect; decision=D-B-020 |
| magical power | 法力强化 | jewellery effect; decision=D-B-020 |
| mayhem | 暴乱 | armour ego; decision=D-B-020 |
| moonshine | 私酒 | potion effect; decision=D-B-020 |
| morningstar | 晨星锤 | weapon; paired with eveningstar; decision=D-B-017 |
| eveningstar | 暮星锤 | weapon; paired with morningstar; decision=D-B-017 |
| lajatang | 双头杖 | weapon; decision=D-A-050 |
| old falchion | 旧弯刃剑 | legacy weapon key; decision=D-B-018 |
| partisan | 阔头枪 | weapon; decision=D-B-018 |
| `potion full name\|invisibility` | 隐形 | potion context key; decision=D-B-020 |
| `potion full name\|might` | 力量 | potion context key; melee-only effect; decision=D-B-022 |
| quarterstaff | 长棍 | weapon; decision=D-B-017 |
| quill talisman | 棘刺护符 | talisman; decision=D-B-020 |
| rampaging | 冲锋 | armour ego; decision=D-B-020 |
| `jewellery full name\|flight` | 飞行 | jewellery context key; decision=D-B-020 |
| sanguine talisman | 血色护符 | talisman; decision=D-B-018 |
| immolation | 内焰 | scroll effect; decision=D-B-020 |
| shadows | 暗影 | armour ego; decision=D-B-018 |
| triple crossbow | 三弦弩 | weapon; decision=D-B-018 |
| executioner's axe | 刽子手斧 | weapon; decision=D-B-017 |
| amulet of the Air | 空气项链 | unrand; decision=D-B-021 |
| Eiolaiphi | 埃奥莱菲 | unrand lore proper name; decision=D-B-021 |
| glaive of Prune | 梅干长柄刀 | unrand; Prune 双关沿用 D-B-021；trunk 已改为 partisan of Prune，此名保留历史兼容；decision=D-C-095 |
| morningstar "Eos" | 晨星锤"厄俄斯" | unrand; decision=D-B-017/D-B-021 |
| Rutra | 鲁特拉 | unrand lore proper name; decision=D-B-021 |
| St. Lee | 圣李 | unrand lore proper name; decision=D-B-021 |
| sword of Cerebov | 塞雷波夫之剑 | unrand; follows unique name; decision=D-B-021 |

### 武器品牌显示名称

| EN | ZH | Scope / comment |
|----|----|----------------|
| chaos | 混沌 | weapon brand verbose/terse; decision=D-B-016/D-B-020 |
| chaotic | 混沌 | weapon brand adjective; decision=D-B-016/D-B-020 |
| confusion | 混乱 | internal weapon brand verbose; decision=D-B-016/D-B-020 |
| Confuse | 混乱 | internal weapon brand terse; decision=D-B-016/D-B-020 |
| confusing | 混乱 | internal weapon brand adjective; decision=D-B-016/D-B-020 |
| `weapon brand full name\|draining` | 汲取 | weapon brand verbose context key; decision=D-B-016/D-B-020 |
| `weapon brand adjective\|draining` | 汲取 | weapon brand adjective context key; decision=D-B-016/D-B-020 |
| `weapon brand terse\|drain` | 汲取 | weapon brand terse context key; decision=D-B-016/D-B-020 |
| spectralising | 幽魂 | weapon brand verbose; decision=D-B-016/D-B-020 |
| spect | 幽魂 | weapon brand terse; decision=D-B-016/D-B-020 |
| spectral | 幽魂 | weapon brand adjective; decision=D-B-016/D-B-020 |
| vampirism | 吸血 | weapon brand verbose; decision=D-B-016/D-B-020 |
| vamp | 吸血 | weapon brand terse; decision=D-B-016/D-B-020 |
| vampiric | 吸血 | weapon brand adjective; decision=D-B-016/D-B-020 |

---

### 新增护符、药水、武器与固定神器（trunk B0）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| vision talisman | 灵视护符 | item-prop.cc；对应 Vision；decision=D-C-095 |
| jade talisman | 玉晶护符 | item-prop.cc；对应 Jademantle／Jade；decision=D-C-095 |
| gecko talisman | 壁虎护符 | item-prop.cc；对应 Hypnogecko／Gecko；decision=D-C-095 |
| mist talisman | 雾护符 | item-prop.cc；对应 Mistmane，物品名未带 mane；decision=D-C-095 |
| centipede bauble | 蜈蚣球 | items.txt；球内的蜈蚣临时化为武器；沿用 flux bauble 的球词根；decision=D-C-095 |
| `potion full name\|mist` | 雾 | 药水完整名上下文的效果片段；与雾药水同词根；decision=D-C-095 |
| athame | 仪式匕首 | item-prop.cc / items.txt；由历史兼容恢复为现行武器；decision=D-C-095 |
| detected item | 探测到的物品 | item-name.cc / items.txt；未知类别的探测物标记；decision=D-C-095 |
| partisan of Prune | 梅干阔头枪 | art-data.txt；Prune 双关沿用 D-B-021，武器采用现行 partisan 基词；decision=D-C-095 |
| amulet of Tranquility | 宁静项链 | art-data.txt；Four Winds 改名，保留 tranquility 字面意象；decision=D-C-095 |
| amulet of the Four Winds | 四方之风项链 | 旧神器名仅保留兼容；当前改用 amulet of Tranquility；decision=D-C-095 |
| swamp witch's dragon scales | 沼泽女巫龙鳞甲 | unrand.txt；保留归属，不武断确定龙鳞来源；decision=D-C-095 |
| athame "Fimbulwinter" | 仪式匕首"芬布尔之冬" | unrand.txt；末日前三年冬季的专名，武器基词复用；decision=D-C-095 |
| fire dragon occultist's scales | 火龙神秘学者鳞甲 | unrand.txt；属于火龙神秘学者 Zmysua；decision=D-C-095 |
| ice dragon arcanist's scales | 冰龙奥术师鳞甲 | unrand.txt；属于冰龙奥术师 Yntzoia；复用 arcanist；decision=D-C-095 |
| giant spiked club "Carina at Dusk" | 巨刺棍"暮色船底座" | unrand.txt 的星空颂歌、art-data.txt 的 ShootingStar 铭文与流星效果共同确认 Carina 指船底座；decision=D-C-095 |
| coolibah bardiche | 库利巴木长柄斧 | unrand.txt；整棵 coolibah tree 雕成；不无据指定树种；decision=D-C-095 |
| staff of Five Virtues | 五德杖 | unrand.txt；五种行为／能力条件；显示名不强改为底层双头杖；decision=D-C-095 |
| Stagehand's Sword | 舞台工之剑 | unrand.txt；伪装为戏剧道具的机关剑；不凭空设立人名；decision=D-C-095 |
| Hana's Scimitar | 哈娜之弯刀 | unrand.txt；雅拉弟子的所有格专名；decision=D-C-095 |
| arcane splint mail | 奥术条板甲 | unrand.txt；古老条板式护甲；splint 不误作夹板医疗器械；decision=D-C-095 |
| bone scales | 骨鳞甲 | unrand.txt；骨龙躯干制成，内部 pearl dragon 身份不改变显示名；decision=D-C-095 |
| Forgewarden's cuirass | 锻炉守卫胸甲 | unrand.txt；宗教图案胸甲；不把内部 plate 身份当显示名；decision=D-C-095 |
| ghost crab claws | 幽灵螃蟹爪 | art-data.txt / unrand.txt；复用 ghost crab 实体，保留 claws 意象；decision=D-C-095 |
| RageSunder | 怒裂 | art-data.txt；连击积蓄的强化劈砍；显示铭文／特效标签，内部属性不改名；decision=D-C-095 |
| Salvo | 齐射 | art-data.txt / status.txt；附带攻击其他目标的连续射击效果；decision=D-C-095 |
| TrickPois | 诡毒 | art-data.txt；施加负面状态附带中毒；decision=D-C-095 |
| IceDoom | 寒冰厄运 | art-data.txt；寒冷伤害累积 doom，复用厄运；decision=D-C-095 |
| FireExpos | 火焰暴露 | art-data.txt；火伤触发 exposed；decision=D-C-095 |
| FireWiz | 火焰施法辅助 | art-data.txt；提高火焰魔法成功率；decision=D-C-095 |
| IceExpos | 寒冰暴露 | art-data.txt；冷伤触发 exposed；decision=D-C-095 |
| IceWiz | 寒冰施法辅助 | art-data.txt；提高寒冰魔法成功率；decision=D-C-095 |
| ShootingStar | 流星 | art-data.txt；命中／击退产生 shooting star；非装备伤害形容词；decision=D-C-095 |
| ConstrDrown | 束缚溺水 | art-data.txt；攻击已受束缚目标时灌水入肺；decision=D-C-095 |
| ConstrBog | 束缚毒沼 | art-data.txt；攻击已受束缚目标时制造毒沼；decision=D-C-095 |
| VirtueSH | 五德格挡 | art-data.txt；五条件带来 SH；decision=D-C-095 |
| VirtueRefl | 五德反射 | art-data.txt；满足多条件带来反射；decision=D-C-095 |
| DevInvis | 诡诈隐形 | art-data.txt；devious 状态攻击触发隐形；decision=D-C-095 |
| ValArchmagi | 勇武大法师 | art-data.txt；法力充足时增强法术；decision=D-C-095 |
| ^Dim | 卸下削弱法术 | art-data.txt；卸下后的临时法术减弱；显示释义，保护内部标记；decision=D-C-095 |
| Apostate | 叛教者 | art-data.txt 铭文与稳定版称号共用 catalog 键；本次不新增上下文；decision=D-C-098（取代 D-C-097 的铭文译法） |
| mist | 雾 | catalog 共享键；art-data.txt 的 Mist 铭文／说明标签与稳定版 mist 是同一大小写不敏感的运行时身份，沿用“雾”；decision=D-C-098（取代 D-C-095 的幽魂雾译法） |
| giant spiked club | 巨刺棍 | Carina 神器所依赖的现行武器基词；沿用现行资产措辞并登记于 SSOT；decision=D-C-095 |


### 物品补登记（B0-2）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| shortbow | 短弓 | 基础武器名；catalog、hints、Hunter 与 tutorial 一致；decision=D-C-096 |
| enlightenment | 启迪 | 药水效果／状态词根；一般宗教语境如入祭坛的 enlightenment 可译“觉悟”；decision=D-C-096 |
| ambrosia | 神食 | 药水效果词根，沿用 catalog 与武僧描述；弃用该效果的“仙酿／仙酒”；普通传说中的 ambrosial nectar 按语境翻译；decision=D-C-096 |


### catalog 补登记（B0-4）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| Archery | 箭术 | 护甲 ego 铭文；item-name.cc 的 SPARM_ARCHERY 显示键；不是技能 Ranged Weapons；decision=D-C-098 |

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

### 引文歌曲题名（B0-2）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| A Whiter Shade of Pale | 《更淡的苍白》 | quotes 中普洛柯哈伦歌曲署名；反常色彩意象的项目译名，不声称官方中文曲名；decision=D-C-096 |
| One of Us Cannot Be Wrong | 《我们之中有一个不会错》 | quotes 中伦纳德·科恩歌曲署名；保留 cannot be wrong 的情态；项目译名，不声称官方中文曲名；decision=D-C-096 |

<!-- domain:species -->
## 十二、种族/物种名称

| EN | ZH | 裁决 | 复合格式 |
|----|----|------|---------|
| human | 人类 | — | 人类 + 职业 |
| deep elf | 精灵 | [D-A-008] | 精灵 + 职业（精灵剑圣、精灵湮灭者） |
| spriggan | 小精灵 | [D-A-011] | 小精灵 + 职业（小精灵气法师、小精灵狂战士） |
| naga / nagaraja | 纳迦 / 纳迦王 | [D-A-012] | 纳迦 + 职业（纳迦法师、纳迦神射手） |
| draconian | 龙人 | [D-A-007] | 颜色 + 龙人（黑龙人、绿龙人） |
| orc | 兽人 | — | 兽人 + 职业（兽人骑士、兽人大祭司） |
| tengu | 天狗 | — | 天狗 + 职业（天狗咒法师） |
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
| demigod | 半神 | — | 半神 + 职业 |
| djinni | 灯神 | — | 灯神 + 职业 |
| minotaur | 牛头人 | — | — |
| felid | 猫 | [D-A-039] | — |
| octopode | 章鱼 | [D-A-040] | — |
| gargoyle | 石像鬼 | — | — |
| formicid | 蚁人 | — | — |
| barachi | 蛙人 | — | — |
| vine stalker | 藤蔓行者 | — | — |
| armataur | 甲马人 | D-C-095 | trunk 已移除；保留 0.34.1／deprecated-armataur 兼容，不能用作 Gale Centaur 译名 |
| coglin | 齿轮地精 | — | — |
| mountain dwarf | 山矮人 | — | — |
| oni | 鬼 | D-C-095 | 0.34.1 已有的现行种族；本次不是 Ogre 改名，ogre → 食人魔继续用于怪物 |
| poltergeist | 骚灵 | [D-A-033] | — |
| revenant | 归来者 | — | — |
| faun | 牧神 | — | — |

**复合命名规则**：`[种族基词] + [职业/角色名]`，不使用斜杠、破折号或空格分隔。

生产数据中的种族形容词形态沿用中文基词：`Barachian → 蛙人`、
`Dwarven → 矮人`、`Elven → 精灵`、`Ghoulish → 食尸鬼`、
`Merfolkian → 人鱼`、`Meteoric → 流星`、`Trollish → 巨魔`。

---

### 新种族（trunk B0）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| Gale Centaur | 疾风半人马 | species; gale-centaur.yaml；保留 centaur 基词与 gale 风意象；decision=D-C-095 |
| Foal | 小马驹 | Gale Centaur 幼体称呼；child_name，非独立种族；decision=D-C-095 |
| Equine | 马形 | Gale Centaur adjective；按句法可用“马的”，不替代种族名；decision=D-C-095 |


### catalog 补登记（B0-4）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| Orcataur | 兽人马 | gale-centaur.yaml 的 Beogh 称呼 orc_name；兽人与 -taur 的组合；不替换正式种族名；decision=D-C-098 |

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
| Evocations | 魔力释放 | skill; source=source.txt; decision=D-A-052 |
| Shapeshifting | 变形术 | skill; source=source.txt; decision=D-C-001 |

### 技能参数补登记（B0-2）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| aptitude | 资质 | 种族／技能训练效率参数；弃用该参数的“天赋／能力倾向”；普通人物魔法天赋不受影响；decision=D-C-096 |


### catalog 补登记（B0-4）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| base skill target | 基础技能目标 | skill-menu.cc 完整提示句中的参数术语；指不计加成的原始技能训练目标，不要求存在同名独立 catalog 键；decision=D-C-098 |

<!-- domain:status -->
## 十四、状态与效果

| EN | ZH | Scope / comment |
|----|----|----------------|
| Haste | 加速 | status; source=status.txt |
| Invisibility | 隐形 | status; source=status.txt |
| Might | 强效 | status; source=status.txt |
| Repel Missiles | 排斥飞弹 | spell and status; source=source.txt; decision=D-A-047 |
| `status\|Blood` | 血甲 | defensive sanguine armour status; decision=D-D-005 |
| DUR_SANGUINE_ARMOUR | 血甲 | internal duration identity; decision=D-D-005 |
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

### 新增云与状态（trunk B0）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| glimmer | 微光 | cloud.cc / clouds.txt；法术残余，可被灵视形态利用；decision=D-C-095 |
| faint frost | 淡霜 | cloud.cc；轻微浮冰晶体，不误示强伤害；decision=D-C-095 |
| frost cloud | 霜云 | clouds.txt；faint frost 的描述标题，非新独立云身份；decision=D-C-095 |
| blinding haze | 致盲浓雾 | cloud.cc / clouds.txt；逗留其中会被致盲；decision=D-C-095 |
| Crystals | 晶体 | status.cc / status.txt；玉衣充能指示；decision=D-C-095 |
| Indom | 刚毅 | status.txt；按生命上限快速恢复一定生命；不表示无敌；decision=D-C-095 |
| Tailwind | 顺风 | status.txt；下一次冲锋移动不耗时；decision=D-C-095 |
| Exegesis | 释经 | status.txt；可低成本再次施放最近释经法术；decision=D-C-095 |
| Vapour | 汽雾 | status.txt；饮药后待喷出的气体混合物；decision=D-C-095 |
| Insubst | 虚体 | status.txt；无实体身体，免疫束缚等，非幽灵种族；decision=D-C-095 |
| insubstantial | 虚体 | duration-data.h；与 Insubst 同词根；decision=D-C-095 |
| -Swift | -迅捷 | 行动加速后的移动迟缓；对齐稳定版共享 catalog 标签，保留负号；decision=D-C-098（取代 D-C-095 的缓步译法） |
| -Sirocco | 灼热风冷却 | status.txt；移动会延后再次施放；decision=D-C-095 |
| -Tail | -尾巴 | status.txt；状态灯对齐实际显示，保留负号；探索后尾巴才能长回；decision=D-C-098（取代 D-C-095 的断尾待生译法） |
| -Jolt | -电冲 | status.txt；状态灯对齐共享 catalog 标签，保留负号；完全恢复生命后才能再次满强度放电；decision=D-C-098（取代 D-C-095 的放电冷却译法） |
| deflecting missiles | 偏转飞弹 | monstatus.txt；替代旧 repelling missiles 标签，复用 Deflect Missiles；decision=D-C-095 |
| divinely shielded | 神圣护盾保护 | monstatus.txt；受神圣护盾保护；decision=D-C-095 |
| exposed | 暴露 | monstatus.txt；更易遭非攻击伤害且意志降低；不译为防具破碎；decision=D-C-095 |
| out of phase | 相位偏移 | monstatus.txt；相位变换效果，区别单纯隐形；decision=D-C-095 |
| stampeding | 奔踏中 | monstatus.txt；与 Stampede 同词根；decision=D-C-095 |

### 状态、云与诱变词根补登记（B0-2）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| dazed | 眩晕 | catalog 状态与催眠相关描述；该状态叙述的 daze／dazing 同根；不全局替换其他机制的“震慑”或一般“恍惚”；decision=D-C-096 |
| barbs | 倒刺 | 造成移动伤害的刺及状态词根；复用 Throw Barbs，不混作普通尖刺；decision=D-C-096 |
| `status\|Barbs` | 尖刺 | 玩家状态的稳定版共享上下文键；普通 barbs 仍用倒刺；decision=D-C-098（取代 D-C-096 的此状态标签译法） |
| `status\|ambrosia-drunk` | 仙酒醉 | 药水作用状态的稳定版共享上下文键；ambrosia 药水仍用神食；decision=D-C-098（取代 D-C-096 的神食酣醉标签译法） |
| noxious fumes | 毒烟 | 造成混乱、可被毒抗抵御的云类型；不同于 poison gas 毒气；命名及明确指称该云的正文同根；decision=D-C-096 |
| mutagenic | 诱变 | 描述使生物发生变异的作用；固定法术名 Mutagenic Gaze → 变异凝视为保留例外，不扩展到其正文；decision=D-C-096 |
| mutagenic energy / mutagenic energies | 诱变能量 | 普通能量描述，包括 Mutagenic Gaze 法术正文；弃用“变异能量／突变能量”；decision=D-C-096 |
| mutagenic power | 诱变力量 | 四肢增强效果的力量；区别发生的变异（mutation）；decision=D-C-096 |
| mutagenic glow | 诱变光芒 | 魔法污染的发光描述；与 mutagenic radiation 同词根；decision=D-C-096 |
| mutagenic radiation | 诱变辐射 | 复用 Contamination 既有译法；decision=D-C-096 |
| mutagenic fog | 诱变雾气 | 云类型及鬃毛药水云、怪物状态描述；弃用“致变雾气／变异雾气”；decision=D-C-096 |
| mutagenic serum | 诱变血清 | 净化诱变催化器正文；沿用 features 既有译法；decision=D-C-096 |

<!-- domain:backgrounds -->
## 十五、角色背景

| EN | ZH | Scope / comment |
|----|----|----------------|
| Air Elementalist | 气元素使 | background; source=backgrounds.txt |
| Artificer | 技师 | background; source=backgrounds.txt |
| Berserker | 狂战士 | background; source=backgrounds.txt |
| Brigand | 强盗 | background; source=backgrounds.txt |
| Chaos Knight | 混沌骑士 | background; source=backgrounds.txt |
| Cinder Acolyte | 灰烬侍僧 | background; source=backgrounds.txt |
| Conjurer | 咒法师 | background; source=backgrounds.txt |
| Delver | 挖掘者 | background; source=backgrounds.txt |
| Earth Elementalist | 土元素使 | background; source=backgrounds.txt |
| Enchanter | 惑控师 | background; source=backgrounds.txt |
| Fighter | 战士 | background; source=backgrounds.txt |
| Fire Elementalist | 火元素使 | background; source=backgrounds.txt |
| Gladiator | 角斗士 | background; source=backgrounds.txt |
| Hedge Wizard | 杂学巫师 | background; source=backgrounds.txt |
| Hexslinger | 诅咒射手 | background; source=backgrounds.txt |
| Hunter | 猎手 | background; source=backgrounds.txt |
| Ice Elementalist | 冰元素使 | background; source=backgrounds.txt |
| Monk | 武僧 | background; source=backgrounds.txt |
| Necromancer | 死灵法师 | background; source=backgrounds.txt |
| Reaver | 掠夺者 | background; source=backgrounds.txt |
| Summoner | 召唤师 | background; source=backgrounds.txt |
| Shapeshifter | 变形人 | background; source=backgrounds.txt |
| Alchemist | 炼金术士 | background; source=backgrounds.txt |
| Wanderer | 漫游者 | background; source=backgrounds.txt |
| Warper | 折跃者 | background; source=backgrounds.txt |
| Forgewright | 锻造师 | background; source=backgrounds.txt |

### 新增背景与分组（trunk B0）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| Mystic | 秘术师 | background; mystic.yaml；元素法术与变形并用，不与学派名“神秘”混同；decision=D-C-095 |
| Stalker | 潜行者 | background; stalker.yaml；潜行、诱敌与变形；旧同名职业仅保留身份兼容；decision=D-C-095 |
| Metamorph | 变形者 | job group; util/job-gen.py；总类，区别职业 Shapeshifter → 变形人；decision=D-C-095 |

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

### 神祇能力与束缚体系（trunk B0）

Ashenzari 装备绑定统一使用“束缚”。物品长名前缀 **bound → 束缚**，短名括注 **(bound) → （已束缚）**，菜单／费用用“已束缚物品”，动作用“束缚／解除束缚”，仪式意象用“枷锁”。后续 defaults 中文正则须覆盖对应显示形式；本阶段只定术语，不修改正则或资产。`curse → 诅咒`、`bound soul → 缚魂` 与 `Constriction → 束缚` 的各自语境保持有效；`cursed()`、CURSE 枚举、英文协议／查找键不随显示文案改名。

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| Ritual of Binding | 束缚仪式 | ability.cc / ability.txt；把已装备物品束缚于自身；decision=D-C-095 |
| Shatter the Chains | 打碎枷锁 | ability.cc；沿用既有措辞，摧毁物品才能解除束缚；decision=D-C-095 |
| Shatter The Chains | 打碎枷锁 | ability.txt 的大小写变体；与能力名同译；decision=D-C-095 |
| bind | 束缚 | Ashenzari 装备语境；bind an item → 束缚物品；decision=D-C-095 |
| binding | 束缚 | Ashenzari 仪式／装备语境；binding sigil 属另一战斗机制，不从本项推导改名；decision=D-C-095 |
| bound | 已束缚 / 束缚 | Ashenzari 装备状态／菜单；物品名前缀的共享 catalog 键（bound 后含空格）使用“束缚”，括注使用“（已束缚）”；decision=D-C-095；前缀由 D-C-098 对齐 |
| Bound item | 绑定物品 | describe-god.cc 神祇详情页的独立共享 catalog 标签；菜单／费用的完整键仍用已束缚物品；decision=D-C-098（限定 D-C-095 的用词范围） |
| unbind | 解除束缚 | Ashenzari 操作提示；仍需完整说明摧毁物品后果；decision=D-C-095 |
| unbound | 未束缚 | Ashenzari 装备状态；与已束缚成对；decision=D-C-095 |
| chains | 枷锁 | Ashenzari 仪式意象；chain yourself → 以枷锁束缚自己；decision=D-C-095 |
| cursed | 诅咒的 | 稳定版共享 catalog 键，旧版装备前缀保留兼容；trunk Ashenzari 装备绑定状态改用 bound；真正诅咒仍用诅咒；decision=D-C-098（取代 D-C-095 的此键译法） |
| Pacify | 安抚 | ability.txt；使敌对生物中立并离开，不再用治疗能力名表达；decision=D-C-095 |
| Divine Alms | 神圣施济 | ability.txt；医治受苦友军，alms 保留施济语义；decision=D-C-095 |
| Aura of Vigour | 活力光环 | ability.txt；提升自己生命／法力上限，并赋予邻近友军活力；decision=D-C-095 |
| Divine Shield | 神圣护盾 | 既有能力；新增友军应用也沿用同词根；decision=D-C-095 |
| divine shield | 神圣护盾 | 怪物获益与战斗消息；区别普通 shield → 盾牌；decision=D-C-095 |
| Divine Vigour | 神圣活力 | 旧能力名保留 0.34.1 兼容；trunk 菜单用 Aura of Vigour；decision=D-C-095 |
| divine vigour | 神圣活力 | monster enchant/message；Aura of Vigour 的效果名；decision=D-C-095 |
| Divine Exegesis | 神圣释经 | 既有能力，登记词根以支持新增 Repeat Exegesis；decision=D-C-095 |
| Repeat Exegesis | 重复释经 | ability.cc；对齐稳定版共享 catalog 键，重复最近的神圣释经法术；decision=D-C-098（取代 D-C-095 的此键译法） |
| Elementalist | 元素师 | 与 elementalist 大小写不敏感的共享 catalog 身份同译；完整能力名、职业名各依其独立键；decision=D-C-098（取代 D-C-095 的此键译法） |
| Battlemage | 战斗法师 | 旧先祖类型保留兼容；一般角色词不受替代；decision=D-C-095 |
| Curse Item | 诅咒物品 | 旧能力标题保留兼容；当前装备仪式用 Ritual of Binding；decision=D-C-095 |
| Ancestor Life: Elementalist | 先祖生涯：元素师 | ability.cc；先祖类型 Elementalist，非新玩家背景；decision=D-C-095 |

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

### 新增变异与形态特征（trunk B0）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| spark swarm | 火花群 | 对齐稳定版共享 catalog 名称；火星与余烬环绕并照亮受火／电伤害的敌人，现象描述不作为名称；decision=D-C-098（取代 D-C-095 的火星群译法） |
| stampede | 奔踏 | mutation-data.h；Gale Centaur 固有特征；与法术、状态同词根；decision=D-C-095 |
| North Wind's embodiment | 北风化身 | mutation-data.h；四风强化系列；decision=D-C-095 |
| South Wind's embodiment | 南风化身 | mutation-data.h；同系列；decision=D-C-095 |
| West Wind's embodiment | 西风化身 | mutation-data.h；同系列；decision=D-C-095 |
| East Wind's embodiment | 东风化身 | mutation-data.h；同系列；decision=D-C-095 |
| autotomy | 自断尾 | hypnogecko.yaml / mutations.txt；受重伤后脱尾诱敌；decision=D-C-095 |
| elemental crystals | 元素晶体 | jademantle.yaml；四元素晶体充能；decision=D-C-095 |
| glimmercast | 微光施放 | vision.yaml；把施法残余转为攻击；decision=D-C-095 |
| gather mist | 聚雾 | mistmane.yaml；探索时制造雾药水；decision=D-C-095 |
| potion clouds | 药水云雾 | mistmane.yaml；喝药水准备喷出有害云；decision=D-C-095 |
| fleshless physiology | 无肉生理 | mutations.txt；石像鬼特征分类，不误示亡灵；decision=D-C-095 |
| plant physiology | 植物生理 | mutations.txt；树形态特征分类；decision=D-C-095 |


### catalog 补登记（B0-4）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| water reaching | 水体延伸 | form 伪变异／特征标签；aqua:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| water splatter | 水花飞溅 | form 伪变异／特征标签；aqua:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| steam response | 遇火生汽 | form 伪变异／特征标签；aqua:badmuts；不声称是可遗传突变；decision=D-C-098 |
| freeze response | 遇冷冻结 | form 伪变异／特征标签；aqua:badmuts；不声称是可遗传突变；decision=D-C-098 |
| extremely fast | 极快 | form 伪变异／特征标签；bat-swarm:fakemuts, bat:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| vampire fangs | 吸血鬼獠牙 | form 伪变异／特征标签；bat-swarm:fakemuts, vampire:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| bloodcurse | 血咒 | form 伪变异／特征标签；bat-swarm:fakemuts, vampire:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| torment resistance 1 | 折磨抗性1 | form 伪变异／特征标签；bat-swarm:fakemuts, statue:fakemuts, vampire:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| very stealthy | 潜行极佳 | form 伪变异／特征标签；bat-swarm:fakemuts, vampire:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| weak attacks | 攻击虚弱 | form 伪变异／特征标签；bat-swarm:badmuts, bat:badmuts, flux:badmuts, pig:fakemuts, walking-scroll:badmuts；不声称是可遗传突变；decision=D-C-098 |
| blade aux | 刀刃辅助攻击 | form 伪变异／特征标签；blade:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| blade parry | 刀刃格挡 | form 伪变异／特征标签；blade:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| vile attack | 恶毒攻击 | form 伪变异／特征标签；death:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| torment immunity | 折磨免疫 | form 伪变异／特征标签；death:fakemuts, fungus:fakemuts, slaughter:fakemuts, tree:fakemuts, wisp:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| dragon claw | 龙爪 | form 伪变异／特征标签；dragon:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| dragon scales | 龙鳞 | form 伪变异／特征标签；dragon:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| eel punch | 电鳗拳击 | form 伪变异／特征标签；eel-hands:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| eeljolt | 电鳗放电 | form 伪变异／特征标签；eel-hands:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| contaminating | 污染攻击 | form 伪变异／特征标签；flux:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| armoured shell | 坚甲 | form 伪变异／特征标签；fortress-crab:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| slow movement | 移动缓慢 | form 伪变异／特征标签；fortress-crab:badmuts；不声称是可遗传突变；decision=D-C-098 |
| terrified | 惊恐 | form 伪变异／特征标签；fungus:badmuts；不声称是可遗传突变；decision=D-C-098 |
| hive swarm | 蜂群护体 | form 伪变异／特征标签；hive:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| hive regen | 蜂巢再生 | form 伪变异／特征标签；hive:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| stealthy | 善于潜行 | form 伪变异／特征标签；hypnogecko:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| acid body | 酸性身体 | form 伪变异／特征标签；jelly:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| amorphous state | 无定形 | form 伪变异／特征标签；jelly:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| acidic touch | 酸蚀触击 | form 伪变异／特征标签；jelly:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| heavily diminished spells | 法术严重削弱 | form 伪变异／特征标签；jelly:badmuts；不声称是可遗传突变；decision=D-C-098 |
| maw attack | 巨口攻击 | form 伪变异／特征标签；maw:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| devouring maw | 吞噬巨口 | form 伪变异／特征标签；maw:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| growling stomach | 胃部咆哮 | form 伪变异／特征标签；maw:badmuts；不声称是可遗传突变；decision=D-C-098 |
| low body AC | 躯干护甲低 | form 伪变异／特征标签；maw:badmuts；不声称是可遗传突变；decision=D-C-098 |
| stinger hair | 毒须鬃发 | form 伪变异／特征标签；medusa:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| lithotoxin | 石化毒素 | form 伪变异／特征标签；medusa:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| slow casting | 施法缓慢 | form 伪变异／特征标签；mistmane:badmuts；不声称是可遗传突变；decision=D-C-098 |
| quills | 刺毛护体 | form 伪变异／特征标签；quill:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| frigid aura | 酷寒灵光 | form 伪变异／特征标签；rime-yak:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| ice wizardry | 寒冰施法辅助 | form 伪变异／特征标签；rime-yak:fakemuts；不声称是可遗传突变；与 IceWiz 同根，降低施法难度，不表示法术威力增强；catalog 待负责译者修订；decision=D-C-098 |
| two hats | 双帽 | form 伪变异／特征标签；serpent:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| damage resistance | 伤害抗性 | form 伪变异／特征标签；slaughter:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| doubled heal-on-kills | 杀敌治疗加倍 | form 伪变异／特征标签；slaughter:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| unshakeable will | 意志不可动摇 | form 伪变异／特征标签；slaughter:fakemuts；不声称是可遗传突变；保留 unshakeable 的绝对强度，不弱化为普通坚韧；catalog 待负责译者修订；decision=D-C-098 |
| demonic bargain | 恶魔契约 | form 伪变异／特征标签；slaughter:badmuts；不声称是可遗传突变；decision=D-C-098 |
| airstrike attack | 空袭攻击 | form 伪变异／特征标签；sphinx:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| hex mastery | 诅咒精通 | form 伪变异／特征标签；sphinx:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| riddle compulsion | 谜语冲动 | form 伪变异／特征标签；sphinx:badmuts；不声称是可遗传突变；decision=D-C-098 |
| ensnaring attack | 蛛网攻击 | form 伪变异／特征标签；spider:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| jumping | 跳跃 | form 伪变异／特征标签；spider:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| poison vulnerability | 毒素弱点 | form 伪变异／特征标签；spider:badmuts, sun-scarab:badmuts；不声称是可遗传突变；decision=D-C-098 |
| weakening spores | 虚弱孢子 | form 伪变异／特征标签；spore:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| electrical cleaving | 电流横扫 | form 伪变异／特征标签；storm:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| evasive | 善于闪避 | form 伪变异／特征标签；storm:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| sun companion | 太阳伙伴 | form 伪变异／特征标签；sun-scarab:fakemuts；不声称是可遗传突变；指随身的太阳热球／余烬伙伴，companion 不增加伴侣的情爱关系；catalog 待负责译者修订；decision=D-C-098 |
| searing attack | 灼热攻击 | form 伪变异／特征标签；sun-scarab:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| fire wizardry | 火焰施法辅助 | form 伪变异／特征标签；sun-scarab:fakemuts；不声称是可遗传突变；与 FireWiz 同根，降低施法难度，不表示法术威力增强；catalog 待负责译者修订；decision=D-C-098 |
| resilient | 坚韧 | form 伪变异／特征标签；tree:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| bat form | 蝠群变形 | form 伪变异／特征标签；vampire:fakemuts；不声称是可遗传突变；vampire fakemut 的说明明确变成一群蝙蝠，复用 batswarm-form 的蝠群词根；catalog 待负责译者修订；decision=D-C-098 |
| hypnotic gaze | 催眠凝视 | form 伪变异／特征标签；vampire:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| magic absorption | 吸收魔法 | form 伪变异／特征标签；walking-scroll:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| novice magic | 新手魔法 | form 伪变异／特征标签；walking-scroll:badmuts；不声称是可遗传突变；decision=D-C-098 |
| werefury | 狼人狂怒 | form 伪变异／特征标签；werewolf:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| werehowl | 狼人嚎叫 | form 伪变异／特征标签；werewolf:fakemuts；不声称是可遗传突变；decision=D-C-098 |
| highly resistant | 高抗性 | form 伪变异／特征标签；wisp:fakemuts；不声称是可遗传突变；表示多种伤害抗性较高，不套用 Might 的“强效”词根；catalog 待负责译者修订；decision=D-C-098 |

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
| armataur | 甲马人 | monster; trunk 已移除，保留历史兼容；decision=D-C-095 |
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

### 新增怪物与先祖类型（trunk B0）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| elementalist | 元素师 | ancestor-elementalist.yaml；先祖由 Battlemage 改为 Elementalist；对齐稳定版共享 catalog 身份，不改独立职业／完整能力名键；decision=D-C-098（取代 D-C-095 的此键译法） |
| abyssal acolyte | 深渊侍僧 | abyssal-acolyte.yaml；复用 Abyss 与 acolyte；decision=D-C-095 |
| herald of the Abyss | 深渊先驱 | herald-of-the-abyss.yaml；深渊来使，不凭空加圣性；decision=D-C-095 |
| airy jade | 气玉晶 | jade-crystal-air.yaml；Jademantle 的气元素晶体；decision=D-C-095 |
| earthen jade | 土玉晶 | jade-crystal-earth.yaml；同系列；decision=D-C-095 |
| fiery jade | 火玉晶 | jade-crystal-fire.yaml；同系列；decision=D-C-095 |
| icy jade | 冰玉晶 | jade-crystal-ice.yaml；同系列；decision=D-C-095 |
| assassin centipede | 刺客蜈蚣 | assassin-centipede.yaml / items.txt；同名临时武器复用；decision=D-C-095 |
| hypnotail | 迷魂尾 | hypnotail.yaml；迷魂壁虎脱落的诱敌尾巴；decision=D-C-095 |
| fungal shambler | 蹒跚菌怪 | monsters.txt；吞噬活体后游荡的寄生菌；decision=D-C-095 |
| glowmurk ghast | 浊光怨灵 | monsters.txt；闪烁的溺亡幽影，接触后消散；decision=D-C-095 |
| mongrel wurm | 杂种蠕龙 | monsters.txt；幼龙等生物的蛇形杂交体，不误作普通蠕虫；decision=D-C-095 |
| roaming sludgefish | 游荡泥鱼 | roaming-sludgefish.yaml；对齐稳定版共享 catalog 键；decision=D-C-098（取代 D-C-095 的此键译法） |
| rusted inspector | 锈蚀监察者 | monsters.txt；失修、抑制魔法的金属监控构装体；decision=D-C-095 |
| scrapshell chimera | 废铁壳奇美拉 | monsters.txt；水生血肉与废铁甲壳融合；decision=D-C-095 |
| sewage sovereign | 污水君主 | monsters.txt；统治污水领域的巨型变异猪；decision=D-C-095 |
| stack of scrap | 废铁堆 | stack-of-scrap.yaml / monsters.txt；金属废料堆叠构装体；decision=D-C-095 |
| telencephalon | 端脑 | monsters.txt；魔法晶体与变异脑组织构成，保留原名解剖学术语；decision=D-C-095 |
| lurker | 潜伏者 | mon-lurk.cc；未显现而等待触发的怪物机制类，非新增物种；区别 Stalker；decision=D-C-095 |
| ghost crab | 幽灵螃蟹 | 新增神器命名所依赖的现行怪物基词；沿用现行资产措辞并登记于 SSOT；decision=D-C-095 |
| occultist | 神秘学者 | 新增火龙鳞甲所依赖的现行角色基词；沿用现行资产措辞并登记于 SSOT；decision=D-C-095 |

### 描述专名补登记（B0-2）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| fenstrider witch | 沼行女巫 | 怪物名及幽灵螃蟹爪的制作群体；沿用 catalog，不混作 swamp witch 沼泽女巫；decision=D-C-096 |
| West Wind | 西风 | Zephyr 传说中人格化的西风；与 West Wind's embodiment → 西风化身共用词根；decision=D-C-096 |


### catalog 补登记（B0-4）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| burstshroom | 爆裂菇 | 怪物／召唤构造实体名；沿用 catalog；spike launcher 复用 Construct Spike Launcher 的词根；decision=D-C-098 |
| spike launcher | 尖刺发射器 | 怪物／召唤构造实体名；沿用 catalog；spike launcher 复用 Construct Spike Launcher 的词根；decision=D-C-098 |

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

### 新增独特怪物（trunk B0）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| Goji | 戈吉 | goji.yaml / goji_unmounted.yaml；骑乘与落地两身份共用地精专名；decision=D-C-095 |


### 新增随机怪物专名（trunk B0）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| Desdemona | 苔丝狄蒙娜 | monname.txt；怪物随机人名，采用既有文学专名惯例；decision=D-C-095 |


### catalog 补登记（B0-4）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| Royal Jelly | 果冻王 | mon-util.cc 果冻王的实体显示名；沿用 catalog 与既有 jelly 词根；decision=D-C-098 |

<!-- domain:monster-titles -->
## 二十、独特怪物称号（全部 86 项，Issue #71）

| EN | ZH | Scope / comment |
|----|----|----------------|
| Agnes title | 流浪者艾格尼丝 | monster-title; source=database/zh/montitle.txt |
| Aizul title | 疏忽的守卫艾祖尔 | monster-title; source=database/zh/montitle.txt |
| Amaemon title | 恶魔投毒者亚麦蒙 | monster-title; source=database/zh/montitle.txt |
| Antaeus title | 安泰俄斯，悲叹河的守卫 | monster-title; source=database/zh/montitle.txt |
| Arachne title | 被放逐的阿拉克涅 | monster-title; source=database/zh/montitle.txt |
| Asmodeus title | 阿斯摩蒂斯，欣嫩谷的王子 | monster-title; source=database/zh/montitle.txt |
| Asterion title | 堕落之王阿斯忒里翁 | monster-title; source=database/zh/montitle.txt |
| Azrael title | 无边烈焰阿兹瑞尔 | monster-title; source=database/zh/montitle.txt |
| Bai Suzhen title | 白素贞，白蛇夫人 | monster-title; source=database/zh/montitle.txt |
| Boris title | 鲍里斯，生死大师 | monster-title; source=database/zh/montitle.txt |
| Cassandra title | 注定毁灭的先知卡珊德拉 | monster-title; source=database/zh/montitle.txt |
| Cerebov title | 塞雷波夫，火与钢之恶魔领主 | monster-title; source=database/zh/montitle.txt |
| Chuck title | 收集者查克 | monster-title; source=database/zh/montitle.txt |
| Crazy Yiuf title | 开悟者疯狂的尤夫 | monster-title; source=database/zh/montitle.txt |
| Dispater title | 迪斯帕特，铁城领主 | monster-title; source=database/zh/montitle.txt |
| Dissolution title | 分解者，吉瓦的高级祭司 | monster-title; source=database/zh/montitle.txt |
| Donald title | 冒险者唐纳德 | monster-title; source=database/zh/montitle.txt |
| Dowan title | 多万，杜维莎的哥哥 | monster-title; source=database/zh/montitle.txt |
| Duvessa title | 杜维莎，多万的妹妹 | monster-title; source=database/zh/montitle.txt |
| Edmund title | 年少者埃德蒙 | monster-title; source=database/zh/montitle.txt |
| Ereshkigal title | 埃列什基伽勒，塔尔塔罗斯的女王 | monster-title; source=database/zh/montitle.txt |
| Erica title | 暴躁的艾丽卡 | monster-title; source=database/zh/montitle.txt |
| Erolcha title | 狡猾的伊罗查 | monster-title; source=database/zh/montitle.txt |
| Eustachio title | 奇伟的尤斯塔奇奥 | monster-title; source=database/zh/montitle.txt |
| Fannar title | 冷酷的凡纳尔 | monster-title; source=database/zh/montitle.txt |
| Frances title | 弗朗西斯，万魔殿女公爵 | monster-title; source=database/zh/montitle.txt |
| Frederick title | 完美的弗雷德里克 | monster-title; source=database/zh/montitle.txt |
| Gastronok title | 沉重的加斯特罗诺克 | monster-title; source=database/zh/montitle.txt |
| Geryon title | 格律翁，地狱的守门人 | monster-title; source=database/zh/montitle.txt |
| Gloorx Vloq title | 格洛克斯·弗洛克，暗之恶魔领主 | monster-title; source=database/zh/montitle.txt |
| Grum title | 猎人格拉姆 | monster-title; source=database/zh/montitle.txt |
| Grunn title | 被惩罚的格伦 | monster-title; source=database/zh/montitle.txt |
| Harold title | 饱经风霜的哈罗德 | monster-title; source=database/zh/montitle.txt |
| Ignacio title | 伊格纳西奥，剧痛大师 | monster-title; source=database/zh/montitle.txt |
| Ijyb title | 爱钻研的艾吉布 | monster-title; source=database/zh/montitle.txt |
| Ilsuiw title | 伊尔苏伊，潮汐女巫 | monster-title; source=database/zh/montitle.txt |
| Jeremiah title | 耶利米，蛙人神游者 | monster-title; source=database/zh/montitle.txt |
| Jessica title | 见习女术师杰西卡 | monster-title; source=database/zh/montitle.txt |
| Jorgrun title | 撼地者约格伦 | monster-title; source=database/zh/montitle.txt |
| Jory title | 血腥伯爵乔里 | monster-title; source=database/zh/montitle.txt |
| Joseph title | 约瑟夫，雇佣兵 | monster-title; source=database/zh/montitle.txt |
| Josephina title | 冰巫妖约瑟菲娜 | monster-title; source=database/zh/montitle.txt |
| Josephine title | 腐朽的死灵法师约瑟芬 | monster-title; source=database/zh/montitle.txt |
| Khufu title | 不朽的法老胡夫 | monster-title; source=database/zh/montitle.txt |
| Kirke title | 喀耳刻，神话编织者 | monster-title; source=database/zh/montitle.txt |
| Lodul title | 雷霆洛杜尔 | monster-title; source=database/zh/montitle.txt |
| Lom Lobon title | 洛姆·洛邦，禁忌知识之恶魔领主 | monster-title; source=database/zh/montitle.txt |
| Louise title | 腐化的路易丝 | monster-title; source=database/zh/montitle.txt |
| Maggie title | 自负的玛吉 | monster-title; source=database/zh/montitle.txt |
| Mara title | 玛拉，幻象领主 | monster-title; source=database/zh/montitle.txt |
| Margery title | 屠龙者玛杰丽 | monster-title; source=database/zh/montitle.txt |
| Maurice title | 盗贼莫里斯 | monster-title; source=database/zh/montitle.txt |
| Menkaure title | 门卡拉，尘土王子 | monster-title; source=database/zh/montitle.txt |
| Mennas title | 门纳斯，辛的代言人 | monster-title; source=database/zh/montitle.txt |
| Mlioglotl title | 姆利奥格洛特尔，无形的恐怖 | monster-title; source=database/zh/montitle.txt |
| Mnoleg title | 姆诺雷格，混沌之恶魔领主 | monster-title; source=database/zh/montitle.txt |
| Murray title | 会说话的恶魔头骨默里 | monster-title; source=database/zh/montitle.txt |
| Natasha title | 娜塔莎，生死仆从 | monster-title; source=database/zh/montitle.txt |
| Nellie title | 内莉，演出明星 | monster-title; source=database/zh/montitle.txt |
| Nergalle title | 内尔加勒，亡者的传说守护者 | monster-title; source=database/zh/montitle.txt |
| Nessos title | 半人马神射手涅索斯 | monster-title; source=database/zh/montitle.txt |
| Nikola title | 疯狂的发明家尼古拉 | monster-title; source=database/zh/montitle.txt |
| Nobody title | 无名氏，未被哀悼者的怨恨 | monster-title; source=database/zh/montitle.txt |
| Norris title | 哲人诺里斯 | monster-title; source=database/zh/montitle.txt |
| Parghit title | 强大的帕吉特 | monster-title; source=database/zh/montitle.txt |
| Pargi title | 柔弱的帕尔吉 | monster-title; source=database/zh/montitle.txt |
| Pikel title | 皮克尔，灵魂商人 | monster-title; source=database/zh/montitle.txt |
| Polyphemus title | 警惕的牧羊人波吕斐摩斯 | monster-title; source=database/zh/montitle.txt |
| Robin title | 强臂罗宾 | monster-title; source=database/zh/montitle.txt |
| Roxanne title | 罗克珊，名誉堪舆师 | monster-title; source=database/zh/montitle.txt |
| Rupert title | 野人鲁珀特 | monster-title; source=database/zh/montitle.txt |
| Saint Roka title | 弥赛亚圣罗卡 | monster-title; source=database/zh/montitle.txt |
| Sigmund title | 可怕的西格蒙德 | monster-title; source=database/zh/montitle.txt |
| Snorg title | 饕餮的斯诺格 | monster-title; source=database/zh/montitle.txt |
| Sojobo title | 索乔波，天狗女王 | monster-title; source=database/zh/montitle.txt |
| Sonja title | 索尼娅，优雅的刺客 | monster-title; source=database/zh/montitle.txt |
| Sprozz title | 创意养蜂人斯普罗兹 | monster-title; source=database/zh/montitle.txt |
| Terence title | 老练的特伦斯 | monster-title; source=database/zh/montitle.txt |
| Tiamat title | 提亚马特，龙神的化身 | monster-title; source=database/zh/montitle.txt |
| Urug title | 兽人弩炮乌鲁格 | monster-title; source=database/zh/montitle.txt |
| Vashnia title | 精英纳迦神射手瓦什妮亚 | monster-title; source=database/zh/montitle.txt |
| Vv title | 流亡的芙芙 | monster-title; source=database/zh/montitle.txt |
| Wiglaf title | 炮手矮人威格拉夫 | monster-title; source=database/zh/montitle.txt |
| Xak'krixis title | 王家远征炼金师扎克里西斯 | monster-title; source=database/zh/montitle.txt |
| Xtahua title | 古老的扎塔瓦 | monster-title; source=database/zh/montitle.txt |
| Zenata title | 泽娜塔，西泽的追寻者 | monster-title; source=database/zh/montitle.txt |


### 新增独特怪物称号（trunk B0）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| Goji, Who Cannot Be Seen | 戈吉，不可见者 | montitle.txt；骑乘幽灵蛾而自诩隐匿的独特怪物称号；decision=D-C-095 |

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
| Controlled Blink | 受控闪烁 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |

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
| Bolt of Inaccuracy | 偏差箭矢 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Explosive Bolt | 爆裂弩矢 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Random Bolt | 随机箭矢 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |

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
| Demonic Horde | 恶魔大军 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Hunting Call | 狩猎呼唤 | ✅ |
| Malign Gateway | 邪恶传送门 | ✅；通往未知污秽异界的临时自维持传送门 |
| Mara Summon | 玛拉召唤 | ✅ |
| Monstrous Menagerie | 怪物动物园 | ✅ |
| Rakshasa Summon | 召唤罗刹 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Recall | 召回术 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Shadow Creatures | 暗影生物 | ✅ |
| Spawn Tentacles | 生成触须 | ✅ |
| Summon Air Elementals | 召唤气元素 | ✅ |
| Summon Butterflies | 召唤蝴蝶 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Summon Cactus Giant | 召唤仙人掌巨人 | ✅ |
| Summon Demon | 召唤恶魔 | ✅ |
| Summon Dragon | 召唤巨龙 | ✅ |
| Summon Drakes | 召唤幼龙 | ✅ |
| Summon Earth Elementals | 召唤地元素 | ✅ |
| Summon Elemental | 召唤元素 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
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
| Summon Iron Elementals | 召唤铁元素 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Summon Mana Viper | 召唤魔力毒蛇 | ✅；复用实体 `mana viper → 魔力毒蛇` |
| Summon Minor Demon | 召唤次级恶魔 | ✅ |
| Summon Mortal Champion | 召唤凡人冠军 | ✅ |
| Summon Mushrooms | 召唤蘑菇 | ✅ |
| Summon Rakshasa | 召唤罗刹 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Summon Scarabs | 召唤圣甲虫 | ✅ |
| Summon Scorpions | 召唤蝎子 | ✅ |
| Summon Seismosaurus Egg | 召唤地震龙蛋 | ✅；复用实体 `seismosaurus egg → 地震龙蛋` |
| Summon Sin Beast | 召唤罪孽兽 | ✅；复用实体 `sin beast → 罪孽兽` |
| Summon Small Mammal | 召唤小型哺乳动物 | ✅ |
| Summon Spiders | 召唤蜘蛛 | ✅ |
| Summon Twister | 召唤旋风 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Summon Tzitzimitl | 召唤齐齐米特尔 | ✅ |
| Summon Ufetubus | 召唤乌菲特布斯 | trunk 已被 Ufetubi Swarm 替代；保留历史标题与实体音译；decision=D-C-095 |
| Summon Undead | 召唤亡灵 | ✅ |
| Summon Vermin | 召唤害虫 | ✅ |
| Summon Water Elementals | 召唤水元素 | ✅ |
| Summon swarm | 召唤虫群 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Vampire Summon | 召唤吸血鬼 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Word of Recall | 召回之言 | ✅；短暂延迟后召回同层有智慧盟友 |

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
| Fire cloud | 火云 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Miasma cloud | 瘴气云 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Poison cloud | 毒气云 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Steam cloud | 蒸汽云 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |

### Breath（22）

| EN | ZH | 备注 |
|---------|------|------|
| Caustic Breath | 腐蚀吐息 | ✅ |
| Chaos Breath | 混沌吐息 | ✅ |
| Cold Breath | 寒霜吐息 | ✅；与 `Breathe Frost → 吐息寒霜` 复用元素词 |
| Combustion Breath | 爆燃吐息 | ✅；射出的挥发余烬会在每个触及生物周围爆炸 |
| Draconian Breath | 龙人吐息 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Fire Breath | 火焰吐息 | ✅ |
| Galvanic Breath | 电击吐息 | ✅ |
| Glacial Breath | 冰川吐息 | ✅ |
| Golden Breath | 金龙吐息 | 🆕 |
| Holy Breath | 神圣吐息 | ✅ |
| Miasma Breath | 瘴气吐息 | ✅ |
| Mud Breath | 泥浆吐息 | ✅ |
| Noxious Breath | 毒瘴吐息 | ✅ |
| Nullifying Breath | 消魔吐息 | ✅ |
| Old serpent of hell breath | 地狱古蛇吐息 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
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
| Mutagenic Gaze | 变异凝视 | ✅；已定稿的固定法术名例外；正文 mutagenic energy 使用“诱变能量”；decision=D-C-096 |
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
| Ring of Flames | 烈焰之环 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Conjure Flame | 召唤火焰 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Flame Tongue | 火焰之舌 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |

### Form（6）

| EN | ZH | 备注 |
|---------|------|------|
| Dragon Form | 巨龙变形 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Hydra Form | 多头蛇变形 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Ice Form | 寒冰变形 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Spider Form | 蜘蛛变形 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Statue Form | 石像变形 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Storm Form | 风暴变形 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |

### Poison / Poisonous（9）

| EN | ZH | 备注 |
|---------|------|------|
| Poisonous Cloud | 毒云 | ✅；复用 Cloud 系列证据 |
| Poison Arrow | 毒箭 | ✅；复用 Arrow 系列证据 |
| Ignite Poison | 点燃毒素 | ✅ |
| Spit Poison | 喷吐毒液 | 📝；与同名能力及其描述统一 |
| Poisonous Vapours | 毒气 | ✅；瞬时气体，不形成持续云 |
| Cure Poison | 解毒术 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Localized Ignite Poison | 局部引爆毒素 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Poison Weapon | 淬毒武器 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Poison cloud | 毒气云 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |

### Awaken（5）

| EN | ZH | 备注 |
|---------|------|------|
| Awaken Armour | 唤醒护甲 | ✅ |
| Awaken Flesh | 唤醒血肉 | ✅ |
| Awaken Forest | 唤醒森林 | ✅ |
| Awaken Vines | 唤醒藤蔓 | ✅ |
| Awaken Earth | 唤醒大地 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |

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
| Cigotuvi's Degeneration | 西格图维之退化 | ⚠️ 已移除兼容；暂缓术语；恢复时复审；无当前机制可供反推 |
| Cigotuvi's Embrace | 西格图维之拥抱 | ⚠️ 已移除兼容；暂缓术语；恢复时复审；无当前机制可供反推 |
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
| Weave Shadows | 编织暗影 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |

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
| Animate Dead | 操纵死尸 | ✅；使施法者杀死的活物有概率化作丧尸复起 |
| Animate Skeleton | 操纵骷髅 | ⚠️ 已移除兼容；暂缓术语；恢复时复审；统一 `Animate → 操纵` |
| Apportation | 隔空取物 | ✅ |
| Arcjolt | 电弧震击 | ✅ |
| Aura of Abjuration | 驱逐灵气 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Avatar Song | 化身之歌 | ✅；限制冒险者远离、眩晕其他生物并可能召来溺魂 |
| Awaken Armour | 唤醒护甲 | ✅ |
| Awaken Earth | 唤醒大地 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Awaken Flesh | 唤醒血肉 | ✅ |
| Awaken Forest | 唤醒森林 | ✅ |
| Awaken Vines | 唤醒藤蔓 | ✅ |
| Banishment | 放逐 | ✅ |
| Battlecry | 战吼 | ✅ |
| Beckoning Gale | 招引之风 | 🆕；扭曲目标周围空气，造成伤害并将其拉近 |
| Berserk Other | 狂暴他人 | ✅；使附近一个盟友进入狂暴 |
| Berserker Rage | 狂暴之怒 | ✅ |
| Beastly Appendage | 野兽肢体 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Bestow Arms | 赐予武器 | ✅ |
| Bind Souls | 束缚灵魂 | 🆕；使附近其他活物死后化为拟像 |
| Blade Hands | 利刃之手 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Bombard | 炮击 | ✅ |
| Brain Bite | 脑噬 | ✅ |
| Brothers in Arms | 战友 | 📝 |
| Cantrip | 小戏法 | ✅ |
| Cause Fear | 恐惧术 | ✅ |
| Chain Lightning | 连锁闪电 | ✅；从最近生物开始向外连锁，距离越远伤害越低 |
| Chain of Chaos | 混沌之链 | ✅ |
| Chant Fire Storm | 咏唱火焰风暴 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Charm | 魅惑 | ✅ |
| Cleansing Flame | 净化之焰 | ✅ |
| Cloud Cone | 云雾锥 | ⚠️ 已移除／TAG 34 兼容；非 `X Cloud` 后缀成员，暂缓术语；恢复时复审 |
| Concentrate Venom | 浓缩毒液 | ✅ |
| Condensation Shield | 凝结护盾 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Confuse | 混乱 | ✅ |
| Conjure Ball Lightning | 召唤球形闪电 | ✅；创造会追敌并爆炸的球状闪电 |
| Conjure Flame | 召唤火焰 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Conjure Living Spells | 召唤活体法术 | ✅ |
| Construct Spike Launcher | 构建尖刺发射器 | ✅ |
| Control Teleport | 控制传送 | ⚠️ 已移除兼容；暂缓术语；恢复时复审；修正中文倒装 |
| Control Undead | 控制亡灵 | ⚠️ 已移除兼容；暂缓术语；恢复时复审；修正中文倒装 |
| Control Winds | 控风术 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Corona | 光晕 | 🆕；环绕并勾勒目标轮廓，使其更易被击中 |
| Corpse Rot | 尸体腐烂 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Corrupt | 腐化 | ✅ |
| Corrupt Body | 腐化躯体 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Corrupting Pulse | 腐化脉冲 | ✅ |
| Creeping Frost | 蔓延冰霜 | ✅；从墙壁唤出冻气，冻结并减速墙边敌人 |
| Crystallising Shot | 结晶射击 | ✅；水晶碎片命中后可能使目标脆化 |
| Cure Poison | 解毒术 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Curse of Agony | 痛苦诅咒 | ✅ |
| Darkness | 黑暗术 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Death Channel | 死亡通道 | ✅；引导期间令被杀的活物、恶魔和神圣生物留下幽魂作战 |
| Death Rattle | 死亡之响 | ✅；呼出垂死精粹并生成瘴气云 |
| Debugging Ray | 调试射线 | ✅ |
| Deflect Missiles | 偏转飞弹 | ✅；排斥力场提高对所有投射物的闪避 |
| Delayed Fireball | 延迟火球 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
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
| Drain Life | 汲取生命 | 🆕；与 `Drain Magic → 汲取魔力` 统一 |
| Drain Magic | 汲取魔力 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Dream Dust | 梦尘 | ✅ |
| Enfeeble | 衰弱 | ✅ |
| Ensnare | 束缚 | ✅；射出蛛网困住单个目标 |
| Ensorcelled Hibernation | 冬眠 | ✅ |
| Entropic Weave | 熵之编织 | ✅ |
| Ephemeral Infusion | 短暂灌注 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Eruption | 喷发 | ✅ |
| Evaporate | 蒸发术 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Excruciating Wounds | 剧痛之伤 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Fastroot | 速生根须 | 🆕；射出种子，以速生树根缠住并挤压目标 |
| Fire Brand | 火焰烙印 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Fire Storm | 火焰风暴 | ✅；9 级大范围定点火焰爆炸，并留下短暂火旋涡 |
| Fireball | 火球 | ✅；投掷会爆炸的火焰球 |
| Flame Tongue | 火焰之舌 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Flame Wave | 火焰波 | ✅ |
| Flash Freeze | 急冻 | ✅；对目标造成高额伤害和短时减速，一半伤害无视寒冷抗性 |
| Flashing Balestra | 闪跃突刺 | 🆕；`balestra` 为击剑前跃接突刺，灵魂跃出持械攻击 |
| Flay | 剥皮 | ✅ |
| Fleetfoot | 轻快脚步 | ✅ |
| Flight | 飞行术 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Force Lance | 力量之矛 | ✅ |
| Forceful Dismissal | 强制驱逐 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Forceful Invitation | 强制邀请 | ✅ |
| Forge Blazeheart Golem | 锻造炽心魔像 | ✅ |
| Forge Lightning Spire | 锻造闪电尖塔 | ✅ |
| Forge Monarch Bomb | 锻造君主炸弹 | ✅ |
| Forge Phalanx Beetle | 锻造方阵甲虫 | ✅ |
| Fortress Blast | 堡垒冲击 | ✅；以施法者护甲决定伤害的延时动能冲击波 |
| Foxfire | 狐火 | 🆕 |
| Freeze | 冰冻 | ✅；相邻单体寒冷攻击，伤害无视护甲 |
| Freezing Aura | 冰封灵气 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Freezing Gust | 冰冻阵风 | 🆕；穿透性严寒气流，沿途留下寒气云 |
| Frenzy | 狂乱术 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Frozen Ramparts | 冰冻壁垒 | ✅；短暂冰封周围墙壁并伤害邻近敌人 |
| Fugue of the Fallen | 亡灵赋格 | ✅ |
| Fulminant Prism | 爆裂棱镜 | ✅ |
| Fulsome Distillation | 精华蒸馏 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Fulsome Fusillade | 猛烈连射 | ✅ |
| Funeral Dirge | 葬礼哀歌 | ✅ |
| Ghostly Fireball | 幽灵火球 | ✅；负能量爆炸使范围内活物衰竭 |
| Ghostly Sacrifice | 幽灵献祭 | ✅；吞噬友方并产生使活物衰竭的负能量爆发 |
| Glaciate | 冰封 | 🆕；锥形寒冰冲击会冰封并减速目标 |
| Gloom | 阴郁 | ✅ |
| Goad Beasts | 激怒野兽 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Grand Avatar | 大化身 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Grasping Roots | 抓握根须 | ✅ |
| Grave Claw | 墓爪 | ✅ |
| Greater Ensnare | 强力束缚 | ✅；命中更高，并在目标附近散布短时蛛网 |
| Hailstorm | 冰雹风暴 | ✅；环形冰雹避开紧邻施法者的目标 |
| Harpoon Shot | 鱼叉射击 | ✅；命中后将目标拉近或使其撞上障碍 |
| Haste | 加速 | ✅；提高施法者行动速度 |
| Haste Other | 加速他人 | ✅；提高附近盟友行动速度 |
| Haste Plants | 加速植物 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Haunt | 鬼魂缠身 | ✅ |
| Heal Other | 治愈他人 | ✅；治疗附近一个盟友 |
| Hellfire Court | 地狱火法庭 | ✅ |
| Hellfire Mortar | 地狱火迫击炮 | ✅ |
| Hoarfrost Bullet | 白霜弹 | ✅；火炮发射的冰霜碎片，命中后施加脆霜减速 |
| Hoarfrost Cannonade | 白霜炮击 | ✅；塑造两座自耗式远程冰霜火炮 |
| Holy Flames | 神圣火焰 | ✅ |
| Holy Light | 圣光术 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Holy word | 圣言术 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Homunculus | 人造人 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Hunting Cry | 狩猎战吼 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Hurl Damnation | 投掷天谴 | 🆕；无视护甲与抗性的 `Damnation` 伤害，非 curse |
| Hurl Sludge | 投掷污泥 | ✅；剧毒污泥会使目标中毒并浸湿周围 |
| Hurl Torchlight | 投掷火炬之光 | ✅；暗影火炬光伤害并强化友方亡灵 |
| Iceblast | 冰爆 | ✅；冰块撞击后爆炸，一半伤害无视寒冷抗性 |
| Ignite Poison | 点燃毒素 | ✅ |
| Ignition | 点火 | ✅ |
| Ill Omen | 凶兆 | ✅ |
| Infernal Servant | 地狱仆从 | ✅ |
| Infestation | 虫群侵扰 | ✅ |
| Infusion | 灌注术 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Injury Bond | 伤害联结 | ✅；与附近盟友联结，替其承担被减免伤害的一半 |
| Injury Mirror | 伤害反射 | ✅ |
| Inner Flame | 内焰 | ✅ |
| Insulation | 绝缘术 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Invisibility | 隐身术 | ✅；使施法者隐形 |
| Invisibility Other | 使他人隐形 | 🆕；使附近盟友隐形 |
| Iron Shot | 铁弹 | ✅；`shot` 指重型金属弹体，不机械统一为“射击” |
| Irradiate | 辐射 | ✅ |
| Jinxbite | 厄运之咬 | ✅ |
| Kinetic Grapnel | 动力抓钩 | ✅ |
| Kiss of Death | 死亡之吻 | ✅；衰竭目标并暂时降低施法者生命值 |
| Landbreaker | 裂地 | ✅ |
| Launch Bomblet | 发射小型炸弹 | ✅；弹道无视火线并将炸弹部署在目标附近 |
| Launch Clockwork Bee | 发射发条蜜蜂 | ✅；制造、上紧发条并放出机械蜜蜂 |
| Launch Sporangium | 发射孢子囊 | ✅；追踪目标并以酸液爆炸生成原生质体 |
| Legendary Destruction | 传奇毁灭 | ✅；立刻连续产生两种爆炸法术效果 |
| Lesser Beckoning | 次级招引 | 🆕；把目标拉至施法者相邻位置，不是召唤法术 |
| Lethal Infusion | 致命灌注 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Localized Ignite Poison | 局部引爆毒素 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Magma Barrage | 岩浆弹幕 | ✅ |
| Magnavolt | 磁暴 | ✅ |
| Major Destruction | 强力毁灭 | 🆕；随机发射有害射束或爆炸，`major` 表示强度而非尺寸 |
| Major Healing | 大型治疗 | ✅；治疗施法者身体所受的大量伤害 |
| Malign Offering | 邪恶献祭 | ✅；汲取敌人生命并治疗附近盟友 |
| Malmutate | 恶性变异 | ✅ |
| Manifold Assault | 多重攻击 | ✅ |
| March of Sorrows | 悲伤行军 | ✅ |
| Marshlight | 沼泽之光 | ✅ |
| Mass Confusion | 群体混乱 | ✅ |
| Mass Regeneration | 群体再生 | ✅；附近所有友方怪物按各自最大生命值快速恢复 |
| Melee | 近战 | ✅ |
| Mesmerise | 迷魂 | ✅；5 级怪物诅咒法术，使冒险者无法主动远离施法者、使其他生物眩晕；与 Sleep「沉睡」及 Charm「魅惑」区分；裁决=[D-A-043] |
| Metabolic Englaciation | 代谢冻结 | 🆕；降低周围生物代谢并减速 |
| Metal Splinters | 金属碎刺 | ✅ |
| Might | 强壮 | ✅；法术显示标题，区别于状态/机制域 `Might → 强效` |
| Might Other | 强壮他人 | ✅；对附近友方施加同类近战伤害增益 |
| Mindburst | 心智爆发 | ✅ |
| Minor Healing | 小型治疗 | ✅；治疗施法者身体所受的少量伤害 |
| Mislead | 误导术 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Momentum Strike | 动量打击 | ✅；借用未来移动能量攻击并令施法者短时无法移动 |
| Mourning Wail | 哀恸之嚎 | 🆕；吐出遗忘悲恸形成负能量云 |
| Necromutation | 亡灵变形 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Oblivion Howl | 湮灭嚎叫 | ✅ |
| Old Deflect Missiles | 旧版偏转飞弹 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Orb of Destruction | 毁灭法球 | ✅；缓慢追踪、初生时伤害较低的纯毁灭魔力法球 |
| Orb of Electricity | 电光球 | ✅；命中时产生大型电能爆炸 |
| Ostracise | 排斥 | ✅ |
| Pain | 痛苦 | ✅ |
| Paralyse | 麻痹 | ✅ |
| Passage of Golubria | 戈卢布里亚之通道 | ✅ |
| Passwall | 穿墙术 | ✅ |
| Permafrost Eruption | 永冻爆发 | ✅；地底严寒与落石轰击敌人最密集处，不在施法者身旁爆发 |
| Petrify | 石化 | ✅ |
| Phantom Blitz | 幻影突击 | ✅；发射保有施法者战斗能力的幻影复制体 |
| Phantom Mirror | 幻影镜 | ✅；制造较脆弱但近似原体的怪物幻影 |
| Phase Shift | 相位变换 | ✅ trunk 新 SPELL_PHASE_SHIFT 已复审：身体偏离常规空间；SPELL_PHASE_SHIFT_OLD 保留同名旧身份兼容；decision=D-C-095 |
| Planar Overlay | 位面叠加 | ✅ |
| Plane Rend | 位面撕裂 | ✅ |
| Platinum Paragon | 白金典范 | ✅ |
| Poison Weapon | 淬毒武器 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Polar Vortex | 极地漩涡 | ✅；冰冻漩涡随施法者移动并抛动范围内生物 |
| Polymorph | 变形术 | ✅ |
| Porkalator | 变猪术 | ✅ |
| Portal Projectile | 传送投射物 | ✅ |
| Prayer of Brilliance | 聪慧祈祷 | ✅ |
| Primal Wave | 原初浪潮 | 🆕；召出激流击退目标并留下短时浅水 |
| Pyroclastic Surge | 火山碎屑涌 | ✅ |
| Pyrrhic Recollection | 惨胜回忆 | ✅ |
| Random Effects | 随机效果 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Ravenous Swarm | 饥渴蝠群 | 🆕；吸血蝙蝠群啃咬非亡灵并最终使其入睡 |
| Rearrange the Pieces | 重新布局 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Rebounding Blaze | 弹跳烈焰 | ✅ |
| Rebounding Chill | 弹跳寒流 | 🆕；穿透性寒气束可从墙壁反弹并命中两次 |
| Regenerate Other | 再生他人 | ✅；恢复量与目标最大生命值成正比 |
| Regeneration | 再生 | ⚠️ 已移除兼容；暂缓术语；恢复时复审；同步 inventory 实际译名 |
| Rending Blade | 撕裂之刃 | ✅；近战命中时在附近敌人间来回撕裂 |
| Resonance Strike | 共鸣打击 | ✅；经目标附近造物级联并逐个增强 |
| Resurrect | 复活术 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Rimeblight | 霜疫 | ✅；从体内冻结宿主并可能在死亡时传播 |
| Ring of Flames | 烈焰之环 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Ring of Thunder | 雷霆之环 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Roll | 翻滚 | ✅ |
| Sacrifice | 献祭 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Sandblast | 沙爆 | 📝 |
| Sap Magic | 削弱魔法 | ✅ |
| Scattershot | 散射术 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Scorch | 烧焦 | ✅ |
| Sculpt Simulacrum | 塑造拟像 | ✅ |
| Seal Doors | 封印门 | ✅ |
| Searing Ray | 灼热射线 | ✅ |
| See Invisible | 识破隐形 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Seismic Stomp | 地震践踏 | ✅ |
| Seracfall | 冰塔崩塌 | ✅ |
| Shaft Self | 自掘竖井 | ✅ 现行能力；同名法术仍为 TAG 34 兼容记录 |
| Shatter | 粉碎 | ✅ |
| Shock | 震击 | ✅ |
| Shred | 撕裂 | ✅ |
| Shroud of Golubria | 戈卢布里亚之幕 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Sigil of Binding | 束缚符文 | ✅ |
| Sign of Ruin | 毁灭印记 | 🆕 |
| Silence | 沉默 | 🆕 |
| Silver Blast | 白银冲击 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Singularity | 奇点术 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Siphon Essence | 吸取精华 | ✅ |
| Siren Song | 塞壬之歌 | ✅；迷魂附近听众，离开施法者视野后解除移动限制 |
| Sleep | 睡眠 | ✅ |
| Sleetstrike | 冰雨打击 | ✅ |
| Slow | 缓慢 | 📝 |
| Smiting | 惩击 | ✅ |
| Song of Shielding | 护盾之歌 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Sonic wave | 音波 | ✅ |
| Soul Splinter | 灵魂分裂 | ✅ |
| Spectral Weapon | 灵体武器 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
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
| Sting | 刺痛 | 🆕 |
| Stoke Flames | 煽旺火焰 | 📝；`stoke` 指添燃料使火势更旺 |
| Stoneskin | 石肤术 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Striking | 打击术 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Strip Willpower | 剥离意志力 | ✅ |
| Stunning Burst | 眩晕爆发 | ✅ |
| Sublimation of Blood | 血液升华 | ✅ |
| Sunray | 阳光射线 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Sure Blade | 精准之刃 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Swiftness | 迅捷 | ✅ |
| Symbol of Torment | 折磨之符 | ✅ |
| Teleport Other | 传送他人 | ✅；短暂延迟后尝试将目标传送出施法者视野 |
| Teleport Self | 自我传送 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Throw | 投掷 | ⚠️ 已移除／TAG 34 兼容；暂缓术语；恢复时复审 |
| Throw Ally | 投掷盟友 | ✅ |
| Throw Barbs | 投掷倒刺 | ✅ |
| Throw Bolas | 投掷流星索 | ✅ |
| Throw Flame | 投掷火焰 | ✅ |
| Throw Frost | 投掷冰霜 | ✅ |
| Throw Icicle | 投掷冰柱 | ✅ |
| Throw Klown Pie | 投掷小丑派 | ✅ |
| Tomb of Doroklohe | 多洛克洛之墓 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Tremorstone | 震石 | ✅ |
| Twisted Resurrection | 扭曲复活 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Unleash Destruction | 释放毁灭 | ✅；马科列布能力的虚拟法术标题 |
| Upheaval | 剧变 | ✅ |
| Vampiric Draining | 吸血术 | ✅ |
| Vanquished Vanguard | 败军先锋 | 📝 |
| Vex | 激怒 | ✅ |
| Virulence | 毒性 | ✅ |
| Vitrify | 玻璃化 | ✅ |
| Volatile Blastmotes | 不稳定爆尘 | ✅ |
| Volley of Thorns | 荆棘齐射 | ✅ |
| Vortex | 漩涡 | ⚠️ 已移除兼容；暂缓术语；恢复时复审；与 `Polar Vortex` 统一词根 |
| Wall of Brambles | 荆棘之墙 | trunk 已被 Cage of Brambles 替代；保留历史标题，不用于新法术；decision=D-C-095 |
| Warning Cry | 警告之嚎 | ✅ |
| Warp Body | 扭曲身体 | ✅；造成少量伤害和短暂变异，变异过多时改为玻璃化 |
| Warp Space | 扭曲空间 | ✅；空间裂隙造成范围伤害并可能短距闪现目标 |
| Warp Weapon | 扭曲武器 | ⚠️ 已移除兼容；暂缓术语；恢复时复审 |
| Waterstrike | 水击 | ✅ |
| Wind Blast | 风击 | ✅；锥形强风推开生物和云雾，碰撞会造成伤害 |
| Woodweal | 林木疗愈 | 🆕；借相邻树木的叶与树皮活力治疗伤势 |
| nonexistent spell | 不存在的法术 | ✅ |

### 上游新增法术（trunk B0）

| EN | ZH | 依据 / 作用域 |
|----|----|---------------|
| Dragon Veins | 龙脉 | spl-data.h / spells.txt；显露地牢元素能量脉络，复数不另造词；decision=D-C-095 |
| Dragon Vein (Fire) | 龙脉（火） | 同系列四元素触发法术；括号区分元素；decision=D-C-095 |
| Dragon Vein (Ice) | 龙脉（冰） | 同系列四元素触发法术；decision=D-C-095 |
| Dragon Vein (Air) | 龙脉（气） | 同系列四元素触发法术；decision=D-C-095 |
| Dragon Vein (Earth) | 龙脉（土） | 同系列四元素触发法术；decision=D-C-095 |
| Ice Thorns | 冰棘 | spells.txt；目标周围的尖锐冰刺；decision=D-C-095 |
| Sirocco | 灼热风 | spells.txt；灼热阵风推退邻敌；避免误译为沙尘暴；decision=D-C-095 |
| Ufetubi Swarm | 乌菲特布斯群 | spells.txt；一群狂暴 ufetubi；沿用现有实体音译；decision=D-C-095 |
| Cage of Brambles | 荆棘牢笼 | spells.txt；围住各邻近敌人的环状荆棘墙；decision=D-C-095 |
| Murky Legion | 浊影军团 | spells.txt；召唤浊光怨灵；保留 murky 与 legion 意象；decision=D-C-095 |
| Touch of Paradox | 悖论之触 | spells.txt；使友军脱离常规空间；沿用 Touch 构词；decision=D-C-095 |
| Bolt of Antimagic | 反魔箭 | spells.txt / spl-util.cc；标题与稳定版 bolt of antimagic 共用大小写不敏感的 catalog 键；decision=D-C-098（取代 D-C-095 的此键译法） |
| Stampede | 奔踏 | spl-data.h / spells.txt；直线奔袭推退敌人，区别 Rampage → 冲锋；decision=D-C-095 |
| Bolster | 强化 | spells.txt；对齐稳定版共享 catalog 键；增强近战与元素抗性，区别 Might → 强壮；decision=D-C-098（取代 D-C-095 的此键译法） |

**历史汇总（0.34.1 复审批次）**：511 法术，✅ 保留 370，📝 修订 15，🆕 新增 28，⚠️ 已移除兼容 98。trunk 增量以 D-C-095 与上述 B0 表为准，不从这份历史统计推导现行法术集合。

---

*最后更新：2026-10-07 | 来源：docs/decisions.md + docs/spell-naming-rules.md + [legacy issue 12 glossary][legacy-12-glossary] + zh-translator.md*

[legacy-12-glossary]: https://github.com/yutio8888/crawl-chn-issues-archive/blob/d31fccd3eb2c2cd612739646769ee1b45b6dfb01/12/glossary_and_style.md
