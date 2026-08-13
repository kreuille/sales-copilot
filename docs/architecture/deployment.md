# Déploiement (proposition — à valider en Phase 1)

## Environnements
| Environnement | Usage | Données |
|---|---|---|
| local | développement | données factices, pas de vraie clé LLM de prod |
| preview | revue de PR (déploiement éphémère par branche, si plateforme le permet) | données factices |
| staging | validation avant prod | données factices ou anonymisées |
| production | usage réel | données réelles des workspaces |

Aucun test automatisé n'appelle un vrai fournisseur LLM avec facturation en CI sans mock/plafond explicite (contrôle de coût).

## Infrastructure proposée (cohérente avec ADR-001)
- Application : Next.js déployée sur plateforme managée (Vercel ou équivalent).
- Base de données : PostgreSQL managé (ex: Neon/Supabase/RDS), un environnement par étage (dev/staging/prod au minimum).
- Secrets : gérés via le secret manager de la plateforme de déploiement, jamais en clair dans le repo (`.env.example` uniquement).
- Fournisseur LLM : Claude API, appelée uniquement depuis le serveur (jamais depuis le client).

## Sauvegardes
- Backups automatiques quotidiens de la base de données (rétention minimale 30 jours), avec test de restauration documenté avant mise en production réelle (Phase 7).

## Rollback
- Déploiements versionnés (chaque déploiement = un commit taggé) ; rollback = redéploiement de la version précédente. Les migrations de schéma doivent être rétro-compatibles au moins une version en arrière pour permettre un rollback sans perte.

## CI/CD (cible, à construire en Phase 1)
```
install → lint → typecheck → unit tests → integration tests (DB) → build → smoke tests → deploy staging → (validation manuelle) → deploy production
```
Une étape en échec bloque le déploiement. Pas d'étape "agent evals" automatisée tant qu'il n'y a pas de dataset de test constitué (voir [[roadmap]] pour le moment où l'introduire).

## Ce qui est explicitement différé
Infrastructure as Code formalisée (Terraform...) — proportionné une fois l'infra dépasse ce qu'une plateforme managée console peut gérer proprement à la main. Documenté comme dette technique conditionnelle si le produit grossit.
