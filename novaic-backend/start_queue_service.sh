#!/bin/bash
# Queue Service 启动脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查环境变量
if [ -z "$NOVAIC_DATA_DIR" ]; then
    echo "❌ Error: NOVAIC_DATA_DIR environment variable is not set"
    echo "Please set it to your data directory, e.g.:"
    echo "  export NOVAIC_DATA_DIR=~/.novaic"
    exit 1
fi

echo "🚀 Starting Queue Service..."
echo "📁 Data directory: $NOVAIC_DATA_DIR"
echo "🗄️  Database: $NOVAIC_DATA_DIR/queue.db"
echo "🔌 Port: ${QUEUE_SERVICE_PORT:-19998}"
echo ""

# 启动 Queue Service
python3 -m queue_service.main

# 或者直接运行
# python3 queue_service/main.py
