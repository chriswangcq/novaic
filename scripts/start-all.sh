#!/bin/bash
# start-all.sh - Start all split services
# Usage: ./start-all.sh [--dev] [--binary]
#   --dev    : Run from source (python -m)
#   --binary : Run from built binaries (default if dist/ exists)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/dist"
DATA_DIR="${NOVAIC_DATA_DIR:-$HOME/.novaic}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Ensure data dir exists
mkdir -p "$DATA_DIR/logs"

# Export for child processes
export NOVAIC_DATA_DIR="$DATA_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  NovAIC Split Services Startup        ${NC}"
echo -e "${GREEN}========================================${NC}"
echo "DATA_DIR: $DATA_DIR"

# Detect mode
MODE="dev"
if [ "$1" = "--binary" ] || ([ -d "$BUILD_DIR" ] && [ "$1" != "--dev" ]); then
    MODE="binary"
fi

echo "MODE: $MODE"
echo ""

# Kill existing processes
echo -e "${YELLOW}Stopping existing services...${NC}"
pkill -f "novaic-gateway" 2>/dev/null || true
pkill -f "novaic-runtime-orchestrator" 2>/dev/null || true
pkill -f "novaic-storage-a" 2>/dev/null || true
pkill -f "main_cortex" 2>/dev/null || true
pkill -f "novaic-agent-runtime" 2>/dev/null || true
pkill -f "file_service.main" 2>/dev/null || true
pkill -f "main_gateway" 2>/dev/null || true
pkill -f "main_runtime_orchestrator" 2>/dev/null || true
sleep 2

start_service() {
    local name=$1
    local port=$2
    local cmd=$3
    
    echo -e "${GREEN}[Starting] $name (port $port)${NC}"
    nohup $cmd > "$DATA_DIR/logs/$name.log" 2>&1 &
    sleep 2
    
    # Health check
    if curl -s "http://127.0.0.1:$port/api/health" > /dev/null 2>&1 || \
       curl -s "http://127.0.0.1:$port/health" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ $name started${NC}"
    else
        echo -e "  ${YELLOW}⚠ $name may not be ready yet${NC}"
    fi
}

if [ "$MODE" = "binary" ]; then
    # Binary mode
    echo -e "${GREEN}Running from binaries...${NC}"
    
    start_service "runtime-orchestrator" 19993 "$BUILD_DIR/novaic-runtime-orchestrator --port 19993"
    start_service "gateway" 19999 "$BUILD_DIR/novaic-gateway --port 19999"
    start_service "storage-a" 19995 "$BUILD_DIR/novaic-storage-a --port 19995"
    start_service "tools-server" 19998 "$BUILD_DIR/novaic-tools-server --port 19998 --gateway-url http://127.0.0.1:19999"
    
    # Workers
    echo -e "${GREEN}[Starting] Workers${NC}"
    nohup $BUILD_DIR/novaic-agent-runtime watchdog \
        --gateway-url http://127.0.0.1:19999 \
        --queue-service-url http://127.0.0.1:19997 \
        > "$DATA_DIR/logs/watchdog.log" 2>&1 &
    
    nohup $BUILD_DIR/novaic-agent-runtime task-worker \
        --gateway-url http://127.0.0.1:19999 \
        --queue-service-url http://127.0.0.1:19997 \
        --tools-server-url http://127.0.0.1:19998 \
        --runtime-orchestrator-url http://127.0.0.1:19993 \
        > "$DATA_DIR/logs/task-worker.log" 2>&1 &
    
    echo -e "  ${GREEN}✓ Workers started${NC}"
    
else
    # Dev mode (python -m)
    echo -e "${GREEN}Running from source (dev mode)...${NC}"
    
    # Runtime Orchestrator
    cd "$SCRIPT_DIR/novaic-runtime-orchestrator"
    source .venv/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null || true
    start_service "runtime-orchestrator" 19993 "python main_runtime_orchestrator.py"
    
    # Gateway
    cd "$SCRIPT_DIR/novaic-gateway"
    source .venv/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null || true
    start_service "gateway" 19999 "python main_gateway.py"
    
    # Storage A (File Service)
    cd "$SCRIPT_DIR/novaic-storage-a"
    source .venv/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null || true
    start_service "storage-a" 19995 "python -m file_service.main --port 19995"
    
    # Cortex
    cd "$SCRIPT_DIR/novaic-cortex"
    source .venv/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null || true
    start_service "cortex" 19996 "python -m novaic_cortex.main_cortex"
    
    # Workers
    cd "$SCRIPT_DIR/novaic-agent-runtime"
    source .venv/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null || true
    
    echo -e "${GREEN}[Starting] Workers${NC}"
    nohup python main_novaic.py watchdog \
        --gateway-url http://127.0.0.1:19999 \
        --queue-service-url http://127.0.0.1:19997 \
        > "$DATA_DIR/logs/watchdog.log" 2>&1 &
    
    nohup python main_novaic.py task-worker \
        --gateway-url http://127.0.0.1:19999 \
        --queue-service-url http://127.0.0.1:19997 \
        --runtime-orchestrator-url http://127.0.0.1:19993 \
        > "$DATA_DIR/logs/task-worker.log" 2>&1 &
    
    echo -e "  ${GREEN}✓ Workers started${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All Services Started!                ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Service Status:"
echo "  Runtime Orchestrator: http://127.0.0.1:19993/api/health"
echo "  Gateway:              http://127.0.0.1:19999/health"
echo "  File Service:         http://127.0.0.1:19995/api/health"
echo "  Cortex:               http://127.0.0.1:19996/health"
echo ""
echo "Logs: $DATA_DIR/logs/"
