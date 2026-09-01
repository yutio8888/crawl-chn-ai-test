# Android 开发分支修复与验收方案

- 制定日期：2026-09-01
- 当前分支：`codex/android-experience-test`
- 当前提交：`6f0d639e7d9a22f4ebafd63ad15c3d1509e076ab`
- 远端跟踪提交：`origin/codex/android-experience-test`，`6c7704362f`
- 适用范围：Android 启动崩溃修复、移动端交互验收、分支集成和候选交付

## 结论

当前分支已经解除 API 35 x86_64 地图加载阶段的原生崩溃，可以在 KVM
模拟器中连续两次冷启动到中文主菜单；它仍不是可合并或可发布候选。剩余阻断主要是测试
脚本可能假阳性、修复后完整交互未覆盖、缺少 ARM64 真机证据、候选构建身份不可信，以及
分支与最新中文基线已经分叉。

本方案按“先建立可信测试信号，再完成产品验收，最后形成不可变候选”的顺序处理。
每个阻断保持独立提交边界，交付独立无上下文代理审核；审核未通过时只修正当前阻断，
不得顺带扩大产品范围。

## 当前证据基线

| 项目 | 当前结果 | 证据或说明 |
|---|---|---|
| Git 工作树 | 产品树干净 | 创建本方案前无改动；本方案文件是当前唯一未跟踪变更 |
| action menu / status drawer | 已包含 | 两个远端功能分支均为当前提交祖先 |
| PCRE 修复 | 已提交 | Android 构建定义 `REGEX_PCRE` 并链接 bundled `libpcre` |
| 标准 code profile | 通过 | `.claude/metrics/verify/20260901T100429331008445+0000-117989-6f0d639e7d9a/` |
| Debug APK | 通过 | 四 ABI 构建、v1/v2 签名和包信息检查通过 |
| x86_64 KVM 启动 | 通过 | 两次地图加载约 6.5 秒，均进入中文主菜单 |
| 崩溃检查 | 通过 | 未发现 SIGSEGV、Fatal、应用 ANR 或 `regexec` |
| Gradle 单元测试 | 无覆盖 | `testDebugUnitTest` 为 `NO-SOURCE` |
| 完整存档和触控流程 | 未完成 | 修复后只验证到主菜单 |
| ARM64 真实运行 | 未完成 | 当前只有构建与 ELF 证据 |
| 基线同步 | 未完成 | 当前基线独有 9 个提交，Android 分支独有 24 个提交 |
| APK 构建身份 | 不合格 | 直接运行 Gradle 复用了旧生成文件，`versionName` 仍显示 `g6c7704362f` |

修复前的 `.artifacts/android-test/TEST-RESULTS.md` 仍然是有效的根因历史记录，但不能代表
当前提交的最终结果。正式候选必须产生一份绑定精确提交的新报告，不能覆盖或改写旧现场。

## 成功标准

只有同时满足以下条件，Android 分支才能进入不可变候选审核：

1. 标准 `code` profile 在正常持久文件系统中通过，阻断失败为 0。
2. 精确候选提交能够构建可安装的 Android APK；签名、包名、SDK、四 ABI 和 PCRE ELF
   依赖检查全部通过。
3. 冒烟测试能够可靠区分 Launcher 与 SDL 游戏进程，检测 native crash、Java crash、ANR、
   异常退出和阶段超时，失败时必须返回非零。
4. API 35 x86_64 KVM 模拟器完成启动、创建或加载存档、HUD、状态抽屉、功能菜单、方向键、
   旋转、编辑器、返回键、前后台和进程重启恢复测试。
5. 至少一台 ARM64 Android 15 真机完成启动、关键触控路径、存档恢复和 30 分钟稳定性测试。
6. APK 显示版本、测试报告、Git 提交和 SHA-256 清单指向同一不可变候选。
7. 每个修复提交获得独立无上下文审核通过；最终候选通过仓库 final gate 和 merge gate。

## 非目标

- 本轮不创建新的 Android 导航体系，不重写现有 action menu 或 status drawer。
- 不把探索性的人因建议直接扩张为产品功能提交。
- 不吞掉 `fsync`、不使用 tmpfs 或临时 mount 绕过正式验证的耐久性契约。
- 不把 x86_64 模拟器成功外推为 ARM64 真机成功。
- 不在未获得分支集成授权时重写或移动现有远端分支历史。
- 不把 debug APK 作为正式签名发布资产。
- 不把陈旧生成文件造成的版本错配预先归类为产品代码缺陷；只有完整 helper 流程仍产生
  错误身份时才授权修复代码。

## 阶段一：修复 Android 冒烟测试的可信度

### 目标

扩展现有 `.claude/scripts/test-android-topbar.sh`，复用已有 `AndroidStartup` 日志协议，
消除“游戏崩溃后 Launcher 仍存活也报告成功”的假阳性。

### 实施范围

- 测试开始前清理 logcat，并记录本次运行的明确时间边界。
- 用阶段日志等待替代固定 `sleep`：至少等待 `maps_complete`、
  `native_initialize_complete` 和 `startup_menu_ready`。
- 在现有 Android 启动诊断通道增加最小的 `dungeon_ready` 状态信号；该信号只描述已经
  完成存档加载并显示地牢，不新增测试框架。
- 同时检查前台 Activity、包 PID 和游戏阶段，不能只接受任意同包进程。
- 自动扫描本次运行后的 SIGSEGV、Fatal signal、`FATAL EXCEPTION`、应用 ANR、
  `ApplicationExitInfo` 异常原因和阶段超时。
- 失败时保存完整 logcat、阶段日志、Activity/窗口状态、退出信息和最后截图，并返回非零。
- 保留 `--apk` 入口，使 x86_64 debug APK 可以直接测试；若调整 `--build`，必须保持
  `buildTest` 真机用途兼容，不用隐式 ABI 猜测替代显式参数。
- 为 shell 参数校验、阶段超时、崩溃扫描和 Launcher 假阳性增加轻量脚本测试。
  测试放入现有 `.claude/scripts/tests/`，开发阶段通过隔离 wrapper 运行针对性测试，最终由
  final gate 的既有 `run_all.sh` 入口统一执行。
- 每次运行将报告写入显式 `--output-dir`；正式证据统一放在
  `.artifacts/android-test/<candidate>/smoke/`，不依赖 `/tmp` 中的临时结果。

### 验收

- 用修复前崩溃日志或可控假 ADB fixture 运行时，脚本必须失败。
- 只有 Launcher 存活、SDL Activity 已退出时，脚本必须失败。
- 在当前 PCRE APK 上完成存档加载并出现 `dungeon_ready` 时，脚本必须成功。
- 成功路径执行前必须通过正式 UI 创建并记录一个可加载存档；干净模拟器没有存档时应明确
  报告前置条件缺失，不能误报产品失败或跳过 `dungeon_ready` 断言。
- 所有失败分支均产生足够复现的证据，不依赖人工查看最终截图才知道结果。

### 提交与审核边界

该阶段只包含测试信号和冒烟脚本修复，不夹带 Android UI 改动。形成精确候选后交给一个
未继承实现上下文的独立代理审核；重点检查假阳性、超时、日志时间边界、ADB 多设备处理和
退出码。审核通过后才能推送或进入下一阶段。

## 阶段二：固定 PCRE 崩溃回归

### 目标

防止后续 Android 构建重新落回 bionic POSIX regex，或在中文、忽略大小写消息上重新崩溃。

### 实施范围

- 为 `text_pattern(..., true)` 增加 ASCII、中文和中英混合文本用例。
- 使用已知触发路径的消息和代表性 `message_colour` 正则，验证不匹配、匹配和非法表达式
  均不会破坏对象生命周期。
- 增加 Android 构建契约检查：`REGEX_PCRE`、PCRE include 和 `libpcre` 依赖必须同时存在。
- 构建后对四个 `libmain.so` 执行 ELF 检查：必须依赖 `libpcre.so`，必须没有未解析的
  `regcomp`、`regexec` 或 `regfree`。
- 不维护一份与生产数据脱节的新正则全集；优先从现有默认消息规则派生最小回归语料。

### 验收

- 新回归在 PCRE 路径通过；故意移除 `REGEX_PCRE` 或 `libpcre` 时构建契约测试失败。
- API 35 x86_64 冷启动至少连续 5 次完成地图加载，崩溃扫描为 0。
- 标准 code profile 通过。

### 提交与审核边界

该阶段只增加 PCRE 回归和构建契约，不修改 Android 交互。独立审核重点检查测试是否真的
绑定生产路径、是否可能在未链接 PCRE 时假通过，以及 PCRE/POSIX 边缘语义差异。

## 阶段三：整合最新中文基线

当前 Android 分支与 `origin/chn-0.34.1-base` 双向分叉。正式候选不能直接复用整合前证据。
由于基线整合超出最初“不合并最新基础分支”的测试范围，执行前需要明确授权。

获得授权后：

1. 在仓库内创建独立 `.worktrees/<name>` 集成 worktree 和 `codex/<topic>` 候选分支，
   不从 linked worktree 移动现有 Android 分支引用。
2. 保留 Android 分支历史，优先使用可审计的集成提交，不重写已共享历史。
3. 人工解决 `.claude/scripts/zh_console_ui_bot.py` 已知冲突。
4. 重点审查 `command.cc` 及双方共同修改的翻译、帮助和测试逻辑。
5. 冲突解决只恢复双方既有语义，不顺带重构或新增功能。
6. 独立审核集成差异，通过后运行标准 code profile；完整 Android 回归在阶段四执行。

若基线仍在变化，先冻结集成目标 SHA；不能用不同时间点的基线拼接验证证据。

在取得整合授权前，可以用当前分支运行针对性诊断和探索性测试，但结果只用于发现缺陷，
不得作为候选验收证据。这样既不阻塞调查，也避免整合后重复整套正式矩阵。

## 阶段四：完成模拟器交互验收

### 测试存档

通过正式 UI 创建一个确定性的非 `*WIZ*` 测试角色并保存。测试报告记录角色、存档状态、
创建步骤和候选提交；存档及截图保存在忽略跟踪的
`.artifacts/android-test/<candidate>/`，不把临时用户数据提交到产品仓库。

### 必测矩阵

| 范围 | 操作 | 通过条件 |
|---|---|---|
| 启动器 | 简体中文、开始游戏、设置 | 无明显英文缺失；设置可保存并传入 SDL Activity |
| 存档 | 创建、加载、强停后恢复 | 地牢位置、角色状态和存档完整 |
| 顶部 HUD | 竖屏、横屏、旋转往返 | HUD 与地牢均可见，无遮挡、拉伸或状态丢失 |
| 安全区 | 系统栏、刘海模拟、全屏 | 顶部字形和可点击区域不进入不可用区域 |
| 状态抽屉 | 打开、滚动、关闭 | 内容与角色状态一致，返回键逐层关闭 |
| action menu | 入口、各页、命令执行 | 可发现、命令正确、关闭后焦点返回游戏 |
| 方向键 | 地牢、背包分页、瞄准、查看 | 视觉方向与实际命令一致，不泄漏字母/数字语义 |
| 键盘 | Classic、Compact、大小设置 | 尺寸生效，旋转后不漂移或覆盖地牢 |
| 编辑器 | 中文标签、输入、保存、取消 | 操作顺序自然，文本保存后可由游戏加载 |
| 生命周期 | Back、Home、恢复、强制重启 | 无误退出、黑屏、状态丢失或异常退出 |

每个场景保存起点、操作后和恢复后的截图，并用同一次运行的 logcat 和退出信息绑定。
探索性观察可以记录为后续 issue，但只有复现稳定且违反上述通过条件的问题才阻断当前候选。

### 提交与审核边界

纯测试执行不产生产品提交。若发现缺陷，每个缺陷单独形成“复现证据—最小修复—针对性
回归—独立审核”闭环，审核通过并提交后再恢复矩阵测试；不得把多个 UI 问题积累成一个
大提交。

## 阶段五：ARM64 真机与稳定性

### 设备最低要求

- ARM64 真实设备，必须运行 Android 15 / API 35；更低 API 设备只能提供兼容性补充证据，
  不能替代该验收项。
- 至少一台约 4 GB RAM 设备或可施加等价内存压力的设备。
- 记录型号、Android build、ABI、分辨率、dpi、字体缩放和系统语言。

### 验收范围

- 冷启动 5 次、热恢复 5 次，记录阶段耗时和异常退出。
- 完成启动、创建/加载存档、移动、战斗、背包分页、状态抽屉、action menu 和旋转。
- Home/返回、锁屏、系统回收后恢复。
- 30 分钟探索及跨层，记录 PSS/RSS 趋势、崩溃、ANR 和明显输入异常。
- 真人拇指确认主要触控目标可用；ADB 注入结果不得代替这一项。

ARM64 缺陷按独立阻断处理；不得用 x86_64 模拟器成功将其关闭。

## 阶段六：候选构建与最终交付

### 精确候选构建

`build-android.sh` 固定从主 checkout 的 HEAD 同步 detached Android build worktree，不能从
另一个 linked integration worktree 直接调用并假定它会构建该 worktree 的 HEAD。冻结候选后，
先让干净的主 checkout 以 detached HEAD 指向候选 OID；这不移动分支引用，也不重写历史。
记录原分支以便构建完成后显式恢复。

候选准备和构建流程：

```bash
CANDIDATE="$(git rev-parse <candidate>^{commit})"
test -z "$(git status --porcelain=v1 --untracked-files=all)"
git switch --detach "$CANDIDATE"
test "$(git rev-parse HEAD)" = "$CANDIDATE"

bash .claude/scripts/run_isolated.sh \
  bash .claude/scripts/verify_zh.sh --profile code

cd crawl-ref/source
bash util/build-android.sh <version-code>
```

helper 会先同步 build worktree，再运行 `make ... android`，从模板重新生成 `app/build.gradle`；
不得用未经该准备步骤的直接 Gradle 调用证明候选身份。需要 x86_64 模拟器 debug APK 时，
只能在 helper 已为同一 OID 完成同步和生成之后，在该 build worktree 中运行
`clean assembleDebug testDebugUnitTest --max-workers=4`；它是设备测试产物，不代替正式候选包。

正式候选从同一 detached 主 checkout 使用 `crawl-ref/source/util/build-android.sh --release`，
并遵守 `docs/build-workflow.md` 的签名要求。构建前后必须检查：

- 主 checkout HEAD、`.worktrees/android-tiles` HEAD 和冻结的 `CANDIDATE` 完全相同
- 重新生成的 `app/build.gradle` 版本与该候选的 `git describe` 结果一致
- `apksigner verify`
- `aapt dump badging`
- APK 内四 ABI 列表和各 ABI `libmain.so` 的 ELF 依赖
- APK SHA-256
- 应用内版本、生成的 Gradle 配置、APK `versionName` 与候选身份一致

若完整 helper 流程仍产生错误身份，才把它登记为独立构建缺陷并授权代码修复；不得根据
当前由旧生成文件造成的错配预先创建产品修复提交。

### 最终证据

新建绑定候选 SHA 的测试报告，至少包含：

- 分支拓扑和基线 SHA
- 构建工具版本及设备矩阵
- 自动化与人工场景逐项结论
- 启动时序、崩溃/ANR 扫描和应用退出原因
- APK 文件名、大小、签名摘要和 SHA-256
- 已知非阻断问题及明确延期范围
- 各独立修复的审核结论

随后按仓库契约准备不可变候选。候选和目标 worktree 必须已初始化精确 submodule 且保持
干净；从干净 target checkout 执行：

```bash
git submodule update --init --recursive
bash .claude/scripts/review_prepare.sh <candidate> <target>
```

只分发 prepared bundle 的 routing 记录点名的 reviewer，并持久化每名 reviewer 的完整
结构化 findings/readiness。混合 C++、Android 和中文资产候选通常需要多个角色，实际集合
以 routing-v2 为准，任意单一通用代理不能替代机械路由。所有 reviewer 均 Ready 后运行：

```bash
printenv TERM
infocmp xterm-256color >/dev/null
TERM=xterm-256color bash .claude/scripts/review_final_gate.sh \
  <candidate> <target>
bash .claude/scripts/review_at_merge.sh <candidate> <target>
```

`review_at_merge.sh` 只在实际合并前立即运行。若 final gate 后没有紧接着合并，本处命令仅
表示顺序要求，不得把提前执行的结果留作未来的 merge-time 证明。

final gate、merge gate、ARM64 真机和版本身份任一缺失时，不得把候选描述为 Android 发布就绪。

## 推荐提交序列

| 顺序 | 单一责任 | 审核重点 |
|---:|---|---|
| 1 | 修复 Android smoke 假阳性和诊断证据 | Activity/PID 区分、超时、日志边界、退出码 |
| 2 | 固定 PCRE Android 回归与 ELF 契约 | 生产路径绑定、四 ABI、正则语义 |
| 3 | 经授权整合最新中文基线 | 冲突、双方语义保持、无范围漂移 |
| 4 | 按测试发现逐个修复交互缺陷 | 每个缺陷单独审核和提交 |
| 5 | 验证候选构建身份 | helper 重生成、Git/Gradle/APK 身份一致；仅持续失败才修代码 |
| 6 | 仅在必要时修复 ARM64 专属缺陷 | 真机复现、ABI 边界、无 x86_64 回归 |

候选提交可以先作为不可变审核对象存在；只有独立审核 Ready、对应验证通过后，才能推送、
合并或作为下一阶段基础。若审核发现问题，新增最小修正并重新审核最终候选，不以口头说明
替代复审。

## 停止条件

出现下列任一情况时暂停当前阶段并返回决策，不自行扩大修复范围：

- 基线整合需要重写已共享历史或删除另一分支提交。
- 修复需要新的持久 schema、测试服务或 Android 导航架构。
- 必须改变公共存档格式、协议身份或翻译资产所有权。
- ARM64 缺陷无法在已有 Android/PCRE 机制内最小修复。
- 正式签名密钥、设备权限或外部发布授权缺失。
