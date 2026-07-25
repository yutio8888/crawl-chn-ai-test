# 法术名称逐项复审结果

本文件是 `docs/spell-name-review-plan.md` 的证据记录，不是术语权威。
通用术语以 `docs/glossary.md` 为准，具体命名裁定以
`docs/decisions.md` 为准。

冻结基线：`5cb9aa27a224a81da780757f8445cfc07de09dfd`

术语上下文 SHA-256：
`1af737231c2c1287c9cc3f3bb34cfa3890138ae2553c955c73db70b41701df3f`

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
| `SPELL_BOLT_OF_INACCURACY` | 已移除兼容 | 偏差箭矢 | 证据不足 | 暂沿用偏差箭矢 | 暂缓高 |
| `SPELL_BOLT_OF_LIGHT` | 现行 | 光箭 | 保留 | 光箭 | 高 |
| `SPELL_BOLT_OF_MAGMA` | 现行 | 岩浆箭 | 保留 | 岩浆箭 | 高 |
| `SPELL_CORROSIVE_BOLT` | 现行 | 腐蚀箭 | 保留 | 腐蚀箭 | 高 |
| `SPELL_DOOM_BOLT` | 现行 | 厄运箭 | 保留 | 厄运箭 | 高 |
| `SPELL_ELECTRICAL_BOLT` | 现行 | 电击箭 | 保留 | 电击箭 | 高 |
| `SPELL_EXPLOSIVE_BOLT` | 已移除兼容 | 爆裂弩矢 | 证据不足 | 暂沿用爆裂弩矢 | 暂缓高 |
| `SPELL_LIGHTNING_BOLT` | 现行 | 闪电箭 | 保留 | 闪电箭 | 高 |
| `SPELL_QUICKSILVER_BOLT` | 现行 | 水银箭 | 保留 | 水银箭 | 高 |
| `SPELL_RANDOM_BOLT` | 已移除兼容 | 随机箭矢 | 证据不足 | 暂沿用随机箭矢 | 暂缓高 |
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
| `SPELL_MIASMA_CLOUD` | 已移除兼容 | 瘴气云 | 证据不足 | 暂沿用瘴气云 | 暂缓高 |
| `SPELL_POISON_CLOUD` | 已移除兼容 | 毒气云 | 证据不足 | 暂沿用毒气云 | 暂缓高 |
| `SPELL_FIRE_CLOUD` | 已移除兼容 | 火云 | 证据不足 | 暂沿用火云 | 暂缓高 |
| `SPELL_STEAM_CLOUD` | 已移除兼容 | 蒸汽云 | 证据不足 | 暂沿用蒸汽云 | 暂缓高 |
| `SPELL_CLOUD_CONE` | 已移除兼容 | 云雾锥 | 证据不足 | 暂沿用云雾锥 | 暂缓高 |

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
| `SPELL_CALL_DOWN_DAMNATION` | 9 / 塑能 / `target, unholy, needs_tracer, monster` | 怪物 | 降下天谴 | 降下天谴 | 保留 |
| `SPELL_CALL_DOWN_LIGHTNING` | 4 / 塑能、气 / `target, monster` | 怪物 | 降下闪电 | 降下闪电 | 保留 |
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

## Summon 词形系列（进行中）

边界：英文标题中含独立 `Summon` 词形，共 42 项；其中 34 项现行、
8 项 `TAG_MAJOR_VERSION == 34` 已移除兼容记录。`Call` 系列、`Recall`
以及仅因学派为 Summoning 而不含该标题词形的法术均不在本系列。为遵守
“完整系列审完后再落地”的规则，本节只累计证据；42 项裁定齐备前不修改
本系列标题或关联描述。

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
| `SPELL_SUMMON_MANA_VIPER` | 5 / 召唤、诅咒 / `mons_abjure` | 玩家、怪物 | 召唤魔力蝰蛇 | 保留 | 高 |
| `SPELL_SUMMON_CACTUS` | 6 / 召唤 / `none` | 玩家 | 召唤仙人掌巨人 | 保留 | 高 |
| `SPELL_SUMMON_SEISMOSAURUS_EGG` | 4 / 召唤、土 / `none` | 玩家 | 召唤震龙蛋 | 保留 | 高 |

- `Summon Small Mammal` 召出老鼠、蝙蝠或短尾矮袋鼠，法术威力提高出现
  短尾矮袋鼠的概率；标题完整保留 Small 与实体类别。
- `Summon Horrible Things` 打开通往深渊的门并召来至少两个憎恶，同时
  令施法者承受 Doom 风险；“恐怖之物”忠实于刻意泛称的原名。
- `Summon Ice Beast` 召出强度随法术威力变化的冰兽；标题直接复用实体名。
- `Summon Hydra` 召出短暂作战的多头蛇，法术威力决定头数；标题不需要
  加入持续时间或头数细节。
- `Summon Forest` 将森林位面与当前世界强行交叠，召出森林之灵并唤醒
  树木；虽然效果不只一个生物，“召唤森林”准确保留法术的宏观中心意象。
- `Summon Mana Viper` 召出咬击带反魔法效果的魔力蝰蛇；标题复用实体名。
- `Summon Cactus Giant` 召出会反伤近战攻击者的仙人掌巨人，高威力会
  召来更老练强壮的个体；标题准确。
- `Summon Seismosaurus Egg` 召出需施法者相邻守护数回合才会孵化的震龙蛋；
  标题准确保留对象是“蛋”而非直接召唤震龙。

描述审阅发现两项明确 Needs Fix，暂记录、不提前落地：

- `Summon Horrible Things` 中文仍声称会损失智力，却遗漏当前效果会积累
  Doom 风险。数量随法术威力提高的趋势在实现中仍存在，但当前英文描述
  不再陈述该细节；重译时应删除旧智力机制并完整恢复 Doom 后果。
- `Summon Mana Viper` 的“迅速耗掉敌人几乎所有的魔力”把
  `nearly any foe` 错解为“几乎所有魔力”；应改为该咬击几乎能影响
  任何敌人的魔力储备。

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
