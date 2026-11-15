# 0.35-trunk-012 发布前门禁记录（2026-11-15）

发布记录与玩家反馈：[Issue #412](https://github.com/yutio8888/crawl-chn-ai-test/issues/412)。
流程依据：[发布工作流](../../release-workflow.md)（本地只做发布前门禁和公开发布，
平台与游玩验收由测试玩家在发布后进行）。

已于 2026-11-15T02:09:47Z 公开为 prerelease（非 latest）：
[Release 0.35-trunk-012](https://github.com/yutio8888/crawl-chn-ai-test/releases/tag/0.35-trunk-012)。
公开时 Latest 仍为 0.34.1-zh5-1-016（其后 0.34.1-zh5-1-017 公开为 Latest）；尚无任何真机或游玩验收结果。

## 候选

- 注释标签 `0.35-trunk-012`，提交 `bb061823cc2b75d9fe3672d1a5d884ec28079ec3`
  （#409 合并提交，含上游同步 #347 及第 23–50 轮修复）。
- `evidence/RELEASE-MANIFEST.txt` 与 `evidence/SHA256SUMS` 为 Release 原件副本；
  安装包本身不入库。MANIFEST 列出 Windows Tiles、macOS Tiles、Android，Linux 仅 CI 构建。
- 草稿由 CI 自动生成的正文在公开时替换为含相对 011 变化、逐项 PR、玩家检查点与技术核验的正文，
  `target_commitish` 设为上述提交。

## 发布前门禁结果

- 标签 CI run 43662818320 首次尝试 14/14 job success，无重跑。
- 草稿 Release 恰为五项资产；`sha256sum -c SHA256SUMS` 三个安装包全部 OK；MANIFEST
  摘要、本地 SHA-256 与 GitHub 资产 digest 逐项一致；公开后回下载再次校验 OK，digest 不变。
- APK：`org.develz.crawl.trunk`，versionName `0.35-trunk-012`，versionCode 944
  （011 为 846），ABI arm64-v8a/armeabi-v7a/x86/x86_64；apksigner v1/v2/v3 验证通过，
  签名证书 SHA-256 `fb3ce3ed1cc644cf6640f3a0acdd71eaef534372d6caf36ec0708c6251971801`，
  与 0.35-trunk-011 相同。
- macOS DMG 与 Windows ZIP 仅核对校验和与清单。

## 未覆盖

本版未做任何本地游戏、模拟器或真机验收。Windows、macOS、Android 的启动、中文显示、
存读档与升级安装均待测试玩家按 Release 正文中的检查点反馈。WebTiles 修复只作用于服务器
部署（webserver 代码与同次构建的 `crawl`、`game_data`），下载包不包含该部署；线上贴图异常的
实际原因未直接取证，待部署后反馈。
