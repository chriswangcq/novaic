# 浏览器控制 API 快速参考

## 快速开始

### 1. 部署脚本

```bash
cd novaic-backend/scripts
python3 deploy_playwright_helper.py 1
```

### 2. 测试连接

```bash
curl http://localhost:9527/api/vms/1/browser/navigate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

---

## API 端点速查

### 导航

```bash
POST /api/vms/:id/browser/navigate
{"url": "https://example.com"}
```

### 点击

```bash
POST /api/vms/:id/browser/click
{"selector": "button#submit"}
```

### 输入文本

```bash
POST /api/vms/:id/browser/type
{"selector": "input#username", "text": "admin"}
```

### 获取内容

```bash
GET /api/vms/:id/browser/content
```

### 截图

```bash
POST /api/vms/:id/browser/screenshot
```

---

## 选择器示例

| 类型 | 示例 | 说明 |
|------|------|------|
| ID | `#submit` | 匹配 id="submit" |
| Class | `.button` | 匹配 class="button" |
| 标签 | `button` | 匹配所有 button |
| 属性 | `[type="submit"]` | 匹配 type="submit" |
| 文本 | `text=Login` | 匹配文本为 "Login" |
| 组合 | `button.primary#submit` | 组合多个条件 |

---

## 常用操作

### 打开页面并截图

```bash
# 1. 导航
curl -X POST http://localhost:9527/api/vms/1/browser/navigate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# 2. 截图
curl -X POST http://localhost:9527/api/vms/1/browser/screenshot \
  | jq -r '.data' | xxd -r -p > screenshot.png
```

### 填写表单并提交

```bash
# 1. 打开页面
curl -X POST http://localhost:9527/api/vms/1/browser/navigate \
  -d '{"url": "https://example.com/login"}'

# 2. 输入用户名
curl -X POST http://localhost:9527/api/vms/1/browser/type \
  -d '{"selector": "input#username", "text": "admin"}'

# 3. 输入密码
curl -X POST http://localhost:9527/api/vms/1/browser/type \
  -d '{"selector": "input#password", "text": "password123"}'

# 4. 点击登录
curl -X POST http://localhost:9527/api/vms/1/browser/click \
  -d '{"selector": "button[type=submit]"}'
```

### 搜索并获取结果

```bash
# 1. 打开 Google
curl -X POST http://localhost:9527/api/vms/1/browser/navigate \
  -d '{"url": "https://www.google.com"}'

# 2. 输入搜索词
curl -X POST http://localhost:9527/api/vms/1/browser/type \
  -d '{"selector": "textarea[name=q]", "text": "Playwright"}'

# 3. 点击搜索
curl -X POST http://localhost:9527/api/vms/1/browser/click \
  -d '{"selector": "input[name=btnK]"}'

# 4. 获取页面内容
curl -X GET http://localhost:9527/api/vms/1/browser/content \
  | jq -r '.html' > results.html
```

---

## Python 快速示例

```python
import httpx
import asyncio

async def quick_test():
    async with httpx.AsyncClient() as client:
        # 导航
        r = await client.post(
            "http://localhost:9527/api/vms/1/browser/navigate",
            json={"url": "https://example.com"}
        )
        print(r.json())
        
        # 截图
        r = await client.post(
            "http://localhost:9527/api/vms/1/browser/screenshot"
        )
        screenshot = bytes.fromhex(r.json()["data"])
        open("screenshot.png", "wb").write(screenshot)
        print("Screenshot saved!")

asyncio.run(quick_test())
```

---

## 故障排查速查

### Guest Agent 不可用

```bash
# 检查 socket
ls -la /tmp/novaic/novaic-ga-*.sock

# 检查 VM 状态
curl http://localhost:9527/api/vms/1
```

### Playwright 未安装

```bash
# SSH 到 VM
ssh ubuntu@<vm-ip>

# 安装 Playwright
/opt/novaic-venv/bin/pip install playwright
/opt/novaic-venv/bin/playwright install chromium
```

### 测试脚本

```bash
# 在 VM 内手动测试
/opt/novaic-venv/bin/python3 /opt/novaic/scripts/playwright_helper.py \
  navigate '{"url":"https://example.com"}'
```

---

## 环境变量

```bash
# vmcontrol URL
export VMCONTROL_URL=http://localhost:9527

# VM ID
export VM_ID=1

# 使用
curl -X POST $VMCONTROL_URL/api/vms/$VM_ID/browser/navigate \
  -d '{"url": "https://example.com"}'
```

---

## 运行完整测试

```bash
cd /Users/wangchaoqun/novaic
./test_browser_api.sh
```

---

## 文件位置

| 文件 | 位置 |
|------|------|
| 浏览器路由 | `novaic-app/src-tauri/vmcontrol/src/api/routes/browser.rs` |
| Playwright 脚本 | `novaic-backend/scripts/playwright_helper.py` |
| 部署脚本 | `novaic-backend/scripts/deploy_playwright_helper.py` |
| 测试脚本 | `test_browser_api.sh` |
| 完整文档 | `BROWSER_CONTROL_API.md` |
| 实现总结 | `BROWSER_CONTROL_IMPLEMENTATION.md` |

---

## 常用 curl 命令模板

```bash
# 设置 base URL
BASE="http://localhost:9527/api/vms/1/browser"

# 导航
curl -X POST $BASE/navigate -H "Content-Type: application/json" -d '{"url":"URL"}'

# 点击
curl -X POST $BASE/click -H "Content-Type: application/json" -d '{"selector":"SELECTOR"}'

# 输入
curl -X POST $BASE/type -H "Content-Type: application/json" -d '{"selector":"SELECTOR","text":"TEXT"}'

# 内容
curl -X GET $BASE/content

# 截图
curl -X POST $BASE/screenshot | jq -r '.data' | xxd -r -p > screenshot.png
```

---

## jq 常用过滤

```bash
# 提取 URL
curl ... | jq -r '.url'

# 提取标题
curl ... | jq -r '.title'

# 提取状态
curl ... | jq -r '.status'

# 提取 HTML（前 100 行）
curl ... | jq -r '.html' | head -100

# 美化输出
curl ... | jq '.'
```

---

## 响应状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 503 | Guest Agent 不可用 |
| 500 | 内部错误 |

---

## 性能提示

1. **并行请求** - 可以同时向多个 VM 发送请求
2. **超时控制** - 默认 30 秒，确保网络稳定
3. **截图大小** - 视口大小 1280x720
4. **浏览器启动** - 每次操作约需 2-3 秒启动浏览器

---

## 下一步

- 📖 完整文档: `BROWSER_CONTROL_API.md`
- 🛠️ 实现详情: `BROWSER_CONTROL_IMPLEMENTATION.md`
- 🧪 运行测试: `./test_browser_api.sh`
- 🚀 开始使用: 部署脚本并调用 API

---

**最后更新**: 2026-02-06
