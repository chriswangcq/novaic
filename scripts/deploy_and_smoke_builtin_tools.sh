#!/usr/bin/env bash
# Deploy Gateway + Tools Server (builtin-tools / tools-config changes) and run smoke tests.
# Usage:
#   ./scripts/deploy_and_smoke_builtin_tools.sh deploy   # Deploy to api.gradievo.com
#   ./scripts/deploy_and_smoke_builtin_tools.sh smoke     # Run smoke tests (local or remote)
#   ./scripts/deploy_and_smoke_builtin_tools.sh          # Deploy + smoke

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GATEWAY_DIR="${ROOT}/novaic-gateway"
TOOLS_DIR="${ROOT}/novaic-tools-server"
SSH_HOST="${SSH_HOST:-root@api.gradievo.com}"
GATEWAY_URL="${GATEWAY_URL:-https://api.gradievo.com}"
# For local smoke, use http://127.0.0.1:19999
LOCAL_GATEWAY="${LOCAL_GATEWAY:-http://127.0.0.1:19999}"
LOCAL_TOOLS="${LOCAL_TOOLS:-http://127.0.0.1:19998}"

# Test agent_id (any non-empty string; no binding = filtered tools)
TEST_AGENT_ID="${TEST_AGENT_ID:-smoke-test-agent}"

deploy() {
  echo "=== Deploying to ${SSH_HOST} ==="
  # 1. Push from local (user must have committed)
  echo "Ensure you have committed and pushed novaic-gateway and novaic-tools-server."
  read -r -p "Press Enter to continue with SSH pull and restart..."
  
  # 2. Pull and restart on server
  ssh "$SSH_HOST" 'bash -s' << 'REMOTE'
    set -e
    echo "Pulling novaic-gateway..."
    cd /opt/novaic/services/novaic-gateway && git pull
    echo "Pulling novaic-tools-server..."
    cd /opt/novaic/services/novaic-tools-server && git pull 2>/dev/null || echo "Tools server path may differ, check manually"
    echo "Restarting Gateway..."
    bash /opt/novaic/restart_gw.sh 2>/dev/null || bash /tmp/restart_gw.sh 2>/dev/null || { pkill -f main_gateway.py 2>/dev/null; sleep 1; cd /opt/novaic/services/novaic-gateway && nohup .venv/bin/python main_gateway.py --host 127.0.0.1 --port 19999 --data-dir /opt/novaic/data --runtime-orchestrator-url http://127.0.0.1:19993 --queue-service-url http://127.0.0.1:19997 --tools-server-url http://127.0.0.1:19998 --file-service-url http://127.0.0.1:19995 --tool-result-service-url http://127.0.0.1:19994 >> /opt/novaic/data/logs/gateway-$(date +%Y%m%d).log 2>&1 & }
    echo "Restarting Tools Server (if separate process)..."
    pkill -f main_tools.py 2>/dev/null || true
    sleep 2
    # Tools server may be started by another process; if standalone:
    if [ -d /opt/novaic/services/novaic-tools-server ]; then
      cd /opt/novaic/services/novaic-tools-server
      nohup .venv/bin/python main_tools.py --port 19998 --data-dir /opt/novaic/data --gateway-url http://127.0.0.1:19999 --tool-result-service-url http://127.0.0.1:19994 >> /opt/novaic/data/logs/tools-$(date +%Y%m%d).log 2>&1 &
    fi
    sleep 2
    echo "Checking Gateway..."
    curl -sf http://127.0.0.1:19999/api/health || echo "WARN: Gateway health check failed"
    echo "Checking Tools Server..."
    curl -sf http://127.0.0.1:19998/api/health || echo "WARN: Tools Server health check failed"
    echo "Deploy done."
REMOTE
}

smoke_local() {
  echo "=== Smoke tests (local: ${LOCAL_GATEWAY}, ${LOCAL_TOOLS}) ==="
  local gw="$1"
  local ts="$2"
  local agent_id="$3"
  
  echo "1. GET ${gw}/internal/agents/${agent_id}/builtin-tools"
  resp=$(curl -sf "${gw}/internal/agents/${agent_id}/builtin-tools" 2>/dev/null || true)
  if [ -z "$resp" ]; then
    echo "   FAIL: No response (is Gateway running?)"
    return 1
  fi
  if echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'tools' in d and isinstance(d.get('tools'), list)" 2>/dev/null; then
    echo "   PASS: tools array present, count=$(echo "$resp" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('tools',[])))")"
  else
    echo "   FAIL: Invalid response"
    echo "$resp" | head -c 200
    return 1
  fi

  echo "2. GET ${gw}/internal/agents/${agent_id}/tools-config"
  resp=$(curl -sf "${gw}/internal/agents/${agent_id}/tools-config" 2>/dev/null || true)
  if [ -z "$resp" ]; then
    echo "   FAIL: No response"
    return 1
  fi
  if echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'disabled_tools' in d" 2>/dev/null; then
    echo "   PASS: disabled_tools present"
  else
    echo "   FAIL: Invalid response"
    return 1
  fi

  echo "3. GET ${ts}/internal/subagents/${agent_id}/main-${agent_id:0:8}/tools (Tools Server -> Gateway builtin-tools)"
  resp=$(curl -sf "${ts}/internal/subagents/${agent_id}/main-${agent_id:0:8}/tools" 2>/dev/null || true)
  if [ -z "$resp" ]; then
    echo "   FAIL: No response (is Tools Server running with GATEWAY_URL?)"
    return 1
  fi
  if echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'tools' in d" 2>/dev/null; then
    echo "   PASS: tools in response"
  else
    echo "   FAIL: Invalid response"
    return 1
  fi

  echo "All smoke tests PASSED."
}

smoke_remote() {
  echo "=== Smoke tests (remote via SSH) ==="
  ssh "$SSH_HOST" "bash -s" << SMOKE
    set -e
    gw="http://127.0.0.1:19999"
    ts="http://127.0.0.1:19998"
    agent_id="${TEST_AGENT_ID}"
    echo "1. GET builtin-tools"
    curl -sf "\${gw}/internal/agents/\${agent_id}/builtin-tools" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'tools' in d; print('PASS:', len(d.get('tools',[])), 'tools')"
    echo "2. GET tools-config"
    curl -sf "\${gw}/internal/agents/\${agent_id}/tools-config" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'disabled_tools' in d; print('PASS')"
    echo "3. GET Tools Server tools"
    curl -sf "\${ts}/internal/subagents/\${agent_id}/main-\${agent_id:0:8}/tools" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'tools' in d; print('PASS')"
    echo "All smoke tests PASSED."
SMOKE
}

cmd="${1:-}"
case "$cmd" in
  deploy)
    deploy
    ;;
  smoke)
    if [ -n "${RUN_ON_SERVER:-}" ] || ssh -o ConnectTimeout=2 "$SSH_HOST" "exit 0" 2>/dev/null; then
      smoke_remote
    else
      smoke_local "$LOCAL_GATEWAY" "$LOCAL_TOOLS" "$TEST_AGENT_ID"
    fi
    ;;
  *)
    deploy
    echo ""
    echo "Waiting 5s for services to stabilize..."
    sleep 5
    if ssh -o ConnectTimeout=2 "$SSH_HOST" "exit 0" 2>/dev/null; then
      smoke_remote
    else
      echo "Cannot SSH to server. Run smoke locally with Gateway and Tools Server already running:"
      echo "  LOCAL_GATEWAY=http://127.0.0.1:19999 LOCAL_TOOLS=http://127.0.0.1:19998 ./scripts/deploy_and_smoke_builtin_tools.sh smoke"
    fi
    ;;
esac
