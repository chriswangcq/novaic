# Browser 工具快速参考

## 新增的5个Browser工具

### 1. browser_scroll
**功能**: 滚动浏览器页面

**参数**:
```python
{
    "direction": "up" | "down" | "left" | "right",  # 必需
    "amount": 100  # 可选，默认100像素
}
```

**示例**:
```python
# 向下滚动200像素
await adapter.call_tool("browser_scroll", {
    "direction": "down",
    "amount": 200
}, vm_id="1")

# 向上滚动（使用默认100像素）
await adapter.call_tool("browser_scroll", {
    "direction": "up"
}, vm_id="1")
```

---

### 2. browser_eval
**功能**: 在浏览器中执行JavaScript代码

**参数**:
```python
{
    "script": "JavaScript代码"  # 必需
}
```

**示例**:
```python
# 点击按钮
await adapter.call_tool("browser_eval", {
    "script": "document.querySelector('.submit-btn').click()"
}, vm_id="1")

# 获取页面标题
await adapter.call_tool("browser_eval", {
    "script": "document.title"
}, vm_id="1")

# 修改DOM
await adapter.call_tool("browser_eval", {
    "script": "document.body.style.backgroundColor = 'lightblue'"
}, vm_id="1")
```

---

### 3. browser_get_tabs
**功能**: 获取所有打开的浏览器标签页列表

**参数**: 无

**返回**:
```python
{
    "success": True,
    "result": {
        "tabs": [
            {"index": 0, "title": "Tab 1", "url": "https://..."},
            {"index": 1, "title": "Tab 2", "url": "https://..."}
        ],
        "active_tab": 0
    }
}
```

**示例**:
```python
# 获取所有标签页
result = await adapter.call_tool("browser_get_tabs", {}, vm_id="1")
tabs = result["result"]["tabs"]
print(f"打开了 {len(tabs)} 个标签页")
```

---

### 4. browser_switch_tab
**功能**: 切换到指定的浏览器标签页

**参数**:
```python
{
    "tab_index": 0  # 必需，标签页索引（从0开始）
}
```

**示例**:
```python
# 切换到第二个标签页
await adapter.call_tool("browser_switch_tab", {
    "tab_index": 1
}, vm_id="1")

# 切换到第一个标签页
await adapter.call_tool("browser_switch_tab", {
    "tab_index": 0
}, vm_id="1")
```

---

### 5. browser_close_tab
**功能**: 关闭当前或指定的浏览器标签页

**参数**:
```python
{
    "tab_index": 0  # 可选，不指定则关闭当前标签页
}
```

**示例**:
```python
# 关闭当前标签页
await adapter.call_tool("browser_close_tab", {}, vm_id="1")

# 关闭第三个标签页
await adapter.call_tool("browser_close_tab", {
    "tab_index": 2
}, vm_id="1")
```

---

## 完整工作流示例

### 多标签页浏览
```python
# 1. 打开第一个网页
await adapter.call_tool("browser_navigate", {
    "url": "https://example.com"
}, vm_id="1")

# 2. 执行JS打开新标签页
await adapter.call_tool("browser_eval", {
    "script": "window.open('https://google.com', '_blank')"
}, vm_id="1")

# 3. 获取所有标签页
tabs_result = await adapter.call_tool("browser_get_tabs", {}, vm_id="1")
print(f"当前有 {len(tabs_result['result']['tabs'])} 个标签页")

# 4. 切换到新标签页
await adapter.call_tool("browser_switch_tab", {
    "tab_index": 1
}, vm_id="1")

# 5. 在新标签页中滚动
await adapter.call_tool("browser_scroll", {
    "direction": "down",
    "amount": 500
}, vm_id="1")

# 6. 关闭当前标签页
await adapter.call_tool("browser_close_tab", {}, vm_id="1")
```

### JavaScript自动化
```python
# 填写表单
await adapter.call_tool("browser_eval", {
    "script": """
        document.querySelector('#username').value = 'user123';
        document.querySelector('#password').value = 'pass123';
        document.querySelector('#login-form').submit();
    """
}, vm_id="1")

# 提取数据
result = await adapter.call_tool("browser_eval", {
    "script": """
        Array.from(document.querySelectorAll('.product')).map(el => ({
            name: el.querySelector('.name').textContent,
            price: el.querySelector('.price').textContent
        }))
    """
}, vm_id="1")

# 等待元素加载
await adapter.call_tool("browser_eval", {
    "script": """
        new Promise(resolve => {
            const interval = setInterval(() => {
                if (document.querySelector('.loaded')) {
                    clearInterval(interval);
                    resolve(true);
                }
            }, 100);
        })
    """
}, vm_id="1")
```

---

## 与现有工具组合

### browser_scroll + screenshot
```python
# 滚动并截图
await adapter.call_tool("browser_scroll", {
    "direction": "down",
    "amount": 300
}, vm_id="1")

screenshot = await adapter.call_tool("screenshot", {}, vm_id="1")
```

### browser_eval + browser_click
```python
# 使用JS查找元素，然后点击
result = await adapter.call_tool("browser_eval", {
    "script": "document.querySelector('.submit-btn').getBoundingClientRect()"
}, vm_id="1")

# 或直接用browser_click
await adapter.call_tool("browser_click", {
    "selector": ".submit-btn"
}, vm_id="1")
```

---

## 错误处理

### 参数验证错误
```python
# 缺少必需参数
result = await adapter.call_tool("browser_scroll", {}, vm_id="1")
# 返回: {"success": False, "error": "Missing required parameter: direction"}

# 无效的枚举值
result = await adapter.call_tool("browser_scroll", {
    "direction": "invalid"
}, vm_id="1")
# 返回: {"success": False, "error": "Invalid direction: invalid..."}

# 无效的tab_index
result = await adapter.call_tool("browser_switch_tab", {
    "tab_index": -1
}, vm_id="1")
# 返回: {"success": False, "error": "Invalid tab_index: -1..."}
```

### HTTP错误
```python
# vmcontrol服务未运行或网络错误
result = await adapter.call_tool("browser_scroll", {
    "direction": "down"
}, vm_id="1")
# 返回: {"success": False, "error": "HTTP error: Connection refused"}
```

---

## API端点映射

| 工具 | HTTP方法 | 端点 |
|------|---------|------|
| browser_scroll | POST | `/api/vms/{vm_id}/browser/scroll` |
| browser_eval | POST | `/api/vms/{vm_id}/browser/eval` |
| browser_get_tabs | GET | `/api/vms/{vm_id}/browser/tabs` |
| browser_switch_tab | POST | `/api/vms/{vm_id}/browser/tabs/switch` |
| browser_close_tab | POST | `/api/vms/{vm_id}/browser/tabs/close` |

---

## 注意事项

1. **tab_index从0开始**: 第一个标签页的索引是0，不是1
2. **JavaScript执行是异步的**: browser_eval可能需要等待Promise完成
3. **滚动amount单位是像素**: 不是百分比或屏幕高度
4. **关闭最后一个标签页**: 可能会关闭整个浏览器窗口
5. **vmcontrol依赖**: 需要vmcontrol服务运行并支持这些API

---

## 故障排查

### 工具调用失败
1. 检查vmcontrol服务是否运行
2. 验证VM是否在线
3. 确认浏览器是否已启动
4. 查看vmcontrol日志

### JavaScript执行失败
1. 检查脚本语法
2. 确认目标元素是否存在
3. 查看浏览器控制台错误
4. 使用try-catch包装脚本

### 标签页操作失败
1. 先调用browser_get_tabs确认标签页数量
2. 确保tab_index在有效范围内
3. 检查浏览器是否支持多标签页
4. 确认没有popup阻止程序

---

## 更多信息

- 完整实现文档: `BROWSER_TOOLS_IMPLEMENTATION_SUMMARY.md`
- vmuse_adapter源码: `novaic-backend/gateway/clients/vmuse_adapter.py`
- vmcontrol API文档: `novaic-backend/VMCONTROL_README.md`
