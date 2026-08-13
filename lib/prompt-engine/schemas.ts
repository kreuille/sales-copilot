import { z } from "zod";
import type { OutputFieldSpec } from "./types";

// Derives both the Claude tool-call JSON Schema and the Zod validator from
// the same output_schema data (agents/registry.yaml), so the two can never
// drift apart — one field list, two representations.

export const SUBMIT_OUTPUT_TOOL_NAME = "submit_output";

export function outputSchemaToJsonSchema(outputSchema: OutputFieldSpec[]) {
  const properties: Record<string, unknown> = {};
  const required: string[] = [];

  for (const f of outputSchema) {
    required.push(f.field);
    switch (f.type) {
      case "integer":
        properties[f.field] = { type: "integer", description: f.description };
        break;
      case "string[3]":
        properties[f.field] = {
          type: "array",
          items: { type: "string" },
          minItems: 3,
          maxItems: 3,
          description: f.description,
        };
        break;
      case "string[]":
        properties[f.field] = {
          type: "array",
          items: { type: "string" },
          minItems: 1,
          description: f.description,
        };
        break;
      case "enum":
        properties[f.field] = { type: "string", enum: f.values, description: f.description };
        break;
      default:
        properties[f.field] = { type: "string", description: f.description };
    }
  }

  return { type: "object" as const, properties, required, additionalProperties: false };
}

export function outputSchemaToZod(outputSchema: OutputFieldSpec[]) {
  const shape: Record<string, z.ZodTypeAny> = {};

  for (const f of outputSchema) {
    switch (f.type) {
      case "integer":
        shape[f.field] = z.number().int();
        break;
      case "string[3]":
        shape[f.field] = z.array(z.string()).length(3);
        break;
      case "string[]":
        shape[f.field] = z.array(z.string()).min(1);
        break;
      case "enum":
        shape[f.field] = z.enum(f.values as [string, ...string[]]);
        break;
      default:
        shape[f.field] = z.string();
    }
  }

  return z.object(shape);
}
