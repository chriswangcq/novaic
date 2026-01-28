#!/bin/bash
# NovAIC Complete Build Script
# Builds Gateway + Tauri App into a single distributable DMG

set -e

echo "=== NovAIC Complete Build ==="
echo ""

# Step 1: Build Gateway
echo "[1/3] Building Gateway..."
cd novaic-gateway
if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install -q -r requirements.txt
fi
./venv/bin/python build.py
echo "  Gateway built: dist/novaic-gateway"

# Step 2: Copy Gateway to Tauri resources
echo ""
echo "[2/3] Copying Gateway to Tauri resources..."
mkdir -p ../novaic-app/src-tauri/resources
cp dist/novaic-gateway ../novaic-app/src-tauri/resources/
echo "  Copied to: novaic-app/src-tauri/resources/"

# Step 3: Build Tauri App
echo ""
echo "[3/3] Building Tauri App..."
cd ../novaic-app
npm run build
cd src-tauri
cargo build --release

# Bundle
echo ""
echo "[4/4] Creating DMG..."
cd target/release/bundle

# Create .app bundle manually if needed
if [ -d "macos/NovAIC.app" ]; then
    hdiutil create -volname "NovAIC" -srcfolder macos/NovAIC.app -ov -format UDZO NovAIC_complete.dmg
    echo ""
    echo "=== Build Complete ==="
    echo "Output: novaic-app/src-tauri/target/release/bundle/NovAIC_complete.dmg"
    ls -lh NovAIC_complete.dmg
else
    echo "Error: .app bundle not found"
    exit 1
fi
