# agentctl and cortex CLI audit check

## Summary

P003 is solved by R004. The split child audits verified `agentctl` and `cortex` CLI output contracts separately, and neither family has an active raw artifact stdout path.

## Evidence

- P005/C002: `agentctl` paths audited and verified.
- P006/C003: `cortex payload` paths audited and verified.
- Tests across runtime and cortex covered user content rendering, shell output contract, tool output contract, shell capability auth, tool schemas, Blob payload client, context event payload writes, and step index payload reads.

## Criteria Map

- `agentctl media audio-qa` consumes Blob input and avoids raw audio stdout: satisfied by P005.
- `agentctl im` and subagent outputs remain metadata/text: satisfied by P005.
- `cortex payload` commands are bounded text-inspection tools: satisfied by P006.
- Raw artifact paths fixed or recorded: no violations found.

## Execution Map

- R004 summarizes child results R002 and R003.
- C002 and C003 provide child success checks.

## Stress Test

- The two plausible artifact vectors were independently traced: audio input is Blob-read then text-output, while payload read/search have explicit bounds.

## Residual Risk

- Global residual cleanup is intentionally handled by P004 and does not block the scoped P003 result.

## Result IDs

- R004
