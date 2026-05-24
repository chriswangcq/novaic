#!/usr/bin/env python3
"""Guard immutable backend image CI/CD workflows."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND_IMAGES = ROOT / ".github" / "workflows" / "backend-images.yml"
PROMOTE_PROD = ROOT / ".github" / "workflows" / "backend-promote-prod.yml"
DEPLOY_DOC = ROOT / "docs" / "runbooks" / "deploy.md"
RUN_ALL_TESTS = ROOT / "scripts" / "run_all_tests.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "lint.yml"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def require_text(text: str, needle: str, label: str, errors: list[str]) -> None:
    require(needle in text, f"{label}: missing {needle!r}", errors)


def main() -> int:
    errors: list[str] = []
    for path in [BACKEND_IMAGES, PROMOTE_PROD]:
        require(path.exists(), f"workflow missing: {path.relative_to(ROOT)}", errors)

    backend = BACKEND_IMAGES.read_text(encoding="utf-8")
    promote = PROMOTE_PROD.read_text(encoding="utf-8")
    deploy_doc = DEPLOY_DOC.read_text(encoding="utf-8")
    run_all_tests = RUN_ALL_TESTS.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for marker in [
        "pull_request:",
        "push:",
        "branches: [\"main\"]",
        "submodules: recursive",
        "./scripts/run_all_tests.sh",
        "docker/api-backend/env.prod.example",
        "docker/api-backend/env.staging.example",
        "docker/llm-factory/env.prod.example",
        "docker/llm-factory/env.staging.example",
        "docker build -f docker/api-backend/Dockerfile",
        "docker build -f docker/llm-factory/Dockerfile",
        "import common.service_runtime",
        "import factory.app",
        "docker/login-action@v3",
        "docker push \"$api_tag\"",
        "docker push \"$factory_tag\"",
        "docker inspect --format='{{index .RepoDigests 0}}'",
        "./deploy services-image staging",
        "./deploy factory-image staging",
        "staging-api.gradievo.com",
    ]:
        require_text(backend, marker, "backend-images.yml", errors)

    for forbidden in [
        "./deploy services\n",
        "./deploy api-backend",
        "./deploy factory\n",
        "deploy services ",
        "deploy factory ",
    ]:
        require(forbidden not in backend, f"backend-images.yml must not use remote-build deploy path: {forbidden!r}", errors)

    for marker in [
        "workflow_dispatch:",
        "api_image:",
        "factory_image:",
        "environment: production",
        "submodules: recursive",
        "NOVAIC_API_SSH_PRIVATE_KEY",
        "./deploy services-image prod",
        "./deploy factory-image prod",
        "api.gradievo.com",
    ]:
        require_text(promote, marker, "backend-promote-prod.yml", errors)

    for forbidden in ["docker build", "docker push", "./deploy services\n", "./deploy factory\n"]:
        require(forbidden not in promote, f"backend-promote-prod.yml must not rebuild or remote-build deploy: {forbidden!r}", errors)

    for marker in [
        "NOVAIC_API_SSH_PRIVATE_KEY",
        "GITHUB_TOKEN",
        "backend-images.yml",
        "backend-promote-prod.yml",
        "workflow_dispatch",
        "production",
        "不在生产机 build",
    ]:
        require_text(deploy_doc, marker, "docs/runbooks/deploy.md", errors)

    require(
        "scripts/ci/lint_immutable_image_workflows.py" in run_all_tests,
        "scripts/run_all_tests.sh missing immutable image workflow guard",
        errors,
    )
    require(
        "python3 scripts/ci/lint_immutable_image_workflows.py" in workflow,
        ".github/workflows/lint.yml missing immutable image workflow guard",
        errors,
    )

    if errors:
        print("lint_immutable_image_workflows FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("lint_immutable_image_workflows OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
