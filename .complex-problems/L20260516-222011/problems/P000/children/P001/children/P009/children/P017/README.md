# Fallback compatibility and TODO residue scan

## Problem

Search for stale fallback/compatibility branches, TODO/FIXME/pass/skip markers, and old migration comments that may violate the current no-backward-compatibility preference.

## Success Criteria

- Searches are bounded and exclude historical ledger noise where appropriate.
- Hits are triaged by risk and active path status.
- Tiny high-confidence cleanup is applied directly; larger issues are routed to specialized audit children.
- Result identifies whether any active old-compat code remains.
