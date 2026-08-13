import { prisma } from "@/lib/db/client";

export interface WorkspaceContextInput {
  offerDescription: string;
  icpDescription: string;
  tone: string;
  pricingSummary?: string;
}

// Returns the current (highest-version) context for the workspace, or null
// if the workspace has never had its context filled in.
export async function getActiveWorkspaceContext(workspaceId: string) {
  return prisma.workspaceContext.findFirst({
    where: { workspaceId },
    orderBy: { version: "desc" },
  });
}

// Context is versioned, never overwritten in place (data-architecture.md
// "Versionnement du contexte workspace") — a new row is always inserted.
export async function createWorkspaceContextVersion(
  workspaceId: string,
  input: WorkspaceContextInput
) {
  const current = await getActiveWorkspaceContext(workspaceId);
  return prisma.workspaceContext.create({
    data: { workspaceId, version: (current?.version ?? 0) + 1, ...input },
  });
}
