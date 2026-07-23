# DCSS 中文版首个正式版发布就绪评估

- 评估日期：2026-07-23
- 评估 worktree：`.worktrees/first-release-readiness`
- 评估分支：`codex/first-release-readiness`
- 候选提交：`35c36aef1d6cbb454b5f0af6fafb76dec0ee98d9`
- 上游内容基线：annotated tag `0.34.1`
- 术语表 SHA-256：`758af12d419613516a6199cb1c2684df21b093e02d21894373a8ff9a03c840be`

## 结论

**当前代码与汉化资产已经达到“正式版候选”质量，但项目今天还不宜直接发布首个正式版。**

> 发布决策更新（2026-07-24）：发布负责人已冻结首版为 `0.34.1-zh1`，仅包含
> Windows Tiles。macOS Tiles 因缺少可用验收环境，只保留 CI 编译产物，不生成正式
> Release 资产；Linux 只保留 CI 编译验证，Android 继续延期。因此下文关于“评估时尚未
> 冻结版本/范围”的内容保留为原始审计记录，不再是当前候选的未决事项。
>
> 实施进度：`codex/first-release-readiness` 已开始补齐
> [正式发布工作流](release-workflow.md)、桌面产物封闭集校验、校验和与草稿 Release；
> 发布范围与人工门禁由
> [GitHub Issue #20](https://github.com/yutio8888/crawl-chn-ai-test/issues/20) 跟踪。
> 在该候选合并、完成不可变边界审查并通过标签 CI 之前，本报告的正式发布结论不变。

分开判断如下：

- **产品与技术候选：Go。** 当前完整静态门禁、主要平台 CI 构建、帮助运行时以及本地
  L1+L2+L3 完整中文运行时均通过，没有发现会阻止玩家使用的确定性翻译、TextDB、协议或
  构建缺陷。
- **正式发布：条件性 No-Go。** 版本号和首版平台范围已经冻结；在发布流水线候选合并、
  标签 CI、Windows 人工验收和草稿批准完成前，仍不得公开正式 Release。

这不是“需要再做一轮大规模汉化”的 No-Go。若首版限定为桌面版，剩余工作主要是一次
范围明确的封版与发行工作，原则上不需要重写现有 i18n 架构。

## 已通过的证据

### 1. 基线与工作树

- `0.34.1` 是当前候选的祖先；当前分支在该标签之后有 968 个提交。
- 审计开始前、静态验证后和完整 runtime 后，主 worktree 与全部 submodule 均无源码改动。
- 远端默认分支 `chn-0.34.1-base` 在评估时仍精确指向 `35c36aef1d`。

### 2. 完整静态门禁

执行：

```bash
bash .claude/scripts/verify_zh.sh --profile ci
```

结果：

- 退出码：0
- 阻断失败：0
- scope：full
- SourceDB：13,547 个物理条目 / 13,547 个 canonical key / 0 collision
- 提取键覆盖：8,124 / 8,124（100%）
- 翻译静态检查：PASS
- 代码与 i18n 安全检查：PASS
- message-overlay 静态审计：PASS

本地证据：

- `.claude/metrics/verify/20260723T205722181858304+0800-2-35c36aef1d6c/verify.log`
- `.claude/metrics/verify/20260723T205722181858304+0800-2-35c36aef1d6c/metadata.json`

代码扫描另外给出 5 条 string-concatenation advisory。逐项检查后，它们都位于
`mark_milestone()` 的英文内部记录路径，并使用 `_god_name_en()` 等 canonical English
身份值；这些值按协议/显示分离政策应保持英文，不是玩家界面漏翻。

### 3. 当前 HEAD 的完整中文运行时

执行：

```bash
TERM=xterm-256color bash .claude/scripts/post_zh_runtime.sh full
```

结果：

- L1 Catch2：PASS，退出码 0
- L2 dlua：PASS，Issue 68 manifest 21 / 21，顺序和语义错误均为 0
- L3 RC Bot：PASS，总 manifest 17 / 17
- rendered panel PTY assertions：PASS
- wizard-assisted gameplay workflow assertions：PASS
- baseline 聚合：current total 0，regressions 0
- 总用时：961 秒
- 总失败：0

本地证据目录：

`.claude/metrics/verify/zh-runtime-20260723T131112Z-2/`

L2 stderr 中存在 coverage 构建切换造成的 `libgcov profiling error` 噪声，但功能测试、
marker 完整性和聚合结果均通过；当前发布不依赖这些覆盖率文件。建议在后续工具维护中隔离
`.gcda`，使发布证据更干净。

### 4. GitHub CI 与平台构建

当前提交的 push workflow：

<https://github.com/yutio8888/crawl-chn-ai-test/actions/runs/30005295391>

以下 job 成功：

- ZH Tooling Tests
- ZH CI Gate
- ZH Runtime Catch2
- ZH Help Runtime Tests
- Code Linting
- Linux Console
- Windows Tiles package
- macOS Tiles App
- Android buildTest

该 push 中 `ZH Runtime Full (L1+L2+L3)` 因触发条件被跳过；本报告用上面的精确 HEAD
本地 full 运行补齐了技术判断，但正式发布仍应在标签候选上生成公开 CI full 证据。

CI 当前保存两个临时 artifact：

| Artifact | 大小 | 到期时间 |
|---|---:|---|
| `windows-tiles` | 36,477,553 bytes | 2026-10-21 |
| `macos-tiles-app` | 83,109,380 bytes | 2026-10-21 |

### 5. 最近汉化改动的不可变审查

最近的玩家可见汉化修复 `f50be93575` 有完整 schema-v4 bundle：

- bundle：`01ed70028285d9d45c17a89c1642d3d4ff2e56045681016d23b32a79e927a06a`
- `translation-reviewer`：Ready，findings 0
- `zh-code-reviewer`：Ready，findings 0
- final approval：`go`

这说明最近的实际译文变更不是未经审查直接进入当前候选。

## 阻止“现在直接正式发布”的事项

### Blocker 1：没有冻结的发行契约

GitHub 在评估时有 5 个开放 issue，全部没有 milestone：

- #5 `source.txt` 拆分与加载守恒评估
- #6 语言守卫内硬编码中文的重新分类
- #8 Android 顶栏状态详情抽屉（P1、needs-review）
- #9 Android 功能入口菜单（blocked）
- #10 `conj_verb` 结构性债务（blocked）

这些 issue 并不都必须在首版修完：#5、#6、#10 主要是维护性或结构性债务，#8、#9
主要影响 Android 竖屏体验。真正的问题是项目没有明确记录哪些属于首版范围、哪些接受延期。
没有 release milestone、支持平台清单和已知问题声明，就无法把“开放 issue”机械地解释为
“允许延期”或“必须完成”。

后续创建的 [Issue #20](https://github.com/yutio8888/crawl-chn-ai-test/issues/20)
已经记录正式范围、`0.34.1-zh1` 和人工门禁。版本与平台范围现已确认，本 blocker 中的
范围决策部分已解除；标签、人工验收和公开批准仍按发布工作流跟踪。

### Blocker 2：没有正式版本身份和永久发行资产

- 仓库没有任何 GitHub Release。
- 除上游标签外，没有中文版正式标签。
- 当前 `git describe` 为 `0.34.1-968-g35c36aef1d`。
- Windows/macOS artifact 是会过期的 Actions 产物，不是永久 Release 资产。
- Linux 只验证了编译，没有上传玩家可下载包。
- Android 只构建了 `buildTest`，没有上传签名 release APK。
- 当前没有发行说明、已知问题清单和 SHA-256 manifest。

按照当前 Makefile，直接从未打中文版标签的 HEAD 打包，会把开发提交式版本写进包名和程序版本。
这适合作为 CI artifact，不适合作为首个正式版身份。

### Blocker 3：当前 HEAD 尚未形成一次完整的封版边界

默认分支未启用 branch protection。PR #19
（`test(i18n): stabilize Full L2 and L3 runtime checks`）：

- GitHub reviews 为空；
- PR 自身的 Full runtime 被跳过；
- 合并发生在多数 CI job 完成之前；
- 本地 schema-v4 evidence 中未找到该候选的 readiness/final approval。

后续 push CI 与本报告的完整 runtime 已证明当前代码能工作，但不能倒推为该次合并满足了项目
自己的不可变审查契约。正式发布前应在一个冻结提交上重新形成完整、可追溯的候选边界，而不是
把多个分支的历史绿灯拼成发布授权。

### Blocker 4：Android 已明确延期

如果首个正式版宣称支持 Android，则当前证据不足：

- CI 只有 `buildTest`，没有签名 release APK；
- #8 仍为 P1 needs-review，要求当前基线上的设备验收与集成；
- #9 依赖 #8；
- 没有发布候选 APK 的真机/模拟器验收记录。

首版已经明确限定为 Windows Tiles，macOS 因缺少验收环境而只保留 CI artifact，#8、#9
延期且不阻塞首版。Linux 同样不属于首版正式资产，只保留 CI 编译质量信号；这些延期会写入
release scope 和 known issues。

## 与 2026-07-16 评估相比

此前评估中的主要 P0 已经实质关闭：

- `source.txt` 结构损坏现在由解析级门禁发现；当前完整扫描为 0 结构错误。
- canonical key collision、相邻字面量、动态 key 和协议/显示边界的门禁已经扩充并通过。
- 工具测试总入口和完整 runtime 分层已进入 CI。
- Windows 与 macOS 已能生成并上传 package artifact。
- 当前条目与提取覆盖分别从 13,223 / 7,454 增至 13,547 / 8,124。

仍然存在的是当时已指出的“正式发行流水线”缺口：临时构建产物已经有了，但标签、永久 Release、
签名 Android、checksum、发布说明和支持矩阵还没有完成。

## 最小正式版清单

建议把以下项目作为一次短周期 release task，而不是继续扩大产品功能范围：

1. 建立首版 release issue/milestone，明确版本名、支持平台、已知问题和延期 issue。
2. 冻结精确候选提交；启用默认分支保护和 required checks，避免封版期间继续无审查漂移。
3. 给候选打下游 annotated tag；在标签上重新运行 CI，并显式启用 Full runtime。
4. 对计划发布的平台做安装后 smoke：
   - Windows：全新目录启动、默认中文、CJK 字体、新游戏、帮助、存读档；
   - macOS/Linux/Android：本版不生成正式资产，后续纳入时另行补齐平台验收。
5. 创建 GitHub Release，附发行说明、known issues、上游 `0.34.1` 与中文候选 SHA、
   字体/许可证说明、各产物 SHA-256。
6. 确认 release 页面上的产物可从全新环境下载、解压/安装和启动，再宣布正式版。

## 推荐决策

- **当前：先完成 `0.34.1-zh1` 的候选合并、标签 CI 和 Windows 人工验收。**
- **Windows 首版：完成上述最小清单后可转 Go；目前没有发现需要大规模返工的代码缺陷。**
- **macOS/Linux/Android：本版延期，不阻塞 `0.34.1-zh1`。**
