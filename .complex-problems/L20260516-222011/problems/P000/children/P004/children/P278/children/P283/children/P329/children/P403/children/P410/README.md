# Worker and health counter classification

## Problem

Worker and health files contain many `or 0` retry/count/status patterns. These are likely non-session counters, but they should be explicitly classified so the final compatibility audit does not hide live session residue among noisy worker metrics.

## Success Criteria

- Inspect worker/health/task execution hits from P402.
- Classify each hit as retry/counter/status-code state or patch it if it affects session mutation.
- Verify no worker counter path writes attach/finalize/session-ended generation authority.
- Add tests only if a live boundary is changed.
- Record the classification matrix for final verification.
