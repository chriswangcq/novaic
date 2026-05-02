#!/usr/bin/env python3
"""Guard the deploy/start/config boundary.

This script intentionally lives in the root repo because the risky residue is
cross-cutting: old root deploy scripts, current docs, runtime env switches, and
the shipped services.json all need to agree on one active path.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
START_SH = ROOT / "scripts" / "start.sh"
SERVICES_JSON = ROOT / "novaic-common" / "config" / "services.json"

ALLOWED_RUNTIME_SWITCHES = {
    "health_check_interval_seconds",
    "scheduler_poll_interval_seconds",
}

RETIRED_FILES = [
    "scripts/start-all.sh",
    "scripts/deploy-all.sh",
    "scripts/deploy-business.sh",
    "scripts/canary/traffic.py",
    "scripts/gateway/deploy-gateway.sh",
    "scripts/gateway/jwt_secret.env.example",
    "scripts/gateway/backfill_file_id.py",
    "scripts/gateway/fail_path_replay_gateway.sh",
    "scripts/gateway/migrate_execution_logs_subagent_id.sh",
    "scripts/gateway/migrate_legacy_user.py",
    "scripts/gateway/migrate_user_data.py",
    "scripts/gateway/replay_gateway_runtime_chain.sh",
    "scripts/submodules",
    "docs/runbooks/subscriber-canary.md",
    "scripts/cleanup_all_dbs.sh",
    "scripts/cleanup_queue_db.sh",
    "scripts/recover_agent_loop.sh",
    "scripts/reset-agent-data.sh",
]

RETIRED_TEXT = [
    "WAKE_TURN_FINALIZER_ENABLED",
    "WAKE_TURN_CLOSER_TOOLS",
    "scripts/start-all.sh",
    "start-all.sh",
    "scripts/deploy-business.sh",
    "deploy-business.sh",
    "scripts/deploy-all.sh",
    "deploy-all.sh",
    "scripts/gateway/deploy-gateway.sh",
    "scripts/gateway/backfill_file_id.py",
    "scripts/gateway/fail_path_replay_gateway.sh",
    "scripts/gateway/migrate_execution_logs_subagent_id.sh",
    "scripts/gateway/migrate_legacy_user.py",
    "scripts/gateway/migrate_user_data.py",
    "scripts/gateway/replay_gateway_runtime_chain.sh",
    "scripts/submodules/",
    "scripts/cleanup_all_dbs.sh",
    "scripts/cleanup_queue_db.sh",
    "scripts/recover_agent_loop.sh",
    "scripts/reset-agent-data.sh",
    "jwt_secret.env",
    "restart_gw.sh",
    "docs/runbooks/subscriber-canary.md",
]

CURRENT_TEXT_TARGETS = [
    "deploy",
    "scripts",
    "docs/architecture",
    "docs/reference",
    "docs/runbooks",
    "novaic-agent-runtime/task_queue",
    "novaic-agent-runtime/tests",
    "novaic-common/common",
    "novaic-common/config",
    "novaic-common/tests",
    "novaic-app/scripts",
]


def main() -> int:
    errors: list[str] = []

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
            errors.append("start.sh config contract missing required strict_config markers:")
            for needle in missing:
                errors.append(f"  - {needle}")
        if present:
            errors.append("start.sh config contract reintroduced mirrored overlay logic:")
            for needle in present:
                errors.append(f"  - {needle}")

    retired_present = [path for path in RETIRED_FILES if (ROOT / path).exists()]
    if retired_present:
        errors.append("retired deploy/config files still exist:")
        errors.extend(f"  - {path}" for path in retired_present)

    services = json.loads(SERVICES_JSON.read_text(encoding="utf-8"))
    runtime_keys = set((services.get("runtime_switches") or {}).keys())
    if runtime_keys != ALLOWED_RUNTIME_SWITCHES:
        errors.append(
            "runtime_switches allowlist mismatch: "
            f"expected {sorted(ALLOWED_RUNTIME_SWITCHES)}, got {sorted(runtime_keys)}"
        )

    for rel in CURRENT_TEXT_TARGETS:
        path = ROOT / rel
        if not path.exists():
            continue
        paths = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()]
        for file_path in paths:
            if file_path.resolve() == Path(__file__).resolve():
                continue
            if ".git" in file_path.parts:
                continue
            try:
                text = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for needle in RETIRED_TEXT:
                if needle in text:
                    errors.append(
                        f"retired deploy/config residue {needle!r} found in "
                        f"{file_path.relative_to(ROOT)}"
                    )

    if errors:
        print("start_config_contract FAILED", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print("start_config_contract OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
