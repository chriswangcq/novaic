# Desktop Split-Chain Closure Bundle — Round 011

## Metadata

| field | value |
|-------|-------|
| canonical_repo_url | `https://github.com/chriswangcq/novaic` |
| branch | `add-virtual-mobile` |
| round | round-011 |
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

## Task 1 — Strict split-config abort verification

```bash
cd novaic-app/src-tauri && cargo check && echo DESKTOP_BUILD=PASS
```

Expected marker: `DESKTOP_BUILD=PASS`

```bash
grep -c "SPLIT_CONFIG_STRICT_ABORT" novaic-app/src-tauri/src/main.rs && \
  echo SPLIT_CONFIG_STRICT_ABORT_CODE_PRESENT=PASS
```

Expected marker: `SPLIT_CONFIG_STRICT_ABORT_CODE_PRESENT=PASS`

---

## Task 2 — Failure-path replay (tools unavailable)

```bash
DIAG_OUT=/tmp/r011-failure-diag.txt \
  bash novaic-app/scripts/failure_path_replay_round009.sh
```

Expected markers: `TOOLS_HOP=FAIL` `FAILURE_PATH_REPLAY=PASS`

Committed artifact: `rounds/round-011/split-fix/round011-failure-path-diag.txt`

---

## Troubleshooting matrix

| symptom | cause | fix |
|---------|-------|-----|
| `SPLIT_CONFIG_STRICT_ABORT` in startup-diagnostics | `NOVAIC_EXTERNAL_SERVICES_MODE=1` set, `NOVAIC_GATEWAY_URL` absent | Set `NOVAIC_GATEWAY_URL=http://<host>:<port>` |
| `DESKTOP_HOP=FAIL` | gateway not reachable | Confirm gateway running; check port in `NOVAIC_GATEWAY_URL` |
| `RUNTIME_HOP=FAIL` | runtime-orchestrator not running | Use `novaic-backend/venv/bin/python main_novaic.py runtime-orchestrator ...` |
| `TOOLS_HOP=FAIL` | tools-server absent or TRS dependency missing | Expected in failure-path scenario; start TRS first for happy path |
| `ModuleNotFoundError: No module named 'uvicorn'` | system python3 used | Use `novaic-backend/venv/bin/python` |
| `curl: Port number was not a decimal number between 0 and 65535` | port > 65535 | Use ports ≤ 65535 (scripts use 61993/61999) |

---

## Artifact index

| artifact | path |
|----------|------|
| failure-path diag (round-011) | `rounds/round-011/split-fix/round011-failure-path-diag.txt` |
| failure-path script | `novaic-app/scripts/failure_path_replay_round009.sh` |
| closure bundle | `rounds/round-011/split-fix/desktop-closure-bundle-round011.md` |
| main.rs strict abort | `novaic-app/src-tauri/src/main.rs` |
| split_runtime.rs | `novaic-app/src-tauri/src/split_runtime.rs` |
