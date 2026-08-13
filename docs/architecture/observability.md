# Observabilité

## Ce qui doit être observable
Toute exécution d'agent (le seul "chemin critique" probabiliste du système) doit produire, par exécution (`AGENT_RUN`) :
```
agent_code
agent_prompt_version
model_used
workspace_id
triggered_by_user_id (pas de PII dans les metrics agrégées, uniquement dans l'audit log scopé)
latency_ms
tokens_in / tokens_out
estimated_cost
status: success | validation_error | model_error | timeout
```

## Logs vs métriques vs audit log
- **Logs structurés** (techniques) : erreurs d'appel modèle, timeouts, erreurs de validation de schéma — 90 jours de rétention, pas de PII en clair.
- **Métriques** (agrégées) : latence p50/p95 par agent, coût total par workspace/mois, taux d'échec par agent — alimentent le suivi de coût (NFR-4) et la détection de dérive qualité (ex: un agent dont le taux d'erreur de format augmente après un changement de version de prompt).
- **Audit log** (`AGENT_RUN`, table domaine) : payload complet entrée/sortie, immuable, accessible uniquement aux membres du workspace concerné — c'est la seule couche où le contenu métier (donc potentiellement PII) est conservé en clair, avec la rétention définie dans [[data-architecture]].

## Métriques produit (à mesurer dès qu'il y a de l'usage réel)
- Nombre d'agents distincts activés par workspace/semaine.
- Taux de réutilisation d'un agent (utilisé >1 fois vs essayé une fois puis abandonné) — détecte le "piège du collectionneur".
- Taux d'enchaînement (agent exécuté avec un `upstream` pré-rempli utilisé) vs exécution isolée.
- Coût moyen par exécution d'agent, par classe de modèle (FAST/BALANCED/DEEP_REASONING).

## Alerting minimal V1
- Taux d'échec d'un agent > seuil sur une fenêtre glissante → alerte (indique un problème de prompt ou de fournisseur modèle).
- Coût journalier par workspace dépassant un budget configuré → alerte (contrôle de coût, NFR-4).

## Ce qui n'est pas nécessaire en V1
Tracing distribué multi-services (pas d'architecture distribuée en V1 — un seul service applicatif). À réévaluer si l'architecture se décompose en plusieurs services.
