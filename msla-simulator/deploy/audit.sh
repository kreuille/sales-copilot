#!/usr/bin/env bash
# AUDIT EN LECTURE SEULE : ne modifie rien. Ne collecte aucun mot de passe ni variable d'environnement.
# Usage : sudo ./audit.sh | tee audit.txt   puis collez audit.txt dans la conversation.
echo "== OS =="; . /etc/os-release; echo "$PRETTY_NAME"; uname -r
echo "== IPv4 publique =="; curl -4 -s --max-time 5 https://api.ipify.org; echo
echo "== DNS simulation.guedou.ch =="; getent hosts simulation.guedou.ch || echo "(pas encore résolu)"
echo "== Ports en écoute =="; ss -tlnp 2>/dev/null | awk 'NR==1||/:(80|443|5678|8080|8443)\s/'
echo "== Serveurs web / proxys (systemd) =="; systemctl list-units --type=service --state=running 2>/dev/null | grep -Ei 'nginx|apache|caddy|traefik|haproxy|docker' || echo none
echo "== Docker conteneurs (noms, images, ports) =="; docker ps --format '{{.Names}} | {{.Image}} | {{.Ports}}' 2>/dev/null || echo "docker absent"
echo "== Fichiers Nginx =="; ls /etc/nginx/sites-enabled /etc/nginx/conf.d 2>/dev/null
echo "== Caddyfile / Traefik / compose =="; ls /etc/caddy 2>/dev/null; find / -maxdepth 4 \( -name Caddyfile -o -name 'traefik*.y*ml' -o -name 'docker-compose*.y*ml' -o -name 'compose*.y*ml' \) 2>/dev/null | head -20
echo "== Certificats Let's Encrypt =="; ls /etc/letsencrypt/live 2>/dev/null || echo "aucun (ou géré par Caddy/Traefik)"
echo "== Pare-feu =="; (ufw status 2>/dev/null || iptables -S 2>/dev/null | head -20)
echo "== Espace disque =="; df -h / | tail -1
