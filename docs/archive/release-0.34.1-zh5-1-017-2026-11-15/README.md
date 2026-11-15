# 0.34.1-zh5-1-017 发布前门禁记录（2026-11-15）

发布记录与玩家反馈：[Issue #411](https://github.com/yutio8888/crawl-chn-ai-test/issues/411)。
流程依据：[发布工作流](../../release-workflow.md)（本地只做发布前门禁和公开发布，
平台与游玩验收由测试玩家在发布后进行）。

已于 2026-11-15T02:36:59Z 公开为正式版并设为 Latest：
[Release 0.34.1-zh5-1-017](https://github.com/yutio8888/crawl-chn-ai-test/releases/tag/0.34.1-zh5-1-017)。
公开时尚无任何真机或游玩验收结果。

## 候选

- 注释标签 `0.34.1-zh5-1-017`，提交 `f1536df51623f1b1ea6da1b68b23fdb663dffbcd`
  （#413 发布说明合并提交，已含 #410 WebTiles 资源 URL 修复及第 23–50 轮修复）。
- `evidence/RELEASE-MANIFEST.txt` 与 `evidence/SHA256SUMS` 为 Release 原件副本；
  安装包本身不入库。MANIFEST 列出 Windows Tiles、Windows Console、Linux Console x86_64、
  macOS Tiles、Android。

## 发布前门禁结果

- 标签 CI run 43664720898 首次尝试 14/14 job success，无重跑。
- 草稿 Release 恰为七项资产；`sha256sum -c SHA256SUMS` 五个安装包全部 OK；MANIFEST
  摘要、本地 SHA-256 与 GitHub 资产 digest 逐项一致；公开后回下载再次校验 OK，digest 不变。
- APK：`org.develz.crawl`，versionName `0.34.1-zh5-1-017`，versionCode 947（016 为 851），
  ABI arm64-v8a/armeabi-v7a/x86/x86_64；apksigner v1/v2/v3 验证通过，签名证书 SHA-256
  `fb3ce3ed1cc644cf6640f3a0acdd71eaef534372d6caf36ec0708c6251971801`，与 0.34.1-zh5-1-016 相同。
- macOS DMG、Windows 与 Linux ZIP 仅核对校验和与清单。

## 未覆盖

本版未做任何本地游戏、模拟器或真机验收，也未测试从 016 覆盖升级。各平台启动、
中文显示、存读档与升级安装均待测试玩家按 Release 正文中的检查点反馈。
WebTiles 修复只作用于服务器部署（webserver 代码与同次构建的 `crawl`、`game_data`），
下载包不包含该部署；线上贴图异常的实际原因未直接取证，待部署后反馈。
