const ALLOWED_PREFIX = ".worktrees/";

function extractWorktreeAddSegments(command) {
  const segments = [];
  const parts = command.split(/&&|\|\||;|\n|\|/);
  for (const part of parts) {
    if (/\bgit\b[\s\S]*\bworktree\b[\s\S]*\badd\b/.test(part)) {
      segments.push(part.trim());
    }
  }
  return segments;
}

function extractTargetPath(segment) {
  const tokens = segment.match(/(?:[^\s"']+|"[^"]*"|'[^']*')+/g) || [];
  const addIdx = tokens.findIndex((t) => t === "add");
  if (addIdx === -1) return null;
  const valueFlags = new Set(["-b", "-B", "--reason"]);
  let i = addIdx + 1;
  while (i < tokens.length) {
    const tok = tokens[i];
    if (valueFlags.has(tok)) {
      i += 2;
      continue;
    }
    if (tok.startsWith("--") && tok.includes("=")) {
      i += 1;
      continue;
    }
    if (tok.startsWith("-")) {
      i += 1;
      continue;
    }
    return tok.replace(/^["']|["']$/g, "");
  }
  return null;
}

function isCompliant(target) {
  if (!target) return false;
  if (target.startsWith("/")) return false;
  if (target.startsWith("~")) return false;
  if (target.startsWith("../")) return false;
  if (target.includes("/../")) return false;
  return target.startsWith(ALLOWED_PREFIX);
}

export default async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return;
      const command = output?.args?.command;
      if (typeof command !== "string") return;

      const segments = extractWorktreeAddSegments(command);
      if (segments.length === 0) return;

      for (const segment of segments) {
        const target = extractTargetPath(segment);
        if (!isCompliant(target)) {
          throw new Error(
            `[worktree-policy] Blocked: worktree must be created inside '${ALLOWED_PREFIX}' at the repo root using a relative path.\n` +
              `  Offending command: ${segment}\n` +
              `  Detected target:   ${target ?? "(none)"}\n` +
              `  Correct form:      git worktree add ${ALLOWED_PREFIX}<name> <branch>\n` +
              `  Rationale:         keeps all worktrees inside the repo (WSL-friendly, relative paths, easy cleanup). See AGENTS.md "Worktree Placement Policy".`
          );
        }
      }
    },
  };
};
