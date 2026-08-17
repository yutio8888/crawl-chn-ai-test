# 翻译工具链使用说明

项目 `.claude/scripts/` 下有多个脚本覆盖翻译质量保障的完整链路。所有脚本从仓库根目录运行。

## 语境化移动短语审计

`audit_move_i18n.py` 会枚举 `_get_move_verb()`、物种 walking verb、
`check_moveto*()` 固定动词及 `_find_cblink_target()` 动词，并将可达语法
场景与 `.claude/scripts/data/move_i18n_manifest.json` 的结构化清单比较。
每个 `move.<context>|<verb>` 都必须有精确且非空的 TextDB 条目；运行时
`C_()` 回退不能视为覆盖成功。此检查在 translation、code、review 和 CI
四类 profile 中均为阻断项。

```bash
python3 .claude/scripts/audit_move_i18n.py
```

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
| **冻结常规物品与 ego 名称清单** | `python3 .claude/scripts/audit_item_name_inventory.py --output /tmp/item-name-inventory.json` |
| **检查本次修改的精确术语键** | `python3 .claude/scripts/check_glossary_terms.py --base HEAD` |
| **检查持久化 T_()/C_() 指针** | `python3 .claude/scripts/scan_i18n_lifetime.py crawl-ref/source/ --require-parser` |
| **T_() 键验证** | `python3 .claude/scripts/i18n_extract.py validate crawl-ref/source/ --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **数据驱动翻译覆盖** | `python3 .claude/scripts/audit_data_i18n.py crawl-ref/source/ --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **source.txt 结构检查** | `python3 .claude/scripts/scan_i18n.py source-db-structure --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **source.txt 大小写碰撞** | `python3 .claude/scripts/scan_i18n.py source-key-collisions --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **source.txt 完整性** | `python3 .claude/scripts/scan_i18n.py source-txt-integrity --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **发现未翻译消息** | `python3 .claude/scripts/scan_i18n.py missing-t crawl-ref/source/` |
| **mprf_p 兼容性** | `python3 .claude/scripts/scan_i18n.py mprf-p crawl-ref/source/ --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **%s 数量一致** | `python3 .claude/scripts/scan_i18n.py arg-mismatch --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **控制符奇偶检查** | `python3 .claude/scripts/source_control_parity.py --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| **运行时冒烟测试** | `bash .claude/scripts/smoke_test.sh` |
| **统一 Catch2 运行时** | `bash .claude/scripts/post_zh_runtime.sh catch2` |
| **运行工具测试** | `bash .claude/scripts/tests/run_all.sh` |
| **隔离运行重 Python 测试/验证** | `bash .claude/scripts/run_isolated.sh python3 <test>` |

### 支持平台与依赖

通用验证入口支持 Ubuntu 和 macOS 系统 `/bin/bash`（包括 Bash 3.2），依赖
Python 3、Node.js、`tree-sitter==0.26.0`、`tree-sitter-cpp==0.23.4` 和
PyYAML。仓库内的 `run_with_timeout.py` 负责跨平台超时与 PTY transcript，
审阅证据锁由 Python `fcntl` 实现，因此无需额外安装 GNU `timeout`、`flock`、
`grep -P` 或 GNU `script`。Windows、Android 与 Tiles 构建辅助脚本属于
目标专用入口，其依赖以对应构建文档为准。

## 资源隔离（run_isolated.sh）

重内存 Python 测试（如 `test_monspeak_inventory.py`、`test_monspell_inventory.py`）、
`unittest discover` 以及整个 `verify_zh.sh` profile 默认运行在 Paseo daemon 的
`paseo.service` cgroup 内，可能耗尽其内存/CPU 预算并断开外层连接。
`fork`/`nohup`/`setsid`/`start_new_session=True` 只能脱离终端与会话，无法脱离
父 cgroup；唯一有效方式是启动到不同的 cgroup。

`.claude/scripts/run_isolated.sh` 在用户级 systemd 会话且 `paseo-workers.slice`
存在时，通过 `systemd-run --user` 启动一个瞬态 service 落入该 slice，并施加
`MemoryHigh`/`MemoryMax`/`CPUWeight`/`CPUQuota` 限制；否则回退为直接 `exec`，
保证 CI 与无 systemd 环境可移植。

```bash
# 隔离运行单个重测试
bash .claude/scripts/run_isolated.sh python3 .claude/scripts/tests/test_monspeak_inventory.py

# 隔离运行整个验证 profile（内部所有 python3 子进程共享同一 cgroup）
bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh --profile translation
```

限制可通过环境变量覆盖：

| 环境变量 | 默认 | 含义 |
|---|---|---|
| `ZH_ISOLATE_MEMORY_HIGH` | `2G` | 节流阈值（memcg.high） |
| `ZH_ISOLATE_MEMORY_MAX` | `3G` | 硬杀阈值（memcg.max） |
| `ZH_ISOLATE_CPU_WEIGHT` | `20` | 相对 daemon 的 CPU 权重 |
| `ZH_ISOLATE_CPU_QUOTA` | `200%` | CPU 软上限（2 核） |

`MemoryHigh=2G`/`MemoryMax=3G` 是单条瞬态 service 的上限，保护单个隔离命令。
对于并发 worker（`run_all.sh` 最多 4 路并发），单 service 上限无法约束总占用，
应在 slice 层叠加聚合上限，例如放置机器本地 drop-in
`~/.config/systemd/user/paseo-workers.slice.d/limits.conf`：

```ini
[Slice]
MemoryHigh=4G
MemoryMax=6G
CPUQuota=300%
```

该 drop-in 位于用户主目录、不入仓库，且其值应大于单 service 上限、小于
`paseo.service` 的 `MemoryMax`（8G），为 daemon 保留余量。两层上限作用不同，
不能互相替代。包装器会将 `python`/`python3` 首参数解析为绝对路径，避免瞬态
service 继承不同的 `PATH`。

Python 版本以仓库根目录 `.python-version` 为唯一来源：本地命令应通过支持
该文件的版本管理器运行，或用 `python3 --version` 核对；CI 的 setup-python
步骤读取同一文件。

## 脚本详解

### audit_item_name_inventory.py — 常规物品与 ego 名称清单

从生产枚举、物品属性表和实际名称 producer 派生常规物品 subtype、武器品牌
verbose/terse/adjective、护甲 ego verbose/terse，以及具体首饰效果名称。
它不会用手写数量证明覆盖；生产枚举身份集和名称 producer 产物集必须双向
相等。输出包含稳定身份、生命周期、每种显示形态、TextDB 翻译状态、输入
文件摘要和清单内容摘要。漏项、多项、重复身份、缺失中文或缺失显示形态
都会以非零状态退出。

```bash
python3 .claude/scripts/audit_item_name_inventory.py \
    --output /tmp/item-name-inventory.json
```

同一入口也负责 `item-description:*` 翻译质量 M1 实验的确定性 bundle。生成模式要求
已经通过双向覆盖检查的 Issue 29 review artifact，以及冻结的 evaluator prompt 和术语
context；输出只能位于 `.artifacts/i18n/quality/`。bundle 保留 canonical truth bytes，
把 truth/population 标为 sealed，并将四个有界 blind shard 与 prompt/context 单独列为
evaluator 文件。adopted revision 只标为 `unadjudicated`，不能从历史 `keep/adjust`
自动推导为 clean。

```bash
python3 .claude/scripts/audit_item_name_inventory.py \
    --scope issue29-v2 \
    --review-results docs/item-extended-review-results.md \
    --quality-m1-output-dir .artifacts/i18n/quality/m1-item-description-v1 \
    --quality-prompt /tmp/quality-prompt.md \
    --quality-context /tmp/quality-context.txt

python3 .claude/scripts/audit_item_name_inventory.py \
    --scope issue29-v2 \
    --review-results docs/item-extended-review-results.md \
    --verify-quality-m1 .artifacts/i18n/quality/m1-item-description-v1 \
    --quality-prompt .artifacts/i18n/quality/m1-item-description-v1/prompt.md \
    --quality-context .artifacts/i18n/quality/m1-item-description-v1/context.txt
```

验证模式从当前 inventory 和 bundle 内冻结的 prompt/context 重建全部文件，要求文件
集合、每个字节、truth commitment、分片重组、identity 守恒和 evaluator 标签隔离全部
一致；缺失、额外、非 canonical、符号链接或摘要漂移均失败关闭。

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

从 C++ 和 Lua 源码中提取所有 `T_("...")`、`C_("ctx", "...")`、
`N_("...")`、`NC_("ctx", "...")` 和 `crawl.t_("...")` 字面量调用，与
source.txt 对比。`N_`/`NC_` 只标记“之后会进入动态 `T_`/`C_`，且没有
专用数据审计”的 C++ 字面量表。它们的宏会先强制字面量拼接，再调用
constexpr helper，因此运行时 `const char*` 和命名字符数组都会编译失败。
宏返回稳定英文字面量且不查缓存；选中后仍必须用匹配的
`T_`/`C_` 即时翻译。协议/内部表和已有专用审计的数据源不需一律标记。
有限 `?:` 表达式中的所有字面量分支也会提取；若仅部分分支可静态确定，
可确定分支进入覆盖清单，同时在 stderr 报告动态分支。Lua 使用轻量词法器，
不会把注释、普通字符串或 long string 中的伪调用当成键。

**已知限制**：不会猜测 `T_(变量)` 的取值范围。若变量来自 C++ 字面量持久表，
必须在表中用 `N_`/`NC_` 标记；以下非 C++ 数据场景由专用审计补充：
- `duration-data.h`: endmsg/expmsg → `T_(endmsg)` at runtime
- `mon-util.cc`: 怪物名 → `T_(en.c_str())` at runtime
- `dat/mons/*.yaml`: 怪物名定义（非 .cc/.h 文件）

这些场景由 `audit_data_i18n.py` 补充扫描。

`T_`/`C_`/`N_`/`NC_` 都支持 C++ 相邻字符串字面量合并。

`//` 和 `/* ... */` 注释中的 `N_("字面量")` /
`NC_("上下文", "字面量")` 是显式 extraction annotation，会纳入覆盖验证；
注释中的 `T_`/`C_` 仍忽略。普通字符串、raw string 和字符字面量里的伪调用
也不提取。注释 annotation 同样只允许语法字面量；宏名/变量实参会
fail-closed，不尝试展开或猜测。

`Ability_List` 中本次受 Issue 63 影响的条目已标记；其余既有能力名仍是
提取可见性范围债，后续修改该表时应尽量整表迁移，不得把部分标记误说成
已覆盖全部能力名。

```bash
python3 .claude/scripts/i18n_extract.py extract crawl-ref/source/        # 提取所有 T_() 键
python3 .claude/scripts/i18n_extract.py validate crawl-ref/source/ \     # 验证覆盖率（CI 阻断）
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt \
    --report-json /tmp/i18n-extract-coverage.json
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
# 覆盖 direct sink、显示文本 producer、Tiles builder 和动态 key wrapper。
python3 .claude/scripts/scan_i18n.py missing-t crawl-ref/source/ \
    --display-contracts-only \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# mprf-p: 位置参数（%n$s）必须用 mprf_p 而非 mprf（MinGW 兼容）
python3 .claude/scripts/scan_i18n.py mprf-p crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt
# source-db-structure: 检查 %%%% 分隔符完整性、格式合规
python3 .claude/scripts/scan_i18n.py source-db-structure \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# source-key-collisions: 大小写不敏感键碰撞检测
python3 .claude/scripts/scan_i18n.py source-key-collisions \
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

`notify_fail`/`yesno`/`set_more` 等 sink、已登记的不可使用原因
producer，以及 Tiles tooltip builder 都属于零债务生产阻断契约。
裸英文或只经 `N_()`/`NC_()` 延迟标记的文本会统一报 `DISPLAY`
并返回失败；必须在显示消费点执行 `T_()`/`C_()`。

默认扫描排除 DEBUG、`#if 0`、WIZARD 分支及 `wiz-*`/`dbg-*` 文件。
TextDB 查找键保持英文；例如 `getLongDescription(... + " status")` 被登记为
已翻译值 provider，不将其键误报为 UI 文案。
`--extended-display-audit` 仅作旧调用兼容标志，不再改变扫描范围或阻断语义。

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

# 单元测试（同时覆盖单文件、小目录和大型目录语义）
python3 .claude/scripts/tests/test_scan_i18n_lifetime.py
```

所有扫描范围统一使用屏蔽注释与字面量的词法候选切片，避免结果因“单文件或
完整仓库”而切换语义，也避免旧 binding 在超大 C++ initializer 上的 native 崩溃。
它检查 helper、聚合字段、成员赋值、容器 mutation、延迟 lambda 与立即调用
lambda。解析器缺失、输入无效或严格目标解析失败均退出 2；JSON 输出包含统一的
`discovered/scanned/failed` 覆盖字段，CI 以 fail-closed 运行。完整生产树中由
条件编译造成、且已精确绑定到文件与错误 offset 的词法债务列在
`coverage.prerequisites`；任何新增或位置变化的词法错误仍立即退出 2。

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

### zh_runtime_check.py — JSONL Issue Protocol v1

统一 Catch2 驱动 `post_zh_runtime.sh catch2` 使用 `zh_runtime_check.py` 解析
`[zh-translation]` 和 `[message-overlay]` 两个标号的输出：

```bash
# 从 Catch2 输出解析 [zh-translation] 协议
python3 .claude/scripts/zh_runtime_check.py \
    --catch2-stderr <path> --catch2-stdout <path> --baseline <path>

# 生成输出基线
python3 .claude/scripts/zh_runtime_check.py \
    --catch2-stderr <path> --catch2-stdout <path> --output-baseline <path>
```

协议 v1 schema 定义在 `.claude/scripts/data/zh_issue_protocol_v1.schema.json`。

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

规则：`STRING_CTOR`/`STRING_OBJECT`/`CONCAT`/`TERNARY` 为 **HIGH（阻断）**，
`CALL_NO_CSTR` 为 **WARN**。格式参数按函数签名及重载槽位解析，不再取首个
字面量；局部标识符按最内层声明类型判断，三元表达式检查每个结果分支。
修复：先构造 `std::string` 局部变量再传 `.c_str()`；三元 `cond ? string(a) : ""`
会把两个分支都提升为 `std::string`。依赖 `pip3 install tree-sitter tree-sitter-cpp`。

### 编排者工具

```bash
# check_checkpoint.sh: 检查 ORCHESTRATION_STATE.md 是否过期
#   退出码: 0=当前, 2=落后1-5个commit, 3=落后6+个commit
bash .claude/scripts/check_checkpoint.sh

# record_review.sh: 记录单行 schema-v2 review JSONL；merge-time 必须附证据字段
bash .claude/scripts/record_review.sh '{"schema_version":2,"review_id":"...","run_id":"...","date":"...","agent_type":"...","task_summary":"...","base":"...","head":"...","diff_hash":"...","glossary_sha256":"...","raw_log":"...","findings":{"blocker":0,"needs_fix":0,"suggestion":0},"fix_iterations":0,"verdict":"Go","trigger":"merge-time","session_id":"..."}'

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

# 任务期默认 changed；也可显式要求全量静态检查
bash .claude/scripts/verify_zh.sh --profile code --scope changed
bash .claude/scripts/verify_zh.sh --profile code --scope full

# CI 门禁（纯静态，不执行 make/runtime）
bash .claude/scripts/verify_zh.sh --profile ci

# 合并审核唯一入口；不要手工运行 --profile review 或 review --full
bash .claude/scripts/review_prepare.sh <candidate> <target>
# 按 routing 完成 reviewer readiness 后：
bash .claude/scripts/review_final_gate.sh <candidate> <target>
bash .claude/scripts/review_at_merge.sh <candidate> <target>
```

`translation`/`code` 默认 `--scope changed`，`review`/`ci` 默认
`--scope full`。changed 只缩小明确支持文件列表的 AST 扫描；Agent/Skill
策略同步、**source-db-static**、source.txt/TextDB 完整性、key coverage、格式、
术语与导出新鲜度等全局门禁始终全量执行。绑定 `--base/--head` 时 changed 集合
来自该不可变范围；未绑定时来自 `HEAD` 相对工作树（含 untracked files）。

**source-db-static 阶段**：所有 profile 均要求执行，不可绕过。连续运行三个
检查（即使前一个失败也继续），收集全部证据后统一判断是否阻断：
```bash
python3 .claude/scripts/scan_i18n.py source-db-structure --source-txt ...
python3 .claude/scripts/scan_i18n.py source-key-collisions --source-txt ...
python3 .claude/scripts/i18n_extract.py validate crawl-ref/source --source-txt ...
```

`verify_zh.sh` 随后嵌套调用 `post-coder.sh` / `post-reviewer.sh` 时会设置
`ZH_VERIFY_SOURCE_DB_STATIC_COMPLETE=1`，仅跳过底层脚本中重复的
`i18n_extract.py validate`。直接运行底层脚本时不设置该标记，仍执行完整 key
coverage；无论前置 phase 成败，`source-db-static` 的结果都已独立记录且阻断。

**--profile ci 纯静态**：`ci` profile 不执行 `make`、`smoke_test.sh`、
`post_zh_runtime.sh` 等任何编译/运行时操作。仅运行静态数据检查（source-db-static
+ translation-static + code-static）。

风险路由自动追加测试：C++ i18n diff 运行增量 `make` 和 ZH smoke；
font/CJK/runtime diff 运行新鲜的 `[zh-translation]` Catch2。review profile 仅由
`review_final_gate.sh` 调用，并运行统一 Catch2；不要在 readiness 或本地 preflight
手工重跑。`--full` 是显式的三层 runtime 开发/发布工具，不属于 reviewer
readiness。`ci` 完全跳过编译和运行时。

同一 immutable mixed candidate 不得串行运行 `translation`、`code`、`ci` 三个
profile。开发期按当前改动选 domain profile；若需要一次组合静态 preflight，只跑
`ci`。先完成 bundle reviewer，再在 reviewer-approved 最终 OID 上各运行一次任务或
release 契约明确要求的 `run_all.sh`、`help-full`、runtime `full`，最后进入唯一
`review_final_gate.sh`。

`post-coder.sh` 的 string-concat advisory 使用版本控制的
`data/string_concat_advisory_baseline.json`。稳定 identity 排除行号，因此代码
移动不会制造新告警；报告分别列出 existing/new/resolved，且只展开 new。
新增项仍是 advisory，不改变既有 blocking 语义。审核后更新基线：

```bash
python3 .claude/scripts/scan_string_concat.py crawl-ref/source/ \
  --skip-low --format json > /tmp/string-concat.json || true
python3 .claude/scripts/advisory_baseline.py \
  --input /tmp/string-concat.json \
  --baseline .claude/scripts/data/string_concat_advisory_baseline.json --write
```

stream builder 若直接以 `builder.str()` 进入 `mpr`/`mprf` 等高置信显示 sink，
报告会携带 sink provenance 并提升为 HIGH；`N_`/`NC_` 仅是延迟键标记，不被
误认为已翻译。发现仍为 advisory，但扫描器输入、读取或解析失败按退出码 2 阻断。

每个 profile 运行 core-static 检查（始终阻断）加上领域特定检查。
报告写入 `.claude/metrics/verify/verify-<profile>-<timestamp>.log`。

底层仍保留 `post-coder.sh`、`post-translator.sh`、`post-reviewer.sh`，
但它们通过 `verify_zh.sh` 统一调度。

### post_zh_runtime.sh — 运行时测试与基线回归

三层运行时测试，支持多种模式：

```bash
# catch2: 统一 Catch2 驱动，构建一次 + 运行两个标号 + 独立解析 + 报告
#         [zh-translation] 和 [message-overlay] 均阻断
#         若 [zh-translation] 失败，[message-overlay] 仍继续运行
#         报告包含 zh-translation=rc, message-overlay=rc 两条记录
bash .claude/scripts/post_zh_runtime.sh catch2

# full: Layer 1 (Catch2) + Layer 2 (Lua) + Layer 3 (RC Bot)（分钟级）
bash .claude/scripts/post_zh_runtime.sh full

# bot: 增量构建当前 Console，并运行 RC、17 面板和 wizard gameplay workflows
bash .claude/scripts/post_zh_runtime.sh bot

# bot-fast: 复用当前 Console，但生成全新的 Bot 日志
bash .claude/scripts/post_zh_runtime.sh bot-fast

# fast: 仅聚合明确指定的旧运行目录（无构建）
ZH_RUNTIME_REUSE_DIR=<run-dir> bash .claude/scripts/post_zh_runtime.sh fast

# baseline: full 运行 + 写入新基线到 test/baselines/zh/
bash .claude/scripts/post_zh_runtime.sh baseline

# help-full: Issue 52 帮助系统全量测试（[zh-help] catch2 + zh_help.rc bot）
bash .claude/scripts/post_zh_runtime.sh help-full

# help-baseline: 帮助系统全量 + 写入基线到 test/baselines/zh-help/
bash .claude/scripts/post_zh_runtime.sh help-baseline
```

聚合脚本 `zh_runtime_check.py` 支持 `--mode default`（三层 i18n 扫描）和
`--mode help`（帮助系统状态标记）。

Bot 不再使用最低标记数门槛：`--bot-manifest all` 要求 11 个 RC 用例 ID
完整、唯一、按序出现，并对恶魔之鞭、蜘蛛之靴、特洛格、歌唱之剑和
妖术女王等关键结果执行语义 token 断言；独立 Python PTY 驱动使用精确、唯一、
有序的 17 个面板用例（含 initial），逐屏验证宗教、角色、装备、技能、能力、
总览、消息、法术、抗性、变异、已识别物品、符文、护甲、珠宝、金币和地图。
独立的 wizard-assisted PTY 使用精确、唯一、有序的 21 个 workflow 用例：
wizard 只负责构造加入特洛格、敌对老鼠和棍棒等确定状态，随后通过普通玩家
按键验证有神宗教页、真实 Tab 近战与击杀、拾取、`=` 整理、`{` 首次铭刻
及替换铭刻、`!` 楼层注释及地城总览。物品栏字母从实际渲染结果解析，
不假定固定槽位；战斗最多
执行 12 次 Tab，未击杀即失败。workflow 使用独立 transcript/results，不混入
RC marker manifest；任一步缺少中文语义、出现已知英文提示、超时或非零退出均阻断。
复用 Console 的 `bot-fast` 预计总耗时约 10–15 秒。
每次运行写入独立的
`zh-runtime-<UTC>-<pid>/` 证据目录，固定 `C.UTF-8` / `xterm` / seed；
任一 shard 超时或非零退出都阻断。帮助 PTY 驱动会逐键打开主帮助、`?/`
查询菜单及全部 23 种类型，拒绝“未知命令”并要求每屏含中文；描述内容的
数据库级精确性由同次 `[zh-help]` Catch2 验证。

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

GitHub Actions 的 zh-specific job 以工作流文件为准：

| Job | 触发 | 需编译 | 说明 |
|-----|------|--------|------|
| `zh_tooling_tests` | push/PR | 否 | Ubuntu + macOS：`run_all.sh`（自动发现所有 test_*） |
| `zh_ci_gate` | push/PR | 否 | Ubuntu + macOS：`verify_zh.sh --profile ci`（纯静态） |
| `zh_runtime_catch2` | push/PR | 是 | 统一 Catch2 驱动：[zh-translation] + [message-overlay] |
| `zh_runtime_full` | schedule/workflow_dispatch | 是 | L1+L2+L3 全量运行时 |
| `zh_help_runtime` | push/PR | 是 | [zh-help] catch2 + zh_help.rc bot |

`zh_ci_gate` 不执行任何编译或运行时操作。`zh_runtime_full` 仅在定时触发
（UTC 17:18）或手动 `workflow_dispatch` 且 `run_full_runtime=true` 时运行。

所有 zh-specific job 均可通过 `schedule` 和 `workflow_dispatch` 控制：
```yaml
schedule:
  - cron: '17 18 * * *'
workflow_dispatch:
  inputs:
    run_full_runtime:
      description: 'Run full runtime tests (L1+L2+L3, slow)'
      type: boolean
      default: false
```

`--profile ci` 为纯静态 gate，合并 source-db-static 和 translation-static
检查，不包含 make、smoke_test.sh 或 post_zh_runtime.sh 等编译/运行时步骤。

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
| i18n 扫描器 | 输入/依赖/发现/读取/解析失败 | 2（基础设施失败） |
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
| `post_zh_runtime.sh` | `bot`, `bot-fast` | 1+（缺失/重复/乱序/语义失败、非零退出或超时） |
| `post_zh_runtime.sh` | `fast` | 1+（聚合失败） |
| `post_zh_runtime.sh` | `help-full`, `help-baseline` | 1+（catch2 失败/bot 失败/帮助回归） |
| `zh_runtime_check.py` | `--baseline` 对比 | 1（有新回归），0（无新问题） |
| `zh_runtime_check.py` | `--mode help --baseline` | 1（帮助类型回归），0（无新问题） |
| `smoke_test.sh` | — | 0（始终，警告不阻断；无 crawl 二进制时跳过） |
| `check_checkpoint.sh` | — | 0=当前, 2=建议更新, 3=强烈建议 |
