#!/usr/bin/env python3
"""
test_split_config_abort.py — verifies SPLIT_CONFIG_STRICT_ABORT logic is present
in the desktop Rust source tree.

Run from anywhere inside the monorepo; resolves paths relative to this script's
own location (no hard-coded absolute paths).

Expected output:
  SPLIT_CONFIG_ABORT_PRESENT=PASS
  SPLIT_CONFIG_ABORT_TEST=PASS
"""

import pathlib
import sys

# Resolve repo root: this script lives at
#   <repo>/novaic-control-plane/rounds/round-003/split-move/repos/novaic-desktop/scripts/
# The repo root is 7 parents up.
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[6]  # 7 levels up to monorepo root

# SPLIT_CONFIG_STRICT_ABORT is emitted in main.rs (the startup abort path).
# split_runtime.rs contains validate_split_config() / gateway_url_explicit()
# which are the underlying helpers; the literal abort marker lives only in main.rs.
TARGETS = [
    REPO_ROOT / "novaic-app" / "src-tauri" / "src" / "main.rs",
]

MARKER = "SPLIT_CONFIG_STRICT_ABORT"
FOUND = 0
MISSING = []

for target in TARGETS:
    if not target.exists():
        MISSING.append(str(target))
        continue
    text = target.read_text()
    count = text.count(MARKER)
    if count > 0:
        print(f"  found {count} occurrence(s) in {target.relative_to(REPO_ROOT)}")
        FOUND += count
    else:
        MISSING.append(str(target.relative_to(REPO_ROOT)))

if MISSING:
    print(f"SPLIT_CONFIG_ABORT_PRESENT=FAIL (missing in: {MISSING})")
    print("SPLIT_CONFIG_ABORT_TEST=FAIL")
    sys.exit(1)

print(f"SPLIT_CONFIG_ABORT_PRESENT=PASS (total={FOUND})")
print("SPLIT_CONFIG_ABORT_TEST=PASS")
