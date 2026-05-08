## Ticket: Audit Business DSL Worker Layer

### Problem Definition

Audit whether the business worker layer has truly become a small explicit DSL over the generic worker/FSM substrate, or whether old imperative lifecycle, hidden dependencies, and direct infrastructure coupling remain in business handlers or action engines.

### Proposed Solution

Inspect worker entry modules, business handler modules, action engines, source modules, and tests. Compare current code against the target shape: business modules should declare job specs, pure-ish computation/decision handlers, and explicit dependencies; generic worker runtime should own lifecycle, polling, sleeping, shutdown, metrics, and reporting.

### Acceptance Criteria

- Identify which business modules are already small DSL/spec layers.
- Identify which modules still contain imperative orchestration or direct side effects.
- Check for lifecycle residue such as `while`, `sleep`, shutdown loops, manual polling, hidden env/time/uuid dependencies, direct DB/client construction in handler files.
- Produce achieved/gap/risk findings with file-level evidence.

### Verification Plan

- Use `wc`, `rg`, and `nl` over `task_queue/workers/*` modules.
- Inspect task/saga/health/scheduler handlers and action engines separately.
- Note whether guard tests enforce the current desired boundary or leave gaps.

### Risks

- Some side effects are legitimate business action execution rather than residue. The audit must separate "business computation/effect plan" from "generic lifecycle/control-plane behavior".
- The phrase "business only DSL" is aspirational; this ticket should not overstate completion if engines still contain direct effect orchestration.

### Assumptions

- No code changes are required for this audit ticket.
- The repository state at audit time is the evidence source.
