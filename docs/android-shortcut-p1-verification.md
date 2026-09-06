# Android 快捷键覆盖 P1 验证记录

Issue：#129（挂在 #105 之下）。方案：[执行方案](android-shortcut-execution-plan.md) 第 2 节。
分支 `claude/android-shortcut-p1`，基线 `8e71c1c1e7`。仅在本 worktree 提交，未 push、merge。
术语表 SHA-256：`366e807eaae5403b6c3925df5970cd237b447ead76fdb717b71273473b5db67e`；
`context_resolve.sh --task-type code --terminology yes` 未要求新裁决，短标签沿用
`dat/descript/zh/commands.txt` 中 `CMD_REST`“休息”、`CMD_WAIT`“等待”、`CMD_CAST_SPELL`
“施法”、`CMD_USE_ABILITY`“能力”的既有用词，饮用/阅读/射击取自覆盖报告。

## 实施内容

| 位置 | 改动 |
|---|---|
| `ui.h` | `InputScreen` 末尾追加 `GAME`（值 18） |
| `ui.cc` `input_descriptor()` | 无顶层 scope 且上下文为 GAME 时发布固定六动作 `5 q r f z a`；已登记 scope 仍优先 |
| `DCSSKeyboard.java` | GAME 下中心键 tag 切为 `KEYCODE_PERIOD` 并显示 `keyboard_wait`，其余上下文恢复 `KEYCODE_NUMPAD_5` 与 `5`；`contextLabelResource` 增加 `case 18` |
| `keyboard_mobile.xml` | 中心键文字与无障碍名改为 `keyboard_wait`，初始 tag 保持 149 |
| `values*/strings.xml` | `keyboard_rest` 改为“休息 / Rest”；新增 `keyboard_wait` 与饮用、阅读、射击、施法、能力 |
| `test_android_quickbar.py` | 更新两条既有断言；新增 `GameActionRowTests` 五条静态检查 |

`keyboard_extra_numeric.xml` 的副数字盘中心继续发 149，改字串后其标签自动变为“休息”，未改布局。

## 静态检查

- `bash .claude/scripts/run_isolated.sh python3 .claude/scripts/tests/test_android_quickbar.py`：35 项通过。
- code profile（绑定候选范围，干净 worktree）：

```sh
bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh \
  --profile code --base 8e71c1c1e7 --head df49e5924d
```

```text
Run ID: 20260906T045728566961265+0000-294638-df49e5924d26
Failures: 0
```

## 构建

本 worktree 初始化 contrib 子模块并复制 Lua 5.4.8 `luac` 后，先
`make ANDROID=1 TILES=y android -j4`（隔离包装内）准备原生工程与 rltiles，再执行
离线 Gradle：

```sh
./gradlew --offline --no-daemon --max-workers=4 \
  -Pandroid.injected.build.abi=arm64-v8a :app:assembleDebug
```

```text
BUILD SUCCESSFUL in 59s
36 actionable tasks: 36 executed
```

APK：`app/build/intermediates/apk/debug/app-debug.apk`，arm64-v8a、test-only debug，
SHA-256 `f6fea34bd65393ec3c4fa91067e95546460a4843185c59e07a20d4c28f17d93e`。
`applicationId` 临时改为 `org.develz.crawl.shortcut129`（仅生成的 `app/build.gradle`，
不入库），`local.properties` 指向 `/opt/android-sdk`。代码候选 `c31cdcf389`，游戏内
版本串 `0.34.1-zh5-1-010-181-gc31cdcf389`。

## 真机验收（Pixel 8a，Android 15，arm64，1080×2400，411dp）

独立安装 `org.develz.crawl.shortcut129`，`cmd locale set-app-locales … zh-CN`，
虚拟键盘为“移动端紧凑键盘”、键盘大小 48。所有按钮均按 `uiautomator dump` 的
真实坐标 `input tap` 点击；只有设置箭袋前置条件时用了硬件 `Q`。截图、
`AndroidKeyboard` 日志与辅助脚本存于
`.claude/metrics/verify/android-shortcut-p1-2026-09-06/`（git 忽略）。
新建角色 Tester129（精灵 战士）。

| 场景 | 结果 | 证据 |
|---|---|---|
| 进入地牢 | 第四行显示 休息/饮用/阅读/射击/施法/能力，中心键“等待”，日志 `context=0 screen=18` | g07 |
| 空地点等待一次 | 时间 0.0 → 1.0，坐标不变，无休息消息 | t01 |
| 连点三次等待 | 1.0 → 4.0，恰好三回合 | t02 |
| 点休息（满生命法力） | 4.0 → 104.0，消息“你开始等待/等待结束”，即原 `CMD_REST` 流程 | t03 |
| 脚下有匕首时等待 | 只耗一回合，未拾取（“你在这里看到了+0 匕首”） | t09 |
| 视野内有短尾矮袋鼠时等待 | 124.0 → 125.0，一回合 | t32 |
| 视野内有敌人时休息 | 被原生安全检查拒绝，回合不变 | t33 |
| 饮用 | 打开物品选择菜单，日志 `screen=8`，第四行变为 确定/返回/描述，中心键 `5`；返回后恢复 | t05、t06 |
| 阅读（无卷轴） | “你没有携带任何卷轴”，回合不变 | t10 |
| 射击（空箭袋） | 与硬件 `f` 一致：游戏本身无提示、回合不变 | t12、t13 |
| 射击（拾取 7 石头后） | 进入瞄准，第四行 确定/取消/上个目标/下个目标/自身，日志 `screen=4`；取消后恢复 | t18 |
| 施法（无法术） | “你不认识任何法术”，回合不变 | t19、t20 |
| 能力（无能力） | “抱歉，你的能力还不足以拥有特殊能力”，回合不变 | t20 |
| 背包 → 物品描述 | 第四行依次变为 确定/返回/上一类/下一类 与 返回/持有/丢弃/调整/技能目标 | t14、t15 |
| 抽屉 → 大地图 | 第四行 返回/上下楼梯/传送门/陷阱，日志 `screen=7`；返回后恢复 | t22、t23 |
| Home 后拉回前台 | 进程未重启，第四行仍为 GAME 行，等待 121.0 → 122.0 | t29、t30 |
| 旋转 | 应用锁定竖屏，`user_rotation=1` 未触发重建；不适用 | t24 |
| 字体 130% | 强制停止后设置 `font_scale 1.3` 再读档：六槽两字标签无换行，键盘高度 504px 不变 | f02 |
| 320dp 窄屏 | 本轮未测（设备 411dp）；模拟器窄屏留待 P2 前补测 | — |

### 观察到但不属于本阶段的事项

- 走上药水格时物品被移动的自动拾取捡走，这是原生自动拾取，不是等待按钮行为。
- 匕首描述页只有五个动作槽，没有箭袋项；匕首在 0.34 也不可投掷（`Q` 提示
  “你没有东西可装入箭袋”）。溢出问题按报告 4.6 留待 P3。
- 首屏消息“发现了五 item”存在英文残留，属翻译问题，与本改动无关，另行登记。

## 结论

P1 验收矩阵中除 320dp 窄屏外全部通过；等待与休息已是两个语义不同的按钮，
游戏态第四行由最内层页面接管并在返回后恢复。未 push、未 merge。
