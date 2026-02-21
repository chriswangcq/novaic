# Round 004 Shared Runtime Common Migration

## Scope

Moved duplicated runtime helpers into shared package:

- target repo: `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos/novaic-shared-runtime-common`
- commit_sha: `8b18c023533e7afbdc974a4886af62538c136456`

## Migrated paths (source -> target)

- `repos/novaic-runtime-orchestrator/runtime_orchestrator/main.py` (inline health/bind logic) -> `repos/novaic-shared-runtime-common/shared_runtime_common/service_runtime.py`
- `repos/novaic-tools-server/tools_server/main.py` (inline health/bind logic) -> `repos/novaic-shared-runtime-common/shared_runtime_common/service_runtime.py`
- `repos/novaic-gateway/services/health_routes.py` (inline health payload) -> `repos/novaic-shared-runtime-common/shared_runtime_common/service_runtime.py`
- `repos/novaic-gateway/config/service_config.py` (inline bind resolution) -> `repos/novaic-shared-runtime-common/shared_runtime_common/service_runtime.py`

## Updated imports

- `repos/novaic-runtime-orchestrator/runtime_orchestrator/main.py` -> `from shared_runtime_common import build_health_payload, resolve_bind`
- `repos/novaic-tools-server/tools_server/main.py` -> `from shared_runtime_common import build_health_payload, resolve_bind`
- `repos/novaic-gateway/services/health_routes.py` -> `from shared_runtime_common import build_health_payload`
- `repos/novaic-gateway/config/service_config.py` -> `from shared_runtime_common import resolve_bind`
