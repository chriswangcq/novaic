# syntax=docker/dockerfile:1.7

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NOVAIC_SERVICES_DIR=/opt/novaic/services \
    NOVAIC_DATA_DIR=/opt/novaic/data

WORKDIR /opt/novaic/services

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        libffi-dev \
        libssl-dev \
        openssh-client \
    && rm -rf /var/lib/apt/lists/*

COPY Entangled ./Entangled
COPY novaic-agent-runtime ./novaic-agent-runtime
COPY novaic-blob-service ./novaic-blob-service
COPY novaic-business ./novaic-business
COPY novaic-common ./novaic-common
COPY novaic-cortex ./novaic-cortex
COPY novaic-device ./novaic-device
COPY novaic-gateway ./novaic-gateway
COPY novaic-logicalfs ./novaic-logicalfs
COPY novaic-sandbox-sdk ./novaic-sandbox-sdk
COPY novaic-sandbox-service ./novaic-sandbox-service
COPY docker/api-backend/requirements.txt /tmp/novaic-api-backend-extra-requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install \
        -r novaic-gateway/requirements.txt \
        -r novaic-agent-runtime/requirements.txt \
        -r novaic-blob-service/requirements.txt \
        -r novaic-sandbox-service/requirements.txt \
        -r novaic-cortex/requirements.txt \
        -r /tmp/novaic-api-backend-extra-requirements.txt \
    && rm -f /tmp/novaic-api-backend-extra-requirements.txt

ENV PYTHONPATH="/opt/novaic/services/Entangled/packages/server-python:/opt/novaic/services/novaic-common:/opt/novaic/services/novaic-gateway:/opt/novaic/services/novaic-business:/opt/novaic/services/novaic-device:/opt/novaic/services/novaic-agent-runtime:/opt/novaic/services/novaic-blob-service:/opt/novaic/services/novaic-sandbox-service:/opt/novaic/services/novaic-cortex:/opt/novaic/services/novaic-logicalfs:/opt/novaic/services/novaic-sandbox-sdk"

RUN mkdir -p /opt/novaic/data/logs /opt/novaic/postgres/secrets \
    && python - <<'PY'
import importlib

modules = [
    "entangled.app.main",
    "entangled.app.schema",
    "common.config",
    "common.service_registry_client",
    "common.service_registry_server",
    "common.service_runtime",
    "gateway.db.postgres",
    "gateway.api.routes",
    "business.schema_push",
    "device.config_agents",
    "queue_service.db.postgres",
    "queue_service.queue_db",
    "queue_service.worker.generic_worker",
    "task_queue.workers.registry",
    "blob_service.routes",
    "blob_service.storage",
    "sandbox_service.main",
    "novaic_cortex.config",
    "novaic_cortex.store",
    "novaic_cortex.registry",
]

for module in modules:
    importlib.import_module(module)
PY

ENTRYPOINT ["python"]
CMD ["-c", "print('novaic api backend image: choose a service command in compose')"]
