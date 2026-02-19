# Status Codes

Use these values in dispatch, reports, review, and redispatch files.

- `PLANNED`: task is defined but not started
- `IN_PROGRESS`: execution has started
- `BLOCKED`: cannot proceed due to dependency/risk
- `DONE`: acceptance criteria met with evidence
- `DONE_WITH_GAPS`: major deliverables done, but at least one acceptance item missing
- `REJECTED`: submission does not meet required quality bar

## Required Metadata
Every task item must include:
- `owner`
- `due`
- `status`
- `evidence`
- `dependencies`
- `risk_level`
