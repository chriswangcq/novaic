# Check: Sandbox Core Final Extraction

## Criteria Map

- Independent `novaic-sandbox-core` package exists and owns sandbox substrate: success.
- Cortex and sandboxd import `sandbox_core`: success.
- `novaic-common/common/sandbox` physically removed: success.
- Tests moved and pass: success.
- Start/deploy/test scripts explicitly include sandbox-core: success.
- No `common.sandbox` import residue: success.

## Evidence

- `novaic-sandbox-core/sandbox_core` contains contracts, client, process, mount namespace, and filesystem modules.
- `find novaic-common/common -maxdepth 2 -type d -name sandbox -print` returned no paths.
- `find novaic-common/tests -maxdepth 1 -name test_sandbox_infra.py -print` returned no paths.
- `rg -n "common\\.sandbox|common/sandbox" . --glob '!**/.git/**' --glob '!**/__pycache__/**' --glob '!**/.venv/**'` returned no matches.
- Targeted tests, common tests, shell syntax checks, import smoke, and local sandboxd live smoke passed.

## Verdict

Success. The old `common.sandbox` half-state is gone, active runtime wiring points at `novaic-sandbox-core`, and every restart path that can invoke `start.sh` now deploys the sandbox substrate and daemon first.
