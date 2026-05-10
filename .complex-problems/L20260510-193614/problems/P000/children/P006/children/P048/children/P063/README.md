# Phase 5D.3 Targeted Cortex State Authority Test Gate

## Problem

Run focused Cortex tests around the modules changed by this remediation chain: operational SQLite store/projections, scope lifecycle, active stack, payload manifest, step result projection API, and scope lock behavior.

This belongs under P048 because targeted tests localize failures before running the full suite.

## Success Criteria

- Run targeted tests for operational store and active stack projection.
- Run targeted tests for scope lifecycle / skill begin-end / status routing.
- Run targeted tests for payload manifest and step formatted projection behavior.
- Run targeted tests for scope lock manager/fail-closed behavior when available.
- Record pass/fail output and triage any failure.
