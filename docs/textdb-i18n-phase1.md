# TextDB 消息国际化 Phase 1 实施记录

状态：**Phase 1 已完成基础设施与两个初始纵向迁移，并启用首个生产
`CASE_MAP`；Phase 2 已完成八批通用施法消息迁移、一次 21-key 分片并行
试点，以及 Wave B、C、D 的并行迁移。当前 catalog 跟踪 128 个 canonical
key、161 个 canonical variant；其中 125 个 key、158 个 variant 进入
structured 路径，另有 3 个完整 key 显式标记为 `LEGACY_ONLY`。**

本文记录 [`textdb-i18n-architecture.md`](textdb-i18n-architecture.md) 的
Phase 1 实际实现范围。Phase 0 基线提交为 `070f812bb6`；Phase 1 在独立分支
`codex/textdb-i18n-phase1` 上实现，不修改通用 TextDB 语法，也不装载新的
TextDB 文件。

## 1. 实际迁移范围

当前共迁移 125 个完整 key 闭包，并为 3 个暂不适合结构化的完整 key 固定
`LEGACY_ONLY` 路由。Phase 1 的两个初始 key 为：

| canonical key | stable ID | 策略 | 选择理由 |
|---|---|---|---|
| `beam catchall cast` | `mon.cast.beam_catchall.v1` | `NONE` | 单一 weight-10 变体；无成功递归、Lua 或 `[a|b]`；不依赖 foe/god/visual 条件；可完整复现 target relation 与 beam 显示 |
| `march of sorrows bone dragon cast` | `mon.cast.march_of_sorrows_bone_dragon.v1` + 两个稳定 case ID | `CASE_MAP` | 单一变体、单一二选一站点、无递归/Lua；原有 targeted binding 时序可保持不变 |

两个 canonical English 快照为：

```text
@The_monster@ throws @beam@ @at@ @target@.
@The_monster@ breathes [collective despair|endless sorrows] @at@ @target@.
```

模板使用 TextDB 不识别的 `${slot}`：

- EN：`${actor} throws ${beam} at/next to/past ${target}.`
- ZH `AT`：`${actor}向${target}射出${beam}。`
- ZH `NEXT_TO`：`${actor}朝${target}旁边射出${beam}。`
- ZH `PAST`：`${actor}射出${beam}，从${target}旁边掠过。`

`march of sorrows bone dragon cast` 将 option index `0/1` 分别映射到两个全局
稳定 case ID：

- `mon.cast.march_of_sorrows_bone_dragon.collective_despair.v1`；
- `mon.cast.march_of_sorrows_bone_dragon.endless_sorrows.v1`。

两者分别渲染“集体的绝望”和“无尽的悲伤”，同样提供 `AT/NEXT_TO/PAST`
三套 EN/ZH 模板。case ID 与 variant ID、其他 case ID 和 tombstone 共享全局
唯一命名空间。

`zh/monspell.txt` 未修改。structured 中文不从该文件选择变体，也不执行中文
递归、Lua 或正文随机。

`Vanquished Vanguard Nergalle cast` 已通过窄 `CAPTURE_SLOT` 迁移。三个
`@orc name@` 不穷举组合，而是从同一次 canonical English 递归展开 trace 捕获三个
有序的最终名字，并以 inventory closure 约束的 leaf vocabulary 验证。
其余未列入 catalog 的 `monspell` key 均在查询和 RNG 之前进入当前语言的 legacy
路径。`CASE_MAP` 当前只允许无递归、无 Lua、恰好一个至少包含两个选项的有限
`[a|b]` 站点；
`CAPTURE_SLOT` 只启用上述“三个 `orc name`、leaf-only vocabulary、无 Lua/
`[a|b]`”严格切片；其他 capture 形状仍被生成期与加载期拒绝。

Phase 2 又完整迁移 `ensnare arachne cast` 的 2 个 variant 和
`guardian serpent cast targeted` 的 3 个 variant。structured descriptor 通过
`binding.resolves_target` 独立声明是否执行目标解析，因此模板可以不引用
`${target}`。当 `resolves_target=true` 时，即使模板不引用 target，仍恰好执行
一次目标解析并保留其 RNG trace；当其为 `false` 时则完全跳过目标解析。
`implies_gesture` 已作为逐行显式元数据接入目标解析前的 binding requirements；
`audible=true` 与非默认 applicability 仍由生成期和加载期拒绝。

当前 actor 槽支持 `actor_ref`、`actor_possessive_name`、
`actor_possessive_pronoun` 与 `actor_reflexive`。模板可仅声明所需的 actor 槽；
加载期和运行时只验证实际声明的字段。中文模板可省略英语语法需要的所有格或
反身代词，但整个 EN/ZH 模板矩阵的 slot schema union 必须与声明一致。

下一批完整迁移 `wizard cast targeted`、`wizard cast`、
`magical cast targeted` 与 `magical cast`，合计 8 个 variant。targeted descriptor
使用 `binding.resolves_target=true` 和 `AT/NEXT_TO/PAST` 关系矩阵；non-target
descriptor 使用 `binding.resolves_target=false` 和唯一 `NONE` 关系。后者禁止
声明 `resolved_target` 槽，也不会调用 `resolve_speech_target()`、消费目标 RNG 或
产生 target trace。`NONE` 是强类型关系，不以伪 `AT` sentinel 表示。

第三批低风险迁移覆盖 7 个完整 key 闭包、10 个 variant：
`awaken flesh kobold fleshcrafter cast`、`dispel undead revenant cast`、
`malign offering priest cast`、`sheza's dance cast`、
`silent blizzard demon cast`、`ushabti cast targeted` 与 `mennas cast`。
其中 targeted descriptor 继续显式声明三种 target relation；其余 descriptor
使用 `NONE`。每个 variant 的 `implies_gesture` 均由 metadata 表达，不再依赖
本地化正文关键词。`mennas cast` 还首次迁移了 `VISUAL` sensory/channel
metadata：模板正文不携带 `VISUAL:` 协议前缀，renderer 生成的 line metadata
保持现有视觉可见性和输出频道语义。

第四批完整迁移 `airstrike blizzard demon cast` 的 3 个 variant，gesture
metadata 为 `[false, true, false]`，全部使用
`resolves_target=false` / `NONE`。第三个 variant 的 legacy
`@possessive@ @arms@` 被收敛为 `actor_possessive_pronoun` 与窄类型
`actor_arms_plural` 槽。production binding 从
descriptor 派生 `needs_actor_arms_plural`，仅该 slot 存在时才严格按 legacy 顺序
调用 `arm_name(false, &can_plural)`，可复数时再调用 `arm_name(true)`；其他
structured key 不检查身体部位，也不新增 chaos spawn 的 RNG。真实暴雪恶魔的
canonical plural 为 `strata`，中文通过
`monster body part plural|strata` 的 literal-only context key 显示为“云层”。
未知 body-part 或不可复数 caster 均 fail closed 为 `CORRUPT`，不会让
任意 legacy token 或未经审计的动态翻译穿透 renderer。不可复数错误边界不再输出
legacy 的 `NO PLURAL ARMS`；该边界保持 RNG 消耗等价，但采用更严格的显式协议错误。

第五批完整迁移 `vv cast` 的 4 个 variant 与
`smiting jeremiah cast` 的 5 个 variant。两者均为 non-target descriptor，
使用 `resolves_target=false` / `NONE`，不解析目标也不消费目标 RNG。
`vv cast` 的上游权重为 `[10, 10, 10, 3]`，四行均保留 `VISUAL` sensory，
gesture metadata 为 `[true, false, false, false]`；Jeremiah 的第三行保留
`VISUAL` sensory，其余四行保持 `PLAIN`，gesture metadata 全为 `false`。
这 9 个 variant 仅复用既有 actor/possessive 槽，不引入新的身体部位、目标或
正文随机物化需求。

structured 中文 actor possessive binding 另有一个窄语法适配：当 caster 可见、
使用 neutral pronoun，且 `mons_is_or_was_unique()` 证明其为单一身份时，
`${possessive}` 使用 context key
`structured actor possessive|neutral singular` → “其”。这修正 Jeremiah 的
英文 singular-they `their` 被全局中文 pronoun 表投影成“它们的”的问题，但不修改
通用 pronoun 表。非 unique neutral actor 因没有单数身份保证，仍保留既有
“它们的”；女性 Vv 仍正常使用“她的”。英文 binding 始终保持 legacy pronoun。

第六批完整迁移 `cantrip gastronok cast` 的 9 个 variant；前 8 个权重 10，
最后一个权重 5。ordinal 1–3 显式声明 `VISUAL` sensory 与
`requires_caster_visible=true`，ordinal 4–8 的 `You...` 行显式声明
`requires_player=true`；其余 applicability 均为 false，9 个 variant 的
`implies_gesture` 均为 false。runtime player applicability 由
`resolve_mon_speech_applicability()` 与 legacy `invalid_msg()` 共享同一
`_get_foe()` 语义，包括 friendly caster 在 foe index 无效时回退玩家的规则。
applicability 在 canonical English variant 已选定、原有选择 RNG 已消耗后，
但在 binding/target/beam callback 前判定；不适用时继续下一个 candidate，
不会重抽同一 key。silent-unprefixed fallback 仍按既有
`ACCEPT_ANY_NONEMPTY` 绕过第二次 applicability 检查。

第七批完整迁移 `hellfire mortar wiglaf cast` 的 3 个 weight-10 variant。
ordinal 0 保留 `VISUAL` sensory 并声明
`requires_caster_visible=true`；behavior audit 证明三行均不命中现有 gesture
heuristic，因此 `implies_gesture` 均为 false。ordinal 1–2 同时保留两套独立
语义：`@at@` 仍由唯一一次 `resolve_speech_target()` 解析
`AT/NEXT_TO/PAST` relation 及其 RNG trace，`${foe}` 则由窄类型
`resolved_foe` binding 解析 player 或 monster foe。normal attempt 的
`requires_foe` 在 canonical variant 选择后、binding 前使用与
`invalid_msg()` 相同的 snapshot 判定；无 foe 时继续下一个 candidate，且不执行
target RNG。foe 显示与 legacy replacement 同构：player 为 `you`/“你”，monster
按 friendly non-unique/non-arena 的 `DESC_YOUR` 与其余 `DESC_THE` 分支命名，
并保留 `'` 后缀裁剪。silent-unprefixed 仍绕过 applicability；若 replacement
语义也无法解析 foe，则 structured binding fail closed 为 `CORRUPT`，不会泄漏
`@foe@`。

第八批完整迁移 `vanquished vanguard nergalle cast` 的 2 个 variant。
ordinal 0 使用窄 `CAPTURE_SLOT`：canonical English 仍按既有顺序完成顶层选择、
三个 `orc name` 递归选择及其 leaf 选择，并从同一 trace 按出现顺序捕获三个最终
replacement；EN/ZH renderer 共享这三个捕获值，不重新抽取。loader 将依赖闭包、
捕获站点数量与顺序、模板槽、103 项 leaf vocabulary locator 及最终 replacement
逐项绑定，重复名字合法，未声明正文或畸形 trace 均 fail closed。ordinal 1 使用
`NONE`，保留固定台词。该迁移消除了最后一个 behavior
`UNANALYSABLE` occurrence。随后从正常 `monspell` legacy 路径删除了由本地化
正文关键词推断 `gestured` 的嗅探；ordinary uncovered legacy targeted 消息仍执行
`@at@` / `@target@` / `@beam@` replacement，但固定以 `gestured=false` 解析目标。
仅当 overlay 非 `ENABLED` 或语言不受支持，且 canonical key 是 compiled catalog
中的 `CANDIDATE` 时，typed compatibility fallback 才保留旧嗅探，以兑现 safe
fallback 的行为与 RNG 契约。

随后进行一次 21-key 分片并行试点，新增 22 个 canonical variant。人工 manifest
由 `000-baseline.json`、`100-wave-a1-pilot.json`、
`110-wave-a2-pilot.json` 与 `120-wave-a3-pilot.json` 四个独立 fragment 组成；
顶层 `monspell.json` 只声明 catalog 顺序和 `fragment_glob`。三个 worker 各自只
拥有一个 pilot fragment，集成者统一执行全局 stable/case/tombstone 唯一性检查、
确定性排序并生成唯一 sidecar，避免并行分支同时改写共享 JSON 数组和生成文件。
这次试点只把 catalog 从 21 个 key 扩至 42 个，不表示其余 `monspell` root 已迁移。

Wave B 随后由 `200-wave-b1.json`、`210-wave-b2.json` 与
`220-wave-b3.json` 三个独立 fragment 并行新增 30 个 actor-only key、30 个
canonical variant。它们均使用 `NONE`、仅声明 `${actor}`，并保持
`resolves_target=false`。`ostracise cast` 的英文虽然出现 “your soul”，其
applicability 仍按 legacy 行为保持 `requires_player=false`，其他
`requires_*` 也均为 false；catalog 不从翻译或正文代词推导候选适用条件。

Wave C 由 `300-wave-c1.json`、`310-wave-c2.json` 与 `320-wave-c3.json`
并行新增 26 个 key、26 个 canonical variant。C1/C2 覆盖 18 个 unseen 消息，
使用无槽纯模板；所有以 `You` 开头的 variant 显式声明
`requires_player=true`，其余 applicability 保持 false。C3 覆盖 8 个 visible
actor-only 消息并声明 `${actor}`。三组均为单一 `NONE` 变体、
`resolves_target=false`、`PLAIN` sensory，且无递归、Lua、`[a|b]`、gesture 或
audible metadata。集成后 catalog 为 98 个 key、129 个 canonical variant、
258 个逐语言验证单位。

Wave D 由 `400-wave-d1.json`、`410-wave-d2.json` 与 `420-wave-d3.json`
并行审计 30 个 key、32 个 canonical variant。其中 27 个 key、29 个 variant
进入 structured 路径；`acid splash cast`、`branch summon cast prefix` 与
`chilling breath cast` 的 3 个 variant 显式保留为 `LEGACY_ONLY`。后者仍属于
catalog 的完整 key 闭包和年度漂移审计范围，但不进入运行时 structured 覆盖表，
也不计入 structured behavior metadata 单位。三者当前都没有 legacy behavior
heuristic occurrence，因此不增加 `remaining_legacy_behavior_occurrences`，也不
阻断 `phase2_ready`。Wave D 集成后的 catalog 总量为 128 key、161 variant；
structured 覆盖为 125 key、158 variant、316 个逐语言验证单位。

## 2. 三类 artifact 的职责

### manifest

`.claude/data/message-overlay/monspell.json` 是人工复审入口和聚合头，保存 schema、
inventory fingerprint、语言集合、显式 catalog 顺序与 fragment glob。实际条目由
`.claude/data/message-overlay/monspell/*.json` fragments 保存：

- stable ID 与 tombstone；
- canonical/selection fingerprint、variant ordinal、权重与英文快照；
- 完整闭包依赖及 fingerprint；
- applicability、`cast_frame` 和物化策略；
- `${slot}` schema、逐行 sensory/channel/behavior 元数据；
- EN/ZH 最终纯模板。

它不是 TextDB 文件，不参与 SpeakDB 装载，也不覆盖既有 key。

### generated sidecar

`crawl-ref/source/fork-message-overlay.generated.inc` 由
`.claude/scripts/generate_message_overlay.py` 从 manifest 与 Phase 0 inventory
确定性生成，供 C++ 只读加载。禁止人工编辑。`--check` 必须逐字节通过。

### runtime catalog module

`fork-message-overlay.{h,cc}` 负责加载期验证、覆盖表、五态状态机、canonical
materialization、纯模板 renderer 和只读诊断。它不解析新的 TextDB 语法。

加载期会一次性验证 schema、inventory fingerprint、完整 key/variant 闭包、权重、
快照、依赖、stable ID/tombstone、策略、槽、语言/关系模板矩阵和频道。缺失、损坏、
未知 schema 或闭包不完整会禁用整个 `monspell` structured 域；首次查询即走
legacy，不发生抽取后 fallback。

## 3. 生产调用链

`databaseSystemInit()` 在任何施法消息查询前验证 overlay。`mon-cast.cc` 的候选
搜索对每个实际 lookup key 先调用覆盖路由，然后严格保留原状态机：

```text
MISSING       → 下一个候选；silent prefixed 时重试无前缀
SUPPRESS      → 立即停止并保持沉默
INAPPLICABLE  → 下一个候选；silent prefixed 时重试无前缀
RENDERED      → 立即输出
CORRUPT       → 立即停止，不查询 legacy、不重放 Lua、不额外消耗 RNG
```

因此：

- normal `beam catchall cast` 直接 structured；
- `silent beam catchall cast` 仍先按 legacy 查询，缺失后无前缀 key structured；
- `unseen beam catchall cast` 缺失后继续下一个候选，不错误重试 base key；
- 不支持 overlay 的语言在任何 canonical 抽取前直接 legacy。

structured 调用顺序为：

```text
canonical English 顶层选择
→ 既有递归/Lua expansion
→ __NONE 与 applicability
→ 若 resolves_target=true，一次目标解析（附只读 trace observer）；
  否则跳过且不产生 target RNG/trace
→ canonical @The_monster@/@at@/@target@/@beam@ 绑定
→ 既有 [a|b] materializer
→ stable locator/signature
→ 当前语言纯模板与 ${slot} 渲染
→ 按逐行 metadata 输出
```

`materialize_bound_legacy_randomness()` 只接受已绑定 `@at@/@target@/@beam@` 的
canonical pattern；未选择输入或残留 token 返回 `CORRUPT`，且 RNG 不动。动态
物化签名包含顶层/递归变体、Lua 结果和每个 `[a|b]` 站点身份/选项，禁止执行后
丢弃。`beam catchall cast` 的签名为 `NONE`；March 条目的两个签名以
`materialization-v1` 编码同一 locator 和唯一站点，并分别以 option index `0`
与 `1` 结尾。生成期和加载期都从 canonical key、variant ordinal 和选项数量
重建完整集合，同数量但伪造的 signature 也会禁用整个 structured 域。

## 4. owning 类型与显示边界

生产模型包含：

- `resolved_target`：relation、visibility、PLAYER/SELF/MONSTER/FEATURE/LOCATION/
  THIN_AIR/INDEFINITE/ERROR tagged kind、位置、feature、actor mid 与 owning display；
- `resolved_beam`：canonical/localized display、配置 name/short_name、spell、flavour、
  real flavour、pierce 与 ranged-attack presence；
- `cast_context`：frame、caster visibility、spell 与 god 数据；
- 逐行 sensory、channel、`implies_gesture`、`audible`；
- 完整 canonical TextDB、Lua、target 和 `[a|b]` owning trace。

canonical English 与当前语言显示值在一次 binding callback 内生成。
`resolves_target=true` 时目标解析恰好执行一次，且先于 beam 与 actor binding；
`false` 时目标解析执行零次。临时 `ScopedLangEn` 只重建已选实体的 owning
English 显示，不重新查询 `monspell`，也不消耗 RNG。

structured line 进入 `mons_speaks_msg()` 时标记为 `already_rendered`：不再运行
`do_mon_str_replacements()`、`[a|b]` 或正文频道前缀解析。本地化正文即使以
`ERROR:`、`WARN:` 等开头，也不能改变频道。多行只能由 catalog 的多条 line
metadata 表达；单个模板内嵌换行会被生成期、加载期和 renderer 拒绝。

legacy 路径继续运行既有 replacement、`invalid_msg()` applicability、silent
fallback 与通用频道/输出逻辑；但 `mon-cast.cc` 不再扫描中英文正文来决定
`gestured`。generic `mon-speak` 的 `VISUAL` candidate applicability 和频道前缀
parser 仍为其他 TextDB 域保留，不属于本次删除范围。

## 5. 诊断与年度升级

只读计数包括 overlay hit、legacy route、inapplicable、suppressed、corrupt 和
unknown schema，并带 domain/schema。测试证明读取或预先改变计数不会改变输出、
RNG state 或 count。

年度上游升级时：

1. 用 Phase 0 production dump 重新导出 canonical English；
2. 运行 monspell inventory diff，人工分类 key/variant/weight/token/递归/Lua/
   `[a|b]`/control-prefix 漂移；
3. 对 `beam catchall cast` 的语义变化人工决定沿用 ID 或创建新 ID；工具不得自动
   批准重绑定；
4. 更新 manifest，运行 generator，检查 sidecar 幂等；
5. 运行 overlay audit、Phase 0/Phase 1 Catch2、code/review verifier；
6. 未证明完整闭包的新 key 保持 legacy。

## 6. 验证证据

实现阶段已经观察到以下结果（均为退出码 0）：

- `[message-overlay]`：28,819 assertions / 28 test cases；
- `[textdb][phase0]`：736,197 assertions / 18 test cases；
- `[mon-cast-target][phase0]`：640 assertions / 5 test cases；
- Python manifest/generator tests：15 tests；
- monspell behavior 审计 fixture：18 tests；
- `audit_message_overlay.py`：`message overlay audit: ok`；
- generated sidecar `--check`：逐字节通过；
- `scan_varargs_string.py`：0 个阻塞问题；
- `scan_i18n_lifetime.py --require-parser`：0 个持久借用指针问题；
- affected Catch2 executable 完整链接成功。

Phase 1 精确测试覆盖：五态、normal/unseen/silent、加载失败、English legacy
输出/RNG、EN/ZH canonical 与 target trace、真实 `[casts|pitches]` 和
`[pulses|vibrates]`、关系/目标/可见性快照、CORRUPT 无 fallback、多行 metadata、
协议残留、本地化正文不参与频道判断，以及诊断无副作用。生产 CASE_MAP 另对
March 条目固定运行 1,024 seeds，逐 seed 核对 option index、全局稳定 case ID、
英文逐字节结果、中文投影、三种目标关系和纯 renderer 不改变 RNG；Phase 0 对同一
key 的既有 1,024-seed 测试继续证明 canonical、真实目标解析、substring 与 legacy
最终 RNG/英文输出等价。

统一 verifier 现在无条件运行 manifest/generator/audit 和 behavior fixture；相关文件发生变化时，
code/review/CI profile 还会构建并运行完整 `[message-overlay]` 测试集，覆盖
Phase 1 基础设施与 Phase 2 production/runtime golden。

## 7. 已知限制与 Phase 2 门禁

- structured 覆盖为 125 个 key、158 个 canonical variant；catalog 另跟踪
  3 个 `LEGACY_ONLY` key，因此总量为 128 key、161 variant。这仍不代表 262 个
  `monspell` root 已迁移；
- `CASE_MAP` 仅启用单有限站点子集；`CAPTURE_SLOT` 仅启用 Nergalle 的三个
  `orc name`、leaf-only vocabulary、无 Lua/substring randomness 窄切片；
- catalog renderer 已接线 actor、actor possessive/reflexive、target、foe 与 beam
  类型化槽，并通过 `binding.resolves_target` 将目标解析需求与 `${target}` 引用解耦；
- neutral singular 的中文 actor possessive 只在“可见 + unique identity”边界
  使用 context key“其”，不会把非 unique neutral actor 自动单数化；
- structured gesture、`VISUAL` sensory/channel、`requires_player`、
  `requires_foe` 与 `requires_caster_visible` 元数据已启用；audible、
  requires named foe/god 尚未启用；
- 正常 `monspell` 路径不再嗅探 gesture 正文；structured gesture 仅来自
  descriptor `implies_gesture`，ordinary legacy targeted 固定传入
  `gestured=false`；故障/不支持语言的 typed compatibility fallback 保留旧嗅探；
- 当前 canonical `monspell` 闭包无 Lua；未来出现 Lua 或不可控副作用时，在建立
  完整契约前必须 `LEGACY_ONLY`；
- 其他 TextDB 域没有迁移。

删除操作依赖 behavior audit 的强门禁：`phase2_ready=true`、
`remaining_legacy_behavior_occurrences=0`、`unanalysable_occurrences=0` 和
`fail_closed_behavior_roots=0`。未来上游新增任何可达的 legacy
gesture/visual/audible 正 behavior occurrence，审计会重新关闭门禁。

### 7.1 candidate key recipe seam

`mon-cast-message-keys.{h,cc}` 是怪物施法 candidate key 顺序的唯一算法源。
`mon-cast.cc` 中的薄 adapter 通过显式 `mons_type_name_en(..., DESC_DBNAME)` 取得
canonical English 怪物 type/species/genus 片段，并按现有运行时路径取得
`spell_english_name()`、body shape、intelligence、Hoarfrost finale 状态与
`bolt::get_short_name()`；它只把这些值快照到 owning `recipe_input`，再物化纯
`key_recipe`。builder 不读取 RNG、TextDB、Lua、全局语言或其他运行时状态，且不对
type/species/genus 重复候选去重。

beam key 在 recipe 中保留为显式 `BEAM_SHORT_NAME` expression；containment dump
在 expression 层处理该 token，不依赖当前语言下的 runtime materialization。
运行时仍注入 `get_short_name()`。现有 `short_name + " beam " + " cast"` 产生的
双空格是兼容契约，当前 seam 与 golden test 会逐字保留它。candidate containment
dump 应直接消费这份 recipe，不能另写一份候选顺序算法。

monster type/species/genus candidate 已不再受 locale 影响；现有
`mons_type_name()` 显示行为保持不变。`BEAM_SHORT_NAME` 的 locale-dependent runtime
物化、双空格行为修正及相应 DB 漂移仍必须放在后续独立行为变更中，并分别提供
EN/ZH 与 RNG golden。

### 7.2 candidate closed-world upper-bound dump

离线审计模块 `catch2-tests/monspell_candidate_artifact.{h,cc}` 只进入
`TEST_OBJECTS`，不进入游戏或 Android runtime；它直接消费 production
`mon_cast_message_keys::build_key_recipe()`，枚举所有有数据的 runtime
`monster_type`、所有 `is_valid_spell()` 法术、去重后的 canonical English
type/species/genus tuple，以及一组有限 scenario cover。scenario cover 的 Catch2
proof 会穷举 32 种 category mask 与所有 humanoid/intelligence/finale/targeted/
visible-beam 布尔组合，要求每个生成 expression 都属于 cover union。

artifact schema-v1 标记 `completeness=closed_world_upper_bound`。base expression
保留 `${beam_short_name}` 符号，不调用 locale-dependent `get_short_name()`；normal、
unseen、silent-prefixed 与 silent-unprefixed fallback lookup 则通过 production
`search_message_candidate()` recorder 生成，再按 production DB fetch 规则 lowercase
后聚合。大小写碰撞会合并 attempt 集合。base 与 lookup expression 都按字节排序并
去重；lookup record 显式列出其 attempt 集合，counts 同时区分唯一 expression 与
attempt 数量。canonical monster/spell fragment 若包含保留标记
`${beam_short_name}`，生成器会 fail closed 为 invalid，避免与符号 token 混淆。
artifact 只写入调用方指定的临时路径，不加入 Git。

生成命令：

```sh
make -C crawl-ref/source textdb-monspell-candidate-dump \
  TEXTDB_MONSPELL_CANDIDATE_DUMP=/tmp/monspell-candidate-upper-bound.json
```

target 会以原子 replace 连续写入两次，并由 hidden Catch2 test 检查最终字节与内存中
的 deterministic serialization 完全相同。该 dump 已由下节的 Python 审计器与
EN/ZH effective SpeakDB 做 containment join；它证明的是所有运行时 candidate 的
closed-world 上界，不声称精确复现某一局游戏实际走过的候选集合。

### 7.3 behavior sound closed-world upper-bound 审计

`.claude/scripts/audit_monspell_behavior.py` 消费 production C++ candidate artifact、
两份 production C++ SpeakDB artifact、Phase 0 inventory 与 production overlay
manifest；它不重新解析 TextDB 源文件。审计器严格验证 candidate schema、domain、
完整性声明、计数、production 六条有序 scenario cover、排序、attempt 集合和
`${beam_short_name}` 符号契约。它将 lowercase 后去重的 base expression 作为三个
有序流，分别生成 normal/fallback、silent-prefixed 与 unseen lookup，再做三路
merge/coalesce，逐条验证 artifact lookup expression 及碰撞后的 attempt union；
不会物化第二份百万级 lookup 集合。base/lookup 同时限定为 canonical English
ASCII，使 Python `lower()` 与当前 production key canonicalization 的证明边界一致；
遇到非 ASCII candidate 时必须升级契约而不是静默沿用。

tracked anchor
`.claude/data/message-overlay/monspell-candidate-anchor.json` 另行固定审阅过的
production artifact SHA-256、counts 与 producer contract。审计器先验证 anchor
并比较 candidate 字节 hash，再解析候选内容；因此即使同时删除一个 base、其三个
lookup 和相应 counts，使剩余闭包内部自洽，也会 fail closed。通过验证后才流式扫描
lookup expression，与 EN/ZH effective nonempty SpeakDB key 求交。EN/ZH effective
merge 遵循本地化空条目回退 canonical English 的运行时规则。

行为分析的 root universe 是 EN/ZH candidate hit 的并集，而不是 inventory 全集。
candidate 命中来自其他 SpeakDB 内容域、仅单语言存在的 key、inventory 中不可达的
root 和符号 expression 的实际匹配均单独报告；单语言存在差异会显式阻断 EN/ZH
parity。随后在 selectable variant/递归 marker 图上传播固定行为谓词：

- `PRE_BINDING/GESTURE` 对应 target resolution 前的旧正文 heuristic；
- `PRE_BINDING/VISUAL_APPLICABILITY` 对应 unseen candidate rejection；
- `POST_MATERIALIZATION/VISUAL_CHANNEL` 与 `SOUND_LIKE_CHANNEL` 对应
  `[a|b]` 物化后的逐行 control prefix；后者不等同于怪物施法的默认 noise，报告
  不把 audible 建模成正文布尔量；
- Lua、递归循环、损坏节点和无法静态确定的频道前缀均 fail closed 为
  `UNANALYSABLE`。

root 与递归子键都复用 Phase 0 `_reachable_variants` 的 production 累计权重边界，
不把 weight 为正简单等同于可达；总权重不为正、不平衡 `@`、递归深度超过 10、
累计 replacement 超过 100，以及随机 option 生成新 bracket 站点时同样 fail closed。
缺失的递归子键仍计一次 leaf call depth，因为 production 会先进入递归查询再发现
missing；该失败查询不额外增加 replacement，配对 marker 本身只计一次。
频道审计中，只要冒号前仍含 `@...@`、`[...]` 或 `{{...}}` 动态片段，即使与
字面后缀拼接或跨递归边界形成，也不得推断为普通频道。

生成的 schema-v1 报告位于
`.claude/data/message-overlay/monspell-behavior-report.json`，支持确定性
`--output` 与逐字节 `--check`。当前 production artifact SHA-256 为：

- candidate：`9eb63d334f31c1dfb608c7c742f2ce4046a711f7450d6de0ac516033baf3c083`；
- EN：`0e539d83c66ace3522e97fe8f7d67fd06766c4953b273f1bab0e31a35f18c1b4`；
- ZH：`da4724309f5341873b1a04fe9a713f42552d6f2d32f4657804e9e84781d996d0`。

当前 candidate upper-bound 在 EN/ZH effective SpeakDB 各命中 251 个 root；命中
并集也是 251 个。Phase 0 inventory 的 262 个 root 中有 11 个不在生产 candidate
上界内，因此行为分析只覆盖 251 个 runtime root。当前静态行为结果为：

| 指标 | EN | ZH |
|---|---:|---:|
| effective runtime behavior root union | 18 | 18 |
| effective runtime gesture root | 15 | 15 |
| visual applicability root | 5 | 5 |
| visual channel root | 5 | 5 |
| sound-like channel root | 0 | 0 |
| unanalyzable root | 0 | 0 |

effective runtime 共证明 72 个正 behavior occurrence，没有 fail-closed
occurrence。这里的覆盖计数拆分为三个不同单位，不能相加后混称“occurrence”：

- 0 个仍走 legacy 正文 heuristic 的 behavior occurrence，其中 0 个已有等价
  metadata；
- 158 个 canonical structured variant，158 个均有完整 behavior metadata；
- 上述 structured variant 的 EN/ZH 模板与 behavior shape 共 316 个逐语言验证
  单位，316 个均完整；3 个 `LEGACY_ONLY` variant 不进入这两个计数。

`ensnare arachne cast` 的 2 个 variant 与
`guardian serpent cast targeted` 的 3 个 variant 已完整迁移。其 gesture requirement
分别为 `[true, false]` 与 `[false, true, false]`，在 canonical variant 选定后、
目标解析前传入唯一一次 binding callback。实际运行路径的 EN/ZH behavior mismatch
因此降为 0；报告仍保留 `raw_legacy_evidence`，用于展示旧中英文正文曾产生的差异，
但该证据不再代表 structured 路径的运行行为。
`vanquished vanguard nergalle cast` 已通过窄 `CAPTURE_SLOT` 完整迁移。频道和
gesture 行为由 descriptor 显式给出；三个动态兽人名字来自 canonical English
trace 的受控递归捕获，不再由静态正文猜测。

这份报告明确标记
`analysis_completeness=SOUND_CLOSED_WORLD_UPPER_BOUND`、
`candidate_key_containment_proven=true`、`runtime_reachability_proven=true` 和
`reachability_kind=SOUND_UPPER_BOUND_NOT_EXACT`。这表示 normal、unseen、
silent-prefixed 与 silent-unprefixed fallback 的 production candidate lookup
闭包已经包含在分析域中，但不表示每个 root 在某个具体运行时状态都一定可达。

`phase2_ready` 为 true。EN/ZH effective runtime behavior parity、候选
containment、runtime reachability、八批既有迁移、21-key pilot 与 Wave B
30-key actor-only 批次均已证明，且
unanalyzable occurrence 与 fail-closed root 均为 0。正常 `monspell` 路径的
gesture 正文嗅探已在独立批次删除；审计持续作为回归门禁。只有 overlay
故障/未加载或语言不受支持，且 key 属于 compiled `CANDIDATE` catalog 时，
compatibility legacy 才执行旧嗅探。generic `mon-speak` parser 仍保留。
生产回归测试通过默认空的 `mons_cast_noise_diagnostics` 注入 target observer 与
通用 `mon_speech_emission_observer`；默认 options 仍调用原 sink。通用 observer
位于 `mons_speaks_msg()` 原本调用 `mprf()` 的最终边界：可见性、`mon_acting`、
legacy replacement、分行、mute、prefix/channel 与 friendly 转换始终先执行，
observer 仅替代最终打印且不能改变 `noticed`。structured 目标解析不使用外部
legacy observer。

production dump 与审计必须串行运行，避免多个 `make` 同时重建或写入同一 Catch2
可执行文件。以下命令可从 worktree 根目录直接复制；三个 artifact 是 `/tmp` 临时
文件，不加入 Git：

```sh
make -C crawl-ref/source textdb-monspell-candidate-dump \
  TEXTDB_MONSPELL_CANDIDATE_DUMP=/tmp/monspell-candidate-upper-bound.json

make -C crawl-ref/source textdb-phase0-dump \
  TEXTDB_PHASE0_DUMP=/tmp/textdb-phase1-behavior-en.json

make -C crawl-ref/source textdb-phase0-dump \
  TEXTDB_PHASE0_LANGUAGE=zh \
  TEXTDB_PHASE0_DUMP=/tmp/textdb-phase1-behavior-zh.json

python3 .claude/scripts/audit_monspell_behavior.py \
  --candidate-anchor \
    .claude/data/message-overlay/monspell-candidate-anchor.json \
  --candidate-artifact /tmp/monspell-candidate-upper-bound.json \
  --english-artifact /tmp/textdb-phase1-behavior-en.json \
  --localized-artifact /tmp/textdb-phase1-behavior-zh.json \
  --inventory .claude/data/message-overlay/monspell-phase0-inventory.json \
  --manifest .claude/data/message-overlay/monspell.json \
  --output .claude/data/message-overlay/monspell-behavior-report.json

python3 .claude/scripts/audit_monspell_behavior.py \
  --candidate-anchor \
    .claude/data/message-overlay/monspell-candidate-anchor.json \
  --candidate-artifact /tmp/monspell-candidate-upper-bound.json \
  --english-artifact /tmp/textdb-phase1-behavior-en.json \
  --localized-artifact /tmp/textdb-phase1-behavior-zh.json \
  --inventory .claude/data/message-overlay/monspell-phase0-inventory.json \
  --manifest .claude/data/message-overlay/monspell.json \
  --output .claude/data/message-overlay/monspell-behavior-report.json \
  --check
```

年度升级时不得根据新 dump 自动改写 anchor。应先保留旧 anchor，审计 candidate
artifact 的 scenario、counts、base/lookup 差异和上游 recipe 变化；只有人工确认
producer contract 仍成立或已按语义变化升级后，才显式更新 anchor SHA/counts，
重新生成 behavior report，并重复 `--check`。未知或漂移的 candidate artifact
必须保持 fail closed，不能自动继承上一版本的可达性证明。

术语表 SHA-256：
`c221e1f1a39b085869ba918da061efaf7c2c32b431c9169d5512be0cecc22c4c`
