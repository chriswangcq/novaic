# Round 003 Report - API Team

## Task 1
- task: Migrate gateway service code from monorepo into `novaic-gateway` and push the first split commit.
- evidence:
  - command:
    - `git rev-parse HEAD`
    - `git ls-remote --heads origin round-003-split`
  - expected_marker:
    - `dfebf419d0c513cec9177e3215ea7f620dce5614`
    - `refs/heads/round-003-split`
  - repo_url:
    - `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/remotes/novaic-gateway.git`
  - branch:
    - `round-003-split`
  - commit_sha:
    - `dfebf419d0c513cec9177e3215ea7f620dce5614`
  - migrated_paths:
    - `novaic-backend/gateway/api/runtime_orchestrator_forward.py -> rounds/round-003/split-move/repos/novaic-gateway/api/runtime_orchestrator_forward.py`
    - `novaic-backend/main_gateway.py (health/runtime-forward subset) -> rounds/round-003/split-move/repos/novaic-gateway/services/gateway_api.py`
    - `novaic-backend/scripts/smoke_gateway_independent_startup.sh (pattern) -> rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh`
  - summary:
    - PASS; `novaic-gateway` split repo has first migration commit and branch pushed to local remote.
  - artifact_path:
    - `rounds/round-003/split-move/repos/novaic-gateway/api/runtime_orchestrator_forward.py`
    - `rounds/round-003/split-move/repos/novaic-gateway/services/gateway_api.py`
    - `rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh`
- status: DONE

## Task 2
- task: Publish `split-move/gateway-migration-map.md` with source->target path mapping and removed/kept decisions.
- evidence:
  - command:
    - `python3 -c "from pathlib import Path; p=Path('/Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/gateway-migration-map.md'); t=p.read_text(encoding='utf-8'); ok=all(k in t for k in ['source_path','target_path','removed-from-initial-split']); print('MIGRATION_MAP_CHECK=PASS' if ok else 'MIGRATION_MAP_CHECK=FAIL')"`
  - expected_marker:
    - `MIGRATION_MAP_CHECK=PASS`
  - repo_url:
    - `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/remotes/novaic-gateway.git`
  - branch:
    - `round-003-split`
  - commit_sha:
    - `dfebf419d0c513cec9177e3215ea7f620dce5614`
  - migrated_paths:
    - `novaic-backend/gateway/api/runtime_orchestrator_forward.py -> rounds/round-003/split-move/repos/novaic-gateway/api/runtime_orchestrator_forward.py`
    - `novaic-backend/main_gateway.py (health/runtime-forward subset) -> rounds/round-003/split-move/repos/novaic-gateway/services/gateway_api.py`
  - summary:
    - PASS; migration map includes source->target mapping plus removed/kept decisions for phased split.
  - artifact_path:
    - `rounds/round-003/split-move/gateway-migration-map.md`
- status: DONE

## Task 3
- task: Run gateway independent startup/health from `novaic-gateway` repo root and record PASS markers.
- evidence:
  - command:
    - `bash rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh`
  - expected_marker:
    - `SPLIT_RUNTIME_HEALTH=PASS`
    - `SPLIT_GATEWAY_HEALTH=PASS`
    - `SPLIT_E2E_RUNTIME_FORWARD=PASS`
  - repo_url:
    - `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/remotes/novaic-gateway.git`
  - branch:
    - `round-003-split`
  - commit_sha:
    - `dfebf419d0c513cec9177e3215ea7f620dce5614`
  - migrated_paths:
    - `novaic-backend/scripts/smoke_gateway_independent_startup.sh (pattern) -> rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh`
    - `novaic-backend/gateway/api/runtime_orchestrator_forward.py -> rounds/round-003/split-move/repos/novaic-gateway/api/runtime_orchestrator_forward.py`
  - summary:
    - PASS; split repo root startup/health passes and cross-repo runtime forwarding endpoint is replayed end-to-end.
  - artifact_path:
    - `rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh`
    - `rounds/round-003/split-move/repos/novaic-gateway/services/gateway_api.py`
    - `rounds/round-003/split-move/repos/novaic-gateway/api/runtime_orchestrator_forward.py`
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
