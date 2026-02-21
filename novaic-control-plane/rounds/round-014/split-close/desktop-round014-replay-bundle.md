# Desktop Split-Chain Replay Bundle — Round 014

## Metadata

| field | value |
|-------|-------|
| canonical_repo_url | `https://github.com/chriswangcq/novaic` |
| branch | `add-virtual-mobile` |
| round | round-014 |
| operator | team-desktop |
| generated_at | 2026-02-21 |

---

## Remote reproducibility

All commands below run from the root of a clean clone; no sibling-directory assumptions.

```bash
git clone https://github.com/chriswangcq/novaic.git
cd novaic
git checkout add-virtual-mobile
cd novaic-backend && python3 -m venv venv && venv/bin/pip install -q -r requirements.txt && cd ..
```

---

## Task 1 — Split-config abort check

```bash
python rounds/round-003/split-move/repos/novaic-desktop/scripts/test_split_config_abort.py
```

Expected markers: `SPLIT_CONFIG_ABORT_PRESENT=PASS` `SPLIT_CONFIG_ABORT_TEST=PASS`

```bash
cd novaic-app/src-tauri && cargo check && echo DESKTOP_BUILD=PASS
```

Expected marker: `DESKTOP_BUILD=PASS`

Gitlink hard check:

```bash
git ls-files --stage | grep "^160000" || echo NO_GITLINKS_IN_INDEX=PASS
```

Expected marker: `NO_GITLINKS_IN_INDEX=PASS`

---

## Task 2 — Failure-path replay (tools unavailable)

```bash
DIAG_OUT=novaic-control-plane/rounds/round-014/split-fix/round014-failure-path-diag.txt \
  bash rounds/round-003/split-move/repos/novaic-desktop/scripts/fail_path_desktop_split_config.sh
```

Expected markers: `TOOLS_HOP=FAIL` `FAILURE_PATH_REPLAY=PASS`

---

## Task 3 — Artifact existence audit

```bash
python3 rounds/round-014/split-close/repos/novaic-evidence-audit/scripts/artifact_existence_audit.py
```

Expected marker: `ROUND014_ARTIFACT_EXISTENCE_AUDIT_COMPLETED`

---

## Troubleshooting matrix

| symptom | cause | fix |
|---------|-------|-----|
| `SPLIT_CONFIG_STRICT_ABORT` in startup-diagnostics | `NOVAIC_EXTERNAL_SERVICES_MODE=1` without `NOVAIC_GATEWAY_URL` | Set `NOVAIC_GATEWAY_URL=http://<host>:<port>` |
| `DESKTOP_HOP=FAIL` | gateway not reachable | Confirm gateway running on expected port |
| `TOOLS_HOP=FAIL` | tools-server absent (expected in failure scenario) | Expected; start TRS for happy path |
| `ModuleNotFoundError: No module named 'uvicorn'` | system python3 used | Use `novaic-backend/venv/bin/python` |
| `GITLINK_FOUND` in audit | `160000` entry in git index | `git rm --cached <path>` to de-gitlink; do not use nested repos under control-plane |
| `ROUND014_ARTIFACT_EXISTENCE_AUDIT_COMPLETED` missing | `artifact_path` references non-existent file | Commit the artifact file; check path spelling |

---

## Artifact index

| artifact | path |
|----------|------|
| test_split_config_abort.py | `novaic-control-plane/rounds/round-003/split-move/repos/novaic-desktop/scripts/test_split_config_abort.py` |
| fail_path_desktop_split_config.sh | `novaic-control-plane/rounds/round-003/split-move/repos/novaic-desktop/scripts/fail_path_desktop_split_config.sh` |
| failure-path diag (round-014) | `novaic-control-plane/rounds/round-014/split-fix/round014-failure-path-diag.txt` |
| replay bundle | `novaic-control-plane/rounds/round-014/split-close/desktop-round014-replay-bundle.md` |
| main.rs (strict abort) | `novaic-app/src-tauri/src/main.rs` |
| split_runtime.rs | `novaic-app/src-tauri/src/split_runtime.rs` |
