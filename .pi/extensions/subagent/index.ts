/**
 * Project subagent tool — delegate tasks to project-local agents
 * (.pi/agents/*.md) in isolated `pi` subprocesses.
 *
 * Adapted from the official pi-coding-agent subagent example with the
 * project's documented interface and defaults:
 *
 *   subagent({ action: "list" })                       -> discover agents
 *   subagent({ agent: "crawl-coder", task: "..." })    -> single run
 *   subagent({ agent: "...", task: "...", cwd })       -> worktree dispatch
 *   subagent({ agent: "...", task: "...", async: true }) -> background run,
 *                                                          output to log file
 *
 * Agent scope defaults to "project" (this repository's .pi/agents are the
 * trusted role definitions; see docs/agent-routing.md). Frontmatter fields
 * systemPromptMode / inheritProjectContext / inheritSkills / thinking are
 * honored, matching the project agent files.
 *
 * Security: subagents spawn a separate pi process with a delegated system
 * prompt, restricted tool set, and the caller-provided cwd. No project
 * agents are executed unless requested by name.
 */

import { spawn } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import type { Message } from "@earendil-works/pi-ai";
import { StringEnum } from "@earendil-works/pi-ai";
import { Type } from "typebox";
import { type AgentConfig, type AgentScope, discoverAgents, formatAgentList } from "./agents.ts";

const PER_TASK_OUTPUT_CAP = 50 * 1024;
const KILL_GRACE_MS = 5000;

interface UsageStats {
  input: number;
  output: number;
  cacheRead: number;
  cacheWrite: number;
  cost: number;
  contextTokens: number;
  turns: number;
}

interface SingleResult {
  agent: string;
  agentSource: "project" | "unknown";
  task: string;
  exitCode: number;
  messages: Message[];
  stderr: string;
  usage: UsageStats;
  model?: string;
  stopReason?: string;
  errorMessage?: string;
}

function emptyUsage(): UsageStats {
  return { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, cost: 0, contextTokens: 0, turns: 0 };
}

function getFinalOutput(messages: Message[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];
    if (msg.role === "assistant") {
      for (const part of msg.content) {
        if (part.type === "text") return part.text;
      }
    }
  }
  return "";
}

function isFailedResult(result: SingleResult): boolean {
  return result.exitCode !== 0 || result.stopReason === "error" || result.stopReason === "aborted";
}

function getResultOutput(result: SingleResult): string {
  if (isFailedResult(result)) {
    return result.errorMessage || result.stderr || getFinalOutput(result.messages) || "(no output)";
  }
  return getFinalOutput(result.messages) || "(no output)";
}

async function writePromptToTempFile(agentName: string, prompt: string): Promise<{ dir: string; filePath: string }> {
  const tmpDir = await fs.promises.mkdtemp(path.join(os.tmpdir(), "pi-subagent-"));
  const safeName = agentName.replace(/[^\w.-]+/g, "_");
  const filePath = path.join(tmpDir, `prompt-${safeName}.md`);
  await fs.promises.writeFile(filePath, prompt, { encoding: "utf-8", mode: 0o600 });
  return { dir: tmpDir, filePath };
}

function getPiInvocation(args: string[]): { command: string; args: string[] } {
  const currentScript = process.argv[1];
  const isBunVirtualScript = currentScript?.startsWith("/$bunfs/root/");
  if (currentScript && !isBunVirtualScript && fs.existsSync(currentScript)) {
    return { command: process.execPath, args: [currentScript, ...args] };
  }
  const execName = path.basename(process.execPath).toLowerCase();
  const isGenericRuntime = /^(node|bun)(\.exe)?$/.test(execName);
  if (!isGenericRuntime) {
    return { command: process.execPath, args };
  }
  return { command: "pi", args };
}

function buildAgentArgs(agent: AgentConfig, promptPath: string, task: string): string[] {
  const args = ["--mode", "json", "-p", "--no-session", "--approve"];
  if (agent.model) args.push("--model", agent.model);
  if (agent.tools && agent.tools.length > 0) args.push("--tools", agent.tools.join(","));
  if (agent.thinking) args.push("--thinking", agent.thinking);
  if (!agent.inheritProjectContext) args.push("--no-context-files");
  if (!agent.inheritSkills) args.push("--no-skills");
  if (agent.systemPromptMode === "append") {
    args.push("--append-system-prompt", promptPath);
  } else {
    args.push("--system-prompt", promptPath);
  }
  args.push(`Task: ${task}`);
  return args;
}

function parseJsonLine(line: string): any | null {
  if (!line.trim()) return null;
  try {
    return JSON.parse(line);
  } catch {
    return null;
  }
}

async function runSingleAgent(
  defaultCwd: string,
  agents: AgentConfig[],
  agentName: string,
  task: string,
  cwd: string | undefined,
  signal: AbortSignal | undefined,
): Promise<SingleResult> {
  const agent = agents.find((a) => a.name === agentName);
  if (!agent) {
    return {
      agent: agentName,
      agentSource: "unknown",
      task,
      exitCode: 1,
      messages: [],
      stderr: `Unknown agent: "${agentName}". Available agents: ${formatAgentList(agents)}.`,
      usage: emptyUsage(),
    };
  }

  const currentResult: SingleResult = {
    agent: agentName,
    agentSource: agent.source,
    task,
    exitCode: 0,
    messages: [],
    stderr: "",
    usage: emptyUsage(),
    model: agent.model,
  };

  let tmpPromptDir: string | null = null;
  let tmpPromptPath: string | null = null;
  try {
    if (agent.systemPrompt.trim()) {
      const tmp = await writePromptToTempFile(agent.name, agent.systemPrompt);
      tmpPromptDir = tmp.dir;
      tmpPromptPath = tmp.filePath;
    }
    const args = buildAgentArgs(agent, tmpPromptPath ?? "", task);
    let wasAborted = false;

    const exitCode = await new Promise<number>((resolve) => {
      const invocation = getPiInvocation(args);
      const proc = spawn(invocation.command, invocation.args, {
        cwd: cwd ?? defaultCwd,
        shell: false,
        stdio: ["ignore", "pipe", "pipe"],
      });
      let buffer = "";

      const processLine = (line: string) => {
        const event = parseJsonLine(line);
        if (!event) return;
        if (event.type === "message_end" && event.message) {
          const msg = event.message as Message;
          currentResult.messages.push(msg);
          if (msg.role === "assistant") {
            currentResult.usage.turns++;
            const usage = msg.usage;
            if (usage) {
              currentResult.usage.input += usage.input || 0;
              currentResult.usage.output += usage.output || 0;
              currentResult.usage.cacheRead += usage.cacheRead || 0;
              currentResult.usage.cacheWrite += usage.cacheWrite || 0;
              currentResult.usage.cost += usage.cost?.total || 0;
              currentResult.usage.contextTokens = usage.totalTokens || 0;
            }
            if (!currentResult.model && msg.model) currentResult.model = msg.model;
            if (msg.stopReason) currentResult.stopReason = msg.stopReason;
            if (msg.errorMessage) currentResult.errorMessage = msg.errorMessage;
          }
        } else if (event.type === "tool_result_end" && event.message) {
          currentResult.messages.push(event.message as Message);
        }
      };

      proc.stdout.on("data", (data) => {
        buffer += data.toString();
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) processLine(line);
      });

      proc.stderr.on("data", (data) => {
        currentResult.stderr += data.toString();
      });

      proc.on("close", (code) => {
        if (buffer.trim()) processLine(buffer);
        resolve(code ?? 0);
      });

      proc.on("error", () => resolve(1));

      if (signal) {
        const killProc = () => {
          wasAborted = true;
          proc.kill("SIGTERM");
          setTimeout(() => {
            if (!proc.killed) proc.kill("SIGKILL");
          }, KILL_GRACE_MS);
        };
        if (signal.aborted) killProc();
        else signal.addEventListener("abort", killProc, { once: true });
      }
    });

    currentResult.exitCode = exitCode;
    if (wasAborted) throw new Error("Subagent was aborted");
    return currentResult;
  } finally {
    if (tmpPromptPath)
      try {
        fs.unlinkSync(tmpPromptPath);
      } catch {
        /* ignore */
      }
    if (tmpPromptDir)
      try {
        fs.rmdirSync(tmpPromptDir);
      } catch {
        /* ignore */
      }
  }
}

function truncateOutput(output: string): string {
  const byteLength = Buffer.byteLength(output, "utf8");
  if (byteLength <= PER_TASK_OUTPUT_CAP) return output;
  let truncated = output.slice(0, PER_TASK_OUTPUT_CAP);
  while (Buffer.byteLength(truncated, "utf8") > PER_TASK_OUTPUT_CAP) {
    truncated = truncated.slice(0, -1);
  }
  return `${truncated}\n\n[Output truncated: ${byteLength - Buffer.byteLength(truncated, "utf8")} bytes omitted.]`;
}

const AgentScopeSchema = StringEnum(["project", "both"] as const, {
  description: 'Agent scope. Default: "project" (this repository\'s .pi/agents).',
  default: "project",
});

const SubagentParams = Type.Object({
  action: Type.Optional(
    StringEnum(["list", "run"] as const, {
      description: '"list" discovers agents; "run" (default) dispatches one agent.',
      default: "run",
    }),
  ),
  agent: Type.Optional(Type.String({ description: "Name of the agent to invoke (run mode)" })),
  task: Type.Optional(Type.String({ description: "Complete task contract for the agent (run mode)" })),
  cwd: Type.Optional(Type.String({ description: "Working directory for the agent process (default: caller cwd)" })),
  async: Type.Optional(
    Type.Boolean({
      description:
        "Run in the background: returns immediately with a log path; poll the log for completion.",
      default: false,
    }),
  ),
  agentScope: Type.Optional(AgentScopeSchema),
});

export default function projectSubagent(pi: ExtensionAPI): void {
  pi.registerTool({
    name: "subagent",
    label: "Subagent",
    description: [
      "Delegate a complete task contract to a project-local agent (.pi/agents/*.md) in an isolated pi subprocess.",
      "Modes: action \"list\" (discover agents) or action \"run\" with agent + task.",
      "Pass cwd from project_worktree for candidate-worktree dispatch.",
      "async: true returns immediately with a log file path; poll it for completion.",
      `Default agent scope is "project".`,
    ].join(" "),
    parameters: SubagentParams,

    async execute(_toolCallId, params, signal, _onUpdate, ctx) {
      try {
        return await this.executeInner(params, signal, ctx);
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `subagent internal error: ${(error as Error).stack || String(error)}`,
            },
          ],
          details: { mode: "error" },
          isError: true,
        };
      }
    },

    async executeInner(params, signal, ctx) {
      const scope: AgentScope = params.agentScope ?? "project";
      const agents = discoverAgents(ctx.cwd, scope);

      if (params.action === "list") {
        return {
          content: [{ type: "text", text: formatAgentList(agents) }],
          details: { mode: "list", agentScope: scope, agents: agents.map((a) => a.name) },
        };
      }

      if (!params.agent || !params.task) {
        return {
          content: [{ type: "text", text: `Invalid parameters. Provide agent + task. Available agents: ${formatAgentList(agents)}` }],
          details: { mode: "run", agentScope: scope },
        };
      }

      const agent = agents.find((a) => a.name === params.agent);
      if (!agent) {
        return {
          content: [{ type: "text", text: `Unknown agent: "${params.agent}". Available agents: ${formatAgentList(agents)}` }],
          details: { mode: "run", agentScope: scope },
          isError: true,
        };
      }

      const targetCwd = params.cwd ?? ctx.cwd;

      if (params.async) {
        // Background run: detached subprocess, output streamed to a log file.
        const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
        const safeName = params.agent.replace(/[^\w.-]+/g, "_");
        const logPath = path.join(os.tmpdir(), `pi-subagent-${safeName}-${timestamp}.log`);
        let promptPath: string | null = null;
        try {
          const tmp = await writePromptToTempFile(params.agent, agent.systemPrompt);
          promptPath = tmp.filePath;
          const args = buildAgentArgs(agent, promptPath, params.task);
          const invocation = getPiInvocation(args);
          const logFd = fs.openSync(logPath, "w", 0o600);
          const proc = spawn(invocation.command, invocation.args, {
            cwd: targetCwd,
            shell: false,
            detached: true,
            stdio: ["ignore", logFd, logFd],
          });
          proc.on("close", () => {
            fs.closeSync(logFd);
            try {
              fs.unlinkSync(promptPath!);
            } catch {
              /* ignore */
            }
          });
          proc.unref();
          return {
            content: [
              {
                type: "text",
                text: `Subagent "${params.agent}" started in background (pid ${proc.pid}). Log: ${logPath}`,
              },
            ],
            details: { mode: "run", async: true, agent: params.agent, cwd: targetCwd, logPath, pid: proc.pid },
          };
        } catch (error) {
          if (promptPath)
            try {
              fs.unlinkSync(promptPath);
            } catch {
              /* ignore */
            }
          return {
            content: [{ type: "text", text: `Failed to start async subagent: ${String(error)}` }],
            details: { mode: "run", async: true, agent: params.agent },
            isError: true,
          };
        }
      }

      const result = await runSingleAgent(targetCwd, agents, params.agent, params.task, undefined, signal);
      if (isFailedResult(result)) {
        return {
          content: [{ type: "text", text: `Agent ${result.stopReason || "failed"}: ${getResultOutput(result)}` }],
          details: { mode: "run", agentScope: scope, result: { ...result, messages: undefined } },
          isError: true,
        };
      }
      return {
        content: [{ type: "text", text: truncateOutput(getResultOutput(result)) }],
        details: { mode: "run", agentScope: scope, result: { ...result, messages: undefined } },
      };
    },
  });
}
