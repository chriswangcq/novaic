# Round 001 Report - Runtime Team

- task: Create `split-plan/runtime-extraction-paths.md` listing files/folders moving to runtime repo candidate.
- evidence:
  - command: `test -f "novaic-control-plane/rounds/round-001/split-plan/runtime-extraction-paths.md" && echo "runtime-extraction-paths: PASS"`
  - summary: PASS - runtime extraction scope doc exists with move/keep boundary and consumer impact note.
  - artifact_path: `novaic-control-plane/rounds/round-001/split-plan/runtime-extraction-paths.md`
- status: DONE

- task: Create `split-plan/runtime-state-contracts.md` documenting lifecycle/state interfaces consumed by other services.
- evidence:
  - command: `test -f "novaic-control-plane/rounds/round-001/split-plan/runtime-state-contracts.md" && echo "runtime-state-contracts: PASS"`
  - summary: PASS - lifecycle states/transitions and provider-consumer contract table documented.
  - artifact_path: `novaic-control-plane/rounds/round-001/split-plan/runtime-state-contracts.md`
- status: DONE

- task: Run startup/lifecycle replay check against current branch and record baseline before extraction.
- evidence:
  - command: `cd novaic-backend && pytest -q tests/contract/test_runtime_orchestrator_process_startup.py && pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
  - summary: PASS - startup contract test `3 passed`; lifecycle consistency test `5 passed`; both replays green on current branch baseline.
  - artifact_path:
    - `novaic-backend/tests/contract/test_runtime_orchestrator_process_startup.py`
    - `novaic-backend/tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
    - `novaic-control-plane/rounds/round-001/20-reports/team-runtime-report.md`
- status: DONE
