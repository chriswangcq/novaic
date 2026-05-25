# Complex Problem Ledger

Ledger: L20260525-153414
Schema: v6
Root: P000 - Disable automatic Release Controller branch polling
Status: done
Updated: 2026-05-25T07:54:28+00:00

## Problem Tree
- [done] P000: Disable automatic Release Controller branch polling

## Active

## Blocked

## Done
- [x] P000: Disable automatic Release Controller branch polling

## Tickets
- [done] T000: Make Release Controller CI/CD explicitly triggered -> P000 (one_go)

## Latest Checks
- [success] C000: P000 The original problem is solved: backend/factory CI/CD no longer starts from autonomous Release Controller branch polling. The live service is disabled for background polling, the new code rejects attempts to re-enable it, diagnostic polling cannot perform real releases, and explicit `/v1/triggers` remains the staging entrypoint.
