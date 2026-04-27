#!/usr/bin/env bash
# PR-76 — keep Cortex focused on scope lifecycle and LLM context assembly.
set -euo pipefail

python3 novaic-cortex/scripts/check_cortex_boundary.py --root .
