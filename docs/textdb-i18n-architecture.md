# TextDB 中文消息渲染架构与年度升级策略

> 状态：架构规格已定；Phase 0/1 已完成；Phase 2 已完成八批低风险迁移、
> 一次 21-key 分片并行试点，以及 Wave B、C、D、E 的并行迁移
> 适用项目：DCSS 中文长期下游分支
> 上游策略：不计划合入 Crawl 主仓库，约每年跟进一次上游大版本
> 评审状态：**Phase 1 Go（完整 candidate 上界）**；Phase 2 当前 structured
> 覆盖 189 个 canonical key、256 个 canonical variant；catalog 另跟踪 9 个
> `LEGACY_ONLY` key、10 个 variant；正常 `monspell` 路径的 gesture
> 正文嗅探已删除，safe compatibility fallback 保留

## 1. 背景

DCSS 的 TextDB 同时承担多种职责：完整句子存储、加权随机选择、
`@key@` 递归展开、运行时实体占位、嵌入 Lua，以及不同语言数据库之间的
回退。当前怪物施法文本暴露出一个结构性问题：英文把目标关系拆成
`@at@` 和 `@target@` 后再拼接，而中文需要根据动作和关系重排整句。

典型关系包括：

- `AT`：向目标射出火焰；
- `NEXT_TO`：朝目标旁边射出火焰；
- `PAST`：火焰从目标旁边掠过。

这三种关系无法共享同一个前置或后置词片段。原实现还会在
`mon-cast.cc` 中搜索已本地化正文里的 `gesture`、`手势`、`指向`，
再据此影响目标推断，使翻译措辞反向参与游戏行为；该嗅探现已由
structured descriptor 与审计门禁取代。

本项目是长期下游分支，不受“补丁必须易于上游接受”的限制；但每年仍需
吸收一次上游大版本，因此架构必须把永久分叉集中在少数稳定边界，并能
机械检测上游数据的语义漂移。

## 2. 设计结论

采用以下总体模型：

> **窄类型化适配器 + 宽 legacy TextDB + 离线漂移审计。**

具体含义是：

1. 只有文本结构依赖运行时语义、或本地化正文参与逻辑判断的领域，才进入
   类型化事件渲染器；第一阶段仅处理 `monspell`。
2. 其他 TextDB 继续负责完整句、随机风味文本、递归词库和名称生成。
3. 通用运行时实体槽逐步类型化，但不要求所有正文转换为稳定消息 ID。
4. 上游英文 TextDB 和通用解析器尽量保持原样。
5. 本地 manifest、生成器和审计器负责管理稳定 ID、元数据、生成文件与
   年度升级。

## 3. 现有 TextDB 机制与边界

`crawl-ref/source/database.cc` 中的 TextDB 目前执行：

- 权重随机选择；
- 翻译库优先、缺失时回退英文；
- `@foo@` 同库递归展开；
- 嵌入 Lua 执行；
- 多个内容域共享数据库生命周期和缓存。

它不执行 `[a|b]`。该语法稍后由 `do_mon_str_replacements()` 调用
`maybe_pick_random_substring()` 逐站点消耗 `random2()`；因此它属于消息的
legacy 随机物化阶段，不能被归入 TextDB expansion 或从 structured 路径省略。

其中 SpeakDB 同时装载：

- `monspeak.txt`；
- `monspell.txt`；
- `monflee.txt`；
- `wpnnoise.txt`；
- `insult.txt`；
- `godspeak.txt`；
- `monname.txt`；
- `colourname.txt`；
- `graffiti.txt`；
- `miscast.txt`。

因此，不应在通用 `@foo@` 解析器中直接加入 ICU/MessageFormat、消息 AST
或领域元数据语法。一次通用解析器变更会同时影响台词、名字、神器噪声、
神祇消息、涂鸦和施法文本。

## 4. TextDB 领域分类

### 4.1 完整适用类型化事件：`monspell`

`monspell` 同时具备三个迁移条件：

- `_speech_fill_target()` 计算 `AT / NEXT_TO / PAST`；
- 动作配价决定中文整句结构；
- 代码从本地化正文推断 `gestured` 行为。

它应采用完整的类型化上下文、显式变体元数据和本地化整句模板。

### 4.2 仅适用元数据或类型化实体槽

| 数据库 | 风险 | 建议 |
|---|---|---|
| `monspeak` | `@to_foe@`、`@at_foe@`、有效性判断和大量角色槽；正文规模极大 | 正文继续使用 TextDB；将 `requires_foe`、`visual_only` 等约束元数据化，逐步类型化实体槽 |
| `miscast` | 怪物、身体部位、颜色和英语屈折 | 保留现有语义键；局部移除英语屈折，使用类型化身体部位参数 |
| `shout` | 怪物、代词、说话方式 | 保留 TextDB；有实际语序问题时迁移对应句型 |
| `godspeak` | 物品、地形、身体部位和颜色组合 | 保留完整句模板；局部使用类型化参数 |
| `wpnnoise` | 武器、玩家、神祇和大量递归风味文本 | 保留 TextDB；只类型化真正的运行时实体槽 |
| `monflee` | 少量怪物主体槽 | 保持现状 |

### 4.3 不适用事件渲染器

以下数据库本质上是语言专用生成语法：

- `randname`；
- `randbook`；
- `rand_all`、`rand_arm`、`rand_wpn`；
- `graffiti`；
- `insult`；
- `colourname`、`miscname`、`monname`。

它们依赖随机词根、短语递归、修饰语顺序和语言风格。正确方案是让中文拥有
独立的组合规则或加权完整句，而不是把它们转换成施法事件。

长篇描述、帮助、FAQ 和 Lua 描述模板也继续使用现有机制。

## 5. 两层本地化架构

### 5.1 第一层：通用类型化槽

类型化槽必须使用 TextDB 不识别的独立语法 `${name}`，不得复用 `@foo@`。
后者属于 SpeakDB 的递归键语法；即使某个名称当前不存在，未来其他内容域
加入同名 key 后，也可能在 adapter 运行前被随机正文替换。

槽名只允许 ASCII 小写字母、数字和下划线，并且必须在 manifest 的
`slot_schema` 中声明。生成器对合并后的完整 SpeakDB 执行保留字审计：

- overlay 模板中的 `${name}` 必须已声明；
- 类型化槽不得写成 `@actor@`、`@target@` 等递归键形式；
- overlay 中每个 `@foo@` 必须明确声明为 TextDB 递归引用，或归入 legacy；
- overlay 保留 key 命名空间、槽名与所有 SpeakDB key 的冲突均阻塞生成。

TextDB 选定原始变体后，再由类型化上下文解析 `${name}`：

```cpp
struct thin_air_tag {};
struct indefinite_tag {};
struct unresolved_target_tag {};

enum class target_relation
{
    NONE,
    AT,
    NEXT_TO,
    PAST,
};

using target_value = variant<actor_ref, feature_ref, location_ref,
                             thin_air_tag, indefinite_tag,
                             unresolved_target_tag>;

struct resolved_target
{
    target_relation relation;
    target_value value;
};

struct message_context
{
    optional<actor_ref> actor;
    optional<resolved_target> target;
    optional<item_ref> item;
    optional<feature_ref> feature;
    optional<god_type> god;
};
```

该层负责实体名称、代词、所有格、身体部位、物品、地形和神祇名称；它不
决定动作，也不把英语介词或词形变化套在已经本地化的文本上。

现有 `do_mon_str_replacements()` 可作为 legacy adapter，逐步把内部替换
迁移到类型化实现。未迁移调用方继续使用当前行为。

### 5.2 第二层：领域语义渲染器

只有调用方本来就掌握结构化事件时，才建立领域上下文。怪物施法建议使用：

```cpp
enum class cast_frame
{
    PROJECTILE,
    GAZE,
    GESTURE,
    VOCAL,
    INVOCATION,
    DIRECT_EFFECT,
};

struct resolved_beam
{
    string lookup_key_en;
    string display_text;
    spell_type origin_spell;
    bool pierces;
    optional<actor_ref> ranged_attack_target;
};

enum class sensory_mode
{
    PLAIN,
    VISUAL,
    SOUND,
};

struct applicability
{
    bool requires_player;
    bool requires_foe;
    bool requires_named_foe;
    bool requires_god;
    bool requires_caster_visible;
};

struct message_line_pattern
{
    string pattern;
    sensory_mode sensory;
    optional<msg_channel_type> channel;
};

struct cast_message_context
{
    const monster &caster;
    resolved_target target;
    spell_type spell;
    resolved_beam beam;
    god_type god;
    bool unseen;
    bool silent;
};

struct selected_message
{
    string stable_id;
    string materialization_case_id;
    vector<message_line_pattern> lines;
    cast_frame frame;
    applicability conditions;
    bool implies_gesture;
    bool audible;
};
```

`resolved_target` 必须覆盖玩家、自身、其他怪物、地形、位置、“空气”和泛指
“某物”；`unresolved_target_tag` 只用于诊断，不得进入正常渲染路径。

`resolved_beam` 拥有渲染所需的英文查询键和已解析显示参数，不能只传
`beam_type`。现有 `get_short_name()` 还依赖 `short_name`、远程攻击对象、
`name`、`pierce` 和具体法术，单个枚举不足以重建结果。

多行消息按行保存 sensory/channel 元数据，输出阶段不得再从每行的
`VISUAL:`、`SOUND:` 等正文前缀推断频道语义。

推荐处理顺序：

```text
英文候选键
  → 在消耗 RNG 前按“整 key 覆盖表”选择 structured 或 legacy 路径
  → structured 路径只从 canonical English DB 选择一次原始变体
  → 对该英语变体执行一次既有 @foo@ 展开与 Lua
  → 用变体身份取得已验证的基础 stable ID 和元数据
  → 先判断 __NONE 与适用性；不适用候选不执行后续 [a|b] 选择
  → 若 resolves_target=true，先解析一次目标并保留现有 RNG 顺序；否则跳过
  → 解析 beam，再生成 actor 与其他 bindings
  → 用 canonical English 值绑定 @at@、@target@、@beam@
  → 执行一次 legacy [a|b] 随机物化并记录分支身份
  → 用“变体身份 + 物化签名”取得 materialization case
  → 无随机查询已物化的整句模板
  → 填充类型化实体槽
  → 输出消息
```

任何游戏行为都不得再从本地化正文反推。

## 6. 怪物施法句型

本地化目录提供“动作框架 × 目标关系”的少量完整句型：

```text
mon.cast.projectile.at
${actor}向${target}射出${beam}。

mon.cast.projectile.next_to
${actor}朝${target}旁边射出${beam}。

mon.cast.projectile.past
${actor}射出${beam}，从${target}旁边掠过。

mon.cast.gaze.at
${actor}凝视着${target}。

mon.cast.gesture.at
${actor}一边吟诵，一边指向${target}。

mon.cast.invocation.at
${actor}祈求${god}向${target}降下怒火。
```

具体法术可以覆盖通用框架。以下顺序只供生成器解析模板继承：

1. 具体稳定 ID + 关系；
2. 具体稳定 ID；
3. 动作框架 + 关系；
4. 动作框架默认模板；
5. 无合法纯模板：不生成 structured 项，整个 key 路由 legacy。

生成器按该顺序为每个 `stable_id × relation × language` 物化最终模板；运行时
只做一次无随机 map 查询，不再遍历回退链。因此不需要人工把所有目标模板
机械复制成三份，也不会为模板继承额外消耗 RNG。

`PAST` 不得统一译成“向目标身后”。它表示轨迹经过、越过或擦过目标，
而不是目标点位于目标背后；目标还可能是地形或空气。

## 7. Fork 专属 catalog overlay

第一阶段采用 `monspell` 专用接入点和通用但 opt-in 的 catalog overlay。它不
向 SpeakDB 装载新 TextDB 文件，也不覆盖任何上游 key。建议目录：

```text
crawl-ref/source/
  fork-message-overlay.h
  fork-message-overlay.cc
  fork-message-overlay.generated.inc

.claude/data/message-overlay/
  monspell.json

.claude/scripts/
  generate_message_overlay.py
  audit_message_overlay.py
```

各文件职责必须保持互斥：

| 文件 | structured 路径职责 | legacy 路径职责 |
|---|---|---|
| `dat/database/monspell.txt` | 唯一 canonical 选择、递归展开、Lua 和 `[a|b]` 来源 | 英文现有行为 |
| `dat/database/zh/monspell.txt` | 不读取、不选择、不执行递归或 Lua | 中文未迁移 key 的现有行为 |
| `.claude/data/message-overlay/monspell.json` 与 `monspell/*.json` | 聚合头维护 schema/catalog 顺序；独立 fragment 人工维护 stable ID、元数据、物化策略和各语言纯模板 | 无运行时职责 |
| `fork-message-overlay.generated.inc` | 生成的覆盖表、catalog、物化 case 和纯模板 | 无职责 |

因此最终设计中不存在 `fork-message-overlay.txt` 或
`zh/fork-message-overlay.txt`。overlay 是 C++ catalog，不是第三套 TextDB；
不会产生重复 key、数据库覆盖顺序或翻译库权重漂移。

人工维护的 manifest 是本地事实源。每个变体至少记录：

```text
schema_version
stable_id
domain
canonical_key
canonical_variant_identity
upstream_variant_fingerprint
selection_graph_fingerprint
upstream_weight
frame
applicability
line_metadata
slot_schema
required_arguments
materialization_policy
materialization_cases
english_snapshot
localized_templates
recursive_dependency_fingerprints
tombstone
```

`fork-message-overlay.generated.inc` 是生成器物化的只读 sidecar catalog，保存
canonical English 变体身份、适用条件、逐行元数据、物化 case 和各语言最终
模板；不得人工编辑。语言只选择最终纯模板，不拥有独立的 TextDB 变体身份。

覆盖单位是“canonical key 的完整可选择闭包”，不是单个随机变体。一个 key
只有在其全部顶层变体、递归依赖、正文随机分支、Lua 输出边界和所有支持语言
模板都可验证时，才能进入 structured 覆盖表；否则整个 key 在任何 RNG 调用
之前直接路由到 legacy。严禁同一个 key 中一部分变体 structured、另一部分在
抽取后 fallback。

其他规则：

- `stable_id` 由人工分配，正文 hash 只用于检测变化；
- 上游仅修改措辞或标点时，经人工确认后可以沿用 ID；
- 语义、参数、可见性或频道变化时必须创建新 ID；
- 删除的 ID 保留 tombstone，防止旧翻译静默绑定到新含义；
- active ID 和 tombstone 共同参与全局唯一性检查，任何历史 ID 都不得复用；
- 未列入 structured 覆盖表的整个 key 继续使用当前语言的 legacy TextDB。

## 8. 运行时兼容协议

### 8.1 载入期验证与域级禁用

catalog overlay 必须在开始游戏、消耗消息 RNG 或执行嵌入 Lua 之前，针对
canonical English SpeakDB 快照完整载入并验证。验证范围包括 manifest schema、
覆盖 key 的完整选择闭包、sidecar catalog、模板槽、stable ID、变体身份、
权重、递归依赖、正文随机项、Lua 边界和所有支持语言的最终纯模板。

某个 domain 的 overlay 只允许两个载入结果：

- `ENABLED`：生成 structured/legacy key 覆盖表，所有 structured key 均通过验证；
- `DISABLED`：存在损坏、未知版本或 catalog 不一致，整域在首个查询前禁用。

`DISABLED` 域从第一次查询起直接走 legacy。不得先从 overlay 随机抽取，发现
协议错误后再调用 `getSpeakString()` 查询 legacy；那会额外消耗随机数，并且
无法撤销已经发生的递归展开或 Lua 副作用。

`ENABLED` 不表示该域所有 key 都已迁移。adapter 必须在查询候选 key、消耗
任何 RNG 之前读取覆盖表：structured key 进入 canonical English 路径，其他
key 直接进入当前语言的既有 legacy 路径。这个选择不能依赖抽中的变体。

### 8.2 一次抽取的窄 API

overlay 不在正文中嵌入 `@message_id@` 或版本化协议头。stable ID 与元数据放在
生成的 sidecar catalog 中，通过 canonical English parser 提供的变体身份关联。
数据库层和 legacy replacement 层提供以下窄边界：

运行时 locator 与审计 provenance 必须分开。运行时 locator 只包含规范 key 和
变体序号；实际贡献文件、文件载入序号和该文件内的定义序号属于 canonical dump
的 provenance。载入期用完整 source/selection fingerprint 验证 locator 所属快照，
不能要求 DBM 在查询时恢复已经丢失的源文件信息。

locator 只用于把本次选择连接到已经验证的 catalog，不承诺跨上游版本稳定；
跨版本身份仍由人工维护的 `stable_id` 承担，正文 hash 只负责漂移检测。这样既
避免把 provenance 误当运行时身份，也保留年度审计所需的覆盖顺序证据。

```cpp
struct variant_locator
{
    string canonical_key;
    size_t variant_ordinal;
};

struct raw_textdb_selection
{
    variant_locator locator;
    string raw_pattern;
    selection_trace trace;
};

enum class raw_selection_status
{
    MISSING,
    SELECTED,
    CORRUPT,
};

struct raw_selection_result
{
    raw_selection_status status;
    optional<raw_textdb_selection> selection;
};

struct expanded_canonical_message
{
    raw_textdb_selection selection;
    string expanded_pattern_en;
    selection_trace db_and_lua_trace;
};

struct materialization_choice
{
    string site_identity;
    int option_index;
};

struct canonical_cast_bindings
{
    string at_en;
    string target_en;
    string beam_en;
    target_resolution_trace target_trace;
};

struct canonical_pre_random_pattern
{
    expanded_canonical_message expanded;
    string pattern_en;
    target_resolution_trace target_trace;
};

struct legacy_materialization
{
    string randomized_pattern_en;
    vector<materialization_choice> choices;
    materialization_signature signature;
    rng_trace substring_trace;
};

raw_selection_result select_canonical_speak_variant(const string &key);
expanded_canonical_message expand_canonical_speak_selection(
    raw_textdb_selection selection);
canonical_pre_random_pattern bind_canonical_cast_tokens(
    const expanded_canonical_message &expanded,
    const canonical_cast_bindings &bindings);
legacy_materialization materialize_legacy_randomness(
    const canonical_pre_random_pattern &ready);
```

这些 API 不是第二套 parser 或 replacement 实现；应从现有
`getSpeakString()` 和 `maybe_pick_random_substring()` 抽取可观测边界。契约是：

1. 每个 structured 候选只从 canonical English DB 选择一次；
2. 在递归展开和 Lua 执行前取得规范 key、变体身份与原始正文；
3. expansion 只消费已经选择的顶层变体，并完整执行既有 `@foo@` 与 Lua；若
   递归深度/替换次数超限、`@` 未闭合、递归子项损坏、Lua 错误或 Lua 未闭合，
   则标记 `CORRUPT`，但仍完成本次 legacy 必须产生的 Lua/output/RNG trace；
4. expansion 后先识别 `__NONE`、再判断适用性；不适用候选不得执行 `[a|b]`；
5. 适用候选仅在 `resolves_target=true` 时完成现有目标解析 RNG，再由
   `bind_canonical_cast_tokens()` 以 canonical English 值替换 `@at@`、
   `@target@`、`@beam@`；false descriptor 跳过目标解析且不得包含目标 token；
6. materializer 按现有源码顺序对每个 `[a|b]` 恰好调用一次 `random2()`，并
   同时返回实际英语正文、分支身份和 trace；
7. sidecar catalog 和模板查询是纯 map 查找，不消耗 RNG、不执行 Lua；
8. legacy 只能在查询前由覆盖表选择，不能在 structured 抽取后启动；
9. 抽取后出现 `CORRUPT` 时停止该候选，不得通过二次查询伪造回退。

低层 API 只报告选择与物化事实；`SUPPRESS`、`INAPPLICABLE` 和 `RENDERED`
由上层 adapter 产生。递归引用最终产生的 `__NONE` 必须映射为 `SUPPRESS`。

`site_identity` 由 canonical 顶层变体身份、递归选择路径和展开后从左到右的
零基站点序号组成；选项数量与顺序进入 fingerprint。不得用翻译正文偏移量或
所选字符串本身充当身份。

`materialize_legacy_randomness()` 不得接收仍含上述三个施法 token 的 raw
expansion；它只接受 `canonical_pre_random_pattern`，并在 debug/测试构建中
断言 `@at@`、`@target@`、`@beam@` 均已消失。该英语 pattern 用于复现既有
扫描范围、生成物化签名和英文 golden；最终中文仍由语义化 target/beam 参数
填充纯模板，不把这里绑定的英语显示文本直接带入中文输出。

如果原型无法在不 fork 通用 parser 的前提下提供这个边界，则 Phase 1 不得
开始；维持 legacy 比接受不可证明的随机行为更安全。

### 8.3 legacy 物化结果如何进入模板

只为了保持 RNG 而执行 expansion 或 `[a|b]` 后丢弃正文是不合格实现。manifest
必须为每个 canonical 变体声明物化策略：

```cpp
enum class materialization_policy
{
    NONE,
    CASE_MAP,
    CAPTURE_SLOT,
    LEGACY_ONLY,
};
```

- `NONE`：仅用于没有显示相关递归随机结果、Lua 动态输出或 `[a|b]` 的变体；
  生成器必须证明 canonical materialization 与英文模板骨架一致；
- `CASE_MAP`：完整物化签名映射到稳定的 `materialization_case_id`，每个 case
  同时提供英文和中文纯模板；
- `CAPTURE_SLOT`：把已声明、有限且可审计的分支身份映射为类型化 choice 槽；
  模板接收 choice ID 对应的本地化值，不直接接收未经声明的英语片段；
- `LEGACY_ONLY`：动态输出不可穷举、Lua 输出无稳定边界或无法证明投影完整时，
  整个 key 不进入 structured 覆盖表。

`materialization_signature` 必须包含递归变体链、Lua 动态输出身份、每个
`[a|b]` 站点及所选下标，以及所有声明的 capture 身份。递归风味文本和 Lua
产生的显示文本与 `[a|b]` 一样，必须通过 `CASE_MAP` 或 `CAPTURE_SLOT` 进入
最终模板，不能仅记录 trace 后丢弃。

英文 structured 输出在完成确定性的实体槽替换后，必须与同一次 canonical
materialization 走现有 legacy replacement 所得正文逐字节一致。中文使用同一
`materialization_case_id` 或 choice ID 选择本地化模板，可以重排语序，但不能
重新随机。如果这一等价无法由生成器和 golden 证明，该 key 保持 legacy。

首个生产 `CASE_MAP` 切片把 `materialization_case_id` 定义为稳定子变体 ID：
它与顶层 variant stable ID、其他 case ID 及 tombstone 共享全局唯一命名空间；
语义删除后同样必须保留 tombstone。当前只启用无递归、无 Lua、恰好一个有限
`[a|b]` 站点的严格子集，生成期与加载期都从 canonical key、顶层 ordinal 和
option index 重建完整 signature 集合。`march of sorrows bone dragon cast` 的
`PROJECTILE` frame 表示复用现有 target/beam binding 时序，而非重新分类法术。
当前生产 catalog 跟踪 198 个 canonical key、266 个 canonical variant，其中
189 个 key、256 个 variant 进入 structured 覆盖表，9 个完整 key、10 个 variant
为 `LEGACY_ONLY`。descriptor
用 `binding.resolves_target` 独立声明是否执行目标解析，因此 `${target}` 不再是
目标解析的隐式开关；不引用 target 的 actor-only 模板也可保持既有目标 RNG trace。
binding resolver 在目标解析前接收已验证的 `frame`、`resolves_target` 与
`implies_gesture`。actor schema 已支持 `actor_ref`、`actor_possessive_name`、
`actor_possessive_pronoun` 和 `actor_reflexive`，并只验证模板实际声明的字段。
英文模板仍可使用所有格和反身槽，中文模板可按自然语序省略冗余代词，只要完整
EN/ZH 模板矩阵的 schema union 与声明一致。第三批的 `mennas cast` 首次启用
生产 `VISUAL` sensory/channel metadata：纯模板不携带 `VISUAL:` 正文协议前缀，
输出层将 sensory 映射到 `MSGCH_TALK_VISUAL`，并由现有
`mons_speaks_msg()` 在 caster 不可见时抑制该行。candidate 搜索本身不会把
unseen 前缀缺失回退到 normal key；这里的不可见抑制属于选中 structured 消息后的
sensory 输出语义。当前另启用窄 applicability 子集：
`requires_player`、`requires_foe` 与 `requires_caster_visible`；
requires named foe/god 与 `audible=true` 仍被生成期和加载期拒绝。

这些 applicability 条件均为逐 variant metadata，并在 canonical English
选择之后、binding 之前判断。`requires_player` 的 runtime snapshot 与 legacy
`invalid_msg()` 共用 `resolve_mon_speech_applicability()`，因此保留 friendly
caster 在无有效 foe index 时把玩家视为 foe 的特殊规则；
`requires_caster_visible` 使用同一 snapshot 的 unseen 状态。不适用结果为
`INAPPLICABLE`，candidate 搜索继续下一候选，既不重抽当前 key，也不调用
target/beam/actor binding。silent-unprefixed 的 `ACCEPT_ANY_NONEMPTY` 兼容路径
继续绕过这些条件。`requires_foe` 复用同一 snapshot 的 `no_foe`，并由独立
`resolved_foe` payload 绑定 player/monster 显示；它不复用 beam target，也不改变
target relation RNG。

actor possessive 的本地化允许一个受控窄适配：neutral pronoun 只说明英语采用
singular-they 变格，现有 `pronoun_plurality()` 因主谓一致会返回 true，不能单独
证明中文应使用复数。structured binding 仅在 caster 可见且
`mons_is_or_was_unique()` 证明单一身份时，通过 literal-only context key
`structured actor possessive|neutral singular` 渲染“其”；否则继续使用全局
pronoun 表。该规则不改变英文 canonical binding，也不修改通用代词语义。

第四批的 `airstrike blizzard demon cast` 新增窄类型
`actor_arms_plural` 槽。production binding 在 canonical English 边界调用
caster 的 `arm_name(false, &can_plural)`，只有可复数时才继续调用
`arm_name(true)`；这一顺序与 legacy replacement 完全一致。该解析由 descriptor
派生的 `binding_requirements.needs_actor_arms_plural` 控制，不含该 slot 的既有
structured key 完全不调用随机身体部位 API。英文值用于替换 legacy `@arms@`，
中文值只允许通过 `monster body part plural` 的 literal-only `NC_`/`C_` 映射
生成。真实暴雪恶魔的受控语义值为 `strata` → “云层”（并保留通用
`arms` → “手臂”）；未知 canonical body-part 不会穿透 renderer，而是因缺失
localized binding 进入 `CORRUPT`，使年度上游漂移可见。
不可复数 caster 也 fail closed 为 `CORRUPT`：这有意比 legacy 输出
`NO PLURAL ARMS` 更严格；两条路径在该错误边界的 RNG 消耗相同，但错误输出不承诺
逐字节等价。正常暴雪恶魔仍保持英文逐字节输出和 RNG 等价。

target relation matrix 由 `binding.resolves_target` 决定：`true` 必须完整提供
`AT/NEXT_TO/PAST`，`false` 必须且只能提供 `NONE`。non-target descriptor 禁止
声明 `resolved_target` 槽；production resolver 不调用目标解析、不消费目标 RNG，
target trace 为空。加载期还检查 canonical raw pattern，materialization 则在
binding callback 前再次检查 expanded pattern，防止递归或漂移引入
`@at@/@target@` 后被空字符串替换。

### 8.4 canonical English 与跨语言 RNG 契约

本项目明确采用“所有语言共享 canonical English 选择与物化轨迹”的方案：

- structured key 无论当前语言为何，都只查询英语 `monspell.txt`；
- 顶层选择、递归 `@foo@`、Lua 和 `[a|b]` 均只执行一次；目标解析仅在
  descriptor 声明 `resolves_target=true` 时执行一次；
- structured 路径不得读取 `zh/monspell.txt`，也不得执行本地化递归、Lua 或
  `[a|b]`；
- 当前语言只影响最后一次无随机 catalog 模板查询和确定性的类型化槽显示。

完整调用顺序必须保持为：

1. 顶层变体选择，随后执行递归选择与 Lua；
2. 识别 `__NONE` 并检查适用性；被拒候选不消耗后续 RNG；
3. 对适用且 `resolves_target=true` 的候选执行目标解析，包括现有
   `one_chance_in()`，随后以 canonical English 值替换 `@at@`、`@target@`、
   `@beam@`；false 候选跳过目标解析，只绑定已声明的非目标 token；
4. 对替换完成的 canonical pattern 按正文顺序执行 `[a|b]` 的 `random2()`；
5. stable case 查询、模板选择和槽渲染，全程不再使用 RNG。

该顺序对应当前 `_speech_message()` 的候选检查、`_speech_fill_target()` 的目标
推断，以及 `mons_speaks_msg()` 调用 `do_mon_str_replacements()` 后才执行
`maybe_pick_random_substring()` 的调用链。原型测试必须以调用边界而非仅以
最终 RNG 状态固定这个顺序。

trace 比较覆盖顶层顺序、显式/默认权重 10、每个递归选择、递归上限、Lua
执行顺序与副作用、descriptor 要求时的目标解析 RNG、每个正文随机站点及其结果。
对同一 seed 和
同一语义上下文，EN/ZH structured 路径必须拥有完全相同的 trace；英文还必须
满足新旧路径的逐字节输出与最终 RNG 状态等价。

该跨语言保证只覆盖 structured key。未迁移 key 仍走当前语言的 legacy DB，
保留现状，不宣称修复既有语言间 RNG 差异。structured 中文模板无需也不得
拥有独立递归图，因为唯一的随机图就是 canonical English 图。

这会使已迁移中文 key 从“语言专属 legacy RNG”切换到 canonical English RNG；
这是建立语言无关游戏状态的显式兼容性决策，而非零行为变化。Phase 0 必须
量化现有 EN/ZH trace 差异并单独复审该切换；英文路径仍以零 RNG、Lua 和输出
变化为硬门禁。

### 8.5 候选搜索状态机

adapter 返回强类型结果，完整保留 `_speech_message()` 的候选搜索语义：

```cpp
enum class message_result
{
    MISSING,
    SUPPRESS,
    INAPPLICABLE,
    RENDERED,
    CORRUPT,
};

struct message_lookup_result
{
    message_result result;
    optional<raw_textdb_selection> selection;
    optional<legacy_materialization> materialization;
    optional<selected_message> message;
};
```

| 结果 | 普通 / unseen 候选 | `silent` 前缀候选 | 是否停止 |
|---|---|---|---|
| `MISSING` | 继续下一个候选 | 重试同一候选的无前缀 key | 否 |
| `SUPPRESS` | 对应 `__NONE` | 对应 `__NONE` | 立即停止并保持沉默 |
| `INAPPLICABLE` | 跳过并继续 | 按现有兼容语义重试无前缀 key | 否 |
| `RENDERED` | 输出消息 | 输出消息 | 输出后停止 |
| `CORRUPT` | 记录诊断并抑制该次消息 | 同左 | 停止，禁止重新抽取 |

载入期整体验证通过后，`CORRUPT` 正常情况下不可达；保留该状态只用于防御
内存破坏、catalog 不变量失效等运行时故障，不能把它当作常规 fallback。

legacy 路径在迁移完成前继续使用现有 `invalid_msg()`。结构化路径由 manifest
显式记录 `requires_player`、`requires_foe`、`requires_named_foe`、
`requires_god`、`requires_caster_visible`（现有 `visual_only` 语义），以及
每行的 `PLAIN / VISUAL / SOUND` 和频道。单元测试必须
逐支复现当前 `_speech_message()` 的键顺序、silent 回退和 `__NONE` 行为。
尤其是 silent 前缀结果缺失或不适用时会查询无前缀 key；当前 legacy 代码对
该次无前缀查询的任意非空结果直接接受，不再次调用 `invalid_msg()`。在另行
批准语义修正前，兼容测试必须把这一点当作既有行为，而不是顺手“修复”。

状态机顺序也是 RNG 契约的一部分：顶层选择在 expansion 前得到的 `MISSING`
或 `CORRUPT` 不执行递归/Lua；expansion 中途检测到的 `CORRUPT` 仍完成本次
legacy expansion/Lua 的 output 与 RNG trace，随后停止，不解析目标或执行
`[a|b]`。`SUPPRESS` 与 `INAPPLICABLE` 已执行 canonical expansion/Lua，但同样
不得解析目标或执行 `[a|b]`；只有最终可渲染候选才产生
`legacy_materialization`。

### 8.6 运行时诊断

至少提供以下按 domain 和 schema 版本聚合的计数器：

- `overlay_hit`；
- `legacy_fallback`；
- `candidate_inapplicable`；
- `message_suppressed`；
- `overlay_corrupt`；
- `unknown_schema`。

年度升级后用这些计数器观察真实覆盖率和异常路径；它们只用于诊断，不得
改变候选顺序、RNG 消耗或消息输出。`legacy_fallback` 这个历史名称只统计
查询前的 legacy 路由（包括 domain 禁用），绝不表示 structured 抽取后的回退。

## 9. 与上游代码的接触面

长期目标是把本地逻辑放进新增文件，只在上游文件保留小型接入点：

- `database.cc`：拆分 canonical English“选择原始变体 / 展开所选变体”的窄 API；
- `mon-util.cc` / `stringutil.cc`：复用既有 `[a|b]` 算法并暴露物化身份与 trace；
- `mon-cast.cc`：include、覆盖表路由、候选 adapter、调用 typed renderer；
- `Makefile.obj`：登记一个对象；
- Android `Android.mk`：登记一个源文件。

不应：

- 重写 `database.cc` 的通用 TextDB parser；
- 批量修改英文 TextDB；
- 向 SpeakDB 装载 fork 专用 key 或覆盖原 key；
- 把所有 TextDB 转成 stable ID；
- 让 overlay 直接依赖 `TextDB`、`DBM*` 或私有权重函数；窄 API 由数据库层
  实现，overlay 只消费稳定的选择结果；
- 在 TextDB 正文中嵌入 stable ID、版本头或其他 adapter 私有协议；
- 让本地化正文影响手势、目标、可见性或频道判断。

## 10. 年度上游升级依据

本地标签对比显示，`0.33.1 → 0.34.1` 期间相关改动约为：

| 文件 | 变化量 |
|---|---:|
| `mon-cast.cc` | `+1070/-630` |
| `monspell.txt` | `+117/-6` |
| `monspeak.txt` | `+150/-116` |
| `database.cc` | `+22/-4` |
| `graffiti.txt` | 新增约 1090 行 |

因此：

- `mon-cast.cc` 是高变动文件，本地接入必须保持为少数小 hunk；
- `database.cc` 相对稳定，可以接受一个窄 API，但不能扩大成 parser fork；
- 全量稳定 ID 会把每年数百行普通文本变化变成人工映射工作；
- 新模块、manifest 和生成器基本不会产生上游文本合并冲突。

## 11. 年度升级 Runbook

### 11.1 建立基线

记录：

- 旧上游 tag；
- 新上游 tag；
- overlay manifest schema 版本；
- 生成器版本；
- 英文 golden；
- 当前术语表 hash。

先导入干净的新上游版本，再重放少量 fork 集成提交；不要先解决翻译数据。

### 11.2 结构化漂移审计

审计器解析新旧 TextDB，报告：

- 新增、删除和可能重命名的 key；
- 变体数量、顺序和 `w:N` 权重变化；
- 英文正文 fingerprint 变化；
- `@placeholder@` 集合变化；
- 递归引用目标变化；
- `[a|b]` 站点、选项数量、顺序和物化 case 变化；
- `VISUAL:`、`SOUND:`、`__NONE` 等控制语义变化；
- structured key 的完整选择闭包、物化策略和候选键可达性。

审计阶段不得自动把旧 stable ID 绑定到新语义。

审计器必须与生产 parser 同构。首选由生产代码导出 canonical dump，离线工具
只比较 dump；若必须维护独立 parser，则须通过共享 fixture 证明以下行为一致：

- key 小写化和规范化；
- 文件载入、覆盖顺序和同名 key 合并；
- 空条目及语言库回退；
- 显式权重和默认权重 10；
- 标准与非标准条目分隔符；
- alias；
- 递归替换顺序、深度和次数上限；
- `maybe_pick_random_substring()` 的扫描顺序、空项处理和 `random2()` 参数；
- 控制前缀；
- Lua 的识别范围与执行边界。

### 11.3 Fingerprint 规范

同时记录 source fingerprint 和 semantic fingerprint：

- source fingerprint：输入必须是合法 UTF-8；移除 BOM，将 `CRLF`/`CR`
  规范为 `LF` 后对字节流取 hash；除此之外保留空白、注释和正文的每个字节；
- semantic fingerprint：对生产 parser 的 canonical dump 做带版本的确定性
  序列化，包含规范 key、来源文件及载入顺序、变体身份、正文、权重、控制
  前缀、槽、递归边、`[a|b]` 站点和 Lua 边界；
- hash 输入必须包含 fingerprint schema 版本。

只改注释或换行形式时 source fingerprint 可以变化而 semantic fingerprint
不变；任何解析图变化都必须改变 semantic fingerprint。active ID 与 tombstone
共同进入全局 ID 唯一性检查。

### 11.4 人工分类

每项漂移只能归为：

- `unchanged`：保留；
- `textual-change`：确认后沿用 stable ID；
- `semantic-change`：创建新 ID 并重新翻译；
- `removed`：写入 tombstone；
- `new-uncovered`：整个 key 暂时直接路由 legacy，或加入迁移队列。

### 11.5 重新生成和重放接入

生成器必须满足：

- 输出幂等；
- active ID 与 tombstone 在全历史范围内唯一；
- structured 覆盖表只包含闭包完整的 canonical key；
- canonical English 权重和选择图与上游一致；
- 每个物化签名恰好映射一个 stable ID、case ID 和各语言纯模板；
- `required_arguments` 与模板占位符一致；
- 完整 SpeakDB 的 `${slot}`、`@recursive_key@` 和保留字冲突审计通过；
- 生成后不存在未解释的差异。

上游接入补丁应按符号和 API 定位；锚点消失时必须失败退出，不能按旧行号
盲目打补丁。

## 12. 验证策略

必须覆盖：

- manifest schema，以及 active ID 与 tombstone 的全局唯一性；
- generator 幂等性；
- 审计器 canonical dump 与生产 parser 在共享 fixture 上完全一致；
- 上游 key、变体、权重、递归引用、Lua 边界、`[a|b]` 和占位符契约；
- structured 覆盖以整 key 为单位，禁止部分变体迁移；
- 英文固定 seed 的逐字节 golden；
- 英文完整轨迹等价，包括顶层、递归引用、Lua、目标解析和正文随机项；
- `[casts|pitches]`、`[pulses|vibrates]` 等真实 monspell case 的物化回归测试；
- random materializer 的输入已完成 `@at@/@target@/@beam@` canonical 绑定；
- 每个物化结果都通过 `CASE_MAP` / `CAPTURE_SLOT` 进入最终模板，禁止丢弃；
- EN/ZH 在同 seed、同语义上下文下的 canonical RNG/Lua trace 完全一致；
- structured 中文路径不读取 `zh/monspell.txt`，不执行语言专属随机或 Lua；
- `frame × relation × visibility × target-kind` 中文快照；
- overlay 缺失、损坏或未知版本时，载入期禁用该域且首次查询直接走 legacy；
- 抽取后 `CORRUPT` 不重新查询、不额外消耗 RNG、不重复执行 Lua；
- `MISSING / SUPPRESS / INAPPLICABLE / RENDERED / CORRUPT` 的逐分支测试；
- 最终输出无 `${slot}`、legacy `@foo@` 和内部协议残留；
- 多行消息逐行 sensory/channel 语义等价；
- 本地化正文不参与行为判断；
- `T_()` / `C_()` 借用指针不被持久保存；
- 英文 DB 键与本地化显示值严格分离；
- 运行时诊断计数器只观测、不改变随机状态或输出。

实现改动完成后，按风险运行：

```bash
bash .claude/scripts/verify_zh.sh --profile code
bash .claude/scripts/verify_zh.sh --profile review
```

并执行受影响平台构建。

## 13. 分阶段实施

### Phase 0：只读审计与测试基线

- 建立 TextDB 结构化 inventory；
- 固化英文消息、随机行为和中文问题样例；
- 建立年度差异脚本的输入输出契约；
- 实现生产 parser canonical dump，并证明离线审计 fixture 同构；
- 清点 `monspell` 的全部递归动态正文、Lua 和 `[a|b]` 站点；
- 原型化 canonical English 一次抽取/展开、legacy 随机物化 API、五态状态机；
- 比较旧英文、新英文和新中文的完整 RNG/Lua/目标/正文随机 trace；
- 验证物化 case 投影能够复现英文逐字节 golden，且不会丢弃动态正文；
- 实现 `${slot}` schema 与全 SpeakDB 保留字冲突审计；
- 完成架构复审并取得 Go。取得 Go 前不得进入 Phase 1。

### Phase 1：`monspell` 专用 catalog overlay

- 新增 catalog overlay 模块、manifest 和 generated sidecar，不增加 TextDB 文件；
- 引入 `resolved_target`、`resolved_beam`、`cast_frame`、适用条件和逐行
  sensory/channel 元数据；
- 只迁移完整选择闭包可验证，且采用 `NONE` 或已完整证明的
  `CASE_MAP / CAPTURE_SLOT` 的 catchall key；
- 未迁移 key 在查询前直接路由当前语言的 legacy TextDB。

实施状态（2026-07-17）：上述基础设施已落地，当前完整迁移 189 个 canonical
key、256 个 canonical variant，并显式跟踪 9 个 `LEGACY_ONLY` key、10 个
variant。
首个迁移项为 `beam catchall cast`（stable ID
`mon.cast.beam_catchall.v1`，`NONE`）。
normal 与 silent fallback 已接入生产候选搜索；unseen、未覆盖 key 和不支持语言
保持 legacy 语义。具体 artifact、运行时链、验证证据和限制见
[`textdb-i18n-phase1.md`](textdb-i18n-phase1.md)。本状态不表示全部
`monspell` 已结构化；`CASE_MAP` 仅启用上述单有限站点切片，`CAPTURE_SLOT`
仅启用 Nergalle 的三个 `orc name`、leaf-only vocabulary、无 Lua/substring
randomness 窄切片。正常 `monspell` 路径的 gesture 正文嗅探已删除；仅
overlay 故障/未加载或语言不受支持的 compiled-candidate compatibility fallback
保留旧行为。structured binding 已支持显式
`resolves_target`、gesture，以及 actor possessive/reflexive 槽；模板是否引用
`${target}` 不再决定是否解析目标。

production candidate recipe 的 closed-world upper-bound dump 已与 EN/ZH effective
SpeakDB 做 containment join。当前两种语言各命中 251 个 runtime root，Phase 0
inventory 的 262 个 root 中有 11 个不在候选上界内；报告标记
`candidate_key_containment_proven=true`、`runtime_reachability_proven=true` 与
`reachability_kind=SOUND_UPPER_BOUND_NOT_EXACT`。这证明所有生产 candidate lookup
都进入分析域，但不声称逐局精确可达。Phase 2 首批已将
`ensnare arachne cast` 与 `guardian serpent cast targeted` 的全部 5 个 canonical
variant 迁移为显式 behavior metadata；effective runtime EN/ZH mismatch 已降为 0。
第二批又迁移 `wizard cast targeted`、`wizard cast`、
`magical cast targeted` 与 `magical cast` 的全部 8 个 variant，并正式启用
non-target `resolves_target=false` / `NONE` relation 契约。第三批低风险迁移新增
`awaken flesh kobold fleshcrafter cast`、`dispel undead revenant cast`、
`malign offering priest cast`、`sheza's dance cast`、
`silent blizzard demon cast`、`ushabti cast targeted` 与 `mennas cast`，
共 7 个完整 key 闭包、10 个 canonical variant；其中 `mennas cast` 是首个生产
`VISUAL` sensory/channel descriptor，unseen suppression 继续由 sensory 输出层
承担。第四批迁移 `airstrike blizzard demon cast` 的全部 3 个 variant，并以
`actor_arms_plural` 收敛 legacy `@arms@` 身体部位替换，并以 descriptor-derived
requirement 保持随机身体形态的 legacy RNG 调用顺序。第五批迁移 `vv cast`
的全部 4 个 variant 与 `smiting jeremiah cast` 的全部 5 个 variant；两者均
使用 non-target `NONE` 契约，并逐行保留原有 `VISUAL` / `PLAIN` sensory 与
显式 gesture metadata，不增加新槽类型或随机物化策略。第六批迁移
`cantrip gastronok cast` 的全部 9 个 variant，显式表达 3 个 visual-only caster
行和 5 个 player-directed 行的 applicability，并验证末尾 weight-5 变体、
真实 Gastronok 所有格以及 visible/unseen candidate 行为。第七批迁移
`hellfire mortar wiglaf cast` 的全部
3 个 variant，引入窄类型 `resolved_foe` binding 与 `requires_foe` applicability；
target relation 与 foe entity 独立解析，无 foe 的 normal attempt 在 binding
前继续下一个 candidate，silent-unprefixed 无法解析 foe 时则 fail closed。
第八批迁移 `vanquished vanguard nergalle cast` 的全部 2 个 variant；ordinal 0
以受控 `CAPTURE_SLOT` 从同一 canonical English trace 捕获三个有序
`orc name` leaf replacement，EN/ZH 共享捕获值且不重新随机，ordinal 1 使用
`NONE`。依赖闭包、站点顺序、模板槽和 103 项 leaf vocabulary 均由
generator/loader 双重验证。当前 behavior report 的 unanalyzable occurrence 与
fail-closed root 均为 0，`phase2_ready=true`。随后完成独立删除批次：
ordinary legacy targeted `monspell` 仍做目标/beam replacement，但固定
`gestured=false`；structured 路径只使用 descriptor `implies_gesture`。
若 overlay 非 `ENABLED` 或语言不受支持，compiled catalog 中的 `CANDIDATE`
会得到 typed compatibility 标记，并在该窄 fallback 中保留旧正文嗅探。

其后完成一次 21-key/22-variant 分片并行试点：顶层 manifest 只持有 catalog
顺序与 fragment glob，既有 21-key baseline 和三个 worker pilot 分别保存在独立
fragment 中；worker 不写共享 sidecar，集成者在全局 stable ID、case ID 与
tombstone 唯一性检查和确定性排序后统一生成。该机制验证了并行迁移的集成边界，
在该试点基础上，Wave B 又由三个独立 fragment 并行迁移 30 个 actor-only key；
每个 key 都是单一 `NONE` 变体，只声明 `${actor}`，并显式保持
`resolves_target=false`。其中 `ostracise cast` 虽含面向玩家的英文措辞，仍按
legacy candidate applicability 保持全部 `requires_*` 为 false（包括
`requires_player=false`），不从正文代词推导新门禁。72-key catalog 是 Wave B
完成时的阶段计数，不代表剩余条目已经
结构化或可以跳过逐 key 闭包、RNG、适用性与译文审计。

Wave C 再由三个独立 fragment 并行迁移 26 个单变体 key：18 个 unseen 消息使用
无槽纯模板，其中所有以 `You` 开头的 variant 显式声明
`requires_player=true`，其余 applicability 仍按 legacy 保持 false；另外 8 个
visible key 使用 `${actor}`。全部条目均为 `NONE`、`PLAIN`，无递归、Lua 或
`[a|b]`，且不从正文中的听觉措辞推导 `audible` 或 channel。集成后 catalog 为
98 个 key、129 个 variant、258 个逐语言验证单位；仍只是 262 个 inventory root
的子集。

Wave D 的八个分片共审计 80 个 key、93 个 variant。73 个 key、85 个 variant
完整进入 structured 路径；`acid splash cast`、`branch summon cast prefix`、
`chilling breath cast`、`polymorphed wizard cast`、
`polymorphed wizard cast targeted`、`rebounding chill thermic dynamo cast` 与
`summon water elementals elemental wellspring cast` 以整 key 的 `LEGACY_ONLY`
模式留在 catalog 中，共 7 个 key、8 个 variant。它们参与 fingerprint、闭包和
年度漂移校验，但不会被 `monspell_overlay_covers()` 收录，也不会计入 structured
metadata 完整性分母。由于这些 key 当前都不存在 legacy gesture/visual 等
behavior occurrence，behavior report 仍有
`remaining_legacy_behavior_occurrences=0`、`phase2_ready=true`。集成后 catalog
总量为 178 key、222 variant；structured 覆盖为 171 key、214 variant、428 个
逐语言验证单位。

Wave E 的三个分片共审计 20 个 key、44 个 variant。E1 将 8 个单变体 key
迁入 structured，并将 `flashing balestra undying armoury cast` 与
`lee's rapid deconstruction screaming refraction cast` 的 2 个单变体完整标记为
`LEGACY_ONLY`；E2 迁移 5 个 key、19 个 variant，包括 `resolved_foe`、
`requires_foe` 与目标关系矩阵；E3 再迁移 5 个 key、15 个 variant，并验证
无 `@at@` 的 Norris 目标模板在三种 relation 下保持同文。集成后 catalog 总量为
198 key、266 variant；structured 覆盖为 189 key、256 variant、512 个逐语言
验证单位，`LEGACY_ONLY` 为 9 key、10 variant。

candidate dump 还必须匹配 tracked production anchor；anchor 固定经人工审阅的
artifact SHA-256、counts 与 producer contract。审计器另外精确验证六条有序
scenario cover，并由 lowercase base expression 三路 merge/coalesce 重建完整
lookup/attempt 闭包。年度升级生成的新 dump 不得自动更新 anchor；必须先审计
recipe 与 artifact 差异，再显式更新该可达性证明锚点。

### Phase 2：移除正文行为嗅探

- 将 `gesture`、`visual`、`audible` 等变为显式元数据；
- binding resolver 接收已验证 descriptor frame、`resolves_target` 与
  `implies_gesture`；true descriptor 即使模板不引用 target，也只执行一次目标
  解析以保持 RNG trace；false descriptor 完全跳过目标解析；
- 结构化路径不运行正文关键词 heuristic；
- 只有所有仍可达、会影响 `gestured` 的 legacy 变体都已迁移或拥有等价
  元数据，并经可达性审计证明覆盖率为 100%，才能删除全局 heuristic；
- 加入 EN/ZH 行为等价测试。

实施状态：上述门禁已由 `phase2_ready=true`、
`remaining_legacy_behavior_occurrences=0`、`unanalysable_occurrences=0` 与
`fail_closed_behavior_roots=0` 满足，`mon-cast.cc` 的正常 `monspell`
中英文 gesture 正文嗅探已经删除。compatibility fallback 不属于 ordinary
uncovered legacy：它只在 overlay 非 `ENABLED` 或语言不受支持，且 key 是
compiled `CANDIDATE` 时启用旧嗅探，以保持 safe fallback 的行为/RNG 等价。
未来可达 ordinary legacy gesture/visual/audible occurrence 会使审计失败。
generic `mon-speak` 的 `invalid_msg()`、`VISUAL` applicability 与频道前缀
parser 仍服务其他 TextDB 域，未在本批次删除。
窄诊断 seam 将 target observer 与通用 final-emission observer 收敛在默认空
options 中；后者定义于 `mon-speak`，只在 `mons_speaks_msg()` 原本调用
`mprf()` 的位置接收 owning final line、最终频道、effective silence 与
`already_rendered`。默认生产调用的选择、替换与输出不变。该 seam 用于直接覆盖
`mons_cast_noise` 的 ordinary legacy、compatibility legacy 与 structured 分支，
不会让外部 legacy observer 参与 structured binding。

### Phase 3：通用类型化实体槽

- 逐步收敛 `do_mon_str_replacements()`；
- 优先处理所有格、身体部位、神祇和目标关系；
- 按实际问题接入 `monspeak`、`miscast` 等领域。

### Phase 4：语言专用生成器

- 仅在确认现有组合产生系统性问题时处理 `randbook`、`insult` 等；
- 保留 TextDB 随机词库；
- 用语言专用完整模板组织词根和参数，不复用施法上下文。

## 14. 明确不做

- 不建设覆盖全部 TextDB 的万能消息 AST；
- 不引入 ICU 作为当前 TextDB 的第二套模板语法；
- 不为了表面 token parity 机械保留英文词序；
- 不要求中文模板复刻英语词序，但不允许 structured 中文拥有独立的
  RNG、递归或 Lua 图；
- 不一次性迁移全部 `monspeak`、`wpnnoise` 或随机名称语料；
- 不允许年度升级工具自动批准语义重绑定；
- 不用 `@foo@` 承载类型化槽；
- 不在随机抽取、递归展开或 Lua 执行后重新查询 legacy；
- 不迁移无法证明完整 RNG 与副作用轨迹等价的变体。

## 15. 最终决策摘要

1. 已迁移的 `monspell` 完整 key 闭包采用类型化事件与关系渲染；其余 key 保持
   legacy。
2. `monspeak` 只迁移行为约束和高风险关系槽，正文继续留在 TextDB。
3. `miscast`、`shout`、`godspeak`、`wpnnoise` 按需使用通用类型化实体槽。
4. 随机名字、书名、涂鸦和辱骂使用语言专用生成语法，不使用事件模型。
5. 通用 TextDB parser 保持兼容，新增能力通过不装载 TextDB key 的 fork
   catalog overlay 接入。
6. 年度升级由结构化 manifest、fingerprint 和人工分类控制。
7. 运行时复杂度保持局部，离线审计承担大部分维护工作。
8. 类型化槽使用 `${name}`，并接受全 SpeakDB 保留字冲突审计。
9. overlay 在载入期整体验证；禁用域从首次查询起走 legacy，抽取后不回退。
10. 候选搜索使用五态结果，严格复制现有 missing、silent 和 `__NONE` 语义。
11. 只有 parser 同构、完整 RNG/Lua 轨迹和 legacy heuristic 覆盖率通过门禁，
    才能推进相应迁移阶段；删除后的 monspell gesture 审计继续阻断覆盖倒退。
12. structured key 的所有语言共享 canonical English 选择、递归、Lua、目标和
    `[a|b]` 轨迹；本地化只发生在最终纯模板与类型化槽。
13. legacy 动态正文必须通过稳定 case 或声明槽进入最终模板，禁止“执行但丢弃”。
14. structured 覆盖以完整 key 闭包为单位；不能在抽中未迁移变体后 fallback。
15. `fork-message-overlay.txt` 及其中文版本不进入设计，避免重复 key 与装载顺序
    风险。
