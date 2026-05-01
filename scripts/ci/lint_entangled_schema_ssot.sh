#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

retired_files=(
  "scripts/generate_entity_types.py"
  "scripts/check_entity_store_pk.py"
  "scripts/sync_entity_id_fields.sh"
  "scripts/gateway/export_entity_id_fields.py"
  "novaic-gateway/gateway/entity/generated_entity_id_fields.json"
  "novaic-app/src/data/entities/__generated__.ts"
  "novaic-app/src/data/entangled/generated_entity_id_fields.json"
  "Entangled/packages/client-rust/entity_id_fields.json"
)

missing_ok=1
for path in "${retired_files[@]}"; do
  if [[ -e "$path" ]]; then
    echo "Retired generated schema artifact still exists: $path" >&2
    missing_ok=0
  fi
done

if [[ "$missing_ok" -ne 1 ]]; then
  exit 1
fi

matches="$(
  rg -n \
    "generate_entity_types|check_entity_store_pk|sync_entity_id_fields|export_entity_id_fields|generated_entity_id_fields|__generated__|entity_id_fields\\.json" \
    .github scripts novaic-app/src novaic-gateway/gateway Entangled \
    --glob '!scripts/ci/lint_entangled_schema_ssot.sh' \
    --glob '!scripts/ci/lint_current_docs_residue.sh' \
    --glob '!**/__pycache__/**' || true
)"

if [[ -n "$matches" ]]; then
  echo "Retired generated schema pipeline references remain in active paths:" >&2
  echo "$matches" >&2
  exit 1
fi
