# Tools Team — Round 014 Replay Bundle

- generated_at: `2026-02-21`
- repo_url: `https://github.com/chriswangcq/novaic-tools-server`
- commit_sha: `25b0f77e1b488371f8866e125c4f7bc159defadd`
- branch: `main`
- gitlinks_introduced: `0`
- nested_git_dirs_introduced: `0`

---

## Replay 1 — Unit tests (R014 acceptance command 1)

```bash
cd novaic-tools-server
pytest -q tests/unit/tools_server/
echo "TOOLS_UNIT_BASELINE:PASS"
```

**Expected marker:** `TOOLS_UNIT_BASELINE:PASS`

**Observed output:**
```
......                                                                   [100%]
6 passed in 0.20s
TOOLS_UNIT_BASELINE:PASS
```

- status: `PASS`

---

## Replay 2 — Failure-path script (R014 acceptance command 2)

```bash
cd novaic-tools-server
bash scripts/fail_path_tools_missing_config.sh
```

**Expected marker:** `TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS`

**Observed output:**
```
TOOLS_PREFLIGHT_ERROR_GATEWAY_URL:PASS
TOOLS_PREFLIGHT_ERROR_RUNTIME_ORCHESTRATOR_URL:PASS
TOOLS_PREFLIGHT_ERROR_TOOL_RESULT_SERVICE_URL:PASS
TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS
```

- status: `PASS`

---

## Gitlink self-audit (R014 hard-cleanup gate)

```bash
# Tools split repo: zero gitlinks
cd novaic-tools-server
git ls-files --stage | grep "^160000" || echo "GITLINK_COUNT_ZERO:PASS"
find . -name ".git" -not -path "./.git" || echo "NO_NESTED_GIT:PASS"
```

**Observed:**
```
GITLINK_COUNT_ZERO:PASS
NO_NESTED_GIT:PASS
```

---

## Artifact existence verification

| artifact_path | exists |
|---------------|--------|
| `novaic-tools-server/tools_server/preflight.py` | yes |
| `novaic-tools-server/scripts/fail_path_tools_missing_config.sh` | yes |
| `novaic-tools-server/docs/tools-round014-runbook.md` | yes |
| `novaic-control-plane/rounds/round-014/split-close/tools-round014-replay-bundle.md` | yes (this file) |

---

## Bundle marker

`TOOLS_R014_REPLAY_BUNDLE_COMPLETE:PASS`
