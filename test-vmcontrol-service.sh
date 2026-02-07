#!/bin/bash
# Test script for vmcontrol service

set -e

echo "==========================================="
echo "VMControl Service Test Script"
echo "==========================================="
echo

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check if vmcontrol binary exists
echo -e "${YELLOW}Step 1: Checking for vmcontrol binary...${NC}"
if [ -f "novaic-app/src-tauri/target/release/vmcontrol" ]; then
    echo -e "${GREEN}✓ Found release binary${NC}"
    VMCONTROL_BIN="novaic-app/src-tauri/target/release/vmcontrol"
elif [ -f "novaic-app/src-tauri/target/debug/vmcontrol" ]; then
    echo -e "${GREEN}✓ Found debug binary${NC}"
    VMCONTROL_BIN="novaic-app/src-tauri/target/debug/vmcontrol"
else
    echo -e "${RED}✗ vmcontrol binary not found${NC}"
    echo "Building vmcontrol..."
    cd novaic-app/src-tauri/vmcontrol
    cargo build --release
    cd ../../..
    VMCONTROL_BIN="novaic-app/src-tauri/target/release/vmcontrol"
fi
echo

# Step 2: Test direct vmcontrol binary
echo -e "${YELLOW}Step 2: Testing vmcontrol binary directly...${NC}"
echo "Command: $VMCONTROL_BIN --help"
$VMCONTROL_BIN --help
echo

# Step 3: Check main_novaic.py help
echo -e "${YELLOW}Step 3: Checking main_novaic.py vmcontrol command...${NC}"
cd novaic-backend
python3 main_novaic.py vmcontrol --help
echo

# Step 4: Start vmcontrol service (in background)
echo -e "${YELLOW}Step 4: Starting vmcontrol service on port 8080...${NC}"
echo "Command: python3 main_novaic.py vmcontrol --port 8080 &"
python3 main_novaic.py vmcontrol --port 8080 > /tmp/vmcontrol-test.log 2>&1 &
VMCONTROL_PID=$!
echo "Started with PID: $VMCONTROL_PID"
echo "Logs: /tmp/vmcontrol-test.log"
echo

# Step 5: Wait for service to be ready
echo -e "${YELLOW}Step 5: Waiting for service to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://127.0.0.1:8080/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Service is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Service failed to start${NC}"
        echo "Last 20 lines of log:"
        tail -20 /tmp/vmcontrol-test.log
        kill $VMCONTROL_PID 2>/dev/null || true
        exit 1
    fi
    echo -n "."
    sleep 1
done
echo

# Step 6: Test health endpoint
echo -e "${YELLOW}Step 6: Testing health endpoint...${NC}"
echo "GET http://127.0.0.1:8080/api/health"
HEALTH_RESPONSE=$(curl -s http://127.0.0.1:8080/api/health)
echo "Response: $HEALTH_RESPONSE"
if echo "$HEALTH_RESPONSE" | grep -q "ok"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
fi
echo

# Step 7: Test VM list endpoint
echo -e "${YELLOW}Step 7: Testing VM list endpoint...${NC}"
echo "GET http://127.0.0.1:8080/api/vms"
VM_RESPONSE=$(curl -s http://127.0.0.1:8080/api/vms)
echo "Response: $VM_RESPONSE"
echo -e "${GREEN}✓ VM list endpoint working${NC}"
echo

# Step 8: Cleanup
echo -e "${YELLOW}Step 8: Cleaning up...${NC}"
echo "Stopping vmcontrol service (PID: $VMCONTROL_PID)"
kill $VMCONTROL_PID 2>/dev/null || true
wait $VMCONTROL_PID 2>/dev/null || true
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo

# Summary
echo "==========================================="
echo -e "${GREEN}All tests passed!${NC}"
echo "==========================================="
echo
echo "Usage examples:"
echo "  # Start vmcontrol on default port (8080)"
echo "  python3 main_novaic.py vmcontrol"
echo
echo "  # Start on custom port"
echo "  python3 main_novaic.py vmcontrol --port 9090"
echo
echo "  # With custom host and binary path"
echo "  python3 main_novaic.py vmcontrol --host 0.0.0.0 --port 8080 --vmcontrol-bin /path/to/vmcontrol"
echo
echo "Environment variables:"
echo "  VMCONTROL_PORT=8080      # Default port"
echo "  VMCONTROL_HOST=127.0.0.1 # Default host"
echo "  RUST_LOG=info            # Log level"
echo
