# agentctl IM shell command success check

## Result IDs

- R000

## Evidence

- `novaic-cortex/novaic_cortex/sandbox.py` generated `agentctl` script now implements `im` subcommands.
- `novaic-cortex/tests/test_shell_capability_runtime.py` verifies read/reply behavior from a real shell subprocess against local fake HTTP endpoints.
- Runtime and Cortex focused tests passed.

## Criteria Map

- Read command calls Environment read and checkpoints observed ids: satisfied by integration test state checks.
- Reply command enforces read-before-reply and reply cap: implemented through Cortex meta read/counter; cap counter verified by integration test.
- Send/history/search/context call matching Environment endpoints: implemented in generated script.
- File-friendly message option: `--message-file` verified by integration test.
- Commands print JSON and fail closed: implemented via JSON print and nonzero exits on validation/blocking errors.

## Execution Map

- Built command parser into generated `agentctl`.
- Reused explicit capability env from the previous ticket.
- Added local fake HTTP server test to exercise subprocess behavior rather than only source-level behavior.

## Stress Test

- The test executes two command calls in one shell command, proving the generated script can read files from RW, make HTTP calls, update Cortex meta, and call Business endpoints from inside the disposable sandbox.

## Residual Risk

- Direct external IM tools remain visible until the separate schema cutover and deletion tickets are completed.
