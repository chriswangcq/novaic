"""Unified strict configuration facade."""

from common.strict_config import load_services_config


_CFG = load_services_config()


class ServiceConfig:
    """服务配置"""

    GATEWAY_DB_FILE = _CFG.get("database", "gateway_db_file")
    RUNTIME_ORCHESTRATOR_DB_FILE = _CFG.get("database", "runtime_orchestrator_db_file")
    DATA_DIR = _CFG.get("paths", "data_dir")

    GATEWAY_HOST = _CFG.get("services", "gateway", "host")
    GATEWAY_PORT = int(_CFG.get("services", "gateway", "port"))
    GATEWAY_URL = _CFG.get("services", "gateway", "url")

    QUEUE_SERVICE_HOST = _CFG.get("services", "queue_service", "host")
    QUEUE_SERVICE_PORT = int(_CFG.get("services", "queue_service", "port"))
    QUEUE_SERVICE_URL = _CFG.get("services", "queue_service", "url")

    TOOLS_SERVER_HOST = _CFG.get("services", "tools_server", "host")
    TOOLS_SERVER_PORT = int(_CFG.get("services", "tools_server", "port"))
    TOOLS_SERVER_URL = _CFG.get("services", "tools_server", "url")

    VMCONTROL_HOST = _CFG.get("services", "vmcontrol", "host")
    VMCONTROL_PORT = int(_CFG.get("services", "vmcontrol", "port"))
    VMCONTROL_URL = _CFG.get("services", "vmcontrol", "url")

    FILE_SERVICE_HOST = _CFG.get("services", "file_service", "host")
    FILE_SERVICE_PORT = int(_CFG.get("services", "file_service", "port"))
    FILE_SERVICE_URL = _CFG.get("services", "file_service", "url")

    TOOL_RESULT_SERVICE_HOST = _CFG.get("services", "tool_result_service", "host")
    TOOL_RESULT_SERVICE_PORT = int(_CFG.get("services", "tool_result_service", "port"))
    TOOL_RESULT_SERVICE_URL = _CFG.get("services", "tool_result_service", "url")

    RUNTIME_ORCHESTRATOR_HOST = _CFG.get("services", "runtime_orchestrator", "host")
    RUNTIME_ORCHESTRATOR_PORT = int(_CFG.get("services", "runtime_orchestrator", "port"))
    RUNTIME_ORCHESTRATOR_URL = _CFG.get("services", "runtime_orchestrator", "url")

    TASK_TIMEOUT = int(_CFG.get("timeouts", "task_timeout"))
    SAGA_STEP_TIMEOUT = int(_CFG.get("timeouts", "saga_step_timeout"))
    SAGA_TIMEOUT = int(_CFG.get("timeouts", "saga_timeout"))
    HTTP_TIMEOUT = float(_CFG.get("timeouts", "http_timeout"))
    INTERNAL_HTTP_TRUST_ENV = bool(_CFG.get("timeouts", "internal_http_trust_env"))

    HEARTBEAT_INTERVAL = float(_CFG.get("worker", "heartbeat_interval"))
    POLL_INTERVAL = float(_CFG.get("worker", "poll_interval"))

    NUM_WORKERS = int(_CFG.get("worker", "num_workers"))
    MAX_CONCURRENT_SAGAS = int(_CFG.get("worker", "max_concurrent_sagas"))

    HRL_TRIGGER_LENGTH = int(_CFG.get("runtime", "hrl_trigger_length"))
    HRL_KEEP_RECENT = int(_CFG.get("runtime", "hrl_keep_recent"))

    SUMMARY_LAST_ROUNDS_FULL = int(_CFG.get("runtime", "summary_last_rounds_full"))
    SUMMARY_LAST_ROUNDS_HOT = int(_CFG.get("runtime", "summary_last_rounds_hot"))

    MAX_MESSAGES_PER_PAGE = int(_CFG.get("runtime", "max_messages_per_page"))
    MAX_EXECUTION_LOGS_PER_PAGE = int(_CFG.get("runtime", "max_execution_logs_per_page"))
    MAX_RUNTIME_CONTEXT_PER_PAGE = int(_CFG.get("runtime", "max_runtime_context_per_page"))
    DEFAULT_CHAT_LIMIT = int(_CFG.get("runtime", "default_chat_limit"))
    DEFAULT_SUMMARY_LENGTH = int(_CFG.get("runtime", "default_summary_length"))

    CLEANUP_KEEP_MESSAGES = int(_CFG.get("runtime", "cleanup_keep_messages"))
    CLEANUP_KEEP_EXECUTION_LOGS = int(_CFG.get("runtime", "cleanup_keep_execution_logs"))

    STUCK_AWAKING_TIMEOUT = int(_CFG.get("runtime", "stuck_awakening_timeout"))
    STUCK_SENDING_TIMEOUT = int(_CFG.get("runtime", "stuck_sending_timeout"))

    HTTP_TIMEOUT_SHORT = float(_CFG.get("timeouts", "http_timeout_short"))
    LLM_CALL_TIMEOUT = float(_CFG.get("timeouts", "llm_call_timeout"))
    MCP_CALL_TIMEOUT = float(_CFG.get("timeouts", "mcp_call_timeout"))
    DB_TRANSACTION_TIMEOUT = float(_CFG.get("timeouts", "db_transaction_timeout"))
    DB_TRANSACTION_TIMEOUT_LONG = float(_CFG.get("timeouts", "db_transaction_timeout_long"))

    VM_MCP_TIMEOUT = int(_CFG.get("runtime", "vm_mcp_timeout"))
    SSH_QUICK_TIMEOUT = int(_CFG.get("runtime", "ssh_quick_timeout"))
    SSH_NORMAL_TIMEOUT = int(_CFG.get("runtime", "ssh_normal_timeout"))

    USE_LEGACY_VMUSE = bool(_CFG.get("runtime", "use_legacy_vmuse"))
    VMUSE_MCP_URL = _CFG.get("runtime", "vmuse_mcp_url")

    LLM_MAX_TOKENS_DEFAULT = int(_CFG.get("llm", "max_tokens_default"))
    LLM_TEMPERATURE_DEFAULT = float(_CFG.get("llm", "temperature_default"))

    TEXT_TRUNCATE_THINK = int(_CFG.get("text_truncate", "think"))
    TEXT_TRUNCATE_ARGS = int(_CFG.get("text_truncate", "args"))
    TEXT_TRUNCATE_RESULT = int(_CFG.get("text_truncate", "result"))
    TEXT_TRUNCATE_LLM_INPUT = int(_CFG.get("text_truncate", "llm_input"))
    TEXT_TRUNCATE_ERROR = int(_CFG.get("text_truncate", "error"))
    TEXT_TRUNCATE_REASONING = int(_CFG.get("text_truncate", "reasoning"))
    TEXT_TRUNCATE_MESSAGE = int(_CFG.get("text_truncate", "message"))

    AUTO_TRUNCATE_ENABLED = bool(_CFG.get("auto_truncate", "enabled"))
    AUTO_TRUNCATE_THRESHOLD_SMALL = int(_CFG.get("auto_truncate", "threshold_small"))
    AUTO_TRUNCATE_THRESHOLD_LARGE = int(_CFG.get("auto_truncate", "threshold_large"))
    AUTO_TRUNCATE_HEAD_SIZE = int(_CFG.get("auto_truncate", "head_size"))
    AUTO_TRUNCATE_TAIL_SIZE = int(_CFG.get("auto_truncate", "tail_size"))
    AUTO_TRUNCATE_TTL_HOURS = int(_CFG.get("auto_truncate", "ttl_hours"))

    IMAGE_COMPRESS_ENABLED = bool(_CFG.get("image", "compress_enabled"))
    IMAGE_MAX_SIZE_KB = int(_CFG.get("image", "max_size_kb"))
    IMAGE_MAX_DIMENSION = int(_CFG.get("image", "max_dimension"))
    IMAGE_QUALITY = int(_CFG.get("image", "quality"))

    DEFAULT_MAX_RETRIES = int(_CFG.get("retry", "default_max_retries"))
    RETRY_BACKOFF_BASE = float(_CFG.get("retry", "backoff_base"))
    RETRY_BACKOFF_MAX = float(_CFG.get("retry", "backoff_max"))
