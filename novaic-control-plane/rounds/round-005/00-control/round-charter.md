# Round 005 Charter

## Window
- Round ID: round-005
- Round status: ACTIVE
- Cadence: sync and submission happen within the round

## Objective
Convert Round 004 conditional pass into full pass by closing execution gaps and hardening split-first runtime paths.

## Scope
- Complete missing Desktop executable report evidence
- Fix Tauri -> tools-server split wiring in code
- Enforce canonical repo URL reporting and stronger evidence quality
- Validate one replayable end-to-end split chain per team

## Success Criteria
- Desktop report is fully completed with code and replay evidence
- Tauri startup path uses split tools path with no monorepo fallback leak
- Every team report includes canonical repo URL and explicit source->target mapping
- One non-author replay chain per team is marked PASS
