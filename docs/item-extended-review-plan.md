# Issue #29 扩展物品翻译复审计划

## 冻结边界

- 基线：`01dc9911ec9948aff661f6ec0b9b0a798fcf909d`
- 初始 glossary SHA-256：
  `8ddd7dc86af7dc0b6e717ca3ed5b7b3fdf82c50e7441ab0dec62bf2396898a81`
- 资产裁决后的 glossary SHA-256：
  `8b2a0a03173972806573f0ee0414d1a905e4c70aacd6f9f1368b92b0505b2036`
- 当前清单状态：**provisional inventory**。本文件冻结资产审阅边界；后续
  `crawl-coder` 扩展现有只读 inventory 后，必须机械验证 inventory 与
  `item-extended-review-results.md` 的 identity 双向差集为空。该机械化工作
  不得改变本批已经审阅的集合或普通物品 D-B-020 的结论边界。

## 验收与非目标

验收要求是每个固定 identity、兼容 identity、稳定生成组件和描述 identity
各有一张唯一证据卡与一个终态；生命周期、输入 SHA、生产者、消费者、条件、
数值、异常与玩法后果均可追溯。允许的终态只有 `keep`、`adjust`、
`retranslate`、`defer terminology`、`defer implementation`。

不修改神器属性、概率、效果、平衡、存档 schema 或协议 identity；不枚举真正
随机的最终名称，不把中文显示名反查成英文 identity，不纳入商店策略、鉴定攻略、
铭文建议和 FAQ。

## 冻结清单

| 批次 | 稳定 identity | 数量 | 生命周期 / 说明 |
|---|---|---:|---|
| A | `art-data.txt` 固定神器 | 140 | 121 current + 19 deleted compatibility |
| A0 | 固定神器 dummy | 2 | internal；不面向玩家，只分类 |
| B | 固定神器 EN/ZH 长描述块 | 140 / 144 | ZH 多 4 个兼容 key |
| C | `unident.txt` 通用描述 | 7 | current |
| C | 普通未鉴定外观组件 | 186 | wand、ring、amulet、staff、potion、ZH scroll |
| D | gizmo 组件 | 539 | adjective 167 + noun 170 + modifier 202 |
| E | 特殊物品身份 | 23 | rune 19 + corpse subtype 2 + gold 1 + Orb 1 |
| F | 普通物品生产 identity | 390 | 只用于 description slot 映射；不重做 D-B-020 名称审计 |
| F | 英文普通描述 DB key | 307 | ZH 初始 310；反向差集须解释或清零 |
| G | randart TextDB grammar key | 115 | `randname/rand_wpn/rand_arm/rand_all` |
| G | randart 候选物理组件 | 2734 | 33/45/19/18 个 key 中的有限候选行 |

普通未鉴定外观组件按独立槽计数：wand `12 + 16`，ring `29 + 13`，
amulet `29 + 13`，staff `4 + 10`，potion `23 + 15`，中文 scroll
`12 + 10`。最终组合不是额外 identity。

## 随机最终串为何不可枚举

randart 名称同时包含加权抽样、最长 25 次重抽、递归数据库 token、玩家名、
种族、分支、英文神名替换以及 `make_name()` 伪词后备；gizmo 名称有
modifier 递归、两类序列号模板、随机数字与大写字母，并将多个槽拼接。
因此最终字符串空间受运行时输入影响，不能用一个历史计数冻结。完整性证明对象是：

1. 有限 TextDB key；
2. 每个 key 下的物理候选序号；
3. token 保真与递归拓扑；
4. 生产 identity、缓存/存档边界和最终显示模板。

## 依赖批次与落地顺序

1. 固定神器：真名、显式/派生外观、基础类型、属性、DBRAND/DESCRIP、hook、
   EN/ZH 长描述。
2. `unident` 通用描述与普通未鉴定外观组件。
3. 19 rune、corpse grammar、gold、Orb。
4. gizmo 三个稳定槽和 539 个物理组件。
5. 当前普通物品 description slot 与 307 个英文 DB key。
6. randart 115 个 grammar key、2734 个有限候选和不可枚举生成语法。
7. 同步 SourceDB、`decisions.md`、`glossary.md` 与 `glossary.utf8`。

共享专名和技能术语必须整组检查后再落地。D-B-020 只有输入、行为、生命周期、
glossary 与 decisions 均未变化的单卡才可复用；由于历史批次没有持久化逐项卡，
且本批 glossary 已变，本计划不整批复用其“已完成”结论，只将其当作校准证据。

## 证据卡字段

结果表每一行即一张紧凑证据卡，至少含 identity、生命周期、英文源、
当前/最终中文、producer/consumer 或元数据、输入位置、终态和 deferred
re-entry trigger。`not applicable` 必须显式出现，不能用空白隐去。

后续 coder 机制必须独立输出并阻断：

- inventory identity 重复；
- reviewed identity 重复；
- `inventory - reviewed`；
- `reviewed - inventory`；
- 非终态结论；
- 无理由或无 re-entry trigger 的 defer；
- EN/ZH key、物理序号或递归 token 不等。

## 验证

资产写入阶段只运行一次：

```bash
bash .claude/scripts/verify_zh.sh --profile translation
```

不在本阶段运行 code、ci、review 或 final gate。完整原始报告路径与所有相关
warning/failure 记录在结果文档。
