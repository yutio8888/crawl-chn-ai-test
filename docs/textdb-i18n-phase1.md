# TextDB 消息国际化 Phase 1 实施记录

状态：**Phase 1 已完成两个 `monspell` catalog overlay 纵向迁移，并启用首个
生产 `CASE_MAP`；Phase 2 尚未开始。**

本文记录 [`textdb-i18n-architecture.md`](textdb-i18n-architecture.md) 的
Phase 1 实际实现范围。Phase 0 基线提交为 `070f812bb6`；Phase 1 在独立分支
`codex/textdb-i18n-phase1` 上实现，不修改通用 TextDB 语法，也不装载新的
TextDB 文件。

## 1. 实际迁移范围

本阶段迁移两个完整 key 闭包：

| canonical key | stable ID | 策略 | 选择理由 |
|---|---|---|---|
| `beam catchall cast` | `mon.cast.beam_catchall.v1` | `NONE` | 单一 weight-10 变体；无成功递归、Lua 或 `[a|b]`；不依赖 foe/god/visual 条件；可完整复现 target relation 与 beam 显示 |
| `march of sorrows bone dragon cast` | `mon.cast.march_of_sorrows_bone_dragon.v1` + 两个稳定 case ID | `CASE_MAP` | 单一变体、单一二选一站点、无递归/Lua；原有 targeted binding 时序可保持不变 |

两个 canonical English 快照为：

```text
@The_monster@ throws @beam@ @at@ @target@.
@The_monster@ breathes [collective despair|endless sorrows] @at@ @target@.
```

模板使用 TextDB 不识别的 `${slot}`：

- EN：`${actor} throws ${beam} at/next to/past ${target}.`
- ZH `AT`：`${actor}向${target}射出${beam}。`
- ZH `NEXT_TO`：`${actor}朝${target}旁边射出${beam}。`
- ZH `PAST`：`${actor}射出${beam}，从${target}旁边掠过。`

`march of sorrows bone dragon cast` 将 option index `0/1` 分别映射到两个全局
稳定 case ID：

- `mon.cast.march_of_sorrows_bone_dragon.collective_despair.v1`；
- `mon.cast.march_of_sorrows_bone_dragon.endless_sorrows.v1`。

两者分别渲染“集体的绝望”和“无尽的悲伤”，同样提供 `AT/NEXT_TO/PAST`
三套 EN/ZH 模板。case ID 与 variant ID、其他 case ID 和 tombstone 共享全局
唯一命名空间。

`zh/monspell.txt` 未修改。structured 中文不从该文件选择变体，也不执行中文
递归、Lua 或正文随机。

`Vanquished Vanguard Nergalle cast` 继续为 `LEGACY_ONLY`。其三个
`@orc name@` 形成不可合理穷举的动态组合，在建立 `CAPTURE_SLOT` 证明前不得迁移。
其余未列入 catalog 的 `monspell` key 均在查询和 RNG 之前进入当前语言的 legacy
路径。`CASE_MAP` 当前只允许无递归、无 Lua、恰好一个至少包含两个选项的有限
`[a|b]` 站点；
`CAPTURE_SLOT` 仍被生成期与加载期拒绝，避免未完成策略被静默接受。

当前 structured slice 还要求 `resolved_target` 槽；非默认 applicability、
`implies_gesture=true` 和 `audible=true` 在其生产消费路径接线前均由生成期和
加载期拒绝。actor-only 模板不在本阶段能力声明内。

## 2. 三类 artifact 的职责

### manifest

`.claude/data/message-overlay/monspell.json` 是人工复审入口，保存：

- stable ID 与 tombstone；
- canonical/selection fingerprint、variant ordinal、权重与英文快照；
- 完整闭包依赖及 fingerprint；
- applicability、`cast_frame` 和物化策略；
- `${slot}` schema、逐行 sensory/channel/behavior 元数据；
- EN/ZH 最终纯模板。

它不是 TextDB 文件，不参与 SpeakDB 装载，也不覆盖既有 key。

### generated sidecar

`crawl-ref/source/fork-message-overlay.generated.inc` 由
`.claude/scripts/generate_message_overlay.py` 从 manifest 与 Phase 0 inventory
确定性生成，供 C++ 只读加载。禁止人工编辑。`--check` 必须逐字节通过。

### runtime catalog module

`fork-message-overlay.{h,cc}` 负责加载期验证、覆盖表、五态状态机、canonical
materialization、纯模板 renderer 和只读诊断。它不解析新的 TextDB 语法。

加载期会一次性验证 schema、inventory fingerprint、完整 key/variant 闭包、权重、
快照、依赖、stable ID/tombstone、策略、槽、语言/关系模板矩阵和频道。缺失、损坏、
未知 schema 或闭包不完整会禁用整个 `monspell` structured 域；首次查询即走
legacy，不发生抽取后 fallback。

## 3. 生产调用链

`databaseSystemInit()` 在任何施法消息查询前验证 overlay。`mon-cast.cc` 的候选
搜索对每个实际 lookup key 先调用覆盖路由，然后严格保留原状态机：

```text
MISSING       → 下一个候选；silent prefixed 时重试无前缀
SUPPRESS      → 立即停止并保持沉默
INAPPLICABLE  → 下一个候选；silent prefixed 时重试无前缀
RENDERED      → 立即输出
CORRUPT       → 立即停止，不查询 legacy、不重放 Lua、不额外消耗 RNG
```

因此：

- normal `beam catchall cast` 直接 structured；
- `silent beam catchall cast` 仍先按 legacy 查询，缺失后无前缀 key structured；
- `unseen beam catchall cast` 缺失后继续下一个候选，不错误重试 base key；
- 不支持 overlay 的语言在任何 canonical 抽取前直接 legacy。

structured 调用顺序为：

```text
canonical English 顶层选择
→ 既有递归/Lua expansion
→ __NONE 与 applicability
→ 一次目标解析（附只读 trace observer）
→ canonical @The_monster@/@at@/@target@/@beam@ 绑定
→ 既有 [a|b] materializer
→ stable locator/signature
→ 当前语言纯模板与 ${slot} 渲染
→ 按逐行 metadata 输出
```

`materialize_bound_legacy_randomness()` 只接受已绑定 `@at@/@target@/@beam@` 的
canonical pattern；未选择输入或残留 token 返回 `CORRUPT`，且 RNG 不动。动态
物化签名包含顶层/递归变体、Lua 结果和每个 `[a|b]` 站点身份/选项，禁止执行后
丢弃。`beam catchall cast` 的签名为 `NONE`；March 条目的两个签名以
`materialization-v1` 编码同一 locator 和唯一站点，并分别以 option index `0`
与 `1` 结尾。生成期和加载期都从 canonical key、variant ordinal 和选项数量
重建完整集合，同数量但伪造的 signature 也会禁用整个 structured 域。

## 4. owning 类型与显示边界

生产模型包含：

- `resolved_target`：relation、visibility、PLAYER/SELF/MONSTER/FEATURE/LOCATION/
  THIN_AIR/INDEFINITE/ERROR tagged kind、位置、feature、actor mid 与 owning display；
- `resolved_beam`：canonical/localized display、配置 name/short_name、spell、flavour、
  real flavour、pierce 与 ranged-attack presence；
- `cast_context`：frame、caster visibility、spell 与 god 数据；
- 逐行 sensory、channel、`implies_gesture`、`audible`；
- 完整 canonical TextDB、Lua、target 和 `[a|b]` owning trace。

canonical English 与当前语言显示值在一次 binding callback 内生成。目标解析只执行
一次；临时 `ScopedLangEn` 只重建已选实体的 owning English 显示，不重新查询
`monspell`，也不消耗 RNG。

structured line 进入 `mons_speaks_msg()` 时标记为 `already_rendered`：不再运行
`do_mon_str_replacements()`、`[a|b]` 或正文频道前缀解析。本地化正文即使以
`ERROR:`、`WARN:` 等开头，也不能改变频道。多行只能由 catalog 的多条 line
metadata 表达；单个模板内嵌换行会被生成期、加载期和 renderer 拒绝。

legacy 路径继续运行既有 replacement 与 gesture/visual/audible 文本 heuristic。
Phase 1 只让已迁移 structured key 使用显式元数据，没有删除全局 heuristic。

## 5. 诊断与年度升级

只读计数包括 overlay hit、legacy route、inapplicable、suppressed、corrupt 和
unknown schema，并带 domain/schema。测试证明读取或预先改变计数不会改变输出、
RNG state 或 count。

年度上游升级时：

1. 用 Phase 0 production dump 重新导出 canonical English；
2. 运行 monspell inventory diff，人工分类 key/variant/weight/token/递归/Lua/
   `[a|b]`/control-prefix 漂移；
3. 对 `beam catchall cast` 的语义变化人工决定沿用 ID 或创建新 ID；工具不得自动
   批准重绑定；
4. 更新 manifest，运行 generator，检查 sidecar 幂等；
5. 运行 overlay audit、Phase 0/Phase 1 Catch2、code/review verifier；
6. 未证明完整闭包的新 key 保持 legacy。

## 6. 验证证据

实现阶段已经观察到以下结果（均为退出码 0）：

- `[message-overlay][phase1]`：21,333 assertions / 15 test cases；
- `[textdb][phase0]`：736,197 assertions / 18 test cases；
- `[mon-cast-target][phase0]`：640 assertions / 5 test cases；
- Python manifest/generator tests：10 tests；
- `audit_message_overlay.py`：`message overlay audit: ok`；
- generated sidecar `--check`：逐字节通过；
- `scan_varargs_string.py`：0 个阻塞问题；
- `scan_i18n_lifetime.py --require-parser`：0 个持久借用指针问题；
- affected Catch2 executable 完整链接成功。

Phase 1 精确测试覆盖：五态、normal/unseen/silent、加载失败、English legacy
输出/RNG、EN/ZH canonical 与 target trace、真实 `[casts|pitches]` 和
`[pulses|vibrates]`、关系/目标/可见性快照、CORRUPT 无 fallback、多行 metadata、
协议残留、本地化正文不参与频道判断，以及诊断无副作用。生产 CASE_MAP 另对
March 条目固定运行 1,024 seeds，逐 seed 核对 option index、全局稳定 case ID、
英文逐字节结果、中文投影、三种目标关系和纯 renderer 不改变 RNG；Phase 0 对同一
key 的既有 1,024-seed 测试继续证明 canonical、真实目标解析、substring 与 legacy
最终 RNG/英文输出等价。

统一 verifier 现在无条件运行 manifest/generator/audit；相关文件发生变化时，
code/review/CI profile 还会构建并运行 `[message-overlay][phase1]`。

## 7. 已知限制与 Phase 2 门禁

- structured 覆盖仅 2 个 key，不代表 262 个 `monspell` root 已迁移；
- `CASE_MAP` 仅启用单有限站点子集；`CAPTURE_SLOT` 尚未启用；
- catalog renderer 当前只为 actor/target/beam 的 projectile schema 接线；
- 全局 legacy gesture/visual/audible heuristic 仍存在；
- 当前 canonical `monspell` 闭包无 Lua；未来出现 Lua 或不可控副作用时，在建立
  完整契约前必须 `LEGACY_ONLY`；
- 其他 TextDB 域没有迁移。

进入 Phase 2 前必须先证明所有仍可达、会影响 gesture/visual/audible 行为的
legacy 变体都有等价元数据覆盖；在覆盖率审计达到 100% 前不得删除全局 heuristic。

术语表 SHA-256：
`c221e1f1a39b085869ba918da061efaf7c2c32b431c9169d5512be0cecc22c4c`
