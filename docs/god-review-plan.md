# 神祇翻译审查计划

本轮审查以 `.claude/scripts/audit_god_inventory.py` 生成的清单为唯一身份边界。
父项来自当前 `TAG_MAJOR_VERSION` 下、`NUM_GODS` 之前的真实神祇枚举，并与
`_god_name_en()`、`god_name()` 逐项交叉检查。兼容性神祇仍属于清单，不因无法
在新游戏中选择而省略。

## 纳入范围

- 每个父项的英文身份、中文短名及生命周期。
- `gods.txt` 的介绍、能力概述、惩罚概述和生产数据中已有的额外段落。
- `godname.txt` 的长名，以及 `godspeak.txt` 的完整英文 key 集合。
- 每个神祇称号槽位。
- 按父项映射的静态神能、被动、喜爱/厌恶行为戒律和神罚 key；Ru、Ashenzari、
  Hepliaklqana、Nemelex Xobeh 的运行时能力来源另保留能力范围及属性 marker。
- ZH-only ability key 与英中 godspeak 静态选择拓扑差异；两者作为显式
`review_findings` 保留，不能通过空值跳过或只枚举中文文件来消失。

脚本同时记录所有输入文件的 SHA-256、术语表 SHA-256、父项/子项清单摘要和
清单摘要。`--review-results` 会要求结果文档为每个冻结父项提供恰好一张证据卡
和非空终局结论。

## 冻结边界

- Git 基线：`7b0224b32c0bd4b7b79119776762ee623857adc9`
- `docs/glossary.md` SHA-256：
  `91f0638a60e633d450ded2b6e7efdd3449e7ad2e0e27e710a52cd0dd2565d645`
- 最终 inventory SHA-256：
  `2985c819290cbffc213152d41cee8db7faa5a14bdd196c90cf76a7b4375c9575`
- 父项：27（current 26，compatibility-disabled 1）
- TextDB 身份：god descriptions 82、god longnames 23、godspeak 193
- 子项摘要：abilities 89、passives 78、conducts 30、wrath gods 28、
  title slots 224
- 终态 review findings：ZH-only ability keys 6、godspeak topology drift 0

逐父项结论和证据卡记录在 `docs/god-review-results.md`，该文件必须通过
inventory 的 `--review-results` 精确覆盖检查。

## 顺序批次

1. 冻结 enum 父项、英文身份 accessor、TextDB key 集与输入哈希。
2. 审查短名、长名和八级称号，并先落地上下文冲突修复。
3. 按父项审查介绍、能力概述、神罚概述以及专属 ability/passive/conduct 子项。
4. 审查 godspeak 内容并消除英中静态选择拓扑差异。
5. 在 `docs/god-review-results.md` 为每个父项写入终局结论，最后运行精确覆盖检查。

## 排除范围

- 神祇强度、平衡改动、攻略建议和玩法设计。
- 将能力、被动、戒律或神罚扩张为独立的逐条措辞审查；本轮只记录其生产身份，
  防止父项审查漏掉关联文本。
- 与神祇展示无关的协议、序列化、Lua 比较和 TextDB 查找 key 的本地化。
- Wiki 或其他外部页面推导的身份数量。

若审查发现必须引入新 schema、持久状态或跨类别重审，先停止并将范围决定交回
维护者，不在本轮清单内自行扩张。

## 执行与证据

生成清单：

```bash
python3 .claude/scripts/audit_god_inventory.py \
  --output .claude/metrics/god-review-inventory.json
```

验证结果覆盖：

```bash
python3 .claude/scripts/audit_god_inventory.py \
  --output .claude/metrics/god-review-inventory.json \
  --review-results docs/god-review-results.md
```

结构性缺项、重复项、英中 TextDB key 集不一致、称号槽位损坏、身份 accessor
缺失或死亡消息使用本地化神名都会使脚本非零退出。措辞与拓扑待审查项保留完整
身份和证据，但不冒充结构性解析失败。
