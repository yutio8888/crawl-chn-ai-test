/**
 * Project subagent tool — delegate tasks to project-local agents
 * (.pi/agents/*.md) in isolated `pi` subprocesses.
 *
 * Adapted from the official pi-coding-agent subagent example with the
 * project's documented interface and defaults:
 *
 *   subagent({ action: "list" })                         -> discover agents
 *   subagent({ agent: "crawl-coder", task: "..." })      -> single run
 *   subagent({ agent: "...", task: "...", cwd })         -> worktree dispatch
 *   subagent({ agent: "...", task: "...", async: true }) -> background run,
 *                                                            live TUI progress,
 *                                                            and a full log file
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

import { spawn, type ChildProcess } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { StringDecoder } from "node:string_decoder";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import type { Message } from "@earendil-works/pi-ai";
import { StringEnum } from "@earendil-works/pi-ai";
import { Type } from "typebox";
import { type AgentConfig, type AgentScope, discoverAgents, formatAgentList } from "./agents.ts";
import {
  applySubagentEvent,
  getDisplayItems,
  getResultOutput,
  isFailedResult,
} from "./live-output.mjs";

const PER_TASK_OUTPUT_CAP = 50 * 1024;
const KILL_GRACE_MS = 5000;
const SHUTDOWN_WAIT_MS = KILL_GRACE_MS + 2000;
const LIVE_UPDATE_INTERVAL_MS = 120;
const BACKGROUND_COMPLETION_TTL_MS = 30_000;
const BACKGROUND_WIDGET_KEY = "subagent-background";
const BACKGROUND_STATUS_KEY = "subagent-background-status";
const BACKGROUND_VISIBLE_JOBS = 4;
const BACKGROUND_VISIBLE_ITEMS = 4;

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
  streamingText?: string;
  settled?: boolean;
}

interface RunSingleAgentOptions {
  signal?: AbortSignal;
  onUpdate?: (result: SingleResult) => void;
  onSpawn?: (process: ChildProcess) => void;
  logPath?: string;
}

type BackgroundStatus = "starting" | "running" | "completed" | "failed" | "aborted";

interface BackgroundJob {
  id: string;
  agent: string;
  cwd: string;
  logPath: string;
  controller: AbortController;
  result: SingleResult;
  status: BackgroundStatus;
  pid?: number;
  process?: ChildProcess;
  started: boolean;
  done?: Promise<void>;
  completionTimer?: ReturnType<typeof setTimeout>;
}

function emptyUsage(): UsageStats {
  return { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, cost: 0, contextTokens: 0, turns: 0 };
}

function initialResult(agent: AgentConfig, task: string): SingleResult {
  return {
    agent: agent.name,
    agentSource: agent.source,
    task,
    exitCode: -1,
    messages: [],
    stderr: "",
    usage: emptyUsage(),
    model: agent.model,
  };
}

function serializableResult(result: SingleResult): Omit<SingleResult, "messages" | "streamingText"> {
  const { messages: _messages, streamingText: _streamingText, ...details } = result;
  return details;
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

function parseJsonLine(line: string): Record<string, unknown> | null {
  if (!line.trim()) return null;
  try {
    return JSON.parse(line) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function formatToolCall(toolName: string, args: Record<string, unknown>): string {
  const shortenPath = (value: string) => {
    const home = os.homedir();
    return value.startsWith(home) ? `~${value.slice(home.length)}` : value;
  };

  switch (toolName) {
    case "bash": {
      const command = String(args.command || "...");
      return `$ ${command.length > 100 ? `${command.slice(0, 100)}…` : command}`;
    }
    case "read": {
      const filePath = shortenPath(String(args.file_path || args.path || "..."));
      const offset = typeof args.offset === "number" ? args.offset : undefined;
      const limit = typeof args.limit === "number" ? args.limit : undefined;
      if (offset === undefined && limit === undefined) return `read ${filePath}`;
      const start = offset ?? 1;
      const end = limit === undefined ? "" : `-${start + limit - 1}`;
      return `read ${filePath}:${start}${end}`;
    }
    case "write":
    case "edit":
      return `${toolName} ${shortenPath(String(args.file_path || args.path || "..."))}`;
    case "ls":
      return `ls ${shortenPath(String(args.path || "."))}`;
    case "find":
      return `find ${String(args.pattern || "*")} in ${shortenPath(String(args.path || "."))}`;
    case "grep":
      return `grep /${String(args.pattern || "")}/ in ${shortenPath(String(args.path || "."))}`;
    default: {
      const encoded = JSON.stringify(args);
      const preview = encoded.length > 100 ? `${encoded.slice(0, 100)}…` : encoded;
      return `${toolName} ${preview}`;
    }
  }
}

function previewText(text: string, maxLines: number): string[] {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trimEnd())
    .filter((line) => line.trim());
  return lines.slice(-maxLines).map((line) => (line.length > 240 ? `${line.slice(0, 240)}…` : line));
}

function liveProgressLines(result: SingleResult, maxItems: number): string[] {
  const items = getDisplayItems(result).slice(-maxItems);
  const lines: string[] = [];
  for (const item of items) {
    if (item.type === "toolCall") {
      lines.push(`→ ${formatToolCall(item.name, item.args)}`);
    } else {
      const textLines = previewText(item.text, item.streaming ? 3 : 2);
      lines.push(...textLines.map((line) => `${item.streaming ? "…" : " "} ${line}`));
    }
  }
  if (lines.length === 0) lines.push("(running…)");
  return lines;
}

function foregroundProgress(result: SingleResult): string {
  return [`⏳ ${result.agent}`, ...liveProgressLines(result, 10)].join("\n");
}

function backgroundStatusIcon(status: BackgroundStatus): string {
  if (status === "completed") return "✓";
  if (status === "failed" || status === "aborted") return "✗";
  return "⏳";
}

function updateBackgroundUi(ctx: ExtensionContext, jobs: Map<string, BackgroundJob>): void {
  if (!ctx.hasUI) return;
  try {
    const visibleJobs = Array.from(jobs.values()).slice(-BACKGROUND_VISIBLE_JOBS);
    if (visibleJobs.length === 0) {
      ctx.ui.setWidget(BACKGROUND_WIDGET_KEY, undefined);
      ctx.ui.setStatus(BACKGROUND_STATUS_KEY, undefined);
      return;
    }

    const running = visibleJobs.filter((job) => job.status === "starting" || job.status === "running").length;
    const lines = [`Subagents: ${running} running`];
    for (const job of visibleJobs) {
      const pid = job.pid === undefined ? "starting" : `pid ${job.pid}`;
      lines.push(`${backgroundStatusIcon(job.status)} ${job.agent} (${pid})`);
      lines.push(...liveProgressLines(job.result, BACKGROUND_VISIBLE_ITEMS).map((line) => `  ${line}`));
      if (job.status !== "running" && job.status !== "starting") lines.push(`  log: ${job.logPath}`);
    }
    ctx.ui.setWidget(BACKGROUND_WIDGET_KEY, lines, { placement: "belowEditor" });
    ctx.ui.setStatus(
      BACKGROUND_STATUS_KEY,
      running > 0 ? ctx.ui.theme.fg("accent", `${running} subagent${running === 1 ? "" : "s"}`) : undefined,
    );
  } catch {
    // Session replacement can invalidate a captured background UI context.
  }
}

async function runSingleAgent(
  defaultCwd: string,
  agents: AgentConfig[],
  agentName: string,
  task: string,
  cwd: string | undefined,
  options: RunSingleAgentOptions = {},
): Promise<SingleResult> {
  const agent = agents.find((candidate) => candidate.name === agentName);
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

  const currentResult: SingleResult = initialResult(agent, task);
  let tmpPromptDir: string | null = null;
  let tmpPromptPath: string | null = null;
  let logFd: number | null = null;
  let updateTimer: ReturnType<typeof setTimeout> | undefined;

  const emitUpdate = () => {
    if (!options.onUpdate) return;
    try {
      options.onUpdate(currentResult);
    } catch {
      // A stale UI context must not stop the delegated process.
    }
  };
  const flushUpdate = () => {
    if (updateTimer) clearTimeout(updateTimer);
    updateTimer = undefined;
    emitUpdate();
  };
  const scheduleUpdate = () => {
    if (!options.onUpdate || updateTimer) return;
    updateTimer = setTimeout(() => {
      updateTimer = undefined;
      emitUpdate();
    }, LIVE_UPDATE_INTERVAL_MS);
    updateTimer.unref?.();
  };
  const writeLog = (data: Buffer | string) => {
    if (logFd === null) return;
    try {
      fs.writeSync(logFd, data);
    } catch {
      // Preserve the agent run even if its diagnostic log becomes unwritable.
    }
  };

  try {
    if (agent.systemPrompt.trim()) {
      const tmp = await writePromptToTempFile(agent.name, agent.systemPrompt);
      tmpPromptDir = tmp.dir;
      tmpPromptPath = tmp.filePath;
    }
    if (options.logPath) logFd = fs.openSync(options.logPath, "wx", 0o600);

    const args = buildAgentArgs(agent, tmpPromptPath ?? "", task);
    let wasAborted = false;

    const exitCode = await new Promise<number>((resolve) => {
      const invocation = getPiInvocation(args);
      const proc = spawn(invocation.command, invocation.args, {
        cwd: cwd ?? defaultCwd,
        shell: false,
        stdio: ["ignore", "pipe", "pipe"],
      });
      const stdoutDecoder = new StringDecoder("utf8");
      const stderrDecoder = new StringDecoder("utf8");
      let stdoutBuffer = "";
      let forceKillTimer: ReturnType<typeof setTimeout> | undefined;
      let resolved = false;

      const finish = (code: number) => {
        if (resolved) return;
        resolved = true;
        resolve(code);
      };
      const processLine = (line: string) => {
        const event = parseJsonLine(line);
        if (!event) return;
        if (applySubagentEvent(currentResult, event)) {
          if (event.type === "message_end" || event.type === "agent_settled") flushUpdate();
          else scheduleUpdate();
        }
      };
      const consumeStdout = (text: string) => {
        stdoutBuffer += text;
        const lines = stdoutBuffer.split("\n");
        stdoutBuffer = lines.pop() || "";
        for (const line of lines) processLine(line);
      };
      const killProc = () => {
        if (wasAborted) return;
        wasAborted = true;
        try {
          proc.kill("SIGTERM");
        } catch {
          // Process may have already exited.
        }
        forceKillTimer = setTimeout(() => {
          if (proc.exitCode === null && proc.signalCode === null) {
            try {
              proc.kill("SIGKILL");
            } catch {
              // Process may have exited between the check and kill.
            }
          }
          // A descendant may keep inherited descriptors open after the direct
          // child exits. Closing our pipe ends prevents that from blocking the
          // ChildProcess "close" event and session teardown indefinitely.
          proc.stdout?.destroy();
          proc.stderr?.destroy();
        }, KILL_GRACE_MS);
        forceKillTimer.unref?.();
      };
      const removeAbortListener = () => options.signal?.removeEventListener("abort", killProc);

      proc.once("spawn", () => options.onSpawn?.(proc));
      proc.stdout?.on("data", (data: Buffer) => {
        writeLog(data);
        consumeStdout(stdoutDecoder.write(data));
      });
      proc.stderr?.on("data", (data: Buffer) => {
        writeLog(data);
        currentResult.stderr += stderrDecoder.write(data);
      });
      proc.on("close", (code) => {
        consumeStdout(stdoutDecoder.end());
        currentResult.stderr += stderrDecoder.end();
        if (stdoutBuffer.trim()) processLine(stdoutBuffer);
        if (forceKillTimer) clearTimeout(forceKillTimer);
        removeAbortListener();
        finish(code ?? (wasAborted ? 1 : 0));
      });
      proc.on("error", (error) => {
        currentResult.stderr += `${currentResult.stderr ? "\n" : ""}${error.message}`;
        removeAbortListener();
        finish(1);
      });

      if (options.signal) {
        if (options.signal.aborted) killProc();
        else options.signal.addEventListener("abort", killProc, { once: true });
      }
    });

    currentResult.exitCode = exitCode;
    currentResult.streamingText = "";
    if (wasAborted) {
      currentResult.stopReason = "aborted";
      currentResult.errorMessage = "Subagent was aborted";
    }
    flushUpdate();
    return currentResult;
  } finally {
    if (updateTimer) clearTimeout(updateTimer);
    if (logFd !== null) {
      try {
        fs.closeSync(logFd);
      } catch {
        /* ignore */
      }
    }
    if (tmpPromptPath) {
      try {
        fs.unlinkSync(tmpPromptPath);
      } catch {
        /* ignore */
      }
    }
    if (tmpPromptDir) {
      try {
        fs.rmdirSync(tmpPromptDir);
      } catch {
        /* ignore */
      }
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
      description: "Run in the session background: return immediately, show live TUI progress, and write a full log.",
      default: false,
    }),
  ),
  agentScope: Type.Optional(AgentScopeSchema),
});

export default function projectSubagent(pi: ExtensionAPI): void {
  const backgroundJobs = new Map<string, BackgroundJob>();
  let backgroundSequence = 0;
  let shuttingDown = false;

  pi.on("session_start", async (_event, ctx) => {
    shuttingDown = false;
    updateBackgroundUi(ctx, backgroundJobs);
  });

  pi.on("session_shutdown", async (_event, ctx) => {
    shuttingDown = true;
    const completions: Promise<void>[] = [];
    for (const job of backgroundJobs.values()) {
      if (job.completionTimer) clearTimeout(job.completionTimer);
      if (job.status === "starting" || job.status === "running") job.controller.abort();
      if (job.done) completions.push(job.done);
    }
    try {
      ctx.ui.setWidget(BACKGROUND_WIDGET_KEY, undefined);
      ctx.ui.setStatus(BACKGROUND_STATUS_KEY, undefined);
    } catch {
      // The old session UI may already be invalid during replacement.
    }
    if (completions.length > 0) {
      let shutdownTimer: ReturnType<typeof setTimeout> | undefined;
      const allDone = Promise.allSettled(completions).then(() => false);
      const timedOut = await Promise.race([
        allDone,
        new Promise<boolean>((resolve) => {
          shutdownTimer = setTimeout(() => resolve(true), SHUTDOWN_WAIT_MS);
        }),
      ]);
      if (shutdownTimer) clearTimeout(shutdownTimer);
      if (timedOut) {
        for (const job of backgroundJobs.values()) {
          if (job.status !== "starting" && job.status !== "running") continue;
          job.process?.stdout?.destroy();
          job.process?.stderr?.destroy();
          job.process?.unref();
        }
      }
    }
    backgroundJobs.clear();
  });

  pi.registerTool({
    name: "subagent",
    label: "Subagent",
    description: [
      "Delegate a complete task contract to a project-local agent (.pi/agents/*.md) in an isolated pi subprocess.",
      'Modes: action "list" (discover agents) or action "run" with agent + task.',
      "Pass cwd from project_worktree for candidate-worktree dispatch.",
      "async: true returns immediately, shows live progress in the TUI, and writes complete JSON stdout and stderr output to a log.",
      'Default agent scope is "project".',
    ].join(" "),
    parameters: SubagentParams,

    async execute(_toolCallId, params, signal, onUpdate, ctx) {
      try {
        const scope: AgentScope = params.agentScope ?? "project";
        const agents = discoverAgents(ctx.cwd, scope);

        if (params.action === "list") {
          return {
            content: [{ type: "text", text: formatAgentList(agents) }],
            details: { mode: "list", agentScope: scope, agents: agents.map((agent) => agent.name) },
          };
        }

        if (!params.agent || !params.task) {
          return {
            content: [
              {
                type: "text",
                text: `Invalid parameters. Provide agent + task. Available agents: ${formatAgentList(agents)}`,
              },
            ],
            details: { mode: "run", agentScope: scope },
          };
        }

        const agent = agents.find((candidate) => candidate.name === params.agent);
        if (!agent) {
          return {
            content: [
              {
                type: "text",
                text: `Unknown agent: "${params.agent}". Available agents: ${formatAgentList(agents)}`,
              },
            ],
            details: { mode: "run", agentScope: scope },
            isError: true,
          };
        }

        const targetCwd = params.cwd ?? ctx.cwd;

        if (params.async) {
          const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
          const safeName = params.agent.replace(/[^\w.-]+/g, "_");
          const jobId = `${safeName}-${timestamp}-${++backgroundSequence}`;
          const logPath = path.join(os.tmpdir(), `pi-subagent-${jobId}.log`);
          const controller = new AbortController();
          const job: BackgroundJob = {
            id: jobId,
            agent: params.agent,
            cwd: targetCwd,
            logPath,
            controller,
            result: initialResult(agent, params.task),
            status: "starting",
            started: false,
          };
          backgroundJobs.set(jobId, job);
          updateBackgroundUi(ctx, backgroundJobs);

          let resolveStarted: (pid: number) => void = () => undefined;
          let rejectStarted: (error: Error) => void = () => undefined;
          const started = new Promise<number>((resolve, reject) => {
            resolveStarted = resolve;
            rejectStarted = reject;
          });
          const runPromise = runSingleAgent(targetCwd, agents, params.agent, params.task, undefined, {
            signal: controller.signal,
            logPath,
            onSpawn: (process) => {
              if (process.pid === undefined) return;
              job.pid = process.pid;
              job.process = process;
              job.started = true;
              job.status = "running";
              resolveStarted(process.pid);
              if (!shuttingDown) updateBackgroundUi(ctx, backgroundJobs);
            },
            onUpdate: (result) => {
              job.result = result;
              if (job.status === "starting") job.status = "running";
              if (!shuttingDown) updateBackgroundUi(ctx, backgroundJobs);
            },
          });

          job.done = runPromise.then(
            (result) => {
              job.result = result;
              if (result.stopReason === "aborted") job.status = "aborted";
              else job.status = isFailedResult(result) ? "failed" : "completed";
              if (shuttingDown || !job.started) return;
              updateBackgroundUi(ctx, backgroundJobs);
              try {
                ctx.ui.notify(
                  `Subagent "${job.agent}" ${job.status}. Full log: ${job.logPath}`,
                  job.status === "completed" ? "info" : "error",
                );
              } catch {
                // Session replacement can invalidate a captured background UI context.
              }
              job.completionTimer = setTimeout(() => {
                if (backgroundJobs.get(job.id) !== job || shuttingDown) return;
                backgroundJobs.delete(job.id);
                updateBackgroundUi(ctx, backgroundJobs);
              }, BACKGROUND_COMPLETION_TTL_MS);
              job.completionTimer.unref?.();
            },
            (error) => {
              job.result.exitCode = 1;
              job.result.errorMessage = error instanceof Error ? error.message : String(error);
              job.status = controller.signal.aborted ? "aborted" : "failed";
              if (!shuttingDown) updateBackgroundUi(ctx, backgroundJobs);
            },
          );

          void runPromise.then(
            (result) => {
              if (!job.started) rejectStarted(new Error(getResultOutput(result)));
            },
            (error) => {
              if (!job.started) rejectStarted(error instanceof Error ? error : new Error(String(error)));
            },
          );

          try {
            const pid = await started;
            return {
              content: [
                {
                  type: "text",
                  text: ctx.hasUI
                    ? `Subagent "${params.agent}" started in background (pid ${pid}). Live progress is shown below the editor. Full log: ${logPath}`
                    : `Subagent "${params.agent}" started in background (pid ${pid}). Full log: ${logPath}`,
                },
              ],
              details: {
                mode: "run",
                async: true,
                agentScope: scope,
                agent: params.agent,
                cwd: targetCwd,
                jobId,
                logPath,
                pid,
              },
            };
          } catch (error) {
            await job.done;
            if (job.completionTimer) clearTimeout(job.completionTimer);
            backgroundJobs.delete(jobId);
            updateBackgroundUi(ctx, backgroundJobs);
            return {
              content: [{ type: "text", text: `Failed to start async subagent: ${String(error)}` }],
              details: { mode: "run", async: true, agentScope: scope, agent: params.agent, logPath },
              isError: true,
            };
          }
        }

        const result = await runSingleAgent(targetCwd, agents, params.agent, params.task, undefined, {
          signal,
          onUpdate: (partial) => {
            onUpdate?.({
              content: [{ type: "text", text: foregroundProgress(partial) }],
              details: {
                mode: "run",
                async: false,
                agentScope: scope,
                running: partial.exitCode === -1,
                agent: partial.agent,
                usage: { ...partial.usage },
              },
            });
          },
        });
        if (isFailedResult(result)) {
          return {
            content: [{ type: "text", text: `Agent ${result.stopReason || "failed"}: ${getResultOutput(result)}` }],
            details: { mode: "run", agentScope: scope, result: serializableResult(result) },
            isError: true,
          };
        }
        return {
          content: [{ type: "text", text: truncateOutput(getResultOutput(result)) }],
          details: { mode: "run", agentScope: scope, result: serializableResult(result) },
        };
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
  });
}
