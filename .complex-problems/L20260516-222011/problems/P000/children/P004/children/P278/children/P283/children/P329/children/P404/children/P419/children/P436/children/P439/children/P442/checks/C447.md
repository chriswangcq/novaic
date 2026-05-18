# Check: P442 materialized context owner classification

## Verdict

Success.

## Evidence Reviewed

- Result `R421`
- Materialized context direct/member hit scans.
- Source slices for runtime handlers, bridge-owned projection calls, workspace helpers, and Cortex endpoints.

## Criteria Map

- Every live hit classified: satisfied.
- Unresolved/misleading names routed to later children: satisfied.
- No code changes made in classification: satisfied.

## Execution Map

The classification distinguishes legitimate projection maintenance from authoritative LLM prepare. It also identifies exactly where cleanup should happen next: bridge helper naming (P443), runtime handler contract clarity (P444), and Cortex endpoint/test cleanup (P445).

## Stress Test

The scan included both function-call syntax and mock/member usage so tests like `bridge.read_context.return_value` were not missed.

## Residual Risk

No classification gap remains. Actual cleanup remains for P443/P444/P445.
