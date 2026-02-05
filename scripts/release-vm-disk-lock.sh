#!/bin/bash
# Release lock on agent VM disk so setup can retry.
# Usage: ./release-vm-disk-lock.sh [agent_id]
#   agent_id optional; if omitted, uses the one from your error (7b053af9-...)

set -e
AGENT_ID="${1:-7b053af9-a386-425f-8127-492bfc156525}"

# 跨平台数据目录
if [ -z "$NOVAIC_DATA_DIR" ]; then
    if [ "$(uname)" = "Darwin" ]; then
        DATA_DIR="$HOME/Library/Application Support/com.novaic.app"
    elif [ "$(uname)" = "Linux" ]; then
        DATA_DIR="$HOME/.local/share/com.novaic.app"
    else
        DATA_DIR="$HOME/.novaic"
    fi
else
    DATA_DIR="$NOVAIC_DATA_DIR"
fi

DISK_PATH="$DATA_DIR/agents/$AGENT_ID/disk.qcow2"

echo "Checking processes using: $DISK_PATH"
if [ ! -f "$DISK_PATH" ]; then
  echo "File not found (maybe already removed). You can Retry setup."
  exit 0
fi

# Find PIDs with file open (macOS)
PIDS=$(lsof +D "$DATA_DIR/agents/$AGENT_ID" 2>/dev/null | awk 'NR>1 {print $2}' | sort -u)
if [ -n "$PIDS" ]; then
  echo "Processes using agent directory: $PIDS"
  for pid in $PIDS; do
    echo "  PID $pid: $(ps -p $pid -o comm= 2>/dev/null || echo '?')"
  done
  read -p "Kill these processes? [y/N] " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    for pid in $PIDS; do kill -9 "$pid" 2>/dev/null || true; done
    echo "Done. You can Retry setup in NovAIC."
  fi
else
  echo "No processes found holding the directory open."
  echo "If lock persists, try: (1) Quit NovAIC app fully (2) Run this script again (3) Retry setup."
fi

# Also show any qemu processes
echo ""
echo "All QEMU-related processes:"
pgrep -fl qemu || true
