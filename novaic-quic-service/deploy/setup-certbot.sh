#!/usr/bin/env bash
# 在 ECS 上为 relay.gradievo.com 申请 Let's Encrypt 证书，并配置自动续期
# 用法: ssh SERVER "bash -s" < deploy/setup-certbot.sh
# 或: ./deploy/setup-certbot.sh
# 或: ./deploy/setup-certbot.sh relay.gradievo.com stun.gradievo.com frontend.gradievo.com
#
# 若已有 relay+stun 证书，需扩展现有证书添加 frontend 时：
#   1. 先配置 nginx（setup-frontend-nginx.sh 已含 /.well-known/acme-challenge/）
#   2. 执行：certbot certonly --webroot -w /var/www/certbot --expand -d relay.gradievo.com -d stun.gradievo.com -m admin@gradievo.com
#   3. 若 HTTP-01 失败，可改用 DNS-01：certbot certonly --manual --preferred-challenges dns --expand ...

set -e
if [ $# -eq 0 ]; then
  DOMAINS=(relay.gradievo.com stun.gradievo.com)
else
  DOMAINS=("$@")
fi
DOMAIN_ARGS=""
for d in "${DOMAINS[@]}"; do
  DOMAIN_ARGS="$DOMAIN_ARGS -d $d"
done
PRIMARY_DOMAIN="${DOMAINS[0]}"

echo "=== 安装 certbot（若未安装）==="
if ! command -v certbot >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update && apt-get install -y certbot
  elif command -v yum >/dev/null 2>&1; then
    yum install -y certbot
  else
    echo "请手动安装 certbot"
    exit 1
  fi
fi

echo ""
echo "=== 申请证书（standalone 模式，会临时占用 80 端口）==="
echo "确保域名已解析到本机，且 80 端口已放行"
echo "若已有 relay+stun 证书需添加 frontend，请手动执行: certbot certonly --standalone --expand $DOMAIN_ARGS -m admin@gradievo.com"
certbot certonly --standalone $DOMAIN_ARGS --non-interactive --agree-tos --email admin@gradievo.com

echo ""
echo "=== 配置自动续期 + 续期后重启服务 ==="
mkdir -p /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/restart-novaic-quic.sh << 'HOOK'
#!/bin/sh
# Certbot 续期成功后重启 novaic-quic-service 和 nginx（frontend 同用此证书）
systemctl restart novaic-quic-service 2>/dev/null || true
systemctl reload nginx 2>/dev/null || true
HOOK
chmod +x /etc/letsencrypt/renewal-hooks/deploy/restart-novaic-quic.sh

if systemctl list-timers certbot.timer &>/dev/null; then
  systemctl enable certbot.timer
  systemctl start certbot.timer 2>/dev/null || true
  echo "certbot.timer 已启用（每日检查续期）"
else
  (crontab -l 2>/dev/null | grep -v certbot; echo "0 3 * * * certbot renew --quiet") | crontab -
  echo "已加入 crontab：每日 3:00 检查续期"
fi

echo ""
echo "证书路径："
echo "  /etc/letsencrypt/live/$PRIMARY_DOMAIN/fullchain.pem"
echo "  /etc/letsencrypt/live/$PRIMARY_DOMAIN/privkey.pem"
echo ""
echo "自动续期已配置，续期成功后会自动重启 novaic-quic-service"
