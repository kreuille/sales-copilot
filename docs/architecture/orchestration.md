# Orchestration

## Principe
Pas d'orchestrateur multi-agents (ADR-002). L'"orchestration" ici se limite à deux mécanismes déterministes :

## 1. Recommandation d'agents (BR-5, FR-5)
Table de règles statique, pas de LLM :
```
symptom: "je_ne_contacte_personne"      -> [agent-01, agent-02, agent-03]
symptom: "on_me_repond_mais_ca_signe_pas" -> [agent-07, agent-11, agent-16]
symptom: "pipe_cimetiere"                -> [agent-05, agent-06, agent-09]
symptom: "je_vends_mais_chaos"           -> [agent-17, agent-18, agent-10]
```
Reprend exactement la grille PART 3 du PDF.

## 2. Enchaînement de contexte (FR-4)
Chaque agent déclare `upstream_agents` (voir [[agent-architecture]]). Quand l'utilisateur ouvre un agent ayant un upstream déjà exécuté sur le même prospect/deal, l'UI pré-remplit le champ correspondant avec la dernière sortie pertinente. L'utilisateur peut toujours l'éditer avant exécution. Aucun agent n'appelle un autre agent lui-même — c'est l'application qui orchestre l'affichage, jamais le modèle qui décide d'invoquer un autre agent.

## Ce qui est explicitement exclu de la V1
- Pas de state machine de workflow complexe (le "workflow" perçu par l'utilisateur est en réalité une suite d'actions humaines explicites, chacune journalisée).
- Pas de queue asynchrone / worker : chaque exécution d'agent est synchrone, déclenchée par une requête utilisateur, retournée dans le même cycle requête/réponse (avec état de chargement si latence modèle élevée).
- Pas d'event-driven architecture : le volume et la nature du produit (usage manuel, pas de flux temps réel entrant) ne le justifient pas.

## Quand réviser cette page
Si un besoin réel apparaît pour : exécuter un agent en tâche de fond, réagir à un événement externe (ex: webhook CRM), ou enchaîner plusieurs agents sans validation humaine intermédiaire — ces trois cas nécessiteraient de rouvrir ADR-002 et de concevoir une vraie couche d'orchestration (queue + state machine), pas juste d'ajouter du code ad hoc.
