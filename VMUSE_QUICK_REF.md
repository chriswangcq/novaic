# VMUSE 快速参考

## 🚀 快速开始

### 1. 部署到现有 VM

```bash
# SSH 到 VM
ssh ubuntu@<vm-ip>

# 1. 安装依赖
sudo /opt/novaic/venv/bin/pip install aiohttp

# 2. 上传文件 (在宿主机执行)
cd novaic-backend/scripts
scp -r vmuse_complete_server.py vmuse_tools/ ubuntu@<vm-ip>:/opt/novaic/scripts/

# 3. 创建 systemd 服务 (在 VM 中)
sudo nano /etc/systemd/system/vmuse-server.service
```

**systemd 服务配置**:
```ini
[Unit]
Description=NovAIC VMUSE Complete Server
After=network.target lightdm.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/novaic/scripts
Environment="XAUTHORITY=/home/ubuntu/.Xauthority"
Environment="DISPLAY=:0"
Environment="PLAYWRIGHT_BROWSERS_PATH=/opt/novaic/.cache"
Environment="HOME=/home/ubuntu"
ExecStart=/opt/novaic/venv/bin/python3 /opt/novaic/scripts/vmuse_complete_server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# 4. 启动服务
sudo systemctl daemon-reload
sudo systemctl enable vmuse-server
sudo systemctl start vmuse-server

# 5. 检查状态
sudo systemctl status vmuse-server
journalctl -u vmuse-server -f

# 6. 测试
curl http://localhost:8080/health
```

### 2. 从宿主机测试

```bash
# 重启 vmcontrol (如果需要)
sudo systemctl restart vmcontrol

# 测试浏览器导航
curl -X POST http://localhost:18888/api/vms/<agent-id>/vmuse/browser/navigate \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com"}'

# 测试截图
curl -X POST http://localhost:18888/api/vms/<agent-id>/vmuse/desktop/screenshot \
  -H 'Content-Type: application/json' \
  -d '{}'
```

## 🔧 工具映射表

| 工具名 | Tool | Operation | VM API 路径 |
|--------|------|-----------|------------|
| browser_navigate | browser | navigate | /api/browser/navigate |
| browser_click | browser | click | /api/browser/click |
| browser_type | browser | type | /api/browser/type |
| browser_screenshot | browser | screenshot | /api/browser/screenshot |
| browser_scroll | browser | scroll | /api/browser/scroll |
| browser_evaluate | browser | evaluate | /api/browser/evaluate |
| screenshot | desktop | screenshot | /api/desktop/screenshot |
| mouse | desktop | mouse | /api/desktop/mouse |
| keyboard | desktop | keyboard | /api/desktop/keyboard |
| shell_exec | shell | command | /api/shell/command |
| file_read | file | read | /api/file/read |
| file_write | file | write | /api/file/write |
| file_list | file | list | /api/file/list |

## 🐛 故障排查

### VM 内服务器无响应

```bash
# 检查服务状态
sudo systemctl status vmuse-server

# 查看日志
journalctl -u vmuse-server -n 100

# 检查端口
ss -tlnp | grep 8080

# 手动测试
curl http://localhost:8080/health
```

### vmcontrol 无法连接 VM

```bash
# 检查 vmcontrol 状态
sudo systemctl status vmcontrol

# 查看日志
journalctl -u vmcontrol -f

# 检查 Guest Agent socket
ls -la /tmp/novaic/novaic-ga-*.sock

# 重启 vmcontrol
sudo systemctl restart vmcontrol
```

### 浏览器工具失败

```bash
# 在 VM 中检查 Playwright
/opt/novaic/venv/bin/playwright --version

# 检查 Chromium
/opt/novaic/venv/bin/playwright install chromium

# 检查环境变量
echo $DISPLAY
echo $XAUTHORITY

# 手动测试 Playwright
/opt/novaic/venv/bin/python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto('https://example.com')
    print(page.title())
    browser.close()
"
```

### 权限问题

```bash
# 检查文件所有权
ls -la /opt/novaic/scripts/

# 修复权限
sudo chown -R ubuntu:ubuntu /opt/novaic/

# 检查 .Xauthority
ls -la /home/ubuntu/.Xauthority
xauth list
```

## 📋 常用命令

```bash
# 重启 VM 服务器
sudo systemctl restart vmuse-server

# 查看实时日志
journalctl -u vmuse-server -f

# 停止服务
sudo systemctl stop vmuse-server

# 禁用自动启动
sudo systemctl disable vmuse-server

# 手动运行 (调试)
cd /opt/novaic/scripts
/opt/novaic/venv/bin/python3 vmuse_complete_server.py

# 测试健康检查
curl http://localhost:8080/health

# 测试浏览器
curl -X POST http://localhost:8080/api/browser/navigate \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com"}'

# 测试 Shell
curl -X POST http://localhost:8080/api/shell/command \
  -H 'Content-Type: application/json' \
  -d '{"command":"ls -la /home/ubuntu"}'
```

## 🔗 API 端点

### Browser

```bash
POST /api/browser/navigate
{"url": "https://example.com"}

POST /api/browser/click
{"selector": "button.submit"}

POST /api/browser/type
{"selector": "input[name='username']", "text": "hello"}

POST /api/browser/screenshot
{}

POST /api/browser/scroll
{"direction": "down", "amount": 500}

POST /api/browser/evaluate
{"script": "document.title"}
```

### Desktop

```bash
POST /api/desktop/screenshot
{"grid": true}

POST /api/desktop/mouse
{"action": "aim", "x": 100, "y": 200, "zoom": 2.0}

POST /api/desktop/mouse
{"action": "click", "aim_id": "aim_abc123"}

POST /api/desktop/keyboard
{"action": "type", "text": "Hello World"}

POST /api/desktop/keyboard
{"action": "key", "keys": ["ctrl", "c"]}
```

### Shell

```bash
POST /api/shell/command
{"command": "ls -la /home/ubuntu"}
```

### File

```bash
POST /api/file/read
{"path": "/home/ubuntu/test.txt"}

POST /api/file/write
{"path": "/home/ubuntu/test.txt", "content": "Hello"}

POST /api/file/list
{"path": "/home/ubuntu"}
```

## 📊 响应格式

### 成功响应

```json
{
  "status": "success",
  "url": "https://example.com",      // browser 工具
  "data": "...",                      // 其他数据
  "screenshot": "base64..."           // 截图数据
}
```

### 错误响应

```json
{
  "status": "error",
  "error": "Error message"
}
```

## 🎯 环境变量

```bash
# VM 内
DISPLAY=:0
XAUTHORITY=/home/ubuntu/.Xauthority
PLAYWRIGHT_BROWSERS_PATH=/opt/novaic/.cache
HOME=/home/ubuntu

# Backend
VMCONTROL_URL=http://127.0.0.1:18888
GATEWAY_URL=http://127.0.0.1:19999
```

## 🔍 调试技巧

1. **查看 VM 服务器日志**:
   ```bash
   tail -f /tmp/vmuse_server.log
   journalctl -u vmuse-server -f
   ```

2. **测试 Guest Agent**:
   ```bash
   # 在宿主机
   socat - UNIX-CONNECT:/tmp/novaic/novaic-ga-<agent-id>.sock
   {"execute":"guest-ping"}
   ```

3. **手动测试工具**:
   ```bash
   # 在 VM 中
   cd /opt/novaic/scripts
   python3 -c "
   import asyncio
   from vmuse_tools.browser import get_browser_tools
   
   async def test():
       browser = get_browser_tools()
       result = await browser.navigate('https://example.com')
       print(result)
   
   asyncio.run(test())
   "
   ```

4. **检查网络**:
   ```bash
   # 在 VM 中
   netstat -tlnp | grep 8080
   ss -tlnp | grep 8080
   curl http://localhost:8080/health
   ```
