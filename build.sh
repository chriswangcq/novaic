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
cp novaic-gateway/dist/novaic-gateway "$RESOURCES_DIR/"
echo "  Copied to: $RESOURCES_DIR/"

# Step 3: Copy novaic-core to Tauri resources
echo ""
echo "[3/4] Copying novaic-core to Tauri resources..."
rm -rf "$RESOURCES_DIR/novaic-core"
mkdir -p "$RESOURCES_DIR/novaic-core"

# Copy source code
cp -r novaic-core/src "$RESOURCES_DIR/novaic-core/"
echo "  Copied: novaic-core/src/"

# Copy skills directory if exists
if [ -d "novaic-core/skills" ]; then
    cp -r novaic-core/skills "$RESOURCES_DIR/novaic-core/"
    echo "  Copied: novaic-core/skills/"
fi

# Copy pyproject.toml
cp novaic-core/pyproject.toml "$RESOURCES_DIR/novaic-core/"
echo "  Copied: novaic-core/pyproject.toml"

# Copy README if exists
if [ -f "novaic-core/README.md" ]; then
    cp novaic-core/README.md "$RESOURCES_DIR/novaic-core/"
fi

echo "  novaic-core packaged to: $RESOURCES_DIR/novaic-core/"

# Step 4: Build Tauri App
echo ""
echo "[4/4] Building Tauri App..."
cd novaic-app
npm run tauri build

echo ""
echo "=== Build Complete ==="
echo "Output files:"
ls -lh src-tauri/target/release/bundle/dmg/*.dmg 2>/dev/null || echo "  DMG not found"
ls -lh src-tauri/target/release/bundle/macos/*.app 2>/dev/null || echo "  APP not found"
