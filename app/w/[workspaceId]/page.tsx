import { redirect } from "next/navigation";
import { requireWorkspaceSession, UnauthenticatedError } from "@/lib/auth/guard";
import { getActiveWorkspaceContext } from "@/lib/data/workspace-context";
import { listProspects } from "@/lib/data/prospects";
import { updateWorkspaceContextAction, createProspectAction } from "@/lib/actions/workspace";

export default async function WorkspacePage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;

  try {
    await requireWorkspaceSession(workspaceId);
  } catch (error) {
    if (error instanceof UnauthenticatedError) {
      redirect("/login");
    }
    return (
      <main>
        <p>Accès refusé à ce workspace.</p>
      </main>
    );
  }

  const [context, prospects] = await Promise.all([
    getActiveWorkspaceContext(workspaceId),
    listProspects(workspaceId),
  ]);

  return (
    <main>
      <h1>Workspace</h1>
      <p>
        <a href={`/w/${workspaceId}/agents`}>Outils workspace (pipeline, performance)</a>
      </p>

      <section>
        <h2>Contexte (offre / ICP / ton)</h2>
        <p>
          Ces champs alimentent directement les prompts des agents — voir le placeholder
          correspondant dans chaque agent.
        </p>
        <form action={updateWorkspaceContextAction.bind(null, workspaceId)}>
          <div>
            <label>
              Offre en 1 phrase
              <br />
              <textarea
                name="offerDescription"
                rows={2}
                defaultValue={context?.offerDescription}
                required
              />
            </label>
          </div>
          <div>
            <label>
              ICP (taille, secteur, persona)
              <br />
              <textarea name="icpDescription" rows={2} defaultValue={context?.icpDescription} required />
            </label>
          </div>
          <div>
            <label>
              Ton (direct / chaleureux / expert)
              <br />
              <input type="text" name="tone" defaultValue={context?.tone} required />
            </label>
          </div>
          <div>
            <label>
              Tarifs (optionnel)
              <br />
              <textarea name="pricingSummary" rows={2} defaultValue={context?.pricingSummary ?? ""} />
            </label>
          </div>
          <button type="submit">Enregistrer</button>
        </form>
        {context && <p>Version actuelle du contexte : {context.version}</p>}
      </section>

      <section>
        <h2>Prospects</h2>
        <form action={createProspectAction.bind(null, workspaceId)}>
          <input type="text" name="fullName" placeholder="Nom complet" required />
          <input type="text" name="company" placeholder="Entreprise (optionnel)" />
          <button type="submit">Ajouter un prospect</button>
        </form>
        <ul>
          {prospects.map((prospect) => (
            <li key={prospect.id}>
              <a href={`/w/${workspaceId}/prospects/${prospect.id}`}>
                {prospect.fullName}
                {prospect.company ? ` — ${prospect.company}` : ""}
              </a>
            </li>
          ))}
          {prospects.length === 0 && <li>Aucun prospect pour le moment.</li>}
        </ul>
      </section>
    </main>
  );
}
