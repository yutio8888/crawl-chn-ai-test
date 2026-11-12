# 第四轮修复与 stable Hexes 回迁：独立只读复审

- 复审者：Claude Opus 5.5，只读。读过 glossary 与裁决，所以这不是盲评。
- 对象：
  - trunk #318 @ `ddf79a9546`（基线 `59aec6256f`）
  - stable #319 @ `193517f833`（基线 `ae5a420e78`）
  - stable #320 @ `f6b597512e`（基线 `ae5a420e78`）
- 三个 PR 当前均为 OPEN/draft。合并前须等适用 CI 全部通过。

## A. 第四轮修复（#318 / #319）：**Ready**（两线均无 Blocking）

1. **R4-7-10（仅 stable）**：通过。
   - `mon-act.cc:4031-4032` 只给两个字面量加了 `T_`，三元条件 `MONS_DISSOLUTION` 和 `MSGCH_SOUND` 都没变。英文模式下 `T_` 直接返回原文，输出逐字节不变。
   - 新增 `You hear a sizzling sound.` → “你听到一阵滋滋声。”。
   - `You hear a grinding noise.` 原本就有译文（研磨声）。
   - 已有的 `You hear a sizzling sound!`（嘶嘶声！）是另一个带感叹号的键，没有被误改。
2. **R4-3-06（两线）**：通过。
   - 只在“一团藤蔓和触须”前补了“挥舞不休的”，对应英文 “A mass of lashing vines and tentacles”。
   - 两线英文相同，第二句没动。
3. **R4-4-04（两线）**：通过。
   - 英文是 “Disciples of the Council learn to perform three martial techniques while moving around in combat.”。
   - 新译“无间门派的门徒学会在战斗中走位时施展三种武术。”把旧译“会学习实践”的动作关系改正了。实体名用的是 glossary 的 `the Wu Jian Council | 无间门派`，没有出现“议会”。
   - 新译已经明写“无间门派的门徒”，of the Council 实际上已经补上了，所以“主体省略是否可接受”这个问题在终稿里已无意义。即使不写，在 Wu Jian powers 条目内省略已知主体也属于可接受的省略，不构成独立漏译。
   - 两线英文与改动相同。
4. **monster-review-results.md 的两行改动**：通过，属于硬性派生。
   - 一行是清单 SHA-256，随 monsters.txt 正文变化。另一行是 `MONS_STARFLOWER` 的终态，由 `keep` 改为 `retranslate: description corrected`，这正是该台账的终态规则（“描述改动为 retranslate”）。
   - 术语表 SHA-256 没有重绑，不是惯性重绑。

## B. stable Hexes 回迁（#320）：**Ready**（无 Blocking）

1. **直接消费者覆盖完整**
   - 我在 stable head 的 `crawl-ref/source` 下（不含测试）git grep “诅咒系 / 诅咒射手 / 诅咒师 / 诅咒精通 / 诅咒枪手”，只剩三处：
     - `source.txt` 的 `Maledictor → 诅咒师`：正确保留，属于真正的诅咒。
     - `jobs.cc:71` 的旧别名“诅咒枪手”：属于 protocol_parse，需要保留。
     - `jobs.cc:123` 新增的“诅咒射手”别名：见第 5 项。
   - 资产改动经词级 diff 归纳，全部是 Hexes 词根替换：
     - 诅咒系 → 妖术系、诅咒射手 → 妖术射手、诅咒师（hexer）→ 妖术师；
     - 下咒 → 施放妖术、残余诅咒（residual hexes）→ 残余妖术、hexed 的“被控制” → “被支配”。
   - 没有夹带其他措辞变化。
   - 新增的 `hex mastery` 与 `Hexes are much easier…` 两个键有真实消费者：`dat/forms/sphinx.yaml:24` 的 fakemut。
2. **没有误改**
   - randbook 按英文池逐项对齐后，只改了 Hexes→妖术、Hexing→施展妖术、Hexed（adj）→被施以妖术的、Hexing（adj）→施展妖术的。
   - Curses、the Curse、Malediction、Cursed、Maledictive 都保留了诅咒或恶咒。
   - `Maledictor → 诅咒师` 保留，普通 curse 和 `curses,` 没有出现在 diff 中。
3. **两线命名一致**
   - 31 个改动条目逐一与 trunk `59aec6256f` 同键的值比较，全部逐字相同。
   - 这些条目中 16 个 descript 条目的英文正文两线也相同，所以照搬 trunk 中文不会造成错配。
   - glossary 各项与 trunk D-C-110 一致：Hexes / Hex / Hexslinger / hexer / Ancestor Life: Hexer / hex mastery / hexed（被支配）。
   - randbook 两个池与 trunk 逐项相同。
4. **英文、内部身份、存档不变**
   - 只改了中文资产和别名，没有改英文键或学派枚举。
   - 测试断言了 `skill_name_en`、`spelltype_long_name_en`、`get_job_name_en`、`mons_type_name_en`（“a hexer”）、`Note` 存档名，以及 `skill_abbr` 仍为 Hex。
5. **jobs.cc 的“诅咒射手”别名**：必要、没有越界，风险低。
   - 回迁前 stable 的 SourceDB 显示名就是“诅咒射手”。旧 rc 选项、存档或成绩里如果写的是这个中文名，回迁后 `get_job_by_name` 用当前显示名已经匹配不上；而这个名字不在 `_job_zh_names()` 的旧别名表里（表里是“诅咒枪手”），补这条别名是必需的。
   - 它放在子串匹配循环之前，只增加一条精确匹配，不影响显示，也不改变英文行为。英文模式下额外接受这个中文串，无害。
   - cjk_inventory 已登记为 protocol_parse。
   - Non-blocking：trunk 的 `jobs.cc` 没有同样的“诅咒射手”别名，trunk 早先改名时可能留下同样的兼容缺口，建议另行核实。
6. **台账：必需派生，没有违规重绑**
   - notice-only 台账（character-mechanics、item-extended、species-background、monster）：
     - 哈希归一化后，非哈希差异只有当前中文正文的替换，以及 monster 台账终态由“description corrected”变为“name and description corrected”。
     - 变化的哈希只有 `fact_sha256`、`inventory_sha256`、`decision_inventory_sha256`。
     - `glossary_sha256` 一处都没有重绑，符合“只同步资产直接派生字段”的规则。
   - 硬性新鲜度台账（graffiti、miscast、miscname、monflee、monspell）：只改了 `glossary_sha256` 和 `inventory_sha256`，非哈希差异为 0。这次 glossary 确实改了，这些台账按规则必须重绑，是正当的。
7. **decisions 写法：通过**
   - D-C-110（稳定线回迁）写明了：
     - 维护者的明确要求；
     - 开发线参照提交 `59aec6256f…`；
     - 适用范围及保留项（curse、Maledictor、Maledictions、`curses,`、Curses/Malediction，不按池名整体替换）；
     - 英文键、身份、存档、旧快照都不变；
     - “不把旧基线下遵守诅咒系的译文追认为当时的错误；前轮冻结样本与原评审保持不变”。
   - D-C-101 只追加了一行“后续处置：Hexes 全称／Hex 简称部分已由本线 D-C-110 取代，以下原裁决保留为历史记录”，原裁决正文没改，标注正确，没有倒改历史。
   - 小瑕疵（Non-blocking）：glossary 第三节表头新增了“作用域”列，但其余学派行仍只有两列，渲染时不美观。glossary.utf8 已重新生成，解析以 CI 结果为准。
8. **测试：真实运行，不是镜像断言**
   - `[hexes-backport]` 在 EN 和 ZH 两种模式下调用真实 API：技能名、学派全称和简称、职业名及按名查找（含两个旧别名）、先祖能力名和描述、怪物显示名与英文身份、Note 存档名、lookup-help 键、长描述、sphinx 形态 fakemut 与变异列表。
   - 期望值都是独立写出的字面量。
   - `test_audit_item_name_inventory.py` 只更新了 BOOK_HEXES 改动带来的清单哈希，390 个身份数不变。
   - 我没有复跑，以 CI 为准。

## #319 与 #320 的冲突

`git merge-tree pr/319 pr/320` 实测结果：

- **`crawl-ref/source/dat/i18n/zh/source.txt` 内容冲突。**
  - 两个 PR 都在文件末尾 klown pie 条目之后追加条目（#319 加滋滋声，#320 加 sphinx 两键）。
  - 解决方法是两边都保留，注意 `%%%%` 分隔符。
- **`docs/monster-review-results.md` 内容冲突。**
  - 两边都改了清单 SHA-256 头行，各自的行改动（STARFLOWER 与 ANCESTOR_HEXER）也会被一并带入。
  - 不要手工挑选其中一边的哈希。#319 合并后，应在 #320 合入新 base 的分支上用现有 renderer 重新生成，或重算清单 SHA，再让 CI 校验 exact-artifact。
- **`crawl-ref/source/dat/descript/zh/monsters.txt` 自动合并成功**（starflower 与 imperial myrmidon 是不同的块）。
- 解决冲突后 #320 的 head 会变。受影响的复审只需核对两个冲突文件的解决结果，并重跑适用检查。

## Non-blocking 汇总

- trunk 缺少“诅咒射手”兼容别名，需另行核实（B5）。
- glossary 学派表新增列后格式不齐（B7）。
- 合并 #319 后，#320 须重新生成 monster 台账清单哈希，而不是手工合并（冲突一节）。

## C. #320 增量复审（f6b597512e → 2ec6f1e470）：**Ready**（无 Blocking）

- 新 head 是 merge 提交，父提交为 `f6b597512e` 与 `51e9e56d55`。`51e9e56d55` 就是 #319 的合并提交，其父提交为 `ae5a420e78` 与 `193517f833`。

1. **source.txt 两边的追加都保留了。**
   - 文件末尾依次是 klown pie → `hex mastery`/妖术精通 → `Hexes are much easier…`/你施放妖术系法术要容易得多，敌人也更难抵抗。 → `You hear a sizzling sound.`/你听到一阵滋滋声。
   - `%%%%` 分隔符完整。已有的 `You hear a sizzling sound!`（嘶嘶声！）没有受影响。
2. **monster-review-results.md**
   - 相对 f6b597512e，只有两行变化：清单 SHA-256 由 `b4012628…` 变为 `d58b4c58…`；STARFLOWER 由 `keep` 变为 `retranslate: description corrected`。
   - ANCESTOR_HEXER 仍是“妖术师”，name and description corrected 一行保留。
   - 术语表 SHA-256 仍为 `dcbfb16a…`，与 #320 原样相同，没有重绑 glossary。
   - 新清单哈希既不同于 #320 原值，也不同于 #319 原值（`525d687c…`），这与“合并后两处资产都变化”相符。
   - 我在只读条件下没有复算这个哈希：生成器需要在仓库工作树里配合 baseline ref 运行，这会创建 worktree，与只读要求冲突。它是否与合并后资产逐字节一致，由 CI 的 ZH CI Gate 和 Review ledgers 的 exact-artifact 检查负责判定。我查询时这些检查仍在运行。
3. **monsters.txt 两处都在。**
   - 第 2299 行是 starflower 的“从死星的外壳中长出的一团挥舞不休的藤蔓和触须。”。
   - 第 1476 行是 imperial myrmidon 的“妖术系法术”。
   - 第 140 行的“妖术女王”在基线里原本就有，不是本次改动。
4. **没有带入额外改动。**
   - `git diff f6b597512e 2ec6f1e470` 的文件清单与 `git diff ae5a420e78 51e9e56d55`（即 #319）完全相同，都是 gods.txt、monsters.txt、source.txt、mon-act.cc、monster-review-results.md 这 5 个文件，均为 9 行新增、6 行删除。
   - 去掉台账后，两份 diff 的增删行逐行相同。
   - 台账的差异只有上面第 2 项所述的清单哈希。
- **前提**：要等新 head 的适用 CI 全部通过，尤其是 exact-artifact 台账检查，才能按长期授权合并。
