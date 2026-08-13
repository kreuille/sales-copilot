import { redirect } from "next/navigation";
import { requireWorkspaceSession, UnauthenticatedError } from "@/lib/auth/guard";
import { listActiveAgentsByScope } from "@/lib/data/agents";
import { listAgentRunsForEntity } from "@/lib/data/agent-runs";
import { AgentSection } from "@/components/agent-section";

export default async function WorkspaceAgentsPage({
  params,
  searchParams,
}: {
  params: Promise<{ workspaceId: string }>;
  searchParams: Promise<{ error?: string; agent?: string }>;
}) {
  const { workspaceId } = await params;
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

  const [agents, runs] = await Promise.all([
    listActiveAgentsByScope("workspace"),
    listAgentRunsForEntity(workspaceId, {}),
  ]);
  const redirectPath = `/w/${workspaceId}/agents`;

  return (
    <main>
      <h1>Outils workspace</h1>
      <p>
        <a href={`/w/${workspaceId}`}>← Retour au workspace</a>
      </p>
      <p>Agents non rattachés à un prospect ou un deal précis (pipeline, performance).</p>

      {agents.map(({ agent, promptVersion }) => (
        <AgentSection
          key={agent.code}
          workspaceId={workspaceId}
          entityRef={{}}
          redirectPath={redirectPath}
          agent={agent}
          promptVersion={promptVersion}
          errorAgentCode={error === "missing_fields" ? errorAgentCode : undefined}
        />
      ))}

      <section>
        <h2>Historique des exécutions (agents workspace)</h2>
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
