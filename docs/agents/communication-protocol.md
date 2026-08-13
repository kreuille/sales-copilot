# Protocole de "communication" entre agents

## Cadrage
Il n'y a pas de communication inter-agents autonome (ADR-002) : les agents ne s'appellent jamais entre eux. Ce document décrit le protocole de **handoff de contexte piloté par l'application**, qui remplace ce que serait un protocole de messages inter-agents dans un système autonome.

## Enveloppe de handoff
Quand la sortie d'un agent amont est proposée en pré-remplissage à un agent aval (FR-4), l'application transporte :
```json
{
  "source_agent_id": "agent-02-profileur",
  "source_agent_run_id": "uuid",
  "target_agent_id": "agent-03-accrocheur",
  "workspace_id": "uuid",
  "prospect_id": "uuid",
  "deal_id": "uuid | null",
  "payload_field": "prospect_brief",
  "payload_value": { "...": "sortie structurée de l'agent 2" },
  "generated_at": "iso-timestamp",
  "editable_by_user": true
}
```
Ce n'est pas un message envoyé à un "agent" au sens d'un processus qui le recevrait et déciderait quoi en faire — c'est une donnée pré-remplie dans un formulaire que l'utilisateur peut éditer avant de déclencher l'agent aval. Le seul "décideur" est l'utilisateur.

## Ce que ce protocole ne fournit pas (volontairement)
Pas de `intent`, `confidence` de délégation, `deadline`, `correlation_id` inter-agents au sens du brief original — ces champs ont du sens pour un système d'agents autonomes qui négocient/priorisent entre eux ; ici, un seul `agent_run_id` par exécution suffit à tracer la chaîne (`source_agent_run_id` suffit à reconstruire la lignée complète d'un prospect/deal via [[data-architecture]]).

## Si ADR-002 est révisé un jour
Si un futur besoin justifie une vraie orchestration multi-agents (ex: exécution en tâche de fond), ce document devra être remplacé par un vrai protocole de message asynchrone (queue, `task_id`/`correlation_id`/`permissions` comme décrit dans le brief initial) — ne pas le anticiper avant que le besoin soit réel.
