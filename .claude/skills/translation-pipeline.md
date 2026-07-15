---
name: translation-pipeline
description: 翻译问题完整修复管道 — 玩家反馈 → 结构化收集 → 分析 → 方案 → 审查 → 执行 → 审核 → 交叉验证 → 合入
---

# Translation Fix Pipeline

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

在 `~/projects/issues/` 下创建 issue 文件：

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

`.claude/workflows/*.js` 使用宿主注入的 `args`、`agent()`、`phase()` 等
DSL，不是普通 Node.js 程序，**不得**用 `node file.js` 直接执行。只有当前
Claude Code 运行时明确提供 workflow runner 时，才通过该 runner 启动。

## 审核 Agent 自动路由

Hosted workflow 与无 runner fallback 必须共享
`.claude/scripts/classify_reviewers.py` 的机器判定，不得各自维护路径规则。
执行前按不可变提交范围生成 JSON：

```bash
REVIEW_ROUTING=$(python3 .claude/scripts/classify_reviewers.py \
  --base <base-revision> --head <head-revision>)
```

尚未形成提交范围时，使用计划中所有目标文件（每个路径作为独立参数）：

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

Hosted runner 必须把解析后的完整 JSON 对象作为
`args.reviewRouting` 传给 single/batch workflow。workflow 缺少该字段时会以
`review_routing_required` 停止，不能静默固定双审或跳过审核。

运行时没有 workflow runner 时，使用 `Agent` 逐阶段回退：

```
Agent(subagent_type="general", description="Analyze issue",
  prompt="Analyze this DCSS Chinese translation issue to find the root cause...")
```

阶段：分析 → 方案 → 方案审核 → 翻译资产修改 → 代码修改 → 路由审核 → 交叉验证 → 报告。

fallback 在审核阶段解析同一个 `REVIEW_ROUTING` JSON，并且只对
`reviewers` 数组中列出的类型调用 `Agent`。不得从 issue 类型、自然语言描述
或 Agent 自报的修改内容另行猜测审核人。术语一致性机械检查和交叉验证不受
reviewer 数量影响，始终执行。

执行阶段必须保持单一写入者：`zh-translator` 独占 `source.txt` 及其他
`zh/*.txt`/TextDB 文件，`crawl-coder` 只修改代码；两者不得并行写翻译资产。

## 结果汇报

完成后向用户报告：
- 修改了哪些文件
- 翻译了什么内容（EN → ZH）
- 使用的术语表 SHA-256
- 审核结论（Go / Conditional Go / No-Go）
- 合入状态
