# 翻译质量迁移 M0 必要性基线报告

状态：**M0 已完成；`Stop` 条件不成立，建议进入受限的 M1。**

本报告记录 `item-description:*` 试点的冻结范围、盲评、揭盲裁决和阶段决定。
M0 没有修改翻译资产、review schema、final gate 或正式验证入口，也没有调用外部
provider。实验明细保存在本地忽略目录
`.artifacts/i18n/quality/m0-item-description-v1/`。

## 一、结论

M0 观察到三个实质缺口：

1. 单体 16-case packet 在第一次受限读取时被传输截断；相同内容拆成四个确定性分片后
   才能完成评价。
2. 预揭盲步骤只保留了真值对象的 SHA-256，没有保留 canonical bytes，也没有完整定义
   真值序列化协议。逻辑标签仍可由冻结 inventory 重建，但不能证明重建字节就是原承诺
   `7874886c…3f08` 所绑定的字节。
3. evaluator 的 12 条 finding 经人工裁决全部成立，但漏掉了 1 条已知、可由精确
   before/after revision 验证的术语错误。

因此，方案中的 M0 `Stop` 条件不成立。M0 只支持进入 M1，范围限于确定性 packet、
真值物化和分片验证；它不授权 M2 事实协议、schema-v4 修改或 final gate 接入。

## 二、冻结边界

| 项目 | 冻结值 |
|---|---|
| Git 基线 | `695d5fbcd5ced6f12d1b68c99c91266b6713a477` |
| review base | `01dc9911ec9948aff661f6ec0b9b0a798fcf909d` |
| population | `item-description:*`，307 个唯一 identity |
| inventory digest | `dd1b961c34fe5cea549eb68c901e3065122d35fab4bc0625c45f9d1f12212904` |
| population digest | `c6da8c69d774a9cee3220f9699b04b0c377297f1ac5eafea3960596c3a1b702f` |
| population identity digest | `5373034332ad435637b983c0e8e8d0cb4c2f9d96458b23324e8ef07f7de5dabf` |
| glossary digest | `95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407` |
| decisions digest | `ab82bb4c888a636cbbf1463289be676a322b8cc14b8d91125018ae0ed1d3df0c` |
| prompt digest | `620cd257f70a0416052e7391ac939a23e7907b728180ac71de3b1f710d82384e` |
| blind packet digest | `2c231357dca8fff29da667bb7d653cf3a04465e544eaa9790fbc408d07adb7b4` |
| seed | `dcss-zh-quality-m0-item-description-v1` |

现有 item inventory 重新审计通过：总 inventory 3,759 条，其中目标 family 307 条；
目标 identity 无重复，inventory 与 reviewed identity 双向相等，输入摘要和终态均有效。

抽样采用冻结 seed 的 SHA-256 排序，选择 16 个互异 identity：

- 6 个 `adjust` identity 的精确 review-base revision；
- 4 个不同 `adjust` identity 的 adopted revision；
- 6 个 `keep` identity 的 adopted revision。

同一 identity 的 before/after 没有同时进入 packet。盲包不含 terminal conclusion、
revision kind、expected severity 或 semantic reason。

## 三、执行记录

### Attempt 1

`translation-reviewer` 在只允许一次组合读取的条件下验证了 prompt、context 和 blind
packet 的哈希，但工具传输在 `M0-003` 内截断，无法获得 16 条完整字符串，按约定返回
`No-Go`。这次失败不产生翻译结论，且没有揭盲。

### Attempt 2

原 blind packet、case、顺序、prompt 和真值承诺均未改变。只把原 packet 按顺序拆成
四个 4-case 分片；分片合并后与原 `items` 逐字相等，且无真值字段。transport manifest
SHA-256 为：

```text
f75d546e5194f4157b5281b8ddf0e31683cc15e5e7c1e79e56d8a8176e914f18
```

第二次输出覆盖 16/16 case，顺序、字段、finding ID、severity 取值和完整 English/Chinese
复制均通过严格校验。输出包含 12 条 `needs_fix`，16 条均报告 context sufficient；输出
SHA-256 为：

```text
b0f5a2fa526e5a9d5aadeff8eb266428766f0767ea6e4e8bd04ceae3eab9e639
```

从 prompt 冻结到有效输出共 776 秒，其中包含第一次 No-Go 和传输重试。输出冻结后的
人工裁决耗时 467 秒。

## 四、揭盲与证据等级

冻结 inventory 和 blind packet 可以无歧义地重建 6 个 review-base `needs_fix` 与 10 个
adopted 候选的历史标签。重建物 SHA-256 为：

```text
c5458aa04d777864ec2448172c2f1dd8f3ccf3b5304997105e840ec81231a85f
```

但原始预承诺没有保留 canonical truth bytes 或完整序列化 schema，所以不能对上述重建物
作原承诺哈希相等证明。以下结果分开报告两种证据：

- “历史标签”只表示冻结 review 的精确 before/after 证据；
- “人工裁决”重新判断 evaluator 指出的问题是否实际存在，再应用当前 severity。

不得把历史 `adjust` 的 adopted revision 自动视为无缺陷，也不得把历史 `keep` 当作永久
正确证明。本轮恰好发现，6 个与历史候选标签冲突的 finding 都是真问题，而不是实际
误报。

## 五、逐 case 结果

| Case | Revision | 历史标签 | Evaluator | 人工裁决 |
|---|---|---:|---:|---|
| M0-001 staff of necromancy | adopted/adjust | none | needs_fix | 成立；`living souls` 的修饰关系仍译错 |
| M0-002 sack of spiders | adopted/adjust | none | clean | clean |
| M0-003 condenser vane | adopted/adjust | none | needs_fix | 成立；`power` 与最高档云雾语义仍有错误 |
| M0-004 staff of air | adopted/adjust | none | clean | clean |
| M0-005 whip | adopted/keep | none | clean | clean |
| M0-006 staff of alchemy | review-base/adjust | needs_fix | needs_fix | 成立并命中历史 `Evocations` 错译 |
| M0-007 wand of mindburst | adopted/keep | none | needs_fix | 成立；`violently literal` 为不成立的中文结构 |
| M0-008 horn of Geryon | review-base/adjust | needs_fix | needs_fix | 成立并命中历史技能名及句法错误 |
| M0-009 Gell's gravitambourine | review-base/adjust | needs_fix | needs_fix | 成立并命中历史 `Evocations` 错译 |
| M0-010 book of winter | adopted/keep | none | needs_fix | 成立；误写为“困在天气中”，遗漏“困在室内” |
| M0-011 potion of haste | adopted/keep | none | clean | clean |
| M0-012 granite talisman | review-base/adjust | needs_fix | needs_fix | `god → 神明` finding 成立；但漏掉历史 `Shapeshifting → 变形术` |
| M0-013 book of scorching | adopted/keep | none | needs_fix | 成立；核心宾语和动词关系不符合自然中文 |
| M0-014 staff of fire | review-base/adjust | needs_fix | needs_fix | 成立并命中历史 `Evocations` 错译 |
| M0-015 phantom mirror | review-base/adjust | needs_fix | needs_fix | 成立并命中历史技能名；同时确认残留句法错误 |
| M0-016 book of unlife | adopted/keep | none | needs_fix | 成立；遗漏 `magical methods` 的魔法性质 |

## 六、指标

### 6.1 覆盖与结构

| 指标 | 结果 |
|---|---:|
| packet case 覆盖 | 16/16，100% |
| identity 覆盖 | 16/16，100% 且唯一 |
| 有效输出结构失败 | 0/1，0% |
| 实际传输 attempt 失败 | 1/2，50% |
| evaluator / 人工 context sufficient 一致 | 16/16，100% |
| unknown | 0/16，0% |
| 已输出 severity 与人工 severity 一致 | 12/12，100% |

### 6.2 历史标签对照

历史标签按 case 只判断“是否有 finding”：

| TP | FP/历史分歧 | TN | FN | Precision | Recall | Accuracy |
|---:|---:|---:|---:|---:|---:|---:|
| 6 | 6 | 4 | 0 | 50.0% | 100% | 62.5% |

若要求 finding 命中精确历史 correction，而不是只在同一 case 报出任意问题，则为
TP=5、历史分歧=7、FN=1，precision=41.7%、recall=83.3%。这些“历史分歧”不能解释为
实际误报，因为人工裁决确认了 7 条额外 finding 全部成立。

### 6.3 人工裁决对照

按 case 判断是否存在任一确定缺陷：

| TP | FP | TN | FN | Precision | Recall | Accuracy |
|---:|---:|---:|---:|---:|---:|---:|
| 12 | 0 | 4 | 0 | 100% | 100% | 100% |

按独立 issue 计，evaluator 命中 12 条，误报 0 条，漏报 1 条；precision=100%，
recall=92.3%，F1=96.0%。case recall 为 100% 而 issue recall 低于 100%，是因为
M0-012 报出了另一个成立的术语问题，却漏掉了该 revision 绑定的 Shapeshifting 问题。

本数据是经过风险增强的小样本，不能用于估算全部 307 条 item description 的缺陷率。

## 七、M1 的最小授权范围

M1 只解决 M0 已观察到的复现与泄漏风险：

1. 优先扩展现有 item inventory/audit 入口，用一个只读适配器同时物化 population
   manifest、blind packet、canonical truth bytes 和 commitment；不得再只保存 truth hash。
2. 对相同输入要求逐字节稳定；验证命令必须能从冻结输入重建 truth，并在揭盲前验证
   commitment。
3. 按明确的最大字节数或 case 数生成确定性分片及 manifest，并证明分片合并与 parent
   packet 完全相等、无真值字段。
4. 增加定向测试，覆盖 identity 守恒、before/after 不跨分区、哈希变化传播、路径可移植
   和标签不进入 evaluator bundle。

M1 不应增加新通用 schema、持久数据库或 evaluator 协议。完成 M1 并重新跑同一 M0
边界以前，不进入 M2。

## 八、证据摘要

| Artifact | SHA-256 |
|---|---|
| blind packet | `2c231357dca8fff29da667bb7d653cf3a04465e544eaa9790fbc408d07adb7b4` |
| attempt 2 raw output | `b0f5a2fa526e5a9d5aadeff8eb266428766f0767ea6e4e8bd04ceae3eab9e639` |
| truth reconstruction | `c5458aa04d777864ec2448172c2f1dd8f3ccf3b5304997105e840ec81231a85f` |
| adjudication | `2240f54ce4ce516f3dcd50448b1a02a343931f8158c262a6d49bea4534cbf607` |
| metrics | `0c9083da601c16529924c1e175c5da7d27ad8f12f7357fa9e3ee2311feffb34e` |

术语裁决绑定的 `docs/glossary.md` SHA-256 为
`95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407`。
