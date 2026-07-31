import { realpathSync } from "node:fs";
import { homedir } from "node:os";
import { isAbsolute, relative, resolve, sep } from "node:path";

const ALLOWED_TOOLS = new Set(["read", "grep", "find", "ls"]);
const PRIVATE_TOP_LEVEL_PATHS = new Set([".git", ".pi-subagents"]);

function expandInputPath(rawPath) {
  let value = rawPath.startsWith("@") ? rawPath.slice(1) : rawPath;
  if (value === "~") return homedir();
  if (value.startsWith("~/") || value.startsWith(`~${sep}`)) {
    return resolve(homedir(), value.slice(2));
  }
  return value;
}

function isOutsideRoot(candidate, root) {
  const relativePath = relative(root, candidate);
  return relativePath === ".."
    || relativePath.startsWith(`..${sep}`)
    || isAbsolute(relativePath);
}

export function repositoryPathViolation(rawPath, rootPath) {
  if (typeof rawPath !== "string" || rawPath.length === 0) {
    return "A repository-relative path is required.";
  }

  let root;
  let candidate;
  try {
    root = realpathSync(rootPath);
    const expandedPath = expandInputPath(rawPath);
    const resolvedPath = isAbsolute(expandedPath)
      ? resolve(expandedPath)
      : resolve(root, expandedPath);
    candidate = realpathSync(resolvedPath);
  } catch {
    return `Path cannot be resolved inside the repository: ${rawPath}`;
  }

  if (isOutsideRoot(candidate, root)) {
    return `Path is outside the repository: ${rawPath}`;
  }

  const relativePath = relative(root, candidate);
  const firstSegment = relativePath.split(sep)[0];
  if (PRIVATE_TOP_LEVEL_PATHS.has(firstSegment)) {
    return `Path is private to the supervisor runtime: ${rawPath}`;
  }

  return undefined;
}

export default function repositoryReadOnlyGuard(pi) {
  const configuredRoot = process.env.PI_SUBAGENT_ROOT;
  if (!configuredRoot) {
    throw new Error("PI_SUBAGENT_ROOT is required by pi-subagent-guard");
  }

  const root = realpathSync(configuredRoot);
  pi.on("tool_call", (event) => {
    if (!ALLOWED_TOOLS.has(event.toolName)) {
      return {
        block: true,
        reason: `Tool is disabled for the read-only Pi worker: ${event.toolName}`,
      };
    }

    const inputPath = event.input?.path;
    if (event.toolName === "read" && typeof inputPath !== "string") {
      return { block: true, reason: "The read tool requires a repository path." };
    }

    const reason = repositoryPathViolation(
      typeof inputPath === "string" ? inputPath : ".",
      root,
    );
    if (reason) return { block: true, reason };
  });
}
