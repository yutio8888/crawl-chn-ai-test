# Dungeon Crawl Stone Soup 中文版

*DCSS 0.34.1 Chinese localization and CJK Tiles support*

[![中文项目 CI](https://github.com/yutio8888/crawl-chn-ai-test/actions/workflows/ci.yml/badge.svg)](https://github.com/yutio8888/crawl-chn-ai-test/actions/workflows/ci.yml)

这是基于 Dungeon Crawl Stone Soup（DCSS）0.34.1 的中文本地化分支。项目同时维护
中文界面与游戏文本、TextDB 中文数据，以及 Tiles 模式下的 CJK 字宽和字体渲染。

> 上游说明见 [README.upstream.md](README.upstream.md)，上游构建细节见
> [crawl-ref/INSTALL.md](crawl-ref/INSTALL.md)。

## 当前状态

项目目前已具备可持续开发和验证的完整链路：

- `source.txt`、ZH TextDB 和代码侧 `T_()` 覆盖主要界面、战斗消息、名称与描述文本；
- 显示文本与协议、存档、Lua/API 等内部英文值分离，避免翻译破坏查找和兼容性；
- Tiles 使用显示宽度感知的 CJK 网格与字体渲染，支持中英文混排；
- 控制台、Windows Tiles 和 Android 使用相互隔离的构建目录与 ccache；
- 中文静态检查、运行时测试、术语检查和候选审查均已有统一入口。

覆盖率、条目数和待办状态会持续变化，不在 README 中写死。查看当前 worktree 的中文
校验结果，请运行：

```bash
bash .claude/scripts/verify_zh.sh --profile translation
```

已追踪任务以独立 Issue 仓库的 `INDEX.md` 为准，位置和接入方式见
[docs/issue-tracking.md](docs/issue-tracking.md)；仓库内零散事项见
[docs/known-issues-zh.md](docs/known-issues-zh.md)。

## 快速开始

### 1. 获取源码与依赖

```bash
git clone --recurse-submodules https://github.com/yutio8888/crawl-chn-ai-test.git
cd crawl-chn-ai-test
```

推荐在 Ubuntu、Debian 或 WSL2 中构建。Ubuntu/Debian 的控制台版依赖可用：

```bash
sudo apt install build-essential libncursesw5-dev bison flex liblua5.4-dev \
  libsqlite3-dev libz-dev pkg-config python3-yaml binutils-gold \
  python-is-python3 ccache
```

Tiles 版还需要 SDL2、Freetype、libpng 和 MinGW 等目标相关依赖。其他发行版、macOS、
MSYS2 和 Android 的依赖说明以 [crawl-ref/INSTALL.md](crawl-ref/INSTALL.md) 为准。

### 2. 准备中文配置

`init.txt` 是本地文件，不提交到 Git。首次构建前从受版本控制的中文模板创建：

```bash
cd crawl-ref/source
test -e init.txt || cp init.zh.txt init.txt
```

### 3. 构建并运行控制台版

```bash
bash util/build-console.sh
./crawl
```

该脚本必须从主 worktree 的 `crawl-ref/source/` 运行，并自动使用独立的控制台 ccache。
如需传递 Make 参数，可直接追加在脚本后面。

## Windows Tiles 构建与部署

Windows Tiles 使用专用的 detached worktree，避免 MinGW 对象文件污染主工作区。首次使用时，
从仓库根目录创建并初始化一次：

```bash
git worktree add .worktrees/mingw-tiles --detach HEAD
git -C .worktrees/mingw-tiles submodule update --init --recursive
```

项目不修改或扩展上游 `contrib/fonts` 子模块。请自行取得
`MapleMono-NF-CN-Regular.ttf`，并放入受 Git 忽略的本地字体目录：

```bash
git submodule update --init --recursive
install -m 0644 /path/to/MapleMono-NF-CN-Regular.ttf \
  crawl-ref/source/dat/tiles/MapleMono-NF-CN-Regular.ttf
```

中文默认部署使用 Maple Mono NF CN。渲染器仍支持配置其他 CJK 字体，但字体文件不由本
汉化仓库或其子模块分发。

只构建 `crawl.exe`：

```bash
cd crawl-ref/source
bash util/build-tiles.sh
```

构建并部署完整可运行目录：

```bash
cd "$(git rev-parse --show-toplevel)"
bash .claude/scripts/deploy.sh
```

默认部署到仓库内已忽略的 `.artifacts/windows-tiles/`。需要固定其他位置时：

```bash
cp .dcss-paths.conf.example .dcss-paths.conf
# 在本地配置中设置 DCSS_DEPLOY_ROOT 或 DCSS_WINDOWS_DEPLOY_DIR
bash .claude/scripts/deploy.sh
```

部署脚本会验证中文配置和 Maple 字体、同步并构建专用 worktree、复制运行时数据，并清理
TextDB 缓存以确保文本更新生效。运行中的游戏应先关闭。完整说明见
[docs/build-workflow.md](docs/build-workflow.md)，渲染原理见
[docs/cjk-tiles-architecture.md](docs/cjk-tiles-architecture.md)。

## 如何参与开发

### 开始一个任务

1. 先阅读 [AGENTS.md](AGENTS.md)；使用 Codex、Claude Code 或 OpenCode 时，再读取对应的
   runtime adapter。
2. 从仓库当前默认/集成分支创建任务分支，不要依赖 README 中的静态“活跃分支”清单。
3. 开工前查看独立 Issue 仓库的 `INDEX.md`，确认任务状态、文件所有权和已有分析。
4. 若使用 Git worktree，只能从仓库根目录创建在 `.worktrees/<name>` 下；不要让 linked
   worktree 占用集成分支。

```bash
git fetch origin
git switch -c <topic-branch> origin/HEAD
```

也可以不切换主工作区，直接从当前远端默认分支创建任务 worktree：

```bash
git fetch origin
git worktree add -b <topic-branch> .worktrees/<name> origin/HEAD
```

分支和 worktree 的完整安全约束见
[.agents/policies/worktree-policy.md](.agents/policies/worktree-policy.md)。

### 翻译或中文数据修改

术语以 [docs/glossary.md](docs/glossary.md) 为唯一当前来源；
[docs/decisions.md](docs/decisions.md) 记录裁定理由和历史。编辑前先解析本任务所需的最新
术语上下文：

```bash
bash .claude/scripts/context_resolve.sh "<任务说明>" \
  --task-type translate --files <目标文件...>
```

常见翻译资产位于：

- `crawl-ref/source/dat/i18n/zh/source.txt`：代码和数据使用的主翻译键；
- `crawl-ref/source/dat/descript/zh/`：怪物、物品、能力等描述；
- `crawl-ref/source/dat/database/zh/`：神祇对话、怪物言语和模板文本。

同一任务中的中文翻译资产必须保持单一写入者。修改完成后运行：

```bash
bash .claude/scripts/verify_zh.sh --profile translation
```

### C++、Lua 或 i18n 实现修改

代码侧修改应保持协议值和显示文本分离，不要翻译 JSON key、存档标识、`.des` 标签、Lua
API 值或数据库查找键。新增 `T_()` 调用时，同一任务还要补齐对应中文条目。

```bash
bash .claude/scripts/context_resolve.sh "<任务说明>" \
  --task-type code --files <目标文件...>
bash .claude/scripts/verify_zh.sh --profile code
```

随后按受影响目标执行一次匹配的构建或运行时测试。若一个候选同时修改代码和翻译资产，
可运行一次组合静态预检：

```bash
bash .claude/scripts/verify_zh.sh --profile ci
```

不要对同一个不可变候选依次重复运行 `translation`、`code` 和 `ci`。测试层级、产物位置和
运行时证据见 [docs/zh-testing.md](docs/zh-testing.md)。

### 提交与审查

提交前请确认：

- `git status --short` 只包含本任务改动；
- 已运行与改动类型匹配的验证 profile，并记录命令、退出码和警告；
- 已构建受影响目标，或说明为什么无需构建；
- 新增行为、架构约束或术语决定已经更新对应权威文档；
- 没有修改字体子模块指针，也没有提交字体文件、`init.txt`、构建产物、缓存或部署目录。

翻译相关候选进入合并阶段后，由维护者按不可变 commit 执行
`review_prepare.sh`、机械路由的领域审查、`review_final_gate.sh` 和合并时校验。不要用一次
非正式 review 或单独运行 `--profile review` 代替该流程。详情见
[.agents/policies/review-contract.md](.agents/policies/review-contract.md)。当前 CI 配置以
[.github/workflows/ci.yml](.github/workflows/ci.yml) 为准。

## 开发约束速查

- 用 `strwidth()` 处理显示宽度，不要用字节数或 `string::size()` 对齐 CJK 文本；
- 不要对中文文本调用英文形态变化函数（例如 `conj_verb()`）；
- 不要修改兼作数据库、协议或存档键的英文 `.name` 字段；
- 格式串的参数位置、类型和复数逻辑必须与英文源文本一致；
- 运行时变量经 `T_()` 查找时，必须确保翻译数据库中存在对应键；
- hosted workflow 文件不是普通 Bash/Node.js 脚本，不要直接执行；
- 构建最多使用 8 个 job；多人或多任务同时编译时使用 4 个并避免并发编译风暴。

翻译架构与安全边界的详细说明见
[docs/translation-architecture.md](docs/translation-architecture.md) 和
[.agents/policies/i18n-safety.md](.agents/policies/i18n-safety.md)。

## 项目结构

```text
.
├── AGENTS.md                         # 跨 runtime 的协作入口
├── CODEX.md / CLAUDE.md              # runtime adapter
├── .agents/                          # 共享 policy、角色路由与技能来源
├── .claude/scripts/                  # 验证、审查、部署和辅助脚本
├── .codex/ / .opencode/              # 各 runtime 配置
├── .github/workflows/ci.yml          # 当前 CI 权威配置
├── docs/                             # 架构、术语、构建、测试与协作文档
└── crawl-ref/
    ├── INSTALL.md                    # 上游跨平台依赖与构建说明
    └── source/
        ├── *.cc, *.h                 # 游戏与 i18n 实现
        ├── dat/i18n/zh/source.txt    # 主翻译数据库
        ├── dat/descript/zh/          # 中文描述 TextDB
        ├── dat/database/zh/          # 中文运行时 TextDB
        ├── init.zh.txt               # 中文配置模板
        └── util/build-*.sh            # 目标隔离的构建入口
```

## 相关资源

- [DCSS 上游仓库](https://github.com/crawl/crawl)
- [DCSS 官方主页](https://crawl.develz.org/)
- [DCSS 社区论坛](https://tavern.dcss.io/)
- [r/dcss](https://www.reddit.com/r/dcss/)
- Libera IRC：`#crawl`（玩家）、`#crawl-dev`（开发）

## 许可证

本项目继承上游 DCSS，采用 GPLv2+ 许可证，详见 [LICENSE](LICENSE)。上游贡献者名单见
[crawl-ref/CREDITS.txt](crawl-ref/CREDITS.txt)。

本项目不修改字体子模块，也不分发下列第三方 CJK 字体。用户自行取得字体时，仍须遵守
各字体许可证：

| 字体 | 本地文件名 | 许可证 |
|---|---|---|
| Maple Mono NF CN | `MapleMono-NF-CN-Regular.ttf` | SIL Open Font License 1.1；见 [许可证副本](docs/fonts/LICENSE-Maple-Mono.txt) |
| 更纱黑体（Sarasa Gothic） | `SarasaFixedSC-Regular.ttf`、`SarasaMonoSC-Regular.ttf` | SIL Open Font License 1.1；见 [许可证副本](docs/fonts/LICENSE-Sarasa-Gothic.txt) |
| DejaVu Sans / DejaVu Sans Mono | 上游字体子模块中的 DejaVu 字体文件 | Bitstream Vera 衍生许可，DejaVu 修改部分为公有领域；见 [DejaVu 官方许可证](https://dejavu-fonts.github.io/License.html) |

OFL 1.1 允许字体随软件捆绑和再分发，但字体本身及其修改版本仍须遵守 OFL 条件；用户
复制或再分发字体时，应同时保留许可证副本和版权声明。
