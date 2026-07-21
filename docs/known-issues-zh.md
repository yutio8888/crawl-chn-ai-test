# 中文本地化历史状态参考

> 本文件仅保留早期完成情况与主动不翻译决策，不再承担 backlog 或状态跟踪。
> 当前可行动问题 → <https://github.com/yutio8888/crawl-chn-ai-test/issues>
> 翻译裁决（术语选择）→ docs/decisions.md
> 冻结日期：2026-07-21

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

## 数据库翻译历史里程碑

[Legacy issue 12](https://github.com/yutio8888/crawl-chn-issues-archive/tree/d31fccd3eb2c2cd612739646769ee1b45b6dfb01/12)
记录了数据库翻译批次；`monname.txt` 于 2026-07-19 补齐。

冻结时，23 个 `dat/database/zh/*.txt` 文件均已纳入中文本地化；当时记录的覆盖率如下。

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
| 兽人、先祖与武器命名池 | monname.txt | 100%（790/790 个显示值）¹ |

¹ `monname.txt` 保留全部英文数据库查找键、`@keyword@` 引用和 `w:N`
权重，仅本地化玩家可见的名字候选值。

---

## 冻结时的主动不翻译记录

以下内容只说明 2026-07-21 冻结时的历史取舍，不表示当前版本仍存在、
也不构成待办。若在当前默认分支复现，请创建 GitHub Issue 并记录当前证据。

### chardump.cc 咒语列表段落未翻译

- **日期**: 2026-07-01
- **文件**: `crawl-ref/source/chardump.cc`
- **位置**: 行 1057, 1059, 1122, 1123, 1127, 1128
- **内容**: "You knew/know the following spells", "Your spell library was/is empty", "Your spell library contained/contains the following spells" 等整句
- **冻结时处理**: 未纳入当时的 T_() 迁移批次（涉及过去时/现在时切换）。

### spl-cast.cc "N/A" 未翻译

- **日期**: 2026-07-01
- **文件**: `crawl-ref/source/spl-cast.cc`
- **位置**: 行 178
- **内容**: `"N/A"` — 咒语伤害描述中的无伤害占位符
- **冻结时处理**: 保留 `N/A`；当时认为玩家可理解，未继续验证 `source.txt` 覆盖。
