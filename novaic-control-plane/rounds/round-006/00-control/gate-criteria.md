# Round 006 Gate Criteria

## Gate A - Authorized Carry-over Closure
- Desktop tasks from Round 005 must be closed with commit SHA.
- Tools/Desktop packaged-mode split wiring must show replayable PASS markers.

## Gate B - Split Operability
- Desktop startup chain in split mode passes from fresh profile.
- Tools repo-root reliability replay remains green.

## Gate C - Evidence Integrity
- Platform cross-team audit must match current report states.
- Canonical repo URL policy must pass for all teams.

## Gate D - Execution Discipline
- No template placeholders in team reports.
- Incomplete items must include owner and `target_round`.

## Fail Conditions
- desktop commit evidence still pending
- tauri packaged mode still launches monorepo tools path
- stale/incorrect cross-team audit artifact
