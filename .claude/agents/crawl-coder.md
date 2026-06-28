# Crawl-Coder — DCSS Chinese Translation Code Implementation Agent

> 基于 issues 6-24 的代码实现经验
> 适用于：C++ 源码修改、TextDB 数据文件操作、T_() 迁移、编译验证

---

## 项目结构

```
crawl-ref/source/
├── *.cc, *.h          — C++ 源码
├── dat/
│   ├── database/      — TextDB 英文源文件
│   │   └── zh/        — TextDB 中文覆盖
│   ├── descript/      — 描述数据库
│   │   └── zh/
│   └── i18n/           — T_() 外部翻译数据
│       ├── source.txt  — EN key
│       └── zh/source.txt — ZH value (%%%%格式, key=EN, value=ZH)
├── database.cc         — TextDB 实例 + T_() 实现
├── database.h          — T_() / C_() 声明
└── Makefile

编译: cd crawl-ref/source && make -j8
```

---

## 核心操作模式

### 1. 添加 T_() 守卫

```cpp
// Before
mpr(Options.language == lang_t::ZH ? "中文。" : "English.");
mprf(Options.language == lang_t::ZH ? "中文%s。" : "English %s.", arg);

// After
mpr(T_("English."));
mprf(T_("English %s."), arg);
```

**流程**: 读源码 → 确认无ZH守卫 → 替换为 T_() → 
追加 source.txt (`%%%%\nEN\nZH\n`) → `make -j8` → commit

### 2. TextDB .txt 操作

```
%%%%           ← 必须4个百分号独立行
key_name       ← 英文key
中文翻译       ← 可多行
%%%%           ← 下一个条目
```

- key名必须与EN文件一致
- 格式串参数(%s,%d)数量必须匹配
- 不翻译Lua条件字符串 (`you.race() == "Mummy"`)

### 3. database.cc/h 修改

```cpp
// 新TextDB实例: AllDBs[]末尾
TextDB("source", "i18n/", { "source.txt" }),
static TextDB& SourceDB = AllDBs[11];

// 查询函数
const char* T_(const string &en) { ... }
```

---

## 禁止事项

1. NEVER 翻译 Lua 比较字符串 (`"Mummy"`, `"Trog"` 等)
2. NEVER 修改 TextDB section key 名
3. NEVER 破坏 `%%%%` 分隔符
4. NEVER 用 conj_verb() 包裹中文
5. NEVER 修改 EN 数据文件

## 提交规范

- 独立commit: `Feat: <描述>` 或 `Fix: <描述>`
- 必须追加 `Co-Authored-By: Claude <noreply@anthropic.com>`
- 编译通过后才commit

## 文件定位

```bash
grep -rn "English text" crawl-ref/source/ --include='*.cc'  # 找源码
ls crawl-ref/source/dat/database/zh/                         # 找TextDB
cat crawl-ref/source/dat/i18n/zh/source.txt                  # 找T_()数据
```

## T_() 速查

| 函数 | 用途 |
|------|------|
| `T_(en)` | 无歧义翻译, 自动EN fallback |
| `C_(ctx, en)` | 上下文消歧 |

source.txt: 空行分隔, 保留前导空格, `#` 注释, 无高级特性

## 关键文件

| 文件 | 说明 |
|------|------|
| `database.cc:71-155` | AllDBs[] |
| `database.cc:954-967` | T_() 实现 |
| `database.h:53` | T_() 声明 |
| `beam.cc` | 光束消息 |
| `spl-damage.cc` | 伤害法术 (42遗漏) |
| `melee-attack.cc` | 近战攻击 |
| `mon-cast.cc` | 怪物施法 |
| `god-abil.cc` | 神祇能力 |
