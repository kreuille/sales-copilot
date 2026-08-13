# Parcours utilisateurs

## J1 — Onboarding d'un workspace
1. L'utilisateur crée un workspace.
2. Il renseigne l'offre (1 phrase), l'ICP (taille, secteur, persona), le ton par défaut — équivalent structuré de "l'astuce Projets Claude" du PDF (coller offre/ICP/exemples dans les instructions du Projet).
3. Ce contexte est stocké une fois et injecté automatiquement dans tous les agents du workspace.

## J2 — Premier diagnostic ("quel agent activer d'abord")
1. L'utilisateur répond à une question simple : "Quel est ton symptôme ?" (reprend la grille PART 3 du PDF : "Je ne contacte personne" / "On me répond mais ça ne signe pas" / "Mon pipe est un cimetière" / "Je vends mais c'est le chaos").
2. Le produit recommande 3 agents max à activer en premier, jamais les 20.

## J3 — Exécution d'un agent isolé
1. L'utilisateur choisit un agent (ex: Agent 7 Qualificateur).
2. Il colle ses notes de call brutes.
3. Le contexte workspace (offre/prix) est pré-rempli automatiquement.
4. Le produit envoie le prompt complet au modèle, affiche la sortie structurée (score, justification, prochaine action).
5. L'utilisateur peut copier la sortie, la corriger, ou la valider dans le deal.

## J4 — Chaîne d'agents sur un même prospect (le job transverse)
1. Agent 1 (Chasseur de Signaux) → score de chaleur + angle d'approche, attaché au prospect.
2. Agent 2 (Profileur) reprend automatiquement les infos déjà collectées → produit un brief.
3. Agent 3 (Accrocheur) reprend automatiquement le brief de l'Agent 2 (le PDF le demande explicitement : "Voici le contexte sur le prospect : [COLLE LE BRIEF DE L'AGENT 2]") → 5 accroches.
4. L'utilisateur choisit une accroche, l'envoie manuellement hors produit (LinkedIn/email), puis marque l'étape comme faite.
5. Plus tard, Agent 5 ou 6 (Relance/Réanimation) reprend l'historique du deal automatiquement.

## J5 — Revue hebdomadaire
1. L'utilisateur colle/synchronise son pipeline (V1 : saisie manuelle ou import CSV ; pas de connecteur CRM réel, cf. A-004).
2. Agent 9 (Analyste de Pipeline) puis Agent 10 (Priorisateur) produisent le plan de la semaine.
3. En fin de semaine, Agent 19 (Analyste de Perf) et Agent 20 (Coach de Rétro) closent la boucle.

## J6 — Cas d'erreur : contexte insuffisant
1. Un agent nécessite une info manquante (ex: prix, ICP) non renseignée dans le workspace.
2. Le produit bloque l'exécution et demande de compléter le contexte plutôt que d'envoyer un prompt incomplet au modèle — reprend la règle explicite de plusieurs prompts source ("zéro invention, écris inconnu si une info manque").
