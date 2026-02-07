# Mouse aim_id 强制要求修复完成

## 概述
成功修复 `novaic-backend/gateway/clients/vmuse_adapter.py` 中的 `_mouse()` 方法，现在所有鼠标操作都强制要求使用 `aim_id`，符合原始 FastMCP VMUSE 的设计。

## 修改内容

### 1. 添加强制 aim_id 检查（第581-606行）
在 `aim` action 处理之后，添加了强制检查逻辑：

```python
# ========== 添加强制 aim_id 检查 ==========
# 所有 execute actions 必须使用 aim_id
actions_requiring_aim_id = ["click", "double", "right_click", "down", "move", "scroll"]

if action in actions_requiring_aim_id:
    # 检查是否提供了 aim_id
    if "aim_id" not in arguments:
        return {
            "success": False,
            "error": f"'{action}' requires aim_id. Use mouse(action='aim', x=..., y=...) first to get an aim_id."
        }
    
    # 从缓存获取 aim 数据
    aim_id = arguments["aim_id"]
    aim = self.aim_cache.get(aim_id)
    if not aim:
        return {
            "success": False,
            "error": f"Invalid or expired aim_id: '{aim_id}'. Please call mouse(action='aim', ...) again to get a new aim_id."
        }
    
    # 强制使用 aim 缓存中的坐标，覆盖任何直接提供的 x, y
    arguments["x"] = aim["x"]
    arguments["y"] = aim["y"]
    
    logger.info(f"[VmuseAdapter] Using aim_id '{aim_id}' at position ({aim['x']}, {aim['y']})")
```

**关键点：**
- 明确列出需要 `aim_id` 的操作
- 提供清晰友好的错误消息
- 强制覆盖任何直接提供的 x, y 坐标

### 2. 修改 double 操作（第632-648行）
移除了在当前位置双击的 fallback：

```python
elif action == "double":
    # 双击 - aim_id 已经设置了 x, y
    x = arguments.get("x")
    y = arguments.get("y")
    
    # 移动到位置并双击（不再支持在当前位置双击）
    await self._exec_guest_command(vm_id, f"xdotool mousemove {x} {y} click --repeat 2 --delay 100 1")
    
    return {
        "success": True,
        "result": {
            "message": f"Mouse double click executed successfully",
            "action": action,
            "x": x,
            "y": y
        }
    }
```

### 3. 修改 down 操作（第650-669行）
移除了在当前位置按下的 fallback：

```python
elif action == "down":
    # 按下鼠标（拖拽开始） - aim_id 已经设置了 x, y
    x = arguments.get("x")
    y = arguments.get("y")
    button = arguments.get("button", "left")
    button_num = {"left": 1, "right": 3, "middle": 2}.get(button, 1)
    
    # 移动到位置并按下（不再支持在当前位置按下）
    await self._exec_guest_command(vm_id, f"xdotool mousemove {x} {y} mousedown {button_num}")
    
    return {
        "success": True,
        "result": {
            "message": f"Mouse down executed successfully",
            "action": action,
            "x": x,
            "y": y,
            "button": button
        }
    }
```

### 4. 修改 scroll 操作（第687-708行）
添加了先移动到 aim 位置再滚动的逻辑：

```python
elif action == "scroll":
    # 滚动 - 转换参数格式
    direction = arguments.get("direction", "down")
    amount = arguments.get("amount", 1)
    
    # 获取 aim 位置
    x = arguments.get("x")
    y = arguments.get("y")
    
    # 先移动鼠标到 aim 位置，然后滚动
    if x is not None and y is not None:
        # 移动到位置
        move_result = await self._exec_guest_command(vm_id, f"xdotool mousemove {x} {y}")
        if move_result.get("exit_code") != 0:
            return {"success": False, "error": "Failed to move mouse before scrolling"}
    
    # 转换：direction + amount → delta
    # up = 正数, down = 负数
    if direction == "up":
        payload["delta"] = amount
    else:  # down
        payload["delta"] = -amount
```

### 5. 更新工具描述（第1573-1574行）
在 `list_tools_mcp_format()` 中更新了 mouse 工具的描述：

```python
{
    "name": "mouse",
    "description": "Control mouse in VM. IMPORTANT: All actions except 'aim' require aim_id. Workflow: 1) aim to get aim_id, 2) use aim_id for other actions.",
    "inputSchema": {
        # ... 保持现有的 schema ...
    }
}
```

## 验证结果

✅ **所有验证通过：**

1. ✓ 强制 aim_id 检查代码存在
2. ✓ 检查逻辑正确
3. ✓ aim_id 缺失时的错误消息清晰友好
4. ✓ aim_id 无效时的错误消息清晰友好
5. ✓ 坐标覆盖逻辑正确
6. ✓ double 已移除 fallback
7. ✓ down 已移除 fallback
8. ✓ scroll 添加了位置移动
9. ✓ 工具描述已更新
10. ✓ 旧的可选 aim_id 代码已移除
11. ✓ Python 语法检查通过

## 工作流程

现在正确的鼠标操作工作流程：

1. **先 aim**：使用 `mouse(action='aim', x=100, y=200)` 获取 `aim_id`
2. **后操作**：使用 `aim_id` 执行操作，例如 `mouse(action='click', aim_id='aim_xxxx')`

### 示例

```python
# 步骤 1: aim 获取位置
result = await adapter.call_tool("mouse", {
    "action": "aim",
    "x": 100,
    "y": 200
})
aim_id = result["aim_id"]

# 步骤 2: 使用 aim_id 点击
await adapter.call_tool("mouse", {
    "action": "click",
    "aim_id": aim_id
})

# 步骤 3: 使用 aim_id 滚动
await adapter.call_tool("mouse", {
    "action": "scroll",
    "aim_id": aim_id,
    "direction": "down",
    "amount": 3
})
```

## 不受影响的操作

- `aim`：不需要 `aim_id`（用于创建 `aim_id`）
- `up`：不需要 `aim_id`（释放鼠标按钮，不需要位置）

## 错误消息

### 缺少 aim_id
```
'click' requires aim_id. Use mouse(action='aim', x=..., y=...) first to get an aim_id.
```

### 无效的 aim_id
```
Invalid or expired aim_id: 'aim_xxxx'. Please call mouse(action='aim', ...) again to get a new aim_id.
```

## 文件修改

- 📝 `/Users/wangchaoqun/novaic/novaic-backend/gateway/clients/vmuse_adapter.py`

## 完成时间

2026-02-06
