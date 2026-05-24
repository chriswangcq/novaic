# Release-controller branch planner and command runner

## Problem

Implement the core planning logic that maps branch changes and manual requests to deterministic release actions, validates immutable refs, and turns actions into verification/build/publish/deploy command plans that can run in dry-run or real execution mode.

This belongs under P002 because this is the controller's release brain: API and polling should call into this module instead of duplicating deployment rules.

## Success Criteria

- Branch rules map `main` to staging auto-deploy, `preview/*` to preview namespace auto-deploy, and `release/*` to candidate-only behavior.
- Branch polling or branch-triggered runs cannot deploy prod.
- Prod promotion accepts only digest refs or sha tags and rejects `latest` or mutable semantic tags.
- Rollback planning uses recorded previous pointers and validates immutable image refs.
- Dry-run planning emits explicit command steps without executing host commands.
- Real execution goes through an injectable command runner that records stdout, stderr, exit code, and failures.
