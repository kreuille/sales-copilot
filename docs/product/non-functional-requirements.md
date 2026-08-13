# Exigences non fonctionnelles

## Sécurité / confidentialité
- NFR-1 : les données collées dans les prompts (notes de call, infos prospects) peuvent contenir des données personnelles (PII) — traiter tout contenu comme sensible par défaut, retention et accès strictement scopés au workspace (voir [[security-architecture]]).
- NFR-2 : aucune donnée d'un workspace n'est visible par un autre workspace (isolation logique, pas nécessairement infra dédiée — A-003).
- NFR-3 : les prompts systèmes et le contexte de workspace ne doivent jamais être modifiables par du contenu externe collé par l'utilisateur (défense contre l'injection indirecte — un texte de call malveillant/piégé ne doit pas pouvoir changer le comportement de l'agent).

## Coûts LLM
- NFR-4 : chaque agent utilise le modèle le moins cher capable de produire une sortie fiable pour sa tâche ; router par classe de tâche (voir [[system-overview]] pour la proposition de routing).
- NFR-5 : pas de boucle agentique — chaque exécution est un appel unique, borné en tokens, déclenché par l'utilisateur (cohérent avec l'absence d'autonomie, A-002).

## Performance
- NFR-6 : temps de réponse perçu < 15s pour un agent simple (accroche, relance) ; agents plus longs (propale complète) peuvent dépasser avec indicateur de progression.

## Fiabilité
- NFR-7 : si un agent échoue (erreur modèle, timeout), l'entrée utilisateur n'est jamais perdue ; retry manuel possible sans ressaisie.

## Observabilité
- NFR-8 : chaque exécution d'agent journalise modèle, latence, tokens entrée/sortie, coût estimé, succès/échec — sans logger le contenu PII en clair dans les métriques agrégées (voir [[observability]]).

## Qualité des prompts
- NFR-9 : toute modification d'un prompt d'agent doit être revue avant mise en production — pas de changement "à l'intuition" sur un prompt en usage (aligné avec le principe eval-first du brief, adapté à l'échelle du produit : revue humaine en V1, evals automatisés quand le volume le justifie).

## Maintenabilité
- NFR-10 : les 20 prompts sont des données versionnées (fichiers), pas du code — modifiable sans déploiement applicatif.
