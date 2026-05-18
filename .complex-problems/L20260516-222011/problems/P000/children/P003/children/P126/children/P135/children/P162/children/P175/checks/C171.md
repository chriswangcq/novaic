# Runtime read_context caller inventory and guard coverage check

## Summary

`P175` is solved. Production `read_context`/`context.read` occurrences are inventoried and classified, tests are grouped by guard purpose, and no unclassified active provider-authority caller remains.

## Evidence

- Production inventory and classification are recorded in `R157`.
- Active handler path: `context_handlers.py` as classified by `P173`.
- Active prepare handler side path: `cortex_handlers.py:302-303`, already classified by `P166` as notification-hint ingestion, not provider authority.
- Runtime continuity comments and attach behavior classified by `P174`.
- Focused tests passed with `41 passed`.

## Criteria Map

- Production occurrences inventoried/classified: satisfied.
- Test-only occurrences grouped by purpose: satisfied.
- Provider non-authority guards listed/run: satisfied.
- Unclassified production caller fixed/split: none found.

## Execution Map

- `T162` one-go executed as closing inventory after `P173` and `P174`.
- Recorded result `R157`.

## Stress Test

If new provider-authority use of `read_context` appears in `llm_handlers`, explicit contract guards fail. If prepare handler starts using `read_result.context`, PR-85 static/behavior guards fail. If context-read starts fetching bodies or scanning unread rows, by-id/order/no-replay tests fail.

## Residual Risk

- None for the inventory scope.

## Result IDs

- R157
