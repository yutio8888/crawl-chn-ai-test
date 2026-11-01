> 2026-11-01 新审计说明：下列旧叙述为历史记录；当前结论以本轮 strict evidence 及文末全量重审记录为准。

# Issue #54 monflee 动态消息全量审阅结果

本轮仅将当前 glossary authority 重绑定至 Tranquillity 拼写兼容别名后的摘要；旧权威字段复原后逐域重现原 inventory 摘要，baseline、生产 dump、卡片正文和结论保持原样。真实 trunk 内容增量另列审查，不由此重绑定推导通过。

冻结基线 `5f168f7b1130f9d2ec9c264f27e4ddc9b64d64d6` 的唯一 identity 已完整审阅：
五个变体中 `keep` 2 项、`adjust` 1 项、`retranslate` 2 项，无延期项。严格证据块
按 production locator 顺序保存结构事实、人工结论和最终候选中文。

<!-- BEGIN STRICT MONFLEE REVIEW EVIDENCE v1 -->
```jsonl
{"baseline":"d2d19e5640af7fb04d2e8af769d146f8bf1b1412","glossary_sha256":"8a36accf4fc362bf8f103d84ba5d5e6639615274e94d38b16a2d2afe0b0c04cf","identity_count":1,"inventory_sha256":"ec346be4dea4723e9391643285ace7b0a306dad27c54f3a1cc6319b1ab5c0bd7"}
{"identity":"monflee:dream sheep flee","key":"dream sheep flee","confidence":"high","glossary_authority":"docs/glossary.md@8a36accf4fc362bf8f103d84ba5d5e6639615274e94d38b16a2d2afe0b0c04cf","terminal_conclusion":"keep","deferral_owner":null,"deferral_reason":null,"reentry_trigger":"EN/ZH source、生产拓扑、递归依赖、调用路径或 glossary authority 变化时重新审阅。","reviewer_rationale":"2026-11-01 fresh primary (keep): 5变体的恐惧叫声、可见惊慌、转身、一跃与撒蹄逃跑分别准确；VISUAL前缀未改，heard-only与可见分支不混淆。生产fear事件与Xom羊宝库两个入口已核。 原审证据定位：[\"crawl-ref/source/mon-behv.cc:1347\",\"crawl-ref/source/mon-behv.cc:1462\",\"crawl-ref/source/dat/des/altar/xom_sheep.des:44\"]。","rejected_alternatives":["不以历史 ledger 的结论代替本轮 fresh primary；本身份的判断依据：5变体的恐惧叫声、可见惊慌、转身、一跃与撒蹄逃跑分别准确；VISUAL前缀未改，heard-only与可见分支不混淆。生产fear事件与Xom羊宝库两个入口已核。"],"current_english":["@The_monster@ bleats in terror.","VISUAL:@The_monster@ is struck with panic!","VISUAL:@The_monster@ panics and turns to flee.","VISUAL:A frightened @monster@ leaps away.","VISUAL:@The_monster@ stampedes away."],"current_chinese":["@The_monster@惊恐地咩咩叫起来。","VISUAL:@The_monster@被吓坏了！","VISUAL:@The_monster@惊慌失措，转身逃跑。","VISUAL:受惊的@monster@一跃而去。","VISUAL:@The_monster@撒蹄狂奔而去。"],"proposed_translation":["@The_monster@惊恐地咩咩叫起来。","VISUAL:@The_monster@被吓坏了！","VISUAL:@The_monster@惊慌失措，转身逃跑。","VISUAL:受惊的@monster@一跃而去。","VISUAL:@The_monster@撒蹄狂奔而去。"],"lifecycle":"current-player-visible","actual_behavior":"梦羊在 ME_SCARE 中进入逃跑行为时，以稳定英文 DB name 查询该 key；Xom 梦羊 vault 也直接查询同一 key。localized SpeakDB 使用生产权重选择正文，随后展开怪物 token。无前缀 ordinal 0 在 pre-mprf seam 作为 MSGCH_TALK emission 继续传递：源怪物 ENCH_MUTE 或源格沉默只将 effective_silence 置为 true，不阻止它抵达 MSGCH_TALK；最终 mprf sink 仅在玩家所在格沉默时由 prepare_message 抑制该 MSGCH_TALK。VISUAL 正文路由至 MSGCH_TALK_VISUAL、清除 silence，仅怪物可见时产生 emission，且不受该 sink 抑制。","display_context":"怪物首次受惊逃跑或 Xom 梦羊事件触发的玩家可见消息。","consumer":{"channel_routing":"crawl-ref/source/mon-speak.cc:851","final_sink":"crawl-ref/source/message.cc:1845","localized_lookup":"crawl-ref/source/database.cc:2307","weighted_selection":"crawl-ref/source/database.cc:1238"},"producers":[{"location":"crawl-ref/source/mon-behv.cc:1287","mode":"fear transition"},{"location":"crawl-ref/source/dat/des/altar/xom_sheep.des:44","mode":"Xom dream sheep event"}],"evidence_locations":["crawl-ref/source/dat/database/monflee.txt:8","crawl-ref/source/dat/database/zh/monflee.txt:8","crawl-ref/source/mon-behv.cc:1287","crawl-ref/source/mon-speak.cc:851","crawl-ref/source/message.cc:1845","crawl-ref/source/dat/des/altar/xom_sheep.des:44"],"dependency_group":"dream sheep flee voice and visual motion","production_facts":{"english_source":"database/monflee.txt","localized_source":"database/zh/monflee.txt","variant_count":5,"weights":[30,10,10,10,10],"control_prefixes":[null,"VISUAL","VISUAL","VISUAL","VISUAL"],"runtime_tokens":[["@The_monster@"],["@The_monster@"],["@The_monster@"],["@monster@"],["@The_monster@"]]},"variant_reviews":[{"english":"@The_monster@ bleats in terror.","weight":30,"variant_ordinal":0,"current_chinese":"@The_monster@惊恐地咩咩叫起来。","proposed_translation":"@The_monster@惊恐地咩咩叫起来。","terminal_conclusion":"keep","rationale":"5变体的恐惧叫声、可见惊慌、转身、一跃与撒蹄逃跑分别准确；VISUAL前缀未改，heard-only与可见分支不混淆。生产fear事件与Xom羊宝库两个入口已核。 本单元 EN=\"@The_monster@ bleats in terror.\"；当前冻结 ZH=\"@The_monster@惊恐地咩咩叫起来。\"。","control_prefix":null,"runtime_tokens":["@The_monster@"]},{"english":"VISUAL:@The_monster@ is struck with panic!","weight":10,"variant_ordinal":1,"current_chinese":"VISUAL:@The_monster@被吓坏了！","proposed_translation":"VISUAL:@The_monster@被吓坏了！","terminal_conclusion":"keep","rationale":"5变体的恐惧叫声、可见惊慌、转身、一跃与撒蹄逃跑分别准确；VISUAL前缀未改，heard-only与可见分支不混淆。生产fear事件与Xom羊宝库两个入口已核。 本单元 EN=\"VISUAL:@The_monster@ is struck with panic!\"；当前冻结 ZH=\"VISUAL:@The_monster@被吓坏了！\"。","control_prefix":"VISUAL","runtime_tokens":["@The_monster@"]},{"english":"VISUAL:@The_monster@ panics and turns to flee.","weight":10,"variant_ordinal":2,"current_chinese":"VISUAL:@The_monster@惊慌失措，转身逃跑。","proposed_translation":"VISUAL:@The_monster@惊慌失措，转身逃跑。","terminal_conclusion":"keep","rationale":"5变体的恐惧叫声、可见惊慌、转身、一跃与撒蹄逃跑分别准确；VISUAL前缀未改，heard-only与可见分支不混淆。生产fear事件与Xom羊宝库两个入口已核。 本单元 EN=\"VISUAL:@The_monster@ panics and turns to flee.\"；当前冻结 ZH=\"VISUAL:@The_monster@惊慌失措，转身逃跑。\"。","control_prefix":"VISUAL","runtime_tokens":["@The_monster@"]},{"english":"VISUAL:A frightened @monster@ leaps away.","weight":10,"variant_ordinal":3,"current_chinese":"VISUAL:受惊的@monster@一跃而去。","proposed_translation":"VISUAL:受惊的@monster@一跃而去。","terminal_conclusion":"keep","rationale":"5变体的恐惧叫声、可见惊慌、转身、一跃与撒蹄逃跑分别准确；VISUAL前缀未改，heard-only与可见分支不混淆。生产fear事件与Xom羊宝库两个入口已核。 本单元 EN=\"VISUAL:A frightened @monster@ leaps away.\"；当前冻结 ZH=\"VISUAL:受惊的@monster@一跃而去。\"。","control_prefix":"VISUAL","runtime_tokens":["@monster@"]},{"english":"VISUAL:@The_monster@ stampedes away.","weight":10,"variant_ordinal":4,"current_chinese":"VISUAL:@The_monster@撒蹄狂奔而去。","proposed_translation":"VISUAL:@The_monster@撒蹄狂奔而去。","terminal_conclusion":"keep","rationale":"5变体的恐惧叫声、可见惊慌、转身、一跃与撒蹄逃跑分别准确；VISUAL前缀未改，heard-only与可见分支不混淆。生产fear事件与Xom羊宝库两个入口已核。 本单元 EN=\"VISUAL:@The_monster@ stampedes away.\"；当前冻结 ZH=\"VISUAL:@The_monster@撒蹄狂奔而去。\"。","control_prefix":"VISUAL","runtime_tokens":["@The_monster@"]}]}
```
<!-- END STRICT MONFLEE REVIEW EVIDENCE v1 -->

## 结论汇总

- Identity：1/1；variant：5/5；无重复、遗漏或延期。
- `keep`：variant 1、2。
- `adjust`：variant 3。
- `retranslate`：variant 0、4。
- DB key、`w:30`、四个 `VISUAL:`、五个 runtime token、变体顺序与默认权重均保持。
- Inventory SHA-256：
  `b575ecb1f8dbd0f1ecaaae57c6c02d76850897626294cbdf7d338e780239ca3c`；
  exact-candidate agreement 在候选提交并重建 production dump 后记录。

PR #194 trunk 移植：仅重绑定本台账的术语权威及派生摘要；恢复旧 glossary 权威可重现原摘要，baseline、production dump、卡片语义正文与结论保持不变。相关显示行为由 D-B-023／D-C-100 及本次回归测试覆盖。

## 2026-11-01 当前生产全文重审

本节与新的 strict evidence 取代旧正文中的当前审计声明。全部判断来自逐条读完 EN/ZH 的 fresh primary，不沿用旧 ledger keep。修复先落入生产，然后冻结本轮 inventory；因此已修项目在本基线记录为 keep，原始发现及修前→修后文本保留在逐 identity/variant/template rationale。明确延期仍按原审 owner 与重入条件保留。

- Baseline: `d2d19e5640af7fb04d2e8af769d146f8bf1b1412`。
- Inventory SHA-256: `ec346be4dea4723e9391643285ace7b0a306dad27c54f3a1cc6319b1ab5c0bd7`。
- Glossary SHA-256: `8a36accf4fc362bf8f103d84ba5d5e6639615274e94d38b16a2d2afe0b0c04cf`。
- Fresh primary SHA-256: `3ad3f20ad8742fb2d6abde90fde6e73b4a73ed2c88c353e540ecf71babd67f50`。
- Identity coverage: `1/1`；缺失、额外及重复 identity 均为零。
- 当前 identity 结论：`{"keep":1}`。
- 逐 variant 覆盖：`5`；保持 production locator 顺序。

## 本轮消费者定位说明

本轮冻结生产版本为 `d2d19e5640af7fb04d2e8af769d146f8bf1b1412`。严格schema中由工具常量规定的 consumer / producer / evidence_locations 行号是历史契约锚点，不表示该版本的当前行号；当前语义追踪使用逐卡 fresh rationale 和下列按符号核对的定位。冻结正文、源文件摘要及身份集合仍绑定本轮生产版本。

以下行号均为 `crawl-ref/source/` 下相应文件，箭头表示历史契约行号→本轮当前位置：

- database.cc：_getWeightedSelection 1238→1285；getSpeakString 2307→2356。
- message.cc：静默玩家消息终端1845→1979。
- mon-behv.cc：逃跑消息查询1287→1347，实际发出点1462；mon-speak.cc：mons_speaks_msg 851→852。
