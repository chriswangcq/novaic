"""
Task Handlers tests (HTTP-based).

v3 变更：
- 删除 subagent.wake 测试（用 get_or_create_runtime 替代）
"""

import pytest

from common.exceptions import ConfigurationError
from task_queue.handlers import get_all_topics, get_handler


def test_get_all_topics():
    topics = get_all_topics()
    assert len(topics) > 0
    # v3: subagent.wake 已删除
    assert "subagent.set_awake" in topics
    assert "runtime.create" in topics


def test_get_handler_not_found():
    with pytest.raises(ConfigurationError, match="No handler"):
        get_handler("nonexistent.topic")


# DELETED: test_execute_subagent_wake - v3 删除 awaking 状态
