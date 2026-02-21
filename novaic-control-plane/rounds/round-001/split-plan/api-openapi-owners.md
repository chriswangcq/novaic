# Round 001 OpenAPI Ownership Map (API Team)

## Contract file ownership (post-split target)

| openapi_file | api_scope | target_repo | primary_owner_team | co_review_team | reason |
|---|---|---|---|---|---|
| `contracts/openapi/gateway-public.v1.yaml` | Gateway external/public API | `novaic-gateway` | `API Team` | `Platform Team` | External API compatibility is gateway-owned and should evolve with API repo release cadence. |
| `contracts/openapi/runtime-orchestrator-internal.v1.yaml` | Runtime internal API consumed by gateway | `novaic-backend` | `Runtime Team` | `API Team` | Runtime service defines provider contract; API is key downstream consumer and must co-review breaking risk. |
| `contracts/openapi/storage-contracts.v1.yaml` | Storage contract baseline | `novaic-shared-kernel` | `Storage-A/B Team` | `API Team`, `Runtime Team` | Multi-repo shared contract should stay in shared-kernel governance path. |

## Ownership guardrails

1. Primary owner approves version bump and release note for its contract file.
2. Co-review team approval is required for breaking or behavior-changing contract updates.
3. Contract files stay versioned (`v1`, `v2`, ...) and cannot be replaced in place for breaking changes.
