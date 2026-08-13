# Exigences fonctionnelles

## FR-1 Gestion de workspace
- FR-1.1 : créer/éditer un workspace (offre, ICP, ton, tarifs).
- FR-1.2 : inviter des membres dans un workspace (A-003 : équipe/clients internes).
- FR-1.3 : le contexte de workspace est versionné (historique des modifications d'offre/ICP) pour audit et pour ne pas casser des deals en cours avec un ICP obsolète.

## FR-2 Registre d'agents
- FR-2.1 : les 20 agents sont catalogués avec leur fonction, leur prompt template, leurs champs d'entrée requis/optionnels, leur format de sortie attendu (voir [[registry]]).
- FR-2.2 : un agent ne peut être exécuté que si tous ses champs d'entrée requis sont renseignés (workspace + saisie utilisateur + éventuel contexte d'un agent amont).
- FR-2.3 : les prompts sont versionnés ; une modification de prompt crée une nouvelle version, l'historique des versions précédentes est conservé.

## FR-3 Entités prospect/deal
- FR-3.1 : créer une fiche prospect (contact + entreprise).
- FR-3.2 : rattacher un deal à un prospect (offre concernée, montant, étape).
- FR-3.3 : chaque exécution d'agent liée à un prospect/deal est journalisée (quel agent, quand, quelle entrée, quelle sortie) → alimente le [[memory-model]].
- FR-3.4 : étapes de deal explicites (repris du PDF : premier contact, après démo, propale envoyée, closing, perdu, gagné).

## FR-4 Enchaînement d'agents
- FR-4.1 : un agent peut déclarer une dépendance "peut reprendre la sortie de l'agent X" (ex: Agent 3 reprend Agent 2, Agent 16 reprend l'historique de deal).
- FR-4.2 : quand une dépendance existe, l'UI propose automatiquement la dernière sortie pertinente comme entrée pré-remplie, modifiable par l'utilisateur.
- FR-4.3 : aucun enchaînement n'est automatique/silencieux — l'utilisateur déclenche chaque agent explicitement (cohérent avec A-002 : pas d'autonomie).

## FR-5 Diagnostic / recommandation d'agents
- FR-5.1 : implémenter la grille "règle des 3 premiers agents" du PDF (PART 3) comme logique déterministe (pas un appel LLM) : symptôme → 3 agents recommandés.

## FR-6 Sortie et export
- FR-6.1 : chaque sortie d'agent est affichée structurée selon le format défini par le prompt (ex: score /10, liste de signaux).
- FR-6.2 : bouton copier / export (texte brut, markdown) pour usage hors produit (email, LinkedIn, CRM externe).
- FR-6.3 : aucune sortie n'est envoyée automatiquement à un tiers (cf. FR-4.3, A-002).

## FR-7 Historique et audit
- FR-7.1 : historique consultable par prospect/deal de toutes les exécutions d'agents.
- FR-7.2 : horodatage, utilisateur ayant déclenché l'exécution, version de prompt utilisée, modèle utilisé.

## FR-8 Import/export pipeline (sans intégration réelle, cf. A-004)
- FR-8.1 : import CSV du pipeline existant de l'utilisateur (colonnes libres, mapping manuel).
- FR-8.2 : export CSV du pipeline structuré par le produit.

## Hors périmètre V1 (explicite)
- Envoi automatique d'email/LinkedIn.
- Connecteur CRM temps réel (HubSpot, Salesforce...).
- Détection automatique de signaux (scraping web/LinkedIn automatisé) — les Agents 1/2 restent alimentés par du texte collé manuellement par l'utilisateur, exactement comme dans le PDF source.
