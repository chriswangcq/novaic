# Preserve Entangled Postgres row output shape

## Problem Definition

Entangled Postgres query paths may return native JSONB values, native booleans, bytes, and timestamp-like text. Verify and preserve the same client-visible row shapes currently produced by SQLite paths, especially JSON, BOOL, TIMESTAMP-like strings, hidden-field masking, and `has_<hidden>` markers.

## Proposed Solution

1. Add focused tests around `_in` and `_out` with representative fake Postgres rows.
2. Cover JSON dict/list/scalar preservation, legacy JSON string decoding, native boolean output, timestamp string preservation, hidden field removal, and `has_<hidden>` marker computation.
3. Cover list/list_stream style output by exercising `_out` through store methods with fake DB rows.
4. Patch serialization/deserialization only if tests expose a shape mismatch.
5. Run full Entangled tests.

## Acceptance Criteria

- JSON output is dict/list/scalar compatible for both JSON strings and native decoded values.
- BOOL output is Python bool-compatible for native booleans and integer legacy values.
- TIMESTAMP-like values remain strings for first cutover.
- Hidden fields are omitted by default and `has_<hidden>` remains correct.
- List/list_stream outputs apply the same conversion.
- Existing SQLite behavior remains passing.

## Verification Plan

Run focused row-shape tests, full Entangled pytest, and py_compile if code changes are needed. Do not change production runtime or migration tooling in this child.

## Risks

- Native Postgres JSONB already arrives decoded, so double-decoding must be avoided.
- Hidden field marker behavior must not leak secret values.

## Assumptions

- P046 and P047 query-generation changes are complete.
- Real Postgres execution remains in staging validation.
