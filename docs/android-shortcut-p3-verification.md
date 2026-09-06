# Android 快捷键 P1–P3 补充验收与 P3 验证记录

2026-09-06，Codex 内联执行 `zh-code-reviewer` 与 `translation-reviewer` 域；
不宣称独立审阅。术语表 SHA-256：
`366e807eaae5403b6c3925df5970cd237b447ead76fdb717b71273473b5db67e`。
原方案见 [执行方案](android-shortcut-execution-plan.md)。

## 候选与交付边界

- P1：`ba663f09a0`，PR #130 已合并为 `8745b0af18`；主检出已快进。
- P2：在原 `26a1eb6c1b` 上补充 `b915769e5c`，尚未推送该修复。
- P3：原 `affa46fccd` 上补充 `27307024dd`、`b94a07535c`；
  `626dca4961` 合入 P2 修复。最终代码候选 `b94a07535c`。
- 推送受自动审批阻止；尚不能宣称 P2/P3 合并就绪或交付完成。
  本地报告与既有截图不替代新候选的 GitHub CI。

## 审阅发现与修复

| 分类 | 证据与影响 | 处理 |
|---|---|---|
| Blocker（已修复） | `topbar-drawer.cc:show_more_actions_popup` 的布局接管导致原第四行消失，违反 §4.3；真机 `map-more` 可复现 | 弹窗登记调用页描述符，保持四行；不继承 more 列表，避免递归打开。`fixed-more`、`fixed-more-repeat` 复测 |
| Blocker（已修复） | `viewmap.cc:CMD_MAP_EXCLUDE_RADIUS` 原来直接 `getchm()`，不能自动展开数字输入，且取消会把 Escape 减去 `'0'` 当半径 | Android 使用 `TextInputScope`，显示既有命令标签与 0–9，仅接受数字；桌面路径保持原行为 |
| Blocker（已修复，待最终设备复测） | `CMD_MAP_ADD_WAYPOINT` 的原生编号提示同样直接读键，第四行仍是 MAP | Android 在调用 `add_waypoint` 期间登记 `TextInputScope` |
| Blocker（已修复，待最终设备复测） | P2 §3.2 要求的空箭袋、不能喊叫且无可命令盟友的禁用原因未实现 | 复用 `quiver::anything_to_quiver()`；`have_allies_to_order()` 复用喊叫模块现有 `_follows_orders` 条件；灰显和长按原因沿用抽屉路径 |
| Needs Fix（文档，已修复） | 方案摘要仍称 Ctrl 桥、溢出表误写四个直接槽、决策存放位置互相矛盾 | 对齐 D6–D8；溢出时实际为三个直接业务槽加“更多”；报告与附录缺口表增加实施后判定 |

输入和 i18n 审阅：`InputAction` 持有 `std::string`，借用译文立即复制；
原生弹窗返回键后才入宏缓冲，取消返回 0；列表仅从拥有顶层布局的 scope 读取。
地图/瞄准使用实时命令绑定，新增桥白名单仅 CK_F10。ZH 查找键与 CMD 身份未翻译。
新增不可用原因中英文语义一致，无格式占位符，未改变术语表。

## 本地验证

- P1 已有完整 CI 成功，复用原验证记录；本轮补测窄屏与长按。
- P2 `--profile code --base ba663f09a0 --head b915769e5c`：
  Run ID `20260906T070726906283241+0000-1345390-b915769e5c39`，Failures 0。
  快捷键测试 36 项通过。
- P3 `--profile code --base 26a1eb6c1b --head 27307024dd`：
  Run ID `20260906T065757077030735+0000-1237554-27307024dd30`，Failures 0。
  首次沙箱运行因库存 fixture 的 `git hash-object -w` 被只读 Git 对象库阻止，
  放开该写入、仍使用 `run_isolated.sh` 后重跑通过；不是忽略失败。
- P3 更新依赖与路径点修复后，正在验证 `b915769e5c..b94a07535c`。
  快捷键测试 41 项通过。所有重型检查与构建均使用资源隔离，构建不超过四个并行作业。
- APK `27307024dd`：`make ANDROID=1 TILES=y android -j4`，随后离线 Gradle
  `--max-workers=4 -Pandroid.injected.build.abi=arm64-v8a :app:assembleDebug`，
  `BUILD SUCCESSFUL in 1m 29s`。生成工程仅临时使用 `org.develz.crawl.shortcut129`。

## Pixel 8a 补充验收

设备证据存于本 worktree 的
`.claude/metrics/verify/android-shortcut-final-2026-09-06/`（git 忽略）。
测试只操作独立包 `org.develz.crawl.shortcut129`；保留原测试存档备份。
实际功能入口使用触屏按钮；巫师命令仅用于创建盟友、敌人等前置局面。
窄屏通过系统 density=540 在 1080px 宽设备上得到 320dp，字体为 130%；
测后恢复原 density=420 与 font_scale=1.0。

| 场景 | 结果与证据 |
|---|---|
| P1 320dp / 130% | 六槽无换行，高 162px=48dp；`narrow-game-stable`。该 GAME 行代码与 P1 候选相同 |
| P1 点击与长按 | 121.0→123.0：一次点击及一次 1.5 秒长按各执行一次等待，位置不变；`narrow-wait` |
| P1 重建恢复 | 改 density 后重启并读档，GAME 六槽和等待恢复；`narrow-game-stable` |
| P2 大字抽屉 | 320dp / 130% 分组可滚动、标签可读；`narrow-drawer`、`narrow-drawer-scroll`；两屏限制原方案只针对标准屏，标准屏复用 P2 原记录 |
| P2 六个盟友选项 | 喊叫、攻击、撤退、停止、守卫、跟随均经触屏执行；`orders-shout`、`attack-order-done`、`orders-retreat-done`、`orders-stop`、`orders-guard`、`orders-follow`。依次增加一次行动，取消不耗回合 |
| P3 地图列表 | 原生中文列表与第四行保持，重复点“更多”无递归；`fixed-more`、`fixed-more-repeat` |
| P3 禁区半径 | 数字提示自动 TEXT；点击完整键盘数字 5 后恢复 MAP；`fixed-radius-text`、`fixed-radius-5` |
| P3 清除禁区 | 原生 Ctrl-E 路径清除红色禁区标记；`fixed-clear` |
| P3 路径点 | 编号设置与查找已测试；旧包需手动展开，已修复，最终包自动展开仍待复测；`waypoint-prompt`、`waypoint-find-stable` |
| P3 技能溢出 | 列表有全部技能、帮助；执行全部技能后显示完整技能集合；`skills-more`、`skills-all` |
| P3 物品溢出 | 刺剑列表显示技能目标及刻写；执行刻写进入 TEXT，写入 P3check 后返回 GAME 且物品显示铭刻；`item-more`、`item-inscribe`、`item-inscribed` |
| P3 瞄准 | 更多列出强制/终点确认、箭袋、物体循环等；关闭恢复 TARGET 六槽；`target-more-correct` |

## 尚待闭合的验收门槛

- 最终 APK 对路径点自动输入与新增不可用原因的设备复测。
- 强制确认与普通确认的对照、箭袋和对象循环、技能帮助以及使用物品溢出的完整设备证据。
- P2/P3 新候选推送、GitHub Actions、完成域审核后的顺序合并。

当前结论：**Changes Requested（Validation Gaps）**；没有把未取得证据的项目写为通过。
