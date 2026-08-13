# Architecture de sécurité

## Périmètre de menace réel (proportionné au produit V1)
Ce produit n'exécute aucune action externe automatique et ne gère pas de paiement — le périmètre de risque est donc plus restreint que celui d'un agent autonome commercial, mais reste réel : données personnelles de prospects, secrets d'API modèle, isolation entre workspaces.

## Authentification / autorisation
- Authentification standard (email/mot de passe ou SSO) au niveau utilisateur.
- Autorisation au niveau `WORKSPACE_MEMBER.role` : `owner` (gère membres + contexte workspace), `member` (exécute agents, gère prospects/deals). Pas de rôle `admin` global multi-workspace en V1 (pas de besoin identifié).
- Toute requête API vérifie que l'utilisateur est membre du `workspace_id` ciblé, via la couche d'accès aux données (ADR-003) — jamais de vérification uniquement côté UI.

## Isolation des données
- `workspace_id` obligatoire sur toute requête de lecture/écriture (ADR-003).
- Un test automatisé dédié doit vérifier explicitement qu'un utilisateur du workspace A ne peut jamais lire/écrire une donnée du workspace B (test de non-régression permanent, cf. brief : "tester explicitement qu'un tenant A ne peut jamais accéder aux données du tenant B").

## Prompt injection / contenu externe hostile
Les notes de call, profils LinkedIn collés, etc. sont du **contenu externe non fiable** au sens du brief, même si collé manuellement par l'utilisateur (un prospect malveillant pourrait avoir écrit un texte piégé sur son propre profil LinkedIn).
- Le template système (instructions de rôle et de format) et le contenu utilisateur (notes collées) sont **toujours séparés structurellement** dans l'appel au modèle (jamais concaténés sans balisage clair) — le contenu collé ne peut jamais être interprété comme une instruction système.
- Aucune sortie de modèle n'est jamais exécutée comme code ou comme commande — c'est du texte affiché à l'utilisateur, point final.
- Le contexte workspace (offre, ICP, tarifs) n'est jamais modifiable par une sortie de modèle ; seule une action humaine explicite (formulaire d'édition) peut le changer.

## Secrets
- Clé API du fournisseur LLM : variable d'environnement / secret manager côté serveur uniquement, jamais exposée au client, jamais loggée.
- `.env.example` fourni avec noms de variables fictifs uniquement (voir Phase 1).

## Données personnelles (PII)
- Les notes prospect/contact constituent des PII. Politique : accès restreint aux membres du workspace concerné, pas d'utilisation de ces données pour entraîner ou fine-tuner un modèle, rétention documentée dans [[data-architecture]].
- Journaux techniques (latence, erreurs) : pas de PII en clair dans les logs agrégés/metrics (NFR-8) — seul l'audit log `AGENT_RUN`, scopé et accessible uniquement aux membres du workspace, contient les payloads complets.

## Actions à validation humaine
Toutes les sorties d'agent sont, par construction, `REVIEW_REQUIRED` — aucune action `AUTONOMOUS` n'existe en V1 puisque aucun agent n'a d'effet de bord externe (cf. [[governance]] pour les modes détaillés et leur future évolution si des connecteurs réels sont ajoutés).

## Ce qui est hors périmètre en V1 (documenté, pas ignoré)
- RLS PostgreSQL strict (ADR-003) — dette technique conditionnelle, voir [[risks]] et [[technical-debt]] (à créer en Phase 1).
- Chiffrement au niveau champ pour les PII — à évaluer si le volume de données sensibles justifie le coût opérationnel, en Phase 6 (hardening) si le produit progresse jusque-là.
