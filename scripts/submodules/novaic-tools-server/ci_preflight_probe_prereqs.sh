#!/usr/bin/env bash
set -euo pipefail

# Policy Choice: Option A
# Ubuntu/Debian CI is supported.
# Non-Linux runner is unsupported without explicit branch.

command -v lsof >/dev/null 2>&1 || { echo "[probe-preflight] FAIL: missing lsof"; exit 1; }
command -v pgrep >/dev/null 2>&1 || { echo "[probe-preflight] FAIL: missing pgrep"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "[probe-preflight] FAIL: missing python3"; exit 1; }
echo "[probe-preflight] PASS"
