# Round 3: player-action sentence review (2026-11-12)

This review checked whether player-action and feedback messages read naturally in Chinese. It also includes two cases the maintainer asked for directly:

- The mixed use of "这里有…" and "此处有：…".
- The untranslated klown pie hit message "Plum!".

These two directed cases are not part of the random sample.

## Refs and scope

| | stable | trunk |
|---|---|---|
| Reviewed base | `4af734c175cee41cfaf75142e04bf1a9aea9ee1c` | `40a7b9976ad10aade1a703e510c68ed0667d3ca5` |
| Fix PR | #316 | #315 |
| Head | `580ad4741f` | `e88dc9a326` |
| Merge commit | `ae5a420e78` | `b42709fcba` |

- **Seed.** The random sample uses seed `2026111203` and per-category subseeds `2026111204`–`09`.
- **Random sample.** 72 message families, 12 in each of six categories:
  - A: movement, stairs and doors.
  - B: melee, ranged and throwing.
  - C: item handling.
  - D: consumables.
  - E: spells and abilities.
  - F: rest and status.

  Earlier-round keys are excluded. See `coverage_r3.md` and `selection_log_r3.json`.
- **Directed HERE check.** 76 entries.
- **Klown pie.** The six flavour labels, at both display sites.

## Units

Message families, findings and defect points are counted separately (see `adjudication.json` → `counts`).

**Random sample**

- 5 families with a confirmed finding: B-03, C-07, E-03, F-02 and F-03.
- 5 findings and 5 defect points.
- C-07 covers 6 sibling sentences.

**Directed HERE check**

- 4 confirmed entries with 5 defect points: D-HERE-07, D-HERE-12, D-HERE-16 (2 points) and D-HERE-42.
- 6 entries unified for consistency in the same scene.

**Not fixed**

- Readability advisories are recorded only.
- 39 sentences need runtime output to judge. They are listed as player check points; they are not counted as verified.

These results do not extrapolate to an error rate for the whole catalogue.

## Reviewers

There were two independent lanes, each with its own sample order:

- Lane 1: Opus 5.5, seed 1301.
- Lane 2: GPT-6.1 Sol, seed 2402.

Both lanes resolved terminology context, glossary SHA-256 `fb814f3252f2…`. This was a contextual review, not a blind one.

The host adjudicated against the source code and the catalog. A third agent, Opus 5.5, reviewed the fixes independently (`fix/review-fix.md`). The single writer was Codex gpt-6.1-sol (`fix/fix-delivery.txt`).

## Corrections recorded

The writer corrected two adjudication premises, and the independent review confirmed both against SourceDB trimming in `database.cc`:

- **F-03.** The constrictor-possessive context values are non-empty.
- **D-HERE-16.** The "There is " prefixes are non-empty.

Both defects still stand, for different reasons than first stated. See `adjudication.json` → `premise_corrections`.

On trunk, the C-07 and shaft keys have no current production consumer. The trunk changes to them only keep the shared keys in sync.

## Files

Some archived files differ from the working copies in trailing whitespace only. It was stripped to satisfy the repository whitespace check. The affected files are `outputs/`, `fix/fix-delivery.txt` and `scripts/enrich_r3.py`.

`adjudication.json` is the revised final version. The F-03 `fix` and the D-HERE-16 `problem` texts were updated in place to the corrected statements, and the original premises are kept in `premise_corrections`.


- `adjudication.json`: final verdicts, corrections, the klown pie mapping and the delivery record.
- `families_r3_index.json`: slim index of the frozen inventory. The full inventory (about 3.9 MB, with calls, branch evidence and reconstructions) is not committed. Its SHA-256 is recorded in the index.
- `coverage_r3.md` and `selection_log_r3.json`: inclusion and exclusion rules, pool sizes, gaps left unchecked, and regression controls.
- `outputs/lane{1,2}/`: the raw reviewer outputs.
- `fix/`: the writer's delivery report and the independent fix review.
- `scripts/`: the generators.
  1. Run `build_inventory_r3.py --repo <repo> --out <dir> --previous <round-2 samples_r2.json>`. Use `../translation-sample-review-r2-2026-11-12/samples_r2.json` as the round-2 file. This script also runs `enrich_r3.py` and `render_r3.py`.
  2. Run `validate_r3.py --out <dir>`.

  Always pass `--out` a directory outside this archive. Otherwise the scripts overwrite the frozen files here.

No local gameplay or screenshot acceptance was performed. Test players verify after release, and the player check points are listed in `fix/fix-delivery.txt`.
