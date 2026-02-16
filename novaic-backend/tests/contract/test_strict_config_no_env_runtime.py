from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

# Runtime service-routing config keys must not be read directly from env.
DISALLOWED_ENV_KEYS = [
    "GATEWAY_URL",
    "NOVAIC_GATEWAY_URL",
    "QUEUE_SERVICE_URL",
    "NOVAIC_QUEUE_SERVICE_URL",
    "TOOLS_SERVER_URL",
    "NOVAIC_TOOLS_SERVER_URL",
    "RUNTIME_ORCHESTRATOR_URL",
    "NOVAIC_RUNTIME_ORCHESTRATOR_URL",
]

TARGET_FILES = [
    ROOT / "main_novaic.py",
    ROOT / "main_gateway.py",
    ROOT / "main_tools.py",
    ROOT / "main_runtime_orchestrator.py",
    ROOT / "tools_server" / "api.py",
    ROOT / "tools_server" / "executor.py",
    ROOT / "task_queue" / "client.py",
    ROOT / "task_queue" / "business" / "mcp.py",
    ROOT / "task_queue" / "handlers" / "llm_handlers.py",
    ROOT / "tool_result_service" / "config.py",
]


def test_runtime_service_urls_not_read_from_env():
    for file_path in TARGET_FILES:
        text = file_path.read_text(encoding="utf-8")
        for key in DISALLOWED_ENV_KEYS:
            assert f'os.getenv("{key}"' not in text, f"{file_path} reads {key} via os.getenv"
            assert f"os.environ.get('{key}'" not in text, f"{file_path} reads {key} via os.environ.get"
            assert f'os.environ.get("{key}"' not in text, f"{file_path} reads {key} via os.environ.get"
