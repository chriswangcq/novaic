#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

matches="$(
  rg -n \
    "generate_entity_types|check_entity_store_pk|sync_entity_id_fields|export_entity_id_fields|generated_entity_id_fields|__generated__|subscriber_enabled|Subscriber: disabled|Runtime Orchestrator.*argparse|--runtime-orchestrator-url" \
    docs/architecture docs/runtime docs/runbooks docs/roadmap/model-entity-refactor.md \
    --glob '!docs/architecture/gateway-decomposition-roadmap.md' || true
)"

if [[ -n "$matches" ]]; then
  echo "Current docs still describe retired operational paths:" >&2
  echo "$matches" >&2
  exit 1
fi
