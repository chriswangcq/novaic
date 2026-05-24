#!/usr/bin/env python3
"""Guard LLM Factory Docker deployment as the current path."""

from __future__ import annotations

import re
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy"
DEPLOY_DOC = ROOT / "docs" / "runbooks" / "deploy.md"
RUN_ALL_TESTS = ROOT / "scripts" / "run_all_tests.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "lint.yml"
SERVICES_JSON = ROOT / "novaic-common" / "config" / "services.json"
COMMON_CONFIG = ROOT / "novaic-common" / "common" / "config.py"
BUSINESS_FACTORY_ADMIN = ROOT / "novaic-business" / "business" / "factory_admin_client.py"

PACKAGE_FILES = [
    "docker/llm-factory/Dockerfile",
    "docker/llm-factory/.dockerignore",
    "docker/llm-factory/compose.yaml",
    "docker/llm-factory/README.md",
]

OLD_FACTORY_TEXT = [
    "FACTORY_HOST",
    "FACTORY_SSH",
    "newapi.gradievo.com",
    "source .venv",
    "systemctl restart llm-factory",
]


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

    for rel in PACKAGE_FILES:
        require((ROOT / rel).exists(), f"Factory Docker package file missing: {rel}", errors)

    deploy = DEPLOY.read_text(encoding="utf-8")
    doc = DEPLOY_DOC.read_text(encoding="utf-8")
    run_all_tests = RUN_ALL_TESTS.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    services_json = SERVICES_JSON.read_text(encoding="utf-8")
    common_config = COMMON_CONFIG.read_text(encoding="utf-8")
    business_factory_admin = BUSINESS_FACTORY_ADMIN.read_text(encoding="utf-8")

    body = function_body(deploy, "deploy_factory", errors)

    for needle in [
        "FACTORY_DOCKER_DIR=\"/opt/novaic/llm-factory\"",
        "FACTORY_COMPOSE_FILE=\"$FACTORY_DOCKER_DIR/docker-compose.yml\"",
        "FACTORY_APP_DIR=\"$FACTORY_DOCKER_DIR/app\"",
        "disabled_backend_release_path \"factory\"",
    ]:
        require_text(deploy if needle.startswith("FACTORY_") else body, needle, "deploy", errors)

    for stale in OLD_FACTORY_TEXT + [
        "sync_factory_docker_package",
        "build llm-factory",
        "up -d llm-factory",
        "factory_env_file",
    ]:
        require(stale not in body, f"deploy_factory still contains old Factory path text {stale!r}", errors)

    for stale in ["FACTORY_HOST=", "FACTORY_SSH="]:
        require(stale not in deploy, f"deploy still defines old Factory variable {stale!r}", errors)

    for stale in ["newapi.gradievo.com", "https://newapi.gradievo.com"]:
        for label, text in [
            ("novaic-common/config/services.json", services_json),
            ("novaic-common/common/config.py", common_config),
            ("novaic-business/business/factory_admin_client.py", business_factory_admin),
        ]:
            require(stale not in text, f"{label}: old Factory URL marker remains {stale!r}", errors)

    require_text(deploy, "factory)        deploy_factory ;;", "deploy", errors)
    require_text(deploy, "LLM Factory Docker", "deploy", errors)
    try:
        services = json.loads(services_json)
    except json.JSONDecodeError as e:
        errors.append(f"novaic-common/config/services.json: invalid JSON: {e}")
        services = {}
    factory_url = (((services.get("services") or {}).get("llm_factory") or {}).get("url"))
    require(
        factory_url == "http://127.0.0.1:19990",
        "novaic-common/config/services.json: llm_factory.url must be http://127.0.0.1:19990",
        errors,
    )
    require_text(common_config, 'LLM_FACTORY_URL = _CFG.get("services", "llm_factory", "url")', "novaic-common/common/config.py", errors)
    require_text(business_factory_admin, "return ServiceConfig.LLM_FACTORY_URL.rstrip(\"/\")", "novaic-business/business/factory_admin_client.py", errors)
    require_text(doc, "LLM Factory（API host Docker）", "docs/runbooks/deploy.md", errors)
    require_text(doc, "Release Controller 内部执行器", "docs/runbooks/deploy.md", errors)
    require_text(doc, "/opt/novaic/llm-factory", "docs/runbooks/deploy.md", errors)
    require_text(doc, "127.0.0.1:19990", "docs/runbooks/deploy.md", errors)
    require_text(run_all_tests, "scripts/ci/lint_llm_factory_docker_path.py", "scripts/run_all_tests.sh", errors)
    require_text(workflow, "python3 scripts/ci/lint_llm_factory_docker_path.py", ".github/workflows/lint.yml", errors)

    if errors:
        print("lint_llm_factory_docker_path FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("lint_llm_factory_docker_path OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
