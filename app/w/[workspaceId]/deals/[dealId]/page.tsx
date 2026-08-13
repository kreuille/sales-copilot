import { notFound, redirect } from "next/navigation";
import { requireWorkspaceSession, UnauthenticatedError } from "@/lib/auth/guard";
import { getDeal, DEAL_STAGE_LABELS } from "@/lib/data/deals";
import { getProspect } from "@/lib/data/prospects";
import { listActiveAgentsByScope } from "@/lib/data/agents";
import { listAgentRunsForDeal } from "@/lib/data/agent-runs";
import { AgentSection } from "@/components/agent-section";
import { transitionDealStageAction } from "@/lib/actions/deals";
import type { DealStage } from "@/app/generated/prisma/enums";

const DEAL_STAGES: DealStage[] = [
  "first_contact",
  "after_demo",
  "proposal_sent",
  "closing",
  "lost",
  "won",
];

export default async function DealPage({
  params,
  searchParams,
}: {
  params: Promise<{ workspaceId: string; dealId: string }>;
  searchParams: Promise<{ error?: string; agent?: string }>;
}) {
  const { workspaceId, dealId } = await params;
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

  const deal = await getDeal(workspaceId, dealId).catch(() => null);
  if (!deal) {
    notFound();
  }
  const prospect = await getProspect(workspaceId, deal.prospectId);
  const [agents, runs] = await Promise.all([
    listActiveAgentsByScope("deal"),
    listAgentRunsForDeal(workspaceId, dealId),
  ]);
  const redirectPath = `/w/${workspaceId}/deals/${dealId}`;

  return (
    <main>
      <h1>Deal — {prospect.fullName}</h1>
      <p>
        <a href={`/w/${workspaceId}/prospects/${prospect.id}`}>← Retour au prospect</a>
      </p>
      <p>Étape actuelle : {DEAL_STAGE_LABELS[deal.stage]}</p>
      {deal.estimatedAmount != null && <p>Montant estimé : {deal.estimatedAmount.toString()} €</p>}

      <form action={transitionDealStageAction.bind(null, workspaceId, dealId)}>
        <label>
          Changer l&apos;étape
          <br />
          <select name="stage" defaultValue={deal.stage}>
            {DEAL_STAGES.map((stage) => (
              <option key={stage} value={stage}>
                {DEAL_STAGE_LABELS[stage]}
              </option>
            ))}
          </select>
        </label>
        <button type="submit">Mettre à jour</button>
      </form>

      {agents.map(({ agent, promptVersion }) => (
        <AgentSection
          key={agent.code}
          workspaceId={workspaceId}
          entityRef={{ dealId }}
          redirectPath={redirectPath}
          agent={agent}
          promptVersion={promptVersion}
          errorAgentCode={error === "missing_fields" ? errorAgentCode : undefined}
        />
      ))}

      <section>
        <h2>Historique des exécutions (agents deal)</h2>
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
