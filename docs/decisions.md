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
- **Current-state correction**: 2026-07-25 经 `D-C-016` 复核，本系列按
  完整 inventory 扩展为 10 项现行标题；`Call Down Lightning` 与
  `Call Down Damnation` 都是短语动词 `call down → 降下`，不属于
  “呼唤”词根。原 5 项改名继续有效。

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

### D-C-016 — Spell name review: Call 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英文描述及各法术实际实现逐项复核
- **Scope**: 10 项现行标题：
  - `Call Canine Familiar → 呼唤犬类使魔`
  - `Call Down Damnation → 降下天谴`
  - `Call Down Lightning → 降下闪电`
  - `Call Imp → 呼唤小恶魔`
  - `Call Lost Souls → 呼唤迷失灵魂`
  - `Call of Chaos → 混沌呼唤`
  - `Call Tide → 呼唤潮汐`
  - `Dragon's Call → 龙之呼唤`
  - `Druid's Call → 德鲁伊呼唤`
  - `Hunting Call → 狩猎呼唤`
- **Choice**:
  - 保留前述九项标题。
  - `Druid's Call` 由“德鲁伊召唤”改为“德鲁伊呼唤”；实现会把同层既有
    林地生物移到目标附近，并不创造召唤物。
  - `call/call upon` 表示发出呼唤、号令或祈请时保留“呼唤”词根；
    `call down` 作为短语动词固定译为“降下”，不机械套用词根。
- **Rejected**:
  - 所有 `Call` 一律译为“召唤”：抹去呼唤既有实体、号令盟友和祈请力量
    与 `Summon` 创造召唤物之间的原名差异。
  - “呼唤天谴／呼唤闪电”：误解 `call down` 的短语结构。
  - “德鲁伊召唤”：对当前召回同层既有生物的机制有明确误导。
- **Description corrections**: 恢复犬类使魔重施时清除中毒、提前攻击和
  横扫相邻敌人的效果；明确天谴仅波及相邻生物且通常由能降下天谴者免疫；
  修正小恶魔、迷失灵魂、潮汐、龙之呼唤及狩猎呼唤的遗漏或生硬表述。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`
- **Affected decisions**: 完整复核并扩展 D-C-009；其 5 项既有改名继续有效。

---

### D-C-017 — Spell name review: Summon 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述、召唤实现与实体映射逐项复核
- **Scope**: 42 项含独立 `Summon` 词形的标题；34 项现行、8 项
  `TAG_MAJOR_VERSION == 34` 已移除兼容
- **Choice**:
  - 26 项现行标题保留；
  - 8 项现行标题重译：
    - `Summon Greater Demon`: 召唤高级恶魔 → **召唤高等恶魔**
    - `Summon Ufetubus`: 召唤乌菲图布斯 → **召唤乌菲特布斯**
    - `Summon Sin Beast`: 召唤罪兽 → **召唤罪孽兽**
    - `Summon Holies`: 召唤圣灵 → **召唤神圣生物**
    - `Summon Mana Viper`: 召唤魔力蝰蛇 → **召唤魔力毒蛇**
    - `Summon Emperor Scorpions`: 召唤帝蝎 → **召唤帝王蝎**
    - `Summon Executioners`: 召唤行刑者 → **召唤处刑人**
    - `Summon Seismosaurus Egg`: 召唤震龙蛋 → **召唤地震龙蛋**
  - 8 项已移除兼容标题因机制证据不足暂沿用。
- **Series rule**: 现行 `Summon` 稳定译为“召唤”；召唤具体当前实体时，
  标题必须复用实体显示名。已移除兼容标题不反向约束现行实体词。
- **Rationale**: 七项修正消除标题与现行实体映射的分裂；`Summon Holies`
  实际召出天使、智天使、德瓦或奥法等神圣生物，“圣灵”会误示为灵体或
  特定宗教概念。其余标题与召出的实体、群体、幻象或位面效果一致。
- **Description corrections**: 按当前英文描述与实体词同步修正
  `Summon Horrible Things` 的过时智力机制、`Summon Mana Viper` 的
  量词歧义、`Summon Mortal Champion` 的机制遗漏，以及关联实体名和
  确定性病句；并将直接关联的魔力毒蛇出现消息、处刑人状态与神罚文本
  同步到同一实体词。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `crawl-ref/source/dat/descript/zh/status.txt`
  - `crawl-ref/source/dat/descript/zh/gods.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`
- **Affected decisions**: 复核并确认 `D-C-012` 的现行元素召唤名称；
  补充现行与已移除兼容标题的生命周期边界。

---

### D-C-018 — Spell name review: Breath 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中法术/能力描述、zap 实现、
  地狱巨蛇分支技能表与实体映射逐项复核
- **Scope**: 22 项含独立 `Breath` 词形的标题；20 项现行、2 项
  `TAG_MAJOR_VERSION == 34` 已移除兼容
- **Choice**:
  - 14 项现行标题保留；
  - 6 项现行标题重译：
    - `Cold Breath`: 寒冷吐息 → **寒霜吐息**
    - `Combustion Breath`: 燃烧吐息 → **爆燃吐息**
    - `gehenna serpent of hell breath`: 火焚地狱蛇之吐息 →
      **欣嫩谷地狱巨蛇吐息**
    - `cocytus serpent of hell breath`: 冰狱蛇之吐息 →
      **悲叹河地狱巨蛇吐息**
    - `dis serpent of hell breath`: 铁城蛇之吐息 →
      **铁城地狱巨蛇吐息**
    - `tartarus serpent of hell breath`: 悲叹地狱蛇之吐息 →
      **塔尔塔罗斯地狱巨蛇吐息**
  - 2 项已移除兼容标题因当前描述与实现均不存在而暂沿用。
- **Series rule**: 法术标题中的 `Breath` 稳定后置为“吐息”；标题明确
  指向具体实体变体时，复用完整的分支限定实体名，不另造简称。
- **Rationale**: `Cold Breath` 复用既有能力术语
  `Breathe Frost → 吐息寒霜`，并继续与能封冰的 `Glacial Breath`
  区分；`Combustion Breath` 射出的挥发余烬会在触及每个生物时爆炸，
  “爆燃”比泛称“燃烧”更准确。其余现行标题准确概括实际吐息。
  `Golden Breath` 仅由非龙人龙形态使用，对应金龙的火、冰、毒三重
  吐息，保留“金龙吐息”；4 个地狱巨蛇标题则复用已确认的分支实体名。
- **Description corrections**: 补回 `Miasma Breath` 只影响活物的条件；
  将 `Noxious Breath` 的 vapour 从“蒸汽”修正为“毒雾”，并保留毒素
  抵抗、混乱及随等级扩展范围和持续时间的机制。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `crawl-ref/source/dat/descript/zh/ability.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`
- **Related entity sync**: `Serpent of Hell (%s)` 同步为
  “地狱巨蛇（%s）”，与 `Serpent of Hell → 地狱巨蛇` 一致。

---

### D-C-019 — Spell name review: Dart 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、英中描述、zap 数据与实际使用者逐项复核
- **Scope**: 2 项现行标题，无已移除兼容成员
- **Choice**:
  - `Magic Dart → 魔法飞弹` 保留；
  - `Slug Dart` 由“弹丸飞镖”重译为 **“蛞蝓飞镖”**。
- **Series rule**: 普通 `Dart` 作为尖细投射物时译为“飞镖”；但
  `Magic Dart` 的原文描述明确称其为必中魔法射弹，保留稳定固定译名
  “魔法飞弹”，不为表面统一牺牲意象与辨识度。
- **Rationale**: `Slug Dart` 是飞镖蛞蝓的天生攻击，发射硬化甲壳质
  尖镖；zap 颜色也明确与蛞蝓自身颜色一致。旧译“弹丸飞镖”把 slug
  错解为弹丸并重复表达投射物；“蛞蝓飞镖”保留原名对使用者的双关，
  同时复用 `dart slug → 飞镖蛞蝓` 的实体词。
- **Rejected**:
  - “魔法飞镖”：破坏 `Magic Dart` 已稳定的魔法射弹意象。
  - “弹丸飞镖”：误解 slug，并形成近义重复。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-020 — Spell name review: Shadow/Shadows 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述、Dithmenos shadow
  mimic 调度与各法术实现逐项复核
- **Scope**: 13 项含独立 `Shadow` 或 `Shadows` 词形的标题；12 项现行、
  1 项 `TAG_MAJOR_VERSION == 34` 已移除兼容；连写的 `Shadowball`
  不属于该机械边界
- **Choice**: 12 项现行标题全部保留；`Weave Shadows` 因当前描述和实现
  均不存在而暂沿用。
- **Series rule**: 此系列的 `Shadow/Shadows` 稳定译为“暗影”；后接实体、
  投射物或效果名时使用自然中文定中结构。
- **Rationale**: 现行标题准确表达复制生物、投射物、墙角袭击、范围风暴、
  延时棱镜、召唤物、炮塔、束缚、减速及范围伤害等实际机制。
  `Shadow Shot → 暗影射击` 虽也可提议“暗影弹”，但原名采用动作名且
  现译没有机制误导，不为纯风格偏好改名。
- **Description corrections**: 依当前英文与实现修正 10 项旧描述，恢复
  墙角触发、随机多目标、无视护甲、延时爆炸、提前摧毁减伤、缠绕、
  投射物类型、可见敌人比例、直线减速、强者更快恢复与固定炮塔等信息。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-021 — Spell name review: Throw 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述、zap 与怪物施法实现逐项复核
- **Scope**: 8 项含独立 `Throw` 词形的标题；7 项现行、1 项
  `TAG_MAJOR_VERSION == 34` 已移除兼容
- **Choice**: 7 项现行标题全部保留；已移除的 `Throw → 投掷` 因当前
  描述与实现均不存在而暂沿用。
- **Series rule**: 标题动词 `Throw` 稳定译为“投掷”；实际表现使用
  fire/hurl 等实现动词不改变标题词根。
- **Rationale**: 火焰、冰霜、冰柱、倒刺、盟友、流星索和小丑派均准确
  标示投掷对象。`Throw Klown Pie → 投掷小丑派` 保留 Killer Klown
  的专属物件意象，又不会误示为投掷小丑本体。
- **Description corrections**: 修正 5 项旧描述，恢复 `Throw Ally` 的
  施法者/落点关系、倒刺移动伤害、巨型流星索无视体型的束缚、冰片
  一半伤害无视寒冷抗性，以及小丑派六类不可抵抗临时效果并删除旧机制。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-022 — Spell name review: Beam 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述、目标选择及双段 beam
  实现逐项复核
- **Scope**: 2 项以独立 `Beam` 结尾的现行标题；`Shadow Beam` 已由
  `D-C-020` 审阅，本批复用机制未变化的证据
- **Choice**:
  - `Plasma Beam → 等离子光束` 保留；
  - `Shadow Beam → 暗影光束` 保留（复用 `D-C-020`）。
- **Series rule**: 表示连续束状投射物的 `Beam` 稳定译为“光束”。
- **Rationale**: `Plasma Beam` 自动选择最远敌人之一，先发射穿透性
  电击束并无视一半护甲，再沿同一路径追加火焰束；“等离子光束”忠实于
  原名且不遗漏形态。无需添加原名没有的“雷火”等机制说明词。
- **Description corrections**: 将“穿透一半防具”修正为“无视目标一半的
  护甲”，并明确火焰束沿同一路径随后射出。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-023 — Spell name review: Gaze 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与怪物凝视实现逐项复核
- **Scope**: 7 项含独立 `Gaze` 词形的现行标题，无已移除兼容成员
- **Choice**: 6 项标题保留；`Draining Gaze` 由“吸取凝视”重译为
  **“衰竭凝视”**。
- **Series rule**: `Gaze` 稳定后置为“凝视”；`draining` 若施加
  Drain/衰竭而没有把生命或魔力转移给施法者，译为“衰竭”，不用“吸取”。
- **Rationale**: `Draining Gaze` 以负能量按最大生命比例施加衰竭，
  不治疗施法者；旧名会误示生命转移。`Antimagic Gaze` 则确实汲取魔力
  并治疗施法者，但标题重点是反魔法效果，现译准确。其余标题直接对应
  麻痹、困惑、虚弱、玻璃化和变异效果。
- **Description corrections**: 重译 `Draining Gaze` 与
  `Mutagenic Gaze` 的过时描述，并统一 7 项关于 line of sight 与
  line of fire 的表述；补回比例衰竭、能量积累、爆炸和不可抵抗等机制。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-024 — Spell name review: Touch 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与施法实现逐项复核
- **Scope**: 2 项含独立 `Touch` 词形的现行标题，无已移除兼容成员
- **Choice**: `Agonising Touch → 剧痛之触` 与
  `Confusing Touch → 困惑之触` 均保留。
- **Series rule**: 此系列的名词性 `Touch` 后置译为“之触”。
- **Rationale**: 前者直接将相邻生物生命减半但不致死，后者给惯用手附魔，
  通过不造成伤害的触碰尝试使目标困惑；两个标题都准确概括结果与施法
  方式，不需要把全部限制写入名称。
- **Description correction**: 为 `Confusing Touch` 补回 dominant hand
  的“惯用手”限定。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-025 — Spell name review: Arrow 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述、zap 与 beam 实现逐项复核
- **Scope**: 4 项以独立 `Arrow` 结尾的现行标题，无已移除兼容成员
- **Choice**: 保留 `Poison Arrow → 毒箭`、`Stone Arrow → 石箭`、
  `Pyre Arrow → 烈火箭` 与 `Mercury Arrow → 汞矢`。
- **Series rule**: 投射物形态明确为 arrow 的标题通常后置为“箭”；
  `Mercury Arrow → 汞矢` 是为避免与 `Quicksilver Bolt → 水银箭`
  重名而保留的辨识性例外。
- **Rationale**: `Mercury Arrow` 与 `Quicksilver Bolt` 的英文名称、
  伤害类型和附加效果均不同，不能合并为同一中文名。旧裁定 `D-C-002`
  已用“汞矢”保留 mercury 与 quicksilver 的词面差异，本次机制复核未发现
  足以推翻它的误导。其余三项分别准确对应剧毒魔法箭、岩刺投射物和会
  附着目标的液态火焰。
- **Description corrections**: 用当前机制重译 `Mercury Arrow` 的过时
  气态汞描述；修正 `Poison Arrow` 的抗性术语和伤害比例表述、
  `Pyre Arrow` 的附着条件及中文语病，并使 `Stone Arrow` 与
  `sharp spine of rock` 对齐。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`
- **Affected decisions**: 复核并保留 `D-C-002` 的 Mercury Arrow
  消除重名裁定。

---

### D-C-026 — Spell name review: Flame/Flames 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与火焰效果实现逐项复核
- **Scope**: 10 项含独立 `Flame` 或 `Flames` 词形的标题；7 项现行、
  3 项已移除兼容
- **Choice**: 9 项标题保留；`Stoke Flames` 由“煽动火焰”重译为
  **“煽旺火焰”**。通常采用“火焰”，在
  `Inner Flame → 内焰`、`Cleansing Flame → 净化之焰`、
  `Ring of Flames → 烈焰之环` 等凝练复合名称中保留“焰／烈焰”变体。
- **Series rule**: `Flame/Flames` 的核心语义统一为“火焰”；“焰”是
  不改变机制含义的紧凑词形，不强制把已经自然且可辨识的复合标题机械
  改成同一字面后缀。
- **Rationale**: 7 项现行法术分别对应小团火焰、黏着燃烧物、神圣火环、
  目标体内火焰、神圣净化爆发、煽旺成蔓延炼狱及向外扩张的火焰波；
  “煽旺”准确表达 `stoke` 的添燃料使火势更旺，而旧译“煽动”通常用于
  挑动情绪或事端，动宾搭配生硬。其余当前标题准确概括核心效果。
  3 项已移除兼容成员没有当前描述或实现，不用历史记忆反推重译。
- **Description corrections**: 为 `Inner Flame` 补回目标每次被击中时
  也会释放火焰的机制；清理 `Sticky Flame` 非实体附着条件中的中文语病。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`
- **Affected decisions**: `Throw Flame` 复用 `D-C-021` 的未变化证据，
  不重复计入全量进度。

---

### D-C-027 — Spell name review: Form 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前生命周期与兼容记录逐项复核
- **Scope**: 6 项以独立 `Form` 结尾的标题，全部为
  `TAG_MAJOR_VERSION == 34` 已移除兼容记录
- **Choice**: `Hydra Form → 多头蛇变形`、`Spider Form → 蜘蛛变形`、
  `Ice Form → 寒冰变形`、`Statue Form → 石像变形`、
  `Storm Form → 风暴变形` 与 `Dragon Form → 巨龙变形` 均暂沿用。
- **Series rule**: 此组历史标题稳定采用 `Form → 变形`；该规则仅说明
  当前兼容标题的一致性，不把已移除法术的历史机制当作现行事实。
- **Rationale**: 六个中文标题都准确表达相应目标形态，内部结构一致；
  但当前源码只保留 `AXED_SPELL` 身份，没有现行描述或实现。缺少可验证
  机制时不凭历史记忆重译，也不把旧法术与现行护符变形系统混为一谈。
- **Description corrections**: 无；六项均无当前英中描述。
- **Affected files**:
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-028 — Spell name review: Poison/Poisonous 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与毒素效果实现逐项复核
- **Scope**: 9 项含独立 `Poison` 或 `Poisonous` 词形的标题；5 项现行、
  4 项已移除兼容
- **Choice**: 8 项标题保留；`Spit Poison` 由“喷毒”重译为
  **“喷吐毒液”**，与其直接引用的同名能力及既有能力术语一致。
- **Series rule**: `Poison/Poisonous` 按语境译为“毒素／毒／淬毒”；
  法术标题若直接复用同名能力描述，应保持同一动作名称。
- **Rationale**: “喷吐毒液”准确表达怪物从口中喷出毒液，也避免法术标题
  与其 `<Spit Poison ability>` 描述目标使用两个译名。其余现行标题分别
  对应毒云、毒箭、点燃毒素和瞬时毒气；四项已移除兼容记录缺少当前
  描述或实现，暂沿用。
- **Description corrections**: `Ignite Poison` 的 poisoned creatures
  由误译的“有毒的生物”改为“中毒的生物”，并明确毒云与迷乱烟雾；
  `Poisonous Vapours` 补回只存在于施法当回合及任何毒素抗性即可免疫的
  机制。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`
- **Affected decisions**: `Poisonous Cloud` 与 `Poison Arrow` 分别复用
  `D-C-015`、`D-C-025` 的未变化证据，不重复计入全量进度。

---

### D-C-029 — Spell name review: Dispel 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述、法术 metadata 与 zap 实现逐项复核
- **Scope**: 2 项含独立 `Dispel` 词形的现行标题，无已移除兼容成员
- **Choice**: 保留 `Dispel Undead → 驱散亡灵` 与
  `Dispel Undead Range → 远程驱散亡灵`。
- **Series rule**: 此处 `Dispel → 驱散` 表示破坏维系魔法造物的力量；
  不与表示把生物传送远离的 `Dispersal → 空间驱离` 混用。
- **Rationale**: 两项法术都以 `BEAM_DISPEL_UNDEAD` 扰乱维系亡灵形体
  的力量并自动命中；区别在于玩家版仅作用于相邻目标，怪物 Range 版射程
  为 4。“驱散亡灵”准确保留原名的魔法语义，“远程”也清楚标示版本差异。
- **Description corrections**: 将生硬的“干扰将亡灵的身体缚在一起的
  力量”改为“扰乱维系亡灵形体的力量”，并统一相邻目标表述。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-030 — Spell name review: Awaken 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与召唤／激活实现逐项复核
- **Scope**: 5 项以 `Awaken` 开头的标题；4 项现行、1 项已移除兼容
- **Choice**: `Awaken Forest → 唤醒森林`、`Awaken Vines → 唤醒藤蔓`、
  `Awaken Flesh → 唤醒血肉`、`Awaken Armour → 唤醒护甲` 与
  `Awaken Earth → 唤醒大地` 均保留。
- **Series rule**: 此系列稳定采用 `Awaken X → 唤醒X`。
- **Rationale**: 四项现行法术分别赋予树木攻击能力、使藤蔓破土抓取敌人、
  激活肉堆形成憎恶及从护甲记忆显现战斗回响；“唤醒”能自然覆盖使静物
  或潜在力量开始行动的共同语义。`Awaken Earth` 已移除且缺少当前机制，
  暂沿用。
- **Description corrections**: 无；四项现行中文描述与英文机制一致。
- **Affected files**:
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-031 — Spell name review: Maxwell's 专名系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与通道／空间位移实现逐项复核
- **Scope**: 2 项以 `Maxwell's` 开头的现行标题，无已移除兼容成员
- **Choice**: 保留 `Maxwell's Capacitive Coupling → 麦克斯韦之电容耦合`
  与 `Maxwell's Portable Piledriver → 麦克斯韦之便携打桩机`。
- **Series rule**: 人名 `Maxwell → 麦克斯韦`，法术所有格结构稳定采用
  “麦克斯韦之……”。
- **Rationale**: 两项标题均准确保留专名及电学／机械意象。电容耦合通过
  通道积累电荷并蒸发最近敌人；便携打桩机以空间压缩和骤然舒张把整列
  生物推向障碍物，标题的夸张机械比喻与实际效果相符。
- **Description corrections**: 为电容耦合补回启动需要可见目标、释放时
  可能选中另一个敌人的规则；完全重译仍误写为“召唤移动桩锤”的便携
  打桩机描述，恢复空间压缩、整列推进、碰撞目标及距离增伤机制。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-032 — Spell name review: Forge 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与锻造构装实现逐项复核
- **Scope**: 4 项以 `Forge` 开头的现行标题，无已移除兼容成员
- **Choice**: `Forge Lightning Spire → 锻造闪电尖塔`、
  `Forge Blazeheart Golem → 锻造炽心魔像`、
  `Forge Monarch Bomb → 锻造君主炸弹` 与
  `Forge Phalanx Beetle → 锻造方阵甲虫` 均保留。
- **Series rule**: 锻造术系列稳定采用 `Forge X → 锻造X`。
- **Rationale**: 四项都由施法者构建持续存在的机械或元素造物，而不是
  临时召来既存生物；“锻造”准确表达学派与创造动作。尖塔、炽心魔像、
  君主炸弹和方阵甲虫也分别对应实际生成物及其核心战术角色。
- **Description corrections**: 四项中文描述均按当前英文重译或补全；
  恢复闪电尖塔优先攻击最远敌人、炽心魔像的创造者依存与法术威力效果、
  君主炸弹的部署／追踪／再次施法引爆规则，以及方阵甲虫的护甲加成、
  啃咬、回归优先级和法术威力缩放。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-033 — Spell name review: Iskenderun's 专名系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与战斗法球／冲击实现逐项复核
- **Scope**: 2 项以 `Iskenderun's` 开头的现行标题，无已移除兼容成员
- **Choice**: `Iskenderun's Battlesphere` 由“伊斯肯德伦之战斗球”重译为
  **“伊斯肯德伦之战斗法球”**；保留
  `Iskenderun's Mystic Blast → 伊斯肯德伦之神秘冲击`。
- **Series rule**: 人名 `Iskenderun → 伊斯肯德伦`，所有格采用
  “伊斯肯德伦之……”；实体 `battlesphere` 统一译为“战斗法球”。
- **Rationale**: 运行时消息、怪物名和术语表均已使用“战斗法球”，旧标题
  “战斗球”既破坏实体一致性，也易被理解成普通球类。神秘冲击则准确保留
  原名意象，并不需要把范围击退机制塞入标题。
- **Description corrections**: 战斗法球描述恢复最重伤目标优先、必中齐射
  及创造者可安全穿透法球位置的规则；神秘冲击补回法术威力提高伤害和
  击退距离。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-034 — Spell name review: Vhi's 专名系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与冲锋、近战附伤及怪物施法实现逐项复核
- **Scope**: 2 项以 `Vhi's` 开头的现行标题，无已移除兼容成员
- **Choice**:
  - `Vhi's Electric Charge`：维之电荷 → **维之电击冲锋**
  - `Vhi's Electrolunge`：维之电冲 → **维之电击突进**
- **Series rule**: 人名 `Vhi → 维`，所有格采用“维之……”；`Electric
  Charge` 保留向敌人冲锋的动作义，`Electrolunge` 用“突进”保留
  lunge 的近身攻击义。
- **Rationale**: 玩家版会沿路径冲到附近敌人身边并发动高命中近战攻击，
  “电荷”把 `charge` 错解为静态电学名词，完全隐藏核心动作。怪物版采用
  同一位移攻击实现，但英文以 `lunge` 区分；“电冲”构词生硬且动作不清，
  “电击突进”既与玩家版形成系列，也保留原名差异。
- **Description corrections**: 玩家版把误译的“蓄力长度”改为“冲锋距离”；
  怪物版删除旧机制“化作穿透性闪电并传送”，恢复冲向敌人、高命中近战、
  法术威力附加电击伤害、穿过危险格与置换目的地生物的当前规则。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-035 — Spell name review: Cigotuvi's 专名系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与瘴气扩散实现逐项复核
- **Scope**: 1 项现行标题与 2 项已移除兼容标题
- **Choice**: 保留 `Cigotuvi's Putrefaction → 西格图维之腐烂`、
  `Cigotuvi's Degeneration → 西格图维之退化` 与
  `Cigotuvi's Embrace → 西格图维之拥抱`。
- **Series rule**: 人名 `Cigotuvi → 西格图维`，所有格采用
  “西格图维之……”；已移除兼容标题只按现存英语语义判断，不用现行法术
  机制反推。
- **Rationale**: “腐烂”准确概括加速伤口组织腐败并涌出瘴气的现行效果；
  “退化”和“拥抱”忠实对应两项已移除标题，缺乏当前描述与实现，不作
  推测性改名。
- **Description corrections**: 现行法术中文描述完全沿用旧版杀死目标后
  制造骷髅的机制。本批按当前英文与实现重译，恢复重伤活物目标限制、
  数回合瘴气扩散、减速与剧毒、施法者脚下不生成但并非免疫，以及暂时
  生命汲取会随法术威力减轻的规则。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-036 — Spell name review: Ozocubu's 专名系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与冰甲／视野制冷实现逐项复核
- **Scope**: 2 项以 `Ozocubu's` 开头的现行标题，无已移除兼容成员
- **Choice**: 保留 `Ozocubu's Armour → 奥佐库布之护甲` 与
  `Ozocubu's Refrigeration → 奥佐库布之制冷`。
- **Series rule**: 人名 `Ozocubu → 奥佐库布`，所有格采用
  “奥佐库布之……”；`Armour → 护甲`、`Refrigeration → 制冷`。
- **Rationale**: “护甲”准确概括厚冰提供护甲加成的自我防护；
  “制冷”保留将整片视野空气降至严寒的主动过程，也与单体“冰冻”等法术
  区分。标题无需枚举移动解除或相邻盟友减伤等二级规则。
- **Description corrections**: 无；两项中文描述均覆盖当前英文机制。
- **Affected files**:
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-037 — Spell name review: Gell's 专名系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、加沃特法术描述、重力铃鼓描述与两项重力实现逐项复核
- **Scope**: 2 项以 `Gell's` 开头的现行标题
- **Choice**: 保留 `Gell's Gavotte → 盖尔之加沃特` 与
  `Gell's Gravitas → 盖尔之重力`。
- **Series rule**: 人名 `Gell → 盖尔`，所有格采用“盖尔之……”；
  舞曲名 `Gavotte → 加沃特`，引力效果 `Gravitas → 重力`。
- **Rationale**: 加沃特本是舞曲名，能保留让全体生物随重力方向翻滚的
  舞蹈意象；“重力”直接对应铃鼓将怪物拉向中心并固定的效果，也保留
  `gravitas` 的重量感。两项无需改名。
- **Description corrections**: Gavotte 法术描述与当前英文一致；
  Gravitas 没有独立法术描述，其效果由重力铃鼓物品描述承载。该描述把
  `Evocations` 误译成“召唤术”，本批修正为术语表规定的“激活技能”。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/items.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-038 — Spell name review: Borgnjor's 专名系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与完全治疗、最大生命损失及尸手束缚实现逐项复核
- **Scope**: 2 项以 `Borgnjor's` 开头的现行标题，无已移除兼容成员
- **Choice**: `Borgnjor's Revivification` 由“博格尼尔之复活”重译为
  **“博格尼尔之复苏”**；保留
  `Borgnjor's Vile Clutch → 博格尼尔之邪恶抓握`。
- **Series rule**: 人名 `Borgnjor → 博格尼尔`，所有格采用
  “博格尼尔之……”。
- **Rationale**: Revivification 只能由仍活着的施法者使用，效果是完全
  治疗并永久牺牲部分最大生命，不能使死者复活；“复活”会与真正的
  resurrection 机制混淆，“复苏”保留恢复生命力的原义而不制造死亡复生
  暗示。Vile Clutch 召出尸手抓住并持续束缚区域内敌人，现译准确。
- **Description corrections**: Revivification 将错误术语“法术力量”统一为
  “法术威力”；Vile Clutch 的区域、束缚与挣脱条件均已完整译出。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-039 — Spell name review: Alistair's 专名系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与醉酒／行走蒸馏器实现逐项复核
- **Scope**: 2 项以 `Alistair's` 开头的现行标题
- **Choice**: 保留 `Alistair's Intoxication → 阿利斯泰尔之醉` 与
  `Alistair's Walking Alembic → 阿利斯泰尔之行走蒸馏器`。
- **Series rule**: 人名 `Alistair → 阿利斯泰尔`，所有格采用
  “阿利斯泰尔之……”；`Intoxication → 醉`，`Alembic → 蒸馏器`。
- **Rationale**: “醉”简洁概括将脑组织转化为酒精并造成混乱的炼金效果；
  “行走蒸馏器”准确表现能近战、酿造药水并自行分发的移动炼金构装。
- **Description corrections**: Walking Alembic 描述完整。Intoxication
  原中文用复数代词“他们”承接单数施法者，容易误读为被接触的目标眩晕；
  本批明确为施法者成功接触其他心灵后会短暂眩晕。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-040 — Spell name review: Eringya's 专名系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与毒沼地形、鳄鱼攻击及拖拽实现逐项复核
- **Scope**: 2 项以 `Eringya's` 开头的现行标题，无已移除兼容成员
- **Choice**: 保留 `Eringya's Noxious Bog → 埃林吉亚之毒沼` 与
  `Eringya's Surprising Crocodile → 埃林吉亚之意外鳄鱼`。
- **Series rule**: 人名 `Eringya → 埃林吉亚`，所有格采用
  “埃林吉亚之……”；关联引文中的人名同步使用同一译法。
- **Rationale**: “毒沼”准确概括污泥造成的有毒沼泽地形；“意外鳄鱼”
  保留 `Surprising Crocodile` 刻意突兀、荒诞的标题语气，也符合鳄鱼从
  施法者脚下突然出现并发动攻击的机制。
- **Description corrections**: 鳄鱼法术旧中文只写“在目标附近召唤并攻击”，
  本批补全相邻目标、从施法者脚下随浑水出现、强化攻击、拖拽双方、安全
  下马及存续期间不可重施；关联引文“埃琳吉娅”统一为“埃林吉亚”。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `crawl-ref/source/dat/descript/zh/quotes.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-041 — Spell name review: Nazja's 专名系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与构装体修复／强化实现逐项复核
- **Scope**: 2 项以 `Nazja's` 开头的现行标题
- **Choice**: 保留 `Nazja's All-Purpose Tempering → 纳兹亚之通用淬炼`
  与 `Nazja's Percussive Tempering → 纳兹亚之冲击淬炼`。
- **Series rule**: 人名 `Nazja → 纳兹亚`，所有格采用“纳兹亚之……”；
  `Tempering → 淬炼`，`All-Purpose → 通用`，`Percussive → 冲击`。
- **Rationale**: 两项均以魔法锤修复并强化构装体，故“淬炼”准确；
  怪物版可影响任意附近构装体，适合“通用”，玩家版敲击时迸发伤害性
  冲击波，适合“冲击”。
- **Description corrections**: 两段中文仍描述旧版强化已装备武器或护甲。
  本批按当前英文与实现重译，恢复构装体目标、修复与攻击强化、邻近敌人
  冲击波伤害，以及强化消退前不可重复施放；并明确玩家版只作用于自身
  锻造术创造物，怪物版可作用于任意附近构装体。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-042 — Spell name review: Olgreb's 专名系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与持续毒害实现逐项复核
- **Scope**: 1 项以 `Olgreb's` 开头的现行标题
- **Choice**: 保留 `Olgreb's Toxic Radiance → 奥尔格雷布之毒辐射`。
- **Series rule**: `Olgreb → 奥尔格雷布`；`Toxic Radiance → 毒辐射`。
- **Rationale**: 法术使施法者持续向整个视野辐射毒能量，“毒辐射”准确
  同时表达毒属性、向外放射和持续范围效果。
- **Description corrections**: 机制内容完整；将“在法术持续时内持续”的
  重复病句润色为“在法术持续期间不断”，不改变语义。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-043 — Spell name review: Lehudib's 专名系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Source**: 511 项 spell inventory、当前英中描述与水晶投射物伤害实现逐项复核
- **Scope**: 1 项以 `Lehudib's` 开头的现行标题
- **Choice**: 保留 `Lehudib's Crystal Spear → 勒胡迪布之水晶矛`。
- **Series rule**: 人名 `Lehudib → 勒胡迪布`，所有格采用
  “勒胡迪布之……”；`Crystal Spear → 水晶矛`。
- **Rationale**: 该法术以短射程发射致命尖锐的水晶碎片，标题中的“水晶矛”
  同时保留材质、长尖投射物意象及原名强度，符合 8 级塑能／土系高伤害机制。
- **Description corrections**: 将“一个致命、锋利的水晶碎片”润色为
  “一枚致命而锋利的水晶碎片”，修正量词和连接，不改变机制。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-044 — Spell name review: 单成员专名批次 A

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: Yara、Leda、Lee、Martyr 各 1 项现行标题
- **Choice**: 保留 `Yara's Violent Unravelling → 亚拉之猛烈解构`、
  `Leda's Liquefaction → 勒达之液化`、`Lee's Rapid Deconstruction →
  李之快速解构` 与 `Martyr's Knell → 殉道者之丧钟`。
- **Rationale**: 四项分别准确对应撕裂附魔、液化地面、快速粉碎目标，
  以及殉道者灵魂死亡／转化的丧钟意象。
- **Description corrections**: Leda、Lee、Martyr 描述与英文一致；
  Yara 补足“相邻生物”中心词并统一非人称代词。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-045 — Spell name review: 单成员专名批次 B

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: Brom、Trog、Tukima、Sheza、Sentinel 各 1 项现行标题
- **Choice**: 保留“布罗姆之碾压巨石”“特洛格之手”“图基玛之舞”
  “谢扎之舞”“哨兵印记”。
- **Rationale**: 五项分别准确对应滚石碾压、神祇庇护、武器倒戈之舞、
  群体活化武器之舞，以及暴露目标位置的标记。
- **Description corrections**: 重译 Sentinel 的全层信标机制；Brom 恢复
  碾过死者、连锁推动、窄道磨损及碎裂条件并删除旧爆炸机制；Sheza 修正
  武器代词；Trog 能力说明补足“恢复效果”中心词。Tukima 描述完整。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `crawl-ref/source/dat/descript/zh/ability.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-046 — Spell name review: Hoarfrost 词根系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 2 项含 `Hoarfrost` 的现行标题
- **Choice**: 保留 `Hoarfrost Cannonade → 白霜炮击` 与
  `Hoarfrost Bullet → 白霜弹`。
- **Series rule**: `Hoarfrost → 白霜`；`Cannonade → 炮击`；
  `Bullet → 弹`。
- **Rationale**: 两项属于同一冰霜火炮机制；“白霜”准确表达覆盖目标并
  减速的脆霜，“炮击”表达两座火炮持续齐射，“弹”对应火炮发射的单枚
  冰霜碎片。
- **Description corrections**: 重译 `Hoarfrost Cannonade` 中文描述，
  补回两座火炮、远程攻击、脆霜减速、逐发自耗及强化最终齐射。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-047 — Spell name review: Death's Door

- **Type**: C — Single-item ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: `Death's Door` 现行法术标题
- **Choice**: 保留 `Death's Door → 死亡之门`。
- **Rationale**: “死亡之门”准确保留英文习语的门槛意象，也与施法者将
  生命降至濒死值、短暂近乎免疫伤害、结束后暂时不能重施的机制一致。
- **Description corrections**: 修正施法者代词指代和亡灵限制末句的
  中文语法，不改变机制含义。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-048 — Spell name review: Freeze/Freezing/Frozen 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 4 项现行法术及 1 项已移除兼容标题
- **Choice**: 将 `Freezing Gust → 冰冻狂风` 重译为“冰冻阵风”；保留
  `Freeze → 冰冻`、`Flash Freeze → 急冻`、
  `Frozen Ramparts → 冰冻壁垒` 与 `Freezing Aura → 冰封灵气`。
- **Series rule**: Freeze 词形按实际语法和机制译为“冰冻／急冻／冰封”；
  `Gust → 阵风`，不得夸大为“狂风”。
- **Rationale**: “阵风”准确对应 gust 的短促气流，并与穿透性寒气束机制
  一致；其余标题分别准确表达直接冻结、瞬发急冻、覆冰墙壁和已移除灵气。
- **Description corrections**: 重译 `Freezing Gust` 的穿透寒气与沿途
  留云机制；删除 `Flash Freeze` 对已冻结目标“没有影响”的过时说法。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-049 — Spell name review: Acid/Corrosive 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 3 项以酸液或腐蚀为核心的现行法术标题
- **Choice**: 保留 `Spit Acid → 喷吐酸液`、`Acid Ball → 酸液球` 与
  `Corrosive Bolt → 腐蚀箭`。
- **Series rule**: `Acid → 酸液` 表达攻击物质；`Corrosive → 腐蚀`
  表达性质或附加效果，不强制合并为单一汉字词根。
- **Rationale**: 两项 Acid 标题分别准确表达喷吐动作和爆炸球状投射物；
  “腐蚀箭”则准确表达穿透酸液束造成的腐蚀效果，且已在 Bolt 批次完成
  机制审阅。
- **Description corrections**: 无；两项新增审阅法术的中英文描述一致。
- **Affected files**:
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-050 — Spell name review: Frost/Rime/Chill 寒冷术语批次

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: `Creeping Frost`、`Rebounding Chill`、`Rimeblight` 与
  `Splinterfrost Shell` 四项现行标题
- **Choice**: 将 `Rebounding Chill → 弹跳寒冷` 重译为“弹跳寒流”；
  保留“蔓延冰霜”“霜疫”与“碎霜之壳”。
- **Series rule**: `frost → 冰霜／霜`、`rime → 霜`；
  投射性 `chill → 寒流`。
- **Rationale**: “寒流”能作为反弹穿透束的具体实体，避免“弹跳寒冷”的
  抽象搭配；其余三项分别准确表达沿墙蔓延冻气、致命霜冻瘟疫和会碎裂
  发射冰片的冰壳。
- **Description corrections**: 重译 `Rebounding Chill` 的穿透、沿墙
  反弹与双次命中机制；重译 `Splinterfrost Shell` 的半圆屏障、推开生物、
  墙段反击和远离融化机制。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-051 — Spell name review: Permafrost Eruption

- **Type**: C — Single-item ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: `Permafrost Eruption` 现行法术标题
- **Choice**: 保留 `Permafrost Eruption → 永冻爆发`。
- **Rationale**: “永冻”准确表达潜藏于大地的 ancient cold，
  “爆发”同时概括严寒喷涌与落石轰击；无需把自动选取敌人密集处写入标题。
- **Description corrections**: 重译中文描述，补回落石必中、寒冷无视护甲、
  邻近目标、自动选择敌人密集处及不在施法者身旁爆发。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-052 — Spell name review: Lightning/Electricity/Thunder 元素系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 10 项标题含 `Lightning`、`Electric/Electrical/Electricity`
  或 `Thunder` 的法术；4 项新增审阅，6 项复用既有证据
- **Choice**: 保留全部现行中文标题及已移除的“雷霆之环”兼容标题。
- **Series rule**: 依构词分别采用“闪电／电击／电光／雷霆”，不机械
  统一；标题需保留投射物、连锁、召唤或环形等核心形态。
- **Rationale**: “召唤球形闪电”“连锁闪电”“电光球”分别准确表达
  追敌爆炸实体、逐目标连锁电弧和命中爆炸的电能球；“雷霆之环”缺少
  当前机制证据，保留兼容译名。其余六项已经由 Bolt、Call、Forge、
  Breath、Vhi 或单词标题批次确认。
- **Description corrections**: 修正 `Chain Lightning` 旧版“不断弹跳直至
  接地”机制；修正 `Conjure Ball Lightning` 球状闪电的代词。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-053 — Spell name review: Glaciate/Iceblast/Hailstorm 寒冷术语批次

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: `Glaciate`、`Iceblast` 与 `Hailstorm` 三项现行标题
- **Choice**: 将 `Glaciate → 冰川` 重译为“冰封”；保留
  `Iceblast → 冰爆` 与 `Hailstorm → 冰雹风暴`。
- **Rationale**: `Glaciate` 是使目标覆冰、冻结的动词，而“冰川”仅表示
  地貌名词；“冰封”准确对应锥形寒冰冲击造成的减速与冰块化。另两项
  分别准确表达撞击爆炸的冰块和环形冰雹风暴。
- **Description corrections**: 重译并润色三项中文描述，修正缺失中心词、
  风暴眼邻接范围、冰块数量及寒冷抗性措辞，不改变机制。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-054 — Spell name review: Fireball 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 2 项现行法术及 1 项已移除兼容标题
- **Choice**: 保留 `Fireball → 火球`、`Ghostly Fireball → 幽灵火球`
  与 `Delayed Fireball → 延迟火球`。
- **Series rule**: `Fireball → 火球`；复合标题保留幽灵性质或延迟方式。
- **Rationale**: 普通火球是爆炸火焰球；幽灵火球虽造成负能量而非火焰，
  但“幽灵”保留原名的死灵意象并与普通火球区分；已移除标题无当前机制
  证据，不用历史印象反推重译。
- **Description corrections**: 修正 `Ghostly Fireball` 中文病句，并补明
  其只会使爆炸范围内的活物衰竭。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-055 — Spell name review: Death 独立词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 标题含独立 `Death` 的 3 项现行法术，不含已审阅的
  `Death's Door`
- **Choice**: 保留 `Death Channel → 死亡通道`、
  `Death Rattle → 死亡之响`、`Kiss of Death → 死亡之吻`。
- **Rationale**: 三项分别保留持续引导死亡力量、垂死喘响与死亡之吻的
  原名意象，能与幽魂留存、瘴气吐息和双方生命代价机制对应。
- **Description corrections**: 修正 `Death Channel` 对 living、demonic、
  holy 与 spectres 的错误翻译；润色 `Kiss of Death` 的机械直译和代词。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-056 — Spell name review: Teleport 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 1 项现行法术及 2 项已移除兼容标题
- **Choice**: 将 `Control Teleport → 传送控制` 修正为“控制传送”；
  保留 `Teleport Other → 传送他人` 与 `Teleport Self → 自我传送`。
- **Series rule**: `Teleport → 传送`；受事者后置，控制动作前置。
- **Rationale**: “传送他人”和“自我传送”正确表达对象；“传送控制”
  是英语词序倒装，“控制传送”才是自然的动宾结构。
- **Description corrections**: 重译 `Teleport Other`，补回尝试判定、
  短暂延迟和将目标送出施法者视野三项机制。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-057 — Spell name review: Control 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 3 项已移除兼容标题；1 项复用 Teleport 批次，2 项新增
- **Choice**: 将 `Control Undead → 亡灵控制` 修正为“控制亡灵”；
  保留 `Control Winds → 控风术` 与已审阅的“控制传送”。
- **Series rule**: `Control + object` 采用动宾结构；可在自然且无歧义时
  缩写为“控X术”。
- **Rationale**: “亡灵控制”是英语词序移植，“控制亡灵”才明确表达
  动作和对象；“控风术”已经是自然、明确的同义压缩。
- **Description corrections**: 无；三项均无当前描述或实现。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-058 — Spell name review: Fire Storm 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 1 项现行法术及 1 项已移除兼容标题
- **Choice**: 保留 `Fire Storm → 火焰风暴` 与
  `Chant Fire Storm → 咏唱火焰风暴`。
- **Series rule**: `Fire Storm → 火焰风暴`；仪式动作 `Chant → 咏唱`。
- **Rationale**: 现行法术是 9 级塑能／火焰法术，在指定目标处制造大范围
  火焰风暴并留下短暂火旋涡，“火焰风暴”忠实且与宏大强度相称。
  已移除标题完整保留咏唱动作和基础法术名，无需重译。
- **Description corrections**: 将 `Fire Storm` 末句调整为自然中文，
  明确一半伤害无视火焰抗性，不改变机制。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-059 — Spell name review: Haste 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 2 项现行法术及 1 项已移除兼容标题
- **Choice**: 保留 `Haste → 加速`、`Haste Other → 加速他人`、
  `Haste Plants → 加速植物`。
- **Series rule**: `Haste → 加速`；受事者后置。
- **Rationale**: 三项标题分别准确表达提高施法者、附近盟友或植物的行动
  速度；现行两项描述与英文一致。
- **Description corrections**: 无。
- **Affected files**:
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-060 — Spell name review: Invisibility 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 2 项现行法术
- **Choice**: 将 `Invisibility Other → 隐身他人` 重译为“使他人隐形”；
  保留 `Invisibility → 隐身术`。
- **Series rule**: 状态采用“隐形”；对他人施加时用显式使役结构。
- **Rationale**: “隐身他人”把不及物的“隐身”机械用作及物动词；
  “使他人隐形”明确受事者和结果。自身法术“隐身术”自然明确。
- **Description corrections**: 无；两项中英文描述一致。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-061 — Spell name review: Abjuration 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 1 项现行法术及 1 项已移除兼容标题
- **Choice**: 保留 `Abjuration → 驱逐术` 与
  `Aura of Abjuration → 驱逐灵气`。
- **Series rule**: `Abjuration → 驱逐`，表示削减敌对召唤物存续时间。
- **Rationale**: “驱逐”准确表达让召唤生物提前离场，而不误示直接伤害
  或普通击退；灵气兼容标题沿用同一词根。
- **Description corrections**: 润色 Abjuration 中文描述，删除冗余量词并
  明确作用于所有附近敌对召唤生物。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-062 — Spell name review: Infusion 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 3 项已移除兼容标题
- **Choice**: 保留 `Ephemeral Infusion → 短暂灌注`、
  `Infusion → 灌注术`、`Lethal Infusion → 致命灌注`。
- **Series rule**: `Infusion → 灌注`；修饰语前置，单独成名时可加“术”。
- **Rationale**: 三项中文结构自然且词根一致；由于没有当前描述或实现，
  不依据历史印象扩写机制或改名。
- **Description corrections**: 无。
- **Affected files**:
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-063 — Spell name review: Song 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 2 项现行法术及 1 项已移除兼容标题
- **Choice**: 保留 `Siren Song → 塞壬之歌`、`Avatar Song → 化身之歌`
  与 `Song of Shielding → 护盾之歌`。
- **Series rule**: `Song → 歌`；所属实体或作用采用“X之歌”。
- **Rationale**: 三项分别准确保留塞壬、化身和护盾意象；现行两项标题
  不需展开意志抵抗、移动限制、眩晕或召来溺魂等后续效果。
- **Description corrections**: 无；现行中英文描述一致。
- **Affected files**:
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-064 — Spell name review: Animate 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 1 项现行法术及 1 项已移除兼容标题
- **Choice**: 保留 `Animate Dead → 操纵死尸`；将
  `Animate Skeleton → 召唤骷髅`修正为“操纵骷髅”。
- **Series rule**: 此死灵法术系列统一采用 `Animate → 操纵`，不得与
  `Summon → 召唤`混用。
- **Rationale**: 现行法术使施法者杀死的活物化作丧尸复起，“操纵死尸”
  保留驱使尸体行动的死灵意象；兼容标题原译把 Animate 误作 Summon，
  “操纵骷髅”忠实保留动作和对象，并恢复系列一致性。
- **Description corrections**: 将“复活成丧尸／复活怪物”改为“化作丧尸
  复起”，避免误示真正复生，同时保留概率、持续时间、重施和离层规则。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-065 — Spell name review: Shot 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 3 项现行怪物法术
- **Choice**: 保留 `Crystallising Shot → 结晶射击`、
  `Harpoon Shot → 鱼叉射击` 与 `Iron Shot → 铁弹`。
- **Series rule**: `shot` 须按标题中的实际指称判断；表示射击动作时采用
  “射击”，表示所发射的重型弹体时可采用“弹”，不作机械统一。
- **Rationale**: 前两项标题突出结晶化和鱼叉拉拽攻击，`Iron Shot`
  则直接指巨大沉重的金属弹体；三项均符合描述和实现。
- **Description corrections**: 重译 `Crystallising Shot` 中文描述，
  移除旧版寒冷伤害与冰霜路障机制，恢复水晶碎片及全伤害脆化效果。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-066 — Spell name review: Hurl 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 3 项现行法术
- **Choice**: 将 `Hurl Damnation` 从“投掷诅咒”改为“投掷天谴”；
  保留 `Hurl Sludge → 投掷污泥` 与
  `Hurl Torchlight → 投掷火炬之光`。
- **Series rule**: `Hurl → 投掷`；伤害机制 `Damnation → 天谴`，
  不得与 `curse → 诅咒` 混同。
- **Rationale**: 三项标题均描述掷出相应能量或物质；Damnation
  明确是无视常规防护的专门伤害机制，而非诅咒状态。
- **Description corrections**: 修正共用能力描述中的“天遣”错字、
  相邻范围、护甲术语、伊莱德莱姆努尔译名及不自然的生物类别表述。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `crawl-ref/source/dat/descript/zh/ability.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-067 — Spell name review: Launch 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 3 项现行法术
- **Choice**: 保留 `Launch Sporangium → 发射孢子囊`、
  `Launch Clockwork Bee → 发射发条蜜蜂` 与
  `Launch Bomblet → 发射小型炸弹`。
- **Series rule**: 对实体进行投送时，`Launch → 发射`。
- **Rationale**: 三项均实际把孢子囊、机械蜜蜂或小型炸弹送向战场。
- **Description corrections**: 重译 `Launch Bomblet` 的现行部署机制；
  修正 `Launch Sporangium` 将原生质体间距误写为孢子囊间距的问题。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-068 — Spell name review: Blast 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 2 项现行法术及 1 项已移除兼容标题；已在专名系列审阅的
  `Iskenderun's Mystic Blast` 不重复计数
- **Choice**: 保留 `Wind Blast → 风击`、`Fortress Blast → 堡垒冲击`
  与 `Silver Blast → 白银冲击`。
- **Series rule**: `blast` 按介质和表现可译为“击”或“冲击”，不机械统一。
- **Rationale**: “风击”简洁表达强风冲击，“堡垒冲击”保留以自身坚固程度
  蓄积动能波的意象；已移除标题缺乏现行机制证据，暂沿用“白银冲击”。
- **Description corrections**: 重译 `Fortress Blast`，恢复蓄力、固定、
  被位移取消、法术威力影响蓄力速度及护甲值决定伤害等现行机制。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-069 — Spell name review: Blade 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 1 项现行法术及 2 项已移除兼容标题
- **Choice**: 保留 `Rending Blade → 撕裂之刃`、
  `Sure Blade → 精准之刃` 与 `Blade Hands → 利刃之手`。
- **Series rule**: 武器或肢体刃化语境中的 `blade → 刃`。
- **Rationale**: 三项分别准确表达来回撕裂的能量刃、精准之刃和手部刃化。
- **Description corrections**: 重译 `Rending Blade`，补全来回攻击附近敌人、
  无法抵抗、封存全部剩余法力、结束返还及每点法力增伤。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-070 — Spell name review: Destruction 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 4 项现行法术
- **Choice**: 将 `Major Destruction` 从“大型毁灭”改为“强力毁灭”；
  保留 `Orb of Destruction → 毁灭法球`、
  `Legendary Destruction → 传奇毁灭` 与
  `Unleash Destruction → 释放毁灭`。
- **Series rule**: `Destruction → 毁灭`；强度级别 `major → 强力`，
  不误译成物理尺寸“大型”。
- **Rationale**: 四项均表示高破坏力魔法；“强力毁灭”准确反映随机有害
  射束或爆炸的等级，避免暗示效果范围或实体尺寸。
- **Description corrections**: 无；中英文描述一致。同步术语表中
  `Orb of Destruction` 的旧记录“毁灭之球”为实际标题“毁灭法球”。
- **Affected files**:
  - `crawl-ref/source/dat/i18n/zh/source.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-071 — Spell name review: Warp 词形系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 2 项现行法术及 1 项已移除兼容标题
- **Choice**: 保留 `Warp Space → 扭曲空间`、`Warp Body → 扭曲身体`
  与 `Warp Weapon → 扭曲武器`。
- **Series rule**: 表示异常改变空间、身体或武器性质时，`Warp → 扭曲`。
- **Rationale**: 三项名称均准确指向被扭曲的对象，不承诺具体后续效果。
- **Description corrections**: 重译两项现行描述，恢复 `Warp Body` 的目标、
  伤害、短暂变异和玻璃化替代，以及 `Warp Space` 的范围伤害与短距闪现。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

---

### D-C-072 — Spell name review: Might/Other 目标系列

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-07-25
- **Scope**: 5 项现行法术（4 项 `Other` 后缀及基础 `Might`）
- **Choice**: 保留 `Might → 强壮`、`Might Other → 强壮他人`、
  `Heal Other → 治愈他人`、`Berserk Other → 狂暴他人` 与
  `Regenerate Other → 再生他人`。
- **Series rule**: `X Other` 作为对他人施加 X 效果的紧凑标题时采用
  “X他人”；法术显示标题 `Might → 强壮` 与状态机制域“强效”分开。
- **Rationale**: 五项均清楚表达施法者自身或他人作为效果目标，且与
  “加速他人”“使他人隐形”等已审阅标题的紧凑命名方式相容。
- **Description corrections**: 修正 `Might` 两项的中文病句，
  `Heal Other` 与 `Berserk Other` 的目标、语序和伤害术语，并补回
  `Regenerate Other` 恢复量与目标最大生命值成正比的规则。
- **Affected files**:
  - `crawl-ref/source/dat/descript/zh/spells.txt`
  - `docs/glossary.md`
  - `docs/glossary.utf8`
  - `docs/decisions.md`

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
| D-C-016 | Spell name review — Call 词形系列 | 1 fix；10 current；7 description fixes | active |
| D-C-017 | Spell name review — Summon 词形系列 | 8 fixes；34 current + 8 axed compatibility | active |
| D-C-018 | Spell name review — Breath 词形系列 | 6 fixes；20 current + 2 axed compatibility | active |
| D-C-019 | Spell name review — Dart 词形系列 | 1 fix；2 current | active |
| D-C-020 | Spell name review — Shadow/Shadows 词形系列 | 12 current + 1 axed compatibility；10 description fixes | active |
| D-C-021 | Spell name review — Throw 词形系列 | 7 current + 1 axed compatibility；5 description fixes | active |
| D-C-022 | Spell name review — Beam 词形系列 | 2 current；1 description fix | active |
| D-C-023 | Spell name review — Gaze 词形系列 | 1 fix；7 current；7 description fixes | active |
| D-C-024 | Spell name review — Touch 词形系列 | 2 current；1 description fix | active |
| D-C-025 | Spell name review — Arrow 词形系列 | 4 current；4 description fixes | active |
| D-C-026 | Spell name review — Flame/Flames 词形系列 | 1 fix；7 current + 3 axed compatibility；2 description fixes | active |
| D-C-027 | Spell name review — Form 词形系列 | 6 axed compatibility | active |
| D-C-028 | Spell name review — Poison/Poisonous 词形系列 | 1 fix；5 current + 4 axed compatibility；2 description fixes | active |
| D-C-029 | Spell name review — Dispel 词形系列 | 2 current；2 description fixes | active |
| D-C-030 | Spell name review — Awaken 词形系列 | 4 current + 1 axed compatibility | active |
| D-C-031 | Spell name review — Maxwell's 专名系列 | 2 current；2 description fixes | active |
| D-C-032 | Spell name review — Forge 词形系列 | 4 current；4 description fixes | active |
| D-C-033 | Spell name review — Iskenderun's 专名系列 | 1 fix；2 current；2 description fixes | active |
| D-C-034 | Spell name review — Vhi's 专名系列 | 2 fixes；2 current；2 description fixes | active |
| D-C-035 | Spell name review — Cigotuvi's 专名系列 | 1 current + 2 axed compatibility；1 description fix | active |
| D-C-036 | Spell name review — Ozocubu's 专名系列 | 2 current | active |
| D-C-037 | Spell name review — Gell's 专名系列 | 2 current；1 related item description fix | active |
| D-C-038 | Spell name review — Borgnjor's 专名系列 | 1 fix；2 current；1 description fix | active |
| D-C-039 | Spell name review — Alistair's 专名系列 | 2 current；1 description clarification | active |
| D-C-040 | Spell name review — Eringya's 专名系列 | 2 current；1 description + 1 quote fix | active |
| D-C-041 | Spell name review — Nazja's 专名系列 | 2 current；2 description fixes | active |
| D-C-042 | Spell name review — Olgreb's 专名系列 | 1 current；1 wording fix | active |
| D-C-043 | Spell name review — Lehudib's 专名系列 | 1 current；1 wording fix | active |
| D-C-044 | Spell name review — 单成员专名批次 A | 4 current；1 description clarification | active |
| D-C-045 | Spell name review — 单成员专名批次 B | 5 current；4 description fixes | active |
| D-C-046 | Spell name review — Hoarfrost 词根系列 | 2 current；1 description retranslation | active |
| D-C-047 | Spell name review — Death's Door | 1 current；2 wording fixes | active |
| D-C-048 | Spell name review — Freeze/Freezing/Frozen 词形系列 | 4 current + 1 axed；1 rename + 2 description fixes | active |
| D-C-049 | Spell name review — Acid/Corrosive 词形系列 | 3 current；1 reused；no text fixes | active |
| D-C-050 | Spell name review — Frost/Rime/Chill 寒冷术语批次 | 4 current；1 rename + 2 description retranslations | active |
| D-C-051 | Spell name review — Permafrost Eruption | 1 current；1 description retranslation | active |
| D-C-052 | Spell name review — Lightning/Electricity/Thunder 元素系列 | 9 current + 1 axed；4 new + 6 reused；2 description fixes | active |
| D-C-053 | Spell name review — Glaciate/Iceblast/Hailstorm 寒冷术语批次 | 3 current；1 rename + 3 description fixes | active |
| D-C-054 | Spell name review — Fireball 词形系列 | 2 current + 1 axed；1 description fix | active |
| D-C-055 | Spell name review — Death 独立词形系列 | 3 current；2 description fixes | active |
| D-C-056 | Spell name review — Teleport 词形系列 | 1 current + 2 axed；1 rename + 1 description retranslation | active |
| D-C-057 | Spell name review — Control 词形系列 | 3 axed；2 new + 1 reused；1 rename | active |
| D-C-058 | Spell name review — Fire Storm 词形系列 | 1 current + 1 axed；1 description wording fix | active |
| D-C-059 | Spell name review — Haste 词形系列 | 2 current + 1 axed；no text fixes | active |
| D-C-060 | Spell name review — Invisibility 词形系列 | 2 current；1 rename | active |
| D-C-061 | Spell name review — Abjuration 词形系列 | 1 current + 1 axed；1 wording fix | active |
| D-C-062 | Spell name review — Infusion 词形系列 | 3 axed；no text fixes | active |
| D-C-063 | Spell name review — Song 词形系列 | 2 current + 1 axed；no text fixes | active |
| D-C-064 | Spell name review — Animate 词形系列 | 1 current + 1 axed；1 rename + 1 description fix | active |
| D-C-065 | Spell name review — Shot 词形系列 | 3 current；1 description retranslation | active |
| D-C-066 | Spell name review — Hurl 词形系列 | 3 current；1 rename + shared description fixes | active |
| D-C-067 | Spell name review — Launch 词形系列 | 3 current；2 description fixes | active |
| D-C-068 | Spell name review — Blast 词形系列 | 2 current + 1 axed；1 description retranslation | active |
| D-C-069 | Spell name review — Blade 词形系列 | 1 current + 2 axed；1 description retranslation | active |
| D-C-070 | Spell name review — Destruction 词形系列 | 4 current；1 rename + glossary sync | active |
| D-C-071 | Spell name review — Warp 词形系列 | 2 current + 1 axed；2 description retranslations | active |
| D-C-072 | Spell name review — Might/Other 目标系列 | 5 current；5 description fixes | active |
