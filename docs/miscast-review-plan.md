# Issue #56 R4 miscast 动态消息全量审阅计划

## 冻结边界

- 上游总览：Issue #40 R4；执行入口：Issue #56。
- 精确基线：`aaafab60aff68e631df0fd2b6136075166045267`。
- Glossary SHA-256：
  `95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407`。
- 本批规范身份是生产 SpeakDB 中 history 触及 `database/miscast.txt` 或
  `database/zh/miscast.txt` 的完整 effective key 集，不纳入其他动态消息库。
- EN 与 ZH 的生产 source manifest 中，`miscast.txt` 都位于 load index 9；33 个
  definition 的有效来源均为该文件，history 长度均为 1，没有 override。
- `miscast_inventory.py` 是窄域 entry/spec。exact-Git source manifest、normalized
  snapshot、TextDB 定义解析、merge、weighted variant 派生、artifact schema、hash
  与安全输出均复用 `monflee_inventory.py` 的既有实现；只把既有 scoped 派生入口
  参数化为可传 `source_basename`，没有复制第二套 TextDB parser。

## 冻结 inventory

身份集合是以下 11 个 school 与三个 target role 的笛卡尔积，顺序也按此冻结：

- school：`conjuration`、`hexes`、`summoning`、`necromancy`、
  `translocation`、`fire`、`ice`、`air`、`earth`、`alchemy`、
  `forgecraft`；
- target role：`player`、`monster`、`unseen`。

因此共有 33 个 identity、193 个有序 weighted variant、25 个随机选择站点。
计数不能替代集合证明：consumer 同时核对完整 key 集、definition 顺序、每个
variant locator、ordinal、weight、raw pattern 与随机选择站点的顺序和每站
alternative 数量。重复、缺失、额外或乱序一律 fail closed。

基线 production artifact 的字节哈希为：

| 输入 | SHA-256 |
|---|---|
| EN TextDB production dump | `0e539d83c66ace3522e97fe8f7d67fd06766c4953b273f1bab0e31a35f18c1b4` |
| ZH TextDB production dump | `cea58e23a18ccee902e76340ac7d42a00680dc175548189cb872d1695a4a2299` |

supplied artifact 的完整 source manifest/order/snapshot 必须与该 exact Git OID
重新派生的结果逐对象一致；scoped history、raw body、parse result 与 weighted
variants 也必须逐对象相等。缺文件、解析不完整、parse error、override、未知字段、
布尔值冒充整数、未知 token 或不完整 coverage 均拒绝。

## Producer、consumer 与最终显示

- `database.cc:120-132` 建立英文 SpeakDB source 顺序；localized child TextDB 按
  生产目录枚举顺序加载 ZH 文件。`database.cc:1238-1315,2307-2317` 完成
  localized-first lookup、fallback 与 weighted selection。
- `spl-miscast.cc:34-47` 先要求玩家可见目标格，再以
  `spelltype_long_name_en(which)` 和 `player`／`monster`／`unseen` 生成稳定英文
  lookup key。实体不可见但目标格可见时使用 `unseen`；目标格不可见则不显示。
- `spl-miscast.cc:49-57` 只直接展开 `@hand@`、`@hands@` 与
  `@hand_conj@`。`spl-miscast.cc:59-61` 对 monster 调用
  `do_mon_str_replacements`；该路径在 `mon-util.cc:4316` 完成方括号选择，并在
  `mon-util.cc:4418-4421,4499` 展开 monster possessive 槽（包括
  `@possessive@`）。非 monster 则由 `spl-miscast.cc:68-70` 仅完成方括号选择。
- `spl-miscast.cc:72` 将 asset pattern 与
  `attack_strength_punctuation(dam)` 拼接后送入最终 `mpr`。asset 本身不得携带
  末尾标点。`BEAM_NONE` school 的 asset 消息固定传 0；其中 Earth 在该固定句号
  消息之后才由 special effect 做三倍 AC 检定并以 `BEAM_FRAG` 结算伤害。
  非 `BEAM_NONE` 的伤害 school 才把抗性调整后的最终伤害传给消息标点。
- 本批不改变 lookup key、fallback、RNG、damage、channel 或最终 sink。

## Token 与随机选择协议

大小写、出现顺序和重复次数都是协议的一部分。三类 colour token 是递归
SpeakDB 引用：

- `@any_colour@`
- `@any_colour_pattern@`
- `@any_glowing_colour@`

它们必须分别解析到 EN/ZH production source order 中的 effective
`colourname.txt` 定义，且不得有 override。其余允许 token 是调用方展开槽：
`@The_monster@`、`@The_monster_possessive@`、`@the_monster@`、
`@the_monster_possessive@`、`@hands@`、`@hand_conj@`、`@possessive@`；
这些 key 不得意外成为 SpeakDB effective entry。

唯一 token-topology 例外是 `miscast:ice miscast player` ordinal 2：英文为
`@hands@, @hand_conj@`，中文只保留 `@hands@`。`@hand_conj@` 是英语单复数
动词屈折槽，中文有意省略。例外按完整 identity + ordinal + 英文 token shape
精确绑定，不能泛化到同 key 其他 variant 或其他 identity。

25 个随机选择站点逐站保留顺序和 alternative 数量；中英文 alternative 文本可因
语言不同而变化，方括号不平衡、嵌套、站点增删或 alternative 数漂移均拒绝。

## Bodyless 现状与候选策略

`spl-miscast.cc:62-65` 的现有 bodyless cleanup 只替换英文 literal
`"'s body"` 与 `"'s skin"`。本批没有修改该 C++，也不声称中文依赖或获得了
新的 locale-aware cleanup。

五个精确 locator 为：

1. `hexes miscast monster` ordinal 4；
2. `hexes miscast monster` ordinal 5；
3. `fire miscast monster` ordinal 2；
4. `ice miscast monster` ordinal 1；
5. `alchemy miscast monster` ordinal 6。

候选 ZH 在这五项保留原 possessive token 的大小写、顺序和数量，只用已审定的
“周身／外表”资产表达规避 literal `身体`／`皮肤`，因此不依赖英文 cleanup。
validator 对这五个 locator 逐项要求候选不含 `身体|皮肤`；它还对所有候选禁止
possessive token 后重复追加“的”。这是一项 asset 约束，不是 runtime 修复。

## Strict ledger 与候选边界

`docs/miscast-review-results.md` 的 strict JSONL block 必须满足：

- metadata 精确绑定 baseline、glossary、EN/ZH production dump hash、33 identity、
  193 variant、25 choice site、唯一 grammar exception 与终态结论计数；
- 33 张 card 按 production identity 顺序完整出现一次；每张 card 的 current EN/ZH、
  provenance、history、weights、token arrays、choice counts、target role、visibility、
  punctuation 与 consumer evidence 都与 inventory 相等；
- 193 个 variant review 按 ordinal 完整出现一次，逐 variant 绑定英文、基线中文、
  proposed 中文、weight、token、choice site、body strategy、grammar exception 与终态；
- `keep` 必须逐字保留；`adjust`／`retranslate` 必须实际改变；不接受 pending 或
  未完成 deferral。

候选模式要求：candidate ref 是完整小写 commit OID，与 checkout HEAD 精确相等；
checkout 包括 untracked file 在内必须 clean；baseline 必须是 candidate ancestor；
EN/ZH candidate production artifacts 必须再次通过 exact-Git 派生。candidate EN
不得漂移，candidate ZH 必须逐 identity、逐 variant 与 ledger proposed 完全一致。

## 验收标准到测试映射

| 验收项 | 机械证据 |
|---|---|
| exact-Git source/order/snapshot 与共用 parser | `test_exact_git_inventory_and_checked_in_ledger_pass`、`test_shared_derivation_is_parameterized_without_a_second_parser` |
| 完整 33/193/25、identity/variant/order/weight | positive integration；card/variant coverage mutation tests |
| unknown field、bool-as-int、extra/missing/duplicate fail closed | `test_unknown_fields_fail_closed_at_every_ledger_level`、`test_boolean_integer_fields_fail_closed`、`test_card_and_variant_coverage_duplicate_extra_missing_fail` |
| token case/order/count 与唯一 `@hand_conj@` 例外 | `test_token_exception_is_exact_and_other_token_drift_fails` |
| recursive colour 与 caller token 分类 | `test_recursive_and_caller_token_classification_fails_closed` |
| 25 choice site shape 与五个 body-neutral locator | `test_choice_shape_and_all_five_body_locators_are_enforced` |
| candidate proposed 逐 variant 一致 | `test_candidate_must_match_every_proposal_variant` |
| exact HEAD 与 clean checkout | `test_candidate_checkout_requires_exact_head_and_clean_tree` |

`test_monflee_inventory.py` 继续覆盖共用 exact-Git/weighted 派生的既有 24 项回归。
`verify_zh.sh` 的 message-overlay static dispatcher 增加 miscast focused suite，风险列表
和 review verification control-plane contract 同步纳入新 entry 与测试。

## 明确排除

- 不修改 `spl-miscast.cc`、`spl-miscast.h` 或任何 runtime C++。
- 不为 bodyless cleanup 新增 helper、locale 分支或 schema。
- 不修改英文 lookup key、TextDB parser、weighted/random chooser、fallback、伤害或标点。
- 不创建第二套全局 parser、ledger schema、final gate、持久状态或目录层级。
- 不把其他 SpeakDB source、其他翻译批次或无关清理纳入 Issue #56。

## 重建入口

先在 HEAD 精确等于目标 OID 且 clean 的 checkout 中生成 production EN/ZH dump，
再运行窄域 consumer。输出必须是新的 `/tmp` 或 `/private/tmp` 直接子文件：

```bash
python3 .claude/scripts/miscast_inventory.py \
  --baseline-ref aaafab60aff68e631df0fd2b6136075166045267 \
  --english-dump /private/tmp/miscast-baseline-en.json \
  --localized-dump /private/tmp/miscast-baseline-zh.json \
  --review-results docs/miscast-review-results.md \
  --inventory-output /private/tmp/miscast-inventory-issue56.json
```

候选提交后增加 `--candidate-ref`、`--candidate-english-dump` 与
`--candidate-localized-dump`，在 clean candidate checkout 中证明 descendant、
artifact 与 ledger proposal 的逐 variant 一致。
