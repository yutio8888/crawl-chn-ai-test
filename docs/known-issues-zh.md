# 已知未完成的小问题（快速参考）

> 本文件仅记录太小而无需开 issue 的零散问题。
> 翻译工程进展和已追踪的 issue → `${DCSS_ISSUES_DIR:-../issues}/INDEX.md`
> 翻译裁决（术语选择）→ docs/decisions.md
> 最后更新：2026-07-01

---

## 已由 Issue 系统追踪

| Issue | 状态 | 说明 |
|-------|------|------|
| #6 | approved | MinGW towlower CJK 损坏修复 |
| #7 | approved | 存档界面 + 技能称号中文化 |
| #8 | approved | 15 条混合中英文日志消息修复 |
| #9 | approved | 10 个 Portal .des 文件翻译 |
| #10 | approved | 10 种龙鳞护甲中文名 |
| #11 | approved | 拾取消息 + 技能菜单 UI + 怪物语音 |
| #12 | phase1_partial | dat/database/zh/ 数据库翻译（~1,432 条） |
| #13 | documented | 神祇名统一 + 文档修正 |
| #14 | documented | 翻译工程同步架构 |
| #15 | analyzed | 项目文档管理 |

---

## 已完成的早期修复

| 类别 | 范围 |
|------|------|
| 核心引擎 | conj_verb 中文绕过、player::name、mons_attack_verb |
| 硬编码英文字符串 | main.cc / spl-damage.cc / spl-cast.cc 等 ~40 处 |
| 混合中英文格式串 | melee-attack.cc / item-use.cc / actor.cc 等 ~80 处 |
| 特性/抗性/状态标签 | feature-data.h、describe.cc、mon-info-flag-name.h |
| 技能面板 + CJK 对齐 | zh/skills.txt、skill-menu.cc |
| 神力界面 | describe-god.cc / god-conduct.cc 等 ~200 条 |
| 怪物状态 | mon-info-flag-name.h / mon-info.cc |

---

## ✅ 已完成（Issue 12 — 2026-07-01 关闭）

所有 22 个 `dat/database/zh/*.txt` 文件均达到 100%+ 覆盖率。

| 项目 | 文件 | 覆盖率 |
|------|------|--------|
| rand* 模板重设计 | randname.txt 等 5 文件 | 100% |
| 怪物对话 | monspeak.txt | 99.5%（732/736） |
| 神祇对话 | godspeak.txt | 100%+（195/193） |
| 装饰性文本 | decorlines.txt | 100%+（138/133） |
| 法术失误描述 | miscast.txt | 100%（33/33） |
| 怪物施法宣言 | monspell.txt | 100%+（290/265） |
| 武器噪音 | wpnnoise.txt | 100%+（69/65） |
| 怪物嘲讽 | insult.txt | 100%（33/33） |
| 怪物喊叫 | shout.txt | 100%（94/94） |
| 涂鸦 | graffiti.txt | 100%（58/58） |
| 颜色名 | colourname.txt | 100%（9/9） |

---

## 主动选择不翻译

### chardump.cc 咒语列表段落未翻译

- **日期**: 2026-07-01
- **文件**: `crawl-ref/source/chardump.cc`
- **位置**: 行 1057, 1059, 1122, 1123, 1127, 1128
- **内容**: "You knew/know the following spells", "Your spell library was/is empty", "Your spell library contained/contains the following spells" 等整句
- **状态**: 暂不修复，需统一 T_() 迁移（涉及过去时/现在时切换）

### spl-cast.cc "N/A" 未翻译

- **日期**: 2026-07-01
- **文件**: `crawl-ref/source/spl-cast.cc`
- **位置**: 行 178
- **内容**: `"N/A"` — 咒语伤害描述中的无伤害占位符
- **状态**: 暂不修复，中国玩家理解 "N/A"，且需要确认 source.txt 是否已有条目

---

### monname.txt — 专有名词保留原文

- **日期**: 2026-06-27
- **文件**: `dat/database/monname.txt`
- **状态**: 暂不翻译

`monname.txt` 包含约 400 个来自 10 种文化的专有名词（西欧、罗马、阿兹特克、美索不达米亚、埃及、祖鲁、阿拉伯、斯拉夫、巴西等），以及约 60 个兽人名字和约 55 个钢铁精灵武器名。这些名字通过 `@ancestor name@`、`@any orc name@` 等关键词显示在中文游戏界面中。

**不翻译的理由**：
1. 文化特征保留 — 音译后不同文化的名字在中文中趋同
2. 行业惯例 — 中文游戏保留次要 NPC 英文原名是常见做法
3. 工作量与收益 — 500+ 名字需要建立 10 种文化的中文音译规范，而它们仅出现在次级 UI 中

**后续方案（如需要改变）**：按需音译高频名字、仅翻译兽人/钢铁精灵名、或全量音译。
