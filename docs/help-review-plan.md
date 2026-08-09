# Issue #52 R3 Help/FAQ TextDB 全量审阅计划

## 冻结边界

- 上游总览：Issue #40 R3；执行入口：Issue #52（help/FAQ 子批）。
- 基线：`7caba5166f4b2fd680ecbc258ea6ffe3f6249f50`。
- Glossary SHA-256：
  `95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407`。
- Inventory SHA-256：
  `29a8c74df7edc14b5ec2a43abb49bbfd794c119ee790991d7d5d995e4bcc5c45`。
- 所有输入均从精确 Git tree 读取；本次重建得到 32 个唯一逻辑 identity，
  由 13 个 `help:<canonical key>` 与 19 个 `faq:<Q/A suffix>` 组成。
- Help 规范身份源是 EN/ZH HelpDB effective key union。FAQ 规范身份源是
  EN/ZH effective `Q:<suffix>`／`A:<suffix>` 的完整 suffix union；一对问题和
  回答共同构成一个 identity。
- 基线 EN/ZH Help key 集合相等；FAQ 两种语言的 Q/A suffix 集合、问题物理
  顺序和配对均相等；无 override、空值、孤立 Q/A 或未解释 Help consumer，
  inventory blocking violations 为 0。
- FAQ 源文件注释宣称按定义顺序显示，但当前 `getAllFAQKeys()` 通过 DBM
  `firstkey`／`nextkey` 迭代，运行时菜单顺序不由文件顺序保证。Inventory 绑定
  EN/ZH 物理问题顺序作为 authoring evidence，并明确记录此消费者事实；本批不
  未经决策扩张为 FAQ 排序架构重构。

## 规范身份

Help：

1. `help:annotate.prompt`
2. `help:console-keycodes`
3. `help:interlevel-travel.altar.prompt`
4. `help:interlevel-travel.branch.prompt`
5. `help:interlevel-travel.depth.prompt`
6. `help:known-menu`
7. `help:level-map`
8. `help:macro-menu`
9. `help:pick-up`
10. `help:skill-menu`
11. `help:spell-library`
12. `help:stash-search.prompt`
13. `help:wiz-monster`

FAQ（按 EN/ZH 共同物理问题顺序）：

1. `faq:goal`
2. `faq:userdir`
3. `faq:roguelike difference`
4. `faq:survival`
5. `faq:downstairs`
6. `faq:cheating`
7. `faq:weapons`
8. `faq:religion`
9. `faq:ghosts`
10. `faq:abyss`
11. `faq:randart`
12. `faq:interact`
13. `faq:version`
14. `faq:beta`
15. `faq:bug`
16. `faq:idea`
17. `faq:help`
18. `faq:changes`
19. `faq:tiles lag`

生命周期：`help:console-keycodes` 是 `!USE_TILE_LOCAL` 下的 console-only
帮助；`help:wiz-monster` 是 wizard-only；其余 Help 条目为 current-player-help；
所有 FAQ 对均为 current-faq-menu-entry。低暴露条目不得省略。

## 输入摘要

| 精确 Git 输入 | SHA-256 |
|---|---|
| `crawl-ref/source/dat/database/help.txt` | `e2cb06acab7287b678b1bc80b09ecb0d84294d8e0711102f1cb747188a2e5867` |
| `crawl-ref/source/dat/database/zh/help.txt` | `3dc065a10c451ce802e6459e67aff2d2f516915353d506c5dd62ea1d7c3cfff3` |
| `crawl-ref/source/dat/database/FAQ.txt` | `f3dbee89b40b13032a810170851d8415de4858362c57560d4ed866aeade7ced8` |
| `crawl-ref/source/dat/database/zh/FAQ.txt` | `96419ca99954ad2d7f9cf796b88a48b9c620844e7cf634c03a7d51dcbc537303` |
| `crawl-ref/source/database.cc` | `0ce343d8f888d00c99bee4d0ebbcee39d0399d997830011de1dc1878a4165d2c` |
| `crawl-ref/source/database.h` | `cf9e39ab5bc35b9f8e8f1f7889d70a16f9262193ecdedb5fb11054e5dbd6dd0b` |
| `crawl-ref/source/command.cc` | `48d0159b323845bf1c3d38bfa9e0de564ad658ffbace871f4e76473cda75c7a3` |
| `crawl-ref/source/macro.cc` | `eb8e2b3d6bb57de4031f49f4b888f9634e76e5f086ed9c75585a7cb6dcf2b99b` |
| `crawl-ref/source/menu.cc` | `08a298fa90933f24d30e6f1b9adc42d0ecfcb930b768857bc6d0f180088a9f72` |
| `crawl-ref/source/invent.cc` | `3b7d4bae827ce7725f29a8c077789bec416d6dfa9f8ecaa24cc6ef809c01a28e` |
| `crawl-ref/source/known-items.cc` | `74c4222b88c65277ebde3a85cac24f4aabb2fe74007ad521fbf86826b83e3f9a` |
| `crawl-ref/source/wiz-mon.cc` | `851b9ff6f1091f38dfb8a4d615a10b784dbc4d9f43f469596908b040e34f883c` |
| `crawl-ref/source/format.cc` | `621c94ef36f821fee67a1497d69f32e6814018cf0349a612b6e6062761e9b9a8` |
| `crawl-ref/source/colour.cc` | `ea636830e8bbcbc28e8ab2581983388a00d949e0942038c53ca6309eea7512d2` |
| `docs/glossary.md` | `95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407` |

## 复用机制与已观察失效

- 复用 `command_inventory.py` 的 production TextDB parser、exact-Git blob
  读取、trusted Git 环境和 fail-closed `/tmp` 独占输出；不新增持久状态、全局
  schema 或第二套 final gate。
- 简单“遇到 `%%%%` 就取下一行”的探测会把分隔符后的注释误作 key，并漏掉
  `Q:version` 等真实 FAQ 条目；`help_inventory.py` 使用生产状态机消除该失效。
- 现有 `[zh-help]` Catch2/CI 主要覆盖通用 `?/` 查询和其他描述数据库，没有
  枚举 HelpDB/FAQDB 的 32 个逻辑 identity；本 inventory 补足完整性证明，后续
  运行时测试仍须走真实 `getHelpString()` 与 FAQ Q/A 消费者。
- 机械 token 比较只产生人工审阅候选，不自动裁决译文。基线已确认一项明确
  结构事实：`help:console-keycodes` 中文 `-1012` 后是 `</2>`，英文对应 `</w>`；
  它将在该 identity 证据卡中判断并提出修订，而不阻止 inventory 冻结。

## 验收标准

1. Inventory identities 完整、唯一、确定排序；Help EN/ZH key 集与 FAQ
   Q/A suffix 集双向相等，每个 FAQ suffix 恰有一个 Q 和一个 A。
2. 每个 Help identity 都绑定精确 consumer literal、lookup、动态菜单入口、
   display sink 和生命周期；每个 FAQ identity 都绑定枚举、Q/A lookup、
   `unwrap_desc`、项目符号替换和菜单显示。
3. 每个 identity 恰有一张证据卡和一个终态结论：`keep`、`adjust`、
   `retranslate`、`defer terminology` 或 `defer implementation`。
4. 每张卡记录 EN/ZH、实际行为、目标、范围、条件、例外、数字、玩法后果、
   dependency group、格式/Lua/URL/路径/按键/list token、证据位置和置信度。
5. Lua 控制骨架与比较字符串必须保持；DB lookup key 保持英文。格式差异、
   `w` 标签内容、路径、URL、数字及列表差异先作为证据，不由扫描器判成错译。
6. Inventory 与 reviewed identity 集合双向差集为空，卡片顺序和机械字段绑定
   一致；每个 defer 有具体原因、owner 和 re-entry trigger。
7. `adjust`、`retranslate` 与 defer 集中交由人工确认；确认前不修改 ZH 资产。
8. 确认后由单一 `zh-translator` 顺序修改 `zh/help.txt` 与 `zh/FAQ.txt`；
   inventory/测试支持由 coder 在译文阶段之后处理，不并发重开翻译资产。
9. 干净候选使用 schema-v4 mechanical routing、translation-reviewer 与
   zh-code-reviewer readiness；若任务契约要求 `help-full`，只在全部 Ready 后
   对精确候选运行一次，再进入单次 final gate 和 merge-time validation。

## 依赖批次

1. Help：拾取、物品与已知物品菜单。
2. Help：地图、搜索、跨层旅行与注释。
3. Help：技能与法术库。
4. Help：宏、控制台键码与 wizard。
5. FAQ：游戏目标、生存与机制。
6. FAQ：用户目录、互动与环境。
7. FAQ：版本、测试、问题报告、建议、帮助、变更与 tiles 性能。

每个批次至少包含一个冻结 `keep` 对照；发现共享术语或事实问题时，先完成整个
依赖组再落地修改。

## 明确排除

- `crawl_manual.txt`、`quickstart.txt`、`macros_guide.txt`、
  `options_guide.txt`、`tiles_help.txt` 等独立文档。
- HelpDB/FAQDB 之外的通用 `?/` 查询描述、passive/status/mutation 文本。
- 已完成的 commands、tutorial、hints 身份和 R4 动态对白。
- 游戏机制、数值、存档 identity、协议键和英文 DB lookup key 修改。

## 重建入口

```bash
python3 .claude/scripts/help_inventory.py \
  --baseline-ref 7caba5166f4b2fd680ecbc258ea6ffe3f6249f50 \
  --inventory-output /tmp/help-inventory-issue52-baseline.json
```

输出采用独占新建；目标已存在时使用另一个明确的新文件名，不覆盖旧证据。结果
ledger 建立后追加 `--review-results docs/help-review-results.md`；候选落地后再追加
`--candidate-ref <exact-commit>`，证明每个已确认中文值与精确候选一致。
