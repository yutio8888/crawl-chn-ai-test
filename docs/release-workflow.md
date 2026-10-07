# DCSS 中文版正式发布工作流

本文定义首个多平台正式版及同一上游基线后续修订版的最小发布边界。它不替代
代码/翻译审查，也不授权自动公开 Release。

每个候选的实施与人工验收状态记录在该候选对应的 release issue 中；首个正式版的
历史记录见已关闭的
[GitHub Issue #20](https://github.com/yutio8888/crawl-chn-ai-test/issues/20)。

## 版本与平台范围

- 上游内容基线：`0.34.1`。
- 下游正式版标签：`0.34.1-zhA-B-CCC`。`A` 是中文版主版本，`B` 是该主版本下的
  发布系列，两者均从 1 开始且不补零；`CCC` 是系列内候选/修订序号，范围为
  `001`–`999`，固定三位并单调递增。
- 新规则的首个候选标签为 `0.34.1-zh5-1-001`。新候选使用同一系列中下一个未被
  使用的 `CCC`（先 `git fetch --tags origin`，再以 `git tag -l '0.34.1-zh*'` 为准），
  不得移动或复用任何已有标签；
  旧规则下的 `0.34.1-zh1` 至 `0.34.1-zh4` 同样作为历史标签保留。
- 正式平台：Windows Tiles、macOS Tiles、Android。
- Linux 仍保留日常 CI 编译验证，不进入正式版资产范围。

`crawl-ref/source/util/gen_ver.pl` 将合法的 `-zhA-B-CCC` 版本识别为正式版，而不是
上游 alpha/beta/rc 预发布版；为保证历史标签仍可复现构建，它也继续识别旧的
`-zhN` 格式。新 Release 门禁只接受三段格式。标签必须指向已经提交且通过项目审查
边界的不可变候选。

## 自动门禁

推送匹配 Actions glob `0.34.1-zh[0-9]*-[0-9]*-[0-9][0-9][0-9]` 的标签后，
`.github/workflows/ci.yml` 会先用严格正则拒绝不合法标签，再执行以下门禁：

1. 运行工具测试、静态 ZH CI、Catch2、帮助系统运行时测试和完整 L1+L2+L3 运行时；
2. 构建 Windows Tiles ZIP、macOS Tiles ad-hoc 签名 DMG，以及由项目密钥签名的四 ABI
   Android APK；Linux Console 继续作为独立 CI 质量信号，不阻塞草稿 Release；
3. 验证 Windows ZIP、macOS DMG 与 Android APK 形成精确的封闭集合；DMG 在 macOS
   runner 上挂载，APK 作为 ZIP 独立校验路径与成员，并用 `apksigner verify` 复核下载后
   的最终文件签名；
4. 检查归档路径安全、成员唯一性、平台主程序、中文 TextDB、设置文件、许可证，以及
   Tiles 包中的 Maple 字体和 OFL 许可证；`i18n/zh`、
   `database/zh`、`descript/zh` 三棵运行时中文数据树会从标签 checkout 完整枚举，数据、
   设置、字体和许可证内容必须与源文件一致（Windows 文本按打包行为归一化 CRLF）；
   APK 内三棵树位于 `assets/dat/...`，并须精确包含 `arm64-v8a`、`armeabi-v7a`、`x86`、
   `x86_64` 的 `libmain.so` 与 `libpcre.so`；
5. 生成 `SHA256SUMS` 与绑定标签、40 位提交 SHA、平台范围的
   `RELEASE-MANIFEST.txt`；
6. 仅创建一次 GitHub 草稿 Release。

校验器是 `.claude/scripts/verify_release_artifacts.py`。缺少文件、空文件、未知产物、
内容漂移、不可执行主程序、重复/大小写冲突成员、路径穿越、符号链接、特殊归档成员或
损坏归档，以及 APK 缺少签名、ABI 或关键 native library 都会使发布失败。
自动流程拒绝任何同标签的既有 Release（包括 draft），也不会上传或刷新其资产。工作流若在
草稿创建后重跑，会停在 create-only 边界；需要修复产物时必须递增 `CCC` 并使用新标签。
`CCC` 到达 `999` 后递增 `B`，并从 `001` 重新开始；不回收旧编号。

## 候选准备

1. 在仓库 Actions secrets 中配置 `ANDROID_KEYSTORE_BASE64`（keystore 文件的 Base64）、
   `ANDROID_KEYSTORE_PASS`、`ANDROID_KEY_ALIAS`，以及可选的 `ANDROID_KEY_PASS`；未配置
   `ANDROID_KEY_PASS` 时使用 store password。密码只通过 `apksigner` 的 `env:` 输入，
   不得出现在命令行参数值或日志中。任一必需 secret 缺失、Base64 无法解码或解码结果
   为空时，标签 job 会在 release Gradle 构建前失败；密码、alias 或 keystore 内容错误会
   在签名阶段失败，未签名或签名无法验证的 APK 不会上传。
2. 确认候选工作树已提交且干净，版本范围、延期平台和已知问题已经写入 release issue。
3. 按 `.agents/policies/review-contract.md` 使用 `--base <base> --head <candidate>`
   运行匹配 profile，或复用内容及依赖未变化的验证证据，并由
   `classify_reviewers.py` 路由领域审查；现有 GitHub Actions CI 必须通过。
4. 从目标分支检出通过验证、领域审阅与 CI 的准确提交；不得从另一个 linked
   worktree 移动目标分支引用。
5. 经发布负责人确认版本号后，创建 annotated tag：

   ```bash
   git tag -a <tag> -m "DCSS 中文版 <tag>"
   git push origin <tag>
   ```

标签推送会启动自动门禁。不要在候选提交、审查记录或版本名尚未确认时执行这一步。

## 草稿验收与公开

所有正式发布门禁 job 成功后，发布负责人在草稿 Release 中完成以下人工验收：

- 用 `sha256sum -c SHA256SUMS`（或平台等价工具）复核 Windows、macOS 与 Android
  下载文件；
- 在全新 Windows 环境解压并启动 Tiles，确认中文默认语言、中文字体和主菜单；
- 完成新游戏、帮助、存档和读档 smoke，并记录 Windows 版本与 CPU 架构；
- 在 macOS 环境校验 DMG 的 SHA-256、打开磁盘映像并启动 Tiles，确认中文默认语言、
  中文字体和主菜单；由于没有 Apple Developer 签名/公证，按发布说明完成一次
  Gatekeeper 的“打开/仍要打开”确认，并记录 macOS 版本与 CPU 架构；
- 完成新游戏、帮助、存档和读档 smoke，并记录 macOS 版本与 CPU 架构；
- 在至少一台 Android 真机安装下载后的签名 APK，记录 Android 版本、设备与 CPU ABI；
  确认安装/升级、启动、中文默认语言、中文字体与主菜单，并完成新游戏、帮助、存档和
  读档 smoke；
- 核对发布说明中的玩家可见变化、支持平台、已知问题、延期项目和准确提交 SHA；
- 核对 Release 仍为 draft，且资产只有 Windows ZIP、macOS DMG、Android APK、
  `SHA256SUMS` 和 `RELEASE-MANIFEST.txt`，共五项。

自动流程到草稿为止。只有上述人工验收全部有记录，且发布负责人明确批准后，才能在
GitHub 界面公开 Release。若任一项失败，保留草稿和 CI 原始证据，修复后用新的
`0.34.1-zhA-B-CCC` 标签发布；不得移动或复用已经对外分发的标签。

## trunk 预发布

`chn-trunk` 持续跟进固定的上游 master 提交；同步引入的新内容须完成翻译和领域审查，
才能对外发布。稳定线与 trunk 线分别发布，不把 trunk 合回稳定线。

- 标签格式为 `X.Y-trunk-NNN`，`NNN` 是三位序号 `001`–`999`，在同一 `X.Y` 下递增，
  不移动或复用已有标签。序号用尽时停止发布，另行决定下一步，不回收编号。
- `X.Y` 必须等于候选提交可达的最近上游 annotated a 标签的主版本号；例如
  `0.35-a0` 对应 `0.35-trunk-001`。CI 从 `https://github.com/crawl/crawl` 只读取回
  a 标签；取回失败、没有可达 a 标签或主版本不匹配时失败，不回退到稳定版版本串。
- 一个提交最多有一个 trunk 标签。打标签前先执行
  `git tag --points-at <commit> --list '*-trunk-*'`，确认输出为空；同时查看该 `X.Y`
  已有标签，选择下一个未使用的序号。
- 发布负责人确认准确候选 SHA、上游基线 SHA、版本号、翻译完成证据、领域审查及 CI
  结果后，才可创建 annotated tag。标签须指向该准确提交；检查 annotated 对象、
  提交指向和 `git describe --exact-match` 身份的门禁继续适用。
- 版本类型始终为 `VER_ALPHA`。精确命中匹配标签时使用裸标签；标签后开发提交带
  `-N-g<下游SHA>`。源码包的 `util/release_ver` 使用同一筛选规则。trunk 线不支持
  Xcode 工程和 `util/mac-crawl-build-update-cdo` 两条构建路径；macOS 使用 Makefile。

trunk 标签触发与正式版相同的完整发布依赖链，包括完整 L1+L2+L3 运行时测试、
Windows/macOS/Android 构建及 `verify_release_artifacts.py` 的封闭集合校验。
校验器接受 trunk 标签，生成绑定裸标签和准确提交的 `SHA256SUMS` 与
`RELEASE-MANIFEST.txt`。自动流程仅创建草稿，设置 GitHub prerelease 和
`latest=false`；发布负责人完成前述多平台人工验收后，方可公开，公开时也必须保留
prerelease 且不得标为 latest。失败时使用新序号重新发布。

发布说明须明确：**trunk 存档不能回到稳定版，两条线可并存安装**。只用稳定版存档副本
测试迁移，并记录 trunk 存读档结果与稳定版原件未变化的证据。

Android 使用固定的 `org.develz.crawl.trunk` 包名与 `Dungeon Crawl Stone Soup Trunk`
应用名，首次发布后保持身份不变。构建时通过 `ANDROID_APPLICATION_ID` 和
`ANDROID_APP_NAME` 传入，`versionName` 必须与 `build.h` 的长版本一致。
设备验收遵循 [Android 手动验收流程](android-architecture.md)，确认稳定版包仍在、
存档在验收前后未变化。**不得使用固定包名的 `test-android-topbar.sh` 冒烟脚本**，
尤其不得在装有稳定版的设备上运行其 `--fresh-install`。

各平台 trunk 的默认存档隔离已在构建参数中实施：

| 平台 | trunk 存档位置 |
|---|---|
| Windows | `%APPDATA%/crawl-trunk/saves/`，通过 `SAVEDIR='~/crawl-trunk'` 指定 |
| Linux | `~/.crawl-trunk/saves/`，通过 `SAVEDIR='~/.crawl-trunk'` 指定 |
| macOS | `~/.crawl-trunk/saves/`，通过 `SAVEDIR='~/.crawl-trunk'` 指定 |
| Android | 应用专属外部文件目录下的 `saves/`，通常为 `Android/data/org.develz.crawl.trunk/files/saves/` |

Windows 上的 `~` 解析到 `%APPDATA%`；Linux/macOS 在运行时解析到用户主目录，
不依赖启动工作目录。macOS 显式构建路径优先于默认 Application Support 路径；
未定义 `SAVE_DIR_PATH` 的构建继续使用原来的默认行为。Windows 包仍须解压到独立目录，
避免覆盖稳定版程序。

macOS trunk 的应用包为 `Dungeon Crawl Stone Soup Trunk - Tiles.app`，
bundle identifier 为 `net.sourceforge.crawl-ref.trunk`，可与稳定版同时放入
`/Applications`。通过 `APP_NAME` 和 `BUNDLE_IDENTIFIER` 构建参数生成名称和同一份 plist；
两项默认值保持稳定版原样。CI 仅在非 `0.34.1-zh*` 标签构建中传入 macOS/Windows
隔离参数。首个公开 trunk 预发布仍须完成人工存读档及并存安装验收。

## 本地校验

工具测试会自动发现发布校验器的正例和逐项负向变异：

```bash
bash .claude/scripts/run_isolated.sh python3 .claude/scripts/tests/test_verify_release_artifacts.py
bash .claude/scripts/run_isolated.sh bash .claude/scripts/tests/run_all.sh
```

完整仓库变更仍使用项目统一入口：

```bash
bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh --profile code
```
