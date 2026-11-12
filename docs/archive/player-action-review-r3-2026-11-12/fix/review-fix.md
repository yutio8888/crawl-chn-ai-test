# 第三轮玩家动作语句修复：独立只读复审

- 复审者：Claude Opus 5.5（只读；读过术语表与裁决，不是盲评）
- 对象：
  - trunk PR #315 @ `e88dc9a326c6a0ccd5ef118c13ed7590a8657ddf`（基线 `40a7b9976a`）
  - stable PR #316 @ `580ad4741fa104b32d54835a9264c9c6cfcf11fb`（基线 `4af734c175`）
- 依据：两条线基线到 head 的完整 diff；source.txt 与 database.cc 的解析和查找代码；各消费者的源码；两条线的 i18n.h、stringutil.h。

## 结论

| 线 | 结论 |
|---|---|
| trunk #315 | **Ready**（无 Blocking） |
| stable #316 | **Ready**（无 Blocking） |

- 前提：两个 PR 的 CI 在 13:4x UTC 查询时仍在运行（trunk 2 项成功、2 项跳过、7 项进行中；stable 1 项成功、2 项跳过、8 项进行中）。合并须等适用 CI 全部通过。
- 下文 Non-blocking 各条都不阻塞合并。

## 1. 两条裁决前提的更正：写入者正确

- **解析规则**：database.cc `_parse_text_db` 会对每个值调用 `_trim_leading_newlines(value)`，并对每一行值做 `trim_string_right(line)`。因此“键行、空行、正文”这种写法的值就是空行之后的正文，不是空值。stable 的 source.txt 里有 1881 个条目采用这种写法。
- `i18n_source_lookup` 只在取回值为空时才回退，并且只剥掉末尾的 `\n`。
- **F-03**：
  - `constrictor possessive|the roots'`、`|the zombie hands'`、`|the vines'`、`|something's` 的值分别是“树根的”“尸手的”“藤蔓的”“某物的”，都不是空值。
  - 旧译 `%s对你的掌控…` 代入真实参数后，得到的是“兽人的对你的掌控”“树根的对你的掌控”。
  - 新译 `%s束缚减弱了…` 与 trunk 现行键 `%s hold on you weakens` 的译文一致。
  - 消费者 stable `player.cc:8644`，已核对。
- **D-HERE-16**：
  - `There is ` 的值是“这里有 ”，行尾空格被 `trim_string_right` 剥掉后实际为“这里有”。
  - `There is an entrance to ` 的值是“有一个通往”。
  - 旧拼接结果因此是“这里有向下的楼梯。”和“有一个通往杂货铺。”。后者缺“的入口”和主语，确实是缺陷。
  - 所以前提“前缀为空”不成立，但修复本身仍然必要；新整句与 trunk `directn.cc:3067` 一致。

## 2. 英文逐字节不变、机制不变：通过

- **B-03 墙体碎裂**：
  - 原来是 `"%s %s shatters…"` 配 `T_("The")/T_("Some")`，英文下得到 “The rock …” 和 “Some rock …”。
  - 新整句 `The %s …` / `Some %s …` 输出相同。
  - `agent() && agent()->is_player()` 判断原样传入，材质判断没变。
  - 与 trunk `beam.cc:982` 的写法一致。
- **describe.cc 编号占位符**：
  - 改用 `make_stringf_p`，参数顺序仍是 feature 在前、key 在后。`%1$s`、`%2$s` 在英文里按顺序展开，输出相同。
  - 中文通过编号调换显示位置，不交换业务参数。
  - 两条键与 trunk `describe.cc:3777/3853` 字面相同。
- **directn.cc 脚下地形**：
  - 原来是 `prefix + feat + " here."`，新整句为 `There is %s here.` / `There is an entrance to %s here.`，英文相同。
  - 删除 `DNGN_ENTER_SHOP` 的 case 后，商店判断改为 `grid == DNGN_ENTER_SHOP` 传入。地板、泥地、水、岩浆的提前返回，以及后续装饰提示，都保留了。
- **player-reacts.cc 分隔符**：
  - stringutil.h:242 的原默认值是 `andc = T_(" and ")`、`comma = ", "`。
  - 新代码在英文下传入 `T_(" and ")` 和 `", "`，与默认值完全一致。
  - 中文下传入 `T_(",")`，已有键的值是“、”，同一做法 `skill-menu.cc:621/661` 早已在用。
  - 整段与 trunk `player-reacts.cc:1307-1312` 逐字相同。
  - `"amulet"` 改为 `T_("amulet")`，英文不变。
  - 上游 stable 的 `attune%2$s` 配 `"attunes itself"` 会产生 “attuneattunes”，这一处原样保留，符合逐字节不变的要求。
- **E-03 英雄消息**：只补了 `T_`，选择条件和持续时间都没变。

## 3. klown pie：通过

- **只作用于显示层**：
  - `NC_` 定义为 `_i18n_deferred_context("" ctx, "" en)`，是 constexpr，直接返回 `en`（i18n.h:34-43）。所以 `pie_effect.desc` 仍是英文身份。
  - 权重、valid、effect 的 lambda 都没有改动（diff 只涉及 6 个 desc 字面量）。
- **两个调用点都已覆盖**：
  - 命中玩家：trunk 4615 / stable 4584，条件 `origin_spell==SPELL_THROW_PIE && final_dam>0` 不变。
  - 命中可见怪物：trunk 5406 / stable 5358，条件 `you.see_cell` 不变。
  - 两处都改为 `klown_pie_flavour_message(effect.desc)`，即 `C_(ctx,"%s!")` 套 `C_(ctx, desc)`。英文模式下 `i18n_source_lookup` 直接返回原文，输出仍是 `plum!` 等。
- **不会误套到普通水果名或颜色名**：
  - 带语境的键是 `klown pie flavour|plum` 等，只有在使用这个语境时才会命中。
  - 普通 `T_("cherry")`、颜色名等无语境查询不会读到这些键。
  - 反方向上，语境键存在时会优先使用，不会回退到无语境的同名键。
- **译名**：李子、柠檬、蓝莓、樱桃、花生脆糖、闪粉都忠实，也自然。glitter 在这里是糊脸的闪粉而不是颜色，译“闪粉”合适；`ETC_GLITTER` 的内部颜色身份没动。
- **后续状态消息**：写入者在 pie-followups.json 中列出 16 个键均已 `T_`、均有非空中文。我没有逐键重核，只抽查了 diff：本次没有新增或残留的 `mprf` 裸字面量。

## 4. HERE 统一：没有越界

- **改动范围**：只改了同场景的普通提示：
  - `Things that are here:` → 这里有：
  - `Items here: %s.` 和 `<cyan>Item%1$s here:</cyan> %2$s.` → 这里的物品：
  - `You see here %s.` 和片段 `You see here ` → 这里有
  - trunk 的 `<cyan>Here:</cyan> %s` → 这里：（stable 已经正确）
- **保留项**：真实列表都保留了冒号。改后两条线 source.txt 中剩余的“此处”（stable 8 处、trunk 11 处）都是括注、标签或叙述，例如（此处）、【就在此处】、点按此处、向此处移动、此处的空气、曾在此处，保留合理。
- **片段拼接**：`items.cc:937` 是 `T_("You see here ") + 物品名 + T_(".")`，中文为“这里有3块石头。”，自然，与整句键的结果一致，测试也实际断言了两者相等。
- 共享的 `T_("; ")` 没有改动，不扩大修改面是合理的。

## 5. 测试：通过

- **登记**：两条线的 `Makefile.obj` 都把 `test_zh_klown_pie.o` 加进了显式 catch2 对象清单，位置与 `test_zh_translation.o` 相邻，登记正确。写入者报告第一次过滤到 0 个用例（exit 2），登记后有 36 个断言真实运行，这个说法与登记前后的对象清单一致。
- **不是镜像断言**：
  - 英文用例用 `msg::tee` 分别捕获旧的 `mprf("%s!", desc)` 和新的显示输出，再逐字节比较。
  - 中文用例检查语境解析结果等于独立写出的期望值，并检查实际输出包含期望内容。
  - `[r3-action-frames]` 的英文期望是按原拼接独立手写的，中文期望是完整字面量。F-03 部分用真实怪物的 `name(DESC_ITS,true)` 和 4 个语境值代入，并断言结果中不出现“的的”。
- 两条线原有的数量测试各只同步了一句期望（你在这里看到 → 这里有），测试逻辑没改。
- **局限**（Non-blocking）：klown pie 测试用的是硬编码的六个标签，没有直接遍历 `pie_effects` 表。以后若新增口味，测试抓不到；本轮 diff 已逐条核对这六项。

## 6. 台账：通过

- 两条线的 diff 都不含 `docs/` 改动。
- notice-only 台账没有重绑；glossary 和 decisions 没改，所以硬性新鲜度台账也不需要重绑。
- 是否有资产派生字段的门禁失败，以 CI 的 Review ledgers 结果为准。写入者报告 world 和 character-mechanics 审计 exit 0。

## 7. trunk 上 C-07 与 shaft 的处理：合理

- **C-07**：
  - trunk 的 C++、Lua、数据库文本中都找不到 `shouldn't be using … like this` 的生产调用。
  - stable 的消费者在 `player-equip.cc:1848-1858`，已核对。
  - trunk 只同步修订共享镜像键，没有运行时影响，也没有声称修复了 trunk 的现行输出。
- **shaft**：
  - trunk 的现行显示走 `dat/descript/hints.txt:1385` 的 `$cmd` 整句，写入者引用的 `zh/hints.txt:972` 已经是“竖井”。
  - stable 的消费者 `hints.cc:2503` 确实是 `T_` 整句。
  - trunk 只同步镜像，保持了两条线的键值一致，也避免以后回补时把“陷坑”带回来。

## Non-blocking

1. stable 的 `directn.h:359` 有一处与任务无关的注释空格调整（“lookup.  The” 改为 “lookup. The”），无害，记录在案。
2. klown pie 测试没有遍历实际效果表，见第 5 项。
3. stable 的 `klown_pie_flavour_message` 在 beam.cc 内用前置声明代替头文件声明，与 trunk 做法一致；以后若有第二个调用者，应改为在头文件中声明。

## 未独立复跑

- 写入者报告的 code profile（trunk/stable exit 0）、工具套件 78/74、checkwhite/unbrace、Catch2 `[klown-pie]` 36 个断言 和 `[r3-action-frames]` 23 个断言，我都没有复跑，以 CI 和日志为准。
- 我复核了两条线的 `git diff --check`，均干净。
- 没有本地游戏或截图验收，符合发布后由玩家验收的流程。
