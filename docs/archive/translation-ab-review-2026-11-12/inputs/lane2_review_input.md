# 中文译文 A/B 盲评输入

你是中文游戏本地化评审。下面是一款英文 roguelike 游戏（Dungeon Crawl Stone Soup 0.34.1）的 48 条英文原文，每条有两份独立的中文译文 A 与 B。

## 评审规则
- 只依据本文件内容评审；不要查找、打开或推断任何译文仓库、提交或作者，不要上网搜索这些译文。可以凭你对游戏机制的公共知识理解原文。
- 源码摘录来自上游英文版，只用于说明这句英文在何时、以何种参数显示。
- `%s`、`%d` 等占位符在运行时由程序填入（英文版填入什么见摘录）。两份译文所在的程序可能以不同形式填充参数（例如参数本身是否已带"的"或量词）。若你的判断依赖参数的具体填充形式，请标 `validation_gap`，不要据此判定错误。
- 专有名词、怪物/法术/神祇名称可能来自两套不同的既定术语表。只有在含义错误、与原文机制不符或同一译文内部自相矛盾时才算错误；仅仅"与你习惯的译名不同"属于偏好。
- 长段说明的两份译文已统一做过换行/空格规整（段内合并、保留段落），本轮不评价排版格式。
- 不要修改或重写译文；如需说明问题，可引用关键片段。

## 每项请评价
1. faithfulness：忠实/完整（有无漏译、增译、误译）
2. mechanics：机制、数字、条件是否与原文一致
3. terminology：术语是否贴切（注意上面的偏好规则）
4. invariants：占位符、标记（如 `<w>`、`@x@`）、行首空格等是否保持
5. readability：中文可读性、语法
6. tone：语气是否贴合原文（神明、怪物、讽刺等）

## 输出
把结果写入与本文件同目录的 `review_output.json`，格式为 JSON 数组，每项：
```
{"sample_id": "...",
 "verdict": "A" | "B" | "tie" | "insufficient_evidence",
 "reason": "一两句理由",
 "scores": {"A": {"faithfulness":1-5,"mechanics":1-5,"terminology":1-5,"invariants":1-5,"readability":1-5,"tone":1-5},
            "B": {...}},   // 可选；1=严重错误，3=可接受但有明显瑕疵，5=无可挑剔
 "findings": [{"side":"A"|"B","type":"objective_error"|"internal_consistency"|"preference"|"validation_gap",
               "category":"mistranslation|omission|addition|mechanics|placeholder|markup|grammar|terminology|tone|format",
               "quote":"关键原文/译文片段","evidence":"依据（引用原文或摘录）","impact":"对玩家的影响"}]}
```
客观错误、内部一致性问题与纯偏好请分开标注。没有充分证据的判断标 `validation_gap`。
最后在回复中给出：A 胜/B 胜/平局/证据不足的数量，以及你认为最重要的 5 条发现。

## 样本

### 2-01（类别：对话/长篇说明）

**英文原文**
```
The echo of an unmourned soul. Though the memories of its living self are
long-faded, it is drawn to the moment of death by some lingering instinct. It
seizes upon the passage of other souls, losing the last vestiges of its being
in the memories of another's life.
```
**用途/位置**：crawl-ref/source/dat/descript/monsters.txt [lost soul]

**上下文（上游英文源码或数据说明）**
```
(数据文件 monsters.txt，条目键 "lost soul"；在游戏内查看对应对象说明时整段显示)
```
**译文 A**
```
一个无人哀悼的灵魂的回音。尽管它自己生前的记忆已经褪去很久了，但还是被某种弥留的本能拉到了死亡的那一刻。它夺取他人灵魂的旅程，在别人生命的记忆中失去了自己存在的最后一丝痕迹。
```
**译文 B**
```
一个无人哀悼的灵魂的回音。尽管它自己生前的记忆已经褪去很久了，但还是被某种弥留的本能拉到了死亡的那一刻。它攫住其他灵魂离去的时刻，并在另一段人生的记忆中耗尽自身最后的残痕。
```

### 2-02（类别：战斗及动态消息）

**英文原文**
```
You sink your fangs into %s and drink %s %s.
```
**用途/位置**：crawl-ref/source/melee-attack.cc:622

**上下文（上游英文源码或数据说明）**
```
  618                                    && mon->holiness() & (MH_NATURAL | MH_PLANT | MH_DEMONIC);
  619  
  620          if (can_heal && !can_enthrall)
  621          {
  622              mprf("You sink your fangs into %s and drink %s %s.",
  623                      mon->name(DESC_THE, true).c_str(),
  624                      mon->pronoun(PRONOUN_POSSESSIVE).c_str(),
  625                      mon->blood_name().c_str());
  626          }
```
**译文 A**
```
你将獠牙刺入%s，饮下了%s%s。
```
**译文 B**
```
你把獠牙插入%s，畅饮了%s%s。
```

### 2-03（类别：神明/角色语气）

**英文原文**
```
Nature churns violently around you!
```
**用途/位置**：crawl-ref/source/god-abil.cc:4210

**上下文（上游英文源码或数据说明）**
```
 4206      }
 4207  
 4208      fail_check();
 4209  
 4210      mprf(MSGCH_GOD, "Nature churns violently around you!");
 4211  
 4212      // TODO: should count get a cap proportional to targets.size()?
 4213      int count = max(1, min((int)targets.size(),
 4214                              max(you.skill_rdiv(SK_INVOCATIONS, 1, 2),
```
**译文 A**
```
大自然在你周围猛烈翻腾！
```
**译文 B**
```
大自然在你周围剧烈翻腾！
```

### 2-04（类别：战斗及动态消息）

**英文原文**
```
%s willpower is stripped away!
```
**用途/位置**：crawl-ref/source/monster.cc:5773

**上下文（上游英文源码或数据说明）**
```
 5769      if (willpower() == WILL_INVULN)
 5770          return false;
 5771  
 5772      if (!quiet && !has_ench(ENCH_LOWERED_WL) && you.can_see(*this))
 5773          mprf("%s willpower is stripped away!", name(DESC_ITS).c_str());
 5774  
 5775      mon_enchant lowered_wl(ENCH_LOWERED_WL, attacker, dur * BASELINE_DELAY);
 5776      return add_ench(lowered_wl);
 5777  }
```
**译文 A**
```
%s的意志被剥除了！
```
**译文 B**
```
%s意志力被剥夺了！
```

### 2-05（类别：神明/角色语气）

**英文原文**
```
You carve a gateway into yourself and beckon forth the legions of chaos!
```
**用途/位置**：crawl-ref/source/god-abil.cc:7119

**上下文（上游英文源码或数据说明）**
```
 7115      if (stop_summoning_prompt())
 7116          return spret::abort;
 7117  
 7118      fail_check();
 7119      mpr("You carve a gateway into yourself and beckon forth the legions of chaos!");
 7120      bleed_for_makhleb(you);
 7121      you.duration[DUR_INFERNAL_LEGION] = (you.skill_rdiv(SK_INVOCATIONS, 5, 4)
 7122                                              + random_range(10, 20)) * BASELINE_DELAY;
 7123  
```
**译文 A**
```
你在自己身上刻出一道门，召来混沌军团！
```
**译文 B**
```
你在自己身上刻出一个通道，召唤混沌军团前来！
```

### 2-06（类别：对话/长篇说明）

**英文原文**
```
A mosquito that has fed upon tainted blood and been transformed into a
revolting and pestilent undead insect, seeking to drain its victims to the last
drop.
```
**用途/位置**：crawl-ref/source/dat/descript/monsters.txt [vampire mosquito]

**上下文（上游英文源码或数据说明）**
```
(数据文件 monsters.txt，条目键 "vampire mosquito"；在游戏内查看对应对象说明时整段显示)
```
**译文 A**
```
这只蚊子以受污染的血液为食，变成了一只令人作呕、散播疾病的亡灵昆虫。它的目的是将它的猎物吸干——一滴不留。
```
**译文 B**
```
这只蚊子以受污染的血液为食，变成了一只令人作呕、散播疾病的亡灵昆虫。它的目的是将它的猎物吸干——一滴不留。
```

### 2-07（类别：法术/技能/变异）

**英文原文**
```
Corrupt Body
```
**用途/位置**：crawl-ref/source/spl-data.h:4655

**上下文（上游英文源码或数据说明）**
```
 4651  AXED_SPELL(SPELL_CONTROLLED_BLINK, "Controlled Blink")
 4652  AXED_SPELL(SPELL_CONTROL_TELEPORT, "Control Teleport")
 4653  AXED_SPELL(SPELL_CONTROL_UNDEAD, "Control Undead")
 4654  AXED_SPELL(SPELL_CONTROL_WINDS, "Control Winds")
 4655  AXED_SPELL(SPELL_CORRUPT_BODY, "Corrupt Body")
 4656  AXED_SPELL(SPELL_CURE_POISON, "Cure Poison")
 4657  AXED_SPELL(SPELL_DARKNESS, "Darkness")
 4658  AXED_SPELL(SPELL_OLD_DEFLECT_MISSILES, "Old Deflect Missiles")
 4659  AXED_SPELL(SPELL_DELAYED_FIREBALL, "Delayed Fireball")
```
**译文 A**
```
腐化躯体
```
**译文 B**
```
腐化躯体
```

### 2-08（类别：战斗及动态消息）

**英文原文**
```
%s floods into %s %s!
```
**用途/位置**：crawl-ref/source/monster.cc:5842

**上下文（上游英文源码或数据说明）**
```
 5838      {
 5839          // Assume any vertebrate bodyplan (and is alive and isn't aquatic) has
 5840          // something that can be called lungs.
 5841          const bool has_lungs = get_mon_shape(*this) < MON_SHAPE_INSECT;
 5842          mprf("%s floods into %s %s!",
 5843                  substance, name(DESC_ITS).c_str(),
 5844                  has_lungs ? "lungs" : "airways");
 5845      }
 5846  
```
**译文 A**
```
%s涌入了%s%s！
```
**译文 B**
```
%s涌入了%s的%s！
```

### 2-09（类别：物品/怪物名称及短说明）

**英文原文**
```
ghost
```
**用途/位置**：crawl-ref/source/directn.cc:3482, crawl-ref/source/mon-death.cc:612

**上下文（上游英文源码或数据说明）**
```
 3478                      str += "dancing weapon";
 3479                  else if (mi.type == MONS_PANDEMONIUM_LORD)
 3480                      str += "pandemonium lord";
 3481                  else if (mi.type == MONS_PLAYER_GHOST)
 3482                      str += "ghost";
 3483              }
 3484              if (!str.empty())
 3485                  desc += " (" + str + ")";
 3486          }
```
**译文 A**
```
鬼魂
```
**译文 B**
```
幽灵
```

### 2-10（类别：物品/怪物名称及短说明）

**英文原文**
```
living smiting commandment
```
**用途/位置**：crawl-ref/source/mon-info.cc:1096

**上下文（上游英文源码或数据说明）**
```
 1092                  case SPELL_LEHUDIBS_CRYSTAL_SPEAR:
 1093                      s = "living crystal spell";
 1094                      break;
 1095                  case SPELL_SMITING:
 1096                      s = "living smiting commandment";
 1097                      break;
 1098                  case SPELL_PARALYSE:
 1099                      s = "living paralysis spell";
 1100                      break;
```
**译文 A**
```
活体惩击诫命
```
**译文 B**
```
活体神罚律令
```

### 2-11（类别：法术/技能/变异）

**英文原文**
```
You cover ground very slowly.
```
**用途/位置**：crawl-ref/source/mutation-data.h:380

**上下文（上游英文源码或数据说明）**
```
  376  { MUT_SLOW, 0, 3, mutflag::bad,
  377    "slowness",
  378  
  379    {"You cover ground slowly.",
  380     "You cover ground very slowly.",
  381     "You cover ground extremely slowly."},
  382  
  383    {"You feel sluggish.",
  384     "You feel sluggish.",
```
**译文 A**
```
你移动非常缓慢。
```
**译文 B**
```
你移动得非常缓慢。
```

### 2-12（类别：战斗及动态消息）

**英文原文**
```
Items here: %s.
```
**用途/位置**：crawl-ref/source/items.cc:933

**上下文（上游英文源码或数据说明）**
```
  929  
  930      string desc_string = item_message(items);
  931      // Stack summary case
  932      if (static_cast<int>(items.size()) >= Options.item_stack_summary_minimum)
  933          mprf_nojoin(MSGCH_FLOOR_ITEMS, "Items here: %s.", desc_string.c_str());
  934      else if (items.size() <= msgwin_lines() - 1)
  935      {
  936          mpr_nojoin(MSGCH_FLOOR_ITEMS, "Things that are here:");
  937          mprf_nocap("%s", desc_string.c_str());
```
**译文 A**
```
此处物品：%s。
```
**译文 B**
```
这里的物品：%s。
```

### 2-13（类别：物品/怪物名称及短说明）

**英文原文**
```
cursed
```
**用途/位置**：crawl-ref/source/l-item.cc:1779

**上下文（上游英文源码或数据说明）**
```
 1775      { "plus2",             l_item_plus2 },
 1776      { "class",             l_item_class },
 1777      { "subtype",           l_item_subtype },
 1778      { "ego",               l_item_ego },
 1779      { "cursed",            l_item_cursed },
 1780      { "name",              l_item_name },
 1781      { "name_coloured",     l_item_name_coloured },
 1782      { "stacks",            l_item_stacks },
 1783      { "quantity",          l_item_quantity },
```
**译文 A**
```
诅咒
```
**译文 B**
```
诅咒的
```

### 2-14（类别：界面/状态）

**英文原文**
```
Huh?
```
**用途/位置**：crawl-ref/source/message.cc:2011

**上下文（上游英文源码或数据说明）**
```
 2007          case MSG_SPELL_FIZZLES:
 2008              mpr("The spell fizzles.");
 2009              break;
 2010          case MSG_HUH:
 2011              mprf(MSGCH_EXAMINE_FILTER, "Huh?");
 2012              crawl_state.cancel_cmd_repeat();
 2013              break;
 2014          case MSG_EMPTY_HANDED_ALREADY:
 2015          case MSG_EMPTY_HANDED_NOW:
```
**译文 A**
```
嗯？
```
**译文 B**
```
嗯？
```

### 2-15（类别：对话/长篇说明）

**英文原文**
```
An unfathomably massive pile of mystic pulsating protoplasm. The slightest
threat will cause it to undergo rapid weaponised mitosis, rapidly overwhelming
potential meals in a cytoplasmic tidal wave.
```
**用途/位置**：crawl-ref/source/dat/descript/monsters.txt [colossal amoeba]

**上下文（上游英文源码或数据说明）**
```
(数据文件 monsters.txt，条目键 "colossal amoeba"；在游戏内查看对应对象说明时整段显示)
```
**译文 A**
```
一堆令人难以理解地巨大的神秘脉动原生质。最轻微的威胁都会导致它进行快速武器化有丝分裂，在细胞质海啸中迅速淹没潜在的猎物。
```
**译文 B**
```
一团大得难以想象、神秘搏动的原生质。最轻微的威胁都会使它迅速进行武器化有丝分裂，以细胞质浪潮淹没潜在的食物。
```

### 2-16（类别：界面/状态）

**英文原文**
```
NOTE: Shaft traps aren't valid on this level.
```
**用途/位置**：crawl-ref/source/wiz-dgn.cc:504

**上下文（上游英文源码或数据说明）**
```
  500              ? "a random trap"
  501              : trap_at(pos)->name(DESC_A).c_str());
  502  
  503      if (trap == TRAP_SHAFT && !is_valid_shaft_level())
  504          mpr("NOTE: Shaft traps aren't valid on this level.");
  505  
  506      return true;
  507  }
  508  
```
**译文 A**
```
注意：本层不允许竖井陷阱。
```
**译文 B**
```
注意：此楼层不能设置竖井陷阱。
```

### 2-17（类别：物品/怪物名称及短说明）

**英文原文**
```
Disturbance
```
**用途/位置**：crawl-ref/source/directn.cc:1869

**上下文（上游英文源码或数据说明）**
```
 1865          _append_container(suffixes, _monster_description_suffixes(mi, behavior));
 1866          text = get_monster_equipment_desc(mi);
 1867      }
 1868      else
 1869          text = "Disturbance";
 1870  
 1871      // Build the final description string.
 1872      if (!suffixes.empty())
 1873      {
```
**译文 A**
```
异动
```
**译文 B**
```
扰动
```

### 2-18（类别：战斗及动态消息）

**英文原文**
```
You lose your grip on %s soul.
```
**用途/位置**：crawl-ref/source/mon-ench.cc:680

**上下文（上游英文源码或数据说明）**
```
  676  
  677      case ENCH_SOUL_RIPE:
  678          // Print message notifying the player, even if they cannot see us
  679          if (!quiet)
  680              mprf("You lose your grip on %s soul.", name(DESC_ITS, true).c_str());
  681          break;
  682  
  683      case ENCH_AWAKEN_FOREST:
  684          env.forest_awoken_until = 0;
```
**译文 A**
```
你失去了对%s灵魂的掌控。
```
**译文 B**
```
你失去了对%s灵魂的掌控。
```

### 2-19（类别：法术/技能/变异）

**英文原文**
```
You feel meek as a lamb.
```
**用途/位置**：crawl-ref/source/mutation-data.h:299

**上下文（上游英文源码或数据说明）**
```
  295     "Your attacks are less effective. (Slay -5)",
  296     "Your attacks are much less effective. (Slay -7)"},
  297    {"You feel meek.",
  298     "You feel even more meek.",
  299     "You feel meek as a lamb."},
  300    {"You feel aggression return to you.",
  301     "You feel a little less meek.",
  302     "You feel a little less meek."},
  303    TILEG_MUT_MEEK,
```
**译文 A**
```
你感到如羔羊般温顺。
```
**译文 B**
```
你感到自己像羔羊般温顺。
```

### 2-20（类别：对话/长篇说明）

**英文原文**
```
Qazlal Stormbringer is a violent god of tempests, who delights in unleashing
the forces of nature against the unsuspecting. Those who invite Qazlal's gaze
will find themselves the eye in a storm of elemental destruction, from which
only their God can protect them. Pious worshippers of Qazlal will gain the
ability to direct and control the destructive might of the storm.
```
**用途/位置**：crawl-ref/source/dat/descript/gods.txt [Qazlal]

**上下文（上游英文源码或数据说明）**
```
(数据文件 gods.txt，条目键 "Qazlal"；在游戏内查看对应对象说明时整段显示)
```
**译文 A**
```
风暴使者卡兹拉尔是狂暴的风暴之神，乐于向毫无防备者释放自然之力。招来祂注视的人，会置身于元素毁灭风暴的中心，唯有这位神祇能够保护他们。虔诚的信徒将获得指引和控制风暴破坏力的能力。
```
**译文 B**
```
兴风者卡兹拉尔是一个狂暴的风暴之神，喜欢释放自然的力量来对付没有戒心的人。那些请求卡兹拉尔注视的人会发现自己处于毁灭性元素风暴的风暴眼中，只有他们的神才能保护他们。虔诚的卡兹拉尔信徒将获得指挥和控制风暴破坏性力量的能力。
```

### 2-21（类别：神明/角色语气）

**英文原文**
```
You hear Kikubaaqudgha cackling.
```
**用途/位置**：crawl-ref/source/god-wrath.cc:655

**上下文（上游英文源码或数据说明）**
```
  651  static bool _kikubaaqudgha_retribution()
  652  {
  653      // death/necromancy theme
  654      const god_type god = GOD_KIKUBAAQUDGHA;
  655      god_speaks(god, coinflip() ? "You hear Kikubaaqudgha cackling."
  656                                 : "Kikubaaqudgha's malice focuses upon you.");
  657  
  658      if (wrath_tension_check(true))
  659      {
```
**译文 A**
```
你听到奇库巴库哈的狂笑声。
```
**译文 B**
```
你听到奇库巴库哈咯咯地笑。
```

### 2-22（类别：对话/长篇说明）

**英文原文**
```
Constructs a frangible shell of reinforced ice in a half-circle around the
caster, pushing creatures out of the way to make space for it, if possible.

This barricade is durable, and whenever a segment of it is destroyed, will
fracture into a salvo of icy projectiles launched at whatever destroyed it.

If the caster strays too far away from their barrier, it will melt rapidly.
```
**用途/位置**：crawl-ref/source/dat/descript/spells.txt [Splinterfrost Shell spell]

**上下文（上游英文源码或数据说明）**
```
(数据文件 spells.txt，条目键 "Splinterfrost Shell spell"；在游戏内查看对应对象说明时整段显示)
```
**译文 A**
```
在施法者周围构造半圆形的强化冰壳，若条件允许，会将生物推开以腾出空间。

这道屏障相当坚固，每当一段被摧毁，就会碎裂成一轮寒冰投射物，射向摧毁它的目标。

如果施法者离屏障太远，冰壳便会迅速融化。
```
**译文 B**
```
在施法者周围构筑一道半圆形的强化冰壳；如有可能，它会将生物推开，为自身腾出位置。

这道屏障十分坚固；每当一段冰壳被摧毁时，都会碎裂成一阵冰片，向摧毁它的生物齐射。

如果施法者离屏障太远，冰壳会迅速融化。
```

### 2-23（类别：对话/长篇说明）

**英文原文**
```
Conjures a stream of stolen suffering, leaving clouds of excruciating misery in
its wake and around its targets. These clouds of negative energy will rapidly
drain the living of small fractions of their maximum health.
```
**用途/位置**：crawl-ref/source/dat/descript/spells.txt [March of Sorrows spell]

**上下文（上游英文源码或数据说明）**
```
(数据文件 spells.txt，条目键 "March of Sorrows spell"；在游戏内查看对应对象说明时整段显示)
```
**译文 A**
```
造出一道窃取而来的苦难之流，沿途及目标周围留下极度苦难云。这些负能量云雾会迅速吸取活物最大生命值的一小部分。
```
**译文 B**
```
生成一股窃取的痛苦之流，它的尾迹和目标周围会留下郁积愁云。这些负能量云会迅速夺去活物的生命值，每次数额相当于其最大生命值的一小部分。
```

### 2-24（类别：物品/怪物名称及短说明）

**英文原文**
```
spectre
```
**用途/位置**：crawl-ref/source/kills.cc:753, crawl-ref/source/mon-info.cc:1211

**上下文（上游英文源码或数据说明）**
```
  749          case kill_monster_desc::M_SIMULACRUM:
  750              modifier = "simulacrum";
  751              break;
  752          case kill_monster_desc::M_SPECTRE:
  753              modifier = "spectre";
  754              break;
  755          case kill_monster_desc::M_SHAPESHIFTER:
  756              modifier = "shapeshifter";
  757              break;
```
**译文 A**
```
幽灵
```
**译文 B**
```
幽灵
```

### 2-25（类别：对话/长篇说明）

**英文原文**
```
Transforms the caster into a lightning bolt, and translocates the caster to
the bolt's destination.
```
**用途/位置**：crawl-ref/source/dat/descript/spells.txt [Blinkbolt spell]

**上下文（上游英文源码或数据说明）**
```
(数据文件 spells.txt，条目键 "Blinkbolt spell"；在游戏内查看对应对象说明时整段显示)
```
**译文 A**
```
将施法者变为闪电箭，并将施法者转移到目的地。
```
**译文 B**
```
使施法者化为一道闪电，并易位到闪电的终点。
```

### 2-26（类别：法术/技能/变异）

**英文原文**
```
Virulence
```
**用途/位置**：crawl-ref/source/spl-data.h:2365

**上下文（上游英文源码或数据说明）**
```
 2361      TILEG_INVISIBILITY,
 2362  },
 2363  
 2364  {
 2365      SPELL_VIRULENCE, "Virulence",
 2366      spschool::alchemy | spschool::hexes,
 2367      spflag::dir_or_target | spflag::needs_tracer | spflag::WL_check
 2368                            | spflag::monster,
 2369      4,
```
**译文 A**
```
毒性
```
**译文 B**
```
毒性激增
```

### 2-27（类别：战斗及动态消息）

**英文原文**
```
%s is now too close for your liking.
```
**用途/位置**：crawl-ref/source/delay.cc:1079

**上下文（上游英文源码或数据说明）**
```
 1075      monster* mon = at.mons_data;
 1076      ASSERT(mon);
 1077  
 1078      if (at.context == SC_ALREADY_IN_VIEW)
 1079          mprf(MSGCH_MONSTER_WARNING, "%s is now too close for your liking.", mon->name(DESC_THE).c_str());
 1080      else
 1081          mprf(MSGCH_MONSTER_WARNING, "%s comes into view.", mon->name(DESC_A).c_str());
 1082  }
 1083  
```
**译文 A**
```
%s现在离你太近了，让你不安。
```
**译文 B**
```
%s离你太近了。
```

### 2-28（类别：物品/怪物名称及短说明）

**英文原文**
```
living paralysis spell
```
**用途/位置**：crawl-ref/source/mon-info.cc:1099

**上下文（上游英文源码或数据说明）**
```
 1095                  case SPELL_SMITING:
 1096                      s = "living smiting commandment";
 1097                      break;
 1098                  case SPELL_PARALYSE:
 1099                      s = "living paralysis spell";
 1100                      break;
 1101                  default:
 1102                      break;
 1103                  }
```
**译文 A**
```
活体麻痹术
```
**译文 B**
```
活体麻痹法术
```

### 2-29（类别：界面/状态）

**英文原文**
```
Running Jiyva off-level sacrifice.
```
**用途/位置**：crawl-ref/source/wizard.cc:109

**上下文（上游英文源码或数据说明）**
```
  105      case CONTROL('I'): debug_item_statistics(); break;
  106  
  107      // case 'j': break;
  108      case 'J':
  109          mpr("Running Jiyva off-level sacrifice.");
  110          jiyva_eat_offlevel_items();
  111          break;
  112      // case CONTROL('J'): break;
  113  
```
**译文 A**
```
正在执行吉瓦的跨楼层献祭。
```
**译文 B**
```
正在执行吉瓦离层祭品处理。
```

### 2-30（类别：法术/技能/变异）

**英文原文**
```
Your blood calms down again.
```
**用途/位置**：crawl-ref/source/mutation-data.h:2449

**上下文（上游英文源码或数据说明）**
```
 2445    {"Your shed blood may rise up to attack you.",
 2446     "Your shed blood may rise up to attack you as a group.", ""},
 2447    {"You feel a willful anger gathering in your blood.",
 2448     "You feel your blood grow even more spiteful.", ""},
 2449    {"Your blood calms down again.",
 2450     "Your blood feels a little less spiteful.", ""},
 2451    TILEG_MUT_SPITEFUL_BLOOD,
 2452  },
 2453  
```
**译文 A**
```
你的鲜血再次平静了下来。
```
**译文 B**
```
你的血液再次平静下来。
```

### 2-31（类别：界面/状态）

**英文原文**
```
                   g - Guard the area.      f - Follow me.
```
**用途/位置**：crawl-ref/source/shout.cc:485

**上下文（上游英文源码或数据说明）**
```
  481      if (!you.berserk() && !you.confused())
  482      {
  483          mpr("Orders for allies: a - Attack new target.");
  484          mpr("                   r - Retreat!             s - Stop attacking.");
  485          mpr("                   g - Guard the area.      f - Follow me.");
  486      }
  487      mpr(" Anything else - Cancel.");
  488  
  489      flush_prev_message(); // buffer doesn't get flushed otherwise
```
**译文 A**
```
g - 守卫此区域。      f - 跟我来。
```
**译文 B**
```
          g - 守卫此地。    f - 跟随我。
```

### 2-32（类别：神明/角色语气）

**英文原文**
```
Your skin crawls.
```
**用途/位置**：crawl-ref/source/god-abil.cc:1408

**上下文（上游英文源码或数据说明）**
```
 1404  void trog_do_trogs_hand(int pow)
 1405  {
 1406      you.increase_duration(DUR_TROGS_HAND,
 1407                            5 + roll_dice(2, pow / 3 + 1), 100,
 1408                            "Your skin crawls.");
 1409      mprf(MSGCH_DURATION, "You feel strong-willed.");
 1410  }
 1411  
 1412  void trog_remove_trogs_hand()
```
**译文 A**
```
你的皮肤一阵发麻。
```
**译文 B**
```
你的皮肤一阵发麻。
```

### 2-33（类别：界面/状态）

**英文原文**
```
You glow brighter.
```
**用途/位置**：crawl-ref/source/player.cc:7875

**上下文（上游英文源码或数据说明）**
```
 7871  {
 7872      if (!duration[DUR_INVIS])
 7873      {
 7874          if (duration[DUR_CORONA])
 7875              mpr("You glow brighter.");
 7876          else
 7877              mpr("You are outlined in light.");
 7878      }
 7879      else
```
**译文 A**
```
你发光更亮了。
```
**译文 B**
```
你身上的光芒更亮了。
```

### 2-34（类别：神明/角色语气）

**英文原文**
```
You are too terrified to leap around!
```
**用途/位置**：crawl-ref/source/god-abil.cc:5407

**上下文（上游英文源码或数据说明）**
```
 5403          return false;
 5404      }
 5405      if (you.is_nervous())
 5406      {
 5407          mpr("You are too terrified to leap around!");
 5408          return false;
 5409      }
 5410  
 5411      // query for location:
```
**译文 A**
```
你太惊恐了，无法跳跃！
```
**译文 B**
```
你太恐惧了，无法跳跃！
```

### 2-35（类别：法术/技能/变异）

**英文原文**
```
Ignition
```
**用途/位置**：crawl-ref/source/spl-data.h:3248

**上下文（上游英文源码或数据说明）**
```
 3244      TILEG_POISONOUS_CLOUD,
 3245  },
 3246  
 3247  {
 3248      SPELL_IGNITION, "Ignition",
 3249      spschool::fire,
 3250      spflag::destructive,
 3251      8,
 3252      200,
```
**译文 A**
```
点火
```
**译文 B**
```
引燃术
```

### 2-36（类别：界面/状态）

**英文原文**
```
Your blood rage is quickly leaving you.
```
**用途/位置**：crawl-ref/source/main.cc:2868

**上下文（上游英文源码或数据说明）**
```
 2864          case 4:
 2865              mprf(MSGCH_DURATION, "You feel your anger nearly subside.");
 2866              break;
 2867          case 6:
 2868              mprf(MSGCH_DURATION, "Your blood rage is quickly leaving you.");
 2869              break;
 2870          }
 2871  
 2872          const int berserk_base_delay = BASELINE_DELAY;
```
**译文 A**
```
你的血怒正在迅速消退。
```
**译文 B**
```
你的嗜血狂怒正在迅速消退。
```

### 2-37（类别：物品/怪物名称及短说明）

**英文原文**
```
bound soul
```
**用途/位置**：crawl-ref/source/mon-info.cc:1215

**上下文（上游英文源码或数据说明）**
```
 1211              ss << "spectre";
 1212          break;
 1213      case MONS_BOUND_SOUL:
 1214          if (nocore)
 1215              ss << "bound soul";
 1216          break;
 1217      case MONS_PILLAR_OF_SALT:
 1218          if (base_type != type)
 1219              ss << (nocore ? "" : " ") << "shaped pillar of salt";
```
**译文 A**
```
受缚灵魂
```
**译文 B**
```
缚魂
```

### 2-38（类别：神明/角色语气）

**英文原文**
```
The monsters
```
**用途/位置**：crawl-ref/source/god-wrath.cc:1680

**上下文（上游英文源码或数据说明）**
```
 1676                                      false, GOD_IGNIS);
 1677  
 1678      // Describe the effect on the monsters.
 1679      mprf("%s %s shrouded in protective flame, covering ground quickly, and attacking fiercely!",
 1680           mons.size() == 1 ? mons[0]->name(DESC_THE).c_str() : "The monsters",
 1681           mons.size() == 1 ? "is" : "are");
 1682  
 1683      for (monster* mon : mons)
 1684      {
```
**译文 A**
```
怪物们
```
**译文 B**
```
这些怪物
```

### 2-39（类别：界面/状态）

**英文原文**
```
You feel perceptive.
```
**用途/位置**：crawl-ref/source/player-equip.cc:2241

**上下文（上游英文源码或数据说明）**
```
 2237                  mpr("You feel resistant to poison.");
 2238              break;
 2239  
 2240          case SPARM_SEE_INVISIBLE:
 2241              mpr("You feel perceptive.");
 2242              autotoggle_autopickup(false);
 2243              break;
 2244  
 2245          case SPARM_INVISIBILITY:
```
**译文 A**
```
你感觉感知更加敏锐。
```
**译文 B**
```
你感到感知力增强了。
```

### 2-40（类别：界面/状态）

**英文原文**
```
It gets dark.
```
**用途/位置**：crawl-ref/source/player-equip.cc:2311

**上下文（上游英文源码或数据说明）**
```
 2307              mpr("You are surrounded by a repulsion field.");
 2308              break;
 2309  
 2310          case SPARM_SHADOWS:
 2311              mpr("It gets dark.");
 2312              update_vision_range();
 2313              break;
 2314  
 2315          case SPARM_RAMPAGING:
```
**译文 A**
```
周围暗了下来。
```
**译文 B**
```
周围变暗了。
```

### 2-41（类别：战斗及动态消息）

**英文原文**
```
%s arms its allies with %s.
```
**用途/位置**：crawl-ref/source/mon-cast.cc:7211

**上下文（上游英文源码或数据说明）**
```
 7207      wpn.quantity = 1;
 7208  
 7209      if (you.can_see(caster))
 7210      {
 7211          mprf(MSGCH_MONSTER_SPELL, "%s arms its allies with %s.", caster.name(DESC_THE).c_str(),
 7212                                      pluralise(wpn.name(DESC_PLAIN, false, true)).c_str());
 7213      }
 7214  
 7215      int dur = random_range(20, 37) * BASELINE_DELAY;
```
**译文 A**
```
%s用%s武装了盟友。
```
**译文 B**
```
%s用%s武装了它的盟友。
```

### 2-42（类别：物品/怪物名称及短说明）

**英文原文**
```
 (fellow slime)
```
**用途/位置**：crawl-ref/source/mon-info.cc:1460

**上下文（上游英文源码或数据说明）**
```
 1456  #if TAG_MAJOR_VERSION == 34
 1457      case ATT_OLD_STRICT_NEUTRAL:
 1458  #endif
 1459          if (fellow_slime())
 1460              out << " (fellow slime)";
 1461          colour_type = MLC_GOOD_NEUTRAL;
 1462          break;
 1463      case ATT_NEUTRAL:
 1464          colour_type = MLC_NEUTRAL;
```
**译文 A**
```
（同族史莱姆）
```
**译文 B**
```
（史莱姆同伴）
```

### 2-43（类别：神明/角色语气）

**英文原文**
```
Kikubaaqudgha's malice focuses upon you.
```
**用途/位置**：crawl-ref/source/god-wrath.cc:656

**上下文（上游英文源码或数据说明）**
```
  652  {
  653      // death/necromancy theme
  654      const god_type god = GOD_KIKUBAAQUDGHA;
  655      god_speaks(god, coinflip() ? "You hear Kikubaaqudgha cackling."
  656                                 : "Kikubaaqudgha's malice focuses upon you.");
  657  
  658      if (wrath_tension_check(true))
  659      {
  660          int xl = you.experience_level;
```
**译文 A**
```
奇库巴库哈的恶意集中到了你身上。
```
**译文 B**
```
奇库巴库哈的恶意聚焦在你身上。
```

### 2-44（类别：战斗及动态消息）

**英文原文**
```
%s is forced to slowly start %s a word of recall!
```
**用途/位置**：crawl-ref/source/xom.cc:4210

**上下文（上游英文源码或数据说明）**
```
 4206      if (phrasing == "dramatically intoning")
 4207          xom_speech = "grant voiceless word of recall";
 4208  
 4209      god_speaks(GOD_XOM, _get_xom_speech(xom_speech).c_str());
 4210      mprf(MSGCH_WARN, "%s is forced to slowly start %s a word of recall!",
 4211                       targetable[0]->name(DESC_A, true, false).c_str(),
 4212                       phrasing.c_str());
 4213      mon_enchant chant_timer = mon_enchant(ENCH_WORD_OF_RECALL, targetable[0], duration);
 4214      targetable[0]->add_ench(chant_timer);
```
**译文 A**
```
%s被迫缓慢地开始%s召回术！
```
**译文 B**
```
%s被迫开始缓缓%s召回真言！
```

### 2-45（类别：神明/角色语气）

**英文原文**
```
The world leaves you behind!
```
**用途/位置**：crawl-ref/source/god-wrath.cc:389

**上下文（上游英文源码或数据说明）**
```
  385              dec_penance(god, 1);
  386          }
  387          else
  388          {
  389              mprf(MSGCH_DANGER, "The world leaves you behind!");
  390              dec_haste_player(10000);
  391              slow_player(81 + random2(10));
  392          }
  393      }
```
**译文 A**
```
世界将你抛在了身后！
```
**译文 B**
```
世界将你抛弃在身后！
```

### 2-46（类别：法术/技能/变异）

**英文原文**
```
You have hooves in place of feet.
```
**用途/位置**：crawl-ref/source/mutation-data.h:756

**上下文（上游英文源码或数据说明）**
```
  752    "hooves",
  753  
  754    {"You have large cloven feet.",
  755     "You have hoof-like feet.",
  756     "You have hooves in place of feet."},
  757  
  758    {"Your feet thicken and deform.",
  759     "Your feet thicken and deform.",
  760     "Your feet have mutated into hooves."},
```
**译文 A**
```
你的脚变成了蹄子。
```
**译文 B**
```
你的双脚是蹄子。
```

### 2-47（类别：法术/技能/变异）

**英文原文**
```
You are significantly more attuned to the shadows.
```
**用途/位置**：crawl-ref/source/mutation-data.h:1101

**上下文（上游英文源码或数据说明）**
```
 1097  { MUT_NIGHTSTALKER, 0, 3, mutflag::good,
 1098    "nightstalker",
 1099  
 1100    {"You are slightly more attuned to the shadows.",
 1101     "You are significantly more attuned to the shadows.",
 1102     "You are completely attuned to the shadows."},
 1103  
 1104    {"You slip into the darkness of the dungeon.",
 1105     "You slip further into the darkness.",
```
**译文 A**
```
你与暗影的同调显著增强。
```
**译文 B**
```
你与阴影的联系显著增强。
```

### 2-48（类别：对话/长篇说明）

**英文原文**
```
Invokes a huge blast of divine fury centered on the user, severely damaging
undead and demons and dealing damage to all other hostile creatures.
```
**用途/位置**：crawl-ref/source/dat/descript/spells.txt [Cleansing Flame spell]

**上下文（上游英文源码或数据说明）**
```
(数据文件 spells.txt，条目键 "Cleansing Flame spell"；在游戏内查看对应对象说明时整段显示)
```
**译文 A**
```
以使用者为中心引发巨大的神怒爆发，重创亡灵和恶魔，并伤害其他所有敌对生物。
```
**译文 B**
```
激起以使用者为中心的巨大的神怒爆炸，会对亡灵和恶魔造成严重伤害，并对所有其他敌对生物造成伤害。
```
