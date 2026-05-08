## P005 Success Check: CI full matrix 与架构守卫门禁接入

### Summary

P005 is complete. The new retired-vocabulary guard is in GitHub lint, and the canonical local matrix now runs the runtime architecture guards before package pytest suites.

### Evidence

- `.github/workflows/lint.yml` includes `python3 scripts/ci/lint_retired_runtime_vocabulary.py`.
- `scripts/run_all_tests.sh` includes the runtime worker, deploy smoke, retired vocabulary, and start/config guards before package test commands.
- Direct guard runs passed.
- Root pytest passed.

### Criteria Map

- GitHub lint runs retired vocabulary guard: satisfied.
- Canonical local matrix runs architecture guards: satisfied.
- Guard execution is explicit and no soft-fail path was added: satisfied.
- Canonical matrix can fail on architecture residue: satisfied by direct script calls under `set -euo pipefail`.

### Execution Map

- `T006` produced `R005`, covering P005's CI wiring work.
- Complete package matrix execution is deferred to P006 final global verification by design.

### Stress Test

- Verified both declarative wiring (`rg` over workflow/runner) and direct execution of all newly required guard commands.

### Residual Risk

- Low. P006 still needs to run full global verification and catch cross-package integration issues.
