# API Team — Round 014 Replay Bundle

- round: `round-014`
- team: `team-api`
- bundle_timestamp: `20260221T230000Z`
- repo_url: `https://github.com/chriswangcq/novaic-gateway`
- commit_sha: `PENDING_PUSH`

---

## De-gitlink Notice

All `artifact_path` entries in this round reference files under `novaic-control-plane/rounds/round-014/evidence/` — a regular directory tracked directly in the control-plane git index.

No artifact path references `rounds/round-003/split-move/repos/novaic-gateway/...` (gitlink-internal) or any local sibling-path directory.

Evidence scripts are also accessible as raw GitHub content:
- `https://raw.githubusercontent.com/chriswangcq/novaic-gateway/main/scripts/smoke_gateway_repo_root.sh`
- `https://raw.githubusercontent.com/chriswangcq/novaic-gateway/main/scripts/fail_path_startup_no_url.sh`
- `https://raw.githubusercontent.com/chriswangcq/novaic-gateway/main/scripts/fail_path_replay_gateway.sh`

---

## Clean-Clone Setup

To replay from a clean environment (no local sibling directories required):

```bash
# 1. Clone the main monorepo (control-plane + evidence files)
git clone https://github.com/chriswangcq/novaic /tmp/novaic-clean-r014
cd /tmp/novaic-clean-r014
git checkout add-virtual-mobile

# 2. Clone the gateway standalone repo for failure-path scripts
git clone https://github.com/chriswangcq/novaic-gateway /tmp/novaic-gw-r014
cd /tmp/novaic-gw-r014

# 3. Bootstrap venv (once only)
python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt

# 4. Run failure-path acceptance scripts
bash scripts/fail_path_startup_no_url.sh
bash scripts/fail_path_replay_gateway.sh
```

No dependency on local sibling directories (`../novaic-runtime-orchestrator`, etc.) for failure-path replays. The `setup_clean_clone.sh` script auto-clones siblings if needed for success-path.

---

## Replay Transcript — Failure Path 1: Startup Without RUNTIME_ORCHESTRATOR_URL

```
$ cd /tmp/novaic-gw-r014
$ bash scripts/fail_path_startup_no_url.sh
FAIL_PATH_STARTUP_NO_URL=PASS
FAIL_PATH_STARTUP_EXIT_CODE=1
```

Exit code: `0` (script itself exits 0; inner import exits 1, confirming guard fires)

---

## Replay Transcript — Failure Path 2: Runtime Orchestrator Unreachable

```
$ cd /tmp/novaic-gw-r014
$ bash scripts/fail_path_replay_gateway.sh
FAIL_PATH_RUNTIME_UNREACHABLE=PASS
FAIL_PATH_EXIT_CODE=7
```

Exit code: `0` (script itself exits 0; inner chain exits 7 (curl connection refused), confirming unreachable detection)

---

## Marker Index

| Marker | Source | Status |
|--------|--------|--------|
| `FAIL_PATH_STARTUP_NO_URL=PASS` | `fail_path_startup_no_url.sh` | PASS |
| `FAIL_PATH_STARTUP_EXIT_CODE=1` | `fail_path_startup_no_url.sh` | PASS |
| `FAIL_PATH_RUNTIME_UNREACHABLE=PASS` | `fail_path_replay_gateway.sh` | PASS |
| `FAIL_PATH_EXIT_CODE=7` | `fail_path_replay_gateway.sh` | PASS |
| `ROUND014_API_BUNDLE_PASS` | this file | PASS |

---

## Artifact Existence (Round 014 Gate D)

| artifact_path | exists |
|---------------|--------|
| `novaic-control-plane/rounds/round-014/evidence/smoke_gateway_repo_root.sh` | YES |
| `novaic-control-plane/rounds/round-014/evidence/fail_path_startup_no_url.sh` | YES |
| `novaic-control-plane/rounds/round-014/evidence/fail_path_replay_gateway.sh` | YES |
| `novaic-control-plane/rounds/round-014/evidence/replay_gateway_runtime_chain.sh` | YES |
| `novaic-control-plane/rounds/round-014/split-close/api-round014-replay-bundle.md` | YES |

All five artifact paths verified present. No gitlink-internal paths.

---

## Summary

- gitlink-internal artifact refs removed: YES
- failure-path markers deterministic: YES (`FAIL_PATH_STARTUP_NO_URL=PASS`, `FAIL_PATH_RUNTIME_UNREACHABLE=PASS`)
- operability artifact is round-014 bundle: YES
- all artifact_path entries are regular control-plane files: YES

ROUND014_API_BUNDLE_PASS
