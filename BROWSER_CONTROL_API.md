# 浏览器控制 API 文档

## 概述

浏览器控制 API 提供了通过 vmcontrol 服务在 VM 内控制浏览器的功能，替代了 VMUSE 的浏览器工具。

### 特性

- 🌐 **页面导航** - 打开任意 URL
- 🖱️ **元素交互** - 点击页面元素
- ⌨️ **文本输入** - 填写表单和输入框
- 📄 **内容获取** - 获取页面 HTML
- 📸 **截图** - 捕获页面视觉状态

### 技术栈

- **前端控制**: vmcontrol Rust 服务（通过 Guest Agent API）
- **浏览器自动化**: Playwright + Chromium（运行在 VM 内）
- **脚本桥接**: Python 辅助脚本（`playwright_helper.py`）

## 架构

```
┌─────────────────┐
│  Client (API)   │
└────────┬────────┘
         │ HTTP
         ↓
┌─────────────────┐
│   vmcontrol     │
│   (Rust)        │
└────────┬────────┘
         │ Guest Agent
         ↓
┌─────────────────┐
│   VM (Ubuntu)   │
│                 │
│  ┌───────────┐  │
│  │ Playwright│  │
│  │  Helper   │  │
│  └─────┬─────┘  │
│        │        │
│        ↓        │
│  ┌───────────┐  │
│  │ Chromium  │  │
│  │ Browser   │  │
│  └───────────┘  │
└─────────────────┘
```

## API 端点

### 1. 导航到 URL

**POST** `/api/vms/:id/browser/navigate`

在 VM 内的浏览器中打开指定 URL。

#### 请求

```json
{
  "url": "https://example.com"
}
```

#### 响应

```json
{
  "status": "success",
  "url": "https://example.com",
  "title": "Example Domain",
  "status_code": 200
}
```

#### 示例

```bash
curl -X POST http://localhost:9527/api/vms/1/browser/navigate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

---

### 2. 点击元素

**POST** `/api/vms/:id/browser/click`

点击页面上的指定元素。

#### 请求

```json
{
  "selector": "button#submit"
}
```

**selector**: CSS 选择器，支持：
- ID: `#submit`
- Class: `.button`
- Attribute: `[type="submit"]`
- Text: `text=Submit`
- 组合: `button.primary#submit`

#### 响应

```json
{
  "status": "success"
}
```

#### 错误响应

```json
{
  "status": "error",
  "error": "Element not found or not clickable: button#submit"
}
```

#### 示例

```bash
curl -X POST http://localhost:9527/api/vms/1/browser/click \
  -H "Content-Type: application/json" \
  -d '{"selector": "button#submit"}'
```

---

### 3. 输入文本

**POST** `/api/vms/:id/browser/type`

在指定输入框中输入文本（会先清空原有内容）。

#### 请求

```json
{
  "selector": "input#username",
  "text": "admin"
}
```

#### 响应

```json
{
  "status": "success"
}
```

#### 示例

```bash
curl -X POST http://localhost:9527/api/vms/1/browser/type \
  -H "Content-Type: application/json" \
  -d '{"selector": "input#username", "text": "admin"}'
```

---

### 4. 获取页面内容

**GET** `/api/vms/:id/browser/content`

获取当前页面的完整 HTML 内容。

#### 响应

```json
{
  "status": "success",
  "html": "<!DOCTYPE html>...",
  "url": "https://example.com",
  "title": "Example Domain"
}
```

#### 示例

```bash
curl -X GET http://localhost:9527/api/vms/1/browser/content
```

---

### 5. 页面截图

**POST** `/api/vms/:id/browser/screenshot`

捕获当前浏览器视口的截图。

#### 响应

```json
{
  "status": "success",
  "data": "89504e470d0a1a0a..."
}
```

**data**: PNG 图像的十六进制字符串

#### 示例

```bash
# 获取截图并保存为 PNG
curl -X POST http://localhost:9527/api/vms/1/browser/screenshot \
  | jq -r '.data' \
  | xxd -r -p > screenshot.png
```

---

## 部署

### 前置条件

1. ✅ VM 已创建并运行
2. ✅ Guest Agent 已安装并运行
3. ✅ VM 内已安装 Playwright 和 Chromium（通过 cloud-init）

### 部署步骤

#### 1. 部署 Playwright 辅助脚本

```bash
cd /Users/wangchaoqun/novaic/novaic-backend/scripts

# 部署到 VM
python3 deploy_playwright_helper.py <vm_id> [vmcontrol_url]

# 示例
python3 deploy_playwright_helper.py 1
python3 deploy_playwright_helper.py 1 http://localhost:9527
```

脚本会自动：
- 上传 `playwright_helper.py` 到 VM 的 `/opt/novaic/scripts/`
- 设置可执行权限
- 验证 Playwright 安装

#### 2. 验证部署

```bash
# 测试导航
curl -X POST http://localhost:9527/api/vms/1/browser/navigate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

---

## 完整测试

运行集成测试脚本：

```bash
cd /Users/wangchaoqun/novaic

# 设置环境变量（可选）
export VM_ID=1
export VMCONTROL_URL=http://localhost:9527

# 运行测试
./test_browser_api.sh
```

测试脚本会执行：
1. 导航到 example.com
2. 获取页面内容
3. 截图
4. 导航到 Google
5. 在搜索框输入文本
6. 点击搜索按钮
7. 最终截图

---

## Python 客户端示例

```python
import httpx
import base64
from pathlib import Path

class BrowserClient:
    def __init__(self, vmcontrol_url: str, vm_id: str):
        self.base_url = vmcontrol_url
        self.vm_id = vm_id
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
    
    async def navigate(self, url: str) -> dict:
        """导航到 URL"""
        response = await self.client.post(
            f"/api/vms/{self.vm_id}/browser/navigate",
            json={"url": url}
        )
        response.raise_for_status()
        return response.json()
    
    async def click(self, selector: str) -> dict:
        """点击元素"""
        response = await self.client.post(
            f"/api/vms/{self.vm_id}/browser/click",
            json={"selector": selector}
        )
        response.raise_for_status()
        return response.json()
    
    async def type_text(self, selector: str, text: str) -> dict:
        """输入文本"""
        response = await self.client.post(
            f"/api/vms/{self.vm_id}/browser/type",
            json={"selector": selector, "text": text}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_content(self) -> dict:
        """获取页面内容"""
        response = await self.client.get(
            f"/api/vms/{self.vm_id}/browser/content"
        )
        response.raise_for_status()
        return response.json()
    
    async def screenshot(self, output_path: str = None) -> bytes:
        """截图"""
        response = await self.client.post(
            f"/api/vms/{self.vm_id}/browser/screenshot"
        )
        response.raise_for_status()
        result = response.json()
        
        # 解码十六进制字符串
        screenshot_bytes = bytes.fromhex(result["data"])
        
        if output_path:
            Path(output_path).write_bytes(screenshot_bytes)
        
        return screenshot_bytes
    
    async def close(self):
        await self.client.aclose()

# 使用示例
async def main():
    browser = BrowserClient("http://localhost:9527", "1")
    
    try:
        # 导航
        await browser.navigate("https://example.com")
        
        # 获取内容
        content = await browser.get_content()
        print(f"Page title: {content['title']}")
        
        # 截图
        await browser.screenshot("screenshot.png")
        print("Screenshot saved!")
        
    finally:
        await browser.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 与 VMUSE 功能对比

| 功能 | VMUSE | 浏览器控制 API | 说明 |
|------|-------|----------------|------|
| 打开 URL | ✅ `open_url` | ✅ `navigate` | 功能等价 |
| 元素点击 | ✅ `click_element` | ✅ `click` | 功能等价 |
| 文本输入 | ✅ `type_text` | ✅ `type` | 功能等价 |
| 页面内容 | ✅ `get_content` | ✅ `content` | 功能等价 |
| 截图 | ✅ `screenshot` | ✅ `screenshot` | 输出格式: hex string |
| 等待元素 | ✅ | 🔄 待实现 | 可通过轮询模拟 |
| JavaScript 执行 | ✅ | 🔄 待实现 | 可扩展 |
| Cookie 管理 | ✅ | 🔄 待实现 | 可扩展 |

### 优势

1. **独立部署** - 不依赖 VMUSE，直接集成到 vmcontrol
2. **更快响应** - 通过 Guest Agent 直接通信，无需 MCP 协议开销
3. **更好控制** - Rust 实现，性能更好
4. **统一接口** - 与其他 vmcontrol API 一致

---

## 故障排查

### 1. Guest Agent 连接失败

**错误**: `Guest Agent not available`

**解决**:
```bash
# 检查 Guest Agent socket
ls -la /tmp/novaic/novaic-ga-*.sock

# 检查 VM 状态
curl http://localhost:9527/api/vms/1

# 重启 VM 内的 qemu-guest-agent
# （在 VM 内执行）
sudo systemctl restart qemu-guest-agent
```

### 2. Playwright 未安装

**错误**: `No module named 'playwright'`

**解决**:
```bash
# 在 VM 内执行
/opt/novaic-venv/bin/pip install playwright
/opt/novaic-venv/bin/playwright install chromium
/opt/novaic-venv/bin/playwright install-deps chromium
```

### 3. 元素未找到

**错误**: `Element not found or not clickable: <selector>`

**解决**:
1. 检查选择器是否正确
2. 确认页面已完全加载
3. 使用更宽松的选择器（如 `text=` 或 `[type=`）
4. 增加等待时间

### 4. 浏览器启动失败

**错误**: `Playwright error: Browser closed unexpectedly`

**解决**:
```bash
# 检查 VM 内 X11 显示
# （在 VM 内执行）
echo $DISPLAY
ps aux | grep X

# 重启 lightdm
sudo systemctl restart lightdm
```

---

## 扩展功能

### 添加新的浏览器命令

1. 在 `playwright_helper.py` 中添加新命令处理：

```python
elif command == "wait_for_element":
    selector = args.get("selector")
    timeout = args.get("timeout", 30000)
    
    try:
        page.wait_for_selector(selector, timeout=timeout)
        result = {"status": "success"}
    except PlaywrightTimeoutError:
        result = {"status": "error", "error": f"Element not found: {selector}"}
```

2. 在 `browser.rs` 中添加对应的路由处理器：

```rust
pub async fn wait_for_element(
    Path(vm_id): Path<String>,
    Json(req): Json<WaitRequest>,
) -> Result<Json<BrowserResponse>, (StatusCode, Json<ApiError>)> {
    let args = serde_json::json!({
        "selector": req.selector,
        "timeout": req.timeout
    });
    
    let result = execute_playwright_command(&vm_id, "wait_for_element", Some(args)).await?;
    Ok(Json(result))
}
```

3. 在 `routes/mod.rs` 中注册新路由：

```rust
.route("/api/vms/:id/browser/wait", post(browser::wait_for_element))
```

---

## 安全考虑

1. **URL 验证** - 考虑添加允许/阻止列表
2. **超时保护** - 默认 30 秒超时，防止无限等待
3. **资源限制** - 浏览器进程资源限制
4. **权限控制** - VM 内运行在 ubuntu 用户权限

---

## 性能优化

1. **浏览器复用** - 当前每次调用都启动新浏览器，可考虑复用
2. **并发控制** - 限制同时运行的浏览器实例数
3. **缓存策略** - 缓存静态资源
4. **超时调优** - 根据实际网络情况调整超时

---

## 开发者指南

### 本地测试

1. 启动 vmcontrol 服务：
```bash
cd /Users/wangchaoqun/novaic/novaic-app/src-tauri/vmcontrol
cargo run
```

2. 确保 VM 正在运行

3. 部署脚本：
```bash
cd /Users/wangchaoqun/novaic/novaic-backend/scripts
python3 deploy_playwright_helper.py 1
```

4. 运行测试：
```bash
cd /Users/wangchaoqun/novaic
./test_browser_api.sh
```

### 调试

查看 vmcontrol 日志：
```bash
# vmcontrol 服务日志会输出到 stdout
tail -f /tmp/vmcontrol.log  # 如果配置了日志文件
```

查看 VM 内的浏览器日志：
```bash
# SSH 到 VM
ssh ubuntu@<vm-ip>

# 手动测试 playwright helper
/opt/novaic-venv/bin/python3 /opt/novaic/scripts/playwright_helper.py navigate '{"url":"https://example.com"}'
```

---

## 总结

浏览器控制 API 提供了完整的浏览器自动化能力，可以替代 VMUSE 的浏览器工具。通过 Playwright 和 Guest Agent 的组合，实现了高性能、可靠的浏览器控制功能。

**核心优势**：
- ✅ 完全集成到 vmcontrol
- ✅ 独立于 VMUSE
- ✅ 高性能 Rust 实现
- ✅ 简单易用的 REST API
- ✅ 完整的错误处理

**下一步**：
- [ ] 添加更多浏览器操作（等待、JavaScript 执行等）
- [ ] 浏览器进程池管理
- [ ] WebSocket 实时浏览器控制
- [ ] 浏览器状态持久化
