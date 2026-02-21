# Team Bad-SHA Test Fixture (Round 010 Negative)
# Purpose: valid canonical repo_url + fake 40-char sha that does NOT exist in the local clone.
# Expected audit result for check_commit_reachability.py:
#   status = UNREACHABLE (local clone exists, sha absent)

## Task 1 — fake commit

- deliverable_type: `code/behavior`
- command: `echo fixture`
- expected_marker: `fixture`
- repo_url: `https://github.com/chriswangcq/novaic`
- branch: `main`
- commit_sha: `deadbeefdeadbeefdeadbeefdeadbeefdeadbeef`
- migrated_paths: `test-fixtures/ -> test-fixtures/`
- artifact_path: `novaic-control-plane/rounds/round-010/split-close/repos/novaic-evidence-audit/test-fixtures/negative-unreachable-sha-report.md`

## Team status

- status: `DONE`
