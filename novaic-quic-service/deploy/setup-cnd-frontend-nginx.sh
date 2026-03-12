#!/usr/bin/env bash
# 在 relay 服务器上配置 relay.gradievo.com/resource/frontend/（前端 CDN，复用 relay 证书）
#
# 用法: ssh root@relay.gradievo.com "bash -s" < deploy/setup-cnd-frontend-nginx.sh
#
# 前置: relay.gradievo.com 证书已存在（/etc/letsencrypt/live/relay.gradievo.com/），无需额外域名

set -e
CERT_DIR="${CERT_DIR:-/etc/letsencrypt/live/relay.gradievo.com}"
STATIC_DIR="/opt/novaic/static"

echo "=== 安装 nginx（若未安装）==="
if command -v nginx >/dev/null 2>&1; then
  echo "nginx 已安装"
else
  if command -v yum >/dev/null 2>&1; then
    yum install -y nginx
  else
    apt-get update && apt-get install -y nginx
  fi
fi

echo ""
echo "=== 创建静态目录 ==="
mkdir -p "$STATIC_DIR"
id nginx >/dev/null 2>&1 && chown -R nginx:nginx "$STATIC_DIR" || chown -R www-data:www-data "$STATIC_DIR" 2>/dev/null || true

echo ""
echo "=== ACME challenge 目录 ==="
mkdir -p /var/www/certbot/.well-known/acme-challenge
id nginx >/dev/null 2>&1 && chown -R nginx:nginx /var/www/certbot || chown -R www-data:www-data /var/www/certbot 2>/dev/null || true

echo ""
echo "=== 生成 nginx 配置 ==="
if [ -d /etc/nginx/conf.d ]; then
  NGINX_CONF="/etc/nginx/conf.d/relay-frontend.conf"
else
  mkdir -p /etc/nginx/sites-available
  NGINX_CONF="/etc/nginx/sites-available/relay-frontend"
fi

cat > "$NGINX_CONF" << NGINX
# relay.gradievo.com — 前端 CDN（路径 /resource/frontend/v{version}/，复用 relay 证书）
server {
    listen 80;
    server_name relay.gradievo.com;
    location ^~ /.well-known/acme-challenge/ {
        root /var/www/certbot;
        allow all;
    }
    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name relay.gradievo.com;

    ssl_certificate     ${CERT_DIR}/fullchain.pem;
    ssl_certificate_key ${CERT_DIR}/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    location /resource/frontend/ {
        alias ${STATIC_DIR}/;
        index index.html;
        add_header Cache-Control "public, max-age=3600";
    }
    location = /resource/frontend {
        return 302 /resource/frontend/;
    }
    location = /resource/frontend/ {
        return 302 /resource/frontend/v0.3.0/;
    }
}
NGINX

if [ -d /etc/nginx/sites-enabled ] && [ "$NGINX_CONF" != "/etc/nginx/conf.d/relay-frontend.conf" ]; then
  ln -sf /etc/nginx/sites-available/relay-frontend /etc/nginx/sites-enabled/
fi

# 移除旧的 cnd-frontend 配置（若存在）
rm -f /etc/nginx/conf.d/cnd-frontend.conf /etc/nginx/sites-available/cnd-frontend 2>/dev/null || true

echo ""
echo "=== 检查并重载 nginx ==="
nginx -t && systemctl reload nginx

echo ""
echo "=== 完成 ==="
echo "前端目录: $STATIC_DIR/v{version}/"
echo "URL: https://relay.gradievo.com/resource/frontend/v0.3.0/"