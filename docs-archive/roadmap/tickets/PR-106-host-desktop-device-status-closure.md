# PR-106 — Close Host Desktop device status false-error fix

| Field | Value |
| --- | --- |
| **Ticket** | PR-106 |
| **Status** | `[✓]` |
| **Scope** | `novaic-app` |
| **Depends on** | PR-105 |
| **Invariant** | A transient device-status probe failure must not overwrite a known Host Desktop entity state with persistent `error`. |

## Problem

The Host Desktop device card could show `Error` even when the local desktop device was online. The UI rendered `DeviceStatusStore` over the entity state, while status polling could write `error` on a transient `get_status` failure.

## Design

- Normalize polled status values before writing them into `DeviceStatusStore`.
- On polling failure, fall back to the entity's known status instead of writing `error`.
- Ensure the visible PC client device list starts polling for the devices it renders.
- Keep the failure-normalization invariant covered by unit tests.

## Implementation Checklist

- [x] Normalize `get_status` results in `useDeviceStatusPolling`.
- [x] Preserve known entity state on probe failure.
- [x] Start polling from `PcClientDeviceList`.
- [x] Add focused unit tests for running/unknown/failure states.

## Unit Test Work

- [x] Run `npm run test:unit -- src/hooks/useDeviceStatusPolling.test.ts`.

## Smoke Test Work

- [x] Run `npm run build`.
- [x] Build and install the desktop app with `./deploy desktop`.

## Deployment Work

- [x] If App frontend artifacts are shipped through Relay, run the App/frontend deploy path after the commit.
- [x] If this is only for a local desktop build, record that no server deploy is required and that a desktop rebuild/install is the delivery path.

## GitHub / Commit Work

- [x] Commit the `novaic-app` device-status files as a PR-106-sized change.
- [x] Commit the parent repo submodule pointer in the closure commit.

## Closeout

Completed locally on 2026-04-30.

Verification:

- `cd novaic-app && npm run test:unit -- src/hooks/useDeviceStatusPolling.test.ts`
- `cd novaic-app && npm run build`
- `./deploy frontend 0.3.0`
- `./deploy desktop`

Notes:

- Frontend deploy published `https://relay.gradievo.com/resource/frontend/v0.3.0/`.
- Desktop deploy installed `/Applications/ByClaw.app`.
- Vite/Rust warnings were pre-existing and non-blocking for this fix.
- App commit: `1b68e45 fix(app): stabilize device status polling (PR-106)`.
