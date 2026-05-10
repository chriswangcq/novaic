# Phase 5B Remove Dead Local Authority Code

## Problem

Live source and tests must not keep old local authority paths after SQLite/LogicalFS/manifest cutovers. Any remaining local NDJSON transition authority, active-stack file walking, temp-path authority, or compatibility fallback code should be physically removed rather than left as confusing residue.

## Success Criteria

- Remove or prove absent live local transition-log authority code.
- Remove or prove absent live active-stack file walking authority code.
- Delete compatibility branches that only support pre-cutover behavior and are not required by current tests.
- Adjust tests to assert current authority paths instead of legacy helpers.
- Run targeted tests covering scope lifecycle, active stack projection, operational store, workspace, and context event APIs.
