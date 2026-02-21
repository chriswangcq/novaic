# Round 012 Report — Tools Team

---

## Task 1 — code/behavior: Fix artifact paths — all referenced files exist

- task: `Ensure every artifact_path in the R012 report resolves to an existing file at gate close time. Remove stale/non-existent references.`
- problem_fixed: `Prior rounds referenced artifact paths that were valid at time of writing but could become stale if files moved. R012 Gate C makes non-existent artifact_path a hard gate failure. All four artifact paths used in this report are verified to exist.`
- solution_applied: `All artifact_path values point to files created or already present in this commit: tools_server/preflight.py (existing), scripts/fail_path_tools_missing_config.sh (new R012), docs/tools-round012-runbook.md (new R012), novaic-control-plane/rounds/round-012/split-close/tools-round012-replay-bundle.md (new R012).`
- target_state_proof: `All four artifact paths verified with: [ -f <path> ] && echo EXISTS for each.`
- evidence:
  - command: `python3 -c "import sys; sys.path.insert(0,'novaic-tools-server'); from tools_server.preflight import preflight_check; print('TOOLS_PREFLIGHT_IMPORT_OK')"`
  - expected_marker: `TOOLS_PREFLIGHT_IMPORT_OK`
  - repo_url: `https://github.com/chriswangcq/novaic-tools-server`
  - commit_sha: `36dfc84ef9c257728c3c4abc7c41b639613039c4`
  - migrated_paths: `novaic-tools-server/tools_server/preflight.py`
  - summary: `PASS — TOOLS_PREFLIGHT_IMPORT_OK printed; all four artifact paths exist on disk.`
  - artifact_path: `novaic-tools-server/tools_server/preflight.py`
- status: DONE

---

## Task 2 — failure-path: Failure-path script with typed error markers

- task: `Publish scripts/fail_path_tools_missing_config.sh — runs all three missing-env-var cases under env -i isolation, asserts typed error markers, emits TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS.`
- problem_fixed: `Previous rounds embedded failure-path replays only as inline commands in runbooks. R012 requires a replayable script at a known artifact_path so Platform can execute bash scripts/fail_path_tools_missing_config.sh directly.`
- solution_applied: `Created novaic-tools-server/scripts/fail_path_tools_missing_config.sh. Each of the three cases uses env -i to prevent inherited env interference. Script exits non-zero on any assertion failure, exits 0 and prints TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS on full success.`
- target_state_proof: `bash scripts/fail_path_tools_missing_config.sh → TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS`
- evidence:
  - command: `bash novaic-tools-server/scripts/fail_path_tools_missing_config.sh`
  - expected_marker: `TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS`
  - repo_url: `https://github.com/chriswangcq/novaic-tools-server`
  - commit_sha: `36dfc84ef9c257728c3c4abc7c41b639613039c4`
  - migrated_paths: `novaic-tools-server/scripts/fail_path_tools_missing_config.sh` (new R012)
  - summary: `PASS — all three typed error markers emitted and TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS confirmed.`
  - artifact_path: `novaic-tools-server/scripts/fail_path_tools_missing_config.sh`
- status: DONE

---

## Task 3 — operability: tools-round012-replay-bundle.md and runbook

- task: `Publish rounds/round-012/split-close/tools-round012-replay-bundle.md and docs/tools-round012-runbook.md. Both must exist at gate close time.`
- problem_fixed: `R012 split-close directory had no tools artifacts. Replay bundle provides a non-author-reproducible record of observed output for all acceptance commands.`
- solution_applied: `Created novaic-control-plane/rounds/round-012/split-close/tools-round012-replay-bundle.md with observed output for all three replays and an artifact existence table. Created docs/tools-round012-runbook.md with 8-entry marker matrix and step-by-step clone/setup/replay chain.`
- target_state_proof: `Both files exist and contain TOOLS_R012_REPLAY_BUNDLE_COMPLETE:PASS and TOOLS_R012_RUNBOOK_COMPLETE:PASS markers.`
- evidence:
  - command: `python3 -c "from pathlib import Path; rb=Path('novaic-control-plane/rounds/round-012/split-close/tools-round012-replay-bundle.md').read_text(); rk=Path('novaic-tools-server/docs/tools-round012-runbook.md').read_text(); assert 'TOOLS_R012_REPLAY_BUNDLE_COMPLETE:PASS' in rb; assert 'TOOLS_R012_RUNBOOK_COMPLETE:PASS' in rk; print('TOOLS_R012_OPERABILITY_ARTIFACTS:PASS')"`
  - expected_marker: `TOOLS_R012_OPERABILITY_ARTIFACTS:PASS`
  - repo_url: `https://github.com/chriswangcq/novaic-tools-server`
  - commit_sha: `36dfc84ef9c257728c3c4abc7c41b639613039c4`
  - migrated_paths: `novaic-tools-server/docs/tools-round012-runbook.md` (new R012)
  - summary: `PASS — both replay bundle and runbook exist with expected markers.`
  - artifact_path: `novaic-control-plane/rounds/round-012/split-close/tools-round012-replay-bundle.md`
- status: DONE

---

## Split-root unit baseline (R012 acceptance command 2)

- command: `python3 -m pytest -q novaic-tools-server/tests/unit/tools_server/ && echo TOOLS_UNIT_BASELINE:PASS`
- expected_marker: `TOOLS_UNIT_BASELINE:PASS`
- repo_url: `https://github.com/chriswangcq/novaic-tools-server`
- commit_sha: `36dfc84ef9c257728c3c4abc7c41b639613039c4`
- summary: `PASS — 6 passed in 0.18s`
- status: DONE

---

## Questions For Program Owner

- question: `artifact_existence_audit.py is referenced as R012 acceptance command 3 but the rounds/round-012/split-close/ directory does not yet contain Platform's audit scripts. Is the audit script expected to be created by Platform before gate close, or should teams provide a self-audit?`
- why_blocking: `Not blocking — all four team artifact paths exist. Self-audit confirms existence. Platform audit script will confirm same when added.`
- options: `A) Platform creates artifact_existence_audit.py before gate close. B) Teams provide self-audit Python script in their split-close directory. C) Acceptance command is skipped if script not present.`
- recommended_option: `A — consistent with prior rounds where Platform provides gate scripts.`
- impact_if_unanswered: `Team artifacts exist; gate will pass once Platform's script is added.`
- requested_by_round: `round-012`

---

## Team status

- status: DONE
- blocker: none
