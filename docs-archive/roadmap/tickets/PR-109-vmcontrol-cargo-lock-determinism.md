# PR-109 — Refresh VmControl Cargo.lock deterministically

| Field | Value |
| --- | --- |
| **Ticket** | PR-109 |
| **Status** | `[✓]` |
| **Scope** | `novaic-app/src-tauri/vmcontrol` |
| **Depends on** | PR-107 |
| **Invariant** | VmControl locked builds must pass without Cargo mutating `Cargo.lock`. |

## Problem

`cargo check --offline` succeeds in `novaic-app/src-tauri/vmcontrol`, but `cargo check --locked` currently fails because `Cargo.lock` is stale relative to the current dependency graph. Running unlocked checks mutates the lockfile, which creates unrelated churn in later VmControl changes.

## Goal

- Refresh only `novaic-app/src-tauri/vmcontrol/Cargo.lock`.
- Do not change Rust or TypeScript product code in this ticket.
- Make `cargo check --locked` pass.
- Keep future VmControl diffs free of dependency-resolution noise.

## Implementation Checklist

- [x] Refresh `Cargo.lock` from the current manifest/dependency graph.
- [x] Inspect the lockfile diff as dependency maintenance, not hidden product logic.
- [x] Verify no non-lockfile files changed in `vmcontrol`.

## Unit Test / Compile Work

- [x] Run `cargo check --locked` in `novaic-app/src-tauri/vmcontrol`.

## Smoke Test Work

- [x] Run the desktop build path, or explicitly record why compile-only verification is sufficient.

## Deployment Work

- [x] If a desktop artifact is rebuilt, install it locally with `./deploy desktop`.
- [x] No backend deploy required.

## GitHub / Commit Work

- [x] Commit the `novaic-app` lockfile refresh as a PR-109-sized change.
- [x] Commit the parent repo submodule pointer and ticket update.
- [x] Push both commits.

## Closeout

Closed 2026-04-30.

Evidence:

- `cargo generate-lockfile` in `novaic-app/src-tauri/vmcontrol` refreshed only `Cargo.lock`.
- `cargo check --locked` in `novaic-app/src-tauri/vmcontrol` passed.
- `./deploy desktop` passed and installed `/Applications/ByClaw.app`.
- No backend deploy required.
