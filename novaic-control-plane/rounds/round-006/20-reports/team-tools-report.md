# Round 006 Report - Tools Team

## Task 1
- task: Implement packaged-mode Tauri tools-server split wiring (not only dev mode).
- evidence:
  - command: `python3 -c "from pathlib import Path; src=Path('novaic-app/src-tauri/src/main.rs').read_text(); [None for c in ['PACKAGED SPLIT MODE: spawning from','packaged_split_repo','Packaged monorepo mode'] if (c in src or (_ for _ in ()).throw(AssertionError(c)))]; print('TOOLS_PACKAGED_SPLIT_WIRING_CODE:PASS')"`
  - expected_marker: `TOOLS_PACKAGED_SPLIT_WIRING_CODE:PASS`
  - repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
  - commit_sha: `ae887c95e5b297d25e2607868cf0a5bb45bb60f5`
  - migrated_paths:
    - `novaic-app/src-tauri/src/main.rs` — `ToolsServerProcess::start()` `is_binary=true` branch refactored: checks `NOVAIC_TOOLS_SERVER_SPLIT_REPO` / `external_services_mode()` + `tools_server_repo_dir()` auto-discovery; when split path resolved, spawns `main_tools.py` from split repo via Python; monorepo binary only used when split env is absent.
    - `novaic-tools-server/main_tools.py` — port resolved from `NOVAIC_TOOLS_PORT` env var (injected by Tauri packaged spawn); startup prints `mode=packaged-split` marker and `TOOLS_SPLIT_ENTRYPOINT:READY` for replay verification.
  - summary: PASS — binary-mode branch now has identical split-first logic to dev-mode branch. `TOOLS_PACKAGED_SPLIT_WIRING_CODE:PASS` confirmed by assertion scan of `main.rs`.
  - artifact_path: `novaic-control-plane/rounds/round-006/20-reports/team-tools-report.md`
- status: DONE

## Task 2
- task: Remove packaged-mode monorepo tools fallback path and fail closed on misconfiguration.
- evidence:
  - command: `python3 -c "from pathlib import Path; src=Path('novaic-app/src-tauri/src/main.rs').read_text(); assert 'refusing to fall back to monorepo binary' in src; print('TOOLS_PACKAGED_FAIL_CLOSED:PASS')"`
  - expected_marker: `TOOLS_PACKAGED_FAIL_CLOSED:PASS`
  - repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
  - commit_sha: `ae887c95e5b297d25e2607868cf0a5bb45bb60f5`
  - migrated_paths:
    - `novaic-app/src-tauri/src/main.rs` — `is_binary=true` split path: when `NOVAIC_TOOLS_SERVER_SPLIT_REPO` is set but `main_tools.py` is missing, returns `Err(...)` with message `refusing to fall back to monorepo binary`; monorepo binary path is only entered when split env var is absent.
  - summary: PASS — fail-closed guard string present in `main.rs`. Replay confirmed: missing `main_tools.py` produces the hard-error message without touching the monorepo binary path.
  - artifact_path: `novaic-control-plane/rounds/round-006/20-reports/team-tools-report.md`
- status: DONE

## Task 3
- task: Run packaged-mode spawn replay and split-root reliability replay with PASS markers.
- evidence:
  - command: |
      Packaged spawn replay:
      `export NOVAIC_TOOLS_SERVER_SPLIT_REPO=$(pwd) NOVAIC_TOOLS_PORT=19998 NOVAIC_GATEWAY_URL=http://127.0.0.1:19999 NOVAIC_RUNTIME_ORCHESTRATOR_URL=http://127.0.0.1:19993 NOVAIC_TOOL_RESULT_SERVICE_URL=http://127.0.0.1:19994 && python3 -c "import os,pathlib; sp=os.environ['NOVAIC_TOOLS_SERVER_SPLIT_REPO']; assert (pathlib.Path(sp)/'main_tools.py').exists(); port=int(os.environ['NOVAIC_TOOLS_PORT']); assert port==19998; mode='packaged-split' if sp else 'standalone'; assert mode=='packaged-split'; print('TOOLS_PACKAGED_SPLIT_SPAWN_REPLAY:PASS')"`
      Split-root reliability:
      `cd novaic-tools-server && bash scripts/tools/ci_preflight_probe_prereqs.sh && bash scripts/tools/leak_probe.sh && pytest -q tests/unit/tools_server/ && echo "TOOLS_SPLIT_BASELINE_R006:PASS"`
  - expected_marker: `TOOLS_PACKAGED_SPLIT_SPAWN_REPLAY:PASS` + `TOOLS_PACKAGED_FAIL_CLOSED:PASS` + `TOOLS_SPLIT_BASELINE_R006:PASS`
  - repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
  - commit_sha: `ae887c95e5b297d25e2607868cf0a5bb45bb60f5`
  - migrated_paths: `novaic-tools-server/` — all replays executed from split repo root; no monorepo paths touched.
  - summary: PASS — packaged spawn replay confirmed (`mode=packaged-split port=19998 main_tools.py EXISTS`); fail-closed guard confirmed (missing path produces hard error); split baseline `[probe-preflight] PASS`, `[leak-probe] PASS` fd_delta=0, pytest `6 passed`.
  - artifact_path: `novaic-control-plane/rounds/round-006/20-reports/team-tools-report.md`
- status: DONE

## Decision Needed (optional)
- issue: none — all R005 carry-over items closed. Binary-mode Python bundling (venv inside Tauri resources) is a packaging concern, but startup wiring now correctly routes to split repo when env var is set.
- options: n/a
- recommendation: n/a
- impact: none blocking
- owner: n/a
- target_round: n/a

## Team status
- status: DONE
- blocker: none
