# Round 002 Report - API Team

## Task 1
- task: Create `split-exec/gateway-repo-candidate.md` with physical extraction path map and ownership.
- evidence:
  - command:
    - `test -f novaic-control-plane/rounds/round-002/split-exec/gateway-repo-candidate.md && echo "ARTIFACT_EXISTS=PASS"`
  - expected_marker:
    - `ARTIFACT_EXISTS=PASS`
  - summary:
    - PASS; gateway candidate artifact created with extraction path map, ownership, and replay baseline markers.
  - artifact_path:
    - `novaic-control-plane/rounds/round-002/split-exec/gateway-repo-candidate.md`
- status: DONE

## Task 2
- task: Create `split-exec/api-contract-release-checklist.md` enforcing OpenAPI + consumer check before merge.
- evidence:
  - command:
    - `test -f novaic-control-plane/rounds/round-002/split-exec/api-contract-release-checklist.md && echo "ARTIFACT_EXISTS=PASS"`
    - `python3 -c "from pathlib import Path; files=['contracts/openapi/gateway-public.v1.yaml','contracts/openapi/runtime-orchestrator-internal.v1.yaml','contracts/openapi/storage-contracts.v1.yaml']; missing=[p for p in files if 'openapi: 3.1.0' not in Path(p).read_text(encoding='utf-8')]; print('OPENAPI_VERSION_CHECK=PASS' if not missing else 'OPENAPI_VERSION_CHECK=FAIL'); [print('FILE_OK='+p) for p in files if p not in missing]; import sys; sys.exit(0 if not missing else 1)"`
    - `python3 -c "from pathlib import Path; checks={'contracts/openapi/gateway-public.v1.yaml':['/health:','operationId: getGatewayHealth'],'contracts/openapi/runtime-orchestrator-internal.v1.yaml':['/internal/health:','operationId: getRuntimeOrchestratorHealth']}; bad=[]; [bad.append((p,m)) for p,ms in checks.items() for m in ms if m not in Path(p).read_text(encoding='utf-8')]; ok=not bad; print('INTERFACE_MARKER_CHECK=PASS' if ok else 'INTERFACE_MARKER_CHECK=FAIL'); [print('FILE_OK='+p) for p in checks]; [print('MARKER_OK='+m) for p,ms in checks.items() for m in ms if (p,m) not in bad]; import sys; sys.exit(0 if ok else 1)"`
  - expected_marker:
    - `ARTIFACT_EXISTS=PASS`
    - `OPENAPI_VERSION_CHECK=PASS`
    - `INTERFACE_MARKER_CHECK=PASS`
  - summary:
    - PASS; checklist artifact created and replay commands verified against current contract files.
  - artifact_path:
    - `novaic-control-plane/rounds/round-002/split-exec/api-contract-release-checklist.md`
    - `contracts/openapi/gateway-public.v1.yaml`
    - `contracts/openapi/runtime-orchestrator-internal.v1.yaml`
    - `contracts/openapi/storage-contracts.v1.yaml`
- status: DONE

## Task 3
- task: Run gateway startup/health replay check from candidate layout and record baseline.
- evidence:
  - command:
    - `bash novaic-backend/scripts/smoke_gateway_independent_startup.sh`
  - expected_marker:
    - `PASS: startup smoke base 61900`
    - `PASS: runtime-orchestrator healthy on 61993`
    - `PASS: gateway healthy on 61999`
    - `PASS: gateway API root reachable`
  - summary:
    - PASS; startup/health replay baseline is green and reproducible using non-author script command.
  - artifact_path:
    - `novaic-backend/scripts/smoke_gateway_independent_startup.sh`
    - `novaic-control-plane/rounds/round-002/split-exec/gateway-repo-candidate.md`
- status: DONE

## Decision Needed (optional)
- issue: none
- options: n/a
- recommendation: n/a
- impact: n/a
- owner: n/a
- target_round: n/a

## Team status
- status: DONE
- blocker: none
