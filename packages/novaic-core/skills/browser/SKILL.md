---
name: novaic-browser
description: Browser automation using Playwright. Use for web operations like navigating pages, filling forms, clicking elements, and taking screenshots. More reliable than desktop tools for web tasks.
---

# Browser Automation

基于 Playwright 的浏览器自动化工具，适用于网页操作。

## 🌐 Browser vs Desktop

| 场景 | 推荐工具 |
|------|----------|
| 网页操作 | `browser_*` 系列（更可靠） |
| 本地应用（微信、VSCode等） | `screenshot` + `mouse` + `keyboard` |
| 需要看到页面 | `browser_screenshot` 或 `screenshot` |

## 可用工具

### browser_navigate

导航到指定 URL。

```python
# 基本导航
browser_navigate(url="https://google.com")

# 等待策略
browser_navigate(url="https://example.com", wait_until="networkidle")
# wait_until: "load" | "domcontentloaded" | "networkidle"
```

### browser_click

点击页面元素，使用选择器定位。

```python
# 文本选择器
browser_click(selector="text=登录")

# CSS 选择器
browser_click(selector="#submit-btn")
browser_click(selector=".login-button")

# 属性选择器
browser_click(selector="[name='submit']")

# 角色选择器
browser_click(selector="role=button[name='Submit']")

# 超时设置（毫秒）
browser_click(selector="text=确认", timeout=10000)
```

### browser_type

在输入框中输入文本。

```python
# 输入并清空原有内容（默认）
browser_type(selector="input[name='username']", text="admin")

# 追加输入，不清空
browser_type(selector="#search", text="query", clear=False)
```

### browser_screenshot

截取浏览器页面。

```python
# 截取可见区域
browser_screenshot()

# 截取整页（包括滚动区域）
browser_screenshot(full_page=True)
```

### browser_scroll

滚动页面。

```python
# 向下滚动
browser_scroll(direction="down")

# 指定滚动量（像素）
browser_scroll(direction="down", amount=500)

# 在特定元素内滚动
browser_scroll(direction="down", selector=".scroll-container")
```

### browser_eval

执行 JavaScript 代码。

```python
# 获取页面标题
browser_eval(script="document.title")

# 获取元素文本
browser_eval(script="document.querySelector('h1').innerText")

# 执行复杂操作
browser_eval(script="window.scrollTo(0, document.body.scrollHeight)")
```

### 标签页管理

```python
# 获取所有标签页
browser_get_tabs()

# 切换到指定标签页（0-based 索引）
browser_switch_tab(index=1)

# 关闭当前标签页
browser_close_tab()

# 关闭指定标签页
browser_close_tab(index=2)
```

## 最佳实践

1. **优先用选择器**：`browser_click(selector="text=登录")` 比坐标点击更可靠
2. **等待加载**：`browser_navigate(url, wait_until="networkidle")` 确保页面完全加载
3. **截图验证**：操作后使用 `browser_screenshot()` 确认结果
4. **错误处理**：设置合适的 timeout，处理元素未找到的情况

## 常见工作流

### 登录网站

```python
browser_navigate(url="https://example.com/login", wait_until="networkidle")
browser_type(selector="input[name='username']", text="admin")
browser_type(selector="input[name='password']", text="password123")
browser_click(selector="text=登录")
browser_screenshot()  # 验证登录结果
```

### 搜索操作

```python
browser_navigate(url="https://google.com")
browser_type(selector="textarea[name='q']", text="search query")
browser_click(selector="text=Google 搜索")
browser_screenshot()  # 查看搜索结果
```
