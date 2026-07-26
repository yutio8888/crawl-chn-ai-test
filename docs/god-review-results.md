# Issue #25 神祇翻译全量复审结果

## 冻结边界

- 基线提交：`7b0224b32c0bd4b7b79119776762ee623857adc9`
- 术语表 SHA-256：`91f0638a60e633d450ded2b6e7efdd3449e7ad2e0e27e710a52cd0dd2565d645`
- 终态 inventory SHA-256：`2985c819290cbffc213152d41cee8db7faa5a14bdd196c90cf76a7b4375c9575`
- 父身份：27（现役 26，兼容禁用 1）
- TextDB 身份：描述 82、长名 23、godspeak 193
- 子身份：能力 89、被动 78、行为 30、愤怒神祇引用 28
- 神祇称号槽：224（28 行，含 `GOD_NO_GOD`，每行 8 槽）
- 终态 godspeak topology drift：0
- 终态 ZH-only ability：6
- 结构 violations：0。重复、父身份缺失/多余、英文名或显示名缺失、
  中英文描述/长名/godspeak key 集不一致、非法长名 key、称号行列数错误、
  子身份行数错误、未知子身份 token、死亡消息误用显示名等字段均为空。

冻结命令：

```bash
python3 .claude/scripts/audit_god_inventory.py \
  --output /tmp/issue25-god-inventory-terminal.json
```

## 一对一父身份终态

计数缩写：`A`=能力、`P`=被动、`L`=喜好行为、`D`=厌恶行为、
`T`=称号槽、`Desc`=描述 key、`Speak`=godspeak key。括号内列出代表性
实现身份；完整集合以终态 inventory 为准。

| 父身份 | 生命周期 | 英→中短名/长名 | 子身份与资产证据 | 唯一终态结论 |
|---|---|---|---|---|
| `GOD_ZIN` | 现役 | Zin→辛；长名 Zin the Law-Giver→定法者辛 | A5(`ABIL_ZIN_DONATE_GOLD`,`ABIL_ZIN_IMPRISON`…); P6(`cleanse_mut_potions`,`protect_from_harm`…); L2/D9; T8(Blasphemer→亵渎者); Desc3; Speak2; wrath=`zin wrath` | 修订：能力名与祈神技能术语统一。 |
| `GOD_SHINING_ONE` | 现役 | the Shining One→光辉者；长名 fallback 短名 | A4(`ABIL_TSO_BLESS_WEAPON`,`ABIL_TSO_CLEANSING_FLAME`…); P6(`abjuration_protection_hd`,`bless_followers_vs_evil`…); L4/D5; T8(Honourless→无耻之徒); Desc3; Speak2; wrath=`the shining one wrath` | 修订：光辉者名、德瓦实体术语、能力与欢迎语统一。 |
| `GOD_KIKUBAAQUDGHA` | 现役 | Kikubaaqudgha→奇库巴库哈；长名 fallback 短名 | A4(`ABIL_KIKU_BLESS_WEAPON`,`ABIL_KIKU_GIFT_CAPSTONE_SPELLS`…); P2(`miscast_protection_necromancy`,`resist_torment`); L5/D0; T8(Tormented→受折磨者); Desc3; Speak6; wrath=`kikubaaqudgha wrath` | 修订：神名、毁灭印记、死灵术施法失误术语、描述与欢迎语。 |
| `GOD_YREDELEMNUL` | 现役 | Yredelemnul→伊莱德莱姆努尔；长名 Yredelemnul the Fallen→堕落者伊莱德莱姆努尔 | A5(`ABIL_YRED_BIND_SOUL`,`ABIL_YRED_FATHOMLESS_SHACKLES`…); P5(`nightvision`,`r_misery`…); L3/D1; T8(Traitor→背叛者); Desc3; Speak6; wrath=`yredelemnul wrath` | 修订：神名、长名、能力与愤怒语义。 |
| `GOD_XOM` | 现役 | Xom→佐姆；长名 Xom of Chaos→混沌之主佐姆（加权条目） | A0; P0; L0/D0; T8(Toy→玩具); Desc3; Speak120; wrath=`xom wrath` | 修订：godspeak 20 项拓扑及变体同步；购物台词压至 12 个汉字并保留凡人、钱袋、小世界与安逸语义。 |
| `GOD_VEHUMET` | 现役 | Vehumet→维胡梅特；长名 fallback 短名 | A0; P3(`mp_on_kill`,`spells_range`…); L5/D0; T8(Meek→温顺者); Desc3; Speak1; wrath=`vehumet wrath` | 修订：称号缺译与地狱之火欢迎语。 |
| `GOD_OKAWARU` | 现役 | Okawaru→奥卡瓦鲁；长名 Warmaster Okawaru→战争之主奥卡瓦鲁 | A5(`ABIL_OKAWARU_DUEL`,`ABIL_OKAWARU_FINESSE`…); P1(`no_allies`); L5/D0; T8(Coward→懦夫); Desc3; Speak2; wrath=`okawaru wrath` | 修订：专属能力祈神技能术语。 |
| `GOD_MAKHLEB` | 现役 | Makhleb→马科列布；长名 Makhleb the Destroyer→毁灭者马科列布 | A6(`ABIL_MAKHLEB_BRAND_SELF_1`,`ABIL_MAKHLEB_DESTRUCTION`…); P1(`restore_hp`); L5/D0; T8(Orderly→守序者); Desc3; Speak2; wrath=`makhleb wrath` | 修订：主描述与处刑者台词拓扑。 |
| `GOD_SIF_MUNA` | 现役 | Sif Muna→西芙·穆娜；长名 Sif Muna the Loreminder→学识之主西芙·穆娜 | A3(`ABIL_SIF_MUNA_CHANNEL_ENERGY`,`ABIL_SIF_MUNA_DIVINE_EXEGESIS`…); P0; L5/D0; T8(Ignorant→无知者); Desc3; Speak2; wrath=`sif muna wrath` | 修订：主描述语义漂移。 |
| `GOD_TROG` | 现役 | Trog→特洛格；长名 Trog the Wrathful→狂怒者特洛格 | A3(`ABIL_TROG_BERSERK`,`ABIL_TROG_BROTHERS_IN_ARMS`…); P2(`abjuration_protection`,`extend_berserk`); L6/D4; T8(Puny→弱小者); Desc3; Speak2; wrath=`trog wrath` | 修订：称号与兄弟连额外陈述。 |
| `GOD_NEMELEX_XOBEH` | 现役 | Nemelex Xobeh→尼姆雷斯·索布；长名 Nemelex Xobeh the Trickster→诡术者尼姆雷斯·索布 | A3(`ABIL_NEMELEX_DEAL_FOUR`,`ABIL_NEMELEX_STACK_FIVE`…); P0; L1/D0; T8(Unlucky `@Genus@`→不幸的`@Genus@`); Desc3; Speak1; wrath=`nemelex xobeh wrath` | 修订：全名、长名、称号及描述一致性。 |
| `GOD_ELYVILON` | 现役 | Elyvilon→艾利维隆；长名 Elyvilon the Healer→治愈者艾利维隆 | A4(`ABIL_ELYVILON_DIVINE_VIGOUR`,`ABIL_ELYVILON_HEAL_OTHER`…); P2(`lifesaving`,`protect_ally`); L1/D5; T8(Sinner→罪人); Desc3; Speak2; wrath=`elyvilon wrath` | 修订：专属能力祈神技能术语，并恢复安抚成功所得的全部经验值。 |
| `GOD_LUGONU` | 现役 | Lugonu→卢格努；长名 Lugonu the Unformed→无形之神卢格努 | A5(`ABIL_LUGONU_ABYSS_ENTER`,`ABIL_LUGONU_ABYSS_EXIT`…); P4(`attract_abyssal_rune`,`map_rot_res_abyss`…); L6/D0; T8(Pure→纯净者); Desc3; Speak2; wrath=`lugonu wrath` | 修订：专属能力祈神技能术语，并恢复放逐成功所得的全部经验值。 |
| `GOD_BEOGH` | 现役 | Beogh→比欧弗；长名 Beogh the Shepherd→牧者比欧弗 | A7(`ABIL_BEOGH_BLOOD_FOR_BLOOD`,`ABIL_BEOGH_RECALL_APOSTLES`…); P2(`convert_orcs`,`water_walk`); L6/D2; T8(Apostate→叛教者); Desc3; Speak3; wrath=`beogh wrath` | 修订：祈神技能术语并删除孤立能力块。 |
| `GOD_JIYVA` | 现役 | Jiyva→吉瓦；长名 fallback 短名 | A2(`ABIL_JIYVA_OOZEMANCY`,`ABIL_JIYVA_SLIMIFY`); P8(`jellies_army`,`jelly_eating`…); L1/D0; T8(Scum→浮渣); Desc3; Speak4; wrath=`jiyva wrath` | 修订：Ooze 神祇称号上下文译法。 |
| `GOD_FEDHAS` | 现役 | Fedhas→费德哈；长名 Fedhas Madash→费德哈·莽动 | A4(`ABIL_FEDHAS_GROW_BALLISTOMYCETE`,`ABIL_FEDHAS_GROW_OKLOB`…); P3(`friendly_plants`,`pass_through_plants`…); L5/D0; T8(`@Walking@ Fertiliser`→`@Walking@肥料`); Desc3; Speak3; wrath=`fedhas wrath` | 修订：孢子炮菌与祈神技能术语。 |
| `GOD_CHEIBRIADOS` | 现役 | Cheibriados→切布理亚多；长名 Cheibriados the Contemplative→深思者切布理亚多 | A4(`ABIL_CHEIBRIADOS_DISTORTION`,`ABIL_CHEIBRIADOS_SLOUCH`…); P7(`no_haste`,`slow_abyss`…); L1/D1; T8(Hasty→急躁者); Desc3; Speak3; wrath=`cheibriados wrath` | 修订：专属能力祈神技能术语。 |
| `GOD_ASHENZARI` | 现役 | Ashenzari→艾申扎利；长名 Ashenzari the Shackled→被缚者艾申扎利 | A0（动态 curse/uncurse 身份已核）; P10(`avoid_traps`,`bondage_skill_boost`…); L1/D0; T8(Star-crossed→厄运缠身者); Desc3; Speak1; wrath=`ashenzari wrath` | 修订：长名、称号与愤怒语义。 |
| `GOD_DITHMENOS` | 现役 | Dithmenos→迪斯姆诺；长名 Dithmenos the Shrouded→隐没者迪斯姆诺 | A3(`ABIL_DITHMENOS_APHOTIC_MARIONETTE`,`ABIL_DITHMENOS_PRIMORDIAL_NIGHTFALL`…); P3(`dampen_noise`,`shadow_attacks`…); L1/D0; T8(Conspicuous→显眼者); Desc3; Speak1; wrath=`dithmenos wrath` | 修订：欢迎语语义。 |
| `GOD_GOZAG` | 现役 | Gozag→哥萨戈；长名 Gozag Ym Sagoz the Greedy→贪婪者哥萨戈·亿·赛格斯 | A3(`ABIL_GOZAG_BRIBE_BRANCH`,`ABIL_GOZAG_CALL_MERCHANT`…); P2(`gold_aura`,`goldify_corpses`); L0/D0; T8(Profligate→挥霍者); Desc3; Speak1; wrath=`gozag wrath` | 保留：术语表明确 `Gozag` 运行时短名与 `Gozag Ym Sagoz the Greedy` 神祇长名的语境分工，生产显示与中文资产一致。 |
| `GOD_QAZLAL` | 现役 | Qazlal→卡兹拉尔；长名 Qazlal Stormbringer→兴风者卡兹拉尔 | A3(`ABIL_QAZLAL_DISASTER_AREA`,`ABIL_QAZLAL_ELEMENTAL_FORCE`…); P4(`cloud_immunity`,`elemental_adaptation`…); L5/D0; T8(Unspoiled→未损者); Desc3; Speak2; wrath=`qazlal wrath` | 修订：避雷针称号、祈神技能术语与天灾免伤范围。 |
| `GOD_RU` | 现役 | Ru→入；长名 Ru the Awakened→觉醒者入 | A3(`ABIL_RU_APOCALYPSE`,`ABIL_RU_DRAW_OUT_POWER`…，动态 sacrifice 身份已核); P2(`aura_of_power`,`upgraded_aura_of_power`); L1/D0; T8(Sleeper→沉睡者); Desc3; Speak2; wrath=`ru wrath` | 保留：当前生产身份与中文资产核对一致。 |
| `GOD_PAKELLAS` | 兼容禁用 | Pakellas→帕克拉斯；长名 Pakellas the Inventive→发明者帕克拉斯 | A0; P0; L5/D0; T8(Reactionary→守旧者); Desc3; Speak3; wrath=`pakellas wrath` | 保留：兼容身份，恢复为现役时按新生产输入重审。 |
| `GOD_USKAYAW` | 现役 | Uskayaw→乌斯卡亚；长名 Uskayaw the Reveller→狂欢者乌斯卡亚 | A3(`ABIL_USKAYAW_GRAND_FINALE`,`ABIL_USKAYAW_LINE_PASS`…); P0; L1/D0; T8(Prude→假正经); Desc3; Speak4; wrath=`uskayaw wrath` | 修订：专属能力祈神技能术语。 |
| `GOD_HEPLIAKLQANA` | 现役 | Hepliaklqana→惠普利亚卡纳；长名 Hepliaklqana the Forgotten→遗忘者惠普利亚卡纳 | A4(`ABIL_HEPLIAKLQANA_IDEALISE`,`ABIL_HEPLIAKLQANA_IDENTITY`…，动态 ancestor type 已核); P2(`frail`,`transfer_drain`); L1/D0; T8(Damnatio Memoriae→记忆抹除者); Desc3; Speak2; wrath=`hepliaklqana wrath` | 修订：祈神技能术语并删除孤立能力块。 |
| `GOD_WU_JIAN` | 现役 | Wu Jian→无间；长名 the Wu Jian Council→无间门派 | A3(`ABIL_WU_JIAN_HEAVENLY_STORM`,`ABIL_WU_JIAN_SERPENTS_LASH`…); P3(`wu_jian_lunge`,`wu_jian_wall_jump`…); L5/D0; T8(Wooden Rat→木鼠); Desc4（含 `wu jian extra`）; Speak1; wrath=`wu jian wrath` | 修订：主描述语义漂移；术语表明确 `Wu Jian` 运行时短名与 `the Wu Jian Council` 实体／派别长名的语境分工。 |
| `GOD_IGNIS` | 现役 | Ignis→曳焰；长名 Ignis, the Dying Flame→曳焰，垂死之火 | A3(`ABIL_IGNIS_FIERY_ARMOUR`,`ABIL_IGNIS_FOXFIRE`…); P1(`resist_fire`); L0/D0; T8(Extinguished→已熄灭者); Desc3; Speak3; wrath=`ignis wrath` | 修订：曳焰短名、长名、描述与台词。 |

## D-A-001 至 D-A-006 复用证据

| 裁决 | 当前英文生产身份 | 采用译名 | 复用依据 |
|---|---|---|---|
| D-A-001 | `Sif Muna` | 西芙·穆娜 | `religion.cc` 英文名与 TextDB key 未改名；当前术语表仍指向同一裁决，U+00B7 保持。 |
| D-A-002 | `Trog` | 特洛格 | 英文生产身份仍为 `Trog`，没有新的音译输入或实体分裂。 |
| D-A-003 | `Kikubaaqudgha` | 奇库巴库哈 | 英文生产身份与描述、能力、godspeak key 仍使用同一拼写；弃用形式已清除。 |
| D-A-004 | `Nemelex Xobeh` | 尼姆雷斯·索布 | 英文双段名未变；所有本次触及显示值使用 U+00B7，不使用 U+30FB。 |
| D-A-005 | `Vehumet` | 维胡梅特 | 英文生产身份仍为 `Vehumet`，没有新的音译输入。 |
| D-A-006 | `the Shining One` | 光辉者 | 生产 lookup key 仍为 `the Shining One`；显示值统一为光辉者，英文 key 保持不变。 |

以上六项的实体输入、英文生产名与裁决适用条件均未变化，因此复用既有
active 裁决，不另建命名决定。

## 子身份与实现核对方法

1. 以 `god-type.h` 中 `NUM_GODS` 之前的具体 `GOD_*` 为父集合，并由
   `religion.cc` 的英文名生产器和显示 lookup key 双向核对。
2. 从 `get_all_god_powers()` 提取直接 `ABIL_*`；另核对 Ashenzari curse、
   Nemelex deck stack、Ru sacrifice、Hepliaklqana ancestor type 的动态 marker，
   终态没有未知能力 token。
3. 从 `god-passive.cc`、`god-conduct.cc`、`god-wrath.cc` 提取被动、喜好/
   厌恶行为和愤怒实现，并将 wrath key 与 82 个描述身份核对。
4. 从 `describe-god.cc` 的 `divine_title[][8]` 冻结 28×8 槽；中文上下文
   lookup 后 224 槽全部有显示值。
5. 对 EN/ZH `gods.txt`、`godname.txt`、`godspeak.txt` 做物理 key 集合、
   重复 key 和规范化检查；godspeak 逐 variant 比较权重、顺序、递归
   `@keyword@`、choice arity 与 Lua site，终态 drift 为 0。

## 本次修改的翻译 key

### `docs/glossary.md`

`Gozag`；`Gozag Ym Sagoz the Greedy`；`Wu Jian`；
`the Wu Jian Council`。

### `docs/glossary.utf8`

机械同步以上四个术语语境。

### `dat/i18n/zh/source.txt`

`Ignis`；`Kikubaaqudgha's malice focuses upon you.`；
`You hear Kikubaaqudgha cackling.`；`You invoke the name of Kikubaaqudgha!`；
`god title|Meek`；`god title|Frenzied`；`@Genus@ of Prey`；
`god title|Ooze`；`god title|Cursed`；`Lightning Rod`；`Recite`；
`Imprison`；`Vitalisation`；`Grow Ballistomycete`；
`status|sign of ruin`；`spell or ability title|Sign of Ruin`；
` powers are based on %s instead of Invocations skill.`。

### `dat/database/zh/godname.txt`

`Yredelemnul lastname`；`Ashenzari lastname`；
`Nemelex Xobeh lastname`；`Ignis lastname`。

### `dat/database/zh/godspeak.txt`

`Xom scenery generic`；`Xom good mutations`；`Xom random mutations`；
`Xom destruction`；`Xom resurrection`；`Xom repel stairs`；
`Ignis elemental wrath`；`Dithmenos welcome`；`Ignis welcome`；
`Ignis death`；`Kikubaaqudgha welcome`；`the Shining One penance`；
`the Shining One welcome`；`Vehumet welcome`；`_trout_species_rare_`；
`Makhleb executioner chatter`；`Xom bazaar trip`；`Xom fake shatter`；
`Xom feature shallow water`；`Xom feature stone arch`；`Xom flora ring`；
`Xom force lance fleet`；`Xom inventory plural`；`Xom mass charm`；
`Xom torment all`；`dance_name`；`_xom_number_`；`Xom brain drain`。

### `dat/descript/zh/gods.txt`

`Ignis`；`Makhleb`；`Nemelex Xobeh`；`Sif Muna`；`Wu Jian`；
`Fedhas powers`；`Ignis powers`；`Kikubaaqudgha powers`；
`Nemelex Xobeh powers`；`Uskayaw powers`；`Ashenzari wrath`；
`Ignis wrath`；`Kikubaaqudgha wrath`；`Nemelex Xobeh wrath`；
`Yredelemnul wrath`。

### `dat/descript/zh/ability.txt`

`Recite ability`；`Vitalisation ability`；`Imprison ability`；
`Divine Shield ability`；`Cleansing Flame ability`；
`Summon Divine Warrior ability`；`Brand Weapon With Holy Wrath ability`；
`Bind Soul ability`；`Heroism ability`；`Finesse ability`；
`Brothers in Arms ability`；`Heal Other ability`；`Heal Self ability`；
`Divine Vigour ability`；`Banish ability`；`Corrupt ability`；
`Smiting ability`；`Wall of Briars ability`；`Grow Ballistomycete ability`；
`Grow Oklob ability`；`Bend Time ability`；`Step From Time ability`；
`Upheaval ability`；`Elemental Force ability`；`Disaster Area ability`；
`Stomp ability`；`Line Pass ability`；`Grand Finale ability`；
`Idealise ability`；`Transference ability`；`Rising Flame ability`；
`Fathomless Shackles ability`；`Light the Black Torch ability`。

删除的孤立完整块：`Recall Orcish Followers ability`、
`Ancestor Life: Elementalist ability`。

### `dat/descript/zh/passives.txt`

`channel magic passive`。

## 排除项与重新进入条件

终态仍有六个 ZH-only ability key，均为角色吐息机制，不属于神祇生产身份：

- `Breathe Acid ability`
- `Breathe Dispelling Energy ability`
- `Breathe Frost ability`
- `Breathe Lightning ability`
- `Breathe Noxious Fumes ability`
- `Breathe Steam ability`

这些身份移交角色机制审计（owner：Issue #27）。仅在其能力生产身份发生变化，
或 Issue #27 的专属能力审计正式进入时重新纳入；本 Issue 不删除、不改写。

## 终态结论

父 identity 集与 27 行证据卡一一相等；所有父身份均有唯一终态结论。
神祇专属孤立 ZH 能力块已删除，剩余六项已有明确 owner 与重新进入条件。
godspeak topology drift、结构 violations 均为 0。
