# Monspeak 全量审核计划（Issue #70）

## 冻结边界

- 基线：`b3ad4425053c2175284d32441d67218df97035b0`
- 工具化提交（本批起点）：`a5eac7dd0e22327f4f8b7ed51b0276c1e0087638`
- 英文生产源：`crawl-ref/source/dat/database/monspeak.txt`
  （9276 行，SpeakDB index 0）
- 中文生产源：`crawl-ref/source/dat/database/zh/monspeak.txt`
  （11741 行）
- 身份全集：733（EN 731 + ZH-only 2：`_jory_rare_`、`default 'j'`）；
  英文 3429 个加权变体，中文 3407 个加权变体；**213 个不对称 key**
  （精确清单在 `monspeak_inventory.py` 的 `EXPECTED_ASYM`，由基线
  dump 逐键推导，不来自任何文档）。
- 术语权威：`docs/glossary.md`，SHA-256
  `95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407`。

消费链（冻结）：`mon-speak.cc::mons_speaks` 经
`getSpeakString("<prefix> <base> <suffix>")` 查询 SpeakDB，`default `
回退链（mon-speak.cc:233/271），基键为怪物 DB 名 / `player ghost` /
`pandemonium lord` / 字形键（`mons_base_char` 的 `'x'`/`'cap-x'`）/
`get_mon_shape_str` 形状键；后缀 `triumphant/banished/killed/
permanently killed/timeout`；固定消费点包括 mon-death.cc（Dowan/
Duvessa 双胞胎死亡键与 `twin_*` 前缀）、attitude-change.cc
（`beogh_converted_orc_*`、Gozag 贿赂）、mon-abil.cc
（`nobody_recollection <key>`）、god-companions.cc / god-abil.cc /
monster.cc（使徒、兽人祭司、Maurice、傀儡）、transform.cc
（`<name> riddle`）、mon-cast.cc（`<name> blink_other[_close]`/
`charge`/`branch summon cast prefix`）、spl-goditem.cc（圣化安抚）、
player-reacts.cc（`recite_closure`）、mon-util.cc（`_laughs_`）与
mapdef.cc 的 `dbname:`/`name:` 标签；展开经
`mon-util.cc::do_mon_str_replacements` 处理（`@The_monster@`、
`@possessive@`（ZH 渲染“它的”）、`@reflexive@`（“它自己”）、
`@subjective@`、`@to_foe@`/`@at_foe@`（必须带前导空格才被替换）、
`@foe,@`、`@at_foe/around@`、`@player_only@` 等）。

## 递归与外部 token 闭包

- 递归碎片：`_<unique>_common_/_rare_/_medium_` 家族、
  `beogh_converted_orc_*` 引用链、`Dowan_Duvessa_*` 死亡链、
  `_generic_Donald_`/`@_generic_orc_speech_@`/`@_wizard_*_@` 等
  326/299（EN/ZH 去重 token 数）；
- 外部/后处理：`Foe_genus`/`Foe_god`/`Subjective`/`The_monster`/
  `The_monster_possessive`/`at_foe` + 5 个跨族 SpeakDB 键
  （`demon_taunt`/`imp_taunt`/`misc_colour`/`orc name`/
  `rainbow_colour`，#69 已冻结）；
- Lua 内联块：比较串（`you.race() == "Felid"`、`you.god() ==
  "Makhleb"` 等）不译，`return` 串可译；Lua 块内不得有空行（空行
  会被生产解析器拆成碎片变体）；`crawl.t_()` 本地化调用保持基线。

## 基线缺陷与验收标准

基线允许且只允许以下已冻结缺陷（数量由 inventory 从基线 dump
派生，审计器逐项校验）：

1. **213 个不对称 key**（EN/ZH 变体数逐键不一致；ZH 侧净缺 318 个、
   净多 296 个变体，双语变体总数 3429/3407）。
2. **191 个 ZH 空变体**（`w:N` 权重行后留空行，生产解析器产生空
   pattern 变体）。
3. **14 个 split-Lua 碎片**（ZH Lua 块内含空行，`{{`/`}}` 被拆成
   孤立碎片，运行时永不执行）：`friendly shoals hound` 3/9、
   `nekomata` 0/6/7/15/16/22、`sprozz` 0/6、`sprozz triumphant`
   0/6、`xak'krixis` 6/11。
4. **15 EN / 39 ZH orphan 键**：EN 15 个（imp-greeting 碎片链与
   5 个陈旧/拼写键）；ZH 额外 24 个（EN 引用在 ZH 侧被内联展开，
   使碎片不可达）。
5. 随机站/Lua 站不对称：EN 47/18 vs ZH 38/5。
6. 其余逐变体漂移：`@to_foe@`/`@at_foe@` 被改写为 `@foe@`、
   `@possessive@`/`@reflexive@`/`@subjective@` 省略、`@foe,@` 丢失
   逗号、大小写漂移（`@the_monster@` vs `@The_monster@`）、无前导
   空格的 `@at_foe@`/`@to_foe@` 运行时泄漏、权重序列错位、随机站
   点被压平、`@_wails_@` 等递归引用被内联、哨兵 `__NONE`/`__NEXT`
   缺失等。

候选必须满足（`monspeak_inventory.py --candidate-ref` 逐项门禁）：

1. 733 个身份各有且仅有一张严格审核卡；每张卡完整绑定当前与拟议
   EN/ZH 变体、权重、结论、理由与证据。
2. 逐键 EN/ZH 变体数、权重序列、逐变体 token 多重集、随机站点拓扑、
   Lua 站点数、split-Lua 拓扑完全一致；双语加权变体总数相等
   （3429/3429）。
3. 无空变体、无未解析 token；ZH orphan 集不得超出基线（只允许通过
   恢复内联引用缩小）；ZH-only 键 `_jory_rare_`/`default 'j'` 必须
   保留（审计强制），裁决为 keep 并记录依据。
4. 候选 EN 逐字等于账本 proposal（本批 EN 保持基线逐字不变，无 EN
   文件改动）；候选 ZH 逐字等于账本 proposal。
5. 除 I70-R4-CODE-001 的 canonical-English 消费者修复外，不修改
   消费者逻辑与其它资产（insult/godspeak/monname/colourname 与既有
   账本）。该修复仅把 mon-speak.cc::mons_speaks 的属类回退查询身份
   从本地化访问器改为 `mons_type_name_en(mons_genus(mons->type),
   DESC_DBNAME)`（与 #69 的 I69-R4-CODE-001 同一模式：中文侧
   本地化名字永远匹配不上英文 monspeak 键，会静默回退到字形/形状
   语音）；不触碰随机选择算法、RNG 调用拓扑或回退链结构，工具与
   基线账本逐字不变。

## 213 个不对称 key 裁决规则

默认 EN 权威：对每个不对称 key，ZH 候选 = 按 EN 逐变体重排/补译/
删除，使变体数、权重序列、token 多重集与 EN 逐位一致。具体分三类：

- **ZH 缺变体（净 318 个）**：按当前 EN 补译（多数为旧版 EN 译文
  错位，需要整键重译；典型如 `_asterion_common_` 13/6、
  `crypt donald` 32/12、`_norris_common_` 14/6、`zot donald`
  21/11、`nekomata` 4/25 的 EN 侧补齐）。
- **ZH 多变体（净 296 个）**：删除无源/重复/空占位变体（典型如
  `_suck_up_adj2_` 4/15、`_crazy_yiuf_sentence_` 3/15、
  `_hostile_imp_rare_` 5/11、`nekomata` 4/25 的 ZH 侧删减）。
- **权重/顺序错位**：按 EN 权重序列逐位对齐（如 `_frog_food_`
  12/15 的空变体删除后权重归位）。

## 批次与依赖顺序

1. unique 家族：`_<unique>_common_/_rare_` 碎片与 `X donald` 神系/
   区域根键——先定专名（术语表：马科列布/比欧弗/伊罗查/艾祖尔等）
   与角色声音；
2. 通用说话家族：`default *` 键族、玩家幽灵（`player ghost`、
   `* player ghost`）、已移除怪物遗留键——先修 191 空变体与 14
   split-Lua 结构；
3. `beogh_converted_orc_*`、兽人祭司、Beogh 使徒与
   Dowan/Duvessa/twin 叙事族——统一 Beogh=比欧弗（基线误用
   “贝奥格”）与双胞胎人设声音；
4. orphan 键裁决（15 EN / 39 ZH）：ZH-inlined 碎片恢复 `@token@`
   引用（`_begs_`、`_friendly_*`、`_silenced_*` 等 24 个），使 ZH
   orphan 集缩小；无恢复目标的孤儿键（imp-greeting 链、
   `no god donald` 等）保留并记录；213 不对称逐键裁决；
5. 剩余独立键（字形键、后缀键、斯芬克斯谜语、Gozag 贿赂、Nobody
   记忆等）与全量语义校对（含结构对齐但译文陈旧的 keep 键，如
   `asterion triumphant`/`boris riddle`/`pikel triumphant`）。

## 可复现命令

基线 inventory：

```bash
make -C crawl-ref/source -j4 textdb-phase0-dump \
  TEXTDB_PHASE0_DB=speak TEXTDB_PHASE0_DUMP=/tmp/monspeak-en.json
make -C crawl-ref/source -j4 textdb-phase0-dump \
  TEXTDB_PHASE0_DB=speak TEXTDB_PHASE0_LANGUAGE=zh \
  TEXTDB_PHASE0_DUMP=/tmp/monspeak-zh.json
python3 .claude/scripts/monspeak_inventory.py \
  --baseline-ref b3ad4425053c2175284d32441d67218df97035b0 \
  --english-dump /tmp/monspeak-en.json \
  --localized-dump /tmp/monspeak-zh.json \
  --inventory-output /tmp/monspeak-inventory.json
```

候选阶段：提交候选后使用新的 `/tmp` 文件名重新生成双语 dump，并在
同一命令追加 `--review-results`、`--candidate-ref <新提交>` 与两份
candidate dump，重新证明 candidate agreement（候选必须逐字等于账本
proposal、733 卡、双语变体数逐键一致 3429/3429、无空变体、无未解析
token、无 split-Lua、orphan 不扩大、闭包完整）：

```bash
make -C crawl-ref/source -j4 textdb-phase0-dump \
  TEXTDB_PHASE0_DB=speak TEXTDB_PHASE0_DUMP=/tmp/monspeak-en-candidate.json
make -C crawl-ref/source -j4 textdb-phase0-dump \
  TEXTDB_PHASE0_DB=speak TEXTDB_PHASE0_LANGUAGE=zh \
  TEXTDB_PHASE0_DUMP=/tmp/monspeak-zh-candidate.json
python3 .claude/scripts/monspeak_inventory.py \
  --baseline-ref b3ad4425053c2175284d32441d67218df97035b0 \
  --english-dump /tmp/monspeak-en.json \
  --localized-dump /tmp/monspeak-zh.json \
  --inventory-output /tmp/monspeak-inventory-candidate.json \
  --review-results docs/monspeak-review-results.md \
  --candidate-ref <新提交> \
  --candidate-english-dump /tmp/monspeak-en-candidate.json \
  --candidate-localized-dump /tmp/monspeak-zh-candidate.json
```

翻译资产编辑阶段按需使用 `bash .claude/scripts/verify_zh.sh --profile
translation`；合并前的静态预检只执行一次 `bash .claude/scripts/
verify_zh.sh --profile ci`，不对同一不可变候选串行重复跑多个 profile。
