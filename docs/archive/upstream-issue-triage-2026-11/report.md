# crawl/crawl 近期 Issue 分析与修复报告（2026-11）

> 范围：`crawl/crawl` 中 2026-08-09 之后（近三个月）创建的 44 个 open issue。

> 方法：逐项读取上游 issue/评论，核对同步点 `08290378b6` 之后的上游提交，检查本分支代码与中文文本；结论分为 `local-fix`、`upstream-only`、`already-fixed-upstream`、`not-reproducible`、`defer`。

> 完整逐项证据、批次和引用路径见 [triage.md](triage.md)。


## 摘要

| 结论 | 数量 |
|---|---:|
| `local-fix` | 13 |
| `upstream-only` | 25 |
| `already-fixed-upstream` | 3 |
| `not-reproducible` | 1 |
| `defer` | 2 |
| **合计** | **44** |

## 本地修复（13）

| # | 标题 | 提交 | 修复要点 |
|---:|---|---|---|
| [5378](https://github.com/crawl/crawl/issues/5378) | Fungal Fisticloak "unwears" itself or destroys other aux gear on Poltergeist of | `7ce1568dcf` | 装备预检对同一 flex 槽重复预留；player-equip.cc:705 改用 `equipment.find_free_compatible_slot/remove`，模拟移除后再预留；新增 156 断言回归 |
| [5384](https://github.com/crawl/crawl/issues/5384) | Undefined behaviour from isalpha(). | `275bc4b5e5` | 13 处 `isalpha`/`tolower` 改用 `isaalpha`/`toalower`，拒绝非 ASCII 字节再做槽位索引；涉及 spl-cast.cc/item-use.cc/items.cc/l-item.cc/quiver.cc/lang-fake.cc；6 文件 `-j4` 编译通过 |
| [5413](https://github.com/crawl/crawl/issues/5413) | memory leak in skill-menu-cc | `c5de3666ed` | `MenuFreeform::attach_item` 拒绝越界项时不接管所有权；skill-menu 用 `m_unattached_items` 保留至 clear，新增 `test_skill_menu.cc`（16 断言） |
| [5414](https://github.com/crawl/crawl/issues/5414) | Lua error when reloading saved game in tutorial mode | `33a3331a5e` | `_reset_game()` 在关闭 Lua 前 `dungeon_events.clear()` + `env.markers.clear()`，避免旧教程监听器在坐标恢复时触发；main.o 编译通过 |
| [5416](https://github.com/crawl/crawl/issues/5416) | New invis breaks autofire | `e08bcb7557` | 旧隐形位置被误计为射线阻挡；l-autofight.cc:99 忽略 `MB_REMEMBERED_INVIS`；新增 `test_autofight.cc`（34 断言） |
| [5418](https://github.com/crawl/crawl/issues/5418) | Rewinded Clockwork bee loses Justiciar's Inspire | `5e2206426e` | 重新上弦走 `change_monster_type()` 清附魔；spl-summoning.cc:3864 按 `mon-place.cc` 规则补回 `ENCH_REGENERATION`（玩家来源 + Justicar's Regalia，300–500）；spl-summoning.o 编译通过 |
| [5483](https://github.com/crawl/crawl/issues/5483) | Talisman hive describes melding helmet even thought it melds both the helmet and the extra hat slot from the unrandtart Zonguldrok | `4c865c94b3` | `SLOT_HELMET` 覆盖所有头部装备槽（含 Zonguldrok 的额外 Hat+）；transform.cc:112-155 标签改为 `All Headgear`，source.txt:48902 新增“全部头部装备” |
| [5499](https://github.com/crawl/crawl/issues/5499) | RandArt sanguine talisman with fly loses fly upon exiting bat mode | `5a655166d1` | 退出临时形态时飞行缓存被清零；transform.cc:2356 在 `equipment.update()` 后按 `you.equip_flight()` 恢复 `ATTR_PERM_FLIGHT`；新增连续两次形态往返测试（77 断言） |
| [5503](https://github.com/crawl/crawl/issues/5503) | Jade Form "Crystals" status display desync | `98ee4b477b` | WebTiles 状态缓存遗漏 `light_text_formatted` 比较；tileweb.cc:1107 补齐；新增颜色变化/缓存稳定/状态移除回归测试 |
| [5530](https://github.com/crawl/crawl/issues/5530) | Fortress talisman ashenrazi can't remove talisman | `9f919b9cdd` | `transforming_is_unsafe()` 预览未镜像解除堡垒形态的双手武器迁移；transform.cc:1971 增加 `shift_twohander_to_slot(SLOT_OFFHAND)` + `update()`；新增 39 断言回归 |
| [5535](https://github.com/crawl/crawl/issues/5535) | Typo when memorising spells (levels instead of slots) | `19cd875609` | spl-book.cc:931-940/1160 + source.txt:2359-2366/5320；英文改 spell slot(s)，中文沿用“法术容量” |
| [5550](https://github.com/crawl/crawl/issues/5550) | Webtiles: TerminalRecorder._spawn hangs at 100% CPU in containerized environments with high RLIMIT_NOFILE | `1b2000d3d8` | `_spawn` 的 Python `for i in range(3, max_fd)` 改为 `os.closerange(3, max_fd)`；新增 `terminal_test.py` 覆盖高 NOFILE 场景 |
| [5551](https://github.com/crawl/crawl/issues/5551) | Spurious invisibility warnings | `40780a6351` | 远处已知隐形怪首次移动时会把警告锚到玩家位置；monster.cc:5597 仅在 `you.see_cell(last_move_pos)` 时刷新记忆；新增 3 个回归场景（18 断言） |

## 上游已修复（3）

| # | 标题 | 证据 |
|---:|---|---|
| [5448](https://github.com/crawl/crawl/issues/5448) | When my apostles got feared, I can remove fear by using recall apostle ability | 召回原无条件设 `BEH_SEEK` 覆盖恐惧逃跑；修复让带 `ENCH_FEAR` 的怪物保留原行为；spl-other.cc:172；该提交是同步点/集成分支祖先 |
| [5526](https://github.com/crawl/crawl/issues/5526) | New clang compile warning in 0.32-a0-7082-g32f959a6b0 | `get_skill_bonus()` 缺 `override` 触发 `-Winconsistent-missing-override`；transform.cc:1483 已含 `const override` |
| [5561](https://github.com/crawl/crawl/issues/5561) | Crash related to Xom effects/circle animation | 当前分支 xom.cc:6237-6245 已含修复；:6605-6608 显示彩环先于祝福；旧版 XL1-4 会抽到空候选 |

## 无法复现（1）

| # | 标题 | 证据 |
|---:|---|---|
| [5463](https://github.com/crawl/crawl/issues/5463) | Coglin does not equip gizmo | 玩家 XL14 发明 gizmo 未装备；acquire.cc:2029/1519 放入背包并立即 `equip_item(SLOT_GIZMO)`，player-equip.cc:1597 登记；需报告者存档和按键序列 |

## 延期（2）

| # | 标题 | 证据 |
|---:|---|---|
| [5557](https://github.com/crawl/crawl/issues/5557) | Stuck "tough sensed monster" in monster list when worshipping Ashenzari | 未取得复现证据；候选缺口在 mutation.cc:3412 清除感知未标记重绘 / tileweb.cc:2030 vs :2093；需 WebTiles 增量复现后再定 |
| [5568](https://github.com/crawl/crawl/issues/5568) | Xom locked up stairs with no monsters left on the level | xom.cc:6007-6108 按可达敌对怪物计数封锁/恢复楼梯；mon-death.cc:3710、mon-util.cc:3674、stairs.cc:324 与上游一致；附件无存档，无法区分计数异常/不可达怪物/恢复失败 |

## 上游问题（25）

| # | 标题 | 结论/证据 |
|---:|---|---|
| [5368](https://github.com/crawl/crawl/issues/5368) | Teleport closet in spider | `grunt_spider_rune_circles` 墙体布局形成孤立格；spider.des:2284；dungeon.cc:1324 设 `FPROP_NO_TELE_INTO`，spl-transloc.cc:1180 排除目标；d09647f 已含保护 |
| [5383](https://github.com/crawl/crawl/issues/5383) | Unidentified Jewelry autopickup does not work | 移动时先鉴定地面物品（player.cc:999→items.cc:1035），`_autopickup_subtype()` 改用已知类型（items.cc:3177）；旧机制 c4c869ff2ff 因强制拾取副作用删除；等待兼顾显式类型与冗余过滤的上游方案 |
| [5429](https://github.com/crawl/crawl/issues/5429) | noise bar and equip bar at the same time | ASCII 下 equip_bar=true 按设计替换噪音条；options_guide.txt:1699 与 output.cc:2269 互斥分支；Tiles 顶栏空间允许时已同时显示（output.cc:2134） |
| [5441](https://github.com/crawl/crawl/issues/5441) | Interlevel travel(ctrl+G) can cause player to use transporter. | 旅行寻路把已知传送器作为路径边并自动进入（dd972a7a068 引入）；travel.cc:1967/970，1829 已有排除保护；禁用/加确认属上游旅行规则 |
| [5442](https://github.com/crawl/crawl/issues/5442) | Ctrl + Direction(forced attack) - attacking ally interaction bugs | main.cc:2868 远程动作前 `could_harm()` 提前拒绝；mon-util.cc:6089 可穿射对象判不可伤害，avatar 分支无提示；beam.cc:5952 正常射击允许穿过；属上游输入体验缺口 |
| [5449](https://github.com/crawl/crawl/issues/5449) | Mutations from potion of mutation may fail to apply silently | `_accept_mutation()` 未排除全部先天冲突，低魔力等会在 mutation.cc:1509 被拒绝且仅调试消息；中文通用提示“你感到极度怪异。”未误称成功；改候选/重抽会影响变异概率 |
| [5462](https://github.com/crawl/crawl/issues/5462) | Fails to run on MacOS due to a failed GateKeeper check | ad-hoc 签名 `5baac99034a0`；mac/Makefile.app-bundle:107 与 verify_release_artifacts.py:605 已有签名/校验；docs/build-workflow.md:54 明确无公证；Apple Developer 签名/公证需另行授权 |
| [5474](https://github.com/crawl/crawl/issues/5474) | Unclear Dialogue when Entering Cocytus | 警告原因在消息栏，确认弹窗只显示通用问句；中文“仍然进入下一层吗？”语义准确；stairs.cc:126/138 + prompt.cc:205；建议上游把警告原因纳入弹窗 |
| [5498](https://github.com/crawl/crawl/issues/5498) | Jade crystals block the doorway | 晶体是怪物实体而非墙；穿墙不含穿门，占据门格时拒绝关门（player.cc:9544）；推晶体是独立机制（player.cc:705）；属上游玩法决定 |
| [5515](https://github.com/crawl/crawl/issues/5515) | Closet in Vaults | 上游定位为 `nicolae_vaults_bisected_inception`，`no_tele_into` 可能是有意设计；vaults_rooms_empty.des:1539；与 #5539 为不同地图 |
| [5517](https://github.com/crawl/crawl/issues/5517) | (console) Dragon Vein feature glyphs aren't hidable by any of the View Layers | Dragon Veins 是地形；show.cc:374 始终更新地形，show.h:80 无地形图层开关；showsymb.cc:302 地形优先覆盖物品；中文菜单不影响规则 |
| [5519](https://github.com/crawl/crawl/issues/5519) | nicolae_transmutations_shop could use adjusting | 属于商品池/权重玩法设计；shops.des:1386 与上游一致；中文 `Changing→变装`、`Room→间` 键存在，shopping.cc:1744 上下文翻译正常 |
| [5521](https://github.com/crawl/crawl/issues/5521) | Vaults index caches tags intended to depend on player location | `validate_map_def()` 解析期执行位置相关 Lua 并写入 `.idx`；levcomp.ypp:103、mapdef.cc:2863/2545/2569、maps.cc:183；reinit 不清标签；修复需区分索引/放置标签 |
| [5522](https://github.com/crawl/crawl/issues/5522) | strange behavior with aiming fireball at solid features | 火球在实体格结束，爆炸范围被地形检查截断（beam.cc:7327）；临时树烧毁还原为墙会截断；火云每格 1/3 概率（beam.cc:1022）；修复会改变实际伤害范围 |
| [5524](https://github.com/crawl/crawl/issues/5524) | Ru redirects out of range spells | Ru 在法术选择前重定向到施法者自身并绕过 tracer 判定；mon-cast.cc:5409 / mon-util.cc:3761；简单距离检查会误伤爆炸/特殊瞄准，属上游干扰时机 |
| [5528](https://github.com/crawl/crawl/issues/5528) | Spurious encounter messages with fog machines | main.cc:2635 在环境更新(2663)前通知新见怪物；lm_fog.lua:209 生成雾、cloud.cc:438 更新遮挡；player-notices.cc:576 用 MF_SEEN 去重；延后通知会影响首次见面副作用 |
| [5529](https://github.com/crawl/crawl/issues/5529) | Feature request: delay/nullify repeated rapid inputs | 请求可配置 5–20ms 快速按键过滤，属无障碍功能设计；client.js:213 无过滤，main.cc:2841/macro.cc:931 无毫秒判重；windowmanager-sdl.cc:1072 仅处理长按重复 |
| [5531](https://github.com/crawl/crawl/issues/5531) | Feature request (clua): Additional ability info. | `you.ability_info()` 仅返回名称/可用性/快捷键（l-you.cc:938），未暴露失败率；ability.cc:4278 的 `tal.fail` 是随机阈值不能直接当百分比；属上游 clua API 缺口 |
| [5538](https://github.com/crawl/crawl/issues/5538) | In seeded games with pregen, being explore-trap shafted changes the RNG. | `classic` 按实际进入顺序生成楼层，竖井跳层改变同分支 RNG 顺序；options_guide.txt:464-482 明确不保证同种子稳定；incremental 才预生成被跳过楼层（PR #1094） |
| [5539](https://github.com/crawl/crawl/issues/5539) | Closet in Dungeon \| Vaults | `hiddenorc1_lemuel` 墙体布局可能形成孤立格；orc.des:322 与上游一致，dungeon.cc:1322 标记禁传送、teleport.cc:181 检查 |
| [5549](https://github.com/crawl/crawl/issues/5549) | Unusual monster items artefact regex | `unusual_monster_items` 只匹配装备名，不含类别前缀；`artefact`/`unrand` 由 `item_prefix()` 单独生成，不经过该匹配；items.cc:801-807 / item-name.cc:4044-4047 / options_guide.txt:1830-1839 |
| [5553](https://github.com/crawl/crawl/issues/5553) | Distracted enemies cast LRD at locations that hit only the player | `ENCH_MISDIRECTED` 设置诱饵目标，但 LRD 独立遍历所有可爆破位置，命中目标只是加分项；mon-behv.cc:499 / mon-cast.cc:6492；强制命中诱饵会改变误导强度 |
| [5554](https://github.com/crawl/crawl/issues/5554) | Being killed by monster Grave Claw produces message including "Killed by a jagged bones" | 中文独立分支经 `_death_beam_display_name()` 输出“由锯齿骨头造成”，不经过英文冠词；zap-data.h:2342 / hiscores.cc:3579-3590 |
| [5566](https://github.com/crawl/crawl/issues/5566) | FR: Setting skill training targets in offline client | 旧目标预填后编辑器从首字符覆盖（skill-menu.cc:1104、precision-menu.cc:785），WebTiles 全选（cio.cc:726、textinput.js:117）；属通用输入编辑器 UX，改本地会影响其他输入框 |
| [5567](https://github.com/crawl/crawl/issues/5567) | compiler warning sb.SB may be used uninitialized in json.cc | GCC 16 误报；`sb_init()` 初始化全部成员，初始化/访问/清理共用同一 `if (out)` 守卫；json.cc:59/849/954 |

## 验证

- 每个本地修复在独立 worktree 中做了定向验证；代码类修复多数跑过绑定范围的 `code` profile（构建、中文 smoke、定向 Catch2）。
- 集成分支最终 `verify_zh.sh --profile ci --base chn-trunk --head 672f60d33f`：0 failures。
- 13 个修复合并后的完整编译与运行由 GitHub Actions 验证。
- 已知缺口：`#5550` 本机缺 `tornado` 未复跑 WebTiles 测试；部分修复未做交互式实机复测。

## 上游跟进

- 关注仍未合并的上游 PR：#5555（堡垒/Ashenzari）、#5556（Grave Claw 冠词）、#5452（发条蜂再生）、#5407（isalpha）、#5559（未鉴定首饰自动拾取）。
- 上游已修复但 issue 仍开放：#5561、#5526、#5448。
- 下次同步时优先核对以上提交，避免重复应用本地补丁。
