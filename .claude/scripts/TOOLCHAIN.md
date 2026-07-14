# 翻译工具链使用说明

项目 `.claude/scripts/` 下有多个脚本覆盖翻译质量保障的完整链路。所有脚本从仓库根目录运行。

## 架构概览

```
Agent 生成修改 → verify_zh.sh --profile <type>  (单入口调度器)
        │
        ├─ translation  → post-translator.sh
        ├─ code         → post-coder.sh
        └─ review       → post-reviewer.sh
                                    ↓
                  ┌──────────────────────────────────────────┐
                   │  scan_i18n.py (子命令集)                  │
                   │  i18n_extract.py (4 子命令)               │
                   │  audit_data_i18n.py (数据驱动覆盖)        │
                   │  source_control_parity.py (控制符奇偶)    │
                   │  check_consistency.sh (7 模式)             │
                   │  cross_file_terms.py                      │
                   │  zh_runtime_check.py (运行时聚合)         │
                   │  smoke_test.sh                            │
                   │  check_checkpoint.sh                      │
                   │  record_review.sh                         │
                  └──────────────────────────────────────────┘

Parser (统一):
  i18n_shared.py — 唯一 source.txt 解析器（Entry dataclass）
  所有脚本通过 i18n_shared.parse_entries() / parse_source_txt() 解析
```

## 快速参考

| 需求 | 命令 |
|------|------|
| **翻译/数据改动验证** | `bash .claude/scripts/verify_zh.sh --profile translation` |
| **C++/i18n 改动验证** | `bash .claude/scripts/verify_zh.sh --profile code` |
| **合并前审查** | `bash .claude/scripts/verify_zh.sh --profile review` |
| **CI 门禁** | `bash .claude/scripts/verify_zh.sh --profile ci` |
| **生成 Agent 术语上下文** | `python3 .claude/scripts/glossary_query.py --task "<任务>" --files <文件>` |
| **检查本次修改的精确术语键** | `python3 .claude/scripts/check_glossary_terms.py --base HEAD` |
| **检查持久化 T_()/C_() 指针** | `python3 .claude/scripts/scan_i18n_lifetime.py crawl-ref/source/ --require-parser` |
| **T_() 键验证** | `python3 .claude/scripts/i18n_extract.py validate crawl-ref/source/ --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **数据驱动翻译覆盖** | `python3 .claude/scripts/audit_data_i18n.py crawl-ref/source/ --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **source.txt 完整性** | `python3 .claude/scripts/scan_i18n.py source-txt-integrity --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **发现未翻译消息** | `python3 .claude/scripts/scan_i18n.py missing-t crawl-ref/source/` |
| **mprf_p 兼容性** | `python3 .claude/scripts/scan_i18n.py mprf-p crawl-ref/source/ --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **%s 数量一致** | `python3 .claude/scripts/scan_i18n.py arg-mismatch --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **控制符奇偶检查** | `python3 .claude/scripts/source_control_parity.py --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **运行时冒烟测试** | `bash .claude/scripts/smoke_test.sh` |
| **运行时回归检查** | `bash .claude/scripts/post_zh_runtime.sh catch2` |
| **运行测试** | `bash .claude/scripts/tests/run_all.sh` |

## 脚本详解

### glossary_query.py — 当前术语表上下文

`docs/glossary.md` 是唯一术语数据源。Agent、Skill 和编排器在翻译、i18n
实现或审核开始前调用本脚本，根据任务说明、文件路径和明确词条选择相关
domain，并输出术语表 SHA-256。输出可直接附加到 Agent prompt：

```bash
python3 .claude/scripts/glossary_query.py \
    --task "翻译 broad axe" \
    --files crawl-ref/source/dat/i18n/zh/source.txt

# 需要精确词条或机器读取时
python3 .claude/scripts/glossary_query.py --term cast --format json
```

不要把脚本输出复制回 Agent/Skill 形成静态术语副本；每次任务重新查询，
才能使用当前 worktree 的最新术语表。`context_resolve.sh` 已统一调用本脚本。

### check_glossary_terms.py — 增量精确键门禁

读取由 `docs/glossary.md` 导出的 OmegaT `docs/glossary.utf8`，检查
`source.txt` 中“英文 key 与术语 source 完全相同”的本次改动。多个批准译法
均可通过；未批准后缀也会失败（例如术语为“召回”时，“召回术”不视为匹配）。

```bash
# 默认只检查相对 HEAD 新增或改动的条目（已接入三个 post-* 入口）
python3 .claude/scripts/check_glossary_terms.py

# 合并前指定比较基线
GLOSSARY_DIFF_BASE=base python3 .claude/scripts/check_glossary_terms.py --base base

# 历史全量审计；可能包含尚未清理的旧漂移，不作为默认门禁
python3 .claude/scripts/check_glossary_terms.py --all
```

门禁前先运行 `export_omegat_glossary.py --check`，确保 OmegaT 导出与 Markdown
源一致。该检查已接入 `post-translator.sh`、`post-coder.sh` 和
`post-reviewer.sh`。

### i18n_extract.py — T_() 键提取与验证

从 C++ 和 Lua 源码中提取所有 `T_("...")`、`C_("ctx", "...")` 和 `crawl.t_("...")` 字面量调用，与 source.txt 对比。

**已知限制**：只匹配 `T_("字面字符串")`，不匹配 `T_(变量)`。以下场景会遗漏：
- `duration-data.h`: endmsg/expmsg → `T_(endmsg)` at runtime
- `mon-util.cc`: 怪物名 → `T_(en.c_str())` at runtime
- `dat/mons/*.yaml`: 怪物名定义（非 .cc/.h 文件）

这些场景由 `audit_data_i18n.py` 补充扫描。

```bash
python3 .claude/scripts/i18n_extract.py extract crawl-ref/source/        # 提取所有 T_() 键
python3 .claude/scripts/i18n_extract.py validate crawl-ref/source/ \     # 验证覆盖率（CI 阻断）
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt
python3 .claude/scripts/i18n_extract.py missing crawl-ref/source/ \      # 生成缺失键存根
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt
python3 .claude/scripts/i18n_extract.py stale crawl-ref/source/ \        # 查找死条目
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt
```

### scan_i18n.py — T_() 世界盲区扫描

替代旧的 `scan_untranslated.sh`。子命令：

```bash
# missing-t: 未翻译的 mprf/mpr 调用（宽泛启发式，供人工审计）
python3 .claude/scripts/scan_i18n.py missing-t crawl-ref/source/

# 高置信显示契约（code/review profile 阻断）
# direct sinks 的顶层字面量必须包 T_()/C_()；动态 wrapper 字面量必须有 key
python3 .claude/scripts/scan_i18n.py missing-t crawl-ref/source/ \
    --display-contracts-only \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# mprf-p: 位置参数（%n$s）必须用 mprf_p 而非 mprf（MinGW 兼容）
python3 .claude/scripts/scan_i18n.py mprf-p crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# source-txt-integrity: 重复 key、自冲突、空译文检查
python3 .claude/scripts/scan_i18n.py source-txt-integrity \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# arg-mismatch: EN key 和 CN 翻译的 %s 数量一致性
python3 .claude/scripts/scan_i18n.py arg-mismatch \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# check-gaps: 位置参数编号间隙检测
python3 .claude/scripts/scan_i18n.py check-gaps \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# validate-terms: 检查 decisions.md 中被拒绝的术语
python3 .claude/scripts/scan_i18n.py validate-terms \
    --glossary docs/decisions.md \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# anti-patterns: 检测已知 Agent 错误模式
python3 .claude/scripts/scan_i18n.py anti-patterns crawl-ref/source/ --strict

# lang-args: 检测 T_() 中语言依赖参数（启发式，始终 exit 0）
python3 .claude/scripts/scan_i18n.py lang-args crawl-ref/source/

# 物种/怪物一致性子命令（已纳入 post-coder.sh）
python3 .claude/scripts/scan_i18n.py species-consistency \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt
python3 .claude/scripts/scan_i18n.py monster-compound-consistency \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt
python3 .claude/scripts/scan_i18n.py monster-dbkey-consistency crawl-ref/source/
python3 .claude/scripts/scan_i18n.py monster-name-assembly crawl-ref/source/mon-info.cc
python3 .claude/scripts/scan_i18n.py monster-title-display \
    crawl-ref/source/directn.cc crawl-ref/source/tileweb.cc
```

显示契约的 sink 与动态 key wrapper 统一声明在 `scan_i18n.py` 顶部元数据中。
扫描器使用 Python 标准库的轻量 C++ 词法解析，不依赖 tree-sitter，因此最小 CI
环境与开发机行为一致。变量参数和 DB/provider 返回值不会按字面量猜测。当前生产
扫描为零债务门禁，不使用 baseline；任何新 `DISPLAY`/`DYNKEY` 候选都会直接阻断。
扫描器仍保留精确 `--allowlist` 能力，仅供未来受控迁移，豁免必须精确匹配 rule、
文件、行号、函数和完整字面量。

### scan_i18n_lifetime.py — 持久翻译指针生命周期门禁

`T_()`/`C_()` 返回 i18n 缓存中的借用指针；清空缓存后，保存在函数静态、
成员或持久容器中的裸 `const char*` 会悬空。扫描器报告：

- `LIFE001`–`LIFE003`：阻断，分别覆盖静态 raw sink、持久成员赋值和容器写入；
- `LIFE101`：非阻断，命名空间 raw 指针在启动期固化语言；
- `LIFE102`：非阻断，持久 owning string 固化首次翻译；
- `LIFE103`：非阻断，类型或 helper 无法可靠解析。

```bash
# 默认只输出并阻断 HIGH
python3 .claude/scripts/scan_i18n_lifetime.py crawl-ref/source/ --require-parser

# 人工审计时同时显示 WARN
python3 .claude/scripts/scan_i18n_lifetime.py crawl-ref/source/ \
    --include-warn --format json --require-parser

# 单元测试（同时覆盖小型 AST 与大型词法路径）
python3 .claude/scripts/tests/test_scan_i18n_lifetime.py
```

实现对小型目标使用 tree-sitter AST，对大型/完整仓库使用屏蔽注释与字面量的
词法候选切片，避免旧 binding 在超大 C++ initializer 上的 native 崩溃。两条路径
都检查 helper、聚合字段、成员赋值、容器 mutation、延迟 lambda 与立即调用
lambda。解析器缺失、输入无效或严格目标解析失败均退出 2；CI 以 fail-closed 运行。

修复时让持久表只保存稳定英文 key，在消费点调用 `T_()`/`C_()` 并立即复制；
同一英文 key 需要不同译文时必须使用 `C_()` 的 context，不能覆盖全局译文。

### audit_data_i18n.py — 数据驱动翻译覆盖检查

`i18n_extract.py` 只能检测 `T_("字面量")`。本脚本补充扫描三类运行时变量调用：

| 扫描源 | 数据文件 | 运行时路径 |
|--------|----------|-----------|
| **怪物名** | `dat/mons/*.yaml` | `mon-util.cc:5957` → `T_(en.c_str())` + `zh_monster_name()` 静态 map |
| **Duration 消息** | `duration-data.h` | `player-reacts.cc:180` → `T_(endmsg)`、`T_(expmsg)` |
| **Feature 名** | `feature-data.h` | `directn.cc:3138` → `T_(get_feature_def().name)` |

```bash
# 检查怪物名、duration、feature 覆盖情况
python3 .claude/scripts/audit_data_i18n.py crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt
```

怪物名同时检查 source.txt 和 `zh_monster_name()` 静态 map 两层回退。

### check_consistency.sh — 数据库完整性

7 种模式。添加 `--strict` 使脚本在发现违规时 exit 1（CI 阻断）。

```bash
bash .claude/scripts/check_consistency.sh --all --strict   # 全部检查
bash .claude/scripts/check_consistency.sh --rulings         # decisions.md 废弃译名
bash .claude/scripts/check_consistency.sh --gods            # 28 位神祇名完整性
bash .claude/scripts/check_consistency.sh --skills          # 14 个技能学派
bash .claude/scripts/check_consistency.sh --format          # %%%% 分隔符数量
bash .claude/scripts/check_consistency.sh --spells          # 法术键完整性
bash .claude/scripts/check_consistency.sh --database        # @keyword@ 引用完整性
```

### cross_file_terms.py — 跨文件术语一致性

扫描 `i18n/zh/` 下所有 `.txt` 文件，检测：
1. 同一 EN key 在不同文件中翻译不同
2. decisions.md 中被拒绝的术语

```bash
python3 .claude/scripts/cross_file_terms.py crawl-ref/source/dat/i18n/zh/ \
    --glossary docs/decisions.md
```

### smoke_test.sh — 运行时冒烟测试

启动 ZH 模式 crawl，检查启动输出中的致命问题：
1. 协议泄露（.des 标签、Lua 标识符）
2. 英文残留（核心 UI 标签未翻译）
3. 崩溃（segfault、assertion）

```bash
bash .claude/scripts/smoke_test.sh
```

### source_control_parity.py — 控制符奇偶检查

检查 source.txt 中英文 key 中的字面控制字符（`\n`、`\t`、`\r`）数量是否与中文翻译保持一致。
`\n` 缺失会导致 Tiles 渲染器中出现过长的行并被截断。

```bash
# \n 不匹配 → 阻断（退出码 1）；\t/\r 不匹配 → 警告（退出码 0）
python3 .claude/scripts/source_control_parity.py \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# 使 \t 和 \r 也变为阻断
python3 .claude/scripts/source_control_parity.py \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt --strict-all
```

**豁免机制**：由于中文句式重组导致合法 `\n` 数量不同的条目，可通过独立豁免文件排除。
默认读取脚本同目录下的 `source-control-parity-exemptions.txt`，格式为每行一个 EN key 行号：

```text
L2619   # Attack monsters: 3→2 \n — CN 单行合并
L24196  # Table legend (kills): 13→10 \n — CJK 宽度软换行移除
```

也可通过 `--exempt-lines <file>` 指定自定义豁免文件。

**正确解析**：正确处理 `\\` 转义（`\\n` 不计为控制字符），区分字面 `\n` 与转义序列。
**跳过空条目**：空中文译文会被标记为缺失所有控制字符。

已接入所有三个 `post-*.sh` 聚合脚本（均为阻断 gate）。

```bash
# 带自定义豁免文件的完整检查
python3 .claude/scripts/source_control_parity.py \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt \
    --exempt-lines source-control-parity-exemptions.txt

# 严格模式：所有控制字符均为阻断
python3 .claude/scripts/source_control_parity.py \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt --strict-all
```

### scan_translation_length.py — 翻译段落长度风险扫描

按 Unicode East Asian Width 估算中文译文的显示列数，逐段检查显式 `\\n`
之间的文本。默认 `>=48` 列报告警告，`>=56` 列报告高风险；这是提示性
扫描，不是阻断 gate，因为实际宽度还取决于字体、窗口和 UI 控件。

```bash
python3 .claude/scripts/scan_translation_length.py \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt
```

需要将高风险作为 CI 失败时，可追加 `--fail-on-risk`；建议先人工筛选后
添加 `\\n`，不要直接把所有报告项机械换行。

### scan_varargs_string.py — 可变参数 std::string UB 扫描（Issue #42 类）

基于 tree-sitter 的 AST 扫描器，检测把 `std::string`（而非 `const char*`）作为
`%s` 实参传给 printf 风格可变参数函数（`make_stringf`/`mprf`/`mprf_p`/`die` 等）。
这是未定义行为：`va_arg(ap, const char*)` 读取 `std::string` 对象前 8 字节（SSO
缓冲/data 指针）当作 `char*` → 运行时乱码/控制字符。编译器 `-Wformat` 对类临时对象
不可靠，故需此静态门禁。

```bash
# 阻断扫描（仅 HIGH）— 已接入 post-coder.sh
python3 .claude/scripts/scan_varargs_string.py crawl-ref/source/

# 含建议级 WARN（裸函数调用实参，需人工确认返回类型）
python3 .claude/scripts/scan_varargs_string.py crawl-ref/source/ --include-warn

# 指定文件 / JSON / CI 强制
python3 .claude/scripts/scan_varargs_string.py --files prompt.cc,describe.cc
python3 .claude/scripts/scan_varargs_string.py crawl-ref/source/ --format json --require-parser
```

规则：`STRING_CTOR`/`CONCAT`/`TERNARY` 为 **HIGH（阻断）**，`CALL_NO_CSTR` 为
**WARN**。修复：先构造 `std::string` 局部变量再传 `.c_str()`；三元 `cond ? string(a) : ""`
会把两个分支都提升为 `std::string`。依赖 `pip3 install tree-sitter tree-sitter-cpp`。

### 编排者工具

```bash
# check_checkpoint.sh: 检查 ORCHESTRATION_STATE.md 是否过期
#   退出码: 0=当前, 2=落后1-5个commit, 3=落后6+个commit
bash .claude/scripts/check_checkpoint.sh

# record_review.sh: 记录 review 指标到 review-log.jsonl
bash .claude/scripts/record_review.sh '{"date":"...","agent_type":"...","findings":{...}}'

# context_resolve.sh: 为 Agent 调度生成精简上下文
CONTEXT=$(bash .claude/scripts/context_resolve.sh "translate god descriptions" \
    --files dat/database/zh/godspeak.txt)
```

### verify_zh.sh — 单入口验证调度器

Agent 每次只需运行一个与改动类型匹配的命令，无需记忆脚本列表。

```bash
# 翻译/数据文件改动
bash .claude/scripts/verify_zh.sh --profile translation

# C++/i18n 代码改动
bash .claude/scripts/verify_zh.sh --profile code

# 合并前审查
bash .claude/scripts/verify_zh.sh --profile review

# CI 门禁（translation + code 并集）
bash .claude/scripts/verify_zh.sh --profile ci
```

每个 profile 运行 core-static 检查（始终阻断）加上领域特定检查。
报告写入 `.claude/metrics/verify/verify-<profile>-<timestamp>.log`。

底层仍保留 `post-coder.sh`、`post-translator.sh`、`post-reviewer.sh`，
但它们通过 `verify_zh.sh` 统一调度。

### post_zh_runtime.sh — 运行时测试与基线回归

三层运行时测试，支持多种模式：

```bash
# catch2: 构建 catch2-tests + 运行 [zh-translation] + 基线对比（秒级）
bash .claude/scripts/post_zh_runtime.sh catch2

# full: Layer 1 (Catch2) + Layer 2 (Lua) + Layer 3 (RC Bot)（分钟级）
bash .claude/scripts/post_zh_runtime.sh full

# fast: 仅聚合已有日志（无构建）
bash .claude/scripts/post_zh_runtime.sh fast

# baseline: full 运行 + 写入新基线到 test/baselines/zh/
bash .claude/scripts/post_zh_runtime.sh baseline

# help-full: Issue 52 帮助系统全量测试（[zh-help] catch2 + zh_help.rc bot）
bash .claude/scripts/post_zh_runtime.sh help-full

# help-baseline: 帮助系统全量 + 写入基线到 test/baselines/zh-help/
bash .claude/scripts/post_zh_runtime.sh help-baseline
```

聚合脚本 `zh_runtime_check.py` 支持 `--mode default`（三层 i18n 扫描）和
`--mode help`（帮助系统状态标记）。

### 运行时基线（版本控制）

基线文件位于版本控制中：
```
test/baselines/zh/zh-baseline.json           # [zh-translation] 三层基线
test/baselines/zh-help/zh-help-baseline.json  # [zh-help] 帮助系统基线
```

运行 `post_zh_runtime.sh baseline` 或 `help-baseline` 更新基线后，
需 review diff 并提交。CI 始终对比版本控制中的固定基线，干净 CI runner
也能可靠做回归检测。

### CI 分层

GitHub Actions 中 4 个 zh-specific job：

| Job | 触发 | 需编译 | 说明 |
|-----|------|--------|------|
| `zh_tooling_tests` | push/PR | 否 | `run_all.sh`（12 个 Python 测试） |
| `zh_ci_gate` | push/PR | 否 | `verify_zh.sh --profile ci`（code + translation 并集） |
| `zh_runtime_catch2` | push/PR | 是 | catch2 [zh-translation] + 基线回归 |
| `zh_help_runtime` | push/PR | 是 | [zh-help] catch2 + zh_help.rc bot |

`zh_ci_gate` 替代了旧的 `zh_static_checks`（原仅运‎行 post-coder.sh），
增加了 post-translator.sh 的控制符 parity、术语验证、格式完整性、
@keyword@ 完整性检查。

### split_source.py — source.txt 条目拆分

从 source.txt 中按正则模式提取条目到领域文件。database.cc 已支持从 `i18n/zh/` 目录加载所有 `.txt` 文件。

```bash
# 预览匹配条目（不修改 source.txt）
python3 .claude/scripts/split_source.py crawl-ref/source/dat/i18n/zh/source.txt \
    --domain spells --pattern 'spell|cast|magic|conjure' \
    --output crawl-ref/source/dat/i18n/zh/spells.txt

# 实际移动（从 source.txt 中移除已匹配条目）
python3 .claude/scripts/split_source.py crawl-ref/source/dat/i18n/zh/source.txt \
    --domain spells --pattern 'spell|cast|magic|conjure' \
    --output crawl-ref/source/dat/i18n/zh/spells.txt --move
```

## 典型工作流

### 新增翻译后

```bash
bash .claude/scripts/verify_zh.sh --profile translation
```

### 代码修改后

```bash
bash .claude/scripts/verify_zh.sh --profile code
```

### 提交前审查

```bash
bash .claude/scripts/verify_zh.sh --profile review
```

### 发现盲区

```bash
python3 .claude/scripts/scan_i18n.py missing-t crawl-ref/source/ > missing.txt
python3 .claude/scripts/scan_i18n.py arg-mismatch \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt > mismatches.txt
```

## 退出码约定

| 脚本 | 子命令 | 发现时退出码 |
|------|--------|-------------|
| `verify_zh.sh` | `--profile translation/code/review/ci` | 1（有 blocking failure） |
| `i18n_extract.py` | `validate` | 1（有缺失 key） |
| `i18n_extract.py` | `stale`, `missing`, `extract` | 0（信息性） |
| `scan_i18n.py` | `missing-t`, `mprf-p`, `arg-mismatch`, `check-gaps`, `source-txt-integrity` | 1（有违规） |
| `scan_i18n.py` | `validate-terms`, `species-consistency`, `monster-*-consistency` | 1（有违规） |
| `scan_i18n.py` | `anti-patterns --strict` | 1（有 strict 发现） |
| `scan_i18n.py` | `anti-patterns`（无 --strict） | 0（lenient-only 不阻断） |
| `scan_i18n.py` | `lang-args` | 0（启发式，始终通过） |
| `check_consistency.sh` | 所有模式 `--strict` | 1（有违规） |
| `cross_file_terms.py` | — | 1（有跨文件问题） |
| `source_control_parity.py` | — | 1（有 `\n` 不匹配），0（仅 `\t`/`\r` 警告或全通过） |
| `source_control_parity.py` | `--strict-all` | 1（有任何控制符不匹配） |
| `post-coder.sh` | — | 1（有 blocking failure） |
| `post-translator.sh` | — | 1（有 blocking failure） |
| `post-reviewer.sh` | — | 1（有 blocking failure） |
| `post_zh_runtime.sh` | `catch2`, `full`, `baseline` | 1+（任一层/聚合失败或基线回归） |
| `post_zh_runtime.sh` | `fast` | 1+（聚合失败） |
| `post_zh_runtime.sh` | `help-full`, `help-baseline` | 1+（catch2 失败/bot 失败/帮助回归） |
| `zh_runtime_check.py` | `--baseline` 对比 | 1（有新回归），0（无新问题） |
| `zh_runtime_check.py` | `--mode help --baseline` | 1（帮助类型回归），0（无新问题） |
| `smoke_test.sh` | — | 0（始终，警告不阻断；无 crawl 二进制时跳过） |
| `check_checkpoint.sh` | — | 0=当前, 2=建议更新, 3=强烈建议 |
