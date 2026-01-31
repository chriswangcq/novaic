#!/bin/bash
# NovAIC Complete Build Script
# Builds Gateway + Worker + Tauri App into a single distributable DMG

set -e

echo "=== NovAIC Complete Build ==="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RESOURCES_DIR="novaic-app/src-tauri/resources"

# Step 1: Build Gateway and Worker
echo "[1/4] Building Gateway and Worker..."
cd novaic-gateway
if [ ! -d ".venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv .venv
fi
echo "  Installing dependencies..."
./.venv/bin/pip install -q -r requirements.txt

echo "  Building Gateway..."
./.venv/bin/python build.py
echo "  Gateway built: dist/novaic-gateway"

echo "  Building Worker..."
./.venv/bin/pyinstaller --clean --noconfirm novaic-worker.spec
echo "  Worker built: dist/novaic-worker"

cd "$SCRIPT_DIR"

# Step 2: Copy Gateway and Worker to Tauri resources
echo ""
echo "[2/4] Copying Gateway and Worker to Tauri resources..."
mkdir -p "$RESOURCES_DIR"

# Copy Gateway (onedir mode)
rm -rf "$RESOURCES_DIR/novaic-gateway"
cp -r novaic-gateway/dist/novaic-gateway "$RESOURCES_DIR/"
echo "  Copied Gateway to: $RESOURCES_DIR/novaic-gateway/"

# Copy Worker (single file)
rm -f "$RESOURCES_DIR/novaic-worker"
cp novaic-gateway/dist/novaic-worker "$RESOURCES_DIR/"
echo "  Copied Worker to: $RESOURCES_DIR/novaic-worker"

# Step 3: Copy novaic-mcp-vmuse to Tauri resources (VM-side MCP)
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

# Note: Host-side MCP services (session, local, memory, chat) are now
# embedded in the Gateway. No separate packaging needed.

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
