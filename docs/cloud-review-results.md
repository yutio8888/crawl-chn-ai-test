# Issue #40 R1 云雾名称与描述全量校对结果

- 基线：`532d80d193`（`chn-0.34.1-base`）
- 术语表 SHA-256：`95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407`
- 清单 SHA-256：`3992b67fac930ba3b0be22fee3aa31ab1e6c7a7f0ca3aaf64d41d62049c7fbf8`
- 输入摘要：
  - `cloud-type.h` `05a1d119e698869fa7e40931268a7510d6d30175914da36db31ae21ea624a503`
  - `cloud.cc` `8a78b967800187701f7e898b83f404aae2cd6b5dadbffe72996edea2f20806e6`
  - `source.txt`、`clouds.txt`、`zh/clouds.txt` 摘要见 inventory JSON
- 身份总数：44（数据表条目 41；特殊值 3：`CLOUD_RANDOM_SMOKE`、
  `CLOUD_RANDOM`、`CLOUD_DEBUGGING`，无数据条目、不可显示，均 `keep`）
- 生命周期：现行 39；TAG 34 兼容（removed，无 producer、被 `?/L` 排除）
  `CLOUD_GLOOM`、`CLOUD_EMBERS`；语言侧独有描述键 `degeneration cloud` 1。
- 终态统计：名称 40 `keep`、1 `defer terminology`；描述 20 `keep`、
  16 `adjust`、2 `retranslate`、1 `defer implementation`。

## 独立审核进程结论（2026-08-08，translation-reviewer）

- 进程：独立 Pi 实例 `opencode-go/deepseek-v4-flash`，会话
  `r1-cloud-review-20260808`，只读；基线/glossary/inventory 三值全部
  一致，Blocker 0。
- 17 项候选：16 同意、1 建议修改（acidic fog 候选措辞）、0 反对。
- 新增 Needs Fix 2：① acidic fog 候选“使其效果免疫”宾语错位，已按建议
  修正候选；② 漏报 salt cloud“被捕获的生物”，已补为第 18 项候选。
- 新增 Suggestion 6（不阻塞）：noxious fumes 落地取“陷入混乱”；steam
  “大大抵消”；calcifying dust“呆任何时长”；spectral mist“聚集→凝聚成形”；
  freezing vapour“冰气云”；seething chaos“翻腾/沸腾”用字。
- 格式保护检查通过：`%%%%`、`<_smoke_cloud_>`、`#` 注释、DB 键均不变。
- 重建命令：`python3 .claude/scripts/cloud_inventory.py --inventory-output /tmp/cloud-inventory.json`
- 覆盖证明：`?/L` 运行时枚举器（`lookup-help.cc`）与清单枚举一致；中英
  描述键双向差集：EN-only 无、ZH-only `degeneration cloud` 唯一孤儿键；
  T_ 键缺口：`gloom`（兼容条目 terse，不显示）、`?`（哨兵，不显示）。

## 名称证据卡（terse / verbose）

| 身份 | 英文名称 | 现行中文 | 证据 | 终态 |
|---|---|---|---|---|
| `cloud:CLOUD_NONE` | `?` / `?` | （无） | 哨兵；`cloud_type_name_en` 对越界返回 "buggy goodness"，`?` 永不显示；T_ 键不存在属正确行为 | keep |
| `cloud:CLOUD_FIRE` | flame / blazing flames | 火焰 / 炽热烈焰 | 现行；BEAM_FIRE，6+r2a(16,2)（玩家 10+r2a(23,2)），火抗≥3 免疫；法术 Flaming Cloud 燃烧云（裁决 D-C-001 族）与大量火焰源产生；词根“火焰”与 glossary 一致 | keep |
| `cloud:CLOUD_MEPHITIC` | noxious fumes | 毒烟 | 现行；混乱/眩晕、毒抗或 clarity 免疫；BEAM_MEPHITIC 束名同键 `noxious fumes → 毒烟`；Mephitic Cloud 迷瘴云、Noxious Cloud 毒瘴云（裁决）、卡牌 summoning 产生；"fumes"=烟，与毒瘴/迷瘴措辞族不同词类不冲突 | keep |
| `cloud:CLOUD_COLD` | freezing vapour / freezing vapours | 冰冻蒸汽 / 冰冻蒸汽 | 现行；BEAM_COLD，冰抗≥3 免疫；Freezing Cloud 冰冻云产生；与“蒸汽”词根族（steam=蒸汽）并存 | keep |
| `cloud:CLOUD_POISON` | poison gas | 毒气 | 现行；中毒+直接伤害，毒抗免疫；Poisonous Cloud 毒云、Breathe Poison Gas 吐息毒气（glossary）产生 | keep |
| `cloud:CLOUD_BLACK_SMOKE` | black smoke | 黑烟 | 现行；不透明、无害；`_smoke_cloud_` 模板描述 | keep |
| `cloud:CLOUD_GREY_SMOKE` | grey smoke | 灰烟 | 同上 | keep |
| `cloud:CLOUD_BLUE_SMOKE` | blue smoke | 蓝烟 | 同上 | keep |
| `cloud:CLOUD_PURPLE_SMOKE` | purple smoke | 紫烟 | 同上 | keep |
| `cloud:CLOUD_TLOC_ENERGY` | translocational energy | 传送能量 | 现行；流放/位移残留，无害；与技能“传送系”、`Translocational energy. → 传送能量。` 一致；观察：disjunction halo 消息 `位移能量` 属传送系显示族另一身份，不在本边界 | keep |
| `cloud:CLOUD_FOREST_FIRE` | spreading flames / a forest fire | 蔓延火焰 / 一场森林大火 | 现行；BEAM_FIRE 同伤害；蔓延烧树、水上生成蒸汽；描述键用 terse | keep |
| `cloud:CLOUD_STEAM` | steam / a cloud of scalding steam | 蒸汽 / 一股灼热蒸汽云 | 现行；0+r2a(16,2)，火抗减伤；Breathe Steam 吐息蒸汽（glossary）词根一致 | keep |
| `cloud:CLOUD_GLOOM` | gloom / thick gloom | （terse 缺）/ 浓厚幽暗 | TAG 34 兼容：`cloud_is_removed` 返回 true，无 producer，`?/L` 排除；terse `gloom` 无 T_ 键但无显示路径；恢复时需补 `幽暗`（与浓厚幽暗一致） | defer terminology: 恢复时复审并补 terse 键 |
| `cloud:CLOUD_INK` | ink | 墨汁 | 现行；仅水中存在，BEAM_NONE；Ink Cloud 墨云产生；名实相符 | keep |
| `cloud:CLOUD_PETRIFY` | calcifying dust | 钙化尘 | 现行；BEAM_PETRIFYING_CLOUD 石化状态（glossary 石化），经验等级判定；Petrifying Cloud 石化云产生；名称直译准确 | keep |
| `cloud:CLOUD_HOLY` | blessed fire | 圣火 | 现行；BEAM_HOLY，神圣能量抗性≥3 免疫，亡灵/恶魔重伤；圣光系（善神）服务者不受影响 | keep |
| `cloud:CLOUD_MIASMA` | foul pestilence / dark miasma | 恶臭瘟疫 / 暗黑瘴气 | 现行；中毒+减速，瘴气抗性；`瘴气` 词根与已移除 Miasma cloud 瘴气云裁决一致；verbose 不显示 | keep |
| `cloud:CLOUD_MIST` | thin mist | 薄雾 | 现行；无害氛围云；深渊生成 | keep |
| `cloud:CLOUD_CHAOS` | seething chaos | 沸腾混沌 | 现行；`chaos_affects_actor` 随机效果；名称与混乱族不冲突 | keep |
| `cloud:CLOUD_RAIN` | rain / the rain | 雨水 / 雨中 | 现行；火系生物受伤；消散后可能留下浅水；"in the rain" 消息模板独立翻译 | keep |
| `cloud:CLOUD_MUTAGENIC` | mutagenic fog | 致变雾气 | 现行；诱变辐射（glossary Contamination 诱变辐射）污染，消散时负面变异；名称取“致变”与状态措辞区分 | keep |
| `cloud:CLOUD_MAGIC_TRAIL` | magical condensation | 魔法凝结 | 现行；无害尾迹（召唤/毁灭法球/流星轨迹）；与 CLOUD_XOM_TRAIL 共享名称与描述键 | keep |
| `cloud:CLOUD_VORTEX` | whirling frost | 旋转冰霜 | 现行；极地漩涡法术产生，BEAM_COLD 部分减伤；名称与法术 极地漩涡 措辞族一致 | keep |
| `cloud:CLOUD_DUST` | sparse dust | 稀疏尘埃 | 现行；无害氛围云；元素使/土系被动产生 | keep |
| `cloud:CLOUD_SPECTRAL` | spectral mist | 幽灵雾气 | 现行；亡灵免疫，生成幽灵亡灵；Spectral Cloud 幽灵云产生；与专名“幽灵”族一致 | keep |
| `cloud:CLOUD_ACID` | acidic fog | 酸雾 | 现行；腐蚀（状态 腐蚀）+伤害，腐蚀抗性免疫；名称与状态/抗性措辞族区分 | keep |
| `cloud:CLOUD_STORM` | thunder / a thunderstorm | 雷鸣 / 雷暴 | 现行；BEAM_ELECTRICITY 23+27 伤害，电击抗性免疫；Magnavolt 磁暴等产生 | keep |
| `cloud:CLOUD_MISERY` | excruciating misery | 极度痛苦 | 现行；玩家每 tick 10% 最大生命、怪物 15%，负能量抗性减免；名称贴切 | keep |
| `cloud:CLOUD_FLUFFY` | white fluffiness | 白色绒毛 | 现行；quokka 死亡产生，无害不透明 | keep |
| `cloud:CLOUD_XOM_TRAIL` | magical condensation | 魔法凝结 | 现行；Xom 高难效果尾迹，与 MAGIC_TRAIL 共享名称/描述正确 | keep |
| `cloud:CLOUD_SALT` | salt | 盐粒 | 现行；Xom 效果，无害不透明 | keep |
| `cloud:CLOUD_GOLD_DUST` | golden dust | 金粉 | 现行；武剑天堂风暴产生；力量加成实际由 DUR_HEAVENLY_STORM 提供，描述为风味文本；`门徒` 与武剑神描述族（门徒）一致 | keep |
| `cloud:CLOUD_EMBERS` | smouldering embers / embers | 阴燃余烬 / 余烬 | TAG 34 兼容（removed、无 producer）；名称直译准确且完整 | keep |
| `cloud:CLOUD_FLAME` | wisps of flame | 火焰飘带 | 现行；狐火（MONS_FOXFIRE 狐火）轨迹；名称与“飘忽的火焰”意象相符 | keep |
| `cloud:CLOUD_ALCOHOL` | alcoholic mist | 酒雾 | 现行；眩晕（酩酊）；wizlab Lua 以名称放置；名称贴切 | keep |
| `cloud:CLOUD_BLASTMOTES` | blastmotes / volatile sparks | 爆尘 / 不稳定火花 | 现行；接触火焰/生物爆炸、震荡击退；blastmotes 为专有名词，音意结合可取 | keep |
| `cloud:CLOUD_ELECTRICITY` | sparks | 火花 | 现行；无害轨迹（Cocytus 毁灭法球、磁暴术余波等） | keep |
| `cloud:CLOUD_FAINT_MIASMA` | faint pestilence | 微弱瘟疫 | 现行；`Rotten Stench`（腐臭恶臭）法术先兆，迅速变浓为 Miasma | keep |
| `cloud:CLOUD_MAGNETISED_DUST` | magnetised fragments | 磁化碎片 | 现行；Magnavolt 磁暴吸引物；与法术名 磁暴 措辞族一致 | keep |
| `cloud:CLOUD_BATS` | bats | 蝙蝠群 | 现行；Bat Swarm 蝙蝠群技能产生；与能力名一致 | keep |
| `cloud:CLOUD_RUST` | rust | 锈蚀 | 现行；腐蚀+削弱攻击（弱化），最小伤害；名称贴切 | keep |
| 特殊值 ×3 | — | — | 无数据表条目，`cloud_name_to_type` 特判，不可显示 | keep |

## 描述证据卡（descript/clouds.txt，键 = terse + " cloud"）

| 键 | 行为核对（producer/consumer/机制） | 现行中文 | 问题 | 终态 |
|---|---|---|---|---|
| flame cloud | BEAM_FIRE；远程冰系攻击穿云减射程并消散云（`_cloud_interacts...`/beam 逻辑）；水上生成蒸汽 | 一团猛烈燃烧的火云… | 语义完整、机制准确 | keep |
| noxious fumes cloud | 混乱；玩家 `1+random2(27)>=XL`，怪物 HD 判定；毒抗免疫 | 一团呛人又有毒的云。任何生物身处其中，都有被气体混乱的危险，除非具有毒抗。越坚韧、经验等级越高的怪物不太会受此影响。 | ①“被气体混乱”语法不通（应为“陷入混乱”）；②EN “creatures” 覆盖玩家与怪物，末句 怪物→生物 | adjust：…都有被气体弄混乱的危险…；…生物不太会受此影响。 |
| freezing vapour cloud | BEAM_COLD；远程火系攻击穿云减射程 | 一团冰气云… | “冰气云”与名称“冰冻蒸汽”措辞不一，可接受；机制准确 | keep |
| poison gas cloud | 中毒+直接伤害；毒抗免疫 | 一团有着致命毒性的云… | 语义完整 | keep |
| _smoke_cloud_ | 四色烟云共用模板；无害 | 一团有色的烟云。无害，除了对哮喘病人。 | 忠实 | keep |
| black/grey/blue/purple smoke cloud | 模板引用 | <_smoke_cloud_> | 结构保留正确 | keep |
| translocational energy cloud | 流放残留；无害 | 这是某个最近来过这里的生物的残留物… | 语义完整；“脱离现实，直到深渊”忠实 | keep |
| spreading flames cloud | 蔓延烧树；水上蒸汽；远程冰系减射程 | 一团熊熊的森林大火。…不幸的是，附近的树木，常常自己会变成更多的火种。 | “kindling for the fire”→ 火种 不准（树变成的是燃料/引火物，不是火种） | adjust：…常常会变成更多供火燃烧的燃料。 |
| steam cloud | 0+r2a(16,2)；火抗进一步减伤 | 一团灼热的蒸汽云。…火抗属性会大大抵消伤害。 | “further reduce”→“大大抵消”略夸大，可接受 | keep |
| ink cloud | 仅水中；BEAM_NONE | 一团墨云，里面完全是水。 | EN “completely filling the water”=墨汁充满水体；“里面完全是水”语义反了 | adjust：一团墨汁，完全充满了水体。 |
| calcifying dust cloud | 石化判定 `random2(62)-13>=XL`；石像鬼相关未明（EN 亦有 XXX 注释） | 一团石化云。…在云中呆任何时长的生物… | “呆任何时长”拗口但可懂 | keep |
| blessed fire cloud | BEAM_HOLY；神圣能量抗性；亡灵/恶魔重伤 | 一团圣火云… | 语义完整 | keep |
| foul pestilence cloud | 中毒+减速；瘴气抗性 | # XXX：清洁一下石像鬼雕像\n一团腐臭的瘟疫云。…并且会发现他们的移动速度变慢了。 | ①注释 “clarify gargoyles” 误译为“清洁一下石像鬼雕像”（应为“澄清石像鬼”）；②EN “may also” 的“可能”丢失 | adjust：注释改“# XXX：澄清石像鬼”；…也可能发现他们的移动速度变慢。 |
| thin mist cloud | 无害氛围云 | 一团蔳雾云。营造氛围的，但无害。 | “蔳”为错字（应为“薄”）；“营造氛围的”句式可保留 | adjust：一团薄雾云。营造氛围的，但无害。 |
| seething chaos cloud | `chaos_affects_actor`：隐身/狂暴/麻痹等随机效果 | 从隐身到狂暴，到完全麻痹。 | 状态名 隐形（glossary status Invisibility→隐形），“隐身”与状态族不一致 | adjust：从隐形到狂暴，再到完全麻痹。 |
| rain cloud | 火系生物受伤；消散后可能留下浅水（`_maybe_leave_water` 仅 FLOOR→SHALLOW_WATER，无加深逻辑） | 一个极度集中的暴风雨。它可能形成浅水池，或临时加深现有水池。完全由火形成的生物不愿在雨中呆太久。 | ①“或临时加深现有水池”为 EN 没有的内容（代码也无加深行为）；②“Beings made of fire”→完全由火形成的生物 拗口 | adjust：一场范围极小的暴风雨。它可能留下短暂的浅水池。由火焰构成的生物不愿在雨中久留。 |
| mutagenic fog cloud | 诱变辐射污染；消散时负面变异 | 一团纯净、无结构的魔法… | 语义完整 | keep |
| magical condensation cloud | MAGIC_TRAIL/XOM_TRAIL 共享；无害尾迹 | 某种高度集中的魔法能量被唤醒，本身是完全无害的。 | “wake”=尾迹/航迹，误译为“被唤醒”，语义错误 | retranslate：某种高度集中的魔法能量留下的尾迹，本身完全无害。 |
| whirling frost cloud | 极地漩涡产生；BEAM_COLD 仅部分减伤；玩家在涡旋结束后仍可被伤 | 一个极地旋涡之风。它将对其内的任何怪物造成严重伤害，只有一部分伤害能通过寒抗而减轻。 | ①“任何怪物”→玩家同样受伤害，应为“任何生物”；②“旋涡”与法术名 极地漩涡 用字不一；③“寒抗”→寒冷抗性（source.txt 既有术语） | adjust：极地漩涡之风。它将对其中的任何生物造成严重伤害，只有一部分伤害能通过寒冷抗性减轻。 |
| sparse dust cloud | 无害氛围云 | 一团薄灰云。营造氛围的，但无害。 | “薄灰”与名称“稀疏尘埃”不一致 | adjust：一团稀疏的尘埃云。营造氛围的，但无害。 |
| spectral mist cloud | 亡灵免疫；生成幽灵亡灵 | 一团幽灵迷雾云。…危险却短暂的亡灵生物将从雾中聚集。 | “coalesce”=凝聚成形，现译可接受 | keep |
| acidic fog cloud | 腐蚀状态+伤害；腐蚀抗性免疫 | 一团腐蚀肉身的酸液云雾，对身处其中的生物造成伤害和酸蚀。酸抗属性可以带来免疫效果。 | ①状态名 腐蚀（glossary status Corrosion→腐蚀），“酸蚀”与状态族冲突；②“Resistance to corrosion”→酸蚀抗性（item-name 既有术语），非“酸抗属性”；③候选初稿“使其效果免疫”宾语错位，独立审核后修正 | adjust：…造成伤害并施加腐蚀。酸蚀抗性可完全免疫其效果。 |
| thunder cloud | BEAM_ELECTRICITY；电击抗性免疫 | 一团黑暗的暴风云。…对那些没有电抗的造成巨大伤害。 | “电抗”→电击抗性（source.txt `electricity resistance→电击抗性`） | adjust：…对那些没有电击抗性的造成巨大伤害。 |
| excruciating misery cloud | 玩家 10%/怪物 15% 最大生命；负能量抗性减免 | 陷入其中的生物会发现自己会不断流失与最大生命值成比例的生命值 | 语义正确但拗口 | adjust：…会反复失去其最大生命值的一小部分… |
| white fluffiness cloud | quokka 死亡；无害 | 一团白色蓬松的云。… | 忠实 | keep |
| salt cloud | Xom；无害 | 一团急速旋转的尘和盐云。它会刺入任何被捕获的生物的眼睛和皮肤，尽管它终究是无害的。 | 独立审核漏报补充：“creatures caught within”→被捕获的生物 误译（云并不捕获生物），与本族“身处其中/在其中的生物”用词不一致 | adjust：它会刺痛身处其中的生物的眼睛和皮肤，尽管它终究是无害的。 |
| golden dust cloud | 武剑天堂风暴；力量加成在风暴持续期 | 一团闪闪发光的金色尘云。身处其中，门徒会在战斗中获得巨大力量。 | “门徒”与武剑神描述族一致 | keep |
| smouldering embers cloud | TAG 34 兼容；可被扑灭、无人管则燃成火焰云 | 一团阴燃的余烬云。… | 忠实；无现行行为可核对 | keep |
| wisps of flame cloud | 狐火轨迹；无害 | 一道火花和一缕烟。营造氛围的，但无害。 | “wisps of flame”→一缕烟 错误（应为 缕缕火焰） | retranslate：一道火花和缕缕火焰。营造氛围的，但无害。 |
| alcoholic mist cloud | wizlab Lua 放置；眩晕 | 一层雾化的月光酒雾气，浓到生物仅仅走过其中就会醉倒。 | “moonshine”→月光酒，与药水身份 私酒（POT_MOONSHINE）不一致 | adjust：一层雾化的私酒雾气，浓到生物仅仅走过其中就会醉倒。 |
| blastmotes cloud | 接触火焰/生物爆炸；震荡击退邻近生物 | 其震荡性的爆炸，会对邻近生物造成冲击。 | “knocking adjacent creatures away”→击退，现译缺击退语义 | adjust：爆炸的冲击波会将邻近生物击退。 |
| sparks cloud | 无害轨迹 | 一道电火花。营造氛围的，但无害。 | “A trail of”→一道，可接受 | keep |
| faint pestilence cloud | 腐臭先兆，迅速变浓 | 微弱的恶臭瘟疫从某处渗出。… | 忠实 | keep |
| magnetised fragments cloud | 磁暴吸引物 | 一团由无数微小的磁化金属碎片组成的云… | 忠实 | keep |
| bats cloud | Bat Swarm 产生；睡眠+伤害；亡灵免疫 | 一群微小的吸血蝙蝠…用催眠的咬伤逐渐使其入睡… | “吸血蝙蝠”与冻结怪物族“吸血鬼蝙蝠群”、变身消息“一群吸血鬼蝙蝠”措辞不一 | adjust：一群微小的吸血鬼蝙蝠… |
| rust cloud | 腐蚀+弱化攻击；最小伤害 | 一团氧化蒸汽… | 忠实 | keep |
| degeneration cloud | 无 EN 键、无代码查询路径（TILE_CLOUD_DEGENERATION 仅被酒雾复用为 tile） | 一团由浓缩的衰退药水形成的云。… | 语言侧孤儿键，永不显示；内容为旧版机制，无法核对 | defer implementation: 保持现状；若上游恢复 degeneration 云雾类型再复核并决定去留 |

## 依赖组一致性

- 魔法凝结 ×2（MAGIC_TRAIL/XOM_TRAIL）：名称与描述共享，修正描述一处
  即覆盖两个身份；Xom 尾迹语境同样成立。
- 四色烟云 + `_smoke_cloud_` 模板：模板单点翻译，结构保留正确。
- 瘟疫 ×2（foul pestilence / faint pestilence）：恶臭瘟疫/微弱瘟疫，
  与“瘴气云”兼容裁决无冲突。
- 蝙蝠族：cloud `bats→蝙蝠群` 与能力 `Bat Swarm→蝙蝠群` 一致；描述措辞
  对齐冻结怪物族（吸血鬼蝙蝠群）后全族统一。
- 蒸汽/冰/火云族：steam→蒸汽、freezing vapour→冰冻蒸汽、flame→火焰，
  与对应吐息/法术（吐息蒸汽/吐息毒气/冰冻云/燃烧云）词根一致。
- 状态与抗性措辞：混乱、隐形、麻痹、腐蚀、石化均按 glossary 状态族；
  寒冷抗性、电击抗性、酸蚀抗性按 source.txt 既有抗性族。

## 跨族观察（不在 R1 边界内，记录不处理）

- disjunction halo 显示族内 `传送能量。` 与 `沐浴在位移能量中` 并存的
  用词漂移；该族另有“位移魔法/传送系”漂移，建议归入 R3/R4 消息族处理。
- `%s cloud → %s云雾`（exclude.cc 排除列表模板）对所有云雾统一生效，
  含蝙蝠群云雾等组合，属模板级显示，无语义缺陷，不改。
- 玩家站入自有金粉云等非伤害云时的 engulf 消息（被吞没）由模板行为
  决定，属消息模板族，不在本边界。

## 结论汇总

- 名称：41 数据条目 + 3 特殊值；`keep` 43，`defer terminology` 1
  （`gloom` terse 键，兼容条目无显示路径）。
- 描述：`keep` 20，`adjust` 16（含独立审核补报的 salt cloud），
  `retranslate` 2（magical condensation、wisps of flame），
  `defer implementation` 1（degeneration cloud 孤儿键）。
- 名称键、描述键双向差集：唯一缺口 `gloom`（兼容、无显示路径），
  唯一语言侧孤儿键 `degeneration cloud`（无查询路径）；二者均不影响
  现行显示。
