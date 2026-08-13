import { getActiveWorkspaceContext } from "@/lib/data/workspace-context";
import type { InputFieldSpec } from "./types";

export interface ResolveInputsResult {
  ok: boolean;
  values: Record<string, string>;
  missing: string[];
}

type WorkspaceContext = Awaited<ReturnType<typeof getActiveWorkspaceContext>>;

// Resolvers for `inline` fields sourced from workspace_context. A function
// (not a flat column map) so a placeholder can combine several columns —
// e.g. "[OFFRE + PRIX]" needs both offerDescription and pricingSummary.
// New agent field names are added here as they're transcribed, not before.
const WORKSPACE_CONTEXT_RESOLVERS: Record<string, (ctx: WorkspaceContext) => string | undefined> =
  {
    offer_one_liner: (ctx) => ctx?.offerDescription,
    offer: (ctx) => ctx?.offerDescription,
    product_description: (ctx) => ctx?.offerDescription,
    icp: (ctx) => ctx?.icpDescription,
    tone: (ctx) => ctx?.tone,
    offer_and_price: (ctx) =>
      ctx?.offerDescription
        ? `${ctx.offerDescription} — Tarifs : ${ctx.pricingSummary ?? "non précisé"}`
        : undefined,
    offer_and_pricing: (ctx) =>
      ctx?.offerDescription
        ? `${ctx.offerDescription} — Tarifs : ${ctx.pricingSummary ?? "non précisé"}`
        : undefined,
  };

// FR-2.2: an agent may only run once every required field is resolved. This
// function never calls the model and never touches AgentRun — callers must
// check `ok` before doing either (system-overview.md sequence diagram).
export async function resolveInputs(
  workspaceId: string,
  inputSchema: InputFieldSpec[],
  userValues: Record<string, string>
): Promise<ResolveInputsResult> {
  const workspaceContext = await getActiveWorkspaceContext(workspaceId);
  const values: Record<string, string> = {};
  const missing: string[] = [];

  for (const spec of inputSchema) {
    if (spec.kind !== "inline" && spec.kind !== "content_block") {
      continue; // handoff hint only, not read by the PromptEngine
    }

    let value: string | undefined;
    if (spec.kind === "content_block") {
      // Regardless of whether the UI pre-filled it from an upstream agent
      // run or deal history, by submit time it's just submitted form data.
      value = userValues[spec.field]?.trim() || undefined;
    } else if (spec.source === "workspace_context") {
      value = WORKSPACE_CONTEXT_RESOLVERS[spec.field]?.(workspaceContext);
    } else {
      // Short, user-typed choice (e.g. call duration, channels available) —
      // not pasted external content, so it's safe to inline directly.
      value = userValues[spec.field]?.trim() || undefined;
    }

    if (!value) {
      if (spec.required) {
        missing.push(spec.field);
      }
      continue;
    }
    values[spec.field] = value;
  }

  return { ok: missing.length === 0, values, missing };
}
