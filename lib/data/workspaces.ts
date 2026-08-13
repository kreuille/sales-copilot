import { prisma } from "@/lib/db/client";

export async function createWorkspaceWithOwner(userId: string, name: string) {
  return prisma.$transaction(async (tx) => {
    const workspace = await tx.workspace.create({ data: { name } });
    await tx.workspaceMember.create({
      data: { workspaceId: workspace.id, userId, role: "owner" },
    });
    return workspace;
  });
}

export async function getFirstWorkspaceForUser(userId: string) {
  const membership = await prisma.workspaceMember.findFirst({
    where: { userId },
    include: { workspace: true },
    orderBy: { id: "asc" },
  });
  return membership?.workspace ?? null;
}
