# `zh smoke` Pi 分析进度

状态：Pi 第三轮修复已审核；历史开发验证记录均绑定目标基线 `084f8138ab532d193de2ec4a3105da4dfbd61759`，不代表当前候选；当前候选的正式验证由 final gate 负责；immutable readiness / merge authorization 尚未执行
任务：分析 `verify_zh.sh` 的 ZH smoke 失败，区分代码问题、验证脚本问题和运行环境问题。
开始时间：2026-08-01 06:36:30 +08:00
分析截止时间：2026-08-01 07:06:30 +08:00（已完成）
修改开始时间：2026-08-01 07:06:20 +08:00
修改截止时间：2026-08-01 07:36:20 +08:00（30 分钟硬限时）
术语表 SHA-256：`912d85c14b360357303835bce502a2e6661ab629ce350548879c85da8dc0d54e`

## 执行约束

- Pi 仅在明确授权的路径内修改，不运行 Git、不访问凭据。
- 本轮 Pi 仅拥有 `.claude/scripts/smoke_test.sh` 和本进度文档的写入范围；不得修改 `traps.cc`、中文资产、其他验证脚本或构建文件。
- 分析范围：`.claude/scripts/smoke_test.sh`、`.claude/scripts/verify_zh.sh`、`.claude/scripts/post_zh_runtime.sh`、`crawl-ref/source/crawl` 的实际启动路径，以及相关验证日志。
- 不重新打开或修改本次已完成的翻译修复。

## 进度记录

| 时间 | 状态 | 记录 |
|---|---|---|
| 06:36:30 | 已建立任务 | 已冻结 30 分钟截止时间和只读范围，准备交付 Pi。 |
| 06:37:29 | 已交付 Pi | Pi 已启动只读分析；硬截止时间 07:06:30。 |
| 06:38:11 | 分析中 | 首次轮询显示 Pi 仍在运行，尚无阶段性输出或异常。 |
| 06:40:33 | 分析中 | 第二轮轮询：Pi 仍在读取脚本和验证日志，未超时。 |
| 06:43:00 | 分析中 | Pi 已运行约 5 分钟，仍未返回最终报告；距离硬截止时间约 23 分钟。 |
| 06:43:09 | 已完成 | Pi 返回 `STATUS: success`；已完成 smoke 调用链、PTY/headless 对照、同提交成败差异和运行时证据分析。 |
| 07:06:20 | 已交付修改 | 已授权 Pi 实施最小 PTY 修复并同步本文件；新的硬截止时间 07:36:20。 |
| ≤07:36:20 | 实施完成 | Pi 已完成 `smoke_test.sh` 最小 PTY 修复（复用 `run_with_timeout.py --pty-transcript`）并同步本文件；未运行任何 shell 测试，待 Codex 审核与验证。 |
| 07:12:27 | 复验反馈 | Codex 语法检查通过，但 smoke 在 PTY 中暴露 `descriptions.zh.lk` 用户目录权限错误；已反馈 Pi 做第二轮最小隔离修复，硬截止仍为 07:36:20。 |
| 07:13:00 | 第二轮开始 | 复验失败证据明确：PTY 已接通、`language = zh` 已生效（锁文件名含 `.zh`），crawl 返回 1，转录为 `Unable to open lock file ".../saves/db/descriptions.zh.lk": Operation not permitted`。判定为运行目录隔离问题，非代码缺陷。 |
| 07:13:00–07:36:20 | 第二轮分析 | 锁文件由 TextDB 再生创建：`database.cc:382` 以 "wb" 建 `<Options.save_dir>/db/descriptions.zh.lk`（`files.cc:4069-4074`）；`save_dir` 源自 `SysEnv.crawl_dir`（`initfile.cc:1535-1539`），macOS 默认值为 `~/Library/Application Support/Dungeon Crawl Stone Soup`（`initfile.cc:4728-4736`），Codex 沙盒不可写。`CRAWL_DIR` 是文档化环境变量（`initfile.cc:4728`），可整体重定向保存/缓存/锁/尸体/崩溃输出；数据目录由 `files.cc:428-435` 的 rawbases 解析：无 `DATA_DIR_PATH` 的构建中 `SysEnv.crawl_dir` 是首个候选基，`find_crawlrc()` 也先查 `<crawl_dir>/init.txt`（`initfile.cc:2201`）；但当前隔离目录为空，均回退到 `crawl_base`（`files.cc:434`）与 `crawl-ref/source/init.txt`（`datafile_path`，`initfile.cc:2245-2247`），故 `language = zh` 与数据加载不受影响。（按 2026-08-01 08:01 轮更正此路径说明。） |
| ≤07:36:20 | 第二轮实施完成 | 最小隔离修复已写入 `smoke_test.sh`：`mktemp -d` 建临时目录并设置 `CRAWL_DIR`；trap 增加 `rm -rf`；`TIMEOUT_SEC` 10→60（覆盖冷缓存首次 TextDB 全量再生的耗时，124 语义不变）。未运行任何 shell/构建/运行时验证。 |
| 07:24:54 | Codex 历史基线验证通过 | `bash -n`、直接 `bash .claude/scripts/smoke_test.sh` 和 `verify_zh.sh --profile translation` 全部通过；profile Run ID：`20260801T072041257346000+0800-55593-084f8138ab53`，Failures: 0；Run ID 绑定目标基线。 |
| 07:25:49 | Codex 历史基线 code profile 通过 | `verify_zh.sh --profile code` 通过，Failures: 0；Tree-sitter 两个 AST 阶段已实际执行，不再是依赖缺失。Run ID：`20260801T072549403964000+0800-59707-084f8138ab53`，绑定目标基线。 |
| 08:01:00 | 本轮开始 | 按合并前审查 Needs Fix 处理（仅限 `smoke_test.sh`、`traps-translation-handoff.md`、本文件）：① trap 先于 `mv init.txt` 注册并初始化 INIT_BAK/INIT_TMP，mv 失败时清理临时目录但不删除原始 init.txt；② 校正 CRAWL_DIR 的 data/config 搜索路径说明；③ 更新 A4/A7 当前源码行号；④ 本文件历史内容标注；⑤ 两份文档验证状态改为明确区分历史开发验证与当前候选。两个非阻塞 Suggestion 不纳入本轮。 |
| ≤08:10:00（约） | 本轮变更完成 | Pi 返回时未运行 shell/构建/Git/验证脚本；变更明细见下方“实施记录（第三轮）”，随后由 Codex 执行验证。 |
| 08:15:31 | Codex 历史基线验证通过 | `bash -n`、直接 smoke、`git diff --check` 和 `verify_zh.sh --profile translation` 均通过；translation Run ID：`20260801T080923685920000+0800-10085-084f8138ab53`，Failures: 0；Run ID 绑定目标基线。正式 final gate / immutable readiness / merge authorization 仍未执行。 |

## 已知背景（历史分析——第一轮启动时的初始假设，已在后续轮次证实/推翻，保留作审计线索）

- 最新 `verify_zh.sh --profile translation` 的 `ZH smoke` 返回退出码 1。
- 直接运行 Debug `crawl -headless ... -test zh_runtime` 此前通过。
- 当前需判断 smoke 脚本是否使用了不适用于 headless 的裸启动参数，或是否存在真实运行时错误。
  （已解决：裸启动 → PTY；运行目录 → CRAWL_DIR 隔离。）

## Pi 结论摘要（第一轮，历史分析——当时 smoke_test.sh 尚未改用 PTY）

- 根因不是 `traps.cc`、中文 TextDB 或 Crawl 中文运行时；`smoke_test.sh:68-74`（旧行号，修复前裸启动；当前文件该区域已被 init.txt 状态化清理与 PTY 启动替换）以无 PTY 的裸 `crawl` 启动 ncurses，非交互会话中 `initscr()` 失败并返回 1。
- `post_zh_runtime.sh` 的 `-headless -test zh_runtime` 和 PTY bot 路径均通过；同一提交曾出现 smoke 成功/失败分歧，证明问题依赖终端环境。
- `-headless` 单独不是修复，因为 Crawl 要求同时提供 `-test`、`-script`、`-objstat` 或 `-builddb`。
- 最小建议是让 `smoke_test.sh` 使用已有 `run_with_timeout.py --pty-transcript` 路径；当前 PTY 已接通，但复验暴露用户目录锁文件权限问题，第二轮需在不吞掉真实错误的前提下隔离运行目录。
- AST 依赖问题与 ZH smoke 独立；`tree-sitter` 已由 Codex 安装并通过两个 AST 扫描器验证。

## Pi 最终证据文件

- `.claude/scripts/smoke_test.sh` 当前候选的 `cleanup()`、`handle_signal()`、`defer_signal()`、init 状态防护，以及后台 `TIMEOUT_PID` / `--pty-transcript` 启动段（第三轮后的实现证据；不使用历史行号范围）。
- `.claude/scripts/verify_zh.sh:671-692`
- `.claude/scripts/post_zh_runtime.sh:194-196,255-260`
- `.claude/scripts/run_with_timeout.py:60-94,148-165`
- `crawl-ref/source/libunix.cc:838-865`
- `crawl-ref/source/main.cc:522-530`
- 最新失败日志：`.claude/metrics/verify/20260801T002321823424000+0800-14844-5baac99034a0/verify.log:6056-6059`

## Pi 结论摘要（第二轮）

- 锁文件错误是 Codex 沙盒对 `~/Library/Application Support/Dungeon Crawl Stone Soup` 的写限制（`EACCES`），不是 `traps.cc`、中文 TextDB 或 Crawl 运行时缺陷；存在可移植的脚本级修复（`CRAWL_DIR` 隔离），故不构成"放弃修复、仅记录阻塞"的情形。
- 第二轮变更没有吞掉锁文件错误：锁文件仍在 TextDB 再生路径中被真实创建（`database.cc:382`），只是落到可写的隔离目录；真实非 0/124 子进程退出仍由当前脚本的 `CHILD_RC` 检查失败；PTY 转录仍写 `ZH_OUT`；协议/英文残留/崩溃三段扫描逻辑未改动。
- 第一轮 PTY 修复（`--pty-transcript`）保持有效；第二轮新增 `CRAWL_DIR` 隔离是叠加的、正交的最小修复。

## 实施记录（Pi 第二轮最小修复）

范围：仅修改 `.claude/scripts/smoke_test.sh` 与本文档；未触碰 `traps.cc`、中文 TextDB/翻译资产、`verify_zh.sh`、`post_zh_runtime.sh`、`run_with_timeout.py`、构建文件或 Git 状态。

第二轮实际变更（`.claude/scripts/smoke_test.sh`；以下行号是历史记录，不作为当前候选锚点）：
- 行 34：`TIMEOUT_SEC` 10→60。冷缓存下 crawl 首次启动会在隔离目录中全量再生全部父 TextDB 及其 zh 子库（`database.cc:355-405`），Debug 二进制更慢；60 秒仍是有界超时，124 契约（终止子进程组、转录仍被扫描）不变。
- `mktemp -d /tmp/crawl_smoke_dir.XXXXXX` 创建隔离目录 `$SMOKE_CRAWL_DIR`；创建失败则退出码 2（与二进制/helper 缺失同约定）。
- cleanup 执行 `rm -rf "$SMOKE_CRAWL_DIR"`、`$ZH_OUT` 清理、init.txt 恢复（后续实现已把 trap 提前到临时目录创建前，并受 INIT_BAK/INIT_TMP 状态约束）。
- 启动命令增加 `CRAWL_DIR="$SMOKE_CRAWL_DIR"` 环境变量（文档化机制，`initfile.cc:4728`），仅作用于 crawl 子进程。
- 未修改 `run_with_timeout.py`、PTY 转录目标 `$ZH_OUT`、退出码语义（0/124 可接受、其余失败）、三段扫描逻辑。

## 实施记录（第三轮：2026-08-01 08:01 合并前审查 Needs Fix）

范围：仅修改 `.claude/scripts/smoke_test.sh`、`traps-translation-handoff.md`、`zh-smoke-pi-progress.md`；未触碰 `traps.cc`、`describe.cc`、中文 TextDB/翻译资产、测试代码、`verify_zh.sh`、`post_zh_runtime.sh`、`run_with_timeout.py`、构建文件或 Git 状态。两个非阻塞 Suggestion 未纳入本轮。

`smoke_test.sh`：
- 行 57-63：CRAWL_DIR 路径说明校正——无 `DATA_DIR_PATH` 构建中 crawl_dir 也参与 config/data 搜索（`find_crawlrc()` 先查 `<crawl_dir>/init.txt`，`initfile.cc:2201`；rawbases 首项 `SysEnv.crawl_dir`，`files.cc:433`），但空临时目录会回退到 crawl_base / 源 init.txt（`datafile_path`，`initfile.cc:2245-2247`）；已通过的运行逻辑未改变。
- 初始化与 cleanup 段：统一 cleanup 函数在创建临时目录前注册，并同时处理 `EXIT`、`INT`、`TERM`、`HUP`；新增 `INIT_TMP` 状态（在临时 `language = zh` init.txt 写入前置位），因此正常退出、显式失败和信号中断都会清理部分文件并恢复备份。
- 备份路径防护：`mv init.txt .init.txt.smoke-bak` 前无条件检查既有备份路径（包括符号链接）并 fail closed，因此不会覆盖或误恢复上次中断遗留的备份。
- init 路径防护：仅允许缺失的 init.txt 或普通非符号链接文件；目录、特殊文件和所有符号链接均拒绝，避免重定向跟随外部目标。mv 失败时原始 init.txt 保持不动。
- timeout runner 在后台运行并由 `TIMEOUT_PID` 跟踪；启动窗口用挂起信号记录避免 PID arm race；收到 `INT`、`TERM`、`HUP` 时先转发信号、等待 helper 的进程组终止宽限并 reap runner，再执行 cleanup，保留 130/143/129 退出码，避免子进程和临时目录脱离控制。cleanup 对关键恢复/删除失败返回非零，不再静默吞错。

`traps-translation-handoff.md`：
- A4 证据行更新为当前代码 `traps.cc:738,740`（完整句子键，`zh/source.txt:7299-7303`）。
- A7 证据行更新为当前代码 `traps.cc:1038-1040`（`zh/source.txt:40509-40510`，已无“处”）。
- 状态行改为明确说明历史开发验证绑定目标基线，当前候选的正式验证由 final gate 负责。

`zh-smoke-pi-progress.md`（本文件）：
- 状态行与“验证状态”改为明确区分历史开发验证与当前候选，避免把目标基线结果绑定到当前候选。
- “已知背景 / Pi 结论摘要（第一轮）”标注为历史分析；CRAWL_DIR 数据搜索说明按 `files.cc:428-435` 更正。

Pi 返回时未运行的验证：`bash -n .claude/scripts/smoke_test.sh`、直接 smoke、`verify_zh.sh --profile code|translation`、构建和 Git；随后 Codex 在目标基线上执行了 `bash -n`、直接 smoke、`git diff --check` 和 `verify_zh.sh --profile translation`，均通过；`profile code` 的前次开发验证也绑定目标基线。上述均为历史开发验证，不代表当前候选；正式 final gate / immutable readiness / merge authorization 尚未执行。

验证状态：**历史开发验证已记录并绑定目标基线；当前候选的正式验证由 final gate 负责**。历史 `bash -n .claude/scripts/smoke_test.sh`、直接 smoke、translation profile 与 code profile 均通过，Failures: 0；Tree-sitter AST 两阶段已实际执行并通过。以上不构成当前候选的通过证据，也不等同于正式 final gate / immutable readiness / merge authorization。

Pi 修改完成后必须列出实际变更行和未运行的验证；Codex 已完成 diff 审核、smoke、翻译 profile 和静态检查；以上均为开发期验证，不构成正式 final gate 或合并授权。

## 后续合并前审查加固

- `smoke_test.sh` 的初始化、信号转发、runner 回收、备份恢复和临时工件清理按同一状态机处理；`INT`、`TERM`、`HUP` 均覆盖，忽略信号的非终止 child 也由 timeout helper 的进程组终止流程回收。
- `.claude/scripts/tests/test_smoke_test.sh` 增加特殊路径矩阵、缺失 init + 残留备份、三种信号、重复信号、非终止 child、子进程终止、具体信号转发、`init.txt` 恢复、transcript 和 `CRAWL_DIR` 删除断言；最新本地结果为 `35 passed, 0 failed`。
- 以上为开发期与定向回归证据；当前候选仍须经过 immutable readiness、final gate 和 merge-time validation。

## 最终交付

Pi 已返回逐项变更、根因对应关系和未运行的验证；Codex 已补写进度终点、审核结论和开发期验证结果。正式 final gate / immutable readiness / merge authorization 尚未执行。
