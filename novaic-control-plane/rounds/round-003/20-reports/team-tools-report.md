# Round 003 Report - Tools Team

## Task 1
- task: Migrate tools server code into `novaic-tools-server` and push first split commit.
- evidence:
  - command: `COMMIT_SHA=$(git -C novaic-tools-server rev-parse HEAD) && REMOTE_SHA=$(git -C novaic-tools-server ls-remote origin split-round-003 | awk '{print $1}') && test "$COMMIT_SHA" = "$REMOTE_SHA" && echo "TOOLS_SPLIT_COMMIT_PUSHED:PASS"`
  - expected_marker: `TOOLS_SPLIT_COMMIT_PUSHED:PASS`
  - repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
  - branch: `split-round-003`
  - commit_sha: `98ca78ddfa098ad893d97e1badf091e408e8d4f1`
  - migrated_paths: `novaic-backend/tools_server/* -> novaic-tools-server/tools_server/*; novaic-backend/common/{config,strict_config,http/clients,tools/definitions}.py -> novaic-tools-server/common/*; novaic-backend/task_queue/utils/trs_sdk.py -> novaic-tools-server/task_queue/utils/trs_sdk.py; novaic-backend/scripts/tools/* -> novaic-tools-server/scripts/tools/*; novaic-backend/tests/unit/tools_server/* -> novaic-tools-server/tests/unit/tools_server/*`
  - summary: PASS - real split repo created, first split commit generated, and commit pushed to tracked remote branch.
  - artifact_path: `novaic-control-plane/rounds/round-003/split-move/tools-migration-map.md`
- status: DONE

## Task 2
- task: Publish `split-move/tools-migration-map.md` with source->target path mapping and runtime dependency contracts.
- evidence:
  - command: `python -c "from pathlib import Path; p=Path('novaic-control-plane/rounds/round-003/split-move/tools-migration-map.md'); t=p.read_text(encoding='utf-8'); assert p.exists(); assert 'source_path | target_path' in t; assert 'split_commit_sha' in t; assert 'file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git' in t; print('TOOLS_MIGRATION_MAP_READY:PASS')"`
  - expected_marker: `TOOLS_MIGRATION_MAP_READY:PASS`
  - repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
  - branch: `split-round-003`
  - commit_sha: `98ca78ddfa098ad893d97e1badf091e408e8d4f1`
  - migrated_paths: `see mapping table in split-move/tools-migration-map.md (source -> target)`
  - summary: PASS - migration map contains path-level move table plus runtime dependency contracts and split commit metadata.
  - artifact_path: `novaic-control-plane/rounds/round-003/split-move/tools-migration-map.md`
- status: DONE

## Task 3
- task: Run timeout/isolation baseline from `novaic-tools-server` repo root and record PASS markers.
- evidence:
  - command: `cd novaic-tools-server && bash scripts/tools/ci_preflight_probe_prereqs.sh && bash scripts/tools/leak_probe.sh && pytest -q tests/unit/tools_server/test_reliability_policy.py tests/unit/tools_server/test_api_reliability_controls.py && echo "TOOLS_SERVER_SPLIT_BASELINE:PASS"`
  - expected_marker: `TOOLS_SERVER_SPLIT_BASELINE:PASS`
  - repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
  - branch: `split-round-003`
  - commit_sha: `98ca78ddfa098ad893d97e1badf091e408e8d4f1`
  - migrated_paths: `novaic-backend/scripts/tools/* + tests/unit/tools_server/* + tools_server/* -> novaic-tools-server corresponding paths`
  - summary: PASS - split repo root baseline passed (`[probe-preflight] PASS`, `[leak-probe] PASS`, `3 passed`).
  - artifact_path: `novaic-control-plane/rounds/round-003/split-move/tools-migration-map.md`
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
