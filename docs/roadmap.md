# Roadmap

Adaptée du cadrage en 7 phases du brief initial à la réalité du produit validé (copilote semi-assisté, pas de SaaS multi-agents complexe). Les phases 4-7 du brief original (workflows commerciaux complets, intégrations réelles, hardening, prod readiness) sont conservées en structure mais fortement réduites en portée tant qu'elles ne sont pas justifiées par un usage réel.

## Phase 0 — Discovery (cette session)
- Lecture intégrale de la source (PDF), cadrage produit validé avec l'utilisateur (A-002 à A-005).
- Spécification complète : `/docs`, `/agents/registry.yaml`, `CLAUDE.md`.
- **Sortie** : ce livrable. Revue de cohérence produit + architecture + sécurité avant Phase 1 (voir tâche de vérification finale).

## Phase 1 — Foundation
- Initialiser le repo (structure de dossiers applicative), valider ADR-001 (stack) avec l'utilisateur.
- Base de données + migrations pour le modèle de [[data-architecture]] (Workspace, Prospect, Deal, Agent, AgentPromptVersion, AgentRun).
- Authentification + autorisation par workspace (voir [[security-architecture]]).
- Transcription verbatim des 20 prompts source dans `agents/registry.yaml` (remplace les placeholders `TO BE TRANSCRIBED VERBATIM`).
- CI minimal (lint, typecheck, unit tests) + environnement local.

## Phase 2 — Vertical slice
- Choisir UN parcours représentatif de bout en bout : recommandé = **F1 Prospection** (Agent 1 → Agent 2 → Agent 3), car il couvre : saisie contexte workspace, exécution d'un agent isolé, handoff de contexte entre deux agents, affichage de sortie structurée, historique.
- Objectif explicite : valider l'architecture (PromptEngine, schémas d'entrée/sortie, UI de handoff), pas encore couvrir toutes les fonctions.
- Mesurer les métriques produit définies dans [[vision]] sur ce slice avant d'aller plus loin (répond à R-01/R-10 dans [[risks]]).

## Phase 3 — Core agents (extension progressive)
- Ajouter les agents restants par fonction, en commençant par les fonctions couvrant "la règle des 3 premiers agents" (F1, F4+F6+F8, F3+F5, F9+F5 — voir grille dans [[orchestration]]).
- Pour chaque agent : spec (déjà faite en Phase 0), transcription prompt, tests, ajout au registre applicatif, documentation.
- Cas particulier Agent 12 (Sparring Partner) traité séparément (UI conversationnelle dédiée).

## Phase 4 — Couverture complète des 10 fonctions
- Compléter les agents restants jusqu'aux 20.
- Introduire les evals légers (dataset de cas nominal/ambigu/donnée manquante par agent) une fois qu'il y a un usage réel à observer — pas avant, pour ne pas halluciner un besoin (cf. R-01).

## Phase 5 — Intégrations (conditionnelle)
- Ne démarre que si A-004 est invalidée par un besoin réel confirmé par l'utilisateur.
- Premier candidat probable : export/sync CRM léger (Notion/Airtable, cités dans le prompt de l'Agent 17).

## Phase 6 — Hardening (conditionnelle, si usage réel dépasse le cercle interne)
- Revue de sécurité, activation de RLS Postgres si passage à un usage multi-tenant élargi (ADR-003 révisée), test de charge si le volume le justifie.

## Phase 7 — Production readiness (conditionnelle)
- RUNBOOK, SECURITY.md, disaster recovery — à produire quand le produit a des utilisateurs réels dépendants de sa disponibilité, pas avant (proportionnalité).

## Revue de cohérence après chaque phase
Avant de passer à la phase suivante : revue produit + architecture + sécurité + IA + données + opérations (grille du brief initial), documentée comme mise à jour de ce fichier et de [[risks]].
