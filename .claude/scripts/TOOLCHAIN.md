# 翻译工具链使用说明

项目 `.claude/scripts/` 下有 14 个脚本覆盖翻译质量保障的完整链路。所有脚本从仓库根目录运行。

## 架构概览

```
Agent 生成修改 → post-*.sh 聚合验证 → 编排者读原始日志判断
                                    ↓
                  ┌──────────────────────────────────────────┐
                  │  scan_i18n.py (6 子命令)                  │
                  │  i18n_extract.py (4 子命令)               │
                  │  audit_data_i18n.py (数据驱动覆盖)        │
                  │  check_consistency.sh (7 模式)             │
                  │  cross_file_terms.py                      │
                  │  smoke_test.sh                            │
                  │  check_checkpoint.sh                      │
                  │  record_review.sh                         │
                  └──────────────────────────────────────────┘
```

## 快速参考

| 需求 | 命令 |
|------|------|
| **T_() 键验证** | `python3 .claude/scripts/i18n_extract.py validate crawl-ref/source/ --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **数据驱动翻译覆盖** | `python3 .claude/scripts/audit_data_i18n.py crawl-ref/source/ --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **发现未翻译消息** | `python3 .claude/scripts/scan_i18n.py missing-t crawl-ref/source/` |
| **mprf_p 兼容性** | `python3 .claude/scripts/scan_i18n.py mprf-p crawl-ref/source/ --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **%s 数量一致** | `python3 .claude/scripts/scan_i18n.py arg-mismatch --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **位置参数间隙** | `python3 .claude/scripts/scan_i18n.py check-gaps --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **术语验证（decisions.md）** | `python3 .claude/scripts/scan_i18n.py validate-terms --glossary docs/decisions.md --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **反模式检测** | `python3 .claude/scripts/scan_i18n.py anti-patterns crawl-ref/source/ --strict` |
| **跨文件术语一致性** | `python3 .claude/scripts/cross_file_terms.py crawl-ref/source/dat/i18n/zh/` |
| **语言依赖参数** | `python3 .claude/scripts/scan_i18n.py lang-args crawl-ref/source/` |
| **数据库完整性** | `bash .claude/scripts/check_consistency.sh --all --strict` |
| **运行时冒烟测试** | `bash .claude/scripts/smoke_test.sh` |
| **检查点验证** | `bash .claude/scripts/check_checkpoint.sh` |
| **聚合验证（推荐）** | `bash .claude/scripts/post-coder.sh` / `post-translator.sh` / `post-reviewer.sh` |
| **上下文注入** | `bash .claude/scripts/context_resolve.sh "task" --files <files>` |
| **运行测试** | `bash .claude/scripts/tests/test_scan_i18n.sh` |

## 脚本详解

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

替代旧的 `scan_untranslated.sh`。6 个子命令：

```bash
# missing-t: 未翻译的 mprf/mpr 调用
python3 .claude/scripts/scan_i18n.py missing-t crawl-ref/source/

# mprf-p: 位置参数（%n$s）必须用 mprf_p 而非 mprf（MinGW 兼容）
python3 .claude/scripts/scan_i18n.py mprf-p crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# arg-mismatch: EN key 和 CN 翻译的 %s 数量一致性
python3 .claude/scripts/scan_i18n.py arg-mismatch \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# check-gaps: 位置参数编号间隙检测（Issue 29 %N$.0s 模式）
python3 .claude/scripts/scan_i18n.py check-gaps \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# validate-terms: 检查 decisions.md 中被拒绝的术语是否仍在代码或翻译中出现
python3 .claude/scripts/scan_i18n.py validate-terms \
    --glossary docs/decisions.md \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# anti-patterns: 检测已知 Agent 错误模式
#   --strict: 零误报规则（英文冠词残留）
#   不加 --strict: 包含 lenient 规则（.c_str() 误用、conj_verb() 中文检测）
python3 .claude/scripts/scan_i18n.py anti-patterns crawl-ref/source/ --strict

# lang-args: 检测 T_() 中语言依赖参数（启发式，始终 exit 0）
python3 .claude/scripts/scan_i18n.py lang-args crawl-ref/source/
```

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

### 聚合验证脚本（推荐使用，替代单独运行）

```bash
bash .claude/scripts/post-coder.sh       # 代码修改后: 阻断 gate；string-concat / smoke 为 warning-only
bash .claude/scripts/post-translator.sh  # 翻译后: 阻断 gate；validate-terms + format + @keyword@
bash .claude/scripts/post-reviewer.sh    # 审查后: 阻断 gate；all consistency + cross-file terms
```

所有输出写入 `.claude/metrics/verify/<agent>-<timestamp>.log`，编排者直接读取原始日志。
这三个脚本在存在 blocking failure 时都会以非零退出，适合本地 gate 和 CI 直接复用。

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
bash .claude/scripts/post-translator.sh
```

### 代码修改后

```bash
bash .claude/scripts/post-coder.sh
bash .claude/scripts/post-coder.sh --full   # 需要显式触发 L1-L3 运行时链路时使用
```

### 提交前审查

```bash
# 0. 检查编排者检查点是否过期
bash .claude/scripts/check_checkpoint.sh

# 1. 运行聚合审查
bash .claude/scripts/post-reviewer.sh

# 2. 编译
cd crawl-ref/source && make -j4
```

### 发现盲区

```bash
python3 .claude/scripts/scan_i18n.py missing-t crawl-ref/source/ > missing.txt
python3 .claude/scripts/scan_i18n.py arg-mismatch \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt > mismatches.txt
```

### CI / 提交前完整检查

```bash
bash .claude/scripts/check_checkpoint.sh && \
bash .claude/scripts/tests/run_all.sh && \
python3 .claude/scripts/i18n_extract.py validate crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt && \
python3 .claude/scripts/scan_i18n.py mprf-p crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt && \
python3 .claude/scripts/scan_i18n.py arg-mismatch \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt && \
python3 .claude/scripts/scan_i18n.py anti-patterns crawl-ref/source/ --strict && \
bash .claude/scripts/check_consistency.sh --all --strict && \
cd crawl-ref/source && make -j4
```

## 退出码约定

| 脚本 | 子命令 | 发现时退出码 |
|------|--------|-------------|
| `i18n_extract.py` | `validate` | 1（有缺失 key） |
| `i18n_extract.py` | `stale`, `missing`, `extract`, `check-escapes` | 0（信息性） |
| `scan_i18n.py` | `missing-t`, `mprf-p`, `arg-mismatch`, `check-gaps` | 1（有违规） |
| `scan_i18n.py` | `validate-terms` | 1（有被拒绝术语） |
| `scan_i18n.py` | `anti-patterns --strict` | 1（有 strict 发现） |
| `scan_i18n.py` | `anti-patterns`（无 --strict） | 0（lenient-only 不阻断） |
| `scan_i18n.py` | `lang-args` | 0（启发式，始终通过） |
| `check_consistency.sh` | 所有模式 `--strict` | 1（有违规） |
| `check_consistency.sh` | 所有模式（无 --strict） | 0（向后兼容） |
| `cross_file_terms.py` | — | 1（有跨文件问题） |
| `post-coder.sh` | 默认 | 1（有 blocking failure），0（仅 warning 或全通过） |
| `post-coder.sh` | `--full` | 1（静态 gate 或 L1-L3 / baseline 聚合失败） |
| `post-translator.sh` | 默认 | 1（有 blocking failure） |
| `post-reviewer.sh` | 默认 | 1（有 blocking failure） |
| `post_zh_runtime.sh` | `fast`, `full`, `baseline` | 1+（任一层或聚合失败，含 marker/baseline 回归） |
| `smoke_test.sh` | — | 0（始终，警告不阻断） |
| `check_checkpoint.sh` | — | 0=当前, 2=建议更新, 3=强烈建议 |
| `record_review.sh` | — | 1（无效 JSON） |
| `context_resolve.sh` | — | 1（参数错误） |
