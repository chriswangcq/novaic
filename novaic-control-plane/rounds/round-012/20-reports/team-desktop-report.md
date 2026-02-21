# Team Desktop — Round 012 Report

## Team
- team: desktop
- round: round-012
- report_status: DONE

---

## Task 1 — Replace missing artifact references with real, path-safe scripts

### Problem
Previous rounds referenced absolute `/Users/wangchaoqun/...` paths in replay scripts, making clean-clone reproduction impossible for non-authors. Round 012 requires all `artifact_path` values to physically exist and scripts must use relative paths only.

### Solution
Created two new scripts under `novaic-control-plane/rounds/round-003/split-move/repos/novaic-desktop/scripts/` that resolve paths relative to their own `__file__` / `$BASH_SOURCE[0]` location. No hardcoded absolute paths.

### Target State Proof

```
command: python rounds/round-003/split-move/repos/novaic-desktop/scripts/test_split_config_abort.py
expected_marker: SPLIT_CONFIG_ABORT_TEST=PASS
result: PASS (found 3 occurrences in novaic-app/src-tauri/src/main.rs)
```

```
command: cd novaic-app/src-tauri && cargo check && echo DESKTOP_BUILD=PASS
expected_marker: DESKTOP_BUILD=PASS
result: PASS
```

- repo_url: `https://github.com/chriswangcq/novaic`
- branch: `add-virtual-mobile`
- commit_sha: `8f0183c5d12c0abec17ba3a5d5bf91a2c3a976fb`
- migrated_paths: `novaic-control-plane/rounds/round-003/split-move/repos/novaic-desktop/scripts/test_split_config_abort.py`, `novaic-control-plane/rounds/round-003/split-move/repos/novaic-desktop/scripts/fail_path_desktop_split_config.sh`
- artifact_path: `novaic-control-plane/rounds/round-003/split-move/repos/novaic-desktop/scripts/test_split_config_abort.py`

---

## Task 2 — Re-run failure-path replay with relative-path script

### Problem
New failure-path script (`fail_path_desktop_split_config.sh`) must produce deterministic `TOOLS_HOP=FAIL FAILURE_PATH_REPLAY=PASS` markers using only relative paths, and its diag output must persist as a round-012 artifact.

### Solution
Ran `fail_path_desktop_split_config.sh` with `DIAG_OUT` pointed to the round-012 artifact location. Script resolves backend venv path from its own directory rather than absolute `/Users/...`.

### Target State Proof

```
command: DIAG_OUT=novaic-control-plane/rounds/round-012/split-fix/round012-failure-path-diag.txt bash rounds/round-003/split-move/repos/novaic-desktop/scripts/fail_path_desktop_split_config.sh
expected_marker: TOOLS_HOP=FAIL FAILURE_PATH_REPLAY=PASS
result: PASS
```

Observed output:
```
DESKTOP_HOP=PASS
GATEWAY_HOP=PASS
RUNTIME_HOP=PASS
TOOLS_HOP=FAIL
TOOLS_UNAVAILABLE=true
FAILURE_PATH_REPLAY=PASS
```

- repo_url: `https://github.com/chriswangcq/novaic`
- branch: `add-virtual-mobile`
- commit_sha: `8f0183c5d12c0abec17ba3a5d5bf91a2c3a976fb`
- migrated_paths: `novaic-control-plane/rounds/round-012/split-fix/round012-failure-path-diag.txt`
- artifact_path: `novaic-control-plane/rounds/round-012/split-fix/round012-failure-path-diag.txt`

---

## Task 3 — Publish desktop-round012-replay-bundle.md + artifact_existence_audit.py

### Problem
Non-authors need a clean-clone-compatible operability bundle for round-012, and Platform needs an `artifact_existence_audit.py` that checks all team `artifact_path` fields physically exist.

### Solution
Authored `desktop-round012-replay-bundle.md` in `round-012/split-close/` with clean-clone steps and no absolute paths. Created `artifact_existence_audit.py` under `round-012/split-close/repos/novaic-evidence-audit/scripts/`.

### Target State Proof

```
command: python3 rounds/round-012/split-close/repos/novaic-evidence-audit/scripts/artifact_existence_audit.py
expected_marker: ARTIFACT_EXISTENCE_AUDIT=PASS
result: PASS (checked=3 missing=0)
```

```
command: grep -c "TOOLS_HOP=FAIL\|SPLIT_CONFIG_STRICT_ABORT\|ARTIFACT_EXISTENCE_AUDIT" novaic-control-plane/rounds/round-012/split-close/desktop-round012-replay-bundle.md && echo DESKTOP_OPERABILITY_BUNDLE=PASS
expected_marker: DESKTOP_OPERABILITY_BUNDLE=PASS
result: PASS
```

- repo_url: `https://github.com/chriswangcq/novaic`
- branch: `add-virtual-mobile`
- commit_sha: `8f0183c5d12c0abec17ba3a5d5bf91a2c3a976fb`
- migrated_paths: `novaic-control-plane/rounds/round-012/split-close/desktop-round012-replay-bundle.md`, `novaic-control-plane/rounds/round-012/split-close/repos/novaic-evidence-audit/scripts/artifact_existence_audit.py`
- artifact_path: `novaic-control-plane/rounds/round-012/split-close/desktop-round012-replay-bundle.md`

---

## Questions for program owner

- question_1: No blockers. All three tasks DONE.

---

## Team status

- status: DONE
- blocker: none
