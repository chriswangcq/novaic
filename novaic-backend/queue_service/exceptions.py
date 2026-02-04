"""
Task Queue 异常定义
"""


class TaskQueueError(Exception):
    """Task Queue 基础异常"""
    pass


class RetryableError(TaskQueueError):
    """
    可重试错误
    
    抛出此异常表示任务应该被释放回 pending 状态，
    由其他 Worker 重新认领并重试。
    
    用于瞬态错误，如：
    - 网络超时
    - 外部服务暂时不可用
    - 资源锁竞争失败
    """
    pass


class TaskNotFoundError(TaskQueueError):
    """任务不存在"""
    pass


class TaskClaimError(TaskQueueError):
    """任务认领失败"""
    pass


class SagaError(TaskQueueError):
    """Saga 执行错误"""
    pass


class SagaStepError(SagaError):
    """Saga 步骤执行错误"""
    
    def __init__(self, step_name: str, message: str, original_error: Exception = None):
        self.step_name = step_name
        self.original_error = original_error
        super().__init__(f"Step '{step_name}' failed: {message}")


class SagaCompensationError(SagaError):
    """Saga 补偿操作错误"""
    
    def __init__(self, step_name: str, message: str):
        self.step_name = step_name
        super().__init__(f"Compensation for '{step_name}' failed: {message}")
