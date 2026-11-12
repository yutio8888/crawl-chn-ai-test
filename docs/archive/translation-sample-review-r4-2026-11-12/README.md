# Round 4: stratified translation sample review (2026-11-12)

## Refs and scope

| | stable | trunk |
|---|---|---|
| Reviewed base | `ae5a420e78579a9433f4ffb127b7a9062a7d948c` | `59aec6256f1824d8c5cd7de92b7c25691132cce9` |
| Fix PR | #319 | #318 |
| Fix merge | `51e9e56d55` | `31133f3142` |
| Hexes backport (maintainer decision) | #320, merge `27dd279443` | — |

- **Seed and sample.** Seed `2026111213`. 70 samples in 7 categories, 10 each, with 5 ordered reserves per category. No samples were voided or redrawn.
- **Categories and pool sizes:**

  | Category | Content | Pool |
  |---|---|---:|
  | R4-1 | item and artefact descriptions | 292 |
  | R4-2 | spell descriptions and effects | 577 |
  | R4-3 | monster descriptions and casting | 682 |
  | R4-4 | god interaction | 224 |
  | R4-5 | tutorial and help long text | 75 |
  | R4-6 | environment events | 103 |
  | R4-7 | other dynamic feedback | 107 |

  The categories were chosen from the coverage matrix of the earlier rounds (`coverage_r4.md`).
- **Exclusions.** Keys from rounds 1–3, the D-C-096 probes, and keys fixed in #299–#316 are excluded. The frozen exclusion inputs are listed in `inputs/*.provenance.json`; each one points to a file in an existing archive at a fixed commit.
- **Line applicability.** 63 samples are the same on both lines, 6 have diverged, and 1 exists only on stable.
- **Reconstruction.** 41 samples are static, 7 are parameter reconstructions, and 22 need runtime or layout output. Those 22 are player check points and are not counted as verified.

## Reviewers and adjudication

There were two independent lanes. Both resolved terminology context (glossary SHA-256 `fb814f3252f2…`), so this was a contextual review, not a blind one.

| Lane | Model | Seed | ok | readability | objective error | insufficient evidence |
|---|---|---:|---:|---:|---:|---:|
| 1 | Opus 5.5 | 1401 | 60 | 8 | 1 | 1 |
| 2 | GPT-6.1 Sol | 2502 | 64 | 2 | 4 | 0 |

The host adjudicated against the source code and the catalog, not by model vote. Of the 70 samples:

- **Confirmed:** 3 samples, 3 findings, 3 defect points.
  - **R4-7-10 (stable):** the wall sizzle and grind sounds were bare literals, so they displayed in English. Now wrapped in `T_`, as on trunk.
  - **R4-3-06 (both lines):** the starflower description omitted "lashing". It now reads 挥舞不休的藤蔓和触须.
  - **R4-4-04 (both lines):** the Wu Jian powers description inverted the action relation. It now reads 无间门派的门徒学会在战斗中走位时施展三种武术…, using the glossary entity name 无间门派.
- **Rejected:** 1 (R4-1-02, see the post-disposition below).
- **Pending:** 1 (R4-4-05, deprecated-form altar actions; needs evidence that those forms are still reachable).
- **Advisory, not fixed:** 9.

The result does not extrapolate to an error rate for the whole catalogue.

## Host corrections

- **R4-4-04, draft wording.** The first adjudication draft proposed 议会门徒. The maintainer questioned this, and it was withdrawn before any candidate used it. Both lines' glossaries define the Wu Jian Council as 无间门派, and trunk D-C-111 defines The Council as 无间门派. The writer judged dropping "of the Council" to be an acceptable ellipsis of a known subject; the final text names the sect explicitly anyway. See `adjudication.json` → `host_corrections`.

## Post-disposition: Hexes

- **What was rejected.** R4-1-02 (this round) and C3-01 (round 2) were rejected at their frozen baselines, because stable's glossary then defined Hexes as 诅咒系.
- **What changed afterwards.** The maintainer then decided that stable adopts trunk D-C-110 (Hexes → 妖术系). This was done in #320:
  - 43 consumer entries were reviewed: 35 changed, 8 kept.
  - Random book names: 4 changed, 97 kept.
  - Ordinary curse, Maledictor, Maledictions and the `curses,` property are kept.
  - `get_job_by_name` also accepts the old display name 诅咒射手, so old saves and score files still match.
- **How it is recorded.** This is a later change of terminology policy. The earlier rejections were not errors at the time. The frozen samples and the original reviews are unchanged. See `adjudication.json` → `post_disposition`.

## Files

- `adjudication.json`: final verdicts, host corrections, the delivery record and the post-disposition.
- `samples_r4.json`, `selection_log_r4.json`, `coverage_r4.md`: the frozen sample and the selection record. `verification_r4.json` records their SHA-256 values. Pools and lane inputs (about 18 MB) are not committed.
- `inputs/`: provenance records of the exclusion sets.
- `outputs/lane{1,2}/`: the raw reviewer outputs.
- `fix/`: the delivery reports for both PRs and the independent review (sections A, B and C).
- `scripts/`: the generators.
  1. Run `build_inventory_r4.py --repo <repo> --out <dir>`.
  2. Run `finish_r4.py --out <dir>`.
  3. Run `validate_r4.py --out <dir>`.

  Always pass `--out` a directory outside this archive. Otherwise the scripts overwrite the frozen files here.

## Normalisation

Some archived files differ from the working copies:

- In `outputs/*/review_notes.md` and `fix/`, absolute working paths were replaced with `<r4-work>/` or `<work>/`.
- Trailing whitespace was stripped to satisfy the repository whitespace check.

`samples_r4.json`, `selection_log_r4.json`, `coverage_r4.md` and both `review_output.json` files are byte-identical to the working copies.

## Not performed

No local gameplay or screenshot acceptance was performed. Test players verify after release; the check points are in `fix/fix-delivery.txt` and `fix/hexes-delivery.txt`.
