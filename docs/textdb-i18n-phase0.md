# TextDB 消息国际化 Phase 0 实施记录

> **历史阶段快照，基线为上游 0.34.1。** Phase 0 当时已完成并通过架构验收；
> 此后 Phase 1 基础设施和 Phase 2 数据迁移也已完成。当前总状态见
> [`textdb-i18n-architecture.md`](textdb-i18n-architecture.md)，后续实现记录见
> [`textdb-i18n-phase1.md`](textdb-i18n-phase1.md)。

本文记录 [`textdb-i18n-architecture.md`](textdb-i18n-architecture.md) 的
Phase 0 原型、数据契约和验证证据。在这个历史边界上，TextDB structured 选择、
catalog 与模板尚未接入游戏路径，游戏仍完全使用 legacy TextDB。进入当时施法调用链的改动只有
目标与 beam 的 typed compatibility seams；其 adapters 仍产出原有 prep/target/beam
字符串。

## 已完成的边界

### 1. production parser canonical artifact

`database.cc` 的 DBM 写入与 Phase 0 dump 共用同一个 TextDB entry consumer；
legacy 加权选择与 dump 共用同一个 weighted parser/chooser。Python 不再实现第二套
TextDB 或 `w:N` parser。

typed dump 保存：

- schema、数据库名、源目录和规范化后的完整源快照；
- key 的全部定义历史与最终 provenance；
- raw body、空正文状态和 weighted parse error；
- canonical key + variant ordinal locator、权重和 raw pattern。

源规范化只移除 UTF-8 BOM、把 CRLF/CR 转为 LF；非法 UTF-8 和 NUL 会被拒绝，
合法字面 U+FFFD 不会被改写。测试 serializer 固定字段顺序，写临时文件后用项目
文件系统 wrapper 原子替换，文件末尾恰好一个 LF。

导出 canonical English：

```sh
make -C crawl-ref/source textdb-phase0-dump \
  TEXTDB_PHASE0_DUMP=/tmp/textdb-phase0-canonical.json
```

当前真实 artifact：

- 10 个 source；
- 1,437 个 effective key；
- 2,910,553 bytes；
- SHA-256
  `0e539d83c66ace3522e97fe8f7d67fd06766c4953b273f1bab0e31a35f18c1b4`。

### 2. monspell inventory 与年度差异契约

`.claude/scripts/audit_monspell_phase0.py` 现在要求 `--dump`，只消费上述 production
artifact。它继续负责静态 token、Lua、控制前缀、`[a|b]`、递归闭包、cycle、
summary 和 fingerprint 分析，但不再发现或解析 raw TextDB。

```sh
python3 .claude/scripts/audit_monspell_phase0.py \
  --dump /tmp/textdb-phase0-canonical.json \
  --check .claude/data/message-overlay/monspell-phase0-inventory.json \
  --materialization-policy \
    .claude/data/message-overlay/monspell-phase0-materialization-policy.json
```

真实 artifact 对既有 inventory 的 byte-for-byte check 通过，source/semantic
fingerprint 均无 drift，不需要重写基线。当前 inventory 为：

| 项目 | 数量 |
|---|---:|
| `monspell` key | 262 |
| 加权变体 | 355 |
| 完整递归闭包 key | 266 |
| 递归引用站点 | 18 |
| `monspell` 内递归 token | 15 |
| 运行时 token | 590 |
| `[a|b]` 站点 | 12 |
| Lua 站点 | 0 |
| 闭包循环 | 0 |

`.claude/scripts/compare_monspell_phase0.py` 接受两个 inventory，确定性报告 key、
variant、权重、token、递归图、随机站点、控制前缀、Lua、provenance 和闭包漂移。
任何漂移都要求人工复审；工具不自动继承 stable ID。

独立的 Phase 0 物化策略账本绑定 inventory semantic fingerprint，并要求每个已选
variant 内部的显示动态性都得到明确处置：`[a|b]`、Lua，或可达的多结果递归子树。
当前账本精确覆盖 14 个动态 variant：13 个有限项为 `CASE_MAP_PROTOTYPE`，Nergalle
为 `LEGACY_ONLY`。新增、删除、选项数变化、递归目标变化、遗漏/重复 locator、空
evidence 或 Lua 未保持 `LEGACY_ONLY` 都会使 audit 失败。该账本只证明 Phase 0
覆盖，不是 Phase 1 catalog 或 stable-ID manifest。

### 3. canonical 选择、递归与 Lua trace

Phase 0 API 将一次查询拆为“选择顶层 raw variant”和“只展开已选 variant”。
两阶段共用 legacy chooser、递归 replacement 和嵌入 Lua 执行核心，trace 记录：

- 每次 weighted choice 的 requested/resolved key、variant、weight、bound、结果；
- 顶层和递归 site path、深度、replacement count 与限制状态；
- Lua 的顺序、源码、结果/错误与前后 RNG；
- 每个阶段的 RNG state、当前 generator count 和 global counts。

真实 `unseen laughing skull cast` 与递归的 `basilisk cast` 各比较 4,096 seeds，
canonical 新路径与 loaded canonical English legacy 路径的正文、RNG state 和 count
完全一致。fixture 另覆盖默认/显式权重、bound 0/1、重复和嵌套 marker、递归
10/11 层、replacement 100/101 次、missing/unbalanced、Lua 正常/错误/未闭合。

当前 canonical `monspell` 闭包没有 Lua。测试环境中的嵌入 Lua 未暴露
`crawl.random2`，因此不能把任意 Lua 外部副作用宣称为已证明；未来出现此类变体时，
在建立专用契约前必须保持 `LEGACY_ONLY`。

### 4. 五态候选搜索原型

纯 Phase 0 状态机已经覆盖：

```text
MISSING / SUPPRESS / INAPPLICABLE / RENDERED / CORRUPT
```

并区分 normal/unseen、silent prefixed、silent unprefixed fallback 三种 attempt。
它固定了现有 `_speech_message()` 的细节：silent 前缀缺失或不适用时重试无前缀；
无前缀 fallback 的任意非空正文直接接受而不再次做 applicability 检查；`__NONE`
始终停止并保持沉默；`CORRUPT` 停止且不得重抽。

顶层选择在 expansion 前得到的 `MISSING/CORRUPT` 不执行递归或 Lua。若
`CORRUPT` 在 expansion 中途产生（递归深度/替换次数超限、未闭合 `@`、子项
损坏、Lua 错误或未闭合 Lua），则继续完成 legacy 本次应有的 Lua/output/RNG
trace，随后停止，不进入目标解析或 `[a|b]`。`INAPPLICABLE` 同样已完成
canonical expansion 和 Lua，但不进入目标解析或 `[a|b]`。该状态机尚未接入
`mon-cast.cc`。

### 5. legacy `[a|b]` 物化与 CASE_MAP 证明

`maybe_pick_random_substring()` 保留原入口，并增加可选 observer。observer 在现有
`random2()` 之后记录实际 materialized site ordinal、option count 和 option
index，不复制扫描或随机逻辑。无 observer 的 legacy trace 路径不会构造 trace
字符串或递归 path。

typed materializer 只接受已经绑定施法 runtime token 的 canonical English
pattern；仍含 `@at@`、`@target@` 或 `@beam@` 时返回 `CORRUPT` 且 RNG 不动。
site identity 包含顶层 locator、已选递归 locator/path 和展开后从左到右的 ordinal。

真实 `orb of entropy cast` 在 4,096 seeds 上完成：

- loaded canonical English legacy 与 typed 新路径的英文逐字节相等；
- 最终 RNG state/count 相等；
- 英文两个 CASE_MAP case 均逐字节等于实际 legacy 结果；
- 中文使用同一个 option index 选择本地化 case，不重新随机；
- CASE_MAP 查询和渲染前后 RNG 不变，动态分支没有执行后丢弃。

这证明了一个真实、有限的跨语言 CASE_MAP 原型，不表示 262 个 key 都可迁移。

全量有限动态英文 golden 又对 9 个真实 key 各运行 8,192 seeds，逐 seed 比较 loaded
canonical legacy 与 typed 路径的最终正文和 RNG state/count，并要求观察到的输出集合
与人工列举集合完全相等：

| key | 覆盖点 | 完整输出数 |
|---|---|---:|
| `roxanne cast` | 递归到 `sphinx cast`，两种顶层正文 | 2 |
| `vex sphinx marauder cast` | 三分支、分支内前导空格和冠词拼接 | 3 |
| `confuse sphinx marauder cast` | 二分支、冠词拼接 | 2 |
| `paralysis guardian sphinx cast` | 单站点二分支 | 2 |
| `burial acolyte cast` | 单站点二分支 | 2 |
| `march of sorrows boris cast` | 加权顶层选择 + 两套二分支 | 4 |
| `weeping skull cast` | 两个顶层 variant 各自带独立二分支 | 4 |
| `silent weeping skull cast` | 单站点二分支 | 2 |
| `orb of winter cast` | 三个顶层 variant，其中一个含三分支 | 5 |

这 26 个完整输出与 orb/bone-dragon 的各 2 个 CASE_MAP 输出合计 30 个，覆盖当前
inventory 的 12/12 个 `[a|b]` 站点，以及唯一有限的多结果递归根 Roxanne。它们
证明递归正文、顶层权重和正文随机的实际选择结果会进入最终英文物化，不会只为消耗
RNG 而执行后丢弃。
`Vanquished Vanguard Nergalle cast` 的单个 variant 含三个独立 `@orc name@`，其
组合空间超过一百万；在建立可声明的递归捕获槽协议前明确保持 `LEGACY_ONLY`，不以
巨大 CASE_MAP 冒充结构化覆盖。

### 6. `${slot}` 与 SpeakDB 保留字审计

`.claude/scripts/audit_textdb_slots_phase0.py` 读取 production artifact 和独立
schema，阻塞：

- 非 `[a-z][a-z0-9_]*`、重复或未声明的 slot；
- 把 slot 写成 `@actor@` 等 TextDB 递归语法；
- 未逐模板声明、声明未使用或 SpeakDB 不存在的 `@key@`；
- reserved namespace、overlay key、slot 与完整 SpeakDB key 集的冲突。

Phase 0 production schema 只声明 `actor`、`beam`、`target`，overlay keys 和
templates 均为空，不构成 Phase 1 catalog。真实 1,437-key artifact 审计结果为
3 slots、0 violations。

```sh
python3 .claude/scripts/audit_textdb_slots_phase0.py \
  --dump /tmp/textdb-phase0-canonical.json \
  --schema .claude/data/message-overlay/monspell-phase0-slot-schema.json
```

### 7. EN/本地化静态拓扑比较

`.claude/scripts/compare_textdb_locale_phase0.py` 接受两个 production artifact，
按“本地化非空 entry 覆盖，否则回退 English”的查询语义比较 canonical
`monspell` roots。报告 variant/weights/bounds、递归闭包和引用顺序、Lua 源码
fingerprint 顺序、`[a|b]` option-count 顺序，以及 localized-only/override/
fallback/missing。

报告固定标记 `dynamic_trace_proven: false`。它用于量化现状和定位需要动态测试的
root，不能替代同 seed RNG/Lua/目标 trace。

本地化导出使用与 `TextDB` child 相同的目录发现规则：`database/<lang>/` 下文件名
以 `txt` 结尾的文件按项目默认字符串顺序装载，若存在 `source.txt` 则强制第一。
这会忠实保留当前“语言目录内所有 txt 都进入 translation SpeakDB”的既有行为，
而不是只读取父 SpeakDB 的十个文件。

```sh
make -C crawl-ref/source textdb-phase0-dump \
  TEXTDB_PHASE0_LANGUAGE=zh \
  TEXTDB_PHASE0_DUMP=/tmp/textdb-phase0-zh.json

python3 .claude/scripts/compare_textdb_locale_phase0.py \
  --canonical-dump /tmp/textdb-phase0-canonical.json \
  --localized-dump /tmp/textdb-phase0-zh.json \
  --output /tmp/textdb-phase0-en-zh-report.json
```

真实 zh artifact 连续导出逐字节一致：22 sources、1,962 effective keys、262 个
`monspell` history/effective keys、357 variants；SHA-256
`da4724309f5341873b1a04fe9a713f42552d6f2d32f4657804e9e84781d996d0`。

静态比较记录 1,382 overridden、55 fallback、580 localized-only、0 missing，
并找到 9 个 selection-topology changed roots：

- `guardian serpent cast`；
- `guardian serpent cast targeted`；
- `unseen acid splash cast`；
- `unseen chilling breath cast`；
- `unseen cold breath cast`；
- `unseen fire breath cast`；
- `unseen searing breath cast`；
- `unseen spit acid cast`；
- `unseen spit poison cast`。

前两项改变顶层 variant 数量/权重 bound；其余项把 English 的递归 helper 正文
改成中文直接正文，因此现有 legacy EN/ZH 的递归随机调用图确实不同。

动态测试按真实 translation merge 语义，对 262 个 roots × 4,096 seeds 比较
weighted choice、成功递归 semantic path、Lua、bounds/results 和 RNG observations。
比较会排除查库为 MISSING 的 runtime slot 及其正文位置派生 replacement count，避免
把中英文占位符数量/语序差异误报成数据库随机图变化。动态差异集合精确等于上述
9 roots：guardian 两项是顶层选择差异；7 个 unseen root 同时出现递归选择和最终
RNG state/count 差异。两侧实际遇到的 weighted key 均覆盖全部 variants。

作为对照，9 个差异 root 加 `orb of entropy cast` 在 canonical-driven 模拟
EN/ZH 路径上以相同 canonical entries 运行 128 seeds，数据库 trace 与 RNG 完全
相同；纯 CASE_MAP 测试另证明最终语言模板不重新随机。该动态测试仍只覆盖数据库
选择/递归/Lua，不包含目标解析与后续 `[a|b]`。

### 8. target-resolution typed seam

原 `_speech_fill_target()` 主体已抽为拥有型 `resolved_speech_target`，记录
AT/NEXT_TO/PAST、PLAYER/SELF/MONSTER/FEATURE/THIN_AIR/INDEFINITE/ERROR、
解析来源、owned display、位置、mid、feature 和错误信息；不保存 `actor*` 或
`T_()` borrowed pointer。兼容 adapter 仍把 owned preposition/display 写回旧的
两个字符串参数，未引入 catalog 或新模板。

`fire_tracer()` 仍无条件位于所有直接目标判断之前。可选 POD observer 用函数指针
和 `void*` 记录整个 tracer phase，以及两处 reservoir `one_chance_in()` 的 bound、
selected 和前后 RNG state/count；事件只在原调用之后发出，不重抽。null 或
default-disabled observer 不读取 RNG。

Catch2 使用受控小地图和真实 `fire_tracer()` 覆盖 player、self、adjacent-player、
feature、thin-air、indefinite，并比较 null/active/default-disabled observer 的
typed 结果与最终 RNG。PAST fixture 额外初始化真实 feature/monster/spell 启动表，
通过 production monster-slot allocator 注册施法者和两个可见候选，让 tracer 到达
目标格并执行两步 reservoir。测试逐事件验证 bound `1/2`、selected、最终候选、
observer 与无 observer 的结果/RNG 等价，并在 RAII teardown 后核对玩家位置、视觉
状态、monster grid、mid cache、monster index 与父 RNG 全部恢复。

同一 compatibility 层新增拥有型 `resolved_beam`：快照 configured name、short
name、origin spell、flavour/real flavour、pierce、远程攻击对象是否存在，以及
已经按旧逻辑求出的 display text；不保存 `ranged_attack*` 或翻译借用指针。
resolver 严格保持 `!targeted`、空 name、`get_short_name()` 的原分支顺序，旧
`mons_cast_noise()` 仅通过 adapter 取得相同字符串。Catch2 覆盖 resolved、
non-targeted、invalid 三类，并证明各分支不改变 RNG。

### 9. canonical 驱动的完整消息物化原型

`materialize_structured_message()` 只服务 Phase 0 测试，不接入 runtime/catalog。
它按固定边界执行一次 canonical 顶层选择与递归/Lua expansion，调用一次 runtime
binding callback，以 canonical English 值绑定 actor/target/beam，最后恰好执行一次
既有 `[a|b]` 物化；返回数据库、binding、substring 和总 RNG 边界。它处理一个已知
适用 key，不取代第 4 节的五态候选搜索状态机。

真实 `march of sorrows bone dragon cast` 在 1,024 seeds 上与现有分阶段 legacy
调用链比较：数据库 trace、实际 target resolver 的 `FIRE_TRACER` 事件、目标结果、
substring site ordinal/bound/index、英文逐字节输出以及最终 RNG state/count 全部
一致。中文只按 canonical option index 从两个最终模板中纯查询，既不读取 zh
TextDB，也不执行递归、Lua、`[a|b]` 或任何 RNG。这闭合了 canonical English 共享
轨迹到本地化最终模板的最小端到端证明。

## Phase 0 验证证据

- C++14 Catch2 完整链接：通过；
- `[textdb][phase0]`：18 cases / 736,197 assertions，通过；
- production artifact 连续导出：逐字节确定；
- production materialization policy 对真实 artifact：精确闭包检查通过；
- Python Phase 0 tests：41 项通过，其中 audit inventory/policy tests 为 14 项；
- annual inventory compare tests：8 项通过；
- slot audit tests：10 项通过；
- locale topology compare tests：9 项通过；
- target/beam typed seams：5 cases（640 assertions），通过；
- variadic string 与 i18n borrowed-pointer 扫描：通过；
- `verify_zh.sh --profile code`：0 failures，通过；
- `verify_zh.sh --profile review`：0 failures，通过；
- `git diff --check`：通过。

本轮最终验证日志为：

- code：`20260716T022057473489931+0800-2-fdac3c119e06`；
- review：`20260716T022228695975657+0800-2-fdac3c119e06`。

未过滤的 Catch2 全套仍有两个与本方案无关的既有 `zh-help` 动态状态用例失败；本轮
新增对象均完成链接，且两个受影响标签均独立通过，因此不把未过滤全套记录表述为
“全部测试通过”。

review profile 初次运行暴露 fast/catch2 聚合器无 bot 日志时仍强制完整 bot manifest
的既有门禁错误；修复后同一历史日志由退出 1 变为退出 0，且未修改 baseline。随后
完整 review profile 重跑成功，不能沿用此前失败日志作为通过证据。

## Phase 0 完成审计

| 架构要求 | 权威证据 | 结论 |
|---|---|---|
| 结构化 inventory 与 parser 同构 | production C++ artifact；inventory byte check | 完成 |
| 英文消息与随机行为基线 | 18 个 `[textdb][phase0]` 用例；固定 seed golden | 完成 |
| 年度差异输入输出契约 | inventory/locale/slot compare scripts 及 41 项 Python 测试 | 完成 |
| 全部递归、Lua、`[a\|b]` 清点 | 266-key 闭包、18 条边、12 个随机站点、0 Lua | 完成 |
| 动态正文不得执行后丢弃 | 30 个完整输出；12/12 随机站点；Roxanne 递归 golden | 完成 |
| 不可穷举项显式 legacy | fingerprint-bound policy 将 Nergalle 标为 `LEGACY_ONLY` | 完成 |
| canonical EN/新 EN/新 ZH 完整轨迹 | bone dragon 端到端 trace；262 roots locale trace 量化 | 完成 |
| 五态搜索、目标和 beam typed seam | 状态机测试；PAST reservoir；5 个 target/beam 用例 | 完成 |
| `${slot}` 与全 SpeakDB 冲突审计 | 1,437 keys、3 slots、0 violations | 完成 |
| 正式工程验证 | code/review profiles 均为 `status=pass`、0 failures | 完成 |

最终架构验收结论：Blocker 0 / Needs Fix 0，Phase 0 **Go**。该结论只解除进入
Phase 1 的阶段门禁，不把任何 Phase 0 prototype API 视为已接入游戏 runtime。

未来年度 inventory 若首次出现 Lua，对应 root 必须保持 `LEGACY_ONLY`，直到建立并
通过副作用轨迹契约；这是持续迁移约束，不是当前 0-Lua inventory 的未完成实现项。

## 年度升级建议流程

```text
更新上游大版本
→ C++ production parser 导出 canonical/localized artifact
→ inventory byte check + materialization policy 闭包；有 drift 时生成年度差异报告
→ slot/namespace 全库冲突审计
→ EN/本地化静态拓扑比较
→ 同 seed 动态 trace 与英文 golden
→ 人工决定 stable ID 继承、替换或 tombstone
```

artifact 是临时审计输入；仓库只保存紧凑 inventory、schema 和人工复审结果，避免
每年维护重复的大型 raw source 副本。

## 术语上下文

本切片使用的 `docs/glossary.md` SHA-256：
`c221e1f1a39b085869ba918da061efaf7c2c32b431c9169d5512be0cecc22c4c`。
