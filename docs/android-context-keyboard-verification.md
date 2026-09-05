# Android 情境键盘验证记录

代码候选：`6b82440c54..b1fe3122ec`。仅在当前 worktree 提交，未 push、merge。
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

先执行要求的 `verify_zh.sh --profile code`。该次发现新增缺失标签、生成资产
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
