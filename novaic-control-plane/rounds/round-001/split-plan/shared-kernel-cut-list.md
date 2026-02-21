# Round 001 Shared Kernel Cut List (Platform)

## Must stay shared (`novaic-shared-kernel`)

- `contracts/**`
  - Reason: cross-repo schema/contract source of truth.
- `compatibility.yaml`
  - Reason: global compatibility matrix used by multiple repos.
- Cross-repo stable DTO/error taxonomy modules under `novaic-shared-kernel/**`
  - Reason: prevents drift across gateway/runtime/tools/app.

## Must move to service repos

- Gateway-specific routing, handler logic, adapter code
  - Target: `novaic-gateway`
- Runtime lifecycle/orchestration implementation
  - Target: `novaic-backend`
- Tool execution runner and VM integration implementation
  - Target: `novaic-mcp-vmuse`
- Desktop UI and client-side orchestration
  - Target: `novaic-app`
- Round dispatch/governance/reporting model
  - Target: `novaic-control-plane`

## Move criteria

1. Service-specific implementation with no multi-repo contract responsibility must move out of shared kernel.
2. Shared kernel retains only versioned interfaces, compatibility policy, and common primitives.
3. If uncertain, default to "move to service repo" and expose only a minimal contract back in shared kernel.
