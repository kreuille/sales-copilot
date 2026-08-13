# Registre des hypothèses

Toute hypothèse structurante doit apparaître ici avec : ID, origine, niveau de confiance, impact, méthode de validation.

## A-001 — Nature réelle du document source
- **Origine** : lecture intégrale du PDF fourni ("20 Agents Claude Spécialisés — La Machine Commerciale du Sales qui Fait 5 Jobs à la Fois", Eric Djavid, 17 pages). La page Notion citée dans le brief initial était inaccessible (pas d'authentification disponible dans cet environnement) ; le PDF fourni en pièce jointe en est le contenu.
- **Constat** : le document est un **lead magnet marketing**, pas une spécification produit. Il contient 10 fonctions commerciales × 2 prompts texte statiques ("copier-coller dans Claude, remplacer les [CROCHETS]"), destinés à un usage 100% manuel, une conversation à la fois. Il ne décrit ni orchestration, ni outils, ni mémoire persistante, ni modèle de données, ni intégrations CRM/email réelles, ni permissions, ni multi-tenance. La dernière partie du document fait la promotion d'une formation payante ("SOLO AI MACHINE").
- **Confiance** : Haute (lecture complète des 17 pages, texte extrait intégralement).
- **Impact** : Majeur. Le brief d'ingénierie initial supposait un produit SaaS agentique complexe (20 agents autonomes, orchestration, sécurité multi-tenant, CI/CD, MCP...) directement dérivé du Notion. Ce niveau de complexité n'est **pas justifié par la source** — il aurait fallu l'inventer entièrement, ce qui va à l'encontre du principe "no speculative features" du même brief.
- **Résolution** : question posée à l'utilisateur (voir A-002 à A-005). Confirmé : on construit un **copilote semi-assisté**, pas un SaaS multi-agents autonome.
- **Validation** : tranchée par l'utilisateur le 2026-08-12 via question directe.

## A-002 — Type de produit
- **Décision utilisateur** : "Copilote semi-assisté" — une application qui structure les 20 prompts, garde un contexte persistant (offre, ICP, historique de deal), enchaîne les agents dans le bon ordre et affiche le résultat. **Aucune action n'est envoyée automatiquement** à un prospect (pas d'auto-send email/LinkedIn). L'humain reste décisionnaire à chaque étape.
- **Confiance** : Haute (choix explicite).
- **Impact** : élimine la quasi-totalité des exigences de gouvernance d'agents autonomes (escalade multi-agents, tool hijacking inter-agents, actions destructrices automatiques). Les "agents" du produit sont en réalité des **templates de prompt + contexte injecté**, exécutés à la demande de l'utilisateur, jamais en tâche de fond.
- **Comment invalider** : si l'utilisateur demande plus tard un envoi automatique (email/LinkedIn), cette hypothèse tombe et il faut réintroduire la couche human-in-the-loop/approval du brief initial (voir [[governance]]).

## A-003 — Utilisateurs cibles
- **Décision utilisateur** : "Mon équipe / mes clients en interne" — pas un usage strictement solo, pas un SaaS public à vendre.
- **Confiance** : Moyenne — le libellé est ambigu entre "mon équipe interne" et "mes clients (externes) que je gère en interne". Traité comme : plusieurs utilisateurs de confiance, chacun avec un ou plusieurs **workspaces** (un workspace = une offre/ICP/pipeline), sans isolation stricte de sécurité type SaaS commercial (pas de facturation, pas de row-level security multi-tenant durcie dès le jour 1).
- **Impact** : nécessite une authentification basique et une séparation de données **par workspace**, mais pas l'infrastructure complète de multi-tenancy (billing, quotas par tenant, isolation réseau).
- **Comment invalider** : si le produit doit être vendu à des tiers non liés à l'équipe d'Arnaud, réviser vers un modèle multi-tenant strict (voir [[security-architecture]]).

## A-004 — Intégrations externes
- **Décision utilisateur** : aucune intégration réelle (CRM, email, LinkedIn) pour l'instant — "à prévoir plus tard".
- **Confiance** : Haute.
- **Impact** : l'architecture doit prévoir des **ports/adaptateurs** (interface `CRMConnector`, `EmailConnector`, etc.) sans implémentation réelle en V1. Le "CRM" du produit est donc interne (stockage propre des contacts/deals), avec export/copier-coller vers l'outil externe de l'utilisateur.
- **Comment invalider** : dès qu'un connecteur réel est demandé (ex: HubSpot), l'implémenter derrière l'interface définie dans [[integrations]] sans changer le cœur du domaine.

## A-005 — Portée de cette session
- **Décision utilisateur** : produire la spécification complète avant tout code (Phase 0 du brief).
- **Confiance** : Haute.
- **Impact** : cette session livre uniquement `/docs`, `/agents` (registre) et `CLAUDE.md`. Aucun code applicatif n'est écrit ici.

## A-006 — Stack technique
- **Origine** : aucune stack n'est imposée par la source ni par l'utilisateur.
- **Décision utilisateur** : ADR-001 validé tel que proposé — Next.js (App Router, TypeScript) + PostgreSQL + Prisma, déployé sur Vercel.
- **Confiance** : Haute (choix explicite du 2026-08-12).
- **Impact** : voir ADR-001 dans [[architecture-decisions]]. Le code applicatif de la Phase 1 peut démarrer sur cette base.
- **Comment invalider** : si un besoin réel (calcul lourd, contrainte d'hébergement, etc.) apparaît plus tard, réviser ADR-001 explicitement plutôt que de dériver silencieusement.

## A-007 — Accès Prisma via driver adapter (`@prisma/adapter-pg`) plutôt que le moteur binaire par défaut
- **Origine** : la machine de développement utilisée pour la Phase 1 bloque l'exécution de binaires natifs fraîchement téléchargés (politique de sécurité Windows, probablement AppLocker/EDR) — `schema-engine-windows.exe` et le moteur de requête par défaut de Prisma échouent avec `EPERM`/`Accès refusé`.
- **Décision** : `lib/db/client.ts` instancie `PrismaClient` avec l'adaptateur `@prisma/adapter-pg` (node-postgres pur JS), qui exécute les requêtes sans spawn de process externe. La migration initiale a en conséquence été écrite à la main (voir R-11 dans [[risks]]) puisque `prisma migrate dev` dépend du même binaire bloqué.
- **Confiance** : Haute pour le choix de l'adaptateur (solution stable et documentée par Prisma, pas un contournement fragile) ; Basse pour la fidélité exacte de la migration écrite à la main tant qu'elle n'a pas été validée par un `prisma migrate diff` sur un poste non restreint ou en CI.
- **Impact** : aucun changement de comportement applicatif — l'adaptateur `pg` est une méthode de connexion supportée nativement par Prisma 7, pas une bibliothèque tierce de contournement. Le seul risque réel est une divergence entre `migration.sql` et `schema.prisma` (R-11).
- **Comment invalider** : une fois `prisma migrate dev` exécutable sur un poste de l'équipe, reconcilier la migration à la main et, si souhaité, revenir au moteur binaire par défaut (l'adaptateur peut aussi être conservé — c'est l'approche recommandée par Prisma pour les déploiements serverless).
