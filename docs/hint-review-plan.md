# Issue #50 R3 Hints TextDB 全量审阅计划

## 冻结边界

- 上游总览：Issue #40 R3；执行入口：Issue #50（hints 子批）。
- 基线：`61b35104580fb56340e3cdac87ca5fffa36788bf`。
- 规范身份源：英文与中文 `hints.txt` 按生产 TextDB 语义解析后的
  effective key union；identity 形式为 `hint:<canonical key>`。
- 生产事实源：`hints.cc`、`hints.h`、英文／中文 `hints.txt`、命令枚举、
  ZH 运行时测试入口及 `docs/glossary.md`。所有输入从精确 Git tree 读取。
- 初始只读探测得到 EN 116 个、ZH 117 个唯一 effective key，union 为
  117；唯一 ZH-only key 是 `dissection reminder`。正式结论以 inventory
  重建结果为准，不把这些计数硬编码成未来版本常量。
- 基线 inventory 已重建为 115 个 current producer、1 个 TAG34 enum
  compatibility、1 个 localized test-only compatibility；补入命令改键邻接
  检测后的 inventory SHA-256 为
  `8a756e6447b258eb6e53742f10ae79cbd257ddb0e19ab13926928940096242fd`。
- 基线存在 18 条待本批解决的 blocking 结构诊断，覆盖 17 个 identity：原有
  5 条为英文 `hint_seen_branch`、`hint_seen_shop` markup，中文
  `hint_seen_first_object` 的两条 markup 诊断，以及中文
  `hint_you_mutated` 的未知 `CMD_DISPLAY_CHARACTER`；新增 13 条为英文命令
  token 与相邻 ASCII 字母融合，合计 15 个 occurrence／13 个 identity。
  后者中 14 个会在改键后产生错误单词，另一个是可工作但应拆开的两步输入。
  这些诊断与 60 个仅供人工审阅的 EN/ZH structural candidates 分离，后者不
  自动构成缺陷。

生命周期必须明确区分：

1. `current`：由 `hints.cc` 的 literal lookup 或有限格式族实际产生；
2. `compatibility enum unconsumed`：有 EN/ZH 与兼容 enum，但无当前显示调用；
3. `localized test-only compatibility`：仅本地化 TextDB 与运行时测试消费；
4. 新出现的其他 producer／EN／ZH 差异必须先解释，不能自动归类。

## 复用机制

- 复用现有 production TextDB parser、exact-Git snapshot、trusted Git 环境、
  fail-closed `/tmp` artifact 写入、命令枚举和 strict JSONL review coverage。
- Hints inventory 只补足 Tutorial inventory 无法表达的 EN/ZH union、
  producer family、兼容生命周期、`$item`／占位符和 Lua／平台结构事实。
- 不新增全局 ledger、schema、质量分数、Gold 或第二套 final gate。

## 验收标准

1. inventory identity 完整、唯一、确定排序；每个 producer、EN-only、ZH-only、
   override、空值和未解析调用都得到机械解释或 fail-closed 结果。
2. 每个 identity 恰有一张证据卡和一个终态结论：`keep`、`adjust`、
   `retranslate`、`defer terminology` 或 `defer implementation`。
3. 每张卡记录 EN/ZH、producer、consumer、显示上下文、实际行为、目标、范围、
   条件、例外、数字、玩法后果、dependency group、token facts、证据位置和置信度。
4. `$cmd[...]`、`$item[...]`、`$1`、`$2`、markup、Lua 块、平台标签和格式
   token 均机械记录；命令 token 在三种生产平台投影中不得与 ASCII 单词片段
   融合。其余 EN/ZH 结构差异作为审阅证据，不自动等同语义缺陷。
5. inventory 与 reviewed identity 集合双向差集为空，顺序和机械字段绑定一致；
   每个 defer 记录原因、owner 与 re-entry trigger。
6. `adjust`、`retranslate` 与 defer 集中交由人工确认；确认前不修改 ZH 资产。
7. 确认后由单一 `zh-translator` 顺序修改中文 TextDB；tooling/code 阶段不并发
   重开该资产。
8. 只运行匹配的 development profile；干净候选依次完成 schema-v4 mechanical
   routing、双 reviewer readiness、单次 final gate、merge-time validation 与 PR CI。

## 审阅顺序

1. 入口、死亡、完成与兼容／测试专用身份；
2. 移动、探索、地图、楼梯、传送门与地形；
3. 物品、装备、背包、自动拾取与消耗品；
4. 战斗、怪物、远程攻击、逃跑与状态警告；
5. 魔法、法力、施法失误、技能、属性与训练；
6. 神祇、信仰、能力、突变与抗性；
7. 其余无共享依赖的提示，并回查所有依赖组的一致性。

每个依赖组必须包含至少一个冻结 `keep` 对照；发现系统性漏项时，扩大到完整
依赖组后再提出结论。

## 非目标

- 不处理 commands、tutorial、help/FAQ 已有或后续子批身份。
- 不把 `hints.cc` 中通用 `T_()` SourceDB 文本扩成一次性 `source.txt` 巨型审阅；
  本批只取得 Hints TextDB identity 的所有权，代码行为只作为事实证据。
- 不修改游戏机制、数值、概率、存档 enum、协议或 TextDB lookup key。
- 不根据换行、长度或简单 token 启发式自动裁决译文。

## 重建入口

```bash
python3 .claude/scripts/hint_inventory.py \
  --baseline-ref 61b35104580fb56340e3cdac87ca5fffa36788bf \
  --inventory-output /tmp/hint-inventory-issue50-baseline.json \
  --review-results docs/hint-review-results.md
```

输出采用 fail-closed 的独占新建；若该 `/tmp` 文件已存在，改用另一个明确的
新文件名，不覆盖旧证据。

候选落地后追加 `--candidate-ref <exact-commit>`，证明每个已确认结论与候选
中文值一致。
