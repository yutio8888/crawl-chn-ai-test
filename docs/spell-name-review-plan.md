# 法术名称逐项复审计划

本文件只记录本轮复审的范围、顺序、进度和证据入口。通用术语仍以
`docs/glossary.md` 为准，具体命名裁定仍写入 `docs/decisions.md`；本文件
不构成第三套术语标准。

## 验收边界

- 冻结基线：`5cb9aa27a224a81da780757f8445cfc07de09dfd`。
- 术语上下文 SHA-256：
  `1af737231c2c1287c9cc3f3bb34cfa3890138ae2553c955c73db70b41701df3f`。
- 以当前 `crawl-ref/source/spl-data.h` 的完整法术枚举为生产清单。
- 每个枚举必须有且仅有一张证据卡和一个明确结论。
- 每张证据卡必须核对英文名、当前中文名、等级、学派、flags、使用者、
  英文描述、中文描述及实际实现。
- 同系列成员逐项审阅，但系列全部完成前不落地任何成员的改名。
- 法术集合、描述或实现变化后，重新生成清单；只复用证据未变化的记录。

## 结论类型

- `保留`
- `微调`
- `重译`
- `暂缓术语`
- `暂缓代码`
- `证据不足`

`证据不足` 不是通过状态。只有前五类结论可以结束单项审阅，且所有暂缓
项目必须有明确的后续入口。

## 执行顺序

1. 生成只读、确定性的全量 inventory，并校验身份完整性与唯一性。
2. 使用已有裁定完成校准批次：
   - Blink 系列
   - Bolt 系列
   - Cloud 系列
   - Dispersal
   - Mesmerise
3. 按共享词根审阅其余系列。
4. 按共享人物专名审阅专名法术。
5. 按共享实体、元素和状态术语审阅关联法术。
6. 审阅无明显依赖的独立法术。
7. 证明 inventory 集合与已审阅集合完全相等。

怪物专属法术随所属系列审阅；没有系列依赖时进入独立法术阶段，不因
曝光率低而免审或自动降级。

## 单项证据卡

每个法术按以下顺序处理：

1. 只读探索角色在不参考中文措辞优劣的前提下提炼英文原名和机制语义。
2. 核对描述与实现，列出目标、范围、条件、例外和玩法后果。
3. 翻译审阅角色比较当前中文名、系列关系、强度和术语。
4. 记录结论、置信度、文件与行号证据。
5. 系列全部完成后统一处理系列内部冲突。

证据卡至少包含：

```text
SPELL_*：
英文名：
当前中文名：
等级 / 学派 / flags：
玩家或怪物使用：
英文原名语义：
实际核心效果：
目标 / 范围 / 条件 / 例外：
英文描述：
中文描述语义一致性：
所属系列：
现行 glossary / decision：
结论：
建议译名：
被拒方案：
证据位置：
置信度：
```

## 进度

### 清单

- [x] 安全只读 inventory（默认执行输入摘要守恒）
- [x] 完整性与唯一性负向测试（含普通与 AXED 完整记录静默漏项变异）
- [x] inventory 与独立 `spell-type.h` 生产身份集合完全相等

当前已验证清单共 511 项：409 项现行法术、98 项
`TAG_MAJOR_VERSION == 34` 已移除兼容记录、2 项描述专用 dummy、2 项内部
placeholder；中文标题映射 511/511，英文与中文描述均为 402/511。
默认参数下 inventory JSON 的 SHA-256 为
`1829b52622d79de772a3de6ac84fb9da0be2431cc3c774b35613e0e73629dbb0`。
聚焦测试 8/8 通过，code profile 0 项失败；开发复审为 0 Blocker /
0 Needs Fix。
清单命令：

```bash
python3 .claude/scripts/migrate_spell_titles.py inventory --require-zh-titles
```

### 校准批次

- [x] Blink 系列（证据、裁定、翻译落地及 translation profile 已完成）
- [x] Bolt 系列（证据、裁定、翻译落地及 translation profile 已完成）
- [x] Cloud 系列（证据、裁定、翻译落地及 translation profile 已完成）
- [x] Dispersal（证据、裁定、描述修正及 translation profile 已完成）
- [x] Mesmerise（证据、裁定、关联术语统一及 translation profile 已完成）

### 全量复审

当前已完成 210/511 项逐项审阅。

- [ ] 共享词根系列
  - [x] Call 词形系列（10 项现行法术；translation profile 已完成）
  - [x] Summon 词形系列（42 项证据、裁定、单批落地及 translation profile 已完成）
  - [x] Breath 词形系列（22 项证据、裁定、单批落地及 translation profile 已完成）
  - [x] Dart 词形系列（2 项证据、裁定、单批落地及 translation profile 已完成）
  - [x] Shadow/Shadows 词形系列（13 项证据、裁定、描述落地及 translation profile 已完成）
  - [x] Throw 词形系列（8 项证据、裁定、描述落地及 translation profile 已完成）
  - [x] Beam 词形系列（2 项均已审阅；其中 1 项复用 Shadow 证据，translation profile 已完成）
  - [x] Gaze 词形系列（7 项证据、裁定、名称与描述落地及 translation profile 已完成）
  - [x] Touch 词形系列（2 项证据、裁定、描述落地及 translation profile 已完成）
  - [x] Arrow 词形系列（4 项证据、裁定、描述落地及 translation profile 已完成）
  - [x] Flame/Flames 词形系列（10 项均已审阅；其中 1 项复用 Throw 证据，translation profile 已完成）
  - [x] Form 词形系列（6 项已移除兼容记录的生命周期、标题裁定及 translation profile 已完成）
  - [x] Poison/Poisonous 词形系列（9 项均已审阅；其中 2 项复用既有证据，translation profile 已完成）
  - [x] Dispel 词形系列（2 项证据、裁定、描述落地及 translation profile 已完成）
  - [x] Awaken 词形系列（5 项证据、裁定及 translation profile 已完成）
  - [x] Forge 词形系列（4 项证据、裁定、描述落地及 translation profile 已完成）
- [ ] 人物专名系列
  - [x] Maxwell's 专名系列（2 项证据、裁定、描述落地及 translation profile 已完成）
  - [x] Iskenderun's 专名系列（2 项证据、裁定、名称与描述落地及 translation profile 已完成）
  - [x] Vhi's 专名系列（2 项证据、裁定、名称与描述落地及 translation profile 已完成）
  - [x] Cigotuvi's 专名系列（1 项现行、2 项已移除兼容；描述落地及 translation profile 已完成）
  - [x] Ozocubu's 专名系列（2 项证据、裁定及 translation profile 已完成）
  - [x] Gell's 专名系列（2 项证据、裁定、关联物品描述修正及 translation profile 已完成）
  - [x] Borgnjor's 专名系列（2 项证据、裁定、名称与描述落地及 translation profile 已完成）
  - [x] Alistair's 专名系列（2 项证据、裁定、描述澄清及 translation profile 已完成）
  - [x] Eringya's 专名系列（2 项证据、裁定、描述、关联引文及 translation profile 已完成）
  - [x] Nazja's 专名系列（2 项证据、裁定、描述重译及 translation profile 已完成）
  - [x] Olgreb's 专名系列（1 项证据、裁定、描述润色及 translation profile 已完成）
  - [x] Lehudib's 专名系列（1 项证据、裁定、描述润色及 translation profile 已完成）
- [ ] 实体、元素和状态术语系列
- [ ] 独立法术
- [ ] 集合相等性终检

## 落地规则

- 审阅者只读，不在 readiness 或证据收集阶段修复问题。
- 中文翻译资产由同一 `zh-translator` 顺序修改。
- 每个完整系列作为一个翻译批次运行
  `bash .claude/scripts/verify_zh.sh --profile translation`。
- 代码支持需求单独交给 `crawl-coder`，不得在译名批次中隐式扩展范围。
- 最终候选使用仓库现有的不可变审查包、机械 reviewer 路由和单次最终门禁。

## 审阅结果

逐项证据卡和系列结论记录在 `docs/spell-name-review-results.md`。进度勾选仅表示
证据与裁定已经齐备；翻译落地、验证和最终门禁状态在结果文件中单独记录。
