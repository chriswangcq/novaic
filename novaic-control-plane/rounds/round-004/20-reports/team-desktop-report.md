# Round 004 Report - Desktop Team

## Task 1
- task: Refactor desktop runtime startup to default to split-service endpoint resolution in non-dev mode, removing monorepo-only fallback assumptions.
- evidence:
  - command:
    - `cargo check` (working dir: `novaic-app/src-tauri`)
    - `npm run build` (working dir: `novaic-app`)
  - expected_marker:
    - `Finished 'dev' profile`
    - `built in`
  - repo_url:
    - `git@github.com:chriswangcq/novaic.git`
  - default_branch:
    - `main`
  - ruleset_or_protection_id:
    - `LOCAL_ONLY_NO_GITHUB_RULESET`
  - required_checks:
    - `cargo-check`
    - `npm-build`
  - permission_model:
    - `local-maintainer-only`
  - summary:
    - PASS; desktop startup path in release/non-dev mode runs split-first external-services probe instead of monorepo local bootstrap path.
  - artifact_path:
    - `novaic-app/src-tauri/src/split_runtime.rs`
    - `novaic-app/src-tauri/src/main.rs`
- status: DONE

## Task 2
- task: Replace hardcoded internal API paths in desktop command/service modules with configurable split-service base URLs.
- evidence:
  - command:
    - `cargo check` (working dir: `novaic-app/src-tauri`)
    - `npm run build` (working dir: `novaic-app`)
  - expected_marker:
    - `Finished 'dev' profile`
    - `built in`
  - repo_url:
    - `git@github.com:chriswangcq/novaic.git`
  - default_branch:
    - `main`
  - ruleset_or_protection_id:
    - `LOCAL_ONLY_NO_GITHUB_RULESET`
  - required_checks:
    - `cargo-check`
    - `npm-build`
  - permission_model:
    - `local-maintainer-only`
  - summary:
    - PASS; desktop command/service modules removed hardcoded host assumptions and now use centralized split-service endpoint resolution.
  - artifact_path:
    - `novaic-app/src/services/vm.ts`
    - `novaic-app/src/hooks/useVm.ts`
    - `novaic-app/src/services/scrcpyStream.ts`
    - `novaic-app/src/config/index.ts`
    - `novaic-app/src-tauri/src/commands/file_commands.rs`
- status: DONE

## Task 3
- task: Run desktop startup against split services and publish one end-to-end PASS marker with commit evidence.
- evidence:
  - command:
    - `npm run tauri:build` (working dir: `novaic-app`)
    - `NOVAIC_GATEWAY_URL="http://127.0.0.1:63999" ROUND_DIR="/Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-004" RUN_LABEL="round004-split-default" OPERATOR_ID="team-desktop" WAIT_SECONDS=20 bash "/Users/wangchaoqun/novaic/novaic-app/scripts/validate_fresh_profile.sh"`
  - expected_marker:
    - `SPLIT_E2E_GATEWAY_HEALTH=PASS`
    - `error_timeout_count=0`
    - `stages=app-bootstrap,external-services`
  - repo_url:
    - `git@github.com:chriswangcq/novaic.git`
  - default_branch:
    - `main`
  - ruleset_or_protection_id:
    - `LOCAL_ONLY_NO_GITHUB_RULESET`
  - required_checks:
    - `tauri-build`
    - `desktop-split-default-replay`
  - permission_model:
    - `local-maintainer-only`
  - summary:
    - PASS; desktop external-services startup replay succeeded against split gateway endpoint with E2E marker.
  - artifact_path:
    - `novaic-control-plane/rounds/round-004/20-reports/desktop-evidence/split-default-e2e-marker.txt`
    - `novaic-control-plane/rounds/round-004/20-reports/desktop-evidence/fresh-profile-round004-split-default-summary.txt`
    - `novaic-control-plane/rounds/round-004/20-reports/desktop-evidence/fresh-profile-round004-split-default-startup-diagnostics.jsonl`
    - `novaic-control-plane/rounds/round-004/20-reports/desktop-evidence/fresh-profile-round004-split-default-metadata.txt`
- status: DONE

## Decision Needed (optional)
- issue: none
- options: n/a
- recommendation: n/a
- impact: none
- owner: n/a
- target_round: n/a

## Team status
- status: DONE
- blocker: none
