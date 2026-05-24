# Release-controller persistent state store

## Problem

Implement durable state persistence for branch heads, release runs, current and previous release pointers, candidates, and failures using atomic JSON writes under a configured state directory.

This belongs under P002 because the controller must be restart-safe before it can safely build, deploy, promote, or roll back releases.

## Success Criteria

- State store initializes the required directory structure without relying on hidden global paths.
- Branch heads can be read and written by branch name.
- Release run records can be created, updated through lifecycle states, listed, and fetched by id.
- Current and previous pointers are updated atomically when a namespace release succeeds.
- Candidate release pointers can be recorded separately from deployed namespace pointers.
- Failure details are persisted on failed runs and survive process restart.
