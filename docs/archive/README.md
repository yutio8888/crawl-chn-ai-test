# 历史文档归档

本目录仅供只读参考，不授予实施、审查、合并或继续实验的权限。没有脚本将本目录文档作为
生产输入读取；文档链接检查仍覆盖此目录。进度与授权以原 Issue/PR 为准，当前规范见
[项目文档索引](../README.md)。

## 翻译质量实验

原始用途是评估物品说明审核流程的缺口，并在既有工具中验证确定性实验输入。

- [迁移计划](translation-quality-2026/translation-quality-migration-plan.md)：实验阶段、边界与停止条件。
- [M0 报告](translation-quality-2026/translation-quality-m0-report.md)：必要性基线、盲评与裁决证据。
- [M1 报告](translation-quality-2026/translation-quality-m1-report.md)：确定性 packet/truth 物化与分片验证。

工具实现仍在 `audit_item_name_inventory.py`；历史材料不授予后续阶段授权。

## Android UI 审计

[审计报告](android-ui-audit-2026-09-22/report.md) 记录当时的源码基线、模拟器观察、
优化建议与未覆盖项；[证据目录](android-ui-audit-2026-09-22/evidence/) 保存截图、
UI 层级与文本记录。后续实施与验收以报告所链接的 PR 为准。

## 上游 issue 分析与修复（2026-11）

[crawl/crawl 近期 issue 分析与修复报告](upstream-issue-triage-2026-11/report.md) 汇总
2026-08-09 之后 44 个上游 open issue 的结论、13 个本地修复提交与验证；
[完整 triage 表](upstream-issue-triage-2026-11/triage.md) 保存逐项证据、批次与引用。
历史材料不授予后续实施或合并权限。

## 译文抽样、术语裁定与消费点冻结（2026-11）

保留抽样评审、跨版本术语回查以及修复前冻结的消费点快照：

- [匿名 A/B 译文质量抽样评审（2026-11-12）](translation-ab-review-2026-11-12/README.md)
- [第 2 轮译文抽样检查（2026-11-12）](translation-sample-review-r2-2026-11-12/README.md)
- [第 3 轮玩家行动与反馈句式审查（2026-11-12）](player-action-review-r3-2026-11-12/README.md)
- [第 4 轮分层译文抽样检查（2026-11-12）](translation-sample-review-r4-2026-11-12/README.md)
- [D-C-096 适用性回查（2026-11-12）](dc096-anchoring-review-2026-11-12/README.md)
- [第 11 轮术语消费点冻结清单（2026-11-13）](r11-terminology-2026-11-13/consumers.json)
- [第 16 轮 Vertigo/Dazed 消费点冻结清单（2026-11-13）](r16-vertigo-2026-11-13/consumers.json)
- [torpor snail 命名与显示消费点冻结清单（2026-11-14）](torpor-snail-2026-11-14/consumers.json)
- [第 51 轮 hellion 等术语消费点冻结清单（2026-11-15）](r51-hellion-2026-11-15/consumers.json)
- [固定神器名称语序调整与消费点（2026-11-15）](unrand-name-order-2026-11-15/README.md)

## trunk 预发布门禁归档

记录各 trunk 预发布版本的提交基线、标签 CI、资产哈希、`RELEASE-MANIFEST.txt`、
APK 身份校验与玩家公告副本（安装包本身不入库）：

- [0.35-trunk-010（2026-11-11）](release-0.35-trunk-010-2026-11-11/README.md)
- [0.35-trunk-011（2026-11-13）](release-0.35-trunk-011-2026-11-13/README.md)
- [0.35-trunk-012（2026-11-15）](release-0.35-trunk-012-2026-11-15/README.md)
- [0.35-trunk-013（2026-11-18）](release-0.35-trunk-013-2026-11-18/README.md)
- [0.35-trunk-014（2026-11-20）](release-0.35-trunk-014-2026-11-20/README.md)
