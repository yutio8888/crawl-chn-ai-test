# 角色机制显示全量校对计划

本计划对应 GitHub Issue #27。目标是从当前生产枚举、数据初始化器、显示消费者和
TextDB 冻结变异、状态、非神祇能力、技能、属性与怪物状态说明的完整清单，
为每个身份留下唯一证据卡和终态结论，并按共享机制依赖组顺序落地中文修订。

## 验收边界

- 变异身份以活动 `mutation-type.h` 和 `mutation-data.h` 交叉验证；每项核对
  名称、等级、获得/失去/未来获得文本、完整描述和实际效果。
- 玩家状态包括 `duration-data.h` 的全部活动时长身份和 `status.h` 中实际进入
  `fill_status_info()` 的附加状态；纯内部占位仍进入清单并标明生命周期。
- 怪物状态以英文 `monstatus.txt` 的稳定 TextDB 槽为身份源，并与中文键集合
  交叉验证。重复英文键必须先消歧，不能依赖最后定义覆盖。
- 能力以 `Ability_List` 为生产源；Issue #25 已拥有的神祇专属能力、被动和
  宗教伪能力按生产顺序机械排除，并在清单中保存完整排除身份。
- 技能以活动 `skill_type` 与 `skill_titles` 表交叉验证；已移除但仍为 TAG 34
  存档兼容保留的技能明确标为 compatibility。名称、说明、五档称号和特殊称号
  均需核对，既有称号裁定只在输入未变化时复用。
- 属性身份以 `stat_type` 和 `player-stats.cc` 的显示表交叉验证，范围只含
  Strength、Intelligence、Dexterity 的名称和增减状态词。
- 法术、物品、神祇身份不重新审阅；只检查共享术语和消费者引用。
- 不修改机制公式、概率、费用、持续时间、数值或平衡。

## 冻结方法

```bash
python3 .claude/scripts/audit_character_mechanics_inventory.py \
  --output /tmp/issue27-inventory.json
```

脚本复用现有 TAG 分支选择、SourceDB 物理键解析、C++ 平衡初始化器解析、
TextDB canonical key 和哈希机制。它记录基线提交、术语表与每个输入文件
SHA-256、生命周期、明确排除项、生产字段、英文/中文显示值和描述。

冻结基线为 `76c815b2ac79d11a8066597ad04d127a1636e153`，术语表
SHA-256 为 `91f0638a60e633d450ded2b6e7efdd3449e7ad2e0e27e710a52cd0dd2565d645`；
结构校准后的 inventory SHA-256 为
`9a3576f3b1f62aa8856654129aec02c6a699725b5ede3b1c032fd844479ed1cd`。

初始清单共 695 个唯一身份：

| 子域 | 身份数 |
|---|---:|
| 变异 | 213 |
| 时长状态 | 223 |
| 附加玩家状态 | 48 |
| 怪物状态说明槽 | 139 |
| 非神祇能力 | 35 |
| 技能 | 34 |
| 属性 | 3 |

生命周期为 current 686、compatibility 5、internal 4。另有 124 个由
Issue #25 拥有的神祇能力身份被明确排除。清单身份无重复。

## 初始结构发现

初始脚本非零退出，冻结了以下必须解决而不能掩盖的发现：

- `MUT_NO_JEWELLERY` 缺少英文和中文完整描述；
- 16 条活动变异获得、失去或未来获得文本缺少中文 SourceDB 映射；
- 英中 `mutations.txt` 都重复定义 `+LOS mutation`，两块语义不同；
- 英文 `monstatus.txt` 重复定义
  `damage-immune at range monstatus`，两块语义不同；
- 中文 mutation/status/monstatus/ability 描述库含 20 个英文生产库不存在的
  陈旧键；需逐项确认删除或恢复依据，不能把中文资产本身当作兼容身份权威。

## 依赖批次与所有权

全部 ZH 资产由同一 `zh-translator` 顺序写入；只读清单、必要生产边界和测试
随后由单一 `crawl-coder` 处理：

1. 校准重复键、缺失描述、陈旧键和已知权威输入，重新冻结无结构歧义的清单；
2. 核对属性、抗性、速度、隐形、沉默、恢复等跨变异/状态/能力共享机制组；
3. 按身体结构、抗性、恶魔变异、种族固有变异、牺牲/禁用系列审阅全部变异；
4. 按增益、减益、冷却、资源和内部时长组审阅玩家状态与怪物状态说明；
5. 审阅 35 个非神祇能力，复用已完成的物品、法术和种族事实；
6. 审阅现行技能、兼容技能、五档称号及特殊称号；
7. 同步 glossary/decisions，证明 inventory 与结果集合双向差集为空；
8. 运行匹配的 development profile，准备不可变候选，按机械路由完成审查，
   最后只运行一次现有 final gate。

逐项证据卡与集合相等证明将记录在
`docs/character-mechanics-review-results.md`。
