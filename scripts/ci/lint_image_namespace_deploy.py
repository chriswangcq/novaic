#!/usr/bin/env python3
"""Guard image-based namespace deploy entrypoints."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy"
DEPLOY_DOC = ROOT / "docs" / "runbooks" / "deploy.md"
RUN_ALL_TESTS = ROOT / "scripts" / "run_all_tests.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "lint.yml"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def require_text(text: str, needle: str, label: str, errors: list[str]) -> None:
    require(needle in text, f"{label}: missing {needle!r}", errors)


def function_body(text: str, name: str, errors: list[str]) -> str:
    match = re.search(rf"^{re.escape(name)}\(\) \{{\n(?P<body>.*?)^\}}\n", text, re.M | re.S)
    if not match:
        errors.append(f"deploy: missing function {name}()")
        return ""
    return match.group("body")


def main() -> int:
    errors: list[str] = []
    deploy = DEPLOY.read_text(encoding="utf-8")
    deploy_doc = DEPLOY_DOC.read_text(encoding="utf-8")
    run_all_tests = RUN_ALL_TESTS.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for marker in [
        "validate_namespace()",
        "normalize_image_ref()",
        "validate_immutable_image_ref()",
        "image_digest_from_ref()",
        "release_id_from_image_ref()",
        "api_backend_env_file_for_namespace()",
        "factory_env_file_for_namespace()",
        "require_release_controller_invocation()",
        "services-image) deploy_services_image \"$2\" \"$3\" ;;",
        "factory-image)  deploy_factory_image \"$2\" \"$3\" ;;",
        "services-image <namespace> <image>",
        "factory-image <namespace> <image>",
    ]:
        require_text(deploy, marker, "deploy", errors)

    validation_body = function_body(deploy, "validate_immutable_image_ref", errors)
    for marker in [
        "@sha256:[0-9a-fA-F]{64}",
        "latest|local|dev|main|master|prod|staging",
        "^sha-?[0-9a-fA-F]{6,40}$",
        "只允许 digest 或 sha tag",
    ]:
        require_text(validation_body, marker, "validate_immutable_image_ref", errors)

    services_body = function_body(deploy, "deploy_services_image", errors)
    for marker in [
        "require_release_controller_invocation \"services-image\" \"$namespace\"",
        "normalize_image_ref api-backend",
        "validate_immutable_image_ref \"$namespace\" \"$image_ref\"",
        "sync_api_backend_compose",
        "sync_api_backend_config_snapshot",
        "write_api_backend_env \"$namespace\" \"$image_ref\"",
        "validate_api_backend_compose \"$env_file\" \"$namespace\"",
        "pull",
        "up -d --no-build --remove-orphans",
    ]:
        require_text(services_body, marker, "deploy_services_image", errors)
    for stale in ["build_api_backend_image", "sync_api_backend_build_context", "docker build"]:
        require(stale not in services_body, f"deploy_services_image must not build on host: {stale}", errors)

    factory_body = function_body(deploy, "deploy_factory_image", errors)
    for marker in [
        "require_release_controller_invocation \"factory-image\" \"$namespace\"",
        "normalize_image_ref llm-factory",
        "validate_immutable_image_ref \"$namespace\" \"$image_ref\"",
        "ensure_host_infra_running",
        "sync_factory_compose_package",
        "write_factory_env \"$namespace\" \"$image_ref\"",
        "verify_factory_runtime_inputs \"$namespace\"",
        "pull llm-factory",
        "up -d --no-build llm-factory",
    ]:
        require_text(factory_body, marker, "deploy_factory_image", errors)
    for stale in ["sync_factory_docker_package", "docker build"]:
        require(stale not in factory_body, f"deploy_factory_image must not build on host: {stale}", errors)

    write_api_body = function_body(deploy, "write_api_backend_env", errors)
    for marker in [
        "api_backend_etc_dir_for_namespace",
        "api_backend_data_dir_for_namespace",
        "api_backend_postgres_secrets_dir_for_namespace",
        "--namespace '$namespace'",
        "--release-id '$release_id'",
        "--image-digest '$image_digest'",
        "--redis-url '$redis_url'",
        "--port-base '$port_base'",
    ]:
        require_text(write_api_body, marker, "write_api_backend_env", errors)

    write_factory_body = function_body(deploy, "write_factory_env", errors)
    for marker in [
        "COMPOSE_PROJECT_NAME=novaic-llm-factory-$namespace",
        "NOVAIC_NAMESPACE=$namespace",
        "NOVAIC_RELEASE_ID=$release_id",
        "NOVAIC_IMAGE_DIGEST=$image_digest",
        "NOVAIC_LLM_FACTORY_IMAGE=$image_ref",
        "NOVAIC_LLM_FACTORY_PORT=$port",
    ]:
        require_text(write_factory_body, marker, "write_factory_env", errors)

    require(
        "scripts/ci/lint_image_namespace_deploy.py" in run_all_tests,
        "scripts/run_all_tests.sh missing image namespace deploy guard",
        errors,
    )
    require(
        "python3 scripts/ci/lint_image_namespace_deploy.py" in workflow,
        ".github/workflows/lint.yml missing image namespace deploy guard",
        errors,
    )

    for marker in [
        "Release Controller 是唯一后端/Factory 发布入口",
        "deploy services-image <namespace> <image-ref>",
        "deploy factory-image <namespace> <image-ref>",
        "人工直接调用会在连接远端前失败",
        "生产机不 build",
        "up -d --no-build",
        "api-backend.<namespace>.env",
        "/opt/novaic/llm-factory/<namespace>/compose.env",
    ]:
        require_text(deploy_doc, marker, "docs/runbooks/deploy.md", errors)

    if errors:
        print("lint_image_namespace_deploy FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("lint_image_namespace_deploy OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
