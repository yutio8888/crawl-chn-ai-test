# 第四轮 lane2 独立审查

模型：GPT-6（Codex）；精确后缀、温度和推理参数未由运行时暴露。

Glossary SHA-256：fb814f3252f249fc230e81fa132dce6a9bb194b014d687fc1524c66827b351d7。已运行 dcss-translation-context 的 context_resolve；非盲评。

固定基线：stable ae5a420e78579a9433f4ffb127b7a9062a7d948c；trunk 59aec6256f1824d8c5cd7de92b7c25691132cce9。仅 lane2，仓库只读。

方法：按70项身份逐项记录完整英文、生产调用、参数与条件、独立语义判断，最后做术语对照。静态长段核对机制、数值、条件、Lua 与命令标签；动态项追踪名称、所有格、列表、动作与可选后缀并做文本还原。还原示例不等于已运行状态，未测试终端尺寸或像素布局。结论仅适用于本批。

关键更正：R4-3-05 输入还原漏掉 apostrophise 自带的的；R4-7-10 stable 研磨声输入还原忽略调用未 T_；R4-4-05 兜底模板不可替代其完整句分流。祈祷动作兜底可达性经完整活动数据枚举补足，未凭未知名称捏造生产输出。


## R4-5-03

1. 完整英文
```text
If retreating to another level, keep in mind that monsters may follow you if
they're standing right next to you when you start climbing or descending the
stairs. And even if you've managed to shake them off, they'll still be there
when you come back, so you might want to use a different set of stairs when you
return.
```

2–3. stable 消费者与参数证据

crawl-ref/source/hints.cc:1444
crawl-ref/source/hints.cc:401
crawl-ref/source/hints.cc:483
crawl-ref/source/hints.cc:2884
crawl-ref/source/hints.cc",

中文全文
```text
如果要撤退到另一层，请记住：当你开始上楼或下楼时，紧挨着你的怪物可能会跟过来。即使你已经甩掉了它们，它们仍会留在那里等你回来，因此返回时或许应该改走另一处楼梯。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "如果要撤退到另一层，请记住：当你开始上楼或下楼时，紧挨着你的怪物可能会跟过来。即使你已经甩掉了它们，它们仍会留在那里等你回来，因此返回时或许应该改走另一处楼梯。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/hints.cc:1367
crawl-ref/source/hints.cc:402
crawl-ref/source/hints.cc:484
crawl-ref/source/hints.cc:2386
crawl-ref/source/hints.cc",

中文全文
```text
如果要撤退到另一层，请记住：当你开始上楼或下楼时，紧挨着你的怪物可能会跟过来。即使你已经甩掉了它们，它们仍会留在那里等你回来，因此返回时或许应该改走另一处楼梯。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "如果要撤退到另一层，请记住：当你开始上楼或下楼时，紧挨着你的怪物可能会跟过来。即使你已经甩掉了它们，它们仍会留在那里等你回来，因此返回时或许应该改走另一处楼梯。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
邻接怪物随上下楼、甩掉仍在旧层、返回改走楼梯三条提示完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-7-04

1. 完整英文
```text
%s ignites a memory of %s to re-knit themselves.

%s ignites a memory of %s.
```

2–3. stable 消费者与参数证据

crawl-ref/source/mon-abil.cc:1480
crawl-ref/source/mon-abil.cc",
crawl-ref/source/mon-abil.cc",

中文全文
```text
%s点燃了关于%s的记忆，以重新拼合自身。

%s点燃了关于%s的记忆。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "%s ignites a memory of %s to re-knit themselves.",
    "zh_template": "%s点燃了关于%s的记忆，以重新拼合自身。",
    "source": {
      "path": "crawl-ref/source/mon-abil.cc",
      "line": 1480
    },
    "parameter_expressions": [
      "MSGCH_MONSTER_SPELL",
      "was_injured\n                ? T_(\"%s ignites a memory of %s to re-knit themselves.\")\n                : T_(\"%s ignites a memory of %s.\")",
      "nobody.name(DESC_THE).c_str()",
      "spells.c_str()"
    ],
    "conditions_and_generation": "1462:     // Change spells\n1463:     nobody.spells.clear();\n1464:     const auto& recollection = _recollections[memories[memories.size() - 1].get_int()];\n1465: \n1466:     vector<string> spell_names;\n1467:     for (pair<spell_type, uint8_t> spell : recollection.spells)\n1468:     {\n1469:         nobody.spells.push_back({spell.first, spell.second, MON_SPELL_WIZARD});\n1470:         spell_names.push_back(spell_title(spell.first));\n1471:     }\n1472:     nobody.spells.push_back({SPELL_PYRRHIC_RECOLLECTION, 0, MON_SPELL_NATURAL});\n1473:     nobody.props[CUSTOM_SPELLS_KEY] = true;\n1474:     memories.pop_back();\n1475: \n1476:     if (can_see)\n1477:     {\n1478:         const string spells = comma_separated_line(spell_names.begin(), spell_names.end(),\n1479:             C_(\"recollection spell list\", \" and \"), C_(\"recollection spell list\", \", \"));\n1480:         mprf(MSGCH_MONSTER_SPELL, was_injured\n1481:                 ? T_(\"%s ignites a memory of %s to re-knit themselves.\")\n1482:                 : T_(\"%s ignites a memory of %s.\"),\n1483:              nobody.name(DESC_THE).c_str(), spells.c_str());\n1484:         string speech = make_stringf(T_(\"\\\"We remember... %s...\\\"\"),\n1485:                             getSpeakString(\"nobody_recollection \" + recollection.key).c_str());\n1486:         mons_speaks_msg(&nobody, speech, MSGCH_TALK);\n1487:     }\n1488: \n1489:     // Heal and move.\n1490:     if (was_injured)\n1491:         monster_blink(&nobody, true, true);\n1492:     nobody.heal(nobody.max_hit_points);\n1493: \n1494:     // If this was a phantom mirror copy, allow it to revive, but don't wipe out\n1495:     // its summon timer at the same time, to keep it from having unlimited duration.\n1496:     mon_enchant summon_timer;\n1497:     if (nobody.has_ench(ENCH_SUMMON_TIMER))\n1498:     {\n1499:         summon_timer = nobody.get_ench(ENCH_SUMMON_TIMER);\n1500:         nobody.del_ench(ENCH_SUMMON_TIMER, true, false);\n1501:     }",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "nobody.name(DESC_THE).c_str()",
        "examples": []
      },
      {
        "expression": "spells.c_str()",
        "examples": []
      }
    ]
  },
  {
    "english": "%s ignites a memory of %s.",
    "zh_template": "%s点燃了关于%s的记忆。",
    "source": {
      "path": "crawl-ref/source/mon-abil.cc",
      "line": 1480
    },
    "parameter_expressions": [
      "MSGCH_MONSTER_SPELL",
      "was_injured\n                ? T_(\"%s ignites a memory of %s to re-knit themselves.\")\n                : T_(\"%s ignites a memory of %s.\")",
      "nobody.name(DESC_THE).c_str()",
      "spells.c_str()"
    ],
    "conditions_and_generation": "1462:     // Change spells\n1463:     nobody.spells.clear();\n1464:     const auto& recollection = _recollections[memories[memories.size() - 1].get_int()];\n1465: \n1466:     vector<string> spell_names;\n1467:     for (pair<spell_type, uint8_t> spell : recollection.spells)\n1468:     {\n1469:         nobody.spells.push_back({spell.first, spell.second, MON_SPELL_WIZARD});\n1470:         spell_names.push_back(spell_title(spell.first));\n1471:     }\n1472:     nobody.spells.push_back({SPELL_PYRRHIC_RECOLLECTION, 0, MON_SPELL_NATURAL});\n1473:     nobody.props[CUSTOM_SPELLS_KEY] = true;\n1474:     memories.pop_back();\n1475: \n1476:     if (can_see)\n1477:     {\n1478:         const string spells = comma_separated_line(spell_names.begin(), spell_names.end(),\n1479:             C_(\"recollection spell list\", \" and \"), C_(\"recollection spell list\", \", \"));\n1480:         mprf(MSGCH_MONSTER_SPELL, was_injured\n1481:                 ? T_(\"%s ignites a memory of %s to re-knit themselves.\")\n1482:                 : T_(\"%s ignites a memory of %s.\"),\n1483:              nobody.name(DESC_THE).c_str(), spells.c_str());\n1484:         string speech = make_stringf(T_(\"\\\"We remember... %s...\\\"\"),\n1485:                             getSpeakString(\"nobody_recollection \" + recollection.key).c_str());\n1486:         mons_speaks_msg(&nobody, speech, MSGCH_TALK);\n1487:     }\n1488: \n1489:     // Heal and move.\n1490:     if (was_injured)\n1491:         monster_blink(&nobody, true, true);\n1492:     nobody.heal(nobody.max_hit_points);\n1493: \n1494:     // If this was a phantom mirror copy, allow it to revive, but don't wipe out\n1495:     // its summon timer at the same time, to keep it from having unlimited duration.\n1496:     mon_enchant summon_timer;\n1497:     if (nobody.has_ench(ENCH_SUMMON_TIMER))\n1498:     {\n1499:         summon_timer = nobody.get_ench(ENCH_SUMMON_TIMER);\n1500:         nobody.del_ench(ENCH_SUMMON_TIMER, true, false);\n1501:     }",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "nobody.name(DESC_THE).c_str()",
        "examples": []
      },
      {
        "expression": "spells.c_str()",
        "examples": []
      }
    ]
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/mon-abil.cc:1438
crawl-ref/source/mon-abil.cc",
crawl-ref/source/mon-abil.cc",

中文全文
```text
%s点燃了关于%s的记忆，以重新拼合自身。

%s点燃了关于%s的记忆。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "%s ignites a memory of %s to re-knit themselves.",
    "zh_template": "%s点燃了关于%s的记忆，以重新拼合自身。",
    "source": {
      "path": "crawl-ref/source/mon-abil.cc",
      "line": 1438
    },
    "parameter_expressions": [
      "MSGCH_MONSTER_SPELL",
      "was_injured\n                ? T_(\"%s ignites a memory of %s to re-knit themselves.\")\n                : T_(\"%s ignites a memory of %s.\")",
      "nobody.name(DESC_THE).c_str()",
      "spells.c_str()"
    ],
    "conditions_and_generation": "1420:     // Change spells\n1421:     nobody.spells.clear();\n1422:     const auto& recollection = _recollections[memories[memories.size() - 1].get_int()];\n1423: \n1424:     vector<string> spell_names;\n1425:     for (pair<spell_type, uint8_t> spell : recollection.spells)\n1426:     {\n1427:         nobody.spells.push_back({spell.first, spell.second, MON_SPELL_WIZARD});\n1428:         spell_names.push_back(spell_title(spell.first));\n1429:     }\n1430:     nobody.spells.push_back({SPELL_PYRRHIC_RECOLLECTION, 0, MON_SPELL_NATURAL});\n1431:     nobody.props[CUSTOM_SPELLS_KEY] = true;\n1432:     memories.pop_back();\n1433: \n1434:     if (can_see)\n1435:     {\n1436:         const string spells = comma_separated_line(spell_names.begin(), spell_names.end(),\n1437:             C_(\"recollection spell list\", \" and \"), C_(\"recollection spell list\", \", \"));\n1438:         mprf(MSGCH_MONSTER_SPELL, was_injured\n1439:                 ? T_(\"%s ignites a memory of %s to re-knit themselves.\")\n1440:                 : T_(\"%s ignites a memory of %s.\"),\n1441:              nobody.name(DESC_THE).c_str(), spells.c_str());\n1442:         string speech = make_stringf(T_(\"\\\"We remember... %s...\\\"\"),\n1443:                             getSpeakString(\"nobody_recollection \" + recollection.key).c_str());\n1444:         mons_speaks_msg(&nobody, speech, MSGCH_TALK);\n1445:     }\n1446: \n1447:     nobody.heal(nobody.max_hit_points);\n1448: \n1449:     // If this was a phantom mirror copy, allow it to revive, but don't wipe out\n1450:     // its summon timer at the same time, to keep it from having unlimited duration.\n1451:     mon_enchant summon_timer;\n1452:     if (nobody.has_ench(ENCH_SUMMON_TIMER))\n1453:     {\n1454:         summon_timer = nobody.get_ench(ENCH_SUMMON_TIMER);\n1455:         nobody.del_ench(ENCH_SUMMON_TIMER, true, false);\n1456:     }\n1457:     // Also, manually delete the previous enkindle without effect, in case\n1458:     // Nobody's taken a big enough hit to go from healthy to dead in one action,\n1459:     // or we'll immediately wipe out the spells we just gave them.",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "nobody.name(DESC_THE).c_str()",
        "examples": []
      },
      {
        "expression": "spells.c_str()",
        "examples": []
      }
    ]
  },
  {
    "english": "%s ignites a memory of %s.",
    "zh_template": "%s点燃了关于%s的记忆。",
    "source": {
      "path": "crawl-ref/source/mon-abil.cc",
      "line": 1438
    },
    "parameter_expressions": [
      "MSGCH_MONSTER_SPELL",
      "was_injured\n                ? T_(\"%s ignites a memory of %s to re-knit themselves.\")\n                : T_(\"%s ignites a memory of %s.\")",
      "nobody.name(DESC_THE).c_str()",
      "spells.c_str()"
    ],
    "conditions_and_generation": "1420:     // Change spells\n1421:     nobody.spells.clear();\n1422:     const auto& recollection = _recollections[memories[memories.size() - 1].get_int()];\n1423: \n1424:     vector<string> spell_names;\n1425:     for (pair<spell_type, uint8_t> spell : recollection.spells)\n1426:     {\n1427:         nobody.spells.push_back({spell.first, spell.second, MON_SPELL_WIZARD});\n1428:         spell_names.push_back(spell_title(spell.first));\n1429:     }\n1430:     nobody.spells.push_back({SPELL_PYRRHIC_RECOLLECTION, 0, MON_SPELL_NATURAL});\n1431:     nobody.props[CUSTOM_SPELLS_KEY] = true;\n1432:     memories.pop_back();\n1433: \n1434:     if (can_see)\n1435:     {\n1436:         const string spells = comma_separated_line(spell_names.begin(), spell_names.end(),\n1437:             C_(\"recollection spell list\", \" and \"), C_(\"recollection spell list\", \", \"));\n1438:         mprf(MSGCH_MONSTER_SPELL, was_injured\n1439:                 ? T_(\"%s ignites a memory of %s to re-knit themselves.\")\n1440:                 : T_(\"%s ignites a memory of %s.\"),\n1441:              nobody.name(DESC_THE).c_str(), spells.c_str());\n1442:         string speech = make_stringf(T_(\"\\\"We remember... %s...\\\"\"),\n1443:                             getSpeakString(\"nobody_recollection \" + recollection.key).c_str());\n1444:         mons_speaks_msg(&nobody, speech, MSGCH_TALK);\n1445:     }\n1446: \n1447:     nobody.heal(nobody.max_hit_points);\n1448: \n1449:     // If this was a phantom mirror copy, allow it to revive, but don't wipe out\n1450:     // its summon timer at the same time, to keep it from having unlimited duration.\n1451:     mon_enchant summon_timer;\n1452:     if (nobody.has_ench(ENCH_SUMMON_TIMER))\n1453:     {\n1454:         summon_timer = nobody.get_ench(ENCH_SUMMON_TIMER);\n1455:         nobody.del_ench(ENCH_SUMMON_TIMER, true, false);\n1456:     }\n1457:     // Also, manually delete the previous enkindle without effect, in case\n1458:     // Nobody's taken a big enough hit to go from healthy to dead in one action,\n1459:     // or we'll immediately wipe out the spells we just gave them.",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "nobody.name(DESC_THE).c_str()",
        "examples": []
      },
      {
        "expression": "spells.c_str()",
        "examples": []
      }
    ]
  }
]
```

4. 独立语义判断与还原
nobody.name 为主体，spells 是 spell_title 列表，中文列表连接后依受伤状态分有无重新拼合自身。列表为名词短语，例某某点燃了关于灼热之光的记忆，以重新拼合自身。此例只演示句法，不声称特定施法列表状态。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-1-08

1. 完整英文
```text
A fishing spear improved with a longer shaft and a three-pronged metal head.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:2895
crawl-ref/source/describe.cc:2907
crawl-ref/source/describe.cc:3461
crawl-ref/source/describe.cc:7279
crawl-ref/source/item-prop.cc",

中文全文
```text
一把经过改进的鱼叉，有了更长的杆和三叉的金属头。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一把经过改进的鱼叉，有了更长的杆和三叉的金属头。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:3167
crawl-ref/source/describe.cc:3179
crawl-ref/source/describe.cc:3731
crawl-ref/source/describe.cc:7967
crawl-ref/source/item-prop.cc",

中文全文
```text
一把经过改进的鱼叉，有了更长的杆和三叉的金属头。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一把经过改进的鱼叉，有了更长的杆和三叉的金属头。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
鱼叉加长杆及三叉金属头完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-2-05

1. 完整英文
```text
The dungeon shakes around %s!

The dungeon rumbles around %s!
```

2–3. stable 消费者与参数证据

crawl-ref/source/spl-damage.cc:1836
crawl-ref/source/spl-damage.cc:1842
crawl-ref/source/spl-damage.cc",
crawl-ref/source/spl-damage.cc",

中文全文
```text
地牢在%s周围震动！

地牢在%s周围隆隆作响！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "The dungeon shakes around %s!",
    "zh_template": "地牢在%s周围震动！",
    "source": {
      "path": "crawl-ref/source/spl-damage.cc",
      "line": 1836
    },
    "parameter_expressions": [
      "T_(\"The dungeon shakes around %s!\")",
      "caster->name(DESC_THE).c_str()"
    ],
    "conditions_and_generation": "1818:         if (devastator)\n1819:             ouch(damage, KILLED_BY_MONSTER, wielder->mid);\n1820:         else\n1821:             ouch(damage, KILLED_BY_BEAM, wielder->mid, \"by Shatter\");\n1822:     }\n1823: \n1824:     return damage;\n1825: }\n1826: \n1827: bool mons_shatter(monster* caster, bool actual)\n1828: {\n1829:     const bool silence = silenced(caster->pos());\n1830:     int foes = 0;\n1831: \n1832:     if (actual)\n1833:     {\n1834:         if (silence)\n1835:         {\n1836:             mprf(T_(\"The dungeon shakes around %s!\"),\n1837:                  caster->name(DESC_THE).c_str());\n1838:         }\n1839:         else\n1840:         {\n1841:             noisy(spell_effect_noise(SPELL_SHATTER), caster->pos(), caster->mid);\n1842:             mprf(MSGCH_SOUND, T_(\"The dungeon rumbles around %s!\"),\n1843:                  caster->name(DESC_THE).c_str());\n1844:         }\n1845:     }\n1846: \n1847:     int pow = 5 + div_rand_round(caster->get_hit_dice() * 9, 2);\n1848: \n1849:     int dest = 0;\n1850:     for (distance_iterator di(caster->pos(), true, true, LOS_RADIUS); di; ++di)\n1851:     {\n1852:         // goes from the center out, so newly dug walls recurse\n1853:         if (!cell_see_cell(caster->pos(), *di, LOS_SOLID))\n1854:             continue;\n1855: ",
    "method": "参数文本还原",
    "full_zh_display": "地牢在兽人周围震动！",
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "caster->name(DESC_THE).c_str()",
        "examples": [
          [
            "兽人",
            "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          ]
        ]
      }
    ],
    "branch_examples": [
      {
        "parameters": [
          {
            "expression": "caster->name(DESC_THE).c_str()",
            "value": "兽人",
            "source_and_state": "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          }
        ],
        "full_zh_display": "地牢在兽人周围震动！"
      }
    ],
    "formula": "按所列原始参数表达式和catalog参数示例逐位置替换；不增加冠词、量词或修正文案。"
  },
  {
    "english": "The dungeon rumbles around %s!",
    "zh_template": "地牢在%s周围隆隆作响！",
    "source": {
      "path": "crawl-ref/source/spl-damage.cc",
      "line": 1842
    },
    "parameter_expressions": [
      "MSGCH_SOUND",
      "T_(\"The dungeon rumbles around %s!\")",
      "caster->name(DESC_THE).c_str()"
    ],
    "conditions_and_generation": "1824:     return damage;\n1825: }\n1826: \n1827: bool mons_shatter(monster* caster, bool actual)\n1828: {\n1829:     const bool silence = silenced(caster->pos());\n1830:     int foes = 0;\n1831: \n1832:     if (actual)\n1833:     {\n1834:         if (silence)\n1835:         {\n1836:             mprf(T_(\"The dungeon shakes around %s!\"),\n1837:                  caster->name(DESC_THE).c_str());\n1838:         }\n1839:         else\n1840:         {\n1841:             noisy(spell_effect_noise(SPELL_SHATTER), caster->pos(), caster->mid);\n1842:             mprf(MSGCH_SOUND, T_(\"The dungeon rumbles around %s!\"),\n1843:                  caster->name(DESC_THE).c_str());\n1844:         }\n1845:     }\n1846: \n1847:     int pow = 5 + div_rand_round(caster->get_hit_dice() * 9, 2);\n1848: \n1849:     int dest = 0;\n1850:     for (distance_iterator di(caster->pos(), true, true, LOS_RADIUS); di; ++di)\n1851:     {\n1852:         // goes from the center out, so newly dug walls recurse\n1853:         if (!cell_see_cell(caster->pos(), *di, LOS_SOLID))\n1854:             continue;\n1855: \n1856:         if (actual)\n1857:         {\n1858:             _shatter_monsters(*di, pow, caster);\n1859:             if (*di == you.pos())\n1860:                 _shatter_player(pow, caster);\n1861:             dest += _shatter_walls(*di, caster);",
    "method": "参数文本还原",
    "full_zh_display": "地牢在兽人周围隆隆作响！",
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "caster->name(DESC_THE).c_str()",
        "examples": [
          [
            "兽人",
            "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          ]
        ]
      }
    ],
    "branch_examples": [
      {
        "parameters": [
          {
            "expression": "caster->name(DESC_THE).c_str()",
            "value": "兽人",
            "source_and_state": "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          }
        ],
        "full_zh_display": "地牢在兽人周围隆隆作响！"
      }
    ],
    "formula": "按所列原始参数表达式和catalog参数示例逐位置替换；不增加冠词、量词或修正文案。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/spl-damage.cc:1845
crawl-ref/source/spl-damage.cc:1851
crawl-ref/source/spl-damage.cc",
crawl-ref/source/spl-damage.cc",

中文全文
```text
地牢在%s周围震动！

地牢在%s周围隆隆作响！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "The dungeon shakes around %s!",
    "zh_template": "地牢在%s周围震动！",
    "source": {
      "path": "crawl-ref/source/spl-damage.cc",
      "line": 1845
    },
    "parameter_expressions": [
      "T_(\"The dungeon shakes around %s!\")",
      "caster->name(DESC_THE).c_str()"
    ],
    "conditions_and_generation": "1827:     return damage;\n1828: }\n1829: \n1830: // For UI purposes.\n1831: dice_def mons_shatter_damage(int spell_hd)\n1832: {\n1833:     return dice_def(3, 5 + (5 + spell_hd * 9 / 2) / 3);\n1834: }\n1835: \n1836: bool mons_shatter(monster* caster, bool actual)\n1837: {\n1838:     const bool silence = silenced(caster->pos());\n1839:     int foes = 0;\n1840: \n1841:     if (actual)\n1842:     {\n1843:         if (silence)\n1844:         {\n1845:             mprf(T_(\"The dungeon shakes around %s!\"),\n1846:                  caster->name(DESC_THE).c_str());\n1847:         }\n1848:         else\n1849:         {\n1850:             noisy(spell_effect_noise(SPELL_SHATTER), caster->pos(), caster->mid);\n1851:             mprf(MSGCH_SOUND, T_(\"The dungeon rumbles around %s!\"),\n1852:                  caster->name(DESC_THE).c_str());\n1853:         }\n1854:     }\n1855: \n1856:     int pow = 5 + div_rand_round(caster->spell_hd() * 9, 2);\n1857: \n1858:     if (actual)\n1859:     {\n1860:         if (!Options.alt_shatter_animation)\n1861:             run_animation(ANIMATION_SHAKE_VIEWPORT, UA_MONSTER);\n1862:         else\n1863:         {\n1864:             // Initial shockwave pulse, then faint big explosion.",
    "method": "参数文本还原",
    "full_zh_display": "地牢在兽人周围震动！",
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "caster->name(DESC_THE).c_str()",
        "examples": [
          [
            "兽人",
            "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          ]
        ]
      }
    ],
    "branch_examples": [
      {
        "parameters": [
          {
            "expression": "caster->name(DESC_THE).c_str()",
            "value": "兽人",
            "source_and_state": "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          }
        ],
        "full_zh_display": "地牢在兽人周围震动！"
      }
    ],
    "formula": "按所列原始参数表达式和catalog参数示例逐位置替换；不增加冠词、量词或修正文案。"
  },
  {
    "english": "The dungeon rumbles around %s!",
    "zh_template": "地牢在%s周围隆隆作响！",
    "source": {
      "path": "crawl-ref/source/spl-damage.cc",
      "line": 1851
    },
    "parameter_expressions": [
      "MSGCH_SOUND",
      "T_(\"The dungeon rumbles around %s!\")",
      "caster->name(DESC_THE).c_str()"
    ],
    "conditions_and_generation": "1833:     return dice_def(3, 5 + (5 + spell_hd * 9 / 2) / 3);\n1834: }\n1835: \n1836: bool mons_shatter(monster* caster, bool actual)\n1837: {\n1838:     const bool silence = silenced(caster->pos());\n1839:     int foes = 0;\n1840: \n1841:     if (actual)\n1842:     {\n1843:         if (silence)\n1844:         {\n1845:             mprf(T_(\"The dungeon shakes around %s!\"),\n1846:                  caster->name(DESC_THE).c_str());\n1847:         }\n1848:         else\n1849:         {\n1850:             noisy(spell_effect_noise(SPELL_SHATTER), caster->pos(), caster->mid);\n1851:             mprf(MSGCH_SOUND, T_(\"The dungeon rumbles around %s!\"),\n1852:                  caster->name(DESC_THE).c_str());\n1853:         }\n1854:     }\n1855: \n1856:     int pow = 5 + div_rand_round(caster->spell_hd() * 9, 2);\n1857: \n1858:     if (actual)\n1859:     {\n1860:         if (!Options.alt_shatter_animation)\n1861:             run_animation(ANIMATION_SHAKE_VIEWPORT, UA_MONSTER);\n1862:         else\n1863:         {\n1864:             // Initial shockwave pulse, then faint big explosion.\n1865:             draw_ring_animation(caster->pos(), you.current_vision, YELLOW, BROWN,\n1866:                                 true, 20, TILE_BOLT_SHATTER_WAVE_YELLOW);\n1867:             bolt visual = bolt::visual_beam(caster->pos(), caster->pos(), 15,\n1868:                                             WHITE, TILE_BOLT_SHATTER_WAVE_WHITE);\n1869:             visual.glyph         = dchar_glyph(DCHAR_EXPLOSION);\n1870:             visual.ex_size       = you.current_vision;",
    "method": "参数文本还原",
    "full_zh_display": "地牢在兽人周围隆隆作响！",
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "caster->name(DESC_THE).c_str()",
        "examples": [
          [
            "兽人",
            "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          ]
        ]
      }
    ],
    "branch_examples": [
      {
        "parameters": [
          {
            "expression": "caster->name(DESC_THE).c_str()",
            "value": "兽人",
            "source_and_state": "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          }
        ],
        "full_zh_display": "地牢在兽人周围隆隆作响！"
      }
    ],
    "formula": "按所列原始参数表达式和catalog参数示例逐位置替换；不增加冠词、量词或修正文案。"
  }
]
```

4. 独立语义判断与还原
沉默使用视觉震动、否则使用声音分支；符号示例地牢在兽人周围震动！/地牢在兽人周围隆隆作响！，只验证名称语法，不声称普通兽人天然会施放该法术。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-6-02

1. 完整英文
```text
A %s emerges from the mists of... memory?....
```

2–3. stable 消费者与参数证据

crawl-ref/source/dat/des/altar/overflow.des:216
crawl-ref/source/dat/des/altar/overflow.des",

中文全文
```text
%s从……记忆的迷雾中浮现？……
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "A %s emerges from the mists of... memory?....",
    "zh_template": "%s从……记忆的迷雾中浮现？……",
    "source": {
      "path": "crawl-ref/source/dat/des/altar/overflow.des",
      "line": 216
    },
    "parameter_expressions": [
      "string.format(\n      crawl.t_(\"A %s emerges from the mists of... memory?....\"),\n      crawl.t_(sp))"
    ],
    "conditions_and_generation": "200: end\n201: \n202: function callback.do_species_mock(data, triggerable, triggerer, marker, ev)\n203:   if data.seen then return else data.seen = true end\n204:   local positions = dgn.find_marker_positions_by_prop(\"mock_location\", 1)\n205:   local sp = species_mock()\n206:   if you.race() == \"Poltergeist\" then\n207:     sp = \"dancing weapon\"\n208:   elseif you.race() == \"Mountain Dwarf\" then\n209:     sp = \"goblin\"\n210:   end\n211:   crawl.god_speaks(\"Xom\", crawl.t_('\"I found one of your ancestors!\"'))\n212:   for i, pos in ipairs(positions) do\n213:     local x, y = pos:xy()\n214:     dgn.create_monster(x, y, \"generate_awake \" .. species_mock())\n215:   end\n216:   crawl.mpr(string.format(\n217:       crawl.t_(\"A %s emerges from the mists of... memory?....\"),\n218:       crawl.t_(sp)))\n219: end\n220: }}\n221: \n222: default-depth: D:3-, Depths\n223: \n224: # These must feature one of the temple_overflow_* TAGs (see header).\n225: # Altars are sorted alphabetically by god, with the Shining One coming\n226: # after Zin. At the end, there are altar vaults which can be used for\n227: # more than just one god.\n228: \n229: ### Ashenzari overflow altars #################################################\n230: \n231: NAME:   ashenzari_altar_1\n232: TAGS:   transparent decor\n233: : standard_overflow_setup(_G, { { \"ashenzari\",  \"_\" } },  true)\n234: MAP",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/dat/des/altar/overflow.des:218
crawl-ref/source/dat/des/altar/overflow.des",

中文全文
```text
%s从……记忆的迷雾中浮现？……
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "A %s emerges from the mists of... memory?....",
    "zh_template": "%s从……记忆的迷雾中浮现？……",
    "source": {
      "path": "crawl-ref/source/dat/des/altar/overflow.des",
      "line": 218
    },
    "parameter_expressions": [
      "string.format(\n      crawl.t_(\"A %s emerges from the mists of... memory?....\"),\n      crawl.t_(sp))"
    ],
    "conditions_and_generation": "202: end\n203: \n204: function callback.do_species_mock(data, triggerable, triggerer, marker, ev)\n205:   if data.seen then return else data.seen = true end\n206:   local positions = dgn.find_marker_positions_by_prop(\"mock_location\", 1)\n207:   local sp = species_mock()\n208:   if you.race() == \"Poltergeist\" then\n209:     sp = \"dancing weapon\"\n210:   elseif you.race() == \"Mountain Dwarf\" then\n211:     sp = \"goblin\"\n212:   end\n213:   crawl.god_speaks(\"Xom\", crawl.t_('\"I found one of your ancestors!\"'))\n214:   for i, pos in ipairs(positions) do\n215:     local x, y = pos:xy()\n216:     dgn.create_monster(x, y, \"generate_awake \" .. species_mock())\n217:   end\n218:   crawl.mpr(string.format(\n219:       crawl.t_(\"A %s emerges from the mists of... memory?....\"),\n220:       crawl.t_(sp)))\n221: end\n222: }}\n223: \n224: default-depth: D:3-, Depths\n225: \n226: # These must feature one of the temple_overflow_* TAGs (see header).\n227: # Altars are sorted alphabetically by god, with the Shining One coming\n228: # after Zin. At the end, there are altar vaults which can be used for\n229: # more than just one god.\n230: \n231: ### Ashenzari overflow altars #################################################\n232: \n233: NAME:   ashenzari_altar_1\n234: TAGS:   transparent decor\n235: : standard_overflow_setup(_G, { { \"ashenzari\",  \"_\" } },  true)\n236: MAP",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。"
  }
]
```

4. 独立语义判断与还原
sp 来自 species_mock，特殊 Poltergeist/Mountain Dwarf 的嘲弄名称与问号保持，按 catalog 为名词短语，例地精从……记忆的迷雾中浮现？……；这是文本代入示例而非实际生成怪物身份断言。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-5-05

1. 完整英文
```text
<white>Welcome to Dungeon Crawl!</white>

Your objective is to lead your <w>{{ return you.race() }} {{ return you.class()
}}</w> safely through the depths of the dungeon, retrieving the fabled Orb of
Zot and returning it to the surface. In the beginning, however, let discovery
be your main goal. Try to delve as deeply as possible but beware; death lurks
around every corner.

For the moment, just remember the following keys and their functions:
  <input>$cmd[CMD_DISPLAY_COMMANDS]?</input> — shows the items and the commands
  <input>$cmd[CMD_SAVE_GAME]</input>  — saves the game, to be resumed later
(but note that death is permanent)
  <input>$cmd[CMD_LOOK_AROUND]</input>  — examines something in your vicinity

The hint mode will help you play Crawl without reading any documentation. If
you haven't yet, you might want to try out the tutorial. Also, if you feel
intrigued, there is more information available in the following files from the
docs/ directory (all of which can also be read in-game):
  <lightblue>quickstart.txt</lightblue>     — A very short guide to Crawl.
  <lightblue>crawl_manual.txt</lightblue>   — This contains all details on
species, magic, skills, etc.
  <lightblue>options_guide.txt</lightblue>  — Crawl's interface is highly
configurable. This document explains all the options.

Happy Crawling!
```

2–3. stable 消费者与参数证据

crawl-ref/source/hints.cc:401
crawl-ref/source/hints.cc:401
crawl-ref/source/hints.cc:483
crawl-ref/source/hints.cc:2884
crawl-ref/source/hints.cc",
crawl-ref/source/hints.cc",

中文全文
```text
<white>欢迎来到地牢爬行！</white>

你的目标是带领你的<w>{{ return crawl.t_(you.race()) .. " " .. crawl.t_(you.class()) }}</w>角色安全深入地牢，取回传说中的佐特宝珠并把它带回地面。不过，刚开始时，应把探索发现作为主要目标。尽量深入，但要小心；死亡潜伏在每个角落。

目前只需记住以下按键及其功能：
  <input>$cmd[CMD_DISPLAY_COMMANDS]?</input> — 显示物品和命令
  <input>$cmd[CMD_SAVE_GAME]</input>  — 保存游戏，稍后可以继续
（但请注意，死亡是永久的）
  <input>$cmd[CMD_LOOK_AROUND]</input>  — 查看附近的事物

提示模式能让你无需阅读任何文档即可游玩 Crawl。如果还没试过教程，不妨先玩一玩。若想进一步了解游戏，docs/ 目录下有以下文件（也都可以在游戏内阅读）：
  <lightblue>quickstart.txt</lightblue>     — 非常简短的 Crawl 入门指南。
  <lightblue>crawl_manual.txt</lightblue>   — 包含种族、魔法、技能等方面的全部详情。
  <lightblue>options_guide.txt</lightblue>  — Crawl 的界面高度可定制；本文档介绍全部选项。

祝你游戏愉快！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "zh_body": "<white>欢迎来到地牢爬行！</white>\n\n你的目标是带领你的<w>{{ return crawl.t_(you.race()) .. \" \" .. crawl.t_(you.class()) }}</w>角色安全深入地牢，取回传说中的佐特宝珠并把它带回地面。不过，刚开始时，应把探索发现作为主要目标。尽量深入，但要小心；死亡潜伏在每个角落。\n\n目前只需记住以下按键及其功能：\n  <input>$cmd[CMD_DISPLAY_COMMANDS]?</input> — 显示物品和命令\n  <input>$cmd[CMD_SAVE_GAME]</input>  — 保存游戏，稍后可以继续\n（但请注意，死亡是永久的）\n  <input>$cmd[CMD_LOOK_AROUND]</input>  — 查看附近的事物\n\n提示模式能让你无需阅读任何文档即可游玩 Crawl。如果还没试过教程，不妨先玩一玩。若想进一步了解游戏，docs/ 目录下有以下文件（也都可以在游戏内阅读）：\n  <lightblue>quickstart.txt</lightblue>     — 非常简短的 Crawl 入门指南。\n  <lightblue>crawl_manual.txt</lightblue>   — 包含种族、魔法、技能等方面的全部详情。\n  <lightblue>options_guide.txt</lightblue>  — Crawl 的界面高度可定制；本文档介绍全部选项。\n\n祝你游戏愉快！",
    "reason": "TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。",
    "parameter_source": "具体提示键/事件枚举由所列生产调用传入_get_hint/tutorial_msg→getHintString→HintsDB。",
    "key_generation_evidence": [
      {
        "path": "crawl-ref/source/hints.cc",
        "line": 401,
        "statement": "string text = getHintString(\"welcome\");",
        "snippet": "391:         if (item == \"<\")\n392:             item += \"<\";\n393: \n394:         text.replace(p, q - p + 1, item);\n395:     }\n396: }\n397: \n398: // Prints the hints mode welcome screen.\n399: void hints_starting_screen()\n400: {\n401:     string text = getHintString(\"welcome\");\n402:     _replace_static_tags(text);\n403:     trim_string(text);\n404: \n405:     auto prompt_ui = make_shared<Text>(formatted_string::parse_string(text));\n406:     prompt_ui->set_wrap_text(true);\n407: #ifdef USE_TILE_LOCAL\n408:     prompt_ui->max_size().width = 800;\n409: #else\n410:     prompt_ui->max_size().width = 80;\n411: #endif"
      }
    ]
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/hints.cc:402
crawl-ref/source/hints.cc:402
crawl-ref/source/hints.cc:484
crawl-ref/source/hints.cc:2386
crawl-ref/source/hints.cc",
crawl-ref/source/hints.cc",

中文全文
```text
<white>欢迎来到地牢爬行！</white>

你的目标是带领你的<w>{{ return crawl.t_(you.race()) }} {{ return crawl.t_(you.class()) }}</w>角色安全深入地牢，取回传说中的佐特宝珠并把它带回地面。不过，刚开始时，应把探索发现作为主要目标。尽量深入，但要小心；死亡潜伏在每个角落。

目前只需记住以下按键及其功能：
  <input>$cmd[CMD_DISPLAY_COMMANDS]?</input> — 显示物品和命令
  <input>$cmd[CMD_SAVE_GAME]</input>  — 保存游戏，稍后可以继续
（但请注意，死亡是永久的）
  <input>$cmd[CMD_LOOK_AROUND]</input>  — 查看附近的事物

提示模式能让你无需阅读任何文档即可游玩 Crawl。如果还没试过教程，不妨先玩一玩。若想进一步了解游戏，docs/ 目录下有以下文件（也都可以在游戏内阅读）：
  <lightblue>quickstart.txt</lightblue>     — 非常简短的 Crawl 入门指南。
  <lightblue>crawl_manual.txt</lightblue>   — 包含种族、魔法、技能等方面的全部详情。
  <lightblue>options_guide.txt</lightblue>  — Crawl 的界面高度可定制；本文档介绍全部选项。

祝你游戏愉快！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "zh_body": "<white>欢迎来到地牢爬行！</white>\n\n你的目标是带领你的<w>{{ return crawl.t_(you.race()) }} {{ return crawl.t_(you.class()) }}</w>角色安全深入地牢，取回传说中的佐特宝珠并把它带回地面。不过，刚开始时，应把探索发现作为主要目标。尽量深入，但要小心；死亡潜伏在每个角落。\n\n目前只需记住以下按键及其功能：\n  <input>$cmd[CMD_DISPLAY_COMMANDS]?</input> — 显示物品和命令\n  <input>$cmd[CMD_SAVE_GAME]</input>  — 保存游戏，稍后可以继续\n（但请注意，死亡是永久的）\n  <input>$cmd[CMD_LOOK_AROUND]</input>  — 查看附近的事物\n\n提示模式能让你无需阅读任何文档即可游玩 Crawl。如果还没试过教程，不妨先玩一玩。若想进一步了解游戏，docs/ 目录下有以下文件（也都可以在游戏内阅读）：\n  <lightblue>quickstart.txt</lightblue>     — 非常简短的 Crawl 入门指南。\n  <lightblue>crawl_manual.txt</lightblue>   — 包含种族、魔法、技能等方面的全部详情。\n  <lightblue>options_guide.txt</lightblue>  — Crawl 的界面高度可定制；本文档介绍全部选项。\n\n祝你游戏愉快！",
    "reason": "TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。",
    "parameter_source": "具体提示键/事件枚举由所列生产调用传入_get_hint/tutorial_msg→getHintString→HintsDB。",
    "key_generation_evidence": [
      {
        "path": "crawl-ref/source/hints.cc",
        "line": 402,
        "statement": "string text = getHintString(\"welcome\");",
        "snippet": "392:         if (item == \"<\")\n393:             item += \"<\";\n394: \n395:         text.replace(p, q - p + 1, item);\n396:     }\n397: }\n398: \n399: // Prints the hints mode welcome screen.\n400: void hints_starting_screen()\n401: {\n402:     string text = getHintString(\"welcome\");\n403:     _replace_static_tags(text);\n404:     trim_string(text);\n405: \n406:     auto prompt_ui = make_shared<Text>(formatted_string::parse_string(text));\n407:     prompt_ui->set_wrap_text(true);\n408: #ifdef USE_TILE_LOCAL\n409:     prompt_ui->max_size().width = 800;\n410: #else\n411:     prompt_ui->max_size().width = 80;\n412: #endif"
      }
    ]
  }
]
```

4. 独立语义判断与还原
目标、永久死亡、三种命令与三份文档完整；两版均通过 Lua 翻译种族背景，stable 合并表达式与 trunk 两块表达式的文本结果可等价。未证种族背景名在所有输入下的布局宽度。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-2-04

1. 完整英文
```text
Cuts the health of an adjacent creature in half. This damage is never
directly lethal.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:4934
crawl-ref/source/spl-data.h",

中文全文
```text
让一个邻近生物的生命值减半。但永远不会直接杀死目标。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "让一个邻近生物的生命值减半。但永远不会直接杀死目标。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:5471
crawl-ref/source/spl-data.h",

中文全文
```text
让一个邻近生物的生命值减半。但永远不会直接杀死目标。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "让一个邻近生物的生命值减半。但永远不会直接杀死目标。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
相邻目标生命减半、不直接致命两项同时完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-5-02

1. 完整英文
```text
:nowrap
<white>Tutorial 3 summary: Items</white>

<yellow>Item commands</yellow>
  <input>$cmd[CMD_PICKUP]</input>  pick up an item
  <input>$cmd[CMD_DROP]</input>  drop an item
  <input>$cmd[CMD_EQUIP]</input>  equip armour, weapons, and jewellery
  <input>$cmd[CMD_UNEQUIP]</input>  unequip armour, weapons, and jewellery
  <input>$cmd[CMD_READ]</input>  read a scroll
  <input>$cmd[CMD_QUAFF]</input>  quaff a potion
  <input>$cmd[CMD_EVOKE]</input>  evoke a wand

  Use and (un)equip commands are also available from item descriptions in the inventory menu (<input>$cmd[CMD_DISPLAY_INVENTORY]</input>).<localtiles>
  And of course, <input>mouseclicks</input> also work.</localtiles>

<yellow>Other</yellow>
  <input>$cmd[CMD_DISPLAY_COMMANDS]?</input> access the command help
  <input>$cmd[CMD_EXPLORE]</input>  explore automatically
  <input>$cmd[CMD_SEARCH_STASHES]</input> search for items/features previously seen<localtiles>
  Several of these commands can also be executed by clicking in the <w>command panel</w>.</localtiles>
```

2–3. stable 消费者与参数证据

crawl-ref/source/dat/des/tutorial/lesson3.des:15
crawl-ref/source/hints.cc:401
crawl-ref/source/hints.cc:483
crawl-ref/source/hints.cc:2884
crawl-ref/source/dat/des/tutorial/lesson3.des",
crawl-ref/source/dat/des/tutorial/lesson3.des",

中文全文
```text
:nowrap
<white>教程3总结：物品</white>

<yellow>物品命令</yellow>
  <input>$cmd[CMD_PICKUP]</input>  捡起物品
  <input>$cmd[CMD_DROP]</input>  丢弃物品
  <input>$cmd[CMD_EQUIP]</input>  装备护甲、武器和首饰
  <input>$cmd[CMD_UNEQUIP]</input>  卸下护甲、武器和首饰
  <input>$cmd[CMD_READ]</input>  阅读卷轴
  <input>$cmd[CMD_QUAFF]</input>  饮用药水
  <input>$cmd[CMD_EVOKE]</input> 使用魔杖

  也可以在物品栏菜单（<input>$cmd[CMD_DISPLAY_INVENTORY]</input>）中的物品描述界面使用物品，或执行装备、卸下命令。<localtiles>
  当然，你也可以用<input>鼠标点击</input>。</localtiles>

<yellow>其他</yellow>
  <input>$cmd[CMD_DISPLAY_COMMANDS]?</input> 查看命令帮助
  <input>$cmd[CMD_EXPLORE]</input>  自动探索
  <input>$cmd[CMD_SEARCH_STASHES]</input> 搜索之前看到过的物品/地标<localtiles>
  上述命令中有很多都可以通过点击<w>命令栏</w>来下达。</localtiles>
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "zh_body": ":nowrap\n<white>教程3总结：物品</white>\n\n<yellow>物品命令</yellow>\n  <input>$cmd[CMD_PICKUP]</input>  捡起物品\n  <input>$cmd[CMD_DROP]</input>  丢弃物品\n  <input>$cmd[CMD_EQUIP]</input>  装备护甲、武器和首饰\n  <input>$cmd[CMD_UNEQUIP]</input>  卸下护甲、武器和首饰\n  <input>$cmd[CMD_READ]</input>  阅读卷轴\n  <input>$cmd[CMD_QUAFF]</input>  饮用药水\n  <input>$cmd[CMD_EVOKE]</input> 使用魔杖\n\n  也可以在物品栏菜单（<input>$cmd[CMD_DISPLAY_INVENTORY]</input>）中的物品描述界面使用物品，或执行装备、卸下命令。<localtiles>\n  当然，你也可以用<input>鼠标点击</input>。</localtiles>\n\n<yellow>其他</yellow>\n  <input>$cmd[CMD_DISPLAY_COMMANDS]?</input> 查看命令帮助\n  <input>$cmd[CMD_EXPLORE]</input>  自动探索\n  <input>$cmd[CMD_SEARCH_STASHES]</input> 搜索之前看到过的物品/地标<localtiles>\n  上述命令中有很多都可以通过点击<w>命令栏</w>来下达。</localtiles>",
    "reason": "TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。",
    "parameter_source": "具体提示键/事件枚举由所列生产调用传入_get_hint/tutorial_msg→getHintString→HintsDB。",
    "key_generation_evidence": [
      {
        "path": "crawl-ref/source/dat/des/tutorial/lesson3.des",
        "line": 15,
        "statement": "crawl.tutorial_msg(\"tutorial3 exit\", true)",
        "snippet": "5: {{\n6: crawl_require(\"dlua/tutorial.lua\")\n7: \n8: tutorial3 = {}\n9: \n10: function tutorial3.msg(text)\n11:     return tutorial_msg(\"tutorial3 \" .. text)\n12: end\n13: \n14: function tutorial3.exit()\n15:     crawl.tutorial_msg(\"tutorial3 exit\", true)\n16: end\n17: \n18: function tutorial3.win()\n19:     crawl.mark_game_won()\n20:     return tutorial3.exit()\n21: end\n22: \n23: function callback.tutorial_trap(data, triggerable, triggerer, marker, ev)\n24:   crawl.mpr(crawl.t_(\"You hear a click...\"))\n25: "
      }
    ]
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/dat/des/tutorial/lesson3.des:15
crawl-ref/source/hints.cc:402
crawl-ref/source/hints.cc:484
crawl-ref/source/hints.cc:2386
crawl-ref/source/dat/des/tutorial/lesson3.des",
crawl-ref/source/dat/des/tutorial/lesson3.des",

中文全文
```text
:nowrap
<white>教程3总结：物品</white>

<yellow>物品命令</yellow>
  <input>$cmd[CMD_PICKUP]</input>  捡起物品
  <input>$cmd[CMD_DROP]</input>  丢弃物品
  <input>$cmd[CMD_EQUIP]</input>  装备护甲、武器和首饰
  <input>$cmd[CMD_UNEQUIP]</input>  卸下护甲、武器和首饰
  <input>$cmd[CMD_READ]</input>  阅读卷轴
  <input>$cmd[CMD_QUAFF]</input>  饮用药水
  <input>$cmd[CMD_EVOKE]</input> 使用魔杖

  也可以在物品栏菜单（<input>$cmd[CMD_DISPLAY_INVENTORY]</input>）中的物品描述界面使用物品，或执行装备、卸下命令。<localtiles>
  当然，你也可以用<input>鼠标点击</input>。</localtiles>

<yellow>其他</yellow>
  <input>$cmd[CMD_DISPLAY_COMMANDS]?</input> 查看命令帮助
  <input>$cmd[CMD_EXPLORE]</input>  自动探索
  <input>$cmd[CMD_SEARCH_STASHES]</input> 搜索之前看到过的物品/地标<localtiles>
  上述命令中有很多都可以通过点击<w>命令栏</w>来下达。</localtiles>
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "zh_body": ":nowrap\n<white>教程3总结：物品</white>\n\n<yellow>物品命令</yellow>\n  <input>$cmd[CMD_PICKUP]</input>  捡起物品\n  <input>$cmd[CMD_DROP]</input>  丢弃物品\n  <input>$cmd[CMD_EQUIP]</input>  装备护甲、武器和首饰\n  <input>$cmd[CMD_UNEQUIP]</input>  卸下护甲、武器和首饰\n  <input>$cmd[CMD_READ]</input>  阅读卷轴\n  <input>$cmd[CMD_QUAFF]</input>  饮用药水\n  <input>$cmd[CMD_EVOKE]</input> 使用魔杖\n\n  也可以在物品栏菜单（<input>$cmd[CMD_DISPLAY_INVENTORY]</input>）中的物品描述界面使用物品，或执行装备、卸下命令。<localtiles>\n  当然，你也可以用<input>鼠标点击</input>。</localtiles>\n\n<yellow>其他</yellow>\n  <input>$cmd[CMD_DISPLAY_COMMANDS]?</input> 查看命令帮助\n  <input>$cmd[CMD_EXPLORE]</input>  自动探索\n  <input>$cmd[CMD_SEARCH_STASHES]</input> 搜索之前看到过的物品/地标<localtiles>\n  上述命令中有很多都可以通过点击<w>命令栏</w>来下达。</localtiles>",
    "reason": "TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。",
    "parameter_source": "具体提示键/事件枚举由所列生产调用传入_get_hint/tutorial_msg→getHintString→HintsDB。",
    "key_generation_evidence": [
      {
        "path": "crawl-ref/source/dat/des/tutorial/lesson3.des",
        "line": 15,
        "statement": "crawl.tutorial_msg(\"tutorial3 exit\", true)",
        "snippet": "5: {{\n6: crawl_require(\"dlua/tutorial.lua\")\n7: \n8: tutorial3 = {}\n9: \n10: function tutorial3.msg(text)\n11:     return tutorial_msg(\"tutorial3 \" .. text)\n12: end\n13: \n14: function tutorial3.exit()\n15:     crawl.tutorial_msg(\"tutorial3 exit\", true)\n16: end\n17: \n18: function tutorial3.win()\n19:     crawl.mark_game_won()\n20:     return tutorial3.exit()\n21: end\n22: \n23: function callback.tutorial_trap(data, triggerable, triggerer, marker, ev)\n24:   crawl.mpr(crawl.t_(\"You hear a click...\"))\n25: "
      }
    ]
  }
]
```

4. 独立语义判断与还原
nowrap、命令宏、装备卸下、物品描述入口及图形点击分支保留；小幅空格差不构成已证对齐损坏。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-4-05

1. 完整英文
```text
You %s the altar of %s.
```

2–3. stable 消费者与参数证据

crawl-ref/source/religion.cc:4047
crawl-ref/source/religion.cc",

中文全文
```text
你%s了%s的祭坛。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You %s the altar of %s.",
    "zh_template": "你%s了%s的祭坛。",
    "source": {
      "path": "crawl-ref/source/religion.cc",
      "line": 4047
    },
    "parameter_expressions": [
      "T_(\"You %s the altar of %s.\")",
      "T_(action.c_str())",
      "god.c_str()"
    ],
    "conditions_and_generation": "4029:               N_(\"You place yourself before the altar of %s.\") },\n4030:             { \"curl up before\",\n4031:               N_(\"You curl up before the altar of %s.\") },\n4032:             { \"unroll yourself before\",\n4033:               N_(\"You unroll yourself before the altar of %s.\") },\n4034:             { \"scuttle before\",\n4035:               N_(\"You scuttle before the altar of %s.\") },\n4036:         };\n4037:         const char *key = nullptr;\n4038:         for (const auto &prayer : prayers)\n4039:             if (action == prayer.action)\n4040:             {\n4041:                 key = prayer.key;\n4042:                 break;\n4043:             }\n4044:         if (key)\n4045:             mprf(T_(key), god.c_str());\n4046:         else\n4047:             mprf(T_(\"You %s the altar of %s.\"), T_(action.c_str()), god.c_str());\n4048:     }\n4049:     // these are included in default force_more_message\n4050: \n4051:     // Note: using worship we could make some gods not allow followers to\n4052:     // return, or not allow worshippers from other religions. - bwr\n4053: \n4054:     // Gods can be racist...\n4055:     if (!player_can_join_god(which_god))\n4056:     {\n4057:         you.turn_is_over = false;\n4058:         print_god_rejection(which_god);\n4059:         return;\n4060:     }\n4061: \n4062:     if (!is_good_god(which_god) && you.penance[which_god])\n4063:     {\n4064:         you.turn_is_over = false;\n4065:         simple_god_message(T_(\" refuses to forgive you so easily!\"), false,",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "T_(action.c_str())",
        "examples": []
      },
      {
        "expression": "god.c_str()",
        "examples": []
      }
    ]
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/religion.cc:4127
crawl-ref/source/religion.cc",

中文全文
```text
你%s了%s的祭坛。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You %s the altar of %s.",
    "zh_template": "你%s了%s的祭坛。",
    "source": {
      "path": "crawl-ref/source/religion.cc",
      "line": 4127
    },
    "parameter_expressions": [
      "T_(\"You %s the altar of %s.\")",
      "get_form()->player_prayer_action().c_str()",
      "god.c_str()"
    ],
    "conditions_and_generation": "4109:             { \"squish down before\", N_(\"You squish down before the altar of %s.\") },\n4110:             { \"crawl onto\", N_(\"You crawl onto the altar of %s.\") },\n4111:             { \"place yourself before\", N_(\"You place yourself before the altar of %s.\") },\n4112:             { \"curl up before\", N_(\"You curl up before the altar of %s.\") },\n4113:             { \"unroll yourself before\", N_(\"You unroll yourself before the altar of %s.\") },\n4114:             { \"scuttle before\", N_(\"You scuttle before the altar of %s.\") },\n4115:         };\n4116:         const char *sentence = nullptr;\n4117:         for (const auto &prayer : prayers)\n4118:             if (action == prayer.action)\n4119:             {\n4120:                 sentence = prayer.sentence;\n4121:                 break;\n4122:             }\n4123:         const string god = god_name(which_god);\n4124:         if (sentence)\n4125:             mprf(T_(sentence), god.c_str());\n4126:         else\n4127:             mprf(T_(\"You %s the altar of %s.\"),\n4128:                  get_form()->player_prayer_action().c_str(), god.c_str());\n4129:     }\n4130:     // these are included in default force_more_message\n4131: \n4132:     // Note: using worship we could make some gods not allow followers to\n4133:     // return, or not allow worshippers from other religions. - bwr\n4134: \n4135:     // Gods can be racist...\n4136:     string rejection_message = cannot_join_god_reason(which_god);\n4137:     if (!rejection_message.empty())\n4138:     {\n4139:         you.turn_is_over = false;\n4140:         mprf(MSGCH_GOD, \"%s\", rejection_message.c_str());\n4141:         return;\n4142:     }\n4143: \n4144:     if (!is_good_god(which_god) && you.penance[which_god])\n4145:     {\n4146:         you.turn_is_over = false;",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "get_form()->player_prayer_action().c_str()",
        "examples": []
      },
      {
        "expression": "god.c_str()",
        "examples": []
      }
    ]
  }
]
```

4. 独立语义判断与还原

补查两版 dat/forms/*.yaml 的 prayer_action 与 dat/species/*.yaml 的 altar_action，并加入 species.cc:487-490 默认 kneel at 和 transform.cc:561-575 飞行默认 hover solemnly before。全部当前动作都命中 god_pitch 的完整句分流，活动差集为空，见 prayer_actions.json。trunk religion.cc:4085-4090 用 ScopedLangEn 取得规范动作，不会拿翻译过的动作误匹配。故本项 fallback 不作为当前正常游戏译文错误。

5. 术语对照及范围

ok。此结论覆盖当前非 deprecated 数据及默认动作；deprecated-hydra、deprecated-porcupine 的历史存档兼容恢复未做运行时验证，不把历史差集外推为现行缺陷。


## R4-2-01

1. 完整英文
```text
You call forth a shade to shield your allies.

%s calls forth a shade to shield themselves.
```

2–3. stable 消费者与参数证据

crawl-ref/source/spl-summoning.cc:1660
crawl-ref/source/spl-summoning.cc:1663
crawl-ref/source/spl-summoning.cc",
crawl-ref/source/spl-summoning.cc",

中文全文
```text
你召唤出一个暗影来保护你的盟友。

%s召唤出一个暗影来保护自己。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You call forth a shade to shield your allies.",
    "zh_template": "你召唤出一个暗影来保护你的盟友。",
    "source": {
      "path": "crawl-ref/source/spl-summoning.cc",
      "line": 1660
    },
    "parameter_expressions": [
      "T_(\"You call forth a shade to shield your allies.\")"
    ],
    "conditions_and_generation": "1642:     return spret::success;\n1643: }\n1644: \n1645: spret cast_martyrs_knell(const actor* caster, int pow, bool fail)\n1646: {\n1647:     if (caster->is_player() && !player_summon_check(MONS_MARTYRED_SHADE))\n1648:         return spret::abort;\n1649: \n1650:     fail_check();\n1651: \n1652:     mgen_data mg = _summon_data(*caster, MONS_MARTYRED_SHADE, summ_dur(2),\n1653:                                 SPELL_MARTYRS_KNELL);\n1654:     mg.hd = (6 + div_rand_round(pow, 11));\n1655: \n1656:     monster* shade = create_monster(mg);\n1657:     if (shade)\n1658:     {\n1659:         if (caster->is_player())\n1660:             mpr(T_(\"You call forth a shade to shield your allies.\"));\n1661:         else if (you.can_see(*shade))\n1662:         {\n1663:             mprf(T_(\"%s calls forth a shade to shield themselves.\"),\n1664:                  caster->name(DESC_THE).c_str());\n1665:         }\n1666: \n1667:         mons_update_aura(*shade);\n1668:     }\n1669:     else if (caster->is_player())\n1670:         canned_msg(MSG_NOTHING_HAPPENS);\n1671: \n1672:     return spret::success;\n1673: }\n1674: \n1675: static spell_type servitor_spells[] =\n1676: {\n1677:     // primary spells\n1678:     SPELL_LEHUDIBS_CRYSTAL_SPEAR,",
    "method": "静态模板，无参数",
    "full_zh_display": "你召唤出一个暗影来保护你的盟友。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  },
  {
    "english": "%s calls forth a shade to shield themselves.",
    "zh_template": "%s召唤出一个暗影来保护自己。",
    "source": {
      "path": "crawl-ref/source/spl-summoning.cc",
      "line": 1663
    },
    "parameter_expressions": [
      "T_(\"%s calls forth a shade to shield themselves.\")",
      "caster->name(DESC_THE).c_str()"
    ],
    "conditions_and_generation": "1645: spret cast_martyrs_knell(const actor* caster, int pow, bool fail)\n1646: {\n1647:     if (caster->is_player() && !player_summon_check(MONS_MARTYRED_SHADE))\n1648:         return spret::abort;\n1649: \n1650:     fail_check();\n1651: \n1652:     mgen_data mg = _summon_data(*caster, MONS_MARTYRED_SHADE, summ_dur(2),\n1653:                                 SPELL_MARTYRS_KNELL);\n1654:     mg.hd = (6 + div_rand_round(pow, 11));\n1655: \n1656:     monster* shade = create_monster(mg);\n1657:     if (shade)\n1658:     {\n1659:         if (caster->is_player())\n1660:             mpr(T_(\"You call forth a shade to shield your allies.\"));\n1661:         else if (you.can_see(*shade))\n1662:         {\n1663:             mprf(T_(\"%s calls forth a shade to shield themselves.\"),\n1664:                  caster->name(DESC_THE).c_str());\n1665:         }\n1666: \n1667:         mons_update_aura(*shade);\n1668:     }\n1669:     else if (caster->is_player())\n1670:         canned_msg(MSG_NOTHING_HAPPENS);\n1671: \n1672:     return spret::success;\n1673: }\n1674: \n1675: static spell_type servitor_spells[] =\n1676: {\n1677:     // primary spells\n1678:     SPELL_LEHUDIBS_CRYSTAL_SPEAR,\n1679:     SPELL_IOOD,\n1680:     SPELL_BOMBARD,\n1681:     SPELL_PLASMA_BEAM, // maybe should be higher?\n1682:     SPELL_PERMAFROST_ERUPTION,",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "caster->name(DESC_THE).c_str()",
        "examples": []
      }
    ]
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/spl-summoning.cc:1584
crawl-ref/source/spl-summoning.cc:1587
crawl-ref/source/spl-summoning.cc",
crawl-ref/source/spl-summoning.cc",

中文全文
```text
你召唤出一个暗影来保护你的盟友。

%s召唤出一个暗影来保护自己。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You call forth a shade to shield your allies.",
    "zh_template": "你召唤出一个暗影来保护你的盟友。",
    "source": {
      "path": "crawl-ref/source/spl-summoning.cc",
      "line": 1584
    },
    "parameter_expressions": [
      "T_(\"You call forth a shade to shield your allies.\")"
    ],
    "conditions_and_generation": "1566:     return spret::success;\n1567: }\n1568: \n1569: spret cast_martyrs_knell(const actor* caster, int pow, bool fail)\n1570: {\n1571:     if (caster->is_player() && !player_summon_check(MONS_MARTYRED_SHADE))\n1572:         return spret::abort;\n1573: \n1574:     fail_check();\n1575: \n1576:     mgen_data mg = _summon_data(*caster, MONS_MARTYRED_SHADE, summ_dur(2),\n1577:                                 SPELL_MARTYRS_KNELL);\n1578:     mg.hd = (6 + div_rand_round(pow, 11));\n1579: \n1580:     monster* shade = create_monster(mg);\n1581:     if (shade)\n1582:     {\n1583:         if (caster->is_player())\n1584:             mpr(T_(\"You call forth a shade to shield your allies.\"));\n1585:         else if (you.can_see(*shade))\n1586:         {\n1587:             mprf(T_(\"%s calls forth a shade to shield themselves.\"),\n1588:                  caster->name(DESC_THE).c_str());\n1589:         }\n1590: \n1591:         mons_update_aura(*shade);\n1592:     }\n1593:     else if (caster->is_player())\n1594:         canned_msg(MSG_NOTHING_HAPPENS);\n1595: \n1596:     return spret::success;\n1597: }\n1598: \n1599: static spell_type servitor_spells[] =\n1600: {\n1601:     // primary spells\n1602:     SPELL_LEHUDIBS_CRYSTAL_SPEAR,",
    "method": "静态模板，无参数",
    "full_zh_display": "你召唤出一个暗影来保护你的盟友。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  },
  {
    "english": "%s calls forth a shade to shield themselves.",
    "zh_template": "%s召唤出一个暗影来保护自己。",
    "source": {
      "path": "crawl-ref/source/spl-summoning.cc",
      "line": 1587
    },
    "parameter_expressions": [
      "T_(\"%s calls forth a shade to shield themselves.\")",
      "caster->name(DESC_THE).c_str()"
    ],
    "conditions_and_generation": "1569: spret cast_martyrs_knell(const actor* caster, int pow, bool fail)\n1570: {\n1571:     if (caster->is_player() && !player_summon_check(MONS_MARTYRED_SHADE))\n1572:         return spret::abort;\n1573: \n1574:     fail_check();\n1575: \n1576:     mgen_data mg = _summon_data(*caster, MONS_MARTYRED_SHADE, summ_dur(2),\n1577:                                 SPELL_MARTYRS_KNELL);\n1578:     mg.hd = (6 + div_rand_round(pow, 11));\n1579: \n1580:     monster* shade = create_monster(mg);\n1581:     if (shade)\n1582:     {\n1583:         if (caster->is_player())\n1584:             mpr(T_(\"You call forth a shade to shield your allies.\"));\n1585:         else if (you.can_see(*shade))\n1586:         {\n1587:             mprf(T_(\"%s calls forth a shade to shield themselves.\"),\n1588:                  caster->name(DESC_THE).c_str());\n1589:         }\n1590: \n1591:         mons_update_aura(*shade);\n1592:     }\n1593:     else if (caster->is_player())\n1594:         canned_msg(MSG_NOTHING_HAPPENS);\n1595: \n1596:     return spret::success;\n1597: }\n1598: \n1599: static spell_type servitor_spells[] =\n1600: {\n1601:     // primary spells\n1602:     SPELL_LEHUDIBS_CRYSTAL_SPEAR,\n1603:     SPELL_IOOD,\n1604:     SPELL_BOMBARD,\n1605:     SPELL_PLASMA_BEAM, // maybe should be higher?\n1606:     SPELL_PERMAFROST_ERUPTION,",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "caster->name(DESC_THE).c_str()",
        "examples": []
      }
    ]
  }
]
```

4. 独立语义判断与还原
玩家保护盟友与怪物保护自身分支区分完整；怪物名不含所有格，例兽人召唤出一个暗影来保护自己。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-5-04

1. 完整英文
```text
Miscasting a spell can have nasty consequences, particularly for the more
difficult spells. Your chance of successfully casting a spell increases with
your magic skills, and can also be improved with the help of some items. Use
the <w>$cmd[CMD_DISPLAY_SPELLS]</w> command<localtiles> or mouse over the spell
tiles</localtiles> to check your current failure rates.
```

2–3. stable 消费者与参数证据

crawl-ref/source/hints.cc:1704
crawl-ref/source/hints.cc:401
crawl-ref/source/hints.cc:483
crawl-ref/source/hints.cc:2884
crawl-ref/source/hints.cc",
crawl-ref/source/hints.cc",

中文全文
```text
施法失误可能造成恶劣后果，法术越难尤其如此。你的魔法技能越高，成功施放法术的概率就越大；一些物品也能提高这个概率。使用 <w>$cmd[CMD_DISPLAY_SPELLS]</w> 命令<localtiles>，或将鼠标悬停在法术图块上</localtiles>，即可查看当前的失败率。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "zh_body": "施法失误可能造成恶劣后果，法术越难尤其如此。你的魔法技能越高，成功施放法术的概率就越大；一些物品也能提高这个概率。使用 <w>$cmd[CMD_DISPLAY_SPELLS]</w> 命令<localtiles>，或将鼠标悬停在法术图块上</localtiles>，即可查看当前的失败率。",
    "reason": "TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。",
    "parameter_source": "具体提示键/事件枚举由所列生产调用传入_get_hint/tutorial_msg→getHintString→HintsDB。",
    "key_generation_evidence": [
      {
        "path": "crawl-ref/source/hints.cc",
        "line": 1704,
        "statement": "print_hint(\"HINT_SPELL_MISCAST_EFFECTS\");",
        "snippet": "1694:         break;\n1695: \n1696:     case HINT_SPELL_MISCAST:\n1697:     {\n1698:         // Don't give at the beginning of your spellcasting career.\n1699:         if (you.max_magic_points <= 2)\n1700:             DELAY_EVENT;\n1701: \n1702:         if (!crawl_state.game_is_hints())\n1703:         {\n1704:             print_hint(\"HINT_SPELL_MISCAST_EFFECTS\");\n1705:             break;\n1706:         }\n1707:         print_hint(\"HINT_YOU_MISCAST\");\n1708: \n1709:         if (!player_effectively_in_light_armour() || you.shield())\n1710:             print_hint(\"HINT_MISCAST_ARMOUR\");\n1711: \n1712:         print_hint(\"HINT_MISCAST_CONTAMINATION_AND_MP\");\n1713:         break;\n1714:     }"
      }
    ]
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/hints.cc:1602
crawl-ref/source/hints.cc:402
crawl-ref/source/hints.cc:484
crawl-ref/source/hints.cc:2386
crawl-ref/source/hints.cc",
crawl-ref/source/hints.cc",

中文全文
```text
施法失误可能造成恶劣后果，法术越难尤其如此。你的魔法技能越高，成功施放法术的概率就越大；一些物品也能提高这个概率。使用 <w>$cmd[CMD_DISPLAY_SPELLS]</w> 命令<localtiles>，或将鼠标悬停在法术图块上</localtiles>，即可查看当前的失败率。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "zh_body": "施法失误可能造成恶劣后果，法术越难尤其如此。你的魔法技能越高，成功施放法术的概率就越大；一些物品也能提高这个概率。使用 <w>$cmd[CMD_DISPLAY_SPELLS]</w> 命令<localtiles>，或将鼠标悬停在法术图块上</localtiles>，即可查看当前的失败率。",
    "reason": "TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。",
    "parameter_source": "具体提示键/事件枚举由所列生产调用传入_get_hint/tutorial_msg→getHintString→HintsDB。",
    "key_generation_evidence": [
      {
        "path": "crawl-ref/source/hints.cc",
        "line": 1602,
        "statement": "print_hint(\"HINT_SPELL_MISCAST_EFFECTS\");",
        "snippet": "1592:         break;\n1593: \n1594:     case HINT_SPELL_MISCAST:\n1595:     {\n1596:         // Don't give at the beginning of your spellcasting career.\n1597:         if (you.max_magic_points <= 2)\n1598:             DELAY_EVENT;\n1599: \n1600:         if (!crawl_state.game_is_hints())\n1601:         {\n1602:             print_hint(\"HINT_SPELL_MISCAST_EFFECTS\");\n1603:             break;\n1604:         }\n1605:         print_hint(\"HINT_YOU_MISCAST\");\n1606: \n1607:         if (!player_effectively_in_light_armour() || you.shield())\n1608:             print_hint(\"HINT_MISCAST_ARMOUR\");\n1609: \n1610:         print_hint(\"HINT_MISCAST_CONTAMINATION_AND_MP\");\n1611:         break;\n1612:     }"
      }
    ]
  }
]
```

4. 独立语义判断与还原
施法失误、困难法术后果、技能物品提升成功率与查失败率操作完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-1-06

1. 完整英文
```text
A small piece of wood and metal, to be strapped on one arm for defence.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:2895
crawl-ref/source/describe.cc:2907
crawl-ref/source/describe.cc:3461
crawl-ref/source/describe.cc:7279
crawl-ref/source/item-prop.cc",

中文全文
```text
一小块木头和金属，通过绑在一只手臂上进行防御。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一小块木头和金属，通过绑在一只手臂上进行防御。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:3167
crawl-ref/source/describe.cc:3179
crawl-ref/source/describe.cc:3731
crawl-ref/source/describe.cc:7967
crawl-ref/source/item-prop.cc",

中文全文
```text
一小块木头和金属，通过绑在一只手臂上进行防御。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一小块木头和金属，通过绑在一只手臂上进行防御。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
小型木金属制防具与单臂绑缚用途完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-2-03

1. 完整英文
```text
Hurls a crackling orb of electrical energy, creating a huge explosion on
impact. Its damage bypasses half of defenders' armour.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:4934
crawl-ref/source/spl-data.h",

中文全文
```text
掷出噼啪作响的电能量球，在撞击时产生巨大爆炸。
造成的伤害无视目标一半的护甲。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "掷出噼啪作响的电能量球，在撞击时产生巨大爆炸。\n造成的伤害无视目标一半的护甲。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:5471
crawl-ref/source/spl-data.h",

中文全文
```text
掷出噼啪作响的电能量球，在撞击时产生巨大爆炸。
造成的伤害无视目标一半的护甲。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "掷出噼啪作响的电能量球，在撞击时产生巨大爆炸。\n造成的伤害无视目标一半的护甲。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
爆炸电球与绕过一半护甲均保留。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-5-09

1. 完整英文
```text
You can search among all items existing in the dungeon with the
<input>$cmd[CMD_SEARCH_STASHES]</input> command. For example,
<input>$cmd[CMD_SEARCH_STASHES]</input> <w>“dagger”</w> will list all daggers,
and allow you to travel to them. You can even search for dungeon features, like
<w>“shop”</w> or <w>“altar”</w>.
```

2–3. stable 消费者与参数证据

crawl-ref/source/hints.cc:596
crawl-ref/source/hints.cc:401
crawl-ref/source/hints.cc:483
crawl-ref/source/hints.cc:2884
crawl-ref/source/hints.cc",
crawl-ref/source/hints.cc",

中文全文
```text
你可以用 <input>$cmd[CMD_SEARCH_STASHES]</input> 命令搜索地牢中现存的所有物品。例如，<input>$cmd[CMD_SEARCH_STASHES]</input> <w>‘匕首’</w> 会列出所有匕首，并让你前往它们所在的位置。你甚至可以搜索地牢设施，例如 <w>‘商店’</w> 或 <w>‘祭坛’</w>。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "zh_body": "你可以用 <input>$cmd[CMD_SEARCH_STASHES]</input> 命令搜索地牢中现存的所有物品。例如，<input>$cmd[CMD_SEARCH_STASHES]</input> <w>‘匕首’</w> 会列出所有匕首，并让你前往它们所在的位置。你甚至可以搜索地牢设施，例如 <w>‘商店’</w> 或 <w>‘祭坛’</w>。",
    "reason": "TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。",
    "parameter_source": "具体提示键/事件枚举由所列生产调用传入_get_hint/tutorial_msg→getHintString→HintsDB。",
    "key_generation_evidence": [
      {
        "path": "crawl-ref/source/hints.cc",
        "line": 596,
        "statement": "print_hint(\"finished stashes\");",
        "snippet": "586:     crawl_state.type = GAME_TYPE_NORMAL;\n587: \n588:     print_hint(\"finished\");\n589:     more();\n590: \n591:     if (Hints.hints_explored)\n592:         print_hint(\"finished explored\");\n593:     else if (Hints.hints_travel)\n594:         print_hint(\"finished travel\");\n595:     else if (Hints.hints_stashes)\n596:         print_hint(\"finished stashes\");\n597:     else\n598:         print_hint(make_stringf(\"finished random %d\", random2(4)));\n599:     more();\n600: \n601:     Hints.hints_events.init(false);\n602: \n603:     // Remove the hints mode file.\n604:     you.save->delete_chunk(\"tut\");\n605: }\n606: "
      }
    ]
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/hints.cc:597
crawl-ref/source/hints.cc:402
crawl-ref/source/hints.cc:484
crawl-ref/source/hints.cc:2386
crawl-ref/source/hints.cc",
crawl-ref/source/hints.cc",

中文全文
```text
你可以用 <input>$cmd[CMD_SEARCH_STASHES]</input> 命令搜索地牢中现存的所有物品。例如，<input>$cmd[CMD_SEARCH_STASHES]</input> <w>‘匕首’</w> 会列出所有匕首，并让你前往它们所在的位置。你甚至可以搜索地牢设施，例如 <w>‘商店’</w> 或 <w>‘祭坛’</w>。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "zh_body": "你可以用 <input>$cmd[CMD_SEARCH_STASHES]</input> 命令搜索地牢中现存的所有物品。例如，<input>$cmd[CMD_SEARCH_STASHES]</input> <w>‘匕首’</w> 会列出所有匕首，并让你前往它们所在的位置。你甚至可以搜索地牢设施，例如 <w>‘商店’</w> 或 <w>‘祭坛’</w>。",
    "reason": "TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。",
    "parameter_source": "具体提示键/事件枚举由所列生产调用传入_get_hint/tutorial_msg→getHintString→HintsDB。",
    "key_generation_evidence": [
      {
        "path": "crawl-ref/source/hints.cc",
        "line": 597,
        "statement": "print_hint(\"finished stashes\");",
        "snippet": "587:     crawl_state.type = GAME_TYPE_NORMAL;\n588: \n589:     print_hint(\"finished\");\n590:     more();\n591: \n592:     if (Hints.hints_explored)\n593:         print_hint(\"finished explored\");\n594:     else if (Hints.hints_travel)\n595:         print_hint(\"finished travel\");\n596:     else if (Hints.hints_stashes)\n597:         print_hint(\"finished stashes\");\n598:     else\n599:         print_hint(make_stringf(\"finished random %d\", random2(4)));\n600:     more();\n601: \n602:     Hints.hints_events.init(false);\n603: \n604:     // Remove the hints mode file.\n605:     you.save->delete_chunk(\"tut\");\n606: }\n607: "
      }
    ]
  }
]
```

4. 独立语义判断与还原
搜索物品与设施、搜索后旅行的操作保留；中文查询词须由实际中文显示名搜索路径支持，本批只静态核对示例与现行名称，不推断搜索覆盖未知物品。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-4-02

1. 完整英文
```text
%s regains the memory of %s %s.
```

2–3. stable 消费者与参数证据

crawl-ref/source/religion.cc:1798
crawl-ref/source/religion.cc",

中文全文
```text
%s恢复了%s%s的记忆。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "%s regains the memory of %s %s.",
    "zh_template": "%s恢复了%s%s的记忆。",
    "source": {
      "path": "crawl-ref/source/religion.cc",
      "line": 1798
    },
    "parameter_expressions": [
      "T_(\"%s regains the memory of %s %s.\")",
      "ancestor.name(DESC_YOUR, true).c_str()",
      "ancestor.pronoun(PRONOUN_POSSESSIVE, true).c_str()",
      "memory.c_str()"
    ],
    "conditions_and_generation": "1780:     _setup_hepliaklqana_ancestor();\n1781:     const monster_type type = you.props.exists(HEPLIAKLQANA_ALLY_TYPE_KEY) ?\n1782:         (monster_type)you.props[HEPLIAKLQANA_ALLY_TYPE_KEY].get_int() :\n1783:         MONS_ANCESTOR;\n1784:     mgen_data mg(type, BEH_FRIENDLY, you.pos(), MHITYOU, MG_AUTOFOE,\n1785:                  GOD_HEPLIAKLQANA);\n1786:     mg.hd = _hepliaklqana_ally_hd();\n1787:     mg.hp = hepliaklqana_ally_hp();\n1788:     mg.extra_flags |= MF_NO_REWARD;\n1789:     mg.mname = hepliaklqana_ally_name();\n1790:     mg.props[MON_GENDER_KEY]\n1791:         = you.props[HEPLIAKLQANA_ALLY_GENDER_KEY].get_int();\n1792:     return mg;\n1793: }\n1794: \n1795: /// Print a message for an ancestor's *something* being gained.\n1796: static void _regain_memory(const monster &ancestor, string memory)\n1797: {\n1798:     mprf(T_(\"%s regains the memory of %s %s.\"),\n1799:          ancestor.name(DESC_YOUR, true).c_str(),\n1800:          ancestor.pronoun(PRONOUN_POSSESSIVE, true).c_str(),\n1801:          memory.c_str());\n1802: }\n1803: \n1804: static string _item_ego_name(object_class_type base_type, int brand)\n1805: {\n1806:     switch (base_type)\n1807:     {\n1808:     case OBJ_WEAPONS:\n1809:     {\n1810:         // 'remembers... draining' reads better than 'drain', but 'flame'\n1811:         // reads better than 'flaming'\n1812:         const bool terse = brand == SPWPN_FLAMING\n1813:                            || brand == SPWPN_ANTIMAGIC;\n1814:         return brand_type_name((brand_type) brand, terse);\n1815:     }\n1816:     case OBJ_ARMOUR:\n1817:         // XXX: hack\n1818:         return T_(\"reflection\");\n1819:     default:",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "ancestor.name(DESC_YOUR, true).c_str()",
        "examples": []
      },
      {
        "expression": "ancestor.pronoun(PRONOUN_POSSESSIVE, true).c_str()",
        "examples": []
      },
      {
        "expression": "memory.c_str()",
        "examples": []
      }
    ]
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/religion.cc:1805
crawl-ref/source/religion.cc",

中文全文
```text
%s恢复了%s%s的记忆。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "%s regains the memory of %s %s.",
    "zh_template": "%s恢复了%s%s的记忆。",
    "source": {
      "path": "crawl-ref/source/religion.cc",
      "line": 1805
    },
    "parameter_expressions": [
      "T_(\"%s regains the memory of %s %s.\")",
      "ancestor.name(DESC_YOUR, true).c_str()",
      "ancestor.pronoun(PRONOUN_POSSESSIVE, true).c_str()",
      "memory.c_str()"
    ],
    "conditions_and_generation": "1787:     _setup_hepliaklqana_ancestor();\n1788:     const monster_type type = you.props.exists(HEPLIAKLQANA_ALLY_TYPE_KEY) ?\n1789:         (monster_type)you.props[HEPLIAKLQANA_ALLY_TYPE_KEY].get_int() :\n1790:         MONS_ANCESTOR;\n1791:     mgen_data mg(type, BEH_FRIENDLY, you.pos(), MHITYOU, MG_AUTOFOE,\n1792:                  GOD_HEPLIAKLQANA);\n1793:     mg.hd = _hepliaklqana_ally_hd();\n1794:     mg.hp = hepliaklqana_ally_hp(type);\n1795:     mg.extra_flags |= MF_NO_REWARD;\n1796:     mg.mname = hepliaklqana_ally_name();\n1797:     mg.props[MON_GENDER_KEY]\n1798:         = you.props[HEPLIAKLQANA_ALLY_GENDER_KEY].get_int();\n1799:     return mg;\n1800: }\n1801: \n1802: /// Print a message for an ancestor's *something* being gained.\n1803: static void _regain_memory(const monster &ancestor, string memory)\n1804: {\n1805:     mprf(T_(\"%s regains the memory of %s %s.\"),\n1806:          ancestor.name(DESC_YOUR, true).c_str(),\n1807:          ancestor.pronoun(PRONOUN_POSSESSIVE, true).c_str(),\n1808:          memory.c_str());\n1809: }\n1810: \n1811: static string _item_ego_name(object_class_type base_type, int brand)\n1812: {\n1813:     switch (base_type)\n1814:     {\n1815:     case OBJ_WEAPONS:\n1816:     {\n1817:         // 'remembers... draining' reads better than 'drain', but 'flame'\n1818:         // reads better than 'flaming'\n1819:         const bool terse = brand == SPWPN_FLAMING\n1820:                            || brand == SPWPN_ANTIMAGIC;\n1821:         return brand_type_name((brand_type) brand, terse);\n1822:     }\n1823:     case OBJ_ARMOUR:\n1824:         // XXX: hack\n1825:         return T_(\"reflection\");\n1826:     default:",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "ancestor.name(DESC_YOUR, true).c_str()",
        "examples": []
      },
      {
        "expression": "ancestor.pronoun(PRONOUN_POSSESSIVE, true).c_str()",
        "examples": []
      },
      {
        "expression": "memory.c_str()",
        "examples": []
      }
    ]
  }
]
```

4. 独立语义判断与还原
名称含你的前缀、PRONOUN_POSSESSIVE 含他的、memory 是物品/铭印等记忆，例你的先祖恢复了他的长剑的记忆。多层所有格各有对象，不是重复的。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-6-06

1. 完整英文
```text
You hear grinding stone!
```

2–3. stable 消费者与参数证据

crawl-ref/source/dat/des/branches/crypt.des:50
crawl-ref/source/dat/des/branches/crypt.des",

中文全文
```text
你听到石块摩擦的声音！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You hear grinding stone!",
    "zh_template": "你听到石块摩擦的声音！",
    "source": {
      "path": "crawl-ref/source/dat/des/branches/crypt.des",
      "line": 50
    },
    "parameter_expressions": [
      "crawl.t_(\"You hear grinding stone!\")",
      "\"warning\""
    ],
    "conditions_and_generation": "34:     end\n35: end\n36: \n37: function callback.grunt_crypt_arrival_guards_awaken(data,triggerable,trigger,marker,ev)\n38:     local seen = false\n39:     for replica in iter.replica_iterator(\"trap_sarcophagus\", 1) do\n40:         if you.see_cell(replica.x, replica.y) then\n41:             seen = true\n42:             break\n43:         end\n44:     end\n45:     if seen then\n46:         crawl.mpr(crawl.t_(\"Something awakens from inside the sarcophagi!\"), \"warning\")\n47:     elseif you.silenced() then\n48:         crawl.mpr(crawl.t_(\"The ground shakes!\"), \"warning\")\n49:     else\n50:         crawl.mpr(crawl.t_(\"You hear grinding stone!\"), \"warning\");\n51:     end\n52:     for replica in iter.replica_iterator(\"trap_sarcophagus\", 1) do\n53:         if dgn.feature_name(dgn.grid(replica.x, replica.y)) == \"granite_statue\" then\n54:             dgn.terrain_changed(replica.x, replica.y, \"floor\", false)\n55:             dgn.colour_at(replica.x, replica.y, \"lightgray\")\n56:             dgn.create_monster(replica.x, replica.y,\n57:                                \"human draugr / human zombie / \\\n58:                                 mummy w:20 / guardian mummy\")\n59:         end\n60:     end\n61: end\n62: \n63: function crypt_entry(e)\n64:     e.tags(\"crypt_entry vaults_entry_crypt patrolling\")\n65:     e.kmons(\"0 = necromancer w:5 / death knight w:5 / \\\n66:                  skeletal warrior / ghoul / \\",
    "method": "静态模板，无参数",
    "full_zh_display": "你听到石块摩擦的声音！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/dat/des/branches/crypt.des:50
crawl-ref/source/dat/des/branches/crypt.des",

中文全文
```text
你听到石块摩擦的声音！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You hear grinding stone!",
    "zh_template": "你听到石块摩擦的声音！",
    "source": {
      "path": "crawl-ref/source/dat/des/branches/crypt.des",
      "line": 50
    },
    "parameter_expressions": [
      "crawl.t_(\"You hear grinding stone!\")",
      "\"warning\""
    ],
    "conditions_and_generation": "34:     end\n35: end\n36: \n37: function callback.grunt_crypt_arrival_guards_awaken(data,triggerable,trigger,marker,ev)\n38:     local seen = false\n39:     for replica in iter.replica_iterator(\"trap_sarcophagus\", 1) do\n40:         if you.see_cell(replica.x, replica.y) then\n41:             seen = true\n42:             break\n43:         end\n44:     end\n45:     if seen then\n46:         crawl.mpr(crawl.t_(\"Something awakens from inside the sarcophagi!\"), \"warning\")\n47:     elseif you.silenced() then\n48:         crawl.mpr(crawl.t_(\"The ground shakes!\"), \"warning\")\n49:     else\n50:         crawl.mpr(crawl.t_(\"You hear grinding stone!\"), \"warning\");\n51:     end\n52:     for replica in iter.replica_iterator(\"trap_sarcophagus\", 1) do\n53:         if dgn.feature_name(dgn.grid(replica.x, replica.y)) == \"granite_statue\" then\n54:             dgn.terrain_changed(replica.x, replica.y, \"floor\", false)\n55:             dgn.colour_at(replica.x, replica.y, \"lightgray\")\n56:             dgn.create_monster(replica.x, replica.y,\n57:                                \"human draugr / human zombie / \\\n58:                                 mummy w:20 / guardian mummy\")\n59:         end\n60:     end\n61: end\n62: \n63: function crypt_entry(e)\n64:     e.tags(\"crypt_entry vaults_entry_crypt patrolling\")\n65:     e.kmons(\"0 = necromancer w:5 / death knight w:5 / \\\n66:                  skeletal warrior / ghoul / \\",
    "method": "静态模板，无参数",
    "full_zh_display": "你听到石块摩擦的声音！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

4. 独立语义判断与还原
石块摩擦听觉提示完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-4-06

1. 完整英文
```text
Your divine vigour has faded away.
```

2–3. stable 消费者与参数证据

crawl-ref/source/god-abil.cc:1412
crawl-ref/source/god-abil.cc",

中文全文
```text
你的神圣活力消退了。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "Your divine vigour has faded away.",
    "zh_template": "你的神圣活力消退了。",
    "source": {
      "path": "crawl-ref/source/god-abil.cc",
      "line": 1412
    },
    "parameter_expressions": [
      "MSGCH_DURATION",
      "T_(\"Your divine vigour has faded away.\")"
    ],
    "conditions_and_generation": "1394:     const int old_mp_max = you.max_magic_points;\n1395:     you.attribute[ATTR_DIVINE_VIGOUR] = vigour_amt;\n1396:     you.set_duration(DUR_DIVINE_VIGOUR,\n1397:                      40 + you.skill_rdiv(SK_INVOCATIONS, 5, 2));\n1398: \n1399:     calc_hp();\n1400:     inc_hp((you.hp_max * you.hp + old_hp_max - 1)/old_hp_max - you.hp);\n1401:     calc_mp();\n1402:     if (old_mp_max > 0)\n1403:     {\n1404:         inc_mp((you.max_magic_points * you.magic_points + old_mp_max - 1)\n1405:                  / old_mp_max\n1406:                - you.magic_points);\n1407:     }\n1408: }\n1409: \n1410: void elyvilon_remove_divine_vigour()\n1411: {\n1412:     mprf(MSGCH_DURATION, T_(\"Your divine vigour has faded away.\"));\n1413:     you.duration[DUR_DIVINE_VIGOUR] = 0;\n1414:     you.attribute[ATTR_DIVINE_VIGOUR] = 0;\n1415:     calc_hp();\n1416:     calc_mp();\n1417: }\n1418: \n1419: bool vehumet_supports_spell(spell_type spell)\n1420: {\n1421:     // Conjurations work by conjuring up a chunk of short-lived matter and\n1422:     // propelling it towards the victim. This is the most popular way, but\n1423:     // by no means it has a monopoly for being destructive.\n1424:     // Vehumet loves all direct physical destruction.\n1425:     return spell_typematch(spell, spschool::conjuration)\n1426:            || (get_spell_flags(spell) & spflag::destructive);\n1427: }\n1428: \n1429: void trog_do_trogs_hand(int pow)\n1430: {",
    "method": "静态模板，无参数",
    "full_zh_display": "你的神圣活力消退了。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/god-abil.cc:1454
crawl-ref/source/god-abil.cc",

中文全文
```text
你的神圣活力消退了。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "Your divine vigour has faded away.",
    "zh_template": "你的神圣活力消退了。",
    "source": {
      "path": "crawl-ref/source/god-abil.cc",
      "line": 1454
    },
    "parameter_expressions": [
      "MSGCH_DURATION",
      "T_(\"Your divine vigour has faded away.\")"
    ],
    "conditions_and_generation": "1436:     you.set_duration(DUR_DIVINE_VIGOUR,\n1437:                      40 + you.skill_rdiv(SK_INVOCATIONS, 5, 2));\n1438: \n1439:     calc_hp();\n1440:     inc_hp((you.hp_max * you.hp + old_hp_max - 1)/old_hp_max - you.hp);\n1441:     calc_mp();\n1442:     if (old_mp_max > 0)\n1443:     {\n1444:         inc_mp((you.max_magic_points * you.magic_points + old_mp_max - 1)\n1445:                  / old_mp_max\n1446:                - you.magic_points);\n1447:     }\n1448: \n1449:     player_update_auras();\n1450: }\n1451: \n1452: void elyvilon_remove_divine_vigour()\n1453: {\n1454:     mprf(MSGCH_DURATION, T_(\"Your divine vigour has faded away.\"));\n1455:     you.duration[DUR_DIVINE_VIGOUR] = 0;\n1456:     you.attribute[ATTR_DIVINE_VIGOUR] = 0;\n1457:     calc_hp();\n1458:     calc_mp();\n1459: }\n1460: \n1461: bool vehumet_supports_spell(spell_type spell)\n1462: {\n1463:     // Conjurations work by conjuring up a chunk of short-lived matter and\n1464:     // propelling it towards the victim. This is the most popular way, but\n1465:     // by no means it has a monopoly for being destructive.\n1466:     // Vehumet loves all direct physical destruction.\n1467:     return spell_typematch(spell, spschool::conjuration)\n1468:            || (get_spell_flags(spell) & spflag::destructive);\n1469: }\n1470: \n1471: void trog_do_trogs_hand(int pow)\n1472: {",
    "method": "静态模板，无参数",
    "full_zh_display": "你的神圣活力消退了。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

4. 独立语义判断与还原
神圣活力结束，完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-7-06

1. 完整英文
```text
%s rages.
```

2–3. stable 消费者与参数证据

crawl-ref/source/mon-act.cc:3837
crawl-ref/source/mon-act.cc",

中文全文
```text
%s狂怒不已。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "%s rages.",
    "zh_template": "%s狂怒不已。",
    "source": {
      "path": "crawl-ref/source/mon-act.cc",
      "line": 3837
    },
    "parameter_expressions": [
      "MSGCH_TALK_VISUAL",
      "T_(\"%s rages.\")",
      "mons->name(DESC_THE).c_str()"
    ],
    "conditions_and_generation": "3819:     _swim_or_move_energy(mons);\n3820: \n3821:     _maybe_launch_opportunity_attack(mons, orig_pos);\n3822:     _maybe_randomize_energy(mons, orig_pos);\n3823: \n3824:     return true;\n3825: }\n3826: \n3827: static bool _monster_move(monster* mons, coord_def& delta)\n3828: {\n3829:     ASSERT(mons); // XXX: change to monster &mons\n3830:     move_array good_move;\n3831: \n3832:     const habitat_type habitat = mons_habitat(*mons);\n3833:     bool deep_water_available = false;\n3834: \n3835:     // TODO: move the below logic out of move code.\n3836:     if (one_chance_in(10) && you.can_see(*mons) && mons->berserk())\n3837:         mprf(MSGCH_TALK_VISUAL, T_(\"%s rages.\"), mons->name(DESC_THE).c_str());\n3838:     // Look, this is silly.\n3839:     if (one_chance_in(5)\n3840:         && mons->has_ench(ENCH_FRENZIED)\n3841:         && get_shout_noise_level(mons_shouts(mons->type)))\n3842:     {\n3843:         monster_attempt_shout(*mons);\n3844:     }\n3845: \n3846:     // If a water (or lava) monster is currently flopping around on land, it\n3847:     // cannot really control where it wants to move, though there's a 50%\n3848:     // chance of flopping into an adjacent water (or lava) grid.\n3849:     if (mons->has_ench(ENCH_AQUATIC_LAND))\n3850:     {\n3851:         vector<coord_def> adj_water;\n3852:         vector<coord_def> adj_move;\n3853:         for (adjacent_iterator ai(mons->pos()); ai; ++ai)\n3854:         {\n3855:             if (!cell_is_solid(*ai))",
    "method": "参数文本还原",
    "full_zh_display": "兽人狂怒不已。",
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "mons->name(DESC_THE).c_str()",
        "examples": [
          [
            "兽人",
            "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          ]
        ]
      }
    ],
    "branch_examples": [
      {
        "parameters": [
          {
            "expression": "mons->name(DESC_THE).c_str()",
            "value": "兽人",
            "source_and_state": "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          }
        ],
        "full_zh_display": "兽人狂怒不已。"
      }
    ],
    "formula": "按所列原始参数表达式和catalog参数示例逐位置替换；不增加冠词、量词或修正文案。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/mon-act.cc:3987
crawl-ref/source/mon-act.cc",

中文全文
```text
%s狂怒不已。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "%s rages.",
    "zh_template": "%s狂怒不已。",
    "source": {
      "path": "crawl-ref/source/mon-act.cc",
      "line": 3987
    },
    "parameter_expressions": [
      "MSGCH_TALK_VISUAL",
      "T_(\"%s rages.\")",
      "mons->name(DESC_THE).c_str()"
    ],
    "conditions_and_generation": "3969:     _swim_or_move_energy(mons);\n3970: \n3971:     _maybe_launch_opportunity_attack(mons, orig_pos);\n3972:     _maybe_randomize_energy(mons, orig_pos);\n3973: \n3974:     return true;\n3975: }\n3976: \n3977: static bool _monster_move(monster* mons, coord_def& delta)\n3978: {\n3979:     ASSERT(mons); // XXX: change to monster &mons\n3980:     move_array good_move;\n3981: \n3982:     const habitat_type habitat = mons_habitat(*mons);\n3983:     bool deep_water_available = false;\n3984: \n3985:     // TODO: move the below logic out of move code.\n3986:     if (one_chance_in(10) && you.can_see(*mons) && mons->berserk())\n3987:         mprf(MSGCH_TALK_VISUAL, T_(\"%s rages.\"), mons->name(DESC_THE).c_str());\n3988:     // Look, this is silly.\n3989:     if (one_chance_in(5)\n3990:         && mons->has_ench(ENCH_FRENZIED)\n3991:         && get_shout_noise_level(mons_shouts(mons->type)))\n3992:     {\n3993:         monster_attempt_shout(*mons);\n3994:     }\n3995: \n3996:     // If a water (or lava) monster is currently flopping around on land, it\n3997:     // cannot really control where it wants to move, though there's a 50%\n3998:     // chance of flopping into an adjacent water (or lava) grid.\n3999:     if (mons->has_ench(ENCH_AQUATIC_LAND))\n4000:     {\n4001:         vector<coord_def> adj_water;\n4002:         vector<coord_def> adj_move;\n4003:         for (adjacent_iterator ai(mons->pos()); ai; ++ai)\n4004:         {\n4005:             if (!cell_is_solid(*ai))",
    "method": "参数文本还原",
    "full_zh_display": "兽人狂怒不已。",
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "mons->name(DESC_THE).c_str()",
        "examples": [
          [
            "兽人",
            "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          ]
        ]
      }
    ],
    "branch_examples": [
      {
        "parameters": [
          {
            "expression": "mons->name(DESC_THE).c_str()",
            "value": "兽人",
            "source_and_state": "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          }
        ],
        "full_zh_display": "兽人狂怒不已。"
      }
    ],
    "formula": "按所列原始参数表达式和catalog参数示例逐位置替换；不增加冠词、量词或修正文案。"
  }
]
```

4. 独立语义判断与还原
DESC_THE 名称接狂怒不已，完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-3-01

1. 完整英文
```text
A half-mortal, half-demonic creature, radiating an intense heat. It weaves
powerful and unpredictable spells of devastation.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:7279
crawl-ref/source/describe.cc:7270
crawl-ref/source/dat/mons/demonspawn-blood-saint.yaml",

中文全文
```text
一个半人半魔的生物，散发着强烈的热量。他编织着强大而不可预测的毁灭咒语。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一个半人半魔的生物，散发着强烈的热量。他编织着强大而不可预测的毁灭咒语。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:7967
crawl-ref/source/describe.cc:7958
crawl-ref/source/dat/mons/demonspawn-blood-saint.yaml",

中文全文
```text
一个半人半魔的生物，散发着强烈的热量。他编织着强大而不可预测的毁灭咒语。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一个半人半魔的生物，散发着强烈的热量。他编织着强大而不可预测的毁灭咒语。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
半凡人半恶魔的形象、强热及不可预测毁灭法术保留；半人半魔对应 demonspawn 描述语境，无需补数值。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-1-03

1. 完整英文
```text
Beam deals %dd%d damage.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:1930
crawl-ref/source/describe.cc",

中文全文
```text
光束造成%dd%d伤害。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "Beam deals %dd%d damage.",
    "zh_template": "光束造成%dd%d伤害。",
    "source": {
      "path": "crawl-ref/source/describe.cc",
      "line": 1930
    },
    "parameter_expressions": [
      "T_(\"Beam deals %dd%d damage.\")",
      "dmg.num",
      "dmg.size"
    ],
    "conditions_and_generation": "1912: \n1913:     // Overrides for ranged weapons and blade weapons, if they exist.\n1914:     if (ranged)\n1915:     {\n1916:         string ranged_ego_desc = getEgoString(ego_key + \" ranged\");\n1917:         if (!ranged_ego_desc.empty())\n1918:             ego_desc = ranged_ego_desc;\n1919:     }\n1920:     if (blade)\n1921:     {\n1922:         string blade_ego_desc = getEgoString(ego_key + \" blade\");\n1923:         if (!blade_ego_desc.empty())\n1924:             ego_desc = blade_ego_desc;\n1925:     }\n1926: \n1927:     if (ego == SPWPN_VALOUR)\n1928:     {\n1929:         dice_def dmg = zap_damage(ZAP_VALOUR_BEAM, property(item, PWPN_DAMAGE), false, false);\n1930:         ego_desc += make_stringf(T_(\"Beam deals %dd%d damage.\"), dmg.num, dmg.size);\n1931:     }\n1932: \n1933:     return ego_desc;\n1934: }\n1935: \n1936: static string _describe_point_change(float points)\n1937: {\n1938:     string point_diff_description;\n1939: \n1940:     point_diff_description += make_stringf(T_(\"%s by %.1f\"),\n1941:                                            points > 0 ? T_(\"increase\") : T_(\"decrease\"),\n1942:                                            abs(points));\n1943: \n1944:     return point_diff_description;\n1945: }\n1946: \n1947: static string _describe_point_diff(int original,\n1948:                                    int changed, int scale = 100)",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "dmg.num",
        "examples": []
      },
      {
        "expression": "dmg.size",
        "examples": []
      }
    ]
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:2043
crawl-ref/source/describe.cc",

中文全文
```text
光束造成%dd%d伤害。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "Beam deals %dd%d damage.",
    "zh_template": "光束造成%dd%d伤害。",
    "source": {
      "path": "crawl-ref/source/describe.cc",
      "line": 2043
    },
    "parameter_expressions": [
      "T_(\"Beam deals %dd%d damage.\")",
      "dmg.num",
      "dmg.size"
    ],
    "conditions_and_generation": "2025: \n2026:     // Overrides for ranged weapons and blade weapons, if they exist.\n2027:     if (ranged)\n2028:     {\n2029:         string ranged_ego_desc = getEgoString(ego_key + \" ranged\");\n2030:         if (!ranged_ego_desc.empty())\n2031:             ego_desc = ranged_ego_desc;\n2032:     }\n2033:     if (blade)\n2034:     {\n2035:         string blade_ego_desc = getEgoString(ego_key + \" blade\");\n2036:         if (!blade_ego_desc.empty())\n2037:             ego_desc = blade_ego_desc;\n2038:     }\n2039: \n2040:     if (ego == SPWPN_VALOUR)\n2041:     {\n2042:         dice_def dmg = zap_damage(ZAP_VALOUR_BEAM, property(item, PWPN_DAMAGE), false, false);\n2043:         ego_desc += make_stringf(T_(\"Beam deals %dd%d damage.\"), dmg.num, dmg.size);\n2044:     }\n2045: \n2046:     return ego_desc;\n2047: }\n2048: \n2049: static string _describe_point_change(float points)\n2050: {\n2051:     string point_diff_description;\n2052: \n2053:     point_diff_description += make_stringf(T_(\"%s by %.1f\"),\n2054:                                            points > 0 ? T_(\"increase\") : T_(\"decrease\"),\n2055:                                            abs(points));\n2056: \n2057:     return point_diff_description;\n2058: }\n2059: \n2060: static string _describe_point_diff(int original,\n2061:                                    int changed,",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "dmg.num",
        "examples": []
      },
      {
        "expression": "dmg.size",
        "examples": []
      }
    ]
  }
]
```

4. 独立语义判断与还原
两个整数分别为骰数与骰面，不是上下限；符号还原为光束造成NdS伤害，例如3d5。不把示例数值当作该物品固定数值。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-4-07

1. 完整英文
```text
You reach the end of your prayer and your brethren are recalled.
```

2–3. stable 消费者与参数证据

crawl-ref/source/god-abil.cc:2738
crawl-ref/source/god-abil.cc",

中文全文
```text
你的祷告结束，你的同胞被召回了。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You reach the end of your prayer and your brethren are recalled.",
    "zh_template": "你的祷告结束，你的同胞被召回了。",
    "source": {
      "path": "crawl-ref/source/god-abil.cc",
      "line": 2738
    },
    "parameter_expressions": [
      "MSGCH_DURATION",
      "T_(\"You reach the end of your prayer and your brethren are recalled.\")"
    ],
    "conditions_and_generation": "2720:     int max = 7 + you.skill_rdiv(SK_INVOCATIONS, 3, 4);\n2721:     if (count >= max)\n2722:         return;\n2723: \n2724:     // Summon orcs faster, the fewer of them we have.\n2725:     // Scales from ~1 orc per 6 aut at 0, up to ~1 orc per 50 aut near max\n2726:     int rate = 10 + 30 * (10 - (count * 10 / max)) / 10;\n2727:     if (count * 3 <= max)\n2728:         rate *= 2;\n2729: \n2730:     int num_to_summon = div_rand_round(rate * delay, 500);\n2731: \n2732:     for (int i = 0; i < num_to_summon; ++i)\n2733:         _place_orcish_reinforcement();\n2734: }\n2735: \n2736: void beogh_end_blood_for_blood()\n2737: {\n2738:     mprf(MSGCH_DURATION, T_(\"You reach the end of your prayer and your brethren are recalled.\"));\n2739:     for (monster_iterator mi; mi; ++mi)\n2740:     {\n2741:         if (mons_is_blood_for_blood_orc(**mi))\n2742:         {\n2743:             place_cloud(CLOUD_TLOC_ENERGY, mi->pos(), 1 + random2(3), *mi);\n2744:             monster_die(**mi, KILL_RESET, -1, true);\n2745:         }\n2746:     }\n2747:     you.duration[DUR_BLOOD_FOR_BLOOD] = 0;\n2748: }\n2749: \n2750: void beogh_ally_healing()\n2751: {\n2752:     if (!you.props.exists(BEOGH_DAMAGE_DONE_KEY)\n2753:         || x_chance_in_y(2, 5)\n2754:         || you.piety() < piety_breakpoint(2))\n2755:     {\n2756:         you.props.erase(BEOGH_DAMAGE_DONE_KEY);",
    "method": "静态模板，无参数",
    "full_zh_display": "你的祷告结束，你的同胞被召回了。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/god-abil.cc:2918
crawl-ref/source/god-abil.cc",

中文全文
```text
你的祷告结束，你的同胞被召回了。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You reach the end of your prayer and your brethren are recalled.",
    "zh_template": "你的祷告结束，你的同胞被召回了。",
    "source": {
      "path": "crawl-ref/source/god-abil.cc",
      "line": 2918
    },
    "parameter_expressions": [
      "MSGCH_DURATION",
      "T_(\"You reach the end of your prayer and your brethren are recalled.\")"
    ],
    "conditions_and_generation": "2900:     int max = 7 + you.skill_rdiv(SK_INVOCATIONS, 3, 4);\n2901:     if (count >= max)\n2902:         return;\n2903: \n2904:     // Summon orcs faster, the fewer of them we have.\n2905:     // Scales from ~1 orc per 6 aut at 0, up to ~1 orc per 50 aut near max\n2906:     int rate = 10 + 30 * (10 - (count * 10 / max)) / 10;\n2907:     if (count * 3 <= max)\n2908:         rate *= 2;\n2909: \n2910:     int num_to_summon = div_rand_round(rate * delay, 500);\n2911: \n2912:     for (int i = 0; i < num_to_summon; ++i)\n2913:         _place_orcish_reinforcement();\n2914: }\n2915: \n2916: void beogh_end_blood_for_blood()\n2917: {\n2918:     mprf(MSGCH_DURATION, T_(\"You reach the end of your prayer and your brethren are recalled.\"));\n2919:     for (monster_iterator mi; mi; ++mi)\n2920:     {\n2921:         if (mons_is_blood_for_blood_orc(**mi))\n2922:         {\n2923:             place_cloud(CLOUD_TLOC_ENERGY, mi->pos(), 1 + random2(3), *mi);\n2924:             monster_die(**mi, KILL_RESET, -1, true);\n2925:         }\n2926:     }\n2927:     you.duration[DUR_BLOOD_FOR_BLOOD] = 0;\n2928: }\n2929: \n2930: void beogh_ally_healing()\n2931: {\n2932:     if (!you.props.exists(BEOGH_DAMAGE_DONE_KEY)\n2933:         || x_chance_in_y(2, 5)\n2934:         || you.piety() < piety_breakpoint(2))\n2935:     {\n2936:         you.props.erase(BEOGH_DAMAGE_DONE_KEY);",
    "method": "静态模板，无参数",
    "full_zh_display": "你的祷告结束，你的同胞被召回了。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

4. 独立语义判断与还原
祈祷结束并召回同胞，完成状态完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-3-07

1. 完整英文
```text
A sly, conniving thief. A self-proclaimed legend, he was one of the most skilled
and crafty of the thieves and rogues lured by the Orb. The magical parasitic
vines that have claimed his body still wish to continue his life's work, with a
back-up plan of both a vicious magic-drinking maw and potent wands.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:7279
crawl-ref/source/describe.cc:7270
crawl-ref/source/dat/mons/maurice.yaml",

中文全文
```text
一个狡猾、搞阴谋的盗贼。
他自称是一位传奇人物，是被宝珠吸引而来的小偷和流氓中最熟练、最狡诈的一个。
而占据了他身体的魔力寄生藤蔓仍然希望继续其一生的工作，
并拥有一张能吸取魔力的凶恶大口和强大的魔杖以备不时之需。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一个狡猾、搞阴谋的盗贼。\n他自称是一位传奇人物，是被宝珠吸引而来的小偷和流氓中最熟练、最狡诈的一个。\n而占据了他身体的魔力寄生藤蔓仍然希望继续其一生的工作，\n并拥有一张能吸取魔力的凶恶大口和强大的魔杖以备不时之需。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:7967
crawl-ref/source/describe.cc:7958
crawl-ref/source/dat/mons/maurice.yaml",

中文全文
```text
一个狡猾、搞阴谋的盗贼。
他自称是一位传奇人物，是被宝珠吸引而来的小偷和流氓中最熟练、最狡诈的一个。
而占据了他身体的魔力寄生藤蔓仍然希望继续其一生的工作，
并拥有一张能吸取魔力的凶恶大口和强大的魔杖以备不时之需。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一个狡猾、搞阴谋的盗贼。\n他自称是一位传奇人物，是被宝珠吸引而来的小偷和流氓中最熟练、最狡诈的一个。\n而占据了他身体的魔力寄生藤蔓仍然希望继续其一生的工作，\n并拥有一张能吸取魔力的凶恶大口和强大的魔杖以备不时之需。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
盗贼传奇、寄生藤蔓接续事业及吸魔口/魔杖后备手段完整。文学魔力不限于 MP 资源键。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-3-08

1. 完整英文
```text
A swift, nightmarish bird whose razor-sharp metallic feathers drip with
corrosive acid.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:7279
crawl-ref/source/describe.cc:7270
crawl-ref/source/dat/mons/caustic-shrike.yaml",

中文全文
```text
一只迅捷而噩梦般的鸟，剃刀般锋利的金属羽毛滴着腐蚀性酸液。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一只迅捷而噩梦般的鸟，剃刀般锋利的金属羽毛滴着腐蚀性酸液。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:7967
crawl-ref/source/describe.cc:7958
crawl-ref/source/dat/mons/caustic-shrike.yaml",

中文全文
```text
一只迅捷而噩梦般的鸟，剃刀般锋利的金属羽毛滴着腐蚀性酸液。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一只迅捷而噩梦般的鸟，剃刀般锋利的金属羽毛滴着腐蚀性酸液。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
迅捷噩梦鸟、锋利金属羽与腐蚀酸液完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-3-05

1. 完整英文
```text
%s animating energy erupts into ghostly fire!
```

2–3. stable 消费者与参数证据

crawl-ref/source/mon-cast.cc:4628
crawl-ref/source/mon-cast.cc",

中文全文
```text
%s活化能量爆发成幽灵之火！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "%s animating energy erupts into ghostly fire!",
    "zh_template": "%s活化能量爆发成幽灵之火！",
    "source": {
      "path": "crawl-ref/source/mon-cast.cc",
      "line": 4628
    },
    "parameter_expressions": [
      "T_(\"%s animating energy erupts into ghostly fire!\")",
      "apostrophise(victim->name(DESC_THE)).c_str()"
    ],
    "conditions_and_generation": "4610:         }\n4611:     }\n4612: \n4613:     return best_target;\n4614: }\n4615: \n4616: /// Everything short of the actual explosion. Returns whether to explode.\n4617: static bool _prepare_ghostly_sacrifice(monster &caster, bolt &beam)\n4618: {\n4619:     if (!in_bounds(beam.target))\n4620:         return false; // assert?\n4621: \n4622:     monster* victim = monster_at(beam.target);\n4623:     if (!victim)\n4624:         return false; // assert?\n4625: \n4626:     if (you.see_cell(victim->pos()))\n4627:     {\n4628:         mprf(T_(\"%s animating energy erupts into ghostly fire!\"),\n4629:              apostrophise(victim->name(DESC_THE)).c_str());\n4630:     }\n4631:     monster_die(*victim, &caster, true);\n4632:     return true;\n4633: }\n4634: \n4635: /// Setup and target a ghostly sacrifice explosion.\n4636: static void _setup_ghostly_sacrifice_beam(bolt& beam, const monster& caster,\n4637:                                           int power)\n4638: {\n4639:     zappy(ZAP_GHOSTLY_SACRIFICE, power, true, beam);\n4640:     beam.target = _mons_ghostly_sacrifice_target(caster, beam);\n4641:     beam.aimed_at_spot = true;  // to get noise to work properly\n4642: }\n4643: \n4644: // Choose a target for Launch Bomblet. Prefer our foe, if not already in ideal\n4645: // range of it. Pick some other valid hostile, if not.\n4646: static coord_def _mons_bomblet_target(const monster& caster)\n4647: {",
    "method": "参数文本还原",
    "full_zh_display": "兽人活化能量爆发成幽灵之火！",
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "apostrophise(victim->name(DESC_THE)).c_str()",
        "examples": [
          [
            "兽人",
            "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          ]
        ]
      }
    ],
    "branch_examples": [
      {
        "parameters": [
          {
            "expression": "apostrophise(victim->name(DESC_THE)).c_str()",
            "value": "兽人",
            "source_and_state": "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          }
        ],
        "full_zh_display": "兽人活化能量爆发成幽灵之火！"
      }
    ],
    "formula": "按所列原始参数表达式和catalog参数示例逐位置替换；不增加冠词、量词或修正文案。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/mon-cast.cc:4727
crawl-ref/source/mon-cast.cc",

中文全文
```text
%s活化能量爆发成幽灵之火！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "%s animating energy erupts into ghostly fire!",
    "zh_template": "%s活化能量爆发成幽灵之火！",
    "source": {
      "path": "crawl-ref/source/mon-cast.cc",
      "line": 4727
    },
    "parameter_expressions": [
      "T_(\"%s animating energy erupts into ghostly fire!\")",
      "apostrophise(victim->name(DESC_THE)).c_str()"
    ],
    "conditions_and_generation": "4709:         }\n4710:     }\n4711: \n4712:     return best_target;\n4713: }\n4714: \n4715: /// Everything short of the actual explosion. Returns whether to explode.\n4716: static bool _prepare_ghostly_sacrifice(monster &caster, bolt &beam)\n4717: {\n4718:     if (!in_bounds(beam.target))\n4719:         return false; // assert?\n4720: \n4721:     monster* victim = monster_at(beam.target);\n4722:     if (!victim)\n4723:         return false; // assert?\n4724: \n4725:     if (you.see_cell(victim->pos()))\n4726:     {\n4727:         mprf(T_(\"%s animating energy erupts into ghostly fire!\"),\n4728:              apostrophise(victim->name(DESC_THE)).c_str());\n4729:     }\n4730:     monster_die(*victim, &caster, true);\n4731:     return true;\n4732: }\n4733: \n4734: /// Setup and target a ghostly sacrifice explosion.\n4735: static void _setup_ghostly_sacrifice_beam(bolt& beam, const monster& caster,\n4736:                                           int power)\n4737: {\n4738:     zappy(ZAP_GHOSTLY_SACRIFICE, power, true, beam);\n4739:     beam.target = _mons_ghostly_sacrifice_target(caster, beam);\n4740:     beam.aimed_at_spot = true;  // to get noise to work properly\n4741: }\n4742: \n4743: // Choose a target for Launch Bomblet. Prefer our foe, if not already in ideal\n4744: // range of it. Pick some other valid hostile, if not.\n4745: static coord_def _mons_bomblet_target(const monster& caster)\n4746: {",
    "method": "参数文本还原",
    "full_zh_display": "兽人活化能量爆发成幽灵之火！",
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "apostrophise(victim->name(DESC_THE)).c_str()",
        "examples": [
          [
            "兽人",
            "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          ]
        ]
      }
    ],
    "branch_examples": [
      {
        "parameters": [
          {
            "expression": "apostrophise(victim->name(DESC_THE)).c_str()",
            "value": "兽人",
            "source_and_state": "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          }
        ],
        "full_zh_display": "兽人活化能量爆发成幽灵之火！"
      }
    ],
    "formula": "按所列原始参数表达式和catalog参数示例逐位置替换；不增加冠词、量词或修正文案。"
  }
]
```

4. 独立语义判断与还原
apostrophise(victim.name(DESC_THE)) 先生成兽人的，因此生产为兽人的活化能量爆发成幽灵之火！；输入兽人活化能量漏了参数内的的，不是生产缺陷。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-4-09

1. 完整英文
```text
The Black Torch roars with renewed intensity!
```

2–3. stable 消费者与参数证据

crawl-ref/source/god-abil.cc:1591
crawl-ref/source/god-abil.cc",

中文全文
```text
黑火炬以新的强度咆哮着！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "The Black Torch roars with renewed intensity!",
    "zh_template": "黑火炬以新的强度咆哮着！",
    "source": {
      "path": "crawl-ref/source/god-abil.cc",
      "line": 1591
    },
    "parameter_expressions": [
      "MSGCH_GOD",
      "T_(\"The Black Torch roars with renewed intensity!\")"
    ],
    "conditions_and_generation": "1573:     if (!mons_can_be_spectralised(*mons, true))\n1574:         return;\n1575: \n1576:     // Track any valid kill, so we can tell how throughly the player scoured\n1577:     // the floor afterward\n1578:     you.props[YRED_KILLS_LOGGED_KEY].get_int() += 1;\n1579: \n1580:     // Only gain fuel from uniques we could raise, and will not bind\n1581:     if (!mons_is_unique(mons->type)\n1582:         || mons->has_ench(ENCH_SOUL_RIPE))\n1583:     {\n1584:         return;\n1585:     }\n1586: \n1587:     if (!player_has_ability(ABIL_YRED_HURL_TORCHLIGHT))\n1588:         return;\n1589: \n1590:     // Gain one torchlight charge for each unique killed\n1591:     mprf(MSGCH_GOD, T_(\"The Black Torch roars with renewed intensity!\"));\n1592:     you.props[YRED_TORCH_POWER_KEY].get_int() += 1;\n1593: }\n1594: \n1595: // Determine if this enemy is adjacent to at least one ally\n1596: static bool _is_isolated_soul(monster* mons)\n1597: {\n1598:     for (adjacent_iterator ai(mons->pos()); ai; ++ai)\n1599:     {\n1600:         const actor* act = actor_at(*ai);\n1601:         if (!act || !act->is_monster())\n1602:             continue;\n1603: \n1604:         if (!act->is_firewood() && mons_aligned(mons, act))\n1605:             return false;\n1606:     }\n1607:     return true;\n1608: }\n1609: ",
    "method": "静态模板，无参数",
    "full_zh_display": "黑火炬以新的强度咆哮着！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/god-abil.cc:1682
crawl-ref/source/god-abil.cc",

中文全文
```text
黑火炬以新的强度咆哮着！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "The Black Torch roars with renewed intensity!",
    "zh_template": "黑火炬以新的强度咆哮着！",
    "source": {
      "path": "crawl-ref/source/god-abil.cc",
      "line": 1682
    },
    "parameter_expressions": [
      "MSGCH_GOD",
      "T_(\"The Black Torch roars with renewed intensity!\")"
    ],
    "conditions_and_generation": "1664:     if (!mons_can_be_spectralised(*mons, true))\n1665:         return;\n1666: \n1667:     // Track any valid kill, so we can tell how throughly the player scoured\n1668:     // the floor afterward\n1669:     you.props[YRED_KILLS_LOGGED_KEY].get_int() += 1;\n1670: \n1671:     // Only gain fuel from uniques we could raise, and will not bind\n1672:     if (!mons_is_unique(mons->type)\n1673:         || mons->has_ench(ENCH_SOUL_RIPE))\n1674:     {\n1675:         return;\n1676:     }\n1677: \n1678:     if (!player_has_ability(ABIL_YRED_HURL_TORCHLIGHT))\n1679:         return;\n1680: \n1681:     // Gain one torchlight charge for each unique killed\n1682:     mprf(MSGCH_GOD, T_(\"The Black Torch roars with renewed intensity!\"));\n1683:     you.props[YRED_TORCH_POWER_KEY].get_int() += 1;\n1684: }\n1685: \n1686: // Determine if this enemy is adjacent to at least one ally\n1687: static bool _is_isolated_soul(monster* mons)\n1688: {\n1689:     for (adjacent_iterator ai(mons->pos()); ai; ++ai)\n1690:     {\n1691:         const actor* act = actor_at(*ai);\n1692:         if (!act || !act->is_monster())\n1693:             continue;\n1694: \n1695:         if (!act->is_firewood() && mons_aligned(mons, act))\n1696:             return false;\n1697:     }\n1698:     return true;\n1699: }\n1700: ",
    "method": "静态模板，无参数",
    "full_zh_display": "黑火炬以新的强度咆哮着！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

4. 独立语义判断与还原
renewed intensity 应表达再度强烈；新的强度较生硬，建议再度猛烈地咆哮起来。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：readability

{"type": "wording", "line": "both", "english": "The Black Torch roars with renewed intensity!", "current_full_zh": "黑火炬以新的强度咆哮着！", "problem": "以新的强度咆哮着不够自然，renewed 在此是恢复并再度强烈。", "suggested_zh": "黑火炬再度猛烈地咆哮起来！", "evidence": "crawl-ref/source/god-abil.cc:1591; crawl-ref/source/god-abil.cc\",", "defect_points": 0}


## R4-1-07

1. 完整英文
```text
A wooden cudgel, loaded with more than just lead.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:2869
crawl-ref/source/art-data.txt",

中文全文
```text
这根木棍，灌的可不仅仅是铅。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "这根木棍，灌的可不仅仅是铅。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:3141
crawl-ref/source/art-data.txt",

中文全文
```text
这根木棍，灌的可不仅仅是铅。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "这根木棍，灌的可不仅仅是铅。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
loaded 的双关与不仅铅的伏笔保留，不据文学描述补机制。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-6-03

1. 完整英文
```text
They guard the %s rune of Zot.
```

2–3. stable 消费者与参数证据

crawl-ref/source/dat/des/branches/pan.des:41
crawl-ref/source/dat/des/branches/pan.des",

中文全文
```text
其守护着佐特%s符文。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "They guard the %s rune of Zot.",
    "zh_template": "其守护着佐特%s符文。",
    "source": {
      "path": "crawl-ref/source/dat/des/branches/pan.des",
      "line": 41
    },
    "parameter_expressions": [
      "string.format(crawl.t_(\"They guard the %s rune of Zot.\"),\n                           crawl.t_(runes[name]))"
    ],
    "conditions_and_generation": "25:         ['Lom Lobon'] = \"You sense a powerful magical presence. It is not pleased.\",\n26:         Cerebov = \"Searing heat pours from the floors and walls of this place.\",\n27:         ['Gloorx Vloq'] = \"Shadowy figures dance across your vision.\"\n28:     }\n29:     local runes = {\n30:         Mnoleg = \"glowing\",\n31:         ['Lom Lobon'] = \"magical\",\n32:         Cerebov = \"fiery\",\n33:         ['Gloorx Vloq'] = \"dark\"\n34:     }\n35: \n36:     crawl.mpr(crawl.t_(msgs[name]), \"warning\")\n37:     crawl.mpr(string.format(\n38:         crawl.t_(\"The mighty Pandemonium lord %s resides here.\"),\n39:         crawl.t_(name)), \"warning\")\n40:     -- Counterpart to branch_rune_desc from lookup-help.cc\n41:     crawl.mpr(string.format(crawl.t_(\"They guard the %s rune of Zot.\"),\n42:                            crawl.t_(runes[name])))\n43:     crawl.take_note(util.i18n_format_or_english(\n44:         \"Entered the realm of %s.\", name))\n45:     crawl.mark_milestone('br.enter', 'entered the realm of ' .. name .. '.', \"\")\n46: end\n47: \n48: function pan_lord_setup(_G, name)\n49:     _G.tags(\"unrand\")\n50: \n51:     local monsters = {\n52:         Mnoleg = \"sin beast band w:100 / \" ..\n53:                  \"neqoxec w:250 / chaos spawn w:250 / \" ..\n54:                  \"zykzyl w:300 / tormentor / \" ..\n55:                  \"tentacled monstrosity / protean progenitor band / \" ..\n56:                  \"very ugly thing / glass eye band / \" ..\n57:                  \"golden eye band / eye of devastation / \"..\n58:                  \"shining eye / demonspawn corrupter\",",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/dat/des/branches/pan.des:41
crawl-ref/source/dat/des/branches/pan.des",

中文全文
```text
其守护着佐特%s符文。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "They guard the %s rune of Zot.",
    "zh_template": "其守护着佐特%s符文。",
    "source": {
      "path": "crawl-ref/source/dat/des/branches/pan.des",
      "line": 41
    },
    "parameter_expressions": [
      "string.format(crawl.t_(\"They guard the %s rune of Zot.\"),\n                           crawl.t_(runes[name]))"
    ],
    "conditions_and_generation": "25:         ['Lom Lobon'] = \"You sense a powerful magical presence. It is not pleased.\",\n26:         Cerebov = \"Searing heat pours from the floors and walls of this place.\",\n27:         ['Gloorx Vloq'] = \"Shadowy figures dance across your vision.\"\n28:     }\n29:     local runes = {\n30:         Mnoleg = \"glowing\",\n31:         ['Lom Lobon'] = \"magical\",\n32:         Cerebov = \"fiery\",\n33:         ['Gloorx Vloq'] = \"dark\"\n34:     }\n35: \n36:     crawl.mpr(crawl.t_(msgs[name]), \"warning\")\n37:     crawl.mpr(string.format(\n38:         crawl.t_(\"The mighty Pandemonium lord %s resides here.\"),\n39:         crawl.t_(name)), \"warning\")\n40:     -- Counterpart to branch_rune_desc from lookup-help.cc\n41:     crawl.mpr(string.format(crawl.t_(\"They guard the %s rune of Zot.\"),\n42:                            crawl.t_(runes[name])))\n43:     crawl.take_note(util.i18n_format_or_english(\n44:         \"Entered the realm of %s.\", name))\n45:     crawl.mark_milestone('br.enter', 'entered the realm of ' .. name .. '.', \"\")\n46: end\n47: \n48: function pan_lord_setup(_G, name)\n49:     _G.tags(\"unrand\")\n50: \n51:     local monsters = {\n52:         Mnoleg = \"sin beast band w:100 / \" ..\n53:                  \"neqoxec w:250 / chaos spawn w:250 / \" ..\n54:                  \"zykzyl w:300 / tormentor / \" ..\n55:                  \"tentacled monstrosity / protean progenitor band / \" ..\n56:                  \"very ugly thing / glass eye band / \" ..\n57:                  \"golden eye band / eye of devastation / \"..\n58:                  \"shining eye / demonspawn corrupter\",",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。"
  }
]
```

4. 独立语义判断与还原
符文修饰来自 glowing/magical/fiery/dark，例其守护着佐特炽热符文。；they 指单个领主，中文其正确。具体名以 catalog 为准。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-2-06

1. 完整英文
```text
Summons multiple floating eyeballs that may be able to vitrify, polymorph,
confuse, mutate or disintegrate.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:4934
crawl-ref/source/spl-data.h",

中文全文
```text
召唤多个浮空眼球，它们可能会造成玻化、变形、混乱、变异或碎裂。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "召唤多个浮空眼球，它们可能会造成玻化、变形、混乱、变异或碎裂。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:5471
crawl-ref/source/spl-data.h",

中文全文
```text
召唤一个或多个浮空眼球，它们可能会造成玻化、变形、混乱、变异或碎裂。
```

trunk 完整英文
```text
Summons one or more floating eyeballs that may be able to vitrify, polymorph,
confuse, mutate or disintegrate.

crawl-ref/source/describe.cc:5471
```cpp
5461:  * @param mon_owner     If this spell is being examined from a monster's
5462:  *                      description, 'spell' is that monster. Else, null.
5463:  * @param description   Set to the description & details of the spell.
5464:  */
5465: static void _get_spell_description(const spell_type spell,
5466:                                   const monster_info *mon_owner,
5467:                                   string &description)
5468: {
5469:     description.reserve(500);
5470:
5471:     const string long_descrip = getLongDescription(string(spell_english_name(spell))
5472:                                                    + " spell");
5473:
5474:     if (!long_descrip.empty())
5475:         description += long_descrip;
5476:     else
5477:     {
5478:         description += T_("This spell has no description. Casting it may therefore be unwise. ");
5479: #ifdef DEBUG
5480:                        T_("Better go fix it.");
5481: #else
```


具体键生成证据：
```json
[
  {
    "path": "crawl-ref/source/spl-data.h",
    "line": 1674,
    "statement": "SPELL_SUMMON_EYEBALLS, \"Summon Eyeballs\",",
    "snippet": "1664:     spschool::none,\n1665:     spflag::monster,\n1666:     5,\n1667:     0,\n1668:     -1, -1,\n1669:     0,\n1670:     TILEG_CREATE_TENTACLES,\n1671: },\n1672: \n1673: {\n1674:     SPELL_SUMMON_EYEBALLS, \"Summon Eyeballs\",\n1675:     spschool::summoning,\n1676:     spflag::monster | spflag::mons_abjure,\n1677:     5,\n1678:     0,\n1679:     -1, -1,\n1680:     0,\n1681:     TILEG_SUMMON_EYEBALLS,\n1682: },\n1683: \n1684: {"
  }
]
```
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "召唤一个或多个浮空眼球，它们可能会造成玻化、变形、混乱、变异或碎裂。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
stable 多个与 trunk 一个或多个分别对应各版英文；五类效果完整。玻化是使目标玻璃化的动作描述，不是改动独立法术名称。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-5-08

1. 完整英文
```text
There are a lot of items here. You choose what to pick up from a menu:
press <w>$cmd[CMD_PICKUP]</w><localtiles> or <w>click</w> on the player
doll</localtiles> to enter the pickup menu. To leave the menu, confirm your
selection with <w>Enter</w>.
```

2–3. stable 消费者与参数证据

crawl-ref/source/dat/des/tutorial/lesson3.des:70
crawl-ref/source/hints.cc:1359
crawl-ref/source/tutorial.cc:43
crawl-ref/source/hints.cc:401
crawl-ref/source/hints.cc:483
crawl-ref/source/hints.cc:2884
crawl-ref/source/dat/des/tutorial/lesson3.des",
crawl-ref/source/hints.cc",
crawl-ref/source/tutorial.cc",
crawl-ref/source/dat/des/tutorial/lesson3.des",
crawl-ref/source/hints.cc",
crawl-ref/source/tutorial.cc",

中文全文
```text
这里有很多物品。你从一个菜单中选择要捡起的东西：
按 <w>$cmd[CMD_PICKUP]</w><localtiles> 或 <w>点击</w> 角色人偶</localtiles>
来进入捡取菜单。要离开菜单，用 <w>回车</w> 确认你的选择。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "zh_body": "这里有很多物品。你从一个菜单中选择要捡起的东西：\n按 <w>$cmd[CMD_PICKUP]</w><localtiles> 或 <w>点击</w> 角色人偶</localtiles>\n来进入捡取菜单。要离开菜单，用 <w>回车</w> 确认你的选择。",
    "reason": "TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。",
    "parameter_source": "具体提示键/事件枚举由所列生产调用传入_get_hint/tutorial_msg→getHintString→HintsDB。",
    "key_generation_evidence": [
      {
        "path": "crawl-ref/source/dat/des/tutorial/lesson3.des",
        "line": 70,
        "statement": "crawl.tutorial_hint(\"HINT_MULTI_PICKUP\")",
        "snippet": "60: MARKER:  } = lua:tutorial3.msg(\"downstairs\")\n61: MARKER:  ] = lua:tutorial3.msg(\"downstairs\")\n62: MARKER:  { = lua:one_way_stair { dst  = \"tutorial_lesson3\", \\\n63:                                  onclimb = \"tutorial3.exit\" }\n64: MARKER:  ( = lua:one_way_stair { dst  = \"tutorial_lesson3\", \\\n65:                                  onclimb = \"tutorial3.exit\" }\n66: MARKER:  [ = lua:one_way_stair { dst  = \"tutorial_lesson3\", \\\n67:                                  onclimb = \"tutorial3.exit\" }\n68: epilogue{{\n69:   if crawl.game_started() then\n70:     crawl.tutorial_hint(\"HINT_MULTI_PICKUP\")\n71:     crawl.tutorial_hint(\"HINT_CHOOSE_STAT\")\n72:     crawl.clear_messages(true)\n73:     crawl.tutorial_msg(\"tutorial3 start\")\n74:     tutorial_intro()\n75:   end\n76: }}\n77: MAP\n78: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n79: xxxxxxxxxxxxxxxxx.....xxxxxxxxxxxxxxxxxxx\n80: xxxxxxxxxxxxxx.....e..xxxxxxxxxxxxxxxxxxx"
      },
      {
        "path": "crawl-ref/source/hints.cc",
        "line": 1359,
        "statement": "print_hint(\"HINT_MULTI_PICKUP\");",
        "snippet": "1349:             Hints.hints_just_triggered = true;\n1350:         }\n1351:         print_hint(\"HINT_YOU_POISON\");\n1352:         break;\n1353: \n1354:     case HINT_ON_FIRE:\n1355:         print_hint(\"HINT_ON_FIRE\");\n1356:         break;\n1357: \n1358:     case HINT_MULTI_PICKUP:\n1359:         print_hint(\"HINT_MULTI_PICKUP\");\n1360:         break;\n1361: \n1362:     case HINT_FULL_INVENTORY:\n1363:         print_hint(\"HINT_FULL_INVENTORY\");\n1364:         break;\n1365: \n1366:     case HINT_SHIFT_RUN:\n1367:         print_hint(\"HINT_SHIFT_RUN\");\n1368:         break;\n1369: "
      },
      {
        "path": "crawl-ref/source/tutorial.cc",
        "line": 43,
        "statement": "else if (strcmp(hintstr, \"HINT_MULTI_PICKUP\") == 0)",
        "snippet": "33: }\n34: \n35: // FIXME: There's got to be a less hacky solution!\n36: void tutorial_init_hint(const char* hintstr)\n37: {\n38:     hints_event_type hint = HINT_EVENTS_NUM;\n39:     if (strcmp(hintstr, \"HINT_NEW_LEVEL\") == 0)\n40:         hint = HINT_NEW_LEVEL;\n41:     else if (strcmp(hintstr, \"HINT_CHOOSE_STAT\") == 0)\n42:         hint = HINT_CHOOSE_STAT;\n43:     else if (strcmp(hintstr, \"HINT_MULTI_PICKUP\") == 0)\n44:         hint = HINT_MULTI_PICKUP;\n45: \n46:     if (hint != HINT_EVENTS_NUM)\n47:         Hints.hints_events[hint] = true;\n48: }\n49: \n50: // noreturn, but tutorial_msg doesn't guarantee it\n51: void tutorial_death_message()\n52: {\n53:     canned_msg(MSG_YOU_DIE);"
      }
    ]
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/dat/des/tutorial/lesson3.des:70
crawl-ref/source/hints.cc:1282
crawl-ref/source/tutorial.cc:43
crawl-ref/source/hints.cc:402
crawl-ref/source/hints.cc:484
crawl-ref/source/hints.cc:2386
crawl-ref/source/dat/des/tutorial/lesson3.des",
crawl-ref/source/hints.cc",
crawl-ref/source/tutorial.cc",
crawl-ref/source/dat/des/tutorial/lesson3.des",
crawl-ref/source/hints.cc",
crawl-ref/source/tutorial.cc",

中文全文
```text
这里有很多物品。你从一个菜单中选择要捡起的东西：
按 <w>$cmd[CMD_PICKUP]</w><localtiles> 或 <w>点击</w> 角色人偶</localtiles>
来进入捡取菜单。要离开菜单，用 <w>回车</w> 确认你的选择。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "zh_body": "这里有很多物品。你从一个菜单中选择要捡起的东西：\n按 <w>$cmd[CMD_PICKUP]</w><localtiles> 或 <w>点击</w> 角色人偶</localtiles>\n来进入捡取菜单。要离开菜单，用 <w>回车</w> 确认你的选择。",
    "reason": "TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。",
    "parameter_source": "具体提示键/事件枚举由所列生产调用传入_get_hint/tutorial_msg→getHintString→HintsDB。",
    "key_generation_evidence": [
      {
        "path": "crawl-ref/source/dat/des/tutorial/lesson3.des",
        "line": 70,
        "statement": "crawl.tutorial_hint(\"HINT_MULTI_PICKUP\")",
        "snippet": "60: MARKER:  } = lua:tutorial3.msg(\"downstairs\")\n61: MARKER:  ] = lua:tutorial3.msg(\"downstairs\")\n62: MARKER:  { = lua:one_way_stair { dst  = \"tutorial_lesson3\", \\\n63:                                  onclimb = \"tutorial3.exit\" }\n64: MARKER:  ( = lua:one_way_stair { dst  = \"tutorial_lesson3\", \\\n65:                                  onclimb = \"tutorial3.exit\" }\n66: MARKER:  [ = lua:one_way_stair { dst  = \"tutorial_lesson3\", \\\n67:                                  onclimb = \"tutorial3.exit\" }\n68: epilogue{{\n69:   if crawl.game_started() then\n70:     crawl.tutorial_hint(\"HINT_MULTI_PICKUP\")\n71:     crawl.tutorial_hint(\"HINT_CHOOSE_STAT\")\n72:     crawl.clear_messages(true)\n73:     crawl.tutorial_msg(\"tutorial3 start\")\n74:     tutorial_intro()\n75:   end\n76: }}\n77: MAP\n78: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n79: xxxxxxxxxxxxxxxxx.....xxxxxxxxxxxxxxxxxxx\n80: xxxxxxxxxxxxxx.....e..xxxxxxxxxxxxxxxxxxx"
      },
      {
        "path": "crawl-ref/source/hints.cc",
        "line": 1282,
        "statement": "print_hint(\"HINT_MULTI_PICKUP\");",
        "snippet": "1272:             Hints.hints_just_triggered = true;\n1273:         }\n1274:         print_hint(\"HINT_YOU_POISON\");\n1275:         break;\n1276: \n1277:     case HINT_ON_FIRE:\n1278:         print_hint(\"HINT_ON_FIRE\");\n1279:         break;\n1280: \n1281:     case HINT_MULTI_PICKUP:\n1282:         print_hint(\"HINT_MULTI_PICKUP\");\n1283:         break;\n1284: \n1285:     case HINT_FULL_INVENTORY:\n1286:         print_hint(\"HINT_FULL_INVENTORY\");\n1287:         break;\n1288: \n1289:     case HINT_SHIFT_RUN:\n1290:         print_hint(\"HINT_SHIFT_RUN\");\n1291:         break;\n1292: "
      },
      {
        "path": "crawl-ref/source/tutorial.cc",
        "line": 43,
        "statement": "else if (strcmp(hintstr, \"HINT_MULTI_PICKUP\") == 0)",
        "snippet": "33: }\n34: \n35: // FIXME: There's got to be a less hacky solution!\n36: void tutorial_init_hint(const char* hintstr)\n37: {\n38:     hints_event_type hint = HINT_EVENTS_NUM;\n39:     if (strcmp(hintstr, \"HINT_NEW_LEVEL\") == 0)\n40:         hint = HINT_NEW_LEVEL;\n41:     else if (strcmp(hintstr, \"HINT_CHOOSE_STAT\") == 0)\n42:         hint = HINT_CHOOSE_STAT;\n43:     else if (strcmp(hintstr, \"HINT_MULTI_PICKUP\") == 0)\n44:         hint = HINT_MULTI_PICKUP;\n45: \n46:     if (hint != HINT_EVENTS_NUM)\n47:         Hints.hints_events[hint] = true;\n48: }\n49: \n50: // noreturn, but tutorial_msg doesn't guarantee it\n51: void tutorial_death_message()\n52: {\n53:     canned_msg(MSG_YOU_DIE);"
      }
    ]
  }
]
```

4. 独立语义判断与还原
多项捡取菜单、快捷键/点击及回车确认完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-7-05

1. 完整英文
```text
escapes!

 struggles to escape constriction.
```

2–3. stable 消费者与参数证据

crawl-ref/source/mon-act.cc:3734
crawl-ref/source/mon-act.cc:3737
crawl-ref/source/mon-act.cc",
crawl-ref/source/dat/i18n/zh/source.txt",
crawl-ref/source/dat/i18n/zh/source.txt",
crawl-ref/source/mon-act.cc",
crawl-ref/source/dat/i18n/zh/source.txt",
crawl-ref/source/dat/i18n/zh/source.txt",

中文全文
```text
逃脱了！

 挣扎着想要挣脱束缚。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": " escapes!",
    "zh_template": " 逃脱了！",
    "source": {
      "path": "crawl-ref/source/mon-act.cc",
      "line": 3734
    },
    "parameter_expressions": [
      "mons",
      "T_(\" escapes!\")"
    ],
    "conditions_and_generation": "3716: \n3717:     if (f == you.pos())\n3718:     {\n3719:         // XX is this actually reachable?\n3720:         fight_melee(&mons, &you);\n3721:         return true;\n3722:     }\n3723: \n3724:     // This includes the case where the monster attacks itself.\n3725:     if (monster* def = monster_at(f))\n3726:     {\n3727:         fight_melee(&mons, def);\n3728:         return true;\n3729:     }\n3730: \n3731:     if (mons.is_constricted() && !mons.cannot_move())\n3732:     {\n3733:         if (mons.attempt_escape())\n3734:             simple_monster_message(mons, T_(\" escapes!\"));\n3735:         else\n3736:         {\n3737:             simple_monster_message(mons, T_(\" struggles to escape constriction.\"));\n3738:             _swim_or_move_energy(mons);\n3739:             return true;\n3740:         }\n3741:     }\n3742: \n3743:     // We should have handled all cases of a monster attempting to attack instead of *just* move, so it should fine to simply silently\n3744:     // stand in place here.\n3745:     if (mons.cannot_move())\n3746:         return false;\n3747: \n3748:     ASSERT(!cell_is_runed(f)); // should be checked in mons_can_traverse\n3749: \n3750:     if (feat_is_closed_door(env.grid(f)))\n3751:     {\n3752:         if (mons_can_destroy_door(mons, f))",
    "method": "参数文本还原",
    "full_zh_display": "兽人逃脱了！",
    "example_state": "指定可见普通兽人作为名称参数文本；不声称已在游戏中触发该状态。",
    "formula": "mons.name(descrip)；need_possessive=true时apostrophise，再拼event片段；CJK-CJK空格归一见message.cc。",
    "parameter_assets": [
      {
        "path": "crawl-ref/source/dat/i18n/zh/source.txt",
        "line": 32556,
        "key": "orc",
        "zh": "兽人"
      },
      {
        "path": "crawl-ref/source/dat/i18n/zh/source.txt",
        "line": 1624,
        "key": "%s's",
        "zh": "%s的"
      }
    ],
    "remaining_runtime": "其他怪物名、不可见分支、状态可达性和布局需运行时。"
  },
  {
    "english": " struggles to escape constriction.",
    "zh_template": " 挣扎着想要挣脱束缚。",
    "source": {
      "path": "crawl-ref/source/mon-act.cc",
      "line": 3737
    },
    "parameter_expressions": [
      "mons",
      "T_(\" struggles to escape constriction.\")"
    ],
    "conditions_and_generation": "3719:         // XX is this actually reachable?\n3720:         fight_melee(&mons, &you);\n3721:         return true;\n3722:     }\n3723: \n3724:     // This includes the case where the monster attacks itself.\n3725:     if (monster* def = monster_at(f))\n3726:     {\n3727:         fight_melee(&mons, def);\n3728:         return true;\n3729:     }\n3730: \n3731:     if (mons.is_constricted() && !mons.cannot_move())\n3732:     {\n3733:         if (mons.attempt_escape())\n3734:             simple_monster_message(mons, T_(\" escapes!\"));\n3735:         else\n3736:         {\n3737:             simple_monster_message(mons, T_(\" struggles to escape constriction.\"));\n3738:             _swim_or_move_energy(mons);\n3739:             return true;\n3740:         }\n3741:     }\n3742: \n3743:     // We should have handled all cases of a monster attempting to attack instead of *just* move, so it should fine to simply silently\n3744:     // stand in place here.\n3745:     if (mons.cannot_move())\n3746:         return false;\n3747: \n3748:     ASSERT(!cell_is_runed(f)); // should be checked in mons_can_traverse\n3749: \n3750:     if (feat_is_closed_door(env.grid(f)))\n3751:     {\n3752:         if (mons_can_destroy_door(mons, f))\n3753:         {\n3754:             env.grid(f) = DNGN_FLOOR;\n3755:             set_terrain_changed(f);",
    "method": "参数文本还原",
    "full_zh_display": "兽人挣扎着想要挣脱束缚。",
    "example_state": "指定可见普通兽人作为名称参数文本；不声称已在游戏中触发该状态。",
    "formula": "mons.name(descrip)；need_possessive=true时apostrophise，再拼event片段；CJK-CJK空格归一见message.cc。",
    "parameter_assets": [
      {
        "path": "crawl-ref/source/dat/i18n/zh/source.txt",
        "line": 32556,
        "key": "orc",
        "zh": "兽人"
      },
      {
        "path": "crawl-ref/source/dat/i18n/zh/source.txt",
        "line": 1624,
        "key": "%s's",
        "zh": "%s的"
      }
    ],
    "remaining_runtime": "其他怪物名、不可见分支、状态可达性和布局需运行时。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/mon-act.cc:3850
crawl-ref/source/mon-act.cc",
crawl-ref/source/dat/i18n/zh/source.txt",
crawl-ref/source/dat/i18n/zh/source.txt",

中文全文
```text
挣扎着想要挣脱束缚。
```

trunk 完整英文
```text
struggles to escape constriction.

crawl-ref/source/mon-act.cc:3850
```cpp
3832:     if (f == you.pos())
3833:     {
3834:         // XX is this actually reachable?
3835:         mons_fight(&mons, &you);
3836:         return true;
3837:     }
3838:
3839:     // This includes the case where the monster attacks itself.
3840:     if (monster* def = monster_at(f))
3841:     {
3842:         if (mons_fight(&mons, def))
3843:             return true;
3844:     }
3845:
3846:     if (mons.is_constricted() && !mons.cannot_move())
3847:     {
3848:         if (!mons.attempt_escape())
3849:         {
3850:             simple_monster_message(mons, T_(" struggles to escape constriction."));
3851:             _swim_or_move_energy(mons);
3852:             return true;
3853:         }
3854:     }
3855:
3856:     // If a bound monster cannot perform an attack or movement towards what it
3857:     // *wants* to, first check if there's anything nearby it could hit instead
3858:     // of doing literally nothing.
3859:     if (mons.cannot_move())
3860:     {
3861:         // Don't consider making intelligent attacks while impaired.
3862:         if (mons_is_fleeing(mons) || mons_is_confused(mons))
3863:             return false;
3864:
3865:         int count = 0;
3866:         actor* targ = nullptr;
3867:         for (radius_iterator ri(mons.pos(), mons.reach_range(), C_SQUARE, LOS_NO_TRANS, true); ri; ++ri)
3868:         {
```
完整调用：
```cpp
simple_monster_message(mons, T_(" struggles to escape constriction."))
```
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": " struggles to escape constriction.",
    "zh_template": " 挣扎着想要挣脱束缚。",
    "source": {
      "path": "crawl-ref/source/mon-act.cc",
      "line": 3850
    },
    "parameter_expressions": [
      "mons",
      "T_(\" struggles to escape constriction.\")"
    ],
    "conditions_and_generation": "3832:     if (f == you.pos())\n3833:     {\n3834:         // XX is this actually reachable?\n3835:         mons_fight(&mons, &you);\n3836:         return true;\n3837:     }\n3838: \n3839:     // This includes the case where the monster attacks itself.\n3840:     if (monster* def = monster_at(f))\n3841:     {\n3842:         if (mons_fight(&mons, def))\n3843:             return true;\n3844:     }\n3845: \n3846:     if (mons.is_constricted() && !mons.cannot_move())\n3847:     {\n3848:         if (!mons.attempt_escape())\n3849:         {\n3850:             simple_monster_message(mons, T_(\" struggles to escape constriction.\"));\n3851:             _swim_or_move_energy(mons);\n3852:             return true;\n3853:         }\n3854:     }\n3855: \n3856:     // If a bound monster cannot perform an attack or movement towards what it\n3857:     // *wants* to, first check if there's anything nearby it could hit instead\n3858:     // of doing literally nothing.\n3859:     if (mons.cannot_move())\n3860:     {\n3861:         // Don't consider making intelligent attacks while impaired.\n3862:         if (mons_is_fleeing(mons) || mons_is_confused(mons))\n3863:             return false;\n3864: \n3865:         int count = 0;\n3866:         actor* targ = nullptr;\n3867:         for (radius_iterator ri(mons.pos(), mons.reach_range(), C_SQUARE, LOS_NO_TRANS, true); ri; ++ri)\n3868:         {",
    "method": "参数文本还原",
    "full_zh_display": "兽人挣扎着想要挣脱束缚。",
    "example_state": "指定可见普通兽人作为名称参数文本；不声称已在游戏中触发该状态。",
    "formula": "mons.name(descrip)；need_possessive=true时apostrophise，再拼event片段；CJK-CJK空格归一见message.cc。",
    "parameter_assets": [
      {
        "path": "crawl-ref/source/dat/i18n/zh/source.txt",
        "line": 35040,
        "key": "orc",
        "zh": "兽人"
      },
      {
        "path": "crawl-ref/source/dat/i18n/zh/source.txt",
        "line": 1669,
        "key": "%s's",
        "zh": "%s的"
      }
    ],
    "remaining_runtime": "其他怪物名、不可见分支、状态可达性和布局需运行时。"
  }
]
```

4. 独立语义判断与还原
stable 成功逃脱与挣扎分支均由 simple_monster_message 补主语；trunk 只保留挣扎调用，不能把缺成功键当漏译。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-1-02

1. 完整英文
```text
An intricate puzzlebox containing an unknowable prize. Transforms the wearer into
a riddle-loving sphinx. In this form, they are {{
    if you.race() == "Felid" then
        return "normally capable of wearing a cloak and barding (though your" ..
               " own diminutive size would prevent this)"
    else
        return "capable of wearing a cloak and barding"
    end
}}, and their melee attacks cause powerful winds to strike their foe which do
increased damage for every open space next to them. They are also masterful
enchanters, casting Hex spells much more easily and ignoring a portion of their
foe's Willpower.

Alas, their love of riddles is so compulsive that even the most hardened
adventurer will be unable to resist posing them to new foes they encounter, no
matter how unwise this may be.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:2895
crawl-ref/source/describe.cc:2907
crawl-ref/source/describe.cc:3461
crawl-ref/source/describe.cc:7279
crawl-ref/source/item-prop.cc",
crawl-ref/source/item-prop.cc",

中文全文
```text
一个内含未知奖品的精巧谜盒。将佩戴者变成一只爱好谜语的斯芬克斯。
在此形态下，佩戴者{{
    if you.race() == "Felid" then
        return "通常能够穿戴披风和马铠（尽管你自身的微小体型会阻止这一点）"
    else
        return "能够穿戴披风和马铠"
    end
}}，其近战攻击会引起强风打击敌人，相邻每多一格空地，伤害就越高。
佩戴者还是高超的惑控师，更容易施放诅咒系法术，
并忽略敌人一部分的意志力。

唉，佩戴者对谜语的热爱如此强烈，以至于即使是最坚毅的冒险者也无法
抗拒向遇到的新敌人提出谜语，无论这可能多么不明智。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "zh_body": "一个内含未知奖品的精巧谜盒。将佩戴者变成一只爱好谜语的斯芬克斯。\n在此形态下，佩戴者{{\n    if you.race() == \"Felid\" then\n        return \"通常能够穿戴披风和马铠（尽管你自身的微小体型会阻止这一点）\"\n    else\n        return \"能够穿戴披风和马铠\"\n    end\n}}，其近战攻击会引起强风打击敌人，相邻每多一格空地，伤害就越高。\n佩戴者还是高超的惑控师，更容易施放诅咒系法术，\n并忽略敌人一部分的意志力。\n\n唉，佩戴者对谜语的热爱如此强烈，以至于即使是最坚毅的冒险者也无法\n抗拒向遇到的新敌人提出谜语，无论这可能多么不明智。",
    "reason": "TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。",
    "parameter_source": "已鉴定unrand：get_unrand_name_en(item)的canonical NAME；其他物品：item.name(DESC_DBNAME,true,false,false)，ZH失败时临时EN生成fallback键。",
    "key_generation_evidence": [
      {
        "path": "crawl-ref/source/item-prop.cc",
        "line": 3238,
        "statement": "case TALISMAN_SPHINX:   return T_(\"riddle talisman\");",
        "snippet": "3228:     case TALISMAN_SPORE:    return T_(\"spore talisman\");\n3229:     case TALISMAN_MAW:      return T_(\"maw talisman\");\n3230:     case TALISMAN_SERPENT:  return T_(\"serpent talisman\");\n3231:     case TALISMAN_EEL:      return T_(\"eel talisman\");\n3232:     case TALISMAN_BLADE:    return T_(\"blade talisman\");\n3233:     case TALISMAN_WEREWOLF: return T_(\"lupine talisman\");\n3234:     case TALISMAN_FORTRESS: return T_(\"fortress talisman\");\n3235:     case TALISMAN_STATUE:   return T_(\"granite talisman\");\n3236:     case TALISMAN_HIVE:     return T_(\"hive talisman\");\n3237:     case TALISMAN_DRAGON:   return T_(\"dragon-coil talisman\");\n3238:     case TALISMAN_SPHINX:   return T_(\"riddle talisman\");\n3239:     case TALISMAN_VAMPIRE:  return T_(\"sanguine talisman\");\n3240:     case TALISMAN_DEATH:    return T_(\"talisman of death\");\n3241:     case TALISMAN_STORM:    return T_(\"storm talisman\");\n3242:     default:\n3243:         return \"buggy talisman\";\n3244:     }\n3245: }\n3246: \n3247: static const pair<talisman_type, int> _talisman_tiers[] =\n3248: {"
      }
    ]
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:3167
crawl-ref/source/describe.cc:3179
crawl-ref/source/describe.cc:3731
crawl-ref/source/describe.cc:7967
crawl-ref/source/item-prop.cc",
crawl-ref/source/item-prop.cc",

中文全文
```text
一个内含未知奖品的精巧谜盒。将佩戴者变成一只爱好谜语的斯芬克斯。
在此形态下，佩戴者{{
    if you.race() == "Felid" then
        return "通常能够穿戴披风和马铠（尽管你自身的微小体型会阻止这一点）"
    else
        return "能够穿戴披风和马铠"
    end
}}，其近战攻击会引起强风打击敌人，相邻每多一格空地，伤害就越高。
佩戴者还是高超的惑控师，更容易施放妖术系法术，
并忽略敌人一部分的意志力。

唉，佩戴者对谜语的热爱如此强烈，以至于即使是最坚毅的冒险者也无法
抗拒向遇到的新敌人提出谜语，无论这可能多么不明智。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "zh_body": "一个内含未知奖品的精巧谜盒。将佩戴者变成一只爱好谜语的斯芬克斯。\n在此形态下，佩戴者{{\n    if you.race() == \"Felid\" then\n        return \"通常能够穿戴披风和马铠（尽管你自身的微小体型会阻止这一点）\"\n    else\n        return \"能够穿戴披风和马铠\"\n    end\n}}，其近战攻击会引起强风打击敌人，相邻每多一格空地，伤害就越高。\n佩戴者还是高超的惑控师，更容易施放妖术系法术，\n并忽略敌人一部分的意志力。\n\n唉，佩戴者对谜语的热爱如此强烈，以至于即使是最坚毅的冒险者也无法\n抗拒向遇到的新敌人提出谜语，无论这可能多么不明智。",
    "reason": "TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。",
    "parameter_source": "已鉴定unrand：get_unrand_name_en(item)的canonical NAME；其他物品：item.name(DESC_DBNAME,true,false,false)，ZH失败时临时EN生成fallback键。",
    "key_generation_evidence": [
      {
        "path": "crawl-ref/source/item-prop.cc",
        "line": 3316,
        "statement": "case TALISMAN_SPHINX:   return T_(\"riddle talisman\");",
        "snippet": "3306:     case TALISMAN_JADE:     return T_(\"jade talisman\");\n3307:     case TALISMAN_MAW:      return T_(\"maw talisman\");\n3308:     case TALISMAN_SERPENT:  return T_(\"serpent talisman\");\n3309:     case TALISMAN_EEL:      return T_(\"eel talisman\");\n3310:     case TALISMAN_BLADE:    return T_(\"blade talisman\");\n3311:     case TALISMAN_WEREWOLF: return T_(\"lupine talisman\");\n3312:     case TALISMAN_FORTRESS: return T_(\"fortress talisman\");\n3313:     case TALISMAN_STATUE:   return T_(\"granite talisman\");\n3314:     case TALISMAN_HIVE:     return T_(\"hive talisman\");\n3315:     case TALISMAN_DRAGON:   return T_(\"dragon-coil talisman\");\n3316:     case TALISMAN_SPHINX:   return T_(\"riddle talisman\");\n3317:     case TALISMAN_VAMPIRE:  return T_(\"sanguine talisman\");\n3318:     case TALISMAN_DEATH:    return T_(\"talisman of death\");\n3319:     case TALISMAN_STORM:    return T_(\"storm talisman\");\n3320:     default:\n3321:         return \"buggy talisman\";\n3322:     }\n3323: }\n3324: \n3325: static const pair<talisman_type, int> _talisman_tiers[] =\n3326: {"
      }
    ]
  }
]
```

4. 独立语义判断与还原
Felid 条件与披风马铠限制、妖术成功及忽略部分意志完整；近战风伤按敌人附近空地计算，中文未明确这一对象，建议补清。stable 诅咒系应为妖术系。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：objective_error

{"type": "terminology", "line": "stable", "english": "An intricate puzzlebox containing an unknowable prize. Transforms the wearer into\na riddle-loving sphinx. In this form, they are {{\n    if you.race() == \"Felid\" then\n        return \"normally capable of wearing a cloak and barding (though your\" ..\n               \" own diminutive size would prevent this)\"\n    else\n        return \"capable of wearing a cloak and barding\"\n    end\n}}, and their melee attacks cause powerful winds to strike their foe which do\nincreased damage for every open space next to them. They are also masterful\nenchanters, casting Hex spells much more easily and ignoring a portion of their\nfoe's Willpower.\n\nAlas, their love of riddles is so compulsive that even the most hardened\nadventurer will be unable to resist posing them to new foes they encounter, no\nmatter how unwise this may be.", "current_full_zh": "一个内含未知奖品的精巧谜盒。将佩戴者变成一只爱好谜语的斯芬克斯。\n在此形态下，佩戴者{{\n    if you.race() == \"Felid\" then\n        return \"通常能够穿戴披风和马铠（尽管你自身的微小体型会阻止这一点）\"\n    else\n        return \"能够穿戴披风和马铠\"\n    end\n}}，其近战攻击会引起强风打击敌人，相邻每多一格空地，伤害就越高。\n佩戴者还是高超的惑控师，更容易施放诅咒系法术，\n并忽略敌人一部分的意志力。\n\n唉，佩戴者对谜语的热爱如此强烈，以至于即使是最坚毅的冒险者也无法\n抗拒向遇到的新敌人提出谜语，无论这可能多么不明智。", "problem": "Hex spells 是控制附魔学派法术，stable 写成诅咒系，与当前妖术系身份不一致；trunk 已修正。", "suggested_zh": "将本段诅咒系法术改为妖术系法术。", "evidence": "crawl-ref/source/describe.cc:2895; crawl-ref/source/describe.cc:2907; crawl-ref/source/describe.cc:3461; crawl-ref/source/describe.cc:7279; crawl-ref/source/item-prop.cc\",", "defect_points": 1}

{"type": "clarity", "line": "both", "english": "An intricate puzzlebox containing an unknowable prize. Transforms the wearer into\na riddle-loving sphinx. In this form, they are {{\n    if you.race() == \"Felid\" then\n        return \"normally capable of wearing a cloak and barding (though your\" ..\n               \" own diminutive size would prevent this)\"\n    else\n        return \"capable of wearing a cloak and barding\"\n    end\n}}, and their melee attacks cause powerful winds to strike their foe which do\nincreased damage for every open space next to them. They are also masterful\nenchanters, casting Hex spells much more easily and ignoring a portion of their\nfoe's Willpower.\n\nAlas, their love of riddles is so compulsive that even the most hardened\nadventurer will be unable to resist posing them to new foes they encounter, no\nmatter how unwise this may be.", "current_full_zh": "一个内含未知奖品的精巧谜盒。将佩戴者变成一只爱好谜语的斯芬克斯。\n在此形态下，佩戴者{{\n    if you.race() == \"Felid\" then\n        return \"通常能够穿戴披风和马铠（尽管你自身的微小体型会阻止这一点）\"\n    else\n        return \"能够穿戴披风和马铠\"\n    end\n}}，其近战攻击会引起强风打击敌人，相邻每多一格空地，伤害就越高。\n佩戴者还是高超的惑控师，更容易施放诅咒系法术，\n并忽略敌人一部分的意志力。\n\n唉，佩戴者对谜语的热爱如此强烈，以至于即使是最坚毅的冒险者也无法\n抗拒向遇到的新敌人提出谜语，无论这可能多么不明智。", "problem": "相邻每多一格空地未明确按敌人周围计算，容易读作佩戴者周围。", "suggested_zh": "其近战攻击会唤起强风打击敌人；敌人周围每多一格空地，伤害就越高。", "evidence": "stable melee-attack.cc:997-1000，airstrike_space_around(defender->pos(),true)。", "defect_points": 0}


## R4-1-01

1. 完整英文
```text
A double-ended whip made from the cured hides of black mambas, and enchanted
with toxins ranging from ordinary venoms to asphyxiating curare.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:2869
crawl-ref/source/art-data.txt",

中文全文
```text
一种由黑曼巴蛇的皮制成的双端鞭，附有从普通的毒液到令人窒息的箭毒碱毒素。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一种由黑曼巴蛇的皮制成的双端鞭，附有从普通的毒液到令人窒息的箭毒碱毒素。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:3141
crawl-ref/source/art-data.txt",

中文全文
```text
一种由黑曼巴蛇的皮制成的双端鞭，附有从普通的毒液到令人窒息的箭毒碱毒素。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一种由黑曼巴蛇的皮制成的双端鞭，附有从普通的毒液到令人窒息的箭毒碱毒素。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
双端黑曼巴皮鞭、普通毒液至窒息箭毒的范围完整；皮革加工性质可由制品语境理解，不另判机械漏译。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-7-03

1. 完整英文
```text
%s searing ray is interrupted.
```

2–3. stable 消费者与参数证据

crawl-ref/source/mon-ench.cc:1993
crawl-ref/source/mon-ench.cc",

中文全文
```text
%s灼热射线被打断了。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "%s searing ray is interrupted.",
    "zh_template": "%s灼热射线被打断了。",
    "source": {
      "path": "crawl-ref/source/mon-ench.cc",
      "line": 1993
    },
    "parameter_expressions": [
      "T_(\"%s searing ray is interrupted.\")",
      "name(DESC_ITS).c_str()"
    ],
    "conditions_and_generation": "1975:         break;\n1976: \n1977:     case ENCH_ANGUISH:\n1978:         if (decay_enchantment(en))\n1979:         {\n1980:             simple_monster_message(*this,\n1981:                 T_(\" is no longer haunted by guilt.\"));\n1982:         }\n1983:         break;\n1984: \n1985:     case ENCH_CHANNEL_SEARING_RAY:\n1986:         // If we've gotten incapacitated since we started, cancel the spell\n1987:         if (is_silenced() || cannot_act() || confused() || asleep()\n1988:             || has_ench(ENCH_FEAR))\n1989:         {\n1990:             del_ench(en, true, false);\n1991:             if (you.can_see(*this))\n1992:             {\n1993:                 mprf(T_(\"%s searing ray is interrupted.\"),\n1994:                      name(DESC_ITS).c_str());\n1995:             }\n1996:         }\n1997:         break;\n1998: \n1999:     case ENCH_BOUND:\n2000:         // Remove Yred binding as soon as we're not in the effect area\n2001:         if (props.exists(YRED_SHACKLES_KEY)\n2002:             && (!is_blasphemy(pos()) || !is_blasphemy(you.pos())\n2003:                 || !you.duration[DUR_FATHOMLESS_SHACKLES]))\n2004:         {\n2005:             props.erase(YRED_SHACKLES_KEY);\n2006:             del_ench(en, true, true);\n2007:         }\n2008:         else\n2009:             decay_enchantment(en);\n2010:         break;\n2011: \n2012:     case ENCH_SOUL_RIPE:",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "name(DESC_ITS).c_str()",
        "examples": []
      }
    ]
  }
]
```

2–3. trunk 消费者与参数证据



中文全文
```text
None
```

trunk 完整英文
```text
None
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[]
```

4. 独立语义判断与还原
stable name(DESC_ITS) 提供兽人的，整句兽人的灼热射线被打断了。；trunk 无对应调用，不把历史键不存在直接报漏译。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-3-06

1. 完整英文
```text
A mass of lashing vines and tentacles growing out of the husk of a dead star.
Space itself runs through the xylem and phloem of its branches, which appear to
be in many places at once.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:7279
crawl-ref/source/describe.cc:7270
crawl-ref/source/dat/mons/starflower.yaml",

中文全文
```text
从死星的外壳中长出的一团藤蔓和触须。
空间贯通着它的分支的木质部和韧皮部，它们似乎同时存在于许多地方。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "从死星的外壳中长出的一团藤蔓和触须。\n空间贯通着它的分支的木质部和韧皮部，它们似乎同时存在于许多地方。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:7967
crawl-ref/source/describe.cc:7958
crawl-ref/source/dat/mons/starflower.yaml",

中文全文
```text
从死星的外壳中长出的一团藤蔓和触须。
空间贯通着它的分支的木质部和韧皮部，它们似乎同时存在于许多地方。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "从死星的外壳中长出的一团藤蔓和触须。\n空间贯通着它的分支的木质部和韧皮部，它们似乎同时存在于许多地方。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
死星外壳、木质部韧皮部与同时多地存在的意象完整，但 lashing 挥舞动作遗漏。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：objective_error

{"type": "omission", "line": "both", "english": "A mass of lashing vines and tentacles growing out of the husk of a dead star.\nSpace itself runs through the xylem and phloem of its branches, which appear to\nbe in many places at once.", "current_full_zh": "从死星的外壳中长出的一团藤蔓和触须。\n空间贯通着它的分支的木质部和韧皮部，它们似乎同时存在于许多地方。", "problem": "lashing 描述藤蔓和触须挥舞抽动的动作，现译省略这一动态形象。", "suggested_zh": "从死星外壳中长出的一团挥舞不休的藤蔓和触须。\n空间本身流经其枝条的木质部和韧皮部，这些枝条似乎同时存在于多处。", "evidence": "crawl-ref/source/describe.cc:7279; crawl-ref/source/describe.cc:7270; crawl-ref/source/dat/mons/starflower.yaml\",", "defect_points": 1}


## R4-3-02

1. 完整英文
```text
A half-mortal, half-demonic creature, oozing with dark energies. It twists
space around itself, and can corrupt weapons, armour and even the very flesh of
its opponents.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:7279
crawl-ref/source/describe.cc:7270
crawl-ref/source/dat/mons/demonspawn-corrupter.yaml",

中文全文
```text
一个半人半魔的生物，散发着黑暗能量。
他扭曲了自身周围的空间，可以腐蚀武器、盔甲甚至对方的血肉。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一个半人半魔的生物，散发着黑暗能量。\n他扭曲了自身周围的空间，可以腐蚀武器、盔甲甚至对方的血肉。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:7967
crawl-ref/source/describe.cc:7958
crawl-ref/source/dat/mons/demonspawn-corrupter.yaml",

中文全文
```text
一个半人半魔的生物，散发着黑暗能量。
他扭曲了自身周围的空间，可以腐蚀武器、盔甲甚至对方的血肉。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一个半人半魔的生物，散发着黑暗能量。\n他扭曲了自身周围的空间，可以腐蚀武器、盔甲甚至对方的血肉。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
黑暗能量、扭曲自身周围空间及武器护甲血肉三类腐化对象完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-5-06

1. 完整英文
```text
<tiles>A small symbol on an item tile signifies that there is at least one other
item in the same heap that you may want to check out.</tiles>
<console>If two or more items are on a single square, then the square will be
highlighted, and the symbol for the item on the top of the heap will be shown.
</console>
```

2–3. stable 消费者与参数证据

crawl-ref/source/hints.cc:1235
crawl-ref/source/hints.cc:401
crawl-ref/source/hints.cc:483
crawl-ref/source/hints.cc:2884
crawl-ref/source/hints.cc",

中文全文
```text
<tiles>物品格子上的一个小符号表示同一堆中至少还有一个你可能想
查看的其他物品。</tiles>
<console>如果两个或更多物品在一个格子上，则该格子会被高亮显示，
堆顶物品的符号会显示在格子上。</console>
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "<tiles>物品格子上的一个小符号表示同一堆中至少还有一个你可能想\n查看的其他物品。</tiles>\n<console>如果两个或更多物品在一个格子上，则该格子会被高亮显示，\n堆顶物品的符号会显示在格子上。</console>",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/hints.cc:1158
crawl-ref/source/hints.cc:402
crawl-ref/source/hints.cc:484
crawl-ref/source/hints.cc:2386
crawl-ref/source/hints.cc",

中文全文
```text
<tiles>物品格子上的一个小符号表示同一堆中至少还有一个你可能想
查看的其他物品。</tiles>
<console>如果两个或更多物品在一个格子上，则该格子会被高亮显示，
堆顶物品的符号会显示在格子上。</console>
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "<tiles>物品格子上的一个小符号表示同一堆中至少还有一个你可能想\n查看的其他物品。</tiles>\n<console>如果两个或更多物品在一个格子上，则该格子会被高亮显示，\n堆顶物品的符号会显示在格子上。</console>",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
图形堆叠标志与控制台高亮、显示堆顶图符分别完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-3-10

1. 完整英文
```text
A large even-toed ungulate. Like human beings, it is omnivorous, intelligent,
and nearly hairless.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:7279
crawl-ref/source/describe.cc:7270
crawl-ref/source/dat/mons/hog.yaml",

中文全文
```text
一头大型偶蹄类动物。像人类一样，杂食、聪明，而且几乎不长毛。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一头大型偶蹄类动物。像人类一样，杂食、聪明，而且几乎不长毛。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:7967
crawl-ref/source/describe.cc:7958
crawl-ref/source/dat/mons/hog.yaml",

中文全文
```text
一头大型偶蹄类动物。像人类一样，杂食、聪明，而且几乎不长毛。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一头大型偶蹄类动物。像人类一样，杂食、聪明，而且几乎不长毛。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
大型偶蹄动物的杂食、聪明、少毛三特性完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-7-01

1. 完整英文
```text
The solar flare engulfs %s%s.

 but does no damage
```

2–3. stable 消费者与参数证据

crawl-ref/source/mon-abil.cc:1577
crawl-ref/source/mon-abil.cc",
crawl-ref/source/mon-abil.cc",

中文全文
```text
太阳耀斑吞没了%s%s。

但没有造成伤害
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "The solar flare engulfs %s%s.",
    "zh_template": "太阳耀斑吞没了%s%s。",
    "source": {
      "path": "crawl-ref/source/mon-abil.cc",
      "line": 1577
    },
    "parameter_expressions": [
      "T_(\"The solar flare engulfs %s%s.\")",
      "mon->name(DESC_THE).c_str()",
      "damage_done ? \"\" : T_(\" but does no damage\")"
    ],
    "conditions_and_generation": "1559:             if (could_harm_enemy(&you, mon) && !mon->is_firewood() && you.see_cell_no_trans(mon->pos()))\n1560:                 targs.push_back(mon);\n1561: \n1562:     if (targs.empty())\n1563:         return;\n1564: \n1565:     simple_monster_message(*ember, T_(\" blazes with a fierce heat.\"), false, MSGCH_FRIEND_SPELL);\n1566: \n1567:     bolt beam;\n1568:     beam.flavour = BEAM_FIRE;\n1569:     dice_def dmg = get_form()->get_special_damage();\n1570:     for (monster* mon : targs)\n1571:     {\n1572:         if (!mon->alive())\n1573:             continue;\n1574: \n1575:         flash_tile(mon->pos(), RED, 0);\n1576:         const int damage_done = mons_adjust_flavoured(mon, beam, mon->apply_ac(dmg.roll()));\n1577:         mprf(T_(\"The solar flare engulfs %s%s.\"), mon->name(DESC_THE).c_str(),\n1578:                 damage_done ? \"\" : T_(\" but does no damage\"));\n1579:         mon->hurt(ember, damage_done, BEAM_FIRE);\n1580:     }\n1581: \n1582:     animation_delay(10, true);\n1583: \n1584:     ember->hurt(ember, random_range(7, 10));\n1585:     ember->del_ench(ENCH_SPELL_CHARGED);\n1586: \n1587:     you.did_trigger(DID_SOLAR_EMBER);\n1588: }\n1589: \n1590: static bool _make_tesseract_spawn(bool near_player, bool outside_vault = false)\n1591: {\n1592:     mgen_data mg(one_chance_in(6) ? MONS_ORB_GUARDIAN : WANDERING_MONSTER);\n1593:     mg.place = level_id::current();\n1594:     mg.place.depth = 7;\n1595:     mg.flags |= MG_FORBID_BANDS;\n1596:     mg.extra_flags |= (MF_HARD_RESET | MF_TESSERACT_SPAWN);",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "mon->name(DESC_THE).c_str()",
        "examples": []
      },
      {
        "expression": "damage_done ? \"\" : T_(\" but does no damage\")",
        "examples": [
          [
            "",
            "按实参条件分支选择；完整条件：damage_done ? \"\" : T_(\" but does no damage\")"
          ],
          [
            "但没有造成伤害",
            "按实参条件分支选择；完整条件：damage_done ? \"\" : T_(\" but does no damage\")"
          ]
        ]
      }
    ]
  },
  {
    "english": " but does no damage",
    "zh_template": "但没有造成伤害",
    "source": {
      "path": "crawl-ref/source/mon-abil.cc",
      "line": 1577
    },
    "parameter_expressions": [
      "T_(\"The solar flare engulfs %s%s.\")",
      "mon->name(DESC_THE).c_str()",
      "damage_done ? \"\" : T_(\" but does no damage\")"
    ],
    "conditions_and_generation": "1559:             if (could_harm_enemy(&you, mon) && !mon->is_firewood() && you.see_cell_no_trans(mon->pos()))\n1560:                 targs.push_back(mon);\n1561: \n1562:     if (targs.empty())\n1563:         return;\n1564: \n1565:     simple_monster_message(*ember, T_(\" blazes with a fierce heat.\"), false, MSGCH_FRIEND_SPELL);\n1566: \n1567:     bolt beam;\n1568:     beam.flavour = BEAM_FIRE;\n1569:     dice_def dmg = get_form()->get_special_damage();\n1570:     for (monster* mon : targs)\n1571:     {\n1572:         if (!mon->alive())\n1573:             continue;\n1574: \n1575:         flash_tile(mon->pos(), RED, 0);\n1576:         const int damage_done = mons_adjust_flavoured(mon, beam, mon->apply_ac(dmg.roll()));\n1577:         mprf(T_(\"The solar flare engulfs %s%s.\"), mon->name(DESC_THE).c_str(),\n1578:                 damage_done ? \"\" : T_(\" but does no damage\"));\n1579:         mon->hurt(ember, damage_done, BEAM_FIRE);\n1580:     }\n1581: \n1582:     animation_delay(10, true);\n1583: \n1584:     ember->hurt(ember, random_range(7, 10));\n1585:     ember->del_ench(ENCH_SPELL_CHARGED);\n1586: \n1587:     you.did_trigger(DID_SOLAR_EMBER);\n1588: }\n1589: \n1590: static bool _make_tesseract_spawn(bool near_player, bool outside_vault = false)\n1591: {\n1592:     mgen_data mg(one_chance_in(6) ? MONS_ORB_GUARDIAN : WANDERING_MONSTER);\n1593:     mg.place = level_id::current();\n1594:     mg.place.depth = 7;\n1595:     mg.flags |= MG_FORBID_BANDS;\n1596:     mg.extra_flags |= (MF_HARD_RESET | MF_TESSERACT_SPAWN);",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/mon-abil.cc:1538
crawl-ref/source/mon-abil.cc",
crawl-ref/source/mon-abil.cc",

中文全文
```text
太阳耀斑吞没了%s%s。

但没有造成伤害
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "The solar flare engulfs %s%s.",
    "zh_template": "太阳耀斑吞没了%s%s。",
    "source": {
      "path": "crawl-ref/source/mon-abil.cc",
      "line": 1538
    },
    "parameter_expressions": [
      "T_(\"The solar flare engulfs %s%s.\")",
      "mon->name(DESC_THE).c_str()",
      "damage_done ? \"\" : T_(\" but does no damage\")"
    ],
    "conditions_and_generation": "1520:             if (could_harm_enemy(&you, mon) && !mon->is_firewood() && you.see_cell_no_trans(mon->pos()))\n1521:                 targs.push_back(mon);\n1522: \n1523:     if (targs.empty())\n1524:         return;\n1525: \n1526:     simple_monster_message(*ember, T_(\" blazes with a fierce heat.\"), false, MSGCH_FRIEND_SPELL);\n1527: \n1528:     bolt beam;\n1529:     beam.flavour = BEAM_FIRE;\n1530:     dice_def dmg = get_form()->get_special_damage();\n1531:     for (monster* mon : targs)\n1532:     {\n1533:         if (!mon->alive())\n1534:             continue;\n1535: \n1536:         flash_tile(mon->pos(), RED, 0);\n1537:         const int damage_done = mons_adjust_flavoured(mon, beam, mon->apply_ac(dmg.roll()));\n1538:         mprf(T_(\"The solar flare engulfs %s%s.\"), mon->name(DESC_THE).c_str(),\n1539:                 damage_done ? \"\" : T_(\" but does no damage\"));\n1540:         mon->hurt(&you, damage_done, BEAM_FIRE);\n1541:     }\n1542: \n1543:     animation_delay(10, true);\n1544: \n1545:     ember->hurt(ember, random_range(7, 10));\n1546:     ember->del_ench(ENCH_SPELL_CHARGED);\n1547: \n1548:     you.did_trigger(DID_SOLAR_EMBER);\n1549: }\n1550: \n1551: static bool _make_tesseract_spawn(bool near_player, bool outside_vault = false)\n1552: {\n1553:     mgen_data mg(one_chance_in(6) ? MONS_ORB_GUARDIAN : WANDERING_MONSTER);\n1554:     mg.place = level_id::current();\n1555:     mg.place.depth = 7;\n1556:     mg.flags |= MG_FORBID_BANDS;\n1557:     mg.extra_flags |= (MF_HARD_RESET | MF_TESSERACT_SPAWN);",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "mon->name(DESC_THE).c_str()",
        "examples": []
      },
      {
        "expression": "damage_done ? \"\" : T_(\" but does no damage\")",
        "examples": [
          [
            "",
            "按实参条件分支选择；完整条件：damage_done ? \"\" : T_(\" but does no damage\")"
          ],
          [
            "但没有造成伤害",
            "按实参条件分支选择；完整条件：damage_done ? \"\" : T_(\" but does no damage\")"
          ]
        ]
      }
    ]
  },
  {
    "english": " but does no damage",
    "zh_template": "但没有造成伤害",
    "source": {
      "path": "crawl-ref/source/mon-abil.cc",
      "line": 1538
    },
    "parameter_expressions": [
      "T_(\"The solar flare engulfs %s%s.\")",
      "mon->name(DESC_THE).c_str()",
      "damage_done ? \"\" : T_(\" but does no damage\")"
    ],
    "conditions_and_generation": "1520:             if (could_harm_enemy(&you, mon) && !mon->is_firewood() && you.see_cell_no_trans(mon->pos()))\n1521:                 targs.push_back(mon);\n1522: \n1523:     if (targs.empty())\n1524:         return;\n1525: \n1526:     simple_monster_message(*ember, T_(\" blazes with a fierce heat.\"), false, MSGCH_FRIEND_SPELL);\n1527: \n1528:     bolt beam;\n1529:     beam.flavour = BEAM_FIRE;\n1530:     dice_def dmg = get_form()->get_special_damage();\n1531:     for (monster* mon : targs)\n1532:     {\n1533:         if (!mon->alive())\n1534:             continue;\n1535: \n1536:         flash_tile(mon->pos(), RED, 0);\n1537:         const int damage_done = mons_adjust_flavoured(mon, beam, mon->apply_ac(dmg.roll()));\n1538:         mprf(T_(\"The solar flare engulfs %s%s.\"), mon->name(DESC_THE).c_str(),\n1539:                 damage_done ? \"\" : T_(\" but does no damage\"));\n1540:         mon->hurt(&you, damage_done, BEAM_FIRE);\n1541:     }\n1542: \n1543:     animation_delay(10, true);\n1544: \n1545:     ember->hurt(ember, random_range(7, 10));\n1546:     ember->del_ench(ENCH_SPELL_CHARGED);\n1547: \n1548:     you.did_trigger(DID_SOLAR_EMBER);\n1549: }\n1550: \n1551: static bool _make_tesseract_spawn(bool near_player, bool outside_vault = false)\n1552: {\n1553:     mgen_data mg(one_chance_in(6) ? MONS_ORB_GUARDIAN : WANDERING_MONSTER);\n1554:     mg.place = level_id::current();\n1555:     mg.place.depth = 7;\n1556:     mg.flags |= MG_FORBID_BANDS;\n1557:     mg.extra_flags |= (MF_HARD_RESET | MF_TESSERACT_SPAWN);",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。"
  }
]
```

4. 独立语义判断与还原
damage_done 分支：太阳耀斑吞没了兽人。/太阳耀斑吞没了兽人但没有造成伤害。；可加逗号更流畅但现句语法成立，不因偏好判错。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-3-03

1. 完整英文
```text
A churning mass of flowing blood that throbs to the beat of an absent heart.

Does it wish to bury itself in your arteries because it recognises, on some
primordial level, that this is where it belongs? Alas, all it is capable of in
this fleeing moment of sentience is violence.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:7279
crawl-ref/source/describe.cc:7270
crawl-ref/source/dat/mons/erythrospite.yaml",

中文全文
```text
一团随着缺席心脏的搏动而脉动的奔流之血。

它想将自己埋入你的动脉，是因为它在某个原始层面上认识到这是它
所属的地方吗？唉，在这短暂的感知时刻，它所能做的只有暴力。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一团随着缺席心脏的搏动而脉动的奔流之血。\n\n它想将自己埋入你的动脉，是因为它在某个原始层面上认识到这是它\n所属的地方吗？唉，在这短暂的感知时刻，它所能做的只有暴力。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:7967
crawl-ref/source/describe.cc:7958
crawl-ref/source/dat/mons/erythrospite.yaml",

中文全文
```text
一团随着缺席心脏的搏动而脉动的奔流之血。

它想将自己埋入你的动脉，是因为它在某个原始层面上认识到这是它
所属的地方吗？唉，在这短暂的感知时刻，它所能做的只有暴力。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一团随着缺席心脏的搏动而脉动的奔流之血。\n\n它想将自己埋入你的动脉，是因为它在某个原始层面上认识到这是它\n所属的地方吗？唉，在这短暂的感知时刻，它所能做的只有暴力。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
缺席心脏的悖论意象仍在，但缺席心脏及感知时刻偏生硬，作为文学可读性建议。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：readability

{"type": "wording", "line": "both", "english": "A churning mass of flowing blood that throbs to the beat of an absent heart.\n\nDoes it wish to bury itself in your arteries because it recognises, on some\nprimordial level, that this is where it belongs? Alas, all it is capable of in\nthis fleeing moment of sentience is violence.", "current_full_zh": "一团随着缺席心脏的搏动而脉动的奔流之血。\n\n它想将自己埋入你的动脉，是因为它在某个原始层面上认识到这是它\n所属的地方吗？唉，在这短暂的感知时刻，它所能做的只有暴力。", "problem": "缺席心脏和感知时刻的汉语搭配生硬，可保留不存在心脏却有心跳的悖论。", "suggested_zh": "一团翻涌的鲜血，随着一颗不存在的心脏的节律搏动。\n\n它想钻进你的动脉，是否因为在某种原始本能中认出了自己的归宿？可惜，在这转瞬即逝的意识中，它只懂得施暴。", "evidence": "crawl-ref/source/describe.cc:7279; crawl-ref/source/describe.cc:7270; crawl-ref/source/dat/mons/erythrospite.yaml\",", "defect_points": 0}


## R4-7-02

1. 完整英文
```text
gasps for air!
```

2–3. stable 消费者与参数证据

crawl-ref/source/mon-ench.cc:1893
crawl-ref/source/mon-ench.cc",

中文全文
```text
拼命喘气！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": " gasps for air!",
    "zh_template": "拼命喘气！",
    "source": {
      "path": "crawl-ref/source/mon-ench.cc",
      "line": 1893
    },
    "parameter_expressions": [
      "*this",
      "T_(\" gasps for air!\")"
    ],
    "conditions_and_generation": "1875:                     pronoun(PRONOUN_POSSESSIVE).c_str());\n1876:         }\n1877:         break;\n1878: \n1879:     case ENCH_INJURY_BOND:\n1880:         // It's hard to absorb someone else's injuries when you're dead\n1881:         if (!me.agent() || !me.agent()->alive()\n1882:             || me.agent()->mid == MID_ANON_FRIEND)\n1883:         {\n1884:             del_ench(ENCH_INJURY_BOND, true, false);\n1885:         }\n1886:         else\n1887:             decay_enchantment(en);\n1888:         break;\n1889: \n1890:     case ENCH_FLOODED:\n1891:         if (!decay_enchantment(en))\n1892:         {\n1893:             simple_monster_message(*this,\n1894:                 T_(\" gasps for air!\"));\n1895:             hurt(me.agent(), roll_dice(3, 2));\n1896:         }\n1897:         break;\n1898: \n1899:     case ENCH_FLAYED:\n1900:     {\n1901:         bool near_ghost = false;\n1902:         for (monster_iterator mi; mi; ++mi)\n1903:         {\n1904:             if (mi->type == MONS_FLAYED_GHOST && !mons_aligned(this, *mi)\n1905:                 && see_cell(mi->pos()))\n1906:             {\n1907:                 near_ghost = true;\n1908:                 break;\n1909:             }\n1910:         }\n1911:         if (!near_ghost)\n1912:             decay_enchantment(en);",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "隐式怪物名称/所有格前缀与原模板或受类型限制的实例需要具体运行时状态。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/mon-ench.cc:1924
crawl-ref/source/mon-ench.cc",

中文全文
```text
拼命喘气！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": " gasps for air!",
    "zh_template": "拼命喘气！",
    "source": {
      "path": "crawl-ref/source/mon-ench.cc",
      "line": 1924
    },
    "parameter_expressions": [
      "*this",
      "T_(\" gasps for air!\")"
    ],
    "conditions_and_generation": "1906:                     pronoun(PRONOUN_POSSESSIVE).c_str());\n1907:         }\n1908:         break;\n1909: \n1910:     case ENCH_INJURY_BOND:\n1911:         // It's hard to absorb someone else's injuries when you're dead\n1912:         if (!me.agent() || !me.agent()->alive()\n1913:             || me.agent()->mid == MID_ANON_FRIEND)\n1914:         {\n1915:             del_ench(ENCH_INJURY_BOND, true, false);\n1916:         }\n1917:         else\n1918:             decay_enchantment(en);\n1919:         break;\n1920: \n1921:     case ENCH_FLOODED:\n1922:         if (!decay_enchantment(en))\n1923:         {\n1924:             simple_monster_message(*this,\n1925:                 T_(\" gasps for air!\"));\n1926:             hurt(me.agent(), roll_dice(3, 2));\n1927:         }\n1928:         break;\n1929: \n1930:     case ENCH_FLAYED:\n1931:     {\n1932:         bool near_ghost = false;\n1933:         for (monster_iterator mi; mi; ++mi)\n1934:         {\n1935:             if (mi->type == MONS_FLAYED_GHOST && !mons_aligned(this, *mi)\n1936:                 && see_cell(mi->pos()))\n1937:             {\n1938:                 near_ghost = true;\n1939:                 break;\n1940:             }\n1941:         }\n1942:         if (!near_ghost)\n1943:             decay_enchantment(en);",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "隐式怪物名称/所有格前缀与原模板或受类型限制的实例需要具体运行时状态。"
  }
]
```

4. 独立语义判断与还原
simple_monster_message 补怪名，例兽人拼命喘气！，未漏主语。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-2-10

1. 完整英文
```text
Wisps of shadow whirl around you...
```

2–3. stable 消费者与参数证据

crawl-ref/source/spl-summoning.cc:1204
crawl-ref/source/spl-summoning.cc",

中文全文
```text
暗影的细丝在你周围旋转……
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "Wisps of shadow whirl around you...",
    "zh_template": "暗影的细丝在你周围旋转……",
    "source": {
      "path": "crawl-ref/source/spl-summoning.cc",
      "line": 1204
    },
    "parameter_expressions": [
      "T_(\"Wisps of shadow whirl around you...\")"
    ],
    "conditions_and_generation": "1186:         canned_msg(MSG_NOTHING_HAPPENS);\n1187:     return spret::success;\n1188: }\n1189: \n1190: spret summon_shadow_creatures()\n1191: {\n1192:     // A small number of the monsters summoned by shadow creatures can fly,\n1193:     // so it is technically still usable above water or lava\n1194:     if (!you_can_see_habitable_spot_near(HT_FLYER, 2))\n1195:     {\n1196:         canned_msg(MSG_NO_AVAILABLE_SPACE);\n1197:         return spret::abort;\n1198:     }\n1199: \n1200:     // Hard to predict what resistances might come from this.\n1201:     if (stop_summoning_prompt())\n1202:         return spret::abort;\n1203: \n1204:     mpr(T_(\"Wisps of shadow whirl around you...\"));\n1205: \n1206:     int num = roll_dice(2, 2);\n1207:     int num_created = 0;\n1208: \n1209:     for (int i = 0; i < num; ++i)\n1210:     {\n1211:         if (monster *mons = create_monster(\n1212:             mgen_data(RANDOM_COMPATIBLE_MONSTER, BEH_FRIENDLY, you.pos(),\n1213:                       MHITYOU, MG_FORCE_BEH | MG_AUTOFOE | MG_NO_OOD)\n1214:                       // This duration is only used for band members.\n1215:                       .set_summoned(&you, MON_SUMM_SCROLL, summ_dur(2))\n1216:                       .set_place(level_id::current()),\n1217:             false))\n1218:         {\n1219:             // Choose a new duration based on HD.\n1220:             int x = max(mons->get_experience_level() - 3, 1);\n1221:             int dur = summ_dur(min(4, 1 + div_rand_round(17, x)));\n1222:             mon_enchant me = mon_enchant(ENCH_SUMMON_TIMER, nullptr, dur);",
    "method": "静态模板，无参数",
    "full_zh_display": "暗影的细丝在你周围旋转……",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/spl-summoning.cc:1136
crawl-ref/source/spl-summoning.cc",

中文全文
```text
暗影的细丝在你周围旋转……
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "Wisps of shadow whirl around you...",
    "zh_template": "暗影的细丝在你周围旋转……",
    "source": {
      "path": "crawl-ref/source/spl-summoning.cc",
      "line": 1136
    },
    "parameter_expressions": [
      "T_(\"Wisps of shadow whirl around you...\")"
    ],
    "conditions_and_generation": "1118:         canned_msg(MSG_NOTHING_HAPPENS);\n1119:     return spret::success;\n1120: }\n1121: \n1122: spret summon_shadow_creatures()\n1123: {\n1124:     // A small number of the monsters summoned by shadow creatures can fly,\n1125:     // so it is technically still usable above water or lava\n1126:     if (!you_can_see_habitable_spot_near(HT_FLYER, 2))\n1127:     {\n1128:         canned_msg(MSG_NO_AVAILABLE_SPACE);\n1129:         return spret::abort;\n1130:     }\n1131: \n1132:     // Hard to predict what resistances might come from this.\n1133:     if (stop_summoning_prompt())\n1134:         return spret::abort;\n1135: \n1136:     mpr(T_(\"Wisps of shadow whirl around you...\"));\n1137: \n1138:     int num = roll_dice(2, 2);\n1139:     int num_created = 0;\n1140: \n1141:     for (int i = 0; i < num; ++i)\n1142:     {\n1143:         if (monster *mons = create_monster(\n1144:             mgen_data(RANDOM_COMPATIBLE_MONSTER, BEH_FRIENDLY, you.pos(),\n1145:                       MHITYOU, MG_FORCE_BEH | MG_AUTOFOE | MG_NO_OOD)\n1146:                       // This duration is only used for band members.\n1147:                       .set_summoned(&you, MON_SUMM_SCROLL, summ_dur(2))\n1148:                       .set_place(level_id::current()),\n1149:             false))\n1150:         {\n1151:             // Choose a new duration based on HD.\n1152:             int x = max(mons->get_experience_level() - 3, 1);\n1153:             int dur = summ_dur(min(4, 1 + div_rand_round(17, x)));\n1154:             mon_enchant me = mon_enchant(ENCH_SUMMON_TIMER, nullptr, dur);",
    "method": "静态模板，无参数",
    "full_zh_display": "暗影的细丝在你周围旋转……",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

4. 独立语义判断与还原
影丝环绕玩家的视觉效果，完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-7-08

1. 完整英文
```text
You are enfeebled!
```

2–3. stable 消费者与参数证据

crawl-ref/source/spl-monench.cc:218
crawl-ref/source/spl-monench.cc",

中文全文
```text
你被削弱了！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You are enfeebled!",
    "zh_template": "你被削弱了！",
    "source": {
      "path": "crawl-ref/source/spl-monench.cc",
      "line": 218
    },
    "parameter_expressions": [
      "T_(\"You are enfeebled!\")"
    ],
    "conditions_and_generation": "200: \n201:     const int dur = random_range(7, 12);\n202:     for (auto hex : hexes)\n203:     {\n204:         if (hex == DUR_DAZED)\n205:             you.daze(random_range(2, 4));\n206:         else if (hex == DUR_BLIND && you.duration[DUR_BLIND] < dur * BASELINE_DELAY)\n207:         {\n208:             you.duration[DUR_BLIND] = 0;\n209:             blind_player(dur);\n210:         }\n211:         else\n212:             you.duration[hex] = max(dur * BASELINE_DELAY, you.duration[hex]);\n213:     }\n214: \n215:     if (res_margin > 0)\n216:         canned_msg(MSG_YOU_PARTIALLY_RESIST);\n217: \n218:     mpr(T_(\"You are enfeebled!\"));\n219:     return true;\n220: }\n221: \n222: spret cast_vile_clutch(int pow, bolt &beam, bool fail)\n223: {\n224:     spret result = zapping(ZAP_VILE_CLUTCH, pow, beam, true, nullptr, fail);\n225: \n226:     if (result == spret::success)\n227:         you.props[VILE_CLUTCH_POWER_KEY].get_int() = pow;\n228: \n229:     return result;\n230: }\n231: \n232: bool start_ranged_constriction(actor& caster, actor& target, int duration,\n233:                                constrict_type type)\n234: {\n235:     if (!caster.can_constrict(target, type))\n236:         return false;",
    "method": "静态模板，无参数",
    "full_zh_display": "你被削弱了！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/spl-monench.cc:218
crawl-ref/source/spl-monench.cc",

中文全文
```text
你被削弱了！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You are enfeebled!",
    "zh_template": "你被削弱了！",
    "source": {
      "path": "crawl-ref/source/spl-monench.cc",
      "line": 218
    },
    "parameter_expressions": [
      "T_(\"You are enfeebled!\")"
    ],
    "conditions_and_generation": "200: \n201:     const int dur = random_range(7, 12);\n202:     for (auto hex : hexes)\n203:     {\n204:         if (hex == DUR_DAZED)\n205:             you.daze(random_range(2, 4));\n206:         else if (hex == DUR_BLIND && you.duration[DUR_BLIND] < dur * BASELINE_DELAY)\n207:         {\n208:             you.duration[DUR_BLIND] = 0;\n209:             blind_player(dur);\n210:         }\n211:         else\n212:             you.duration[hex] = max(dur * BASELINE_DELAY, you.duration[hex]);\n213:     }\n214: \n215:     if (res_margin > 0)\n216:         canned_msg(MSG_YOU_PARTIALLY_RESIST);\n217: \n218:     mpr(T_(\"You are enfeebled!\"));\n219:     return true;\n220: }\n221: \n222: spret cast_vile_clutch(int pow, bolt &beam, bool fail)\n223: {\n224:     spret result = zapping(ZAP_VILE_CLUTCH, pow, beam, true, nullptr, fail);\n225: \n226:     if (result == spret::success)\n227:         you.props[VILE_CLUTCH_POWER_KEY].get_int() = pow;\n228: \n229:     return result;\n230: }\n231: \n232: bool start_ranged_constriction(actor& caster, actor& target, int duration,\n233:                                constrict_type type)\n234: {\n235:     if (!caster.can_constrict(target, type))\n236:         return false;",
    "method": "静态模板，无参数",
    "full_zh_display": "你被削弱了！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

4. 独立语义判断与还原
玩家被 enfeeble，削弱的对象正确。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-7-07

1. 完整英文
```text
You feel the power of Zot begin to gather its forces!
```

2–3. stable 消费者与参数证据

crawl-ref/source/mon-abil.cc:1640
crawl-ref/source/mon-abil.cc",

中文全文
```text
你感到佐特的力量开始集结兵力！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You feel the power of Zot begin to gather its forces!",
    "zh_template": "你感到佐特的力量开始集结兵力！",
    "source": {
      "path": "crawl-ref/source/mon-abil.cc",
      "line": 1640
    },
    "parameter_expressions": [
      "MSGCH_WARN",
      "T_(\"You feel the power of Zot begin to gather its forces!\")"
    ],
    "conditions_and_generation": "1622:     }\n1623: \n1624:     return mons_place(mg);\n1625: }\n1626: \n1627: void activate_tesseracts()\n1628: {\n1629:     if (you.props.exists(TESSERACT_SPAWN_COUNTER_KEY))\n1630:         return;\n1631: \n1632:     bool did_activate = false;\n1633:     for (monster_iterator mi; mi; ++mi)\n1634:     {\n1635:         if (mi->type != MONS_BOUNDLESS_TESSERACT)\n1636:             continue;\n1637: \n1638:         if (!did_activate)\n1639:         {\n1640:             mprf(MSGCH_WARN, T_(\"You feel the power of Zot begin to gather its forces!\"));\n1641:             take_note(Note(NOTE_TESSERACT_ACTIVATED));\n1642:             mark_milestone(\"tesseract.activate\", \"activated a tesseract\");\n1643:             // Tracked on the player instead of the monster so status lookup is quicker.\n1644:             you.props[TESSERACT_SPAWN_COUNTER_KEY] = 0;\n1645:             mi->props[TESSERACT_SPAWN_TIMER_KEY] = you.elapsed_time;\n1646: \n1647:             // Remove patrolling from everything but Orb guardians.\n1648:             for (monster_iterator mi2; mi2; ++mi2)\n1649:                 if (mi2->type != MONS_ORB_GUARDIAN && !mi2->friendly())\n1650:                     mi2->patrol_point.reset();\n1651: \n1652:             tesseract_action(**mi);\n1653:             did_activate = true;\n1654: \n1655:             // Spawn several monsters outside the orb vault immediately.\n1656:             const int num = random_range(4, 7);\n1657:             for (int i = 0; i < num; ++i)\n1658:                 _make_tesseract_spawn(false, true);",
    "method": "静态模板，无参数",
    "full_zh_display": "你感到佐特的力量开始集结兵力！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/mon-abil.cc:1601
crawl-ref/source/mon-abil.cc",

中文全文
```text
你感到佐特的力量开始集结兵力！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You feel the power of Zot begin to gather its forces!",
    "zh_template": "你感到佐特的力量开始集结兵力！",
    "source": {
      "path": "crawl-ref/source/mon-abil.cc",
      "line": 1601
    },
    "parameter_expressions": [
      "MSGCH_WARN",
      "T_(\"You feel the power of Zot begin to gather its forces!\")"
    ],
    "conditions_and_generation": "1583:     }\n1584: \n1585:     return mons_place(mg);\n1586: }\n1587: \n1588: void activate_tesseracts()\n1589: {\n1590:     if (you.props.exists(TESSERACT_SPAWN_COUNTER_KEY))\n1591:         return;\n1592: \n1593:     bool did_activate = false;\n1594:     for (monster_iterator mi; mi; ++mi)\n1595:     {\n1596:         if (mi->type != MONS_BOUNDLESS_TESSERACT)\n1597:             continue;\n1598: \n1599:         if (!did_activate)\n1600:         {\n1601:             mprf(MSGCH_WARN, T_(\"You feel the power of Zot begin to gather its forces!\"));\n1602:             take_note(Note(NOTE_TESSERACT_ACTIVATED));\n1603:             mark_milestone(\"tesseract.activate\", \"activated a tesseract\");\n1604:             // Tracked on the player instead of the monster so status lookup is quicker.\n1605:             you.props[TESSERACT_SPAWN_COUNTER_KEY] = 0;\n1606:             mi->props[TESSERACT_SPAWN_TIMER_KEY] = you.elapsed_time;\n1607: \n1608:             // Remove patrolling from everything but Orb guardians.\n1609:             for (monster_iterator mi2; mi2; ++mi2)\n1610:                 if (mi2->type != MONS_ORB_GUARDIAN && !mi2->friendly())\n1611:                     mi2->patrol_point.reset();\n1612: \n1613:             tesseract_action(**mi);\n1614:             did_activate = true;\n1615: \n1616:             // Spawn several monsters outside the orb vault immediately.\n1617:             const int num = random_range(4, 7);\n1618:             for (int i = 0; i < num; ++i)\n1619:                 _make_tesseract_spawn(false, true);",
    "method": "静态模板，无参数",
    "full_zh_display": "你感到佐特的力量开始集结兵力！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

4. 独立语义判断与还原
activate_tesseracts 确实唤来数个怪物；集结兵力对应 forces，不是将纯魔法能量误当士兵。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-1-04

1. 完整英文
```text
A small chunk of dense but otherwise unremarkable natural mineral. It can be
thrown to cause minor damage.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:2895
crawl-ref/source/describe.cc:2907
crawl-ref/source/describe.cc:3461
crawl-ref/source/describe.cc:7279
crawl-ref/source/item-name.cc",

中文全文
```text
一小块致密而常见的天然矿物。投掷它可以造成少量伤害。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一小块致密而常见的天然矿物。投掷它可以造成少量伤害。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:3167
crawl-ref/source/describe.cc:3179
crawl-ref/source/describe.cc:3731
crawl-ref/source/describe.cc:7967
crawl-ref/source/item-name.cc",

中文全文
```text
一小块致密而常见的天然矿物。投掷它可以造成少量伤害。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一小块致密而常见的天然矿物。投掷它可以造成少量伤害。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
致密天然矿物、可投掷及少量伤害完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-5-10

1. 完整英文
```text
<tiles>A small symbol on a stair tile signifies that there are items in that
position that you may want to check out.</tiles>
<console>If any items are covering stairs or an escape hatch, then that will
be indicated by highlighting the <w><<</w> or <w>></w> symbol, instead of hiding
the stair symbol with an item glyph.</console>
```

2–3. stable 消费者与参数证据

crawl-ref/source/hints.cc:1227
crawl-ref/source/hints.cc:401
crawl-ref/source/hints.cc:483
crawl-ref/source/hints.cc:2884
crawl-ref/source/hints.cc",

中文全文
```text
<tiles>楼梯地块上的小符号表示该位置还有物品，你可能会想查看。</tiles>
<console>如果有物品盖在楼梯或逃生舱口上，系统会把 <w><<</w> 或 <w>></w> 符号高亮显示，而不会用物品图符遮住楼梯符号。</console>
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "<tiles>楼梯地块上的小符号表示该位置还有物品，你可能会想查看。</tiles>\n<console>如果有物品盖在楼梯或逃生舱口上，系统会把 <w><<</w> 或 <w>></w> 符号高亮显示，而不会用物品图符遮住楼梯符号。</console>",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/hints.cc:1150
crawl-ref/source/hints.cc:402
crawl-ref/source/hints.cc:484
crawl-ref/source/hints.cc:2386
crawl-ref/source/hints.cc",

中文全文
```text
<tiles>楼梯地块上的小符号表示该位置还有物品，你可能会想查看。</tiles>
<console>如果有物品盖在楼梯或逃生舱口上，系统会把 <w><<</w> 或 <w>></w> 符号高亮显示，而不会用物品图符遮住楼梯符号。</console>
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "<tiles>楼梯地块上的小符号表示该位置还有物品，你可能会想查看。</tiles>\n<console>如果有物品盖在楼梯或逃生舱口上，系统会把 <w><<</w> 或 <w>></w> 符号高亮显示，而不会用物品图符遮住楼梯符号。</console>",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
楼梯物品覆盖时高亮楼梯符号、不替换成物品图符，完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-4-08

1. 完整英文
```text
Yredelemnul sends servants to aid you!
```

2–3. stable 消费者与参数证据

crawl-ref/source/god-abil.cc:1507
crawl-ref/source/god-abil.cc",

中文全文
```text
伊莱德莱姆努尔派来了仆从来援助你！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "Yredelemnul sends servants to aid you!",
    "zh_template": "伊莱德莱姆努尔派来了仆从来援助你！",
    "source": {
      "path": "crawl-ref/source/god-abil.cc",
      "line": 1507
    },
    "parameter_expressions": [
      "T_(\"Yredelemnul sends servants to aid you!\")"
    ],
    "conditions_and_generation": "1489:     int cap = div_rand_round(min((int)you.piety(), piety_breakpoint(4)) * 27, piety_breakpoint(4));\n1490:     int pow = min(you.experience_level, cap);\n1491: \n1492:     // Summon one stronger servant and two lesser ones.\n1493:     // (Note that a 'single' servant can be multiple monsters, depending on what\n1494:     // type we roll)\n1495:     if (yred_random_servant(pow))\n1496:         aid = true;\n1497:     if (yred_random_servant(div_rand_round(pow * 7, 10), false, 2))\n1498:         aid = true;\n1499:     // At very high power, a chance for additional servants\n1500:     if (x_chance_in_y(max(0, pow - 20), 10))\n1501:     {\n1502:         if (yred_random_servant(div_rand_round(pow * random_range(6, 9), 10), false, 2))\n1503:             aid = true;\n1504:     }\n1505: \n1506:     if (aid)\n1507:         mpr(T_(\"Yredelemnul sends servants to aid you!\"));\n1508: \n1509:     return true;\n1510: }\n1511: \n1512: // Called whenever you leave a floor with the black torch lit.\n1513: // Handles cleanup and prints messages based on how thoroughly the player\n1514: // scoured the floor.\n1515: void yred_end_conquest()\n1516: {\n1517:     // Calculate how cleared the floor is:\n1518:     int souls_remaining = 0;\n1519:     for (monster_iterator mi; mi; ++mi)\n1520:     {\n1521:         if (!mi->wont_attack() && !mi->is_firewood()\n1522:             && mons_can_be_spectralised(**mi, true)\n1523:             // Ignore monsters in no-tele-into areas, since these are often\n1524:             // literally unreachable, and we also don't want Yred to be unhappy\n1525:             // whenever there was a ghost vault on the floor.",
    "method": "静态模板，无参数",
    "full_zh_display": "伊莱德莱姆努尔派来了仆从来援助你！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/god-abil.cc:1598
crawl-ref/source/god-abil.cc",

中文全文
```text
伊莱德莱姆努尔派来了仆从来援助你！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "Yredelemnul sends servants to aid you!",
    "zh_template": "伊莱德莱姆努尔派来了仆从来援助你！",
    "source": {
      "path": "crawl-ref/source/god-abil.cc",
      "line": 1598
    },
    "parameter_expressions": [
      "T_(\"Yredelemnul sends servants to aid you!\")"
    ],
    "conditions_and_generation": "1580:     int cap = div_rand_round(min((int)you.piety(), piety_breakpoint(4)) * 27, piety_breakpoint(4));\n1581:     int pow = min(you.experience_level, cap);\n1582: \n1583:     // Summon one stronger servant and two lesser ones.\n1584:     // (Note that a 'single' servant can be multiple monsters, depending on what\n1585:     // type we roll)\n1586:     if (yred_random_servant(pow))\n1587:         aid = true;\n1588:     if (yred_random_servant(div_rand_round(pow * 7, 10), false, 2))\n1589:         aid = true;\n1590:     // At very high power, a chance for additional servants\n1591:     if (x_chance_in_y(max(0, pow - 20), 10))\n1592:     {\n1593:         if (yred_random_servant(div_rand_round(pow * random_range(6, 9), 10), false, 2))\n1594:             aid = true;\n1595:     }\n1596: \n1597:     if (aid)\n1598:         mpr(T_(\"Yredelemnul sends servants to aid you!\"));\n1599: \n1600:     return true;\n1601: }\n1602: \n1603: // Called whenever you leave a floor with the black torch lit.\n1604: // Handles cleanup and prints messages based on how thoroughly the player\n1605: // scoured the floor.\n1606: void yred_end_conquest()\n1607: {\n1608:     // Calculate how cleared the floor is:\n1609:     int souls_remaining = 0;\n1610:     for (monster_iterator mi; mi; ++mi)\n1611:     {\n1612:         if (!mi->wont_attack() && !mi->is_firewood()\n1613:             && mons_can_be_spectralised(**mi, true)\n1614:             // Ignore monsters in no-tele-into areas, since these are often\n1615:             // literally unreachable, and we also don't want Yred to be unhappy\n1616:             // whenever there was a ghost vault on the floor.",
    "method": "静态模板，无参数",
    "full_zh_display": "伊莱德莱姆努尔派来了仆从来援助你！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

4. 独立语义判断与还原
派遣仆从援助玩家，完整；来重复轻微，不作偏好式改写。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-6-05

1. 完整英文
```text
Welcome to %s!
```

2–3. stable 消费者与参数证据

crawl-ref/source/dat/des/portals/wizlab.des:169
crawl-ref/source/dat/des/portals/wizlab.des",

中文全文
```text
欢迎来到%s！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "Welcome to %s!",
    "zh_template": "欢迎来到%s！",
    "source": {
      "path": "crawl-ref/source/dat/des/portals/wizlab.des",
      "line": 169
    },
    "parameter_expressions": [
      "string.format(crawl.t_(\"Welcome to %s!\"),\n                            crawl.t_(wizlab_desc))"
    ],
    "conditions_and_generation": "153:     e.chance(math.floor(dgn.wizlab_chance_percent / 100 * 10000))\n154:     -- Don't apply the chance in Vaults, since we use a Vaults room for that\n155:     -- branch.\n156:     e.depth_chance(\"Vaults\", 0)\n157: end\n158: \n159: -- Destinations:\n160: function wizlab_setup (e)\n161:     e.orient(\"encompass\")\n162:     e.tags(\"no_item_gen no_monster_gen\")\n163:     e.kfeat(\"< = exit_wizlab\")\n164: end\n165: \n166: function wizlab_milestone (e, wizlab_desc)\n167:     crawl.mark_milestone(\"br.enter\", \"entered \" .. wizlab_desc .. \".\", \"parent\")\n168:     crawl.take_note(util.i18n_format_or_english(\"Entered %s\", wizlab_desc))\n169:     crawl.mpr(string.format(crawl.t_(\"Welcome to %s!\"),\n170:                             crawl.t_(wizlab_desc)))\n171: end\n172: \n173: function wizlab_doroklohe_convert_boxes(data, triggerable, triggerer,\n174:                                         marker, ev)\n175:   if triggerer.type ~= \"turn\" or triggerer.sub_type ~= \"countdown\" then\n176:     return\n177:   end\n178: \n179:   if data.phase == 1 then\n180:     data.phase = data.phase + 1\n181:     crawl.mpr(crawl.t_(\"The walls briefly shake.\"), \"warning\")\n182:     return\n183:   elseif data.phase == 2 then\n184:     data.phase = data.phase + 1\n185:     crawl.mpr(crawl.t_(\"The walls violently shake.\"), \"warning\")\n186:     return",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/dat/des/portals/wizlab.des:169
crawl-ref/source/dat/des/portals/wizlab.des",

中文全文
```text
欢迎来到%s！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "Welcome to %s!",
    "zh_template": "欢迎来到%s！",
    "source": {
      "path": "crawl-ref/source/dat/des/portals/wizlab.des",
      "line": 169
    },
    "parameter_expressions": [
      "string.format(crawl.t_(\"Welcome to %s!\"),\n                            crawl.t_(wizlab_desc))"
    ],
    "conditions_and_generation": "153:     e.chance(math.floor(dgn.wizlab_chance_percent / 100 * 10000))\n154:     -- Don't apply the chance in Vaults, since we use a Vaults room for that\n155:     -- branch.\n156:     e.depth_chance(\"Vaults\", 0)\n157: end\n158: \n159: -- Destinations:\n160: function wizlab_setup (e)\n161:     e.orient(\"encompass\")\n162:     e.tags(\"no_item_gen no_monster_gen\")\n163:     e.kfeat(\"< = exit_wizlab\")\n164: end\n165: \n166: function wizlab_milestone (e, wizlab_desc)\n167:     crawl.mark_milestone(\"br.enter\", \"entered \" .. wizlab_desc .. \".\", \"parent\")\n168:     crawl.take_note(util.i18n_format_or_english(\"Entered %s\", wizlab_desc))\n169:     crawl.mpr(string.format(crawl.t_(\"Welcome to %s!\"),\n170:                             crawl.t_(wizlab_desc)))\n171: end\n172: \n173: function wizlab_doroklohe_convert_boxes(data, triggerable, triggerer,\n174:                                         marker, ev)\n175:   if triggerer.type ~= \"turn\" or triggerer.sub_type ~= \"countdown\" then\n176:     return\n177:   end\n178: \n179:   if data.phase == 1 then\n180:     data.phase = data.phase + 1\n181:     crawl.mpr(crawl.t_(\"The walls briefly shake.\"), \"warning\")\n182:     return\n183:   elseif data.phase == 2 then\n184:     data.phase = data.phase + 1\n185:     crawl.mpr(crawl.t_(\"The walls violently shake.\"), \"warning\")\n186:     return",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。"
  }
]
```

4. 独立语义判断与还原
wizlab_desc 是巫师实验室目的地显示名，例欢迎来到云中法师的密室！；协议里程碑另走英文键，不拿它代入中文消息。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-4-01

1. 完整英文
```text
You grasp %s shadow with your own and put on a performance!
```

2–3. stable 消费者与参数证据

crawl-ref/source/god-abil.cc:3143
crawl-ref/source/god-abil.cc",

中文全文
```text
你用自己的影子抓住%s影子，开始表演！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You grasp %s shadow with your own and put on a performance!",
    "zh_template": "你用自己的影子抓住%s影子，开始表演！",
    "source": {
      "path": "crawl-ref/source/god-abil.cc",
      "line": 3143
    },
    "parameter_expressions": [
      "T_(\"You grasp %s shadow with your own and put on a performance!\")",
      "target.name(DESC_ITS).c_str()"
    ],
    "conditions_and_generation": "3125:     return T_(\"There isn't a suitable marionette in sight.\");\n3126: }\n3127: \n3128: spret dithmenos_marionette(monster& target, bool fail)\n3129: {\n3130:     vector<spell_type> mon_spells;\n3131:     for (const mon_spell_slot slot : target.spells)\n3132:     {\n3133:         if (valid_marionette_spell(slot.spell))\n3134:             mon_spells.push_back(slot.spell);\n3135:     }\n3136: \n3137:     // Should be impossible, I think.\n3138:     if (mon_spells.empty())\n3139:         return spret::abort;\n3140: \n3141:     fail_check();\n3142: \n3143:     mprf(T_(\"You grasp %s shadow with your own and put on a performance!\"),\n3144:           target.name(DESC_ITS).c_str());\n3145: \n3146:     behaviour_event(&target, ME_WHACK, &you);\n3147: \n3148:     vector<monster*> valid_targs = _get_marionette_targets();\n3149: \n3150:     int num_casts = 3 + max(0, you.skill_rdiv(SK_INVOCATIONS, 1, 6) - 2);\n3151:     int num_successful_casts = 0;\n3152: \n3153:     const int old_foe = target.foe;\n3154:     const coord_def old_target = target.target;\n3155:     const int old_energy = target.speed_increment;\n3156:     target.attitude = ATT_MARIONETTE;\n3157:     env.final_effect_monster_cache.push_back(target);\n3158: \n3159:     // Attempt to cast all valid spells the monster has, in randomized order,\n3160:     // (but using all spells at least once before repeating). End early if the\n3161:     // monster dies or we fail to be able to validly cast any spell.\n3162:     while (num_successful_casts < num_casts)",
    "method": "参数文本还原",
    "full_zh_display": "你用自己的影子抓住兽人的影子，开始表演！",
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "target.name(DESC_ITS).c_str()",
        "examples": [
          [
            "兽人的",
            "中文DESC_ITS经apostrophise；套用catalog %s's，未添加英文所有格。"
          ]
        ]
      }
    ],
    "branch_examples": [
      {
        "parameters": [
          {
            "expression": "target.name(DESC_ITS).c_str()",
            "value": "兽人的",
            "source_and_state": "中文DESC_ITS经apostrophise；套用catalog %s's，未添加英文所有格。"
          }
        ],
        "full_zh_display": "你用自己的影子抓住兽人的影子，开始表演！"
      }
    ],
    "formula": "按所列原始参数表达式和catalog参数示例逐位置替换；不增加冠词、量词或修正文案。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/god-abil.cc:3333
crawl-ref/source/god-abil.cc",

中文全文
```text
你用自己的影子抓住%s影子，开始表演！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You grasp %s shadow with your own and put on a performance!",
    "zh_template": "你用自己的影子抓住%s影子，开始表演！",
    "source": {
      "path": "crawl-ref/source/god-abil.cc",
      "line": 3333
    },
    "parameter_expressions": [
      "T_(\"You grasp %s shadow with your own and put on a performance!\")",
      "target.name(DESC_ITS).c_str()"
    ],
    "conditions_and_generation": "3315:     return T_(\"There isn't a suitable marionette in sight.\");\n3316: }\n3317: \n3318: spret dithmenos_marionette(monster& target, bool fail)\n3319: {\n3320:     vector<spell_type> mon_spells;\n3321:     for (const mon_spell_slot slot : target.spells)\n3322:     {\n3323:         if (valid_marionette_spell(slot.spell))\n3324:             mon_spells.push_back(slot.spell);\n3325:     }\n3326: \n3327:     // Should be impossible, I think.\n3328:     if (mon_spells.empty())\n3329:         return spret::abort;\n3330: \n3331:     fail_check();\n3332: \n3333:     mprf(T_(\"You grasp %s shadow with your own and put on a performance!\"),\n3334:           target.name(DESC_ITS).c_str());\n3335: \n3336:     behaviour_event(&target, ME_WHACK, &you);\n3337: \n3338:     vector<monster*> valid_targs = _get_marionette_targets();\n3339: \n3340:     int num_casts = 3 + max(0, you.skill_rdiv(SK_INVOCATIONS, 1, 6) - 2);\n3341:     int num_successful_casts = 0;\n3342: \n3343:     const int old_foe = target.foe;\n3344:     const coord_def old_target = target.target;\n3345:     const int old_energy = target.speed_increment;\n3346:     target.base_attitude = ATT_MARIONETTE;\n3347: \n3348:     // Attempt to cast all valid spells the monster has, in randomized order,\n3349:     // (but using all spells at least once before repeating). End early if the\n3350:     // monster dies or we fail to be able to validly cast any spell.\n3351:     while (num_successful_casts < num_casts)\n3352:     {",
    "method": "参数文本还原",
    "full_zh_display": "你用自己的影子抓住兽人的影子，开始表演！",
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "target.name(DESC_ITS).c_str()",
        "examples": [
          [
            "兽人的",
            "中文DESC_ITS经apostrophise；套用catalog %s's，未添加英文所有格。"
          ]
        ]
      }
    ],
    "branch_examples": [
      {
        "parameters": [
          {
            "expression": "target.name(DESC_ITS).c_str()",
            "value": "兽人的",
            "source_and_state": "中文DESC_ITS经apostrophise；套用catalog %s's，未添加英文所有格。"
          }
        ],
        "full_zh_display": "你用自己的影子抓住兽人的影子，开始表演！"
      }
    ],
    "formula": "按所列原始参数表达式和catalog参数示例逐位置替换；不增加冠词、量词或修正文案。"
  }
]
```

4. 独立语义判断与还原
DESC_ITS 自带所有格，例你用自己的影子抓住兽人的影子，开始表演！；未重复补的。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-5-01

1. 完整英文
```text
That<console> $1</console> is a closed door. You can open it by walking into it.
Sometimes it is useful to close a door. Do so by <nomouse>pressing
<w>$cmd[CMD_CLOSE_DOOR]</w> while next to it. If there are several doors, you
will then be prompted for a direction.</nomouse><localtiles>clicking on the door
while next to it.</localtiles>
```

2–3. stable 消费者与参数证据

crawl-ref/source/hints.cc:1291
crawl-ref/source/hints.cc:401
crawl-ref/source/hints.cc:483
crawl-ref/source/hints.cc:2884
crawl-ref/source/hints.cc",
crawl-ref/source/hints.cc",

中文全文
```text
那<console> $1</console>是一扇关着的门。走向它即可打开。有时把门关上会很有用。站在门旁时，<nomouse>按 <w>$cmd[CMD_CLOSE_DOOR]</w> 即可关门；如果旁边有好几扇门，系统会提示你选择方向。</nomouse><localtiles>单击门即可将它关上。</localtiles>
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "zh_body": "那<console> $1</console>是一扇关着的门。走向它即可打开。有时把门关上会很有用。站在门旁时，<nomouse>按 <w>$cmd[CMD_CLOSE_DOOR]</w> 即可关门；如果旁边有好几扇门，系统会提示你选择方向。</nomouse><localtiles>单击门即可将它关上。</localtiles>",
    "reason": "TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。",
    "parameter_source": "具体提示键/事件枚举由所列生产调用传入_get_hint/tutorial_msg→getHintString→HintsDB。",
    "key_generation_evidence": [
      {
        "path": "crawl-ref/source/hints.cc",
        "line": 1291,
        "statement": "print_hint(\"HINT_SEEN_DOOR\", glyph_to_tagstr(get_cell_glyph(gc)));",
        "snippet": "1281:         break;\n1282: \n1283:     case HINT_SEEN_DOOR:\n1284:         if (you.num_turns < 1)\n1285:             DELAY_EVENT;\n1286: \n1287: #ifdef USE_TILE\n1288:         tiles.place_cursor(CURSOR_TUTORIAL, gc);\n1289:         tiles.add_text_tag(TAG_TUTORIAL, T_(\"Closed door\"), gc);\n1290: #endif\n1291:         print_hint(\"HINT_SEEN_DOOR\", glyph_to_tagstr(get_cell_glyph(gc)));\n1292:         break;\n1293: \n1294:     case HINT_SEEN_RUNED_DOOR:\n1295: #ifdef USE_TILE\n1296:         tiles.place_cursor(CURSOR_TUTORIAL, gc);\n1297:         tiles.add_text_tag(TAG_TUTORIAL, T_(\"Runed door\"), gc);\n1298: #endif\n1299:         print_hint(\"HINT_SEEN_RUNED_DOOR\", glyph_to_tagstr(get_cell_glyph(gc)));\n1300:         break;\n1301: "
      }
    ]
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/hints.cc:1214
crawl-ref/source/hints.cc:402
crawl-ref/source/hints.cc:484
crawl-ref/source/hints.cc:2386
crawl-ref/source/hints.cc",
crawl-ref/source/hints.cc",

中文全文
```text
那<console> $1</console>是一扇关着的门。走向它即可打开。有时把门关上会很有用。站在门旁时，<nomouse>按 <w>$cmd[CMD_CLOSE_DOOR]</w> 即可关门；如果旁边有好几扇门，系统会提示你选择方向。</nomouse><localtiles>单击门即可将它关上。</localtiles>
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "zh_body": "那<console> $1</console>是一扇关着的门。走向它即可打开。有时把门关上会很有用。站在门旁时，<nomouse>按 <w>$cmd[CMD_CLOSE_DOOR]</w> 即可关门；如果旁边有好几扇门，系统会提示你选择方向。</nomouse><localtiles>单击门即可将它关上。</localtiles>",
    "reason": "TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。",
    "parameter_source": "具体提示键/事件枚举由所列生产调用传入_get_hint/tutorial_msg→getHintString→HintsDB。",
    "key_generation_evidence": [
      {
        "path": "crawl-ref/source/hints.cc",
        "line": 1214,
        "statement": "print_hint(\"HINT_SEEN_DOOR\", glyph_to_tagstr(get_cell_glyph(gc)));",
        "snippet": "1204:         break;\n1205: \n1206:     case HINT_SEEN_DOOR:\n1207:         if (you.num_turns < 1)\n1208:             DELAY_EVENT;\n1209: \n1210: #ifdef USE_TILE\n1211:         tiles.place_cursor(CURSOR_TUTORIAL, gc);\n1212:         tiles.add_text_tag(TAG_TUTORIAL, T_(\"Closed door\"), gc);\n1213: #endif\n1214:         print_hint(\"HINT_SEEN_DOOR\", glyph_to_tagstr(get_cell_glyph(gc)));\n1215:         break;\n1216: \n1217:     case HINT_SEEN_RUNED_DOOR:\n1218: #ifdef USE_TILE\n1219:         tiles.place_cursor(CURSOR_TUTORIAL, gc);\n1220:         tiles.add_text_tag(TAG_TUTORIAL, T_(\"Runed door\"), gc);\n1221: #endif\n1222:         print_hint(\"HINT_SEEN_RUNED_DOOR\", glyph_to_tagstr(get_cell_glyph(gc)));\n1223:         break;\n1224: "
      }
    ]
  }
]
```

4. 独立语义判断与还原
关门的相邻条件、多个门需选方向与图形点击分支完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-7-09

1. 完整英文
```text
You radiate an aura of cold.
```

2–3. stable 消费者与参数证据

crawl-ref/source/spl-monench.cc:86
crawl-ref/source/spl-monench.cc",

中文全文
```text
你散发出寒冷的光环。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You radiate an aura of cold.",
    "zh_template": "你散发出寒冷的光环。",
    "source": {
      "path": "crawl-ref/source/spl-monench.cc",
      "line": 86
    },
    "parameter_expressions": [
      "T_(\"You radiate an aura of cold.\")"
    ],
    "conditions_and_generation": "68:     if ((!mons && you.get_mutation_level(MUT_COLD_BLOODED))\n69:         || (mons && mons_class_flag(mons->type, M_COLD_BLOOD)))\n70:     {\n71:         duration *= 2;\n72:     }\n73: \n74:     // Guarantee a minimum duration if not fully resisted.\n75:     duration = max(duration, 2 + random2(4));\n76: \n77:     if (!mons)\n78:         return slow_player(duration);\n79: \n80:     return do_slow_monster(*mons, agent, duration * BASELINE_DELAY);\n81: }\n82: \n83: spret cast_englaciation(int pow, bool fail)\n84: {\n85:     fail_check();\n86:     mpr(T_(\"You radiate an aura of cold.\"));\n87:     apply_area_visible([pow] (coord_def where) {\n88:         return englaciate(where, pow, &you);\n89:     }, you.pos());\n90:     return spret::success;\n91: }\n92: \n93: /** Corona a monster.\n94:  *\n95:  *  @param mons the monster to get a backlight.\n96:  *  @param source The actor responsible for this.\n97:  *  @returns true if it got backlit (even if it was already).\n98:  */\n99: bool corona_monster(monster* mons, const actor* source)\n100: {\n101:     const bool was_glowing = mons->backlit();\n102: \n103:     mons->add_ench(mon_enchant(ENCH_CORONA, source));\n104: ",
    "method": "静态模板，无参数",
    "full_zh_display": "你散发出寒冷的光环。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/spl-monench.cc:86
crawl-ref/source/spl-monench.cc",

中文全文
```text
你散发出寒冷的光环。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You radiate an aura of cold.",
    "zh_template": "你散发出寒冷的光环。",
    "source": {
      "path": "crawl-ref/source/spl-monench.cc",
      "line": 86
    },
    "parameter_expressions": [
      "T_(\"You radiate an aura of cold.\")"
    ],
    "conditions_and_generation": "68:     if ((!mons && you.get_mutation_level(MUT_COLD_BLOODED))\n69:         || (mons && mons_class_flag(mons->type, M_COLD_BLOOD)))\n70:     {\n71:         duration *= 2;\n72:     }\n73: \n74:     // Guarantee a minimum duration if not fully resisted.\n75:     duration = max(duration, 4 + random2(4));\n76: \n77:     if (!mons)\n78:         return slow_player(duration);\n79: \n80:     return do_slow_monster(*mons, agent, duration * BASELINE_DELAY);\n81: }\n82: \n83: spret cast_englaciation(int pow, bool fail)\n84: {\n85:     fail_check();\n86:     mpr(T_(\"You radiate an aura of cold.\"));\n87:     apply_area_visible([pow] (coord_def where) {\n88:         return englaciate(where, pow, &you);\n89:     }, you.pos());\n90:     return spret::success;\n91: }\n92: \n93: /** Corona a monster.\n94:  *\n95:  *  @param mons the monster to get a backlight.\n96:  *  @param source The actor responsible for this.\n97:  *  @returns true if it got backlit (even if it was already).\n98:  */\n99: bool corona_monster(monster* mons, const actor* source)\n100: {\n101:     const bool was_glowing = mons->backlit();\n102: \n103:     mons->add_ench(mon_enchant(ENCH_CORONA, source));\n104: ",
    "method": "静态模板，无参数",
    "full_zh_display": "你散发出寒冷的光环。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

4. 独立语义判断与还原
玩家散发寒冷光环，完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-4-04

1. 完整英文
```text
Disciples of the Council learn to perform three martial techniques while moving
around in combat. They will also be taught to move at unfathomable speeds for
short distances, and become able to summon a storm of golden clouds to increase
their precision and damage for as long as they keep using martial attacks.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe-god.cc:729
crawl-ref/source/religion.cc",

中文全文
```text
门徒在战斗中走位时会学习实践三种武术。他们还将学习以不可测的速度短距离移动，
并能召唤金色云雾风暴来提高命中和伤害；只要持续使用武术攻击，强化便能持续。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "门徒在战斗中走位时会学习实践三种武术。他们还将学习以不可测的速度短距离移动，\n并能召唤金色云雾风暴来提高命中和伤害；只要持续使用武术攻击，强化便能持续。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe-god.cc:737
crawl-ref/source/religion.cc",

中文全文
```text
门徒在战斗中走位时会学习实践三种武术。他们还将学习以不可测的速度短距离移动，
并能召唤金色云雾风暴来提高命中和伤害；只要持续使用武术攻击，强化便能持续。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "门徒在战斗中走位时会学习实践三种武术。他们还将学习以不可测的速度短距离移动，\n并能召唤金色云雾风暴来提高命中和伤害；只要持续使用武术攻击，强化便能持续。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
原意是学会在移动时施展三种武术；现译成走位时学习实践，学习的时间条件与技能的触发动作关系错位。其余短距离高速与持续武术维持风暴正确。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：objective_error

{"type": "scope", "line": "both", "english": "Disciples of the Council learn to perform three martial techniques while moving\naround in combat. They will also be taught to move at unfathomable speeds for\nshort distances, and become able to summon a storm of golden clouds to increase\ntheir precision and damage for as long as they keep using martial attacks.", "current_full_zh": "门徒在战斗中走位时会学习实践三种武术。他们还将学习以不可测的速度短距离移动，\n并能召唤金色云雾风暴来提高命中和伤害；只要持续使用武术攻击，强化便能持续。", "problem": "学习的是在移动中施展武术，现译在走位时学习实践改变了动作关系。", "suggested_zh": "议会门徒会学会在战斗走位时施展三种武术。他们还将学会以不可思议的速度短距离移动，并能召唤金色云雾风暴来提高命中和伤害；只要持续使用武术攻击，强化便能持续。", "evidence": "crawl-ref/source/describe-god.cc:729; crawl-ref/source/religion.cc\",", "defect_points": 1}


## R4-6-10

1. 完整英文
```text
You hear a hidden mechanism click...the prison walls lower!
```

2–3. stable 消费者与参数证据

crawl-ref/source/dat/des/variable/large_themed.des:50
crawl-ref/source/dat/des/variable/large_themed.des",

中文全文
```text
你听到隐藏机关咔哒作响……监狱的墙壁降下了！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You hear a hidden mechanism click...the prison walls lower!",
    "zh_template": "你听到隐藏机关咔哒作响……监狱的墙壁降下了！",
    "source": {
      "path": "crawl-ref/source/dat/des/variable/large_themed.des",
      "line": 50
    },
    "parameter_expressions": [
      "crawl.t_(\"You hear a hidden mechanism click...the prison walls lower!\")"
    ],
    "conditions_and_generation": "34:                      blink frog w:8 / manticore w:4 / hell rat w:4 / raven w:2')\n35:         e.kmons('8 = death yak w:14 / hydra / skyshark w:4 / \\\n36:                      black mamba / lindwurm w:8 / torpor snail w:4 / \\\n37:                      boulder beetle w:2 / catoblepas w:2 / mountainshell w:2')\n38:     end\n39: end\n40: \n41: function callback.wizard_prison_walls()\n42:   local wall_pos = dgn.find_marker_positions_by_prop(\"prison\", \"wall\")\n43:   if wall_pos == nil then\n44:     return\n45:   end\n46: \n47:   for i, pos in ipairs(wall_pos) do\n48:     dgn.terrain_changed(pos.x, pos.y, \"floor\", false)\n49:   end\n50:   crawl.mpr(crawl.t_(\"You hear a hidden mechanism click...the prison walls lower!\"))\n51: end\n52: \n53: }}\n54: \n55: default-depth: D:12-, !D:$, Depths, !Depths:$\n56: # be careful to adapt these numbers for new vaults (using DEPTH)\n57: \n58: ###############################################################################\n59: # Castle of kobolds and goblins\n60: NAME:    minmay_goblin_kobold_castle\n61: TAGS:    no_rotate\n62: ORIENT:  north\n63: DEPTH:   D:3-6\n64: MONS:    goblin ; sling / hobgoblin w:2 ; sling\n65: MONS:    goblin ; club / hobgoblin ; club / gnoll w:3 ; club | spear\n66: MONS:    kobold ; stone",
    "method": "静态模板，无参数",
    "full_zh_display": "你听到隐藏机关咔哒作响……监狱的墙壁降下了！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/dat/des/variable/large_themed.des:50
crawl-ref/source/dat/des/variable/large_themed.des",

中文全文
```text
你听到隐藏机关咔哒作响……监狱的墙壁降下了！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You hear a hidden mechanism click...the prison walls lower!",
    "zh_template": "你听到隐藏机关咔哒作响……监狱的墙壁降下了！",
    "source": {
      "path": "crawl-ref/source/dat/des/variable/large_themed.des",
      "line": 50
    },
    "parameter_expressions": [
      "crawl.t_(\"You hear a hidden mechanism click...the prison walls lower!\")"
    ],
    "conditions_and_generation": "34:                      blink frog w:8 / manticore w:4 / hell rat w:4 / raven w:2')\n35:         e.kmons('8 = death yak w:14 / hydra / skyshark w:4 / \\\n36:                      black mamba / lindwurm w:8 / torpor snail w:4 / \\\n37:                      boulder beetle w:2 / catoblepas w:2 / mountainshell w:2')\n38:     end\n39: end\n40: \n41: function callback.wizard_prison_walls()\n42:   local wall_pos = dgn.find_marker_positions_by_prop(\"prison\", \"wall\")\n43:   if wall_pos == nil then\n44:     return\n45:   end\n46: \n47:   for i, pos in ipairs(wall_pos) do\n48:     dgn.terrain_changed(pos.x, pos.y, \"floor\", false)\n49:   end\n50:   crawl.mpr(crawl.t_(\"You hear a hidden mechanism click...the prison walls lower!\"))\n51: end\n52: \n53: }}\n54: \n55: default-depth: D:12-, !D:$, Depths, !Depths:$\n56: # be careful to adapt these numbers for new vaults (using DEPTH)\n57: \n58: ###############################################################################\n59: # Castle of kobolds and goblins\n60: NAME:    minmay_goblin_kobold_castle\n61: TAGS:    no_rotate\n62: ORIENT:  north\n63: DEPTH:   D:3-6\n64: MONS:    goblin ; sling / hobgoblin w:2 ; sling\n65: MONS:    goblin ; club / hobgoblin ; club / gnoll w:3 ; club | spear\n66: MONS:    kobold ; stone",
    "method": "静态模板，无参数",
    "full_zh_display": "你听到隐藏机关咔哒作响……监狱的墙壁降下了！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

4. 独立语义判断与还原
隐藏机关咔哒、监狱墙下降完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-4-10

1. 完整英文
```text
Trog is an ancient god of anger and violence. Followers are expected to kill in
Trog's name, and especially to slay wizards. In return, worshippers of Trog
gain the ability to go berserk at will in combat, and will be granted
assistance in the form of powerful weapons and mighty allies. Followers are
absolutely forbidden the use of spell magic.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe-god.cc:1103
crawl-ref/source/religion.cc",

中文全文
```text
特洛格是愤怒和暴力古神。特洛格的信徒要以祂之名杀死敌人，特别是要杀死巫师。
作为回报，信徒们会获得在战斗中自行狂暴的能力，
并会被赐予强大的武器和强力的盟友作为援助。特洛格绝对禁止祂的信徒施放法术。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "特洛格是愤怒和暴力古神。特洛格的信徒要以祂之名杀死敌人，特别是要杀死巫师。\n作为回报，信徒们会获得在战斗中自行狂暴的能力，\n并会被赐予强大的武器和强力的盟友作为援助。特洛格绝对禁止祂的信徒施放法术。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe-god.cc:1111
crawl-ref/source/religion.cc",

中文全文
```text
特洛格是愤怒和暴力古神。特洛格的信徒要以祂之名杀死敌人，特别是要杀死巫师。
作为回报，信徒们会获得在战斗中自行狂暴的能力，
并会被赐予强大的武器和强力的盟友作为援助。特洛格绝对禁止祂的信徒施放法术。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "特洛格是愤怒和暴力古神。特洛格的信徒要以祂之名杀死敌人，特别是要杀死巫师。\n作为回报，信徒们会获得在战斗中自行狂暴的能力，\n并会被赐予强大的武器和强力的盟友作为援助。特洛格绝对禁止祂的信徒施放法术。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
特洛格古神性质、以神名杀敌尤其巫师、战斗随意狂暴、武器盟友及法术禁令完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-1-10

1. 完整英文
```text
A robe woven of living vines. The vines form a symbiotic relationship with
their wearer, greatly increasing their regeneration, but preventing them from
being healed by potions.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:2869
crawl-ref/source/art-data.txt",

中文全文
```text
一件用活的藤蔓编织而成的长袍。藤蔓与穿戴者形成了共生关系，
大幅增强穿戴者的恢复能力，但是无法再通过药水获得治疗。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一件用活的藤蔓编织而成的长袍。藤蔓与穿戴者形成了共生关系，\n大幅增强穿戴者的恢复能力，但是无法再通过药水获得治疗。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:3141
crawl-ref/source/art-data.txt",

中文全文
```text
一件用活的藤蔓编织而成的长袍。藤蔓与穿戴者形成了共生关系，
大幅增强穿戴者的恢复能力，但是无法再通过药水获得治疗。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一件用活的藤蔓编织而成的长袍。藤蔓与穿戴者形成了共生关系，\n大幅增强穿戴者的恢复能力，但是无法再通过药水获得治疗。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
藤蔓共生、显著再生增益及药水不能治疗的反面效果完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-3-04

1. 完整英文
```text
is unaffected.
```

2–3. stable 消费者与参数证据

crawl-ref/source/mon-cast.cc:6059
crawl-ref/source/mon-cast.cc",
crawl-ref/source/dat/i18n/zh/source.txt",
crawl-ref/source/dat/i18n/zh/source.txt",

中文全文
```text
不受影响。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": " is unaffected.",
    "zh_template": "不受影响。",
    "source": {
      "path": "crawl-ref/source/mon-cast.cc",
      "line": 6059
    },
    "parameter_expressions": [
      "*ai->as_monster()",
      "T_(\" is unaffected.\")"
    ],
    "conditions_and_generation": "6041:     return ai_action::bad();\n6042: }\n6043: \n6044: // Actually attempt to mesmerise all valid enemies in LoS.\n6045: static void _mesmerise_los(monster& agent, int power, bool check_hearing)\n6046: {\n6047:     for (actor_near_iterator ai(agent.pos(), LOS_NO_TRANS); ai; ++ai)\n6048:     {\n6049:         // This duplicates some of _mesmerise_could_affect, but we want to\n6050:         // print immunity messages for other types of immunity.\n6051:         if (mons_aligned(&agent, *ai) || ai->is_peripheral())\n6052:             continue;\n6053: \n6054:         if (!_mesmerise_could_affect(agent, **ai, false, check_hearing))\n6055:         {\n6056:             if (ai->is_player())\n6057:                 canned_msg(MSG_YOU_UNAFFECTED);\n6058:             else\n6059:                 simple_monster_message(*ai->as_monster(), T_(\" is unaffected.\"));\n6060: \n6061:             continue;\n6062:         }\n6063: \n6064:         const int resist = ai->check_willpower(&agent, power);\n6065: \n6066:         // Once mesmerised by a particular monster, you cannot resist anymore.\n6067:         bool already_mesmerised = ai->is_player() ? you.beheld_by(agent)\n6068:                                     : ai->as_monster()->has_ench(ENCH_DAZED);\n6069: \n6070:         if (resist > 0 && !already_mesmerised)\n6071:         {\n6072:             mprf(\"%s%s\", ai->name(DESC_THE).c_str(), ai->resist_margin_phrase(resist).c_str());\n6073:             continue;\n6074:         }\n6075: \n6076:         if (ai->is_player())\n6077:             you.add_beholder(agent);",
    "method": "参数文本还原",
    "full_zh_display": "兽人不受影响。",
    "example_state": "指定可见普通兽人作为名称参数文本；不声称已在游戏中触发该状态。",
    "formula": "mons.name(descrip)；need_possessive=true时apostrophise，再拼event片段；CJK-CJK空格归一见message.cc。",
    "parameter_assets": [
      {
        "path": "crawl-ref/source/dat/i18n/zh/source.txt",
        "line": 32556,
        "key": "orc",
        "zh": "兽人"
      },
      {
        "path": "crawl-ref/source/dat/i18n/zh/source.txt",
        "line": 1624,
        "key": "%s's",
        "zh": "%s的"
      }
    ],
    "remaining_runtime": "其他怪物名、不可见分支、状态可达性和布局需运行时。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/mon-cast.cc:6262
crawl-ref/source/mon-cast.cc",
crawl-ref/source/dat/i18n/zh/source.txt",
crawl-ref/source/dat/i18n/zh/source.txt",

中文全文
```text
不受影响。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": " is unaffected.",
    "zh_template": "不受影响。",
    "source": {
      "path": "crawl-ref/source/mon-cast.cc",
      "line": 6262
    },
    "parameter_expressions": [
      "*ai->as_monster()",
      "T_(\" is unaffected.\")"
    ],
    "conditions_and_generation": "6244:     return ai_action::bad();\n6245: }\n6246: \n6247: // Actually attempt to mesmerise all valid enemies in LoS.\n6248: static void _mesmerise_los(monster& agent, int power, bool check_hearing)\n6249: {\n6250:     for (actor_near_iterator ai(agent.pos(), LOS_NO_TRANS); ai; ++ai)\n6251:     {\n6252:         // This duplicates some of _mesmerise_could_affect, but we want to\n6253:         // print immunity messages for other types of immunity.\n6254:         if (mons_aligned(&agent, *ai) || ai->is_peripheral())\n6255:             continue;\n6256: \n6257:         if (!_mesmerise_could_affect(agent, **ai, false, check_hearing))\n6258:         {\n6259:             if (ai->is_player())\n6260:                 canned_msg(MSG_YOU_UNAFFECTED);\n6261:             else\n6262:                 simple_monster_message(*ai->as_monster(), T_(\" is unaffected.\"));\n6263: \n6264:             continue;\n6265:         }\n6266: \n6267:         const int resist = ai->check_willpower(&agent, power);\n6268: \n6269:         // Once mesmerised by a particular monster, you cannot resist anymore.\n6270:         bool already_mesmerised = ai->is_player() ? you.beheld_by(agent)\n6271:                                     : ai->as_monster()->has_ench(ENCH_DAZED);\n6272: \n6273:         if (resist > 0 && !already_mesmerised)\n6274:         {\n6275:             mprf(\"%s%s\", ai->name(DESC_THE).c_str(), ai->resist_margin_phrase(resist).c_str());\n6276:             continue;\n6277:         }\n6278: \n6279:         if (ai->is_player())\n6280:             you.add_beholder(agent);",
    "method": "参数文本还原",
    "full_zh_display": "兽人不受影响。",
    "example_state": "指定可见普通兽人作为名称参数文本；不声称已在游戏中触发该状态。",
    "formula": "mons.name(descrip)；need_possessive=true时apostrophise，再拼event片段；CJK-CJK空格归一见message.cc。",
    "parameter_assets": [
      {
        "path": "crawl-ref/source/dat/i18n/zh/source.txt",
        "line": 35040,
        "key": "orc",
        "zh": "兽人"
      },
      {
        "path": "crawl-ref/source/dat/i18n/zh/source.txt",
        "line": 1669,
        "key": "%s's",
        "zh": "%s的"
      }
    ],
    "remaining_runtime": "其他怪物名、不可见分支、状态可达性和布局需运行时。"
  }
]
```

4. 独立语义判断与还原
simple_monster_message 补主语，例兽人不受影响。；不能把独立片段当漏主语。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-1-05

1. 完整英文
```text
A large war axe with a formidable double-sided head.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:2895
crawl-ref/source/describe.cc:2907
crawl-ref/source/describe.cc:3461
crawl-ref/source/describe.cc:7279
crawl-ref/source/item-prop.cc",

中文全文
```text
一把有着令人生畏的双面斧头的大型战斧。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一把有着令人生畏的双面斧头的大型战斧。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:3167
crawl-ref/source/describe.cc:3179
crawl-ref/source/describe.cc:3731
crawl-ref/source/describe.cc:7967
crawl-ref/source/item-prop.cc",

中文全文
```text
一把有着令人生畏的双面斧头的大型战斧。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一把有着令人生畏的双面斧头的大型战斧。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
大型战斧与双面斧头完整，修饰链可读，无必要偏好改写。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-6-09

1. 完整英文
```text
It guards the demonic rune of Zot.
```

2–3. stable 消费者与参数证据

crawl-ref/source/dat/des/branches/pan.des:288
crawl-ref/source/dat/des/branches/pan.des",

中文全文
```text
它守护着佐特恶魔符文。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "It guards the demonic rune of Zot.",
    "zh_template": "它守护着佐特恶魔符文。",
    "source": {
      "path": "crawl-ref/source/dat/des/branches/pan.des",
      "line": 288
    },
    "parameter_expressions": [
      "crawl.t_(\"It guards the demonic rune of Zot.\")"
    ],
    "conditions_and_generation": "272:     else\n273:         e.subst(\"12 = .\")\n274:         e.kmons(glyph .. \" = \" .. tiertwo .. \" / \" ..\n275:                 tierthree .. \" / \" .. tierthree)\n276:     end\n277: \n278:     e.ftile(\".+12O$ : floor_demonic_red / floor_demonic_blue / \" ..\n279:                      \"floor_demonic_green / floor_demonic_magenta\")\n280: end\n281: \n282: function pan_declare_demonic_rune(holy)\n283:   if holy then\n284:     crawl.mpr(crawl.t_(\"The tension of great conflict fills the air!\"), \"warning\")\n285:     crawl.mpr(crawl.t_(\"The demonic rune of Zot may be found here.\"))\n286:   else\n287:     crawl.mpr(crawl.t_(\"A powerful Pandemonium lord resides here.\"), \"warning\")\n288:     crawl.mpr(crawl.t_(\"It guards the demonic rune of Zot.\"))\n289:   end\n290: end\n291: \n292: function pan_highlights_setup(e)\n293:   -- Choose fixed demonic rune vaults.\n294:   local set = { \"boxes\", \"hellions\", \"pain\", \"frozen\", \"disco\" }\n295:   local vaultone = \"_\" .. util.random_from(set)\n296:   local vaulttwo = vaultone\n297:   while vaulttwo == vaultone do\n298:      vaulttwo = \"_\" .. util.random_from(set)\n299:   end\n300:   e.hook('post_place', function ()\n301:     dgn.place_maps{tag=(\"pan_fixed_rune\" .. vaultone), count=1, die_on_error=true}\n302:     dgn.place_maps{tag=(\"pan_fixed_lure\" .. vaulttwo), count=1, die_on_error=true}\n303:     dgn.place_maps{tag=(\"serial_pan\" .. vaultone), count=3}\n304:     dgn.place_maps{tag=(\"serial_pan\" .. vaulttwo), count=3}",
    "method": "静态模板，无参数",
    "full_zh_display": "它守护着佐特恶魔符文。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/dat/des/branches/pan.des:288
crawl-ref/source/dat/des/branches/pan.des",

中文全文
```text
它守护着佐特恶魔符文。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "It guards the demonic rune of Zot.",
    "zh_template": "它守护着佐特恶魔符文。",
    "source": {
      "path": "crawl-ref/source/dat/des/branches/pan.des",
      "line": 288
    },
    "parameter_expressions": [
      "crawl.t_(\"It guards the demonic rune of Zot.\")"
    ],
    "conditions_and_generation": "272:     else\n273:         e.subst(\"12 = .\")\n274:         e.kmons(glyph .. \" = \" .. tiertwo .. \" / \" ..\n275:                 tierthree .. \" / \" .. tierthree)\n276:     end\n277: \n278:     e.ftile(\".+12O$ : floor_demonic_red / floor_demonic_blue / \" ..\n279:                      \"floor_demonic_green / floor_demonic_magenta\")\n280: end\n281: \n282: function pan_declare_demonic_rune(holy)\n283:   if holy then\n284:     crawl.mpr(crawl.t_(\"The tension of great conflict fills the air!\"), \"warning\")\n285:     crawl.mpr(crawl.t_(\"The demonic rune of Zot may be found here.\"))\n286:   else\n287:     crawl.mpr(crawl.t_(\"A powerful Pandemonium lord resides here.\"), \"warning\")\n288:     crawl.mpr(crawl.t_(\"It guards the demonic rune of Zot.\"))\n289:   end\n290: end\n291: \n292: function pan_highlights_setup(e)\n293:   -- Choose fixed demonic rune vaults.\n294:   local set = { \"boxes\", \"hellions\", \"pain\", \"frozen\", \"disco\" }\n295:   local vaultone = \"_\" .. util.random_from(set)\n296:   local vaulttwo = vaultone\n297:   while vaulttwo == vaultone do\n298:      vaulttwo = \"_\" .. util.random_from(set)\n299:   end\n300:   e.hook('post_place', function ()\n301:     dgn.place_maps{tag=(\"pan_fixed_rune\" .. vaultone), count=1, die_on_error=true}\n302:     dgn.place_maps{tag=(\"pan_fixed_lure\" .. vaulttwo), count=1, die_on_error=true}\n303:     dgn.place_maps{tag=(\"serial_pan\" .. vaultone), count=3}\n304:     dgn.place_maps{tag=(\"serial_pan\" .. vaulttwo), count=3}",
    "method": "静态模板，无参数",
    "full_zh_display": "它守护着佐特恶魔符文。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

4. 独立语义判断与还原
守卫恶魔符文，完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-6-08

1. 完整英文
```text
As the champion is destroyed, you hear a distant grinding noise.
```

2–3. stable 消费者与参数证据

crawl-ref/source/dat/des/variable/compat.des:147
crawl-ref/source/dat/des/variable/compat.des",

中文全文
```text
随着冠军被消灭，你听到远处传来摩擦声。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "As the champion is destroyed, you hear a distant grinding noise.",
    "zh_template": "随着冠军被消灭，你听到远处传来摩擦声。",
    "source": {
      "path": "crawl-ref/source/dat/des/variable/compat.des",
      "line": 147
    },
    "parameter_expressions": [
      "crawl.t_(\"As the champion is destroyed, you hear a distant grinding noise.\")"
    ],
    "conditions_and_generation": "131: \n132:   local function get_replica (replicanum)\n133:     local myreplicas = dgn.find_marker_positions_by_prop(\"skele_replica\", replicanum)\n134:     return myreplicas[1]\n135:   end\n136: \n137:   local wall_pos = get_replica(data.skele_number)\n138:   if wall_pos == nil then\n139:     crawl.mpr(\"Couldn't find a replica!\")\n140:   end\n141: \n142:   dgn.terrain_changed(wall_pos.x, wall_pos.y, \"floor\", false)\n143: \n144:   if you.see_cell(wall_pos.x, wall_pos.y) then\n145:     crawl.mpr(crawl.t_(\"As the champion is destroyed, a metal wall slides away!\"))\n146:   else\n147:     crawl.mpr(crawl.t_(\"As the champion is destroyed, you hear a distant grinding noise.\"))\n148:   end\n149: end\n150: \n151: function tukima_machine (data, triggerable, triggerer, marker, ev)\n152:   -- do nothing\n153: end\n154: \n155: function wizlab_eringya_grow(data, triggerable, triggerer, marker, ev)\n156:   -- do nothing\n157: end\n158: \n159: function callback.spiders_nest_cobweb_light(data, triggerable, triggerer, marker, ev)\n160:   -- do nothing\n161: end\n162: \n163: function callback.spiders_nest_web_lair(data, triggerable, triggerer, marker, ev)",
    "method": "静态模板，无参数",
    "full_zh_display": "随着冠军被消灭，你听到远处传来摩擦声。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/dat/des/variable/compat.des:147
crawl-ref/source/dat/des/variable/compat.des",

中文全文
```text
随着冠军被消灭，你听到远处传来摩擦声。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "As the champion is destroyed, you hear a distant grinding noise.",
    "zh_template": "随着冠军被消灭，你听到远处传来摩擦声。",
    "source": {
      "path": "crawl-ref/source/dat/des/variable/compat.des",
      "line": 147
    },
    "parameter_expressions": [
      "crawl.t_(\"As the champion is destroyed, you hear a distant grinding noise.\")"
    ],
    "conditions_and_generation": "131: \n132:   local function get_replica (replicanum)\n133:     local myreplicas = dgn.find_marker_positions_by_prop(\"skele_replica\", replicanum)\n134:     return myreplicas[1]\n135:   end\n136: \n137:   local wall_pos = get_replica(data.skele_number)\n138:   if wall_pos == nil then\n139:     crawl.mpr(\"Couldn't find a replica!\")\n140:   end\n141: \n142:   dgn.terrain_changed(wall_pos.x, wall_pos.y, \"floor\", false)\n143: \n144:   if you.see_cell(wall_pos.x, wall_pos.y) then\n145:     crawl.mpr(crawl.t_(\"As the champion is destroyed, a metal wall slides away!\"))\n146:   else\n147:     crawl.mpr(crawl.t_(\"As the champion is destroyed, you hear a distant grinding noise.\"))\n148:   end\n149: end\n150: \n151: function tukima_machine (data, triggerable, triggerer, marker, ev)\n152:   -- do nothing\n153: end\n154: \n155: function wizlab_eringya_grow(data, triggerable, triggerer, marker, ev)\n156:   -- do nothing\n157: end\n158: \n159: function callback.spiders_nest_cobweb_light(data, triggerable, triggerer, marker, ev)\n160:   -- do nothing\n161: end\n162: \n163: function callback.spiders_nest_web_lair(data, triggerable, triggerer, marker, ev)",
    "method": "静态模板，无参数",
    "full_zh_display": "随着冠军被消灭，你听到远处传来摩擦声。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

4. 独立语义判断与还原
冠军毁灭引起远处摩擦声，完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-7-10

1. 完整英文
```text
You hear a sizzling sound.

You hear a grinding noise.
```

2–3. stable 消费者与参数证据

crawl-ref/source/mon-act.cc:4031
crawl-ref/source/mon-act.cc",
crawl-ref/source/mon-act.cc",

中文全文
```text
[此模板无中文catalog条目：You hear a sizzling sound.]

你听到一阵研磨声。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You hear a sizzling sound.",
    "zh_template": null,
    "source": {
      "path": "crawl-ref/source/mon-act.cc",
      "line": 4031
    },
    "parameter_expressions": [
      "MSGCH_SOUND",
      "mons->type == MONS_DISSOLUTION\n                                ? \"You hear a sizzling sound.\"\n                                : \"You hear a grinding noise.\""
    ],
    "conditions_and_generation": "4013:         {\n4014:             // Flattening trees has a movement cost to the monster\n4015:             // - 100% over and above its normal move cost.\n4016:             _swim_or_move_energy(*mons);\n4017:             if (you.see_cell(target))\n4018:             {\n4019:                 const bool actor_visible = you.can_see(*mons);\n4020:                 mprf(T_(\"%s knocks down a tree!\"),\n4021:                         actor_visible?\n4022:                         mons->name(DESC_THE).c_str() : T_(\"Something\"));\n4023:                 noisy(25, target);\n4024:             }\n4025:             else\n4026:                 noisy(25, target, \"You hear a crashing sound.\");\n4027:         }\n4028:         // Dissolution dissolves walls.\n4029:         else if (player_can_hear(target))\n4030:         {\n4031:             mprf(MSGCH_SOUND, mons->type == MONS_DISSOLUTION\n4032:                                 ? \"You hear a sizzling sound.\"\n4033:                                 : \"You hear a grinding noise.\");\n4034:         }\n4035:     }\n4036: \n4037:     bool ret = false;\n4038:     if (good_move[delta.x + 1][delta.y + 1] && !delta.origin())\n4039:     {\n4040:         // Check for attacking player.\n4041:         // XX is this actually reachable? this exact condition is already dealt\n4042:         // with in handle_monster_move\n4043:         if (mons->pos() + delta == you.pos())\n4044:         {\n4045:             ret = fight_melee(mons, &you);\n4046:             delta.reset();\n4047:         }\n4048: \n4049:         // If we're following the player through stairs, the only valid\n4050:         // movement is towards the player. -- bwr\n4051:         if (testbits(mons->flags, MF_TAKING_STAIRS))",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。"
  },
  {
    "english": "You hear a grinding noise.",
    "zh_template": "你听到一阵研磨声。",
    "source": {
      "path": "crawl-ref/source/mon-act.cc",
      "line": 4031
    },
    "parameter_expressions": [
      "MSGCH_SOUND",
      "mons->type == MONS_DISSOLUTION\n                                ? \"You hear a sizzling sound.\"\n                                : \"You hear a grinding noise.\""
    ],
    "conditions_and_generation": "4013:         {\n4014:             // Flattening trees has a movement cost to the monster\n4015:             // - 100% over and above its normal move cost.\n4016:             _swim_or_move_energy(*mons);\n4017:             if (you.see_cell(target))\n4018:             {\n4019:                 const bool actor_visible = you.can_see(*mons);\n4020:                 mprf(T_(\"%s knocks down a tree!\"),\n4021:                         actor_visible?\n4022:                         mons->name(DESC_THE).c_str() : T_(\"Something\"));\n4023:                 noisy(25, target);\n4024:             }\n4025:             else\n4026:                 noisy(25, target, \"You hear a crashing sound.\");\n4027:         }\n4028:         // Dissolution dissolves walls.\n4029:         else if (player_can_hear(target))\n4030:         {\n4031:             mprf(MSGCH_SOUND, mons->type == MONS_DISSOLUTION\n4032:                                 ? \"You hear a sizzling sound.\"\n4033:                                 : \"You hear a grinding noise.\");\n4034:         }\n4035:     }\n4036: \n4037:     bool ret = false;\n4038:     if (good_move[delta.x + 1][delta.y + 1] && !delta.origin())\n4039:     {\n4040:         // Check for attacking player.\n4041:         // XX is this actually reachable? this exact condition is already dealt\n4042:         // with in handle_monster_move\n4043:         if (mons->pos() + delta == you.pos())\n4044:         {\n4045:             ret = fight_melee(mons, &you);\n4046:             delta.reset();\n4047:         }\n4048: \n4049:         // If we're following the player through stairs, the only valid\n4050:         // movement is towards the player. -- bwr\n4051:         if (testbits(mons->flags, MF_TAKING_STAIRS))",
    "method": "静态模板，无参数",
    "full_zh_display": "你听到一阵研磨声。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/mon-act.cc:4175
crawl-ref/source/mon-act.cc",
crawl-ref/source/mon-act.cc",

中文全文
```text
你听到一阵滋滋声。

你听到一阵研磨声。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You hear a sizzling sound.",
    "zh_template": "你听到一阵滋滋声。",
    "source": {
      "path": "crawl-ref/source/mon-act.cc",
      "line": 4175
    },
    "parameter_expressions": [
      "MSGCH_SOUND",
      "mons->type == MONS_DISSOLUTION\n                                ? T_(\"You hear a sizzling sound.\")\n                                : T_(\"You hear a grinding noise.\")"
    ],
    "conditions_and_generation": "4157:         {\n4158:             // Flattening trees has a movement cost to the monster\n4159:             // - 100% over and above its normal move cost.\n4160:             _swim_or_move_energy(*mons);\n4161:             if (you.see_cell(target))\n4162:             {\n4163:                 const bool actor_visible = you.can_see(*mons);\n4164:                 mprf(T_(\"%s knocks down a tree!\"),\n4165:                         actor_visible?\n4166:                         mons->name(DESC_THE).c_str() : T_(\"Something\"));\n4167:                 noisy(25, target);\n4168:             }\n4169:             else\n4170:                 noisy(25, target, T_(\"You hear a crashing sound.\"));\n4171:         }\n4172:         // Dissolution dissolves walls.\n4173:         else if (player_can_hear(target))\n4174:         {\n4175:             mprf(MSGCH_SOUND, mons->type == MONS_DISSOLUTION\n4176:                                 ? T_(\"You hear a sizzling sound.\")\n4177:                                 : T_(\"You hear a grinding noise.\"));\n4178:         }\n4179:     }\n4180: \n4181:     bool ret = false;\n4182:     if (good_move[delta.x + 1][delta.y + 1] && !delta.origin())\n4183:     {\n4184:         // Check for attacking player.\n4185:         // XX is this actually reachable? this exact condition is already dealt\n4186:         // with in handle_monster_move\n4187:         if (mons->pos() + delta == you.pos())\n4188:         {\n4189:             ret = mons_fight(mons, &you);\n4190:             delta.reset();\n4191:         }\n4192: \n4193:         // If we're following the player through stairs, the only valid\n4194:         // movement is towards the player. -- bwr\n4195:         if (testbits(mons->flags, MF_TAKING_STAIRS))",
    "method": "静态模板，无参数",
    "full_zh_display": "你听到一阵滋滋声。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  },
  {
    "english": "You hear a grinding noise.",
    "zh_template": "你听到一阵研磨声。",
    "source": {
      "path": "crawl-ref/source/mon-act.cc",
      "line": 4175
    },
    "parameter_expressions": [
      "MSGCH_SOUND",
      "mons->type == MONS_DISSOLUTION\n                                ? T_(\"You hear a sizzling sound.\")\n                                : T_(\"You hear a grinding noise.\")"
    ],
    "conditions_and_generation": "4157:         {\n4158:             // Flattening trees has a movement cost to the monster\n4159:             // - 100% over and above its normal move cost.\n4160:             _swim_or_move_energy(*mons);\n4161:             if (you.see_cell(target))\n4162:             {\n4163:                 const bool actor_visible = you.can_see(*mons);\n4164:                 mprf(T_(\"%s knocks down a tree!\"),\n4165:                         actor_visible?\n4166:                         mons->name(DESC_THE).c_str() : T_(\"Something\"));\n4167:                 noisy(25, target);\n4168:             }\n4169:             else\n4170:                 noisy(25, target, T_(\"You hear a crashing sound.\"));\n4171:         }\n4172:         // Dissolution dissolves walls.\n4173:         else if (player_can_hear(target))\n4174:         {\n4175:             mprf(MSGCH_SOUND, mons->type == MONS_DISSOLUTION\n4176:                                 ? T_(\"You hear a sizzling sound.\")\n4177:                                 : T_(\"You hear a grinding noise.\"));\n4178:         }\n4179:     }\n4180: \n4181:     bool ret = false;\n4182:     if (good_move[delta.x + 1][delta.y + 1] && !delta.origin())\n4183:     {\n4184:         // Check for attacking player.\n4185:         // XX is this actually reachable? this exact condition is already dealt\n4186:         // with in handle_monster_move\n4187:         if (mons->pos() + delta == you.pos())\n4188:         {\n4189:             ret = mons_fight(mons, &you);\n4190:             delta.reset();\n4191:         }\n4192: \n4193:         // If we're following the player through stairs, the only valid\n4194:         // movement is towards the player. -- bwr\n4195:         if (testbits(mons->flags, MF_TAKING_STAIRS))",
    "method": "静态模板，无参数",
    "full_zh_display": "你听到一阵研磨声。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

4. 独立语义判断与还原
stable 两个三元分支均裸英文，无论 catalog 有无条目都会显示英文；输入研磨声的中文还原不符合调用。trunk 两分支已加 T_。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：objective_error

{"type": "untranslated", "line": "stable", "english": "You hear a sizzling sound.\n\nYou hear a grinding noise.", "current_full_zh": "You hear a sizzling sound. / You hear a grinding noise.", "problem": "两条声音都缺少 T_；研磨声虽有中文条目仍未被调用，不仅是滋滋声缺catalog。", "suggested_zh": "你听到一阵滋滋声。 / 你听到一阵研磨声。", "evidence": "stable mon-act.cc:4031-4033；trunk :4175 两分支 T_。", "defect_points": 1}


## R4-6-04

1. 完整英文
```text
The abyss shimmers again as the detected abyssal rune vanishes from your memory%1$s.

 and reappears

The abyssal matter surrounding you shimmers strangely.

You detect the abyssal rune!
```

2–3. stable 消费者与参数证据

crawl-ref/source/abyss.cc:332
crawl-ref/source/abyss.cc:338
crawl-ref/source/abyss.cc:339
crawl-ref/source/abyss.cc",
crawl-ref/source/abyss.cc",
crawl-ref/source/abyss.cc",
crawl-ref/source/abyss.cc",

中文全文
```text
深渊再次闪烁，你记忆中探测到的深渊符文消失了%1$s。

，又重新出现了

你周围的深渊物质奇怪地闪烁着。

你探测到了深渊符文！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "The abyss shimmers again as the detected abyssal rune vanishes from your memory%1$s.",
    "zh_template": "深渊再次闪烁，你记忆中探测到的深渊符文消失了%1$s。",
    "source": {
      "path": "crawl-ref/source/abyss.cc",
      "line": 332
    },
    "parameter_expressions": [
      "T_(\"The abyss shimmers again as the detected \"\n              \"abyssal rune vanishes from your memory%1$s.\")",
      "detected ? T_(\" and reappears\") : \"\""
    ],
    "conditions_and_generation": "314:     // now we need to check if a new or moved rune appeared\n315: \n316:     bool detected = false;\n317:     cur_loc = coord_def(-1,-1);\n318:     // check if a new one generated\n319:     for (rectangle_iterator ri(MAPGEN_BORDER); ri; ++ri)\n320:     {\n321:         // sets map knowledge by side effect if found\n322:         if (_sync_rune_knowledge(*ri))\n323:         {\n324:             detected = true;\n325:             cur_loc = *ri;\n326:             break;\n327:         }\n328:     }\n329: \n330:     if (existed)\n331:     {\n332:         mprf_p(T_(\"The abyss shimmers again as the detected \"\n333:               \"abyssal rune vanishes from your memory%1$s.\"),\n334:               detected ? T_(\" and reappears\") : \"\");\n335:     }\n336:     else if (detected)\n337:     {\n338:         mpr(T_(\"The abyssal matter surrounding you shimmers strangely.\"));\n339:         mpr(T_(\"You detect the abyssal rune!\"));\n340:     }\n341: \n342:     // XX could do the xom check from here?\n343: }\n344: \n345: static bool _abyss_place_rune_vault(const map_bitmask &abyss_genlevel_mask)\n346: {\n347:     bool result = false;\n348:     int tries = 10;\n349:     do\n350:     {\n351:         result = _abyss_place_vault_tagged(abyss_genlevel_mask, \"abyss_rune\");\n352:     }",
    "method": "参数文本还原",
    "full_zh_display": "深渊再次闪烁，你记忆中探测到的深渊符文消失了，又重新出现了。",
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "detected ? T_(\" and reappears\") : \"\"",
        "examples": [
          [
            "，又重新出现了",
            "按实参条件分支选择；完整条件：detected ? T_(\" and reappears\") : \"\""
          ],
          [
            "",
            "按实参条件分支选择；完整条件：detected ? T_(\" and reappears\") : \"\""
          ]
        ]
      }
    ],
    "branch_examples": [
      {
        "parameters": [
          {
            "expression": "detected ? T_(\" and reappears\") : \"\"",
            "value": "，又重新出现了",
            "source_and_state": "按实参条件分支选择；完整条件：detected ? T_(\" and reappears\") : \"\""
          }
        ],
        "full_zh_display": "深渊再次闪烁，你记忆中探测到的深渊符文消失了，又重新出现了。"
      },
      {
        "parameters": [
          {
            "expression": "detected ? T_(\" and reappears\") : \"\"",
            "value": "",
            "source_and_state": "按实参条件分支选择；完整条件：detected ? T_(\" and reappears\") : \"\""
          }
        ],
        "full_zh_display": "深渊再次闪烁，你记忆中探测到的深渊符文消失了。"
      }
    ],
    "formula": "按所列原始参数表达式和catalog参数示例逐位置替换；不增加冠词、量词或修正文案。"
  },
  {
    "english": " and reappears",
    "zh_template": "，又重新出现了",
    "source": {
      "path": "crawl-ref/source/abyss.cc",
      "line": 332
    },
    "parameter_expressions": [
      "T_(\"The abyss shimmers again as the detected \"\n              \"abyssal rune vanishes from your memory%1$s.\")",
      "detected ? T_(\" and reappears\") : \"\""
    ],
    "conditions_and_generation": "314:     // now we need to check if a new or moved rune appeared\n315: \n316:     bool detected = false;\n317:     cur_loc = coord_def(-1,-1);\n318:     // check if a new one generated\n319:     for (rectangle_iterator ri(MAPGEN_BORDER); ri; ++ri)\n320:     {\n321:         // sets map knowledge by side effect if found\n322:         if (_sync_rune_knowledge(*ri))\n323:         {\n324:             detected = true;\n325:             cur_loc = *ri;\n326:             break;\n327:         }\n328:     }\n329: \n330:     if (existed)\n331:     {\n332:         mprf_p(T_(\"The abyss shimmers again as the detected \"\n333:               \"abyssal rune vanishes from your memory%1$s.\"),\n334:               detected ? T_(\" and reappears\") : \"\");\n335:     }\n336:     else if (detected)\n337:     {\n338:         mpr(T_(\"The abyssal matter surrounding you shimmers strangely.\"));\n339:         mpr(T_(\"You detect the abyssal rune!\"));\n340:     }\n341: \n342:     // XX could do the xom check from here?\n343: }\n344: \n345: static bool _abyss_place_rune_vault(const map_bitmask &abyss_genlevel_mask)\n346: {\n347:     bool result = false;\n348:     int tries = 10;\n349:     do\n350:     {\n351:         result = _abyss_place_vault_tagged(abyss_genlevel_mask, \"abyss_rune\");\n352:     }",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。"
  },
  {
    "english": "The abyssal matter surrounding you shimmers strangely.",
    "zh_template": "你周围的深渊物质奇怪地闪烁着。",
    "source": {
      "path": "crawl-ref/source/abyss.cc",
      "line": 338
    },
    "parameter_expressions": [
      "T_(\"The abyssal matter surrounding you shimmers strangely.\")"
    ],
    "conditions_and_generation": "320:     {\n321:         // sets map knowledge by side effect if found\n322:         if (_sync_rune_knowledge(*ri))\n323:         {\n324:             detected = true;\n325:             cur_loc = *ri;\n326:             break;\n327:         }\n328:     }\n329: \n330:     if (existed)\n331:     {\n332:         mprf_p(T_(\"The abyss shimmers again as the detected \"\n333:               \"abyssal rune vanishes from your memory%1$s.\"),\n334:               detected ? T_(\" and reappears\") : \"\");\n335:     }\n336:     else if (detected)\n337:     {\n338:         mpr(T_(\"The abyssal matter surrounding you shimmers strangely.\"));\n339:         mpr(T_(\"You detect the abyssal rune!\"));\n340:     }\n341: \n342:     // XX could do the xom check from here?\n343: }\n344: \n345: static bool _abyss_place_rune_vault(const map_bitmask &abyss_genlevel_mask)\n346: {\n347:     bool result = false;\n348:     int tries = 10;\n349:     do\n350:     {\n351:         result = _abyss_place_vault_tagged(abyss_genlevel_mask, \"abyss_rune\");\n352:     }\n353:     while (!result && --tries);\n354: \n355:     return result;\n356: }",
    "method": "静态模板，无参数",
    "full_zh_display": "你周围的深渊物质奇怪地闪烁着。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  },
  {
    "english": "You detect the abyssal rune!",
    "zh_template": "你探测到了深渊符文！",
    "source": {
      "path": "crawl-ref/source/abyss.cc",
      "line": 339
    },
    "parameter_expressions": [
      "T_(\"You detect the abyssal rune!\")"
    ],
    "conditions_and_generation": "321:         // sets map knowledge by side effect if found\n322:         if (_sync_rune_knowledge(*ri))\n323:         {\n324:             detected = true;\n325:             cur_loc = *ri;\n326:             break;\n327:         }\n328:     }\n329: \n330:     if (existed)\n331:     {\n332:         mprf_p(T_(\"The abyss shimmers again as the detected \"\n333:               \"abyssal rune vanishes from your memory%1$s.\"),\n334:               detected ? T_(\" and reappears\") : \"\");\n335:     }\n336:     else if (detected)\n337:     {\n338:         mpr(T_(\"The abyssal matter surrounding you shimmers strangely.\"));\n339:         mpr(T_(\"You detect the abyssal rune!\"));\n340:     }\n341: \n342:     // XX could do the xom check from here?\n343: }\n344: \n345: static bool _abyss_place_rune_vault(const map_bitmask &abyss_genlevel_mask)\n346: {\n347:     bool result = false;\n348:     int tries = 10;\n349:     do\n350:     {\n351:         result = _abyss_place_vault_tagged(abyss_genlevel_mask, \"abyss_rune\");\n352:     }\n353:     while (!result && --tries);\n354: \n355:     return result;\n356: }\n357: ",
    "method": "静态模板，无参数",
    "full_zh_display": "你探测到了深渊符文！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/abyss.cc:341
crawl-ref/source/abyss.cc:347
crawl-ref/source/abyss.cc:348
crawl-ref/source/abyss.cc",
crawl-ref/source/abyss.cc",
crawl-ref/source/abyss.cc",
crawl-ref/source/abyss.cc",

中文全文
```text
深渊再次闪烁，你记忆中探测到的深渊符文消失了%1$s。

，又重新出现了

你周围的深渊物质奇怪地闪烁着。

你探测到了深渊符文！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "The abyss shimmers again as the detected abyssal rune vanishes from your memory%1$s.",
    "zh_template": "深渊再次闪烁，你记忆中探测到的深渊符文消失了%1$s。",
    "source": {
      "path": "crawl-ref/source/abyss.cc",
      "line": 341
    },
    "parameter_expressions": [
      "T_(\"The abyss shimmers again as the detected \"\n              \"abyssal rune vanishes from your memory%1$s.\")",
      "detected ? T_(\" and reappears\") : \"\""
    ],
    "conditions_and_generation": "323:     // now we need to check if a new or moved rune appeared\n324: \n325:     bool detected = false;\n326:     cur_loc = coord_def(-1,-1);\n327:     // check if a new one generated\n328:     for (rectangle_iterator ri(MAPGEN_BORDER); ri; ++ri)\n329:     {\n330:         // sets map knowledge by side effect if found\n331:         if (_sync_rune_knowledge(*ri))\n332:         {\n333:             detected = true;\n334:             cur_loc = *ri;\n335:             break;\n336:         }\n337:     }\n338: \n339:     if (existed)\n340:     {\n341:         mprf_p(T_(\"The abyss shimmers again as the detected \"\n342:               \"abyssal rune vanishes from your memory%1$s.\"),\n343:               detected ? T_(\" and reappears\") : \"\");\n344:     }\n345:     else if (detected)\n346:     {\n347:         mpr(T_(\"The abyssal matter surrounding you shimmers strangely.\"));\n348:         mpr(T_(\"You detect the abyssal rune!\"));\n349:     }\n350: \n351:     // XX could do the xom check from here?\n352: }\n353: \n354: static bool _abyss_place_rune_vault(const map_bitmask &abyss_genlevel_mask)\n355: {\n356:     bool result = false;\n357:     int tries = 10;\n358:     do\n359:     {\n360:         result = _abyss_place_vault_tagged(abyss_genlevel_mask, \"abyss_rune\");\n361:     }",
    "method": "参数文本还原",
    "full_zh_display": "深渊再次闪烁，你记忆中探测到的深渊符文消失了，又重新出现了。",
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "detected ? T_(\" and reappears\") : \"\"",
        "examples": [
          [
            "，又重新出现了",
            "按实参条件分支选择；完整条件：detected ? T_(\" and reappears\") : \"\""
          ],
          [
            "",
            "按实参条件分支选择；完整条件：detected ? T_(\" and reappears\") : \"\""
          ]
        ]
      }
    ],
    "branch_examples": [
      {
        "parameters": [
          {
            "expression": "detected ? T_(\" and reappears\") : \"\"",
            "value": "，又重新出现了",
            "source_and_state": "按实参条件分支选择；完整条件：detected ? T_(\" and reappears\") : \"\""
          }
        ],
        "full_zh_display": "深渊再次闪烁，你记忆中探测到的深渊符文消失了，又重新出现了。"
      },
      {
        "parameters": [
          {
            "expression": "detected ? T_(\" and reappears\") : \"\"",
            "value": "",
            "source_and_state": "按实参条件分支选择；完整条件：detected ? T_(\" and reappears\") : \"\""
          }
        ],
        "full_zh_display": "深渊再次闪烁，你记忆中探测到的深渊符文消失了。"
      }
    ],
    "formula": "按所列原始参数表达式和catalog参数示例逐位置替换；不增加冠词、量词或修正文案。"
  },
  {
    "english": " and reappears",
    "zh_template": "，又重新出现了",
    "source": {
      "path": "crawl-ref/source/abyss.cc",
      "line": 341
    },
    "parameter_expressions": [
      "T_(\"The abyss shimmers again as the detected \"\n              \"abyssal rune vanishes from your memory%1$s.\")",
      "detected ? T_(\" and reappears\") : \"\""
    ],
    "conditions_and_generation": "323:     // now we need to check if a new or moved rune appeared\n324: \n325:     bool detected = false;\n326:     cur_loc = coord_def(-1,-1);\n327:     // check if a new one generated\n328:     for (rectangle_iterator ri(MAPGEN_BORDER); ri; ++ri)\n329:     {\n330:         // sets map knowledge by side effect if found\n331:         if (_sync_rune_knowledge(*ri))\n332:         {\n333:             detected = true;\n334:             cur_loc = *ri;\n335:             break;\n336:         }\n337:     }\n338: \n339:     if (existed)\n340:     {\n341:         mprf_p(T_(\"The abyss shimmers again as the detected \"\n342:               \"abyssal rune vanishes from your memory%1$s.\"),\n343:               detected ? T_(\" and reappears\") : \"\");\n344:     }\n345:     else if (detected)\n346:     {\n347:         mpr(T_(\"The abyssal matter surrounding you shimmers strangely.\"));\n348:         mpr(T_(\"You detect the abyssal rune!\"));\n349:     }\n350: \n351:     // XX could do the xom check from here?\n352: }\n353: \n354: static bool _abyss_place_rune_vault(const map_bitmask &abyss_genlevel_mask)\n355: {\n356:     bool result = false;\n357:     int tries = 10;\n358:     do\n359:     {\n360:         result = _abyss_place_vault_tagged(abyss_genlevel_mask, \"abyss_rune\");\n361:     }",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。"
  },
  {
    "english": "The abyssal matter surrounding you shimmers strangely.",
    "zh_template": "你周围的深渊物质奇怪地闪烁着。",
    "source": {
      "path": "crawl-ref/source/abyss.cc",
      "line": 347
    },
    "parameter_expressions": [
      "T_(\"The abyssal matter surrounding you shimmers strangely.\")"
    ],
    "conditions_and_generation": "329:     {\n330:         // sets map knowledge by side effect if found\n331:         if (_sync_rune_knowledge(*ri))\n332:         {\n333:             detected = true;\n334:             cur_loc = *ri;\n335:             break;\n336:         }\n337:     }\n338: \n339:     if (existed)\n340:     {\n341:         mprf_p(T_(\"The abyss shimmers again as the detected \"\n342:               \"abyssal rune vanishes from your memory%1$s.\"),\n343:               detected ? T_(\" and reappears\") : \"\");\n344:     }\n345:     else if (detected)\n346:     {\n347:         mpr(T_(\"The abyssal matter surrounding you shimmers strangely.\"));\n348:         mpr(T_(\"You detect the abyssal rune!\"));\n349:     }\n350: \n351:     // XX could do the xom check from here?\n352: }\n353: \n354: static bool _abyss_place_rune_vault(const map_bitmask &abyss_genlevel_mask)\n355: {\n356:     bool result = false;\n357:     int tries = 10;\n358:     do\n359:     {\n360:         result = _abyss_place_vault_tagged(abyss_genlevel_mask, \"abyss_rune\");\n361:     }\n362:     while (!result && --tries);\n363: \n364:     return result;\n365: }",
    "method": "静态模板，无参数",
    "full_zh_display": "你周围的深渊物质奇怪地闪烁着。",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  },
  {
    "english": "You detect the abyssal rune!",
    "zh_template": "你探测到了深渊符文！",
    "source": {
      "path": "crawl-ref/source/abyss.cc",
      "line": 348
    },
    "parameter_expressions": [
      "T_(\"You detect the abyssal rune!\")"
    ],
    "conditions_and_generation": "330:         // sets map knowledge by side effect if found\n331:         if (_sync_rune_knowledge(*ri))\n332:         {\n333:             detected = true;\n334:             cur_loc = *ri;\n335:             break;\n336:         }\n337:     }\n338: \n339:     if (existed)\n340:     {\n341:         mprf_p(T_(\"The abyss shimmers again as the detected \"\n342:               \"abyssal rune vanishes from your memory%1$s.\"),\n343:               detected ? T_(\" and reappears\") : \"\");\n344:     }\n345:     else if (detected)\n346:     {\n347:         mpr(T_(\"The abyssal matter surrounding you shimmers strangely.\"));\n348:         mpr(T_(\"You detect the abyssal rune!\"));\n349:     }\n350: \n351:     // XX could do the xom check from here?\n352: }\n353: \n354: static bool _abyss_place_rune_vault(const map_bitmask &abyss_genlevel_mask)\n355: {\n356:     bool result = false;\n357:     int tries = 10;\n358:     do\n359:     {\n360:         result = _abyss_place_vault_tagged(abyss_genlevel_mask, \"abyss_rune\");\n361:     }\n362:     while (!result && --tries);\n363: \n364:     return result;\n365: }\n366: ",
    "method": "静态模板，无参数",
    "full_zh_display": "你探测到了深渊符文！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

4. 独立语义判断与还原
可选后缀有/无都还原：深渊再次闪烁，你记忆中探测到的深渊符文消失了，又重新出现了。/…消失了。；无重复句号，重现条件保留。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-6-01

1. 完整英文
```text
%1$s shimmers and splits apart.
```

2–3. stable 消费者与参数证据

crawl-ref/source/timed-effects.cc:365
crawl-ref/source/timed-effects.cc",

中文全文
```text
%1$s闪烁着分裂开来。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "%1$s shimmers and splits apart.",
    "zh_template": "%1$s闪烁着分裂开来。",
    "source": {
      "path": "crawl-ref/source/timed-effects.cc",
      "line": 365
    },
    "parameter_expressions": [
      "T_(\"%1$s shimmers and splits apart.\")",
      "mon->name(DESC_THE).c_str()"
    ],
    "conditions_and_generation": "347:         const int num = 2 + one_chance_in(3);\n348:         for (int i = 0; i < num; ++i)\n349:         {\n350:             if (_multiplicity_clone(mon))\n351:             {\n352:                 if (you.can_see(*mon))\n353:                     seen = true;\n354:                 did_clone = true;\n355:             }\n356:         }\n357: \n358:         // Apply cooldown.\n359:         if (did_clone)\n360:             you.props[MULTIPLICITY_TIME_KEY] = you.elapsed_time + random_range(270, 600);\n361: \n362:         if (seen)\n363:         {\n364:             flash_tile(mon->pos(), LIGHTBLUE, 150);\n365:             mprf_p(T_(\"%1$s shimmers and splits apart.\"), mon->name(DESC_THE).c_str());\n366:         }\n367:     }\n368: \n369:     if (you.has_bane(BANE_MORTALITY)\n370:         && you.elapsed_time > you.props[MORTALITY_TIME_KEY].get_int()\n371:         && you.hp * 10 <= you.hp_max * 4)\n372:     {\n373:         _maybe_mortality_summon();\n374:     }\n375: }\n376: \n377: // Get around C++ dividing integers towards 0.\n378: static int _div(int num, int denom)\n379: {\n380:     div_t res = div(num, denom);\n381:     return res.rem >= 0 ? res.quot : res.quot - 1;\n382: }\n383: ",
    "method": "参数文本还原",
    "full_zh_display": "兽人闪烁着分裂开来。",
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "mon->name(DESC_THE).c_str()",
        "examples": [
          [
            "兽人",
            "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          ]
        ]
      }
    ],
    "branch_examples": [
      {
        "parameters": [
          {
            "expression": "mon->name(DESC_THE).c_str()",
            "value": "兽人",
            "source_and_state": "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          }
        ],
        "full_zh_display": "兽人闪烁着分裂开来。"
      }
    ],
    "formula": "按所列原始参数表达式和catalog参数示例逐位置替换；不增加冠词、量词或修正文案。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/timed-effects.cc:365
crawl-ref/source/timed-effects.cc",

中文全文
```text
%1$s闪烁着分裂开来。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "%1$s shimmers and splits apart.",
    "zh_template": "%1$s闪烁着分裂开来。",
    "source": {
      "path": "crawl-ref/source/timed-effects.cc",
      "line": 365
    },
    "parameter_expressions": [
      "T_(\"%1$s shimmers and splits apart.\")",
      "mon->name(DESC_THE).c_str()"
    ],
    "conditions_and_generation": "347:         const int num = 2 + one_chance_in(3);\n348:         for (int i = 0; i < num; ++i)\n349:         {\n350:             if (_multiplicity_clone(mon))\n351:             {\n352:                 if (you.can_see(*mon))\n353:                     seen = true;\n354:                 did_clone = true;\n355:             }\n356:         }\n357: \n358:         // Apply cooldown.\n359:         if (did_clone)\n360:             you.props[MULTIPLICITY_TIME_KEY] = you.elapsed_time + random_range(270, 600);\n361: \n362:         if (seen)\n363:         {\n364:             flash_tile(mon->pos(), LIGHTBLUE, 150);\n365:             mprf_p(T_(\"%1$s shimmers and splits apart.\"), mon->name(DESC_THE).c_str());\n366:         }\n367:     }\n368: \n369:     if (you.has_bane(BANE_MORTALITY)\n370:         && you.elapsed_time > you.props[MORTALITY_TIME_KEY].get_int()\n371:         && you.hp * 10 <= you.hp_max * 4)\n372:     {\n373:         _maybe_mortality_summon();\n374:     }\n375: }\n376: \n377: // Get around C++ dividing integers towards 0.\n378: static int _div(int num, int denom)\n379: {\n380:     div_t res = div(num, denom);\n381:     return res.rem >= 0 ? res.quot : res.quot - 1;\n382: }\n383: ",
    "method": "参数文本还原",
    "full_zh_display": "兽人闪烁着分裂开来。",
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "mon->name(DESC_THE).c_str()",
        "examples": [
          [
            "兽人",
            "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          ]
        ]
      }
    ],
    "branch_examples": [
      {
        "parameters": [
          {
            "expression": "mon->name(DESC_THE).c_str()",
            "value": "兽人",
            "source_and_state": "以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。"
          }
        ],
        "full_zh_display": "兽人闪烁着分裂开来。"
      }
    ],
    "formula": "按所列原始参数表达式和catalog参数示例逐位置替换；不增加冠词、量词或修正文案。"
  }
]
```

4. 独立语义判断与还原
名称由 DESC_THE 提供，例兽人闪烁着分裂开来。；不增所有格。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-2-08

1. 完整英文
```text
Fires a bolt of dispelling energy at a targeted creature, possibly removing
some of its enchantments.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:4934
crawl-ref/source/spl-data.h",

中文全文
```text
向目标生物发射一道驱散能量，可能移除其部分魔法效果。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "向目标生物发射一道驱散能量，可能移除其部分魔法效果。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:5471
crawl-ref/source/spl-data.h",

中文全文
```text
向目标生物发射一道可穿透目标的驱散能量之箭，可能移除其部分魔法效果。
```

trunk 完整英文
```text
Fires a penetrating bolt of dispelling energy at a targeted creature, possibly
removing some of its enchantments.

crawl-ref/source/describe.cc:5471
```cpp
5461:  * @param mon_owner     If this spell is being examined from a monster's
5462:  *                      description, 'spell' is that monster. Else, null.
5463:  * @param description   Set to the description & details of the spell.
5464:  */
5465: static void _get_spell_description(const spell_type spell,
5466:                                   const monster_info *mon_owner,
5467:                                   string &description)
5468: {
5469:     description.reserve(500);
5470:
5471:     const string long_descrip = getLongDescription(string(spell_english_name(spell))
5472:                                                    + " spell");
5473:
5474:     if (!long_descrip.empty())
5475:         description += long_descrip;
5476:     else
5477:     {
5478:         description += T_("This spell has no description. Casting it may therefore be unwise. ");
5479: #ifdef DEBUG
5480:                        T_("Better go fix it.");
5481: #else
```


具体键生成证据：
```json
[
  {
    "path": "crawl-ref/source/spl-data.h",
    "line": 1457,
    "statement": "SPELL_QUICKSILVER_BOLT, \"Quicksilver Bolt\",",
    "snippet": "1447:     spschool::none,\n1448:     spflag::monster,\n1449:     1,\n1450:     0,\n1451:     -1, -1,\n1452:     0,\n1453:     TILEG_CANTRIP,\n1454: },\n1455: \n1456: {\n1457:     SPELL_QUICKSILVER_BOLT, \"Quicksilver Bolt\",\n1458:     spschool::conjuration,\n1459:     spflag::dir_or_target | spflag::needs_tracer | spflag::not_self,\n1460:     5,\n1461:     200,\n1462:     LOS_RADIUS, LOS_RADIUS,\n1463:     0,\n1464:     TILEG_QUICKSILVER_BOLT,\n1465: },\n1466: \n1467: {"
  }
]
```
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "向目标生物发射一道可穿透目标的驱散能量之箭，可能移除其部分魔法效果。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
trunk 新增穿透限定在中文体现；stable 无此限定，分别成立。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-2-07

1. 完整英文
```text
Releases a thick cloud of ink to obscure vision.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:4934
crawl-ref/source/spl-data.h",

中文全文
```text
释出浓厚的墨云，模糊视线。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "释出浓厚的墨云，模糊视线。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:5471
crawl-ref/source/spl-data.h",

中文全文
```text
释出浓厚的墨云，模糊视线。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "释出浓厚的墨云，模糊视线。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
浓墨云遮蔽视线，完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-3-09

1. 完整英文
```text
A huge, three-headed, winged arch-demon, guardian of the four Hells. Legends
say that his silver horn can summon terrible beasts to aid him in battle.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:7279
crawl-ref/source/describe.cc:7270
crawl-ref/source/dat/mons/geryon.yaml",

中文全文
```text
一个巨大的三头有翼大恶魔，是四个地狱的守卫者。
传说他的银色号角可以召唤可怕的野兽来助他战斗。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一个巨大的三头有翼大恶魔，是四个地狱的守卫者。\n传说他的银色号角可以召唤可怕的野兽来助他战斗。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:7967
crawl-ref/source/describe.cc:7958
crawl-ref/source/dat/mons/geryon.yaml",

中文全文
```text
一个巨大的三头有翼大恶魔，是四个地狱的守卫者。
传说他的银色号角可以召唤可怕的野兽来助他战斗。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "一个巨大的三头有翼大恶魔，是四个地狱的守卫者。\n传说他的银色号角可以召唤可怕的野兽来助他战斗。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
三头有翼巨魔、四地狱守卫及银角召兽完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-6-07

1. 完整英文
```text
Suddenly a wall slides open!
```

2–3. stable 消费者与参数证据

crawl-ref/source/dat/des/traps/rats_trap.des:42
crawl-ref/source/dat/des/traps/rats_trap.des",

中文全文
```text
一面墙突然滑开了！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "Suddenly a wall slides open!",
    "zh_template": "一面墙突然滑开了！",
    "source": {
      "path": "crawl-ref/source/dat/des/traps/rats_trap.des",
      "line": 42
    },
    "parameter_expressions": [
      "crawl.t_(\"Suddenly a wall slides open!\")"
    ],
    "conditions_and_generation": "26:   end\n27: \n28:   data.triggered = true\n29:   dgn.grid(x, y, \"floor\")\n30: \n31:   for replica in iter.replica_iterator(\"hole\", 1) do\n32:       if not dgn.is_passable(replica.x,replica.y) then\n33:         dgn.terrain_changed(replica.x, replica.y, \"floor\", false)\n34:         dgn.create_item(replica.x, replica.y, \"stone q:3 / stone q:2 / stone\")\n35:       else\n36:         crawl.mpr(crawl.t_(\"You hear a click.\"))\n37:         return\n38:       end\n39:   end\n40: \n41:   crawl.mpr(crawl.t_(\"You step on to a pressure plate.\"))\n42:   crawl.mpr(crawl.t_(\"Suddenly a wall slides open!\"))\n43: \n44: end\n45: \n46: }}\n47: \n48: NAME:   dk_rats_in_the_wall\n49: DEPTH:  D:4-10\n50: TAGS:   no_monster_gen\n51: KPROP:  R = no_tele_into\n52: MONS:   generate_awake rat, generate_awake river rat\n53: SUBST:  R = 112\n54: KFEAT:  ^ = pressure plate trap\n55: # some chance for a big hole in the wall\n56: : if crawl.one_chance_in(4) then\n57: SUBST:  Z : z\n58: : else",
    "method": "静态模板，无参数",
    "full_zh_display": "一面墙突然滑开了！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/dat/des/traps/rats_trap.des:42
crawl-ref/source/dat/des/traps/rats_trap.des",

中文全文
```text
一面墙突然滑开了！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "Suddenly a wall slides open!",
    "zh_template": "一面墙突然滑开了！",
    "source": {
      "path": "crawl-ref/source/dat/des/traps/rats_trap.des",
      "line": 42
    },
    "parameter_expressions": [
      "crawl.t_(\"Suddenly a wall slides open!\")"
    ],
    "conditions_and_generation": "26:   end\n27: \n28:   data.triggered = true\n29:   dgn.grid(x, y, \"floor\")\n30: \n31:   for replica in iter.replica_iterator(\"hole\", 1) do\n32:       if not dgn.is_passable(replica.x,replica.y) then\n33:         dgn.terrain_changed(replica.x, replica.y, \"floor\", false)\n34:         dgn.create_item(replica.x, replica.y, \"stone q:3 / stone q:2 / stone\")\n35:       else\n36:         crawl.mpr(crawl.t_(\"You hear a click.\"))\n37:         return\n38:       end\n39:   end\n40: \n41:   crawl.mpr(crawl.t_(\"You step on to a pressure plate.\"))\n42:   crawl.mpr(crawl.t_(\"Suddenly a wall slides open!\"))\n43: \n44: end\n45: \n46: }}\n47: \n48: NAME:   dk_rats_in_the_wall\n49: DEPTH:  D:4-10\n50: TAGS:   no_monster_gen\n51: KPROP:  R = no_tele_into\n52: MONS:   generate_awake rat, generate_awake river rat\n53: SUBST:  R = 112\n54: KFEAT:  ^ = trap_pressure_plate\n55: # some chance for a big hole in the wall\n56: : if crawl.one_chance_in(4) then\n57: SUBST:  Z : z\n58: : else",
    "method": "静态模板，无参数",
    "full_zh_display": "一面墙突然滑开了！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

4. 独立语义判断与还原
墙壁滑开、突然发生完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-1-09

1. 完整英文
```text
An ancient artefact of Okawaru, these woolen robes were lost when a former
champion failed a duel. Its enchantments increase in power when the wearer
emerges victorious from threatening combat, but resorting to the use of scrolls
or potions for assistance causes them to fade away again.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:2869
crawl-ref/source/art-data.txt",

中文全文
```text
这件羊毛长袍是奥卡瓦鲁的一件古代神器，前冠军在决斗失败后遗落了它。
当穿戴者在有威胁的战斗中获胜时，其附着的魔力会增强，
但若在有敌对怪物可见时求助于卷轴或药水，这些加成便会再次消失。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "这件羊毛长袍是奥卡瓦鲁的一件古代神器，前冠军在决斗失败后遗落了它。\n当穿戴者在有威胁的战斗中获胜时，其附着的魔力会增强，\n但若在有敌对怪物可见时求助于卷轴或药水，这些加成便会再次消失。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:3141
crawl-ref/source/art-data.txt",

中文全文
```text
这件羊毛长袍是奥卡瓦鲁的一件古代神器，前冠军在决斗失败后遗落了它。
当穿戴者在有威胁的战斗中获胜时，其附着的魔力会增强，
但若在有敌对怪物可见时求助于卷轴或药水，这些加成便会再次消失。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "这件羊毛长袍是奥卡瓦鲁的一件古代神器，前冠军在决斗失败后遗落了它。\n当穿戴者在有威胁的战斗中获胜时，其附着的魔力会增强，\n但若在有敌对怪物可见时求助于卷轴或药水，这些加成便会再次消失。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
附魔随威胁战斗获胜增强、卷轴药水使加成消退；中文增加敌对怪物可见条件与生产 item-use.cc:2065-2067、3317-3322 一致，不按字面对照误报错误。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-5-07

1. 完整英文
```text
Wearing heavy body armour or using a shield, especially a large one, can
severely hamper your spellcasting abilities. You can check the effect of this
by comparing the failure rates on the <w>$cmd[CMD_CAST_SPELL]\?</w> screen with
and without the item being worn.
```

2–3. stable 消费者与参数证据

crawl-ref/source/hints.cc:1710
crawl-ref/source/hints.cc:401
crawl-ref/source/hints.cc:483
crawl-ref/source/hints.cc:2884
crawl-ref/source/hints.cc",
crawl-ref/source/hints.cc",

中文全文
```text
穿戴重型身体护甲或使用盾牌，尤其是大型盾牌，会严重妨碍你的施法能力。
你可以通过比较 <w>$cmd[CMD_CAST_SPELL]\?</w> 屏幕上穿戴和不穿戴该物品时
的失败率来检查其影响。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "zh_body": "穿戴重型身体护甲或使用盾牌，尤其是大型盾牌，会严重妨碍你的施法能力。\n你可以通过比较 <w>$cmd[CMD_CAST_SPELL]\\?</w> 屏幕上穿戴和不穿戴该物品时\n的失败率来检查其影响。",
    "reason": "TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。",
    "parameter_source": "具体提示键/事件枚举由所列生产调用传入_get_hint/tutorial_msg→getHintString→HintsDB。",
    "key_generation_evidence": [
      {
        "path": "crawl-ref/source/hints.cc",
        "line": 1710,
        "statement": "print_hint(\"HINT_MISCAST_ARMOUR\");",
        "snippet": "1700:             DELAY_EVENT;\n1701: \n1702:         if (!crawl_state.game_is_hints())\n1703:         {\n1704:             print_hint(\"HINT_SPELL_MISCAST_EFFECTS\");\n1705:             break;\n1706:         }\n1707:         print_hint(\"HINT_YOU_MISCAST\");\n1708: \n1709:         if (!player_effectively_in_light_armour() || you.shield())\n1710:             print_hint(\"HINT_MISCAST_ARMOUR\");\n1711: \n1712:         print_hint(\"HINT_MISCAST_CONTAMINATION_AND_MP\");\n1713:         break;\n1714:     }\n1715: \n1716:     case HINT_GLOWING:\n1717:         print_hint(\"HINT_GLOWING\");\n1718: \n1719:         if (!player_harmful_contamination())\n1720:             print_hint(\"HINT_CONTAMINATION_MILD\");"
      }
    ]
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/hints.cc:1608
crawl-ref/source/hints.cc:402
crawl-ref/source/hints.cc:484
crawl-ref/source/hints.cc:2386
crawl-ref/source/hints.cc",
crawl-ref/source/hints.cc",

中文全文
```text
穿戴重型身体护甲或使用盾牌，尤其是大型盾牌，会严重妨碍你的施法能力。
你可以通过比较 <w>$cmd[CMD_CAST_SPELL]\?</w> 屏幕上穿戴和不穿戴该物品时
的失败率来检查其影响。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "zh_body": "穿戴重型身体护甲或使用盾牌，尤其是大型盾牌，会严重妨碍你的施法能力。\n你可以通过比较 <w>$cmd[CMD_CAST_SPELL]\\?</w> 屏幕上穿戴和不穿戴该物品时\n的失败率来检查其影响。",
    "reason": "TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。",
    "parameter_source": "具体提示键/事件枚举由所列生产调用传入_get_hint/tutorial_msg→getHintString→HintsDB。",
    "key_generation_evidence": [
      {
        "path": "crawl-ref/source/hints.cc",
        "line": 1608,
        "statement": "print_hint(\"HINT_MISCAST_ARMOUR\");",
        "snippet": "1598:             DELAY_EVENT;\n1599: \n1600:         if (!crawl_state.game_is_hints())\n1601:         {\n1602:             print_hint(\"HINT_SPELL_MISCAST_EFFECTS\");\n1603:             break;\n1604:         }\n1605:         print_hint(\"HINT_YOU_MISCAST\");\n1606: \n1607:         if (!player_effectively_in_light_armour() || you.shield())\n1608:             print_hint(\"HINT_MISCAST_ARMOUR\");\n1609: \n1610:         print_hint(\"HINT_MISCAST_CONTAMINATION_AND_MP\");\n1611:         break;\n1612:     }\n1613: \n1614:     case HINT_GLOWING:\n1615:         print_hint(\"HINT_GLOWING\");\n1616: \n1617:         if (!player_harmful_contamination())\n1618:             print_hint(\"HINT_CONTAMINATION_MILD\");"
      }
    ]
  }
]
```

4. 独立语义判断与还原
重甲和盾牌尤其大盾妨碍施法、穿戴前后比较失败率完整，命令转义保持。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-4-03

1. 完整英文
```text
You hear the singing of a choir!

You are suddenly bathed in radiance!
```

2–3. stable 消费者与参数证据

crawl-ref/source/god-abil.cc:1338
crawl-ref/source/god-abil.cc:1340
crawl-ref/source/god-abil.cc",
crawl-ref/source/god-abil.cc",

中文全文
```text
你听到了唱诗班的歌声！

你突然沐浴在光辉之中！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You hear the singing of a choir!",
    "zh_template": "你听到了唱诗班的歌声！",
    "source": {
      "path": "crawl-ref/source/god-abil.cc",
      "line": 1338
    },
    "parameter_expressions": [
      "MSGCH_SOUND",
      "T_(\"You hear the singing of a choir!\")"
    ],
    "conditions_and_generation": "1320: \n1321:     if (mons->friendly() || mons->good_neutral())\n1322:     {\n1323:         mpr(T_(\"You cannot imprison law-abiding creatures!\"));\n1324:         return spret::abort;\n1325:     }\n1326: \n1327:     int power = 3 + (roll_dice(5, you.skill(SK_INVOCATIONS, 5) + 12) / 26);\n1328: \n1329:     return cast_tomb(power, mons, -GOD_ZIN, fail);\n1330: }\n1331: \n1332: void zin_sanctuary()\n1333: {\n1334:     ASSERT(!env.sanctuary_time);\n1335: \n1336:     // Yes, shamelessly stolen from NetHack...\n1337:     if (!silenced(you.pos())) // How did you manage that?\n1338:         mprf(MSGCH_SOUND, T_(\"You hear the singing of a choir!\"));\n1339:     else\n1340:         mpr(T_(\"You are suddenly bathed in radiance!\"));\n1341: \n1342:     flash_view(UA_PLAYER, WHITE);\n1343:     // Allow extra time for the flash to linger.\n1344:     scaled_delay(1000);\n1345: \n1346:     // Pets stop attacking and converge on you.\n1347:     you.pet_target = MHITYOU;\n1348:     create_sanctuary(you.pos(), 7 + you.skill_rdiv(SK_INVOCATIONS) / 2);\n1349: }\n1350: \n1351: void tso_divine_shield()\n1352: {\n1353:     if (!you.duration[DUR_DIVINE_SHIELD])\n1354:         mpr(T_(\"A divine shield appears in front of you!\"));\n1355:     else\n1356:         mpr(T_(\"Your divine shield is renewed.\"));",
    "method": "静态模板，无参数",
    "full_zh_display": "你听到了唱诗班的歌声！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  },
  {
    "english": "You are suddenly bathed in radiance!",
    "zh_template": "你突然沐浴在光辉之中！",
    "source": {
      "path": "crawl-ref/source/god-abil.cc",
      "line": 1340
    },
    "parameter_expressions": [
      "T_(\"You are suddenly bathed in radiance!\")"
    ],
    "conditions_and_generation": "1322:     {\n1323:         mpr(T_(\"You cannot imprison law-abiding creatures!\"));\n1324:         return spret::abort;\n1325:     }\n1326: \n1327:     int power = 3 + (roll_dice(5, you.skill(SK_INVOCATIONS, 5) + 12) / 26);\n1328: \n1329:     return cast_tomb(power, mons, -GOD_ZIN, fail);\n1330: }\n1331: \n1332: void zin_sanctuary()\n1333: {\n1334:     ASSERT(!env.sanctuary_time);\n1335: \n1336:     // Yes, shamelessly stolen from NetHack...\n1337:     if (!silenced(you.pos())) // How did you manage that?\n1338:         mprf(MSGCH_SOUND, T_(\"You hear the singing of a choir!\"));\n1339:     else\n1340:         mpr(T_(\"You are suddenly bathed in radiance!\"));\n1341: \n1342:     flash_view(UA_PLAYER, WHITE);\n1343:     // Allow extra time for the flash to linger.\n1344:     scaled_delay(1000);\n1345: \n1346:     // Pets stop attacking and converge on you.\n1347:     you.pet_target = MHITYOU;\n1348:     create_sanctuary(you.pos(), 7 + you.skill_rdiv(SK_INVOCATIONS) / 2);\n1349: }\n1350: \n1351: void tso_divine_shield()\n1352: {\n1353:     if (!you.duration[DUR_DIVINE_SHIELD])\n1354:         mpr(T_(\"A divine shield appears in front of you!\"));\n1355:     else\n1356:         mpr(T_(\"Your divine shield is renewed.\"));\n1357: \n1358:     const int charges = 3 + you.skill_rdiv(SK_INVOCATIONS, 2, 5);",
    "method": "静态模板，无参数",
    "full_zh_display": "你突然沐浴在光辉之中！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/god-abil.cc:1330
crawl-ref/source/god-abil.cc:1332
crawl-ref/source/god-abil.cc",
crawl-ref/source/god-abil.cc",

中文全文
```text
你听到了唱诗班的歌声！

你突然沐浴在光辉之中！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "You hear the singing of a choir!",
    "zh_template": "你听到了唱诗班的歌声！",
    "source": {
      "path": "crawl-ref/source/god-abil.cc",
      "line": 1330
    },
    "parameter_expressions": [
      "MSGCH_SOUND",
      "T_(\"You hear the singing of a choir!\")"
    ],
    "conditions_and_generation": "1312: \n1313:     if (mons->friendly() || mons->good_neutral())\n1314:     {\n1315:         mpr(T_(\"You cannot imprison law-abiding creatures!\"));\n1316:         return spret::abort;\n1317:     }\n1318: \n1319:     int power = 3 + (roll_dice(5, you.skill(SK_INVOCATIONS, 5) + 12) / 26);\n1320: \n1321:     return cast_tomb(power, mons, -GOD_ZIN, fail);\n1322: }\n1323: \n1324: void zin_sanctuary()\n1325: {\n1326:     ASSERT(!env.sanctuary_time);\n1327: \n1328:     // Yes, shamelessly stolen from NetHack...\n1329:     if (!silenced(you.pos())) // How did you manage that?\n1330:         mprf(MSGCH_SOUND, T_(\"You hear the singing of a choir!\"));\n1331:     else\n1332:         mpr(T_(\"You are suddenly bathed in radiance!\"));\n1333: \n1334:     flash_view(UA_PLAYER, WHITE);\n1335:     // Allow extra time for the flash to linger.\n1336:     scaled_delay(1000);\n1337: \n1338:     // Pets stop attacking and converge on you.\n1339:     you.pet_target = MHITYOU;\n1340:     create_sanctuary(you.pos(), 7 + you.skill_rdiv(SK_INVOCATIONS) / 2);\n1341: }\n1342: \n1343: void tso_divine_shield()\n1344: {\n1345:     if (!you.duration[DUR_DIVINE_SHIELD])\n1346:         mpr(T_(\"A divine shield appears in front of you!\"));\n1347:     else\n1348:         mpr(T_(\"Your divine shield is renewed.\"));",
    "method": "静态模板，无参数",
    "full_zh_display": "你听到了唱诗班的歌声！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  },
  {
    "english": "You are suddenly bathed in radiance!",
    "zh_template": "你突然沐浴在光辉之中！",
    "source": {
      "path": "crawl-ref/source/god-abil.cc",
      "line": 1332
    },
    "parameter_expressions": [
      "T_(\"You are suddenly bathed in radiance!\")"
    ],
    "conditions_and_generation": "1314:     {\n1315:         mpr(T_(\"You cannot imprison law-abiding creatures!\"));\n1316:         return spret::abort;\n1317:     }\n1318: \n1319:     int power = 3 + (roll_dice(5, you.skill(SK_INVOCATIONS, 5) + 12) / 26);\n1320: \n1321:     return cast_tomb(power, mons, -GOD_ZIN, fail);\n1322: }\n1323: \n1324: void zin_sanctuary()\n1325: {\n1326:     ASSERT(!env.sanctuary_time);\n1327: \n1328:     // Yes, shamelessly stolen from NetHack...\n1329:     if (!silenced(you.pos())) // How did you manage that?\n1330:         mprf(MSGCH_SOUND, T_(\"You hear the singing of a choir!\"));\n1331:     else\n1332:         mpr(T_(\"You are suddenly bathed in radiance!\"));\n1333: \n1334:     flash_view(UA_PLAYER, WHITE);\n1335:     // Allow extra time for the flash to linger.\n1336:     scaled_delay(1000);\n1337: \n1338:     // Pets stop attacking and converge on you.\n1339:     you.pet_target = MHITYOU;\n1340:     create_sanctuary(you.pos(), 7 + you.skill_rdiv(SK_INVOCATIONS) / 2);\n1341: }\n1342: \n1343: void tso_divine_shield()\n1344: {\n1345:     if (!you.duration[DUR_DIVINE_SHIELD])\n1346:         mpr(T_(\"A divine shield appears in front of you!\"));\n1347:     else\n1348:         mpr(T_(\"Your divine shield is renewed.\"));\n1349: \n1350:     const int charges = 3 + you.skill_rdiv(SK_INVOCATIONS, 2, 5);",
    "method": "静态模板，无参数",
    "full_zh_display": "你突然沐浴在光辉之中！",
    "formula": "catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。"
  }
]
```

4. 独立语义判断与还原
非沉默唱诗班、沉默光辉两分支正确，不用声音去还原沉默分支。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-2-02

1. 完整英文
```text
A fragment of %s is already outside their body!
```

2–3. stable 消费者与参数证据

crawl-ref/source/spl-summoning.cc:3505
crawl-ref/source/spl-summoning.cc",

中文全文
```text
%s的灵魂碎片已经在其体外了！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "A fragment of %s is already outside their body!",
    "zh_template": "%s的灵魂碎片已经在其体外了！",
    "source": {
      "path": "crawl-ref/source/spl-summoning.cc",
      "line": 3505
    },
    "parameter_expressions": [
      "T_(\"A fragment of %s is already outside their body!\")",
      "victim.name(DESC_THE).c_str()"
    ],
    "conditions_and_generation": "3487: \n3488:     if (agent.is_player())\n3489:         you.duration[DUR_HELLFIRE_MORTAR_COOLDOWN] = dur;\n3490: \n3491:     return spret::success;\n3492: }\n3493: \n3494: bool make_soul_wisp(const actor& agent, actor& victim)\n3495: {\n3496:     if (victim.is_monster() && !mons_can_be_spectralised(*victim.as_monster(), true))\n3497:         return false;\n3498: \n3499:     // Don't try to create a wisp from a monster who's already had one made from\n3500:     // them. (This causes weird messaging and removes the Weak effect).\n3501:     if (victim.is_monster() && victim.props.exists(SOUL_SPLINTERED_KEY))\n3502:     {\n3503:         if (agent.is_player() && victim.observable())\n3504:         {\n3505:             mprf(T_(\"A fragment of %s is already outside their body!\"),\n3506:                     victim.name(DESC_THE).c_str());\n3507:         }\n3508:         return false;\n3509:     }\n3510: \n3511:     mgen_data mg = _summon_data(agent, MONS_SOUL_WISP, summ_dur(2), SPELL_SOUL_SPLINTER);\n3512:     mg.pos = victim.pos();\n3513:     mg.set_range(1);\n3514:     mg.flags |= MG_SEE_SUMMONER;\n3515: \n3516:     // Damage improves when extracted from stronger enemies, but they are always fragile.\n3517:     mg.hd = 2 + div_rand_round(victim.get_experience_level(), 2);\n3518:     mg.hp = random_range(5, 8);\n3519: \n3520:     if (monster* wisp = create_monster(mg))\n3521:     {\n3522:         if (you.see_cell(victim.pos()))\n3523:         {\n3524:             mprf(T_(\"A fragment of %s soul is dislodged from %s body.\"),",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "victim.name(DESC_THE).c_str()",
        "examples": []
      }
    ]
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/spl-summoning.cc:3583
crawl-ref/source/spl-summoning.cc",

中文全文
```text
%s的灵魂碎片已经在其体外了！
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "english": "A fragment of %s is already outside their body!",
    "zh_template": "%s的灵魂碎片已经在其体外了！",
    "source": {
      "path": "crawl-ref/source/spl-summoning.cc",
      "line": 3583
    },
    "parameter_expressions": [
      "T_(\"A fragment of %s is already outside their body!\")",
      "victim.name(DESC_THE).c_str()"
    ],
    "conditions_and_generation": "3565: \n3566:     if (agent.is_player())\n3567:         you.duration[DUR_HELLFIRE_MORTAR_COOLDOWN] = lava_length * BASELINE_DELAY + hellfire_mortar_cooldown_length(lava_length);\n3568: \n3569:     return spret::success;\n3570: }\n3571: \n3572: bool make_soul_wisp(const actor& agent, actor& victim)\n3573: {\n3574:     if (victim.is_monster() && !mons_can_be_spectralised(*victim.as_monster(), true))\n3575:         return false;\n3576: \n3577:     // Don't try to create a wisp from a monster who's already had one made from\n3578:     // them. (This causes weird messaging and removes the Weak effect).\n3579:     if (victim.is_monster() && victim.props.exists(SOUL_SPLINTERED_KEY))\n3580:     {\n3581:         if (agent.is_player() && victim.observable())\n3582:         {\n3583:             mprf(T_(\"A fragment of %s is already outside their body!\"),\n3584:                     victim.name(DESC_THE).c_str());\n3585:         }\n3586:         return false;\n3587:     }\n3588: \n3589:     mgen_data mg = _summon_data(agent, MONS_SOUL_WISP, summ_dur(2), SPELL_SOUL_SPLINTER);\n3590:     mg.pos = victim.pos();\n3591:     mg.set_range(1);\n3592:     mg.flags |= MG_SEE_SUMMONER;\n3593: \n3594:     // Damage improves when extracted from stronger enemies, but they are always fragile.\n3595:     mg.hd = 2 + div_rand_round(victim.get_experience_level(), 2);\n3596:     mg.hp = random_range(5, 8);\n3597: \n3598:     if (monster* wisp = create_monster(mg))\n3599:     {\n3600:         if (you.see_cell(victim.pos()))\n3601:         {\n3602:             mprf(T_(\"A fragment of %s soul is dislodged from %s body.\"),",
    "method": "需要运行时或布局才能确定",
    "full_zh_display": null,
    "reason": "未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。",
    "resolved_parameter_examples": [
      {
        "expression": "victim.name(DESC_THE).c_str()",
        "examples": []
      }
    ]
  }
]
```

4. 独立语义判断与还原
victim.name(DESC_THE) 为名称而非所有格，例兽人的灵魂碎片已经在其体外了！；模板补的正确，已有碎片的限制完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok


## R4-2-09

1. 完整英文
```text
Transmutes a small amount of the air around a target into toxic vapours,
poisoning anyone unfortunate enough to breathe them in. The quantity of air
affected is small and it will not persist beyond the turn in which it is cast.

It cannot affect those with any resistance to poison.
```

2–3. stable 消费者与参数证据

crawl-ref/source/describe.cc:4934
crawl-ref/source/spl-data.h",

中文全文
```text
将目标周围的少量空气转化为有毒气体，使吸入者中毒。
受影响的气体只存在于施法当回合，且无法影响任何具有毒素抗性的生物。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "将目标周围的少量空气转化为有毒气体，使吸入者中毒。\n受影响的气体只存在于施法当回合，且无法影响任何具有毒素抗性的生物。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

2–3. trunk 消费者与参数证据

crawl-ref/source/describe.cc:5471
crawl-ref/source/spl-data.h",
crawl-ref/source/english.cc",
crawl-ref/source/message.cc",
crawl-ref/source/item-name.cc",
crawl-ref/source/item-name.cc",
crawl-ref/source/english.cc",
crawl-ref/source/message.cc",
crawl-ref/source/item-name.cc",
crawl-ref/source/item-name.cc",

中文全文
```text
将目标周围的少量空气转化为有毒气体，使吸入者中毒。
受影响的气体只存在于施法当回合，且无法影响任何具有毒素抗性的生物。
```

冻结的调用参数、条件与输入还原（输入错误以上述独立判断为准）：
```json
[
  {
    "method": "静态模板，无参数",
    "full_zh_display": "将目标周围的少量空气转化为有毒气体，使吸入者中毒。\n受影响的气体只存在于施法当回合，且无法影响任何具有毒素抗性的生物。",
    "formula": "按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。"
  }
]
```

4. 独立语义判断与还原
目标周围少量空气、吸入中毒、仅当回合及任何毒抗免疫完整。

5. 术语适用性
当前 glossary 在相应对象与机制内使用；Hexes 为学派身份，文学魔力不强行等同MP，所有格按生产实现判断。结论：ok
