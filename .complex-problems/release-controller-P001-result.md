# Release-controller design result

## Summary

Created the release-controller architecture design at `docs/architecture/release-controller.md`.

## Evidence

- The document inventories the current image deploy substrate and API-host namespace runtime.
- It defines branch rules for `main`, `preview/*`, `release/*`, manual prod promotion, and rollback.
- It defines a durable state model under `/opt/novaic/release-controller`.
- It defines run lifecycle states, command boundaries, HTTP API, safety rules, deployment shape, non-goals, and migration steps.
- Sanity checks confirmed required sections and core rules are present.

## Verification

- `rg` found required headings and the explicit prod no-auto-deploy rule.
- A Python sanity check verified references to `main`, `staging`, `release/*`, manual promote, and existing deploy commands.

## Residual Risk

- The design assumes a local/internal registry remains available on the API host until a separate registry decision is made.
