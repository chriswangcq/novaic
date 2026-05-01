#!/usr/bin/env bash
# 部署 Gateway 到 api.gradievo.com
# 用法: ./scripts/deploy-gateway.sh root@api.gradievo.com
# 或: bash scripts/deploy-gateway.sh root@api.gradievo.com
#
# 部署内容：
#   - rsync novaic-gateway 到 /opt/novaic/services/novaic-gateway
#   - 复制 restart_gw.sh 到 /opt/novaic/restart_gw.sh
#   - 若 jwt_secret.env 不存在，从 example 复制（需手动填写 JWT_SECRET）
#   - 执行 restart_gw.sh 重启 Gateway

set -e
TARGET="${1:?Usage: $0 user@host}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATEWAY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== 部署 Gateway 到 $TARGET ==="
echo "源目录: $GATEWAY_DIR"

# 1. rsync 代码（排除 .git、__pycache__、.pytest_cache、.mypy_cache、.venv）
rsync -avz --delete \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '.mypy_cache' \
  --exclude '*.pyc' \
  --exclude '.venv' \
  --exclude '.env' \
  "$GATEWAY_DIR/" "$TARGET:/opt/novaic/services/novaic-gateway/"

# 2. 部署 restart_gw.sh
scp "$GATEWAY_DIR/scripts/restart_gw.sh" "$TARGET:/opt/novaic/restart_gw.sh"

# 3. 若 jwt_secret.env 不存在，从 example 复制（需手动填写）
ssh "$TARGET" 'bash -s' << 'REMOTE'
if [ ! -f /opt/novaic/jwt_secret.env ]; then
  echo "警告: /opt/novaic/jwt_secret.env 不存在，从 example 复制"
  cp /opt/novaic/services/novaic-gateway/scripts/jwt_secret.env.example /opt/novaic/jwt_secret.env
  echo "请编辑 /opt/novaic/jwt_secret.env 填写 JWT_SECRET 后重新执行 restart_gw.sh"
  exit 1
fi
REMOTE

# 4. 确保 jwt_secret.env 含 FRONTEND_CDN_URL（若缺失则追加）
ssh "$TARGET" 'bash -s' << 'REMOTE'
if ! grep -q 'FRONTEND_CDN_URL' /opt/novaic/jwt_secret.env 2>/dev/null; then
  echo "" >> /opt/novaic/jwt_secret.env
  echo "# 前端 OTA 热更新 CDN URL（可选）" >> /opt/novaic/jwt_secret.env
  echo "export FRONTEND_CDN_URL=https://relay.gradievo.com/resource/frontend/v0.3.0/" >> /opt/novaic/jwt_secret.env
  echo "export FRONTEND_VERSION=0.3.0" >> /opt/novaic/jwt_secret.env
  echo "已追加 FRONTEND_CDN_URL 到 jwt_secret.env"
fi
REMOTE

# 5. 重启 Gateway
echo ""
echo "=== 重启 Gateway ==="
ssh "$TARGET" 'bash /opt/novaic/restart_gw.sh'

echo ""
echo "=== 部署完成 ==="
echo "验证: ssh $TARGET 'ss -tlnp | grep 19999'"
