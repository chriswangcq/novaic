# Sandbox Backing Path Residue Audit Check

## Summary

Success. The audit found ephemeral backing path strings only in defensive rejection logic and tests/descriptions that prevent reuse, not in active contracts that encourage `/tmp/novaic-cortex-sandbox-*` paths.

## Evidence

- `P647-sandbox-path-scan.txt` records the backing path and stable path scans.
- `P647-sandbox-path-context.txt` shows active code rejects `novaic-cortex-sandbox-*` commands before execution.
- Builtin tool descriptions and shell capability help explicitly point to stable `/cortex/ro` and `/cortex/rw`.
- Tests assert the rejection and stable-path guidance.

## Criteria Map

- Scan output recorded: satisfied.
- Meaningful ephemeral hits classified: satisfied.
- No active user/agent-facing contract tells agents to reuse backing paths: satisfied; the active code forbids them.
- Active leaks fixed or follow-up: none found.

## Execution Map

- Ran scans for ephemeral backing paths and stable path contract terms.
- Inspected sandbox guard, guard tests, builtin tool descriptions, and shell capability help.

## Stress Test

The quoted-path rejection test covers the failure mode where an old backing path appears embedded in a shell command; the guard rejects it before execution.

## Residual Risk

Historical artifacts outside current repos can still contain old bad paths, but current code/tests/tool contracts do not expose them as usable paths.

## Result IDs

- R640
