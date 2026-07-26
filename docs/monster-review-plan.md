# Issue #24 怪物名称、描述与生命周期全量复审计划

## 冻结边界

- 基线提交：`7e7e7e78f5ab7c7fc5f5ee458a205850510ad15c`
- 目标分支：`chn-0.34.1-base`
- 依赖：Issue #16 已关闭；其怪物名称完整性修复已包含在基线中。
- 生产身份源：`crawl-ref/source/monster-type.h` 中 `NUM_MONSTERS` 之前的
  活跃具体枚举。
- 现行定义源：`crawl-ref/source/dat/mons/*.yaml`。
- 显示消费者：`source.txt` 名称、`montitle.txt` 独特怪物称号及中英文
  `monsters.txt` 描述。

## 验收标准

1. 由只读清单命令确定性枚举全部具体怪物身份，并交叉验证枚举与
   `dat/mons` 定义集合。
2. 每个身份记录生命周期、暴露类型、名称、genus/species、独特性、
   生产数据、核心数值/抗性/攻击/法术/行为字段、描述和实际消费者。
3. 每个身份恰有一张证据卡和一个终态结论：
   `keep`、`adjust`、`retranslate`、`defer terminology` 或
   `defer implementation`。
4. 现行名称与术语表一致；同名冲突、描述语义缺失及过时机制全部给出
   明确处理。兼容枚举不得借用无关的同名 SourceDB 条目。
5. 清单集合、证据卡集合与终态结论集合完全相等，且无重复、无漏项。
6. ZH 资产由单一译者顺序修改，通过 translation profile；提交后的
   干净候选按 review-contract-v4 准备并只运行一次 final gate。

## 非目标

- 不改怪物平衡、AI、生成表、法术机制或存档枚举值。
- 不把已移除兼容身份重新引入 `dat/mons`。
- 不独立裁定法术名称、通用对白或 Wiki 统计。

## 既有机制复用

扩展 `.claude/scripts/monster_name_ssot.py`，沿用现有 TextDB 解析、
名称 SSOT 与重复译名检查；不新增清单模块、持久数据库或第二套 YAML
语义解析器。清单 JSON 是可重建证据，不提交派生副本；逐项终态记录在
`docs/monster-review-results.md`。

## 顺序

1. 冻结枚举/定义/消费者清单。
2. 先审 genus/species 与共享术语，再审普通怪物、独特怪物和内部实体。
3. 顺序落地名称，再落地描述和决策文档。
4. 证明 795 项集合相等，运行 translation profile。
5. 提交干净候选，准备机械路由评审，最后运行一次 final gate。
