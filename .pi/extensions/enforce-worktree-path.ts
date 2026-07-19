import {
  isToolCallEventType,
  type ExtensionAPI,
} from "@earendil-works/pi-coding-agent";

const ALLOWED_PREFIX = ".worktrees/";

export function extractWorktreeAddSegments(command: string): string[] {
  const segments: string[] = [];
  const parts = command.split(/&&|\|\||;|\n|\|/);
  for (const part of parts) {
    if (/\bgit\b[\s\S]*\bworktree\b[\s\S]*\badd\b/.test(part)) {
      segments.push(part.trim());
    }
  }
  return segments;
}

export function extractTargetPath(segment: string): string | null {
  const tokens = segment.match(/(?:[^\s"']+|"[^"]*"|'[^']*')+/g) ?? [];
  const addIndex = tokens.findIndex((token) => token === "add");
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
    return token.replace(/^["']|["']$/g, "");
  }
  return null;
}

export function isCompliantWorktreeTarget(target: string | null): boolean {
  if (!target) return false;
  if (target.startsWith("/") || target.startsWith("~") || target.startsWith("../")) {
    return false;
  }
  if (target.includes("/../")) return false;
  return target.startsWith(ALLOWED_PREFIX);
}

export default function enforceWorktreePath(pi: ExtensionAPI): void {
  pi.on("tool_call", (event) => {
    if (!isToolCallEventType("bash", event)) return;

    for (const segment of extractWorktreeAddSegments(event.input.command)) {
      const target = extractTargetPath(segment);
      if (!isCompliantWorktreeTarget(target)) {
        return {
          block: true,
          reason:
            `[worktree-policy] Blocked: worktree must be created inside '${ALLOWED_PREFIX}' ` +
            `at the repo root using a relative path. Offending command: ${segment}; ` +
            `detected target: ${target ?? "(none)"}; correct form: ` +
            `git worktree add ${ALLOWED_PREFIX}<name> <branch>. See AGENTS.md and ` +
            `.agents/policies/worktree-policy.md.`,
        };
      }
    }
  });
}
