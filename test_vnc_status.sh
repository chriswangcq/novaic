#!/bin/bash

# Test VNC Status API
# Tests the VNC connection status detection endpoint

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Testing VNC Status API ===${NC}\n"

# Configuration
GATEWAY_URL="http://localhost:8000"
AGENT_ID="${1:-test-agent-001}"

echo -e "${YELLOW}Using Agent ID: ${AGENT_ID}${NC}\n"

# Function to test VNC status
test_vnc_status() {
    local agent_id=$1
    
    echo -e "${YELLOW}Testing VNC status for agent: ${agent_id}${NC}"
    
    # Call the API
    response=$(curl -s "${GATEWAY_URL}/api/vm/vnc/status/${agent_id}")
    
    # Parse response
    available=$(echo "$response" | jq -r '.available')
    vm_running=$(echo "$response" | jq -r '.vm_running')
    vnc_socket_exists=$(echo "$response" | jq -r '.vnc_socket_exists')
    vnc_socket_path=$(echo "$response" | jq -r '.vnc_socket_path')
    vmcontrol_healthy=$(echo "$response" | jq -r '.vmcontrol_healthy')
    vm_registered=$(echo "$response" | jq -r '.vm_registered')
    vnc_url=$(echo "$response" | jq -r '.vnc_url')
    reason=$(echo "$response" | jq -r '.reason')
    
    # Display results
    echo ""
    echo "Response:"
    echo "$response" | jq '.'
    echo ""
    
    # Summary
    echo -e "${YELLOW}Status Summary:${NC}"
    
    if [ "$available" = "true" ]; then
        echo -e "  ${GREEN}✓ VNC Available${NC}"
    else
        echo -e "  ${RED}✗ VNC Not Available${NC}"
    fi
    
    if [ "$vm_running" = "true" ]; then
        echo -e "  ${GREEN}✓ VM Running${NC}"
    else
        echo -e "  ${RED}✗ VM Not Running${NC}"
    fi
    
    if [ "$vnc_socket_exists" = "true" ]; then
        echo -e "  ${GREEN}✓ VNC Socket Exists${NC} (${vnc_socket_path})"
    else
        echo -e "  ${RED}✗ VNC Socket Not Found${NC} (${vnc_socket_path})"
    fi
    
    if [ "$vmcontrol_healthy" = "true" ]; then
        echo -e "  ${GREEN}✓ VmControl Healthy${NC}"
    else
        echo -e "  ${RED}✗ VmControl Not Healthy${NC}"
    fi
    
    if [ "$vm_registered" = "true" ]; then
        echo -e "  ${GREEN}✓ VM Registered in VmControl${NC}"
    else
        echo -e "  ${RED}✗ VM Not Registered in VmControl${NC}"
    fi
    
    echo ""
    echo -e "  VNC URL: ${vnc_url}"
    echo -e "  Reason: ${reason}"
    echo ""
}

# Test 1: Check VNC status for the specified agent
echo -e "${YELLOW}Test 1: Check VNC Status${NC}"
test_vnc_status "$AGENT_ID"

# Test 2: Check VNC status for a non-existent agent
echo -e "${YELLOW}Test 2: Check VNC Status for Non-Existent Agent${NC}"
test_vnc_status "non-existent-agent"

echo -e "${GREEN}=== Testing Complete ===${NC}"
