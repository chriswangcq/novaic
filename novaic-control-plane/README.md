# NovAIC Control Plane

This repository is the command center for cross-repo team execution.

It is intentionally docs-first:
- dispatch and execution are file-driven
- evidence is required for completion
- decisions are auditable

## Structure

- `governance/` shared rules and quality bars
- `rounds/` execution cycles (dispatch -> reports -> round-feedback -> redispatch -> close)
- `decisions/` ADR-style architecture and governance decisions
- `evidence-index/` stable links to execution evidence from service repos

## Core Rule

Understanding is not completion.

A task is only considered done when it includes:
1. exact command(s)
2. pass/fail summary
3. artifact/doc path

## How to start a new round

1. Copy `rounds/round-template/` to `rounds/round-XXX/`
2. Fill `00-control/round-charter.md` and `00-control/gate-criteria.md`
3. Create team dispatch files under `10-dispatch/`
4. Ask teams to report under `20-reports/`
5. Program owner writes round feedback under `30-round-feedback/`
6. Redispatch unresolved items under `40-redispatch/`
7. Close in `90-close/`
