# asset-ownership-v1

Every task assigns exactly one writer to every file. Agents are not alone in
the repository: preserve existing changes, do not revert work owned by another
writer, and coordinate before touching an overlapping path.

## Default ownership

- `zh-translator` owns Chinese wording and translation assets under
  `crawl-ref/source/dat/i18n/zh/`, `crawl-ref/source/dat/database/zh/`, and
  `crawl-ref/source/dat/descript/zh/`.
- `crawl-coder` owns C++, headers, Lua integration, build files, parsers,
  database loading/schema, and code-side `T_()`/`C_()` migration.
- English/protocol/TextDB lookup keys remain English regardless of the writer.
- Reviewers are read-only and never repair findings during the readiness pass.

## Structural exception

A coder may edit an explicitly listed ZH data file for a purely structural or
mechanical repair, such as a broken delimiter or loader-compatible key, only
when the orchestrator assigns that complete path to the coder and no translator
is writing it concurrently. The coder must not make independent wording or
terminology decisions under this exception.

## Mixed tasks

For a task that needs both translated assets and source changes:

1. resolve the current glossary context;
2. assign every ZH translation asset to one translator writer;
3. complete translation-asset edits first;
4. run the coder for source/build changes without reopening translator-owned
   files;
5. verify the combined worktree and review the exact committed diff.

Batch work uses the same ownership model. Parallel analysis is allowed, but
translation assets are written sequentially by their single owner.
