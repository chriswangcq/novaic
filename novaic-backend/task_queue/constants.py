"""
Task Queue constants.
"""

# Runtime phases (DEPRECATED - Saga 步骤替代 phase 状态)
# 保留常量定义以兼容旧代码，但不再用于流程控制
PHASE_NEED_THINK = "need_think"
PHASE_WAITING_ACTIONS = "waiting_actions"
PHASE_COMPLETED = "completed"
