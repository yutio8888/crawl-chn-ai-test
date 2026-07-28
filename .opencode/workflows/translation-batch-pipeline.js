export const meta = {
  name: 'translation-batch-pipeline',
  description: '批量翻译修复流程（B′）：共享 worktree + 阶段批处理。Analyze 归并同根因 → Execute 串行落盘 → 批量审核。',
  phases: [
    { title: 'Batch Analyze', detail: '并行分析所有 issue → 归并同根因 → 建立批次术语表' },
    { title: 'Batch Plan', detail: '基于合并后的问题集制定统一修复方案' },
    { title: 'Review Plan', detail: '方案审核闸门（最多3轮修订）' },
    { title: 'Execute Sequential', detail: '两遍串行：先完成全批翻译资产，再执行全批代码修改' },
    { title: 'Prepare Review Bundle', detail: '提交边界：要求两端 clean，并由 target checkout 创建不可变 bundle' },
    { title: 'Batch Review', detail: '按文件机械路由代码/翻译 reviewer，并检查术语一致性' },
    { title: 'Cross-validate', detail: '全量校验脚本 + 遗漏检测' },
    { title: 'Seal Final Evidence', detail: '持久化 readiness，并由 target checkout 独占运行一次 final gate' },
    { title: 'Report', detail: '汇总报告：逐 issue 状态 + 整体判决' },
  ],
}

const ISSUES = args?.issues || [{ description: args?.description || '未提供问题描述' }]
const TARGET_ROOT = args?.targetRoot || null
const TARGET_BRANCH = args?.targetBranch || null
const CANDIDATE_BRANCH = args?.candidateBranch || null
log('批量处理 ' + ISSUES.length + ' 个问题')

// ── Schemas (reused from single-issue pipeline) ─────────

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

const MERGED_PLAN_SCHEMA = {
  type: 'object',
  properties: {
    approach: { type: 'string' },
    mergedGroups: { type: 'array', items: { type: 'object', properties: {
      rootCause: { type: 'string' },
      issueIndices: { type: 'array', items: { type: 'number' } },
      codeChanges: { type: 'array', items: { type: 'object', properties: {
        file: { type: 'string' }, change: { type: 'string' }, reason: { type: 'string' },
      } } },
      translationsNeeded: { type: 'array', items: { type: 'object', properties: {
        english: { type: 'string' }, context: { type: 'string' },
      } } },
    } } },
    risks: { type: 'array', items: { type: 'string' } },
    acceptanceCriteria: { type: 'array', items: { type: 'string' } },
    nonGoals: { type: 'array', items: { type: 'string' } },
    batchGlossary: { type: 'array', items: { type: 'object', properties: {
      term: { type: 'string' }, translation: { type: 'string' }, rationale: { type: 'string' },
    } } },
  },
  required: ['approach', 'mergedGroups', 'risks', 'acceptanceCriteria', 'nonGoals', 'batchGlossary'],
}

const REVIEW_PLAN_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['approved', 'changes_requested', 'rejected'] },
    issues: { type: 'array', items: { type: 'object', properties: {
      severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
      category: { type: 'string', enum: ['core_gap', 'implementation_gap', 'out_of_scope', 'design_induced'] },
      preferredAction: { type: 'string', enum: ['delete', 'reuse', 'narrow', 'add'] },
      description: { type: 'string' }, suggestion: { type: 'string' },
    }, required: ['severity', 'category', 'preferredAction', 'description', 'suggestion'] } },
  },
  required: ['verdict', 'issues'],
}

const EXEC_ITEM_SCHEMA = {
  type: 'object',
  properties: {
    groupIndex: { type: 'number' },
    code: { type: 'object', properties: {
      filesModified: { type: 'array', items: { type: 'string' } },
      compileStatus: { type: 'string', enum: ['pass', 'fail', 'not_attempted'] },
      verificationStatus: { type: 'string', enum: ['pass', 'fail', 'not_attempted'] },
      summary: { type: 'string' },
    }, required: ['filesModified', 'compileStatus', 'verificationStatus', 'summary'] },
    translation: { type: 'object', properties: {
      entriesAdded: { type: 'number' }, entriesModified: { type: 'number' },
      verificationStatus: { type: 'string', enum: ['pass', 'fail', 'not_attempted'] },
    }, required: ['entriesAdded', 'entriesModified', 'verificationStatus'] },
  },
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

const CODE_BATCH_REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    findings: { type: 'array', maxItems: 200, items: CODE_FINDING_SCHEMA },
    reviewedScope: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
    glossarySha256: { type: 'string', pattern: '^[0-9a-f]{64}$' },
  },
  required: ['findings', 'reviewedScope', 'glossarySha256'],
}

const TRANS_BATCH_REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    findings: { type: 'array', maxItems: 200, items: TRANS_FINDING_SCHEMA },
    reviewedScope: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
    glossarySha256: { type: 'string', pattern: '^[0-9a-f]{64}$' },
  },
  required: ['findings', 'reviewedScope', 'glossarySha256'],
}

const validateReviewFindings = (kind, result, expectedGlossarySha256, expectedScope) => {
  if (result.glossarySha256 !== expectedGlossarySha256)
    throw new Error(`${kind} reviewer glossary SHA-256 does not match the bundle`)
  if (!Array.isArray(result.findings) || result.findings.length > 200)
    throw new Error(`${kind} reviewer findings must be an array of at most 200 items`)
  if (JSON.stringify(result.reviewedScope) !== JSON.stringify(expectedScope))
    throw new Error(`${kind} reviewer reviewedScope must exactly equal routing.files`)
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

// ── Phase 1: Batch Analyze ─────────────────────────────

phase('Batch Analyze')

// Step 1a: Parallel analysis of all issues
log('并行分析 ' + ISSUES.length + ' 个问题...')
const analyses = await parallel(
  ISSUES.map((issue, i) => () =>
    agent(
      'Analyze this DCSS Chinese translation issue.\n' +
      '\nIssue #' + (i + 1) + ': ' + (issue.description || '未提供描述') +
      (issue.issueRef ? '\nGitHub issue: ' + issue.issueRef : '') +
      '\n\nSteps:\n' +
      '1. grep the codebase for the reported English text\n' +
      '2. Read surrounding code to understand display context\n' +
      '3. Classify: Type I (missing T_()), II (wrapper), III (runtime var), IV (TextDB), V (protocol)\n' +
      '4. Determine severity and affected files\n' +
      '\nBe precise about file paths and root cause — this feeds into batch merging.',
      { label: 'analyze-' + (i + 1), schema: ANALYSIS_SCHEMA }
    )
  )
)

const validAnalyses = analyses.filter(Boolean)
log('分析完成: ' + validAnalyses.length + '/' + ISSUES.length + ' 成功')

if (validAnalyses.length === 0) {
  log('FAIL: All analyses failed')
  return { error: 'all_analyses_failed' }
}

// Step 1b: Merge same-root-cause issues (plain JS dedup)
const groups = []
const used = new Set()

for (let i = 0; i < validAnalyses.length; i++) {
  if (used.has(i)) continue
  const group = { rootCause: validAnalyses[i].rootCause, category: validAnalyses[i].category, indices: [i] }
  used.add(i)

  // Find same root cause + same category
  for (let j = i + 1; j < validAnalyses.length; j++) {
    if (used.has(j)) continue
    if (validAnalyses[j].rootCause === group.rootCause && validAnalyses[j].category === group.category) {
      group.indices.push(j)
      used.add(j)
    }
  }
  groups.push(group)
}

log('归并: ' + validAnalyses.length + ' 个问题 → ' + groups.length + ' 个独立根因组')
for (const g of groups) {
  if (g.indices.length > 1) {
    log('  合并组: ' + g.rootCause.substring(0, 60) + '... (' + g.indices.length + ' issues)')
  }
}

// Step 1c: Build batch glossary for unified terminology
const glossary = await agent(
  'Build a batch terminology glossary for these translation issues.\n' +
  '\nMerged groups:\n' + JSON.stringify(groups.map(g => ({
    rootCause: g.rootCause,
    category: g.category,
    issueCount: g.indices.length,
    analyses: g.indices.map(i => ({
      summary: validAnalyses[i].summary,
      files: validAnalyses[i].affectedFiles,
      type: validAnalyses[i].translationType,
    })),
  }))) +
  '\n\nFor each entity name (god, monster, spell, skill, item) mentioned in the issues:\n' +
  '1. Check docs/decisions.md and docs/glossary.md for existing rulings\n' +
  '2. If a term appears across multiple issues, establish a SINGLE consistent translation\n' +
  '3. Output: term → translation → rationale (cite glossary/decisions source)\n' +
  '\nThis glossary will guide ALL translations in this batch to ensure consistency.',
  { label: 'build-glossary', schema: {
    type: 'object',
    properties: {
      terms: { type: 'array', items: { type: 'object', properties: {
        english: { type: 'string' }, chinese: { type: 'string' }, rationale: { type: 'string' },
      } } },
    },
    required: ['terms'],
  }}
)

if (glossary?.terms?.length) {
  log('批次术语表: ' + glossary.terms.length + ' 条')
}

// ── Phase 2: Batch Plan ────────────────────────────────

phase('Batch Plan')

let plan = await agent(
  'Create a unified fix plan for this batch of translation issues.\n' +
  '\nMerged groups (' + groups.length + '):\n' + JSON.stringify(groups.map(g => ({
    rootCause: g.rootCause,
    category: g.category,
    issueIndices: g.indices,
    details: g.indices.map(i => validAnalyses[i].summary),
  }))) +
  '\nBatch glossary:\n' + JSON.stringify(glossary?.terms || []) +
  '\n\nFor EACH merged group, specify:\n' +
  '- codeChanges: files to modify, what to change, why\n' +
  '- translationsNeeded: English text + context for each entry\n' +
  '\nBefore proposing changes, inspect current scripts, tests, and verification entry points. State observable acceptance criteria and explicit non-goals. Prefer extending existing files.\n' +
  'If proposing a new module, schema, persistent state, or directory, explain in that change\'s reason: the observed failure, why the existing mechanism is insufficient, and why the simplest alternative is not viable.\n' +
  'Do not add merge protocols, leases, recovery state, trusted clocks, reflog handling, or other infrastructure unless explicitly required by the user.\n' +
  '\nCRITICAL: Use the batch glossary for ALL terminology. Consistency across groups is mandatory.\n' +
  'Follow .agents/policies/i18n-safety.md: mprf_p for positional %n$s formats, no .c_str() on const char*, no protocol translation.\n' +
  'For Type III: plan the translator-owned source.txt entry before the coder-owned T_(variable). For Type V: text should stay English.',
  { label: 'batch-plan', schema: MERGED_PLAN_SCHEMA }
)

if (!plan) {
  log('FAIL: Batch plan failed')
  return { error: 'batch_plan_failed', analyses: validAnalyses, groups }
}

log('方案: ' + plan.approach)
log('合并组: ' + plan.mergedGroups.length + ' | 术语: ' + (plan.batchGlossary?.length || 0) + ' | 风险: ' + (plan.risks?.length || 0))

// ── Phase 3: Review Plan (gate) ────────────────────────

phase('Review Plan')
let planReview = await agent(
  'Review this batch fix plan. Be a skeptical gatekeeper.\n' +
  '\nPlan: ' + JSON.stringify(plan) + '\n' +
  'Analyses: ' + JSON.stringify(validAnalyses) + '\n' +
  '\nReview in this order:\n' +
  '1. Scope and simplicity: does every change serve an acceptance criterion; can any mechanism be deleted, reused, or narrowed; does the plan duplicate repository infrastructure?\n' +
  '2. In-scope coverage: are confirmed issues, failure paths, required tests, and glossary constraints covered?\n' +
  '3. Implementability: do referenced files, commands, and entry points exist; can all items execute sequentially without file conflicts?\n' +
  '4. Internal consistency: do the plan, risks, acceptance criteria, non-goals, and batch glossary agree?\n' +
  '\nClassify every issue. Out-of-scope risks do not block this plan. For design-induced issues, prefer deleting the responsible mechanism. Recommend adding a mechanism only after delete, reuse, and narrow are insufficient. Reject the plan when it requires new infrastructure or material scope expansion that needs user approval.\n' +
  '\nVerdict: approved | changes_requested | rejected',
  { label: 'review-plan', schema: REVIEW_PLAN_SCHEMA }
)

if (!planReview) {
  log('FAIL: Plan review failed')
  return { error: 'plan_review_failed' }
}

let planIterations = 0
while (planReview.verdict !== 'approved' && planIterations < 3) {
  planIterations++
  log('方案审核: ' + planReview.verdict + ' (第 ' + planIterations + '/3 轮)')

  if (planReview.verdict === 'rejected') {
    log('FAIL: 方案被否决')
    return { error: 'plan_rejected', planReview }
  }

  plan = await agent(
    'Revise the batch plan after classifying every review issue.\n' +
    'Review issues: ' + JSON.stringify(planReview.issues) + '\n' +
    'Current plan: ' + JSON.stringify(plan) + '\n' +
    'Resolve blocker or major issues only when they are inside the acceptance criteria or caused by the proposed diff. Preserve non-goals for out_of_scope issues. For design_induced issues, delete or narrow the responsible mechanism before adding one. A finding may be rejected with concrete repository evidence; reviewer suggestions are not commands.',
    { label: 'revise-plan-r' + planIterations, schema: MERGED_PLAN_SCHEMA }
  )
  if (!plan) { log('FAIL: Plan revision failed'); return { error: 'plan_revision_failed' } }

  planReview = await agent(
    'Re-review the revised plan.\n' +
    'Previous issues: ' + JSON.stringify(planReview.issues) + '\n' +
    'Revised plan: ' + JSON.stringify(plan) + '\n' +
    'Are all in-scope blocking issues resolved, rejected with concrete repository evidence, or eliminated by deleting the design that created them? Did the revision remain within the original non-goals?',
    { label: 'rereview-plan-r' + planIterations, schema: REVIEW_PLAN_SCHEMA }
  )
  if (!planReview) { log('FAIL: Re-review failed'); return { error: 'plan_rereview_failed' } }
}

if (planReview.verdict !== 'approved') {
  log('FAIL: 方案未通过')
  return { error: 'plan_not_approved', planIterations }
}
log('方案通过 ✅ (' + planIterations + ' 轮修订)')

// ── Phase 4: Execute Sequential ────────────────────────

phase('Execute Sequential')

const execResults = plan.mergedGroups.map((_, groupIndex) => ({ groupIndex }))

// Pass 1: finish every translator-owned asset before any coder is dispatched.
for (let g = 0; g < plan.mergedGroups.length; g++) {
  const grp = plan.mergedGroups[g]
  log('翻译组 ' + (g + 1) + '/' + plan.mergedGroups.length + ': ' + grp.rootCause.substring(0, 50) + '...')

  const transResult = await agent(
    'Add Chinese translations for batch group ' + (g + 1) + '/' + plan.mergedGroups.length + '.\n' +
    '\nTranslations needed: ' + JSON.stringify(grp.translationsNeeded) + '\n' +
    '\nBATCH GLOSSARY — YOU MUST USE THESE EXACT TRANSLATIONS:\n' + JSON.stringify(plan.batchGlossary) +
    '\n\nSteps:\n' +
    '1. Run context_resolve.sh with --task-type translate for the exact target files\n' +
    '2. Apply the returned glossary context and retain its SHA-256\n' +
    '3. For EACH entry, grep source.txt first to avoid duplicates\n' +
    '4. Add entries to crawl-ref/source/dat/i18n/zh/source.txt\n' +
    '5. For TextDB: add to correct zh/*.txt with English key\n' +
    '6. Preserve literal \\n, \\t, \\r, %%%%, %N$s, <tag>, and @keyword@ tokens byte-for-byte\n' +
    '7. Run: bash .claude/scripts/verify_zh.sh --profile translation\n' +
    '8. Return verificationStatus=pass only when that profile exits 0; otherwise return fail\n' +
    '9. If files changed, commit only translator-owned assets after verification, follow the active runtime commit-trailer policy, and leave the worktree clean\n' +
    '\nUse the batch glossary only when it agrees with the current resolver output; current docs/glossary.md wins.',
    { agentType: 'zh-translator', label: 'trans-g' + (g + 1), schema: EXEC_ITEM_SCHEMA.properties.translation }
  )

  const transOk = transResult?.verificationStatus === 'pass'
  if (!transOk) {
    log('  G' + (g + 1) + ' 翻译验证失败；全批代码阶段未运行。')
    return { error: 'translation_execution_failed', groupIndex: g, translation: transResult }
  }

  execResults[g].translation = transResult
  log('  G' + (g + 1) + ' 翻译: +' + transResult.entriesAdded + ' added, ' + (transResult.entriesModified || 0) + ' modified')
}

log('全部翻译资产已完成并验证；开始代码阶段。')

// Pass 2: code may now rely on every translator-owned key and TextDB asset.
for (let g = 0; g < plan.mergedGroups.length; g++) {
  const grp = plan.mergedGroups[g]
  const transResult = execResults[g].translation
  log('代码组 ' + (g + 1) + '/' + plan.mergedGroups.length + ': ' + grp.rootCause.substring(0, 50) + '...')

  const codeResult = await agent(
    'Implement code changes for batch group ' + (g + 1) + '/' + plan.mergedGroups.length + '.\n' +
    '\nRoot cause: ' + grp.rootCause + '\n' +
    'Code changes: ' + JSON.stringify(grp.codeChanges) + '\n' +
    'Type: ' + (validAnalyses[grp.issueIndices[0]]?.translationType || '?') + '\n' +
    '\nBatch glossary (USE THESE EXACT TRANSLATIONS):\n' + JSON.stringify(plan.batchGlossary) +
    '\n\nSteps:\n' +
    '1. Run context_resolve.sh with --task-type code for the exact target files\n' +
    '2. Apply the returned glossary context and retain its SHA-256\n' +
    '3. Make each code change as specified; do not reopen translator-owned assets\n' +
    '4. Run make -j4 to verify compilation\n' +
    '5. If compilation fails, fix and recompile\n' +
    '6. Run: bash .claude/scripts/verify_zh.sh --profile code\n' +
    '7. Return verificationStatus=pass only when that profile exits 0; otherwise return fail\n' +
    '8. If files changed, commit only coder-owned files after verification, follow the active runtime commit-trailer policy, and leave the worktree clean\n' +
    '\nCRITICAL: Use mprf_p for positional %n$s formats. No .c_str() on const char*. No protocol translation. Do not edit source.txt or ZH TextDB assets.',
    { agentType: 'crawl-coder', label: 'code-g' + (g + 1), schema: EXEC_ITEM_SCHEMA.properties.code }
  )

  const codeOk = codeResult?.compileStatus === 'pass'
    && codeResult?.verificationStatus === 'pass'
  if (!codeOk) {
    log('  G' + (g + 1) + ' 代码编译或验证失败；停止后续代码组。')
    return { error: 'code_execution_failed', groupIndex: g, code: codeResult, translation: transResult }
  }

  execResults[g].code = codeResult
  log('  G' + (g + 1) + ' 代码: ✅ | ' + (codeResult?.summary || ''))
}

log('执行完成: ' + execResults.length + ' 组全部处理')

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
  'Prepare the immutable schema-v4 review boundary. This is a mechanical Git and evidence task; do not edit source or translation files.\n' +
  '\nTarget checkout: ' + TARGET_ROOT +
  '\nTarget branch: ' + TARGET_BRANCH +
  '\nCandidate branch: ' + CANDIDATE_BRANCH +
  '\n\n1. Confirm target and candidate linked worktree are clean and match the named branches; do not commit or repair a dirty tree.\n' +
  '2. From the target checkout run: bash .claude/scripts/review_prepare.sh ' + CANDIDATE_BRANCH + ' ' + TARGET_BRANCH + '\n' +
  '3. Parse its canonical JSON and return prepared=true only on exit 0, copying bundle_id, bundle_path, target_head, candidate_head, glossary_sha256, and complete routing exactly.\n' +
  '4. On failure return prepared=false with the exact diagnostic.',
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

// ── Phase 6: Batch Review ──────────────────────────────

phase('Batch Review')

const routedReviewers = REVIEW_ROUTING?.reviewers
const routingMatrix = {
  none: [], code: ['zh-code-reviewer'], translation: ['translation-reviewer'],
  mixed: ['zh-code-reviewer', 'translation-reviewer'],
}
const expectedReviewers = routingMatrix[REVIEW_ROUTING?.classification]
if (REVIEW_ROUTING?.schema_version !== 2
    || !Array.isArray(routedReviewers)
    || !expectedReviewers
    || JSON.stringify(routedReviewers) !== JSON.stringify(expectedReviewers)) {
  log('FAIL: review bundle contains invalid mechanical routing.')
  return { error: 'review_routing_invalid', phase: 'Batch Review', reviewBoundary }
}

log('审核路由: ' + (REVIEW_ROUTING.classification || '?') + ' → '
  + (routedReviewers.length ? routedReviewers.join(', ') : 'no reviewers'))

const reviewJobs = []
if (routedReviewers.includes('zh-code-reviewer')) {
  reviewJobs.push(async () => ({ kind: 'code', result: await agent(
    'Review ALL code changes from this batch.\n' +
    'Resolve current terminology with context_resolve.sh --task-type review.\n' +
    'Inspect bundle ' + reviewBoundary.bundle_id + ' and its exact ' + reviewBoundary.target_head + '..' + reviewBoundary.candidate_head + ' committed diff plus existing development-profile and targeted-test logs.\n' +
    'Fail No-Go if the bundle, heads, routing, glossary hash, or clean-worktree precondition cannot be verified.\n' +
    'Do not run verify_zh.sh --profile review; the final gate owns the single full review run.\n' +
    'Review the diff: protocol/display, T_() correctness, compilation, DB integrity, EN mode.\n' +
    'Use review-contract-v5 severities blocker|needs_fix|suggestion. Return the complete findings array; each finding requires id, severity, file, line, evidence, impact, and fix. Do not return counts or readiness. Interpret relevant failures/warnings, report glossary SHA-256, and return reviewedScope exactly as ' + JSON.stringify(REVIEW_ROUTING.files) + '.',
    { agentType: 'zh-code-reviewer', label: 'code-review', schema: CODE_BATCH_REVIEW_SCHEMA }
  ) }))
}
if (routedReviewers.includes('translation-reviewer')) {
  reviewJobs.push(async () => ({ kind: 'translation', result: await agent(
    'Review ALL translation quality from this batch.\n' +
    'Resolve current terminology with context_resolve.sh --task-type review.\n' +
    'Inspect bundle ' + reviewBoundary.bundle_id + ' and its exact ' + reviewBoundary.target_head + '..' + reviewBoundary.candidate_head + ' committed diff plus existing development-profile and targeted-test logs.\n' +
    'Fail No-Go if the bundle, heads, routing, glossary hash, or clean-worktree precondition cannot be verified.\n' +
    'Do not run verify_zh.sh --profile review; the final gate owns the single full review run.\n' +
    'Review: semantic accuracy, no fabrication, natural Chinese, precision, terminology.\n' +
    'Cross-reference against batch glossary and docs/glossary.md.\n' +
    'Use review-contract-v5 severities blocker|needs_fix|suggestion. Return the complete findings array; each finding requires id, severity, file, line, evidence, impact, fix, english, and chinese. Do not return counts or readiness. Interpret content-relevant failures/warnings, report glossary SHA-256, and return reviewedScope exactly as ' + JSON.stringify(REVIEW_ROUTING.files) + '.',
    { agentType: 'translation-reviewer', label: 'trans-review', schema: TRANS_BATCH_REVIEW_SCHEMA }
  ) }))
}
const reviews = reviewJobs.length ? await parallel(reviewJobs) : []
const reviewResult = kind => {
  const result = reviews.find(item => item?.kind === kind)?.result || null
  if (!result) return null
  const findings = validateReviewFindings(
    kind, result, reviewBoundary.glossary_sha256, REVIEW_ROUTING.files)
  const count = severity => findings.filter(item => item.severity === severity).length
  const blockers = count('blocker')
  const needsFix = count('needs_fix')
  return { ...result, findings, blockers, needsFix, suggestions: count('suggestion'),
    readiness: blockers ? 'No-Go' : needsFix ? 'Changes Requested' : 'Ready for Final Gate' }
}
const codeReview = reviewResult('code')
const transReview = reviewResult('translation')

log([
  codeReview ? 'Code:' + codeReview.readiness + ' B' + codeReview.blockers + 'F' + codeReview.needsFix : 'Code:N/A',
  transReview ? 'Trans:' + transReview.readiness + ' B' + transReview.blockers + 'F' + transReview.needsFix : 'Trans:N/A',
].join(' | '))

const executionIncomplete = execResults.length !== plan.mergedGroups.length
  || execResults.some(result => {
    const group = plan.mergedGroups[result.groupIndex]
    const codeRequired = (group?.codeChanges?.length || 0) > 0
    const translationRequired = (group?.translationsNeeded?.length || 0) > 0
    return (codeRequired && result.code?.compileStatus !== 'pass')
      || (translationRequired && !result.translation)
  })
const reviewerIncomplete = routedReviewers.some(kind =>
  kind === 'zh-code-reviewer' ? !codeReview : !transReview)
const hasBlockers = (codeReview?.blockers > 0) || (transReview?.blockers > 0)
  || codeReview?.readiness === 'No-Go' || transReview?.readiness === 'No-Go'
const hasChangesRequested = (codeReview?.needsFix > 0) || (transReview?.needsFix > 0)
  || codeReview?.readiness === 'Changes Requested'
  || transReview?.readiness === 'Changes Requested'

// ── Phase 6: Cross-validate ────────────────────────────

phase('Cross-validate')

const crossValidation = await agent(
  'Adversarial cross-validation on the ENTIRE batch.\n' +
  '\nBatch: ' + ISSUES.length + ' issues → ' + groups.length + ' groups → ' + execResults.length + ' executed\n' +
  'Code review: ' + (codeReview?.readiness || '?') + ' B' + (codeReview?.blockers || 0) + '\n' +
  'Trans review: ' + (transReview?.readiness || '?') + ' B' + (transReview?.blockers || 0) + '\n' +
  '\nPerform read-only analysis and narrowly targeted checks only. Do not run the full review profile; the final gate owns it.\n' +
  'Run the focused terminology ruling check: bash .claude/scripts/check_consistency.sh --rulings\n' +
  '\nCheck: missed edge cases? side effects? same pattern elsewhere? EN mode ok? format strings ok? DB keys ok?\n' +
  'Also check: any glossary term used inconsistently across groups? Any duplicate source.txt keys from serial appends?',
  { label: 'cross-validate', schema: CROSS_VALIDATE_SCHEMA }
)

if (crossValidation) {
  log('交叉验证: ' + (crossValidation.passed ? 'PASS' : 'ISSUES FOUND'))
  if (crossValidation.missedItems?.length) log('遗漏: ' + crossValidation.missedItems.join('; '))
  if (crossValidation.sideEffects?.length) log('副作用: ' + crossValidation.sideEffects.join('; '))
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
} else if (!reviewFailure) {
  readinessEvidence = await agent(
    'Persist the exact schema-v4 reviewer findings and readiness records. Do not edit or commit repository files and do not run any verification profile.\n' +
    '\nTarget checkout: ' + TARGET_ROOT +
    '\nCandidate branch: ' + CANDIDATE_BRANCH +
    '\nBundle id: ' + reviewBoundary.bundle_id +
    '\nRequired routed reviewers: ' + JSON.stringify(routedReviewers) +
    '\nReviewed scope: ' + JSON.stringify(REVIEW_ROUTING.files) +
    '\nCode findings: ' + JSON.stringify(codeReview?.findings || []) +
    '\nTranslation findings: ' + JSON.stringify(transReview?.findings || []) +
    '\n\nResolve the candidate linked-worktree path. For every routed role, write a canonical ordinary JSON file outside both clean Git worktrees (for example under /tmp) containing schema, validated bundle_id/bundle_sha256/routing_sha256, reviewer, reviewed_scope exactly equal to routing.files, and the exact findings array. Invoke record-readiness with --findings-json naming that file. Then run status. Return completed=true only when every role was recorded and state is FINAL_GATE_REQUIRED (11) or FINAL_APPROVAL_REQUIRED (13). Never invoke review_final_gate.sh in this step.',
    { label: 'persist-review-readiness', schema: EVIDENCE_RESULT_SCHEMA }
  )

}
if (!reviewFailure && readinessEvidence?.completed) {
  finalGate = await agent(
      'Run the single schema-v4 final gate. Do not run verify_zh.sh directly, pass retry/recovery flags, or modify evidence manually.\n' +
      '\nFrom the clean target checkout ' + TARGET_ROOT + ', run exactly:\n' +
      '  bash .claude/scripts/review_final_gate.sh ' + CANDIDATE_BRANCH + ' ' + TARGET_BRANCH + '\n' +
      '\nParse the emitted JSON and return completed=true only for MERGEABLE with exit code 0. Preserve any other exact state/exit code and do not retry automatically.',
      { label: 'run-single-final-gate', schema: EVIDENCE_RESULT_SCHEMA }
    )
}

const hardFailure = reviewFailure || !readinessEvidence?.completed
  || !finalGate?.completed || finalGate?.state !== 'MERGEABLE'
const finalReadiness = hardFailure ? 'NOT_READY' : 'MERGEABLE'

// ── Phase 8: Aggregate Report ──────────────────────────

phase('Report')

// Per-issue status
const issueStatus = validAnalyses.map((a, i) => {
  const grpIdx = groups.findIndex(g => g.indices.includes(i))
  return '  Issue #' + (i + 1) + ': ' + a.category + ' | Type ' + a.translationType + ' | Group ' + (grpIdx + 1) + ' | ' + a.summary.substring(0, 60)
}).join('\n')

await agent(
  'Generate the batch pipeline report as clean markdown.\n' +
  '\n## Batch Summary\n' +
  'Issues: ' + ISSUES.length + ' → Merged to ' + groups.length + ' root cause groups\n' +
  'Glossary: ' + (glossary?.terms?.length || 0) + ' terms\n' +
  '\n## Per-Issue Status\n' + issueStatus + '\n' +
  '\n## Plan\n' + (plan?.approach || 'N/A') + '\n' +
  'Groups: ' + (plan?.mergedGroups?.length || 0) + ' | Risks: ' + (plan?.risks?.join('; ') || 'none') + '\n' +
  'Plan rounds: ' + planIterations + '\n' +
  '\n## Execution (sequential, same worktree)\n' +
  execResults.map(r => '  G' + (r.groupIndex + 1) + ': code=' + (r.code?.compileStatus || '?') + ' trans=+' + (r.translation?.entriesAdded || 0)).join('\n') + '\n' +
  '\n## Reviews\n' +
  'Code: ' + (codeReview?.readiness || '?') + ' B:' + (codeReview?.blockers || 0) + ' F:' + (codeReview?.needsFix || 0) + ' S:' + (codeReview?.suggestions || 0) + '\n' +
  'Trans: ' + (transReview?.readiness || '?') + ' B:' + (transReview?.blockers || 0) + ' F:' + (transReview?.needsFix || 0) + ' S:' + (transReview?.suggestions || 0) + '\n' +
  '\n## Cross-Validation\n' +
  (crossValidation?.passed ? 'PASS' : 'ISSUES') + '\n' +
  'Missed: ' + (crossValidation?.missedItems?.join('; ') || 'none') + '\n' +
  'Side effects: ' + (crossValidation?.sideEffects?.join('; ') || 'none') + '\n' +
  '\n## Evidence\n' +
  'Bundle: ' + reviewBoundary.bundle_id + '\n' +
  'Readiness evidence: ' + readinessEvidence?.state + ' (exit ' + readinessEvidence?.exitCode + ')\n' +
  'Final gate: ' + finalGate?.state + ' (exit ' + finalGate?.exitCode + ')\n' +
  '\n## Readiness: ' + finalReadiness + '\n' +
  (finalReadiness === 'MERGEABLE' ? 'Run review_at_merge.sh read-only, then merge the exact approved candidate OID.' : 'Do not merge. Resolve the state; failed/interrupted attempts and stale residue require explicit operator action.') + '\n' +
  '\nFormat as structured markdown with sections: Summary, Per-Issue Status, Batch Glossary, Changes, Reviews, Cross-Validation, Evidence, Merge Authorization.',
  { label: 'report' }
)

return {
  analyses: validAnalyses,
  groups,
  glossary,
  plan,
  planReview,
  planIterations,
  execResults,
  reviewBoundary,
  reviewRouting: REVIEW_ROUTING,
  codeReview,
  transReview,
  crossValidation,
  readinessEvidence,
  finalGate,
  readiness: finalReadiness,
  hasBlockers,
  hasChangesRequested,
  hardFailure,
}
