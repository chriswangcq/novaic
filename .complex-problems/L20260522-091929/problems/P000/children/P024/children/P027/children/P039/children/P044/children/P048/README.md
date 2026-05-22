# Preserve Entangled row output shape under Postgres query paths

## Problem

After query generation becomes dialect-aware, verify the client-visible row shapes are preserved for JSON, BOOL, TIMESTAMP-like fields, hidden fields, `has_<hidden>` markers, and list/list_stream responses.

## Success Criteria

- JSON input/output stays dict/list/scalar compatible.
- BOOL output stays Python bool-compatible.
- TIMESTAMP-like values remain string-compatible for first cutover.
- Hidden fields are removed and `has_<hidden>` markers remain correct.
- Existing SQLite behavior remains passing.
- Fake Postgres row-shape tests cover representative outputs without requiring a production Postgres instance.
