# 0.35-trunk-011 发布前门禁记录（2026-11-13）

发布记录与玩家反馈：[Issue #343](https://github.com/yutio8888/crawl-chn-ai-test/issues/343)。
流程依据：[发布工作流](../../release-workflow.md)（本地只做发布前门禁和公开发布，
平台与游玩验收由测试玩家在发布后进行）。

已于 2026-11-13T22:22:51Z 公开为 prerelease（非 latest）：
[Release 0.35-trunk-011](https://github.com/yutio8888/crawl-chn-ai-test/releases/tag/0.35-trunk-011)。
公开时 Latest 仍为 0.34.1-zh5-1-016；尚无任何真机或游玩验收结果。

## 候选

- 注释标签 `0.35-trunk-011`，提交 `302f1aeb791b93d13596f58fb548035613a9ced7`（#341 合并提交）。
- `evidence/RELEASE-MANIFEST.txt` 与 `evidence/SHA256SUMS` 为 Release 原件副本；
  安装包本身不入库。MANIFEST 列出 Windows Tiles、macOS Tiles、Android，Linux 仅 CI 构建。

## 发布前门禁结果

- 标签 CI run 43455849951 第 6 次尝试 14/14 job success。此前多次尝试中 macOS job
  未分配到 GitHub 托管 runner（无执行步骤）而被取消，均按 `gh run rerun --failed`
  重跑，未修改工作流或绕过门禁。
- 草稿 Release 恰为五项资产；`sha256sum -c SHA256SUMS` 三个安装包全部 OK；公开后
  GitHub 资产 digest 与本地 SHA-256 逐项一致。
- APK：`org.develz.crawl.trunk`，versionName `0.35-trunk-011`，versionCode 846
  （010 为 765），ABI arm64-v8a/armeabi-v7a/x86/x86_64；apksigner v1/v2/v3 验证通过，
  签名证书 SHA-256 `fb3ce3ed1cc644cf6640f3a0acdd71eaef534372d6caf36ec0708c6251971801`，
  与回下载的 0.35-trunk-010 APK 证书相同。
- macOS DMG 与 Windows ZIP 仅核对校验和与清单。

## 未覆盖

本版未做任何本地游戏、模拟器或真机验收。Windows、macOS、Android 的启动、中文显示、
存读档与升级安装均待测试玩家按 Release 正文中的检查点反馈。
