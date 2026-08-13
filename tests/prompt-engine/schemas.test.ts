import { describe, expect, it } from "vitest";
import { outputSchemaToJsonSchema, outputSchemaToZod } from "@/lib/prompt-engine/schemas";
import type { OutputFieldSpec } from "@/lib/prompt-engine/types";

const agent1Output: OutputFieldSpec[] = [
  { field: "heat_score_10", type: "integer" },
  { field: "heat_score_justification", type: "string" },
  { field: "top_3_signals", type: "string[3]" },
  { field: "recommended_angle", type: "string" },
  { field: "timing_recommendation", type: "enum", values: ["maintenant", "dans_1_mois", "jamais"] },
];

describe("outputSchemaToJsonSchema", () => {
  it("produces a JSON Schema with every field required and no extras allowed", () => {
    const schema = outputSchemaToJsonSchema(agent1Output);
    expect(schema.required).toEqual([
      "heat_score_10",
      "heat_score_justification",
      "top_3_signals",
      "recommended_angle",
      "timing_recommendation",
    ]);
    expect(schema.additionalProperties).toBe(false);
    expect(schema.properties.top_3_signals).toMatchObject({
      type: "array",
      minItems: 3,
      maxItems: 3,
    });
    expect(schema.properties.timing_recommendation).toMatchObject({
      enum: ["maintenant", "dans_1_mois", "jamais"],
    });
  });
});

describe("outputSchemaToZod", () => {
  const zodSchema = outputSchemaToZod(agent1Output);

  it("accepts well-formed model output", () => {
    const result = zodSchema.safeParse({
      heat_score_10: 8,
      heat_score_justification: "Recent funding round and hiring spree",
      top_3_signals: ["funding", "hiring", "new CTO"],
      recommended_angle: "hiring spree",
      timing_recommendation: "maintenant",
    });
    expect(result.success).toBe(true);
  });

  it("rejects output with the wrong array length (BR-1 forces exactly 3 signals)", () => {
    const result = zodSchema.safeParse({
      heat_score_10: 8,
      heat_score_justification: "x",
      top_3_signals: ["only one"],
      recommended_angle: "x",
      timing_recommendation: "maintenant",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a timing value outside the enum", () => {
    const result = zodSchema.safeParse({
      heat_score_10: 8,
      heat_score_justification: "x",
      top_3_signals: ["a", "b", "c"],
      recommended_angle: "x",
      timing_recommendation: "next_quarter",
    });
    expect(result.success).toBe(false);
  });
});

describe("string[] (variable-length list output)", () => {
  const blockedDealsOutput: OutputFieldSpec[] = [
    { field: "blocked_deals", type: "string[]", description: "One formatted line per blocked deal" },
  ];

  it("JSON Schema allows any array length with at least one item", () => {
    const schema = outputSchemaToJsonSchema(blockedDealsOutput);
    expect(schema.properties.blocked_deals).toMatchObject({
      type: "array",
      items: { type: "string" },
      minItems: 1,
    });
    expect(schema.properties.blocked_deals).not.toHaveProperty("maxItems");
  });

  it("Zod accepts a list of any length >= 1 and rejects an empty list", () => {
    const zodSchema = outputSchemaToZod(blockedDealsOutput);
    expect(zodSchema.safeParse({ blocked_deals: ["Acme — 18 jours sans action"] }).success).toBe(
      true
    );
    expect(
      zodSchema.safeParse({
        blocked_deals: ["Acme — 18 jours", "Beta — 22 jours", "Gamma — 30 jours"],
      }).success
    ).toBe(true);
    expect(zodSchema.safeParse({ blocked_deals: [] }).success).toBe(false);
  });
});
