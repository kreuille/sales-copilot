# Règles d'escalade

## Cadrage
Dans un système autonome, l'escalade répond à "quand un agent ne doit pas décider seul". Ici, **aucun agent ne décide ni n'agit seul** (ADR-002) — chaque sortie est par construction soumise à l'utilisateur. Ce document définit donc plutôt : quand le système doit **bloquer une exécution** ou **avertir l'utilisateur avant qu'il ne s'appuie sur une sortie**.

## R-1 Blocage avant exécution (pas d'escalade, un refus déterministe)
Si un champ `required` du schéma d'entrée d'un agent est manquant (contexte workspace incomplet ou saisie utilisateur incomplète), l'exécution est bloquée avec un message explicite — pas d'appel au modèle avec un contexte partiel (FR-2.2). Ce n'est pas une "escalade humaine" au sens du brief : c'est un refus déterministe, l'humain est déjà l'unique décideur.

## R-2 Avertissement de confiance déclarée par l'agent
Certains agents déclarent explicitement une confiance faible dans leur propre sortie (ex: Agent 1 "si les signaux sont faibles, dis-le", Agent 2/17 "écris inconnu plutôt que deviner"). Le produit doit **afficher visiblement** ces marqueurs de faible confiance dans l'UI (ex: badge "signal faible" ou "info manquante"), pas les enfouir dans un paragraphe de texte — pour que l'utilisateur ne les manque pas avant de s'appuyer sur la sortie.

## R-3 Sortie non conforme au schéma
Si la sortie du modèle ne respecte pas le `output_schema` attendu (champ manquant, format invalide — voir [[agent-architecture]]), le système rejette la sortie et propose un nouvel essai. Il n'y a pas d'"escalade vers un humain" au sens processus métier ici — il n'y a qu'un seul humain, déjà en attente de la sortie.

## R-4 Différence avec le brief initial
Les seuils de confiance numériques (>0.90 autonome, 0.70-0.90 selon risque, etc.) du brief initial supposent des actions automatiques déclenchées par un score de confiance. **Ce produit n'a aucune action automatique** (BR-6) : ces seuils n'ont donc pas d'application directe en V1. Ils devront être réintroduits si ADR-002 est révisé (passage à des actions semi-automatiques ou automatiques).

## R-5 Cas du Sparring Partner (Agent 12)
Seul agent conversationnel multi-tour. Règle spécifique : la simulation n'a aucun effet de bord (rien n'est jamais envoyé à un vrai prospect), donc pas de blocage de contexte requis au même niveau que les autres agents — seul le persona du prospect simulé est requis en entrée.
