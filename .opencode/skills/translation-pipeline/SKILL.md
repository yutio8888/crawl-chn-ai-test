---
name: translation-pipeline
description: 翻译问题完整修复管道 — 玩家反馈 → 结构化收集 → 分析 → 方案 → 审查 → 执行 → 审核 → 交叉验证 → 合入
---

# Translation Fix Pipeline

<!-- BEGIN GENERATED: asset-ownership -->
# asset-ownership-v1

Every task assigns exactly one writer to every file. Agents are not alone in
the repository: preserve existing changes, do not revert work owned by another
writer, and coordinate before touching an overlapping path.

## Default ownership

- `zh-translator` owns Chinese wording and translation assets under
  `crawl-ref/source/dat/i18n/zh/`, `crawl-ref/source/dat/database/zh/`, and
  `crawl-ref/source/dat/descript/zh/`.
- `crawl-coder` owns C++, headers, Lua integration, build files, parsers,
  database loading/schema, and code-side `T_()`/`C_()` migration.
- English/protocol/TextDB lookup keys remain English regardless of the writer.
- Reviewers are read-only and never repair findings during the readiness pass.

## Structural exception

A coder may edit an explicitly listed ZH data file for a purely structural or
mechanical repair, such as a broken delimiter or loader-compatible key, only
when the orchestrator assigns that complete path to the coder and no translator
is writing it concurrently. The coder must not make independent wording or
terminology decisions under this exception.

## Mixed tasks

For a task that needs both translated assets and source changes:

1. resolve the current glossary context;
2. assign every ZH translation asset to one translator writer;
3. complete translation-asset edits first;
4. run the coder for source/build changes without reopening translator-owned
   files;
5. verify the combined worktree and review the exact committed diff.

Batch work uses the same ownership model. Parallel analysis is allowed, but
translation assets are written sequentially by their single owner.
<!-- END GENERATED: asset-ownership -->

当用户报告翻译问题（未翻译文本、翻译错误、翻译 bug）时，按以下流程处理。

## Trigger

| 触发词 | 示例 |
|--------|------|
| 未翻译 / 显示英文 | "这里没翻译", "XX还是英文" |
| 翻译错误 | "翻译错了", "这个翻译不对" |
| 翻译 bug | "翻译bug", "translation bug" |
| 玩家/测试反馈 | "玩家反馈说...", "测试发现..." |

## Intake: 结构化信息收集

用户报告问题时，确保收集到以下信息（缺失的主动询问）：

1. **确切文本**: 游戏中出现的英文原文是什么？（截图最佳）
2. **出现位置**: 游戏内哪里？（日志、物品栏、怪物名、描述、菜单等）
3. **触发场景**: 文本出现时正在做什么？
4. **期望结果**: 应该显示什么中文？（可选）

## 创建 Issue 跟踪文件

在 `${DCSS_ISSUES_DIR:-../issues}/` 下创建 issue 文件；该相对默认值以仓库
根目录为基准，可通过 `DCSS_ISSUES_DIR` 指向其他位置：

```markdown
# Issue <N>: <简述>
- **日期**: YYYY-MM-DD
- **状态**: Analyzing
- **来源**: <玩家反馈/自查>
- **原文**: <EN text>
- **位置**: <game location>
```

## 启动修复流程

进入分析阶段前，必须从当前 worktree 生成术语上下文：

```bash
bash .claude/scripts/context_resolve.sh "<issue/task>" \
  --task-type translate --files <target-files>
```

将完整输出传给分析、翻译和审核 Agent，并在最终报告中记录其中的
`docs/glossary.md` SHA-256。执行期间若术语表发生变化，重新生成上下文；
不得用工作流或 Skill 内的静态术语副本覆盖当前术语表。

`.opencode/workflows/*.js` 使用宿主注入的 `args`、`agent()`、`phase()` 等
DSL，不是普通 Node.js 程序，**不得**用 `node file.js` 直接执行。只有当前
OpenCode 宿主明确提供兼容 workflow runner 时，才通过该 runner 启动。

## 审核 Agent 自动路由

Hosted workflow 与无 runner fallback 必须共享
`.claude/scripts/classify_reviewers.py` 的机器判定，不得各自维护路径规则。
计划阶段可按目标文件运行分类器作成本预估，但该结果不是 readiness 路由。
执行者必须先完成开发期 profile、只提交自己拥有的文件并留下 clean
worktree。随后从 clean target checkout 运行：

```bash
bash .claude/scripts/review_prepare.sh <candidate-branch> <target-branch>
```

该命令绑定精确 target/candidate OID、真实 glossary SHA-256 与 binary diff，
创建 shared-common-dir bundle；其 `routing` 字段才是唯一审核路由依据。
尚未形成提交范围时可使用以下命令预估 reviewer，但不得据此写 readiness：

```bash
REVIEW_ROUTING=$(python3 .claude/scripts/classify_reviewers.py \
  --files <file-1> <file-2> ...)
```

分类器输出的 `reviewers` 是唯一审核路由依据：

- 纯代码、脚本或工作流/策略基础设施：仅 `zh-code-reviewer`
- 纯 ZH 翻译文本或术语治理文本：仅 `translation-reviewer`
- 混合变更：两者都运行
- 空 diff：不派发 reviewer，继续机械交叉验证
- `crawl-ref/source/` 下未识别文件：fail-safe 派发 `zh-code-reviewer`

Hosted runner 必须给 single/batch workflow 传入 `args.targetRoot`、
`args.targetBranch` 和 `args.candidateBranch`。workflow 在 Execute 后调用
`review_prepare.sh`，直接消费新 bundle 的完整 `routing`；缺少参数、工作树
未提交/不干净或边界创建失败时以 `review_boundary_required` 停止，不能审查
旧 routing，也不能静默固定双审或跳过审核。

运行时没有 workflow runner 时，使用 `task` 逐阶段回退：

```
task(subagent_type="general", description="Analyze issue",
  prompt="Analyze this DCSS Chinese translation issue to find the root cause...")
```

阶段：分析 → 方案 → 方案审核 → 翻译资产修改 → 代码修改 → 提交/Bundle
边界 → 路由审核 → 交叉验证 → readiness 持久化 → 单次 final gate → 报告。

fallback 同样先运行 `review_prepare.sh`，解析 bundle 的 `routing`，并且只对
`reviewers` 数组中列出的类型调用 `task`。不得从 issue 类型、自然语言描述
或 Agent 自报的修改内容另行猜测审核人。术语一致性机械检查和交叉验证不受
reviewer 数量影响，始终执行。reviewer 只检查已提交、干净 worktree 的精确
bundle diff 和开发期日志，输出 `Ready for Final Gate`、`Changes Requested`
或 `No-Go`；不得运行 `--profile review`。

执行阶段必须保持单一写入者：`zh-translator` 独占 `source.txt` 及其他
`zh/*.txt`/TextDB 文件，`crawl-coder` 只修改代码；两者不得并行写翻译资产。

交叉验证通过且所有路由 reviewer 都 Ready 后，orchestrator 先使用 target
checkout 的 `review_bundle.py record-readiness` 写入每个角色的精确计数，再且
仅再运行一次 `review_final_gate.sh <candidate> <target>`。失败或中断不得自动
重试；该命令持有 bundle 锁并生成 head-bound verification 与最终批准，
`review_at_merge.sh` 只读验证现有证据。

## 结果汇报

完成后向用户报告：
- 修改了哪些文件
- 翻译了什么内容（EN → ZH）
- 使用的术语表 SHA-256
- readiness（Ready for Final Gate / Changes Requested / No-Go）
- final gate / merge gate 状态
- 合入状态
