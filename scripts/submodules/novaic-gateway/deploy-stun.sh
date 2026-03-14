#!/usr/bin/env bash
# 部署 STUN 服务器 + nginx UDP 代理到 api.gradievo.com
# 用法: bash scripts/deploy-stun.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATEWAY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$GATEWAY_DIR"

SERVER="root@api.gradievo.com"

echo "=== 1. 推送代码到服务器 ==="
git add scripts/stun_server.py nginx/novaic-stun-stream.conf 2>/dev/null || true
git status --short

echo ""
echo "=== 2. 部署 STUN 服务 ==="
ssh "$SERVER" 'bash -s' << 'REMOTE'
set -e
cd /opt/novaic/services/novaic-gateway
git pull

# 创建 systemd 服务（STUN 直接绑定 0.0.0.0:3478，不经过 nginx）
# 注：部分 nginx 版本无 stream 模块，UDP 直连更简单
mkdir -p /etc/systemd/system
cat > /etc/systemd/system/novaic-stun.service << 'SVC'
[Unit]
Description=NovAIC STUN Server (RFC 5389)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/novaic/services/novaic-gateway
ExecStart=/usr/bin/python3 scripts/stun_server.py --host 0.0.0.0 --port 443
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVC

systemctl daemon-reload
systemctl enable novaic-stun
systemctl restart novaic-stun
systemctl status novaic-stun --no-pager
REMOTE

echo ""
echo "=== 3. 放行防火墙 UDP 443（与 HTTPS TCP 443 共存）==="
ssh "$SERVER" 'bash -s' << 'REMOTE'
if command -v ufw >/dev/null 2>&1; then
  ufw allow 443/udp 2>/dev/null || true
  ufw status | grep "443" || echo "ufw: check manually"
elif command -v firewall-cmd >/dev/null 2>&1; then
  firewall-cmd --add-port=443/udp --permanent 2>/dev/null || true
  firewall-cmd --reload 2>/dev/null || true
else
  echo "No ufw/firewalld, ensure UDP 443 is open (cloud security group)"
fi
REMOTE

echo ""
echo "=== 4. 完成 ==="
echo "STUN 服务器: api.gradievo.com:443 (UDP，与 HTTPS 共存)"
echo "客户端配置: export NOVAIC_STUN_SERVER=api.gradievo.com:443"
echo "验证: NOVAIC_STUN_SERVER=api.gradievo.com:443 python3 novaic-app/scripts/test-stun.py 45678"
