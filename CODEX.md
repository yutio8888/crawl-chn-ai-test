# CODEX.md - Codex Runtime Overlay

This file translates the repository's OpenCode-oriented `AGENTS.md` into
instructions that are directly usable in the current Codex desktop/runtime
environment.

For canonical project knowledge, still read `AGENTS.md` first and `CLAUDE.md`
when the task touches build commands, branch discipline, testing, CJK tiles,
translation architecture, issue tracking, or commit discipline.

## Runtime Mapping

OpenCode-specific dispatch syntax is not available in this Codex environment.
Use the following equivalents instead.

| OpenCode concept | OpenCode syntax | Codex equivalent |
| --- | --- | --- |
| Project subagent | `task(subagent_type="...")` | Use available multi-agent tools if exposed through `tool_search`; otherwise handle inline with the same role-specific rules. |
| Skill | `skill(name="...")` | Read the relevant `.opencode/skills/<name>/SKILL.md` file, then execute the described workflow manually with shell/tools. |
| Workflow | `node .opencode/workflows/*.js '<json>'` | Run the same Node script from the shell when available. |
| Explore agent | `task(subagent_type="explore")` | Use `rg`, `rg --files`, `git grep`, and read-only shell/file inspection. |
| Bash command | `bash ...` | Prefer WSL commands via `wsl.exe -d Ubuntu -- bash -lc "cd /home/yutio888/projects/crawl && ..."` from Windows PowerShell when direct UNC execution is unreliable. |

## Role Routing In Codex

Use these role behaviors when OpenCode would delegate to a project agent.

### `zh-translator`

Use this behavior for:

- Translating text or files.
- Adding `T_()` entries.
- Converting hardcoded Chinese to translation entries.
- Batch i18n work.

Codex procedure:

1. Read `.opencode/skills/translation-pipeline/SKILL.md` or the relevant
   translation skill when the task is pipeline-shaped.
2. Resolve terminology context with:

   ```bash
   bash .claude/scripts/context_resolve.sh "<task>" --files <target-files>
   ```

3. Apply translation changes directly, preserving DCSS TextDB separators and
   existing terminology.
4. Run the relevant validation scripts from `CLAUDE.md` or `.claude/scripts/`.

### `crawl-coder`

Use this behavior for:

- C++ source changes.
- Code-side `T_()` migration.
- TextDB/data file changes.
- Build or compile fixes.

Codex procedure:

1. Read nearby code and existing project patterns before editing.
2. Keep changes scoped to the requested behavior.
3. Use `apply_patch` for manual edits.
4. Run focused validation or build commands appropriate to the touched files.

### `zh-code-reviewer`

Use this behavior for:

- Code review.
- `T_()` migration review.
- Protocol/display audits.
- TextDB integrity checks.
- Translation bug root-cause investigation.

Codex procedure:

1. Use code-review posture: findings first, ordered by severity.
2. Ground findings in exact file and line references.
3. Prioritize behavioral bugs, regressions, missing tests, translation-system
   violations, and protocol leakage.
4. Use scripts such as `.claude/scripts/classify_review.sh` and
   `.claude/scripts/review_at_merge.sh` when applicable.

### `translation-reviewer`

Use this behavior for:

- Translation quality review.
- Terminology consistency.
- Source/target meaning comparison.
- Character voice and style checks.

Codex procedure:

1. Compare the Chinese text against source English where available.
2. Check project terminology context before proposing changes.
3. Report quality issues separately from code or data-format issues.

### `explore`

Use this behavior for read-only code search.

Codex procedure:

1. Prefer `rg` and `rg --files`.
2. Use `git grep` when repository indexing helps.
3. Do not edit files during an exploration-only request.

## Workflow Mapping

### Single Translation Issue

OpenCode says to load `translation-pipeline`.

Codex procedure:

1. Read `.opencode/skills/translation-pipeline/SKILL.md`.
2. Run or manually follow `.opencode/workflows/translation-fix-pipeline.js`.
3. Preserve the pipeline phases:
   Analyze -> Plan -> Review Plan -> Execute -> Review -> Cross-validate ->
   Report.
4. If the workflow script is usable, invoke it as:

   ```bash
   node .opencode/workflows/translation-fix-pipeline.js '<json args>'
   ```

### Batch Translation Issues

Codex procedure:

1. Use a shared worktree unless the user requests otherwise.
2. Merge root-cause analysis and terminology context before editing.
3. Execute source/TextDB changes sequentially when conflicts are likely.
4. If the workflow script is usable, invoke it as:

   ```bash
   node .opencode/workflows/translation-batch-pipeline.js '<json args>'
   ```

## Shell And Filesystem Notes

The project path is a WSL UNC path:

```text
\\wsl$\Ubuntu\home\yutio888\projects\crawl
```

If PowerShell cannot operate directly in that UNC working directory, use WSL:

```powershell
wsl.exe -d Ubuntu -- bash -lc "cd /home/yutio888/projects/crawl && <command>"
```

When editing files manually, use Codex `apply_patch`. Do not rewrite unrelated
user changes. Do not run destructive commands such as `git reset --hard` or
recursive deletion unless the user explicitly requested them and approval is
granted.

## Commit Discipline

When Codex creates commits for this repository, include:

```text
Co-Authored-By: opencode <noreply@opencode.ai>
```

Use this trailer because the repository's current discipline accepts the
OpenCode identity for migrated agent work. If the user explicitly wants a Codex
identity later, agree on the trailer before committing.

## Practical Decision Rules

- Simple git operations, quick questions, and local planning can be handled
  inline.
- Translation work should first gather terminology context.
- Code implementation should follow local C++/TextDB patterns before inventing
  new helpers.
- Review requests should be answered as reviews, not summaries.
- Workflows that exist as `.js` files should be run through shell when possible;
  otherwise follow their phases manually.
- If a future Codex multi-agent tool is available, discover it with
  `tool_search` before emulating OpenCode `task(...)` inline.

