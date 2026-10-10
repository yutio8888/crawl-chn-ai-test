# Issue 120：基线探针与实施边界

状态：已按后续授权完成方案 2 和三个宏的局部适配。下文先保留探针阶段的
原始记录，文末给出最终实现、验证和剩余工作。未修改被扫描的 C++ 文件。

基线：`6b82440c5496e04517fc6ae197943bbf84f8ae43`。
分支：`codex/scanner-preproc-exemption`。
术语上下文 SHA-256：
`366e807eaae5403b6c3925df5970cd237b447ead76fdb717b71273473b5db67e`。

## 探针与模式清单

探针通过 `git show` 读取基线，使用生产入口的 `parse_cpp_annotations()`，
遍历全部子节点（包括 ERROR 的子节点），并使用原有 phase-2 lexer 和
`_preprocessor_switch_lines()` 判断节点起点。以下行号仅是探针证据，
不是拟议豁免条件。尚未登记任何新模式。

| 文件 | 行 | 节点及文本锚点 | 成因及处理边界 |
|---|---:|---|---|
| directn.cc | 622 | missing `}` | `#ifndef USE_TILE_LOCAL` 切开 if/else，恢复时提前结束 else 块；现有窗口内 |
| directn.cc | 626 | ERROR `}` | 上述提前结束使真正闭括号孤立；现有窗口内 |
| directn.cc | 1941 | ERROR `else` | `DEBUG_DIAGNOSTICS` 分支末尾的 else 与 endif 后语句分离；现有窗口内 |
| directn.cc | 2439 | ERROR `#ifdef USE_TILE_LOCAL\n    : public` | 类继承列表被条件指令切开；现有 directive 规则处理 |
| directn.cc | 2441 | ERROR `#else\n    : public ui` | 同一继承列表的另一分支；现有 directive 规则处理 |
| directn.cc | 2443 | ERROR `#endif` | 同一继承列表结束指令；现有 directive 规则处理 |
| directn.cc | 2446 | ERROR `UIDirectionChooserView(direction_chooser& dc) :` | 类头恢复失败，构造函数被误读；现有窗口内 |
| directn.cc | 2447 | missing `;` | 上述恢复把成员初始化列表当作需要分号的语句；现有窗口内 |
| directn.cc | 3721 | ERROR `*` | DEBUG_DIAGNOSTICS 中 `const vault_placement &vp(*env.level_vaults[map_index]);` 的直接初始化被当作声明符解析；现有窗口内 |
| directn.cc | 3721 | ERROR `.` | 同一初始化被误读后的成员访问恢复错误；现有窗口内 |
| main.cc | 193 | ERROR `void` | `NORETURN static void` 声明宏；现有 annotation helper 只覆盖 `NORETURN void`，不在窗口内 |
| main.cc | 235 | ERROR `__attribute__((externally_visible))` | 条件分支内的 GNU 属性与 endif 后 main 声明分离；现有窗口内 |
| main.cc | 426 | ERROR `void` | `NORETURN static void` 定义宏，与 193 同因，不在窗口内 |
| main.cc | 2041 | ERROR `#ifdef USE_TILE_LOCAL` | 构造函数参数中的位或表达式被条件切开；现有 directive 规则处理 |
| main.cc | 2043 | ERROR `#endif` | 上述参数表达式的条件结束；现有 directive 规则处理 |
| main.cc | 2051 | ERROR `"<w>"` | 字符串与 `CRAWL` 对象宏相邻，宏未展开；距 endif 已 8 行，不在窗口内 |
| main.cc | 2400 | ERROR `tiles.` | USE_TILE_WEB 内的 else 与前面的 if 分隔，调用被误读为声明；现有窗口内 |
| menu.cc | 115 | ERROR `#ifdef USE_TILE_LOCAL` | 构造函数成员初始化列表中插入指令；现有 directive 规则处理 |
| menu.cc | 117 | ERROR `#endif` | 上述初始化列表的条件结束；现有 directive 规则处理 |
| menu.cc | 791 | missing `;` | `if (min_column_width <= 0)` 的语句体从下一行 ifdef 开始，恢复时误报缺少分号；节点在指令之前，不在窗口内 |
| menu.cc | 2397 | ERROR `indent\n#ifdef` | 声明名与初始化值被 ifdef 切开；节点起点不在窗口内，现有 directive 规则也不匹配 |
| menu.cc | 2401 | ERROR `=` | 上述声明的 else 分支留下孤立初始化符；现有 lexer 将该分支从窗口扣除 |
| menu.cc | 2810 | ERROR `const int width =` | 声明与初始化值被下一行 ifdef 切开；节点在指令之前，不在窗口内 |
| menu.cc | 2987 | ERROR `#ifdef USE_TILE_LOCAL` | set_scroll 参数表达式被条件切开；现有 directive 规则处理 |
| menu.cc | 2989 | ERROR `#endif` | 上述参数表达式的条件结束；现有 directive 规则处理 |
| menu.cc | 3566 | ERROR `, int` | `va_arg(args, int)` 的第二个参数是类型，未展开的宏被按普通函数调用解析；不在窗口内 |

因此无法把全部节点登记成满足指定三条件的条件编译模式。
尤其不能为窗口外的 `void`、字符串、`, int` 添加通用 ERROR 白名单。

## SKIP 原因

`verify_zh.sh` 的 code profile 默认 changed scope；未绑定 base/head 时，
文件集合来自 `git diff --name-only HEAD` 加 untracked 文件，绑定时来自
`git diff --name-only BASE..HEAD`。`post-coder.sh` 只将 C++ 路径收进
`CHANGED_CPP`，为空时 `run_scoped_scanner()` 输出
`RESULT: SKIP (changed scope has no C++ files)`。
拼接 advisory 在相同条件下报告无改动 C++。

这是无改动文件导致的既定优化，保持不变。工具脚本本身的改动也不会产生
CHANGED_CPP；因此本任务的 code profile 不能单独证明三个基线文件均被扫描，
必须另外显式运行三个文件的真实 CLI。下方探针已执行这两条 CLI，没有 SKIP。
生命周期 CLI 当前使用 lexical engine，不调用共享的 has_relevant_parse_error；
Issue 描述的共享解析失败实际涉及 varargs 和 concat 两个入口。

## 待确定的最小范围

建议保留方案 2 的路径、节点类型、局部文本匹配，不改变风险规则，也不做宏配置
预处理展开，但另行授权两项必要改动：

1. 针对已确认的条件切分结构，允许紧邻指令之前和 else 分支中的节点，
   仍由 phase-2 lexer 发现指令，并以精确上下文限制；这改变现有窗口语义。
2. 对 `NORETURN static void`、相邻字符串的 `CRAWL`、`va_arg(args, int)`
   提供各自受限的语法适配；这些不是条件编译窗口豁免。

这两项超出当前“切换点之外的任何解析错误仍 fail-closed”的硬性范围。
AGENTS.md 的 Minimal Sufficient Design 要求范围实质扩展前返回用户决定，
所以在此停止实施，不以扩大白名单伪造验收通过。

尚未运行实施后的 run_all、code profile 和 Android 分支验证；尚无实现、测试、
最终文档提交，也未发布完成 handoff 评论。方案 3 留待后续。

## 可复现探针

从仓库根目录执行以下代码。输出记录所有节点，随后运行两条真实扫描器 CLI；
扫描器退出码与 stdout/stderr 均原样输出。临时目录只包含导出的基线文件。

```python
import importlib.metadata
import subprocess
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, '.claude/scripts')
from tree_sitter import Language, Parser
import tree_sitter_cpp
from i18n_shared import parse_cpp_annotations, _preprocessor_switch_lines, _line_of_byte

for package in ('tree-sitter', 'tree-sitter-cpp'):
    print(package, importlib.metadata.version(package))
with tempfile.TemporaryDirectory() as td:
    paths = []
    for name in ('directn', 'main', 'menu'):
        relative = f'crawl-ref/source/{name}.cc'
        source = subprocess.check_output(['git', 'show', f'6b82440c54:{relative}'])
        path = Path(td) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(source)
        paths.append(str(path))
        tree = parse_cpp_annotations(Parser(Language(tree_sitter_cpp.language())), source)
        switch = _preprocessor_switch_lines(source)
        print('FILE', relative)
        stack = [tree.root_node]
        while stack:
            node = stack.pop()
            if node.is_missing or node.type == 'ERROR':
                line = _line_of_byte(source, node.start_byte)
                kind = 'missing ' + node.type if node.is_missing else node.type
                print(line, kind, repr(source[node.start_byte:node.end_byte]),
                      'window=', line in switch)
            stack.extend(reversed(node.children))
    for scanner in ('scan_varargs_string.py', 'scan_string_concat.py'):
        command = ['python3', f'.claude/scripts/{scanner}', '--files',
                   ','.join(paths), '--format', 'json', '--require-parser']
        result = subprocess.run(command, capture_output=True, text=True)
        print('COMMAND:', ' '.join(command))
        print('EXIT:', result.returncode)
        print('STDOUT:\n' + result.stdout)
        print('STDERR:\n' + result.stderr)
```

## 探针原始输出摘要

探针枚举 directn.cc 10 个、main.cc 7 个、menu.cc 9 个 ERROR/missing 节点。
两个基线 CLI 均退出 2，coverage 为 discovered=3、scanned=1、failed=2。
逐节点成因见上表；原文保存在
`.claude/metrics/verify/issue120/issue120-probe.txt`（gitignored）。

## 最终实施（授权后的方案 2）

后续授权允许对精确模式扩展条件窗口，并在现有 annotation helper 中适配
三个具体宏。前文“待确定”及“尚未实施”记录的是探针提交时的状态；以下为
最终实现与验证结果。

`i18n_shared.py` 的 `_PREPROCESSOR_PATTERNS` 使用
`crawl-ref/source/directn.cc`、`main.cc`、`menu.cc` 的仓库相对路径后缀，
不再使用整文件 SHA 或绝对行号。导出目录和独立 worktree 保留该后缀即可
复用豁免。任何以 `crawl-ref/source/<登记文件名>` 结尾的路径都可匹配，
不校验其所在仓库身份；只有同名、但不具备该后缀的路径不会匹配。
省略路径也不会匹配模式。

每个模式登记节点类型、精确节点文本（missing 节点使用缺失 token）及完整
局部上下文。匹配 ERROR 文本采用全等，防止 parser recovery 吞入新错误后
仍因前缀相同而被放行。原有 phase-2 lexer 和 `_PREPROC_SWITCH_WINDOW=4`
保持不变；原 live-body/post-endif 窗口之外，仅在登记上下文含 lexer 确认的
真实条件指令且节点距该指令至多四行时允许匹配。这覆盖指令前节点和 else
分支，不全局扩展窗口。ERROR 子节点继续逐个校验，未配对条件指令仍阻断。
三个登记文件的 directive ERROR 也使用具体模式，不走原有泛用 directive
恢复分支。模式旁保留逐节点成因，探针行号只作注释证据。

精确上下文包含空白：menu.cc L115 模式以前置空行开头，删除该空行也会
撤销豁免。这是选择完整上下文匹配带来的已知脆弱点，不承诺任意格式改动
均可通过。登记文件内关闭了通用 `#` 指令 ERROR 恢复；新增条件切分结构
会比未登记文件更严格地 fail-closed，须探测新节点并登记有成因的精确模式。

三个宏适配均属于**方案 3 的前置局部步骤**，以后完整预处理实现时一并替换：

- `NORETURN static void`：复用既有函数声明/定义前缀匹配，等长空格替换
  NORETURN；函数签名及函数体继续由 parser 校验。
- `CRAWL`：只匹配 AST 中的独立 identifier，且与实际字符串字面量之间
  只有空白，将五字节替换为五字节的空字符串占位。注释、raw-string 内容、
  宏定义和更长标识符不会触发。
- `va_arg`：只匹配该具体调用名；简单命名类型、限定符及指针/引用类型经
  alias declaration 解析确认后，把类型操作数等长改为普通表达式占位。
  保留完整第一操作数，避免抹掉其嵌套调用中的风险或真实语法错误。
  未支持的复杂类型形式保持原样并继续 fail-closed。

所有替换保持字节长度和换行位置。字符串取值读取归一化 AST 文本，诊断
仍使用原始源代码位置，避免把占位位置上的原始 `CRAWL` 字节误读成字符串。
varargs、生命周期和拼接风险规则没有改变；被扫描 C++ 文件没有修改。

除了前述 changed/no-C++ 的 SKIP（保持不变），回归测试确认两个扫描器的
生产目录入口原本还会跳过 parse validation。因此三个已登记路径在目录
入口也强制走同一解析校验，这是关闭实际验收缺口的最小入口修复。
其他文件的既有目录入口行为没有扩大到本任务处理范围。

## 测试与证据说明

新增测试通过真实 varargs/concat CLI 覆盖三文件基线、插入七行、删除五处
空行、两个入口、错误路径、窗口外删分号、窗口内未登记错误。三个宏分别
覆盖合法输入与同一位置删分号，并检查字节终点及换行位置。额外验证具体
宏名限制、注释/字符串/define 不改写及 va_arg 第一操作数中的 HIGH 风险
不会被归一化隐藏。原 completeness 测试更新为路径/上下文语义，保留 EOL
和 phase-2 lexer 回归。

基线和两个 Android HEAD 均使用 `git archive` 导出到临时目录，用当前分支
脚本运行。每个分支显式扫描“本分支改动的全部 C/C++ 文件 + 三个登记文件”，
并分别对整个 source 目录运行 varargs、concat、lifetime 三个 CLI。没有修改
其他 worktree。concat 退出 1 表示 advisory；退出 2 或非空 coverage.failed
才是解析/基础设施失败。varargs/lifetime 必须退出 0。

首轮沙箱验证失败原文也保留：沙箱将 /tmp 属主显示为 uid 65534，且禁止
部分既有测试写 Git 对象；初始 PATH 中 Python 是 3.11.2。最终验证使用
`.python-version` 指定的 Python 3.13.14，通过 run_isolated.sh 在宿主权限
下执行。宿主默认四路 run_all 有一次清单测试因临时 dirty checkout 失败，
因此使用现有 ZH_TOOLING_TEST_JOBS=1 串行设置重跑，不修改测试门禁。

完整命令、退出码及输出保存在 gitignored 的
`.claude/metrics/verify/issue120/issue120-scanner-validation.txt` 和
`.claude/metrics/verify/issue120/issue120-scanner-branches.txt`。
verify 的汇总 stdout、内部 verify.log 及
post-coder 原始日志均保留，避免只提供报告路径而遗漏实际 code-static 输出。

最终 full-scope code profile 退出 0，`0 blocking failure(s)`；code-static
报告八项 advisory。额外导出基线版本的 concat 扫描器和 shared helper 复查，
得到相同的 571 existing、8 new、22 resolved 及相同八条 identity。这些是
既有 advisory baseline 差异，不是本次改动引入，未改写该 baseline。

领域审阅路由结果为 zh-code-reviewer；用户提供的独立审核（Fable 5.1）结论
为 Changes Requested（Blocker 0、Needs Fix 1、Suggestion 8），修复见下文。
修复后的独立复审及 GitHub CI 待接手者在合并前完成。按用户要求没有 push、merge。方案 3 的完整
Android/桌面宏配置预处理留待后续。
## 首轮验收结果（审核修复前）

验证代码提交：`dba4d2d4ffd7`（后续提交仅保存本文及原始证据）。

| 验证 | 结果 |
|---|---|
| 完整 run_all（Python 3.13.14、host、JOBS=1） | exit 0；61 passed, 0 failed |
| code --scope full --base 6b82440c54 --head dba4d2d4ff | exit 0；0 blocking failure(s) |
| 基线三文件显式 CLI | varargs=0，concat=1 advisory，lifetime=0；解析失败为零 |
| android-save-safety 84df089468a39c7b912be08ea23d14acc8d46622 | 显式范围和全目录三个扫描器全部通过 |
| android-context-keyboard 108705b0f6edffe1b2457972aa146c691cc8ae39 | 显式范围和全目录三个扫描器全部通过 |

验证后再次读取两个分支 HEAD，均与导出时一致。当前分支相对基线的
`crawl-ref/source` diff 为空。

原始证据（仅本地，不入库）：
`.claude/metrics/verify/issue120/issue120-scanner-validation.txt`、
`.claude/metrics/verify/issue120/issue120-scanner-branches.txt`。

## 独立审核修复

- Needs Fix：directn 副本使用 `td/crawl-ref/source/directn.cc`，目录入口指向
  `td/crawl-ref/source`；两个扫描器、两个入口均先证明未注入时通过，再证明
  窗口外注入错误后失败，避免路径不匹配造成无效负例。
- S2/S3：更新伪指令集成负例的注释，明确它们不能单独证明 lexer 窗口语义；
  修正 lexer 说明的误缩进。
- S4：在登记的 `vault_placement &vp(...)` 上下文内部只删除一个分号，
  通过真实 CLI 和两个入口验证正例通过、负例阻断。
- S5：上下文最后一行由最后一个实际字节（`start + len(context) - 1`）
  计算；新增边界负例，拒绝把紧随上下文的下一行指令算进上下文。
- S6/S7：准确说明路径后缀匹配不绑定仓库身份；缺少 tree-sitter 时通过
  setUp/skipTest 跳过该依赖测试，而不是导入失败。
- S8/S9：上文记录空白也参与精确匹配的脆弱点，以及登记文件新增条件切分
  结构会更严格 fail-closed 的行为；TOOLCHAIN.md 同步说明后者。

原始日志已逐字移至 `.claude/metrics/verify/issue120/`（gitignored），
未推送的原文档提交通过 `git commit --amend` 移除两份日志，现为
`2754330f18`，没有使用 reset --hard。

本轮复验使用 Python 3.13.14、宿主权限和 run_isolated.sh，串行运行完整
套件以避开既有 clean-checkout 夹具竞态，再对干净修复提交执行完整 code
profile。原文位置（不入库）：

```text
.claude/metrics/verify/issue120/review-targeted.log
.claude/metrics/verify/issue120/review-completeness.log
.claude/metrics/verify/issue120/review-missing-parser.log
.claude/metrics/verify/issue120/review-run-all.log
.claude/metrics/verify/issue120/review-code-full.log
```

完整 profile 的内部 verify.log 和 post-coder 日志也汇入 review-code-full.log。
执行命令（PATH 先选用 .python-version 指定版本）：

```bash
ZH_TOOLING_TEST_JOBS=1 bash .claude/scripts/run_isolated.sh bash .claude/scripts/tests/run_all.sh
bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh --profile code --scope full --base 6b82440c54 --head HEAD
```

## 分支只读扫描复现脚本

将下列脚本保存到临时文件，在当前 worktree 根目录使用 run_isolated.sh
运行。脚本只读其他 worktree，所有导出文件都在临时目录；不创建 worktree、
不移动任何分支引用。它的全部 stdout/stderr 见上述分支扫描日志。

```python
import json
import os
from pathlib import Path
import subprocess
import tempfile

root = Path.cwd()
scripts = root / '.claude/scripts'
base = '6b82440c5496e04517fc6ae197943bbf84f8ae43'
branches = [
    ('baseline', root, base),
    ('android-save-safety', root.parent / 'android-save-safety', 'HEAD'),
    ('android-context-keyboard', root.parent / 'android-context-keyboard', 'HEAD'),
]
failed = False
for label, repo, ref in branches:
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', ref], text=True).strip()
    print(f'=== {label} HEAD={head} ===', flush=True)
    with tempfile.TemporaryDirectory(prefix='issue120-') as td:
        export = Path(td)
        # Archive extraction only writes this temporary directory.
        archive = subprocess.Popen(['git', '-C', str(repo), 'archive', head,
                                    'crawl-ref/source'], stdout=subprocess.PIPE)
        extracted = subprocess.run(['tar', '-x', '-C', td], stdin=archive.stdout)
        archive.stdout.close()
        if archive.wait() or extracted.returncode:
            raise RuntimeError('archive export failed')
        changed = subprocess.check_output(['git', '-C', str(repo), 'diff',
                                           '--name-only', base, head], text=True).splitlines()
        files = {f'crawl-ref/source/{name}.cc' for name in ('directn', 'main', 'menu')}
        files.update(p for p in changed if Path(p).suffix in ('.cc', '.h', '.cpp', '.c'))
        absolute = [str(export / p) for p in sorted(files)]
        for scanner in ('scan_varargs_string.py', 'scan_string_concat.py', 'scan_i18n_lifetime.py'):
            scopes = ('explicit',) if label == 'baseline' else ('explicit', 'full')
            for scope in scopes:
                args = [str(export / 'crawl-ref/source')] if scope == 'full' else (
                    ['--files', *absolute] if scanner == 'scan_i18n_lifetime.py'
                    else ['--files', ','.join(absolute)])
                command = ['python3', str(scripts / scanner), *args,
                           '--format', 'json', '--require-parser']
                print('COMMAND:', ' '.join(command), flush=True)
                result = subprocess.run(command, text=True, capture_output=True)
                print('EXIT:', result.returncode, flush=True)
                print('STDOUT:\n' + result.stdout, flush=True)
                print('STDERR:\n' + result.stderr, flush=True)
                data = json.loads(result.stdout)
                coverage = data.get('coverage', data.get('meta', {}).get('coverage'))
                acceptable = result.returncode == 0 or (
                    scanner == 'scan_string_concat.py' and result.returncode == 1)
                if coverage and coverage['failed']:
                    acceptable = False
                print(f'CHECK {label} {scanner} {scope}: {"PASS" if acceptable else "FAIL"}', flush=True)
                failed |= not acceptable
raise SystemExit(1 if failed else 0)
```

## 方案 3 的显式实验入口（基线 5209b80e3b）

本轮新增可用的 `--compile-commands DB` 补充扫描入口，没有切换默认门禁。
每个 DB 表示一个配置；三个扫描器先保留原始源码的风险结果，再严格检查
每个请求文件在每个 DB 中的展开内容。缺文件条目、缺依赖、CPP 失败和
展开后的 ERROR/missing 均退出 2。此模式不把原始条件编译造成的恢复节点
作为整个文件的语法证明，语法判断来自明确列出的 CPP 配置；未列出的配置
也不因原始恢复扫描而获得语法覆盖。默认模式的失败行为及已有适配仍保留。

共用 helper 调用 Clang `-E`，从真实 linemarker 提取目标文件文本并映射
回原始调用行，不保留整份依赖头文本。字符串内部的伪 marker 不参与映射；
多行 raw literal 的内部换行与 Clang 另外输出的行填充分别处理，中文文件名
按 C 字节转义解码。源码主动写入的 `#line`/GNU marker 暂不支持并拒绝，
包括 phase-2 拼接和注释后的指令；不能借伪造 filename 静默裁掉目标代码。
宏展开诊断定位到原调用行，不声称提供逐 token 拼写列。

`__builtin_va_arg` 是 CPP 后仍存在的编译器 intrinsic。其第二操作数经受限
类型语法及 alias declaration 检查后等长替换为表达式占位，完整保留第一
操作数；不支持类型、错误第一操作数和其他真实语法仍拒绝。它没有重用
前置 `va_arg` 豁免来宣称宏已被解决。`directn.cc` 的局部引用初始化改为
`const vault_placement &vp = *env.level_vaults[map_index];`，消除确认过的
合法 C++ 被 tree-sitter 误解析的问题，引用对象、初始化时机和作用域不变。

数据库接受标准 `arguments` 或 Unix shell 风格 `command`，每文件每 DB
必须唯一。首版支持 Clang 和 NDK Clang，明确拒绝 GCC、响应文件、外部
compiler config、间接预处理参数和其他编译动作。对象/依赖输出参数移除，
现代 Clang 的自动 driver config 关闭；配置所需参数必须显式写在命令中。
真实 NDK 回归确认 config 内藏 `-o` 不能在验证失败前覆盖既有输出文件。

Makefile 的 `i18n-compile-commands` 目标只导出调用配置下普通 core `.cc`
的 `CXX`、`STDFLAG` 和 `ALL_CFLAGS`，不维护另一份宏清单，不编译依赖。
header、utility、rltiles 和 Catch2 的专属上下文/参数不由该目标猜测。
详细命令及限制见 `.claude/scripts/TOOLCHAIN.md` 的显式预处理章节。
生命周期 helper 索引只展开 DB 中列出的文件，未列出的仍使用既有 lexical
索引；不同 DB 的互斥 helper 分开建立索引。该入口不是完整跨文件预处理。
展开结果仅在一次进程内复用，没有新后台服务、磁盘缓存或默认 CI 依赖。

### 实测范围与剩余条件

原型覆盖 directn/main/menu 三个真实 TU，配置为 Linux console、local
tiles、webtiles、console 加 DEBUG_DIAGNOSTICS，以及 NDK arm64 API 21。
最终桌面 CLI 使用 Makefile 导出参数，显式配置同 tree 已准备的依赖/生成
头目录；NDK 部分仍是基于现有构建宏的有界原型参数，并非完整 NDK 构建数据库。
这些证据不代表 Windows、macOS、其他 Android ABI/API 或全部 debug 组合。

原型比较每 TU 的 dump-tokens 与普通 `-E`：前者约 70–79 MB、5.2–5.8 秒，
后者约 3.6–6.2 MB、0.23–0.37 秒，提取的目标文本约 63–97 KB。因此显式入口
采用 linemarker，不把逐 token dump 放入默认工作流。

console 全发现范围探针共 784 文件，111.422 秒：740 个没有 CPP/TS 缺口，
44 个有缺口（9 CPP、35 parser）。这不是 44 个游戏源码错误，也不是 740 个
文件风险扫描通过：缺口包括平台头、header 包含前置上下文、合法 C++ 的
TS 限制及 prebuilt 的源内 `#line`。arena、beam、clua 等真实 TU 也仍有
TS 缺口，不能用三个成功原型覆盖代替全目录支持。以后默认替换前还需解决
这些输入、从真实 TU 保留 header 的包含上下文、验证真实平台构建矩阵，
然后才能删除已被充分替代的旧模式和前置适配。Issue #120 继续保留该范围。

最终三个扫描器对三文件和五 DB 的真实 CLI 退出码分别为 varargs=0、
concat=1 advisory、lifetime=0，coverage.failed 均为空。concat 同时报告原始
与各配置的结果，因此可包含重复 identity 和宏标记展开后的建议项；没有
改写既有 baseline，也不把 advisory 退出 1 误作解析失败或无风险结论。

定向回归覆盖宏参数中的 T_/C_/mprf_p、原始风险保留、互斥 helper 配置隔离、
原调用行诊断、源内伪 marker、Unicode/空格路径、缺配置和真实语法负例，
以及输出参数与 compiler config 的文件保护。已有 completeness 和 lifetime
套件也通过。实际命令和 stdout/stderr 保留在本机临时日志：

- `/tmp/issue120-configured-final.log`：预处理和真实 CLI/Makefile 回归。
- `/tmp/issue120-completeness-tests.log`：既有 scanner completeness。
- `/tmp/issue120-lifetime-tests.log`：既有 lifetime scanner 回归。
- `/tmp/issue120-final-real-clis.log`：实际配置参数、CLI 命令、结果和 NDK sentinel；
  各 scanner 的完整输出路径也记录在此文件。
- `/tmp/issue120-full-console-inventory.jsonl`：全发现范围的 CPP/TS 探针。
- `/tmp/issue120-prototype-negatives-final.log`：前期真实源配置及负例原型。

绑定候选的 code profile、领域复审和 CI 由编排者统一执行；本节不预先宣称
它们已经通过，也不以本轮显式入口关闭整个方案 3。

## 后续推进：真实目标编译命令导出

本轮从 `b27476622d` 继续，范围是剩余验收第 1、2 项所需的构建配置来源。
普通 core 导出器已扩展到所选实际构建目标的 C++ 编译单元：utility、生成
的 tiledef 和 Catch2。`I18N_BUILD_GOAL` 复用现有目标的标准及 debug/coverage
分支；`I18N_SCAN_FILES=all` 从对应对象清单导出，无需维护另一份源文件清单。
各文件的导出目标与真实对象目标共享专属变量声明，保留 YACC 参数、tiledef
参数和 Catch2 自定义 main 宏。tilegen 使用其自身 Makefile 的宿主编译参数，
单独导出；不能用游戏目标或 NDK 的参数代替宿主工具参数。

新增的 `export_compile_commands.py` 只负责序列化 Make 已求值的参数和汇总，
不选择编译器、不推断宏、不运行编译。临时条目随命令结束删除，全部条目收齐
后才原子替换输出。导出时不读取或修复旧依赖文件，不生成源码，也不编译对象。
具体用法和范围在 TOOLCHAIN 的显式预处理章节。

这一阶段没有改变三个扫描器的解析或风险规则。既有 44 个 CPP/TS 缺口的原始
清单已用于范围分析：其中有头文件独立解析缺少宏/包含上下文、合法 C++ 的
parser 限制、平台头及生成代码的源内行号指令。新增导出能力不等于这些缺口
已经修复，也不把未编译的源文件登记为已验证。真实 TU 中的头文件上下文、
跨文件 helper、源内 `#line`、剩余语法适配和完整 Windows/macOS/Android
矩阵仍待完成。默认门禁和旧模式保留，Issue #120 继续 Open。

### 本轮验证与边界

通过 `run_isolated.sh` 使用 Python 3.13.14 验证，证据位于当前工作树的
`.claude/metrics/verify/issue120-tu-export/`（gitignored）：

- `preprocessor.log`：现有预处理回归文件 26 项通过，包含三个扫描器的宏风险、
  原始风险保留及缺配置/真实语法错误负例。新增导出测试把实际对象编译 recipe
  的 Make dry-run 参数与导出条目逐项比对，覆盖 console、local tiles、webtiles、
  debug、Catch2、monster；这验证参数来源，不代表这些平台的全量风险扫描完成。
- `dryrun-path-tests.log`：最终 `make -n`、相对路径、旧数据库保留、旧依赖文件
  不读取和不生成构建产物的补充回归通过；全量目标清单和并行收集也在回归中。
- `tilegen-commands.json` 和 `tilegen-real-cli.log`：实际 Linux tilegen、
  `TILES=y DEBUG=y` 配置的 5 个 TU 使用导出 DB 执行三个真实 CLI，全部
  `coverage.failed=[]`。varargs/lifetime 退出 0；concat 退出 1，保留 90 项
  原始及展开来源的 advisory，不把重复来源计作新增游戏缺陷。
- `verify_zh.sh --profile code` 最终退出 0，零阻断。
  原始报告：`.claude/metrics/verify/20260912T065608775572998+0000-1317597-b27476622deb/verify.log`。
  首轮失败是新工作树尚未初始化/构建已锁定的 Lua 子模块；按现有 CI 的命令
  补齐 luac 后复验通过，没有跳过语法门禁。

审阅路由为 `zh-code-reviewer`，本轮按该领域在同一会话内自查，未进行独立
审阅。以上是未提交工作树的开发验证；尚无绑定提交的合并审阅或 GitHub CI，
不宣称已满足整个 Issue 的关闭条件。

## 后续推进：头文件的真实包含上下文

这一阶段在同一候选工作树中扩展三个扫描器的显式 `--compile-commands`
入口。验收范围是：无需给头文件编造独立编译命令，能保留真实 TU 的宏状态和
包围结构；诊断回到目标物理文件；任何必需上下文的失败继续阻断。完整平台
矩阵、源内 `#line` 支持、跨 TU 完整语义和默认门禁替换不属于本阶段完成项。

共享预处理器按 Clang 的 include 进入/返回标记记录每次包含，保留目标文件
及其实际包含祖先。类成员片段、函数参数片段和初始化器片段因此能在包围结构
内解析。同一文件重复包含仍保留各次宏状态；一批头文件按 DB 内 TU 流式展开，
不对每个头文件重跑全部命令，也没有新增后台服务或持久缓存。

三个 CLI 按上下文扫描，再将风险表达式定位到请求文件的物理行；上下文代码
不混入目标文件的 finding。JSON 增加 `translation_unit`，与配置路径一起
区分同一行在不同 TU 中的结果。头文件未被任何所选 TU 生效包含、CPP 失败、
目标上下文语法错误或原始行号无法保证时退出 2；某个 TU 成功不能掩盖后续
失败。源内 `#line` 仍明确拒绝，包含文件也执行检查。

生命周期索引使用当前 TU 的非系统头文件展开定义，避免把另一个 TU 对同一
头文件的宏状态合并进来。未配置文件的 lexical 事实不再冒充配置事实；原始
源码风险扫描继续保留。索引自身仍是 lexical 分析，其他 TU 的包含定义、完整
跨文件语义与索引输入的完整语法验证仍待后续推进。头文件回归另发现直接借用
指针的类成员初始化被误归为全局 advisory，本阶段已将其识别为 HIGH，并验证
普通方法局部变量、函数静态变量、局部类成员和命名空间变量的区别。

### 验证证据与剩余缺口

证据位于 `.claude/metrics/verify/issue120-header-context/`（gitignored）：

- `preprocessor.log`：完整预处理回归通过，包含三个真实 CLI 的头文件风险、
  重复包含、Unicode/空格路径、跨 TU 宏隔离、原始风险保留，以及缺上下文、
  后续上下文失败、CPP/语法错误、源内行号指令等负例。导出 recipe 比对也在
  已有对象文件的工作树中复验通过，测试不依赖对象尚未构建。
- `lifetime.log`：生命周期回归通过，含类成员初始化的作用域正反例。
- `core-commands.json`、`core-contexts.log`、`core-real-cli.log`：使用当前
  Linux console Make 配置的 `macro.cc coord.cc perlin.cc database.cc`，
  扫描 `cmd-keys.h coord.h perlin.h database.h`；三个 CLI 均退出 0，
  各自 `discovered=4, scanned=4, failed=[]`。当前机器单次 varargs、concat、
  lifetime 分别约 6.35、6.34、10.34 秒，仅表示该子集成本。
- `host-commands.json`、`host-real-cli.log`：使用 tilegen 的实际宿主 DB，
  扫描其四个工具头文件；三个 CLI 均退出 0，覆盖失败为空。
- `lifetime-raw-full.json`：全库原始源码生命周期检查退出 0、无 HIGH，保留
  `branch-data.h`、`macros.h`、`threads.h` 的原有 lexical 前置条件。该证据
  验证默认风险规则的兼容性，不计作全库配置预处理覆盖。
- `mpr-gap.log`：同一核心 DB 中的 `mpr.h:109` 在 `macro.cc` 和 `database.cc`
  上下文仍触发 tree-sitter 的 missing identifier；保留物理头文件和 TU 定位，
  继续作为阻断项。本阶段没有增加解析错误白名单，也没有据此重写旧 44 项
  全范围缺口清单的通过数。
- 项目规定的 `verify_zh.sh --profile code` 退出 0、零阻断。原始报告：
  `.claude/metrics/verify/20260912T072838950747257+0000-1545439-b27476622deb/verify.log`。
  验证后仅补齐本节证据记录。

真实依赖和生成头通过现有 Make 目标准备，命令日志保存在上述证据目录。
显式子集 DB 的成功只证明所列 TU；全量头文件包含关系、utility/Catch2 的
实际风险覆盖、合法 C++ parser 缺口、源内 `#line` 和 Windows/macOS/Android
真实构建矩阵仍未完成。审阅路由为 `zh-code-reviewer`，本阶段执行同会话领域
自查；未提交、未进行独立合并审阅或 GitHub CI。默认门禁继续使用现有模式，
Issue #120 仍不满足关闭条件。


## 2026-10-10 续办：有限 TU/header 候选恢复

当前候选基于 `d1a7d2d36bce4aa819b4494770dc3b55ac83ad65`，位于
`.worktrees/issue120-tu-recovery` / `codex/issue120-tu-recovery`。
从旧 `issue120-tu-context` 原样保留导出器和 TU/header 的 tracked WIP，
未清理旧工作树、旧证据或其他分支。上两节的日志属于旧开发验证，尤其旧
未绑定 base/head 的 profile 不能作为本候选的最终门禁。

本阶段接受范围是 Make 求值的真实对象编译参数导出，以及显式配置下的
有限头文件包含上下文。没有改默认验证入口，没有删除方案 2 模式或旧适配，
没有反向迁移 trunk 生产代码，也没有引入依赖、后台服务或持久缓存。
基线 Makefile 的实际对象 recipe、utility/tiledef/Catch2 专属变量及
C++14/自定义 Catch2 main 分支与导出目标一并核查；跨目标参数仍须通过
现有 recipe 比对回归复证，不能凭补丁适用或历史输出推断通过。

旧 `mpr.h` 缺口的最小修复位于 `parse_preprocessed_cpp`。tree-sitter 将
合法 deleted free function 误解析为 initialized function declaration
和缺 operand 的 delete expression。适配只接受单个具名函数声明的精确
`= delete;` 形状，等长置空 initializer，继续解析其签名、参数、终止分号及
相邻代码。成员 deleted function 保持原生解析能力；本适配范围内的非法
delete 操作数、缺分号和错误签名继续阻断，不使用节点/文件 ERROR 白名单。
这不保证原生 parser 拒绝所有其他声明形式的非法操作数。现有测试文件
扩展了源位置/字节边界正反例和三个真实 CLI 的头文件上下文回归，保留
varargs、concat、lifetime 风险以及准确的头文件/TU/调用行身份。

独立审阅的仅 `.cc` 输入负例发现：varargs/concat 未检查所含头文件中的
同文件 `#line`。现将所有实际 include frame 的源指令检查覆盖 TU-only 和
header 两种请求；新增三个 CLI 对该头文件路径的失败回归。旧候选与负例
证据保留，未经实际测试不将新候选宣称通过。

源码 `#line` 仍 fail-closed。后续必须区分物理文件/行与 compiler presumed
file/line，并验证 generated input 和 marker 的进入、返回及伪造边界，
不能直接把 presumed linemarker 当成物理调用位置。本阶段不实现该映射。
其他 TU 的完整语义、索引输入的完整语法验证、完整 Windows/macOS/Android
ABI/API/debug 矩阵及全范围运行成本仍未完成；explicit 子集成功不意味着
整个 Issue #120 完成，不能切换默认门禁或关闭 Issue。

当前仅完成轻量 AST 探针与 `git diff --check`；未运行 Make 构建、重 Python
套件或完整 profile。集中验证按现有隔离入口执行以下 focused 回归，再对
最终提交运行匹配的 bound code profile；结果需由本轮实际日志补充：

```bash
bash .claude/scripts/run_isolated.sh python3 .claude/scripts/tests/test_preprocessor_patterns.py
bash .claude/scripts/run_isolated.sh python3 .claude/scripts/tests/test_scan_i18n_lifetime.py
bash .claude/scripts/run_isolated.sh python3 .claude/scripts/tests/test_scanner_completeness.py
```

真实核心头文件复验需先按现有构建流程准备依赖/生成头，再使用当前
console DB 的 `macro.cc coord.cc perlin.cc database.cc`，显式请求
`cmd-keys.h coord.h perlin.h database.h mpr.h`。这能核对旧 mpr 缺口；
未准备依赖或未覆盖全部上下文时仍应退出 2，不把缺输入视作通过。
