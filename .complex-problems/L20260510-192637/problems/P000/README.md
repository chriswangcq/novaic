# Cortex State Authority Remediation Plan

## Problem

The previous audit concluded that Cortex mostly behaves as a state-semantic service with durable semantic authority in LogicalFS/Workspace, but several state planes remain outside the clean model:

- Redis scope locks.
- Local NDJSON scope transition log.
- Blob-backed raw payload bytes.
- Active stack/status still derived from projection files.
- LogicalFS shell view is snapshot + patch rather than live state.
- Process-level caches/config/docs residue.

The user clarified that state is allowed to exist in SQLite and maybe Redis. The goal is not "all bytes must be files"; the goal is a clean state model with explicit authority, dependency boundaries, recoverability, and no hidden in-process durable state.

This task is planning only: produce a detailed remediation design for each issue. Do not implement code changes in this pass.

## Success Criteria

- Define a clear state authority model that allows LogicalFS/Workspace, SQLite, Redis, and Blob only with explicit roles.
- For every imperfect area found in the audit, propose a concrete solution path.
- Explain which state should be authoritative, cache/projection, coordination, artifact, or observability.
- Include phased implementation strategy and verification plan.
- Avoid one-go treatment unless a subproblem is genuinely small and independently verifiable.
- Record all plan work in the solve-complex-problems ledger.
