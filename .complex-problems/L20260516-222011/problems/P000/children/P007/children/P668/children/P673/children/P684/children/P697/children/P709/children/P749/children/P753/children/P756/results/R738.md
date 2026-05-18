# Gateway Business Device service-code residue discovery

## Summary
Scanned active Python service code in `novaic-gateway`, `novaic-business`, and `novaic-device` for legacy/compat/fallback/direct/bypass and cross-service/device/media terms. Most hits are current guardrails or explicit boundary comments, not active old execution paths.

Confirmed current surfaces:
- `novaic-device/device/gateway_facing_api.py` documents that Gateway must not import device modules directly and forwards operations to VmControl through typed CloudBridge.
- `novaic-device/device/vmcontrol_routes.py` presents the current typed VmControl command broker. The removed historical `/vms/{vm_id}/screenshot` inline media route is not present in active code.
- `novaic-business/main_business.py` says Gateway imports are eliminated and Business is independent from Gateway.
- `novaic-business/main_subscriber.py` loads IM aggregation config at the process edge and injects it, matching the explicit dependency boundary direction.
- `novaic-gateway/main_gateway.py` keeps Gateway as HTTP/composition surface rather than business-rule host.

Candidate cleanup items for remediation:
- `novaic-business/business/internal/message.py` returns the phrase `Cancellation executed directly via Queue Service`; this is current behavior but the word `directly` can be misread as a bypass. Prefer `Cancellation requested via Queue Service`.
- `novaic-device/device/config_agents_db.py` keeps a historical CASCADE cleanup comment naming old tables such as `chat_messages`, `execution_logs`, `tasks`, `pending_questions`, `agent_runtime_state`, `pipeline_tasks`, `subagents`, and `vm_processes`. This is likely stale implementation residue and should be narrowed to current Device DB ownership.
- `novaic-device/device/entity_store.py` contains historical wording about previously talking to Entangled directly. It appears explanatory rather than active old path, but should be inspected during remediation to avoid stale boundary narration in source.

No product code was changed in this discovery ticket.
