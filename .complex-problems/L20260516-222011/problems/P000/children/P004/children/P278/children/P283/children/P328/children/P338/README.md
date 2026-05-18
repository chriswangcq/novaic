# Remaining stack and finalize reason archive boundary

## Problem

Finalize/session-ended events must record why a wake ended and what stack remained at the same generation boundary. If reason or remaining stack is recorded separately from generation checks, diagnostics and recovery can point at the wrong wake.

## Success Criteria

- Map where finalize reason, ended-at, and remaining stack are recorded.
- Verify these records are tied to explicit saga/scope/generation identity.
- Fix any path that records reason or remaining stack based on stale active lookup after generation changed.
- Add tests proving stale finalize cannot archive remaining stack for a newer wake.
- Add tests proving valid finalize records reason and remaining stack for the intended generation.

## Belongs Under

This is the observability and recovery correctness boundary for T324/P328; it ensures forced archive/debug records are trustworthy.
