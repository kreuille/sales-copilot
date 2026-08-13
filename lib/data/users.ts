import { prisma } from "@/lib/db/client";
import { hashPassword } from "@/lib/auth/password";

// Not workspace-scoped: a user can belong to several workspaces
// (WorkspaceMember is the join), so lookups here are keyed by email/id only.
export async function getUserByEmail(email: string) {
  return prisma.user.findUnique({ where: { email } });
}

export async function createUser(input: { email: string; password: string; name?: string }) {
  const passwordHash = await hashPassword(input.password);
  return prisma.user.create({
    data: { email: input.email, name: input.name, passwordHash },
  });
}
