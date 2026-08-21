# TextDB 覆盖映射（#40 R0）

来源：`crawl-ref/source/database.cc` 的 12 个 `TextDB` 分组定义（行 87-176）、各审核子 Issue 的
范围声明与本仓库审核账本。本映射是 #40 R0 的只读覆盖记录：每个 TextDB 家族有唯一审核归属或明确
排除依据；重叠与重入条件显式记录。不替代任何子 Issue 的冻结 inventory。

身份/生命周期来源：`database.cc` 加载清单（load order）为唯一生产来源；各家族 inventory 工具
（monflee/miscast/monspell/wpnnoise/graffiti/decorlines_inventory.py）从 exact-Git 派生并绑定。

## 分组与文件清单

| 分组 | 目录 | 文件 | 消费入口（主要） |
|---|---|---|---|
| descriptions | descript/ | features/items/unident/unrand/monsters/spells/gods/branches/skills/ability/cards/commands/clouds/status/monstatus/mutations/passives.txt | describe.cc / describe-spells / menu / lookup-help |
| gamestart | descript/ | species/backgrounds.txt | newgame / describe.cc |
| randart | database/ | randname/randbook/rand_all/rand_arm/rand_wpn.txt | items.cc 神器生成与显示 |
| speak | database/ | monspeak/monspell/monflee/wpnnoise/insult/godspeak/monname/colourname/graffiti/miscast.txt | mon-speak.cc / spl-miscast / xom / directn / database.cc SpeakDB |
| shout | database/ | shout.txt（+insult.txt 共享） | shout.cc ShoutDB |
| misc | database/ | miscname/godname/montitle/decorlines/monname/colourname/graffiti/gizmo.txt | database.cc MiscDB / directn / items |
| quotes | descript/ | quotes.txt | describe.cc 引文 |
| help | database/ | help.txt | help.cc / menu |
| FAQ | database/ | FAQ.txt | help.cc FAQ |
| hints | descript/ | hints.txt/tutorial.txt | hints.cc / tutorial |
| egos | descript/ | egos.txt | describe.cc 物品 ego |
| source | i18n/ | source.txt（C++ `T_()`/`C_()` 键） | 全游戏 C++ 显示 |

## 覆盖状态（每家族唯一归属）

图例：✅ 已审核且可复用（证据在对应 issue/账本）；🔲 尚无全量证据（#40 子批待执行）；
⛔ 明确非玩家显示或协议边界；⚠️ 部分覆盖（有独立证据但非完整家族账本）。

| 家族/文件 | 状态 | 审核归属 | 证据 |
|---|---|---|---|
| descriptions/monsters.txt | ✅ | #24 | docs/monster-review-results.md |
| descriptions/gods.txt + passives/ability（神祇域） | ✅ | #25 | docs/god-review-results.md |
| gamestart/species+backgrounds | ✅ | #26 | docs/species-background-review-results.md |
| descriptions/mutations/status/monstatus/skills/ability（角色域） | ✅ | #27 | docs/character-mechanics-review-results.md |
| descriptions/branches/features（地下城域） | ✅ | #28 | docs/world-review-results.md |
| descriptions/items/unident/unrand（物品域）+ egos | ✅ | #29（+ #48 修复） | docs/item-extended-review-results.md |
| descriptions/clouds | ✅ | #41 | docs/cloud-review-results.md |
| descriptions/cards | ✅ | #42 | docs/card-review-results.md |
| descriptions/commands | ✅ | #43 | docs/command-review-results.md |
| hints/tutorial | ✅ | #46/#50 | docs/tutorial-review-results.md / hint-review-results.md |
| help + FAQ | ✅ | #52 | docs/help-review-results.md |
| speak/monspell | ✅ | #59 | docs/monspell-review-results.md |
| speak/monflee | ✅ | #54 | docs/monflee-review-results.md |
| speak/wpnnoise | ✅ | #60（+ #61/#62 消费者修复） | docs/wpnnoise-review-results.md |
| speak/graffiti + misc/graffiti（同源双载） | ✅ | #66 | docs/graffiti-review-results.md |
| speak/miscast | ✅ | #56 | docs/miscast-review-results.md |
| speak/godspeak | ✅ | #25（神祇台词域） | god ledger + #25 关闭评论 |
| misc/decorlines | ✅ | #67 | docs/decorlines-review-results.md |
| speak/monspeak | ✅ | #70（怪物说话消息域） | docs/monspeak-review-results.md |
| **shout/shout + speak|shout/insult（共享）** | ✅ | #69（同批冻结 ShoutDB/SpeakDB 双载 provenance） | docs/shout-review-results.md |
| misc/montitle | ✅ | #71（#24 怪物实体域扩展；复用 unique-monster identity provenance） | #71 / #73，合并 `aa8e6275ce` |
| misc/gizmo | ✅ | #29（539 个有限语法组件；最终程序化名称明确不可有限枚举） | docs/item-extended-review-results.md |
| misc/miscname | 🔲 | #87（2026-08-21 收口复核确认其含独立玩家消息，既有账本未完整取得所有权） | EN/ZH 各 10 个物理预检 key；最终范围以 exact-Git production inventory 为准 |
| quotes/quotes.txt | ✅ | #72（复用 #3 及怪物/法术专名证据） | 465 identities；386 keep / 79 adjust；远端 CI `32450858787` success |
| **randart/randname/randbook/rand_all/rand_arm/rand_wpn** | ⚠️ | #29 覆盖"随机神器/gizmo 按有限命名组件和生成规则证明覆盖"；无独立 randart 账本 | #29 关闭评论 |
| misc/godname | ✅ | #25（"神祇生产身份、显示名和称号：…godname.txt"） | #25 |
| speak|misc/monname、speak|misc/colourname | ⚠️ | 依赖证据：被 #25（Beogh 使徒/祖先名）、#66/#67（graffiti/decorlines 作者与颜色 token）消费；无独立家族账本，作为依赖族记录 | #66/#67 账本中的 external-token 绑定 |
| source/source.txt | ✅ | 持续维护（#40 R6 增量复核入口 + 各修复 issue）；无一次性全量人工审计（#40 明示） | verify_zh.sh source-db-static |

## 重叠与排除依据

- **insult.txt 双载**：同时属于 SpeakDB 与 ShoutDB（database.cc:130,149）。W4 必须冻结共享
  provenance 边界（#56 关闭评论已记录该风险）；两库的 key 空间与 override 顺序需同一批次处理。
- **monname/colourname 双载**：speak 与 misc 各加载一次（monname index 6/4，colourname 7/5）。
  作为命名依赖被多家族消费；不单独建账本，但在每个消费家族账本中以 external-token 绑定验证。
- **graffiti 双载**：speak（index 8）与 misc（index 6）同源；#66 已在 speak 侧冻结闭包，misc 侧
  加载顺序由 decorlines 批次（#67）的 misc manifest 验证。
- **decorlines→graffiti 依赖**：`any_graffiti` 为跨家族递归根；#67 冻结 misc 侧闭包证据。
- **montitle 归属（已裁决 2026-08-18）**：montitle.txt 86 keys 全部为 `<unique-monster dbname> title`，
  消费链 `getMiscString(db_name() + " title")`（mon-info.cc:1055、describe.cc:7035、
  player-notices.cc:330）即 #24 怪物显示链的同一实体集；#24 已审 unique 怪物名/描述/身份，
  但明示范围未含 title 文件。裁决：作为 #24 怪物实体域的扩展子批（新 Issue #71），复用
  #24 unique-monster identity inventory 作 provenance，只审 montitle.txt 本身；EN/ZH 键
  86/86 无不对称。
- **randart 归属**：#29 明示"随机神器/gizmo 按有限命名组件和生成规则证明覆盖"，视为该域证据；
  若上游 randart 组件漂移，重入触发后回到 #29 或新子批。
- **miscname 归属（2026-08-21 收口复核）**：它是独立 MiscDB 玩家消息家族，不是协议或命名
  依赖。消费者至少包括 `spl-summoning.cc`、`traps.cc`、`main.cc` 与 `stairs.cc`；物理预检
  还发现 EN `summon_horrible_things` 与 ZH `SHT_int_loss` 的 key 风险。既有法术/世界/开局
  账本没有冻结这一完整 TextDB 家族，故建立 #87 按 production inventory 逐身份审核；完成前
  不得把该族标为覆盖。
- **明确非玩家显示**：协议/lookup 键值（英文）、`__NONE`/`__DEFAULT` 哨兵、Lua 比较串不属于
  显示文本；各家族账本已按 i18n-safety 策略隔离。

## 重入条件（输入漂移失效）

任一已审家族的以下输入变化 → 对应账本与证据卡失效，按 #40 R6 增量复核入口重审：

1. EN/ZH 源文件内容变化（上游同步或本仓库修复）；
2. 加载顺序/文件清单变化（database.cc TextDB 定义）；
3. 消费者代码变化（显示链、RNG 拓扑、token 替换层）；
4. `docs/glossary.md` 术语权威变化（SHA 变更）；
5. 依赖家族重审导致的外部 token 语义变化（如 graffiti 闭包改动影响 decorlines）。

失效判定以各 inventory 工具重跑为准（exact-Git 绑定 + scope SHA）；未变化证据按
`docs/glossary.md` 与账本 reentry_trigger 复用，不重做全量历史审核。

## 关闭条件映射（#40）

- 已完成并关闭：R1 cloud #41、R2 card #42、R3 commands/tutorial/hints/help #43/#46/#50/#52、
  R4 各动态消息家族 #54/#56/#59/#60/#66/#67/#69/#70、montitle #71、R5 quotes #72。
- R6 已真实使用：#77 在当前 production inventory 上只重审 10 个失效 command identity，复用
  296 个输入未变 identity，重冻结后 `coverage_equal=true`，合并 `a29423cdcc`。
- 当前唯一 R0/R1-R5 收口缺口为 miscname #87。它完成并更新本映射后，#40 才满足关闭条件。
