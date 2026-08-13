# Vision produit

## Nom de travail
**Sales Copilot** (nom provisoire — à valider).

## En une phrase
Un copilote qui transforme les 20 prompts spécialisés d'Eric Djavid en un outil structuré : contexte persistant par workspace, enchaînement guidé des agents le long du cycle de vente, et sortie prête à copier ou exporter — sans jamais agir automatiquement à la place de l'utilisateur.

## Problème
Un solo ou une petite équipe (consultant, freelance, fondateur) fait à la fois les 10 fonctions d'une équipe commerciale (prospection, outreach, follow-up, qualification, pipeline, objections, démo, closing, CRM, performance). Le changement de casquette permanent dégrade la qualité de chaque tâche. Le réflexe "prompt générique dans ChatGPT" ne résout rien : pas de contexte persistant, pas de spécialisation, pas de suivi entre les tâches.

Le PDF source répond à ce problème avec 20 prompts copier-coller, mais souffre de trois limites que ce produit doit adresser :
1. **Piège du collectionneur** : prompts copiés dans un doc, jamais réutilisés.
2. **Piège du généraliste** : tout mélangé dans une seule conversation Claude, perte de spécialisation.
3. **Re-briefing permanent** : sans mémoire persistante (offre, ICP, historique), chaque appel d'agent repart de zéro.

## Ce que le produit fait
- Centralise les 20 prompts sous forme de templates versionnés, organisés par les 10 fonctions.
- Maintient un **contexte de workspace** persistant (offre, ICP, ton) injecté automatiquement dans chaque prompt — fini le re-briefing.
- Maintient un **contexte par prospect/deal** (brief, historique d'échanges, dernière sortie d'agent) pour chaîner les agents (ex: sortie de l'Agent 2 "Profileur" → entrée de l'Agent 3 "Accrocheur").
- Guide l'utilisateur vers le bon agent selon son symptôme (repris de la grille "règle des 3 premiers agents" du PDF, PART 3).
- Affiche chaque sortie d'agent avec un niveau de confiance déclaré par le prompt lui-même (les prompts source demandent déjà "dis-le si les signaux sont faibles", "écris inconnu plutôt que d'inventer").
- Garde un historique consultable par prospect/deal.

## Ce que le produit ne fait PAS (V1)
- N'envoie aucun message (email, LinkedIn, CRM) automatiquement. Toute sortie est à copier/valider manuellement par l'utilisateur.
- Ne se connecte à aucun CRM/boîte mail externe en V1 ([[integrations]], A-004).
- N'exécute aucune action "agentique" en tâche de fond, sans déclenchement humain.
- N'est pas un produit multi-tenant commercial en V1 (A-003).

## Pourquoi un LLM est nécessaire ici (et où il ne l'est pas)
Les 20 prompts sont fondamentalement des tâches de **génération et de raisonnement qualitatif** (rédaction, scoring argumenté, synthèse) — c'est le cœur de valeur d'un LLM, conforme au principe "AI as decision layer, software as control layer". En revanche, la persistance du contexte, l'enchaînement des agents, l'authentification, le stockage des workspaces/deals et l'historique sont du **logiciel déterministe classique** — aucun agent autonome n'est nécessaire pour ces responsabilités (voir ADR-002 dans [[architecture-decisions]]).

## Métrique de succès produit (à affiner en Phase 2 avec usage réel)
- Nombre d'agents activés et réutilisés (pas juste copiés une fois) par utilisateur/semaine.
- Temps de re-briefing économisé (proxy : nombre de fois où le contexte workspace/deal est réutilisé sans ressaisie).
- Taux d'agents enchaînés (sortie d'un agent réinjectée comme entrée d'un autre) vs agents utilisés isolément.
