# Architecture des données

## Modèle de domaine (entités principales)

```mermaid
erDiagram
    WORKSPACE ||--o{ WORKSPACE_MEMBER : contient
    WORKSPACE ||--o{ PROSPECT : contient
    WORKSPACE ||--o{ DEAL : contient
    WORKSPACE ||--o{ AGENT_RUN : journalise
    WORKSPACE ||--|| WORKSPACE_CONTEXT : a
    PROSPECT ||--o{ DEAL : concerne
    PROSPECT ||--o{ AGENT_RUN : concerne
    DEAL ||--o{ AGENT_RUN : concerne
    DEAL ||--o{ DEAL_STAGE_EVENT : historise
    AGENT ||--o{ AGENT_PROMPT_VERSION : versionne
    AGENT_PROMPT_VERSION ||--o{ AGENT_RUN : execute

    WORKSPACE {
      uuid id PK
      string name
      timestamp created_at
    }
    WORKSPACE_CONTEXT {
      uuid workspace_id FK
      text offer_description
      text icp_description
      text tone
      text pricing_summary
      int version
      timestamp updated_at
    }
    WORKSPACE_MEMBER {
      uuid id PK
      uuid workspace_id FK
      uuid user_id FK
      string role
    }
    PROSPECT {
      uuid id PK
      uuid workspace_id FK
      string full_name
      string company
      string role_title
      text raw_notes
      timestamp created_at
    }
    DEAL {
      uuid id PK
      uuid workspace_id FK
      uuid prospect_id FK
      string stage
      numeric estimated_amount
      timestamp last_action_at
    }
    DEAL_STAGE_EVENT {
      uuid id PK
      uuid deal_id FK
      string from_stage
      string to_stage
      timestamp occurred_at
    }
    AGENT {
      uuid id PK
      string code
      string name
      string function_id
    }
    AGENT_PROMPT_VERSION {
      uuid id PK
      uuid agent_id FK
      int version_number
      text template
      json input_schema
      json output_schema
      boolean is_active
    }
    AGENT_RUN {
      uuid id PK
      uuid workspace_id FK
      uuid agent_prompt_version_id FK
      uuid prospect_id FK
      uuid deal_id FK
      uuid triggered_by_user_id FK
      json input_payload
      json output_payload
      string model_used
      int tokens_in
      int tokens_out
      numeric estimated_cost
      string status
      timestamp created_at
    }
```

## Principes
- **IDs immuables** : `uuid` partout, jamais de clé métier (nom, email) comme clé technique.
- **`workspace_id` obligatoire** sur toutes les tables métier dès le premier jour (ADR-003), même sans RLS activé en V1.
- **Pas de résumé LLM comme source de vérité** (BR-7) : `AGENT_RUN.output_payload` est structuré (JSON conforme au `output_schema` de l'agent), pas un simple bloc de texte. Le texte libre reste disponible pour affichage/copie mais les champs exploitables (score, étape recommandée, etc.) sont extraits en champs typés.
- **Historique immuable** : `AGENT_RUN` et `DEAL_STAGE_EVENT` ne sont jamais mis à jour, seulement insérés — sert d'audit log (voir [[security-architecture]]).
- **Versionnement du contexte workspace** : `WORKSPACE_CONTEXT` versionné pour ne pas casser rétroactivement l'interprétation d'un `AGENT_RUN` passé si l'ICP change.

## Rétention
| Donnée | Propriétaire | Rétention par défaut | Justification |
|---|---|---|---|
| `PROSPECT`, `DEAL` | Workspace | Tant que le workspace existe | Donnée métier active |
| `AGENT_RUN` | Workspace | Minimum 12 mois (audit), configurable | Traçabilité des décisions, coûts |
| `WORKSPACE_CONTEXT` (versions passées) | Workspace | Conservé indéfiniment (léger volume) | Explique le comportement passé des agents |
| Logs techniques (latence, erreurs) | Système | 90 jours | Debug opérationnel, pas de valeur métier long terme |

## Ce que ce modèle ne couvre pas (volontairement)
Pas de table `Company` enrichie automatiquement (pas de scraping/enrichissement automatique, cf. FR "hors périmètre V1") — `PROSPECT.raw_notes` et `company` restent des champs saisis/collés par l'utilisateur.
