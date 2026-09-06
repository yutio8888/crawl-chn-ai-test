# Android 快捷键覆盖执行方案

依据：[快捷键与 Android 紧凑交互覆盖技术报告](android-shortcut-coverage-report.md) 与
[覆盖附录](android-shortcut-inventory.md)。制定日期 2026-09-06，代码基线
`8e71c1c1e7`（含报告所述 `ce63365bdc` 扫描器提交，`crawl-ref/source/` 输入链路
相对报告冻结基线无差异）。本文只是执行方案，不是实施记录；所有“已核实”均为
本次静态源码核对，未构建 APK、未操作设备。

## 1. 目标、非目标与已定决策

目标按报告第 6 节分三个阶段交付，每个阶段独立成 PR、独立验收、独立可合并：

| 阶段 | 交付 | 用户可见结果 |
|---|---|---|
| P1 | 等待/休息分离；游戏态第四行六个高频动作 | 紧凑键盘内完成等待、休息、饮用、阅读、射击、施法、能力 |
| P2 | 抽屉分组并补 14 个命令；喊叫子提示接入情境行 | 搜索、旅行、丢弃、盟友命令等不再依赖完整键盘 |
| P3 | 地图“更多”、瞄准高级动作、Ctrl 情境桥 | 排除区域、路径点、强制确认等高级操作触屏可达 |

非目标（沿用报告与 #105 的边界）：不新增持久控件配置系统、不做 PocketZot 式
三页分页、不实现通用宏层、不在 Java 复制游戏规则、不改桌面端行为、不改
`CMD_*` 语义。这些若被审阅提出，先按 AGENTS.md “删除、复用、缩窄”处理。

### 1.1 已定设计决策

**D1 中心键采用报告 3.3 的“推荐长期方案”**：GAME 上下文中心键改发真正的
`CMD_WAIT`，自动休息移到第四行槽 0。理由：当前中英文可见标签已经是“等待 /
Wait”，玩家心智模型已是等待；把行为改对是修正错标，而不是改变一个正确习惯。
NAVIGATION/TEXT 的中心键保持 `5`（tag 149）不动。若用户否决，退回“最小兼容
方案”只需把第 2.1 节的 tag 切换去掉、把槽 0 从休息改为等待，其余步骤不变。

**D2 第四行游戏态动作固定为**：`休息 饮用 阅读 射击 施法 能力`，对应键值
`'5' 'q' 'r' 'f' 'z' 'a'`。全部是可打印 ASCII，经现有
`sendContextKey()`→`InputConnection.commitText` 路径直达，不需要扩展原生
`nativeKeyboardKey` 白名单（该白名单目前只放行 `CK_LEFT/CK_RIGHT`）。休息不用
`CK_NUMPAD_5`，因为负值 CK 键会被白名单拒绝；`'5'` 在 `cmd-keys.h:141` 同样绑定
`CMD_REST`。

**D3 不可用状态交给原命令自身反馈**：无药水按“饮用”只会得到原生
“You aren't carrying any potions”且不耗回合；第一阶段不在 Java 或描述符中判断
可用性，避免复制游戏规则。是否在后续做灰显，等真机反馈再决定。

**D4 抽屉新增命令一律走 `selected_command` 回 `encode_command_as_key()`**：
已核实该函数直接编码枚举（`command.cc:1642`），不依赖默认键，因此
`CMD_AUTOFIGHT_NOMOVE` 可以照常返回主循环执行，不需要类似 Quick Cast 的
特殊执行路径。

**D5 短标签资源策略沿用情境键盘既有约定**：原生标签留空，Java 按
`(screen, slot, key)` 从 Android `values`/`values-zh`/`values-zh-rCN` 资源解析；
抽屉命令标签走 TextDB `dat/descript/commands.txt` 与 `zh/commands.txt` 的
`android command menu|<label>` 键。ZH TextDB 由 `zh-translator` 写，Android
资源与 C++/Java 由 `crawl-coder` 写；术语先跑 `context_resolve.sh`，并在验证
记录里保留 glossary SHA-256。

### 1.2 已确认事项（2026-09-06）

1. 确认 D1（中心键改等待）。已确认，按 D1 执行。
2. 跟踪 Issue：#129（挂在 #105 之下）。
3. 分支：`claude/android-shortcut-p1`。

## 2. 第一阶段：等待/休息分离与游戏态第四行

### 2.1 改动清单（按依赖顺序）

**C++（`crawl-ref/source/`）**

1. `ui.h`：`InputScreen` 末尾追加 `GAME`（值 18，注释“append only”已要求）。
2. `ui.cc` `input_descriptor()`：现有逻辑只在最内层 scope 拥有 `top_layout()`
   时发布动作并强制为 NAVIGATION。新增分支：当 `result.context == GAME`
   （即无顶层布局且 `MOUSE_MODE_COMMAND`）时，填 `screen = GAME` 与 D2 六个
   动作，标签留空。描述符是常量，JNI 去重（`syscalls.cc:348`）保证只发送一次；
   Activity 重建的 `input_context_refresh` 通道无需改动。
3. 不改 `InputActionScope`，不给主游戏套 scope（报告 7.1 明确警告 scope 会
   把上下文改成 NAVIGATION）。

**Java（`android-project/app/src/main/java/org/develz/crawl/`）**

4. `DCSSKeyboard.setInputContext()`：在现有 `explore.setTag(...)` 切换旁，为
   `key_mobile_5` 同步切换 tag：GAME → `KeyEvent.KEYCODE_PERIOD`，否则 → 149。
   `dispatchKeyEvent` 对非数字盘键走 `commitText(getUnicodeChar())`，得到 `.`
   → `CMD_WAIT`（`cmd-keys.h:14`）。实施时用 logcat `KEY` 级日志确认收到
   的是 `.` 而非空字符；若 `getUnicodeChar()` 在无字符映射的合成事件上返回 0，
   改为 tag `KEYCODE_S`（发 `s`，`cmd-keys.h:10` 同为 `CMD_WAIT`）。
5. 中心文字：GAME 用新资源 `keyboard_wait`，其余保持 `"5"`。
6. `contextLabelResource()` 增加 `case 18`，按键值映射：
   `'5'→keyboard_rest`、`'q'→keyboard_quaff`、`'r'→keyboard_read`、
   `'f'→keyboard_fire`、`'z'→keyboard_cast`、`'a'→keyboard_ability`。

**资源（`res/`）**

7. `keyboard_mobile.xml` `key_mobile_5`：`text`/`contentDescription` 改为
   `@string/keyboard_wait`；初始 tag 保持 149，由 Java 在上下文刷新时切换，
   避免 NAVIGATION 下发送句点。
8. `values*/strings.xml`：`keyboard_rest` 的文字改为真实语义“休息 / Rest”；
   新增 `keyboard_wait`“等待 / Wait”与上面五个动作标签。三套资源同时改。
9. `keyboard_extra_numeric.xml` `key_extra_5` 继续引用 `keyboard_rest` 且发
   149：改字串后它自动变成正确的“休息”，不改布局。

**测试（`.claude/scripts/tests/test_android_quickbar.py`）**

10. 第 94 行英文兜底断言改为 `keyboard_rest: "Rest"`，追加
    `keyboard_wait: "Wait"` 及五个新标签；第 107 行无障碍名称断言改为
    `key_mobile_5 → @string/keyboard_wait`。
11. 新增用例：`input_descriptor()` GAME 分支发布的六个键全部落在可打印
    ASCII 范围（防止将来有人放入 `CK_*` 而绕过白名单）；`InputScreen` 枚举
    最后一项为 `GAME` 且 Java `case 18` 存在；`setInputContext` 对
    `key_mobile_5` 的 tag 切换与 `explore` 成对出现。
12. 复跑现有 `test_publication_outside_loop_is_rejected` 与
    `test_menu_and_prompt_publish_current_actions_each_input_wait`，确认新分支
    没有破坏“只在 `wait_event` 中采样”的不变量。

### 2.2 术语

`context_resolve.sh "<task>" --task-type code --files <上述资源与 strings 文件>`。
glossary 当前没有 wait/rest 条目，短标签以 TextDB 中 “You start resting” 等
既有译文用词为准，不新增裁决；若 resolver 输出要求裁决，先记入
`docs/decisions.md` 再改资源。

### 2.3 验证顺序

1. `bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh --profile code`
   （提交后追加 `--base <base> --head <candidate>`）。新 worktree 需先复制
   Lua 5.4.8 `luac`，见记忆“Fresh-worktree luac gate”。
2. Android debug 构建：按 `docs/android-context-keyboard-verification.md` 的
   `make ANDROID=1 TILES=y android -j4` + 离线 Gradle `:app:assembleDebug`
   x86_64，`--max-workers=4`。构建前 rltiles 必须以 `TILES=y` 重新生成，否则
   出现图块空白（记忆“Android tiles artifact contamination”）。
3. 模拟器冒烟：`-gpu swangle_indirect`；确认四行高度不变、GAME 第四行六槽
   出现、进入背包/瞄准/确认后第四行被内层上下文接管、返回后恢复。
4. Pixel 8a 真机（序列号见记忆）：独立 applicationId 安装，不改字体缩放。
   用 `uiautomator dump` 取按钮坐标后以 `adb shell input tap` 点击真实按钮，
   不用 `input keyevent` 代替；`logcat -s AndroidKeyboard KEY` 留证。

### 2.4 验收矩阵（报告 7.2 中本阶段适用行）

| 场景 | 判定方法 |
|---|---|
| 空地点等待 | 一次点击后 HUD 回合数只增一次、坐标不变、无 Rest 状态、无“You start resting” |
| 敌人在视野内点等待 | 仍耗一次行动；不出现休息安全检查提示 |
| 脚下有物品/楼梯/商店/祭坛 | 只等待，不拾取、不换层、不进店、不祈祷 |
| 点休息 | 出现休息流程并可被敌人出现打断；等价于旧中心键 |
| 连点/长按等待 | 每次抬起只一次 `CMD_WAIT`；无 down/click 重复；长按不变成多回合 |
| 饮用/阅读/射击/施法/能力 | 有条目时进入原菜单并可用情境行确认/取消；无条目时只有原生提示且回合不变 |
| 瞄准/查看/大地图/文本输入 | 第四行显示内层动作；中心键显示 `5`，不再发句点 |
| 旋转/Home 返回/Activity 重建 | 重建后第四行按 GAME 描述符重发；无残留 tag、无重复派发 |
| 320dp 窄屏 + 字体 130% | 六槽文字可读、48dp 高度、无换行溢出；不满足则减到四槽并留“更多”入口，不加第五行 |

### 2.5 阶段产出

- PR 一个；`classify_reviewers.py` 路由 `zh-code-reviewer` 审阅 C++/Java，
  ZH 资源文字由 `translation-reviewer` 复核。
- `docs/android-shortcut-p1-verification.md`：候选 SHA、构建原文、逐行验收
  结果、截图与 logcat 路径、glossary SHA-256。
- GitHub Actions 通过后从目标检出合并；不从 worktree 内移动分支。

## 3. 第二阶段：抽屉扩展与喊叫子提示

前置：P1 已合并，真机反馈未要求调整第四行。

### 3.1 命令与分组

`topbar-drawer.cc` 的 `commands[]` 保持单一 `DrawerScroller`（现有测试
`test_single_scroller_has_no_page_or_submenu_navigation` 要求），在同一滚动
内容里用 `add_quick_section` 同款标题分四组，每组一个 `CommandGrid(3, ...)`：

| 组 | 保留 | 新增（默认键仅供对照） |
|---|---|---|
| 战斗与物品 | 背包、拾取、法术、能力 | 激活 `CMD_EVOKE`、指定物品发射 `CMD_FIRE_ITEM_NO_QUIVER`、主攻击 `CMD_PRIMARY_ATTACK`、原地自动战斗 `CMD_AUTOFIGHT_NOMOVE`、箭袋 `CMD_QUIVER_ITEM`、武器切换 `CMD_WEAPON_SWAP`、丢弃 `CMD_DROP`、喊叫/盟友 `CMD_SHOUT` |
| 探索与地图 | 探索、地图、当前位置出口 | 藏品搜索 `CMD_SEARCH_STASHES`、跨层旅行 `CMD_INTERLEVEL_TRAVEL`、地牢概览 `CMD_DISPLAY_OVERMAP` |
| 角色与信息 | 角色、技能、信仰、变异、已知物品、记忆法术、Full View | 消息历史 `CMD_READ_MESSAGES`、金币与购物清单 `CMD_LIST_GOLD` |
| 系统 | Commands 帮助 | 原生游戏菜单 `CMD_GAME_MENU`（保存/放弃/宏在其内且保留原确认） |

不直接加“保存退出”“放弃角色”按钮：交给原生 `GameMenu`，避免在抽屉里
出现破坏性动作且减少一层确认设计。每个新命令的 `command_type` 名称在实施时
以 `command-type.h` 核对，上表中 `CMD_LIST_GOLD`、`CMD_QUIVER_ITEM`、
`CMD_WEAPON_SWAP` 为待核对名。

### 3.2 每个新命令必须同时落地的四处

1. `rltiles/dc-commands.txt` “Mobile command panel” 段新增 `menu_<x>` 32px
   图标（`TILEG_MENU_*`）；无现成美术时先复用同段最接近的图标并在 PR 说明。
2. `dat/descript/commands.txt` 增加 `android command menu|<Label>` 与
   `android command menu summary|<Label>`；`dat/descript/zh/commands.txt` 由
   `zh-translator` 同步。测试
   `test_every_menu_label_resolves_in_both_description_databases` 会强制两库
   都有键。
3. `commands[]` 条目；更新 `test_all_commands_keep_their_fixed_order_and_identity`
   中固定顺序列表。
4. 条件不可用项（与 Pick Up/Exit 同款）：`CMD_SHOUT` 无盟友且不能喊叫时、
   `CMD_QUIVER_ITEM` 无可选动作时给 summary 原因，沿用 `available=false`
   长按描述路径。

### 3.3 喊叫子提示

`shout.cc:485–506` 是消息栏提示后 `getchm`，不是 `PromptMenu`，当前没有
描述符。方案：在该提示的读键前后用 `InputActionScope(InputScreen::SHOUT, ...)`
（枚举追加为 19）发布 `t/a/r/s/g/f` 与 Esc；`owner` 为当前 `top_layout()`
（消息栏提示无顶层布局时为空指针，与现有 `PromptMenu::show_in_msgpane` 登记
方式一致，实施时先核对该路径的 owner 语义）。Java `case 19` 按键值给六个短
标签；槽超过六个时优先 `t/a/r/s/f`，`g` 进入 P3 的“更多”范围。

### 3.4 验收要点

- 抽屉滚动成本：标准屏 3 列下四组总高度可在两屏内滚完；否则先把角色与信息组
  低频项后移，不加标签页。
- `CMD_AUTOFIGHT_NOMOVE`：敌人相邻/远处/无目标三种情况坐标均不变。
- 丢弃：进入多选、分类切换、数量、确认后背包滚动位置恢复。
- 喊叫：全部子命令、盟友目标选择与取消不需完整键盘，回合消耗与原版一致。
- 搜索：`Ctrl-F` 等价流程直接进入，结果页已有 `/` `=` 情境键继续可用。

## 4. 第三阶段：地图“更多”、瞄准高级动作、Ctrl 情境桥

前置：P2 合并；本阶段进入前先提交一页设计决策到 `docs/decisions.md`，因为
“更多”机制与 Ctrl 桥属于报告要求单独决策的持久机制。

1. **Ctrl 情境桥**：`sendContextKey()` 当前丢弃 1–26 的控制字符。扩展
   `nativeKeyboardKey` 接受 1–26，转换为 `SDLK_a + n - 1` 并设置
   `KMOD_CTRL`，由 `windowmanager-sdl.cc` 现有 modifier 逻辑产出 `CONTROL(x)`；
   Java 端把 `1 <= key <= 26` 转交原生桥。先用 `Ctrl-E`（清除排除）与
   `Ctrl-W`（路径点）做真机验证，再接页面。禁止把 `Ctrl-S` 暴露给主游戏
   描述符，只允许在局部页面（`?/` 排序）发布。
2. **大地图“更多”**：MAP 屏第 6 槽发布“更多”，打开一个复用抽屉 `describe`
   风格的动作弹窗，列出排除 `e`、半径 `R`（随后进入数字输入，TEXT 上下文
   自动切完整键盘，不做数字盘复用）、清除排除 `Ctrl-E`、路径点 `w`/`Ctrl-W`、
   查找祭坛/物品；弹窗有自己的 `InputActionScope`，关闭后恢复 MAP 描述符。
3. **瞄准“高级”**：TARGET 屏第 6 槽发布“高级”弹窗：终点确认、强制确认
   `!`/`@`、切换箭袋动作、路径显示。普通确认继续占槽 0，危险确认不抢默认槽。
4. **溢出页面**：物品描述/使用物品/技能/箭袋四个已确认截断点接入同一
   “更多”弹窗，把描述符里第 6 槽之后的候选动作列出；不改各页面已有前四槽
   逻辑。
5. 验收：地图排除/半径数字/清除/路径点/查找闭环；强制确认与普通确认分别
   校验；每个“更多”弹窗取消后回到原描述符且不继承底层动作。

## 5. 风险与应对

| 风险 | 应对 |
|---|---|
| `KEYCODE_PERIOD` 合成事件 `getUnicodeChar()` 返回 0 | 改用 `KEYCODE_S`；两者都绑定 `CMD_WAIT` |
| GAME 描述符与 `manualFull` 冲突：用户手动展开完整键盘时第四行归属 | 第四行属于 `keyboard_mobile`，完整布局下不可见；实施时核对 `key_context_*` 所在布局 |
| 第四行六个短标签在 320dp/130% 下换行 | 验收表已定：减槽加“更多”，不加行、不缩字号 |
| 抽屉新增图标需要美术 | 先复用同段图标并在 PR 标注；图标质量不阻塞功能合并 |
| ZH TextDB 与代码分属不同写者 | 先由 coder 提交英文键，再由 translator 在同 worktree 补 zh；`test_every_menu_label_resolves...` 在两者齐备前会红，PR 以该测试通过为合并条件 |
| Ctrl 桥扩展打开新的输入面 | 只在 P3 实施、只接受 1–26、按页面白名单发布；主游戏描述符测试断言键值全部可打印 |
| 真机 APK 与源码不一致的旧反馈 | 每份验证记录写明候选 SHA 与 applicationId |

## 6. 时间线与门槛

| 序 | 里程碑 | 完成定义 |
|---|---|---|
| 0 | 用户确认 1.2 三项 | Issue 建立或挂靠决定，分支前缀确定 |
| 1 | P1 代码就绪 | code profile 通过、测试新增与更新通过、模拟器冒烟通过 |
| 2 | P1 真机验收 | 2.4 矩阵全部通过并写入验证记录 |
| 3 | P1 审阅与合并 | 审阅 Ready、CI 通过、从目标检出合并 |
| 4 | P2 翻译键与图标就位 | 两库键齐备、固定顺序测试更新 |
| 5 | P2 真机验收与合并 | 3.4 要点通过 |
| 6 | P3 设计决策 | `docs/decisions.md` 记录“更多”机制与 Ctrl 桥的范围 |
| 7 | P3 实施、验收、合并 | 第 4 节验收通过 |

每个阶段结束都要回到报告 4.5 的缺口表，把对应行从“无入口”改为实际判定
等级，并把该表更新到附录；不在报告里提前宣称覆盖。
