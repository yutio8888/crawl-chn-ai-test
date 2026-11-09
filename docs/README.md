# 文档生命周期索引

## 收录边界与生命周期

`docs/` 收录本项目的架构、流程、术语参考、审核输入与证据，以及明确归档的历史材料；
上游游戏文档位于 `crawl-ref/docs/`，不属于本索引的维护范围。本页是项目文档的唯一综合导航。

| 生命周期 | 含义 |
|---|---|
| canonical | 当前规范或权威参考，修改时同步其消费者 |
| active | 持续维护的映射或工作参考，实际进度以 Issue/PR 为准 |
| frozen-input | 保留给特定审核、裁定或工具的冻结输入，不自动成为现行规范 |
| historical | 历史材料，只读参考，不授予实施、审查或合并权限 |
| evidence | 绑定特定输入与验证边界的审核证据；输入漂移时按重入条件复核 |

问题、进度、授权和验收状态以 [GitHub Issues](https://github.com/yutio8888/crawl-chn-ai-test/issues)
及对应 Pull Request 为权威；文档中的历史状态不替代这些记录。

## 治理入口

共享入口为 [AGENTS.md](../AGENTS.md)、[配置权威映射](../.agents/README.md)
和 [共享策略目录](../.agents/policies/)。本索引只链接入口，不复制策略正文。

| Runtime | Adapter |
|---|---|
| Pi | [.pi/APPEND_SYSTEM.md](../.pi/APPEND_SYSTEM.md) |
| Codex | [CODEX.md](../CODEX.md) |
| DSH（实验性） | [DSH.md](../DSH.md) |

## 流程（canonical）

| 文档 | 用途 |
|---|---|
| [agent-routing.md](agent-routing.md) | 角色与任务路由 |
| [dual-agent-workflow.md](dual-agent-workflow.md) | 跨 runtime 协作与交接 |
| [issue-tracking.md](issue-tracking.md) | Issue、PR 与跨会话记录 |
| [build-workflow.md](build-workflow.md) | 构建与部署 |
| [zh-testing.md](zh-testing.md) | 验证 profile、运行时证据与领域审查 |
| [release-workflow.md](release-workflow.md) | 发布流程与门禁 |

脚本用法参考 [TOOLCHAIN.md](../.claude/scripts/TOOLCHAIN.md)，可用参数以脚本当前
`--help` 输出为准。

## 架构（canonical）

| 文档 | 用途 |
|---|---|
| [translation-architecture.md](translation-architecture.md) | 翻译数据流与协议/显示边界 |
| [textdb-i18n-architecture.md](textdb-i18n-architecture.md) | TextDB 消息 overlay 与上游升级 |
| [cjk-tiles-architecture.md](cjk-tiles-architecture.md) | CJK 网格、字体渲染与编码 |
| [android-architecture.md](android-architecture.md) | Android 触控、键盘、抽屉与设备验证 |

## 术语与命名参考

| 文档 | 生命周期与用途 |
|---|---|
| [glossary.md](glossary.md) | canonical：当前术语来源 |
| [glossary.utf8](glossary.utf8) | canonical：从术语表导出的 OmegaT 词表 |
| [decisions.md](decisions.md) | canonical：术语与命名裁定及理由 |
| [spell-naming-rules.md](spell-naming-rules.md) | canonical：法术命名原则与强度审查标准 |
| [design-item-naming.md](design-item-naming.md) | frozen-input：裁定引用的历史设计输入，现行规则以裁定为准 |

术语判断前从当前工作树运行 `bash .claude/scripts/context_resolve.sh "<task>" --task-type <translate|code|review> --files <target-files>`。
翻译质量流程实验已移入 [历史归档](archive/translation-quality-2026/translation-quality-migration-plan.md)，不改变现行术语权威。

## 翻译审核台账（evidence）

台账必须直属 `docs/`，禁止进入子目录；`classify_reviewers.py` 与 `verify_zh.sh`
依赖此约定。下表列出现有 inventory/audit 入口；工具检查身份和结构，不能替代逐项语义审查。
工具路径均相对仓库根目录的 `.claude/scripts/`。

| 台账 | 对应工具 |
|---|---|
| [card-review-results.md](card-review-results.md) | [card_inventory.py](../.claude/scripts/card_inventory.py) |
| [character-mechanics-review-results.md](character-mechanics-review-results.md) | [audit_character_mechanics_inventory.py](../.claude/scripts/audit_character_mechanics_inventory.py) |
| [cloud-review-results.md](cloud-review-results.md) | [cloud_inventory.py](../.claude/scripts/cloud_inventory.py) |
| [command-review-results.md](command-review-results.md) | [command_inventory.py](../.claude/scripts/command_inventory.py) |
| [decorlines-review-results.md](decorlines-review-results.md) | [decorlines_inventory.py](../.claude/scripts/decorlines_inventory.py) |
| [frontend-review-results.md](frontend-review-results.md) | 无独立 inventory/audit 脚本；冻结来源清单与逐项覆盖证据见台账 |
| [god-review-results.md](god-review-results.md) | [audit_god_inventory.py](../.claude/scripts/audit_god_inventory.py) |
| [graffiti-review-results.md](graffiti-review-results.md) | [graffiti_inventory.py](../.claude/scripts/graffiti_inventory.py) |
| [guide-review-results.md](guide-review-results.md) | [guide_inventory.py](../.claude/scripts/guide_inventory.py) |
| [help-review-results.md](help-review-results.md) | [help_inventory.py](../.claude/scripts/help_inventory.py) |
| [hint-review-results.md](hint-review-results.md) | [hint_inventory.py](../.claude/scripts/hint_inventory.py) |
| [item-extended-review-results.md](item-extended-review-results.md) | [audit_item_name_inventory.py](../.claude/scripts/audit_item_name_inventory.py) |
| [miscast-review-results.md](miscast-review-results.md) | [miscast_inventory.py](../.claude/scripts/miscast_inventory.py) |
| [miscname-review-results.md](miscname-review-results.md) | [miscname_inventory.py](../.claude/scripts/miscname_inventory.py) |
| [monflee-review-results.md](monflee-review-results.md) | [monflee_inventory.py](../.claude/scripts/monflee_inventory.py) |
| [monspeak-review-results.md](monspeak-review-results.md) | [monspeak_inventory.py](../.claude/scripts/monspeak_inventory.py) |
| [monspell-review-results.md](monspell-review-results.md) | [monspell_inventory.py](../.claude/scripts/monspell_inventory.py) |
| [monster-review-results.md](monster-review-results.md) | [monster_name_ssot.py](../.claude/scripts/monster_name_ssot.py) |
| [quotes-review-results.md](quotes-review-results.md) | [quotes_inventory.py](../.claude/scripts/quotes_inventory.py) |
| [shout-review-results.md](shout-review-results.md) | [shout_inventory.py](../.claude/scripts/shout_inventory.py) |
| [source-review-results.md](source-review-results.md) | 无独立 inventory 脚本；[scan_i18n.py](../.claude/scripts/scan_i18n.py) 的 SourceDB 检查提供结构审计 |
| [species-background-review-results.md](species-background-review-results.md) | [audit_species_background_inventory.py](../.claude/scripts/audit_species_background_inventory.py) |
| [spell-name-review-results.md](spell-name-review-results.md) | [migrate_spell_titles.py](../.claude/scripts/migrate_spell_titles.py) |
| [tutorial-review-results.md](tutorial-review-results.md) | [tutorial_inventory.py](../.claude/scripts/tutorial_inventory.py) |
| [world-review-results.md](world-review-results.md) | [audit_world_inventory.py](../.claude/scripts/audit_world_inventory.py) |
| [wpnnoise-review-results.md](wpnnoise-review-results.md) | [wpnnoise_inventory.py](../.claude/scripts/wpnnoise_inventory.py) |

[textdb-coverage-map.md](textdb-coverage-map.md) 为 active：维护 TextDB 家族、台账归属与重入条件。
新的全量审核使用 [batch-translation-review Skill](../.agents/skills/batch-translation-review/SKILL.md)。

## 审核计划与冻结输入（frozen-input）

这些材料保留已有消费者的输入边界；下表区分直接读取与设计/证据引用，避免把历史计划当作新授权。

| 文档 | 消费者与保留理由 |
|---|---|
| [guide-review-plan.md](guide-review-plan.md) | `guide_inventory.py:417,434` 读取、生成；`tests/test_guide_inventory.py` 校验 |
| [help-review-plan.md](help-review-plan.md) | `help_inventory.py` 及 `tests/test_help_inventory.py` 对应的 Help/FAQ 身份与消费者边界设计输入；不由测试直接读取 |
| [monspell-review-plan.md](monspell-review-plan.md) | `monspell_inventory.py:528` 注释引用 R4-MONSPELL-CODE-004-R3 |
| [monster-review-plan.md](monster-review-plan.md) | `decisions.md` 裁定 D-C-092 的证据输入 |
| [spell-name-review-plan.md](spell-name-review-plan.md) | `spell-name-review-results.md` 的结论标签与验收边界；`migrate_spell_titles.py inventory` 提供清单 |
| [translation-full-rereview-plan.md](translation-full-rereview-plan.md) | `audit_world_inventory.py:2617` 生成的验证说明引用其批次边界 |
| [issue120-scanner-preproc-report.md](issue120-scanner-preproc-report.md) | Issue #120 方案裁定与探针证据；`tests/test_preprocessor_patterns.py`、`tests/test_scanner_completeness.py` 对应实现边界的回归参考，不直接读取报告 |

## 历史归档（historical / evidence）

[archive/README.md](archive/README.md) 列出翻译质量实验和 Android UI 审计的原始用途。
归档保留当时的结论与证据边界，不作为当前实施授权。

[review-recovery-history.md](review-recovery-history.md) 是已退役审查控制面的只读历史。
其路径受 `test_agent_docs.py` 保护，原位保留，不授予合并权限。

## 字体许可证

| 文件 | 用途 |
|---|---|
| [LICENSE-Maple-Mono.txt](fonts/LICENSE-Maple-Mono.txt) | 分发字体的许可证副本；`verify_release_artifacts.py` 将其作为 Windows/macOS 包内许可证的内容比对来源，路径固定 |
| [LICENSE-Sarasa-Gothic.txt](fonts/LICENSE-Sarasa-Gothic.txt) | 保留字体许可证参考；当前发布验证器未将其列作内容比对来源 |

## 维护规则

- 有工具、测试、裁定或现行文档消费者的材料应保留，变动时同步消费者。
- 无消费者的一次性材料应归档或删除，结论写回对应 Issue/PR。
- 不写死测试数、条目数、模型名或分支列表；以脚本、配置和 Git 状态为准。
- 新增文档必须进入本索引；历史组的明细由归档索引列出。
- 审核台账禁止进入子目录；机器绑定路径的调整必须同步工具和测试，本次保持原位。
- 扩展后的 `test_agent_docs.py` 检查整个 `docs/**/*.md` 的相对链接；移动文档时修正链接。
- 删除文档可用 `git log --diff-filter=D --name-only -- docs/` 找到删除提交，再用
  `git show <commit>^:docs/<file>` 取回；无需为修复历史引用恢复已删除文档。
