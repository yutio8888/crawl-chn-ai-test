# verification-authoring-v1

Apply this policy when writing or reviewing a validator, scanner, deployment
check, or parser-facing test. Cover the behavior the tool claims to guarantee
and risks introduced by the change, using existing tests and interfaces.

- Identify relevant artifacts, consumer semantics, and invariants. Counts alone
  do not prove identity, membership, uniqueness, order, or content when the
  check claims those guarantees.
- Prefer production helpers and realistic inputs. A focused unit test may
  reuse existing integration coverage; add end-to-end coverage only when a
  changed construction, lookup, fallback, or deployment boundary needs it.
  Document material differences if a fixture reimplements production behavior.
- Blocking release, protocol, and structural/parser integrity checks fail
  closed if required input is missing or their claimed invariant cannot be
  evaluated. Test new or changed guarantees with passing cases and minimal
  negative mutations. Preserve existing strict artifact-validation coverage.
- Advisory or heuristic tools may report unsupported input or incomplete
  coverage through their existing interface. They must not claim complete
  validation or a successful blocking check on that basis. Unknown states block
  only when the tool's declared contract requires rejection.
- Do not add tests that merely mirror wording or implementation details. Reuse
  existing fixtures and regression entry points; no new evidence protocol,
  persistent state, parser framework, or universal end-to-end gate is implied.
- Preserve logs for actual checks. Report commands/results and material warnings
  or gaps; detailed raw evidence can stay in the existing verification log.
