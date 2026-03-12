#!/usr/bin/env bash
# OTA 三处配置一致性校验：config/index.ts OTA_ORIGINS、remote-frontend.json remote.urls、setup.rs OTA_ALLOWED_HOSTS
# 新增 CDN 域名时需同时修改三处，此脚本用于 CI 校验

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# 1. 从 config/index.ts 提取 OTA_ORIGINS 的 host（排序）
ORIGINS_HOSTS=$(sed -n "s/.*OTA_ORIGINS = \[\([^]]*\)\].*/\1/p" novaic-app/src/config/index.ts | tr -d "'\"" | tr ',' '\n' | sed 's|https://||g' | sed 's|http://||g' | tr -d ' ' | grep -v '^$' | sort -u)
if [ -z "$ORIGINS_HOSTS" ]; then
  echo "ERROR: Could not extract OTA_ORIGINS from novaic-app/src/config/index.ts"
  exit 1
fi

# 2. 从 remote-frontend.json 提取 remote.urls 的 host（排序）
REMOTE_HOSTS=$(grep -E '"https://[^"]+\*"' novaic-app/src-tauri/capabilities/remote-frontend.json | sed 's/.*"https:\/\/\([^"*\/]*\).*/\1/' | sed 's/\/$//' | sort -u)
if [ -z "$REMOTE_HOSTS" ]; then
  echo "ERROR: Could not extract remote.urls from novaic-app/src-tauri/capabilities/remote-frontend.json"
  exit 1
fi

# 3. 从 setup.rs 提取 OTA_ALLOWED_HOSTS（排序）
RUST_HOSTS=$(sed -n 's/.*OTA_ALLOWED_HOSTS: &\[&str\] = &\[\([^]]*\)\].*/\1/p' novaic-app/src-tauri/src/setup.rs | tr -d '"' | tr ',' '\n' | tr -d ' ' | grep -v '^$' | sort -u)
if [ -z "$RUST_HOSTS" ]; then
  echo "ERROR: Could not extract OTA_ALLOWED_HOSTS from novaic-app/src-tauri/src/setup.rs"
  exit 1
fi

# 4. 比较三处是否一致
DIFF_ORIGIN_REMOTE=$(diff <(echo "$ORIGINS_HOSTS") <(echo "$REMOTE_HOSTS") || true)
DIFF_ORIGIN_RUST=$(diff <(echo "$ORIGINS_HOSTS") <(echo "$RUST_HOSTS") || true)
DIFF_REMOTE_RUST=$(diff <(echo "$REMOTE_HOSTS") <(echo "$RUST_HOSTS") || true)

if [ -n "$DIFF_ORIGIN_REMOTE" ] || [ -n "$DIFF_ORIGIN_RUST" ] || [ -n "$DIFF_REMOTE_RUST" ]; then
  echo "ERROR: OTA config mismatch across three locations"
  echo ""
  echo "config/index.ts OTA_ORIGINS hosts:"
  echo "$ORIGINS_HOSTS"
  echo ""
  echo "remote-frontend.json remote.urls hosts:"
  echo "$REMOTE_HOSTS"
  echo ""
  echo "setup.rs OTA_ALLOWED_HOSTS:"
  echo "$RUST_HOSTS"
  echo ""
  echo "Update all three to match. See HANDOVER.md OTA section."
  exit 1
fi

echo "OK: OTA config consistent (config, remote-frontend.json, setup.rs)"
