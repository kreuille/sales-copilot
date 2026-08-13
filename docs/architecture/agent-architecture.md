# Architecture des "agents" (prompt-agents)

## Ce qu'est un agent ici
Un agent n'est **pas** un processus autonome. C'est la combinaison de :
1. Un **template de prompt versionné** (texte avec placeholders), directement dérivé des 20 prompts du PDF.
2. Un **schéma d'entrée** (quels champs sont requis/optionnels, d'où ils viennent : workspace, saisie utilisateur, sortie d'un agent amont).
3. Un **schéma de sortie** (structure attendue, ex: score, justification, liste de signaux) permettant de stocker la sortie en données structurées (BR-7).
4. Une **fonction d'assemblage déterministe** qui construit le prompt final à partir de (1)+(2) et l'envoie en un seul appel au modèle.

## Anatomie d'un agent (exemple : Agent 7, Le Qualificateur)
```yaml
id: agent-07-qualificateur
function_id: F4-qualification
name: "Le Qualificateur"
purpose: "Qualifier froidement un deal après un call de découverte, sans optimisme de vendeur."
input_schema:
  - field: offer_and_price
    source: workspace_context.pricing_summary
    required: true
  - field: discovery_notes
    source: user_input
    required: true
output_schema:
  - field: score_pain
  - field: score_budget
  - field: score_decision
  - field: score_timing
  - field: score_fit
  - field: global_score
  - field: closing_probability
  - field: missed_question
  - field: next_action
confidence_policy: "Le prompt impose déjà le pessimisme par défaut (BR-2) ; le produit n'ajoute pas de seuil de confiance numérique supplémentaire ici, l'agent est un outil d'aide à la décision, jamais une action automatique."
upstream_agents: []
downstream_agents: [agent-16-strategie-closing]
human_validation: "toujours — la sortie est un avis structuré, jamais une action"
```

Ce format est répété pour les 20 agents dans [[registry]] (registre complet, `agents/registry.yaml`).

## Pourquoi pas de "vrais" agents autonomes ici
Voir ADR-002. Les critères d'éligibilité à un futur "agent autonome" (si jamais un besoin apparaît) seraient : (a) la tâche nécessite plusieurs appels LLM avec décision intermédiaire, (b) la tâche nécessite d'appeler des outils externes de façon conditionnelle, (c) une action a un effet de bord externe (envoi, écriture CRM tiers). Aucun des 20 agents source ne remplit ces critères en V1.

## Classes de modèle (routing coût, NFR-4)
| Classe | Usage | Exemples d'agents |
|---|---|---|
| FAST/CHEAP | Extraction/structuration simple, faible enjeu de nuance | Agent 17 (Greffier), Agent 18 (Compte Rendu) |
| BALANCED | Rédaction avec nuance, scoring argumenté | Agent 3, 5, 11, 15 |
| DEEP_REASONING | Analyse multi-critères à enjeu (qualification, stratégie de closing, sparring) | Agent 7, 8, 12, 16 |

Le mapping précis modèle→classe est un paramètre de configuration, pas une décision architecturale figée (permet de suivre l'évolution de l'offre de modèles sans changer le code).

## Contrat de sortie et qualité
Chaque agent doit respecter le contrat de sortie défini par son `output_schema`. Si le modèle renvoie une sortie non conforme (champ manquant, format invalide), le `PromptEngine` (voir [[system-overview]]) rejette la sortie et propose un retry manuel — jamais d'auto-correction silencieuse qui pourrait masquer une hallucination.
