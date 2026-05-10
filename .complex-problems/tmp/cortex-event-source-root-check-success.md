# Cortex full event-sourced context source cutover check

## Result IDs

- R062

## Criteria Map

- Context lifecycle must have an event domain, durable event store, and writer: satisfied.
- Active context write APIs must emit events: satisfied.
- Active LLM context preparation must read from event projection: satisfied.
- Usage/status accounting that needs message tokens must read from event projection: satisfied.
- Legacy DFS fallback must be removed rather than retained as compatibility: satisfied.
- Legacy-only data must fail explicitly instead of silently producing stale context: satisfied.
- Old DFS renderer code and direct tests must be physically removed: satisfied.
- Full Cortex tests must pass: satisfied.

## Execution Map

- The work was split into phases for design, write model, read model, API cutover, read-path cutover, and cleanup.
- Phase 5 originally found physical old-code residue and correctly spawned a follow-up instead of accepting a partial cutover.
- The follow-up physically deleted old renderer files and direct tests, then passed focused/full verification.

## Evidence

Final production scan:

```bash
rg -n "ContextEngine|StepTree|prepare_messages_for_llm|context_stack\\.engine|context_stack\\.step_tree" novaic-cortex/novaic_cortex
```

Result: no matches.

Final full Cortex tests:

```text
430 passed
```

Final diff shape:

```text
791 insertions(+), 1903 deletions(-)
```

## Stress Test

The root check uses the strongest version of the user's constraints:

- no one-go acceptance while old code remains;
- no hidden compatibility fallback;
- old data may be deleted, so legacy-only roots should require reset;
- source guards and production scans must both agree.

The implementation meets those constraints.

## Residual Risk

The only intentional incompatibility is old roots without context events. That is not a defect under this problem's requirements; it is the selected full-cut behavior.

## Verdict

Successful.
