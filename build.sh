#!/bin/bash
# NovAIC Complete Build Script
# Builds unified Backend + Tauri App into a single distributable DMG

set -e

echo "=== NovAIC Complete Build ==="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RESOURCES_DIR="novaic-app/src-tauri/resources"

# Step 1: Build unified Backend (Gateway + MCP Gateway + Master + Worker)
echo "[1/3] Building unified Backend (novaic-backend)..."
cd novaic-gateway

if [ ! -d ".venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv .venv
fi

echo "  Installing dependencies..."
./.venv/bin/pip install -q -r requirements.txt

echo "  Building novaic-backend (onedir mode)..."
./.venv/bin/pyinstaller --clean --noconfirm novaic-backend.spec

# Check build result
if [ ! -f "dist/novaic-backend/novaic-backend" ]; then
    echo "ERROR: Build failed - novaic-backend not found"
    exit 1
fi

BACKEND_SIZE=$(du -sh dist/novaic-backend | cut -f1)
echo "  Built: dist/novaic-backend/ ($BACKEND_SIZE)"

cd "$SCRIPT_DIR"

# Step 2: Copy Backend and MCP to Tauri resources
echo ""
echo "[2/3] Copying resources to Tauri..."
mkdir -p "$RESOURCES_DIR"

# Copy unified Backend (onedir)
echo "  Copying novaic-backend..."
rm -rf "$RESOURCES_DIR/novaic-backend"
cp -r novaic-gateway/dist/novaic-backend "$RESOURCES_DIR/"
echo "  Copied: $RESOURCES_DIR/novaic-backend/"

# Copy novaic-mcp-vmuse (VM-side MCP server)
echo "  Copying novaic-mcp-vmuse..."
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

# Step 3: Build Tauri App
echo ""
echo "[3/3] Building Tauri App..."
cd novaic-app

# Regenerate app icon with macOS safe area (smaller, rounder) if script and deps exist
ICON_SCRIPT="src-tauri/icons/regenerate_app_icon.py"
if [ -f "$ICON_SCRIPT" ] && python3 -c "from PIL import Image" 2>/dev/null; then
    echo "  Regenerating app icon (safe-area)..."
    (cd src-tauri/icons && python3 regenerate_app_icon.py) || true
fi

# Unset CI env var as tauri CLI doesn't accept CI=1 (only true/false)
unset CI

npm run tauri build

echo ""
echo "=== Build Complete ==="
echo ""
echo "Output files:"
ls -lh src-tauri/target/release/bundle/dmg/*.dmg 2>/dev/null || echo "  DMG not found"
ls -lh src-tauri/target/release/bundle/macos/*.app 2>/dev/null || echo "  APP not found"
echo ""
echo "Backend usage (four components):"
echo "  ./novaic-backend gateway --port 19999"
echo "  ./novaic-backend mcp-gateway --port 19998"
echo "  ./novaic-backend master --gateway-url http://127.0.0.1:19999 --mcp-gateway-url http://127.0.0.1:19998"
echo "  ./novaic-backend worker --gateway http://127.0.0.1:19999 --mcp-gateway-url http://127.0.0.1:19998"
