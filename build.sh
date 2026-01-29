#!/bin/bash
# NovAIC Complete Build Script
# Builds Gateway + Tauri App into a single distributable DMG

set -e

echo "=== NovAIC Complete Build ==="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RESOURCES_DIR="novaic-app/src-tauri/resources"

# Step 1: Build Gateway
echo "[1/4] Building Gateway..."
cd novaic-gateway
if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install -q -r requirements.txt
fi
./venv/bin/python build.py
echo "  Gateway built: dist/novaic-gateway"
cd "$SCRIPT_DIR"

# Step 2: Copy Gateway to Tauri resources
echo ""
echo "[2/4] Copying Gateway to Tauri resources..."
mkdir -p "$RESOURCES_DIR"
# onedir mode: copy the entire directory
rm -rf "$RESOURCES_DIR/novaic-gateway"
cp -r novaic-gateway/dist/novaic-gateway "$RESOURCES_DIR/"
echo "  Copied to: $RESOURCES_DIR/novaic-gateway/"

# Step 3: Copy novaic-mcp-vmuse to Tauri resources
echo ""
echo "[3/4] Copying novaic-mcp-vmuse to Tauri resources..."
rm -rf "$RESOURCES_DIR/novaic-mcp-vmuse"
mkdir -p "$RESOURCES_DIR/novaic-mcp-vmuse"

# Copy source code
cp -r novaic-mcp-vmuse/src "$RESOURCES_DIR/novaic-mcp-vmuse/"
echo "  Copied: novaic-mcp-vmuse/src/"

# Copy skills directory if exists
if [ -d "novaic-mcp-vmuse/skills" ]; then
    cp -r novaic-mcp-vmuse/skills "$RESOURCES_DIR/novaic-mcp-vmuse/"
    echo "  Copied: novaic-mcp-vmuse/skills/"
fi

# Copy pyproject.toml
cp novaic-mcp-vmuse/pyproject.toml "$RESOURCES_DIR/novaic-mcp-vmuse/"
echo "  Copied: novaic-mcp-vmuse/pyproject.toml"

# Copy README if exists
if [ -f "novaic-mcp-vmuse/README.md" ]; then
    cp novaic-mcp-vmuse/README.md "$RESOURCES_DIR/novaic-mcp-vmuse/"
fi

echo "  novaic-mcp-vmuse packaged to: $RESOURCES_DIR/novaic-mcp-vmuse/"

# Step 4: Build Tauri App
echo ""
echo "[4/4] Building Tauri App..."
cd novaic-app
# Unset CI env var as tauri CLI doesn't accept CI=1 (only true/false)
unset CI
npm run tauri build

echo ""
echo "=== Build Complete ==="
echo "Output files:"
ls -lh src-tauri/target/release/bundle/dmg/*.dmg 2>/dev/null || echo "  DMG not found"
ls -lh src-tauri/target/release/bundle/macos/*.app 2>/dev/null || echo "  APP not found"
