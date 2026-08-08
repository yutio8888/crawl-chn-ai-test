# Issue #40 R2 卡牌名称与描述全量校对结果

- 基线：`9fb8e5dd22ef6607613d1c4381b7369f93a08a7e`（`chn-0.34.1-base` HEAD）
- 术语表 SHA-256：`95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407`
- 清单 SHA-256：`611eee819d584e8d02a0f4d9282e69c6d0db9b8e3be010e8dfae4cc8f8db516f`
  （生产语义 SourceDB 模型版；修复轮 R2-CODE-001..003 后重生成，baseline 9fb8e5dd22）
- 输入摘要：
  - `decks.h` `949b9fc43217…`
  - `decks.cc` `84002fd6e329…`
  - `cards.txt` `ab9722e5b162…`
  - `zh/cards.txt` `35d606026a4c…`
  - `source.txt` `2f2fc9d90c36…`
- 身份总数：25（现行 21；TAG 34 移除 3：SHAFT/STAIRS/FAMINE；哨兵 1：`NUM_CARDS`）
- 生命周期：现行 21；移除 3（`card_is_removed()`=true、`?/C` 排除、`card_effect` 落入
  buggy 分支）；哨兵 1（兜底名 `a buggy card` + `a very buggy card`）
- 描述键：EN 24 = ZH 24，双向差集为空（EN-only 无、ZH-only 无）；Famine/Stairs
  无描述键（EN/ZH 均无），Shaft 描述键存在（dead key）
- T_ 键缺口：`Wrath` 无卡牌专属键；生产 SourceDB 键全小写规范化，`T_("Wrath")` 命中武器铭印键 `wrath→狂怒`（item-name.cc SPARM_RAGE），**基线时卡名实际显示「狂怒」而非英文**（SourceDB 小写规范键空间，非缺失回退）

## 独立审核进程结论（2026-08-08，translation-reviewer）

- 进程：独立 Pi 实例 `opencode-go/deepseek-v4-flash`，只读；基线/glossary/inventory
  三值一致。
- 25 身份逐张证据卡；终态统计：**14 keep、7 adjust、0 retranslate、
  3 defer terminology、1 defer implementation**；Blocker 0。
- 7 项 adjust（候选译文见下节）；依赖组内 `keep` 对照复核完成（召唤组 6 张、
  毁灭组 6 张、逃脱组 5 张、惩罚组 4 张、移除组 3 张、哨兵 1 张全部有卡）。
- Suggestion（不阻塞，9 条）：card power 五译并存（能量×3 / 力量 / 威力）建议统一
  为“卡牌威力”；oklob plant 卡图“酸箭草”vs 怪物显示名“奥克罗布植物”跨族分裂
  （留待怪物族）；Wild Magic“误施了法术”vs glossary miscast→施法失误；“魔力”vs
  MP→法力（冻结消息惯例）；Elixir“健康/生命”两译；Torment“痛苦的伤害”与 Pain 卡名
  同词避歧；Elements“怪物”→“野兽”；Swarm 卡名“虫群”vs 描述“群蜂”泛化差；
  buggy 兜底消息“有问题的牌”vs 卡名“有 bug 的卡牌”不一致（消息键冻结，仅观察）。

## 名称证据卡（现行 21 + 哨兵 1）

| 身份 | 英文名称 | 现行中文 | 证据 | 终态 |
|---|---|---|---|---|
| `card:CARD_VELOCITY` | Velocity | 速度 | 现行；牌组 escape×5；`_velocity_card` 只解自身减速、友方加速、敌方减速，**从不加速使用者本人**；名称直译准确 | keep（名称） |
| `card:CARD_TOMB` | the Tomb | 墓穴 | 现行；`cast_tomb(10+power/20+random2(power/4))` 石墙环绕，离开中心墙塌；名称与描述一致 | keep |
| `card:CARD_EXILE` | Exile | 放逐 | 现行；`_exile_card` 放逐附近生物，能量越高越多，永不放逐使用者 | keep |
| `card:CARD_VITRIOL` | Vitriol | 硫酸 | 现行；`_damaging_card` 酸蚀伤害（ZAP_ACID）；glossary 无冲突 | keep |
| `card:CARD_CLOUD` | the Cloud | 云雾 | 现行；`_cloud_card` 敌方被有害云雾环绕，随威力变化；与云雾族术语（glossary Cloud→云 系列、R1 已审）协调，卡名取“云雾”作实体名不冲突 | keep |
| `card:CARD_STORM` | the Storm | 风暴 | 现行；`_storm_card` 风与雷电；描述与效果一致（仅 suggestion：统一“卡牌威力”） | keep |
| `card:CARD_PAIN` | Pain | 痛苦 | 现行；glossary Pain→痛苦 ✅；`_damaging_card`：苦痛→衰竭箭→高威力附折磨 | keep（名称） |
| `card:CARD_TORMENT` | Torment | 折磨 | 现行；glossary Torment→折磨 ✅（按比例伤害）；对使用者施加折磨 | keep |
| `card:CARD_ORB` | the Orb | 天球 | 名称失实：天文学术语，与描述“毁灭球”及 glossary Orb of Destruction→毁灭法球、Orb of Electricity→电光球 族不符；EN 为泛称 | **adjust（名称）→法球** |
| `card:CARD_ELIXIR` | the Elixir | 灵药 | 现行；快速恢复 HP/MP；与效果消息（生命和魔法）一致 | keep |
| `card:CARD_SUMMON_DEMON` | the Pentagram | 五芒星 | 名称 keep；描述“五角星”与卡名“五芒星”同身份混用 | **adjust（描述）** |
| `card:CARD_SUMMON_WEAPON` | the Dance | 舞蹈 | 名称 keep；描述“飞舞的武器/印记/卡牌力量”与怪物名“舞动武器”、glossary brand→铭印、“卡牌威力”不一致 | **adjust（描述）** |
| `card:CARD_SUMMON_BEE` | the Swarm | 虫群 | 现行；召唤蜂群（蜜蜂/蜂后/墨利埃） | keep |
| `card:CARD_WILD_MAGIC` | Wild Magic | 狂野魔法 | 现行；`C_("card name", …)` 语境键存在；效果=狂野魔法作用于敌人并回蓝 | keep |
| `card:CARD_WRATH` | Wrath | 狂怒（铭印键误用） | **无卡牌专属键**：生产 SourceDB 小写规范键命中武器铭印键 `wrath→狂怒`（卡名误用铭印译文）；神怒家族一致（god UI Wrath→神怒、Godly wrath is upon you!→神怒降临于你！、本卡描述“神怒”） | **defer implementation（语境键补全：神怒）** |
| `card:CARD_WRAITH` | the Wraith | 幽魂 | 现行；`drain_player` 汲取经验值；描述“衰竭”与汲取族一致 | keep |
| `card:CARD_SWINE` | the Swine | 猪群 | 名称失实：EN 单数集合名词，效果=使用者变成一头猪（不可取消），且怪物名 hog→猪、holy swine→圣猪 先例 | **adjust（名称）→猪** |
| `card:CARD_ILLUSION` | the Illusion | 幻象 | 现行；召唤使用者幻象，威力随自身 | keep |
| `card:CARD_DEGEN` | Degeneration | 退化 | 名称 keep；描述漏译 malmutate（恶性变异）、daze 误作“昏迷”（状态名“眩晕”） | **adjust（描述）** |
| `card:CARD_ELEMENTS` | the Elements | 元素 | 现行；召唤四元素野兽三只 | keep |
| `card:CARD_RANGERS` | the Rangers | 游侠 | 现行；召唤数个射手 | keep |
| `card:NUM_CARDS` | a buggy card / a very buggy card | 有 bug 的卡牌 / 非常有 bug 的卡牌 | 哨兵；兜底描述键齐全，EN/ZH 对等 | keep |

## 移除兼容组（×3，defer terminology）

| 身份 | 回退名 | 描述键 | 终态 |
|---|---|---|---|
| `card:CARD_SHAFT_REMOVED` | 有 bug 的卡牌 | the Shaft card（EN/ZH dead key 存在） | defer terminology：恢复时复审 |
| `card:CARD_STAIRS_REMOVED` | 有 bug 的卡牌 | 无 | defer terminology：恢复时复审 |
| `card:CARD_FAMINE_REMOVED` | 有 bug 的卡牌 | 无 | defer terminology：恢复时复审 |

re-entry trigger：仅当 TAG_MAJOR_VERSION 变更或遗留存档路径重新激活该卡时复审
术语；现无显示路径，不补译名（最小充分设计）。

## 建议落地批次（待人工确认）

| # | 身份 | 文件 | 修改 |
|---|---|---|---|
| 1 | CARD_WRATH | `zh/source.txt` + `decks.cc` | 新增语境键 `card name|Wrath` → `神怒`，`decks.cc` 改用 `C_("card name", "Wrath")`（修复卡名误用铭印译文「狂怒」；不能用普通键 `Wrath`——与武器铭印键 `wrath` 在 SourceDB 规范键空间碰撞，Issue 66 检测确认） |
| 2 | CARD_ORB | `zh/source.txt` | `the Orb` → `法球`（原“天球”） |
| 3 | CARD_SWINE | `zh/source.txt` | `the Swine` → `猪`（原“猪群”） |
| 4 | CARD_PAIN | `zh/cards.txt` | “抽出此牌会释放一个有着攻击性的死灵术。” → “抽出此牌会释放一个死灵系攻击法术。” |
| 5 | CARD_VELOCITY | `zh/cards.txt` | “抽出此牌，自己和友方的速度会得到极大提升，而敌人的行动会严重迟缓。” → “抽出此牌可以让盟友获得极大的速度，或让敌人严重迟缓（并可能移除自身的减速效果）。” |
| 6 | CARD_DEGEN | `zh/cards.txt` | “抽出此牌会尝试将附近的敌人变成较弱的形态，如果他们无法被变形，会暂时昏迷。” → “抽出此牌会尝试将附近的敌人变形并恶性变异为更弱的形态，无法被变形的敌人会短暂眩晕。” |
| 7 | CARD_SUMMON_DEMON | `zh/cards.txt` | 描述中“仪式五角星图案”→“仪式五芒星图案”（与卡名统一） |
| 8 | CARD_SUMMON_WEAPON | `zh/cards.txt` | “抽出此牌将召唤出一把飞舞的武器。其质量、印记和友好程度都受卡牌力量影响。” → “抽出此牌将召唤出一把舞动武器。其质量、铭印和友好程度都受卡牌威力影响。” |

依赖组落地顺序：惩罚组（1、3）→ 毁灭组（2、4、6）→ 逃脱组（5）→ 召唤组（7、8）；
每批运行 `verify_zh.sh --profile translation`。Suggestion 项不进入本批次。

## 落地记录（2026-08-08，人工确认后）

- zh 批次：提交 `6b85724d79`（source.txt 3 处值改动 + 语境键块 + zh/cards.txt 5 处描述；单一 zh-translator）
- 代码侧：提交 `4a2233df4b`（decks.cc `card_name()` CARD_WRATH → `C_("card name", "Wrath")`；单一 crawl-coder）
- 碰撞修复说明：首轮以普通键 `Wrath→神怒` 落地被 `verify_zh.sh` 静态完整性检查拦截（canonical `wrath` 双定义：铭印键 5061 `wrath→狂怒` + 新键 9382 `Wrath→神怒`）；运行时 SourceDB 键全小写规范化，二者同键。改用语境键后碰撞消除（`card name|wrath` 与 `wrath` 规范键不同），武器铭印 `wrath→狂怒` 不受影响。
- 验证：`verify_zh.sh --profile translation` 0 blocking；`--profile code` 0 blocking（含 i18n 提取/键覆盖：`card name|Wrath` 被识别）。

## 覆盖证明

- 清单枚举（25）与证据卡（25）双向差集为空；每身份恰一张卡、一个终态结论。
- 清单枚举（25）与证据卡（25）双向差集为空；每身份恰一张卡、一个终态结论。
- 生产语义覆盖：baseline 时 `canonical collisions = [card:CARD_WRATH]`（`T_("Wrath")`
  → 规范键 `wrath` 命中铭印键，卡名显示「狂怒」）；候选后 collisions 为空，
  `C_('card name','Wrath')` → `card name|wrath` 命中「神怒」；`T_ unresolved`
  两版本均为空（无英文回退显示）。
- 消费者核对：`?/C`（排除 removed 21 键）、`_describe_cards`（`card_name_en + " card"`，
  附 `which_decks` 牌组归属）、`card_effect` 逐项行为、`name_to_card`（T_ 与 EN 双匹配，
  ZH 子串匹配兜底）。
- 重建命令：`python3 .claude/scripts/card_inventory.py --baseline-ref 9fb8e5dd22ef6607613d1c4381b7369f93a08a7e --inventory-output /tmp/card-inventory-<新文件名>.json`（输出路径必须为全新文件；重复重建请更换文件名或先删除旧文件）
