# Round 002 Desktop Repo Candidate (Desktop Team)

## Candidate repo

- target_repo: `novaic-app`
- owner_team: `Desktop Team`
- source_root_now: `novaic-app`
- extraction_mode: physical split with local startup replay baseline

## Physical extraction boundaries

| source_path | target_repo_path | owner_team | run_state |
|---|---|---|---|
| `novaic-app/src/**` | `novaic-app/src/**` | `Desktop Team` | candidate-ready |
| `novaic-app/src-tauri/src/**` | `novaic-app/src-tauri/src/**` | `Desktop Team` | candidate-ready |
| `novaic-app/src-tauri/capabilities/**` | `novaic-app/src-tauri/capabilities/**` | `Desktop Team` | candidate-ready |
| `novaic-app/scripts/validate_fresh_profile.sh` | `novaic-app/scripts/validate_fresh_profile.sh` | `Desktop Team` | candidate-ready |
| `novaic-app/package.json` | `novaic-app/package.json` | `Desktop Team` | candidate-ready |

## Backend dependency matrix (contract/runtime coupling)

| desktop surface | dependency target | dependency type | boundary rule |
|---|---|---|---|
| `src/services/api.ts` | Gateway `127.0.0.1:19999` `/api/*` | HTTP contract | consume versioned API only |
| `src/store/index.ts` | Gateway SSE (`/api/chat/messages`, `/api/logs/stream`) | stream contract | no direct backend source import |
| `src/services/vm.ts` | VmControl `127.0.0.1:19996`, Websockify `:20007` fallback | websocket/runtime endpoint | keep URL/health semantics stable |
| `src-tauri/src/main.rs` | runtime-orchestrator/file/queue/tools/tool-result services | process orchestration | startup args and health endpoints are contracts |
| `src/config/index.ts` | local port baseline (`19993-19999`) | runtime config | preserve compatibility or provide shim |

## Replay commands for candidate operability

- build replay:
  - `npm run build` (cwd: `novaic-app`)
  - expected marker: `built in`
- startup replay:
  - `ROUND_DIR="/Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-002" RUN_LABEL="round002-split-compatible" OPERATOR_ID="team-desktop" WAIT_SECONDS=20 bash "/Users/wangchaoqun/novaic/novaic-app/scripts/validate_fresh_profile.sh"`
  - expected marker: `error_timeout_count=0`

## Acceptance note

- Candidate is accepted for Round 002 when build/startup replay markers are green and report evidence paths are replayable by non-author.
