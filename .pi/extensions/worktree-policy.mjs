import { lstat, mkdir, realpath, stat } from "node:fs/promises";
import path from "node:path";

const NAME_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;
const WORKTREE_DIR = ".worktrees";
const GIT_TIMEOUT_MS = 30_000;

function stripQuotes(value) {
  return value.replace(/^["']|["']$/g, "");
}

function shellTokens(segment) {
  return (segment.match(/(?:[^\s"']+|"[^"]*"|'[^']*')+/g) ?? []).map(stripQuotes);
}

function normalizeShellForGuard(segment) {
  return segment
    .replace(/''|""/g, "")
    .replace(/\\([^\n])/g, "$1");
}

export function extractGitWorktreeSegments(command) {
  const segments = [];
  for (const part of command.split(/&&|\|\||;|\n|\|/)) {
    const normalized = normalizeShellForGuard(part);
    if (/\bgit\b[\s\S]*\bworktree\b/.test(normalized)) {
      segments.push(part.trim());
    }
  }
  return segments;
}

export function containsEnabledWorktreeFlag(value) {
  if (Array.isArray(value)) return value.some(containsEnabledWorktreeFlag);
  if (!value || typeof value !== "object") return false;
  return Object.entries(value).some(([key, child]) =>
    (key === "worktree" && child === true) || containsEnabledWorktreeFlag(child));
}

export function extractTargetPath(segment) {
  const tokens = shellTokens(segment);
  const addIndex = tokens.indexOf("add");
  if (addIndex === -1) return null;

  const valueFlags = new Set(["-b", "-B", "--reason"]);
  let index = addIndex + 1;
  while (index < tokens.length) {
    const token = tokens[index];
    if (valueFlags.has(token)) {
      index += 2;
      continue;
    }
    if (token.startsWith("--") && token.includes("=")) {
      index += 1;
      continue;
    }
    if (token.startsWith("-")) {
      index += 1;
      continue;
    }
    return token;
  }
  return null;
}

export function validateWorktreeName(name) {
  if (typeof name !== "string" || !NAME_PATTERN.test(name) || name === "." || name === "..") {
    throw new Error("worktree name must be one safe path component using letters, digits, '.', '_' or '-'");
  }
  return name;
}

export function relativeWorktreePath(name) {
  return `${WORKTREE_DIR}/${validateWorktreeName(name)}`;
}

export function isCompliantWorktreeTarget(target) {
  if (typeof target !== "string") return false;
  try {
    return target === relativeWorktreePath(target.slice(`${WORKTREE_DIR}/`.length));
  } catch {
    return false;
  }
}

export function worktreeToolCallViolation(event) {
  if (!event || typeof event !== "object") return null;
  if (event.toolName === "subagent" && containsEnabledWorktreeFlag(event.input)) {
    return "[worktree-policy] Blocked pi-subagents worktree:true. Create an isolated checkout with project_worktree, then pass its returned cwd to subagent without worktree:true.";
  }
  if (event.toolName !== "bash" || typeof event.input?.command !== "string") return null;
  const segment = extractGitWorktreeSegments(event.input.command)[0];
  if (!segment) return null;
  const target = extractTargetPath(segment);
  return "[worktree-policy] Blocked direct Git worktree operation. Use project_worktree " +
    "so lifecycle operations are anchored to the primary checkout and serialized. " +
    `Offending command: ${segment}; detected target: ${target ?? "(none)"}. ` +
    "See AGENTS.md and .agents/policies/worktree-policy.md.";
}

export function validatePiBranch(branch) {
  if (typeof branch !== "string" || !branch.startsWith("pi/")) {
    throw new Error("task branch must use the Pi ownership prefix 'pi/' and a valid non-empty suffix");
  }
  const components = branch.slice("pi/".length).split("/");
  if (components.length === 0 || components.some((component) =>
    !NAME_PATTERN.test(component) || component === "." || component === "..")) {
    throw new Error("task branch must use the Pi ownership prefix 'pi/' and safe path components");
  }
  return branch;
}

export function parseWorktreePorcelain(output) {
  if (typeof output !== "string" || !output.trim()) {
    throw new Error("git worktree inventory is empty");
  }
  const records = [];
  for (const block of output.trim().split(/\n\s*\n/)) {
    const record = { path: "", head: null, branch: null, detached: false, bare: false };
    for (const line of block.split("\n")) {
      if (line.startsWith("worktree ")) record.path = line.slice("worktree ".length);
      else if (line.startsWith("HEAD ")) record.head = line.slice("HEAD ".length);
      else if (line.startsWith("branch ")) record.branch = line.slice("branch refs/heads/".length);
      else if (line === "detached") record.detached = true;
      else if (line === "bare") record.bare = true;
    }
    if (!record.path) throw new Error("git worktree inventory contains a record without a path");
    records.push(record);
  }
  return records;
}

function resultText(result) {
  return (result.stderr || result.stdout || "git command failed").trim();
}

async function runGit(exec, cwd, args, signal, allowFailure = false) {
  const result = await exec("git", args, { cwd, signal, timeout: GIT_TIMEOUT_MS });
  if (!allowFailure && result.code !== 0) {
    throw new Error(`git ${args.join(" ")} failed: ${resultText(result)}`);
  }
  return result;
}

async function inventory(exec, cwd, signal) {
  const result = await runGit(exec, cwd, ["worktree", "list", "--porcelain"], signal);
  return parseWorktreePorcelain(result.stdout);
}

async function discoverMainRoot(exec, cwd, signal) {
  const inside = await runGit(exec, cwd, ["rev-parse", "--is-inside-work-tree"], signal);
  if (inside.stdout.trim() !== "true") throw new Error("project worktrees require a non-bare Git repository");

  const records = await inventory(exec, cwd, signal);
  if (records[0].bare) throw new Error("project worktrees do not support a bare primary repository");
  return { mainRoot: await realpath(records[0].path), records };
}

function expectedAbsolutePath(mainRoot, name) {
  const expected = path.resolve(mainRoot, relativeWorktreePath(name));
  const parent = path.dirname(expected);
  if (parent !== path.join(mainRoot, WORKTREE_DIR)) {
    throw new Error("resolved worktree path escapes the primary repository worktree directory");
  }
  return expected;
}

function pathIsInside(candidate, root) {
  const relative = path.relative(root, candidate);
  return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}

async function pathExists(value) {
  try {
    await stat(value);
    return true;
  } catch (error) {
    if (error && error.code === "ENOENT") return false;
    throw error;
  }
}

async function ensurePolicyWorktreeDirectory(mainRoot) {
  const directory = path.join(mainRoot, WORKTREE_DIR);
  try {
    const metadata = await lstat(directory);
    if (metadata.isSymbolicLink() || !metadata.isDirectory()) {
      throw new Error(`${WORKTREE_DIR} must be a real directory directly below the primary checkout`);
    }
  } catch (error) {
    if (!error || error.code !== "ENOENT") throw error;
    await mkdir(directory);
  }
  const canonical = await realpath(directory);
  if (canonical !== directory) {
    throw new Error(`${WORKTREE_DIR} resolves outside the primary checkout`);
  }
  return directory;
}

async function requireClean(exec, cwd, signal, label) {
  const status = await runGit(exec, cwd, ["status", "--porcelain", "--untracked-files=normal"], signal);
  if (status.stdout.trim()) throw new Error(`${label} must be clean before this operation`);
}

function policyWorktrees(records, mainRoot) {
  const base = path.join(mainRoot, WORKTREE_DIR);
  return records
    .filter((record) => {
      const relative = path.relative(base, path.resolve(record.path));
      return relative && relative !== ".." && !relative.startsWith(`..${path.sep}`)
        && !path.isAbsolute(relative) && !relative.includes(path.sep);
    })
    .map((record) => ({ ...record, name: path.basename(record.path) }));
}

async function resolveCommit(exec, cwd, startPoint, signal) {
  const expression = `${startPoint || "HEAD"}^{commit}`;
  const result = await runGit(exec, cwd, ["rev-parse", "--verify", expression], signal);
  const oid = result.stdout.trim();
  if (!/^[0-9a-fA-F]{40,64}$/.test(oid)) throw new Error(`start point did not resolve to a commit: ${startPoint || "HEAD"}`);
  return oid;
}

async function createWorktree(input, context) {
  const name = validateWorktreeName(input.name);
  const { exec, cwd, signal } = context;
  await requireClean(exec, cwd, signal, "current checkout");
  const baseOid = await resolveCommit(exec, cwd, input.startPoint, signal);
  const { mainRoot } = await discoverMainRoot(exec, cwd, signal);
  const relativePath = relativeWorktreePath(name);
  const absolutePath = expectedAbsolutePath(mainRoot, name);

  await ensurePolicyWorktreeDirectory(mainRoot);
  const records = await inventory(exec, mainRoot, signal);
  if (records.some((record) => path.resolve(record.path) === absolutePath) || await pathExists(absolutePath)) {
    throw new Error(`worktree target already exists: ${relativePath}`);
  }

  let branch = null;
  const args = ["worktree", "add"];
  if (input.branch !== undefined) {
    branch = validatePiBranch(input.branch);
    await runGit(exec, mainRoot, ["check-ref-format", "--branch", branch], signal);
    if (records.some((record) => record.branch === branch)) throw new Error(`branch is already checked out: ${branch}`);
    const exists = await runGit(exec, mainRoot, ["show-ref", "--verify", "--quiet", `refs/heads/${branch}`], signal, true);
    if (exists.code === 0) throw new Error(`branch already exists; create requires a new task branch: ${branch}`);
    if (exists.code !== 1) throw new Error(`failed to check task branch ${branch}: ${resultText(exists)}`);
    args.push("-b", branch);
  } else {
    args.push("--detach");
  }
  args.push(relativePath, baseOid);

  await runGit(exec, mainRoot, args, signal);
  const created = (await inventory(exec, mainRoot, signal))
    .find((record) => path.resolve(record.path) === absolutePath);
  if (!created) throw new Error("Git reported success but the new worktree is absent from its inventory");

  return { action: "create", name, cwd: absolutePath, worktreePath: relativePath, branch, head: created.head };
}

async function listWorktrees(_input, context) {
  const { mainRoot, records } = await discoverMainRoot(context.exec, context.cwd, context.signal);
  return {
    action: "list",
    mainRoot,
    worktrees: policyWorktrees(records, mainRoot).map((record) => ({
      name: record.name,
      cwd: path.resolve(record.path),
      worktreePath: relativeWorktreePath(record.name),
      branch: record.branch,
      head: record.head,
      detached: record.detached,
    })),
  };
}

async function removeWorktree(input, context) {
  const name = validateWorktreeName(input.name);
  const { exec, cwd, signal } = context;
  const { mainRoot } = await discoverMainRoot(exec, cwd, signal);
  const relativePath = relativeWorktreePath(name);
  const absolutePath = expectedAbsolutePath(mainRoot, name);
  if (pathIsInside(path.resolve(cwd), absolutePath)) throw new Error("cannot remove the worktree containing the active Pi session");

  const records = await inventory(exec, mainRoot, signal);
  const record = records.find((candidate) => path.resolve(candidate.path) === absolutePath);
  if (!record) throw new Error(`registered project worktree not found: ${relativePath}`);
  await requireClean(exec, absolutePath, signal, "target worktree");
  await runGit(exec, mainRoot, ["worktree", "remove", relativePath], signal);

  return {
    action: "remove",
    name,
    worktreePath: relativePath,
    retainedBranch: record.branch,
    message: record.branch ? `Removed worktree; retained branch ${record.branch}.` : "Removed detached worktree.",
  };
}

export async function manageProjectWorktree(input, context) {
  if (!input || typeof input !== "object") throw new Error("project worktree input must be an object");
  if (input.action === "list") return listWorktrees(input, context);
  if (input.action === "create") return createWorktree(input, context);
  if (input.action === "remove") return removeWorktree(input, context);
  throw new Error("action must be one of: list, create, remove");
}
