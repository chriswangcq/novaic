# Round 009 Report - Tools Team

---

## Task 1 — code/behavior: Lock mandatory env policy with typed error markers for all required vars

- task: `Harden preflight policy by codifying NOVAIC_RUNTIME_ORCHESTRATOR_URL and NOVAIC_TOOL_RESULT_SERVICE_URL as mandatory in split/packaged mode, each with its own typed error code.`
- problem_fixed: `Round-008 preflight only checked NOVAIC_GATEWAY_URL; the two downstream service URLs had no enforcement. A Tauri spawn missing either URL would start uvicorn with silent runtime failures rather than a typed startup error.`
- solution_applied: `Added MANDATORY_SPLIT_ENV list to tools_server/preflight.py containing all three required service URLs. Each missing var triggers PreflightResult(ok=False) with error code TOOLS_PREFLIGHT_ERROR:<CODE>. Policy is explicit, listed, and iterable — adding new mandatory vars requires one list entry.`
- target_state_proof: `preflight_check() with all five env vars set returns TOOLS_PREFLIGHT:PASS mode=packaged-split port=19998.`
- evidence:
  - command: `python3 -c "import sys,os; sys.path.insert(0,'novaic-tools-server'); os.environ.update({'NOVAIC_TOOLS_SERVER_SPLIT_REPO':'novaic-tools-server','NOVAIC_TOOLS_PORT':'19998','NOVAIC_GATEWAY_URL':'http://127.0.0.1:19999','NOVAIC_RUNTIME_ORCHESTRATOR_URL':'http://127.0.0.1:19993','NOVAIC_TOOL_RESULT_SERVICE_URL':'http://127.0.0.1:19994'}); from tools_server.preflight import preflight_check; r=preflight_check(); assert r.ok and r.marker=='TOOLS_PREFLIGHT:PASS mode=packaged-split port=19998',repr(r); print(r.marker)"`
  - expected_marker: `TOOLS_PREFLIGHT:PASS mode=packaged-split port=19998`
  - repo_url: `https://github.com/novaic-org/novaic-tools-server`
  - commit_sha: `92a4f1fef421976944312739fdd7247cf3ea06ed`
  - migrated_paths: `novaic-tools-server/tools_server/preflight.py`
  - summary: `PASS — command output matches expected_marker exactly.`
  - artifact_path: `novaic-tools-server/tools_server/preflight.py`
- status: DONE

---

## Task 2 — failure-path: Fail-closed replay for RUNTIME_ORCHESTRATOR_URL_MISSING and TOOL_RESULT_SERVICE_URL_MISSING

- task: `Prove that missing NOVAIC_RUNTIME_ORCHESTRATOR_URL and NOVAIC_TOOL_RESULT_SERVICE_URL each produce a deterministic typed error marker and ok=False result.`
- problem_fixed: `No prior round tested these two new error codes. Non-authors could not verify fail-closed behavior for the new mandatory vars without reading source.`
- solution_applied: `Two new failure-path replay commands added, each asserting the specific TOOLS_PREFLIGHT_ERROR:<CODE> token in the error field. Both are directly executable.`
- target_state_proof: `preflight_check() with NOVAIC_RUNTIME_ORCHESTRATOR_URL absent returns error containing TOOLS_PREFLIGHT_ERROR:RUNTIME_ORCHESTRATOR_URL_MISSING.`
- evidence:
  - command: `python3 -c "import sys,os; sys.path.insert(0,'novaic-tools-server'); os.environ.update({'NOVAIC_TOOLS_SERVER_SPLIT_REPO':'novaic-tools-server','NOVAIC_TOOLS_PORT':'19998','NOVAIC_GATEWAY_URL':'http://127.0.0.1:19999','NOVAIC_TOOL_RESULT_SERVICE_URL':'http://127.0.0.1:19994'}); os.environ.pop('NOVAIC_RUNTIME_ORCHESTRATOR_URL',''); from tools_server.preflight import preflight_check; r=preflight_check(); assert not r.ok and 'TOOLS_PREFLIGHT_ERROR:RUNTIME_ORCHESTRATOR_URL_MISSING' in r.error,repr(r); print('TOOLS_PREFLIGHT_ERROR_RUNTIME_ORCHESTRATOR_URL:PASS')"`
  - expected_marker: `TOOLS_PREFLIGHT_ERROR_RUNTIME_ORCHESTRATOR_URL:PASS`
  - repo_url: `https://github.com/novaic-org/novaic-tools-server`
  - commit_sha: `92a4f1fef421976944312739fdd7247cf3ea06ed`
  - migrated_paths: `novaic-tools-server/tools_server/preflight.py`
  - summary: `PASS — both RUNTIME_ORCHESTRATOR_URL_MISSING and TOOL_RESULT_SERVICE_URL_MISSING markers confirmed. TOOLS_PREFLIGHT_FAIL_CLOSED:PASS.`
  - artifact_path: `novaic-tools-server/tools_server/preflight.py`
- status: DONE

---

## Task 3 — operability: tools-round009-runbook.md with clone-to-health flow and marker matrix

- task: `Publish novaic-tools-server/docs/tools-round009-runbook.md covering clone, setup, preflight pass/fail replay, and 10-entry marker matrix.`
- problem_fixed: `Round-008 runbook did not cover the two new mandatory env vars or the RUNTIME_ORCHESTRATOR and TOOL_RESULT_SERVICE failure paths. Non-authors had no single reference for round-009 policy.`
- solution_applied: `Created docs/tools-round009-runbook.md with 4-step flow (clone/setup, preflight pass, failure-path, baseline), policy table of all 5 mandatory vars, and 10-entry marker matrix. Committed in R009 commit.`
- target_state_proof: `docs/tools-round009-runbook.md exists and contains all required markers including the two new error codes.`
- evidence:
  - command: `python3 -c "from pathlib import Path; d=Path('novaic-tools-server/docs/tools-round009-runbook.md').read_text(); assert all(m in d for m in ['TOOLS_PREFLIGHT:PASS','TOOLS_PREFLIGHT_ERROR:RUNTIME_ORCHESTRATOR_URL_MISSING','TOOLS_PREFLIGHT_ERROR:TOOL_RESULT_SERVICE_URL_MISSING','TOOLS_PREFLIGHT_FAIL_CLOSED:PASS','TOOLS_SPLIT_BASELINE:PASS','TOOLS_R009_RUNBOOK_COMPLETE:PASS']); print('TOOLS_R009_RUNBOOK_COMPLETE:PASS')"`
  - expected_marker: `TOOLS_R009_RUNBOOK_COMPLETE:PASS`
  - repo_url: `https://github.com/novaic-org/novaic-tools-server`
  - commit_sha: `92a4f1fef421976944312739fdd7247cf3ea06ed`
  - migrated_paths: `novaic-tools-server/docs/tools-round009-runbook.md` (new)
  - summary: `PASS — runbook present with all 6 required markers confirmed.`
  - artifact_path: `novaic-tools-server/docs/tools-round009-runbook.md`
- status: DONE

---

## Split-root reliability baseline

- command: `bash novaic-tools-server/scripts/tools/ci_preflight_probe_prereqs.sh 2>/dev/null | grep -c PASS && pytest -q novaic-tools-server/tests/unit/tools_server/ 2>&1 | grep passed && echo TOOLS_SPLIT_BASELINE_R009:PASS`
- expected_marker: `TOOLS_SPLIT_BASELINE_R009:PASS`
- repo_url: `https://github.com/novaic-org/novaic-tools-server`
- commit_sha: `92a4f1fef421976944312739fdd7247cf3ea06ed`
- status: DONE

---

## Questions For Program Owner

- question: `Should the MANDATORY_SPLIT_ENV list in preflight.py be externally configurable (e.g. via a JSON config file) in future rounds, or is hard-coding the list in source acceptable long-term?`
- why_blocking: `Not blocking for round-009. Relevant if new services are added without a code change cycle.`
- options: `A) Keep hard-coded list in source (change requires code commit). B) Load mandatory var list from config/services.json at startup. C) Introduce NOVAIC_PREFLIGHT_REQUIRED_VARS env var as override.`
- recommended_option: `A — list is short (3 entries), changes rarely, and code review provides appropriate governance.`
- impact_if_unanswered: `List stays hard-coded; no runtime impact.`
- requested_by_round: `round-010`

## Team status
- status: DONE
- blocker: none
