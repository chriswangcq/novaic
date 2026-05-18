# Gateway/App Edge Boundary Map

## Role
Gateway is a thin edge service. It owns user ingress concerns that must sit at the edge: authentication, App WebSocket push/signaling, TURN credential endpoints, Entangled sync endpoint discovery, Blob edge/control-plane helpers, and local auth-only SQLite tables.

Gateway does **not** own Business logic, Entangled schema/action authority, Queue DB/session FSM, Runtime worker execution, Device/CloudBridge execution, or Cortex context/scope state.

## Entrypoints and Launch Evidence
- `novaic-gateway/main_gateway.py`: FastAPI/uvicorn entrypoint, CLI arguments for host/port/data-dir/queue-service-url/blob-service-url/blob-upload-url/resource-dir.
- `novaic-gateway/gateway/api/routes.py`: minimal infrastructure API routes, including health.
- `novaic-gateway/gateway/api/app_client.py`: App WS endpoint and push/signaling registry.
- `scripts/start.sh`: Gateway launched on `19999` with Queue/Blob/service config.
- `novaic-app/scripts/start-backends.sh` and generated backend resource scripts: app-local launch wrappers.

## Owned Responsibilities
- Auth/JWT and `/internal/auth/*` validation.
- App WS push/signaling and Entangled endpoint discovery.
- TURN credential endpoint.
- Blob edge/control-plane routes; Gateway Python app does not own raw Blob bytes.
- Local SQLite auth store for users/tokens only.

## Explicit Non-Ownership
- Entangled owns entity sync/schema/action substrate; Gateway only gives the app endpoint discovery.
- Business owns product action hooks, internal product APIs, Environment/Subscriber, Device orchestration, and entity/action server writes.
- Device owns hardware/VM/WebRTC execution and CloudBridge typed WS broker.
- Queue Service owns `queue.db`, task/saga/session scheduling, and FSM state.
- Runtime workers execute Saga/Task/Health/Scheduler roles and call services by explicit URLs.
- Cortex owns scope/context/work trace and shell orchestration.

## Active vs Historical/Generated Notes
- Active docs such as `docs/gateway-architecture.md` and `docs/gateway/README.md` already describe Gateway as thin edge.
- `docs/architecture/service-topology.md` includes an old-vs-new comparison table. Rows such as `Gateway 负责 entity sync/schema -> Entangled...` and `Queue DB 在 Gateway -> Queue Service...` are intentional contrast, not active claims.
- Roadmap/ticket docs contain many historical Gateway decomposition references and must not be treated as active implementation truth.
- Generated app resource wrappers mirror launch behavior and should be patched only when source wrapper changes require consistency.

## P714 Cleanup Candidates
- Review whether `docs/runbooks/local-backends.md` saying the local app script only starts Gateway/Queue/Blob/workers is still current after recent service extraction work.
- Review active docs for any non-contrast wording that still says Runtime goes through Gateway for business state or Gateway owns entity schema/sync.
- If `docs/architecture/service-topology.md` old-vs-new rows confuse readers, consider adding an explicit heading that the table is "retired claim -> current truth".
