---
name: batch-translation-review
description: Audit a finite, enumerable DCSS Chinese translation collection with a frozen inventory, one evidence-backed decision per identity, dependency-aware batching, safe sequential landing, and proof of complete coverage. Use when a user asks to review an entire category or series such as all spell, ability, item, monster, status, or related description translations, especially when the result must include per-entry conclusions or batched edits. Do not use for one wording question, one reported translation bug, or formal readiness review of an already prepared candidate.
---

# Batch Translation Review

Use this Skill to audit a complete translation collection without omissions,
duplicate decisions, or inconsistent changes across related entries. Keep
domain facts in the current inventory, glossary, decisions, and source files;
never copy a completed audit's counts, hashes, paths, or translations here.

## Load Current Authority

1. Load `$dcss-translation-context` with task type `review` and the actual
   collection files.
2. Read the complete resolver output and retain its glossary SHA-256.
3. Read the domain naming rules, existing decisions, and any current inventory
   tool or plan relevant to the collection.
4. Route a single reported bug to `$translation-pipeline` instead. Route a
   simple wording judgment directly to `translation-reviewer`.

## Freeze the Acceptance Boundary

Before judging wording:

1. Identify the production source of truth and the stable identity for each
   member.
2. Generate a deterministic, read-only inventory with the repository's
   existing domain tool. Prefer an independently maintained identity source to
   prove completeness and uniqueness.
3. Record the baseline, inventory digest, glossary digest, input-file digests,
   lifecycle categories, and explicit exclusions.
4. Require every inventory identity to have exactly one evidence card and one
   terminal conclusion.
5. Refuse to claim a full audit when the collection cannot be enumerated
   reliably. If implementation is authorized, build or repair the smallest
   read-only inventory mechanism first under the matching code ownership and
   verification policy; otherwise report the missing mechanism as a blocker.

Do not hard-code expected counts or infer historical behavior from a current
entity with a similar name. Regenerate the inventory when its source set
changes.

## Partition by Shared Dependencies

Review entries in an order that exposes consistency constraints:

1. calibration groups with existing authoritative decisions;
2. shared lexical roots and grammatical structures;
3. shared proper names;
4. shared entities, elements, statuses, and mechanics;
5. entries without meaningful dependencies.

Include low-exposure, internal, removed, and compatibility entries when they
belong to the frozen inventory. Keep lifecycle categories explicit. Review
every member of a dependency group before landing any rename from that group.

## Build One Evidence Card per Identity

Collect evidence read-only. Use `not applicable` explicitly rather than
silently omitting a field:

```text
Identity:
Lifecycle:
English source name:
Current Chinese name:
Metadata and display context:
Producer, consumer, and user:
English source meaning:
Actual effect or behavior:
Target, scope, conditions, exceptions, and consequences:
English description:
Chinese description semantic parity:
Shared dependency group:
Current glossary and decision authority:
Conclusion:
Proposed translation:
Rejected alternatives:
Evidence locations:
Confidence:
Deferred follow-up:
```

Inspect implementation or data behavior whenever the displayed name or
description promises a game effect. Do not let the English title alone
override current behavior, and do not let implementation details erase
meaning that the English description explicitly communicates.

Use these default conclusions:

- `keep`
- `adjust`
- `retranslate`
- `defer terminology`
- `defer implementation`

Treat `insufficient evidence` as non-terminal. Convert it only after locating
more evidence or record an explicit deferral with its reason, preserved current
translation, owner, and re-entry trigger. A removed entry with no current
behavior normally requires `defer terminology; review if restored`, not a
speculative rename.

## Reuse and Invalidate Evidence Safely

Parallelize read-only discovery when useful, but keep reviewers read-only.
Reuse an evidence card only when its identity, English source, Chinese source,
behavioral evidence, lifecycle, glossary authority, and relevant decisions are
unchanged. Record what was reused and why.

Invalidate the affected cards when any dependency changes. Regenerate the
inventory after a membership change, then prove which unaffected cards remain
valid. Resolve cross-entry conflicts only after the complete dependency group
has been inspected.

## Land Coherent Batches

Stop after the evidence and result report when the user requested review only.
Land changes only when the request also authorizes translation or code edits.

Follow `.agents/policies/asset-ownership.md` and
`.agents/policies/translation-integrity.md`:

1. Assign exactly one writer to every file.
2. Let one `zh-translator` update Chinese translation assets sequentially.
3. Separate code support into a later `crawl-coder` phase without reopening
   translator-owned files.
4. Update affected descriptions, related display terms, glossary entries,
   exported glossary artifacts, and durable decisions in the same coherent
   batch.
5. Synchronize glossary and decision authority before verification.
6. Run the single matching development profile after each complete dependency
   group or practical coherent batch, not after every entry.
7. Preserve the raw report and explain failures. Record a failed attempt when a
   stale glossary, structural issue, or other real defect requires a retry.

Do not run the final review profile after each batch and do not create a new
readiness schema, ledger, or final-gate substitute.

## Prove Completion

Before preparing the candidate, prove all of the following mechanically where
possible:

- inventory identities are complete and unique;
- reviewed identities are complete and unique;
- inventory and reviewed identity sets are equal in both directions;
- every identity has one terminal conclusion;
- every deferral has a reason and re-entry trigger;
- every completed dependency group has consistent terminology;
- translation assets, glossary exports, decisions, and result records agree.

When the user authorizes persisted task artifacts, keep them distinct:

- the plan records the frozen boundary, ordering, progress, and evidence entry
  points;
- the result record stores evidence cards and decisions;
- the glossary and decision log remain terminology authority;
- a change summary is derived from the final diff and does not replace evidence.

## Use Existing Final Review

After landing all accepted batches, create one clean committed candidate. Use
the repository's existing `review_prepare.sh`, mechanical reviewer routing,
immutable readiness records, and single `review_final_gate.sh` run exactly as
defined by `.agents/policies/review-contract.md`.

Report the baseline and candidate identities, inventory and glossary digests,
coverage equality, conclusion counts, changed translations and descriptions,
deferred items, development verification, routed readiness, and final-gate
status.
