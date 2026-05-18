# Session ledger generation helper classification

## Problem

`session_ledger.py` uses raw `int(current.get("generation") or 0)` in active generation helpers. These are DB authority helpers and must either validate stored generation explicitly or be classified as safe integer DB adapters.

## Success Criteria

- Session ledger active generation read/increment helpers validate DB generation without accepting bool/malformed values.
- Existing session ledger behavior for no row/no active state remains correct.
- Focused tests cover malformed stored generation if directly injectable, or source classification explains why SQLite schema prevents it.
- Targeted guard no longer reports unclassified session ledger generation defaults.
