import { prisma } from "@/lib/db/client";
import type { AgentScope } from "@/app/generated/prisma/enums";

// Agent/AgentPromptVersion are global registry data, not workspace-scoped
// (no workspace_id column — see data-architecture.md), so unlike the rest of
// lib/data/* these lookups take no workspaceId.

// Drives the prospect/deal/workspace pages — each renders exactly the
// agents whose scope matches, sorted by function so related agents group
// together, with zero per-page hardcoding of which agent goes where.
export async function listActiveAgentsByScope(scope: AgentScope) {
  const agents = await prisma.agent.findMany({
    where: { scope },
    include: { promptVersions: { where: { isActive: true }, take: 1 } },
    orderBy: [{ functionId: "asc" }, { code: "asc" }],
  });
  return agents
    .filter((agent) => agent.promptVersions.length > 0)
    .map((agent) => ({ agent, promptVersion: agent.promptVersions[0] }));
}

export async function getActiveAgentPromptVersion(agentCode: string) {
  const agent = await prisma.agent.findUnique({
    where: { code: agentCode },
    include: { promptVersions: { where: { isActive: true }, take: 1 } },
  });
  const promptVersion = agent?.promptVersions[0];
  if (!agent || !promptVersion) {
    throw new Error(`No active prompt version for agent ${agentCode}`);
  }
  return { agent, promptVersion };
}
