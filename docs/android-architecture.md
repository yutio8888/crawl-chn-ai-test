# Android 触控界面架构与验证

本文是 Android 版触控交互、生命周期处理和测试入口的当前参考。构建、签名、CI APK
与部署见 [build-workflow.md](build-workflow.md)；SDK/NDK 准备见
`crawl-ref/docs/develop/android.txt`；正式发布门禁见
[release-workflow.md](release-workflow.md)。问题状态以 GitHub Issues 为准，本文不记录
进度或计数。以下源码路径均相对 `crawl-ref/source/`，Java 路径相对
`android-project/app/src/main/java/`。

## 设计约束

- 复用现有机制：不新增持久控件配置系统、PocketZot 式分页或通用宏层；扩展现有
  输入描述符、命令抽屉和 `test_android_quickbar.py`。
- Java 不复制游戏规则，也不从 UI 线程改动游戏状态；抽屉命令经
  `encode_command_as_key()` 回到原生命令分派，不可用动作由命令本身反馈。
- 新增原生代码放在 `#ifdef __ANDROID__` 内，桌面端行为不变。
- 空间不足时减少直接槽位并加入“更多”，不新增行、不缩小字体。
- 存档、放弃等破坏性操作只经原生 `GameMenu`，保留原有确认。
- 横屏适配见 #113；当前所有 Activity 锁定竖屏，布局代码中的横屏兼容分支在正常使用中
  不可达。恢复该工作前需重新确认范围。

## 输入上下文与描述符

`ui.h` 定义跨 JNI 共享的枚举，数值与 `DCSSKeyboard.java` 一致，只能追加：

- `ui::InputContext`：`GAME`、`NAVIGATION`、`TEXT`、`NUMBER`。`input_context()`
  依次检查顶层 `TextInputScope`、获得焦点且接受文本/数字的控件、是否存在顶层布局，
  最后以 `MOUSE_MODE_COMMAND` 判定 `GAME`。
- `ui::InputScreen`（仅 Android）：标识当前页面类型，供 Java 按
  (screen, slot, key) 解析标签。
- `InputDescriptor` 包含上下文、页面和六个 `InputAction {label, key}`。`key == 0`
  表示空槽；标签为空时由 Java 资源解析。页面描述符中槽 0 为确认、槽 1 为取消；
  `GAME` 描述符六槽都是命令。

`InputActionScope` 与 `TextInputScope` 是 RAII 作用域：只有属于当前 `top_layout()`
的最内层作用域发布动作，TEXT/NUMBER 上下文不发布，因此未登记的嵌套弹窗不会继承
底层页面的动作。动作超过直接槽位时 `spill_input_actions()` 把最后一槽改为“更多”；
`UIRoot` 拦截 `INPUT_MORE_KEY` 并显示原生 `show_more_actions_popup()`，所选键经
`macro_buf_add` 进入输入队列。“更多”弹窗保留调用页的六槽，但不继承其溢出列表，
避免递归打开。

没有作用域时，`GAME` 行固定为休息、饮用、阅读、射击、施法、能力；每个槽发送该命令
当前生效的第一个可打印键位，因此跟随用户键位映射，未绑定的命令留空。

### JNI 通道

- `SDLWrapper::wait_event()` 每次等待时调用 `jni_input_context()`；该函数按完整描述符
  去重后调用 `SDLActivity.jniInputContext`。Activity 重建时 `nativeResetInputContext()`
  置位并推送 expose 事件，使原生侧重新发布。
- Java 在 UI 线程更新键盘。可打印字符与 Enter/Esc/Tab 走 `InputConnection`；负值键
  只允许 `CK_LEFT`、`CK_RIGHT` 与 `CK_F10`（“更多”），经 `nativeKeyboardKey` 进入 SDL
  事件队列。新增控制键应优先走原生弹窗，而不是扩大该白名单。
- 其他通道：`nativeCommitUtf8`（完整 UTF-8 输入法提交）、`nativeTouchScroll`、
  `nativeRequestRedraw`、显示密度与阅读字号查询。

## 屏幕键盘

启动器键盘模式为：0 关闭、1 经典、2 透明、3 系统输入法、4 紧凑（手机默认）。模式
0 与 3 不显示情境行。

紧凑键盘（`android-project/app/src/main/res/layout/keyboard_mobile.xml`）为八方向盘加游戏动作区，下方是六个情境槽：

- 中心键在 `GAME` 中发送 `.`（`CMD_WAIT`，单回合等待），其他上下文发送数字盘 5；
  休息（`CMD_REST`）位于情境槽 0。等待与休息不可互相替代。
- 探索键在非 `GAME` 上下文变为确认；自动战斗、背包、拾取、菜单键在非 `GAME` 中隐藏
  但保留网格位置。自动战斗支持长按连发，离开 `GAME` 即停止。
- 菜单键发送 F1；在紧凑布局的 `GAME` 中由 `tilesdl.cc` 拦截并打开命令抽屉。
- 所有自定义键盘的触控目标不小于 48dp；按实测文字宽度适配行高，情境标签过长时拆为
  两行三列。键盘总高度取紧凑与完整布局的较大值，切换布局或上下文不改变 SDL 画面
  尺寸（#119）。
- TEXT/NUMBER 上下文自动显示完整键盘，槽 0–2 变为确认、取消和临时系统输入法；
  临时系统输入法不改变已保存的键盘模式，离开文本上下文即结束。NUMBER 使用数字输入类型。
- 模式 1/2 在 `GAME` 中显示完整键盘，在菜单等 NAVIGATION 上下文切换为方向盘加情境行。
  手动切换到完整键盘在上下文变化间保持，但不跨 Activity 重建持久化。

## 顶栏、抽屉与快捷栏

- `AndroidPortraitLayoutPolicy`（`layout-policy.cc`）使用顶部 HUD、浮层消息区和底部
  弹窗，替代旧的竖屏 `TabbedRegion`（#9）。
- 点击 HUD 状态灯打开状态详情抽屉（所选状态优先）；状态行末的“全部状态”按钮打开完整
  列表；点击 HUD 其他位置打开命令抽屉。抽屉用模态遮罩，Esc/返回或点外部关闭。
- 命令抽屉（`topbar-drawer.cc` 的 `show_topbar_command_menu`）是单一滚动列表，按
  战斗与物品、探索与地图、角色与信息、系统四组排列，另有“全部法术”“全部能力”分区。
  不可用条目灰显并在点击时说明原因；长按显示详情。法术和能力在抽屉关闭后才执行。
- 底部快捷栏为一行 48dp 图标，仅在完整视野仍能放下时显示；在法术与能力之间平衡分配，
  溢出时最后一格打开抽屉中的完整列表。消息区有 48dp 的消息历史按钮。

## 原生页面动作

菜单、物品/法术/地形/神祇描述、瞄准、地图、确认提示、`--more--`、喊叫、图层、
使用物品、商店、旅行、箭袋和技能页面都登记了页面动作；当前登记点可用
`git grep -n -E 'InputActionScope|keyboard_actions' -- crawl-ref/source` 查找。菜单子类通过
`keyboard_screen()`、`keyboard_actions()`、`keyboard_more()` 提供动作，分类菜单在情境槽中
提供上一类/下一类；没有专属按键的菜单保持空行。瞄准页的“更多”包含终点确认、强制动作等
高级操作；地图页的“更多”包含排除区域和路径点，其编号提示在 Android 上用
`TextInputScope` 展开输入键盘。

## 字符串归属

| 文本 | 位置 |
|---|---|
| 启动器、Java 外壳、键盘与情境槽标签 | `android-project/app/src/main/res/values*/strings.xml` |
| 命令抽屉标签与摘要 | `dat/descript/commands.txt` 与 `dat/descript/zh/commands.txt` 中的 `android command menu` 键 |
| 溢出项、全部法术/状态、消息历史等原生标签 | `T_()` 与 `dat/i18n/zh/source.txt`，或命令描述数据库 |

`values-zh` 必须覆盖 `values` 的全部键，由 `test_android_quickbar.py` 检查。修改 ZH
翻译资产仍遵循 `.agents/policies/asset-ownership.md` 的单一写入者规则。

## 生命周期与稳健性

- **暂停存档**：`SDLActivity.handleNativeState()` 在 RESUMED→PAUSED 转换时调用
  `nativeSaveGame()`，它只登记请求并最多等待 2 秒，不在 UI 线程触碰游戏状态。实际
  存档由游戏线程在 `wait_event()` 或 `world_reacts()` 末尾的安全点执行；
  `_pause_save_is_safe()` 不满足（生成关卡、正在存档、进入关卡等）时跳过。宁可跳过，
  也不写出损坏存档。已知限制：`wait_event()` 可能在回合中途（如 `more()`）到达，
  保存的是该时刻的状态；存档写入失败和连续 `onPause` 重叠的处理只经代码分析，未经设备测试。
- **配置变化**：主 Activity 在进程内处理方向、屏幕尺寸、键盘、`fontScale` 和
  `uiMode` 变化，只重新适配键盘并请求重绘（#122）。显示密度、语言、布局方向以及
  `smallestScreenSize`/`screenLayout`（多窗口、折叠屏尺寸变化）未声明，游戏中发生这些
  变化仍会重建 Activity 并结束游戏进程。
- **画面**：全屏保留刘海安全区（#88）；旋转后黑屏的根因（`surfaceChanged` 中的
  休眠）已移除（#91）。键盘尺寸由启动器限制在 48dp 与屏幕短边的合理比例之间，
  旧的越界值会被迁移（#89）。
- **地图缓存**：`.des` 缓存用 `file_modtime()` 打时间戳，Android 资产路径返回 APK 的
  `lastUpdateTime`，避免每次启动重建（#123）。
- **正则**：Android 使用内置 PCRE（`-DREGEX_PCRE`、共享 `libpcre.so`），不使用会崩溃的
  bionic POSIX regex；APK 由 `check_android_pcre_apk.sh` 校验。
- **启动标记**：`AndroidStartup phase=` 日志（含 `dungeon_ready`）供冒烟脚本判断启动
  进度。

## 测试与验收

### 自动检查

| 入口 | 覆盖 | 运行位置 |
|---|---|---|
| `.claude/scripts/tests/test_android_*.py` | 抽屉顺序与 TextDB 键、GAME 行、等待/休息分离、“更多”拦截与溢出、快捷栏、列表与技能页、消息/状态按钮、输入法提交、阅读字号、`values-zh` 完整性等静态与小型编译夹具检查 | `.claude/scripts/tests/run_all.sh`（CI 工具测试 job） |
| `.claude/scripts/tests/test_android_pcre_apk.sh`、`.claude/scripts/tests/test_android_topbar.sh` | PCRE 检查器与设备冒烟脚本自身的回归测试（使用伪造的 `llvm-readelf`/adb） | `.claude/scripts/tests/run_all.sh` |
| `.claude/scripts/check_android_pcre_apk.sh` | APK 的 ABI 集合、每个 ABI 的 `libmain.so`/`libpcre.so` 与 PCRE 依赖，禁止 POSIX regex 符号 | CI Android job（debug APK；release APK 仅在发布标签上） |
| Gradle `:app:testDebugUnitTest` | `app/src/test` 中的 JVM 单元测试（键盘尺寸、存储、文本编辑器、自动战斗连发） | CI Android job |

`verify_zh.sh` 的 profile 不运行 Android 测试；Android 改动应运行相关的
`test_android_*.py`，并按改动类型运行匹配的 profile。`app/src/androidTest` 中的仪器测试
需要模拟器或真机，目前不在 CI 中运行，可用 Gradle 的 `connectedDebugAndroidTest` 执行。

### 设备冒烟

`.claude/scripts/test-android-topbar.sh` 安装 APK，经启动器进入游戏、载入首个存档并截取
HUD，同时扫描崩溃、ANR 和退出信息；选项见 `--help`。它使用固定包名
`org.develz.crawl`，`--fresh-install` 会删除该包的数据；`--build` 直接在
`.worktrees/android-tiles` 中构建，调用前应先按 [build-workflow.md](build-workflow.md)
同步该 worktree。

### 手动模拟器或真机验收

1. 在运行 Gradle 之前的同一 worktree 中执行 `make ANDROID=1 TILES=y android -j4`。若其间
   做过控制台或 `verify_zh.sh` 构建，要重新执行；否则 rltiles 数据或 `build.h` 版本可能
   是非 Tiles 构建的结果，表现为地牢和物品贴图空白，或启动时找不到数据库缓存目录后崩溃。
2. 需要与已安装的其他签名包共存时，只修改生成且被忽略的 `app/build.gradle` 中的
   `applicationId`，不要修改 `versionName`（原生缓存路径依赖它与 `build.h` 一致）。
   每次重新执行第 1 步都会从 `build.gradle.in` 重新生成该文件，需要重新修改；冒烟脚本的
   固定包名不适用于这种安装。
3. 无窗口模拟器使用 `emulator -avd <avd> -no-window -gpu swangle_indirect`；其他渲染器
   可能在载入地图贴图时无提示退出。
4. 用 `adb shell cmd locale set-app-locales <package> --user 0 --locales zh-CN` 切换应用
   语言；用 `uiautomator dump` 找到真实按钮后以 `adb shell input tap` 点击，长按用
   `input swipe X Y X Y <ms>`。日志用
   `adb logcat -s AndroidStartup:I AndroidKeyboard:V KEY:V` 同时查看启动阶段与键盘事件。
5. 窄屏检查可在启动前设置 `adb shell wm density`（密度变化会重建 Activity）；字体缩放
   现在可以在游戏中调整。
6. 验收记录写明候选提交、包名、设备或模拟器的 Android 版本与 ABI。x86_64 模拟器通过
   不代表 ARM64 真机通过；ADB 注入也不能替代真实手指的误触和人体工学检查。

## 已知遗留

- 完整键盘上带方向箭头的 `h/j/k/l` 发送字母键码，而菜单左右翻页只绑定
  `CK_LEFT`/`CK_RIGHT` 与 Tab/Shift-Tab；纯触控用户应使用紧凑方向盘或情境槽中的上一类/
  下一类。
- 横屏紧凑键盘的空间分配见 #113。
