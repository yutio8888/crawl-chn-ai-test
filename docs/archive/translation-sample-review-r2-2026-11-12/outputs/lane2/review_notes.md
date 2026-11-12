# Lane2 独立译文审查


模型：GPT-6（Codex）；运行时未向评审暴露精确模型后缀、采样温度或推理参数，不臆测。

固定基线：stable 83af93c8bdbbaf1b66aeac0af3eaa6ff58cebc57；trunk 302ecba316bee8be19b73d06c3697cf82bd5bc3e。

Glossary SHA-256：fb814f3252f249fc230e81fa132dce6a9bb194b014d687fc1524c66827b351d7。

方法：仅读取 lane2；不修改仓库。读取项目规则并运行 context_resolve，非盲评。以下每项依次记录完整英文、生产消费者、条件参数证据、独立语义判断，最后检查术语适用范围。未用决定编号或 CI 代替证据。输入源码片段是冻结证据；补查均用 git show 固定 SHA。未执行构建或运行时排版测试，ok 表示静态文本与消费者未发现问题，不认证全部终端尺寸。

补查发现输入中 C1-02/C1-09 标注 trunk 缺中文与源码不符：trunk dat/i18n/zh/source.txt:48238 与 :48150 均有正常条目；不据输入标注报漏译。stable database.cc:2672 起还原换行转义，因此不能把输入中的字面量 \n 当运行时乱码。

总体观察仅适用于这80项：多数语义及数值完整，少量术语、范围和增译问题；不外推全库错误率。



## C4-08


1. 完整英文

```text
With a soft hiss, the gate opens fully!
```


2. 生产使用者

stable crawl-ref/source/stairs.cc:488; trunk crawl-ref/source/stairs.cc:500


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
else
        mpr(T_("With a soft hiss, the gate opens fully!"));

```

```cpp
else
        mpr(T_("With a soft hiss, the gate opens fully!"));

```


4. 独立语义判断

非沉默分支的轻微嘶声和开门完成均完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C2-04


1. 完整英文

```text
This helmet is too small for your head.
```


2. 生产使用者

stable crawl-ref/source/player-equip.cc:530; trunk crawl-ref/source/player-equip.cc:549


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
if (player_size >= SIZE_LARGE)
                NO_EQUIP(T_("This helmet is too small for your head."))
            else if (player_size <= SIZE_LITTLE)
                NO_EQUIP(T_("This helmet is too large for your head."))
            else if (species::is_draconian(you.species))
                NO_EQUIP(T_("You can't wear that with your reptilian head."))
            else if (you.species == SP_OCTOPODE)
                NO_EQUIP(T_("Your can't wear that!"))
            else if (you.has_mutation(MUT_HORNS, include_form))
                NO_EQUIP(T_("You can't fit that over your horns."))
            else if (you.has_mutation(MUT_ANTENNAE, include_form))
                NO_EQUIP(T_("You can't fit that over your antennae."))
            else if (you.has_mutation(MUT_BEAK, include_form))
                NO_EQUIP(T_("You can't fit that over your beak."))
        }
    }
    else if (item.base_type == OBJ_WEAPONS)
    {
        const size_type bsize = you.body_size(PSIZE_TORSO, !include_form);

```

```cpp
if (player_size >= SIZE_LARGE)
                NO_EQUIP(T_("This helmet is too small for your head."))
            else if (player_size <= SIZE_LITTLE)
                NO_EQUIP(T_("This helmet is too large for your head."))
            else if (species::is_draconian(you.species))
                NO_EQUIP(T_("You can't wear that with your reptilian head."))
            else if (you.species == SP_OCTOPODE)
                NO_EQUIP(T_("Your can't wear that!"))
            else if (you.has_mutation(MUT_HORNS, temp))
                NO_EQUIP(T_("You can't fit that over your horns."))
            else if (you.has_mutation(MUT_ANTENNAE, temp))
                NO_EQUIP(T_("You can't fit that over your antennae."))
            else if (you.has_mutation(MUT_BEAK, temp))
                NO_EQUIP(T_("You can't fit that over your beak."))
        }
    }
    else if (item.base_type == OBJ_WEAPONS)
    {
        const size_type bsize = you.body_size(PSIZE_TORSO, !temp);

```


4. 独立语义判断

体型过大导致头盔太小，条件和对象正确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C2-08


1. 完整英文

```text
%s becomes incredibly heavy!
```


2. 生产使用者

stable crawl-ref/source/item-use.cc:2173; trunk crawl-ref/source/item-use.cc:2243


3. 机制与参数证据

动态参数说明：格式实参的真实生成表达式见各消费者 statement（保留完整调用，包括嵌套名称/数值表达式）。

```cpp
mprf(T_("%s becomes incredibly heavy!"),itname.c_str());

```

```cpp
mprf(T_("%s becomes incredibly heavy!"),itname.c_str());

```


4. 独立语义判断

沉重铭印变化与物品名参数准确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C6-02


1. 完整英文

```text
You are too depleted to draw on your %s recklessly!
```


2. 生产使用者

stable crawl-ref/source/quiver.cc:138; trunk crawl-ref/source/quiver.cc:146


3. 机制与参数证据

动态参数说明：格式实参的真实生成表达式见各消费者 statement（保留完整调用，包括嵌套名称/数值表达式）。

```cpp
mprf(T_("You are too depleted to draw on your %s recklessly!"), resource);

```

```cpp
mprf(T_("You are too depleted to draw on your %s recklessly!"), resource);

```


4. 独立语义判断

资源实际为生命或魔法，两分支都能成句；魔法用于 MP 可改为法力以更明确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C4-06


trunk 完整英文（版本对照）：

```text
%s emits a blaring wail!
```


1. 完整英文

```text
%s emits a blaring wail!
```


2. 生产使用者

stable crawl-ref/source/traps.cc:597


3. 机制与参数证据

动态参数说明：格式实参的真实生成表达式见各消费者 statement（保留完整调用，包括嵌套名称/数值表达式）。

```cpp
string msg = make_stringf(T_("%s emits a blaring wail!"),
                               name(DESC_THE).c_str());

```


4. 独立语义判断

陷阱名填入主语，警报哀嚎准确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C1-02


trunk 完整英文（版本对照）：

```text
mute/unmute sound effects
```


1. 完整英文

```text
mute/unmute sound effects
```


2. 生产使用者

stable crawl-ref/source/command.cc:1197; trunk crawl-ref/source/command.cc:1176


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
#ifdef USE_SOUND
    _add_command(cols, 1, CMD_TOGGLE_SOUND, T_("mute/unmute sound effects"));

```

```cpp
#ifdef USE_SOUND
    _add_command(cols, 1, CMD_TOGGLE_SOUND, T_("mute/unmute sound effects"));

```


4. 独立语义判断

音效静音开关含义准确；源码复核发现 trunk 也有中文条目，输入缺失标注不成立。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C5-04


trunk 完整英文（版本对照）：

```text
You can easily mark its square as dangerous to avoid accidentally entering into its field of view when using auto-explore or auto-travel. To do so, enter targeting mode with <w>%</w> and then press <w>%</w> when your cursor is hovering over the monster's grid. Doing so will mark this grid and all surrounding ones within a radius of 8 as "excluded" ones that explore or travel modes won't enter.
```


1. 完整英文

```text
You can easily mark its square as dangerous to avoid accidentally entering into its field of view when using auto-explore or auto-travel. To do so, enter targeting mode with <w>%</w> and then press <w>%</w> when your cursor is hovering over the monster's grid. Doing so will mark this grid and all surrounding ones within a radius of 8 as "excluded" ones that explore or travel modes won't enter.
```


2. 生产使用者

stable crawl-ref/source/hints.cc:2787


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
string exclude_tip = T_("You can easily mark its square as dangerous "
                    "to avoid accidentally entering into its field of view when "
                    "using auto-explore or auto-travel. To do so, enter targeting "
                    "mode with <w>%</w> and then press <w>%</w> when your cursor "
                    "is hovering over the monster's grid. Doing so will mark this "
                    "grid and all surrounding ones within a radius of 8 as "
                    "\"excluded\" ones that explore or travel modes won't enter.");

```


4. 独立语义判断

排除操作的两键、光标位置、半径8和探索旅行禁入都完整；未见 trunk 调用不能据其缺键判漏译。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C4-10


1. 完整英文

```text
You enter a Zot trap.
```


2. 生产使用者

stable crawl-ref/source/traps.cc:705; trunk crawl-ref/source/traps.cc:621


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
mpr(T_("You enter a Zot trap."));

```

```cpp
mpr(T_("You enter a Zot trap."));

```


4. 独立语义判断

进入佐特陷阱，准确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C6-09


1. 完整英文

```text
you cannot see anything nearby that you can launch.
```


2. 生产使用者

stable crawl-ref/source/spl-util.cc:1989; trunk crawl-ref/source/spl-util.cc:2007


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
if (!piledriver_target_exists())
                return T_("you cannot see anything nearby that you can launch.");

```

```cpp
if (!piledriver_target_exists())
                return T_("you cannot see anything nearby that you can launch.");

```


4. 独立语义判断

piledriver 无可发射目标，否定及附近可见范围完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C5-01


trunk 完整英文（版本对照）：

```text
In Tiles, you can achieve the same, in either direction, by clicking the <w>left mouse button</w>.
```


1. 完整英文

```text
In Tiles, you can achieve the same, in either direction, by clicking the <w>left mouse button</w>.
```


2. 生产使用者

stable crawl-ref/source/hints.cc:2520


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
#ifdef USE_TILE
        ostr << T_(" In Tiles, you can achieve the same, in either direction, "
                "by clicking the <w>left mouse button</w>.");

```


4. 独立语义判断

前文楼梯上下两向均可点击，任意方向略显过宽但上下文可消解。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；本条存在上述术语或语义问题。 verdict=readability


## C4-09


1. 完整英文

```text
fly down
```


2. 生产使用者

stable crawl-ref/source/stairs.cc:241; trunk crawl-ref/source/stairs.cc:234


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
mprf(T_("You %s through the gate."),
             you.airborne() ? (going_up ? T_("fly up") : T_("fly down"))
                            : (going_up ? T_("go up") : T_("go down")));

```

```cpp
mprf(T_("You %s through the gate."),
             you.airborne() ? (going_up ? T_("fly up") : T_("fly down"))
                            : (going_up ? T_("go up") : T_("go down")));

```


4. 独立语义判断

向下飞填入你%s穿过了大门，成句成立。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C5-02


1. 完整英文

```text
Escape hatch
```


2. 生产使用者

stable crawl-ref/source/hints.cc:1162; trunk crawl-ref/source/hints.cc:1108


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
tiles.add_text_tag(TAG_TUTORIAL, T_("Escape hatch"), gc);

```

```cpp
tiles.add_text_tag(TAG_TUTORIAL, T_("Escape hatch"), gc);

```


4. 独立语义判断

逃生口标签准确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C1-03


1. 完整英文

```text
<yellow>$</yellow> : gold (<w>%</w> counts gold)
```


2. 生产使用者

stable crawl-ref/source/command.cc:1072; trunk crawl-ref/source/command.cc:1070


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
_add_insert_commands(cols, 0, T_("<yellow>$</yellow> : gold (<w>%</w> counts gold)"),
                         { CMD_LIST_GOLD });

```

```cpp
_add_insert_commands(cols, 0, T_("<yellow>$</yellow> : gold (<w>%</w> counts gold)"),
                         { CMD_LIST_GOLD });

```


4. 独立语义判断

金币图例与计数键完整，百分号是命令插入槽。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C6-04


1. 完整英文

```text
You cannot fit into any form of body armour or wear helmets.
```


2. 生产使用者

stable crawl-ref/source/mutation.cc:882; trunk crawl-ref/source/mutation.cc:884


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
"unfitting armour",
                      _innatemut(T_("You cannot fit into any form of body armour or wear helmets."))};

```

```cpp
"unfitting armour",
                      _innatemut(T_("You cannot fit into any form of body armour or wear helmets."))};

```


4. 独立语义判断

身体护甲与头盔全部禁用，完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C3-08


1. 完整英文

```text
{{
    if you.race() == "Djinni" then
        return "Being skilled in Spellcasting increases the success rate and spell "..
               "power of all spells."
    else
        return "Being skilled in Spellcasting slightly increases the success " ..
                "rate and spell power of all spells, along with increasing your " ..
                "magical reserves. Training Spellcasting also gives you more spell " ..
                "slots to spend on new spells."
    end
}}
```


2. 生产使用者

stable crawl-ref/source/describe.cc:4647; stable crawl-ref/source/describe.cc:8012; stable crawl-ref/source/hints.cc:759; stable crawl-ref/source/tilereg-skl.cc:140; trunk crawl-ref/source/describe.cc:5047; trunk crawl-ref/source/describe.cc:8746; trunk crawl-ref/source/hints.cc:748; trunk crawl-ref/source/tilereg-skl.cc:140


3. 机制与参数证据

动态参数说明：lookup key = skill_name_en(skill)，skill 为技能枚举；正文由 get_skill_description 返回，describe_skill / hints / tiles UI 消费。无格式实参。

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false, &spell_fail_details);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```


4. 独立语义判断

Lua 灯神分支不谈法力和法术槽，其他种族分支保留略微加成与储备，协议比较值未译。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C6-03


1. 完整英文

```text
You can't rise from this level!
```


2. 生产使用者

stable crawl-ref/source/ability.cc:1838; trunk crawl-ref/source/ability.cc:1930


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
if (!level_above().is_valid())
        return _ability_failure(T_("You can't rise from this level!"), quiet, reason);

```

```cpp
if (!level_above().is_valid())
        return _ability_failure(T_("You can't rise from this level!"), quiet, reason);

```


4. 独立语义判断

楼层上方无有效位置导致不能上升，完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C4-04


1. 完整英文

```text
door
```


2. 生产使用者

stable crawl-ref/source/terrain.cc:907; stable crawl-ref/source/terrain.cc:908; trunk crawl-ref/source/terrain.cc:944; trunk crawl-ref/source/terrain.cc:945


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
T_("miniscule ") , T_("buggy door"),
        ""               , T_("door"),
        T_("large ")     , T_("door"),
        ""               , T_("gate"),
        T_("huge ")      , T_("gate"),
    };

```

```cpp
T_("miniscule ") , T_("buggy door"),
        ""               , T_("door"),
        T_("large ")     , T_("door"),
        ""               , T_("gate"),
        T_("huge ")      , T_("gate"),
    };

```

```cpp
T_("miniscule ") , T_("buggy door"),
        ""               , T_("door"),
        T_("large ")     , T_("door"),
        ""               , T_("gate"),
        T_("huge ")      , T_("gate"),
    };

```

```cpp
T_("miniscule ") , T_("buggy door"),
        ""               , T_("door"),
        T_("large ")     , T_("door"),
        ""               , T_("gate"),
        T_("huge ")      , T_("gate"),
    };

```


4. 独立语义判断

门与 large 等前缀组合成立。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C1-09


trunk 完整英文（版本对照）：

```text
annotate the dungeon level
```


1. 完整英文

```text
annotate the dungeon level
```


2. 生产使用者

stable crawl-ref/source/command.cc:1115; trunk crawl-ref/source/command.cc:1105


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
_add_command(cols, 0, CMD_ANNOTATE_LEVEL,
        T_("annotate the dungeon level"), 2);

```

```cpp
_add_command(cols, 0, CMD_ANNOTATE_LEVEL, T_("annotate the dungeon level"), 2);

```


4. 独立语义判断

楼层注释动作准确；trunk 源码实际也有中文条目。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C1-06


1. 完整英文

```text
For full 16-colour-mode, try setting a better TERM value than `xterm`, e.g. `xterm-256color` (most terminals) or `putty-256color` (for PuTTY).
```


2. 生产使用者

stable crawl-ref/source/command.cc:832; trunk crawl-ref/source/command.cc:832


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
// hint for the putty users:
        if (info.term == "xterm")
            s += T_("For full 16-colour-mode, try setting a better TERM value than `xterm`, e.g. `xterm-256color` (most terminals) or `putty-256color` (for PuTTY).\n");

```

```cpp
// hint for the putty users:
        if (info.term == "xterm")
            s += T_("For full 16-colour-mode, try setting a better TERM value than `xterm`, e.g. `xterm-256color` (most terminals) or `putty-256color` (for PuTTY).\n");

```


4. 独立语义判断

TERM 建议、16 色及终端示例完整；结尾换行是序列化形式。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C2-03


1. 完整英文

```text
Aiming: <white>Phantom Mirror</white>
```


2. 生产使用者

stable crawl-ref/source/evoke.cc:646; trunk crawl-ref/source/evoke.cc:637


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
args.top_prompt = T_("Aiming: <white>Phantom Mirror</white>");

```

```cpp
args.top_prompt = T_("Aiming: <white>Phantom Mirror</white>");

```


4. 独立语义判断

幻影镜瞄准提示与白色标签完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C2-02


1. 完整英文

```text
appreciates the memories.
```


2. 生产使用者

stable crawl-ref/source/potion.cc:555; trunk crawl-ref/source/potion.cc:550


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
simple_god_message(T_(" appreciates the memories."), false,
                               GOD_HEPLIAKLQANA);

```

```cpp
simple_god_message(T_(" appreciates the memories."), false,
                               GOD_HEPLIAKLQANA);

```


4. 独立语义判断

神名由 simple_god_message 补在前，记忆作为宾语正确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C2-10


1. 完整英文

```text
%s projects an invisible shield of force!
```


2. 生产使用者

stable crawl-ref/source/item-use.cc:2178; trunk crawl-ref/source/item-use.cc:2248


3. 机制与参数证据

动态参数说明：格式实参的真实生成表达式见各消费者 statement（保留完整调用，包括嵌套名称/数值表达式）。

```cpp
mprf(T_("%s projects an invisible shield of force!"),itname.c_str());

```

```cpp
mprf(T_("%s projects an invisible shield of force!"),itname.c_str());

```


4. 独立语义判断

防护铭印的无形力场护盾准确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C3-10


1. 完整英文

```text
Summonings deals with summoning creatures from another plane of reality to
temporarily aid you. Increasing Summonings skill may grant a number of effects
depending on the spell, such as longer duration or more powerful allies. Note
that summoned beings do not leave corpses and give no experience when killed,
and their equipment is as ephemeral as they are.

Being skilled in Summonings increases the success rate and spell power of
spells in this school. Many spells belong to a combination of several schools,
in which case spellcasting success and power will depend on the average skill
in these schools.
```


2. 生产使用者

stable crawl-ref/source/describe.cc:4647; stable crawl-ref/source/describe.cc:8012; stable crawl-ref/source/hints.cc:759; stable crawl-ref/source/tilereg-skl.cc:140; trunk crawl-ref/source/describe.cc:5047; trunk crawl-ref/source/describe.cc:8746; trunk crawl-ref/source/hints.cc:748; trunk crawl-ref/source/tilereg-skl.cc:140


3. 机制与参数证据

动态参数说明：lookup key = skill_name_en(skill)，skill 为技能枚举；正文由 get_skill_description 返回，describe_skill / hints / tiles UI 消费。无格式实参。

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false, &spell_fail_details);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```


4. 独立语义判断

召唤时限、无尸体经验、临时装备及多学派平均完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C5-09


trunk 完整英文（版本对照）：

```text
your religious standing (<w>%</w>)
```


1. 完整英文

```text
your religious standing (<w>%</w>)
```


2. 生产使用者

stable crawl-ref/source/hints.cc:1757


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
listed.push_back(T_("your religious standing (<w>%</w>)"));

```


4. 独立语义判断

religious standing 是在神祇面前的信仰状态、虔诚与惩戒情况，并非宗教主张或立场。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；本条存在上述术语或语义问题。 verdict=objective_error


## C6-07


1. 完整英文

```text
You cannot wall jump away from %s!
```


2. 生产使用者

stable crawl-ref/source/god-abil.cc:6391; trunk crawl-ref/source/god-abil.cc:6450


3. 机制与参数证据

动态参数说明：格式实参的真实生成表达式见各消费者 statement（保留完整调用，包括嵌套名称/数值表达式）。

```cpp
error_ret = make_stringf(T_("You cannot wall jump away from %s!"),
             beholder->name(DESC_THE, true).c_str());

```

```cpp
error_ret = make_stringf(T_("You cannot wall jump away from %s!"),
             beholder->name(DESC_THE, true).c_str());

```


4. 独立语义判断

凝视者名称填入禁止远离对象，蹬墙跳限制准确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C3-03


1. 完整英文

```text
Your Invocations skill affects the likelihood that an attempt to use divine
abilities with certain gods will be successful, and often the power of such
abilities.

{{
    if you.race() ~= "Djinni" then
        return "The Invocations skill also affects your magical reserves, " ..
               "but to a lesser degree than the Spellcasting skill. Only the " ..
               "higher contribution is used."
    end
}}
```


2. 生产使用者

stable crawl-ref/source/describe.cc:4647; stable crawl-ref/source/describe.cc:8012; stable crawl-ref/source/hints.cc:759; stable crawl-ref/source/tilereg-skl.cc:140; trunk crawl-ref/source/describe.cc:5047; trunk crawl-ref/source/describe.cc:8746; trunk crawl-ref/source/hints.cc:748; trunk crawl-ref/source/tilereg-skl.cc:140


3. 机制与参数证据

动态参数说明：lookup key = skill_name_en(skill)，skill 为技能枚举；正文由 get_skill_description 返回，describe_skill / hints / tiles UI 消费。无格式实参。

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false, &spell_fail_details);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```


4. 独立语义判断

神能成功率威力与法力储备、非灯神条件及只取较高贡献完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C2-07


1. 完整英文

```text
Your %s briefly %s through it before you manage to get a firm grip on it.
```


2. 生产使用者

stable crawl-ref/source/player-equip.cc:1976; trunk crawl-ref/source/player-equip.cc:2030


3. 机制与参数证据

动态参数说明：格式实参的真实生成表达式见各消费者 statement（保留完整调用，包括嵌套名称/数值表达式）。

```cpp
mprf_p(T_("Your %s briefly %s through it before you manage "
                    "to get a firm grip on it."),
                    hand.c_str(), conjugate_verb("pass", plural).c_str());

```

```cpp
mprf_p(T_("Your %s briefly %s through it before you manage "
                    "to get a firm grip on it."),
                    hand.c_str(), conjugate_verb("pass", plural).c_str());

```


4. 独立语义判断

第一参数为手部名称；第二参数只是 pass/passes 的英语屈折，用零精度隐藏而将动词固化为穿过，未漏实义。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C4-03


1. 完整英文

```text
The abyssal rune of Zot can be found at this depth.
```


2. 生产使用者

stable crawl-ref/source/stairs.cc:971; trunk crawl-ref/source/stairs.cc:998


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
if (!you.runes[RUNE_ABYSSAL] && you.depth >= ABYSSAL_RUNE_MIN_LEVEL)
                mpr(T_("The abyssal rune of Zot can be found at this depth."));

```

```cpp
if (!you.runes[RUNE_ABYSSAL] && you.depth >= ABYSSAL_RUNE_MIN_LEVEL)
                mpr(T_("The abyssal rune of Zot can be found at this depth."));

```


4. 独立语义判断

深渊符文可在此深度取得，可能找到的表达保留可能性。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C2-01


1. 完整英文

```text
You feel a baleful cunning.
```


2. 生产使用者

stable crawl-ref/source/player-equip.cc:2033; trunk crawl-ref/source/player-equip.cc:2087


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
case SPWPN_DEVIOUS:
            mpr(T_("You feel a baleful cunning."));

```

```cpp
case SPWPN_DEVIOUS:
            mpr(T_("You feel a baleful cunning."));

```


4. 独立语义判断

武器铭印带来的邪恶狡黠感觉准确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C3-07


1. 完整英文

```text
Forgecraft is the art of shaping tangible objects out of magic. Forgecraft
spells can construct a wide array of mechanical creatures that will fight
alongside the caster, as well as create traps and barricades and even turn the
physical resilience of one's armour into a weapon.

Being skilled in Forgecraft increases the success rate and spell power of
spells in this school. Many spells belong to a combination of several schools,
in which case spellcasting success and power will depend on the average skill
in these schools.
```


2. 生产使用者

stable crawl-ref/source/describe.cc:4647; stable crawl-ref/source/describe.cc:8012; stable crawl-ref/source/hints.cc:759; stable crawl-ref/source/tilereg-skl.cc:140; trunk crawl-ref/source/describe.cc:5047; trunk crawl-ref/source/describe.cc:8746; trunk crawl-ref/source/hints.cc:748; trunk crawl-ref/source/tilereg-skl.cc:140


3. 机制与参数证据

动态参数说明：lookup key = skill_name_en(skill)，skill 为技能枚举；正文由 get_skill_description 返回，describe_skill / hints / tiles UI 消费。无格式实参。

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false, &spell_fail_details);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```


4. 独立语义判断

魔法造实体、机械盟友、陷阱路障、护甲韧性及多学派公式完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C6-08


1. 完整英文

```text
You can't rise from this level without the Orb!
```


2. 生产使用者

stable crawl-ref/source/ability.cc:1833; trunk crawl-ref/source/ability.cc:1925


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
return _ability_failure(T_("You can't rise from this level without the Orb!"),
                                    quiet, reason);

```

```cpp
return _ability_failure(T_("You can't rise from this level without the Orb!"),
                                    quiet, reason);

```


4. 独立语义判断

离开需要宝珠的条件保留。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C3-06


1. 完整英文

```text
Fire Magic focuses mainly on dealing fire damage over long distances, with many
effective Conjurations.

Being skilled in Fire Magic increases the success rate and spell power of
spells in this school. Many spells belong to a combination of several schools,
in which case spellcasting success and power will depend on the average skill
in these schools.
```


2. 生产使用者

stable crawl-ref/source/describe.cc:4647; stable crawl-ref/source/describe.cc:8012; stable crawl-ref/source/hints.cc:759; stable crawl-ref/source/tilereg-skl.cc:140; trunk crawl-ref/source/describe.cc:5047; trunk crawl-ref/source/describe.cc:8746; trunk crawl-ref/source/hints.cc:748; trunk crawl-ref/source/tilereg-skl.cc:140


3. 机制与参数证据

动态参数说明：lookup key = skill_name_en(skill)，skill 为技能枚举；正文由 get_skill_description 返回，describe_skill / hints / tiles UI 消费。无格式实参。

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false, &spell_fail_details);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```


4. 独立语义判断

远程火焰伤害、咒法及多学派平均技能完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C5-07


trunk 完整英文（版本对照）：

```text
%s can be thrown without the use of a launcher.
```


1. 完整英文

```text
%s can be thrown without the use of a launcher.
```


2. 生产使用者

stable crawl-ref/source/hints.cc:2164


3. 机制与参数证据

动态参数说明：格式实参的真实生成表达式见各消费者 statement（保留完整调用，包括嵌套名称/数值表达式）。

```cpp
ostr << make_stringf(T_("%s can be thrown without the use of a "
                                       "launcher."), item.name(DESC_YOUR).c_str());

```


4. 独立语义判断

可投掷弹药不需发射器，物品名参数位置正确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C6-01


1. 完整英文

```text
You can't remove jewellery.
```


2. 生产使用者

stable crawl-ref/source/item-use.cc:1020; trunk crawl-ref/source/item-use.cc:1023


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
mprf(MSGCH_PROMPT, "%s",
                     oper == OPER_PUTON ? T_("You can't wear jewellery.")
                                        : T_("You can't remove jewellery."));

```

```cpp
mprf(MSGCH_PROMPT, "%s",
                     oper == OPER_PUTON ? T_("You can't wear jewellery.")
                                        : T_("You can't remove jewellery."));

```


4. 独立语义判断

无法卸下饰物限制准确，珠宝可统一为饰品但未造成机制误解。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C2-05


1. 完整英文

```text
That isn't an equippable item.
```


2. 生产使用者

stable crawl-ref/source/player-equip.cc:470; trunk crawl-ref/source/player-equip.cc:478


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
if (!item_type_is_equipment(item.base_type))
        NO_EQUIP(T_("That isn't an equippable item."))

    vector<equipment_slot> slots = get_all_item_slots(item);

```

```cpp
if (!item_type_is_equipment(item.base_type))
        NO_EQUIP(T_("That isn't an equippable item."))

    // Your god won't let you make use of gear they abhor.
    if (god_forbids_item(item, temp))
    {
        if (god_forbids)
            *god_forbids = true;

```


4. 独立语义判断

装备类别检查失败，译文准确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C5-05


trunk 完整英文（版本对照）：

```text
To do this, press <w>%%</w>, then <w>%s</w> to select %s.
```


1. 完整英文

```text
To do this, press <w>%%</w>, then <w>%s</w> to select %s.
```


2. 生产使用者

stable crawl-ref/source/hints.cc:2030


3. 机制与参数证据

动态参数说明：格式实参的真实生成表达式见各消费者 statement（保留完整调用，包括嵌套名称/数值表达式）。

```cpp
result = make_stringf(T_("To do this, press <w>%%</w>, then "
                                 "<w>%s</w> to select %s."),
                              string(1, (char)item.slot).c_str(),
                              name.c_str());

```


4. 独立语义判断

先命令后物品字母与名称顺序正确，%%先由 printf 成为命令插槽。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C3-09


1. 完整英文

```text
Being skilled in Unarmed Combat increases your accuracy, damage and attack
speed in melee combat when barehanded.
```


2. 生产使用者

stable crawl-ref/source/describe.cc:4647; stable crawl-ref/source/describe.cc:8012; stable crawl-ref/source/hints.cc:759; stable crawl-ref/source/tilereg-skl.cc:140; trunk crawl-ref/source/describe.cc:5047; trunk crawl-ref/source/describe.cc:8746; trunk crawl-ref/source/hints.cc:748; trunk crawl-ref/source/tilereg-skl.cc:140


3. 机制与参数证据

动态参数说明：lookup key = skill_name_en(skill)，skill 为技能枚举；正文由 get_skill_description 返回，describe_skill / hints / tiles UI 消费。无格式实参。

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false, &spell_fail_details);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```


4. 独立语义判断

徒手近战命中、伤害、速度三项完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C5-10


trunk 完整英文（版本对照）：

```text
didn't mind your converting to
```


1. 完整英文

```text
didn't mind your converting to
```


2. 生产使用者

stable crawl-ref/source/hints.cc:1536; stable crawl-ref/source/hints.cc:1549


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
text << T_("Fortunately, it seems that ") << old_god_name <<
                        T_(" didn't mind your converting to ") << new_god_name
                     << T_(". ");

```

```cpp
text << T_("Fortunately, it seems that ") << old_god_name <<
                        T_(" didn't mind your converting to ") << new_god_name
                     << T_(". That's because ") << old_god_name << T_(" is one of "
                        "the good gods who generally are rather forgiving "
                        "about change of faith - unless you switch over to "
                        "the path of evil, in which case their retribution "
                        "can be nasty indeed!");

```


4. 独立语义判断

两条善神改信分支均接旧神名和新神名，成句准确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C6-06


1. 完整英文

```text
you cannot sustain more frozen ramparts right now.
```


2. 生产使用者

stable crawl-ref/source/spl-util.cc:1959; trunk crawl-ref/source/spl-util.cc:1977


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
case SPELL_FROZEN_RAMPARTS:
        if (temp && you.duration[DUR_FROZEN_RAMPARTS])
            return T_("you cannot sustain more frozen ramparts right now.");

```

```cpp
case SPELL_FROZEN_RAMPARTS:
        if (temp && you.duration[DUR_FROZEN_RAMPARTS])
            return T_("you cannot sustain more frozen ramparts right now.");

```


4. 独立语义判断

已有冰霜壁垒持续时不能再维持，完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C4-01


1. 完整英文

```text
This shop has been abandoned, nothing of value remains.
```


2. 生产使用者

stable crawl-ref/source/stairs.cc:396; trunk crawl-ref/source/stairs.cc:408


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
else if (ftype == DNGN_ABANDONED_SHOP)
                mpr(T_("This shop has been abandoned, nothing of value remains."));

```

```cpp
else if (ftype == DNGN_ABANDONED_SHOP)
                mpr(T_("This shop has been abandoned, nothing of value remains."));

```


4. 独立语义判断

废弃店铺没有有价物的描述准确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C5-08


trunk 完整英文（版本对照）：

```text
Jewellery can be <w>%</w>ut on or <w>%</w>emoved again, though in Tiles, either can be done by clicking on the item in your inventory.
```


1. 完整英文

```text
Jewellery can be <w>%</w>ut on or <w>%</w>emoved again, though in Tiles, either can be done by clicking on the item in your inventory.
```


2. 生产使用者

stable crawl-ref/source/hints.cc:2306


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
#ifdef USE_TILE
            ostr << T_("Jewellery can be <w>%</w>ut on or <w>%</w>emoved again, "
                    "though in Tiles, either can be done by clicking on the item "
                    "in your inventory.");

```


4. 独立语义判断

饰品穿戴取下及图形模式点击完整，Tiles 英文可读性可改进。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；本条存在上述术语或语义问题。 verdict=readability


## C6-10


1. 完整英文

```text
You can't evoke this right now
```


2. 生产使用者

stable crawl-ref/source/describe.cc:2795; trunk crawl-ref/source/describe.cc:3065


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
case OBJ_MISCELLANY:
            case OBJ_WANDS:
                description << (T_("You can't evoke this right now"));

```

```cpp
case OBJ_MISCELLANY:
            case OBJ_WANDS:
                description << (T_("You can't evoke this right now"));

```


4. 独立语义判断

杂项和魔杖当前不能激活，译文完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C1-01


1. 完整英文

```text
wield a weapon (<w>-</w> to unwield)
```


2. 生产使用者

stable crawl-ref/source/command.cc:1239; trunk crawl-ref/source/command.cc:1213


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
_add_command(cols, 1, CMD_WIELD_WEAPON,
        T_("wield a weapon (<w>-</w> to unwield)"), 2);

```

```cpp
_add_command(cols, 1, CMD_WIELD_WEAPON,
        T_("wield a weapon (<w>-</w> to unwield)"), 2);

```


4. 独立语义判断

持握与卸下的动作及快捷键完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C3-04


1. 完整英文

```text
Evocations skill affects your ability to use magical items like wands and other
uncommon objects, increasing the power or success rate of such items.
```


2. 生产使用者

stable crawl-ref/source/describe.cc:4647; stable crawl-ref/source/describe.cc:8012; stable crawl-ref/source/hints.cc:759; stable crawl-ref/source/tilereg-skl.cc:140; trunk crawl-ref/source/describe.cc:5047; trunk crawl-ref/source/describe.cc:8746; trunk crawl-ref/source/hints.cc:748; trunk crawl-ref/source/tilereg-skl.cc:140


3. 机制与参数证据

动态参数说明：lookup key = skill_name_en(skill)，skill 为技能枚举；正文由 get_skill_description 返回，describe_skill / hints / tiles UI 消费。无格式实参。

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false, &spell_fail_details);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```


4. 独立语义判断

技能提升魔杖等物品威力或成功率，中文准确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C4-05


1. 完整英文

```text
You are entangled in a web!
```


2. 生产使用者

stable crawl-ref/source/traps.cc:1244; trunk crawl-ref/source/traps.cc:1033


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
mpr(T_("You are entangled in a web!"));

```

```cpp
mpr(T_("You are entangled in a web!"));

```


4. 独立语义判断

蛛网缠绕对象为玩家，准确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C1-08


1. 完整英文

```text
Full palette:
```


2. 生产使用者

stable crawl-ref/source/command.cc:886; trunk crawl-ref/source/command.cc:886


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
#endif

    s += T_("\nFull palette:\n");

```

```cpp
#endif

    s += T_("\nFull palette:\n");

```


4. 独立语义判断

完整色板标签正确，换行有加载器支持。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C4-07


1. 完整英文

```text
You carefully make your way through the web.
```


2. 生产使用者

stable crawl-ref/source/traps.cc:674; trunk crawl-ref/source/traps.cc:590


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
if (one_chance_in(3))
                mpr(T_("You carefully make your way through the web."));

```

```cpp
if (one_chance_in(3))
                mpr(T_("You carefully make your way through the web."));

```


4. 独立语义判断

谨慎通过蛛网，完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C1-10


1. 完整英文

```text
<w>:</w>: Browse character notes
<w>#</w>: Browse character dump
```


2. 生产使用者

stable crawl-ref/source/command.cc:918; trunk crawl-ref/source/command.cc:918


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
cols.add_formatted(0,
            T_("<w>:</w>: Browse character notes\n"
               "<w>#</w>: Browse character dump"), false);

```

```cpp
cols.add_formatted(0,
            T_("<w>:</w>: Browse character notes\n"
               "<w>#</w>: Browse character dump"), false);

```


4. 独立语义判断

角色笔记与 dump 信息区分成立，换行转义不是显示损坏。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C3-02


1. 完整英文

```text
Polearms can be evoked with ‘v’ to attack enemies from two spaces away.

Being skilled with Polearms will allow you to attack more quickly with all
weapons of this type, as well as increasing your accuracy and damage with them.

Being skilled with Polearms increases your effectiveness with Axes and Staves,
and vice versa.
```


2. 生产使用者

stable crawl-ref/source/describe.cc:4647; stable crawl-ref/source/describe.cc:8012; stable crawl-ref/source/hints.cc:759; stable crawl-ref/source/tilereg-skl.cc:140; trunk crawl-ref/source/describe.cc:5047; trunk crawl-ref/source/describe.cc:8746; trunk crawl-ref/source/hints.cc:748; trunk crawl-ref/source/tilereg-skl.cc:140


3. 机制与参数证据

动态参数说明：lookup key = skill_name_en(skill)，skill 为技能枚举；正文由 get_skill_description 返回，describe_skill / hints / tiles UI 消费。无格式实参。

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false, &spell_fail_details);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```


4. 独立语义判断

两格攻击、速度命中伤害和斧杖交叉训练都保留。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C4-02


trunk 完整英文（版本对照）：

```text
The shaft vanishes in a puff of logic!
```


1. 完整英文

```text
The shaft vanishes in a puff of logic!
```


2. 生产使用者

stable crawl-ref/source/stairs.cc:639


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
if (known_shaft)
                mpr(T_("The shaft vanishes in a puff of logic!"));

```


4. 独立语义判断

逻辑之雾是原文幽默，中文保留荒诞意象。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C1-07


1. 完整英文

```text
<h>Targeting
<w>Enter</w> or <w>f</w> : confirm current target
<w>.</w> : confirm and stop at target
<w>+</w> and <w>-</w> : cycle between targets
```


2. 生产使用者

stable crawl-ref/source/command.cc:1430; trunk crawl-ref/source/command.cc:1401


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
cols.add_formatted(
            1,
            T_("\n<h>Targeting\n"
               "<w>Enter</w> or <w>f</w> : confirm current target\n"
               "<w>.</w> : confirm and stop at target\n"
               "<w>+</w> and <w>-</w> : cycle between targets\n"),
            false);

```

```cpp
cols.add_formatted(
            1,
            T_("\n<h>Targeting\n"
               "<w>Enter</w> or <w>f</w> : confirm current target\n"
               "<w>.</w> : confirm and stop at target\n"
               "<w>+</w> and <w>-</w> : cycle between targets\n"),
            false);

```


4. 独立语义判断

确认目标、停在目标和循环目标三种操作区分正确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C2-06


1. 完整英文

```text
You feel nauseous.
```


2. 生产使用者

stable crawl-ref/source/potion.cc:139; stable crawl-ref/source/potion.cc:209; trunk crawl-ref/source/potion.cc:136; trunk crawl-ref/source/potion.cc:202


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
if (ddoor)
            mpr(T_("You feel nauseous."));

```

```cpp
mpr(T_("You feel nauseous."));

```

```cpp
if (ddoor)
            mpr(T_("You feel nauseous."));

```

```cpp
mpr(T_("You feel nauseous."));

```


4. 独立语义判断

死亡之门相关恶心感准确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C3-05


1. 完整英文

```text
Training Throwing will make thrown weapons (such as javelins) more accurate
and damaging. It also makes certain magical darts more likely to have an
effect.
```


2. 生产使用者

stable crawl-ref/source/describe.cc:4647; stable crawl-ref/source/describe.cc:8012; stable crawl-ref/source/hints.cc:759; stable crawl-ref/source/tilereg-skl.cc:140; trunk crawl-ref/source/describe.cc:5047; trunk crawl-ref/source/describe.cc:8746; trunk crawl-ref/source/hints.cc:748; trunk crawl-ref/source/tilereg-skl.cc:140


3. 机制与参数证据

动态参数说明：lookup key = skill_name_en(skill)，skill 为技能枚举；正文由 get_skill_description 返回，describe_skill / hints / tiles UI 消费。无格式实参。

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false, &spell_fail_details);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```


4. 独立语义判断

投掷命中伤害及特定飞镖效果概率准确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C5-03


trunk 完整英文（版本对照）：

```text
where
```


1. 完整英文

```text
where
```


2. 生产使用者

stable crawl-ref/source/hints.cc:1517


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
text << T_("Should you decide that abandoning ") << old_god_name
                     << T_("wasn't such a smart move after all, and you'd like to "
                        "return to your old faith, you'll have to find an "
                        "altar dedicated to ") << old_god_name << T_(" where");

```


4. 独立语义判断

接在神名祭坛后并引出重新改信，中文关系衔接成立。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C2-09


1. 完整英文

```text
%s softly glows with a divine radiance!
```


2. 生产使用者

stable crawl-ref/source/player-equip.cc:1893; stable crawl-ref/source/transform.cc:1962; trunk crawl-ref/source/player-equip.cc:1947; trunk crawl-ref/source/transform.cc:2156


3. 机制与参数证据

动态参数说明：格式实参的真实生成表达式见各消费者 statement（保留完整调用，包括嵌套名称/数值表达式）。

```cpp
mprf(T_("%s softly glows with a divine radiance!"),
                        item_name.c_str());

```

```cpp
mprf(T_("%s softly glows with a divine radiance!"),
             uppercase_first(weapon->name(DESC_YOUR)).c_str());

```

```cpp
mprf(T_("%s softly glows with a divine radiance!"),
                        item_name.c_str());

```

```cpp
mprf(T_("%s softly glows with a divine radiance!"),
             uppercase_first(weapon->name(DESC_YOUR)).c_str());

```


4. 独立语义判断

神圣光辉与柔和程度完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C3-01


trunk 完整英文（版本对照）：

```text
Hexes try to bestow various enchantments on nearby things. While none do direct
damage, being ensorcelled can effectively take an opponent out of combat,
although they often require overcoming an opponent's willpower to have an effect.
Skill in Hexes can help overcome this.

Being skilled in Hexes increases the success rate and spell power of spells in
this school. Many spells belong to a combination of several schools, in which
case spellcasting success and power will depend on the average skill in these
schools.
```


1. 完整英文

```text
Hexes try to bestow various enchantments on nearby things. While none do direct
damage, being ensorcelled can effectively take an opponent out of combat,
although they often require overcoming an opponent's willpower to have an effect.
Skill in Hexes can help overcome this.

Being skilled in Hexes increases the success rate and spell power of spells in
this school. Many spells belong to a combination of several schools, in which
case spellcasting success and power will depend on the average skill in these
schools.
```


2. 生产使用者

stable crawl-ref/source/describe.cc:4647; stable crawl-ref/source/describe.cc:8012; stable crawl-ref/source/hints.cc:759; stable crawl-ref/source/tilereg-skl.cc:140; trunk crawl-ref/source/describe.cc:5047; trunk crawl-ref/source/describe.cc:8746; trunk crawl-ref/source/hints.cc:748; trunk crawl-ref/source/tilereg-skl.cc:140


3. 机制与参数证据

动态参数说明：lookup key = skill_name_en(skill)，skill 为技能枚举；正文由 get_skill_description 返回，describe_skill / hints / tiles UI 消费。无格式实参。

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```

```cpp
result += getLongDescription(skill_name_en(skill));

```

```cpp
inf.body << get_skill_description(skill, false, &spell_fail_details);

```

```cpp
mprf(MSGCH_TUTORIAL, "%s", get_skill_description(skill).c_str());

```

```cpp
inf.body << get_skill_description(skill, true);

```


4. 独立语义判断

本条描述控制、附魔及意志抵抗的 Hexes 学派，非装备或神祇诅咒；stable 学派名与当前术语不一致，trunk 已修正。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；本条存在上述术语或语义问题。 verdict=objective_error


## C1-04


1. 完整英文

```text
No variable named '%s' to make constant
```


2. 生产使用者

stable crawl-ref/source/initfile.cc:3910; trunk crawl-ref/source/initfile.cc:3960


3. 机制与参数证据

动态参数说明：格式实参的真实生成表达式见各消费者 statement（保留完整调用，包括嵌套名称/数值表达式）。

```cpp
// should this really be case insensitive?
        if (!variables.count(state.field))
            report_error(T_("No variable named '%s' to make constant"), state.field.c_str());

```

```cpp
// should this really be case insensitive?
        if (!variables.count(state.field))
            report_error(T_("No variable named '%s' to make constant"), state.field.c_str());

```


4. 独立语义判断

不存在变量时无法设常量，名称参数保留。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C5-06


trunk 完整英文（版本对照）：

```text
That
```


1. 完整英文

```text
That
```


2. 生产使用者

stable crawl-ref/source/hints.cc:860


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
#endif

    string text = T_("That ");

```


4. 独立语义判断

图形模式拼出那个怪物是某怪物；控制台模式接怪物字形，都成立。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C1-05


1. 完整英文

```text
<h>Android Controls

<w>Back key</w>: Alias for escape
<w>Volume keys</w>: Zoom dungeon & map
Long press for right click.
Touch with two fingers for scrolling.
Toggle keyboard icon controls the
virtual keyboard visibility.
```


2. 生产使用者

stable crawl-ref/source/command.cc:938; trunk crawl-ref/source/command.cc:938


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
#ifdef __ANDROID__
    cols.add_formatted(0,
        T_("\n<h>Android Controls\n"
           "\n"
           "<w>Back key</w>: Alias for escape\n"
           "<w>Volume keys</w>: Zoom dungeon & map\n"
           "Long press for right click.\n"
           "Touch with two fingers for scrolling.\n"
           "Toggle keyboard icon controls the\n"
           "virtual keyboard visibility.\n"),
        false);

```

```cpp
#ifdef __ANDROID__
    cols.add_formatted(0,
        T_("\n<h>Android Controls\n"
           "\n"
           "<w>Back key</w>: Alias for escape\n"
           "<w>Volume keys</w>: Zoom dungeon & map\n"
           "Long press for right click.\n"
           "Touch with two fingers for scrolling.\n"
           "Toggle keyboard icon controls the\n"
           "virtual keyboard visibility.\n"),
        false);

```


4. 独立语义判断

Android 操作、缩放、长按、双指和键盘可见性完整；转义换行由加载器还原。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C6-05


1. 完整英文

```text
Jiyva prevents you from harming jellies.
```


2. 生产使用者

stable crawl-ref/source/describe-god.cc:926; trunk crawl-ref/source/describe-god.cc:934


3. 机制与参数证据

动态参数说明：无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。

```cpp
desc.cprintf(T_("Jiyva prevents you from harming jellies.\n"));

```

```cpp
desc.cprintf(T_("Jiyva prevents you from harming jellies.\n"));

```


4. 独立语义判断

吉瓦禁止伤害果冻类怪物，主体宾语准确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C7-07


1. 完整英文

```text
Invokes a powerful regeneration ability which stacks with all other sources and
is effective even on those who would not otherwise be able to regenerate. It
also fortifies the user's willpower, protecting against many magical effects.
```


2. 生产使用者

stable crawl-ref/source/ability.cc:529; stable crawl-ref/source/ability.cc:1609; stable crawl-ref/source/ability.cc:1616; stable crawl-ref/source/describe.cc:5149; stable crawl-ref/source/describe.cc:5153; trunk crawl-ref/source/ability.cc:536; trunk crawl-ref/source/ability.cc:1670; trunk crawl-ref/source/ability.cc:1677; trunk crawl-ref/source/ability.cc:1723; trunk crawl-ref/source/describe.cc:5699; trunk crawl-ref/source/describe.cc:5703


3. 机制与参数证据

动态参数与键生成：ability 枚举 → ability_name(ability, true)（英文能力名，含动态能力的 canonical 分支） + " ability" → getLongDescription；get_ability_desc 返回基础正文，可能再附加状态相关文字；本样本单位仅为 TextDB 正文。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

再生叠加与意志强化保留，但 those 不限物种，译为物种缩窄了适用对象。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；本条存在上述术语或语义问题。 verdict=objective_error


## C8-06


1. 完整英文

```text
@_Edmund_common_@

w:5
@_Edmund_rare_@

%%%%
_Edmund_common_

VISUAL:@The_monster@ gestures @at_foe@ with @possessive@ flail.

@The_monster@ clears @possessive@ throat.

@The_monster@ says, "You wouldn't believe how much I paid for this flail."

@The_monster@ asks @foe,@ "Have you met my wondrous brother?"

@The_monster@ says @to_foe@, "I might not be good at magic, but I can still kill you!"

@The_monster@ says, "People think my brother is the best. I think he's crazy."

@The_monster@ says, "I'm quite good with sums, too."

@The_monster@ says, "People accused me of being a cutpurse!"

%%%%
_Edmund_rare_

VISUAL:@The_monster@ grinds @possessive@ teeth, and then sighs.

w:1
VISUAL:@The_monster@ looks rather jealous.

@The_monster@ says, "A flail is better than a scythe, any day of the week!"

w:5
@The_monster@ says, "What use are spells, anyway?"

w:5
@The_monster@ mutters, "Who needs spells, anyway?"

@The_monster@ says, "Everyone always remembers my brother. 'Who's Edmund?' they ask!"

@The_monster@ says, "People will remember me! They'll remember me and die!"

w:1
@The_monster@ says, "Maybe I'll buy a title. How does Count Edmund sound?"

w:1
@The_monster@ whines, "My parents never had time for me!"
```


2. 生产使用者

stable crawl-ref/source/mon-speak.cc:89; stable crawl-ref/source/mon-speak.cc:271; stable crawl-ref/source/mon-speak.cc:692; stable crawl-ref/source/mon-speak.cc:863; stable crawl-ref/source/database.cc:1515; stable crawl-ref/source/database.cc:2353; stable crawl-ref/source/database.cc:2360; trunk crawl-ref/source/mon-speak.cc:90; trunk crawl-ref/source/mon-speak.cc:272; trunk crawl-ref/source/mon-speak.cc:693; trunk crawl-ref/source/mon-speak.cc:864; trunk crawl-ref/source/database.cc:1516; trunk crawl-ref/source/database.cc:2356; trunk crawl-ref/source/database.cc:2363


3. 机制与参数证据

动态参数与键生成：单位为一个根 key 的完整变体组，附递归引用的全部组（含 w: 权重；不抽单条变体）。怪物 dat/mons/*.yaml name → mons->base_name(DESC_DBNAME)；mon-speak.cc 从态度/逃跑/沉默/混乱/信仰/分支等生成 prefixes，先查 prefix + key，逐级退回裸 key / default key。database.cc _getRandomisedStr 在组内按权重取变体并递归展开 @子键@；剩余运行时占位符交给 do_mon_str_replacements(msg,*mons)。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

兄弟嫉妒、算数、爵位等完整；accused 只说明遭指控，诬陷额外断言指控为假。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；本条存在上述术语或语义问题。 verdict=objective_error


## C7-05


1. 完整英文

```text
Artificers start with a few magic wands and a club. They'll need to find better
weapons and armour before their wands run out.
```


2. 生产使用者

stable crawl-ref/source/newgame.cc:1357; stable crawl-ref/source/newgame.cc:1361; stable crawl-ref/source/database.cc:2337; trunk crawl-ref/source/newgame.cc:1336; trunk crawl-ref/source/newgame.cc:1340; trunk crawl-ref/source/database.cc:2340


3. 机制与参数证据

动态参数与键生成：职业枚举 id → get_job_name_en(id)，英文 name 来自 dat/jobs/*.yaml → getGameStartDescription(db_key)。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

魔杖与棍棒开局、耗尽前换更好装备完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C8-05


1. 完整英文

```text
@_Eustachio_common_@

w:5
@_Eustachio_rare_@

%%%%
_Eustachio_common_

@The_monster@ screams @at_foe@, "At last I'll have my revenge!"

@The_monster@ screams @at_foe@, "Hey, you killed my favourite bat!"

@The_monster@ says @to_foe@, "Summoning is fun!"

@The_monster@ says @to_foe@, "My allies will avenge me."

@The_monster@ screams, "This atrocity can only be purified with blood!"

@The_monster@ utters an oath, "I will die for my friends!"

@The_monster@ growls, "To hell with you, honourless miscreant!"

@The_monster@ asks, "How can you live without manners, virtues and honour?"

%%%%
_Eustachio_rare_

@The_monster@ yells @at_foe@, "Perjured traitor, DIE!"

VISUAL:@The_monster@ twirls @possessive@ moustache.

@The_monster@ calls on the powers of shadow!

@The_monster@ brags, "I can call spirits from the vasty deep."
```


2. 生产使用者

stable crawl-ref/source/mon-speak.cc:89; stable crawl-ref/source/mon-speak.cc:271; stable crawl-ref/source/mon-speak.cc:692; stable crawl-ref/source/mon-speak.cc:863; stable crawl-ref/source/database.cc:1515; stable crawl-ref/source/database.cc:2353; stable crawl-ref/source/database.cc:2360; trunk crawl-ref/source/mon-speak.cc:90; trunk crawl-ref/source/mon-speak.cc:272; trunk crawl-ref/source/mon-speak.cc:693; trunk crawl-ref/source/mon-speak.cc:864; trunk crawl-ref/source/database.cc:1516; trunk crawl-ref/source/database.cc:2356; trunk crawl-ref/source/database.cc:2363


3. 机制与参数证据

动态参数与键生成：单位为一个根 key 的完整变体组，附递归引用的全部组（含 w: 权重；不抽单条变体）。怪物 dat/mons/*.yaml name → mons->base_name(DESC_DBNAME)；mon-speak.cc 从态度/逃跑/沉默/混乱/信仰/分支等生成 prefixes，先查 prefix + key，逐级退回裸 key / default key。database.cc _getRandomisedStr 在组内按权重取变体并递归展开 @子键@；剩余运行时占位符交给 do_mon_str_replacements(msg,*mons)。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

复仇、蝙蝠、友谊、荣誉和夸耀召灵完整；文学深渊不机械外推游戏分支术语。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C7-09


1. 完整英文

```text
Breathes a blast of poison gas at a targeted creature.
```


2. 生产使用者

stable crawl-ref/source/ability.cc:355; stable crawl-ref/source/ability.cc:1609; stable crawl-ref/source/ability.cc:1616; stable crawl-ref/source/describe.cc:5149; stable crawl-ref/source/describe.cc:5153; trunk crawl-ref/source/ability.cc:361; trunk crawl-ref/source/ability.cc:1670; trunk crawl-ref/source/ability.cc:1677; trunk crawl-ref/source/ability.cc:1723; trunk crawl-ref/source/describe.cc:5699; trunk crawl-ref/source/describe.cc:5703


3. 机制与参数证据

动态参数与键生成：ability 枚举 → ability_name(ability, true)（英文能力名，含动态能力的 canonical 分支） + " ability" → getLongDescription；get_ability_desc 返回基础正文，可能再附加状态相关文字；本样本单位仅为 TextDB 正文。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

向目标生物喷吐毒气，准确。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C8-08


1. 完整英文

```text
w:20
@_wizard_@

w:1
@The_monster@ [grouses|grumbles] about arcanists.

w:9
__NONE

%%%%
_wizard_

@_wizard_common_spell_@
@_fake_spell_effect_@

w:8
@_wizard_medium_@

w:1
@_wizard_rare_@

%%%%
_wizard_common_spell_

@The_monster@ wildly gestures.

@The_monster@ mumbles some strange words.

@The_monster@ howls an incantation.

%%%%
_fake_spell_effect_

VISUAL:@The_monster@ shimmers violently.

VISUAL:@The_monster@ glows brightly for a moment.

VISUAL:@The_monster_possessive@ @hands@ start to glow.

VISUAL:You feel disoriented. @player_only@

VISUAL:You feel troubled. @player_only@

%%%%
_wizard_medium_

VISUAL:@The_monster@ becomes larger for a moment.

VISUAL:@The_monster_possessive@ eyes start to glow.

@The_monster@ shouts @at_foe@, "You can't withstand my power!"

@The_monster@ shouts @at_foe@, "You are history!"

%%%%
_wizard_rare_

@The_monster@ says @to_foe@, "Argatax netranoch dertex."

@The_monster@ says @to_foe@, "Dogrw nutew berg."

@The_monster@ shouts @at_foe@, "Entram moth deg ulag!"
```


2. 生产使用者

stable crawl-ref/source/mon-speak.cc:89; stable crawl-ref/source/mon-speak.cc:271; stable crawl-ref/source/mon-speak.cc:692; stable crawl-ref/source/mon-speak.cc:863; stable crawl-ref/source/database.cc:1515; stable crawl-ref/source/database.cc:2353; stable crawl-ref/source/database.cc:2360; trunk crawl-ref/source/mon-speak.cc:90; trunk crawl-ref/source/mon-speak.cc:272; trunk crawl-ref/source/mon-speak.cc:693; trunk crawl-ref/source/mon-speak.cc:864; trunk crawl-ref/source/database.cc:1516; trunk crawl-ref/source/database.cc:2356; trunk crawl-ref/source/database.cc:2363


3. 机制与参数证据

动态参数与键生成：单位为一个根 key 的完整变体组，附递归引用的全部组（含 w: 权重；不抽单条变体）。怪物 dat/mons/*.yaml name → mons->base_name(DESC_DBNAME)；mon-speak.cc 从态度/逃跑/沉默/混乱/信仰/分支等生成 prefixes，先查 prefix + key，逐级退回裸 key / default key。database.cc _getRandomisedStr 在组内按权重取变体并递归展开 @子键@；剩余运行时占位符交给 do_mon_str_replacements(msg,*mons)。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

假施法递归两行、视觉限制、选择项和胡话均保留，手部名称由运行时替换。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C7-01


1. 完整英文

```text
Frail symbionts, Vine Stalkers cannot regain health from potions. Their magical
reserves absorb damage, and they pack a magic-restoring bite.
```


2. 生产使用者

stable crawl-ref/source/newgame.cc:1357; stable crawl-ref/source/newgame.cc:1361; stable crawl-ref/source/database.cc:2337; trunk crawl-ref/source/newgame.cc:1336; trunk crawl-ref/source/newgame.cc:1340; trunk crawl-ref/source/database.cc:2340


3. 机制与参数证据

动态参数与键生成：种族枚举 id → species::name(id, species::SPNAME_PLAIN, true)，英文 name 来自 dat/species/*.yaml → getGameStartDescription(db_key)。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

吸伤与咬击恢复的是 MP；stable 法力正确，trunk 改为魔力偏离资源术语。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；本条存在上述术语或语义问题。 verdict=objective_error


## C8-02


1. 完整英文

```text
VISUAL:@The_monster@ drips [complex|unknown] stolen formulae onto the @surface@.

VISUAL:@The_monster@ is briefly caught in foreign memories of distant [stars|lands|kingdoms].

VISUAL:@The_monster@ twitches its length with the pilfered instincts of [wings|pincers|fins].
```


2. 生产使用者

stable crawl-ref/source/mon-speak.cc:89; stable crawl-ref/source/mon-speak.cc:271; stable crawl-ref/source/mon-speak.cc:692; stable crawl-ref/source/mon-speak.cc:863; stable crawl-ref/source/database.cc:1515; stable crawl-ref/source/database.cc:2353; stable crawl-ref/source/database.cc:2360; trunk crawl-ref/source/mon-speak.cc:90; trunk crawl-ref/source/mon-speak.cc:272; trunk crawl-ref/source/mon-speak.cc:693; trunk crawl-ref/source/mon-speak.cc:864; trunk crawl-ref/source/database.cc:1516; trunk crawl-ref/source/database.cc:2356; trunk crawl-ref/source/database.cc:2363


3. 机制与参数证据

动态参数与键生成：单位为一个根 key 的完整变体组，附递归引用的全部组（含 w: 权重；不抽单条变体）。怪物 dat/mons/*.yaml name → mons->base_name(DESC_DBNAME)；mon-speak.cc 从态度/逃跑/沉默/混乱/信仰/分支等生成 prefixes，先查 prefix + key，逐级退回裸 key / default key。database.cc _getRandomisedStr 在组内按权重取变体并递归展开 @子键@；剩余运行时占位符交给 do_mon_str_replacements(msg,*mons)。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

公式、偷来的记忆和肢体本能的选择项完整，抽动句略硬但未改语义。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C8-04


1. 完整英文

```text
@_Snorg_common_@

w:2
@_Snorg_rare_@

%%%%
_Snorg_common_

VISUAL:@The_monster@ pats @possessive@ sizable gut.

VISUAL:@The_monster@ beckons gently.

VISUAL:@The_monster@ smiles kindly.

VISUAL:A flash of anger passes briefly over @the_monster_possessive@ face.

VISUAL:@The_monster@ draws @possessive@ long claws delicately across @possessive@ gut.

%%%%
_Snorg_rare_

@The_monster@ remarks @to_foe@, "Ah, I'm absolutely famished!"

@The_monster@ remarks @to_foe@, "Ah, I could eat a centaur!"
```


2. 生产使用者

stable crawl-ref/source/mon-speak.cc:89; stable crawl-ref/source/mon-speak.cc:271; stable crawl-ref/source/mon-speak.cc:692; stable crawl-ref/source/mon-speak.cc:863; stable crawl-ref/source/database.cc:1515; stable crawl-ref/source/database.cc:2353; stable crawl-ref/source/database.cc:2360; trunk crawl-ref/source/mon-speak.cc:90; trunk crawl-ref/source/mon-speak.cc:272; trunk crawl-ref/source/mon-speak.cc:693; trunk crawl-ref/source/mon-speak.cc:864; trunk crawl-ref/source/database.cc:1516; trunk crawl-ref/source/database.cc:2356; trunk crawl-ref/source/database.cc:2363


3. 机制与参数证据

动态参数与键生成：单位为一个根 key 的完整变体组，附递归引用的全部组（含 w: 权重；不抽单条变体）。怪物 dat/mons/*.yaml name → mons->base_name(DESC_DBNAME)；mon-speak.cc 从态度/逃跑/沉默/混乱/信仰/分支等生成 prefixes，先查 prefix + key，逐级退回裸 key / default key。database.cc _getRandomisedStr 在组内按权重取变体并递归展开 @子键@；剩余运行时占位符交给 do_mon_str_replacements(msg,*mons)。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

拍肚、招手、笑容、怒色、长爪与饥饿台词完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C8-07


1. 完整英文

```text
@_Aizul_common_@

w:5
@_Aizul_rare_@

%%%%
_Aizul_common_

VISUAL:@The_monster@ yawns, and then pretends @subjective@ didn't.

@The_monster@ says, "Feeling sleepy?"

@The_monster@ says, "I wasn't actually sleeping!"

VISUAL:@The_monster@ hisses menacingly.

@The_monster@ screams @at_foe@, "I'll haunt your nightmares!"

%%%%
_Aizul_rare_

@The_monster@ says, "Sweet dreams!"

@The_monster@ hums a lullaby.

VISUAL:@The_monster@ coils and then uncoils.

@The_monster@ says, "Everybody has to sleep sometimes."

@The_monster@ says @to_foe@, "Fancy a snooze?"

@The_monster@ says, "They said they'd gotten someone better!"

@The_monster@ says, "Replaced! How does it feel to be replaced?"

@The_monster@ moans, "No job prospects! Who wants sleepy Aizul to guard their treasure?"

VISUAL:@The_monster@ winks several times @at_foe@.
```


2. 生产使用者

stable crawl-ref/source/mon-speak.cc:89; stable crawl-ref/source/mon-speak.cc:271; stable crawl-ref/source/mon-speak.cc:692; stable crawl-ref/source/mon-speak.cc:863; stable crawl-ref/source/database.cc:1515; stable crawl-ref/source/database.cc:2353; stable crawl-ref/source/database.cc:2360; trunk crawl-ref/source/mon-speak.cc:90; trunk crawl-ref/source/mon-speak.cc:272; trunk crawl-ref/source/mon-speak.cc:693; trunk crawl-ref/source/mon-speak.cc:864; trunk crawl-ref/source/database.cc:1516; trunk crawl-ref/source/database.cc:2356; trunk crawl-ref/source/database.cc:2363


3. 机制与参数证据

动态参数与键生成：单位为一个根 key 的完整变体组，附递归引用的全部组（含 w: 权重；不抽单条变体）。怪物 dat/mons/*.yaml name → mons->base_name(DESC_DBNAME)；mon-speak.cc 从态度/逃跑/沉默/混乱/信仰/分支等生成 prefixes，先查 prefix + key，逐级退回裸 key / default key。database.cc _getRandomisedStr 在组内按权重取变体并递归展开 @子键@；剩余运行时占位符交给 do_mon_str_replacements(msg,*mons)。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

嗜睡守卫的否认、失业与噩梦威胁完整；午觉比 snooze 稍窄但属于轻微措辞。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C8-10


1. 完整英文

```text
@_Polyphemus_common_@

w:5
@_Polyphemus_rare_@

%%%%
_Polyphemus_common_

VISUAL:@The_monster@ glares at @foe@ with @possessive@ lone eye.

VISUAL:@The_monster@ wildly rolls @possessive@ eye at @foe@.

@The_monster@ @_shouts_@ loudly for @possessive@ pets to attack!

@The_monster@ @_shouts_@ @at_foe@, "You will make a great snack!"

@The_monster@ @_shouts_@, "Attack, my pets! Attack!"

@The_monster@ says @to_foe@, "Trying to escape from me is @_pointless_@!"

%%%%
_shouts_

shouts

yells

roars

%%%%
_pointless_

pointless

senseless

useless

%%%%
_Polyphemus_rare_

VISUAL:@The_monster@ seems to be sizing @foe@ up for @possessive@ next meal.

VISUAL:@The_monster@ stomps at the @surface@ furiously.

VISUAL:@The_monster@ looks around for something heavy to throw at @foe@.

@The_monster@ says @to_foe@, "Do you like to play 'catch'?"

@The_monster@ says @to_foe@, "@Foe_genus@ for dinner? Sounds delicious!"
```


2. 生产使用者

stable crawl-ref/source/mon-speak.cc:89; stable crawl-ref/source/mon-speak.cc:271; stable crawl-ref/source/mon-speak.cc:692; stable crawl-ref/source/mon-speak.cc:863; stable crawl-ref/source/database.cc:1515; stable crawl-ref/source/database.cc:2353; stable crawl-ref/source/database.cc:2360; trunk crawl-ref/source/mon-speak.cc:90; trunk crawl-ref/source/mon-speak.cc:272; trunk crawl-ref/source/mon-speak.cc:693; trunk crawl-ref/source/mon-speak.cc:864; trunk crawl-ref/source/database.cc:1516; trunk crawl-ref/source/database.cc:2356; trunk crawl-ref/source/database.cc:2363


3. 机制与参数证据

动态参数与键生成：单位为一个根 key 的完整变体组，附递归引用的全部组（含 w: 权重；不抽单条变体）。怪物 dat/mons/*.yaml name → mons->base_name(DESC_DBNAME)；mon-speak.cc 从态度/逃跑/沉默/混乱/信仰/分支等生成 prefixes，先查 prefix + key，逐级退回裸 key / default key。database.cc _getRandomisedStr 在组内按权重取变体并递归展开 @子键@；剩余运行时占位符交给 do_mon_str_replacements(msg,*mons)。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

独眼、宠物攻击、投掷重物与食物威胁完整；喊道作独立喊叫动词时略显生硬。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；本条存在上述术语或语义问题。 verdict=readability


## C7-06


1. 完整英文

```text
Shapeshifters use talismans to shift their form, making them powerful melee
fighters (especially when unarmed) at the cost of armour.
```


2. 生产使用者

stable crawl-ref/source/newgame.cc:1357; stable crawl-ref/source/newgame.cc:1361; stable crawl-ref/source/database.cc:2337; trunk crawl-ref/source/newgame.cc:1336; trunk crawl-ref/source/newgame.cc:1340; trunk crawl-ref/source/database.cc:2340


3. 机制与参数证据

动态参数与键生成：职业枚举 id → get_job_name_en(id)，英文 name 来自 dat/jobs/*.yaml → getGameStartDescription(db_key)。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

护符变形、近战尤其徒手增益及护甲代价完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C7-08


1. 完整英文

```text
Coats a wielded weapon or your fists with slime, turning the next living or
corporeal undead monster hit into a neutral slime.
```


2. 生产使用者

stable crawl-ref/source/ability.cc:597; stable crawl-ref/source/ability.cc:1609; stable crawl-ref/source/ability.cc:1616; stable crawl-ref/source/describe.cc:5149; stable crawl-ref/source/describe.cc:5153; trunk crawl-ref/source/ability.cc:606; trunk crawl-ref/source/ability.cc:1670; trunk crawl-ref/source/ability.cc:1677; trunk crawl-ref/source/ability.cc:1723; trunk crawl-ref/source/describe.cc:5699; trunk crawl-ref/source/describe.cc:5703


3. 机制与参数证据

动态参数与键生成：ability 枚举 → ability_name(ability, true)（英文能力名，含动态能力的 canonical 分支） + " ability" → getLongDescription；get_ability_desc 返回基础正文，可能再附加状态相关文字；本样本单位仅为 TextDB 正文。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

武器或拳头、下一个命中目标、活物/有形亡灵及中立黏液效果完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C8-09


1. 完整英文

```text
w:100
__NONE

w:2
@The_monster@ caws, "Nevermore!"
```


2. 生产使用者

stable crawl-ref/source/mon-speak.cc:89; stable crawl-ref/source/mon-speak.cc:271; stable crawl-ref/source/mon-speak.cc:692; stable crawl-ref/source/mon-speak.cc:863; stable crawl-ref/source/database.cc:1515; stable crawl-ref/source/database.cc:2353; stable crawl-ref/source/database.cc:2360; trunk crawl-ref/source/mon-speak.cc:90; trunk crawl-ref/source/mon-speak.cc:272; trunk crawl-ref/source/mon-speak.cc:693; trunk crawl-ref/source/mon-speak.cc:864; trunk crawl-ref/source/database.cc:1516; trunk crawl-ref/source/database.cc:2356; trunk crawl-ref/source/database.cc:2363


3. 机制与参数证据

动态参数与键生成：单位为一个根 key 的完整变体组，附递归引用的全部组（含 w: 权重；不抽单条变体）。怪物 dat/mons/*.yaml name → mons->base_name(DESC_DBNAME)；mon-speak.cc 从态度/逃跑/沉默/混乱/信仰/分支等生成 prefixes，先查 prefix + key，逐级退回裸 key / default key。database.cc _getRandomisedStr 在组内按权重取变体并递归展开 @子键@；剩余运行时占位符交给 do_mon_str_replacements(msg,*mons)。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

静默权重100与啼叫权重2完整，Nevermore 文学表达成立。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C7-04


1. 完整英文

```text
Hunters carry a shortbow, light armour and a scroll of butterflies.
```


2. 生产使用者

stable crawl-ref/source/newgame.cc:1357; stable crawl-ref/source/newgame.cc:1361; stable crawl-ref/source/database.cc:2337; trunk crawl-ref/source/newgame.cc:1336; trunk crawl-ref/source/newgame.cc:1340; trunk crawl-ref/source/database.cc:2340


3. 机制与参数证据

动态参数与键生成：职业枚举 id → get_job_name_en(id)，英文 name 来自 dat/jobs/*.yaml → getGameStartDescription(db_key)。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

短弓、轻甲、蝴蝶卷轴完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C8-03


1. 完整英文

```text
VISUAL:@The_monster@ glitters, immutable and inevitable, in the dim dungeon light.

w:5
VISUAL:You see your fractured reflection in @the_monster@ contort and writhe. @player_only@
```


2. 生产使用者

stable crawl-ref/source/mon-speak.cc:89; stable crawl-ref/source/mon-speak.cc:271; stable crawl-ref/source/mon-speak.cc:692; stable crawl-ref/source/mon-speak.cc:863; stable crawl-ref/source/database.cc:1515; stable crawl-ref/source/database.cc:2353; stable crawl-ref/source/database.cc:2360; trunk crawl-ref/source/mon-speak.cc:90; trunk crawl-ref/source/mon-speak.cc:272; trunk crawl-ref/source/mon-speak.cc:693; trunk crawl-ref/source/mon-speak.cc:864; trunk crawl-ref/source/database.cc:1516; trunk crawl-ref/source/database.cc:2356; trunk crawl-ref/source/database.cc:2363


3. 机制与参数证据

动态参数与键生成：单位为一个根 key 的完整变体组，附递归引用的全部组（含 w: 权重；不抽单条变体）。怪物 dat/mons/*.yaml name → mons->base_name(DESC_DBNAME)；mon-speak.cc 从态度/逃跑/沉默/混乱/信仰/分支等生成 prefixes，先查 prefix + key，逐级退回裸 key / default key。database.cc _getRandomisedStr 在组内按权重取变体并递归展开 @子键@；剩余运行时占位符交给 do_mon_str_replacements(msg,*mons)。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

两条视觉描述与仅玩家分支完整，不变而必然的汉语搭配较生硬。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；本条存在上述术语或语义问题。 verdict=readability


## C7-10


1. 完整英文

```text
Casts any spell from your spell library with guaranteed success. You receive a
bonus to spell power based on your Invocations skill that is worth 50% more
than equivalent levels of training in the relevant skills of the spell itself.
```


2. 生产使用者

stable crawl-ref/source/ability.cc:523; stable crawl-ref/source/ability.cc:1609; stable crawl-ref/source/ability.cc:1616; stable crawl-ref/source/describe.cc:5149; stable crawl-ref/source/describe.cc:5153; trunk crawl-ref/source/ability.cc:528; trunk crawl-ref/source/ability.cc:1670; trunk crawl-ref/source/ability.cc:1677; trunk crawl-ref/source/ability.cc:1723; trunk crawl-ref/source/describe.cc:5699; trunk crawl-ref/source/describe.cc:5703


3. 机制与参数证据

动态参数与键生成：ability 枚举 → ability_name(ability, true)（英文能力名，含动态能力的 canonical 分支） + " ability" → getLongDescription；get_ability_desc 返回基础正文，可能再附加状态相关文字；本样本单位仅为 TextDB 正文。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

stable 祈神的150%等效与 trunk 施法等效、短期低虔诚再施放差异均各自保留。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C8-01


1. 完整英文

```text
@_crazy_yiuf_speech_@

%%%%
_crazy_yiuf_speech_

w:300
@The_monster@ @_crazy_yiuf_speech_verbs_@, "@_crazy_yiuf_sentence_@"

VISUAL:@The_monster@ waves @possessive@ quarterstaff at you. @player_only@

@The_monster@ cries, "You leg down broken song, no?"

VISUAL:@The_monster@ glowers.

VISUAL:@The_monster@ twirls on the spot.

VISUAL:@The_monster@ flaps @possessive@ cloak.

@The_monster@ says, "Crazy? Crazy!? PORCUPINE!"

@The_monster@ sings, "Trees, trees, trees, circus!"

w:2
@The_monster@ says, "I'm not crazy!"

w:2
@The_monster@ says, "What sane person could live in this world and not be crazy?"

%%%%
_crazy_yiuf_speech_verbs_

w:20
says

whimpers

cries

laughs

screams

yells

grits

%%%%
_crazy_yiuf_sentence_

w:2
@_crazy_yiuf_wordlist1_@! @_crazy_yiuf_wordlist1_@ @_crazy_yiuf_wordlist2_@ @_crazy_yiuf_wordlist2_@.

w:6
@_crazy_yiuf_wordlist1_@ @_crazy_yiuf_wordlist2_@ @_crazy_yiuf_wordlist2_@!

w:2
@_crazy_yiuf_wordlist1_@!

%%%%
_crazy_yiuf_wordlist1_

You

Peeping

Fire

Ice

Shadow

Iron

Action

Aardvark

Announcement

Paint

Snoogle

Hah

Powder

Hack

Scoff

Two

Candle

Gum

Rot

Castle

Cholesterol

Buddy

Snower

Leather

Rifle

Trifle

Fluff

Gnoll

Orb

Adder

Dawk

Goldfish

Shower

Line

Mountain

Tosser

Tonal

East

Blight

Lay

Whiteboard

Flower

Papa

Mama

Whippet

Pitchfork

Cod

Ghoul

Snurf

Goober

Prologue

Proton

Key

Island

Ten

Cards

Sif Muna

Lugonu

Nubble

Race

Seed

Cake

Citrus

Spliff

Defame

Liver

Mugger

Walk

Earwax

Millennium

Holy

Unholy

%%%%
_crazy_yiuf_wordlist2_

sing-song

sing

song

broken

hand

leg

down

bush

tired

snail

chicken

hippo

shrimp

Xom

cower

chair

blue

green

sallow

sow

horse

donkey

stair

wrapper

King

Queen

infinity

cloud

bag

tea

light

dark

lumber

ingot

water

foot

shoe

knee

arm

head

eyeball

snockshim

koolooloo

toodlewoodle

childish

ragdoll

seventy

poople

ladder

illywillydillykilly

Orb Guardian

Hive

tortoise

turtle

testudinal

return to song

mobile

senile

canine

feline

bovine

disdain

pontify

verde

hog

ena

spinner

agre

arga

meccalolo

fast

aubergine

sanguine

twenty-three

twenty-seven

forty-two

unthinkable

high

action

pizzabubble

noodlescoop

mumblescurry

alas

rumpyflump

sizzlefizz
```


2. 生产使用者

stable crawl-ref/source/mon-speak.cc:89; stable crawl-ref/source/mon-speak.cc:271; stable crawl-ref/source/mon-speak.cc:692; stable crawl-ref/source/mon-speak.cc:863; stable crawl-ref/source/database.cc:1515; stable crawl-ref/source/database.cc:2353; stable crawl-ref/source/database.cc:2360; trunk crawl-ref/source/mon-speak.cc:90; trunk crawl-ref/source/mon-speak.cc:272; trunk crawl-ref/source/mon-speak.cc:693; trunk crawl-ref/source/mon-speak.cc:864; trunk crawl-ref/source/database.cc:1516; trunk crawl-ref/source/database.cc:2356; trunk crawl-ref/source/database.cc:2363


3. 机制与参数证据

动态参数与键生成：单位为一个根 key 的完整变体组，附递归引用的全部组（含 w: 权重；不抽单条变体）。怪物 dat/mons/*.yaml name → mons->base_name(DESC_DBNAME)；mon-speak.cc 从态度/逃跑/沉默/混乱/信仰/分支等生成 prefixes，先查 prefix + key，逐级退回裸 key / default key。database.cc _getRandomisedStr 在组内按权重取变体并递归展开 @子键@；剩余运行时占位符交给 do_mon_str_replacements(msg,*mons)。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

疯言呓语的无意义词表应保留荒诞；两版本新增行已对应，递归键权重和台词主意完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C7-02


1. 完整英文

```text
Formicids are humanoid ants adept at digging. Their limbs are exceptionally
strong and they live in a state of permanent stasis.
```


2. 生产使用者

stable crawl-ref/source/newgame.cc:1357; stable crawl-ref/source/newgame.cc:1361; stable crawl-ref/source/database.cc:2337; trunk crawl-ref/source/newgame.cc:1336; trunk crawl-ref/source/newgame.cc:1340; trunk crawl-ref/source/database.cc:2340


3. 机制与参数证据

动态参数与键生成：种族枚举 id → species::name(id, species::SPNAME_PLAIN, true)，英文 name 来自 dat/species/*.yaml → getGameStartDescription(db_key)。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

挖掘、四肢强壮、永久停滞完整。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## C7-03


1. 完整英文

```text
Djinn are ever-burning spirits. They learn spells automatically as they grow,
and cast by drawing down their own fires.
```


2. 生产使用者

stable crawl-ref/source/newgame.cc:1357; stable crawl-ref/source/newgame.cc:1361; stable crawl-ref/source/database.cc:2337; trunk crawl-ref/source/newgame.cc:1336; trunk crawl-ref/source/newgame.cc:1340; trunk crawl-ref/source/database.cc:2340


3. 机制与参数证据

动态参数与键生成：种族枚举 id → species::name(id, species::SPNAME_PLAIN, true)，英文 name 来自 dat/species/*.yaml → getGameStartDescription(db_key)。

键生成及递归替换链见输入本项冻结片段。


4. 独立语义判断

成长自动学法术、消耗自身火焰施法完整，保留描述意象无需硬加生命值。


5. 术语对照与结论

依实际消费者语义检查当前 glossary；未见需要由术语表推翻的语义结论。 verdict=ok


## 补充机制证据

C7-07：补查 stable 83af93c8bd:crawl-ref/source/player.cc:1442-1444 明确 Trog 手绕过 sickness 或 inhibited regeneration，并额外 rr +=100；:7328-7329 增加意志抗性。这些限制不全由物种造成。
