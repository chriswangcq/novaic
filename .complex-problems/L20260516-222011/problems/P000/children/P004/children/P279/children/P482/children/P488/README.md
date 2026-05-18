# Finalize/session compatibility residue inventory

## Problem

Before deleting or tightening any finalize/session code, build a precise inventory of compatibility residue across finalize ownership, session-ended handling, attach/generation checks, recovery paths, and related tests/docs. This belongs under P482 because stale compatibility branches must be classified before removal, and because broad grep output without classification is not enough.

## Success Criteria

- Search artifacts cover finalize, session-ended, attach, generation, recovery, legacy, compat, fallback, stale, previous, and remaining-stack terms.
- Matching production files and tests are classified as active FSM behavior, adapter boundary, guard/test fixture, removable residue, or ambiguous.
- The classification identifies exact follow-up child problems when a hit is not safe to one-go delete.
- Evidence paths are saved under the ledger tmp directory.
