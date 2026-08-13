# Modèle de mémoire

Reprend la distinction du brief initial, adaptée à un système sans agents autonomes.

## Mémoire éphémère (contexte d'exécution)
- Durée de vie : le temps d'une exécution d'agent (un appel).
- Contenu : le prompt assemblé (template + contexte + entrée utilisateur) envoyé au modèle.
- Ne persiste pas au-delà de l'appel, sauf dans `AGENT_RUN` (voir mémoire commerciale ci-dessous, qui est la persistance, pas la mémoire éphémère elle-même).

## Mémoire utilisateur
- Préférences d'affichage, agents favoris/récents. Faible enjeu, pas de PII sensible.

## Mémoire workspace (équivalent "account/company" du brief, élargi au niveau workspace)
- `WORKSPACE_CONTEXT` : offre, ICP, ton, tarifs — versionné (voir [[data-architecture]]).
- Propriétaire : le workspace. Source : saisie humaine explicite uniquement (jamais déduite automatiquement d'une sortie d'agent, pour éviter qu'une hallucination pollue le contexte de tous les agents suivants).

## Mémoire commerciale (historique)
- `AGENT_RUN`, `DEAL_STAGE_EVENT` : historique des interactions, décisions, sorties d'agents par prospect/deal.
- C'est la mémoire qui alimente le handoff de contexte ([[communication-protocol]]) et les agents "historique" (Relanceur, Réanimateur, Stratège de Closing).

## Knowledge Base
- **Absente en V1.** Aucun besoin de RAG identifié : les 20 agents source ne référencent pas de base de connaissance externe durable (pas de documentation produit à interroger, pas de base de cas clients). Si un besoin apparaît (ex: bibliothèque de cas clients réutilisables pour les propales), il faudra concevoir cette couche explicitement plutôt que de la supposer.

## Audit log
- `AGENT_RUN` sert aussi d'audit log immuable (voir [[security-architecture]]) : qui a déclenché quoi, quand, avec quelle version de prompt, quel modèle, quel coût.

## Ce que ce modèle évite explicitement
Stocker un "résumé mémoire" généré par LLM comme source de vérité sur un prospect/deal (BR-7) — chaque agent qui produit une information structurée (score, étape recommandée) l'écrit dans un champ typé, pas seulement dans un texte libre difficile à interroger plus tard.
