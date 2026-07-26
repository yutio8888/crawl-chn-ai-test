# 地牢世界显示文本全量校对计划

本计划对应 GitHub Issue #28。目标是从当前生产枚举、数据表、显示消费者和
`.des` 场景脚本冻结分支、地下城特征、传送门与 vault 玩家可见文本的完整
清单，为每个生产身份或稳定显示槽留下唯一证据卡和终态结论，并在不改变
协议、存档或地图生成行为的前提下顺序落地中文修订。

## 验收边界

- 分支身份以活动 `branch_type` 与 `branches[]` 的双向集合和顺序为权威。
  每项核对短名、长名、入口消息、层数与位置事实、符文和完整描述。
  每张卡还记录 parent、深度范围、层数、flags、入口/出口/逃生特征、
  环境噪声和 descent parents。`shortname` 同时具有英文反查/TextDB key
  路径和最终显示路径：生产值始终保持英文，只在显示 sink 翻译；
  `abbrevname` 和关卡标识同样保持 canonical English。
- 地下城特征身份以活动 `dungeon_feature_type` 与 `feat_defs[]` 的双向集合
  为权威。每项核对显示名、实际交互或危险、通行与阻挡属性、状态和描述；
  证据卡记录 flags、minimap 类别、原始 producer 和实际消费者引用。
  `vaultname`、KFEAT、Lua 与存档 identity 保持 canonical English。
- 传送门家族以当前生产 `dat/des/portals/*.des` 文件集合为权威。没有独立
  显示消息的家族也保留父证据卡，不能从清单中静默消失。
- vault 场景显示槽从全部生产 `dat/des/**/*.des` 的真实显示 producer
  确定性抽取。相同英文在不同触发点不合并；文件、包围锚点、sink 类别和
  稳定序号共同构成显示槽身份。
- 在抽取显示槽前，先枚举全部生产 `.des` 的 `crawl.*` 调用和已知 marker
  constructor/显示字段，建立 producer universe。每种 producer 必须被分类为
  当前显示槽、外部翻译所有权、协议/查找值或诊断；未知 producer 使 inventory
  fail-visible。`crawl.god_speaks` 等玩家显示 sink 和
  `tutorial_msg`/`tutorial_hint` 等查找路径都必须有明确分类，不能因不属于
  当前四个 direct sink 而静默消失。
- 定时传送门的 `initmsg`、`finalmsg`、范围消息、消失消息和场景描述只保存
  英文 source key，并在现有显示 sink late translate。格式命名参数、实体宏、
  颜色标记和 marker schema 原样保留。
- 测试、注释、诊断、wizmode、dry-run 和外部协议 payload 进入明确排除集。
  tutorial、sprint、altar 等特殊模式不得被扫描器静默漏掉；若不在当前翻译
  所有权内，仍记录排除原因和重新进入条件。

## 证据卡必填字段

每个 identity 或稳定显示槽使用同一组可机械校验的字段；`not applicable`
必须显式填写，不能用缺列代替：

- identity、lifecycle、英文源文、当前中文和显示上下文；
- producer、全部相关 consumer 和用户；
- 实际机制或行为，以及目标、范围、条件、例外和玩法后果；
- 触发时机、持久化/序列化分类和 late-translation sink；
- 格式占位符、实体宏、markup 与结构 token；
- glossary/decision 权威、共享依赖组和证据位置；
- terminal conclusion、采用译文、拒绝方案、置信度和暂缓重新进入条件。

结果验证必须绑定当前 inventory digest，并检查每个字段存在且内容有效；
只证明 Markdown 第一列 identity 和最后一列 conclusion 不足以作为完成证据。

## 冻结方法

```bash
python3 .claude/scripts/audit_world_inventory.py \
  --output /tmp/issue28-world-inventory.json
```

审计器复用仓库现有 TAG 分支选择、SourceDB 生产加载顺序、C++ 初始化器切分、
TextDB 物理键解析和 Lua 字符串词法机制。它记录基线、术语表和所有生产输入
SHA-256，并机械证明：

- 分支枚举与数据表集合、顺序和唯一性一致；
- 特征枚举与生产定义集合一致，数值空洞和共享显示别名不会合并身份；
- portal 家族父集合来自当前生产目录；
- 每个显示槽具有稳定 identity、producer、consumer、触发与持久化分类；
- producer universe 中每个调用或字段恰好进入 included/excluded/unknown，
  unknown 集必须为空；
- 显示 source key 能精确命中当前中文 SourceDB；
- 英中描述键、格式参数、实体宏和结构 token 保持一致；
- inventory 与结果证据卡集合双向差集为空，且证据卡必填字段完整。

首轮 inventory 允许以非零状态保存真实发现。修复不得通过硬编码历史计数、
忽略未知 producer 或把近似翻译当作 exact-key 命中来制造绿色结果。

## 最终纠错边界

首轮发现清单记录了 781 个身份（含 516 个 `.des` 显示槽），其摘要为
`05dcadd34933fae5b5f62d892e3dbd29acbe5fdf0bac9647d6303809c911d96b`。
实现阶段按真实 Lua 运行时修正了两类枚举误差：12 个相邻 `initmsg` 字符串
片段合并回完整运行时消息，8 个地图生成或坐标诊断槽转入明确排除集。
机械迁移证明记录在 `docs/world-review-results.md`；旧集合独有 20 项、
新集合独有 0 项，显示包装前后身份双向差集均为 0。

纠错后的第二阶段边界为 761 个唯一身份：40 个分支、211 个地下城特征、
14 个传送门家族及 496 个 `.des` 显示槽；其 inventory SHA-256 为
`7a56e520767dce0a1d57a3af82a4fd14705f2c3b304e8b218865fea33892b2be`。
就绪审阅随后发现 Trove/Wizlab 的有限生产标题没有逐标题身份。机械生产扫描
新增 Trove 12 项、Wizlab 15 项，旧 761 项全部保留，删除 0 项。

就绪审阅纳入 27 个标题后得到摘要
`34d8c6bbf8cdb440253fe49435ac7d719921ccad72aec91e506456d5e14d937c`。
完整 adoption 对象绑定随后补充了 feature 描述键的冠词候选。一次就绪候选
还错误地把首个 TextDB 分隔符前的内容恢复为条目，得到摘要
`3b49625119479dddeaa9aee96790bf2cc056e834fb781bca21b0daf774cd15d8`；
代码复审按生产 `_parse_text_db` 语义拒绝了该假设。移除非生产条目后，
身份集合和实际译文均未变化，完整事实摘要相应更新。

最终生产边界为 788 个唯一身份：40 个分支、211 个地下城特征、14 个
传送门家族及 523 个 `.des` 显示槽。最终 inventory SHA-256 为
`98bf113173ab65ba614b960d827553aae31a5bc52c55e993706f686468ab1cb4`；
17 类违规全部为 0。结果证据卡必须绑定此最终摘要；此前摘要仅作为发现、
纠错与就绪审阅历史保留，不得用于最终覆盖声明。

## 生命周期与明确排除

- 分支生命周期从当前生产 `branch_is_unfinished()` 边界导出；兼容分支不补造
  现役描述，若恢复为现役则重新进入完整审阅。
- 空名 sentinel、内部 overlay 和 dummy feature 保留身份并标明生命周期，
  但不要求虚构玩家显示译文。
- 分支与特征的共享显示名或协议别名只记录依赖关系，不改变枚举 identity。
- 神祇祭坛、怪物、物品、法术和符文专名复用已完成实体审计；本 Issue 只核对
  它们在世界文本中的上下文和组合语义。
- `.des` 的 NAME、TAGS、KFEAT、MARKER、schema 字段、Lua 比较、查找键、
  序列化值和 milestone payload 不属于待翻译显示值。

## 依赖批次与所有权

只读发现可以并行，所有写入保持单写者并按以下顺序完成：

1. 当现有机制无法可靠枚举本类别时，按 `batch-translation-review` 的前置
   例外，由单一 `crawl-coder` 只补齐最小只读 inventory 与负向测试；
   此阶段不编辑任何 ZH 资产或生产显示代码，完成后冻结边界并保存初始发现；
2. 由单一 `zh-translator` 顺序处理分支与特征名称、完整描述及共享术语；
3. 同一翻译写者处理 portal/vault 显示 source key，并同步有效 glossary、
   decision 和结果证据；
4. 由单一 `crawl-coder` 在翻译资产阶段之后接管 C++、Lua、DES、inventory
   和测试，迁移真实显示 sink，同时保持协议与持久化 identity 为英文。
   该 coder 不得重新打开 translator-owned ZH 路径；
5. 证明 inventory、证据卡、翻译资产、术语裁定和代码消费者一致；
6. 对 combined candidate 只运行匹配的 development profile，提交干净候选，
   使用仓库现有机械 reviewer 路由和单次 final gate。

逐项证据卡、集合相等证明、结论统计和最终验证记录在
`docs/world-review-results.md`。

## 明确非目标

- 不修改地图生成、分支布局、vault 设计、符文分布、传送门概率或难度。
- 不翻译 `.des` 协议值，不改变 marker、TextDB 或存档 schema。
- 不建立中文到英文的反向 identity 映射或第二套解析器、ledger、审阅协议。
- 不把攻略、FAQ、商店策略或非实体教程文案混入世界实体清单。
- 不重做已经完成的神祇、怪物、物品、法术和角色机制身份裁定。

## 针对性运行时边界

- 枚举 current branch 的 shortname、longname、entry message 和完整描述；
  `branch_by_shortname()`、帮助 TextDB lookup/fallback 始终使用英文
  shortname，最终标题按当前语言显示。
- 对 unique feature vaultname 验证 English exact round-trip；共享 alias 只
  要求解析为合法生产 identity，不把显示译文送入 Lua/KFEAT/存档路径。
- 对 timed portal 的每种持久化槽和 feature rename 做 EN→ZH、ZH→EN
  save/load 与切换语言测试，断言存储值保持英文而显示跟随当前语言。
- 对 direct display、外部所有权 sink、tutorial lookup 和未知 producer 各有
  正向样例及最小负向变异，防止 producer universe 再次产生静默空洞。
