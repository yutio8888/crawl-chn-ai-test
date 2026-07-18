# Agent Routing and Ownership

This is the runtime-neutral routing authority. Runtime adapters define only how
to invoke these roles.

## Roles

| Role | Primary responsibility | Does not own |
|---|---|---|
| `zh-translator` | Chinese wording, semantic parity, terminology, translation assets | C++ implementation or build logic |
| `crawl-coder` | C++/Lua/build changes, code-side i18n, TextDB loader/schema and structural repairs | Independent Chinese terminology decisions |
| `translation-reviewer` | EN/ZH accuracy, completeness, naturalness, glossary use, voice | Runtime safety and implementation approval |
| `zh-code-reviewer` | Runtime safety, protocol/display separation, formats, TextDB structure, scanner triage | Stylistic preference or character voice |
| `ocr` | Verbatim text extraction from screenshots or images | Translation, interpretation, or file edits |
| read-only explorer | Search, call-chain tracing, scope discovery | File edits |

Translation-asset writer rules are normative in
`.agents/policies/asset-ownership.md`. Reviewer boundaries and readiness states
are normative in `.agents/policies/review-contract.md`.

## Routing

- Direct translation or terminology work → `zh-translator`.
- C++, Lua, Makefile, build failure, loader/schema, or code-side `T_()` change →
  `crawl-coder`.
- Structural repair to a ZH TextDB file → `crawl-coder` only when it is the
  explicitly assigned sole writer; otherwise route the asset to
  `zh-translator`.
- Translation quality or terminology review → `translation-reviewer`.
- Code review, protocol/display audit, format/database integrity, or i18n bug
  root-cause review → `zh-code-reviewer`.
- Screenshot/image text extraction → `ocr`; pass the extracted text to the
  appropriate translator or reviewer in a later phase.
- Read-only search → the runtime's explorer.
- A reported translation bug spanning analysis, assets, code, and review → the
  `translation-pipeline` skill.

For every translation, i18n implementation, or review route, run
`context_resolve.sh` first and attach its complete output.

## Full Pipeline

The supported phases are:

```text
Analyze → Plan → Review Plan → Execute Translation Assets
→ Execute Code → Commit/Clean Boundary → review_prepare.sh
→ Mechanically Routed Review → Cross-validate
→ Record Readiness → review_final_gate.sh → Report
```

Reviewer routing comes only from `classify_reviewers.py` for the exact prepared
target/candidate boundary. Depending on the diff, zero, one, or both domain
reviewers may be required. Do not hard-code a three-reviewer or always-two-
reviewer pipeline.

Workflow DSL files may automate these phases only in a compatible hosted
runner. Without one, the orchestrator reproduces the same phases using normal
runtime agent calls; it does not execute the DSL file with Node.js.

## Fallback

Simple Git operations, quick questions, and planning can be handled inline.
When a specialized role is unavailable, handle the task inline under the same
policy and ownership boundaries rather than inventing a different workflow.
