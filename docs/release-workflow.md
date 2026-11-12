# DCSS 中文版正式发布工作流

本文定义首个多平台正式版及同一上游基线后续修订版的最小发布边界。它不替代
代码/翻译审查，也不授权自动公开 Release。

每个候选的实施、发布前门禁与发布后测试玩家验收反馈记录在该候选对应的
release issue 中；首个正式版的
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
APK 的 `res/` 普通资源文件按 Android 的精确路径查找语义区分大小写，允许 AAPT2
资源路径缩名产生的 `res/2F.xml` / `res/2f.xml` 等不同文件；精确重名、目录冲突及
其他命名空间的大小写冲突仍会失败。Windows ZIP 与 macOS DMG 不使用此例外。
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

按维护者 2026-11-11 的指示，本地只负责发布前门禁和公开发布；真实设备运行与
游玩验收改由测试玩家在发布后进行。本地设备不足、未覆盖自然游玩或升级安装，
不再是公开的前置条件，也不另开本地模拟器或真机验收任务。此规定替代此前
“草稿阶段完成多平台人工验收后才能公开”的门槛。

发布前本地门禁（全部满足后方可公开）：

- 标签触发的全部正式发布门禁 job 成功；因 runner 未接单而取消的 job 按现有机制
  重跑通过，不跳过、不绕过；
- 候选身份正确：标签、准确提交 SHA 与 `RELEASE-MANIFEST.txt` 一致；
- 用 `sha256sum -c SHA256SUMS` 复核三个下载文件，资产只有 Windows ZIP、macOS DMG、
  Android APK、`SHA256SUMS` 和 `RELEASE-MANIFEST.txt`，共五项；
- Android APK 的包名、应用名、`versionName` 与签名可验证，签名证书与此前同线
  已发布版本一致；
- 发布说明列明玩家可见变化、支持平台、已知问题、延期项目、准确提交 SHA、已做的
  包核验与任何补充证据，以及待测试玩家验证的项目和反馈方式；不得把构建成功、
  包核验或模拟器结果写成真机验收通过。

公开须有维护者授权；授权可在打标签前或草稿生成后给出。公开后，测试玩家用最终
下载包验证：Windows 与 macOS（含 Gatekeeper“打开/仍要打开”）解压或挂载、启动、
中文默认语言、字体与主菜单；Android 真机安装或升级、启动与中文显示；新游戏、
帮助、存档和读档；trunk 与稳定版并存安装及存档隔离。反馈与覆盖状态记录在对应
release issue。若发现阻塞问题，保留 Release 与 CI 原始证据，修复后用新的标签发布；
不得移动或复用已经对外分发的标签。

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
`latest=false`；满足前述发布前本地门禁并有维护者授权后即可公开，公开时必须保留
prerelease 且不得标为 latest，平台验收由测试玩家在发布后进行。失败时使用新序号
重新发布。

发布说明须明确：**trunk 存档不能回到稳定版，两条线可并存安装**。只用稳定版存档副本
测试迁移，并记录 trunk 存读档结果与稳定版原件未变化的证据。

Android 使用固定的 `org.develz.crawl.trunk` 包名与 `Dungeon Crawl Stone Soup Trunk`
应用名，首次发布后保持身份不变。构建时通过 `ANDROID_APPLICATION_ID` 和
`ANDROID_APP_NAME` 传入，`versionName` 必须与 `build.h` 的长版本一致。
发布后测试玩家的设备验收可参考 [Android 手动验收流程](android-architecture.md)，
确认稳定版包仍在、存档在验收前后未变化。**不得使用固定包名的
`test-android-topbar.sh` 冒烟脚本**，
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
隔离参数。存读档及并存安装由测试玩家在发布后验证，并在发布说明中列为待验证项。

## 验收组织与故障处理建议

本节同时适用于稳定版与 trunk 预发布，供汇总发布后测试玩家的验收反馈与排障；
不修改上文门禁，也不新增审批、验证 profile 或跟踪系统。可在对应 release issue
使用下表，按实际平台范围裁剪；状态按证据填写“通过／未通过／未测／受阻”。构建成功、
发布授权和其他平台的结果，都不证明该平台人工验收通过。

| 平台／前端 | 包名与 SHA-256 | 系统、CPU／ABI、测试人 | 启动／中文 | 新游戏／帮助 | 保存／重载 | 结果与问题链接 |
| --- | --- | --- | --- | --- | --- | --- |
| Windows Tiles | 待填 | 待填 | 未测 | 未测 | 未测 | 待填 |
| Windows Console | 待填 | 待填 | 未测 | 未测 | 未测 | 待填 |
| Linux Console | 待填 | 待填 | 未测 | 未测 | 未测 | 待填 |
| macOS Tiles | 待填 | 待填 | 未测 | 未测 | 未测 | 待填 |
| Android 真机 | 待填 | 待填 | 未测 | 未测 | 未测 | 待填 |

草稿交付时，建议一并提供下载入口、校验方法、支持架构、操作清单及反馈位置，
尽早了解可用设备。对固定下载包完成验收；若修复后换了包，重新核对版本和摘要，
并按变化复测受影响场景。无法测试的平台保持明确的覆盖缺口，可约定反馈负责人
或下一步处理方式；未测不宜被扩大为所有后续工作都要停顿。正常游玩深度与问题记录方式见
[实际游玩测试建议](zh-testing.md#实际游玩测试与验收修复建议)。

CI 失败先核实候选 SHA、触发事件、失败步骤及实际 runner 的系统、架构和工具链。
同一工作流名称或检查名称不保证使用相同环境；其他提交或定时构建的成功结果不能
替代当前 PR 的检查。对尚未获得 runner 就取消的任务，记录容量问题并按现有机制
重试；对进入编译或测试后失败的任务，保留实际错误并修复根因。若只是临时容量
问题，可优先考虑重试；确需切换 runner 时，应把工具链和依赖兼容性纳入验证。
模拟平台的测试还要注意宏的作用范围，避免目标平台宏改变宿主标准库的判断；
混入目标平台头文件通常不能解决这种测试隔离问题。

产物校验失败时，用真实归档核实平台语义，区分损坏包与校验器误报。修正误报应
只调整证明有误的边界，并保留其他安全与完整性检查，同时检查真实产物与负例回归。
例如 [PR #182](https://github.com/yutio8888/crawl-chn-ai-test/pull/182) 修正了合法
AAPT2 `res/` 大小写资源的误报，并撤回了应对容量问题引入的 runner 迁移；期间另一
主分支定时构建成功，并不能替代不同候选、不同 OS/SDK 环境下的 PR 验证。
可复用未变内容的有效证据，避免不必要的整套重跑。重试或换候选仍
遵循上文的不可变标签、create-only 资产边界和候选验证要求。

发布记录宜分别说明平台验收事实、遗留问题和发布决定。若明确的会话指令与默认
流程有差异，应按适用的指令层级处理，并如实留下决定及证据缺口；授权不是测试
结果，后续补测也不能倒填成发布前已通过。已公开版本的维护记录与下一候选验收
可以继续推进，当前状态以对应 Issue、PR 和 Release 为准。例如稳定线已公开的
[012 Release](https://github.com/yutio8888/crawl-chn-ai-test/releases/tag/0.34.1-zh5-1-012)
的发布事实与各平台验收覆盖是不同记录，具体证据见
[Issue #181](https://github.com/yutio8888/crawl-chn-ai-test/issues/181)。

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
