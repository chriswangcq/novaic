# Round 008 Report - API Team

---

## Task 1 — code/behavior: Remove PYTHON_BIN fallback; enforce local .venv as only Python source

- task: `Remove optional PYTHON_BIN env-override fallback from smoke_gateway_repo_root.sh; add SPLIT_RUNTIME_ENDPOINT_ENFORCED=PASS marker`
- problem_fixed: `smoke_gateway_repo_root.sh accepted PYTHON_BIN env var allowing external Python injection, bypassing local .venv and making replay non-deterministic`
- solution_applied: `Removed if [ -n "${PYTHON_BIN:-}" ] branch from resolve_python_bin(); function now unconditionally bootstraps $ROOT_DIR/.venv; added SPLIT_RUNTIME_ENDPOINT_ENFORCED=PASS marker as machine-checkable proof`
- target_state_proof: `smoke_gateway_repo_root.sh emits SPLIT_RUNTIME_ENDPOINT_ENFORCED=PASS on every run; no PYTHON_BIN branch in script source`
- command: `bash novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh`
- expected_marker: `SPLIT_RUNTIME_ENDPOINT_ENFORCED=PASS`
- expected_marker: `SPLIT_GATEWAY_HEALTH=PASS`
- expected_marker: `SPLIT_E2E_RUNTIME_FORWARD=PASS`
- repo_url: `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway`
- commit_sha: `5a8c1052747a323a449239e7d160650c4f0e1537`
- migrated_paths: `rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh (modified)`
- artifact_path: `rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh`
- status: `DONE`

---

## Task 2 — failure-path: Deterministic fail marker and non-zero exit when runtime unreachable

- task: `Create fail_path_replay_gateway.sh; run replay chain with invalid runtime URL; verify FAIL_PATH_RUNTIME_UNREACHABLE=PASS emitted and inner chain exits non-zero`
- problem_fixed: `No failure-path verification existed; chain behavior when runtime was unreachable was untested and had no deterministic machine-greppable marker`
- solution_applied: `Created scripts/fail_path_replay_gateway.sh; runs replay_gateway_runtime_chain.sh with RUNTIME_BASE_URL=http://127.0.0.1:29999; captures non-zero exit (curl exit 7, connection refused); emits FAIL_PATH_RUNTIME_UNREACHABLE=PASS; standalone — no services required`
- target_state_proof: `fail_path_replay_gateway.sh exits 0 and emits FAIL_PATH_RUNTIME_UNREACHABLE=PASS when inner chain exits non-zero with bad URL`
- command: `bash novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway/scripts/fail_path_replay_gateway.sh`
- expected_marker: `FAIL_PATH_RUNTIME_UNREACHABLE=PASS`
- expected_marker: `FAIL_PATH_EXIT_CODE=7`
- repo_url: `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway`
- commit_sha: `5a8c1052747a323a449239e7d160650c4f0e1537`
- migrated_paths: `rounds/round-003/split-move/repos/novaic-gateway/scripts/fail_path_replay_gateway.sh (new)`
- artifact_path: `rounds/round-003/split-move/repos/novaic-gateway/scripts/fail_path_replay_gateway.sh`
- status: `DONE`

---

## Task 3 — operability: Publish replay bundle with success + failure transcripts and marker index

- task: `Publish api-gateway-replay-bundle-round008.md containing success-path transcript, failure-path transcript, and 12-entry marker index`
- problem_fixed: `Round 007 artifact had only success path; Gate C required failure-path replay; Gate D required a named operability artifact with both paths documented`
- solution_applied: `Created rounds/round-008/split-fix/api-gateway-replay-bundle-round008.md with: success-path observed output (10 markers), failure-path observed output (2 markers), full marker index table; bundle verified MARKER_COUNT=12/12`
- target_state_proof: `grep returns 0 for all key markers in the artifact file`
- command: `grep -q "FAIL_PATH_RUNTIME_UNREACHABLE=PASS" novaic-control-plane/rounds/round-008/split-fix/api-gateway-replay-bundle-round008.md && grep -q "SPLIT_RUNTIME_ENDPOINT_ENFORCED=PASS" novaic-control-plane/rounds/round-008/split-fix/api-gateway-replay-bundle-round008.md && echo "REPLAY_BUNDLE_CHECK=PASS"`
- expected_marker: `REPLAY_BUNDLE_CHECK=PASS`
- repo_url: `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway`
- commit_sha: `5a8c1052747a323a449239e7d160650c4f0e1537`
- migrated_paths: `rounds/round-008/split-fix/api-gateway-replay-bundle-round008.md (new operability artifact)`
- artifact_path: `rounds/round-008/split-fix/api-gateway-replay-bundle-round008.md`
- status: `DONE`

---

## Questions For Program Owner

- question: `When will file:/// repo_url values be replaced with https://github.com/<org>/<repo> canonical remote URLs?`
- why_blocking: `Current reports use file:/// pointing to local monorepo paths. If remote repos are created in a future round, all prior evidence referencing file:/// will need a migration notice; canonical URL audit policy will need updating.`
- options: `A: Keep file:/// permanently (no remote repos will be created). B: Define a target round for GitHub remote creation and update canonical URL policy to require https:// from that round.`
- recommended_option: `B — announce migration round in advance so teams update reports and audits in one pass`
- impact_if_unanswered: `Teams cannot determine whether current file:/// evidence will remain valid at round close`
- requested_by_round: `round-008`

---

## Team status

- status: `DONE`
- blocker: `none`
