# crawl/crawl 上游 Issue 追踪

> 范围：`crawl/crawl` 仓库中 **2026-08-09 之后（近三个月）** 创建的 open issue（当前 44 个；上游总开放 issue 344 个；更早的 issue 不纳入本轮）。

> 目的：判断上游反馈的问题是否影响本中文分支，是否需要本地修复，并记录证据、结论和修复提交。

> 状态标记：`pending` 待确认；`local-fix` 需本地修复；`already-fixed-upstream` 上游已修，等待同步；`upstream-only` 仅上游玩法/平台问题，本分支不单独修；`not-reproducible` 无法复现；`defer` 延期。


## 批次总表

| # | 创建日期 | 标题 | 标签 | 批次 | 是否需要本地修复 | 上游状态 | 结论 | 修复分支/提交 | 证据/备注 |
|---:|---|---|---|---|---|---|---|---|---|
| [5568](https://github.com/crawl/crawl/issues/5568) | 2026-11-08 | Xom locked up stairs with no monsters left on the level | — | W5 | no (defer) | open; no related fix through c17805322d | defer | — | xom.cc:6007-6108 按可达敌对怪物计数封锁/恢复楼梯；mon-death.cc:3710、mon-util.cc:3674、stairs.cc:324 与上游一致；附件无存档，无法区分计数异常/不可达怪物/恢复失败 |
| [5567](https://github.com/crawl/crawl/issues/5567) | 2026-11-08 | compiler warning sb.SB may be used uninitialized in json.cc | — | W1 | no | open; no fix through 7c4eee1bee | upstream-only | — | GCC 16 误报；`sb_init()` 初始化全部成员，初始化/访问/清理共用同一 `if (out)` 守卫；json.cc:59/849/954 |
| [5566](https://github.com/crawl/crawl/issues/5566) | 2026-11-07 | FR: Setting skill training targets in offline client | — | — | pending | pending | pending | — | — |
| [5561](https://github.com/crawl/crawl/issues/5561) | 2026-11-04 | Crash related to Xom effects/circle animation | — | W2 | no | 已由上游 `fb7e857c27` 修复（最低等级限制为 3） | already-fixed-upstream | — | 当前分支 xom.cc:6237-6245 已含修复；:6605-6608 显示彩环先于祝福；旧版 XL1-4 会抽到空候选 |
| [5557](https://github.com/crawl/crawl/issues/5557) | 2026-11-04 | Stuck "tough sensed monster" in monster list when worshipping Ashenzari | — | W1 | no (defer) | open; no related fix through 7c4eee1bee | defer | — | 未取得复现证据；候选缺口在 mutation.cc:3412 清除感知未标记重绘 / tileweb.cc:2030 vs :2093；需 WebTiles 增量复现后再定 |
| [5554](https://github.com/crawl/crawl/issues/5554) | 2026-11-02 | Being killed by monster Grave Claw produces message including "Killed by a jagged bones" | — | W1 | no | open; 上游 PR #5556 未合并 | upstream-only | — | 中文独立分支经 `_death_beam_display_name()` 输出“由锯齿骨头造成”，不经过英文冠词；zap-data.h:2342 / hiscores.cc:3579-3590 |
| [5553](https://github.com/crawl/crawl/issues/5553) | 2026-11-02 | Distracted enemies cast LRD at locations that hit only the player | — | W7 | no | open; no related fix through c17805322d | upstream-only | — | `ENCH_MISDIRECTED` 设置诱饵目标，但 LRD 独立遍历所有可爆破位置，命中目标只是加分项；mon-behv.cc:499 / mon-cast.cc:6492；强制命中诱饵会改变误导强度 |
| [5551](https://github.com/crawl/crawl/issues/5551) | 2026-11-02 | Spurious invisibility warnings | — | W5 | yes | open; no upstream fix through c17805322d | local-fix | `40780a6351` | 远处已知隐形怪首次移动时会把警告锚到玩家位置；monster.cc:5597 仅在 `you.see_cell(last_move_pos)` 时刷新记忆；新增 3 个回归场景（18 断言） |
| [5550](https://github.com/crawl/crawl/issues/5550) | 2026-11-01 | Webtiles: TerminalRecorder._spawn hangs at 100% CPU in containerized environments with high RLIMIT_NOFILE | — | W6 | yes | open; no upstream fix through c17805322d | local-fix | `1b2000d3d8` | `_spawn` 的 Python `for i in range(3, max_fd)` 改为 `os.closerange(3, max_fd)`；新增 `terminal_test.py` 覆盖高 NOFILE 场景 |
| [5549](https://github.com/crawl/crawl/issues/5549) | 2026-11-01 | Unusual monster items artefact regex | — | — | pending | pending | pending | — | — |
| [5539](https://github.com/crawl/crawl/issues/5539) | 2026-10-26 | Closet in Dungeon | Vaults | — | pending | pending | pending | — | — |
| [5538](https://github.com/crawl/crawl/issues/5538) | 2026-10-26 | In seeded games with pregen, being explore-trap shafted changes the RNG. | — | W7 | pending | pending | pending | — | — |
| [5535](https://github.com/crawl/crawl/issues/5535) | 2026-10-25 | Typo when memorising spells (levels instead of slots) | — | W1 | yes | open; no upstream fix through 7c4eee1bee | local-fix | `19cd875609` | spl-book.cc:931-940/1160 + source.txt:2359-2366/5320；英文改 spell slot(s)，中文沿用“法术容量” |
| [5531](https://github.com/crawl/crawl/issues/5531) | 2026-10-24 | Feature request (clua): Additional ability info. | — | — | pending | pending | pending | — | — |
| [5530](https://github.com/crawl/crawl/issues/5530) | 2026-10-23 | Fortress talisman ashenrazi can't remove talisman | — | — | pending | pending | pending | — | — |
| [5529](https://github.com/crawl/crawl/issues/5529) | 2026-10-23 | Feature request: delay/nullify repeated rapid inputs | — | — | pending | pending | pending | — | — |
| [5528](https://github.com/crawl/crawl/issues/5528) | 2026-10-23 | Spurious encounter messages with fog machines | — | W5 | no | open; no related fix through c17805322d | upstream-only | — | main.cc:2635 在环境更新(2663)前通知新见怪物；lm_fog.lua:209 生成雾、cloud.cc:438 更新遮挡；player-notices.cc:576 用 MF_SEEN 去重；延后通知会影响首次见面副作用 |
| [5526](https://github.com/crawl/crawl/issues/5526) | 2026-10-22 | New clang compile warning in 0.32-a0-7082-g32f959a6b0 | — | W5 | no | 已由上游 `201d16105e` 修复，早于 08290378b6 | already-fixed-upstream | — | `get_skill_bonus()` 缺 `override` 触发 `-Winconsistent-missing-override`；transform.cc:1483 已含 `const override` |
| [5524](https://github.com/crawl/crawl/issues/5524) | 2026-10-22 | Ru redirects out of range spells | — | W7 | pending | pending | pending | — | — |
| [5522](https://github.com/crawl/crawl/issues/5522) | 2026-10-19 | strange behavior with aiming fireball at solid features | — | W7 | pending | pending | pending | — | — |
| [5521](https://github.com/crawl/crawl/issues/5521) | 2026-10-19 | Vaults index caches tags intended to depend on player location | — | W6 | no | open; no related fix through c17805322d | upstream-only | — | `validate_map_def()` 解析期执行位置相关 Lua 并写入 `.idx`；levcomp.ypp:103、mapdef.cc:2863/2545/2569、maps.cc:183；reinit 不清标签；修复需区分索引/放置标签 |
| [5519](https://github.com/crawl/crawl/issues/5519) | 2026-10-18 | nicolae_transmutations_shop could use adjusting | — | W2 | no | open; no related fix through 7c4eee1bee | upstream-only | — | 属于商品池/权重玩法设计；shops.des:1386 与上游一致；中文 `Changing→变装`、`Room→间` 键存在，shopping.cc:1744 上下文翻译正常 |
| [5517](https://github.com/crawl/crawl/issues/5517) | 2026-10-17 | (console) Dragon Vein feature glyphs aren't hidable by any of the View Layers | — | W3 | no | open; no related fix through 7c4eee1bee | upstream-only | — | Dragon Veins 是地形；show.cc:374 始终更新地形，show.h:80 无地形图层开关；showsymb.cc:302 地形优先覆盖物品；中文菜单不影响规则 |
| [5515](https://github.com/crawl/crawl/issues/5515) | 2026-10-16 | Closet in Vaults | — | — | pending | pending | pending | — | — |
| [5503](https://github.com/crawl/crawl/issues/5503) | 2026-10-10 | Jade Form "Crystals" status display desync | — | W2 | yes | open; no upstream fix through 7c4eee1bee | local-fix | `98ee4b477b` | WebTiles 状态缓存遗漏 `light_text_formatted` 比较；tileweb.cc:1107 补齐；新增颜色变化/缓存稳定/状态移除回归测试 |
| [5499](https://github.com/crawl/crawl/issues/5499) | 2026-10-07 | RandArt sanguine talisman with fly loses fly upon exiting bat mode | — | — | pending | pending | pending | — | — |
| [5498](https://github.com/crawl/crawl/issues/5498) | 2026-10-07 | Jade crystals block the doorway | — | — | pending | pending | pending | — | — |
| [5483](https://github.com/crawl/crawl/issues/5483) | 2026-10-04 | Talisman hive describes melding helmet even thought it melds both the helmet and the extra hat slot from the unrandtart Zonguldrok | — | W3 | yes | open; no related fix through 7c4eee1bee | local-fix | `4c865c94b3` | `SLOT_HELMET` 覆盖所有头部装备槽（含 Zonguldrok 的额外 Hat+）；transform.cc:112-155 标签改为 `All Headgear`，source.txt:48902 新增“全部头部装备” |
| [5474](https://github.com/crawl/crawl/issues/5474) | 2026-10-02 | Unclear Dialogue when Entering Cocytus | — | W2 | no | open; no related fix through 7c4eee1bee | upstream-only | — | 警告原因在消息栏，确认弹窗只显示通用问句；中文“仍然进入下一层吗？”语义准确；stairs.cc:126/138 + prompt.cc:205；建议上游把警告原因纳入弹窗 |
| [5463](https://github.com/crawl/crawl/issues/5463) | 2026-09-29 | Coglin does not equip gizmo | — | — | pending | pending | pending | — | — |
| [5462](https://github.com/crawl/crawl/issues/5462) | 2026-09-29 | Fails to run on MacOS due to a failed GateKeeper check | — | W6 | no | open; upstream PR #4382 closed unmerged; no fix through c17805322d | upstream-only | — | ad-hoc 签名 `5baac99034a0`；mac/Makefile.app-bundle:107 与 verify_release_artifacts.py:605 已有签名/校验；docs/build-workflow.md:54 明确无公证；Apple Developer 签名/公证需另行授权 |
| [5449](https://github.com/crawl/crawl/issues/5449) | 2026-09-23 | Mutations from potion of mutation may fail to apply silently | — | W4 | no | open; no related fix through c17805322d | upstream-only | — | `_accept_mutation()` 未排除全部先天冲突，低魔力等会在 mutation.cc:1509 被拒绝且仅调试消息；中文通用提示“你感到极度怪异。”未误称成功；改候选/重抽会影响变异概率 |
| [5448](https://github.com/crawl/crawl/issues/5448) | 2026-09-22 | When my apostles got feared, I can remove fear by using recall apostle ability | — | — | pending | pending | pending | — | — |
| [5442](https://github.com/crawl/crawl/issues/5442) | 2026-09-21 | Ctrl + Direction(forced attack) - attacking ally interaction bugs | — | W4 | no | open; no related fix through c17805322d | upstream-only | — | main.cc:2868 远程动作前 `could_harm()` 提前拒绝；mon-util.cc:6089 可穿射对象判不可伤害，avatar 分支无提示；beam.cc:5952 正常射击允许穿过；属上游输入体验缺口 |
| [5441](https://github.com/crawl/crawl/issues/5441) | 2026-09-21 | Interlevel travel(ctrl+G) can cause player to use transporter. | — | W4 | no | open; no related fix through c17805322d | upstream-only | — | 旅行寻路把已知传送器作为路径边并自动进入（dd972a7a068 引入）；travel.cc:1967/970，1829 已有排除保护；禁用/加确认属上游旅行规则 |
| [5429](https://github.com/crawl/crawl/issues/5429) | 2026-09-19 | noise bar and equip bar at the same time | — | W3 | no | open; no related fix through 7c4eee1bee | upstream-only | — | ASCII 下 equip_bar=true 按设计替换噪音条；options_guide.txt:1699 与 output.cc:2269 互斥分支；Tiles 顶栏空间允许时已同时显示（output.cc:2134） |
| [5418](https://github.com/crawl/crawl/issues/5418) | 2026-09-14 | Rewinded Clockwork bee loses Justiciar's Inspire | — | — | pending | pending | pending | — | — |
| [5416](https://github.com/crawl/crawl/issues/5416) | 2026-09-13 | New invis breaks autofire | — | W4 | yes | open; no upstream fix through c17805322d | local-fix | `e08bcb7557` | 旧隐形位置被误计为射线阻挡；l-autofight.cc:99 忽略 `MB_REMEMBERED_INVIS`；新增 `test_autofight.cc`（34 断言） |
| [5414](https://github.com/crawl/crawl/issues/5414) | 2026-09-12 | Lua error when reloading saved game in tutorial mode | — | W6 | yes | open; no upstream fix through c17805322d | local-fix | `33a3331a5e` | `_reset_game()` 在关闭 Lua 前 `dungeon_events.clear()` + `env.markers.clear()`，避免旧教程监听器在坐标恢复时触发；main.o 编译通过 |
| [5413](https://github.com/crawl/crawl/issues/5413) | 2026-09-12 | memory leak in skill-menu-cc | — | W3 | yes | open; no related fix through 7c4eee1bee | local-fix | `c5de3666ed` | `MenuFreeform::attach_item` 拒绝越界项时不接管所有权；skill-menu 用 `m_unattached_items` 保留至 clear，新增 `test_skill_menu.cc`（16 断言） |

| [5384](https://github.com/crawl/crawl/issues/5384) | 2026-08-22 | Undefined behaviour from isalpha(). | — | — | pending | pending | pending | — | — |
| [5383](https://github.com/crawl/crawl/issues/5383) | 2026-08-22 | Unidentified Jewelry autopickup does not work | — | — | pending | pending | pending | — | — |
| [5378](https://github.com/crawl/crawl/issues/5378) | 2026-08-18 | Fungal Fisticloak "unwears" itself or destroys other aux gear on Poltergeist of  | — | — | pending | pending | pending | — | — |
| [5368](https://github.com/crawl/crawl/issues/5368) | 2026-08-09 | Teleport closet in spider | Vaults | — | — | pending | pending | pending | — | — |

## 方法与约束

- 仅纳入创建时间在 2026-08-09 之后（近三个月）的 open issue；更早的 issue 不纳入本轮追踪。
- 每个 issue 由独立子代理确认：是否已在上游 `master` 修复、是否影响本分支、是否需要本地修复。

- 需要修复时，在独立 worktree 中基于 `opencode/chn-trunk-pr` 实现最小修复，附测试/验证证据，再汇入集成分支。

- 不修改上游玩法与平衡；只处理与本分支相关的崩溃、编译、显示、文本、平台兼容问题。

- 修复提交格式建议：`fix(upstream-#<n>): <summary>`；不直接推送或创建 PR，由主代理统一收口。

