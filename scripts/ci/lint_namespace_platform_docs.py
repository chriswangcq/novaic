#!/usr/bin/env python3
"""Guard namespace-first platform docs."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVICE_REGISTRY_DOC = ROOT / "docs" / "services" / "service-registry.md"
SERVICE_COMM_DOC = ROOT / "docs" / "architecture" / "service-communication.md"
PORTS_DOC = ROOT / "docs" / "reference" / "ports-and-config.md"
API_ROUTES_DOC = ROOT / "docs" / "reference" / "api-routes.md"
DEPLOY_DOC = ROOT / "docs" / "runbooks" / "deploy.md"
API_BACKEND_README = ROOT / "docker" / "api-backend" / "README.md"
FACTORY_README = ROOT / "docker" / "llm-factory" / "README.md"
RUN_ALL_TESTS = ROOT / "scripts" / "run_all_tests.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "lint.yml"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def require_text(text: str, needle: str, label: str, errors: list[str]) -> None:
    require(needle in text, f"{label}: missing {needle!r}", errors)


def main() -> int:
    errors: list[str] = []
    service_registry = SERVICE_REGISTRY_DOC.read_text(encoding="utf-8")
    service_comm = SERVICE_COMM_DOC.read_text(encoding="utf-8")
    ports = PORTS_DOC.read_text(encoding="utf-8")
    api_routes = API_ROUTES_DOC.read_text(encoding="utf-8")
    deploy = DEPLOY_DOC.read_text(encoding="utf-8")
    api_backend_readme = API_BACKEND_README.read_text(encoding="utf-8")
    factory_readme = FACTORY_README.read_text(encoding="utf-8")
    run_all_tests = RUN_ALL_TESTS.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for marker in [
        "服务名保持稳定",
        "(namespace, service_name, instance_id)",
        "metadata.environment",
        "/v1/registry/namespaces/{namespace}/services/{service_name}/discover",
        "Nginx 只做 ingress，不参与服务发现",
        "staging-api.gradievo.com",
        "proxy_pass http://127.0.0.1:29999",
    ]:
        require_text(service_registry, marker, "docs/services/service-registry.md", errors)

    for marker in [
        "服务名不随环境改名",
        "prod 服务无法 discover staging 实例",
        "staging 服务也无法 discover prod 实例",
        "server_name api.gradievo.com;",
        "proxy_pass http://127.0.0.1:19999;",
        "server_name staging-api.gradievo.com;",
        "proxy_pass http://127.0.0.1:29999;",
    ]:
        require_text(service_comm, marker, "docs/architecture/service-communication.md", errors)

    for marker in [
        "Namespace data plane",
        "api-backend.<namespace>.env",
        "redis://127.0.0.1:6379/1",
        "OSS 隔离必须由 bucket 或 prefix 完成",
        "CI 在 main 构建不可变镜像",
        "回滚就是切回上一组已记录 digest",
        "/opt/novaic/postgres/secrets/<namespace>/novaic_registry_dsn",
    ]:
        require_text(ports, marker, "docs/reference/ports-and-config.md", errors)

    for marker in [
        "/v1/registry/namespaces/{namespace}/instances",
        "/v1/registry/namespaces/{namespace}/services/{service_name}/discover",
    ]:
        require_text(api_routes, marker, "docs/reference/api-routes.md", errors)

    for stale in [
        "/v1/registry/instances` | POST",
        "/v1/registry/services/{service_name}/discover",
    ]:
        require(stale not in api_routes, f"docs/reference/api-routes.md has legacy no-namespace route: {stale}", errors)
        require(stale not in service_registry, f"docs/services/service-registry.md has legacy no-namespace route: {stale}", errors)

    for marker in [
        "image-based namespace deploy",
        "远端 build 只作为回退",
        "environment approval",
        "不在生产机 build",
        "Owner/removal gate",
        "services-legacy",
    ]:
        require_text(deploy, marker, "docs/runbooks/deploy.md", errors)

    for marker in [
        "CI/CD should deploy immutable refs",
        "Service names",
        "registry namespace",
        "/opt/novaic/data/<namespace>",
        "/opt/novaic/docker/api-backend.<namespace>.env",
    ]:
        require_text(api_backend_readme, marker, "docker/api-backend/README.md", errors)

    for marker in [
        "/opt/novaic/llm-factory/<namespace>/compose.env",
        "staging uses `29990`",
        "namespace-aware service registry",
        "do not add",
    ]:
        require_text(factory_readme, marker, "docker/llm-factory/README.md", errors)

    require(
        "scripts/ci/lint_namespace_platform_docs.py" in run_all_tests,
        "scripts/run_all_tests.sh missing namespace docs guard",
        errors,
    )
    require(
        "python3 scripts/ci/lint_namespace_platform_docs.py" in workflow,
        ".github/workflows/lint.yml missing namespace docs guard",
        errors,
    )

    if errors:
        print("lint_namespace_platform_docs FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("lint_namespace_platform_docs OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
