# verification-authoring-v1

This policy applies when an agent writes or reviews a validator, scanner,
deployment check, parser-facing test, or other verification control.

- Enumerate the complete production artifact and its invariants before writing
  the check. Counts alone never prove identity, membership, uniqueness, order,
  content, conservation, or rejection of unknown data.
- Match production semantics for the parser, working directory,
  initialization, locale, environment, and compile/runtime options. Prefer the
  production helper or entry point. If a test must reimplement semantics,
  document the difference and cover it with a strict end-to-end check.
- Exercise the real construction, lookup, fallback, or deployment path. A
  relaxed helper test is insufficient unless a stricter end-to-end test covers
  the behaviour it omits.
- Fail closed when required input is missing, parsing is incomplete, an unknown
  field or state appears, or the complete invariant cannot be evaluated. Expose
  the failure through the validator's existing interface, normally a non-zero
  exit or an existing structured unresolved result. This requirement does not
  introduce a new result protocol, parser, persistent state, distributed
  coordination, recovery mechanism, or general compiler.
- Give every invariant a passing fixture and a minimal negative mutation that
  breaks only that invariant and must be rejected.
- Preserve raw tool evidence. Report the exact command, exit code, blocking
  failure count, relevant warnings, and the reason a failure is or is not
  actionable.

Reviewers reject checks that validate only source tokens or a convenient subset
when the production consumer observes a larger effective artifact.
