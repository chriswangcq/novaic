#!/usr/bin/env python3
"""Guard service catalog, registry-only discovery, and current routing docs."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
SERVICES_JSON = ROOT / "novaic-common" / "config" / "services.json"
SERVICE_CATALOG = ROOT / "novaic-common" / "common" / "service_catalog.py"
SERVICE_DISCOVERY = ROOT / "novaic-common" / "common" / "service_discovery.py"
COMMON_CONFIG = ROOT / "novaic-common" / "common" / "config.py"
SERVICE_REGISTRY_SERVER = ROOT / "novaic-common" / "common" / "service_registry_server.py"
API_BACKEND_COMPOSE = ROOT / "docker" / "api-backend" / "compose.yaml"
API_BACKEND_DOCKERFILE = ROOT / "docker" / "api-backend" / "Dockerfile"
RUN_ALL_TESTS = ROOT / "scripts" / "run_all_tests.sh"

CURRENT_DOCS = [
    ROOT / "docs" / "README.md",
    ROOT / "docs" / "overview.md",
    ROOT / "docs" / "architecture" / "agent-execution-pipeline.md",
    ROOT / "docs" / "architecture" / "service-communication.md",
    ROOT / "docs" / "reference" / "api-routes.md",
    ROOT / "docs" / "reference" / "environment-variables.md",
    ROOT / "docs" / "reference" / "ports-and-config.md",
    ROOT / "docs" / "runbooks" / "troubleshooting.md",
    ROOT / "docs" / "services" / "llm-factory.md",
    ROOT / "docs" / "services" / "service-registry.md",
    ROOT / "docker" / "api-backend" / "README.md",
    ROOT / "novaic-llm-factory" / "README.md",
    ROOT / "novaic-llm-factory" / "config.example.json",
    ROOT / "novaic-llm-factory" / "factory" / "config.py",
    ROOT / "novaic-llm-factory" / "factory" / "app.py",
    ROOT / "novaic-llm-factory" / "main.py",
]

REQUIRED_SERVICE_FIELDS = {
    "url",
    "protocol",
    "port",
    "health_path",
    "compose_service",
    "owner",
    "dependencies",
}

EXPECTED_DISCOVERY = {
    "mode": "registry_only",
    "registry_backend": "postgres",
    "default_ttl_seconds": 30,
    "postgres_table": "service_registry_instances",
}

REGISTERED_COMPOSE_SERVICES = {
    "service-registry": "service_registry",
    "entangled": "entangled_service",
    "queue-service": "queue_service",
    "blob-service": "blob_service",
    "sandboxd": "sandboxd",
    "gateway": "gateway",
    "business": "business",
    "device": "device",
    "cortex": "cortex",
}

REQUIRED_REGISTRY_BINDINGS = {
    "queue_service=--queue-service-url",
    "blob_service=--blob-service-url",
    "blob_service=--blob-upload-url",
    "entangled_service=--entangled-url",
    "gateway=--gateway-url",
    "business=--business-url",
    "sandboxd=--sandboxd-url",
    "cortex=--cortex-url",
}

FORBIDDEN_STATIC_DEPENDENCY_FLAGS = {
    "--queue-service-url",
    "--blob-service-url",
    "--blob-upload-url",
    "--entangled-url",
    "--gateway-url",
    "--business-url",
    "--sandboxd-url",
    "--cortex-url",
}

STALE_FALLBACK_MARKERS = [
    "客户端解析仍应保留 static fallback",
    "回退 `services.json` 的静态 bootstrap URL",
    "否则回退静态 URL",
    "registry 不可用或无 fresh healthy 实例时回退静态目录",
    "static fallback resolver",
]


def main() -> int:
    errors: list[str] = []
    services_config = json.loads(SERVICES_JSON.read_text(encoding="utf-8"))
    services = services_config.get("services") or {}

    for name, payload in sorted(services.items()):
        if not isinstance(payload, dict):
            errors.append(f"services.{name} must be an object")
            continue
        if "url" not in payload:
            continue

        missing = sorted(REQUIRED_SERVICE_FIELDS - set(payload))
        if missing:
            errors.append(f"services.{name} missing static catalog fields: {missing}")

        parsed = urlparse(str(payload.get("url")))
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            errors.append(f"services.{name}.url must be an http(s) URL")
        if payload.get("protocol") != parsed.scheme:
            errors.append(f"services.{name}.protocol must match URL scheme")
        if payload.get("port") != parsed.port:
            errors.append(f"services.{name}.port must match URL port")
        health_path = payload.get("health_path")
        if not isinstance(health_path, str) or not health_path.startswith("/"):
            errors.append(f"services.{name}.health_path must start with /")
        dependencies = payload.get("dependencies")
        if not isinstance(dependencies, list) or not all(isinstance(dep, str) for dep in dependencies):
            errors.append(f"services.{name}.dependencies must be a list of strings")
        else:
            unknown = sorted(dep for dep in dependencies if dep not in services)
            if unknown:
                errors.append(f"services.{name}.dependencies reference unknown services: {unknown}")

    discovery = services_config.get("service_discovery")
    if discovery != EXPECTED_DISCOVERY:
        errors.append(f"service_discovery defaults drifted: expected {EXPECTED_DISCOVERY}, got {discovery}")

    service_registry = services.get("service_registry") or {}
    expected_registry_fields = {
        "url": "http://127.0.0.1:19991",
        "port": 19991,
        "health_path": "/ready",
        "compose_service": "service-registry",
        "owner": "novaic-common",
    }
    for key, expected in expected_registry_fields.items():
        if service_registry.get(key) != expected:
            errors.append(f"services.service_registry.{key} expected {expected!r}, got {service_registry.get(key)!r}")

    code_markers = [
        (SERVICE_CATALOG, "class ServiceCatalog", "typed static catalog"),
        (SERVICE_DISCOVERY, "class ServiceRegistry", "dynamic registry"),
        (SERVICE_DISCOVERY, "class RegistryOnlyResolver", "registry-only resolver"),
        (SERVICE_DISCOVERY, "class ServiceDiscoveryError", "registry-only discovery error"),
        (SERVICE_DISCOVERY, "class PostgresServiceRegistryStore", "Postgres registry store"),
        (ROOT / "novaic-common" / "common" / "service_registry_client.py", "class ServiceRegistryHttpClient", "registry HTTP client"),
        (ROOT / "novaic-common" / "common" / "service_runtime.py", "def resolve_dependencies", "registry-only runtime dependency resolver"),
        (SERVICE_REGISTRY_SERVER, "def create_app", "central registry FastAPI app factory"),
        (SERVICE_REGISTRY_SERVER, "/v1/registry/namespaces/{namespace}/instances", "namespace registry register API"),
        (SERVICE_REGISTRY_SERVER, "@app.delete", "central registry deregister API"),
        (SERVICE_REGISTRY_SERVER, "create_postgres_registry_from_dsn_file", "central registry Postgres startup"),
        (COMMON_CONFIG, "SERVICE_DISCOVERY_MODE", "ServiceConfig discovery mode"),
        (COMMON_CONFIG, "SERVICE_DISCOVERY_ENABLED", "ServiceConfig discovery flag"),
        (COMMON_CONFIG, "SERVICE_REGISTRY_POSTGRES_TABLE", "ServiceConfig registry table"),
        (COMMON_CONFIG, "SERVICE_REGISTRY_URL", "ServiceConfig central registry URL"),
        (API_BACKEND_COMPOSE, "service-registry:", "Compose service-registry role"),
        (API_BACKEND_COMPOSE, "common.service_runtime", "Compose registry runtime wrapper"),
        (API_BACKEND_COMPOSE, "--require-service", "Compose registry dependency bindings"),
        (API_BACKEND_COMPOSE, "/opt/novaic/postgres/secrets/novaic_registry_dsn", "Compose registry DSN"),
        (API_BACKEND_COMPOSE, "NOVAIC_REGISTRY_PORT:?NOVAIC_REGISTRY_PORT required", "Compose registry healthcheck"),
        (API_BACKEND_DOCKERFILE, "common.service_registry_server", "Dockerfile registry import smoke"),
        (API_BACKEND_DOCKERFILE, "common.service_registry_client", "Dockerfile registry client import smoke"),
        (API_BACKEND_DOCKERFILE, "common.service_runtime", "Dockerfile registry runtime import smoke"),
        (RUN_ALL_TESTS, "scripts/ci/lint_service_catalog_discovery.py", "test runner catalog/discovery guard"),
    ]
    for path, marker, label in code_markers:
        if marker not in path.read_text(encoding="utf-8"):
            errors.append(f"{path.relative_to(ROOT)} missing {label}: {marker!r}")

    for path in CURRENT_DOCS:
        text = path.read_text(encoding="utf-8")
        if ":9100" in text or "port 9100" in text or '"port": 9100' in text:
            errors.append(f"{path.relative_to(ROOT)} still references old LLM Factory port 9100")

    _check_compose_registry_runtime(API_BACKEND_COMPOSE.read_text(encoding="utf-8"), errors)

    for path in [
        ROOT / "docs" / "architecture" / "service-communication.md",
        ROOT / "docs" / "reference" / "ports-and-config.md",
        ROOT / "docs" / "services" / "service-registry.md",
        ROOT / "docker" / "api-backend" / "README.md",
    ]:
        text = path.read_text(encoding="utf-8")
        for marker in STALE_FALLBACK_MARKERS:
            if marker in text:
                errors.append(f"{path.relative_to(ROOT)} still contains stale fallback marker: {marker!r}")

    ports_doc = (ROOT / "docs" / "reference" / "ports-and-config.md").read_text(encoding="utf-8")
    for marker in [
        "manifest/bootstrap 元数据",
        "/opt/novaic/etc/<namespace>/secrets.json",
        "service-registry",
        "127.0.0.1:19991",
        "novaic_registry_dsn",
        "registry-only runtime discovery",
        "RegistryOnlyResolver",
        "不做 runtime fallback",
    ]:
        if marker not in ports_doc:
            errors.append(f"docs/reference/ports-and-config.md missing marker {marker!r}")

    communication_doc = (ROOT / "docs" / "architecture" / "service-communication.md").read_text(encoding="utf-8")
    for marker in ["ServiceRegistry", "RegistryOnlyResolver", "service_runtime", "service-registry", "19991", "不使用静态 URL 回退"]:
        if marker not in communication_doc:
            errors.append(f"docs/architecture/service-communication.md missing marker {marker!r}")

    service_doc = (ROOT / "docs" / "services" / "service-registry.md").read_text(encoding="utf-8")
    for marker in [
        "/v1/registry/namespaces/{namespace}/instances",
        "/v1/registry/namespaces/{namespace}/instances/{service_name}/{instance_id}",
        "(namespace, service_name, instance_id)",
        "service_registry_instances",
        "registry-only",
        "deregister",
    ]:
        if marker not in service_doc:
            errors.append(f"docs/services/service-registry.md missing marker {marker!r}")

    if errors:
        print("lint_service_catalog_discovery FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("lint_service_catalog_discovery OK")
    return 0


def _check_compose_registry_runtime(text: str, errors: list[str]) -> None:
    for compose_service, service_name in REGISTERED_COMPOSE_SERVICES.items():
        service_block = _compose_service_block(text, compose_service)
        if "common.service_runtime" not in service_block:
            errors.append(f"docker/api-backend/compose.yaml {compose_service} is not wrapped by common.service_runtime")
        if f"- {service_name}" not in service_block:
            errors.append(f"docker/api-backend/compose.yaml {compose_service} missing registry service name {service_name!r}")
        for marker in ["--instance-id", "--advertise-url", "--health-path", "--compose-service"]:
            if f"- {marker}" not in service_block:
                errors.append(f"docker/api-backend/compose.yaml {compose_service} missing {marker}")

    for binding in REQUIRED_REGISTRY_BINDINGS:
        if f"- {binding}" not in text:
            errors.append(f"docker/api-backend/compose.yaml missing registry binding {binding!r}")

    lines = text.splitlines()
    for index, line in enumerate(lines[:-1]):
        flag = line.strip()[2:] if line.strip().startswith("- --") else ""
        if flag not in FORBIDDEN_STATIC_DEPENDENCY_FLAGS:
            continue
        next_value = lines[index + 1].strip()
        if next_value.startswith("- http://127.0.0.1:199"):
            errors.append(
                "docker/api-backend/compose.yaml has forbidden static dependency "
                f"URL after {flag} on line {index + 1}"
            )


def _compose_service_block(text: str, service_name: str) -> str:
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


if __name__ == "__main__":
    raise SystemExit(main())
