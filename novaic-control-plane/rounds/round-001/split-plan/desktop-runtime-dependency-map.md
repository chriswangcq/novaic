# Round 001 Desktop Runtime Dependency Map (Desktop Team)

## Scope

- Map desktop startup/process orchestration and endpoint dependencies for repo split safety.

## Local process dependency graph

### Desktop host process

- `novaic-app/src-tauri/src/main.rs`
  - Root supervisor process (Tauri app host).
  - Performs startup diagnostics and port preflight before service boot.

### Managed backend-side local services (started/observed by desktop host)

- Runtime Orchestrator: `127.0.0.1:19993`
- Tool Result Service: `127.0.0.1:19994`
- File Service: `127.0.0.1:19995`
- VmControl: `127.0.0.1:19996`
- Queue Service: `127.0.0.1:19997`
- Tools Server: `127.0.0.1:19998`
- Gateway: `127.0.0.1:19999`

## Client endpoint dependency map

### Gateway HTTP API (`/api/*`)

- Primary adapter: `novaic-app/src/services/api.ts`
- Main dependency groups:
  - health/config (`/api/health`, `/api/config*`)
  - agent lifecycle/model (`/api/agents*`)
  - chat/history/interrupt (`/api/chat/*`, `/api/agent/interrupt`)
  - logs and diagnostics (`/api/logs/*`)
  - skills/tools config (`/api/skills*`, `/api/tools/categories`)
  - VM and device orchestration (`/api/vm/*`, `/api/devices/*`)
  - file upload and retrieval (`/api/files/*`, `/api/images/*`)

### Streaming dependencies

- Chat SSE: `${GATEWAY_URL}/api/chat/messages`
- Execution-log SSE: `${GATEWAY_URL}/api/logs/stream`
- Source owner: `novaic-app/src/store/index.ts`

### VM/VNC runtime dependencies

- VM lifecycle adapter: `novaic-app/src/services/vm.ts`
- Preferred VNC path:
  - health probe: `http://localhost:19996/health`
  - websocket: `ws://localhost:19996/api/vms/{agent_id}/vnc`
- Fallback VNC path:
  - `ws://localhost:20007/websockify`

## Startup baseline and replay observability

### Startup diagnostics artifact

- Location contract: `$APP_DATA/logs/startup-diagnostics.jsonl`
- Baseline stages:
  - `app-bootstrap`
  - `cleanup`
  - `port-preflight`
  - `runtime-orchestrator`
  - `gateway`
  - `vmcontrol`
  - `queue-service`
  - `file-service`
  - `tool-result-service`

### Replay command (desktop team baseline)

- `ROUND_DIR="novaic-control-plane/rounds/round-001" RUN_LABEL="round001-baseline" OPERATOR_ID="team-desktop" WAIT_SECONDS=20 bash "novaic-app/scripts/validate_fresh_profile.sh"`

## Split risks and contract controls

1. **Port coupling risk:** desktop currently assumes fixed localhost ports; split must preserve service discovery contract or provide compatibility shim.
2. **API breadth risk:** desktop binds many gateway routes from one adapter file; endpoint version drift must be protected by contract tests.
3. **Startup order risk:** desktop host supervises multi-service boot; runtime teams must keep health semantics stable to prevent false startup failure.
