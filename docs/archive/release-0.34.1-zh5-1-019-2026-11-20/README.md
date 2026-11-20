# 0.34.1-zh5-1-019 发布前门禁记录（2026-11-20）

发布记录与玩家反馈：[Issue #470](https://github.com/yutio8888/crawl-chn-ai-test/issues/470)。
流程依据：[发布工作流](../../release-workflow.md)（本地只做发布前门禁和公开发布，
平台与游玩验收由测试玩家在发布后进行）。

已于 2026-11-20T11:00:37Z 公开为正式版并设为 Latest：
[Release 0.34.1-zh5-1-019](https://github.com/yutio8888/crawl-chn-ai-test/releases/tag/0.34.1-zh5-1-019)。
公开时尚无任何真机或游玩验收结果。

## 候选

- 注释标签 `0.34.1-zh5-1-019`（tag 对象 `222f628c06364e4f2de9f83435c744973aef1ef0`），
  提交 `5a1ab9e93ebdf2f1dcfa2c7b66379e8df1ba68bf`（[#471](https://github.com/yutio8888/crawl-chn-ai-test/pull/471)
  发布说明合并提交，已含自 018 以来的 #446、#449、#451、#452、#455、#457、#459、
  #461、#463、#466、#467）。
- `evidence/RELEASE-MANIFEST.txt` 与 `evidence/SHA256SUMS` 为 Release 原件副本；
  安装包本身不入库。MANIFEST 列出 Windows Tiles、Windows Console、Linux Console x86_64、
  macOS Tiles、Android。

## 发布前门禁结果

- 标签 CI [run 44717255710](https://github.com/yutio8888/crawl-chn-ai-test/actions/runs/44717255710)
  首次尝试 14/14 job success，无重跑。
- Draft Release 恰为七项资产；`sha256sum -c SHA256SUMS` 五个安装包全部 OK；MANIFEST
  摘要与本地下载校验逐项一致。
- APK：`org.develz.crawl`（Dungeon Crawl Stone Soup），versionName `0.34.1-zh5-1-019`，
  versionCode `1039`（018 为 `998`），ABI `arm64-v8a` / `armeabi-v7a` / `x86` / `x86_64`
  （均含 `libmain.so` 与 `libpcre.so`）；`apksigner` v1/v2/v3 验证通过，签名证书 SHA-256
  `fb3ce3ed1cc644cf6640f3a0acdd71eaef534372d6caf36ec0708c6251971801`，与 0.34.1-zh5-1-018 相同。
- macOS DMG、Windows 与 Linux ZIP 仅核对校验和与清单。

## 未覆盖

本版未做任何本地游戏、模拟器或真机验收，也未测试从 018 覆盖升级。各平台启动、
中文显示、存读档与升级安装均待测试玩家按 Release 正文与 Issue #470 中的检查点反馈。
旧存档已生成的神器名、书名与历史消息记录不迁移。
