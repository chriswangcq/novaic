# Round 003 Desktop Integration Map (Desktop Team)

## Target split repo

- repo: `novaic-app`
- repo_url: `git@github.com:chriswangcq/novaic.git`
- split branch: `add-virtual-mobile`

## Endpoint/provider mapping (split-aware)

| desktop caller | endpoint | provider repo | provider service |
|---|---|---|---|
| `novaic-app/src/services/api.ts` | `GET /api/health` | `novaic-gateway` | gateway |
| `novaic-app/src/services/api.ts` | `POST /api/chat/send` | `novaic-gateway` | gateway -> runtime pipeline |
| `novaic-app/src/store/index.ts` | `GET /api/chat/messages` (SSE) | `novaic-gateway` | gateway stream |
| `novaic-app/src/store/index.ts` | `GET /api/logs/stream` (SSE) | `novaic-gateway` | gateway log stream |
| `novaic-app/src/services/vm.ts` | `GET /api/vm/status/{agent_id}` | `novaic-gateway` | vm/routing APIs |
| `novaic-app/src/services/vm.ts` | `GET /health`, `WS /api/vms/{agent_id}/vnc` | `novaic-backend` | vmcontrol |

## Desktop runtime mode mapping

- **Bundled mode (default):**
  - Tauri host starts local backend components and uses `http://127.0.0.1:19999`.
- **Split external mode:**
  - Set `NOVAIC_EXTERNAL_SERVICES_MODE=1`
  - Set `NOVAIC_GATEWAY_URL=http://127.0.0.1:<split-gateway-port>`
  - Desktop startup probes `<gateway>/api/health` and skips monorepo-local service auto-start.

## Source-to-target migration mapping

| source (monorepo-coupled) | target (split-ready) | reason |
|---|---|---|
| `novaic-app/src-tauri/src/main.rs` (inlined gateway endpoint assumption) | `novaic-app/src-tauri/src/split_runtime.rs` | centralize external split endpoint/runtime mode parsing |
| `novaic-app/src-tauri/src/vm/deploy.rs` (`127.0.0.1:19999` hardcode) | `novaic-app/src-tauri/src/split_runtime.rs::gateway_base_url()` | make deploy flow consume split gateway endpoint |
| `novaic-app/src-tauri/src/commands/agent_commands.rs` (`AGENT_BASE_URL` hardcode) | `novaic-app/src-tauri/src/split_runtime.rs::gateway_base_url()` | align command plane calls with split gateway URL |

## Replay markers for integration acceptance

- startup marker: `external-services` stage is `ok` in startup diagnostics.
- e2e marker: desktop replay summary includes `error_timeout_count=0`.
- cross-repo marker: split gateway health returns 200 at configured external URL.
