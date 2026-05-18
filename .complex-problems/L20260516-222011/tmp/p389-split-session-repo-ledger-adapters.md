# Session repo and ledger generation adapters

## Problem

`session_repo.py` and `session_ledger.py` still contain raw generation defaults in state reconstruction and ledger generation helpers. These need to be either fixed as live authority paths or classified as safe persistence adapters with tests.

## Success Criteria

- Runtime state reconstruction rejects malformed active/session state generation where it affects authority decisions.
- Ledger active generation helpers are either replaced with explicit validators or documented/test-covered as internal DB integer adapters.
- Focused session repo/ledger tests pass.
- Guard matrix classifies all remaining repo/ledger generation hits.
