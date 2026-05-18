# Classify audit and projection generation defaults

## Problem Definition

Audit/projection modules still show raw generation defaults. These modules format observed history rather than making session authority decisions, but the residue should be explicitly classified and patched if any path is live authority.

## Proposed Solution

Run targeted guards over audit/projection modules, inspect every hit, and record whether each is a safe diagnostic projection or needs a fix. Patch only if a hit mutates live control-plane state.

## Acceptance Criteria

- All audit/projection guard hits are classified.
- No live state mutation path remains hidden in audit/projection code.
- Compile/tests are run if code is touched; otherwise read-only classification evidence is enough.

## Verification Plan

Run targeted `rg` and inspect `session_audit.py`, `queue_audit.py`, and projection helpers.

## Risks

- Over-patching audit DTO coercion could make diagnostics brittle without improving control-plane correctness.

## Assumptions

- Audit/projection code is not a write authority unless inspection proves otherwise.
