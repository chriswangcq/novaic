# Round 002 Report - Tools Team

## Task 1
- task: Create `split-exec/tools-repo-candidate.md` with physical extraction boundaries for tools server and executor.
- evidence:
  - command: `test -f "novaic-control-plane/rounds/round-002/split-exec/tools-repo-candidate.md" && test -d "novaic-backend/tools_server" && test -f "novaic-backend/main_tools.py" && test -d "novaic-backend/scripts/tools" && test -d "novaic-backend/tests/unit/tools_server" && echo "TOOLS_REPO_CANDIDATE_CHECK:PASS"`
  - expected_marker: `TOOLS_REPO_CANDIDATE_CHECK:PASS`
  - summary: PASS - candidate extraction artifact exists and all declared source boundaries are present in current monorepo.
  - artifact_path: `novaic-control-plane/rounds/round-002/split-exec/tools-repo-candidate.md`
- status: DONE

## Task 2
- task: Create `split-exec/tools-min-dependency-list.md` with must-have dependencies and post-split compatibility constraints.
- evidence:
  - command: `python -c "import json, pathlib; root=pathlib.Path('/Users/wangchaoqun/novaic'); art=(root/'novaic-control-plane/rounds/round-002/split-exec/tools-min-dependency-list.md'); txt=art.read_text(encoding='utf-8'); tokens=['GATEWAY_URL','RUNTIME_ORCHESTRATOR_URL','VMCONTROL_URL','FILE_SERVICE_URL','TOOL_RESULT_SERVICE_URL','tools_reliability']; assert all(t in txt for t in tokens); cfg=json.loads((root/'novaic-backend/config/services.json').read_text(encoding='utf-8')); keys={'request_timeout_seconds','execution_timeout_seconds','global_timeout_seconds','max_concurrent_per_runtime'}; assert keys.issubset(cfg['tools_reliability'].keys()); print('TOOLS_MIN_DEPENDENCY_CHECK:PASS')"`
  - expected_marker: `TOOLS_MIN_DEPENDENCY_CHECK:PASS`
  - summary: PASS - minimum dependency matrix is documented and required `tools_reliability` config keys are confirmed present for post-split compatibility baseline.
  - artifact_path: `novaic-control-plane/rounds/round-002/split-exec/tools-min-dependency-list.md`
- status: DONE

## Task 3
- task: Run timeout/isolation/leak replay checks and publish baseline for candidate extraction.
- evidence:
  - command: `cd novaic-backend && bash scripts/tools/ci_preflight_probe_prereqs.sh && bash scripts/tools/leak_probe.sh && pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py tests/unit/tools_server/test_policy_doc_sync.py tests/unit/common/test_strict_config.py && echo "TOOLS_TIMEOUT_ISOLATION_LEAK_BASELINE:PASS"`
  - expected_marker: `TOOLS_TIMEOUT_ISOLATION_LEAK_BASELINE:PASS`
  - summary: PASS - preflight PASS, leak probe PASS (`fd delta=0`, `leaked=[]`), reliability/policy/config replay suite PASS (`19 passed`).
  - artifact_path: `novaic-control-plane/rounds/round-002/split-exec/tools-min-dependency-list.md`
- status: DONE

## Decision Needed (optional)
- issue:
- options:
- recommendation:
- impact:
- owner:
- target_round:

## Team status
- status: DONE
- blocker: none
