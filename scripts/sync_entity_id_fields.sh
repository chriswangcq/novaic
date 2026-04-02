#!/usr/bin/env bash
# Copy Gateway-generated entity→idField map to Rust + App (single source: novaic-gateway export).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${1:-$ROOT/novaic-gateway/gateway/entity/generated_entity_id_fields.json}"
if [[ ! -f "$SRC" ]]; then
  echo "Missing $SRC — run: cd novaic-gateway && python scripts/export_entity_id_fields.py" >&2
  exit 1
fi
cp "$SRC" "$ROOT/Entangled/packages/client-rust/entity_id_fields.json"
cp "$SRC" "$ROOT/novaic-app/src/data/entangled/generated_entity_id_fields.json"
echo "Synced entity id fields → entangled-client + novaic-app"
