# 翻译质量评审方法迁移方案

> 状态：执行基线 v0.3；M0 与 M1 已完成，结论见
> [M0 必要性基线报告](translation-quality-m0-report.md)和
> [M1 确定性物化报告](translation-quality-m1-report.md)。
>
> 设计输入：ToME4 翻译质量文档包中的 evaluator 校准、分层抽样、事实判定和
> 匿名裁决思路。该文档包不是本仓库权威来源，且其中部分实现与实验结论无法由
> 当前快照复核；本方案不复制其模型、样本数量、并发参数或质量等级。
>
> 当前决策：M1 的确定性 packet、真值物化和分片验证门已通过；M2 尚未获授权。
> 不替换现有翻译资产、分类 inventory、证据卡、schema-v4 readiness 或 final gate。

## 一、目标与验收边界

本迁移首先回答一个问题：当前 `translation-reviewer` 直接选择
`blocker / needs_fix / suggestion` 时，是否存在可重复观察的缺陷发现、上下文判断
或严重度不稳定；只有观察到实际缺口，才引入最小的新机制。

第一轮迁移的目标是：

1. 用现有已审计 identity 和证据卡建立可复现的 evaluator 校准实验；
2. 将“发现了什么”和“如何映射到现有 severity”分开测量；
3. 保留代表性、风险增强和同源异境三类样本的统计边界；
4. 使用未参与调试的封存样本检验方法是否真正改善；
5. 让所有实验产物保持只读、可删除且不具备合并授权能力；
6. 用数据决定停止、保留有界 packet、采用事实优先输出，或另行申请扩大范围。

设计阶段完成不等于迁移完成。只有满足后文的阶段门，才能进入下一阶段。

## 二、明确非目标

本方案不做以下事项：

- 不建立第二套翻译 readiness、ledger 或 final-gate 协议；
- 不修改 `.agents/policies/review-contract.md` 的当前三档 severity 语义；
- 不给全语料批量标记 Gold、Silver、Candidate 或 Quarantine；
- 不引入 0–4 质量向量、统一加权总分或完整 MQM taxonomy；
- 不以抽样代替 `batch-translation-review` 的完整分类审计；
- 不创建跨全部 TextDB、`source.txt` 和代码文本的统一 `unit_id`；
- 不建设翻译记忆、模糊检索、自动联想或 `reuse_scope` 产品功能；
- 不让 evaluator 自动修改中文资产、术语表、裁决记录或源码；
- 不让无工具 evaluator 对需要源码行为的机制争议作最终裁决；
- 不在本地质量命令中隐式调用外部 provider；
- 不照搬外部项目的固定样本量、分片大小、模型或 worker 数。

翻译记忆和复用范围是独立产品决策；只有用户明确批准后才能另立计划。

## 三、必须复用的现有机制

迁移不得重复建设下列能力：

| 现有能力 | 权威来源 | 本迁移中的用途 |
|---|---|---|
| 术语与规则上下文 | `docs/glossary.md`、`docs/decisions.md`、`.claude/scripts/context_resolve.sh` | 生成当前、可追踪的 packet 上下文 |
| 完整分类 inventory | 各 `.claude/scripts/audit_*_inventory.py` 及对应 review plan/results | 提供 identity、生命周期、生产事实和完整性边界 |
| 逐 identity 证据卡 | `docs/*-review-results.md` | 提供经人工确认的校准候选和事实依据 |
| 全量分类审计流程 | `.agents/skills/batch-translation-review/SKILL.md` | 保证抽样实验不冒充完整审计 |
| 当前 finding 语义 | `.claude/scripts/data/review_findings_v2.schema.json` | 作为最终 severity 映射目标，不在试点中替换 |
| 不可变候选与最终证据 | `.agents/policies/review-contract.md` | 继续独占合并授权；实验结果不得进入该信任边界 |
| 技术与运行门禁 | `.claude/scripts/verify_zh.sh` 及现有审计、扫描和运行测试 | 确认结构/运行事实；模型意见不能覆盖其结果 |

若某个候选分类没有可确定枚举的 identity、完整证据卡或稳定 inventory digest，
该分类不进入首轮试点。不得为扩大样本而先建设通用 inventory。

## 四、迁移取舍

| 外部设计概念 | DCSS 决策 | 理由 |
|---|---|---|
| 冻结 inventory、逐项身份和完整覆盖 | 直接复用 | DCSS 已有更严格的分类 inventory 和集合相等证明 |
| 代表性 / 风险增强 / contrast 分层 | 适配 | 只用于 evaluator 校准和风险统计，不生成全语料质量结论 |
| bounded context packet | 适配 | 从现有证据卡派生，不建立新的规范内容源 |
| evaluator 输出影响事实、宿主派生 severity | 试点采用 | 可直接检验是否比自由选择 severity 更稳定 |
| calibration / holdout 隔离和预注册 | 采用 | 防止在同一小样本上反复调试后宣称达标 |
| 双 evaluator 与匿名裁决 | 条件采用 | 只有首轮基线证明独立评审有净收益时才增加成本 |
| quote 规范化与问题图聚类 | 延后 | 先观察 DCSS 是否真实出现一对多 finding 匹配失败 |
| per-entry 通用 `revision_id` | 暂不采用 | 先绑定现有 identity、inventory digest 和完整 packet bytes |
| 相关术语依赖摘要 | 仅作附加信息 | 仍保留完整 glossary SHA-256，不削弱现有失效边界 |
| Gold/Silver、质量向量与复用等级 | 不采用 | 与现有终态及 readiness 重叠，且当前没有 TM 产品需求 |
| 外部固定样本、分片和并发参数 | 不采用 | 必须按 DCSS 数据分布和实际 provider 重新测量 |

## 五、实验数据流

```text
现有分类 inventory + 已审计证据卡 + glossary/decisions
                         │
                         ▼
              冻结实验 population manifest
                         │
                         ▼
       exploratory / calibration / holdout 确定性分区
                         │
                         ▼
                 bounded context packets
                         │
                         ▼
        当前自由定级基线 / 事实优先 evaluator 试验
                         │
                         ▼
            严格覆盖校验、事实映射与人工裁决
                         │
                         ▼
          报告缺陷发现、误报、稳定性与人工成本
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
        Stop       保留 packet     申请正式化事实协议
```

所有运行产物默认写入：

```text
.artifacts/i18n/quality/<run-id>/
```

该目录已被 Git 忽略。实验工具不得写入翻译资产、`docs/glossary.md`、
`docs/decisions.md`、review results 或 `.claude/metrics/verify/`。

## 六、population 与分区

### 6.1 首轮 population

首轮只选择一个已经完成机械 inventory 和逐项证据卡验证的分类。选择条件：

- identity 完整且唯一；
- inventory 和 reviewed identity 双向相等；
- 每项都有当前英文、当前中文、生命周期和终态；
- 机制文本具有可引用的生产事实；
- inventory、输入文件和 glossary 均有内容摘要；
- 不需要读取未获授权的外部或受限内容。

优先选择同时保存 review-base 中文、adopted 中文和逐输入摘要的分类；这样历史缺陷
revision 与修订后 revision 可以分别重建，而不是从一个终态标签猜测文本质量。

首选但尚未冻结的试点 population 是扩展物品审计中可机械筛选的
`item-description:*` identity family：它保存英文描述、review-base/adopted 中文、
producer/consumer、结构化元数据和输入摘要，也包含适合检验条件、数字、完整性与
自然度的长文本。进入 M0 前仍须由现有 item inventory 证明该 family 的 identity
完整且唯一，并由用户确认；本建议不等于扩大或重做物品全量审计。

population manifest 绑定：

- 基线 Git commit；
- inventory contract 与 SHA-256；
- glossary SHA-256；
- decisions SHA-256；
- 规范化、排序后的全部 identity；
- 输入文件及其 SHA-256；
- 明确排除项和理由；
- 分区规则版本和 seed 标识。

时间戳、主机名和本地绝对路径不得参与 population 身份。

### 6.2 真值与精确 revision 绑定

现有 evidence card 的 `keep / adjust / retranslate / defer ...` 是分类审计的处理终态，
不是脱离文本 revision 的质量标签。例如，`adjust` 通常表示 review-base 中文需要调整，
但同一张卡中的 adopted/current 中文已经落地修正；不得据此把当前中文标成 defect。

校准真值必须遵守：

- 每个结论绑定完整 canonical packet bytes，而不是只绑定 identity 或终态；
- 历史缺陷案例使用精确 review-base 中文、当时英文/生产事实和人工确认的问题；
- adopted/current 中文是另一个独立 revision，只有证据卡与当前 inventory 摘要仍一致时
  才能作为已审阅候选；
- `keep` 只能支持其精确被审 revision，不证明同 identity 的其他中文 revision clean；
- `defer terminology` 和 `defer implementation` 不是 clean/defect 真值，默认进入
  context/adjudication 样本或排除，并记录理由；
- 同一 identity 的 before/after 对必须位于同一分区，防止答案通过配对泄漏；
- 人工裁决记录必须绑定 packet digest，packet 改变后旧真值只能作为历史证据。

现有 terminal conclusion 可以帮助发现候选案例，但不能单独生成 benchmark 标签。

### 6.3 四类集合

1. `exploratory`：已经用于设计、历史争议或调试的案例；可修改规则，不作泛化证据。
2. `calibration`：允许查看裁决并调整 packet、事实字段和映射规则。
3. `holdout`：与前两者互斥；规则冻结前不查看 evaluator 结果或人工答案。
4. `operational`：仅在 holdout 通过后用于后续正式质量实验，不属于本计划首轮交付。

每个 identity 只能属于一个集合。同一 dependency 或 contrast group 必须整体进入
同一集合，防止同组译法向另一集合泄漏。

### 6.4 样本来源桶

在 calibration 和 holdout 内分别记录：

- `representative`：按生命周期、文本功能、长度和分类分层的代表性样本；
- `risk-enriched`：包含条件、否定、数字、参数、控制 token、长文本、动态组装或
  上下文不确定等事实的样本；
- `contrast`：同源异境、共享词根、合法多译或历史争议的完整对照组。

风险标志只能决定抽样和审核优先级，不能直接生成 defect 或 severity。各桶必须
分别报告，不得用 risk-enriched 的缺陷率估计整个分类的缺陷率。

样本数量不写死在本方案中。实现时根据 population 大小、对照组原子性和能够检测
的最小差异预先登记；结果产生后不得删除争议项来提高指标。

## 七、bounded context packet

packet 只包含当前 identity 的有限、可审计事实：

```text
packet identity and content digest
population and inventory digest
identity and lifecycle
English source/name/description
evaluated Chinese revision (review-base or adopted/current, explicitly identified)
display context and text function
producer, consumer, and user
actual behavior and mechanics facts
target, scope, conditions, exceptions, and consequences
format placeholders, markup, tokens, and newline signature
current applicable glossary rows and decision references
contrast/dependency siblings included in the same packet
relative evidence locations
```

不得向 evaluator 提供：

- 证据卡终态、预期 severity 或 readiness；
- 另一 evaluator 的结果；
- 历史 finding、修复方案或候选 grade；
- provider/model 偏好；
- 主机绝对路径、凭据或无界仓库内容。

packet 使用现有 domain identity，不创建通用 `unit_id`。在首轮试点中，评价身份绑定：

```text
population digest + inventory identity + complete canonical packet bytes
```

任一 packet 字节、inventory、glossary 或 decisions 变化都会产生新评价身份。相关术语
引用可以支持诊断，但不得代替完整 glossary SHA-256。

## 八、事实优先 evaluator 输出

### 8.1 最小 item

首轮事实协议只保留当前三档 severity 所需的信息：

```json
{
  "identity": "...",
  "context_sufficient": true,
  "findings": []
}
```

每条 finding 包含：

```json
{
  "finding_id": "A-001",
  "defect_class": "semantic | terminology | language | technical | context",
  "source_quote": "...",
  "source_occurrence": 1,
  "target_quote": "...",
  "target_occurrence": 1,
  "is_defect": "yes | no | unknown",
  "runtime_or_structure_break": "yes | no | unknown",
  "definite_translation_error": "yes | no | unknown",
  "non_required_preference": "yes | no | unknown",
  "changes_player_understanding": "yes | no | unknown",
  "body": "...",
  "evidence_refs": []
}
```

`unknown` 不能被宿主转换成 `no`。模型不输出最终 severity、readiness、grade、修复后的
中文或授权状态。

### 8.2 证据跨度

evaluator 输出短 `quote + occurrence`；宿主在 packet 的原始字段中解析位置。偏移由
宿主生成，不接受模型自报偏移。

漏译可以使用非空 source quote 和空 target quote，但必须同时满足：

- `is_defect=yes`；
- `definite_translation_error=yes`；
- body 说明缺失命题及其预期语义位置。

quote 不存在、occurrence 越界或多个位置无法消歧时，该 finding 进入人工队列，不能
自动映射 severity。

### 8.3 逻辑校验

以下组合必须失败，不得静默修复：

- `is_defect=no` 且 `definite_translation_error=yes`；
- `is_defect=no` 且 `runtime_or_structure_break=yes`；
- `is_defect=yes` 且所有影响事实均为 `no`、body 又没有可核验证据；
- `non_required_preference=yes` 且 `definite_translation_error=yes`；
- `context_sufficient=false`，但依赖缺失上下文的事实全部被强行写成确定值；
- identity 缺失、重复、越界或未完整覆盖 packet；
- evaluator 输出宿主专属的 severity、readiness 或 grade。

## 九、映射到当前 severity

事实协议不改变 `.agents/policies/review-contract.md`。宿主映射规则为：

| 已确认事实 | 当前 severity / 状态 |
|---|---|
| 现有确定性门禁或 `zh-code-reviewer` 确认运行、协议、格式或结构破坏 | `blocker` |
| `is_defect=yes` 且 `definite_translation_error=yes`，无运行破坏 | `needs_fix` |
| `is_defect=no` 且仅 `non_required_preference=yes` | `suggestion` |
| 任一决定性事实为 `unknown`、context 不足或事实冲突 | `needs_adjudication`，不得生成 Ready |

模型报告的 `runtime_or_structure_break=yes` 只是技术核验候选；没有现有门禁或
`zh-code-reviewer` 证据时不能单独派生 `blocker`。

`changes_player_understanding` 用于分析和审核优先级，不引入新的 major/minor 等级。
readiness 仍只由当前正式 finding 数组按照现有工具派生。

## 十、阶段与决策门

### M0：必要性基线

不新增脚本或 schema。使用现有证据卡手工构建一个小型 exploratory/calibration
packet 集，让当前评审方式在隐藏精确 revision 真值的条件下完成评价。历史
`adjust/retranslate` 卡必须使用其 review-base 中文和具体人工证据；修订后的 adopted
中文作为另一个 packet，不继承原终态的 defect 标签。

必须记录：

- exact packet revision 和 identity 覆盖率；
- definite defect 的漏报和误报；
- 当前 severity 与绑定该 packet digest 的人工真值之间的冲突；
- context 不足比例；
- 输出结构失败；
- 人工复核时间。

**决策门：** 若没有可重复的实质缺口，选择 `Stop`，不新增基础设施。

### M1：确定性 packet 与分区

仅在 M0 证明手工 packet 不可稳定复现或容易泄漏答案时，才由 `crawl-coder` 在现有
审计入口旁增加最小只读适配器和定向测试。优先扩展现有脚本；新模块需要单独说明
现有入口为何不足。

**完成条件：** 相同输入逐字节生成相同 manifest、分区和 packet；identity 守恒；
无绝对路径；无规范资产写入；holdout 标签不出现在 evaluator bundle 中。

**执行结果：** 已通过。现有 item inventory 入口能够物化并自包含复验 11 个 artifact；
同一 16-case 边界、canonical truth、4 个 shard 和标签隔离均通过定向测试。详见
[M1 确定性物化报告](translation-quality-m1-report.md)。

### M2：事实优先 evaluator

在同一 calibration 集上并列运行当前自由定级基线与事实优先协议。调整只允许发生在
calibration；所有 prompt、规则、字段和 content hash 在 holdout 前冻结。

**完成条件：** 输出覆盖完整、逻辑校验严格、severity 可由事实确定性重算，且原始
输出与任何允许的确定性格式修复均保留独立摘要。

### M3：封存验证

在未见 holdout 上执行预登记次数的独立评价。正式运行前冻结：

- evaluator 配置与 prompt hash；
- packet、事实和映射规则；
- 样本 identity 与桶；
- 最大重试次数；
- 指标与决策阈值。

**完成条件：** 报告全部预登记指标，不挑选最佳 attempt，不用 holdout 结果继续调参。

### M4：人工裁决与 Go/No-Go

人工先判断问题是否存在和事实是否成立，再重新应用规则；不根据 evaluator 身份投票。
只有实际观察到两个 evaluator 对同一问题拆分不同，才增加匿名 issue matching；否则
保留逐 item 的简单裁决。

允许的结论：

1. `Stop`：当前流程已足够，删除实验 artifact；
2. `Packet-only`：bounded packet 改善上下文，但事实协议没有净收益；
3. `Facts-with-human-adjudication`：问题发现可靠，但关键事实仍需人工；
4. `Go`：事实协议在 holdout 上改善缺陷发现或定级稳定性，申请正式 contract；
5. `No-Go`：共同漏报、上下文缺口或人工成本不可接受。

任何 `Go` 都只授权下一份实施计划，不自动授权修改 schema-v4 review 或 final gate。

## 十一、指标

首轮必须同时报告原始计数和比例：

- packet、identity 和 item 覆盖完整性；
- definite defect 的 precision、recall 和混淆矩阵；
- 两种协议对人工确认 `needs_fix` 的共同漏报数；
- `suggestion` 被错误升级为 defect 的数量；
- context sufficient 一致率和 `unknown` 比例；
- 事实字段逐项一致率；
- severity 映射一致率；
- 输出解析/校验失败率；
- 需要人工裁决的 item 与 finding 比例；
- 每个协议的人工复核时间；
- representative、risk-enriched 和 contrast 分桶结果。

若使用两个 evaluator，另一 evaluator 不是人工真值。precision/recall 只能在匿名人工
裁决后计算；裁决前只报告双方交集、并集和分歧。

具体阈值在 M3 前根据 population 和样本量预登记，不在本设计草案中写死。无足够
confirmed defect 时必须报告证据不足，不能用高比例宣称方法稳定。

## 十二、测试与验证

### 12.1 身份与分区

- 相同输入产生相同 population、分区和 packet digest；
- identity 重复、缺失或出现双向差集时失败；
- glossary、decisions、inventory 或 packet 内容改变使评价身份变化；
- 只改变运行路径和时间戳不改变内容身份；
- dependency/contrast group 不跨集合；
- exploratory、calibration 和 holdout 两两互斥；
- 不可满足的覆盖约束显式失败或产生结构化警告。

### 12.2 packet 边界

- bundle 不含终态、预期 severity、另一 evaluator 结果或修复方案；
- 只包含仓库相对路径；
- 无主机名、用户名、凭据或 clone-specific 路径；
- 格式 token、换行和占位符按原字节保留；
- 相关 glossary/decision 引用可追踪且完整 glossary digest 仍存在；
- 生成过程不修改 tracked 文件或 `.claude/metrics/verify/`。

### 12.3 evaluator 与映射

- 覆盖不完整、重复 identity、未知字段和非法枚举失败；
- quote 唯一、重复、缺失、漏译和越界情况均有定向测试；
- 每个逻辑冲突都有负向测试；
- 相同 facts 必定派生相同当前 severity；
- `unknown` 不会静默降为 `suggestion` 或 clean；
- 模型技术判断不能在无确定性证据时派生 `blocker`；
- 实验结果不能生成正式 readiness 或 final Go。

### 12.4 仓库验证

纯文档设计阶段运行：

```bash
git diff --check
python3 .claude/scripts/check_path_portability.py
```

未来若修改 packet builder、validator 或 scanner，由 `crawl-coder` 按
`.agents/policies/verification-authoring.md` 增加正反测试，并运行单个匹配的
`.claude/scripts/verify_zh.sh --profile code`。不得串行运行全部开发 profile。

## 十三、所有权、安全和回滚

- 质量实验由 orchestrator 冻结 population、分区、运行配置和验收标准；
- packet builder、schema validator 或规则映射属于 `crawl-coder`；
- 中文语义真值、术语、完整性、自然度和人物口吻由 `translation-reviewer` 裁决；
- 运行、协议、格式和结构事实由现有门禁及 `zh-code-reviewer` 确认；
- 试点不写中文资产，因此不分配 `zh-translator` 写入任务；
- evaluator 默认无工具、无会话、无仓库访问，只读取 bounded packet；
- 外部 provider 调用必须由用户单独授权 provider、model、数据类型和条目范围；
- 缓存命中不得伪装成一次新的独立评价；
- 失败、重试和确定性格式修复保留原始字节及摘要，不挑选最符合预期的输出；
- 任一阶段可通过删除对应 `.artifacts/i18n/quality/<run-id>/` 回滚，不触碰规范数据；
- 旧实验结果永远是非授权指标，不迁移、升级或复制成 schema-v4 readiness。

## 十四、设计完成标准

本设计可以进入 M0 的前提是：

- 用户确认首轮只评测 evaluator，不建设 TM 或全语料质量等级；
- 选择一个已有完整 inventory 和证据卡的试点分类；
- 明确哪些历史案例属于 exploratory，不能进入 holdout；
- 冻结 M0 的最小样本、人工真值来源和成功/停止条件；
- 不需要修改现有翻译资产、glossary、decisions、review contract 或 final gate；
- 外部调用若存在，已取得独立授权；
- 本文档通过 diff 和路径可移植性检查。

M0 结束后必须先提交必要性报告，再决定是否实施 M1。不得因迁移方案已经存在而默认
继续建设工具。
