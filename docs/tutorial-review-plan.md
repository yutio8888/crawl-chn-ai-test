# Issue #46 R3 教程文本全量校对计划

## 冻结边界

- 上游总览：Issue #40 R3；执行入口：Issue #46（tutorial 子批）。
- 基线提交：`60ff40cd99eb1836b1b8b66701f538fa5e3349c4`。
- 术语权威：`docs/glossary.md` SHA-256
  `95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407`。
- 生产身份源：`lesson1.des` 至 `lesson5.des` 的静态教程消息生产者、
  `dat/dlua/tutorial.lua` 的全局 intro 与转发链、`tutorial.cc` 的 death 消息。
- TextDB：英文及中文 `dat/descript[/zh]/tutorial.txt`；消费者为
  `hints.cc::tutorial_msg()`、`hint_replace_cmds()`、平台标签过滤和 Lua/C++ 入口。
- 当前确定性 inventory：88 个唯一身份；生产者、EN 键与 ZH 键双向差集均为空。
  数量由精确 Git blob 重建，不作为工具内硬编码条件。
- Inventory SHA-256：
  `a7aa3dff6e17e723d70b0eb3b759ca8d1011401f89ec44c1d4c586a2c4cd3171`。

## 验收标准

1. 每个生产身份恰有一张规范证据卡和一个终态结论；inventory 与 review
   identities 顺序及集合完全相等。
2. 每项核对 EN/ZH 语义、producer/consumer、`$cmd[...]`、markup、平台块、
   `:nowrap` 与实际教程显示环境。
3. `adjust`、`retranslate` 与 defer 在资产写入前集中交由人工确认；无确认不落地。
4. 中文资产由单一 writer 顺序修改；清单工具与测试不重新打开该资产。
5. 定向测试及匹配 development profile 通过；干净候选按 review-contract-v5
   完成双评审、单次 final gate、PR CI 和 merge-time validation。

## 非目标

- 不处理 hints、help/FAQ 或其他 R3 子批，不修改游戏机制和教程生产流程。
- 不新增全局 ledger/schema、自动质量评分或第二套 final gate。
- 未观察到、需要扩大机制边界的问题记录为 `defer implementation`，不在本批扩张。

## 审校顺序与落地

1. 入口、总结与退出。
2. 移动与探索。
3. 战斗、目标选择与远程攻击。
4. 物品、物品栏与商店。
5. 魔法、盟友与法力。
6. 信仰、神授能力与教程结束。
7. 冻结人工确认后的结论，顺序写入 ZH TextDB，重建严格证据并证明覆盖相等。

重建命令：

```bash
python3 .claude/scripts/tutorial_inventory.py \
  --baseline-ref 60ff40cd99eb1836b1b8b66701f538fa5e3349c4 \
  --inventory-output /tmp/tutorial-inventory-<新文件名>.json \
  --review-results docs/tutorial-review-results.md
```
