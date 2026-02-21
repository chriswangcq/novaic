# Round 001 Migration Order (Platform)

## Extraction order

1. `novaic-shared-kernel`
2. `novaic-gateway`
3. `novaic-backend`
4. `novaic-mcp-vmuse`
5. `novaic-app`
6. `novaic-control-plane` (governance stays stable; migrate only if needed later)

## Hard dependency rationale

- `novaic-shared-kernel` must go first because service and client repos consume shared contracts.
- `novaic-gateway` follows to stabilize external API surface before downstream runtime/tooling coupling.
- `novaic-backend` depends on stable gateway-facing and shared contract boundaries.
- `novaic-mcp-vmuse` relies on runtime/tool interfaces and shared contract versions.
- `novaic-app` migrates after API/runtime/tool boundaries are fixed to avoid repeated UI-side rewiring.
- `novaic-control-plane` remains last to minimize process churn during active split execution.

## Per-step replay checks

- Confirm path ownership map exists:
  - `test -f novaic-control-plane/rounds/round-001/split-plan/repo-boundaries.md`
- Confirm shared-kernel cut list exists:
  - `test -f novaic-control-plane/rounds/round-001/split-plan/shared-kernel-cut-list.md`
- Confirm migration sequence is documented:
  - `test -f novaic-control-plane/rounds/round-001/split-plan/migration-order.md`
