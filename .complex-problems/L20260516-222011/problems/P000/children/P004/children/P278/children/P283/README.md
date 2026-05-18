# Problem: Session generation attach and finalize boundary audit

## Problem

Audit how session generation is assigned, advanced, checked during attach, and checked during finalize/session end. Verify that stale attach/finalize events cannot mutate or close the wrong wake/session generation.

## Success Criteria

- Map generation creation and advancement paths with file references.
- Verify attach/finalize handlers require expected generation where needed.
- Identify any fallback path that accepts missing or stale generation.
