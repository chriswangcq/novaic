# Round 006 Runtime Replay Artifact

## Split repo

- repo_url: `file:///Users/wangchaoqun/split-remotes/novaic-runtime-orchestrator.git`
- branch: `split/round-003-runtime`
- commit_sha: `f338decc9b3222cebd88c37a490179c77e739b6e`
- working_copy: `/Users/wangchaoqun/novaic-runtime-orchestrator`

## Replay commands and output

### 1) Lifecycle contract guard

- command: `cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_contract_guard_replay.sh`
- output:
  ```
  PASS: runtime lifecycle contract guard replay
  PASS: contract runtime_id rt-2f161e1aacd9
  ```
- status: PASS

### 2) Startup health replay

- command: `cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_startup_health_replay.sh`
- output:
  ```
  PASS: runtime-orchestrator startup from split repo root
  PASS: runtime health endpoint http://127.0.0.1:62993/api/health
  ```
- status: PASS

### 3) Contract test suite

- command: `cd /Users/wangchaoqun/novaic-runtime-orchestrator && pytest -q tests/contract/test_runtime_orchestrator_process_startup.py tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
- output: `6 passed, 2 skipped`
- status: PASS

## Regression check

- Desktop/Tools packaged-mode updates this round do not affect runtime split repo.
- Runtime split repo has no dependency on tauri packaged-mode, tools runner, or desktop bundle paths.
- All lifecycle contract endpoints (`/api/health`, `/internal/health`, `/internal/runtimes/get-or-create`, `/internal/runtimes/{id}/set-status`, `/internal/runtimes/{id}/wake`, `/internal/runtimes/list`) are stable with no breakage.
