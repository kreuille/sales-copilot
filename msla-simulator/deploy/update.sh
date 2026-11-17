#!/usr/bin/env bash
# Mise à jour depuis VOTRE ordinateur :  ./update.sh utilisateur@IP_VPS chemin/vers/index.html
set -e
scp "$2" "$1":/tmp/index.html
ssh "$1" 'sudo install -o root -g root -m 644 /tmp/index.html /var/www/simulation/light/index.html && rm /tmp/index.html'
echo "OK : https://simulation.guedou.ch/light/ (aucun rechargement de serveur nécessaire)"
