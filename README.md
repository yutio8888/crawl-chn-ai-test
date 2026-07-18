# 龙腾世纪：地下城探险 · 中文版

*Dungeon Crawl Stone Soup (DCSS) — Chinese Localization & CJK Tiles Support*

[![Build Status](https://github.com/crawl/crawl/workflows/Build/badge.svg)](https://github.com/crawl/crawl/actions/)

一个基于 DCSS 0.34.1 的中文汉化分支，提供完整的中文界面翻译与 CJK（中日韩）字符 tiles
渲染支持。玩家可以用中文畅玩这款经典 roguelike 游戏，在 tiles 模式下正常显示汉字。

> **上游原版 README**：[README.upstream.md](README.upstream.md)

---

## 目录

1. [功能特性](#功能特性)
2. [快速开始](#快速开始)
3. [项目结构](#项目结构)
4. [翻译进度](#翻译进度)
5. [技术架构](#技术架构)
6. [贡献指南](#贡献指南)
7. [相关资源](#相关资源)
8. [许可证](#许可证)

---

## 功能特性

### 中文翻译

- `source.txt` 与 ZH TextDB 覆盖游戏界面、战斗日志、怪物名称、技能说明、物品描述、
  神祇对话等；当前条目与覆盖数据以验证脚本报告为准
- 支持 `T_()` 宏系统：C++ 端直接嵌入翻译键，编译期提取与校验
- 三种翻译通道：
  - **C++ 字面量** `T_("English text")` — 可静态扫描
  - **函数包装器** `skill_name()` / `spell_title()` 等 — 内部自动翻译，调用者无感
  - **运行时变量** `T_(variable)` — 数据驱动的动态翻译（怪物名、地形名等）
- 独立的 TextDB 描述数据库：怪物描述、装备说明、神祇对话等存储在
  `crawl-ref/source/dat/descript/zh/` 和 `crawl-ref/source/dat/database/zh/` 中
- 当前术语以 [`docs/glossary.md`](docs/glossary.md) 为准；
  [`docs/decisions.md`](docs/decisions.md) 保存裁定理由和历史

### CJK Tiles 渲染

- **三层架构**解决 CJK 字符在 tiles 网格中的宽度问题：
  1. **网格计数层** (`tilereg-text.cc`)：使用 `wcwidth()` 计算每个字符的实际显示宽度，
     CJK 字符占 2 格，第二格标记为零宽空格 (U+200B)
  2. **渲染层** (`fontwrapper-ft.cc`)：跳过续格标记，CJK 字符使用 2 倍背景宽度
  3. **字体选择层**：默认中文部署使用 Maple Mono NF CN 作为主字体；渲染器仍支持
     可选的缺字回退
- 支持中英文混排，对齐正确

### 工具链

| 工具 | 用途 |
|------|------|
| `i18n_extract.py` | 提取 `T_()` 键 → 校验 source.txt 覆盖率 |
| `audit_data_i18n.py` | 审计数据驱动的运行时翻译 |
| `scan_i18n.py` | 多维度扫描：格式字符串、参数匹配、`mprf`→`mprf_p` 兼容性 |
| `check_consistency.sh` | 跨文件术语一致性检查 |
| `context_resolve.sh` | 动态术语上下文注入（AI 辅助翻译） |

---

## 快速开始

### 环境要求

- Linux (WSL2) 或 macOS
- GCC / Clang (C++17)
- Git、`make`、`pkg-config`
- 依赖库：Lua、SQLite、PCRE、SDL2、SDL2_image、Freetype、libpng、zlib

### 控制台版

```bash
cd crawl-ref/source
test -e init.txt || cp init.zh.txt init.txt
bash util/build-console.sh
./crawl
```

### Tiles 版（Windows 交叉编译）

```bash
test -d .worktrees/mingw-tiles/crawl-ref/source || \
  git worktree add .worktrees/mingw-tiles --detach HEAD
test -e crawl-ref/source/init.txt || \
  cp crawl-ref/source/init.zh.txt crawl-ref/source/init.txt
# 先按 docs/build-workflow.md 安装 MapleMono-NF-CN-Regular.ttf
bash crawl-ref/source/util/build-tiles.sh
bash .claude/scripts/deploy.sh
```

以上命令从仓库根目录运行。帮助脚本在专用 `.worktrees/mingw-tiles` 中生成
`crawl.exe`；部署脚本会在构建前检查中文配置和 Maple 字体，并在目标中验证
二者。完整流程与字体放置位置见 `docs/build-workflow.md`。

### 必需字体

| 字体 | 用途 |
|------|------|
| `MapleMono-NF-CN-Regular.ttf` | 所有 Tiles 文本角色的默认 CJK 主字体 |

渲染器仍支持缺字回退，但默认中文部署不再依赖固定的
DejaVu-primary/Sarasa-secondary 组合。运行时字体部署到 `dat/tiles/`，详见
`docs/cjk-tiles-architecture.md` 和 `docs/build-workflow.md`。

---

## 项目结构

```
crawl/                               # 仓库根目录
├── README.md                        # 本文件
├── README.upstream.md               # 上游原版 README（归档）
├── AGENTS.md                        # 跨运行时共享 Agent 入口
├── CODEX.md                         # Codex 运行时适配
├── CLAUDE.md                        # Claude Code 运行时适配
├── .agents/                         # 共享 policy、skill 与权威性地图
├── .opencode/                       # OpenCode agent/skill/运行时配置
├── .codex/                          # Codex agent 配置
├── docs/
│   ├── glossary.md                  # 当前术语 SSOT
│   ├── decisions.md                 # 翻译决策注册表
│   └── build-workflow.md            # 构建与部署流程
├── crawl-ref/
│   ├── source/
│   │   ├── *.cc, *.h                # C++ 游戏源码（含 T_() 翻译宏）
│   │   ├── dat/
│   │   │   ├── i18n/zh/source.txt   # 主翻译数据库
│   │   │   ├── descript/zh/         # 描述文本数据库
│   │   │   └── database/zh/         # 文本数据库（神祇对话等）
│   │   ├── contrib/fonts/           # 可选的本地字体来源
│   │   ├── init.zh.txt              # 受版本控制的中文配置模板
│   │   └── Makefile                 # 构建配置
│   └── docs/                        # 上游游戏文档
├── .claude/
│   ├── scripts/                     # 翻译工具链脚本
│   ├── workflows/                   # AI 工作流定义
│   └── skills/                      # AI 技能定义
└── .github/                         # CI 配置
```

### 分支说明

分支状态会随并行开发变化，不在本文维护“当前活跃”清单。使用
`git branch --show-current`、`git branch --all` 和任务交接记录确认当前状态；
Agent 的分支与 worktree 约束见 [`AGENTS.md`](AGENTS.md)。

---

## 翻译进度

翻译条目、调用点和覆盖率均为易变数据，不在手写文档中冻结。运行
`bash .claude/scripts/verify_zh.sh --profile translation` 查看当前 worktree 的
结构、键覆盖和术语验证结果；最终合并证据由项目审查门禁生成。

### 覆盖范围

- ✅ 战斗日志消息
- ✅ 怪物攻击动词
- ✅ UI 面板（Q/W/I/E/!/$/^）
- ✅ 瞄准界面
- ✅ 物品栏提示
- ✅ 地形描述
- ✅ 技能/法术名称
- ✅ 怪物描述表
- ✅ 命令帮助文本
- ✅ 种族难度标签
- ✅ 未鉴定药水/卷轴命名

---

## 技术架构

### 翻译系统

```
T_("English text")
    ↓
i18n_source_lookup()
    ↓
dat/i18n/zh/source.txt  ← 翻译数据库
    ↓
返回中文 / 回退英文
```

所有翻译通过 `T_()` 宏进行，语言选择在翻译数据库层面完成，C++ 代码保持语言无关。
`Options.language` 仅影响 `T_()` 查找的数据文件，调用方无需添加语言守卫。

### CJK Tiles 渲染

```
┌─────────────────────────────────────────┐
│  Layer 1: tilereg-text.cc               │
│  wcwidth() → CJK=2格, ASCII=1格         │
│  第2格写入 U+200B (ZWS) 续格标记        │
├─────────────────────────────────────────┤
│  Layer 2: fontwrapper-ft.cc             │
│  render_textblock()                     │
│  跳过续格标记，CJK 字符 2x 背景宽度      │
├─────────────────────────────────────────┤
│  Layer 3: fontwrapper-ft.cc             │
│  get_glyph_info() / load_glyph()        │
│  主字体 → CJK 回退字体链                 │
│  Atlas 单元格加宽以容纳 CJK 字形         │
└─────────────────────────────────────────┘
```

### 翻译类型体系

| 类型 | 模式 | 可审计性 |
|------|------|----------|
| I — C++ 字面量 | `T_("You hit %s.")` | 静态扫描 ✅ |
| II — 函数包装器 | `skill_name(sk)` → 内部 `T_()` | 调用链审计 |
| III — 运行时变量 | `T_(endmsg)` 数据驱动 | `audit_data_i18n.py` |
| IV — TextDB | `zh/monsters.txt` 等 | 按文件校验 |
| V — 协议/内部 | 永不翻译 | 禁止翻译 ❌ |

---

## 贡献指南

### 翻译贡献

1. 从 [`docs/glossary.md`](docs/glossary.md) 解析当前术语；
   [`docs/decisions.md`](docs/decisions.md) 仅用于查阅裁定理由和历史
2. 修改或新增 `crawl-ref/source/dat/i18n/zh/source.txt` 条目
3. 如有新增 `T_()` 调用，由同一任务的翻译资产所有者补齐对应条目
4. 运行统一校验：

```bash
bash .claude/scripts/verify_zh.sh --profile translation
```

### 代码贡献

1. Fork 本仓库
2. 在 `chn-0.34.1-base` 分支上创建特性分支
3. 确保 `make -j8` 编译通过
4. 如涉及 tiles，确保 `make CROSSHOST=x86_64-w64-mingw32 TILES=y -j8` 通过
5. 提交 PR

### 常见反模式（请勿重复）

- ❌ 翻译协议键（JSON key、`.des` 标签、存档标识符必须保持英文）
- ❌ 对中文调用 `conj_verb()`（产生乱码如 `"抓取s"`）
- ❌ 修改用作数据库查找键的 `.name` 字段
- ❌ 在同一格式字符串中混用中英文
- ❌ 使用 `buf.size()` 做 CJK 对齐（用 `strwidth()` 代替）
- ❌ 对运行时变量添加 `T_()` 但不添加 `source.txt` 条目

---

## 相关资源

- **上游项目**：[github.com/crawl/crawl](https://github.com/crawl/crawl)
- **官方主页**：[crawl.develz.org](https://crawl.develz.org/)
- **在线游玩**：crawl.develz.org 提供 Webtiles 和 SSH 接入
- **社区论坛**：[tavern.dcss.io](https://tavern.dcss.io/)
- **Reddit**：[r/dcss](https://www.reddit.com/r/dcss/)
- **IRC**：Libera 上的 `#crawl`（玩家）、`#crawl-dev`（开发）

---

## 许可证

本项目基于上游 DCSS，采用 **GPLv2+** 许可证。详见 [LICENSE](LICENSE)。

上游项目致谢名单见 [CREDITS.txt](crawl-ref/CREDITS.txt)。

### 字体版权

本项目使用以下字体：

| 字体 | 许可证 | 说明 |
|------|--------|------|
| **Maple Mono NF CN** | 遵循所下载字体发行包附带的许可证 | 中文 Tiles 默认主字体；文件不存入本仓库 |
| **DejaVu Sans** / **DejaVu Sans Mono** | [Bitstream Vera](crawl-ref/docs/license/lgpl.txt) + 公共领域 | 上游 DCSS 字体，可用于其他配置 |
| **Sarasa Mono SC**（可选） | [SIL Open Font License 1.1](https://openfontlicense.org/) | 历史回退方案；不是当前部署必需项 |

部署前请自行取得 `MapleMono-NF-CN-Regular.ttf`，确认其发行包许可证，并按
[`docs/build-workflow.md`](docs/build-workflow.md) 放置。Sarasa 的仓库内许可证副本
见 [`docs/fonts/LICENSE-Sarasa-Gothic.txt`](docs/fonts/LICENSE-Sarasa-Gothic.txt)。

---

*Have fun crawling! 祝探索愉快！🐉*
