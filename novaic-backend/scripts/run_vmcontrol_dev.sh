#!/bin/bash
# 开发模式启动 vmcontrol

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VMCONTROL_DIR="$PROJECT_ROOT/../novaic-app/src-tauri/vmcontrol"

echo "=== Starting vmcontrol in development mode ==="
echo "Project root: $PROJECT_ROOT"
echo "vmcontrol dir: $VMCONTROL_DIR"
echo ""

# 检查目录是否存在
if [ ! -d "$VMCONTROL_DIR" ]; then
    echo "ERROR: vmcontrol directory not found at $VMCONTROL_DIR"
    exit 1
fi

cd "$VMCONTROL_DIR"

# 设置日志级别
export RUST_LOG=debug

# 启动服务
echo "Starting vmcontrol with:"
echo "  Port: 8080"
echo "  Host: 127.0.0.1"
echo "  Log level: $RUST_LOG"
echo ""

cargo run -- --port 8080 --host 127.0.0.1
