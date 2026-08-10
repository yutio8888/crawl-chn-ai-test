# Issue #54 R4 monflee 动态消息全量审阅计划

## 冻结边界

- 上游总览：Issue #40 R4；执行入口：Issue #54。
- 基线：`5f168f7b1130f9d2ec9c264f27e4ddc9b64d64d6`。
- Glossary SHA-256：
  `95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407`。
- Inventory SHA-256：
  `8fec9feeb418c8d6d641585b46b1f320638f2126d053ea99a2a0485485579de1`。
- 本批只拥有 `database/monflee.txt` 家族。`monspeak`、`monspell`、`shout`、
  `wpnnoise`、`insult`、`miscast`、`graffiti` 与 `decorlines` 均不在本批。
- 规范身份来源是生产 C++ SpeakDB artifact 中 effective source 为
  `database/monflee.txt` 的完整 key 集。Python inventory 先完整验证 supplied
  production artifact，再从 exact Git OID 独立派生 EN/ZH source manifest、
  normalized snapshots，以及所有 history 触及 `monflee.txt` 的 scoped entries；
  派生过程复用 checked-in `_parse_text_db` 语义 helper，只保留窄域 weighted adapter，
  不建立第二套全局 TextDB parser。

## 生产身份与生命周期

生产英文及中文 artifact 都只发现一个稳定 key：

1. `monflee:dream sheep flee`

该 key 是 current-player-visible。常规生产者在怪物受到惊吓、切换为逃跑行为时，
以稳定英文 DB name 拼接 `" flee"` 查询；Xom 梦羊 vault 也会对同一 key 直接调用
speech 入口。它不是已移除、兼容或内部 sentinel。

该 identity 有五个有序变体：权重依次为 `30, 10, 10, 10, 10`。第 0 项无
控制前缀，在 pre-`mprf` emission seam 保持 `MSGCH_TALK`；源怪物
`ENCH_MUTE` 或源格沉默只令 `effective_silence=true`，不阻止该 emission
抵达 `MSGCH_TALK`。最终 sink 只有在玩家所在格沉默时才由
`prepare_message` 抑制这条 `MSGCH_TALK`。第 1–4 项带 `VISUAL:`，
路由至 `MSGCH_TALK_VISUAL` 并清除 silence；它们仅在怪物可见时
产生 emission，且不受该 sink 的沉默抑制。运行时 token 依次为
`@The_monster@`、`@The_monster@`、`@The_monster@`、`@monster@`、
`@The_monster@`。

## 输入摘要

| 精确基线输入 | SHA-256 |
|---|---|
| production EN TextDB artifact | `0e539d83c66ace3522e97fe8f7d67fd06766c4953b273f1bab0e31a35f18c1b4` |
| production ZH TextDB artifact | `0e9f36cd94f72a77bff07f9d5e51ed5dceee6033a021febf185abd2c338c4f2d` |
| `crawl-ref/source/dat/database/monflee.txt` | `e0a0c784aee53ef7759311263fa9219665c0396f6328fa23166b48a1813f6ee9` |
| `crawl-ref/source/dat/database/zh/monflee.txt` | `c8af497389f6c30127a656fe153c45a021b41e552f2023fe13e3833426c8a255` |
| `crawl-ref/source/database.cc` | `0ce343d8f888d00c99bee4d0ebbcee39d0399d997830011de1dc1878a4165d2c` |
| `crawl-ref/source/database.h` | `cf9e39ab5bc35b9f8e8f1f7889d70a16f9262193ecdedb5fb11054e5dbd6dd0b` |
| `crawl-ref/source/mon-behv.cc` | `f069b4e708100083522a3c92b72bf0d96c809dee794f39f8be0d11be9d3a6604` |
| `crawl-ref/source/mon-speak.cc` | `830135c6443896b707096d055a0ce534a7eec1c9059e43381463bd9f8f8584df` |
| `crawl-ref/source/dat/des/altar/xom_sheep.des` | `aa28e0c171ab980d7db29ae01f0fe331531718c2fe37414328a025da4b5096ae` |
| `docs/glossary.md` | `95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407` |

Production artifact 的完整 source manifest、顺序与 normalized snapshots 必须与
这些文件所在的精确 Git OID 绑定；consumer 还从完整 source 序列独立重建所有
history 触及 `monflee.txt` 的 entry，并逐对象核对 provenance、raw body、parse
result 与 variants。它不宣称重建或验证 artifact 中与本批无关的 entry。

## Producer、consumer 与显示边界

- `database.cc:120-132` 将 `monflee.txt` 纳入 SpeakDB；
  `database.cc:944-968,1017-1068` 通过生产 parser 输出 EN/ZH typed artifact。
- `database.cc:1238-1260,2307-2317` 优先查询 localized SpeakDB，缺失时回退英文，
  并使用生产 weighted chooser。
- `mon-behv.cc:1271-1297,1399-1401` 在 `ME_SCARE` 中查询
  `mon->name(DESC_DBNAME) + " flee"`，随后切换逃跑行为，并把源格
  沉默状态传入 `mons_speaks_msg`。
- `dat/des/altar/xom_sheep.des:42-44` 对可见的 Xom 梦羊直接查询同一稳定 key。
- `mon-speak.cc:851-912` 展开 `@...@` token 并剥离控制前缀。无前缀项
  保持 `MSGCH_TALK`；`ENCH_MUTE` 或上游传入的源格沉默只在
  pre-`mprf` seam 标记 `effective_silence`。`VISUAL:` 改路由为
  `MSGCH_TALK_VISUAL`、清除 silence，并在怪物不可见时取消 emission。
- `message.cc:1568-1585,1835-1848` 是 `mprf` 后的最终消息 sink；
  `prepare_message` 只在玩家所在格沉默时抑制 `MSGCH_TALK`，
  不抑制 `MSGCH_TALK_VISUAL`。
- 现有 Catch2 observer 挂在 `mon-speak.cc:904-911` 的 pre-`mprf` 分支，
  直接证明 channel、`effective_silence` 与可见性 emission，不直接证明
  最终 `mprf` 显示；后者由上述静态调用链证明。

## 验收标准

1. Production EN/ZH artifact schema 与 exact-OID source manifest/order/snapshots
   严格验证；所有 history 触及 `monflee.txt` 的 key、provenance、raw body、parse
   result、variant locator、ordinal、weight 与 raw pattern 均独立派生并逐对象核对；
   parse error、override、重复 identity、ordinal gap 或未识别控制前缀 fail closed。
2. EN/ZH key 集相等；每个 key 的 variant 数、顺序、权重、控制前缀与大小写敏感
   runtime token topology 相等。
3. 每个 identity 恰有一张 evidence card 和一个终态结论；卡中五个 variant
   review 与 production locator 一一对应。
4. 每个 variant 核对英文含义、中文语义、角色声音、声音／视觉通道、可见性、
   沉默行为与最终消息后果。
5. 中文修改不得改变 DB key、`w:N`、`VISUAL:`、`@...@`、变体数、顺序或权重。
6. Baseline current、人工 proposed 与 exact candidate production artifact 完全一致；
   inventory/review/candidate 双向覆盖相等。
7. Python inventory 单测与 production speech Catch2 均通过；混合候选只运行一次
   matching development profile，然后进入机械 routing、双 readiness、单次 final
   gate、GitHub CI 与 merge-time validation。

## 依赖组与人工确认

唯一依赖组是 dream sheep flee 五个变体。第 0 项校准梦羊声音；第 1、2 项作为
冻结 `keep` 对照；第 3、4 项校准惊恐跳跃／奔逃动作。必须在同一批完整检查后
才能落地任何角色声音改写。

## 明确排除

- 不修改怪物逃跑 AI、触发条件、目标选择、概率或 RNG。
- 不修改英文 DB lookup key、production TextDB parser、fallback 或随机选择算法。
- 不把其他动态消息库、云雾/卡牌/R3 已审 identity 或 `source.txt` 纳入本批。
- 不创建第二套全局 ledger、parser、最终门禁或持久协调状态。

## 重建入口

先在 HEAD 精确等于目标 OID 且 clean 的独立 checkout 中，由 production C++ 生成
EN/ZH artifact，再交给窄域 consumer。consumer 不执行或信任当前 worktree binary；
它用 `--baseline-ref` 从 Git object database 独立派生 scoped evidence 并 cross-check
supplied artifact：

```bash
make -C crawl-ref/source -j4 textdb-phase0-dump \
  TEXTDB_PHASE0_DUMP=/tmp/monflee-baseline-en.json
make -C crawl-ref/source -j4 textdb-phase0-dump \
  TEXTDB_PHASE0_LANGUAGE=zh \
  TEXTDB_PHASE0_DUMP=/tmp/monflee-baseline-zh.json
python3 .claude/scripts/monflee_inventory.py \
  --baseline-ref 5f168f7b1130f9d2ec9c264f27e4ddc9b64d64d6 \
  --english-dump /tmp/monflee-baseline-en.json \
  --localized-dump /tmp/monflee-baseline-zh.json \
  --inventory-output /tmp/monflee-inventory-issue54.json
```

候选落地后增加 results、candidate ref 与 candidate EN/ZH artifact 参数，重新证明
candidate agreement。所有输出使用新的 `/tmp` 文件名，不覆盖旧证据。
