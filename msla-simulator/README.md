# Simulateur MSLA (LCD vs DLP)

Simulateur de précision d'impression résine (LCD/MSLA et DLP) pour modèles dentaires, en 3 langues (FR/EN/ZH),
avec guide pas à pas et compensation ML.

- `deploy/site/light/index.html` : l'application (un seul fichier HTML statique, aucune dépendance sauf Google Fonts).
- `deploy/` : audit VPS (lecture seule), sauvegarde, rollback, mise à jour, configs nginx/Caddy/Traefik. Voir `deploy/LISEZMOI.md`.
- `ml/` : boîte à outils Python (simulation, jeu de données, récupérabilité, U-Net, calibration). Voir `ml/README.md`.

Cible de déploiement : https://simulation.guedou.ch/light/
