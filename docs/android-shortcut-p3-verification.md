# Android 快捷键 P1–P3 补充验收与 P3 验证记录

2026-09-06，Codex 内联执行 `zh-code-reviewer` 与 `translation-reviewer` 域；
不宣称独立审阅。术语表 SHA-256：
`366e807eaae5403b6c3925df5970cd237b447ead76fdb717b71273473b5db67e`。
原方案见 [执行方案](android-shortcut-execution-plan.md)。

## 候选与交付边界

- P1：`ba663f09a0`，PR #130 已合并为 `8745b0af18`；主检出已快进。
- P2：在原 `26a1eb6c1b` 上补充 `b915769e5c`；已推送，PR #131。
  `0758b73a37` 修正 CI 检出的既有注释空格。
- P3：原 `affa46fccd` 上补充 `27307024dd`、`b94a07535c`；
  `626dca4961` 合入 P2 修复。对象循环补充修复 `c54c569cf0`、`aa9bd4ad43`；最终代码候选 `aa9bd4ad43`。
- 用户随后明确授权公开推送，P2/P3 已发布；P3 PR #132。
  最新验收口径及 CI 状态见对应 PR 的合并审核记录。

## 审阅发现与修复

| 分类 | 证据与影响 | 处理 |
|---|---|---|
| Blocker（已修复） | `topbar-drawer.cc:show_more_actions_popup` 的布局接管导致原第四行消失，违反 §4.3；真机 `map-more` 可复现 | 弹窗登记调用页描述符，保持四行；不继承 more 列表，避免递归打开。`fixed-more`、`fixed-more-repeat` 复测 |
| Blocker（已修复） | `viewmap.cc:CMD_MAP_EXCLUDE_RADIUS` 原来直接 `getchm()`，不能自动展开数字输入，且取消会把 Escape 减去 `'0'` 当半径 | Android 使用 `TextInputScope`，显示既有命令标签与 0–9，仅接受数字；桌面路径保持原行为 |
| Blocker（已修复） | `CMD_MAP_ADD_WAYPOINT` 的原生编号提示同样直接读键，第四行仍是 MAP | Android 在调用 `add_waypoint` 期间登记 `TextInputScope` |
| Blocker（已修复） | P2 §3.2 要求的空箭袋、不能喊叫且无可命令盟友的禁用原因未实现 | 复用 `quiver::anything_to_quiver()`；`have_allies_to_order()` 复用喊叫模块现有 `_follows_orders` 条件；灰显和长按原因沿用抽屉路径 |
| Blocker（已修复） | 瞄准对象循环命令有枚举与键位，却没有 `process_command` 分支，真机按钮无效 | 临时收集已有物品候选并复用 `cycle_target`；RAII 恢复怪物候选和索引；复用 `_is_target_in_range` 处理 -1 与 hitfunc 范围 |
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
- P3 最终代码与依赖：`--profile code --base b915769e5c --head 950f523bab`，
  Run ID `20260906T072014976846241+0000-1547360-950f523bab89`，Failures 0。
  前一轮所有检查通过，但期间编辑验收文档触发候选变动门槛；固定文档后重跑通过。
  快捷键测试 41 项通过。对象循环完整修复的 code profile `b915769e5c..aa9bd4ad43`：
  `20260906T074400241935136+0000-1766433-aa9bd4ad43b8`，Failures 0。
  所有重型检查与构建均使用资源隔离，构建不超过四个并行作业。
- APK `27307024dd`：`make ANDROID=1 TILES=y android -j4`，随后离线 Gradle
  `--max-workers=4 -Pandroid.injected.build.abi=arm64-v8a :app:assembleDebug`，
  `BUILD SUCCESSFUL in 1m 29s`。最终代码 `b94a07535c`（构建 HEAD `950f523bab`）
  再构建 `BUILD SUCCESSFUL in 54s`，APK 摘要见证据目录 `final-apk.sha256`。
  对象循环完整修复 APK `aa9bd4ad43`：`BUILD SUCCESSFUL in 48s`，
  摘要见 `range-apk.sha256`；真机安装与回归通过。
  生成工程仅临时使用 `org.develz.crawl.shortcut129`。

## Pixel 8a 补充验收

设备证据存于本 worktree 的
`.claude/metrics/verify/android-shortcut-final-2026-09-06/`（git 忽略）。
测试只操作独立包 `org.develz.crawl.shortcut129`；测试结束已恢复原 Tester129 存档与
init.txt，逐文件 SHA-256 与备份一致。保留本次 APK，原正式包未操作。
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
| P3 路径点 | 编号设置与查找已测试；旧包需手动展开，最终包自动展开已复测通过；`waypoint-prompt`、`waypoint-find-stable`、`final-waypoint-stable`、`final-waypoint-set` |
| P3 技能溢出 | 列表有全部技能、帮助；执行全部技能后显示完整技能集合；`skills-more`、`skills-all`；帮助先进入技能说明模式，再次点击打开正文，`skills-help-page` |
| P3 物品溢出 | 刺剑列表显示技能目标及刻写；执行刻写进入 TEXT，写入 P3check 后返回 GAME 且物品显示铭刻；`item-more`、`item-inscribe`、`item-inscribed` |
| P3 使用物品溢出 | 装备菜单五候选保留前三项；更多中切换列表选中地面匕首，再执行描述打开该匕首详情；`equip-more-list`、`equip-switch-list`、`equip-describe` |
| P3 对象循环 | 最终 APK 下查看模式锁子甲→地面标枪→反向锁子甲；射击模式同样定位锁子甲，保持光路与 TARGET，回合不变；`object-range-first`、`object-range-next`、`object-range-back`、`object-fire-range` |
| P3 瞄准 | 更多列出强制/终点确认、箭袋、物体循环等；关闭恢复 TARGET 六槽；`target-more-correct` |

## 尚待闭合的验收门槛

- P2 长背包已用 41 件物品补测：详情取消返回保持滚动位置
  （`longpack-cancel-before/after`）；执行丢弃会关闭菜单回 GAME，
  再打开背包从顶部开始（`longpack-reopened`）。已向用户确认 §3.4
  是否要求跨关闭重开保持位置；此产品行为尚待明确。两种不可用原因均已通过，
  `empty-quiver-reason`、`unavailable-orders-verified`。
- 普通确认与更多中的强制确认分别实际投出标枪，
  `ordinary-confirm-final`、`force-shot-verified`；强制确认仍保留自伤与友军保护，
  `force-confirm-shot`、`force-confirm`。范围差异由 `select(false, false)` / `select(true, false)`
  的代码分支核验，未把投掷物射程内测试声称为射程外实测。
  箭袋前后切换已通过：石头与银标枪互换，`quiver-next-final`、`quiver-prev-final`。
- P2/P3 新候选推送、GitHub Actions、完成域审核后的顺序合并。

当前结论：**Changes Requested（Validation Gaps）**；没有把未取得证据的项目写为通过。

## 最终审核边界

P2 代码候选 `b915769e5c`，后续提交仅补充文档；P3 代码候选 `aa9bd4ad43`，
后续只合并 P2 验收记录与更新本报告，复用内容及依赖未变化的验证。
`classify_reviewers.py` 对 P2 相对 `8745b0af18`、P3 相对 P2 的差异均为 mixed，
两域已内联检查。P1 原未跟踪设计稿已通过命名 stash 保留，未覆盖或删除。

已发现的实现阻塞均修复；当前合并结论仍为 Changes Requested（Validation Gaps）：
P2 背包跨关闭重开是否恢复位置的验收口径，以及 P2/P3 新候选的 GitHub CI 尚待闭合。
原 P2 CI run `34017568264` 成功，但不覆盖新修复。自动审批两次拒绝推送到现有
公开 origin，要求用户明确授权代码载荷导出到该 GitHub 仓库；未绕过审批。

## GitHub CI 后续修正

P2 首轮 CI 的 checkwhite 检出 shout.h 既有注释双空格，`0758b73a37`
修正后 lint 通过，P3 同步该修正。P3 run `34021079499` 工具测试检出
`test_line_ending_normalization_equivalence` 硬编码的 directn.cc 行号因
对象循环代码插入而漂移；改用唯一源码语句定位同一条件编译区间，
仍断言 LF/CRLF/CR 的集合一致、锚点唯一且位于集合中，未豁免测试。
后续代码未改变 APK 功能，复用已完成的设备验证。
