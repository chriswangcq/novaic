# Round 001 Desktop Boundary (Desktop Team)

## Target repo

- `novaic-app`

## Extraction scope (must stay/move into desktop repo)

### Frontend UI and state

- `novaic-app/src/components/**`
  - Reason: desktop UX surface (chat, visual panel, settings, onboarding, VM controls).
- `novaic-app/src/store/**`
  - Reason: client-side session/chat/log state and SSE coordination.
- `novaic-app/src/hooks/**`
  - Reason: UI lifecycle and client orchestration logic bound to desktop runtime.
- `novaic-app/src/services/**`
  - Reason: desktop-side API adapters and data shaping for UI consumption.
- `novaic-app/src/config/**`
  - Reason: desktop-local endpoint/port defaults and runtime behavior toggles.

### Tauri host/runtime shell

- `novaic-app/src-tauri/src/**`
  - Reason: desktop host process entrypoint, process supervision, local command bridge.
- `novaic-app/src-tauri/capabilities/**`
  - Reason: Tauri capability model and desktop security boundary.
- `novaic-app/src-tauri/tauri.conf.json`
  - Reason: desktop packaging/runtime config and platform metadata.

### Desktop packaging and replay scripts

- `novaic-app/package.json`
  - Reason: desktop build/packaging command surface.
- `novaic-app/scripts/validate_fresh_profile.sh`
  - Reason: startup replay baseline and operability diagnostics evidence.
- `novaic-app/scripts/build_desktop_evidence_bundle.sh`
  - Reason: CI/QA handoff artifact bundling for desktop release evidence.

## Backend coupling points (contract-only dependencies)

### Gateway API coupling

- `novaic-app/src/services/api.ts`
  - Coupling: desktop consumes Gateway endpoints (`/api/*`) via Tauri invoke bridge.
  - Contract rule: endpoint shape/version owned by API/Runtime through shared contracts; desktop remains consumer.

### Runtime and process orchestration coupling

- `novaic-app/src-tauri/src/main.rs`
  - Coupling: desktop host starts and health-checks backend service processes on fixed local ports.
  - Contract rule: process startup args and health endpoints are treated as runtime contract, not source import.

### VM/VNC coupling

- `novaic-app/src/services/vm.ts`
  - Coupling: desktop consumes VM lifecycle endpoints and vmcontrol websocket endpoints.
  - Contract rule: desktop references stable URLs/ports only; vm implementation details stay outside app repo.

## Out-of-scope (must stay outside desktop repo)

- `novaic-backend/**`
  - Runtime orchestration, gateway handlers, queue/file/tool-result services.
- `novaic-mcp-vmuse/**`
  - Tool runner and MCP execution internals.
- `contracts/**`, `compatibility.yaml`, `novaic-shared-kernel/**`
  - Shared contracts, compatibility policy, and common primitives.

## Boundary guardrails for split

1. Desktop repo must not import sibling repo code by relative file path.
2. Cross-repo integration must use versioned contract/API boundaries.
3. Any desktop-facing endpoint/process contract change requires impact notes from API and Runtime teams.
