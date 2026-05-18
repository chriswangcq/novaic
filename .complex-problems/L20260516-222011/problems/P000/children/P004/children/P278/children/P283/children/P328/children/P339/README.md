# Finalize generation aggregate regression coverage

## Problem

After the targeted finalize/session-ended fixes, aggregate tests and source guards must prove the full boundary is closed and no stale compatibility residue remains.

## Success Criteria

- Build a matrix covering repository, outbox, runtime handler, remaining-stack archive, watchdog/recovery, and restart paths.
- Run focused pytest suites covering session FSM, outbox, recovery, generation checks, and legacy cleanup.
- Run source guards for missing generation defaults, direct active clear helpers, and stale fallback generation behavior.
- Record any uncovered path as a new follow-up child problem rather than declaring success.
- Close only when stale finalize/session-ended cannot clear, restart, or archive a newer active generation.

## Belongs Under

This is the final skeptical verification layer for T324/P328; it prevents partial implementation from being mistaken for full closure.
