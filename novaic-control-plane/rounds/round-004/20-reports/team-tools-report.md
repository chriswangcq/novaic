# Round 004 Report - Tools Team

## Task 1
- task: Migrate remaining tools execution/policy code from monorepo tools paths into split tools repo.
- evidence:
  - command: `cd novaic-tools-server && git rev-parse HEAD && git ls-remote origin split-round-003 | awk '{print $1}'`
  - expected_marker: `c279971e82fdbad66e71394a0b24d036175fd287`
  - repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
  - default_branch: `split-round-003`
  - ruleset_or_protection_id: `none (local bare repo)`
  - required_checks: `preflight + leak probe + pytest tests/unit/tools_server/`
  - permission_model: `local file remote, single maintainer`
  - commit_sha: `c279971e82fdbad66e71394a0b24d036175fd287`
  - migrated_paths:
    - `novaic-backend/tools_server/RELIABILITY_POLICY.md` -> `novaic-tools-server/tools_server/RELIABILITY_POLICY.md`
    - `novaic-backend/tools_server/OPERATOR_RUNBOOK.md` -> `novaic-tools-server/tools_server/OPERATOR_RUNBOOK.md`
    - `novaic-backend/scripts/tools/RUNNER_SUPPORT_POLICY.md` -> `novaic-tools-server/scripts/tools/RUNNER_SUPPORT_POLICY.md`
    - `novaic-backend/tests/unit/tools_server/test_policy_doc_sync.py` -> `novaic-tools-server/tests/unit/tools_server/test_policy_doc_sync.py`
    - `novaic-backend/main_tools.py` -> `novaic-tools-server/main_tools.py`
    - `novaic-backend/tools_server/api.py` (health endpoint added) -> `novaic-tools-server/tools_server/api.py`
  - summary: PASS — local HEAD and remote `origin/split-round-003` both resolve to `c279971e82fdbad66e71394a0b24d036175fd287`. Migration commit confirmed pushed.
  - artifact_path: `novaic-control-plane/rounds/round-004/split-run/tools-round004-execution.md`
- status: DONE

## Task 2
- task: Update callers to consume split tools service endpoints/imports instead of monorepo-local module paths.
- evidence:
  - command: `python3 - <<'PY' from pathlib import Path; files={'novaic-backend/main_novaic.py':['NOVAIC_TOOLS_SERVER_SPLIT_REPO','Loading split repo entrypoint'],'novaic-backend/start_all_services.sh':['TOOLS_SPLIT_REPO','NOVAIC_TOOLS_SERVER_SPLIT_REPO'],'novaic-backend/start_all_dev.sh':['TOOLS_SPLIT_REPO','NOVAIC_TOOLS_SERVER_SPLIT_REPO']}; [(_ for t in ts for _ in [None] if t not in Path(p).read_text(encoding='utf-8') and (_ for _ in ()).throw(AssertionError(f'{t} missing in {p}'))) for p,ts in files.items()]; print('TOOLS_CALLER_SPLIT_WIRING:PASS') PY`
  - expected_marker: `TOOLS_CALLER_SPLIT_WIRING:PASS`
  - repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
  - default_branch: `split-round-003`
  - ruleset_or_protection_id: `none`
  - required_checks: `split wiring tokens present in main_novaic.py / start_all_services.sh / start_all_dev.sh`
  - permission_model: `monorepo change, no additional gate required`
  - commit_sha: `c279971e82fdbad66e71394a0b24d036175fd287`
  - migrated_paths:
    - `novaic-backend/main_novaic.py` — added `NOVAIC_TOOLS_SERVER_SPLIT_REPO` path-switch in `run_tools_server()`
    - `novaic-backend/start_all_services.sh` — added `TOOLS_SPLIT_REPO` env-var branch for split entrypoint
    - `novaic-backend/start_all_dev.sh` — same split-repo env branch for dev mode
  - summary: PASS — all three caller files contain the required split wiring tokens; verified by assertion script.
  - artifact_path: `novaic-control-plane/rounds/round-004/split-run/tools-round004-execution.md`
- status: DONE

## Task 3
- task: Run timeout/isolation tests from split tools repo root and publish PASS markers with commit evidence.
- evidence:
  - command: `cd novaic-tools-server && bash scripts/tools/ci_preflight_probe_prereqs.sh && bash scripts/tools/leak_probe.sh && pytest -q tests/unit/tools_server/ && echo "TOOLS_SPLIT_BASELINE:PASS"`
  - expected_marker: `TOOLS_SPLIT_BASELINE:PASS`
  - repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
  - default_branch: `split-round-003`
  - ruleset_or_protection_id: `none`
  - required_checks: `[probe-preflight] PASS + [leak-probe] PASS (fd delta=0) + 6 passed`
  - permission_model: `local file remote, single maintainer`
  - commit_sha: `c279971e82fdbad66e71394a0b24d036175fd287`
  - migrated_paths: `split repo root (novaic-tools-server/) — all tests run from extracted location`
  - summary: PASS — `[probe-preflight] PASS`, `[leak-probe] PASS` (fd_before=27 fd_after=27 delta=0), pytest `6 passed`.
  - artifact_path: `novaic-control-plane/rounds/round-004/split-run/tools-round004-execution.md`
- status: DONE

## Decision Needed (optional)
- issue: Tauri desktop launch path (`novaic-app/src-tauri/src/main.rs`) still hardcodes tools-server binary from monorepo. Needs `NOVAIC_TOOLS_SERVER_SPLIT_REPO` wiring added to Rust process spawn or config injection.
- options: A) Add env-var to Tauri spawn command; B) Bundle split repo binary path in `config/services.json`; C) Defer to next round.
- recommendation: Option A — minimal change to Rust spawn; inject `NOVAIC_TOOLS_SERVER_SPLIT_REPO` env var at `PORT_TOOLS_SERVER` process start.
- impact: Without this, Tauri desktop mode still uses monorepo tools module, not split repo. Tools split is effectively unused in packaged desktop build.
- owner: `Desktop Team` + `Tools Team`
- target_round: `round-005`

## Team status
- status: DONE
- blocker: none (Tauri desktop wiring gap raised as Decision Needed, tracked for round-005)
