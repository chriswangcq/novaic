# Round 002 API Contract Release Checklist (API Team)

This checklist is required before merging API-side contract changes in split execution.

## Checklist (must all pass)

1. OpenAPI version markers are present in all contract files.
2. Gateway and runtime health endpoints/operation IDs still match baseline.
3. Gateway startup/health replay is green.
4. Consumer impact note is recorded for any changed dependency contract.

## Replay commands and expected markers

- command:
  - `python3 -c "from pathlib import Path; files=['contracts/openapi/gateway-public.v1.yaml','contracts/openapi/runtime-orchestrator-internal.v1.yaml','contracts/openapi/storage-contracts.v1.yaml']; missing=[p for p in files if 'openapi: 3.1.0' not in Path(p).read_text(encoding='utf-8')]; print('OPENAPI_VERSION_CHECK=PASS' if not missing else 'OPENAPI_VERSION_CHECK=FAIL'); [print('FILE_OK='+p) for p in files if p not in missing]; import sys; sys.exit(0 if not missing else 1)"`
- expected_marker:
  - `OPENAPI_VERSION_CHECK=PASS`

- command:
  - `python3 -c "from pathlib import Path; checks={'contracts/openapi/gateway-public.v1.yaml':['/health:','operationId: getGatewayHealth'],'contracts/openapi/runtime-orchestrator-internal.v1.yaml':['/internal/health:','operationId: getRuntimeOrchestratorHealth']}; bad=[]; [bad.append((p,m)) for p,ms in checks.items() for m in ms if m not in Path(p).read_text(encoding='utf-8')]; ok=not bad; print('INTERFACE_MARKER_CHECK=PASS' if ok else 'INTERFACE_MARKER_CHECK=FAIL'); [print('FILE_OK='+p) for p in checks]; [print('MARKER_OK='+m) for p,ms in checks.items() for m in ms if (p,m) not in bad]; import sys; sys.exit(0 if ok else 1)"`
- expected_marker:
  - `INTERFACE_MARKER_CHECK=PASS`

- command:
  - `bash novaic-backend/scripts/smoke_gateway_independent_startup.sh`
- expected_marker:
  - `PASS: gateway API root reachable`

## Consumer impact note template

- changed_contract:
- consumer_team:
- behavior_change:
- compatibility_risk:
- migration_action:
