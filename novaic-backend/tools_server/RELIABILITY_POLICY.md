# Tools Server Reliability Policy

## Goals
- Deterministic timeout behavior for tool calls.
- Runtime-level isolation to prevent one runtime from saturating workers.
- Guaranteed cleanup on cancellation/timeout paths.

## Timeout Layers
- `request_timeout_seconds` (`NOVAIC_TOOLS_REQUEST_TIMEOUT_SECONDS`, default `300`):
  API-level timeout for `POST /internal/runtimes/{runtime_id}/tools/call`.
- `execution_timeout_seconds` (`NOVAIC_TOOLS_EXECUTION_TIMEOUT_SECONDS`, default `disabled`):
  Internal timeout enforced by `ToolExecutor.execute(...)`.
- `global_timeout_seconds` (`NOVAIC_TOOLS_GLOBAL_TIMEOUT_SECONDS`, default `1800`):
  Hard cap for all tool execution timeouts.

Resolution order:
1. Start from `execution_timeout_seconds`.
2. If tool args include `timeout`, use the tighter value.
3. Apply `global_timeout_seconds` cap.

## Isolation
- `max_concurrent_tools_per_runtime` (`NOVAIC_TOOLS_MAX_CONCURRENT_PER_RUNTIME`, default `4`)
- Each runtime gets its own semaphore in `RuntimeContext.execution_semaphore`.
- Tool calls in the same runtime share this budget; different runtimes are isolated.

## Cleanup Rules
- `ToolExecutor` returns deterministic timeout errors on `asyncio.TimeoutError`.
- On timeout, executor closes open HTTP clients to avoid leaked connections.
- API layer always closes executor in `finally` block (even when request timeout triggers).

## Recommended Production Baseline
- `NOVAIC_TOOLS_REQUEST_TIMEOUT_SECONDS=300`
- `NOVAIC_TOOLS_EXECUTION_TIMEOUT_SECONDS=` (unset for heartbeat-governed long operations)
- `NOVAIC_TOOLS_GLOBAL_TIMEOUT_SECONDS=1800`
- `NOVAIC_TOOLS_MAX_CONCURRENT_PER_RUNTIME=4`

## Environment Dependency Policy (Round 007 Decision, finalized)

**Policy Choice: Option A** — Ubuntu/Debian Linux CI + macOS local dev.

### Probe Prerequisites
`leak_probe.sh` requires `lsof`, `pgrep`, and `python3`.

| Environment         | `lsof`/`pgrep` source                          | Supported |
|---------------------|------------------------------------------------|-----------|
| Ubuntu CI runner    | Auto-installed by `ci_preflight_probe_prereqs.sh` | YES     |
| macOS local dev     | Native OS binaries                             | YES       |
| Non-Linux CI runner | No auto-install path exists                    | NO        |

### Rules
1. If a required binary is missing, `leak_probe.sh` exits immediately with an explicit
   error message and install hint. There is no silent fallback.
2. CI always calls `scripts/tools/ci_preflight_probe_prereqs.sh` before the probe to
   ensure binaries are present on Linux runners.
3. Adding a non-Linux runner to CI **requires** extending `ci_preflight_probe_prereqs.sh`
   with an OS-detection branch before the probe step may run.

### Rationale
Option A was chosen over Option B (Python fallback) and Option C (pure Python probe)
because:
- No non-Linux CI runners currently exist or are planned.
- Fail-fast behavior on missing binaries is easier to debug than a silent fallback.
- Maintenance cost of a multi-OS fallback path exceeds current benefit.

### Review Trigger
Re-evaluate this policy if a macOS or Windows CI runner is added.
Decision record: `ops-rounds/round-007/20-reports/team-tools-report.md`
