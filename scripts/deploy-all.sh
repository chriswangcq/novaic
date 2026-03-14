#!/usr/bin/env bash
# 一键部署：前端 → Relay → 手机 App → 桌面 App
#
# 用法: ./scripts/deploy-all.sh [version]
#   version 默认 0.3.0，用于前端 CDN 路径
#
# 前置: relay SSH 端口 52222，relay 服务器 47.243.221.45

set -e
VERSION="${1:-0.3.0}"
RELAY_HOST="root@47.243.221.45"
RELAY_SSH="ssh -p 52222"
RELAY_RSYNC="rsync -avz --delete -e \"ssh -p 52222\""
STATIC_DIR="/opt/novaic/static"
TARGET_DIR="${STATIC_DIR}/v${VERSION}"
VITE_BASE_PATH="/resource/frontend/v${VERSION}/"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "1. 部署前端到 Relay"
echo "=========================================="
cd "$REPO_ROOT/novaic-app"
echo "构建前端 (base=${VITE_BASE_PATH})..."
VITE_BASE="${VITE_BASE_PATH}" npm run build
if [ ! -f dist/index.html ]; then
  echo "错误: dist/index.html 不存在"
  exit 1
fi
echo "部署到 relay..."
$RELAY_SSH "$RELAY_HOST" "mkdir -p $TARGET_DIR"
rsync -avz --delete -e "ssh -p 52222" dist/ "$RELAY_HOST:$TARGET_DIR/"
echo "前端已部署: https://relay.gradievo.com${VITE_BASE_PATH}"
echo ""

echo "=========================================="
echo "2. 部署 Relay (novaic-quic-service)"
echo "=========================================="
cd "$REPO_ROOT/novaic-quic-service"
echo "推送源码到 relay..."
$RELAY_SSH "$RELAY_HOST" 'mkdir -p /opt/novaic/novaic-quic-service'
rsync -avz -e "ssh -p 52222" --exclude target --exclude .git \
  "$REPO_ROOT/novaic-quic-service/" "$RELAY_HOST:/opt/novaic/novaic-quic-service/"
echo "Relay 服务器编译、重启..."
$RELAY_SSH "$RELAY_HOST" 'export PATH="$HOME/.cargo/bin:$PATH" && cd /opt/novaic/novaic-quic-service && cargo build --release && systemctl stop novaic-quic-service && cp target/release/novaic-quic-service ./ && systemctl start novaic-quic-service'
echo "验证 relay 状态..."
$RELAY_SSH "$RELAY_HOST" 'systemctl status novaic-quic-service --no-pager' || true
echo ""

echo "=========================================="
echo "3. 构建并安装手机 App (iOS)"
echo "=========================================="
cd "$REPO_ROOT/novaic-app"
./scripts/build-and-install-ios.sh
echo ""

echo "=========================================="
echo "4. 构建桌面 App (macOS)"
echo "=========================================="
cd "$REPO_ROOT/novaic-app"
npm run tauri:build -- --bundles app
APP_PATH="src-tauri/target/release/bundle/macos/NovAIC.app"
echo "桌面 App 已构建: $APP_PATH"
echo "安装到 /Applications: cp -r $APP_PATH /Applications/NovAIC.app"
echo ""

echo "=========================================="
echo "部署完成"
echo "=========================================="
echo "请手动执行:"
echo "  - 更新 Gateway: export FRONTEND_CDN_URL=https://relay.gradievo.com${VITE_BASE_PATH}"
echo "    export FRONTEND_VERSION=${VERSION}"
echo "    然后重启: ssh root@api.gradievo.com 'bash /opt/novaic/restart_gw.sh'"
echo ""
