import { prisma } from "@/lib/db/client";
import type { WorkspaceRole } from "@/app/generated/prisma/enums";

// Every API route must call this before touching workspace-scoped data —
// membership is never inferred from the UI (security-architecture.md
// "Authentification / autorisation").
export async function getMembership(workspaceId: string, userId: string) {
  return prisma.workspaceMember.findUnique({
    where: { workspaceId_userId: { workspaceId, userId } },
  });
}

export async function requireMembership(
  workspaceId: string,
  userId: string,
  minRole?: WorkspaceRole
): Promise<{ role: WorkspaceRole }> {
  const membership = await getMembership(workspaceId, userId);
  if (!membership) {
    throw new Error(`User ${userId} is not a member of workspace ${workspaceId}`);
  }
  if (minRole === "owner" && membership.role !== "owner") {
    throw new Error(`User ${userId} must be an owner of workspace ${workspaceId}`);
  }
  return membership;
}
