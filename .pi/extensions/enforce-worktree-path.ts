import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { StringEnum } from "@earendil-works/pi-ai";
import { Type } from "typebox";
import {
  manageProjectWorktree,
  worktreeToolCallViolation,
} from "./worktree-policy.mjs";

let mutationQueue: Promise<unknown> = Promise.resolve();

function serializeMutation<T>(operation: () => Promise<T>): Promise<T> {
  const run = mutationQueue.then(operation, operation);
  mutationQueue = run.then(() => undefined, () => undefined);
  return run;
}

function formatResult(result: unknown): string {
  return JSON.stringify(result, null, 2);
}

export default function enforceWorktreePath(pi: ExtensionAPI): void {
  pi.on("tool_call", (event) => {
    const reason = worktreeToolCallViolation(event);
    if (reason) return { block: true, reason };
  });

  pi.registerTool({
    name: "project_worktree",
    label: "Project Worktree",
    description:
      "List, create, or safely remove project-policy worktrees. Creation runs from " +
      "the primary checkout with a relative .worktrees/<name> target and returns an " +
      "absolute cwd for a later subagent call. Omit branch for detached HEAD; supplied " +
      "task branches must start with pi/. Removal refuses dirty or active worktrees and " +
      "retains branches.",
    promptSnippet: "Manage policy-compliant project worktrees for isolated subagent cwd dispatch",
    promptGuidelines: [
      "Use project_worktree instead of pi-subagents worktree:true in this repository.",
      "After project_worktree create, pass its returned cwd to subagent with worktree:false or without the worktree field.",
      "Do not remove a project worktree until its changes are committed or intentionally discarded and the worktree is clean.",
    ],
    parameters: Type.Object({
      action: StringEnum(["list", "create", "remove"] as const, {
        description: "Lifecycle action",
      }),
      name: Type.Optional(Type.String({
        description: "One-component directory name below .worktrees; required for create/remove",
      })),
      branch: Type.Optional(Type.String({
        description: "New pi/<topic> task branch for create; omit to create detached",
      })),
      startPoint: Type.Optional(Type.String({
        description: "Commit-ish for create; defaults to the active checkout's exact HEAD",
      })),
    }, { additionalProperties: false }),
    async execute(_toolCallId, params, signal, _onUpdate, ctx) {
      const operation = () => manageProjectWorktree(params, {
        cwd: ctx.cwd,
        signal,
        exec: (command: string, args: string[], options: Record<string, unknown>) =>
          pi.exec(command, args, options),
      });
      const result = params.action === "list" ? await operation() : await serializeMutation(operation);
      return {
        content: [{ type: "text", text: formatResult(result) }],
        details: result,
      };
    },
  });
}
