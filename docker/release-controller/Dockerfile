# syntax=docker/dockerfile:1.7

FROM python:3.13-slim AS runtime

ARG DOCKER_CLI_VERSION=29.1.3
ARG DOCKER_COMPOSE_VERSION=v2.40.3

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NOVAIC_RELEASE_CONTROLLER_CONFIG=/opt/novaic/release-controller/config.json

WORKDIR /opt/novaic/release-controller

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        openssh-client \
        rsync \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
        amd64) docker_arch="x86_64"; compose_arch="x86_64" ;; \
        arm64) docker_arch="aarch64"; compose_arch="aarch64" ;; \
        *) echo "unsupported architecture: $arch" >&2; exit 1 ;; \
    esac; \
    curl -fsSL "https://download.docker.com/linux/static/stable/${docker_arch}/docker-${DOCKER_CLI_VERSION}.tgz" -o /tmp/docker.tgz; \
    tar -xzf /tmp/docker.tgz -C /tmp; \
    install -m 0755 /tmp/docker/docker /usr/local/bin/docker; \
    mkdir -p /usr/local/lib/docker/cli-plugins; \
    curl -fsSL "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-linux-${compose_arch}" -o /usr/local/lib/docker/cli-plugins/docker-compose; \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose; \
    docker --version; \
    docker compose version; \
    rm -rf /tmp/docker /tmp/docker.tgz

COPY novaic-release-controller /opt/novaic/release-controller

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install /opt/novaic/release-controller \
    && python - <<'PY'
import importlib

for module in [
    "release_controller.config",
    "release_controller.executor",
    "release_controller.planner",
    "release_controller.poller",
    "release_controller.polling",
    "release_controller.runner",
    "release_controller.service",
    "release_controller.state",
]:
    importlib.import_module(module)
PY

EXPOSE 19880

CMD ["python", "-m", "release_controller.main"]
