"""Executable entrypoint for the NovAIC release controller."""

from __future__ import annotations

import os

import uvicorn

from release_controller.config import load_config
from release_controller.service import create_app


def build_app():
    config_path = os.environ.get("NOVAIC_RELEASE_CONTROLLER_CONFIG")
    if not config_path:
        raise RuntimeError("NOVAIC_RELEASE_CONTROLLER_CONFIG is required")
    return create_app(load_config(config_path))


def main() -> None:
    app = build_app()
    config = app.extra.get("controller_config")
    host = getattr(config.server, "host", "127.0.0.1") if config else "127.0.0.1"
    port = getattr(config.server, "port", 19880) if config else 19880
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
