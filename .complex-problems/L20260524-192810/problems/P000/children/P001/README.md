# Implement first-class Release Controller quality gates

## Problem

The controller currently has a generic `deploy.verify_commands` list that is not clearly modeled as CI. A clean solution needs typed quality gates with stable names, validated commands, and branch-release plan steps that run after source checkout/submodule update and before any image build or staging deploy. This child handles the code-level model, planner ordering, runner failure semantics, and unit tests.

## Success Criteria

- Release Controller config accepts an explicit quality-gate list with stable gate names and argv commands.
- Malformed quality gates and empty commands are rejected by config validation.
- Branch release plans include named `quality-*` steps after git/submodule steps and before `build-api-backend` / `build-llm-factory`.
- Promotion and rollback plans do not include branch CI gates or image build steps.
- Nonzero quality gate exits stop subsequent build/deploy steps and surface the failed step in the release result.
- Tests cover parsing, ordering, dry-run/real runner behavior, and existing manual deploy guard behavior remains intact.
