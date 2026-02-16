"""Unified strict configuration facade."""

from common.strict_config import load_services_config


_CFG = load_services_config()


class ServiceConfig:
    """服务配置"""

    # Database files (hard split, no legacy compatibility)
    GATEWAY_DB_FILE = _CFG.get("database", "gateway_db_file")
    RUNTIME_ORCHESTRATOR_DB_FILE = _CFG.get("database", "runtime_orchestrator_db_file")
    DATA_DIR = _CFG.get("paths", "data_dir")
    
    # Gateway
    GATEWAY_HOST = _CFG.get("services", "gateway", "host")
    GATEWAY_PORT = int(_CFG.get("services", "gateway", "port"))
    GATEWAY_URL = _CFG.get("services", "gateway", "url")
    
    # Queue Service
    QUEUE_SERVICE_HOST = _CFG.get("services", "queue_service", "host")
    QUEUE_SERVICE_PORT = int(_CFG.get("services", "queue_service", "port"))
    QUEUE_SERVICE_URL = _CFG.get("services", "queue_service", "url")
    
    # Tools Server
    TOOLS_SERVER_HOST = _CFG.get("services", "tools_server", "host")
    TOOLS_SERVER_PORT = int(_CFG.get("services", "tools_server", "port"))
    TOOLS_SERVER_URL = _CFG.get("services", "tools_server", "url")
    
    # VMControl (Rust service)
    VMCONTROL_HOST = _CFG.get("services", "vmcontrol", "host")
    VMCONTROL_PORT = int(_CFG.get("services", "vmcontrol", "port"))
    VMCONTROL_URL = _CFG.get("services", "vmcontrol", "url")
    
    # File Service
    FILE_SERVICE_HOST = _CFG.get("services", "file_service", "host")
    FILE_SERVICE_PORT = int(_CFG.get("services", "file_service", "port"))
    FILE_SERVICE_URL = _CFG.get("services", "file_service", "url")
    
    # Tool Result Service
    TOOL_RESULT_SERVICE_HOST = _CFG.get("services", "tool_result_service", "host")
    TOOL_RESULT_SERVICE_PORT = int(_CFG.get("services", "tool_result_service", "port"))
    TOOL_RESULT_SERVICE_URL = _CFG.get("services", "tool_result_service", "url")

    # Runtime Orchestrator (Phase 4)
    RUNTIME_ORCHESTRATOR_HOST = _CFG.get("services", "runtime_orchestrator", "host")
    RUNTIME_ORCHESTRATOR_PORT = int(_CFG.get("services", "runtime_orchestrator", "port"))
    RUNTIME_ORCHESTRATOR_URL = _CFG.get("services", "runtime_orchestrator", "url")
    
    # Timeouts
    # 超时配置计算逻辑：
    # - LLM_TIMEOUT = 300s
    # - max_retries = 3 (共 4 次尝试)
    # - Task 总执行时间 = 300s × 4 = 1200s
    # - 确保 SAGA_STEP_TIMEOUT > LLM_TIMEOUT × (max_retries + 1)
    TASK_TIMEOUT = int(_CFG.get("timeouts", "task_timeout"))
    SAGA_STEP_TIMEOUT = int(_CFG.get("timeouts", "saga_step_timeout"))  # 25 分钟，覆盖 Task 重试
    SAGA_TIMEOUT = int(_CFG.get("timeouts", "saga_timeout"))  # 30 分钟，Saga 整体超时
    HTTP_TIMEOUT = float(_CFG.get("timeouts", "http_timeout"))
    # Internal service-to-service HTTP calls should bypass system proxy by default.
    INTERNAL_HTTP_TRUST_ENV = bool(_CFG.get("timeouts", "internal_http_trust_env"))
    
    # Intervals
    HEARTBEAT_INTERVAL = float(_CFG.get("worker", "heartbeat_interval"))
    POLL_INTERVAL = float(_CFG.get("worker", "poll_interval"))
    
    # Concurrency
    NUM_WORKERS = int(_CFG.get("worker", "num_workers"))
    MAX_CONCURRENT_SAGAS = int(_CFG.get("worker", "max_concurrent_sagas"))
    
    # ===== 业务逻辑配置 =====
    
    # HRL (Hot Runtime List) 配置
    HRL_TRIGGER_LENGTH = int(_CFG.get("runtime", "hrl_trigger_length"))
    HRL_KEEP_RECENT = int(_CFG.get("runtime", "hrl_keep_recent"))
    
    # Summary 配置
    SUMMARY_LAST_ROUNDS_FULL = int(_CFG.get("runtime", "summary_last_rounds_full"))
    SUMMARY_LAST_ROUNDS_HOT = int(_CFG.get("runtime", "summary_last_rounds_hot"))
    
    # 分页配置
    MAX_MESSAGES_PER_PAGE = int(_CFG.get("runtime", "max_messages_per_page"))
    MAX_EXECUTION_LOGS_PER_PAGE = int(_CFG.get("runtime", "max_execution_logs_per_page"))
    MAX_RUNTIME_CONTEXT_PER_PAGE = int(_CFG.get("runtime", "max_runtime_context_per_page"))
    DEFAULT_CHAT_LIMIT = int(_CFG.get("runtime", "default_chat_limit"))
    DEFAULT_SUMMARY_LENGTH = int(_CFG.get("runtime", "default_summary_length"))
    
    # 清理配置
    CLEANUP_KEEP_MESSAGES = int(_CFG.get("runtime", "cleanup_keep_messages"))
    CLEANUP_KEEP_EXECUTION_LOGS = int(_CFG.get("runtime", "cleanup_keep_execution_logs"))
    
    # Stuck 检测配置
    STUCK_AWAKING_TIMEOUT = int(_CFG.get("runtime", "stuck_awakening_timeout"))
    STUCK_SENDING_TIMEOUT = int(_CFG.get("runtime", "stuck_sending_timeout"))
    
    # ===== 超时配置扩展 =====
    
    HTTP_TIMEOUT_SHORT = float(_CFG.get("timeouts", "http_timeout_short"))
    LLM_CALL_TIMEOUT = float(_CFG.get("timeouts", "llm_call_timeout"))
    MCP_CALL_TIMEOUT = float(_CFG.get("timeouts", "mcp_call_timeout"))
    DB_TRANSACTION_TIMEOUT = float(_CFG.get("timeouts", "db_transaction_timeout"))
    DB_TRANSACTION_TIMEOUT_LONG = float(_CFG.get("timeouts", "db_transaction_timeout_long"))
    
    # VM 配置
    VM_MCP_TIMEOUT = int(_CFG.get("runtime", "vm_mcp_timeout"))
    SSH_QUICK_TIMEOUT = int(_CFG.get("runtime", "ssh_quick_timeout"))
    SSH_NORMAL_TIMEOUT = int(_CFG.get("runtime", "ssh_normal_timeout"))
    
    # ===== VMUSE 配置 =====
    
    # 使用传统 VMUSE MCP 还是新的 vmcontrol 适配器
    USE_LEGACY_VMUSE = bool(_CFG.get("runtime", "use_legacy_vmuse"))
    VMUSE_MCP_URL = _CFG.get("runtime", "vmuse_mcp_url")
    
    # ===== LLM 配置 =====
    
    LLM_MAX_TOKENS_DEFAULT = int(_CFG.get("llm", "max_tokens_default"))
    LLM_TEMPERATURE_DEFAULT = float(_CFG.get("llm", "temperature_default"))
    
    # ===== 文本截断配置 =====
    
    TEXT_TRUNCATE_THINK = int(_CFG.get("text_truncate", "think"))
    TEXT_TRUNCATE_ARGS = int(_CFG.get("text_truncate", "args"))
    TEXT_TRUNCATE_RESULT = int(_CFG.get("text_truncate", "result"))
    TEXT_TRUNCATE_LLM_INPUT = int(_CFG.get("text_truncate", "llm_input"))
    TEXT_TRUNCATE_ERROR = int(_CFG.get("text_truncate", "error"))
    TEXT_TRUNCATE_REASONING = int(_CFG.get("text_truncate", "reasoning"))
    TEXT_TRUNCATE_MESSAGE = int(_CFG.get("text_truncate", "message"))
    
    # ===== 长结果截断配置 =====
    
    AUTO_TRUNCATE_ENABLED = bool(_CFG.get("auto_truncate", "enabled"))
    AUTO_TRUNCATE_THRESHOLD_SMALL = int(_CFG.get("auto_truncate", "threshold_small"))  # 4KB（仅文本）
    AUTO_TRUNCATE_THRESHOLD_LARGE = int(_CFG.get("auto_truncate", "threshold_large"))  # 10KB（仅文本）
    AUTO_TRUNCATE_HEAD_SIZE = int(_CFG.get("auto_truncate", "head_size"))  # 1.5KB
    AUTO_TRUNCATE_TAIL_SIZE = int(_CFG.get("auto_truncate", "tail_size"))  # 1.5KB
    AUTO_TRUNCATE_TTL_HOURS = int(_CFG.get("auto_truncate", "ttl_hours"))
    
    # ===== 图像处理配置 =====
    
    IMAGE_COMPRESS_ENABLED = bool(_CFG.get("image", "compress_enabled"))
    IMAGE_MAX_SIZE_KB = int(_CFG.get("image", "max_size_kb"))  # 500KB
    IMAGE_MAX_DIMENSION = int(_CFG.get("image", "max_dimension"))  # 1920px
    IMAGE_QUALITY = int(_CFG.get("image", "quality"))  # 85%
    
    # ===== 重试配置 =====
    
    DEFAULT_MAX_RETRIES = int(_CFG.get("retry", "default_max_retries"))
    RETRY_BACKOFF_BASE = float(_CFG.get("retry", "backoff_base"))
    RETRY_BACKOFF_MAX = float(_CFG.get("retry", "backoff_max"))
    
    @classmethod
    def validate(cls):
        """验证配置有效性"""
        errors = []
        
        # 验证端口范围
        if not (1024 <= cls.GATEWAY_PORT <= 65535):
            errors.append(f"Invalid GATEWAY_PORT: {cls.GATEWAY_PORT}")
        
        if not (1024 <= cls.QUEUE_SERVICE_PORT <= 65535):
            errors.append(f"Invalid QUEUE_SERVICE_PORT: {cls.QUEUE_SERVICE_PORT}")
        
        if not (1024 <= cls.TOOLS_SERVER_PORT <= 65535):
            errors.append(f"Invalid TOOLS_SERVER_PORT: {cls.TOOLS_SERVER_PORT}")
        
        if not (1024 <= cls.VMCONTROL_PORT <= 65535):
            errors.append(f"Invalid VMCONTROL_PORT: {cls.VMCONTROL_PORT}")
        
        if not (1024 <= cls.FILE_SERVICE_PORT <= 65535):
            errors.append(f"Invalid FILE_SERVICE_PORT: {cls.FILE_SERVICE_PORT}")
        
        if not (1024 <= cls.TOOL_RESULT_SERVICE_PORT <= 65535):
            errors.append(f"Invalid TOOL_RESULT_SERVICE_PORT: {cls.TOOL_RESULT_SERVICE_PORT}")
        
        # 验证超时值
        if cls.TASK_TIMEOUT <= 0:
            errors.append(f"Invalid TASK_TIMEOUT: {cls.TASK_TIMEOUT}")
        
        if cls.SAGA_TIMEOUT <= 0:
            errors.append(f"Invalid SAGA_TIMEOUT: {cls.SAGA_TIMEOUT}")
        
        if cls.SAGA_STEP_TIMEOUT <= 0:
            errors.append(f"Invalid SAGA_STEP_TIMEOUT: {cls.SAGA_STEP_TIMEOUT}")
        
        if cls.HTTP_TIMEOUT <= 0:
            errors.append(f"Invalid HTTP_TIMEOUT: {cls.HTTP_TIMEOUT}")
        
        # 验证间隔值
        if cls.HEARTBEAT_INTERVAL <= 0:
            errors.append(f"Invalid HEARTBEAT_INTERVAL: {cls.HEARTBEAT_INTERVAL}")
        
        if cls.POLL_INTERVAL <= 0:
            errors.append(f"Invalid POLL_INTERVAL: {cls.POLL_INTERVAL}")
        
        # 验证并发值
        if cls.NUM_WORKERS <= 0:
            errors.append(f"Invalid NUM_WORKERS: {cls.NUM_WORKERS}")
        
        if cls.MAX_CONCURRENT_SAGAS <= 0:
            errors.append(f"Invalid MAX_CONCURRENT_SAGAS: {cls.MAX_CONCURRENT_SAGAS}")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True
