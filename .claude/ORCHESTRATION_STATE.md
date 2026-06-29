---
updated: 2026-06-30T00:10:00+08:00
last_commit: ff18ebd4115b
session_id: 00000000-0000-0000-0000-000000000000
---

# 编排者状态 — DCSS 汉化项目

> 编排者（人类 + Claude）的决策与约束外部存储器。
> **不是对话日志**——只记录决策、约束、待决事项。
> 每次做决策、调度 Agent、或评估 review 结果后，必须更新此文件。
>
> 职责边界：
> - 不存 issue 状态 → `~/projects/issues/INDEX.md`
> - 不存翻译决策 → `docs/decisions.md`
> - 不存脚本输出 → `.claude/metrics/verify/`
> - **只存**：为什么做决策、跨 issue 约束、编排者在忙什么

---

## 一、当前决策栈（最近优先）

### D-20260630-001: Phase A 架构优化基础设施
- **决策**: 实施 check_consistency.sh --strict、ORCHESTRATION_STATE.md、check_checkpoint.sh、record_review.sh、post-*.sh 聚合脚本
- **为什么**: 建立"Agent 生成 / 脚本验证 / 编排者判断"三层架构的基础设施
- **状态**: `executing` — 在 worktree phase-a-checkpoint 中实施
- **约束**: 验证逻辑不写在 prompt 里，全部活在 scripts/ 下

### D-20260629-008: Issue 26 equip_slot_name() — 显示 T_()，协议用英文
- **决策**: `equip_slot_name()` 写入存档用英文（protocol），显示时经 T_() 翻译
- **为什么**: `equip_slot_by_name()` 用 `strcasecmp` 做 Lua 槽位匹配
- **状态**: `approved_with_notes` — 已修复
- **约束**: 任何用于 `strcasecmp`/`find`/`lowercase` 匹配的返回值，需要 `_en()` 变体

### D-20260629-007: Issue 30 scan_i18n.py mprf-p — make_stringf_p 识别
- **决策**: `POSITIONAL_CALL_RE` 正则扩展以识别 `make_stringf_p`/`vmake_stringf_p`
- **状态**: `approved` — 已合入

### D-20260629-006: Issue 29 ARG-DIFF 架构 — conj_verb 延期
- **决策**: 17 条 arg-mismatch 中，16 条是单复数分离（conj_verb），延后处理
- **为什么**: conj_verb 移除是 P2 质量改进
- **状态**: `approved_with_notes` — beam.cc 仍待迁移

### D-20260629-005: Issue 31 存档中文化 — 写入英文，显示 T_()
- **决策**: 存档文件写入英文原名，显示时经 T_() 翻译；反向查找保留 deprecated 兼容路径
- **状态**: `analyzed` — 方案已定，待执行

### D-20260629-004: Issue 27 ARG-DIFF — source.txt 3 条目需 C++ 重构
- **决策**: 3 个条目涉及格式串参数调整，需改 C++ 调用侧代码
- **状态**: `analyzed` — 待执行

### D-20260627-003: Issue 14 翻译同步架构 — DECISIONS.md SSOT
- **决策**: 四层同步架构——DECISIONS.md 为 SSOT + auto checks + session injection + memory
- **状态**: `approved` — 已落地

### D-20260627-002: Issue 12 Phase 0/1 — rand* 翻译顺序
- **决策**: rand_all → rand_arm/wpn → randname → randbook（按 @keyword@ 依赖图）
- **状态**: `approved` — Phase 1 已交付

---

## 二、跨 Issue 约束注册表

> 任何 Agent、任何任务都必须遵守。新增约束时写明来源和适用范围。

| ID | 约束 | 来源 | 适用范围 |
|----|------|------|---------|
| C-01 | `god_name()` DB 查找 → `_god_name_en()` | Issue 14, 26 | 所有神祇相关代码 |
| C-02 | `equip_slot_name()` 协议用途 → `_en()` 变体 | Issue 26 | Lua API 调用链 |
| C-03 | `species::name()` 匹配 → `from_str_loose` 两阶段查找 | Issue 6 | 物种名匹配 |
| C-04 | source.txt 追加前 → `grep -F` 去重 | Agent-Prone Mistakes | 所有 source.txt 修改 |
| C-05 | `conj_verb()` 绝不包裹中文 | 已知反模式 | 所有动词处理代码 |
| C-06 | 位置参数 → `mprf_p`（非 `mprf`） | Issue 30, MinGW 限制 | 所有 `%n$s` 格式串 |
| C-07 | Lua 比较字符串绝不翻译 | 已知反模式 | `"Mummy"`, `"Zin"` 等 |

---

## 三、待决事项

| ID | 事项 | 阻塞于 | 创建 |
|----|------|--------|------|
| P-01 | Issue 32 Options.language 清理 (~50 处, 20+ 文件) | analysis.md | 2026-06-29 |
| P-02 | Issue 25 Phase 1 strwidth + 翻译文件修复 | 调度 | 2026-06-28 |
| P-03 | Issue 27 ARG-DIFF beam.cc conj_verb 迁移 | crawl-coder | 2026-06-29 |
| P-04 | Issue 31 存档中文化执行 | 方案确认 | 2026-06-29 |

---

## 四、Agent 调度日志

| 时间 | Agent | Worktree | 任务 | 结果 |
|------|-------|----------|------|------|
| 2026-06-30 | — | phase-a-checkpoint | Phase A 基础设施实施 | 进行中 |
| 2026-06-29 | zh-code-reviewer | — | Issue 27 review | ✅ Go |
| 2026-06-29 | crawl-coder | fix-tcr1-v2 | TCR1 P0 fix | ✅ |

---

## 五、Prompt 行数追踪

> Phase B+ 改造 prompt 时的对照基线。每次修改 Agent prompt 后更新。

| Agent | Phase A 基线 | 当前 | 备注 |
|-------|-------------|------|------|
| zh-translator | 266 | — | 2026-06-30 基线 |
| crawl-coder | 167 | — | 2026-06-30 基线 |
| zh-code-reviewer | 218 | — | 2026-06-30 基线 |
| translation-reviewer | 91 | — | 2026-06-30 基线 |
