# Retry final quality-gated staging release

## Problem

The controller image and runtime dependencies are now fixed, but the real quality-gated staging rollout must be retried for commit `491bd7e6ad55a70d96f41d0fbfea872be72e92e8` and verified end to end.

## Success Criteria

- `/v1/polls/once` creates a successful staging run for commit `491bd7e6ad55a70d96f41d0fbfea872be72e92e8`.
- The run command plan and execution evidence show `quality-release-controller-ci` and `quality-release-path-lints` before build/deploy, both successful.
- Staging public health passes after the run.
- Prod current pointer remains on commit `e4fb5740cc8481617bcd3d9f2928d7f4ebf586df` unless explicitly promoted.
- Polling is re-enabled with `last_error=null` and main head recorded/skipped as unchanged.
- Direct manual `services-image` and `factory-image` calls still fail locally before remote side effects.
