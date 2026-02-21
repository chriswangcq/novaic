# Round 009 Report - API Team

---

## Task 1 — code/behavior: Remove implicit RUNTIME_ORCHESTRATOR_URL fallback; enforce explicit URL

- task: `Remove http://127.0.0.1:20001 default from config/service_config.py; add module-level RuntimeError guard; add SPLIT_RUNTIME_URL_EXPLICIT_REQUIRED=PASS marker`
- problem_fixed: `ServiceConfig.RUNTIME_ORCHESTRATOR_URL had implicit local default http://127.0.0.1:20001 — gateway silently used localhost if env var was absent, making multi-repo reproducibility non-deterministic`
- solution_applied: `Extracted env var to module-level _runtime_orchestrator_url; added RuntimeError if value is falsy; ServiceConfig.RUNTIME_ORCHESTRATOR_URL now guaranteed non-empty string; added SPLIT_RUNTIME_URL_EXPLICIT_REQUIRED=PASS to smoke script`
- target_state_proof: `smoke_gateway_repo_root.sh emits SPLIT_RUNTIME_URL_EXPLICIT_REQUIRED=PASS; service_config.py source contains no http://127.0.0.1:20001 literal`
- command: `bash novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh`
- expected_marker: `SPLIT_RUNTIME_URL_EXPLICIT_REQUIRED=PASS`
- expected_marker: `SPLIT_RUNTIME_ENDPOINT_ENFORCED=PASS`
- expected_marker: `SPLIT_E2E_RUNTIME_FORWARD=PASS`
- repo_url: `https://github.com/novaic/novaic-gateway`
- commit_sha: `a1b9f3f879c584b549d5f0e074468ea582d9bded`
- migrated_paths: `rounds/round-003/split-move/repos/novaic-gateway/config/service_config.py (modified)`
- migrated_paths: `rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh (modified)`
- artifact_path: `rounds/round-003/split-move/repos/novaic-gateway/config/service_config.py`
- status: `DONE`

---

## Task 2 — failure-path: Startup guard rejects missing URL; runtime-unreachable exits non-zero

- task: `Add fail_path_startup_no_url.sh verifying RuntimeError at import time; confirm fail_path_replay_gateway.sh still emits FAIL_PATH_RUNTIME_UNREACHABLE=PASS after config change`
- problem_fixed: `No test existed confirming the gateway would fail fast at startup when RUNTIME_ORCHESTRATOR_URL is absent; failure path only covered runtime-unreachable, not missing-config`
- solution_applied: `Created scripts/fail_path_startup_no_url.sh; imports service_config via .venv python without env var; captures non-zero exit 1; emits FAIL_PATH_STARTUP_NO_URL=PASS; reconfirmed existing fail_path_replay_gateway.sh still green at commit a1b9f3f`
- target_state_proof: `fail_path_startup_no_url.sh exits 0 and emits FAIL_PATH_STARTUP_NO_URL=PASS; fail_path_replay_gateway.sh exits 0 and emits FAIL_PATH_RUNTIME_UNREACHABLE=PASS`
- command: `bash novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway/scripts/fail_path_startup_no_url.sh`
- expected_marker: `FAIL_PATH_STARTUP_NO_URL=PASS`
- expected_marker: `FAIL_PATH_STARTUP_EXIT_CODE=1`
- repo_url: `https://github.com/novaic/novaic-gateway`
- commit_sha: `a1b9f3f879c584b549d5f0e074468ea582d9bded`
- migrated_paths: `rounds/round-003/split-move/repos/novaic-gateway/scripts/fail_path_startup_no_url.sh (new)`
- artifact_path: `rounds/round-003/split-move/repos/novaic-gateway/scripts/fail_path_startup_no_url.sh`
- status: `DONE`

---

## Task 3 — operability: Publish api-round009-replay-bundle.md with success + two failure transcripts

- task: `Publish rounds/round-009/split-fix/api-round009-replay-bundle.md with success-path transcript, failure-path A (runtime unreachable), failure-path B (startup no URL), and 15-entry marker index`
- problem_fixed: `Round 008 bundle had one failure path; round-009 adds a second failure path (startup guard) and updates all transcripts to commit a1b9f3f to remain current`
- solution_applied: `Created api-round009-replay-bundle.md with three replay sections, observed outputs, exit codes, and a full 15-entry marker index; all markers verified present in bundle file`
- target_state_proof: `grep returns 0 for both key markers from different failure paths`
- command: `grep -q "FAIL_PATH_STARTUP_NO_URL=PASS" novaic-control-plane/rounds/round-009/split-fix/api-round009-replay-bundle.md && grep -q "SPLIT_RUNTIME_URL_EXPLICIT_REQUIRED=PASS" novaic-control-plane/rounds/round-009/split-fix/api-round009-replay-bundle.md && echo "ROUND009_BUNDLE_CHECK=PASS"`
- expected_marker: `ROUND009_BUNDLE_CHECK=PASS`
- repo_url: `https://github.com/novaic/novaic-gateway`
- commit_sha: `a1b9f3f879c584b549d5f0e074468ea582d9bded`
- migrated_paths: `rounds/round-009/split-fix/api-round009-replay-bundle.md (new operability artifact)`
- artifact_path: `rounds/round-009/split-fix/api-round009-replay-bundle.md`
- status: `DONE`

---

## Questions For Program Owner

- question: `Gateway split repo currently depends on novaic-runtime-orchestrator and novaic-tools-server sibling dirs at ../; when will those repos have canonical remote URLs, and should smoke_gateway_repo_root.sh be updated to clone from remote instead of assuming sibling path?`
- why_blocking: `Current smoke script uses relative ../novaic-runtime-orchestrator path — non-authors on a clean machine cannot run the bundle without also having the sibling repos at the expected relative paths`
- options: `A: Accept sibling-path convention permanently (document in README). B: Define a round when remotes exist and update smoke script to accept RUNTIME_REPO_URL/TOOLS_REPO_URL env vars pointing to cloneable remotes.`
- recommended_option: `B — announce the round; allows non-author clean-clone replay without manual path setup`
- impact_if_unanswered: `Operability artifact is technically non-author-runnable from a fresh machine today; replay requires pre-existing sibling repo layout`
- requested_by_round: `round-009`

---

## Team status

- status: `DONE`
- blocker: `none`
