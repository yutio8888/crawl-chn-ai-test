# DCSS 中文版正式发布工作流

本文定义首个桌面正式版及同一上游基线后续修订版的最小发布边界。它不替代
代码/翻译审查，也不授权自动公开 Release。

实施与人工验收状态统一记录在
[GitHub Issue #20](https://github.com/yutio8888/crawl-chn-ai-test/issues/20)。

## 版本与平台范围

- 上游内容基线：`0.34.1`。
- 下游正式版标签：`0.34.1-zhN`，其中 `N` 从 1 开始单调递增。
- 首版候选标签：`0.34.1-zh1`。
- 首发平台：仅 Windows Tiles。
- macOS Tiles 因缺少可用验收环境，不作为首版正式资产，但继续由 CI 构建并保存临时
  Actions artifact。Linux 仍保留日常 CI 编译验证，Android 暂缓；只有平台发布资产及
  相应验收完成后，才可在后续版本加入正式版范围。

`crawl-ref/source/util/gen_ver.pl` 将合法的 `-zhN` 版本识别为正式版，而不是上游
alpha/beta/rc 预发布版。标签必须指向已经提交且通过项目审查边界的不可变候选。

## 自动门禁

推送匹配 `0.34.1-zh*` 的标签后，`.github/workflows/ci.yml` 会：

1. 运行工具测试、静态 ZH CI、Catch2、帮助系统运行时测试和完整 L1+L2+L3 运行时；
2. 构建 Windows Tiles 正式资产；macOS Tiles 继续构建并上传临时 Actions artifact，
   Linux Console 继续作为独立 CI 质量信号，二者均不阻塞草稿 Release；
3. 验证 Windows 归档文件形成精确的封闭集合；
4. 检查归档路径安全、成员唯一性、平台主程序、中文 TextDB、设置文件、许可证，以及
   Tiles 包中的 Maple 字体和 OFL 许可证；`i18n/zh`、
   `database/zh`、`descript/zh` 三棵运行时中文数据树会从标签 checkout 完整枚举，数据、
   设置、字体和许可证内容必须与源文件一致（Windows 文本按打包行为归一化 CRLF）；
5. 生成 `SHA256SUMS` 与绑定标签、40 位提交 SHA、平台范围的
   `RELEASE-MANIFEST.txt`；
6. 仅创建一次 GitHub 草稿 Release。

校验器是 `.claude/scripts/verify_release_artifacts.py`。缺少文件、空文件、未知产物、
内容漂移、不可执行主程序、重复/大小写冲突成员、路径穿越、符号链接、特殊归档成员或
损坏归档都会使发布失败。
自动流程拒绝任何同标签的既有 Release（包括 draft），也不会上传或刷新其资产。工作流若在
草稿创建后重跑，会停在 create-only 边界；需要修复产物时必须使用新的 `0.34.1-zhN` 标签。

## 候选准备

1. 确认候选工作树已提交且干净，版本范围、延期平台和已知问题已经写入 release issue。
2. 按 `.agents/policies/review-contract.md` 准备不可变候选，并完成机械路由的就绪审查和
   final gate。
3. 从目标分支检出获批的准确提交；不得从另一个 linked worktree 移动目标分支引用。
4. 经发布负责人确认版本号后，创建 annotated tag：

   ```bash
   git tag -a 0.34.1-zh1 -m "DCSS 中文版 0.34.1-zh1"
   git push origin 0.34.1-zh1
   ```

标签推送会启动自动门禁。不要在候选提交、审查记录或版本名尚未确认时执行这一步。

## 草稿验收与公开

所有正式发布门禁 job 成功后，发布负责人在草稿 Release 中完成以下人工验收：

- 用 `sha256sum -c SHA256SUMS`（或平台等价工具）复核 Windows 下载文件；
- 在全新 Windows 环境解压并启动 Tiles，确认中文默认语言、中文字体和主菜单；
- 完成新游戏、帮助、存档和读档 smoke，并记录 Windows 版本与 CPU 架构；
- 核对发布说明中的玩家可见变化、支持平台、已知问题、延期项目和准确提交 SHA；
- 核对 Release 仍为 draft，且资产只有 Windows 归档、`SHA256SUMS` 和
  `RELEASE-MANIFEST.txt`，共三项；macOS Actions artifact 不得出现在 Release 中。

自动流程到草稿为止。只有上述人工验收全部有记录，且发布负责人明确批准后，才能在
GitHub 界面公开 Release。若任一项失败，保留草稿和 CI 原始证据，修复后用新的
`0.34.1-zhN` 标签发布；不得移动或复用已经对外分发的标签。

## 本地校验

工具测试会自动发现发布校验器的正例和逐项负向变异：

```bash
python3 .claude/scripts/tests/test_verify_release_artifacts.py
bash .claude/scripts/tests/run_all.sh
```

完整仓库变更仍使用项目统一入口：

```bash
bash .claude/scripts/verify_zh.sh --profile code
```
