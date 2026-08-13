# Issue #40 收口工作计划（2026-08-13）

来源：2026-08-13 对 `5f168f7b..028f4993`（62 提交、15 个已关闭子 Issue）的整体 review。
review 结论：当前基线功能/翻译/集成测试健康，无运行时或翻译 Blocker；但 #40 关闭条件未满足，
且存在 2 项 needs_fix 与若干验证缺口。本文档是逐项执行清单，避免后续处理遗漏。

整体 review 报告要点：
- Needs Fix：N1 增量 AST scanner 对 directn.cc fail-closed 不一致；N2 #64/#67 关闭记录边界不精确。
- 验证缺口：V1 #54/#56/#59 历史 bundle 不在本地证据库；V2 无 62-commit 范围的新 immutable bundle；V3 #40 路线空白（R0 映射缺失、R4 剩 monspeak/insult/shout、R5 未做、R6 未使用、monspell defer 未单列跟踪）。
- 建议：P3 共享 primitive 抽取（非阻塞，不重写现有工具）。

## 工作项清单

| ID | 优先级 | 项目 | 验收标准 | 依赖 | 状态 |
|---|---|---|---|---|---|
| W1 | P1 | 增量 AST scanner changed/full 一致性修复（`scan_varargs_string.py` / `scan_string_concat.py` 对 `directn.cc:626` 预处理分支的 pre-existing parse 错误） | changed-scope 与 full-root 对 directn.cc 结果一致；窄化识别 + 回归测试；code profile 全绿 | 无 | 进行中 |
| W2 | P1 | Issue 关闭记录更正：#64（approved bundle candidate=`2038fabd`，style 提交 `2132cd99` 为后续）、#67（`306d9099..028f4993` 实际 12 commits 非 8）、#54/#56（补 PR #55/#58 证据链接） | 各 Issue 有更正评论，记录精确边界；不制造追溯性 Go | 无 | ✅ 完成（2026-08-13，评论 5287523273/5287524354/5287525276/5287526285） |
| W3 | P2 | monspell symbolic-state defer 单独建单跟踪（`vanquished vanguard nergalle cast`，分析器上限） | 建 Issue，含 reentry trigger；台账引用该 Issue | 无 | 待办 |
| W4 | P2 | R4 `shout`/`insult` 家族全量校对（共享 ShoutDB provenance 边界） | 子 Issue + inventory + 逐身份审核 + 机械路由 + schema-v4 Final Gate | 先冻结 ShoutDB 共享加载边界 | 待办 |
| W5 | P2 | R4 `monspeak` 家族全量校对（最大语料） | 同上 | W4 的 provenance 模式可复用 | 待办 |
| W6 | P2 | R0 覆盖映射（全部 TextDB 家族唯一审核归属、排除项、重入条件） | 文档化映射；每个家族有归属或明确排除依据 | 无 | 待办 |
| W7 | P2 | R5 `quotes` 引文全量校对 | 子 Issue + 复用 #3 与怪物/法术专名证据 | W6 | 待办 |
| W8 | P2 | R6 增量维护入口实际使用并记录证据 | 一次真实 inventory 重生成/失效复核记录 | W4-W7 完成后 | 待办 |
| W9 | P2 | #40 关闭（R0 完成 + R1-R5 子 Issue 全关 + R6 已用） | 满足 #40 完成条件；关闭评论记录全部证据 | W1-W8 | 待办 |
| W10 | P3 | 共享 primitive 抽取（exact-Git manifest / safe output / JSONL 绑定） | 仅抽取至少两家工具验证过的 primitive；不重写现有工具 | 新批开始时评估 | 可选 |

## 执行顺序说明

- W2（纯记录更正，无代码）→ W1（scanner 修复，代码）→ W3（建单）→ W4/W5（完整批次，各含
  tooling + 翻译 + 评审 + final gate）→ W6（R0 映射文档）→ W7（quotes 批次）→ W8 → W9。
- 每项完成后在本表更新状态并记录证据位置；跨会话 handoff 写入对应 GitHub Issue 评论。
- 本表不复制 GitHub Issue 的 Open/Closed 状态细节，只维护本计划内的执行进度。
