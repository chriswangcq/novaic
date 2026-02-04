#!/bin/bash
# 启动 Gateway 并实时输出日志

cd /Users/wangchaoqun/novaic/novaic-backend
source venv/bin/activate

export NOVAIC_DATA_DIR=~/.novaic
export NOVAIC_GATEWAY_URL=http://127.0.0.1:19999
export NOVAIC_MCP_GATEWAY_URL=http://127.0.0.1:19998
export PYTHONUNBUFFERED=1

echo "Starting Gateway..."
timeout 30 python main_gateway.py --port 19999 --data-dir ~/.novaic 2>&1 | tee /tmp/gateway_startup.log
