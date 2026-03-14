#!/usr/bin/env bash
# 在 relay 服务器上配置 frontend.gradievo.com（与 relay 同机）
#
# 用法: ssh root@relay.gradievo.com "bash -s" < deploy/setup-frontend-nginx.sh
# 或: ./deploy/setup-frontend-nginx.sh
#
# 前置:
#   1. frontend.gradievo.com DNS 已指向本机
#   2. 已申请证书（含 frontend.gradievo.com）:
#      certbot certonly --standalone -d relay.gradievo.com -d stun.gradievo.com -d frontend.gradievo.com

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
# CentOS 用 nginx，Debian 用 www-data
id nginx >/dev/null 2>&1 && chown -R nginx:nginx "$STATIC_DIR" || chown -R www-data:www-data "$STATIC_DIR" 2>/dev/null || true

echo ""
echo "=== 生成 nginx 配置 ==="
# CentOS/RHEL 使用 conf.d，Debian/Ubuntu 使用 sites-available
if [ -d /etc/nginx/conf.d ]; then
  NGINX_CONF="/etc/nginx/conf.d/frontend.conf"
else
  mkdir -p /etc/nginx/sites-available
  NGINX_CONF="/etc/nginx/sites-available/frontend"
fi

# ACME challenge 目录（certbot webroot 扩证用）
mkdir -p /var/www/certbot/.well-known/acme-challenge
id nginx >/dev/null 2>&1 && chown -R nginx:nginx /var/www/certbot || chown -R www-data:www-data /var/www/certbot 2>/dev/null || true

cat > "$NGINX_CONF" << NGINX
# frontend.gradievo.com — 前端静态资源
# 注意：80 端口需保留 /.well-known/acme-challenge/ 供 certbot 扩证
server {
    listen 80;
    server_name frontend.gradievo.com;
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
    server_name frontend.gradievo.com;

    ssl_certificate     ${CERT_DIR}/fullchain.pem;
    ssl_certificate_key ${CERT_DIR}/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    root ${STATIC_DIR};
    index index.html;
    location = / {
        return 302 /v0.3.0/;
    }
    location / {
        add_header Cache-Control "public, max-age=3600";
        try_files \$uri \$uri/ =404;
    }
}
NGINX

# Debian/Ubuntu: 启用 sites-enabled
if [ -d /etc/nginx/sites-enabled ] && [ "$NGINX_CONF" != "/etc/nginx/conf.d/frontend.conf" ]; then
  ln -sf /etc/nginx/sites-available/frontend /etc/nginx/sites-enabled/
fi

echo ""
echo "=== 检查并重载 nginx ==="
nginx -t && systemctl reload nginx

echo ""
echo "=== 完成 ==="
echo "前端目录: $STATIC_DIR"
echo "部署示例: rsync -avz dist/ root@relay.gradievo.com:${STATIC_DIR}/v0.3.0/"
echo "URL: https://frontend.gradievo.com/v0.3.0/"
