import { anthropic } from "@/lib/llm/client";
import { resolveModel, resolveMaxTokens, type ModelClass } from "@/lib/llm/model-routing";
import { resolveInputs } from "./resolve-inputs";
import { assemblePrompt } from "./assemble";
import { outputSchemaToJsonSchema, outputSchemaToZod, SUBMIT_OUTPUT_TOOL_NAME } from "./schemas";
import { createAgentRun } from "@/lib/data/agent-runs";
import type { InputFieldSpec, OutputFieldSpec } from "./types";
import type { Prisma } from "@/app/generated/prisma/client";

export interface RunAgentInput {
  workspaceId: string;
  agentPromptVersionId: string;
  template: string;
  inputSchema: InputFieldSpec[];
  outputSchema: OutputFieldSpec[];
  modelClass: ModelClass;
  triggeredByUserId: string;
  prospectId?: string;
  dealId?: string;
  userValues: Record<string, string>;
}

export type RunAgentResult =
  | { status: "missing_fields"; missing: string[] }
  | { status: "succeeded"; output: Record<string, unknown>; agentRunId: string }
  | { status: "validation_error"; agentRunId: string }
  | { status: "failed"; agentRunId?: string; message: string };

// The single deterministic entry point described in system-overview.md:
// resolve -> (stop here if incomplete, FR-2.2) -> assemble -> one LLM call ->
// validate -> persist. No retries, no auto-correction of a malformed model
// response (agent-architecture.md).
export async function runAgent(input: RunAgentInput): Promise<RunAgentResult> {
  const resolved = await resolveInputs(input.workspaceId, input.inputSchema, input.userValues);
  if (!resolved.ok) {
    return { status: "missing_fields", missing: resolved.missing };
  }

  const { system, userContent } = assemblePrompt(
    input.template,
    input.inputSchema,
    resolved.values
  );
  const jsonSchema = outputSchemaToJsonSchema(input.outputSchema);
  const zodSchema = outputSchemaToZod(input.outputSchema);
  const model = resolveModel(input.modelClass);
  const inputPayload = resolved.values as Prisma.InputJsonValue;

  let response;
  try {
    response = await anthropic.messages.create({
      model,
      max_tokens: resolveMaxTokens(input.modelClass),
      system,
      messages: [{ role: "user", content: userContent }],
      tools: [{ name: SUBMIT_OUTPUT_TOOL_NAME, input_schema: jsonSchema }],
      tool_choice: { type: "tool", name: SUBMIT_OUTPUT_TOOL_NAME },
    });
  } catch (error) {
    return {
      status: "failed",
      message: error instanceof Error ? error.message : "LLM call failed",
    };
  }

  let toolUse: Extract<(typeof response.content)[number], { type: "tool_use" }> | undefined;
  for (const block of response.content) {
    if (block.type === "tool_use") {
      toolUse = block;
      break;
    }
  }

  if (!toolUse) {
    const run = await createAgentRun(input.workspaceId, {
      agentPromptVersionId: input.agentPromptVersionId,
      triggeredByUserId: input.triggeredByUserId,
      prospectId: input.prospectId,
      dealId: input.dealId,
      inputPayload,
      modelUsed: model,
      tokensIn: response.usage.input_tokens,
      tokensOut: response.usage.output_tokens,
      status: "failed",
    });
    return {
      status: "failed",
      agentRunId: run.id,
      message: "Le modèle n'a pas renvoyé de sortie structurée",
    };
  }

  const parsed = zodSchema.safeParse(toolUse.input);

  const run = await createAgentRun(input.workspaceId, {
    agentPromptVersionId: input.agentPromptVersionId,
    triggeredByUserId: input.triggeredByUserId,
    prospectId: input.prospectId,
    dealId: input.dealId,
    inputPayload,
    outputPayload: toolUse.input as Prisma.InputJsonValue,
    modelUsed: model,
    tokensIn: response.usage.input_tokens,
    tokensOut: response.usage.output_tokens,
    status: parsed.success ? "succeeded" : "validation_error",
  });

  if (!parsed.success) {
    return { status: "validation_error", agentRunId: run.id };
  }
  return { status: "succeeded", output: parsed.data, agentRunId: run.id };
}
