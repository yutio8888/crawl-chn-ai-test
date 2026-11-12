# 第四轮覆盖与样本冻结

固定refs：{"stable": "ae5a420e78579a9433f4ffb127b7a9062a7d948c", "trunk": "59aec6256f1824d8c5cd7de92b7c25691132cce9"}

本轮是首批70项有边界抽检清单，不代表七类已审完。只做候选总体、抽样和源文本还原，不评价译文。

## 前轮覆盖矩阵

|前轮证据|规模／范围|本轮处理|
|---|---|---|
|R1 samples_with_identity|48项、6层小样本|排除key、英文正文及归一模板|
|D-C-096 inventory|46个spec探针|排除探针身份及PR修复键|
|R2 samples + selection log|80项、C1–C8|排除键和模板；C5-09宗教状态提示不作为新增|
|R3 index|72消息族 + 76 HERE定向|排除全部模板/catalog key；含function身份的已覆盖源族整体不计|
|PR #299–#316|18个merge的一父中文资产差分|解析修改／删除键；同样排除|

归档证据Git提交和SHA-256：
```json
[
  {
    "label": "r1",
    "path": "docs/archive/translation-ab-review-2026-11-12/samples_with_identity.json",
    "commit": "59aec6256f1824d8c5cd7de92b7c25691132cce9",
    "sha256": "264318e1a4cfc14e08765493ea463c6f1ea1491a244b8e9d05fc097165d79378"
  },
  {
    "label": "dc096",
    "path": "docs/archive/dc096-anchoring-review-2026-11-12/anchoring-B-inventory.json",
    "commit": "ae5a420e78579a9433f4ffb127b7a9062a7d948c",
    "sha256": "2c8871d82e2196502d6bb8edff5da549013e17988f87dbe5080daa3e1b7ad645"
  },
  {
    "label": "r2",
    "path": "docs/archive/translation-sample-review-r2-2026-11-12/samples_r2.json",
    "commit": "59aec6256f1824d8c5cd7de92b7c25691132cce9",
    "sha256": "8580f27c56bcbbfaabb9af517b296857e708c1ea8fa994a99d79e3c6cf041e9a"
  },
  {
    "label": "r2log",
    "path": "docs/archive/translation-sample-review-r2-2026-11-12/selection_log_r2.json",
    "commit": "59aec6256f1824d8c5cd7de92b7c25691132cce9",
    "sha256": "f3d352fdf169821e1f3c2041443ae9f78a4bd9a5330cc697e2993c0b4e2ca897"
  },
  {
    "label": "r3",
    "path": "docs/archive/player-action-review-r3-2026-11-12/families_r3_index.json",
    "commit": "59aec6256f1824d8c5cd7de92b7c25691132cce9",
    "sha256": "10ba9bfbdf1b13a848338f168ef5027b773d4160a7f5b255d2d7e354628b9fb8"
  }
]
```

## 本轮类别及候选总体

|类别|候选总体|高风险候选|静态候选|抽中高风险+静态|子种子|备用|
|---|---:|---:|---:|---:|---:|---:|
|R4-1 物品／神器长说明与物品属性行|292|46|246|5+5|2026111214|5|
|R4-2 法术正文与效果反馈|577|229|348|5+5|2026111215|5|
|R4-3 怪物正文与施法反馈|682|85|597|5+5|2026111216|5|
|R4-4 神祇交互与神祇正文|224|100|124|5+5|2026111217|5|
|R4-5 教程／帮助长段|75|36|39|5+5|2026111218|5|
|R4-6 环境及vault宣告|103|8|95|5+5|2026111219|5|
|R4-7 怪物动作及状态动态反馈|107|102|5|6+4|2026111220|5|

R4-1：R1仅抽样物品名/短说明，R2主要操作，R3为动作反馈；完整items/unrand及物品属性行仍有未覆盖单位。

R4-2：R1法术/技能层是小样本，R2技能及能力正文不等同spell正文，R3偏施法入口；保留未重叠的spell正文和效果调用。

R4-3：R1怪物名/短说明稀疏，R2怪物言语根key不等同monster正文，R3偏玩家动作；补怪物完整正文和mon-cast输出。

R4-4：既有神祇检查及探针/修复键全部排除，不把它们算新单位；正文powers/wrath/extra和其他剩余交互仍形成独立候选。C5-09宗教状态提示及归一同源模板不纳入。

R4-5：R2 C1/C5主要直接界面提示片段；R3未按整个HintsDB正文枚举。保留有具体事件/教程调用的完整未覆盖段落。

R4-6：R3移动/HERE覆盖部分楼层/位置反馈，不等同云、深渊和mainline vault公告；补实际crawl.mpr输出，排除用户自动战斗脚本与Sprint评分，并将stairs整体留给既有移动轮次而不再次计为新增。

R4-7：R3为玩家动作与反馈；剩余monster enchantment/行动事件/能力状态有独立动态模板。动态多、完整静态对照少，采用6+4配额。

种子=2026111213，各类Random(seed+类别序号)；候选按英文key（casefold）及完整正文排序，分高风险/静态子池分别shuffle。先高风险正选、备用，再静态正选、备用；一般5+5正选、3+2备用。R4-6备用2+3；R4-7因静态总体少，正选6+4、备用4+1。备用按记录顺序使用。作废0、补抽0；范围验证发生于最终抽样前，未按中文质量选择。

高风险定义：格式参数/隐式怪物前缀、相邻条件调用组；长段正文长度至少650或含机制数字/半数/倍数/等级/回合/伤害/概率等英文信号。高风险长正文不因此虚构运行时变量；它可属于静态正文。静态对照是不含这些风险信号的候选，并非声称没有游戏条件。

## 纳入、排除与孤立候选

TextDB按英文lookup key配对完整中英文，并提供具体数据name/枚举/字面量生成证据和生产lookup。items限能从item-name/item-prop具体字面量证明的键；unrand匹配art-data NAME；spell匹配spl-data标题；monster匹配dat/mons name；god匹配canonical god name及后缀；hint匹配具体事件键和getHintString路径。纯别名正文不独立计数。

动态单元是同函数中调用间隔不超过8行的输出组，保留模板、片段、所有提取到的相邻条件和实参。同key或同完整英文正文全局只计一次。R4-1只取物品相关描述函数；其他C++动态候选要求真实mpr/yesno/simple_monster_message入口，不把内部make_stringf当显示消费者。环境Lua仅取mainline .des中的crawl.mpr，排除Sprint/教程/自动战斗用户脚本。

排除调试/巫师、错误诊断、内部键、既有key与归一模板；归一将格式位置/类型占位视为同一参数位置文本，防止仅更换占位符形式成为新增。含既有source path+function身份的已覆盖调用族整体排除；排除项及回归对照详见selection_log。

未取得具体生产生成器证据或为别名正文的候选数：404。单独逐项列于selection_log.unproven_or_isolated；这是未证明的排除集合，不把“没有在本抽样框中找到证据”一概断言为死键。

## 还原和两线适用性

样本级还原方式（只要含一个待运行分支，该样本计入待运行）：{"静态模板，无参数": 41, "需要运行时或布局才能确定": 22, "参数文本还原": 7}

stable模板/正文分支级统计：{"静态模板，无参数": 46, "需要运行时或布局才能确定": 24, "参数文本还原": 10}

两线适用性：{"相同": 63, "分化": 6, "只在 stable": 1}

没有执行游戏或新增渲染断言，因此“已有测试覆盖”计0。参数文本还原保留实际catalog名称及源码表达式；不自行补冠词、量词、所有格或标点。具体状态可达性、命令绑定、Lua占位和窗口折行仍需运行时/布局验证。

## 仍未查区域

此候选总体不等于仓库全部可见文本：未穷尽生成式物品DBNAME、TextDB所有别名链、所有spell文件、动态Lua/长括号文本、完全变量化输出与全部跨函数拼接。未测试角色/神祇/变形/可见性条件的全部组合；TextDB本体之外的运行时追加属性与语言分支保留调用证据但不声称已还原所有值。mon-cast lambda/table的近邻组可能仍需评审结合完整源文件细分；未开展游戏机制正确性评价。

## 回归对照（不计新增）
- R4-2 "Avatar Song spell"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 4934}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 5471}]}
- R4-2 "Blinkbolt spell"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 4934}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 5471}]}
- R4-2 "Cleansing Flame spell"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 4934}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 5471}]}
- R4-2 "Enfeeble spell"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 4934}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 5471}]}
- R4-2 "March of Sorrows spell"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 4934}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 5471}]}
- R4-2 "Mephitic Cloud spell"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 4934}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 5471}]}
- R4-2 "Mesmerise spell"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 4934}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 5471}]}
- R4-2 "Noxious Cloud spell"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 4934}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 5471}]}
- R4-2 "Siren Song spell"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 4934}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 5471}]}
- R4-2 "Splinterfrost Shell spell"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 4934}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 5471}]}
- R4-3 "Aizul"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "bound soul"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "brain worm"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "burstshroom"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "colossal amoeba"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "Crazy Yiuf"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "crystal echidna"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "crystal guardian"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "djinni"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "Dowan"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "Edmund"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "Eustachio"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "formicid"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "ghost"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "iron imp"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "lost soul"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "neqoxec"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "occultist"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "Polyphemus"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "raven"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "shadow imp"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "shapeshifter"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "Snorg"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "vampire mosquito"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "vine stalker"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-3 "white imp"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 7279}, {"path": "crawl-ref/source/describe.cc", "line": 7270}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 7967}, {"path": "crawl-ref/source/describe.cc", "line": 7958}]}
- R4-4 "Qazlal"：{"stable": [{"path": "crawl-ref/source/describe-god.cc", "line": 1103}], "trunk": [{"path": "crawl-ref/source/describe-god.cc", "line": 1111}]}
- R4-5 "HINT_SEEN_ARMOUR"：{"stable": [{"path": "crawl-ref/source/hints.cc", "line": 1139}, {"path": "crawl-ref/source/hints.cc", "line": 401}, {"path": "crawl-ref/source/hints.cc", "line": 483}, {"path": "crawl-ref/source/hints.cc", "line": 2884}], "trunk": [{"path": "crawl-ref/source/hints.cc", "line": 1062}, {"path": "crawl-ref/source/hints.cc", "line": 402}, {"path": "crawl-ref/source/hints.cc", "line": 484}, {"path": "crawl-ref/source/hints.cc", "line": 2386}]}
- R4-1 "\nYour spell failure would worsen by up to %d%% (press '!' for details)."：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 2106}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 2231}]}
- R4-1 "If you %s this item, your spell failure would %s:\n"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 2167}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 2371}]}
- R4-1 "%s"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 4478}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 4799}, {"path": "crawl-ref/source/describe.cc", "line": 4826}]}
- R4-1 "%s"：{"stable": [{"path": "crawl-ref/source/describe.cc", "line": 4505}], "trunk": [{"path": "crawl-ref/source/describe.cc", "line": 4799}, {"path": "crawl-ref/source/describe.cc", "line": 4826}]}
- R4-2 "%1$s %2$s blasted with magical radiation%3$s"：{"stable": [{"path": "crawl-ref/source/spl-damage.cc", "line": 2075}], "trunk": [{"path": "crawl-ref/source/spl-damage.cc", "line": 2105}]}
- R4-2 "%s"：{"stable": [{"path": "crawl-ref/source/spl-damage.cc", "line": 3464}], "trunk": [{"path": "crawl-ref/source/spl-damage.cc", "line": 3465}]}
- R4-2 "You can't see anything there. Cast anyway?"：{"stable": [{"path": "crawl-ref/source/spl-damage.cc", "line": 3708}], "trunk": [{"path": "crawl-ref/source/spl-damage.cc", "line": 3703}]}
- R4-2 "You can't see anything to vaporise!"：{"stable": [{"path": "crawl-ref/source/spl-damage.cc", "line": 4682}], "trunk": [{"path": "crawl-ref/source/spl-damage.cc", "line": 4655}]}
- R4-2 "Your magical reserves are too exhausted to conjure more reagents."：{"stable": [{"path": "crawl-ref/source/spl-damage.cc", "line": 5124}, {"path": "crawl-ref/source/spl-damage.cc", "line": 5132}], "trunk": [{"path": "crawl-ref/source/spl-damage.cc", "line": 5120}, {"path": "crawl-ref/source/spl-damage.cc", "line": 5128}]}
- R4-2 "%s"：{"stable": [{"path": "crawl-ref/source/spl-damage.cc", "line": 5266}, {"path": "crawl-ref/source/spl-damage.cc", "line": 5271}], "trunk": [{"path": "crawl-ref/source/spl-damage.cc", "line": 5257}, {"path": "crawl-ref/source/spl-damage.cc", "line": 5262}]}
- R4-2 "Your familiar is too far away to imbue with magic."：{"stable": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 246}], "trunk": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 248}]}
- R4-2 " is already dancing."：{"stable": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 892}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 897}], "trunk": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 826}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 831}]}
- R4-2 "A forested plane collides here with a resounding crunch!"：{"stable": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 1546}], "trunk": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 1482}]}
- R4-2 "Something you can't see blocks your briars from growing!"：{"stable": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 2698}], "trunk": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 2783}]}
- R4-2 "That space is already occupied."：{"stable": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 2790}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 2797}], "trunk": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 2875}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 2882}]}
- R4-2 "That space is already occupied."：{"stable": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 2837}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 2844}], "trunk": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 2922}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 2929}]}
- R4-2 "%s summons some %s!"：{"stable": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 2993}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 2997}], "trunk": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 3078}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 3082}]}
- R4-2 "Flames leap up around you!"：{"stable": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 3024}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 3029}], "trunk": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 3109}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 3114}]}
- R4-2 "%s sends a boulder rolling forward!"：{"stable": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 3191}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 3195}], "trunk": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 3274}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 3278}]}
- R4-2 "%s sculpts two cannons from ice!"：{"stable": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 3341}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 3345}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 3352}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 3356}], "trunk": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 3404}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 3408}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 3415}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 3419}]}
- R4-2 "With a metallic buzz, %s clockwork bee launches itself at %s."：{"stable": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 3667}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 3677}], "trunk": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 3745}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 3755}]}
- R4-2 "You lack sufficient magical power to recharge your bee."：{"stable": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 3775}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 3782}], "trunk": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 3842}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 3849}]}
- R4-2 "%s constructs an explosive harbinger and releases it."：{"stable": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 4458}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 4462}], "trunk": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 4549}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 4553}]}
- R4-2 "%s orders the %s explosives to detonate!"：{"stable": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 4535}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 4540}], "trunk": [{"path": "crawl-ref/source/spl-summoning.cc", "line": 4621}, {"path": "crawl-ref/source/spl-summoning.cc", "line": 4626}]}
- R4-2 "There's already a cloud here!"：{"stable": [{"path": "crawl-ref/source/spl-clouds.cc", "line": 63}], "trunk": [{"path": "crawl-ref/source/spl-clouds.cc", "line": 69}]}
- R4-2 "You can't draw power from your own body while in death's door."：{"stable": [{"path": "crawl-ref/source/spl-other.cc", "line": 37}, {"path": "crawl-ref/source/spl-other.cc", "line": 39}, {"path": "crawl-ref/source/spl-other.cc", "line": 41}], "trunk": [{"path": "crawl-ref/source/spl-other.cc", "line": 39}, {"path": "crawl-ref/source/spl-other.cc", "line": 41}, {"path": "crawl-ref/source/spl-other.cc", "line": 43}, {"path": "crawl-ref/source/spl-other.cc", "line": 65}, {"path": "crawl-ref/source/spl-other.cc", "line": 67}]}
- R4-2 "You draw magical energy from your own body!"：{"stable": [{"path": "crawl-ref/source/spl-other.cc", "line": 63}, {"path": "crawl-ref/source/spl-other.cc", "line": 65}], "trunk": [{"path": "crawl-ref/source/spl-other.cc", "line": 39}, {"path": "crawl-ref/source/spl-other.cc", "line": 41}, {"path": "crawl-ref/source/spl-other.cc", "line": 43}, {"path": "crawl-ref/source/spl-other.cc", "line": 65}, {"path": "crawl-ref/source/spl-other.cc", "line": 67}]}
- R4-2 "You attempt to intoxicate your foes!"：{"stable": [{"path": "crawl-ref/source/spl-other.cc", "line": 470}, {"path": "crawl-ref/source/spl-other.cc", "line": 478}], "trunk": [{"path": "crawl-ref/source/spl-other.cc", "line": 489}, {"path": "crawl-ref/source/spl-other.cc", "line": 497}]}
- R4-2 "You slip past the binding sigil."：{"stable": [{"path": "crawl-ref/source/spl-other.cc", "line": 590}, {"path": "crawl-ref/source/spl-other.cc", "line": 593}, {"path": "crawl-ref/source/spl-other.cc", "line": 601}], "trunk": [{"path": "crawl-ref/source/spl-other.cc", "line": 609}, {"path": "crawl-ref/source/spl-other.cc", "line": 612}, {"path": "crawl-ref/source/spl-other.cc", "line": 620}]}
- R4-2 "Your spike launcher falls apart as you grow too distant to maintain it."：{"stable": [{"path": "crawl-ref/source/spl-other.cc", "line": 736}], "trunk": []}
- R4-2 "...but somehow remain%1$s in the same place."：{"stable": [{"path": "crawl-ref/source/spl-transloc.cc", "line": 803}], "trunk": [{"path": "crawl-ref/source/spl-transloc.cc", "line": 831}]}
- R4-2 "You can't see anything to attack."：{"stable": [{"path": "crawl-ref/source/spl-transloc.cc", "line": 1461}, {"path": "crawl-ref/source/spl-transloc.cc", "line": 1463}], "trunk": [{"path": "crawl-ref/source/spl-transloc.cc", "line": 1515}, {"path": "crawl-ref/source/spl-transloc.cc", "line": 1517}]}
- R4-2 "Not with that terrain in the way!"：{"stable": [{"path": "crawl-ref/source/spl-transloc.cc", "line": 1632}, {"path": "crawl-ref/source/spl-transloc.cc", "line": 1640}], "trunk": [{"path": "crawl-ref/source/spl-transloc.cc", "line": 1660}, {"path": "crawl-ref/source/spl-transloc.cc", "line": 1703}]}
- R4-3 "Mutagenic energy flows into you."：{"stable": [{"path": "crawl-ref/source/mon-cast.cc", "line": 530}], "trunk": [{"path": "crawl-ref/source/mon-cast.cc", "line": 607}]}
- R4-3 "%s %s go into a battle-frenzy!"：{"stable": [{"path": "crawl-ref/source/mon-cast.cc", "line": 2955}, {"path": "crawl-ref/source/mon-cast.cc", "line": 2960}], "trunk": []}
- R4-3 "%1$s %2$s frozen%3$s"：{"stable": [{"path": "crawl-ref/source/mon-cast.cc", "line": 5862}], "trunk": [{"path": "crawl-ref/source/mon-cast.cc", "line": 5996}]}
- R4-3 "%s trance deepens."：{"stable": [{"path": "crawl-ref/source/mon-cast.cc", "line": 6084}, {"path": "crawl-ref/source/mon-cast.cc", "line": 6086}], "trunk": [{"path": "crawl-ref/source/mon-cast.cc", "line": 6287}, {"path": "crawl-ref/source/mon-cast.cc", "line": 6289}]}
- R4-3 "%s"：{"stable": [{"path": "crawl-ref/source/mon-cast.cc", "line": 6564}], "trunk": [{"path": "crawl-ref/source/mon-cast.cc", "line": 6765}]}
- R4-3 "%s"：{"stable": [{"path": "crawl-ref/source/mon-cast.cc", "line": 6795}], "trunk": [{"path": "crawl-ref/source/mon-cast.cc", "line": 6996}]}
- R4-3 "%s arms its allies with %s."：{"stable": [{"path": "crawl-ref/source/mon-cast.cc", "line": 7223}], "trunk": [{"path": "crawl-ref/source/mon-cast.cc", "line": 7423}]}
- R4-4 "You lose track of time!"：{"stable": [{"path": "crawl-ref/source/god-wrath.cc", "line": 444}, {"path": "crawl-ref/source/god-wrath.cc", "line": 450}], "trunk": [{"path": "crawl-ref/source/god-wrath.cc", "line": 416}, {"path": "crawl-ref/source/god-wrath.cc", "line": 422}]}
- R4-4 "Your doom draws closer."：{"stable": [{"path": "crawl-ref/source/god-wrath.cc", "line": 737}], "trunk": [{"path": "crawl-ref/source/god-wrath.cc", "line": 706}]}
- R4-4 "The monsters"：{"stable": [{"path": "crawl-ref/source/god-wrath.cc", "line": 1739}], "trunk": [{"path": "crawl-ref/source/god-wrath.cc", "line": 1697}]}
- R4-4 " is dazed by your recitation."：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 1096}], "trunk": [{"path": "crawl-ref/source/god-abil.cc", "line": 1089}]}
- R4-4 "%s"：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 1547}], "trunk": [{"path": "crawl-ref/source/god-abil.cc", "line": 1638}]}
- R4-4 "%s"：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 2335}], "trunk": [{"path": "crawl-ref/source/god-abil.cc", "line": 2514}]}
- R4-4 "%s"：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 2512}], "trunk": [{"path": "crawl-ref/source/god-abil.cc", "line": 2692}]}
- R4-4 "Are you sure you wish to flee a divine trial? This will place you under penance!"：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 2802}, {"path": "crawl-ref/source/god-abil.cc", "line": 2805}, {"path": "crawl-ref/source/god-abil.cc", "line": 2812}], "trunk": [{"path": "crawl-ref/source/god-abil.cc", "line": 2982}, {"path": "crawl-ref/source/god-abil.cc", "line": 2985}, {"path": "crawl-ref/source/god-abil.cc", "line": 2992}]}
- R4-4 "Your orcish features manifest fully."：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 2830}, {"path": "crawl-ref/source/god-abil.cc", "line": 2837}], "trunk": [{"path": "crawl-ref/source/god-abil.cc", "line": 3010}, {"path": "crawl-ref/source/god-abil.cc", "line": 3017}]}
- R4-4 "%s"：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 4091}], "trunk": [{"path": "crawl-ref/source/god-abil.cc", "line": 4274}]}
- R4-4 "You can't see any clouds you can empower."：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 4165}], "trunk": [{"path": "crawl-ref/source/god-abil.cc", "line": 4350}]}
- R4-4 "There isn't enough space here!"：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 4248}, {"path": "crawl-ref/source/god-abil.cc", "line": 4253}, {"path": "crawl-ref/source/god-abil.cc", "line": 4262}], "trunk": [{"path": "crawl-ref/source/god-abil.cc", "line": 4430}, {"path": "crawl-ref/source/god-abil.cc", "line": 4435}, {"path": "crawl-ref/source/god-abil.cc", "line": 4444}]}
- R4-4 "You are too terrified to leap around!"：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 5480}], "trunk": [{"path": "crawl-ref/source/god-abil.cc", "line": 5644}]}
- R4-4 "Something unexpectedly blocks you, preventing you from leaping!"：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 5576}], "trunk": [{"path": "crawl-ref/source/god-abil.cc", "line": 5740}]}
- R4-4 "You cannot move away from %s!"：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 5826}, {"path": "crawl-ref/source/god-abil.cc", "line": 5834}, {"path": "crawl-ref/source/god-abil.cc", "line": 5842}, {"path": "crawl-ref/source/god-abil.cc", "line": 5849}, {"path": "crawl-ref/source/god-abil.cc", "line": 5855}, {"path": "crawl-ref/source/god-abil.cc", "line": 5861}], "trunk": [{"path": "crawl-ref/source/god-abil.cc", "line": 5985}, {"path": "crawl-ref/source/god-abil.cc", "line": 5993}, {"path": "crawl-ref/source/god-abil.cc", "line": 6001}, {"path": "crawl-ref/source/god-abil.cc", "line": 6008}, {"path": "crawl-ref/source/god-abil.cc", "line": 6014}, {"path": "crawl-ref/source/god-abil.cc", "line": 6020}]}
- R4-4 "Something unexpectedly blocks you, preventing you from passing!"：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 5886}], "trunk": [{"path": "crawl-ref/source/god-abil.cc", "line": 6045}]}
- R4-4 "You can't see anything there. Try transferring anyway?"：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 6196}, {"path": "crawl-ref/source/god-abil.cc", "line": 6205}], "trunk": []}
- R4-4 "%s cannot be transferred there."：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 6226}], "trunk": []}
- R4-4 "There is nothing to wall jump against here."：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 6495}, {"path": "crawl-ref/source/god-abil.cc", "line": 6501}, {"path": "crawl-ref/source/god-abil.cc", "line": 6507}], "trunk": [{"path": "crawl-ref/source/god-abil.cc", "line": 6552}, {"path": "crawl-ref/source/god-abil.cc", "line": 6558}, {"path": "crawl-ref/source/god-abil.cc", "line": 6564}]}
- R4-4 "%s"：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 6662}], "trunk": [{"path": "crawl-ref/source/god-abil.cc", "line": 6719}]}
- R4-4 "You are already unleashing the legions of chaos!"：{"stable": [{"path": "crawl-ref/source/god-abil.cc", "line": 7169}, {"path": "crawl-ref/source/god-abil.cc", "line": 7177}], "trunk": [{"path": "crawl-ref/source/god-abil.cc", "line": 7227}, {"path": "crawl-ref/source/god-abil.cc", "line": 7235}]}
- R4-4 "%s"：{"stable": [{"path": "crawl-ref/source/religion.cc", "line": 2315}], "trunk": [{"path": "crawl-ref/source/religion.cc", "line": 2339}]}
- R4-4 "Your funded stores close, unable to pay their debts without your funds."：{"stable": [{"path": "crawl-ref/source/religion.cc", "line": 3138}], "trunk": [{"path": "crawl-ref/source/religion.cc", "line": 3152}, {"path": "crawl-ref/source/religion.cc", "line": 3157}]}
- R4-4 "%s"：{"stable": [{"path": "crawl-ref/source/god-prayer.cc", "line": 68}], "trunk": [{"path": "crawl-ref/source/god-prayer.cc", "line": 71}]}
- R4-6 "%1$s %2$s in the rain."：{"stable": [{"path": "crawl-ref/source/cloud.cc", "line": 1772}, {"path": "crawl-ref/source/cloud.cc", "line": 1779}, {"path": "crawl-ref/source/cloud.cc", "line": 1786}], "trunk": [{"path": "crawl-ref/source/cloud.cc", "line": 1956}, {"path": "crawl-ref/source/cloud.cc", "line": 1963}, {"path": "crawl-ref/source/cloud.cc", "line": 1970}]}
- R4-6 "%s"：{"stable": [{"path": "crawl-ref/source/cloud.cc", "line": 1956}], "trunk": [{"path": "crawl-ref/source/cloud.cc", "line": 2133}]}
- R4-6 "%s"：{"stable": [{"path": "crawl-ref/source/abyss.cc", "line": 413}], "trunk": [{"path": "crawl-ref/source/abyss.cc", "line": 422}]}
- R4-6 "%s"：{"stable": [{"path": "crawl-ref/source/abyss.cc", "line": 451}, {"path": "crawl-ref/source/abyss.cc", "line": 453}, {"path": "crawl-ref/source/abyss.cc", "line": 455}], "trunk": [{"path": "crawl-ref/source/abyss.cc", "line": 458}, {"path": "crawl-ref/source/abyss.cc", "line": 460}, {"path": "crawl-ref/source/abyss.cc", "line": 462}]}
- R4-6 "%s"：{"stable": [{"path": "crawl-ref/source/abyss.cc", "line": 1776}], "trunk": [{"path": "crawl-ref/source/abyss.cc", "line": 1775}]}
- R4-6 "%s"：{"stable": [{"path": "crawl-ref/source/abyss.cc", "line": 2410}], "trunk": [{"path": "crawl-ref/source/abyss.cc", "line": 2398}]}
- R4-6 "%s"：{"stable": [{"path": "crawl-ref/source/timed-effects.cc", "line": 87}], "trunk": [{"path": "crawl-ref/source/timed-effects.cc", "line": 90}]}
- R4-6 "%s"：{"stable": [{"path": "crawl-ref/source/timed-effects.cc", "line": 140}], "trunk": [{"path": "crawl-ref/source/timed-effects.cc", "line": 140}]}
- R4-6 "%s"：{"stable": [{"path": "crawl-ref/source/timed-effects.cc", "line": 205}], "trunk": [{"path": "crawl-ref/source/timed-effects.cc", "line": 205}]}
- R4-6 "The walls disappear%s!"：{"stable": [{"path": "crawl-ref/source/timed-effects.cc", "line": 714}, {"path": "crawl-ref/source/timed-effects.cc", "line": 719}, {"path": "crawl-ref/source/timed-effects.cc", "line": 724}, {"path": "crawl-ref/source/timed-effects.cc", "line": 729}, {"path": "crawl-ref/source/timed-effects.cc", "line": 731}], "trunk": [{"path": "crawl-ref/source/timed-effects.cc", "line": 726}, {"path": "crawl-ref/source/timed-effects.cc", "line": 731}, {"path": "crawl-ref/source/timed-effects.cc", "line": 736}, {"path": "crawl-ref/source/timed-effects.cc", "line": 741}, {"path": "crawl-ref/source/timed-effects.cc", "line": 743}]}
- R4-6 "%s"：{"stable": [{"path": "crawl-ref/source/timed-effects.cc", "line": 875}, {"path": "crawl-ref/source/timed-effects.cc", "line": 877}], "trunk": [{"path": "crawl-ref/source/timed-effects.cc", "line": 90}, {"path": "crawl-ref/source/timed-effects.cc", "line": 140}, {"path": "crawl-ref/source/timed-effects.cc", "line": 205}, {"path": "crawl-ref/source/timed-effects.cc", "line": 726}, {"path": "crawl-ref/source/timed-effects.cc", "line": 731}, {"path": "crawl-ref/source/timed-effects.cc", "line": 736}, {"path": "crawl-ref/source/timed-effects.cc", "line": 741}, {"path": "crawl-ref/source/timed-effects.cc", "line": 743}, {"path": "crawl-ref/source/timed-effects.cc", "line": 901}, {"path": "crawl-ref/source/timed-effects.cc", "line": 1007}, {"path": "crawl-ref/source/timed-effects.cc", "line": 1009}, {"path": "crawl-ref/source/timed-effects.cc", "line": 1012}, {"path": "crawl-ref/source/timed-effects.cc", "line": 1014}]}
- R4-6 "%s"：{"stable": [{"path": "crawl-ref/source/timed-effects.cc", "line": 894}], "trunk": [{"path": "crawl-ref/source/timed-effects.cc", "line": 901}]}
- R4-6 "The runic seals fade away."：{"stable": [{"path": "crawl-ref/source/timed-effects.cc", "line": 979}, {"path": "crawl-ref/source/timed-effects.cc", "line": 981}, {"path": "crawl-ref/source/timed-effects.cc", "line": 984}, {"path": "crawl-ref/source/timed-effects.cc", "line": 986}], "trunk": [{"path": "crawl-ref/source/timed-effects.cc", "line": 1007}, {"path": "crawl-ref/source/timed-effects.cc", "line": 1009}, {"path": "crawl-ref/source/timed-effects.cc", "line": 1012}, {"path": "crawl-ref/source/timed-effects.cc", "line": 1014}]}
- R4-6 "%s"：{"stable": [{"path": "crawl-ref/source/orb.cc", "line": 66}, {"path": "crawl-ref/source/orb.cc", "line": 68}, {"path": "crawl-ref/source/orb.cc", "line": 73}, {"path": "crawl-ref/source/orb.cc", "line": 75}], "trunk": [{"path": "crawl-ref/source/orb.cc", "line": 66}, {"path": "crawl-ref/source/orb.cc", "line": 68}, {"path": "crawl-ref/source/orb.cc", "line": 73}, {"path": "crawl-ref/source/orb.cc", "line": 75}]}
- R4-6 "%s"：{"stable": [{"path": "crawl-ref/source/orb.cc", "line": 94}, {"path": "crawl-ref/source/orb.cc", "line": 99}], "trunk": [{"path": "crawl-ref/source/orb.cc", "line": 94}, {"path": "crawl-ref/source/orb.cc", "line": 99}]}
- R4-6 "The mighty Pandemonium lord %s resides here."：{"stable": [{"path": "crawl-ref/source/dat/des/branches/pan.des", "line": 37}], "trunk": [{"path": "crawl-ref/source/dat/des/branches/pan.des", "line": 37}]}
- R4-6 "The demonic rune of Zot may be found here."：{"stable": [{"path": "crawl-ref/source/dat/des/branches/pan.des", "line": 285}], "trunk": [{"path": "crawl-ref/source/dat/des/branches/pan.des", "line": 285}]}
- R4-6 "A powerful Pandemonium lord resides here."：{"stable": [{"path": "crawl-ref/source/dat/des/branches/pan.des", "line": 287}], "trunk": [{"path": "crawl-ref/source/dat/des/branches/pan.des", "line": 287}, {"path": "crawl-ref/source/dat/des/branches/pan.des", "line": 2669}]}
- R4-6 "A powerful Pandemonium lord resides here."：{"stable": [{"path": "crawl-ref/source/dat/des/branches/pan.des", "line": 2669}], "trunk": [{"path": "crawl-ref/source/dat/des/branches/pan.des", "line": 287}, {"path": "crawl-ref/source/dat/des/branches/pan.des", "line": 2669}]}
- R4-6 "<yellow>A demonic rune of Zot can be found here... for a price.</yellow>"：{"stable": [{"path": "crawl-ref/source/dat/des/branches/pan.des", "line": 2670}], "trunk": [{"path": "crawl-ref/source/dat/des/branches/pan.des", "line": 2670}]}
- R4-6 "Here, spectral monks perform complicated, martial routines; they fade quickly."：{"stable": [{"path": "crawl-ref/source/dat/des/portals/wizlab.des", "line": 363}], "trunk": [{"path": "crawl-ref/source/dat/des/portals/wizlab.des", "line": 363}]}
- R4-7 " is stunned by your conviction and fails to attack."：{"stable": [{"path": "crawl-ref/source/mon-act.cc", "line": 184}], "trunk": [{"path": "crawl-ref/source/mon-act.cc", "line": 202}]}
- R4-7 " is dazed by the spores."：{"stable": [{"path": "crawl-ref/source/mon-act.cc", "line": 1416}], "trunk": [{"path": "crawl-ref/source/mon-act.cc", "line": 1439}, {"path": "crawl-ref/source/mon-act.cc", "line": 1441}]}
- R4-7 " is stunned by your conviction and fails to attack."：{"stable": [{"path": "crawl-ref/source/mon-act.cc", "line": 1602}, {"path": "crawl-ref/source/mon-act.cc", "line": 1609}], "trunk": [{"path": "crawl-ref/source/mon-act.cc", "line": 1683}, {"path": "crawl-ref/source/mon-act.cc", "line": 1690}]}
- R4-7 "Something you can't see is thrashing in a web."：{"stable": [{"path": "crawl-ref/source/mon-act.cc", "line": 2459}, {"path": "crawl-ref/source/mon-act.cc", "line": 2461}, {"path": "crawl-ref/source/mon-act.cc", "line": 2467}], "trunk": [{"path": "crawl-ref/source/mon-act.cc", "line": 2539}, {"path": "crawl-ref/source/mon-act.cc", "line": 2541}, {"path": "crawl-ref/source/mon-act.cc", "line": 2547}]}
- R4-7 "%s"：{"stable": [{"path": "crawl-ref/source/mon-act.cc", "line": 2923}, {"path": "crawl-ref/source/mon-act.cc", "line": 2925}], "trunk": [{"path": "crawl-ref/source/mon-act.cc", "line": 3001}, {"path": "crawl-ref/source/mon-act.cc", "line": 3003}]}
- R4-7 "%s"：{"stable": [{"path": "crawl-ref/source/mon-act.cc", "line": 3554}, {"path": "crawl-ref/source/mon-act.cc", "line": 3556}], "trunk": [{"path": "crawl-ref/source/mon-act.cc", "line": 3666}, {"path": "crawl-ref/source/mon-act.cc", "line": 3668}]}
- R4-7 "You lose your grip on %s soul."：{"stable": [{"path": "crawl-ref/source/mon-ench.cc", "line": 744}], "trunk": [{"path": "crawl-ref/source/mon-ench.cc", "line": 764}]}
- R4-7 "Two slime creatures merge to form %s."：{"stable": [{"path": "crawl-ref/source/mon-abil.cc", "line": 383}, {"path": "crawl-ref/source/mon-abil.cc", "line": 389}, {"path": "crawl-ref/source/mon-abil.cc", "line": 398}], "trunk": [{"path": "crawl-ref/source/mon-abil.cc", "line": 388}, {"path": "crawl-ref/source/mon-abil.cc", "line": 394}, {"path": "crawl-ref/source/mon-abil.cc", "line": 408}]}
- R4-7 "%s writhes in pain as voices assail %s mind."：{"stable": [{"path": "crawl-ref/source/mon-abil.cc", "line": 711}, {"path": "crawl-ref/source/mon-abil.cc", "line": 719}], "trunk": [{"path": "crawl-ref/source/mon-abil.cc", "line": 733}]}
- R4-7 "%s"：{"stable": [{"path": "crawl-ref/source/spl-monench.cc", "line": 246}], "trunk": [{"path": "crawl-ref/source/spl-monench.cc", "line": 246}]}
- R4-7 "%s"：{"stable": [{"path": "crawl-ref/source/spl-monench.cc", "line": 388}, {"path": "crawl-ref/source/spl-monench.cc", "line": 394}], "trunk": [{"path": "crawl-ref/source/spl-monench.cc", "line": 384}, {"path": "crawl-ref/source/spl-monench.cc", "line": 390}]}

其他同源调用排除与全量修复键见selection_log_r4.json。

重跑：`python3 scripts/build_inventory_r4.py --repo <仓库> --out <产出目录>`。输入归档来自固定Git对象并冻结inputs；源文件只通过git archive/show读取。两份lane分别以1401/2502对70项独立乱序。
