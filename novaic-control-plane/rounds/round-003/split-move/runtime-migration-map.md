# Round 003 Runtime Migration Map (Runtime Team)

## Target repository

- repo_url: `file:///Users/wangchaoqun/split-remotes/novaic-runtime-orchestrator.git`
- working_copy: `/Users/wangchaoqun/novaic-runtime-orchestrator`
- branch: `split/round-003-runtime`
- first_split_commit_sha: `0e02a6aec003fccbf9f07346b2bae32585e46c06`

## Source -> target migrated paths

- `novaic-backend/runtime_orchestrator/**` -> `runtime_orchestrator/**`
- `novaic-backend/main_runtime_orchestrator.py` -> `main_runtime_orchestrator.py`
- `novaic-backend/common/**` -> `common/**`
- `novaic-backend/config/services.json` -> `config/services.json`
- `novaic-backend/tests/contract/test_runtime_orchestrator_process_startup.py` -> `tests/contract/test_runtime_orchestrator_process_startup.py`
- `novaic-backend/tests/contract/http_probe.py` -> `tests/contract/http_probe.py`
- `novaic-backend/tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py` -> `tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
- `novaic-runtime-orchestrator/scripts/runtime_startup_health_replay.sh` -> `scripts/runtime_startup_health_replay.sh`

## Contract ownership details

- runtime provider contract:
  - `contracts/openapi/runtime-orchestrator-internal.v1.yaml`
  - owner: `Runtime Team` (provider)
  - consumers: `API Team`, `Agent Runtime Team`, `Desktop Team`
- lifecycle/state ownership:
  - source of truth moves with code to `runtime_orchestrator/**`
  - state semantics remain contract-first and replay-gated after split
- compatibility note:
  - runtime repo does not take ownership of shared contract file location; versioned contract remains in shared contract domain.
