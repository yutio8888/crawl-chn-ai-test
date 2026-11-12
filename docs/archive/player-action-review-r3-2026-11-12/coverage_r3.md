# 第三轮玩家动作及反馈消息族覆盖

refs：{"stable": "4af734c175cee41cfaf75142e04bf1a9aea9ee1c", "trunk": "40a7b9976ad10aade1a703e510c68ed0667d3ca5"}

本轮是有边界的首批清单，不是动作消息全审。消息族以同函数内相邻输出调用组成（调用间隔不超过8行）；保留各调用的完整模板、片段、实参及附近条件代码。相同模板不同参数值不拆样本。

每类选12族：高风险6族、常用动作静态对照6族。高频是按常用动作入口选定的源码区域代理，不是运行频率测量。高风险含格式参数或字符串拼接；每类独立 Random(seed+类别序号)，先shuffle高风险子池取6，再shuffle静态子池取6。以文件和首调用行号排序；seed=2026111203。

|类别|总体|高风险候选|静态候选|抽中|子种子|
|---|---:|---:|---:|---:|---:|
|A|62|24|38|12（6+6）|2026111204|
|B|157|124|33|12（6+6）|2026111205|
|C|71|39|32|12（6+6）|2026111206|
|D|41|8|33|12（6+6）|2026111207|
|E|47|11|36|12（6+6）|2026111208|
|F|50|14|36|12（6+6）|2026111209|

纳入：实际生产C++的mpr/mprf及变体、yesno、simple_monster_message等带直接字面量的输出；限定动作源码范围，排除测试、debug/wizard函数；item-use按函数名把读卷/喝药/魔杖分到D，其余归C。状态类delay只取休息/奔跑，player只取恢复和状态函数。

排除：前轮80项和更早48项的英文键；任一直接模板命中排除集时整族不计入新增。回归对照列表见文末及JSON。非字面量输出尚未自动追溯，未计入本候选总体。

还原计数（随机样本stable模板/片段级，同族可含多个分支）：{"参数文本还原": 23, "需要运行时输出才能确定的": 39, "静态模板，无参数": 71}

随机样本两线：{"相同": 65, "分化": 5, "只在 stable": 2}

HERE定向两线：{"只在 trunk": 13, "相同": 56, "只在 stable": 7}

具体名称/数量示例按源码：中文DESC_A和article_a不自动加“一把”；普通堆叠为数字+ASCII空格+名称。item_message达到摘要阈值时返回glyph列表，低于阈值时才返回物品名称列表；两种输出单独还原。{"quantity": "源码例：2+ASCII空格+药水名称；不把“两瓶”当成自动生成值。", "article": "DESC_A与article_a在中文省略a/an，不自动产生“一把”。", "colour": "示例句省略菜单颜色标签；源调用仍完整保留。", "assertions": "未运行游戏或自动化测试；不标记为已有自动化断言覆盖。"}

定向HERE：独立directed段，D-HERE-xx，不计入72随机消息族。穷举范围为两线生产C++、头文件消息表以及Lua/vault DSL中包含英文独立单词here的已定位字面量（宏、显示入口或有catalog配对的消息数据）；包括流式拼接片段。按用途分组、记录全部识别到的消费者。每个key含尾空格和中文尾空格计数；评审输入末尾保留独立节。

待查覆盖：HERE已额外枚举Lua/vault DSL和头文件消息表；仍未穷尽Lua长括号字符串及完全动态拼接、其他TextDB帮助/描述中的here。随机动作池未追溯Lua/地图脚本、变量化/函数返回字符串；未覆盖所有duration-data表驱动结束消息、所有canned_msg枚举和战斗动词生成器、怪物自主行为与玩家动作的全部可达性组合。局部代码证据不等于运行时每个状态可达性。句子无法从已确认参数完整确定时标为需要运行时输出，未执行游戏或构造测试。

HERE catalog中尚未找到直接消费者的键（不冒充生产消息）：{"stable": [{"key": "You feel the power of the Orb interfering with translocations here.", "text": "你感到天球的力量在此干扰着传送。", "line": 11964}, {"key": "You see here", "text": "你在这里看到", "line": 27107}, {"key": "Here's the shortest path: ", "text": "以下是最短路径：", "line": 34112}, {"key": "And here are the needed waypoints: ", "text": "以下是所需路径点：", "line": 34118}, {"key": "<cyan>Item%s here:</cyan> %s.", "text": "<cyan>这里的物品%s：</cyan>%s。", "line": 34397}, {"key": "This screen shows the spells in your spell library. From here you can memorise spells by selecting them, as well as view spell descriptions, search for them, and organize them. As a conjurer, you start with five memorisable spells, and one already memorised: Magic Dart. (To view memorised spells, you can exit this menu and select <w>I</w>.)", "text": "此界面显示你的法术库中的法术。你可以在此选择法术进行记忆，也可以查看", "line": 40740}, {"key": "\\nWhile standing here, you can %senter %s with the <w>%s</w> key; it will vanish after you do so.", "text": "\\n站在这里时，你可以按<w>%s</w>键进入%s；进入后它就会消失。", "line": 40944}, {"key": "\\nWhile standing here, you can %s %s with the <w>%s</w> key%s.", "text": "\\n站在这里时，你可以按<w>%s</w>键%s%s。", "line": 40947}, {"key": "\\nWhile standing here, you can enter %s with with the <w>%s</w> key.", "text": "\\n站在这里时，你可以按<w>%s</w>键进入%s。", "line": 40953}], "trunk": [{"key": "You feel the power of the Orb interfering with translocations here.", "text": "你感到天球的力量在此干扰着传送。", "line": 12515}, {"key": "You see here", "text": "你在这里看到", "line": 29177}, {"key": "Here's the shortest path: ", "text": "以下是最短路径：", "line": 36647}, {"key": "And here are the needed waypoints: ", "text": "以下是所需路径点：", "line": 36653}, {"key": "<cyan>Item%s here:</cyan> %s.", "text": "<cyan>这里的物品%s：</cyan>%s。", "line": 36965}, {"key": "This screen shows the spells in your spell library. From here you can memorise spells by selecting them, as well as view spell descriptions, search for them, and organize them. As a conjurer, you start with five memorisable spells, and one already memorised: Magic Dart. (To view memorised spells, you can exit this menu and select <w>I</w>.)", "text": "此界面显示你的法术库中的法术。你可以在此选择法术进行记忆，也可以查看", "line": 43608}, {"key": "\\nWhile standing here, you can %senter %s with the <w>%s</w> key; it will vanish after you do so.", "text": "\\n站在这里时，你可以按<w>%s</w>键进入%s；进入后它就会消失。", "line": 43812}, {"key": "\\nWhile standing here, you can %s %s with the <w>%s</w> key%s.", "text": "\\n站在这里时，你可以按<w>%s</w>键%s%s。", "line": 43815}, {"key": "\\nWhile standing here, you can enter %s with with the <w>%s</w> key.", "text": "\\n站在这里时，你可以按<w>%s</w>键进入%s。", "line": 43821}]}

随机范围文件：
```json
{
  "A": [
    "movement.cc",
    "stairs.cc",
    "travel.cc"
  ],
  "B": [
    "melee-attack.cc",
    "ranged-attack.cc",
    "throw.cc",
    "beam.cc"
  ],
  "C": [
    "items.cc",
    "item-use.cc",
    "player-equip.cc"
  ],
  "D": [
    "potion.cc",
    "evoke.cc",
    "item-use.cc"
  ],
  "E": [
    "spl-cast.cc",
    "ability.cc"
  ],
  "F": [
    "delay.cc",
    "player.cc",
    "player-reacts.cc"
  ]
}
```

回归对照（不计入新增）：
- A crawl-ref/source/stairs.cc:225 `climb_message`：["fly down"]
- A crawl-ref/source/stairs.cc:394 `_check_stairs`：["This shop has been abandoned, nothing of value remains."]
- A crawl-ref/source/stairs.cc:472 `_rune_effect`：["With a soft hiss, the gate opens fully!"]
- A crawl-ref/source/stairs.cc:639 `_travel_destination`：["The shaft vanishes in a puff of logic!"]
- A crawl-ref/source/stairs.cc:969 `floor_transition`：["The abyssal rune of Zot can be found at this depth."]
- B crawl-ref/source/melee-attack.cc:634 `melee_attack::do_vampire_lifesteal`：["You sink your fangs into %s and drink %s %s."]
- C crawl-ref/source/items.cc:945 `item_check`：["Items here: %s."]
- C crawl-ref/source/item-use.cc:1018 `_can_generically_use`：["You can't remove jewellery."]
- C crawl-ref/source/item-use.cc:2173 `_brand_weapon`：["%s becomes incredibly heavy!", "%s projects an invisible shield of force!"]
- C crawl-ref/source/player-equip.cc:1875 `_equip_weapon_effect`：["%s softly glows with a divine radiance!"]
- C crawl-ref/source/player-equip.cc:1976 `_equip_weapon_effect`：["You feel a baleful cunning.", "Your %s briefly %s through it before you manage to get a firm grip on it."]
- C crawl-ref/source/player-equip.cc:2233 `_equip_armour_effect`：["You feel perceptive."]
- C crawl-ref/source/player-equip.cc:2268 `_equip_armour_effect`：["It gets dark."]

重跑：`python3 scripts/build_inventory_r3.py --repo <repo> --out <output> --previous <samples_r2.json>`。固定git对象以archive/show导出；排除资料首次冻结到inputs。不修改仓库，不运行编译或游戏。
