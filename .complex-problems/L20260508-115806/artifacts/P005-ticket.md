# Timestamp-aware deploy smoke

## Problem Definition

Deploy verification can be fooled by stale process state or historical logs. A restart/status path that only tails logs or checks process counts can report success even when the fresh deploy did not emit expected runtime evidence after the restart boundary.

## Proposed Solution

Add a timestamp-aware deploy smoke path that captures a remote epoch before restart and verifies the critical runtime logs were updated after that boundary. Expose the same check as an explicit deploy subcommand for manual recovery, and add a local CI guard so this behavior cannot silently disappear.

## Acceptance Criteria

- Deploy restart captures a remote timestamp before restarting services and runs a fresh-log smoke check after startup.
- Manual deploy status/smoke operation can verify critical logs relative to an explicit timestamp or a recent default window.
- The check uses stable server paths and log mtimes or equivalent timestamp evidence, not stale tail output.
- CI/lint coverage fails if the timestamp-aware smoke hook is removed from deploy flow.
- Documentation explains how to run the fresh deploy smoke and why it exists.

## Verification Plan

- Static syntax check for deploy scripts.
- Run the new deploy-smoke lint locally.
- Run existing deploy/start contract lint if present.
- Confirm no stale-log-only deploy status text remains as the only verification story.

## Risks

- Some quiet workers may not emit logs immediately. The check should verify critical startup logs that are expected to update during restart rather than every possible worker shard.
- Remote shell compatibility should stay POSIX-ish and avoid dependencies beyond standard Linux utilities and Python when possible.

## Assumptions

- Runtime logs live under `/opt/novaic/data/logs`.
- The restart path starts queue-service, health, scheduler, session-outbox, saga-outbox, task, saga, subscriber, cortex, gateway, and business logs through existing scripts.
