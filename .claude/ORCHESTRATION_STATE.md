# 编排约束 — DCSS 汉化项目

本文件只保存跨 Issue、跨运行时都必须遵守的编排约束。它不是对话日志、
Issue 索引、当前任务面板、提交清单或验证输出目录。

## 信息边界

- 问题、当前状态、验收标准、负责人和跨会话交接：
  `yutio8888/crawl-chn-ai-test` GitHub Issues。
- 实现、精确提交范围、代码审查与 CI 证据：关联 Pull Request。
- 长期术语和架构决策：`docs/glossary.md`、`docs/decisions.md` 与架构文档。
- 验证日志：`.claude/metrics/verify/`。
- 2026-07-21 之前的 Issue 分析、计划和评审：只读归档
  <https://github.com/yutio8888/crawl-chn-issues-archive>。

不得在本文件复制 GitHub Issue 的 Open/Closed 状态、优先级、待办列表、
实现进度或评审结论。需要跨会话继续的具体任务，应把分支、commit、已完成验证
和剩余工作评论到同一个 GitHub Issue。

## 跨 Issue 编排约束

1. 中文翻译资产在一个任务中只有一个 writer；混合任务先完成翻译资产，再处理代码。
2. 工作树只能创建在仓库内的 `.worktrees/<name>`。
3. 翻译或 i18n 工作在派发、编辑或审查前运行当前 worktree 的
   `.claude/scripts/context_resolve.sh`；术语以 `docs/glossary.md` 为唯一来源。
4. 协议/显示边界、格式参数、TextDB 结构和所有权规则以 `.agents/policies/` 为准，
   不在此复制具体规则清单。
5. 评审对象是干净提交的候选 commit，由 `classify_reviewers.py` 路由；合并条件
   是匹配的验证 profile、领域审阅与 GitHub CI。
6. 运行匹配改动类型的单一验证 profile，避免对同一候选串行运行所有 profile。

## Issue 追踪切换决策

- GitHub Issues 是问题状态的唯一来源；自动化命令显式使用
  `--repo yutio8888/crawl-chn-ai-test`。
- 旧 Issue 仓库已冻结并设置为 GitHub Archived，不再接收编号、状态更新或交接。
- 只迁移仍有行动价值的历史 Issue；稳定的 Legacy ID 映射记录在
  `docs/issue-tracking.md`，该映射不复制状态。
- 旧仓库脚本不得直接恢复为运行依赖；如确需其中能力，应将最小行为移入主仓库
  的现有受测工具。
