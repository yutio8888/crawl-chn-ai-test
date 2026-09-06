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
- code profile：见下文。

## 构建

（待填）

## 真机验收（Pixel 8a，Android 15，arm64）

（待填）
