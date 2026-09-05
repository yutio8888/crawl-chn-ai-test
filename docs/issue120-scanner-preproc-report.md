# Issue 120：基线探针与实施边界

状态：探针完成，尚未实施豁免。方案 2 的三条件与三文件全部通过之间存在
已复现的冲突，须先确定范围。没有改动扫描器或被扫描的 C++ 文件。

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

## 探针原始输出

上述 Python 探针退出码：0。内嵌两条 CLI 均退出 2，分别有两个文件解析失败；
varargs HIGH/WARN 均为 0，concat 已扫描的 directn.cc 有六条既存 MED advisory。
失败来自尚未适配的基线语法，属于本任务必须解决的阻断，不是工具缺失。

```text
tree-sitter 0.26.0
tree-sitter-cpp 0.23.4
FILE crawl-ref/source/directn.cc
622 missing } b'' window= True
626 ERROR b'}' window= True
1941 ERROR b'else' window= True
2439 ERROR b'#ifdef USE_TILE_LOCAL\n    : public' window= True
2441 ERROR b'#else\n    : public ui' window= False
2443 ERROR b'#endif' window= False
2446 ERROR b'UIDirectionChooserView(direction_chooser& dc) :' window= True
2447 missing ; b'' window= True
3721 ERROR b'*' window= True
3721 ERROR b'.' window= True
FILE crawl-ref/source/main.cc
193 ERROR b'void' window= False
235 ERROR b'__attribute__((externally_visible))' window= True
426 ERROR b'void' window= False
2041 ERROR b'#ifdef USE_TILE_LOCAL' window= False
2043 ERROR b'#endif' window= False
2051 ERROR b'"<w>"' window= False
2400 ERROR b'tiles.' window= True
FILE crawl-ref/source/menu.cc
115 ERROR b'#ifdef USE_TILE_LOCAL' window= False
117 ERROR b'#endif' window= False
791 missing ; b'' window= False
2397 ERROR b'indent\n#ifdef' window= False
2401 ERROR b'=' window= False
2810 ERROR b'const int width =' window= False
2987 ERROR b'#ifdef USE_TILE_LOCAL' window= False
2989 ERROR b'#endif' window= False
3566 ERROR b', int' window= False
COMMAND: python3 .claude/scripts/scan_varargs_string.py --files /tmp/tmp7d69tfjz/crawl-ref/source/directn.cc,/tmp/tmp7d69tfjz/crawl-ref/source/main.cc,/tmp/tmp7d69tfjz/crawl-ref/source/menu.cc --format json --require-parser
EXIT: 2
STDOUT:
{
  "scanner": "scan_varargs_string.py",
  "findings": [],
  "summary": {
    "HIGH": 0,
    "WARN": 0
  },
  "coverage": {
    "discovered": 3,
    "scanned": 1,
    "failed": [
      "/tmp/tmp7d69tfjz/crawl-ref/source/main.cc: tree-sitter parse error in /tmp/tmp7d69tfjz/crawl-ref/source/main.cc",
      "/tmp/tmp7d69tfjz/crawl-ref/source/menu.cc: tree-sitter parse error in /tmp/tmp7d69tfjz/crawl-ref/source/menu.cc"
    ]
  }
}

STDERR:
ERROR: /tmp/tmp7d69tfjz/crawl-ref/source/main.cc: tree-sitter parse error in /tmp/tmp7d69tfjz/crawl-ref/source/main.cc
ERROR: /tmp/tmp7d69tfjz/crawl-ref/source/menu.cc: tree-sitter parse error in /tmp/tmp7d69tfjz/crawl-ref/source/menu.cc

COMMAND: python3 .claude/scripts/scan_string_concat.py --files /tmp/tmp7d69tfjz/crawl-ref/source/directn.cc,/tmp/tmp7d69tfjz/crawl-ref/source/main.cc,/tmp/tmp7d69tfjz/crawl-ref/source/menu.cc --format json --require-parser
EXIT: 2
STDOUT:
{
  "meta": {
    "scanner": "scan_string_concat.py",
    "version": "1.0.0",
    "mode": "bare-only",
    "source": "/tmp/tmp7d69tfjz/crawl-ref/source",
    "coverage": {
      "discovered": 3,
      "scanned": 1,
      "failed": [
        "/tmp/tmp7d69tfjz/crawl-ref/source/main.cc: tree-sitter parse error in /tmp/tmp7d69tfjz/crawl-ref/source/main.cc",
        "/tmp/tmp7d69tfjz/crawl-ref/source/menu.cc: tree-sitter parse error in /tmp/tmp7d69tfjz/crawl-ref/source/menu.cc"
      ]
    }
  },
  "findings": [
    {
      "file": "directn.cc",
      "line": 3040,
      "column": 30,
      "rule": "COMPOUND_ASSIGN",
      "risk": "MED",
      "score": 2,
      "literal": "fruit cache",
      "receiver": "messageLookup",
      "wrapped": false,
      "reason": [
        "file=directn.cc (+2)"
      ],
      "sink": null
    },
    {
      "file": "directn.cc",
      "line": 3042,
      "column": 30,
      "rule": "COMPOUND_ASSIGN",
      "risk": "MED",
      "score": 2,
      "literal": "meat cache",
      "receiver": "messageLookup",
      "wrapped": false,
      "reason": [
        "file=directn.cc (+2)"
      ],
      "sink": null
    },
    {
      "file": "directn.cc",
      "line": 3044,
      "column": 30,
      "rule": "COMPOUND_ASSIGN",
      "risk": "MED",
      "score": 2,
      "literal": "baked goods cache",
      "receiver": "messageLookup",
      "wrapped": false,
      "reason": [
        "file=directn.cc (+2)"
      ],
      "sink": null
    },
    {
      "file": "directn.cc",
      "line": 3072,
      "column": 80,
      "rule": "RUNTIME_CONCAT",
      "risk": "MED",
      "score": 2,
      "literal": " peaceful ",
      "receiver": "?",
      "wrapped": false,
      "reason": [
        "file=directn.cc (+2)"
      ],
      "sink": null
    },
    {
      "file": "directn.cc",
      "line": 3078,
      "column": 43,
      "rule": "RUNTIME_CONCAT",
      "risk": "MED",
      "score": 2,
      "literal": "default peaceful ",
      "receiver": "?",
      "wrapped": false,
      "reason": [
        "file=directn.cc (+2)"
      ],
      "sink": null
    },
    {
      "file": "directn.cc",
      "line": 3081,
      "column": 43,
      "rule": "RUNTIME_CONCAT",
      "risk": "MED",
      "score": 2,
      "literal": "default ",
      "receiver": "?",
      "wrapped": false,
      "reason": [
        "file=directn.cc (+2)"
      ],
      "sink": null
    }
  ],
  "summary": {
    "COMPOUND_ASSIGN": {
      "total": 3,
      "HIGH": 0,
      "MED": 3,
      "LOW": 0
    },
    "RUNTIME_CONCAT": {
      "total": 3,
      "HIGH": 0,
      "MED": 3,
      "LOW": 0
    }
  },
  "per_file": {
    "directn.cc": {
      "MED": 6,
      "total": 6
    }
  }
}

STDERR:
ERROR: /tmp/tmp7d69tfjz/crawl-ref/source/main.cc: tree-sitter parse error in /tmp/tmp7d69tfjz/crawl-ref/source/main.cc
ERROR: /tmp/tmp7d69tfjz/crawl-ref/source/menu.cc: tree-sitter parse error in /tmp/tmp7d69tfjz/crawl-ref/source/menu.cc

```
