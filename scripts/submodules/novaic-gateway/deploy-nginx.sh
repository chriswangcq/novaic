#!/bin/bash
# 部署 nginx 配置到 api.gradievo.com
# 用法: ./deploy-nginx.sh  或  bash deploy-nginx.sh
# 需在 novaic-gateway/nginx 目录下执行，或指定路径

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DOMAIN="api.gradievo.com"
CERT_PATH="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
KEY_PATH="/etc/letsencrypt/live/${DOMAIN}/privkey.pem"

sed -e "s/YOUR_DOMAIN/${DOMAIN}/g" \
    -e "s|/path/to/cert.pem|${CERT_PATH}|g" \
    -e "s|/path/to/key.pem|${KEY_PATH}|g" \
    novaic-cloud.conf > /tmp/novaic-production.conf

echo "Generated config. Deploy to server:"
echo "  scp /tmp/novaic-production.conf root@${DOMAIN}:/tmp/"
echo "  scp novaic-stun-stream.conf root@${DOMAIN}:/tmp/"
echo "  ssh root@${DOMAIN} 'cp /tmp/novaic-production.conf /etc/nginx/sites-enabled/novaic && cp /tmp/novaic-stun-stream.conf /etc/nginx/conf.d/ && nginx -t && systemctl reload nginx'"
