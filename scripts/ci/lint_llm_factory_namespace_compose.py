#!/usr/bin/env python3
"""Guard namespace-aware LLM Factory Compose configuration."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "docker" / "llm-factory" / "compose.yaml"
ENV_EXAMPLE = ROOT / "docker" / "llm-factory" / "env.example"
ENV_PROD = ROOT / "docker" / "llm-factory" / "env.prod.example"
ENV_STAGING = ROOT / "docker" / "llm-factory" / "env.staging.example"
README = ROOT / "docker" / "llm-factory" / "README.md"
RUN_ALL_TESTS = ROOT / "scripts" / "run_all_tests.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "lint.yml"

REQUIRED_ENV_KEYS = [
    "COMPOSE_PROJECT_NAME",
    "NOVAIC_NAMESPACE",
    "NOVAIC_RELEASE_ID",
    "NOVAIC_HOST_ID",
    "NOVAIC_ENVIRONMENT",
    "NOVAIC_IMAGE_DIGEST",
    "NOVAIC_LLM_FACTORY_IMAGE",
    "NOVAIC_LLM_FACTORY_BUILD_CONTEXT",
    "NOVAIC_LLM_FACTORY_RUNTIME_ENV",
    "NOVAIC_LLM_FACTORY_DATA_DIR",
    "NOVAIC_LLM_FACTORY_SECRETS_DIR",
    "NOVAIC_LLM_FACTORY_CONFIG",
    "NOVAIC_LLM_FACTORY_PORT",
    "NOVAIC_LLM_FACTORY_CONTAINER_PORT",
    "NOVAIC_POSTGRES_NETWORK",
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


def main() -> int:
    errors: list[str] = []
    compose = COMPOSE.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    run_all_tests = RUN_ALL_TESTS.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for path in [ENV_EXAMPLE, ENV_PROD, ENV_STAGING]:
        require(path.exists(), f"missing env sample: {path.relative_to(ROOT)}", errors)

    for marker in [
        'name: "${COMPOSE_PROJECT_NAME:-novaic-llm-factory}"',
        "${NOVAIC_LLM_FACTORY_IMAGE:-novaic/llm-factory:local}",
        "NOVAIC_NAMESPACE:?NOVAIC_NAMESPACE required",
        "NOVAIC_RELEASE_ID:?NOVAIC_RELEASE_ID required",
        "NOVAIC_LLM_FACTORY_RUNTIME_ENV:?NOVAIC_LLM_FACTORY_RUNTIME_ENV required",
        "NOVAIC_LLM_FACTORY_DATA_DIR:?NOVAIC_LLM_FACTORY_DATA_DIR required",
        "NOVAIC_LLM_FACTORY_SECRETS_DIR:?NOVAIC_LLM_FACTORY_SECRETS_DIR required",
        "NOVAIC_LLM_FACTORY_PORT:?NOVAIC_LLM_FACTORY_PORT required",
        "NOVAIC_POSTGRES_NETWORK:-novaic-postgres_default",
    ]:
        require(marker in compose, f"compose missing marker {marker!r}", errors)

    for stale in [
        "container_name:",
        "- ./runtime.env",
        "./data:/data",
        "./secrets:/run/secrets",
        "127.0.0.1:19990:19990",
    ]:
        require(stale not in compose, f"compose retains fixed Factory marker {stale!r}", errors)

    prod = load_env(ENV_PROD)
    staging = load_env(ENV_STAGING)
    for label, values in [("prod", prod), ("staging", staging)]:
        for key in REQUIRED_ENV_KEYS:
            require(values.get(key, "") != "", f"{label} env missing non-empty {key}", errors)
        require(values.get("NOVAIC_NAMESPACE") == label, f"{label} env namespace drifted", errors)
        require(values.get("NOVAIC_ENVIRONMENT") == label, f"{label} env environment drifted", errors)
        for key in [
            "NOVAIC_LLM_FACTORY_RUNTIME_ENV",
            "NOVAIC_LLM_FACTORY_DATA_DIR",
            "NOVAIC_LLM_FACTORY_SECRETS_DIR",
        ]:
            require(
                re.search(rf"/{label}/", values.get(key, "")) is not None,
                f"{label} {key} is not namespace-scoped",
                errors,
            )
        require(":latest" not in values.get("NOVAIC_LLM_FACTORY_IMAGE", ""), f"{label} image must not use latest", errors)

    require(prod.get("NOVAIC_LLM_FACTORY_PORT") == "19990", "prod Factory host port must be 19990", errors)
    require(staging.get("NOVAIC_LLM_FACTORY_PORT") == "29990", "staging Factory host port must be 29990", errors)
    require(prod.get("NOVAIC_LLM_FACTORY_CONTAINER_PORT") == staging.get("NOVAIC_LLM_FACTORY_CONTAINER_PORT"), "container port should remain stable", errors)

    for key in [
        "COMPOSE_PROJECT_NAME",
        "NOVAIC_NAMESPACE",
        "NOVAIC_LLM_FACTORY_IMAGE",
        "NOVAIC_LLM_FACTORY_RUNTIME_ENV",
        "NOVAIC_LLM_FACTORY_DATA_DIR",
        "NOVAIC_LLM_FACTORY_SECRETS_DIR",
        "NOVAIC_LLM_FACTORY_PORT",
    ]:
        require(prod.get(key) != staging.get(key), f"prod/staging must differ for {key}", errors)

    for key in ["NOVAIC_LLM_FACTORY_RUNTIME_ENV", "NOVAIC_LLM_FACTORY_DATA_DIR", "NOVAIC_LLM_FACTORY_SECRETS_DIR"]:
        require("prod" not in staging.get(key, ""), f"staging {key} references prod", errors)

    for marker in ["env.prod.example", "env.staging.example", "29990", "namespace-aware service registry"]:
        require(marker in readme, f"docker/llm-factory/README.md missing marker {marker!r}", errors)

    require(
        "scripts/ci/lint_llm_factory_namespace_compose.py" in run_all_tests,
        "scripts/run_all_tests.sh missing LLM Factory namespace guard",
        errors,
    )
    require(
        "python3 scripts/ci/lint_llm_factory_namespace_compose.py" in workflow,
        ".github/workflows/lint.yml missing LLM Factory namespace guard",
        errors,
    )

    if errors:
        print("lint_llm_factory_namespace_compose FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("lint_llm_factory_namespace_compose OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
