# Build release-controller config and model foundation

## Problem Definition

The release-controller needs a clear package foundation before state storage, planning, and APIs can be implemented. The foundation must define validated configuration and shared domain models so later code does not rely on implicit environment guesses or loosely shaped dictionaries.

## Proposed Solution

Create a `release_controller` Python package under a dedicated repository directory. Add:

- `models.py` with dataclasses and enums for branch rules, release modes, run status, image refs, command steps, command results, release artifacts, and release runs.
- `config.py` with JSON config loading, validation, and explicit defaults only for safe local values.
- A sample config file that documents the intended shape without containing production secrets.
- A small package entrypoint module that later API and CLI code can import.

The config loader should fail loudly when required values are missing or invalid. Environment isolation should be modeled through namespace fields; service names should remain stable.

## Acceptance Criteria

- The package can be imported locally.
- Config loading supports state directory, repo path or URL, branch rules, registry image names, deploy script path, poll interval, dry-run default, and server bind settings.
- Branch rules validate that prod is not an automatic branch deployment target.
- Models capture release modes, run states, namespace targets, immutable image refs, command plans, and run records.
- Invalid config raises a deterministic exception with a useful message.

## Verification Plan

- Run a Python import check for the package.
- Run targeted unit tests for config validation and model serialization.
- Run a small local config load against the sample config.

## Risks

- Over-flexible config would recreate hidden deployment behavior; keep required fields explicit.
- Putting operational secrets in the sample config would be unsafe; keep sample values non-secret placeholders.

## Assumptions

- Runtime Docker packaging will point the service at a real config path later.
- Later slices will add state persistence, planner execution, and HTTP APIs on top of these models.
