// One-off helper: applies prisma/migrations/*/migration.sql files in order
// via node-postgres, bypassing the Prisma schema-engine binary (blocked in
// this environment). Not part of the app; safe to delete once `prisma
// migrate dev` can run normally again.
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { Client } from "pg";
import "dotenv/config";

const migrationsDir = join(import.meta.dirname, "..", "prisma", "migrations");
const dirs = readdirSync(migrationsDir, { withFileTypes: true })
  .filter((d) => d.isDirectory())
  .map((d) => d.name)
  .sort();

const client = new Client({ connectionString: process.env.DATABASE_URL });
await client.connect();

for (const dir of dirs) {
  const sql = readFileSync(join(migrationsDir, dir, "migration.sql"), "utf8");
  console.log(`Applying ${dir}...`);
  await client.query(sql);
}

await client.end();
console.log("Done.");
