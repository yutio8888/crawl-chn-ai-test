# 0.35-trunk-013 发布前门禁记录（2026-11-18）

发布记录与玩家反馈：[Issue #439](https://github.com/yutio8888/crawl-chn-ai-test/issues/439)。
流程依据：[发布工作流](../../release-workflow.md)（本地只做发布前门禁和公开发布，
平台与游玩验收由测试玩家在发布后进行）。

已于 2026-11-18T05:19:31Z 公开为 prerelease（非 latest）：
[Release 0.35-trunk-013](https://github.com/yutio8888/crawl-chn-ai-test/releases/tag/0.35-trunk-013)。
公开时 Latest 仍为 0.34.1-zh5-1-017；尚无任何真机或游玩验收结果。

## 候选

- 注释标签 `0.35-trunk-013`，提交 `7c79008f70e1f9b88e47d1bf9cf136387a0e2a1b`
  （#437 合并提交；树与已复审且 CI 通过的 head `6decd95317` 逐字节相同）。
- 相对 `0.35-trunk-012` 包含：上游同步 #425、#430、#433；#416、#418、#419、#422、#423、
  #426、#428、#431、#434、#437；发布凭据归档 #415。稳定线专属的等级书名修复（#436）不在本版。
- `evidence/RELEASE-MANIFEST.txt` 与 `evidence/SHA256SUMS` 为 Release 原件副本；
  安装包本身不入库。MANIFEST 列出 Windows Tiles、macOS Tiles、Android，Linux 仅 CI 构建。
- 草稿由 CI 自动生成的正文在公开时替换为“玩家公告 + 技术附录”，`target_commitish` 设为上述提交。

## 玩家公告

- `announcement.md`：Release 正文开头的玩家公告终稿，按维护者要求在公开前由 Gemini 撰写，
  主持逐条核对事实（示例均在冻结提交的 `source.txt` 中实核）。
- `announcement-provenance.txt`：写作 agent、请求的 profile/model 与运行时报告 model
  （二者不一致，未断言后端型号）、修订记录及一处主持事实校对（“杂音”措辞）。

## 发布前门禁结果

- 标签 CI run 44238023026 首次尝试 14/14 job success，无重跑。
- 草稿 Release 恰为五项资产；`sha256sum -c SHA256SUMS` 三个安装包全部 OK；MANIFEST
  摘要、本地 SHA-256 与 GitHub 资产 digest 逐项一致；公开后回下载再次校验 OK，digest 不变。
- APK：`org.develz.crawl.trunk`（Dungeon Crawl Stone Soup Trunk），versionName
  `0.35-trunk-013`，versionCode 991（012 为 944），ABI arm64-v8a/armeabi-v7a/x86/x86_64；
  apksigner v1/v2/v3 验证通过，签名证书 SHA-256
  `fb3ce3ed1cc644cf6640f3a0acdd71eaef534372d6caf36ec0708c6251971801`，与 0.35-trunk-012 相同。
- macOS DMG 与 Windows ZIP 仅核对校验和与清单。

## 未覆盖

本版未做任何本地游戏、模拟器或真机验收。Windows、macOS、Android 的启动、中文显示、
存读档与升级安装均待测试玩家按 Release 正文中的检查点反馈。随机神器与书名改进的证据为
固定种子生产样本（英文输出逐字节不变），属有限样本。旧存档已生成的名称与消息历史不迁移。
本版无 WebTiles 服务器端新改动。
