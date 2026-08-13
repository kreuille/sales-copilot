# Architecture Decision Records (ADR)

## ADR-001 — Stack technique proposée
**Contexte** : aucune stack imposée par la source ni par l'utilisateur (A-006). Produit : app web multi-utilisateurs, CRUD + appels LLM synchrones, pas de charge temps réel critique, équipe probablement petite (Arnaud + collaborateurs).

**Options considérées**
1. Next.js (React, full-stack TS) + PostgreSQL + Prisma + déploiement Vercel/Render.
2. Django (Python) + PostgreSQL — écosystème mûr, admin auto-généré.
3. Node/Express API séparée + frontend React séparé.

**Décision** : Next.js (App Router, TypeScript) + PostgreSQL + Prisma, déployé sur Vercel avec Postgres managé (Neon/Supabase — à trancher au moment du provisioning, sans impact architectural).

**Pourquoi** : un seul langage (TypeScript) pour front, API et logique domaine réduit la charge cognitive pour une petite équipe ; typage fort de bout en bout (aligné avec le principe "typage strict" du brief) ; écosystème mature pour auth, ORM, observabilité ; time-to-market rapide pour un vertical slice.

**Avantages** : DX élevée, déploiement managé simple, typage partagé front/back, large communauté.
**Inconvénients** : couplage au runtime Node ; moins adapté si des besoins de calcul lourd apparaissent plus tard.
**Risques** : sur-ingénierie du framework si le produit reste très simple (mitigé : on n'utilise que le sous-ensemble CRUD + Server Actions/API routes nécessaire).
**Conséquences** : les futurs connecteurs (ADR-004) s'écrivent comme modules TypeScript derrière une interface commune.
**Migration possible** : oui — la couche domaine reste indépendante du framework web si elle est isolée (voir data-architecture).

*Statut : validé par l'utilisateur le 2026-08-12 (A-006). Prisma retenu (vs Drizzle) pour la maturité de l'écosystème et l'admin studio intégré, adapté à une petite équipe. Vercel retenu comme plateforme de déploiement pour l'intégration native Next.js.*

## ADR-002 — Pas d'agents autonomes ni d'orchestrateur multi-agents
**Contexte** : le brief initial supposait 20 agents Claude autonomes avec orchestration, mémoire inter-agents, escalade, permissions granulaires. Le produit réel validé est un copilote semi-assisté (A-002).

**Options considérées**
1. Framework d'orchestration multi-agents (ex: graph d'agents, boucles agentiques, agents qui s'appellent entre eux).
2. Un seul appel LLM synchrone par action utilisateur, avec contexte assemblé de manière déterministe.

**Décision** : option 2. Chaque "agent" est un couple (template de prompt versionné + schéma d'entrée/sortie), exécuté par une fonction déterministe qui assemble le contexte et fait un seul appel LLM.

**Pourquoi** : aucun des 20 prompts source ne nécessite un raisonnement multi-étapes autonome — ce sont des tâches "une entrée riche → une sortie structurée". Ajouter une orchestration multi-agents ajouterait de la complexité, du coût, des risques de sécurité (tool hijacking, boucles incontrôlées) sans bénéfice produit démontré. Conforme au principe "Ne crée jamais un agent simplement parce que le projet le mentionne" et "Deterministic before probabilistic" du brief.

**Avantages** : coût prévisible (1 appel = 1 coût connu), débogage trivial, sécurité simplifiée (pas de délégation d'outils entre agents), latence faible.
**Inconvénients** : si un futur besoin nécessite un vrai raisonnement multi-étapes autonome (ex: recherche web multi-sources avant scoring), il faudra réviser cet ADR.
**Risques** : sous-dimensionnement si l'usage évolue vers de l'automatisation complète (mitigé par une architecture en couches qui permet d'insérer un orchestrateur plus tard sans réécrire le domaine).
**Conséquences** : pas de framework d'agents (LangGraph, CrewAI...) nécessaire en V1 ; le "registre d'agents" ([[registry]]) est une donnée de configuration, pas du code d'orchestration.
**Migration possible** : oui, si validé par un besoin produit réel et documenté dans une révision de A-002.

## ADR-003 — Isolation par workspace plutôt que multi-tenancy SaaS stricte
**Contexte** : utilisateurs = équipe + clients internes (A-003), pas de vente à des tiers externes en V1.

**Options considérées**
1. Multi-tenancy complet (tenant_id partout, row-level security stricte, isolation infra).
2. Isolation logique par `workspace_id` avec permissions applicatives, sans infrastructure dédiée par tenant.

**Décision** : option 2, avec `workspace_id` sur toutes les tables métier dès le premier jour (pour permettre une migration vers option 1 sans réécriture), mais sans row-level security au niveau base de données en V1.

**Pourquoi** : le risque réel (fuite de données entre deux clients externes payants) n'existe pas encore. Construire l'isolation stricte maintenant serait de la sur-ingénierie (A-003, "no premature abstraction").
**Avantages** : rapidité de mise en œuvre, complexité proportionnée au risque réel actuel.
**Inconvénients** : si le produit devient un vrai SaaS vendu à des tiers, un audit de sécurité et probablement du RLS Postgres seront nécessaires avant cette bascule.
**Risques** : oubli d'un filtre `workspace_id` dans une requête = fuite de données inter-workspace. Mitigation : toute requête de lecture domaine passe par une couche d'accès aux données qui impose le filtre (pas de requête ad hoc dans les endpoints).
**Conséquences** : documenté comme dette technique conditionnelle dans [[risks]].
**Migration possible** : oui, RLS Postgres activable sans changer le schéma si `workspace_id` est déjà partout.

## ADR-004 — Intégrations externes en ports/adaptateurs, non implémentées en V1
**Contexte** : pas de CRM/email/LinkedIn réel à connecter pour l'instant (A-004), mais très probable plus tard.

**Décision** : définir des interfaces (`CRMExportPort`, futur `CRMSyncPort`, futur `EmailSendPort`) dans le domaine, sans implémentation réelle en V1 ; seule l'implémentation "export CSV / copier-coller" existe au départ.

**Pourquoi** : évite de coupler le domaine à un fournisseur précis avant de savoir lequel l'utilisateur emploie réellement ; évite aussi de développer une intégration qui ne sera peut-être jamais utilisée (no speculative features) tout en gardant le point d'extension prêt.

**Avantages** : ajout d'un connecteur réel = nouvel adaptateur, zéro changement du domaine.
**Inconvénients** : légère abstraction "à vide" en V1 (un seul adaptateur réel).
**Risques** : sur-abstraction si aucun connecteur réel n'est jamais demandé — accepté car le coût de l'interface est faible.
**Conséquences** : voir [[integrations]].

## ADR-005 — Prompts comme données versionnées, pas comme code
**Contexte** : NFR-9, NFR-10 — modification de prompt sans déploiement, revue avant mise en prod.

**Décision** : les 20 templates de prompts sont stockés comme enregistrements versionnés (fichiers structurés en V1, table `prompt_version` dès que l'édition en ligne est nécessaire), pas hardcodés dans le code applicatif.

**Pourquoi** : sépare la logique produit (stable) du contenu métier (évolutif), permet une revue humaine légère (diff de fichier) avant publication, ouvre la voie à des evals automatisés plus tard sans changer l'architecture.
**Avantages** : itération rapide sur les prompts sans redéploiement complet de l'app (si stockage DB) ou avec review de diff simple (si fichiers versionnés en Git).
**Inconvénients** : nécessite un mécanisme de publication/activation de version.
**Risques** : divergence entre versions si mal géré — mitigé par un champ `active_version` explicite par agent.
**Conséquences** : voir [[registry]] et [[governance]].
