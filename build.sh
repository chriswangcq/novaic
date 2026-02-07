#!/bin/bash
# NovAIC Complete Build Script
# Builds unified Backend + Tauri App into a single distributable DMG

set -e

echo "=== NovAIC Complete Build ==="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RESOURCES_DIR="novaic-app/src-tauri/resources"

# Step 1: Build unified Backend (Gateway + Tools Server + Workers)
echo "[1/4] Building unified Backend (novaic-backend)..."
cd novaic-backend

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

# Step 2: Build vmcontrol (Rust VM control service)
echo ""
echo "[2/4] Building vmcontrol..."
cd novaic-app/src-tauri/vmcontrol

echo "  Building vmcontrol (release mode)..."
cargo build --release

VMCONTROL_SIZE=$(du -sh target/release/vmcontrol | cut -f1)
echo "  Built: target/release/vmcontrol ($VMCONTROL_SIZE)"

cd "$SCRIPT_DIR"

# Step 3: Copy Backend and vmcontrol to Tauri resources
echo ""
echo "[3/4] Copying resources to Tauri..."
mkdir -p "$RESOURCES_DIR"

# Copy unified Backend (onedir)
echo "  Copying novaic-backend..."
rm -rf "$RESOURCES_DIR/novaic-backend"
cp -r novaic-backend/dist/novaic-backend "$RESOURCES_DIR/"
echo "  Copied: $RESOURCES_DIR/novaic-backend/"

# Copy vmcontrol binary
echo "  Copying vmcontrol..."
mkdir -p "$RESOURCES_DIR/vmcontrol"
cp novaic-app/src-tauri/vmcontrol/target/release/vmcontrol "$RESOURCES_DIR/vmcontrol/"
echo "  Copied: $RESOURCES_DIR/vmcontrol/vmcontrol"

# Note: novaic-vm (FastMCP) is no longer needed - all VM tools are now provided by vmuse_adapter via vmcontrol

# Step 4: Build Tauri App
echo ""
echo "[4/4] Building Tauri App..."
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
echo "Backend usage (Saga/Task Architecture - multiple workers):"
echo "  ./novaic-backend gateway --port 19999 --data-dir /path/to/data"
echo "  ./novaic-backend tools-server --port 19998 --data-dir /path/to/data"
echo "  ./novaic-backend watchdog --gateway-url http://127.0.0.1:19999"
echo "  ./novaic-backend task-worker --gateway-url http://127.0.0.1:19999  # x3"
echo "  ./novaic-backend saga-worker --gateway-url http://127.0.0.1:19999  # x3"
echo "  ./novaic-backend health --gateway-url http://127.0.0.1:19999"
echo ""
echo "Default worker configuration:"
echo "  - Gateway:      1"
echo "  - Tools Server: 1"
echo "  - Watchdog:     1"
echo "  - Task Workers: 3"
echo "  - Saga Workers: 3"
echo "  - Health:       1"
