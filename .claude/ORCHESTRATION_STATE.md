---
updated: 2026-07-05T15:00:00+08:00
last_commit: b77a14a718
session_id: b34cf734-660f-441b-aee1-094015fbe006
---

# 编排者状态 — DCSS 汉化项目

> 编排者（人类 + Claude）的决策与约束外部存储器。
> **不是对话日志**——只记录决策、约束、待决事项。
> 每次做决策、调度 Agent、或评估 review 结果后，必须更新此文件。
>
> 职责边界：
> - 不存 issue 状态 → `${DCSS_ISSUES_DIR:-../issues}/INDEX.md`
> - 不存翻译决策 → `docs/decisions.md`
> - 不存脚本输出 → `.claude/metrics/verify/`
> - **只存**：为什么做决策、跨 issue 约束、编排者在忙什么

---

## 一、当前决策栈（最近优先）

### D-20260705-014: 怪物名称术语表建立 + 100% 覆盖率达成

- **决策**: 22 个高频词根术语决策写入 `docs/decisions.md` (D-A-007 ~ D-A-028)，后扩展至 25 条 (D-A-029 ~ D-A-031)
- **状态**: `approved` — 已合入 chn-0.34.1-base (b77a14a718)
- **成果**: 怪物名覆盖率 668/668 (100%)；修正 4 处术语不一致；发现 audit_data_i18n.py 分隔符解析 bug（%%%% vs %%%%%）
- **新增决策**: draconian→龙人, deep elf→精灵, dragon→龙, drake→幼龙, jelly→果冻怪, goblin/hobgoblin→地精/大地精, giant 三模式规则 等
- **术语修正**: Summon Drakes 召唤小龙→召唤幼龙, hobgoblin 大哥布林→大地精, Royal Jelly 皇家史莱姆→果冻王, martyred shade 殉道残影→殉道暗影
- **约束**: jelly≠slime（果冻怪≠史莱姆），四类无定形怪物各保留独立中文术语

### D-20260701-013: Issue 32 并发分析 — 6 Agent 3 轮计划
- **决策**: 剩余 ~79 分支分为 6 Agent、3 轮并发执行，按共享数据依赖分组
- **状态**: `planned` — 待 zh-code-reviewer 审阅
- **分组**: 第 1 轮独立简单文件(A1:8 文件/A2:5 文件)，第 2 轮共享集群(A3:5 文件/A4:2 文件)，第 3 轮复杂独立文件(A5:2 文件/A6:2 文件)
- **约束**: 按 share 数据结构分组；source.txt 冲突用 append-only 合并；consolidation worktree 收集所有 commit 后一次性 merge

### D-20260701-012: Issue 34/X1 T_() 迁移完成 + Issue 12 DB 100%
- **决策**: 49 个 commit 合入 chn-0.34.1-base，T_() 覆盖率 93.5%，ARG-DIFF 清零，Issue 12 全部 DB 文件完成
- **状态**: `approved` — Issues 12/24/25/27/28/34/X1/X2 全部关闭
- **剩余活跃 Issue**: 仅 31（存档兼容）和 32（硬编码分支清理）

### D-20260630-008: Phase A-E 架构优化全部完成 + 审查修复
- **决策**: 6 个 Phase 全线实施，25 条审查发现全部修复
- **核心原则**: Agent 只生成修改；脚本负责结构化验证；编排者负责语义判断
- **状态**: `approved` — 已合入 chn-0.34.1-base（9f06b19f83）
- **新建脚本（12 个）**: check_checkpoint, record_review, post-translator, post-coder, post-reviewer, smoke_test, cross_file_terms, split_source, context_resolve, validate-terms, anti-patterns, missing-t (扩展)
- **修改文件（6 个）**: CLAUDE.md, check_consistency.sh, scan_i18n.py, database.cc, crawl-coder.md, TOOLCHAIN.md
- **约束**: 验证逻辑不写在 prompt 里，全部活在 scripts/ 下；Agent prompt 不含自检段

### D-20260630-007: Phase E — 动态上下文注入 + 增量验证
- **决策**: context_resolve.sh 按任务类型生成精简上下文；crawl-coder 增量验证协议
- **状态**: `approved` — 已合入

### D-20260630-006: Phase D — source.txt 拆分支持 + 跨文件术语扫描
- **决策**: database.cc 目录扫描（所有 .txt 文件自动加载）；cross_file_terms.py 跨文件检测
- **状态**: `approved` — 基础设施已就绪，实际数据拆分待执行
- **约束**: 拆分后需同步启用 cross_file_terms.py

### D-20260630-005: Phase C — 运行时冒烟测试
- **决策**: smoke_test.sh 检测启动输出中的协议泄露、英文残留、崩溃
- **状态**: `approved` — 已合入（仅检查启动输出，ncurses 交互需 expect 驱动）

### D-20260630-004: Phase B+ — Agent prompt 改造
- **决策**: 4 个 Agent 全部删除自检段 → 替换为证据协议（调用 post-*.sh）
- **状态**: `approved` — 已合入

### D-20260630-003: Phase B — validate-terms + anti-patterns
- **决策**: scan_i18n.py 新增两个子命令；check_consistency.sh --strict 模式
- **状态**: `approved` — 已合入（3 轮审查修复后零误报）

### D-20260630-002: Phase A — 编排者基础设施
- **决策**: ORCHESTRATION_STATE.md + check_checkpoint.sh + post-*.sh + record_review.sh
- **状态**: `approved` — 已合入

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
| C-08 | Agent 不做自检 → 调用 post-*.sh，编排者读原始日志 | Phase A/B+ | 所有 Agent |
| C-09 | 验证逻辑不写在 prompt 里 → 活在 `.claude/scripts/` 下 | Phase A 核心原则 | 所有验证相关代码 |

---

## 三、待决事项

| ID | 事项 | 阻塞于 | 创建 |
|----|------|--------|------|
| P-01 | Issue 32 Options.language 清理 — 6 Agent 3 轮并发计划已出，待 review | zh-code-reviewer 审阅 | 2026-06-29 |
| P-04 | Issue 31 存档中文化执行 | 方案确认 | 2026-06-29 |
| P-05 | source.txt 实际拆分（基础设施已就绪，数据待拆分） | 确认拆分方案 | 2026-06-30 |
| P-06 | 远期：完整测试框架 + 趋势分析 + prompt 自动调优 | Phase E 交付 | 远期 |

---

## 四、Agent 调度日志

| 时间 | Agent | Worktree | 任务 | 结果 |
|------|-------|----------|------|------|
| 2026-06-30 | — | fix-green-suggestions | 🟢 5 条建议修复 | ✅ |
| 2026-06-30 | — | fix-all-review-issues | 12 条 🔴🟡 修复 | ✅ |
| 2026-06-30 | — | fix-hardcoded-terms | cross_file_terms 去硬编码 | ✅ |
| 2026-06-30 | — | phase-e-context | Phase E 上下文注入 | ✅ |
| 2026-06-30 | — | phase-d-source-split | Phase D source 拆分 | ✅ |
| 2026-06-30 | — | fix-review-n1-n3 | N1+N3 审查修复 | ✅ |
| 2026-06-30 | — | fix-parse-decisions | parse_decisions 修复 | ✅ |
| 2026-06-30 | — | fix-anti-patterns-bugs | 3 个阻断 bug 修复 | ✅ |
| 2026-06-30 | — | phase-c-smoke-test | Phase C smoke test | ✅ |
| 2026-06-30 | — | phase-b-plus-prompts | Phase B+ prompt 改造 | ✅ |
| 2026-06-30 | — | phase-b-scripts | Phase B 验证脚本 | ✅ |
| 2026-06-30 | — | phase-a-checkpoint | Phase A 基础设施 | ✅ |
| 2026-06-29 | zh-code-reviewer | — | Issue 27 review | ✅ Go |
| 2026-06-29 | crawl-coder | fix-tcr1-v2 | TCR1 P0 fix | ✅ |
| 2026-06-30 | crawl-coder | issue34-batch-b | Issue 34 Batch B — Monster System T_() migration (24 files, ~470 entries) | 🟢 |

---

## 五、Prompt 行数追踪

> Phase B+ 改造 prompt 时的对照基线。每次修改 Agent prompt 后更新。

| Agent | Phase A 基线 | Phase B+ | 当前 | 备注 |
|-------|-------------|----------|------|------|
| zh-translator | 266 | 285 | 285 | 自检删除，证据协议替换 |
| crawl-coder | 167 | 181 | 183 | 增量验证协议 + @keyword@ 检查 |
| zh-code-reviewer | 218 | 235 | 235 | 自检删除，证据协议替换 |
| translation-reviewer | 91 | 97 | 97 | Execution 证据协议替换 |
