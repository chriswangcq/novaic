# Round 001 Report - Tools Team

- task: Create `split-plan/tools-extraction-paths.md` for tools server, executor, and related policies.
- evidence:
  - command: `test -f "novaic-control-plane/rounds/round-001/split-plan/tools-extraction-paths.md" && echo "tools-extraction-paths: PASS"`
  - summary: PASS - extraction scope for tools server, entrypoint, scripts, and tests is documented with move/keep rules.
  - artifact_path: `novaic-control-plane/rounds/round-001/split-plan/tools-extraction-paths.md`
- status: DONE

- task: Create `split-plan/tools-runtime-deps.md` describing runtime dependencies that must remain compatible after split.
- evidence:
  - command: `test -f "novaic-control-plane/rounds/round-001/split-plan/tools-runtime-deps.md" && echo "tools-runtime-deps: PASS"`
  - summary: PASS - dependency matrix and compatibility replay checks are documented for gateway/runtime/vmcontrol/file/trs/config/policy links.
  - artifact_path: `novaic-control-plane/rounds/round-001/split-plan/tools-runtime-deps.md`
- status: DONE

- task: Run reliability/probe replay checks and capture baseline timeout/isolation evidence.
- evidence:
  - command: `cd novaic-backend && bash scripts/tools/ci_preflight_probe_prereqs.sh && bash scripts/tools/leak_probe.sh && pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py tests/unit/tools_server/test_policy_doc_sync.py tests/unit/common/test_strict_config.py`
  - summary: PASS - preflight PASS (`lsof`/`pgrep` available), leak probe PASS (`fd delta=0`, `leaked=[]`), and reliability/policy test suite PASS (`19 passed`).
  - artifact_path: `novaic-control-plane/rounds/round-001/split-plan/tools-runtime-deps.md`
- status: DONE
