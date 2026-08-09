# Issue #43 R3 命令名称与描述全量校对计划（子批次 1：commands）

## 冻结边界

- 基线提交：`b56f853c4377bb5c07dfb1544fea5447a5c8ad15`（PR #44 精确候选；
  fast-forward 合并后的 `chn-0.34.1-base` HEAD）
- 上游总览：Issue #40 R3；执行入口子 Issue #43（子批次 1）。
- 生产身份源：`crawl-ref/source/command-type.h` 的 `command_type` 枚举（306 成员，
  含 `CMD_NO_CMD` 与 `CMD_MAX_CMD` 哨兵）；名称映射 `crawl-ref/source/macro.cc`
  `_cmds_to_names`（286 个物理条目；20 个标识符未由生成器物理发射，包含
  `CMD_NO_CMD` fallback、范围别名、合成命令与哨兵）。13 个范围别名虽未
  物理发射，但会因共享枚举整数值而在 `map<int,string>` 中命中已映射的目标名；
  仅 `CMD_MIN_SYNTHETIC` 所指的未发射值仍回退。`util/cmd-name.pl` 消费但不输出首个
  `CMD_NO_CMD`，末尾 `{CMD_NO_CMD, nullptr}` 仅为初始化停止哨兵；两方向查找
  仍通过既有 fallback 收敛到 `CMD_NO_CMD`。
- 描述数据源：`crawl-ref/source/dat/descript/commands.txt`（EN）与
  `crawl-ref/source/dat/descript/zh/commands.txt`（ZH），TextDB 键 =
  `CMD_X`（terse）与 `CMD_X verbose`（verbose）；EN 96 键行 / 95 唯一键
  （`CMD_EXPLORE_NO_REST` 重复定义，26 行覆盖 22 行，上游既有），ZH 96 键行 / 96 唯一键。
- 消费者：`describe.cc get_command_description()`（`#ifdef USE_TILE_LOCAL`；
  verbose → terse → 键名回退链）、`tilereg-cmd.cc`（tiles 命令菜单描述：
  命令条 terse 常显、`?` 详情 verbose）、`hints.cc hint_replace_cmds()` 的
  `$cmd[CMD_X]` 标签展开（`name_to_command` 反向解析，未知 → CMD_NO_CMD）。
- 命令名显示：`command_to_string()`（按键符号，T_ 仅影响 "uppercase %c" 等模板），
  与 commands.txt 描述键（EN 键名）解耦——描述键始终为 EN `CMD_X`，ZH 值在
  zh/commands.txt。

## 机械事实（清单工具 command_inventory.py 已断言）

- 双向差集：EN-only 无；**ZH-only `cmd_show_keyboard verbose` 1 键**
  （规范键小写后 = `cmd_show_keyboard verbose`，无对应枚举成员，
  `name_to_command` → CMD_NO_CMD，**孤儿键**）。
- **键名缺陷**：ZH 侧 `CMD_SHOW_KEYBOARD verbose`（369-372 行）为孤儿键——
  应为 `CMD_TOGGLE_KEYBOARD verbose`，但**正确键已存在于 389-392 行**（值
  「切换屏幕键盘的可见性。」与 EN 对等，运行时正常命中）；孤儿键永不查询
  （`name_to_command` → CMD_NO_CMD），清理即可。
- EN 侧 `CMD_EXPLORE_NO_REST` 重复定义（22/26 行，26 行生效）——上游既有，
  两定义语义一致，如实记录不修改。
- 描述键覆盖：51 个物理命令名有 terse 键、44 个有 verbose 键。按
  `map<int,string>` 的生产别名语义，3 个范围别名身份会复用已映射目标的
  描述；因此 54 个枚举身份至少有一项有效描述，252 个无描述（unused）。
- source.txt 无 CMD 形态键（commands.txt 为 TextDB 资产，不经 source.txt）。
- 无 T_ 缺口；无 EN/ZH 值缺失（missing_zh_keys 为空）。

## 验收标准

1. 清单工具确定性枚举全部枚举成员与 commands.txt 键，双向差集为空；每身份
   恰一张证据卡与一个终态结论（`keep`/`adjust`/`retranslate`/`defer`）。
2. 每项核对：terse/verbose 语义对等、`$cmd[...]` 展开目标、verbose→terse
   回退链影响、平台分支（USE_TILE_LOCAL）、按键提示与实际 UI。
3. 不把换行或文字长度启发式直接当作语义缺陷；`$cmd`、markup、Lua、条件块
   与平台分支原样保留。
4. ZH 资产由单一 `zh-translator` 顺序写入；每个依赖组或实际小批次运行
   `verify_zh.sh --profile translation`。
5. 本计划只做只读审核与证据记录；落地修改需另行授权，并在干净候选上按
   review-contract 走一次 final gate。

## 非目标

- 不改命令枚举、按键映射、宏系统行为；不修改 EN commands.txt 上游键。
- 不重审 #23–#29 既有冻结边界；tutorial/hints/help/FAQ 归子批次 2–4。
- 不新增全局 ledger/schema；inventory JSON 是可重建临时 artifact。

## 顺序

1. 冻结清单并记录 digest（本计划；修正生产 name-map 语义后的 inventory SHA
   `ad6ba57a62d49b14562385ada3dffb9c3b9c0230df379b2ac37fa592266c002e`，重建命令见下）。
2. 按显示消费者分组审核：tiles 命令条常显组（terse）→ 详情组（verbose）→
   回退链影响组（仅 terse 无 verbose 的命令）→ 未映射/哨兵组。
3. 逐个身份记录证据卡与终态结论（`docs/command-review-results.md`）。
4. 用户授权后由单一 `zh-translator` 落地批次（含 `CMD_SHOW_KEYBOARD verbose`
   键名修复），运行 translation profile。
5. 提交干净候选，机械路由评审，单次 final gate（如授权落地）。

## 重建命令

```bash
python3 .claude/scripts/command_inventory.py \
  --baseline-ref b56f853c4377bb5c07dfb1544fea5447a5c8ad15 \
  --inventory-output /tmp/command-inventory-<新文件名>.json \
  --review-results docs/command-review-results.md
  （输出仅允许 canonical /tmp 直下全新 basename；重复重建请更换文件名或先删除旧文件）
```
