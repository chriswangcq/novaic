# Task Execution Policy Tables

## Problem

Task execution still encodes idempotency, retry, completion/failure, and saga adaptation as a large imperative method. Introduce explicit decision/policy units so task behavior can be tested from input snapshots.

## Success Criteria

- Task execution has explicit policy/decision helpers or tables for idempotency and failure handling.
- Tests cover duplicate completed, in-progress contention, business error, retryable error, and success scenarios at the decision/policy boundary.
- The engine uses the plan/effect substrate from P002.
- No old direct effect branch remains.
