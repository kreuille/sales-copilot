# Déploiement sûr de simulation.guedou.ch/light/ (VPS avec n8n)

L'ancien `deploy.sh` n'est PAS à utiliser : il installerait nginx et entrerait en conflit
avec le reverse proxy de n8n (ports 80/443).

## Étapes
1. DNS IONOS : enregistrement A `simulation` -> IPv4 du VPS (n'affecte pas les autres sous-domaines).
2. SSH : `ssh utilisateur@IP` (de préférence par clé ; jamais de mot de passe dans une conversation).
3. `sudo ./audit.sh | tee audit.txt` (lecture seule) -> coller le résultat dans la conversation.
4. `sudo ./backup.sh`
5. Selon l'audit : nginx-snippet.conf, caddy-snippet.txt ou traefik-snippet.yml.
6. Copier le site : `sudo mkdir -p /var/www/simulation && sudo cp -r site/. /var/www/simulation/`
7. Vérifier https://simulation.guedou.ch/light/ puis votre URL n8n.
8. Retour arrière : `sudo ./rollback.sh` (+ restauration de la sauvegarde si nécessaire).
9. Mises à jour : `./update.sh utilisateur@IP nouveau/index.html`
