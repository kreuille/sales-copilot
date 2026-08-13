# Règles métier

Règles explicitement énoncées dans les prompts source (PDF) et élevées au rang de règles produit — donc à faire respecter par le système, pas seulement espérées du modèle.

## BR-1 — Zéro invention
Tout agent traitant des données prospect (Profileur, Greffier, Chasseur de Signaux...) doit répondre "inconnu"/"signal faible" plutôt qu'inventer une information. Le produit ne doit jamais masquer cette instruction ni permettre à l'utilisateur de la désactiver silencieusement.

## BR-2 — Pessimisme par défaut sur la qualification
L'Agent 7 (Qualificateur) et l'Agent 9 (Analyste de Pipeline) doivent être pessimistes par défaut ("un deal mal qualifié coûte 3 semaines", "préfère un pipeline propre de 10 deals à un pipeline gonflé de 40"). Le produit ne doit pas permettre de sortie artificiellement positive pour "faire plaisir".

## BR-3 — Un agent = un job, jamais de mélange
Un agent ne doit produire que le format de sortie défini pour sa fonction. Le produit empêche structurellement le "piège du généraliste" (PART 3 du PDF) en n'offrant pas de mode "conversation libre multi-fonctions" en V1.

## BR-4 — Pas de fausse urgence
L'Agent 16 (Stratège de Closing) doit s'appuyer sur un levier d'urgence honnête uniquement (disponibilité réelle limitée, date de démarrage réelle). Le produit ne doit fournir aucun template ou raccourci générant une urgence fabriquée.

## BR-5 — Maximum 3 agents actifs à l'onboarding
Reprend la "règle des 3 premiers agents" (PART 3) : le produit ne doit jamais recommander plus de 3 agents à un nouveau workspace. Les autres restent disponibles mais non mis en avant.

## BR-6 — Pas d'action automatique
Aucune règle métier ne doit jamais déclencher l'envoi d'un message, la modification d'un CRM externe ou toute action visible par un tiers sans validation humaine explicite (cf. A-002, FR-4.3).

## BR-7 — Historique de deal comme source de vérité
La sortie structurée de chaque agent (score, brief, étape) doit être stockée en données structurées dans le deal, pas seulement conservée comme résumé de texte libre — évite de perdre l'information dans un blob non exploitable (aligné avec le principe général "éviter de stocker des résumés LLM comme source de vérité lorsqu'une donnée structurée existe").
