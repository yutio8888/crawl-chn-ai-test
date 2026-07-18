export const meta = {
  name: 'translation-fix-pipeline',
  description: '翻译问题完整修复流程：分析→方案→审查→执行→审核→交叉验证→报告。由 translation-pipeline skill 驱动。',
  phases: [
    { title: 'Analyze', detail: '根因分析：定位未翻译文本的类型、来源和影响范围' },
    { title: 'Plan', detail: '制定修复方案：涉及文件、修改策略、风险评估' },
    { title: 'Review Plan', detail: '方案审核闸门：不通过则回退修订（最多3轮）' },
    { title: 'Execute', detail: '顺序执行：zh-translator 独占翻译资产，crawl-coder 仅改代码' },
    { title: 'Prepare Review Bundle', detail: '提交边界：要求两端 clean，并由 target checkout 创建不可变 bundle' },
    { title: 'Review', detail: '机械路由审核：按文件选择代码/翻译 reviewer，并检查术语一致性' },
    { title: 'Cross-validate', detail: '交叉验证：全部校验脚本 + 遗漏检测 + 副作用' },
    { title: 'Seal Final Evidence', detail: '持久化 readiness，并由 target checkout 独占运行一次 final gate' },
    { title: 'Report', detail: '最终报告：汇总结果 + 合入建议' },
  ],
}

const ISSUE = args?.description || '未提供问题描述'
const ISSUE_FILE = args?.issueFile || null
const TARGET_ROOT = args?.targetRoot || null
const TARGET_BRANCH = args?.targetBranch || null
const CANDIDATE_BRANCH = args?.candidateBranch || null

// ── Structured Output Schemas ───────────────────────────

const ANALYSIS_SCHEMA = {
  type: 'object',
  properties: {
    category: { type: 'string', enum: ['missing_t', 'wrong_translation', 'protocol_leak', 'textdb_missing', 'format_error', 'type_ii_wrapper', 'other'] },
    summary: { type: 'string' },
    rootCause: { type: 'string' },
    affectedFiles: { type: 'array', items: { type: 'string' } },
    translationType: { type: 'string', enum: ['I', 'II', 'III', 'IV', 'V'] },
    severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
  },
  required: ['category', 'summary', 'rootCause', 'affectedFiles', 'translationType'],
}

const PLAN_SCHEMA = {
  type: 'object',
  properties: {
    approach: { type: 'string' },
    codeChanges: { type: 'array', items: { type: 'object', properties: {
      file: { type: 'string' }, change: { type: 'string' }, reason: { type: 'string' },
    } } },
    translationsNeeded: { type: 'array', items: { type: 'object', properties: {
      english: { type: 'string' }, context: { type: 'string' },
    } } },
    risks: { type: 'array', items: { type: 'string' } },
  },
  required: ['approach', 'codeChanges', 'translationsNeeded'],
}

const REVIEW_PLAN_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['approved', 'changes_requested', 'rejected'] },
    issues: { type: 'array', items: { type: 'object', properties: {
      severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
      description: { type: 'string' }, suggestion: { type: 'string' },
    } } },
    summary: { type: 'string' },
  },
  required: ['verdict', 'issues'],
}

const CODE_RESULT_SCHEMA = {
  type: 'object',
  properties: {
    filesModified: { type: 'array', items: { type: 'string' } },
    changesSummary: { type: 'string' },
    compileStatus: { type: 'string', enum: ['pass', 'fail', 'not_attempted'] },
    verificationStatus: { type: 'string', enum: ['pass', 'fail', 'not_attempted'] },
  },
  required: ['filesModified', 'changesSummary', 'compileStatus', 'verificationStatus'],
}

const TRANS_RESULT_SCHEMA = {
  type: 'object',
  properties: {
    entriesAdded: { type: 'number' },
    entriesModified: { type: 'number' },
    verificationStatus: { type: 'string', enum: ['pass', 'fail', 'not_attempted'] },
  },
  required: ['entriesAdded', 'entriesModified', 'verificationStatus'],
}

const CODE_FINDING_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    id: { type: 'string', pattern: '^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$' },
    severity: { type: 'string', enum: ['blocker', 'needs_fix', 'suggestion'] },
    file: { type: 'string', minLength: 1, maxLength: 512 },
    line: { type: 'integer', minimum: 1, maximum: 10000000 },
    evidence: { type: 'string', minLength: 1, maxLength: 4000 },
    impact: { type: 'string', minLength: 1, maxLength: 4000 },
    fix: { type: 'string', minLength: 1, maxLength: 4000 },
  },
  required: ['id', 'severity', 'file', 'line', 'evidence', 'impact', 'fix'],
}

const TRANS_FINDING_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    ...CODE_FINDING_SCHEMA.properties,
    english: { type: 'string', minLength: 1, maxLength: 4000 },
    chinese: { type: 'string', minLength: 1, maxLength: 4000 },
  },
  required: [...CODE_FINDING_SCHEMA.required, 'english', 'chinese'],
}

const CODE_REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    findings: { type: 'array', maxItems: 200, items: CODE_FINDING_SCHEMA },
    summary: { type: 'string' },
    glossarySha256: { type: 'string', pattern: '^[0-9a-f]{64}$' },
  },
  required: ['findings', 'glossarySha256'],
}

const TRANS_REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    findings: { type: 'array', maxItems: 200, items: TRANS_FINDING_SCHEMA },
    summary: { type: 'string' },
    glossarySha256: { type: 'string', pattern: '^[0-9a-f]{64}$' },
  },
  required: ['findings', 'glossarySha256'],
}

const validateReviewFindings = (kind, result, expectedGlossarySha256) => {
  if (result.glossarySha256 !== expectedGlossarySha256)
    throw new Error(`${kind} reviewer glossary SHA-256 does not match the bundle`)
  if (!Array.isArray(result.findings) || result.findings.length > 200)
    throw new Error(`${kind} reviewer findings must be an array of at most 200 items`)
  const translation = kind === 'translation'
  const fields = ['id', 'severity', 'file', 'line', 'evidence', 'impact', 'fix']
    .concat(translation ? ['english', 'chinese'] : []).sort()
  const ids = new Set()
  const text = (value, limit, label) => {
    if (typeof value !== 'string' || !value || value.includes('\0') || [...value].length > limit)
      throw new Error(`${kind} reviewer ${label} is invalid`)
  }
  for (const [index, finding] of result.findings.entries()) {
    if (!finding || typeof finding !== 'object' || Array.isArray(finding)
        || JSON.stringify(Object.keys(finding).sort()) !== JSON.stringify(fields))
      throw new Error(`${kind} reviewer finding ${index} fields are invalid`)
    if (!/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$/.test(finding.id) || ids.has(finding.id))
      throw new Error(`${kind} reviewer finding ${index} id is invalid or duplicated`)
    ids.add(finding.id)
    if (!['blocker', 'needs_fix', 'suggestion'].includes(finding.severity))
      throw new Error(`${kind} reviewer finding ${index} severity is invalid`)
    text(finding.file, 512, `finding ${index} file`)
    const pathParts = finding.file.split('/')
    if (finding.file.startsWith('/') || pathParts.some(part => !part || part === '.' || part === '..'))
      throw new Error(`${kind} reviewer finding ${index} file is not a normalized relative path`)
    if (!Number.isInteger(finding.line) || finding.line < 1 || finding.line > 10000000)
      throw new Error(`${kind} reviewer finding ${index} line is invalid`)
    for (const field of ['evidence', 'impact', 'fix'])
      text(finding[field], 4000, `finding ${index} ${field}`)
    if (translation)
      for (const field of ['english', 'chinese'])
        text(finding[field], 4000, `finding ${index} ${field}`)
  }
  return result.findings
}

const CROSS_VALIDATE_SCHEMA = {
  type: 'object',
  properties: {
    passed: { type: 'boolean' },
    missedItems: { type: 'array', items: { type: 'string' } },
    sideEffects: { type: 'array', items: { type: 'string' } },
  },
  required: ['passed'],
}

const REVIEW_BOUNDARY_SCHEMA = {
  type: 'object',
  properties: {
    prepared: { type: 'boolean' },
    bundle_id: { type: 'string' },
    bundle_path: { type: 'string' },
    target_head: { type: 'string' },
    candidate_head: { type: 'string' },
    glossary_sha256: { type: 'string' },
    bundle_sha256: { type: 'string' },
    routing_sha256: { type: 'string' },
    routing: { type: 'object' },
    error: { type: 'string' },
  },
  required: ['prepared'],
}

const EVIDENCE_RESULT_SCHEMA = {
  type: 'object',
  properties: {
    completed: { type: 'boolean' },
    state: { type: 'string' },
    exitCode: { type: 'number' },
    recordedReviewers: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
  },
  required: ['completed', 'state', 'exitCode'],
}

// ── Phase 1: Analyze ────────────────────────────────────

phase('Analyze')
const analysis = await agent(
  `Analyze this DCSS Chinese translation issue to find the root cause.

Issue: ${ISSUE}
${ISSUE_FILE ? 'Tracking file: ' + ISSUE_FILE : ''}

Steps:
1. grep the codebase for the reported English text to locate the source
2. Read the surrounding code to understand how the text is displayed
3. Classify using DCSS Translation System Architecture (Type I-V):
   I = literal T_("string") missing | II = function wrapper issue
   III = runtime T_(variable) without source.txt | IV = TextDB descriptor missing
   V = protocol/internal (should stay English, not a bug)
4. Determine severity: blocker (crash/fully English UI), major, minor

Reference docs/translation-architecture.md.`,
  { label: 'analyze', schema: ANALYSIS_SCHEMA }
)

if (!analysis) {
  log('FAIL: Analysis returned no result')
  return { error: 'analysis_failed', phase: 'Analyze' }
}

log('Type ' + analysis.translationType + ' | ' + analysis.category + ' | ' + analysis.summary)
log('Root cause: ' + analysis.rootCause)
log('Files: ' + analysis.affectedFiles.join(', '))

// ── Phase 2: Plan ───────────────────────────────────────

phase('Plan')
let plan = await agent(
  `Create a fix plan based on this analysis:

${JSON.stringify(analysis, null, 2)}

Issue: ${ISSUE}

Design the minimal, correct fix:
- Type I: wrap with T_() + add source.txt entry
- Type II: fix the wrapper function's internal T_() call
- Type III: add source.txt entries, run audit_data_i18n.py to verify
- Type IV: add/update entry in zh/*.txt database file (English key, Chinese value)
- Type V: revert to English — this is NOT a bug

For each code change: file path, what to change, why.
For each translation: English text and context.
Follow .agents/policies/i18n-safety.md: mprf_p for positional %n$s formats, no .c_str() on const char*, no protocol translation.`,
  { label: 'plan', schema: PLAN_SCHEMA }
)

if (!plan) {
  log('FAIL: Plan returned no result')
  return { error: 'plan_failed', phase: 'Plan', analysis }
}

log('Approach: ' + plan.approach)
log('Changes: ' + plan.codeChanges.length + ' code, ' + plan.translationsNeeded.length + ' trans, ' + plan.risks.length + ' risks')

// ── Phase 3: Review Plan (gate with retry) ──────────────

phase('Review Plan')
let planReview = await agent(
  `Review this fix plan. Be a skeptical gatekeeper.

Analysis: ${JSON.stringify(analysis)}
Plan: ${JSON.stringify(plan)}

Check:
1. Translation type classification correct?
2. ALL affected files identified? (grep to verify)
3. Approach minimal — only changes what's needed?
4. Format string risks (%s count, arg order)?
5. Project conventions followed (AGENTS.md and .agents/policies/)?
6. Missing edge cases or side effects?

Verdict: approved (proceed) | changes_requested (revise) | rejected (abort)`,
  { label: 'review-plan', schema: REVIEW_PLAN_SCHEMA }
)

if (!planReview) {
  log('FAIL: Plan review returned no result')
  return { error: 'plan_review_failed', phase: 'Review Plan', analysis, plan }
}

let planIterations = 0
while (planReview.verdict !== 'approved' && planIterations < 3) {
  planIterations++
  log('Plan review: ' + planReview.verdict + ' (round ' + planIterations + '/3)')

  if (planReview.verdict === 'rejected') {
    log('FAIL: Plan rejected — ' + (planReview.issues?.[0]?.description || 'fundamental'))
    return { error: 'plan_rejected', phase: 'Review Plan', analysis, plan, planReview }
  }

  plan = await agent(
    `Revise the plan. Address EVERY issue from the review.

Review issues: ${JSON.stringify(planReview.issues)}
Current plan: ${JSON.stringify(plan)}

Explain how each revision addresses the feedback.`,
    { label: 'revise-plan-r' + planIterations, schema: PLAN_SCHEMA }
  )
  if (!plan) { log('FAIL: Revision failed'); return { error: 'plan_revision_failed' } }

  planReview = await agent(
    `Re-review. Were ALL previous issues addressed?

Previous issues: ${JSON.stringify(planReview.issues)}
Revised plan: ${JSON.stringify(plan)}`,
    { label: 'rereview-plan-r' + planIterations, schema: REVIEW_PLAN_SCHEMA }
  )
  if (!planReview) { log('FAIL: Re-review failed'); return { error: 'plan_rereview_failed' } }
}

if (planReview.verdict !== 'approved') {
  log('FAIL: Plan not approved after max revisions')
  return { error: 'plan_not_approved', phase: 'Review Plan', planIterations, planReview }
}
log('Plan approved after ' + planIterations + ' revision(s)')

// ── Phase 4: Execute (single writer per asset) ──────────

phase('Execute')

// Translation assets have one owner. Run translation first, then code in the
// same worktree so reviewers and cross-validation see the complete result.
const translationResult = await agent(
    `Add Chinese translations for these entries.

Translations needed: ${JSON.stringify(plan.translationsNeeded)}
Context: ${ISSUE}
${ISSUE_FILE ? 'Issue file: ' + ISSUE_FILE : ''}

Steps:
1. Run context_resolve.sh with --task-type translate for the exact target files
2. Apply the returned current glossary context and retain its SHA-256
3. For each entry, grep source.txt first to avoid duplicates
4. You exclusively own source.txt and other zh/*.txt/TextDB assets for this run
5. Run: bash .claude/scripts/verify_zh.sh --profile translation
6. Return verificationStatus=pass only when that profile exits 0; otherwise return fail
7. If you changed translation assets, commit only those owned files after the
   profile passes, follow the active runtime's commit-trailer policy, and leave
   the worktree clean for immutable review.

Translation rules:
- Preserve literal \\n, \\t, \\r, %%%%, %N$s, <tag>, and @keyword@ tokens
- No verb conjugation (remove conj_verb calls)
- Add 了 after verbs for completed actions
- Adverbs BEFORE verbs in Chinese
- No articles (the/a/an), no plural forms
- Format specifiers (%s, %d) must match argument count
- TextDB (Type IV): English key, Chinese value in zh/*.txt`,
    { agentType: 'zh-translator', label: 'translate', schema: TRANS_RESULT_SCHEMA }
)

if (translationResult?.verificationStatus !== 'pass') {
  log('Translation verification failed; code execution is blocked.')
  return { error: 'translation_execution_failed', phase: 'Execute', translationResult }
}

const codeResult = await agent(
    `Implement code changes for this translation fix.

Code changes: ${JSON.stringify(plan.codeChanges)}
Analysis type: ${analysis.translationType}

Steps:
1. Run context_resolve.sh with --task-type code for the exact target files
2. Apply the returned current glossary context and retain its SHA-256
3. Make each code change as specified in the plan
4. Run make -j4 to verify compilation
5. If compilation fails, diagnose, fix, recompile — iterate until pass
6. Run: bash .claude/scripts/verify_zh.sh --profile code
7. Return verificationStatus=pass only when that profile exits 0; otherwise return fail
8. If you changed code, commit only your owned files after the profile passes,
   follow the active runtime's commit-trailer policy, and leave the worktree
   clean for immutable review.

CRITICAL rules (from .agents/policies/i18n-safety.md and asset-ownership.md):
- Use mprf_p (not mprf) for positional format strings
- Never add .c_str() on const char* return values
- Never translate protocol/internal strings
- Never call conj_verb() on Chinese strings
- Do not edit source.txt or any zh/*.txt/TextDB asset; zh-translator owns them
- Type III: add T_(variable) in code; the preceding translation step owns its source.txt entry
- Type V: report that text should remain English (not a bug)`,
    { agentType: 'crawl-coder', label: 'code', schema: CODE_RESULT_SCHEMA }
)

if (codeResult?.compileStatus !== 'pass'
    || codeResult?.verificationStatus !== 'pass') {
  log('Code compilation or verification failed; review is blocked.')
  return { error: 'code_execution_failed', phase: 'Execute', codeResult, translationResult }
}

if (codeResult && codeResult.compileStatus === 'pass') {
  log('Code: compile OK | ' + codeResult.changesSummary)
} else {
  log('Code: ' + (codeResult?.compileStatus || 'skipped'))
}

if (translationResult) {
  log('Translation: +' + translationResult.entriesAdded + ' added, ' + (translationResult.entriesModified || 0) + ' modified')
} else {
  log('Translation: skipped')
}

// ── Phase 5: Prepare immutable review boundary ─────────

phase('Prepare Review Bundle')

if (!TARGET_ROOT || !TARGET_BRANCH || !CANDIDATE_BRANCH) {
  log('FAIL: targetRoot, targetBranch, and candidateBranch are required before review.')
  return {
    error: 'review_boundary_arguments_required',
    phase: 'Prepare Review Bundle',
    required: ['targetRoot', 'targetBranch', 'candidateBranch'],
  }
}

const reviewBoundary = await agent(
  `Prepare the immutable schema-v4 review boundary. This is a mechanical Git
and evidence task; do not edit source, translation, policy, or documentation files.

Target checkout: ${TARGET_ROOT}
Target branch: ${TARGET_BRANCH}
Candidate branch: ${CANDIDATE_BRANCH}

1. Confirm the target checkout and candidate linked worktree are clean and
   their HEADs exactly match the named branches. Do not commit or repair a dirty tree.
2. From the target checkout run exactly:
   bash .claude/scripts/review_prepare.sh ${CANDIDATE_BRANCH} ${TARGET_BRANCH}
3. Parse the command's canonical JSON. Return prepared=true only when it exits
   zero, and copy bundle_id, bundle_path, target_head, candidate_head,
   glossary_sha256, and the complete routing object exactly from that output.
4. On any failure return prepared=false with the exact diagnostic.`,
  { label: 'prepare-review-bundle', schema: REVIEW_BOUNDARY_SCHEMA }
)

if (!reviewBoundary?.prepared || !reviewBoundary?.bundle_id
    || !reviewBoundary?.routing) {
  log('FAIL: Immutable review boundary was not prepared: ' + (reviewBoundary?.error || 'unknown error'))
  return {
    error: 'review_boundary_required',
    phase: 'Prepare Review Bundle',
    reviewBoundary,
  }
}

const REVIEW_ROUTING = reviewBoundary.routing

// ── Phase 6: Review (machine-routed) ────────────────────

phase('Review')

const routedReviewers = REVIEW_ROUTING?.reviewers
const routingMatrix = {
  none: [], code: ['zh-code-reviewer'], translation: ['translation-reviewer'],
  mixed: ['zh-code-reviewer', 'translation-reviewer'],
}
const expectedReviewers = routingMatrix[REVIEW_ROUTING?.classification]
if (REVIEW_ROUTING?.schema_version !== 1
    || !Array.isArray(routedReviewers)
    || !expectedReviewers
    || JSON.stringify(routedReviewers) !== JSON.stringify(expectedReviewers)) {
  log('FAIL: review bundle contains invalid mechanical routing.')
  return { error: 'review_routing_invalid', phase: 'Review', reviewBoundary }
}

log('Review routing: ' + (REVIEW_ROUTING.classification || '?') + ' → '
  + (routedReviewers.length ? routedReviewers.join(', ') : 'no reviewers'))

const reviewJobs = []
if (routedReviewers.includes('zh-code-reviewer')) {
  reviewJobs.push(async () => ({ kind: 'code', result: await agent(
    `Review the code changes for this translation fix.

First resolve the current glossary with context_resolve.sh --task-type review.
Inspect bundle ${reviewBoundary.bundle_id}, its exact
${reviewBoundary.target_head}..${reviewBoundary.candidate_head} committed diff,
and the existing development-profile and targeted-test logs. Fail No-Go if the
bundle, heads, routing, glossary hash, or clean-worktree precondition cannot be verified.
Do not run verify_zh.sh --profile review; the final gate owns the single full review run.

Then review the diff:
1. Protocol/display separation — any protocol keys translated?
2. T_() correctness — correct usage, no missing source.txt entries?
3. Compilation — does make -j4 pass?
4. Database integrity — %%%% parity, duplicate keys, @keyword@ refs?
5. EN mode safety — does English mode still work?

Use review-contract-v4 severities: blocker | needs_fix | suggestion. Return the
complete findings array; every finding must contain id, severity, file, line,
evidence, impact, and fix. Do not return counts or a readiness verdict. Interpret
every relevant failure or warning and report the glossary SHA-256.`,
    { agentType: 'zh-code-reviewer', label: 'code-review', schema: CODE_REVIEW_SCHEMA }
  ) }))
}

if (routedReviewers.includes('translation-reviewer')) {
  reviewJobs.push(async () => ({ kind: 'translation', result: await agent(
    `Review the Chinese translation quality.

First resolve the current glossary with context_resolve.sh --task-type review.
Inspect bundle ${reviewBoundary.bundle_id}, its exact
${reviewBoundary.target_head}..${reviewBoundary.candidate_head} committed diff,
and the existing development-profile and targeted-test logs. Fail No-Go if the
bundle, heads, routing, glossary hash, or clean-worktree precondition cannot be verified.
Do not run verify_zh.sh --profile review; the final gate owns the single full review run.

Then review:
1. Semantic accuracy — ZH matches EN exactly?
2. No fabrication — no mechanics added not in EN?
3. Language quality — natural Chinese, no translationese?
4. Precision — numbers/percentages preserved?
5. Cross-reference docs/glossary.md for terminology.

Use review-contract-v4 severities: blocker | needs_fix | suggestion. Return the
complete findings array; every finding must contain id, severity, file, line,
evidence, impact, fix, english, and chinese. Do not return counts or a readiness
verdict. Interpret every relevant failure or warning and report the glossary SHA-256.`,
    { agentType: 'translation-reviewer', label: 'trans-review', schema: TRANS_REVIEW_SCHEMA }
  ) }))
}

const reviews = reviewJobs.length ? await parallel(reviewJobs) : []
const reviewResult = kind => {
  const result = reviews.find(item => item?.kind === kind)?.result || null
  if (!result) return null
  const findings = validateReviewFindings(kind, result, reviewBoundary.glossary_sha256)
  const count = severity => findings.filter(item => item.severity === severity).length
  const blockers = count('blocker')
  const needsFix = count('needs_fix')
  return { ...result, findings, blockers, needsFix, suggestions: count('suggestion'),
    readiness: blockers ? 'No-Go' : needsFix ? 'Changes Requested' : 'Ready for Final Gate' }
}
const codeReview = reviewResult('code')
const transReview = reviewResult('translation')

log([
  codeReview ? 'Code:' + codeReview.readiness + ' B' + codeReview.blockers + 'F' + codeReview.needsFix + 'S' + codeReview.suggestions : 'Code:N/A',
  transReview ? 'Trans:' + transReview.readiness + ' B' + transReview.blockers + 'F' + transReview.needsFix + 'S' + transReview.suggestions : 'Trans:N/A',
].join(' | '))

const codeRequired = (plan?.codeChanges?.length || 0) > 0
const translationRequired = (plan?.translationsNeeded?.length || 0) > 0
const executionIncomplete = (codeRequired && (codeResult?.compileStatus !== 'pass'
    || codeResult?.verificationStatus !== 'pass'))
  || (translationRequired && translationResult?.verificationStatus !== 'pass')
const reviewerIncomplete = routedReviewers.some(kind =>
  kind === 'zh-code-reviewer' ? !codeReview : !transReview)
const hasBlockers = (codeReview?.blockers > 0) || (transReview?.blockers > 0)
  || codeReview?.readiness === 'No-Go' || transReview?.readiness === 'No-Go'
const hasChangesRequested = (codeReview?.needsFix > 0) || (transReview?.needsFix > 0)
  || codeReview?.readiness === 'Changes Requested'
  || transReview?.readiness === 'Changes Requested'

// ── Phase 6: Cross-validate ─────────────────────────────

phase('Cross-validate')

const crossValidation = await agent(
  `Adversarial cross-validation. Be skeptical — assume something was missed.

Issue: ${ISSUE}
Analysis: ${JSON.stringify(analysis)}
Code result: ${JSON.stringify(codeResult)}
Translation result: ${JSON.stringify(translationResult)}
Reviews: code=${codeReview?.readiness}(B${codeReview?.blockers}) trans=${transReview?.readiness}(B${transReview?.blockers})

Perform read-only analysis and narrowly targeted checks only. Do not run the full
review profile; the final gate owns that single head-bound verification run.
Run the focused terminology ruling check:
  bash .claude/scripts/check_consistency.sh --rulings

Answer:
1. Any edge cases missed?
2. Any side effects on other features?
3. Same pattern elsewhere that also needs fixing?
4. Does EN mode still work?
5. Any format string mismatches?
6. Any DB lookup key broken?

Report everything — prefer false positives over missed issues.`,
  { label: 'cross-validate', schema: CROSS_VALIDATE_SCHEMA }
)

if (crossValidation) {
  log('Cross-validate: ' + (crossValidation.passed ? 'PASS' : 'ISSUES FOUND'))
  if (crossValidation.missedItems?.length) log('Missed: ' + crossValidation.missedItems.join('; '))
  if (crossValidation.sideEffects?.length) log('Side effects: ' + crossValidation.sideEffects.join('; '))
}

const verificationIncomplete = crossValidation?.passed !== true
const reviewFailure = executionIncomplete || reviewerIncomplete
  || verificationIncomplete || hasBlockers || hasChangesRequested

// ── Phase 7: Persist readiness + one final gate ─────────

phase('Seal Final Evidence')

let readinessEvidence = {
  completed: false, state: 'READINESS_NOT_RECORDED', exitCode: 10,
  recordedReviewers: [], summary: 'Review or cross-validation did not pass.',
}
let finalGate = {
  completed: false, state: 'FINAL_GATE_NOT_RUN', exitCode: 11,
  recordedReviewers: [], summary: 'Final gate requires persisted readiness.',
}

if (!reviewFailure && routedReviewers.length === 0) {
  readinessEvidence = {
    completed: true, state: 'READINESS_NOT_REQUIRED', exitCode: 0,
    recordedReviewers: [], summary: 'Mechanical routing requires no reviewers.',
  }
  finalGate = {
    completed: true, state: 'MERGEABLE', exitCode: 0,
    recordedReviewers: [], summary: 'No final review profile is required for an unrouted diff.',
  }
} else if (!reviewFailure) {
  readinessEvidence = await agent(
    `Persist the exact schema-v4 reviewer findings and readiness records. This is an evidence
task only; do not edit or commit repository files and do not run any verification profile.

Target checkout: ${TARGET_ROOT}
Candidate branch: ${CANDIDATE_BRANCH}
Bundle id: ${reviewBoundary.bundle_id}
Required routed reviewers: ${JSON.stringify(routedReviewers)}
Code findings: ${JSON.stringify(codeReview?.findings || [])}
Translation findings: ${JSON.stringify(transReview?.findings || [])}

1. Resolve the candidate linked-worktree path from the clean target checkout.
2. For each routed reviewer, invoke the target checkout's
   .claude/scripts/review_bundle.py record-readiness with --repo set to that
   candidate worktree, --bundle ${reviewBoundary.bundle_id}, the exact reviewer
   role, and --findings-json naming a canonical ordinary JSON file outside both
   clean Git worktrees (for example under /tmp). The file must
   contain schema, bundle_id, bundle_sha256, routing_sha256, reviewer, and the
   exact findings array. Obtain all bindings from validated bundle status; never
   invent or copy them from reviewer prose.
3. Run review_bundle.py status for the same bundle. Return completed=true only
   when every routed role was recorded and status is FINAL_GATE_REQUIRED (11)
   or FINAL_APPROVAL_REQUIRED (13). Copy the actual state/exit code and roles.
4. Never invoke review_final_gate.sh in this step.`,
    { label: 'persist-review-readiness', schema: EVIDENCE_RESULT_SCHEMA }
  )

  if (readinessEvidence?.completed) {
    finalGate = await agent(
      `Run the single schema-v4 final gate now that all required reviewers are ready.
Do not run verify_zh.sh directly, do not pass retry/recovery flags, and do not
modify source or evidence manually.

From the clean target checkout ${TARGET_ROOT}, run exactly:
  bash .claude/scripts/review_final_gate.sh ${CANDIDATE_BRANCH} ${TARGET_BRANCH}

Parse the emitted JSON and return completed=true only for MERGEABLE with exit
code 0. For any other state preserve the exact state, exit code, and diagnostic;
do not retry automatically.`,
      { label: 'run-single-final-gate', schema: EVIDENCE_RESULT_SCHEMA }
    )
  }
}

const hardFailure = reviewFailure || !readinessEvidence?.completed
  || !finalGate?.completed || finalGate?.state !== 'MERGEABLE'
const finalReadiness = hardFailure ? 'NOT_READY' : 'MERGEABLE'

// ── Phase 8: Report ─────────────────────────────────────

phase('Report')

await agent(
  `Generate the final pipeline report as clean markdown.

Issue: ${ISSUE}
Analysis: Type ${analysis?.translationType} | ${analysis?.category} | ${analysis?.summary}
Root cause: ${analysis?.rootCause}
Files: ${analysis?.affectedFiles?.join(', ')}

Plan: ${plan?.approach}
Changes: ${plan?.codeChanges?.length} code, ${plan?.translationsNeeded?.length} translations
Risks: ${plan?.risks?.join('; ')}
Plan review rounds: ${planIterations}

Code: ${codeResult?.compileStatus || 'N/A'} | ${codeResult?.changesSummary || ''}
Files: ${codeResult?.filesModified?.join(', ') || 'N/A'}
Translation: +${translationResult?.entriesAdded || 0} added, ${translationResult?.entriesModified || 0} modified

Code Review: ${codeReview?.readiness || 'N/A'} (B:${codeReview?.blockers || 0} F:${codeReview?.needsFix || 0} S:${codeReview?.suggestions || 0})
  ${codeReview?.summary || ''}
Translation Review: ${transReview?.readiness || 'N/A'} (B:${transReview?.blockers || 0} F:${transReview?.needsFix || 0} S:${transReview?.suggestions || 0})
  ${transReview?.summary || ''}
Cross-Validation: ${crossValidation?.passed ? 'PASS' : 'ISSUES'}
  Missed: ${crossValidation?.missedItems?.join('; ') || 'none'}
  Side effects: ${crossValidation?.sideEffects?.join('; ') || 'none'}

Bundle: ${reviewBoundary.bundle_id}
Readiness evidence: ${readinessEvidence?.state} (exit ${readinessEvidence?.exitCode})
Final gate: ${finalGate?.state} (exit ${finalGate?.exitCode})

Readiness: ${finalReadiness}
${finalReadiness === 'MERGEABLE' ? 'Merge gate: run review_at_merge.sh read-only, then merge the exact approved candidate OID.' : 'Do not merge. Resolve the reported state; a failed/interrupted attempt requires an explicit retry and stale residue requires explicit recovery.'}

Format as a structured markdown report with sections: Summary, Analysis, Changes Made, Review Results, Cross-Validation, Evidence, Merge Authorization.`,
  { label: 'report' }
)

return {
  analysis, plan, planReview, planIterations,
  codeResult, translationResult,
  reviewBoundary, reviewRouting: REVIEW_ROUTING,
  codeReview, transReview,
  crossValidation,
  readinessEvidence, finalGate,
  readiness: finalReadiness, hasBlockers, hasChangesRequested, hardFailure,
}
