#!/usr/bin/env bash
# Retire UNIQUEMENT le simulateur. Ne touche ni n8n ni les certificats des autres domaines.
set -e
rm -f /etc/nginx/conf.d/simulation.guedou.ch.conf /etc/nginx/sites-enabled/simulation
rm -rf /var/www/simulation
if command -v nginx >/dev/null; then nginx -t && systemctl reload nginx; fi
echo "Simulateur retiré. Caddy/Traefik : retirer le bloc ajouté puis recharger (sauvegarde dans ~/backup-avant-simulation-*)."
