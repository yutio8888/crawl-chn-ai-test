# CJK (中日韩) 字符在 Tiles 版本中的双倍宽度支持

> **历史实现记录。** 本文保留早期双字体方案、问题分析和提交背景，不再
> 定义当前部署配置。当前权威架构见
> [`docs/cjk-tiles-architecture.md`](cjk-tiles-architecture.md)，构建与字体
> 前置条件见 [`docs/build-workflow.md`](build-workflow.md)。

## 概述

DCSS (Dungeon Crawl Stone Soup) 的 Webtiles/本地 tiles 版本最初设计仅支持 ASCII/Latin 字符。中文字符（以及日文、韩文字符）的标准显示宽度是英文字符的 **2 倍**，但游戏引擎将所有字符统一视为单倍宽度。本文档记录了为 tiles 版本添加 CJK 双倍宽度支持的实现方案。

## 架构背景

游戏文字渲染分为两条独立路径：

### 路径 1：TextRegion 网格系统

- **文件**：`tilereg-text.cc` + `fontwrapper-ft.cc:render_textblock()`
- **用途**：消息日志区、游戏主界面文字覆盖层
- **机制**：字符存储在固定大小的 `char32_t cbuf[]` 网格数组中，每个 cell 原本占 1 个字符位置
- **问题**：CJK 字符在网格中占 1 个 cell，但视觉宽度应为 2 个 cell

### 路径 2：FontWrapper 自由形式渲染

- **文件**：`fontwrapper-ft.cc:store()` / `render_string()`
- **用途**：菜单、tooltip、悬停文字、UI 元素
- **机制**：按每个字形的实际 `advance` 值逐字渲染，天然支持 CJK 宽度
- **状态**：✅ 无需修改——`string_width()` 已正确返回 CJK 字符串的像素宽度

### 控制台层（cio.cc）

- **状态**：✅ 已全面使用 `wcwidth()` 处理光标定位、退格、文本编辑

## 三层修改方案

### 第一层：CJK 网格占位（`tilereg-text.cc`）

**文件**：`crawl-ref/source/tilereg-text.cc`

**函数**：`TextRegion::addstr_aux()`

**核心逻辑**：

```cpp
for (int i = 0; i < len && x < mx; i++)
{
    int cw = wcwidth(buffer[i]);
    if (cw < 0) cw = 1;  // 控制字符视为宽度 1

    if (x + cw > mx)     // 行尾截断
        break;

    cbuf[adrs + x] = buffer[i];
    abuf[adrs + x] = text_col;

    // CJK 字符：在相邻 cell 填入 ZWSP 作为"右半部分"占位标记
    if (cw == 2)
    {
        cbuf[adrs + x + 1] = 0x200B;  // ZERO WIDTH SPACE
        abuf[adrs + x + 1] = text_col;
    }

    x += cw;  // CJK 前进 2，ASCII 前进 1
}
print_x = x + cx_ofs;
```

**关键设计决策**：
- 使用 `0x200B`（零宽空格）而非空格作为占位标记，避免与真实空格混淆
- `print_x` 按实际显示宽度前进，而非字符数量

### 第二层：CJK 渲染支持（`fontwrapper-ft.cc:render_textblock()`）

**文件**：`crawl-ref/source/fontwrapper-ft.cc`

**函数**：`FTFontWrapper::render_textblock()`

**核心逻辑**：

```cpp
char32_t ch = chars[i];

// 跳过 CJK 占位标记，不渲染、不前进位置
if (ch == 0x200B)
{
    i++;
    continue;
}

// 背景矩形使用双倍宽度
int char_w = wcwidth(ch);
if (char_w <= 0) char_w = 1;

GLWPrim rect(adv.x, adv.y,
             adv.x + m_max_advance.x * char_w,  // CJK: 2x 宽度
             adv.y + m_max_advance.y);
```

### 第三层：字体回退（`fontwrapper-ft.cc/h`）

**问题**：DejaVu Sans Mono 不含 CJK 字形，中文字符会显示为乱码/方块。

**方案**：实现双字体回退机制，保留 DejaVu 的 metrics 用于布局，缺失的字形从 Sarasa 字体加载。

**新增成员变量**（`fontwrapper-ft.h`）：

```cpp
FT_Face cjk_face;   // CJK 回退字体 face
FT_Byte *cjk_ttf;   // CJK 字体数据（FreeType 不复制，必须保持引用）
```

**字体加载**（`load_font()`）：

```cpp
#define CJK_FALLBACK_FONT "contrib/fonts/SarasaMonoSC-Regular.ttf"
// 加载失败不致命——缺失的字形会使用 MISSING_CHAR
```

**字形查询回退**（`get_glyph_info()`）：

```cpp
FT_Int glyph_index = FT_Get_Char_Index(face, ch);
FT_Face use_face = face;
bool is_cjk = false;

if (!glyph_index && cjk_face)
{
    glyph_index = FT_Get_Char_Index(cjk_face, ch);
    if (glyph_index) { use_face = cjk_face; is_cjk = true; }
}

// 使用 use_face 加载/渲染字形...

// CJK 字形：调整 ascender 与 DejaVu 基线对齐
if (is_cjk)
    glyph.ascender = m_ascender;
```

**字形纹理加载回退**（`load_glyph()`）：

同样的回退逻辑——先尝试主字体，再尝试 CJK 回退字体。

**Atlas 单元格尺寸调整**（`configure_font()`）：

```cpp
// CJK 字形可达 2x 基础 advance，扩大 atlas cell
while (charsz.x <= m_max_advance.x * 2)
    charsz.x *= 2;
```

## 字体配置（历史说明）

本文件记录最初的 DejaVu/Sarasa 双字体实现，不再定义受支持的部署配置。
当前 C++ 默认值以 Maple Mono NF CN 为所有 Tiles 文本角色的主字体；渲染器
仍支持可选回退，但不要求固定的 DejaVu/Sarasa 组合。权威配置、字体放置
位置和部署前置条件见 [`docs/cjk-tiles-architecture.md`](cjk-tiles-architecture.md)
与 [`docs/build-workflow.md`](build-workflow.md)。

## 编译

```bash
cd crawl-ref/source
make CROSSHOST=x86_64-w64-mingw32 TILES=y -j8
# 产物：crawl.exe
```

## 已处理的边缘情况

| 场景 | 处理方式 |
|------|----------|
| CJK 字符在行末溢出 | `x + cw > mx` 时截断，不写入该字符 |
| 光标在 CJK 字符后半部分 | 光标渲染函数临时替换 cell 为 `_`，正常显示 |
| 消息滚动 | 整个 cell 对（CJK + ZWSP）一起滚动，无割裂 |
| 非 CJK 控制字符 | `wcwidth < 0` 时视为宽度 1 |
| CJK 回退字体加载失败 | 非致命错误，缺失字形显示 MISSING_CHAR（¿） |

## CJK 文本编码修复

在 CJK 渲染支持之外，还发现并修复了两个与 CJK 文本编码/损坏相关的深层 bug。

### 问题：MinGW 交叉编译版中文启动崩溃

**现象**：使用 `language=zh` 创建角色退出后再次启动，报错：
```
Unknown species choice: 绪剧休
```

实际应为 `"精灵"`（UTF-8: `e7 b2 be e7 81 b5`），但被错误解码为 `"绪剧休"`（`e7 bb ae e5 89 a7 e4 bc 92`）。

### 根因（双层）

| 层 | 原因 | 文件 | 影响 |
|----|------|------|------|
| 🔴 主因 | `FileLineInput::get_line()` 对无 BOM 文件调用 `mb_to_utf8()` → `mbrtowc` 用 GBK locale 解码 UTF-8 字节 | `unicode.cc:333` | 所有不含 BOM 且包含非 ASCII 内容的 `.prf`/`.des` 文件 |
| 🟡 次因 | `lowercase_string` → `towlower` 对 CJK 字符的 MinGW 兼容性问题 | `stringutil.cc:56` | `from_str_loose`、`str_to_god`、`get_job_by_name` 等通过 `lowercase_string` 查找中文名的所有路径 |

**主因详细机制**：

```
FileLineInput::get_line()
  └─ BOM_NORMAL case → mb_to_utf8(out.c_str())
       └─ mbrtowc(&c, s, MB_LEN_MAX, &ps)
            └─ 用当前 locale 编码解释字节 → MinGW 非 UTF-8 → 损坏
```

| 平台 | locale | `mb_to_utf8` 行为 | 结果 |
|------|--------|-------------------|------|
| Linux (glibc) | UTF-8 | 直接验证 UTF-8 | ✅ 不变 |
| **MinGW (msvcrt)** | C / CP936 / GBK | `mbrtowc` 用 GBK 解释 UTF-8 字节 | ❌ 字符错乱 |

`start-ns.prf` 由 `write_newgame_options_file` 写入中文物种/职业名，不包含 BOM。`FileLineInput` 打开时检测不到 BOM，走 `BOM_NORMAL` 分支调用 `mb_to_utf8`。MinGW 的 `mbrtowc` 用系统 ANSI 代码页（如 CP936）解码 UTF-8 字节，产生完全不同的字符。

### 修复 1：写入 UTF-8 BOM（治本）

**文件**：`initfile.cc:2575-2579`

```cpp
string fn = get_prefs_filename();
FILE *f = fopen_u(fn.c_str(), "w");
if (!f)
    return;
// Write UTF-8 BOM so that FileLineInput uses utf8_validate (BOM_UTF8)
// instead of mb_to_utf8, which corrupts CJK on non-UTF-8 locales (MinGW).
fprintf(f, "\xEF\xBB\xBF");
prefs.write_prefs(f);
```

**原理**：`FileLineInput` 构造函数检测文件开头的 BOM（`unicode.cc:275-298`）。当检测到 `0xEF 0xBB 0xBF`（UTF-8 BOM）时，设置 `bom = BOM_UTF8`。`get_line()` 在 `BOM_UTF8` 分支调用 `utf8_validate()` 而非 `mb_to_utf8()`，直接验证并保留原始 UTF-8 字节，绕过 locale 转换。

### 修复 2：`lowercase_string` CJK 范围保护（防御层）

**文件**：`stringutil.cc:42-65`

```cpp
string lowercase_string(const string &s)
{
    string res;
    char32_t c;
    char buf[4];
    for (const char *tp = s.c_str(); int len = utf8towc(&c, tp); tp += len)
    {
        if (isaalpha(tp[0]))
            res.append(1, toalower(tp[0]));
        else if (c >= 0x2E80 && c <= 0x9FFF)
            // CJK and related scripts have no case — preserve original
            // bytes. iswupper/iswlower may return incorrect values for
            // these ranges on MinGW/msvcrt.
            res.append(tp, len);
        else if (c > 0x7F && !iswupper(c) && !iswlower(c))
            res.append(tp, len);  // skip towlower for non-case symbols
        else
            res.append(buf, wctoutf8(buf, towlower(c)));
    }
    return res;
}
```

**U+2E80–U+9FFF 覆盖范围**：CJK 部首补充、康熙部首、CJK 标点、平假名、片假名、注音符号、CJK 统一汉字、CJK 扩展 A 区。这些区间无大小写属性，直接保留原始字节。

| 字符类别 | 路径 | 行为 |
|---------|------|------|
| ASCII 字母 (a-Z) | `isaalpha` → `toalower` | 正确小写 |
| **CJK (U+2E80–U+9FFF)** | **新增保护** → 保留原始字节 | **不经过 towlower** ✅ |
| 拉丁扩展 (é, ü, ñ) | `iswupper`/`iswlower` → `towlower` | 正确小写 |
| 其他无大小写符号 | `!iswupper && !iswlower` → 保留 | 跳过 towlower |

### 修复 3：Hex 诊断输出（诊断工具，保留）

**文件**：`initfile.cc:1317-1322, 1361-1367`

```cpp
if (ret == SP_UNKNOWN)
{
    string hex;
    for (unsigned char ch : str)
        hex += make_stringf("%02x ", ch);
    mprf(MSGCH_ERROR, "Unknown species choice: %s [hex: %s]\n",
         str.c_str(), hex.c_str());
}
```

错误消息中包含原始字节的十六进制表示，便于未来诊断 CJK 编码问题。

### 相关提交

| 提交 | 说明 |
|------|------|
| `7232fc86` | `lowercase_string` 的 `iswupper`/`iswlower` 保护 (v1) |
| `a0900219` | 改用 Unicode 范围 `0x2E80–0x9FFF` 直接判断 (v2) |
| `768cd197` | 添加 hex 诊断输出 |
| `ca2ec438` | **主修复**：`write_newgame_options_file` 写入 UTF-8 BOM |

### 经验教训

1. **`mb_to_utf8` 是跨平台文本处理的隐性陷阱**。在 Linux（UTF-8 locale）上是无害的恒等变换，在 Windows（非 UTF-8 locale）上是字符损坏引擎。
2. **任何写入后被 `FileLineInput` 读回的文件，如果包含非 ASCII 内容，必须带 BOM 或以其他方式确保走 `BOM_UTF8` 路径**。
3. **`towlower` 在 MinGW 上不可靠**。即使 locale 问题解决，也不应将 CJK 字符传递给 `towlower`。Unicode 范围直接判断比 `iswupper`/`iswlower` 更可靠。
4. **双重根因叠加**。两个独立 bug（`mb_to_utf8` locale 转换 + `towlower` CJK 处理）叠加，仅修复任何一个都不够。

## CJK UI 布局修复

CJK 字符宽度为 ASCII 的 2 倍，使用 `%-Ns` 等字节宽度格式化会导致列对齐错乱。以下修复使用 `chop_string()`（基于 `wcwidth()` 的显示宽度截断）替代硬编码空格/字节宽度格式化。

### 列标题对齐

**文件**：`spl-cast.cc`, `chardump.cc`, `ability.cc`, `spl-book.cc`, `describe-spells.cc`

**问题**：法术菜单、能力菜单、法术书描述的列标题（`威力`/`伤害`/`范围`/`学派`/`失败率`/`消耗` 等）使用硬编码 ASCII 空格对齐，CJK 字符导致列偏移。

**修复**：使用 `chop_string()` 重建列标题，基于数据列的实际显示宽度计算间距，而非固定空格数。

| 文件 | 影响 UI |
|------|---------|
| `spl-cast.cc` | 法术列表 — 威力/伤害/范围/噪音 列标题 |
| `chardump.cc` | 角色 dump — 法术列表输出 |
| `ability.cc` | 能力菜单 — 消耗/失败率 列标题 |
| `spl-book.cc` | 法术书 — 学派/失败率 列标题 |
| `describe-spells.cc` | 法术描述 — 法术/学派/等级/已知 标题 |

### 技能菜单对齐

**文件**：`skill-menu.cc`

**问题**：技能名使用 `%-15s`（15 字节宽度）格式化，CJK 技能名（如"锤与链枷"= 8 字节但显示宽度 = 8 cells）不兼容字节宽度对齐。

**修复**：替换 `%-15s` 为 `chop_string(skill_name, 15)`，基于显示宽度截断。

### 怪物面板布局

**文件**：`describe.cc`, `mon-info.cc`

**问题**：怪物信息面板的 `TablePrinter` 使用 `codepoints()` 而非 `wcwidth()` 计算列宽，导致中文标签（如 `再生: 1/回合`）溢出换行。

**修复**：
- `_str_display_width()` — 基于 `wcwidth()` 的显示宽度计算
- `_pad_to_display_width()` — 基于显示宽度的填充
- 替换 `codepoints()` 调用为以上两函数

### 中文代词支持

**文件**：`mon-util.cc`, `mon-info.cc`

**问题**：怪物描述中 `decline_pronoun()` 仅返回英文代词（`It`/`its`/`it`），中文句中出现英文代词残留。

**修复**：添加 `_pronoun_declension_zh` 表，支持 它/他/她/你/它们 五种代词的中文变格（主格/所有格/宾格/反身代词）。

## 当时未实现的 TODO

下面是历史实现批次留下的观察，不是当前 backlog。若在当前默认分支仍可复现，
应通过 GitHub Issue 记录新的版本、平台和验证证据。

- **组合字符**（`wcwidth == 0`）：如变音符号、泰文声调等，当时的代码将其视为宽度 1 的普通字符，候选改进是将组合字符与前一个基础字符合并渲染。

## 中文翻译工作

在实现 CJK 双倍宽度支持的同时，进行了全面的中文本地化翻译，覆盖 **40+ 个源文件**。

### 翻译类别

| 类别 | 内容 | 主要文件 |
|------|------|----------|
| 游戏日志 | 怪物进出视野、攻击消息、拾取、死亡 | `delay.cc`, `mon-act.cc`, `items.cc`, `message.cc` |
| 怪物攻击动词 | 25+ 种攻击方式 (咬/爪击/刺/啄等) | `mon-util.cc`, `melee-attack.cc` |
| UI 面板 | 快捷动作(Q)、装备(W)、法术(I)、角色(E) | `quiver.cc`, `item-use.cc`, `spl-cast.cc`, `main.cc` |
| 瞄准界面 | 按键提示、风险、目标选择 | `directn.cc`, `quiver.cc`, `spl-cast.cc` |
| 物品栏 | 20+ 条错误提示 | `invent.cc` |
| 地形描述 | 门、祭坛、楼梯 | `directn.cc` |
| 种族选择 | 难度标签 | `species-groups.h` |
| 法术名称 | 14 个英文法术名 | `dat/descript/zh/spells.txt` |
| 怪物描述 | 攻击表头、速度、投掷 | `describe.cc`, `mon-info.cc`, `mon-cast.cc` |
| 命令帮助 | 装备/穿戴/持握命令 | `command.cc` |
| 商店/金币 | 金币数量、购买提示 | `shopping.cc`, `main.cc` |

### Bug 修复

| Bug | 文件 | 修复 |
|-----|------|------|
| `language = zh` 启动崩溃 | `species.cc` | `get_species_zh_name()` 返回 `nullptr` 时崩溃 — 添加 null 检查 |
| 中文日志出现多余分号 | `message.cc` | `_ends_in_punctuation()` 不识别中文标点 — 添加中文标点检查 |
| CJK 字形高低不一 | `fontwrapper-ft.cc` | 强制 ascender 覆盖导致不同汉字视觉高度不同 — 移除覆盖，使用原生 ascender |
| **CJK 编码：启动后物种名错乱** | `unicode.cc` + `initfile.cc` | `FileLineInput::get_line()` → `mb_to_utf8()` 在 MinGW 上用 GBK locale 解码 UTF-8 字节 — `write_newgame_options_file` 写入 UTF-8 BOM 强制走 `BOM_UTF8` 安全路径 |
| **CJK 编码：`towlower` 损坏 CJK** | `stringutil.cc` | `lowercase_string` 对所有非 ASCII 调用 `towlower`，MinGW 上不可靠 — 对 U+2E80–U+9FFF 范围直接保留原始字节 |
| **法术/能力菜单列标题错位** | `spl-cast.cc`, `ability.cc`, `spl-book.cc`, `describe-spells.cc`, `chardump.cc` | 硬编码 ASCII 空格对齐列标题 — 使用 `chop_string()` 基于显示宽度重建 |
| **技能菜单 CJK 名溢出** | `skill-menu.cc` | `%-15s` 字节宽度格式化 — 替换为 `chomp_string(skill_name, 15)` |
| **怪物面板中文标签溢出** | `describe.cc`, `mon-info.cc` | `TablePrinter` 用 `codepoints()` 计算列宽 — 改用 `_str_display_width()` / `_pad_to_display_width()` 基于 `wcwidth()` |
| **怪物描述中出现英文代词** | `mon-util.cc`, `mon-info.cc` | `decline_pronoun()` 仅返回英文 — 添加 `_pronoun_declension_zh` 表 |

## 编译与部署

### 依赖

- GCC / `x86_64-w64-mingw32-g++` (交叉编译)
- FreeType, SDL2, SDL2-image, libpng, zlib, lua, sqlite, pcre
- 预编译 MinGW contrib 库: `contrib/install/x86_64-w64-mingw32/lib/`

### 编译命令

**WSL 控制台版（调试用）：**
```bash
cd crawl-ref/source
make -j8
# 产物: crawl-ref/source/crawl
```

**Windows Tiles 版：**
```bash
cd crawl-ref/source
make CROSSHOST=x86_64-w64-mingw32 TILES=y -j8
# 产物: crawl-ref/source/crawl.exe
```

### 部署路径

- 仓库内产物目录示例：`.artifacts/windows-tiles/`
- 外部游戏目录：通过 `deploy.sh` 参数或 `DCSS_WINDOWS_DEPLOY_DIR` 指定
- 需同步复制：`crawl.exe`、`dat/` 和版本化字体；`init.txt` 仅用于可选覆盖
