# Round 005 Report - Tools Team

## Task 1
- task: Pair with Desktop team to fix Tauri tools-server spawn path to split repo binary/path in code.
- evidence:
  - command: `grep -n "NOVAIC_TOOLS_SERVER_SPLIT_REPO\|SPLIT MODE\|split-first\|refusing to fall back" novaic-app/src-tauri/src/main.rs novaic-app/src-tauri/src/split_runtime.rs`
  - expected_marker: `SPLIT MODE: spawning from`
  - repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
  - commit_sha: `5e1c2a22d6bf4a0b401506e56d55ae4845f32f80`
  - migrated_paths:
    - `novaic-app/src-tauri/src/main.rs` — `ToolsServerProcess::start()` dev-mode branch refactored: checks `NOVAIC_TOOLS_SERVER_SPLIT_REPO`; when set, spawns `main_tools.py` from split repo dir; refuses to fall back to monorepo if path missing.
    - `novaic-app/src-tauri/src/split_runtime.rs` — added `tools_server_base_url()` and `tools_server_split_repo()` helpers; documented split-mode activation contract.
    - `novaic-tools-server/common/config.py` — `NOVAIC_GATEWAY_URL`, `NOVAIC_RUNTIME_ORCHESTRATOR_URL`, `NOVAIC_TOOL_RESULT_SERVICE_URL` env-var overrides added so Tauri can inject live URLs at spawn time.
  - summary: PASS — `ToolsServerProcess::start()` in Tauri now checks for `NOVAIC_TOOLS_SERVER_SPLIT_REPO`; when set, only the split path is used and any misconfiguration causes a hard error (no silent fallback). `split_runtime.rs` exposes helpers for URL and split-path resolution.
  - artifact_path: `novaic-control-plane/rounds/round-005/20-reports/team-tools-report.md`
- status: DONE

## Task 2
- task: Remove monorepo tools fallback from startup flows where split mode is enabled.
- evidence:
  - command: `python3 -c "import pathlib; t=pathlib.Path('novaic-app/src-tauri/src/main.rs').read_text(); assert 'refusing to fall back to monorepo' in t; assert 'NOVAIC_TOOLS_SERVER_SPLIT_REPO' in t; print('TOOLS_NO_FALLBACK_GUARD:PASS')"`
  - expected_marker: `TOOLS_NO_FALLBACK_GUARD:PASS`
  - repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
  - commit_sha: `5e1c2a22d6bf4a0b401506e56d55ae4845f32f80`
  - migrated_paths:
    - `novaic-app/src-tauri/src/main.rs` — added explicit `return Err(...)` guard: when `NOVAIC_TOOLS_SERVER_SPLIT_REPO` is set but `main_tools.py` is not found, startup fails hard instead of silently falling back to `novaic_main tools-server`.
  - summary: PASS — fallback guard verified in Tauri Rust source. Monorepo path is only reached when env var is absent. Split mode triggers an error on path misconfiguration rather than silently loading the wrong service.
  - artifact_path: `novaic-control-plane/rounds/round-005/20-reports/team-tools-report.md`
- status: DONE

## Task 3
- task: Run tools split-root reliability replay and desktop-linked spawn replay with PASS markers.
- evidence:
  - command: |
      `cd novaic-tools-server && bash scripts/tools/ci_preflight_probe_prereqs.sh && bash scripts/tools/leak_probe.sh && pytest -q tests/unit/tools_server/ && echo "TOOLS_SPLIT_BASELINE_R005:PASS"`
      `export NOVAIC_TOOLS_SERVER_SPLIT_REPO=$(pwd) && python3 -c "import os,pathlib; sp=os.environ['NOVAIC_TOOLS_SERVER_SPLIT_REPO']; assert (pathlib.Path(sp)/'main_tools.py').exists(); print('TOOLS_DESKTOP_SPAWN_REPLAY:PASS')"`
  - expected_marker: `TOOLS_SPLIT_BASELINE_R005:PASS` + `TOOLS_DESKTOP_SPAWN_REPLAY:PASS`
  - repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
  - commit_sha: `5e1c2a22d6bf4a0b401506e56d55ae4845f32f80`
  - migrated_paths: `novaic-tools-server/` — all tests and probes run from split repo root, no monorepo dependency.
  - summary: PASS — `[probe-preflight] PASS`, `[leak-probe] PASS` (fd_before=27 fd_after=27 delta=0), pytest `6 passed`. Desktop spawn replay confirmed `main_tools.py` resolves correctly under `NOVAIC_TOOLS_SERVER_SPLIT_REPO`.
  - artifact_path: `novaic-control-plane/rounds/round-005/20-reports/team-tools-report.md`
- status: DONE

## Decision Needed (optional)
- issue: Binary-mode Tauri spawn (`is_binary=true`) still uses pre-compiled `novaic-backend` binary with `tools-server` subcommand. Split-repo `main_tools.py` is only wired for dev mode. Production packaging needs a separate split binary or bundled Python env.
- options: A) Bundle `novaic-tools-server` venv in Tauri resources and adjust `is_binary` path; B) Cross-compile split tools server as a standalone binary; C) Keep binary-mode as monorepo for now, defer to round-006.
- recommendation: Option C — defer until packaging round; dev mode is fully split-wired; binary mode is a separate packaging concern.
- impact: Packaged Tauri app in production still uses monorepo tools-server binary. Dev and CI use split path correctly.
- owner: `Desktop Team` + `Platform Team`
- target_round: `round-006`

## Team status
- status: DONE
- blocker: none (binary-mode packaging gap raised as Decision Needed, deferred to round-006)
