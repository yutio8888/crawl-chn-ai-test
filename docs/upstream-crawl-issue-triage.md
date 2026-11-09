# crawl/crawl 上游 Issue 追踪

> 范围：`crawl/crawl` 仓库中 2026-09-01 之后创建的 open issue（当前抓取 40 个；上游总开放 issue 344 个，历史项分批补入）。

> 目的：判断上游反馈的问题是否影响本中文分支，是否需要本地修复，并记录证据、结论和修复提交。

> 状态标记：`pending` 待确认；`local-fix` 需本地修复；`already-fixed-upstream` 上游已修，等待同步；`upstream-only` 仅上游玩法/平台问题，本分支不单独修；`not-reproducible` 无法复现；`defer` 延期。


## 批次总表

| # | 创建日期 | 标题 | 标签 | 批次 | 是否需要本地修复 | 上游状态 | 结论 | 修复分支/提交 | 证据/备注 |
|---:|---|---|---|---|---|---|---|---|---|
| [5568](https://github.com/crawl/crawl/issues/5568) | 2026-11-08 | Xom locked up stairs with no monsters left on the level | — | — | pending | pending | pending | — | — |
| [5567](https://github.com/crawl/crawl/issues/5567) | 2026-11-08 | compiler warning sb.SB may be used uninitialized in json.cc | — | W1 | pending | pending | pending | — | — |
| [5566](https://github.com/crawl/crawl/issues/5566) | 2026-11-07 | FR: Setting skill training targets in offline client | — | — | pending | pending | pending | — | — |
| [5561](https://github.com/crawl/crawl/issues/5561) | 2026-11-04 | Crash related to Xom effects/circle animation | — | — | pending | pending | pending | — | — |
| [5557](https://github.com/crawl/crawl/issues/5557) | 2026-11-04 | Stuck "tough sensed monster" in monster list when worshipping Ashenzari | — | W1 | pending | pending | pending | — | — |
| [5554](https://github.com/crawl/crawl/issues/5554) | 2026-11-02 | Being killed by monster Grave Claw produces message including "Killed by a jagged bones" | — | W1 | pending | pending | pending | — | — |
| [5553](https://github.com/crawl/crawl/issues/5553) | 2026-11-02 | Distracted enemies cast LRD at locations that hit only the player | — | — | pending | pending | pending | — | — |
| [5551](https://github.com/crawl/crawl/issues/5551) | 2026-11-02 | Spurious invisibility warnings | — | — | pending | pending | pending | — | — |
| [5550](https://github.com/crawl/crawl/issues/5550) | 2026-11-01 | Webtiles: TerminalRecorder._spawn hangs at 100% CPU in containerized environments with high RLIMIT_NOFILE | — | — | pending | pending | pending | — | — |
| [5549](https://github.com/crawl/crawl/issues/5549) | 2026-11-01 | Unusual monster items artefact regex | — | — | pending | pending | pending | — | — |
| [5539](https://github.com/crawl/crawl/issues/5539) | 2026-10-26 | Closet in Dungeon | Vaults | — | pending | pending | pending | — | — |
| [5538](https://github.com/crawl/crawl/issues/5538) | 2026-10-26 | In seeded games with pregen, being explore-trap shafted changes the RNG. | — | — | pending | pending | pending | — | — |
| [5535](https://github.com/crawl/crawl/issues/5535) | 2026-10-25 | Typo when memorising spells (levels instead of slots) | — | W1 | pending | pending | pending | — | — |
| [5531](https://github.com/crawl/crawl/issues/5531) | 2026-10-24 | Feature request (clua): Additional ability info. | — | — | pending | pending | pending | — | — |
| [5530](https://github.com/crawl/crawl/issues/5530) | 2026-10-23 | Fortress talisman ashenrazi can't remove talisman | — | — | pending | pending | pending | — | — |
| [5529](https://github.com/crawl/crawl/issues/5529) | 2026-10-23 | Feature request: delay/nullify repeated rapid inputs | — | — | pending | pending | pending | — | — |
| [5528](https://github.com/crawl/crawl/issues/5528) | 2026-10-23 | Spurious encounter messages with fog machines | — | — | pending | pending | pending | — | — |
| [5526](https://github.com/crawl/crawl/issues/5526) | 2026-10-22 | New clang compile warning in 0.32-a0-7082-g32f959a6b0 | — | — | pending | pending | pending | — | — |
| [5524](https://github.com/crawl/crawl/issues/5524) | 2026-10-22 | Ru redirects out of range spells | — | — | pending | pending | pending | — | — |
| [5522](https://github.com/crawl/crawl/issues/5522) | 2026-10-19 | strange behavior with aiming fireball at solid features | — | — | pending | pending | pending | — | — |
| [5521](https://github.com/crawl/crawl/issues/5521) | 2026-10-19 | Vaults index caches tags intended to depend on player location | — | — | pending | pending | pending | — | — |
| [5519](https://github.com/crawl/crawl/issues/5519) | 2026-10-18 | nicolae_transmutations_shop could use adjusting | — | — | pending | pending | pending | — | — |
| [5517](https://github.com/crawl/crawl/issues/5517) | 2026-10-17 | (console) Dragon Vein feature glyphs aren't hidable by any of the View Layers | — | — | pending | pending | pending | — | — |
| [5515](https://github.com/crawl/crawl/issues/5515) | 2026-10-16 | Closet in Vaults | — | — | pending | pending | pending | — | — |
| [5503](https://github.com/crawl/crawl/issues/5503) | 2026-10-10 | Jade Form "Crystals" status display desync | — | — | pending | pending | pending | — | — |
| [5499](https://github.com/crawl/crawl/issues/5499) | 2026-10-07 | RandArt sanguine talisman with fly loses fly upon exiting bat mode | — | — | pending | pending | pending | — | — |
| [5498](https://github.com/crawl/crawl/issues/5498) | 2026-10-07 | Jade crystals block the doorway | — | — | pending | pending | pending | — | — |
| [5483](https://github.com/crawl/crawl/issues/5483) | 2026-10-04 | Talisman hive describes melding helmet even thought it melds both the helmet and the extra hat slot from the unrandtart Zonguldrok | — | — | pending | pending | pending | — | — |
| [5474](https://github.com/crawl/crawl/issues/5474) | 2026-10-02 | Unclear Dialogue when Entering Cocytus | — | — | pending | pending | pending | — | — |
| [5463](https://github.com/crawl/crawl/issues/5463) | 2026-09-29 | Coglin does not equip gizmo | — | — | pending | pending | pending | — | — |
| [5462](https://github.com/crawl/crawl/issues/5462) | 2026-09-29 | Fails to run on MacOS due to a failed GateKeeper check | — | — | pending | pending | pending | — | — |
| [5449](https://github.com/crawl/crawl/issues/5449) | 2026-09-23 | Mutations from potion of mutation may fail to apply silently | — | — | pending | pending | pending | — | — |
| [5448](https://github.com/crawl/crawl/issues/5448) | 2026-09-22 | When my apostles got feared, I can remove fear by using recall apostle ability | — | — | pending | pending | pending | — | — |
| [5442](https://github.com/crawl/crawl/issues/5442) | 2026-09-21 | Ctrl + Direction(forced attack) - attacking ally interaction bugs | — | — | pending | pending | pending | — | — |
| [5441](https://github.com/crawl/crawl/issues/5441) | 2026-09-21 | Interlevel travel(ctrl+G) can cause player to use transporter. | — | — | pending | pending | pending | — | — |
| [5429](https://github.com/crawl/crawl/issues/5429) | 2026-09-19 | noise bar and equip bar at the same time | — | — | pending | pending | pending | — | — |
| [5418](https://github.com/crawl/crawl/issues/5418) | 2026-09-14 | Rewinded Clockwork bee loses Justiciar's Inspire | — | — | pending | pending | pending | — | — |
| [5416](https://github.com/crawl/crawl/issues/5416) | 2026-09-13 | New invis breaks autofire | — | — | pending | pending | pending | — | — |
| [5414](https://github.com/crawl/crawl/issues/5414) | 2026-09-12 | Lua error when reloading saved game in tutorial mode | — | — | pending | pending | pending | — | — |
| [5413](https://github.com/crawl/crawl/issues/5413) | 2026-09-12 | memory leak in skill-menu-cc | — | — | pending | pending | pending | — | — |

## 方法与约束

- 每个 issue 由独立子代理确认：是否已在上游 `master` 修复、是否影响本分支、是否需要本地修复。

- 需要修复时，在独立 worktree 中基于 `opencode/chn-trunk-pr` 实现最小修复，附测试/验证证据，再汇入集成分支。

- 不修改上游玩法与平衡；只处理与本分支相关的崩溃、编译、显示、文本、平台兼容问题。

- 修复提交格式建议：`fix(upstream-#<n>): <summary>`；不直接推送或创建 PR，由主代理统一收口。

