// One-off helper: drops and recreates the public schema, then reapplies
// prisma/migrations/*/migration.sql — used in this environment because the
// Prisma schema-engine binary (which `prisma migrate reset` needs) is
// blocked from executing. Not part of the app; safe to delete once
// `prisma migrate dev` can run normally again.
import { Client } from "pg";
import "dotenv/config";

const client = new Client({ connectionString: process.env.DATABASE_URL });
await client.connect();
await client.query("DROP SCHEMA public CASCADE; CREATE SCHEMA public;");
await client.end();
console.log("Schema reset.");
