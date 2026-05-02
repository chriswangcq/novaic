# PR-187 — Main Path Guard CI Enforcement and Stale Ticket Archival

Status: `[closed]` — 2026-05-03

## Goal

Close the remaining process gap after PR-186: the main-path acceptance guard must run from normal CI/test entrypoints, and stale historical checklist residue must not look like active work.

## Current-State Analysis

PR-186 added the right acceptance tests and root guard, but the guard was still manually invoked during closure. `.github/workflows/lint.yml` did not run `lint_agent_main_path_acceptance.sh`, `lint_retired_agent_paths.sh`, or `lint_lifecycle_loop_ownership.sh`.

The workflow also still called `scripts/ci/lint_outbox_trigger_sync.sh`, but that script no longer exists. That is exactly the kind of old branch residue this cleanup is meant to prevent.

Historical PR-90 and PR-91 were already marked deployed/closed, but each retained conditional unchecked checklist items. Those items were not current work:

- PR-90's optional lifecycle events are superseded by Cortex trace projection and Activity Timeline.
- PR-91's optional schema invariant is covered by the active docs/cache guardrail.

## Small Tickets

- [x] [PR-187A — Wire main-path guards into CI and root test entrypoint](PR-187A-wire-main-path-guards-into-ci.md)
- [x] [PR-187B — Archive stale execution-log/cache checklist residue](PR-187B-archive-stale-ticket-checklist-residue.md)

## Required Process

For each small ticket:

1. Analyze the current state.
2. Create or update the small ticket with the implementation plan.
3. Implement the smallest permanent cleanup.
4. Run the relevant guard/tests.
5. Confirm there is no open old-path ambiguity.

## Done Criteria

- [x] Normal GitHub lint fails if PR-186 main-path guard fails.
- [x] Root `scripts/run_all_tests.sh` runs the same main-path guard bundle.
- [x] The broken `lint_outbox_trigger_sync.sh` workflow reference is removed.
- [x] PR-90 and PR-91 no longer have misleading unchecked stale subtasks.
- [x] Validation commands are captured below.

## Closure

Closed 2026-05-03.

Validation:

```bash
scripts/ci/lint_agent_main_path_acceptance.sh
scripts/ci/lint_retired_agent_paths.sh
scripts/ci/lint_lifecycle_loop_ownership.sh
scripts/run_all_tests.sh
rg -n "lint_outbox_trigger_sync" .github/workflows scripts
```

Result: all guard/test commands passed; the retired workflow reference has no matches.

No production deploy was required because this ticket only changes CI/test/docs guardrails.
