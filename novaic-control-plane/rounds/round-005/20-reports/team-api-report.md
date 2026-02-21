# Round 005 Report - API Team

## Task 1
- task: Remove remaining monorepo shortcut calls in gateway runtime forwarding paths and keep split endpoint-only wiring.
- evidence:
  - command:
    - `python3 -c "from pathlib import Path; txt=Path('scripts/smoke_gateway_repo_root.sh').read_text(encoding='utf-8'); print('NO_MONOREPO_SHORTCUT=PASS' if 'novaic-backend/venv' not in txt else 'NO_MONOREPO_SHORTCUT=FAIL')"`
  - expected_marker:
    - `NO_MONOREPO_SHORTCUT=PASS`
  - repo_url:
    - `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/remotes/novaic-gateway.git`
  - commit_sha:
    - `e9cad76b7a79e289344bf8745cdb04d7a50702e5`
  - migrated_paths:
    - `rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh (remove monorepo fallback and use split-repo local .venv bootstrap only)`
  - summary:
    - PASS; replay script no longer references monorepo python shortcut and keeps split endpoint wiring via `RUNTIME_ORCHESTRATOR_URL`.
  - artifact_path:
    - `rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh`
    - `rounds/round-003/split-move/repos/novaic-gateway/.gitignore`
- status: DONE

## Task 2
- task: Add one fixed replay chain for gateway -> runtime with strict PASS markers and failure exit code.
- evidence:
  - command:
    - `bash rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh`
  - expected_marker:
    - `FIXED_CHAIN_RUNTIME_HEALTH=PASS`
    - `FIXED_CHAIN_GATEWAY_HEALTH=PASS`
    - `FIXED_CHAIN_FORWARD_HEALTH=PASS`
    - `SPLIT_FIXED_RUNTIME_CHAIN=PASS`
  - repo_url:
    - `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/remotes/novaic-gateway.git`
  - commit_sha:
    - `e9cad76b7a79e289344bf8745cdb04d7a50702e5`
  - migrated_paths:
    - `rounds/round-003/split-move/repos/novaic-gateway/scripts/replay_gateway_runtime_chain.sh (new fixed chain with strict marker checks and non-zero exit on mismatch)`
    - `rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh (wire fixed chain replay)`
  - summary:
    - PASS; fixed chain now executes in deterministic order (runtime health -> gateway health -> forward health) with strict marker gating.
  - artifact_path:
    - `rounds/round-003/split-move/repos/novaic-gateway/scripts/replay_gateway_runtime_chain.sh`
    - `rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh`
- status: DONE

## Task 3
- task: Commit and verify startup/health replay from gateway split repo root.
- evidence:
  - command:
    - `git rev-parse HEAD`
    - `git ls-remote --heads origin round-003-split`
    - `bash rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh`
  - expected_marker:
    - `e9cad76b7a79e289344bf8745cdb04d7a50702e5`
    - `refs/heads/round-003-split`
    - `SPLIT_RUNTIME_HEALTH=PASS`
    - `SPLIT_GATEWAY_HEALTH=PASS`
    - `SPLIT_TOOLS_HEALTH=PASS`
    - `SPLIT_GATEWAY_STATUS_ROUTE=PASS`
    - `SPLIT_E2E_RUNTIME_FORWARD=PASS`
  - repo_url:
    - `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/remotes/novaic-gateway.git`
  - commit_sha:
    - `e9cad76b7a79e289344bf8745cdb04d7a50702e5`
  - migrated_paths:
    - `rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh`
    - `rounds/round-003/split-move/repos/novaic-gateway/scripts/replay_gateway_runtime_chain.sh`
    - `rounds/round-003/split-move/repos/novaic-gateway/.gitignore`
  - summary:
    - PASS; split repo root replay is green after Round 005 commit and remote branch head matches reported commit SHA.
  - artifact_path:
    - `rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh`
    - `/tmp/novaic-gateway-split.log`
    - `/tmp/novaic-runtime-orchestrator-split.log`
    - `/tmp/novaic-tools-server-split.log`
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
