import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "@/app/generated/prisma/client";

// Driver adapter (node-postgres) instead of Prisma's default binary query
// engine: this environment blocks execution of freshly-downloaded native
// binaries, and the adapter talks to Postgres over the wire instead of
// spawning a sidecar process.
declare global {
  var __prisma: PrismaClient | undefined;
}

function createClient() {
  const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });
  return new PrismaClient({ adapter });
}

export const prisma = globalThis.__prisma ?? createClient();

if (process.env.NODE_ENV !== "production") {
  globalThis.__prisma = prisma;
}
