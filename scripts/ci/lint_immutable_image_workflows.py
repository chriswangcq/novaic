#!/usr/bin/env python3
"""Guard that backend releases are owned by Release Controller, not GitHub workflows."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND_IMAGES = ROOT / ".github" / "workflows" / "backend-images.yml"
PROMOTE_PROD = ROOT / ".github" / "workflows" / "backend-promote-prod.yml"
DEPLOY_DOC = ROOT / "docs" / "runbooks" / "deploy.md"
RELEASE_CONTROLLER_DOC = ROOT / "docs" / "architecture" / "release-controller.md"
RUN_ALL_TESTS = ROOT / "scripts" / "run_all_tests.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "lint.yml"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def require_text(text: str, needle: str, label: str, errors: list[str]) -> None:
    require(needle in text, f"{label}: missing {needle!r}", errors)


def main() -> int:
    errors: list[str] = []
    require(not BACKEND_IMAGES.exists(), "backend-images.yml must not exist; Release Controller owns backend builds/deploys", errors)
    require(not PROMOTE_PROD.exists(), "backend-promote-prod.yml must not exist; Release Controller owns prod promotion", errors)

    deploy_doc = DEPLOY_DOC.read_text(encoding="utf-8")
    release_controller_doc = RELEASE_CONTROLLER_DOC.read_text(encoding="utf-8")
    run_all_tests = RUN_ALL_TESTS.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for marker in [
        "Release Controller 是唯一后端/Factory 发布入口",
        "GitHub Actions 不再承担 backend/factory 构建、发布、promote 或 rollback",
        "POST /v1/promotions/prod",
        "POST /v1/rollbacks/<namespace>",
        "生产机不 build",
    ]:
        require_text(deploy_doc, marker, "docs/runbooks/deploy.md", errors)

    for marker in [
        "replaces GitHub Actions and direct operator scripts",
        "Direct operator execution without that identity fails",
        "It does not use GitHub Actions for backend/factory release orchestration",
    ]:
        require_text(release_controller_doc, marker, "docs/architecture/release-controller.md", errors)

    require(
        "scripts/ci/lint_immutable_image_workflows.py" in run_all_tests,
        "scripts/run_all_tests.sh missing release-controller workflow guard",
        errors,
    )
    require(
        "python3 scripts/ci/lint_immutable_image_workflows.py" in workflow,
        ".github/workflows/lint.yml missing release-controller workflow guard",
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
