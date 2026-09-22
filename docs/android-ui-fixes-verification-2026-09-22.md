# Android 首批优化验证记录

日期：2026-09-22。分支：`codex/android-ui-fixes`；工作树：`.worktrees/android-ui-fixes`。

基线：`b27476622deb59cf5e8b39102845232464dcc846`。本记录保存提交前工作树改动的验证结果，实施范围为[优化报告](android-ui-optimization-report-2026-09-22.md)的 A01、A03、A04。

## 实现

- **A01 瞄准误确认**：使用地图区域返回的鼠标处理结果，仅有效地图左键点击进入原有目标确认路径。HUD、消息区点击和 Android 长按不再确认此前的目标。
- **A03 配置编辑**：以 UTF-8 循环读取；同目录临时文件完整写入、同步和关闭后，再原子替换原文件。返回/取消时比较实际内容，有未保存修改则提示继续编辑或放弃；保存失败保留草稿。
- **A04 空箭袋**：无可用动作时说明原因；有候选动作时打开既有选择菜单，取消不消耗回合，选择后进入正常瞄准。
- 为使现有严格扫描器能够解析本次修改的 `quiver.cc`，整理两处被条件编译拆开的 `else`。WIZARD 描述与旧版存档动作识别逻辑保持等价；未调整扫描器或豁免规则。

中文资源在 `values-zh` 和 `values-zh-rCN` 同步增加四条关闭确认文案。C++ 提示复用已有翻译键。术语 SHA-256：`366e807eaae5403b6c3925df5970cd237b447ead76fdb717b71273473b5db67e`。

## 构建与自动验证

Android 使用独立测试包名 `org.develz.crawl.uifixes`、x86_64 debug APK；包名和 `-j4` 仅设置在生成的本地 Gradle 文件中。模拟器为独立 Pixel 7 AVD，Android 15 / API 35，1080×2400、420dpi、字号 100%、应用语言 zh-CN，GPU 后端 swangle。

最终 APK 保留在 `crawl-ref/source/android-project/app/build/intermediates/apk/debug/app-debug.apk`。

最终 APK SHA-256：`d3e303c6b507f20809add16570f31dcc5fedec507048dae2471554886eef1ffb`。

| 检查 | 结果 |
|---|---|
| 隔离 Gradle `:app:testDebugUnitTest :app:assembleDebug :app:assembleDebugAndroidTest`，离线、单 ABI、最多 4 个 worker | 构建成功；16 项 JVM 测试通过 |
| `DCSSTextEditorUiTest` | 7 项设备测试通过 |
| Catch `[quiver]` | 13 个断言通过；包含显式清空及失效弹药两个分支 |
| 隔离 `verify_zh.sh --profile code` | 退出 0；6 阶段全部通过，0 个阻塞失败 |
| `git diff --check` | 通过 |

编辑器测试覆盖空文件、ASCII、中文、emoji、CRLF、无末尾换行和长文本的字节往返；短读及 `available()==0`；未修改直接退出、撤销全部修改、继续编辑、明确放弃、Activity 重建；写入失败保留原文件/草稿、重试成功，以及替换失败清理临时文件。

首次设备测试暴露测试同步问题：主线程空闲不等于退出动画结束，连续对话框也可能选到错误窗口。测试改为观察真实 `ON_DESTROY` 并明确匹配对话框窗口，保留全部退出和内容断言；复测 7 项通过，生产 Java 未因此改变。

统一检查采用 Python 3.13.14；按现有 CI 命令编译工作树内 Lua 5.4.8 的 `luac`。C++ 构建入口设置为一次构建 `crawl` 与 `catch2-tests-executable`，最多 `-j4`，随后执行原有中文启动烟雾检查。首轮因缺少 `luac` 和上述基线解析障碍未通过静态检查，且在烟雾检查阶段被 SIGTERM 中断；该轮不计为通过。

本地完整日志位于 `.artifacts/android-ui-fixes/`，包括 `gradle-final.log`、`gradle-delivery.log`、`editor-instrumentation-final.log`、`catch-quiver-final.log`、`parser-cleanup.log` 和 `verify-code-final.log`；统一检查的分阶段证据位于 `.claude/metrics/verify/20260922T060055274680105+0000-3681289-b27476622deb/`。静态检查没有新增警告；日志仍包含既有的 movement manifest `leap` 提示和编译警告，并非所有历史警告均已清零。

## 模拟器验收

使用本次新建的普通角色 UiFixes，归来者猎手，D:1，未开启巫师模式。

| 操作 | 观察 |
|---|---|
| 射击瞄准并把光标移到下方，点击顶部 HUD | 保持 TARGET，行动时间为 0.0；[前](evidence/android-ui-fixes-2026-09-22/01-target-before-hud.png) / [后](evidence/android-ui-fixes-2026-09-22/02-target-after-hud.png) |
| 对地图长按 900ms、点击消息区 | 均保持 TARGET 和 0.0；[长按后](evidence/android-ui-fixes-2026-09-22/03-target-after-longpress.png) / [消息区后](evidence/android-ui-fixes-2026-09-22/04-target-after-message.png) |
| 点击情境栏“确定”，再次瞄准并点按有效地图格 | 正常射击；时间依次变为 1.3、2.5；[确定](evidence/android-ui-fixes-2026-09-22/05-explicit-confirm.png) / [地图点按](evidence/android-ui-fixes-2026-09-22/06-map-click-confirm.png) |
| 清空箭袋后点击“射击”，再取消 | 打开含短弓候选的选择菜单；取消后仍为 2.5，显示中文反馈；[菜单](evidence/android-ui-fixes-2026-09-22/08-empty-fire-menu.png) / [取消](evidence/android-ui-fixes-2026-09-22/09-empty-fire-cancel.png) |
| 再次射击并选择短弓 | 进入 TARGET；[截图](evidence/android-ui-fixes-2026-09-22/10-empty-fire-selected.png) |
| 对自身确认 | 原有自射保护拒绝操作，时间仍为 2.5；[截图](evidence/android-ui-fixes-2026-09-22/11-self-target-refused.png) |
| 重新瞄准下方并确认 | 正常射击至 3.8；[截图](evidence/android-ui-fixes-2026-09-22/13-fire-after-reselect.png) |
| 启动页编辑外部存储 `init.txt` 并原样保存 | `# 中文\nlanguage = zh\n` 保存前后均 23 字节，逐字节相同，无 NUL；[打开状态](evidence/android-ui-fixes-2026-09-22/14-rc-clean-open.png) |
| 编辑后按系统返回 | 出现完整中文关闭确认；[截图](evidence/android-ui-fixes-2026-09-22/15-rc-discard-dialog.png) |

截图 01–15 来自条件编译等价整理前的实现包。最终包重新生成图块并打包后，已确认[读档和地图显示正常](evidence/android-ui-fixes-2026-09-22/16-final-loaded.png)；空箭袋[打开菜单](evidence/android-ui-fixes-2026-09-22/17-final-empty-menu.png)并[取消](evidence/android-ui-fixes-2026-09-22/18-final-empty-cancel.png)仍为 3.8；重新选择后，HUD 点击与地图长按[保持 TARGET 和 3.8](evidence/android-ui-fixes-2026-09-22/19-final-target-filter.png)，显式确认[正常射击至 5.1](evidence/android-ui-fixes-2026-09-22/20-final-confirm.png)。Java 生产文件和瞄准/空箭袋实现主体未再改变。

## 审查与边界

独立实现审查覆盖鼠标事件消费、原有目标校验链、空动作分支、保存事务、草稿恢复、资源标识和测试同步；未发现新增 Blocker 或 Needs Fix；6 阶段统一检查、16 项 JVM、7 项设备测试及 Catch 回归均已核对。主线程另复核四条中文与英文语义一致、措辞自然。

同一工作树先后构建 console 与 Android 时，console 的 tilegen 会把共享 `rltiles/tiledef-*.cc` 中图块尺寸生成为零。最终打包前已重新运行 `make ANDROID=20260922 TILES=y android -j4` 恢复图块数据，再执行 Gradle；此后没有再次运行 host make。中间生成文件污染的 APK 不作为交付包。

本轮设备验证使用短弓覆盖共享瞄准入口；射程、视线、友军保护的保留另由原有 `select(false, false)` / `move_is_ok` 调用链审查支持，没有把它们写成全部设备实测。未执行全部投掷/法术组合、真机手势或性能矩阵。A02 大字号、A05–A10 仍属于后续批次。本记录不包含合并验收。
