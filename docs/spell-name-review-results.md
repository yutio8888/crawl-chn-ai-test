# 法术名称逐项复审结果

本文件是 `docs/spell-name-review-plan.md` 的证据记录，不是术语权威。
通用术语以 `docs/glossary.md` 为准，具体命名裁定以
`docs/decisions.md` 为准。

冻结基线：`5cb9aa27a224a81da780757f8445cfc07de09dfd`

术语上下文 SHA-256：
`4070a396e65a4bdf1fd2dfbc9e95bcc40053391e65441053f73c08146ed31d9e`

## Blink 系列

系列结论：保留 `Blink → 闪烁` 核心词根；8 项现行法术与 1 项已移除
兼容记录分开审阅。现行标题中 4 项含显式受事者的译名存在英语词序移植，
应统一改为自然的使役结构。

| Enum | 生命周期 | 当前译名 | 裁定 | 建议译名 | 置信度 |
|---|---|---|---|---|---|
| `SPELL_BLINK` | 现行 | 闪烁 | 保留 | 闪烁 | 高 |
| `SPELL_BLINK_ALLIES_AWAY` | 现行 | 闪烁盟友远离 | 重译 | 使盟友闪烁远离 | 高 |
| `SPELL_BLINK_ALLIES_ENCIRCLE` | 现行 | 闪烁盟友包围 | 重译 | 使盟友闪烁合围 | 高 |
| `SPELL_BLINK_AWAY` | 现行 | 远离闪烁 | 保留 | 远离闪烁 | 高 |
| `SPELL_BLINK_CLOSE` | 现行 | 接近闪烁 | 保留 | 接近闪烁 | 高 |
| `SPELL_BLINK_OTHER` | 现行 | 闪烁他人 | 微调 | 使他人闪烁 | 高 |
| `SPELL_BLINK_OTHER_CLOSE` | 现行 | 闪烁他人接近 | 重译 | 使他人闪烁靠近 | 高 |
| `SPELL_BLINK_RANGE` | 现行 | 退避闪烁 | 保留 | 退避闪烁 | 高 |
| `SPELL_CONTROLLED_BLINK` | 已移除兼容 | 受控闪烁 | 保留 | 受控闪烁 | 高 |

### `SPELL_BLINK`

- 英文名 / 当前中文名：Blink / 闪烁。
- 等级、学派与 flags：2 级传送系，`escape | selfench`。
- 使用者：玩家和怪物；两条实现都是非精确的附近位移。
- 核心效果：玩家随机短距位移并获得随法术威力变化的短暂再次施放间隔；
  怪物随机闪烁到附近可用格。
- 裁定：保留“闪烁”。标题不需要加入仅属于玩家路径的冷却细节。
- 证据：`crawl-ref/source/spl-data.h:508`、
  `crawl-ref/source/dat/descript/spells.txt:178`、
  `crawl-ref/source/dat/descript/zh/spells.txt:144`、
  `crawl-ref/source/spl-transloc.cc:919`、
  `crawl-ref/source/mon-cast.cc:690`。

### `SPELL_BLINK_ALLIES_AWAY`

- 英文名 / 当前中文名：Blink Allies Away / 闪烁盟友远离。
- 等级、学派与 flags：6 级传送系，`target | monster`；怪物专属。
- 核心效果：选择靠近敌人的施法者盟友，将其闪烁到更远的位置。
- 裁定：重译为“使盟友闪烁远离”。当前标题把不及物的“闪烁”直接置于
  “盟友”前，施法对象与结果方向不清。
- 被拒方案：“盟友远离闪烁”弱化使役关系；“闪送盟友远离”丢失系列词根；
  “盟友退避闪烁”会与 Blink Range 的特殊机制混淆。
- 证据：`crawl-ref/source/spl-data.h:2498`、
  `crawl-ref/source/dat/descript/spells.txt:146`、
  `crawl-ref/source/dat/descript/zh/spells.txt:116`、
  `crawl-ref/source/mon-cast.cc:2858`、
  `crawl-ref/source/mon-cast.cc:6403`。

### `SPELL_BLINK_ALLIES_ENCIRCLE`

- 英文名 / 当前中文名：Blink Allies Encircling / 闪烁盟友包围。
- 等级、学派与 flags：6 级传送系，`target | monster`；怪物专属。
- 核心效果：把 3–6 名盟友移动到目标敌人的相邻格，形成合围。
- 裁定：重译为“使盟友闪烁合围”，保留使役对象、系列词根和阵形结果。
- 被拒方案：“使盟友闪烁包围”结果补语生硬；“盟友环绕闪烁”弱化使役
  和包围结果；“闪送盟友合围”丢失系列词根。
- 证据：`crawl-ref/source/spl-data.h:2220`、
  `crawl-ref/source/dat/descript/spells.txt:150`、
  `crawl-ref/source/dat/descript/zh/spells.txt:120`、
  `crawl-ref/source/mon-cast.cc:2858`、
  `crawl-ref/source/mon-cast.cc:6365`。

### `SPELL_BLINK_AWAY`

- 英文名 / 当前中文名：Blink Away / 远离闪烁。
- 等级、学派与 flags：2 级传送系，`escape | monster | selfench`；
  怪物专属。
- 核心效果：施法者相对当前敌人移动到更远位置。
- 裁定：保留“远离闪烁”，与“接近闪烁”构成明确方向对偶。
- 证据：`crawl-ref/source/spl-data.h:530`、
  `crawl-ref/source/dat/descript/spells.txt:155`、
  `crawl-ref/source/dat/descript/zh/spells.txt:124`、
  `crawl-ref/source/teleport.cc:368`、
  `crawl-ref/source/mon-cast.cc:702`。

### `SPELL_BLINK_CLOSE`

- 英文名 / 当前中文名：Blink Close / 接近闪烁。
- 等级、学派与 flags：2 级传送系，`monster | target`；怪物专属。
- 核心效果：施法者向当前敌人靠近。
- 裁定：保留“接近闪烁”。
- 附带发现：中文描述遗漏英文描述的 “a short distance”，应在本系列翻译
  批次补回“一小段距离”，但不影响标题裁定。
- 证据：`crawl-ref/source/spl-data.h:541`、
  `crawl-ref/source/dat/descript/spells.txt:159`、
  `crawl-ref/source/dat/descript/zh/spells.txt:128`、
  `crawl-ref/source/teleport.cc:411`、
  `crawl-ref/source/mon-cast.cc:708`。

### `SPELL_BLINK_OTHER`

- 英文名 / 当前中文名：Blink Other / 闪烁他人。
- 等级、学派与 flags：2 级传送系，
  `dir_or_target | escape | monster | needs_tracer`；怪物专属。
- 核心效果：使目标敌人进行不可由意志抵抗的随机短距闪烁。
- 裁定：微调为“使他人闪烁”，修复“闪烁”被机械当作及物动词的问题。
- 被拒方案：“他人闪烁”弱化使役关系；“闪送他人”丢失系列词根；
  “使敌人闪烁”不必要地把较中性的 Other 改写为机制限定。
- 证据：`crawl-ref/source/spl-data.h:1511`、
  `crawl-ref/source/dat/descript/spells.txt:168`、
  `crawl-ref/source/dat/descript/zh/spells.txt:136`、
  `crawl-ref/source/mon-cast.cc:2425`、
  `crawl-ref/source/beam.cc:6184`。

### `SPELL_BLINK_OTHER_CLOSE`

- 英文名 / 当前中文名：Blink Other Close / 闪烁他人接近。
- 等级、学派与 flags：2 级传送系，
  `dir_or_target | monster | needs_tracer`；怪物专属。
- 核心效果：使目标敌人闪烁一小段距离，向施法者靠近。
- 裁定：重译为“使他人闪烁靠近”，明确受事者、动作和方向。
- 被拒方案：“使他人接近闪烁”可能被读成在近处闪烁；“使他人闪烁近身”
  误示必定抵达相邻格；“闪送他人靠近”丢失系列词根。
- 证据：`crawl-ref/source/spl-data.h:1523`、
  `crawl-ref/source/dat/descript/spells.txt:163`、
  `crawl-ref/source/dat/descript/zh/spells.txt:132`、
  `crawl-ref/source/mon-cast.cc:2429`、
  `crawl-ref/source/teleport.cc:341`、
  `crawl-ref/source/beam.cc:6192`。

### `SPELL_BLINK_RANGE`

- 英文名 / 当前中文名：Blink Range / 退避闪烁。
- 等级、学派与 flags：2 级传送系，`escape | monster | selfench`；
  怪物专属。
- 核心效果：远离当前敌人，但仍保持在该敌人视线范围内。
- 裁定：保留“退避闪烁”。英文数据本身注明名称需要改进，现译依据机制
  避免“范围闪烁”造成的施法范围误解。
- 证据：`crawl-ref/source/spl-data.h:519`、
  `crawl-ref/source/dat/descript/spells.txt:173`、
  `crawl-ref/source/dat/descript/zh/spells.txt:140`、
  `crawl-ref/source/teleport.cc:395`、
  `docs/decisions.md:750`。

### `SPELL_CONTROLLED_BLINK`

- 英文名 / 当前中文名：Controlled Blink / 受控闪烁。
- 生命周期：仅存在于 `TAG_MAJOR_VERSION == 34` 的 `AXED_SPELL` 与存档兼容
  路径，不是现行可施放法术，也没有现行英中描述。
- 历史核心效果：允许玩家选择附近落点；当前仍存在的同名实现辅助函数用于
  物品路径，不能据此把该法术当作现行成员。
- 裁定：历史标题保留“受控闪烁”，但在 glossary 中标为“已移除／兼容”，
  不计入 8 个现行系列成员。
- 证据：`crawl-ref/source/spl-data.h:4641`、
  `crawl-ref/source/spl-util.cc:2525`、
  `crawl-ref/source/spell-type.h:37`、
  `crawl-ref/source/ghost.cc:1112`、
  `crawl-ref/source/spl-transloc.cc:861`、
  `crawl-ref/source/item-use.cc:2583`。

### 落地状态

- [x] 机制证据收集
- [x] 翻译审阅裁定
- [x] 单一翻译写入者落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-013`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T145517519115000+0800-41550-5cb9aa27a224`。

## Bolt 系列

系列结论：常规现行 `Bolt` 稳定译为“箭”，不改译为会与 `Beam` 混淆的
“束”，也不取弩箭义的“弩矢”。`Blinkbolt` 是融合构词，但“闪烁箭”仍可
保留；`Thunderbolt` 是词汇化单词且机制为扇形连续电弧，保留例外“雷击”。
3 项已移除兼容记录不参与现行词根计数。

| Enum | 生命周期 | 当前译名 | 裁定 | 建议译名 | 置信度 |
|---|---|---|---|---|---|
| `SPELL_BLINKBOLT` | 现行 | 闪烁箭 | 保留 | 闪烁箭 | 高 |
| `SPELL_BOLT_OF_COLD` | 现行 | 寒冰箭 | 保留 | 寒冰箭 | 高 |
| `SPELL_BOLT_OF_DEVASTATION` | 现行 | 毁灭箭 | 保留 | 毁灭箭 | 高 |
| `SPELL_BOLT_OF_DRAINING` | 现行 | 吸取箭 | 重译 | 衰竭箭 | 高 |
| `SPELL_BOLT_OF_FIRE` | 现行 | 火焰箭 | 保留 | 火焰箭 | 高 |
| `SPELL_BOLT_OF_FLESH` | 现行 | 血肉箭 | 保留 | 血肉箭 | 高 |
| `SPELL_BOLT_OF_INACCURACY` | 已移除兼容 | 偏差箭矢 | 无当前机制 | 暂缓术语（恢复时复审；暂沿用偏差箭矢） | 高 |
| `SPELL_BOLT_OF_LIGHT` | 现行 | 光箭 | 保留 | 光箭 | 高 |
| `SPELL_BOLT_OF_MAGMA` | 现行 | 岩浆箭 | 保留 | 岩浆箭 | 高 |
| `SPELL_CORROSIVE_BOLT` | 现行 | 腐蚀箭 | 保留 | 腐蚀箭 | 高 |
| `SPELL_DOOM_BOLT` | 现行 | 厄运箭 | 保留 | 厄运箭 | 高 |
| `SPELL_ELECTRICAL_BOLT` | 现行 | 电击箭 | 保留 | 电击箭 | 高 |
| `SPELL_EXPLOSIVE_BOLT` | 已移除兼容 | 爆裂弩矢 | 无当前机制 | 暂缓术语（恢复时复审；暂沿用爆裂弩矢） | 高 |
| `SPELL_LIGHTNING_BOLT` | 现行 | 闪电箭 | 保留 | 闪电箭 | 高 |
| `SPELL_QUICKSILVER_BOLT` | 现行 | 水银箭 | 保留 | 水银箭 | 高 |
| `SPELL_RANDOM_BOLT` | 已移除兼容 | 随机箭矢 | 无当前机制 | 暂缓术语（恢复时复审；暂沿用随机箭矢） | 高 |
| `SPELL_SOJOURNING_BOLT` | 现行 | 旅居箭 | 微调 | 羁旅箭 | 中 |
| `SPELL_THUNDERBOLT` | 现行 | 雷击 | 保留 | 雷击 | 高 |
| `SPELL_VENOM_BOLT` | 现行 | 毒液箭 | 保留 | 毒液箭 | 高 |

### 逐项机制与命名证据

- `SPELL_BLINKBOLT`：5 级空气／传送法术；穿透电束造成伤害并让施法者沿
  路径位移，玩家版本在目标处停止且有冷却。复合词仍保留“闪烁箭”；
  “闪电遁”会丢失系列辨识。证据：`spl-data.h:162`、
  `zap-data.h:1555`、`spl-transloc.cc:2058`、`beam.cc:2704`。
- `SPELL_BOLT_OF_COLD`：6 级寒冰穿透束，无附加状态；“寒冰箭”是规则
  既有范例，“寒冰束”会与 Beam 混淆。证据：`spl-data.h:107`、
  `zap-data.h:597`、`dat/descript/spells.txt:189`。
- `SPELL_BOLT_OF_DEVASTATION`：5 级怪物法术，造成伤害并剥离意志；
  “毁灭箭”保留原名强语气，“意志破坏箭”过度说明式。证据：
  `spl-data.h:1411`、`zap-data.h:82`、`beam.cc:1806`。
- `SPELL_BOLT_OF_DRAINING`：5 级负能量穿透束，对活物施加 Drain，不把
  生命或魔力转给施法者；“吸取箭”误示施法者获益，重译“衰竭箭”。
  “汲取箭”仍有同一误导。证据：`spl-data.h:432`、
  `zap-data.h:803`、`beam.cc:1671`。
- `SPELL_BOLT_OF_FIRE`：6 级火焰穿透束，可烧树，无附加状态；保留与
  “寒冰箭”对称的“火焰箭”。证据：`spl-data.h:96`、
  `zap-data.h:582`、`beam.cc:2943`。
- `SPELL_BOLT_OF_FLESH`：6 级怪物法术，穿透魔法弹在末端生成短暂肉堆；
  “血肉箭”保留原名实体意象，“肉堆箭”会让附加效果覆盖标题。
  证据：`spl-data.h:2653`、`zap-data.h:113`、`beam.cc:2755`。
- `SPELL_BOLT_OF_INACCURACY`：仅 TAG 34 `AXED_SPELL` 占位，没有现行
  描述、zap 或实现；暂沿用“偏差箭矢”，若恢复再比较“失准箭”。
  证据：`spl-data.h:4641`、`dat/i18n/zh/source.txt:16872`。
- `SPELL_BOLT_OF_LIGHT`：6 级穿透光束，可致盲适用目标；“光箭”简洁，
  “致盲光箭”会把概率附效写入标题。证据：`spl-data.h:2642`、
  `zap-data.h:1475`、`beam.cc:5309`。
- `SPELL_BOLT_OF_MAGMA`：5 级熔岩穿透束，一半伤害绕过火抗；保留
  “岩浆箭”，不把抗性细节塞入标题。证据：`spl-data.h:197`、
  `zap-data.h:1285`、`dat/descript/spells.txt:216`。
- `SPELL_CORROSIVE_BOLT`：6 级酸性穿透束，可施加腐蚀；“腐蚀箭”同时
  保留属性和附效，“酸液箭”会弱化 Corrosive。证据：
  `spl-data.h:2631`、`zap-data.h:1460`、`beam.cc:4501`。
- `SPELL_DOOM_BOLT`：5 级普通伤害穿透束并施加 Doom，不是负能量；
  “厄运箭”准确，“毁灭箭”会与 Devastation 冲突。证据：
  `spl-data.h:4519`、`zap-data.h:97`、`beam.cc:4468`。
- `SPELL_ELECTRICAL_BOLT`：5 级怪物专属高命中电束，可墙面反弹；
  “电击箭”与 Lightning Bolt 的“闪电箭”保持区分。证据：
  `spl-data.h:2758`、`zap-data.h:452`、`beam.cc:2428`。
- `SPELL_EXPLOSIVE_BOLT`：仅 TAG 34 `AXED_SPELL` 占位，没有现行实现
  可以判断其历史上采用 projectile 还是 crossbow 义；暂沿用“爆裂弩矢”。
  证据：`spl-data.h:4664`、`dat/i18n/zh/source.txt:16923`。
- `SPELL_LIGHTNING_BOLT`：5 级穿透电束，绕过一半护甲且可墙面反弹；
  “闪电箭”自然稳定，“雷霆箭”无据增强。证据：`spl-data.h:118`、
  `zap-data.h:771`、`beam.cc:2428`。
- `SPELL_QUICKSILVER_BOLT`：5 级水银穿透束，命中后驱散 enchantments；
  保留原名意象“水银箭”，不按机制改成“驱散箭”。证据：
  `spl-data.h:1456`、`zap-data.h:1445`、`beam.cc:4459`。
- `SPELL_RANDOM_BOLT`：仅 TAG 34 `AXED_SPELL` 占位，没有现行随机池；
  暂沿用“随机箭矢”，不参与现行词根计数。证据：`spl-data.h:4685`、
  `dat/i18n/zh/source.txt:16986`。
- `SPELL_SOJOURNING_BOLT`：6 级穿透不稳定能量，命中后有概率延迟传送
  受害者；“旅居”偏现代异地暂住且生硬，微调为更凝练奇幻的“羁旅箭”。
  “维度跃迁箭”依据的是错误中文描述。证据：`spl-data.h:3292`、
  `zap-data.h:1960`、`beam.cc:4513`、`beam.cc:5235`。
- `SPELL_THUNDERBOLT`：雷击杖的连续瞄准扇形电弧，不走普通 zap_data
  直线束；英文是词汇化单词，保留机制准确的例外“雷击”。
  证据：`spl-data.h:2051`、`target.cc:1313`、
  `spl-damage.cc:3263`。
- `SPELL_VENOM_BOLT`：5 级毒素穿透束，可施加中毒；“毒液箭”保留
  venom 强于泛称“毒”的含义。证据：`spl-data.h:342`、
  `zap-data.h:788`、`beam.cc:1591`。

### 附带描述问题

- `Bolt of Draining`：中文把英文 `living creature` 扩大为所有“生物”。
- `Corrosive Bolt`：中文遗漏 `highly-corrosive` 的强腐蚀修辞。
- `Doom Bolt`：中文捏造“毁灭性的负能量束”，遗漏施加 Doom。
- `Quicksilver Bolt`：中文“无视护甲”与英文和驱散实现相反。
- `Sojourning Bolt`：中文捏造“穿越多个维度／维度间弹跳”，遗漏延迟传送
  及玩家目标的特殊同行逻辑。

### 落地状态

- [x] 机制证据收集
- [x] 翻译审阅裁定
- [x] 单一翻译写入者落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-014`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T152511196031000+0800-92653-8e6c745c786a`。

## Cloud 词形系列

系列结论：现行 `X Cloud` 后缀构词稳定保留中心词“云”。8 项现行标题
全部保留；4 项 `X Cloud` 历史兼容标题和反向复合词 `Cloud Cone` 均因
缺少现行 metadata、描述与实现而暂沿用，不反向约束现行译名。
`Cloud Cone` 的中心词是 Cone，不计入 `X Cloud` 后缀系列，但仍留在全法术
词形索引中。

| Enum | 生命周期 | 当前译名 | 裁定 | 建议译名 | 置信度 |
|---|---|---|---|---|---|
| `SPELL_FREEZING_CLOUD` | 现行 | 冰冻云 | 保留 | 冰冻云 | 高 |
| `SPELL_MEPHITIC_CLOUD` | 现行 | 迷瘴云 | 保留 | 迷瘴云 | 中高 |
| `SPELL_POISONOUS_CLOUD` | 现行 | 毒云 | 保留 | 毒云 | 高 |
| `SPELL_NOXIOUS_CLOUD` | 现行 | 毒瘴云 | 保留 | 毒瘴云 | 中高 |
| `SPELL_INK_CLOUD` | 现行 | 墨云 | 保留 | 墨云 | 高 |
| `SPELL_PETRIFYING_CLOUD` | 现行 | 石化云 | 保留 | 石化云 | 高 |
| `SPELL_SPECTRAL_CLOUD` | 现行 | 幽灵云 | 保留 | 幽灵云 | 中高 |
| `SPELL_FLAMING_CLOUD` | 现行 | 燃烧云 | 保留 | 燃烧云 | 高 |
| `SPELL_MIASMA_CLOUD` | 已移除兼容 | 瘴气云 | 无当前机制 | 暂缓术语（恢复时复审；暂沿用瘴气云） | 高 |
| `SPELL_POISON_CLOUD` | 已移除兼容 | 毒气云 | 无当前机制 | 暂缓术语（恢复时复审；暂沿用毒气云） | 高 |
| `SPELL_FIRE_CLOUD` | 已移除兼容 | 火云 | 无当前机制 | 暂缓术语（恢复时复审；暂沿用火云） | 高 |
| `SPELL_STEAM_CLOUD` | 已移除兼容 | 蒸汽云 | 无当前机制 | 暂缓术语（恢复时复审；暂沿用蒸汽云） | 高 |
| `SPELL_CLOUD_CONE` | 已移除兼容 | 云雾锥 | 无当前机制 | 暂缓术语（恢复时复审；暂沿用云雾锥） | 高 |

### 逐项机制与命名证据

- `SPELL_FREEZING_CLOUD`：5 级玩家寒冰／空气法术，在目标处形成大团
  `CLOUD_COLD` 并持续造成寒冷伤害。“冰冻云”表达致伤动态；“冻结云”
  易读成云本身被冻结。证据：`spl-data.h:309`、
  `dat/descript/spells.txt:799`、`spl-clouds.cc:104`。
- `SPELL_MEPHITIC_CLOUD`：3 级玩家瓶式小范围爆炸，生成短命
  `CLOUD_MEPHITIC`，核心效果为对无毒抗目标施加混乱。“迷瘴云”用机制
  导向词区分 Noxious 和历史 Miasma；“混乱云”会过度以机制替代原名。
  证据：`spl-data.h:331`、`dat/descript/spells.txt:1321`、
  `beam.cc:3133`、`cloud.cc:1090`。
- `SPELL_POISONOUS_CLOUD`：5 级怪物法术，产生 `CLOUD_POISON`，具有毒性
  直击、路径和终点毒云，并造成毒伤与中毒。“毒云”直接、准确。
  证据：`spl-data.h:465`、`zap-data.h:67`、
  `beam.cc:2451`、`cloud.cc:1146`。
- `SPELL_NOXIOUS_CLOUD`：沼泽龙的大型呼气云，同样生成
  `CLOUD_MEPHITIC`，零直伤、主效果混乱；“毒瘴云”与“毒瘴吐息”一致，
  并避免和 Poisonous Cloud 重名。证据：`spl-data.h:1366`、
  `mon-spell.h:320`、`zap-data.h:52`。
- `SPELL_INK_CLOUD`：海怪在水中以自身为中心生成 opaque、无伤害的浓墨，
  主要遮挡视线。“墨云”准确且不暗示伤害。证据：`spl-data.h:1796`、
  `mon-cast.cc:7837`、`cloud.cc:176`。
- `SPELL_PETRIFYING_CLOUD`：石化牛呼出的钙化尘沿路径生成
  `CLOUD_PETRIFY`；云本身无伤害，持续暴露会石化。“石化云”保留核心
  玩法效果。证据：`spl-data.h:2007`、`zap-data.h:285`、
  `cloud.cc:1121`。
- `SPELL_SPECTRAL_CLOUD`：`CLOUD_SPECTRAL` 会伤害非亡灵，并逐渐生成
  短命灵体亡灵；“幽灵云”在复合词中可表示 spectral 属性，不必理解为
  单只 ghost。证据：`spl-data.h:2175`、`beam.cc:3066`、
  `cloud.cc:628`、`cloud.cc:660`。
- `SPELL_FLAMING_CLOUD`：火蟹使用的现行法术，沿路径及终点产生
  `CLOUD_FIRE` 火焰伤害云；“燃烧云”与已移除 Fire cloud 保持身份区分。
  证据：`spl-data.h:2770`、`zap-data.h:467`、
  `beam.cc:3028`。
- `SPELL_MIASMA_CLOUD`、`SPELL_POISON_CLOUD`、`SPELL_FIRE_CLOUD`、
  `SPELL_STEAM_CLOUD`：当前只有 TAG 34 `AXED_SPELL`、removed set 和标题
  映射；不能从现行同名 cloud type 或其他能力反推历史机制。证据：
  `spl-data.h:4712`、`spl-util.cc:2560`、`spl-util.cc:2582`、
  `spl-util.cc:2586`、`spl-util.cc:2608`。
- `SPELL_CLOUD_CONE`：当前同样只有 TAG 34 兼容占位；英文语法是 Cloud
  修饰 Cone，不属于 `X Cloud` 后缀系列。证据：`spl-data.h:4720`、
  `spell-type.h:402`、`spl-util.cc:2537`。

### 附带描述问题

- `Mephitic Cloud`：中文遗漏脆弱瓶爆炸的投送方式，并把英文
  `creatures` 缩窄为“怪物”。
- `Petrifying Cloud`：中文把“受尘雾影响超过片刻才石化”的触发条件误译
  成“被石化较长时间”。
- `Flaming Cloud`：中文遗漏英文 `large` 的规模信息。
- `Poisonous Cloud`：中文遗漏英文 `great` 的规模信息。

### 落地状态

- [x] 机制证据收集
- [x] 翻译审阅裁定
- [x] 单一翻译写入者落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-015`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T155003270263000+0800-32795-ed4f20cfc60f`。

## 校准批次：Dispersal

### 裁定

| 英文名 | 当前中文名 | 裁定 | 置信度 |
|---|---|---|---|
| Dispersal | 空间驱离 | 保留 | 高 |

`SPELL_DISPERSAL` 是 6 级位移法术，以施法者为中心作用于附近生物。
目标若未抵抗意志便被传送到远处；即使抵抗成功，也仍会被强制闪送较短
距离。受影响的怪物还会进行一次独立的意志检定，失败时因空间扭曲而
混乱。证据：`spl-data.h:1151`、`spl-cast.cc:1408`、
`spl-cast.cc:2537`、`spl-transloc.cc:1738`、
`dat/descript/spells.txt:547`。

“空间驱离”准确表达空间位移与使目标远离的机制，也与解除魔法效果的
`Dispel → 驱散` 清楚区分；因此维持 `D-A-042`，拒绝恢复旧译“驱散”。

### 附带描述问题

原中文描述含“传送掉”“会被……被闪送”“被空间的扭曲所混乱”等
病句，且没有清楚表达混乱来自独立的意志检定。本批已按英文描述和实现
修正，不改变 TextDB 键。

### 落地状态

- [x] 机制证据收集
- [x] 翻译审阅裁定
- [x] 单一翻译写入者落地
- [x] translation profile
- [x] 既有实体裁定复核（`D-A-042`）

## 校准批次：Mesmerise

### 裁定

| 英文名 | 原中文名 | 裁定中文名 | 置信度 |
|---|---|---|---|
| Mesmerise | 催眠 | 迷魂 | 高 |

`SPELL_MESMERISE` 是 5 级怪物诅咒法术，对视野内所有敌人进行意志
检定。失败的冒险者会被施法者迷住，无法主动向远离施法者的方向移动；
其他生物则获得 `ENCH_DAZED`，无法行动。离开施法者视野会解除玩家的
移动限制。证据：`spl-data.h:1985`、`mon-cast.cc:5971`、
`mon-cast.cc:6041`、`movement.cc:852`、`behold.cc:150`、
`dat/descript/spells.txt:1327`。

旧译“催眠”会使玩家预期睡眠效果，但实现既不施加睡眠，也不使用睡眠
抗性；“魅惑”又容易与 charming 和阵营转化混淆。“迷魂”准确表达
`entrance/mesmerise` 的心智攫取效果，并与既有“迷魂宝珠”一致。

### 关联术语

为避免法术名与同一机制的状态、装备和界面文本分裂，本批同时将直接表示
`mesmerise/mesmerism` 的“催眠”统一为“迷魂”；自然句中的“迷住”
按中文语法保留。旧记录中“L2”及“全部 12 处”的说法已过时，由
`D-A-043` 取代。

### 落地状态

- [x] 机制证据收集
- [x] 翻译审阅裁定
- [x] 单一翻译写入者落地
- [x] translation profile
- [x] 实体与关联术语裁定登记（`D-A-043`）

Dispersal 与 Mesmerise 校准批次验证结果：
`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T155659431750000+0800-47686-8cbecea16c3d`。本批裁定后的
`docs/glossary.md` SHA-256 为
`e71f034792ca67686c5de48a6d467ca27ce0dbf8ab8f67ce64061344502b48df`；
重新生成后的 511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`46ae59b963872f6ac9908d06fae38123873e47e64ee851175d18e6cc0eb4e7c0`。

## Call 词形系列

系列结论：10 项均为现行法术。`call/call upon` 表示呼唤既有实体、号令
盟友或祈请力量时保留“呼唤”；`call down` 是“降下”的短语动词，不属于
同一中文词根。9 项保留，`Druid's Call` 因实际召回同层既有林地生物而由
“德鲁伊召唤”改为“德鲁伊呼唤”。

| Enum | 等级 / 学派 / flags | 使用者 | 原中文名 | 裁定中文名 | 裁定 |
|---|---|---|---|---|---|
| `SPELL_CALL_CANINE_FAMILIAR` | 3 / 召唤 / `none` | 玩家 | 呼唤犬类使魔 | 呼唤犬类使魔 | 保留 |
| `SPELL_CALL_DOWN_DAMNATION` | 9 / 咒法 / `target, unholy, needs_tracer, monster` | 怪物 | 降下天谴 | 降下天谴 | 保留 |
| `SPELL_CALL_DOWN_LIGHTNING` | 4 / 咒法、气 / `target, monster` | 怪物 | 降下闪电 | 降下闪电 | 保留 |
| `SPELL_CALL_IMP` | 2 / 召唤 / `unholy` | 玩家 | 呼唤小恶魔 | 呼唤小恶魔 | 保留 |
| `SPELL_CALL_LOST_SOULS` | 5 / 召唤、死灵 / `unholy, monster` | 怪物 | 呼唤迷失灵魂 | 呼唤迷失灵魂 | 保留 |
| `SPELL_CALL_OF_CHAOS` | 7 / 诅咒 / `chaotic, monster` | 怪物 | 混沌呼唤 | 混沌呼唤 | 保留 |
| `SPELL_CALL_TIDE` | 7 / 位移 / `monster` | 怪物 | 呼唤潮汐 | 呼唤潮汐 | 保留 |
| `SPELL_DRAGON_CALL` | 9 / 召唤 / `none` | 玩家 | 龙之呼唤 | 龙之呼唤 | 保留 |
| `SPELL_DRUIDS_CALL` | 6 / 召唤 / `monster` | 怪物 | 德鲁伊召唤 | 德鲁伊呼唤 | 重译 |
| `SPELL_HUNTING_CALL` | 6 / 诅咒 / `monster, selfench` | 怪物 | 狩猎呼唤 | 狩猎呼唤 | 保留 |

### 逐项证据卡

- `SPELL_CALL_CANINE_FAMILIAR`：召出与法术威力同步成长的犬神；重施会
  治疗、清除中毒并强化下一次攻击。“呼唤犬类使魔”忠实于标题及施法
  消息中的 call，保留。证据：`spl-data.h:1084`、
  `spl-summoning.cc:235`、`dat/descript/spells.txt:262`。
- `SPELL_CALL_DOWN_DAMNATION`：无需直射地对指定敌人及相邻格造成无视
  防护的天谴伤害，部分能施放天谴的生物免疫。“降下天谴”准确体现
  `call down` 与强度，保留。证据：`spl-data.h:487`、
  `spl-cast.cc:2502`、`beam.cc:6797`、`dat/descript/spells.txt:272`。
- `SPELL_CALL_DOWN_LIGHTNING`：无需直射地以闪电轰击远处目标，近身目标
  不可选。“降下闪电”准确，保留。证据：`spl-data.h:498`、
  `mon-cast.cc:3611`、`dat/descript/spells.txt:280`。
- `SPELL_CALL_IMP`：从地狱呼来持矛小恶魔，武器质量随法术威力提高。
  “呼唤小恶魔”保留 Call 与 Summon 的命名区别。证据：
  `spl-data.h:734`、`spl-summoning.cc:1096`、
  `dat/descript/spells.txt:286`。
- `SPELL_CALL_LOST_SOULS`：召出 2–3 个迷失灵魂，能挽救强大亡灵或把
  垂死活物转为幽灵形态。“呼唤迷失灵魂”准确，保留。证据：
  `spl-data.h:2198`、`mon-cast.cc:8330`、
  `dat/descript/spells.txt:292`。
- `SPELL_CALL_OF_CHAOS`：祈请混沌之力影响附近盟友，多数为增益，少数
  会反噬。“混沌呼唤”准确表达 call upon，保留。证据：
  `spl-data.h:2454`、`mon-cast.cc:3071`、
  `dat/descript/spells.txt:298`。
- `SPELL_CALL_TIDE`：改变大片水域潮汐，最终令整层水域涨潮，施法者附近
  涨得更高。“呼唤潮汐”准确，保留。证据：`spl-data.h:1774`、
  `mon-cast.cc:7821`、`dat/descript/spells.txt:305`。
- `SPELL_DRAGON_CALL`：向龙域发出持续呼唤，龙会逐一应召并持续消耗
  施法者法力。“龙之呼唤”准确，保留。证据：`spl-data.h:2576`、
  `spl-summoning.cc:504`、`dat/descript/spells.txt:594`。
- `SPELL_DRUIDS_CALL`：把同层既有林地生物移到目标附近并令其参战，不会
  创造召唤物。“德鲁伊召唤”会误导为生成生物，重译为“德鲁伊呼唤”。
  被拒方案：“德鲁伊召回”虽贴近实现，却偏离英文标题稳定意象。
  证据：`spl-data.h:1840`、`mon-cast.cc:2878`、
  `mon-cast.cc:4223`、`dat/descript/spells.txt:623`。
- `SPELL_HUNTING_CALL`：发出可被沉默阻止的狩猎号令，使附近同类盟友
  获得加速移动效果。“狩猎呼唤”准确，保留。证据：
  `spl-data.h:2816`、`mon-cast.cc:2976`、
  `dat/descript/spells.txt:976`。

十项英文与中文描述键均存在。中文描述整体语义一致；本批同时修复犬类
使魔、降下天谴、呼唤小恶魔、迷失灵魂、呼唤潮汐、龙之呼唤和狩猎呼唤
共 7 项描述
中的机制遗漏、范围误写或生硬表述。

### 落地状态

- [x] 机制证据收集
- [x] 翻译审阅裁定
- [x] 单一翻译写入者落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-016`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T160443184505000+0800-60545-9db1ba2ba80d`。本批裁定后的
`docs/glossary.md` SHA-256 为
`0abeba2a2d9ad32a2d3891389d4b6a14848e7e27600b35330887aa24defed6de`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`240df3fc2e2a6cce722ad4294c122385b5f8712be7bb0c7f2805b9f922d00dfa`。

## Summon 词形系列（已完成）

边界：英文标题中含独立 `Summon` 词形，共 42 项；其中 34 项现行、
8 项 `TAG_MAJOR_VERSION == 34` 已移除兼容记录。`Call` 系列、`Recall`
以及仅因学派为 Summoning 而不含该标题词形的法术均不在本系列。遵守
“完整系列审完后再落地”的规则，42 项裁定齐备后才一次性修改本系列
标题、关联描述与直接引用实体的文本。

### 首批：现行非 `monster` flag 成员（8/42）

这 8 项均有英文和中文描述。flags 不含 `monster` 只说明玩家施法路径
存在；其中若干也可由怪物使用，使用者字段以实际调度为准。

| Enum | 等级 / 学派 / flags | 实际使用者 | 当前译名 | 初步裁定 | 置信度 |
|---|---|---|---|---|---|
| `SPELL_SUMMON_SMALL_MAMMAL` | 1 / 召唤 / `none` | 玩家、怪物 | 召唤小型哺乳动物 | 保留 | 高 |
| `SPELL_SUMMON_HORRIBLE_THINGS` | 8 / 召唤 / `unholy, chaotic, mons_abjure` | 玩家、怪物 | 召唤恐怖之物 | 保留 | 高 |
| `SPELL_SUMMON_ICE_BEAST` | 3 / 冰、召唤 / `none` | 玩家、怪物 | 召唤冰兽 | 保留 | 高 |
| `SPELL_SUMMON_HYDRA` | 7 / 召唤 / `mons_abjure` | 玩家、怪物 | 召唤多头蛇 | 保留 | 高 |
| `SPELL_SUMMON_FOREST` | 5 / 召唤、位移 / `none` | 玩家 | 召唤森林 | 保留 | 高 |
| `SPELL_SUMMON_MANA_VIPER` | 5 / 召唤、诅咒 / `mons_abjure` | 玩家、怪物 | 召唤魔力蝰蛇 | 重译为“召唤魔力毒蛇” | 高 |
| `SPELL_SUMMON_CACTUS` | 6 / 召唤 / `none` | 玩家 | 召唤仙人掌巨人 | 保留 | 高 |
| `SPELL_SUMMON_SEISMOSAURUS_EGG` | 4 / 召唤、土 / `none` | 玩家 | 召唤震龙蛋 | 重译为“召唤地震龙蛋” | 高 |

- `Summon Small Mammal` 召出老鼠、蝙蝠或短尾矮袋鼠，法术威力提高出现
  短尾矮袋鼠的概率；标题完整保留 Small 与实体类别。
- `Summon Horrible Things` 打开通往深渊的门并召来至少两个憎恶，同时
  令施法者承受 Doom 风险；“恐怖之物”忠实于刻意泛称的原名。
- `Summon Ice Beast` 召出强度随法术威力变化的冰兽；标题直接复用实体名。
- `Summon Hydra` 召出短暂作战的多头蛇，法术威力决定头数；标题不需要
  加入持续时间或头数细节。
- `Summon Forest` 将森林位面与当前世界强行交叠，召出森林之灵并唤醒
  树木；虽然效果不只一个生物，“召唤森林”准确保留法术的宏观中心意象。
- `Summon Mana Viper` 召出咬击带反魔法效果的魔力毒蛇；旧标题没有复用
  当前实体名，因此改为“召唤魔力毒蛇”。
- `Summon Cactus Giant` 召出会反伤近战攻击者的仙人掌巨人，高威力会
  召来更老练强壮的个体；标题准确。
- `Summon Seismosaurus Egg` 召出需施法者相邻守护数回合才会孵化的
  地震龙蛋；改名后既复用实体名，也保留对象是“蛋”而非直接召唤地震龙。

描述审阅发现并已修正两项明确 Needs Fix：

- `Summon Horrible Things` 中文仍声称会损失智力，却遗漏当前效果会积累
  Doom 风险。数量随法术威力提高的趋势在实现中仍存在，但当前英文描述
  不再陈述该细节；本批已删除旧智力机制并完整恢复 Doom 后果。
- `Summon Mana Viper` 的“迅速耗掉敌人几乎所有的魔力”把
  `nearly any foe` 错解为“几乎所有魔力”；应改为该咬击几乎能影响
  任何敌人的魔力储备；本批已按英文语义修正。

证据：`spl-data.h:408`、`spl-data.h:566`、`spl-data.h:712`、
`spl-data.h:1974`、`spl-data.h:2510`、`spl-data.h:2598`、
`spl-data.h:3614`、`spl-data.h:4385`；`spl-summoning.cc:193`、
`spl-summoning.cc:297`、`spl-summoning.cc:363`、
`spl-summoning.cc:459`、`spl-summoning.cc:675`、
`spl-summoning.cc:1402`、`spl-summoning.cc:1482`、
`spl-summoning.cc:4659`；`dat/descript/spells.txt:2081`、
`dat/descript/spells.txt:2123`、`dat/descript/spells.txt:2147`、
`dat/descript/spells.txt:2154`、`dat/descript/spells.txt:2159`、
`dat/descript/spells.txt:2169`、`dat/descript/spells.txt:2197`、
`dat/descript/spells.txt:2211`。

### 其余现行成员（34/42）

| Enum | 当前译名 | 裁定 | 建议译名 | 置信度 |
|---|---|---|---|---|
| `SPELL_SUMMON_DEMON` | 召唤恶魔 | 保留 | 召唤恶魔 | 高 |
| `SPELL_SUMMON_GREATER_DEMON` | 召唤高等恶魔 | 重译 | 召唤高等恶魔 | 高 |
| `SPELL_SUMMON_DRAGON` | 召唤巨龙 | 保留 | 召唤巨龙 | 高 |
| `SPELL_SUMMON_UFETUBUS` | 召唤乌菲图布斯 | 重译 | 召唤乌菲特布斯 | 高 |
| `SPELL_SUMMON_SIN_BEAST` | 召唤罪兽 | 重译 | 召唤罪孽兽 | 高 |
| `SPELL_SUMMON_UNDEAD` | 召唤亡灵 | 保留 | 召唤亡灵 | 高 |
| `SPELL_SUMMON_DRAKES` | 召唤幼龙 | 保留 | 召唤幼龙 | 高 |
| `SPELL_SUMMON_MUSHROOMS` | 召唤蘑菇 | 保留 | 召唤蘑菇 | 高 |
| `SPELL_WATER_ELEMENTALS` | 召唤水元素 | 保留 | 召唤水元素 | 高 |
| `SPELL_SUMMON_EYEBALLS` | 召唤眼球 | 保留 | 召唤眼球 | 高 |
| `SPELL_EARTH_ELEMENTALS` | 召唤地元素 | 保留 | 召唤地元素 | 高 |
| `SPELL_AIR_ELEMENTALS` | 召唤气元素 | 保留 | 召唤气元素 | 高 |
| `SPELL_FIRE_ELEMENTALS` | 召唤火元素 | 保留 | 召唤火元素 | 高 |
| `SPELL_FAKE_MARA_SUMMON` | 玛拉召唤 | 保留 | 玛拉召唤 | 中高 |
| `SPELL_SUMMON_ILLUSION` | 召唤幻象 | 保留 | 召唤幻象 | 高 |
| `SPELL_SUMMON_MORTAL_CHAMPION` | 召唤凡人冠军 | 保留 | 召唤凡人冠军 | 中高 |
| `SPELL_SUMMON_HOLIES` | 召唤圣灵 | 重译 | 召唤神圣生物 | 高 |
| `SPELL_SUMMON_MINOR_DEMON` | 召唤次级恶魔 | 保留 | 召唤次级恶魔 | 高 |
| `SPELL_SUMMON_VERMIN` | 召唤害虫 | 保留 | 召唤害虫 | 高 |
| `SPELL_SUMMON_EMPEROR_SCORPIONS` | 召唤帝蝎 | 重译 | 召唤帝王蝎 | 高 |
| `SPELL_SUMMON_SCARABS` | 召唤圣甲虫 | 保留 | 召唤圣甲虫 | 高 |
| `SPELL_SUMMON_EXECUTIONERS` | 召唤行刑者 | 重译 | 召唤处刑人 | 高 |
| `SPELL_SUMMON_TZITZIMITL` | 召唤齐齐米特尔 | 保留 | 召唤齐齐米特尔 | 高 |
| `SPELL_SUMMON_HELL_SENTINEL` | 召唤地狱哨兵 | 保留 | 召唤地狱哨兵 | 高 |
| `SPELL_SUMMON_SPIDERS` | 召唤蜘蛛 | 保留 | 召唤蜘蛛 | 高 |
| `SPELL_SUMMON_SCORPIONS` | 召唤蝎子 | 保留 | 召唤蝎子 | 高 |

六项重译均来自当前实体词不一致，而非对机制的自由改名：

- `greater demon` 在现有语体术语中为“高等恶魔”，“高级恶魔”生硬；
- `ufetubus → 乌菲特布斯`、`sin beast → 罪孽兽`、
  `emperor scorpion → 帝王蝎`、`Executioner → 处刑人` 均已有当前实体
  映射，法术标题应直接复用；
- `Summon Holies` 实际召出天使、智天使、德瓦或奥法等神圣生物；
  “圣灵”会误示为灵体或特定宗教概念，改为“召唤神圣生物”。

首批中的两项初步裁定据实体表复核后修正：

- `Summon Mana Viper`：魔力蝰蛇 → **魔力毒蛇**；
- `Summon Seismosaurus Egg`：震龙蛋 → **地震龙蛋**。

这两项分别复用 `mana viper → 魔力毒蛇` 与
`seismosaurus egg → 地震龙蛋` 的当前实体映射。标题仍准确保留召唤
对象及“蛋”的机制重点。

其余现行标题与召出的实体、群体或位面效果一致。特殊形态
`Mara Summon` 是玛拉制造自身幻象的内部怪物法术，保留原名结构；
`Summon Forest` 虽不只生成单一生物，但标题准确概括森林位面交叠的
整体效果；`Summon Mortal Champion` 的 champion 与项目既有“冠军”
用语一致。

### 已移除兼容成员（42/42）

| Enum | 英文名 | 当前译名 | 裁定 |
|---|---|---|---|
| `SPELL_FAKE_RAKSHASA_SUMMON` | Rakshasa Summon | 召唤罗刹 | 暂缓术语（恢复时复审） |
| `SPELL_IRON_ELEMENTALS` | Summon Iron Elementals | 召唤铁元素 | 暂缓术语（恢复时复审） |
| `SPELL_SUMMON_BUTTERFLIES` | Summon Butterflies | 召唤蝴蝶 | 暂缓术语（恢复时复审） |
| `SPELL_SUMMON_ELEMENTAL` | Summon Elemental | 召唤元素 | 暂缓术语（恢复时复审） |
| `SPELL_SUMMON_RAKSHASA` | Summon Rakshasa | 召唤罗刹 | 暂缓术语（恢复时复审） |
| `SPELL_SUMMON_TWISTER` | Summon Twister | 召唤旋风 | 暂缓术语（恢复时复审） |
| `SPELL_VAMPIRE_SUMMON` | Vampire Summon | 召唤吸血鬼 | 暂缓术语（恢复时复审） |
| `SPELL_SUMMON_SWARM` | Summon swarm | 召唤虫群 | 暂缓术语（恢复时复审） |

八项均只有 TAG 34 `AXED_SPELL` 占位、removed set 与标题映射，没有当前
描述和实现；不能从现行同名实体或其他召唤法术反推历史机制。它们不参与
现行 `Summon → 召唤` 词根与实体一致性的计数，若恢复须按恢复版本重审。

### 附带描述修正

除首批已记录的两项外，本批已同步修正以下确定性问题：

- `Summon Ufetubus`、`Summon Sin Beast`、`Summon Drakes`、
  `Summon Earth Elementals`、`Summon Mana Viper`、
  `Summon Emperor Scorpions`、`Summon Executioners`、
  `Summon Tzitzimitl`、`Summon Seismosaurus Egg` 的对象名与当前实体
  映射不一致；
- `Summon Mushrooms` 的 `wandering mushroom` 与 `deathcap` 未复用
  “游走蘑菇”“死亡菌”实体名；
- `Summon Undead` 将 wraith 译成“幽灵”并把 lesser undead 生硬译作
  “次要亡灵”；
- `Summon Mortal Champion` 遗漏光辉者、最强且最快，以及本地会响应的
  两类具体生物；
- `Summon Minor Demon` 把 minor demon 缩成“小恶魔”，会与 imp 混淆；
- `Mara Summon` 与 `Summon Illusion` 含“与原先的有同样……”病句；
- `Summon Vermin` 标点错误；`Summon Cactus Giant` 语序生硬；
- 魔力毒蛇出现消息、Execution 状态和马科列布神罚文本仍分别使用
  “魔力蝰蛇”“行刑者”“处决者”，本批一并统一到现行实体名。

完整系列裁定：34 项现行标题中 26 项保留、8 项重译；8 项已移除兼容
标题全部因机制证据不足而暂沿用。名称、描述与直接关联实体文本已由
单一翻译写入者一次性落地，避免同一词根出现发布中的过渡状态。

### 落地状态

- [x] 42/42 机制证据与名称裁定
- [x] 单一翻译写入者完整系列落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-017`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T161824296144000+0800-88221-3612fab09f35`。本批裁定后的
`docs/glossary.md` SHA-256 为
`7536042fedba3d2b7d933e51babaeb079b7acda69d8b20f26bd573d4bb4faf9f`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`7d23cc171b690aa07c54d40963ba751c894a65cdf64f0c7cf43c7992b1917228`。

## Breath 词形系列（已完成）

边界：英文标题中含独立 `Breath` 词形，共 22 项；其中 20 项现行、
2 项 `TAG_MAJOR_VERSION == 34` 已移除兼容。现行成员中 14 项有法术
TextDB 描述，8 项玩家能力另由 ability TextDB 提供或补充描述；4 个
地狱巨蛇内部法术与 `Rust Breath`、`Golden Breath` 依实现和调用路径
核对。两项已移除兼容成员没有当前描述或实现。

| Enum | 生命周期 | 当前译名 | 核心效果证据 | 裁定 |
|---|---|---|---|---|
| `SPELL_MIASMA_BREATH` | 现行 | 瘴气吐息 | 瘴气云；使活物中毒并可能减速 | 保留 |
| `SPELL_CAUSTIC_BREATH` | 现行 | 腐蚀吐息 | 浓酸喷流；沿途留腐蚀云并腐蚀目标 | 保留 |
| `SPELL_FIRE_BREATH` | 现行 | 火焰吐息 | 对目标喷吐火焰 | 保留 |
| `SPELL_SEARING_BREATH` | 现行 | 灼热吐息 | 火焰束；终点留下火焰云 | 保留 |
| `SPELL_CHAOS_BREATH` | 现行 | 混沌吐息 | 产生大片混沌精能烟云 | 保留 |
| `SPELL_COLD_BREATH` | 现行 | 寒冷吐息 | 凝聚的冰寒气流 | 重译为“寒霜吐息” |
| `SPELL_GLACIAL_BREATH` | 现行 | 冰川吐息 | 强力冰霜波；被击杀者封入耐久冰块 | 保留 |
| `SPELL_HOLY_BREATH` | 现行 | 神圣吐息 | 神圣火焰云；克制亡灵与恶魔，不伤神圣生物 | 保留 |
| `SPELL_SERPENT_OF_HELL_GEH_BREATH` | 现行 | 火焚地狱蛇之吐息 | 欣嫩谷变体随机使用火焰吐息、熔岩箭或火球 | 重译为“欣嫩谷地狱巨蛇吐息” |
| `SPELL_SERPENT_OF_HELL_COC_BREATH` | 现行 | 冰狱蛇之吐息 | 悲叹河变体随机使用寒冷吐息、寒风或急冻 | 重译为“悲叹河地狱巨蛇吐息” |
| `SPELL_SERPENT_OF_HELL_DIS_BREATH` | 现行 | 铁城蛇之吐息 | 铁城变体随机使用铁弹、水银箭或腐蚀箭 | 重译为“铁城地狱巨蛇吐息” |
| `SPELL_SERPENT_OF_HELL_TAR_BREATH` | 现行 | 悲叹地狱蛇之吐息 | 塔尔塔罗斯变体随机使用幽灵火球、瘴气或毒箭 | 重译为“塔尔塔罗斯地狱巨蛇吐息” |
| `SPELL_NOXIOUS_BREATH` | 现行 | 毒瘴吐息 | 毒雾使未抵抗毒素者混乱；范围与持续时间成长 | 保留 |
| `SPELL_COMBUSTION_BREATH` | 现行 | 燃烧吐息 | 挥发余烬接触生物后爆炸；使用者免疫 | 重译为“爆燃吐息” |
| `SPELL_NULLIFYING_BREATH` | 现行 | 消魔吐息 | 驱散魔法效果并施加反魔法；使用者免疫 | 保留 |
| `SPELL_STEAM_BREATH` | 现行 | 蒸汽吐息 | 蒸汽烫伤并留下遮挡视线的蒸汽云 | 保留 |
| `SPELL_MUD_BREATH` | 现行 | 泥浆吐息 | 泥球击退；泥泞阻碍移动并可能使攻击失手 | 保留 |
| `SPELL_GALVANIC_BREATH` | 现行 | 电击吐息 | 电流经目标及与其相连的生物传导 | 保留 |
| `SPELL_RUST_BREATH` | 现行 | 锈蚀吐息 | 堡垒蟹形态喷出锈蚀云 | 保留 |
| `SPELL_GOLDEN_BREATH` | 现行 | 金龙吐息 | 非龙人龙形态的火、冰伤害与沿途毒云 | 保留 |
| `SPELL_DRACONIAN_BREATH` | 已移除兼容 | 龙人吐息 | 无当前描述或实现 | 暂缓术语（恢复时复审） |
| `SPELL_SERPENT_OF_HELL_BREATH_REMOVED` | 已移除兼容 | 地狱古蛇吐息 | 无当前描述或实现 | 暂缓术语（恢复时复审） |

系列结论：20 项现行标题中 14 项保留、6 项重译。`Cold Breath` 改为
“寒霜吐息”，复用 `Breathe Frost → 吐息寒霜`，并与能将被击杀者封入
冰块的 `Glacial Breath → 冰川吐息` 保持区别。`Combustion Breath`
改为“爆燃吐息”，明确挥发余烬逐目标爆炸的核心特征。其余 4 项重译
让内部标题完整复用 `Serpent of Hell` 的分支限定实体名。
`Golden Breath → 金龙吐息` 由非龙人龙形态专用，其实现正是金龙式
火、冰、毒三重吐息，因此保留上下文明确的现译。

描述审阅同步修正两项 Needs Fix：

- `Miasma Breath` 原中文称影响“任何生物”，遗漏英文与机制限定的
  living creatures；现改为“活物”。
- `Noxious Breath` 的 vapour 原译成“蒸汽”，与 Steam Breath 混淆；
  现改为“毒雾”，并保留毒素抵抗、混乱和等级成长条件。

证据：`spl-data.h:1489`、`spl-data.h:1558`—`1628`、
`spl-data.h:1929`、`spl-data.h:2676`—`2712`、
`spl-data.h:3857`—`3935`、`spl-data.h:4475`—`4486`、
`spl-util.cc:2450`—`2474`、`spl-zap.cc:49`、`spl-zap.cc:128`—`159`、
`spl-zap.cc:176`、`zap-data.h:255`—`447`、
`zap-data.h:1101`—`1116`、`zap-data.h:1221`、
`zap-data.h:1352`、`zap-data.h:1976`—`2021`、
`zap-data.h:2622`—`2670`、`ability.cc:766`—`776`、
`ability.cc:4425`—`4427`、`transform.cc:809`—`821`、
`spl-damage.cc:3232`—`3260`。

### 落地状态

- [x] 22/22 机制证据与名称裁定
- [x] 单一翻译写入者完整系列落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-018`）

验证结果：首次 translation profile（Run ID
`20260725T162450588680000+0800-99223-1db80705e827`）因同批新增的
`Cold Breath` 与 `Combustion Breath` 裁定尚未重新导出
`docs/glossary.utf8` 而失败；重新生成派生术语表后复测通过，0 项失败。
最新通过的 Run ID 为
`20260725T162619124811000+0800-2244-1db80705e827`。本批裁定后的
`docs/glossary.md` SHA-256 为
`af5f6da8cb91917fef04a63bf9f797af0cb8839717e754e04781cb4f9cc61496`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`688fb5c82db1bca051c42f179fe491817c3cf94e419f8596f715d93fd938b224`。

## Dart 词形系列

边界：英文标题以独立 `Dart` 结尾的 2 项现行法术，无已移除兼容成员。

| Enum | 等级 / 学派 / flags | 使用者 | 原中文名 | 裁定中文名 | 裁定 |
|---|---|---|---|---|---|
| `SPELL_MAGIC_DART` | 1 / 咒法 / `dir_or_target, needs_tracer` | 玩家、怪物 | 魔法飞弹 | 魔法飞弹 | 保留 |
| `SPELL_SLUG_DART` | 1 / 咒法 / `dir_or_target, needs_tracer, monster` | 飞镖蛞蝓 | 弹丸飞镖 | 蛞蝓飞镖 | 重译 |

- `Magic Dart` 发射必中小型魔法射弹；zap 使用自动命中，标题和描述都把
  dart 作为魔法射弹意象。“魔法飞弹”准确且是稳定固定词形，不为形式
  统一改成“魔法飞镖”。
- `Slug Dart` 是飞镖蛞蝓的天生攻击，发射硬化甲壳质尖镖，zap 颜色还
  明确与蛞蝓自身颜色一致。“弹丸飞镖”把 slug 错解成 projectile slug，
  且“弹丸／飞镖”重复描述投射物；改为“蛞蝓飞镖”，保留使用者双关并
  与实体 `dart slug → 飞镖蛞蝓` 对应。

英中两项描述键均存在且机制一致，无需修改正文。证据：
`spl-data.h:41`、`spl-data.h:3104`、`spl-zap.cc:11`、
`spl-zap.cc:103`、`zap-data.h:563`、`zap-data.h:1524`、
`mon-spell.h:423`、`mon-spell.h:708`、`dat/descript/spells.txt:1209`、
`dat/descript/spells.txt:1920`。

### 落地状态

- [x] 2/2 机制证据与名称裁定
- [x] 单一翻译写入者完整系列落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-019`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T163018947719000+0800-11363-971a54b02563`。本批裁定后的
`docs/glossary.md` SHA-256 为
`5b97f68339de1634fbfd1f8fdaa783d23297a5ac0979bf1cce393eaed4fec04d`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`660ff3a19309d42de3109f6af54dab6c29613bd73064e7edb6c33f8dfe2ed759`。

## Arrow 词形系列

边界：英文标题以独立 `Arrow` 结尾的 4 项现行法术，无已移除兼容成员。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_POISON_ARROW` | 毒箭 | 剧毒魔法箭；少量直接伤害无视毒素抗性 | 保留 |
| `SPELL_STONE_ARROW` | 石箭 | 发射尖锐岩刺 | 保留 |
| `SPELL_PYRE_ARROW` | 烈火箭 | 附着液态火焰；持续造成无视护甲的火焰伤害 | 保留 |
| `SPELL_MERCURY_ARROW` | 汞矢 | 元素汞箭造成毒素伤害并可能溅射削弱效果 | 保留（辨识性例外） |

名称结论：常规采用 `Arrow → 箭`。`Mercury Arrow → 汞矢` 保留为
辨识性例外，因为 `Quicksilver Bolt` 已译为“水银箭”；两者的英文名称、
伤害类型和附加效果不同，统一成同一个中文标题会妨碍玩家识别。
其余三项准确表达英文标题，不在标题中额外添加原名没有的附着、持续伤害
或抗性机制。

描述审阅同步修正 4 项：以当前机制重译 Mercury 的过时气态汞描述，
补回箭矢冲击伤害、毒素免疫、削弱溅射与无视抗性；统一 Poison 的抗性
术语和少量直接伤害表述；修正 Pyre 的附着条件及语病；使 Stone 与
`sharp spine of rock` 对齐。

证据：`spl-data.h:778`、`spl-data.h:893`、`spl-data.h:1569`、
`spl-data.h:3226`、`zap-data.h:882`、`zap-data.h:994`、
`zap-data.h:1316`、`zap-data.h:2561`、`spl-cast.cc:1432`、
`spl-cast.cc:2090`、`beam.cc:4569`、`beam.cc:7525`。

### 落地状态

- [x] 4/4 机制证据与名称裁定
- [x] 单一翻译写入者描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-025`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T164427329781000+0800-36468-088c4f20c97e`。本批裁定后的
`docs/glossary.md` SHA-256 为
`5c7b299a9d61ee61b35910a6ef40c4644b35a5130b77736da9d13931b1ddcf72`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`1829b52622d79de772a3de6ac84fb9da0be2431cc3c774b35613e0e73629dbb0`。

## Flame/Flames 词形系列

边界：英文标题含独立 `Flame` 或 `Flames` 词形的 10 项法术；其中
7 项现行、3 项 `TAG_MAJOR_VERSION == 34` 已移除兼容。`Throw Flame`
已在 Throw 批次审阅，本批复用其机制未变化的证据且不重复计数；新增
审阅身份为 9 项。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_THROW_FLAME` | 现行 | 投掷火焰 | 抛出一小团火焰 | 保留（复用 D-C-021） |
| `SPELL_STICKY_FLAME` | 现行 | 黏着火焰 | 邻接黏着燃烧；移动可提前扑灭 | 保留 |
| `SPELL_HOLY_FLAMES` | 现行 | 神圣火焰 | 以神圣火环困住敌人 | 保留 |
| `SPELL_INNER_FLAME` | 现行 | 内焰 | 击中时释火，死亡时按体形爆炸 | 保留 |
| `SPELL_CLEANSING_FLAME` | 现行 | 净化之焰 | 以施法者为中心的神圣净化爆发 | 保留 |
| `SPELL_STOKE_FLAMES` | 现行 | 煽动火焰 | 召出会蔓延的炼狱 | 重译为“煽旺火焰” |
| `SPELL_FLAME_WAVE` | 现行 | 火焰波 | 引导逐步向外扩张的火焰波 | 保留 |
| `SPELL_RING_OF_FLAMES` | 已移除兼容 | 烈焰之环 | 无当前描述或实现 | 暂缓术语（恢复时复审） |
| `SPELL_CONJURE_FLAME` | 已移除兼容 | 召唤火焰 | 无当前描述或实现 | 暂缓术语（恢复时复审） |
| `SPELL_FLAME_TONGUE` | 已移除兼容 | 火焰之舌 | 无当前描述或实现 | 暂缓术语（恢复时复审） |

名称结论：9 项标题保留，`Stoke Flames` 重译为“煽旺火焰”。
`stoke` 是添燃料或拨动燃料使火势更旺；旧译“煽动火焰”套用了
“煽动情绪／事端”的常见搭配，既不自然，也弱化了火势增强的动作。
`Flame/Flames` 的核心语义稳定为“火焰”，
但自然的复合标题允许使用更凝练的“焰”或带强度色彩的“烈焰”，不应
机械统一字面后缀。`内焰`、`净化之焰` 与 `烈焰之环` 都没有改变原名
或机制指向。

描述审阅发现 2 项需要修正：`Inner Flame` 漏译目标每次被击中时也会
释放火焰；`Sticky Flame` 的非实体附着条件有多余空格和生硬语病。
其余 5 项现行描述与英文机制一致。

证据：`spl-data.h:701`、`spl-data.h:1918`、`spl-data.h:2018`、
`spl-data.h:3015`、`spl-data.h:3625`、`spl-data.h:3658`、
`spl-data.h:4689`、`spl-data.h:4730`—`4732`、
`dat/descript/spells.txt:361`、`dat/descript/spells.txt:698`、
`dat/descript/spells.txt:1015`、`dat/descript/spells.txt:1070`、
`dat/descript/spells.txt:2031`、`dat/descript/spells.txt:2052`、
`mon-cast.cc:8532`、`mon-cast.cc:8652`、
`spl-damage.cc:3798`—`3855`、`mon-explode.cc:317`—`392`。

### 落地状态

- [x] 10/10 名称裁定（9 项新增证据，1 项复用未变化证据）
- [x] 单一翻译写入者描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-026`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T164855022535000+0800-45680-95fedcbdcb73`。本批裁定后的
`docs/glossary.md` SHA-256 为
`f52c123564259105c5a6d64ed3d7f9d65a906ba6f043782276721fe3ca85f57b`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`1829b52622d79de772a3de6ac84fb9da0be2431cc3c774b35613e0e73629dbb0`。

## Form 词形系列

边界：英文标题以独立 `Form` 结尾的 6 项法术，全部为
`TAG_MAJOR_VERSION == 34` 已移除兼容记录；没有现行成员。

| Enum | 生命周期 | 当前译名 | 当前机制证据 | 裁定 |
|---|---|---|---|---|
| `SPELL_HYDRA_FORM` | 已移除兼容 | 多头蛇变形 | 无当前描述或实现 | 暂缓术语（恢复时复审） |
| `SPELL_SPIDER_FORM` | 已移除兼容 | 蜘蛛变形 | 无当前描述或实现 | 暂缓术语（恢复时复审） |
| `SPELL_ICE_FORM` | 已移除兼容 | 寒冰变形 | 无当前描述或实现 | 暂缓术语（恢复时复审） |
| `SPELL_STATUE_FORM` | 已移除兼容 | 石像变形 | 无当前描述或实现 | 暂缓术语（恢复时复审） |
| `SPELL_STORM_FORM` | 已移除兼容 | 风暴变形 | 无当前描述或实现 | 暂缓术语（恢复时复审） |
| `SPELL_DRAGON_FORM` | 已移除兼容 | 巨龙变形 | 无当前描述或实现 | 暂缓术语（恢复时复审） |

名称结论：六项都采用自然且一致的 `Form → 变形` 结构，并准确标出目标
形态；但当前源码只有 `AXED_SPELL` 身份。没有现行描述和实现时，不凭
历史记忆判断强度或附加机制，也不以现行护符变形系统反推旧法术重命名。

证据：511 项 inventory 的生命周期与描述存在性字段；
`spl-data.h:4733`—`4739` 的六项 `AXED_SPELL` 记录；
`spell-type.h` 中受 `TAG_MAJOR_VERSION == 34` 保护的独立身份。

### 落地状态

- [x] 6/6 生命周期证据与标题裁定
- [x] 无翻译资产修改
- [x] translation profile
- [x] 系列裁定登记（`D-C-027`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T165142383612000+0800-51642-6a3c231a76d9`。本批裁定后的
`docs/glossary.md` SHA-256 为
`b2d3de29d93544445001b1afca83b4312e23861a331cc08b426325af5986c2c5`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`1829b52622d79de772a3de6ac84fb9da0be2431cc3c774b35613e0e73629dbb0`。

## Poison/Poisonous 词形系列

边界：英文标题含独立 `Poison` 或 `Poisonous` 词形的 9 项法术；其中
5 项现行、4 项 `TAG_MAJOR_VERSION == 34` 已移除兼容。
`Poisonous Cloud`、`Poison Cloud` 与 `Poison Arrow` 已在既有批次审阅，
本批复用未变化证据且不重复计数；新增审阅身份为 6 项。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_POISONOUS_CLOUD` | 现行 | 毒云 | 生成致命毒云 | 保留（复用 D-C-015） |
| `SPELL_POISON_ARROW` | 现行 | 毒箭 | 剧毒魔法箭 | 保留（复用 D-C-025） |
| `SPELL_IGNITE_POISON` | 现行 | 点燃毒素 | 把附近毒素及毒性云雾转为液态火焰 | 保留 |
| `SPELL_SPIT_POISON` | 现行 | 喷毒 | 喷吐毒液；描述直接引用同名能力 | 重译为“喷吐毒液” |
| `SPELL_POISONOUS_VAPOURS` | 现行 | 毒气 | 瞬时毒气；任何毒素抗性均可免疫 | 保留 |
| `SPELL_CURE_POISON` | 已移除兼容 | 解毒术 | 无当前描述或实现 | 暂缓术语（恢复时复审） |
| `SPELL_IGNITE_POISON_SINGLE` | 已移除兼容 | 局部引爆毒素 | 无当前描述或实现 | 暂缓术语（恢复时复审） |
| `SPELL_POISON_WEAPON` | 已移除兼容 | 淬毒武器 | 无当前描述或实现 | 暂缓术语（恢复时复审） |
| `SPELL_POISON_CLOUD` | 已移除兼容 | 毒气云 | 无当前描述或实现 | 暂缓术语（恢复时复审；复用 D-C-015） |

名称结论：`Spit Poison` 重译为“喷吐毒液”，与其直接引用的同名能力、
能力描述及怪物施法消息统一；旧译“喷毒”过度缩略。其余标题保留，
`Poison/Poisonous` 根据名词结构自然采用“毒素／毒／淬毒”，不机械限定
为单一汉字词根。

描述审阅修正 2 项：`Ignite Poison` 将 poisoned creatures 从“有毒的
生物”纠正为“中毒的生物”，并明确两类毒性云雾；`Poisonous Vapours`
补回气体只存在于施法当回合，以及任何毒素抗性都可完全免疫的规则。

证据：`spl-data.h:465`、`spl-data.h:778`、`spl-data.h:1073`、
`spl-data.h:1422`、`spl-data.h:3237`、`spl-data.h:4676`、
`spl-data.h:4684` 与其余 AXED 记录；
`dat/descript/spells.txt:1032`、`dat/descript/spells.txt:1583`—
`1593`、`dat/descript/spells.txt:1983`；
`dat/descript/zh/ability.txt:6`、`dat/database/zh/monspell.txt:327`。

### 落地状态

- [x] 9/9 名称裁定（6 项新增证据，3 项复用未变化证据）
- [x] 单一翻译写入者名称与描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-028`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T165416323974000+0800-56496-e1215c094df5`。本批裁定后的
`docs/glossary.md` SHA-256 为
`8bf9969e96c966b80bd0ad1b6631e4ade79d1b8c629c14065090f63e61745547`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`1829b52622d79de772a3de6ac84fb9da0be2431cc3c774b35613e0e73629dbb0`。

## Dispel 词形系列

边界：英文标题以 `Dispel Undead` 为核心的 2 项现行法术，无已移除
兼容成员。

| Enum | 等级 / 使用者 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_DISPEL_UNDEAD` | 4 / 玩家 | 驱散亡灵 | 对相邻亡灵造成极大伤害 | 保留 |
| `SPELL_DISPEL_UNDEAD_RANGE` | 5 / 怪物 | 远程驱散亡灵 | 射程 4；远程重创亡灵 | 保留 |

名称结论：两项均保留。这里的 `Dispel → 驱散` 是破坏维系亡灵形体的
魔力，并非把亡灵推开或传送；因此“驱散亡灵”符合效果，也不会与
`Dispersal → 空间驱离` 混淆。Range 版以“远程”准确标出关键差别。

描述审阅将两项生硬的“干扰将亡灵的身体缚在一起的力量”改为
“扰乱维系亡灵形体的力量”，不改变伤害或目标机制。

证据：`spl-data.h:767`、`spl-data.h:3437`；
`dat/descript/spells.txt:537`—`545`；`spl-zap.cc` 的 zap 映射及
`zap-data.h` 的亡灵伤害配置。

### 落地状态

- [x] 2/2 机制证据与名称裁定
- [x] 单一翻译写入者描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-029`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T165720573835000+0800-63302-8e041c646575`。本批裁定后的
`docs/glossary.md` SHA-256 为
`d24c3375aea4350a6379bbc8e4b9bd4c1d3581abbd8ecf2bea530cff0caa78d6`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`1829b52622d79de772a3de6ac84fb9da0be2431cc3c774b35613e0e73629dbb0`。

## Maxwell's 专名系列

边界：英文标题以 `Maxwell's` 开头的 2 项现行法术，无已移除兼容成员。

| Enum | 等级 / 学派 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_MAXWELLS_COUPLING` | 8 / 空气 | 麦克斯韦之电容耦合 | 通道积累电荷并蒸发最近敌人 | 保留 |
| `SPELL_PILEDRIVER` | 3 / 传送 | 麦克斯韦之便携打桩机 | 压缩空间并将整列生物推向障碍物 | 保留 |

名称结论：两项均保留。`Maxwell → 麦克斯韦` 与项目中的同名物品一致，
所有格结构“麦克斯韦之……”自然统一。电容耦合准确使用电学术语；
便携打桩机则以机械比喻描述空间骤然舒张后把最远端敌人撞上障碍物的效果，
没有必要改成说明式标题。

描述审阅修正 2 项：电容耦合补回启动需要可见目标、释放时可能选中另一
敌人的规则；便携打桩机原中文仍误写成召唤移动桩锤，本批按当前英文与
实现恢复空间压缩、整列推进、碰撞目标及移动距离决定伤害的完整机制。

证据：`spl-data.h:3459`—`3466`、`spl-data.h:3946`、
`spl-damage.cc:4638`—`4691`、`spl-transloc.cc:2111`—`2287`、
`target.cc:2682`—`2727`。

### 落地状态

- [x] 2/2 机制证据与名称裁定
- [x] 单一翻译写入者描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-031`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T170149630085000+0800-73223-c75bc0af41a6`。本批裁定后的
`docs/glossary.md` SHA-256 为
`ab759ef1633510eb457075b8281741340d74a8edf0aef662cb40bdbeb13b68a8`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`1bace0bd3f53a8a79462dbd78324d9d8f828438d6f22bc82d8ea6297d5bb7f55`。

## Forge 词形系列

边界：英文标题以 `Forge` 开头的 4 项现行法术，无已移除兼容成员。

| Enum | 等级 / 学派 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_FORGE_LIGHTNING_SPIRE` | 4 / 锻造、气 | 锻造闪电尖塔 | 固定尖塔不时电击最远敌人 | 保留 |
| `SPELL_FORGE_BLAZEHEART_GOLEM` | 4 / 锻造、火 | 锻造炽心魔像 | 近战构装；外壳破坏后核心爆炸 | 保留 |
| `SPELL_MONARCH_BOMB` | 6 / 锻造、火 | 锻造君主炸弹 | 部署追踪小炸弹；再次施法引爆全体 | 保留 |
| `SPELL_PHALANX_BEETLE` | 6 / 锻造 | 锻造方阵甲虫 | 相邻时提高护甲；被分开后优先返回 | 保留 |

名称结论：四项均保留稳定的 `Forge X → 锻造X`。它们实际构建持续存在
的机械或元素造物，不是召来既存生物；各对象名也准确对应尖塔、魔像、
飞行炸弹工厂与护卫甲虫。

描述审阅发现四项均有旧版或缺失机制：闪电尖塔漏掉不规律攻击及最远目标
优先级；炽心魔像沿用“召唤者”且把 spellpower 误作“能量”；君主炸弹
仅余一句旧摘要；方阵甲虫漏掉啃咬、回归优先级及法术威力缩放。本批均已
按当前英文补齐。

证据：`spl-data.h:2521`—`2539`、`spl-data.h:4318`—`4325`、
`spl-data.h:4396`—`4403`；`dat/descript/spells.txt:735`—`775`；
相应锻造术召唤、构装 AI 与再次施法引爆实现。

### 落地状态

- [x] 4/4 机制证据与名称裁定
- [x] 单一翻译写入者描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-032`）

验证结果：覆盖 Maxwell's 与 Forge 当前差异的
`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T170409207345000+0800-77820-c75bc0af41a6`。本批裁定后的
`docs/glossary.md` SHA-256 为
`56b64a4ef05f5e2df77908c310d1bd2137c97734ad84378759880b69f90d0fd9`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`1bace0bd3f53a8a79462dbd78324d9d8f828438d6f22bc82d8ea6297d5bb7f55`。

## Iskenderun's 专名系列

边界：英文标题以 `Iskenderun's` 开头的 2 项现行法术。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_BATTLESPHERE` | 伊斯肯德伦之战斗球 | 随攻击法术向最重伤敌人发出必中齐射 | 重译为“伊斯肯德伦之战斗法球” |
| `SPELL_ISKENDERUNS_MYSTIC_BLAST` | 伊斯肯德伦之神秘冲击 | 范围物理冲击并击退受伤目标 | 保留 |

名称结论：专名稳定为“伊斯肯德伦”，所有格结构一致。“战斗法球”与
实体及运行时术语统一，也比普通“战斗球”更准确表达魔法构装；
“神秘冲击”准确概括爆炸与击退。

描述审阅同步恢复战斗法球的最重伤目标、必中齐射与穿透规则，并为神秘
冲击补回法术威力同时提高伤害和击退距离。

证据：对应 `spl-data.h` 条目、`dat/descript/spells.txt:1096`—`1109`、
战斗法球选敌实现及神秘冲击击退实现。

### 落地状态

- [x] 2/2 机制证据与名称裁定
- [x] 单一翻译写入者名称与描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-033`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T170725144407000+0800-84810-09af58b73919`。本批裁定后的
`docs/glossary.md` SHA-256 为
`ef666e6dcbf314881d6e99b708eec0e7380eb42d7a6b7e1ab59fc59e2d57ea37`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`950f6da3308eaea8f730f3559109c074197ed0ff80d3b8977808642efe8052a9`。

## Vhi's 专名系列

边界：英文标题以 `Vhi's` 开头的 2 项现行法术，无已移除兼容成员。

| Enum | 等级 / 学派 / flags | 使用者 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|---|
| `SPELL_ELECTRIC_CHARGE` | 4 / 气、传送 / `noisy, dir_or_target` | 玩家 | 维之电荷 | 冲到附近敌人身边，高命中近战并按距离、法术威力和物理伤害追加电击伤害 | 重译为“维之电击冲锋” |
| `SPELL_ELECTROLUNGE` | 4 / 气、传送 / `noisy, target, monster` | 怪物 | 维之电冲 | 使用同一空间冲锋实现，高命中近战并按法术威力追加电击伤害 | 重译为“维之电击突进” |

名称结论：专名稳定采用 `Vhi → 维`。“电荷”把 `Electric Charge` 的
charge 错解成静态电学名词，与实际冲向敌人的核心动作不符；“电击冲锋”
同时保留电属性和冲锋义。怪物版原名用 `lunge` 区分，译为“电击突进”
既保持系列关系，也避免生硬且含义不清的“电冲”。

描述审阅修正 2 项：玩家版的 `length of the charge` 是冲锋距离，不是
蓄力时长；怪物版中文仍描述早期“化作穿透性闪电并传送”的旧机制，现按
英文恢复冲向敌人、高命中近战、法术威力附伤、穿越危险格和置换生物。

证据：`spl-data.h:174`—`193`、`dat/descript/spells.txt:2352`—`2369`、
`spl-transloc.cc:546`—`818`、`mon-cast.cc:720`—`738`、
`melee-attack.cc:3862`—`3868`、`spl-damage.cc:4800`—`4803`。

### 落地状态

- [x] 2/2 机制证据与名称裁定
- [x] 单一翻译写入者名称与描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-034`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T171208090527000+0800-93263-f6015edd67a9`。本批裁定后的
`docs/glossary.md` SHA-256 为
`748251d091471b99094f1b3c5ac4650790436fb6d534006c960cd608dd3769be`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`2ba444c35624ab694f679a68438eeb7f77653e66ed611744db47f82c204ef7e9`。

## Cigotuvi's 专名系列

边界：英文标题以 `Cigotuvi's` 开头的 3 项法术；其中
`Cigotuvi's Putrefaction` 现行，另外 2 项为已移除兼容记录。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_PUTREFACTION` | 现行 | 西格图维之腐烂 | 使重伤活物在数回合内涌出瘴气，并暂时汲取施法者生命 | 保留 |
| `SPELL_CIGOTUVIS_DEGENERATION` | 已移除兼容 | 西格图维之退化 | 无当前描述或实现 | 暂缓术语（恢复时复审） |
| `SPELL_CIGOTUVIS_EMBRACE` | 已移除兼容 | 西格图维之拥抱 | 无当前描述或实现 | 暂缓术语（恢复时复审） |

名称结论：三项均保留稳定的 `Cigotuvi → 西格图维` 与
“专名之……”结构。“腐烂”准确表达受损活体组织加速腐败这一触发机制；
两项兼容标题的直译也成立，但不以缺失的机制为由作推测性重译。

描述审阅修正 1 项：现行 Putrefaction 中文仍描述旧版的杀敌制造骷髅。
本批按当前英文和实现重译，恢复仅能指定重伤活物、瘴气持续扩散并造成
减速与剧毒、施法者脚下受气流保护但并非免疫，以及暂时生命汲取随
法术威力减轻等规则。

证据：`spl-data.h:860`—`867`、`spl-data.h:4648`—`4649`、
`dat/descript/spells.txt:348`—`360`、`spl-clouds.cc:34`—`56`。

### 落地状态

- [x] 3/3 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-035`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T171439211946000+0800-98477-91e091a48933`。本批裁定后的
`docs/glossary.md` SHA-256 为
`ed9a4fab16c3cc3d47fdb11140e733c7d4cbb6b7423b9dbafe49c90d0320c562`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`2ba444c35624ab694f679a68438eeb7f77653e66ed611744db47f82c204ef7e9`。

## Ozocubu's 专名系列

边界：英文标题以 `Ozocubu's` 开头的 2 项现行法术，无已移除兼容成员。

| Enum | 等级 / 学派 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_OZOCUBUS_ARMOUR` | 3 / 冰 | 奥佐库布之护甲 | 厚冰提高护甲；移动或重甲会削弱收益 | 保留 |
| `SPELL_OZOCUBUS_REFRIGERATION` | 7 / 冰 | 奥佐库布之制冷 | 冻结视野内其他生物；相邻盟友可部分隔绝寒冷 | 保留 |

名称结论：专名稳定采用 `Ozocubu → 奥佐库布`。两项名称都准确概括
核心效果：“护甲”对应厚冰提供的护甲加成，“制冷”对应使整片视野空气
骤冷的过程，并未误示只攻击单体或召唤冰系实体。

描述审阅未发现机制偏差。护甲描述已说明原地维持、移动解除及重甲负担
降低加成；制冷描述已说明攻击视野内其他生物和相邻盟友提供部分隔绝。

证据：`spl-data.h:690`—`730`、`dat/descript/spells.txt:1464`—`1477`、
`spl-selfench.cc:54`—`74`、`spl-damage.cc:632`—`656`。

### 落地状态

- [x] 2/2 机制证据与名称裁定
- [x] 无名称或描述翻译修改
- [x] translation profile
- [x] 系列裁定登记（`D-C-036`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T171537550373000+0800-1624-c8efa2a0ba07`。本批裁定后的
`docs/glossary.md` SHA-256 为
`f5165a99af6ace1d05c6db8e3b5c2b1a7ee7c3e0a375c009a815e06b3e8f4045`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`2ba444c35624ab694f679a68438eeb7f77653e66ed611744db47f82c204ef7e9`。

## Gell's 专名系列

边界：英文标题以 `Gell's` 开头的 2 项现行效果。Gavotte 有独立法术
描述；Gravitas 仅供盖尔的重力铃鼓使用，其说明由物品 TextDB 承载。

| Enum | 使用入口 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_GELLS_GAVOTTE` | 6 级传送法术 | 盖尔之加沃特 | 改变局部重力方向，使视野内生物翻滚并承受碰撞 | 保留 |
| `SPELL_GRAVITAS` | 重力铃鼓 | 盖尔之重力 | 将范围内怪物拉向中心并固定敌对目标 | 保留 |

名称结论：专名稳定采用 `Gell → 盖尔`。“加沃特”保留舞曲名及群体随
方向移动的意象；“重力”准确对应铃鼓施加的向心引力，也保留原词的
重量双关。两项标题都无需塞入碰撞、固定或范围等二级机制。

描述审阅发现 1 项关联 Needs Fix：Gavotte 中文完整对应当前英文；
Gravitas 没有独立法术描述，但重力铃鼓的中文说明把效果范围和持续时间
所依赖的 `Evocations` 错译成“召唤术”。本批原修正为“激活技能”，
现按 D-A-052 的技能名统一为“魔力释放”。

证据：`spl-data.h:3025`—`3035`、`spl-data.h:3957`—`3964`、
`dat/descript/spells.txt:860`—`875`、`dat/descript/items.txt:723`—`733`、
`spl-transloc.cc:1828`—`1879`、`evoke.cc:970`—`984`。

### 落地状态

- [x] 2/2 入口、机制证据与名称裁定
- [x] 单一翻译写入者关联物品描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-037`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T171729292505000+0800-4902-33df8f9204b0`。本批裁定后的
`docs/glossary.md` SHA-256 为
`fbca868a01d12b1e8bdd013ef12d6eefef71f199f002fac6c3d009bcc2872a1c`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`2ba444c35624ab694f679a68438eeb7f77653e66ed611744db47f82c204ef7e9`。

## Borgnjor's 专名系列

边界：英文标题以 `Borgnjor's` 开头的 2 项现行法术，无已移除兼容成员。

| Enum | 等级 / 学派 / flags | 使用者 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|---|
| `SPELL_BORGNJORS_REVIVIFICATION` | 8 / 死灵 / `none` | 玩家 | 博格尼尔之复活 | 完全治愈仍活着的施法者，永久降低最大生命；可解除死亡之门并短暂麻痹 | 重译为“博格尼尔之复苏” |
| `SPELL_BORGNJORS_VILE_CLUTCH` | 5 / 死灵、土 / `dir_or_target, not_self, needs_tracer` | 玩家、怪物 | 博格尼尔之邪恶抓握 | 区域内尸手将敌人束缚在原地并持续收紧，直到挣脱 | 保留 |

名称结论：专名稳定采用 `Borgnjor → 博格尼尔`。Revivification 不会
使死者复活，且亡灵无法施放；“复活”会错误暗示 resurrection，改为
“复苏”以表达恢复仍存的生命力。Vile Clutch 的现译保留 vile 的邪恶
意象与 clutch 的抓握动作，符合尸手束缚机制。

描述审阅修正 1 项术语错误：`power` 应按术语表译为“法术威力”，不能写成
“法术力量”。其余完全治疗、最大生命永久损失、死亡之门交互、亡灵限制，
以及尸手的区域束缚和挣脱条件均与英文一致。

证据：`spl-data.h:668`—`675`、`spl-data.h:3259`—`3266`、
`dat/descript/spells.txt:226`—`238`、`spl-selfench.cc:94`—`109`、
`spl-util.cc:1856`—`1864`、`beam.cc:3952`—`3957`、
`beam.cc:6700`—`6706`。

### 落地状态

- [x] 2/2 机制证据与名称裁定
- [x] 单一翻译写入者名称与描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-038`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T172013512876000+0800-11309-2c87f4b8d28b`。本批裁定后的
`docs/glossary.md` SHA-256 为
`80577c85b430dc87f7a7c4fd3b9a24624d303db34f196bfe3f54aed008f4cf2d`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d9736ee6b3113b7ab8bef126c8444805aec33f4c672437b663210528cc58db86`。

## Alistair's 专名系列

边界：英文标题以 `Alistair's` 开头的 2 项现行法术。

| Enum | 等级 / 学派 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_INTOXICATE` | 5 / 炼金 | 阿利斯泰尔之醉 | 混乱视野内智慧生物；成功时施法者短暂眩晕 | 保留 |
| `SPELL_WALKING_ALEMBIC` | 5 / 锻造、炼金 | 阿利斯泰尔之行走蒸馏器 | 构建近战炼金构装，酿造并向盟友分发药水 | 保留 |

名称结论：专名稳定采用 `Alistair → 阿利斯泰尔`。“醉”保留脑组织转化
为酒精的荒诞炼金意象；“行走蒸馏器”准确指向能移动、战斗、酿造和分发
药水的构装。两项名称均与当前效果一致。

描述审阅修正 1 项指代歧义：Intoxication 英文明确是施法者在成功接触
其他心灵后短暂眩晕，旧中文的“他们”可能被理解为受术目标；本批明确
主语为施法者。Walking Alembic 描述完整。

证据：`spl-data.h:1185`—`1192`、`spl-data.h:4307`—`4314`、
`dat/descript/spells.txt:25`—`39`、Intoxication 群体惑控实现、
`spl-summoning.cc:4264`—`4282`。

### 落地状态

- [x] 2/2 机制证据与名称裁定
- [x] 单一翻译写入者描述澄清
- [x] translation profile
- [x] 系列裁定登记（`D-C-039`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T172145181943000+0800-14637-8739dacfd4a7`。本批裁定后的
`docs/glossary.md` SHA-256 为
`fdc97e93f4e4ac985d49635a6cd0585d1418e985c2fbce0cf8c154b4d633051f`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d9736ee6b3113b7ab8bef126c8444805aec33f4c672437b663210528cc58db86`。

## Eringya's 专名系列

边界：英文标题以 `Eringya's` 开头的 2 项现行法术，无已移除兼容成员。

| Enum | 等级 / 学派 / flags | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_NOXIOUS_BOG` | 6 / 炼金 / `no_ghost, destructive` | 埃林吉亚之毒沼 | 有毒污泥把附近合适地面暂时变成伤害并毒害怪物的毒沼 | 保留 |
| `SPELL_SURPRISING_CROCODILE` | 4 / 召唤、传送 / `target, no_ghost, not_self` | 埃林吉亚之意外鳄鱼 | 鳄鱼从施法者脚下出现，强化攻击相邻目标并拖拽双方 | 保留 |

名称结论：专名稳定采用 `Eringya → 埃林吉亚`。“毒沼”准确表达 noxious
bog 的地形与毒害效果；“意外鳄鱼”保留英文故意突兀的戏谑感，也符合鳄鱼
突然从施法者脚下现身的演出，无需改成过度说明性的“突袭鳄鱼”。

描述审阅修正 1 项严重旧译：Surprising Crocodile 原中文仅称在目标附近
召唤并攻击，遗漏当前英文的出现位置、强化攻击、拖拽施法者和目标、下马
落位及不可重施规则。本批完整补回，并把关联引文中的“埃琳吉娅”统一为
已确认专名“埃林吉亚”。Noxious Bog 描述与当前英文一致。

证据：`spl-data.h:3414`—`3421`、`spl-data.h:4285`—`4292`、
`dat/descript/spells.txt:651`—`666`、`spl-damage.cc:4709`—`4758`、
`spl-summoning.cc:3914`—`4035`、`dat/descript/quotes.txt:523`—`527`。

### 落地状态

- [x] 2/2 机制证据与名称裁定
- [x] 单一翻译写入者描述与关联引文修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-040`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T172406621637000+0800-20271-c4f1b1ef858b`。本批裁定后的
`docs/glossary.md` SHA-256 为
`1384a328a02912da8487f61644548a750e29d6528f6f89cafa89fbbb2e761aaf`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d9736ee6b3113b7ab8bef126c8444805aec33f4c672437b663210528cc58db86`。

## Nazja's 专名系列

边界：英文标题以 `Nazja's` 开头的 2 项现行锻造术。

| Enum | 使用者 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_PERCUSSIVE_TEMPERING` | 玩家 | 纳兹亚之冲击淬炼 | 修复并强化自身锻造的构装体，同时伤害其邻敌 | 保留 |
| `SPELL_ALL_PURPOSE_TEMPERING` | 怪物 | 纳兹亚之通用淬炼 | 修复并强化任意附近构装体，同时伤害其邻敌 | 保留 |

名称结论：专名稳定采用 `Nazja → 纳兹亚`。共同词根“淬炼”准确表达
魔法锤修复并强化构装体；“冲击”对应敲击产生的冲击波，“通用”对应
怪物版更宽泛的构装体目标范围。两项名称无需修改。

描述审阅修正 2 项机制级 Needs Fix：旧中文把两项都写成强化已装备的
武器或护甲，已完全不符合当前版本。本批恢复魔法锤、构装体目标、修复和
攻击强化、邻近敌人受火花／熔渣／冲击波伤害，以及强化期间不可重复施放；
同时准确区分玩家版仅限自身锻造物与怪物版任意附近构装体。

证据：`spl-data.h:4351`—`4372`、`dat/descript/spells.txt:1401`—`1417`、
`spl-monench.cc:403`—`450`、`mon-cast.cc:7520`—`7560`。

### 落地状态

- [x] 2/2 机制证据与名称裁定
- [x] 单一翻译写入者两段描述重译
- [x] translation profile
- [x] 系列裁定登记（`D-C-041`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T172544356980000+0800-23911-1411aa19df14`。本批裁定后的
`docs/glossary.md` SHA-256 为
`350ec3166f5465442e2198d78a89cf070a10f6098175e9ace208d5056a490d92`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d9736ee6b3113b7ab8bef126c8444805aec33f4c672437b663210528cc58db86`。

## Olgreb's 专名系列

边界：英文标题以 `Olgreb's` 开头的 1 项现行法术。

| Enum | 等级 / 学派 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_OLGREBS_TOXIC_RADIANCE` | 4 / 炼金 | 奥尔格雷布之毒辐射 | 持续毒害视线内所有生物 | 保留 |

名称结论：“奥尔格雷布之毒辐射”准确表达从施法者向整个视野持续放射
毒能量的效果，不会误示为单体射线或一次性爆发。

描述机制完整；本批仅消除“在法术持续时内持续”的重复病句。

证据：`spl-data.h:353`—`360`、`dat/descript/spells.txt:1431`—`1434`、
`player-reacts.cc:957`—`958`、怪物 Toxic Radiance 持续效果实现。

### 落地状态

- [x] 1/1 机制证据与名称裁定
- [x] 单一翻译写入者描述润色
- [x] translation profile
- [x] 系列裁定登记（`D-C-042`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T172733668753000+0800-27170-aa90c5015122`。本批裁定后的
`docs/glossary.md` SHA-256 为
`29f1c4254be7f901b35bec2a9601eb2f7c597fb238f2126e2057b286f4512c5e`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d9736ee6b3113b7ab8bef126c8444805aec33f4c672437b663210528cc58db86`。

## Lehudib's 专名系列

边界：英文标题以 `Lehudib's` 开头的 1 项现行法术。

| Enum | 等级 / 学派 / flags | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_LEHUDIBS_CRYSTAL_SPEAR` | 8 / 咒法、土 / `dir_or_target, needs_tracer` | 勒胡迪布之水晶矛 | 短射程发射尖锐水晶投射物，造成极高物理伤害 | 保留 |

名称结论：专名稳定采用 `Lehudib → 勒胡迪布`。“水晶矛”忠实保留
Crystal Spear 的材质与尖锐长形投射物意象，也符合短射程、高伤害的
8 级法术强度，不需要改成实现描述中的“水晶碎片”。

中英文描述机制一致；本批只把生硬的量词和顿号结构改为“一枚致命而锋利
的水晶碎片”。

证据：`spl-data.h:443`—`450`、`dat/descript/spells.txt:1196`—`1198`、
`zap-data.h:834`—`846`、`mon-cast.cc:2330`、`mon-spell.h:66`—`73`。

### 落地状态

- [x] 1/1 机制证据与名称裁定
- [x] 单一翻译写入者描述润色
- [x] translation profile
- [x] 系列裁定登记（`D-C-043`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T172950885503000+0800-32198-45d6f29f31c6`。本批裁定后的
`docs/glossary.md` SHA-256 为
`7cba810aa7ec02c684b444ebd699410f24d383ce7b45e3c9157c27b0daa52f02`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d9736ee6b3113b7ab8bef126c8444805aec33f4c672437b663210528cc58db86`。

## 单成员专名批次 A

边界：Yara、Leda、Lee、Martyr 各自唯一的现行法术，共 4 项。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_VIOLENT_UNRAVELLING` | 亚拉之猛烈解构 | 撕裂附魔，诱变爆炸并驱散召唤物 | 保留 |
| `SPELL_LEDAS_LIQUEFACTION` | 勒达之液化 | 液化周围地面，妨碍移动与近战 | 保留 |
| `SPELL_LRD` | 李之快速解构 | 粉碎墙壁或脆性生物形成爆炸碎片 | 保留 |
| `SPELL_MARTYRS_KNELL` | 殉道者之丧钟 | 召唤替盟友分担伤害的殉道者灵魂 | 保留 |

名称结论：四项名称均准确对应当前核心效果。描述审阅只发现 Yara 一项
指代缺损：补足“任何相邻生物”，并把召唤物统一为“它们”；其余三项
与英文一致。

证据：对应 `spl-data.h` 条目、英文与中文 TextDB，以及各项施法实现。

### 落地状态

- [x] 4/4 机制证据与名称裁定
- [x] 单一翻译写入者描述澄清
- [x] translation profile
- [x] 系列裁定登记（`D-C-044`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T173107850002000+0800-35267-699a1244b4eb`。本批裁定后的
`docs/glossary.md` SHA-256 为
`364c07cfa2bd2c4b92dbce38b3f4dc9e83ded7a2079f486bca1b496e5252799b`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d9736ee6b3113b7ab8bef126c8444805aec33f4c672437b663210528cc58db86`。

## 单成员专名批次 B

边界：Brom、Trog、Tukima、Sheza、Sentinel 各自唯一的现行法术，共 5 项。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_BOULDER` | 布罗姆之碾压巨石 | 滚石碾过死者并推动幸存者 | 保留 |
| `SPELL_TROGS_HAND` | 特洛格之手 | 强力恢复并提高意志力 | 保留 |
| `SPELL_TUKIMAS_DANCE` | 图基玛之舞 | 活化敌方武器使其倒戈 | 保留 |
| `SPELL_SHEZAS_DANCE` | 谢扎之舞 | 从各处召来并活化武器 | 保留 |
| `SPELL_SENTINEL_MARK` | 哨兵印记 | 向同层所有生物暴露目标的位置 | 保留 |

名称结论：五项名称均准确对应当前效果。描述修正 4 项：Sentinel 原中文
完全属于另一套机制；Brom 残留旧爆炸、磨损和摆动规则；Sheza 武器代词
错误；Trog 能力说明缺少中心词。Tukima 描述与英文一致。

证据：对应 `spl-data.h` 条目、英文与中文 spell/ability TextDB，以及
滚石、标记、武器活化和恢复效果实现。

### 落地状态

- [x] 5/5 机制证据与名称裁定
- [x] 单一翻译写入者四项描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-045`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T173313984361000+0800-38838-9c6076d62e63`。本批裁定后的
`docs/glossary.md` SHA-256 为
`59bd489694d613edf3bf5ae6ab3a5432f6601656e45f88f3084f06454272ba9c`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d9736ee6b3113b7ab8bef126c8444805aec33f4c672437b663210528cc58db86`。

## Hoarfrost 词根系列

边界：英文标题含 `Hoarfrost` 的 2 项现行法术。

| Enum | 等级 / 学派 / flags | 使用者 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|---|
| `SPELL_HOARFROST_CANNONADE` | 5 / 锻造、冰 / 无 | 玩家、怪物 | 白霜炮击 | 塑造两座远程火炮；逐发自耗，最终齐射强化 | 保留 |
| `SPELL_HOARFROST_BULLET` | 5 / 咒法、冰 / `dir_or_target, needs_tracer, monster` | 白霜火炮 | 白霜弹 | 冰霜碎片命中后减速；第五发碎裂并产生额外范围伤害 | 保留 |

名称结论：两项稳定采用 `Hoarfrost → 白霜`。“白霜弹”准确指向火炮的
单发冰霜碎片；“白霜炮击”表达两座火炮连续射击形成的 cannonade，
不需要因实体数量改为“炮台”。

中文 `Hoarfrost Bullet` 描述与英文和实现一致。`Hoarfrost Cannonade`
原中文仍称“一座冰霜炮台”且只写攻击附近敌人，遗漏脆霜减速、逐发自耗
及强化终幕，本批已按当前英文与实现重译。

证据：`spl-data.h:4003`—`4032`、`dat/descript/spells.txt:990`—`1007`、
`spl-summoning.cc:3274`—`3313`、`mon-cast.cc:347`—`378`、
`beam.cc:4529`—`4539`、`beam.cc:5249`—`5265`。

### 落地状态

- [x] 2/2 机制证据与名称裁定
- [x] 单一翻译写入者描述重译
- [x] translation profile
- [x] 系列裁定登记（`D-C-046`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T173458047137000+0800-43342-80216cf5184d`。本批裁定后的
`docs/glossary.md` SHA-256 为
`a40d58378839e4dc1d746fdbb71e6839f3fed49c7ebb132182d56d5d2d0ff686`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d9736ee6b3113b7ab8bef126c8444805aec33f4c672437b663210528cc58db86`。

## Death's Door

边界：`Death's Door` 这一项现行法术。

| Enum | 等级 / 学派 / flags | 使用者 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|---|
| `SPELL_DEATHS_DOOR` | 9 / 死灵 / `no_ghost` | 玩家、怪物 | 死亡之门 | 短暂近乎免疫伤害；生命降至濒死值且不能接受治疗；结束后进入重施冷却 | 保留 |

名称结论：“死亡之门”准确保留 `at death's door` 的濒死门槛意象，并与
施法消息中的 doorway 意象一致。标题无需枚举法术威力决定的剩余生命、
结束警告或冷却机制。

英文描述与实现一致。中文描述完整覆盖近乎免疫伤害、濒死生命值、治疗
无效、到期警告、重施冷却、法术威力影响结束生命值和亡灵限制；本批只
修正施法者代词指代与亡灵限制末句的中文语法。

证据：`spl-data.h:375`—`382`、`dat/descript/spells.txt:471`—`481`、
`spl-selfench.cc:36`—`51`、`duration-data.h:358`—`371`、
`ouch.cc:1384`—`1390`、`player-reacts.cc:894`—`904`。

### 落地状态

- [x] 1/1 机制证据与名称裁定
- [x] 单一翻译写入者两处措辞修正
- [x] translation profile
- [x] 单项裁定登记（`D-C-047`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T173722806271000+0800-48561-103eb2887a70`。本批裁定后的
`docs/glossary.md` SHA-256 为
`58ebdb5137d6d3fdf8a406dd2d11f25cb7bf9a96400e0c9dad75e41a0f9ba140`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d9736ee6b3113b7ab8bef126c8444805aec33f4c672437b663210528cc58db86`。

## Freeze/Freezing/Frozen 词形系列

边界：标题中含独立 `Freeze`、`Freezing` 或 `Frozen` 词形的 5 项法术；
其中 4 项现行、1 项 `TAG_MAJOR_VERSION == 34` 已移除兼容。已在 Cloud
批次审阅的 `Freezing Cloud` 不重复计数。

| Enum | 生命周期 | 等级 / 学派 / flags | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|---|
| `SPELL_FREEZE` | 现行 | 1 / 冰 / `dir_or_target, not_self, destructive` | 冰冻 | 相邻单体伤害，无视护甲，可减速冷血生物 | 保留 |
| `SPELL_FLASH_FREEZE` | 现行 | 7 / 咒法、冰 / `dir_or_target, monster, needs_tracer` | 急冻 | 高额伤害并短时减速；一半伤害无视寒冷抗性 | 保留 |
| `SPELL_FREEZING_GUST` | 现行 | 5 / 咒法、冰、气 / `target, needs_tracer, cloud, monster` | 冰冻狂风 | 穿透性严寒气流，沿途留下致命寒气云 | 重译为“冰冻阵风” |
| `SPELL_FROZEN_RAMPARTS` | 现行 | 3 / 冰 / `no_ghost, destructive` | 冰冻壁垒 | 冰封周围墙壁，伤害墙边敌人；移动后解除 | 保留 |
| `SPELL_FREEZING_AURA` | 已移除兼容 | — | 冰封灵气 | 无当前描述或实现 | 保留兼容标题 |

名称结论：Freeze 词形不必机械统一为单个中文字样，应按构词和机制分别
采用“冰冻／急冻／冰封”。唯一名称问题是 `Gust` 被夸大为“狂风”；
“冰冻阵风”既忠实于短促气流原义，也符合穿透性寒气束的实际表现。

描述审阅发现两项 Needs Fix：`Freezing Gust` 原中文误写成伤害并减速
路径敌人的强风，遗漏穿透和沿途生成寒气云；`Flash Freeze` 原中文声称
对已冻结目标无效，但现行英文与实现只是不重复施加冻结，伤害仍然生效。

证据：`spl-data.h:320`—`327`、`spl-data.h:679`—`686`、
`spl-data.h:2388`—`2395`、`spl-data.h:3448`—`3455`、
`spl-data.h:4669`、`dat/descript/spells.txt:708`—`711`、
`dat/descript/spells.txt:794`—`814`、`beam.cc:2435`—`2510`、
`beam.cc:4529`—`4539`、`spl-damage.cc:4498`—`4555`。

### 落地状态

- [x] 5/5 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者名称和描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-048`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T173948204505000+0800-54736-80411c83e378`。本批裁定后的
`docs/glossary.md` SHA-256 为
`1fc790829eafef04efb4f0153a724bfb05fcf23ff4e5fb6c4e948d53b2fcbc15`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`cd53a3e0eeee8ac15014ba0ad88ede96cdcddbee06f81b4468a347334d97a580`。

## Acid/Corrosive 词形系列

边界：以酸液物质或腐蚀性质为核心的 3 项现行法术。`Corrosive Bolt`
已在 Bolt 批次审阅，本批复用其未变化的机制证据且不重复计数；新增
审阅身份为 2 项。

| Enum | 等级 / 学派 / flags | 使用者 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|---|
| `SPELL_SPIT_ACID` | 5 / 炼金 / `dir_or_target, monster, noisy, needs_tracer` | 怪物 | 喷吐酸液 | 向单个目标喷出酸液 | 保留 |
| `SPELL_ACID_BALL` | 5 / 咒法、炼金 / `dir_or_target, needs_tracer, monster` | 怪物 | 酸液球 | 投掷会爆炸的腐蚀性酸液球 | 保留 |
| `SPELL_CORROSIVE_BOLT` | 6 / 咒法、炼金 / `dir_or_target, needs_tracer` | 玩家、怪物 | 腐蚀箭 | 穿透酸液束，可施加腐蚀 | 保留（复用 D-C-014） |

名称结论：`Acid` 作为攻击物质稳定译为“酸液”，因此“喷吐酸液”和
“酸液球”分别准确表达动作与投射物形态；`Corrosive` 强调腐蚀性质，
“腐蚀箭”与 Bolt 系列规则一致。三项无需强制使用同一个中文字根。

`Spit Acid` 与 `Acid Ball` 的中英文描述均准确且完整，不需要修改。

证据：`spl-data.h:1546`—`1554`、`spl-data.h:4564`—`4572`、
`dat/descript/spells.txt:6`—`8`、`dat/descript/spells.txt:1975`—`1977`、
`mon-cast.cc:2362`—`2389`、`zap-data.h:2703`—`2716`；Corrosive Bolt
复用 `D-C-014` 的机制证据。

### 落地状态

- [x] 3/3 机制证据与名称裁定（2 项新增，1 项复用）
- [x] 描述一致，无需修改
- [x] translation profile
- [x] 系列裁定登记（`D-C-049`）

验证结果：覆盖 Acid/Corrosive 与 Frost/Rime/Chill 当前差异的
`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T174356732603000+0800-63283-7833d575d6e4`。裁定后的
`docs/glossary.md` SHA-256 为
`539fb3f7d74593a7c20d04f0011a4c33d120e230cee42a027eda458162a56381`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`b0e73be1fa96d25dead8cb7fe00588c6e718ad560d0458ec70f78c019ae20930`。

## Frost/Rime/Chill 寒冷术语批次

边界：尚未审阅且标题含 `Frost`、`Rime` 或 `Chill` 的 4 项现行法术。

| Enum | 等级 / 学派 / flags | 使用者 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|---|
| `SPELL_CREEPING_FROST` | 5 / 咒法、冰 / `monster` | 怪物 | 蔓延冰霜 | 从墙壁唤出冻气，伤害、冻结并减速墙边敌人 | 保留 |
| `SPELL_REBOUNDING_CHILL` | 7 / 咒法、冰 / `dir_or_target, needs_tracer, monster` | 怪物 | 弹跳寒冷 | 穿透寒气束沿墙反弹，可命中目标两次 | 重译为“弹跳寒流” |
| `SPELL_RIMEBLIGHT` | 7 / 死灵、冰 / `dir_or_target, unclean, destructive, not_self` | 玩家、怪物 | 霜疫 | 持续从体内冻结宿主，迸射冰片并可能在死亡时传播 | 保留 |
| `SPELL_SPLINTERFROST_SHELL` | 7 / 锻造、冰 / `target, not_self` | 玩家、怪物 | 碎霜之壳 | 构筑半圆冰障；墙段破裂时向破坏者齐射冰片 | 保留 |

名称结论：“蔓延冰霜”“霜疫”“碎霜之壳”均准确传达当前机制；
`Rebounding Chill` 的 cold bolt 是可穿透、可沿墙反弹的具体寒气流，
“弹跳寒流”比抽象且搭配生硬的“弹跳寒冷”准确自然。

描述审阅发现两项 Needs Fix：`Rebounding Chill` 原中文属于不存在的
近战反击冰环；`Splinterfrost Shell` 原中文属于不存在的吸伤贴身护盾，
两项均已按当前英文描述和实现完整重译。另两项中英文机制一致。

证据：`spl-data.h:2399`—`2406`、`spl-data.h:2554`—`2561`、
`spl-data.h:3991`—`3998`、`spl-data.h:4340`—`4347`、
`dat/descript/spells.txt:440`—`444`、`dat/descript/spells.txt:1669`—`1672`、
`dat/descript/spells.txt:1697`—`1709`、`dat/descript/spells.txt:1987`—`1995`、
`beam.cc:2418`、`spl-summoning.cc:4599`—`4604`。

### 落地状态

- [x] 4/4 机制证据与名称裁定
- [x] 单一翻译写入者名称与描述重译
- [x] translation profile
- [x] 系列裁定登记（`D-C-050`）

验证结果：覆盖 Acid/Corrosive 与 Frost/Rime/Chill 当前差异的
`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T174356732603000+0800-63283-7833d575d6e4`。裁定后的
`docs/glossary.md` SHA-256 为
`539fb3f7d74593a7c20d04f0011a4c33d120e230cee42a027eda458162a56381`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`b0e73be1fa96d25dead8cb7fe00588c6e718ad560d0458ec70f78c019ae20930`。

## Permafrost Eruption

边界：`Permafrost Eruption` 这一项现行法术。

| Enum | 等级 / 学派 / flags | 使用者 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|---|
| `SPELL_PERMAFROST_ERUPTION` | 6 / 冰、土 / `destructive` | 玩家、怪物 | 永冻爆发 | 落石必中目标；严寒无视护甲并冻结邻近生物；自动选择敌人密集处 | 保留 |

名称结论：“永冻”准确表达潜藏于大地的古老严寒，“爆发”概括其猛烈
喷涌和震落岩石的表现；标题不必展开自动选取目标和安全距离。

原中文描述误写为施法者周围的普通冰冻爆发，遗漏落石必中、寒冷无视
护甲、邻近目标、自动选取敌人密集处及不在施法者身旁爆发，本批已按
现行英文描述重译。

证据：`spl-data.h` 中 `SPELL_PERMAFROST_ERUPTION` 条目、
`dat/descript/spells.txt:1506`—`1515` 及对应施法实现。

### 落地状态

- [x] 1/1 机制证据与名称裁定
- [x] 单一翻译写入者描述重译
- [x] translation profile
- [x] 单项裁定登记（`D-C-051`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T174607102817000+0800-67581-68f23c07c5ca`。本批裁定后的
`docs/glossary.md` SHA-256 为
`ae1ab8dbe6d738426bd8f8f3ebe255ea6a74b528d4a7257b84252b5199141c08`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`b0e73be1fa96d25dead8cb7fe00588c6e718ad560d0458ec70f78c019ae20930`。

## Lightning/Electricity/Thunder 元素系列

边界：标题含 `Lightning`、`Electric`、`Electrical`、`Electricity`
或 `Thunder` 的 10 项法术。6 项已在既有批次审阅，本批新增 3 项现行
法术和 1 项已移除兼容标题。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_CONJURE_BALL_LIGHTNING` | 现行 | 召唤球形闪电 | 创造会追敌并爆炸的球状闪电 | 保留 |
| `SPELL_CHAIN_LIGHTNING` | 现行 | 连锁闪电 | 从最近生物开始向外连锁，距离越远伤害越低 | 保留 |
| `SPELL_ORB_OF_ELECTRICITY` | 现行 | 电光球 | 电能球命中时产生大型爆炸 | 保留 |
| `SPELL_RING_OF_THUNDER` | 已移除兼容 | 雷霆之环 | 无当前描述或实现 | 暂缓术语（恢复时复审） |
| `SPELL_LIGHTNING_BOLT` | 现行 | 闪电箭 | 穿透闪电束 | 保留（复用 D-C-014） |
| `SPELL_ELECTRICAL_BOLT` | 现行 | 电击箭 | 高命中电束，可墙面反弹 | 保留（复用 D-C-014） |
| `SPELL_CALL_DOWN_LIGHTNING` | 现行 | 降下闪电 | 从目标上方降下闪电 | 保留（复用 D-C-016） |
| `SPELL_FORGE_LIGHTNING_SPIRE` | 现行 | 锻造闪电尖塔 | 锻造远程闪电构装 | 保留（复用 D-C-032） |
| `SPELL_ELECTRIC_CHARGE` | 现行 | 维之电击冲锋 | 沿最短路径冲锋并电击目标 | 保留（复用 D-C-034） |
| `SPELL_THUNDERBOLT` | 现行 | 雷击 | 连续施放时形成扇形电弧 | 保留（复用 D-C-014） |

名称结论：该组按实际构词分别使用“闪电／电击／电光／雷霆”，无需机械
统一。三项新增现行标题准确区分会追敌的球状闪电、逐目标扩散的电弧和
命中爆炸的电能球；已移除的 Ring of Thunder 缺少当前机制证据，暂沿用。

描述审阅发现两处 Needs Fix：`Chain Lightning` 原中文残留“不断弹跳
直到接地”的旧机制，现行法术是先击中最近生物再向外连锁；`Conjure
Ball Lightning` 使用了指人的“他们”指代球状闪电。其余新增描述一致。

证据：`spl-data.h:1231`—`1249`、`spl-data.h:2377`—`2385`、
`spl-data.h:4721`，对应英文与中文描述，以及连锁电弧、球状闪电和
电能球的施法实现；其余六项复用对应既有裁定。

### 落地状态

- [x] 10/10 生命周期、机制证据与名称裁定（4 项新增，6 项复用）
- [x] 单一翻译写入者两处描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-052`）

验证结果：覆盖 Lightning/Electricity/Thunder 与寒冷术语当前差异的
`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T174921709354000+0800-75557-976d5f4df2cc`。裁定后的
`docs/glossary.md` SHA-256 为
`dd8fb9706ab97e86f9ab65f79db16b91d4255ba62530b44d099de48e4fabf109`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`0574e4bd74af7ee549cb29d9d4bd00a855c3a0a67edfd5800cbecc41976bedf8`。

## Glaciate/Iceblast/Hailstorm 寒冷术语批次

边界：寒冷元素剩余的 `Glaciate`、`Iceblast`、`Hailstorm` 三项现行法术。

| Enum | 等级 / 学派 / flags | 使用者 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|---|
| `SPELL_GLACIATE` | 9 / 咒法、冰 / `dir_or_target, monster` | 怪物 | 冰川 | 锥形寒冰冲击；近处伤害更高，命中后冰封减速，击杀可能生成冰块 | 重译为“冰封” |
| `SPELL_ICEBLAST` | 5 / 咒法、冰 / `dir_or_target, needs_tracer` | 玩家道具、怪物 | 冰爆 | 大团冰块撞击爆炸，一半伤害无视寒冷抗性 | 保留 |
| `SPELL_HAILSTORM` | 3 / 咒法、冰 / 无 | 玩家 | 冰雹风暴 | 环形冰雹攻击；紧邻施法者处为安全风暴眼 | 保留 |

名称结论：`Glaciate` 是“使冰封”的动词，当前“冰川”误作地貌名词；
改为“冰封”能准确表达命中目标覆冰减速、击杀者化为冰块的机制。
“冰爆”和“冰雹风暴”分别忠实保留投射物爆炸与天气形态。

三项中文描述均有语言或准确性问题：`Glaciate` 缺少被卷入者中心词，
`Hailstorm` 将 adjacent 泛化为附近，`Iceblast` 将单个 large mass
写成大量冰块；三项寒冷抗性句式亦不自然，本批已统一修正。

证据：`spl-data.h:2565`—`2572`、`spl-data.h:3093`—`3100`、
`spl-data.h:3403`—`3410`、`dat/descript/spells.txt:889`—`895`、
`dat/descript/spells.txt:932`—`937`、`dat/descript/spells.txt:1027`—`1030`、
`spl-damage.cc:3987`—`4059`、`spl-damage.cc:4295`—`4297`。

### 落地状态

- [x] 3/3 机制证据与名称裁定
- [x] 单一翻译写入者名称与描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-053`）

验证结果：覆盖 Lightning/Electricity/Thunder 与寒冷术语当前差异的
`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T174921709354000+0800-75557-976d5f4df2cc`。裁定后的
`docs/glossary.md` SHA-256 为
`dd8fb9706ab97e86f9ab65f79db16b91d4255ba62530b44d099de48e4fabf109`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`0574e4bd74af7ee549cb29d9d4bd00a855c3a0a67edfd5800cbecc41976bedf8`。

## Fireball 词形系列

边界：标题含 `Fireball` 的 3 项法术；2 项现行，1 项已移除兼容。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_FIREBALL` | 现行 | 火球 | 投掷会爆炸的火焰球 | 保留 |
| `SPELL_GHOSTLY_FIREBALL` | 现行 | 幽灵火球 | 负能量爆炸使范围内活物衰竭 | 保留 |
| `SPELL_DELAYED_FIREBALL` | 已移除兼容 | 延迟火球 | 无当前描述或实现 | 暂缓术语（恢复时复审） |

名称结论：“火球”准确概括普通法术的爆炸投射物；“幽灵火球”保留
Ghostly 的死灵意象，同时与造成火焰伤害的普通火球明确区分。已移除的
延迟火球缺少当前机制证据，暂沿用。

普通 Fireball 的中英文描述一致。Ghostly Fireball 原中文存在语法缺失，
且没有明确只影响活物，本批改为“使其笼罩的所有活物陷入衰竭”。

证据：`spl-data.h:52`—`60`、`spl-data.h:2186`—`2194`、
`spl-data.h:4659`，`dat/descript/spells.txt:694`—`696`、
`dat/descript/spells.txt:874`—`877`，以及对应爆炸 zap 实现。

### 落地状态

- [x] 3/3 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-054`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T175125508466000+0800-79351-5bcf280899f5`。本批裁定后的
`docs/glossary.md` SHA-256 为
`8bb9f80d039c66166c2173fe5cfe2a8b80f9bc7c94686cba2b99d8e7a04691bf`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`0574e4bd74af7ee549cb29d9d4bd00a855c3a0a67edfd5800cbecc41976bedf8`。

## Death 独立词形系列

边界：标题含独立 `Death` 的 3 项现行法术；已审阅的 `Death's Door`
不重复计数。

| Enum | 等级 / 学派 / flags | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_DEATH_CHANNEL` | 6 / 死灵 / `helpful, selfench` | 死亡通道 | 引导期间令被杀的活物、恶魔和神圣生物留下幽魂作战 | 保留 |
| `SPELL_DEATH_RATTLE` | 7 / 咒法、死灵、气 / `dir_or_target, monster` | 死亡之响 | 呼出垂死精粹并生成瘴气云 | 保留 |
| `SPELL_KISS_OF_DEATH` | 1 / 咒法、死灵 / `dir_or_target, needs_tracer, not_self` | 死亡之吻 | 衰竭目标，同时暂时降低施法者生命值 | 保留 |

名称结论：三项标题分别保留死亡力量的持续通道、临终喘响和“死亡之吻”
的原名意象，并能区分幽魂生成、瘴气吐息与双方生命代价三种机制。

描述审阅发现两项 Needs Fix：Death Channel 将 living、demonic、holy
误译成“生物、邪物、圣物”，并重复使用“灵魂”；Kiss of Death 的
fragment 机械重复且使用指人复数代词。本批已按英文含义修正。
Death Rattle 的中英文描述一致。

证据：`spl-data.h` 对应三项条目、`dat/descript/spells.txt:462`—`469`、
`2300`—`2304`，以及幽魂生成、瘴气吐息和生命汲取实现。

### 落地状态

- [x] 3/3 机制证据与名称裁定
- [x] 单一翻译写入者两项描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-055`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T175315514034000+0800-83103-7dea740d5619`。本批裁定后的
`docs/glossary.md` SHA-256 为
`22b7d9fd8160ab3bffb23692177a8a811b4339995b964683b6a613ccb7d8a90e`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`0574e4bd74af7ee549cb29d9d4bd00a855c3a0a67edfd5800cbecc41976bedf8`。

## Teleport 词形系列

边界：标题含 `Teleport` 的 3 项法术；1 项现行，2 项已移除兼容。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_TELEPORT_OTHER` | 现行 | 传送他人 | 短暂延迟后尝试将目标传送出施法者视野 | 保留 |
| `SPELL_CONTROL_TELEPORT` | 已移除兼容 | 传送控制 | 无当前描述或实现 | 修正为“控制传送” |
| `SPELL_TELEPORT_SELF` | 已移除兼容 | 自我传送 | 无当前描述或实现 | 保留 |

名称结论：`Teleport → 传送` 稳定一致。“传送他人”和“自我传送”
准确表达受事者；“传送控制”是英语词序倒装，即使不依赖历史机制也能
确定为语言错误，改为自然的动宾结构“控制传送”。

Teleport Other 原中文误写为即时“随机传送”，遗漏短暂延迟、尝试判定
和传出施法者视野的目的，本批已按现行英文描述重译。

证据：`spl-data.h:364`—`372`、`spl-data.h:4652`、
`spl-data.h:4727`、`dat/descript/spells.txt:2252`—`2255` 及传送实现。

### 落地状态

- [x] 3/3 生命周期、机制／语言证据与名称裁定
- [x] 单一翻译写入者名称与描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-056`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T175500604011000+0800-86234-9cc288086e3d`。本批裁定后的
`docs/glossary.md` SHA-256 为
`ed8fb9766d8e81c16df038c1d97e46c8a38e0ce4f4634d28bae76551b5b1fb1b`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`63c8bea2fe5acdd6995eda8e5bae0ba2992814c508c09b323c59e27984ee7e1b`。

## Control 词形系列

边界：以 `Control` 开头的 3 项已移除兼容法术标题；Control Teleport
已在 Teleport 批次审阅，本批新增 2 项。

| Enum | 当前译名 | 机制证据 | 裁定 |
|---|---|---|---|
| `SPELL_CONTROL_UNDEAD` | 亡灵控制 | 无当前描述或实现 | 修正为“控制亡灵” |
| `SPELL_CONTROL_WINDS` | 控风术 | 无当前描述或实现 | 保留 |
| `SPELL_CONTROL_TELEPORT` | 控制传送 | 无当前描述或实现 | 保留（复用 D-C-056） |

名称结论：三项都缺少当前机制证据，但标题自身足以判断中文语序。
“亡灵控制”是英语词序移植，改为动宾结构“控制亡灵”；“控风术”和
“控制传送”均自然明确。

证据：`spl-data.h:4652`—`4654` 的 AXED 兼容记录及中文标题映射。

### 落地状态

- [x] 3/3 生命周期与语言证据裁定（2 项新增，1 项复用）
- [x] 单一翻译写入者名称落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-057`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T175632754190000+0800-89149-05c69294cbe0`。本批裁定后的
`docs/glossary.md` SHA-256 为
`f9d428e76130f7ad06a6ed70bea09aa0859a16801a841c30d6efe440f1c99336`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`34e7f6f24cd6c466a32f3b8e6a17dd705f2fdd33c0011d7c5dea7e782a24f9a3`。

## Fire Storm 词形系列

边界：包含完整 `Fire Storm` 的 2 项标题；1 项现行，1 项已移除兼容。

| Enum | 生命周期 / 等级 / 学派 / flags | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_FIRE_STORM` | 现行 / 9 / 咒法、火焰 / `target, needs_tracer` | 火焰风暴 | 在目标处制造大范围火焰爆炸，留下短暂火旋涡；一半伤害无视火焰抗性 | 保留 |
| `SPELL_CHANT_FIRE_STORM` | 已移除兼容 | 咏唱火焰风暴 | 无当前描述或实现 | 保留 |

名称结论：现行标题准确表达法术的火焰属性、风暴规模和 9 级宏大强度；
兼容标题完整保留 `Chant` 的咏唱动作及基础法术名。两项均忠实且不误导。

描述审阅发现一项 Needs Fix：Fire Storm 末句“它造成的一半伤害，火抗
无法抵御”语序生硬。本批改为“一半伤害无视火焰抗性”，机制不变。

证据：`spl-data.h:476`—`483`、`spl-data.h:4647`、
`dat/descript/spells.txt:688`—`692`、`spl-cast.cc:1346`—`1347`
及 `beam.cc:3147`—`3161`。

### 落地状态

- [x] 2/2 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-058`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T175912759124000+0800-96031-f7109482eddb`。本批裁定后的
`docs/glossary.md` SHA-256 为
`e1c9a71325bc68d058d325f98196788d46c52bd5f462b0a30d63d06266944f91`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`34e7f6f24cd6c466a32f3b8e6a17dd705f2fdd33c0011d7c5dea7e782a24f9a3`。

## Haste 词形系列

边界：标题含 `Haste` 的 3 项法术；2 项现行，1 项已移除兼容。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_HASTE` | 现行 | 加速 | 提高施法者行动速度 | 保留 |
| `SPELL_HASTE_OTHER` | 现行 | 加速他人 | 提高附近盟友行动速度 | 保留 |
| `SPELL_HASTE_PLANTS` | 已移除兼容 | 加速植物 | 无当前描述或实现 | 保留 |

名称结论：三项稳定采用 `Haste → 加速`，并以后置受事者区分自身、他人
与植物；译名自然且没有误示持续时间或额外效果。

现行两项中英文描述准确一致；兼容标题无当前描述或实现。

证据：`spl-data.h:231`—`239`、`spl-data.h:1684`—`1693`、
`spl-data.h:4673`，`dat/descript/spells.txt:939`—`950`。

### 落地状态

- [x] 3/3 生命周期、机制证据与名称裁定
- [x] 无游戏文本修改
- [x] translation profile
- [x] 系列裁定登记（`D-C-059`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T180057618805000+0800-105-748f34c7c12b`。本批裁定后的
`docs/glossary.md` SHA-256 为
`cd03726dadca42a76a52fe76dd6f16f4738a993f50251293048946e6aed285db`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`34e7f6f24cd6c466a32f3b8e6a17dd705f2fdd33c0011d7c5dea7e782a24f9a3`。

## Invisibility 词形系列

边界：标题含 `Invisibility` 的 2 项现行法术。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_INVISIBILITY` | 隐身术 | 使施法者隐形 | 保留 |
| `SPELL_INVISIBILITY_OTHER` | 隐身他人 | 使附近盟友隐形 | 重译为“使他人隐形” |

名称结论：“隐身术”作为自身法术名自然明确；“隐身他人”把不及物的
“隐身”机械用作及物动词，改为“使他人隐形”以明确受事者与结果状态。

两项中英文描述准确一致，不需要修改。

证据：对应 `spl-data.h` 两项条目及
`dat/descript/spells.txt:1076`—`1082`。

### 落地状态

- [x] 2/2 机制证据与名称裁定
- [x] 单一翻译写入者名称落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-060`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T180330242874000+0800-6605-140e18dd488e`。本批裁定后的
`docs/glossary.md` SHA-256 为
`2e035cc7fa6b46892579a755db4589768f92ba2ac233b3228bef9c8f1792d2f9`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`c392f90fa10ecbdf48d9fdcf1e7f47cbf16d18454c2043495490bdf34dd5fff1`。

## Abjuration 词形系列

边界：标题含 `Abjuration` 的 2 项法术；1 项现行，1 项已移除兼容。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_ABJURATION` | 现行 | 驱逐术 | 缩短附近所有敌对召唤生物的剩余存续时间 | 保留 |
| `SPELL_AURA_OF_ABJURATION` | 已移除兼容 | 驱逐灵气 | 无当前描述或实现 | 保留 |

名称结论：“驱逐”准确表达让召唤生物提前离场，不会误示普通击退；
“驱逐灵气”沿用相同词根，作为兼容标题自然明确。

现行中文描述语义正确但“附近任何敌对的召唤物”结构冗余，本批润色为
“附近所有敌对召唤生物”，与英文 any nearby hostile summoned creatures
一致。

证据：`spl-data.h` 的现行 Abjuration 条目、Aura of Abjuration 兼容记录，
以及 `dat/descript/spells.txt:2`—`4`。

### 落地状态

- [x] 2/2 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者描述润色
- [x] translation profile
- [x] 系列裁定登记（`D-C-061`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T180448437054000+0800-9047-5f09f674dad3`。本批裁定后的
`docs/glossary.md` SHA-256 为
`60ef8d04e4ec41f1156b3b50e2612600bf7ec2792e2cadfbb5c4a51859caa120`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`c392f90fa10ecbdf48d9fdcf1e7f47cbf16d18454c2043495490bdf34dd5fff1`。

## Infusion 词形系列

边界：标题含 `Infusion` 的 3 项法术，全部为已移除兼容记录。

| Enum | 当前译名 | 机制证据 | 裁定 |
|---|---|---|---|
| `SPELL_EPHEMERAL_INFUSION` | 短暂灌注 | 无当前描述或实现 | 保留 |
| `SPELL_INFUSION` | 灌注术 | 无当前描述或实现 | 保留 |
| `SPELL_LETHAL_INFUSION` | 致命灌注 | 无当前描述或实现 | 保留 |

名称结论：三项稳定采用 `Infusion → 灌注`，修饰语位置自然；单独成名的
“灌注术”也符合中文法术名习惯。缺少当前机制证据，不作推测性改名。

证据：`spl-data.h:4662`、`spl-data.h:4678`、`spl-data.h:4680`
的 AXED 兼容记录及中文标题映射。

### 落地状态

- [x] 3/3 生命周期与名称裁定
- [x] 无游戏文本修改
- [x] translation profile
- [x] 系列裁定登记（`D-C-062`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T180655285530000+0800-13139-525f35b6ef1c`。本批裁定后的
`docs/glossary.md` SHA-256 为
`29260c7727bfea4f1ff0ce097806af61521baab73d7a431b1722e3ba552b505a`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`c392f90fa10ecbdf48d9fdcf1e7f47cbf16d18454c2043495490bdf34dd5fff1`。

## Song 词形系列

边界：标题含 `Song` 的 3 项法术；2 项现行，1 项已移除兼容。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_SIREN_SONG` | 现行 | 塞壬之歌 | 迷魂附近听众；限制冒险者远离并眩晕其他生物 | 保留 |
| `SPELL_AVATAR_SONG` | 现行 | 化身之歌 | 更强的歌声效果，且可能从深水召来溺魂 | 保留 |
| `SPELL_SONG_OF_SHIELDING` | 已移除兼容 | 护盾之歌 | 无当前描述或实现 | 保留 |

名称结论：三项自然采用“X之歌”结构，分别保留塞壬、化身和护盾意象；
标题无需枚举意志抵抗、移动限制、眩晕或召来溺魂等后续机制。

现行两项中英文描述准确一致；兼容标题无当前描述或实现。

证据：对应 `spl-data.h` 三项条目及 `dat/descript/spells.txt:76`—`85`、
`1896`—`1902`。

### 落地状态

- [x] 3/3 生命周期、机制证据与名称裁定
- [x] 无游戏文本修改
- [x] translation profile
- [x] 系列裁定登记（`D-C-063`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T180907580005000+0800-17233-7a0d313eb6e6`。本批裁定后的
`docs/glossary.md` SHA-256 为
`de13b8ddbe0891b689ce97e9637405d5f4dc57b61a8dfb6d7ae6f08ef8f5af36`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`c392f90fa10ecbdf48d9fdcf1e7f47cbf16d18454c2043495490bdf34dd5fff1`。

## Animate 词形系列

边界：标题以 `Animate` 开头的 2 项法术；1 项现行，1 项已移除兼容。

| Enum | 生命周期 / 等级 / 学派 / flags | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_ANIMATE_DEAD` | 现行 / 4 / 死灵 / `helpful, no_ghost` | 操纵死尸 | 施法后一段时间内，杀死的活物有概率化作丧尸复起 | 保留 |
| `SPELL_ANIMATE_SKELETON` | 已移除兼容 | 召唤骷髅 | 无当前描述或实现 | 修正为“操纵骷髅” |

名称结论：“操纵死尸”准确保留驱使尸体行动的死灵意象；“召唤骷髅”
把 Animate 错译成 Summon，改为“操纵骷髅”后既忠实原名，也恢复系列
词根一致性。

描述审阅发现一项 Needs Fix：“复活成丧尸／复活怪物”容易误示真正
复生。本批改为“化作丧尸复起”，保留生成概率、持续时间、重施遣散及
离开楼层遣散等全部机制。

证据：`spl-data.h:600`—`607`、`spl-data.h:4742`、
`dat/descript/spells.txt:47`—`52`、`mon-death.cc:2004`—`2014`
及 `spl-other.cc:85`—`101`。

### 落地状态

- [x] 2/2 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者名称与描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-064`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T181106715819000+0800-23171-2de6fad2050b`。本批裁定后的
`docs/glossary.md` SHA-256 为
`b2586168f5593fe9f9af9e364e98162a644d54876bb914ff663d1a25c0dd2610`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`18c48b881a3dd29790ab0387d80ea51ae1e9d5ed27396991365e9066a9b32f42`。

## Shot 词形系列

边界：英文标题以独立 `Shot` 结尾、且尚未在其他系列审阅的 3 项现行
怪物法术。`Shadow Shot` 已在 Shadow 系列完成，不重复计数。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_CRYSTALLISING_SHOT` | 现行 | 结晶射击 | 投掷水晶碎片，可能使目标脆化并增加其所受全部伤害 | 保留 |
| `SPELL_HARPOON_SHOT` | 现行 | 鱼叉射击 | 带刺重物命中后将目标拉近，受阻时发生碰撞 | 保留 |
| `SPELL_IRON_SHOT` | 现行 | 铁弹 | 掷出巨大沉重的金属弹体 | 保留 |

名称结论：`shot` 在前两项中表示一次特征明确的射击，采用“射击”自然；
`Iron Shot` 中则指所发射的重型金属弹体，沿用“铁弹”比机械译作
“铁射击”准确。三项标题均符合当前效果与描述。

描述审阅发现 `Crystallising Shot` 中文仍记录旧版寒冷伤害和冰霜路障，
与英文及现行实现不符；现已重译为水晶碎片命中并可能施加全伤害脆化。
`Harpoon Shot` 与 `Iron Shot` 中英文描述一致。

证据：`spl-data.h:871`—`879`、`3303`—`3311`、
`3813`—`3821`，`dat/descript/spells.txt:451`—`455`、
`943`—`946`、`1084`—`1086`，以及 `beam.cc:7705`—`7710`。

### 落地状态

- [x] 3/3 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-065`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T181252321852000+0800-27174-0717d678616c`。本批裁定后的
`docs/glossary.md` SHA-256 为
`f6f79c7688c96524f5cbde26bc0a1820a742fe16e6eecfeff858671eb6117929`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`18c48b881a3dd29790ab0387d80ea51ae1e9d5ed27396991365e9066a9b32f42`。

## Hurl 词形系列

边界：英文标题以 `Hurl` 开头的 3 项现行法术。

| Enum | 生命周期 | 原译名 | 审阅后译名 | 核心效果 | 裁定 |
|---|---|---|---|---|---|
| `SPELL_HURL_DAMNATION` | 现行 | 投掷诅咒 | 投掷天谴 | 对目标及相邻生物造成无视常规防护的天谴伤害 | 修改 |
| `SPELL_HURL_SLUDGE` | 现行 | 投掷污泥 | 投掷污泥 | 剧毒污泥伤害、中毒并浸湿目标周围 | 保留 |
| `SPELL_HURL_TORCHLIGHT` | 现行 | 投掷火炬之光 | 投掷火炬之光 | 暗影火炬光伤害生者、恶魔和神圣生物，并强化友方亡灵 | 保留 |

名称结论：三项统一采用 `Hurl → 投掷`。`Hurl Damnation` 的
`Damnation` 是无视护甲和抗性的专门伤害机制，不是 curse；原译
“投掷诅咒”会误示状态效果，现统一为既有能力术语“投掷天谴”。

描述审阅确认 `Hurl Sludge` 与英文一致；两项复用 ability 文本的法术中，
修正了天谴描述的错字、相邻范围和护甲术语，以及火炬之光描述中的
伊莱德莱姆努尔译名和不自然类别表述。

证据：`spl-data.h:1342`—`1352`、`3492`—`3500`、
`3880`—`3888`，`dat/descript/spells.txt:980`—`988`、
`1021`—`1025`，以及 `dat/descript/ability.txt:67`—`73`、
`306`—`314`。

### 落地状态

- [x] 3/3 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者名称与共用描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-066`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T181513641783000+0800-30670-a2c6d4330735`。本批裁定后的
`docs/glossary.md` SHA-256 为
`40f5af29d5cda809fcf9a2c8fc7376a4da6e88ddf6ad1ad60a2661867b108556`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`3799be0da35c486f957e2336146596875cddb75ff522e561762abe1f9b000519`。

## Launch 词形系列

边界：英文标题以 `Launch` 开头的 3 项现行法术。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_LAUNCH_SPORANGIUM` | 发射孢子囊 | 发射追踪目标并以酸液爆炸的孢子囊 | 保留 |
| `SPELL_CLOCKWORK_BEE` | 发射发条蜜蜂 | 制造、上紧发条并放出机械蜜蜂 | 保留 |
| `SPELL_DEPLOY_BOMBLET` | 发射小型炸弹 | 以无视火线的弹道命中目标并在附近部署炸弹 | 保留 |

名称结论：三项均实际将相应实体投送到战场，采用 `Launch → 发射`
准确自然。描述审阅重译了 `Launch Bomblet` 的现行弹道、部署和目标限制，
并将 `Launch Sporangium` 误写的“孢子囊间距”修正为原生质体生成间距。
`Launch Clockwork Bee` 中英文一致。

证据：`spl-data.h:3359`—`3367`、`4230`—`4238`、
`4329`—`4337`，`dat/descript/spells.txt:1141`—`1167`。

### 落地状态

- [x] 3/3 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-067`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T181700801813000+0800-34284-6a659ade6bd3`。本批裁定后的
`docs/glossary.md` SHA-256 为
`8dc14c4f4072fb1707ca79ec3d0cbba7861e4dd0b82e76be9fd91b8efaa5194d`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`3799be0da35c486f957e2336146596875cddb75ff522e561762abe1f9b000519`。

## Blast 词形系列

边界：英文标题含独立 `Blast`、且尚未在其他系列审阅的 3 项法术；
2 项现行，1 项已移除兼容。`Iskenderun's Mystic Blast` 已在
Iskenderun's 专名系列完成，不重复计数。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_WIND_BLAST` | 现行 | 风击 | 锥形强风推开生物和云雾，碰撞造成伤害 | 保留 |
| `SPELL_FORTRESS_BLAST` | 现行 | 堡垒冲击 | 延时形成大范围动能波，伤害完全取决于施法者护甲 | 保留 |
| `SPELL_SILVER_BLAST` | 已移除兼容 | 白银冲击 | 无当前描述或实现 | 暂缓术语（恢复时复审） |

名称结论：`blast` 可描述爆发性的风力或冲击波；“风击”和“堡垒冲击”
分别贴合介质与表现，无需机械统一。已移除标题没有现行机制可供反推。

描述审阅发现 `Fortress Blast` 中文仍写成旧版即时击退。现已按英文重译，
恢复以身体强度蓄积动能波、蓄力期间固定、被位移会取消、法术威力缩短
蓄力时间，以及护甲值独立决定伤害等规则。`Wind Blast` 描述准确。

证据：`spl-data.h:2276`—`2284`、`4374`—`4382`、
`4693`，`dat/descript/spells.txt:777`—`788`、
`2417`—`2420`。

### 落地状态

- [x] 3/3 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-068`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T181928468775000+0800-39038-0a2d89f8b24d`。本批裁定后的
`docs/glossary.md` SHA-256 为
`4f42d8c8c30740101aeb87e90c53e0b18fb5ab6021f2850b6c61c502079f7b49`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`3799be0da35c486f957e2336146596875cddb75ff522e561762abe1f9b000519`。

## Blade 词形系列

边界：英文标题含独立 `Blade` 的 3 项法术；1 项现行，2 项已移除兼容。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_RENDING_BLADE` | 现行 | 撕裂之刃 | 近战命中时能量刃在附近敌人间来回撕裂 | 保留 |
| `SPELL_SURE_BLADE` | 已移除兼容 | 精准之刃 | 无当前描述或实现 | 保留 |
| `SPELL_BLADE_HANDS` | 已移除兼容 | 利刃之手 | 无当前描述或实现 | 保留 |

名称结论：三项均以“刃”准确表达 blade；现行标题中的“撕裂”与来回切割
附近敌人的机制直接一致。两项已移除标题语义清楚，无需用过期机制反推。

描述审阅发现 `Rending Blade` 原中文遗漏大部分机制，已重译并补全来回
攻击、无法抵抗、暂时封存所有剩余法力、利刃消失时返还及每点法力增伤。

证据：`spl-data.h:4407`—`4415`、`4703`、`4736`，
`dat/descript/spells.txt:1679`—`1690`。

### 落地状态

- [x] 3/3 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-069`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T182153183146000+0800-44297-3ae573315201`。本批裁定后的
`docs/glossary.md` SHA-256 为
`dfeb3df6068a899f58dbfda74cfb0ac61fee3a5b1308066d297191e1059513cb`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`3799be0da35c486f957e2336146596875cddb75ff522e561762abe1f9b000519`。

## Destruction 词形系列

边界：英文标题含独立 `Destruction` 的 4 项现行法术。

| Enum | 原译名 | 审阅后译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_IOOD` | 毁灭法球 | 毁灭法球 | 缓慢追踪目标、初生时伤害较低的纯魔力法球 | 保留 |
| `SPELL_LEGENDARY_DESTRUCTION` | 传奇毁灭 | 传奇毁灭 | 立刻连续产生两个随机爆炸法术效果 | 保留 |
| `SPELL_MAJOR_DESTRUCTION` | 大型毁灭 | 强力毁灭 | 向目标随机发射有害射束或爆炸 | 修改 |
| `SPELL_UNLEASH_DESTRUCTION` | 释放毁灭 | 释放毁灭 | 马科列布能力使用的虚拟法术 | 保留 |

名称结论：四项稳定采用 `Destruction → 毁灭`。`Major` 在此表示法术
强度级别，不是实体尺寸或范围；“大型毁灭”生硬且易误导，改为
“强力毁灭”。术语表中的“毁灭之球”并非当前游戏标题，已同步为
实际使用的“毁灭法球”。

四项中英文描述与现行效果一致，无需修改描述文本。

证据：`spl-data.h:1785`—`1793`、`2410`—`2418`、
`2487`—`2497`、`3867`—`3877`，
`dat/descript/spells.txt:1191`—`1194`、`1230`—`1232`、
`1436`—`1447`，以及 `dat/descript/ability.txt:379` 起的
马科列布能力描述。

### 落地状态

- [x] 4/4 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者名称落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-070`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T182359223415000+0800-49087-de95952fdaa1`。本批裁定后的
`docs/glossary.md` SHA-256 为
`9332b480dc96435636a289843449dfa70a05b002ac13262760a4dd15b6739c5c`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`dfb2d3c1272afacf21d92cce46a0d8ca727c66118ef0fea25ea0735190bbdfa6`。

## Warp 词形系列

边界：英文标题以 `Warp` 开头的 3 项法术；2 项现行，1 项已移除兼容。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_WARP_SPACE` | 现行 | 扭曲空间 | 空间裂隙造成范围伤害并可能令目标短距闪现 | 保留 |
| `SPELL_WARP_BODY` | 现行 | 扭曲身体 | 造成少量伤害和短暂变异，变异过多时改为玻璃化 | 保留 |
| `SPELL_WARP_BRAND` | 已移除兼容 | 扭曲武器 | 无当前描述或实现 | 保留 |

名称结论：三项均准确采用 `Warp → 扭曲` 并指出被改变的空间、身体或武器；
标题不需枚举伤害、变异、玻璃化或闪现等后续机制。

两项现行中文描述均对应旧机制。`Warp Body` 已修正目标并补全少量伤害、
短暂变异及玻璃化替代；`Warp Space` 已从单体随机传送重译为范围裂隙伤害
及偶发短距闪现。已移除的 `Warp Weapon` 无当前描述或实现。

证据：`spl-data.h:3281`—`3289`、`4530`—`4539`、`4706`，
`dat/descript/spells.txt:2396`—`2405`。

### 落地状态

- [x] 3/3 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-071`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T182538532243000+0800-52509-49e725d5d0a4`。本批裁定后的
`docs/glossary.md` SHA-256 为
`1b57cedae1d0164d49f5c8073abf8a9ba75401b208ad9abdda6993d6dea92801`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`dfb2d3c1272afacf21d92cce46a0d8ca727c66118ef0fea25ea0735190bbdfa6`。

## Might/Other 目标系列

边界：尚未审阅的 4 项 `Other` 后缀法术及与其中一项成对的基础
`Might`，共 5 项现行法术。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_MIGHT` | 强壮 | 提高施法者造成的近战伤害 | 保留 |
| `SPELL_MIGHT_OTHER` | 强壮他人 | 提高附近友方造成的近战伤害 | 保留 |
| `SPELL_HEAL_OTHER` | 治愈他人 | 治疗附近友方 | 保留 |
| `SPELL_BERSERK_OTHER` | 狂暴他人 | 使附近友方狂暴，提升生命、速度和近战伤害 | 保留 |
| `SPELL_REGENERATE_OTHER` | 再生他人 | 使其他生物短时快速再生，恢复量随最大生命值提高 | 保留 |

名称结论：四项 `Other` 标题均以紧凑的“X他人”清楚标示目标，与既有
“加速他人”等标题一致。`Might → 强壮` 是法术显示标题；机制和状态域
可继续使用“强效”，二者不应在本批机械替换。

描述审阅修正 `Might` 与 `Might Other` 的“近战的攻击力”病句，并为
`Regenerate Other` 补回按目标最大生命值计算恢复量的规则；同时修正
`Heal Other` 的 ally 术语和语序，以及 `Berserk Other` 的单个目标表述
和近战伤害术语。

证据：`spl-data.h:1818`—`1826`、`1906`—`1915`、
`2860`—`2868`、`3835`—`3843` 及基础 `Might` 条目，
`dat/descript/spells.txt:131`—`134`、`972`—`974`、
`1351`—`1358`、`1674`—`1677`。

### 落地状态

- [x] 5/5 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-072`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T182929824503000+0800-60256-156463cba939`。本批裁定后的
`docs/glossary.md` SHA-256 为
`eb00287ea625d3fcae5c5b5c1afc8966687b12ed7922e7a9457bc7b7e6979ef4`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`dfb2d3c1272afacf21d92cce46a0d8ca727c66118ef0fea25ea0735190bbdfa6`。

## Vortex 词形系列

边界：英文标题含独立 `Vortex` 的 2 项法术；1 项现行，1 项已移除兼容。

| Enum | 生命周期 | 原译名 | 审阅后译名 | 核心效果 | 裁定 |
|---|---|---|---|---|---|
| `SPELL_POLAR_VORTEX` | 现行 | 极地漩涡 | 极地漩涡 | 冰冻漩涡随施法者移动，伤害并抛动范围内生物 | 保留 |
| `SPELL_VORTEX` | 已移除兼容 | 涡流 | 漩涡 | 无当前描述或实现 | 修改 |

名称结论：法术标题统一采用 `Vortex → 漩涡`，准确表达围绕中心旋转、
卷起并抛动生物的形态；基础兼容标题“涡流”改为“漩涡”以消除系列分裂。
TextDB 会折叠键的大小写，因此不新增重复的 `Vortex` 键，而是将既有通用
`vortex/vortices` 同步为“漩涡”，由同一运行时键提供标题译值。

现行描述机制完整；本批修正缺失中心语的病句，并明确寒冷抗性最多只能
减免一半伤害，以及漩涡无法跟随施法者完成长距离传送。

证据：`spl-data.h:454`—`462`、`4725`，
`dat/descript/spells.txt:1595`—`1604`。

### 落地状态

- [x] 2/2 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者名称与描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-073`）

验证结果：前两次 translation profile 暴露并确认了 TextDB 大小写键碰撞；
移除重复标题键、统一既有通用键后再次运行通过，0 项失败；最终 Run ID
`20260725T183434923249000+0800-69834-2b70ab6284b0`。本批裁定后的
`docs/glossary.md` SHA-256 为
`3ecd04af6784590e74e69c8420a1bbdeeb50eac3ce9f0f0dc7f4ff8896097b82`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d4a0192de4e719ba0e885085e10d9657836835f687b28306fc85d84dada150ae`。

## Strike 词形系列

边界：英文标题以独立 `Strike` 结尾、且尚未在其他系列审阅的 2 项
现行法术。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_MOMENTUM_STRIKE` | 动量打击 | 借用施法者未来移动能量攻击，之后短时无法移动 | 保留 |
| `SPELL_RESONANCE_STRIKE` | 共鸣打击 | 经目标附近造物级联，每个造物都会增强伤害 | 保留 |

名称结论：两项均以 `Strike → 打击` 表示直接攻击；“动量”与未来移动
能量代价相符，“共鸣”则准确概括附近造物逐级增强的机制。

两项中英文描述准确一致，无需修改游戏文本。

证据：`spl-data.h:1029`—`1037`、`3170`—`3178`，
`dat/descript/spells.txt:1691`—`1695`、`2346`—`2350`，
以及 `mon-cast.cc:6739`—`6752`。

### 落地状态

- [x] 2/2 生命周期、机制证据与名称裁定
- [x] 无游戏文本修改
- [x] translation profile
- [x] 系列裁定登记（`D-C-074`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T183602136034000+0800-72441-2074faa1fbf0`。本批裁定后的
`docs/glossary.md` SHA-256 为
`23a062383788808870dedd2e2c72c339c41fa1f13452db8dd466c7c040389187`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d4a0192de4e719ba0e885085e10d9657836835f687b28306fc85d84dada150ae`。

## Sacrifice 词形系列

边界：英文标题含独立 `Sacrifice` 的 2 项法术；1 项现行，1 项已移除兼容。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_GHOSTLY_SACRIFICE` | 现行 | 幽灵献祭 | 吞噬友方并产生汲取范围内活物的负能量爆发 | 保留 |
| `SPELL_SACRIFICE` | 已移除兼容 | 献祭 | 无当前描述或实现 | 保留 |

名称结论：两项均以 `Sacrifice → 献祭` 准确表达不可逆地消耗生物或其
本质作为法术代价；现行标题中的“幽灵”保留负能量与鬼魅意象。

描述审阅发现 `motivating essence` 被误译成“行动力”，且原中文将彻底
吞噬、抹除献祭对象弱化为“衰竭或破坏”。现已重译，并明确燃料既可为
活物也可为造物。

证据：`spl-data.h:3181`—`3189` 及 `SPELL_SACRIFICE` 兼容条目，
`dat/descript/spells.txt:879`—`883`，`mon-cast.cc:4570` 起。

### 落地状态

- [x] 2/2 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-075`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T183745913739000+0800-76159-0d7a5c6144c0`。本批裁定后的
`docs/glossary.md` SHA-256 为
`55e88b1b9bf2a66c337a4ec7fb27cc935467686af6f10bacbef928661fcef5b7`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d4a0192de4e719ba0e885085e10d9657836835f687b28306fc85d84dada150ae`。

## Regeneration 词形系列

边界：英文标题含独立 `Regeneration` 的 2 项法术；1 项现行，
1 项已移除兼容。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_MASS_REGENERATION` | 现行 | 群体再生 | 使附近所有友方怪物快速再生 | 保留 |
| `SPELL_REGENERATION` | 已移除兼容 | 再生 | 无当前描述或实现 | 保留 |

名称结论：两项采用 `Regeneration → 再生`，现行范围修饰
`Mass → 群体`，准确清晰。术语表旧记“快速再生”与 inventory 不符，
已同步为实际兼容标题“再生”。

描述审阅发现 `Mass Regeneration` 中文错误包含施法者，且漏掉每个目标
按自身最大生命值计算恢复量；现已按英文修正。

证据：`spl-data.h:3846`—`3854`、`4688`，
`dat/descript/spells.txt:1298`—`1302`。

### 落地状态

- [x] 2/2 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-076`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T183922443035000+0800-78133-08bcc7e78e87`。本批裁定后的
`docs/glossary.md` SHA-256 为
`91ad17c22f6f5073f0eff020de5705d0f42929b9a6be9c0d20970957d0b2e1ce`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d4a0192de4e719ba0e885085e10d9657836835f687b28306fc85d84dada150ae`。

## Recall 词形系列

边界：英文标题含独立 `Recall` 的 2 项法术；1 项现行，1 项已移除兼容。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_WORD_OF_RECALL` | 现行 | 召回之言 | 短暂延迟后召回同层有智慧盟友 | 保留 |
| `SPELL_RECALL` | 已移除兼容 | 召回术 | 无当前描述或实现 | 保留 |

名称结论：两项稳定采用 `Recall → 召回`；“召回之言”准确保留通过咒言
发动的形式，“召回术”则是清楚的基础兼容标题。

现行中英文描述准确一致；兼容标题无当前描述或实现。

证据：`spl-data.h:2151`—`2160` 及 `SPELL_RECALL` 兼容条目，
`dat/descript/spells.txt:2427`—`2430`。

### 落地状态

- [x] 2/2 生命周期、机制证据与名称裁定
- [x] 无游戏文本修改
- [x] translation profile
- [x] 系列裁定登记（`D-C-077`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T184056759233000+0800-81683-47babba25821`。本批裁定后的
`docs/glossary.md` SHA-256 为
`ef86ef1acef786476003c625377eee8812243d529fe66477cd2524478e6bab64`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d4a0192de4e719ba0e885085e10d9657836835f687b28306fc85d84dada150ae`。

## Phantom 词形系列

边界：英文标题含独立 `Phantom` 的 2 项现行法术。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_PHANTOM_MIRROR` | 幻影镜 | 制造较脆弱但近似原体的怪物幻影 | 保留 |
| `SPELL_PHANTOM_BLITZ` | 幻影突击 | 编织并发射拥有施法者同等战斗能力的幻影复制体 | 保留 |

名称结论：两项稳定采用 `Phantom → 幻影`，准确表示近似原体、但更脆弱
或短暂存在的复制物；“镜”和“突击”分别对应复制媒介与发射式攻击。

描述审阅发现 `Phantom Blitz` 中文仍写成施法者自身化为幻影冲刺，
与英文和实现不符。现已重译为编织并发射施法者复制体，说明复制体保有
同等武艺和神秘力量；`Phantom Mirror` 原文漏掉“almost”的限定，
已修正为“几乎与原体无异”。

证据：`spl-data.h:2609`—`2617`、`4047`—`4055`，
`dat/descript/spells.txt:1528`—`1537`，
`beam.cc:2774`—`2808` 及召唤上限表 `spl-summoning.cc:2516`。

### 落地状态

- [x] 2/2 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者完成 2 项描述修复
- [x] translation profile
- [x] 系列裁定登记（`D-C-078`）

验证结果：覆盖两项描述修复的 `verify_zh.sh --profile translation`
通过，0 项失败；Run ID
`20260725T184449555127000+0800-90256-28f3c8c24ac6`。本批裁定后的
`docs/glossary.md` SHA-256 为
`84583fd23a5b0fe50e5b9893b8ccc47ec5314af68dd2de5d1e1aedde175e877f`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d4a0192de4e719ba0e885085e10d9657836835f687b28306fc85d84dada150ae`。

## Missiles 词形系列

边界：英文标题含 `Deflect Missiles` 的 2 项法术；1 项现行，
1 项已移除兼容。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_DEFLECT_MISSILES` | 现行 | 偏转飞弹 | 排斥力场提高对所有投射物的闪避，无法行动时仍有效 | 保留 |
| `SPELL_OLD_DEFLECT_MISSILES` | 已移除兼容 | 旧版偏转飞弹 | 无当前描述或实现 | 保留 |

名称结论：“偏转飞弹”准确概括通过排斥力场改变投射物轨迹的防御效果；
兼容标题加“旧版”明确其生命周期，无需另行反推机制。

现行中文描述仍记录旧版单目标攻击与穿透攻击的回避差异，现已按英文重译，
明确效果覆盖所有投射物，且施法者无法行动时仍然有效。

证据：`spl-data.h:745`—`753`、`4658`，
`dat/descript/spells.txt:486`—`489`。

### 落地状态

- [x] 2/2 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-079`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T184650171778000+0800-94228-1d2a76d8a21c`。本批裁定后的
`docs/glossary.md` SHA-256 为
`aa5faa5c3ea400487da58d98edec2aac67a84e3ca4a0dab86d504df49cf81c7f`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d4a0192de4e719ba0e885085e10d9657836835f687b28306fc85d84dada150ae`。

## Healing 强度系列

边界：英文标题以 `Healing` 为核心、由 `Minor` 与 `Major`
区分强度的 2 项现行法术。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_MINOR_HEALING` | 现行 | 小型治疗 | 治疗施法者身体所受的少量伤害 | 保留 |
| `SPELL_MAJOR_HEALING` | 现行 | 大型治疗 | 治疗施法者身体所受的大量伤害 | 保留 |

名称结论：两项稳定采用 `Healing → 治疗`，并以
`Minor → 小型`、`Major → 大型` 表达明确强度递进。其 2 级与 6 级、
少量与大量自我治疗机制相符，名称无需加入额外目标或数值。

描述审阅发现旧中文把 `small/large amount of damage` 误写成
“小部分/大部分创伤”，容易被理解为按既有伤势比例治疗；现已恢复
“身体所受的少量/大量伤害”语义。

证据：`spl-data.h:1309`—`1328`，
`dat/descript/spells.txt:1234`—`1236`、`1365`—`1367`，
`mon-cast.cc:255`—`260`、`1356`—`1365`、`7800`—`7802`。

### 落地状态

- [x] 2/2 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者完成 2 项描述修复
- [x] translation profile
- [x] 系列裁定登记（`D-C-080`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T184937956296000+0800-1709-bf1542442a5f`。本批裁定后的
`docs/glossary.md` SHA-256 为
`925120dc0847a33307f0a76e85b27933cad16b4c95e97e8c63f363ba4f52c1a8`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`d4a0192de4e719ba0e885085e10d9657836835f687b28306fc85d84dada150ae`。

## Injury 词形系列

边界：英文标题以 `Injury` 开头的 2 项现行怪物法术。

| Enum | 等级 / 学派 / flags | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_INJURY_MIRROR` | 4 / 无 / `selfench, monster` | 伤害反射 | 短时间把所受伤害反射给攻击者，结束后暂时无法再次施放 | 保留 |
| `SPELL_INJURY_BOND` | 5 / 妖术 / `helpful, monster` | 伤害链接 | 与附近盟友联结，使其伤害减半，施法者承担被阻止伤害的一半 | 微调为“伤害联结” |

系列结论：`Mirror → 反射` 准确表达以所受伤害触发对攻击者的反馈；
`Bond` 及英文描述中的 `Binds` 强调施法者与盟友间建立的关系，
“链接”带有较强的技术语感，改为“联结”更符合魔法效果，也与伤害反射
形成清楚区分。

`Injury Mirror` 中文描述与英文机制一致。`Injury Bond` 旧描述用
“转移一半伤害”概括结果，但未明确盟友先获得伤害减半、施法者再承受
被阻止伤害的一半；现已按英文描述重译。

被拒方案：“伤害纽带”容易被理解为伤害本身形成的实体；“伤势联结”
偏离标题中更宽泛的 damage/injury 机制语义；保留“伤害链接”则语体
不够自然。

证据：`spl-data.h:1941`—`1948`、`2164`—`2171`，
`dat/descript/spells.txt:1055`—`1064`、
`dat/descript/zh/spells.txt:668`—`676`、
`mon-cast.cc:1393`、`4688`、`8311`—`8323`、
`monster.cc:4268`—`4273`。

### 落地状态

- [x] 2/2 机制证据与名称裁定
- [x] 单一翻译写入者完成名称与描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-081`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T185211631005000+0800-8084-fae7b846fb79`。本批裁定后的
`docs/glossary.md` SHA-256 为
`1076ac9ecbeffdb7447bd913e0fb0b01bb8c4db9fdc164c8623dd2a9b8c41923`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`4a194db035d4f372a80378bb5ce3f3573ea44d5c5e634909ce57c6a6deac5e42`。

## Ensnare 词形系列

边界：英文标题含 `Ensnare` 的 2 项现行怪物法术。

| Enum | 等级 / 学派 / flags | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_ENSNARE` | 6 / 咒法、妖术 / `dir_or_target, needs_tracer, monster` | 束缚 | 射出高命中蛛网，困住单个目标 | 保留 |
| `SPELL_GREATER_ENSNARE` | 6 / 咒法、妖术 / `dir_or_target, needs_tracer, monster` | 强力束缚 | 更高命中地困住目标，并在附近散布 3–6 张短时蛛网 | 保留 |

系列结论：两项都以蛛网困住目标为核心，`Ensnare → 束缚` 准确；
Greater 版提高命中，并把控制扩展到目标附近，现有“强力束缚”能够自然
表达同源强化，不必改成只强调数量的“蛛网散布”。

普通版中文描述与英文机制一致。Greater 版旧中文仍称其“大幅降低闪避和
格挡能力”，当前英文与实现均无此效果；现已重译为困住目标并在附近散布
会短时消散的额外蛛网。

证据：`spl-data.h:2029`—`2051`，
`dat/descript/spells.txt:638`—`640`、`927`—`930`，
`dat/descript/zh/spells.txt:454`—`456`、`1724`—`1727`，
`mon-cast.cc:2472`—`2487`、`beam.cc:2812`—`2825`。

### 落地状态

- [x] 2/2 机制证据与名称裁定
- [x] 单一翻译写入者完成描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-082`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T185400584507000+0800-11877-38c230fa39a0`。本批裁定后的
`docs/glossary.md` SHA-256 为
`9e5b0830967bf1f52ccf60e0cbd70dd8075b5ad533d2eff41034ac0e2433ef07`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`4a194db035d4f372a80378bb5ce3f3573ea44d5c5e634909ce57c6a6deac5e42`。

## Malign 词形系列

边界：英文标题以 `Malign` 开头的 2 项现行法术。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_MALIGN_GATEWAY` | 现行 | 邪恶传送门 | 开启通往污秽异界的传送门，召来暂时受控的利爪触手 | 保留 |
| `SPELL_MALIGN_OFFERING` | 现行 | 邪恶献祭 | 汲取敌人生命并治疗附近盟友 | 保留 |

名称结论：两项稳定采用 `Malign → 邪恶`。Gateway 具有不洁、混沌属性，
并连通污秽异界；Offering 通过死灵术伤害敌人来治疗盟友。现译准确保留
负面道德色彩，同时由“传送门 / 献祭”清楚区分实体与行为。

描述审阅发现 `Malign Gateway` 中文遗漏英文 `unknown` 和
`self-sustained` 两项限定，现已补回“未知且污秽异界”和“暂时自我维系”。
`Malign Offering` 中英文描述一致。

证据：`spl-data.h:577`—`585`、`2321`—`2329`，
`dat/descript/spells.txt:1238`—`1249`，
`spl-summoning.cc:1359`—`1367`、`mon-cast.cc:9843`—`9846`。

### 落地状态

- [x] 2/2 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者完成描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-083`）

验证结果：覆盖 Malign 与后续成对词根差异的
`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T185830923643000+0800-22443-9b28b0b0f251`。本次验证后的
`docs/glossary.md` SHA-256 为
`7548bf15eaf7d86c778710dc639248c4f377f516c89ccef61d64667a3faf4c7c`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`c0ce5598b036d61d8dbd87e7801ae5817d663c3525406b8d3fee1d8edfe029fb`。

## 成对词根批次

边界：差集中仅余两个成员的 Spells、Magic、Holy、Hellfire、Golubria、
Fulsome、Forceful、Drain、Corrupt、Beckoning、Arms 与 Agony 词根；
共 23 个唯一枚举（16 项现行、7 项已移除兼容）。`Drain Magic` 同时属于
Magic 与 Drain，只计一次；Malign 两项已由 D-C-083 覆盖。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_DIMINISH_SPELLS` | 现行 | 削弱法术 | 不可抵抗地暂时削弱一个敌人的法术威力 | 保留 |
| `SPELL_CONJURE_LIVING_SPELLS` | 现行 | 召唤活体法术 | 创造多个遇敌后自行施放并消散的活体法术 | 保留 |
| `SPELL_SAP_MAGIC` | 现行 | 削弱魔法 | 目标施法后暂时失去继续施法能力 | 保留 |
| `SPELL_DRAIN_MAGIC` | 已移除兼容 | 汲取魔力 | 现存兼容描述称其造成反魔法武器般的魔力流失 | 保留 |
| `SPELL_HOLY_LIGHT` | 已移除兼容 | 圣光术 | 无当前实现与描述 | 暂缓术语（恢复时复审） |
| `SPELL_HOLY_WORD` | 已移除兼容 | 圣言术 | 无当前实现与描述 | 暂缓术语（恢复时复审） |
| `SPELL_HELLFIRE_COURT` | 现行 | 地狱火法庭 | 召唤火焰与天谴恶魔 | 保留 |
| `SPELL_HELLFIRE_MORTAR` | 现行 | 地狱火迫击炮 | 沿熔岩裂隙移动并自动发射岩浆的迫击炮 | 保留 |
| `SPELL_GOLUBRIAS_PASSAGE` | 现行 | 戈卢布里亚之通道 | 开启成对、进入即关闭的随机互通传送门 | 保留 |
| `SPELL_SHROUD_OF_GOLUBRIA` | 已移除兼容 | 戈卢布里亚之幕 | 无当前实现与描述 | 暂缓术语（恢复时复审） |
| `SPELL_FULSOME_FUSILLADE` | 现行 | 猛烈连射 | 数回合向随机敌人倾泻可叠加反应的爆炸试剂 | 保留 |
| `SPELL_FULSOME_DISTILLATION` | 已移除兼容 | 精华蒸馏 | 无当前实现与描述 | 暂缓术语（恢复时复审） |
| `SPELL_FORCEFUL_INVITATION` | 现行 | 强制邀请 | 从指定分支之一召唤生物 | 保留 |
| `SPELL_FORCEFUL_DISMISSAL` | 已移除兼容 | 强制驱逐 | 无当前实现与描述 | 暂缓术语（恢复时复审） |
| `SPELL_DRAIN_LIFE` | 现行 | 吸取生命 | 汲取附近所有敌人的生命并按伤害治疗使用者 | 微调为“汲取生命” |
| `SPELL_CORRUPT_LOCALE` | 现行 | 腐化 | 以深渊能量改变附近区域并暂时召来深渊生物 | 保留 |
| `SPELL_CORRUPT_BODY` | 已移除兼容 | 腐化躯体 | 无当前实现与描述 | 暂缓术语（恢复时复审） |
| `SPELL_BECKONING_GALE` | 现行 | 召唤强风 | 扭曲目标周围空气，造成伤害并将其拉近 | 重译为“招引之风” |
| `SPELL_BECKONING` | 现行 | 次级召唤 | 把目标拉至施法者相邻位置 | 重译为“次级招引” |
| `SPELL_BROTHERS_IN_ARMS` | 现行 | 战友 | 复用同名能力，召来战友 | 保留 |
| `SPELL_BESTOW_ARMS` | 现行 | 赐予武器 | 暂时向附近盟友授予军械库中的魔法武器 | 保留 |
| `SPELL_CURSE_OF_AGONY` | 现行 | 痛苦诅咒 | 施法者接下来两次近战命中时各将目标剩余生命减半 | 保留 |
| `SPELL_AGONY` | 现行 | 剧痛 | 将目标生命减半但不直接致死 | 保留 |

名称结论：`Beckoning` 两项都把既有目标拉近，旧译“召唤”会误示创造或
召来新实体，统一采用“招引”；Gale 由“之风”明确执行招引的是气流。
`Drain Life` 改为“汲取生命”，与 `Drain Magic → 汲取魔力` 及战斗域
`Drain → 汲取` 一致。`Arms` 在 Brothers in Arms 中指战友，在
Bestow Arms 中指武器，现译分别处理词义，不能机械统一。其余标题准确；
已移除兼容成员不以历史猜测替代当前证据。

描述审阅修正六项机制偏差：Curse of Agony 的两次命中分别触发减半；
Sap Magic 不会打断当前施法，而是在施法后短暂封锁后续施法；
Diminish Spells 是单个敌人且英文未承诺固定减半；Hellfire Mortar
补回裂隙、移动、受阻和闭合全过程；Hellfire Court 明确召唤的是两类
恶魔；Forceful Invitation 修复分支选择语序。另润色
Conjure Living Spells 的“自行施放”表述。

证据：各项等级、学派、flags 与生命周期来自 `spl-data.h` 的对应
`SPELL_*` 记录及 `AXED_SPELL` 区；描述来自
`dat/descript/spells.txt` 同名键。实现交叉核对：
`spl-summoning.cc:1362`、`2470`、`2493`—`2511`、`3369`—`3438`，
`spl-transloc.cc:1669`、`mon-cast.cc:263`—`273`、`471`、
`1505`、`2375`、`6538`、`8000`—`8063`、`8278`、`8691`、
`9843`，以及 `spl-zap.cc:90`、`111`—`112`。

### 落地状态

- [x] 23/23 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者完成 3 项名称与 7 项描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-084`）

验证结果：与 Malign 批次共同运行的 translation profile 通过，0 项失败；
Run ID `20260725T185830923643000+0800-22443-9b28b0b0f251`。
本批裁定后的 glossary 与 inventory SHA-256 分别为
`7548bf15eaf7d86c778710dc639248c4f377f516c89ccef61d64667a3faf4c7c`
和 `c0ce5598b036d61d8dbd87e7801ae5817d663c3525406b8d3fee1d8edfe029fb`。

首轮 Run ID `20260725T185650139651000+0800-19332-9b28b0b0f251`
曾在 changed exact-key terminology 阶段失败：三项新标题已写入
`source.txt`，但 glossary 尚保留旧译。同步三项术语并重新导出
`glossary.utf8` 后，上述最终运行通过；该失败未涉及 TextDB 结构或
游戏机制文本。

## 独立法术批次 A1

边界：inventory 与既有审阅证据差集中的前 20 项现行法术；这些标题没有
尚未审阅的同词根依赖，逐项独立裁定。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_CAUSE_FEAR` | 恐惧术 | 使附近生物无法接近且可能近战失手，离开视野即结束 | 保留 |
| `SPELL_APPORTATION` | 隔空取物 | 把远处物品堆顶端物品拉向施法者 | 保留 |
| `SPELL_BLASTMOTE` | 不稳定爆尘 | 生成接触火焰或生物后爆炸并击退的粉尘云 | 保留 |
| `SPELL_DIG` | 挖掘 | 在天然岩石中挖出通道 | 保留 |
| `SPELL_ARCJOLT` | 电弧震击 | 电流由近邻目标继续连锁，半数伤害无视护甲 | 保留 |
| `SPELL_POLYMORPH` | 变形术 | 随机改变生物形态，对变形生物尤其有效 | 保留 |
| `SPELL_SLOW` | 缓慢 | 减慢目标行动 | 保留 |
| `SPELL_PETRIFY` | 石化 | 连锁至多三目标，先减速再石化且承伤减半 | 保留 |
| `SPELL_CONFUSE` | 混乱 | 使目标心智陷入混乱 | 保留 |
| `SPELL_DISJUNCTION` | 空间分离 | 使施法者附近生物按距离概率闪烁远离 | 保留 |
| `SPELL_MASS_CONFUSION` | 群体混乱 | 混乱所有注视施法者的生物 | 保留 |
| `SPELL_SMITING` | 惩击 | 无需直射路径地惩击视野内指定敌人 | 保留 |
| `SPELL_CHARMING` | 魅惑 | 使敌对生物暂时倒戈；冒险者只会短暂混乱 | 保留 |
| `SPELL_PAIN` | 痛苦 | 对一个活物造成痛苦伤害 | 保留 |
| `SPELL_SOUL_SPLINTER` | 灵魂分裂 | 分出目标灵魂碎片形成魂灵并削弱本体 | 保留 |
| `SPELL_VAMPIRIC_DRAINING` | 吸血术 | 窃取相邻活物生命并给予施法者 | 保留 |
| `SPELL_HAUNT` | 鬼魂缠身 | 召唤仅攻击指定目标、目标死后消散的幽魂 | 保留 |
| `SPELL_BERSERKER_RAGE` | 狂暴之怒 | 复用狂暴能力效果 | 保留 |
| `SPELL_BANISHMENT` | 放逐 | 把生物放逐至深渊 | 保留 |
| `SPELL_STING` | 刺痛 | 发射结晶毒刺，兼具物理伤害与中毒 | 保留 |

名称结论：20 项现译均准确保留核心动作或状态，且没有会把目标、范围或
机制类别引向错误理解的措辞。`Vampiric Draining` 采用自然的“吸血术”
比机械拼接“吸血汲取”更符合中文法术名；`Smiting → 惩击` 也与其无视
直射路径的神罚式攻击吻合。

描述审阅修正六项：Apportation 的物品来自远处而非附近；
Volatile Blastmotes 会把相邻生物推开；Arcjolt 沿相连目标跳跃且半数
伤害无视护甲；Smiting 指定视野内敌人；Charm 对冒险者只造成短暂混乱；
Pain 当前英文没有施法者反噬。

证据：对应 `spl-data.h` 的 20 个 `SPELL_*` 记录、
`dat/descript/spells.txt` 与 `dat/descript/zh/spells.txt` 同名键；
实现交叉核对 `spl-transloc.cc`、`spl-zap.cc`、`mon-cast.cc`、
`spl-summoning.cc` 中对应 enum 分支及 zap 映射。

### 落地状态

- [x] 20/20 机制证据与名称裁定
- [x] 单一翻译写入者完成 6 项描述落地
- [x] translation profile
- [x] 批次裁定登记（`D-C-085`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T190249229858000+0800-30821-825be7a16f59`。本批裁定后的
`docs/glossary.md` SHA-256 为
`7548bf15eaf7d86c778710dc639248c4f377f516c89ccef61d64667a3faf4c7c`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`c0ce5598b036d61d8dbd87e7801ae5817d663c3525406b8d3fee1d8edfe029fb`。

## 独立法术批次 A2

边界：inventory 差集顺序第 21–40 项，共 20 项现行独立法术。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_SUBLIMATION_OF_BLOOD` | 血液升华 | 以部分生命换取魔法能量，且不直接致命 | 保留 |
| `SPELL_BOMBARD` | 炮击 | 轰出铁球并常使施法者后退 | 保留 |
| `SPELL_SHOCK` | 震击 | 发射反弹电击束，半数伤害无视护甲 | 保留 |
| `SPELL_SWIFTNESS` | 迅捷 | 大幅提高移动速度，结束后暂时迟缓 | 保留 |
| `SPELL_DEBUGGING_RAY` | 调试射线 | 测试用必中高伤害射线 | 保留 |
| `SPELL_MINDBURST` | 心智爆发 | 突破意志后造成完全无视护甲的心灵伤害 | 保留 |
| `SPELL_SYMBOL_OF_TORMENT` | 折磨之符 | 折磨附近活物与神圣生物，生命减半但不致死 | 保留 |
| `SPELL_SIPHON_ESSENCE` | 吸取精华 | 折磨附近活物敌人并以造成的痛苦治疗使用者 | 保留 |
| `SPELL_AIRSTRIKE` | 空袭 | 扭曲目标周围空气，周边越空旷伤害越高 | 保留 |
| `SPELL_PASSWALL` | 穿墙术 | 长时间施法后穿过相邻岩墙，期间获得护甲 | 保留 |
| `SPELL_HIBERNATION` | 冬眠 | 降低单体代谢使其入睡，醒后暂时免疫睡眠 | 保留 |
| `SPELL_ENGLACIATION` | 深度冻结 | 降低周围生物代谢并按寒抗、体质减速 | 重译为“代谢冻结” |
| `SPELL_SILENCE` | 沉默 | 消除附近声音并阻止多类有声行动 | 保留 |
| `SPELL_SHATTER` | 粉碎 | 以巨大冲击伤害附近生物并可能摧毁墙壁 | 保留 |
| `SPELL_DISCHARGE` | 静电释放 | 电流在相邻生物与施法者间跳跃 | 保留 |
| `SPELL_CORONA` | 怪异发光球 | 以光晕勾勒目标，使其更易被击中 | 重译为“光晕” |
| `SPELL_SANDBLAST` | 沙爆 | 高速岩屑攻击，施法较慢且易受护甲削减 | 保留 |
| `SPELL_SIMULACRUM` | 塑造拟像 | 以相邻生物塑造至多五个冰制拟像 | 保留 |
| `SPELL_PORTAL_PROJECTILE` | 传送投射物 | 把射出或投掷的弹药传送至指定敌人 | 保留 |
| `SPELL_MONSTROUS_MENAGERIE` | 怪物动物园 | 召唤蝎尾狮、林德虫或劫掠斯芬克斯之一 | 保留 |

名称结论：`Metabolic Englaciation` 的辨识核心是降低代谢，改为
“代谢冻结”恢复原名与机制；`Corona` 是目标周围的光晕而非发光球实体，
改为“光晕”。其余 18 项现译均准确且自然。

描述审阅修正九项：Shock 的半护甲无视；Mindburst 的双关与无心智免疫；
Symbol of Torment 的目标类别和负能量抗性；Siphon Essence 的范围、
生命减半与非致死规则；Passwall 的护甲术语；Silence 的神力祈求；
Static Discharge 的返回伤害与护甲；Sculpt Simulacrum 的目标类别及
上限格式；Monstrous Menagerie 的当前候选集合并删除旧强度规则。

证据：对应 `spl-data.h` 的 20 个 `SPELL_*` 记录、
`dat/descript/spells.txt` 与中文同名键，以及 `spl-cast.cc`、
`spl-damage.cc`、`spl-earth.cc`、`spl-summoning.cc`、`mon-cast.cc`
中对应 enum 的施法分支。

### 落地状态

- [x] 20/20 机制证据与名称裁定
- [x] 单一翻译写入者完成 2 项名称与 9 项描述落地
- [x] translation profile
- [x] 批次裁定登记（`D-C-086`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T190704753008000+0800-40579-bd282bcbbce9`。本批裁定后的
`docs/glossary.md` SHA-256 为
`3e50a70435f1e1e74d824e7356910d199785f6fb1f565d551884905463cacba1`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`ea22e8f4f4ab3b1cc76e9abea565aea7b3c85035418a8074a2b9c26ed95ffb03`。

首轮 Run ID `20260725T190402692280000+0800-33775-bd282bcbbce9`
在 changed exact-key terminology 阶段失败：A2 的名称裁定尚未完成，
`Corona` 与 `Metabolic Englaciation` 的 source 映射已分别改为
“光晕”“代谢冻结”，但 glossary 仍记录“怪异发光球”“深度冻结”。
统一 `source.txt`、`glossary.md` 并重新导出 `glossary.utf8` 后，上述
最终运行通过；该失败未涉及 TextDB 结构或描述格式。

## 独立法术批次 A3

边界：inventory 差集顺序第 41–60 项，共 20 项现行独立法术。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_FULMINANT_PRISM` | 爆裂棱镜 | 生成延时爆炸、提前摧毁则减弱的棱镜 | 保留 |
| `SPELL_PARALYSE` | 麻痹 | 短时间阻止目标采取行动 | 保留 |
| `SPELL_WOODWEAL` | 木质愈合 | 借相邻树木的活力治疗大量伤害 | 重译为“林木疗愈” |
| `SPELL_BRAIN_BITE` | 脑噬 | 汲取可见敌人的心智和魔力，低魔力时伤害翻倍 | 保留 |
| `SPELL_STEAM_BALL` | 蒸汽球 | 向目标投射高温蒸汽球 | 保留 |
| `SPELL_CANTRIP` | 小戏法 | 随机施放无明显效果的微小法术鼓舞自己 | 保留 |
| `SPELL_METAL_SPLINTERS` | 金属碎刺 | 发射易被护甲削减的金属碎片 | 保留 |
| `SPELL_SPLINTERSPRAY` | 碎片喷射 | 发射易被护甲削减的木屑 | 保留 |
| `SPELL_PORKALATOR` | 变猪术 | 把目标变成移动迅速但无法施法的猪 | 保留 |
| `SPELL_CREATE_TENTACLES` | 生成触须 | 伸出大型触须攻击附近敌人 | 保留 |
| `SPELL_SLEEP` | 睡眠 | 使目标入睡，受伤或巨响可能唤醒 | 保留 |
| `SPELL_PRIMAL_WAVE` | 原始波浪 | 召出激流击退目标并留下短时浅水 | 重译为“原初浪潮” |
| `SPELL_VANQUISHED_VANGUARD` | 败军先锋 | 召来远古兽人先锋灵魂以长柄武器合围猎物 | 保留 |
| `SPELL_STICKS_TO_SNAKES` | 棍变蛇 | 掷出棍棒并变成随施法者增强的蛇 | 保留 |
| `SPELL_MALMUTATE` | 恶性变异 | 施加几乎总是有害的变异 | 保留 |
| `SPELL_GLOOM` | 阴郁 | 释放吞没光亮、可致盲的阴霾 | 保留 |
| `SPELL_FORCE_LANCE` | 力量之矛 | 震荡力击退目标，撞墙或生物时追加伤害 | 保留 |
| `SPELL_DIMENSION_ANCHOR` | 维度锚定 | 阻止目标移位及部分跨位面效果，但不阻止放逐 | 保留 |
| `SPELL_THORN_VOLLEY` | 荆棘齐射 | 发射一小阵锋利荆棘 | 保留 |
| `SPELL_WALL_OF_BRAMBLES` | 荆棘之墙 | 生长脆弱但难清除、可被弹药穿过的荆棘 | 保留 |

名称结论：`Primal Wave` 以原初力量召出具有击退效果的激流，
“原初浪潮”比“原始波浪”更自然，也更符合六级怪物法术的规模。
`Woodweal` 借相邻树木的叶与树皮活力治疗，“林木疗愈”比误示木材
本身愈合的“木质愈合”更自然。其余 18 项标题都能准确辨识其核心实体、
动作或状态。

描述审阅修正七项：Fulminant Prism 补回材质与延时爆炸；
Primal Wave 把“击倒”纠正为击退；Vanquished Vanguard、
Sticks to Snakes 与 Gloom 按当前英文重译；Malmutate 修复亡灵腐朽；
Dimension Anchor 将“跨层”纠正为跨位面。

证据：对应 `spl-data.h` 的 20 个 `SPELL_*` 记录、
`dat/descript/spells.txt` 与中文同名键，以及 `mon-cast.cc`、
`spl-summoning.cc`、`spl-zap.cc`、`beam.cc` 中相应 enum 分支。

### 落地状态

- [x] 20/20 机制证据与名称裁定
- [x] 单一翻译写入者完成 2 项名称与 7 项描述落地
- [x] translation profile
- [x] 批次裁定登记（`D-C-087`）

初轮 Run ID `20260725T190954711331000+0800-47257-38b7c6fc44e1`
在 Woodweal 自然度复核前已通过。将其进一步改为“林木疗愈”后，与 A4
共同运行的 translation profile 仍通过，0 项失败；Run ID
`20260725T191540235476000+0800-61036-bdfb8a964679`。最终
`docs/glossary.md` SHA-256 为
`7dacdefbc4d60ecc52c335def33e07962b4a54782d5565e96e11c2be0abc35ce`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`6452c99a6a751039be6531bd14c2439c08a1c1cc834ade1e7d9057d53aed4e99`。

## 独立法术批次 A4

边界：inventory 差集顺序第 61–80 项，共 20 项现行独立法术。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_WATERSTRIKE` | 水击 | 搅动目标周围或下方水体造成伤害 | 保留 |
| `SPELL_STRIP_WILLPOWER` | 剥离意志力 | 大幅降低目标意志力 | 保留 |
| `SPELL_FUGUE_OF_THE_FALLEN` | 亡灵赋格 | 击杀非召唤敌人累积灵魂以强化攻势 | 保留 |
| `SPELL_SEARING_RAY` | 灼热射线 | 持续专注时追踪目标的穿透奥术射线 | 保留 |
| `SPELL_DISCORD` | 纷乱 | 使附近生物狂乱并攻击周围一切 | 保留 |
| `SPELL_VIRULENCE` | 毒性 | 使目标更易受毒素影响 | 保留 |
| `SPELL_PLANEREND` | 位面撕裂 | 从六个高危分支之一召来强大威胁 | 保留 |
| `SPELL_CHAIN_OF_CHAOS` | 混沌之链 | 混沌电弧以不可预测效果连击附近生物 | 保留 |
| `SPELL_SIGN_OF_RUIN` | 毁灭印记 | 群体印记在受近战伤害时触发汲取与削弱 | 保留 |
| `SPELL_REBOUNDING_BLAZE` | 弹跳烈焰 | 穿透火焰束可从墙壁反弹并二次命中 | 保留 |
| `SPELL_SPELLSPARK_SERVITOR` | 法术火花仆从 | 构造可施放主人部分破坏法术的金属仆从 | 保留 |
| `SPELL_IRRADIATE` | 辐射 | 以自身表层转化的魔能轰击邻敌并积累污染 | 保留 |
| `SPELL_SPIT_LAVA` | 喷吐岩浆 | 喷吐半数伤害无视火抗的岩浆 | 保留 |
| `SPELL_BATTLECRY` | 战吼 | 提高附近盟友攻击威力 | 保留 |
| `SPELL_WARNING_CRY` | 警告之嚎 | 制造巨响警醒附近敌人 | 保留 |
| `SPELL_FUNERAL_DIRGE` | 葬礼哀歌 | 仪式吟唱暂时加速并强化附近亡灵盟友 | 保留 |
| `SPELL_SEAL_DOORS` | 封印门 | 封住附近门与楼梯阻挡非盟友通行 | 保留 |
| `SPELL_FLAY` | 剥皮 | 制造非致命的幻痛伤口 | 保留 |
| `SPELL_CORRUPTING_PULSE` | 腐化脉冲 | 暂时恶性变异所有可见目标 | 保留 |
| `SPELL_MOURNING_WAIL` | 哀悼嚎哭 | 吐出悲恸形成汲取活物生命的负能量云 | 重译为“哀恸之嚎” |

名称结论：`Mourning Wail` 的旧译“哀悼嚎哭”构词生硬，
“哀恸之嚎”自然保留悲恸情绪与发声意象。其余 19 项准确概括目标、
投射物、状态或核心动作。

描述审阅修正七项：Plane Rend 补回佐特领域并明确召来强大威胁；
Rebounding Blaze 改回穿透且可沿墙反弹的火焰束；Sign of Ruin
补回群体目标、汲取及缓慢、虚弱或失明的附加状态；Spellspark Servitor
恢复当前金属构造体和灌注能力；Spit Lava、Seal Doors 与
Corrupting Pulse 分别修正岩浆抗性、通行阵营和亡灵腐朽规则。

证据：对应 `spl-data.h` 的 20 个 `SPELL_*` 记录、
`dat/descript/spells.txt` 与中文同名键，以及 `mon-cast.cc`、
`spl-damage.cc`、`spl-summoning.cc`、`beam.cc` 中相应 enum 分支。

### 落地状态

- [x] 20/20 机制证据与名称裁定
- [x] 单一翻译写入者完成 1 项名称与 7 项描述落地
- [x] translation profile
- [x] 批次裁定登记（`D-C-088`）

验证结果：覆盖 A3 自然度复核与 A4 当前差异的
`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T191540235476000+0800-61036-bdfb8a964679`。
本批裁定后的 glossary 与 inventory SHA-256 分别为
`7dacdefbc4d60ecc52c335def33e07962b4a54782d5565e96e11c2be0abc35ce`
和 `6452c99a6a751039be6531bd14c2439c08a1c1cc834ade1e7d9057d53aed4e99`。
补充四项描述修正后，与 B1 共同运行的 translation profile 仍通过，
0 项失败；Run ID
`20260725T191721888947000+0800-64295-a7ede56e0456`。

## 独立法术批次 B1

边界：A4 之后的 10 项现行独立法术。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_MARCH_OF_SORROWS` | 悲伤行军 | 生成痛苦之流并在路径及目标周围留下负能量云 | 保留 |
| `SPELL_ENTROPIC_WEAVE` | 熵之编织 | 无需直射地腐蚀目标 | 保留 |
| `SPELL_OBLIVION_HOWL` | 湮灭嚎叫 | 在受害者心中留下会引来噩梦生物的回声 | 保留 |
| `SPELL_PRAYER_OF_BRILLIANCE` | 聪慧祈祷 | 强化附近友方法师的施法威力与频率 | 保留 |
| `SPELL_FLEETFOOT` | 轻快脚步 | 召风短暂提高施法者移动速度 | 保留 |
| `SPELL_GREATER_SERVANT_MAKHLEB` | 地狱仆从 | 召唤一个大恶魔 | 保留 |
| `SPELL_BIND_SOULS` | 绑定灵魂 | 使附近其他活物死后化为拟像 | 重译为“束缚灵魂” |
| `SPELL_INFESTATION` | 虫群侵扰 | 侵染生物并在其死后孵出死亡甲虫 | 保留 |
| `SPELL_STILL_WINDS` | 静止风 | 维持大范围静止空气并阻止云雾形成 | 保留 |
| `SPELL_DREAM_DUST` | 梦尘 | 以催眠梦尘使目标入睡，梦羊会增强效果 | 保留 |

名称结论：`Bind Souls` 改为“束缚灵魂”，避免界面式“绑定”并准确表达
死灵魔法关系；其余九项标题准确概括声音、祈祷、移动、召唤或状态机制。

描述审阅修正 Fleetfoot 与 Bind Souls 两项：前者恢复召风来源与移动速度
增益，后者补回“其他附近活物”及死后化为拟像的附魔条件。

证据：对应 `spl-data.h` 的 10 个 `SPELL_*` 记录、
`dat/descript/spells.txt` 与中文同名键，以及 `mon-cast.cc`、
`spl-summoning.cc`、`spl-necromancy.cc` 中相应 enum 分支。

### 落地状态

- [x] 10/10 机制证据与名称裁定
- [x] 单一翻译写入者完成 1 项名称与 2 项描述落地
- [x] translation profile
- [x] 批次裁定登记（`D-C-089`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T191834040957000+0800-68051-6a67aa2193c9`。
本批裁定后的 glossary 与 inventory SHA-256 分别为
`ee024106cd48cddf7e8a567e4f75e95ed6fed81b5436207ff3b1286ab6f6e878`
和 `adcd05d7de8811a4894c1fc723811f6588ebe724cb8fb85256feed2d05fb623d`。

## 独立法术批次 B2

边界：B1 之后的 30 项现行独立法术。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_UPHEAVAL` | 剧变 | 以岩浆、冰、风或碎石轰击小范围 | 保留 |
| `SPELL_IGNITION` | 点火 | 以火球吞噬周围所有敌人，施法者及盟友免疫 | 保留 |
| `SPELL_FASTROOT` | 快速扎根 | 射出种子，以速生树根缠绕挤压目标 | 重译为“速生根须” |
| `SPELL_GRASPING_ROOTS` | 抓握根须 | 从地下召根抓住并挤压目标 | 保留 |
| `SPELL_SPORULATE` | 产孢 | 释放追敌爆炸并混乱活物的浮游孢子 | 保留 |
| `SPELL_STARBURST` | 星爆 | 向各方向射出穿透火焰束 | 保留 |
| `SPELL_FOXFIRE` | 狐火 | 生成两个自动寻敌的燃烧沼气球 | 保留 |
| `SPELL_MARSHLIGHT` | 沼泽之光 | 生成比狐火更强的两个燃烧沼气球 | 保留 |
| `SPELL_SONIC_WAVE` | 音波 | 内部无描述的声波法术记录 | 保留 |
| `SPELL_ROLL` | 翻滚 | 巨砾甲虫滚成球并获得高速与双倍近战伤害 | 保留 |
| `SPELL_MANIFOLD_ASSAULT` | 多重攻击 | 扭曲空间，以一次近战攻击命中多个可见敌人 | 保留 |
| `SPELL_CONCENTRATE_VENOM` | 浓缩毒液 | 强化目标天然毒液，使咬击与喷吐可减速、窒息 | 保留 |
| `SPELL_ERUPTION` | 喷发 | 在目标下方形成短命局部火山 | 保留 |
| `SPELL_PYROCLASTIC_SURGE` | 火山碎屑涌 | 从岩浆引火焚烧邻近或位于其上的敌人 | 保留 |
| `SPELL_STUNNING_BURST` | 眩晕爆发 | 弱电击造成极短麻痹，电抗可防而意志无效 | 保留 |
| `SPELL_SERACFALL` | 冰塔崩塌 | 将附近拟像崩成爆炸冰块 | 保留 |
| `SPELL_SCORCH` | 烧焦 | 灼烧随机敌人并暂时剥除火抗 | 保留 |
| `SPELL_ENFEEBLE` | 衰弱 | 削弱近战与法术，抵抗失败还会眩晕、失明 | 保留 |
| `SPELL_ANGUISH` | 哀痛 | 使附近敌人造成的伤害反弹给自身 | 保留 |
| `SPELL_DIVINE_ARMAMENT` | 神圣武装 | 将信仰显化为自行战斗的固定灵体武器 | 保留 |
| `SPELL_JINXBITE` | 厄运之咬 | 顽劣之灵追击并伤害、汲取目标 | 保留 |
| `SPELL_SIGIL_OF_BINDING` | 束缚符文 | 两个符文限制移动，结束后给予迅捷 | 保留 |
| `SPELL_DIMENSIONAL_BULLSEYE` | 维度靶心 | 攻击其他敌人时复制投射物传送至标记目标 | 保留 |
| `SPELL_VITRIFY` | 玻璃化 | 使目标如玻璃般脆弱并提高所受全部伤害 | 保留 |
| `SPELL_TREMORSTONE` | 震石 | 内部无描述的震石法术记录 | 保留 |
| `SPELL_MAGNAVOLT` | 磁暴 | 磁化目标并向所有标记者发射必中电束 | 保留 |
| `SPELL_SEISMIC_STOMP` | 地震践踏 | 震裂地面，地面生物可能失衡延后行动 | 保留 |
| `SPELL_FLASHING_BALESTRA` | 闪光弩击 | 灵魂跃出持械攻击并短暂独立决斗 | 重译为“闪跃突刺” |
| `SPELL_SHADOW_BALL` | 暗影球 | 投出小范围爆炸的闪烁暗影球 | 保留 |
| `SPELL_GRAVE_CLAW` | 墓爪 | 消耗死亡余韵，以必中骨片固定目标 | 保留 |

名称结论：Fastroot 改为“速生根须”，避免误示施法者扎根；
Flashing Balestra 改为“闪跃突刺”，恢复 balestra 的击剑前跃接突刺
含义并吻合灵魂跃出持械攻击。其余 28 项准确保留核心机制。

描述审阅修正十项：Grasping Roots、Sporulate、Starburst、
Manifold Assault、Enfeeble、Divine Armament、Magnavolt、
Seismic Stomp、Flashing Balestra 与 Grave Claw 均按当前英文和实现
补全目标、条件、例外或玩法后果。

证据：对应 `spl-data.h` 的 30 个 `SPELL_*` 记录、
`dat/descript/spells.txt` 与中文同名键，以及 `mon-cast.cc`、
`spl-damage.cc`、`spl-summoning.cc`、`spl-forge.cc`、`beam.cc`
中相应 enum 分支。Balestra 词义另以击剑辞书“前跃后接突刺”交叉确认。

### 落地状态

- [x] 30/30 机制证据与名称裁定
- [x] 单一翻译写入者完成 2 项名称与 10 项描述落地
- [x] translation profile
- [x] 批次裁定登记（`D-C-090`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T192149011346000+0800-74419-1362cc07f134`。本批裁定后的
`docs/glossary.md` SHA-256 为
`4e6017f9b1a8de1b194b731840a9690b541edce884e594f49d954aa258c42385`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`56e546f71165560597db443ed7ed5ca5ca8bbb612e5e0696518a80b02958d2de`。

## 独立法术终批 B3

边界：最后 51 个未审阅枚举，包括 16 项现行法术、2 项内部 placeholder、
2 项描述 dummy 与 31 项已移除兼容记录。

| Enum | 生命周期 | 当前译名 | 核心效果 / 证据状态 | 裁定 |
|---|---|---|---|---|
| `SPELL_SPIKE_LAUNCHER` | 现行 | 构建尖刺发射器 | 在相邻墙内构造反复刺击邻敌的陷阱 | 保留 |
| `SPELL_KINETIC_GRAPNEL` | 现行 | 动力抓钩 | 命中嵌入后使下次近战必中并获杀伤加成 | 保留 |
| `SPELL_DIAMOND_SAWBLADES` | 现行 | 钻石锯片 | 固定锻造至多四片锯片，数回合撕裂邻敌 | 保留 |
| `SPELL_SHRED` | 现行 | 撕裂 | 以锯齿躯体旋转重创相邻敌人 | 保留 |
| `SPELL_PLATINUM_PARAGON` | 现行 | 白金典范 | 构造复制神器、联动攻击并可过载的金属勇士 | 保留 |
| `SPELL_MAGMA_BARRAGE` | 现行 | 岩浆弹幕 | 向至多两敌发射穿透熔岩弹，半伤无视火抗 | 保留 |
| `SPELL_VEX` | 现行 | 激怒 | 迫使目标数回合攻击附近格子，可能打空或误伤盟友 | 保留 |
| `SPELL_RAVENOUS_SWARM` | 现行 | 贪婪虫群 | 吸血蝙蝠啃咬非亡灵并最终使其入睡 | 重译为“饥渴蝠群” |
| `SPELL_DOMINATE_UNDEAD` | 现行 | 支配亡灵 | 群体改变附近亡灵阵营，冒险者改为随机攻击 | 保留 |
| `SPELL_DETONATION_CATALYST` | 现行 | 引爆催化剂 | 近战触发友方免疫爆炸，持续攻击可维持 | 保留 |
| `SPELL_SPHINX_SISTERS` | 现行 | 斯芬克斯姐妹 | 召一守卫一劫掠斯芬克斯施妖术与狂风 | 保留 |
| `SPELL_ILL_OMEN` | 现行 | 凶兆 | 无阻碍时扭曲命运并施加大量厄运 | 保留 |
| `SPELL_OSTRACISE` | 现行 | 排斥 | 暂降有效虔诚并封锁相应神圣能力 | 保留 |
| `SPELL_PYRRHIC_RECOLLECTION` | 描述 dummy | 惨胜回忆 | 点燃记忆，暂获强力法术知识并治疗 | 保留 |
| `SPELL_PLANAR_OVERLAY` | 描述 dummy | 位面叠加 | 叠加相邻现实，使本地怪物在楼层出现 | 保留 |
| `SPELL_DOOMSAYING` | 现行 | 宣告厄运 | 施加厄运并在施法者死后触发伏击、封楼梯 | 保留 |
| `SPELL_SLEETSTRIKE` | 现行 | 冰雨打击 | 严寒气旋冰封减速，空旷增伤且半伤无视寒抗 | 保留 |
| `SPELL_LANDBREAKER` | 现行 | 裂地 | 落石攻击多敌并阻塞其后方退路 | 保留 |
| `SPELL_NO_SPELL` | 内部 placeholder | 不存在的法术 | 测试占位，无玩家机制 | 保留 |
| `SPELL_CONDENSATION_SHIELD` | 已移除兼容 | 凝结护盾 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_DARKNESS` | 已移除兼容 | 黑暗术 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_DEMONIC_HORDE` | 已移除兼容 | 恶魔大军 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_EVAPORATE` | 已移除兼容 | 蒸发术 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_FIRE_BRAND` | 已移除兼容 | 火焰烙印 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_FLY` | 已移除兼容 | 飞行术 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_FRENZY` | 已移除兼容 | 狂乱术 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_GRAND_AVATAR` | 已移除兼容 | 大化身 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_HUNTING_CRY` | 已移除兼容 | 狩猎战吼 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_INSULATION` | 已移除兼容 | 绝缘术 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_MELEE` | 内部 placeholder | 近战 | 内部兼容占位，无当前描述 | 保留 |
| `SPELL_MISLEAD` | 已移除兼容 | 误导术 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_PHASE_SHIFT` | 已移除兼容 | 相位变换 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_REARRANGE_PIECES` | 已移除兼容 | 重新布局 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_SEE_INVISIBLE` | 已移除兼容 | 识破隐形 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_SHAFT_SELF` | 已移除兼容 | 自我竖井 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_SINGULARITY` | 已移除兼容 | 奇点术 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_SPECTRAL_WEAPON` | 已移除兼容 | 灵体武器 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_STONESKIN` | 已移除兼容 | 石肤术 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_SUNRAY` | 已移除兼容 | 阳光射线 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_STRIKING` | 已移除兼容 | 打击术 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_RESURRECT` | 已移除兼容 | 复活术 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_HOMUNCULUS` | 已移除兼容 | 人造人 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_SCATTERSHOT` | 已移除兼容 | 散射术 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_TWISTED_RESURRECTION` | 已移除兼容 | 扭曲复活 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_RANDOM_EFFECTS` | 已移除兼容 | 随机效果 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_GOAD_BEASTS` | 已移除兼容 | 激怒野兽 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_TOMB_OF_DOROKLOHE` | 已移除兼容 | 多洛克洛之墓 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_EXCRUCIATING_WOUNDS` | 已移除兼容 | 剧痛之伤 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_CORPSE_ROT` | 已移除兼容 | 尸体腐烂 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_BEASTLY_APPENDAGE` | 已移除兼容 | 野兽肢体 | 无当前实现或描述 | 暂缓术语（恢复时复审） |
| `SPELL_NECROMUTATION` | 已移除兼容 | 亡灵变形 | 无当前实现或描述 | 暂缓术语（恢复时复审） |

名称结论：现行标题仅 Ravenous Swarm 存在确定误示，改为“饥渴蝠群”；
其余现行、dummy 和 placeholder 标题均合理。31 项已移除兼容记录没有
当前实现和描述，不以历史猜测替代证据，逐项裁定为暂缓术语
（恢复时复审）。

描述审阅修正十三项：Kinetic Grapnel、Diamond Sawblades、Shred、
Magma Barrage、Vex、Dominate Undead、Detonation Catalyst、
Sphinx Sisters、Ill Omen、Ostracise、Pyrrhic Recollection、
Sleetstrike 与 Landbreaker 均恢复当前目标、范围、条件与后果。

证据：现行及 dummy 项对应 `spl-data.h` 记录、
`dat/descript/spells.txt` 与中文同名键，以及 `mon-cast.cc`、
`spl-forge.cc`、`spl-summoning.cc`、`spl-zap.cc` 中相应 enum 分支；
兼容项对应 `spl-data.h` 的 `AXED_SPELL` 区和 `spell-type.h` 身份记录。

### 落地状态

- [x] 51/51 生命周期、机制证据与名称裁定
- [x] 单一翻译写入者完成 1 项名称与 13 项描述落地
- [x] translation profile
- [x] 批次裁定登记（`D-C-091`）

验证结果：在将已移除兼容项统一归类为带恢复入口的“暂缓术语”后，
`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T195550854715000+0800-7475-8a5cb19202e1`。最终
`docs/glossary.md` SHA-256 为
`3a2d51e01b9680933a1790a3ceeb7da46d22667b7ac9e98f3c6567b503862cc8`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`e0aec9932c914db4cbe9f4e81043ae70bf74bf013792b1c68b42c68be7816afa`。
inventory enum 集合与本文件审阅 enum 集合均为 511，双向差集为空。
结构终检共有 522 个表格引用、509 个表格唯一 enum；13 个额外引用分别
属于 13 个跨系列成员，且每项恰有一行明确标为“复用”。因此表格中仍只有
509 张规范证据卡，再加上 Dispersal 与 Mesmerise 的两张独立证据卡，
合计恰好 511 张，不存在第二张相互竞争的裁定。

## Awaken 词形系列

边界：英文标题以 `Awaken` 开头的 5 项法术；其中 4 项现行、
1 项 `TAG_MAJOR_VERSION == 34` 已移除兼容。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_AWAKEN_FOREST` | 现行 | 唤醒森林 | 附近树木攻击相邻敌人 | 保留 |
| `SPELL_AWAKEN_VINES` | 现行 | 唤醒藤蔓 | 藤蔓抓住闯入者并拖向树木 | 保留 |
| `SPELL_AWAKEN_FLESH` | 现行 | 唤醒血肉 | 肉堆化为强化大型憎恶并伤害邻敌 | 保留 |
| `SPELL_AWAKEN_ARMOUR` | 现行 | 唤醒护甲 | 从所穿护甲记忆显现战斗回响 | 保留 |
| `SPELL_AWAKEN_EARTH` | 已移除兼容 | 唤醒大地 | 无当前描述或实现 | 暂缓术语（恢复时复审） |

名称结论：四项现行标题准确采用 `Awaken X → 唤醒X`，共同表达让原本
静止的树木、藤蔓、血肉或护甲力量开始行动。标题无需枚举攻击、拖拽、
憎恶生成或护甲重量等后续机制。已移除的 `Awaken Earth` 没有当前机制
证据，暂沿用。

描述审阅未发现语义偏差。证据：`spl-data.h:1829`、
`spl-data.h:2232`、`spl-data.h:2665`、`spl-data.h:3525`、
`spl-data.h:4741`；`dat/descript/spells.txt:87`—`111`；
对应中文描述；`mon-cast.cc` 的森林、藤蔓与血肉施法路径及
Awaken Armour 的锻造实现。

### 落地状态

- [x] 5/5 机制／生命周期证据与名称裁定
- [x] 无翻译资产修改
- [x] translation profile
- [x] 系列裁定登记（`D-C-030`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T165940431722000+0800-67902-a9927e7b16f9`。本批裁定后的
`docs/glossary.md` SHA-256 为
`d6fa21c7c034bdf3f6f40655ec5977826979e4f3c8c7e3279220064b09130ee1`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`1829b52622d79de772a3de6ac84fb9da0be2431cc3c774b35613e0e73629dbb0`。

## Gaze 词形系列

边界：英文标题以独立 `Gaze` 结尾的 7 项现行法术，无已移除兼容成员。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_PARALYSIS_GAZE` | 麻痹凝视 | 不可抵抗的短时麻痹；需要充能 | 保留 |
| `SPELL_CONFUSION_GAZE` | 困惑凝视 | 通过意志检定的困惑 | 保留 |
| `SPELL_ANTIMAGIC_GAZE` | 反魔法凝视 | 汲取魔力并按汲取量治疗施法者 | 保留 |
| `SPELL_DRAINING_GAZE` | 吸取凝视 | 负能量按最大生命比例施加衰竭 | 重译为“衰竭凝视” |
| `SPELL_WEAKENING_GAZE` | 虚弱凝视 | 不可抵抗地削弱近战攻击 | 保留 |
| `SPELL_VITRIFYING_GAZE` | 玻璃化凝视 | 不可抵抗地提高所受全部伤害 | 保留 |
| `SPELL_MUTAGENIC_GAZE` | 变异凝视 | 积累变异能量，导致有害变异或爆炸 | 保留 |

名称结论：稳定采用 `Gaze → 凝视`。唯一重译项 `Draining Gaze`
不把生命转移给施法者，而是施加 Drain/衰竭；“吸取凝视”会与真正汲取
魔力并治疗施法者的 `Antimagic Gaze` 混淆，因此改为“衰竭凝视”。

描述审阅同步修正 7 项：明确 gaze 只需视线而无需直达射线，恢复
Draining 的活物、负能量及最大生命比例机制，恢复 Mutagenic 的能量
积累与爆炸后果，并修正麻痹、玻璃化和虚弱等表述。

证据：`spl-data.h:2904`—`2959`、`spl-data.h:3802`、
`spl-data.h:4553`、`mon-cast.cc:472`—`529`、
`mon-cast.cc:1468`—`1496`、`mon-cast.cc:7776`—`7795`。

### 落地状态

- [x] 7/7 机制证据与名称裁定
- [x] 单一翻译写入者名称及描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-023`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T163930499789000+0800-27732-4448e8a3e80a`。本批裁定后的
`docs/glossary.md` SHA-256 为
`dc35d644bd70de1bc9da131717d485fb1153f622a5bbde1336062416d5dba3be`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`1829b52622d79de772a3de6ac84fb9da0be2431cc3c774b35613e0e73629dbb0`。

## Touch 词形系列

边界：英文标题含独立 `Touch` 词形的 2 项现行法术，无已移除兼容成员。

| Enum | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|
| `SPELL_AGONISING_TOUCH` | 剧痛之触 | 相邻目标生命减半，但不直接致死 | 保留 |
| `SPELL_CONFUSING_TOUCH` | 困惑之触 | 惯用手附魔；无伤害触碰可能使目标困惑 | 保留 |

名称结论：两项均自然采用 `Touch → 之触`，准确表达近距离触碰机制与
结果。描述审阅只发现 `Confusing Touch` 漏译 dominant hand，本批补为
“惯用手”；其余机制与英文一致。

证据：`spl-data.h:937`、`spl-data.h:1051`、
`dat/descript/spells.txt:131`、`dat/descript/spells.txt:382`、
`spl-cast.cc:2701` 及 Confusing Touch 近战触发实现。

### 落地状态

- [x] 2/2 机制证据与名称裁定
- [x] 单一翻译写入者描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-024`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T164128898119000+0800-31160-c33b6eda4ced`。本批裁定后的
`docs/glossary.md` SHA-256 为
`dd7c8fee1a58e245c8764d1dcdff62f35d464926788c038207979917d21dbb71`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`1829b52622d79de772a3de6ac84fb9da0be2431cc3c774b35613e0e73629dbb0`。

## Beam 词形系列

边界：英文标题以独立 `Beam` 结尾的 2 项现行法术，无已移除兼容成员。
`Shadow Beam` 已在 Shadow/Shadows 批次审阅，本批复用其机制未变化的
证据且不重复计数；新增审阅身份仅为 `Plasma Beam`。

| Enum | 等级 / 学派 / flags | 使用者 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|---|
| `SPELL_PLASMA_BEAM` | 6 / 火、气 / `noisy, destructive` | 玩家、怪物 | 等离子光束 | 自动选择最远敌人之一；穿透电击束无视一半护甲，再追加同路径火焰束 | 保留 |
| `SPELL_SHADOW_BEAM` | 5 / 咒法 / `dir_or_target, monster, needs_tracer, silent` | 怪物 | 暗影光束 | 穿透性暗影束 | 保留（复用 D-C-020） |

系列结论：两项都以穿透性 beam 为核心，`Beam → 光束` 自然且准确。
`Plasma Beam` 的火、气学派和双段实现支持“等离子光束”；不应为了强调
双元素改成原名不存在的“雷火光束”。`Shadow Beam` 已有完整独立证据。

标题无需修改。描述审阅修正一项 Needs Fix：旧文“穿透防御者的一半防具”
既混用装备类别，也没有清楚表达 armour bypass；现改为“无视目标一半的
护甲”，并明确火焰束沿同一路径随后射出。

证据：`spl-data.h:140`、`spl-data.h:4093`、
`dat/descript/spells.txt:1555`、`dat/descript/spells.txt:1785`、
`spl-cast.cc:1393`、`spl-cast.cc:2531`、`zap-data.h:1883`、
`zap-data.h:1898`、`spl-util.cc:2367`。

### 落地状态

- [x] 2/2 名称裁定（1 项新增证据，1 项复用未变化证据）
- [x] 单一翻译写入者描述修正
- [x] translation profile
- [x] 系列裁定登记（`D-C-022`）

验证结果：覆盖 Beam 当前差异的 `verify_zh.sh --profile translation`
通过，0 项失败；Run ID
`20260725T163645858802000+0800-23887-6f9d722cf77d`。本批裁定后的
`docs/glossary.md` SHA-256 为
`d359c94d477bd28ff04a58662f1a2635a83294a49bded08e18cb997ef78d35c9`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`660ff3a19309d42de3109f6af54dab6c29613bd73064e7edb6c33f8dfe2ed759`。

## Throw 词形系列

边界：英文标题中含独立 `Throw` 词形，共 8 项；其中 7 项现行、
1 项 `TAG_MAJOR_VERSION == 34` 已移除兼容。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_THROW_FLAME` | 现行 | 投掷火焰 | 小团火焰 | 保留 |
| `SPELL_THROW_FROST` | 现行 | 投掷冰霜 | 小团冰霜 | 保留 |
| `SPELL_THROW_ICICLE` | 现行 | 投掷冰柱 | 冰片；一半伤害无视寒冷抗性 | 保留 |
| `SPELL_THROW_BARBS` | 现行 | 投掷倒刺 | 倒刺使目标移动时受伤 | 保留 |
| `SPELL_THROW_ALLY` | 现行 | 投掷盟友 | 将附近盟友扔到敌人附近 | 保留 |
| `SPELL_THROW_BOLAS` | 现行 | 投掷流星索 | 无视敌人体型并束缚在原地 | 保留 |
| `SPELL_THROW_PIE` | 现行 | 投掷小丑派 | 施加不可抵抗的随机临时削弱 | 保留 |
| `SPELL_THROW` | 已移除兼容 | 投掷 | 无当前描述或实现 | 暂缓术语（恢复时复审） |

名称结论：7 项现行标题全部保留，稳定采用 `Throw → 投掷`。实现中的
fire/hurl 描述具体发射动作，不构成标题重译依据；“小丑派”也能表达
Killer Klown 专属物件，不误示为投掷小丑本体。

描述审阅修正 5 项 Needs Fix：`Throw Ally` 的施法者和落点关系、
`Throw Barbs` 的移动伤害、`Throw Bolas` 对最大体型仍能束缚、
`Throw Icicle` 一半伤害无视寒冷抗性，以及 `Throw Klown Pie`
遗漏失明并残留旧版月亮派文本的问题。

证据：`spl-data.h:276`—`287`、`spl-data.h:1007`、
`spl-data.h:2782`、`spl-data.h:3004`、`spl-data.h:3325`—`3337`、
`spl-data.h:4704`、`mon-cast.cc:2318`—`2356`、
`mon-cast.cc:2513`、`mon-cast.cc:2719`、`beam.cc:4447`、
`beam.cc:4519`、`beam.cc:5285`—`5292`。

### 落地状态

- [x] 8/8 机制证据与名称裁定
- [x] 单一翻译写入者完整系列描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-021`）

验证结果：`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T163550762468000+0800-21896-882a67b66967`。本批裁定后的
`docs/glossary.md` SHA-256 为
`d359c94d477bd28ff04a58662f1a2635a83294a49bded08e18cb997ef78d35c9`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`660ff3a19309d42de3109f6af54dab6c29613bd73064e7edb6c33f8dfe2ed759`。

## Shadow/Shadows 词形系列

边界：英文标题中含独立 `Shadow` 或 `Shadows` 词形，共 13 项；其中
12 项现行、1 项 `TAG_MAJOR_VERSION == 34` 已移除兼容。连写的
`Shadowball` 不在本系列。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_SHADOW_CREATURES` | 现行 | 暗影生物 | 复制当前地域原生生物 | 保留 |
| `SPELL_SHADOW_SHARD` | 现行 | 暗影碎片 | 单体硬化暗影碎片 | 保留 |
| `SPELL_SHADOW_BEAM` | 现行 | 暗影光束 | 穿透暗影束 | 保留 |
| `SPELL_CREEPING_SHADOW` | 现行 | 蔓延暗影 | 从墙角袭击相邻敌人 | 保留 |
| `SPELL_SHADOW_TEMPEST` | 现行 | 暗影风暴 | 暗影闪电攻击至多半数可见敌人 | 保留 |
| `SPELL_SHADOW_PRISM` | 现行 | 暗影棱镜 | 延时爆炸；提前摧毁则减弱 | 保留 |
| `SPELL_SHADOW_PUPPET` | 现行 | 暗影傀儡 | 活影仆从骚扰并缠绕敌人 | 保留 |
| `SPELL_SHADOW_TURRET` | 现行 | 暗影炮塔 | 固定炮塔反复开火 | 保留 |
| `SPELL_SHADOW_SHOT` | 现行 | 暗影射击 | 单体小型硬化暗影弹 | 保留 |
| `SPELL_SHADOW_BIND` | 现行 | 暗影束缚 | 随机将多名附近敌人钉在影子上 | 保留 |
| `SPELL_SHADOW_TORPOR` | 现行 | 暗影麻木 | 直线群体减速 | 保留 |
| `SPELL_SHADOW_DRAINING` | 现行 | 暗影吸取 | 附近群体无视护甲伤害 | 保留 |
| `SPELL_WEAVE_SHADOWS` | 已移除兼容 | 编织暗影 | 无当前描述或实现 | 暂缓术语（恢复时复审） |

名称结论：12 项现行标题全部准确保留 `Shadow/Shadows → 暗影` 词根；
已移除的 `Weave Shadows` 不用现行机制反推。描述审阅发现 10 项中文
仍对应旧机制或遗漏关键规则，本批已按当前英文与实现修正：
`Shadow Creatures`、`Creeping Shadow`、`Shadow Bind`、
`Shadow Draining`、`Shadow Prism`、`Shadow Puppet`、
`Shadow Shot`、`Shadow Tempest`、`Shadow Torpor`、
`Shadow Turret`。`Shadow Shard` 与 `Shadow Beam` 原描述一致。

证据：`spl-data.h:1040`、`spl-data.h:4081`—`4208`、
`spl-data.h:4707`、`mon-cast.cc:775`—`859`、
`mon-cast.cc:3646`、`mon-cast.cc:5651`—`5663`、
`god-passive.cc:1713`—`1800`、`zap-data.h:2191`—`2312`、
`spl-summoning.cc:2233`、`spl-summoning.cc:2517`—`2518`。

### 落地状态

- [x] 13/13 机制证据与名称裁定
- [x] 单一翻译写入者完整系列描述落地
- [x] translation profile
- [x] 系列裁定登记（`D-C-020`）

验证结果：覆盖 Dart 与 Shadow 当前差异的
`verify_zh.sh --profile translation` 通过，0 项失败；Run ID
`20260725T163136983447000+0800-13931-971a54b02563`。本批裁定后的
`docs/glossary.md` SHA-256 为
`5b97f68339de1634fbfd1f8fdaa783d23297a5ac0979bf1cce393eaed4fec04d`；
511 项 inventory 完整性断言全部通过，JSON SHA-256 为
`660ff3a19309d42de3109f6af54dab6c29613bd73064e7edb6c33f8dfe2ed759`。

## Stage B 最终冻结清单复核

本节记录当前工作树的最终绑定，不改写上文各历史批次当时的 SHA。当前
`docs/glossary.md` SHA-256 为
`4070a396e65a4bdf1fd2dfbc9e95bcc40053391e65441053f73c08146ed31d9e`；
以 `migrate_spell_titles.py inventory --require-zh-titles` 重新生成的
JSON SHA-256 为
`39e5f81f49162f31506b9960ffe3756b7141d753a0ca753c29a28dc7aa929e67`。

冻结清单的机械断言为：预期 enum 511 项、实际解析 511 项、唯一 enum
511 项，`enum_identity_complete_and_unique=true`。另将清单中的 enum
集合与本文全部 `SPELL_*` 身份去重集合双向比较：两侧均为 511 项，
inventory 减本文为 0 项，本文减 inventory 也为 0 项。因此这里证明的是
既有复审文档与当前生产清单的身份双向覆盖，不另造简单逐卡协议。

本轮因术语与译文变化直接复核两项现行召唤法术：

- `SPELL_SUMMON_DEMON`：5 级召唤法术，flags 为 `unholy`、
  `mons_abjure`、`monster`，英文与中文描述均存在；当前标题“召唤恶魔”
  与对象一致，终态仍为保留。
- `SPELL_SUMMON_GREATER_DEMON`：7 级召唤法术，flags 为 `unholy`、
  `mons_abjure`、`monster`，英文与中文描述均存在；当前标题已为
  “召唤高等恶魔”，准确复用 `greater demon → 高等恶魔`，历史重译裁定
  已落地，终态仍记为重译。

## 2026-11-01 全法术正文、名称与专用动态说明续审
本节是本文件的续审记录；前文历史基线和命名裁定保留。冻结输入请求基线 c759f8ff383a7f803e4a2c6430e0f3300154a541，生产快照交付 d20758170b1c34ba2ebdfa140b20a8c79cac2cc9；本批实施基线 31d6c0d7a41fde6e39d3600788d040b3ac65e14c。核心法术定义与正文在冻结期间与请求基线字节相同；共享显示接口按冻结时文件摘要绑定。
覆盖：524 个法术定义（含兼容、内部与描述占位身份）、411 个 EN/ZH 正文键、44 个法术专用动态说明身份，共 979 张唯一卡。清单与卡片集合双向相等，重复、遗漏与多余均为零。此边界不覆盖全库通用消息，也不声称所有无正文的法术获得了新正文。
冻结清单内容 SHA-256：`2cafa38b7fa3860659f959e5587c422f86aa4098490f475651732ac3df7fe91f`；完整清单文件 SHA-256：`cfc6a1aa732914d35cd26db97e2f1aff1b14f8b1427e62968ad941438d85e3e0`；原始审查文件 SHA-256：`5ea15b1b564a38360f08acdf75dc428a9919a47f3250616d7d240bfbbbad1d1e`。原冻结结论为 keep 825、adjust 51、defer terminology 103；51 项 Needs Fix 与 19 项 Suggestion 分开记录。
当前术语 SHA-256：`e47b7b2aee9e32cd5448b15eb45dea34cfdea82b31d9161e8bf30fff8dd24b8a`。glossary 是一致性约束，不是词义正确性的证明。未变条目沿用本轮完整阅读与机制审查的证据；本批改动则使用当前正文、完整显示模板和独立语言复核闭环。四地狱专名依赖按 D-C-103 重审，既有合理近义命名未被自动判错。
51 项确认问题全部实施：45 个正文身份、6 个动态身份；采用 14 项建议，保留另外 5 项建议。下表的 adjust 是已实施的本轮裁定，不将关闭后记录改成从未有问题的 keep。兼容延期保留原值、责任人与重新进入条件。正文保留源键并定位到生产文件；中文列为本次审定内容，名称与正文是独立身份。

### 完整正文
| 身份 | 英文源名／源键 | 当前中文／采用内容 | 终态 | 理由、发现与处理 | 证据 |
|---|---|---|---|---|---|
| textdb:abjuration spell | abjuration spell | <br>缩短附近所有敌对召唤生物的剩余存续时间。 | keep | 附近所有敌对召唤物剩余时间缩短；友敌、召唤类别、时限齐全。 | crawl-ref/source/dat/descript/spells.txt:2；crawl-ref/source/dat/descript/zh/spells.txt:2 |
| textdb:acid ball spell | acid ball spell | <br>投掷一颗会爆炸的腐蚀酸液球。 | keep | 投掷、爆炸、腐蚀酸液球三义齐全；非无酸性普通弹丸。 | crawl-ref/source/dat/descript/spells.txt:6；crawl-ref/source/dat/descript/zh/spells.txt:6 |
| textdb:agonising touch spell | agonising touch spell | <br>让一个邻近生物的生命值减半。但永远不会直接杀死目标。 | keep | 相邻目标生命减半、绝不直接致死齐全；名称剧痛之触表触碰与强烈痛苦。 | crawl-ref/source/dat/descript/spells.txt:10；crawl-ref/source/dat/descript/zh/spells.txt:10 |
| textdb:agony spell | agony spell | <br>让一个目标生物的生命值减半。但永远不会直接杀死目标。 | keep | 目标生命减半、绝不直接致死齐全；与相邻touch区别仍由正文保留。 | crawl-ref/source/dat/descript/spells.txt:15；crawl-ref/source/dat/descript/zh/spells.txt:14 |
| textdb:airstrike spell | airstrike spell | <br>使目标生物周围的空气扭曲成一团狂暴的气旋。<br>如果目标周围空旷，它会造成更大的伤害。 | keep | 目标周围狂暴空气旋涡、越空旷越高伤齐全；空袭无新增军械含义。 | crawl-ref/source/dat/descript/spells.txt:20；crawl-ref/source/dat/descript/zh/spells.txt:18 |
| textdb:alistair's intoxication spell | alistair's intoxication spell | <br>将你周围怪物的大脑中的一小部分物质转化成酒精，<br>以此混乱视野中的所有智慧生物（但有毒抗的生物可能会抵抗这个效果）。<br>如果施法者成功与其他心灵接触，便会短暂眩晕。<br>在巫师们的宴会上，这道法术经常被用来打破冷场。 | keep | 脑物质转酒精、视野智慧目标、毒抗可能抵抗、成功心灵接触才自身短眩晕、宴会破冰幽默齐全。 | crawl-ref/source/dat/descript/spells.txt:25；crawl-ref/source/dat/descript/zh/spells.txt:23 |
| textdb:alistair's walking alembic spell | alistair's walking alembic spell | <br>构建一个可移动且具战斗能力的炼金制造厂。它利用近战摩擦来酿造各种<br>有用的药水，在出拳时排放有毒副产品的云雾。当积累足够热量完成合成时，<br>它将在解体前自动向附近盟友分发成品药水。 | keep | 移动战斗炼金厂、近战摩擦酿药、拳目标排毒副产云、热量够则附近友军得成药并解体齐全。 | crawl-ref/source/dat/descript/spells.txt:33；crawl-ref/source/dat/descript/zh/spells.txt:1551 |
| textdb:anguish spell | anguish spell | <br>用超自然的痛苦折磨附近的敌人，<br>使他们在效果持续期间发出的所有伤害会反弹到他们身上。<br>意志力强的敌人可以抵抗痛苦的死灵幻觉，而没有意识的生物则不受到影响。 | keep | 附近敌人所致全伤害反弹、持续期间、意志抵抗、无心智免疫齐全。 | crawl-ref/source/dat/descript/spells.txt:41；crawl-ref/source/dat/descript/zh/spells.txt:30 |
| textdb:animate dead spell | animate dead spell | <br>施法后的一段时间内，被施法者杀死的活物会化作丧尸复起。<br>使怪物化作丧尸的概率和效果持续时间随法术威力提高。<br>重新施放此法术会使丧尸归于尘土，离开当前楼层也同样如此。 | keep | 施法后一段时间内自己杀活物变丧尸、概率与持续随威力、重施/离层清丧尸齐全。 | crawl-ref/source/dat/descript/spells.txt:47；crawl-ref/source/dat/descript/zh/spells.txt:44 |
| textdb:antimagic gaze spell | antimagic gaze spell | <br>使目标的魔力泄入空气，如同被反魔法武器击中，无需直达射线即可生效。 | keep | 目标汲魔如反魔武器、无需直射路径齐全。 | crawl-ref/source/dat/descript/spells.txt:54；crawl-ref/source/dat/descript/zh/spells.txt:50 |
| textdb:apportation spell | apportation spell | <br>将地面上指定位置的所有物品拉向施法者。<br><br>法术威力较低时，物品可能无法一直被拉到施法者所在的位置。<br><br>特别强大的魔法物品，例如佐特宝珠，可能会主动抵抗该法术的拉力。 | keep | 地面指定位置全部物品拉向己、低威力未必拉到、极强神器如宝珠可抵抗齐全。 | crawl-ref/source/dat/descript/spells.txt:59；crawl-ref/source/dat/descript/zh/spells.txt:54 |
| textdb:arcjolt spell | arcjolt spell | <br>向与施法者相邻或近邻的一切传导电流。电流会沿相互连接的目标继续跳跃，<br>但施法者不受影响。造成的伤害无视目标一半的护甲。 | adjust | 相邻/近邻链式电流、自身豁免齐全；忽略半护甲被误写成半伤害无视护甲。 本批已修复并复核：半护甲被误成半伤害。 | crawl-ref/source/dat/descript/spells.txt:68；crawl-ref/source/dat/descript/zh/spells.txt:62；crawl-ref/source/spl-damage.cc:2950 |
| textdb:avatar song spell | avatar song spell | <br>唱出一首极具魔力、萦绕心头的歌。未能抵抗的冒险者会无法远离歌者<br>（有时还会不由自主地被拉近），其他生物则会直接陷入眩晕。<br><br>此外，它可能从附近的任何深水中召来溺魂。<br><br>离开施法者视野会结束控制移动的效果。 | keep | 未抵抗冒险者不能远离且可能被拉近、其他生物眩晕、深水可能溺魂、离视线解控制齐全。 | crawl-ref/source/dat/descript/spells.txt:75；crawl-ref/source/dat/descript/zh/spells.txt:71 |
| textdb:awaken armour spell | awaken armour spell | <br>汲取你所穿护甲的记忆，显现出一个与你并肩作战的回响。<br>回响移动缓慢，但攻击威力会随用于构成它的护甲重量大幅提高，<br>并拥有护甲本身的全部防御属性。<br><br>法术威力会提高其耐久度。 | keep | 穿戴护甲记忆回响、慢移、重量大增伤、全防御属性继承、威力增耐久齐全。 | crawl-ref/source/dat/descript/spells.txt:86；crawl-ref/source/dat/descript/zh/spells.txt:36 |
| textdb:awaken flesh spell | awaken flesh spell | <br>引导一股混沌能量穿过施法者视野中的每个肉堆，将其激活为强化的大型憎恶，<br>并对不幸站在它们旁边的任何敌人造成混沌伤害。 | keep | 视野每肉堆、混沌能量、强化大型憎恶、邻近敌人混沌伤齐全。 | crawl-ref/source/dat/descript/spells.txt:95；crawl-ref/source/dat/descript/zh/spells.txt:1557 |
| textdb:awaken forest spell | awaken forest spell | <br>为附近的树赋予运动能力，它们得以甩动树枝，移动根茎。<br>这些被施加魔法的树将会猛击邻近的敌人。 | keep | 树有限运动/枝根活动/邻敌猛击齐全；有限未译直语但枝根活动未变成自由行走。 | crawl-ref/source/dat/descript/spells.txt:101；crawl-ref/source/dat/descript/zh/spells.txt:80 |
| textdb:awaken vines spell | awaken vines spell | <br>让藤蔓破土而出。藤蔓会伸向前抓住闯入者，把他们拖向任一附近的树。 | keep | 藤蔓长出、抓闯入者、拖向附近树齐全。 | crawl-ref/source/dat/descript/spells.txt:107；crawl-ref/source/dat/descript/zh/spells.txt:85 |
| textdb:banishment spell | banishment spell | <br>将一个生物放逐到深渊。 | keep | 生物放逐深渊齐全。 | crawl-ref/source/dat/descript/spells.txt:112；crawl-ref/source/dat/descript/zh/spells.txt:89 |
| textdb:battlecry spell | battlecry spell | <br>激励施法者附近的友方更积极地投入战斗，增加他们的打击力量。 | keep | 近旁友方更积极且增强攻击齐全。 | crawl-ref/source/dat/descript/spells.txt:116；crawl-ref/source/dat/descript/zh/spells.txt:93 |
| textdb:beckoning gale spell | beckoning gale spell | <br>扭曲一个生物周围的空气，造成伤害并试图将其拉向施法者。 | keep | 目标空气扭曲伤害并试图拉近施法者齐全。 | crawl-ref/source/dat/descript/spells.txt:121；crawl-ref/source/dat/descript/zh/spells.txt:1562 |
| textdb:berserk other spell | berserk other spell | <br>使附近的一个盟友陷入狂暴状态。狂暴会暂时提升生命值、速度和近战伤害。 | keep | 近旁友军狂暴、暂HP/速度/近战伤害提高齐全。 | crawl-ref/source/dat/descript/spells.txt:130；crawl-ref/source/dat/descript/zh/spells.txt:101 |
| textdb:berserker rage spell | berserker rage spell | <br>&lt;Berserk ability&gt; | keep | Berserk能力引用原样，已在能力组全读所引正文及副作用；当前法术名狂暴之怒可成立。 | crawl-ref/source/dat/descript/spells.txt:126；crawl-ref/source/dat/descript/zh/spells.txt:97 |
| textdb:bestow arms spell | bestow arms spell | <br>暂时授予众多附近盟友来自军械库的魔法武器，只要维系它们的灵魂保持完整。 | keep | 暂授多名附近盟友军械库魔武器、依赖维系灵魂完整齐全。 | crawl-ref/source/dat/descript/spells.txt:135；crawl-ref/source/dat/descript/zh/spells.txt:1566 |
| textdb:bind souls spell | bind souls spell | <br>为附近其他活物施加魔法，使其被杀死后化为拟像。 | keep | 其他附近活物、死亡后拟像齐全。 | crawl-ref/source/dat/descript/spells.txt:140；crawl-ref/source/dat/descript/zh/spells.txt:105 |
| textdb:blink allies away spell | blink allies away spell | <br>将施法者视野内的友方从附近敌人那里闪送走。 | keep | 施法者视野盟友远离附近敌人齐全；描述闪送是转移行为近义，不必强制换名词。 | crawl-ref/source/dat/descript/spells.txt:145；crawl-ref/source/dat/descript/zh/spells.txt:113 |
| textdb:blink allies encircling spell | blink allies encircling spell | <br>将施法者视野内的友军转移到目标敌人周围。 | keep | 视野内若干盟友、合围选定敌人齐全。 | crawl-ref/source/dat/descript/spells.txt:149；crawl-ref/source/dat/descript/zh/spells.txt:117 |
| textdb:blink away spell | blink away spell | <br>将施法者转移到远离目标敌人的位置。 | keep | 施法者去离指定敌更远处齐全。 | crawl-ref/source/dat/descript/spells.txt:154；crawl-ref/source/dat/descript/zh/spells.txt:121 |
| textdb:blink close spell | blink close spell | <br>将施法者向目标敌人转移一小段距离。 | keep | 施法者向敌短距靠近齐全。 | crawl-ref/source/dat/descript/spells.txt:158；crawl-ref/source/dat/descript/zh/spells.txt:125 |
| textdb:blink other close spell | blink other close spell | <br>将目标敌人向施法者处转移一小段距离。意志力无法抗拒它。 | keep | 敌方向施法者短距移位、意志不能抗拒齐全。 | crawl-ref/source/dat/descript/spells.txt:162；crawl-ref/source/dat/descript/zh/spells.txt:129 |
| textdb:blink other spell | blink other spell | <br>随机地将目标敌人转移一小段距离。意志力无法抗拒它。 | keep | 敌方随机短距移位、意志不能抗拒齐全。 | crawl-ref/source/dat/descript/spells.txt:167；crawl-ref/source/dat/descript/zh/spells.txt:133 |
| textdb:blink range spell | blink range spell | <br>将施法者移到远离目标敌人的位置，但仍然在其视线范围内。 | keep | 施法者远离目标但仍在目标视线内齐全。 | crawl-ref/source/dat/descript/spells.txt:172；crawl-ref/source/dat/descript/zh/spells.txt:137 |
| textdb:blink spell | blink spell | <br>随机地将施法者转移一小段距离。<br>以这种方式移位后，短时间内无法再次施展该法术，其间隔时间取决于法术威力。 | keep | 随机短距、威力决定短时禁重施齐全。 | crawl-ref/source/dat/descript/spells.txt:177；crawl-ref/source/dat/descript/zh/spells.txt:141 |
| textdb:blinkbolt spell | blinkbolt spell | <br>将施法者变为一道可穿透目标的闪电箭，并将其转移到箭的目的地。 | keep | 化穿透闪电并移位至终点齐全。 | crawl-ref/source/dat/descript/spells.txt:183；crawl-ref/source/dat/descript/zh/spells.txt:146 |
| textdb:bolster spell | bolster spell | <br>强化施法者的体魄，大幅增加其近战伤害及对所有元素的抗性。 | keep | 自身物理强化、近战伤及全元素抗性大增齐全。 | crawl-ref/source/dat/descript/spells.txt:193；crawl-ref/source/dat/descript/zh/spells.txt:2097 |
| textdb:bolt of antimagic spell | bolt of antimagic spell | <br>发射一道可穿透目标的反魔箭，其力量在存在本身的层面上自相矛盾，<br>能汲取受害者储存的魔力。 | keep | 穿透反魔箭、存在论悖论意象、汲储备魔力齐全。 | crawl-ref/source/dat/descript/spells.txt:188；crawl-ref/source/dat/descript/zh/spells.txt:2092 |
| textdb:bolt of cold spell | bolt of cold spell | <br>射出一道穿透性的寒冰箭。 | keep | 穿透寒冰箭齐全。 | crawl-ref/source/dat/descript/spells.txt:198；crawl-ref/source/dat/descript/zh/spells.txt:150 |
| textdb:bolt of devastation spell | bolt of devastation spell | <br>射出一道可穿透目标的悲伤与心痛之箭，使受害者的意志力减半。 | keep | 穿透悲伤心痛箭、意志减半齐全。 | crawl-ref/source/dat/descript/spells.txt:202；crawl-ref/source/dat/descript/zh/spells.txt:154 |
| textdb:bolt of draining spell | bolt of draining spell | <br>射出一道穿透性的负能量箭，对击中的任何活物造成负能量伤害并使其衰竭。 | keep | 穿透负能量箭、任何命中活物衰竭齐全；附负能量伤害与实现一致。 | crawl-ref/source/dat/descript/spells.txt:207；crawl-ref/source/dat/descript/zh/spells.txt:158 |
| textdb:bolt of fire spell | bolt of fire spell | <br>射出一道穿透性的烈火箭。 | keep | 穿透烈火箭齐全。 | crawl-ref/source/dat/descript/spells.txt:212；crawl-ref/source/dat/descript/zh/spells.txt:162 |
| textdb:bolt of flesh spell | bolt of flesh spell | <br>发射可穿透目标的魔法血肉弹幕，在路径尽头的地面上短暂留下一堆血肉。 | keep | 穿透魔法血肉弹幕、路径尽头短暂肉堆齐全。 | crawl-ref/source/dat/descript/spells.txt:216；crawl-ref/source/dat/descript/zh/spells.txt:1570 |
| textdb:bolt of light spell | bolt of light spell | <br>发射一道可穿透目标的灼热光线，可能致盲击中的任何活物、恶魔或神圣生物。 | keep | 穿透灼热光、可能致盲活物恶魔神圣三类齐全。 | crawl-ref/source/dat/descript/spells.txt:221；crawl-ref/source/dat/descript/zh/spells.txt:1574 |
| textdb:bolt of magma spell | bolt of magma spell | <br>射出一道穿透性的岩浆箭。它造成的一半伤害，火抗无法抵御。 | keep | 穿透熔岩、半伤无视火抗齐全；此处英文确实修饰伤害而不是护甲。 | crawl-ref/source/dat/descript/spells.txt:226；crawl-ref/source/dat/descript/zh/spells.txt:166 |
| textdb:bombard spell | bombard spell | <br>向一个目标轰击铁球。轰击的力量也常常会使施法者踉跄地向后退。 | keep | 铁球轰目标、常使施法者后退齐全。 | crawl-ref/source/dat/descript/spells.txt:231；crawl-ref/source/dat/descript/zh/spells.txt:170 |
| textdb:borgnjor's revivification spell | borgnjor's revivification spell | <br>这道法术瞬间治愈施法者身上所有的创伤，<br>但同时会永久损失部分最大生命值；法术威力越高，损失越少。<br><br>这道法术极为强大，足以将施法者从“死亡之门”里拉出来，<br>但这么做施法者会被暂时麻痹。它对亡灵无效。 | adjust | 即时全治、永久最大HP代价随威力反比、取消死亡门且短麻痹、亡灵无效齐全。 建议处理：adopt；“反比”可改“威力越高，永久HP损失越少”，避免读成严格数学反比例；实际6+binomial函数不是1/power。 | crawl-ref/source/dat/descript/spells.txt:236；crawl-ref/source/dat/descript/zh/spells.txt:174 |
| textdb:borgnjor's vile clutch spell | borgnjor's vile clutch spell | <br>唤起地牢地层下被长久掩埋的尸体的手。<br>范围内被抓住的敌人会被定在原地，并持续受到缠绕挤压，直到挣脱。 | adjust | 地底尸手、敌原地束缚齐全，但漏持续缠绕挤压机制。 本批已修复并复核：漏缠绕挤压机制。 | crawl-ref/source/dat/descript/spells.txt:244；crawl-ref/source/dat/descript/zh/spells.txt:182；crawl-ref/source/spl-monench.cc:232；crawl-ref/source/beam.cc:6690 |
| textdb:brain bite spell | brain bite spell | <br>令视野中的一个敌人流失少量心智和一定比例的魔力，无需直射。<br>如果敌人的魔力储备几近耗尽，则会受到双倍伤害。 | keep | 可见敌人少量心智与比例魔力、无需直射、近空魔双伤齐全。 | crawl-ref/source/dat/descript/spells.txt:250；crawl-ref/source/dat/descript/zh/spells.txt:187 |
| textdb:brom's barrelling boulder spell | brom's barrelling boulder spell | <br>在给定的基本方向上释出一个硕大的滚动巨砾。<br>巨砾会伤害撞到的生物，从死者身上碾过，并将幸存者及其身后的其他生物<br>一并无助地向后推去。<br><br>巨砾庞大且横冲直撞，难以在狭窄区域使用；沿窄道发射时，它会迅速与墙壁<br>摩擦而解体。它离开施法者视线、撞上墙壁或其他无法推动的生物时也会碎裂。 | keep | 基本方向滚巨石、伤命中者、滚过死者/推幸存者及后排、窄道摩毁、离视线/墙/不动生物碎裂齐全。 | crawl-ref/source/dat/descript/spells.txt:256；crawl-ref/source/dat/descript/zh/spells.txt:192 |
| textdb:brothers in arms spell | brothers in arms spell | <br>召唤一个庞大而愤怒的盟友，在狂暴中大肆破坏。 | adjust | 与引用能力的EN/ZH文字一致，但当前monster-only法术的召唤物按施法者种类从固定表选，summon_berserker不读XL；玩家能力才按XL选型。应分开法术正文，避免把正确玩家缩放强加怪物。 本批已修复并复核：怪物法术继承了仅属玩家能力的XL缩放。 | crawl-ref/source/dat/descript/spells.txt:268；crawl-ref/source/dat/descript/zh/spells.txt:201；crawl-ref/source/mon-cast.cc:8240；crawl-ref/source/spl-summoning.cc:690 |
| textdb:cage of brambles spell | cage of brambles spell | <br>使带刺的荆棘墙迅速生长，将附近所有敌人分别围在环中。<br>施法者的盟友可以不受阻碍地向荆棘另一侧发射投射物，<br>但其他人若想清除这些荆棘，恐怕会吃些苦头。 | keep | 附近每敌荆棘环围、施法者盟友可穿射、他人拆除痛苦齐全。 | crawl-ref/source/dat/descript/spells.txt:272；crawl-ref/source/dat/descript/zh/spells.txt:2101 |
| textdb:call canine familiar spell | call canine familiar spell | <br>召唤一个犬神来协助施法者。<br>这些神秘的犬科动物与它们的召唤者形成了一种纽带，<br>施法者的法术威力越强，它们就越强。<br><br>当你的魔宠在附近时，重施这个法术会给它注入额外的魔力，<br>愈合它的部分伤口、清除中毒，并使它的下一次攻击提前发动并横扫相邻敌人。 | keep | 召犬神、缔结纽带、施法威力正比强化；附近重施治疗/解毒/下一击更快横扫齐全。 | crawl-ref/source/dat/descript/spells.txt:278；crawl-ref/source/dat/descript/zh/spells.txt:205 |
| textdb:call down damnation spell | call down damnation spell | <br>以天谴轰击指定敌人，无需直射。这股不洁力量会伤害目标及与其相邻的<br>所有生物，且不受护甲、抗性等任何防护手段影响。不过，某些生物<br>（通常是自身也能降下天谴的生物）完全不会受到天谴伤害。 | keep | 指定敌无直射天谴、邻伤、无视防护、特定通常能天谴者免疫齐全。 | crawl-ref/source/dat/descript/spells.txt:288；crawl-ref/source/dat/descript/zh/spells.txt:214 |
| textdb:call down lightning spell | call down lightning spell | <br>用闪电轰击敌人，无需直射。<br>目标性魔法需要有距离才能发挥作用，因此相邻或几乎相邻的敌人无法被击中。 | keep | 指定敌无需直射闪电、相邻及近邻无法命中齐全。 | crawl-ref/source/dat/descript/spells.txt:296；crawl-ref/source/dat/descript/zh/spells.txt:220 |
| textdb:call imp spell | call imp spell | <br>从地狱深处呼唤出一个低阶恶魔。它配备着一支长矛，可以戳刺施法者的敌人。<br>小恶魔的武器质量随法术威力的增强而提升。 | keep | 地狱低阶魔、长矛刺敌、威力增武器质量齐全。 | crawl-ref/source/dat/descript/spells.txt:302；crawl-ref/source/dat/descript/zh/spells.txt:225 |
| textdb:call lost souls spell | call lost souls spell | <br>召唤一些由死灵魔法形成的幽魂。这些迷失之魂可以进入更强大的亡灵体内，<br>将其从消亡边缘救回；也可以把垂死的活物变成对应的幽灵形态。 | adjust | 死灵幽魂、救强大亡灵濒死、垂死活物变幽灵齐全；lost souls遗魂与标题迷失灵魂是同一可辨实体。 建议处理：adopt；可将“这些遗魂”对齐当前实体标签“迷失之魂”；同义描述不作为阻断。 | crawl-ref/source/dat/descript/spells.txt:308；crawl-ref/source/dat/descript/zh/spells.txt:230 |
| textdb:call of chaos spell | call of chaos spell | <br>召来混沌之力增强附近盟友，赋予其加速、强效、活力加倍或更高抗性。<br>这个混沌的魔法偶尔会适得其反，<br>导致友方失去意志力或变得狂暴、被变形或被内焰所充斥。 | keep | 附近友军加速/强效/双活力/抗性四益、偶发反效果意志丧失/狂暴/变形/内焰四项齐全。 | crawl-ref/source/dat/descript/spells.txt:314；crawl-ref/source/dat/descript/zh/spells.txt:235 |
| textdb:call tide spell | call tide spell | <br>施法者能影响大范围内所有水域的潮汐状态。呼唤潮汐后不久，整层水域都会<br>进入高潮；施法者附近的水位还会涨得比通常更高。 | keep | 大范围水潮、稍后全层高潮、施法者旁更高水位齐全。 | crawl-ref/source/dat/descript/spells.txt:321；crawl-ref/source/dat/descript/zh/spells.txt:241 |
| textdb:cantrip spell | cantrip spell | <br>施放一个初级魔法，意在提升施法者的士气。它没有明显的效果。 | keep | 数种小法术之一、试图鼓舞、无可察效果；中文初级单次不表示可挑选法术。 | crawl-ref/source/dat/descript/spells.txt:328；crawl-ref/source/dat/descript/zh/spells.txt:246 |
| textdb:cause fear spell | cause fear spell | <br>这道法术让施法者附近的生物陷入恐惧之中，使它们无法接近施法者，<br>对施法者的近战攻击有可能失败。离开施法者的视野范围将结束效果。 | keep | 附近恐惧、不能接近/近战偶尔失败、离视线结束齐全。 | crawl-ref/source/dat/descript/spells.txt:333；crawl-ref/source/dat/descript/zh/spells.txt:250 |
| textdb:caustic breath spell | caustic breath spell | <br>&lt;Caustic Breath ability&gt; | keep | Caustic Breath能力引用完整，按能力卡全正文复审结果挂接。 | crawl-ref/source/dat/descript/spells.txt:339；crawl-ref/source/dat/descript/zh/spells.txt:1578 |
| textdb:chain lightning spell | chain lightning spell | <br>释放一股巨大的电流，先击中离施法者最近的生物，再从那里向外连锁。<br>它走得越远，造成的伤害就越小。次生电弧的范围有限，对施法者的伤害很小。<br>该法术无视目标一半的护甲，且造成的一半伤害不受电击抗性影响。 | adjust | 最近生物起链、渐远渐弱、次级短距/自伤小齐全；半护甲及半电抗被写成半伤害无视二者。 本批已修复并复核：半护甲结算误译。 | crawl-ref/source/dat/descript/spells.txt:348；crawl-ref/source/dat/descript/zh/spells.txt:260；crawl-ref/source/beam.cc:4608；crawl-ref/source/spl-damage.cc:198；crawl-ref/source/fight.cc:800 |
| textdb:chain of chaos spell | chain of chaos spell | <br>创造一个纯混沌能量的弧，以不可预知的效果攻击周围的生物。<br>能量弧会触及施法者但不会伤害他。 | keep | 纯混沌弧、近旁不可测效果、可触施法者但无害齐全。 | crawl-ref/source/dat/descript/spells.txt:343；crawl-ref/source/dat/descript/zh/spells.txt:255 |
| textdb:chaos breath spell | chaos breath spell | <br>呼出一大片充满纯粹混沌精能的云。 | adjust | 大范围混沌本质烟云；中文混乱混淆Chaos与Confusion。 本批已修复并复核：Chaos被混成Confusion。 | crawl-ref/source/dat/descript/spells.txt:360；crawl-ref/source/dat/descript/zh/spells.txt:271；crawl-ref/source/spl-zap.cc:148；docs/glossary.md:chaos |
| textdb:charm spell | charm spell | <br>使一个敌对生物为施法者战斗一段时间。<br>执意追寻宝珠的冒险者不会被魅惑，而只会短暂陷入混乱。 | keep | 敌暂为己战、追宝冒险者改短混乱齐全。 | crawl-ref/source/dat/descript/spells.txt:355；crawl-ref/source/dat/descript/zh/spells.txt:266 |
| textdb:cigotuvi's putrefaction spell | cigotuvi's putrefaction spell | <br>以魔法加速受损活体组织的腐败，使大量瘴气在数回合内从目标的伤口中涌出。<br>任何站在其中的活物都可能被减速并身中剧毒。<br>气流会阻止瘴气在施法者站立处形成，但除此之外，施法者并不免疫其效果。<br><br>此法术只能以至少已身受重伤的活物为目标。<br>引导这种死灵能量会使施法者自身的最大生命值暂时衰竭，<br>但法术威力越高，这项副作用就越轻。 | adjust | 伤口持续数回合瘴气、活物可能慢/重毒、站己处不生云但非其他豁免、仅重伤活物、威力降低自身暂衰竭齐全；中文生命汲取未明确最大HP。 建议处理：adopt；建议明确自身“最大生命值暂时衰竭”，当前措辞对应原文health drained，但玩家更易区分直接HP损失。 | crawl-ref/source/dat/descript/spells.txt:364；crawl-ref/source/dat/descript/zh/spells.txt:909 |
| textdb:cleansing flame spell | cleansing flame spell | <br>激起以使用者为中心的巨大的神怒爆炸，会对亡灵和恶魔造成严重伤害，<br>并对所有其他敌对生物造成伤害。 | keep | 自身中心神怒、亡灵恶魔重伤及其他敌伤齐全。 | crawl-ref/source/dat/descript/spells.txt:377；crawl-ref/source/dat/descript/zh/spells.txt:279 |
| textdb:cold breath spell | cold breath spell | <br>呼出一股凝聚的冰寒之气。 | keep | 集中冰冷空气吐息齐全。 | crawl-ref/source/dat/descript/spells.txt:382；crawl-ref/source/dat/descript/zh/spells.txt:275 |
| textdb:combustion breath spell | combustion breath spell | <br>&lt;Combustion Breath ability&gt; | keep | Combustion Breath引用原样，能力组已全文核爆余烬/逐生物爆/自身免伤。 | crawl-ref/source/dat/descript/spells.txt:391；crawl-ref/source/dat/descript/zh/spells.txt:1582 |
| textdb:concentrate venom spell | concentrate venom spell | <br>强化目标怪物自身的毒液。带毒的叮咬和喷吐的毒液变得更强，会造成减慢和窒息。 | adjust | 目标自然毒液强化、毒咬喷吐造成慢/窒息齐全；唾液可建议写喷吐毒液更清晰。 建议处理：adopt；毒性spit可写“喷吐毒液”，比唾液更明确。 | crawl-ref/source/dat/descript/spells.txt:386；crawl-ref/source/dat/descript/zh/spells.txt:284 |
| textdb:confuse spell | confuse spell | <br>使生物的头脑陷入迷惑和混乱。 | keep | 心智困惑混乱齐全。 | crawl-ref/source/dat/descript/spells.txt:395；crawl-ref/source/dat/descript/zh/spells.txt:288 |
| textdb:confusing touch spell | confusing touch spell | <br>这道法术能向施法者的惯用手注入魔法能量。当施法者触碰一个怪物时，<br>这些能量会被释放出来，可能会让目标怪物陷入混乱。<br>施法者以这种触碰怪物的方式进行的攻击不会造成伤害。 | keep | 惯用手施魔、触碰释放可能混乱、尝试触碰攻击无伤齐全。 | crawl-ref/source/dat/descript/spells.txt:399；crawl-ref/source/dat/descript/zh/spells.txt:292 |
| textdb:confusion gaze spell | confusion gaze spell | <br>使一个生物的心智陷入迷茫与混乱，只需视线，无需直达射线。 | keep | 心智混乱且无需直射齐全。 | crawl-ref/source/dat/descript/spells.txt:406；crawl-ref/source/dat/descript/zh/spells.txt:298 |
| textdb:conjure ball lightning spell | conjure ball lightning spell | <br>创造数个球状闪电，找到最近的敌人后造成巨大的闪电爆炸。<br>造成的伤害无视目标一半的护甲。<br>施法者需要谨慎，因为闪电并不能判断它击中的是什么。<br><br>让球状闪电保持凝聚的魔力的范围有限，如果在爆炸前离施法者太远，<br>它们可能会无害地消散。 | adjust | 数个电球、敌前爆炸/可能误伤、离施法者远可无害消散齐全；最近敌 qualifier漏且半护甲误为半伤。 本批已修复并复核：半护甲误译并漏最近目标。 | crawl-ref/source/dat/descript/spells.txt:411；crawl-ref/source/dat/descript/zh/spells.txt:302；crawl-ref/source/spl-summoning.cc:924；crawl-ref/source/beam.cc:4608 |
| textdb:conjure living spells spell | conjure living spells spell | <br>创造几个活体自主法术；它们会在第一个敌人进入射程时自行施放，<br>随后消散。 | keep | 数个自主活法术、第一敌入程自施后消散齐全。 | crawl-ref/source/dat/descript/spells.txt:422；crawl-ref/source/dat/descript/zh/spells.txt:311 |
| textdb:construct spike launcher spell | construct spike launcher spell | <br>在相邻的墙壁内构建一个简单的机械陷阱，反复刺穿随机的相邻敌人。<br>受墙壁本身保护，它对大多数形式的伤害免疫，但如果施法者离开其附近<br>将会解体。 | keep | 相邻墙内陷阱、反复随机刺邻敌、多数伤免疫、离附近解体齐全。 | crawl-ref/source/dat/descript/spells.txt:427；crawl-ref/source/dat/descript/zh/spells.txt:1586 |
| textdb:corona spell | corona spell | <br>这道法术创造出光晕以环绕生物，有效地勾勒出其轮廓。<br>这道光抵消了地牢幽暗、阴郁的氛围，因此要击中目标生物就容易多了。 | adjust | 光晕勾轮廓提高命中齐全；驱散霉味字面化了原文氛围修辞。 建议处理：adopt；“驱散霉味”把musty atmosphere字面化，可润为“抵消地牢幽暗、阴郁的氛围”。 | crawl-ref/source/dat/descript/spells.txt:434；crawl-ref/source/dat/descript/zh/spells.txt:316 |
| textdb:corrosive bolt spell | corrosive bolt spell | <br>射出一道由强腐蚀性酸液构成的穿透箭。 | keep | 穿透强腐蚀酸箭齐全。 | crawl-ref/source/dat/descript/spells.txt:440；crawl-ref/source/dat/descript/zh/spells.txt:321 |
| textdb:corrupt spell | corrupt spell | <br>在附近释放深渊的能量。这会改变受影响区域的外观，并暂时召唤出深渊中的生物。<br>它不能在深渊中释放。 | keep | 附近深渊能量、改外观/暂召怪、深渊不可齐全。 | crawl-ref/source/dat/descript/spells.txt:444；crawl-ref/source/dat/descript/zh/spells.txt:325 |
| textdb:corrupting pulse spell | corrupting pulse spell | <br>向所有可见目标注入腐化，暂时对他们的身体造成有害的变异。<br>它不会影响人造物；亡灵若受到影响则会腐朽。 | keep | 全部可见目标暂有害变异、人造免疫/亡灵腐朽齐全。 | crawl-ref/source/dat/descript/spells.txt:450；crawl-ref/source/dat/descript/zh/spells.txt:330 |
| textdb:creeping frost spell | creeping frost spell | <br>激起墙壁中刺骨的寒意。任何站在墙边的施法者的敌人都会被冻结，<br>并会发现他们的移动速度变慢了。寒抗能削减其伤害，但无法抵御冰冻效果。 | keep | 墙体寒霜、墙邻敌冻结减移动、寒抗减伤但不免冻结齐全。 | crawl-ref/source/dat/descript/spells.txt:456；crawl-ref/source/dat/descript/zh/spells.txt:335 |
| textdb:creeping shadow spell | creeping shadow spell | <br>从附近墙角召来暗影，袭击所有紧邻这些墙壁的施法者敌人。 | adjust | 附近墙角出影、邻墙敌受袭；中文把目标缩为仅邻墙角而实际任意可见墙邻敌。 本批已修复并复核：邻墙目标范围缩成只邻墙角。 | crawl-ref/source/dat/descript/spells.txt:462；crawl-ref/source/dat/descript/zh/spells.txt:1592；crawl-ref/source/mon-cast.cc:3805 |
| textdb:crystallising shot spell | crystallising shot spell | <br>掷出一块巨大而沉重的水晶碎片。它可能令生物的身体结构变得如破碎的<br>粗制水晶般脆弱，使其受到的所有伤害增加。 | keep | 大重晶片、可能全来源受伤提高齐全。 | crawl-ref/source/dat/descript/spells.txt:467；crawl-ref/source/dat/descript/zh/spells.txt:1596 |
| textdb:curse of agony spell | curse of agony spell | <br>诅咒一个敌人；施法者接下来两次以近战击中该敌人时，<br>每次都会使其剩余生命值减半。 | keep | 下一两次施法者近战命中各令目标剩HP减半齐全。 | crawl-ref/source/dat/descript/spells.txt:473；crawl-ref/source/dat/descript/zh/spells.txt:340 |
| textdb:death channel spell | death channel spell | <br>束缚被杀死的活物、恶魔和神圣生物的灵魂，迫使其幽魂留下，<br>并在引导持续期间为施法者而战。 | keep | 杀死活物/恶魔/神圣灵魂幽魂为己战、引导持续期间齐全。 | crawl-ref/source/dat/descript/spells.txt:478；crawl-ref/source/dat/descript/zh/spells.txt:351 |
| textdb:death rattle spell | death rattle spell | <br>呼出死亡的实质，制造出有毒的瘴气。 | keep | 临终精华成有毒瘴气齐全；死亡实质属可接受风格略泛。 | crawl-ref/source/dat/descript/spells.txt:483；crawl-ref/source/dat/descript/zh/spells.txt:356 |
| textdb:death's door spell | death's door spell | <br>使施法者在短时间内几乎不受伤害，但也会让施法者危险地接近死亡。<br>事实上，如此接近，以至于身体认为自己已经死了——治疗效果将无济于事。<br><br>施法者将在法术结束前不久收到一个警告。结束后，无法立即重新施展该法术，<br>但在效果结束时，法术威力高的施法者将会更远离死亡。<br>它对已经成为亡灵的生物无效。 | keep | 短时近无敌/濒死/治疗无效、到期前一次警告、禁立即再施、高威力结束后离死更远、亡灵无效齐全。 | crawl-ref/source/dat/descript/spells.txt:487；crawl-ref/source/dat/descript/zh/spells.txt:360 |
| textdb:debugging ray spell | debugging ray spell | <br>射出一道能造成巨大伤害（1500 hp）的射线，而且百发百中。 | keep | 1500hp伤害/必命中齐全，调试射线准确保持内部工具语气。 | crawl-ref/source/dat/descript/spells.txt:498；crawl-ref/source/dat/descript/zh/spells.txt:369 |
| textdb:deflect missiles spell | deflect missiles spell | <br>以排斥力场包裹施法者，大幅提高其对所有种类投射物的闪避能力——<br>即使施法者因其他原因无法行动时也依然有效。 | keep | 排斥场对所有投射物增加闪避、不能行动仍有效齐全。 | crawl-ref/source/dat/descript/spells.txt:502；crawl-ref/source/dat/descript/zh/spells.txt:373 |
| textdb:detonation catalyst spell | detonation catalyst spell | <br>在施法者的拳头或近战武器上附着不稳定催化剂，<br>使每次攻击都在主要目标处引发火焰爆炸；施法者及其盟友不受爆炸伤害。<br>持续攻击可无限延长催化剂活性，采取其他行动则会使其迅速衰减。<br>武器基础伤害和法术威力都会提高爆炸伤害。 | keep | 拳或近战附催化剂、每主目标火爆、自己友军免、持续攻击可无限续/其他动作快衰、武器基础伤害和威力增爆伤齐全。 | crawl-ref/source/dat/descript/spells.txt:507；crawl-ref/source/dat/descript/zh/spells.txt:1601 |
| textdb:diamond sawblades spell | diamond sawblades spell | <br>在施法者周围固定位置锻造至多四片锋利锯片，<br>在数回合内撕碎与其相邻的敌人。 | keep | 最多四片、固定围绕位置、数回合攻击各自邻敌齐全。 | crawl-ref/source/dat/descript/spells.txt:517；crawl-ref/source/dat/descript/zh/spells.txt:1608 |
| textdb:dig spell | dig spell | <br>从未经加工的岩石中挖出一条通道。 | adjust | 挖天然未加工岩隧道；unworked误成未成形，含义从未加工转为未有形。 本批已修复并复核：天然岩石被误作未成形岩石。 | crawl-ref/source/dat/descript/spells.txt:522；crawl-ref/source/dat/descript/zh/spells.txt:378；crawl-ref/source/beam.cc:digging |
| textdb:dimension anchor spell | dimension anchor spell | <br>阻止受影响目标尝试进行的任何移位，无论是否是主动的。<br>这甚至包括一些跨位面效果，但不包括放逐。 | keep | 阻主动被动移位、包括部分跨位面但放逐例外齐全。 | crawl-ref/source/dat/descript/spells.txt:526；crawl-ref/source/dat/descript/zh/spells.txt:382 |
| textdb:dimensional bullseye spell | dimensional bullseye spell | <br>在施法者的武器和选定的目标之间建立连接。<br>每当施法者向*不同的*敌人投射东西时，对应的弹药就会传送到目标。<br>法术威力越强，命中率就越高。 | keep | 武器与选目标连结、射/投不同敌人才复制投射物传到目标、威力加命中齐全。 | crawl-ref/source/dat/descript/spells.txt:532；crawl-ref/source/dat/descript/zh/spells.txt:387 |
| textdb:diminish spells spell | diminish spells spell | <br>不可抵抗地暂时削弱一个敌人的法术威力。 | keep | 不可抗拒暂降敌法术威力齐全。 | crawl-ref/source/dat/descript/spells.txt:538；crawl-ref/source/dat/descript/zh/spells.txt:1613 |
| textdb:discord spell | discord spell | <br>驱使附近的生物陷入疯狂，使它们以极大的力量和速度无情地攻击周围的一切。 | keep | 附近生物疯狂、强力量速度、无情攻击附近一切齐全。 | crawl-ref/source/dat/descript/spells.txt:542；crawl-ref/source/dat/descript/zh/spells.txt:393 |
| textdb:disjunction spell | disjunction spell | <br>让施法者周围一个球形区域内的空间结构变得不稳定，<br>使周围生物从施法者那里被闪送走。闪送的概率取决于到施法者的距离，<br>当直接近身时，几乎一定会被闪送。 | keep | 暂不稳空间、周围者远闪、距离决定概率/紧邻近必齐全。 | crawl-ref/source/dat/descript/spells.txt:547；crawl-ref/source/dat/descript/zh/spells.txt:397 |
| textdb:dispel undead range spell | dispel undead range spell | <br>通过扰乱维系亡灵形体的力量，对一个亡灵造成极大伤害。 | keep | 干扰形体魔力伤亡灵甚重齐全；范围区别由标题远程及另一相邻版本保留。 | crawl-ref/source/dat/descript/spells.txt:558；crawl-ref/source/dat/descript/zh/spells.txt:407 |
| textdb:dispel undead spell | dispel undead spell | <br>通过扰乱维系亡灵形体的力量，对相邻的亡灵造成极大伤害。 | keep | 相邻亡灵/维系形体力量被干扰而重伤齐全。 | crawl-ref/source/dat/descript/spells.txt:553；crawl-ref/source/dat/descript/zh/spells.txt:403 |
| textdb:dispersal spell | dispersal spell | <br>将施法者附近的所有生物传送到远处。<br>即使生物的意志足以抵抗，也仍会被不可抗拒地闪送一小段距离。<br>此外，任何受该法术影响的怪物都有一次独立的意志检定；<br>检定失败时，它会因空间扭曲而陷入混乱。 | keep | 短距全生物远传、意志抵抗仍短闪、每受影响怪另意志判混乱齐全。 | crawl-ref/source/dat/descript/spells.txt:563；crawl-ref/source/dat/descript/zh/spells.txt:411 |
| textdb:divine armament spell | divine armament spell | <br>将施法者的信仰显化为一件灵体武器，由其自行与敌人战斗并将其斩杀。<br>这件武器直接反映施法者独有的虔诚，因此每次从神祇处获得的武器都相同。 | keep | 信仰精神武器自行战斗杀敌、独特虔诚决定每次同武器齐全。 | crawl-ref/source/dat/descript/spells.txt:570；crawl-ref/source/dat/descript/zh/spells.txt:1617 |
| textdb:dominate undead spell | dominate undead spell | <br>试图强行改变附近所有尚未效忠施法者的亡灵之阵营。<br>意志坚定的冒险者无法被完全控制，只会在效果期间随机攻击附近敌友；<br>施法者死亡会使此法术提前解除。 | keep | 附近未效忠亡灵改阵营、固执冒险者不完全受控/随机打敌友、法术期结束恢复/施法者死可提前解；中文省略恢复理智为时限可推。 | crawl-ref/source/dat/descript/spells.txt:578；crawl-ref/source/dat/descript/zh/spells.txt:1622 |
| textdb:doom bolt spell | doom bolt spell | <br>发射一道可穿透目标的诅咒恶意之箭，使目标遭受厄运。 | keep | 穿透诅咒恶意、造成厄运状态齐全。 | crawl-ref/source/dat/descript/spells.txt:600；crawl-ref/source/dat/descript/zh/spells.txt:1628 |
| textdb:doomsaying spell | doomsaying spell | <br>预言可怕的未来，施加等于当前达到 100% 尚需量一半的厄运。<br>施法者死亡时，这一命运会有一小部分化为伏击实现：本层数个藏得很好的敌人会<br>准确无误地找到你的位置，所有楼梯也会暂时封闭。<br><br>此法术只能施放一次；即使在信使睡梦中杀死它，也无法逃过命运的安排。 | keep | 至100%差额一半厄运、施法者死触本层隐敌寻位及全楼梯暂封、仅一次/睡中杀亦不避齐全。 | crawl-ref/source/dat/descript/spells.txt:589；crawl-ref/source/dat/descript/zh/spells.txt:1632 |
| textdb:dragon veins spell | dragon veins spell | <br>让施法者汲取遍布地牢的元素能量地脉，将其破坏力引向敌人。<br>施放时，会在相邻的地面格上显露至多四条龙脉，分别对应火焰、寒冰、<br>空气和大地魔法。踏上任意一条龙脉，便会消耗1点魔力，立即触发一次<br>破坏性施法，攻击至多3个随机敌人，并获得所汲取元素的额外效果：<br><br>火（西）：优先攻击生命值最少的敌人。击杀目标时，会留下短暂的火焰云雾。<br><br>冰（东）：优先攻击生命值最多的敌人。短暂冰封目标，使其移动减慢。<br><br>气（北）：优先攻击最远的敌人。与其他三种元素不同，对远处目标也能造成完整伤害。<br><br>土（南）：优先攻击最近的敌人。攻击的目标数少一个，对飞行生物的伤害<br>大幅降低，但近距离被击中的敌人可能会站立不稳。<br><br>在法术结束前，你至多可以汲取其中两条龙脉的力量。 | keep | 最多四邻地龙脉、西火东冰北气南土、1MP最多3随机敌；火最少HP/杀留火云、冰最多HP/短减速、气最远/远仍全伤、土最近/少1目标/飞行减伤/近可能踉跄、最多踏2脉齐全。 | crawl-ref/source/dat/descript/spells.txt:618；crawl-ref/source/dat/descript/zh/spells.txt:2107 |
| textdb:dragon's call spell | dragon's call spell | <br>向龙域发出强力呼唤，接连召来巨龙与施法者的敌人交战。<br>维持该法术代价高昂，每条响应呼唤的新龙都会进一步消耗施法者的魔力。<br>呼唤结束后，短时间内无法再次发出呼唤。呼唤的持续时间及应召龙的种类<br>取决于法术威力。 | keep | 呼龙接连出战、每新龙耗更多MP、结束短禁重施、威力决定持续/龙种齐全。 | crawl-ref/source/dat/descript/spells.txt:610；crawl-ref/source/dat/descript/zh/spells.txt:424 |
| textdb:drain life spell | drain life spell | <br>汲取附近所有敌人的生命力，并按造成的伤害成比例地治疗使用者。 | keep | 附近所有敌汲命、自疗与伤正比齐全。 | crawl-ref/source/dat/descript/spells.txt:642；crawl-ref/source/dat/descript/zh/spells.txt:431 |
| textdb:drain magic spell | drain magic spell | <br>使目标的魔力泄到空中，就像他们被反魔法武器击中一样。 | defer terminology | 魔力泄空如反魔武器齐全。 延期理由：Retained text read in full for parity, but associated spell is AXED; dummy level 7 and another current spell do not prove historical behavior.；责任：future restoration implementer and sole zh-translator；重入：Restore this exact spell identity, or change its retained EN/ZH source.；保留原值见中文列。 | crawl-ref/source/dat/descript/spells.txt:647；crawl-ref/source/dat/descript/zh/spells.txt:435 |
| textdb:draining gaze spell | draining gaze spell | <br>以负能量充斥一个活物，使其按最大生命值的一定比例陷入衰竭。<br>该法术需要视线，但无需直达射线。 | keep | 活物负能量、按最大HP比例衰竭、需视线不需直射齐全。 | crawl-ref/source/dat/descript/spells.txt:652；crawl-ref/source/dat/descript/zh/spells.txt:1640 |
| textdb:dream dust spell | dream dust spell | <br>用催眠的梦尘淹没目标，以迷人的视觉景象使其入睡。另有梦羊时，会增加效果的强度和持续时间。 | adjust | 梦尘催眠、额外梦羊加强和延时齐全；遗漏迷人的视觉展示这一施法表现命题。 本批已修复并复核：漏视觉展示命题。 | crawl-ref/source/dat/descript/spells.txt:657；crawl-ref/source/dat/descript/zh/spells.txt:439；crawl-ref/source/mon-cast.cc:7006 |
| textdb:druid's call spell | druid's call spell | <br>召回同层其他地方的林地生物。 | keep | 同层其他林地生物召回齐全。 | crawl-ref/source/dat/descript/spells.txt:663；crawl-ref/source/dat/descript/zh/spells.txt:443 |
| textdb:electrical bolt spell | electrical bolt spell | <br>向目标射出一道命中率很高、可穿透目标的闪电箭。 | keep | 高命中穿透电箭齐全。 | crawl-ref/source/dat/descript/spells.txt:667；crawl-ref/source/dat/descript/zh/spells.txt:447 |
| textdb:enfeeble spell | enfeeble spell | <br>用邪恶能量压倒敌人，不可抗拒地削弱其近战攻击并降低法术威力。<br>它还会使无法抵抗全部诅咒力量的敌人眩晕和失明，<br>即使目标没有视觉感官也不例外。 | keep | 不可抗拒弱近战及法术、未抗完整诅咒才额外眩晕盲、无视觉仍受影响齐全。 | crawl-ref/source/dat/descript/spells.txt:671；crawl-ref/source/dat/descript/zh/spells.txt:451 |
| textdb:ensnare spell | ensnare spell | <br>向生物射出一连串的网，使目标困于黏性的网中。 | keep | 蛛网丝射流困目标黏网齐全；一连串网可建议改蛛丝避免多个捕网印象。 | crawl-ref/source/dat/descript/spells.txt:678；crawl-ref/source/dat/descript/zh/spells.txt:457 |
| textdb:ensorcelled hibernation spell | ensorcelled hibernation spell | <br>降低目标的代谢率，诱导冬眠。目标苏醒后，将在一段时间内无法再次入睡。 | keep | 代谢下降冬眠、醒后短时不能再睡齐全。 | crawl-ref/source/dat/descript/spells.txt:682；crawl-ref/source/dat/descript/zh/spells.txt:461 |
| textdb:entropic weave spell | entropic weave spell | <br>腐蚀目标，无需直达目标的射线路径。 | adjust | 腐蚀且不需直射路径；中文无需直射法术误把路径条件改为法术类型。 本批已修复并复核：射线路径条件误成法术种类。 | crawl-ref/source/dat/descript/spells.txt:687；crawl-ref/source/dat/descript/zh/spells.txt:465；crawl-ref/source/mon-cast.cc:8750 |
| textdb:eringya's noxious bog spell | eringya's noxious bog spell | <br>施法者释放出一股污泥，将附近区域变成有毒的沼泽。<br>污泥会对所有怪物造成伤害、引起中毒，即使是那些抗毒的怪物。<br>沼泽不能在有多个坚固地形相邻的区域形成，也不能在缺少坚实地面的区域形成，<br>例如深水或熔岩。变化只是暂时的，且无法在施法者的视线外持续。<br>法术威力越强，沼泽的持续时间就越长。 | keep | 近区毒沼、全怪含毒抗受伤中毒、邻多坚固地形/无实地如深水熔岩不能生、暂时/离视线不可维持、威力延时齐全。 | crawl-ref/source/dat/descript/spells.txt:691；crawl-ref/source/dat/descript/zh/spells.txt:469 |
| textdb:eringya's surprising crocodile spell | eringya's surprising crocodile spell | <br>召唤一条利齿森森的鳄鱼袭击相邻敌人。鳄鱼会随一股浑浊水流从施法者脚下现身，<br>对选定目标发动强化攻击，并将目标和施法者一同向后拖拽，<br>随后让施法者在它身后安全下马。鳄鱼仍在场时无法再次施放此法术。 | keep | 利齿鳄鱼袭邻敌、脚下水涌、强化一击/拖目标及施法者后退、施法者安全下骑在鳄后、鳄在禁重施齐全。 | crawl-ref/source/dat/descript/spells.txt:700；crawl-ref/source/dat/descript/zh/spells.txt:1645 |
| textdb:eruption spell | eruption spell | <br>裂开地面，在目标下方生成一个局部的、短暂存在的火山。 | keep | 裂地、目标下局部短命火山齐全。 | crawl-ref/source/dat/descript/spells.txt:708；crawl-ref/source/dat/descript/zh/spells.txt:477 |
| textdb:fastroot spell | fastroot spell | <br>射出一颗魔法种子，以快速生长的树根缠绕目标。被缠绕者将遭受痛苦的挤压，<br>直至挣脱或树根枯萎。树根只能在坚实的地面上生长。 | keep | 种子生快速根缠绕、痛苦挤压至逃或枯、仅实地齐全。 | crawl-ref/source/dat/descript/spells.txt:712；crawl-ref/source/dat/descript/zh/spells.txt:1651 |
| textdb:fire breath spell | fire breath spell | <br>向一个目标生物喷吐火焰气流。 | keep | 对目标喷火齐全。 | crawl-ref/source/dat/descript/spells.txt:724；crawl-ref/source/dat/descript/zh/spells.txt:486 |
| textdb:fire storm spell | fire storm spell | <br>这道法术能在目标区域塑造出一团威力巨大的火焰风暴，<br>在大范围内造成火焰伤害的同时还会留下一些短暂存在的火旋涡。<br>它造成的一半伤害无视火焰抗性。 | adjust | 目标强烈火风暴、短命火旋涡/半伤忽火抗齐全，但大范围伤害被省略未明确。 本批已修复并复核：漏大范围伤害。 | crawl-ref/source/dat/descript/spells.txt:728；crawl-ref/source/dat/descript/zh/spells.txt:490；crawl-ref/source/spl-damage.cc:cast_fire_storm |
| textdb:fireball spell | fireball spell | <br>掷出一个爆炸性的火球。 | keep | 爆炸火球投掷齐全。 | crawl-ref/source/dat/descript/spells.txt:734；crawl-ref/source/dat/descript/zh/spells.txt:496 |
| textdb:flame wave spell | flame wave spell | <br>用一波火焰冲击施法者的周围。<br>如果施法者保持专注，并为法术提供魔力（通过原地等待而不采取任何其他行动），<br>就会向外辐射更多更大的火焰波。 | keep | 自身周围一波火、原地等待不他动并供魔才更多更大波齐全。 | crawl-ref/source/dat/descript/spells.txt:738；crawl-ref/source/dat/descript/zh/spells.txt:500 |
| textdb:flaming cloud spell | flaming cloud spell | <br>生成一大团咆哮的火焰云。 | keep | 大团咆哮烈火云齐全。 | crawl-ref/source/dat/descript/spells.txt:744；crawl-ref/source/dat/descript/zh/spells.txt:506 |
| textdb:flash freeze spell | flash freeze spell | <br>冻结一个目标周围的空气，对目标造成重大伤害并短暂减慢其移动速度。<br>它造成的一半伤害无法被寒冷抗性抵御。 | adjust | 目标空气冰冻、重伤/半伤忽冷抗齐全，但短暂移动减慢的时限漏译。 本批已修复并复核：漏移动减慢的短暂时限。 | crawl-ref/source/dat/descript/spells.txt:748；crawl-ref/source/dat/descript/zh/spells.txt:510；crawl-ref/source/beam.cc:4524；crawl-ref/source/beam.cc:5267 |
| textdb:flashing balestra spell | flashing balestra spell | <br>军械库中的一个灵魂闪跃而出，以武器发动攻击，<br>随后独立决斗片刻，再返回翻腾的灵魂之中。 | keep | 军械库一个魂跳出武攻、独立决斗片刻、回灵魂旋流齐全。 | crawl-ref/source/dat/descript/spells.txt:753；crawl-ref/source/dat/descript/zh/spells.txt:1656 |
| textdb:flay spell | flay spell | <br>撕开目标身上痛苦的幻象伤口，伤口会在施法者死亡后或短时间内消失。<br>它不能直接杀死对方，并对非自然目标无效。 | keep | 疼痛幻伤、短时间或施法者死消、不可直接杀/非自然免疫齐全。 | crawl-ref/source/dat/descript/spells.txt:718；crawl-ref/source/dat/descript/zh/spells.txt:481 |
| textdb:fleetfoot spell | fleetfoot spell | <br>召来风力，在短时间内提高施法者的移动速度。 | keep | 短时风提高移动速度齐全。 | crawl-ref/source/dat/descript/spells.txt:759；crawl-ref/source/dat/descript/zh/spells.txt:515 |
| textdb:force lance spell | force lance spell | <br>发射一道震荡力。若命中造成伤害，可能会击退目标。<br>如果目标因此撞上墙壁或其他生物，二者都会受到额外伤害。 | keep | 震荡力命中并造成伤害才可能击退、撞墙/生物双方追加伤齐全。 | crawl-ref/source/dat/descript/spells.txt:763；crawl-ref/source/dat/descript/zh/spells.txt:519 |
| textdb:forceful invitation spell | forceful invitation spell | <br>从蛇穴、蜘蛛巢穴、沼泽、海滩、精灵殿堂、宝库或墓室之一召唤一些生物；<br>具体分支因施法者而异。 | adjust | 七个分支之一且随施法者不同齐全；Spider Nest被缩成蜘蛛巢违明确术语蜘蛛巢穴。 本批已修复并复核：分支名违反明确限定。 | crawl-ref/source/dat/descript/spells.txt:769；crawl-ref/source/dat/descript/zh/spells.txt:524；docs/glossary.md:Spider Nest |
| textdb:forge blazeheart golem spell | forge blazeheart golem spell | <br>在一颗不稳定的元素火花外锻造渣铁外壳。<br>它能像雨点般密集地对创造者的敌人造成打击——<br>如此猛烈，以至于魔像本身经常被它们的冲击所损坏。<br><br>它只能勉强独立于创造者的魔力，<br>每当两者离开彼此身边，它内部的火焰就会迅速休眠。<br>如果它的外壳在仍处于活动状态时被摧毁，暴露的核心将在片刻后剧烈爆炸。<br><br>法术威力越高，它的爆炸伤害就越高。 | keep | 不稳元素火花渣铁壳/猛烈打击反伤自身、相离快休眠、活动时毁壳稍后核爆、威力增爆伤齐全。 | crawl-ref/source/dat/descript/spells.txt:775；crawl-ref/source/dat/descript/zh/spells.txt:1312 |
| textdb:forge lightning spire spell | forge lightning spire spell | <br>在附近锻造一座无法移动的闪电尖塔。尖塔会不时向施法者的敌人释放电击，<br>并优先攻击离它最远的敌人。 | keep | 附近不动闪电塔、不时向敌电击、优先最远者齐全。 | crawl-ref/source/dat/descript/spells.txt:788；crawl-ref/source/dat/descript/zh/spells.txt:1356 |
| textdb:forge monarch bomb spell | forge monarch bomb spell | <br>锻造一个塞满集束小炸弹的飞行燃烧武器工厂。它能在近战中部署小炸弹，<br>也能将其发射至远处。君主炸弹的小炸弹不会自行攻击，而会追赶施法者的敌人，<br>直至收到爆炸信号。<br><br>此法术创造的任何造物仍然存在时再次施法，会引爆君主炸弹及所有小炸弹，<br>对它们相邻的所有生物造成火焰与物理混合伤害，但施法者自身除外。 | keep | 飞行燃烧厂集束弹、近布远射、小弹不自行攻击只追敌、任何造物仍在重施引爆全部、邻接混合火/物伤且自身免齐全。 | crawl-ref/source/dat/descript/spells.txt:794；crawl-ref/source/dat/descript/zh/spells.txt:1661 |
| textdb:forge phalanx beetle spell | forge phalanx beetle spell | <br>锻造一个小型机械守卫；只要与创造者相邻，它就会提高创造者的护甲。<br><br>方阵甲虫也能啃咬敌人，但绝不会自愿离开创造者身边；若被强行分开，<br>它会优先回到创造者身边，不顾其他事务。<br><br>法术威力会提高护甲加成幅度及甲虫自身的耐久度。 | keep | 小守卫邻创者加AC、可咬敌但不主动离/分离优先返、威力加AC及耐久齐全。 | crawl-ref/source/dat/descript/spells.txt:805；crawl-ref/source/dat/descript/zh/spells.txt:1670 |
| textdb:fortress blast spell | fortress blast spell | <br>汲取施法者自身的身体强度，制造一道对大范围敌人造成伤害的动能冲击波。<br>冲击波开始成形后的数回合内，施法者会被固定在原地；若在此期间被迫位移，<br>法术就会取消，但施法者仍可自由执行其他动作。<br><br>法术威力越高，法术完成得越快；造成的伤害则完全取决于施法者的护甲值。 | keep | 自身物理强度生成大面积动能波、锁数回合但可别动、期间移位取消、威力加快/伤仅AC齐全。 | crawl-ref/source/dat/descript/spells.txt:817；crawl-ref/source/dat/descript/zh/spells.txt:1679 |
| textdb:foxfire spell | foxfire spell | <br>在施法者附近生成两个燃烧的沼气球。球会迅速寻找最近的怪物并灼烧它们。<br>如果不能到达目标或者施法者与它们互换位置，它们将会无害地消散。 | keep | 两个相邻沼气火球、找最近怪、不可达/交换位无害消散齐全。 | crawl-ref/source/dat/descript/spells.txt:828；crawl-ref/source/dat/descript/zh/spells.txt:529 |
| textdb:freeze spell | freeze spell | <br>冰冻一个相邻的目标，造成的伤害能无视目标可能拥有的任何护甲。<br>这可能会暂时减缓冷血动物的速度。 | keep | 相邻目标无视护甲伤害、冷血可能暂慢齐全。 | crawl-ref/source/dat/descript/spells.txt:834；crawl-ref/source/dat/descript/zh/spells.txt:534 |
| textdb:freezing cloud spell | freezing cloud spell | <br>生成一大团致命的冰汽云。 | keep | 大团致命冷汽云齐全。 | crawl-ref/source/dat/descript/spells.txt:839；crawl-ref/source/dat/descript/zh/spells.txt:539 |
| textdb:freezing gust spell | freezing gust spell | <br>发射一道穿透性的严寒气流，在沿途留下致命的寒气云。 | keep | 穿透冷气箭/沿途致命冷云齐全。 | crawl-ref/source/dat/descript/spells.txt:843；crawl-ref/source/dat/descript/zh/spells.txt:1687 |
| textdb:frozen ramparts spell | frozen ramparts spell | <br>用冰封住周围的墙壁一小段时间。在冰墙附近游荡的敌人会受到伤害，<br>并可能会暂时减缓冷血生物的速度。每个受害者一次只能受到一面冰墙的影响。<br><br>如果施法者移动到新位置，冰会破裂、脱落。 | keep | 暂冰墙、邻墙敌伤/冷血可能慢、每目标仅一墙、施法者移位冰掉齐全。 | crawl-ref/source/dat/descript/spells.txt:848；crawl-ref/source/dat/descript/zh/spells.txt:543 |
| textdb:fugue of the fallen spell | fugue of the fallen spell | <br>呼唤那些早已死去者留下的残念。在激活状态下，<br>施法者及其盟友每杀死一个非召唤的敌人就会吸引更多复仇的灵魂进入施法者的武器，<br>暂时提高其近战和远程攻击力。当这个加成达到最大值时，<br>每次命中都会释出死者一丝痛苦，对与目标相邻的其他敌人造成痛楚伤害。<br><br>重施这个法术会使你失去对吸引来的灵魂的控制，重置你积累的任何加成，<br>即使在维持此法术期间，死者刺耳的哀嚎也可能引来不必要的注意。 | adjust | 长死者残余魂、己友杀非召唤敌积魂增近远效能、满时每击痛楚伤邻目标其他敌、重施重置/维持时哀嚎招注意齐全；弥留物误指临死且末句要保持它不自然。 本批已修复并复核：long-dead remnants误为临终弥留物。 | crawl-ref/source/dat/descript/spells.txt:856；crawl-ref/source/dat/descript/zh/spells.txt:550；crawl-ref/source/spl-selfench.cc:171；crawl-ref/source/player-reacts.cc:1277 |
| textdb:fulminant prism spell | fulminant prism spell | <br>生成一个由不稳定软金合金制成的闪亮棱镜。可惜它不能充当法定货币，<br>因为短时间后便会以奥术力量猛烈爆炸；若提前摧毁，爆炸会弱得多。 | keep | 不稳软金棱镜/不能货币幽默、短后奥术爆炸、提前毁爆弱齐全。 | crawl-ref/source/dat/descript/spells.txt:869；crawl-ref/source/dat/descript/zh/spells.txt:560 |
| textdb:fulsome fusillade spell | fulsome fusillade spell | <br>这部鲁莽化学的巅峰之作会创造大量易爆试剂，如雨般倾泻在敌人身上。<br>接下来的数回合中，视野内最多 3 个随机敌人会被爆炸烧杯击中，<br>受到火焰、寒冷、电击或毒素伤害。如果爆炸彼此重叠，反应会造成更高的<br>不可抵抗伤害，并有时给爆炸范围内的目标施加随机有害状态。<br><br>维持此法术每回合会消耗少量魔力。爆炸绝不会瞄准可能伤害施法者的位置，<br>但施法者的盟友及附近其他事物就没有这么幸运了。 | keep | 数回合每次最多3随机可见敌试剂火冷电毒、重叠更强不可抗伤及可能随机负面、逐回合耗MP、自身安全友方未必齐全。 | crawl-ref/source/dat/descript/spells.txt:876；crawl-ref/source/dat/descript/zh/spells.txt:1691 |
| textdb:funeral dirge spell | funeral dirge spell | <br>这首仪礼歌可以短暂地唤起附近的几个亡灵盟友，<br>让他们更快地移动，并以更大的力量进行攻击。 | keep | 数名附近亡灵友方短时快移强攻齐全。 | crawl-ref/source/dat/descript/spells.txt:891；crawl-ref/source/dat/descript/zh/spells.txt:565 |
| textdb:galvanic breath spell | galvanic breath spell | <br>&lt;Galvanic Breath ability&gt; | keep | Galvanic Breath能力引用完整，已复审目标与相连生物电链。 | crawl-ref/source/dat/descript/spells.txt:896；crawl-ref/source/dat/descript/zh/spells.txt:1701 |
| textdb:gell's gavotte spell | gell's gavotte spell | <br>短暂地将局部重力重新定向为施法者选择的某个基本方向，使视野内所有生物<br>向该方向翻滚一小段距离。<br><br>施法者不能免疫此法术的重力效应，但会受到缓冲而免受碰撞伤害。其他生物<br>则没有这般幸运——骤然的撞击会重创任何未贴近新的"地面"站立的生物。<br><br>重力需要短暂时间才能稳定到足以重新施放此法术，不过更强大的法师能够<br>更频繁地使用它。 | keep | 四正方向局部重力/视野全体短移、施法者也移动但无碰撞伤/其他未贴新地面受伤、短冷高威力更频繁齐全。 | crawl-ref/source/dat/descript/spells.txt:900；crawl-ref/source/dat/descript/zh/spells.txt:1705 |
| textdb:ghostly fireball spell | ghostly fireball spell | <br>掷出一颗爆炸性的负能量球，使其笼罩的所有活物陷入衰竭。 | keep | 爆炸负能量球、笼罩活物衰竭齐全。 | crawl-ref/source/dat/descript/spells.txt:914；crawl-ref/source/dat/descript/zh/spells.txt:570 |
| textdb:ghostly sacrifice spell | ghostly sacrifice spell | <br>以一名友方的活力精华制造一股负能量，使其笼罩的所有活物陷入衰竭。<br>为法术提供燃料的友方，无论是活物还是造物，都会在此过程中被吞噬并彻底抹除。 | keep | 友方活力作负能爆、活物衰竭、献祭活物或构装体都被消灭齐全。 | crawl-ref/source/dat/descript/spells.txt:919；crawl-ref/source/dat/descript/zh/spells.txt:574 |
| textdb:glacial breath spell | glacial breath spell | <br>&lt;Glacial Breath ability&gt; | keep | Glacial Breath引用完整，已复审击杀后留坚固冰块。 | crawl-ref/source/dat/descript/spells.txt:925；crawl-ref/source/dat/descript/zh/spells.txt:1716 |
| textdb:glaciate spell | glaciate spell | <br>召来一股强大的寒冰冲击。锥形范围内的生物会受到伤害，<br>越靠近施法者，所受伤害越高。被冲击命中的生物会被冰封，移动速度减慢；<br>被冲击杀死的生物则可能冻成坚实的冰块。<br>它造成的一半伤害无法被寒冷抗性抵御。 | keep | 强冰锥、近更伤、命中冰封慢移/击杀可能冰块、半伤忽寒抗齐全。 | crawl-ref/source/dat/descript/spells.txt:929；crawl-ref/source/dat/descript/zh/spells.txt:579 |
| textdb:gloom spell | gloom spell | <br>释放一波有害阴霾，试图吞没附近生物周围的光亮。<br>任何被波及的活物、恶魔或神圣生物都可能短暂失明，盲目踉跄。<br>意志力无法抵抗此法术，但更强壮的生物仍可能摆脱效果。 | keep | 附近吞光、活物恶魔神圣可短盲、意志无效但强者可挡齐全。 | crawl-ref/source/dat/descript/spells.txt:937；crawl-ref/source/dat/descript/zh/spells.txt:345 |
| textdb:grasping roots spell | grasping roots spell | <br>从地下深处召出巨大的抓握根须，抓住并挤压受害者。<br>若受害者挣脱，或召唤者移出其视野，根须便会退去。 | keep | 深根抓握挤压、逃脱/施法者离视线根退齐全。 | crawl-ref/source/dat/descript/spells.txt:946；crawl-ref/source/dat/descript/zh/spells.txt:586 |
| textdb:grave claw spell | grave claw spell | <br>唤起新近死者的怨恨，以骨片刺穿指定敌人。此法术绝不会落空，<br>并会将目标固定在原地数回合，但每次施放都会迅速消耗施法者身上残留的死亡气息。<br><br>最多可积蓄足以施放三次的怨恨；只有造成足够多活物死亡才能补充。 | keep | 骨片指定敌必中/数回合定身、最多存3次、消耗残死/足够活物死亡充能齐全。 | crawl-ref/source/dat/descript/spells.txt:952；crawl-ref/source/dat/descript/zh/spells.txt:1720 |
| textdb:greater ensnare spell | greater ensnare spell | <br>向生物射出一连串的网，使目标困于黏性的网中，并在附近散布额外蛛网；<br>这些蛛网会在短时间后消散。 | keep | 蛛网流困目标、周围额外蛛网/短时消散齐全。 | crawl-ref/source/dat/descript/spells.txt:967；crawl-ref/source/dat/descript/zh/spells.txt:1727 |
| textdb:hailstorm spell | hailstorm spell | <br>召来一阵冰雹，痛击附近未能躲避的生物。<br>风暴眼足够宽广，紧邻施法者的怪物不会受影响。<br>由于强烈的冲击和锋利边缘，它造成的一半伤害无法被寒冷抗性抵御。 | keep | 附近未躲冰雹伤、相邻风眼免疫、冲击切割半伤忽寒抗齐全。 | crawl-ref/source/dat/descript/spells.txt:972；crawl-ref/source/dat/descript/zh/spells.txt:595 |
| textdb:harpoon shot spell | harpoon shot spell | <br>发射一个长而灵活的带刺重物。<br>被它捕捉的受害者会被拉至与施法者相邻的位置或与挡住去路的东西相撞。 | adjust | 长柔韧带刺物拉扯、撞途中障碍齐全；adjacent只写附近，漏精确相邻落点。 本批已修复并复核：精确相邻落点弱化。 | crawl-ref/source/dat/descript/spells.txt:983；crawl-ref/source/dat/descript/zh/spells.txt:605；crawl-ref/source/beam.cc:pull_actor |
| textdb:haste other spell | haste other spell | <br>加速一个附近友方的行动。 | keep | 附近一友方所有行动加速齐全。 | crawl-ref/source/dat/descript/spells.txt:979；crawl-ref/source/dat/descript/zh/spells.txt:601 |
| textdb:haste spell | haste spell | <br>加速施法者的行动。 | keep | 自己行动加速齐全。 | crawl-ref/source/dat/descript/spells.txt:988；crawl-ref/source/dat/descript/zh/spells.txt:610 |
| textdb:haunt spell | haunt spell | <br>召唤幽魂和幽灵，以困扰施法者的目标。他们只会攻击他们所缠扰的生物，<br>一旦目标死亡，它们会迅速消散。召唤出的幽灵数量随法术威力增强而增加。 | adjust | 幽灵鬼魂只打缠扰目标、目标死快消、威力增数量齐全。 本批已修复并复核：wraith亚类被混成ghost近义类。 | crawl-ref/source/dat/descript/spells.txt:992；crawl-ref/source/dat/descript/zh/spells.txt:614；docs/decisions.md:D-A-038；crawl-ref/source/spl-summoning.cc:cast_haunt |
| textdb:heal other spell | heal other spell | <br>治疗附近的一个盟友。 | keep | 附近一友方治疗齐全。 | crawl-ref/source/dat/descript/spells.txt:1012；crawl-ref/source/dat/descript/zh/spells.txt:619 |
| textdb:hellfire court spell | hellfire court spell | <br>召唤火焰与天谴恶魔。 | keep | 召火与天谴恶魔齐全；Court法庭/宫廷有双义，仅可提非阻断宫廷建议，不无依据推翻旧名。 建议处理：retain；Court亦可指魔王宫廷随从；“地狱火宫廷”可供风格讨论，现有法庭意象尚无足够反证，不强制改名。 | crawl-ref/source/dat/descript/spells.txt:998；crawl-ref/source/dat/descript/zh/spells.txt:623 |
| textdb:hellfire mortar spell | hellfire mortar spell | <br>劈开施法者前方的地面，以熔岩塑造出一门可怕的武器。<br>这门迫击炮会沿充满熔岩的裂隙缓慢移动，并自动向施法者的敌人发射岩浆。<br><br>迫击炮抵达路径终点或被其他生物挡住时，会沉回熔岩；<br>裂隙随后也会很快闭合。 | keep | 前方裂地熔岩炮、慢沿裂隙自射岩浆、尽头/生物阻挡沉回、裂隙稍后合齐全。 | crawl-ref/source/dat/descript/spells.txt:1002；crawl-ref/source/dat/descript/zh/spells.txt:1732 |
| textdb:hoarfrost bullet spell | hoarfrost bullet spell | <br>发射一枚冰片，为命中的目标覆盖一层脆霜，使其移动减慢。<br><br>每次发射都会消耗火炮剩余耐久度；若火炮存续到发射 5 次，<br>最后一发会碎裂并额外伤害主要目标周围的所有敌人。 | keep | 冰片覆脆霜慢移、每发损耐久、存活发5次则末发碎射全邻敌额外伤齐全。 | crawl-ref/source/dat/descript/spells.txt:1030；crawl-ref/source/dat/descript/zh/spells.txt:1740 |
| textdb:hoarfrost cannonade spell | hoarfrost cannonade spell | <br>塑造两座冰霜火炮，从远处攻击施法者的敌人。<br>它们发射的寒冷碎片会迅速在目标身上覆上一层脆霜，减慢其移动速度。<br><br>这些火炮寿命短暂，每次发射碎片都会消耗自身的一部分；<br>如果未受干扰并存续到发射最终齐射，最后一轮攻击会格外强力。 | keep | 两炮远程冰片慢移、短命/每发耗体、未干预存到最后更强齐全。 | crawl-ref/source/dat/descript/spells.txt:1039；crawl-ref/source/dat/descript/zh/spells.txt:1747 |
| textdb:holy breath spell | holy breath spell | <br>呼出一大片闪耀着善神荣光的神圣火焰云。<br>这些火焰对亡灵和恶魔生物特别致命，对神圣生物没有影响。 | adjust | 大团神圣火/善神荣、亡灵恶魔更伤/神圣免齐全；cloud可明确云以保留残留地形信息。 建议处理：adopt；可补“火焰云”使cloud地形更直观；一团火焰为可成立形态近义。 | crawl-ref/source/dat/descript/spells.txt:1049；crawl-ref/source/dat/descript/zh/spells.txt:640 |
| textdb:holy flames spell | holy flames spell | <br>用神圣的火焰圈住一个敌人。<br>这些火焰对亡灵和恶魔生物特别致命，对神圣生物没有影响。 | keep | 圣火环困敌、亡灵恶魔更伤/圣者免齐全。 | crawl-ref/source/dat/descript/spells.txt:1055；crawl-ref/source/dat/descript/zh/spells.txt:645 |
| textdb:hunting call spell | hunting call spell | <br>激励附近盟友加快移动。 | keep | 附近友军快移齐全。 | crawl-ref/source/dat/descript/spells.txt:1016；crawl-ref/source/dat/descript/zh/spells.txt:627 |
| textdb:hurl damnation spell | hurl damnation spell | <br>&lt;Hurl Damnation ability&gt; | keep | Hurl Damnation能力引用完整，已核目标邻伤/防护无效/免疫例外。 | crawl-ref/source/dat/descript/spells.txt:1020；crawl-ref/source/dat/descript/zh/spells.txt:631 |
| textdb:hurl sludge spell | hurl sludge spell | <br>生成一道饱含剧毒的污泥，它会让受害者中毒并使其周围浸满污泥。<br>污泥会对所有怪物造成伤害、引起中毒，即使是那些抗毒的怪物。 | adjust | 剧毒污泥伤/毒/毒抗者仍受影响齐全；浸满周围污泥被写成仅环境变湿。 本批已修复并复核：毒泥浸润被写成普通潮湿。 | crawl-ref/source/dat/descript/spells.txt:1024；crawl-ref/source/dat/descript/zh/spells.txt:635；crawl-ref/source/spl-zap.cc:205；crawl-ref/source/beam.cc:HURL_SLUDGE |
| textdb:hurl torchlight spell | hurl torchlight spell | <br>掷出一股暗影火炬之光，对活物、恶魔和神圣生物造成无法抵抗的伤害。<br>火炬之光还会短暂增强被其爆发击中的友方亡灵，提高其近战伤害，<br>并让其免费行动一次。<br><br>它不会伤害崇拜伊莱德莱姆努尔的生物。 | keep | 活物恶魔神圣不可抗伤、友方亡灵增近战并一次免费行动、同教Yred无害齐全。 | crawl-ref/source/dat/descript/spells.txt:1061；crawl-ref/source/dat/descript/zh/spells.txt:1755 |
| textdb:ice thorns spell | ice thorns spell | <br>使尖锐的冰棘从目标敌人周围的地面长出，形成一圈。<br>任何不会飞的生物踏上冰棘都会受到伤害，随后冰棘便会碎裂消失。<br><br>施法者踏上自己的冰棘不会受伤，但冰棘仍会碎裂。 | keep | 目标敌周围冰棘环、非飞踏伤后碎、自踏无伤仍碎齐全。 | crawl-ref/source/dat/descript/spells.txt:1075；crawl-ref/source/dat/descript/zh/spells.txt:2125 |
| textdb:iceblast spell | iceblast spell | <br>发射一大团冰块，在撞击时爆炸。<br>它造成的一半伤害无法被寒冷抗性抵御。 | keep | 大冰块撞爆/半伤忽寒抗齐全。 | crawl-ref/source/dat/descript/spells.txt:1070；crawl-ref/source/dat/descript/zh/spells.txt:650 |
| textdb:ignite poison spell | ignite poison spell | <br>将附近的所有毒素变成液态火焰，从内部灼烧中毒的生物。<br>它还会将毒云和迷乱烟雾变成火焰。施法者不会直接受到影响。 | keep | 附近毒转液火由内焚中毒者、毒云迷瘴转火、自身不直接受影响齐全。 | crawl-ref/source/dat/descript/spells.txt:1084；crawl-ref/source/dat/descript/zh/spells.txt:655 |
| textdb:ignition spell | ignition spell | <br>施法者周围的所有敌人都被火球吞噬。<br>施法者及其友方免受火焰伤害，永远不会被此法术伤害。 | keep | 周遭全敌火球、自己友方绝不受本法伤齐全。 | crawl-ref/source/dat/descript/spells.txt:1090；crawl-ref/source/dat/descript/zh/spells.txt:660 |
| textdb:ill omen spell | ill omen spell | <br>扭曲目标的命运之网，施加大量厄运。施法者与目标之间有任何阻碍时均无法使用。 | keep | 大量厄运、目标间有任意阻碍不可齐全。 | crawl-ref/source/dat/descript/spells.txt:1096；crawl-ref/source/dat/descript/zh/spells.txt:1763 |
| textdb:infernal servant spell | infernal servant spell | <br>召唤一个大恶魔。 | keep | 召大恶魔齐全；此怪物法术固定正文与能力长文不是同一范围。 | crawl-ref/source/dat/descript/spells.txt:963；crawl-ref/source/dat/descript/zh/spells.txt:591 |
| textdb:infestation spell | infestation spell | <br>召来圣甲虫瘟疫，使受影响的生物遭到侵染，持续时间取决于法术威力。<br>死亡圣甲虫会在这些生物体内生长，并在它们死亡时破体而出。 | adjust | 甲虫感染/死亡爆出死亡甲虫齐全；威力决定感染持续时间被错接为按威力感染。 本批已修复并复核：威力修饰的持续时间错接；死亡甲虫与当前实体死亡圣甲虫可统一，保留直接命题后由怪物词根组择定。。 建议处理：adopt；死亡甲虫与当前实体死亡圣甲虫可统一，保留直接命题后由怪物词根组择定。 | crawl-ref/source/dat/descript/spells.txt:1101；crawl-ref/source/dat/descript/zh/spells.txt:666；crawl-ref/source/spl-summoning.cc:2270；crawl-ref/source/beam.cc:BEAM_INFESTATION |
| textdb:injury bond spell | injury bond spell | <br>将施法者与附近的盟友联结起来，使他们受到的所有伤害减半；<br>作为代价，施法者会承受被阻止伤害的一半。 | keep | 友军受伤减半、施法者只受被免部分的一半齐全，未写成完整承受一半初始伤。 | crawl-ref/source/dat/descript/spells.txt:1107；crawl-ref/source/dat/descript/zh/spells.txt:671 |
| textdb:injury mirror spell | injury mirror spell | <br>短时间内反射所受伤害；施法者每次受到伤害时，都会伤害攻击者。<br>持续时间结束后，施法者会有一小段时间无法再次施放此法术。 | keep | 暂反伤/每次自身受伤伤攻击者、结束后短禁再施齐全。 | crawl-ref/source/dat/descript/spells.txt:1112；crawl-ref/source/dat/descript/zh/spells.txt:676 |
| textdb:ink cloud spell | ink cloud spell | <br>释出浓厚的墨云，模糊视线。 | keep | 浓墨云遮视线齐全。 | crawl-ref/source/dat/descript/spells.txt:1118；crawl-ref/source/dat/descript/zh/spells.txt:681 |
| textdb:inner flame spell | inner flame spell | <br>向一个敌人体内灌入烈火。目标每次被击中时都会释放火焰，<br>死亡时更会猛烈爆炸；爆炸范围取决于目标体形。 | keep | 内火每次命中释火/死爆、爆范围由目标体型齐全。 | crawl-ref/source/dat/descript/spells.txt:1122；crawl-ref/source/dat/descript/zh/spells.txt:685 |
| textdb:invisibility other spell | invisibility other spell | <br>使附近的一个友方隐形。 | keep | 附近友方隐形齐全。 | crawl-ref/source/dat/descript/spells.txt:1136；crawl-ref/source/dat/descript/zh/spells.txt:697 |
| textdb:invisibility spell | invisibility spell | <br>使施法者隐形，并将其随机移至不远处。<br><br>当敌人处于你看不见的隐形状态时，你对其攻击的命中率会降低，<br>对其攻击的闪避和格挡能力也会受到严重削弱。 | keep | 自身隐形及随机短移、对看不见敌命中降/闪避格挡重罚齐全。 | crawl-ref/source/dat/descript/spells.txt:1128；crawl-ref/source/dat/descript/zh/spells.txt:690 |
| textdb:iron shot spell | iron shot spell | <br>掷出一个巨大而沉重的钢铁投射物。 | keep | 大重金属弹齐全，钢铁与铁弹材质语境相容。 | crawl-ref/source/dat/descript/spells.txt:1140；crawl-ref/source/dat/descript/zh/spells.txt:701 |
| textdb:irradiate spell | irradiate spell | <br>将施法者一层极薄的皮肤（或类似物质）直接转为纯魔法能量，轰击相邻生物。<br>这可能会使目标严重变形、虚弱，并削弱其护甲。施法者并非完全不受影响；<br>身上仍残留着一些魔力，在几次施法后它们会对身体造成危险的污染。 | adjust | 极薄皮肤转纯魔能炸邻物、可能重变形弱/降AC、几施后危险污染齐全；皮肤的或类似物质句多出的的需删。 本批已修复并复核：重复助词造成病句。 | crawl-ref/source/dat/descript/spells.txt:1144；crawl-ref/source/dat/descript/zh/spells.txt:705；crawl-ref/source/spl-damage.cc:2123 |
| textdb:iskenderun's battlesphere spell | iskenderun's battlesphere spell | <br>召出一颗由破坏性能量构成的小型战斗法球。每当创造者施放攻击性法术，<br>战斗法球也会向它能触及的附近敌人中受伤最重者射出绝不会落空的能量齐射。<br><br>创造者的攻击可以自由穿过战斗法球的位置而不伤到它。 | keep | 小能量球/每攻击法术后向最伤可达近敌必中齐射、可自由穿射不伤齐全。 | crawl-ref/source/dat/descript/spells.txt:1152；crawl-ref/source/dat/descript/zh/spells.txt:711 |
| textdb:iskenderun's mystic blast spell | iskenderun's mystic blast spell | <br>引爆一颗劈啪作响的破坏性能量球。爆炸会以物理力量冲击附近所有怪物，<br>并击退受到伤害的目标。法术威力会提高伤害和击退距离。 | keep | 物理能量球爆击附近全怪、有伤则击退、威力增伤增距离齐全。 | crawl-ref/source/dat/descript/spells.txt:1161；crawl-ref/source/dat/descript/zh/spells.txt:718 |
| textdb:jinxbite spell | jinxbite spell | <br>唤起顽劣之灵的留意。效果还在持续时，顽劣之灵会跟进施法者的攻击。<br>如果这个法术击垮了受害者的意志力，<br>他们将受到轻微伤害，并会被灵体顽皮的恶意衰竭。<br><br>然而，灵体的援助是反复无常的；除非看到了易受影响的受害者，<br>否则无法呼唤他们，而且一旦没有其他受害者，它们就会迅速消散。<br>呼唤灵体也会在一段时间内降低施法者自身的意志力。 | keep | 顽灵跟进攻击/过意志检则小伤及衰竭、需可见易感目标/无目标快消、自身意志暂降齐全。 | crawl-ref/source/dat/descript/spells.txt:1167；crawl-ref/source/dat/descript/zh/spells.txt:723 |
| textdb:kinetic grapnel spell | kinetic grapnel spell | <br>以细薄的动能丝缠绕施法者的近战武器，并把另一端射向附近敌人。<br>若抓钩命中并造成伤害，便会嵌入目标，使施法者下一次对其发动的近战攻击<br>必定命中，并获得少量杀伤加成。 | keep | 近战武器动能丝射近敌、命中有伤嵌入、下一次对其近战必中/少杀伤加成齐全。 | crawl-ref/source/dat/descript/spells.txt:1177；crawl-ref/source/dat/descript/zh/spells.txt:1767 |
| textdb:kiss of death spell | kiss of death spell | <br>从施法者的精元中塑出一枚碎片，再将其扭曲为死亡碎片，痛苦地衰竭受击者。<br>施法者自身的最大生命值也会衰竭，直到获得足够的经验值后才会恢复。 | adjust | 自身精元化死片痛楚衰竭敌、自生命降低至经验恢复齐全；可非阻断明确最大生命值以贴drain_player。 建议处理：adopt；可明确经验恢复的是生命值上限衰竭，避免与一般受伤混淆；英文也只说health reduced。 | crawl-ref/source/dat/descript/spells.txt:2394；crawl-ref/source/dat/descript/zh/spells.txt:1460 |
| textdb:landbreaker spell | landbreaker spell | <br>猛烈震裂地貌，使碎石砸向数名附近敌人及其身后的地面，<br>从而阻断它们逃离施法者的路线。 | keep | 裂地砸数敌及身后地面、阻逃施法者路径齐全。 | crawl-ref/source/dat/descript/spells.txt:1191；crawl-ref/source/dat/descript/zh/spells.txt:1773 |
| textdb:launch bomblet spell | launch bomblet spell | <br>沿无视火线的弹道发射一枚小型炸弹，对射程内的单个目标造成少量伤害，<br>并将炸弹部署在其附近。无法以紧邻施法者的敌人为目标；<br>若目标附近没有空间供炸弹落下，也无法以其为目标。 | keep | 抛物弹忽射线、射程单敌小伤/其旁部署弹、邻敌或附近无空不可齐全。 | crawl-ref/source/dat/descript/spells.txt:1197；crawl-ref/source/dat/descript/zh/spells.txt:1778 |
| textdb:launch clockwork bee spell | launch clockwork bee spell | <br>制造一只机械蜜蜂，并用数回合上紧发条，再将其放出攻击指定敌人。<br>蜜蜂迅捷而强大，但攻击会很快耗尽发条，最终使其无助地停止移动。<br><br>施法者可尝试移入休眠蜜蜂所在位置，花费 1点法力修复并重新上紧发条。<br><br>法术威力会增加蜜蜂休眠前可发动的攻击次数。 | keep | 数回合造上弦蜂/快强/攻击耗弦至不能动、移入花1MP修补重上、威力增休眠前攻击数齐全。 | crawl-ref/source/dat/descript/spells.txt:1205；crawl-ref/source/dat/descript/zh/spells.txt:1784 |
| textdb:launch sporangium spell | launch sporangium spell | <br>发射一个腐蚀性孢子囊；它会追逐任何诱人的营养来源——例如你自己——<br>并将其吞没在巨大酸液爆炸中。爆炸接触的墙壁上可能扎根初生原生质体，<br>它们能自行发射酸液，但任何一只原生质体的 2 格内都不会再生成另一只。 | keep | 腐蚀孢子囊逐营养源含自己/大酸爆、触墙可初生原生质体自射酸/彼此2格内不再生齐全。 | crawl-ref/source/dat/descript/spells.txt:1218；crawl-ref/source/dat/descript/zh/spells.txt:1793 |
| textdb:leda's liquefaction spell | leda's liquefaction spell | <br>这道法术让施法者身边的地面液化，使地面变得难以通行。<br>在液化地面的任何移动都将减慢，被困在液化地面上的生物将无法飞行。<br>近战攻击施法者的尝试可能会失败。<br><br>起始的生效范围的半径取决于法术威力，然后会缩小，最后只覆盖施法者，<br>直到完全失效。维持着与大地的连接会减慢施法者的移动速度，即使他们正在飞行。 | keep | 液地慢移动/困者不飞/近战可能失败、威力初半径渐缩最终自身、即飞行施法者也慢齐全。 | crawl-ref/source/dat/descript/spells.txt:1225；crawl-ref/source/dat/descript/zh/spells.txt:739 |
| textdb:lee's rapid deconstruction spell | lee's rapid deconstruction spell | <br>将一堵墙或一个可见的易碎怪物炸成致命的碎片。<br>这适用于由冰、骨或任何壁状物质构成的怪物，<br>也可以用在那些被石化成石头的怪物。防具可以大大削弱其造成的伤害。<br><br>由岩石、冰或骨构成的目标会引起小爆炸。<br>金属目标会引起一个范围小却更具有破坏性的爆炸，<br>而水晶目标会引起一个范围大而更具有破坏性的爆炸。 | keep | 墙及可见脆怪碎片、冰骨墙材石化可用、护甲大减、石冰骨小爆/金属小强/晶体大强齐全。 | crawl-ref/source/dat/descript/spells.txt:1236；crawl-ref/source/dat/descript/zh/spells.txt:748 |
| textdb:legendary destruction spell | legendary destruction spell | <br>立刻连续产生两个爆炸魔法效果。效果会是火球、冰爆和幽灵火球的任意组合。 | adjust | 瞬时连两个爆法、火球冰爆幽灵火球任意组合齐全；把Ghostly Fireball写旧名鬼火球。 本批已修复并复核：引用法术名称过时。 | crawl-ref/source/dat/descript/spells.txt:1247；crawl-ref/source/dat/descript/zh/spells.txt:758；docs/glossary.md:Ghostly Fireball |
| textdb:lehudib's crystal spear spell | lehudib's crystal spear spell | <br>掷出一枚致命而锋利的水晶碎片。 | keep | 致命锋利水晶片齐全。 | crawl-ref/source/dat/descript/spells.txt:1252；crawl-ref/source/dat/descript/zh/spells.txt:762 |
| textdb:lesser beckoning spell | lesser beckoning spell | <br>将目标引来，试图将其拉至与施法者相邻的位置。 | adjust | 招引目标尝试至相邻；中文仅靠近遗漏精确目的格。 本批已修复并复核：招引终点遗漏相邻限定。 | crawl-ref/source/dat/descript/spells.txt:1256；crawl-ref/source/dat/descript/zh/spells.txt:766；crawl-ref/source/spl-transloc.cc:beckon |
| textdb:lightning bolt spell | lightning bolt spell | <br>发射一道强大且可穿透目标的闪电箭，其伤害无视目标一半的护甲，<br>并且可以从墙壁上弹回，击中目标两次。 | adjust | 强穿电箭/墙反弹两击齐全；半护甲误成半伤害无视护甲。 本批已修复并复核：半护甲误为半伤害。 | crawl-ref/source/dat/descript/spells.txt:1260；crawl-ref/source/dat/descript/zh/spells.txt:770；crawl-ref/source/beam.cc:4608 |
| textdb:magic dart spell | magic dart spell | <br>这道法术射出一支小魔法射弹，该法术百发百中。 | keep | 小魔能飞弹必命中齐全。 | crawl-ref/source/dat/descript/spells.txt:1265；crawl-ref/source/dat/descript/zh/spells.txt:775 |
| textdb:magma barrage spell | magma barrage spell | <br>向至多两个不同敌人发射穿透性熔岩弹；造成的伤害有一半无视火焰抗性。 | keep | 至多两个不同敌/穿熔岩箭/半伤忽火抗齐全。 | crawl-ref/source/dat/descript/spells.txt:1269；crawl-ref/source/dat/descript/zh/spells.txt:1799 |
| textdb:magnavolt spell | magnavolt spell | <br>以一层带磁电的金属碎片包裹目标，随后释放强大电流，<br>必定向所有可见且带有碎片的目标跳跃，并为每个标记者追加一道电束。<br>被磁化的生物无法闪避攻击，隐形时也会显形；若在碎片仍附着时死亡，<br>会留下短时带电金属云，继续充当此法术的引雷物。 | keep | 磁化金属层、每可见覆碎片目标必中额外电束、无法闪避/揭隐、死留短金属云仍引雷齐全。 | crawl-ref/source/dat/descript/spells.txt:1274；crawl-ref/source/dat/descript/zh/spells.txt:1803 |
| textdb:major destruction spell | major destruction spell | <br>向目标生物射出随机的有害射束或爆炸。 | keep | 随机有害射束或爆炸对目标齐全；AXED兼容仅保留现文不推历史机制。 | crawl-ref/source/dat/descript/spells.txt:1286；crawl-ref/source/dat/descript/zh/spells.txt:779 |
| textdb:major healing spell | major healing spell | <br>治疗施法者身体所受的大量伤害。 | keep | 自己大量伤害治疗齐全。 | crawl-ref/source/dat/descript/spells.txt:1290；crawl-ref/source/dat/descript/zh/spells.txt:783 |
| textdb:malign gateway spell | malign gateway spell | <br>这道法术能在现实世界中撕开一道裂口，<br>创造出一座能暂时自我维系、通往某个未知且污秽异界的传送门。<br>该法术需要开阔的空间才能成功。<br>片刻之后，一条强大的长有爪子的触手将穿过传送门，<br>在一段时间内会受施法者的意志所制约，其持续时间取决于法术威力。<br>随着传送门的失效，触手将被切断并转而攻击施法者。<br>传送门的持续时间随法术威力的增强而增加。 | keep | 现实裂污异界自维暂门、需开地/稍后触手、依威力受控/到期断而敌/威力延门齐全。 | crawl-ref/source/dat/descript/spells.txt:1294；crawl-ref/source/dat/descript/zh/spells.txt:787 |
| textdb:malign offering spell | malign offering spell | <br>吸取一个敌人的生命，同时治疗附近的盟友。 | keep | 汲敌命治疗附近友方齐全。 | crawl-ref/source/dat/descript/spells.txt:1303；crawl-ref/source/dat/descript/zh/spells.txt:797 |
| textdb:malmutate spell | malmutate spell | <br>让一个目标发生一次变异。这种变异几乎总是有害的。<br>它不会影响人造物；亡灵若受到影响则会腐朽。 | keep | 一次通常有害变异、人造免/亡灵腐朽齐全。 | crawl-ref/source/dat/descript/spells.txt:1307；crawl-ref/source/dat/descript/zh/spells.txt:801 |
| textdb:manifold assault spell | manifold assault spell | <br>将空间扭曲成反常结构，以一次近战攻击同时打击多个可见敌人。<br>法术威力越高，单次施法攻击的敌人越多；徒手攻击一次只能打击一半数量，<br>因为扭曲自己的肢体需要格外谨慎。<br><br>攻击耗时与普通近战攻击完全相同。这类攻击绝不会落空，<br>但无法精确控制命中位置，因此不能对毫无戒备的敌人造成额外伤害。 | keep | 空间多可见敌一次近战/威力增数量、徒手半数、同近战耗时/必中/不能背刺加伤齐全。 | crawl-ref/source/dat/descript/spells.txt:1312；crawl-ref/source/dat/descript/zh/spells.txt:806 |
| textdb:mara summon spell | mara summon spell | <br>编织出施法者的幻象。这些幻象拥有与本体相同的物理战斗能力，也能施放相同的法术。 | keep | 施法者幻象等战斗/等法术齐全。 | crawl-ref/source/dat/descript/spells.txt:1324；crawl-ref/source/dat/descript/zh/spells.txt:815 |
| textdb:march of sorrows spell | march of sorrows spell | <br>生成一股窃取的痛苦之流，它的尾迹和目标周围会留下郁积愁云。<br>这些负能量云会迅速夺去活物的生命值，每次数额相当于其最大生命值的一小部分。 | adjust | 痛苦流尾及目标旁负能云、按最大HP比例迅速损当前生命；中文遗漏活物限定与小比例。 本批已修复并复核：漏活物及小比例限定。 | crawl-ref/source/dat/descript/spells.txt:1329；crawl-ref/source/dat/descript/zh/spells.txt:819；crawl-ref/source/cloud.cc:1394 |
| textdb:marshlight spell | marshlight spell | <br>在施法者附近生成两个燃烧的沼气球。球会迅速寻找最近的怪物并灼烧它们。<br>巫师试着将其仿制为“狐火”，但他们的版本的威力要小得多。 | keep | 两个邻沼气球找最近怪焚烧、巫师仿狐火但弱很多齐全。 | crawl-ref/source/dat/descript/spells.txt:1335；crawl-ref/source/dat/descript/zh/spells.txt:824 |
| textdb:martyr's knell spell | martyr's knell spell | <br>召唤一个早已死去的殉道者的灵魂来保护你的盟友一段时间。<br>这个灵魂将分担你的盟友原本会受到的伤害。<br><br>如果它被杀（再次！），它将变成一个剥皮鬼，会对敌人造成虚幻的创伤。<br>这样的伤口转瞬即逝，当鬼魂离开时就会消退——除非你能先杀死它的受害者。 | keep | 长死殉道灵暂护/分担部分友伤、再死剥皮鬼/幻伤/短暂离去消/先杀例外齐全。 | crawl-ref/source/dat/descript/spells.txt:1341；crawl-ref/source/dat/descript/zh/spells.txt:829 |
| textdb:mass confusion spell | mass confusion spell | <br>让所有注视着施法者的人陷入混乱之中。 | keep | 注视施法者全体混乱齐全。 | crawl-ref/source/dat/descript/spells.txt:1350；crawl-ref/source/dat/descript/zh/spells.txt:837 |
| textdb:mass regeneration spell | mass regeneration spell | <br>使附近所有友方怪物在短时间内快速再生。<br>每个目标的恢复量都与其自身最大生命值成正比。 | keep | 附近全友方怪短期快再生、按各自maxHP正比齐全。 | crawl-ref/source/dat/descript/spells.txt:1354；crawl-ref/source/dat/descript/zh/spells.txt:1810 |
| textdb:maxwell's capacitive coupling spell | maxwell's capacitive coupling spell | <br>只要施法者保持专注（原地等待且不采取任何其他行动），体内就会逐渐积累电荷。<br>达到阈值后，电荷会与最近的可见敌人耦合，立即将其蒸发。法术威力越高，<br>积累电荷的速度越快。开始积累电荷时需要一个可见目标，但释放电荷时<br>可能会选中另一个敌人。 | keep | 原地等待不他动积电、阈值最近可见敌即死、威力快积、起始需可见目标/释放可换目标齐全。 | crawl-ref/source/dat/descript/spells.txt:1360；crawl-ref/source/dat/descript/zh/spells.txt:841 |
| textdb:maxwell's portable piledriver spell | maxwell's portable piledriver spell | <br>压缩包围施法者与相邻敌人（或连续一列敌人）的一片空间，随后令其骤然舒张，<br>将所有人向前推进，直至最远端的不幸生物撞上坚固物体。对该生物造成的伤害<br>与移动距离成正比。 | keep | 自己及邻连续敌空间压骤松、推进至末端撞实物、末者伤随距正比齐全。 | crawl-ref/source/dat/descript/spells.txt:1369；crawl-ref/source/dat/descript/zh/spells.txt:1815 |
| textdb:mephitic cloud spell | mephitic cloud spell | <br>召出一个脆弱的瓶子，瓶子爆炸后形成一团短暂存在的有害烟雾。<br>烟雾可能使任何没有毒抗的生物陷入混乱。<br>越坚韧、经验等级越高的生物越不容易受影响。 | keep | 易碎瓶短有害烟云、无毒抗可混乱/强经验较难齐全。 | crawl-ref/source/dat/descript/spells.txt:1377；crawl-ref/source/dat/descript/zh/spells.txt:848 |
| textdb:mercury arrow spell | mercury arrow spell | <br>召出一支由元素汞构成的箭矢，对命中的目标造成直接毒素伤害，<br>并可能短暂削弱其近战攻击。<br><br>箭矢的冲击力即使对毒素免疫者也会造成少量伤害；削弱效果还可能溅射至相邻目标，<br>并完全无视毒素抗性。 | keep | 汞箭直接毒伤及可能短弱近战、物理力毒免仍小伤、弱化可邻溅/完全不看毒抗齐全。 | crawl-ref/source/dat/descript/spells.txt:1430；crawl-ref/source/dat/descript/zh/spells.txt:895 |
| textdb:mesmerise spell | mesmerise spell | <br>尝试迷住视野内所有敌人。未能抵抗的冒险者会无法远离施法者，<br>其他生物则会直接陷入眩晕。<br><br>离开施法者视野会结束控制移动的效果。 | keep | 视野全敌迷魂、未抵抗玩家不能远离/其他直接眩晕、离视线解控制齐全。 | crawl-ref/source/dat/descript/spells.txt:1383；crawl-ref/source/dat/descript/zh/spells.txt:854 |
| textdb:metabolic englaciation spell | metabolic englaciation spell | <br>降低施法者周围所有生物的新陈代谢速率，减慢所有没有寒抗的生物。<br>冷血生物将受到更强烈的影响，而更强壮的生物会在更短的时间内被减速。 | keep | 附近全生物代谢降、无寒抗才减速、冷血更强/强者短持续齐全。 | crawl-ref/source/dat/descript/spells.txt:1391；crawl-ref/source/dat/descript/zh/spells.txt:861 |
| textdb:metal splinters spell | metal splinters spell | <br>射出一连串金属碎片。防具可以大大削弱其造成的伤害。 | keep | 金属碎片爆发/护甲强减伤齐全。 | crawl-ref/source/dat/descript/spells.txt:1398；crawl-ref/source/dat/descript/zh/spells.txt:866 |
| textdb:miasma breath spell | miasma breath spell | <br>产生一大团恶臭的瘟疫云，使接触到的活物中毒，有时还会使其减速。 | keep | 大恶臭瘴气云、活物中毒/可能减速齐全。 | crawl-ref/source/dat/descript/spells.txt:1402；crawl-ref/source/dat/descript/zh/spells.txt:870 |
| textdb:might other spell | might other spell | <br>大幅提高一个附近友方造成的近战伤害。 | keep | 附近友方近战伤显著增齐全；强壮他人是法术标题专用映射，非状态Might标签，不机械改强效。 | crawl-ref/source/dat/descript/spells.txt:1407；crawl-ref/source/dat/descript/zh/spells.txt:874 |
| textdb:might spell | might spell | <br>大幅提高施法者造成的近战伤害。 | keep | 自身近战伤显著增齐全；强壮为法术显示专门名，未承诺力量属性数值。 | crawl-ref/source/dat/descript/spells.txt:1411；crawl-ref/source/dat/descript/zh/spells.txt:878 |
| textdb:mindburst spell | mindburst spell | <br>发动心灵攻击。若突破受害者的意志力，便会以极其直白而猛烈的方式<br>“击爆其心智”，造成完全无视护甲的伤害。此法术对无心智生物无效。 | keep | 心灵攻击过意志才伤、爆心智幽默/完全忽AC、无心智免齐全。 | crawl-ref/source/dat/descript/spells.txt:1415；crawl-ref/source/dat/descript/zh/spells.txt:882 |
| textdb:minor healing spell | minor healing spell | <br>治疗施法者身体所受的少量伤害。 | keep | 自己少量伤治疗齐全。 | crawl-ref/source/dat/descript/spells.txt:1421；crawl-ref/source/dat/descript/zh/spells.txt:887 |
| textdb:momentum strike spell | momentum strike spell | <br>施法者从自己的未来移动中借来能量轰击目标。<br>在之后的一小段时间内，施法者将无法移动——不能行走、飞行、蜿蜒爬行等。<br>只有能移动的生物才能施放这个法术。 | adjust | 借未来移动能量轰敌/之后短不能行走飞行蛇行/仅可移动生物能施；无法动弹暗示全行动停且slither误滑翔，宜明确仅移动受禁。 本批已修复并复核：移动受禁被写成全身不能行动。 | crawl-ref/source/dat/descript/spells.txt:2440；crawl-ref/source/dat/descript/zh/spells.txt:1488；crawl-ref/source/spl-damage.cc:cast_momentum_strike |
| textdb:monstrous menagerie spell | monstrous menagerie spell | <br>召唤一个强大的异域生物援助施法者：蝎尾狮、蛇龙或劫掠斯芬克斯。 | adjust | 援己强异域生物/蝎尾狮林德虫劫掠斯芬克斯三选一齐全。 建议处理：adopt；lindwurm在此为林德虫、另一正文及当前实体为蛇龙；建议随怪物词根组统一，不把合理神话生物译法差异判为新机制错误。 | crawl-ref/source/dat/descript/spells.txt:1425；crawl-ref/source/dat/descript/zh/spells.txt:891 |
| textdb:mourning wail spell | mourning wail spell | <br>呼出一股被遗忘的悲伤之流，它的尾迹会留下郁积愁云，<br>但会跳过那些容易受到它影响的生物。<br>这些负能量云会迅速夺去活物的生命值，每次数额相当于其最大生命值的一小部分。 | adjust | 遗悲流/沿途负能云/跳过易受害者/活物迅速小比例maxHP扣生命；漏活物与小量。 本批已修复并复核：漏活物及小比例限定。 | crawl-ref/source/dat/descript/spells.txt:1439；crawl-ref/source/dat/descript/zh/spells.txt:903；crawl-ref/source/cloud.cc:1394；crawl-ref/source/beam.cc:3105 |
| textdb:mud breath spell | mud breath spell | <br>&lt;Mud Breath ability&gt; | keep | Mud Breath能力引用完整，已审泥球击退/泥地慢敌/偶尔攻击失手。 | crawl-ref/source/dat/descript/spells.txt:1446；crawl-ref/source/dat/descript/zh/spells.txt:1825 |
| textdb:murky legion spell | murky legion spell | <br>召唤若干浊光怨灵，它们会在一次攻击中同时散播诱变辐射和浅水，随后消失。 | keep | 浊光怨灵单次同时污染与浅水后消失齐全。 | crawl-ref/source/dat/descript/spells.txt:1450；crawl-ref/source/dat/descript/zh/spells.txt:2132 |
| textdb:mutagenic gaze spell | mutagenic gaze spell | <br>使目标体内积累诱变能量，最终可能达到足以造成有害变异或不稳定魔法能量<br>爆炸的程度。该法术需要视线，但无需直达射线。 | adjust | 目标积诱变能至有害变异/能爆、需视线不需射线齐全；正文变异能量违D-C096明确限定。 本批已修复并复核：普通能量术语未按限域统一。 | crawl-ref/source/dat/descript/spells.txt:1455；crawl-ref/source/dat/descript/zh/spells.txt:1829；docs/glossary.md:863；crawl-ref/source/mon-cast.cc:598 |
| textdb:nazja's all-purpose tempering spell | nazja's all-purpose tempering spell | <br>显现一把魔法锤，修复并暂时增强附近任意构装体的攻击能力——<br>无论是魔像、方阵甲虫，甚至舞动武器。<br>这一过程会迸发大量火花、熔渣和冲击波，对目标构装体相邻的所有敌人<br>造成可观伤害；强化消退前，不能对同一目标再次施放此法术。 | keep | 魔锤任意附近构装/修补暂增攻、魔像甲虫舞武含、火花渣震波伤目标邻敌、加成在不可重施齐全。 | crawl-ref/source/dat/descript/spells.txt:1462；crawl-ref/source/dat/descript/zh/spells.txt:1834 |
| textdb:nazja's percussive tempering spell | nazja's percussive tempering spell | <br>显现一把魔法锤，修复并暂时增强由施法者自身锻造系法术创造的任意构装体的<br>攻击能力。这一过程会迸发大量火花、熔渣和冲击波，对目标构装体相邻的<br>所有敌人造成可观伤害；强化消退前，不能对同一目标再次施放此法术。 | adjust | 限自己锻造系所造构装、修补暂增攻/邻敌副伤/同目标禁重施至结束齐全；锻造术可建议明确学派锻造系。 建议处理：adopt；Forgecraft spells可写“锻造系法术”以明确学派；锻造术在句中仍可理解。 | crawl-ref/source/dat/descript/spells.txt:1471；crawl-ref/source/dat/descript/zh/spells.txt:1841 |
| textdb:noxious breath spell | noxious breath spell | <br>&lt;Noxious Breath ability&gt; | keep | Noxious Breath能力引用完整，已核无毒抗才可能混乱与等级范围持续缩放。 | crawl-ref/source/dat/descript/spells.txt:1480；crawl-ref/source/dat/descript/zh/spells.txt:1847 |
| textdb:noxious cloud spell | noxious cloud spell | <br>产生大量有毒烟雾，这可能会引起混乱。 | keep | 大有害烟云可能混乱齐全；云为烟雾自然同义。 | crawl-ref/source/dat/descript/spells.txt:1484；crawl-ref/source/dat/descript/zh/spells.txt:919 |
| textdb:nullifying breath spell | nullifying breath spell | <br>&lt;Nullifying Breath ability&gt; | keep | Nullifying Breath能力引用完整，已核每命中驱散/施法干扰/自身无害。 | crawl-ref/source/dat/descript/spells.txt:1488；crawl-ref/source/dat/descript/zh/spells.txt:1851 |
| textdb:oblivion howl spell | oblivion howl spell | <br>发放出刺耳的嚎叫，在受害者的脑海中回荡。<br>当那些回声还在徘徊时，噩梦般的生物会听到并追踪它们的来源。<br>每个生物只能使用此法术一次。 | adjust | 刺耳心灵回声引噩梦生物追源、每个施法生物仅能用一次；特定生物一次误解given creature。 本批已修复并复核：given creature误作特殊生物限定。 | crawl-ref/source/dat/descript/spells.txt:604；crawl-ref/source/dat/descript/zh/spells.txt:418；crawl-ref/source/mon-cast.cc:_oblivion_howl |
| textdb:olgreb's toxic radiance spell | olgreb's toxic radiance spell | <br>施法者放出毒能量，在法术持续期间不断毒害视线内的所有生物。 | keep | 自己毒光环、法术持续时视野所有生物不断中毒齐全。 | crawl-ref/source/dat/descript/spells.txt:1492；crawl-ref/source/dat/descript/zh/spells.txt:923 |
| textdb:orb of destruction spell | orb of destruction spell | <br>生成一个毁灭性的纯魔力球。比起其他的发射物，这种能量球的飞行速度相对较慢。<br>能量球会自动追踪目标，但因为它们的惯性太强，<br>因此特别敏捷的对手可能会躲开它们。<br>球体需要一段时间来稳定，新生的能量球无法发挥出全部的伤害潜力。<br><br>地牢的居民可以在它撞到目标前一直维持着球体，但你在施放时，<br>球体在离开你的视线时就会消散。 | keep | 纯毁灭慢追踪球/惯性可躲/新生弱、地牢居民可维至撞/玩家离视线散齐全。 | crawl-ref/source/dat/descript/spells.txt:1497；crawl-ref/source/dat/descript/zh/spells.txt:927 |
| textdb:orb of electricity spell | orb of electricity spell | <br>掷出噼啪作响的电能量球，在撞击时产生巨大爆炸。<br>造成的伤害无视目标一半的护甲。 | adjust | 电球撞击大爆齐全；半护甲误成半伤害无视护甲。 本批已修复并复核：半护甲误为半伤害。 | crawl-ref/source/dat/descript/spells.txt:1509；crawl-ref/source/dat/descript/zh/spells.txt:937；crawl-ref/source/beam.cc:4608 |
| textdb:ostracise spell | ostracise spell | <br>使目标暂时与神祇隔绝，降低其在所信奉神祇眼中的有效虔诚值，<br>并阻止使用依赖该虔诚值的神圣能力。重复受影响会进一步降低有效虔诚，<br>但绝不会直接导致逐出教派。目标获得经验时效果会逐渐消退，<br>最终恢复原有全部虔诚带来的能力。 | keep | 目标有效虔诚暂降/所需神能禁、叠降不直接逐出、经验逐恢复全部旧虔诚齐全。 | crawl-ref/source/dat/descript/spells.txt:1514；crawl-ref/source/dat/descript/zh/spells.txt:1855 |
| textdb:ozocubu's armour spell | ozocubu's armour spell | <br>在施法者的身体上覆一层厚的冰，只要施法者留在原地，就能获得大量护甲值加成。<br>如果施法者移动到新位置，冰会破裂、脱落。<br>该法术对重甲效果变弱，施法者护甲的负重等级越高，加成越低。 | adjust | 厚冰当前地点加AC/移位掉、护甲越重越弱齐全；负担等级违现行负重等级。 本批已修复并复核：参数名旧译。 | crawl-ref/source/dat/descript/spells.txt:1525；crawl-ref/source/dat/descript/zh/spells.txt:942；docs/glossary.md:encumbrance rating；crawl-ref/source/spl-selfench.cc:ice_armour |
| textdb:ozocubu's refrigeration spell | ozocubu's refrigeration spell | <br>使空气变得非常寒冷，冻结视线中的所有其他生物。<br>这对紧密聚在一起的生物效果较差——<br>与盟友相邻的生物会得到部分遮护，受到的寒冷伤害较小。 | adjust | 视野其他生物冷伤、拥抱相邻盟友才部分减伤；中文改为相邻其他任意生物，改了阵营条件。 本批已修复并复核：减伤阵营条件被移除。 | crawl-ref/source/dat/descript/spells.txt:1533；crawl-ref/source/dat/descript/zh/spells.txt:948；crawl-ref/source/spl-damage.cc:625 |
| textdb:pain spell | pain spell | <br>让一个活物遭受极其痛苦的伤害。 | keep | 一个活物极痛伤害齐全。 | crawl-ref/source/dat/descript/spells.txt:1540；crawl-ref/source/dat/descript/zh/spells.txt:954 |
| textdb:paralyse spell | paralyse spell | <br>让一个生物短期无法做出任何行动。 | keep | 生物短期一切行动禁齐全。 | crawl-ref/source/dat/descript/spells.txt:1544；crawl-ref/source/dat/descript/zh/spells.txt:958 |
| textdb:paralysis gaze spell | paralysis gaze spell | <br>不可抵抗地使一个生物短时间无法采取任何行动。该凝视需要多次充能，<br>但只需视线，无需直达射线。 | keep | 不可抗拒短禁全部行动、多次充能/不需射线齐全。 | crawl-ref/source/dat/descript/spells.txt:1548；crawl-ref/source/dat/descript/zh/spells.txt:962 |
| textdb:passage of golubria spell | passage of golubria spell | <br>这道法术开启两扇传送门（其中一扇总是出现在施法者附近）；<br>任何走进传送门的生物都会被随机传送到另一个打开着的传送门。<br>同一时间可以打开的传送门数量并没有限制。<br>但是，传送门在打开后会短时间内关闭，或是一旦进入就立刻关闭。 | keep | 两门其中一近己、进入随机到其他开门/数量不限/短时或进入即关齐全。 | crawl-ref/source/dat/descript/spells.txt:1553；crawl-ref/source/dat/descript/zh/spells.txt:967 |
| textdb:passwall spell | passwall spell | <br>施法者可以穿过相邻的岩墙行进一小段距离，然后重新出现在另一边。<br>施展此法术所需时间格外漫长；在此期间施法者无法行动，<br>但也会因与岩石调谐而获得更高护甲。 | keep | 邻岩短穿到另侧、异常长施法不能行动/同岩调谐加AC齐全。 | crawl-ref/source/dat/descript/spells.txt:1560；crawl-ref/source/dat/descript/zh/spells.txt:974 |
| textdb:permafrost eruption spell | permafrost eruption spell | <br>唤醒潜藏于大地深处的古老严寒，使其猛烈喷涌而出。喷发的力量震落顶上的岩石，<br>以无法躲避的力量砸中目标。寒意本身虽转瞬即逝，却极其刺骨；<br>它会完全无视护甲，冻结目标及其邻近生物。<br><br>法术总会尝试轰击视野内敌人最密集的位置，且绝不会在施法者身旁爆发。 | keep | 古寒猛喷/天顶岩砸必中、冷忽AC伤目标邻人、总选敌最密/不爆自己旁齐全。 | crawl-ref/source/dat/descript/spells.txt:1567；crawl-ref/source/dat/descript/zh/spells.txt:1862 |
| textdb:petrify spell | petrify spell | <br>石化一个目标生物，以及链中至多另外两个敌人。<br>那些意志力不足以抵抗该法术的生物会暂时变慢，然后变成石头。在他们恢复肉身前，<br>他们无法行动，但受到的伤害会减半。该法术对次级目标的威力会减弱。 | adjust | 主目标及链最多另两敌、未抗意志先短慢后石化/不能动但半伤/次级威力弱齐全；中文把额外foes改为生物。 本批已修复并复核：链式次级目标敌方限制被删。 | crawl-ref/source/dat/descript/spells.txt:1577；crawl-ref/source/dat/descript/zh/spells.txt:980；crawl-ref/source/spl-monench.cc:cast_petrify |
| textdb:petrifying cloud spell | petrifying cloud spell | <br>呼出一股钙化尘雾。任何受其影响超过片刻的生物都会被石化。 | keep | 钙化雾受影响超过片刻才石化齐全。 | crawl-ref/source/dat/descript/spells.txt:1584；crawl-ref/source/dat/descript/zh/spells.txt:986 |
| textdb:phantom blitz spell | phantom blitz spell | <br>编织出施法者的幻影复制体，并将其猛烈射出。这些幻影拥有与施法者相同的<br>武艺和神秘力量；临时组成的幻影夜行队足以压倒施法者的受害者。 | keep | 强力射自身幻象/同武艺法术/即兴幻影夜行可压敌齐全。 | crawl-ref/source/dat/descript/spells.txt:1589；crawl-ref/source/dat/descript/zh/spells.txt:1870 |
| textdb:phantom mirror spell | phantom mirror spell | <br>创造一个怪物的幻影复制体。复制体会较为脆弱，但除此之外几乎与原体无异。 | keep | 生物幻镜复制/较脆但余几乎同原体齐全。 | crawl-ref/source/dat/descript/spells.txt:1595；crawl-ref/source/dat/descript/zh/spells.txt:990 |
| textdb:phase shift spell | phase shift spell | <br>使施法者的身体略微偏离正常空间的相位，让其确切位置变得模糊不清。<br>没有超自然敏锐视觉的攻击者会更难击中施法者，<br>也无法判断其受伤的程度。 | keep | 自身相位偏离模糊位置/无超视者难中且不见伤势齐全；同title多个定义不凭重名判错。 | crawl-ref/source/dat/descript/spells.txt:1600；crawl-ref/source/dat/descript/zh/spells.txt:2136 |
| textdb:planar overlay spell | planar overlay spell | <br>将相邻现实的一部分叠加到此处，使随机的本地怪物出现在本层其他位置。<br>首次使用时会同时到来多个怪物；之后则会缓慢而稳定地出现。<br><br>经过相当长时间后，这些怪物甚至可能出现在玩家附近。 | keep | 邻现实叠/随机本地怪在同层其他处、首批多/后慢稳/很久后可近玩家齐全。 | crawl-ref/source/dat/descript/spells.txt:1607；crawl-ref/source/dat/descript/zh/spells.txt:1875 |
| textdb:plane rend spell | plane rend spell | <br>从史莱姆之坑、精灵殿堂、宝库、墓室、远古坟冢或佐特领域之一<br>召唤强大威胁；每次施法选择的分支都可能不同。 | keep | 六分支之一强威胁/每施随机分支齐全；分支名另依世界名组，不自立称谓。 建议处理：retain；分支译名可随世界实体组统一；当前近义名不作为此法术的独立机制缺陷。 | crawl-ref/source/dat/descript/spells.txt:1617；crawl-ref/source/dat/descript/zh/spells.txt:994 |
| textdb:plasma beam spell | plasma beam spell | <br>向施法者最远的可见敌人之一发射一道可穿透目标的等离子束。<br>电离束会无视防御者一半的护甲，随后沿同一路径射出一道火焰束。 | keep | 最远可见敌之一/穿等离子半护甲/随后同路火束齐全；此条正确译一半护甲，与其他电术形成校准。 | crawl-ref/source/dat/descript/spells.txt:1623；crawl-ref/source/dat/descript/zh/spells.txt:999 |
| textdb:platinum paragon spell | platinum paragon spell | <br>构建一名闪亮的金属勇士，其战力足以媲美最伟大的在世战士。<br>它抵抗一切形式的魔法，并使用施法者所选任意神器近战武器的完美复制品。<br><br>首次部署时，它会在周围产生伤害性冲击波，并在攻击敌人时缓慢积蓄能量。<br>能量充足后，可再次施法使典范过载，在广大区域内发动一连串伤害提高的攻击，<br>但会在过程中摧毁典范。<br><br>由于它与创造者维持魔法联系，创造者每次攻击时，它都会额外发动攻击。<br>双方距离足够近时，它有时甚至会格挡指向创造者的攻击。 | adjust | 额外攻击仅要求玩家看见典范且它有可打目标；&lt;=2距离仅限制替玩家招架。中文把足够近提前到整句，错误扩大限制。其余全魔抗/神器复制/落地冲击/攻击充能/过载广域增伤自毁均保留。 本批已修复并复核：距离条件错误套到额外攻击。 | crawl-ref/source/dat/descript/spells.txt:1629；crawl-ref/source/dat/descript/zh/spells.txt:1882；crawl-ref/source/spl-summoning.cc:4139；crawl-ref/source/spl-summoning.cc:4202 |
| textdb:poison arrow spell | poison arrow spell | <br>射出一支裹着剧毒的魔法箭。即使具有毒素抗性的目标也会中毒；<br>该箭造成的少量直接伤害还会无视毒素抗性。 | keep | 剧毒箭、毒抗者仍中毒/少量直接伤忽毒抗齐全。 | crawl-ref/source/dat/descript/spells.txt:1645；crawl-ref/source/dat/descript/zh/spells.txt:1004 |
| textdb:poisonous cloud spell | poisonous cloud spell | <br>生成一大团致命的毒云。 | keep | 大致命毒气云齐全。 | crawl-ref/source/dat/descript/spells.txt:1651；crawl-ref/source/dat/descript/zh/spells.txt:1009 |
| textdb:poisonous vapours spell | poisonous vapours spell | <br>将目标周围的少量空气转化为有毒气体，使吸入者中毒。<br>受影响的气体只存在于施法当回合，且无法影响任何具有毒素抗性的生物。 | keep | 少量空气转毒/吸入中毒、仅施法当回合/任何毒抗者免齐全。 | crawl-ref/source/dat/descript/spells.txt:1655；crawl-ref/source/dat/descript/zh/spells.txt:1894 |
| textdb:polar vortex spell | polar vortex spell | <br>将施法者周围的空气变成冰冻的旋涡，对卷入其中的所有生物造成巨大伤害，<br>寒冷抗性最多只能减免其中一半。受影响的生物还会被卷到空中并抛来抛去。<br>只有风暴眼是安全的，并且它会跟随施法者。<br>在封闭区域，该法术的效果会大大降低。旋涡消散后，短时间内无法再次施放。 | keep | 冰旋巨大伤、寒抗只减一半/卷空抛掷、随己风眼唯安全、闭区削弱、完后短冷齐全。 | crawl-ref/source/dat/descript/spells.txt:1663；crawl-ref/source/dat/descript/zh/spells.txt:1013 |
| textdb:polymorph spell | polymorph spell | <br>随机改变一个生物的外形。该法术对会变换形态的生物尤其有效。 | keep | 随机改生物外形、对变形者特效齐全。 | crawl-ref/source/dat/descript/spells.txt:1672；crawl-ref/source/dat/descript/zh/spells.txt:1020 |
| textdb:porkalator spell | porkalator spell | <br>将目标变为猪。目标的移动变得迅捷，但无法施法。施法者一死，变形就会结束。 | keep | 目标变猪/快移不能施法/施法者死解齐全。 | crawl-ref/source/dat/descript/spells.txt:1677；crawl-ref/source/dat/descript/zh/spells.txt:1024 |
| textdb:portal projectile spell | portal projectile spell | <br>向一个目标敌人传送一个投射的弹药。 | keep | 射出或扔出的弹药传至敌齐全；投射上位词不构成删除投掷机制。 | crawl-ref/source/dat/descript/spells.txt:1682；crawl-ref/source/dat/descript/zh/spells.txt:1028 |
| textdb:prayer of brilliance spell | prayer of brilliance spell | <br>施法者为附近的友方法师赋予魔力，让他们能够更有力、更频繁地施法。 | keep | 附近己方巫师更强且更频繁施法齐全。 | crawl-ref/source/dat/descript/spells.txt:1686；crawl-ref/source/dat/descript/zh/spells.txt:67 |
| textdb:primal wave spell | primal wave spell | <br>召出一股激流，可能将目标击退，并在短时间内形成一滩浅水。 | keep | 水流可能击退、短浅水池齐全。 | crawl-ref/source/dat/descript/spells.txt:1691；crawl-ref/source/dat/descript/zh/spells.txt:1032 |
| textdb:pyre arrow spell | pyre arrow spell | <br>向目标生物发射一团会附着其身的液态火焰，在数个回合内造成无视护甲的火焰伤害。<br>目标移动时能更快扑灭火焰。<br><br>若目标没有实体，液态火焰便无法附着。 | keep | 液火黏目标、多回忽AC火伤、移动快灭/无实体不黏齐全。 | crawl-ref/source/dat/descript/spells.txt:1696；crawl-ref/source/dat/descript/zh/spells.txt:1036 |
| textdb:pyroclastic surge spell | pyroclastic surge spell | <br>从熔岩中引出灼热的火焰。任何站在熔岩旁边或上方的施法者的敌人都会被灼烧。 | keep | 熔岩取火、熔岩邻及上方敌受焚齐全。 | crawl-ref/source/dat/descript/spells.txt:1704；crawl-ref/source/dat/descript/zh/spells.txt:1043 |
| textdb:pyrrhic recollection spell | pyrrhic recollection spell | <br>点燃环绕“无名氏”的光环中的一段记忆，暂时赋予其一个强力法术的知识并治疗伤势。<br>这股力量十分短暂，承受任何显著伤害后便会熄灭；<br>但只要还有其他记忆残留，无名氏就无法获得永久安息。 | adjust | 无名者环记忆点燃/暂强法术知识与治疗/显著伤熄/余记忆尚有则无名者不永久死；它们代词可误指记忆，宜重述无名者。 本批已修复并复核：专名及代词对象不清。 | crawl-ref/source/dat/descript/spells.txt:1709；crawl-ref/source/dat/descript/zh/spells.txt:1899；docs/glossary.md:Nobody title；docs/decisions.md:D-C-094 |
| textdb:quicksilver bolt spell | quicksilver bolt spell | <br>向目标生物发射一道可穿透目标的驱散能量之箭，可能移除其部分魔法效果。 | keep | 穿透驱散能、可能删部分魔法齐全。 | crawl-ref/source/dat/descript/spells.txt:1718；crawl-ref/source/dat/descript/zh/spells.txt:1821 |
| textdb:ravenous swarm spell | ravenous swarm spell | <br>释放一股吸血蝙蝠洪流，填满目标周围的空气。<br><br>这些吸血生物会贪婪啃咬一切非亡灵目标；其啃咬最终甚至会使受害者入睡，<br>令其成为轻易捕获的猎物。 | keep | 目标周围蝙蝠洪/啃一切非亡灵/最终可睡易猎齐全。 | crawl-ref/source/dat/descript/spells.txt:1723；crawl-ref/source/dat/descript/zh/spells.txt:1905 |
| textdb:rebounding blaze spell | rebounding blaze spell | <br>发射一道充满能量的穿透火焰束，可从墙壁弹回并二次命中目标。 | keep | 穿透能火/反墙两次命中齐全。 | crawl-ref/source/dat/descript/spells.txt:1731；crawl-ref/source/dat/descript/zh/spells.txt:1912 |
| textdb:rebounding chill spell | rebounding chill spell | <br>发射一道穿透性的强力寒流，能从墙壁反弹并命中目标两次。 | keep | 穿透强寒流/反墙两击齐全。 | crawl-ref/source/dat/descript/spells.txt:1736；crawl-ref/source/dat/descript/zh/spells.txt:1916 |
| textdb:regenerate other spell | regenerate other spell | <br>使另一个生物在短时间内快速再生。恢复量与该生物的最大生命值成正比。 | keep | 另一生物短暂快速再生、按其maxHP正比齐全。 | crawl-ref/source/dat/descript/spells.txt:1741；crawl-ref/source/dat/descript/zh/spells.txt:1920 |
| textdb:rending blade spell | rending blade spell | <br>将施法者的魔法能量凝聚成一柄猛烈噼啪作响的利刃。法术生效期间，<br>每当施法者的近战攻击命中，这柄利刃便会在附近敌人之间来回撕开一条路径，<br>造成无法抵抗的伤害。<br><br>施放此法术会暂时抽走施法者所有剩余法力以构成利刃；利刃消失时，<br>这些能量会立刻返还。以此方式封存的每一点法力都会略微提高利刃的伤害。 | keep | 魔力裂刃、己每近战中则穿旁敌不可抗伤、暂抽全部剩MP/消失立即返、每点增伤齐全。 | crawl-ref/source/dat/descript/spells.txt:1746；crawl-ref/source/dat/descript/zh/spells.txt:1924 |
| textdb:resonance strike spell | resonance strike spell | <br>召唤一股来自大地的力量，攻击施法者视线内的敌人。<br>法术将附近的造物串联起来，每有一个造物在目标附近就会增强力量。 | keep | 地力打可见敌、附近构装级联/每邻目标构装增威齐全。 | crawl-ref/source/dat/descript/spells.txt:1758；crawl-ref/source/dat/descript/zh/spells.txt:1047 |
| textdb:rimeblight spell | rimeblight spell | <br>使一个生物（及其附近最多两个其他生物）感染魔法瘟疫，从内向外缓慢冻结。<br>受害者每回合受到无视护甲的寒冷伤害；随着疾病发展，水晶冰片会猛烈地从体内迸出，<br>伤害附近敌人。受害者最终倒下时，瘟疫可能传播给周围生物。<br><br>对活物、神圣或恶魔生物而言，此病尤其凶猛，会以宿主受苦时释放的死灵能量为食。<br>当宿主接近死亡时，疾病会迅速加剧，吞噬其身体最后的残余，<br>只留下一根扭曲的冥界冰柱。 | keep | 主及最多两邻魔疫/从内冻、每回忽AC冷伤/发展冰片邻敌/死可传播、活物神圣魔更猛/苦供死灵/濒死快吞遗冥冰齐全。 | crawl-ref/source/dat/descript/spells.txt:1764；crawl-ref/source/dat/descript/zh/spells.txt:1933 |
| textdb:roll spell | roll spell | <br>滚成一个球，给予巨砾甲虫巨大的速度以及双倍的近战攻击力。<br>只有在与敌人有一定距离时才能进行翻滚，<br>并且甲虫在进行滚动攻击后总会展开身体。 | keep | 滚球甲虫巨速/双近战伤、需敌距、尝试攻击后必展开齐全。 | crawl-ref/source/dat/descript/spells.txt:1778；crawl-ref/source/dat/descript/zh/spells.txt:1052 |
| textdb:sandblast spell | sandblast spell | <br>将一些小碎石以极高的速度射向目标。因为从周围环境中获得岩石的速度很慢，<br>使得这个法术的施法时间多出大多数法术的一半。防具可以大大削弱其造成的伤害。 | keep | 快碎岩、环境取岩慢所以施法1.5倍、AC大减齐全。 | crawl-ref/source/dat/descript/spells.txt:1784；crawl-ref/source/dat/descript/zh/spells.txt:1058 |
| textdb:sap magic spell | sap magic spell | <br>腐化目标生物的施法能力。受此状态影响时施放法术，<br>会使目标暂时失去魔法，短时间内无法继续施法。 | keep | 腐化施法、仍施一法后短禁后续齐全。 | crawl-ref/source/dat/descript/spells.txt:1790；crawl-ref/source/dat/descript/zh/spells.txt:1063 |
| textdb:scorch spell | scorch spell | <br>灼烧一个随机的可见敌人。受此伤害的敌人会在短时间内失去火焰抗性。 | keep | 随机可见敌灼烧、受伤者短时间火抗烧掉齐全。 | crawl-ref/source/dat/descript/spells.txt:1796；crawl-ref/source/dat/descript/zh/spells.txt:1068 |
| textdb:sculpt simulacrum spell | sculpt simulacrum spell | <br>生成以相邻的活物、恶魔或神圣生物为原型的冰制拟像。<br>这些脆弱的替身将在短时间内成型，最终获得移动和攻击施法者敌人的能力。<br><br>善神不喜欢这个法术，因为它能把血和灵液变成不自然的赝品。<br><br>你最多可以同时维系 5 个拟像。 | keep | 相邻活/魔/圣拟像、短成形再动攻、血灵液忤善神、上限5齐全。 | crawl-ref/source/dat/descript/spells.txt:1801；crawl-ref/source/dat/descript/zh/spells.txt:1072 |
| textdb:seal doors spell | seal doors spell | <br>封印附近的门和楼梯，阻止不属于施法者盟友的生物通过。 | keep | 附近门与楼梯封、非施法者盟友不可通齐全。 | crawl-ref/source/dat/descript/spells.txt:1812；crawl-ref/source/dat/descript/zh/spells.txt:1081 |
| textdb:searing breath spell | searing breath spell | <br>向一个目标生物喷吐火焰气流，在终点留下一团火焰云。 | keep | 目标喷火、终点留火云齐全。 | crawl-ref/source/dat/descript/spells.txt:1824；crawl-ref/source/dat/descript/zh/spells.txt:1091 |
| textdb:searing ray spell | searing ray spell | <br>从施法者的手中射出一束持续的穿透性奥术能量射线。<br>如果施法者保持专注，并为法术提供魔力（通过原地等待而不采取任何其他行动），<br>射线将会追踪施法者的目标。 | keep | 手中持续穿透奥术线、原地等/不他动供MP则跟踪移动目标齐全。 | crawl-ref/source/dat/descript/spells.txt:1817；crawl-ref/source/dat/descript/zh/spells.txt:1085 |
| textdb:seismic stomp spell | seismic stomp spell | <br>重踏地面，发出猛烈震波，震裂多名附近敌人脚下的地面。<br>飞行生物受到的伤害大幅降低；地面生物则可能完全失去平衡，<br>在崎岖地面上重新站稳时延后下一次行动。 | keep | 重踏裂多近敌地、飞者大减伤/地者可能失足延下次行动齐全。 | crawl-ref/source/dat/descript/spells.txt:1829；crawl-ref/source/dat/descript/zh/spells.txt:1943 |
| textdb:sentinel's mark spell | sentinel's mark spell | <br>在目标生物身上施加强力信标，将被标记者的存在和位置告知同层所有生物。 | keep | 强信标/同层所有生物知存在位置齐全。 | crawl-ref/source/dat/descript/spells.txt:1837；crawl-ref/source/dat/descript/zh/spells.txt:109 |
| textdb:seracfall spell | seracfall spell | <br>猛烈地将附近的一个拟像崩成大冰块，它会在轰然倒塌时爆炸。<br>由于强大的冲击和切削，它造成的一半伤害无视寒冰抗性。 | keep | 附近拟像变冰团撞爆/寒抗仍受部分伤相符。中文明确一半虽比EN精确，但实际SPELL_SERACFALL→ZAP_ICEBLAST→BEAM_ICE，fight.cc:800可抗比例50%，故数字正确；未误信beam.cc旧40/60注释。 | crawl-ref/source/dat/descript/spells.txt:1842；crawl-ref/source/dat/descript/zh/spells.txt:1095；crawl-ref/source/spl-zap.cc:155；crawl-ref/source/fight.cc:800 |
| textdb:shadow beam spell | shadow beam spell | <br>发射一道穿透性的暗影能量束。 | keep | 穿透暗影光束齐全。 | crawl-ref/source/dat/descript/spells.txt:1852；crawl-ref/source/dat/descript/zh/spells.txt:1949 |
| textdb:shadow bind spell | shadow bind spell | <br>将附近随机选中的数名敌人钉在各自的影子上，使其短时间无法移动。<br>法术威力越高，同时影响的敌人越多。 | keep | 近随机数敌钉自身影子/短禁移动/威力多目标齐全。 | crawl-ref/source/dat/descript/spells.txt:1856；crawl-ref/source/dat/descript/zh/spells.txt:1953 |
| textdb:shadow creatures spell | shadow creatures spell | <br>创造施法者当前地域原生生物的复制品，以暗影和深渊物质的丝线将其编织成形。 | keep | 当前地点原生生物复制/暗影深渊丝线编织齐全。 | crawl-ref/source/dat/descript/spells.txt:1861；crawl-ref/source/dat/descript/zh/spells.txt:1100 |
| textdb:shadow draining spell | shadow draining spell | <br>强行从附近所有敌人的影子中夺取一缕，造成完全无视目标护甲的伤害。 | keep | 附近所有敌影夺一缕、伤完全忽AC齐全。 | crawl-ref/source/dat/descript/spells.txt:1866；crawl-ref/source/dat/descript/zh/spells.txt:1958 |
| textdb:shadow prism spell | shadow prism spell | <br>创造一个暗影棱镜，短暂延迟后会释放猛烈的暗影爆炸。<br>若棱镜提前被摧毁，爆炸威力会大幅减弱。 | keep | 暗影棱镜短延爆、提前毁威大弱齐全。 | crawl-ref/source/dat/descript/spells.txt:1871；crawl-ref/source/dat/descript/zh/spells.txt:1962 |
| textdb:shadow puppet spell | shadow puppet spell | <br>召唤一个活影仆从骚扰并缠住施法者的敌人。<br>它的攻击强度随法术威力直接提高。 | keep | 活影仆骚扰/缠绕敌、攻击强度直接依威力齐全；缠住可明确挤压以贴constrict。 | crawl-ref/source/dat/descript/spells.txt:1876；crawl-ref/source/dat/descript/zh/spells.txt:1967 |
| textdb:shadow shard spell | shadow shard spell | <br>向单个敌人射出一枚硬化的暗影碎片。 | keep | 单敌硬化影碎片齐全。 | crawl-ref/source/dat/descript/spells.txt:1881；crawl-ref/source/dat/descript/zh/spells.txt:1104 |
| textdb:shadow shot spell | shadow shot spell | <br>向单个敌人射出一颗小型硬化暗影弹。 | keep | 单敌小硬化影弹齐全。 | crawl-ref/source/dat/descript/spells.txt:1885；crawl-ref/source/dat/descript/zh/spells.txt:1972 |
| textdb:shadow tempest spell | shadow tempest spell | <br>向可见敌人中的至多一半降下暗影闪电，造成无法抵抗的伤害。 | keep | 所有可见敌最多一半受不可抗暗雷齐全。 | crawl-ref/source/dat/descript/spells.txt:1889；crawl-ref/source/dat/descript/zh/spells.txt:1976 |
| textdb:shadow torpor spell | shadow torpor spell | <br>汲取一列敌人的活力，使其短时间减速。法术威力越高，效果持续越久，<br>但更强大的生物可能更快摆脱这种麻木。 | keep | 一列敌短慢/威力延时/强者更快摆脱齐全。 | crawl-ref/source/dat/descript/spells.txt:1894；crawl-ref/source/dat/descript/zh/spells.txt:1980 |
| textdb:shadow turret spell | shadow turret spell | <br>用凝固的暗影形成一座固定炮塔，反复向施法者的敌人开火。 | keep | 固定影炮反复向敌射击齐全。 | crawl-ref/source/dat/descript/spells.txt:1900；crawl-ref/source/dat/descript/zh/spells.txt:1985 |
| textdb:shadowball spell | shadowball spell | <br>掷出一颗由闪烁暗影构成的球体，在小范围内爆炸。 | adjust | 闪烁暗影球、小范围爆炸；中文漏闪烁与小范围且换成击中时爆。 本批已修复并复核：漏小范围与闪烁修饰。 | crawl-ref/source/dat/descript/spells.txt:1848；crawl-ref/source/dat/descript/zh/spells.txt:1989；crawl-ref/source/spl-zap.cc:SPELL_SHADOW_BALL |
| textdb:shatter spell | shatter spell | <br>这道法术让施法者身边爆发出一道巨大的冲击力，对附近所有生物造成严重伤害。<br>它对那些由冰、骨或任何类似墙壁的物质（例如岩石、金属或水晶）构成的生物<br>尤为有效，对被石化的生物也同样如此。它对飞行、凝胶状和非实体生物的效果较差。<br>它可能会摧毁周围墙壁。 | adjust | 周围大震波重伤全生物、冰骨墙材/石化特效、飞凝胶虚体弱效/可毁墙；漏岩石金属水晶三例且石化那句有病句。 本批已修复并复核：漏材质例子且石化句病句。 | crawl-ref/source/dat/descript/spells.txt:1905；crawl-ref/source/dat/descript/zh/spells.txt:1108；crawl-ref/source/spl-damage.cc:shatter |
| textdb:sheza's dance spell | sheza's dance spell | <br>从四面八方召唤武器——一把新锻造的匕首，一把在腐朽的坟墓中生锈已久的剑，<br>一把仍在蒸腾着受害者热血的斧头——激活它们并派它们出击。 | keep | 四方武器/新匕首锈剑热血斧三意象、活化出击齐全。 | crawl-ref/source/dat/descript/spells.txt:1914；crawl-ref/source/dat/descript/zh/spells.txt:1115 |
| textdb:shock spell | shock spell | <br>发射一道会反弹的电击束；造成的伤害无视目标一半的护甲。 | adjust | 反弹电束齐全；半护甲误为半伤忽护甲。 本批已修复并复核：半护甲误为半伤害。 | crawl-ref/source/dat/descript/spells.txt:1920；crawl-ref/source/dat/descript/zh/spells.txt:1120；crawl-ref/source/beam.cc:4608 |
| textdb:shred spell | shred spell | <br>原地旋转，以锯齿状躯体重创相邻敌人。 | keep | 原地旋/锯齿身/邻敌重伤齐全。 | crawl-ref/source/dat/descript/spells.txt:1924；crawl-ref/source/dat/descript/zh/spells.txt:1993 |
| textdb:sigil of binding spell | sigil of binding spell | <br>在附近创造两个印记。任何经过它们的生物都会被束缚，仍可正常行动和闪避，<br>但无法移动离开。除施法者之外，被束缚的生物在效果消失时，移动速度会回升，<br>暂时变得迅捷。从任何来源获得的迅捷效果都能免疫束缚。<br><br>一次只能维持一组印记，而且如果它们离开你的视线，就会提前失效。 | keep | 两个近印/经过定身但可行动闪避、非己解后迅捷/任意迅捷免束缚、一组/离视线提前失效齐全。 | crawl-ref/source/dat/descript/spells.txt:1929；crawl-ref/source/dat/descript/zh/spells.txt:1124 |
| textdb:sign of ruin spell | sign of ruin spell | <br>为一群敌人施加毁灭印记，使其躯体不可避免地衰败崩解。<br>带有印记者每次受到近战伤害时都会陷入严重衰竭，<br>并可能额外陷入缓慢、虚弱或失明之一。 | keep | 一组敌印记衰亡、每次近战伤重衰竭/可能慢弱盲三额外之一齐全；能力组亦真核本正文，非依旧keep。 | crawl-ref/source/dat/descript/spells.txt:1939；crawl-ref/source/dat/descript/zh/spells.txt:1997 |
| textdb:silence spell | silence spell | <br>消除施法者附近的所有声音。<br>这使得无法在施法者附近阅读卷轴、施放法术、祈求神力或喊叫。<br><br>某些怪物具有与生俱来的魔法或特殊能力，即使被沉默也能使用。<br><br>起始的生效范围的半径取决于法术威力，然后会缩小，最后只覆盖施法者，<br>直到完全失效。 | keep | 附近无声/卷轴法术神能喊叫禁、某怪天生特殊免、威力初半径渐缩最后己至过期齐全。 | crawl-ref/source/dat/descript/spells.txt:1946；crawl-ref/source/dat/descript/zh/spells.txt:1132 |
| textdb:siphon essence spell | siphon essence spell | <br>折磨附近的活物敌人，使其生命值减半；此伤害绝不会直接致命。<br>造成的痛苦随后会治疗使用者。 | keep | 近活物敌HP半/永不直接杀/痛苦治疗己齐全。 | crawl-ref/source/dat/descript/spells.txt:1958；crawl-ref/source/dat/descript/zh/spells.txt:2003 |
| textdb:siren song spell | siren song spell | <br>唱出萦绕心头的歌，迷住附近听众。未能抵抗的冒险者会无法远离歌者，<br>其他生物则会直接陷入眩晕。<br><br>离开施法者视野会结束控制移动的效果。 | keep | 听众迷魂、未抗玩家不能远离/其他眩晕、离施法者视线止控制齐全。 | crawl-ref/source/dat/descript/spells.txt:1963；crawl-ref/source/dat/descript/zh/spells.txt:1142 |
| textdb:sirocco spell | sirocco spell | <br>释放一阵灼热的风，烧伤至多3个相邻生物并将其向后吹退。<br>可惜，留在这些生物周围盘旋的无常气流，也会在随后的数回合内加快其移动。<br><br>施放后数回合内无法再次施放此法术，移动还会延缓其恢复。 | keep | 至多3邻生物火伤吹退/后数回快移副效、数回禁再施/移动延充能齐全。 | crawl-ref/source/dat/descript/spells.txt:2002；crawl-ref/source/dat/descript/zh/spells.txt:2142 |
| textdb:sleep spell | sleep spell | <br>使一个目标生物沉睡。对目标造成伤害通常会将其唤醒，<br>如果发出巨大响声，也可能会这样。 | adjust | 目标睡、通常受伤醒/大声可能醒；中文去掉typically变成受伤必醒。 本批已修复并复核：概率限定变成保证。 | crawl-ref/source/dat/descript/spells.txt:1971；crawl-ref/source/dat/descript/zh/spells.txt:1149；crawl-ref/source/dat/descript/spells.txt:1973 |
| textdb:sleetstrike spell | sleetstrike spell | <br>使目标周围空气扭曲成严寒气旋，以冰封住受害者并短暂减慢移动。<br>目标周围越空旷，受到的伤害越高；造成的伤害有一半无视寒冷抗性。 | keep | 目标周围冷气旋/短冰封慢移、空旷增伤/半伤忽寒抗齐全。 | crawl-ref/source/dat/descript/spells.txt:1976；crawl-ref/source/dat/descript/zh/spells.txt:2008 |
| textdb:slow spell | slow spell | <br>减慢一个生物的行动。 | keep | 生物行动变慢齐全。 | crawl-ref/source/dat/descript/spells.txt:1983；crawl-ref/source/dat/descript/zh/spells.txt:1154 |
| textdb:slug dart spell | slug dart spell | <br>射出一个坚硬甲壳质的锋利飞镖。 | keep | 硬甲壳锋利飞镖齐全。 | crawl-ref/source/dat/descript/spells.txt:1987；crawl-ref/source/dat/descript/zh/spells.txt:1158 |
| textdb:smiting spell | smiting spell | <br>惩击视线内的指定敌人，无需直射路径。 | keep | 视野指定敌/不需直射路径齐全。 | crawl-ref/source/dat/descript/spells.txt:1991；crawl-ref/source/dat/descript/zh/spells.txt:1162 |
| textdb:sojourning bolt spell | sojourning bolt spell | <br>吐出一道穿透性且不稳定的双射能量冲击。若命中，它可能会在短暂延迟后<br>传送受害者。对于像你这样格外可口的冒险者，这次传送会将受害者移向<br>施法者的盟友，并在可能的情况下捎上施法者同行。 | keep | 穿透不稳双射冲击/命中可能稍延后传、玩家受害者被传至敌盟友及可能带施法者齐全。 | crawl-ref/source/dat/descript/spells.txt:1995；crawl-ref/source/dat/descript/zh/spells.txt:2013 |
| textdb:soul splinter spell | soul splinter spell | <br>尝试迫使活物、神圣或恶魔生物的一小片灵魂离开身体，显现为灵魂微光。<br>它名义上受死灵法师控制，却会优先攻击自己的来源，凭本能试图回归原本归宿。<br>在灵魂微光归位前，受害者会陷入虚弱。<br><br>由更强灵魂创造的灵魂微光攻击伤害更高，但始终十分脆弱。 | adjust | 活/圣/魔小魂片化魂光、名义受控/优先来源欲回、归位前弱/强魂高攻但脆齐全；灵魂之息偏离D-C092实体灵魂微光。 本批已修复并复核：已裁定实体旧名。 | crawl-ref/source/dat/descript/spells.txt:2010；crawl-ref/source/dat/descript/zh/spells.txt:2019；docs/decisions.md:D-C-092；crawl-ref/source/dat/i18n/zh/source.txt:soul wisp |
| textdb:spawn tentacles spell | spawn tentacles spell | <br>伸出巨大的触手攻击附近的敌人。 | keep | 大触手攻近敌齐全，触须与触手普通形态近义。 | crawl-ref/source/dat/descript/spells.txt:2022；crawl-ref/source/dat/descript/zh/spells.txt:1166 |
| textdb:spectral cloud spell | spectral cloud spell | <br>制造一团幽灵迷雾云，对亡灵以外的所有生物造成轻微伤害。<br>随时间的推移，危险但短暂存在的幽灵亡灵生物将从迷雾中聚合。 | keep | 迷雾云非亡灵皆少伤、逐渐凝危险短命幽灵亡灵齐全。 | crawl-ref/source/dat/descript/spells.txt:2026；crawl-ref/source/dat/descript/zh/spells.txt:1170 |
| textdb:spellspark servitor spell | spellspark servitor spell | <br>构造一个金属仆从，以施法者自身奥术知识的火花为核心。<br>它能施放创造者掌握的部分破坏性法术，但无法灌注最强大、最不稳定的魔法。<br>仆从的力量随法术威力提高。<br><br>（掌握此法术时，可通过“灌注仆从”能力选择它施放的合格法术。） | keep | 金仆自身知识火花/部分创造者已知破坏法术/最强最不稳不可、威力增强、掌握时灌注仆从选法齐全。 | crawl-ref/source/dat/descript/spells.txt:2032；crawl-ref/source/dat/descript/zh/spells.txt:1175 |
| textdb:sphinx sisters spell | sphinx sisters spell | <br>召唤一对善出谜题的斯芬克斯——一只守卫、一只劫掠者——<br>以诅咒系法术削弱敌人并用狂风猛击。法术威力会提高其耐久与法术威力。 | keep | 一守卫一劫掠斯芬克斯/谜题意象/诅咒削弱及狂风攻击、威力增耐久及施法威力齐全。 | crawl-ref/source/dat/descript/spells.txt:2043；crawl-ref/source/dat/descript/zh/spells.txt:2027 |
| textdb:spit acid spell | spit acid spell | <br>向一个目标生物喷吐酸液。 | keep | 目标吐酸齐全。 | crawl-ref/source/dat/descript/spells.txt:2050；crawl-ref/source/dat/descript/zh/spells.txt:1183 |
| textdb:spit lava spell | spit lava spell | <br>向一个目标生物喷吐岩浆；造成的伤害有一半无视火焰抗性。 | keep | 目标吐岩浆、半伤忽火抗齐全。 | crawl-ref/source/dat/descript/spells.txt:2054；crawl-ref/source/dat/descript/zh/spells.txt:1187 |
| textdb:spit poison spell | spit poison spell | <br>&lt;Spit Poison ability&gt; | keep | Spit Poison能力引用完整，前任务已全文核目标生物喷毒。 | crawl-ref/source/dat/descript/spells.txt:2058；crawl-ref/source/dat/descript/zh/spells.txt:1191 |
| textdb:splinterfrost shell spell | splinterfrost shell spell | <br>在施法者周围构筑一道半圆形的强化冰壳；如有可能，<br>它会将生物推开，为自身腾出位置。<br><br>这道屏障十分坚固；每当一段冰壳被摧毁时，都会碎裂成一阵冰片，<br>向摧毁它的生物齐射。<br><br>如果施法者离屏障太远，冰壳会迅速融化。 | adjust | 半圆强化冰壳/尽可能推生物让位、耐久/毁一段反射冰弹给破坏者、施法者离远快融齐全；空间允许可非阻断拓为如有可能。 建议处理：adopt；if possible可写“如有可能”，比“空间允许”覆盖更完整；未证明当前说法会独立破坏已述效果。 | crawl-ref/source/dat/descript/spells.txt:2062；crawl-ref/source/dat/descript/zh/spells.txt:2032 |
| textdb:splinterspray spell | splinterspray spell | <br>射出一连串木头碎片。防具可以大大削弱其造成的伤害。 | keep | 木碎刺连发/AC强减伤齐全。 | crawl-ref/source/dat/descript/spells.txt:2072；crawl-ref/source/dat/descript/zh/spells.txt:1195 |
| textdb:sporulate spell | sporulate spell | <br>释放一个快速移动、充满气体的浮游孢子。找到敌人后，孢子会爆炸，<br>伤害爆炸范围内的一切，并额外使活物陷入混乱。 | keep | 快速充气浮孢、寻敌后爆伤一切/额外乱活物齐全。 | crawl-ref/source/dat/descript/spells.txt:2076；crawl-ref/source/dat/descript/zh/spells.txt:1199 |
| textdb:stampede spell | stampede spell | <br>沿直线迅速冲向敌人。此后每回合，使用者都会沿该方向以双倍速度移动，<br>以更高的伤害和命中率攻击途中的敌人，并将其推退，<br>直到无法继续移动或已越过目标为止。<br><br>只有当目标位于使用者的八个方位之一时，才能使用。 | keep | 直冲敌、后每回双速/增伤增命中推途敌、不能移动或越目标即止/需八方位齐全。 | crawl-ref/source/dat/descript/spells.txt:2082；crawl-ref/source/dat/descript/zh/spells.txt:2149 |
| textdb:starburst spell | starburst spell | <br>从施法者向各个方向射出穿透性的烈火束。 | keep | 各方向穿透火束齐全；bolts译束语义可成立，与命名根不做机械改。 | crawl-ref/source/dat/descript/spells.txt:2092；crawl-ref/source/dat/descript/zh/spells.txt:1204 |
| textdb:static discharge spell | static discharge spell | <br>向施法者身边的生物释放出几股电流。<br>这些电流可能跃向其他相邻生物，或返回施法者，最终接地消散。<br>电弧返回施法者时造成的伤害较低；造成的伤害无视目标一半的护甲。 | adjust | 邻生物电流可邻链或返自身后接地/返自己弱伤齐全；半护甲误成半伤忽AC且链相邻关系写松。 本批已修复并复核：半护甲误为半伤害。 | crawl-ref/source/dat/descript/spells.txt:2096；crawl-ref/source/dat/descript/zh/spells.txt:1208；crawl-ref/source/spl-damage.cc:2707 |
| textdb:steam ball spell | steam ball spell | <br>向一个目标生物投射热蒸汽球。 | adjust | 向选目标热蒸汽球齐全；热省略由蒸汽语境自然承接，可非阻断补热。 建议处理：adopt；可加“热蒸汽”，与英文修饰语更紧；蒸汽语境已表达温热攻击。 | crawl-ref/source/dat/descript/spells.txt:2103；crawl-ref/source/dat/descript/zh/spells.txt:1214 |
| textdb:steam breath spell | steam breath spell | <br>&lt;Steam Breath ability&gt; | keep | Steam Breath能力引用同一大小写不敏感键，已核强蒸汽烫目标/留遮视云。 | crawl-ref/source/dat/descript/spells.txt:2107；crawl-ref/source/dat/descript/zh/spells.txt:2042 |
| textdb:sticks to snakes spell | sticks to snakes spell | <br>掷出棍棒并将其变成蛇；施法者越强，生成的蛇也必定越强。 | keep | 棍变蛇、施法者更强必更强蛇齐全。 | crawl-ref/source/dat/descript/spells.txt:2111；crawl-ref/source/dat/descript/zh/spells.txt:2046 |
| textdb:sticky flame spell | sticky flame spell | <br>释放一股短程的粘性燃烧物质，它会附着在邻近的生物身上，<br>并在几个回合内造成无视护甲的火焰伤害。如果受害者能够移动，他会更快地将火扑灭。<br><br>如果目标没有实体，液态火焰便无法附着。 | keep | 短程可黏邻生物、数回忽AC火伤/能移动提前灭/无实体不黏齐全。 | crawl-ref/source/dat/descript/spells.txt:2116；crawl-ref/source/dat/descript/zh/spells.txt:1218 |
| textdb:still winds spell | still winds spell | <br>使空气在一大片区域内进入反常的静止状态，<br>防止除极地旋涡之外的任何事物破坏平静。<br>该效果需要集中注意力才能维持，且只能持续很短的时间；<br>如果施法者被杀死，则云会重新正常形成。 | keep | 大区不自然静风/只极地旋涡可破/维持注意且短时/施法者死云可再生齐全。 | crawl-ref/source/dat/descript/spells.txt:2124；crawl-ref/source/dat/descript/zh/spells.txt:1225 |
| textdb:sting spell | sting spell | <br>生成一个锯齿状的结晶毒素碎片。毒刺的冲击总是会让易感目标中毒。<br>即使是有毒抗的目标也有可能中毒，免疫毒的怪物也会受到毒刺的物理冲击。 | keep | 锯毒晶、易感必中毒/毒抗仍概率毒/毒免仍物冲伤齐全。 | crawl-ref/source/dat/descript/spells.txt:2131；crawl-ref/source/dat/descript/zh/spells.txt:1232 |
| textdb:stoke flames spell | stoke flames spell | <br>为地狱之火添加恶意，与火焰结合成蔓延的毁灭性的大火。 | keep | 恶意融合地狱火变蔓延火狱齐全，毁灭大火是inferno意象非新增数字。 | crawl-ref/source/dat/descript/spells.txt:2137；crawl-ref/source/dat/descript/zh/spells.txt:1237 |
| textdb:stone arrow spell | stone arrow spell | <br>射出一根尖锐的岩刺。 | keep | 尖岩刺发射齐全。 | crawl-ref/source/dat/descript/spells.txt:2141；crawl-ref/source/dat/descript/zh/spells.txt:1241 |
| textdb:strip willpower spell | strip willpower spell | <br>大大削弱目标的意志力，使其更容易受到各种魔法效果的影响。 | keep | 大降意志/易多种魔效齐全。 | crawl-ref/source/dat/descript/spells.txt:2145；crawl-ref/source/dat/descript/zh/spells.txt:1245 |
| textdb:stunning burst spell | stunning burst spell | <br>发出微弱的电脉冲，撞击时会造成短暂的麻痹。<br>意志力对抵抗这种影响毫无用处，但电抗有时可以阻止它的影响。 | keep | 微弱电击/撞击很短麻痹/意志无用电抗有时挡齐全；标题眩晕与麻痹近义风格可讨论但正文不误。 建议处理：retain；标题“震慑爆发”可与dazed眩晕状态拉开距离；当前标题属自然近义，正文明确为短暂麻痹，不强制改名。 | crawl-ref/source/dat/descript/spells.txt:2150；crawl-ref/source/dat/descript/zh/spells.txt:1249 |
| textdb:sublimation of blood spell | sublimation of blood spell | <br>将施法者的部分血液转化为魔法能量。这个过程是痛苦的，但绝不会直接致命。<br>转换的效率随法术威力增强而增加。 | keep | 血换魔、痛但不直接致死、威力提高转换效率齐全。 | crawl-ref/source/dat/descript/spells.txt:2156；crawl-ref/source/dat/descript/zh/spells.txt:1254 |
| textdb:summon air elementals spell | summon air elementals spell | <br>召唤一个或多个气元素。 | keep | 一或多气元素齐全。 | crawl-ref/source/dat/descript/spells.txt:2162；crawl-ref/source/dat/descript/zh/spells.txt:1259 |
| textdb:summon cactus giant spell | summon cactus giant spell | <br>召唤一名来自格外多刺部落的战士。近战攻击这名巨人的敌人将遭到痛苦反击！<br>法术威力越高，响应召唤的战士越老练、强壮。 | keep | 刺族战士/近战反伤/高威力更年长健壮齐全。 | crawl-ref/source/dat/descript/spells.txt:2166；crawl-ref/source/dat/descript/zh/spells.txt:1263 |
| textdb:summon demon spell | summon demon spell | <br>打开一扇通往万魔殿领域的大门，引出其中一位居民为施法者效劳一段时间。 | keep | 万魔殿居民暂为施法者效劳齐全。 | crawl-ref/source/dat/descript/spells.txt:2172；crawl-ref/source/dat/descript/zh/spells.txt:1268 |
| textdb:summon dragon spell | summon dragon spell | <br>召唤并束缚一条强大的龙来执行施法者的命令。<br>当法术威力很高时，便可以召唤特别致命的龙，或者同时召唤多个较弱的龙。 | keep | 强龙被召束/高威力可特别致命种或同时多弱龙齐全。 | crawl-ref/source/dat/descript/spells.txt:2177；crawl-ref/source/dat/descript/zh/spells.txt:1272 |
| textdb:summon drakes spell | summon drakes spell | <br>召唤一只或多只幼龙或蛇龙。 | adjust | 多幼龙与蛇龙齐全；当前lindwurm有效实体确为蛇龙，不擅按另一正文林德虫改这里。 当前数量公式1+random2(...)确实允许单只，明确multiple/多只的EN/ZH均需同步校正。 本批已修复并复核：EN/ZH都保证多只，但当前数量可为1。 | crawl-ref/source/dat/descript/spells.txt:2183；crawl-ref/source/dat/descript/zh/spells.txt:1277；crawl-ref/source/mon-cast.cc:8335 |
| textdb:summon earth elementals spell | summon earth elementals spell | <br>召唤一个或多个地元素。 | keep | 一或多地元素齐全。 | crawl-ref/source/dat/descript/spells.txt:2187；crawl-ref/source/dat/descript/zh/spells.txt:1281 |
| textdb:summon emperor scorpions spell | summon emperor scorpions spell | <br>召唤一只或多只高贵而凶暴的帝王蝎。 | adjust | 多个高贵凶暴帝王蝎齐全。 当前数量公式1+random2(...)确实允许单只，明确multiple/多只的EN/ZH均需同步校正。 本批已修复并复核：EN/ZH都保证多只，但当前数量可为1。 | crawl-ref/source/dat/descript/spells.txt:2191；crawl-ref/source/dat/descript/zh/spells.txt:1285；crawl-ref/source/mon-cast.cc:8720 |
| textdb:summon executioners spell | summon executioners spell | <br>召唤一个或多个处刑人撕裂施法者的敌人。 | adjust | 多个处刑人撕敌齐全。 当前数量公式1+random2(...)确实允许单只，明确multiple/多只的EN/ZH均需同步校正。 本批已修复并复核：EN/ZH都保证多个，但当前数量可为1。 | crawl-ref/source/dat/descript/spells.txt:2195；crawl-ref/source/dat/descript/zh/spells.txt:1289；crawl-ref/source/mon-cast.cc:8760 |
| textdb:summon eyeballs spell | summon eyeballs spell | <br>召唤一个或多个浮空眼球，它们可能会造成玻化、变形、混乱、变异或碎裂。 | adjust | 多个眼球/可能玻化变形混乱变异粉碎各异效齐全。 当前数量公式1+random2(...)确实允许单只，明确multiple/多只的EN/ZH均需同步校正。 本批已修复并复核：EN/ZH都保证多个，但当前数量可为1。 | crawl-ref/source/dat/descript/spells.txt:2199；crawl-ref/source/dat/descript/zh/spells.txt:1293；crawl-ref/source/mon-cast.cc:8422 |
| textdb:summon fire elementals spell | summon fire elementals spell | <br>召唤一个或多个火元素。 | keep | 一或多火元素齐全。 | crawl-ref/source/dat/descript/spells.txt:2204；crawl-ref/source/dat/descript/zh/spells.txt:1297 |
| textdb:summon forest spell | summon forest spell | <br>强行将森林位面与这个世界相交。该法术需要开阔的空间才能成功。<br>当法术生效时，森林之灵会被召唤出来，<br>森林的树会被唤醒，并对附近的敌人造成伤害。<br>法术威力能增加位面相交的持续时间、大小和密集程度；灵体的力量也会更强。 | keep | 森林位面相交/需开地、精灵树醒攻近敌、威力增时大小密度及灵体力齐全。 | crawl-ref/source/dat/descript/spells.txt:2208；crawl-ref/source/dat/descript/zh/spells.txt:1301 |
| textdb:summon greater demon spell | summon greater demon spell | <br>召唤一名万魔殿的高等恶魔为施法者效劳。 | keep | 万魔殿高等魔为己效劳齐全。 | crawl-ref/source/dat/descript/spells.txt:2216；crawl-ref/source/dat/descript/zh/spells.txt:1308 |
| textdb:summon hell sentinel spell | summon hell sentinel spell | <br>召唤一尊地狱哨兵——一座由仇恨驱动的噩梦般建筑。 | keep | 地狱哨兵/活化仇恨建筑噩梦意象齐全。 | crawl-ref/source/dat/descript/spells.txt:2224；crawl-ref/source/dat/descript/zh/spells.txt:1328 |
| textdb:summon holies spell | summon holies spell | <br>召来神圣战士协助施法者。 | keep | 神圣战士援施法者齐全。 | crawl-ref/source/dat/descript/spells.txt:2228；crawl-ref/source/dat/descript/zh/spells.txt:1332 |
| textdb:summon horrible things spell | summon horrible things spell | <br>打开一扇通往深渊的大门，并从那片可怖之地呼来两个或更多畸形的可憎之物。<br>它们虽强大，但以这种方式让心智触及深渊的本质会使施法者遭受厄运，<br>最终可能付出惨重代价。 | keep | 深渊门两或多丑憎恶、强大但触深渊招厄运/最终惨重代价齐全。 | crawl-ref/source/dat/descript/spells.txt:2232；crawl-ref/source/dat/descript/zh/spells.txt:1336 |
| textdb:summon hydra spell | summon hydra spell | <br>召唤一只多头蛇，在短时间内与施法者并肩战斗。<br>法术威力决定着头的数量。 | keep | 多头蛇短助战、威力定头数齐全。 | crawl-ref/source/dat/descript/spells.txt:2239；crawl-ref/source/dat/descript/zh/spells.txt:1342 |
| textdb:summon ice beast spell | summon ice beast spell | <br>召唤一只冰兽为施法者效劳。野兽的力量取决于法术威力。 | keep | 冰兽效劳/威力定强度齐全。 | crawl-ref/source/dat/descript/spells.txt:2244；crawl-ref/source/dat/descript/zh/spells.txt:1347 |
| textdb:summon illusion spell | summon illusion spell | <br>召唤一个暂时存在的敌人镜像。<br>该复制品拥有与本体相同的物理战斗能力，也能施放相同的法术。 | keep | 敌人暂镜像、同物战/同法术齐全。 | crawl-ref/source/dat/descript/spells.txt:2249；crawl-ref/source/dat/descript/zh/spells.txt:1351 |
| textdb:summon mana viper spell | summon mana viper spell | <br>召唤一条紫鳞魔力毒蛇，其咬击能够迅速削减几乎任何敌人的魔力储备。<br>法术威力越强，魔力毒蛇咬击的反魔法效果越强。 | keep | 紫鳞蛇、咬击快速汲几乎任意敌魔、高威力增强反魔齐全。 | crawl-ref/source/dat/descript/spells.txt:2254；crawl-ref/source/dat/descript/zh/spells.txt:1361 |
| textdb:summon minor demon spell | summon minor demon spell | <br>召唤一至三个次级（第 5 阶）恶魔。 | keep | 1至3第5阶次魔齐全。 | crawl-ref/source/dat/descript/spells.txt:2260；crawl-ref/source/dat/descript/zh/spells.txt:1366 |
| textdb:summon mortal champion spell | summon mortal champion spell | <br>召来光辉者麾下最强大、最迅捷的凡人冠军之一。<br>在这座地牢中，会响应召唤的是小精灵防御者和精灵剑圣。 | keep | 光辉者最强最快凡人冠军、spriggan defender/deep elf blademaster两种齐全；当前有效中文实体正是小精灵防御者/精灵剑圣，不擅改深前缀。 | crawl-ref/source/dat/descript/spells.txt:2264；crawl-ref/source/dat/descript/zh/spells.txt:2050 |
| textdb:summon mushrooms spell | summon mushrooms spell | <br>在目标生物附近召唤游走蘑菇和死亡菌。 | keep | 目标旁游走蘑菇/死亡菌齐全；附近与next to略松但实现放置range1-2，与现文不冲突。 | crawl-ref/source/dat/descript/spells.txt:2270；crawl-ref/source/dat/descript/zh/spells.txt:1370 |
| textdb:summon scarabs spell | summon scarabs spell | <br>召唤出一群死亡圣甲虫。 | keep | 一群死亡圣甲虫齐全；同源Infestation的死亡甲虫不同译名需成组处理。 | crawl-ref/source/dat/descript/spells.txt:2274；crawl-ref/source/dat/descript/zh/spells.txt:1374 |
| textdb:summon scorpions spell | summon scorpions spell | <br>召唤出一群毒蝎子。 | keep | 一群毒蝎齐全。 | crawl-ref/source/dat/descript/spells.txt:2278；crawl-ref/source/dat/descript/zh/spells.txt:1378 |
| textdb:summon seismosaurus egg spell | summon seismosaurus egg spell | <br>召唤一颗凶猛蜥蜴的蛋，即将孵化。只要附近有可见敌人且施法者始终与蛋相邻，<br>它便会在被召唤数回合后孵化，蹂躏召唤者的敌人。<br><br>地震龙即使尚未成年也不容小觑。它坚韧得近乎山岳，脚步能产生猛烈的<br>地震冲击波。每道冲击波都会对不会飞的敌人造成大量伤害，有时甚至会<br>让它们彻底站立不稳。<br><br>法术威力会提高蛋的耐久度和其中地震龙的力量，但不会缩短孵化时间。 | keep | 将孵蛋/近有可见敌且施法者始邻才数回孵、坚如山幼体/足踏非飞伤和可能失足、威力增蛋耐久和龙强不减孵时齐全。 | crawl-ref/source/dat/descript/spells.txt:2282；crawl-ref/source/dat/descript/zh/spells.txt:2055 |
| textdb:summon sin beast spell | summon sin beast spell | <br>召唤一只致命的罪孽兽。 | keep | 致命罪孽兽齐全。 | crawl-ref/source/dat/descript/spells.txt:2220；crawl-ref/source/dat/descript/zh/spells.txt:1324 |
| textdb:summon small mammal spell | summon small mammal spell | <br>召唤一只老鼠、蝙蝠或短尾矮袋鼠来协助施法者。<br>法术威力越强，越有可能召唤出短尾矮袋鼠。 | keep | 鼠蝠短尾矮袋鼠之一/威力增后者概率齐全。 | crawl-ref/source/dat/descript/spells.txt:2297；crawl-ref/source/dat/descript/zh/spells.txt:1382 |
| textdb:summon spiders spell | summon spiders spell | <br>召唤一个或多个蜘蛛。 | keep | 一或多蜘蛛齐全。 | crawl-ref/source/dat/descript/spells.txt:2302；crawl-ref/source/dat/descript/zh/spells.txt:1393 |
| textdb:summon tzitzimitl spell | summon tzitzimitl spell | <br>召唤一个齐齐米特尔——传播疾病与绝望的恶魔。 | keep | 齐齐米特尔/疾病绝望恶魔齐全。 | crawl-ref/source/dat/descript/spells.txt:2306；crawl-ref/source/dat/descript/zh/spells.txt:1397 |
| textdb:summon undead spell | summon undead spell | <br>召唤多个亡灵怪物，包括各种鬼魂、吸血鬼、幽魂和其他低阶亡灵。 | keep | 多亡灵/鬼吸血鬼幽魂及其他低阶齐全。 | crawl-ref/source/dat/descript/spells.txt:2315；crawl-ref/source/dat/descript/zh/spells.txt:1401 |
| textdb:summon vermin spell | summon vermin spell | <br>召唤多只老鼠、蜘蛛、蠕虫和蛙。 | keep | 多鼠蜘蛛虫蛙齐全。 | crawl-ref/source/dat/descript/spells.txt:2320；crawl-ref/source/dat/descript/zh/spells.txt:1405 |
| textdb:summon water elementals spell | summon water elementals spell | <br>召唤一个或多个水元素。 | keep | 一或多水元素齐全。 | crawl-ref/source/dat/descript/spells.txt:2324；crawl-ref/source/dat/descript/zh/spells.txt:1409 |
| textdb:swiftness spell | swiftness spell | <br>召唤风以极大地提高施法者的移动速度。效果结束后，施法者的移动会暂时变慢。 | adjust | 风大增移动、完后移动慢一阵；中文动作慢可能误示所有行动减速，应限定移动。 本批已修复并复核：后遗症从移动慢扩大为动作慢。 | crawl-ref/source/dat/descript/spells.txt:2328；crawl-ref/source/dat/descript/zh/spells.txt:1413；crawl-ref/source/spl-selfench.cc:cast_swiftness |
| textdb:symbol of torment spell | symbol of torment spell | <br>召唤黑暗力量，折磨施法者附近的活物和神圣生物，使其生命值减半；<br>负能量抗性可抵消部分效果。此伤害绝不会直接致命。 | keep | 附近活或圣HP减半/负抗部分免/不直接杀齐全。 | crawl-ref/source/dat/descript/spells.txt:2333；crawl-ref/source/dat/descript/zh/spells.txt:1417 |
| textdb:teleport other spell | teleport other spell | <br>尝试在短暂延迟后将目标生物传送出施法者的视野。 | keep | 尝试短延后把目标送出己视野齐全。 | crawl-ref/source/dat/descript/spells.txt:2339；crawl-ref/source/dat/descript/zh/spells.txt:1422 |
| textdb:throw ally spell | throw ally spell | <br>将附近的一名盟友扔向施法怪物的敌人，只造成很少伤害，并让被扔出的怪物<br>落在目标附近。 | keep | 近友投敌/极小伤/落目标旁齐全。 | crawl-ref/source/dat/descript/spells.txt:2344；crawl-ref/source/dat/descript/zh/spells.txt:1426 |
| textdb:throw barbs spell | throw barbs spell | <br>向目标射出一阵倒刺，将其刺穿，使其移动时遭受痛苦。 | keep | 倒刺齐射/刺身且移动痛齐全。 | crawl-ref/source/dat/descript/spells.txt:2349；crawl-ref/source/dat/descript/zh/spells.txt:1431 |
| textdb:throw bolas spell | throw bolas spell | <br>向目标投掷一具巨型流星索；它甚至能缠住最庞大的敌人，将其束缚在原地。 | keep | 巨流星索/即最大敌可包裹原地束齐全。 | crawl-ref/source/dat/descript/spells.txt:2354；crawl-ref/source/dat/descript/zh/spells.txt:2066 |
| textdb:throw flame spell | throw flame spell | <br>抛出一小团火焰。 | keep | 小团火焰齐全。 | crawl-ref/source/dat/descript/spells.txt:2359；crawl-ref/source/dat/descript/zh/spells.txt:1435 |
| textdb:throw frost spell | throw frost spell | <br>抛出一小团冰霜。 | keep | 小团寒霜齐全。 | crawl-ref/source/dat/descript/spells.txt:2363；crawl-ref/source/dat/descript/zh/spells.txt:1439 |
| textdb:throw icicle spell | throw icicle spell | <br>射出一枚冰片。由于冲击强烈且边缘锋利，其一半伤害会无视寒冷抗性。 | keep | 冰片/冲击锋边半伤忽寒抗齐全。 | crawl-ref/source/dat/descript/spells.txt:2367；crawl-ref/source/dat/descript/zh/spells.txt:1443 |
| textdb:throw klown pie spell | throw klown pie spell | <br>扔出一块有害却出奇美味的派，可能使受击者遭受多种无法抵抗的临时<br>削弱效果，包括眩晕、沉默、火焰易伤、脆弱、失明或厌恶饮用药水。 | keep | 有害却美味派/不可抗暂效果/眩晕沉默火易伤脆弱盲禁药六类齐全。 | crawl-ref/source/dat/descript/spells.txt:2372；crawl-ref/source/dat/descript/zh/spells.txt:1447 |
| textdb:thunderbolt spell | thunderbolt spell | <br>产生一道可穿透目标的电弧。 | keep | 穿透电弧齐全。 | crawl-ref/source/dat/descript/spells.txt:2379；crawl-ref/source/dat/descript/zh/spells.txt:1452 |
| textdb:touch of paradox spell | touch of paradox spell | <br>使附近一个随机盟友脱离空间的束缚，赋予其天生的多重攻击能力，<br>能以一次必定命中的近战攻击打击多个远处敌人。<br>它使用这项能力时，也有一定几率闪烁。 | adjust | 近随机友方得天然多重攻击/一必中近攻多远敌/用时可能闪烁齐全；闪现近义非阻断术语建议。 建议处理：adopt；blink普通动词可对齐“闪烁”；当前闪现属可理解近义，不作阻断。 | crawl-ref/source/dat/descript/spells.txt:2383；crawl-ref/source/dat/descript/zh/spells.txt:2162 |
| textdb:trog's hand spell | trog's hand spell | <br>&lt;Trog's Hand ability&gt; | keep | Trog Hand能力引用完整，已核再生叠加/不再生者可用/意志强化。 | crawl-ref/source/dat/descript/spells.txt:2390；crawl-ref/source/dat/descript/zh/spells.txt:1456 |
| textdb:tukima's dance spell | tukima's dance spell | <br>给一个目标敌人的武器注入生命，它会脱离敌人掌控，倒戈相向。<br>一旦目标死亡，武器很快就会落地。<br><br>某些强大的有名字的神器不会被影响，任何需要魔力释放技能的属性都不会被激活。 | keep | 敌武离手倒戈不断攻、敌死后武器落地/部分固定神器免/需魔力释放属性禁齐全。 | crawl-ref/source/dat/descript/spells.txt:2400；crawl-ref/source/dat/descript/zh/spells.txt:1465 |
| textdb:ufetubi swarm spell | ufetubi swarm spell | <br>召唤一群狂暴的乌菲特布斯。这些烦人的低阶恶魔会迅速蜂拥而上，<br>包围施法者的敌人。 | keep | 狂暴乌菲特布斯群/烦低阶魔快围施法者敌齐全。 | crawl-ref/source/dat/descript/spells.txt:2310；crawl-ref/source/dat/descript/zh/spells.txt:2157 |
| textdb:upheaval spell | upheaval spell | <br>呼唤自然力量，用岩浆、冰、风或碎石轰击一小片区域。 | keep | 自然力小区岩浆冰风碎石齐全。 | crawl-ref/source/dat/descript/spells.txt:2409；crawl-ref/source/dat/descript/zh/spells.txt:1472 |
| textdb:vampiric draining spell | vampiric draining spell | <br>窃取邻近生物的生命力，并将其给予施法者。 | keep | 邻生物生命给施法者齐全。 | crawl-ref/source/dat/descript/spells.txt:2414；crawl-ref/source/dat/descript/zh/spells.txt:1476 |
| textdb:vanquished vanguard spell | vanquished vanguard spell | <br>呼唤远古战死兽人的徘徊灵魂，让它们短暂重拾战斗使命。<br>这些先锋比多数幽灵更依恋生前，能以生者般的技巧挥舞长柄武器，<br>并冷酷高效地包围猎物。 | keep | 远古死兽人短得战使命/较幽灵更念前生/长柄活人技冷高效围敌齐全。 | crawl-ref/source/dat/descript/spells.txt:2418；crawl-ref/source/dat/descript/zh/spells.txt:1387 |
| textdb:venom bolt spell | venom bolt spell | <br>发射一道穿透性的毒箭。 | keep | 穿透毒箭齐全。 | crawl-ref/source/dat/descript/spells.txt:2426；crawl-ref/source/dat/descript/zh/spells.txt:1480 |
| textdb:vex spell | vex spell | <br>以无谓的挫败感蒙蔽目标心智，迫使其数回合内只会攻击附近格子，<br>无论格子为空还是其中站着盟友。 | keep | 无谓挫败遮心/数回仅攻邻格包括空/盟友齐全。 | crawl-ref/source/dat/descript/spells.txt:2430；crawl-ref/source/dat/descript/zh/spells.txt:2070 |
| textdb:vhi's electric charge spell | vhi's electric charge spell | <br>让施法者冲向选定的一个附近敌人，在近身时发动高精度的近战攻击。<br>所造成的额外电击伤害取决于冲锋距离、法术威力和这次物理攻击的伤害。<br>施法者被包裹在扭曲的空间中，从而得以安全地穿过生物、陷阱和有害地形，<br>并置换在目的地的生物。<br>该法术所花费的时间是正常施展一个法术或发动一次近战攻击所需的时间中的较大者。 | keep | 选近敌冲锋高命中近攻、电伤由距威力物伤三项、扭空间可过生物陷阱险地/移开终点者、法耗时与近攻取较大齐全。 | crawl-ref/source/dat/descript/spells.txt:2446；crawl-ref/source/dat/descript/zh/spells.txt:1494 |
| textdb:vhi's electrolunge spell | vhi's electrolunge spell | <br>让施法者冲向选定的一个附近敌人，在近身时发动高精度的近战攻击，<br>并根据法术威力造成额外电击伤害。<br>施法者会被包裹在扭曲的空间中，因而能够安全穿过生物、陷阱和有害地形，<br>并置换目的地的生物。 | keep | 选近敌冲高命中近攻/依威力额外电伤、扭空间安全过生物陷阱险地/移终点者齐全。 | crawl-ref/source/dat/descript/spells.txt:2457；crawl-ref/source/dat/descript/zh/spells.txt:2075 |
| textdb:virulence spell | virulence spell | <br>使一个目标生物更易受到毒害。 | keep | 选目标更易受毒齐全。 | crawl-ref/source/dat/descript/spells.txt:2436；crawl-ref/source/dat/descript/zh/spells.txt:1484 |
| textdb:vitrify spell | vitrify spell | <br>使一个生物的身体结构变得像玻璃那样易碎而脆弱，<br>使其受到的伤害增加，无论伤害来自何处。 | adjust | 体如玻璃脆/全来源伤提高；中文改成所有来源攻击，漏非攻击伤害。 本批已修复并复核：全部伤害来源被缩成攻击。 | crawl-ref/source/dat/descript/spells.txt:2465；crawl-ref/source/dat/descript/zh/spells.txt:1502；crawl-ref/source/mon-ench.cc:ENCH_VITRIFIED |
| textdb:vitrifying gaze spell | vitrifying gaze spell | <br>不可抵抗地使一个生物的身体结构变得如玻璃般易碎，使其承受的所有伤害<br>增加。该法术只需视线，无需直达射线。 | keep | 不可抗玻化/全来源伤增/视线不需射线齐全。 | crawl-ref/source/dat/descript/spells.txt:2470；crawl-ref/source/dat/descript/zh/spells.txt:1507 |
| textdb:volatile blastmotes spell | volatile blastmotes spell | <br>在施法者周围生成一团不稳定的爆炸粉尘云。<br>这些物质在接触明火或生物时会爆炸——包括任何愚蠢到还在其中逗留的施法者！<br>震荡爆炸会将相邻生物推开。所造成的伤害随法术威力增强而增加。 | keep | 己周不稳粉尘云/明火或生物含己触爆、震荡推邻/威力增伤齐全。 | crawl-ref/source/dat/descript/spells.txt:1184；crawl-ref/source/dat/descript/zh/spells.txt:733 |
| textdb:volley of thorns spell | volley of thorns spell | <br>射出一小束锋利的荆棘。 | keep | 小阵锋刺齐射齐全。 | crawl-ref/source/dat/descript/spells.txt:2476；crawl-ref/source/dat/descript/zh/spells.txt:1512 |
| textdb:warning cry spell | warning cry spell | <br>发出巨大的噪音，警示周围的敌人。 | keep | 大声警近敌齐全。 | crawl-ref/source/dat/descript/spells.txt:2480；crawl-ref/source/dat/descript/zh/spells.txt:1516 |
| textdb:warp body spell | warp body spell | <br>以诱发变异的腐化力量扭曲一个生物的身体，造成少量伤害并施加一项短暂变异。<br>若目标已经受到多项短暂变异影响，则改为对其施加玻璃化。 | keep | 诱变腐化体/小伤一短变异、已有多暂变则玻化齐全；诱发变异是自然展开同义，不作术语硬错。 | crawl-ref/source/dat/descript/spells.txt:2484；crawl-ref/source/dat/descript/zh/spells.txt:2082 |
| textdb:warp space spell | warp space spell | <br>短暂撕开一道猛烈的空间裂隙，伤害被卷入其中的一切，<br>并有时使它们闪烁至不远处。 | adjust | 短而烈空间裂/全卷入者受伤且有时短闪齐全。 建议处理：adopt；blink普通动词可写“闪烁”；当前短距离闪现语义可成立。 | crawl-ref/source/dat/descript/spells.txt:2490；crawl-ref/source/dat/descript/zh/spells.txt:2087 |
| textdb:waterstrike spell | waterstrike spell | <br>使目标周围或下方的水剧烈旋转，造成伤害。<br>它可以影响站在水中或在水上飞行的目标。 | keep | 目标旁/下水旋伤、立水或飞水上可中齐全。 | crawl-ref/source/dat/descript/spells.txt:2495；crawl-ref/source/dat/descript/zh/spells.txt:1520 |
| textdb:weakening gaze spell | weakening gaze spell | <br>不可抵抗地使一个生物的近战攻击暂时变弱。该法术只需视线，无需直达射线。 | keep | 不可抗近战暂弱、视线不需射线齐全。 | crawl-ref/source/dat/descript/spells.txt:2500；crawl-ref/source/dat/descript/zh/spells.txt:1525 |
| textdb:wind blast spell | wind blast spell | <br>产生一股强风，在锥形区域内推开生物和云雾。<br>如果生物因此撞上其他东西，它会受到伤害。 | keep | 强风锥推人云/撞物才伤齐全。 | crawl-ref/source/dat/descript/spells.txt:2505；crawl-ref/source/dat/descript/zh/spells.txt:1529 |
| textdb:woodweal spell | woodweal spell | <br>利用树叶和树皮的生命力来治疗大量创伤。<br>如果没有相邻的树，则无法施放。 | keep | 叶皮生命大治疗/必须邻树齐全。 | crawl-ref/source/dat/descript/spells.txt:2510；crawl-ref/source/dat/descript/zh/spells.txt:1534 |
| textdb:word of recall spell | word of recall spell | <br>在短时间延迟后，将同层的有智慧的友方召回到施法者那边。 | keep | 同层智慧友短延召回己齐全。 | crawl-ref/source/dat/descript/spells.txt:2515；crawl-ref/source/dat/descript/zh/spells.txt:1539 |
| textdb:yara's violent unravelling spell | yara's violent unravelling spell | <br>如果施放在一个已经被魔法祝福（或诅咒）的生物身上，这些魔法将被撕碎，<br>转化为破坏性的诱变辐射。受害者和任何相邻生物都会被炸伤并严重变形，<br>变得虚弱且护甲降低。<br>被召唤的生物特别容易受到伤害，<br>因为将它们绑定在这个位面的魔法会瓦解，导致它们立刻消散。 | keep | 目标已有祝/咒魔效才拆成诱变辐射、目标及邻炸重变形弱/降甲、召唤束系瓦解即解散齐全。 | crawl-ref/source/dat/descript/spells.txt:2520；crawl-ref/source/dat/descript/zh/spells.txt:1543 |

### 名称与定义
| 身份 | 英文源名／源键 | 当前中文／采用内容 | 终态 | 理由、发现与处理 | 证据 |
|---|---|---|---|---|---|
| spell:SPELL_CAUSE_FEAR | Cause Fear | 恐惧术 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近恐惧、不能接近/近战偶尔失败、离视线结束齐全。 | crawl-ref/source/spl-data.h:30 |
| spell:SPELL_MAGIC_DART | Magic Dart | 魔法飞弹 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：小魔能飞弹必命中齐全。 | crawl-ref/source/spl-data.h:41 |
| spell:SPELL_FIREBALL | Fireball | 火球 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：爆炸火球投掷齐全。 | crawl-ref/source/spl-data.h:52 |
| spell:SPELL_APPORTATION | Apportation | 隔空取物 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：地面指定位置全部物品拉向己、低威力未必拉到、极强神器如宝珠可抵抗齐全。 | crawl-ref/source/spl-data.h:63 |
| spell:SPELL_BLASTMOTE | Volatile Blastmotes | 不稳定爆尘 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：己周不稳粉尘云/明火或生物含己触爆、震荡推邻/威力增伤齐全。 | crawl-ref/source/spl-data.h:74 |
| spell:SPELL_DIG | Dig | 挖掘 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：挖天然未加工岩隧道；unworked误成未成形，含义从未加工转为未有形。 | crawl-ref/source/spl-data.h:85 |
| spell:SPELL_BOLT_OF_FIRE | Bolt of Fire | 火焰箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透烈火箭齐全。 | crawl-ref/source/spl-data.h:96 |
| spell:SPELL_BOLT_OF_COLD | Bolt of Cold | 寒冰箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透寒冰箭齐全。 | crawl-ref/source/spl-data.h:107 |
| spell:SPELL_LIGHTNING_BOLT | Lightning Bolt | 闪电箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：强穿电箭/墙反弹两击齐全；半护甲误成半伤害无视护甲。 | crawl-ref/source/spl-data.h:118 |
| spell:SPELL_ARCJOLT | Arcjolt | 电弧震击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：相邻/近邻链式电流、自身豁免齐全；忽略半护甲被误写成半伤害无视护甲。 | crawl-ref/source/spl-data.h:129 |
| spell:SPELL_PLASMA_BEAM | Plasma Beam | 等离子光束 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：最远可见敌之一/穿等离子半护甲/随后同路火束齐全；此条正确译一半护甲，与其他电术形成校准。 | crawl-ref/source/spl-data.h:140 |
| spell:SPELL_PERMAFROST_ERUPTION | Permafrost Eruption | 永冻爆发 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：古寒猛喷/天顶岩砸必中、冷忽AC伤目标邻人、总选敌最密/不爆自己旁齐全。 | crawl-ref/source/spl-data.h:151 |
| spell:SPELL_BLINKBOLT | Blinkbolt | 闪烁箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：化穿透闪电并移位至终点齐全。 | crawl-ref/source/spl-data.h:162 |
| spell:SPELL_ELECTRIC_CHARGE | Vhi's Electric Charge | 维之电击冲锋 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：选近敌冲锋高命中近攻、电伤由距威力物伤三项、扭空间可过生物陷阱险地/移开终点者、法耗时与近攻取较大齐全。 | crawl-ref/source/spl-data.h:174 |
| spell:SPELL_ELECTROLUNGE | Vhi's Electrolunge | 维之电击突进 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：选近敌冲高命中近攻/依威力额外电伤、扭空间安全过生物陷阱险地/移终点者齐全。 | crawl-ref/source/spl-data.h:186 |
| spell:SPELL_BOLT_OF_MAGMA | Bolt of Magma | 岩浆箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透熔岩、半伤无视火抗齐全；此处英文确实修饰伤害而不是护甲。 | crawl-ref/source/spl-data.h:197 |
| spell:SPELL_POLYMORPH | Polymorph | 变形术 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：随机改生物外形、对变形者特效齐全。 | crawl-ref/source/spl-data.h:208 |
| spell:SPELL_SLOW | Slow | 缓慢 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：生物行动变慢齐全。 | crawl-ref/source/spl-data.h:220 |
| spell:SPELL_HASTE | Haste | 加速 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：自己行动加速齐全。 | crawl-ref/source/spl-data.h:231 |
| spell:SPELL_PETRIFY | Petrify | 石化 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：主目标及链最多另两敌、未抗意志先短慢后石化/不能动但半伤/次级威力弱齐全；中文把额外foes改为生物。 | crawl-ref/source/spl-data.h:242 |
| spell:SPELL_CONFUSE | Confuse | 混乱 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：心智困惑混乱齐全。 | crawl-ref/source/spl-data.h:253 |
| spell:SPELL_INVISIBILITY | Invisibility | 隐身术 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：自身隐形及随机短移、对看不见敌命中降/闪避格挡重罚齐全。 | crawl-ref/source/spl-data.h:265 |
| spell:SPELL_THROW_FLAME | Throw Flame | 投掷火焰 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：小团火焰齐全。 | crawl-ref/source/spl-data.h:276 |
| spell:SPELL_THROW_FROST | Throw Frost | 投掷冰霜 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：小团寒霜齐全。 | crawl-ref/source/spl-data.h:287 |
| spell:SPELL_DISJUNCTION | Disjunction | 空间分离 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：暂不稳空间、周围者远闪、距离决定概率/紧邻近必齐全。 | crawl-ref/source/spl-data.h:298 |
| spell:SPELL_FREEZING_CLOUD | Freezing Cloud | 冰冻云 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：大团致命冷汽云齐全。 | crawl-ref/source/spl-data.h:309 |
| spell:SPELL_FREEZING_GUST | Freezing Gust | 冰冻阵风 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透冷气箭/沿途致命冷云齐全。 | crawl-ref/source/spl-data.h:320 |
| spell:SPELL_MEPHITIC_CLOUD | Mephitic Cloud | 迷瘴云 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：易碎瓶短有害烟云、无毒抗可混乱/强经验较难齐全。 | crawl-ref/source/spl-data.h:331 |
| spell:SPELL_VENOM_BOLT | Venom Bolt | 毒液箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透毒箭齐全。 | crawl-ref/source/spl-data.h:342 |
| spell:SPELL_OLGREBS_TOXIC_RADIANCE | Olgreb's Toxic Radiance | 奥尔格雷布之毒辐射 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：自己毒光环、法术持续时视野所有生物不断中毒齐全。 | crawl-ref/source/spl-data.h:353 |
| spell:SPELL_TELEPORT_OTHER | Teleport Other | 传送他人 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：尝试短延后把目标送出己视野齐全。 | crawl-ref/source/spl-data.h:364 |
| spell:SPELL_DEATHS_DOOR | Death's Door | 死亡之门 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：短时近无敌/濒死/治疗无效、到期前一次警告、禁立即再施、高威力结束后离死更远、亡灵无效齐全。 | crawl-ref/source/spl-data.h:375 |
| spell:SPELL_MASS_CONFUSION | Mass Confusion | 群体混乱 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：注视施法者全体混乱齐全。 | crawl-ref/source/spl-data.h:386 |
| spell:SPELL_SMITING | Smiting | 惩击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：视野指定敌/不需直射路径齐全。 | crawl-ref/source/spl-data.h:397 |
| spell:SPELL_SUMMON_SMALL_MAMMAL | Summon Small Mammal | 召唤小型哺乳动物 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：鼠蝠短尾矮袋鼠之一/威力增后者概率齐全。 | crawl-ref/source/spl-data.h:408 |
| spell:SPELL_ABJURATION | Abjuration | 驱逐术 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近所有敌对召唤物剩余时间缩短；友敌、召唤类别、时限齐全。 | crawl-ref/source/spl-data.h:421 |
| spell:SPELL_BOLT_OF_DRAINING | Bolt of Draining | 衰竭箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透负能量箭、任何命中活物衰竭齐全；附负能量伤害与实现一致。 | crawl-ref/source/spl-data.h:432 |
| spell:SPELL_LEHUDIBS_CRYSTAL_SPEAR | Lehudib's Crystal Spear | 勒胡迪布之水晶矛 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：致命锋利水晶片齐全。 | crawl-ref/source/spl-data.h:443 |
| spell:SPELL_POLAR_VORTEX | Polar Vortex | 极地漩涡 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：冰旋巨大伤、寒抗只减一半/卷空抛掷、随己风眼唯安全、闭区削弱、完后短冷齐全。 | crawl-ref/source/spl-data.h:454 |
| spell:SPELL_POISONOUS_CLOUD | Poisonous Cloud | 毒云 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：大致命毒气云齐全。 | crawl-ref/source/spl-data.h:465 |
| spell:SPELL_FIRE_STORM | Fire Storm | 火焰风暴 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标强烈火风暴、短命火旋涡/半伤忽火抗齐全，但大范围伤害被省略未明确。 | crawl-ref/source/spl-data.h:476 |
| spell:SPELL_CALL_DOWN_DAMNATION | Call Down Damnation | 降下天谴 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：指定敌无直射天谴、邻伤、无视防护、特定通常能天谴者免疫齐全。 | crawl-ref/source/spl-data.h:487 |
| spell:SPELL_CALL_DOWN_LIGHTNING | Call Down Lightning | 降下闪电 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：指定敌无需直射闪电、相邻及近邻无法命中齐全。 | crawl-ref/source/spl-data.h:498 |
| spell:SPELL_BLINK | Blink | 闪烁 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：随机短距、威力决定短时禁重施齐全。 | crawl-ref/source/spl-data.h:509 |
| spell:SPELL_BLINK_RANGE | Blink Range | 退避闪烁 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：施法者远离目标但仍在目标视线内齐全。 | crawl-ref/source/spl-data.h:520 |
| spell:SPELL_BLINK_AWAY | Blink Away | 远离闪烁 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：施法者去离指定敌更远处齐全。 | crawl-ref/source/spl-data.h:531 |
| spell:SPELL_BLINK_CLOSE | Blink Close | 接近闪烁 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：施法者向敌短距靠近齐全。 | crawl-ref/source/spl-data.h:542 |
| spell:SPELL_ISKENDERUNS_MYSTIC_BLAST | Iskenderun's Mystic Blast | 伊斯肯德伦之神秘冲击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：物理能量球爆击附近全怪、有伤则击退、威力增伤增距离齐全。 | crawl-ref/source/spl-data.h:555 |
| spell:SPELL_SUMMON_HORRIBLE_THINGS | Summon Horrible Things | 召唤恐怖之物 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：深渊门两或多丑憎恶、强大但触深渊招厄运/最终惨重代价齐全。 | crawl-ref/source/spl-data.h:566 |
| spell:SPELL_MALIGN_GATEWAY | Malign Gateway | 邪恶传送门 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：现实裂污异界自维暂门、需开地/稍后触手、依威力受控/到期断而敌/威力延门齐全。 | crawl-ref/source/spl-data.h:577 |
| spell:SPELL_CHARMING | Charm | 魅惑 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：敌暂为己战、追宝冒险者改短混乱齐全。 | crawl-ref/source/spl-data.h:588 |
| spell:SPELL_ANIMATE_DEAD | Animate Dead | 操纵死尸 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：施法后一段时间内自己杀活物变丧尸、概率与持续随威力、重施/离层清丧尸齐全。 | crawl-ref/source/spl-data.h:600 |
| spell:SPELL_PAIN | Pain | 痛苦 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：一个活物极痛伤害齐全。 | crawl-ref/source/spl-data.h:611 |
| spell:SPELL_SOUL_SPLINTER | Soul Splinter | 灵魂分裂 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：活/圣/魔小魂片化魂光、名义受控/优先来源欲回、归位前弱/强魂高攻但脆齐全；灵魂之息偏离D-C092实体灵魂微光。 | crawl-ref/source/spl-data.h:623 |
| spell:SPELL_VAMPIRIC_DRAINING | Vampiric Draining | 吸血术 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：邻生物生命给施法者齐全。 | crawl-ref/source/spl-data.h:635 |
| spell:SPELL_HAUNT | Haunt | 鬼魂缠身 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：幽灵鬼魂只打缠扰目标、目标死快消、威力增数量齐全。 | crawl-ref/source/spl-data.h:646 |
| spell:SPELL_MARTYRS_KNELL | Martyr's Knell | 殉道者之丧钟 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：长死殉道灵暂护/分担部分友伤、再死剥皮鬼/幻伤/短暂离去消/先杀例外齐全。 | crawl-ref/source/spl-data.h:657 |
| spell:SPELL_BORGNJORS_REVIVIFICATION | Borgnjor's Revivification | 博格尼尔之复苏 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：即时全治、永久最大HP代价随威力反比、取消死亡门且短麻痹、亡灵无效齐全。 | crawl-ref/source/spl-data.h:668 |
| spell:SPELL_FREEZE | Freeze | 冰冻 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：相邻目标无视护甲伤害、冷血可能暂慢齐全。 | crawl-ref/source/spl-data.h:679 |
| spell:SPELL_OZOCUBUS_REFRIGERATION | Ozocubu's Refrigeration | 奥佐库布之制冷 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：视野其他生物冷伤、拥抱相邻盟友才部分减伤；中文改为相邻其他任意生物，改了阵营条件。 | crawl-ref/source/spl-data.h:690 |
| spell:SPELL_STICKY_FLAME | Sticky Flame | 黏着火焰 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：短程可黏邻生物、数回忽AC火伤/能移动提前灭/无实体不黏齐全。 | crawl-ref/source/spl-data.h:701 |
| spell:SPELL_SUMMON_ICE_BEAST | Summon Ice Beast | 召唤冰兽 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：冰兽效劳/威力定强度齐全。 | crawl-ref/source/spl-data.h:712 |
| spell:SPELL_OZOCUBUS_ARMOUR | Ozocubu's Armour | 奥佐库布之护甲 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：厚冰当前地点加AC/移位掉、护甲越重越弱齐全；负担等级违现行负重等级。 | crawl-ref/source/spl-data.h:723 |
| spell:SPELL_CALL_IMP | Call Imp | 呼唤小恶魔 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：地狱低阶魔、长矛刺敌、威力增武器质量齐全。 | crawl-ref/source/spl-data.h:734 |
| spell:SPELL_DEFLECT_MISSILES | Deflect Missiles | 偏转飞弹 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：排斥场对所有投射物增加闪避、不能行动仍有效齐全。 | crawl-ref/source/spl-data.h:745 |
| spell:SPELL_BERSERKER_RAGE | Berserker Rage | 狂暴之怒 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：Berserk能力引用原样，已在能力组全读所引正文及副作用；当前法术名狂暴之怒可成立。 | crawl-ref/source/spl-data.h:756 |
| spell:SPELL_DISPEL_UNDEAD | Dispel Undead | 驱散亡灵 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：相邻亡灵/维系形体力量被干扰而重伤齐全。 | crawl-ref/source/spl-data.h:767 |
| spell:SPELL_POISON_ARROW | Poison Arrow | 毒箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：剧毒箭、毒抗者仍中毒/少量直接伤忽毒抗齐全。 | crawl-ref/source/spl-data.h:778 |
| spell:SPELL_BANISHMENT | Banishment | 放逐 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：生物放逐深渊齐全。 | crawl-ref/source/spl-data.h:790 |
| spell:SPELL_STING | Sting | 毒刺 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 实际display使用冻结的上下文名；未把裸键Sting=刺痛/Metal Splinters=金属碎刺当成当前标题。 正文关联：锯毒晶、易感必中毒/毒抗仍概率毒/毒免仍物冲伤齐全。 | crawl-ref/source/spl-data.h:802 |
| spell:SPELL_SUBLIMATION_OF_BLOOD | Sublimation of Blood | 血液升华 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：血换魔、痛但不直接致死、威力提高转换效率齐全。 | crawl-ref/source/spl-data.h:813 |
| spell:SPELL_TUKIMAS_DANCE | Tukima's Dance | 图基玛之舞 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：敌武离手倒戈不断攻、敌死后武器落地/部分固定神器免/需魔力释放属性禁齐全。 | crawl-ref/source/spl-data.h:824 |
| spell:SPELL_SUMMON_DEMON | Summon Demon | 召唤恶魔 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：万魔殿居民暂为施法者效劳齐全。 | crawl-ref/source/spl-data.h:836 |
| spell:SPELL_SUMMON_GREATER_DEMON | Summon Greater Demon | 召唤高等恶魔 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：万魔殿高等魔为己效劳齐全。 | crawl-ref/source/spl-data.h:848 |
| spell:SPELL_PUTREFACTION | Cigotuvi's Putrefaction | 西格图维之腐烂 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：伤口持续数回合瘴气、活物可能慢/重毒、站己处不生云但非其他豁免、仅重伤活物、威力降低自身暂衰竭齐全；中文生命汲取未明确最大HP。 | crawl-ref/source/spl-data.h:860 |
| spell:SPELL_IRON_SHOT | Iron Shot | 铁弹 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：大重金属弹齐全，钢铁与铁弹材质语境相容。 | crawl-ref/source/spl-data.h:871 |
| spell:SPELL_BOMBARD | Bombard | 炮击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：铁球轰目标、常使施法者后退齐全。 | crawl-ref/source/spl-data.h:882 |
| spell:SPELL_STONE_ARROW | Stone Arrow | 石箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：尖岩刺发射齐全。 | crawl-ref/source/spl-data.h:893 |
| spell:SPELL_SHOCK | Shock | 震击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：反弹电束齐全；半护甲误为半伤忽护甲。 | crawl-ref/source/spl-data.h:904 |
| spell:SPELL_SWIFTNESS | Swiftness | 迅捷 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：风大增移动、完后移动慢一阵；中文动作慢可能误示所有行动减速，应限定移动。 | crawl-ref/source/spl-data.h:915 |
| spell:SPELL_DEBUGGING_RAY | Debugging Ray | 调试射线 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：1500hp伤害/必命中齐全，调试射线准确保持内部工具语气。 | crawl-ref/source/spl-data.h:926 |
| spell:SPELL_AGONISING_TOUCH | Agonising Touch | 剧痛之触 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：相邻目标生命减半、绝不直接致死齐全；名称剧痛之触表触碰与强烈痛苦。 | crawl-ref/source/spl-data.h:937 |
| spell:SPELL_CURSE_OF_AGONY | Curse of Agony | 痛苦诅咒 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：下一两次施法者近战命中各令目标剩HP减半齐全。 | crawl-ref/source/spl-data.h:949 |
| spell:SPELL_MINDBURST | Mindburst | 心智爆发 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：心灵攻击过意志才伤、爆心智幽默/完全忽AC、无心智免齐全。 | crawl-ref/source/spl-data.h:961 |
| spell:SPELL_DEATH_CHANNEL | Death Channel | 死亡通道 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：杀死活物/恶魔/神圣灵魂幽魂为己战、引导持续期间齐全。 | crawl-ref/source/spl-data.h:973 |
| spell:SPELL_SYMBOL_OF_TORMENT | Symbol of Torment | 折磨之符 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近活或圣HP减半/负抗部分免/不直接杀齐全。 | crawl-ref/source/spl-data.h:985 |
| spell:SPELL_SIPHON_ESSENCE | Siphon Essence | 吸取精华 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：近活物敌HP半/永不直接杀/痛苦治疗己齐全。 | crawl-ref/source/spl-data.h:996 |
| spell:SPELL_THROW_ICICLE | Throw Icicle | 投掷冰柱 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：冰片/冲击锋边半伤忽寒抗齐全。 | crawl-ref/source/spl-data.h:1007 |
| spell:SPELL_AIRSTRIKE | Airstrike | 空袭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标周围狂暴空气旋涡、越空旷越高伤齐全；空袭无新增军械含义。 | crawl-ref/source/spl-data.h:1018 |
| spell:SPELL_MOMENTUM_STRIKE | Momentum Strike | 动量打击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：借未来移动能量轰敌/之后短不能行走飞行蛇行/仅可移动生物能施；无法动弹暗示全行动停且slither误滑翔，宜明确仅移动受禁。 | crawl-ref/source/spl-data.h:1030 |
| spell:SPELL_SHADOW_CREATURES | Shadow Creatures | 暗影生物 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：当前地点原生生物复制/暗影深渊丝线编织齐全。 | crawl-ref/source/spl-data.h:1041 |
| spell:SPELL_CONFUSING_TOUCH | Confusing Touch | 困惑之触 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：惯用手施魔、触碰释放可能混乱、尝试触碰攻击无伤齐全。 | crawl-ref/source/spl-data.h:1052 |
| spell:SPELL_PASSWALL | Passwall | 穿墙术 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：邻岩短穿到另侧、异常长施法不能行动/同岩调谐加AC齐全。 | crawl-ref/source/spl-data.h:1063 |
| spell:SPELL_IGNITE_POISON | Ignite Poison | 点燃毒素 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近毒转液火由内焚中毒者、毒云迷瘴转火、自身不直接受影响齐全。 | crawl-ref/source/spl-data.h:1074 |
| spell:SPELL_CALL_CANINE_FAMILIAR | Call Canine Familiar | 呼唤犬类使魔 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：召犬神、缔结纽带、施法威力正比强化；附近重施治疗/解毒/下一击更快横扫齐全。 | crawl-ref/source/spl-data.h:1085 |
| spell:SPELL_SUMMON_DRAGON | Summon Dragon | 召唤巨龙 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：强龙被召束/高威力可特别致命种或同时多弱龙齐全。 | crawl-ref/source/spl-data.h:1096 |
| spell:SPELL_HIBERNATION | Ensorcelled Hibernation | 冬眠 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：代谢下降冬眠、醒后短时不能再睡齐全。 | crawl-ref/source/spl-data.h:1107 |
| spell:SPELL_ENGLACIATION | Metabolic Englaciation | 代谢冻结 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近全生物代谢降、无寒抗才减速、冷血更强/强者短持续齐全。 | crawl-ref/source/spl-data.h:1119 |
| spell:SPELL_SILENCE | Silence | 沉默 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近无声/卷轴法术神能喊叫禁、某怪天生特殊免、威力初半径渐缩最后己至过期齐全。 | crawl-ref/source/spl-data.h:1130 |
| spell:SPELL_SHATTER | Shatter | 粉碎 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：周围大震波重伤全生物、冰骨墙材/石化特效、飞凝胶虚体弱效/可毁墙；漏岩石金属水晶三例且石化那句有病句。 | crawl-ref/source/spl-data.h:1141 |
| spell:SPELL_DISPERSAL | Dispersal | 空间驱离 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：短距全生物远传、意志抵抗仍短闪、每受影响怪另意志判混乱齐全。 | crawl-ref/source/spl-data.h:1152 |
| spell:SPELL_DISCHARGE | Static Discharge | 静电释放 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：邻生物电流可邻链或返自身后接地/返自己弱伤齐全；半护甲误成半伤忽AC且链相邻关系写松。 | crawl-ref/source/spl-data.h:1163 |
| spell:SPELL_CORONA | Corona | 光晕 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：光晕勾轮廓提高命中齐全；驱散霉味字面化了原文氛围修辞。 | crawl-ref/source/spl-data.h:1174 |
| spell:SPELL_INTOXICATE | Alistair's Intoxication | 阿利斯泰尔之醉 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：脑物质转酒精、视野智慧目标、毒抗可能抵抗、成功心灵接触才自身短眩晕、宴会破冰幽默齐全。 | crawl-ref/source/spl-data.h:1186 |
| spell:SPELL_LRD | Lee's Rapid Deconstruction | 李之快速解构 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：墙及可见脆怪碎片、冰骨墙材石化可用、护甲大减、石冰骨小爆/金属小强/晶体大强齐全。 | crawl-ref/source/spl-data.h:1197 |
| spell:SPELL_SANDBLAST | Sandblast | 沙爆 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：快碎岩、环境取岩慢所以施法1.5倍、AC大减齐全。 | crawl-ref/source/spl-data.h:1208 |
| spell:SPELL_SIMULACRUM | Sculpt Simulacrum | 塑造拟像 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：相邻活/魔/圣拟像、短成形再动攻、血灵液忤善神、上限5齐全。 | crawl-ref/source/spl-data.h:1220 |
| spell:SPELL_CONJURE_BALL_LIGHTNING | Conjure Ball Lightning | 召唤球形闪电 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：数个电球、敌前爆炸/可能误伤、离施法者远可无害消散齐全；最近敌 qualifier漏且半护甲误为半伤。 | crawl-ref/source/spl-data.h:1232 |
| spell:SPELL_CHAIN_LIGHTNING | Chain Lightning | 连锁闪电 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：最近生物起链、渐远渐弱、次级短距/自伤小齐全；半护甲及半电抗被写成半伤害无视二者。 | crawl-ref/source/spl-data.h:1243 |
| spell:SPELL_PORTAL_PROJECTILE | Portal Projectile | 传送投射物 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：射出或扔出的弹药传至敌齐全；投射上位词不构成删除投掷机制。 | crawl-ref/source/spl-data.h:1254 |
| spell:SPELL_MONSTROUS_MENAGERIE | Monstrous Menagerie | 怪物动物园 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：援己强异域生物/蝎尾狮林德虫劫掠斯芬克斯三选一齐全。 | crawl-ref/source/spl-data.h:1265 |
| spell:SPELL_GOLUBRIAS_PASSAGE | Passage of Golubria | 戈卢布里亚之通道 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：两门其中一近己、进入随机到其他开门/数量不限/短时或进入即关齐全。 | crawl-ref/source/spl-data.h:1276 |
| spell:SPELL_FULMINANT_PRISM | Fulminant Prism | 爆裂棱镜 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：不稳软金棱镜/不能货币幽默、短后奥术爆炸、提前毁爆弱齐全。 | crawl-ref/source/spl-data.h:1287 |
| spell:SPELL_PARALYSE | Paralyse | 麻痹 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：生物短期一切行动禁齐全。 | crawl-ref/source/spl-data.h:1298 |
| spell:SPELL_MINOR_HEALING | Minor Healing | 小型治疗 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：自己少量伤治疗齐全。 | crawl-ref/source/spl-data.h:1310 |
| spell:SPELL_MAJOR_HEALING | Major Healing | 大型治疗 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：自己大量伤害治疗齐全。 | crawl-ref/source/spl-data.h:1321 |
| spell:SPELL_WOODWEAL | Woodweal | 林木疗愈 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：叶皮生命大治疗/必须邻树齐全。 | crawl-ref/source/spl-data.h:1332 |
| spell:SPELL_HURL_DAMNATION | Hurl Damnation | 投掷天谴 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：Hurl Damnation能力引用完整，已核目标邻伤/防护无效/免疫例外。 | crawl-ref/source/spl-data.h:1343 |
| spell:SPELL_BRAIN_BITE | Brain Bite | 脑噬 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：可见敌人少量心智与比例魔力、无需直射、近空魔双伤齐全。 | crawl-ref/source/spl-data.h:1356 |
| spell:SPELL_NOXIOUS_CLOUD | Noxious Cloud | 毒瘴云 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：大有害烟云可能混乱齐全；云为烟雾自然同义。 | crawl-ref/source/spl-data.h:1367 |
| spell:SPELL_STEAM_BALL | Steam Ball | 蒸汽球 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：向选目标热蒸汽球齐全；热省略由蒸汽语境自然承接，可非阻断补热。 | crawl-ref/source/spl-data.h:1379 |
| spell:SPELL_UFETUBI_SWARM | Ufetubi Swarm | 乌菲特布斯群 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：狂暴乌菲特布斯群/烦低阶魔快围施法者敌齐全。 | crawl-ref/source/spl-data.h:1390 |
| spell:SPELL_SUMMON_SIN_BEAST | Summon Sin Beast | 召唤罪孽兽 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：致命罪孽兽齐全。 | crawl-ref/source/spl-data.h:1401 |
| spell:SPELL_BOLT_OF_DEVASTATION | Bolt of Devastation | 毁灭箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透悲伤心痛箭、意志减半齐全。 | crawl-ref/source/spl-data.h:1412 |
| spell:SPELL_SPIT_POISON | Spit Poison | 喷吐毒液 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：Spit Poison能力引用完整，前任务已全文核目标生物喷毒。 | crawl-ref/source/spl-data.h:1423 |
| spell:SPELL_SUMMON_UNDEAD | Summon Undead | 召唤亡灵 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：多亡灵/鬼吸血鬼幽魂及其他低阶齐全。 | crawl-ref/source/spl-data.h:1435 |
| spell:SPELL_CANTRIP | Cantrip | 小戏法 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：数种小法术之一、试图鼓舞、无可察效果；中文初级单次不表示可挑选法术。 | crawl-ref/source/spl-data.h:1446 |
| spell:SPELL_QUICKSILVER_BOLT | Quicksilver Bolt | 水银箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透驱散能、可能删部分魔法齐全。 | crawl-ref/source/spl-data.h:1457 |
| spell:SPELL_METAL_SPLINTERS | Metal Splinters | 金属碎片 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 实际display使用冻结的上下文名；未把裸键Sting=刺痛/Metal Splinters=金属碎刺当成当前标题。 正文关联：金属碎片爆发/护甲强减伤齐全。 | crawl-ref/source/spl-data.h:1468 |
| spell:SPELL_SPLINTERSPRAY | Splinterspray | 碎片喷射 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：木碎刺连发/AC强减伤齐全。 | crawl-ref/source/spl-data.h:1479 |
| spell:SPELL_MIASMA_BREATH | Miasma Breath | 瘴气吐息 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：大恶臭瘴气云、活物中毒/可能减速齐全。 | crawl-ref/source/spl-data.h:1490 |
| spell:SPELL_SUMMON_DRAKES | Summon Drakes | 召唤幼龙 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：多幼龙与蛇龙齐全；当前lindwurm有效实体确为蛇龙，不擅按另一正文林德虫改这里。 当前数量公式1+random2(...)确实允许单只，明确multiple/多只的EN/ZH均需同步校正。 | crawl-ref/source/spl-data.h:1502 |
| spell:SPELL_BLINK_OTHER | Blink Other | 使他人闪烁 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：敌方随机短距移位、意志不能抗拒齐全。 | crawl-ref/source/spl-data.h:1513 |
| spell:SPELL_BLINK_OTHER_CLOSE | Blink Other Close | 使他人闪烁靠近 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：敌方向施法者短距移位、意志不能抗拒齐全。 | crawl-ref/source/spl-data.h:1525 |
| spell:SPELL_SUMMON_MUSHROOMS | Summon Mushrooms | 召唤蘑菇 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标旁游走蘑菇/死亡菌齐全；附近与next to略松但实现放置range1-2，与现文不冲突。 | crawl-ref/source/spl-data.h:1536 |
| spell:SPELL_SPIT_ACID | Spit Acid | 喷吐酸液 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标吐酸齐全。 | crawl-ref/source/spl-data.h:1547 |
| spell:SPELL_CAUSTIC_BREATH | Caustic Breath | 腐蚀吐息 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：Caustic Breath能力引用完整，按能力卡全正文复审结果挂接。 | crawl-ref/source/spl-data.h:1559 |
| spell:SPELL_PYRE_ARROW | Pyre Arrow | 烈火箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：液火黏目标、多回忽AC火伤、移动快灭/无实体不黏齐全。 | crawl-ref/source/spl-data.h:1570 |
| spell:SPELL_FIRE_BREATH | Fire Breath | 火焰吐息 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：对目标喷火齐全。 | crawl-ref/source/spl-data.h:1581 |
| spell:SPELL_SEARING_BREATH | Searing Breath | 灼热吐息 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标喷火、终点留火云齐全。 | crawl-ref/source/spl-data.h:1593 |
| spell:SPELL_CHAOS_BREATH | Chaos Breath | 混沌吐息 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：大范围混沌本质烟云；中文混乱混淆Chaos与Confusion。 | crawl-ref/source/spl-data.h:1605 |
| spell:SPELL_COLD_BREATH | Cold Breath | 寒霜吐息 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：集中冰冷空气吐息齐全。 | crawl-ref/source/spl-data.h:1617 |
| spell:SPELL_GLACIAL_BREATH | Glacial Breath | 冰川吐息 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：Glacial Breath引用完整，已复审击杀后留坚固冰块。 | crawl-ref/source/spl-data.h:1629 |
| spell:SPELL_WATER_ELEMENTALS | Summon Water Elementals | 召唤水元素 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：一或多水元素齐全。 | crawl-ref/source/spl-data.h:1640 |
| spell:SPELL_PORKALATOR | Porkalator | 变猪术 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标变猪/快移不能施法/施法者死解齐全。 | crawl-ref/source/spl-data.h:1651 |
| spell:SPELL_CREATE_TENTACLES | Spawn Tentacles | 生成触须 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：大触手攻近敌齐全，触须与触手普通形态近义。 | crawl-ref/source/spl-data.h:1663 |
| spell:SPELL_SUMMON_EYEBALLS | Summon Eyeballs | 召唤眼球 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：多个眼球/可能玻化变形混乱变异粉碎各异效齐全。 当前数量公式1+random2(...)确实允许单只，明确multiple/多只的EN/ZH均需同步校正。 | crawl-ref/source/spl-data.h:1674 |
| spell:SPELL_HASTE_OTHER | Haste Other | 加速他人 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近一友方所有行动加速齐全。 | crawl-ref/source/spl-data.h:1685 |
| spell:SPELL_TOUCH_OF_PARADOX | Touch of Paradox | 悖论之触 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：近随机友方得天然多重攻击/一必中近攻多远敌/用时可能闪烁齐全；闪现近义非阻断术语建议。 | crawl-ref/source/spl-data.h:1697 |
| spell:SPELL_EARTH_ELEMENTALS | Summon Earth Elementals | 召唤地元素 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：一或多地元素齐全。 | crawl-ref/source/spl-data.h:1708 |
| spell:SPELL_AIR_ELEMENTALS | Summon Air Elementals | 召唤气元素 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：一或多气元素齐全。 | crawl-ref/source/spl-data.h:1719 |
| spell:SPELL_FIRE_ELEMENTALS | Summon Fire Elementals | 召唤火元素 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：一或多火元素齐全。 | crawl-ref/source/spl-data.h:1730 |
| spell:SPELL_SLEEP | Sleep | 睡眠 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标睡、通常受伤醒/大声可能醒；中文去掉typically变成受伤必醒。 | crawl-ref/source/spl-data.h:1741 |
| spell:SPELL_FAKE_MARA_SUMMON | Mara Summon | 玛拉召唤 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：施法者幻象等战斗/等法术齐全。 | crawl-ref/source/spl-data.h:1753 |
| spell:SPELL_SUMMON_ILLUSION | Summon Illusion | 召唤幻象 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：敌人暂镜像、同物战/同法术齐全。 | crawl-ref/source/spl-data.h:1764 |
| spell:SPELL_PRIMAL_WAVE | Primal Wave | 原初浪潮 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：水流可能击退、短浅水池齐全。 | crawl-ref/source/spl-data.h:1775 |
| spell:SPELL_CALL_TIDE | Call Tide | 呼唤潮汐 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：大范围水潮、稍后全层高潮、施法者旁更高水位齐全。 | crawl-ref/source/spl-data.h:1786 |
| spell:SPELL_IOOD | Orb of Destruction | 毁灭法球 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 实际display使用冻结的上下文名；未把裸键Sting=刺痛/Metal Splinters=金属碎刺当成当前标题。 正文关联：纯毁灭慢追踪球/惯性可躲/新生弱、地牢居民可维至撞/玩家离视线散齐全。 | crawl-ref/source/spl-data.h:1797 |
| spell:SPELL_INK_CLOUD | Ink Cloud | 墨云 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：浓墨云遮视线齐全。 | crawl-ref/source/spl-data.h:1808 |
| spell:SPELL_MIGHT | Might | 强壮 | keep | 此法术赋近战伤害强效但标题沿普通强壮意象，不承诺增加力量属性；与正文及BEAM_MIGHT相容。spells域明确允许强壮，不能机械套状态域强效。 正文关联：自身近战伤显著增齐全；强壮为法术显示专门名，未承诺力量属性数值。 | crawl-ref/source/spl-data.h:1819 |
| spell:SPELL_MIGHT_OTHER | Might Other | 强壮他人 | keep | 此法术赋近战伤害强效但标题沿普通强壮意象，不承诺增加力量属性；与正文及BEAM_MIGHT相容。spells域明确允许强壮，不能机械套状态域强效。 正文关联：附近友方近战伤显著增齐全；强壮他人是法术标题专用映射，非状态Might标签，不机械改强效。 | crawl-ref/source/spl-data.h:1830 |
| spell:SPELL_AWAKEN_FOREST | Awaken Forest | 唤醒森林 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：树有限运动/枝根活动/邻敌猛击齐全；有限未译直语但枝根活动未变成自由行走。 | crawl-ref/source/spl-data.h:1841 |
| spell:SPELL_DRUIDS_CALL | Druid's Call | 德鲁伊呼唤 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：同层其他林地生物召回齐全。 | crawl-ref/source/spl-data.h:1852 |
| spell:SPELL_BROTHERS_IN_ARMS | Brothers in Arms | 战友 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：与引用能力的EN/ZH文字一致，但当前monster-only法术的召唤物按施法者种类从固定表选，summon_berserker不读XL；玩家能力才按XL选型。应分开法术正文，避免把正确玩家缩放强加怪物。 | crawl-ref/source/spl-data.h:1863 |
| spell:SPELL_TROGS_HAND | Trog's Hand | 特洛格之手 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：Trog Hand能力引用完整，已核再生叠加/不再生者可用/意志强化。 | crawl-ref/source/spl-data.h:1874 |
| spell:SPELL_SUMMON_MORTAL_CHAMPION | Summon Mortal Champion | 召唤凡人冠军 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：光辉者最强最快凡人冠军、spriggan defender/deep elf blademaster两种齐全；当前有效中文实体正是小精灵防御者/精灵剑圣，不擅改深前缀。 | crawl-ref/source/spl-data.h:1885 |
| spell:SPELL_VANQUISHED_VANGUARD | Vanquished Vanguard | 败军先锋 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：远古死兽人短得战使命/较幽灵更念前生/长柄活人技冷高效围敌齐全。 | crawl-ref/source/spl-data.h:1896 |
| spell:SPELL_SUMMON_HOLIES | Summon Holies | 召唤神圣生物 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：神圣战士援施法者齐全。 | crawl-ref/source/spl-data.h:1907 |
| spell:SPELL_HEAL_OTHER | Heal Other | 治愈他人 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近一友方治疗齐全。 | crawl-ref/source/spl-data.h:1918 |
| spell:SPELL_HOLY_FLAMES | Holy Flames | 神圣火焰 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：圣火环困敌、亡灵恶魔更伤/圣者免齐全。 | crawl-ref/source/spl-data.h:1930 |
| spell:SPELL_HOLY_BREATH | Holy Breath | 神圣吐息 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：大团神圣火/善神荣、亡灵恶魔更伤/神圣免齐全；cloud可明确云以保留残留地形信息。 | crawl-ref/source/spl-data.h:1941 |
| spell:SPELL_INJURY_MIRROR | Injury Mirror | 伤害反射 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：暂反伤/每次自身受伤伤攻击者、结束后短禁再施齐全。 | crawl-ref/source/spl-data.h:1953 |
| spell:SPELL_DRAIN_LIFE | Drain Life | 汲取生命 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近所有敌汲命、自疗与伤正比齐全。 | crawl-ref/source/spl-data.h:1964 |
| spell:SPELL_LEDAS_LIQUEFACTION | Leda's Liquefaction | 勒达之液化 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：液地慢移动/困者不飞/近战可能失败、威力初半径渐缩最终自身、即飞行施法者也慢齐全。 | crawl-ref/source/spl-data.h:1975 |
| spell:SPELL_SUMMON_HYDRA | Summon Hydra | 召唤多头蛇 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：多头蛇短助战、威力定头数齐全。 | crawl-ref/source/spl-data.h:1986 |
| spell:SPELL_MESMERISE | Mesmerise | 迷魂 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：视野全敌迷魂、未抵抗玩家不能远离/其他直接眩晕、离视线解控制齐全。 | crawl-ref/source/spl-data.h:1997 |
| spell:SPELL_HELLFIRE_COURT | Hellfire Court | 地狱火法庭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 建议处理：retain；Court亦可指魔王宫廷随从；“地狱火宫廷”可供风格讨论，现有法庭意象尚无足够反证，不强制改名。 正文关联：召火与天谴恶魔齐全；Court法庭/宫廷有双义，仅可提非阻断宫廷建议，不无依据推翻旧名。 | crawl-ref/source/spl-data.h:2008 |
| spell:SPELL_PETRIFYING_CLOUD | Petrifying Cloud | 石化云 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：钙化雾受影响超过片刻才石化齐全。 | crawl-ref/source/spl-data.h:2019 |
| spell:SPELL_INNER_FLAME | Inner Flame | 内焰 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：内火每次命中释火/死爆、爆范围由目标体型齐全。 | crawl-ref/source/spl-data.h:2030 |
| spell:SPELL_ENSNARE | Ensnare | 束缚 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：蛛网丝射流困目标黏网齐全；一连串网可建议改蛛丝避免多个捕网印象。 | crawl-ref/source/spl-data.h:2041 |
| spell:SPELL_GREATER_ENSNARE | Greater Ensnare | 强力束缚 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：蛛网流困目标、周围额外蛛网/短时消散齐全。 | crawl-ref/source/spl-data.h:2052 |
| spell:SPELL_THUNDERBOLT | Thunderbolt | 雷击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透电弧齐全。 | crawl-ref/source/spl-data.h:2063 |
| spell:SPELL_BATTLESPHERE | Iskenderun's Battlesphere | 伊斯肯德伦之战斗法球 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：小能量球/每攻击法术后向最伤可达近敌必中齐射、可自由穿射不伤齐全。 | crawl-ref/source/spl-data.h:2074 |
| spell:SPELL_SUMMON_MINOR_DEMON | Summon Minor Demon | 召唤次级恶魔 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：1至3第5阶次魔齐全。 | crawl-ref/source/spl-data.h:2085 |
| spell:SPELL_STICKS_TO_SNAKES | Sticks to Snakes | 棍变蛇 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：棍变蛇、施法者更强必更强蛇齐全。 | crawl-ref/source/spl-data.h:2096 |
| spell:SPELL_MALMUTATE | Malmutate | 恶性变异 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：一次通常有害变异、人造免/亡灵腐朽齐全。 | crawl-ref/source/spl-data.h:2107 |
| spell:SPELL_GLOOM | Gloom | 阴郁 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近吞光、活物恶魔神圣可短盲、意志无效但强者可挡齐全。 | crawl-ref/source/spl-data.h:2119 |
| spell:SPELL_BECKONING_GALE | Beckoning Gale | 招引之风 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标空气扭曲伤害并试图拉近施法者齐全。 | crawl-ref/source/spl-data.h:2130 |
| spell:SPELL_FORCE_LANCE | Force Lance | 力量之矛 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：震荡力命中并造成伤害才可能击退、撞墙/生物双方追加伤齐全。 | crawl-ref/source/spl-data.h:2141 |
| spell:SPELL_SENTINEL_MARK | Sentinel's Mark | 哨兵印记 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：强信标/同层所有生物知存在位置齐全。 | crawl-ref/source/spl-data.h:2152 |
| spell:SPELL_WORD_OF_RECALL | Word of Recall | 召回之言 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：同层智慧友短延召回己齐全。 | crawl-ref/source/spl-data.h:2165 |
| spell:SPELL_INJURY_BOND | Injury Bond | 伤害联结 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：友军受伤减半、施法者只受被免部分的一半齐全，未写成完整承受一半初始伤。 | crawl-ref/source/spl-data.h:2176 |
| spell:SPELL_SPECTRAL_CLOUD | Spectral Cloud | 幽灵云 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：迷雾云非亡灵皆少伤、逐渐凝危险短命幽灵亡灵齐全。 | crawl-ref/source/spl-data.h:2187 |
| spell:SPELL_GHOSTLY_FIREBALL | Ghostly Fireball | 幽灵火球 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：爆炸负能量球、笼罩活物衰竭齐全。 | crawl-ref/source/spl-data.h:2198 |
| spell:SPELL_CALL_LOST_SOULS | Call Lost Souls | 呼唤迷失灵魂 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：死灵幽魂、救强大亡灵濒死、垂死活物变幽灵齐全；lost souls遗魂与标题迷失灵魂是同一可辨实体。 | crawl-ref/source/spl-data.h:2210 |
| spell:SPELL_DIMENSION_ANCHOR | Dimension Anchor | 维度锚定 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：阻主动被动移位、包括部分跨位面但放逐例外齐全。 | crawl-ref/source/spl-data.h:2221 |
| spell:SPELL_BLINK_ALLIES_ENCIRCLE | Blink Allies Encircling | 使盟友闪烁合围 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：视野内若干盟友、合围选定敌人齐全。 | crawl-ref/source/spl-data.h:2233 |
| spell:SPELL_AWAKEN_VINES | Awaken Vines | 唤醒藤蔓 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：藤蔓长出、抓闯入者、拖向附近树齐全。 | crawl-ref/source/spl-data.h:2244 |
| spell:SPELL_THORN_VOLLEY | Volley of Thorns | 荆棘齐射 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：小阵锋刺齐射齐全。 | crawl-ref/source/spl-data.h:2255 |
| spell:SPELL_CAGE_OF_BRAMBLES | Cage of Brambles | 荆棘牢笼 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近每敌荆棘环围、施法者盟友可穿射、他人拆除痛苦齐全。 | crawl-ref/source/spl-data.h:2266 |
| spell:SPELL_WATERSTRIKE | Waterstrike | 水击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标旁/下水旋伤、立水或飞水上可中齐全。 | crawl-ref/source/spl-data.h:2277 |
| spell:SPELL_WIND_BLAST | Wind Blast | 风击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：强风锥推人云/撞物才伤齐全。 | crawl-ref/source/spl-data.h:2288 |
| spell:SPELL_STRIP_WILLPOWER | Strip Willpower | 剥离意志力 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：大降意志/易多种魔效齐全。 | crawl-ref/source/spl-data.h:2299 |
| spell:SPELL_FUGUE_OF_THE_FALLEN | Fugue of the Fallen | 亡灵赋格 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：长死者残余魂、己友杀非召唤敌积魂增近远效能、满时每击痛楚伤邻目标其他敌、重施重置/维持时哀嚎招注意齐全；弥留物误指临死且末句要保持它不自然。 | crawl-ref/source/spl-data.h:2311 |
| spell:SPELL_SUMMON_VERMIN | Summon Vermin | 召唤害虫 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：多鼠蜘蛛虫蛙齐全。 | crawl-ref/source/spl-data.h:2322 |
| spell:SPELL_MALIGN_OFFERING | Malign Offering | 邪恶献祭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：汲敌命治疗附近友方齐全。 | crawl-ref/source/spl-data.h:2333 |
| spell:SPELL_SEARING_RAY | Searing Ray | 灼热射线 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：手中持续穿透奥术线、原地等/不他动供MP则跟踪移动目标齐全。 | crawl-ref/source/spl-data.h:2344 |
| spell:SPELL_DISCORD | Discord | 纷乱 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近生物疯狂、强力量速度、无情攻击附近一切齐全。 | crawl-ref/source/spl-data.h:2355 |
| spell:SPELL_INVISIBILITY_OTHER | Invisibility Other | 使他人隐形 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近友方隐形齐全。 | crawl-ref/source/spl-data.h:2366 |
| spell:SPELL_VIRULENCE | Virulence | 毒性 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：选目标更易受毒齐全。 | crawl-ref/source/spl-data.h:2377 |
| spell:SPELL_ORB_OF_ELECTRICITY | Orb of Electricity | 电光球 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：电球撞击大爆齐全；半护甲误成半伤害无视护甲。 | crawl-ref/source/spl-data.h:2389 |
| spell:SPELL_FLASH_FREEZE | Flash Freeze | 急冻 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标空气冰冻、重伤/半伤忽冷抗齐全，但短暂移动减慢的时限漏译。 | crawl-ref/source/spl-data.h:2400 |
| spell:SPELL_CREEPING_FROST | Creeping Frost | 蔓延冰霜 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：墙体寒霜、墙邻敌冻结减移动、寒抗减伤但不免冻结齐全。 | crawl-ref/source/spl-data.h:2411 |
| spell:SPELL_LEGENDARY_DESTRUCTION | Legendary Destruction | 传奇毁灭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：瞬时连两个爆法、火球冰爆幽灵火球任意组合齐全；把Ghostly Fireball写旧名鬼火球。 | crawl-ref/source/spl-data.h:2422 |
| spell:SPELL_FORCEFUL_INVITATION | Forceful Invitation | 强制邀请 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：七个分支之一且随施法者不同齐全；Spider Nest被缩成蜘蛛巢违明确术语蜘蛛巢穴。 | crawl-ref/source/spl-data.h:2433 |
| spell:SPELL_PLANEREND | Plane Rend | 位面撕裂 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：六分支之一强威胁/每施随机分支齐全；分支名另依世界名组，不自立称谓。 | crawl-ref/source/spl-data.h:2444 |
| spell:SPELL_CHAIN_OF_CHAOS | Chain of Chaos | 混沌之链 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：纯混沌弧、近旁不可测效果、可触施法者但无害齐全。 | crawl-ref/source/spl-data.h:2455 |
| spell:SPELL_CALL_OF_CHAOS | Call of Chaos | 混沌呼唤 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近友军加速/强效/双活力/抗性四益、偶发反效果意志丧失/狂暴/变形/内焰四项齐全。 | crawl-ref/source/spl-data.h:2466 |
| spell:SPELL_SIGN_OF_RUIN | Sign of Ruin | 毁灭印记 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 实际display使用冻结的上下文名；未把裸键Sting=刺痛/Metal Splinters=金属碎刺当成当前标题。 正文关联：一组敌印记衰亡、每次近战伤重衰竭/可能慢弱盲三额外之一齐全；能力组亦真核本正文，非依旧keep。 | crawl-ref/source/spl-data.h:2477 |
| spell:SPELL_SAP_MAGIC | Sap Magic | 削弱魔法 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：腐化施法、仍施一法后短禁后续齐全。 | crawl-ref/source/spl-data.h:2488 |
| spell:SPELL_MAJOR_DESTRUCTION | Major Destruction | 强力毁灭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：随机有害射束或爆炸对目标齐全；AXED兼容仅保留现文不推历史机制。 | crawl-ref/source/spl-data.h:2499 |
| spell:SPELL_BLINK_ALLIES_AWAY | Blink Allies Away | 使盟友闪烁远离 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：施法者视野盟友远离附近敌人齐全；描述闪送是转移行为近义，不必强制换名词。 | crawl-ref/source/spl-data.h:2511 |
| spell:SPELL_SUMMON_FOREST | Summon Forest | 召唤森林 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：森林位面相交/需开地、精灵树醒攻近敌、威力增时大小密度及灵体力齐全。 | crawl-ref/source/spl-data.h:2522 |
| spell:SPELL_FORGE_LIGHTNING_SPIRE | Forge Lightning Spire | 锻造闪电尖塔 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近不动闪电塔、不时向敌电击、优先最远者齐全。 | crawl-ref/source/spl-data.h:2533 |
| spell:SPELL_FORGE_BLAZEHEART_GOLEM | Forge Blazeheart Golem | 锻造炽心魔像 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：不稳元素火花渣铁壳/猛烈打击反伤自身、相离快休眠、活动时毁壳稍后核爆、威力增爆伤齐全。 | crawl-ref/source/spl-data.h:2544 |
| spell:SPELL_REBOUNDING_BLAZE | Rebounding Blaze | 弹跳烈焰 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透能火/反墙两次命中齐全。 | crawl-ref/source/spl-data.h:2555 |
| spell:SPELL_REBOUNDING_CHILL | Rebounding Chill | 弹跳寒流 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透强寒流/反墙两击齐全。 | crawl-ref/source/spl-data.h:2566 |
| spell:SPELL_GLACIATE | Glaciate | 冰封 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：强冰锥、近更伤、命中冰封慢移/击杀可能冰块、半伤忽寒抗齐全。 | crawl-ref/source/spl-data.h:2577 |
| spell:SPELL_DRAGON_CALL | Dragon's Call | 龙之呼唤 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：呼龙接连出战、每新龙耗更多MP、结束短禁重施、威力决定持续/龙种齐全。 | crawl-ref/source/spl-data.h:1096 |
| spell:SPELL_SPELLSPARK_SERVITOR | Spellspark Servitor | 法术火花仆从 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：金仆自身知识火花/部分创造者已知破坏法术/最强最不稳不可、威力增强、掌握时灌注仆从选法齐全。 | crawl-ref/source/spl-data.h:2599 |
| spell:SPELL_SUMMON_MANA_VIPER | Summon Mana Viper | 召唤魔力毒蛇 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：紫鳞蛇、咬击快速汲几乎任意敌魔、高威力增强反魔齐全。 | crawl-ref/source/spl-data.h:2610 |
| spell:SPELL_PHANTOM_MIRROR | Phantom Mirror | 幻影镜 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：生物幻镜复制/较脆但余几乎同原体齐全。 | crawl-ref/source/spl-data.h:2621 |
| spell:SPELL_DIMINISH_SPELLS | Diminish Spells | 削弱法术 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：不可抗拒暂降敌法术威力齐全。 | crawl-ref/source/spl-data.h:2632 |
| spell:SPELL_CORROSIVE_BOLT | Corrosive Bolt | 腐蚀箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透强腐蚀酸箭齐全。 | crawl-ref/source/spl-data.h:2643 |
| spell:SPELL_BOLT_OF_LIGHT | Bolt of Light | 光箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透灼热光、可能致盲活物恶魔神圣三类齐全。 | crawl-ref/source/spl-data.h:2654 |
| spell:SPELL_BOLT_OF_ANTIMAGIC | Bolt of Antimagic | 反魔箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透反魔箭、存在论悖论意象、汲储备魔力齐全。 | crawl-ref/source/spl-data.h:2665 |
| spell:SPELL_BOLT_OF_FLESH | Bolt of Flesh | 血肉箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透魔法血肉弹幕、路径尽头短暂肉堆齐全。 | crawl-ref/source/spl-data.h:2676 |
| spell:SPELL_AWAKEN_FLESH | Awaken Flesh | 唤醒血肉 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：视野每肉堆、混沌能量、强化大型憎恶、邻近敌人混沌伤齐全。 | crawl-ref/source/spl-data.h:2688 |
| spell:SPELL_SERPENT_OF_HELL_GEH_BREATH | gehenna serpent of hell breath | 欣嫩谷地狱巨蛇吐息 | adjust | D-C-103完整世界依赖组已解决同一领域的多套名称冲突；复用对应领域词根并保留吐息动作，本批采用当前显示名，关闭原名称延期。缺少独立wrapper正文仍属原正文覆盖缺口，不再作为名称延期理由。 | crawl-ref/source/spl-data.h:2699；crawl-ref/source/spl-util.cc:2573 |
| spell:SPELL_SERPENT_OF_HELL_COC_BREATH | cocytus serpent of hell breath | 悲叹河地狱巨蛇吐息 | adjust | D-C-103完整世界依赖组已解决同一领域的多套名称冲突；复用对应领域词根并保留吐息动作，本批采用当前显示名，关闭原名称延期。缺少独立wrapper正文仍属原正文覆盖缺口，不再作为名称延期理由。 | crawl-ref/source/spl-data.h:2711；crawl-ref/source/spl-util.cc:2573 |
| spell:SPELL_SERPENT_OF_HELL_DIS_BREATH | dis serpent of hell breath | 迪斯地狱巨蛇吐息 | adjust | D-C-103完整世界依赖组已解决同一领域的多套名称冲突；复用对应领域词根并保留吐息动作，本批采用当前显示名，关闭原名称延期。缺少独立wrapper正文仍属原正文覆盖缺口，不再作为名称延期理由。 | crawl-ref/source/spl-data.h:2723；crawl-ref/source/spl-util.cc:2573 |
| spell:SPELL_SERPENT_OF_HELL_TAR_BREATH | tartarus serpent of hell breath | 塔尔塔罗斯地狱巨蛇吐息 | adjust | D-C-103完整世界依赖组已解决同一领域的多套名称冲突；复用对应领域词根并保留吐息动作，本批采用当前显示名，关闭原名称延期。缺少独立wrapper正文仍属原正文覆盖缺口，不再作为名称延期理由。 | crawl-ref/source/spl-data.h:2735；crawl-ref/source/spl-util.cc:2573 |
| spell:SPELL_SUMMON_EMPEROR_SCORPIONS | Summon Emperor Scorpions | 召唤帝王蝎 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：多个高贵凶暴帝王蝎齐全。 当前数量公式1+random2(...)确实允许单只，明确multiple/多只的EN/ZH均需同步校正。 | crawl-ref/source/spl-data.h:2747 |
| spell:SPELL_IRRADIATE | Irradiate | 辐射 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：极薄皮肤转纯魔能炸邻物、可能重变形弱/降AC、几施后危险污染齐全；皮肤的或类似物质句多出的的需删。 | crawl-ref/source/spl-data.h:2758 |
| spell:SPELL_SPIT_LAVA | Spit Lava | 喷吐岩浆 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标吐岩浆、半伤忽火抗齐全。 | crawl-ref/source/spl-data.h:2769 |
| spell:SPELL_ELECTRICAL_BOLT | Electrical Bolt | 电击箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：高命中穿透电箭齐全。 | crawl-ref/source/spl-data.h:2781 |
| spell:SPELL_FLAMING_CLOUD | Flaming Cloud | 燃烧云 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：大团咆哮烈火云齐全。 | crawl-ref/source/spl-data.h:2793 |
| spell:SPELL_THROW_BARBS | Throw Barbs | 投掷倒刺 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：倒刺齐射/刺身且移动痛齐全。 | crawl-ref/source/spl-data.h:2805 |
| spell:SPELL_BATTLECRY | Battlecry | 战吼 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：近旁友方更积极且增强攻击齐全。 | crawl-ref/source/spl-data.h:2817 |
| spell:SPELL_WARNING_CRY | Warning Cry | 警告之嚎 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：大声警近敌齐全。 | crawl-ref/source/spl-data.h:2828 |
| spell:SPELL_HUNTING_CALL | Hunting Call | 狩猎呼唤 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近友军快移齐全。 | crawl-ref/source/spl-data.h:2839 |
| spell:SPELL_FUNERAL_DIRGE | Funeral Dirge | 葬礼哀歌 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：数名附近亡灵友方短时快移强攻齐全。 | crawl-ref/source/spl-data.h:2850 |
| spell:SPELL_SEAL_DOORS | Seal Doors | 封印门 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近门与楼梯封、非施法者盟友不可通齐全。 | crawl-ref/source/spl-data.h:2861 |
| spell:SPELL_FLAY | Flay | 剥皮 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：疼痛幻伤、短时间或施法者死消、不可直接杀/非自然免疫齐全。 | crawl-ref/source/spl-data.h:2872 |
| spell:SPELL_BERSERK_OTHER | Berserk Other | 狂暴他人 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：近旁友军狂暴、暂HP/速度/近战伤害提高齐全。 | crawl-ref/source/spl-data.h:2883 |
| spell:SPELL_CORRUPTING_PULSE | Corrupting Pulse | 腐化脉冲 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：全部可见目标暂有害变异、人造免疫/亡灵腐朽齐全。 | crawl-ref/source/spl-data.h:2894 |
| spell:SPELL_SIREN_SONG | Siren Song | 塞壬之歌 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：听众迷魂、未抗玩家不能远离/其他眩晕、离施法者视线止控制齐全。 | crawl-ref/source/spl-data.h:2905 |
| spell:SPELL_AVATAR_SONG | Avatar Song | 化身之歌 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：未抵抗冒险者不能远离且可能被拉近、其他生物眩晕、深水可能溺魂、离视线解控制齐全。 | crawl-ref/source/spl-data.h:2916 |
| spell:SPELL_MURKY_LEGION | Murky Legion | 浊影军团 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：浊光怨灵单次同时污染与浅水后消失齐全。 | crawl-ref/source/spl-data.h:2927 |
| spell:SPELL_PARALYSIS_GAZE | Paralysis Gaze | 麻痹凝视 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：不可抗拒短禁全部行动、多次充能/不需射线齐全。 | crawl-ref/source/spl-data.h:2938 |
| spell:SPELL_CONFUSION_GAZE | Confusion Gaze | 困惑凝视 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：心智混乱且无需直射齐全。 | crawl-ref/source/spl-data.h:2949 |
| spell:SPELL_ANTIMAGIC_GAZE | Antimagic Gaze | 反魔法凝视 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标汲魔如反魔武器、无需直射路径齐全。 | crawl-ref/source/spl-data.h:2960 |
| spell:SPELL_DRAINING_GAZE | Draining Gaze | 衰竭凝视 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：活物负能量、按最大HP比例衰竭、需视线不需直射齐全。 | crawl-ref/source/spl-data.h:2971 |
| spell:SPELL_WEAKENING_GAZE | Weakening Gaze | 虚弱凝视 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：不可抗近战暂弱、视线不需射线齐全。 | crawl-ref/source/spl-data.h:2983 |
| spell:SPELL_MOURNING_WAIL | Mourning Wail | 哀恸之嚎 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：遗悲流/沿途负能云/跳过易受害者/活物迅速小比例maxHP扣生命；漏活物与小量。 | crawl-ref/source/spl-data.h:2994 |
| spell:SPELL_DEATH_RATTLE | Death Rattle | 死亡之响 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：临终精华成有毒瘴气齐全；死亡实质属可接受风格略泛。 | crawl-ref/source/spl-data.h:3005 |
| spell:SPELL_MARCH_OF_SORROWS | March of Sorrows | 悲伤行军 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：痛苦流尾及目标旁负能云、按最大HP比例迅速损当前生命；中文遗漏活物限定与小比例。 | crawl-ref/source/spl-data.h:3016 |
| spell:SPELL_SUMMON_SCARABS | Summon Scarabs | 召唤圣甲虫 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：一群死亡圣甲虫齐全；同源Infestation的死亡甲虫不同译名需成组处理。 | crawl-ref/source/spl-data.h:3027 |
| spell:SPELL_THROW_ALLY | Throw Ally | 投掷盟友 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：近友投敌/极小伤/落目标旁齐全。 | crawl-ref/source/spl-data.h:3038 |
| spell:SPELL_CLEANSING_FLAME | Cleansing Flame | 净化之焰 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：自身中心神怒、亡灵恶魔重伤及其他敌伤齐全。 | crawl-ref/source/spl-data.h:3049 |
| spell:SPELL_GRAVITAS | Gell's Gravitas | 盖尔之重力 | keep | 当前item-only重力鼓路径拉入附近怪、伤并束敌；Gravitas→重力与Gell→盖尔相符，不把AXED旧重力效果借来。 | crawl-ref/source/spl-data.h:3061 |
| spell:SPELL_VIOLENT_UNRAVELLING | Yara's Violent Unravelling | 亚拉之猛烈解构 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标已有祝/咒魔效才拆成诱变辐射、目标及邻炸重变形弱/降甲、召唤束系瓦解即解散齐全。 | crawl-ref/source/spl-data.h:3072 |
| spell:SPELL_ENTROPIC_WEAVE | Entropic Weave | 熵之编织 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：腐蚀且不需直射路径；中文无需直射法术误把路径条件改为法术类型。 | crawl-ref/source/spl-data.h:3083 |
| spell:SPELL_SUMMON_EXECUTIONERS | Summon Executioners | 召唤处刑人 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：多个处刑人撕敌齐全。 当前数量公式1+random2(...)确实允许单只，明确multiple/多只的EN/ZH均需同步校正。 | crawl-ref/source/spl-data.h:3094 |
| spell:SPELL_OBLIVION_HOWL | Oblivion Howl | 湮灭嚎叫 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：刺耳心灵回声引噩梦生物追源、每个施法生物仅能用一次；特定生物一次误解given creature。 | crawl-ref/source/spl-data.h:3105 |
| spell:SPELL_PRAYER_OF_BRILLIANCE | Prayer of Brilliance | 聪慧祈祷 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近己方巫师更强且更频繁施法齐全。 | crawl-ref/source/spl-data.h:3116 |
| spell:SPELL_ICEBLAST | Iceblast | 冰爆 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：大冰块撞爆/半伤忽寒抗齐全。 | crawl-ref/source/spl-data.h:3127 |
| spell:SPELL_SLUG_DART | Slug Dart | 蛞蝓飞镖 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：硬甲壳锋利飞镖齐全。 | crawl-ref/source/spl-data.h:3138 |
| spell:SPELL_FLEETFOOT | Fleetfoot | 轻快脚步 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：短时风提高移动速度齐全。 | crawl-ref/source/spl-data.h:3149 |
| spell:SPELL_GREATER_SERVANT_MAKHLEB | Infernal Servant | 地狱仆从 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：召大恶魔齐全；此怪物法术固定正文与能力长文不是同一范围。 | crawl-ref/source/spl-data.h:3160 |
| spell:SPELL_BIND_SOULS | Bind Souls | 束缚灵魂 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：其他附近活物、死亡后拟像齐全。 | crawl-ref/source/spl-data.h:3171 |
| spell:SPELL_INFESTATION | Infestation | 虫群侵扰 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：甲虫感染/死亡爆出死亡甲虫齐全；威力决定感染持续时间被错接为按威力感染。 | crawl-ref/source/spl-data.h:3182 |
| spell:SPELL_STILL_WINDS | Still Winds | 静止风 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：大区不自然静风/只极地旋涡可破/维持注意且短时/施法者死云可再生齐全。 | crawl-ref/source/spl-data.h:3193 |
| spell:SPELL_RESONANCE_STRIKE | Resonance Strike | 共鸣打击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：地力打可见敌、附近构装级联/每邻目标构装增威齐全。 | crawl-ref/source/spl-data.h:3204 |
| spell:SPELL_GHOSTLY_SACRIFICE | Ghostly Sacrifice | 幽灵献祭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：友方活力作负能爆、活物衰竭、献祭活物或构装体都被消灭齐全。 | crawl-ref/source/spl-data.h:3215 |
| spell:SPELL_DREAM_DUST | Dream Dust | 梦尘 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：梦尘催眠、额外梦羊加强和延时齐全；遗漏迷人的视觉展示这一施法表现命题。 | crawl-ref/source/spl-data.h:3226 |
| spell:SPELL_BECKONING | Lesser Beckoning | 次级招引 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：招引目标尝试至相邻；中文仅靠近遗漏精确目的格。 | crawl-ref/source/spl-data.h:3237 |
| spell:SPELL_UPHEAVAL | Upheaval | 剧变 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：自然力小区岩浆冰风碎石齐全。 | crawl-ref/source/spl-data.h:3249 |
| spell:SPELL_MERCURY_ARROW | Mercury Arrow | 汞矢 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：汞箭直接毒伤及可能短弱近战、物理力毒免仍小伤、弱化可邻溅/完全不看毒抗齐全。 | crawl-ref/source/spl-data.h:3260 |
| spell:SPELL_POISONOUS_VAPOURS | Poisonous Vapours | 毒气 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：少量空气转毒/吸入中毒、仅施法当回合/任何毒抗者免齐全。 | crawl-ref/source/spl-data.h:3271 |
| spell:SPELL_IGNITION | Ignition | 点火 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：周遭全敌火球、自己友方绝不受本法伤齐全。 | crawl-ref/source/spl-data.h:3282 |
| spell:SPELL_BORGNJORS_VILE_CLUTCH | Borgnjor's Vile Clutch | 博格尼尔之邪恶抓握 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：地底尸手、敌原地束缚齐全，但漏持续缠绕挤压机制。 | crawl-ref/source/spl-data.h:3293 |
| spell:SPELL_FASTROOT | Fastroot | 速生根须 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：种子生快速根缠绕、痛苦挤压至逃或枯、仅实地齐全。 | crawl-ref/source/spl-data.h:3304 |
| spell:SPELL_WARP_SPACE | Warp Space | 扭曲空间 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：短而烈空间裂/全卷入者受伤且有时短闪齐全。 | crawl-ref/source/spl-data.h:3315 |
| spell:SPELL_SOJOURNING_BOLT | Sojourning Bolt | 羁旅箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透不稳双射冲击/命中可能稍延后传、玩家受害者被传至敌盟友及可能带施法者齐全。 | crawl-ref/source/spl-data.h:3326 |
| spell:SPELL_HARPOON_SHOT | Harpoon Shot | 鱼叉射击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：长柔韧带刺物拉扯、撞途中障碍齐全；adjacent只写附近，漏精确相邻落点。 | crawl-ref/source/spl-data.h:3337 |
| spell:SPELL_GRASPING_ROOTS | Grasping Roots | 抓握根须 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：深根抓握挤压、逃脱/施法者离视线根退齐全。 | crawl-ref/source/spl-data.h:3348 |
| spell:SPELL_THROW_BOLAS | Throw Bolas | 投掷流星索 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：巨流星索/即最大敌可包裹原地束齐全。 | crawl-ref/source/spl-data.h:3359 |
| spell:SPELL_THROW_PIE | Throw Klown Pie | 投掷小丑派 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：有害却美味派/不可抗暂效果/眩晕沉默火易伤脆弱盲禁药六类齐全。 | crawl-ref/source/spl-data.h:3371 |
| spell:SPELL_SPORULATE | Sporulate | 产孢 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：快速充气浮孢、寻敌后爆伤一切/额外乱活物齐全。 | crawl-ref/source/spl-data.h:3382 |
| spell:SPELL_LAUNCH_SPORANGIUM | Launch Sporangium | 发射孢子囊 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：腐蚀孢子囊逐营养源含自己/大酸爆、触墙可初生原生质体自射酸/彼此2格内不再生齐全。 | crawl-ref/source/spl-data.h:3393 |
| spell:SPELL_STARBURST | Starburst | 星爆 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：各方向穿透火束齐全；bolts译束语义可成立，与命名根不做机械改。 | crawl-ref/source/spl-data.h:3404 |
| spell:SPELL_FOXFIRE | Foxfire | 狐火 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：两个相邻沼气火球、找最近怪、不可达/交换位无害消散齐全。 | crawl-ref/source/spl-data.h:3415 |
| spell:SPELL_MARSHLIGHT | Marshlight | 沼泽之光 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：两个邻沼气球找最近怪焚烧、巫师仿狐火但弱很多齐全。 | crawl-ref/source/spl-data.h:3426 |
| spell:SPELL_HAILSTORM | Hailstorm | 冰雹风暴 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近未躲冰雹伤、相邻风眼免疫、冲击切割半伤忽寒抗齐全。 | crawl-ref/source/spl-data.h:3437 |
| spell:SPELL_NOXIOUS_BOG | Eringya's Noxious Bog | 埃林吉亚之毒沼 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：近区毒沼、全怪含毒抗受伤中毒、邻多坚固地形/无实地如深水熔岩不能生、暂时/离视线不可维持、威力延时齐全。 | crawl-ref/source/spl-data.h:3448 |
| spell:SPELL_AGONY | Agony | 剧痛 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标生命减半、绝不直接致死齐全；与相邻touch区别仍由正文保留。 | crawl-ref/source/spl-data.h:3459 |
| spell:SPELL_DISPEL_UNDEAD_RANGE | Dispel Undead Range | 远程驱散亡灵 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：干扰形体魔力伤亡灵甚重齐全；范围区别由标题远程及另一相邻版本保留。 | crawl-ref/source/spl-data.h:3471 |
| spell:SPELL_FROZEN_RAMPARTS | Frozen Ramparts | 冰冻壁垒 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：暂冰墙、邻墙敌伤/冷血可能慢、每目标仅一墙、施法者移位冰掉齐全。 | crawl-ref/source/spl-data.h:3482 |
| spell:SPELL_MAXWELLS_COUPLING | Maxwell's Capacitive Coupling | 麦克斯韦之电容耦合 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：原地等待不他动积电、阈值最近可见敌即死、威力快积、起始需可见目标/释放可换目标齐全。 | crawl-ref/source/spl-data.h:3493 |
| spell:SPELL_SONIC_WAVE | Sonic wave | 音波 | keep | 当前fire_los_attack_spell的声音范围伤；Sonic wave→音波贴切。 | crawl-ref/source/spl-data.h:3508 |
| spell:SPELL_ROLL | Roll | 翻滚 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：滚球甲虫巨速/双近战伤、需敌距、尝试攻击后必展开齐全。 | crawl-ref/source/spl-data.h:3515 |
| spell:SPELL_HURL_SLUDGE | Hurl Sludge | 投掷污泥 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：剧毒污泥伤/毒/毒抗者仍受影响齐全；浸满周围污泥被写成仅环境变湿。 | crawl-ref/source/spl-data.h:3526 |
| spell:SPELL_SUMMON_TZITZIMITL | Summon Tzitzimitl | 召唤齐齐米特尔 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：齐齐米特尔/疾病绝望恶魔齐全。 | crawl-ref/source/spl-data.h:3537 |
| spell:SPELL_SUMMON_HELL_SENTINEL | Summon Hell Sentinel | 召唤地狱哨兵 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：地狱哨兵/活化仇恨建筑噩梦意象齐全。 | crawl-ref/source/spl-data.h:3548 |
| spell:SPELL_AWAKEN_ARMOUR | Awaken Armour | 唤醒护甲 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿戴护甲记忆回响、慢移、重量大增伤、全防御属性继承、威力增耐久齐全。 | crawl-ref/source/spl-data.h:3559 |
| spell:SPELL_MANIFOLD_ASSAULT | Manifold Assault | 多重攻击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：空间多可见敌一次近战/威力增数量、徒手半数、同近战耗时/必中/不能背刺加伤齐全。 | crawl-ref/source/spl-data.h:3570 |
| spell:SPELL_CONCENTRATE_VENOM | Concentrate Venom | 浓缩毒液 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标自然毒液强化、毒咬喷吐造成慢/窒息齐全；唾液可建议写喷吐毒液更清晰。 | crawl-ref/source/spl-data.h:3581 |
| spell:SPELL_ERUPTION | Eruption | 喷发 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：裂地、目标下局部短命火山齐全。 | crawl-ref/source/spl-data.h:3593 |
| spell:SPELL_PYROCLASTIC_SURGE | Pyroclastic Surge | 火山碎屑涌 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：熔岩取火、熔岩邻及上方敌受焚齐全。 | crawl-ref/source/spl-data.h:3604 |
| spell:SPELL_STUNNING_BURST | Stunning Burst | 眩晕爆发 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 建议处理：retain；标题“震慑爆发”可与dazed眩晕状态拉开距离；当前标题属自然近义，正文明确为短暂麻痹，不强制改名。 正文关联：微弱电击/撞击很短麻痹/意志无用电抗有时挡齐全；标题眩晕与麻痹近义风格可讨论但正文不误。 | crawl-ref/source/spl-data.h:3615 |
| spell:SPELL_CORRUPT_LOCALE | Corrupt | 腐化 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近深渊能量、改外观/暂召怪、深渊不可齐全。 | crawl-ref/source/spl-data.h:3626 |
| spell:SPELL_CONJURE_LIVING_SPELLS | Conjure Living Spells | 召唤活体法术 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：数个自主活法术、第一敌入程自施后消散齐全。 | crawl-ref/source/spl-data.h:3637 |
| spell:SPELL_SUMMON_CACTUS | Summon Cactus Giant | 召唤仙人掌巨人 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：刺族战士/近战反伤/高威力更年长健壮齐全。 | crawl-ref/source/spl-data.h:3648 |
| spell:SPELL_STOKE_FLAMES | Stoke Flames | 煽旺火焰 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：恶意融合地狱火变蔓延火狱齐全，毁灭大火是inferno意象非新增数字。 | crawl-ref/source/spl-data.h:3659 |
| spell:SPELL_SERACFALL | Seracfall | 冰塔崩塌 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近拟像变冰团撞爆/寒抗仍受部分伤相符。中文明确一半虽比EN精确，但实际SPELL_SERACFALL→ZAP_ICEBLAST→BEAM_ICE，fight.cc:800可抗比例50%，故数字正确；未误信beam.cc旧40/60注释。 | crawl-ref/source/spl-data.h:3670 |
| spell:SPELL_SCORCH | Scorch | 烧焦 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：随机可见敌灼烧、受伤者短时间火抗烧掉齐全。 | crawl-ref/source/spl-data.h:3681 |
| spell:SPELL_FLAME_WAVE | Flame Wave | 火焰波 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：自身周围一波火、原地等待不他动并供魔才更多更大波齐全。 | crawl-ref/source/spl-data.h:3692 |
| spell:SPELL_ENFEEBLE | Enfeeble | 衰弱 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：不可抗拒弱近战及法术、未抗完整诅咒才额外眩晕盲、无视觉仍受影响齐全。 | crawl-ref/source/spl-data.h:3703 |
| spell:SPELL_SUMMON_SPIDERS | Summon Spiders | 召唤蜘蛛 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：一或多蜘蛛齐全。 | crawl-ref/source/spl-data.h:3714 |
| spell:SPELL_ANGUISH | Anguish | 哀痛 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近敌人所致全伤害反弹、持续期间、意志抵抗、无心智免疫齐全。 | crawl-ref/source/spl-data.h:3725 |
| spell:SPELL_SUMMON_SCORPIONS | Summon Scorpions | 召唤蝎子 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：一群毒蝎齐全。 | crawl-ref/source/spl-data.h:3736 |
| spell:SPELL_SHEZAS_DANCE | Sheza's Dance | 谢扎之舞 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：四方武器/新匕首锈剑热血斧三意象、活化出击齐全。 | crawl-ref/source/spl-data.h:3747 |
| spell:SPELL_DIVINE_ARMAMENT | Divine Armament | 神圣武装 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：信仰精神武器自行战斗杀敌、独特虔诚决定每次同武器齐全。 | crawl-ref/source/spl-data.h:3758 |
| spell:SPELL_KISS_OF_DEATH | Kiss of Death | 死亡之吻 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：自身精元化死片痛楚衰竭敌、自生命降低至经验恢复齐全；可非阻断明确最大生命值以贴drain_player。 | crawl-ref/source/spl-data.h:3769 |
| spell:SPELL_JINXBITE | Jinxbite | 厄运之咬 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：顽灵跟进攻击/过意志检则小伤及衰竭、需可见易感目标/无目标快消、自身意志暂降齐全。 | crawl-ref/source/spl-data.h:3780 |
| spell:SPELL_SIGIL_OF_BINDING | Sigil of Binding | 束缚符文 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：两个近印/经过定身但可行动闪避、非己解后迅捷/任意迅捷免束缚、一组/离视线提前失效齐全。 | crawl-ref/source/spl-data.h:3791 |
| spell:SPELL_DIMENSIONAL_BULLSEYE | Dimensional Bullseye | 维度靶心 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：武器与选目标连结、射/投不同敌人才复制投射物传到目标、威力加命中齐全。 | crawl-ref/source/spl-data.h:3802 |
| spell:SPELL_BOULDER | Brom's Barrelling Boulder | 布罗姆之碾压巨石 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：基本方向滚巨石、伤命中者、滚过死者/推幸存者及后排、窄道摩毁、离视线/墙/不动生物碎裂齐全。 | crawl-ref/source/spl-data.h:3813 |
| spell:SPELL_VITRIFY | Vitrify | 玻璃化 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：体如玻璃脆/全来源伤提高；中文改成所有来源攻击，漏非攻击伤害。 | crawl-ref/source/spl-data.h:3824 |
| spell:SPELL_VITRIFYING_GAZE | Vitrifying Gaze | 玻璃化凝视 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：不可抗玻化/全来源伤增/视线不需射线齐全。 | crawl-ref/source/spl-data.h:3836 |
| spell:SPELL_CRYSTALLISING_SHOT | Crystallising Shot | 结晶射击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：大重晶片、可能全来源受伤提高齐全。 | crawl-ref/source/spl-data.h:3847 |
| spell:SPELL_TREMORSTONE | Tremorstone | 震石 | keep | 当前震石zap/多次爆炸分派；Tremorstone→震石为触发物名，不误示施法者变石。 | crawl-ref/source/spl-data.h:3858 |
| spell:SPELL_REGENERATE_OTHER | Regenerate Other | 再生他人 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：另一生物短暂快速再生、按其maxHP正比齐全。 | crawl-ref/source/spl-data.h:3869 |
| spell:SPELL_MASS_REGENERATION | Mass Regeneration | 群体再生 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近全友方怪短期快再生、按各自maxHP正比齐全。 | crawl-ref/source/spl-data.h:3880 |
| spell:SPELL_NOXIOUS_BREATH | Noxious Breath | 毒瘴吐息 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：Noxious Breath能力引用完整，已核无毒抗才可能混乱与等级范围持续缩放。 | crawl-ref/source/spl-data.h:3891 |
| spell:SPELL_UNLEASH_DESTRUCTION | Unleash Destruction | 释放毁灭 | keep | 当前随机破坏性能量zap，与释放毁灭动宾义一致；能力本体五分支另见已审能力。 | crawl-ref/source/spl-data.h:3903 |
| spell:SPELL_HURL_TORCHLIGHT | Hurl Torchlight | 投掷火炬之光 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：活物恶魔神圣不可抗伤、友方亡灵增近战并一次免费行动、同教Yred无害齐全。 | crawl-ref/source/spl-data.h:3914 |
| spell:SPELL_COMBUSTION_BREATH | Combustion Breath | 爆燃吐息 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：Combustion Breath引用原样，能力组已全文核爆余烬/逐生物爆/自身免伤。 | crawl-ref/source/spl-data.h:3925 |
| spell:SPELL_NULLIFYING_BREATH | Nullifying Breath | 消魔吐息 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：Nullifying Breath能力引用完整，已核每命中驱散/施法干扰/自身无害。 | crawl-ref/source/spl-data.h:3936 |
| spell:SPELL_STEAM_BREATH | Steam Breath | 蒸汽吐息 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：Steam Breath能力引用同一大小写不敏感键，已核强蒸汽烫目标/留遮视云。 | crawl-ref/source/spl-data.h:3947 |
| spell:SPELL_MUD_BREATH | Mud Breath | 泥浆吐息 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：Mud Breath能力引用完整，已审泥球击退/泥地慢敌/偶尔攻击失手。 | crawl-ref/source/spl-data.h:3958 |
| spell:SPELL_GALVANIC_BREATH | Galvanic Breath | 电击吐息 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：Galvanic Breath能力引用完整，已复审目标与相连生物电链。 | crawl-ref/source/spl-data.h:3969 |
| spell:SPELL_PILEDRIVER | Maxwell's Portable Piledriver | 麦克斯韦之便携打桩机 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：自己及邻连续敌空间压骤松、推进至末端撞实物、末者伤随距正比齐全。 | crawl-ref/source/spl-data.h:3980 |
| spell:SPELL_GELLS_GAVOTTE | Gell's Gavotte | 盖尔之加沃特 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：四正方向局部重力/视野全体短移、施法者也移动但无碰撞伤/其他未贴新地面受伤、短冷高威力更频繁齐全。 | crawl-ref/source/spl-data.h:3991 |
| spell:SPELL_MAGNAVOLT | Magnavolt | 磁暴 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：磁化金属层、每可见覆碎片目标必中额外电束、无法闪避/揭隐、死留短金属云仍引雷齐全。 | crawl-ref/source/spl-data.h:4002 |
| spell:SPELL_FULSOME_FUSILLADE | Fulsome Fusillade | 猛烈连射 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：数回合每次最多3随机可见敌试剂火冷电毒、重叠更强不可抗伤及可能随机负面、逐回合耗MP、自身安全友方未必齐全。 | crawl-ref/source/spl-data.h:4014 |
| spell:SPELL_RIMEBLIGHT | Rimeblight | 霜疫 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：主及最多两邻魔疫/从内冻、每回忽AC冷伤/发展冰片邻敌/死可传播、活物神圣魔更猛/苦供死灵/濒死快吞遗冥冰齐全。 | crawl-ref/source/spl-data.h:4025 |
| spell:SPELL_HOARFROST_CANNONADE | Hoarfrost Cannonade | 白霜炮击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：两炮远程冰片慢移、短命/每发耗体、未干预存到最后更强齐全。 | crawl-ref/source/spl-data.h:4037 |
| spell:SPELL_SEISMIC_STOMP | Seismic Stomp | 地震践踏 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：重踏裂多近敌地、飞者大减伤/地者可能失足延下次行动齐全。 | crawl-ref/source/spl-data.h:4048 |
| spell:SPELL_HOARFROST_BULLET | Hoarfrost Bullet | 白霜弹 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：冰片覆脆霜慢移、每发损耐久、存活发5次则末发碎射全邻敌额外伤齐全。 | crawl-ref/source/spl-data.h:4059 |
| spell:SPELL_FLASHING_BALESTRA | Flashing Balestra | 闪跃突刺 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：军械库一个魂跳出武攻、独立决斗片刻、回灵魂旋流齐全。 | crawl-ref/source/spl-data.h:4070 |
| spell:SPELL_PHANTOM_BLITZ | Phantom Blitz | 幻影突击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：强力射自身幻象/同武艺法术/即兴幻影夜行可压敌齐全。 | crawl-ref/source/spl-data.h:4081 |
| spell:SPELL_BESTOW_ARMS | Bestow Arms | 赐予武器 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：暂授多名附近盟友军械库魔武器、依赖维系灵魂完整齐全。 | crawl-ref/source/spl-data.h:4092 |
| spell:SPELL_HELLFIRE_MORTAR | Hellfire Mortar | 地狱火迫击炮 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：前方裂地熔岩炮、慢沿裂隙自射岩浆、尽头/生物阻挡沉回、裂隙稍后合齐全。 | crawl-ref/source/spl-data.h:4103 |
| spell:SPELL_SHADOW_SHARD | Shadow Shard | 暗影碎片 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：单敌硬化影碎片齐全。 | crawl-ref/source/spl-data.h:4115 |
| spell:SPELL_SHADOW_BEAM | Shadow Beam | 暗影光束 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透暗影光束齐全。 | crawl-ref/source/spl-data.h:4127 |
| spell:SPELL_SHADOW_BALL | Shadowball | 暗影球 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：闪烁暗影球、小范围爆炸；中文漏闪烁与小范围且换成击中时爆。 | crawl-ref/source/spl-data.h:4139 |
| spell:SPELL_CREEPING_SHADOW | Creeping Shadow | 蔓延暗影 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近墙角出影、邻墙敌受袭；中文把目标缩为仅邻墙角而实际任意可见墙邻敌。 | crawl-ref/source/spl-data.h:4151 |
| spell:SPELL_SHADOW_TEMPEST | Shadow Tempest | 暗影风暴 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：所有可见敌最多一半受不可抗暗雷齐全。 | crawl-ref/source/spl-data.h:4162 |
| spell:SPELL_SHADOW_PRISM | Shadow Prism | 暗影棱镜 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：暗影棱镜短延爆、提前毁威大弱齐全。 | crawl-ref/source/spl-data.h:4173 |
| spell:SPELL_SHADOW_PUPPET | Shadow Puppet | 暗影傀儡 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：活影仆骚扰/缠绕敌、攻击强度直接依威力齐全；缠住可明确挤压以贴constrict。 | crawl-ref/source/spl-data.h:4185 |
| spell:SPELL_SHADOW_TURRET | Shadow Turret | 暗影炮塔 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：固定影炮反复向敌射击齐全。 | crawl-ref/source/spl-data.h:4196 |
| spell:SPELL_SHADOW_SHOT | Shadow Shot | 暗影射击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：单敌小硬化影弹齐全。 | crawl-ref/source/spl-data.h:4207 |
| spell:SPELL_SHADOW_BIND | Shadow Bind | 暗影束缚 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：近随机数敌钉自身影子/短禁移动/威力多目标齐全。 | crawl-ref/source/spl-data.h:4219 |
| spell:SPELL_SHADOW_TORPOR | Shadow Torpor | 暗影麻木 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：一列敌短慢/威力延时/强者更快摆脱齐全。 | crawl-ref/source/spl-data.h:4230 |
| spell:SPELL_SHADOW_DRAINING | Shadow Draining | 暗影吸取 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近所有敌影夺一缕、伤完全忽AC齐全。 | crawl-ref/source/spl-data.h:4242 |
| spell:SPELL_GRAVE_CLAW | Grave Claw | 墓爪 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：骨片指定敌必中/数回合定身、最多存3次、消耗残死/足够活物死亡充能齐全。 | crawl-ref/source/spl-data.h:4253 |
| spell:SPELL_CLOCKWORK_BEE | Launch Clockwork Bee | 发射发条蜜蜂 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：数回合造上弦蜂/快强/攻击耗弦至不能动、移入花1MP修补重上、威力增休眠前攻击数齐全。 | crawl-ref/source/spl-data.h:4264 |
| spell:SPELL_SPIKE_LAUNCHER | Construct Spike Launcher | 构建尖刺发射器 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：相邻墙内陷阱、反复随机刺邻敌、多数伤免疫、离附近解体齐全。 | crawl-ref/source/spl-data.h:4275 |
| spell:SPELL_KINETIC_GRAPNEL | Kinetic Grapnel | 动力抓钩 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：近战武器动能丝射近敌、命中有伤嵌入、下一次对其近战必中/少杀伤加成齐全。 | crawl-ref/source/spl-data.h:4286 |
| spell:SPELL_DIAMOND_SAWBLADES | Diamond Sawblades | 钻石锯片 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：最多四片、固定围绕位置、数回合攻击各自邻敌齐全。 | crawl-ref/source/spl-data.h:4297 |
| spell:SPELL_SHRED | Shred | 撕裂 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：原地旋/锯齿身/邻敌重伤齐全。 | crawl-ref/source/spl-data.h:4308 |
| spell:SPELL_SURPRISING_CROCODILE | Eringya's Surprising Crocodile | 埃林吉亚之意外鳄鱼 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：利齿鳄鱼袭邻敌、脚下水涌、强化一击/拖目标及施法者后退、施法者安全下骑在鳄后、鳄在禁重施齐全。 | crawl-ref/source/spl-data.h:4319 |
| spell:SPELL_PLATINUM_PARAGON | Platinum Paragon | 白金典范 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：额外攻击仅要求玩家看见典范且它有可打目标；&lt;=2距离仅限制替玩家招架。中文把足够近提前到整句，错误扩大限制。其余全魔抗/神器复制/落地冲击/攻击充能/过载广域增伤自毁均保留。 | crawl-ref/source/spl-data.h:4330 |
| spell:SPELL_WALKING_ALEMBIC | Alistair's Walking Alembic | 阿利斯泰尔之行走蒸馏器 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：移动战斗炼金厂、近战摩擦酿药、拳目标排毒副产云、热量够则附近友军得成药并解体齐全。 | crawl-ref/source/spl-data.h:4341 |
| spell:SPELL_MONARCH_BOMB | Forge Monarch Bomb | 锻造君主炸弹 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：飞行燃烧厂集束弹、近布远射、小弹不自行攻击只追敌、任何造物仍在重施引爆全部、邻接混合火/物伤且自身免齐全。 | crawl-ref/source/spl-data.h:4352 |
| spell:SPELL_DEPLOY_BOMBLET | Launch Bomblet | 发射小型炸弹 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：抛物弹忽射线、射程单敌小伤/其旁部署弹、邻敌或附近无空不可齐全。 | crawl-ref/source/spl-data.h:4363 |
| spell:SPELL_SPLINTERFROST_SHELL | Splinterfrost Shell | 碎霜之壳 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：半圆强化冰壳/尽可能推生物让位、耐久/毁一段反射冰弹给破坏者、施法者离远快融齐全；空间允许可非阻断拓为如有可能。 | crawl-ref/source/spl-data.h:4374 |
| spell:SPELL_PERCUSSIVE_TEMPERING | Nazja's Percussive Tempering | 纳兹亚之冲击淬炼 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：限自己锻造系所造构装、修补暂增攻/邻敌副伤/同目标禁重施至结束齐全；锻造术可建议明确学派锻造系。 | crawl-ref/source/spl-data.h:4385 |
| spell:SPELL_ALL_PURPOSE_TEMPERING | Nazja's All-Purpose Tempering | 纳兹亚之通用淬炼 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：魔锤任意附近构装/修补暂增攻、魔像甲虫舞武含、火花渣震波伤目标邻敌、加成在不可重施齐全。 | crawl-ref/source/spl-data.h:4396 |
| spell:SPELL_FORTRESS_BLAST | Fortress Blast | 堡垒冲击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：自身物理强度生成大面积动能波、锁数回合但可别动、期间移位取消、威力加快/伤仅AC齐全。 | crawl-ref/source/spl-data.h:4408 |
| spell:SPELL_SUMMON_SEISMOSAURUS_EGG | Summon Seismosaurus Egg | 召唤地震龙蛋 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：将孵蛋/近有可见敌且施法者始邻才数回孵、坚如山幼体/足踏非飞伤和可能失足、威力增蛋耐久和龙强不减孵时齐全。 | crawl-ref/source/spl-data.h:4419 |
| spell:SPELL_PHALANX_BEETLE | Forge Phalanx Beetle | 锻造方阵甲虫 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：小守卫邻创者加AC、可咬敌但不主动离/分离优先返、威力加AC及耐久齐全。 | crawl-ref/source/spl-data.h:4430 |
| spell:SPELL_RENDING_BLADE | Rending Blade | 撕裂之刃 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：魔力裂刃、己每近战中则穿旁敌不可抗伤、暂抽全部剩MP/消失立即返、每点增伤齐全。 | crawl-ref/source/spl-data.h:4441 |
| spell:SPELL_MAGMA_BARRAGE | Magma Barrage | 岩浆弹幕 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：至多两个不同敌/穿熔岩箭/半伤忽火抗齐全。 | crawl-ref/source/spl-data.h:4452 |
| spell:SPELL_VEX | Vex | 激怒 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：无谓挫败遮心/数回仅攻邻格包括空/盟友齐全。 | crawl-ref/source/spl-data.h:4463 |
| spell:SPELL_RAVENOUS_SWARM | Ravenous Swarm | 饥渴蝠群 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标周围蝙蝠洪/啃一切非亡灵/最终可睡易猎齐全。 | crawl-ref/source/spl-data.h:4475 |
| spell:SPELL_DOMINATE_UNDEAD | Dominate Undead | 支配亡灵 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：附近未效忠亡灵改阵营、固执冒险者不完全受控/随机打敌友、法术期结束恢复/施法者死可提前解；中文省略恢复理智为时限可推。 | crawl-ref/source/spl-data.h:4487 |
| spell:SPELL_DETONATION_CATALYST | Detonation Catalyst | 引爆催化剂 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：拳或近战附催化剂、每主目标火爆、自己友军免、持续攻击可无限续/其他动作快衰、武器基础伤害和威力增爆伤齐全。 | crawl-ref/source/spl-data.h:4498 |
| spell:SPELL_RUST_BREATH | Rust Breath | 锈蚀吐息 | keep | 当前锈云持续腐蚀/削弱，锈蚀吐息准确；不与普通元素酸喷吐混同。 | crawl-ref/source/spl-data.h:4509 |
| spell:SPELL_GOLDEN_BREATH | Golden Breath | 金龙吐息 | keep | 当前同时火/寒束及毒云，金龙吐息复用金龙元素组合而非新增金属伤。 | crawl-ref/source/spl-data.h:4520 |
| spell:SPELL_SPHINX_SISTERS | Sphinx Sisters | 斯芬克斯姐妹 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：一守卫一劫掠斯芬克斯/谜题意象/诅咒削弱及狂风攻击、威力增耐久及施法威力齐全。 | crawl-ref/source/spl-data.h:4531 |
| spell:SPELL_ILL_OMEN | Ill Omen | 凶兆 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：大量厄运、目标间有任意阻碍不可齐全。 | crawl-ref/source/spl-data.h:4542 |
| spell:SPELL_DOOM_BOLT | Doom Bolt | 厄运箭 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：穿透诅咒恶意、造成厄运状态齐全。 | crawl-ref/source/spl-data.h:4553 |
| spell:SPELL_WARP_BODY | Warp Body | 扭曲身体 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：诱变腐化体/小伤一短变异、已有多暂变则玻化齐全；诱发变异是自然展开同义，不作术语硬错。 | crawl-ref/source/spl-data.h:4564 |
| spell:SPELL_OSTRACISE | Ostracise | 排斥 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标有效虔诚暂降/所需神能禁、叠降不直接逐出、经验逐恢复全部旧虔诚齐全。 | crawl-ref/source/spl-data.h:4576 |
| spell:SPELL_MUTAGENIC_GAZE | Mutagenic Gaze | 变异凝视 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标积诱变能至有害变异/能爆、需视线不需射线齐全；正文变异能量违D-C096明确限定。 | crawl-ref/source/spl-data.h:4587 |
| spell:SPELL_ACID_BALL | Acid Ball | 酸液球 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：投掷、爆炸、腐蚀酸液球三义齐全；非无酸性普通弹丸。 | crawl-ref/source/spl-data.h:4598 |
| spell:SPELL_NO_SPELL | nonexistent spell | 不存在的法术 | keep | 内部nonexistent spell/Melee占位显示与不存在法术/近战语义匹配；没有独立玩家法术效果可补写。 | crawl-ref/source/spl-data.h:4609 |
| spell:SPELL_PYRRHIC_RECOLLECTION | Pyrrhic Recollection | 惨胜回忆 | keep | 描述专用dummy名称与对应展示效果一致；不将其当作另一个玩家可记忆法术。 正文关联：无名者环记忆点燃/暂强法术知识与治疗/显著伤熄/余记忆尚有则无名者不永久死；它们代词可误指记忆，宜重述无名者。 | crawl-ref/source/spl-data.h:4621 |
| spell:SPELL_PLANAR_OVERLAY | Planar Overlay | 位面叠加 | keep | 描述专用dummy名称与对应展示效果一致；不将其当作另一个玩家可记忆法术。 正文关联：邻现实叠/随机本地怪在同层其他处、首批多/后慢稳/很久后可近玩家齐全。 | crawl-ref/source/spl-data.h:4632 |
| spell:SPELL_DOOMSAYING | Doomsaying | 宣告厄运 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：至100%差额一半厄运、施法者死触本层隐敌寻位及全楼梯暂封、仅一次/睡中杀亦不避齐全。 | crawl-ref/source/spl-data.h:4643 |
| spell:SPELL_SLEETSTRIKE | Sleetstrike | 冰雨打击 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标周围冷气旋/短冰封慢移、空旷增伤/半伤忽寒抗齐全。 | crawl-ref/source/spl-data.h:4654 |
| spell:SPELL_LANDBREAKER | Landbreaker | 裂地 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：裂地砸数敌及身后地面、阻逃施法者路径齐全。 | crawl-ref/source/spl-data.h:4665 |
| spell:SPELL_STAMPEDE | Stampede | 奔踏 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：直冲敌、后每回双速/增伤增命中推途敌、不能移动或越目标即止/需八方位齐全。 | crawl-ref/source/spl-data.h:4676 |
| spell:SPELL_BOLSTER | Bolster | 强化 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：自身物理强化、近战伤及全元素抗性大增齐全。 | crawl-ref/source/spl-data.h:4687 |
| spell:SPELL_PHASE_SHIFT | Phase Shift | 相位变换 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：自身相位偏离模糊位置/无超视者难中且不见伤势齐全；同title多个定义不凭重名判错。 | crawl-ref/source/spl-data.h:4698 |
| spell:SPELL_DRAGON_VEINS | Dragon Veins | 龙脉 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：最多四邻地龙脉、西火东冰北气南土、1MP最多3随机敌；火最少HP/杀留火云、冰最多HP/短减速、气最远/远仍全伤、土最近/少1目标/飞行减伤/近可能踉跄、最多踏2脉齐全。 | crawl-ref/source/spl-data.h:4709 |
| spell:SPELL_DRAGON_VEIN_FIRE | Dragon Vein (Fire) | 龙脉（火） | keep | 龙脉火分支：优先低HP，击杀火云。 | crawl-ref/source/spl-data.h:4720 |
| spell:SPELL_DRAGON_VEIN_ICE | Dragon Vein (Ice) | 龙脉（冰） | keep | 龙脉冰分支：优先高HP并冰封慢移。 | crawl-ref/source/spl-data.h:4731 |
| spell:SPELL_DRAGON_VEIN_AIR | Dragon Vein (Air) | 龙脉（气） | keep | 龙脉气分支：优先远敌且远距不减伤。 | crawl-ref/source/spl-data.h:4742 |
| spell:SPELL_DRAGON_VEIN_EARTH | Dragon Vein (Earth) | 龙脉（土） | keep | 龙脉土分支：优先近敌、2目标、飞行减伤与近距踉跄。 | crawl-ref/source/spl-data.h:4753 |
| spell:SPELL_ICE_THORNS | Ice Thorns | 冰棘 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：目标敌周围冰棘环、非飞踏伤后碎、自踏无伤仍碎齐全。 | crawl-ref/source/spl-data.h:4764 |
| spell:SPELL_SIROCCO | Sirocco | 灼热风 | keep | 已独立比较原名的动作/对象/材质/方向/范围/专名与完整正文、当前分派及定义。此名称在对应语境可成立；既有glossary映射仅用于一致性，不充当语义通过理由。 正文关联：至多3邻生物火伤吹退/后数回快移副效、数回禁再施/移动延充能齐全。 | crawl-ref/source/spl-data.h:4776 |
| spell:SPELL_AURA_OF_ABJURATION | Aura of Abjuration | 驱逐灵气 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4790 |
| spell:SPELL_BOLT_OF_INACCURACY | Bolt of Inaccuracy | 偏差箭矢 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4791 |
| spell:SPELL_CHANT_FIRE_STORM | Chant Fire Storm | 咏唱火焰风暴 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4792 |
| spell:SPELL_CIGOTUVIS_DEGENERATION | Cigotuvi's Degeneration | 西格图维之退化 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4793 |
| spell:SPELL_CIGOTUVIS_EMBRACE | Cigotuvi's Embrace | 西格图维之拥抱 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4794 |
| spell:SPELL_CONDENSATION_SHIELD | Condensation Shield | 凝结护盾 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4795 |
| spell:SPELL_CONTROLLED_BLINK | Controlled Blink | 受控闪烁 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4796 |
| spell:SPELL_CONTROL_TELEPORT | Control Teleport | 控制传送 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4797 |
| spell:SPELL_CONTROL_UNDEAD | Control Undead | 控制亡灵 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4798 |
| spell:SPELL_CONTROL_WINDS | Control Winds | 控风术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4799 |
| spell:SPELL_CORRUPT_BODY | Corrupt Body | 腐化躯体 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4800 |
| spell:SPELL_CURE_POISON | Cure Poison | 解毒术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4801 |
| spell:SPELL_DARKNESS | Darkness | 黑暗术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4802 |
| spell:SPELL_OLD_DEFLECT_MISSILES | Old Deflect Missiles | 旧版偏转飞弹 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4803 |
| spell:SPELL_DELAYED_FIREBALL | Delayed Fireball | 延迟火球 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4804 |
| spell:SPELL_DEMONIC_HORDE | Demonic Horde | 恶魔大军 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4805 |
| spell:SPELL_DRACONIAN_BREATH | Draconian Breath | 龙人吐息 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4806 |
| spell:SPELL_EPHEMERAL_INFUSION | Ephemeral Infusion | 短暂灌注 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4807 |
| spell:SPELL_EVAPORATE | Evaporate | 蒸发术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4808 |
| spell:SPELL_EXPLOSIVE_BOLT | Explosive Bolt | 爆裂弩矢 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4809 |
| spell:SPELL_FAKE_RAKSHASA_SUMMON | Rakshasa Summon | 召唤罗刹 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4810 |
| spell:SPELL_FIRE_BRAND | Fire Brand | 火焰烙印 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4811 |
| spell:SPELL_FLY | Flight | 飞行术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4812 |
| spell:SPELL_FORCEFUL_DISMISSAL | Forceful Dismissal | 强制驱逐 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4813 |
| spell:SPELL_FREEZING_AURA | Freezing Aura | 冰封灵气 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4814 |
| spell:SPELL_FRENZY | Frenzy | 狂乱术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4815 |
| spell:SPELL_FULSOME_DISTILLATION | Fulsome Distillation | 精华蒸馏 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4816 |
| spell:SPELL_GRAND_AVATAR | Grand Avatar | 大化身 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4817 |
| spell:SPELL_HASTE_PLANTS | Haste Plants | 加速植物 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4818 |
| spell:SPELL_HOLY_LIGHT | Holy Light | 圣光术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4819 |
| spell:SPELL_HUNTING_CRY | Hunting Cry | 狩猎战吼 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4820 |
| spell:SPELL_IGNITE_POISON_SINGLE | Localized Ignite Poison | 局部引爆毒素 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4821 |
| spell:SPELL_INSULATION | Insulation | 绝缘术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4822 |
| spell:SPELL_INFUSION | Infusion | 灌注术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4823 |
| spell:SPELL_IRON_ELEMENTALS | Summon Iron Elementals | 召唤铁元素 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4824 |
| spell:SPELL_LETHAL_INFUSION | Lethal Infusion | 致命灌注 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4825 |
| spell:SPELL_MELEE | Melee | 近战 | keep | 内部nonexistent spell/Melee占位显示与不存在法术/近战语义匹配；没有独立玩家法术效果可补写。 | crawl-ref/source/spl-data.h:4826 |
| spell:SPELL_MISLEAD | Mislead | 误导术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4827 |
| spell:SPELL_PHASE_SHIFT_OLD | Phase Shift | 相位变换 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 正文关联：自身相位偏离模糊位置/无超视者难中且不见伤势齐全；同title多个定义不凭重名判错。 | crawl-ref/source/spl-data.h:4828 |
| spell:SPELL_POISON_WEAPON | Poison Weapon | 淬毒武器 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4829 |
| spell:SPELL_RANDOM_BOLT | Random Bolt | 随机箭矢 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4830 |
| spell:SPELL_REARRANGE_PIECES | Rearrange the Pieces | 重新布局 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4831 |
| spell:SPELL_RECALL | Recall | 召回术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4832 |
| spell:SPELL_REGENERATION | Regeneration | 再生 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4833 |
| spell:SPELL_RING_OF_FLAMES | Ring of Flames | 烈焰之环 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4834 |
| spell:SPELL_SEE_INVISIBLE | See Invisible | 识破隐形 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4835 |
| spell:SPELL_SHAFT_SELF | Shaft Self | 自掘竖井 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4836 |
| spell:SPELL_SHROUD_OF_GOLUBRIA | Shroud of Golubria | 戈卢布里亚之幕 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4837 |
| spell:SPELL_SILVER_BLAST | Silver Blast | 白银冲击 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4838 |
| spell:SPELL_SINGULARITY | Singularity | 奇点术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4839 |
| spell:SPELL_SONG_OF_SHIELDING | Song of Shielding | 护盾之歌 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4840 |
| spell:SPELL_SPECTRAL_WEAPON | Spectral Weapon | 灵体武器 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4841 |
| spell:SPELL_STONESKIN | Stoneskin | 石肤术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4842 |
| spell:SPELL_SUMMON_BUTTERFLIES | Summon Butterflies | 召唤蝴蝶 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4843 |
| spell:SPELL_SUMMON_ELEMENTAL | Summon Elemental | 召唤元素 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4844 |
| spell:SPELL_SUMMON_RAKSHASA | Summon Rakshasa | 召唤罗刹 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4845 |
| spell:SPELL_SUMMON_TWISTER | Summon Twister | 召唤旋风 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4846 |
| spell:SPELL_SUNRAY | Sunray | 阳光射线 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4847 |
| spell:SPELL_SURE_BLADE | Sure Blade | 精准之刃 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4848 |
| spell:SPELL_THROW | Throw | 投掷 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4849 |
| spell:SPELL_VAMPIRE_SUMMON | Vampire Summon | 召唤吸血鬼 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4850 |
| spell:SPELL_WARP_BRAND | Warp Weapon | 扭曲武器 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4851 |
| spell:SPELL_WEAVE_SHADOWS | Weave Shadows | 编织暗影 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4852 |
| spell:SPELL_STRIKING | Striking | 打击术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4853 |
| spell:SPELL_RESURRECT | Resurrect | 复活术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4854 |
| spell:SPELL_HOLY_WORD | Holy word | 圣言术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4855 |
| spell:SPELL_SACRIFICE | Sacrifice | 献祭 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4856 |
| spell:SPELL_MIASMA_CLOUD | Miasma cloud | 瘴气云 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4857 |
| spell:SPELL_POISON_CLOUD | Poison cloud | 毒气云 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4858 |
| spell:SPELL_FIRE_CLOUD | Fire cloud | 火云 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4859 |
| spell:SPELL_STEAM_CLOUD | Steam cloud | 蒸汽云 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4860 |
| spell:SPELL_HOMUNCULUS | Homunculus | 人造人 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4861 |
| spell:SPELL_SERPENT_OF_HELL_BREATH_REMOVED | Old serpent of hell breath | 地狱古蛇吐息 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4862 |
| spell:SPELL_SCATTERSHOT | Scattershot | 散射术 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4863 |
| spell:SPELL_SUMMON_SWARM | Summon swarm | 召唤虫群 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4864 |
| spell:SPELL_CLOUD_CONE | Cloud Cone | 云雾锥 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4865 |
| spell:SPELL_RING_OF_THUNDER | Ring of Thunder | 雷霆之环 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4866 |
| spell:SPELL_TWISTED_RESURRECTION | Twisted Resurrection | 扭曲复活 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4867 |
| spell:SPELL_RANDOM_EFFECTS | Random Effects | 随机效果 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4868 |
| spell:SPELL_HYDRA_FORM | Hydra Form | 多头蛇变形 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4869 |
| spell:SPELL_VORTEX | Vortex | 漩涡 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4870 |
| spell:SPELL_GOAD_BEASTS | Goad Beasts | 激怒野兽 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4871 |
| spell:SPELL_TELEPORT_SELF | Teleport Self | 自我传送 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4872 |
| spell:SPELL_TOMB_OF_DOROKLOHE | Tomb of Doroklohe | 多洛克洛之墓 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4873 |
| spell:SPELL_EXCRUCIATING_WOUNDS | Excruciating Wounds | 剧痛之伤 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4874 |
| spell:SPELL_CONJURE_FLAME | Conjure Flame | 召唤火焰 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4875 |
| spell:SPELL_CORPSE_ROT | Corpse Rot | 尸体腐烂 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4876 |
| spell:SPELL_FLAME_TONGUE | Flame Tongue | 火焰之舌 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4877 |
| spell:SPELL_BEASTLY_APPENDAGE | Beastly Appendage | 野兽肢体 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4878 |
| spell:SPELL_SPIDER_FORM | Spider Form | 蜘蛛变形 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4879 |
| spell:SPELL_ICE_FORM | Ice Form | 寒冰变形 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4880 |
| spell:SPELL_BLADE_HANDS | Blade Hands | 利刃之手 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4881 |
| spell:SPELL_STATUE_FORM | Statue Form | 石像变形 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4882 |
| spell:SPELL_STORM_FORM | Storm Form | 风暴变形 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4883 |
| spell:SPELL_DRAGON_FORM | Dragon Form | 巨龙变形 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4884 |
| spell:SPELL_NECROMUTATION | Necromutation | 亡灵变形 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4885 |
| spell:SPELL_AWAKEN_EARTH | Awaken Earth | 唤醒大地 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4886 |
| spell:SPELL_ANIMATE_SKELETON | Animate Skeleton | 操纵骷髅 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 | crawl-ref/source/spl-data.h:4887 |
| spell:SPELL_DRAIN_MAGIC | Drain Magic | 汲取魔力 | defer terminology | 此精确枚举是AXED兼容记录；已阅读旧标题的修饰语与族根，但无现行行为可支撑改名。AXED占位level=7不是其历史真实等级，不能据此评分或推出威力。 延期理由：Removed compatibility spell has no current semantics to adjudicate a rename; do not infer from similarly named modern spells.；责任：future restoration implementer + sole zh-translator；重入：Restore this exact enum or change its retained localized surface.；保留原值见中文列。 正文关联：魔力泄空如反魔武器齐全。 | crawl-ref/source/spl-data.h:4888 |

### 专用动态说明
| 身份 | 英文源名／源键 | 当前中文／采用内容 | 终态 | 理由、发现与处理 | 证据 |
|---|---|---|---|---|---|
| spell-help:47c1d9884ec99aad | spell miscast&#124;Miscasting this spell causes magic contamination and may %s.\n | 此法术施法失误会造成诱变辐射，并可能%s。\n | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5225 |
| spell-help:04329f3c77f0f9e1 | spell miscast&#124;Miscasting this spell causes magic contamination.\n | 此法术施法失误会造成诱变辐射。\n | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5229 |
| spell-help:3882db29cc6a4916 | Miscasting this spell causes magic contamination | 施放失败会导致魔法污染 | keep | 此翻译键属于非ZH分支旧英文碎片；当前ZH路径使用独立spell miscast上下文完整句，因此不能把该旧键的失误/失败或污染措辞当成此sink的已证实当前缺陷。 | crawl-ref/source/describe.cc:5233 |
| spell-help:525939a0efc1dcde |  and also  | 并可能造成 | keep | 此翻译键属于非ZH分支旧英文碎片；当前ZH路径使用独立spell miscast上下文完整句，因此不能把该旧键的失误/失败或污染措辞当成此sink的已证实当前缺陷。 | crawl-ref/source/describe.cc:5235 |
| spell-help:22dc194cc2136db3 | .\n | 。\n | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5236 |
| spell-help:444674d983c3f680 | Your battlesphere is not activated by any of your spells.\n / Your battlesphere fires when you cast %s.\n | 你的任何法术都无法激活你的战斗法球。\n / 你施放%s时，你的战斗法球会开火。\n | adjust | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 旧碎片本身无独立语义错误，随完整模板迁移退休；同组替代与关闭证据见 spell-help:a5ab9295c8156050。 | crawl-ref/source/describe.cc:5244 |
| spell-help:4bab73151855d096 | Your battlesphere is not activated by any of your spells.\n / Your battlesphere fires when you cast %s.\n | 你的任何法术都无法激活你的战斗法球。\n / 你施放%s时，你的战斗法球会开火。\n | adjust | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 旧碎片本身无独立语义错误，随完整模板迁移退休；同组替代与关闭证据见 spell-help:a5ab9295c8156050。 | crawl-ref/source/describe.cc:5246 |
| spell-help:a5ab9295c8156050 | Your battlesphere is not activated by any of your spells.\n / Your battlesphere fires when you cast %s.\n | 你的任何法术都无法激活你的战斗法球。\n / 你施放%s时，你的战斗法球会开火。\n | adjust | 实际完整拼接“你的战斗法球会在你施放&lt;法术列表&gt;。”缺“时开火”谓语；不能孤立说此碎片正确。 本批已修复并复核：战斗法球动态触发条件拼成病句。 | crawl-ref/source/describe.cc:5249 |
| spell-help:e1a3e78cb5c88586 |  or  | 或 | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5253 |
| spell-help:224c7229367e69f3 | Your servitor | 你的仆从 | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5261 |
| spell-help:41ce1dbd93772a26 |  is unable to mimic any of your spells | 无法模仿你的任何法术 | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5263 |
| spell-help:722c421e3a0c9cf5 |  casts  | 会施放 | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5265 |
| spell-help:1b979ae0dd431ffd | Your paragon wields  | 你的典范持有 | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5272 |
| spell-help:f564872bbd4dcb0d | Your servitor can be imbued with this spell.\n | 你的仆从可以被赋予此法术。\n | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5281 |
| spell-help:63735e3cf1cb3783 | Your servitor could be imbued with this spell if your spell success rate were higher.\n | 如果你的法术成功率更高，你的仆从就可以被赋予这个法术。\n | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5283 |
| spell-help:40761c8ecd7aac56 | This inflicts up to 40% magical contamination when cast by you.\n | 由你施放时，此法术会造成至多40%的诱变辐射。\n | adjust | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 本批已修复并复核：Irradiate专用尾句术语和百分号显示。 | crawl-ref/source/describe.cc:5287 |
| spell-help:36d752cc5f3e07c3 | You can sustain at most %s creature summoned by this spell.\n / You can sustain at most %s creatures summoned by this spell.\n / You can sustain at most %s martyred shade summoned by this spell.\n / You can sustain at most %s martyred shades summoned by this spell.\n | 你最多可以维持此法术召唤的%s个生物。\n / 你最多可以维持此法术召唤的%s个生物。\n / 你最多可以维持此法术召唤的%s个殉道暗影。\n / 你最多可以维持此法术召唤的%s个殉道暗影。\n | adjust | 玩家拼接为“你最多可以维持&lt;数量&gt; 个生物 由此法术召唤。”，后置定语导致病句；殉道暗影特殊上限也共用此路径。怪物分支已有完整可翻译模板。 本批已修复并复核：玩家召唤上限说明英语词序直拼。 | crawl-ref/source/describe.cc:5293 |
| spell-help:be2b54e8568daed0 | You can sustain at most %s creature summoned by this spell.\n / You can sustain at most %s creatures summoned by this spell.\n / You can sustain at most %s martyred shade summoned by this spell.\n / You can sustain at most %s martyred shades summoned by this spell.\n | 你最多可以维持此法术召唤的%s个生物。\n / 你最多可以维持此法术召唤的%s个生物。\n / 你最多可以维持此法术召唤的%s个殉道暗影。\n / 你最多可以维持此法术召唤的%s个殉道暗影。\n | adjust | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 旧碎片本身无独立语义错误，随完整模板迁移退休；同组替代与关闭证据见 spell-help:36d752cc5f3e07c3。 | crawl-ref/source/describe.cc:5295 |
| spell-help:f15b06e4f0780798 |  creature |  个生物 | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5295 |
| spell-help:043a718774c572bd | s |  | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5296 |
| spell-help:b80fda684d0e168e | You can sustain at most %s creature summoned by this spell.\n / You can sustain at most %s creatures summoned by this spell.\n / You can sustain at most %s martyred shade summoned by this spell.\n / You can sustain at most %s martyred shades summoned by this spell.\n | 你最多可以维持此法术召唤的%s个生物。\n / 你最多可以维持此法术召唤的%s个生物。\n / 你最多可以维持此法术召唤的%s个殉道暗影。\n / 你最多可以维持此法术召唤的%s个殉道暗影。\n | adjust | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 旧碎片本身无独立语义错误，随完整模板迁移退休；同组替代与关闭证据见 spell-help:36d752cc5f3e07c3。 | crawl-ref/source/describe.cc:5297 |
| spell-help:8efb9e099439a0b0 |  supports the use of this spell.\n |  赞成使用这个法术。\n | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5303 |
| spell-help:62c147f1c9564139 | This spell is empowered while you are enkindled.\n | 此法术在点燃状态下得到强化。\n | adjust | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 本批已修复并复核：Enkindled状态旧名。 | crawl-ref/source/describe.cc:5307 |
| spell-help:50bdca1bc7d86b80 | \nYou cannot cast this spell: %s\n | \n你无法施放此法术：%s\n | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5312 |
| spell-help:c1e8f4fd81cd4df6 | \nYou cannot memorise this spell: %s\n | \n你无法记忆此法术：%s\n | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5314 |
| spell-help:ad56d88e68b58a71 | This spell would have no effect right now because  | <br>此法术当前不会产生任何效果，因为  | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5329 |
| spell-help:b53ab23816efa4e0 | \nYou have harvested enough death to cast this spell %d time. (Maximum of %d.) | \n你已收割了足够的死亡能量，可以施放此法术%d次。（最多%d次。） | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5337 |
| spell-help:4a980c6fb84b589c | \nYou have harvested enough death to cast this spell %d times. (Maximum of %d.) | \n你已收割了足够的死亡能量，可以施放此法术%d次。（最多%d次。） | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5339 |
| spell-help:03444556f65c49b1 | This spell has no description. Casting it may therefore be unwise.  | <br>此法术没有描述。因此施放此法术可能并非明智之举。 | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5383 |
| spell-help:d4c776c6971045e3 | Better go fix it. | 不如去修复它。 | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5385 |
| spell-help:8519267d123bc9f1 | Please submit a bug report. | 请提交一个错误报告。 | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5387 |
| spell-help:874b2e4beddf7fef | \n%s creates living %s spells.\n | \n%s创造活体%s法术。\n | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5396 |
| spell-help:cf67b46d96ea555c | \nIf you are struck by this, you will no longer be %s.\n | \n如果你被此击中，你将不再%s。\n | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5404 |
| spell-help:5bb9b662ad2f5b65 | \nYou currently have no enchantments that could be removed by this.\n | \n你目前没有任何可以以此移除的附魔。\n | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5409 |
| spell-help:d8803aef9539ab04 | \nRange :  | \n范围： | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5420 |
| spell-help:6820c84131cb8b5c | \nDefences :  | \n防御 :  | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5426 |
| spell-help:ae6fac2f299fe6fc | \nResists :  | \n抗性 :  | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5428 |
| spell-help:acbc4199b3fb0fe6 | \n\n&lt;magenta&gt;This spell cannot be performed via Aphotic Marionette.&lt;/magenta&gt;\n | \n\n&lt;magenta&gt;此法术无法通过无光傀儡施放。&lt;/magenta&gt;\n | adjust | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 本批已修复并复核：Aphotic Marionette能力旧名。 | crawl-ref/source/describe.cc:5434 |
| spell-help:4c51cfa811646577 | \n\n&lt;magenta&gt;When cast via Aphotic Marionette, this spell will affect the player instead.&lt;/magenta&gt;\n | \n\n&lt;magenta&gt;通过无光傀儡施放时，此法术将转而对你生效。&lt;/magenta&gt;\n | adjust | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 本批已修复并复核：Aphotic Marionette名称及效果对象错误。 | crawl-ref/source/describe.cc:5439 |
| spell-help:e3651a63b5fac9e2 | %s can sustain at most %s creature summoned by this spell.\n | %s最多能维持该法术召唤的%s个生物。\n | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5451 |
| spell-help:bb20ddb48c0f6b34 | %s can sustain at most %s creatures summoned by this spell.\n | %s最多能维持该法术召唤的%s个生物。\n | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5455 |
| spell-help:8336ed449f0502aa |  (pow %d) | （威力%d） | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5477 |
| spell-help:b990612fa778a903 | You cannot be affected by this spell right now. %s\n | 你目前无法受到此法术的影响。%s\n | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5480 |
| spell-help:d9ab484987a82470 | Chance to defeat your Will: %d%%%s\n | 击破你意志的几率：%d%%%s\n | keep | 在实际拼接/分支中比较完整说明：施法失误、法术球/仆从/典范、灌注资格、召唤上限、神祇、燃魂、记忆限制、墓爪次数、怪物专用说明与意志检定等；格式token仅保留事实，不作代码安全结论。 | crawl-ref/source/describe.cc:5483 |

### 实施边界与证据复用
Brothers in Arms 的玩家能力仍保留真实经验等级缩放，怪物法术改用独立 EN/ZH 正文；四项召唤保留一只或多只及类型任选的实际范围。半护甲与半抗性伤害、缠绕挤压、移动后遗症、衰竭生命上限等按原卡实现证据核对。法术球及召唤上限改用完整模板，Irradiate 的百分号按直接文本输出处理，Aphotic 的对象为玩家且标记完整闭合。
现有专用动态清单中的旧碎片身份保留作为迁移来源；替代完整模板在同一卡列出，不将一个旧碎片误称为多个新审查身份。未变的通用复数后缀和句号片段不机械删除。完整逐键动作、原始失败与复核日志位于本批验证目录；静态文本与 Lua 检查不等同实际游戏运行。
Receive Forbidden Knowledge 所依赖的 Infestation 时限错误已修复；其他关联正文复用本轮新审证据。Repeat Exegesis 的完整定义／正文集合已审，但无独立正文的身份仍按原卡保留，不夸大运行覆盖。当前实施后终态：{"adjust": 72, "defer terminology": 99, "keep": 808}。
