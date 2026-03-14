# Agent Runtime Diagnostics Policy (Stable Governance)

## Scope
This policy defines normative defaults for idempotency ledger diagnostics.
It is a stable governance artifact and must not rely only on round-specific reports.

## Ownership
- Owner: Agent Runtime Team
- Reviewers: Runtime Team, Platform Team
- Change control: any breaking/default change requires documented review in round report and reviewer sign-off.

## Normative Defaults
- Default query limit: `20`
- Maximum query limit: `200`
- Default diagnostics scope: `only_contended=true`

## Frequency Policy
- Incident mode: run diagnostics every `5m`
- Routine mode: run diagnostics every `60m`

## Retention Policy
- Retain contention evidence snapshots/log exports for at least `7d`
- Retain replay command outputs in CI artifacts for at least `14d`

## Drift Rule
- Runbook and implementation checks must remain aligned with this document.
- CI policy check must fail when defaults drift from this governance file.
