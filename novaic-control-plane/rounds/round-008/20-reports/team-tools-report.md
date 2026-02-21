# Round 008 Report - Tools Team

---

## Task 1 — code/behavior: Typed preflight checks for packaged-mode spawn

- task: `Harden packaged-mode spawn with explicit preflight checks for split path and required env, returning typed PreflightResult errors before uvicorn starts.`
- problem_fixed: `main_tools.py had no pre-start validation; a misconfigured Tauri spawn produced an ungreppable Python traceback instead of a typed diagnostic. Non-authors could not distinguish startup failure from configuration error.`
- solution_applied: `Extracted tools_server/preflight.py with PreflightResult dataclass and preflight_check() covering SPLIT_PATH_MISSING / MAIN_TOOLS_MISSING / GATEWAY_URL_MISSING error codes. Module has zero uvicorn/FastAPI imports. main_tools.py now calls preflight_check() and exits 1 printing TOOLS_PREFLIGHT_FAIL_CLOSED:PASS on failure.`
- target_state_proof: `preflight_check() returns ok=True with marker TOOLS_PREFLIGHT:PASS mode=packaged-split port=19998 when all env vars are valid.`
- evidence:
  - command: `python3 -c "import sys,os; sys.path.insert(0,'novaic-tools-server'); os.environ.update({'NOVAIC_TOOLS_SERVER_SPLIT_REPO':'novaic-tools-server','NOVAIC_TOOLS_PORT':'19998','NOVAIC_GATEWAY_URL':'http://127.0.0.1:19999'}); from tools_server.preflight import preflight_check; r=preflight_check(); assert r.ok and r.marker=='TOOLS_PREFLIGHT:PASS mode=packaged-split port=19998',repr(r); print(r.marker)"`
  - expected_marker: `TOOLS_PREFLIGHT:PASS mode=packaged-split port=19998`
  - repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
  - commit_sha: `33b4ea26b818a2705b49b6dbb727d3d9663f7c32`
  - migrated_paths: `novaic-tools-server/tools_server/preflight.py` (new), `novaic-tools-server/main_tools.py` (updated)
  - summary: `PASS — command output matches expected_marker exactly.`
  - artifact_path: `novaic-tools-server/tools_server/preflight.py`
- status: DONE

---

## Task 2 — failure-path: Packaged-mode fail-closed replay with non-zero exit

- task: `Run packaged-mode spawn replay with intentionally missing split path; verify TOOLS_PREFLIGHT_ERROR:SPLIT_PATH_MISSING typed error and TOOLS_PREFLIGHT_ERROR_SPLIT_PATH:PASS confirmation marker.`
- problem_fixed: `No prior round verified fail-closed behavior with a greppable terminal marker. Teams had to read Rust source to confirm the guard existed. Non-author replay was impossible.`
- solution_applied: `preflight_check() returns PreflightResult(ok=False, error='[preflight] TOOLS_PREFLIGHT_ERROR:SPLIT_PATH_MISSING ...') when the split repo path does not exist. main_tools.py prints TOOLS_PREFLIGHT_FAIL_CLOSED:PASS and exits 1. All three failure codes are deterministic and greppable.`
- target_state_proof: `preflight_check() with NOVAIC_TOOLS_SERVER_SPLIT_REPO=/nonexistent returns ok=False and error containing TOOLS_PREFLIGHT_ERROR:SPLIT_PATH_MISSING.`
- evidence:
  - command: `python3 -c "import sys,os; sys.path.insert(0,'novaic-tools-server'); os.environ.update({'NOVAIC_TOOLS_SERVER_SPLIT_REPO':'/nonexistent','NOVAIC_TOOLS_PORT':'19998','NOVAIC_GATEWAY_URL':'http://127.0.0.1:19999'}); from tools_server.preflight import preflight_check; r=preflight_check(); assert not r.ok; assert 'TOOLS_PREFLIGHT_ERROR:SPLIT_PATH_MISSING' in r.error; print('TOOLS_PREFLIGHT_ERROR_SPLIT_PATH:PASS')"`
  - expected_marker: `TOOLS_PREFLIGHT_ERROR_SPLIT_PATH:PASS`
  - repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
  - commit_sha: `33b4ea26b818a2705b49b6dbb727d3d9663f7c32`
  - migrated_paths: `novaic-tools-server/tools_server/preflight.py`
  - summary: `PASS — command exits 0 only after assertions pass; TOOLS_PREFLIGHT_ERROR:SPLIT_PATH_MISSING confirmed in error field.`
  - artifact_path: `novaic-tools-server/tools_server/preflight.py`
- status: DONE

---

## Task 3 — operability artifact: Packaged/dev diagnostic runbook with marker matrix

- task: `Publish novaic-tools-server/docs/packaged-runbook.md containing step-by-step diagnostic replay, failure-path verification, split-root baseline, and full marker matrix.`
- problem_fixed: `No single non-author-reproducible reference existed for diagnosing split-mode startup failures. Marker meanings were scattered across round reports.`
- solution_applied: `Created docs/packaged-runbook.md with: 3-step diagnostic flow (preflight / failure-path / baseline), 9-entry marker matrix, failure-to-fix mapping table. Committed in R008 commit.`
- target_state_proof: `docs/packaged-runbook.md exists and contains all required markers.`
- evidence:
  - command: `python3 -c "from pathlib import Path; d=Path('novaic-tools-server/docs/packaged-runbook.md').read_text(); assert all(m in d for m in ['TOOLS_PREFLIGHT:PASS','TOOLS_PREFLIGHT_ERROR:SPLIT_PATH_MISSING','TOOLS_PREFLIGHT_FAIL_CLOSED:PASS','TOOLS_SPLIT_BASELINE:PASS']); print('TOOLS_RUNBOOK_COMPLETE:PASS')"`
  - expected_marker: `TOOLS_RUNBOOK_COMPLETE:PASS`
  - repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
  - commit_sha: `33b4ea26b818a2705b49b6dbb727d3d9663f7c32`
  - migrated_paths: `novaic-tools-server/docs/packaged-runbook.md` (new)
  - summary: `PASS — all 4 required markers confirmed present in runbook.`
  - artifact_path: `novaic-tools-server/docs/packaged-runbook.md`
- status: DONE

---

## Split-root reliability baseline

- command: `bash novaic-tools-server/scripts/tools/ci_preflight_probe_prereqs.sh 2>/dev/null | grep -c PASS && pytest -q novaic-tools-server/tests/unit/tools_server/ 2>&1 | grep passed && echo TOOLS_SPLIT_BASELINE_R008:PASS`
- expected_marker: `TOOLS_SPLIT_BASELINE_R008:PASS`
- repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
- commit_sha: `33b4ea26b818a2705b49b6dbb727d3d9663f7c32`
- status: DONE

---

## Questions For Program Owner

- question: `Should NOVAIC_RUNTIME_ORCHESTRATOR_URL and NOVAIC_TOOL_RESULT_SERVICE_URL also be required env vars in packaged-split preflight, or are they optional (graceful degradation allowed)?`
- why_blocking: `If required, preflight must add RUNTIME_ORCHESTRATOR_URL_MISSING and TOOL_RESULT_SERVICE_URL_MISSING error codes. If optional, current implementation is complete.`
- options: `A) Add both as required (hard fail on absence). B) Keep current — only NOVAIC_GATEWAY_URL required, others degrade gracefully. C) Make required/optional configurable via env flag.`
- recommended_option: `B — runtime orchestrator and TRS are call-time dependencies, not startup dependencies.`
- impact_if_unanswered: `Preflight stays as implemented (option B); can be hardened in round-009 if policy changes.`
- requested_by_round: `round-009`

## Team status
- status: DONE
- blocker: none

## Team status
- status: DONE
- blocker: none
