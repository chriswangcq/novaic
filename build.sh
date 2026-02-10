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

# Step 2.5: Bundle QEMU with all dependencies (for self-contained distribution)
echo ""
echo "[2.5/4] Bundling QEMU with dependencies..."
QEMU_RESOURCES="$RESOURCES_DIR/qemu"
QEMU_LIBS="$QEMU_RESOURCES/libs"
rm -rf "$QEMU_RESOURCES"
mkdir -p "$QEMU_RESOURCES"
mkdir -p "$QEMU_LIBS"

ARCH=$(uname -m)
QEMU_COPIED=false

# Function to collect all Homebrew dependencies iteratively
collect_all_deps_iterative() {
    local LIBS_DIR="$1"
    shift
    local BINARIES=("$@")
    
    # First, copy direct dependencies from all binaries
    for BINARY in "${BINARIES[@]}"; do
        if [ -f "$BINARY" ]; then
            otool -L "$BINARY" 2>/dev/null | grep "/opt/homebrew" | awk '{print $1}' | while read DEP; do
                DEP_NAME=$(basename "$DEP")
                if [ -f "$DEP" ] && [ ! -f "$LIBS_DIR/$DEP_NAME" ]; then
                    echo "      Copying: $DEP_NAME"
                    copy_without_xattr "$DEP" "$LIBS_DIR/$DEP_NAME"
                    chmod 755 "$LIBS_DIR/$DEP_NAME"
                fi
            done
        fi
    done
    
    # Multiple passes to get transitive dependencies (up to 5 levels deep)
    for i in 1 2 3 4 5; do
        local FOUND_NEW=false
        for LIB in "$LIBS_DIR"/*.dylib; do
            if [ -f "$LIB" ]; then
                otool -L "$LIB" 2>/dev/null | grep "/opt/homebrew" | awk '{print $1}' | while read DEP; do
                    DEP_NAME=$(basename "$DEP")
                    if [ -f "$DEP" ] && [ ! -f "$LIBS_DIR/$DEP_NAME" ]; then
                        echo "      Copying (level $i): $DEP_NAME"
                        copy_without_xattr "$DEP" "$LIBS_DIR/$DEP_NAME"
                        chmod 755 "$LIBS_DIR/$DEP_NAME"
                    fi
                done
            fi
        done
    done
}

# Function to copy file without extended attributes
copy_without_xattr() {
    local SRC="$1"
    local DEST="$2"
    # Use cat to copy content only, avoiding extended attributes
    cat "$SRC" > "$DEST"
    chmod --reference="$SRC" "$DEST" 2>/dev/null || chmod 755 "$DEST"
}

# Function to bundle a binary with its dylib dependencies using install_name_tool
bundle_binary_with_deps() {
    local BINARY="$1"
    local DEST_DIR="$2"
    local LIBS_DIR="$3"
    local BINARY_NAME=$(basename "$BINARY")
    
    echo "    Copying $BINARY_NAME..."
    copy_without_xattr "$BINARY" "$DEST_DIR/$BINARY_NAME"
    chmod 755 "$DEST_DIR/$BINARY_NAME"
    
    # Update the binary to use @executable_path/libs/
    otool -L "$BINARY" 2>/dev/null | grep "/opt/homebrew" | awk '{print $1}' | while read DEP; do
        DEP_NAME=$(basename "$DEP")
        install_name_tool -change "$DEP" "@executable_path/libs/$DEP_NAME" "$DEST_DIR/$BINARY_NAME" 2>/dev/null || true
    done
}

# Function to fix library references within libs directory
fix_lib_references() {
    local LIBS_DIR="$1"
    
    echo "    Fixing library cross-references..."
    for LIB in "$LIBS_DIR"/*.dylib; do
        if [ -f "$LIB" ]; then
            local LIB_NAME=$(basename "$LIB")
            
            # Fix the library's own ID
            install_name_tool -id "@executable_path/libs/$LIB_NAME" "$LIB" 2>/dev/null || true
            
            # Fix references to other Homebrew libraries
            local DEPS=$(otool -L "$LIB" 2>/dev/null | grep "/opt/homebrew" | awk '{print $1}')
            for DEP in $DEPS; do
                local DEP_NAME=$(basename "$DEP")
                install_name_tool -change "$DEP" "@executable_path/libs/$DEP_NAME" "$LIB" 2>/dev/null || true
            done
        fi
    done
}

if [ "$ARCH" = "arm64" ]; then
    # macOS ARM64
    QEMU_BIN="/opt/homebrew/bin/qemu-system-aarch64"
    QEMU_IMG="/opt/homebrew/bin/qemu-img"
    QEMU_SHARE="/opt/homebrew/share/qemu"
    
    if [ -f "$QEMU_BIN" ]; then
        echo "  Bundling qemu-system-aarch64..."
        bundle_binary_with_deps "$QEMU_BIN" "$QEMU_RESOURCES" "$QEMU_LIBS"
        QEMU_COPIED=true
    else
        echo "  Warning: qemu-system-aarch64 not found at $QEMU_BIN"
    fi
    
    if [ -f "$QEMU_IMG" ]; then
        echo "  Bundling qemu-img..."
        bundle_binary_with_deps "$QEMU_IMG" "$QEMU_RESOURCES" "$QEMU_LIBS"
    fi
    
    # Collect all dependencies for both binaries
    if [ "$QEMU_COPIED" = true ]; then
        echo "  Collecting all dependencies..."
        collect_all_deps_iterative "$QEMU_LIBS" "$QEMU_BIN" "$QEMU_IMG"
    fi
    
    # Copy QEMU share directory (ROM files, firmware, keymaps, etc.)
    if [ -d "$QEMU_SHARE" ]; then
        echo "  Copying QEMU share directory (ROM files, firmware)..."
        QEMU_SHARE_DEST="$QEMU_RESOURCES/share"
        mkdir -p "$QEMU_SHARE_DEST"
        # Copy all files from share directory
        for FILE in "$QEMU_SHARE"/*; do
            if [ -f "$FILE" ]; then
                FILENAME=$(basename "$FILE")
                copy_without_xattr "$FILE" "$QEMU_SHARE_DEST/$FILENAME"
            elif [ -d "$FILE" ]; then
                # Copy subdirectories (like keymaps, firmware)
                DIRNAME=$(basename "$FILE")
                cp -r "$FILE" "$QEMU_SHARE_DEST/$DIRNAME"
            fi
        done
        chmod -R 644 "$QEMU_SHARE_DEST"/* 2>/dev/null || true
        find "$QEMU_SHARE_DEST" -type d -exec chmod 755 {} \; 2>/dev/null || true
        SHARE_SIZE=$(du -sh "$QEMU_SHARE_DEST" | cut -f1)
        echo "    Copied share directory ($SHARE_SIZE)"
    else
        echo "  Warning: QEMU share directory not found at $QEMU_SHARE"
    fi
else
    # macOS Intel or Linux x86_64
    QEMU_BIN_PATHS=("/usr/local/bin/qemu-system-x86_64" "/usr/bin/qemu-system-x86_64" "/opt/homebrew/bin/qemu-system-x86_64")
    QEMU_IMG_PATHS=("/usr/local/bin/qemu-img" "/usr/bin/qemu-img" "/opt/homebrew/bin/qemu-img")
    FOUND_QEMU_BIN=""
    FOUND_QEMU_IMG=""
    
    for QEMU_BIN in "${QEMU_BIN_PATHS[@]}"; do
        if [ -f "$QEMU_BIN" ]; then
            echo "  Bundling qemu-system-x86_64..."
            bundle_binary_with_deps "$QEMU_BIN" "$QEMU_RESOURCES" "$QEMU_LIBS"
            FOUND_QEMU_BIN="$QEMU_BIN"
            QEMU_COPIED=true
            break
        fi
    done
    
    for QEMU_IMG in "${QEMU_IMG_PATHS[@]}"; do
        if [ -f "$QEMU_IMG" ]; then
            echo "  Bundling qemu-img..."
            bundle_binary_with_deps "$QEMU_IMG" "$QEMU_RESOURCES" "$QEMU_LIBS"
            FOUND_QEMU_IMG="$QEMU_IMG"
            break
        fi
    done
    
    # Collect all dependencies for both binaries
    if [ "$QEMU_COPIED" = true ]; then
        echo "  Collecting all dependencies..."
        collect_all_deps_iterative "$QEMU_LIBS" "$FOUND_QEMU_BIN" "$FOUND_QEMU_IMG"
    fi
fi

# Fix cross-references between libraries
if [ "$QEMU_COPIED" = true ]; then
    fix_lib_references "$QEMU_LIBS"
    
    # Remove empty libs directory if no libraries were copied
    if [ -z "$(ls -A "$QEMU_LIBS" 2>/dev/null)" ]; then
        rmdir "$QEMU_LIBS"
    fi
    
    # Clear extended attributes (com.apple.provenance causes Tauri build issues)
    echo "  Clearing extended attributes..."
    xattr -cr "$QEMU_RESOURCES" 2>/dev/null || true
    
    # Create entitlements file for QEMU (required for HVF hardware virtualization)
    QEMU_ENTITLEMENTS="$QEMU_RESOURCES/qemu.entitlements"
    cat > "$QEMU_ENTITLEMENTS" << 'ENTITLEMENTS_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.hypervisor</key>
    <true/>
</dict>
</plist>
ENTITLEMENTS_EOF
    
    # Re-sign all binaries and libraries (required on macOS after modification)
    echo "  Re-signing binaries and libraries with HVF entitlement..."
    for BIN in "$QEMU_RESOURCES"/qemu-*; do
        if [ -f "$BIN" ] && [ -x "$BIN" ]; then
            codesign --force --sign - --entitlements "$QEMU_ENTITLEMENTS" "$BIN" 2>/dev/null && echo "    Signed: $(basename "$BIN")"
        fi
    done
    for LIB in "$QEMU_LIBS"/*.dylib; do
        if [ -f "$LIB" ]; then
            codesign --force --sign - "$LIB" 2>/dev/null
        fi
    done
    echo "    Signed all libraries in libs/"
    
    # Clear extended attributes again after signing
    xattr -cr "$QEMU_RESOURCES" 2>/dev/null || true
    
    QEMU_SIZE=$(du -sh "$QEMU_RESOURCES" | cut -f1)
    echo "  Bundled QEMU: $QEMU_RESOURCES/ ($QEMU_SIZE)"
    
    # Verify the bundled binary works
    echo "  Verifying bundled QEMU..."
    if "$QEMU_RESOURCES/qemu-system-aarch64" --version >/dev/null 2>&1 || \
       "$QEMU_RESOURCES/qemu-system-x86_64" --version >/dev/null 2>&1; then
        echo "  Verification passed!"
    else
        echo "  Warning: Bundled QEMU verification failed, checking dependencies..."
        otool -L "$QEMU_RESOURCES"/qemu-system-* 2>/dev/null | grep "not found" || echo "  All dependencies resolved"
    fi
else
    echo "  Warning: QEMU binaries not found, app will use system QEMU"
    # Keep the empty directory so Tauri build doesn't fail
    # The app will fall back to system QEMU when bundled QEMU is not present
    echo "QEMU not bundled - using system QEMU" > "$QEMU_RESOURCES/README.txt"
fi

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
rm -rf "$RESOURCES_DIR/vmcontrol"
mkdir -p "$RESOURCES_DIR/vmcontrol"
cp novaic-app/src-tauri/vmcontrol/target/release/vmcontrol "$RESOURCES_DIR/vmcontrol/"
echo "  Copied: $RESOURCES_DIR/vmcontrol/vmcontrol"

# Note: novaic-vm (FastMCP) is no longer needed - all VM tools are now provided by vmuse_adapter via vmcontrol

# Step 4: Build Tauri App
echo ""
echo "[4/4] Building Tauri App..."
cd novaic-app

# Clean Tauri build cache to avoid stale resource issues
# This is necessary when resources (like QEMU) are added/modified
echo "  Cleaning Tauri build cache..."
(cd src-tauri && cargo clean -p novaic 2>/dev/null) || true

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
