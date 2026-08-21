# miscname 全量审核计划（Issue #87）

## 冻结边界

- 基线：`89b97ae826e1a065b9cdc9b1b715883c7eaa4d3d`。
- 生产加载：`database.cc` 的 `TextDB("misc", "database/", ...)`，其中
  `miscname.txt` 是第一项；双语证据来自完整 MiscDB phase-0 dump，而
  identity 只取 effective provenance 命中 `miscname.txt` 的定义。
- 英文/中文源：`crawl-ref/source/dat/database/{,zh/}miscname.txt`。
- 稳定 identity 使用英文生产 lookup key；全集、变体数和不对称项均由
  inventory 从 exact-Git dump 重生成，不以本文计数作为成员权威。
- 术语权威：`docs/glossary.md`，SHA-256
  `366e807eaae5403b6c3925df5970cd237b447ead76fdb717b71273473b5db67e`。

## 消费与生命周期

- `spl-summoning.cc::cast_summon_horrible_things` 直接查询
  `summon_horrible_things`；基线中文只有 `SHT_int_loss`，因此中文子库
  miss 后回退英文父库。候选必须使用真实英文 lookup key。
- `traps.cc` 查询 `harlequin_trap_lines`，结果作为
  `%s%s的攻击被注入了混乱！` 的句首片段。
- `main.cc::_announce_goal_message` 查询 `welcome_spam + suffix`；现有可达
  定义为基本、`dungeon descent` 与 `Halloween`，`Hints` 没有专用定义，
  inventory 将其记作已知 missing lookup，但不伪造翻译 identity。
- `stairs.cc::_hell_effects` 在 quiet/noisy 两个键间选择；quiet 内含一个
  `you.can_smell()` Lua 站。
- `_great_adj_`、`_halloween_things_`、`_lowly_` 仅由 welcome 键递归
  展开；其余为直接生产根。所有成员必须从根键闭包可达。

## 基线缺陷与候选标准

基线冻结三类结构缺陷：不可达的 `SHT_int_loss` 别名、`_great_adj_`
缺少一个英文对应变体、`hell_effect_noisy` 缺少最后一条英文对应消息。
候选必须同时满足：

1. 双语 key 集完全相等，且等于基线英文稳定 identity 集；
2. 逐键变体数、顺序、权重、递归 token 顺序、随机站结构与 Lua 站数量
   完全相等；
3. 英文 proposal 等于基线英文，中文逐 identity 等于严格账本批准 digest；
4. exact-Git 消费者、MiscDB 加载顺序与 localized→English fallback 形状不变；
5. 每个 identity 恰有一张证据卡和一个终态，无未解释 defer。

## 顺序与非目标

按共享依赖顺序审核：三个递归片段 → welcome 基本/模式/万圣节 → 召唤
骇物 → 丑角陷阱 → quiet/noisy 地狱消息。只修改中文 `miscname.txt` 和
本域的库存/证据/覆盖文档；不修改英文文本、RNG、消费者、TextDB 协议，
也不取得其他 MiscDB 文件的所有权。

## 可复现验证

先分别生成基线和候选的完整 EN/ZH MiscDB phase-0 dump，再运行：

```bash
python3 .claude/scripts/miscname_inventory.py \
  --baseline-ref 89b97ae826e1a065b9cdc9b1b715883c7eaa4d3d \
  --english-dump /tmp/miscname-baseline-en.json \
  --localized-dump /tmp/miscname-baseline-zh.json \
  --review-results docs/miscname-review-results.md \
  --candidate-ref <candidate> \
  --candidate-english-dump /tmp/miscname-candidate-en.json \
  --candidate-localized-dump /tmp/miscname-candidate-zh.json \
  --inventory-output /tmp/miscname-candidate-inventory.json
```

随后只运行匹配本批的 `verify_zh.sh --profile translation`；干净提交由
机械 reviewer routing、单次 final gate 与 merge-time gate 接管。
