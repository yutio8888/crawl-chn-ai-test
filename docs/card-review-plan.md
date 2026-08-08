# Issue #40 R2 卡牌名称与描述全量校对计划

## 冻结边界

- 基线提交：`9fb8e5dd22ef6607613d1c4381b7369f93a08a7e`（`chn-0.34.1-base` HEAD，本轮起点）
- 上游总览：Issue #40 R2；无独立子 Issue 编号时以本计划为执行入口。
- 生产身份源：`crawl-ref/source/decks.h` 的 `card_type` 枚举（25 成员 = 21 现行
  + 3 移除 + `NUM_CARDS` 哨兵；3 个移除成员位于 `#if TAG_MAJOR_VERSION == 34`
  条件块：`CARD_SHAFT_REMOVED`、`CARD_STAIRS_REMOVED`、`CARD_FAMINE_REMOVED`）。
- 名称数据源：`crawl-ref/source/decks.cc` 的 `card_name_en()`（EN 键）与
  `card_name()`（`T_()` / `C_("card name", "Wild Magic")` 显示名）；生命周期
  经 `card_is_removed()` 交叉校验。
- 描述数据源：`crawl-ref/source/dat/descript/cards.txt`（EN）与
  `crawl-ref/source/dat/descript/zh/cards.txt`（ZH），DB 键 =
  `card_name_en(card) + " card"`（`decks.cc _describe_cards()`、
  `lookup-help.cc _get_card_keys()`）。两语言各 24 键：21 现行 + the Shaft card
  （移除卡） + a buggy card + a very buggy card（哨兵）；Famine/Stairs 无描述键。
- 牌组归属（producer analog）：`decks.cc` 四个 `deck_archetype` 表——
  escape（Tomb/Exile/Elixir/Cloud/Velocity）、destruction（Vitriol/Pain/Orb/
  Degeneration/Wild Magic/Storm）、summoning（Elements/Pentagram/Dance/Swarm/
  Rangers/Illusion）、punishment（Wraith/Wrath/Swine/Torment）。
- 显示消费者：`?/C` 卡牌帮助菜单（`lookup-help.cc _get_card_keys()`，排除
  removed）、`decks.cc _describe_cards()` 牌组检视弹窗（`card_name_en + " card"`
  查描述并附 `which_decks()` 牌组归属）、`card_effect()` 实际效果、抽牌/堆叠
  消息（`stack_top`/`stack_contents`/`deck_contents`）、`name_to_card()` 反向
  解析（同时匹配 T_ 与 EN 名）。

## 验收标准

1. 清单命令确定性枚举全部枚举成员，交叉验证 `card_name_en()`/`card_name()`
   switch 覆盖（case 集与顺序一致，缺失即失败）；记录 baseline、inventory
   digest、glossary digest 与输入文件摘要。
2. 每个身份恰有一张证据卡和一个终态结论：`keep`、`adjust`、
   `retranslate`、`defer terminology` 或 `defer implementation`。
3. 名称键集合、描述键集合与 T_ 键集合双向差集为空（语境键
   `card name|Wild Magic` 单独核对）；语言侧独有键与 T_ 缺口单独记录生命周期
   并给出终态。
4. 每项描述核对 producer、consumer、实际行为：`card_effect()` 的目标、强度
   分支（card power）、条件、例外、持续效果（如 Tomb 墙体维持/塌落）、召唤
   生物与友好度依赖。
5. 同一依赖组（共享召唤语义、共享伤害/状态词根、共享牌组）内术语一致；与
   既有冻结边界（法术名、云雾名、状态、技能、glossary 如 Pain=痛苦、
   Torment=折磨、Cloud=云 系列）不一致时给出依据或暂缓。
6. ZH 资产由单一 `zh-translator` 顺序写入；每个依赖组或实际小批次运行
   `verify_zh.sh --profile translation`。
7. 本计划只做只读审核与证据记录；落地修改需另行授权，并在干净候选上按
   review-contract 走一次 final gate。

## 非目标

- 不改卡牌机制、数值、概率、牌组权重、AI、存档 identity 或枚举值。
- 不重审 #23–#29、法术/物品/怪物/状态/云雾等既有冻结边界；只复用其结论
  （如 glossary `Pain → 痛苦`、`Torment → 折磨`、云雾族 `X Cloud → X云`）。
- 不新增全局 ledger/schema；inventory JSON 是可重建临时 artifact。
- 不处理牌组名（deck name/flavour）、神祇能力文本等非卡牌身份族；仅记录
  跨族观察。

## 既有机制复用

- 复用 `?/C` 运行时枚举器（`_get_card_keys()` + `card_name_en()`）作为游戏内
  身份证明；复用 `docs/decisions.md` 既有裁定（`Evocations → 魔力释放`、
  `Orb of Zot → 佐特宝珠/力量宝珠` 等仅作依赖引用）。
- 新增 `.claude/scripts/card_inventory.py`（只读、确定性、可重建），解析
  枚举、名称 switch、生命周期、牌组表、T_ 键（含语境键）与中英描述键，
  输出 JSON inventory 与覆盖报告；复刻 R1 `cloud_inventory.py` 的安全基线
  （baseline blob 绑定 + fail-closed 输出）。解析器为严格语法（任何未消费
  的非注释 token、未配对预处理帧、重复 case/枚举成员、牌组表引用未知成员
  均报错退出）；source.txt 采用生产语义 SourceDB 模型（物理键原样保留、
  规范键小写化、T_/C_ 生产查找，基线时 `T_("Wrath")` 如实报告为命中武器
  铭印键 `wrath→狂怒` 的 canonical 碰撞）。

## 顺序

1. 冻结清单并记录 digest（本计划）。
2. 按共享依赖分组审核：召唤组（×6）→ 毁灭组（×6）→ 逃脱组（×5）→ 惩罚组
   （×4）→ 移除兼容组（×3）→ 哨兵组（×1 + 兜底描述键）。
3. 逐个身份记录证据卡与终态结论（`docs/card-review-results.md`），冻结
   依赖组内 `keep` 对照复核。
4. 用户授权后由单一 `zh-translator` 落地名称与描述批次，运行 translation
   profile。
5. 提交干净候选，机械路由评审，单次 final gate（如授权落地）。

## 重建命令

```bash
python3 .claude/scripts/card_inventory.py \
  --baseline-ref 9fb8e5dd22ef6607613d1c4381b7369f93a08a7e \
  --inventory-output /tmp/card-inventory-<新文件名>.json
  （输出路径仅允许 canonical `/tmp`（macOS realpath 为 `/private/tmp`）直下的单个
   全新 basename：拒绝嵌套组件、`.`、`..`、已存在目标、符号链接与可改名的 OS 临时根；
   重复重建请更换文件名或先删除旧文件）
```
