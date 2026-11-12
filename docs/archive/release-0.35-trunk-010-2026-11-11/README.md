# 0.35-trunk-010 发布前门禁与补充证据（2026-11-11）

发布记录与玩家反馈：[Issue #296](https://github.com/yutio8888/crawl-chn-ai-test/issues/296)。
流程依据：[发布工作流](../../release-workflow.md)（本地只做发布前门禁和公开发布，
平台与游玩验收由测试玩家在发布后进行）。

已于 2026-11-11T23:45:17Z 公开为 prerelease（非 latest）：
[Release 0.35-trunk-010](https://github.com/yutio8888/crawl-chn-ai-test/releases/tag/0.35-trunk-010)。
公开时尚无任何真机验收结果。

## 候选

- 标签 `0.35-trunk-010`，提交 `4b8c1a62ca26fef8a8df492bb7f1e0f86fa3ceed`。
- `evidence/RELEASE-MANIFEST.txt` 与 `evidence/SHA256SUMS` 为草稿 Release 原件副本；
  安装包本身不入库。

## 发布前门禁结果

- CI run 43030210300 最终 14 项 success。attempt 1、2 各有一个 macOS job 因
  “The job was not acquired by Runner of type hosted even after multiple attempts”
  被取消（无执行步骤），按现有机制重跑 failed jobs，attempt 3 全部成功。
- `sha256sum -c SHA256SUMS` 三项 OK；资产恰为五项。
- APK：`org.develz.crawl.trunk`，versionName `0.35-trunk-010`，versionCode 765，
  ABI arm64-v8a/armeabi-v7a/x86/x86_64；签名证书 SHA-256
  `fb3ce3ed1cc644cf6640f3a0acdd71eaef534372d6caf36ec0708c6251971801`，与 0.35-trunk-008 相同。
- Windows ZIP 含 `crawl.exe`、中文字体、`dat/i18n/zh`、`dat/database/zh`；macOS DMG
  仅核对校验和。

## Android 模拟器补充证据（不是真机验收）

AVD `dcss_api35_x86_64`（Android 15，x86_64，`-gpu swangle_indirect`），安装草稿同一 APK
（SHA-256 与 `SHA256SUMS` 一致）。模拟器上已装稳定版
`org.develz.crawl`（0.34.1-zh5-1-010-84-g91bb4030cc）。

| 步骤 | 结果 | 截图 |
|---|---|---|
| 首次安装，与稳定版并存 | 成功 | — |
| 启动游戏主菜单 | 中文、字体正常、标题 0.35-trunk-010 | `evidence/01-main-menu-zh.png` |
| 新游戏（人类战士） | HUD 与消息中文 | `evidence/02-new-game-hud.png` |
| 帮助 | 中文帮助目录 | `evidence/03-help.png` |
| Ctrl+S 存档 → 强制停止 → 重启 → 读档 | 成功，游戏时间 2.0 保持 | `evidence/04-reload.png` |
| 稳定版存档目录（615 个文件）md5 前后对比 | 完全一致 | — |

未覆盖：从 008 升级安装、Windows、macOS、Android 真机。截图哈希见
`evidence/SCREENSHOTS.sha256`。

## 已知问题（非本版回归）

- 帮助标题 “Dungeon Crawl Help” 译为“地下城 Crawl 帮助”，与“地牢爬行”不一致（008 已存在）。
- Android 原生启动器按钮为英文（未核对是否为既有设计）。
