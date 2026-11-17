#!/usr/bin/env bash
# Sauvegarde les configurations avant toute modification (copie uniquement, aucune suppression).
set -e
B="$HOME/backup-avant-simulation-$(date +%Y%m%d-%H%M)"
mkdir -p "$B"
cp -a /etc/nginx "$B/" 2>/dev/null || true
cp -a /etc/caddy "$B/" 2>/dev/null || true
cp -a /etc/letsencrypt "$B/" 2>/dev/null || true
find / -maxdepth 4 \( -name Caddyfile -o -name 'traefik*.y*ml' -o -name 'docker-compose*.y*ml' -o -name 'compose*.y*ml' \) 2>/dev/null | while read -r f; do
  mkdir -p "$B$(dirname "$f")"; cp -a "$f" "$B$f"
done
echo "Sauvegarde : $B"
