# P505 pre-cleanup reference sweep
created: 2026-05-17T12:27:08Z

## constants references
./novaic-agent-runtime/task_queue/constants.py:1:"""Deprecated phase string constants (inline values; do not import from shared package)."""
./novaic-agent-runtime/task_queue/constants.py:3:PHASE_NEED_THINK = "need_think"
./novaic-agent-runtime/task_queue/constants.py:4:PHASE_WAITING_ACTIONS = "waiting_actions"
./novaic-agent-runtime/task_queue/constants.py:5:PHASE_COMPLETED = "completed"
./novaic-agent-runtime/task_queue/constants.py:7:__all__ = ["PHASE_NEED_THINK", "PHASE_WAITING_ACTIONS", "PHASE_COMPLETED"]

## deprecated polling comment references
novaic-agent-runtime/task_queue/client.py:678:    # ---------- Deprecated Message polling removed ----------

## session_ended remaining_stack signature
502:    def session_ended(
510:        remaining_stack: Optional[Dict[str, Any]] = None,
528:            "remaining_stack": dict(remaining_stack or {}),
