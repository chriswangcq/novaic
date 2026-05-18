# P366 Check: Finalize Diagnostics Source Map

## Verdict

`success`

## Criteria Map

- Production files/functions listed: satisfied.
- Mutating and non-mutating paths classified: satisfied.
- Identity fields and gaps identified: satisfied.
- Implementation targets for later children clear: satisfied.

## Evidence

R350 maps:

- React finalize producers.
- Wake-finalize payload builders.
- Session-ended handler/client/route/repo/ledger.
- Recovery/compensation finalize producers.
- Cortex task handler, bridge, Cortex API, workspace archive, and active-stack projection.

## Stress Test

The source map crossed repository boundaries into `novaic-cortex` because archive metadata is not fully visible from `novaic-agent-runtime` alone.

## Residual Risk

No P366-scoped residual risk. The discovered Cortex archive diagnostics gap is intentionally deferred to P368.
