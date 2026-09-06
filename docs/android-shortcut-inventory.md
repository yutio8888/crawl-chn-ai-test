# 默认快捷键与 Android 覆盖附录

## 1. 冻结范围、计数与读法

审计基线：`07ac836d23667aa165cefb7560caec35799fe2a2`。写作期间 HEAD 前进到 `ce63365bdca0abc4dc81e37e4501146effd5a837`（无关扫描器提交）；父报告核实游戏源码与术语文件对审计基线无差异，枚举校验仍直接读取冻结提交。这是源码静态盘点，不是当前安装 APK 的触控验收。术语上下文 SHA-256：`366e807eaae5403b6c3925df5970cd237b447ead76fdb717b71273473b5db67e`。

枚举权威是 [cmd-keys.h](../crawl-ref/source/cmd-keys.h) **所有非注释初始化行的条件编译并集**，不是帮助页最后显示的单个键。补集核对 [command-type.h](../crawl-ref/source/command-type.h)、[cmd-name.h](../crawl-ref/source/cmd-name.h) 和 [macro.cc](../crawl-ref/source/macro.cc) 的实际上下文分派。以下来源短路径均相对 `crawl-ref/source/`；默认键表的“行”均指 `cmd-keys.h`，按同一行各键出现顺序一一对应。

| 冻结集合 | CMD 数 | 说明 |
|---|---:|---|
| 普通上下文、有默认绑定 | 110 | 含 2 个鼠标事件命令；102 个不受绑定表条件保护，8 个有条件；不含哨兵 |
| 瞄准／查看 | 59 | 含 16 个 WIZARD 命令、2 个鼠标事件命令 |
| 层地图 | 48 | 含 2 个 WIZARD、2 个 Tiles 缩放命令 |
| 普通菜单及多选菜单 | 22 | 普通菜单 17，多选覆盖 5 |
| 角色图块编辑 | 18 | 全部 USE_TILE |
| 默认表哨兵 | 1 | NUL，不是玩家快捷键 |
| **默认表合计** | **258** | **420 条初始化行 = 419 条绑定 + 1 条哨兵** |
| 枚举中无默认绑定、非范围别名 | 34 | 27 普通、1 菜单反向模式、1 物品局部、4 合成、1 末尾哨兵 |
| 枚举范围别名 | 14 | 不是额外动作 |
| **command-type.h 全部名称** | **306** | 258 + 34 + 14 |

键保留源码写法以避免丢失同义默认绑定：`CONTROL('X')` 是 Ctrl-X；`LC_CONTROL(...)` 是 local-tiles 控制键编码；`CK_*` 是原生特殊键，不等于外观相似的可打印字符；`'\t'` 为 Tab，`' '` 为空格，`'\\'` 为反斜线，`'\''` 为单引号。数码盘与主键盘数字不可随意合并。表中竖线以 Markdown 转义显示。

**特别重要：普通状态 `s`／`.` 是等待一回合；`5`／`CK_NUMPAD_5` 是休息／长等待。Android 紧凑方向盘中心显示“等待”（英文 Wait），实际发送数字盘 5 执行休息，存在标签／行为不一致，不能记作“一回合等待”。** 标签依据 `android-project/app/src/main/res/values-zh/strings.xml:43`；绑定依据 `cmd-keys.h:10-14,31,139-141`、`command.cc:1000-1001`、`main.cc:2267-2274`。

### Android 覆盖记号与证据索引

每个普通命令均列最短已确认类别；没有列出的专用入口不算已证明。**“背包能打开”不等于每个物品命令的特殊语义已覆盖。**

- **紧**：紧凑键盘直接动作。`android-project/app/src/main/res/layout/keyboard_mobile.xml:17-213`；`android-project/app/src/main/java/org/develz/crawl/DCSSKeyboard.java:231-247,417-467`（下称 `Keyboard`）。八向移动、休息、探索、自动战斗、背包、拾取、菜单、返回；非游戏状态会隐藏游戏动作。
- **抽**：Android 命令抽屉直接入口。`topbar-drawer.cc:724-740`；拾取／出口按局面启用，出口是当前格上下楼／入店，不是存档退出（795-824）。
- **情物**：物品描述的实际可用动作，`describe.cc:3920-3964,4005-4045,4299-4328`。仅四个动作槽，直接使用优先；箭袋、改字母、铭刻、技能目标可能被挤掉。只能证明“选定该物品的操作”，不是普通命令的完整选物／批量语义。
- **情地**：地形描述上下楼、门等，`describe.cc:3761-3800,4025-4030`。受当前地形、可达性和可用动作约束。
- **快**：底部法术／能力快捷栏及抽屉 Quick Cast／Quick Abilities；`tilesdl.cc:951-1019,1299-1349`、`topbar-drawer.cc:860-929,1024-1045`。底栏空间不足隐藏、单行溢出截断；不是完整法术或能力菜单的替代。
- **触**：其他实际触屏入口。地图点按／长按：`tilereg-dgn.cc:488-594`；HUD：`tilereg-stat.cc:71-98`；日志叠层：`tilesdl.cc:1076-1081`（显示日志不自动证明历史命令入口）。
- **游**：原生 `GameMenu` 的可点条目，`main.cc:2080-2117`。与 Android 命令抽屉是两种菜单；普通 `~` 能进入原生菜单，紧凑 F1 在游戏态被 Android 拦截打开命令抽屉（`tilesdl.cc:718-732`）。所以“游”通常仍需先展开完整键盘输入 `~`，不记作紧凑直达。
- **全**：未确认紧凑／抽屉专用入口，保留完整键盘（lower／upper／ctrl／numeric）的键输入路径。`Keyboard:470-529`；`DCSSKeyboardBase.java:44-66,87-90,109-143,173-185`。Ctrl 被 `isActionEvent` 显式转发，不能引用旧报告断言当前 Ctrl-F 不可输入。特殊硬件键／组合实际送达仍需真机验收；“全”是静态路径分类，不是每键真机通过。
- 六槽情境送键与完整键盘是不同通路：`DCSSKeyboardBase.java:150-168` 的 `sendContextKey` 仅直接处理 Enter／Esc／Tab 和可打印 ASCII（32–126）；正数 Ctrl-F=6／Ctrl-S=19 被忽略。负数虽会转交 `nativeKeyboardKey`，但 `syscalls.cc:415-435` 的 JNI 白名单目前仅接受 `CK_LEFT`／`CK_RIGHT`，其余记录 Unsupported 并返回，**不是任意负数 CK 都能送达**。当前完整键盘 Ctrl 路径存在，不等于任意 Ctrl／特殊键动作可直接填入情境槽。
- **未**：该特殊动作未证实 Android 可达；**无键**：没有默认键，需绑定配置或下表所列局部入口；不能直接按 CMD 名输入。

`InputActionScope` 是最内层界面描述符，不保证六个槽永远都有内容；`Keyboard:423-436` 将不可用槽隐藏。完整／紧凑布局固定四行，不等于所有设备配置默认显示紧凑键盘（259-291,462-467）。

## 2. 普通命令：全部 110 个默认绑定 CMD

### 2.1 移动、等待与强制方向攻击

| CMD | 全部默认键 | 行 | Android／语义边界 |
|---|---|---|---|
| `CMD_WAIT` | `'s'` / `CK_CLEAR` / `CK_NUMPAD_DECIMAL` / `CK_DELETE` / `'.'` | 10,11,12,13,14 | 全；单回合等待，紧凑中心不是此命令 |
| `CMD_MOVE_DOWN_LEFT` | `CK_END` / `CK_NUMPAD_1` / `'b'` | 15,23,32 | 紧 ↙；触地图移动 |
| `CMD_MOVE_LEFT` | `CK_LEFT` / `CK_NUMPAD_4` / `'h'` | 16,24,33 | 紧 ←；触地图移动 |
| `CMD_MOVE_DOWN` | `CK_DOWN` / `CK_NUMPAD_2` / `'j'` | 17,25,34 | 紧 ↓；触地图移动 |
| `CMD_MOVE_UP` | `CK_UP` / `CK_NUMPAD_8` / `'k'` | 18,26,35 | 紧 ↑；触地图移动 |
| `CMD_MOVE_RIGHT` | `CK_RIGHT` / `CK_NUMPAD_6` / `'l'` | 19,27,36 | 紧 →；触地图移动 |
| `CMD_MOVE_DOWN_RIGHT` | `CK_PGDN` / `CK_NUMPAD_3` / `'n'` | 20,28,37 | 紧 ↘；触地图移动 |
| `CMD_MOVE_UP_RIGHT` | `CK_PGUP` / `CK_NUMPAD_9` / `'u'` | 21,29,38 | 紧 ↗；触地图移动 |
| `CMD_MOVE_UP_LEFT` | `CK_HOME` / `CK_NUMPAD_7` / `'y'` | 22,30,39 | 紧 ↖；触地图移动 |
| `CMD_REST` | `CK_NUMPAD_5` / `CK_SHIFT_CLEAR` / `CK_CTRL_CLEAR` / `'5'` | 31,139,140,141 | 紧中心显示“等待”，实际休息；长等待／恢复流程 |
| `CMD_RUN_DOWN_LEFT` | `CK_SHIFT_END` / `'B'` | 60,68 | 全；连续移动不是一次地图点按的同一命令 |
| `CMD_RUN_LEFT` | `CK_SHIFT_LEFT` / `'H'` | 61,69 | 全 |
| `CMD_RUN_DOWN` | `CK_SHIFT_DOWN` / `'J'` | 62,70 | 全 |
| `CMD_RUN_UP` | `CK_SHIFT_UP` / `'K'` | 63,71 | 全 |
| `CMD_RUN_RIGHT` | `CK_SHIFT_RIGHT` / `'L'` | 64,72 | 全 |
| `CMD_RUN_DOWN_RIGHT` | `CK_SHIFT_PGDN` / `'N'` | 65,73 | 全 |
| `CMD_RUN_UP_RIGHT` | `CK_SHIFT_PGUP` / `'U'` | 66,74 | 全 |
| `CMD_RUN_UP_LEFT` | `CK_SHIFT_HOME` / `'Y'` | 67,75 | 全 |
| `CMD_ATTACK_DOWN_LEFT` | `CONTROL('B')` / `CK_CTRL_END` | 142,150 | 全；强制方向攻击，不等于紧凑普通移动 |
| `CMD_ATTACK_LEFT` | `CONTROL('H')` / `CK_CTRL_LEFT` | 143,151 | 全；Ctrl-H 与退格的终端兼容性须留意 |
| `CMD_ATTACK_DOWN` | `CONTROL('J')` / `CK_CTRL_DOWN` | 144,152 | 全 |
| `CMD_ATTACK_UP` | `CONTROL('K')` / `CK_CTRL_UP` | 145,153 | 全 |
| `CMD_ATTACK_RIGHT` | `CONTROL('L')` / `CK_CTRL_RIGHT` | 146,154 | 全 |
| `CMD_ATTACK_DOWN_RIGHT` | `CONTROL('N')` / `CK_CTRL_PGDN` | 147,155 | 全 |
| `CMD_ATTACK_UP_RIGHT` | `CONTROL('U')` / `CK_CTRL_PGUP` | 148,156 | 全 |
| `CMD_ATTACK_UP_LEFT` | `CONTROL('Y')` / `CK_CTRL_HOME` | 149,157 | 全 |

### 2.2 战斗、法术、能力及物品

| CMD | 全部默认键 | 行 | Android／语义边界 |
|---|---|---|---|
| `CMD_USE_ABILITY` | `'a'` | 41 | 抽；快可执行具体能力；能力列表另有情境切换 |
| `CMD_UNEQUIP` | `'c'` | 42 | 全；情物可卸下具体装备，不代替通用卸装选择；使用菜单 Tab 可切入 |
| `CMD_DROP` | `'d'` | 43 | 全批量入口；情物可丢当前物品，不代表批量选择已直达 |
| `CMD_EQUIP` | `'e'` | 44 | 全；情物可装备具体物品；使用菜单 Tab 可切入 |
| `CMD_FIRE` | `'f'` | 45 | 全进入当前箭袋动作瞄准；瞄准后有情境确认，不是主游戏发射按钮 |
| `CMD_PICKUP` | `'g'` / `','` | 46,98 | 紧、抽、情物；触点自身按地面情况拾取 |
| `CMD_DISPLAY_INVENTORY` | `'i'` | 47 | 紧、抽；条目点按进入描述 |
| `CMD_AUTOFIRE` | `'p'` / `CK_SHIFT_TAB` | 49,363 | 全；不要与 Tab 自动战斗混同 |
| `CMD_QUAFF` | `'q'` | 51 | 全选药水；情物饮用当前药水 |
| `CMD_READ` | `'r'` | 52 | 全选卷轴；情物阅读当前物品 |
| `CMD_SHOUT` | `'t'` | 53 | 全；进入命令／喊叫局部界面，不是能力菜单 |
| `CMD_EVOKE` | `'V'` | 54 | 全选激活物；情物局部键为小写 v |
| `CMD_PRIMARY_ATTACK` | `'v'` | 55 | 全；主攻击动作，不等同自动战斗／查看 |
| `CMD_WIELD_WEAPON` | `'w'` | 56 | 全；情物持用当前武器，卸武器局部动作另列 |
| `CMD_CAST_SPELL` | `'z'` | 58 | 全施法菜单；快选择具体法术，仍走原施法规则 |
| `CMD_FORCE_CAST_SPELL` | `'Z'` | 59 | 全；强制进入施法不能由普通快施法自动推定 |
| `CMD_DROP_LAST` | `'D'` | 78 | 全；丢上次拾取批次，不能由单物品丢弃替代 |
| `CMD_FIRE_ITEM_NO_QUIVER` | `'F'` | 80 | 全；不改箭袋的选物发射，未证实专用触屏入口 |
| `CMD_DISPLAY_SPELLS` | `'I'` | 83 | 抽；法术列表，不等于普通施法命令 |
| `CMD_MEMORISE_SPELL` | `'M'` | 84 | 抽；法术库条目及模式情境入口 |
| `CMD_WEAR_JEWELLERY` | `'P'` | 86 | 全；情物佩戴当前物品 |
| `CMD_QUIVER_ITEM` | `'Q'` | 87 | 全箭袋选择；情物为 q 或药水时 v，槽位可能溢出 |
| `CMD_REMOVE_JEWELLERY` | `'R'` | 88 | 全；情物卸下当前物品 |
| `CMD_REMOVE_ARMOUR` | `'T'` | 91 | 全；情物脱下当前护甲 |
| `CMD_WEAR_ARMOUR` | `'W'` | 92 | 全；情物穿戴当前护甲 |
| `CMD_ADJUST_INVENTORY` | `'='` | 107 | 全完整调整流程；情物仅当前物品字母，次级槽可能溢出 |
| `CMD_INSCRIBE_ITEM` | `'{'` | 128 | 全；情物局部 i，次级槽可能溢出且教程禁用 |
| `CMD_SWAP_QUIVER_RECENT` | `']'` | 130 | 全；最近箭袋动作，不等于打开箭袋列表 |
| `CMD_CYCLE_QUIVER_BACKWARD` | `'('` | 131 | 全；与瞄准局部箭袋循环分开枚举 |
| `CMD_CYCLE_QUIVER_FORWARD` | `')'` | 132 | 全 |
| `CMD_WEAPON_SWAP` | `'\''` | 135 | 全；自动切换武器不是选定物品持用 |
| `CMD_AUTOFIGHT` | `CONTROL('I')` | 362 | 紧自动战斗发 Tab；可能移动／耗回合 |

### 2.3 地图、探索、信息与环境

| CMD | 全部默认键 | 行 | Android／语义边界 |
|---|---|---|---|
| `CMD_DISPLAY_SKILLS` | `'m'` | 48 | 抽；技能页情境见局部表 |
| `CMD_EXPLORE` | `'o'` | 50 | 紧、抽；自动探索 |
| `CMD_LOOK_AROUND` | `'x'` | 57 | 全进入光标查看；触长按直接描述格子只覆盖查看需求的一部分 |
| `CMD_DISPLAY_MUTATIONS` | `'A'` | 76 | 抽 |
| `CMD_CLOSE_DOOR` | `'C'` | 77 | 全方向提示；情地关闭指定门 |
| `CMD_EXPERIENCE_CHECK` | `'E'` | 79 | 全；HUD 等级显示不等于执行经验信息命令 |
| `CMD_INTERLEVEL_TRAVEL` | `CONTROL('G')` / `'G'` | 81,82 | 全进入；随后有旅行情境按钮 |
| `CMD_OPEN_DOOR` | `'O'` | 85 | 全方向提示；情地开指定门；普通走入门仅部分等效 |
| `CMD_DISPLAY_MAP` | `'X'` | 93 | 抽；层地图情境见第 4 节 |
| `CMD_GO_UPSTAIRS` | `'<'` | 94 | 抽当前出口、情地；触点自身受当前格限制 |
| `CMD_GO_DOWNSTAIRS` | `'>'` | 95 | 抽当前出口、情地；含入店／门道等地形语义 |
| `CMD_DISPLAY_CHARACTER_STATUS` | `'@'` | 96 | 全；HUD 状态详情抽屉是另一种展示，未判为同命令 |
| `CMD_RESISTS_SCREEN` | `'%'` | 97 | 抽角色；触长按自身角色详情路径 |
| `CMD_MAKE_NOTE` | `':'` | 99 | 全；文本输入，查看笔记并不创建笔记 |
| `CMD_READ_MESSAGES` | `'_'` | 101 | 绑定仅 !USE_TILE_LOCAL；执行还需 DGL_SIMPLE_MESSAGING（main.cc:2379-2384），非本地战斗日志 |
| `CMD_SHOW_TERRAIN` | `'\|'` | 103 | 全进入；图层切换有情境按钮 |
| `CMD_INSPECT_FLOOR` | `';'` | 104 | 全；main.cc:2257-2263 有拾取／强制自动拾取语义，长按看地面不完全等效 |
| `CMD_DISPLAY_RELIGION` | `'^'` | 105 | 抽；神祇页切换／加入属于局部动作 |
| `CMD_CHARACTER_DUMP` | `'#'` | 106 | 全生成档案；游为生成并查看的另一个 CMD |
| `CMD_DISPLAY_COMMANDS` | `'?'` | 108 | 抽、游；帮助页局部键独立 |
| `CMD_ANNOTATE_LEVEL` | `'!'` | 109 | 全；进入楼层注释输入 |
| `CMD_LIST_GOLD` | `u'€'` / `u'£'` / `u'¥'` / `u'₩'` / `'$'` | 110,111,112,113,114 | 全可用 $；商店情境 $ 是购物清单局部操作，不强行合并 |
| `CMD_LIST_JEWELLERY` | `'"'` | 127 | 全；背包装備列表不等于消息栏装备摘要 |
| `CMD_LIST_ARMOUR` | `'['` | 129 | 全；同上，command.cc:376-383 |
| `CMD_DISPLAY_KNOWN_OBJECTS` | `'\\'` | 133 | 抽；使用物品菜单也接受反斜线（item-use.cc:830-833） |
| `CMD_DISPLAY_RUNES` | `'}'` | 134 | 全；角色信息的符文显示不计专用入口 |
| `CMD_TOGGLE_AUTOPICKUP` | `CONTROL('A')` | 158 | 全；拾取按钮不是自动拾取开关 |
| `CMD_CLEAR_MAP` | `CONTROL('C')` | 159 | 全；清地图／旅行轨迹 |
| `CMD_SEARCH_STASHES` | `CONTROL('F')` | 160 | 全进入；结果页有情境排序／过滤 |
| `CMD_DISPLAY_OVERMAP` | `CONTROL('O')` | 161 | 全；地牢总览不同于 X 层地图 |
| `CMD_REPLAY_MESSAGES` | `CONTROL('P')` | 162 | 全；未由日志叠层显示推定历史入口 |
| `CMD_FIX_WAYPOINT` | `CONTROL('W')` | 165 | 全；层地图另有 w 局部入口 |
| `CMD_FULL_VIEW` | `CONTROL('X')` | 166 | 抽 Full View；列可见怪物／物品／地形 |
| `CMD_ZOOM_IN` | `LC_CONTROL('=')` / `LC_CONTROL('+')` | 448,449 | 默认绑定 USE_TILE_LOCAL；其他触屏缩放行为另需按设备验证 |
| `CMD_ZOOM_OUT` | `LC_CONTROL('-')` | 450 | 默认绑定 USE_TILE_LOCAL；同上 |

### 2.4 系统、重复、平台及调试

| CMD | 全部默认键 | 行 | Android／语义边界 |
|---|---|---|---|
| `CMD_EDIT_PLAYER_TILE` | `'-'` | 7 | USE_TILE；全或游进入；编辑器独立绑定见第 6 节 |
| `CMD_SAVE_GAME` | `'S'` | 89 | 全；有确认的存档退出；确认情境不等于入口 |
| `CMD_SAVE_GAME_NOW` | `CONTROL('S')` | 90 | 全或游；**无查询存档退出**，不是继续游玩时只存档 |
| `CMD_MACRO_MENU` | `CONTROL('D')` | 115 | 全或游；可点宏编辑菜单，原始键录入仍需键盘 |
| `CMD_MACRO_ADD` | `CONTROL('E')` | 116 | 全；快速添加宏，不等于进入管理菜单 |
| `CMD_GAME_MENU` | `'~'` / `CK_F1` | 117,118 | 紧 F1 打开 Android 抽屉；全 ~ 打开原生 GameMenu，二者不可混称 |
| `CMD_TOGGLE_TAB_ICONS` | `CK_F11` | 120 | __ANDROID__；全 F 层；旧标签页已禁用的布局中实际效果未证实 |
| `CMD_TOGGLE_KEYBOARD` | `CK_F12` | 121 | __ANDROID__；全 F 层或游；“展开完整”不是“隐藏键盘” |
| `CMD_WIZARD` | `'&'` | 124 | WIZARD；全；**调试／改变计分资格**，内部 raw 调试键不在本枚举 |
| `CMD_EXPLORE_MODE` | `'+'` | 125 | WIZARD；全；**探索模式／改变计分资格**，不是 o 自动探索 |
| `CMD_PREV_CMD_AGAIN` | ``'`'`` | 136 | 全；重做上次命令，可能耗回合 |
| `CMD_REPEAT_CMD` | `'0'` / `CK_INSERT` | 137,138 | 全；输入次数后重复下一命令，非宏列表 |
| `CMD_QUIT` | `CONTROL('Q')` | 163 | 全或游；**放弃角色／死亡**，非返回／存档退出 |
| `CMD_REDRAW_SCREEN` | `CONTROL('R')` | 164 | 全；重绘 |
| `CMD_SUSPEND_GAME` | `CONTROL('Z')` | 167 | 全候选；执行 USE_UNIX_SIGNALS，实际 SIGTSTP 排除 USE_TILE_LOCAL／Windows（main.cc:2462-2476），不等于 Android 后台 |
| `CMD_MOUSE_MOVE` | `CK_MOUSE_MOVE` | 273 | 触事件，不是可打印快捷键；不保证经普通 main 分派执行 |
| `CMD_MOUSE_CLICK` | `CK_MOUSE_CLICK` | 274 | 触事件；本地 Tiles 常由 region 直接消费（tilereg-dgn.cc:488-594） |

## 3. 瞄准／查看上下文：全部 59 个 CMD

上下文 `KMC_TARGETING`，不是普通命令。Android 专用情境仅 **Enter、Esc、-、=、r**（`directn.cc:2724-2726`），加紧凑方向键与地图目标点选（`directn.cc:2591-2602`）。下表“全”同第 1 节；“紧方向”不代表 Shift 直线发射。空格在查看模式可被改作取消，默认表本身也注明此例外（`cmd-keys.h:192`）；`directn.cc` 的运行时语义优先于静态绑定。

| CMD | 全部默认键 | 行 | Android／条件 |
|---|---|---|---|
| `CMD_TARGET_CANCEL` | `ESCAPE` / `CONTROL('G')` / `'x'` | 168,169,170 | 情取消／返回 |
| `CMD_TARGET_DESCRIBE` | `'v'` | 189 | 全；长按格子描述为其他入口，需保持目标模式 |
| `CMD_TARGET_FULL_DESCRIBE` | `CONTROL('X')` | 190 | 全；列可选目标，不等于普通 Full View |
| `CMD_TARGET_HELP` | `'?'` | 191 | 全 |
| `CMD_TARGET_SELECT` | `' '` / `CK_ENTER` / `'5'` / `CK_CLEAR` / `CK_NUMPAD_5` / `CK_NUMPAD_ENTER` / `'f'` | 192,197,198,236,253,254,255 | 情确认／紧中心；可能发射并耗回合 |
| `CMD_TARGET_CYCLE_BEAM` | `CONTROL('C')` | 193 | 全 |
| `CMD_TARGET_TOGGLE_BEAM` | `':'` | 194 | 全 |
| `CMD_TARGET_SELECT_FORCE` | `'!'` | 195 | 全；**强制选择** |
| `CMD_TARGET_SELECT_FORCE_ENDPOINT` | `'@'` | 196 | 全；**强制终点** |
| `CMD_TARGET_SELECT_ENDPOINT` | `CK_NUMPAD_DECIMAL` / `'.'` | 199,200 | 全；终点发射与 Enter 不同 |
| `CMD_TARGET_EXCLUDE` | `'e'` | 201 | 全 |
| `CMD_TARGET_FIND_PORTAL` | `'\t'` / `'\\'` | 202,203 | 全；不是层地图情境槽 |
| `CMD_TARGET_FIND_TRAP` | `'^'` | 204 | 全 |
| `CMD_TARGET_FIND_ALTAR` | `'_'` | 205 | 全 |
| `CMD_TARGET_FIND_UPSTAIR` | `'<'` | 206 | 全 |
| `CMD_TARGET_FIND_DOWNSTAIR` | `'>'` | 207 | 全 |
| `CMD_TARGET_FIND_YOU` | `'r'` | 208 | 情自身 |
| `CMD_TARGET_GET` | `'g'` | 211 | 全；目标位置拾取 |
| `CMD_TARGET_CYCLE_BACK` | `CK_NUMPAD_SUBTRACT` / `CK_NUMPAD_SUBTRACT2` / `'-'` | 212,213,214 | 情上一目标 |
| `CMD_TARGET_CYCLE_FORWARD` | `'='` / `CK_NUMPAD_ADD` / `CK_NUMPAD_ADD2` / `'+'` | 215,216,217,218 | 情下一目标 |
| `CMD_TARGET_OBJ_CYCLE_BACK` | `CK_NUMPAD_DIVIDE` / `'/'` / `';'` | 219,220,221 | 全；物体循环不同于怪物循环 |
| `CMD_TARGET_OBJ_CYCLE_FORWARD` | `CK_NUMPAD_MULTIPLY` / `'*'` / `'\''` | 222,223,224 | 全 |
| `CMD_TARGET_DOWN_LEFT` | `'b'` / `CK_END` / `CK_NUMPAD_1` | 225,237,245 | 紧方向 |
| `CMD_TARGET_LEFT` | `'h'` / `CK_LEFT` / `CK_NUMPAD_4` | 226,238,246 | 紧方向 |
| `CMD_TARGET_DOWN` | `'j'` / `CK_DOWN` / `CK_NUMPAD_2` | 227,239,247 | 紧方向 |
| `CMD_TARGET_UP` | `'k'` / `CK_UP` / `CK_NUMPAD_8` | 228,240,248 | 紧方向 |
| `CMD_TARGET_RIGHT` | `'l'` / `CK_RIGHT` / `CK_NUMPAD_6` | 229,241,249 | 紧方向 |
| `CMD_TARGET_DOWN_RIGHT` | `'n'` / `CK_PGDN` / `CK_NUMPAD_3` | 230,242,250 | 紧方向 |
| `CMD_TARGET_UP_RIGHT` | `'u'` / `CK_PGUP` / `CK_NUMPAD_9` | 231,243,251 | 紧方向 |
| `CMD_TARGET_UP_LEFT` | `'y'` / `CK_HOME` / `CK_NUMPAD_7` | 232,244,252 | 紧方向 |
| `CMD_TARGET_CYCLE_QUIVER_FORWARD` | `')'` | 233 | 全 |
| `CMD_TARGET_CYCLE_QUIVER_BACKWARD` | `'('` | 234 | 全 |
| `CMD_TARGET_SELECT_ACTION` | `'Q'` | 235 | 全；进入箭袋选择后才有其情境按钮 |
| `CMD_TARGET_DIR_DOWN_LEFT` | `'B'` / `CK_SHIFT_END` | 256,264 | 全；方向发射 |
| `CMD_TARGET_DIR_LEFT` | `'H'` / `CK_SHIFT_LEFT` | 257,265 | 全 |
| `CMD_TARGET_DIR_DOWN` | `'J'` / `CK_SHIFT_DOWN` | 258,266 | 全 |
| `CMD_TARGET_DIR_UP` | `'K'` / `CK_SHIFT_UP` | 259,267 | 全 |
| `CMD_TARGET_DIR_RIGHT` | `'L'` / `CK_SHIFT_RIGHT` | 260,268 | 全 |
| `CMD_TARGET_DIR_DOWN_RIGHT` | `'N'` / `CK_SHIFT_PGDN` | 261,269 | 全 |
| `CMD_TARGET_DIR_UP_RIGHT` | `'U'` / `CK_SHIFT_PGUP` | 262,270 | 全 |
| `CMD_TARGET_DIR_UP_LEFT` | `'Y'` / `CK_SHIFT_HOME` | 263,271 | 全 |
| `CMD_TARGET_MOUSE_MOVE` | `CK_MOUSE_MOVE` | 275 | 触鼠标兼容事件 |
| `CMD_TARGET_MOUSE_SELECT` | `CK_MOUSE_CLICK` | 276 | 触地图目标点选；**不能假定只是无副作用预览** |
| `CMD_TARGET_WIZARD_MAKE_FRIENDLY` | `'F'` | 172 | WIZARD；全；调试 |
| `CMD_TARGET_WIZARD_BLESS_MONSTER` | `'P'` | 173 | WIZARD；全；调试 |
| `CMD_TARGET_WIZARD_MAKE_SHOUT` | `'s'` | 174 | WIZARD；全；调试 |
| `CMD_TARGET_WIZARD_GIVE_ITEM` | `'o'` | 175 | WIZARD；全；调试 |
| `CMD_TARGET_WIZARD_MOVE` | `'m'` | 176 | WIZARD；全；调试 |
| `CMD_TARGET_WIZARD_PATHFIND` | `'w'` | 177 | WIZARD；全；调试 |
| `CMD_TARGET_WIZARD_MISCAST` | `'M'` | 178 | WIZARD；全；调试 |
| `CMD_TARGET_WIZARD_MAKE_SUMMONED` | `'S'` | 179 | WIZARD；全；调试 |
| `CMD_TARGET_WIZARD_POLYMORPH` | `'~'` | 180 | WIZARD；全；调试 |
| `CMD_TARGET_WIZARD_DEBUG_MONSTER` | `'D'` | 181 | WIZARD；全；调试 |
| `CMD_TARGET_WIZARD_HEAL_MONSTER` | `CONTROL('H')` | 182 | WIZARD；全；调试 |
| `CMD_TARGET_WIZARD_HURT_MONSTER` | `','` | 183 | WIZARD；全；调试 |
| `CMD_TARGET_WIZARD_DEBUG_PORTAL` | `'"'` | 184 | WIZARD；全；调试 |
| `CMD_TARGET_WIZARD_BANISH_MONSTER` | `CONTROL('B')` | 185 | WIZARD；全；调试 |
| `CMD_TARGET_WIZARD_KILL_MONSTER` | `CONTROL('K')` | 186 | WIZARD；全；调试 |
| `CMD_TARGET_WIZARD_CREATE_MIMIC` | `CONTROL('(')` | 187 | WIZARD；完整组合输入未实测 |

## 4. 层地图上下文：全部 48 个 CMD

`KMC_LEVELMAP`；Android 情境槽是 Esc、<、>、Tab、^（`viewmap.cc:945-949`）。紧凑非游戏态“确定”发 Enter，因此可触发前往目标；地图寻路可能实际移动，不能视作只关闭地图。

| CMD | 全部默认键 | 行 | Android／条件 |
|---|---|---|---|
| `CMD_MAP_HELP` | `'?'` | 278 | 全 |
| `CMD_MAP_CLEAR_MAP` | `CONTROL('C')` | 279 | 全 |
| `CMD_MAP_FORGET` | `CONTROL('F')` | 280 | 全；遗忘地图 |
| `CMD_MAP_UNFORGET` | `CONTROL('U')` | 281 | 全 |
| `CMD_MAP_ADD_WAYPOINT` | `CONTROL('W')` / `'w'` | 282,283 | 全 |
| `CMD_MAP_EXCLUDE_AREA` | `'e'` | 284 | 全 |
| `CMD_MAP_CLEAR_EXCLUDES` | `CONTROL('E')` | 285 | 全 |
| `CMD_MAP_EXCLUDE_RADIUS` | `'R'` | 286 | 全；后续半径输入独立 |
| `CMD_MAP_MOVE_DOWN_LEFT` | `'b'` / `CK_END` / `CK_NUMPAD_1` | 287,295,303 | 紧方向 |
| `CMD_MAP_MOVE_LEFT` | `'h'` / `CK_LEFT` / `CK_NUMPAD_4` | 288,296,304 | 紧方向 |
| `CMD_MAP_MOVE_DOWN` | `'j'` / `CK_DOWN` / `CK_NUMPAD_2` | 289,297,305 | 紧方向 |
| `CMD_MAP_MOVE_UP` | `'k'` / `CK_UP` / `CK_NUMPAD_8` | 290,298,306 | 紧方向 |
| `CMD_MAP_MOVE_RIGHT` | `'l'` / `CK_RIGHT` / `CK_NUMPAD_6` | 291,299,307 | 紧方向 |
| `CMD_MAP_MOVE_DOWN_RIGHT` | `'n'` / `CK_PGDN` / `CK_NUMPAD_3` | 292,300,308 | 紧方向 |
| `CMD_MAP_MOVE_UP_RIGHT` | `'u'` / `CK_PGUP` / `CK_NUMPAD_9` | 293,301,309 | 紧方向 |
| `CMD_MAP_MOVE_UP_LEFT` | `'y'` / `CK_HOME` / `CK_NUMPAD_7` | 294,302,310 | 紧方向 |
| `CMD_MAP_JUMP_DOWN_LEFT` | `'B'` / `CK_SHIFT_END` | 311,319 | 全；跳光标非一步 |
| `CMD_MAP_JUMP_LEFT` | `'H'` / `CK_SHIFT_LEFT` | 312,320 | 全 |
| `CMD_MAP_JUMP_DOWN` | `'J'` / `CK_SHIFT_DOWN` | 313,321 | 全 |
| `CMD_MAP_JUMP_UP` | `'K'` / `CK_SHIFT_UP` | 314,322 | 全 |
| `CMD_MAP_JUMP_RIGHT` | `'L'` / `CK_SHIFT_RIGHT` | 315,323 | 全 |
| `CMD_MAP_JUMP_DOWN_RIGHT` | `'N'` / `CK_SHIFT_PGDN` | 316,324 | 全 |
| `CMD_MAP_JUMP_UP_RIGHT` | `'U'` / `CK_SHIFT_PGUP` | 317,325 | 全 |
| `CMD_MAP_JUMP_UP_LEFT` | `'Y'` / `CK_SHIFT_HOME` | 318,326 | 全 |
| `CMD_MAP_PREV_LEVEL` | `'['` | 327 | 全；情地查看目的地不是层地图全局翻层按钮 |
| `CMD_MAP_NEXT_LEVEL` | `']'` | 328 | 全 |
| `CMD_MAP_GOTO_LEVEL` | `'G'` | 329 | 全 |
| `CMD_MAP_SCROLL_DOWN` | `CK_NUMPAD_ADD` / `CK_NUMPAD_ADD2` / `'+'` / `CK_MOUSE_B5` | 330,331,332,333 | 全；滚轮事件不证明触摸拖动同语义 |
| `CMD_MAP_SCROLL_UP` | `CK_NUMPAD_SUBTRACT` / `CK_NUMPAD_SUBTRACT2` / `'-'` / `CK_MOUSE_B4` | 334,335,336,337 | 全 |
| `CMD_MAP_FIND_UPSTAIR` | `'<'` | 338 | 情上行楼梯 |
| `CMD_MAP_FIND_DOWNSTAIR` | `'>'` | 339 | 情下行楼梯 |
| `CMD_MAP_FIND_YOU` | `'@'` | 340 | 全 |
| `CMD_MAP_FIND_PORTAL` | `'\t'` / `'\\'` | 341,342 | 情传送门 |
| `CMD_MAP_FIND_TRAP` | `'^'` | 343 | 情陷阱 |
| `CMD_MAP_FIND_ALTAR` | `'_'` | 344 | 全 |
| `CMD_MAP_FIND_EXCLUDED` | `'E'` | 345 | 全 |
| `CMD_MAP_FIND_WAYPOINT` | `'F'` / `'W'` | 346,347 | 全 |
| `CMD_MAP_FIND_STASH` | `'I'` / `'\''` | 348,350 | 全 |
| `CMD_MAP_FIND_STASH_REVERSE` | `'O'` | 349 | 全 |
| `CMD_MAP_GOTO_TARGET` | `CK_NUMPAD_DECIMAL` / `'.'` / `CK_NUMPAD_ENTER` / `CK_ENTER` / `'S'` / `','` / `';'` | 351,352,353,354,355,356,357 | 紧确定；目标旅行，可能耗回合 |
| `CMD_MAP_ANNOTATE_LEVEL` | `'!'` | 358 | 全 |
| `CMD_MAP_EXPLORE` | `'o'` | 359 | 全；紧凑原探索键此时变 Enter，不能算 o |
| `CMD_MAP_DESCRIBE` | `'v'` | 360 | 全 |
| `CMD_MAP_EXIT_MAP` | `ESCAPE` | 361 | 情返回／紧返回 |
| `CMD_MAP_WIZARD_TELEPORT` | `'T'` | 366 | WIZARD；全；调试传送 |
| `CMD_MAP_WIZARD_FORGET` | `CONTROL('X')` | 367 | WIZARD；全；调试 |
| `CMD_MAP_ZOOM_IN` | `LC_CONTROL('=')` / `LC_CONTROL('+')` / `'}'` | 451,452,457 | 前两键 USE_TILE_LOCAL；末键 USE_TILE；全 |
| `CMD_MAP_ZOOM_OUT` | `LC_CONTROL('-')` / `'{'` | 453,458 | 前键 USE_TILE_LOCAL；末键 USE_TILE；全 |

## 5. 菜单上下文：全部 22 个有默认绑定 CMD

`KMC_MENU` 与 `KMC_MENU_MULTISELECT` 分开；多选优先覆盖 Enter、逗号、减号等。`cmd-keys.h:370-371` 明确这些菜单命令不能在 WebTiles 重绑定，数字盘转换由 Menu 处理。菜单子类可拦截同键，因此“默认绑定存在”不保证每个菜单接受。Android 基础描述符见 `menu.cc:1564-1664`。

| CMD | 全部默认键 | 行 | Android／实际覆盖 |
|---|---|---|---|
| `CMD_MENU_UP` | `CK_UP` | 372 | 紧上下方向；触列表导航 |
| `CMD_MENU_DOWN` | `CK_DOWN` | 373 | 紧方向 |
| `CMD_MENU_LINE_UP` | `CK_SHIFT_UP` / `CK_SHIFT_LEFT` | 374,380 | 全组合；触滚动仅等效阅读，不保证同命令 |
| `CMD_MENU_RIGHT` | `CK_RIGHT` / `CK_TAB` | 375,376 | 紧右；分页背包情下一类；其他菜单可能切列／模式 |
| `CMD_MENU_LEFT` | `CK_LEFT` / `CK_SHIFT_TAB` | 377,378 | 紧左；分页背包情上一类 |
| `CMD_MENU_LINE_DOWN` | `CK_SHIFT_DOWN` / `CK_SHIFT_RIGHT` | 379,381 | 全组合；触滚动 |
| `CMD_MENU_PAGE_UP` | `'<'` / `'-'` / `CK_PGUP` | 382,383,384 | 紧数字盘映射／全；减号常被局部拦截 |
| `CMD_MENU_PAGE_DOWN` | `' '` / `'>'` / `'+'` / `CK_PGDN` | 385,386,387,388 | 紧数字盘映射／全；空格可被覆盖 |
| `CMD_MENU_SCROLL_TO_TOP` | `CK_HOME` | 389 | 紧数字盘映射／全 |
| `CMD_MENU_SCROLL_TO_END` | `CK_END` | 390 | 紧数字盘映射／全 |
| `CMD_MENU_SEARCH` | `CONTROL('F')` | 391 | 全；无独立通用情境槽 |
| `CMD_MENU_CYCLE_MODE` | `'!'` | 392 | 情，仅真实 action_cycle／toggle 存在且未保留为条目键时 |
| `CMD_MENU_CYCLE_HEADERS` | `','` | 393 | 全；多选逗号变全选，不是循环分类 |
| `CMD_MENU_HELP` | `'_'` / `'?'` | 394,395 | 情，当 help_key 存在；物品菜单可改为描述 |
| `CMD_MENU_SELECT` | `CK_ENTER` | 396 | 紧确定／情确认／触条目 |
| `CMD_MENU_EXAMINE` | `'\\'` / `'\''` | 397,398 | 全；内部菜单需支持 examine，长按条目依实现 |
| `CMD_MENU_EXIT` | `CK_MOUSE_B2` / `CK_MOUSE_CMD` / `CONTROL('G')` / `ESCAPE` | 399,400,401,402 | 紧返回／情返回；不可取消菜单例外 |
| `CMD_MENU_ACCEPT_SELECTION` | `CK_ENTER` | 405 | 多选；情确认／紧确定 |
| `CMD_MENU_SELECT_ALL` | `','` | 406 | 多选；情全选，动态判断 MF_MULTISELECT |
| `CMD_MENU_INVERT_SELECTION` | `'*'` | 407 | 多选；全，不能由全选替代 |
| `CMD_MENU_CLEAR_SELECTION` | `'-'` | 408 | 多选；全，不能由返回替代 |
| `CMD_MENU_TOGGLE_SELECTED` | `'.'` | 409 | 多选；全切换当前悬停项的选中状态，触点按条目可满足单项切换需求（menu.cc:1994-2001） |

## 6. 角色图块编辑上下文：全部 18 个 CMD

所有下列绑定受 `USE_TILE` 保护（`cmd-keys.h:411-443`），属于 `KMC_DOLL`，不是游戏行动。Android 没有核实专门情境动作行；通过完整键盘／原生 GameMenu 进入后，普通方向／确认键可能复用，仍需设备验证编辑器显示和输入。

| CMD | 全部默认键 | 行 |
|---|---|---|
| `CMD_DOLL_RANDOMIZE` | `CONTROL('R')` | 412 |
| `CMD_DOLL_SELECT_PREV_DOLL` | `'H'` / `CK_SHIFT_LEFT` | 413,415 |
| `CMD_DOLL_SELECT_NEXT_DOLL` | `'L'` / `CK_SHIFT_RIGHT` | 414,416 |
| `CMD_DOLL_SELECT_PREV_PART` | `'k'` / `CK_UP` / `CK_NUMPAD_8` | 417,421,425 |
| `CMD_DOLL_SELECT_NEXT_PART` | `'j'` / `CK_DOWN` / `CK_NUMPAD_2` | 418,422,426 |
| `CMD_DOLL_CHANGE_PART_PREV` | `'h'` / `CK_LEFT` / `CK_NUMPAD_4` | 419,423,427 |
| `CMD_DOLL_CHANGE_PART_NEXT` | `'l'` / `CK_RIGHT` / `CK_NUMPAD_6` | 420,424,428 |
| `CMD_DOLL_CONFIRM_CHOICE` | `CK_NUMPAD_ENTER` / `CK_ENTER` | 429,430 |
| `CMD_DOLL_COPY` | `CONTROL('C')` | 431 |
| `CMD_DOLL_PASTE` | `CONTROL('V')` | 432 |
| `CMD_DOLL_TAKE_OFF` | `'t'` | 433 |
| `CMD_DOLL_TAKE_OFF_ALL` | `CONTROL('T')` | 434 |
| `CMD_DOLL_TOGGLE_EQUIP` | `'*'` | 435 |
| `CMD_DOLL_TOGGLE_EQUIP_ALL` | `CONTROL('E')` | 436 |
| `CMD_DOLL_JOB_DEFAULT` | `CONTROL('D')` | 437 |
| `CMD_DOLL_CHANGE_MODE` | `'m'` | 438 |
| `CMD_DOLL_SAVE` | `ESCAPE` / `CONTROL('S')` | 439,440 |
| `CMD_DOLL_QUIT` | `'q'` / `CONTROL('Q')` | 441,442 |

## 7. 无默认键、内部命令与枚举边界

以下“行”改指 `command-type.h`。`cmd-name.h:5-299` 有命令名并不等于有默认键，也不等于任意上下文可用。`macro.cc:2125-2165,2242-2264`：27 个普通无默认名和菜单反向模式具有正常上下文；技能目标只有名称，落 `KMC_NONE`，不算通用玩家可绑定入口。宏／RC 设置可赋新键，但不计默认触屏覆盖。

| CMD | 默认键 | 枚举行 | Android／范围 |
|---|---|---|---|
| `CMD_NO_CMD_DEFAULT` | 无 | 6 | 无键；禁用键映射的特殊命令，不是游戏动作 |
| `CMD_SAFE_WAIT` | 无 | 23 | 无键；安全检查后等待，紧中心休息不能替代 |
| `CMD_SAFE_MOVE_LEFT` | 无 | 24 | 无键；普通紧方向不是 safe 版本 |
| `CMD_SAFE_MOVE_DOWN` | 无 | 25 | 无键 |
| `CMD_SAFE_MOVE_UP` | 无 | 26 | 无键 |
| `CMD_SAFE_MOVE_RIGHT` | 无 | 27 | 无键 |
| `CMD_SAFE_MOVE_UP_LEFT` | 无 | 28 | 无键 |
| `CMD_SAFE_MOVE_DOWN_LEFT` | 无 | 29 | 无键 |
| `CMD_SAFE_MOVE_UP_RIGHT` | 无 | 30 | 无键 |
| `CMD_SAFE_MOVE_DOWN_RIGHT` | 无 | 31 | 无键 |
| `CMD_CLOSE_DOOR_LEFT` | 无 | 42 | 无键；情地指定门需求部分等效，不证明此CMD入口 |
| `CMD_CLOSE_DOOR_DOWN` | 无 | 43 | 无键 |
| `CMD_CLOSE_DOOR_UP` | 无 | 44 | 无键 |
| `CMD_CLOSE_DOOR_RIGHT` | 无 | 45 | 无键 |
| `CMD_CLOSE_DOOR_UP_LEFT` | 无 | 46 | 无键 |
| `CMD_CLOSE_DOOR_DOWN_LEFT` | 无 | 47 | 无键 |
| `CMD_CLOSE_DOOR_UP_RIGHT` | 无 | 48 | 无键 |
| `CMD_CLOSE_DOOR_DOWN_RIGHT` | 无 | 49 | 无键 |
| `CMD_TOGGLE_SOUND` | 无 | 55 | 无键；声音功能受构建支持限制，不因枚举存在而承诺有效 |
| `CMD_PICKUP_QUANTITY` | 无 | 57 | 无键；main.cc:2276-2278 与普通拾取参数不同；旧物品region有引用不证明Android主布局直达 |
| `CMD_ZAP_WAND` | 无 | 79 | 无键；main.cc:2300 独立 zap_wand；情物激活魔杖是需求等效，不是默认CMD绑定 |
| `CMD_LOOKUP_HELP` | 无 | 101 | 游 / 条目（main.cc:2104-2105）或帮助页 /；不是按斜线直接从地牢查询 |
| `CMD_EXPLORE_NO_REST` | 无 | 117 | 无键；main.cc:2411；紧探索不是“不休息探索” |
| `CMD_AUTOFIGHT_NOMOVE` | 无 | 134 | 无键；紧自动战斗不保证不移动 |
| `CMD_SHOW_CHARACTER_DUMP` | 无 | 162 | 游 #；生成并查看（main.cc:2394-2403），不同于仅生成 |
| `CMD_REVEAL_OPTIONS` | 无 | 165 | TARGET_OS_MACOSX；非 Android，main.cc:2386-2393 |
| `CMD_LUA_CONSOLE` | 无 | 167 | 无键；调试／脚本执行，main.cc:2516-2518；不计普通触屏功能 |
| `CMD_SET_SKILL_TARGET` | 无 | 172 | 仅物品局部 s，情物次级槽；非普通上下文、不能因cmd-name有名就承诺正常bindkey |
| `CMD_MENU_CYCLE_MODE_REVERSE` | 无 | 319 | 无键；KMC_MENU，可自定义绑定；不等于通用左键在所有菜单的行为 |
| `CMD_DISABLE_MORE` | 无 | 361 | 内部合成命令：关闭 more |
| `CMD_ENABLE_MORE` | 无 | 363 | 内部合成命令：开启 more |
| `CMD_UNWIELD_WEAPON` | 无 | 364 | 合成／物品局部 u；情物卸武器，非通用普通绑定 |
| `CMD_NEXT_CMD` | 无 | 367 | 内部忽略并请求下一输入 |
| `CMD_MAX_CMD` | 无 | 370 | 枚举末尾哨兵，不是命令 |

默认表末尾独立哨兵：

| CMD | 默认表字面值 | cmd-keys.h 行 | 范围 |
|---|---|---|---|
| `CMD_NO_CMD` | `'\0'` | 461 | 表终止，macro.cc:2146-2147 不安装此绑定 |

14 个范围别名（`command-type.h` 行号）；不重复计入实际动作：

| 别名 | 指向 | 行 |
|---|---|---|
| `CMD_MIN_TILE` | `CMD_EDIT_PLAYER_TILE` | 145 |
| `CMD_MAX_TILE` | `CMD_EDIT_PLAYER_TILE` | 146 |
| `CMD_MAX_NORMAL` | `CMD_LUA_CONSOLE` | 169 |
| `CMD_MIN_OVERMAP` | `CMD_MAP_CLEAR_MAP` | 176 |
| `CMD_MAX_OVERMAP` | `CMD_MAP_EXIT_MAP` | 239 |
| `CMD_MIN_TARGET` | `CMD_TARGET_DOWN_LEFT` | 243 |
| `CMD_MAX_TARGET` | `CMD_TARGET_HELP` | 304 |
| `CMD_MIN_MENU` | `CMD_MENU_UP` | 307 |
| `CMD_MAX_MENU` | `CMD_MENU_EXIT` | 325 |
| `CMD_MIN_MENU_MS` | `CMD_MENU_ACCEPT_SELECTION` | 329 |
| `CMD_MAX_MENU_MS` | `CMD_MENU_TOGGLE_SELECTED` | 334 |
| `CMD_MIN_DOLL` | `CMD_DOLL_RANDOMIZE` | 339 |
| `CMD_MAX_DOLL` | `CMD_DOLL_QUIT` | 357 |
| `CMD_MIN_SYNTHETIC` | `CMD_DISABLE_MORE` | 362 |

## 8. 不由 cmd-keys.h 穷举的局部输入

本节列出独立来源、已核实的局部键与 Android 覆盖。**这是对默认玩家界面的补充，不宣称穷举源码每个 raw 字符分支。** 字母／数字动态分配的物品、法术、能力、分支、楼层、菜单项目须以当前界面为准，不冻结成所有角色共有的键表。

| 界面／独立来源 | 已核实局部键与语义 | Android 实际覆盖／剩余边界 |
|---|---|---|
| 是非确认：prompt.cc:200-229,261-279；menu.cc:1601-1613 | Y/N；有 ask_always 才有 A；Enter 是否采用默认由调用者控制；Esc 可映射默认答案；调用者可另加 explicit_keymap | 情境是／否／总是只显示实际答案；不能把所有确认都当 Enter=是。保存确认额外 S→y 见 main.cc:2484-2487。危险确认可要求大写／更强输入，不由 cmd-keys 表给出 |
| more：message.cc:2015-2036 | 空格、Enter／换行、数字盘 Enter 继续；Esc 类键设置 more 自动清除；非 user_forced 时鼠标点击也继续 | 情境“继续”发空格；没有独立默认 more CMD，不能与等待一回合混同；返回可能改变后续消息清除行为 |
| 背包／拾取：menu.cc:1586-1599；known-items.cc:131-137 | 分页时左右切类；多选逗号全选；! 模式；已知物品额外 - 切已识别／未识别；条目字母和数量动态 | 有确认／返回／前后类／全选／切模式；没有把 * 反选、- 清选统称为全选覆盖 |
| 使用物品：item-use.cc:793-863 | 装备类 Tab 在装备／卸下间切换；! 操作模式；- 徒手；逗号切背包／地面或 easy_floor_use；? 描述；反斜线已知物品；数字铭刻选择 | Tab、!、-、逗号、? 按条件排入四个候选槽；末项可能放不下。反斜线／数字仍需全键盘，局部菜单被进入才有这些动作 |
| 物品描述：describe.cc:3970-4045,4299-4328 | w 持用／穿戴；u 卸武器；t 脱护甲；v 激活；r 阅读／摘下；p 佩戴；q 饮用／放箭袋；药水箭袋改 v；g 拾取／前往；d 丢弃；i 铭刻；= 改字母；s 技能目标 | 情物取真实可用列表，四动作上限、直接动作优先；不能宣称每个描述页同时有所有按钮；局部小写不等同主游戏默认键 |
| 法术列表：spl-cast.cc:224-244；法术库 spl-book.cc:731-769 | 列表 ! 模式／列切换、? 描述当前法术；法术库 ! 施法／记忆／描述／隐藏等模式、? 帮助、Ctrl-F 搜索；搜索中 Esc 先退出搜索；字母对应当前法术 | 列表 !／?、法术库 !／? 有情境候选；Ctrl-F 没有独立槽。快栏可选择具体已记忆法术，不穷举字母分配 |
| 法术描述：describe.cc:5085-5087 | Esc 返回；描述界面不是默认施法菜单 | 当前专用情境仅返回，**没有据此确认“描述页一键施法”** |
| 能力：ability.cc:3981-4012,4045-4074，menu.cc:1655-1663 | 动态能力字母；ToggleableMenu 的 ! 切换 | 抽／快进入；可用切换由菜单决定，不是任意能力都有固定键 |
| 喊叫／盟友命令：shout.cc:485-506,529-630,673-698 | 主游戏 t 先进入提示；局部 t 喊叫（! 为旧键兼容）；a 攻击新目标；r 撤退方向；s 停止攻击；g 守卫区域；f 跟随；Esc 或其他未识别键取消。能否说话、狂暴／混乱影响提示及命令可用性；a/r 后再进入目标选择 | 提示直接 `get_ch()`，shout.cc 没有 `InputActionScope`／`InputScreen` 注册，依赖完整键盘局部字母；仅增加主游戏 t 按钮不足以覆盖下层操作。a/r 的后续瞄准可用已有目标情境键，但不能倒推前置 a/r 已有入口；成功喊叫／发令耗回合 |
| 地形／怪物／神祇描述：describe.cc:203-208,3761-3800,4025-4030,7627-7632；describe-god.cc:1262,1344,1404 附近 | ! 切页面／引言；地形 < > [ ] o c 按可用动作；神祇加入 Enter 后 Y/N | 有返回、适用时切页、地形动作和加入确认；不是通用动作轮盘，也不表示地牢 o/c 含义改变 |
| 技能：skill-menu.cc:1142-1177,1531-1588 | / 训练模式；竖线或 Tab 训练／专注动作；* 显示技能；_ 等级显示；! 视图；= 设目标；- 清目标；? 帮助；经验模式 Enter | 四候选槽优先 =、!、-、/、*、?（依局面截断）；菜单内部切换行仍可点。竖线、_ 不在该情境候选表；不可写成“所有技能键均有底栏按钮” |
| 商店：shopping.cc:983-994,1478-1515 | ! 购买／查看；/ 排序；$ 购物清单；物品字母与多选购买 | 情境 !、/、$，!/$ 仅 can_purchase；确认／返回由 Menu 描述符补充。购买行为与物品查询不同，不能在所有商店状态承诺同一按钮 |
| 藏品搜索：stash.cc:1113-1162,1552-1557,1641-1652 | 空搜索位置 ? 帮助；Enter 可复用上次搜索；结果 ! 旅行／查看、/ 排序、= 过滤无用／重复物品 | 搜索输入为 TEXT 全键盘；结果 !、/、= 有情境入口；主游戏 Ctrl-F 本身仍属于全键盘入口 |
| 跨层旅行：travel.cc:2450-2464,2483-2495,2506-2577 | Tab 默认目标；* 路径点；_ 祭坛；? 帮助；允许时 < > 上下层；Ctrl-P 父分支；. 当前分支；0–9 路径点；分支字母动态；Enter 在消息栏／菜单形式有所不同 | 情境仅 Tab、*、_、? 条件提供；< >、Ctrl-P、.、数字没有据此记为独立情境槽；分支条目可点；! 可保留为分支快捷键而非切模式 |
| 箭袋动作：quiver.cc:2764-2825 | ! 聚焦模式；* 或 % 背包；& 全部法术；^ 全部能力；- 清空；数字铭刻；逗号分类行为见2730-2754 | 情境 ! 后三个槽按物品／法术／能力／清空排序，- 可被挤掉；% 是备用键但不另有按钮；不能等同主游戏 ] 最近动作 |
| 显示图层：view.cc:1035-1094 | a 全部，m 怪物，p 玩家，i 物品，c 云雾，其他键退出；!USE_TILE_LOCAL 另有 w 怪物武器、h 怪物健康 | 情境有 a/m/p/i/c 与 Esc；w/h 非 Android 本地图块分支；须先进入图层界面，不能在地牢直接发送这些局部字母 |
| 帮助：command.cc:455-480,1497-1517,1546-1625 | ? 快捷键页；Home 目录；* 手册；% 资质；^ 入门；~ 宏帮助；& 配置帮助；t Tiles（USE_TILE_LOCAL）；: 笔记；# 档案；/ 查询；q FAQ；v 版本；! 诊断；Esc 返回 | 抽可打开帮助；普通滚动页无专属情境行。局部页跳转不能仅凭正文看见热键就声称文字可点；手册章节热键来自所加载文件，不在 CMD 冻结表 |
| 帮助查询 ?/：lookup-help.cc:1502-1545,1044 附近 | M 怪物、S 法术、K 技能、A 能力、C 卡牌、I 物品、F 地形、G 神祇、B 分支、L 云雾、P 被动、T 状态、U 突变、N 灾祸；类型选择大小写兼容；部分结果 Ctrl-S 排序 | 类型条目走菜单，搜索走文本；未确认 Ctrl-S 专用触屏按钮；不要沿用旧报告断言当前完整 Ctrl 层不可送达 |
| 原生 GameMenu：main.cc:2080-2117 | Esc 返回；S 保存退出；# 生成并查看档案；- 角色图块（LOCAL）；~ 宏；? 帮助；/ 查询；O 显示配置文件（macOS）；F12 键盘（Android）；Q 放弃角色 | 条目可点，但 Android 紧凑 F1 拦截为另一命令抽屉；主游戏 ~ 是进入本菜单的键，不是直接打开宏编辑器 |
| 宏编辑：macro.cc:1016-1170,1194-1234,1279-1347,1430-1530,1607-1650 | 管理 ! 循环宏／各上下文键映射、~ 新建／编辑触发键、- 清空当前模式映射；触发键录入 ~ 按数字键码；编辑 r 重定义、R 原始输入、c 清除、a 放弃、? 帮助；原始输入 Enter 结束、Esc/Ctrl-G 取消；列表 Delete/Backspace 删除当前映射 | 菜单条目可点，未注册专属宏情境行；原始触发键捕获不接受任意鼠标事件替代。管理模式／用户映射内容不是固定默认命令集合 |
| 行编辑：cio.cc:924-1065 | Esc 系取消；↑/Ctrl-P 前历史、↓/Ctrl-N 后历史；Enter 提交；Ctrl-K 删到末尾；Delete/Ctrl-D 删当前；Backspace 删前字符；Ctrl-W 删词；Ctrl-U 删到开头；←/Ctrl-B、→/Ctrl-F 移光标；Home/Ctrl-A、End/Ctrl-E 首尾 | TEXT 自动完整键盘，历史仅有 history 时有效；当前实现鼠标点击尚不定位文本光标（1049-1051）；键组合路径存在不代表 IME 和每种输入框均实测通过 |

### 条件、隐藏状态与非目标

- 本文冻结的是该提交的 DCSS 分支，不外推旧版 `e/c/v/V` 等命令含义，也不把未来版本的新命令补进当前集合。
- USE_TILE（绑定：角色编辑器／地图括号缩放）、USE_TILE_LOCAL（本地 Ctrl 缩放；排除 `_` 在线消息）、__ANDROID__（F11/F12）、WIZARD（调试／探索模式）均保留；这些是源码并集，不是声称某 APK 同时编译所有平台条件。
- 技能、商店、物品等局部动作由实际游戏状态／菜单 flags 决定；只有提供的槽位算情境覆盖。不可用条目、隐藏快捷栏、旧侧栏均不能计作始终可见入口。
- 不穷举任意 RC `bindkey`、用户宏展开、Lua 自定义命令、所有动态条目字母／铭刻数字、系统 IME 编辑组合、桌面窗口快捷键，以及 WIZARD 入口后的所有 raw 调试键。调试原始处理入口见 [wizard.cc:52-248,272 起](../crawl-ref/source/wizard.cc)，默认表中的 WIZARD CMD 已完整收录。
- 本节局部来源清单不是“全部 C++ 输入分支”的形式证明；对独立子界面未列出的 raw 键，应回到该页 `process_key`／输入回调核对，不由此制造默认 CMD。

## 9. 校验与待核实项

文档集合校验以表格首列精确 CMD 标识为准：默认表 258 个名称全部有行；每个默认键字面值及其源行对应核对；枚举 306 个名称（含别名与哨兵）全部有记录。无默认普通命令单独列出，不拿 `CMD_*` 前缀字符串命中数充当动作数。

实际校验通过：306 个首列名称各出现一次；258 个默认表 CMD 的全部 420 对“键字面值／行号”完全一致（含哨兵），缺失／多余／重复均为零；相对链接目标存在，无行尾空白。`git diff --check` 返回 0；新文件额外以 `git diff --no-index --check -- /dev/null docs/android-shortcut-inventory.md` 检查，无空白诊断，返回 1 表示新文件差异。只运行文档差异检查和内存枚举比较，不构建、不运行游戏、不提交。需后续设备验收：完整 Ctrl／Shift／特殊键实际输入，目标点击是否直接执行、不同菜单的数字盘转换，快捷栏隐藏／溢出及情境候选截断，原生 GameMenu 与 Android 抽屉的入口区别，平台键 F11/F12 的实际效果。所有“全／紧／抽／情／触”均保留此静态证据边界。


## 10. P1–P3 实施后的缺口表

以下与覆盖报告 §4.5 同步；上文枚举仍是冻结基线，默认绑定并未改写。阶段实现不等于已合并，验收与交付状态见 [P3 验证记录](android-shortcut-p3-verification.md)。

| 优先级 | 功能与默认键 | 当前覆盖判定 | 缺口与推荐落点  P1–P3 实施后判定 |
|---|---|---|------|
| P0 | 单回合等待 `.` / `s` | **无独立紧凑／抽屉入口**；完整键盘可达，点自己仅条件覆盖 | 中心或固定游戏态动作槽；与自动休息分开  P1：紧凑中心独立等待；休息在第四行。 |
| P1 | 饮用 `q`、阅读 `r`、激活 `V` | 物品描述可间接使用，但没有对应主游戏快捷键/抽屉命令 | 紧急道具不宜每次打开背包找物品再开描述；`q/r`优先第四行，`V`进抽屉  P1：饮用、阅读直接可达；P2：激活抽屉入口。 |
| P1 | 箭袋动作 `f`、不改箭袋指定物品发射 `F`、主攻击 `v` | 无主紧凑/抽屉对应入口；自动战斗不等价 | 默认直接暴露 `f`；`F/v`进入战斗动作组，保持命令差别  P1：射击直接可达；P2：发射物品、主攻击抽屉入口。 |
| P1 | 不移动自动战斗 `CMD_AUTOFIGHT_NOMOVE` | **无默认键**，不是打开完整键盘就能使用；当前 Tab 对应的自动战斗可能移动 | 用现有抽屉直接返回该命令，或专用动作；不要错误标成 `p/Shift-Tab`  P2：抽屉直接返回 CMD_AUTOFIGHT_NOMOVE。 |
| P1 | 强制定向攻击 Ctrl + 八方向 | 只有完整 Ctrl 层；紧凑八方向是普通移动/相邻攻击 | 战斗“原地攻击”模式或专用入口，明显提示与单次复位；普通移动不能替代打不可见敌人位置  未纳入本次三阶段；完整 Ctrl 层保留。 |
| P1 | 强制施法 `Z`；瞄准 `!` / `@` | 快捷施法普通路径不等于强制施法；目标情境行只有普通确认等五项 | 高级战斗/瞄准操作；区分“启动强制施法”与“强制确认目标/终点”  P3：目标与终点强制确认在“更多”；强制施法 Z 仍无专用入口。 |
| P1 | 箭袋选择 `Q`、最近 `]`、前后 `(`/`)` | 全局入口缺；物品描述设定单件箭袋不是全局选择 | 增加箭袋入口；已有 QUIVER 页可复用，但其清空动作仍有条件截断  P2：箭袋抽屉入口；P3：目标页前后切换；最近动作与箭袋页溢出仍未覆盖。 |
| P1 | 喊叫／盟友命令 `t` | 主入口缺，**后续字母选项也未接入情境描述符** | 不能只加一个 `t` 按钮；`shout.cc:485–506` 的 `t/a/r/s/g/f` 与取消应一起适配  P2：抽屉及六槽喊叫子提示；取消沿用返回。 |
| P1 | 藏品搜索 `Ctrl-F` | 仅完整 Ctrl 层；结果页已有排序 `/`、过滤 `=` | 先在抽屉加入 `CMD_SEARCH_STASHES`，直接复用原生搜索流程；不必先扩 Ctrl 情境桥  P2：搜索抽屉入口，TEXT 输入复用原流程。 |
| P1 | 多选丢弃 `d`、数量操作 | **主入口缺**；单物品描述 `d` 不等于多选 | `invent.cc:1496–1520` 背包是单选描述；新增 `CMD_DROP`入口后复用已有多选、分类、全选、确认  P2：丢弃抽屉入口，复用多选与数量流程。 |
| P1 | 跨层旅行 `G`、地牢概览 `Ctrl-O` | 抽屉的地图 `X`不是 `G` 或概览 | 增加明确入口；旅行页虽已有默认目标/路径点等按钮，不能反推主入口完整  P2：跨层旅行与地牢概览抽屉入口。 |
| P1 | 大地图排除 `e`、半径 `R`、清除 Ctrl-E、路径点 `w`/Ctrl-W | MAP 行无这些动作 | 增加地图“更多”；`R`后还要输入数字，不能只加前缀按钮；详见 `viewmap.cc:1082–1111`  P3：MAP 更多列表；半径与路径点编号发布 TEXT，清除走原生控制键。 |
| P2 | 全局关门 `C`、开门 `O` | 无全局快捷入口，但相邻门长按描述→FEATURE `c/o` **条件可达** | 比完全缺功能优先级低；在战斗/地形动作组显化，不重造开关门实现  未新增全局入口；保持 FEATURE 条件可达。 |
| P2 | 武器切换 `'`、上次拾取丢弃 `D` | 背包装备操作不等价于这些快速命令 | 战斗/物品组；不把操作效果近似算作精确覆盖  P2：武器切换已补；上次拾取丢弃 D 仍未补。 |
| P2 | 铭刻 `{`、调整字母 `=`、物品技能目标 | 物品页候选存在，但业务槽最多四个，后排可被截断 | 提供该页可用动作的“更多”；不能对所有物品统一写“都有”或“都没有”  P3：按物品实际候选溢出到更多，已实测刻写。 |
| P2 | 重复上次反引号、重复次数 `0`/Insert | 紧凑无入口；方向盘数字盘键不等于文本数量数字 | 高级组；必须同时处理次数输入、中断、危险确认，不建议默认长按隐式重复  未纳入本次三阶段。 |
| P2 | 查询排序 `?/` 页面中的 Ctrl-S | 仅完整 Ctrl 层；不是藏品搜索结果 `/` 排序 | 需要局部上下文动作及输入桥支持；防止 Ctrl-S 泄漏到主游戏保存退出  未纳入本次三阶段，保留完整键盘。 |
| P2 | 消息历史 Ctrl-P、金币/清单 `$`、符文 `}`、注释 `!`、笔记 `:`等 | 有的可通过子页面/其他 UI 间接达到，但不是当前15槽抽屉的明确同名命令 | 按附录逐项归类，补入信息组；不要把全部信息功能挤进主键盘  P2：消息历史、金币清单；P3：地图楼层注释；其他仍按原附录。 |
| P2 | 保存退出、宏、键位/系统管理 | 原生GameMenu有条目，但紧凑F1打开的是Android抽屉 | 给明确系统入口，区分保存、放弃和地形Exit，保留原确认  P2：系统菜单入口，保留原生确认。 |
