# Remove Root Scratch From Workspace Initialization

## Problem Definition

`Workspace.initialize()` still creates `/rw/scratch/.keep` by default. That makes the old global scratch path part of the Workspace default layout even though current shell scratch is subagent-aware.

## Proposed Solution

Remove `/rw/scratch` from `Workspace.initialize()` and update the direct initialization layout test so it no longer expects root scratch. Do not rewrite broad test fixtures in this ticket; that belongs to P639.

## Acceptance Criteria

- `Workspace.initialize()` no longer initializes `/rw/scratch`.
- Direct layout assertion tests pass and do not expect `rw/scratch`.
- No unrelated code is changed.

## Verification Plan

Run a focused scan of `Workspace.initialize()` and run `tests/test_workspace.py::test_initialize_creates_layout` plus nearby workspace initialization tests.

## Risks

- Some tests may rely on `/rw/scratch/.keep` being present; P639 will address broader fixture rewrites if they surface.

## Assumptions

- Arbitrary writes under `/rw/...` do not require pre-created directories because the storage authority creates parent paths on write.
