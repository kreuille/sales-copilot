import { notFound, redirect } from "next/navigation";
import { requireWorkspaceSession, UnauthenticatedError } from "@/lib/auth/guard";
import { getProspect } from "@/lib/data/prospects";
import { listDealsForProspect, DEAL_STAGE_LABELS } from "@/lib/data/deals";
import { listActiveAgentsByScope } from "@/lib/data/agents";
import { listAgentRunsForProspect } from "@/lib/data/agent-runs";
import { AgentSection } from "@/components/agent-section";
import { createDealAction } from "@/lib/actions/deals";
import type { DealStage } from "@/app/generated/prisma/enums";

const DEAL_STAGES: DealStage[] = [
  "first_contact",
  "after_demo",
  "proposal_sent",
  "closing",
  "lost",
  "won",
];

export default async function ProspectPage({
  params,
  searchParams,
}: {
  params: Promise<{ workspaceId: string; prospectId: string }>;
  searchParams: Promise<{ error?: string; agent?: string }>;
}) {
  const { workspaceId, prospectId } = await params;
  const { error, agent: errorAgentCode } = await searchParams;

  try {
    await requireWorkspaceSession(workspaceId);
  } catch (err) {
    if (err instanceof UnauthenticatedError) {
      redirect("/login");
    }
    return (
      <main>
        <p>Accès refusé à ce workspace.</p>
      </main>
    );
  }

  const prospect = await getProspect(workspaceId, prospectId).catch(() => null);
  if (!prospect) {
    notFound();
  }

  const [deals, agents, runs] = await Promise.all([
    listDealsForProspect(workspaceId, prospectId),
    listActiveAgentsByScope("prospect"),
    listAgentRunsForProspect(workspaceId, prospectId),
  ]);
  const redirectPath = `/w/${workspaceId}/prospects/${prospectId}`;

  return (
    <main>
      <h1>{prospect.fullName}</h1>
      {prospect.company && <p>{prospect.company}</p>}
      <p>
        <a href={`/w/${workspaceId}`}>← Retour au workspace</a>
      </p>

      <section>
        <h2>Deals</h2>
        <form action={createDealAction.bind(null, workspaceId, prospectId)}>
          <label>
            Étape de départ
            <select name="stage" defaultValue="first_contact">
              {DEAL_STAGES.map((stage) => (
                <option key={stage} value={stage}>
                  {DEAL_STAGE_LABELS[stage]}
                </option>
              ))}
            </select>
          </label>
          <input type="number" name="estimatedAmount" placeholder="Montant estimé (optionnel)" />
          <button type="submit">Créer un deal</button>
        </form>
        <ul>
          {deals.map((deal) => (
            <li key={deal.id}>
              <a href={`/w/${workspaceId}/deals/${deal.id}`}>
                {DEAL_STAGE_LABELS[deal.stage]}
                {deal.estimatedAmount != null ? ` — ${deal.estimatedAmount.toString()} €` : ""}
              </a>
            </li>
          ))}
          {deals.length === 0 && <li>Aucun deal pour le moment.</li>}
        </ul>
      </section>

      {agents.map(({ agent, promptVersion }) => (
        <AgentSection
          key={agent.code}
          workspaceId={workspaceId}
          entityRef={{ prospectId }}
          redirectPath={redirectPath}
          agent={agent}
          promptVersion={promptVersion}
          errorAgentCode={error === "missing_fields" ? errorAgentCode : undefined}
        />
      ))}

      <section>
        <h2>Historique des exécutions (agents prospect)</h2>
        <ul>
          {runs.map((run) => (
            <li key={run.id}>
              {run.createdAt.toLocaleString("fr-FR")} — {run.agentPromptVersion.agent.name} —{" "}
              {run.status}
            </li>
          ))}
          {runs.length === 0 && <li>Aucune exécution pour le moment.</li>}
        </ul>
      </section>
    </main>
  );
}
