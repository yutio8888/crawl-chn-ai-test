# Lane1 评审记录（第二轮抽检）

- 评审者：Claude Opus 5.5（claude-opus-5-5），Claude Code 子会话，默认参数；只读，未修改仓库。
- 输入：`review_input_lane1.md`（当时的工作路径；归档只保留样本顺序 `inputs/lane1_order.json`，内容可由 `samples_r2.json` 重建）（80 项，顺序种子1201）；未读取 lane2 输入或输出。
- 基线：stable 83af93c8bd、trunk 302ecba316，源码证据全部用 `git show <sha>:<path>` 查取。
- 术语上下文：`context_resolve.sh --task-type review`，glossary SHA-256 `fb814f3252f249fc230e81fa132dce6a9bb194b014d687fc1524c66827b351d7`（输出存 `lane1_ctx.txt`（当时的工作文件，未归档））。已读术语表，**不是盲评**。

## 方法
1. 逐项先读完整英文、消费者语句与条件，再给出独立语义判断，最后才对照术语表/catalog。
2. 动态拼句：在固定 stable/trunk 的 catalog（dat/i18n/zh/source.txt）中查出同一语句的所有相邻片段译文，按代码顺序拼成整句检查（C5-03、C5-06、C5-10、C4-09、C6-02）。
3. 怪物言语（C8）：核对 mon-util.cc do_mon_str_replacements 对 @foe@ / @foe,@ / @possessive@ 的中文路径及 strip_cjk_spaces。
4. 术语：核对同概念在两线 catalog 中的其他译法（Frozen Ramparts、magic reserves、character dump、jewellery、alarm trap）。

## 计数
ok 64 / readability 11 / objective_error 5 / insufficient_evidence 0；objective_error 缺陷点合计 5。

## 客观错误
- C5-09：religious standing（信仰/虔诚状态）误译为“宗教立场”。
- C5-03：“altar dedicated to … where”拼接后丢失“祭坛”，成句“找到一座<神名>，在那里…”。
- C1-10：character dump 译“角色存档信息”，误指存档；同概念他处为角色报告/转储。
- C6-06：Frozen Ramparts 法术名为“冰冻壁垒”，失败句写作“冰霜壁垒”（两线）。
- C7-01（仅 trunk）：藤蔓行者说明用“魔力储备/恢复魔力”，与 MP=法力及 stable 不一致。

## 总体观察（仅限本样本，不外推）
- 直接显示的短句、失败提示、技能说明整体忠实，格式标记与占位符完整。
- 本样本中的问题集中在：片段拼接后的整句完整性、同一概念跨键译名漂移（jewellery 珠宝/首饰/饰品；character dump；Frozen Ramparts），以及 trunk 残留的旧版种族说明译法。
- jewellery、resource "magic"（魔法 vs 法力）属共享短键/无术语条目，只列为建议，不建议单句修改。
