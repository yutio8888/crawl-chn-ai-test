# Issue #40 R1 云雾名称与描述全量校对计划

## 冻结边界

- 基线提交：`eaecb7122c2db8633693e51b692c14425b6b654d`（`pi/r1-clouds` HEAD，合并 `chn-0.34.1-base`）
- 上游总览：Issue #40 R1；无独立子 Issue 编号时以本计划为执行入口。
- 生产身份源：`crawl-ref/source/cloud-type.h` 的 `cloud_type` 枚举
  （`NUM_CLOUD_TYPES` 之前的全部成员；含 `CLOUD_RANDOM_SMOKE`、
  `CLOUD_RANDOM`、`CLOUD_DEBUGGING` 三个特殊值）。
- 名称数据源：`crawl-ref/source/cloud.cc` 的 `clouds[]` 表（terse_name 与
  verbose_name），经 `cloud_type_name_en()` → `T_()` 显示。
- 描述数据源：`crawl-ref/source/dat/descript/clouds.txt`（EN）与
  `crawl-ref/source/dat/descript/zh/clouds.txt`（ZH），DB 键 =
  terse 名 + `" cloud"`（`describe.cc get_cloud_desc()`）。
- 显示消费者：`?/L` 云雾帮助菜单（`lookup-help.cc _get_cloud_keys()`）、
  `describe.cc get_cloud_desc()`、`directn.cc`/`exclude.cc`/`nearby-danger.cc`
  区域描述与移动警告、`tilereg-dgn.cc` 地图块提示、`player.cc`/`potion.cc`
  移动警告。
- 名称解析消费者：`cloud_name_to_type()` 同时匹配 T_ 与 EN 名称
  （Lua `.des` 用 `cloud_type = "alcoholic mist"` 放置云雾）。

## 验收标准

1. 清单命令确定性枚举全部枚举成员，并交叉验证 `clouds[]` 数据表覆盖；
   记录 baseline、inventory digest、glossary digest 与输入文件摘要。
2. 每个身份恰有一张证据卡和一个终态结论：`keep`、`adjust`、
   `retranslate`、`defer terminology` 或 `defer implementation`。
3. 名称键集合、描述键集合与 T_ 键集合双向差集为空；语言侧独有键
   （无 EN 键、无代码查询路径）单独记录生命周期并给出终态。
4. 每项描述核对 producer、consumer、实际行为：伤害、抗性/免疫、状态、
   持续条件、传播/消散、地形交互与显示消费者。
5. 同一依赖组（共享专名、共享词根、同名云雾）内术语一致；与既有冻结
   边界（法术名、怪物名、状态、技能）不一致时给出依据或暂缓。
6. ZH 资产由单一 `zh-translator` 顺序写入；每个依赖组或实际小批次运行
   `verify_zh.sh --profile translation`。
7. 本计划只做只读审核与证据记录；落地修改需另行授权，并在干净候选上
   按 review-contract 走一次 final gate。

## 非目标

- 不改云雾机制、数值、抗性算法、生成表或枚举值。
- 不重审 #23–#29、法术/物品/怪物/状态等既有冻结边界；只复用其结论。
- 不新增全局 ledger/schema；inventory JSON 是可重建临时 artifact。
- 不处理 disjunction halo（`位移能量`）等非云雾显示族；仅记录跨族观察。

## 既有机制复用

- 复用 `?/L` 运行时枚举器（`_get_cloud_keys()` + `cloud_name_to_type()`）
  作为游戏内身份证明；复用 `docs/decisions.md` 中 `X Cloud` 系列、
  迷瘴云/毒瘴云/毒云、`火云/瘴气云/毒气云/蒸汽云` 兼容裁决。
- 新增 `.claude/scripts/cloud_inventory.py`（只读、确定性、可重建），
  解析枚举、数据表、T_ 键与中英描述键，输出 JSON inventory 与覆盖报告。

## 顺序

1. 冻结清单并记录 digest（本计划）。
2. 先审共享词根/共享名称依赖组（魔法凝结×2、烟×4、瘟疫×2、蒸汽/冰/火
   云族、蝙蝠族），再审独立条目。
3. 逐个身份记录证据卡与终态结论（`docs/cloud-review-results.md`）。
4. 用户授权后由单一 `zh-translator` 落地名称与描述批次，运行
   translation profile。
5. 提交干净候选，机械路由评审，单次 final gate（如授权落地）。

## 重建命令

```bash
python3 .claude/scripts/cloud_inventory.py \
  --baseline-ref eaecb7122c2db8633693e51b692c14425b6b654d \
  --inventory-output /tmp/cloud-inventory.json
```
