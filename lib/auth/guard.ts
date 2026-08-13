import { auth } from "@/auth";
import { requireMembership } from "@/lib/data/workspace-members";
import type { WorkspaceRole } from "@/app/generated/prisma/enums";

export class UnauthenticatedError extends Error {
  constructor() {
    super("No authenticated session");
    this.name = "UnauthenticatedError";
  }
}

// Single entry point every API route must call before touching
// workspace-scoped data: resolves the session server-side (never trusts a
// client-supplied user id) and verifies workspace membership via the data
// access layer (security-architecture.md "Authentification / autorisation" —
// "jamais de vérification uniquement côté UI").
export async function requireWorkspaceSession(workspaceId: string, minRole?: WorkspaceRole) {
  const session = await auth();
  const userId = session?.user?.id;
  if (!userId) {
    throw new UnauthenticatedError();
  }
  const membership = await requireMembership(workspaceId, userId, minRole);
  return { userId, role: membership.role };
}
