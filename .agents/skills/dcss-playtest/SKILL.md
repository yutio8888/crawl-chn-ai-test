---
name: dcss-playtest
description: Run evidence-backed real gameplay tests of Dungeon Crawl Stone Soup, especially Chinese console builds, with branch-focused routing, survival rules, and per-action captures. Use for playtesting a candidate build, reaching Lair/Orcish Mines, or analyzing why an automated playtest stalled.
---

# DCSS Playtest

Use this Skill for actual gameplay testing, not translation-only review. Keep the
user's endpoint: a report, a fix, or a merge. This Skill does not add commit,
release, or publication authority.

## Inputs and isolation

Record before play:

- candidate commit/tag, crawl-ref tree, build source, frontend, OS/arch;
- binary SHA-256 and `-version` output;
- glossary SHA-256 from `context_resolve.sh` when translation judgments are in
  scope;
- one isolated runtime and save/morgue/macro/home directory per lane, plus a
  dedicated tmux socket.

Never reuse a user save directory. Do not run wizard, debug explore, memory
reads, save edits, or death rollback. Normal auto-explore (`o`) and auto-attack
(`Tab`) are allowed; they are not debug modes.

Capture a labelled 80x24 screen after each meaningful action. Preserve
`actions.jsonl`, raw terminal output, the final save, the character dump, and
the real process exit code.

## Choose a character for depth, not novelty

For a first branch-progression run:

- Prefer **Minotaur Fighter** (shield + one-handed weapon) or **Minotaur
  Berserker**. Both are forgiving and straightforward.
- Keep one weapon class; train weapon skill to a comfortable delay first, then
  Fighting for HP, then Armour/Dodging/Shields as equipment dictates.
- For MiBe, treat Berserk as an emergency tool, not a default opener.
- Use the heaviest armour/shield the character can carry without wrecking
  attack speed. Carry curing, haste, might, blinking, and teleport options.
- A caster run should focus one attack school to a low failure rate before
  branching into defence or summons.

### Caster baseline: Deep Elf Conjurer (Alchemy + Conjuration + Spellcasting)

A proven 15-rune reference character (`morgue-yutio888-20261104-160724.txt`,
0.35-trunk-004 web, seed `4302450506678966134`) started as a Deep Elf Conjurer
and prioritized **Alchemy + Conjurations + Spellcasting** early, then widened
into elemental schools.

Early order:

1. Train **Conjurations** first enough to make the starting attack spell
   reliable; add **Alchemy** for the poison/alchemy attack line and
   **Spellcasting** for MP and spell slots.
2. Reference milestones: Alchemy 1 on D:1, Conjurations 5 on D:2, Spellcasting 5
   and Alchemy 5 by D:4. Do not spread into every school before this core works.
3. Typical early pickups: Searing Ray on D:1–2, Fulminant Prism and Iskenderun's
   Mystic Blast on D:2, Blink on D:4, Olgreb's Toxic Radiance on D:6,
   Iskenderun's Battlesphere on D:8, Mephitic Cloud by D:10–11, Airstrike /
   Freezing Cloud around D:8.
4. Take **Sif Muna** when found (the reference took her on D:5) for channeling,
   spell gifts, and mana recovery. High Intelligence and MP management matter
   more than melee damage.
5. After the core, add Fighting for HP, Dodging, Shields, and one or two
   elemental schools that match the spells actually found. The reference ended
   broad (Spellcasting 27, Conjurations 23, Fire/Ice/Air/Earth 23, Alchemy 8,
   Fighting/Dodging/Shields 27, Translocations 16), but that is a late-game
   outcome, not an early target.

Caster combat rules:

- Fight from corridors and doors; use Fulminant Prism/Mephitic Cloud/Freezing
  Cloud to break groups; retreat and kite rather than trading melee.
- Keep Blink/teleport and a shield/robe option; low HP is the primary danger.
- Use channeling/MP recovery before MP reaches zero; do not hoard escape
  consumables.
- Inspect spell failure and spell power; train the school of the spell you
  actually use, not a theoretical endgame school.

Do not switch builds mid-run to chase loot. Depth comes from a coherent build,
not from clearing every optional vault.

## Route: reach the branches before the run decays

The Lair entrance appears on D:8–D:11; the Orcish Mines entrance appears on
D:9–D:12. Do not spend the whole session clearing D:1–D:5.

Suggested route card:

| Depth | Goal | Discipline |
|---|---|---|
| D:1–D:4 | Get online, find Temple, basic gear | Fight only what blocks exploration; skip optional uniques |
| D:5–D:7 | Power spike, god, better weapon/armour | Stair-dance dangerous packs; do not full-clear |
| D:8–D:11 | **Find Lair and Orc entrances** | Fully reveal each candidate level near stairs; enter a branch when found |
| Lair:1 / Orc:1 | Capture branch evidence | Explore 30–50 turns, then return if the other branch is still missing |

Use `Ctrl-F` to search known features (stairs, branch names, shops). Treat it as
a convenience for **already known** features, not as a way to discover an
unseen branch stair. If a branch entrance is visible, capture it before
descending. Entering a branch means a screen showing `Lair:1` or `Orc:1`; a
message or a guess is not proof. Record a missing branch as a Validation Gap,
never as a pass.

### Budget and per-level audit

For a branch-focused lane, reserve **90–120 minutes** and allow at most two
fresh characters. Depth is more important than kill count: a shorter run that
enters a branch is better evidence than a long full clear that never reaches
D:8.

Use soft checkpoints, not rigid quotas:

- about D:5 with 2,500–4,000 turns;
- about D:8 with 4,500–7,000 turns;
- first branch entrance before 10,000 turns.

If the run is far behind, **timebox** shops, identification, and low-threat
fights rather than skipping them: they provide information, consumables, and
XP. Cut optional vaults, portal detours, and repeated UI inspection first. Do
not skip healing or safety to catch up.

At each D:8–D:11 level:

1. Check `%` and `X` to see the map and current depth.
2. Auto-explore safe reachable areas; stop on dangerous monsters or low HP.
3. Record which regions are unexplored and which are marked dangerous.
4. Revisit after recovering or rerouting through another staircase.
5. Capture the branch stair and the first `Lair:1`/`Orc:1` screen.

If the entrance is not found, record the explored area and the remaining
unexplored area. “Not found” is not “not present.”

## Survival and stop rules

These are playtest rules, not game rules:

- Rest to full in a safe, cleared area before entering a new room. Below
  **75% HP**, do not start optional fights or chase.
- At **< 50% HP**, stop auto-explore, retreat toward a cleared stair, and use
  healing/escape consumables. At **< 30% HP**, or when one more hit could kill,
  use an emergency option immediately or leave the level; do not continue
  ordinary attacks.
- Do not start a fight at low HP just to clear one more room. Do not press
  `Tab` into an unseen or ranged threat; examine with `x`/`v` first.
- In dangerous fights, send **one key at a time** and read the screen after
  each action. Avoid long key batches while HP is dropping, a status is
  changing, or a new monster appears.
- Do not skip every unique or group. Engage when the power check below favors
  you; a capable character that avoids all fights stops gaining XP and never
  reaches the branches. Skip only when clearly underpowered, out of escape
  options, or the fight would be in bad terrain.
- Use stairs to split packs: retreat upstairs, rest, then fight the first
  pursuer. Use corridors and doors to limit line of sight, then kill the split
  group rather than abandoning the floor.
- Poison, constriction, confusion, and berserk ending are decision points.
  Check whether the next hit or poison tick can kill before resting or
  continuing.
- A natural death is valid evidence. Restart at most once in the same lane and
  record both characters; never restore a save to undo death.
- Stop when both branch targets are captured, the time/risk budget is spent, or
  the character cannot safely continue. Report the stop reason explicitly.

Depth targets are more important than kill count. A 1,500-turn run stuck on
D:4 is less useful than a 1,200-turn run that reaches D:9 and enters Lair.

### Combat power evaluation

Before a unique, a large group, or an unknown dangerous monster, pause and
check the player sheet and the target:

- HP/MP, AC/EV/SH, weapon delay and damage, resistances, and current statuses;
- known healing, haste, might, agility, resistance, blink, teleport, wands,
  throwing items, god abilities, and summons;
- escape route and terrain: corridor, door, staircase, open room, water, lava;
- enemy abilities and speed via `x`/`v`, especially smiters, casters, paralysis,
  ranged attackers, and summons.

Engage when most of these are true: HP is at least ~75%, a retreat route
exists, the fight can be taken in a corridor or at a stair, dangerous casters
can be focused first, and at least one emergency consumable is ready. Pre-buff
before entering, not after HP collapses. Use wands/throwing/god abilities as
part of the plan, not as a last resort.

If the check fails, do not simply walk away from the branch: retreat to a
chokepoint or cleared stair, split the group, heal/buff, and re-engage. Change
level only when the position is genuinely lost, then return by another stair.
“Avoid every unique/group” is a failure mode, not a safety rule.

## Consumables, identification, and threat handling

- Use identify scrolls proactively once the character is safe. Identify unknown
  potions, scrolls, and wands in batches; prioritise healing, escape, resistance,
  and emergency items. Do not hoard identification for a perfect item while
  carrying unknown healing or escape options.
- Use consumables early enough to matter. At ~50–60% HP, heal before the next
  dangerous exchange; pre-buff with might/haste/agility/resistance before a
  unique or group, not after the fight turns bad. Use wands and throwing items
  on dangerous casters/ranged threats. Hoarding a heal until 20% HP is a
  common way to lose a winnable fight.
- Visit shops and identify gear when the route allows. Shops are useful for
  filling resistance/escape gaps; timebox them, but do not skip them as a class.
  Low-threat fights are normal XP and practice; do not avoid all of them either.
  The rule is **route progress first**, not “skip everything optional.”
- Against a **pursuing unique**, first decide whether you are prepared to fight
  in a corridor/stair. If yes, stop retreating, pre-buff, and fight with an
  escape route. If not, go upstairs or change level, heal/buff on a cleared
  floor, and return through another staircase. If it follows, repeat the
  stair/level change. Do not trade hits in the open while unprepared.
- Against a **sleeping dangerous unique**, do not wake it accidentally. Use the
  map (`X`) and the exclusion command (`e`) to mark it and its approach, then
  route around. Keep the exclusion until the area is safe. Do not auto-explore
  or auto-travel through an excluded sleeping unique. If it blocks the only
  route or must be cleared, prepare buffs/escape first, then wake and fight it
  deliberately.
- Keep escape consumables identified before D:8. If the character has no known
  healing/blink/teleport, spend identification and shop time to acquire or
  identify them before entering a branch-search level.

## Common failure modes to avoid

Recent automated runs failed to reach Lair/Orc for predictable reasons:

- full-clearing early levels and optional vaults instead of heading to D:8;
- fighting a pursuing unique or group in the open without buffs/escape, or
  avoiding every fight until the character is too weak to progress;
- waking a sleeping dangerous unique while auto-exploring;
- hoarding identify scrolls and leaving healing/escape consumables unknown;
- hoarding healing/haste/might until critical HP instead of using them early;
- stopping at low HP without using stairs, haste, blink, teleport, or curing;
- treating “no branch entrance seen on one path” as “branch absent” without
  fully exploring D:8–D:11;
- spending the whole session on item/menu inspection and build experiments;
- switching weapon classes or spreading skill XP after finding a shiny item;
- mistyping command keys and triggering explore-mode or travel prompts;
- reporting a branch as covered without a `Lair:1`/`Orc:1` capture.

When the run stalls, inspect the last 20 actions and the current level map
before deciding whether to retreat or reroute. Do not keep auto-exploring into
an unknown dangerous area.

Save normally and verify a reload at least once before D:8, and again before or
after a branch entry once the area is safe. Saving is not a checkpoint for
undoing death; never restore a copy after a fatal mistake.

## Evidence and report

Write to the lane directory only:

- `screens/<sequence>-<meaning>.txt` for every novel screen, branch entry,
  shop/altar, combat result, and anomaly;
- `actions.jsonl` with UTC, keys, and screen label;
- `issues.json` for confirmed problems with full text, screen, turn/place,
  keys, expected/actual, reproducibility, and regression status;
- `observations.json` for uncertain behavior;
- `report.md` with candidate metadata, character/seed, turns/XL/depth, route,
  branch coverage, issues, validation gaps, and save/dump/exit paths.

Use the actual exit code from the game process. A fixed `echo 0` in a launcher
is not evidence.

## References

Strategy sources used for this protocol:

- CrawlWiki Walkthrough: <http://crawl.chaosforge.org/Walkthrough>
- CrawlWiki Early Game Character Building:
  <http://crawl.chaosforge.org/Early_Game_Character_Building>
- MiBe beginner guide: <https://dungeoncrawlstonesoup.com/guides/mibe>

Reference build data: `morgue-yutio888-20261104-160724.txt` (Deep Elf Conjurer,
Sif Muna, 15 runes, 0.35-trunk-004 web, seed `4302450506678966134`).

The wiki walkthrough gives the D:8–D:11 Lair and D:9–D:12 Orc ranges, the
Lair-first recommendation, and the “skip optional floors/branches” principle.
The MiBe guide adds the practical early route: train one weapon + Fighting,
full-clear toward Lair, use stairs/corridors, avoid frivolous Berserk, and use
Trog's Hand against willpower threats.
