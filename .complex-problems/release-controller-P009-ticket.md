# Implement release-controller planner and command runner

## Problem Definition

The release-controller needs deterministic planning logic that maps branch changes and manual operations to release actions without duplicating deployment behavior across API handlers. It also needs a command runner boundary that supports dry-run verification and real command execution while recording results.

## Proposed Solution

Add:

- `release_controller.planner` for branch rule matching, namespace resolution, run id creation, immutable image ref validation, branch release planning, prod promotion planning, rollback planning, and command plan construction.
- `release_controller.runner` for an injectable command runner that can execute `CommandPlan` steps or return dry-run results without touching Docker or deploy commands.

Planning should use the existing deploy contract:

- `./deploy services-image <namespace> <api-image-ref>`
- `./deploy factory-image <namespace> <factory-image-ref>`

The planner must reject prod branch automation and reject mutable image refs for prod promotion and rollback.

## Acceptance Criteria

- `main` maps to staging auto-deploy.
- `preview/*` maps to a namespace generated from the configured namespace template.
- `release/*` produces a candidate-only plan without namespace deployment.
- Branch polling/manual branch triggers cannot deploy prod.
- Prod promotion accepts digest refs and sha tags, and rejects `latest` or mutable tags.
- Rollback planning uses recorded previous pointers and rejects missing previous state clearly.
- Dry-run plans include explicit verify/build/push/deploy/smoke steps without executing commands.
- Real command execution goes through a runner that records stdout, stderr, exit code, and failure.

## Verification Plan

- Add unit tests for branch matching and namespace resolution.
- Add unit tests for immutable ref acceptance/rejection.
- Add unit tests for branch release dry-run command plans.
- Add unit tests for prod promotion planning.
- Add unit tests for rollback planning with and without previous pointers.
- Add unit tests for dry-run runner and subprocess runner failure capture.

## Risks

- The planner must not smuggle prod into an automatic branch rule.
- Command execution must remain behind the runner so tests never call Docker or deploy.
- Image ref validation must be strict enough to block mutable release inputs.

## Assumptions

- The deploy script remains the canonical deployment authority.
- Actual git polling will call planner functions later; this ticket does not need a background scheduler.
