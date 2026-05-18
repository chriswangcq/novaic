# Finalize and recovery ownership final verification

## Problem

After mapping and any remediation, P280 needs focused tests and final guard evidence proving finalize/watchdog/recovery ownership is coherent and event/FSM/outbox-oriented.

## Success Criteria

- Focused finalize, suspected-dead, recovery, saga compensation, and session-ended tests pass.
- Final guard artifacts show no unclassified ownership bypass.
- The result maps P280 success criteria to saved evidence.
- Any remaining ambiguity is turned into a follow-up problem instead of waived.
