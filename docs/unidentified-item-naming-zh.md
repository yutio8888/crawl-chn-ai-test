# 未鉴定药水与卷轴的中文命名方案

> **0.34.1 下游实现记录。** 本文描述的药水限定词和卷轴外观方案已经进入当前
> 代码；它不是待实施提案。文末“未覆盖项”只记录当时的范围边界，当前待办以
> [GitHub Issues](https://github.com/yutio8888/crawl-chn-ai-test/issues) 为准。

## 问题

未鉴定物品通过随机外观描述来区分不同子类型：

- **药水**：修饰词 + 颜色 + "potion"（如 "bubbling blue potion"）
- **卷轴**：`make_name(seed, MNAME_SCROLL)` 生成拉丁字母标签（如 "scroll labelled YSTORVO GHEMMI"）

在以 `0.34.1` 为基线的早期下游候选中，结构词（“药水”“卷轴”）已经中文化，
但内容词尚未翻译：

- 药水输出 `fizzy yellow药水`（修饰词和颜色仍是英文）
- 卷轴输出 `标有YSTORVO GHEMMI的卷轴`（拉丁标签未处理）

## 设计约束

1. **不在游戏代码内引入额外的中文字符串** — 中文内容通过 T_() 进入
   `dat/i18n/zh/source.txt`，或放在独立的 `zh-*.h/.cc` 文件中
2. `subtype_rnd` 存储格式不变 — 确保存档兼容和中英切换正常
3. 英文模式完全不受影响

## 药水方案：T_() 包裹描述符

### 原理

`potion_qualifiers[]` 和 `potion_colours[]` 原本是裸 `const char*` 数组，不经过
T_()。且英文修饰词带有尾随空格（`"bubbling "`），无法直接作为 T_() key。

修改分两步：

1. **去除尾随空格**：修饰词 key 从 `"bubbling "` 变为 `"bubbling"`，空格在组装时显式添加
2. **T_() 包裹**：`T_(qualifier)` / `T_(clr)` 自动查找中文翻译

### 组装逻辑

```cpp
const char *t_qual = T_(qualifier);
const char *t_clr   = T_(clr);

if (Options.language == lang_t::ZH)
    buff << t_qual << t_clr << T_("potion");        // "冒泡的蓝色药水"
else
{
    buff << t_qual;
    if (qualifier[0] != '\0')
        buff << ' ';                                // EN 显式空格
    buff << t_clr << ' ' << T_("potion");           // "bubbling blue potion"
}
```

### 翻译对照表

#### 修饰词（15 种）

| EN | ZH | 说明 |
|----|----|------|
| (empty) | (empty) | 无修饰词 |
| bubbling | 冒泡的 | 大泡翻腾 |
| fuming | 冒烟的 | 散发烟雾（主动） |
| fizzy | 起泡的 | 细小气泡 |
| viscous | 粘稠的 | 浓稠流动 |
| lumpy | 块状的 | 有块状物 |
| smoky | 烟熏的 | 有烟味（被动） |
| glowing | 发光 | 已存在于 source.txt，不重复添加 |
| sedimented | 有沉淀的 | 底部有沉淀 |
| metallic | 金属色的 | 金属光泽 |
| murky | 浑浊的 | 不透明浑浊 |
| gluggy | 咕嘟的 | 粘稠到发出咕嘟声 |
| oily | 油性的 | 油状液体 |
| slimy | 黏滑的 | 滑腻质感 |
| emulsified | 乳化的 | 乳状混合 |

> **注意**："fuming"（冒烟的）与 "smoky"（烟熏的）的区分：
> fuming 强调主动散发烟雾/蒸汽，smoky 强调被烟熏过的气味。

#### 颜色（22 种）

| EN | ZH | EN | ZH |
|----|----|----|----|
| blue | 蓝色 | black | 黑色 |
| silvery | 银色 | cyan | 青色 |
| purple | 紫色 | orange | 橙色 |
| inky | 墨色 | red | 红色 |
| yellow | 黄色 | green | 绿色 |
| brown | 棕色 | ruby | 红宝石色 |
| white | 白色 | emerald | 祖母绿色 |
| grey | 灰色 | pink | 粉红色 |
| coppery | 铜色 | golden | 金色 |
| dark | 深色 | puce | 暗红色 |
| amethyst | 紫晶色 | sapphire | 蓝宝石色 |

### 翻译存储

所有翻译条目位于 `crawl-ref/source/dat/i18n/zh/source.txt`，通过标准
`%%%%` 分隔符追加。共新增 36 条（修饰词 14 条 + 颜色 22 条；"glowing"
已存在故跳过）。

## 卷轴方案：中文外观描述系统

### 设计思路

放弃 `make_name(MNAME_SCROLL)` 的拉丁字母标签，改为两维度物理外观描述，
与药水的 qualifier × colour 结构对齐。

### 数据流

```
subtype_rnd (uint32_t, 保持 make_name seed 编码不变)
    │
    ├─ EN: make_name(subtype_rnd, MNAME_SCROLL) → "YSTORVO GHEMMI"
    │
    └─ ZH: 从 seed 派生出 binding/seal 索引
              binding = (subtype_rnd >> 4) % 12
              seal    = (subtype_rnd >> 12) % 10
              组装: scroll_binding_zh[binding] + scroll_seal_zh[seal]
                   + "的" + T_("scroll")
```

关键设计决策：
- `subtype_rnd` 存储格式不变（保持 `make_name` seed），EN 端完全不受影响
- ZH 端通过位运算从 seed 派生出 binding/seal 索引，纯确定性映射
- `>>4` 和 `>>12` 取 seed 不同位段，确保不同 seed 产生不同外观组合
- 无需修改 `ng-init.cc` 的初始化逻辑
- 无需修改存档格式

### 新增文件

#### `zh-scroll-appearance.h`

```cpp
enum scroll_binding_type {
    SBI_RED_SILK, SBI_BLUE_SILK, SBI_HEMP_CORD, SBI_GOLD_THREAD,
    SBI_SILVER_THREAD, SBI_LEATHER_CORD, SBI_GREEN_SILK, SBI_PURPLE_SILK,
    SBI_BLACK_THREAD, SBI_WHITE_SILK, SBI_COPPER_CHAIN, SBI_PLAIN_BAND,
    NDSC_SCROLL_BINDING
};

enum scroll_seal_type {
    SSE_WAX, SSE_GOLD_FOIL, SSE_SILVER_FOIL, SSE_BONE_CLASP,
    SSE_JADE_CLASP, SSE_COPPER_CLASP, SSE_TIN, SSE_SEALING_WAX,
    SSE_TALISMAN, SSE_NONE,
    NDSC_SCROLL_SEAL
};
```

#### `zh-scroll-appearance.cc`

中文外观字符串数组，所有中文字符集中于此文件，不散落于游戏逻辑代码中。

### 中文外观描述

#### 捆扎物（12 种）

| 枚举 | 中文 | 含义 |
|------|------|------|
| SBI_RED_SILK | 红绸带 | 红色丝绸带 |
| SBI_BLUE_SILK | 蓝绸带 | 蓝色丝绸带 |
| SBI_HEMP_CORD | 麻绳 | 粗麻绳 |
| SBI_GOLD_THREAD | 金丝线 | 金色丝线 |
| SBI_SILVER_THREAD | 银丝线 | 银色丝线 |
| SBI_LEATHER_CORD | 皮绳 | 皮革绳 |
| SBI_GREEN_SILK | 绿绸带 | 绿色丝绸带 |
| SBI_PURPLE_SILK | 紫绸带 | 紫色丝绸带 |
| SBI_BLACK_THREAD | 黑丝线 | 黑色丝线 |
| SBI_WHITE_SILK | 白绸带 | 白色丝绸带 |
| SBI_COPPER_CHAIN | 铜链 | 铜质细链 |
| SBI_PLAIN_BAND | 素色带 | 无染色束带 |

#### 封印/特征（10 种）

| 枚举 | 中文 | 含义 |
|------|------|------|
| SSE_WAX | 蜡封 | 普通蜡封 |
| SSE_GOLD_FOIL | 金箔封 | 金箔封口 |
| SSE_SILVER_FOIL | 银箔封 | 银箔封口 |
| SSE_BONE_CLASP | 骨扣 | 骨制扣环 |
| SSE_JADE_CLASP | 玉扣 | 玉制扣环 |
| SSE_COPPER_CLASP | 铜扣 | 铜制扣环 |
| SSE_TIN | 锡封 | 锡制封印 |
| SSE_SEALING_WAX | 火漆印 | 火漆印章 |
| SSE_TALISMAN | 符纸封 | 符纸封印 |
| SSE_NONE | (空) | 无封印，组装时省略 |

### 示例输出

| binding | seal | 输出 |
|---------|------|------|
| 红绸带 | 蜡封 | 红绸带蜡封的卷轴 |
| 麻绳 | 骨扣 | 麻绳骨扣的卷轴 |
| 金丝线 | 火漆印 | 金丝线火漆印的卷轴 |
| 皮绳 | (无) | 皮绳的卷轴 |
| 素色带 | 符纸封 | 素色带符纸封的卷轴 |

### 组合数

12 捆扎物 × 10 封印 = 120 种组合。seed 的 32 位空间足够覆盖。

## 语言切换安全性

`subtype_rnd` 是一个 `uint32_t` 数值。药水和卷轴各自以不同方式编码这个数值，
但编码本身是**语言无关的**——切换语言只是用不同的方式解读同一个数字。

| 场景 | ZH → EN | EN → ZH |
|------|---------|---------|
| 药水 | `T_("bubbling")` 从 "冒泡的" 变为 "bubbling" ✓ | 反向亦然 |
| 卷轴 | `(seed>>4)%12` → 不再使用；改用 `make_name(seed)` → 拉丁标签 ✓ | 反向亦然 |
| 鉴定后 | 走 `identified` 分支，`T_()` 自动切换 ✓ | 同上 |

中英文互相切换后，未鉴定物品名称正常显示，不会出现乱码、crash 或空白。

## 涉及文件

| 文件 | 改动 |
|------|------|
| `crawl-ref/source/item-name.cc` | 药水修饰词去尾随空格 + T_() 包裹；卷轴 ZH 分支改用外观系统 |
| `crawl-ref/source/dat/i18n/zh/source.txt` | 新增 36 条翻译（修饰词 14 条 + 颜色 22 条） |
| `crawl-ref/source/zh-scroll-appearance.h` | **新增** — 枚举定义 + extern 声明 |
| `crawl-ref/source/zh-scroll-appearance.cc` | **新增** — 中文外观数组（捆扎物 12 条 + 封印 10 条） |
| `crawl-ref/source/Makefile.obj` | 添加 `zh-scroll-appearance.o` |
| `crawl-ref/source/Makefile` | `OBJECTS += zh-scroll-appearance.o` |

## 当时未覆盖的范围

下表记录该实现批次没有处理的物品类型，不表示它们在当前默认分支仍必然存在同样
问题。需要行动时应先用当前构建复现，再由 GitHub Issue 跟踪。

以下未鉴定物品类型暂未纳入本次修改，但存在同样的"半翻译"问题：

| 物品类型 | 当前中文输出 | 外观维度 |
|----------|-------------|---------|
| 魔杖 (wand) | `iron jewelled wand` → 英文不变 | 材质 × 特征 |
| 戒指 (ring) | `wooden encrusted ring` → 英文不变 | 材质 × 特征 |
| 项链 (amulet) | `sapphire dented amulet` → 英文不变 | 材质 × 特征 |
| 法杖 (staff) | `glowing crooked staff` → 英文不变 | 特征 × 形状 |

当时建议后续按同样模式评估这些类型（魔杖/戒指/项链/法杖可考虑走 T_()，
因为描述词英文本身有意义）；当前是否仍需该方案必须重新验证。
