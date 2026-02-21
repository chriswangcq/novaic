# Round 004 Report - Platform Team

## Task 1
- task: Migrate shared/common runtime modules that are duplicated across split repos into one shared package and update imports in split repos.
- evidence:
  - command: `python3 -c "from pathlib import Path; import subprocess; root=Path('novaic-control-plane/rounds/round-003/split-move/repos'); files=[root/'novaic-runtime-orchestrator/runtime_orchestrator/main.py',root/'novaic-tools-server/tools_server/main.py',root/'novaic-gateway/services/health_routes.py',root/'novaic-gateway/config/service_config.py']; assert all('shared_runtime_common' in p.read_text(encoding='utf-8') for p in files); shas=[subprocess.check_output(['git','-C',str(root/r),'rev-parse','HEAD'],text=True).strip() for r in ['novaic-shared-runtime-common','novaic-gateway','novaic-runtime-orchestrator','novaic-tools-server']]; print('ROUND004_SHARED_COMMON_MIGRATION_PASS', ','.join(shas))"`
  - expected_marker: `ROUND004_SHARED_COMMON_MIGRATION_PASS`
  - repo_url: `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos`
  - default_branch: `main`
  - ruleset_or_protection_id: `BRANCH_PROTECTION_BASELINE.md (local split repo)`
  - required_checks: `repo smoke + startup health + shared import check`
  - permission_model: `CODEOWNERS in split repos (@platform-team with runtime/tools owners)`
  - commit_sha: `8b18c023533e7afbdc974a4886af62538c136456,282f59fff8747e4b586f6395f65cce1b0a26ca5a,b5b1b415883dbe74dc5e4f518dea06a8bbbdae5d,194bb8b46b7f05181ca7dadc71664b92c0c3f6c3`
  - migrated_paths: `novaic-runtime-orchestrator/runtime_orchestrator/main.py -> novaic-shared-runtime-common/shared_runtime_common/service_runtime.py; novaic-tools-server/tools_server/main.py -> novaic-shared-runtime-common/shared_runtime_common/service_runtime.py; novaic-gateway/services/health_routes.py -> novaic-shared-runtime-common/shared_runtime_common/service_runtime.py; novaic-gateway/config/service_config.py -> novaic-shared-runtime-common/shared_runtime_common/service_runtime.py`
  - summary: PASS - shared helpers extracted to dedicated package and split repos switched to shared imports.
  - artifact_path: `novaic-control-plane/rounds/round-004/split-prod/shared-runtime-common-migration.md`
- status: DONE

## Task 2
- task: Remove monorepo-only path assumptions from startup scripts used by split repos.
- evidence:
  - command: `bash "novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh"`
  - expected_marker: `SPLIT_E2E_RUNTIME_FORWARD=PASS`
  - repo_url: `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway`
  - default_branch: `main`
  - ruleset_or_protection_id: `BRANCH_PROTECTION_BASELINE.md (local split repo)`
  - required_checks: `SPLIT_RUNTIME_HEALTH=PASS,SPLIT_GATEWAY_HEALTH=PASS,SPLIT_TOOLS_HEALTH=PASS`
  - permission_model: `CODEOWNERS + split repo branch baseline`
  - commit_sha: `282f59fff8747e4b586f6395f65cce1b0a26ca5a`
  - migrated_paths: `novaic-gateway/scripts/smoke_gateway_repo_root.sh (monorepo python/path assumptions) -> novaic-gateway/scripts/smoke_gateway_repo_root.sh (split-compatible dependency-aware startup)`
  - summary: PASS - startup script no longer hard-requires monorepo root and validates runtime/gateway/tools health from split repos.
  - artifact_path: `novaic-control-plane/rounds/round-004/split-prod/startup-path-assumptions-fix.md`
- status: DONE

## Task 3
- task: Run one multi-repo bring-up command that starts gateway + runtime + tools via split repos and record PASS marker.
- evidence:
  - command: `bash "novaic-control-plane/rounds/round-004/split-prod/bringup_gateway_runtime_tools.sh"`
  - expected_marker: `ROUND004_MULTI_REPO_BRINGUP_PASS`
  - repo_url: `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos`
  - default_branch: `main`
  - ruleset_or_protection_id: `BRANCH_PROTECTION_BASELINE.md (local split repos)`
  - required_checks: `runtime health + gateway health + tools health + runtime-forward path`
  - permission_model: `CODEOWNERS enforced per split repo`
  - commit_sha: `282f59fff8747e4b586f6395f65cce1b0a26ca5a,b5b1b415883dbe74dc5e4f518dea06a8bbbdae5d,194bb8b46b7f05181ca7dadc71664b92c0c3f6c3,8b18c023533e7afbdc974a4886af62538c136456`
  - migrated_paths: `novaic-gateway/services/gateway_api.py -> runtime endpoint via split URL; novaic-runtime-orchestrator/runtime_orchestrator/main.py -> split startup entrypoint; novaic-tools-server/tools_server/main.py -> split startup entrypoint; shared_runtime_common/service_runtime.py -> common runtime helpers`
  - summary: PASS - one command starts three split repos and verifies cross-repo runtime forward path.
  - artifact_path: `novaic-control-plane/rounds/round-004/split-prod/multi-repo-bringup.md`
- status: DONE

## Decision Needed (optional)
- issue:
- options:
- recommendation:
- impact:
- owner:
- target_round:

## Team status
- status: DONE
- blocker: none
