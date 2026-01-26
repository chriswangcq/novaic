#!/bin/bash

# NovAIC VM - 停止虚拟机

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$VM_DIR/.vm.pid"

echo ""
echo "════════════════════════════════════════════"
echo "  NovAIC VM - 停止虚拟机"
echo "════════════════════════════════════════════"
echo ""

if [ ! -f "$PID_FILE" ]; then
    echo "VM 未在运行 (PID 文件不存在)"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ps -p "$PID" > /dev/null 2>&1; then
    echo "正在停止 VM (PID: $PID)..."
    
    # 优雅关闭
    kill -TERM "$PID" 2>/dev/null || true
    
    # 等待进程结束
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            break
        fi
        echo "  等待关闭... ($i/10)"
        sleep 1
    done
    
    # 如果还在运行，强制终止
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "  强制终止..."
        kill -9 "$PID" 2>/dev/null || true
    fi
    
    rm -f "$PID_FILE"
    echo ""
    echo "✅ VM 已停止"
else
    echo "VM 进程不存在 (PID: $PID)"
    rm -f "$PID_FILE"
fi

echo ""
