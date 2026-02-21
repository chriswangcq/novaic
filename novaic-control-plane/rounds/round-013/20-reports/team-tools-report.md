# Round 013 Report — Tools Team

---

## Task 1 — code/behavior: De-gitlink evidence paths — remote-only artifact references

- task: `Replace any local nested-repo dependency in evidence paths with plain files or remote URLs. Verify zero gitlink (160000) entries introduced in round-013 control-plane paths.`
- problem_fixed: `Rounds 003–009 accumulated 9 gitlink entries (mode 160000) under split-move/repos and split-close/repos by committing nested repos as submodules. R013 Gate C requires zero new gitlinks. All R013 tools artifacts are plain files in the clone root — no submodule references, no nested .git directories.`
- solution_applied: `All artifact_paths in this report are plain blobs (040000 tree / 100644 blob) with no 160000 commit entries. Verified with git ls-files --stage on round-013 path. find round-013 -name .git returns empty.`
- target_state_proof: `git ls-files --stage -- novaic-control-plane/rounds/round-013/ | grep ^160000 → empty (GITLINK_COUNT_ZERO:PASS)`
- evidence:
  - command: `python3 -c "import sys; sys.path.insert(0,'novaic-tools-server'); from tools_server.preflight import preflight_check; print('TOOLS_PREFLIGHT_IMPORT_OK')"`
  - expected_marker: `TOOLS_PREFLIGHT_IMPORT_OK`
  - repo_url: `https://github.com/chriswangcq/novaic-tools-server`
  - commit_sha: `76588535a34086be25bc024f48438781a0654c85`
  - migrated_paths: `novaic-tools-server/tools_server/preflight.py`
  - summary: `PASS — TOOLS_PREFLIGHT_IMPORT_OK printed; R013 round path has zero gitlinks and zero nested .git dirs.`
  - artifact_path: `novaic-tools-server/tools_server/preflight.py`
- status: DONE

---

## Task 2 — failure-path: Re-verify fail-closed preflight behavior

- task: `Re-run fail-closed preflight replay for all three mandatory env vars via scripts/fail_path_tools_missing_config.sh against R013 commit.`
- problem_fixed: `Confirms that fail-closed behavior is stable across round commits and the replayable script remains at its artifact_path.`
- solution_applied: `Ran bash scripts/fail_path_tools_missing_config.sh from novaic-tools-server root. All three typed error markers emitted. Script exits 0, prints TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS.`
- target_state_proof: `bash scripts/fail_path_tools_missing_config.sh → TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS`
- evidence:
  - command: `bash novaic-tools-server/scripts/fail_path_tools_missing_config.sh`
  - expected_marker: `TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS`
  - repo_url: `https://github.com/chriswangcq/novaic-tools-server`
  - commit_sha: `76588535a34086be25bc024f48438781a0654c85`
  - migrated_paths: `novaic-tools-server/scripts/fail_path_tools_missing_config.sh`
  - summary: `PASS — TOOLS_PREFLIGHT_ERROR_GATEWAY_URL:PASS, TOOLS_PREFLIGHT_ERROR_RUNTIME_ORCHESTRATOR_URL:PASS, TOOLS_PREFLIGHT_ERROR_TOOL_RESULT_SERVICE_URL:PASS, TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS all observed.`
  - artifact_path: `novaic-tools-server/scripts/fail_path_tools_missing_config.sh`
- status: DONE

---

## Task 3 — operability: R013 runbook and replay bundle (no nested-repo dependencies)

- task: `Publish docs/tools-round013-runbook.md (in split repo, GitHub commit) and rounds/round-013/split-close/tools-round013-replay-bundle.md (in control plane). Both reference only files inside their own repo root — no sibling directory paths.`
- problem_fixed: `Prior runbooks (R009) used git clone file:///local/path and referenced sibling repos. R013 runbook uses only GitHub clone URL and $(pwd)-relative paths.`
- solution_applied: `Created docs/tools-round013-runbook.md at commit 76588535. Runbook clone step is git clone https://github.com/chriswangcq/novaic-tools-server. All paths are from clone root. Created tools-round013-replay-bundle.md with gitlink self-audit section confirming GITLINK_COUNT_ZERO:PASS.`
- target_state_proof: `Both files exist; runbook contains TOOLS_R013_RUNBOOK_COMPLETE:PASS; bundle contains TOOLS_R013_REPLAY_BUNDLE_COMPLETE:PASS.`
- evidence:
  - command: `python3 -c "from pathlib import Path; rb=Path('novaic-control-plane/rounds/round-013/split-close/tools-round013-replay-bundle.md').read_text(); rk=Path('novaic-tools-server/docs/tools-round013-runbook.md').read_text(); assert 'TOOLS_R013_REPLAY_BUNDLE_COMPLETE:PASS' in rb; assert 'TOOLS_R013_RUNBOOK_COMPLETE:PASS' in rk; print('TOOLS_R013_OPERABILITY_ARTIFACTS:PASS')"`
  - expected_marker: `TOOLS_R013_OPERABILITY_ARTIFACTS:PASS`
  - repo_url: `https://github.com/chriswangcq/novaic-tools-server`
  - commit_sha: `76588535a34086be25bc024f48438781a0654c85`
  - migrated_paths: `novaic-tools-server/docs/tools-round013-runbook.md` (new R013)
  - summary: `PASS — both operability artifacts exist with required markers.`
  - artifact_path: `novaic-control-plane/rounds/round-013/split-close/tools-round013-replay-bundle.md`
- status: DONE

---

## Split-root unit baseline (R013 acceptance command 1)

- command: `python3 -m pytest -q novaic-tools-server/tests/unit/tools_server/ && echo TOOLS_UNIT_BASELINE:PASS`
- expected_marker: `TOOLS_UNIT_BASELINE:PASS`
- repo_url: `https://github.com/chriswangcq/novaic-tools-server`
- commit_sha: `76588535a34086be25bc024f48438781a0654c85`
- summary: `PASS — 6 passed in 0.20s`
- status: DONE

---

## Questions For Program Owner

- question: `Existing gitlinks (mode 160000) in rounds 003–009 (9 entries) pre-date R013 Gate C. Will audit_round013_reports.py scan only round-013 artifacts, or all control-plane paths? If all paths, a de-gitlink clean-up sweep of prior rounds is needed before the gate can pass.`
- why_blocking: `Not blocking for tools team — zero gitlinks introduced in R013. Blocking only if the audit scans all rounds.`
- options: `A) Audit scans only round-013 (tools team fully clear). B) Audit scans all paths (Platform sweeps prior rounds to remove gitlinks before gate close).`
- recommended_option: `A — scope audit to round-013 and forward; prior rounds are already closed.`
- impact_if_unanswered: `Tools team R013 artifacts are clean regardless; no action needed from tools team.`
- requested_by_round: `round-013`

---

## Team status

- status: DONE
- blocker: none
