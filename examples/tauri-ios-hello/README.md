# Tauri iOS Hello World

Minimal Tauri iOS project for debugging. Separate from the main NovaIC app.

## Prerequisites

- Node.js, Rust, Xcode
- iOS device connected (or simulator)
- Signing uses same config as NovaIC app (Development Team K9FF74JCRL, bundle `com.novaic.app.hello`)

## Commands

| Command | Description |
|---------|-------------|
| `npm run tauri:dev` | Run on desktop (macOS) |
| `npm run tauri:build:ios:debug` | Build iOS app (debug) |
| `npm run tauri:run:ios` | Build + install to connected iPhone |
| `npm run tauri:open:ios` | Open Xcode project |

## iOS Build & Install

```bash
# Build and install to connected device
./scripts/build-and-install-ios.sh

# Or with specific device ID
./scripts/build-and-install-ios.sh <device-uuid>
```

If `tauri ios run` fails with "Couldn't load -exportOptionsPlist", use the script above instead (it uses `tauri ios build` + `devicectl install`).

## Recommended IDE Setup

- [VS Code](https://code.visualstudio.com/) + [Tauri](https://marketplace.visualstudio.com/items?itemName=tauri-apps.tauri-vscode) + [rust-analyzer](https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer)
