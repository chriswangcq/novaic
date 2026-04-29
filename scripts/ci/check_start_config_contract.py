#!/usr/bin/env python3
"""Guard that start.sh uses common.strict_config instead of mirrored config logic."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
START_SH = ROOT / "scripts" / "start.sh"


def main() -> int:
    source = START_SH.read_text(encoding="utf-8")

    required = [
        "from common.strict_config import load_services_config",
        'load_services_config("$BASE/novaic-common/config/services.json", force_reload=True)',
        "Do not reimplement runtime_switches overlay semantics in shell",
    ]
    banned = [
        'base = json.load(open("$BASE/novaic-common/config/services.json"))',
        "base[\"runtime_switches\"].update(overlay)",
        "overlay_path = pathlib.Path(\"/opt/novaic/etc/runtime_switches.json\")",
    ]

    missing = [needle for needle in required if needle not in source]
    present = [needle for needle in banned if needle in source]
    if missing or present:
        if missing:
            print("start.sh config contract missing required strict_config markers:", file=sys.stderr)
            for needle in missing:
                print(f"  - {needle}", file=sys.stderr)
        if present:
            print("start.sh config contract reintroduced mirrored overlay logic:", file=sys.stderr)
            for needle in present:
                print(f"  - {needle}", file=sys.stderr)
        return 1

    print("start_config_contract OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
