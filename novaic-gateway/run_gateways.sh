#!/usr/bin/env bash
# 本地手动启动 Gateway + MCP Gateway（与 Tauri 分开跑时用）
# Usage: ./run_gateways.sh  或  bash run_gateways.sh

set -e
GATEWAY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${NOVAIC_DATA_DIR:-$HOME/Library/Application Support/com.novaic.app}"

# 停掉旧进程
pkill -f "python main.py" 2>/dev/null || true
pkill -f "python mcp_main.py" 2>/dev/null || true
sleep 2

cd "$GATEWAY_DIR"
export NOVAIC_DATA_DIR="$DATA_DIR"

# 先起 Gateway (19999)
nohup python main.py > /tmp/gateway.log 2>&1 &
echo "[run_gateways] Gateway started (PID $!)"
sleep 3

# 再起 MCP Gateway (19998)，需指向 Gateway
export NOVAIC_GATEWAY_URL="${NOVAIC_GATEWAY_URL:-http://127.0.0.1:19999}"
nohup python mcp_main.py > /tmp/mcp_gateway.log 2>&1 &
echo "[run_gateways] MCP Gateway started (PID $!)"
sleep 6

# 检查 Gateway 状态
echo ""
echo "=== Gateway (19999) ==="
curl -s "http://127.0.0.1:19999/api/system/status" | python -m json.tool | head -25
echo ""
echo "=== MCP Gateway (19998) /internal/mcp/stats ==="
curl -s "http://127.0.0.1:19998/internal/mcp/stats" | python -m json.tool 2>/dev/null | head -15 || echo "(no stats yet)"
