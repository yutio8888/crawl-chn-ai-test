# 物品中文命名设计文档

## 1. 背景

DCSS 物品名称的翻译通过**两个层面**协作完成：

- **T_() 查表**（source.txt）：基础名、品牌名、效果名的英文→中文映射
- **C++ 结构性代码**（item-name.cc / artefact.cc）：中英文不同的语序（"X of Y" → "Y之X"）

当前系统已实现大部分物品的翻译覆盖，但在命名一致性上存在一些问题。

## 2. 当前物品命名系统架构

```
item.name(desc, terse, ident)
  └─ name_aux()                          [item-name.cc:_name_*]
       ├─ OBJ_WEAPONS  → _name_weapon()  [brand desc + base name]
       ├─ OBJ_ARMOUR   → name_aux()       [ego desc + base name]
       ├─ OBJ_POTIONS  → name_aux()       [effect + "药水"]
       ├─ OBJ_SCROLLS  → name_aux()       [effect + "卷轴"]
       ├─ OBJ_WANDS    → name_aux()       [effect + "魔杖"]
       ├─ OBJ_STAVES   → name_aux()       [type + "法杖"]
       ├─ OBJ_BOOKS    → name_aux()       [type + "之书"]
       ├─ OBJ_JEWELLERY → jewellery_type_name()
       │     └─ make_stringf_p(T_("%1$s %2$s"), cls, effect)
       │        cls = T_("ring of") / T_("amulet of")
       │        effect = jewellery_effect_name(type)
       ├─ OBJ_TALISMANS → talisman_type_name()
       └─ 神器        → get_artefact_name() [+ T_() on unrand names]
```

### 结构性改变（ZH vs EN）总结

| 模式 | EN | ZH | 代码位置 |
|------|-----|----|---------|
| 品牌（adj类） | `flaming sword` | `烈焰之剑` | item-name.cc:1700 |
| 品牌（非adj类） | `sword of protection` | `防护之剑` | item-name.cc:1709-1712 |
| 护甲附魔 | `robe of fire resistance` | `火焰抗性之袍` | item-name.cc:1930-1941 |
| 弹药品牌 | `dart of venom` | `剧毒之飞镖` | item-name.cc:1857-1860 |
| 药水 | `potion of curing` | `治疗药水` | item-name.cc:1999-2002 |
| 魔杖 | `wand of flame` | `火焰魔杖` | item-name.cc:1959-1962 |
| 法杖 | `staff of fire` | `火焰法杖` | item-name.cc:2203-2229 |
| 卷轴 | `scroll of identify` | `鉴定卷轴` | item-name.cc:2070 |
| 书籍 | `book of Fire` | `火焰之书` | item-name.cc:1568-1570 |
| 手册 | `manual of Long Blades` | `长剑手册` | item-name.cc:1490-1494 |
| 珠宝 | `ring of protection` | `防护戒指` | item-name.cc:1173 → `%2$s%1$s` |
| 神器 | `sword of Cerebov` | `赛瑞博之剑` | artefact.cc:1681-1691 |

## 3. 发现的问题

### 问题 1：珠宝命名缺"之"

**现状**：
- 武器品牌：`烈焰之剑`（"之"）
- 护甲附魔：`火焰抗性之袍`（"之"）
- 弹药品牌：`剧毒之飞镖`（"之"）
- **珠宝：`防护戒指`**（无"之"）

**根因**：`jewellery_type_name()` 使用 `make_stringf_p(T_("%1$s %2$s"), cls, effect)`。其中：
- `cls` = T_("ring of") → "戒指"
- `effect` = T_("protection") → "防护"
- 中文格式串：`%2$s%1$s` → "防护戒指"

而 D-B-001（品牌属格统一）规定 `Y之X` 格式。珠宝也应遵循同一原则。

**影响范围**：所有戒指和项链的显示名称。

### 问题 2：~~死代码 `zh_weapon_brands_*` 数组~~ 已确认不存在

经验证：当前代码库中没有 `zh_weapon_brands_terse[]` 或 `zh_weapon_brands_adj[]`。品牌名翻译全部通过 T_() + source.txt 管理。

（早期分析中的误报来源于子代理报告混淆。）

### 问题 3：翻译原则缺失文档

DECISIONS.md 中有 D-B-001（品牌属格→之），但未扩展到珠宝、护甲、弹药等领域。需要统一的原则文档。

## 4. 设计方案

### 4.1 珠宝命名修复（高优先级）

**目标**：`防护戒指` → `防护之戒指`，统一遵循 D-B-001。

**方案**：修改 `jewellery_type_name()` 的格式串，使中文模式下输出 `effect之cls`。

具体改动：
1. 在 source.txt 中将 `%1$s %2$s` → 的翻译从 `%2$s%1$s` 改为 `%2$s之%1$s`
2. 确认 "ring of" → "戒指" 和 "amulet of" → "项链" 的翻译保持不变

**影响**：
| 当前 | 修改后 |
|------|--------|
| 防护戒指 | 防护之戒指 |
| 火焰抗性戒指 | 火焰抗性之戒指 |
| 再生项链 | 再生之项链 |
| 守护之灵项链 | 守护之灵之项链？→ 需注意"之之"问题 |

**注意**：部分珠宝效果名本身已含"之"（如 `guardian spirit` → "守护之灵"），拼接后可能出现"守护之灵之项链"。需特殊处理——效果名中已有"之"的，珠宝层不再加。

### 4.2 翻译原则文档（高优先级）

**方案**：在 DECISIONS.md 中添加 Type-B 规则，明确物品命名原则。

## 5. 实施计划

### Phase 1：原则文档 ✅（已完成）
1. 更新 DECISIONS.md，新增 D-B-013 至 D-B-016
2. 覆盖所有物品类别的命名规则、结构模式、品牌词典

### Phase 2：珠宝"之"修复（待定——详见"未解决的问题"）
1. 检查 source.txt 中 `%1$s %2$s` 条目 → 将 `%2$s%1$s` 改为 `%2$s之%1$s`
2. 检查是否有珠宝效果名含"之"导致双"之之"问题 → 列出例外清单
3. 编译验证 + verify_zh

## 6. 未解决的问题

1. **部分翻译可能需重新审校**：当前 source.txt 中的 weapon_ego 条目（如 DRag→雷击、repulsion→排斥等）是否与游戏内效果描述一致，需逐个验证。
2. **珠宝"之之"问题**：需枚举所有珠宝效果名，标记已含"之"的条目，在代码中做去重处理。
3. **品牌名与附魔名的同词异译**：如 "protection" 作为武器品牌→"防护"，作为护甲附魔→"防护"（AH+3 名称），作为戒指效果→"防护"——目前相同，但未来可能需要 C_() 消歧。
