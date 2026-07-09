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
- **Source**: issues/2 (TODO_GODNAME.md)
- **Choice**: 西芙·穆娜
- **Rejected**: 席夫·穆纳
- **Rationale**: `芙` (lotus) is common in goddess names, better matches the Norse goddess gender than `夫` (man/husband)
- **Affected files**:
  - `dat/database/zh/godname.txt` ✅
  - `dat/descript/zh/gods.txt` (×4) ✅
  - `dat/database/zh/godspeak.txt` (×2) ✅
  - `dat/database/zh/FAQ.txt` ✅
  - `dat/descript/zh/features.txt` ✅
- **Tracking issue**: issue 13
- **Resolved**: 2026-06-27 (commit: issue 13 + follow-up)

---

### D-A-002 — Trog → 特洛格

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-06-26
- **Source**: issues/2 (TODO_GODNAME.md)
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
- **Tracking issue**: issue 13
- **Resolved**: 2026-06-27 (commit: issue 13 + follow-up)

---

### D-A-003 — Kikubaaqudgha → 奇库巴库哈

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: issue 13
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
- **Tracking issue**: issue 13

---

### D-A-004 — Nemelex Xobeh middle dot → U+00B7

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: issue 12 Phase 0
- **Choice**: U+00B7 (·) as separator in 尼姆雷斯·索布
- **Rejected**: U+30FB (・) katakana middle dot
- **Rationale**: U+00B7 is the standard Chinese middle dot; U+30FB is CJK-specific and renders inconsistently across fonts
- **Affected files**:
  - `dat/database/zh/godname.txt` ✅
  - All other references use U+00B7 ✅
- **Tracking issue**: issue 12

---

### D-A-005 — Vehumet → 维胡梅特

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: issue 12 Phase 0
- **Choice**: 维胡梅特
- **Rejected**: (none — this was the original translation, confirmed correct)
- **Rationale**: Phonetic transliteration is accurate and already in use across all files
- **Affected files**: All files use 维胡梅特 ✅
- **Tracking issue**: issue 12

---

### D-A-006 — The Shining One → 光辉者

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: issue 12 Phase 0
- **Choice**: 光辉者
- **Rejected**: (none — confirmed correct)
- **Rationale**: Semantic translation; `光辉` (radiance/glory) + `者` (-er suffix) matches the god title pattern
- **Affected files**: All files use 光辉者 ✅
- **Tracking issue**: issue 12

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
- **Known issue**: "orc wizard" and "orc sorcerer" both resolve to 兽人巫师. Monitor for player confusion; if necessary, differentiate as 兽人巫师 (wizard) / 兽人术士 (sorcerer).

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
- **Source**: Issue 49 monster name terminology review
- **Choice**: Unify `polter-` root under 骚灵
  - `poltergeist → 骚灵`
  - `polterguardian → 骚灵护卫` (no change needed)
- **Rejected**: 吵闹鬼 (too literal, "noisy ghost" misses restless-spirit connotation); 喧灵系 (viable alternative, but 骚灵 is more established in Chinese gaming)
- **Rationale**: 骚灵 (restless spirit) is the standard Chinese fantasy translation for "poltergeist" — matches the German root "poltern" (to rumble/make noise). 吵闹鬼 is too literal and loses the ethereal quality. Unifying under 骚灵 makes `polterguardian` predictable from `poltergeist`.
- **Affected files**:
  - `dat/i18n/zh/source.txt` ✅ (`poltergeist`)
- **Tracking issue**: Issue 49 (monster-name-terminology.md)
- **Resolved**: 2026-07-09

---

### D-A-034 — cacodemon → 恶灵恶魔

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-09
- **Source**: Issue 49 monster name terminology review
- **Choice**: 恶灵恶魔
- **Rejected**: 恶灵 (loses demon classification — 混入幽灵系); 恶灵魔 (unnecessary shortening)
- **Rationale**: Preserves both the "evil spirit" (恶灵) character of the original and the demon classification (恶魔). All other demon-type monsters use 恶魔 as their base classifier; `cacodemon` should not be an exception. 恶灵恶魔 keeps the unique flavor while maintaining terminological consistency.
- **Affected files**:
  - `dat/i18n/zh/source.txt` ✅
- **Tracking issue**: Issue 49 (monster-name-terminology.md)
- **Resolved**: 2026-07-09

---

### D-A-035 — fiend → 邪魔 (统一)

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-09
- **Source**: Issue 49 monster name terminology review
- **Choice**: All fiends → 邪魔
  - `Ice Fiend → 冰霜邪魔`
  - `Brimstone Fiend → 硫磺邪魔`
  - `shadow fiend → 暗影邪魔`
- **Rejected**: 恶魔 (overlaps with demon classification, losing the distinct fiend identity); mixed 邪魔/恶魔 (inconsistent)
- **Rationale**: 邪魔 conveys a more malevolent/sinister connotation than the relatively neutral 恶魔 — appropriate for fiend-type creatures. The project distinguishes between demon, fiend, and devil as three separate creature families; using distinct classifiers preserves this distinction in Chinese.
- **Affected files**:
  - `dat/i18n/zh/source.txt` ✅ (Ice Fiend, Brimstone Fiend, shadow fiend)
- **Tracking issue**: Issue 49 (monster-name-terminology.md)
- **Resolved**: 2026-07-09

---

### D-A-036 — vampire → 吸血鬼 (基名统一)

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-09
- **Source**: Issue 49 monster name terminology review
- **Choice**: Base monster name `vampire → 吸血鬼`, compounds follow 吸血鬼 pattern
  - `vampire (monster) → 吸血鬼`
  - `vampire bat → 吸血鬼蝙蝠`
  - Existing: vampire knight/mage/bloodprince → 吸血鬼骑士/法师/血王子 (no change)
- **Rejected**: 吸血 (base form reads as verb/adjective "bloodsucking" rather than noun "vampire"; inconsistent with all compound forms)
- **Rationale**: The base monster name `vampire` is a noun (the creature), not an adjective. Using 吸血 for the base form creates a noun/adjective inconsistency with all compound forms (吸血鬼骑士, 吸血鬼法师) where 吸血鬼 is the noun prefix. Vampire bat is also a creature name, so follows the same pattern.
- **Affected files**:
  - `dat/i18n/zh/source.txt` ✅
- **Tracking issue**: Issue 49 (monster-name-terminology.md)
- **Resolved**: 2026-07-09

---

### D-A-037 — skeleton → 骷髅 (基名统一)

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-09
- **Source**: Issue 49 monster name terminology review (P2)
- **Choice**: Unify all skeleton forms to 骷髅
  - `skeleton → 骷髅` (from 骸骨)
  - `large skeleton → 大型骷髅` (no change)
  - `small skeleton → 小型骷髅` (no change)
- **Rejected**: 骸骨 (formal/anatomical, less common in gaming); mixed 骸骨/骷髅 (inconsistent)
- **Rationale**: 骷髅 is the standard term for skeleton monsters in Chinese gaming culture. 骸骨 (skeletal remains/bones) is more anatomical and less idiomatic for a hostile creature. The compound forms already use 骷髅; unifying the base form eliminates the inconsistency.
- **Affected files**:
  - `dat/i18n/zh/source.txt` ✅
- **Tracking issue**: Issue 49 (monster-name-terminology.md)
- **Resolved**: 2026-07-09

---

### D-A-038 — wraith → 幽魂 (统一，区分 ghost)

- **Type**: A — Entity ruling
- **Status**: active
- **Date**: 2026-07-09
- **Source**: Issue 49 monster name terminology review (P2)
- **Choice**: All wraith forms → 幽魂
  - `wraith → 幽魂` (from 幽灵)
  - `the Wraith → 幽魂` (no change)
  - `freezing wraith → 冰冻幽魂` (from 冰冻幽灵)
  - `shadow wraith → 暗影幽魂` (from 暗影幽灵)
- **Rejected**: 幽灵 (overlaps with ghost/spectre, losing wraith's distinct identity)
- **Rationale**: 幽魂 (wraith/restless spirit) in Chinese gaming commonly denotes ethereal, life-draining undead — distinct from 幽灵 (ghost, more general). Using 幽魂 for wraiths preserves the undead subtype distinction and matches the unique monster `the Wraith` which already used 幽魂.
- **Affected files**:
  - `dat/i18n/zh/source.txt` ✅
- **Tracking issue**: Issue 49 (monster-name-terminology.md)
- **Resolved**: 2026-07-09

---

### D-B-012 — `X之球` as canonical orb naming pattern

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-07-09
- **Source**: Issue 49 monster name terminology review (P2)
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
- **Tracking issue**: Issue 49 (monster-name-terminology.md)
- **Resolved**: 2026-07-09

---

## Type-B: Rule Rulings (style/grammar/formatting conventions)

---

### D-B-001 — Brand genitive unified to 之

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: issues/8 commit 3
- **Choice**: `Y之X` for all weapon/armour brand names (e.g., `flaming sword` → `火焰之剑`)
- **Rejected**: `Y的X` (colloquial form)
- **Rationale**: `之` is the literary/classical genitive marker appropriate for item names; `的` is colloquial and reads as lower register. Unified across all brands to avoid mixed styles.
- **Scope**: `item-name.cc` brand naming, all weapon/armour ego prefixes
- **Tracking issue**: issues/8

---

### D-B-002 — comma_separated_line Chinese separators

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: issues/8 commit 2
- **Choice**: `、` (U+3001) for list separator, `和` for final conjunction
- **Rejected**: English `, ` and ` and `
- **Rationale**: Chinese enumeration uses `、` between items and `和` before the last item. Using English separators reads as a formatting bug.
- **Scope**: All `comma_separated_line()` calls where the output is player-visible Chinese text
- **Tracking issue**: issues/8

---

### D-B-003 — article_a Chinese skip

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: issues/8 commit 1
- **Choice**: `article_a()` returns empty string in Chinese mode
- **Rejected**: Translating "a/an" as "一个" (over-specifies quantity)
- **Rationale**: Chinese has no articles. Adding `一个` where English uses `a/an` introduces unwanted quantification. Omission is the correct default.
- **Scope**: `english.cc:article_a()`
- **Tracking issue**: issues/8

---

### D-B-004 — conj_verb Chinese disable

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: issues/8 anti-pattern #2
- **Choice**: Never call `conj_verb()` on Chinese strings
- **Rejected**: Calling `conj_verb()` and getting garbled output (e.g., `"抓取s"`)
- **Rationale**: `conj_verb()` applies English conjugation rules (adding -s/-es/-ing suffix). Chinese has no verb conjugation — person/number/tense are expressed through particles and word order, not suffixes.
- **Scope**: All .cc files — this is a NEVER rule (anti-pattern #2 in CLAUDE.md)
- **Tracking issue**: issues/8

---

### D-B-005 — Chinese no plural marking

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: issues/8 commit 2
- **Choice**: Remove English plural `"s"` suffix logic in Chinese mode
- **Rejected**: Retaining English plural markers on Chinese text
- **Rationale**: Chinese nouns have no singular/plural distinction. Plurality is expressed through context, numbers, or measure words — never through noun suffixes.
- **Scope**: All string formatting that conditionally appends "s" based on count
- **Tracking issue**: issues/8

---

### D-B-006 — Adverb position: BEFORE verb in Chinese

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: CLAUDE.md translation rules
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
- **Source**: issue 16
- **Choice**: Database keys use `spell_english_names` (English), not `spell_title()` (Chinese).
  `spell_title()` translation revisions do not require syncing `zh/spells.txt` keys.
- **Rejected**: Chinese spell_title() as DB key source — causes key breakage on translation change
  and key collisions when two spells share the same Chinese name (e.g., Pain/Anguish both 痛苦).
- **Rationale**: English keys eliminate the translation-revision→key-breakage fragility.
  zh/spells.txt now matches all 9 other zh/ database files in using English keys.
- **Scope**: `ability.cc` (ABIL_SIF_MUNA_REPEAT_EXEGESIS), `zh/spells.txt` keys
- **Note**: Issue 16 listed 3 "missing" spells (Gell's Gravity, Unleash Destruction, Stoneshock)
  whose EN keys do not exist in the 0.34.1 spells.txt database. These were likely misidentified
  or refer to spells removed/renamed in earlier versions. No action needed.
- **Tracking issue**: issue 16

---

## Type-C: Batch Rulings (large-scale translation sets)

---

### D-C-001 — Skill titles (216 items)

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: issues/7
- **Choice**: Full Chinese translation of all 216 skill rank titles via `zh_skill_titles` map
- **Rejected**: Partial translation or machine-only translation
- **Rationale**: Skill titles are high-visibility UI text. Each title was manually translated with attention to rank hierarchy and thematic consistency within each skill.
- **Scope**: `skills.cc:zh_skill_titles` map + `skill_title_by_rank()` lookup
- **Tracking issue**: issues/7

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
- **Source**: issue 10
- **Choice**: Chinese `item_base_name()` mapping for all item types
- **Rejected**: English-only item names in Chinese mode
- **Rationale**: Item names are Type I static display data — must be translated at the data layer for consistency.
- **Scope**: `item-name.cc:item_base_name()`
- **Tracking issue**: issue 10
- **Resolved**: 2026-06-27

---

### D-C-004 — Portal .des file messages (~40 items)

- **Type**: C — Batch ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: issue 9
- **Choice**: Chinese initmsg/finalmsg for all 13 portal vault .des files
- **Rejected**: English-only portal messages
- **Rationale**: Portal entry/exit messages are player-visible atmospheric text. Uses `crawl.language()` Lua function for runtime language selection.
- **Scope**: `dat/des/variable/*.des` portal files
- **Tracking issue**: issue 9
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

---

### D-B-008 — Descript ZH 必须与 EN 保持机制一致

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: issue 17
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
- **Tracking issue**: issue 17

---

### D-B-009 — @keyword@ 引用完整性

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: issue 18
- **Choice**: Every @keyword@ referenced in a ZH database file must have a
  corresponding definition in either the same ZH file or the EN fallback.
  Prefix conventions (e.g., `@_graffiti_xxx_@`) must match exactly.
- **Rejected**: Broken @keyword@ references that silently fail at runtime
- **Rationale**: @keyword@ references are resolved at display time. A missing
  definition produces blank output or raw `@_key_@` text — both are
  user-visible bugs. Prefix mismatches (e.g., `@_hailed_god_@` missing
  the `graffiti_` prefix) are a known failure mode (issue 19).
- **Scope**: All `dat/database/zh/*.txt` files
- **Verification**: `check_consistency.sh --database --keywords`
- **Tracking issue**: issue 18

---

### D-B-010 — EN 内容变更时需要 ZH 重新审查

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-27
- **Source**: issues 17+18
- **Choice**: When EN database/descript entries are modified (content change, not
  just formatting), the corresponding ZH entries must be flagged for review.
- **Rejected**: ZH entries silently drifting out of sync with updated EN content
- **Rationale**: Entry count mismatch >10% is a strong signal that ZH has not
  been updated to match EN content changes. Version drift is most common in
  `gods.txt`, `mutations.txt`, `ability.txt` — files tied to game mechanics
  that evolve across versions.
- **Scope**: All `dat/descript/zh/*.txt` and `dat/database/zh/*.txt`
- **Verification**: `check_consistency.sh --stale`
- **Tracking issue**: issues 17+18

### D-B-011 — 工具函数语言守卫

- **Type**: B — Rule ruling
- **Status**: active
- **Date**: 2026-06-28
- **Source**: issue 22
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
- **Tracking issue**: issue 22

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
| D-C-001 | Skill titles | 216 items | active |
| D-C-002 | Spell names | 6 fixes | active |
| D-C-003 | Item base names | ~200 items | active — all ✅ |
| D-C-004 | Portal .des | ~40 messages | active — all ✅ |
| D-C-005 | Monster YAML names | 489 entries → 100% coverage | active ✅ |
| D-C-006 | Lightning Rod | 雷击杖 | active ✅ |
