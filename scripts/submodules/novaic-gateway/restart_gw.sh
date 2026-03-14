#!/bin/bash
# Gateway 重启脚本（由 deploy-gateway.sh 部署到 /opt/novaic/restart_gw.sh）
# 依赖：/opt/novaic/jwt_secret.env 含 JWT_SECRET、RELAY_URL

set -e
source /opt/novaic/jwt_secret.env
export JWT_SECRET
export RELAY_URL="${RELAY_URL:-https://relay.gradievo.com/p2p/relay}"

pkill -f main_gateway.py 2>/dev/null || true
sleep 1
cd /opt/novaic/services/novaic-gateway
nohup .venv/bin/python main_gateway.py \
  --host 127.0.0.1 --port 19999 \
  --data-dir /opt/novaic/data \
  --runtime-orchestrator-url http://127.0.0.1:19993 \
  --queue-service-url http://127.0.0.1:19997 \
  --tools-server-url http://127.0.0.1:19998 \
  --file-service-url http://127.0.0.1:19995 \
  --tool-result-service-url http://127.0.0.1:19994 \
  >> /opt/novaic/data/logs/gateway-$(date +%Y%m%d).log 2>&1 &
echo $! > /tmp/gw.pid
echo "Started PID $!"
