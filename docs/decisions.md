# DECISIONS.md — Translation Decision Registry

Single Source of Truth for all cross-issue Chinese translation naming decisions.
Before translating any entity name, check this file for existing rulings.

**Maintenance rule**: Decision execution status is updated by the commit that fixes
the affected file. Each commit body annotates `Updates: DECISION-XXX` when it
resolves an outstanding ❌.

**Status values**:
- `active` — Currently in effect
- `superseded` → points to replacement decision ID
- `reversed` — Explicitly abandoned (e.g., English source misunderstood)

**Relationship to Memory**: The Claude memory system stores the fact that this
file exists and should be consulted. This file stores the actual ruling content.

---

## Type-A: Entity Rulings (god/monster/spell/item names)

---

### D-A-001 — Sif Muna → 西芙·穆娜

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-06-26
- **Source**: [legacy issue 2 `TODO_GODNAME.md`][legacy-2-godname]
- **Choice**: 西芙·穆娜
- **Rejected**: 席夫·穆纳
- **Rationale**: `芙` (lotus) is common in goddess names, better matches the Norse goddess gender than `夫` (man/husband)
- **Affected files**:
  - `dat/database/zh/godname.txt` ✅
  - `dat/descript/zh/gods.txt` (×4) ✅
  - `dat/database/zh/godspeak.txt` (×2) ✅
  - `dat/database/zh/FAQ.txt` ✅
  - `dat/descript/zh/features.txt` ✅
- **Tracking issue**: [legacy issue 13][legacy-13]
- **Resolved**: 2026-06-27 (legacy issue 13 + follow-up)

---

### D-A-002 — Trog → 特洛格

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-06-26
- **Source**: [legacy issue 2 `TODO_GODNAME.md`][legacy-2-godname]
- **Choice**: 特洛格
- **Rejected**: 特洛戈
- **Rationale**: `格` matches the hard 'g' ending better; `戈` (dagger-axe) reads as an ancient weapon rather than a name syllable
- **Affected files**:
  - `dat/database/zh/godname.txt` ✅
  - `dat/descript/zh/egos.txt` ✅
  - `dat/descript/zh/hints.txt` ✅
  - `dat/descript/zh/spells.txt` ✅
  - `dat/descript/zh/status.txt` ✅
  - `dat/descript/zh/gods.txt` (×10) ✅
  - `dat/database/zh/godspeak.txt` (×2) ✅
  - `dat/database/zh/FAQ.txt` ✅
  - `dat/database/zh/help.txt` ✅
  - `dat/descript/zh/unrand.txt` (×2) ✅
  - `dat/descript/zh/backgrounds.txt` ✅
  - `dat/descript/zh/features.txt` ✅
  - `dat/descript/zh/tutorial.txt` (×2) ✅
  - `dat/descript/zh/ability.txt` ✅
- **Tracking issue**: [legacy issue 13][legacy-13]
- **Resolved**: 2026-06-27 (legacy issue 13 + follow-up)

---

### D-A-003 — Kikubaaqudgha → 奇库巴库哈

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: [legacy issue 13][legacy-13]
- **Choice**: 奇库巴库哈
- **Rejected**: 奇库巴库加
- **Rationale**: `哈` preserves the breathy 'gha' ending; `加` (add/plus) was a phonetic mismatch
- **Affected files**:
  - `dat/database/zh/godspeak.txt` ✅
  - `dat/descript/zh/gods.txt` ✅
  - `dat/descript/zh/ability.txt` ✅
  - `dat/descript/zh/features.txt` ✅
  - `dat/descript/zh/items.txt` ✅
  - `dat/descript/zh/monsters.txt` ✅
  - `dat/database/zh/graffiti.txt` ✅ (created with correct name in Phase 1)
- **Tracking issue**: [legacy issue 13][legacy-13]

---

### D-A-004 — Nemelex Xobeh middle dot → U+00B7

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: [legacy issue 12][legacy-12] Phase 0
- **Choice**: U+00B7 (·) as separator in 尼姆雷斯·索布
- **Rejected**: U+30FB (・) katakana middle dot
- **Rationale**: U+00B7 is the standard Chinese middle dot; U+30FB is CJK-specific and renders inconsistently across fonts
- **Affected files**:
  - `dat/database/zh/godname.txt` ✅
  - All other references use U+00B7 ✅
- **Tracking issue**: [legacy issue 12][legacy-12]

---

### D-A-005 — Vehumet → 维胡梅特

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: [legacy issue 12][legacy-12] Phase 0
- **Choice**: 维胡梅特
- **Rejected**: (none — this was the original translation, confirmed correct)
- **Rationale**: Phonetic transliteration is accurate and already in use across all files
- **Affected files**: All files use 维胡梅特 ✅
- **Tracking issue**: [legacy issue 12][legacy-12]

---

### D-A-006 — The Shining One → 光辉者

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: [legacy issue 12][legacy-12] Phase 0
- **Choice**: 光辉者
- **Rejected**: (none — confirmed correct)
- **Rationale**: Semantic translation; `光辉` (radiance/glory) + `者` (-er suffix) matches the god title pattern
- **Affected files**: All files use 光辉者 ✅
- **Tracking issue**: [legacy issue 12][legacy-12]

---

### D-A-007 — draconian → 龙人

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 龙人
- **Rejected**: 龙裔 (over-specifies bloodline)
- **Rationale**: 龙人 captures the half-dragon, half-humanoid nature. Color prefixes follow simple modifier pattern (黑龙人, 绿龙人). Standard convention for dragonborn-style races in Chinese fantasy.
- **Examples**: black draconian → 黑龙人, draconian annihilator → 龙人湮灭者, draconian stormcaller → 龙人风暴召唤者

---

### D-A-008 — deep elf → 精灵

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 精灵 (不加"深"前缀)
- **Rejected**: 深精灵 (Chinese fantasy convention: 精灵 already implies subterranean elves; DCSS has no surface elf to distinguish from)
- **Rationale**: DCSS has no generic "elf" monster — only "deep elf X" subtypes, so "精灵" unambiguously means "deep elf" in monster context. Player species "High Elf → 高等精灵" also uses 精灵, mirroring the English relationship. The "deep" spatial connotation is sacrificed for natural Chinese readability.
- **Examples**: deep elf annihilator → 精灵湮灭者, deep elf blademaster → 精灵剑圣, deep elf high priest → 精灵大祭司

---

### D-A-009 — orc → 兽人

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 兽人
- **Rejected**: 半兽人 (orcs are a distinct race, not half-human)
- **Rationale**: Standard convention from Warcraft/LoTR translations. All entries consistent.
- **Examples**: orc knight → 兽人骑士, orc warlord → 兽人军阀, orc apostle → 兽人使徒
- **Resolved issue**: `orc wizard → 兽人巫师` and
  `orc sorcerer → 兽人术士` are now distinct; see D-A-041.

---

### D-A-010 — merfolk → 鱼人

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 鱼人
- **Rejected**: 人鱼 (美人鱼 — too mermaid-associated, gendered)
- **Rationale**: 鱼人 captures the fish-human hybrid nature. Murloc-style naming fits DCSS's merfolk design.
- **Examples**: merfolk aquamancer → 鱼人水法师, merfolk impaler → 鱼人穿刺者, merfolk siren → 鱼人塞壬

---

### D-A-011 — spriggan → 小精灵

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 小精灵
- **Rejected**: 树精 (too plant-specific), 妖精 (too generic)
- **Rationale**: 小精灵 captures the small, fairy-like nature. Differentiated from 精灵 (deep elf) by the diminutive 小. In gameplay these two creature types never appear in similar contexts, so the partial term overlap is not a practical issue.
- **Examples**: spriggan air mage → 小精灵气法师, spriggan berserker → 小精灵狂战士, spriggan rider → 小精灵骑手

---

### D-A-012 — naga → 纳迦

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 纳迦
- **Rejected**: 蛇人 (loses mythological specificity), 娜迦 (娜 is feminine — naga are gender-neutral)
- **Rationale**: 纳迦 is the standard Chinese transliteration from Hindu/Buddhist mythology. Consistent across all entries including nagaraja → 纳迦王.
- **Examples**: naga mage → 纳迦法师, naga sharpshooter → 纳迦神射手, nagaraja → 纳迦王

---

### D-A-013 — demonspawn → 恶魔裔

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 恶魔裔
- **Rejected**: 魔裔 (ambiguous — could mean 魔鬼后裔), 恶魔后裔 (too long)
- **Rationale**: 裔 suffix precisely denotes bloodline/lineage, matching -spawn semantics.
- **Examples**: demonspawn blood saint → 恶魔裔血圣, demonspawn corrupter → 恶魔裔腐蚀者, demonspawn warmonger → 恶魔裔战争贩子

---

### D-A-014 — tengu → 天狗

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 天狗
- **Rejected**: 天狗人 (unnecessary), 鸟人 (derogatory)
- **Rationale**: 天狗 is the direct Chinese term for tengu — a well-known yokai in East Asian folklore. No qualifiers needed.
- **Examples**: tengu conjurer → 天狗咒法师, tengu reaver → 天狗掠夺者, tengu warrior → 天狗战士

---

### D-A-015 — dragon → 龙

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 龙 (element/type prefix: X龙)
- **Rejected**: (none — 龙 is the only viable option)
- **Rationale**: Universal Chinese term. Element/modifier precedes: 酸龙, 骨龙, 火龙, 金龙, 冰龙, 铁龙. Special: komodo dragon → 科摩多龙 (transliteration, not 巨蜥).
- **Examples**: acid dragon → 酸龙, golden dragon → 金龙, storm dragon → 风暴龙
- **See also**: D-A-016 (drake → 幼龙)

---

### D-A-016 — drake → 幼龙

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 幼龙
- **Rejected**: 小龙 (too informal/ambiguous — was previously used in "Summon Drakes → 召唤小龙", now unified to 幼龙), 龙兽 (reads as "dragon-beast"), 雏龙 (avian, hatchling-specific)
- **Rationale**: 幼龙 distinguishes smaller/younger drakes from adult dragons (龙). This is the key structural distinction: the Chinese dragon taxonomy uses 幼龙 vs 龙. **Pre-existing inconsistency fixed**: "Summon Drakes" changed from 召唤小龙 to 召唤幼龙.
- **Examples**: drake → 幼龙, rime drake → 霜幼龙, death drake → 死亡幼龙, wind drake → 风幼龙

---

### D-A-017 — imp → 小恶魔

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 小恶魔
- **Rejected**: 小鬼 (too folkloric/goblin), 魔童 (implies child-demon, not low-rank)
- **Rationale**: 小 captures both diminutive size and low-tier rank. 恶魔 establishes demonic nature. Color/modifier precedes the full compound: 蔚蓝小恶魔, 暗影小恶魔.
- **Examples**: crimson imp → 深红小恶魔, shadow imp → 暗影小恶魔, white imp → 白色小恶魔

---

### D-A-018 — golem → 魔像

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 魔像
- **Rejected**: 石魔像 (too specific), 构造体 (too sci-fi), 魔偶 (too puppet-like)
- **Rationale**: 魔像 is the established RPG convention (Diablo, Warcraft). Works for all materials.
- **Examples**: golem → 魔像, iron golem → 铁魔像, toenail golem → 趾甲魔像

---

### D-A-019 — lich → 巫妖

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 巫妖
- **Rejected**: 亡灵巫师 (loses the specific lich concept), 尸巫 (too narrow)
- **Rationale**: Standard D&D/Warcraft convention. 巫 (sorcery) + 妖 (unnatural being).
- **Examples**: lich → 巫妖, ancient lich → 远古巫妖, dread lich → 恐怖巫妖

---

### D-A-020 — horror → 恐怖

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 恐怖 (modifier + 恐怖 for subtypes)
- **Rejected**: 惊骇体 (unnecessary 体 suffix), 梦魇 (too dream/nightmare-specific)
- **Rationale**: 恐怖 is treated as a monster type like 元素. Modifier precedes: 潜伏恐怖, 无形恐怖. Though 恐怖 is adjective-primary in Chinese, DCSS horrors always appear with a prefix qualifier, so standalone usage is essentially theoretical. The compounds read naturally as "[qualifier] + horror-type".
- **Examples**: lurking horror → 潜伏恐怖, unseen horror → 无形恐怖, thrashing horror → 鞭笞恐怖

---

### D-A-021 — elemental → 元素

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 元素 (element type prefix: X元素)
- **Rejected**: 元素体 (unnecessary 体), 精灵 (collision with elf)
- **Rationale**: Standard term. Element type prefixed: 气元素, 地元素, 火元素.
- **Examples**: air elemental → 气元素, fire elemental → 火元素, quicksilver elemental → 水银元素

---

### D-A-022 — ironbound → 铁缚

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 铁缚 (prefix, followed by class name)
- **Rejected**: 铁链 (too literal chains), 缚铁 (verb-object, unusual as modifier), 铁枷 (punishment device)
- **Rationale**: 铁缚 captures "bound/encased in iron." The 缚 evokes the dwarven ironforge aesthetic with grimdark undertones.
- **Examples**: ironbound beastmaster → 铁缚驯兽师, ironbound thunderhulk → 铁缚雷躯, ironbound frostheart → 铁缚霜心

---

### D-A-023 — death (prefix) → 死亡

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 死亡
- **Rejected**: 死 (too short, parsing ambiguity), 亡 (too literary, ambiguous standalone)
- **Rationale**: 死亡 is the standard undead-monster prefix. Note: standalone "death" as a spell school is translated differently (亡语), but in monster name prefixes, always use 死亡.
- **Examples**: death cob → 死亡天鹅, death knight → 死亡骑士, deathcap → 死亡菌

---

### D-A-024 — hell (prefix) → 地狱

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 地狱
- **Rejected**: 炼狱 (purgatory — different concept), 魔 (too broad)
- **Rationale**: 地狱 maps directly to Hell as location/domain. Used as prefix for Hells-branch monsters. Differentiated from 恶魔 (demon race) and 亡灵 (undead).
- **Examples**: hell hound → 地狱犬, hell knight → 地狱骑士, hell lord → 地狱领主

---

### D-A-025 — iron (prefix) → 铁

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 铁 (single character prefix)
- **Rejected**: 钢铁 (too modern/industrial)
- **Rationale**: Standard elemental prefix across all monster types: 铁龙, 铁魔像, 铁元素, 铁巨人, 铁小恶魔, 铁巨魔. Single-character integrates cleanly with all roots.
- **Examples**: iron dragon → 铁龙, iron elemental → 铁元素, iron troll → 铁巨魔

---

### D-A-026 — sensed monster → 感知怪物

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 感知怪物 (difficulty + 感知怪物 for subtypes)
- **Rejected**: 侦测怪物 (too military/radar), 灵知怪物 (too esoteric)
- **Rationale**: These are Ashenzari-detection placeholders — monsters revealed through walls before the player can see them. 感知 captures extrasensory detection. Base form: 感知到的怪物 (with 的). Subtypes drop 的 for compound compatibility: 简单感知怪物, 友善感知怪物.
- **Examples**: sensed monster → 感知到的怪物, easy sensed monster → 简单感知怪物, nasty sensed monster → 危险感知怪物

---

### D-A-027 — ogre → 食人魔

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 食人魔
- **Rejected**: 巨人 (collision with giant), 巨怪 (too close to troll)
- **Rationale**: Standard Warcraft/D&D convention. Distinct from 巨魔 (troll) and 巨人 (giant). Modifier-before-root: 双头食人魔.
- **Examples**: ogre → 食人魔, ogre mage → 食人魔法师, two-headed ogre → 双头食人魔

---

### D-A-028 — troll → 巨魔

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Monster name terminology batch
- **Choice**: 巨魔
- **Rejected**: 穴居巨魔 (unnecessary regional specificity)
- **Rationale**: Standard Warcraft convention. Consistent subtypes: 铁巨魔, 月巨魔. "Deep troll" → 深渊巨魔 uses 深渊 rather than 深 because 深渊巨魔 is an established convention for abyssal trolls in Chinese fantasy.
- **Examples**: troll → 巨魔, iron troll → 铁巨魔, moon troll → 月巨魔, deep troll → 深渊巨魔

---

### D-A-029 — jelly → 果冻怪

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Terminology consistency audit
- **Choice**: 果冻怪 (azure jelly→天蓝果冻怪, star jelly→星之果冻, Royal Jelly→果冻王)
- **Rejected**: 史莱姆 (collision with slime creature→史莱姆 — jelly and slime are distinct DCSS monster types)
- **Rationale**: DCSS has four distinct amorphous monster families: jelly (果冻怪/果冻), slime (史莱姆/黏液), ooze (软泥), blob (凝胶团/酸液团). Translating jelly as 史莱姆 would lose the gameplay distinction between jelly-type and slime-type monsters. Royal Jelly→果冻王 keeps the boss in the 果冻 family while conveying its status as the jelly king.
- **Examples**: jelly → 果冻怪, azure jelly → 天蓝果冻怪, star jelly → 星之果冻

---

### D-A-030 — goblin / hobgoblin → 地精 / 大地精

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Terminology consistency audit
- **Choice**: 地精 (goblin), 大地精 (hobgoblin)
- **Rejected**: 大哥布林 (hobgoblin — previously in source.txt, inconsistent with goblin→地精)
- **Rationale**: 地精 is the standard D&D/Pathfinder convention. hobgoblin→大地精 follows the 大+base pattern for "greater" variants. Unified hobgoblin from 大哥布林 to 大地精.
- **Examples**: goblin → 地精, hobgoblin → 大地精

---

### D-A-031 — giant naming pattern (three sub-rules)

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-05
- **Source**: Terminology consistency audit
- **Choice**: Three distinct patterns:
  - Standalone "giant" → **巨型**
  - "giant <animal/creature>" → **巨X** (prefix 巨)
  - "<element/type> giant" → **X巨人** (suffix 巨人)
- **Rejected**: Uniform 巨人 for all (doesn't match natural Chinese: 巨蛙 is more natural than 巨人蛙)
- **Rationale**: Chinese distinguishes between "a giant version of X" (巨X: 巨蛙, 巨蜥, 巨蟑螂) and "a giant made of X" (X巨人: 火巨人, 霜巨人, 石巨人). This mirrors English word order distinction.
- **Examples**: 
  - Standalone: giant → 巨型
  - Animal prefix: giant frog → 巨蛙, giant lizard → 巨蜥, giant cockroach → 巨蟑螂
  - Elemental suffix: fire giant → 火巨人, frost giant → 霜巨人, stone giant → 石巨人, cactus giant → 仙人掌巨人

---

### D-A-032 — cane toad → 海蟾蜍

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-08
- **Source**: Translation quality review — "cane toad → 甘蔗蟾蜍" analysis
- **Choice**: 海蟾蜍
- **Rejected**: 甘蔗蟾蜍 (literal translation of "cane toad", secondary alias in Chinese — less recognizable to players)
- **Rationale**: 海蟾蜍 (marine toad) is the standard Chinese common name for *Rhinella marina / Bufo marinus*, the real-world species that the monster is based on. Chinese Wikipedia lists 甘蔗蟾蜍 as a secondary alias. The project convention is to use the most widely recognized Chinese common name for real-world-based creatures, matching the approach for 牛蛙 (bullfrog) and 巨蛙 (giant frog).
- **Examples**: cane toad → 海蟾蜍
- **Affected files**:
  - `dat/i18n/zh/source.txt` ✅
  - `dat/descript/zh/monsters.txt` ✅
- **Tracking issue**: (none — direct fix)
- **Resolved**: 2026-07-08

---

### D-A-033 — polter- root unification → 骚灵系

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-09
- **Source**: [legacy issue 49 monster name terminology review][legacy-49-terms]
- **Choice**: Unify `polter-` root under 骚灵
  - `poltergeist → 骚灵`
  - `polterguardian → 骚灵护卫` (no change needed)
- **Rejected**: 吵闹鬼 (too literal, "noisy ghost" misses restless-spirit connotation); 喧灵系 (viable alternative, but 骚灵 is more established in Chinese gaming)
- **Rationale**: 骚灵 (restless spirit) is the standard Chinese fantasy translation for "poltergeist" — matches the German root "poltern" (to rumble/make noise). 吵闹鬼 is too literal and loses the ethereal quality. Unifying under 骚灵 makes `polterguardian` predictable from `poltergeist`.
- **Affected files**:
  - `dat/i18n/zh/source.txt` ✅ (`poltergeist`)
- **Tracking issue**: [legacy issue 49 `monster-name-terminology.md`][legacy-49-terms]
- **Resolved**: 2026-07-09

---

### D-A-034 — cacodemon → 恶灵恶魔

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-09
- **Source**: [legacy issue 49 monster name terminology review][legacy-49-terms]
- **Choice**: 恶灵恶魔
- **Rejected**: 恶灵 (loses demon classification — 混入幽灵系); 恶灵魔 (unnecessary shortening)
- **Rationale**: Preserves both the "evil spirit" (恶灵) character of the original and the demon classification (恶魔). All other demon-type monsters use 恶魔 as their base classifier; `cacodemon` should not be an exception. 恶灵恶魔 keeps the unique flavor while maintaining terminological consistency.
- **Affected files**:
  - `dat/i18n/zh/source.txt` ✅
- **Tracking issue**: [legacy issue 49 `monster-name-terminology.md`][legacy-49-terms]
- **Resolved**: 2026-07-09

---

### D-A-035 — fiend → 邪魔 (统一)

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-09
- **Source**: [legacy issue 49 monster name terminology review][legacy-49-terms]
- **Choice**: All fiends → 邪魔
  - `Ice Fiend → 冰霜邪魔`
  - `Brimstone Fiend → 硫磺邪魔`
  - `shadow fiend → 暗影邪魔`
- **Rejected**: 恶魔 (overlaps with demon classification, losing the distinct fiend identity); mixed 邪魔/恶魔 (inconsistent)
- **Rationale**: 邪魔 conveys a more malevolent/sinister connotation than the relatively neutral 恶魔 — appropriate for fiend-type creatures. The project distinguishes between demon, fiend, and devil as three separate creature families; using distinct classifiers preserves this distinction in Chinese.
- **Affected files**:
  - `dat/i18n/zh/source.txt` ✅ (Ice Fiend, Brimstone Fiend, shadow fiend)
- **Tracking issue**: [legacy issue 49 `monster-name-terminology.md`][legacy-49-terms]
- **Resolved**: 2026-07-09

---

### D-A-036 — vampire → 吸血鬼 (基名统一)

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-09
- **Source**: [legacy issue 49 monster name terminology review][legacy-49-terms]
- **Choice**: Base monster name `vampire → 吸血鬼`, compounds follow 吸血鬼 pattern
  - `vampire (monster) → 吸血鬼`
  - `vampire bat → 吸血鬼蝙蝠`
  - Existing: vampire knight/mage/bloodprince → 吸血鬼骑士/法师/血王子 (no change)
- **Rejected**: 吸血 (base form reads as verb/adjective "bloodsucking" rather than noun "vampire"; inconsistent with all compound forms)
- **Rationale**: The base monster name `vampire` is a noun (the creature), not an adjective. Using 吸血 for the base form creates a noun/adjective inconsistency with all compound forms (吸血鬼骑士, 吸血鬼法师) where 吸血鬼 is the noun prefix. Vampire bat is also a creature name, so follows the same pattern.
- **Affected files**:
  - `dat/i18n/zh/source.txt` ✅
- **Tracking issue**: [legacy issue 49 `monster-name-terminology.md`][legacy-49-terms]
- **Resolved**: 2026-07-09

---

### D-A-037 — skeleton → 骷髅 (基名统一)

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-09
- **Source**: [legacy issue 49 monster name terminology review][legacy-49-terms] (P2)
- **Choice**: Unify all skeleton forms to 骷髅
  - `skeleton → 骷髅` (from 骸骨)
  - `large skeleton → 大型骷髅` (no change)
  - `small skeleton → 小型骷髅` (no change)
- **Rejected**: 骸骨 (formal/anatomical, less common in gaming); mixed 骸骨/骷髅 (inconsistent)
- **Rationale**: 骷髅 is the standard term for skeleton monsters in Chinese gaming culture. 骸骨 (skeletal remains/bones) is more anatomical and less idiomatic for a hostile creature. The compound forms already use 骷髅; unifying the base form eliminates the inconsistency.
- **Affected files**:
  - `dat/i18n/zh/source.txt` ✅
- **Tracking issue**: [legacy issue 49 `monster-name-terminology.md`][legacy-49-terms]
- **Resolved**: 2026-07-09

---

### D-A-038 — wraith → 幽魂 (统一，区分 ghost)

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-09
- **Source**: [legacy issue 49 monster name terminology review][legacy-49-terms] (P2)
- **Choice**: All wraith forms → 幽魂
  - `wraith → 幽魂` (from 幽灵)
  - `the Wraith → 幽魂` (no change)
  - `freezing wraith → 冰冻幽魂` (from 冰冻幽灵)
  - `shadow wraith → 暗影幽魂` (from 暗影幽灵)
- **Rejected**: 幽灵 (overlaps with ghost/spectre, losing wraith's distinct identity)
- **Rationale**: 幽魂 (wraith/restless spirit) in Chinese gaming commonly denotes ethereal, life-draining undead — distinct from 幽灵 (ghost, more general). Using 幽魂 for wraiths preserves the undead subtype distinction and matches the unique monster `the Wraith` which already used 幽魂.
- **Affected files**:
  - `dat/i18n/zh/source.txt` ✅
- **Tracking issue**: [legacy issue 49 `monster-name-terminology.md`][legacy-49-terms]
- **Resolved**: 2026-07-09

---

### D-B-012 — `X之球` as canonical orb naming pattern

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-07-09
- **Source**: [legacy issue 49 monster name terminology review][legacy-49-terms] (P2)
- **Choice**: Canonical monster orb naming pattern: `X之球`
  - `Orb of Destruction → 毁灭之球` (no change)
  - `great orb of eyes → 巨眼之球` (no change)
  - `orb of entropy → 熵之球` (no change)
  - `orb of fire → 火焰之球` (no change)
  - `orb of winter → 寒冬之球` (no change)
  - `orb of Dispater → 迪斯帕特之球` (from 迪斯帕特之法球)
  - `Orb of Electricity → 电光球` (kept — short punchy spell name, not a monster entity)
  - `Orb of Zot → 佐特宝珠` (kept — unique key game object, not a monster)
- **Rejected**: `X法球` (arcane orb, reads as a spell school rather than monster); mixed patterns (inconsistent genus-species feel)
- **Rationale**: `X之球` is the dominant pattern (6 of 8 cases). Standardizing eliminates the exception without affecting the two justified outliers (Orb of Zot as a unique game object, Orb of Electricity as a spell name).
- **Scope**: All monster orbs (entity names, not spell names)
- **Tracking issue**: [legacy issue 49 `monster-name-terminology.md`][legacy-49-terms]
- **Resolved**: 2026-07-09

---

## Type-B: Rule Rulings (style/grammar/formatting conventions)

---

### D-B-001 — Brand genitive unified to 之

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: [legacy issue 8][legacy-8] commit 3
- **Choice**: `Y之X` for all weapon/armour brand names (e.g., `flaming sword` → `火焰之剑`)
- **Rejected**: `Y的X` (colloquial form)
- **Rationale**: `之` is the literary/classical genitive marker appropriate for item names; `的` is colloquial and reads as lower register. Unified across all brands to avoid mixed styles.
- **Scope**: `item-name.cc` brand naming, all weapon/armour ego prefixes
- **Tracking issue**: [legacy issue 8][legacy-8]

---

### D-B-002 — comma_separated_line Chinese separators

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: [legacy issue 8][legacy-8] commit 2
- **Choice**: `、` (U+3001) for list separator, `和` for final conjunction
- **Rejected**: English `, ` and ` and `
- **Rationale**: Chinese enumeration uses `、` between items and `和` before the last item. Using English separators reads as a formatting bug.
- **Scope**: All `comma_separated_line()` calls where the output is player-visible Chinese text
- **Tracking issue**: [legacy issue 8][legacy-8]

---

### D-B-003 — article_a Chinese skip

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: [legacy issue 8][legacy-8] commit 1
- **Choice**: `article_a()` returns empty string in Chinese mode
- **Rejected**: Translating "a/an" as "一个" (over-specifies quantity)
- **Rationale**: Chinese has no articles. Adding `一个` where English uses `a/an` introduces unwanted quantification. Omission is the correct default.
- **Scope**: `english.cc:article_a()`
- **Tracking issue**: [legacy issue 8][legacy-8]

---

### D-B-004 — conj_verb Chinese disable

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: [legacy issue 8][legacy-8] anti-pattern #2
- **Choice**: Never call `conj_verb()` on Chinese strings
- **Rejected**: Calling `conj_verb()` and getting garbled output (e.g., `"抓取s"`)
- **Rationale**: `conj_verb()` applies English conjugation rules (adding -s/-es/-ing suffix). Chinese has no verb conjugation — person/number/tense are expressed through particles and word order, not suffixes.
- **Scope**: All .cc files — this is a NEVER rule in `.agents/policies/i18n-safety.md`
- **Tracking issue**: [legacy issue 8][legacy-8]

---

### D-B-005 — Chinese no plural marking

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: [legacy issue 8][legacy-8] commit 2
- **Choice**: Remove English plural `"s"` suffix logic in Chinese mode
- **Rejected**: Retaining English plural markers on Chinese text
- **Rationale**: Chinese nouns have no singular/plural distinction. Plurality is expressed through context, numbers, or measure words — never through noun suffixes.
- **Scope**: All string formatting that conditionally appends "s" based on count
- **Tracking issue**: [legacy issue 8][legacy-8]

---

### D-B-006 — Adverb position: BEFORE verb in Chinese

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: `docs/glossary.md`
- **Choice**: Adverbs always precede verbs in Chinese translations
- **Rejected**: English adverb placement (can be post-verbal)
- **Rationale**: Chinese word order is strictly modifier-before-modified. English allows adverbs after verbs; Chinese does not.
- **Scope**: All translation work
- **Tracking issue**: N/A (standing rule)

---

### D-B-007 — spell_title() changes do not affect DB keys

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: [legacy issue 16][legacy-16]
- **Choice**: Database keys use `spell_english_names` (English), not `spell_title()` (Chinese).
  `spell_title()` translation revisions do not require syncing `zh/spells.txt` keys.
- **Rejected**: Chinese spell_title() as DB key source — causes key breakage on translation change
  and key collisions when two spells share the same Chinese name (e.g., Pain/Anguish both 痛苦).
- **Rationale**: English keys eliminate the translation-revision→key-breakage fragility.
  zh/spells.txt now matches all 9 other zh/ database files in using English keys.
- **Scope**: `ability.cc` (ABIL_SIF_MUNA_REPEAT_EXEGESIS), `zh/spells.txt` keys
- **Note**: [Legacy issue 16][legacy-16] listed 3 "missing" spells (Gell's Gravity, Unleash Destruction, Stoneshock)
  whose EN keys do not exist in the 0.34.1 spells.txt database. These were likely misidentified
  or refer to spells removed/renamed in earlier versions. No action needed.
- **Tracking issue**: [legacy issue 16][legacy-16]

---

## Type-C: Batch Rulings (large-scale translation sets)

---

### D-C-001 — Skill titles (216 items)

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: [legacy issue 7][legacy-7]
- **Choice**: Full Chinese translation of all 216 skill rank titles via `zh_skill_titles` map
- **Rejected**: Partial translation or machine-only translation
- **Rationale**: Skill titles are high-visibility UI text. Each title was manually translated with attention to rank hierarchy and thematic consistency within each skill.
- **Scope**: `skills.cc:zh_skill_titles` map + `skill_title_by_rank()` lookup
- **Tracking issue**: [legacy issue 7][legacy-7]

---

### D-C-002 — Spell name fixes (6 items)

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-06-26
- **Source**: i18n-improve (`_spell_review/impl_plan.md`)
- **Choice**: 6 spell name corrections:
  - MERCURY_ARROW: 水银箭 → 汞矢 (P0 — 与 QUICKSILVER_BOLT 重名)
  - BLINK_RANGE: 范围闪烁 → 退避闪烁 (P1 — "范围"误解核心效果)
  - ENGLACIATION: 代谢冻结 → 深度冻结 (P1 — "代谢"与冰冻效果冲突)
  - HIBERNATION: 施法冬眠 → 冬眠 (P1 — 唯一带"施法"前缀，破坏一致性)
  - BOULDER: 布罗姆之滚石 → 布罗姆之碾压巨石 (P1 — 丢失 Barrelling 含义)
  - SUMMON_DRAGON: 召唤龙 → 召唤巨龙 (P2 — 与"龙之呼唤"区分不足)
- **Rejected**: Original translations (inaccurate, inconsistent, or unidiomatic)
- **Rationale**: Each correction addressed a specific quality issue: inaccurate element description, missing nuance, unidiomatic compound formation, or naming inconsistency within the spell list.
- **Scope**: `spl-data.h` spell name definitions
- **Tracking issue**: i18n-improve

---

### D-C-003 — Item base names (200 items, including 10 dragon scales)

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: [legacy issue 10][legacy-10]
- **Choice**: Chinese `item_base_name()` mapping for all item types
- **Rejected**: English-only item names in Chinese mode
- **Rationale**: Item names are Type I static display data — must be translated at the data layer for consistency.
- **Scope**: `item-name.cc:item_base_name()`
- **Tracking issue**: [legacy issue 10][legacy-10]
- **Resolved**: 2026-06-27

---

### D-C-004 — Portal .des file messages (~40 items)

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: [legacy issue 9][legacy-9]
- **Choice**: Chinese initmsg/finalmsg for all 13 portal vault .des files
- **Rejected**: English-only portal messages
- **Rationale**: Portal entry/exit messages are player-visible atmospheric text. Uses `crawl.language()` Lua function for runtime language selection.
- **Scope**: `dat/des/variable/*.des` portal files
- **Tracking issue**: [legacy issue 9][legacy-9]
- **Resolved**: 2026-06-27

---

### D-C-006 — lightning rod → 雷击杖

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-08
- **Source**: Translation quality review — "避雷针" analysis
- **Choice**: 雷击杖
- **Rejected**: 避雷针 (contradicts item's offensive function — 避 = avoid/protect, but the item shoots lightning at enemies), 引雷针 (better semantics but 针 still misrepresents rod)
- **Rationale**: 雷击 (lightning strike) accurately describes the item's offensive function. 杖 (rod/staff) matches the physical form better than 针 (needle). Consistent with how other rod-like items are named in Chinese.
- **Affected files**:
  - `dat/i18n/zh/source.txt` ✅
- **Tracking issue**: (none — direct fix)
- **Resolved**: 2026-07-08

---

### D-C-007 — Spell name revision: Bolt 系列去多余"之"

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-12
- **Source**: spell naming rules batch review (Bolt series)
- **Choice**: 6 Bolt系列法术去掉非必要的"之"——属性/材质修饰语前置，符合规则 §6.3:
  - Bolt of Devastation: 毁灭之箭 → 毁灭箭
  - Bolt of Draining: 吸取之箭 → 吸取箭
  - Bolt of Flesh: 血肉之箭 → 血肉箭
  - Bolt of Light: 光之箭 → 光箭
  - Doom Bolt: 厄运之箭 → 厄运箭
  - Sojourning Bolt: 旅居之箭 → 旅居箭
- **Rejected**: 保留原译（违反§6.3 "of不机械译成之"原则）
- **Rationale**: 系列基准词根为"箭"（火焰箭/寒冰箭/岩浆箭），其余成员应保持同构。"毁灭""吸取""血肉"等为属性修饰而非专名领属，不应使用"之"
- **Scope**: `dat/i18n/zh/source.txt` Bolt系列条目，`docs/glossary.md` Section 十三
- **Affected decisions**: D-C-002 (非重叠，不冲突)

---

### D-C-008 — Spell name revision: Cloud 重名拆分

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-12
- **Source**: spell naming rules batch review (Cloud系列)
- **Choice**: 2对重名Cloud法术拆分:
  - Noxious Cloud: 毒云 → 毒瘴云（消除与Poisonous Cloud重名，与Noxious Breath毒瘴吐息词根一致）
  - Mephitic Cloud: 瘴气云 → 迷瘴云（消除与Miasma Cloud重名；“迷”指混乱效果）
- **Rejected**: 保留两对重名（违反§5.4 不同英文法术不得同中文名）
- **Rationale**: Poisonous Cloud保留“毒云”，当前为产生毒伤与中毒云的L5怪物法术；Noxious Cloud改为“毒瘴云”，当前为沼泽龙产生混乱云的呼气法术。Miasma Cloud保留“瘴气云”仅作为已移除兼容标题；Mephitic Cloud改为“迷瘴云”突出其混乱效果
- **Scope**: `dat/i18n/zh/source.txt` Cloud条目
- **Current-state correction**: 2026-07-25 经 D-C-015 复核，纠正旧记录中的
  `nausea` 与“L6玩家法术”两项过时事实；原重名拆分裁定继续有效。

---

### D-C-009 — Spell name revision: Call 系列统一"呼唤"

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-12
- **Source**: spell naming rules batch review (Call系列)
- **Choice**: 5个Call法术统一为"呼唤"词根（与既有的Dragon's Call→"龙之呼唤"对齐）:
  - Call Imp: 召唤小恶魔 → 呼唤小恶魔
  - Call Canine Familiar: 召唤犬类使魔 → 呼唤犬类使魔
  - Call Tide: 召唤潮汐 → 呼唤潮汐
  - Call Lost Souls: 召唤迷失灵魂 → 呼唤迷失灵魂
  - Call of Chaos: 混沌召唤 → 混沌呼唤
- **Rejected**: 保留"召唤"译法（混淆Call与Summon的英文原意差异）
- **Rationale**: Call不同于Summon——Call是"呼唤/召唤某一实体前来"，Summon是"召唤创造实体"。英文系列内部及Dragon's Call已用"呼唤"；统一后可清晰区分两个词根
- **Scope**: `dat/i18n/zh/source.txt` Call系列条目
- **Note**: Call Down Damnation 不在本系列内——该法术是Down + Damnation，"降下天谴"不涉及呼唤

---

### D-C-010 — Spell name revision: 杂项

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-12
- **Source**: spell naming rules batch review
- **Choice**: 11项杂项修正:
  - Pyre Arrow: 火葬之箭 → 烈火箭（"火葬"文化联想误导）
  - Searing Breath: 灼热之息 → 灼热吐息（Breath系列词根统一）
  - Call Down Damnation: 降下诅咒 → 降下天谴（L9法术强度匹配）
  - Brothers in Arms: 战友召唤 → 战友（原译多余"召唤"）
  - Vanquished Vanguard: 被征服的先锋 → 败军先锋（生硬直译）
  - Summon Minor Demon: 召唤小恶魔 → 召唤次级恶魔（消除与Call Imp重名）
  - Eringya's Noxious Bog: 埃林吉亚之有毒沼泽 → 埃林吉亚之毒沼（去冗余）
  - Eringya's Surprising Crocodile: 埃林吉亚之惊喜鳄鱼 → 埃林吉亚之意外鳄鱼（"惊喜"含正面色彩）
  - Regenerate Other: 治愈他人 → 再生他人（消除与Heal Other重名）
  - Discord: 混乱 → 纷乱（消除与Confuse重名）
  - Anguish: 痛苦 → 哀痛（消除与Pain重名）
- **Scope**: `dat/i18n/zh/source.txt`, `docs/glossary.md`

---

### D-C-011 — Spell name revision: 新增缺失法术

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-12
- **Source**: source.txt missing entries identified during batch review
- **Choice**: 新增12条缺失的source.txt条目:
  - Fireball: 火球, Haste: 加速, Sting: 毒刺, Silence: 沉默,
  - Sign of Ruin: 毁灭征兆, Foxfire: 狐火, Agony: 剧痛,
  - Golden Breath: 金龙吐息, Condensation Shield: 凝结之盾,
  - See Invisible: 侦测隐形, Throw: 投掷, Vortex: 漩涡
- **Scope**: `dat/i18n/zh/source.txt`

---

### D-C-012 — Spell name revision: 元素召唤统一

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-12
- **Source**: spell naming rules batch review — 元素系列
- **Choice**: 3个元素召唤法术名称统一为短元素名，与实体名称匹配:
  - Summon Air Elementals: 召唤空气元素 → 召唤气元素
  - Summon Fire Elementals: 召唤火焰元素 → 召唤火元素
  - Summon Earth Elementals: 召唤大地元素 → 召唤地元素
- **Rejected**: 保留长格式（与其他元素"水元素/铁元素"格式不一致）
- **Rationale**: 实体名（air elemental→气元素, fire elemental→火元素, earth elemental→地元素）使用单字前缀+元素，法术名应复用。Water/Iron已为"水元素/铁元素"，Air/Fire/Earth不应使用"空气/火焰/大地"长格式
- **Scope**: `dat/i18n/zh/source.txt`, `docs/glossary.md`
- **Historical note (superseded by D-A-043)**: 当时因相关状态文本使用“催眠”而
  暂缓单改法术名；其中“L2”及“全部 12 处”的记录也已不符合当前数据。

---

### D-C-013 — Spell name revision: Blink 系列使役结构与生命周期

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: Blink 系列逐项复审；对照当前 `spl-data.h`、英文法术描述及位移实现
- **Choice**:
  - 保留系列核心词根 `Blink → 闪烁`，并将 8 项现行法术与 1 项已移除兼容记录分开登记。
  - `Blink Allies Away`：闪烁盟友远离 → **使盟友闪烁远离**。
  - `Blink Allies Encircling`：闪烁盟友包围 → **使盟友闪烁合围**。
  - `Blink Other`：闪烁他人 → **使他人闪烁**。
  - `Blink Other Close`：闪烁他人接近 → **使他人闪烁靠近**。
  - 保留 `Blink → 闪烁`、`Blink Away → 远离闪烁`、`Blink Close → 接近闪烁`、`Blink Range → 退避闪烁`、`Controlled Blink → 受控闪烁`。
- **Mechanism basis**: 四项修订法术均由施法者使盟友或目标发生闪烁位移，旧译把不及物的“闪烁”机械置于受事者之前，弱化或混淆了使役关系。`Blink Allies Away` 使靠近敌人的盟友闪烁至更远位置；`Blink Allies Encircling` 将 3–6 名盟友移动至目标敌人的相邻格形成合围；`Blink Other` 使目标敌人进行无法以意志抵抗的随机短距闪烁；`Blink Other Close` 使目标敌人向施法者闪烁靠近一小段距离。
- **Rejected**:
  - “盟友远离闪烁”“盟友环绕闪烁”“他人闪烁”：弱化施法者对受事者的使役关系。
  - “闪送盟友远离／合围”“闪送他人”：丢失已确认的 Blink 系列“闪烁”词根。
  - “盟友退避闪烁”：与 `Blink Range → 退避闪烁` 的特殊机制混淆。
  - “使盟友闪烁包围”：结果补语生硬；“使他人接近闪烁”可能被理解为在近处闪烁；“使他人闪烁近身”误示目标必定抵达相邻格；“使敌人闪烁”不必要地把较中性的 `Other` 改写为机制限定。
- **Lifecycle**: `Controlled Blink` 仅存在于 `TAG_MAJOR_VERSION == 34` 的 `AXED_SPELL` 与存档兼容路径，不是现行可施放法术，也没有现行英中描述。历史标题“受控闪烁”保留，但不计入 8 项现行成员；当前仍存在的同名实现辅助函数用于物品路径，不改变该法术的已移除状态。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/decisions.md`

---

### D-C-014 — Spell name revision: Bolt 系列词根、生命周期与描述校准

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: Bolt 系列逐项复审；对照当前英文法术描述、现行法术登记及命中效果实现
- **Choice**:
  - 确认常规现行法术的系列词根 `Bolt → 箭`，并将 16 项现行法术与 3 项已移除／TAG 34 兼容记录分开登记。
  - `Bolt of Draining`：吸取箭 → **衰竭箭**。这里的 Drain 是负能量造成的“衰竭”状态，不会把生命或魔力转给施法者。
  - `Sojourning Bolt`：旅居箭 → **羁旅箭**。新译保留旅途、漂泊之意，同时避免“旅居”偏向定居生活的静态语感。
  - 保留其余 14 项现行标题：`Blinkbolt → 闪烁箭`、`Bolt of Cold → 寒冰箭`、`Bolt of Devastation → 毁灭箭`、`Bolt of Fire → 火焰箭`、`Bolt of Flesh → 血肉箭`、`Bolt of Light → 光箭`、`Bolt of Magma → 岩浆箭`、`Corrosive Bolt → 腐蚀箭`、`Doom Bolt → 厄运箭`、`Electrical Bolt → 电击箭`、`Lightning Bolt → 闪电箭`、`Quicksilver Bolt → 水银箭`、`Thunderbolt → 雷击`、`Venom Bolt → 毒液箭`。
- **Form exceptions**:
  - `Blinkbolt → 闪烁箭` 保留复合词的既有标题，不机械拆写。
  - `Thunderbolt → 雷击` 是固定词形例外，不改成“雷箭”。
- **Lifecycle boundary**: `Bolt of Inaccuracy → 偏差箭矢`、`Explosive Bolt → 爆裂弩矢`、`Random Bolt → 随机箭矢` 仅作为已移除／TAG 34 兼容标题暂沿用，不计入 16 项现行成员或现行词根统计。现有证据不足以确认其历史机制，本裁定不声称已完成机制审阅。
- **Rejected**:
  - 将现行 Bolt 一律译为“束”：会把系列标题误收窄为 beam 形态，并破坏既有“箭”词根。
  - 将现行 Bolt 一律译为“弩矢”：英文没有 crossbow 语义，且会凭空加入武器来源。
  - 保留“吸取箭”：暗示生命或魔力被转移给施法者，与实际衰竭效果不符。
  - 保留“旅居箭”：静态定居语感弱化了法术的旅途意象。
- **Description corrections**:
  - `Bolt of Draining`：恢复仅影响 `living creature` 的限定，并准确说明负能量伤害会造成衰竭。
  - `Corrosive Bolt`：恢复 `highly-corrosive` 的强腐蚀修辞。
  - `Doom Bolt`：删除未实现的“穿透性负能量束”和“毁灭”效果，改为由受诅恶意凝聚而成的箭并施加厄运。
  - `Quicksilver Bolt`：删除错误的“部分无视护甲”，改为驱散能量可能移除目标的部分魔法效果。
  - `Sojourning Bolt`：删除虚构的多维弹跳；完整保留穿透且不稳定的双射能量、命中后延迟传送，以及以玩家为目标时将受害者移向施法者盟友并尽可能捎上施法者的特殊逻辑。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/decisions.md`
- **Affected decisions**: 补充并更新 D-C-007；其“去多余之”的结构裁定仍有效。

---

### D-C-015 — Spell name review: Cloud 后缀系列、生命周期与描述校准

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: Cloud 词形系列逐项复审；对照当前 `spl-data.h`、英中描述、云类型及命中效果实现
- **Choice**:
  - 确认现行 `X Cloud` 后缀系列的中心词根 `Cloud → 云`。
  - 保留 8 项现行标题：`Flaming Cloud → 燃烧云`、`Freezing Cloud → 冰冻云`、`Ink Cloud → 墨云`、`Mephitic Cloud → 迷瘴云`、`Noxious Cloud → 毒瘴云`、`Petrifying Cloud → 石化云`、`Poisonous Cloud → 毒云`、`Spectral Cloud → 幽灵云`。
  - `Mephitic Cloud` 与 `Noxious Cloud` 都生成以混乱为主效果的 `CLOUD_MEPHITIC`，但前者是玩家使用的瓶式小范围爆炸，后者是沼泽龙的大型呼气云；`Poisonous Cloud` 则生成造成毒伤与中毒的 `CLOUD_POISON`。三者名称须保持区分。
- **Lifecycle boundary**:
  - `Miasma cloud → 瘴气云`、`Poison cloud → 毒气云`、`Fire cloud → 火云`、`Steam cloud → 蒸汽云` 仅作为已移除／TAG 34 兼容标题暂沿用。当前没有 metadata、描述或实现足以完成其历史机制复核。
  - `Cloud Cone → 云雾锥` 同样仅为已移除兼容标题且机制证据不足。英文中心词是 `Cone`，因此它不属于 `X Cloud` 后缀系列，但仍保留在全法术词形索引中。
  - 现行 `Flaming Cloud` 与已移除 `Fire cloud` 是不同生命周期的独立身份，不得因都关联火焰云类型而合并。
- **Rejected**:
  - 将 `Mephitic Cloud`、`Noxious Cloud`、`Poisonous Cloud` 合并为同一中文名：会掩盖混乱云与毒伤云，以及不同投送方式的玩法差异。
  - 以现行 cloud type、吐息或辅助实现反推五项已移除法术的历史机制。
  - 把 `Cloud Cone` 计入 `X Cloud` 后缀词根统计：其中心词是 `Cone`。
  - 将“冰冻云”改成“冻结云”、将“幽灵云”改成说明式机制标题：均无足够辨识收益。
- **Description corrections**:
  - `Mephitic Cloud`：恢复脆弱瓶爆炸的投送方式，并将英文 `creatures` 完整译为“生物”。
  - `Petrifying Cloud`：恢复“受钙化尘雾影响超过片刻才石化”的触发条件，不再误写为石化持续时间。
  - `Flaming Cloud` 与 `Poisonous Cloud`：恢复英文 `large`／`great` 的规模信息。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/decisions.md`
- **Affected decisions**: 更新 D-C-008 的当前事实；其消除重名的标题裁定继续有效。

---

### D-B-008 — Descript ZH 必须与 EN 保持机制一致

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: [legacy issue 17][legacy-17]
- **Choice**: ZH descriptions (descript/zh/) must not add, remove, or alter game
  mechanics described in the corresponding EN entry.
- **Rejected**: Fabricating mechanics in translation (e.g., adding healing effects,
  knockback, god associations, or stealth penalties not present in EN)
- **Rationale**: Translation must preserve the player's mechanical understanding
  of the game. Fabricated mechanics mislead players and violate the
  translator's responsibility to faithfully represent the source material.
- **Scope**: All `dat/descript/zh/*.txt` files
- **Verification**: `check_consistency.sh --descript` catches key mismatches;
  content parity requires periodic manual EN/ZH sampling.
- **Tracking issue**: [legacy issue 17][legacy-17]

---

### D-B-009 — @keyword@ 引用完整性

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: [legacy issue 18][legacy-18]
- **Choice**: Every @keyword@ referenced in a ZH database file must have a
  corresponding definition in either the same ZH file or the EN fallback.
  Prefix conventions (e.g., `@_graffiti_xxx_@`) must match exactly.
- **Rejected**: Broken @keyword@ references that silently fail at runtime
- **Rationale**: @keyword@ references are resolved at display time. A missing
  definition produces blank output or raw `@_key_@` text — both are
  user-visible bugs. Prefix mismatches (e.g., `@_hailed_god_@` missing
  the `graffiti_` prefix) are a known failure mode ([legacy issue 19][legacy-19]).
- **Scope**: All `dat/database/zh/*.txt` files
- **Verification**: `check_consistency.sh --database --keywords`
- **Tracking issue**: [legacy issue 18][legacy-18]

---

### D-B-010 — EN 内容变更时需要 ZH 重新审查

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: [legacy issue 17][legacy-17] + [legacy issue 18][legacy-18]
- **Choice**: When EN database/descript entries are modified (content change, not
  just formatting), the corresponding ZH entries must be flagged for review.
- **Rejected**: ZH entries silently drifting out of sync with updated EN content
- **Rationale**: Entry count mismatch >10% is a strong signal that ZH has not
  been updated to match EN content changes. Version drift is most common in
  `gods.txt`, `mutations.txt`, `ability.txt` — files tied to game mechanics
  that evolve across versions.
- **Scope**: All `dat/descript/zh/*.txt` and `dat/database/zh/*.txt`
- **Verification**: `check_consistency.sh --stale`
- **Tracking issue**: [legacy issue 17][legacy-17] + [legacy issue 18][legacy-18]

### D-B-011 — 工具函数语言守卫

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-28
- **Source**: [legacy issue 22][legacy-22]
- **Choice**: 返回用户可见字符串的工具函数必须有语言守卫。
  典型模式：`return zh ? "中文" : "English";`
  或在调用点包裹 `Options.language` 检查。
- **Rejected**: 在工具函数中直接返回中文（无守卫），导致 EN 模式下显示中文。
- **Rationale**: `_beam_type_name` 等 Layer 3 函数的返回值直接进入 `mprf`/
  消息系统。如果函数内无语言守卫检查，EN 模式下会显示中文。
  这与 Type II 数据（动态格式串）的语言守卫原则一致。
  `scan_untranslated.sh --layer3` 可自动检测 `zh ? "X" : "X"` stub 模式。
- **Scope**: 所有返回用户可见字符串的 `_zh_*` 工具函数、Layer 3 显示函数、
  `zh_names` map 查找函数、`dungeon_feature_name_zh` 等。
- **Tracking issue**: [legacy issue 22][legacy-22]

[legacy-2-godname]: https://github.com/yutio8888/crawl-chn-issues-archive/blob/d31fccd3eb2c2cd612739646769ee1b45b6dfb01/2/TODO_GODNAME.md
[legacy-7]: https://github.com/yutio8888/crawl-chn-issues-archive/tree/d31fccd3eb2c2cd612739646769ee1b45b6dfb01/7
[legacy-8]: https://github.com/yutio8888/crawl-chn-issues-archive/tree/d31fccd3eb2c2cd612739646769ee1b45b6dfb01/8
[legacy-9]: https://github.com/yutio8888/crawl-chn-issues-archive/tree/d31fccd3eb2c2cd612739646769ee1b45b6dfb01/9
[legacy-10]: https://github.com/yutio8888/crawl-chn-issues-archive/tree/d31fccd3eb2c2cd612739646769ee1b45b6dfb01/10
[legacy-12]: https://github.com/yutio8888/crawl-chn-issues-archive/tree/d31fccd3eb2c2cd612739646769ee1b45b6dfb01/12
[legacy-13]: https://github.com/yutio8888/crawl-chn-issues-archive/tree/d31fccd3eb2c2cd612739646769ee1b45b6dfb01/13
[legacy-16]: https://github.com/yutio8888/crawl-chn-issues-archive/tree/d31fccd3eb2c2cd612739646769ee1b45b6dfb01/16
[legacy-17]: https://github.com/yutio8888/crawl-chn-issues-archive/tree/d31fccd3eb2c2cd612739646769ee1b45b6dfb01/17
[legacy-18]: https://github.com/yutio8888/crawl-chn-issues-archive/tree/d31fccd3eb2c2cd612739646769ee1b45b6dfb01/18
[legacy-19]: https://github.com/yutio8888/crawl-chn-issues-archive/tree/d31fccd3eb2c2cd612739646769ee1b45b6dfb01/19
[legacy-22]: https://github.com/yutio8888/crawl-chn-issues-archive/tree/d31fccd3eb2c2cd612739646769ee1b45b6dfb01/22
[legacy-49-terms]: https://github.com/yutio8888/crawl-chn-issues-archive/blob/d31fccd3eb2c2cd612739646769ee1b45b6dfb01/49/monster-name-terminology.md

---

## Type-D: Context-Sensitive Resolution

These terms have multiple valid Chinese translations depending on context.
The glossary and context_resolve.sh use these tables for disambiguation.

---

### D-D-001 — cast 翻译消歧

- **Type**: D — Context-sensitive resolution
- **Status**: active
- **Date**: 2026-06-30
- **EN term**: cast

| Context | ZH |
|---------|----|
| Generic spellcasting | 施法 |
| Ritualistic/religious | 吟诵 |
| Sacred/divine | 咏唱 |

---

### D-D-002 — blood 翻译消歧

- **Type**: D — Context-sensitive resolution
- **Status**: active
- **Date**: 2026-06-30
- **EN term**: blood

| Context | ZH |
|---------|----|
| Normal usage | 血 |
| Emphatic/literary (god descriptions) | 鲜血 |

---

### D-D-003 — penance 翻译消歧

- **Type**: D — Context-sensitive resolution
- **Status**: active
- **Date**: 2026-06-30
- **EN term**: penance

| Context | ZH |
|---------|----|
| Law gods (Zin, The Shining One) | 惩戒 |
| Self-sacrifice gods (Elyvilon) | 苦修 |

---

### D-D-004 — god 翻译消歧

- **Type**: D — Context-sensitive resolution
- **Status**: active
- **Date**: 2026-06-30
- **EN term**: god

| Context | ZH |
|---------|----|
| Formal, narrative | 神祇 |
| Casual, spoken dialogue | 神 |

---

### D-A-039 — Felid → 猫 (玩家种族名)

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-09
- **Source**: 种族名称翻译分析 — Felid 是四足猫，非人形
- **Choice**: 猫（去掉"人"后缀）
- **Rejected**: 猫人（错误暗示人形），猫妖（不必要的修饰）
- **Rationale**: Felid 在游戏中是被描述为智力猫科动物的四足生物，不是猫形类人种族。"猫"简洁准确，符合游戏内设定。Cat → 猫（genus），Feline → 猫科（adj）。
- **Affected files**:
  - `species.cc` ✅ (zh_names map)
  - `dat/i18n/zh/source.txt` ✅ (Felid, Cat, Feline 条目)
- **Tracking issue**: (none — direct fix)
- **Resolved**: 2026-07-09

---

### D-A-040 — Octopode → 章鱼 (玩家种族名)

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-09
- **Source**: 种族名称翻译分析 — Octopode 是触手软体生物，非人形
- **Choice**: 章鱼（去掉"人"后缀）
- **Rejected**: 章鱼人（错误暗示人形），章鱼怪（不必要的贬义）
- **Rationale**: Octopode 在游戏中是不可穿戴靴子/手套/斗篷的触手状软体生物，不是章鱼形类人种族。"章鱼"简洁准确。Octopus → 章鱼（genus），Octopoid → 章鱼形（adj）。
- **Affected files**:
  - `species.cc` ✅ (zh_names map)
  - `dat/i18n/zh/source.txt` ✅ (Octopode, Octopus, Octopoid 条目)
- **Tracking issue**: (none — direct fix)
- **Resolved**: 2026-07-09

---

### D-B-013 — 物品命名结构模式（所有类别）

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-07-12
- **Source**: Item naming design review (docs/design-item-naming.md)
- **Choice**: 全物品类别中文命名结构规则如下：

| 类别 | EN 模式 | ZH 模式 | 示例 |
|------|---------|---------|------|
| 武器品牌(adj类) | `brand_adj + body` | `adj + body` | 烈焰之剑、疾速匕首 |
| 武器品牌(非adj) | `body of brand` | `brand之body` | 防护之剑、电击之杖 |
| 护甲附魔 | `body of ego` | `ego之body` | 火焰抗性之袍、潜行之斗篷 |
| 弹药品牌(postfix) | `body of brand` | `brand之body` | 剧毒之飞镖 |
| 药水 | `potion of effect` | `effect药水` | 治疗药水、加速药水 |
| 魔杖 | `wand of effect` | `effect魔杖` | 火焰魔杖、麻痹魔杖 |
| 法杖 | `staff of type` | `type法杖` | 火焰法杖、塑能法杖 |
| 卷轴 | `scroll of effect` | `effect卷轴` | 鉴定卷轴、传送卷轴 |
| 书籍 | `book of type` | `type之书` | 火焰之书、召唤之书 |
| 手册 | `manual of skill` | `skill手册` | 长剑手册、火焰魔法手册 |
| 珠宝 | `ring/amulet of effect` | `effect戒指/项链` | 防护戒指、再生项链 |
| 神器 | `basename of name` | `name之basename` | 赛瑞博之剑、特洛格之怒 |
| 随机神器 | `basename of X` | `Xbasename` | 闪电之剑、毁灭之棍 |

- **Rejected**: 珠宝目前暂不加"之"（原因：部分效果名已含"之"→"守护之灵之戒指"需额外处理；待后续统一）
- **Rationale**: 统一的结构模式便于玩家理解和记忆，也为新条目翻译提供明确指引
- **Scope**: 所有 `item-name.cc` 和 `artefact.cc` 中的 ZH 命名逻辑
- **Tracking issue**: docs/design-item-naming.md

---

### D-B-014 — 物品基础名翻译风格

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-07-12
- **Source**: Item naming design review
- **Choice**: 物品基础名遵循以下翻译风格：
  1. **材料/类型 + 甲/盾/匕/剑/斧/锤/杖**：皮甲、板甲、小圆盾、长剑、战斧、钉头锤、法杖
  2. **种族/神性 + 之 + 武器类型**：恶魔之刃、善灵之刃、神圣之鞭
  3. **龙鳞甲**：X龙鳞甲（火龙鳞甲、冰龙鳞甲、金龙鳞甲）
  4. **Pair of** / **复数**：中文跳过，直接用单数基础名
  5. **品牌/附魔名**：统一二字或四字格式（烈焰、寒霜、神圣惩戒、火焰抗性）
- **Rejected**: 
  - 英文直译如"pair of boots→靴子的一对"（不符合中文习惯）
  - 混合使用"的"和"之"（统一用"之"）
- **Rationale**: 中文命名应简洁自然，符合游戏内物品显示区域的长度限制。二字品牌名利于在有限空间显示。龙鳞甲统一命名帮助玩家快速识别护甲类型
- **Scope**: `item-name.cc` 中所有 `T_()` 基础名字典条目

---

### D-B-015 — Demon/Sacred/Eudemon 前缀统一

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-07-12
- **Source**: Item naming design review
- **Choice**: 
  - `demon` 在物品名中 → `恶魔`（demon blade→恶魔之刃, demon whip→恶魔之鞭, demon trident→恶魔三叉戟）
  - `eudemon` → `善灵`（eudemon blade→善灵之刃）
  - `sacred` → `神圣`（sacred scourge→神圣之鞭）
- **Rejected**: `demon→魔`（太短，且与怪物名"恶魔"不一致）
- **Rationale**: 保持与怪物分类命名一致（demon→恶魔已在 D-A-034 中确定）。prefix+之+base 格式适用于"附魔武器"命名模式
- **Scope**: `source.txt` 中的武器基础名条目，以及所有引用这些前缀的描述文件

---

### D-B-016 — 武器品牌翻译词典（全表）

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-07-12
- **Source**: Item naming design review (consolidation of zh_weapon_brands_*)
- **Choice**: 以下为武器品牌的完整中文翻译对照表（verbose/terse/adj 三形式）：

| EN (verbose) | EN (terse) | EN (adj) | ZH (names) | ZH (adj) | 注 |
|-------------|-----------|---------|------------|---------|----|
| flaming | flame | flaming | 烈焰 | 烈焰 | — |
| freezing | freeze | freezing | 寒霜 | 寒霜 | — |
| holy wrath | holy | holy | 神圣惩戒 | 圣光 | — |
| electrocution | elec | electric | 电击 | 雷电 | — |
| venom | venom | venomous | 剧毒 | 剧毒 | — |
| protection | protect | protective | 防护 | 防护 | adj=name |
| draining | drain | draining | 吸血 | 生命吸取 | — |
| speed | fast | fast | 疾速 | 疾速 | — |
| heavy | heavy | heavy | 沉重 | 沉重 | adj=name |
| vampirism | vamp | vampiric | 吸血(vampirism) | 吸血 | — |
| pain | pain | painful | 痛苦 | 痛苦 | — |
| antimagic | antimagic | antimagic | 禁魔 | 禁魔 | adj=name |
| distortion | distort | distorting | 扭曲 | 扭曲 | — |
| chaos | chaos | chaotic | 混沌 | 混沌 | — |
| penetration | penet | penetrating | 穿透 | 穿透 | — |
| reaping | reap | reaping | 收割 | 收割 | — |
| spectralising | spect | spectral | 幽魂 | 幽魂 | — |
| rebuke | rebuke | rebuking | 斥责 | 斥责 | — |
| valour | valour | valourous | 勇武 | 勇武 | — |
| entangling | entangle | entangling | 缠绕 | 缠绕 | — |
| sundering | sunder | sundering | 碎裂 | 碎裂 | — |
| concussion | concuss | concussing | 震荡 | 震荡 | — |
| devious | devious | devious | 狡诈 | 狡诈 | adj=name |
| acid | acid | acidic | 酸蚀 | 酸蚀 | — |
| confusion | confuse | confusing | 迷惑 | 迷惑 | v34+ |
| weakness | weak | weakening | 弱化 | 弱化 | v34+ |
| vulnerability | vuln | will-reducing | 意志削弱 | 意志削弱 | v34+ |
| foul flame | foul flame | foul flame | 秽焰 | 秽焰 | v34+ |

- **Rejected**: 英文 terse 形式直接音译（"flame→弗莱姆"），保持全部意译
- **Rationale**: 统一 adj 和 name 形式，除部分特殊项外尽量一致。draining 和 vampirism 的中文区分："吸血"(draining, 每次吸少量) vs "吸血(vampirism)"(不死生物吸血)
- **Scope**: `source.txt` 中的 `weapon_brands_verbose[]` / `weapon_brands_terse[]` / `weapon_brands_adj[]` 对应 T_() 条目
- **Note**: 所有品牌名翻译统一通过 source.txt 中的 T_() 条目管理，无重复数据

### D-B-017 — 基础武器名称纠偏（结构、材质与系列关系）

- **Type**: B — Naming revision
- **Status**: active
- **Date**: 2026-07-13
- **Source**: 基础武器名称复审；对照 `item-prop.cc` 的武器类别、物品描述和法术命名规则中的“忠实且不误导”“系列一致”原则
- **Choice**:
  - `arbalest`：钢弩 → **重弩**。原译把描述中的钢制结构误当成名称限定；`arbalest` 的核心区别是重型弩，不应凭描述添加材质。
  - `dire flail`：恐怖链枷 → **双头链枷**。`dire` 在此是武器型号/规模语义；“恐怖”表达情绪而未区分武器结构，改用稳定的双头结构信息。
  - `morningstar` / `eveningstar`：流星锤 / 黄昏之星 → **晨星锤 / 暮星锤**。两者是对应的钉头锤武器名称，统一保留 morning/evening 的系列差异，并明确武器类别。
  - `executioner's axe`：刽子手之斧 → **刽子手斧**。基础武器名采用紧凑的“修饰语+武器类别”结构；“之”仅用于品牌或 `of` 属格结构。
  - `great mace`：大战锤 → **巨型钉头锤**。`mace` 应与基础名 `mace` 的“钉头锤”词根一致，不能改译为 hammer（战锤）。
  - `quarterstaff`：铁头棍 → **长棍**。物品描述明确为木制战斗棍，原译凭空添加“铁头”；“长棍”保留 quarterstaff 的长棍形制。
- **Rejected**: 保留“钢弩”“铁头棍”等描述性误加材质；将 `eveningstar` 继续译为“黄昏之星”（缺少锤类信息且破坏与 `morningstar` 的对应关系）。
- **Scope**: `crawl-ref/source/dat/i18n/zh/source.txt` 基础武器名条目；不改变品牌、神器专名或物品描述正文。

### D-B-019 — Barding → 马铠（排除"马甲"歧义）

- **Type**: B — Entity ruling
- **Status**: active
- **Date**: 2026-07-14
- **Source**: 玩家反馈——"马甲"有互联网"小号/分身"歧义
- **Choice**: `Barding` → `马铠`
- **Rejected**: `马甲`（游戏玩家首先联想到 sock puppet/小号，而非马用护甲）
- **Rationale**: "马铠"是汉语中马用护甲的正统历史名称（古代亦称"具装"），无网络歧义。`Black Knight's barding` 和描述正文已使用"马铠"，本次统一物品类型名和提示语，消除内部不一致。`centaur barding` 保持"半人马战甲"（centaur 非马，用"战甲"合理）。
- **Affected files**:
  - `dat/i18n/zh/source.txt` ✅（Barding + 提示语两处）
- **Tracking issue**: (none — direct fix)
- **Resolved**: 2026-07-14

---

### D-B-018 — 其他物品名称纠偏与术语登记

- **Type**: B — Naming revision
- **Status**: active
- **Date**: 2026-07-13
- **Source**: 物品基础名、护甲 ego、护符名称复审；对照当前物品描述和实现，遵循“忠实且不误导”原则
- **Choice**:
  - `partisan`：阔刃戟 → **阔头枪**。它是枪头两侧带突出部的长柄枪，不应与 `halberd` 的“戟”混同。
  - `broad axe`：阔斧 → **阔刃斧**。补出 broad 的刃部信息，避免过度省略。
  - `dragon-coil talisman`：龙卷护符 → **盘龙护符**。`coil` 是盘绕形态，不是 tornado/龙卷。
  - `falchion`：弯刃刀 → **弯刃剑**；`old falchion` 同步改为“旧弯刃剑”。物品描述明确为单刃剑，需保留武器类别。
  - `sanguine talisman`：血族护符 → **血色护符**。`sanguine` 指血色/血液意象，不能把效果中的 vampire 反向写入名称。
  - `shadows`（护甲 ego）：暗影庇护 → **暗影**。该 ego 的效果是降低可见距离，不是防护效果。
  - `triple crossbow`：三连弩 → **三弦弩**。当前描述明确为三根弦串联以提高威力，不是三发连射。
- **Rejected**: “阔刃戟”“龙卷护符”“血族护符”“暗影庇护”“三连弩”等会混淆武器类别、形态或机制的译法。
- **Scope**: `source.txt`、旧版本 `old falchion` 条目、神器/测试名称、引文标题和术语表；不改动普通叙事文本中“空气”等自然用语。

---

### D-A-041 — 非 unique 怪物显示名消歧与文学引文例外

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-21
- **Source**: [GitHub Issue #3](https://github.com/yutio8888/crawl-chn-ai-test/issues/3)
  and the archived `monster-name-ssot-nonunique` experiment
- **Problem**: distinct English monsters shared the same Chinese display name,
  while prose databases sometimes used an accidental synonym and sometimes a
  contextually required literary, religious, historical, or lexical rendering.
- **Display-name choices**:
  - `orc sorcerer → 兽人术士`; retain `orc wizard → 兽人巫师`.
  - `alligator snapping turtle → 巨鳄龟`; retain `snapping turtle → 鳄龟`.
  - `Spatial Maelstrom → 空间乱流`; retain `spatial vortex → 空间漩涡`.
  - `zombie → 丧尸`; retain `Jiangshi → 僵尸` for the Chinese
    hopping-vampire entity. Established work titles retain their published
    form, such as 《僵尸世界大战》.
- **Description rule**: when an English monster description explicitly names
  its subject, the Chinese description uses the `source.txt` display name.
  This is a lexical consistency invariant, not permission to replace natural
  Chinese words that refer to a different sense.
- **Quote rule**: ordinary self-reference uses the display-name SSOT
  (`boggart → 博加特`). A quote may retain a different rendering only
  through an exact-key exception with a non-empty contextual reason. Examples
  include Biblical `cherub → 基路伯`, Tolkien's `goblin → 哥布林`,
  natural-history `jackal → 胡狼`, the proper mythic name
  `kraken → 克拉肯`, and lexical `wight → 人`. The blocking checker
  owns the complete executable exception set and rejects stale exceptions.
- **Rejected**: preserving ambiguous display-name collisions; mechanically
  replacing every prose occurrence; global Chinese-word exceptions; treating
  an allowlist as proof that an unrelated future mismatch is valid.
- **Rationale**: map/log identity needs distinct stable names, but literary
  fidelity requires preserving source-specific proper names, established
  scripture terminology, work titles, and genuine alternate senses.
- **Affected authorities**:
  - `dat/i18n/zh/source.txt` and matching ZH prose assets
  - `docs/glossary.md`
  - `.claude/scripts/monster_name_ssot.py`
- **Resolved**: 2026-07-21

---

### D-A-042 — Dispersal → 空间驱离

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 当前法术描述与 `cast_dispersal` 实现复核
- **Choice**: 空间驱离
- **Rejected**: 驱散（Dispersal 旧译；仅否定该法术名，不否定 Dispel 及普通动词“驱散”）
- **Rationale**: `Dispersal` 会将施法者附近的生物传送到远处；成功抵抗的生物仍会被强制闪送一小段距离。“空间驱离”同时表达空间位移和使目标远离，并与已确认的 `Dispel → 驱散` 明确区分，避免误解为解除魔法效果。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt` ✅
  - `crawl-ref/source/dat/descript/zh/spells.txt` ✅
  - `docs/glossary.md` ✅
  - `docs/glossary.utf8` ✅
- **Description correction**: 复核时同步修正“传送掉”“被……被闪送”及
  “被空间的扭曲所混乱”等病句，并明确混乱使用一次独立的意志检定。
- **Resolved**: 2026-07-25

---

### D-A-043 — Mesmerise → 迷魂

- **Type**: A — Entity and terminology ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 当前法术数据、描述、`_mesmerise_los` 与移动限制实现复核
- **Choice**: 迷魂
- **Rejected**:
  - 催眠（旧译；错误暗示睡眠，而法术不施加睡眠）
  - 魅惑（容易与 charming 及阵营控制混淆）
- **Rationale**: 当前 `Mesmerise` 是 5 级怪物诅咒法术，对视野内敌人进行
  意志检定。失败的冒险者无法主动远离施法者，其他生物则陷入
  `ENCH_DAZED`；离开施法者视野会解除玩家的移动限制。“迷魂”保留
  `entrance/mesmerise` 的心智攫取含义，不暗示睡眠或阵营转化，并与既有
  “迷魂宝珠”一致。
- **Terminology scope**: 同批统一直接表示 `mesmerise/mesmerism` 机制的
  法术名、状态短名、冷却、半径、装备说明和消息；自然句中的“迷住”可按
  中文语法保留。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt` ✅
  - `crawl-ref/source/dat/descript/zh/status.txt` ✅
  - `crawl-ref/source/dat/descript/zh/monstatus.txt` ✅
  - `docs/glossary.md` ✅
  - `docs/glossary.utf8` ✅
  - `docs/decisions.md` ✅
- **Supersedes**: `D-C-012` 中暂缓修改 Mesmerise 的历史注记；不影响该
  裁定的元素召唤规则。
- **Resolved**: 2026-07-25

---

## Quick Reference: All Decision IDs

| ID | Entity | Choice | Status |
|----|--------|--------|--------|
| D-A-001 | Sif Muna | 西芙·穆娜 | active — all ✅ |
| D-A-002 | Trog | 特洛格 | active — all ✅ |
| D-A-003 | Kikubaaqudgha | 奇库巴库哈 | active — all ✅ |
| D-A-004 | Nemelex Xobeh · | U+00B7 | active — all ✅ |
| D-A-005 | Vehumet | 维胡梅特 | active — all ✅ |
| D-A-006 | The Shining One | 光辉者 | active — all ✅ |
| D-A-032 | cane toad | 海蟾蜍 | active ✅ |
| D-A-033 | polter- root | 骚灵系 | active ✅ |
| D-A-034 | cacodemon | 恶灵恶魔 | active ✅ |
| D-A-035 | fiend | 邪魔（统一） | active ✅ |
| D-A-036 | vampire | 吸血鬼（基名统一） | active ✅ |
| D-A-037 | skeleton | 骷髅（基名统一） | active ✅ |
| D-A-038 | wraith | 幽魂（统一） | active ✅ |
| D-B-012 | Orb naming | X之球（标准模式） | active ✅ |
| D-B-001 | Brand genitive | 之 | active |
| D-B-002 | List separators | 、+ 和 | active |
| D-B-003 | article_a | skip in ZH | active |
| D-B-004 | conj_verb | disable in ZH | active |
| D-B-005 | Plural marking | remove in ZH | active |
| D-B-006 | Adverb position | before verb | active |
| D-B-007 | spell_title() → DB key | use English | active |
| D-B-008 | Descript mechanics parity | ZH must match EN | active |
| D-B-009 | @keyword@ integrity | must resolve at runtime | active |
| D-B-010 | EN change → ZH review | flag on version drift | active |
| D-B-011 | Tool function language guard | must guard return values | active |
| D-B-013 | Item naming structural patterns | ZH patterns for all categories | active |
| D-B-014 | Item base name translation style | 类+型, 种族之刃, X龙鳞甲 | active |
| D-B-015 | Demon/Sacred/Eudemon prefix | 恶魔/善灵/神圣 | active |
| D-B-016 | Weapon brand dictionary | full ZH table (29 brands) | active |
| D-B-019 | Barding → 马铠 | 马铠 | active ✅ |
| D-C-001 | Skill titles | 216 items | active |
| D-C-002 | Spell names | 6 fixes | active |
| D-C-003 | Item base names | ~200 items | active — all ✅ |
| D-C-004 | Portal .des | ~40 messages | active — all ✅ |
| D-C-005 | Monster YAML names | 489 entries → 100% coverage | active ✅ |
| D-C-006 | Lightning Rod | 雷击杖 | active ✅ |
| D-A-039 | Felid (player species) | 猫 | active ✅ |
| D-A-040 | Octopode (player species) | 章鱼 | active ✅ |
| D-A-041 | non-unique monster display names and quote exceptions | 术士 / 巨鳄龟 / 乱流 / 丧尸 | active ✅ |
| D-A-042 | Dispersal | 空间驱离 | active ✅ |
| D-A-043 | Mesmerise | 迷魂 | active ✅ |
| D-C-007 | Spell name revision — Bolt 系列去"之" | 6 fixes | active |
| D-C-008 | Spell name revision — Cloud 重名拆分 | 2 fixes | active |
| D-C-009 | Spell name revision — Call 系列统一"呼唤" | 5 fixes | active |
| D-C-010 | Spell name revision — 杂项 | 11 fixes | active |
| D-C-011 | Spell name revision — 新增缺失法术 | 12 new entries | active |
| D-C-012 | Spell name revision — 元素召唤统一 | 3 fixes | active |
| D-C-013 | Spell name revision — Blink 系列 | 4 fixes；8 current + 1 axed compatibility | active |
| D-C-014 | Spell name revision — Bolt 系列 | 2 fixes；16 current + 3 axed compatibility | active |
| D-C-015 | Spell name review — Cloud 后缀系列 | 8 current + 5 axed compatibility；4 description fixes | active |
