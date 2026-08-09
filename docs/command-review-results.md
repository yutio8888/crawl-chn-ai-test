# Issue #40 R3 命令名称与描述全量校对结果草案（子批次 1：commands）

- 基线：`b56f853c4377bb5c07dfb1544fea5447a5c8ad15`（PR #44 精确候选；
  fast-forward 合并后的 `chn-0.34.1-base` HEAD）
- 术语表 SHA-256：`95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407`
- 清单 SHA-256：`9320c0b54dc594c8d579aef7fa5236c4e4b5d47c378ded79b87dd96596bbba03`
- 身份总数：306 枚举成员 = 51 个至少有一个 commands.txt 描述键
  + 255 个无 commands.txt 描述键成员；19 个未映射成员是后者的子集，
  不另行相加。
- 描述键：EN 95 唯一 / ZH 96 唯一；EN-only 无；**ZH-only `cmd_show_keyboard verbose` 1 键（孤儿）**
- EN 侧 `CMD_EXPLORE_NO_REST` 双定义（22/26 行，26 行生效，DBM_REPLACE）——上游既有，ZH 侧单定义

## 初步只读审核（2026-08-08，translation-reviewer）

- 进程：独立 Pi 实例，只读；报告了 54 条审核记录，候选统计为
  **44 keep、6 adjust、4 retranslate**；needs_fix 10 条（R3-NF-01..10）；
  suggestion 4 条。当前持久化文档不能重建这 54 条记录与 306 个
  inventory identity 之间的唯一绑定。
- 状态：这些结果是待规范化的审核输入，不是 306 个 inventory identity 的
  一对一终态台账；在双向覆盖等式建立前，不宣称完成全量审核，
  也不授权译文落地。
- 重点：孤儿键 `CMD_SHOW_KEYBOARD verbose`（2023 年命令改名遗留）清理；`CMD_SHOW_CHARACTER_DUMP`
  verbose 值尾孤儿行「丢弃角色的进度」；`CMD_EXPLORE_NO_REST` ZH 侧缺长描述（EN 经双定义
  使 terse/verbose 均显长描述，ZH 仅短句 → 显示对等缺口）；`CMD_REST`「此将休息100回合」
  语法残缺；`CMD_DISPLAY_RELIGION` 神祗→神祇、戒律、虔诚度；`CMD_LOOKUP_HELP` 魔法→法术；
  `CMD_MAP_FIND_*` 衍文与 门户→传送门。
- Suggestion（不阻塞）：MP 术语全局统一（法力 vs 魔法值）超出本批次另立议题；android
  菜单文案复核归子批次 2–4；255 个无描述键成员（含 19 个未映射
  成员）尚需逐身份绑定生命周期与终态结论，不修改其行为。

## 有描述键身份的审核摘要（非完整证据台账）

| 身份 | terse 现行 | 证据要点 | 终态 |
|---|---|---|---|
| CMD_REST | 休息并回血 | verbose「此将休息100回合」语法残缺；健康/魔力 vs 生命值/魔法值同段不一致；100 回合数字正确 | retranslate（verbose） |
| CMD_EXPLORE | 自动探索当前楼层 | 语义对等；停止条件完整 | keep |
| CMD_EXPLORE_NO_REST | 自动探索当前楼层，不先休息 | EN 双定义 → 有效 terse=长描述（含 explore_auto_rest 机制）；ZH 仅短句，显示对等缺口 | adjust（补长描述） |
| CMD_INTERLEVEL_TRAVEL | 前往其他楼层 | 语义对等 | keep |
| CMD_TOGGLE_KEYBOARD | 切换键盘 | **孤儿键 CMD_SHOW_KEYBOARD verbose 清理**（正确键已存在） | adjust（键清理） |
| CMD_SHOW_CHARACTER_DUMP | 丢弃并显示角色的进度 | terse「丢弃」误导（dump=导出档案）；verbose 尾孤儿行「丢弃角色的进度」；存档目录→morgue 目录；「 玩家名.txt」空格 | retranslate |
| CMD_CHARACTER_DUMP | 导出角色进度 | verbose 存档目录→morgue 目录、丢入到→导出到、空格 | adjust |
| CMD_DISPLAY_RELIGION | 显示你的宗教状况 | 神祗错字；conduct→戒律；信仰等级→虔诚度（既有 37 处） | retranslate |
| CMD_LOOKUP_HELP | 查看怪物、魔法… | spells→法术（glossary 与文件内一致） | adjust |
| CMD_MAP_EXPLORE | 移动到下一探索点 | 「然后将自动探索那里」缺主语、语义偏移 | retranslate |
| CMD_MAP_FIND_PORTAL | 寻找商店和门户 | portal→传送门（既有 71 处） | adjust |
| CMD_MAP_FIND_ALTAR | 循环显示切换到本层的祭坛 | 「切换到」衍文 | adjust |
| 其余 39 身份 | — | 语义对等、术语一致 | keep（44 含 android 摘要） |

## 建议落地批次（待人工确认）

| # | 文件:行 | 修改 |
|---|---|---|
| 1 | zh/commands.txt:369-372 | 删除孤儿块 `CMD_SHOW_KEYBOARD verbose`（正确键 389-392 行保留） |
| 2 | zh/commands.txt:115,117-123 | CMD_SHOW_CHARACTER_DUMP：terse→「导出并显示角色进度」；verbose 值整段替换（删除 121-122 行孤儿空行/孤儿行「丢弃角色的进度」）→「将角色的详细信息导出到 morgue 目录中的文件“玩家名.txt”，并在游戏中显示该文件。它包含主要数据、装备、法术、技能、笔记等等。」（方案审核修正：魔法→法术 与批次 #3 姊妹命令统一） |
| 3 | zh/commands.txt:126 | CMD_CHARACTER_DUMP verbose：「丢入到存档目录…“ 玩家名.txt”」→「导出到 morgue 目录…“玩家名.txt”」；魔法→法术（保持与 NF-06 一致） |
| 4 | zh/commands.txt:8-9 | CMD_REST verbose →「恢复你的生命值和魔法值。一旦有敌对怪物出现，休息就会中断。如果生命值和魔法值都已满，休息将持续100回合。」 |
| 5 | zh/commands.txt:66 | CMD_DISPLAY_RELIGION verbose →「显示你信仰的神祇的好恶、戒律，以及当前的虔诚度和神赐的能力。」 |
| 6 | zh/commands.txt:191 | CMD_LOOKUP_HELP verbose →「查看怪物、法术、能力、物品等的描述。」 |
| 7 | zh/commands.txt:323 | CMD_MAP_FIND_ALTAR verbose →「循环显示本层的祭坛。」 |
| 8 | zh/commands.txt:303,307 | CMD_MAP_FIND_PORTAL → terse「寻找商店和传送门」；verbose「循环显示本层的商店和传送门。」 |
| 9 | zh/commands.txt:227 | CMD_MAP_EXPLORE verbose →「将光标移到自动探索将要前往的下一个位置。」 |
| 10 | zh/commands.txt:385-388 | CMD_EXPLORE_NO_REST：值替换为长描述译文（不复制 EN 双定义——ZH 规范键空间禁止重复定义）：「自动探索当前楼层，并沿途收集物品。一旦有敌对怪物出现，或是遇到新物品或新地标时，探索就会停止。与 CMD_EXPLORE 不同，此命令会将 explore_auto_rest 视为 false，将 explore_auto_rest_status 视为空。」 |

依赖组落地顺序：键清理（1）→ 档案组（2、3）→ 移动/探索组（4、9、10）→ 信息组（5、6）→ 地图组（7、8）；
每批运行 `verify_zh.sh --profile translation`。Suggestion 项不进入本批次。

## 方案审核结论（2026-08-08，translation-reviewer，落地前一轮）

- 总体：**approve with modifications**（10 项中 9 项逐字 approve；批次 #2 按修正文本 approve）。
- 修正：批次 #2 verbose 整段替换（魔法→法术 与姊妹命令统一，见上表）。
- 信息项（不阻塞）：EN 原句为 "main stats, equipment, spells, skills, notes, etc."（spells 非 magic，批次 #3 的 法术 正确）；NF-03 fix 原文已含 法术，编排者未新增改动；批次 #10 值替换在结构对称、无静默覆盖依赖、键行数对等三点成立；ZH verbose 回退「…视为空。。」与 EN "empty.." 均为回退机制固有标点重复，结构对等；长描述首两句可后续与 CMD_EXPLORE 对齐（suggestion）。
- 完整性：10 批次与 R3-NF-01..10 一一对应无遗漏；落地后 ZH 唯一键 95 = EN 唯一键 95，双向差集为空；EN 双定义系上游既有，未引入新不对称。

## 覆盖缺口与完成条件

- 清单已确定性产生 306 个完整且唯一的 identity；这只证明 inventory
  边界，不等于审核覆盖。
- 当前文档只保留了有描述键身份的摘要，且将 39 个 keep 身份合并为一行；
  reviewed identity 集合因此无法从本文档机械重建。
- 完成全量台账前，必须为 306 个 identity 各保留一张证据卡和一个
  终态结论，并机械证明 inventory/reviewed 集合双向相等；在此之前，
  不进入译文落地或 final gate。
- 键集合：双向差集仅 ZH-only 孤儿键 `cmd_show_keyboard verbose`（入批次 #1）；
  无 EN 值缺失；`$cmd[CMD_X]` 展开目标全部可解析（除孤儿键外）。
- 回退链核对：`get_command_description` verbose→terse→键名；terse-only 命令 7 个
  （回退行为记录，值无需修改）；CMD_EXPLORE_NO_REST 经批次 #10 对齐 EN 有效值。
- 重建命令：`python3 .claude/scripts/command_inventory.py --baseline-ref b56f853c4377bb5c07dfb1544fea5447a5c8ad15 --inventory-output /tmp/command-inventory-<新文件名>.json`（仅 /tmp 直下全新 basename）
