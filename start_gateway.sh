#!/bin/bash
# 启动 Gateway 并实时输出日志

# 使用相对路径，从脚本所在目录导航
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/novaic-backend" || cd "$SCRIPT_DIR" || exit 1

# 激活虚拟环境（如果存在）
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
fi

export NOVAIC_DATA_DIR=~/.novaic
export NOVAIC_GATEWAY_URL=http://127.0.0.1:19999
export NOVAIC_MCP_GATEWAY_URL=http://127.0.0.1:19998
export PYTHONUNBUFFERED=1

echo "Starting Gateway..."
timeout 30 python main_gateway.py --port 19999 --data-dir ~/.novaic 2>&1 | tee /tmp/gateway_startup.log
