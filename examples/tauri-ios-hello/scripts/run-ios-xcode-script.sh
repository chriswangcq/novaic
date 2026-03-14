#!/usr/bin/env bash
# Wrapper for tauri ios xcode-script: must run from tauri-ios-hello root
# Xcode build env PATH may not include npm
set -e
export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.volta/bin:$PATH"
if ! command -v npm >/dev/null 2>&1; then
  [ -f "$HOME/.nvm/nvm.sh" ] && . "$HOME/.nvm/nvm.sh"
  [ -f "$HOME/.fnm/fnm" ] && eval "$("$HOME/.fnm/fnm" env)"
fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec npm run -- tauri ios xcode-script "$@"
