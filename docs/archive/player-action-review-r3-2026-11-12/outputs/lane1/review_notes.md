# Lane1 评审记录（第三轮：玩家动作及反馈语句）

- 评审者：Claude Opus 5.5（claude-opus-5-5），Claude Code 子会话，默认参数；只读，未修改仓库；未读取 lane2。
- 基线：stable 4af734c175、trunk 40a7b9976a，源码均用 `git show <sha>:<path>` 查看；catalog 用固定 sha 的 dat/i18n/zh/source.txt（按运行时规则：key 小写、跳过前导空行）。
- 术语上下文：沿用本会话 `context_resolve.sh --task-type review` 的输出，glossary SHA-256 `fb814f3252f249fc230e81fa132dce6a9bb194b014d687fc1524c66827b351d7`（工作区 docs/glossary.md；本轮术语判断只涉及 shaft，以 catalog 用量为主证据）。已读术语表，**不是盲评**。

## 方法
1. 用脚本把输入压缩成逐句的“英文 / 中文模板 / 还原句 / 示例参数”视图，再逐族阅读。
2. 对“需要运行时输出”和高风险拼接族，回到固定 sha 源码追参数：B-02、B-03、C-02、C-05、C-06、D-04、D-05、F-02、A-01、A-03、D-01、D-HERE-03/16/18/20/32/58/69/70。
3. 核对了运行时翻译机制本身：database.cc i18n_source_lookup（key 小写；空译文退回英文）、message.cc mprf（不做自动翻译）、mon-util/simple_monster_message（只有 simple_monster_message 会做 strip_cjk_spaces）。

## 计数
- 随机 72 族：ok 63 / readability 6 / objective_error 3 / insufficient_evidence 0
- directed 76 组：ok 69 / readability 5 / objective_error 2

## 客观错误
- E-03（stable）：Okawaru 英雄气概两条消息没有 T_，显示英文。
- B-03（stable）：T_("The") 命中空译文键后退回英文，显示“The岩石碎成了小片。”。
- F-02（stable）：护身符槽位字面量 "amulet" 没有 T_，显示“你的amulet适应了…”。
- D-HERE-16（stable）：商店入口拼句缺“的入口”（“有一个通往一家武器店。”）；另有“这里有 ”尾空格。
- D-HERE-42（stable）：shaft 在教程中译“陷坑”，catalog 其余 29 处均为“竖井”。
三个 stable 拼接/字面量问题在 trunk 均已修正；修复时可参照 trunk 的写法。

## D-HERE 结论要点
- item_check 同一场景：单件“你在这里看到了…”、很多“这里有很多物品。”、没有“这里没有任何物品。”，只有 2~N 件的列表标题“此处有：”和堆叠摘要“此处物品：”用“此处”。列表冒号应保留，建议改为“这里有：”“这里的物品：”；列表分隔“； ”有多余空格。
- 格子描述面板（get_square_desc）中混用“这里：”和“此处物品：”；trunk viewmap 的同一个 Here: 标签译“此处：”。建议统一为“这里”。
- “（此处）”“【就在此处】”“已不在此处”属于括注/标签，“在此祈祷”“此处的空气”属于说明文字，可以保留；不建议全局禁用“此处”。
- “你在这里看到了” 和 “你在这里看到%s。” 有没有“了”不一致。

## 静态核对 / 参数还原 / 缺口
- 静态模板族直接对照 catalog 判定。
- 参数还原：上面第 2 条所列各族，以及输入已给示例的族（还原有误时已在 findings 中指出，如 A-01）。
- 缺口：B-02、A-03、E-05 依赖动词变位/移动短语助手，只做了静态推断，没有运行输出；B-03 依据对 TextDB 空值处理的代码追踪，建议用运行时断言确认。
- 结论只限本样本，不外推全库。
