import { prisma } from "@/lib/db/client";
import type { Prisma } from "@/app/generated/prisma/client";
import type { AgentRunStatus } from "@/app/generated/prisma/enums";

// {} means workspace-scoped (no prospect/deal attached) — Prisma matches
// that against prospectId/dealId IS NULL, which is exactly how
// workspace-scoped AgentRun rows are stored.
export type AgentRunEntityRef = { prospectId?: string; dealId?: string };

export interface CreateAgentRunInput {
  agentPromptVersionId: string;
  triggeredByUserId: string;
  prospectId?: string;
  dealId?: string;
  inputPayload: Prisma.InputJsonValue;
  outputPayload?: Prisma.InputJsonValue;
  modelUsed: string;
  tokensIn?: number;
  tokensOut?: number;
  estimatedCost?: number;
  status: AgentRunStatus;
}

// FR-7 history/audit: list every AgentRun for a prospect or deal, scoped to
// the workspace so a run from another workspace can never leak through even
// if a prospectId/dealId were guessed or reused.
export async function listAgentRunsForProspect(workspaceId: string, prospectId: string) {
  return prisma.agentRun.findMany({
    where: { workspaceId, prospectId },
    orderBy: { createdAt: "desc" },
    include: { agentPromptVersion: { include: { agent: true } } },
  });
}

export async function listAgentRunsForDeal(workspaceId: string, dealId: string) {
  return prisma.agentRun.findMany({
    where: { workspaceId, dealId },
    orderBy: { createdAt: "desc" },
    include: { agentPromptVersion: { include: { agent: true } } },
  });
}

// Generic version of the two functions above, keyed by an entity ref instead
// of a specific column — used by AgentSection so the same component works
// for prospect-, deal-, and workspace-scoped agents.
export async function listAgentRunsForEntity(workspaceId: string, entityRef: AgentRunEntityRef) {
  return prisma.agentRun.findMany({
    where: {
      workspaceId,
      prospectId: entityRef.prospectId ?? null,
      dealId: entityRef.dealId ?? null,
    },
    orderBy: { createdAt: "desc" },
    include: { agentPromptVersion: { include: { agent: true } } },
  });
}

// Handoff pre-fill lookup (FR-4.2): the latest successful run of a given
// agent for this exact entity — a prospect's Agent 1 run never pre-fills a
// different prospect's Agent 2 form, a deal's Agent 7 run never leaks into a
// workspace-level agent, etc.
export async function getLatestSucceededRun(
  workspaceId: string,
  agentCode: string,
  entityRef: AgentRunEntityRef
) {
  return prisma.agentRun.findFirst({
    where: {
      workspaceId,
      prospectId: entityRef.prospectId ?? null,
      dealId: entityRef.dealId ?? null,
      status: "succeeded",
      agentPromptVersion: { agent: { code: agentCode } },
    },
    orderBy: { createdAt: "desc" },
  });
}

// Display lookup (any status, not just succeeded) — AgentSection uses this
// to show "here's what the last run of this agent produced", including
// failed/validation_error runs so the user isn't left guessing.
export async function getLatestRunForAgent(
  workspaceId: string,
  agentCode: string,
  entityRef: AgentRunEntityRef
) {
  return prisma.agentRun.findFirst({
    where: {
      workspaceId,
      prospectId: entityRef.prospectId ?? null,
      dealId: entityRef.dealId ?? null,
      agentPromptVersion: { agent: { code: agentCode } },
    },
    orderBy: { createdAt: "desc" },
  });
}

// AgentRun is insert-only (security-architecture.md audit log) — no update
// function is exposed here on purpose.
export async function createAgentRun(workspaceId: string, input: CreateAgentRunInput) {
  return prisma.agentRun.create({
    data: { workspaceId, ...input },
  });
}
