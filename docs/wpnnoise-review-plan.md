# Issue #60 wpnnoise 聒噪武器消息全量校对 — 证据整合计划

> 本计划冻结 Issue #60 的验收边界、证据来源、身份集合、依赖顺序、不对称事实、
> 代码侧延期记录与重入规则，并描述 `docs/wpnnoise-review-results.md` 严格台账的
> 生成与验证方式。v1 阶段只产出证据报告、不落地翻译改动，全部
> adjust/retranslate/defer 候选交人工确认；人工确认后翻译改动已随候选提交
> `1de9250baabffad96f8c945caebde60c62e43000` 落地，工具门禁扩展至
> `4fd31b9b90c0ba095bf982acc37a3f9f5933e551`（v2：reviewed_actions 卡级动作 +
> 候选绑定）。本版文档将严格台账迁移至 v2，并把全部已批准动作绑定到该候选；
> 下一步为 prepared candidate review（review_prepare.sh → 机械路由审阅员 →
> review_final_gate.sh），本阶段不声称最终就绪、不运行最终 review profile。

## 1. 冻结边界与摘要

| 项 | 值 |
|---|---|
| 任务 | Issue #60（[翻译校对][R4][P2] 聒噪武器消息（wpnnoise）全量校对），子任务于 R4（Refs #40） |
| 精确基线 OID | `7b56bccf9ce06646b65acf056b1445ad2999512d`（inventory `baseline_ref`） |
| 工具冻结提交（v1） | `8c3897bbe7b994f37f8c2fc949ee5efac0566660`（wpnnoise 相关生产文件与基线逐字节一致） |
| 翻译落地提交（候选） | `1de9250baabffad96f8c945caebde60c62e43000`（48 处替换 + 12 处插入 + 1 处孤儿删除；候选 ZH 731 变体、EN 731 变体） |
| 候选门禁提交（v2） | `4fd31b9b90c0ba095bf982acc37a3f9f5933e551`（v2 reviewed_actions 卡级动作与候选绑定；仅脚本/测试） |
| 候选 EN dump artifact SHA-256 | `0e539d83c66ace3522e97fe8f7d67fd06766c4953b273f1bab0e31a35f18c1b4`（`/tmp/wpnnoise-candidate-en.json`，与基线 EN 逐字节一致） |
| 候选 ZH dump artifact SHA-256 | `4d5f9e2048f2c7a51811da63ad841182dc5d866c1f64b8337479ab9a07299eb3`（`/tmp/wpnnoise-candidate-zh.json`） |
| Inventory SHA-256（canonical JSON digest，含于文件内 `inventory_sha256`） | `6b3e4d1810be0ffc1c239413a4b98d87ce48b6ce8a0c4b1ef6a485dc089de68e` |
| Inventory 文件字节 SHA-256（格式化 dump） | `fc326a5f8156214860cd330521bd2dbc606f8a9d449baccab69375111d6ac65d`（**非不一致**：canonical digest 排除 `inventory_sha256` 自字段，与格式化文件字节哈希本就不等） |
| Glossary SHA-256 | `95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407`（`docs/glossary.md`，术语权威；resolver 输出 `/tmp/r4-wpnnoise-consolidate-context.txt`） |
| Scope SHA-256 | `e62dac239522913a8ab43547c42c8c42e4ade8a043fc63a9158af9e416dd12be` |
| EN production dump artifact SHA-256 | `0e539d83c66ace3522e97fe8f7d67fd06766c4953b273f1bab0e31a35f18c1b4`（`/tmp/wpnnoise-baseline-en.json`） |
| ZH production dump artifact SHA-256 | `fbc39f38b816797c187710de3faf89f96bc98db4c9cc81c8f656f1af6e8cd5db`（`/tmp/wpnnoise-baseline-zh.json`） |
| 范围常量 | 65 identity；EN 731 变体；ZH 720 变体；EN 84 / ZH 83 随机子串站；EN 2 / ZH 3 Lua 站；VISUAL 6/6；SOUND 1/1；静态-only 0 |
| 本批只读证据 | `/tmp/wpnnoise-review-4.md`（唱歌剑，37 identity）、`-5.md`（噪音族+神器，9）、`-6.md`（低语/帽子，16）、`-7.md`（菌/鳗+代码侧，3） |

inventory 由 `.claude/scripts/wpnnoise_inventory.py` 以 exact-Git 派生 + production
dump 绑定重建，重建结果 `inventory_sha256` 与上述 canonical digest 一致（验证命令见
§16）。报告是证据而非自动 Gold：整合时对每项提议回到原始源文件与消费者代码
独立核对（见 §8 整合规则）。

## 2. 生产边界与源清单

- 英文源：`crawl-ref/source/dat/database/wpnnoise.txt`（SpeakDB 加载序号 3，第 4 个
  源；normalized snapshot SHA-256 `b16f343ed0691574f70b7be7acb460c12834e3dc03b86fbe6d36513468cb5ce3`）。
- 中文源：`crawl-ref/source/dat/database/zh/wpnnoise.txt`（SpeakDB ZH 加载序号 22；
  snapshot SHA-256 `81ccb149399d0d48d1c6329790b182dabb60c86cdb60ea1ad3c6cbe971ad655f`）。
- 加载器：`database.cc` 的 `TextDB("speak", "database/", ...)`；其余 SpeakDB 文件
  （EN monspeak/monspell/monflee/insult/godspeak/monname/colourname/graffiti/miscast；
  ZH FAQ/colourname/decorlines/gizmo/godname/godspeak/graffiti/help/insult/miscast/
  miscname/monflee/monname/monspeak/monspell/montitle/rand_all/rand_arm/rand_wpn/
  randbook/randname/shout）仅参与加载顺序、碰撞与 effective-provenance 证明，
  不取得其翻译所有权。
- 有效 provenance：65 个 key 全部由本文件 effective 定义（无 override、
  无 parse error、无空 body、definition ordinal 从 0 连续）；EN/ZH key 集双向相等。

## 3. 身份边界：28 根 + 37 递归碎片

生命周期 `direct-production-root` 共 28 个根 key（现行调用点直接查询）：
`shield of the gong`、`frozen axe "frostbite"`、`trishula "condemnation"`、
`noisy weapon`、`singing sword silenced|no_tension|low_tension|high_tension|scream`、
`majin-bo greeting|cast|cast weak`、`zonguldrok greeting|reprise|farewell`、
`zonguldrok hat good|okay|bad|crown of dyrovepreva|crown of vainglory|hat of
pondering|hat of the alchemist|hat of the bear spirit|hood of the assassin|mask of
the dragon`、`fungus thoughts`、`eel hand actions|eel hand solo actions`。

生命周期 `recursive-internal-fragment` 共 37 个 key，仅经 SpeakDB 递归 token
（`@key@`）可达；可达性由 inventory 的引用闭包逐 key 证明（fragments ==
referenced，无假设、无孤立碎片、无意外引用根）。

## 4. 依赖顺序与依赖组

按共享依赖排序审阅（同组先校准共享词根/专名/机制）：

| 顺序 | 依赖组 | identity 数 | 成员 |
|---|---|---|---|
| 1 | 锣盾：声音频道与固定响度 | 1 | shield of the gong |
| 2 | 噪音神器武器：寒冷环境拟声 | 1 | frozen axe "frostbite" |
| 3 | 噪音神器武器：审判呼号 | 1 | trishula "condemnation" |
| 4 | 噪音武器：随机聊天与拟声族 | 6 | noisy weapon、_weapon_chatter_、_rare_chatter_、weapon_noises、_instrumental_noises_、weapon_noise |
| 5 | 唱歌剑：静默/张力层级 | 5 | singing sword silenced/no_tension/low_tension/high_tension/scream |
| 6 | 唱歌剑：张力碎片 | 32 | _weapon_noises_low-high_tension_、_singing_no_tension_、_singing_no-low_tension_、_speaking_no_tension_、_common_speaking_no_tension_、_rare_speaking_no_tension_、_speaking_low_tension_、_speaking_low-high_tension_、_speaking_high_tension_、_godless_sorter_、_scream_、_real_song_no_tension_、_real_song_low_tension_、_real_song_low-high_tension_、_real_song_high_tension_、_screams_、_screams_how_、_loudly_、_beastly_adjective_、_beast_、_strikes_up_what_、_kind_of_scales_、_rhyme_word_、_song_theme_、_musical_topic_、_exasperated_、_crimson_、_miscreants_、_pets_、_corpses_、_body_part_、_glorious_ |
| 7 | 马金魔杖：低语包装 | 3 | majin-bo greeting/cast/cast weak |
| 8 | 宗古德洛克：低语包装 | 3 | zonguldrok greeting/reprise/farewell |
| 9 | 宗古德洛克：帽子评论 | 10 | zonguldrok hat good/okay/bad + 7 个 per-unrand key |
| 10 | 菌皮斗篷：思想絮语 | 1 | fungus thoughts |
| 11 | 电鳗之手：风味消息 | 2 | eel hand actions/solo actions |

合计 65。跨组共享：`_instrumental_noises_`/`weapon_noises` 同时被唱歌剑根
（high/low/no_tension 的 4-6 槽）递归消费，批次 B 的修正自动流向唱歌剑显示，
无需二次编辑。

## 5. 消费链与路由

- `NOISY_EQUIPMENT`：`melee-attack.cc:2011`（ARTP_NOISE 攻击）→
  `shout.cc:386 noisy_equipment`（`ScopedLangEn` 稳定英文限定名查询、`NONE`
  抑制、`noisy weapon` 回退）→ `shout.cc:304 item_noise`（控制前缀路由频道、
  token 替换、`[a|b]` 随机子串、`@CAPS@` 展开、按频道 mprf、非 TALK_VISUAL
  时 `noisy(20)`）。非随机神器 key：`shield of the gong`、`frozen axe
  "frostbite"`、`trishula "Condemnation"`（大写 C 与运行时英文名一致）。
- `SINGING_SWORD`：`art-func.h:355` 按静默与 tension 选
  silenced/no_tension/low_tension/high_tension/SCREAM key（loudness
  {0,0,20,30,40}）→ `item_noise`。tier 同时决定 sonic-wave 行为，本批只审显示消息。
- `GONG`：`art-func.h:479-486` 以稳定英文 key 查询，`MSGCH_SOUND` 直显 + `noisy(40)`；
  无 token/随机/前缀处理。
- `WHISPER`：`art-func.h:1207`（Majin-Bo 装备）、`spl-cast.cc:848`（按法术等级选
  cast/cast weak）、`art-func.h:1866/1882`（Zonguldrok 装备/卸下）、
  `player-equip.cc:2198`（帽子评论按 artefact/brand/unrand 英文名派生 key）；
  `make_stringf(T_("A voice whispers, \"%s\""), ...)` 包装经 `MSGCH_TALK` 显示。
- `FUNGUS`：`art-func.h:1893` 装备 + `:1911` world_reacts，`MSGCH_TALK` 直显。
- `EEL`：`player-reacts.cc:1279 _do_eel_flavour_msg` 按 arm_count 选 solo/actions
  key，替换 `@head@`/`@skin@` 后 `MSGCH_TALK` 直显；**不执行
  `maybe_pick_random_substring`**（player-reacts.cc 零调用点），因此 `[a|b]`
  保持字面（EN/ZH 均受影响，上游继承路径）。
- `RECURSIVE`：`database.cc:2307 getSpeakString` → `_getRandomisedStr` 加权选择 +
  递归 `@key@` 展开（:1497，未命中保持原样）+ `_execute_embedded_lua`（:526）；
  Lua 比较字符串（`"No God"`）为协议身份，不得翻译。

## 6. EN/ZH 不对称（冻结事实）

`ASYMMETRIC_VARIANT_KEYS` 冻结 6 个 key 的 (EN, ZH) 变体数：

| key | EN | ZH | 说明 |
|---|---|---|---|
| `_instrumental_noises_` | 13 | 12 | EN-only ordinal 12 为位置伪影：其译文 `在打鼓。` 存在于 ZH:292；真正缺失的是 EN[8] kazoo（+1 错位自 :287 起） |
| `_real_song_no_tension_` | 21 | 19 | EN-only ordinals 19/20 真缺失（兽人金矿 / 我们曾欢笑），提议补齐 |
| `_scream_` | 71 | 70 | EN-only ordinal 70 真缺失（Túrin/Gurthang 引文），提议补齐 |
| `_speaking_high_tension_` | 32 | 33 | ZH-only ordinal 32 为位置伪影：实际多余变体（deus vult + Lua 孤儿）位于 ZH 序数 1（:963-965），致 2-32 整体 +1 错位 |
| `fungus thoughts` | 14 | 7 | EN-only ordinals 7-13 真缺失（7 条消息 ZH 下不可见），提议补齐 |
| `weapon_noise` | 39 | 38 | EN-only ordinal 38 为位置伪影：其译文 `一个沉闷的笑话。` 存在于 ZH:375；真正缺失的是 EN[30] kazoo（+1 错位自 :364 起） |

其余 59 个 key EN/ZH 变体数相等。位置伪影与真缺失由原始文件逐行核对区分，
不预设两语言拓扑逐字相同；每处错位在结果卡 rationale 中记录精确源映射
（如 `_instrumental_noises_` ZH:288 ↔ EN:291）。上述六处不对称在候选
`1de9250b` 中全部消解：候选 ZH 为 731/731（12 处批准插入 + 1 处孤儿删除），
由 v2 候选门禁逐位置证明；基线侧冻结事实与 `ASYMMETRIC_VARIANT_KEYS` 不变。

## 7. 审核证据批次映射（只读）

| 批次 | 报告 | 覆盖 | 结论 |
|---|---|---|---|
| A | `-4.md` | 唱歌剑 37 identity（511 EN / 509 ZH + 3 EN-only + 1 ZH-only） | 44 变体级 fix + 1 孤儿 + 1 跨 identity 命名；0 blocker |
| B | `-5.md` | 噪音族+神器 9 identity（132 EN / 130 ZH） | 2 kazoo 插入 + 1 定向 retranslate；其余 keep |
| C | `-6.md` | 低语/帽子 16 identity（63/63） | 3 definite fix；13 keep；5 style 建议 |
| D | `-7.md` | 菌/鳗 3 identity（18 ZH + 7 EN-only） | 1 完整性 fix（fungus 7 缺失）；2 keep + 3 代码侧 defer 建议 |

整合规则（本阶段执行）：

1. 报告是证据，不是自动 Gold：每项 fix 回到原始 EN/ZH 文件与消费者代码复核；
   与协议（key/权重/控制前缀/token/Lua/随机站形状）冲突的提议拒绝。
2. 采纳全部审阅员确认的 definite fix；style-only 建议降级为拒绝项或 rationale
   记录，不改动文本。跨 identity 命名（唱歌剑 → 歌唱之剑，
   `i18n/zh/source.txt:28516` canonical）计入 fix。
3. 逐 identity 按冻结 inventory 的 ZH 变体序数出卡：每个现行 ZH 变体恰好一张
   变体审阅（keep/adjust/retranslate/defer），提议文本逐字记录；卡级结论按
   validator 聚合规则（retranslate > adjust > defer > keep）得出，不得手工覆盖。
4. 错位/缺失内容不伪造序数 EN 对应：精确源映射（文件行 ↔ EN ordinal）写入
   rationale，使用台账 schema 的 locator 模型（variant_ordinal = ZH 文件序数）。
5. 一票一写：本阶段只写 `docs/wpnnoise-review-plan.md` 与
   `docs/wpnnoise-review-results.md`；`zh/wpnnoise.txt` 与脚本/测试/glossary/
   decisions 一律不动。

## 8. 台账 schema（docs/wpnnoise-review-results.md）

严格块标记 `<!-- BEGIN STRICT WPNNOISE REVIEW EVIDENCE v2 -->` /
`<!-- END STRICT WPNNOISE REVIEW EVIDENCE v2 -->`，内含唯一 fenced jsonl 块：
第 1 行为 metadata（baseline、glossary_sha256、inventory_sha256、identity_count、
双侧 dump artifact SHA、变体/随机站/Lua 站计数、`terminal_conclusion_counts`），
随后按 inventory entry 顺序（key 字典序）每 identity 一行卡。卡字段、变体字段、
production_facts 字段、聚合与 defer 校验均以 `wpnnoise_inventory.py` 的
`validate_results` 为准（本计划不复制 schema）。

v2 在每张卡上新增必填字段 `reviewed_actions`（无动作卡为空列表）：动作记录字段
`{kind, variant_ordinal, text, rationale}`。`kind=add` 绑定基线 EN-only 缺失变体
（按基线 EN 序数），要求批准文本的协议（控制前缀/runtime token/随机子串站/
Lua 站/比较串）与基线 EN 变体逐项一致；序数落在现行 ZH 变体数内的 add 必须借
占位 proposal 槽（kazoo 卡即此约定）。`kind=remove` 绑定 ZH-only 孤儿（按基线
ZH 序数），要求文本与基线 ZH 变体逐字节一致。add 序数是候选（最终）位置、
remove 序数是基线位置，由双指针 walk 映射，不做其他序数配对假设。

## 9. 缺失变体与孤儿决策的表示（v2 卡级动作）

- v1 的 `proposed_translation` 长度必须等于现行 ZH 变体数、`variant_reviews`
  只覆盖现行 ZH 变体：**新增**（kazoo、fungus 7 条、`_real_song_no_tension_`
  19/20、`_scream_` 70）与**删除**（`_speaking_high_tension_` 孤儿）属变体数量
  变更，v1 无法以字符串提议表达；v2 以卡级 `reviewed_actions` 表达并绑定候选。
- v2 动作明细（六张动作卡，共 13 条动作）：`_instrumental_noises_` add@8、
  `weapon_noise` add@30（kazoo 插入，占位约定：proposal[8]/proposal[30] 即插入
  文本）；`_real_song_no_tension_` add@19/add@20；`_scream_` add@70；
  `fungus thoughts` add@7-13；`_speaking_high_tension_` remove@1（基线 ZH
  ordinal 1 的精确 deus-vult 文本；ordinal 1 的 defer terminology 变体审阅保留
  v1 结论）。
- 位置伪影（`_instrumental_noises_` [12]、`weapon_noise` [38]、
  `_speaking_high_tension_` zh_only [32]）保留为冻结 production_facts，并在
  rationale 中注明真实缺失位置与源映射。
- 卡级结论按聚合规则不变：`fungus thoughts` 现行 7 变体全 keep ⇒ 卡级 keep，
  完整性修复以 add@7-13 动作落地；`_instrumental_noises_` 与 `weapon_noise` 以
  错位槽（ordinal 8/30）承载 kazoo 提议 ⇒ 卡级 adjust。
- 落地与绑定：上述全部动作已按人工确认随候选 `1de9250b` 落地；候选门禁
  `4fd31b9b90` 要求候选 EN 与基线逐字节一致、候选 key 集双向相等（全 key
  EN==ZH，无残留单边变更），每候选变体为已批准 add（协议与 EN 定位器一致）或
  匹配基线变体（权重不变、文本=审阅 proposal 或占位保留）；未审阅的
  key/权重/控制/token/Lua/随机站漂移、多余插入/删除/重排全部失败关闭。

## 10. 代码侧发现与 defer implementation 记录

本阶段独立追踪确认（不修代码，仅记录证据；翻译 token 一律保留）：

1. **家族级英文冠词泄漏**（确认）：`shout.cc:358-362`
   `@The_weapon@→"The @weapon@"` 等 + `:312-313` 非随机神器前置改写，随后拼
   `item.name(DESC_BASENAME)`；ZH 构建显示如 `The 歌唱之剑` / `Your 歌唱之剑`。
   批次 D 审阅员发现、批次 A 唱歌剑审阅员未发现；本次独立追踪 shout.cc 确认。
   记录为 `defer implementation`（owner=crawl-coder）于家族代表载体：
   `trishula "condemnation"` v0（NOISY_EQUIPMENT 族）与 `_real_song_high_tension_`
   v0（SINGING_SWORD 族）；其余 17 个含武器 token 的 identity 在 rationale 记录
   该泄漏与载体位置（卡级结论仅在聚合允许处改为 defer implementation，不扩大
   措辞所有权）。
2. **电鳗 `@head@` 英文泄漏**（确认）：`player-reacts.cc:1286-1287` 硬编码
   `"form"/"head"` 字面量（无 T_()/ZH 分支；对比 `@skin@` 经
   `species::skin_name` 正确本地化）。记录为 `defer implementation` 于
   `eel hand actions` v0 与 `eel hand solo actions` v1（owner=crawl-coder）。
3. **电鳗 `[a|b]` 不展开**（确认）：`_do_eel_flavour_msg` 从不调用
   `maybe_pick_random_substring`（player-reacts.cc 零调用点），EN/ZH 均按字面
   显示；ZH 忠实镜像，不得单方面改动括号。记录为 `defer implementation` 于
   `eel hand solo actions` v0（owner=crawl-coder）。

`eel hand actions` / `eel hand solo actions` / `trishula "condemnation"` /
`_real_song_high_tension_` 四卡的翻译结论均为 keep（proposal==current），卡级
结论按任务指示记录为 `defer implementation`（聚合允许），deferral 三字段齐备。

## 11. 排除项（非目标）

- 不修改噪声数值、触发概率、tension 算法、Singing Sword sonic-wave、神器机制、
  RNG 或存档 identity。
- 不取得 `monspeak`/`monspell`/`monflee`/`shout`/`insult`/`godspeak`/`graffiti`/
  `decorlines` 的翻译所有权；其他 SpeakDB 文件仅用于加载、碰撞、递归与
  provenance 证明。
- 不重审已完成的神器名称/描述、神祇名称或种族名称；输入未变化时引用既有
  裁定（含 D-A-049 Zonguldrok → 宗古德洛克）。
- 不将 source-only 定义自动等同于可达玩家消息；可达性由 inventory 闭包证明。
- 不新增第二套 final gate、全局质量分数或自动 Gold；不运行最终 review profile。
- 不修改 C++/Lua/构建/glossary/decisions/脚本/测试。

## 12. 人工确认停止点与落地状态

v1 阶段在证据报告处停止：`docs/wpnnoise-review-results.md` 的 65 张卡与全部
变体提议（含缺失变体建议文本、孤儿删除建议、代码侧 defer）提交人工确认，
**不落地 `zh/wpnnoise.txt` 改动**。人工确认后，翻译改动已由单一 `zh-translator`
按批次顺序随候选 `1de9250b` 落地（48 处替换 + 12 处插入 + 1 处孤儿删除，
`zh/wpnnoise.txt`），工具门禁 `4fd31b9b90` 提供 v2 候选绑定证明。

本阶段只做文档迁移：将严格台账升级到 v2（卡级 `reviewed_actions`），并把它
与候选 `1de9250b` 精确绑定（验证命令见 §14）。不修改任何 ZH/EN 资产、脚本、
测试、glossary、decisions。剩余下一步是 prepared candidate review：按
review-contract 由 `review_prepare.sh` 准备不可变候选、机械路由审阅员、记录
readiness，最后由 `review_final_gate.sh` 单次运行最终 profile；本阶段不运行
最终 review profile、不声称最终就绪。

## 13. 重入规则

- 通用：英文或中文 TextDB source、production key/variant/weight/control/token/
  Lua/随机子串拓扑、database.cc 加载顺序与递归、shout.cc/art-func.h/
  player-equip.cc/player-reacts.cc 消费者语义、docs/glossary.md 权威变化时
  重新审阅。
- 代码侧 defer：冠词泄漏与 `@head@` 泄漏在 `item_noise`/电鳗路径改为语言感知
  处理或引入集中式 token 替换层后重验显示；`[a|b]` 展开在电鳗路径接入
  `maybe_pick_random_substring` 后重验 solo v0。
- 孤儿：已以 v2 remove@1 动作表达并随 `1de9250b` 落地（候选 ZH 33→32），
  候选门禁证明前移对齐；基线 inventory 保持冻结。若候选 ZH 拓扑再次变化（新增
  EN-only 变体或新的 ZH-only 孤儿），更新 `_speaking_high_tension_` 卡的
  reviewed_actions 并重跑候选门禁。
- 缺失变体：已以 v2 add 动作表达并随 `1de9250b` 落地（kazoo ×2、`_real_song_`
  no_tension 19/20、`_scream_` 70、fungus 7-13），候选门禁逐位置证明协议一致；
  基线 `ASYMMETRIC_VARIANT_KEYS` 冻结保留。若 EN 源再次新增变体，更新相应卡的
  动作并重跑候选门禁。

## 14. 验证

- 严格台账（v2）：`bash .claude/scripts/wpnnoise_inventory.py --baseline-ref
  7b56bccf9ce06646b65acf056b1445ad2999512d --english-dump
  /tmp/wpnnoise-baseline-en.json --localized-dump /tmp/wpnnoise-baseline-zh.json
  --inventory-output /tmp/wpnnoise-inventory-v2.json --review-results
  docs/wpnnoise-review-results.md --glossary docs/glossary.md`，要求 exit 0、
  inventory/reviewed 双向相等、每卡聚合一致、defer 三字段齐备、每卡
  reviewed_actions 合规、metadata 计数一致，且重建 inventory digest ==
  `6b3e4d18…`。
- 候选绑定（精确）：同一命令追加 `--candidate-ref
  1de9250baabffad96f8c945caebde60c62e43000 --candidate-english-dump
  /tmp/wpnnoise-candidate-en.json --candidate-localized-dump
  /tmp/wpnnoise-candidate-zh.json`（dumps 为 exact-Git 全量布局生成，SHA-256 见
  §1），要求 exit 0、候选 EN 与基线逐字节一致（`0e539d83…`）、65 identity /
  731 ZH 变体全部接受、candidate_sha256 == `315863293f32fbbaccff403d5e3acf7f0
  7aa55c09d5a8a89c4a92cd83cd0f84f`。候选门禁要求候选为 exact clean HEAD；
  本 worktree HEAD 为工具提交时，经 `/tmp/run_wpnnoise_docs_gate.py` 仅 mock
  该守卫（4fd31b9b90 建立的驱动模式），其余全部为真实生产代码路径。
- 本计划与结果文件不做其他 lint（仓库无 markdown linter）；结果文件由上述
  严格解析器同时充当结构校验。
