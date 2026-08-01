# `traps.cc` 中文翻译问题交接文档

状态：A1–A10 已实施并逐项审核；A11 已确认不修改；历史开发验证（profile code/translation 均 Failures: 0）绑定目标基线 `084f8138ab532d193de2ec4a3105da4dfbd61759`，不代表当前候选；当前候选的正式验证由 final gate 负责；immutable readiness / merge authorization 尚未执行
范围：`traps.cc` 直接产生的用户可见文本、陷阱名称显示路径，以及对应的
`zh/source.txt` / `miscname.txt` 翻译。
术语表 SHA-256：`912d85c14b360357303835bce502a2e6661ab629ce350548879c85da8dc0d54e`

## 1. 工作边界

Pi 是只读分析 worker：每次只处理一个编号，返回源码证据、调用链、建议补丁
边界和验收条件，不直接修改文件、不运行 Git 操作。Codex 负责根据 Pi 的结果
实施、审阅、验证和合并；未经审核的建议不得进入最终候选。

写入所有权必须保持单写者：

- C++ / 头文件：Codex 以 `crawl-coder` 边界实施；
- `crawl-ref/source/dat/i18n/zh/source.txt`：统一由 Codex 按
  `zh-translator` 边界逐项实施，保持键唯一、占位符完整；
- `crawl-ref/source/dat/database/zh/miscname.txt`：本轮只读确认，除非 Pi
  提供新的明确证据；
- `docs/glossary.md`：本轮不修改。

明确不做：不翻译协议/查找键，不把内部归因字符串提前本地化，不顺手扩展到
整个翻译库，也不覆盖现有无关的 `handoff.md`、`.codex/` 或 `tools/` 改动。

## 2. 修订后的问题清单

> A1–A10 的“证据”和“现象”默认记录目标基线上的修复前问题；凡已实施的项目，
> 另列“当前候选”证据。这样不会把历史缺陷误读为当前候选仍存在的问题。

### A1：陷阱名的 `DESC_A` 重复

- 证据：`crawl-ref/source/traps.cc:121` 的
  `article_a(basename) + basename`；中文 `article_a()` 已返回名称本身。
- 现象：`传送陷阱传送陷阱`；英文路径也存在重复拼接风险。
- 方案：删除 `+ basename`，保留 `return article_a(basename);`。
- 验收：`DESC_A` 对传送、警报、捕网、Zot 等陷阱名称只输出一次名称；不改变
  `DESC_THE` 和内部英文键。

### A2：怪物触发陷阱时动作短语泄漏英文

- 证据：`crawl-ref/source/traps.cc:443-554` 多处使用
  `mprf(T_("%s %s!"), ..., raw_english_action)`；中文键为 `%s%s！`。
- 现象：`某怪物invokes a tyrant's trap！` 等。
- 方案：优先把每个分支改成完整的 `T_()` 句子；如果采用短语键，必须逐个
  添加精确英文键，并保证中文和 `%s%s！` 自然拼接。同步修正
  `an devourer's` 为 `a devourer's`。
- 译文方向：`invokes`、`sets off`、`triggers` 等按上下文译为“发动/触发”；
  不机械保留英文空格或冠词。
- 当前 canonical 术语：harlequin 使用“丑角”，因此完整消息使用“丑角陷阱”。
- 验收：tyrant、archmage、devourer 等各分支无英文泄漏，句末标点正确，所有
  `%s` 仍按原语义传递。

### A3：警报触发短语泄漏英文

- 证据：`crawl-ref/source/traps.cc:577-580` 将 `pulls` / `sets off` 作为
  未翻译参数，中文键为 `%s%s了警报！`。
- 方案：优先完整翻译模板；若保持碎片结构，中文应组合成“拉响了警报”，不能
  使用“拉动了警报”。
- 验收：两种触发方式均输出自然中文，无 `pulls`、`sets off`。

### A4：竖井坍塌消息泄漏 `The` / `A`

- 证据（修复前）：`crawl-ref/source/traps.cc:732-733`（旧行号）把 `"The"` / `"A"` 作为参数传入
  `T_("%s shaft crumbles and collapses.")`。当前代码 `crawl-ref/source/traps.cc:738,740` 已改为
  完整句子 `mpr(T_("The shaft crumbles and collapses."))` 与 `mpr(T_("A shaft crumbles and collapses."))`，
  对应 `zh/source.txt:7299-7303` 两个完整键（均译为“竖井碎裂坍塌了。”）。
- 方案：拆成两个完整英文键和两个完整中文模板；中文均可为“竖井碎裂并坍塌了。”，
  不要单独给通用 `The` / `A` 增加翻译。
- 验收：已知玩家和未知玩家两条路径都无英文冠词泄漏，句意不变。

### A5：佐特领域剥夺意志力消息未本地化

- 证据：`crawl-ref/source/traps.cc:313` 使用原始英文字符串；
  `player.cc:8490-8495` 立即显示该消息；已有中文键为“你的意志力被剥夺了！”。
- 方案：在产生端把完整字面量包裹 `T_()`；该值不会跨越持久化或身份边界。
- 验收：中文显示正确，英文显示保持原文，扫描器不报 borrowed pointer 或
  variadic 问题。

### A6：`full_trap_name()` 的完整名称组合缺键/大小写不一致

- 证据：`crawl-ref/source/describe.cc:960-974` 组合本地化 basename 和后缀；
  `directn.cc:3101` 使用该显示路径；`feature-data.h:347-364` 提供完整名称。
- 现象：`dispersal`、`gas`、`dormant shadow` 等片段缺键时会回退到英文；
  `Passage of Golubria` 与 `passage of Golubria` 还存在大小写键差异。
- 方案：在 `full_trap_name()` 中显式使用每个 trap type 的完整 canonical
  display key 并执行 `T_()`，覆盖旧陷阱、`gas trap` 和 `dormant shadow trap`；
  对 `passage of Golubria` 复用现有大小写不敏感的 `Passage of Golubria` 键，
  不新增大小写重复键。不得盲改 feature-data，不得把内部 enum、协议键或身份值
  本地化。
- 验收：直接查看陷阱、`name(DESC_A/DESC_THE)`、进入陷阱消息分别覆盖
  teleport、dispersal、harlequin、Zot、Golubria、net 等名称；不存在英文回退，
  也不存在重复“陷阱”。

### A7：恶意力量与传送陷阱消息占位符语义错误

- 证据（修复前）：`crawl-ref/source/traps.cc:960-961,1031-1033`（旧行号）的 `%s` 已是完整句子，
  `source.txt` 对外层模板追加“处”。当前代码 `crawl-ref/source/traps.cc:1038-1040` 使用
  `make_stringf(T_("%s and a teleportation trap spontaneously manifests!"), _malev_msg().c_str())`，
  对应 `zh/source.txt:40509-40510` 已改为 `%s随后，一个传送陷阱突然出现了！`（不再追加“处”）。
- 现象：`一股邪恶力量充满了地牢……处突然出现了一个传送陷阱！`。
- 方案：把外层中文模板改为 `%s随后，一个传送陷阱突然出现了！`，保留一个
  `%s`，不修改 C++ 占位符数量。
- 验收：不同地点代入后句子均通顺；不重复“处”，不丢失“邪恶力量充满地牢”和
  “传送陷阱出现”两个命题。

### A8：`harlequin's trap` / `net trap` 术语一致性

- 证据：`source.txt` 中完整键与片段键分别存在“丑角/小丑”和“网/捕网”的不一致。
- 方案：按 `docs/world-review-results.md` 的现有 canonical 决定统一为“丑角”和
  “网”，同步完整键、片段键、进入消息和触发消息；本项不应被误报成必然的 C++
  显示路径缺陷。
- 验收：所有同一实体的名称、描述和触发消息使用“丑角陷阱/网陷阱”；共享 `net`
  键的墙壁跳跃消息仍然自然。

### A9：神祇不满措辞不自然

- 证据（修复前）：`source.txt` 中 `You feel a twinge of divine disapproval.` 曾为
  “你感到一丝神的反对。”；当前候选 `source.txt:9551` 为“你感到神祇的一丝不满。”。
- 方案：改为“你感到神祇的一丝不满。”，保留“轻微/一丝”的语义。

### A10：逃离捕网误译

- 证据（修复前）：`source.txt` 中 `You slip out of the net.` 曾为“你从网中滑过了”；
  当前候选 `source.txt:23375` 为“你从网中滑脱了”。
- 方案：改为“你从网中滑脱了。”；不要与另一个 `The net passes right through
  you.` 的“穿过身体”语义混淆。
- 验收：两个相邻消息分别表达“逃脱捕网”和“捕网穿过身体”。

### A11：不得在产生端本地化 `a Zot trap`

- 证据：`traps.cc:309,319,327,333` 的字符串进入麻痹记录、召唤者/网关归因等
  内部身份路径；`player.cc:7649-7655` 会保存 source。
- 结论：Pi 提议的产生端 `T_()` 不是修复方案，应拒绝。保持英文身份值；若未来
  需要用户可见中文，必须在最终 display sink 单独翻译并先审计全部消费者。
- 验收：笔记、归因、序列化和查找路径仍使用稳定英文身份，不出现语言切换导致的
  身份变化。

## 3. 已确认无需修改的相邻项目

- `The trap's stomach acid` 的延迟显示翻译路径正确；
- 中文省略英文复数后缀的现状符合项目决策；
- harlequin 动态片段与外层中文模板拼接正确；
- Golubria passage 的进入/阻塞/无出口消息占位符组合正确；
- 普通怪物进入通道时中文不需要人为补英文空格。

## 4. 逐项执行顺序

按以下顺序，每次将一个编号交给 Pi 做只读复核，再由 Codex 实施和审核：

1. A1、A5：低风险 C++ 修复；
2. A2、A3：动作短语和警报模板；
3. A4：竖井完整模板；
4. A7：传送陷阱外层中文模板；
5. A6：完整陷阱名称映射（在其他模板稳定后处理）；
6. A9、A10：纯文本修正；
7. A8：术语统一；
8. A11：复核并记录为明确不修改项。

每项完成后必须检查：

- `git diff --check`；
- 精确键、大小写和占位符数量；
- 对 C++ 改动运行 `bash .claude/scripts/verify_zh.sh --profile code`；
- 对翻译资产改动运行 `bash .claude/scripts/verify_zh.sh --profile translation`；
- 全部完成后再做一次定向运行时/静态审计，确认没有英文回退、身份本地化或
  其他 `traps.cc` 回归。

本文件是工作清单，不是 final gate 或 merge authorization。最终候选仍需按仓库
review contract 准备、路由审阅并由 Codex 完成最终验证。
