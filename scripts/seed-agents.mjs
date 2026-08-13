// Upserts Agent + AgentPromptVersion rows from agents/registry.yaml.
//
// AgentRun has a required FK to AgentPromptVersion, but the prompt text
// itself is versioned data in registry.yaml (ADR-005) — the DB is a mirror
// for referential integrity and runtime queries, not the source of truth.
// Run manually after editing the registry: `npm run seed`.
import { readFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { parse } from "yaml";
import { Client } from "pg";
import "dotenv/config";

const registryPath = new URL("../agents/registry.yaml", import.meta.url);
const doc = parse(readFileSync(registryPath, "utf8"));

const client = new Client({ connectionString: process.env.DATABASE_URL });
await client.connect();

let seeded = 0;
for (const agent of doc.agents) {
  if (agent.template.startsWith("TO BE TRANSCRIBED")) {
    continue; // not transcribed yet — nothing to seed
  }

  const agentResult = await client.query(
    `INSERT INTO agent (id, code, name, function_id, model_class, scope)
     VALUES ($1, $2, $3, $4, $5, $6)
     ON CONFLICT (code) DO UPDATE SET
       name = EXCLUDED.name,
       function_id = EXCLUDED.function_id,
       model_class = EXCLUDED.model_class,
       scope = EXCLUDED.scope
     RETURNING id`,
    [randomUUID(), agent.id, agent.name, agent.function_id, agent.model_class, agent.scope]
  );
  const agentId = agentResult.rows[0].id;

  await client.query(
    `INSERT INTO agent_prompt_version
       (id, agent_id, version_number, template, input_schema, output_schema, is_active)
     VALUES ($1, $2, $3, $4, $5, $6, true)
     ON CONFLICT (agent_id, version_number) DO UPDATE SET
       template = EXCLUDED.template,
       input_schema = EXCLUDED.input_schema,
       output_schema = EXCLUDED.output_schema,
       is_active = true`,
    [
      randomUUID(),
      agentId,
      agent.version,
      agent.template,
      JSON.stringify(agent.input_schema),
      JSON.stringify(agent.output_schema),
    ]
  );

  seeded += 1;
  console.log(`Seeded ${agent.id}`);
}

await client.end();
console.log(`Done. ${seeded} agent(s) seeded.`);
