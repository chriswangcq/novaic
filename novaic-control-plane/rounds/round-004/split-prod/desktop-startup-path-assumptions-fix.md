# Round 004 Desktop Startup Path Assumptions Fix

## Goal

- Make desktop startup default to split-service endpoint resolution in non-dev mode.
- Remove hardcoded local API host assumptions from desktop command/service modules.

## Code migration map

| source path | migrated change |
|---|---|
| `novaic-app/src-tauri/src/main.rs` | startup path switches to external split probe by default in release builds (`external-services` health stage) |
| `novaic-app/src-tauri/src/split_runtime.rs` | centralized split endpoint resolver (`NOVAIC_GATEWAY_URL`) and default external-mode policy |
| `novaic-app/src/services/vm.ts` | vmcontrol/websockify URLs now use configurable local hosts, not hardcoded `localhost` |
| `novaic-app/src/hooks/useVm.ts` | default VM endpoint URLs now use configurable local hosts |
| `novaic-app/src/services/scrcpyStream.ts` | scrcpy websocket URL now uses configurable local host |

## Runtime behavior change

- In debug builds, external mode remains opt-in.
- In non-dev/release builds, external split mode is the default unless explicitly overridden.
- Desktop startup now validates configured split gateway with `/api/health` and records `external-services` startup diagnostics.

## Replay marker expectations

- `SPLIT_E2E_GATEWAY_HEALTH=PASS`
- `error_timeout_count=0`
- `stages=app-bootstrap,external-services`
