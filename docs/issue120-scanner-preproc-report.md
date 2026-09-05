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
