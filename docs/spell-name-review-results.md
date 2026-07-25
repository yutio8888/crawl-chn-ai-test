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
