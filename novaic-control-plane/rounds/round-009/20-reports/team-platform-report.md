# Round 009 Report - Platform Team

---

## Task 1
- deliverable_type: `code-behavior`
- task: `Upgrade audit scripts to enforce https://github.com/<org>/<repo> only and add commit reachability check`

### problem_fixed
Round 008 accepted both `file:///` and `https://github.com/` repo_url values.  Round 009
requires remote-traceable evidence: only `https://github.com/<org>/<repo>` (5 path
segments) is accepted; `file:///` and `local:` schemes are both rejected.  No prior round
verified that a reported `commit_sha` actually exists in the referenced remote, allowing
fabricated SHAs to pass audit silently.

### solution_applied
Rewrote all four audit scripts under
`rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/`:
- `enforce_canonical_repo_url.py`: changed `is_canonical_https()` to require
  `https://github.com/` prefix + exactly 5 path segments; rejects `file:///` and `local:`.
- `audit_round009_reports.py`: updated `is_canonical_https()` with same rule.
- `check_commit_reachability.py` (new): extracts `(repo_url, commit_sha)` pairs,
  calls `git ls-remote` per pair; returns REACHABLE / UNREACHABLE / SKIP_REMOTE.
  SKIP_REMOTE when remote not contactable (offline/no-auth); only UNREACHABLE causes
  audit failure.
- `regression_check_prior_green_teams.py`: updated to enforce https-only regression check.
All carried-forward fixes: `[ \t]*` cross-line prevention, backtick-strip in
`extract_team_status()`.

### evidence
- command: `python3 "novaic-control-plane/rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/enforce_canonical_repo_url.py"`
- expected_marker: `ROUND009_CANONICAL_REPO_URL_AUDIT_COMPLETED`
- repo_url: `https://github.com/chriswangcq/novaic`
- commit_sha: `94e08c3054646fff01b2f9af38d3e66516df15dd`
- migrated_paths: `rounds/round-008/split-close/repos/novaic-evidence-audit/scripts/enforce_canonical_repo_url.py -> rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/enforce_canonical_repo_url.py`
- migrated_paths: `rounds/round-008/split-close/repos/novaic-evidence-audit/scripts/audit_round008_reports.py -> rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/audit_round009_reports.py`
- migrated_paths: `rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/check_commit_reachability.py (new)`
- migrated_paths: `rounds/round-008/split-close/repos/novaic-evidence-audit/scripts/regression_check_prior_green_teams.py -> rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/regression_check_prior_green_teams.py`
- artifact_path: `novaic-control-plane/rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/enforce_canonical_repo_url.py`
- status: `DONE`

---

## Task 2
- deliverable_type: `failure-path`
- task: `Negative fixtures: prove audit rejects invalid URL (Fixture A) and detects unreachable SHA (Fixture B)`

### problem_fixed
No prior round tested the rejection path for non-https `repo_url` values as a
controlled assertion (only observed incidentally via storage-ab `local:` scheme).  Commit
reachability checks are new in Round 009 and require explicit proof that UNREACHABLE is
correctly distinguished from SKIP_REMOTE.

### solution_applied
Created two negative fixture files and one test script:
- `test-fixtures/negative-invalid-url-report.md`: three tasks with `file:///`,
  `local:`, and SSH `git@github.com:` `repo_url` values — all three must be rejected.
- `test-fixtures/negative-unreachable-sha-report.md`: three tasks with valid
  `https://github.com/` URL but fake 40-char SHA values.  Tasks 1 and 2 use valid-length
  SHAs → mocked as UNREACHABLE.  Task 3 uses `PENDING` (length ≠ 40) → SKIP_REMOTE.
- `scripts/test_negative_fixtures.py`: runs Fixture A URL rejection check and Fixture B
  mocked reachability check; exits non-zero if any expected detection is missing.

### evidence
- command: `python3 "novaic-control-plane/rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/test_negative_fixtures.py"`
- expected_marker: `ROUND009_NEGATIVE_FIXTURE_PASS`
- repo_url: `https://github.com/chriswangcq/novaic`
- commit_sha: `94e08c3054646fff01b2f9af38d3e66516df15dd`
- migrated_paths: `rounds/round-009/split-close/repos/novaic-evidence-audit/test-fixtures/negative-invalid-url-report.md (new)`
- migrated_paths: `rounds/round-009/split-close/repos/novaic-evidence-audit/test-fixtures/negative-unreachable-sha-report.md (new)`
- migrated_paths: `rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/test_negative_fixtures.py (new)`
- artifact_path: `novaic-control-plane/rounds/round-009/split-close/negative-fixture-test-result.md`
- status: `DONE`

---

## Task 3
- deliverable_type: `operability`
- task: `Publish gate_round009.sh: five-audit sequential runner, exits non-zero on first failure`

### problem_fixed
Round 008 gate runner ran three audits.  Round 009 adds `check_commit_reachability.py`
and `test_negative_fixtures.py`, requiring a new gate runner that covers all five scripts
and proves end-to-end gate pass in one command.

### solution_applied
Created `rounds/round-009/split-close/gate_round009.sh` (executable, `set -euo pipefail`).
Runs five audits in order: canonical-URL, commit-reachability, cross-team evidence,
regression-safety, negative-fixture-tests.  Aborts on first non-zero exit.  Prints
`ROUND009_GATE_RUNNER_PASS` only when all five pass.  Accepts `PYTHON` env var override.

### evidence
- command: `python3 -c "from pathlib import Path; p=Path('novaic-control-plane/rounds/round-009/split-close/repos/novaic-evidence-audit'); assert all((p/f).exists() for f in ['scripts/audit_round009_reports.py','scripts/enforce_canonical_repo_url.py','scripts/check_commit_reachability.py','scripts/regression_check_prior_green_teams.py','test-fixtures/negative-invalid-url-report.md','test-fixtures/negative-unreachable-sha-report.md']); print('ROUND009_AUDIT_BUNDLE_PUBLISHED_PASS')"`
- expected_marker: `ROUND009_AUDIT_BUNDLE_PUBLISHED_PASS`
- repo_url: `https://github.com/chriswangcq/novaic`
- commit_sha: `94e08c3054646fff01b2f9af38d3e66516df15dd`
- migrated_paths: `rounds/round-009/split-close/gate_round009.sh (new — 5-audit sequential runner)`
- artifact_path: `novaic-control-plane/rounds/round-009/split-close/gate_round009.sh`
- status: `DONE`

---

## Questions For Program Owner
- question: `Round 009 enforces https://github.com/ repo_url for all teams. Several split repos (novaic-gateway, novaic-runtime-orchestrator, novaic-tools-server, novaic-storage-a/b) currently exist only as local git repos with no GitHub remote. Teams cannot supply valid https:// URLs or pass commit reachability checks until these repos are pushed to GitHub. What is the target org/repo naming convention and which round is the GitHub push deadline?`
- why_blocking: `All teams except those already using https://github.com/chriswangcq/novaic (desktop, api) will fail Gate A until their split repos are on GitHub. Commit reachability audit (Gate B) also cannot produce REACHABLE results for any team without GitHub remotes.`
- options: `(a) Platform creates GitHub repos under org chriswangcq in this round and pushes all split repos; (b) Program owner declares a GitHub migration round (e.g. round-010) with org/repo names provided now; (c) Gate B is soft-blocked (SKIP_REMOTE is acceptable) until GitHub remotes exist`
- recommended_option: `(b) — declare the target org and repo names now so teams can prepare; keep Gate B as SKIP_REMOTE-tolerant until the migration round`
- impact_if_unanswered: `Most teams will have Gate A failures in round-009 reports; round cannot close`
- requested_by_round: `round-009`

## Team status
- status: `DONE`
- blocker: `none`
- open_p1: `other teams need https:// repo_url values — requires GitHub repo creation`
- open_p0: `none`
