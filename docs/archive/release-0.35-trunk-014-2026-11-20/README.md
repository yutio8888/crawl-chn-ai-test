# 0.35-trunk-014 发布前门禁记录（2026-11-20）

发布记录与玩家反馈：[Issue #469](https://github.com/yutio8888/crawl-chn-ai-test/issues/469)。
流程依据：[发布工作流](../../release-workflow.md)（本地只做发布前门禁和公开发布，
平台与游玩验收由测试玩家在发布后进行）。

已于 2026-11-20T10:25:12Z 公开为 prerelease（非 latest）：
[Release 0.35-trunk-014](https://github.com/yutio8888/crawl-chn-ai-test/releases/tag/0.35-trunk-014)。
公开时 Latest 仍为 `0.34.1-zh5-1-018`；尚无任何真机或游玩验收结果。

## 候选

- 注释标签 `0.35-trunk-014`，提交 `c662be078cb34f6b1519f0bba4f3eca0ff88b427`（#468 合并提交）。
- 相对 `0.35-trunk-013` 包含：上游同步 #443（`ecd2bd72d73`）、#460（`9cbd9afba78`）；#440（013 归档）、#441、#447、#448、#450、#453、#454、#456、#458、#462、#464、#465、#468。
- `evidence/RELEASE-MANIFEST.txt` 与 `evidence/SHA256SUMS` 为 Release 原件副本；安装包本身不入库。MANIFEST 列出 Windows Tiles、macOS Tiles、Android，Linux 仅 CI 构建。
- 公开时将 `target_commitish` 设为 `c662be078cb34f6b1519f0bba4f3eca0ff88b427`，并以 `announcement.md` 替换自动草稿说明。

## 发布前门禁结果

- 标签 CI [run 44710669630](https://github.com/yutio8888/crawl-chn-ai-test/actions/runs/44710669630) 首次尝试 14/14 job success，无重跑。
- 草稿 Release 恰为五项资产；`sha256sum -c SHA256SUMS` 三个安装包全部 OK；MANIFEST 摘要与本地回下载校验逐项一致。
- APK：`org.develz.crawl.trunk`（Dungeon Crawl Stone Soup Trunk），versionName `0.35-trunk-014`，versionCode `1036`（013 为 `991`），ABI `arm64-v8a` / `armeabi-v7a` / `x86` / `x86_64`（均含 `libmain.so` 与 `libpcre.so`）；`apksigner` v1/v2/v3 验证通过，签名证书 SHA-256 `fb3ce3ed1cc644cf6640f3a0acdd71eaef534372d6caf36ec0708c6251971801`，与 `0.35-trunk-013` 一致。
- macOS DMG 与 Windows ZIP 仅核对校验和与清单。

## 未覆盖

本版未做任何本地游戏、模拟器或真机验收。Windows、macOS、Android 的启动、中文显示、存读档与升级安装均待测试玩家按 Release 正文与 Issue #469 中的检查点反馈。旧存档已生成的名称与消息历史不迁移。本版无 WebTiles 服务器端新改动。
