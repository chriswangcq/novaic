# PR-209 Agent Monitor Final Product Shape

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Product/architecture contract |
| Created | 2026-05-04 |
| Scope | `docs/roadmap/agent-monitor-final-product-shape.md`, roadmap indexes |
| Dependencies | PR-193, PR-186D, PR-208 |

## Large Work Order

Define the final product shape for Agent Monitor so later UI/runtime work has one contract to implement and review against.

## Current-state Analysis

Already true:

- Agent Monitor reads Entangled `agent-activity-records` / `agent-activity-participants`.
- Runtime projects public records from Cortex trace writes.
- App no longer uses action polling or direct Cortex HTTP read path for Monitor.
- Existing App tests cover public-surface rendering, bottom ordering, expansion, and debug redaction.

Missing before this ticket:

- A single final product-shape document for the bottom capsule and floating activity layer.
- A clear split between user-facing activity content and developer diagnostics.
- A documented acceptance matrix for Observation / Reasoning / Action / Summary.
- A follow-up list that avoids reopening the old execution-log/debug path.

## Small Tickets

### PR-209A Final Surface Contract

- Objective: define bottom capsule, activity layer, and message status boundaries.
- Scope: new final product-shape document.
- Expected result: product surfaces are specified without relying on debug UI language.
- Verification: review new document sections "Product Surfaces" and "Message Status".

### PR-209B Content Taxonomy and Projection Rules

- Objective: define what Observation, Reasoning, Action, Summary, and Failure mean in the monitor.
- Scope: new final product-shape document.
- Expected result: content categories map to source paths and forbid raw payload/debug fields.
- Verification: review taxonomy, projection, and detail expansion sections.

### PR-209C State and Acceptance Matrix

- Objective: define empty/loading/running/failed behavior plus concrete acceptance scenarios.
- Scope: new final product-shape document.
- Expected result: future UI tickets can test against a stable checklist.
- Verification: review state table and acceptance matrix.

### PR-209D Roadmap Index Wiring

- Objective: make the final shape discoverable from roadmap indexes.
- Scope: update docs index and tickets README.
- Expected result: readers can find the contract from the roadmap entry points.
- Verification: `rg` links and file paths.

## Result Review

Review checklist:

- [x] The spec says Agent Monitor is a user-facing activity channel, not diagnostics.
- [x] The spec names Entangled projection as the App read path.
- [x] The spec keeps Cortex as source trace/projection input, not UI source of truth.
- [x] The spec separates message status from monitor activity.
- [x] The spec requires latest activity in capsule and latest-bottom ordering in the layer.
- [x] The spec allows reasoning from provider `reasoning_content`.
- [x] The spec forbids raw MCP, raw HTTP, result ids, stack traces, and secrets in the public monitor.
- [x] Follow-up tickets are small and implementation-oriented.

## Verification

Commands:

```bash
git diff --check
rg -n "agent-monitor-final-product-shape|PR-209" docs/README.md docs/roadmap/agent-activity-timeline.md docs/roadmap/tickets/README.md
rg -n "result id|raw MCP|raw HTTP|stack trace|execution log" docs/roadmap/agent-monitor-final-product-shape.md
```

Expected:

- `git diff --check` passes.
- Links to the final shape document and PR-209 ticket are present.
- Debug terms appear only in negative/forbidden contexts.

## Closure

Closed as a documentation/product-contract ticket. No runtime or App behavior changed in this PR.

