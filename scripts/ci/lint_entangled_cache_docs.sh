#!/usr/bin/env bash
set -euo pipefail

# Guardrail for PR-91:
# The active App Entangled cache is a read model (`entity_meta` + `entity_items`).
# `pending_ops` is legacy-only and must not reappear as an active troubleshooting
# or client write-queue instruction.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

matches="$(
  rg -n -i \
    "(active[^\\n]*pending_ops|pending_ops[^\\n]*active|current[^\\n]*pending_ops|pending_ops[^\\n]*required|clear[^\\n]*pending_ops|pending_ops[^\\n]*cleanup|client write queue|write queue[^\\n]*pending_ops)" \
    docs Entangled/packages/client-rust/src scripts \
    --glob '*.md' --glob '*.rs' --glob '*.sh' \
    --glob '!docs/roadmap/tickets/**' \
    --glob '!scripts/ci/lint_entangled_cache_docs.sh' || true
)"

if [[ -z "$matches" ]]; then
  exit 0
fi

violations="$(
  printf '%s\n' "$matches" | rg -v -i \
    "(no longer active|not active|legacy|historical|deprecated|stale docs|do not add offline write queue|废弃|退役|历史|初始化|DROP TABLE|rejects reintroducing)" || true
)"

if [[ -n "$violations" ]]; then
  echo "Active-path pending_ops/client write-queue wording is not allowed:" >&2
  echo "$violations" >&2
  exit 1
fi
