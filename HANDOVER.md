# NovAIC Current Handover

> Current-state handover only. Historical incident notes live in
> `docs/roadmap/tickets/` and must not be treated as active architecture.

## Architecture Entry Points

- System overview: `docs/README.md`
- Backend service boundaries: `docs/architecture/overview.md`
- Environment / Cortex / Runtime direction:
  - `docs/roadmap/agent-perception-action-architecture.md`
  - `docs/roadmap/agent-activity-timeline.md`
  - `docs/roadmap/agent-subject-environment-im.md`
- Roadmap ticket index: `docs/roadmap/tickets/README.md`

## Current Backend Shape

- **Business** owns product semantics and Entangled-backed domain entities:
  Environment events/messages/notifications, agents, devices, prompt/product
  context, and schema registration.
- **Runtime** owns the Agent execution loop:
  queue/session lifecycle, notification claim/finalize, LLM calls, tool
  execution, and Cortex writes.
- **Cortex** owns Agent work trajectory:
  skill/scope tree, action/observation/reasoning traces, scope summaries, and
  Blob-backed payload references. Cortex does not own product memory.
- **Blob Service** owns object storage:
  S3/OSS credentials, multipart upload/download, large payload storage, and
  object lifecycle. Other services store refs, not raw large payloads.
- **Gateway** is edge infrastructure:
  Auth, App WebSocket, file/blob proxy edge, WebRTC signaling, and sync endpoint
  discovery. It is not schema authority and not business orchestration.
- **App** reads Entangled-projected entities for product state where possible.
  The Agent Monitor reads the Entangled agent-activity projection, not a direct
  Cortex/debug endpoint.
- **VmControl / Device** execute local device and VM operations. VMControl is
  not a source of truth for Agent state.

## Current Local Commands

| Need | Command |
| --- | --- |
| Run desktop app in dev | `cd novaic-app && npm install && npm run tauri:dev` |
| Run UI only | `cd novaic-app && npm run dev` |
| Build desktop app | `cd novaic-app && npm run tauri:build` |
| Deploy backend services | `./deploy services` |
| Deploy frontend OTA | `./deploy frontend [version]` |
| Run root guard tests | `pytest` |
| Run all module tests | `./scripts/run_all_tests.sh` |

## Current Maintenance Principles

- Do not keep old branches as fallback. If the new path owns the behavior,
  physically delete the old path and add a guard.
- Do not infer long-term memory from chat replies. Continuity is explicit:
  Environment notifications drive wake, Runtime observes via tools, and Cortex
  stores observed work trajectory.
- Do not put raw large tool payloads into Cortex or Agent Monitor. Store a
  payload/blob ref plus a concise observation.
- Keep App resource bundles generated from their source repo through one sync
  script; generated Python artifacts must not enter packaged resources.
- Historical docs may remain for archaeology, but active docs and ticket index
  must describe the current path only.

## Current Cleanup Ticket

- PR-225 closed residual App/Common/docs tails:
  App VMUse resources now sync from the submodule with generated artifacts
  filtered and guarded; Common LogContext no longer exports a caller mirror;
  VMControl no longer exposes the legacy register API or Gateway SSH-port
  lookup; old roadmap checkboxes are marked as archive material.
