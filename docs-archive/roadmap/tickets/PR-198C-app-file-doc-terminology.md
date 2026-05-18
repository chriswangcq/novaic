# PR-198C — App / File Doc Terminology

| Field | Value |
|---|---|
| Status | Done |
| Parent | [PR-198](PR-198-global-service-topology-doc-cleanup.md) |
| Repo | docs |

## Task

Fix terminology in App and file docs where old Gateway paths are named imprecisely:

- File upload still uses Gateway as file proxy.
- Chat/message/product writes use Entangled actions.
- App UI docs should not reference deleted Gateway skill files as current code.

## Tests / Checks

- Grep for stale `gateway/api/skill_actions.py`, `gateway/api/vm.py`, and `POST /api/chat/send` in current architecture docs.

## Result

App/file docs now distinguish Gateway file proxy from Entangled product actions and Business skill/tool ownership.

Additional cleanup folded in: Entangled/Gateway boundary docs were rewritten so `RemoteEntityStore` and `GatewayBusinessEntityClient` only appear as retired concepts, not current paths.
