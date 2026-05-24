#!/usr/bin/env python3
"""Guard active service config from carrying committed secret material."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVICES_JSON = ROOT / "novaic-common" / "config" / "services.json"
STRICT_CONFIG = ROOT / "novaic-common" / "common" / "strict_config.py"
WRITE_ENV = ROOT / "docker" / "api-backend" / "write_env.py"
DEPLOY = ROOT / "deploy"
START_SH = ROOT / "scripts" / "start.sh"

SECRET_FIELDS = {
    "jwt_secret",
    "turn_secret",
    "internal_tasks_secret",
    "cortex_internal_key",
    "queue_service_internal_key",
    "clerk_publishable_key",
    "clerk_jwks_url",
    "alibaba_cloud_access_key_id",
    "alibaba_cloud_access_key_secret",
}

SUSPICIOUS_PATTERNS = (
    re.compile(r"^LTAI[A-Za-z0-9]{12,}$"),
    re.compile(r"^[A-Fa-f0-9]{32,}$"),
    re.compile(r"^[A-Za-z0-9_\\-]{24,}$"),
)


def main() -> int:
    errors: list[str] = []
    services = json.loads(SERVICES_JSON.read_text(encoding="utf-8"))
    secrets = services.get("secrets")
    if not isinstance(secrets, dict):
        errors.append("services.json secrets section must exist as an object")
    else:
        missing = sorted(SECRET_FIELDS - set(secrets))
        if missing:
            errors.append(f"services.json missing declared secret fields: {missing}")

        for key in sorted(SECRET_FIELDS & set(secrets)):
            value = secrets.get(key)
            if value not in ("", None):
                errors.append(f"services.json secrets.{key} must be empty in committed defaults")
            if isinstance(value, str) and any(pattern.match(value) for pattern in SUSPICIOUS_PATTERNS):
                errors.append(f"services.json secrets.{key} looks like committed secret material")

    strict_config = STRICT_CONFIG.read_text(encoding="utf-8")
    write_env = WRITE_ENV.read_text(encoding="utf-8")
    deploy = DEPLOY.read_text(encoding="utf-8")
    start_sh = START_SH.read_text(encoding="utf-8")

    required_markers = [
        (strict_config, "NOVAIC_SECRETS_PATH", "strict_config secret overlay env marker"),
        (strict_config, "/opt/novaic/etc/secrets.json", "strict_config production secret overlay path"),
        (write_env, "--secrets-json", "api-backend env writer explicit secret input"),
        (deploy, "api_backend_etc_dir_for_namespace", "deploy namespace secret dir selection"),
        (deploy, "--secrets-json '$etc_dir/secrets.json'", "deploy explicit namespace secret input"),
        (start_sh, "secrets overlay = secrets.local.json or /opt/novaic/etc/secrets.json", "legacy start secret comment"),
    ]
    for text, marker, label in required_markers:
        if marker not in text:
            errors.append(f"missing {label}: {marker!r}")

    if errors:
        print("lint_service_config_secret_split FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("lint_service_config_secret_split OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
