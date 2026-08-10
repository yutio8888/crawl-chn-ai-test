# Issue #59 R4 monspell 怪物施法宣言全量逐身份审阅计划

## 冻结边界

- 上游总览：Issue #40 R4；执行入口：Issue #59（怪物施法宣言 monspell 全量逐身份翻译校对）。
- 精确基线：`8e974d60549c1946403b3866efa56cb48db364b8`。
- Glossary SHA-256：
  `95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407`
  （`docs/glossary.md`，术语权威）。
- 冻结 inventory SHA-256：
  `f0f2f00f4cf842a017c91c4364652aadfd679e461687308105eec2f8fac37932`
  （`/tmp/monspell-inventory-8e974d6054.json`，本计划的唯一数字来源）。
- 冻结 scope SHA-256：`7d62024c758b00b3bd1e012eaf4c879530b12095ca9b7b538b3d7ddaf39931cc`。
- candidate anchor artifact SHA-256：
  `9eb63d334f31c1dfb608c7c742f2ce4046a711f7450d6de0ac516033baf3c083`
  （`monspell_candidate_lookup` schema v1；行为报告 `inputs.candidate_anchor.artifact_sha256`
  同值绑定）。
- 语义指纹：`7031515a931079c2c58c792d5c7ddc44d8fb391c2814aa371fa3c417298db94b`
  （phase0 inventory、overlay manifest `inventory_semantic_fingerprint` 与行为报告三侧绑定）。
- source 指纹：`49ef2b9eb42f55312a4cf3965487af07c82b555f5b6720c3c1fa43903828a054`
  （EN production `monspell.txt` 的 phase0 source 指纹，双侧重建一致）。
- 本批规范身份是 overlay catalog 与生产 SpeakDB 双源合一的完整 effective key 集：
  262 个 canonical_key，全部来自 `monspell.txt` 作用域（source_basename
  `monspell.txt`，`lua_sites=0`、`overridden_keys=0`），不纳入其他消息库。

步骤 2 工具 `monspell_inventory.py` 已于提交
`3aab51a5355f33e6b364ac5cfe822a5a9c54760e` 落地并注册（26 项测试通过）。它是窄域
entry/spec：exact-Git source manifest、normalized snapshot、TextDB 定义解析、
weighted variant 派生、artifact hash 与安全输出均复用 `monflee_inventory.py` 的
既有实现；phase0 语义指纹绑定复用 `audit_monspell_phase0`；catalog 装载复用
`generate_message_overlay`。没有复制第二套 TextDB parser。

## 冻结 inventory 与身份集合

身份集合 = overlay catalog（`.claude/data/message-overlay/monspell.json` +
`monspell/*.json`）的 262 个 canonical_key，与 phase0 inventory 的
`monspell_keys=262`、行为报告 `inventory_root_count=262` 三方一致。分布如下：

| 维度 | 分布 |
|---|---|
| route | STRUCTURED 245 / LEGACY 12 / SUPPRESSED 5 |
| entry_mode | CANDIDATE 250 / LEGACY_ONLY 10 / CLOSURE_ONLY 2 |
| 可达性 | reachable（runtime_evidence=true）251 / unreachable 11 |
| no-zh entry | 15（= 10 个 LEGACY_ONLY + 5 个 SUPPRESSED） |

计数不能替代集合证明：consumer 同时核对完整 key 集、catalog 顺序、每个 variant
locator/ordinal/weight/raw pattern、entry_mode、policy 序列与 legacy 双源绑定。
重复、缺失、额外或乱序一律 fail closed。

### STRUCTURED 245（按 canonical_key 排序，紧凑列表）

```
acid ball nascent plasmodium cast | airstrike blizzard demon cast | airstrike cast | airstrike wind drake cast | angel cast targeted | antimagic gaze norris cast | awaken flesh kobold fleshcrafter cast | basilisk cast | basilisk cast targeted | battlecry cast
battlecry cherub cast | battlecry satyr cast | beam catchall cast | beckoning gale chonchon cast | beckoning gale hippogriff cast | berserker rage rupert cast | bes kemwar cast | blink range ironbound thunderhulk cast | blinkbolt cast | blizzard demon cast
bolt of draining natural cast | bolt of fire ophan cast | bolt of flesh kobold fleshcrafter cast | bolt of flesh zykzyl cast | bolt of magma molten gargoyle cast | bombardier beetle cast | brain worm cast | burial acolyte cast | call down lightning cast | call lost souls cast
call of chaos cast | cantrip cast | cantrip dissolution cast | cantrip gastronok cast | cause fear satyr cast | clockroach cast | cognitogaunt cast | cold breath cast | confuse sphinx marauder cast | conjure living spells cast
corrupting pulse wretched star cast | crab cast targeted | creeping frost cast | crystal echidna cast targeted | crystallising shot crystal guardian cast | culicivora cast targeted | curse skull cast | death rattle ushabti cast | dispel undead revenant cast | dissolution cast
divine armament cast | dominate undead vampire bloodprince cast | doomsaying cassandra cast | dragon cast | dragon cast targeted | drake cast targeted | druid's call cast | dryad cast | eidolon cast targeted | electrical bolt cast
electrical bolt shock serpent cast | enfeeble zykzyl cast | ensnare arachne cast | ensnare natural cast | eruption cast | eye of draining cast | fire breath cast | fireball hell hog cast | flashing balestra undying armoury cast | flayed ghost cast
floating eye cast | floating eye cast targeted | force lance polterguardian cast | formless jellyfish cast | frances cast | freeze cast | gastronok cast | gastronok cast targeted | geryon cast | ghost moth cast
ghost moth cast targeted | ghostly fireball revenant cast | glowing orange brain cast | golden eye cast targeted | grasping roots cast | grasping roots natural cast | grave claw vampire bloodprince cast | guardian serpent cast | guardian serpent cast targeted | harpoon shot cast
haste other priest cast | heal other priest cast | hellfire court cast | hellfire mortar cast | hellfire mortar wiglaf cast | hoarfrost bullet cast | hoarfrost bullet cast finale | holy flames cast | hurl torchlight cast | injury mirror screaming refraction cast
invisibility shadowghast cast | kobold blastminer cast targeted | landbreaker natural cast | laughing skull cast | launch bomblet cast | lee's rapid deconstruction screaming refraction cast | legendary destruction cast | lightning bolt electric golem cast | lightning bolt natural cast | living spell cast
magical cast | magical cast targeted | major destruction cast | malign offering priest cast | malmutate zykzyl cast | manifold assault natural cast | manticore cast | mara summon cast | march of sorrows bone dragon cast | march of sorrows boris cast
mennas cast | metal splinters war gargoyle cast | might other priest cast | minor healing dryad cast | non-humanoid wizard cast | non-humanoid wizard cast targeted | obsidian statue cast | orange crystal statue cast | orange crystal statue cast targeted | orb of destruction cast
orb of destruction orb spider cast | orb of entropy cast | orb of fire cast | orb of winter cast | ostracise cast | paralyse xtahua cast | paralysis gaze cast | petrifying cloud cast | phantom blitz cast | phantom mirror cast
poisonous cloud natural cast | priest cast | priest cast targeted | primal wave elemental wellspring cast | primal wave norris cast | pyroclastic surge cast | quicksilver bolt natural cast | raven cast | ravenous swarm vampire bloodprince cast | rebounding blaze thermic dynamo cast
rebounding chill thermic dynamo cast | roxanne cast | rupert cast targeted | scrub nettle cast targeted | searing breath cast | seismic stomp cast | shadow shot cast | sheza's dance cast | silent berserker rage rupert cast | silent blizzard demon cast
silent curse skull cast | silent flayed ghost cast | silent laughing skull cast | silent weeping skull cast | siphon essence cast | sleep satyr cast | slug dart cast | smiting guardian sphinx cast | smiting jeremiah cast | sojourning bolt cast
spectral cloud revenant cast | sphinx cast | spit acid cast | spit lava cast | spit poison cast | splinterspray cast | steam ball natural cast | sticks to snakes cast | sticky flame cast | stone arrow gargoyle cast
stunning burst cast | summon eyeballs dissolution cast | summon mortal champion fravashi cast | summon water elementals elemental wellspring cast | sun moth cast | symbol of torment cast | thrashing horror cast | throw bolas cast | throw icicle shard shrike cast | throw klown pie cast
undertaker cast targeted | unseen airstrike cast | unseen blinkbolt cast | unseen bolt of fire ophan cast | unseen call of chaos cast | unseen cold breath cast | unseen curse skull cast | unseen dragon cast | unseen ensnare arachne cast | unseen ensnare natural cast
unseen fire breath cast | unseen floating eye cast targeted | unseen geryon cast | unseen ghost moth cast targeted | unseen holy flames cast | unseen laughing skull cast | unseen mara summon cast | unseen non-humanoid wizard cast | unseen orb of destruction cast | unseen phantom blitz cast
unseen priest cast | unseen searing breath cast | unseen spit acid cast | unseen spit poison cast | unseen symbol of torment cast | unseen thermic dynamo cast | unseen vv cast | unseen warning cry cast | unseen warning cry howler monkey cast | unseen warning cry seraph cast
unseen warning cry ushabti cast | unseen warning cry vault sentinel cast | unseen weeping skull cast | unseen wizard cast | ushabti cast targeted | vanquished vanguard nergalle cast | vex sphinx marauder cast | vhi's electrolunge cast | volley of thorns cast | vv cast
warning cry cast | warning cry hippogriff cast | warning cry howler monkey cast | warning cry seraph cast | warning cry ushabti cast | warning cry vault sentinel cast | weakening gaze cast | weeping skull cast | wind blast cast | wind blast wind drake cast
wizard cast | wizard cast targeted | woodweal cast | word of recall cast | wretched star cast
```

STRUCTURED 全部为 entry_mode=CANDIDATE（245/245）；production 来源为 catalog
（`production_zh_source=catalog`），legacy 双源 `zh/monspell.txt` 仅作 fallback
（`fallback_zh_source=zh/monspell.txt`）。

### LEGACY 12

| canonical_key | entry_mode | runtime_evidence | legacy 变体数 |
|---|---|---|---|
| `_unseen_breath_cast_` | CLOSURE_ONLY | false | 1 |
| `_unseen_spit_cast_` | CLOSURE_ONLY | false | 1 |
| `acid splash cast` | LEGACY_ONLY | false | 1 |
| `branch summon cast prefix` | LEGACY_ONLY | false | 1 |
| `chilling breath cast` | LEGACY_ONLY | false | 1 |
| `paralysis guardian sphinx cast` | LEGACY_ONLY | false | 1 |
| `polymorphed unseen wizard cast` | LEGACY_ONLY | false | 1 |
| `polymorphed wizard cast` | LEGACY_ONLY | false | 1 |
| `polymorphed wizard cast targeted` | LEGACY_ONLY | false | 1 |
| `unseen acid splash cast` | LEGACY_ONLY | false | 1 |
| `unseen chilling breath cast` | LEGACY_ONLY | false | 1 |
| `unseen priest cast targeted` | LEGACY_ONLY | true | 3 |

LEGACY 12 的 production 来源为 `zh/monspell.txt`；其中 11 条不可达（无 candidate
dump 运行时证据），唯一可达的是 `unseen priest cast targeted`（3 个 legacy 变体、
9 个 runtime token、权重 10/10/10）。

### SUPPRESSED 5（稳定 stable_id，`.suppress.v1`）

| canonical_key | stable_id |
|---|---|
| `avatar song cast` | `mon.cast.avatar_song.suppress.v1` |
| `blink away revenant cast` | `mon.cast.blink_away_revenant.suppress.v1` |
| `blink magical cast` | `mon.cast.blink_magical.suppress.v1` |
| `seal doors cast` | `mon.cast.seal_doors.suppress.v1` |
| `siren song cast` | `mon.cast.siren_song.suppress.v1` |

五条均为 CANDIDATE、variant 0 的 `english_snapshot=__NONE`、`suppresses=true`、
policy NONE、production 来源 `none`。结论固定 `keep`（无玩家可见文本，见 §5）。

### 可达性分区

- reachable 251 = STRUCTURED 245 + SUPPRESSED 5 + LEGACY 1
  （`unseen priest cast targeted`）；行为报告 `candidate_lookup` EN/ZH
  hit_count 均为 251。
- unreachable 11（仅 phase0 静态定义审阅，不产生 candidate dump 运行时证据）：
  `_unseen_breath_cast_`、`_unseen_spit_cast_`、`acid splash cast`、
  `branch summon cast prefix`、`chilling breath cast`、
  `paralysis guardian sphinx cast`、`polymorphed unseen wizard cast`、
  `polymorphed wizard cast`、`polymorphed wizard cast targeted`、
  `unseen acid splash cast`、`unseen chilling breath cast`。
- 行为报告 `universe.runtime_roots`（251）与 `inventory_unreachable_roots`（11）
  互斥且并集恰好覆盖 catalog 262。

## 双源证据来源

### Structured 路由（overlay catalog 清单）

- 清单：`.claude/data/message-overlay/monspell.json`（schema v1，domain
  `monspell`，`inventory_semantic_fingerprint` 绑定语义指纹）+ 28 个 fragment
  （`monspell/*.json`，`000-baseline.json` 至 `590-wave-final.json`，含
  `530-lowercase-actor.json`、`550-suppress.json`），合计 262 条目、
  0 tombstone。
- ZH 模板：582 个 = line_metadata 539 项 + materialization_cases 43 项。
- 关系分布（按模板计，`structured_relation_counts`）：AT 115 / NEXT_TO 115 /
  PAST 115 / NONE 237；其中 line_metadata 层 AT 111 / NEXT_TO 111 / PAST 111 /
  NONE 206（539），case 层 AT 4 / NEXT_TO 4 / PAST 4 / NONE 31（43）。
- 感官（按 line_metadata 项计，一项多关系只带一个 sensory）：
  PLAIN 342 / VISUAL 10，无 SOUND；channel 全部为 None。
- per-identity primary materialization_policy（variant 0 策略，
  `primary_policy_counts`）：NONE 233 / CASE_MAP 8 / CAPTURE_SLOT 1 /
  RECURSIVE_CASE_MAP 10 / LEGACY_ONLY 10。
- 混配条目 3 条（同一 identity 内各 variant policy 不同，
  `mixed_policy_keys`）：
  - `orb of entropy cast`：`[CASE_MAP, NONE, NONE, NONE]`；
  - `orb of winter cast`：`[NONE, NONE, CASE_MAP]`；
  - `vanquished vanguard nergalle cast`：`[CAPTURE_SLOT, NONE]`。
- 可审模板边界：582 个 catalog 模板中 580 个落在 245 个 STRUCTURED identity
  （结构化审核按卡逐模板进行）；其余 2 个模板属于 CLOSURE_ONLY 的
  `_unseen_breath_cast_`、`_unseen_spit_cast_`（各 1 个、relation NONE），其路由
  为 LEGACY，不进入 structured 审核。case-map 模板（CASE_MAP /
  RECURSIVE_CASE_MAP）必须携带非 root 的 `case_id`。

### Legacy 路由（SpeakDB 双源）

- 生产双源：`database/monspell.txt`（EN，load index 1）与
  `database/zh/monspell.txt`（ZH，load index 14，localized child TextDB 第 2 源）；
  `getSpeakString` 按生产权重选择正文。EN 文件 1340 行、ZH 文件 1337 行，
  各 265 个 `%%%%` 定义分隔。
- 变体：355 个 EN 变体跨 262 键；357 个 ZH 变体
  （`en_variant_count=355`、`zh_variant_count=357`）。
- token 站点：605 个 EN token 站点（590 runtime + 15 recursive）；
  529 个 ZH token 站点；12 个随机子串站点；0 Lua；0 override。
- 冻结双 key 不对称（`asymmetric_variant_keys`，按 (EN, ZH) 变体数）：
  `guardian serpent cast` (1, 4)、`guardian serpent cast targeted` (3, 2)。
  这是冻结的基线事实，不作为缺陷处理；两 key 的 EN/ZH 逐 ordinal 配对由台账
  `fallback` 语义覆盖。
- ZH token 词汇是 EN 真子集；86 个同序配对变体的 token 用法与 EN 不同
  （`monspell_inventory.py` 模块 docstring 记录的基线事实，非缺陷）。台账因此
  不断言逐变体 EN==ZH token 相等，而是断言：key 集相同、定义 ordinal 连续、
  仅 monspell.txt provenance、无 override/parse error、每个配对 ordinal 的
  weight 与控制前缀一致、ZH token 词汇 ⊆ EN 词汇、变体/token/站点计数冻结、
  双 key 不对称冻结。
- 控制符：EN/ZH 文件各 10 个 `VISUAL:` 前缀（legacy variants 中
  `control_prefix=VISUAL` 的 10 个），无 `SOUND:`。
- no-zh entry 15（10 个 LEGACY_ONLY + 5 个 SUPPRESSED）：catalog 无 ZH 模板，
  legacy 双源无 ZH 配对变体。

### 路由判定与行为证据

- `route_monspell_message`（`fork-message-overlay.cc:1704`）：overlay enabled
  且 `monspell_overlay_covers(key)`（`:1676`）→ STRUCTURED，否则 LEGACY；
  STRUCTURED 失败永不回退 LEGACY。
- `resolve_monspell_cast_message`：`mon-cast.cc:9291` 调用点
  （定义 `fork-message-overlay.cc:1748 search_message_candidate`）；
  物化 `fork-message-overlay.cc:1779 materialize_monspell_candidate`；
  渲染 `fork-message-overlay.cc:2400 render_materialized_candidate`（zh）。
- legacy：`database.cc:2307 getSpeakString` 加权选择 + token/递归/`[a|b]` 展开；
  `VISUAL:` 前缀正文路由至 `MSGCH_TALK_VISUAL`。
- SUPPRESSED：`english_snapshot=__NONE` 的 CANDIDATE；模板被抑制，任何语言都
  不产生 emission，亦不回退 LEGACY，玩家无可见文本。
- 行为报告（`.claude/data/message-overlay/monspell-behavior-report.json`）：
  `phase2_ready=true`、`phase2_blockers=[]`、coverage 全 true
  （catalog_coverage_complete、en_zh_behavior_parity_proven、
  candidate_key_containment_proven）、`locale_presence_mismatch` /
  `locale_behavior_mismatch` / `locale_behavior_inconclusive` 全空、
  `analysis_completeness=SOUND_CLOSED_WORLD_UPPER_BOUND`。

### 行为报告漂移说明（重要）

- checked-in 行为报告是 2026-07-17 快照（提交 `6991f5c4d3`），其
  `inputs.localized_artifact.sha256 = da4724309f5341873b1a04fe9a713f42552d6f2d32f4657804e9e84781d996d0`
  与当前基线 `8e974d6054` 重新派生的 ZH production dump
  （`1d6505e1923a3cb021dafd4457a14ae7dba6e825445bdf9e670232a4bdcb4eca`，即冻结
  inventory `dumps.localized.artifact_sha256`）不一致。
- 根因：报告生成后 ZH 数据继续演进（如 8/9 的 miscast 审核批次改动了
  `database/zh/` 下其他消息库），`monspell.txt` 自身作用域未变。
- 用当前基线重建报告（`/tmp/monspell-behavior-rebuild.json`）后，全部关键断言
  字段一致：`phase2_ready`、coverage、locale mismatch 三空、candidate
  artifact/anchor 指纹、inventory 语义指纹、EN artifact、candidate_lookup
  hit 251/251。唯一差异：`vanquished vanguard nergalle cast` 的 ZH locale
  分析从可分析变为 `UNANALYSABLE`（detail：`vanquished vanguard nergalle
  cast:0 pre-binding: symbolic state limit exceeded`）——这是分析器符号状态
  上限导致 fail-closed，不是翻译缺陷。
- 审核该 identity 时必须在卡内注明此证据缺口，结论倾向标注
  `defer implementation`（或充分说明为何仍可给出 keep/adjust/retranslate）。
- CI 不执行 behavior `--check`；本批工具 `monspell_inventory.py` 只断言
  phase2_ready/blockers、coverage、universe 计数、candidate_lookup hit、
  语义指纹与 candidate anchor 绑定，不校验 `localized_artifact.sha256`，
  因此该漂移不影响本批断言。

## Producer、consumer 与最终显示

- key 配方：`mon-cast.cc:8764 _speech_keys → build_key_recipe`（
  `mon-cast-message-keys.{h,cc}`；`catch2-tests/test_mon_cast_message_keys.cc`
  8 个 TEST_CASE 冻结配方顺序、重复分类、优先级与“不消耗游戏 RNG”）。
- 路由：`fork-message-overlay.cc:1676 monspell_overlay_covers` /
  `:1704 route_monspell_message`（overlay enabled && covers → STRUCTURED，
  否则 LEGACY；STRUCTURED 失败 die，永不回退 LEGACY）。
- 搜索/物化/渲染：`fork-message-overlay.cc:1748 search_message_candidate`、
  `:1779 materialize_monspell_candidate`、`:2400
  render_materialized_candidate(zh)`；`mon-cast.cc:9291` 调用点。
- legacy：`database.cc:2307 getSpeakString` 加权选择 + token/递归/`[a|b]`
  展开；`VISUAL:` 前缀正文路由至 `MSGCH_TALK_VISUAL`。
- SUPPRESSED：`__NONE` snapshot；路由判定为结构化覆盖，但候选物化不产生
  emission，render 产出空，无玩家可见文本；不消耗 RNG、不回退。
- 本批不改变 lookup key、catalog 顺序、权重、RNG、channel 或最终 sink。

## 审核方法（逐 identity 证据卡）

后续 translation-reviewer 按冻结 inventory 的 entry 顺序逐 identity 出具证据卡
（写入 `docs/monspell-review-results.md`，schema 见 §6）。每张卡必须覆盖：

- **两路由 ZH 措辞**：STRUCTURED 卡逐模板核对 `pattern_en`/`pattern_zh` 的命题、
  结构、语气与 token/槽位；LEGACY 卡逐变体核对 `english`/`current_chinese`。
- **关系**：`relation` ∈ AT / NEXT_TO / PAST / NONE 逐模板绑定，中文方位表达
  （“向/朝/旁边/之前/身后”等）必须与关系一致。
- **感官与通道**：sensory PLAIN/VISUAL 与 `VISUAL:` 控制前缀原样保留（glossary：
  `VISUAL:` / `SOUND:` 前缀、`@keyword@`、`w:N` 权重、`%%%%` 分隔符、`{{ }}`
  Lua 块、`[variant|choice]` 选择语法均不可变）；channel 全 None。
- **token/递归/`[a|b]`**：runtime token 大小写、顺序与重复次数是协议一部分；
  递归 token 站点（15 个）与 12 个随机子串站点逐站核对 alternative 数量；
  方括号不平衡、站点增删或 alternative 漂移拒绝。
- **视角**：玩家可见（player-visible）/怪物（monster，展开 `@The_monster@`
  等槽）/不可见（unseen，`unseen …` key 不暴露怪物身份）三视角措辞。
- **怪物角色声音**：按 `docs/glossary.md` 角色声音速查表核对（龙=半文言
  自称“吾/本座”；小恶魔=嬉皮笑脸；高等恶魔=冷傲；巫妖=冷智“吾/本巫”；
  地精/兽人=“老子/俺”短句；幽灵=断续短句；Xom=跳跃无因果等）；怪物专用
  呼名（如 `@orc name@`）与咒文内容保持角色一致性。
- **术语**：cast=施法（通用）/吟诵（仪式）/咏唱（神圣）；shout=喊叫（非
  “吼叫”=roar）；`X of Y` → `Y之X`；所有术语以 glossary SHA-256
  `95eeacf9…` 为准。

分路由聚合与结论规则（与 `validate_results` 一致）：

- **STRUCTURED 245**：按 `structured_template_reviews` 聚合
  （`_aggregate`：retranslate > adjust > defer > keep）；legacy fallback 变体
  的 `legacy_variant_reviews` 只允许 keep/adjust、禁止 retranslate，且不参与
  聚合；structured 结论为 retranslate 时，任何 legacy adjust 的 rationale
  必须引用同步标记“与 structured 模板同步”。
- **LEGACY 12**：按 `legacy_variant_reviews` 聚合；无 structured reviews。
- **SUPPRESSED 5**：结论固定 keep（无 structured reviews、无 proposed
  structured、legacy reviews 全 keep）；卡内注明“抑制消息：任何语言、任何
  可见性下都不显示”。
- **unreachable 11**：仅 phase0 静态定义审阅，无 candidate dump 运行时证据；
  `reviewer_rationale` 必须含标记“仅 phase0 静态定义审阅，无 candidate dump
  运行时证据”。
- 结论词 ∈ keep / adjust / retranslate / defer terminology / defer
  implementation；keep 必须逐字保留，adjust/retranslate 必须实际改变；
  defer 必须提供 `deferral_owner`、`deferral_reason`、`reentry_trigger` 且
  保留现状。
- `vanquished vanguard nergalle cast` 的卡必须注明行为报告证据缺口（§3.4），
  倾向 `defer implementation` 或充分说明。

**非目标**：不修改路由/配方/schema/catalog 顺序/权重/RNG；不重做 structured
叠加层证明（candidate anchor 已冻结）；审核中发现的实现缺陷（如
`symbolic state limit exceeded` 类分析器问题）单独开 Issue，不进本批台账。

## 严格台账 schema（docs/monspell-review-results.md）

`docs/monspell-review-results.md` 尚不存在；由后续 zh-translator 创建。本计划
只描述其 schema（定义见 `monspell_inventory.py` 的 `STRICT_BEGIN`/
`STRICT_END`/`METADATA_FIELDS`/`CARD_FIELDS` 与 `validate_results` 不变量，
格式先例为 `docs/miscast-review-results.md`）：

- strict JSONL block 以注释标记包裹：
  `<!-- BEGIN STRICT MONSPELL REVIEW EVIDENCE v1 -->` 与
  `<!-- END STRICT MONSPELL REVIEW EVIDENCE v1 -->`。
- 记录数固定为 263 = 1 条 metadata + 262 张 identity 卡；metadata 必须是首行。
- metadata 字段（`METADATA_FIELDS`）：
  `baseline`（== inventory `baseline_ref`）、`glossary_sha256`（==
  `95eeacf9…`）、`identity_count`（== 262）、`inventory_sha256`（==
  `f0f2f00f…`）。
- 每张卡的 identity 集合与 inventory `entries` 精确相等、顺序完全一致
  （逐 identity 出现一次，重复/缺失/额外/乱序 fail closed）。
- 卡字段（`CARD_FIELDS`，31 项）：`identity`、`key`、`route`、`entry_mode`、
  `primary_materialization_policy`、`runtime_evidence`、
  `production_zh_source`、`fallback_zh_source`、`terminal_conclusion`、
  `confidence`、`lifecycle`（按路由冻结：structured-overlay-emission /
  legacy-speakdb-emission / suppressed-no-emission）、`actual_behavior`、
  `display_context`、`consumer`（FROZEN_CONSUMER 七点：route_decision
  fork-message-overlay.cc:1704、overlay_covers :1676、candidate_search
  mon-cast.cc:9291、candidate_search_definition :1748、materialize :1779、
  render :2400、legacy_getspeakstring database.cc:2307）、`producers`
  （mon-cast.cc:8764 `_speech_keys → build_key_recipe`）、
  `dependency_group`（`{key} 怪物施法消息路由与本地化`）、`glossary_authority`
  （`docs/glossary.md@95eeacf9…`）、`evidence_locations`（按路由：STRUCTURED
  8 点 / LEGACY 5 点 / SUPPRESSED 3 点，含 EN/ZH source 行号）、
  `current_english`、`current_chinese`、`current_structured_zh`、
  `proposed_translation`、`proposed_structured_zh`、
  `structured_template_reviews`、`legacy_variant_reviews`、
  `production_facts`、`reentry_trigger`、`rejected_alternatives`、
  `reviewer_rationale`、`deferral_owner`、`deferral_reason`。
- `production_facts`（`PRODUCTION_FACT_FIELDS`）：`structured_template_count`、
  `structured_relations`、`legacy_variant_count`、`weights`、
  `control_prefixes`、`materialization_policies`、`runtime_tokens`，必须与
  inventory entry 逐字段相等。
- `structured_template_reviews` 逐模板绑定
  `locator`/`pattern_en`/`relation`/`sensory`/`materialization_policy`/
  `current_pattern_zh`/`proposed_pattern_zh`/`rationale`/
  `terminal_conclusion`（defer 时加 deferral 三字段）；case-map 模板必须携带
  非 root `case_id`；keep 保留、adjust/retranslate 必须改动、defer 保留。
- `legacy_variant_reviews` 逐变体绑定 `variant_ordinal`/`weight`/
  `control_prefix`/`runtime_tokens`/`english`/`current_chinese`/
  `proposed_translation`/`fallback`（== route != LEGACY）/`rationale`/
  `terminal_conclusion`；未配对 EN 变体（`chinese=None`）必须 keep 且
  proposal 为 None。
- 结论聚合与路由规则见 §5；SUPPRESSED 必须 keep；STRUCTURED 的 legacy
  reviews 只允许 keep/adjust；LEGACY 无 structured reviews。
- 候选边界：candidate ref 为完整小写 commit OID 且与 checkout HEAD 精确相等；
  checkout（含 untracked）必须 clean；baseline 必须是 candidate ancestor；
  candidate EN 不得漂移；candidate ZH 必须逐 identity 与 ledger proposal
  完全一致（legacy 变体对齐 candidate ZH dump、structured 模板按
  key+ordinal+case_id+relation locator 对齐 candidate manifest）。

## 验收标准到测试映射

| 验收项 | 机械证据 |
|---|---|
| catalog/phase0/legacy 三方绑定与 262 identity | `build_binds_catalog_phase0_and_legacy`、`consistency_assertions_fail_closed` |
| 路由派生用 snapshot + stable_id（SUPPRESSED/STRUCTURED/LEGACY） | `route_derivation_uses_snapshot_and_stable_id` |
| legacy 双源 fail-closed（key 集/ordinal/weight/控制符/token 子集） | `legacy_binding_fail_closed` |
| structured 模板提取 fail-closed（582/539/43、关系、感官、channel） | `structured_template_extraction_fail_closed` |
| 台账 263 记录、metadata 绑定、卡集合/顺序 | `valid_ledger_passes_with_route_counts`、`ledger_coverage_duplicate_extra_missing_order_fail`、`metadata_bindings_fail_closed` |
| 未知字段、非终态结论、bool-as-int fail closed | `card_unknown_fields_and_nonterminal_fail`、`boolean_integer_fields_fail_closed` |
| 冻结 behavior/consumer/producer 证据 | `frozen_behavior_evidence_fail_closed` |
| SUPPRESSED keep-only、STRUCTURED 聚合与 fallback 规则、LEGACY 聚合 | `suppressed_route_requires_keep_with_fallback_only`、`structured_aggregation_and_legacy_fallback_rules`、`legacy_route_aggregation_and_structured_forbidden` |
| case-map 携带 case_id、unreachable 静态审阅标记、unpaired keep None、deferral 三字段 | `case_map_reviews_carry_case_id_and_cover_cases`、`unreachable_identities_require_static_review_rationale`、`unpaired_en_variant_must_keep_none`、`deferral_fields_are_required_and_forbidden` |
| 混配 policy 生产事实 | `mixed_policy_entry_production_facts` |
| candidate 绑定/EN 漂移/manifest 漂移/commit gate/CLI 安全输出 | `candidate_binding_matches_proposals`、`candidate_english_drift_is_rejected`、`candidate_manifest_drift_is_rejected`、`candidate_commit_gate_fails_closed`、`cli_exclusive_tmp_output`、`cli_candidate_and_review_validation` |

`verify_zh.sh` 的 message-overlay static dispatcher 已注册
`test_monspell_inventory.py`（26 项全过），与 `test_message_overlay.py`、
`test_audit_monspell_behavior.py`、`test_miscast_inventory.py`、
`test_monflee_inventory.py` 同批运行。

## 执行顺序与人工确认点

1. **审核**：translation-reviewer 按本计划逐 identity 出具证据卡并写入
   `docs/monspell-review-results.md`（严格台账 schema 见 §6）。
2. **人工确认**：人对 adjust/retranslate 候选逐条确认（含
   `vanquished vanguard nergalle cast` 的证据缺口结论）。
3. **落地 zh/monspell.txt**（zh-translator）：LEGACY 12 与 STRUCTURED 的
   fallback 变体按台账 proposal 落地。
4. **落地结构化清单**（crawl-coder）：STRUCTURED 模板 pattern_zh 按台账
   proposal 写入 catalog fragments（含 case-map 各 case）。
5. **候选绑定**：生成 candidate commit 与 EN/ZH candidate dump，运行
   `monspell_inventory.py --candidate-ref …` 证明 descendant、artifact 与
   ledger proposal 逐 identity 一致。
6. **review_prepare**：`review_prepare.sh` 准备不可变候选边界。
7. **机械 review**：按 `.agents/policies/review-contract.md` 只派机械路由的
   reviewer，记录 readiness。
8. **final gate**：`review_final_gate.sh <candidate> <target>` 单一最终运行，
   通过后合并。

## 明确排除（非目标）

- 不修改 `mon-cast.cc`、`fork-message-overlay.cc`、`database.cc`、
  `mon-cast-message-keys.*` 或任何 runtime C++。
- 不修改英文 lookup key、catalog 顺序、权重、RNG、channel、fallback 或
  最终 sink。
- 不重做 structured 叠加层证明（candidate anchor `9eb63d33…` 已冻结）。
- 不修改 inventory/ledger schema、final gate、持久状态或目录层级。
- 不把其他 SpeakDB source、其他翻译批次或无关清理纳入 Issue #59。
- 审核中发现的实现缺陷（如分析器状态上限）单独开 Issue，不进本批台账。

## 重建入口

先在 HEAD 精确等于基线 OID 且 clean 的 checkout 中生成 production EN/ZH dump，
再运行窄域 consumer。输出必须是新的 `/tmp` 或 `/private/tmp` 直接子文件：

```bash
python3 .claude/scripts/monspell_inventory.py \
  --baseline-ref 8e974d60549c1946403b3866efa56cb48db364b8 \
  --english-dump /tmp/monspell-phase0-en-8e974d6054.json \
  --localized-dump /tmp/monspell-phase0-zh-8e974d6054.json \
  --phase0-inventory .claude/data/message-overlay/monspell-phase0-inventory.json \
  --manifest .claude/data/message-overlay/monspell.json \
  --behavior-report .claude/data/message-overlay/monspell-behavior-report.json \
  --candidate-anchor .claude/data/message-overlay/monspell-candidate-anchor.json \
  --glossary docs/glossary.md \
  --review-results docs/monspell-review-results.md \
  --inventory-output /tmp/monspell-inventory-issue59.json
```

候选提交后增加 `--candidate-ref`、`--candidate-english-dump` 与
`--candidate-localized-dump`（三者必须同时提供且要求 `--review-results`），在
clean candidate checkout 中证明 descendant、artifact 与 ledger proposal 的
逐 identity 一致。
