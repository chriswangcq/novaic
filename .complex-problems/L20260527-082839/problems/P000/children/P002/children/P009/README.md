# Commit and push root submodule pointers and deployment ledger

## Problem

The Release Controller reads the root repo commit, so root must record updated submodule pointers for server-relevant repos and the deployment ledger state.

## Success Criteria

- Root commit includes updated submodule pointers for pushed subrepo commits and `.complex-problems` deployment/reasoning ledgers.
- Unrelated `CLAUDE.md` is not staged.
- Root `origin/main` contains the commit to trigger.
- Final root commit SHA is recorded for Release Controller trigger.
