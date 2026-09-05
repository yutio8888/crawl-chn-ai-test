# Android 情境键盘验证记录

代码候选：`6b82440c54..HEAD`（当前分支；每次验证的确切 head 见下文）。仅在当前 worktree 提交，未 push、merge。
术语表 SHA-256：`366e807eaae5403b6c3925df5970cd237b447ead76fdb717b71273473b5db67e`。

## 实施提交

| 提交 | 内容 |
|---|---|
| `121d8d8177` | 一页实施说明、接口与验收边界 |
| `edfe7f39c2` | Android 描述符、布局所有者绑定、RAII 恢复、完整描述符 JNI 去重 |
| `7037cc22b7` | 六槽情境行、固定四行高度、手动完整键盘保留、InputConnection/SDL 按键入口、日志 |
| `e9a8e6295b` | 菜单、物品/法术描述、瞄准、是非/more、地图接入 |
| `b1fe3122ec` | 修复 pickup 菜单标签遗漏；新短标签改用 Android 中英文资源 |

原生物品/是非/more 标签继续用已有 `T_()`。新增短标签没有现成 TextDB 键，
按用户允许的 Android 资源方式，在 Java 显示端按界面和槽位解析；非零键值
表示动作存在，空槽不会因资源回退而激活。未修改 ZH 翻译资产。

物品按钮只取真实可用操作；法术描述页目前只支持查看和退出，故提供返回。
`!` 仅在菜单真的支持 action_cycle 时提供；普通 InvMenu 的 `!` 是物品类别
快捷键，不冒充动作切换。非分页菜单不显示无效的类别切换按钮。

## 构建

使用本 worktree 的 `make ANDROID=1 TILES=y android -j4` 准备工程，再运行
隔离包装下的 Gradle `:app:assembleDebug`，参数为
`--offline --no-daemon --max-workers=4 -Pandroid.injected.build.abi=x86_64`。
生成的 app/build.gradle 将 NDK jobs 限为四；SDK 路径仅写入忽略的 local.properties。
Gradle 缓存复制到临时位置；缺失 contrib 按当前 gitlink 从本机对象库解包，
未改其他 worktree 或子模块指针。

描述符提交通过 NDK C++11 语法编译；三个实施阶段的 Android debug 构建均成功。
最后恢复正式 applicationId 后的构建原文：

```text
BUILD SUCCESSFUL in 7s
36 actionable tasks: 11 executed, 25 up-to-date
```

APK：`crawl-ref/source/android-project/app/build/intermediates/apk/debug/app-debug.apk`。
这是 x86_64、versionCode=1 的本地 test-only debug APK，安装需要 `adb install -t`；
未使用发布签名。SHA-256：
`3f75226bf95edf088a4955bafa8037404f4ec8f3736d941e311dab50e70fd59d`。

## Code profile

首次执行 `verify_zh.sh --profile code` 未指定 base/head（未绑定范围，不能作为
某个完整提交范围的证据）；Run ID 为
`20260905T080418675402025+0000-3-7037cc22b713`，Scope 为 changed，
结果为 `Summary: 3 blocking failure(s)`。该次发现新增缺失标签、生成资产
副本被扫描和只读 Git 对象导致的 fixture 失败，均已修正或消除环境干扰。
随后在干净候选上完整执行：

```sh
bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh \
  --profile code --base 6b82440c54 --head b1fe3122ec
```

第二次暂时移出生成的 app/build 和 app/src/main/assets，执行完成后恢复；
允许验证 fixture 写当前 worktree 的 Git 对象。最终原文摘录：

```text
Run ID: 20260905T081509321339862+0000-75691-b1fe3122ecf5
Failures: 1
--- post-coder / code-static ---
RESULT: FAIL (exit 1)
--- zh smoke ---
Smoke test passed
RESULT: PASS
Summary: 1 blocking failure(s)
```

唯一失败阶段是 code-static：varargs 扫描与字符串拼接扫描遇到 `menu.cc`、
`directn.cc` 的 tree-sitter 预处理解析错误。对比基线与候选的所有 ERROR/missing
节点，类型与字节内容完全相同，只有插入代码之后的行号移动；directn 的基线
豁免绑定整文件 SHA，文件变更使豁免失效。未修改扫描器或扩大豁免。
Source/DB、翻译生命周期、movement、桌面编译、消息覆盖检查与 ZH smoke 均通过。
**自动 profile 未全绿；不能宣称 CI 通过。**

完整本地输出位于 `.claude/metrics/verify/`：

- `20260905T081509321339862+0000-75691-b1fe3122ecf5/verify.log`
- `coder-2026-09-05T08-15-16+00-00.log`
- `android-context-keyboard-parser-comparison.log`
- `android-context-keyboard-build.log`

## 模拟器与复审

在 x86_64 模拟器并存安装测试 applicationId `org.develz.crawl.contextkeyboard`，
保留原有不同签名应用及存档。该 applicationId 仅改本地生成文件，最终已恢复。
测试使用英语及应用级 zh-CN 资源；键盘高度均为 504 px。

- 紧凑/完整的 UIAutomator 边界相同：`[0,1833][1080,2337]`。
- 主地牢、文本输入、背包、物品描述、丢弃、拾取、瞄准、地图、是非提示之间
  切换时，SDL 保持 `1080x1697`，启动显示键盘后没有对应的 surfaceChanged。
- 手动展开后，背包 → 主地牢 → 背包仍为 `manualFull=true`。
- 背包中文槽位：确定、返回、上一类、下一类；单选未显示全选。
- A-01 分类切换：**待设备验证**。此前发送过“下一类”点击，但只有点击后
  仍显示装备类的截图，缺少切换前后的分类记录；当时其他分类是否非空也未
  确认，不能据此认定分类切换通过。“上一类”没有点击验证记录。后续须在
  至少两个非空分类间分别点击上一类/下一类，记录标题和物品列表变化。
- 丢弃菜单显示全选；拾取菜单显示确定、返回、全选。
- 物品页显示真实穿脱/丢弃等操作；点击丢弃已执行并恢复主地牢。
- 物品页返回恢复背包；是非提示显示是/否且否可取消。
- 瞄准显示确定、取消、上个目标、下个目标、自身；地图显示返回、上下行楼梯、
  传送门、陷阱；已点击自身/取消和上行楼梯/返回。

原始按钮边界及日志：`android-context-keyboard-buttons.log`、
`android-context-keyboard-smoke.log`、`android-context-keyboard-layout.log`，
均在上述本地验证目录。

分类器路由为 code / zh-code-reviewer。完整差异与修正复审结论：
`Ready — 0 Blocker，0 Needs Fix，0 Suggestion`。解析器限制经过人工补充审查；
该结论不是 merge 授权。

未验证：真机与其他 ABI、横屏/极端字号、所有物品种类、实战施法瞄准、法术
描述/已知物品/more 的完整运行时路径，以及显示/隐藏键盘的专门 resize 断言。
模拟器地牢图块区域显示为空白，未将本次键盘冒烟视作渲染正确性验证，也未
追查其基线归属。GitHub Actions 未运行（按要求不 push）。
下一步先在真机补齐这些交互，再处理扫描器基线解析限制并运行远端 CI。

## Pixel 8a 真机复测（2026-09-05）

本节补充并更新上文历史未验证项。代码为 `f2b595fef8`（含 Activity 重建时
重发描述符、Classic 1/2 恢复原热区偏好的修正）。设备为 Pixel 8a，Android 15，
`arm64-v8a`；所有设备命令均指定 `adb -s 44061JEKB02240`。
没有操作 `emulator-5554`，没有卸载或清除原游戏数据。测试包
`org.develz.crawl.contextkeyboard` 并存安装，应用语言 zh-CN；使用其独立目录中的
Human Conjurer 巫师角色 `PixelKeyboard`，不使用已有正式存档。

### 构建与图块空白归属

最终 APK：`/tmp/pixel-context-arm64-debug.apk`，SHA-256：
`07af148447dc917ee292f974f5fbb33138255a5059564f41435378ddbc41a983`。
`versionName=0.34.1-zh5-1-010-131-gf2b595fef8`，与 `build.h` 中的
`CRAWL_VERSION_LONG` 一致；只替换生成工程的 applicationId。

本次定位了两项构建准备问题，均已纠正后重新安装、验证：

1. 初次人为追加测试版 versionName 后缀，导致 Java 创建的缓存目录与原生版本号
   不一致。原文为 `DB directory .../cache.0.34.1-zh5-1-010-131-gf2b595fef8/db/
   does not exist and I can't create it`，随后退出时出现 `FORTIFY:
   pthread_mutex_lock called on a destroyed mutex`。改回一致版本号后可正常启动。
   这是初始测试构建配置失败，不能从整次任务记录中删除，也不计入最终 APK 的
   无崩溃结论。
2. 真机初次进入地牢也空白，且物品图标同样缺失。PNG 解码正常，例如诊断原文
   `texture floor.png 1024x2048 bpp=4 alpha=1072653`；但本地生成的
   `rltiles/tiledef-floor.cc` 图块信息全部为 `tile_info(0, 0, 0, 0, 0, 0, 0, 0)`。
   无 tiles 构建留下的生成数据被直接 Gradle 构建复用，零尺寸使图块被跳过。
   重新执行带 `TILES=y` 的生成步骤后恢复为
   `tile_info(32, 32, 0, 0, 0, 0, 32, 32)`；同步图集并重建后，墙、地板、角色、
   背包物品图标均正常。临时诊断代码已移除，无需修改 Surface/viewport 或资源路径。

因此空白归属为**构建产物污染**，不能归为模拟器 GPU 环境问题。旧模拟器 APK
本次没有复测，不能据真机修复结果声称该旧包已通过。后续运行过无 tiles 构建后，
必须重新准备 tiles 生成数据再运行 Android Gradle；只重新打包 PNG 不够。

本次修复构建产物的命令（均在当前 worktree，构建限制四任务）：

```sh
bash .claude/scripts/run_isolated.sh make -C crawl-ref/source/rltiles -j4 TILES=y
cp crawl-ref/source/rltiles/{floor,wall,feat,main,player,gui,icons}.png \
  crawl-ref/source/android-project/app/src/main/assets/dat/tiles/
# SDK、Gradle 缓存位置通过本机环境配置，不提交生成工程。
cd crawl-ref/source/android-project
./gradlew --offline --no-daemon --max-workers=4 \
  -Pandroid.injected.build.abi=arm64-v8a :app:assembleDebug
```

Gradle 实际通过 `run_isolated.sh` 在子 shell 中运行。最终构建/安装原文：

```text
BUILD SUCCESSFUL in 52s
36 actionable tasks: 7 executed, 29 up-to-date
Performing Streamed Install
Success
```

### 点击验收

以下证据均位于当前 worktree 的 `.claude/metrics/verify/`，文件名前缀统一为
`pixel-context-`；截图 `.png` 同时配有 `.xml` UIAutomator dump 与
`-window.log`。SDL 原生标题/列表不在 UIAutomator 树内，按截图核对；Java 按钮
按 resource-id 定位点击，不以发送等价硬件键替代按钮验收。

| 项目 | 点击前 → 点击后（通过） | 截图后缀 |
|---|---|---|
| 地牢渲染 | 空白 → 墙、地板、角色和快捷图标正常 | `loaded`、`tiles-restored` |
| A-01 下一类 | 装备：`a - +0 长袍（已穿戴）` → 药水：`g - 魔法药水` | `a01-before`、`a01-next` |
| A-01 上一类 | 药水页 → 原装备页，长袍列表恢复 | `a01-next`、`a01-prev` |
| 拾取全选、确定 | 匕首和药水未选 → 两项选中 → 菜单关闭，消息显示 `b - +0 匕首; d - 块状的棕色药水` | `pickup-before`、`pickup-selected`、`pickup-done` |
| 物品脱下、穿戴 | 点击 `(t)脱下`，护甲 2→0，消息确认脱下；重开页按钮变 `(w)穿戴`，点击后护甲恢复 2 | `item-before`、`item-removed`、`item-unworn`、`item-worn` |
| 瞄准下个、上个、自身 | 地精 → 老鼠 → 地精 → 玩家，黄色目标框和瞄准说明同步变化 | `target-before`、`target-next`、`target-prev`、`target-self` |
| 地图楼梯与返回 | 巫师揭示地图后，连续点下行楼梯使地图移到两个不同位置；上行楼梯返回入口区域；返回退出地图 | `map-before`、`map-stairs1`、`map-stairs2`、`map-up`、`map-return` |
| 是、否 | 原生 yesno 提示，分别点是/否后关闭；`crawl.mpr(tostring(crawl.yesno(...)))` 显示 `True` / `False` | `yes-before`、`no-before`、`yes-result`、`no-result` |
| 更多继续 | 临时 `force_more_message += .` 触发实际 `--更多-- 点按继续`；点击槽位“继续”后提示消失，恢复巫师命令输入 | `more-prompt`、`more-continued` |

拾取物品由巫师 `&%` 创建；瞄准使用 `&m` 创建 rat/goblin，`&E` 暂停时间，
使用魔法飞弹瞄准但不发射。是非通过巫师 Lua 调用真实 `yesno` 路径。
Lua 解释器内 `crawl.more()` 被原生明确抑制，因此未将这次无提示调用计为通过；
改用退出解释器后的实际消息提示，完成后以 `force_more_message -= .` 移除临时规则。

### 十轮稳定性、手动切换与生命周期

设备日志时区为 Asia/Shanghai。17:13:02–17:15:55 完成十轮：
主地牢 → 背包 → 长袍描述 → 退出两层 → 魔法飞弹瞄准 → 取消 →
巫师创建怪物的文本输入 → 取消。每种状态检查实际键盘树及情境按钮，
首末轮另存截图；共 51 次状态断言，50 份 `round-01-*` 至 `round-10-*` XML。
文本输入自动显示完整键盘，退出自动恢复紧凑。

`pixel-context-rounds.log` 与 `pixel-context-summary.log` 的原文摘录：

```text
device start 2026-09-05_17:13:02
device end 2026-09-05_17:15:55
rounds=10 state_checks=51 bounds=['[0,1833][1080,2337]']
round_context_changes=88
round_updateLayout=0
round_surfaceChanged=0
round_heights=['504']
manual_updateLayout=2
manual_surfaceChanged=0
final_pid=13104 fatal_segv_anr_fortify_gl_error_matches=0
```

键盘显示后的 SDL Surface 为 `1080x1712`。从 17:05:38 显示键盘至
17:16:54 首次 Home 前没有新的 surfaceChanged，涵盖以上所有点击测试、十轮
上下文测试，以及 17:16:06–17:16:24 手动完整/紧凑测试。
手动展开后进入背包、返回地牢仍保持完整键盘；再点击“紧凑”恢复，三份截图
`manual-full`、`manual-full-inv`、`manual-compact` 的边界均相同。

```text
09-05 17:05:38.762 13104 13104 V SDL     : Window size: 1080x1712
09-05 17:16:11.347 13104 13104 I AndroidKeyboard: context=1 screen=1 manualFull=true height=504
09-05 17:16:16.281 13104 13104 I AndroidKeyboard: context=0 screen=0 manualFull=true height=504
```

Home 返回用 `am task focus 185` 恢复原有游戏任务，背包四个情境按钮仍正确；
`home-before`、`home-resumed` 保留前后证据。首次尝试用 `am start` 启动 launcher
只是增加了一层 launcher，已用 Back 退出该层，再执行上述已有任务恢复测试；
没有将 launcher 截图冒充游戏恢复结果。后台 Surface 销毁/恢复会产生回调，
恢复尺寸仍为 `1080x1712`，不计为键盘上下文切换引起的 resize。

横屏支持：在背包中旋转后四个情境按钮仍显示，点击“下一类”成功从装备切到药水，
转回竖屏仍保留药水分类和正确按钮。证据 `landscape-inventory`、`landscape-next`、
`portrait-return`。横屏键盘边界 `[121,513][2400,1017]`，高度仍 504；
Surface 稳定于 `2279x513`，转回恢复 `1080x1712`。旋转本身会改变 Surface
尺寸并产生中间回调，不属于上述“同方向内切换键盘不 resize”的断言。
设备旋转设置已恢复原值 `free`、`accelerometer_rotation=1`、`user_rotation=0`。

最终 APK 从启动至旋转完成始终为 PID 13104。其完整 logcat 中未检出
SIGSEGV、Fatal、ANR、FORTIFY 或 Crawl.gl ERROR；events 缓冲无本测试包
am_anr/am_crash，exit-info 中没有最终进程退出记录。原文和检查结果保存在
`pixel-context-final-logcat.log`、`pixel-context-events.log`、
`pixel-context-exit-info.log`、`pixel-context-summary.log`。
初始错误版本号构建的失败另见 `pixel-context-initial-startup-failure.log`，
没有声称包含该失败在内的整次会话“零 Fatal”。

### 结果与边界

- 通过：arm64 debug 构建及并存安装、修复后的真机图块渲染、A-01 双向分类点击、
  拾取全选/确定、物品穿脱、瞄准前后目标/自身、地图楼梯/返回、是/否、更多继续、
  十轮稳定性、手动完整键盘保留与切回、Home 恢复、横竖屏恢复、最终运行无崩溃/ANR。
- 初始失败已解决：测试 versionName 不一致、无 tiles 的零坐标生成产物。
  本次没有遗留源代码修复，也没有未解决的本轮阻断缺陷。
- 未覆盖：模拟器和其他 ABI 复测、强制 Activity 重建（旋转由 configChanges
  接管，不能替代重建测试）、所有物品/法术描述/已知物品菜单变体、实际发射法术、
  键盘整体隐藏/显示专门断言。GitHub Actions 未运行，未 push。

Pixel 验证提交仅修改文档，源代码为 `f2b595fef8`。当时的零失败 code profile
范围仅为 `a45c7d2a77888e1d1237c7651dd5fe824bd768c1..f2b595fef86d76d9b0695bbb5be145efd87f54d8`，
只覆盖最后一个修复提交，不证明整条分支通过。原文为 `Summary: 0 blocking failure(s)`，记录：
`.claude/metrics/verify/20260905T083002357202476+0000-420503-f2b595fef86d/verify.log`。
本次 Android 原生重新编译通过，`git diff --check` 通过；文档分类器输出
`classification=none, reviewers=[]`，不重复运行会改变 tiles 生成状态的无关构建。
截图、XML 和日志为本 worktree 的本地验证产物（Git 忽略），本提交保存结果与索引。
下一步按需补强制 Activity 重建和其他设备；复测前先按本节准备完整 tiles 产物。

## 独立审核修正（无设备，2026-09-05）

Needs Fix 1：两个 CONFIRM 生产路径的 Always 槽位均改为空标签、保留 `A` 键，
Java 在 screen 5 / slot 2 回退到 `keyboard_always`，values 为 Always，
values-zh 与 values-zh-rCN 为“总是”。未修改 TextDB 翻译资产或桌面行为。

Needs Fix 2：上文零失败结论已限定为最后一个提交的增量范围。
此前完整范围是 `6b82440c5496e04517fc6ae197943bbf84f8ae43..b1fe3122ecf5d83fa627aa4d66aba7337d8f1d51`，
其 post-coder/code-static 为 `RESULT: FAIL (exit 1)`；之后零失败的增量测试未覆盖
menu.cc/directn.cc，不能消除完整范围失败。基线文件已有 tree-sitter 解析问题，
directn.cc 又因整文件 SHA 变化使绑定豁免失效；更新豁免属于扫描器配置变更，
留给用户决定，本次不改扫描器或豁免。

建议取舍：S-1 采纳，声明仅支持 CK_LEFT/CK_RIGHT，未支持按键记录警告，便于
定位误发布；S-2 采纳，`!` 同时检查 `skip_process_command`，避免子类禁用动作后
出现无效按钮；S-3 采纳，注明 JNI 标签必须为不含 NUL 的 BMP UTF-8 子集。
S-4 不采纳：原任务明确要求两处 `Log.i("AndroidKeyboard", ...)` 供统计，保持该约定。
S-6 仅记录：manualFull 在 Activity 重建后丢失，不新增偏好持久化或生命周期状态。
本次提供的建议编号中没有 S-5，不推测其内容。

### 修正提交的构建与完整范围复跑

修正代码提交：`b2cf9b486da493259d309b9ad99d986daa8e1590`。
Android arm64 debug 使用前述隔离 Gradle 命令构建，未安装、未操作任何设备。
补齐新增日志需要的 Android log 头文件后，最终原文：

```text
BUILD SUCCESSFUL in 14s
36 actionable tasks: 8 executed, 28 up-to-date
```

构建日志：`.claude/metrics/verify/android-context-always-build.log`。
随后在干净修正提交上执行用户要求的完整范围：

```sh
bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh \
  --profile code --base 6b82440c54 --head b2cf9b486d
```

确切范围与原文：

```text
Run ID: 20260905T100650265267344+0000-1059436-b2cf9b486da4
Base: 6b82440c5496e04517fc6ae197943bbf84f8ae43
Head: b2cf9b486da493259d309b9ad99d986daa8e1590
=== Code verification (post-coder.sh) ===
RESULT: FAIL (exit 1)
=== Risk gate: incremental C++ build ===
RESULT: PASS
=== Risk gate: ZH smoke ===
Smoke test passed
RESULT: PASS
Summary: 1 blocking failure(s)
```

完整范围 **仍失败**：post-coder/code-static 中 varargs 与拼接扫描继续报告
menu.cc/directn.cc 的 tree-sitter 解析错误。未将基线解析问题或 SHA 绑定豁免失效
改写成通过，未更新豁免配置。其余阶段通过：策略同步、Source/DB（8211/8211）、
生命周期、movement、消息覆盖、桌面编译、ZH smoke；smoke 原文为
`No protocol leaks`、`No English residue in core UI`、`No crashes`。

完整日志：
`.claude/metrics/verify/20260905T100650265267344+0000-1059436-b2cf9b486da4/verify.log`；
失败明细：`.claude/metrics/verify/coder-2026-09-05T10-06-57+00-00.log`。
验证期间临时移出生成的 Android build/assets，结束后恢复，并重新生成完整 tiles
数据，避免无 tiles 验证构建污染后续 Android 构建。未修改翻译资产。

分类器路由 zh-code-reviewer；修正增量 `aea9f475fe..b2cf9b486d` 复审为
`Ready — 0 Blocker，0 Needs Fix，0 Suggestion`，这不代表完整分支 profile 通过。
本段后续文档提交只记录结果，不改变已编译、已验证的源码；没有把它冒充为
另一次完整 profile。扫描器配置是否更新仍留给用户决定。未 push、未 merge。
