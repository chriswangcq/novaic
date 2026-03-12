#!/usr/bin/env bash
# Relay 迁移：8.146.233.64 → 47.243.221.45
# 用法: ./scripts/migrate-relay-to-47.sh
# 前置: ssh root@47.243.221.45 可登录

set -e
OLD_RELAY="root@8.146.233.64"
NEW_RELAY="root@47.243.221.45"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Relay 迁移：8.146.233.64 → 47.243.221.45 ==="
echo ""

echo "=== 1. 复制证书（旧 relay → 新 relay）==="
ssh -o ConnectTimeout=10 "$OLD_RELAY" "tar czf - -C /etc letsencrypt 2>/dev/null" > /tmp/letsencrypt.tar.gz
scp -o ConnectTimeout=10 -P 52222 /tmp/letsencrypt.tar.gz root@47.243.221.45:/tmp/
ssh -p 52222 root@47.243.221.45 "mkdir -p /etc && tar xzf /tmp/letsencrypt.tar.gz -C /etc && rm -f /tmp/letsencrypt.tar.gz"
rm -f /tmp/letsencrypt.tar.gz
echo "证书已复制"
echo ""

echo "=== 2. 部署 novaic-quic-service ==="
cd "$REPO_ROOT/novaic-quic-service"
DEPLOY_OVERSEAS=1 SSH_OPTS="-o Port=52222 -o StrictHostKeyChecking=accept-new" ./deploy/deploy.sh root@47.243.221.45
echo ""

echo "=== 3. 部署 nginx + relay 前端 ==="
ssh -p 52222 root@47.243.221.45 "bash -s" < deploy/setup-cnd-frontend-nginx.sh
echo "同步前端静态文件（旧 relay → 本地 → 新 relay）..."
mkdir -p /tmp/relay-static-migration
rsync -avz "$OLD_RELAY:/opt/novaic/static/" /tmp/relay-static-migration/ 2>/dev/null && \
rsync -avz -e "ssh -p 52222" /tmp/relay-static-migration/ root@47.243.221.45:/opt/novaic/static/ 2>/dev/null && \
rm -rf /tmp/relay-static-migration || {
  echo "从旧 relay 同步失败，尝试本地构建部署..."
  cd "$REPO_ROOT/novaic-app"
  VITE_BASE="/resource/frontend/v0.3.0/" npm run build 2>/dev/null
  rsync -avz -e "ssh -p 52222" dist/ root@47.243.221.45:/opt/novaic/static/v0.3.0/ 2>/dev/null || echo "需先 npm run build，再手动 rsync -avz -e 'ssh -p 52222' dist/ root@47.243.221.45:/opt/novaic/static/v0.3.0/"
}
echo ""

echo "=== 迁移完成 ==="
echo ""
echo "请更新 DNS："
echo "  relay.gradievo.com  A  47.243.221.45"
echo "  stun.gradievo.com   A  47.243.221.45"
echo ""
echo "验证："
echo "  curl -sk https://relay.gradievo.com/resource/frontend/v0.3.0/ -o /dev/null -w '%{http_code}'"
echo "  curl -s https://api.gradievo.com/api/config/frontend"
