import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { prisma } from "@/lib/db/client";
import { resolveInputs } from "@/lib/prompt-engine/resolve-inputs";
import type { InputFieldSpec } from "@/lib/prompt-engine/types";

const agent1InputSchema: InputFieldSpec[] = [
  {
    field: "offer_one_liner",
    source: "workspace_context",
    kind: "inline",
    placeholder: "[OFFER]",
    required: true,
  },
  { field: "icp", source: "workspace_context", kind: "inline", placeholder: "[ICP]", required: true },
  {
    field: "raw_company_info",
    source: "user_input",
    kind: "content_block",
    placeholder: "[NOTES]",
    required: true,
  },
];

describe("resolveInputs", () => {
  let workspaceWithContext: { id: string };
  let workspaceWithoutContext: { id: string };

  beforeAll(async () => {
    workspaceWithContext = await prisma.workspace.create({ data: { name: "Has context" } });
    await prisma.workspaceContext.create({
      data: {
        workspaceId: workspaceWithContext.id,
        version: 1,
        offerDescription: "We help B2B teams sell faster",
        icpDescription: "50-200 person SaaS companies",
        tone: "direct",
      },
    });
    workspaceWithoutContext = await prisma.workspace.create({ data: { name: "No context" } });
  });

  afterAll(async () => {
    await prisma.workspace.deleteMany({
      where: { id: { in: [workspaceWithContext.id, workspaceWithoutContext.id] } },
    });
    await prisma.$disconnect();
  });

  it("resolves ok when workspace context exists and the required user field is provided", async () => {
    const result = await resolveInputs(workspaceWithContext.id, agent1InputSchema, {
      raw_company_info: "They just raised a Series B",
    });
    expect(result.ok).toBe(true);
    expect(result.values).toMatchObject({
      offer_one_liner: "We help B2B teams sell faster",
      icp: "50-200 person SaaS companies",
      raw_company_info: "They just raised a Series B",
    });
  });

  it("reports the missing required user field without touching the DB (FR-2.2)", async () => {
    const result = await resolveInputs(workspaceWithContext.id, agent1InputSchema, {});
    expect(result.ok).toBe(false);
    expect(result.missing).toEqual(["raw_company_info"]);
  });

  it("reports missing workspace_context fields when the workspace has none", async () => {
    const result = await resolveInputs(workspaceWithoutContext.id, agent1InputSchema, {
      raw_company_info: "some info",
    });
    expect(result.ok).toBe(false);
    expect(result.missing).toEqual(expect.arrayContaining(["offer_one_liner", "icp"]));
  });

  it("resolves a composed workspace_context field (offer + pricing)", async () => {
    await prisma.workspaceContext.create({
      data: {
        workspaceId: workspaceWithContext.id,
        version: 2,
        offerDescription: "We help B2B teams sell faster",
        icpDescription: "50-200 person SaaS companies",
        tone: "direct",
        pricingSummary: "€500/month",
      },
    });
    const result = await resolveInputs(
      workspaceWithContext.id,
      [
        {
          field: "offer_and_price",
          source: "workspace_context",
          kind: "inline",
          placeholder: "[OFFRE + PRIX]",
          required: true,
        },
      ],
      {}
    );
    expect(result.ok).toBe(true);
    expect(result.values.offer_and_price).toBe("We help B2B teams sell faster — Tarifs : €500/month");
  });

  it("inlines a short user_input choice field directly (not wrapped as a content block)", async () => {
    const result = await resolveInputs(
      workspaceWithContext.id,
      [
        {
          field: "call_duration",
          source: "user_input",
          kind: "inline",
          placeholder: "[30/45/60 MIN]",
          required: true,
        },
      ],
      { call_duration: "45" }
    );
    expect(result.ok).toBe(true);
    expect(result.values.call_duration).toBe("45");
  });
});
