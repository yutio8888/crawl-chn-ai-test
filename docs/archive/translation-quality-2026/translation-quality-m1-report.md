# 翻译质量迁移 M1 确定性物化报告

状态：**M1 已完成；确定性 packet/truth 与分片门通过，M2 尚未开始。**

M1 只修复 M0 已经观察到的两个流程问题：单体 packet 会被传输截断，以及只保留
truth hash、没有保留 canonical truth bytes。它没有修改中文资产、glossary、decisions、
review schema、severity 或 final gate，也没有调用外部 provider。

## 一、实现结果

M1 复用了现有 `.claude/scripts/audit_item_name_inventory.py`，没有新建通用质量框架。
该入口现在可以：

1. 从通过双向覆盖验证的 Issue 29 evidence cards 中冻结完整的
   `item-description:*` population；
2. 用冻结 seed 确定性选择与 M0 完全相同的 16 个 identity 和 revision；
3. 同时物化 blind parent packet、4 个有界 shard、canonical population、canonical
   truth、commitment、prompt、context 和 manifest；
4. 从当前 inventory 与 bundle 内的 prompt/context 重建全部文件，并逐字节验证现有
   bundle；
5. 对文件缺失或多余、非 canonical JSON、摘要漂移、分片不守恒、重复 identity、
   非相对 source path、符号链接和 evaluator 标签泄漏失败关闭。

生成物只允许写入 `.artifacts/i18n/quality/<run-id>/`。本轮真实运行位于本地忽略目录
`.artifacts/i18n/quality/m1-item-description-v1/`，共 11 个文件。

## 二、artifact 边界

| Role | 文件 | evaluator 可见 |
|---|---|---|
| evaluator | `prompt.md`、`context.txt`、4 个 `blind-shard-*.json` | 是 |
| audit | `blind-packet.json`、`commitment.json` | 否 |
| sealed | `population.json`、`truth.json` | 否 |
| manifest | `manifest.json` | 否 |

每个 blind shard 最多 4 个 case；按 shard index 合并后的 `items` 必须与 parent packet
逐字相等。blind parent 和 shard 都禁止出现以下 case-specific 字段：

```text
pre_review_chinese
adopted_chinese
revision_kind
terminal_conclusion
semantic_reason
historical_expected_severity
expected_correction_chinese
```

truth 为每个 case 保存 evaluated Chinese digest、revision kind、历史证据状态和 packet
item digest。review-base `adjust` revision 保存精确 adopted correction，并标记历史
`needs_fix`；adopted revision 一律标记 `unadjudicated`，不再从历史 `keep/adjust` 自动
推导为 clean。这一限制直接来自 M0 对 6 个“历史 clean 候选”的反例。

## 三、确定性选择

M1 使用与 M0 承诺一致的算法：

```text
sha256(seed|pool|identity)
sha256(seed|order|identity|revision-kind)
```

seed 为 `dcss-zh-quality-m0-item-description-v1`。选择边界仍为：

- 6 个 `adjust` identity 的 review-base revision；
- 后续 4 个不同 `adjust` identity 的 adopted revision；
- 6 个 `keep` identity 的 adopted revision；
- 同一 identity 不重复，因此 before/after 不会同时进入 evaluator packet。

机械比较确认 M1 的 16 个 blind `items` 与 M0 packet 逐字相等，包括 case ID、顺序、
English、Chinese、producer、consumer、metadata 和 source files。M1 parent digest 因采用
新的 contract 和可复现 population digest 而不同，这是有意的 contract 版本变化，
不是样本变化。

## 四、真实运行摘要

| 项目 | 值 |
|---|---|
| Git/data baseline | `695d5fbcd5ced6f12d1b68c99c91266b6713a477` |
| review base | `01dc9911ec9948aff661f6ec0b9b0a798fcf909d` |
| inventory rows | 3,759 |
| item-description population | 307 个唯一 identity |
| inventory SHA-256 | `dd1b961c34fe5cea549eb68c901e3065122d35fab4bc0625c45f9d1f12212904` |
| population identity SHA-256 | `5373034332ad435637b983c0e8e8d0cb4c2f9d96458b23324e8ef07f7de5dabf` |
| population SHA-256 | `ea6ea2853971057968cbb98cb917e3900d2ffda74471593ce9fd9b70b51edc5a` |
| blind packet SHA-256 | `9b61ec1603bf4dac8bc23ce4e4d7cf81c34c82deb8a202ffa7821d9f410b820d` |
| evaluator bundle SHA-256 | `d70144a8a806115f73b85702ddc67acd75499fefe44f9fb2cbbe595c344276cc` |
| truth SHA-256 | `b175f49f697be1f72a529c92c10183c7d889068793a95c09cda5d30e98cc1ca1` |
| commitment SHA-256 | `33090fd58c6225a4cb43ef0f70bde8a940d6aaa507ace6c2ebc1fe4bfafe56d5` |
| manifest SHA-256 | `76341c4655994d63a4b2fef9fd56b6bb24f89c01dd3190aba1f8bff35ed7a0ec` |
| prompt SHA-256 | `620cd257f70a0416052e7391ac939a23e7907b728180ac71de3b1f710d82384e` |
| context SHA-256 | `145c71e07d3808d74132bf0721671fa6698e07b21a34dbc75b3c7e380ecbe8e5` |

生成命令成功后，又使用 bundle 自己保存的 `prompt.md` 和 `context.txt` 执行独立 verify
命令。verify 从当前 inventory 重建 11 个文件，要求文件集合及每个字节完全相等；
manifest 和 truth digest 与生成运行一致。

## 五、测试与验证

新增 5 组定向测试，覆盖：

- 同输入两次生成逐字节相等；
- 真实 M0 16-case 选择和顺序不变；
- adopted revision 只能是 `unadjudicated`；
- truth bytes 存在且 commitment 可揭封；
- 分片重组、identity 唯一和 evaluator 标签隔离；
- 重复 identity、结论/revision 冲突、绝对 source path 和 review violation；
- shard、truth、canonical JSON、prompt、文件集合及输出目录的最小负向变异；
- prompt 改变会传播到 blind packet、truth、commitment 和 manifest。

验证结果：

| 验证 | 结果 |
|---|---|
| 新增 M1 定向测试 | 5/5 PASS |
| `test_audit_item_name_inventory.py` 完整回归 | 22/22 PASS |
| 真实 bundle materialize | PASS |
| 真实 bundle self-contained verify | PASS |
| `verify_zh.sh --profile code` | PASS，0 blocking failures |

code profile run ID：
`20260805T174846011029000+0800-45041-695d5fbcd5ce`。

术语上下文绑定的 `docs/glossary.md` SHA-256 为
`95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407`。

## 六、阶段决定

M1 的完成条件已经满足：相同输入逐字节稳定，identity 守恒，truth 原始字节可揭封，
分片可以重组，evaluator bundle 无标签泄漏，路径可移植，规范资产未被写入。

因此可以单独申请 M2，但不能自动进入。M2 若获批准，只应在同一 calibration 边界上
比较：

1. 当前直接输出 `blocker / needs_fix / suggestion` 的基线；
2. 先输出语义、术语、完整性、自然度和 context 事实，再由宿主映射现有 severity 的
   事实优先协议。

M1 没有证明需要数字总分、新严重度、Gold/Silver 等级或正式门禁接入，也没有修复 M0
发现的具体翻译问题。
