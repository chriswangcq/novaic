"""测试 subagent_id 在 think 和 tool 事件中的一致性"""

def test_react_actions_passes_subagent_id():
    """测试 react_actions saga 是否正确传递 subagent_id"""
    from task_queue.sagas.react_actions import _build_tool_execute_tasks
    
    ctx = {
        "runtime_id": "rt-test-123",
        "agent_id": "agent-test",
        "subagent_id": "subagent-test-456",  # 非默认值
        "round_num": 1,
        "tool_calls": [
            {
                "id": "call-1",
                "function": {"name": "test_tool", "arguments": "{}"},
            },
            {
                "id": "call-2",
                "function": {"name": "another_tool", "arguments": '{"key": "value"}'},
            },
        ],
    }
    
    tasks = _build_tool_execute_tasks(ctx)
    
    # 验证
    assert len(tasks) == 2, "应该生成2个任务"
    
    for i, task in enumerate(tasks):
        assert task["payload"]["runtime_id"] == "rt-test-123"
        assert task["payload"]["agent_id"] == "agent-test"
        assert task["payload"]["subagent_id"] == "subagent-test-456", \
            f"Task {i} 的 subagent_id 应该是 'subagent-test-456'"
        assert task["payload"]["round_id"] == "round-1"
    
    print("✅ 测试通过：subagent_id 正确传递到所有 tool.execute 任务")

def test_react_actions_uses_default_subagent_id():
    """测试 saga context 中没有 subagent_id 时使用默认值"""
    from task_queue.sagas.react_actions import _build_tool_execute_tasks
    
    ctx = {
        "runtime_id": "rt-test",
        "agent_id": "agent-test",
        # 故意不提供 subagent_id
        "tool_calls": [
            {"id": "call-1", "function": {"name": "test", "arguments": "{}"}},
        ],
    }
    
    tasks = _build_tool_execute_tasks(ctx)
    
    assert tasks[0]["payload"]["subagent_id"] == "main", \
        "没有提供 subagent_id 时应该使用默认值 'main'"
    
    print("✅ 测试通过：默认 subagent_id 为 'main'")

if __name__ == "__main__":
    test_react_actions_passes_subagent_id()
    test_react_actions_uses_default_subagent_id()
    print("\n🎉 所有测试通过！")
