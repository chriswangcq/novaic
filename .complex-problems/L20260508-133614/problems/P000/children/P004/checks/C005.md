## P004 Success Check: 旧词汇、退休注释、transitional allowlist 清理

### Summary

P004 is complete. The active runtime/business paths no longer expose the stale active-session helper names, retired prompt-splice vocabulary, or transitional allowlist marker. A dedicated lint now guards the cleaned vocabulary.

### Evidence

- `python3 scripts/ci/lint_retired_runtime_vocabulary.py` passed.
- `rg -n "list_active_sessions|rebuild_active_sessions_from_sagas|prompt-splice|prompt_splice|prompt splice|TRANSITIONAL" novaic-agent-runtime novaic-business scripts/ci --glob '!scripts/ci/lint_retired_runtime_vocabulary.py' --glob '!**/.venv/**' || true` returned no hits.
- `bash scripts/ci/lint_httpx.sh` passed during ticket execution.
- Runtime targeted tests passed: 22 tests.
- Business aggregation tests passed: 23 tests.

### Criteria Map

- Known old active-session names renamed/isolated: satisfied by `list_active_session_states` and `rebuild_session_state_from_running_sagas`.
- Retired prompt splice comments removed/rewritten: satisfied across runtime handler and tests.
- `TRANSITIONAL` allowlist residue removed: satisfied in `scripts/ci/lint_httpx.sh`.
- Tests/lints verify absence in active code paths: satisfied by `scripts/ci/lint_retired_runtime_vocabulary.py` plus targeted pytest/lint runs.

### Execution Map

- `T005` produced `R004`, covering all P004 acceptance items directly.
- No follow-up tickets were required.

### Stress Test

- The residue lint scans runtime queue service, task queue handlers/tests, business dispatch code/tests, and CI scripts. This deliberately covers the places most likely to reintroduce the old terms while avoiding archival docs and the lint script itself.

### Residual Risk

- Low. P005 still needs to wire the new lint into the broader CI matrix so this guard runs automatically instead of only manually.
