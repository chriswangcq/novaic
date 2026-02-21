# Desktop Split-Chain Replay Bundle — Round 012

## Metadata

| field | value |
|-------|-------|
| canonical_repo_url | `https://github.com/chriswangcq/novaic` |
| branch | `add-virtual-mobile` |
| round | round-012 |
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

---

## Task 1 — Strict split-config abort (no absolute paths)

```bash
python rounds/round-003/split-move/repos/novaic-desktop/scripts/test_split_config_abort.py
```

Expected markers:
- `SPLIT_CONFIG_ABORT_PRESENT=PASS`
- `SPLIT_CONFIG_ABORT_TEST=PASS`

Also verify build:

```bash
cd novaic-app/src-tauri && cargo check && echo DESKTOP_BUILD=PASS
```

Expected marker: `DESKTOP_BUILD=PASS`

---

## Task 2 — Failure-path replay (tools unavailable, no absolute paths)

```bash
DIAG_OUT=novaic-control-plane/rounds/round-012/split-fix/round012-failure-path-diag.txt \
  bash rounds/round-003/split-move/repos/novaic-desktop/scripts/fail_path_desktop_split_config.sh
```

Expected markers:
- `TOOLS_HOP=FAIL`
- `FAILURE_PATH_REPLAY=PASS`

---

## Task 3 — Artifact existence audit

```bash
python3 rounds/round-012/split-close/repos/novaic-evidence-audit/scripts/artifact_existence_audit.py
```

Expected marker: `ARTIFACT_EXISTENCE_AUDIT=PASS`

---

## Troubleshooting matrix

| symptom | cause | fix |
|---------|-------|-----|
| `SPLIT_CONFIG_STRICT_ABORT` in startup-diagnostics | `NOVAIC_EXTERNAL_SERVICES_MODE=1` set, `NOVAIC_GATEWAY_URL` absent | Set `NOVAIC_GATEWAY_URL=http://<host>:<port>` |
| `DESKTOP_HOP=FAIL` | gateway not reachable | Confirm gateway running; check port in `NOVAIC_GATEWAY_URL` |
| `RUNTIME_HOP=FAIL` | runtime-orchestrator not running | `venv/bin/python main_novaic.py runtime-orchestrator ...` |
| `TOOLS_HOP=FAIL` | tools-server absent (expected in failure-path) | Expected; start TRS for happy path |
| `ModuleNotFoundError: No module named 'uvicorn'` | system python3 used instead of venv | Use `novaic-backend/venv/bin/python` |
| `curl: Port number not between 0 and 65535` | port > 65535 | Scripts use valid range 61993–61999 |
| `ARTIFACT_EXISTENCE_AUDIT=FAIL` | `artifact_path` in report doesn't exist on disk | Ensure artifact was committed; check path casing |

---

## Artifact index

| artifact | path |
|----------|------|
| test_split_config_abort.py | `novaic-control-plane/rounds/round-003/split-move/repos/novaic-desktop/scripts/test_split_config_abort.py` |
| fail_path_desktop_split_config.sh | `novaic-control-plane/rounds/round-003/split-move/repos/novaic-desktop/scripts/fail_path_desktop_split_config.sh` |
| failure-path diag (round-012) | `novaic-control-plane/rounds/round-012/split-fix/round012-failure-path-diag.txt` |
| artifact_existence_audit.py | `novaic-control-plane/rounds/round-012/split-close/repos/novaic-evidence-audit/scripts/artifact_existence_audit.py` |
| replay bundle | `novaic-control-plane/rounds/round-012/split-close/desktop-round012-replay-bundle.md` |
| main.rs (strict abort) | `novaic-app/src-tauri/src/main.rs` |
| split_runtime.rs | `novaic-app/src-tauri/src/split_runtime.rs` |
