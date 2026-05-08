## Ticket: Audit Runtime Wiring Deployment And Old-Path Residue

### Problem Definition

Audit whether the current runtime entrypoints, scripts, packaging, and deployed processes actually use the new unified worker/FSM substrate and whether old worker paths remain as live code, startup paths, or deployment residue.

### Proposed Solution

Inspect local runtime entrypoints, worker registry, startup scripts, packaging spec, process runner, and deployed process state. Verify retired worker entrypoints are physically absent, startup paths point at unified `main_novaic.py` modes, and live deployment matches the intended worker set.

### Acceptance Criteria

- Confirm whether retired `main_task.py`, `main_saga.py`, watchdog-style direct worker entrypoints, and old gateway flags are absent from live wiring.
- Confirm which worker modes are registered through unified runtime registry.
- Confirm deployment process layout at runtime when reachable.
- Identify stale docs/logs/scripts or supervision gaps that could make old conclusions misleading.

### Verification Plan

- Use `git status`, `test`, `rg`, and `nl` over entrypoints/scripts/specs.
- Inspect `task_queue/workers/registry.py`, `process_runner.py`, and `worker_assemblies.py` wiring points.
- Run deployment status / remote process inspection if available.

### Risks

- Runtime logs can contain stale historical errors after fixes; audit must distinguish current process state from old log residue.
- Deployment status may be reachable but not authoritative about every process role; use multiple evidence points.

### Assumptions

- Read-only runtime inspection is allowed.
- No deployment or code changes are required for this audit ticket.
