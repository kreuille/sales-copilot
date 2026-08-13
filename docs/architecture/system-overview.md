# Vue d'ensemble système

## Cadrage
Copilote semi-assisté, multi-workspace, sans agents autonomes ni intégrations externes réelles en V1 (voir [[assumptions]] A-002 à A-004). Le système est un **CRUD applicatif classique** (workspaces, prospects, deals, historique) enrichi d'une **couche de génération LLM synchrone, déclenchée par l'utilisateur, sans état persistant côté modèle**.

## Diagramme de contexte

```mermaid
graph TD
    User[Utilisateur - membre d'un workspace] --> WebApp[Application Web]
    WebApp --> API[API applicative]
    API --> AuthN[Authentification / Authorization]
    API --> Domain[Couche domaine : Workspace, Prospect, Deal, AgentRun]
    Domain --> DB[(Base de données)]
    API --> PromptEngine[Moteur de prompts : registre + injection de contexte]
    PromptEngine --> Registry[(Registre d'agents versionné - fichiers/DB)]
    PromptEngine --> LLM[Fournisseur LLM - Claude API]
    Domain --> AuditLog[(Journal d'audit des exécutions)]
    API --> Export[Export CSV / copier-coller]
    User -.copie manuelle.-> ExternalTools[CRM / Email / LinkedIn externes]
```

Points clés :
- Aucune flèche automatique vers `ExternalTools` : toute sortie franchit la frontière du système par une action humaine (copier, exporter), jamais par un appel API sortant du système vers un tiers de communication.
- `PromptEngine` n'est pas un orchestrateur multi-agents : c'est une fonction déterministe (assemble contexte workspace + contexte deal + entrée utilisateur + template versionné → un seul appel LLM → sortie structurée validée).

## Flux d'exécution d'un agent (séquence)

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant API as API
    participant PE as PromptEngine
    participant DB as Base de données
    participant LLM as Claude API

    U->>API: Sélectionne agent + saisit entrée
    API->>DB: Charge contexte workspace + contexte deal (si lié)
    API->>PE: assemble(template, contexte, entrée)
    PE->>PE: valide champs requis (BR / FR-2.2)
    alt champ requis manquant
        PE-->>API: erreur de validation
        API-->>U: demande de compléter le contexte
    else contexte complet
        PE->>LLM: appel unique, sans boucle
        LLM-->>PE: sortie brute
        PE->>PE: parse vers format structuré attendu par l'agent
        PE-->>API: sortie structurée + confiance déclarée
        API->>DB: journalise AgentRun (audit)
        API-->>U: affiche sortie, propose copier/export
    end
```

## Classes de composants
| Composant | Nature | Pourquoi pas un agent autonome |
|---|---|---|
| Recommandation d'agents (BR-5, FR-5) | Code déterministe (table de règles) | Mapping symptôme → agents fixe, pas de raisonnement nécessaire |
| Validation des champs requis (FR-2.2) | Code déterministe | Règle de complétude, pas de jugement |
| Génération de sortie d'agent | 1 appel LLM synchrone | Cœur de valeur : rédaction/raisonnement qualitatif |
| Enchaînement de contexte (FR-4) | Code déterministe (pré-remplissage UI) | Récupération de données, pas de décision |
| Historique / audit | Code déterministe + stockage | Doit être fiable à 100%, jamais probabiliste |

Voir ADR-002 dans [[architecture-decisions]] pour la justification complète du choix "pas d'agents autonomes".
