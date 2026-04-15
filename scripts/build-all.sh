#!/bin/bash
# build-all.sh - Build all split repos into binaries
# Usage: ./build-all.sh [--clean] [--tauri]
#   --clean: Clean previous builds (dist/)
#   --tauri: Build full DMG (delegates to novaic-app/scripts/build-dmg.sh)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/dist"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Parse arguments
CLEAN=false
BUILD_TAURI=false
for arg in "$@"; do
    case $arg in
        --clean) CLEAN=true ;;
        --tauri) BUILD_TAURI=true ;;
    esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  NovAIC Split Build (Strategy A)     ${NC}"
echo -e "${GREEN}========================================${NC}"

# --tauri: delegate to build-dmg.sh (single source of truth)
if [ "$BUILD_TAURI" = true ]; then
    cd "$SCRIPT_DIR/novaic-app"
    exec ./scripts/build-dmg.sh
fi

# Clean if requested
if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}Cleaning previous builds...${NC}"
    rm -rf "$BUILD_DIR"
fi

mkdir -p "$BUILD_DIR"

# Build order matters for dependencies
REPOS=(
    "novaic-storage-a"
    "novaic-gateway"
    "novaic-agent-runtime"
)

build_repo() {
    local repo=$1
    local spec_file="$SCRIPT_DIR/$repo/$repo.spec"
    
    echo ""
    echo -e "${GREEN}[Building] $repo${NC}"
    
    if [ ! -f "$spec_file" ]; then
        echo -e "${RED}  ERROR: $spec_file not found${NC}"
        return 1
    fi
    
    cd "$SCRIPT_DIR/$repo"
    
    # Activate venv if exists
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Build with PyInstaller
    pyinstaller --clean --noconfirm "$spec_file"
    
    # Copy binary to dist
    if [ -f "dist/$repo" ]; then
        cp "dist/$repo" "$BUILD_DIR/"
        echo -e "${GREEN}  ✓ Built: $BUILD_DIR/$repo${NC}"
    else
        echo -e "${RED}  ERROR: Binary not found${NC}"
        return 1
    fi
}

# Build each repo
for repo in "${REPOS[@]}"; do
    if [ -d "$SCRIPT_DIR/$repo" ]; then
        build_repo "$repo"
    else
        echo -e "${YELLOW}[Skip] $repo (not found)${NC}"
    fi
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Python Backends Build Complete!      ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Binaries in: $BUILD_DIR/"
ls -la "$BUILD_DIR/"

echo ""
echo "To run services:"
echo "  $BUILD_DIR/novaic-gateway --port 19999"
echo "  $BUILD_DIR/novaic-storage-a --port 19995"
echo "  $BUILD_DIR/novaic-agent-runtime scheduler --gateway-url http://127.0.0.1:19999 --queue-service-url http://127.0.0.1:19997"
echo ""
echo "To build Tauri DMG, run: ./build-all.sh --tauri"
