# Desktop Split-Chain Closure Bundle — Round 010

## Metadata

| field | value |
|-------|-------|
| canonical_repo_url | `https://github.com/chriswangcq/novaic` |
| branch | `add-virtual-mobile` |
| commit_sha | `49cdace72edd4c04f9259c59cdc51e6fec22400a` |
| round | round-010 |
| operator | team-desktop |
| generated_at | 2026-02-21 |

---

## Clean-clone setup (non-author reproducible)

```bash
git clone https://github.com/chriswangcq/novaic.git
cd novaic
git checkout add-virtual-mobile

# Install Rust toolchain (if not present)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# Install Node deps for frontend
cd novaic-app && npm install && cd ..

# Set up Python venv for backend replay scripts
cd novaic-backend && python3 -m venv venv && venv/bin/pip install -q -r requirements.txt && cd ..
```

---

## Task 1 — strict split-config abort verification

```bash
cd novaic-app/src-tauri && cargo check && echo DESKTOP_BUILD=PASS
```

Expected marker: `DESKTOP_BUILD=PASS`

Verify strict-abort code is present:

```bash
grep -c "SPLIT_CONFIG_STRICT_ABORT" novaic-app/src-tauri/src/main.rs && \
  echo SPLIT_CONFIG_STRICT_ABORT_CODE_PRESENT=PASS
```

Expected marker: `SPLIT_CONFIG_STRICT_ABORT_CODE_PRESENT=PASS`

---

## Task 2 — failure-path replay (tools endpoint unavailable)

```bash
DIAG_OUT=/tmp/r010-failure-diag.txt \
  bash novaic-app/scripts/failure_path_replay_round009.sh
```

Expected markers: `TOOLS_HOP=FAIL` `FAILURE_PATH_REPLAY=PASS`

---

## Task 3 — commit reachability check

```bash
python3 novaic-control-plane/rounds/round-010/split-close/repos/novaic-evidence-audit/scripts/check_commit_reachability.py
```

Expected marker: `COMMIT_REACHABILITY=PASS`

---

## Troubleshooting matrix

| symptom | cause | fix |
|---------|-------|-----|
| `SPLIT_CONFIG_STRICT_ABORT` in startup-diagnostics | `NOVAIC_EXTERNAL_SERVICES_MODE=1` set, `NOVAIC_GATEWAY_URL` absent | Set `NOVAIC_GATEWAY_URL=http://<host>:<port>` |
| `DESKTOP_HOP=FAIL` | gateway not reachable | Confirm gateway running and port matches `NOVAIC_GATEWAY_URL` |
| `RUNTIME_HOP=FAIL` | runtime-orchestrator not running | Start with `novaic-backend/venv/bin/python main_novaic.py runtime-orchestrator ...` |
| `TOOLS_HOP=FAIL` | tools-server absent or TRS missing | Expected in failure-path scenario; start TRS then tools-server for happy path |
| `ModuleNotFoundError: No module named 'uvicorn'` | system python3 used | Use `novaic-backend/venv/bin/python` |
| `curl: Port number was not a decimal number between 0 and 65535` | port > 65535 | Use ports in range 1024–65535 (scripts use 61993/61999) |
| `COMMIT_REACHABILITY=FAIL` | commits not pushed to remote | Run `git push origin add-virtual-mobile` |
| `UNREACHABLE` in reachability report | SHA not ancestor of any remote ref | Push or reference a commit that is on the remote |

---

## Artifact index

| artifact | path |
|----------|------|
| failure-path diag (round-010) | `rounds/round-010/split-fix/round010-failure-path-diag.txt` |
| failure-path script | `novaic-app/scripts/failure_path_replay_round009.sh` |
| closure bundle | `rounds/round-010/split-fix/desktop-closure-bundle-round010.md` |
| reachability script | `rounds/round-010/split-close/repos/novaic-evidence-audit/scripts/check_commit_reachability.py` |
| main.rs strict abort | `novaic-app/src-tauri/src/main.rs` |
| split_runtime.rs | `novaic-app/src-tauri/src/split_runtime.rs` |
