import { describe, expect, it } from "vitest";
import { getActiveAgentPromptVersion } from "@/lib/data/agents";

// Depends on `npm run seed` having been run against the local dev database.
describe("getActiveAgentPromptVersion", () => {
  it("reads back the seeded agent-01 prompt version", async () => {
    const { agent, promptVersion } = await getActiveAgentPromptVersion(
      "agent-01-chasseur-de-signaux"
    );
    expect(agent.modelClass).toBe("BALANCED");
    expect(promptVersion.isActive).toBe(true);
    expect(promptVersion.template).toContain("analyste de signaux d'achat B2B");
  });

  it("throws for a code that doesn't exist in the registry", async () => {
    await expect(getActiveAgentPromptVersion("agent-99-does-not-exist")).rejects.toThrow(
      /No active prompt version/
    );
  });

  it("reads back agent 12 (Sparring Partner) as scope conversational, still seeded but unwired", async () => {
    const { agent } = await getActiveAgentPromptVersion("agent-12-sparring-partner");
    expect(agent.scope).toBe("conversational");
  });
});
