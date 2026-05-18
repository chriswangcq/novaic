# Problem: Cortex archive projection cleanup

## Problem

Archive projection/readback paths may still walk old files or expose stale/debug-oriented shapes that should not be part of the live ContextEvent contract.

## Goal

Audit and clean archive projection helpers/read paths.

## Success Criteria

- Archive projection paths are classified.
- Live stale/debug-only projection residue is removed or isolated.
- Tests or guards prove archive projections do not reintroduce raw payload/context leakage.
