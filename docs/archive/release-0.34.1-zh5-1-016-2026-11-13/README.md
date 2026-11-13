# 0.34.1-zh5-1-016 发布前门禁记录（2026-11-13）

发布记录与玩家反馈：[Issue #344](https://github.com/yutio8888/crawl-chn-ai-test/issues/344)。
流程依据：[发布工作流](../../release-workflow.md)（本地只做发布前门禁和公开发布，
平台与游玩验收由测试玩家在发布后进行）。

已于 2026-11-13T21:58:10Z 公开为正式版并设为 Latest：
[Release 0.34.1-zh5-1-016](https://github.com/yutio8888/crawl-chn-ai-test/releases/tag/0.34.1-zh5-1-016)。
公开时尚无任何真机或游玩验收结果。

## 候选

- 注释标签 `0.34.1-zh5-1-016`，提交 `1682aafe83475b42506f3b08ce81e3f3f354dd51`
  （#345 合并提交，已含 #346 发条蜂英文所有格修复）。
- `evidence/RELEASE-MANIFEST.txt` 与 `evidence/SHA256SUMS` 为 Release 原件副本；
  安装包本身不入库。MANIFEST 列出 Windows Tiles、Windows Console、Linux Console x86_64、
  macOS Tiles、Android。

## 发布前门禁结果

- 标签 CI run 43464010204 第 9 次尝试 14/14 job success。此前尝试中 macOS job
  多次未分配到 GitHub 托管 runner 被取消，另有一次 DMG 打包 `hdiutil: create failed -
  Resource busy`；均按 `gh run rerun --failed` 重跑，未修改工作流或绕过门禁。
- 草稿 Release 恰为七项资产；`sha256sum -c SHA256SUMS` 五个安装包全部 OK；公开后
  GitHub 资产 digest 与本地 SHA-256 逐项一致。
- APK：`org.develz.crawl`，versionName `0.34.1-zh5-1-016`，versionCode 851，
  ABI arm64-v8a/armeabi-v7a/x86/x86_64；apksigner v1/v2/v3 验证通过，签名证书 SHA-256
  `fb3ce3ed1cc644cf6640f3a0acdd71eaef534372d6caf36ec0708c6251971801`，与回下载的
  0.34.1-zh5-1-015 APK 证书相同。
- macOS DMG、Windows 与 Linux ZIP 仅核对校验和与清单。

## 未覆盖

本版未做任何本地游戏、模拟器或真机验收，也未测试从 015 覆盖升级。各平台启动、
中文显示、存读档与升级安装均待测试玩家按 Release 正文中的检查点反馈。
