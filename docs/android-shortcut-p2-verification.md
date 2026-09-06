# Android 快捷键覆盖 P2 验证记录

Issue：#129 第二阶段。方案：[执行方案](android-shortcut-execution-plan.md) 第 3 节。
分支 `claude/android-shortcut-p2`，基于 P1 候选之上。仅在本 worktree 提交。
术语：沿用 P1 的 `context_resolve.sh --terminology yes` 结果与 glossary SHA-256
`366e807eaae5403b6c3925df5970cd237b447ead76fdb717b71273473b5db67e`；新增抽屉标签与
摘要在 `dat/descript/zh/commands.txt` 中，用词沿用既有条目（箭袋、激活、跨层旅行等）。

## 实施内容

| 位置 | 改动 |
|---|---|
| `topbar-drawer.cc` | `command_entry` 增加 `section`；同一滚动器内四个分组标题各带一个 `CommandGrid`；新增 14 个命令入口 |
| `shout.cc` | “What are your orders?” 提示前登记 `InputScreen::SHOUT` 描述符：`t a r s g f`，按提示行条件隐藏 |
| `ui.h` | `InputScreen` 追加 `SHOUT`（值 19） |
| `DCSSKeyboard.java` | `case 19` 按键值解析六个命令标签 |
| `values*/strings.xml` | 喊叫、攻击、撤退、停止、守卫、跟随 |
| `dat/descript/commands.txt`、`zh/commands.txt` | 四个分组标题、14 个标签与摘要 |
| `test_android_quickbar.py` | 固定顺序表改为带分组的 29 项；分组连续性、标题解析、SHOUT 行静态检查 |

新增入口图标复用现有 32px 命令/能力/物品图块（例如 `TILE_WAND_OFFSET`、
`TILEG_ABILITY_BEOGH_RECALL`），作为占位，可后续替换。放弃角色与保存不单独成按钮，
经“系统菜单”进入原生 GameMenu 并保留其确认。

## 静态检查

- `test_android_quickbar.py`：36 项通过。
- code profile：见下文。

## 构建

与 P1 相同流程（`make ANDROID=1 TILES=y android -j4` + 离线 Gradle arm64 debug）：

```text
BUILD SUCCESSFUL
36 actionable tasks: 36 executed
```

APK SHA-256 前缀 `00da1ad419b9ae71`（候选 `96ab734865`，游戏内版本串
`0.34.1-zh5-1-010-184-g96ab734865`）。

## 真机验收（Pixel 8a，包 `org.develz.crawl.shortcut129`，读取 P1 存档 Tester129）

截图与日志存于 `.claude/metrics/verify/android-shortcut-p2-2026-09-06/`（git 忽略）。

| 场景 | 结果 | 证据 |
|---|---|---|
| 打开抽屉 | 四个分组标题；战斗与物品 12 项、探索与地图 7 项、角色与信息 8 项、系统 2 项；总高约 1.6 屏，单滚动器 | p02、p11 |
| 盟友命令 | 第四行 喊叫/攻击/撤退/停止/守卫/跟随，日志 `screen=19`；返回键取消后恢复 GAME 行 | p03、p04 |
| 丢弃 | 进入多选背包，第四行 确定/返回/上一类/下一类/全选 | p05 |
| 原地自动战斗 | “视线内没有目标！”，回合不变 | p06 |
| 跨层旅行 | 旅行提示，第四行 确定/返回/帮助，`screen=15` | p07 |
| 地牢概览 | 概览页打开，NAVIGATION 上下文 | p08 |
| 搜索 | “搜索什么”文本提示，TEXT 上下文自动展开完整键盘 | p09 |
| 系统菜单 | 原生 GameMenu（保存、宏、帮助、放弃角色带原确认） | p12 |
| 消息历史 | 消息历史页打开 | p13 |
| 金币 | “你持有0枚金币。” | p14 |
| 攻击 | 进入方向选择，TARGET 行 | p16 |
| 发射物品 | 物品选择菜单 | p17 |
| 箭袋 | QUIVER 页：聚焦模式/背包/清空箭袋 | p18 |
| 激活、切换武器 | 原生提示（无可激活物品/无副武器），回合不变，GAME 行保持 | p19、p20 |

未测：盟友命令的实际下达（当前角色无盟友；提示与键位链路已验证）；抽屉在字体 130% 下的
滚动成本。
