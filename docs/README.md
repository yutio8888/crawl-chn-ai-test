# 文档索引

`docs/` 只保存当前架构、流程、术语和仍被工具或权威文档引用的审核证据。问题、进度和
验收状态以 [GitHub Issues](https://github.com/yutio8888/crawl-chn-ai-test/issues) 为准，
实现与审查证据记录在对应 Pull Request。跨 runtime 的入口和规范来源表见仓库根目录的
`AGENTS.md` 与 `.agents/README.md`。

## 协作与流程

| 文档 | 内容 |
|---|---|
| [agent-routing.md](agent-routing.md) | 角色与任务路由 |
| [dual-agent-workflow.md](dual-agent-workflow.md) | 跨 runtime 协作与交接 |
| [issue-tracking.md](issue-tracking.md) | GitHub Issue 使用方式与旧 issue 仓库归档 |
| [build-workflow.md](build-workflow.md) | 控制台、Windows Tiles、macOS、Android 构建与部署 |
| [zh-testing.md](zh-testing.md) | 验证 profile、运行时证据、领域审查与合并 |
| [release-workflow.md](release-workflow.md) | 正式版标签、平台范围与发布门禁 |

脚本级用法和退出码见 `.claude/scripts/TOOLCHAIN.md`。

## 架构

| 文档 | 内容 |
|---|---|
| [translation-architecture.md](translation-architecture.md) | 翻译数据流、协议值与显示文本边界 |
| [textdb-i18n-architecture.md](textdb-i18n-architecture.md) | TextDB 消息 overlay 与年度上游升级流程 |
| [cjk-tiles-architecture.md](cjk-tiles-architecture.md) | CJK 网格宽度、字体渲染与 Windows 编码 |
| [android-architecture.md](android-architecture.md) | Android 触控输入、键盘、抽屉、生命周期与设备验证 |

## 术语与命名

| 文档 | 内容 |
|---|---|
| [glossary.md](glossary.md) | 唯一当前术语来源；`glossary.utf8` 是由它导出的 OmegaT 词表 |
| [decisions.md](decisions.md) | 术语与命名裁定及理由 |
| [spell-naming-rules.md](spell-naming-rules.md) | 法术名通用命名原则与强度审查标准 |
| [design-item-naming.md](design-item-naming.md) | 物品命名的历史设计记录，被 `decisions.md` 引用；现行规则以裁定为准 |

## 翻译审核台账

- `*-review-results.md`：各文本域全量审核的冻结台账，多数由对应 inventory 脚本和测试读取；
  修改它们按混合改动路由审查。
- [textdb-coverage-map.md](textdb-coverage-map.md)：TextDB 家族到审核台账的索引与重审条件。
- 保留的 `*-review-plan.md` 只限仍被引用的计划：`guide-review-plan.md` 由
  `guide_inventory.py` 生成并校验；`help`、`monspell` 计划被测试或脚本注释引用；
  `monster` 计划被 `decisions.md` 引用；`spell-name` 计划定义了其台账的结论标签。

新的全量审核按 `.agents/skills/batch-translation-review/SKILL.md` 执行。

## 待决与历史记录

| 文档 | 状态 |
|---|---|
| [issue120-scanner-preproc-report.md](issue120-scanner-preproc-report.md) | Issue #120（扫描器完整预处理）的探针与已实施的方案 2；后续状态见该 Issue |
| [translation-quality-migration-plan.md](translation-quality-migration-plan.md) 及 M0/M1 报告 | 翻译质量评审实验；M1 工具仍在 `audit_item_name_inventory.py` 中，M2 未获授权 |
| [review-recovery-history.md](review-recovery-history.md) | 已退役审查控制面的只读归档，不授予任何合并权限 |

`fonts/` 存放随仓库分发字体的许可证副本。

## 维护规则

- 已完成的计划、验证记录和一次性调查不留在 `docs/`：结论写回对应 Issue/PR，仍然有效的
  约束并入上面的权威文档。
- 不在文档中写死测试数、条目数、分支列表或模型名；以脚本 `--help`、配置和 Git 状态为准。
- 已删除文档可从 Git 历史取回，例如
  `git log --diff-filter=D --name-only -- docs/` 找到删除提交后用
  `git show <commit>^:docs/<file>` 查看。
