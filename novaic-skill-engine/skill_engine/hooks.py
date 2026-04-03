"""
Skill Engine — Hooks (生命周期钩子)

借鉴 Claude Code parseHooksFromFrontmatter():
技能在特定时机触发回调 — pre_invoke / post_invoke / on_error。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("skill_engine.hooks")


class HookEvent(str, Enum):
    """钩子事件类型"""
    PRE_INVOKE = "pre_invoke"       # 技能调用前
    POST_INVOKE = "post_invoke"     # 技能调用后
    ON_ERROR = "on_error"           # 技能执行出错时
    ON_ACTIVATE = "on_activate"     # 条件激活时
    ON_COMPACT = "on_compact"       # 上下文压缩后


@dataclass
class HookDefinition:
    """钩子定义"""
    event: HookEvent
    command: str = ""               # Shell 命令（可选）
    callback_id: str = ""           # 回调 ID（集成方注册）
    timeout: int = 30               # 超时秒数


@dataclass
class HooksConfig:
    """
    技能的钩子配置
    
    Example YAML:
        hooks:
          pre_invoke:
            command: "echo 'Starting skill...'"
          post_invoke:
            command: "notify-send 'Skill completed'"
          on_error:
            callback_id: "error_handler_v1"
    """
    hooks: Dict[HookEvent, HookDefinition] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: Optional[Dict[str, Any]]) -> "HooksConfig":
        """从 frontmatter dict 解析 hooks 配置"""
        if not raw:
            return cls()

        hooks = {}
        for key, value in raw.items():
            try:
                event = HookEvent(key)
            except ValueError:
                logger.warning("[Hooks] Unknown event: %s", key)
                continue

            if isinstance(value, str):
                hooks[event] = HookDefinition(event=event, command=value)
            elif isinstance(value, dict):
                hooks[event] = HookDefinition(
                    event=event,
                    command=value.get("command", ""),
                    callback_id=value.get("callback_id", ""),
                    timeout=value.get("timeout", 30),
                )

        return cls(hooks=hooks)

    def has_hook(self, event: HookEvent) -> bool:
        return event in self.hooks

    def get_hook(self, event: HookEvent) -> Optional[HookDefinition]:
        return self.hooks.get(event)


# ── 钩子执行器 ──

# 已注册的回调函数
_callbacks: Dict[str, Callable[..., Any]] = {}


def register_hook_callback(callback_id: str, fn: Callable[..., Any]) -> None:
    """
    注册钩子回调函数。
    
    集成方在启动时注册，技能触发时引擎通过 callback_id 查找执行。
    
    Example:
        def my_error_handler(skill_name, error, context):
            send_alert(f"Skill {skill_name} failed: {error}")
        
        register_hook_callback("error_handler_v1", my_error_handler)
    """
    _callbacks[callback_id] = fn
    logger.debug("[Hooks] Registered callback: %s", callback_id)


def unregister_hook_callback(callback_id: str) -> None:
    _callbacks.pop(callback_id, None)


def execute_hook(
    hooks_config: Optional[HooksConfig],
    event: HookEvent,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    执行技能钩子。
    
    Returns:
        钩子输出文本（如果有），否则 None。
    """
    if not hooks_config or not hooks_config.has_hook(event):
        return None

    hook = hooks_config.get_hook(event)
    if not hook:
        return None

    ctx = context or {}

    # 优先执行 callback
    if hook.callback_id and hook.callback_id in _callbacks:
        try:
            result = _callbacks[hook.callback_id](**ctx)
            logger.info(
                "[Hooks] Callback %s executed for %s",
                hook.callback_id,
                event.value,
            )
            return str(result) if result else None
        except Exception as e:
            logger.error(
                "[Hooks] Callback %s failed: %s", hook.callback_id, e,
            )
            return None

    # Shell command 执行由集成方负责（安全隔离）
    if hook.command:
        logger.info(
            "[Hooks] Shell hook for %s: %s (delegated to integrator)",
            event.value,
            hook.command[:80],
        )
        # 返回命令文本，由集成方决定是否执行
        return f"__HOOK_SHELL__:{hook.command}"

    return None


def clear_callbacks() -> None:
    """清除所有回调（测试用）"""
    _callbacks.clear()
