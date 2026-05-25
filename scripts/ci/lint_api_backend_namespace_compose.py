#!/usr/bin/env python3
"""Guard namespace-aware API backend Compose configuration."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "docker" / "api-backend" / "compose.yaml"
ENV_EXAMPLE = ROOT / "docker" / "api-backend" / "env.example"
ENV_PROD = ROOT / "docker" / "api-backend" / "env.prod.example"
ENV_STAGING = ROOT / "docker" / "api-backend" / "env.staging.example"
WRITE_ENV = ROOT / "docker" / "api-backend" / "write_env.py"
RUN_ALL_TESTS = ROOT / "scripts" / "run_all_tests.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "lint.yml"

REGISTERED_COMPOSE_SERVICES = {
    "service-registry",
    "entangled",
    "queue-service",
    "blob-service",
    "sandboxd",
    "gateway",
    "business",
    "device",
    "cortex",
}

PORT_KEYS = [
    "NOVAIC_ENTANGLED_PORT",
    "NOVAIC_RUNTIME_SCHEDULER_PORT",
    "NOVAIC_RUNTIME_HEALTH_PORT",
    "NOVAIC_SUBSCRIBER_PORT",
    "NOVAIC_REGISTRY_PORT",
    "NOVAIC_DEVICE_PORT",
    "NOVAIC_SANDBOX_PORT",
    "NOVAIC_BLOB_PORT",
    "NOVAIC_CORTEX_PORT",
    "NOVAIC_QUEUE_PORT",
    "NOVAIC_BUSINESS_PORT",
    "NOVAIC_GATEWAY_PORT",
]

REQUIRED_ENV_KEYS = [
    "COMPOSE_PROJECT_NAME",
    "NOVAIC_NAMESPACE",
    "NOVAIC_RELEASE_ID",
    "NOVAIC_HOST_ID",
    "NOVAIC_ENVIRONMENT",
    "NOVAIC_IMAGE_DIGEST",
    "NOVAIC_API_BACKEND_IMAGE",
    "NOVAIC_DATA_DIR",
    "NOVAIC_SANDBOX_SHARED_DIR",
    "NOVAIC_POSTGRES_SECRETS_DIR",
    "NOVAIC_ETC_DIR",
    "NOVAIC_SERVICE_REGISTRY_URL",
    "NOVAIC_REGISTRY_TABLE",
    "NOVAIC_REDIS_URL",
    "NOVAIC_ENTANGLED_SERVICE_TOKEN_FILE",
    "NOVAIC_JWT_SECRET",
    "NOVAIC_CORTEX_INTERNAL_KEY",
    "NOVAIC_BLOB_BACKEND",
    "NOVAIC_OSS_ACCESS_KEY",
    "NOVAIC_OSS_SECRET_KEY",
    "NOVAIC_OSS_ENDPOINT",
    "NOVAIC_OSS_REGION",
    "NOVAIC_OSS_BUCKET",
    *PORT_KEYS,
]


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if sep:
            values[key] = value
    return values


def compose_service_block(text: str, service_name: str) -> str:
    marker = f"\n  {service_name}:"
    start = text.find(marker)
    if start < 0:
        return ""
    start += 1
    next_start = len(text)
    match = re.search(r"\n  [A-Za-z0-9_-]+:\n", text[start + len(marker) :])
    if match:
        next_start = start + len(marker) + match.start()
    return text[start:next_start]


def main() -> int:
    errors: list[str] = []
    compose = COMPOSE.read_text(encoding="utf-8")
    write_env = WRITE_ENV.read_text(encoding="utf-8")
    run_all_tests = RUN_ALL_TESTS.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for path in [ENV_EXAMPLE, ENV_PROD, ENV_STAGING]:
        require(path.exists(), f"missing env sample: {path.relative_to(ROOT)}", errors)

    for marker in [
        'name: "${COMPOSE_PROJECT_NAME:-novaic-api-backend}"',
        "NOVAIC_NAMESPACE:?NOVAIC_NAMESPACE required",
        "NOVAIC_RELEASE_ID:?NOVAIC_RELEASE_ID required",
        "NOVAIC_SERVICE_REGISTRY_URL:?NOVAIC_SERVICE_REGISTRY_URL required",
        "NOVAIC_DATA_DIR:?NOVAIC_DATA_DIR required",
        "NOVAIC_SANDBOX_SHARED_DIR",
        "NOVAIC_REDIS_URL:?NOVAIC_REDIS_URL required",
        "NOVAIC_ENTANGLED_SERVICE_TOKEN_FILE:?NOVAIC_ENTANGLED_SERVICE_TOKEN_FILE required",
        "NOVAIC_REGISTRY_TABLE:?NOVAIC_REGISTRY_TABLE required",
        "${NOVAIC_HOST_ID:-api-host-1}-gateway",
    ]:
        require(marker in compose, f"compose missing marker {marker!r}", errors)

    require("api-host-1-gateway" not in compose, "compose must not hard-code instance ids", errors)
    require("/opt/novaic/data:/opt/novaic/data" not in compose, "compose must not hard-code shared data mount", errors)
    require("entangled_production_service_token" not in compose, "compose must not keep production-named token file", errors)

    lines = compose.splitlines()
    for index, line in enumerate(lines[:-1]):
        if line.strip() == "- --service-registry-url":
            require(
                "NOVAIC_SERVICE_REGISTRY_URL" in lines[index + 1],
                f"--service-registry-url is not namespace env-driven near line {index + 1}",
                errors,
            )

    for service_name in REGISTERED_COMPOSE_SERVICES:
        block = compose_service_block(compose, service_name)
        require(block, f"compose missing service block {service_name}", errors)
        for marker in ["--namespace", "--release-id", "--host-id", "--compose-project", "--environment"]:
            require(marker in block, f"{service_name} missing {marker}", errors)

    for marker in [
        'parser.add_argument("--namespace"',
        'parser.add_argument("--release-id"',
        '"NOVAIC_SERVICE_REGISTRY_URL"',
        '"NOVAIC_REGISTRY_TABLE"',
        '"NOVAIC_REDIS_URL"',
        '"NOVAIC_SANDBOX_SHARED_DIR"',
        '"NOVAIC_ENTANGLED_SERVICE_TOKEN_FILE"',
        "DEFAULT_PORT_OFFSETS",
    ]:
        require(marker in write_env, f"write_env.py missing marker {marker!r}", errors)

    prod = load_env(ENV_PROD)
    staging = load_env(ENV_STAGING)
    for label, values in [("prod", prod), ("staging", staging)]:
        for key in REQUIRED_ENV_KEYS:
            require(values.get(key, "") != "", f"{label} env missing non-empty {key}", errors)
        require(values.get("NOVAIC_NAMESPACE") == label, f"{label} env namespace drifted", errors)
        require(values.get("NOVAIC_ENVIRONMENT") == label, f"{label} env environment drifted", errors)
        require(values.get("NOVAIC_DATA_DIR", "").endswith(f"/{label}"), f"{label} data dir is not namespaced", errors)
        require(
            values.get("NOVAIC_SANDBOX_SHARED_DIR", "").endswith(f"/{label}/sandbox"),
            f"{label} sandbox shared dir is not namespaced",
            errors,
        )
        require(
            values.get("NOVAIC_POSTGRES_SECRETS_DIR", "").endswith(f"/{label}"),
            f"{label} postgres secrets dir is not namespaced",
            errors,
        )
        require(values.get("NOVAIC_ETC_DIR", "").endswith(f"/{label}"), f"{label} etc dir is not namespaced", errors)
        require(":latest" not in values.get("NOVAIC_API_BACKEND_IMAGE", ""), f"{label} image must not use latest", errors)

    for key in [
        "COMPOSE_PROJECT_NAME",
        "NOVAIC_NAMESPACE",
        "NOVAIC_DATA_DIR",
        "NOVAIC_SANDBOX_SHARED_DIR",
        "NOVAIC_POSTGRES_SECRETS_DIR",
        "NOVAIC_ETC_DIR",
        "NOVAIC_SERVICE_REGISTRY_URL",
        "NOVAIC_REDIS_URL",
    ]:
        require(prod.get(key) != staging.get(key), f"prod/staging must differ for {key}", errors)

    for key in PORT_KEYS:
        require(prod.get(key, "").startswith("199"), f"prod {key} must use 199xx range", errors)
        require(staging.get(key, "").startswith("299"), f"staging {key} must use 299xx range", errors)
        require(prod.get(key) != staging.get(key), f"prod/staging must differ for {key}", errors)

    for key in ["NOVAIC_DATA_DIR", "NOVAIC_SANDBOX_SHARED_DIR", "NOVAIC_POSTGRES_SECRETS_DIR", "NOVAIC_ETC_DIR", "NOVAIC_REDIS_URL"]:
        require("prod" not in staging.get(key, ""), f"staging {key} references prod", errors)

    require(
        prod.get("NOVAIC_SERVICE_REGISTRY_URL", "").endswith(f":{prod.get('NOVAIC_REGISTRY_PORT')}"),
        "prod registry URL must match registry port",
        errors,
    )
    require(
        staging.get("NOVAIC_SERVICE_REGISTRY_URL", "").endswith(f":{staging.get('NOVAIC_REGISTRY_PORT')}"),
        "staging registry URL must match registry port",
        errors,
    )

    require(
        "scripts/ci/lint_api_backend_namespace_compose.py" in run_all_tests,
        "scripts/run_all_tests.sh missing namespace compose guard",
        errors,
    )
    require(
        "python3 scripts/ci/lint_api_backend_namespace_compose.py" in workflow,
        ".github/workflows/lint.yml missing namespace compose guard",
        errors,
    )

    if errors:
        print("lint_api_backend_namespace_compose FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("lint_api_backend_namespace_compose OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
