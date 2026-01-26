# NovAIC 技术设计文档

> **版本**: v1.1  
> **更新日期**: 2026-01-10  
> **状态**: 设计中

---

## 目录

1. [系统总览](#1-系统总览)
2. [架构设计](#2-架构设计)
3. [虚拟机 Agent 设计](#3-虚拟机-agent-设计)
4. [Open Interpreter 集成](#4-open-interpreter-集成)
5. [可视化执行设计](#5-可视化执行设计) ⭐ 新增
6. [云服务设计](#6-云服务设计)
7. [Tauri 桌面应用设计](#7-tauri-桌面应用设计)
8. [通信协议](#8-通信协议)
9. [数据库设计](#9-数据库设计)
10. [安全设计](#10-安全设计)
11. [部署方案](#11-部署方案)

---

## 1. 系统总览

### 1.1 系统组成

NovAIC 由三大核心模块组成：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NovAIC 系统架构                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ☁️ 云服务层                                                                │
│  ├── 用户认证服务                                                           │
│  ├── 订阅管理服务                                                           │
│  └── LLM API 代理服务                                                       │
│                                                                             │
│  💻 桌面应用层 (Tauri)                                                       │
│  ├── React 前端 UI                                                          │
│  ├── Rust 后端核心                                                          │
│  └── 虚拟机管理器                                                           │
│                                                                             │
│  🖥️ 虚拟机层                                                                │
│  ├── Agent 服务 (基于 Open Interpreter)                                     │
│  ├── Linux 桌面环境                                                         │
│  └── VNC Server                                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈总览

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| **云服务** | Python + FastAPI + PostgreSQL | 轻量、快速开发 |
| **桌面应用** | Tauri + React + TypeScript | 跨平台、轻量 |
| **虚拟化** | QEMU / Virtualization.framework | 成熟稳定 |
| **Agent** | Python + Open Interpreter | 复用成熟方案 |
| **VNC** | TigerVNC + noVNC | 开源、易集成 |
| **LLM** | Claude API (Anthropic) | 编码能力强 |

---

## 2. 架构设计

### 2.1 完整架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ☁️ NovAIC 云服务                                │
│                         https://api.novaic.com                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                           API Gateway                                 │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │    Auth     │  │ Subscription│  │  LLM Proxy  │  │   Usage     │  │  │
│  │  │   Service   │  │   Service   │  │   Service   │  │   Service   │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        PostgreSQL Database                            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ▲
                                      │ HTTPS (JWT Auth)
                                      │
┌─────────────────────────────────────────────────────────────────────────────┐
│  用户设备 (macOS)                                                           │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  NovAIC.app (Tauri)                                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  前端 (React + TypeScript)                                      │  │  │
│  │  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │  │  │
│  │  │  │   Chat UI     │  │   VNC View    │  │   File Manager    │   │  │  │
│  │  │  │   (对话界面)   │  │   (noVNC)     │  │   (文件管理)       │   │  │  │
│  │  │  └───────────────┘  └───────────────┘  └───────────────────┘   │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  后端 (Rust)                                                    │  │  │
│  │  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │  │  │
│  │  │  │  VM Manager   │  │ File Transfer │  │  Local Storage    │   │  │  │
│  │  │  │  (虚拟机管理)  │  │  (文件传输)    │  │  (本地存储)        │   │  │  │
│  │  │  └───────────────┘  └───────────────┘  └───────────────────┘   │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                         │                    │                              │
│            HTTP :8080   │       VNC :5900    │                              │
│                         ▼                    ▼                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  虚拟机 (QEMU)                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  NovAIC Agent (Python + FastAPI)                                 │  │  │
│  │  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │  │  │
│  │  │  │  HTTP Server  │  │  OI Core      │  │  Tool Executor    │   │  │  │
│  │  │  │  (API 服务)    │  │ (Open Interp) │  │  (工具执行器)      │   │  │  │
│  │  │  └───────────────┘  └───────────────┘  └───────────────────┘   │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  Linux 环境 (Ubuntu + XFCE)                                     │  │  │
│  │  │  ├── Python 3.11 + pip                                          │  │  │
│  │  │  ├── Node.js 20 + npm                                           │  │  │
│  │  │  ├── Firefox / Chromium                                         │  │  │
│  │  │  ├── VS Code                                                    │  │  │
│  │  │  └── TigerVNC Server (:5900)                                    │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
用户输入: "帮我用 Python 分析 sales.xlsx"
                │
                ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 1: 前端处理                                                 │
│ ├── 用户在 Chat UI 输入消息                                      │
│ ├── 上传文件到虚拟机 (通过 File Transfer)                        │
│ └── 调用 Agent API: POST /api/chat                              │
└──────────────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 2: Agent 处理                                               │
│ ├── 接收消息 + 构造 Claude 请求                                  │
│ ├── 调用云服务 LLM Proxy: POST /api/llm/chat                    │
│ │   └── 云服务验证 Token → 检查配额 → 调用 Claude API           │
│ ├── 接收 Claude 响应 (Tool Use: run_python)                     │
│ ├── Open Interpreter 执行 Python 代码                           │
│ │   └── 用户通过 VNC 看到终端在运行                              │
│ ├── 如果需要继续，重复调用 Claude                                │
│ └── 返回最终结果                                                 │
└──────────────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 3: 前端展示                                                 │
│ ├── 显示 AI 回复                                                 │
│ ├── 提供文件下载按钮                                             │
│ └── VNC 画面实时显示执行过程                                     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. 虚拟机 Agent 设计

### 3.1 Agent 职责

| 职责 | 说明 |
|------|------|
| **接收指令** | 通过 HTTP API 接收来自 Tauri App 的用户指令 |
| **调用 LLM** | 通过云服务代理调用 Claude API |
| **执行工具** | 解析 Tool Use，执行代码/文件/浏览器操作 |
| **返回结果** | 将执行结果返回给前端 |
| **流式输出** | 支持 SSE 流式返回，提升用户体验 |

### 3.2 Agent 架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  NovAIC Agent                                                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  HTTP Layer (FastAPI)                                                 │  │
│  │  ├── POST /api/chat          # 对话接口                               │  │
│  │  ├── POST /api/chat/stream   # 流式对话接口                           │  │
│  │  ├── GET  /api/history       # 获取历史                               │  │
│  │  ├── POST /api/upload        # 上传文件                               │  │
│  │  ├── GET  /api/download      # 下载文件                               │  │
│  │  ├── POST /api/interrupt     # 中断执行                               │  │
│  │  └── GET  /api/health        # 健康检查                               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Agent Core                                                           │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │  │
│  │  │  Session        │  │  LLM Client     │  │  Tool Router        │   │  │
│  │  │  Manager        │  │  (Cloud Proxy)  │  │                     │   │  │
│  │  │  ├── 会话状态    │  │  ├── 认证       │  │  ├── run_command    │   │  │
│  │  │  ├── 消息历史    │  │  ├── 重试       │  │  ├── run_python     │   │  │
│  │  │  └── 上下文压缩  │  │  └── 流式处理   │  │  ├── read_file      │   │  │
│  │  └─────────────────┘  └─────────────────┘  │  ├── write_file     │   │  │
│  │                                            │  ├── list_files     │   │  │
│  │                                            │  ├── browser_action │   │  │
│  │                                            │  └── ...            │   │  │
│  │                                            └─────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Tool Executors                                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Shell     │  │   Python    │  │    File     │  │   Browser   │  │  │
│  │  │  Executor   │  │  Executor   │  │  Executor   │  │  Executor   │  │  │
│  │  │  (subprocess│  │  (exec/OI)  │  │  (os/shutil)│  │ (Playwright)│  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Agent 目录结构

```
/opt/novaic-agent/
├── main.py                 # 入口文件
├── config.py               # 配置
├── requirements.txt        # 依赖
│
├── api/                    # HTTP API 层
│   ├── __init__.py
│   ├── routes.py           # 路由定义
│   ├── schemas.py          # 请求/响应模型
│   └── middleware.py       # 中间件
│
├── core/                   # 核心逻辑
│   ├── __init__.py
│   ├── agent.py            # Agent 主循环
│   ├── session.py          # 会话管理
│   └── llm_client.py       # LLM 客户端
│
├── tools/                  # 工具执行器
│   ├── __init__.py
│   ├── base.py             # 工具基类
│   ├── shell.py            # Shell 执行器
│   ├── python.py           # Python 执行器
│   ├── file.py             # 文件操作
│   └── browser.py          # 浏览器控制
│
└── utils/                  # 工具函数
    ├── __init__.py
    └── helpers.py
```

---

## 4. Open Interpreter 集成

### 4.1 集成策略

我们采用**部分复用 + 自定义封装**的策略：

| 复用部分 | 自定义部分 |
|----------|------------|
| Tool 定义和执行逻辑 | HTTP API 层 |
| Python/Shell 执行器 | LLM 调用（通过云服务代理） |
| 代码安全检查 | 会话管理 |
| 流式输出处理 | 认证鉴权 |

### 4.2 Open Interpreter 核心使用

```python
# core/oi_integration.py

from interpreter import interpreter

class OpenInterpreterWrapper:
    """Open Interpreter 封装类"""
    
    def __init__(self):
        # 配置 Open Interpreter
        interpreter.llm.model = "claude-sonnet-4-20250514"
        interpreter.llm.api_base = None  # 我们自己处理 API 调用
        interpreter.auto_run = True       # 自动执行代码
        interpreter.verbose = True        # 详细输出
        
        # 禁用原生 LLM 调用，我们自己处理
        interpreter.llm.supports_functions = True
    
    def get_tools(self) -> list:
        """获取 Open Interpreter 的工具定义"""
        return [
            {
                "name": "run_code",
                "description": "Execute code in a specified programming language",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "description": "Programming language (python, javascript, shell, etc.)"
                        },
                        "code": {
                            "type": "string", 
                            "description": "Code to execute"
                        }
                    },
                    "required": ["language", "code"]
                }
            }
        ]
    
    def execute_code(self, language: str, code: str) -> dict:
        """执行代码"""
        try:
            # 使用 Open Interpreter 的代码执行能力
            result = interpreter.computer.run(language, code)
            return {
                "success": True,
                "output": result.get("output", ""),
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
```

### 4.3 自定义 Agent 实现

```python
# core/agent.py

import httpx
from typing import AsyncGenerator
from .oi_integration import OpenInterpreterWrapper
from .llm_client import LLMClient

class NBCCAgent:
    """NovAIC Agent 核心类"""
    
    def __init__(self, user_token: str, cloud_api_base: str):
        self.user_token = user_token
        self.llm_client = LLMClient(
            api_base=cloud_api_base,
            token=user_token
        )
        self.oi = OpenInterpreterWrapper()
        self.messages = []
        
        # 定义可用工具
        self.tools = [
            {
                "name": "run_command",
                "description": "Execute a shell command in the terminal",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to execute"
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "run_python",
                "description": "Execute Python code",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute"
                        }
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "read_file",
                "description": "Read the contents of a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Write content to a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write"
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "list_files",
                "description": "List files in a directory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "browser_open",
                "description": "Open a URL in the browser",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to open"
                        }
                    },
                    "required": ["url"]
                }
            }
        ]
    
    async def chat(self, user_message: str) -> AsyncGenerator[dict, None]:
        """
        处理用户消息，返回流式响应
        """
        # 添加用户消息
        self.messages.append({
            "role": "user",
            "content": user_message
        })
        
        while True:
            # 调用 LLM（通过云服务代理）
            response = await self.llm_client.chat(
                messages=self.messages,
                tools=self.tools,
                stream=True
            )
            
            # 收集完整响应
            full_response = await self._collect_stream(response)
            
            # 检查是否有工具调用
            if full_response.get("stop_reason") == "tool_use":
                # 执行工具
                tool_results = await self._execute_tools(full_response["tool_use"])
                
                # 添加 assistant 消息
                self.messages.append({
                    "role": "assistant",
                    "content": full_response["content"]
                })
                
                # 添加工具结果
                self.messages.append({
                    "role": "user",
                    "content": tool_results
                })
                
                # 通知前端工具执行结果
                yield {
                    "type": "tool_result",
                    "data": tool_results
                }
            else:
                # 完成，返回最终响应
                self.messages.append({
                    "role": "assistant", 
                    "content": full_response["content"]
                })
                
                yield {
                    "type": "final",
                    "data": full_response["content"]
                }
                break
    
    async def _execute_tools(self, tool_calls: list) -> list:
        """执行工具调用"""
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_input = tool_call["input"]
            
            # 通知前端正在执行
            print(f"[Agent] Executing tool: {tool_name}")
            
            # 执行对应的工具
            if tool_name == "run_command":
                result = await self._run_command(tool_input["command"])
            elif tool_name == "run_python":
                result = self.oi.execute_code("python", tool_input["code"])
            elif tool_name == "read_file":
                result = await self._read_file(tool_input["path"])
            elif tool_name == "write_file":
                result = await self._write_file(tool_input["path"], tool_input["content"])
            elif tool_name == "list_files":
                result = await self._list_files(tool_input["path"])
            elif tool_name == "browser_open":
                result = await self._browser_open(tool_input["url"])
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
            
            results.append({
                "type": "tool_result",
                "tool_use_id": tool_call.get("id"),
                "content": str(result)
            })
        
        return results
    
    async def _run_command(self, command: str) -> dict:
        """执行 shell 命令"""
        import asyncio
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        return {
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
            "return_code": process.returncode
        }
    
    async def _read_file(self, path: str) -> dict:
        """读取文件"""
        try:
            with open(path, 'r') as f:
                content = f.read()
            return {"content": content}
        except Exception as e:
            return {"error": str(e)}
    
    async def _write_file(self, path: str, content: str) -> dict:
        """写入文件"""
        try:
            with open(path, 'w') as f:
                f.write(content)
            return {"success": True, "path": path}
        except Exception as e:
            return {"error": str(e)}
    
    async def _list_files(self, path: str) -> dict:
        """列出目录"""
        import os
        try:
            files = os.listdir(path)
            return {"files": files}
        except Exception as e:
            return {"error": str(e)}
    
    async def _browser_open(self, url: str) -> dict:
        """打开浏览器"""
        import webbrowser
        try:
            webbrowser.open(url)
            return {"success": True, "url": url}
        except Exception as e:
            return {"error": str(e)}
```

### 4.4 LLM 客户端（云服务代理）

```python
# core/llm_client.py

import httpx
from typing import AsyncGenerator, Optional

class LLMClient:
    """LLM 客户端，通过云服务代理调用"""
    
    def __init__(self, api_base: str, token: str):
        self.api_base = api_base  # https://api.novaic.com
        self.token = token
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def chat(
        self,
        messages: list,
        tools: list,
        stream: bool = False
    ) -> AsyncGenerator[dict, None]:
        """
        调用 LLM API
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": messages,
            "tools": tools,
            "stream": stream,
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096
        }
        
        if stream:
            async with self.client.stream(
                "POST",
                f"{self.api_base}/api/llm/chat",
                headers=headers,
                json=payload
            ) as response:
                if response.status_code == 401:
                    raise Exception("认证失败，请重新登录")
                if response.status_code == 403:
                    raise Exception("订阅已过期或配额不足")
                if response.status_code != 200:
                    raise Exception(f"API 调用失败: {response.status_code}")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield {"type": "stream", "data": line[6:]}
        else:
            response = await self.client.post(
                f"{self.api_base}/api/llm/chat",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 401:
                raise Exception("认证失败，请重新登录")
            if response.status_code == 403:
                raise Exception("订阅已过期或配额不足")
            if response.status_code != 200:
                raise Exception(f"API 调用失败: {response.status_code}")
            
            yield response.json()
```

### 4.5 HTTP API 层

```python
# api/routes.py

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import json

from core.agent import NBCCAgent

app = FastAPI(title="NovAIC Agent API")

# 全局 Agent 实例
agent: Optional[NBCCAgent] = None

class InitRequest(BaseModel):
    user_token: str
    cloud_api_base: str = "https://api.novaic.com"

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    type: str  # "text", "tool_result", "final", "error"
    data: str

# ==================== API 端点 ====================

@app.post("/api/init")
async def init_agent(request: InitRequest):
    """初始化 Agent"""
    global agent
    agent = NBCCAgent(
        user_token=request.user_token,
        cloud_api_base=request.cloud_api_base
    )
    return {"status": "ok", "message": "Agent initialized"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """非流式对话"""
    if not agent:
        raise HTTPException(status_code=400, detail="Agent not initialized")
    
    results = []
    async for chunk in agent.chat(request.message):
        results.append(chunk)
    
    return {"results": results}

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式对话 (SSE)"""
    if not agent:
        raise HTTPException(status_code=400, detail="Agent not initialized")
    
    async def event_generator():
        try:
            async for chunk in agent.chat(request.message):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), path: str = "/home/user/uploads"):
    """上传文件到虚拟机"""
    import os
    
    os.makedirs(path, exist_ok=True)
    file_path = os.path.join(path, file.filename)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {"status": "ok", "path": file_path}

@app.get("/api/download")
async def download_file(path: str):
    """从虚拟机下载文件"""
    import os
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(path, filename=os.path.basename(path))

@app.get("/api/history")
async def get_history():
    """获取对话历史"""
    if not agent:
        raise HTTPException(status_code=400, detail="Agent not initialized")
    
    return {"messages": agent.messages}

@app.post("/api/clear")
async def clear_history():
    """清空对话历史"""
    if not agent:
        raise HTTPException(status_code=400, detail="Agent not initialized")
    
    agent.messages = []
    return {"status": "ok"}

@app.post("/api/interrupt")
async def interrupt():
    """中断当前执行"""
    # TODO: 实现中断逻辑
    return {"status": "ok"}

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "agent_initialized": agent is not None
    }
```

### 4.6 Agent 入口文件

```python
# main.py

import uvicorn
from api.routes import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
```

### 4.7 依赖文件

```txt
# requirements.txt

fastapi==0.109.0
uvicorn==0.27.0
httpx==0.26.0
pydantic==2.5.0
open-interpreter==0.2.0
python-multipart==0.0.6
playwright==1.41.0
```

---

## 5. 可视化执行设计

### 5.1 设计目标

**核心原则**：用户能「看到」AI 在做什么

| 问题 | 原方案 | 改进后 |
|------|--------|--------|
| 用户能看到代码执行吗？ | ❌ 后台运行，VNC 静止 | ✅ 终端窗口可见 |
| 用户能看到执行进度吗？ | ❌ 无反馈 | ✅ 实时日志面板 |
| 用户能看到浏览器操作吗？ | ✅ VNC 可见 | ✅ VNC 可见 |

### 5.2 双重可视化方案（A + B）

```
┌─────────────────────────────────────────────────────────────────────┐
│  方案 A: 可见终端执行                                                │
│  ├── 虚拟机启动时自动打开终端窗口                                    │
│  ├── Agent 所有命令通过 tmux 发送到可见终端                          │
│  └── 用户在 VNC 画面中看到命令执行                                   │
├─────────────────────────────────────────────────────────────────────┤
│  方案 B: 实时执行日志                                                │
│  ├── Agent 执行时通过 SSE 推送日志到前端                             │
│  ├── 前端显示：工具名称、执行状态、输出内容                          │
│  └── 作为 VNC 的补充，提供详细信息                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.3 可见终端实现

#### 5.3.1 虚拟机启动脚本

```bash
#!/bin/bash
# /opt/novaic-agent/start.sh

# 1. 启动 VNC Server
vncserver :0 -geometry 1280x800 -depth 24

# 2. 启动桌面环境
export DISPLAY=:0
startxfce4 &

# 3. 等待桌面启动
sleep 3

# 4. 启动 tmux 会话（Agent 命令的执行目标）
tmux new-session -d -s agent -x 120 -y 30

# 5. 打开一个始终可见的终端窗口，连接到 tmux
xfce4-terminal --maximize --title="Agent Terminal" \
  --command="tmux attach-session -t agent" &

# 6. 启动 Agent 服务
cd /opt/novaic-agent
python main.py &

echo "NovAIC Agent started"
```

#### 5.3.2 Agent 命令执行（可见终端版）

```python
# tools/visible_executor.py

import asyncio
import subprocess
from typing import AsyncGenerator

class VisibleExecutor:
    """在可见终端中执行命令"""
    
    TMUX_SESSION = "agent"
    
    async def run_in_visible_terminal(
        self, 
        command: str,
        capture_output: bool = True
    ) -> AsyncGenerator[dict, None]:
        """
        在可见终端中执行命令
        用户可以在 VNC 中看到执行过程
        """
        
        # 1. 通过 tmux 发送命令到可见终端
        tmux_cmd = f"tmux send-keys -t {self.TMUX_SESSION} '{command}' Enter"
        subprocess.run(tmux_cmd, shell=True)
        
        yield {"type": "status", "data": "命令已发送到终端"}
        
        # 2. 同时捕获输出用于返回和日志
        if capture_output:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 实时读取并推送输出
            async for line in self._read_stream(process.stdout):
                yield {"type": "stdout", "data": line}
            
            async for line in self._read_stream(process.stderr):
                yield {"type": "stderr", "data": line}
            
            await process.wait()
            yield {
                "type": "complete", 
                "data": {"return_code": process.returncode}
            }
    
    async def _read_stream(self, stream) -> AsyncGenerator[str, None]:
        """异步读取流"""
        while True:
            line = await stream.readline()
            if not line:
                break
            yield line.decode().rstrip()
    
    async def run_python_visible(self, code: str) -> AsyncGenerator[dict, None]:
        """在可见终端中执行 Python 代码"""
        
        # 将代码写入临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.py', 
            delete=False
        ) as f:
            f.write(code)
            script_path = f.name
        
        yield {"type": "status", "data": f"执行 Python 脚本: {script_path}"}
        
        # 在可见终端中执行
        async for event in self.run_in_visible_terminal(f"python {script_path}"):
            yield event
```

#### 5.3.3 更新 Agent 核心类

```python
# core/agent.py (更新版)

from tools.visible_executor import VisibleExecutor

class NBCCAgent:
    def __init__(self, user_token: str, cloud_api_base: str):
        # ... 原有初始化 ...
        self.visible_executor = VisibleExecutor()
    
    async def _run_command(self, command: str) -> AsyncGenerator[dict, None]:
        """在可见终端中执行命令"""
        async for event in self.visible_executor.run_in_visible_terminal(command):
            yield event
    
    async def _run_python(self, code: str) -> AsyncGenerator[dict, None]:
        """在可见终端中执行 Python"""
        async for event in self.visible_executor.run_python_visible(code):
            yield event
```

### 5.4 实时执行日志

#### 5.4.1 SSE 日志事件格式

```typescript
// 日志事件类型
interface LogEvent {
  type: 'tool_start' | 'status' | 'stdout' | 'stderr' | 'progress' | 'tool_end' | 'error';
  timestamp: string;
  data: {
    tool?: string;        // 工具名称
    message?: string;     // 状态消息
    output?: string;      // 输出内容
    progress?: number;    // 进度 0-100
    error?: string;       // 错误信息
  };
}

// 示例事件流
// data: {"type": "tool_start", "timestamp": "...", "data": {"tool": "run_python"}}
// data: {"type": "status", "timestamp": "...", "data": {"message": "加载文件..."}}
// data: {"type": "stdout", "timestamp": "...", "data": {"output": "Processing row 1000"}}
// data: {"type": "progress", "timestamp": "...", "data": {"progress": 50}}
// data: {"type": "tool_end", "timestamp": "...", "data": {"tool": "run_python"}}
```

#### 5.4.2 Agent SSE 推送实现

```python
# api/routes.py (更新版)

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from datetime import datetime
import json

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式对话，包含执行日志"""
    if not agent:
        raise HTTPException(status_code=400, detail="Agent not initialized")
    
    async def event_generator():
        try:
            async for event in agent.chat_with_logs(request.message):
                # 添加时间戳
                event["timestamp"] = datetime.now().isoformat()
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': {'error': str(e)}})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

```python
# core/agent.py (chat_with_logs 方法)

async def chat_with_logs(self, user_message: str) -> AsyncGenerator[dict, None]:
    """带日志的对话方法"""
    
    self.messages.append({"role": "user", "content": user_message})
    
    while True:
        # 调用 LLM
        response = await self.llm_client.chat(
            messages=self.messages,
            tools=self.tools
        )
        
        if response.get("stop_reason") == "tool_use":
            for tool_call in response["tool_use"]:
                tool_name = tool_call["name"]
                tool_input = tool_call["input"]
                
                # 发送工具开始事件
                yield {
                    "type": "tool_start",
                    "data": {"tool": tool_name, "input": tool_input}
                }
                
                # 执行工具并流式返回日志
                if tool_name == "run_command":
                    async for log in self._run_command(tool_input["command"]):
                        yield {"type": log["type"], "data": log["data"]}
                        
                elif tool_name == "run_python":
                    async for log in self._run_python(tool_input["code"]):
                        yield {"type": log["type"], "data": log["data"]}
                
                # 发送工具结束事件
                yield {
                    "type": "tool_end",
                    "data": {"tool": tool_name}
                }
            
            # 继续对话循环
            self.messages.append({"role": "assistant", "content": response["content"]})
            self.messages.append({"role": "user", "content": tool_results})
        else:
            # 完成
            yield {
                "type": "final",
                "data": {"content": response["content"]}
            }
            break
```

### 5.5 前端执行日志组件

```typescript
// src/components/ExecutionLog/ExecutionLog.tsx

import React, { useState, useEffect, useRef } from 'react';
import './ExecutionLog.css';

interface LogEntry {
  type: string;
  timestamp: string;
  data: any;
}

interface ExecutionLogProps {
  logs: LogEntry[];
  isExecuting: boolean;
}

export function ExecutionLog({ logs, isExecuting }: ExecutionLogProps) {
  const logEndRef = useRef<HTMLDivElement>(null);
  const [expanded, setExpanded] = useState(false);
  
  // 自动滚动到底部
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);
  
  const getLogIcon = (type: string) => {
    switch (type) {
      case 'tool_start': return '🚀';
      case 'tool_end': return '✅';
      case 'stdout': return '📝';
      case 'stderr': return '⚠️';
      case 'progress': return '📊';
      case 'error': return '❌';
      default: return '📋';
    }
  };
  
  const formatLog = (log: LogEntry) => {
    switch (log.type) {
      case 'tool_start':
        return `开始执行: ${log.data.tool}`;
      case 'tool_end':
        return `完成: ${log.data.tool}`;
      case 'stdout':
      case 'stderr':
        return log.data.output || log.data.message;
      case 'progress':
        return `进度: ${log.data.progress}%`;
      default:
        return log.data.message || JSON.stringify(log.data);
    }
  };
  
  return (
    <div className={`execution-log ${expanded ? 'expanded' : ''}`}>
      <div className="log-header">
        <span className="log-title">
          📋 执行日志
          {isExecuting && <span className="executing-badge">执行中...</span>}
        </span>
        <button onClick={() => setExpanded(!expanded)}>
          {expanded ? '收起' : '展开'}
        </button>
      </div>
      
      <div className="log-content">
        {logs.length === 0 ? (
          <div className="log-empty">暂无执行日志</div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className={`log-entry log-${log.type}`}>
              <span className="log-icon">{getLogIcon(log.type)}</span>
              <span className="log-time">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              <span className="log-message">{formatLog(log)}</span>
            </div>
          ))
        )}
        <div ref={logEndRef} />
      </div>
      
      {/* 进度条 */}
      {isExecuting && (
        <div className="log-progress">
          <div className="progress-bar" />
        </div>
      )}
    </div>
  );
}
```

```css
/* src/components/ExecutionLog/ExecutionLog.css */

.execution-log {
  background: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
  transition: height 0.3s ease;
}

.execution-log.expanded {
  height: 300px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #2d2d2d;
  border-bottom: 1px solid #3d3d3d;
}

.log-title {
  font-weight: 500;
  color: #e0e0e0;
}

.executing-badge {
  margin-left: 8px;
  padding: 2px 8px;
  background: #4caf50;
  border-radius: 4px;
  font-size: 12px;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.log-content {
  height: 150px;
  overflow-y: auto;
  padding: 8px;
  font-family: 'Fira Code', monospace;
  font-size: 12px;
}

.log-entry {
  display: flex;
  align-items: flex-start;
  padding: 4px 0;
  color: #b0b0b0;
}

.log-entry.log-tool_start { color: #64b5f6; }
.log-entry.log-tool_end { color: #81c784; }
.log-entry.log-stderr { color: #ef5350; }
.log-entry.log-error { color: #ef5350; }

.log-icon {
  margin-right: 8px;
}

.log-time {
  color: #666;
  margin-right: 8px;
  min-width: 70px;
}

.log-progress {
  height: 3px;
  background: #333;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #4caf50, #8bc34a);
  animation: progress 2s infinite;
}

@keyframes progress {
  0% { width: 0%; }
  100% { width: 100%; }
}
```

### 5.6 前端集成 Hook

```typescript
// src/hooks/useAgentWithLogs.ts

import { useState, useCallback, useRef } from 'react';

interface LogEntry {
  type: string;
  timestamp: string;
  data: any;
}

export function useAgentWithLogs() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  
  const sendMessage = useCallback(async (content: string) => {
    // 清空上次的日志
    setLogs([]);
    setIsExecuting(true);
    
    // 添加用户消息
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    }]);
    
    try {
      // 使用 SSE 接收流式响应
      const response = await fetch('http://localhost:8080/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content })
      });
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const text = decoder.decode(value);
        const lines = text.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const event = JSON.parse(line.slice(6));
            
            // 添加到日志
            setLogs(prev => [...prev, event]);
            
            // 处理最终响应
            if (event.type === 'final') {
              setMessages(prev => [...prev, {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: event.data.content,
                timestamp: new Date()
              }]);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error:', error);
      setLogs(prev => [...prev, {
        type: 'error',
        timestamp: new Date().toISOString(),
        data: { error: String(error) }
      }]);
    } finally {
      setIsExecuting(false);
    }
  }, []);
  
  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);
  
  return {
    messages,
    logs,
    isExecuting,
    sendMessage,
    clearLogs
  };
}
```

### 5.7 整体 UI 布局更新

```typescript
// src/App.tsx (更新版)

import React from 'react';
import { ChatView } from './components/Chat/ChatView';
import { VNCView } from './components/VNC/VNCView';
import { ExecutionLog } from './components/ExecutionLog/ExecutionLog';
import { useAgentWithLogs } from './hooks/useAgentWithLogs';

export function App() {
  const { messages, logs, isExecuting, sendMessage, clearLogs } = useAgentWithLogs();
  
  return (
    <div className="app">
      <header className="app-header">
        <h1>NovAIC</h1>
        <div className="user-menu">...</div>
      </header>
      
      <main className="app-main">
        {/* 左侧：对话区 */}
        <div className="chat-panel">
          <ChatView 
            messages={messages} 
            onSendMessage={sendMessage}
            isLoading={isExecuting}
          />
        </div>
        
        {/* 右侧：可视化区 */}
        <div className="visual-panel">
          {/* 上半部分：VNC 画面 */}
          <div className="vnc-section">
            <VNCView host="localhost" port={5900} />
          </div>
          
          {/* 下半部分：执行日志 */}
          <div className="log-section">
            <ExecutionLog 
              logs={logs} 
              isExecuting={isExecuting}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
```

### 5.8 可视化效果预览

```
┌─────────────────────────────────────────────────────────────────────┐
│  用户发送: "帮我分析 sales.xlsx"                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  VNC 画面变化:                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Terminal - Agent                                              │  │
│  │ ─────────────────────────────────────────────────────────────│  │
│  │ $ python /tmp/script_123.py                                  │  │
│  │ Loading sales.xlsx...                                        │  │
│  │ Processing 5000 rows...                                      │  │
│  │ [████████████████████░░░░░░░░░░] 60%                         │  │
│  │ Generating chart...                                          │  │
│  │ ✓ Report saved to /home/user/report.pdf                      │  │
│  │ $                                                            │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  执行日志面板:                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 🚀 10:23:45 开始执行: run_python                              │  │
│  │ 📋 10:23:45 写入脚本到 /tmp/script_123.py                    │  │
│  │ 📝 10:23:46 Loading sales.xlsx...                            │  │
│  │ 📝 10:23:47 Processing 5000 rows...                          │  │
│  │ 📊 10:23:48 进度: 60%                                        │  │
│  │ 📝 10:23:50 Generating chart...                              │  │
│  │ ✅ 10:23:52 完成: run_python                                  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  用户体验: ✅ 能看到终端在跑  ✅ 能看到详细日志  ✅ 知道执行进度     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. 云服务设计

### 6.1 云服务架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  NovAIC Cloud Service                                                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  API Gateway (FastAPI)                                                │  │
│  │  ├── 路由分发                                                         │  │
│  │  ├── 认证中间件 (JWT)                                                 │  │
│  │  ├── 限流中间件                                                       │  │
│  │  └── 日志中间件                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│         ┌────────────────────────────┼────────────────────────────┐        │
│         ▼                            ▼                            ▼        │
│  ┌─────────────┐             ┌─────────────┐             ┌─────────────┐  │
│  │    Auth     │             │Subscription │             │  LLM Proxy  │  │
│  │   Service   │             │   Service   │             │   Service   │  │
│  │             │             │             │             │             │  │
│  │ ├── 注册    │             │ ├── 创建订阅│             │ ├── 验证配额│  │
│  │ ├── 登录    │             │ ├── 查询状态│             │ ├── 调用Claude│ │
│  │ ├── 刷新Token│            │ ├── 取消订阅│             │ ├── 记录用量│  │
│  │ └── 登出    │             │ └── 配额管理│             │ └── 流式转发│  │
│  └─────────────┘             └─────────────┘             └─────────────┘  │
│         │                            │                            │        │
│         └────────────────────────────┼────────────────────────────┘        │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL                                                           │  │
│  │  ├── users (用户表)                                                   │  │
│  │  ├── subscriptions (订阅表)                                           │  │
│  │  ├── usage_records (用量记录表)                                       │  │
│  │  └── api_keys (API Key 管理，内部)                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 云服务 API 定义

```yaml
# openapi.yaml

openapi: 3.0.0
info:
  title: NovAIC Cloud API
  version: 1.0.0

paths:
  # ========== 认证 ==========
  /api/auth/register:
    post:
      summary: 用户注册
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                password:
                  type: string
                name:
                  type: string
      responses:
        200:
          description: 注册成功
          
  /api/auth/login:
    post:
      summary: 用户登录
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                password:
                  type: string
      responses:
        200:
          description: 登录成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                  refresh_token:
                    type: string
                  expires_in:
                    type: integer
                    
  /api/auth/refresh:
    post:
      summary: 刷新 Token
      
  /api/auth/logout:
    post:
      summary: 登出
      
  # ========== 用户 ==========
  /api/user/profile:
    get:
      summary: 获取用户信息
      security:
        - bearerAuth: []
        
  /api/user/usage:
    get:
      summary: 获取用量统计
      security:
        - bearerAuth: []
        
  # ========== 订阅 ==========
  /api/subscription/plans:
    get:
      summary: 获取订阅套餐列表
      
  /api/subscription/create:
    post:
      summary: 创建订阅
      security:
        - bearerAuth: []
        
  /api/subscription/status:
    get:
      summary: 查询订阅状态
      security:
        - bearerAuth: []
        
  /api/subscription/cancel:
    post:
      summary: 取消订阅
      security:
        - bearerAuth: []
        
  # ========== LLM 代理 ==========
  /api/llm/chat:
    post:
      summary: LLM 对话（代理 Claude API）
      security:
        - bearerAuth: []
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                model:
                  type: string
                  default: claude-sonnet-4-20250514
                messages:
                  type: array
                tools:
                  type: array
                max_tokens:
                  type: integer
                stream:
                  type: boolean
      responses:
        200:
          description: 成功
        401:
          description: 未认证
        403:
          description: 订阅过期或配额不足
        429:
          description: 请求过于频繁

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

### 5.3 云服务核心代码

```python
# cloud_service/main.py

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import jwt
import httpx
from datetime import datetime, timedelta
from anthropic import Anthropic

app = FastAPI(title="NovAIC Cloud Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
SECRET_KEY = "your-secret-key-change-in-production"
CLAUDE_API_KEY = "your-claude-api-key"  # 用户看不到这个

# Anthropic 客户端
anthropic = Anthropic(api_key=CLAUDE_API_KEY)

# ==================== 模型 ====================

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class LLMChatRequest(BaseModel):
    model: str = "claude-sonnet-4-20250514"
    messages: list
    tools: Optional[list] = None
    max_tokens: int = 4096
    stream: bool = False

# ==================== 认证 ====================

async def get_current_user(authorization: str = None):
    """验证 JWT Token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证信息")
    
    token = authorization[7:]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token")

async def check_subscription(user_id: str):
    """检查订阅状态"""
    # TODO: 从数据库查询
    # 这里简化处理
    return {
        "plan": "pro",
        "quota": 100000,
        "used": 5000,
        "expires_at": datetime.now() + timedelta(days=30)
    }

# ==================== API 端点 ====================

@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    """用户注册"""
    # TODO: 保存到数据库
    # 这里简化处理
    return {"status": "ok", "message": "注册成功"}

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """用户登录"""
    # TODO: 验证密码，从数据库查询
    # 这里简化处理
    
    # 生成 JWT
    payload = {
        "user_id": "user_123",
        "email": request.email,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 7 * 24 * 3600
    }

@app.get("/api/user/profile")
async def get_profile(user = Depends(get_current_user)):
    """获取用户信息"""
    return {
        "user_id": user["user_id"],
        "email": user["email"]
    }

@app.get("/api/subscription/status")
async def get_subscription_status(user = Depends(get_current_user)):
    """获取订阅状态"""
    subscription = await check_subscription(user["user_id"])
    return subscription

@app.post("/api/llm/chat")
async def llm_chat(
    request: LLMChatRequest,
    user = Depends(get_current_user)
):
    """LLM 对话代理"""
    # 检查订阅
    subscription = await check_subscription(user["user_id"])
    
    if subscription["used"] >= subscription["quota"]:
        raise HTTPException(status_code=403, detail="配额已用完")
    
    # 调用 Claude API
    try:
        response = anthropic.messages.create(
            model=request.model,
            max_tokens=request.max_tokens,
            messages=request.messages,
            tools=request.tools or []
        )
        
        # 记录用量
        # TODO: 保存到数据库
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        print(f"[Usage] User {user['user_id']} used {tokens_used} tokens")
        
        # 转换响应格式
        return {
            "id": response.id,
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": block.type,
                    "text": block.text if hasattr(block, 'text') else None,
                    "id": block.id if hasattr(block, 'id') else None,
                    "name": block.name if hasattr(block, 'name') else None,
                    "input": block.input if hasattr(block, 'input') else None,
                }
                for block in response.content
            ],
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 7. Tauri 桌面应用设计

### 6.1 项目结构

```
novaic-app/
├── src/                        # React 前端
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatView.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   └── MessageBubble.tsx
│   │   ├── VNC/
│   │   │   ├── VNCView.tsx
│   │   │   └── VNCControls.tsx
│   │   ├── Files/
│   │   │   ├── FileUpload.tsx
│   │   │   └── FileList.tsx
│   │   └── Layout/
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── MainLayout.tsx
│   ├── hooks/
│   │   ├── useAgent.ts
│   │   ├── useVNC.ts
│   │   └── useAuth.ts
│   ├── services/
│   │   ├── agent.ts
│   │   ├── vm.ts
│   │   └── auth.ts
│   ├── store/
│   │   ├── index.ts
│   │   ├── chatSlice.ts
│   │   └── authSlice.ts
│   ├── App.tsx
│   └── main.tsx
│
├── src-tauri/                  # Rust 后端
│   ├── src/
│   │   ├── main.rs
│   │   ├── vm/
│   │   │   ├── mod.rs
│   │   │   ├── qemu.rs
│   │   │   └── manager.rs
│   │   ├── files/
│   │   │   ├── mod.rs
│   │   │   └── transfer.rs
│   │   └── commands/
│   │       ├── mod.rs
│   │       ├── vm_commands.rs
│   │       └── file_commands.rs
│   ├── Cargo.toml
│   └── tauri.conf.json
│
├── package.json
└── tsconfig.json
```

### 6.2 Tauri 命令定义

```rust
// src-tauri/src/commands/vm_commands.rs

use tauri::command;
use crate::vm::manager::VMManager;

#[command]
pub async fn start_vm() -> Result<String, String> {
    let manager = VMManager::new();
    manager.start().await.map_err(|e| e.to_string())?;
    Ok("VM started".to_string())
}

#[command]
pub async fn stop_vm() -> Result<String, String> {
    let manager = VMManager::new();
    manager.stop().await.map_err(|e| e.to_string())?;
    Ok("VM stopped".to_string())
}

#[command]
pub async fn get_vm_status() -> Result<String, String> {
    let manager = VMManager::new();
    let status = manager.status().await.map_err(|e| e.to_string())?;
    Ok(status)
}

#[command]
pub async fn init_agent(token: String) -> Result<String, String> {
    // 调用虚拟机内的 Agent init API
    let client = reqwest::Client::new();
    let response = client
        .post("http://localhost:8080/api/init")
        .json(&serde_json::json!({
            "user_token": token,
            "cloud_api_base": "https://api.novaic.com"
        }))
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    if response.status().is_success() {
        Ok("Agent initialized".to_string())
    } else {
        Err("Failed to initialize agent".to_string())
    }
}
```

```rust
// src-tauri/src/commands/file_commands.rs

use tauri::command;
use std::path::Path;

#[command]
pub async fn upload_file_to_vm(
    local_path: String,
    vm_path: String,
) -> Result<String, String> {
    // 使用 SCP 或 HTTP 上传到虚拟机
    let client = reqwest::Client::new();
    
    let file_content = std::fs::read(&local_path)
        .map_err(|e| e.to_string())?;
    
    let file_name = Path::new(&local_path)
        .file_name()
        .unwrap()
        .to_str()
        .unwrap();
    
    let form = reqwest::multipart::Form::new()
        .part("file", reqwest::multipart::Part::bytes(file_content)
            .file_name(file_name.to_string()))
        .text("path", vm_path);
    
    let response = client
        .post("http://localhost:8080/api/upload")
        .multipart(form)
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    if response.status().is_success() {
        Ok("File uploaded".to_string())
    } else {
        Err("Upload failed".to_string())
    }
}

#[command]
pub async fn download_file_from_vm(
    vm_path: String,
    local_path: String,
) -> Result<String, String> {
    let client = reqwest::Client::new();
    
    let response = client
        .get("http://localhost:8080/api/download")
        .query(&[("path", &vm_path)])
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    if response.status().is_success() {
        let bytes = response.bytes().await.map_err(|e| e.to_string())?;
        std::fs::write(&local_path, bytes).map_err(|e| e.to_string())?;
        Ok("File downloaded".to_string())
    } else {
        Err("Download failed".to_string())
    }
}
```

### 6.3 前端 Agent Hook

```typescript
// src/hooks/useAgent.ts

import { useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/tauri';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: string[];
}

interface UseAgentReturn {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (content: string, files?: File[]) => Promise<void>;
  clearHistory: () => void;
}

export function useAgent(): UseAgentReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string, files?: File[]) => {
    setIsLoading(true);
    setError(null);

    // 添加用户消息
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
      attachments: files?.map(f => f.name),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      // 上传文件
      if (files && files.length > 0) {
        for (const file of files) {
          const arrayBuffer = await file.arrayBuffer();
          const bytes = Array.from(new Uint8Array(arrayBuffer));
          
          await invoke('upload_file_to_vm', {
            localPath: file.name,  // 实际应该用完整路径
            vmPath: `/home/user/uploads/${file.name}`,
          });
        }
      }

      // 发送消息到 Agent
      const response = await fetch('http://localhost:8080/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
      
      // 处理响应
      for (const result of data.results) {
        if (result.type === 'final') {
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: result.data,
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, assistantMessage]);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearHistory = useCallback(() => {
    setMessages([]);
    fetch('http://localhost:8080/api/clear', { method: 'POST' });
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearHistory,
  };
}
```

### 6.4 VNC 组件

```typescript
// src/components/VNC/VNCView.tsx

import React, { useEffect, useRef, useState } from 'react';
import RFB from '@novnc/novnc/lib/rfb';

interface VNCViewProps {
  host?: string;
  port?: number;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function VNCView({
  host = 'localhost',
  port = 5900,
  onConnect,
  onDisconnect,
}: VNCViewProps) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const rfbRef = useRef<RFB | null>(null);
  const [connected, setConnected] = useState(false);
  const [isInteractive, setIsInteractive] = useState(false);

  useEffect(() => {
    if (!canvasRef.current) return;

    // 创建 WebSocket URL
    const url = `ws://${host}:${port}/websockify`;

    // 创建 RFB 连接
    const rfb = new RFB(canvasRef.current, url, {
      credentials: { password: '' },
    });

    rfb.scaleViewport = true;
    rfb.resizeSession = true;
    rfb.viewOnly = !isInteractive;

    rfb.addEventListener('connect', () => {
      setConnected(true);
      onConnect?.();
    });

    rfb.addEventListener('disconnect', () => {
      setConnected(false);
      onDisconnect?.();
    });

    rfbRef.current = rfb;

    return () => {
      rfb.disconnect();
    };
  }, [host, port, onConnect, onDisconnect]);

  // 切换交互模式
  useEffect(() => {
    if (rfbRef.current) {
      rfbRef.current.viewOnly = !isInteractive;
    }
  }, [isInteractive]);

  return (
    <div className="vnc-container">
      <div className="vnc-toolbar">
        <span className={`status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '● 已连接' : '○ 未连接'}
        </span>
        <button
          onClick={() => setIsInteractive(!isInteractive)}
          className={isInteractive ? 'active' : ''}
        >
          {isInteractive ? '🖱️ 交互模式' : '👀 观看模式'}
        </button>
        <button onClick={() => rfbRef.current?.sendCtrlAltDel()}>
          Ctrl+Alt+Del
        </button>
      </div>
      <div ref={canvasRef} className="vnc-canvas" />
    </div>
  );
}
```

---

## 8. 通信协议

### 7.1 Tauri App ↔ Agent API

| 端点 | 方法 | 说明 | 请求 | 响应 |
|------|------|------|------|------|
| `/api/init` | POST | 初始化 Agent | `{user_token, cloud_api_base}` | `{status}` |
| `/api/chat` | POST | 对话 | `{message}` | `{results: [{type, data}]}` |
| `/api/chat/stream` | POST | 流式对话 | `{message}` | SSE stream |
| `/api/upload` | POST | 上传文件 | multipart/form-data | `{status, path}` |
| `/api/download` | GET | 下载文件 | `?path=xxx` | file binary |
| `/api/history` | GET | 获取历史 | - | `{messages}` |
| `/api/clear` | POST | 清空历史 | - | `{status}` |
| `/api/health` | GET | 健康检查 | - | `{status}` |

### 7.2 Agent ↔ Cloud Service API

| 端点 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/auth/login` | POST | 登录 | 无 |
| `/api/auth/register` | POST | 注册 | 无 |
| `/api/llm/chat` | POST | LLM 代理 | Bearer Token |
| `/api/subscription/status` | GET | 订阅状态 | Bearer Token |

### 7.3 SSE 事件格式

```typescript
// 流式响应事件
interface SSEEvent {
  type: 'text' | 'tool_use' | 'tool_result' | 'final' | 'error';
  data: string | object;
}

// 示例
// data: {"type": "text", "data": "我来帮你分析..."}
// data: {"type": "tool_use", "data": {"name": "run_python", "input": {...}}}
// data: {"type": "tool_result", "data": {"output": "...", "error": null}}
// data: {"type": "final", "data": "分析完成！报告已保存到..."}
```

---

## 9. 数据库设计

### 8.1 ER 图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     users       │     │  subscriptions  │     │  usage_records  │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │────<│ user_id (FK)    │     │ id (PK)         │
│ email           │     │ id (PK)         │────<│ subscription_id │
│ password_hash   │     │ plan            │     │ tokens_used     │
│ name            │     │ status          │     │ created_at      │
│ created_at      │     │ quota           │     └─────────────────┘
│ updated_at      │     │ used            │
└─────────────────┘     │ starts_at       │
                        │ expires_at      │
                        │ created_at      │
                        └─────────────────┘
```

### 8.2 表结构

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 订阅表
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    plan VARCHAR(50) NOT NULL, -- 'free', 'pro', 'pro_cloud', 'team'
    status VARCHAR(20) NOT NULL, -- 'active', 'cancelled', 'expired'
    quota INTEGER NOT NULL, -- 月配额 (tokens)
    used INTEGER DEFAULT 0, -- 已用配额
    starts_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用量记录表
CREATE TABLE usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id),
    tokens_used INTEGER NOT NULL,
    model VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_usage_records_subscription_id ON usage_records(subscription_id);
CREATE INDEX idx_usage_records_created_at ON usage_records(created_at);
```

---

## 10. 安全设计

### 9.1 安全架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           安全边界                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  云服务安全                                                                  │
│  ├── JWT 认证 (RS256)                                                       │
│  ├── HTTPS 强制                                                             │
│  ├── API Rate Limiting                                                     │
│  ├── 请求签名验证                                                           │
│  └── API Key 加密存储                                                       │
│                                                                             │
│  传输安全                                                                    │
│  ├── TLS 1.3                                                               │
│  ├── Certificate Pinning (可选)                                            │
│  └── 敏感数据加密传输                                                       │
│                                                                             │
│  本地安全                                                                    │
│  ├── 虚拟机沙盒隔离                                                         │
│  ├── 代码执行确认                                                           │
│  ├── 文件访问限制                                                           │
│  ├── 网络访问控制                                                           │
│  └── Token 安全存储 (Keychain)                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 代码执行安全

```python
# tools/safe_executor.py

import ast
import re
from typing import List, Tuple

class CodeSafetyChecker:
    """代码安全检查器"""
    
    # 危险模块
    DANGEROUS_MODULES = [
        'os.system', 'subprocess', 'eval', 'exec',
        'pickle', 'marshal', '__import__'
    ]
    
    # 危险模式
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf',
        r'sudo\s+',
        r'chmod\s+777',
        r'/etc/passwd',
        r'/etc/shadow',
    ]
    
    def check_python(self, code: str) -> Tuple[bool, List[str]]:
        """检查 Python 代码安全性"""
        warnings = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, [f"语法错误: {e}"]
        
        for node in ast.walk(tree):
            # 检查危险导入
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.DANGEROUS_MODULES:
                        warnings.append(f"危险导入: {alias.name}")
            
            # 检查 eval/exec
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec']:
                        warnings.append(f"危险函数: {node.func.id}")
        
        return len(warnings) == 0, warnings
    
    def check_shell(self, command: str) -> Tuple[bool, List[str]]:
        """检查 Shell 命令安全性"""
        warnings = []
        
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                warnings.append(f"危险命令模式: {pattern}")
        
        return len(warnings) == 0, warnings
```

---

## 11. 部署方案

### 10.1 开发环境

```bash
# 1. 启动虚拟机
qemu-system-x86_64 \
  -m 4G \
  -smp 2 \
  -hda novaic-vm.qcow2 \
  -net nic -net user,hostfwd=tcp::8080-:8080,hostfwd=tcp::5900-:5900 \
  -vnc :0

# 2. 虚拟机内启动 Agent
cd /opt/novaic-agent
python main.py

# 3. 启动 Tauri 开发服务器
cd novaic-app
npm run tauri dev
```

### 10.2 生产环境（云服务）

```yaml
# docker-compose.yml

version: '3.8'

services:
  api:
    build: ./cloud_service
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/nbcc
      - SECRET_KEY=${SECRET_KEY}
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
    depends_on:
      - db

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=nbcc

volumes:
  postgres_data:
```

### 10.3 桌面应用打包

```bash
# macOS
npm run tauri build

# 产出
# target/release/bundle/dmg/NovAIC_0.1.0_aarch64.dmg
# target/release/bundle/macos/NovAIC.app
```

### 10.4 虚拟机镜像制作

```bash
# 1. 创建基础镜像
qemu-img create -f qcow2 novaic-vm.qcow2 20G

# 2. 安装 Ubuntu
qemu-system-x86_64 -m 2G -hda novaic-vm.qcow2 -cdrom ubuntu.iso -boot d

# 3. 配置环境（在虚拟机内）
apk add python3 py3-pip nodejs npm firefox xfce4 tigervnc
pip install -r /opt/novaic-agent/requirements.txt

# 4. 配置自启动
# /etc/init.d/novaic-agent
# /etc/init.d/tigervnc

# 5. 压缩镜像
qemu-img convert -O qcow2 -c novaic-vm.qcow2 novaic-vm-compressed.qcow2
```

---

## 附录

### A. 环境变量

```bash
# 云服务
DATABASE_URL=postgresql://user:pass@localhost:5432/nbcc
SECRET_KEY=your-jwt-secret-key
CLAUDE_API_KEY=sk-ant-xxx

# 桌面应用
CLOUD_API_BASE=https://api.novaic.com
VM_IMAGE_PATH=/path/to/novaic-vm.qcow2
```

### B. 参考文档

- [Open Interpreter 文档](https://docs.openinterpreter.com)
- [Tauri 文档](https://tauri.app/v1/guides/)
- [noVNC 文档](https://github.com/novnc/noVNC)
- [Claude API 文档](https://docs.anthropic.com/claude/reference)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

---

**文档版本**: v1.1  
**最后更新**: 2026-01-10

## 文档变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2026-01-10 | 初始版本 |
| v1.1 | 2026-01-10 | 新增第5章「可视化执行设计」（方案A+B）|

