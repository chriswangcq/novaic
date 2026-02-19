#!/usr/bin/env bash
set -euo pipefail

# Round 009 Runtime guard:
# enforce shared local probe helper usage through an explicit
# startup/health allowlist policy, and emit warning telemetry for
# non-allowlisted localhost probe patterns.

CONTRACT_ROOT="tests/contract"
HELPER_FILE="${CONTRACT_ROOT}/http_probe.py"
REPORT_PATH="${PROBE_GUARD_REPORT_PATH:-}"

if [[ ! -d "$CONTRACT_ROOT" ]]; then
  echo "missing contract tests directory: $CONTRACT_ROOT"
  exit 1
fi

if [[ ! -f "$HELPER_FILE" ]]; then
  echo "missing helper file: $HELPER_FILE"
  exit 1
fi

python - "$HELPER_FILE" "$CONTRACT_ROOT" "$REPORT_PATH" <<'PY'
import pathlib
import re
import sys
from datetime import datetime, timezone

helper_path = pathlib.Path(sys.argv[1])
contract_root = pathlib.Path(sys.argv[2])
report_arg = sys.argv[3] if len(sys.argv) > 3 else ""
report_path = pathlib.Path(report_arg) if report_arg else None

helper = helper_path.read_text(encoding="utf-8")

if "trust_env=False" not in helper:
    raise SystemExit(
        f"proxy-safe helper check failed: trust_env=False not found in {helper_path}"
    )

localhost_marker = re.compile(r"127\.0\.0\.1|localhost|/api/health")
httpx_verbs = re.compile(r"httpx\.(get|post|put|delete|patch)\(")
httpx_client = re.compile(r"httpx\.Client\(")

# Explicit allowlist policy: only startup/health contract tests are
# governed by strict hard-fail checks.
allowlist_patterns = ("test_*startup*.py", "test_*health*.py")
allowlisted_files: list[pathlib.Path] = []
for pattern in allowlist_patterns:
    allowlisted_files.extend(sorted(contract_root.glob(pattern)))
allowlisted_files = sorted(set(allowlisted_files))

if not allowlisted_files:
    raise SystemExit("probe safety guard misconfigured: no allowlisted files found")

checked = 0
for test_file in allowlisted_files:
    text = test_file.read_text(encoding="utf-8")

    if not localhost_marker.search(text):
        raise SystemExit(
            f"allowlisted startup/health test missing localhost marker: {test_file}"
        )

    if "from .http_probe import local_get" not in text:
        raise SystemExit(
            f"localhost probe test must import shared helper: {test_file}"
        )

    if "local_get(" not in text:
        raise SystemExit(
            f"localhost probe test must call local_get helper: {test_file}"
        )

    if httpx_verbs.search(text):
        raise SystemExit(
            f"unsafe direct httpx verb call in localhost probe test: {test_file}"
        )

    if httpx_client.search(text):
        raise SystemExit(
            f"unsafe direct httpx.Client usage in localhost probe test: {test_file}"
        )
    checked += 1

# Telemetry warnings: non-allowlisted contract tests with localhost probes
# that do not use the shared helper.
warnings: list[str] = []
all_contract_tests = sorted(contract_root.glob("test_*.py"))
allowlisted_set = {p.resolve() for p in allowlisted_files}
for test_file in all_contract_tests:
    if test_file.resolve() in allowlisted_set:
        continue
    text = test_file.read_text(encoding="utf-8")
    if localhost_marker.search(text) and "from .http_probe import local_get" not in text:
        warnings.append(
            f"non-allowlisted localhost probe without shared helper: {test_file}"
        )

for warning in warnings:
    print(f"WARN: {warning}")

summary = (
    "localhost probe safety guard passed "
    f"(allowlisted={len(allowlisted_files)}, checked={checked}, warnings={len(warnings)})"
)
print(summary)

if report_path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Runtime Localhost Probe Telemetry",
        "",
        f"- generated_at: {now}",
        f"- contract_tests_scanned: {len(all_contract_tests)}",
        f"- allowlisted_tests: {len(allowlisted_files)}",
        f"- checked_tests: {checked}",
        f"- warnings_count: {len(warnings)}",
        "",
        "## Warning Entries",
    ]
    if warnings:
        lines.extend([f"- {w}" for w in warnings])
    else:
        lines.append("- none")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"telemetry_report={report_path}")
PY

