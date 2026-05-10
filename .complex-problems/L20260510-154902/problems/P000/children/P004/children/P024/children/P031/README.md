# Phase 3.2.3: Verify root/wake/notification cutover boundaries

## Problem

After root/wake and notification events are wired, run a focused audit to ensure there is no hidden bypass for these facts and that later Phase 3 children still own unrelated context/tool/skill writes.

## Success Criteria

- Static scans identify all remaining direct writes related to root/wake/notification lifecycle and explain whether they are projection/debug-only or still pending.
- Focused tests for lifecycle and notification event writes pass.
- Full Cortex suite passes.
- Any remaining direct source-of-truth write becomes a follow-up before P024 closes.
