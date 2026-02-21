# Round 001 Tools Extraction Paths (Tools Team)

## Target repo and scope

| target_repo | owner_team | source_path | move_type | notes |
|---|---|---|---|---|
| `novaic-mcp-vmuse` | `Tools Team` | `novaic-backend/tools_server/**` | MUST_MOVE | Tools server API, executor, runtime manager, reliability policy, and runbook are tools-owned implementation. |
| `novaic-mcp-vmuse` | `Tools Team` | `novaic-backend/main_tools.py` | MUST_MOVE | Tools server entrypoint and lifecycle bootstrapping. |
| `novaic-mcp-vmuse` | `Tools Team` | `novaic-backend/scripts/tools/**` | MUST_MOVE | Probe/replay scripts and runner support policy are tools operability baseline. |
| `novaic-mcp-vmuse` | `Tools Team` | `novaic-backend/tests/unit/tools_server/**` | MUST_MOVE | Unit and policy-sync tests that gate tools reliability behavior. |
| `novaic-mcp-vmuse` | `Tools Team` | `novaic-backend/tests/unit/common/test_strict_config.py` | SPLIT_OR_SHARE | Shared config test currently validates tools reliability config keys; move or duplicate based on final config ownership. |

## Must stay in shared kernel or platform-owned locations

| source_path | owner_after_split | keep_reason |
|---|---|---|
| `contracts/**` | `novaic-shared-kernel` | Cross-repo contract source of truth; tools repo consumes but does not own. |
| `compatibility.yaml` | `novaic-shared-kernel` | Global compatibility matrix across service repos. |
| `novaic-control-plane/**` | `Platform Team` | Program governance, dispatch, and evidence process are not tools runtime code. |

## Co-migration notes

1. Move `tools_server/**`, `main_tools.py`, and `scripts/tools/**` in one batch to avoid broken script-to-module relative paths.
2. Keep test replayability by preserving command compatibility (`bash scripts/tools/leak_probe.sh`, `pytest -q tests/unit/tools_server/...`) in the target repo.
3. If strict config ownership remains in backend/shared infra, keep tests that validate `tools_reliability` fields in the owning repo and leave only tools-specific assertions in tools repo.
