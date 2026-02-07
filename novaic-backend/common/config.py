"""统一配置管理模块"""
import os


class ServiceConfig:
    """服务配置"""
    
    # Gateway
    GATEWAY_HOST = os.getenv("GATEWAY_HOST", "127.0.0.1")
    GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "19999"))
    GATEWAY_URL = os.getenv("GATEWAY_URL", f"http://{GATEWAY_HOST}:{GATEWAY_PORT}")
    
    # Queue Service
    QUEUE_SERVICE_HOST = os.getenv("QUEUE_SERVICE_HOST", "127.0.0.1")
    QUEUE_SERVICE_PORT = int(os.getenv("QUEUE_SERVICE_PORT", "19997"))
    QUEUE_SERVICE_URL = os.getenv("QUEUE_SERVICE_URL", f"http://{QUEUE_SERVICE_HOST}:{QUEUE_SERVICE_PORT}")
    
    # Tools Server
    TOOLS_SERVER_HOST = os.getenv("TOOLS_SERVER_HOST", "127.0.0.1")
    TOOLS_SERVER_PORT = int(os.getenv("TOOLS_SERVER_PORT", "19998"))
    TOOLS_SERVER_URL = os.getenv("TOOLS_SERVER_URL", f"http://{TOOLS_SERVER_HOST}:{TOOLS_SERVER_PORT}")
    
    # VMControl (Rust service)
    VMCONTROL_HOST = os.getenv("VMCONTROL_HOST", "127.0.0.1")
    VMCONTROL_PORT = int(os.getenv("VMCONTROL_PORT", "8080"))
    VMCONTROL_URL = os.getenv("VMCONTROL_URL", f"http://{VMCONTROL_HOST}:{VMCONTROL_PORT}")
    
    # Timeouts
    TASK_TIMEOUT = int(os.getenv("TASK_TIMEOUT", "60"))
    SAGA_TIMEOUT = int(os.getenv("SAGA_TIMEOUT", "300"))
    SAGA_STEP_TIMEOUT = int(os.getenv("SAGA_STEP_TIMEOUT", "300"))
    HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "30.0"))
    
    # Intervals
    HEARTBEAT_INTERVAL = float(os.getenv("HEARTBEAT_INTERVAL", "10.0"))
    POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "0.1"))
    
    # Concurrency
    NUM_WORKERS = int(os.getenv("NUM_WORKERS", "5"))
    MAX_CONCURRENT_SAGAS = int(os.getenv("MAX_CONCURRENT_SAGAS", "10"))
    
    # ===== 业务逻辑配置 =====
    
    # HRL (Hot Runtime List) 配置
    HRL_TRIGGER_LENGTH = int(os.getenv("HRL_TRIGGER_LENGTH", "15"))
    HRL_KEEP_RECENT = int(os.getenv("HRL_KEEP_RECENT", "5"))
    
    # Summary 配置
    SUMMARY_LAST_ROUNDS_FULL = int(os.getenv("SUMMARY_LAST_ROUNDS_FULL", "3"))
    SUMMARY_LAST_ROUNDS_HOT = int(os.getenv("SUMMARY_LAST_ROUNDS_HOT", "5"))
    
    # 分页配置
    MAX_MESSAGES_PER_PAGE = int(os.getenv("MAX_MESSAGES_PER_PAGE", "100"))
    MAX_EXECUTION_LOGS_PER_PAGE = int(os.getenv("MAX_EXECUTION_LOGS_PER_PAGE", "100"))
    MAX_RUNTIME_CONTEXT_PER_PAGE = int(os.getenv("MAX_RUNTIME_CONTEXT_PER_PAGE", "50"))
    DEFAULT_CHAT_LIMIT = int(os.getenv("DEFAULT_CHAT_LIMIT", "20"))
    DEFAULT_SUMMARY_LENGTH = int(os.getenv("DEFAULT_SUMMARY_LENGTH", "50"))
    
    # 清理配置
    CLEANUP_KEEP_MESSAGES = int(os.getenv("CLEANUP_KEEP_MESSAGES", "200"))
    CLEANUP_KEEP_EXECUTION_LOGS = int(os.getenv("CLEANUP_KEEP_EXECUTION_LOGS", "500"))
    
    # Stuck 检测配置
    STUCK_AWAKING_TIMEOUT = int(os.getenv("STUCK_AWAKING_TIMEOUT", "60"))
    STUCK_SENDING_TIMEOUT = int(os.getenv("STUCK_SENDING_TIMEOUT", "30"))
    
    # ===== 超时配置扩展 =====
    
    HTTP_TIMEOUT_SHORT = float(os.getenv("HTTP_TIMEOUT_SHORT", "10.0"))
    LLM_CALL_TIMEOUT = float(os.getenv("LLM_CALL_TIMEOUT", "60.0"))
    MCP_CALL_TIMEOUT = float(os.getenv("MCP_CALL_TIMEOUT", "30.0"))
    DB_TRANSACTION_TIMEOUT = float(os.getenv("DB_TRANSACTION_TIMEOUT", "10.0"))
    DB_TRANSACTION_TIMEOUT_LONG = float(os.getenv("DB_TRANSACTION_TIMEOUT_LONG", "15.0"))
    
    # VM 配置
    VM_MCP_TIMEOUT = int(os.getenv("VM_MCP_TIMEOUT", "120"))
    SSH_QUICK_TIMEOUT = int(os.getenv("SSH_QUICK_TIMEOUT", "3"))
    SSH_NORMAL_TIMEOUT = int(os.getenv("SSH_NORMAL_TIMEOUT", "10"))
    
    # ===== VMUSE 配置 =====
    
    # 使用传统 VMUSE MCP 还是新的 vmcontrol 适配器
    USE_LEGACY_VMUSE = os.getenv("USE_LEGACY_VMUSE", "false").lower() == "true"
    VMUSE_MCP_URL = os.getenv("VMUSE_MCP_URL", "http://127.0.0.1:8080/mcp")
    
    # ===== LLM 配置 =====
    
    LLM_MAX_TOKENS_DEFAULT = int(os.getenv("LLM_MAX_TOKENS_DEFAULT", "2000"))
    LLM_TEMPERATURE_DEFAULT = float(os.getenv("LLM_TEMPERATURE_DEFAULT", "0.3"))
    
    # ===== 文本截断配置 =====
    
    TEXT_TRUNCATE_THINK = int(os.getenv("TEXT_TRUNCATE_THINK", "500"))
    TEXT_TRUNCATE_ARGS = int(os.getenv("TEXT_TRUNCATE_ARGS", "200"))
    TEXT_TRUNCATE_RESULT = int(os.getenv("TEXT_TRUNCATE_RESULT", "2000"))
    TEXT_TRUNCATE_LLM_INPUT = int(os.getenv("TEXT_TRUNCATE_LLM_INPUT", "1000"))
    TEXT_TRUNCATE_ERROR = int(os.getenv("TEXT_TRUNCATE_ERROR", "200"))
    TEXT_TRUNCATE_REASONING = int(os.getenv("TEXT_TRUNCATE_REASONING", "500"))
    TEXT_TRUNCATE_MESSAGE = int(os.getenv("TEXT_TRUNCATE_MESSAGE", "500"))
    
    # ===== 重试配置 =====
    
    DEFAULT_MAX_RETRIES = int(os.getenv("DEFAULT_MAX_RETRIES", "3"))
    RETRY_BACKOFF_BASE = float(os.getenv("RETRY_BACKOFF_BASE", "2.0"))
    RETRY_BACKOFF_MAX = float(os.getenv("RETRY_BACKOFF_MAX", "60.0"))
    
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
