# Registre des agents — vue lisible

Vue humaine du registre machine `agents/registry.yaml`. 20 agents, 10 fonctions, directement dérivés des prompts du PDF source (texte des prompts non reproduit intégralement ici pour éviter la duplication — la version canonique est le fichier YAML).

| # | Agent | Fonction | Upstream | Downstream | Classe modèle |
|---|---|---|---|---|---|
| 1 | Le Chasseur de Signaux | F1 Prospection | — | Agent 2 | BALANCED |
| 2 | Le Profileur | F1 Prospection | Agent 1 (optionnel) | Agent 3 | BALANCED |
| 3 | L'Accrocheur | F2 Outreach | Agent 2 | Agent 4 | BALANCED |
| 4 | L'Architecte de Séquence | F2 Outreach | Agent 2, 3 | — | BALANCED |
| 5 | Le Relanceur | F3 Follow-up | historique deal | — | FAST/CHEAP |
| 6 | Le Réanimateur | F3 Follow-up | historique deal | — | BALANCED |
| 7 | Le Qualificateur | F4 Qualification | notes de call | Agent 16 | DEEP_REASONING |
| 8 | Le Détecteur de Red Flags | F4 Qualification | historique échanges | — | DEEP_REASONING |
| 9 | L'Analyste de Pipeline | F5 Pipeline | export pipeline | Agent 10 | DEEP_REASONING |
| 10 | Le Priorisateur | F5 Pipeline | Agent 9 (optionnel) | — | BALANCED |
| 11 | Le Désamorceur | F6 Objections | contexte deal | — | BALANCED |
| 12 | Le Sparring Partner | F6 Objections | — | — | BALANCED (conversationnel multi-tour, cf. note) |
| 13 | Le Préparateur de Démo | F7 Démo | brief/notes découverte | — | DEEP_REASONING |
| 14 | Le Débriefeur de Call | F7 Démo | transcript/notes | Agent 15, 18 | BALANCED |
| 15 | Le Rédacteur de Propale | F8 Proposal | notes call, Agent 14 (optionnel) | — | DEEP_REASONING |
| 16 | Le Stratège de Closing | F8 Proposal | historique deal, Agent 7 (optionnel) | — | DEEP_REASONING |
| 17 | Le Greffier | F9 CRM/ops | notes en vrac | — | FAST/CHEAP |
| 18 | Le Rédacteur de Compte Rendu | F9 CRM/ops | notes call, Agent 14 (optionnel) | — | FAST/CHEAP |
| 19 | L'Analyste de Perf | F10 Performance | chiffres funnel | — | BALANCED |
| 20 | Le Coach de Rétro | F10 Performance | plan de semaine (Agent 10), résultats réels | — | BALANCED |

## Note sur l'Agent 12 (Sparring Partner)
Seul agent du registre qui est **conversationnel multi-tour par nature** (simulation de jeu de rôle jusqu'à "STOP"). Ce n'est pas un agent autonome au sens du brief (aucune action externe, pas d'outils) — c'est une conversation LLM classique avec état de session éphémère, gérée comme un cas particulier d'UI (fil de discussion dédié) plutôt que comme le pattern "une entrée → une sortie structurée" des 19 autres agents. Documenté explicitement pour ne pas être oublié en Phase 3.

## Source de vérité
Le contenu exact des 20 prompts (texte complet) est repris depuis le PDF source et doit être transcrit tel quel dans `agents/registry.yaml` (champ `template`) en Phase 1, avec uniquement l'ajout du balisage de séparation contexte-système / contenu-utilisateur (cf. [[security-architecture]]) — pas de reformulation du contenu métier sans revue.
