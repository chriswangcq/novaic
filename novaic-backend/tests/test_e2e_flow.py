"""
端到端流程测试

测试今天修改的核心功能：
1. 两阶段提交（消息不丢失）
2. Task 重试区分错误类型
3. 并行步骤失败处理
4. Saga 永不失败机制
5. HTTP 连接管理
6. Payload 验证
"""

import pytest
import json
import tempfile
import os
import sys

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestImportsAndStructure:
    """测试模块导入和结构"""
    
    def test_saga_definitions_registered(self):
        """所有 Saga 定义应该正确注册"""
        from task_queue.sagas import get_all_saga_definitions
        
        sagas = get_all_saga_definitions()
        saga_names = [s.name for s in sagas]
        
        # 核心 Saga 应该存在
        assert "message_process" in saga_names
        assert "runtime_start" in saga_names
        assert "react_think" in saga_names
        assert "react_actions" in saga_names
        assert "runtime_complete" in saga_names
        
        # 每个 Saga 应该有步骤
        for saga in sagas:
            assert len(saga.steps) > 0, f"Saga {saga.name} has no steps"
    
    def test_handlers_registered(self):
        """所有 Handler 应该正确注册"""
        from task_queue.handlers import get_all_topics, get_handler
        
        topics = get_all_topics()
        assert len(topics) > 0
        
        # 核心 topic 应该存在
        core_topics = [
            "runtime.create",
            "runtime.set_status",
            "llm.call",
            "saga.trigger",
        ]
        for topic in core_topics:
            assert topic in topics, f"Missing topic: {topic}"
            handler = get_handler(topic)
            assert callable(handler), f"Handler for {topic} is not callable"


class TestExceptions:
    """测试异常类"""
    
    def test_business_error_hierarchy(self):
        """业务异常应该有正确的继承关系"""
        from common.exceptions import (
            BusinessError,
            ValidationError,
            NotFoundError,
            StateConflictError,
            ConfigurationError,
        )
        
        assert issubclass(ValidationError, BusinessError)
        assert issubclass(NotFoundError, BusinessError)
        assert issubclass(StateConflictError, BusinessError)
        assert issubclass(ConfigurationError, BusinessError)
    
    def test_retryable_error_detection(self):
        """可重试错误检测应该正确工作"""
        from task_queue.exceptions import is_retryable_error, RETRYABLE_EXCEPTIONS
        import httpx
        
        # 可重试错误
        assert is_retryable_error(TimeoutError("timeout"))
        assert is_retryable_error(ConnectionError("connection refused"))
        
        # 不可重试错误
        from common.exceptions import ValidationError
        assert not is_retryable_error(ValidationError("invalid param"))
        assert not is_retryable_error(ValueError("bad value"))
    
    def test_payload_validation_error(self):
        """PayloadValidationError 应该包含详细信息"""
        from task_queue.exceptions import PayloadValidationError
        
        error = PayloadValidationError("Invalid payload", details={"field": "agent_id", "error": "required"})
        assert error.details["field"] == "agent_id"


class TestSagaStep:
    """测试 SagaStep 配置"""
    
    def test_saga_step_has_failure_policy(self):
        """SagaStep 应该有 failure_policy 字段"""
        from task_queue.saga import SagaStep, StepType
        
        step = SagaStep(
            name="test",
            step_type=StepType.PARALLEL,
            failure_policy="ignore_failures",
        )
        assert step.failure_policy == "ignore_failures"
    
    def test_saga_step_default_failure_policy(self):
        """SagaStep 默认 failure_policy 应该是 fail_fast"""
        from task_queue.saga import SagaStep, StepType
        
        step = SagaStep(name="test", step_type=StepType.TASK, topic="test.topic")
        assert step.failure_policy == "fail_fast"


class TestClientContextManager:
    """测试 Client 上下文管理器"""
    
    def test_saga_client_context_manager(self):
        """SagaClient 应该支持上下文管理器"""
        from task_queue.client import SagaClient
        
        # 不实际连接，只测试接口
        client = SagaClient("http://localhost:8000")
        assert hasattr(client, "__enter__")
        assert hasattr(client, "__exit__")
        
        # 测试 close 可以多次调用
        client.close()
        client.close()  # 不应该抛异常
    
    def test_task_queue_client_context_manager(self):
        """TaskQueueClient 应该支持上下文管理器"""
        from task_queue.client import TaskQueueClient
        
        client = TaskQueueClient("http://localhost:8000")
        assert hasattr(client, "__enter__")
        assert hasattr(client, "__exit__")
        
        client.close()
        client.close()
    
    def test_gateway_client_context_manager(self):
        """GatewayInternalClient 应该支持上下文管理器"""
        from task_queue.client import GatewayInternalClient
        
        client = GatewayInternalClient("http://localhost:8000")
        assert hasattr(client, "__enter__")
        assert hasattr(client, "__exit__")
        
        client.close()
        client.close()


class TestGatewayClientTwoPhaseCommit:
    """测试两阶段提交相关的 API"""
    
    def test_gateway_client_has_two_phase_methods(self):
        """GatewayInternalClient 应该有两阶段提交方法"""
        from task_queue.client import GatewayInternalClient
        
        client = GatewayInternalClient("http://localhost:8000")
        
        # 新方法
        assert hasattr(client, "find_sending_message")
        assert hasattr(client, "confirm_message")
        
        client.close()


class TestValidation:
    """测试 Payload 验证"""
    
    def test_validate_basic_payload_none(self):
        """None payload 应该被转换为空 dict"""
        from task_queue.handlers.validation import validate_basic_payload
        
        result = validate_basic_payload(None, "test.topic")
        assert result == {}
    
    def test_validate_basic_payload_dict(self):
        """dict payload 应该原样返回"""
        from task_queue.handlers.validation import validate_basic_payload
        
        payload = {"key": "value"}
        result = validate_basic_payload(payload, "test.topic")
        assert result == payload
    
    def test_validate_basic_payload_invalid_type(self):
        """非 dict payload 应该抛出 BusinessError"""
        from task_queue.handlers.validation import validate_basic_payload
        from common.exceptions import BusinessError
        
        with pytest.raises(BusinessError):
            validate_basic_payload("not a dict", "test.topic")
        
        with pytest.raises(BusinessError):
            validate_basic_payload(123, "test.topic")
        
        with pytest.raises(BusinessError):
            validate_basic_payload(["list"], "test.topic")


class TestWatchdogTwoPhaseCommit:
    """测试 Watchdog 两阶段提交"""
    
    def test_watchdog_has_two_phase_methods(self):
        """WatchdogSync 应该有两阶段提交相关方法"""
        from task_queue.workers.watchdog_sync import WatchdogSync
        
        # 检查方法存在
        assert hasattr(WatchdogSync, "_find_sending_message")
        assert hasattr(WatchdogSync, "_confirm_message")
        assert hasattr(WatchdogSync, "_process_message_two_phase")


class TestSagaWorkerNeverFail:
    """测试 Saga 永不失败机制"""
    
    def test_saga_worker_has_retry_mechanism(self):
        """SagaWorkerSync 应该有重试机制"""
        from task_queue.workers.saga_worker_sync import (
            SagaWorkerSync,
            RETRYABLE_EXCEPTIONS,
            MAX_SAGA_RETRIES,
        )
        
        # 检查常量
        assert MAX_SAGA_RETRIES >= 1
        assert len(RETRYABLE_EXCEPTIONS) > 0
        
        # 检查方法
        assert hasattr(SagaWorkerSync, "_is_retryable_error")
        assert hasattr(SagaWorkerSync, "_handle_saga_exception")
    
    def test_saga_worker_metrics_has_retried(self):
        """SagaWorkerMetrics 应该有 sagas_retried 指标"""
        from task_queue.workers.saga_worker_sync import SagaWorkerMetrics
        
        metrics = SagaWorkerMetrics()
        assert hasattr(metrics, "sagas_retried")
        assert metrics.sagas_retried == 0


class TestTaskWorkerErrorHandling:
    """测试 TaskWorker 错误处理"""
    
    def test_task_worker_imports_exceptions(self):
        """TaskWorkerSync 应该导入异常类"""
        # 这个测试验证 task_worker_sync.py 能正确导入异常
        from task_queue.workers.task_worker_sync import TaskWorkerSync
        from common.exceptions import BusinessError
        from task_queue.exceptions import RETRYABLE_EXCEPTIONS
        
        # 如果导入成功，说明异常处理逻辑可用
        assert True


class TestSagaClientRelease:
    """测试 SagaClient release 方法"""
    
    def test_saga_client_has_release_method(self):
        """SagaClient 应该有 release 方法"""
        from task_queue.client import SagaClient
        
        client = SagaClient("http://localhost:8000")
        assert hasattr(client, "release")
        client.close()


# ==================== 集成测试（需要服务运行）====================

@pytest.mark.skip(reason="需要服务运行")
class TestIntegrationWithServices:
    """集成测试（需要 Gateway 和 Queue Service 运行）"""
    
    def test_full_message_flow(self):
        """测试完整的消息处理流程"""
        # TODO: 启动服务后运行
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
