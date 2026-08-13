import { prisma } from "@/lib/db/client";
import { NotFoundInWorkspaceError } from "@/lib/data/errors";

export interface CreateProspectInput {
  fullName: string;
  company?: string;
  roleTitle?: string;
  rawNotes?: string;
}

// Every function here takes workspaceId as the first argument and folds it
// into the Prisma `where` clause — no route/API code queries Prospect
// directly (ADR-003, security-architecture.md "Isolation des données").
export async function listProspects(workspaceId: string) {
  return prisma.prospect.findMany({
    where: { workspaceId },
    orderBy: { createdAt: "desc" },
  });
}

export async function getProspect(workspaceId: string, prospectId: string) {
  const prospect = await prisma.prospect.findFirst({
    where: { id: prospectId, workspaceId },
  });
  if (!prospect) {
    throw new NotFoundInWorkspaceError("Prospect", prospectId);
  }
  return prospect;
}

export async function createProspect(workspaceId: string, input: CreateProspectInput) {
  return prisma.prospect.create({
    data: { workspaceId, ...input },
  });
}
