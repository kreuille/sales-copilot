# Gouvernance des agents

## Principe de moindre privilège appliqué à un système sans agents autonomes
Même sans agents autonomes, le principe de moindre privilège s'applique à trois niveaux :
1. **Accès aux données** : un agent ne reçoit dans son prompt assemblé que les champs définis par son `input_schema` (voir [[registry]]) — jamais l'intégralité de la base du workspace. Ex : l'Agent 3 (Accrocheur) reçoit le brief du prospect, pas l'historique financier des autres deals du workspace.
2. **Aucun outil, aucune action externe** : aucun agent n'a accès à un outil d'écriture externe (email, CRM tiers, LinkedIn) en V1 — cohérent avec A-004/ADR-004. Si un connecteur réel est ajouté un jour, il ne doit être exposé qu'à l'action humaine qui déclenche l'envoi, jamais directement pilotable par une sortie de modèle.
3. **Aucune modification du contexte système** : une sortie de modèle ne peut jamais modifier `WORKSPACE_CONTEXT`, un `AGENT_PROMPT_VERSION`, ou tout autre paramètre de gouvernance — seule une action humaine explicite (formulaire, publication de version) le peut (cf. [[security-architecture]]).

## Modes d'action (adaptés du brief)
| Mode | Application dans ce produit |
|---|---|
| AUTONOMOUS | **Inexistant en V1** — aucune sortie d'agent ne déclenche une action sans validation humaine. |
| REVIEW_REQUIRED | **Mode par défaut de tous les agents** — la sortie est affichée, l'utilisateur décide de l'utiliser, l'éditer ou l'ignorer. |
| APPROVAL_REQUIRED | Réservé aux futures EXTERNAL_ACTION/COMMUNICATION_ACTION si des connecteurs réels sont ajoutés (ex: envoi email automatique) — non applicable en V1 car aucune action de ce type n'existe. |
| BLOCKED | Toute exécution avec un `input_schema` incomplet (R-1 dans [[escalation-rules]]). |

## Cycle de vie d'un prompt (versionnement, NFR-9/NFR-10, ADR-005)
1. Toute modification du texte d'un agent crée une nouvelle `AGENT_PROMPT_VERSION` (jamais d'édition en place de la version active).
2. Revue humaine obligatoire avant activation d'une nouvelle version (a minima : relecture par un second membre du workspace admin, ou par l'auteur du produit en phase V1 solo).
3. La version précédente reste consultable — permet de comprendre pourquoi une sortie passée différait d'une sortie actuelle.
4. Quand le volume d'usage le justifie (voir [[roadmap]]), introduire des evals automatisés avant d'activer une nouvelle version (cf. brief : "une modification de prompt ne doit jamais être poussée en production uniquement sur intuition").

## Frontières explicites (ce qu'un agent ne doit jamais faire, dérivé des règles métier)
- Un agent de rédaction (Accrocheur, Rédacteur de Propale...) ne modifie jamais directement une fiche CRM/deal — seul le Greffier (Agent 17) produit une sortie destinée à alimenter le CRM, et seulement sur validation humaine.
- Un agent d'analyse (Qualificateur, Analyste de Pipeline...) ne déclenche jamais d'action — il produit un avis structuré, point final.
- Aucun agent ne doit recevoir dans son prompt des données d'un autre workspace, même en cas de bug applicatif — la couche d'accès aux données doit le rendre structurellement impossible (voir [[security-architecture]]).
