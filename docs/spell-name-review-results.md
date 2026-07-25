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
| `SPELL_SUMMON_GREATER_DEMON` | 召唤高级恶魔 | 重译 | 召唤高等恶魔 | 高 |
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
| `SPELL_FAKE_RAKSHASA_SUMMON` | Rakshasa Summon | 召唤罗刹 | 证据不足，暂沿用 |
| `SPELL_IRON_ELEMENTALS` | Summon Iron Elementals | 召唤铁元素 | 证据不足，暂沿用 |
| `SPELL_SUMMON_BUTTERFLIES` | Summon Butterflies | 召唤蝴蝶 | 证据不足，暂沿用 |
| `SPELL_SUMMON_ELEMENTAL` | Summon Elemental | 召唤元素 | 证据不足，暂沿用 |
| `SPELL_SUMMON_RAKSHASA` | Summon Rakshasa | 召唤罗刹 | 证据不足，暂沿用 |
| `SPELL_SUMMON_TWISTER` | Summon Twister | 召唤旋风 | 证据不足，暂沿用 |
| `SPELL_VAMPIRE_SUMMON` | Vampire Summon | 召唤吸血鬼 | 证据不足，暂沿用 |
| `SPELL_SUMMON_SWARM` | Summon swarm | 召唤虫群 | 证据不足，暂沿用 |

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
| `SPELL_DRACONIAN_BREATH` | 已移除兼容 | 龙人吐息 | 无当前描述或实现 | 证据不足，暂沿用 |
| `SPELL_SERPENT_OF_HELL_BREATH_REMOVED` | 已移除兼容 | 地狱古蛇吐息 | 无当前描述或实现 | 证据不足，暂沿用 |

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
| `SPELL_MAGIC_DART` | 1 / 塑能 / `dir_or_target, needs_tracer` | 玩家、怪物 | 魔法飞弹 | 魔法飞弹 | 保留 |
| `SPELL_SLUG_DART` | 1 / 塑能 / `dir_or_target, needs_tracer, monster` | 飞镖蛞蝓 | 弹丸飞镖 | 蛞蝓飞镖 | 重译 |

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
| `SPELL_RING_OF_FLAMES` | 已移除兼容 | 烈焰之环 | 无当前描述或实现 | 证据不足，暂沿用 |
| `SPELL_CONJURE_FLAME` | 已移除兼容 | 召唤火焰 | 无当前描述或实现 | 证据不足，暂沿用 |
| `SPELL_FLAME_TONGUE` | 已移除兼容 | 火焰之舌 | 无当前描述或实现 | 证据不足，暂沿用 |

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
| `SPELL_HYDRA_FORM` | 已移除兼容 | 多头蛇变形 | 无当前描述或实现 | 证据不足，暂沿用 |
| `SPELL_SPIDER_FORM` | 已移除兼容 | 蜘蛛变形 | 无当前描述或实现 | 证据不足，暂沿用 |
| `SPELL_ICE_FORM` | 已移除兼容 | 寒冰变形 | 无当前描述或实现 | 证据不足，暂沿用 |
| `SPELL_STATUE_FORM` | 已移除兼容 | 石像变形 | 无当前描述或实现 | 证据不足，暂沿用 |
| `SPELL_STORM_FORM` | 已移除兼容 | 风暴变形 | 无当前描述或实现 | 证据不足，暂沿用 |
| `SPELL_DRAGON_FORM` | 已移除兼容 | 巨龙变形 | 无当前描述或实现 | 证据不足，暂沿用 |

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
| `SPELL_CURE_POISON` | 已移除兼容 | 解毒术 | 无当前描述或实现 | 证据不足，暂沿用 |
| `SPELL_IGNITE_POISON_SINGLE` | 已移除兼容 | 局部引爆毒素 | 无当前描述或实现 | 证据不足，暂沿用 |
| `SPELL_POISON_WEAPON` | 已移除兼容 | 淬毒武器 | 无当前描述或实现 | 证据不足，暂沿用 |
| `SPELL_POISON_CLOUD` | 已移除兼容 | 毒气云 | 无当前描述或实现 | 证据不足，暂沿用（复用 D-C-015） |

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
| `SPELL_CIGOTUVIS_DEGENERATION` | 已移除兼容 | 西格图维之退化 | 无当前描述或实现 | 证据不足，暂沿用 |
| `SPELL_CIGOTUVIS_EMBRACE` | 已移除兼容 | 西格图维之拥抱 | 无当前描述或实现 | 证据不足，暂沿用 |

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
所依赖的 `Evocations` 错译成“召唤术”。本批修正为“激活技能”。

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
| `SPELL_LEHUDIBS_CRYSTAL_SPEAR` | 8 / 塑能、土 / `dir_or_target, needs_tracer` | 勒胡迪布之水晶矛 | 短射程发射尖锐水晶投射物，造成极高物理伤害 | 保留 |

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
| `SPELL_HOARFROST_BULLET` | 5 / 塑能、冰 / `dir_or_target, needs_tracer, monster` | 白霜火炮 | 白霜弹 | 冰霜碎片命中后减速；第五发碎裂并产生额外范围伤害 | 保留 |

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
| `SPELL_FLASH_FREEZE` | 现行 | 7 / 塑能、冰 / `dir_or_target, monster, needs_tracer` | 急冻 | 高额伤害并短时减速；一半伤害无视寒冷抗性 | 保留 |
| `SPELL_FREEZING_GUST` | 现行 | 5 / 塑能、冰、气 / `target, needs_tracer, cloud, monster` | 冰冻狂风 | 穿透性严寒气流，沿途留下致命寒气云 | 重译为“冰冻阵风” |
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
| `SPELL_ACID_BALL` | 5 / 塑能、炼金 / `dir_or_target, needs_tracer, monster` | 怪物 | 酸液球 | 投掷会爆炸的腐蚀性酸液球 | 保留 |
| `SPELL_CORROSIVE_BOLT` | 6 / 塑能、炼金 / `dir_or_target, needs_tracer` | 玩家、怪物 | 腐蚀箭 | 穿透酸液束，可施加腐蚀 | 保留（复用 D-C-014） |

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
| `SPELL_CREEPING_FROST` | 5 / 塑能、冰 / `monster` | 怪物 | 蔓延冰霜 | 从墙壁唤出冻气，伤害、冻结并减速墙边敌人 | 保留 |
| `SPELL_REBOUNDING_CHILL` | 7 / 塑能、冰 / `dir_or_target, needs_tracer, monster` | 怪物 | 弹跳寒冷 | 穿透寒气束沿墙反弹，可命中目标两次 | 重译为“弹跳寒流” |
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
| `SPELL_RING_OF_THUNDER` | 已移除兼容 | 雷霆之环 | 无当前描述或实现 | 证据不足，暂沿用 |
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
| `SPELL_GLACIATE` | 9 / 塑能、冰 / `dir_or_target, monster` | 怪物 | 冰川 | 锥形寒冰冲击；近处伤害更高，命中后冰封减速，击杀可能生成冰块 | 重译为“冰封” |
| `SPELL_ICEBLAST` | 5 / 塑能、冰 / `dir_or_target, needs_tracer` | 玩家道具、怪物 | 冰爆 | 大团冰块撞击爆炸，一半伤害无视寒冷抗性 | 保留 |
| `SPELL_HAILSTORM` | 3 / 塑能、冰 / 无 | 玩家 | 冰雹风暴 | 环形冰雹攻击；紧邻施法者处为安全风暴眼 | 保留 |

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
| `SPELL_DELAYED_FIREBALL` | 已移除兼容 | 延迟火球 | 无当前描述或实现 | 证据不足，暂沿用 |

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

## Awaken 词形系列

边界：英文标题以 `Awaken` 开头的 5 项法术；其中 4 项现行、
1 项 `TAG_MAJOR_VERSION == 34` 已移除兼容。

| Enum | 生命周期 | 当前译名 | 核心效果 | 裁定 |
|---|---|---|---|---|
| `SPELL_AWAKEN_FOREST` | 现行 | 唤醒森林 | 附近树木攻击相邻敌人 | 保留 |
| `SPELL_AWAKEN_VINES` | 现行 | 唤醒藤蔓 | 藤蔓抓住闯入者并拖向树木 | 保留 |
| `SPELL_AWAKEN_FLESH` | 现行 | 唤醒血肉 | 肉堆化为强化大型憎恶并伤害邻敌 | 保留 |
| `SPELL_AWAKEN_ARMOUR` | 现行 | 唤醒护甲 | 从所穿护甲记忆显现战斗回响 | 保留 |
| `SPELL_AWAKEN_EARTH` | 已移除兼容 | 唤醒大地 | 无当前描述或实现 | 证据不足，暂沿用 |

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
| `SPELL_SHADOW_BEAM` | 5 / 塑能 / `dir_or_target, monster, needs_tracer, silent` | 怪物 | 暗影光束 | 穿透性暗影束 | 保留（复用 D-C-020） |

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
| `SPELL_THROW` | 已移除兼容 | 投掷 | 无当前描述或实现 | 证据不足，暂沿用 |

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
| `SPELL_WEAVE_SHADOWS` | 已移除兼容 | 编织暗影 | 无当前描述或实现 | 证据不足，暂沿用 |

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
