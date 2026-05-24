# syntax=docker/dockerfile:1.7

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NOVAIC_RELEASE_CONTROLLER_CONFIG=/opt/novaic/release-controller/config.json

WORKDIR /opt/novaic/release-controller

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        docker.io \
        git \
    && rm -rf /var/lib/apt/lists/*

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
