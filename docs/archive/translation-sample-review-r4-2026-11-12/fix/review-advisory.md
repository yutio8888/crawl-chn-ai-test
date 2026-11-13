# 第四轮 9 项建议修复：独立只读复审

- 对象：
  - trunk #322 @ `e7407964ca`（基线 `e469790144`）
  - stable #323 @ `6c866d0eb9`（基线 `27dd279443`）
- 复审者：Claude Opus 5.5，只读。读过 glossary，所以这不是盲评。
- 改动范围：两线都只改了中文资产和派生台账，没有改 C++、Lua/.des 或英文资产，英文输出不变。
- 两线 descript 部分的增删行逐行相同。source.txt 部分，stable 另外补了 1 个 `fiery` 键，并单独修正了一个 plural 后缀（stable 的旧值本来就不同）。

## 结论

| 线 | 结论 |
|---|---|
| trunk #322 | **Ready**（无 Blocking） |
| stable #323 | **Ready**（无 Blocking） |

前提：合并前须等适用 CI 全部通过。

## 逐项核对

| 项 | 原文 → 旧句 → 新句 | 结论 |
|---|---|---|
| R4-4-09 | The Black Torch roars with renewed intensity! → 黑火炬以新的强度咆哮着！ → 黑火炬再度猛烈地咆哮起来！ | Ready：renewed intensity 译为“再度猛烈”，自然，不再是直译 |
| R4-4-10 | Trog 首句 → 特洛格是愤怒和暴力古神。 → 特洛格是愤怒和暴力的古神。 | Ready：只补了“的” |
| R4-6-02 | A %s emerges from the mists of... memory?.... → %s从……记忆的迷雾中浮现？…… → %s从迷雾中浮现……那是记忆的迷雾吗？…… | Ready，详见下文 |
| R4-6-03 | They guard the %s rune of Zot. → 其守护着佐特%s符文。 → 这位领主守护着佐特%s符文。 | Ready，详见下文 |
| R4-7-01 | 共享后缀 ` but does no damage` / ` but do no damage` → 但没有造成伤害 / ␠但没有造成伤害 → ，但没有造成伤害 | Ready，详见下文 |
| R4-1-06 | buckler → 一小块木头和金属，通过绑在一只手臂上进行防御。 → 一面由木材和金属制成的小盾，绑在一只手臂上用于防御。 | Ready：“小盾”明确了物品，搭配自然 |
| R4-3-02 | demonspawn corrupter：盔甲 → 护甲 | Ready：glossary 中 armour 为护甲；只改了这一处 |
| R4-5-10 | HINT_STAIR_BRAND：逃生舱口 → 逃生口 | Ready：只改了这一处，没有扩大到全库，见 Non-blocking N2 |
| R4-1-02 | riddle talisman：相邻每多一格空地 → 敌人周围每多一格空地 | Ready，详见下文 |

### R4-6-02
- 消费者是 `overflow.des:219`（stable 为 :217），`%s` 来自 `crawl.t_(sp)`，即 species_mock 的种族名，Poltergeist 时为 dancing weapon，Mountain Dwarf 时为 goblin。
- 代入真实名称的完整句，例如“地精从迷雾中浮现……那是记忆的迷雾吗？……”。
- 迟疑和疑问落在“迷雾是否为记忆”的辨认上，对应英文 “mists of... memory?”。旧句的问号挂在“浮现”上，看起来像怀疑怪物是否出现，新句纠正了这一点，语义没有变。

### R4-6-03
- `pan.des` 的 `pan_lord_epilogue` 依次输出三句：领主专属消息；“The mighty Pandemonium lord %s resides here.”；“They guard the %s rune of Zot.”。
- 这里的 they 是单数 they，指刚提到的那一位万魔殿领主（四个领主各对应一种符文修饰：glowing/magical/fiery/dark）。所以“这位领主”的指代和数量都正确，比“其”更明确。
- 修饰词 `crawl.t_(runes[name])` 是无语境查询。stable 原本没有无语境的 `fiery` 键，Cerebov 这句会回退成英文 “fiery”。stable 新增 `fiery → 火`，与 trunk 已有的同键（trunk source.txt 第 48554 行）一致。
- 现有的语境键 `rune_name|fiery → 烈焰` 不会被这个无语境调用命中，作者的判断正确。这一处补键直接关系到 R4-6-03 这句能否正确显示，属于必要的补齐，没有越界。

### R4-7-01
我 git grep 了两个后缀的全部 `T_` 消费者：
- **trunk**：actor.cc:799、beam.cc:4463 和 5856（plural 时分别取两个后缀）、mon-abil.cc:1539（太阳耀斑）、spl-damage.cc:916/1019/2004、terrain.cc:2671/2718。
- **stable**：beam.cc:4433/5819、mon-abil.cc:1578、spl-damage.cc:903/1006/1975、terrain.cc:2695/2738。

逐个查了这些调用对应的中文模板：
- beam：`%1$s%2$s了%3$s%4$s%5$s%6$s`，后缀在第 5 个占位，句末标点在第 6 个占位；
- 太阳耀斑：`太阳耀斑吞没了%s%s。`；
- 冻结：`你冻结了%s%s%s`；
- airstrike：`%s，并击中了%s%s%s`；
- 灼烧：`火焰舔舐%s%s。`；
- 墙壁和寒气：`墙壁冻结了%s%s%s` / `寒冷的空气侵袭了%s%s%s`；
- actor.cc 的形式是后缀加上 `T_(".")`。

在所有这些模板里，后缀前面都没有逗号，后面跟的是句号或 `attack_strength_punctuation` 的结果，所以不会出现双重标点。

- **无伤害分支**：得到“……兽人，但没有造成伤害。”。
- **有伤害分支**：后缀为空字符串，不受影响。
- plural 后缀 ` but do no damage` 原来是“␠但没有造成伤害”（前面带一个半角空格），这次一并统一成“，但没有造成伤害”，顺带消除了中文里的半角空格。
- 以下几处使用的是不同的键，不受影响：
  - stable 的 `actor.cc:779` 是裸英文 `", but do no damage."`（不经 T_）；
  - stable 的 mon-cast `", but does no damage."`、`"You %s %s, but do no damage."`；
  - 两线 melee-attack 和 ranged-attack 中的整句模板。
- 英文键没有变，英文输出不变。
- 测试中的断言 `string(T_(" but do no damage")) + T_(".")` 是由 T_ 动态组成期望值的，不受译文变化影响。

### R4-1-02
- `melee-attack.cc:999/4624` 中是 `airstrike_space_around(defender->pos(), true)`，计算的是敌人周围的空格。英文 “every open space next to them” 中的 them 指 foe。所以“敌人周围每多一格空地”正确，旧句的“相邻”没有说明是谁相邻。
- Felid 的 Lua 条件块（if/else 两个 return）没有改动。
- stable 正文中仍是“更容易施放妖术系法术”，Hexes 回迁的结果没有被回退。

## 台账：通过，属于必需派生，没有重绑 glossary

两线做法相同：
- **item-extended**：buckler 和 riddle talisman 两张卡的 adopted_chinese 随正文变化，Decision inventory SHA-256 随之更新，另有两个计数字段各变化 1（408→409、3299→3298 之类的统计）。
- **monster**：清单 SHA-256 更新；corrupter 的终态由 keep 改为 `retranslate: description corrected`，这是该台账的终态规则。术语表 SHA-256 行没有改动。
- **world**：memory 和 pan 两张卡的中文随资产变化，Inventory-SHA256 更新。摘要中的 `glossary_sha256` 保留旧值（trunk `2534b6d47d80…`、stable `799190851dcb…`），没有重绑。

归一化哈希后，非哈希差异只有上述资产文本和终态分类的变化。

## Non-blocking

- **N1**：stable 的 `source.txt` 在新增的 `fiery` 条目前多了一个空的 `%%%%` 分隔行（第 50194 行附近出现连续两行 `%%%%`）。解析器会把它当作空键跳过，不影响运行；trunk 在第 51191 行也早就有同样的情况。建议以后顺手删掉。
- **N2**：R4-5-10 按任务范围只改了 HINT_STAIR_BRAND 这一处。全库仍有“逃生舱口”残留（trunk 的 hints.txt 2 处、source.txt 1 处；stable 的 hints.txt 1 处、source.txt 1 处），与“逃生口”并存。是否统一应另行决定，本轮不扩大修改范围是正确的。
