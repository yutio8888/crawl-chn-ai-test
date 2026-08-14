# Shout/Insult 全量审核计划（Issue #69）

## 冻结边界

- 基线：`3d67767ee477f543c4e6db9a17981aae40a75307`
- 英文生产源：`crawl-ref/source/dat/database/shout.txt`（469 行）、
  `crawl-ref/source/dat/database/insult.txt`（1260 行）
- 中文生产源：`crawl-ref/source/dat/database/zh/shout.txt`（464 行）、
  `crawl-ref/source/dat/database/zh/insult.txt`（1153 行）
- 身份全集：124（shout 91 + insult 33）；英文 675 个加权变体，中文
  650 个加权变体；8 个 key 变体数不对称（give_up 30/29、insult
  general adj1 78/72、insult general adj2 70/65、insult general noun
  103/84、insult mummy adj2 18/17、insult mummy noun 15/14、insult
  vampire adj2 11/12、run_away 27/34）；17 个 token-multiset drift
  定位点（由 inventory 从基线 dump 派生）。
- 术语权威：`docs/glossary.md`，SHA-256
  `95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407`。

消费链（冻结）：`shout.cc::monster_shout` 按 `default_msg_keys`
（26 键）、`DESC_DBNAME` 怪物名键、`pandemonium lord` 与字形
（`'&'`/`'cap-G'`/`'cap-J'`）查询 ShoutDB → `do_mon_str_replacements`
展开（`@The_monster@`/`@The_monster_possessive@`/`@possessive@`/
`@says@`/`@subjective@` 等）→ 声音/视觉频道显示；
`transform.cc::getShoutString("Sphinx riddle …")` 查询三个 Sphinx
谜语根键；insult.txt 双载（ShoutDB index 1 / SpeakDB index 4），
`mon-util.cc::_get_species_insult` 经 `@species_insult_*@` 走
SpeakDB 后处理路径解析 12 个 `insult <species>` 键与 `small_food`。

## 递归与外部 token 闭包

- ShoutDB 递归片段：`@demon_taunt@`（→ShoutDB insult 键）、`@imp@`、
  `@imp_taunt@`、`@possessive@`、`@says@`、`@_riddle_adj_@`、
  `@_riddle_fail_acknowledged_@`、`@_riddle_fail_general_@`、
  `@_riddle_prefix_@`；
- insult 递归链：`@generic_insult@`、`@demon_taunt_special@`、
  `@give_up@`、`@run_away@`、`@run_or_give_up@`、`@insult_noun@`、
  `@species_insult_noun@`、`@body_or_spiritual_part@`、
  `@important_body_part@`、`@important_spiritual_part@`、
  `@feast_or_devour@`、`@meal@`、`@small_food@`、`@whilst_thou_can@`、
  `@will_or_shall@` 等；
- `@__DEMON_TAUNT@` 等 `__XXX` 回退标记与 `__NONE`/`__DEFAULT`/
  `__NEXT` 哨兵保留；`__BUGGY` 是唯一的 in-file sentinel key；
  `#### Player sphinx riddle lines` 标题块是解析产物空 key，永不成为
  identity。
- 全部 token 在候选落地中原样保留；审计器要求逐变体 token 多重集、
  权重序列、随机站数量与 Lua 站数量 EN/ZH 完全一致。

## 基线缺陷与验收标准

基线允许且只允许以下已冻结缺陷（数量由 inventory 从基线 dump 派生）：

1. 8 个不对称 key（见冻结边界）：中文侧无源多余变体（run_away +7、
   insult vampire adj2 +1）或中文侧缺失变体（其余 6 键）。
2. 17 个 token-multiset drift 定位点，全部由中文侧独立改写产生：
   - shout 13 处：`'cap-g'`、`__cherub seen`（0–3）、
     `__faint_skitter seen`、`__rustle seen`、`__skitter seen`、
     `ballistomycete spore`、`giant slug`、`glowing orange brain`、
     `moth of wrath`、`player ghost` —— 中文侧省略
     `@possessive@` 或把 `@The_monster_possessive@` 改写为
     `@The_monster@`＋“的”；
   - insult 4 处：`insult mummy adj2`（16，计数不对称导致的错位）、
     `insult spriggan noun`（0、16，`@small_food@` 被移到末尾）、
     `insult vampire adj2`（10，计数不对称导致的错位）。
   - 无纯 token 顺序漂移；严格候选门要求逐点对齐多重集。
3. 除上述冻结缺陷外，`Polyphemus` 中文引号错用（开引号用了
   U+201D），`__moan` 将 chilling 误作 凄凉，`demon_taunt_special`
   第 3 变体 `@run_away@` 与 `@whilst_thou_can@` 之间缺连接标点。

候选必须满足：

1. 124 个身份各有且仅有一张严格审核卡；每张卡完整绑定当前 EN/ZH
   变体和拟议 EN/ZH 变体、权重、证据与结论。
2. 双语各 124 个 key；逐键变体数与权重序列一致；双语加权变体总数
   相等（675/675）。
3. 123 个 live/递归身份双语从消费根键可达；1 个 AXED_MON legacy 身份
   （`giant slug`）无 live producer/入边引用，分类为
   legacy-axed-monster 并显式豁免可达性；无悬空 token、解析错误、空
   body；`__BUGGY` 保持每语言恰好 1 个变体；`#### Player sphinx
   riddle lines` 标题块永不成为 identity。
4. 仅允许严格账本明确批准的文本、权重、顺序与 token 变化；英文与
   中文候选必须逐字等于账本 proposal。
5. 除 I69-R4-CODE-001 的 canonical-English 消费者修复外，不修改消费者
   逻辑：该修复仅把 shout.cc::_shout_key 与 mon-util.cc::
   do_mon_str_replacements 的 ShoutDB/SpeakDB 查询身份改用英文访问器
   （mons_type_name_en / species::name raw=true），不触碰随机选择
   算法、RNG 调用拓扑或 SpeakDB 双载语义；英文源保持基线逐字不变
   （本批无恢复 EN 的裁决）。

## 8 个不对称 key 裁决规则

- 候选必须做到逐键 EN/ZH 变体数一致（124/124 键、双语变体总数
  675/675）。
- 裁决方向逐键举证（默认 EN 权威）：
  - `run_away`（27/34）与 `insult vampire adj2`（11/12）：中文侧
    存在无源多余变体 → **删除 ZH 多余变体**（run_away 删 7 个、
    vampire adj2 删 1 个），权重序列对齐；
  - `give_up`（30/29）、`insult general adj1`（78/72）、`insult
    general adj2`（70/65）、`insult general noun`（103/84）、
    `insult mummy adj2`（18/17）、`insult mummy noun`（15/14）：
    **补译 ZH 缺失变体**（分别 +1/+6/+5/+19/+1/+1），并删除中文侧
    无源重复/游离变体（give_up 删 7 个无源变体、以精确译文替换
    2 个错配变体）；
  - 权重序列逐键一致；`w:N` 权重标记原样保留。
- 英文源保持基线逐字不变；英文 proposal 与基线相同。
- 17 个 drift 定位点逐点裁决：中文侧补回 `@possessive@`（“将
  @possessive@目光转向你”等）或改用 `@The_monster_possessive@`
  （运行期渲染结果与基线逐字相同，仅 token 结构对齐）；insult
  侧由计数对齐与 `@small_food@` 归位自然消除。

## 批次与依赖顺序

1. 谜语碎片（`_riddle_adj_`/`_riddle_prefix_`/`_riddle_fail_*`）与
   Sphinx riddle 根键——先定共享词根；
2. 26 个 `__XXX` 默认键族（`__BARK`/`__ROAR`/`__DEMON_TAUNT` 等，
   逐键核对角色声音，含 `__moan` 修正）；
3. insult 递归碎片（`generic_insult`/`demon_taunt_special`/
   `give_up`/`run_away`/`run_or_give_up`/`insult_noun`/
   `species_insult_noun`/`body_or_spiritual_part`/
   `important_*_part`/`feast_or_devour`/`meal`/`small_food`/
   `whilst_thou_can`/`will_or_shall` 等）；
4. `demon_taunt`/`imp`/`imp_taunt` 恶魔嘲讽族；
5. 怪物名键（`__bark seen` 等后缀物化、player ghost 族、活体怪物
   键、glyph 键）——与 #24 怪物名证据一致；
6. 8 个不对称 key 逐键裁决（默认 EN 权威；删 ZH 无源变体或补 ZH
   缺失变体，权重序列对齐）；
7. 顺序落地 ZH 资产，重新生成双语 shout phase-0 dump，执行候选
   审计，提交，worktree 保持 clean。

## 可复现命令

基线 inventory：

```bash
make -C crawl-ref/source -j4 textdb-phase0-dump \
  TEXTDB_PHASE0_DB=shout TEXTDB_PHASE0_DUMP=/tmp/shout-en.json
make -C crawl-ref/source -j4 textdb-phase0-dump \
  TEXTDB_PHASE0_DB=shout TEXTDB_PHASE0_LANGUAGE=zh \
  TEXTDB_PHASE0_DUMP=/tmp/shout-zh.json
python3 .claude/scripts/shout_inventory.py \
  --baseline-ref 3d67767ee477f543c4e6db9a17981aae40a75307 \
  --english-dump /tmp/shout-en.json \
  --localized-dump /tmp/shout-zh.json \
  --inventory-output /tmp/shout-inventory.json
```

候选阶段使用新的 `/tmp` 文件名重新生成双语 dump，并在同一命令追加
`--review-results`、`--candidate-ref <新提交>` 与两份 candidate
dump，重新证明 candidate agreement（候选必须逐字等于账本 proposal、
124/124 键、双语变体数逐键一致、无未解析 token、闭包完整）。
翻译资产编辑阶段可按需使用 `bash .claude/scripts/verify_zh.sh
--profile translation`；本候选是混合改动（Python 验证代码、database.cc/
database.h、Catch2 测试与 ZH 资产），合并前的静态预检只执行一次
`bash .claude/scripts/verify_zh.sh --profile ci`（ci 是 translation ∪
code 的 union，覆盖 i18n 生命周期/varargs 等代码侧检查），不对同一
不可变候选串行重复跑多个 profile。
