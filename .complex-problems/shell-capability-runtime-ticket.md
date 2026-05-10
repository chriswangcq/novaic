# Implement sandbox capability command substrate

## Problem Definition

The Cortex sandbox currently gives agents a shell, stable `/cortex/*` paths, and environment variables, but lacks a small durable command surface for runtime/cortex operations. This blocks the intended boundary where interface tools can live inside shell while the external harness stays minimal.

## Proposed Solution

Add a tiny command substrate generated into each disposable sandbox:

- `agentctl`
- `runtimectl`
- `cortex`

The substrate should be created in a sandbox-private bin directory prepended to `PATH`. It should avoid imports from the source tree at runtime, read config from `.novaic_env.json`/environment, and support reliable help commands immediately.

## Acceptance Criteria

- `command -v agentctl runtimectl cortex` succeeds in a fresh Cortex shell.
- `agentctl --help`, `runtimectl --help`, and `cortex payload --help` exit successfully.
- Help commands do not reference or leak `/tmp/novaic-cortex-sandbox-*` paths in stdout/stderr.
- Help commands do not force RO materialization just because they are used.
- Unit tests cover command presence and help behavior.

## Verification Plan

- Add focused Cortex tests around sandbox shell execution.
- Run the new test file.
- Run a nearby sandbox/path safety test set if available.

## Risks

- If wrappers depend on installed package entry points, source-tree tests can fail because sandbox `cwd` is RW, not the repo root.
- If wrapper output includes ephemeral paths, it violates the stable-path contract.
- If command detection accidentally references `/cortex/ro`, help smoke tests could reintroduce slow RO loading.

## Assumptions

- The first implementation can expose help and substrate wiring before richer `agentctl`/`runtimectl` subcommands are added.
- Rich behavior should be implemented incrementally behind the same command substrate rather than as direct non-shell tools.
