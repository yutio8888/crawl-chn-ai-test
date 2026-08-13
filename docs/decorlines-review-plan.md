# Decorlines 全量审核计划（Issue #67）

## 冻结边界

- 基线：`306d9099ae08a94a64f051d487dfed0a9675e178`
- 英文生产源：`crawl-ref/source/dat/database/decorlines.txt`
- 中文生产源：`crawl-ref/source/dat/database/zh/decorlines.txt`
- 身份全集：两侧各 132 个唯一 canonical key；英文 209 个加权变体，
  中文 266 个加权变体；63 个 key 变体数不对称。
- 术语权威：`docs/glossary.md`，SHA-256
  `95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407`。

消费链（冻结）：`directn.cc::_walk_on_decor` → `getMiscString` 多级 key
回退 → `maybe_pick_random_substring` → `@your_weapon@`/`@your_hands@`
（`C_("decor possessive", "your")`，zh/source.txt 已有键）→
`do_mon_name_replacements` → `mprf(MSGCH_DECOR_FLAVOUR)`。

## 递归与外部 token 闭包

- 递归内部片段（4 个）：`@_baked_good_and_reaction_@`、
  `@_fruit_and_reaction_@`、`@_meat_and_reaction_@`、`@sparkling_message@`；
- 外部 MiscDB 查找：`@any_graffiti@`（#66 冻结闭包）、`@any_colour@`、
  `@any_colour_pattern@`；
- 消费者后处理：`@your_hands@`、`@your_weapon@`；
- 全部 token 在候选落地中原样保留；审计器要求逐变体 token 多重集与
  顺序、权重序列、随机站（`[a|b]`）数量与 Lua 站数量 EN/ZH 完全一致。

## 基线缺陷与验收标准

基线允许且只允许以下已冻结缺陷（数量由 inventory 从基线 dump 派生）：

- 63 个不对称 key：约 50 个 species/form cache 键 EN 1/ZH 2（中文侧
  多一条无源中文新增变体，且 canonical 英文变体原样未译）、
  `blade fruit/meat cache`、`draconian fruit cache`、`dragon fruit cache`、
  `spriggan meat cache`、`vampire fruit cache` EN 2/ZH 3、`felid fruit cache`
  EN 3/ZH 4、`default fountain_blood` EN 5/ZH 4、`default peaceful
  fountain_sparkling` EN 2/ZH 1、`wu jian peaceful fountain_blue`
  EN 2/ZH 1；
- `default fountain_blood`：Lua 块与蚊子行被合并进同一个变体；
- `default peaceful fountain_sparkling`：Lua 块与 `w:1` 涂鸦行被合并进
  同一个变体；
- 57 个变体 body 的 token 多重集漂移（`baseline_token_multiset_drift`，
  全部由上述结构缺陷产生：无源新增变体无 token 而英文有、英文原样
  变体残留、`short * cache` 中文侧用根键引用代替片段引用）；
- 术语漂移：`Dungeon→副本`（应为 地牢）、`Pandemonium→深渊`（应为
  万魔殿）、`adder→毒蛇`（应为 蝰蛇）、`spriggan→精灵`（应为 小精灵，
  与 elven 冲突）、`tengu→鸟人`（应为 天狗）、`naga→娜迦`（应为 纳迦）。

候选必须满足：

1. 132 个身份各有且仅有一张严格审核卡；每张卡完整绑定当前 EN/ZH
   变体和拟议 EN/ZH 变体、权重、证据与结论。
2. 双语各 132 个 key；逐键变体数与权重序列一致；双语加权变体总数相等。
3. 双语从消费根键可达全部 132 个键；无悬空 token、解析错误、空 body；
   `jiyva peaceful fountain_blue` 的双重定义是唯一被冻结的 override。
4. 仅允许严格账本明确批准的文本、权重、顺序与 token 变化；英文与
   中文候选必须逐字等于账本 proposal。
5. 不修改消费者逻辑、随机选择算法或 RNG 调用拓扑。

## 63 个不对称 key 裁决规则

- 候选必须做到逐键 EN/ZH 变体数一致（132/132 键、双语变体总数相等）。
- 裁决方向逐键举证：
  - EN 1/ZH 2 与 EN 2/ZH 3、EN 3/ZH 4 的 species/form cache 键：经仓库
    全史 pickaxe 与上游 0.34.1 标签核对，中文侧额外变体
    （“你低头嗅了嗅……”“你倒挂着……”“你从……上方飘过……”等）
    在 EN 任何版本中均无对应源，属无源新增 → **删除 ZH 多余变体**；
    canonical 英文变体在中文侧残留为英文原样 → 补译为中文。
  - EN 2/ZH 1 与 EN 5/ZH 4（`default peaceful fountain_sparkling`、
    `wu jian peaceful fountain_blue`、`default fountain_blood`）：
    **恢复 ZH 缺失变体（补译/拆分）**。
- 英文源保持基线逐字不变（本批无恢复 EN 的裁决）；英文 proposal 与
  基线相同。
- 权重序列必须逐键一致；`[a|b]` 随机站数量与 Lua 站数量 EN/ZH 一致。

## 批次与依赖顺序

1. 递归内部片段（`_baked_good_and_reaction_`/`_fruit_and_reaction_`/
   `_meat_and_reaction_`）与 `sparkling_message`——先定共享词根；
2. 喷泉键族（default、各 god fountain 键、`default fountain_blood` 与
   `default peaceful fountain_sparkling` 的结构拆分）；
3. 根缓存键（fruit/meat/baked goods cache）；
4. species/form cache 键族——同一 species 三类缓存术语一致；
5. 其余独立键（ashenzari 地牢术语、cheibriados 润色等）；
6. 顺序落地 ZH 资产，重新生成双语 misc phase-0 dump，执行候选审计；
7. `verify_zh.sh --profile translation`，提交，worktree 保持 clean。

## 可复现命令

基线 inventory：

```bash
make -C crawl-ref/source -j4 textdb-phase0-dump \
  TEXTDB_PHASE0_DB=misc TEXTDB_PHASE0_DUMP=/tmp/decorlines-misc-en.json
make -C crawl-ref/source -j4 textdb-phase0-dump \
  TEXTDB_PHASE0_DB=misc TEXTDB_PHASE0_LANGUAGE=zh \
  TEXTDB_PHASE0_DUMP=/tmp/decorlines-misc-zh.json
python3 .claude/scripts/decorlines_inventory.py \
  --baseline-ref 306d9099ae08a94a64f051d487dfed0a9675e178 \
  --english-dump /tmp/decorlines-misc-en.json \
  --localized-dump /tmp/decorlines-misc-zh.json \
  --inventory-output /tmp/decorlines-baseline-inventory.json
```

候选阶段在同一命令追加 `--review-results`、`--candidate-ref <新提交>` 与
两份 candidate misc dump，重新证明 candidate agreement（候选必须逐字等于
账本 proposal、132/132 键、双语变体数逐键一致、无未解析 token、闭包
完整）。所有输出使用新的 `/tmp` 文件名，不覆盖旧证据。
