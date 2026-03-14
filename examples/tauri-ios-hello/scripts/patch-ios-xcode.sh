#!/usr/bin/env bash
# Fix Xcode build script: Build Rust Code must run npm from tauri-ios-hello root
set -e
cd "$(dirname "$0")/.."
GEN=src-tauri/gen/apple
[ ! -d "$GEN" ] && exit 0

PBXPROJ="$GEN/tauri-ios-hello.xcodeproj/project.pbxproj"
[ ! -f "$PBXPROJ" ] && exit 0

# Remove FORCE_COLOR / stray "0" that breaks arch arg
sed -i '' 's/} 0 \${/} \${/g' "$PBXPROJ" 2>/dev/null || true

# Use wrapper script (locates project root via $0, no SRCROOT dependency)
if ! grep -q 'run-ios-xcode-script.sh' "$PBXPROJ" 2>/dev/null; then
  sed -i '' 's|shellScript = "cd \\"$(SRCROOT)/../../..\\" \&\& npm run -- tauri ios xcode-script -v|shellScript = "\"${SRCROOT}/../../../scripts/run-ios-xcode-script.sh\" -v|' "$PBXPROJ"
  sed -i '' 's|shellScript = "npm run -- tauri ios xcode-script -v|shellScript = "\"${SRCROOT}/../../../scripts/run-ios-xcode-script.sh\" -v|' "$PBXPROJ"
fi
