> 历史快照：以下为阶段 B 当时的判断；仅将工作路径改为可移植引用。后续 D05/D06 裁决见 [README](README.md)，不回写原始证据卡。

# D-C-096 有界适用性风险回查（阶段 B，只读）

本报告先按完整英文、当前消费者和机制形成语义判断，再核对旧决定；已加载术语上下文，不自称盲评。仅核对下列冻结探针，不声称全库或整个 D-C-096 完整重审。

## 范围与证据固定

纳入 piety 资源/叙述/等级，barbs 正文及短标签，Dazed 与迷魂及同词根叙述，noxious fumes 云类型和性质泛称，travel exclusion，技能与普通 aptitude。排除其他 D-C-096 词项、纯风格、全部法术数值、旧存档显示快照迁移，以及本任务禁止改动的发布流程文件。阶段 C 未开始，decisions/glossary/游戏资产/测试均未修改。

原始冻结清单：`anchoring-B-inventory.json`；SHA-256 `2c8871d82e2196502d6bb8edff5da549013e17988f87dbe5080daa3e1b7ad645`。46 个逻辑探针 × 两线 = 92 张证据卡；包含缺失/旧键槽，并非 92 个有效生产译文。原始清单保持不变。A01 的尾空格消费者差异单独补充，不静默替换冻结选择器。

本报告中的行号均属于下列固定树；后续合并漂移须重新定位，不照搬行号。

- stable：base `b1c79709858a214df94a912f5eb14a95a0b18564`；阶段 A head `e9227fd6d5fe45d4f597b0b54c6f885b48a3053a`；glossary SHA-256 `b31f5c1e6bb71645b8ef4645dfd0e901149f938830ca2cb55efe9bd24cb356e7`；当时的解析上下文工作材料 `anchoring-B-context-stable.txt`（未归档；glossary 摘要如上）。

- trunk：base `5417df71b38aacf59adeff888d4ada88d5576391`；阶段 A head `eb43a337e47ee6c4110f38fb18c1b715c5e6a6f1`；glossary SHA-256 `cdccfd9e10789d9bd17cf369e2a60180a8c7b1850e259e3786d7940ebff9726a`；当时的解析上下文工作材料 `anchoring-B-context-trunk.txt`（未归档；glossary 摘要如上）。

## 结论和两线差异

没有确认新的“由旧宽泛归类导致的实际误译”。D01 现行两线已经按迷魂更正。D05/D06 各两线（共四张卡）为“证据不足”：源码机制已明确，欠缺的是能证明英文叙述必须技术名化的语义依据；保留当前译文，交独立 translation-reviewer 复审，获得用户认可的明确语义结论后才重入阶段 C。不能仅凭 ENCH_DAZED 认定 trance/mesmerised 的叙述翻译错误。

稳定线 P03（辛诵经诗句）、D08（巨口负面形态说明）存在英文回退/无中文精确键，是覆盖观察，非已证实的 D-C-096 误分类后果；本任务不补资产。D08 的机制确为 add_beholder，不是纯拟人比喻。

版本差异集中于：trunk 完整 piety note 键 / stable 拼接；龙召唤描述 divine abilities / Invocations；trunk 新 Hint 条目 / stable 旧 Source 整段；旧 exclusion 计数键；上述稳定线两个无中译路径。A01 两线实际消费者都带尾空格。当前结论不要求跨版本补造另一线接口。

附带范围提示：D12 召唤物的 drain 措辞是否准确属于另一个效果语义问题；此卡仅确认 daze→眩晕，不以“保留”宣称整段描述所有效果均通过审查。

## 逐项证据

每卡的“英文/中文”均为冻结条目完整内容，保留字面 `\n`、占位符、拼接片段与语境键；描述类键另列完整正文。共享链可跨卡引用，不用词根代替机制。缺失项不虚构本线译文；恢复死键时须重新查消费者。

### trunk

#### A01 · aptitude

精确键 `The species aptitude is in <white>white</white>.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:12883`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:12883`。

```text
English: The species aptitude is in <white>white</white>.
中文: 
种族资质以<white>白色</white>显示。
```

实际生产键补充（`repr` 显示尾空格）：`'The species aptitude is in <white>white</white>. '`；`crawl-ref/source/dat/i18n/zh/source.txt:29507`。

```text
English: The species aptitude is in <white>white</white>. 
中文: 
种族资质以<white>白色</white>显示。
```

当前调用链/机制证据：`crawl-ref/source/skill-menu.cc:1855`。

独立语义与旧决定适用性：skill-menu 实际查询带尾部空格的完整键；冻结选择器无尾空格，是旧死键。补充精确消费者键如下，两线当前译文均“种族资质以白色显示”。技能资质机制成立；不把死键冒充消费者。

**结论：保留（有证据）。**

#### A02 · aptitude

精确键 `<w>~</w>: Macros help\n<w>&</w>: Options help\n<w>%</w>: Table of aptitudes\n<w>/</w>: Lookup description\n<w>Q</w>: FAQ\n`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:43389`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:43389`。

```text
English: <w>~</w>: Macros help\n<w>&</w>: Options help\n<w>%</w>: Table of aptitudes\n<w>/</w>: Lookup description\n<w>Q</w>: FAQ\n
中文: <w>~</w>：宏帮助\n<w>&</w>：选项帮助\n<w>%</w>：资质表\n<w>/</w>：查找说明\n<w>Q</w>：常见问题\n
```

当前调用链/机制证据：`crawl-ref/source/command.cc:924`。

独立语义与旧决定适用性：command 查询完整多行快捷键帮助，% 打开 Table of aptitudes；“资质表”是技能训练参数表，成立。

**结论：保留（有证据）。**

#### A03 · aptitude

精确键 `HINT_SKILL_COSTS`；资产 `crawl-ref/source/dat/descript/zh/hints.txt:819`；英文依据 `crawl-ref/source/dat/descript/hints.txt:1111`。

```text
English: 
The training cost (in <cyan>cyan</cyan>) shows the experience cost to raise the
given skill one level, relative to the cost of raising an aptitude zero skill
from level zero to level one.
中文: 
训练成本（以<cyan>青色</cyan>显示）表示将指定技能提升一级所需的经验值，以资质为零的技能从零级升到一级所需的经验值为基准。
```

当前调用链/机制证据：`crawl-ref/source/hints.cc:1712`、`crawl-ref/source/skills.cc:193`。

独立语义与旧决定适用性：trunk hints_skill_costs_info 读取 HINT_SKILL_COSTS；skill_cost_baseline 取 Human Fighting 0→1 的经验基准，scaled_skill_cost 与其比值。完整中文保留零资质零级升一级，成立。stable 没有新 Hint 键，实际版本见 A05。

**结论：保留（有证据）。**

#### A04 · aptitude

精确键 `Dowan`；资产 `crawl-ref/source/dat/descript/zh/monsters.txt:106`；英文依据 `crawl-ref/source/dat/descript/monsters.txt:134`。

```text
English: 
A beautiful but vain deep elf with an aptitude for magic and little else. His
skills are the perfect complement of his twin sister Duvessa's fighting prowess.
In search of more powerful spells, he journeys to the surface with his sister.
中文: 
一个美丽但高傲的地底精灵，有着魔法天赋，但除此之外，就没什么了。
他的技能是对他的双胞胎妹妹杜维莎的格斗技能的完美补充。
为寻求更强大的魔法，他和他的妹妹一起前往地表。
```

当前调用链/机制证据：`crawl-ref/source/describe.cc:7945`、`crawl-ref/source/describe.cc:8399`、`crawl-ref/source/describe.cc:8401`。

独立语义与旧决定适用性：Dowan 怪物资料是人物叙述“魔法天赋”，不是物种各技能训练倍率；普通 aptitude 不套资质，当前保留。

**结论：保留（有证据）。**

#### A05 · aptitude

精确键 `The training cost (in <cyan>cyan</cyan>) shows the experience cost to raise the given skill one level, relative to the cost of raising an aptitude zero skill from level zero to level one.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:43596`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:43596`。

```text
English: The training cost (in <cyan>cyan</cyan>) shows the experience cost to raise the given skill one level, relative to the cost of raising an aptitude zero skill from level zero to level one.
中文: 训练成本（以<cyan>青色</cyan>显示）表示将指定技能提升一级所需的经验值，相对于当前
```

当前调用链/机制证据：`crawl-ref/source/skills.cc:193`。

独立语义与旧决定适用性：stable hints 仍用此完整 T_ 解释训练消耗相对零资质0→1基准；中文机制条件完整。trunk 转新 Hint 接口 A03，此旧 Source 项不是当前消费者。

**结论：不适用。**

生命周期/处理：本线不存在该中文槽、已有另一接口，或当前生产不再读取该旧键；不据此更改资产。若恢复消费者，重新验证。

#### B01 · barbs

精确键 `crystal echidna`；资产 `crawl-ref/source/dat/descript/zh/monsters.txt:835`；英文依据 `crawl-ref/source/dat/descript/monsters.txt:1098`。

```text
English: 
A spiny, long snouted rodent grown out of pure living crystal. It is
immune to most forms of magic and hurls both crystallising shots and painful
barbs.
中文: 
一个由纯净的活水晶生成的多刺、长鼻啮齿动物。它免疫大多数形式的魔法，
既能射击使目标结晶，也能投掷令人剧痛的倒刺。
```

当前调用链/机制证据：`crawl-ref/source/mon-spell.h:648`、`crawl-ref/source/beam.cc:4531`。

独立语义与旧决定适用性：水晶针鼹的攻击包括结晶射击及投掷倒刺；命中由 beam 对玩家调用 barb_player。正文的多刺外形与射出的倒刺分别成立；不能因短标签“尖刺”例外反推正文。

**结论：保留（有证据）。**

#### B02 · barbs

精确键 `Barbs status`；资产 `crawl-ref/source/dat/descript/zh/status.txt:172`；英文依据 `crawl-ref/source/dat/descript/status.txt:222`。

```text
English: 
There are barbs embedded in your skin, and moving around will cause you to take
damage. Remaining in place for a short time will allow you to remove the barbs
without taking damage.
中文: 
有倒刺扎入你的皮肤，移动时会受到伤害。
在原地停留片刻，就能移除这些倒刺而不受伤害。
```

当前调用链/机制证据：`crawl-ref/source/movement.cc:152`、`crawl-ref/source/movement.cc:174`、`crawl-ref/source/player-reacts.cc:1102`、`crawl-ref/source/player-reacts.cc:1556`。

独立语义与旧决定适用性：移动触发 _apply_barbs_damage，静止可 extract_barbs 并减持续时间。皮肤扎入与排出的对象是倒刺，正文用“倒刺”成立。

**结论：保留（有证据）。**

#### B03 · barbs

精确键 `status|Barbs`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:40551`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:40551`。

```text
English: Barbs
中文: 尖刺
```

当前调用链/机制证据：`crawl-ref/source/duration-data.h:529`、`crawl-ref/source/status.cc:201`、`crawl-ref/source/status.cc:205`、`crawl-ref/source/status.cc:207`。

独立语义与旧决定适用性：DUR_BARBS 的 light_text 经 status 的 C_("status",...) 显示；这是 D-C-098 明定的短标签“尖刺”例外。保留；普通正文不据此改名。

**结论：保留（有证据）。**

#### D01 · daze / non-Dazed

精确键 `You break out of your daze.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:22213`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:22213`。

```text
English: You break out of your daze.
中文: 你摆脱了迷魂。
```

当前调用链/机制证据：`crawl-ref/source/duration-data.h:869`、`crawl-ref/source/duration-data.h:868`。

独立语义与旧决定适用性：DUR_MESMERISED 结束清除 beholders；trunk 在回调直接发消息，stable 在持续时间结束分发 T_(endmsg) 并清除 beholders。当前“摆脱了迷魂”已更正，不能由 daze 词根回改“眩晕”。旧 daze 归类不适用；当前迷魂译文有证据保留。

**结论：保留（有证据）。**

#### D02 · daze / non-Dazed

精确键 `You snap out of the daze.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:18538`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:18538`。

```text
English: You snap out of the daze.
中文: 你从眩晕中清醒过来。
```

当前调用链/机制证据：`crawl-ref/source/player.cc:8678`。

独立语义与旧决定适用性：player 的 break_daze 分支清除 DUR_DAZED 并给予眩晕免疫；“从眩晕中清醒过来”对应实际 Dazed，适用成立。

**结论：保留（有证据）。**

#### D03 · daze / non-Dazed

精确键 `%s snaps out of %s daze.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:1834`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:1834`。

```text
English: %s snaps out of %s daze.
中文: %s从%s眩晕中清醒过来。
```

当前调用链/机制证据：`crawl-ref/source/mon-behv.cc:1254`。

独立语义与旧决定适用性：mon-behv 先确认 ENCH_DAZED，再在新鲜效果保护期后删除该附魔并发恢复消息；“眩晕”成立，不同于 D01。

**结论：保留（有证据）。**

#### D04 · daze / non-Dazed

精确键 ` is dazed by your recitation.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:35613`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:35613`。

```text
English:  is dazed by your recitation.
中文: 被你的吟诵弄得眩晕了。
```

当前调用链/机制证据：`crawl-ref/source/god-abil.cc:1089`。

独立语义与旧决定适用性：辛诵经 zin_eff::daze 分支调用 mon->daze 后才发此消息；当前眩晕术语有直接依据。

**结论：保留（有证据）。**

#### D05 · daze / non-Dazed

精确键 `%s trance deepens.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:36073`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:36073`。

```text
English: %s trance deepens.
中文: %s恍惚状态加深了。
```

当前调用链/机制证据：`crawl-ref/source/mon-cast.cc:6287`、`crawl-ref/source/mon-cast.cc:6248`。

独立语义与旧决定适用性：_mesmerise_los 对已带 ENCH_DAZED 的怪物发 trance deepens 并延长附魔；对玩家则走 beholder。英文在怪物分支刻意用 trance 叙述；当前“恍惚状态加深”是否必须替成技术标签，现有术语作用域不足以裁定。机制证据充分，语义取舍待独立复审；不能仅凭 enum 自动改。

**结论：证据不足。**

延期责任：独立 translation-reviewer；重入条件：区分技术状态名与英文叙述的明确语义证据及维护者认可。当前译文保留，不自动加入 reject 或提出批量替换。

#### D06 · daze / non-Dazed

精确键 `%s is mesmerised by %s!`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:36076`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:36076`。

```text
English: %s is mesmerised by %s!
中文: %1$s被%2$s迷住了！
```

当前调用链/机制证据：`crawl-ref/source/mon-cast.cc:6289`、`crawl-ref/source/mon-cast.cc:6248`。

独立语义与旧决定适用性：_mesmerise_los 首次对怪物施加 ENCH_DAZED 时发 mesmerised 消息；玩家同施法走 add_beholder。当前“迷住了”忠实叙述英文，但是否造成玩家与怪物状态混淆需复审；不以词根或状态 enum 单独决定。

**结论：证据不足。**

延期责任：独立 translation-reviewer；重入条件：区分技术状态名与英文叙述的明确语义证据及维护者认可。当前译文保留，不自动加入 reject 或提出批量替换。

#### D07 · daze / non-Dazed

精确键 `%s is briefly mesmerised by your gaze.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:1519`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:1519`。

```text
English: %s is briefly mesmerised by your gaze.
中文: %s被你的凝视短暂迷住了。
```

当前调用链/机制证据：`crawl-ref/source/transform.cc:2962`。

独立语义与旧决定适用性：vampire_mesmerism_check 的此消息在 Will 抵抗成功的 else 分支，只扣 speed_increment 10；失败分支才 mon.daze。该消息既不设置 DUR_MESMERISED，也不设置 ENCH_DAZED。“短暂迷住”应按叙述处理，技术眩晕规则不适用。

**结论：保留（有证据）。**

#### D08 · daze / non-Dazed

精确键 `Your maw sometimes becomes mesmerised by tasty morsels.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:25213`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:25213`。

```text
English: Your maw sometimes becomes mesmerised by tasty morsels.
中文: 你的巨口有时会被美味的食物迷住。
```

当前调用链/机制证据：`crawl-ref/source/dat/forms/maw.yaml:13`、`crawl-ref/source/transform.cc:2916`、`crawl-ref/source/mutation.cc:698`、`crawl-ref/source/mutation.cc:702`、`crawl-ref/source/mutation.cc:717`。

独立语义与旧决定适用性：maw.yaml badmut 经 Form 负面假突变描述进入 T_；maw_hunger_check 对可食目标调用 you.add_beholder(...,true,6..10)。这是实际玩家迷魂，绝非仅因拟人比喻即可排除机制。trunk“被美味的食物迷住”成立；stable 有英文及机制但无本中文键，为独立覆盖缺口。

**结论：保留（有证据）。**

#### D09 · daze / non-Dazed

精确键 `You are mesmerised.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:8836`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:8836`。

```text
English: You are mesmerised.
中文: 你陷入了迷魂状态。
```

当前调用链/机制证据：`crawl-ref/source/status.cc:420`。

独立语义与旧决定适用性：STATUS_BEHELD 由 you.beheld() 产生完整状态说明，当前“迷魂”符合 beholder 机制，Dazed 规则不适用。

**结论：保留（有证据）。**

#### D10 · daze / non-Dazed

精确键 `Mesmerise spell`；资产 `crawl-ref/source/dat/descript/zh/spells.txt:854`；英文依据 `crawl-ref/source/dat/descript/spells.txt:1382`。

```text
English: 
Attempts to entrance all enemies in sight. Adventurers who fail to resist will
become unable to move away from the caster, while other creatures will become
dazed outright.

Leaving the caster's line of sight will end the movement-controlling effect.
中文: 
尝试迷住视野内所有敌人。未能抵抗的冒险者会无法远离施法者，
其他生物则会直接陷入眩晕。

离开施法者视野会结束控制移动的效果。
```

当前调用链/机制证据：`crawl-ref/source/mon-cast.cc:6248`。

独立语义与旧决定适用性：Mesmerise 对玩家限制远离施法者，对怪物走 _mesmerise_los 的 ENCH_DAZED。当前完整中文区分玩家迷魂与其他生物眩晕；仅在对应目标分支适用，不按标题强行同名。

**结论：保留（有证据）。**

#### D11 · daze / non-Dazed

精确键 `Enfeeble spell`；资产 `crawl-ref/source/dat/descript/zh/spells.txt:451`；英文依据 `crawl-ref/source/dat/descript/spells.txt:671`。

```text
English: 
Overwhelms an enemy with malignant energies, irresistibly weakening their melee
attacks and reducing the power of their spells. It will additionally daze and
blind any foe that fails to resist the full force of the curse - even those
without visual senses!
中文: 
用邪恶能量压倒敌人，不可抗拒地削弱其近战攻击并降低法术威力。
它还会使无法抵抗全部诅咒力量的敌人眩晕和失明，
即使目标没有视觉感官也不例外。
```

当前调用链/机制证据：`crawl-ref/source/spl-monench.cc:153`、`crawl-ref/source/spl-monench.cc:168`、`crawl-ref/source/spl-monench.cc:205`。

独立语义与旧决定适用性：Enfeeble 的怪物路径加 ENCH_DAZED/mon.daze，玩家路径 you.daze；完整描述中“眩晕”成立。本卡不重审衰弱的全部数值。

**结论：保留（有证据）。**

#### D12 · daze / non-Dazed

精确键 `Cacophony status`；资产 `crawl-ref/source/dat/descript/zh/status.txt:832`；英文依据 `crawl-ref/source/dat/descript/status.txt:1110`。

```text
English: 
You are noisily attacking with all of your armour. Every piece of armour you
haunt currently moves of its own volition; any damage it takes will not affect
you, you can freely fire through it, and its attacks may daze, drain, or confuse
your enemies.
中文: 
你正驱使所有护甲喧闹地攻击。你附身的每件护甲都会自主行动；
它们受到的任何伤害都不会影响你，你也可以自由地穿过它们射击。
它们的攻击可能使敌人眩晕、汲取其生命力，或使其陷入混乱。
```

当前调用链/机制证据：`crawl-ref/source/ability.cc:3131`、`crawl-ref/source/dat/mons/haunted-armour.yaml:8`、`crawl-ref/source/melee-attack.cc:4858`。

独立语义与旧决定适用性：Cacophony 召唤 MON_SUMM_CACOPHONY 的 haunted armour；其 trickster 攻击从效果集中选 ENCH_DAZED 后调用 defender->daze。“眩晕”成立。仅核对该术语；其他攻击效果措辞不在此结论内。

**结论：保留（有证据）。**

#### D13 · daze / non-Dazed

精确键 `burstshroom`；资产 `crawl-ref/source/dat/descript/zh/monsters.txt:3163`；英文依据 `crawl-ref/source/dat/descript/monsters.txt:950`。

```text
English: 
A rapidly-growing mushroom whose life-cycle culminates in an explosive release
of spores. These spores have a mild psychoactive effect and can sometimes daze
creatures who breathe them in.
中文: 
一种快速生长的蘑菇，其生命周期以孢子的爆发性释放为高潮。
这些孢子具有轻微的致幻效果，有时会使吸入它们的生物眩晕。
```

当前调用链/机制证据：`crawl-ref/source/mon-act.cc:1379`、`crawl-ref/source/mon-act.cc:1437`。

独立语义与旧决定适用性：_burstshroom_grow 的孢子攻击对合适目标调用 targ->daze；当前“眩晕”有机制依据，保留。

**结论：保留（有证据）。**

#### D14 · daze / non-Dazed

精确键 `dazed monstatus`；资产 `crawl-ref/source/dat/descript/zh/monstatus.txt:158`；英文依据 `crawl-ref/source/dat/descript/monstatus.txt:174`。

```text
English: 
This creature is temporarily unable to act, but any hostile action will cause it to
immediately regain its senses.
中文: 
这个生物暂时无法行动，但任何敌对行为将使其立即恢复神智。
```

当前调用链/机制证据：`crawl-ref/source/mon-info.cc:86`、`crawl-ref/source/mon-info-flag-name.h:104`、`crawl-ref/source/directn.cc:1851`、`crawl-ref/source/describe.cc:8368`。

独立语义与旧决定适用性：ENCH_DAZED 映射 MB_DAZED，旗标描述键 dazed 经 attribute/status descriptor 送入怪物说明。完整 dazed monstatus 正文描述不能行动、遇敌对行为即恢复；正文没有强塞状态名，配套短名在 D16 为眩晕。当前语义保留。

**结论：保留（有证据）。**

#### D15 · daze / non-Dazed

精确键 `You are too mesmerised to rage.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:45342`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:45342`。

```text
English: You are too mesmerised to rage.
中文: 你深受迷魂影响，无法狂暴。
```

当前调用链/机制证据：`crawl-ref/source/player-act.cc:754`。

独立语义与旧决定适用性：player-act 在 beheld 且非 demonaxe 的分支拒绝狂暴；消息描述玩家迷魂限制，不是 Dazed。当前迷魂保留。

**结论：保留（有证据）。**

#### D16 · daze / non-Dazed

精确键 `dazed`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:21202`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:21202`。

```text
English: dazed
中文: 眩晕
```

当前调用链/机制证据：`crawl-ref/source/mon-info.cc:86`、`crawl-ref/source/mon-info-flag-name.h:104`、`crawl-ref/source/mon-act.cc:2276`。

独立语义与旧决定适用性：ENCH_DAZED→MB_DAZED→dazed 状态名；mon-act 对该附魔消耗行动能量并返回。这里是实际 Dazed 的短名，眩晕成立。

**结论：保留（有证据）。**

#### D17 · daze / non-Dazed

精确键 `Siren Song spell`；资产 `crawl-ref/source/dat/descript/zh/spells.txt:1142`；英文依据 `crawl-ref/source/dat/descript/spells.txt:1962`。

```text
English: 
Sings a haunting song that mesmerises nearby listeners. Adventurers who fail to
resist will become unable to move away from the singer, while other creatures
will become dazed outright.

Leaving the caster's line of sight will end the movement-controlling effect.
中文: 
唱出萦绕心头的歌，迷住附近听众。未能抵抗的冒险者会无法远离歌者，
其他生物则会直接陷入眩晕。

离开施法者视野会结束控制移动的效果。
```

当前调用链/机制证据：`crawl-ref/source/mon-cast.cc:6248`。

独立语义与旧决定适用性：Siren Song 使用同一 _mesmerise_los：玩家 add_beholder，怪物 ENCH_DAZED。完整描述分别写无法远离及眩晕；分目标成立，不能全篇只用一种状态名。

**结论：保留（有证据）。**

#### D18 · daze / non-Dazed

精确键 `Avatar Song spell`；资产 `crawl-ref/source/dat/descript/zh/spells.txt:71`；英文依据 `crawl-ref/source/dat/descript/spells.txt:75`。

```text
English: 
Sings a powerfully haunting song. Adventurers who fail to resist will become
unable to move away from the singer (and will sometimes be drawn closer
involuntarily), while other creatures will become dazed outright.

In addition, it may call forth drowned souls from any nearby bodies of deep
water.

Leaving the caster's line of sight will end the movement-controlling effect.
中文: 
唱出一首极具魔力、萦绕心头的歌。未能抵抗的冒险者会无法远离歌者
（有时还会不由自主地被拉近），其他生物则会直接陷入眩晕。

此外，它可能从附近的任何深水中召来溺魂。

离开施法者视野会结束控制移动的效果。
```

当前调用链/机制证据：`crawl-ref/source/mon-cast.cc:6248`。

独立语义与旧决定适用性：Avatar Song 的控制路径同 D17，并另有溺亡之魂效果；此卡只审迷魂/眩晕两种目标机制。中文对应成立，不据此声称其他段落全审通过。

**结论：保留（有证据）。**

#### F01 · noxious fumes

精确键 `noxious fumes`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:18754`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:18754`。

```text
English: noxious fumes
中文: 毒烟
```

当前调用链/机制证据：`crawl-ref/source/cloud.cc:103`、`crawl-ref/source/cloud.cc:929`、`crawl-ref/source/cloud.cc:1027`、`crawl-ref/source/cloud.cc:1219`。

独立语义与旧决定适用性：cloud 类型表将 CLOUD_MEPHITIC 命名 noxious fumes；接触效果是混乱，受抗毒等条件影响。名称“毒烟”成立，不能与 CLOUD_POISON 的“毒气”混用。

**结论：保留（有证据）。**

#### F02 · noxious fumes

精确键 `poison gas`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:18757`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:18757`。

```text
English: poison gas
中文: 毒气
```

当前调用链/机制证据：`crawl-ref/source/cloud.cc:116`、`crawl-ref/source/cloud.cc:1029`、`crawl-ref/source/cloud.cc:1275`。

独立语义与旧决定适用性：CLOUD_POISON 的 poison gas 会施加中毒伤害；“毒气”成立，和 F01 类型不同。

**结论：保留（有证据）。**

#### F03 · noxious fumes

精确键 `noxious fumes cloud`；资产 `crawl-ref/source/dat/descript/zh/clouds.txt:11`；英文依据 `crawl-ref/source/dat/descript/clouds.txt:12`。

```text
English: 
A cloud of vile, choking fumes. Any creature spending time in it will be at
risk of becoming confused by the gases, unless resistant to poison. Tougher,
more experienced creatures are less likely to be affected.
中文: 
一团呛人又有毒的云。
任何生物身处其中，除非具有毒抗，否则都有陷入混乱的危险。
越坚韧、经验等级越高的生物不太会受此影响。
```

当前调用链/机制证据：`crawl-ref/source/describe.cc:3520`、`crawl-ref/source/cloud.cc:929`、`crawl-ref/source/cloud.cc:1027`、`crawl-ref/source/cloud.cc:1219`。

独立语义与旧决定适用性：get_cloud_desc 用英文云名加 cloud 查询长描述；正文的 vile/choking fumes 是性质泛称，并说明混乱及抗毒。当前“呛人又有毒的云”不要求每处重复云专名“毒烟”，适用范围缩小为名称槽。

**结论：保留（有证据）。**

#### F04 · noxious fumes

精确键 `poison gas cloud`；资产 `crawl-ref/source/dat/descript/zh/clouds.txt:23`；英文依据 `crawl-ref/source/dat/descript/clouds.txt:26`。

```text
English: 
A cloud of deadly poison. Any creature without resistance to poison will be
both poisoned and directly harmed by time spent in it.
中文: 
一团有着致命毒性的云。任何没有毒抗的生物，在里面就会中毒并直接受到伤害。
```

当前调用链/机制证据：`crawl-ref/source/describe.cc:3520`、`crawl-ref/source/cloud.cc:1029`、`crawl-ref/source/cloud.cc:1275`。

独立语义与旧决定适用性：poison gas cloud 描述中毒和毒伤；属于 CLOUD_POISON，不机械套 noxious fumes 的云名术语。当前语义保留。

**结论：保留（有证据）。**

#### F05 · noxious fumes

精确键 `Mephitic Cloud spell`；资产 `crawl-ref/source/dat/descript/zh/spells.txt:848`；英文依据 `crawl-ref/source/dat/descript/spells.txt:1376`。

```text
English: 
Conjures a fragile flask that explodes into short-lived clouds of noxious fumes.
These clouds may cause confusion in any creature not resistant to poison.
Tougher, more experienced creatures are less likely to be affected.
中文: 
召出一个脆弱的瓶子，瓶子爆炸后形成一团短暂存在的毒烟。
烟雾可能使任何没有毒抗的生物陷入混乱。
越坚韧、经验等级越高的生物越不容易受影响。
```

当前调用链/机制证据：`crawl-ref/source/beam.cc:2547`、`crawl-ref/source/beam.cc:6889`、`crawl-ref/source/cloud.cc:929`、`crawl-ref/source/cloud.cc:1027`、`crawl-ref/source/cloud.cc:1219`。

独立语义与旧决定适用性：Mephitic Cloud 产生 CLOUD_MEPHITIC，完整施法描述中的 noxious fumes 是这个实际云类型，毒烟成立。

**结论：保留（有证据）。**

#### F06 · noxious fumes

精确键 `Noxious Cloud spell`；资产 `crawl-ref/source/dat/descript/zh/spells.txt:919`；英文依据 `crawl-ref/source/dat/descript/spells.txt:1483`。

```text
English: 
Creates a large cloud of noxious fumes, which may cause confusion.
中文: 
产生大量毒烟，这可能会引起混乱。
```

当前调用链/机制证据：`crawl-ref/source/beam.cc:2498`、`crawl-ref/source/spl-data.h:1367`。

独立语义与旧决定适用性：bolt::get_cloud_type 对 SPELL_NOXIOUS_CLOUD 明确返回 CLOUD_MEPHITIC；不是由法术名猜测。当前毒烟成立。

**结论：保留（有证据）。**

#### F07 · noxious fumes

精确键 `tutorial4 aiming_clouds`；资产 `crawl-ref/source/dat/descript/zh/tutorial.txt:500`；英文依据 `crawl-ref/source/dat/descript/tutorial.txt:551`。

```text
English: 
Mephitic Cloud covers an area in noxious fumes when cast, and you'll be able to
see the area it affects as you target it. Try to catch multiple enemies in a
single cloud in order to be more efficient with your magic.
中文: 
施放迷瘴云时，毒烟会覆盖一片区域；瞄准时，你会看到它影响的范围。
设法将多个敌人捕在一片云中，以更有效地利用你的魔法。
```

当前调用链/机制证据：`crawl-ref/source/dat/des/tutorial/lesson4.des:53`。

独立语义与旧决定适用性：教学 lesson4 的 aiming_clouds marker 读取同名教学说明；文本说明 Mephitic Cloud 的瞄准与混乱云。当前“毒烟”与云类型成立，教学其他操作指令不在此卡重审范围。

**结论：保留（有证据）。**

#### P01 · piety

精确键 `A donation of $%d equates to an increase of piety by %d.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:2599`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:2599`。

```text
English: A donation of $%d equates to an increase of piety by %d.
中文: 捐赠$%d相当于增加%d点虔诚值。
```

当前调用链/机制证据：`crawl-ref/source/god-abil.cc:285`。

独立语义与旧决定适用性：数字捐赠换取 piety 资源；译作“虔诚值”有机制依据。适用：资源义成立，不推广到信仰叙述。

**结论：保留（有证据）。**

#### P02 · piety

精确键 `You feel less pious.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:10066`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:10066`。

```text
English: You feel less pious.
中文: 你感到自己的虔诚值降低了。
```

当前调用链/机制证据：`crawl-ref/source/player-equip.cc:2586`、`crawl-ref/source/art-func.h:1974`。

独立语义与旧决定适用性：卸除信仰护符（trunk 另有 FORGEWARDEN）计算 raw_piety/3 后调用 lose_piety；这里不是单纯情绪描写。“虔诚值降低”成立。

**结论：保留（有证据）。**

#### P03 · piety

精确键 `To the devout, Zin provideth. From the rest...`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:53791`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:53791`。

```text
English: To the devout, Zin provideth. From the rest...
中文: 辛供养虔信者。至于其余之众……
```

当前调用链/机制证据：`crawl-ref/source/god-abil.cc:375`、`crawl-ref/source/god-abil.cc:629`。

独立语义与旧决定适用性：辛诵经诗句描写神供养虔信者，不是资源增减；trunk 经 T_ 翻译后替换经文槽。适用：叙述义缩小为虔信者，不加“值”。stable 的 book_of_zin 文本直接组装，当前无此中文键，见缺失说明。

**结论：保留（有证据）。**

#### P04 · piety

精确键 `Pious`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:14897`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:14897`。

```text
English: Pious
中文: 虔诚者
```

当前调用链/机制证据：`crawl-ref/source/describe-god.cc:140`、`crawl-ref/source/describe-god.cc:252`、`crawl-ref/source/describe-god.cc:286`、`crawl-ref/source/describe-god.cc:300`。

独立语义与旧决定适用性：god_title 按 _piety_level 选称号，再由 _render_god_title 调 C_("god title",key)；两线无 god title|Pious 专键，回退普通 Pious。称号称人为“虔诚者”，不是把资源命名为人。适用：称号例外，保留。

**结论：保留（有证据）。**

#### P05 · piety

精确键 `piety note|Reached %1$s piety under %2$s`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:48383`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:48383`。

```text
English: Reached %1$s piety under %2$s
中文: 对%2$s的虔诚等级达到了%1$s。
```

当前调用链/机制证据：`crawl-ref/source/notes.cc:182`、`crawl-ref/source/notes.cc:969`。

独立语义与旧决定适用性：NOTE_PIETY_RANK 记录星级门槛。trunk 为完整语境键并重排占位符；stable 用 Reached + 星号 + piety under + 神名拼接。这里是“虔诚等级”，不是数值资源单位；两线需分别按实际接口判断。

**结论：保留（有证据）。**

#### P06 · piety

精确键 `It occasionally summons a dragon when using Invocations with hostile monsters in sight. Chance is 10% + twice the piety cost of the ability used.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:31758`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:31758`。

```text
English: It occasionally summons a dragon when using Invocations with hostile monsters in sight. Chance is 10% + twice the piety cost of the ability used.
中文: 视野内有敌对怪物时使用祈神能力，偶尔会召唤一条龙。触发几率为10% + 所使用能力的虔诚消耗的两倍。
```

当前调用链/机制证据：`crawl-ref/source/art-data.txt:1004`。

独立语义与旧决定适用性：stable 的 Invocations 版本仍在 art-data；trunk 生产描述已改 divine abilities，旧 Invocations 只余 Source 兼容条目及直接查询测试。piety cost 是资源花费；保留中文，不把旧键当现行生产缺陷。

**结论：不适用。**

生命周期/处理：本线不存在该中文槽、已有另一接口，或当前生产不再读取该旧键；不据此更改资产。若恢复消费者，重新验证。

#### P07 · piety

精确键 `It occasionally summons a dragon when using divine abilities with hostile monsters in sight. Chance is 10% + twice the piety cost of the ability used.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:31980`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:31980`。

```text
English: It occasionally summons a dragon when using divine abilities with hostile monsters in sight. Chance is 10% + twice the piety cost of the ability used.
中文: 视野内有敌对怪物时使用神祇能力，它偶尔会召唤一条龙。触发几率为10% + 所用能力消耗的虔诚值的两倍。
```

当前调用链/机制证据：`crawl-ref/source/art-data.txt:1004`。

独立语义与旧决定适用性：trunk art-data 当前描述 divine abilities，概率取决于技能所花 piety，故“虔诚值消耗”成立。stable 生产版本是 P06，无本键；不向另一版本补造条目。

**结论：保留（有证据）。**

#### P08 · piety

精确键 ` piety under `；资产 `crawl-ref/source/dat/i18n/zh/source.txt:37859`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:37859`。

```text
English:  piety under 
中文: 的虔诚信徒，虔诚度
```

当前调用链/机制证据：`crawl-ref/source/notes.cc:182`、`crawl-ref/source/notes.cc:969`。

独立语义与旧决定适用性：trunk 旧 piety under 片段已被 P05 整句替代，旧“虔诚度”属于非生产死键。stable 活跃的同片段已作为 P05 复合身份核对；此槽为空以免重复。旧快照/死键不按资源规则批改。

**结论：不适用。**

生命周期/处理：本线不存在该中文槽、已有另一接口，或当前生产不再读取该旧键；不据此更改资产。若恢复消费者，重新验证。

#### T01 · travel exclusion

精确键 `This transporter is marked as excluded!`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:7962`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:7962`。

```text
English: This transporter is marked as excluded!
中文: 这个传送器设有禁区标记！
```

当前调用链/机制证据：`crawl-ref/source/main.cc:1598`。

独立语义与旧决定适用性：main 的传送器检查排除标记并询问用户；标记限制自动寻路而非绝对禁止使用。中文“禁区标记”成立。

**结论：保留（有证据）。**

#### T02 · travel exclusion

精确键 `This %s%s is marked as excluded! Open it anyway?`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:43767`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:43767`。

```text
English: This %s%s is marked as excluded! Open it anyway?
中文: 这个%s%s设有禁区标记！仍要打开它吗？
```

当前调用链/机制证据：`crawl-ref/source/player.cc:9394`。

独立语义与旧决定适用性：player 的开门确认检查 excluded 标记后仍允许用户确认打开；“禁区标记”不应改成不能手动进入的物理禁制。当前保留。

**结论：保留（有证据）。**

#### T03 · travel exclusion

精确键 `\nTo avoid accidentally opening a door you'd rather remain closed during travel or autoexplore, you can mark it with an exclusion from the map view (<w>X</w>) with <w>ee</w> while your cursor is on the grid in question. Such an exclusion will prevent autotravel from ever entering that grid until you remove the exclusion with another press of <w>Xe</w>.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:43698`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:43698`。

```text
English: \nTo avoid accidentally opening a door you'd rather remain closed during travel or autoexplore, you can mark it with an exclusion from the map view (<w>X</w>) with <w>ee</w> while your cursor is on the grid in question. Such an exclusion will prevent autotravel from ever entering that grid until you remove the exclusion with another press of <w>Xe</w>.
中文: \n为避免在旅行或自动探索时意外打开你希望保持关闭的门，你可以在光标位于该格时，从地图视图（<w>X</w>）中按<w>ee</w>将其标记为旅行禁区。此禁区标记会阻止自动旅行进入该格，直到你再次按<w>Xe</w>将其移除。
```

当前调用链/机制证据：`crawl-ref/source/hints.cc:2174`。

独立语义与旧决定适用性：stable hints 仍以整段 T_ 解释地图标记如何阻止 autotravel；trunk 已改为 HINT_DESCRIBE_CLOSED_DOOR，旧整段 Source 不再由该生产路径读取。stable 禁区译文成立，trunk 旧键只记录生命周期。

**结论：不适用。**

生命周期/处理：本线不存在该中文槽、已有另一接口，或当前生产不再读取该旧键；不据此更改资产。若恢复消费者，重新验证。

#### T04 · travel exclusion

精确键 `HINT_DESCRIBE_CLOSED_DOOR`；资产 `crawl-ref/source/dat/descript/zh/hints.txt:986`；英文依据 `crawl-ref/source/dat/descript/hints.txt:1429`。

```text
English: 
To avoid accidentally opening a door you'd rather remain closed during travel
or autoexplore, you can mark it with an exclusion from the map view
(<w>$cmd[CMD_DISPLAY_MAP]</w>) with
<w>$cmd[CMD_MAP_EXCLUDE_AREA]$cmd[CMD_MAP_EXCLUDE_AREA]</w> while your cursor
is on the square in question. Such an exclusion will prevent autotravel from
ever entering that grid until you remove the exclusion with another press of
<w>$cmd[CMD_DISPLAY_MAP]$cmd[CMD_MAP_EXCLUDE_AREA]</w>.
中文: 
为避免在旅行或自动探索时意外打开你希望保持关闭的门，你可以进入地图视图（<w>$cmd[CMD_DISPLAY_MAP]</w>），将光标移到该格上，按 <w>$cmd[CMD_MAP_EXCLUDE_AREA]$cmd[CMD_MAP_EXCLUDE_AREA]</w> 将其标记为禁区。此禁区会阻止自动旅行进入该格，直到你再次按 <w>$cmd[CMD_DISPLAY_MAP]$cmd[CMD_MAP_EXCLUDE_AREA]</w> 将其移除。
```

当前调用链/机制证据：`crawl-ref/source/hints.cc:2174`。

独立语义与旧决定适用性：trunk hints 的 _get_hint("HINT_DESCRIBE_CLOSED_DOOR") 读取当前长说明；stable 没有这个新接口。其禁区影响自动旅行、不剥夺手动开门能力，trunk 当前译文成立。

**结论：保留（有证据）。**

#### T05 · travel exclusion

冻结选择器：`['%d %sexclusion%s']`；本线无精确中文条目（P08 stable 是主动去重空槽）。

```text
参考检索键（不是本线中文）: %d %sexclusion%s
```

当前调用链/机制证据：`crawl-ref/source/exclude.cc:689`、`crawl-ref/source/dgn-overview.cc:1097`、`crawl-ref/source/dgn-overview.cc:1099`。

独立语义与旧决定适用性：旧复数字串没有当前生产调用者；exclude_set::get_exclusion_desc 已用独立单复数键，dgn-overview 传 display=true，持久化注记路径默认 false 保持英文。trunk 无旧条目，stable 旧译仍存；均不把兼容旧键或存档字段当现行 UI 修正。

**结论：不适用。**

生命周期/处理：本线不存在该中文槽、已有另一接口，或当前生产不再读取该旧键；不据此更改资产。若恢复消费者，重新验证。


### stable

#### A01 · aptitude

精确键 `The species aptitude is in <white>white</white>.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:12314`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:12314`。

```text
English: The species aptitude is in <white>white</white>.
中文: 
种族资质以<white>白色</white>显示。
```

实际生产键补充（`repr` 显示尾空格）：`'The species aptitude is in <white>white</white>. '`；`crawl-ref/source/dat/i18n/zh/source.txt:27410`。

```text
English: The species aptitude is in <white>white</white>. 
中文: 
种族资质以<white>白色</white>显示。
```

当前调用链/机制证据：`crawl-ref/source/skill-menu.cc:1832`。

独立语义与旧决定适用性：skill-menu 实际查询带尾部空格的完整键；冻结选择器无尾空格，是旧死键。补充精确消费者键如下，两线当前译文均“种族资质以白色显示”。技能资质机制成立；不把死键冒充消费者。

**结论：保留（有证据）。**

#### A02 · aptitude

精确键 `<w>~</w>: Macros help\n<w>&</w>: Options help\n<w>%</w>: Table of aptitudes\n<w>/</w>: Lookup description\n<w>Q</w>: FAQ\n`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:40533`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:40533`。

```text
English: <w>~</w>: Macros help\n<w>&</w>: Options help\n<w>%</w>: Table of aptitudes\n<w>/</w>: Lookup description\n<w>Q</w>: FAQ\n
中文: <w>~</w>：宏帮助\n<w>&</w>：选项帮助\n<w>%</w>：资质表\n<w>/</w>：查找说明\n<w>Q</w>：常见问题\n
```

当前调用链/机制证据：`crawl-ref/source/command.cc:924`。

独立语义与旧决定适用性：command 查询完整多行快捷键帮助，% 打开 Table of aptitudes；“资质表”是技能训练参数表，成立。

**结论：保留（有证据）。**

#### A03 · aptitude

冻结选择器：`['HINT_SKILL_COSTS']`；本线无精确中文条目（P08 stable 是主动去重空槽）。

```text
参考检索键（不是本线中文）: HINT_SKILL_COSTS
```

当前调用链/机制证据：`crawl-ref/source/skills.cc:189`。

独立语义与旧决定适用性：trunk hints_skill_costs_info 读取 HINT_SKILL_COSTS；skill_cost_baseline 取 Human Fighting 0→1 的经验基准，scaled_skill_cost 与其比值。完整中文保留零资质零级升一级，成立。stable 没有新 Hint 键，实际版本见 A05。

**结论：不适用。**

生命周期/处理：本线不存在该中文槽、已有另一接口，或当前生产不再读取该旧键；不据此更改资产。若恢复消费者，重新验证。

#### A04 · aptitude

精确键 `Dowan`；资产 `crawl-ref/source/dat/descript/zh/monsters.txt:119`；英文依据 `crawl-ref/source/dat/descript/monsters.txt:146`。

```text
English: 
A beautiful but vain deep elf with an aptitude for magic and little else. His
skills are the perfect complement of his twin sister Duvessa's fighting prowess.
In search of more powerful spells, he journeys to the surface with his sister.
中文: 
一个美丽但高傲的地底精灵，有着魔法天赋，但除此之外，就没什么了。
他的技能是对他的双胞胎妹妹杜维莎的格斗技能的完美补充。
为寻求更强大的魔法，他和他的妹妹一起前往地表。
```

当前调用链/机制证据：`crawl-ref/source/describe.cc:7255`、`crawl-ref/source/describe.cc:7666`、`crawl-ref/source/describe.cc:7668`。

独立语义与旧决定适用性：Dowan 怪物资料是人物叙述“魔法天赋”，不是物种各技能训练倍率；普通 aptitude 不套资质，当前保留。

**结论：保留（有证据）。**

#### A05 · aptitude

精确键 `The training cost (in <cyan>cyan</cyan>) shows the experience cost to raise the given skill one level, relative to the cost of raising an aptitude zero skill from level zero to level one.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:40728`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:40728`。

```text
English: The training cost (in <cyan>cyan</cyan>) shows the experience cost to raise the given skill one level, relative to the cost of raising an aptitude zero skill from level zero to level one.
中文: 训练成本（以<cyan>青色</cyan>显示）表示将指定技能提升一级所需的相对经验值，以资质为零的技能从零级升到一级所需的经验值为基准。
```

当前调用链/机制证据：`crawl-ref/source/hints.cc:1858`、`crawl-ref/source/skills.cc:189`。

独立语义与旧决定适用性：stable hints 仍用此完整 T_ 解释训练消耗相对零资质0→1基准；中文机制条件完整。trunk 转新 Hint 接口 A03，此旧 Source 项不是当前消费者。

**结论：保留（有证据）。**

#### B01 · barbs

精确键 `crystal echidna`；资产 `crawl-ref/source/dat/descript/zh/monsters.txt:858`；英文依据 `crawl-ref/source/dat/descript/monsters.txt:1080`。

```text
English: 
A spiny, long snouted rodent grown out of pure living crystal. It is
immune to most forms of magic and hurls both crystallising shots and painful
barbs.
中文: 
一个由纯净的活水晶生成的多刺、长鼻啮齿动物。它免疫大多数形式的魔法，
既能射击使目标结晶，也能投掷令人剧痛的倒刺。
```

当前调用链/机制证据：`crawl-ref/source/mon-spell.h:621`、`crawl-ref/source/beam.cc:4495`。

独立语义与旧决定适用性：水晶针鼹的攻击包括结晶射击及投掷倒刺；命中由 beam 对玩家调用 barb_player。正文的多刺外形与射出的倒刺分别成立；不能因短标签“尖刺”例外反推正文。

**结论：保留（有证据）。**

#### B02 · barbs

精确键 `Barbs status`；资产 `crawl-ref/source/dat/descript/zh/status.txt:172`；英文依据 `crawl-ref/source/dat/descript/status.txt:221`。

```text
English: 
There are barbs embedded in your skin, and moving around will cause you to take
damage. Remaining in place for a short time will allow you to remove the barbs
without taking damage.
中文: 
有倒刺扎入你的皮肤，移动时会受到伤害。
在原地停留片刻，就能移除这些倒刺而不受伤害。
```

当前调用链/机制证据：`crawl-ref/source/movement.cc:145`、`crawl-ref/source/movement.cc:167`、`crawl-ref/source/player-reacts.cc:993`、`crawl-ref/source/player-reacts.cc:1421`。

独立语义与旧决定适用性：移动触发 _apply_barbs_damage，静止可 extract_barbs 并减持续时间。皮肤扎入与排出的对象是倒刺，正文用“倒刺”成立。

**结论：保留（有证据）。**

#### B03 · barbs

精确键 `status|Barbs`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:37767`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:37767`。

```text
English: Barbs
中文: 尖刺
```

当前调用链/机制证据：`crawl-ref/source/duration-data.h:502`、`crawl-ref/source/status.cc:186`、`crawl-ref/source/status.cc:188`。

独立语义与旧决定适用性：DUR_BARBS 的 light_text 经 status 的 C_("status",...) 显示；这是 D-C-098 明定的短标签“尖刺”例外。保留；普通正文不据此改名。

**结论：保留（有证据）。**

#### D01 · daze / non-Dazed

精确键 `You break out of your daze.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:21337`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:21337`。

```text
English: You break out of your daze.
中文: 你摆脱了迷魂。
```

当前调用链/机制证据：`crawl-ref/source/duration-data.h:798`、`crawl-ref/source/duration-data.h:798`。

独立语义与旧决定适用性：DUR_MESMERISED 结束清除 beholders；trunk 在回调直接发消息，stable 在持续时间结束分发 T_(endmsg) 并清除 beholders。当前“摆脱了迷魂”已更正，不能由 daze 词根回改“眩晕”。旧 daze 归类不适用；当前迷魂译文有证据保留。

**结论：保留（有证据）。**

#### D02 · daze / non-Dazed

精确键 `You snap out of the daze.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:17797`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:17797`。

```text
English: You snap out of the daze.
中文: 你从眩晕中清醒过来。
```

当前调用链/机制证据：`crawl-ref/source/player.cc:8394`。

独立语义与旧决定适用性：player 的 break_daze 分支清除 DUR_DAZED 并给予眩晕免疫；“从眩晕中清醒过来”对应实际 Dazed，适用成立。

**结论：保留（有证据）。**

#### D03 · daze / non-Dazed

精确键 `%s snaps out of %s daze.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:1789`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:1789`。

```text
English: %s snaps out of %s daze.
中文: %s从%s眩晕中清醒过来。
```

当前调用链/机制证据：`crawl-ref/source/mon-behv.cc:1190`。

独立语义与旧决定适用性：mon-behv 先确认 ENCH_DAZED，再在新鲜效果保护期后删除该附魔并发恢复消息；“眩晕”成立，不同于 D01。

**结论：保留（有证据）。**

#### D04 · daze / non-Dazed

精确键 ` is dazed by your recitation.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:33111`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:33111`。

```text
English:  is dazed by your recitation.
中文: 被你的吟诵弄得眩晕了。
```

当前调用链/机制证据：`crawl-ref/source/god-abil.cc:1096`。

独立语义与旧决定适用性：辛诵经 zin_eff::daze 分支调用 mon->daze 后才发此消息；当前眩晕术语有直接依据。

**结论：保留（有证据）。**

#### D05 · daze / non-Dazed

精确键 `%s trance deepens.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:33562`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:33562`。

```text
English: %s trance deepens.
中文: %s恍惚状态加深了。
```

当前调用链/机制证据：`crawl-ref/source/mon-cast.cc:6084`、`crawl-ref/source/mon-cast.cc:6045`。

独立语义与旧决定适用性：_mesmerise_los 对已带 ENCH_DAZED 的怪物发 trance deepens 并延长附魔；对玩家则走 beholder。英文在怪物分支刻意用 trance 叙述；当前“恍惚状态加深”是否必须替成技术标签，现有术语作用域不足以裁定。机制证据充分，语义取舍待独立复审；不能仅凭 enum 自动改。

**结论：证据不足。**

延期责任：独立 translation-reviewer；重入条件：区分技术状态名与英文叙述的明确语义证据及维护者认可。当前译文保留，不自动加入 reject 或提出批量替换。

#### D06 · daze / non-Dazed

精确键 `%s is mesmerised by %s!`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:33565`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:33565`。

```text
English: %s is mesmerised by %s!
中文: %1$s被%2$s迷住了！
```

当前调用链/机制证据：`crawl-ref/source/mon-cast.cc:6086`、`crawl-ref/source/mon-cast.cc:6045`。

独立语义与旧决定适用性：_mesmerise_los 首次对怪物施加 ENCH_DAZED 时发 mesmerised 消息；玩家同施法走 add_beholder。当前“迷住了”忠实叙述英文，但是否造成玩家与怪物状态混淆需复审；不以词根或状态 enum 单独决定。

**结论：证据不足。**

延期责任：独立 translation-reviewer；重入条件：区分技术状态名与英文叙述的明确语义证据及维护者认可。当前译文保留，不自动加入 reject 或提出批量替换。

#### D07 · daze / non-Dazed

精确键 `%s is briefly mesmerised by your gaze.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:1498`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:1498`。

```text
English: %s is briefly mesmerised by your gaze.
中文: %s被你的凝视短暂迷住了。
```

当前调用链/机制证据：`crawl-ref/source/transform.cc:2677`。

独立语义与旧决定适用性：vampire_mesmerism_check 的此消息在 Will 抵抗成功的 else 分支，只扣 speed_increment 10；失败分支才 mon.daze。该消息既不设置 DUR_MESMERISED，也不设置 ENCH_DAZED。“短暂迷住”应按叙述处理，技术眩晕规则不适用。

**结论：保留（有证据）。**

#### D08 · daze / non-Dazed

冻结选择器：`['Your maw sometimes becomes mesmerised by tasty morsels.']`；本线无精确中文条目（P08 stable 是主动去重空槽）。

```text
参考检索键（不是本线中文）: Your maw sometimes becomes mesmerised by tasty morsels.
```

当前调用链/机制证据：`crawl-ref/source/dat/forms/maw.yaml:13`、`crawl-ref/source/transform.cc:2630`、`crawl-ref/source/mutation.cc:695`、`crawl-ref/source/mutation.cc:699`、`crawl-ref/source/mutation.cc:713`。

独立语义与旧决定适用性：maw.yaml badmut 经 Form 负面假突变描述进入 T_；maw_hunger_check 对可食目标调用 you.add_beholder(...,true,6..10)。这是实际玩家迷魂，绝非仅因拟人比喻即可排除机制。trunk“被美味的食物迷住”成立；stable 有英文及机制但无本中文键，为独立覆盖缺口。

**结论：不适用。**

生命周期/处理：本线不存在该中文槽、已有另一接口，或当前生产不再读取该旧键；不据此更改资产。若恢复消费者，重新验证。

#### D09 · daze / non-Dazed

精确键 `You are mesmerised.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:8467`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:8467`。

```text
English: You are mesmerised.
中文: 你陷入了迷魂状态。
```

当前调用链/机制证据：`crawl-ref/source/status.cc:398`。

独立语义与旧决定适用性：STATUS_BEHELD 由 you.beheld() 产生完整状态说明，当前“迷魂”符合 beholder 机制，Dazed 规则不适用。

**结论：保留（有证据）。**

#### D10 · daze / non-Dazed

精确键 `Mesmerise spell`；资产 `crawl-ref/source/dat/descript/zh/spells.txt:851`；英文依据 `crawl-ref/source/dat/descript/spells.txt:1327`。

```text
English: 
Attempts to entrance all enemies in sight. Adventurers who fail to resist will
become unable to move away from the caster, while other creatures will become
dazed outright.

Leaving the caster's line of sight will end the movement-controlling effect.
中文: 
尝试迷住视野内所有敌人。未能抵抗的冒险者会无法远离施法者，
其他生物则会直接陷入眩晕。

离开施法者视野会结束控制移动的效果。
```

当前调用链/机制证据：`crawl-ref/source/mon-cast.cc:6045`。

独立语义与旧决定适用性：Mesmerise 对玩家限制远离施法者，对怪物走 _mesmerise_los 的 ENCH_DAZED。当前完整中文区分玩家迷魂与其他生物眩晕；仅在对应目标分支适用，不按标题强行同名。

**结论：保留（有证据）。**

#### D11 · daze / non-Dazed

精确键 `Enfeeble spell`；资产 `crawl-ref/source/dat/descript/zh/spells.txt:451`；英文依据 `crawl-ref/source/dat/descript/spells.txt:631`。

```text
English: 
Overwhelms an enemy with malignant energies, irresistibly weakening their melee
attacks and reducing the power of their spells. It will additionally daze and
blind any foe that fails to resist the full force of the curse - even those
without visual senses!
中文: 
用邪恶能量压倒敌人，不可抗拒地削弱其近战攻击并降低法术威力。
它还会使无法抵抗全部诅咒力量的敌人眩晕和失明，
即使目标没有视觉感官也不例外。
```

当前调用链/机制证据：`crawl-ref/source/spl-monench.cc:153`、`crawl-ref/source/spl-monench.cc:168`、`crawl-ref/source/spl-monench.cc:205`。

独立语义与旧决定适用性：Enfeeble 的怪物路径加 ENCH_DAZED/mon.daze，玩家路径 you.daze；完整描述中“眩晕”成立。本卡不重审衰弱的全部数值。

**结论：保留（有证据）。**

#### D12 · daze / non-Dazed

精确键 `Cacophony status`；资产 `crawl-ref/source/dat/descript/zh/status.txt:843`；英文依据 `crawl-ref/source/dat/descript/status.txt:1117`。

```text
English: 
You are noisily attacking with all of your armour. Every piece of armour you
haunt currently moves of its own volition; any damage it takes will not affect
you, you can freely fire through it, and its attacks may daze, drain, or confuse
your enemies.
中文: 
你正驱使所有护甲喧闹地攻击。你附身的每件护甲都会自主行动；
它们受到的任何伤害都不会影响你，你也可以自由地穿过它们射击。
它们的攻击可能使敌人眩晕、陷入衰竭，或使其陷入混乱。
```

当前调用链/机制证据：`crawl-ref/source/ability.cc:2988`、`crawl-ref/source/dat/mons/haunted-armour.yaml:8`、`crawl-ref/source/melee-attack.cc:4664`。

独立语义与旧决定适用性：Cacophony 召唤 MON_SUMM_CACOPHONY 的 haunted armour；其 trickster 攻击从效果集中选 ENCH_DAZED 后调用 defender->daze。“眩晕”成立。仅核对该术语；其他攻击效果措辞不在此结论内。

**结论：保留（有证据）。**

#### D13 · daze / non-Dazed

精确键 `burstshroom`；资产 `crawl-ref/source/dat/descript/zh/monsters.txt:3188`；英文依据 `crawl-ref/source/dat/descript/monsters.txt:932`。

```text
English: 
A rapidly-growing mushroom whose life-cycle culminates in an explosive release
of spores. These spores have a mild psychoactive effect and can sometimes daze
creatures who breathe them in.
中文: 
一种快速生长的蘑菇，其生命周期以孢子的爆发性释放为高潮。
这些孢子具有轻微的致幻效果，有时会使吸入它们的生物眩晕。
```

当前调用链/机制证据：`crawl-ref/source/mon-act.cc:1366`、`crawl-ref/source/mon-act.cc:1415`。

独立语义与旧决定适用性：_burstshroom_grow 的孢子攻击对合适目标调用 targ->daze；当前“眩晕”有机制依据，保留。

**结论：保留（有证据）。**

#### D14 · daze / non-Dazed

精确键 `dazed monstatus`；资产 `crawl-ref/source/dat/descript/zh/monstatus.txt:158`；英文依据 `crawl-ref/source/dat/descript/monstatus.txt:174`。

```text
English: 
This creature is temporarily unable to act, but any hostile action will cause it to
immediately regain its senses.
中文: 
这个生物暂时无法行动，但任何敌对行为将使其立即恢复神智。
```

当前调用链/机制证据：`crawl-ref/source/mon-info.cc:86`、`crawl-ref/source/mon-info-flag-name.h:103`、`crawl-ref/source/directn.cc:1837`、`crawl-ref/source/describe.cc:7624`、`crawl-ref/source/describe.cc:7633`。

独立语义与旧决定适用性：ENCH_DAZED 映射 MB_DAZED，旗标描述键 dazed 经 attribute/status descriptor 送入怪物说明。完整 dazed monstatus 正文描述不能行动、遇敌对行为即恢复；正文没有强塞状态名，配套短名在 D16 为眩晕。当前语义保留。

**结论：保留（有证据）。**

#### D15 · daze / non-Dazed

精确键 `You are too mesmerised to rage.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:42426`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:42426`。

```text
English: You are too mesmerised to rage.
中文: 你深受迷魂影响，无法狂暴。
```

当前调用链/机制证据：`crawl-ref/source/player-act.cc:757`。

独立语义与旧决定适用性：player-act 在 beheld 且非 demonaxe 的分支拒绝狂暴；消息描述玩家迷魂限制，不是 Dazed。当前迷魂保留。

**结论：保留（有证据）。**

#### D16 · daze / non-Dazed

精确键 `dazed`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:20371`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:20371`。

```text
English: dazed
中文: 眩晕
```

当前调用链/机制证据：`crawl-ref/source/mon-info.cc:86`、`crawl-ref/source/mon-info-flag-name.h:103`、`crawl-ref/source/mon-act.cc:2208`。

独立语义与旧决定适用性：ENCH_DAZED→MB_DAZED→dazed 状态名；mon-act 对该附魔消耗行动能量并返回。这里是实际 Dazed 的短名，眩晕成立。

**结论：保留（有证据）。**

#### D17 · daze / non-Dazed

精确键 `Siren Song spell`；资产 `crawl-ref/source/dat/descript/zh/spells.txt:1140`；英文依据 `crawl-ref/source/dat/descript/spells.txt:1896`。

```text
English: 
Sings a haunting song that mesmerises nearby listeners. Adventurers who fail to
resist will become unable to move away from the singer, while other creatures
will become dazed outright.

Leaving the caster's line of sight will end the movement-controlling effect.
中文: 
唱出萦绕心头的歌，迷住附近听众。未能抵抗的冒险者会无法远离歌者，
其他生物则会直接陷入眩晕。

离开施法者视野会结束控制移动的效果。
```

当前调用链/机制证据：`crawl-ref/source/mon-cast.cc:6045`。

独立语义与旧决定适用性：Siren Song 使用同一 _mesmerise_los：玩家 add_beholder，怪物 ENCH_DAZED。完整描述分别写无法远离及眩晕；分目标成立，不能全篇只用一种状态名。

**结论：保留（有证据）。**

#### D18 · daze / non-Dazed

精确键 `Avatar Song spell`；资产 `crawl-ref/source/dat/descript/zh/spells.txt:71`；英文依据 `crawl-ref/source/dat/descript/spells.txt:76`。

```text
English: 
Sings a powerfully haunting song. Adventurers who fail to resist will become
unable to move away from the singer (and will sometimes be drawn closer
involuntarily), while other creatures will become dazed outright.

In addition, it may call forth drowned souls from any nearby bodies of deep
water.

Leaving the caster's line of sight will end the movement-controlling effect.
中文: 
唱出一首极具魔力、萦绕心头的歌。未能抵抗的冒险者会无法远离歌者
（有时还会不由自主地被拉近），其他生物则会直接陷入眩晕。

此外，它可能从附近的任何深水中召来溺魂。

离开施法者视野会结束控制移动的效果。
```

当前调用链/机制证据：`crawl-ref/source/mon-cast.cc:6045`。

独立语义与旧决定适用性：Avatar Song 的控制路径同 D17，并另有溺亡之魂效果；此卡只审迷魂/眩晕两种目标机制。中文对应成立，不据此声称其他段落全审通过。

**结论：保留（有证据）。**

#### F01 · noxious fumes

精确键 `noxious fumes`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:17995`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:17995`。

```text
English: noxious fumes
中文: 毒烟
```

当前调用链/机制证据：`crawl-ref/source/cloud.cc:100`、`crawl-ref/source/cloud.cc:880`、`crawl-ref/source/cloud.cc:977`、`crawl-ref/source/cloud.cc:1090`。

独立语义与旧决定适用性：cloud 类型表将 CLOUD_MEPHITIC 命名 noxious fumes；接触效果是混乱，受抗毒等条件影响。名称“毒烟”成立，不能与 CLOUD_POISON 的“毒气”混用。

**结论：保留（有证据）。**

#### F02 · noxious fumes

精确键 `poison gas`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:17998`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:17998`。

```text
English: poison gas
中文: 毒气
```

当前调用链/机制证据：`crawl-ref/source/cloud.cc:113`、`crawl-ref/source/cloud.cc:979`、`crawl-ref/source/cloud.cc:1146`。

独立语义与旧决定适用性：CLOUD_POISON 的 poison gas 会施加中毒伤害；“毒气”成立，和 F01 类型不同。

**结论：保留（有证据）。**

#### F03 · noxious fumes

精确键 `noxious fumes cloud`；资产 `crawl-ref/source/dat/descript/zh/clouds.txt:11`；英文依据 `crawl-ref/source/dat/descript/clouds.txt:12`。

```text
English: 
A cloud of vile, choking fumes. Any creature spending time in it will be at
risk of becoming confused by the gases, unless resistant to poison. Tougher,
more experienced creatures are less likely to be affected.
中文: 
一团呛人又有毒的云。
任何生物身处其中，除非具有毒抗，否则都有陷入混乱的危险。
越坚韧、经验等级越高的生物不太会受此影响。
```

当前调用链/机制证据：`crawl-ref/source/describe.cc:3245`、`crawl-ref/source/cloud.cc:880`、`crawl-ref/source/cloud.cc:977`、`crawl-ref/source/cloud.cc:1090`。

独立语义与旧决定适用性：get_cloud_desc 用英文云名加 cloud 查询长描述；正文的 vile/choking fumes 是性质泛称，并说明混乱及抗毒。当前“呛人又有毒的云”不要求每处重复云专名“毒烟”，适用范围缩小为名称槽。

**结论：保留（有证据）。**

#### F04 · noxious fumes

精确键 `poison gas cloud`；资产 `crawl-ref/source/dat/descript/zh/clouds.txt:23`；英文依据 `crawl-ref/source/dat/descript/clouds.txt:26`。

```text
English: 
A cloud of deadly poison. Any creature without resistance to poison will be
both poisoned and directly harmed by time spent in it.
中文: 
一团有着致命毒性的云。任何没有毒抗的生物，在里面就会中毒并直接受到伤害。
```

当前调用链/机制证据：`crawl-ref/source/describe.cc:3245`、`crawl-ref/source/cloud.cc:979`、`crawl-ref/source/cloud.cc:1146`。

独立语义与旧决定适用性：poison gas cloud 描述中毒和毒伤；属于 CLOUD_POISON，不机械套 noxious fumes 的云名术语。当前语义保留。

**结论：保留（有证据）。**

#### F05 · noxious fumes

精确键 `Mephitic Cloud spell`；资产 `crawl-ref/source/dat/descript/zh/spells.txt:845`；英文依据 `crawl-ref/source/dat/descript/spells.txt:1321`。

```text
English: 
Conjures a fragile flask that explodes into short-lived clouds of noxious fumes.
These clouds may cause confusion in any creature not resistant to poison.
Tougher, more experienced creatures are less likely to be affected.
中文: 
召出一个脆弱的瓶子，瓶子爆炸后形成短暂存在的毒烟云。
这些云可能使任何没有毒抗的生物陷入混乱。
越坚韧、经验越丰富的生物越不容易受影响。
```

当前调用链/机制证据：`crawl-ref/source/beam.cc:2497`、`crawl-ref/source/beam.cc:6862`、`crawl-ref/source/cloud.cc:880`、`crawl-ref/source/cloud.cc:977`、`crawl-ref/source/cloud.cc:1090`。

独立语义与旧决定适用性：Mephitic Cloud 产生 CLOUD_MEPHITIC，完整施法描述中的 noxious fumes 是这个实际云类型，毒烟成立。

**结论：保留（有证据）。**

#### F06 · noxious fumes

精确键 `Noxious Cloud spell`；资产 `crawl-ref/source/dat/descript/zh/spells.txt:916`；英文依据 `crawl-ref/source/dat/descript/spells.txt:1423`。

```text
English: 
Creates a large cloud of noxious fumes, which may cause confusion.
中文: 
产生一大片毒烟云，可能引起混乱。
```

当前调用链/机制证据：`crawl-ref/source/beam.cc:2448`、`crawl-ref/source/spl-data.h:1366`。

独立语义与旧决定适用性：bolt::get_cloud_type 对 SPELL_NOXIOUS_CLOUD 明确返回 CLOUD_MEPHITIC；不是由法术名猜测。当前毒烟成立。

**结论：保留（有证据）。**

#### F07 · noxious fumes

精确键 `tutorial4 aiming_clouds`；资产 `crawl-ref/source/dat/descript/zh/tutorial.txt:499`；英文依据 `crawl-ref/source/dat/descript/tutorial.txt:550`。

```text
English: 
Mephitic Cloud covers an area in noxious fumes when cast, and you'll be able to
see the area it affects as you target it. Try to catch multiple enemies in a
single cloud in order to be more efficient with your magic.
中文: 
施放迷瘴云时，毒烟会覆盖一片区域；瞄准时，你会看到它影响的范围。
设法将多个敌人笼罩在同一片云中，以更有效地利用你的魔法。
```

当前调用链/机制证据：`crawl-ref/source/dat/des/tutorial/lesson4.des:54`。

独立语义与旧决定适用性：教学 lesson4 的 aiming_clouds marker 读取同名教学说明；文本说明 Mephitic Cloud 的瞄准与混乱云。当前“毒烟”与云类型成立，教学其他操作指令不在此卡重审范围。

**结论：保留（有证据）。**

#### P01 · piety

精确键 `A donation of $%d equates to an increase of piety by %d.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:2509`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:2509`。

```text
English: A donation of $%d equates to an increase of piety by %d.
中文: 捐赠$%d相当于增加%d点虔诚值。
```

当前调用链/机制证据：`crawl-ref/source/god-abil.cc:289`。

独立语义与旧决定适用性：数字捐赠换取 piety 资源；译作“虔诚值”有机制依据。适用：资源义成立，不推广到信仰叙述。

**结论：保留（有证据）。**

#### P02 · piety

精确键 `You feel less pious.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:9628`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:9628`。

```text
English: You feel less pious.
中文: 你感到自己的虔诚值降低了。
```

当前调用链/机制证据：`crawl-ref/source/player-equip.cc:2506`。

独立语义与旧决定适用性：卸除信仰护符（trunk 另有 FORGEWARDEN）计算 raw_piety/3 后调用 lose_piety；这里不是单纯情绪描写。“虔诚值降低”成立。

**结论：保留（有证据）。**

#### P03 · piety

冻结选择器：`['To the devout, Zin provideth. From the rest...']`；本线无精确中文条目（P08 stable 是主动去重空槽）。

```text
参考检索键（不是本线中文）: To the devout, Zin provideth. From the rest...
```

当前调用链/机制证据：`crawl-ref/source/god-abil.cc:379`、`crawl-ref/source/god-abil.cc:636`。

独立语义与旧决定适用性：辛诵经诗句描写神供养虔信者，不是资源增减；trunk 经 T_ 翻译后替换经文槽。适用：叙述义缩小为虔信者，不加“值”。stable 的 book_of_zin 文本直接组装，当前无此中文键，见缺失说明。

**结论：不适用。**

生命周期/处理：本线不存在该中文槽、已有另一接口，或当前生产不再读取该旧键；不据此更改资产。若恢复消费者，重新验证。

#### P04 · piety

精确键 `Pious`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:14261`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:14261`。

```text
English: Pious
中文: 虔诚者
```

当前调用链/机制证据：`crawl-ref/source/describe-god.cc:140`、`crawl-ref/source/describe-god.cc:252`、`crawl-ref/source/describe-god.cc:287`、`crawl-ref/source/describe-god.cc:301`。

独立语义与旧决定适用性：god_title 按 _piety_level 选称号，再由 _render_god_title 调 C_("god title",key)；两线无 god title|Pious 专键，回退普通 Pious。称号称人为“虔诚者”，不是把资源命名为人。适用：称号例外，保留。

**结论：保留（有证据）。**

#### P05 · piety

精确键 `Reached `；资产 `crawl-ref/source/dat/i18n/zh/source.txt:35234`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:35234`。

```text
English: Reached 
中文: 达到了
```

精确键 ` piety under `；资产 `crawl-ref/source/dat/i18n/zh/source.txt:35276`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:35276`。

```text
English:  piety under 
中文: 虔诚等级，信仰
```

当前调用链/机制证据：`crawl-ref/source/notes.cc:178`、`crawl-ref/source/notes.cc:733`。

独立语义与旧决定适用性：NOTE_PIETY_RANK 记录星级门槛。trunk 为完整语境键并重排占位符；stable 用 Reached + 星号 + piety under + 神名拼接。这里是“虔诚等级”，不是数值资源单位；两线需分别按实际接口判断。

**结论：保留（有证据）。**

#### P06 · piety

精确键 `It occasionally summons a dragon when using Invocations with hostile monsters in sight. Chance is 10% + twice the piety cost of the ability used.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:29502`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:29502`。

```text
English: It occasionally summons a dragon when using Invocations with hostile monsters in sight. Chance is 10% + twice the piety cost of the ability used.
中文: 视野内有敌对怪物时使用祈神能力，偶尔会召唤一条龙。触发几率为10% + 所使用能力的虔诚值消耗的两倍。
```

当前调用链/机制证据：`crawl-ref/source/art-data.txt:995`。

独立语义与旧决定适用性：stable 的 Invocations 版本仍在 art-data；trunk 生产描述已改 divine abilities，旧 Invocations 只余 Source 兼容条目及直接查询测试。piety cost 是资源花费；保留中文，不把旧键当现行生产缺陷。

**结论：保留（有证据）。**

#### P07 · piety

冻结选择器：`['It occasionally summons a dragon when using divine abilities with hostile monsters in sight. Chance is 10% + twice the piety cost of the ability used.']`；本线无精确中文条目（P08 stable 是主动去重空槽）。

```text
参考检索键（不是本线中文）: It occasionally summons a dragon when using divine abilities with hostile monsters in sight. Chance is 10% + twice the piety cost of the ability used.
```

当前调用链/机制证据：`crawl-ref/source/art-data.txt:995`。

独立语义与旧决定适用性：trunk art-data 当前描述 divine abilities，概率取决于技能所花 piety，故“虔诚值消耗”成立。stable 生产版本是 P06，无本键；不向另一版本补造条目。

**结论：不适用。**

生命周期/处理：本线不存在该中文槽、已有另一接口，或当前生产不再读取该旧键；不据此更改资产。若恢复消费者，重新验证。

#### P08 · piety

冻结选择器：`[]`；本线无精确中文条目（P08 stable 是主动去重空槽）。

```text
参考检索键（不是本线中文）:  piety under 
```

当前调用链/机制证据：`crawl-ref/source/notes.cc:178`、`crawl-ref/source/notes.cc:733`。

独立语义与旧决定适用性：trunk 旧 piety under 片段已被 P05 整句替代，旧“虔诚度”属于非生产死键。stable 活跃的同片段已作为 P05 复合身份核对；此槽为空以免重复。旧快照/死键不按资源规则批改。

**结论：不适用。**

生命周期/处理：本线不存在该中文槽、已有另一接口，或当前生产不再读取该旧键；不据此更改资产。若恢复消费者，重新验证。

#### T01 · travel exclusion

精确键 `This transporter is marked as excluded!`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:7638`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:7638`。

```text
English: This transporter is marked as excluded!
中文: 这个传送器设有禁区标记！
```

当前调用链/机制证据：`crawl-ref/source/main.cc:1542`。

独立语义与旧决定适用性：main 的传送器检查排除标记并询问用户；标记限制自动寻路而非绝对禁止使用。中文“禁区标记”成立。

**结论：保留（有证据）。**

#### T02 · travel exclusion

精确键 `This %s%s is marked as excluded! Open it anyway?`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:40899`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:40899`。

```text
English: This %s%s is marked as excluded! Open it anyway?
中文: 这个%s%s设有禁区标记！仍要打开它吗？
```

当前调用链/机制证据：`crawl-ref/source/player.cc:9106`。

独立语义与旧决定适用性：player 的开门确认检查 excluded 标记后仍允许用户确认打开；“禁区标记”不应改成不能手动进入的物理禁制。当前保留。

**结论：保留（有证据）。**

#### T03 · travel exclusion

精确键 `\nTo avoid accidentally opening a door you'd rather remain closed during travel or autoexplore, you can mark it with an exclusion from the map view (<w>X</w>) with <w>ee</w> while your cursor is on the grid in question. Such an exclusion will prevent autotravel from ever entering that grid until you remove the exclusion with another press of <w>Xe</w>.`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:40830`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:40830`。

```text
English: \nTo avoid accidentally opening a door you'd rather remain closed during travel or autoexplore, you can mark it with an exclusion from the map view (<w>X</w>) with <w>ee</w> while your cursor is on the grid in question. Such an exclusion will prevent autotravel from ever entering that grid until you remove the exclusion with another press of <w>Xe</w>.
中文: \n为避免在旅行或自动探索时意外打开你希望保持关闭的门，你可以在光标位于该格时，从地图视图（<w>X</w>）中按<w>ee</w>将其标记为旅行禁区。此禁区标记会阻止自动旅行进入该格，直到你再次按<w>Xe</w>将其移除。
```

当前调用链/机制证据：`crawl-ref/source/hints.cc:2582`。

独立语义与旧决定适用性：stable hints 仍以整段 T_ 解释地图标记如何阻止 autotravel；trunk 已改为 HINT_DESCRIBE_CLOSED_DOOR，旧整段 Source 不再由该生产路径读取。stable 禁区译文成立，trunk 旧键只记录生命周期。

**结论：保留（有证据）。**

#### T04 · travel exclusion

冻结选择器：`['HINT_DESCRIBE_CLOSED_DOOR']`；本线无精确中文条目（P08 stable 是主动去重空槽）。

```text
参考检索键（不是本线中文）: HINT_DESCRIBE_CLOSED_DOOR
```

当前调用链/机制证据：`crawl-ref/source/hints.cc:2582`。

独立语义与旧决定适用性：trunk hints 的 _get_hint("HINT_DESCRIBE_CLOSED_DOOR") 读取当前长说明；stable 没有这个新接口。其禁区影响自动旅行、不剥夺手动开门能力，trunk 当前译文成立。

**结论：不适用。**

生命周期/处理：本线不存在该中文槽、已有另一接口，或当前生产不再读取该旧键；不据此更改资产。若恢复消费者，重新验证。

#### T05 · travel exclusion

精确键 `%d %sexclusion%s`；资产 `crawl-ref/source/dat/i18n/zh/source.txt:34766`；英文依据 `crawl-ref/source/dat/i18n/zh/source.txt:34766`。

```text
English: %d %sexclusion%s
中文: %d个%s禁区%s
```

当前调用链/机制证据：`crawl-ref/source/exclude.cc:750`、`crawl-ref/source/exclude.cc:824`、`crawl-ref/source/dgn-overview.cc:1115`、`crawl-ref/source/dgn-overview.cc:1117`。

独立语义与旧决定适用性：旧复数字串没有当前生产调用者；exclude_set::get_exclusion_desc 已用独立单复数键，dgn-overview 传 display=true，持久化注记路径默认 false 保持英文。trunk 无旧条目，stable 旧译仍存；均不把兼容旧键或存档字段当现行 UI 修正。

**结论：不适用。**

生命周期/处理：本线不存在该中文槽、已有另一接口，或当前生产不再读取该旧键；不据此更改资产。若恢复消费者，重新验证。

## 覆盖与只读检查

冻结/已审身份集合双向相等，无重复：92 / 92。分类计数：保留（有证据） 76；需要更正 0；证据不足 4；不适用 12。

原始清单列出的全部输入 SHA-256 已逐一复核未变。补充调用链文件摘要另存 `anchoring-B-evidence-supplement.json`，不覆盖原冻结清单。阶段 B 为只读审查，未自动构建或跑翻译 profile。阶段 A 的检查另见交付报告。
