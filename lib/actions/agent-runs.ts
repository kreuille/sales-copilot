"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { requireWorkspaceSession } from "@/lib/auth/guard";
import { getActiveAgentPromptVersion } from "@/lib/data/agents";
import { runAgent } from "@/lib/prompt-engine/run";
import type { InputFieldSpec, OutputFieldSpec } from "@/lib/prompt-engine/types";
import type { AgentRunEntityRef } from "@/lib/data/agent-runs";

// Generic across all three scopes (prospect/deal/workspace): entityRef
// selects which one, redirectPath is the page to return to (and to redirect
// back to with an error on FR-2.2 missing fields, since there's no AgentRun
// row to revalidate against in that case).
export async function runAgentAction(
  workspaceId: string,
  entityRef: AgentRunEntityRef,
  redirectPath: string,
  agentCode: string,
  formData: FormData
) {
  const { userId } = await requireWorkspaceSession(workspaceId);
  const { agent, promptVersion } = await getActiveAgentPromptVersion(agentCode);

  const userValues: Record<string, string> = {};
  for (const [key, value] of formData.entries()) {
    if (typeof value === "string") {
      userValues[key] = value;
    }
  }

  const result = await runAgent({
    workspaceId,
    agentPromptVersionId: promptVersion.id,
    template: promptVersion.template,
    inputSchema: promptVersion.inputSchema as unknown as InputFieldSpec[],
    outputSchema: promptVersion.outputSchema as unknown as OutputFieldSpec[],
    modelClass: agent.modelClass,
    triggeredByUserId: userId,
    prospectId: entityRef.prospectId,
    dealId: entityRef.dealId,
    userValues,
  });

  if (result.status === "missing_fields") {
    // FR-2.2: no LLM call, no AgentRun row was created for this attempt.
    redirect(`${redirectPath}?error=missing_fields&agent=${agentCode}`);
  }

  revalidatePath(redirectPath);
}
