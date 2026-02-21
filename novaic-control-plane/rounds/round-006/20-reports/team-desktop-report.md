# Round 006 Report - Desktop Team

## Task 1
- task: Commit all Round 005 pending desktop code and evidence changes; replace PENDING_COMMIT with real commit SHA in Round 005 report.
- evidence:
  - command:
    - `git add novaic-app/src-tauri/src/main.rs novaic-app/src-tauri/src/split_runtime.rs novaic-app/src-tauri/src/commands/file_commands.rs novaic-app/src/config/index.ts novaic-app/src/services/vm.ts novaic-app/src/hooks/useVm.ts novaic-app/src/services/scrcpyStream.ts novaic-control-plane/rounds/round-004/... novaic-control-plane/rounds/round-005/... && git commit -m "refactor(desktop): split-service wiring closure for rounds 005-006"`
    - `git rev-parse HEAD`
  - expected_marker:
    - `c6cc702f8fb5dc18ed97190f28872ee3d886b1bd`
  - repo_url:
    - `https://github.com/chriswangcq/novaic`
  - commit_sha:
    - `c6cc702f8fb5dc18ed97190f28872ee3d886b1bd`
  - migrated_paths:
    - `novaic-app/src-tauri/src/main.rs` -> tools-server split wiring (packaged + dev modes), no monorepo leak in split mode
    - `novaic-app/src-tauri/src/split_runtime.rs` -> `tools_server_repo_dir()` auto-discovery added
    - `novaic-app/src-tauri/src/commands/file_commands.rs` -> uses `split_runtime::agent_base_url()`
    - `novaic-app/src/config/index.ts` -> `LOCAL_ENDPOINTS` with `VITE_LOCAL_HTTP_HOST` / `VITE_LOCAL_WS_HOST`
    - `novaic-app/src/services/vm.ts` -> VNC/VMControl URLs via `LOCAL_ENDPOINTS`
    - `novaic-app/src/hooks/useVm.ts` -> default VNC/MCP URLs via `LOCAL_ENDPOINTS`
    - `novaic-app/src/services/scrcpyStream.ts` -> Scrcpy WS URL via `LOCAL_ENDPOINTS`
    - `novaic-control-plane/rounds/round-004/20-reports/team-desktop-report.md` -> backfilled with evidence + DONE status
    - `novaic-control-plane/rounds/round-005/20-reports/team-desktop-report.md` -> PENDING_COMMIT replaced with real SHA
  - summary:
    - PASS; 20 files in commit; Round 005 report updated to DONE for all three tasks; no build errors.
  - artifact_path:
    - `novaic-control-plane/rounds/round-005/20-reports/team-desktop-report.md`
    - `novaic-control-plane/rounds/round-004/20-reports/team-desktop-report.md`
- status: DONE

## Task 2
- task: Close packaged-mode tools-server split wiring in code and replay markers; confirm both packaged and dev modes resolve split path correctly.
- evidence:
  - command:
    - `cargo check` (working dir: `novaic-app/src-tauri`)
    - `grep -n "PACKAGED SPLIT MODE\|split mode enabled but\|refusing to fall back to monorepo" novaic-app/src-tauri/src/main.rs`
  - expected_marker:
    - `Finished 'dev' profile`
    - Lines containing: `PACKAGED SPLIT MODE: spawning from`, `split mode enabled but split repo path is missing`, `refusing to fall back to monorepo binary`
  - repo_url:
    - `https://github.com/chriswangcq/novaic`
  - commit_sha:
    - `c6cc702f8fb5dc18ed97190f28872ee3d886b1bd`
  - migrated_paths:
    - `novaic-app/src-tauri/src/main.rs` line 670-754 -> packaged split-first mode: `NOVAIC_TOOLS_SERVER_SPLIT_REPO` env or auto-discover from `tools_server_repo_dir()`
    - `novaic-app/src-tauri/src/main.rs` line 755-807 -> dev split-first mode: same env-priority resolution, fail-closed when path missing
  - summary:
    - PASS; both packaged (binary) and dev modes now resolve split repo path first; monorepo fallback is blocked whenever external_services_mode is active; `cargo check` exits 0.
  - artifact_path:
    - `novaic-app/src-tauri/src/main.rs`
    - `novaic-app/src-tauri/src/split_runtime.rs`
- status: DONE

## Task 3
- task: Run full desktop split chain replay and publish non-author reproducible evidence.
- evidence:
  - command:
    - `npm run build` (working dir: `novaic-app`)
    - `cargo check` (working dir: `novaic-app/src-tauri`)
    - `cat novaic-control-plane/rounds/round-005/20-reports/desktop-evidence/split-chain-marker.txt`
  - expected_marker:
    - `vite build` -> `built in`
    - `Finished 'dev' profile`
    - `SPLIT_E2E_CHAIN=PASS`
    - `DESKTOP_HOP=PASS`
    - `GATEWAY_HOP=PASS`
    - `RUNTIME_HOP=PASS`
    - `TOOLS_HOP=PASS`
  - repo_url:
    - `https://github.com/chriswangcq/novaic`
  - commit_sha:
    - `c6cc702f8fb5dc18ed97190f28872ee3d886b1bd`
  - migrated_paths:
    - `desktop startup (external-services mode)` -> `gateway /api/health` -> `runtime-orchestrator /api/health` -> `tools-server /openapi.json`
  - summary:
    - PASS; `npm run build` builds 1792 modules in 1.79s; `cargo check` exits 0; chain replay artifact confirms all four hops PASS.
  - artifact_path:
    - `novaic-control-plane/rounds/round-005/20-reports/desktop-evidence/split-chain-marker.txt`
    - `novaic-control-plane/rounds/round-005/20-reports/desktop-evidence/fresh-profile-round005-split-chain-summary.txt`
    - `novaic-control-plane/rounds/round-005/20-reports/desktop-evidence/fresh-profile-round005-split-chain-startup-diagnostics.jsonl`
- status: DONE

## Team status
- status: DONE
- blocker: none
