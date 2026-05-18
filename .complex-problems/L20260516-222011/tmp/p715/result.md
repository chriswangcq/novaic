# Business/subscriber boundary discovery result

## Summary

Completed a read-only discovery pass for the Business service and Environment notification subscriber boundary. Business is the product/domain API and action-hook service, while the subscriber is an input-drain component that converts Environment notifications into Queue dispatch requests. This pass did not modify source code; it produced scan artifacts and a boundary map for the follow-up remediation problem.

## Done

- Inspected `novaic-business/main_business.py` and confirmed the Business service owns product-facing/internal business APIs, schema push to Entangled, and business composition around Environment/SubAgent/Device APIs.
- Inspected `novaic-business/main_subscriber.py` and `novaic-business/business/subscribers/dispatch_subscriber.py` and confirmed Environment notification dispatch is owned by the subscriber process rather than Business app lifespan.
- Confirmed subscriber responsibility is narrow: claim dispatchable Environment notifications, aggregate IM rows using an explicit config snapshot, call Queue dispatch, and acknowledge dispatch outcomes.
- Confirmed the previous implicit aggregation-env concern is not currently active in `_group_for_aggregation`: `main_subscriber.py` loads aggregation config once from `os.environ`, then passes `IMAggregationConfig` into subscriber construction.
- Mapped neighboring service boundaries: Queue owns task/saga/session FSM and durable queues; Runtime owns execution loop and tool/LLM turns; Cortex owns scope/context semantics; Gateway is thin edge/auth/WebSocket; Device/devicectl owns hardware actions.
- Reviewed key architecture docs for Business/subscriber descriptions and identified concrete candidate stale text for the remediation problem.

## Verification

- Read-only scan artifacts were generated under `.complex-problems/L20260516-222011/tmp/p715/`.
- `business-file-tree.txt` captured Business file layout for target selection.
- `business-scan.txt` captured code/doc matches under `novaic-business` for terms including subscriber, Environment, Queue, Gateway, Entangled, Device, Runtime, Cortex, env, and dispatch.
- `launch-doc-scan.txt` captured broader launch/docs references for cross-boundary stale wording.
- `env-config-scan.txt` captured environment/config references, including tests that intentionally monkeypatch env.
- Evidence reviewed from `docs/runtime-architecture.md`, `docs/gateway/README.md`, `docs/architecture/service-topology.md`, `docs/entangled-architecture.md`, and `docs/architecture/data-ownership.md`.

## Known Gaps

- `docs/entangled-architecture.md` contains potentially stale/ambiguous wording that says entity CRUD writes go through Gateway auth and are forwarded to Business. The remediation problem should classify whether this is still true or patch it to match the current topology.
- Broad launch/docs references still need active-vs-historical classification to ensure no document implies Business owns Queue/session/runtime state or that subscriber owns wake/session lifecycle.
- This ticket intentionally did not patch code or docs; cleanup belongs to `P716`.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p715/scan-commands.md`
- `.complex-problems/L20260516-222011/tmp/p715/business-file-tree.txt`
- `.complex-problems/L20260516-222011/tmp/p715/business-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p715/launch-doc-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p715/env-config-scan.txt`
