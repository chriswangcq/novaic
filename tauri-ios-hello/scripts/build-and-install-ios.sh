#!/usr/bin/env bash
# Build iOS app and install to connected device.
# Workaround for Tauri CLI bug: "tauri ios run" fails with
#   error: Couldn't load -exportOptionsPlist The file ".tmpXXXX" couldn't be opened
# This script uses "tauri ios build" + devicectl install.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$APP_DIR"

echo "Building iOS app (debug)..."
npm run tauri:build:ios:debug

BUILD_DIR="$APP_DIR/src-tauri/gen/apple/build/arm64"
IPA_PATH="$BUILD_DIR/tauri-ios-hello.ipa"
if [[ ! -f "$IPA_PATH" ]]; then
  # Fallback: find any .ipa in build dir (Tauri may use different naming)
  IPA_PATH=$(find "$BUILD_DIR" -maxdepth 1 -name "*.ipa" 2>/dev/null | head -1)
fi
if [[ ! -f "$IPA_PATH" ]]; then
  echo "Error: IPA not found. Expected at $BUILD_DIR/tauri-ios-hello.ipa"
  echo "Make sure Xcode signing is configured (Development Team in Signing & Capabilities)."
  exit 1
fi

DEVICE=$(xcrun devicectl list devices 2>/dev/null | awk '
  /connected/ && !/Simulator/ {
    for (i=1;i<=NF;i++) if ($i ~ /^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$/) { print $i; exit }
  }
' | head -1)

if [[ -z "$DEVICE" ]]; then
  echo "No connected iOS device. Connect an iPhone and try again."
  echo "Or pass device ID: $0 <device-uuid>"
  exit 1
fi

echo "Installing to device $DEVICE..."
xcrun devicectl device install app --device "$DEVICE" "$IPA_PATH"

echo "Done. Tauri iOS Hello is installed."
