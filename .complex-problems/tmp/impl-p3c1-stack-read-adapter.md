# Phase 3C1 SQLite Active Stack Read Adapter

## Problem

Runtime cutover needs one explicit adapter to read active-stack projection from operational SQLite and expose stable helpers for top frame, frame list, parent path, and response-compatible stack shape. Without this adapter, each API endpoint would duplicate SQLite row handling or keep using file-walk reads.

## Success Criteria

- Add a small read adapter/helper for SQLite active-stack projection.
- Adapter returns top-first frames and stack depth compatible with existing API responses.
- Adapter resolves current active scope path from the top frame `scope_path`, falling back to root only for empty stack.
- Adapter fails loudly for malformed non-empty frames missing `scope_path`.
- Focused tests cover empty and non-empty projections.
