"""
Compact Engine — Post-Compact Cleanup (压缩后清理)

借鉴 Claude Code postCompactCleanup.ts:
压缩完成后需要重置各种缓存和状态。
通过回调注册机制实现，不硬编码依赖。
"""

from __future__ import annotations

import logging
from typing import Callable, List, Optional

from .types import CompactResult, CompactStage

logger = logging.getLogger("compact_engine.cleanup")


# 已注册的清理回调
_cleanup_callbacks: List[Callable[[CompactResult], None]] = []


def register_cleanup(callback: Callable[[CompactResult], None]) -> Callable[[], None]:
    """
    注册压缩后清理回调。返回反注册函数。
    
    集成方在启动时注册需要在压缩后重置的组件。
    
    Example:
        # 注册
        unsubscribe = register_cleanup(lambda result: my_cache.clear())
        
        # 反注册
        unsubscribe()
    
    典型的清理操作:
    - 清除 prompt 缓存
    - 重置 skill 加载状态
    - 通知 UI 上下文已压缩
    - 更新 token 统计
    - 重置 cache break detection 基线
    """
    _cleanup_callbacks.append(callback)

    def unsubscribe():
        try:
            _cleanup_callbacks.remove(callback)
        except ValueError:
            pass

    return unsubscribe


def run_post_compact_cleanup(result: CompactResult) -> int:
    """
    执行所有注册的压缩后清理回调。
    
    返回成功执行的回调数量。
    每个回调独立执行，一个失败不影响其他。
    """
    success_count = 0

    for callback in _cleanup_callbacks:
        try:
            callback(result)
            success_count += 1
        except Exception as e:
            logger.error(
                "[Cleanup] Callback failed: %s (stage=%s, action=%s)",
                e,
                result.stage.value,
                result.action.value,
            )

    if success_count > 0:
        logger.info(
            "[Cleanup] Executed %d/%d callbacks after %s",
            success_count,
            len(_cleanup_callbacks),
            result.stage.value,
        )

    return success_count


def clear_cleanup_callbacks() -> None:
    """清除所有回调（测试用）"""
    _cleanup_callbacks.clear()
