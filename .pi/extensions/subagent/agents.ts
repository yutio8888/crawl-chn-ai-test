/**
 * Project-local agent discovery for the subagent tool.
 *
 * Discovers agents from the nearest `.pi/agents/*.md` directory by walking
 * upward from the caller's cwd (repository-root-relative, per the project
 * path-portability policy). Each agent file uses YAML frontmatter:
 *
 *   name, description (required); tools, model, thinking,
 *   systemPromptMode (replace|append), inheritProjectContext,
 *   inheritSkills (optional).
 *
 * The body after the frontmatter becomes the agent system prompt.
 */

import * as fs from "node:fs";
import * as path from "node:path";
import { CONFIG_DIR_NAME, getAgentDir, parseFrontmatter } from "@earendil-works/pi-coding-agent";

export type AgentScope = "project" | "both";

export interface AgentConfig {
  name: string;
  description: string;
  tools?: string[];
  model?: string;
  thinking?: string;
  systemPromptMode: "replace" | "append";
  inheritProjectContext: boolean;
  inheritSkills: boolean;
  systemPrompt: string;
  source: "project";
  filePath: string;
}

function parseBool(value: unknown): boolean {
  // parseFrontmatter parses YAML booleans as real booleans, not strings.
  if (typeof value === "boolean") return value;
  if (typeof value === "string") return value.trim().toLowerCase() !== "false";
  return true;
}

function loadAgentsFromDir(dir: string): AgentConfig[] {
  const agents: AgentConfig[] = [];
  if (!fs.existsSync(dir)) return agents;

  let entries: fs.Dirent[];
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return agents;
  }

  for (const entry of entries) {
    if (!entry.name.endsWith(".md")) continue;
    if (!entry.isFile() && !entry.isSymbolicLink()) continue;

    const filePath = path.join(dir, entry.name);
    let content: string;
    try {
      content = fs.readFileSync(filePath, "utf-8");
    } catch {
      continue;
    }

    const { frontmatter, body } = parseFrontmatter<Record<string, string>>(content);
    if (!frontmatter.name || !frontmatter.description) continue;

    const tools = frontmatter.tools
      ?.split(",")
      .map((t: string) => t.trim())
      .filter(Boolean);

    agents.push({
      name: frontmatter.name,
      description: frontmatter.description,
      tools: tools && tools.length > 0 ? tools : undefined,
      model: frontmatter.model,
      thinking: frontmatter.thinking,
      systemPromptMode: frontmatter.systemPromptMode === "append" ? "append" : "replace",
      inheritProjectContext: parseBool(frontmatter.inheritProjectContext),
      inheritSkills: parseBool(frontmatter.inheritSkills),
      systemPrompt: body,
      source: "project",
      filePath,
    });
  }
  return agents;
}

function isDirectory(p: string): boolean {
  try {
    return fs.statSync(p).isDirectory();
  } catch {
    return false;
  }
}

function findNearestProjectAgentsDir(cwd: string): string | null {
  let currentDir = cwd;
  while (true) {
    const candidate = path.join(currentDir, CONFIG_DIR_NAME, "agents");
    if (isDirectory(candidate)) return candidate;
    const parentDir = path.dirname(currentDir);
    if (parentDir === currentDir) return null;
    currentDir = parentDir;
  }
}

export function discoverAgents(cwd: string, scope: AgentScope): AgentConfig[] {
  const projectAgentsDir = findNearestProjectAgentsDir(cwd);
  const projectAgents = projectAgentsDir ? loadAgentsFromDir(projectAgentsDir) : [];

  if (scope === "project") return projectAgents;

  // scope === "both": user agents first, then project agents override by name.
  const userDir = path.join(getAgentDir(), "agents");
  const userAgents = loadAgentsFromDir(userDir);
  const agentMap = new Map<string, AgentConfig>();
  for (const agent of userAgents) agentMap.set(agent.name, agent);
  for (const agent of projectAgents) agentMap.set(agent.name, agent);
  return Array.from(agentMap.values());
}

export function formatAgentList(agents: AgentConfig[]): string {
  if (agents.length === 0) return "none";
  return agents
    .map((a) => `${a.name} (${a.source}): ${a.description}${a.model ? ` [${a.model}]` : ""}`)
    .join("; ");
}
