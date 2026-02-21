# Desktop Split-Chain Replay Bundle — Round 013

## Metadata

| field | value |
|-------|-------|
| canonical_repo_url | `https://github.com/chriswangcq/novaic` |
| branch | `add-virtual-mobile` |
| round | round-013 |
| operator | team-desktop |
| generated_at | 2026-02-21 |

---

## Clean-clone setup

```bash
git clone https://github.com/chriswangcq/novaic.git
cd novaic
git checkout add-virtual-mobile
cd novaic-backend && python3 -m venv venv && venv/bin/pip install -q -r requirements.txt && cd ..
```

> No absolute paths. All scripts resolve from their own location using `__file__` / `$BASH_SOURCE[0]`.

---

## Task 1 — Split-config abort check

```bash
python rounds/round-003/split-move/repos/novaic-desktop/scripts/test_split_config_abort.py
```

Expected markers:
- `SPLIT_CONFIG_ABORT_PRESENT=PASS`
- `SPLIT_CONFIG_ABORT_TEST=PASS`

Build verification:

```bash
cd novaic-app/src-tauri && cargo check && echo DESKTOP_BUILD=PASS
```

Expected marker: `DESKTOP_BUILD=PASS`

No-gitlink check:

```bash
git ls-files --stage | grep "^160000" | grep "novaic-desktop\|round-013" || echo NO_DESKTOP_GITLINKS=PASS
```

Expected marker: `NO_DESKTOP_GITLINKS=PASS`

---

## Task 2 — Failure-path replay (tools unavailable)

```bash
DIAG_OUT=novaic-control-plane/rounds/round-013/split-fix/round013-failure-path-diag.txt \
  bash rounds/round-003/split-move/repos/novaic-desktop/scripts/fail_path_desktop_split_config.sh
```

Expected markers:
- `TOOLS_HOP=FAIL`
- `FAILURE_PATH_REPLAY=PASS`

---

## Task 3 — Round-013 evidence audit

```bash
python3 rounds/round-013/split-close/repos/novaic-evidence-audit/scripts/audit_round013_reports.py
```

Expected marker: `AUDIT_ROUND013=PASS`

---

## Troubleshooting matrix

| symptom | cause | fix |
|---------|-------|-----|
| `SPLIT_CONFIG_STRICT_ABORT` in startup-diagnostics | `NOVAIC_EXTERNAL_SERVICES_MODE=1` set without `NOVAIC_GATEWAY_URL` | Set `NOVAIC_GATEWAY_URL=http://<host>:<port>` |
| `DESKTOP_HOP=FAIL` | gateway unreachable | Confirm gateway running on expected port |
| `TOOLS_HOP=FAIL` | tools-server absent (expected in failure scenario) | Expected; start TRS for happy path |
| `ModuleNotFoundError: No module named 'uvicorn'` | system python3 used | Use `novaic-backend/venv/bin/python` |
| `GITLINK_FOUND` in audit | nested `.git` under control-plane path | Remove nested `.git` dir or use `git rm --cached` to de-gitlink |
| `AUDIT_ROUND013=FAIL` | missing artifact or bad repo_url | Check path exists and repo_url starts with `https://github.com/chriswangcq/` |

---

## Artifact index

| artifact | path |
|----------|------|
| test_split_config_abort.py | `novaic-control-plane/rounds/round-003/split-move/repos/novaic-desktop/scripts/test_split_config_abort.py` |
| fail_path_desktop_split_config.sh | `novaic-control-plane/rounds/round-003/split-move/repos/novaic-desktop/scripts/fail_path_desktop_split_config.sh` |
| failure-path diag (round-013) | `novaic-control-plane/rounds/round-013/split-fix/round013-failure-path-diag.txt` |
| audit_round013_reports.py | `novaic-control-plane/rounds/round-013/split-close/repos/novaic-evidence-audit/scripts/audit_round013_reports.py` |
| replay bundle | `novaic-control-plane/rounds/round-013/split-close/desktop-round013-replay-bundle.md` |
| main.rs (strict abort) | `novaic-app/src-tauri/src/main.rs` |
| split_runtime.rs | `novaic-app/src-tauri/src/split_runtime.rs` |
