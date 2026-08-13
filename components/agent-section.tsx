import { getLatestSucceededRun, getLatestRunForAgent } from "@/lib/data/agent-runs";
import type { AgentRunEntityRef } from "@/lib/data/agent-runs";
import { getDealHistorySummary } from "@/lib/data/deals";
import { flattenOutputForHandoff, isLowConfidenceValue } from "@/lib/prompt-engine/format-output";
import { runAgentAction } from "@/lib/actions/agent-runs";
import type { InputFieldSpec } from "@/lib/prompt-engine/types";
import type { Agent, AgentPromptVersion } from "@/app/generated/prisma/client";

interface AgentSectionProps {
  workspaceId: string;
  entityRef: AgentRunEntityRef;
  redirectPath: string;
  agent: Agent;
  promptVersion: AgentPromptVersion;
  errorAgentCode?: string;
}

// The registry's `placeholder` (the exact PDF bracket text) already reads as
// a label — reused here instead of adding a separate human-label field. Some
// templates reuse a generic bracket like "[X]" for several distinct metrics
// (agent-19) — the field name is appended so those don't render as
// identical, undifferentiated labels.
function fieldLabel(placeholder: string | undefined, field: string): string {
  const humanized = placeholder ? placeholder.replace(/^\[/, "").replace(/\]$/, "") : "";
  const fieldWords = field.replace(/_/g, " ");
  return humanized && humanized.toLowerCase() !== fieldWords.toLowerCase()
    ? `${humanized} (${fieldWords})`
    : humanized || fieldWords;
}

// FR-4.2 handoff, generalized: a content_block field's default value comes
// from (a) an auto-generated deal-history summary if its source is
// deal_history, or (b) the latest successful run of whichever upstream
// agent(s) declare `prefills: <this field>` — whichever is found first, for
// this exact entity. Fields with neither stay blank, same as Phase 2.
async function resolvePrefill(
  workspaceId: string,
  entityRef: AgentRunEntityRef,
  inputSchema: InputFieldSpec[],
  field: InputFieldSpec
): Promise<string> {
  if (field.source === "deal_history") {
    return entityRef.dealId ? getDealHistorySummary(workspaceId, entityRef.dealId) : "";
  }
  const hints = inputSchema.filter((spec) => spec.prefills === field.field);
  for (const hint of hints) {
    const run = await getLatestSucceededRun(workspaceId, hint.source, entityRef);
    if (run) {
      return flattenOutputForHandoff(run.outputPayload);
    }
  }
  return "";
}

function OutputDisplay({ output }: { output: unknown }) {
  if (!output || typeof output !== "object") return null;
  return (
    <dl>
      {Object.entries(output as Record<string, unknown>).map(([key, value]) => {
        const lowConfidence =
          isLowConfidenceValue(value) ||
          (Array.isArray(value) && value.some((item) => isLowConfidenceValue(item)));
        const display = Array.isArray(value) ? value.join(" · ") : String(value);
        return (
          <div key={key}>
            <dt>
              <strong>{key}</strong>
            </dt>
            <dd>
              {lowConfidence && <strong>Confiance faible : </strong>}
              {display}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}

// Reused across the prospect, deal, and workspace pages — one form-building
// + prefill + output-display implementation for all 19 wired agents (agent
// 12 is scope: conversational and never reaches this component).
export async function AgentSection({
  workspaceId,
  entityRef,
  redirectPath,
  agent,
  promptVersion,
  errorAgentCode,
}: AgentSectionProps) {
  const inputSchema = promptVersion.inputSchema as unknown as InputFieldSpec[];
  const realFields = inputSchema.filter(
    (spec) => (spec.kind === "inline" && spec.source === "user_input") || spec.kind === "content_block"
  );

  const fieldsWithPrefill = await Promise.all(
    realFields.map(async (field) => ({
      field,
      prefill:
        field.kind === "content_block"
          ? await resolvePrefill(workspaceId, entityRef, inputSchema, field)
          : "",
    }))
  );

  const latestRun = await getLatestRunForAgent(workspaceId, agent.code, entityRef);

  return (
    <section>
      <h3>{agent.name}</h3>

      {errorAgentCode === agent.code && (
        <p role="alert">
          Le contexte workspace (offre / ICP / ton) et les champs requis ci-dessous sont nécessaires
          avant d&apos;exécuter cet agent.
        </p>
      )}

      <form action={runAgentAction.bind(null, workspaceId, entityRef, redirectPath, agent.code)}>
        {fieldsWithPrefill.map(({ field, prefill }) =>
          field.kind === "content_block" ? (
            <div key={field.field}>
              <label>
                {fieldLabel(field.placeholder, field.field)}
                <br />
                <textarea
                  name={field.field}
                  rows={5}
                  defaultValue={prefill}
                  required={field.required}
                />
              </label>
            </div>
          ) : (
            <div key={field.field}>
              <label>
                {fieldLabel(field.placeholder, field.field)}
                <br />
                <input type="text" name={field.field} required={field.required} />
              </label>
            </div>
          )
        )}
        <button type="submit">Exécuter {agent.name}</button>
      </form>

      {latestRun && (
        <div>
          <p>
            Dernière exécution : {latestRun.createdAt.toLocaleString("fr-FR")} — statut :{" "}
            {latestRun.status}
          </p>
          {latestRun.status === "succeeded" && <OutputDisplay output={latestRun.outputPayload} />}
          {latestRun.status === "validation_error" && (
            <p>Le modèle a renvoyé une sortie non conforme. Réessaie ou ajuste le contexte.</p>
          )}
          {latestRun.status === "failed" && <p>L&apos;appel au modèle a échoué.</p>}
        </div>
      )}
    </section>
  );
}
