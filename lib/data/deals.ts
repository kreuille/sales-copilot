import { prisma } from "@/lib/db/client";
import { NotFoundInWorkspaceError } from "@/lib/data/errors";
import { listAgentRunsForDeal } from "@/lib/data/agent-runs";
import { flattenOutputForHandoff } from "@/lib/prompt-engine/format-output";
import type { DealStage } from "@/app/generated/prisma/enums";

export interface CreateDealInput {
  prospectId: string;
  stage: DealStage;
  estimatedAmount?: number;
}

// Matches the vocabulary the source prompts themselves use (agent-05,
// agent-16...) — "premier contact", not our DB enum spelling.
export const DEAL_STAGE_LABELS: Record<DealStage, string> = {
  first_contact: "premier contact",
  after_demo: "après démo",
  proposal_sent: "propale envoyée",
  closing: "closing",
  lost: "perdu",
  won: "gagné",
};

export async function listDeals(workspaceId: string) {
  return prisma.deal.findMany({
    where: { workspaceId },
    orderBy: { lastActionAt: "desc" },
  });
}

export async function listDealsForProspect(workspaceId: string, prospectId: string) {
  return prisma.deal.findMany({
    where: { workspaceId, prospectId },
    orderBy: { lastActionAt: "desc" },
  });
}

export async function getDeal(workspaceId: string, dealId: string) {
  const deal = await prisma.deal.findFirst({
    where: { id: dealId, workspaceId },
  });
  if (!deal) {
    throw new NotFoundInWorkspaceError("Deal", dealId);
  }
  return deal;
}

export async function createDeal(workspaceId: string, input: CreateDealInput) {
  return prisma.deal.create({
    data: { workspaceId, ...input, lastActionAt: new Date() },
  });
}

// Auto-generated default for `deal_history`-sourced content_block fields
// (the deal's current stage + its most recent successful agent outputs,
// flattened) — always editable by the user before a run, exactly like an
// upstream-agent handoff pre-fill.
export async function getDealHistorySummary(workspaceId: string, dealId: string) {
  const deal = await getDeal(workspaceId, dealId);
  const runs = await listAgentRunsForDeal(workspaceId, dealId);
  const lines = [`Étape actuelle du deal : ${DEAL_STAGE_LABELS[deal.stage]}`];

  const recentSucceeded = runs.filter((r) => r.status === "succeeded").slice(0, 3);
  for (const run of recentSucceeded) {
    lines.push(
      `--- ${run.agentPromptVersion.agent.name} (${run.createdAt.toLocaleDateString("fr-FR")}) ---`
    );
    lines.push(flattenOutputForHandoff(run.outputPayload));
  }
  return lines.join("\n");
}

// Stage changes are insert-only (DealStageEvent is never updated) —
// data-architecture.md "Historique immuable".
export async function transitionDealStage(
  workspaceId: string,
  dealId: string,
  toStage: DealStage
) {
  const deal = await getDeal(workspaceId, dealId);
  return prisma.$transaction([
    prisma.deal.update({
      where: { id: deal.id },
      data: { stage: toStage, lastActionAt: new Date() },
    }),
    prisma.dealStageEvent.create({
      data: { dealId: deal.id, fromStage: deal.stage, toStage },
    }),
  ]);
}
