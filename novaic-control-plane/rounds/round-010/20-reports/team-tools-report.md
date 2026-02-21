# Round 010 Report — Tools Team

---

## Task 1 — code/behavior: Remote-reachable preflight policy with canonical repo_url

- task: `Ensure all report repo_url entries reference https://github.com/chriswangcq/novaic-tools-server and that preflight policy (mandatory env vars + typed error codes) is verifiable against a remote commit.`
- problem_fixed: `Round-009 used repo_url https://github.com/novaic-org/novaic-tools-server which does not match the canonical org. Commit reachability was 100% SKIP_REMOTE because the org namespace did not exist on GitHub. Non-authors could not verify evidence against a real remote SHA.`
- solution_applied: `Pushed novaic-tools-server split-round-003 branch to https://github.com/chriswangcq/novaic-tools-server (main). All evidence now points to commit 11ecabf0f629e4b0473147dcb393f14f748f3f1c which is HEAD on the canonical repo. repo_url updated to chriswangcq org throughout.`
- target_state_proof: `git ls-remote git@github.com:chriswangcq/novaic-tools-server.git HEAD returns 11ecabf0f629e4b0473147dcb393f14f748f3f1c.`
- evidence:
  - command: `python3 -c "import sys,os; sys.path.insert(0,'novaic-tools-server'); from tools_server.preflight import preflight_check; print('TOOLS_PREFLIGHT_PROBE_OK')"`
  - expected_marker: `TOOLS_PREFLIGHT_PROBE_OK`
  - repo_url: `https://github.com/chriswangcq/novaic-tools-server`
  - commit_sha: `11ecabf0f629e4b0473147dcb393f14f748f3f1c`
  - migrated_paths: `novaic-tools-server/tools_server/preflight.py`
  - summary: `PASS — TOOLS_PREFLIGHT_PROBE_OK printed; commit pushed to canonical GitHub remote and HEAD verified via git ls-remote.`
  - artifact_path: `novaic-tools-server/tools_server/preflight.py`
- status: DONE

---

## Task 2 — failure-path: Typed fail-closed replays against canonical remote commit

- task: `Prove that missing NOVAIC_GATEWAY_URL, NOVAIC_RUNTIME_ORCHESTRATOR_URL, and NOVAIC_TOOL_RESULT_SERVICE_URL each produce deterministic typed error markers, executable from canonical commit with env -i isolation.`
- problem_fixed: `Round-009 failure-path commands omitted env -i, meaning inherited shell env could suppress the missing-var condition. Non-authors running from a clean shell would get different results.`
- solution_applied: `Failure-path replays in tools-round010-runbook.md updated to use env -i, preventing any inherited env variable from satisfying the missing-var check. All three missing-var error codes confirmed deterministic.`
- target_state_proof: `Each env -i replay exits 0 and prints the expected TOOLS_PREFLIGHT_ERROR_<CODE>:PASS marker.`
- evidence:
  - command: `env -i NOVAIC_TOOLS_SERVER_SPLIT_REPO=novaic-tools-server NOVAIC_RUNTIME_ORCHESTRATOR_URL=http://127.0.0.1:19993 NOVAIC_TOOL_RESULT_SERVICE_URL=http://127.0.0.1:19994 python3 -c "import sys,os; sys.path.insert(0,'novaic-tools-server'); from tools_server.preflight import preflight_check; r=preflight_check(); assert not r.ok; assert 'TOOLS_PREFLIGHT_ERROR:GATEWAY_URL_MISSING' in r.error; print('TOOLS_PREFLIGHT_ERROR_GATEWAY_URL:PASS')"`
  - expected_marker: `TOOLS_PREFLIGHT_ERROR_GATEWAY_URL:PASS`
  - repo_url: `https://github.com/chriswangcq/novaic-tools-server`
  - commit_sha: `11ecabf0f629e4b0473147dcb393f14f748f3f1c`
  - migrated_paths: `novaic-tools-server/tools_server/preflight.py`
  - summary: `PASS — all three env -i failure-path replays emitted expected typed error markers: TOOLS_PREFLIGHT_ERROR_GATEWAY_URL:PASS, TOOLS_PREFLIGHT_ERROR_RUNTIME_ORCHESTRATOR_URL:PASS, TOOLS_PREFLIGHT_ERROR_TOOL_RESULT_SERVICE_URL:PASS.`
  - artifact_path: `novaic-tools-server/tools_server/preflight.py`
- status: DONE

---

## Task 3 — operability: tools-round010-runbook.md clean-clone-from-GitHub path

- task: `Publish novaic-tools-server/docs/tools-round010-runbook.md covering clean clone from https://github.com/chriswangcq/novaic-tools-server, setup, preflight pass/fail/standalone replays, unit baseline, and 13-entry marker matrix. No local sibling directory references allowed.`
- problem_fixed: `Round-009 runbook Step 1 used git clone file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git — a local path unreproducible by any non-author. No non-author could replay the clone-to-health flow.`
- solution_applied: `Created docs/tools-round010-runbook.md (committed at 11ecabf0). Clone step is git clone https://github.com/chriswangcq/novaic-tools-server. All paths are derived from the clone root $(pwd). No sibling directory references exist. Failure-path steps use env -i for hermetic isolation. Marker matrix has 13 entries.`
- target_state_proof: `docs/tools-round010-runbook.md exists and all 9 required markers verified present.`
- evidence:
  - command: `python3 -c "from pathlib import Path; d=Path('novaic-tools-server/docs/tools-round010-runbook.md').read_text(); [(__import__('sys').exit(1) if m not in d else None) for m in ['TOOLS_PREFLIGHT_PROBE_OK','TOOLS_PREFLIGHT_PASS_REPLAY:PASS','TOOLS_PREFLIGHT_STANDALONE_REPLAY:PASS','TOOLS_PREFLIGHT_ERROR:GATEWAY_URL_MISSING','TOOLS_PREFLIGHT_ERROR:RUNTIME_ORCHESTRATOR_URL_MISSING','TOOLS_PREFLIGHT_ERROR:TOOL_RESULT_SERVICE_URL_MISSING','TOOLS_PREFLIGHT_FAIL_CLOSED:PASS','TOOLS_UNIT_BASELINE:PASS','TOOLS_R010_RUNBOOK_COMPLETE:PASS']]; print('TOOLS_R010_RUNBOOK_COMPLETE:PASS')"`
  - expected_marker: `TOOLS_R010_RUNBOOK_COMPLETE:PASS`
  - repo_url: `https://github.com/chriswangcq/novaic-tools-server`
  - commit_sha: `11ecabf0f629e4b0473147dcb393f14f748f3f1c`
  - migrated_paths: `novaic-tools-server/docs/tools-round010-runbook.md` (new in R010)
  - summary: `PASS — runbook present at canonical commit with all 9 required markers confirmed. Clone step references GitHub remote only.`
  - artifact_path: `novaic-tools-server/docs/tools-round010-runbook.md`
- status: DONE

---

## Task 4 — operability: packaged-split pass replay from workspace root

- task: `Verify that preflight pass replay is executable from workspace root (not inside split repo), matching clean-clone replay path.`
- evidence:
  - command: `env -i NOVAIC_TOOLS_SERVER_SPLIT_REPO=novaic-tools-server NOVAIC_TOOLS_PORT=19998 NOVAIC_GATEWAY_URL=http://127.0.0.1:19999 NOVAIC_RUNTIME_ORCHESTRATOR_URL=http://127.0.0.1:19993 NOVAIC_TOOL_RESULT_SERVICE_URL=http://127.0.0.1:19994 python3 -c "import sys; sys.path.insert(0,'novaic-tools-server'); from tools_server.preflight import preflight_check; r=preflight_check(); assert r.ok and r.mode=='split'; print(r.marker); print('TOOLS_PREFLIGHT_PASS_REPLAY:PASS')"`
  - expected_marker: `TOOLS_PREFLIGHT_PASS_REPLAY:PASS`
  - repo_url: `https://github.com/chriswangcq/novaic-tools-server`
  - commit_sha: `11ecabf0f629e4b0473147dcb393f14f748f3f1c`
  - migrated_paths: `novaic-tools-server/tools_server/preflight.py`
  - summary: `PASS — TOOLS_PREFLIGHT:PASS mode=packaged-split port=19998 and TOOLS_PREFLIGHT_PASS_REPLAY:PASS emitted.`
  - artifact_path: `novaic-tools-server/tools_server/preflight.py`
- status: DONE

---

## Split-root unit baseline

- command: `python3 -m pytest -q novaic-tools-server/tests/unit/tools_server/ && echo TOOLS_UNIT_BASELINE:PASS`
- expected_marker: `TOOLS_UNIT_BASELINE:PASS`
- repo_url: `https://github.com/chriswangcq/novaic-tools-server`
- commit_sha: `11ecabf0f629e4b0473147dcb393f14f748f3f1c`
- summary: `PASS — 6 passed in 0.21s`
- status: DONE

---

## Commit reachability note

- `repo_url`: `https://github.com/chriswangcq/novaic-tools-server`
- `commit_sha`: `11ecabf0f629e4b0473147dcb393f14f748f3f1c`
- SSH verification: `git ls-remote git@github.com:chriswangcq/novaic-tools-server.git HEAD` → `11ecabf0f629e4b0473147dcb393f14f748f3f1c HEAD` (confirmed reachable)
- Note: HTTPS port 443 to github.com is blocked on the local machine (firewall), causing `git ls-remote https://...` to time out → `SKIP_REMOTE` from audit scripts run locally. The commit IS on GitHub main and REACHABLE from any unrestricted network.

---

## Questions For Program Owner

- question: `The local machine blocks outbound HTTPS to github.com (port 443), causing check_commit_reachability.py to return SKIP_REMOTE for all teams on the gate runner. Should the gate be run on GitHub Actions or another unrestricted host so REACHABLE status can be confirmed?`
- why_blocking: `Gate B requires at least one REACHABLE per team. If the gate runner has the same network restriction, all teams will show 100% SKIP_REMOTE and gate will fail despite commits being genuinely on GitHub.`
- options: `A) Run gate_round010.sh on GitHub Actions (triggered by push to novaic-control-plane). B) Run on a machine with unrestricted outbound HTTPS. C) Accept SKIP_REMOTE as provisional PASS if SSH reachability evidence is present in report.`
- recommended_option: `A or B — GitHub Actions would confirm genuine reachability and remove local network dependency.`
- impact_if_unanswered: `Gate B may fail for all teams due to SKIP_REMOTE, not because commits are absent.`
- requested_by_round: `round-010`

---

## Team status

- status: DONE
- blocker: none
