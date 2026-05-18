# Check: Factory log boundary is safe and separated

## Summary

Success. `R587` shows factory logs are stored LLM-call records with media redaction, and the raw JSON UI renders those stored records with escaping. No monitor-preview path is involved.

## Evidence

- `R587` records scan and test artifacts:
  - `.complex-problems/L20260516-222011/tmp/p600/factory-log-boundary-scan.txt`
  - `.complex-problems/L20260516-222011/tmp/p600/factory-log-boundary-tests.txt`
- `novaic-llm-factory/factory/contracts.py:88-147` redacts provider-native image bytes in log snapshots.
- `novaic-llm-factory/factory/routes/chat_routes.py:130-160` stores request log snapshots separately from provider execution.
- `novaic-llm-factory/factory/routes/log_routes.py:40-62` bounds detail bodies returned by the logs API.
- `novaic-llm-factory/static/factory-logs.html:471-579` renders visual/raw detail from stored `request_body`/`response_body` using escaped text.
- Redaction tests passed: `3 passed in 0.18s`.

## Criteria Map

- Exact scans recorded: satisfied.
- Backend request/response persistence slices cited: satisfied.
- Frontend raw JSON detail slices cited: satisfied.
- Unexpected raw media persistence follow-up: not needed; image bytes are redacted in snapshots.

## Execution Map

- `T593` ran read-only audit plus focused factory tests.
- No code changes were needed.

## Stress Test

- Plausible failure mode: current display perception sends a base64 image to the provider and factory logs persist the entire base64 data URL.
- Covered by log snapshot tests that input data URL/base64 image payloads and assert secret base64 is absent while a redacted marker remains.

## Residual Risk

- Factory logs can show redacted provider request structure by design. This is observability, not an LLM context source.

## Result IDs

- R587
