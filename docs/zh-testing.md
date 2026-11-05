# Chinese Translation Verification

## Development Profiles

Use focused existing checks during development, then one profile matching the
coherent change when it affects translation, game code, or verification tools:

```bash
bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh --profile translation
bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh --profile code
bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh --profile ci
```

`translation` and `code` default to changed scope. Without a bound range, they
inspect only changes relative to HEAD, including untracked files. A clean
worktree does not mean the last commit has been verified. For a committed
candidate, use the matching profile with an explicit range, for example:

```bash
bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh \
  --profile code --base <base> --head <candidate>
```

The bound candidate must be checked out and clean. Do not discard unrelated
work to meet that condition. Reuse earlier verification if the tested content
and relevant dependencies are unchanged; record the scope covered by the evidence.

| Task | Local verification |
|---|---|
| Read-only review | Inspect scope and existing logs; targeted checks only to resolve concrete uncertainty |
| Policy/docs only | Existing documentation, configuration, and sync checks; no game build |
| Verification tooling | Relevant regression tests and `code` profile |
| Translated assets | `translation` profile, preserving global key/structure integrity |
| C++/i18n | `code` profile and affected target/runtime checks selected by risk |
| Mixed assets and code | `code` profile plus focused translation checks; use `ci` instead when combined full static preflight is needed, with runtime checks separately if required |

Known governance-only changes skip game static and overlay phases in local
changed mode. Relevant source/data and validator dependencies retain global
integrity checks; overlay dependencies select the heavy overlay suite. Unknown
paths are conservative. `ci` and full scope retain their full static coverage.
Skipping unrelated phases does not verify the changed tool: run its focused
tests. Read current options from `verify_zh.sh --help`.

The miscname exact-candidate integration test needs committed inputs. A dirty,
unbound changed run explicitly skips that case while exercising its fixture
regressions; bound and CI/full runs retain the clean-candidate check. Report
the skip as unavailable candidate evidence, not a successful integration run.

Agents that write or review verification controls follow
`.agents/policies/verification-authoring.md` for coverage proportional to the
tool's claimed guarantees, realistic fixtures, and blocking versus advisory
behavior. No new end-to-end test is needed when existing coverage is sufficient.

The report is written below `.claude/metrics/verify/`. Agents report the exact
command, exit code, blocking failure count, and relevant warnings rather than
only saying that verification “passed”.

## Runtime Evidence

The runtime suite combines:

- Catch2 translation and message-overlay checks;
- dlua translation/database smoke tests, including ZH canonical-English
  identity assertions for the five protocol-facing `you.*` bindings;
- RC bot UI and gameplay workflows;
- aggregation against version-controlled baselines.

The identity runtime case also constructs the named
`heliophobic_arrival_battle_scene` arrival vault through the production Vault
path; it fails if the vault cannot be found or placed, rather than claiming
coverage from a parser-only check. Use `.claude/scripts/post_zh_runtime.sh --help` and `.claude/scripts/TOOLCHAIN.md`
for current modes and artifact locations. Avoid
hard-coded test/assertion/marker counts in prose because the suites evolve.

A newly created linked worktree has empty directories for recorded contrib
submodules. Before a build or a check that needs contrib dependencies,
initialize its exact gitlinks and confirm the superproject remains clean:

```bash
git submodule update --init --recursive
git status --porcelain=v1 --untracked-files=all
```

Submodule initialization is environment preparation, not candidate content.

## 实际游玩测试与验收修复建议

本节供后续维护和候选验收按改动风险选用，不要求每次任务都委派测试或开展长局，
也不增加审批、验证 profile 或问题跟踪系统。构建和脚本检查提供自动验证证据，
实际游玩补充操作、动态文本及布局证据，发布验收关注最终下载包；记录各自覆盖范围，
避免把一种证据推定为另一种验收通过。正式发布仍遵循
[发布工作流](release-workflow.md)。

### 先明确测试对象与可用设备

建议在测试记录中注明源码提交、分支或标签、构建来源、运行前端、操作系统与 CPU 架构；正式
包另记文件名和 SHA-256。稳定版与 trunk 分开记录，不能把一个候选的问题或通过结论
直接归给另一个。没有连接 Android 设备时，明确写“Android 真机未测”；Linux 本机
游玩、Android 构建成功和 APK 签名有效分别说明各自覆盖范围。

如需并行游玩，宜给测试代理分配独立角色、存档和日志位置，防止互相覆盖；通常可让
测试者先报告，由负责相应源文件的实现者集中修复。授权委派与运行时工具以当前会话为准，角色路由见
[agent-routing.md](agent-routing.md)。

### 用玩法事件规划深度，不只累计运行时间

| 路线 | 建议实际触达的事件 | 要观察的输出 |
| --- | --- | --- |
| 共用起步 | 启动、建角、帮助、拾取、装备、探索、战斗、换层 | 默认中文、名称、确认提示、操作与结果是否一致 |
| 近战与状态 | 正常战斗中产生状态、状态恢复、使用神力及效果结束 | 来源、时态、所有格、程度变化和动态名称拼接 |
| 施法与能力 | 查看技能、学习与施放法术、使用能力、资源不足或目标不可用 | 菜单、快捷入口、禁用原因、目标提示和效果说明 |
| 界面与输入 | 长名称、长帮助、小终端；有设备时测试触摸、滚动、横屏与软键盘 | 中文截断、换行、末项可达性、焦点与按键是否匹配 |
| 持久化 | 保存退出、重新启动、读档后继续操作 | 角色、位置、装备和游戏进度保留，中文仍正常 |

上表是可选路线，不是每轮都要完成的清单。局部修复可聚焦原场景及相邻分支；涉及
广泛动态文本时，可安排正常模式长局，逐步触达新的玩法事件。长局前先试一次保存
重载有助于保留复现条件。死亡、自然结束或达到约定范围时，记录已覆盖事件、结束
原因及尚未触达的场景，未触达项保持未测。

固定种子有助于复现地图，还应尽量保留触发前的存档和关键操作。必要时可用 wizard、
测试脚本或构造状态补充罕见分支，单独标明其用途，不能计作正常模式的自然游玩。
记录现实耗时、游戏显示时间和回合数时保留各自单位，不互相换算成未经核实的数字。

### 发现问题时保留最小可复现记录

建议复用当前任务的 Issue 与本地验证日志，按问题需要记录以下信息；暂缺存档或截图
不妨碍先报告，但应注明复现限制：

- 候选版本、平台和前端，以及种子、触发前存档或必要的角色状态；
- 关键操作、实际显示的完整文本和截图或终端捕获；
- 可复现程度、影响、预期行为及其依据；没有核实的解释标为待核实；
- 所属场景、后续修复 PR，以及原场景复测结果。

终端捕获可帮助检索文本；字体、字形、视觉对齐和触摸命中还需要相应画面或实际
设备证据。记录漏译、混排、语序、术语和显示问题时，先完整保留输出，之后再追踪
源消息、查询键与动态参数。一次实测发现不等于近期提交引入；归因需要基线对照。
分类及阻断级别复用 [review-contract.md](../.agents/policies/review-contract.md)。

### 从实测发现到修复关闭

1. 核实版本与复现条件，合并同根因的重复报告，区分文本错误、代码输出错误、打包
   错误和测试环境问题；保留尚不能复现的项目及其证据缺口。
2. 依照 [agent-routing.md](agent-routing.md) 分配翻译、代码和审阅责任；涉及术语或
   翻译判断时先解析当前上下文。端到端翻译问题使用现有 translation-pipeline skill，
   不因报告来自实测就跳过资产所有权和协议／显示边界检查。
3. 修复真实输出入口，核对动态参数、来源差异及相邻分支；需要回归测试时，覆盖
   玩家确实触发过的生产路径，而不只测试一个改写后的字符串。
4. 使用本文件规定的单一匹配 profile 和必要的聚焦检查，对已提交候选绑定准确
   `--base`、`--head`；按风险完成领域审核及适用 CI，再按既有授权交付。
5. 条件允许时，用修复后的候选重走原始触发步骤，按风险检查紧邻的正常／异常或
   不同来源分支。
   若脚本通过但尚未重现玩家场景，分别记录“自动回归通过”和“原场景待复测”。

开发候选的游玩证据可在相关代码与依赖未变时复用，但不替代最终下载包的版本、
校验值、数据完整性与启动验收。最终包验收清单及各平台覆盖状态放在 release issue，
详见 [发布工作流](release-workflow.md)。

例如，稳定版与 trunk 分开进行的本机游玩为
[稳定版长局修复 PR #179](https://github.com/yutio8888/crawl-chn-ai-test/pull/179)
提供了翻译与显示问题的实际场景；
[PR #180](https://github.com/yutio8888/crawl-chn-ai-test/pull/180) 新增字符版分发后，
又需要检查最终包及其前端。后续结果和覆盖缺口继续记录在对应
[发布 Issue](https://github.com/yutio8888/crawl-chn-ai-test/issues/181)，不在本文复制进度表。

## Domain Review and Merge

Before pushing source changes, run the local checks from the `Code Linting`
job in [ci.yml](../.github/workflows/ci.yml) against the complete changed-file
range intended for the PR. This includes `util/checkwhite -n` and, for changed
C++ files, `util/unbrace -n`, run from `crawl-ref/source`. Fix any findings and
rerun the affected checks before pushing, so formatting errors do not consume
another full GitHub Actions run. Keep the workflow authoritative for file
selection and commands; local lint does not replace the matching verification
profile or required CI.

Ordinary review accepts existing files or uncommitted changes and reports
findings plus Validation Gaps. It does not require a build, commit, or remote
comment. For an authorized merge:

1. commit the candidate and require a clean worktree;
2. verify the matching profile with `--base <base> --head <candidate>`, or reuse
   valid evidence for unchanged content and dependencies;
3. route reviewers with
   `python3 .claude/scripts/classify_reviewers.py --base <target> --head <candidate>`
   and apply the routed domains, inline when delegation is unavailable or unnecessary;
4. reviewers report findings, Validation Gaps, and Ready or Changes Requested;
   post to the PR/issue only when authorized;
5. applicable GitHub Actions CI (`.github/workflows/ci.yml`) must pass; use the
   existing PR or manual workflow, since a task branch alone does not trigger CI;
6. merge from the target checkout.

The complete review contract is `.agents/policies/review-contract.md`. There is
no separate final evidence gate, immutable bundle, readiness object, or local
merge authorization. Expired one-time recovery records remain available in the
non-authorizing [review recovery archive](review-recovery-history.md).

Verification is not restarted solely because the task advances to review or
delivery. New changes, failures, or missing evidence justify additional checks.
Task completion and cleanup follow `AGENTS.md`; do not apply release gates to
ordinary development.

## CI

The current CI definition is `.github/workflows/ci.yml`; it is authoritative
for job names and commands. Agent documentation should link to it instead of
copying job inventories that drift.

CI event routing, runner matrices, and commands are defined in
[ci.yml](../.github/workflows/ci.yml). Generic verification scripts support
macOS system `/bin/bash` (Bash 3.2) and BSD userland; target-specific helpers
use the dependencies documented by their build workflow.

The exact Python version is defined once by the root `.python-version` file.
Local tooling commands should run through a version manager that honors it (or
otherwise verify `python3 --version` matches it); CI's setup-python steps read
the same file.
