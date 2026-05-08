# Complex Problem Ledger

Ledger: L20260508-192710
Schema: v6
Root: P000 - Smoke Wake Shell Timeout And ImReply Cap Diagnosis
Status: done
Updated: 2026-05-08T11:52:48+00:00

## Problem Tree
- [done] P000: Smoke Wake Shell Timeout And ImReply Cap Diagnosis

## Active

## Blocked

## Done
- [x] P000: Smoke Wake Shell Timeout And ImReply Cap Diagnosis

## Tickets
- [done] T000: Diagnose smoke wake shell timeout and im_reply cap -> P000 (one_go)

## Latest Checks
- [success] C000: P000 The original failure is solved. The historical `im_reply` cap was caused by counters being written to agent-root metadata instead of wake-scope metadata, and the shell timeout was caused by Cortex sandbox setup materializing the full RO tree on every shell command. Both paths were changed, deployed, and verified with targeted unit tests plus production smoke tests.
