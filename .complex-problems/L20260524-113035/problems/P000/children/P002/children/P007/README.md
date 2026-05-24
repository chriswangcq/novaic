# Release-controller config and model foundation

## Problem

Create the release-controller package foundation with explicit configuration loading and typed domain models for branch rules, run states, image refs, namespaces, and command plans.

This belongs under P002 because every later core service slice depends on the same validated configuration and shared model vocabulary.

## Success Criteria

- A clear release-controller package exists in the repository.
- Config loading supports repo path or URL, branch rules, registry image names, deploy script path, poll interval, dry-run default, state directory, and server bind settings.
- Branch rule models preserve stable service names and isolate environments through namespace.
- Run state and command plan models are explicit enough for state persistence, planner, and API modules to share.
- Invalid configuration fails loudly with a useful error instead of falling back to implicit defaults.
