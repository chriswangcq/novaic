# Session hidden input and duplicate config audit

## Problem

Audit environment/global hidden inputs and duplicate worker/session configuration that could keep old logic alive or make tests non-deterministic.

## Success Criteria

- Search session coordinator, workers, subscriber/dispatcher setup, and tests for implicit `os.environ`, globals, and duplicate config branching.
- Classify retained hits.
- Fix or split any risky hidden input.
